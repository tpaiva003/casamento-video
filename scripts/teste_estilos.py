# -*- coding: utf-8 -*-
"""Menu de tratamentos visuais, para o Tiago escolher a ver.

A primeira tentativa (esteira deslizante) foi rejeitada. Isto substitui-a por
quatro tratamentos distintos, construidos a partir das referencias que ele
mandou, cada um com o seu cartao a dizer o que e.

  A. FUNDO DESFOCADO  fotos verticais deixam de ter barras pretas: o fundo
                      passa a ser a propria foto ampliada e desfocada.
                      Resolve 111 das 353 fotos, que sao verticais.
  B. COLAGEM          varias fotos entram uma a uma e ficam, compondo um
                      quadro. No fim a composicao respira com um zoom lento.
  C. RAJADA           stop-motion a serio, 5 fotogramas por foto, corte seco.
  D. PILHA            as fotos caem uma sobre a outra, tortas, como polaroids
                      atiradas para cima de uma mesa.

Os fotogramas sao desenhados em Pillow e enviados por cano para o ffmpeg, sem
passar pelo disco. Da controlo total sobre movimento, rotacao e transparencia,
que os filtros do ffmpeg nao dao com esta comodidade.

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

# Escolhidas do inventario. As verticais sao o ponto do tratamento A.
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


def abrir(caminho, lado_max=2200):
    im = Image.open(caminho)
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail((lado_max, lado_max), Image.LANCZOS)
    return im


def cobrir(im, larg, alt):
    """Escala para encher larg x alt sem deformar, cortando o excesso."""
    f = max(larg / im.width, alt / im.height)
    novo = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))),
                     Image.LANCZOS)
    x = (novo.width - larg) // 2
    y = (novo.height - alt) // 2
    return novo.crop((x, y, x + larg, y + alt))


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


# ----------------------------------------------------------------- A
def trat_fundo_desfocado(fotos, seg_por_foto=4.4, fade=0.7):
    """Vertical ao centro, e o fundo e a propria foto ampliada e desfocada.

    Sem isto, uma foto vertical num ecra 16:9 fica com duas barras pretas que
    ocupam metade da largura. Com isto, o ecra fica cheio e a cor do fundo
    vem sempre da propria fotografia, portanto nunca destoa.
    """
    quadros_foto = int(seg_por_foto * FPS)
    quadros_fade = int(fade * FPS)
    camadas = []
    for caminho in fotos:
        im = abrir(caminho)
        fundo = cobrir(im, L, A).filter(ImageFilter.GaussianBlur(46))
        fundo = Image.blend(Image.new("RGB", (L, A), (0, 0, 0)), fundo, 0.55)
        camadas.append((im, fundo))

    for i, (im, fundo) in enumerate(camadas):
        for q in range(quadros_foto):
            t = q / quadros_foto
            zoom = 1.0 + 0.05 * t
            alt = int(1004 * zoom)
            larg = max(1, int(im.width * alt / im.height))
            frente = im.resize((larg, alt), Image.LANCZOS)
            quadro = fundo.copy()
            quadro.paste(frente, ((L - larg) // 2, (A - alt) // 2))
            if i > 0 and q < quadros_fade:
                a = q / quadros_fade
                ant = camadas[i - 1][1]
                quadro = Image.blend(ant, quadro, a)
            yield rodape(quadro, "A. FUNDO DESFOCADO   |   111 das 353 fotos sao verticais")


# ----------------------------------------------------------------- B
POSICOES = [
    (150, 120, 780, 0, -3.5),
    (980, 90, 700, 0, 2.5),
    (250, 560, 620, 0, 2.0),
    (900, 520, 560, 0, -2.0),
    (1400, 430, 420, 0, 4.0),
]


def trat_colagem(fotos, entrada=0.62, total_s=11.0):
    """As fotos entram uma a uma e FICAM. No fim o quadro inteiro respira.

    E a diferenca em relacao a esteira que nao resultou: aqui nada sai do
    ecra, o que se ve e um quadro a compor-se.
    """
    total = int(total_s * FPS)
    preparadas = []
    for caminho, (px, py, pw, _ph, rot) in zip(fotos, POSICOES):
        im = abrir(caminho, 1400)
        alt = int(pw * im.height / im.width)
        im = im.resize((pw, alt), Image.LANCZOS)
        moldura = Image.new("RGB", (pw + 16, alt + 16), (238, 238, 240))
        moldura.paste(im, (8, 8))
        preparadas.append((moldura, px, py, rot))

    base_fundo = cobrir(abrir(fotos[0], 900), L, A)
    base_fundo = base_fundo.filter(ImageFilter.GaussianBlur(60))
    base_fundo = Image.blend(Image.new("RGB", (L, A), (8, 8, 10)), base_fundo, 0.28)

    for q in range(total):
        t = q / FPS
        tf = q / total
        respirar = 1.0 + 0.035 * suave(max(0.0, (tf - 0.45) / 0.55))
        quadro = base_fundo.copy()
        capa = Image.new("RGBA", (L, A), (0, 0, 0, 0))
        for i, (im, px, py, rot) in enumerate(preparadas):
            inicio = i * entrada
            if t < inicio:
                continue
            p = suave((t - inicio) / 0.3)
            escala = (1.14 - 0.14 * p) * respirar
            w = max(1, int(im.width * escala))
            h = max(1, int(im.height * escala))
            peca = im.resize((w, h), Image.LANCZOS).convert("RGBA")
            peca = peca.rotate(rot, resample=Image.BICUBIC, expand=True)
            if p < 1:
                alfa = peca.split()[3].point(lambda v: int(v * p))
                peca.putalpha(alfa)
            cx = px + im.width / 2
            cy = py + im.height / 2
            cx = L / 2 + (cx - L / 2) * respirar
            cy = A / 2 + (cy - A / 2) * respirar
            capa.alpha_composite(peca, (int(cx - peca.width / 2),
                                        int(cy - peca.height / 2)))
        quadro = Image.alpha_composite(quadro.convert("RGBA"), capa).convert("RGB")
        yield rodape(quadro, "B. COLAGEM   |   entram uma a uma e ficam")


# ----------------------------------------------------------------- C
def trat_rajada(fotos, quadros_por_foto=5):
    """Stop-motion a serio. 5 fotogramas por foto, ou seja 0,2 s. Corte seco.

    Uma leve variacao de escala a alternar da a energia de fotografia batida,
    em vez de parecer um erro de reproducao.
    """
    for i, caminho in enumerate(fotos):
        im = abrir(caminho, 2000)
        escala = 1.0 if i % 2 == 0 else 1.025
        quadro = cobrir(im, int(L * escala), int(A * escala))
        if escala != 1.0:
            x = (quadro.width - L) // 2
            y = (quadro.height - A) // 2
            quadro = quadro.crop((x, y, x + L, y + A))
        quadro = rodape(quadro.copy(),
                        "C. RAJADA   |   5 fotogramas por foto, 0,2 s cada")
        for _ in range(quadros_por_foto):
            yield quadro


# ----------------------------------------------------------------- D
def trat_pilha(fotos, cadencia=0.85, cauda_s=2.4):
    """As fotos caem uma sobre a outra, tortas, e acumulam-se.

    E o "photo roll": nada desaparece, o monte cresce. No fim afasta-se um
    pouco para se ver o conjunto.
    """
    angulos = [-9, 6, -4, 11, -7, 3, -12, 8]
    total = int((len(fotos) * cadencia + cauda_s) * FPS)
    preparadas = []
    for i, caminho in enumerate(fotos):
        im = abrir(caminho, 1300)
        larg = 880
        alt = int(larg * im.height / im.width)
        im = im.resize((larg, alt), Image.LANCZOS)
        moldura = Image.new("RGB", (larg + 18, alt + 18), (240, 240, 242))
        moldura.paste(im, (9, 9))
        preparadas.append((moldura, angulos[i % len(angulos)]))

    fundo = Image.new("RGB", (L, A), (10, 10, 12))
    for q in range(total):
        t = q / FPS
        tf = q / total
        afastar = 1.0 - 0.10 * suave(max(0.0, (tf - 0.7) / 0.3))
        quadro = fundo.copy().convert("RGBA")
        for i, (im, ang) in enumerate(preparadas):
            inicio = i * cadencia
            if t < inicio:
                continue
            p = suave((t - inicio) / 0.38)
            escala = (1.16 - 0.16 * p) * afastar
            desvio_y = int((1 - p) * -130)
            w = max(1, int(im.width * escala))
            h = max(1, int(im.height * escala))
            peca = im.resize((w, h), Image.LANCZOS).convert("RGBA")
            peca = peca.rotate(ang, resample=Image.BICUBIC, expand=True)
            if p < 1:
                alfa = peca.split()[3].point(lambda v: int(v * p))
                peca.putalpha(alfa)
            # Espalha ligeiramente o monte para nao ficar tudo em cima do mesmo
            dx = int(math.sin(i * 1.7) * 90 * afastar)
            dy = int(math.cos(i * 2.1) * 46 * afastar)
            quadro.alpha_composite(peca, ((L - peca.width) // 2 + dx,
                                          (A - peca.height) // 2 + dy + desvio_y))
        yield rodape(quadro.convert("RGB"),
                     "D. PILHA   |   caem umas sobre as outras e ficam")


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
         "-c:v", "libx264", "-crf", "19", "-preset", "medium",
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
