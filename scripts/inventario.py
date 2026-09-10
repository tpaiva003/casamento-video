# -*- coding: utf-8 -*-
"""Inventario de todo o media: metadados, datas, resolucao e miniaturas.

Percorre 00-ORIGINAL-MAE e 01-NOVAS, le dimensoes e EXIF, calcula o fator de
upscaling necessario para projecao 1920x1080 (decisoes 003 e 004), cruza com a
timeline da mae da Clara para herdar legenda, bloco e pessoa, e gera as
miniaturas de 400 px em proxies/.

Nao altera nem apaga nada no media. Duplicados por conteudo sao apenas
reportados, nunca tratados (BRIEFING seccao 12).

Uso:  py -3.11 scripts/inventario.py
"""
import csv
import hashlib
import os
import re
import sys
from collections import defaultdict

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = r"C:\casamento-video-media\trabalho"
PASTAS = [("00-ORIGINAL-MAE", os.path.join(BASE, "00-ORIGINAL-MAE")),
          ("01-NOVAS", os.path.join(BASE, "01-NOVAS"))]
OUT = os.path.join(REPO, "data", "inventario.csv")
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")
PROXIES = os.path.join(REPO, "proxies")

EXT = (".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".bmp")
LARGURA_ALVO, ALTURA_ALVO = 1920, 1080
LADO_PROXY = 400
NASCIMENTO = 1995  # Clara e Tiago nasceram ambos em 1995, dito nas legendas

# Seccoes da timeline dela, em segundos, tiradas dos 12 cartoes de ecra inteiro.
SECCOES = [
    (0.0, 20.4, "Fanfarra", ""),
    (20.4, 498.0, "Clara", "Clara"),
    (498.0, 659.0, "Familia", "Familia"),
    (659.0, 695.0, "Amigos e colegas", "Amigos"),
    (695.0, 761.0, "Colegas de trabalho (dela)", "Amigos"),
    (761.0, 1020.0, "Tiago", "Tiago"),
    (1020.0, 1071.0, "Colegas de trabalho (dele)", "Amigos"),
    (1071.0, 1228.0, "O encontro", "Ambos"),
    (1228.0, 1401.0, "Cumplicidades", "Ambos"),
    (1401.0, 9999.0, "The End", ""),
]

COLUNAS = [
    "id", "ficheiro", "pasta", "sha256", "bytes", "largura", "altura",
    "orientacao", "aspeto", "fator_upscale", "resolucao_ok", "equipamento",
    "digitalizacao", "data_exif", "ano", "fonte_ano",
    "usada_pela_mae", "inicio_original_s",
    "duracao_original_s", "bloco_original", "pessoa", "fonte_pessoa",
    "legenda_mae", "proxy", "caminho", "nota",
]


def seccao(t):
    for ini, fim, nome, pessoa in SECCOES:
        if ini <= t < fim:
            return nome, pessoa
    return "", ""


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1048576), b""):
            h.update(bloco)
    return h.hexdigest()


# Equipamentos que NAO sao camaras. Se a foto veio de um destes, a data EXIF e
# o dia em que a mae da Clara a passou a scanner, nao o dia em que foi tirada.
# Uma foto de bebe do Tiago aparece datada de 2013 por esta razao exata.
SCANNERS = re.compile(
    r"scanjet|ojj\d|officejet|deskjet|laserjet|envy|smart\s*tank|mfp|"
    r"canoscan|perfection|epson\s*scan|mp\s*navigator|imageclass|"
    r"workforce|pixma|lide|photosmart",
    re.I)


def equipamento(img):
    """Marca e modelo do EXIF, se existirem."""
    try:
        exif = img.getexif()
    except Exception:
        return ""
    marca = str(exif.get(271, "") or "").strip()
    modelo = str(exif.get(272, "") or "").strip()
    return re.sub(r"\s+", " ", ("%s %s" % (marca, modelo)).strip())


