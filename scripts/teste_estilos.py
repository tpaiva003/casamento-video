# -*- coding: utf-8 -*-
"""Menu de tratamentos visuais, para o Tiago escolher a ver.

  A. FUNDO DESFOCADO  fotos verticais deixam de ter barras pretas: o fundo
                      passa a ser a propria foto ampliada e desfocada.
                      Resolve 111 das 353 fotos, que sao verticais.
  B. COLAGEM          varias fotos entram uma a uma e ficam, compondo um
                      quadro. No fim a composicao respira com um zoom lento.
  C. RAJADA           stop-motion, 5 fotogramas por foto, corte seco.
  D. PILHA            as fotos caem umas sobre as outras, tortas, como
                      polaroids atiradas para cima de uma mesa.

PORQUE E QUE A PRIMEIRA VERSAO TREMIA
-------------------------------------
Tinha dois defeitos, os dois meus:

1. Quantizacao a inteiro. Em cada fotograma eu redimensionava a foto para
   int(largura * escala) e colava-a em int(x). Quando o movimento avanca meio
   pixel por fotograma, a imagem fica parada em varios fotogramas e depois
   salta um pixel de uma vez. O olho le isso como tremor.
2. Reamostragem repetida a partir do original. Redimensionar o original para
   um tamanho ligeiramente diferente em cada fotograma faz a fase da
   reamostragem mudar, e a textura fervilha.

A correcao e a mesma para os dois: cada foto e preparada UMA VEZ no tamanho
maximo de que vai precisar, ja rodada, e depois cada fotograma so lhe aplica
uma transformacao afim com precisao de sub-pixel. Nunca ha arredondamento a
inteiro na posicao nem no tamanho.

Na rajada o tremor era deliberado, uma alternancia de escala para dar energia.
Foi removido: agora e corte seco puro.

Uso:  py -3.11 scripts/teste_estilos.py
"""
import csv
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
SAIDA = r"C:\casamento-video-media\testes"

L, A, FPS = 1920, 1080, 25
FUNDO = (12, 12, 14)
FONTE_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONTE_REG = r"C:\Windows\Fonts\arial.ttf"

VERTICAIS = ["f0039", "f0046", "f0322", "f0060"]
COLAGEM = ["f0331", "f0334", "f0336", "f0308", "f0315"]
RAJADA = ["f0040", "f0042", "f0043", "f0083", "f0161", "f0163", "f0213",
          "f0216", "f0217", "f0222", "f0226", "f0057", "f0327", "f0328",
          "f0329", "f0330", "f0332", "f0333", "f0335", "f0337"]
PILHA = ["f0331", "f0327", "f0308", "f0334", "f0315", "f0336", "f0316", "f0328"]


def ffmpeg():
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Microsoft\WinGet\Packages"
                     r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                     r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
    if os.path.exists(p):
        return p
    from shutil import which
    return which("ffmpeg") or sys.exit("ffmpeg nao encontrado")


