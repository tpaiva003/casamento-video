# -*- coding: utf-8 -*-
"""Mede, DENTRO DAS CARAS, quanto cada fotografia final se afastou do original.

PORQUE EXISTE (23 de setembro): o Tiago disse que algumas imagens pareciam ter perdido
qualidade e que numa delas "os modelos foram para la editar os olhos e ficou estranho". A
garantia que existia media a diferenca media por pixel na fotografia INTEIRA e recusava acima
de 8 por cento. Uma cara ocupa uma fraccao pequena do quadro: um olho inteiramente redesenhado
mexe pouco nessa media, e por isso ele viu uma coisa que a medida nao via.

O QUE MEDE, por cara e nao pela fotografia toda:
  - SSIM, a semelhanca estrutural, entre o original e o final a MESMA escala. Responde a
    pergunta certa: a forma mudou, ou so mudou o contraste? Um realce mantem a SSIM alta.
  - O detalhe fino que sobrou. Abaixo de 1 o filtro comeu textura, e e isso que faz uma pele
    parecer plastico; muito acima de 1 e realce a mais, que faz halos.
  - O mesmo dentro dos olhos, quando o detector os encontra, porque foi ali que ele reparou.

O QUE NAO FAZ: nao altera nenhuma imagem e nao escreve nada em
C:\\casamento-video-media\\. So le e mede. As imagens de prova vao para a pasta que se pedir.

Uso:
    py -3.11 scripts/auditar_caras.py                 as fotografias do filme
    py -3.11 scripts/auditar_caras.py --todas         as 719
    py -3.11 scripts/auditar_caras.py --provas <pasta>  escreve os recortes das piores
"""
import csv
import os
import sys

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = r"C:\casamento-video-media\trabalho"
FIN = r"C:\casamento-video-media\FINAIS"
# Abaixo disto a forma mudou a serio e alguem tem de olhar. Medido no lote de 23 de setembro.
SSIM_SUSPEITA = 0.90
DETALHE_BAIXO = 0.60
DETALHE_ALTO = 1.60


def carregar_indices():
    inv = {r["id"]: r for r in csv.DictReader(
        open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig"))}
    fin = {r["id"]: r for r in csv.DictReader(
        open(os.path.join(REPO, "data", "finais.csv"), encoding="utf-8-sig"))}
    return inv, fin


def caminhos(ident, inv, fin):
    r, f = inv[ident], fin[ident]
    return (os.path.join(MEDIA, r["pasta"].replace("/", os.sep), r["ficheiro"]),
            os.path.join(FIN, f["final"]))


def ler(caminho):
    """Cinzentos, com a rotacao do EXIF aplicada, como o render faz."""
    dados = np.fromfile(caminho, dtype=np.uint8)      # suporta acentos no caminho
    img = cv2.imdecode(dados, cv2.IMREAD_COLOR)
    return img


def detalhe(x):
    s = cv2.GaussianBlur(x, (0, 0), 1.2)
    return float(np.abs(x.astype(np.float32) - s.astype(np.float32)).mean())


def caras_de(cinza):
    """As caras que o detector encontra, de frente e de perfil, sem repetir."""
    achadas = []
    for nome in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
        c = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, nome))
        for (x, y, w, h) in c.detectMultiScale(cinza, 1.15, 6, minSize=(60, 60)):
            if not any(abs(x - a) < w * 0.5 and abs(y - b) < h * 0.5 for a, b, _w, _h in achadas):
                achadas.append((int(x), int(y), int(w), int(h)))
    return achadas


def uma(ident, inv, fin):
    co, cf = caminhos(ident, inv, fin)
    if not (os.path.exists(co) and os.path.exists(cf)):
        return None
    o, d = ler(co), ler(cf)
    if o is None or d is None:
        return None
    if (d.shape[1], d.shape[0]) != (o.shape[1], o.shape[0]):
        d = cv2.resize(d, (o.shape[1], o.shape[0]), interpolation=cv2.INTER_AREA)
    go = cv2.cvtColor(o, cv2.COLOR_BGR2GRAY)
    gd = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)
    caras = caras_de(go)
    saida = {"id": ident, "caras": len(caras), "piores": []}
    for (x, y, w, h) in caras:
        a, b = go[y:y + h, x:x + w], gd[y:y + h, x:x + w]
        if min(a.shape) < 32:
            continue
        s = float(ssim(a, b))
        da, db = detalhe(a), detalhe(b)
        saida["piores"].append({"caixa": (x, y, w, h), "ssim": s,
                                "detalhe": db / max(0.01, da), "lado": int(min(w, h))})
    saida["piores"].sort(key=lambda c: c["ssim"])
    # e a fotografia inteira, para termo de comparacao
    saida["ssim_total"] = float(ssim(go, gd))
    saida["detalhe_total"] = detalhe(gd) / max(0.01, detalhe(go))
    return saida


