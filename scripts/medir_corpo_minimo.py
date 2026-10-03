# -*- coding: utf-8 -*-
"""O corpo minimo de cada letra da Mesa, medido como na decisao 084, para o data/fontes.json.

O Tiago, a 2 de outubro, pediu que a Mesa deixe mudar a letra das legendas e dos cartoes. A Mesa
oferece as letras de data/fontes.json, e cada uma leva `corpo_minimo`: o corpo a partir do qual a
letra separa as letras a 15 metros. E com ele que se compara uma letra com outra, e que o
montar_da_mesa.py diz quando uma escolha se le pior do que a de hoje.

O METODO E O DA 084, e nao outro. A 23 de setembro mediu-se assim que o Arial Bold separa as
letras a partir do corpo 58 e o Impact so a partir do 106:
  - ecra de 2,50 m de largura com 1920 pixeis, olho a 15 m;
  - o olho de uma sala com gente de todas as idades e vinho, 20/30: um borrao gaussiano de
    sigma 1,5 minutos de arco;
  - o par "nn" branco sobre preto, e o contraste de Michelson do vale branco entre as hastes,
    na fila do meio, depois do borrao;
  - a letra separa quando esse contraste chega a 0,30;
  - corpos de 30 para cima, de 4 em 4, e conta o primeiro que separa.
Antes de medir as outras, o script refaz a medida do Arial Bold e do Impact e recusa escrever
se nao der 58 e 106: um metodo que ja nao da os numeros da 084 nao e o da 084.

AS LETRAS ABREM-SE COMO O FILME AS ABRE, pelo render.abrir_letra(): nas variaveis com o eixo do
peso no eixo_peso de data/fontes.json. Medir a letra noutro peso era medir outra letra. As que so
tem maiusculas (Cinzel, Bebas Neue) medem-se com o mesmo "nn", que nelas desenha o que se ve.

So escreve o campo corpo_minimo, linha a linha, e deixa o resto do ficheiro como esta.

Uso:
    py -3.11 scripts/medir_corpo_minimo.py              mede e escreve
    py -3.11 scripts/medir_corpo_minimo.py --so-dizer   mede e so diz
"""
import json
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

LARGURA_ECRA_MM = 2500.0
PX_MM = LARGURA_ECRA_MM / 1920.0
DIST_MM = 15000.0
PX_POR_ARCMIN = (math.radians(1.0 / 60.0) * DIST_MM) / PX_MM
SIGMA_SALA = 1.5            # minutos de arco, olho 20/30
LIMIAR = 0.30               # o contraste do vale a partir do qual a letra separa
PAR = "nn"
CORPOS = range(30, 400, 4)  # do 30, de 4 em 4: e assim que saem o 58 e o 106
CALIBRACAO = {"Arial Bold": (r"C:\Windows\Fonts\arialbd.ttf", 58),
              "Impact": (r"C:\Windows\Fonts\impact.ttf", 106)}


def desenha(fonte, texto, pad=40):
    """O texto branco sobre preto, com folga a volta para o borrao nao bater na borda."""
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    b = d0.textbbox((0, 0), texto, font=fonte)
    im = Image.new("L", (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), texto, font=fonte, fill=255)
    return im


def entre_letras(fonte, par=PAR, sigma=SIGMA_SALA):
    """Michelson entre o vale branco que separa duas hastes e as proprias hastes, depois do olho."""
    im = desenha(fonte, par)
    bb = im.getbbox()
    if not bb:
        return 0.0
    borrado = im.filter(ImageFilter.GaussianBlur(sigma * PX_POR_ARCMIN))
    px = borrado.load()
    y = (bb[1] + bb[3]) // 2
    fila = [px[x, y] for x in range(bb[0], bb[2])]
    picos, vales = [], []
    for i in range(1, len(fila) - 1):
        if fila[i] >= fila[i - 1] and fila[i] >= fila[i + 1]:
            picos.append(fila[i])
        if fila[i] <= fila[i - 1] and fila[i] <= fila[i + 1]:
            vales.append(fila[i])
    if not picos or not vales:
        return 0.0
    p = max(picos)
    vs = [v for v in vales if v < p]
    if not vs:
        return 0.0
    v = min(vs)
    return 0.0 if p + v == 0 else (p - v) / float(p + v)