def suave(t):
    """Travagem no fim. Faz o movimento parecer pousado em vez de mecanico."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def abrir(caminho, lado_max=2600):
    im = Image.open(caminho)
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail((lado_max, lado_max), Image.LANCZOS)
    return im


def cobrir(im, larg, alt):
    """Escala para encher larg x alt sem deformar, cortando o excesso."""
    f = max(larg / im.width, alt / im.height)
    novo = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))),
                     Image.LANCZOS)
    x = (novo.width - larg) // 2
    y = (novo.height - alt) // 2
    return novo.crop((x, y, x + larg, y + alt))


def compor(tela, sprite, cx, cy, escala, alfa=1.0):
    """Coloca `sprite` centrado em (cx, cy) com precisao de SUB-PIXEL.

    Esta funcao e a correcao do tremor. Em vez de redimensionar e colar em
    coordenadas inteiras, separa a posicao em parte inteira e parte
    fracionaria, e mete a fracionaria dentro da propria transformacao afim.
    O resultado e que um movimento de meio pixel por fotograma aparece mesmo
    como meio pixel, em vez de ficar parado e depois saltar.

    `sprite` deve vir ja no tamanho maximo que vai ter e ja rodado, para que
    `escala` ande sempre perto de 1 e a reamostragem nao introduza fervilho.
    """
    larg = sprite.width * escala
    alt = sprite.height * escala
    x0 = cx - larg / 2.0
    y0 = cy - alt / 2.0
    ix, iy = math.floor(x0), math.floor(y0)
    fx, fy = x0 - ix, y0 - iy

    cx_dest = int(math.ceil(larg + fx)) + 1
    cy_dest = int(math.ceil(alt + fy)) + 1
    if cx_dest < 1 or cy_dest < 1:
        return
    inv = 1.0 / escala
    peca = sprite.transform(
        (cx_dest, cy_dest), Image.AFFINE,
        (inv, 0.0, -fx * inv, 0.0, inv, -fy * inv),
        resample=Image.BICUBIC)

    if alfa < 1.0:
        peca.putalpha(peca.split()[3].point(lambda v: int(v * alfa)))

    # Recorta o que cai fora da tela, para o alpha_composite nao rejeitar.
    px0 = max(0, -ix)
    py0 = max(0, -iy)
    px1 = min(peca.width, tela.width - ix)
    py1 = min(peca.height, tela.height - iy)
    if px1 <= px0 or py1 <= py0:
        return
    tela.alpha_composite(peca.crop((px0, py0, px1, py1)),
                         (ix + px0, iy + py0))


def moldurar(im, margem=9, cor=(240, 240, 242)):
    m = Image.new("RGB", (im.width + margem * 2, im.height + margem * 2), cor)
    m.paste(im, (margem, margem))
    return m


def cartao(texto, sub, segundos=2.6):
    base = Image.new("RGB", (L, A), FUNDO)
    d = ImageDraw.Draw(base)
    f1 = ImageFont.truetype(FONTE_BOLD, 88)
    f2 = ImageFont.truetype(FONTE_REG, 38)
    w1 = d.textbbox((0, 0), texto, font=f1)[2]
    d.text(((L - w1) / 2, A / 2 - 110), texto, font=f1, fill=(240, 240, 245))
    for i, linha in enumerate(sub.split("\n")):
        w2 = d.textbbox((0, 0), linha, font=f2)[2]
        d.text(((L - w2) / 2, A / 2 + 20 + i * 52), linha, font=f2,
               fill=(150, 150, 162))
    for _ in range(int(segundos * FPS)):
        yield base


def rodape(im, texto):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONTE_REG, 30)
    w = d.textbbox((0, 0), texto, font=f)[2]
    d.rectangle([(L - w) / 2 - 18, A - 76, (L + w) / 2 + 18, A - 24],
                fill=(0, 0, 0))
    d.text(((L - w) / 2, A - 68), texto, font=f, fill=(225, 225, 232))
    return im


ETIQUETA_A = "A. FUNDO DESFOCADO   |   111 das 353 fotos sao verticais"
ETIQUETA_B = "B. COLAGEM   |   entram uma a uma e ficam"
ETIQUETA_C = "C. RAJADA   |   5 fotogramas por foto, 0,2 s cada"
ETIQUETA_D = "D. PILHA   |   caem umas sobre as outras e ficam"


# ----------------------------------------------------------------- A
def trat_fundo_desfocado(fotos, seg_por_foto=4.4, fade=0.8):
    """Vertical ao centro, e o fundo e a propria foto ampliada e desfocada."""
    ALTURA_BASE = 1004
    ZOOM = 0.05
    quadros = int(seg_por_foto * FPS)
    q_fade = int(fade * FPS)

    preparadas = []
    for caminho in fotos:
        im = abrir(caminho)
        fundo = cobrir(im, L, A).filter(ImageFilter.GaussianBlur(46))
        fundo = Image.blend(Image.new("RGB", (L, A), (0, 0, 0)), fundo, 0.55)
        # Preparada UMA VEZ no tamanho maximo. Depois so encolhe, nunca cresce.
        alt_max = int(round(ALTURA_BASE * (1 + ZOOM)))
        larg_max = max(1, round(im.width * alt_max / im.height))
        frente = im.resize((larg_max, alt_max), Image.LANCZOS).convert("RGBA")
        preparadas.append((frente, fundo, alt_max))

    anterior = None
    for i, (frente, fundo, alt_max) in enumerate(preparadas):
        for q in range(quadros):
            t = q / quadros
            escala = (ALTURA_BASE * (1 + ZOOM * t)) / alt_max
            tela = fundo.convert("RGBA")
            compor(tela, frente, L / 2.0, A / 2.0, escala)
            quadro = tela.convert("RGB")
            if i > 0 and q < q_fade and anterior is not None:
                quadro = Image.blend(anterior, quadro, q / q_fade)
            yield rodape(quadro, ETIQUETA_A)
        tela = fundo.convert("RGBA")
        compor(tela, frente, L / 2.0, A / 2.0,
               (ALTURA_BASE * (1 + ZOOM)) / alt_max)
        anterior = tela.convert("RGB")


# ----------------------------------------------------------------- B
POSICOES = [
    (540, 330, 760, -3.5),
    (1330, 300, 660, 2.5),
    (560, 800, 600, 2.0),
    (1180, 760, 540, -2.0),
    (1610, 640, 400, 4.0),
]


def trat_colagem(fotos, entrada=0.62, total_s=11.0):
    """As fotos entram uma a uma e FICAM. No fim o quadro inteiro respira."""
    ENTRA = 1.14      # escala de chegada, antes de assentar
    RESPIRA = 1.030   # zoom lento do conjunto no fim
    total = int(total_s * FPS)

    preparadas = []
    for caminho, (cx, cy, larg, rot) in zip(fotos, POSICOES):
        im = abrir(caminho, 1600)
        alt = round(larg * im.height / im.width)
        im = moldurar(im.resize((larg, alt), Image.LANCZOS), 8)
        # Preparada no tamanho MAXIMO (chegada x respiracao) e ja rodada.
        maxf = ENTRA * RESPIRA
        grande = im.resize((round(im.width * maxf), round(im.height * maxf)),
                           Image.LANCZOS).convert("RGBA")
        grande = grande.rotate(rot, resample=Image.BICUBIC, expand=True)
        preparadas.append((grande, cx, cy, maxf))

    fundo = cobrir(abrir(fotos[0], 900), L, A)
    fundo = fundo.filter(ImageFilter.GaussianBlur(60))
    fundo = Image.blend(Image.new("RGB", (L, A), (8, 8, 10)), fundo, 0.28)

    for q in range(total):
        t = q / FPS
        tf = q / total
        respirar = 1.0 + (RESPIRA - 1.0) * suave(max(0.0, (tf - 0.45) / 0.55))
        tela = fundo.convert("RGBA")
        for i, (sprite, cx, cy, maxf) in enumerate(preparadas):
            inicio = i * entrada
            if t < inicio:
                continue
            p = suave((t - inicio) / 0.32)
            escala = (ENTRA - (ENTRA - 1.0) * p) * respirar / maxf
            dx = L / 2.0 + (cx - L / 2.0) * respirar
            dy = A / 2.0 + (cy - A / 2.0) * respirar
            compor(tela, sprite, dx, dy, escala, alfa=min(1.0, p * 1.4))
        yield rodape(tela.convert("RGB"), ETIQUETA_B)


# ----------------------------------------------------------------- C
def trat_rajada(fotos, quadros_por_foto=5):
    """Stop-motion. 5 fotogramas por foto, corte seco, sem movimento nenhum.

    A versao anterior alternava a escala entre 1,0 e 1,025 para dar energia.
    Era isso o tremor nesta parte, e foi removido.
    """
    for caminho in fotos:
        im = abrir(caminho, 2400)
        quadro = rodape(cobrir(im, L, A), ETIQUETA_C)
        for _ in range(quadros_por_foto):
            yield quadro


# ----------------------------------------------------------------- D
def trat_pilha(fotos, cadencia=0.85, cauda_s=2.6):
    """As fotos caem umas sobre as outras, tortas, e acumulam-se."""
    ENTRA = 1.16
    angulos = [-9, 6, -4, 11, -7, 3, -12, 8]
    total = int((len(fotos) * cadencia + cauda_s) * FPS)

    preparadas = []
    for i, caminho in enumerate(fotos):
        im = abrir(caminho, 1600)
        larg = 880
        alt = round(larg * im.height / im.width)
        im = moldurar(im.resize((larg, alt), Image.LANCZOS), 9)
        grande = im.resize((round(im.width * ENTRA), round(im.height * ENTRA)),
                           Image.LANCZOS).convert("RGBA")
        grande = grande.rotate(angulos[i % len(angulos)],
                               resample=Image.BICUBIC, expand=True)
        preparadas.append(grande)

    fundo = Image.new("RGB", (L, A), (10, 10, 12))
    for q in range(total):
        t = q / FPS
        tf = q / total
        afastar = 1.0 - 0.10 * suave(max(0.0, (tf - 0.7) / 0.3))
        tela = fundo.convert("RGBA")
        for i, sprite in enumerate(preparadas):
            inicio = i * cadencia
            if t < inicio:
                continue
            p = suave((t - inicio) / 0.40)
            escala = (ENTRA - (ENTRA - 1.0) * p) * afastar / ENTRA
            desvio_y = (1.0 - p) * -130.0
            dx = L / 2.0 + math.sin(i * 1.7) * 90.0 * afastar
            dy = A / 2.0 + math.cos(i * 2.1) * 46.0 * afastar + desvio_y
            compor(tela, sprite, dx, dy, escala, alfa=min(1.0, p * 1.5))
        yield rodape(tela.convert("RGB"), ETIQUETA_D)


def main():
    ff = ffmpeg()
    os.makedirs(SAIDA, exist_ok=True)
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = {r["id"]: r for r in csv.DictReader(fh)}

    def caminhos(ids):
        return [inv[i]["caminho"] for i in ids if i in inv]

    v, c, r, p = (caminhos(VERTICAIS), caminhos(COLAGEM),
                  caminhos(RAJADA), caminhos(PILHA))
    print("Fotos: A=%d  B=%d  C=%d  D=%d" % (len(v), len(c), len(r), len(p)))
    if not (v and c and r and p):
        sys.exit("Faltam fotos no inventario para algum dos tratamentos.")

    final = os.path.join(SAIDA, "teste_estilos.mp4")
    proc = subprocess.Popen(
        [ff, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (L, A),
         "-framerate", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", final],
        stdin=subprocess.PIPE)

    sequencia = [
        cartao("A. FUNDO DESFOCADO",
               "a foto vertical deixa de ter barras pretas\n"
               "o fundo passa a ser a propria foto, ampliada e desfocada"),
        trat_fundo_desfocado(v),
        cartao("B. COLAGEM",
               "as fotos entram uma a uma e ficam\n"
               "no fim o quadro inteiro respira"),
        trat_colagem(c),
        cartao("C. RAJADA",
               "stop-motion: 5 fotogramas por foto, corte seco\n"
               "para amigos, viagens, festas"),
        trat_rajada(r),
        cartao("D. PILHA",
               "caem umas sobre as outras, tortas\n"
               "nada desaparece, o monte cresce"),
        trat_pilha(p),
    ]

    n = 0
    for gerador in sequencia:
        for quadro in gerador:
            proc.stdin.write(quadro.tobytes())
            n += 1
            if n % 100 == 0:
                print("  %d fotogramas" % n, end="\r")
    proc.stdin.close()
    proc.wait()
    print("\nEscrito: %s   (%d fotogramas, %.1f s)" % (final, n, n / FPS))


if __name__ == "__main__":
    main()