def data_exif(img):
    """DateTimeOriginal, DateTimeDigitized ou DateTime, o primeiro que exista."""
    try:
        exif = img.getexif()
    except Exception:
        return ""
    for tag in (36867, 36868, 306):
        v = exif.get(tag)
        if not v:
            continue
        m = re.match(r"(\d{4})[:\-](\d{2})[:\-](\d{2})", str(v).strip())
        if m and m.group(1) != "0000":
            return "%s-%s-%s" % m.groups()
    return ""


def ano_do_nome(nome):
    """So aceita datas plausiveis e completas.

    Nomes de redes sociais sao cadeias longas de digitos onde qualquer padrao
    de 4 digitos aparece por acaso (ex: 69916331_2555139434539758_29207367...
    contem "2073"). Exigir mes e dia validos, e fronteira de token, elimina
    esses falsos positivos.
    """
    for m in re.finditer(r"(?<!\d)(19[5-9]\d|20[0-2]\d)[-_]?(\d{2})[-_]?(\d{2})(?!\d)", nome):
        ano, mes, dia = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mes <= 12 and 1 <= dia <= 31 and ano <= 2026:
            return str(ano)
    return ""


def ano_da_legenda(txt):
    """As legendas dela dizem anos ("Em 2011") ou idades ("Aos 8 anos")."""
    if not txt:
        return "", ""
    m = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", txt)
    if m:
        return m.group(1), "legenda (ano escrito)"
    m = re.search(r"[Aa]os\s+(\d{1,2})\s+anos", txt)
    if m:
        return str(NASCIMENTO + int(m.group(1))), "legenda (idade)"
    m = re.search(r"[Cc]om\s+(\d{1,2})\s+anos", txt)
    if m:
        return str(NASCIMENTO + int(m.group(1))), "legenda (idade)"
    return "", ""


def carregar_timeline():
    """Nome de ficheiro em minusculas -> primeira aparicao na timeline dela."""
    if not os.path.exists(TIMELINE):
        return {}
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    video = [r for r in linhas if r["faixa"] == "video" and r["ficheiro"]]
    textos = [r for r in linhas if r["faixa"] == "texto" and r["texto_ecra"]]
    por_ficheiro = {}
    for r in sorted(video, key=lambda x: float(x["inicio_s"])):
        chave = r["ficheiro"].lower()
        if chave in por_ficheiro:
            continue
        ini, fim = float(r["inicio_s"]), float(r["fim_s"])
        legenda = " / ".join(t["texto_ecra"] for t in textos
                             if ini <= float(t["inicio_s"]) < fim)
        bloco, pessoa = seccao(ini)
        por_ficheiro[chave] = {
            "inicio": ini,
            "duracao": float(r["duracao_s"]),
            "legenda": re.sub(r"\s+", " ", legenda).strip(),
            "bloco": bloco,
            "pessoa": pessoa,
        }
    return por_ficheiro