def corpo_minimo(abrir):
    """O primeiro corpo de CORPOS em que a letra separa, e o contraste dele; (None, 0) se nunca."""
    for c in CORPOS:
        e = entre_letras(abrir(c))
        if e >= LIMIAR:
            return c, e
    return None, 0.0


def calibrar():
    """Refaz a medida da 084. Devolve a lista do que nao bate (vazia quando bate)."""
    erros = []
    for nome, (caminho, certo) in CALIBRACAO.items():
        c, e = corpo_minimo(lambda corpo, caminho=caminho: ImageFont.truetype(caminho, corpo))
        print("  calibracao da 084: %-11s %s (contraste %.3f), a 084 diz %d" % (nome, c, e, certo))
        if c != certo:
            erros.append("%s deu %s e a 084 diz %d" % (nome, c, certo))
    return erros


def medir_todas(entradas):
    """{id: (corpo, contraste)} das letras de data/fontes.json, abertas como o filme as abre."""
    medidas = {}
    for ident, e in entradas.items():
        def abrir(corpo, ident=ident):
            f = render.abrir_letra(ident, corpo, entradas, avisar=False)
            if f is None:
                raise OSError("a letra %s nao abre" % ident)
            return f
        try:
            medidas[ident] = corpo_minimo(abrir)
        except OSError as erro:
            print("  %s: %s, fica por medir" % (ident, erro))
    return medidas


def escrever(caminho, medidas):
    """So o campo corpo_minimo da linha de cada id, e o resto do ficheiro tal e qual."""
    with open(caminho, encoding="utf-8", newline="") as fh:
        texto = fh.read()
    linhas = texto.split("\n")
    mudadas = 0
    for i, linha in enumerate(linhas):
        m = re.search(r'"id"\s*:\s*"([^"]+)"', linha)
        if not m or m.group(1) not in medidas or medidas[m.group(1)][0] is None:
            continue
        nova = re.sub(r'("corpo_minimo"\s*:\s*)(null|\d+)', lambda x: x.group(1) + str(medidas[m.group(1)][0]),
                      linha, count=1)
        if nova != linha:
            linhas[i] = nova
            mudadas += 1
    novo = "\n".join(linhas)
    json.loads(novo)          # nunca se escreve um ficheiro que nao se le
    if novo != texto:
        with open(caminho, "w", encoding="utf-8", newline="") as fh:
            fh.write(novo)
    return mudadas


def main():
    so_dizer = "--so-dizer" in sys.argv
    print("A 15 m num ecra de 2,50 m: 1 arcmin = %.2f px; olho 20/30, sigma %.2f px; limiar %.2f no par %r"
          % (PX_POR_ARCMIN, SIGMA_SALA * PX_POR_ARCMIN, LIMIAR, PAR))
    erros = calibrar()
    if erros:
        sys.exit("O metodo ja nao da os numeros da 084 (%s): nao escrevo nada." % "; ".join(erros))
    entradas = render.letras_da_mesa()
    if not entradas:
        sys.exit("Nao consegui ler %s." % render.FONTES_DA_MESA)
    medidas = medir_todas(entradas)
    print()
    print("  %-22s %6s  %9s  %s" % ("letra", "corpo", "contraste", "a 46 le-se como o Arial Bold a"))
    for ident, (c, e) in medidas.items():
        como = "" if not c else "%d" % int(math.floor(46 * 58.0 / c + 0.5))
        print("  %-22s %6s  %9.3f  %s" % (ident, c, e, como))
    if so_dizer:
        return
    n = escrever(render.FONTES_DA_MESA, medidas)
    print()
    print("Escrito: %s (%d letras com o corpo_minimo mudado)" % (render.FONTES_DA_MESA, n))


if __name__ == "__main__":
    main()