def main():
    inv, fin = carregar_indices()
    if "--todas" in sys.argv:
        ids = sorted(inv)
    else:
        ids = sorted({r["id"] for r in csv.DictReader(
            open(os.path.join(REPO, "data", "montagens", "v3.csv"), encoding="utf-8-sig"))
            if r["id"]})
    provas = sys.argv[sys.argv.index("--provas") + 1] if "--provas" in sys.argv else None
    if provas:
        os.makedirs(provas, exist_ok=True)

    linhas, sem_cara = [], 0
    for ident in ids:
        if ident not in fin or ident not in inv:
            continue
        r = uma(ident, inv, fin)
        if not r:
            continue
        if not r["piores"]:
            sem_cara += 1
            continue
        pior = r["piores"][0]
        linhas.append((pior["ssim"], pior["detalhe"], ident, fin[ident]["origem"],
                       fin[ident]["ficheiro"], pior["caixa"], r["ssim_total"],
                       r["detalhe_total"], len(r["piores"])))
    linhas.sort()
    print("fotografias medidas: %d, com cara encontrada: %d, sem cara: %d"
          % (len(ids), len(linhas), sem_cara))
    print()
    print("AS CARAS QUE MAIS MUDARAM DE FORMA (SSIM baixa = forma diferente)")
    print("  ssim  detalhe  id      origem      ficheiro")
    for s, det, ident, org, f, caixa, st, dt, n in linhas[:16]:
        marca = "  <<<" if (s < SSIM_SUSPEITA or det < DETALHE_BAIXO or det > DETALHE_ALTO) else ""
        print("  %.3f  %5.2f   %s  %-11s %-40s%s" % (s, det, ident, org, f[:40], marca))
    print()
    print("AS QUE MAIS TEXTURA PERDERAM NA CARA")
    for s, det, ident, org, f, caixa, st, dt, n in sorted(linhas, key=lambda l: l[1])[:10]:
        print("  detalhe %.2f  ssim %.3f  %s  %-11s %s" % (det, s, ident, org, f[:40]))

    # O RELATORIO INTEIRO EM CSV, e nao so as dezasseis do ecra: e dele que a guarda das caras
    # se alimenta, e e ele que diz quantas fotografias de todo o acervo estao em causa.
    cam = os.path.join(REPO, "data", "auditoria_caras.csv")
    with open(cam, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "origem", "ficheiro", "ssim_cara", "detalhe_cara",
                    "ssim_total", "detalhe_total", "caras", "caixa"])
        for s, det, ident, org, f, caixa, st, dt, n in linhas:
            w.writerow([ident, org, f, "%.4f" % s, "%.3f" % det,
                        "%.4f" % st, "%.3f" % dt, n, "%d;%d;%d;%d" % caixa])
    maus = [l for l in linhas if l[0] < SSIM_SUSPEITA or l[1] < DETALHE_BAIXO
            or l[1] > DETALHE_ALTO]
    print()
    print("A GUARDA PROPOSTA (ssim < %.2f, ou detalhe fora de %.2f a %.2f) apanha %d de %d"
          % (SSIM_SUSPEITA, DETALHE_BAIXO, DETALHE_ALTO, len(maus), len(linhas)))
    import collections
    print("  por origem: %s" % dict(collections.Counter(l[3] for l in maus)))
    print("  escrito: %s" % cam)

    if provas:
        escreve_provas(linhas[:10], inv, fin, provas)


def escreve_provas(piores, inv, fin, pasta):
    """Cada cara suspeita ao tamanho real: original em cima, final em baixo."""
    for s, det, ident, org, f, (x, y, w, h), st, dt, n in piores:
        co, cf = caminhos(ident, inv, fin)
        o, d = ler(co), ler(cf)
        if (d.shape[1], d.shape[0]) != (o.shape[1], o.shape[0]):
            d = cv2.resize(d, (o.shape[1], o.shape[0]), interpolation=cv2.INTER_AREA)
        m = int(max(w, h) * 0.25)
        x0, y0 = max(0, x - m), max(0, y - m)
        x1, y1 = min(o.shape[1], x + w + m), min(o.shape[0], y + h + m)
        a, b = o[y0:y1, x0:x1], d[y0:y1, x0:x1]
        alvo = 420
        esc = alvo / float(max(1, a.shape[1]))
        tam = (alvo, int(a.shape[0] * esc))
        a = cv2.resize(a, tam, interpolation=cv2.INTER_NEAREST)
        b = cv2.resize(b, tam, interpolation=cv2.INTER_NEAREST)
        folha = np.full((tam[1] * 2 + 62, alvo, 3), 20, np.uint8)
        folha[26:26 + tam[1]] = a
        folha[52 + tam[1]:52 + tam[1] * 2] = b
        cv2.putText(folha, "ORIGINAL", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 210, 255), 1)
        cv2.putText(folha, "FINAL (%s)  ssim %.2f  detalhe %.2f" % (org, s, det),
                    (6, 44 + tam[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (90, 210, 255), 1)
        nome = os.path.join(pasta, "cara_%s.jpg" % ident)
        cv2.imencode(".jpg", folha, [cv2.IMWRITE_JPEG_QUALITY, 94])[1].tofile(nome)
    print()
    print("provas escritas em %s" % pasta)


# SO CORRE QUANDO E CHAMADO PELO NOME. Sem esta guarda, importar o modulo corria o
# programa todo: o consolidar.py importa o auditar_caras para a guarda das caras e
# arrancava uma auditoria de 719 fotografias sem ninguem pedir.
if __name__ == "__main__":
    main()