def main():
    timeline = carregar_timeline()
    os.makedirs(PROXIES, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    ja_registadas = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8-sig", newline="") as fh:
            ja_registadas = {r["sha256"] for r in csv.DictReader(fh)}

    linhas, erros = [], []
    por_hash = defaultdict(list)

    for etiqueta, raiz in PASTAS:
        if not os.path.isdir(raiz):
            continue
        for base, _dirs, ficheiros in os.walk(raiz):
            for nome in sorted(ficheiros):
                if not nome.lower().endswith(EXT):
                    continue
                caminho = os.path.join(base, nome)
                rel = os.path.relpath(base, raiz)
                pasta = etiqueta if rel == "." else "%s/%s" % (
                    etiqueta, rel.replace("\\", "/"))
                try:
                    h = sha256(caminho)
                    with Image.open(caminho) as bruta:
                        img = ImageOps.exif_transpose(bruta)
                        larg, alt = img.size
                        dexif = data_exif(bruta)
                        equip = equipamento(bruta)
                        proxy = os.path.join(PROXIES, h[:12] + ".jpg")
                        if not os.path.exists(proxy):
                            mini = img.convert("RGB")
                            mini.thumbnail((LADO_PROXY, LADO_PROXY), Image.LANCZOS)
                            mini.save(proxy, "JPEG", quality=82, optimize=True)
                except Exception as e:
                    erros.append((caminho, "%s: %s" % (type(e).__name__, e)))
                    continue

                por_hash[h].append("%s/%s" % (pasta, nome))

                fator = max(LARGURA_ALVO / larg, ALTURA_ALVO / alt)
                tl = timeline.get(nome.lower())
                legenda = tl["legenda"] if tl else ""

                # Digitalizacao: equipamento de scanner, ou nome de lote de
                # digitalizacao (8-5.jpg, 21-49-13.JPG) sem camara declarada.
                lote = bool(re.match(r"^\d{1,3}(-\d{1,3}){0,3}(\s*\(\d+\))?$",
                                     os.path.splitext(nome)[0].strip()))
                scan = bool(SCANNERS.search(equip)) or (lote and not equip)

                ano, fonte = "", ""
                if dexif and not scan:
                    ano, fonte = dexif[:4], "EXIF"
                if not ano:
                    ano, fonte = ano_da_legenda(legenda)
                if not ano:
                    candidato = ano_do_nome(nome)
                    if candidato:
                        ano, fonte = candidato, "nome do ficheiro"

                if alt > larg:
                    orient = "vertical"
                elif larg > alt:
                    orient = "horizontal"
                else:
                    orient = "quadrada"

                nota = []
                if scan and dexif:
                    nota.append("EXIF %s e a data da digitalizacao, nao da foto" % dexif[:4])
                if fator > 2.0:
                    nota.append("upscale forte")
                if max(larg, alt) < 400:
                    nota.append("miniatura, provavelmente inutilizavel")
                if not ano:
                    nota.append("ano por determinar")

                linhas.append({
                    "id": "",
                    "ficheiro": nome,
                    "pasta": pasta,
                    "sha256": h,
                    "bytes": os.path.getsize(caminho),
                    "largura": larg,
                    "altura": alt,
                    "orientacao": orient,
                    "aspeto": round(larg / alt, 3),
                    "fator_upscale": round(fator, 2),
                    "resolucao_ok": "Sim" if fator <= 1.0 else "Nao",
                    "equipamento": equip,
                    "digitalizacao": "Sim" if scan else "Nao",
                    "data_exif": dexif,
                    "ano": ano,
                    "fonte_ano": fonte,
                    "usada_pela_mae": "Sim" if tl else "Nao",
                    "inicio_original_s": round(tl["inicio"], 1) if tl else "",
                    "duracao_original_s": round(tl["duracao"], 1) if tl else "",
                    "bloco_original": tl["bloco"] if tl else "",
                    "pessoa": tl["pessoa"] if tl else "",
                    "fonte_pessoa": "bloco da mae" if tl and tl["pessoa"] else "",
                    "legenda_mae": legenda,
                    "proxy": "proxies/" + h[:12] + ".jpg",
                    "caminho": caminho,
                    "nota": "; ".join(nota),
                })

    linhas.sort(key=lambda r: (r["pasta"], r["ficheiro"].lower()))
    for i, r in enumerate(linhas, 1):
        r["id"] = "f%04d" % i

    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas)

    novas = [r for r in linhas if r["sha256"] not in ja_registadas] if ja_registadas else []
    dups = {h: v for h, v in por_hash.items() if len(v) > 1}

    print("Escrito %s" % OUT)
    print("Imagens inventariadas: %d" % len(linhas))
    if ja_registadas:
        print("Imagens novas desde o inventario anterior: %d" % len(novas))
    print("Miniaturas de %d px em %s" % (LADO_PROXY, PROXIES))
    scans = sum(1 for r in linhas if r["digitalizacao"] == "Sim")
    enganosas = sum(1 for r in linhas
                    if r["digitalizacao"] == "Sim" and r["data_exif"])
    print("Digitalizacoes detetadas: %d (%d traziam data EXIF enganosa)"
          % (scans, enganosas))
    print("Duplicados confirmados por sha256: %d grupos" % len(dups))
    for h, v in list(dups.items())[:25]:
        print("   %s  ->  %s" % (h[:12], " | ".join(v)))
    if erros:
        print("Ficheiros que nao consegui ler: %d" % len(erros))
        for c, e in erros[:10]:
            print("   %s  (%s)" % (os.path.basename(c), e))


if __name__ == "__main__":
    main()
