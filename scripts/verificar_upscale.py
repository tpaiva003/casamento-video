# -*- coding: utf-8 -*-
"""Verifica se o tratamento das fotos esta mesmo a melhorar, ou a piorar.

A pergunta e do Tiago e e a certa: dizer que o Real-ESRGAN melhora nao chega,
tem de se medir. E medir mal e facil, por isso a comparacao aqui e justa por
construcao:

  O ORIGINAL e levado ao MESMO TAMANHO da saida, com lanczos, antes de ser
  medido. Sem isso estariamos a comparar uma imagem pequena com uma grande e a
  chamar melhoria ao simples facto de haver mais pixeis.

Duas medidas, porque uma so engana:

  NITIDEZ, desvio padrao do laplaciano. Sobe com detalhe verdadeiro mas TAMBEM
  com grao e com halos de realce. Sozinha, premeia o artefacto.

  ENERGIA DE ALTA FREQUENCIA NOS LISOS. Mede a agitacao nas zonas que deviam
  ser lisas, ceu, paredes, pele. Se esta sobe muito, o que ganhamos foi ruido,
  nao detalhe.

Uma melhoria a serio sobe a nitidez SEM subir a agitacao nos lisos.

Gera tambem recortes a 100 por cento lado a lado, em
C:\\casamento-video-media\\verificacao\\, para se poder olhar em vez de confiar.

Uso:  py -3.11 scripts/verificar_upscale.py
      py -3.11 scripts/verificar_upscale.py --recortes 12
"""
import csv
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
PASTAS = [(r"C:\casamento-video-media\upscaled-ia", "IA"),
          (r"C:\casamento-video-media\upscaled", "lanczos")]
SAIDA = r"C:\casamento-video-media\verificacao"

LAPLACIANO = ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 4, -1, 0, -1, 0], scale=1)


def nitidez(im):
    return ImageStat.Stat(im.convert("L").filter(LAPLACIANO)).stddev[0]


def agitacao_nos_lisos(im, lado=14):
    """Desvio padrao do laplaciano so nos blocos que sao lisos no original.

    Divide a imagem em blocos, escolhe o quarto mais liso, e mede so ai. E
    nesses sitios que o ruido e os halos aparecem sem disfarce.
    """
    g = im.convert("L")
    g.thumbnail((700, 700), Image.LANCZOS)
    lap = g.filter(LAPLACIANO)
    blocos = []
    for y in range(0, g.height - lado, lado):
        for x in range(0, g.width - lado, lado):
            caixa = (x, y, x + lado, y + lado)
            blocos.append((ImageStat.Stat(g.crop(caixa)).stddev[0],
                           ImageStat.Stat(lap.crop(caixa)).stddev[0]))
    if not blocos:
        return 0.0
    blocos.sort(key=lambda b: b[0])
    lisos = blocos[:max(1, len(blocos) // 4)]
    return sum(b[1] for b in lisos) / len(lisos)


def rotular(im, texto, tamanho=40):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", tamanho)
    w = d.textbbox((0, 0), texto, font=f)[2]
    d.rectangle([12, 12, 34 + w, 26 + tamanho], fill=(0, 0, 0))
    d.text((22, 16), texto, font=f, fill=(255, 255, 255))
    return im


def main():
    quantos_recortes = 8
    if "--recortes" in sys.argv:
        quantos_recortes = int(sys.argv[sys.argv.index("--recortes") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = {r["id"]: r for r in csv.DictReader(fh)}

    casos = []
    for pasta, etiqueta in PASTAS:
        if not os.path.isdir(pasta):
            continue
        for nome in sorted(os.listdir(pasta)):
            if not nome.lower().endswith((".jpg", ".png")):
                continue
            ident = nome.split("__")[0]
            r = inv.get(ident)
            if not r or not os.path.exists(r["caminho"]):
                continue
            casos.append((etiqueta, r, os.path.join(pasta, nome)))

    if not casos:
        sys.exit("Nada tratado ainda.")

    print("A verificar %d ficheiros tratados" % len(casos))
    print()

    resultados = []
    for etiqueta, r, tratado in casos:
        try:
            with Image.open(tratado) as t:
                t = t.convert("RGB")
                alvo = t.size
                with Image.open(r["caminho"]) as o:
                    o = ImageOps.exif_transpose(o).convert("RGB")
                    base = o.resize(alvo, Image.LANCZOS)
                resultados.append({
                    "etiqueta": etiqueta,
                    "id": r["id"],
                    "ficheiro": r["ficheiro"],
                    "origem": "%sx%s" % (r["largura"], r["altura"]),
                    "saida": "%dx%d" % alvo,
                    "nit_base": nitidez(base),
                    "nit_trat": nitidez(t),
                    "agit_base": agitacao_nos_lisos(base),
                    "agit_trat": agitacao_nos_lisos(t),
                    "caminho_base": r["caminho"],
                    "caminho_trat": tratado,
                })
        except Exception as e:
            print("  erro em %s: %s" % (r["ficheiro"][:40], e))

    for x in resultados:
        x["d_nit"] = 100 * (x["nit_trat"] - x["nit_base"]) / max(0.01, x["nit_base"])
        x["d_agit"] = 100 * (x["agit_trat"] - x["agit_base"]) / max(0.01, x["agit_base"])
        # Melhoria real: mais nitidez sem pagar em agitacao nos lisos.
        if x["d_nit"] > 3 and x["d_agit"] < 15:
            x["veredicto"] = "melhor"
        elif x["d_nit"] < -3 or x["d_agit"] > 40:
            x["veredicto"] = "PIOR"
        else:
            x["veredicto"] = "igual"

    for etiqueta, _ in PASTAS:
        grupo = [x for x in resultados if x["etiqueta"] == etiqueta]
        if not grupo:
            continue
        print("== %s: %d ficheiros ==" % (etiqueta, len(grupo)))
        for v in ("melhor", "igual", "PIOR"):
            n = sum(1 for x in grupo if x["veredicto"] == v)
            print("   %-8s %3d  (%.0f%%)" % (v, n, 100 * n / len(grupo)))
        nit = sorted(x["d_nit"] for x in grupo)
        agi = sorted(x["d_agit"] for x in grupo)
        print("   nitidez:  mediana %+.0f%%   pior %+.0f%%   melhor %+.0f%%"
              % (nit[len(nit) // 2], nit[0], nit[-1]))
        print("   agitacao nos lisos: mediana %+.0f%%   pior %+.0f%%"
              % (agi[len(agi) // 2], agi[-1]))
        print()

    piores = [x for x in resultados if x["veredicto"] == "PIOR"]
    if piores:
        print("OS QUE PIORARAM")
        for x in sorted(piores, key=lambda x: x["d_nit"])[:12]:
            print("   %-8s %-34s nit %+.0f%%  agit %+.0f%%"
                  % (x["etiqueta"], x["ficheiro"][:34], x["d_nit"], x["d_agit"]))
        print()

    # Recortes a 100 por cento, escolhendo os extremos e o meio.
    os.makedirs(SAIDA, exist_ok=True)
    ordenados = sorted(resultados, key=lambda x: x["d_nit"])
    escolhidos = []
    if ordenados:
        n = len(ordenados)
        passos = max(1, n // max(1, quantos_recortes))
        escolhidos = ordenados[::passos][:quantos_recortes]
    for x in escolhidos:
        try:
            with Image.open(x["caminho_trat"]) as t:
                t = t.convert("RGB")
                with Image.open(x["caminho_base"]) as o:
                    base = ImageOps.exif_transpose(o).convert("RGB").resize(t.size, Image.LANCZOS)
                lado = min(760, t.width // 2, t.height // 2)
                cx, cy = t.width // 2 - lado // 2, int(t.height * 0.38)
                caixa = (cx, cy, cx + lado, cy + lado)
                a = rotular(base.crop(caixa), "ORIGINAL")
                b = rotular(t.crop(caixa), x["etiqueta"].upper())
                par = Image.new("RGB", (lado * 2 + 10, lado), (0, 0, 0))
                par.paste(a, (0, 0))
                par.paste(b, (lado + 10, 0))
                par.save(os.path.join(
                    SAIDA, "%s_%s_nit%+.0f.jpg" % (x["id"], x["etiqueta"], x["d_nit"])),
                    "JPEG", quality=92)
        except Exception as e:
            print("  recorte falhou em %s: %s" % (x["ficheiro"][:30], e))

    print("Recortes a 100%% em %s (%d pares)" % (SAIDA, len(escolhidos)))


if __name__ == "__main__":
    main()
