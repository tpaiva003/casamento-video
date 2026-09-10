# -*- coding: utf-8 -*-
"""Teste em video da mecanica de rajada. Fecha o ponto D do DECISOES.md.

Produz um MP4 curto com duas partes, com as MESMAS fotos, para se comparar a
olho e nao a discutir:

  PARTE A, ritmo dela: uma foto de cada vez, 5 s, zoom lento, crossfade 1,5 s.
  PARTE B, esteira: as fotos entram pela direita e deslizam para a esquerda,
           acumulando-se. Duas ou tres visiveis ao mesmo tempo.

A pergunta que o teste tem de responder e se cada foto continua legivel numa
cortina com duas ou tres em simultaneo, e se o deslize cansa. Por isso o video
escreve no ecra os dois numeros que interessam: de quanto em quanto tempo
entra uma foto, e quanto tempo cada uma fica visivel.

Uso:  py -3.11 scripts/teste_rajada.py
"""
import csv
import os
import subprocess
import sys

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
SAIDA = r"C:\casamento-video-media\testes"

L, A, FPS = 1920, 1080, 25
FUNDO = (14, 14, 16)

# Parte A, ritmo dela
DUR_FOTO = 5.0
CROSSFADE = 1.5

# Parte B, esteira
ALTURA_FOTO = 860       # deixa margem em cima e em baixo
INTERVALO = 44          # espaco entre fotos
DUR_ESTEIRA = 18.0

FONTE = "C\\:/Windows/Fonts/arialbd.ttf"

# Escolhidas a mao do inventario: horizontais, resolucao a chegar, e do tipo de
# material a que a rajada se destina (viagens, festas, convivios).
ESCOLHIDAS = ["f0040", "f0042", "f0043", "f0083", "f0161", "f0163",
              "f0213", "f0216", "f0217", "f0222", "f0226", "f0057"]


def ffmpeg():
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Microsoft\WinGet\Packages"
                     r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                     r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
    if os.path.exists(p):
        return p
    from shutil import which
    return which("ffmpeg") or sys.exit("ffmpeg nao encontrado")


def correr(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ERRO ffmpeg:\n" + (r.stderr or "")[-1500:])
        sys.exit(1)


def escapar(texto):
    """O parser de filtros do ffmpeg parte em virgulas e dois pontos.

    Dentro de drawtext, os dois pontos e as virgulas do proprio texto tem de
    ir escapados, senao sao lidos como separadores de opcoes.
    """
    for de, para in (("\\", "\\\\"), (":", "\\:"), ("'", "\\'"),
                     (",", "\\,"), ("%", "\\%")):
        texto = texto.replace(de, para)
    return texto


def legenda(texto, tam=46, y=40):
    return ("drawtext=fontfile='%s':text='%s':x=(w-text_w)/2:y=%d:fontsize=%d:"
            "fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=18"
            % (FONTE, escapar(texto), y, tam))


def cartao(ff, texto, sub, saida, dur=3.0):
    correr([ff, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=0x0e0e10:s=%dx%d:d=%.2f:r=%d" % (L, A, dur, FPS),
            "-vf", "%s,%s" % (legenda(texto, 76, A // 2 - 90),
                              legenda(sub, 40, A // 2 + 30)),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", saida])


def clip_estilo_dela(ff, foto, saida):
    """Uma foto, 5 s, zoom lento ao centro. E o que ela fez 252 vezes.

    Nota sobre o zoompan: o parametro d e a duracao EM FOTOGRAMAS DE SAIDA por
    cada fotograma de entrada. Com -loop 1 entram 125 fotogramas, por isso d=125
    daria 125x125 fotogramas, ou seja 10 minutos em vez de 5 segundos. O correto
    e d=1, animando o zoom pelo indice do fotograma de saida, 'on'.
    """
    total = int(DUR_FOTO * FPS)
    correr([ff, "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-t", "%.2f" % DUR_FOTO, "-i", foto,
            "-vf",
            "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,"
            "zoompan=z='1+0.15*on/%d':d=1:x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':s=%dx%d:fps=%d,setsar=1"
            % (int(L * 1.4), int(A * 1.4), int(L * 1.4), int(A * 1.4),
               total, L, A, FPS),
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-r", str(FPS), saida])


def construir_esteira(fotos, destino):
    """Tira uma tira horizontal larga com todas as fotos lado a lado.

    Deixa 1920 px de folga nas duas pontas para a primeira entrar pela direita
    e a ultima sair pela esquerda, em vez de aparecerem ja no sitio.
    """
    imagens = []
    for caminho in fotos:
        with Image.open(caminho) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            larg = int(im.width * ALTURA_FOTO / im.height)
            imagens.append(im.resize((larg, ALTURA_FOTO), Image.LANCZOS))

    total = sum(i.width for i in imagens) + INTERVALO * (len(imagens) - 1)
    largura = total + 2 * L
    tira = Image.new("RGB", (largura, A), FUNDO)
    x = L
    for im in imagens:
        tira.paste(im, (x, (A - ALTURA_FOTO) // 2))
        x += im.width + INTERVALO
    tira.save(destino, "JPEG", quality=92)

    passo = (sum(i.width for i in imagens) / len(imagens)) + INTERVALO
    return largura, passo, sum(i.width for i in imagens) / len(imagens)


def main():
    ff = ffmpeg()
    os.makedirs(SAIDA, exist_ok=True)
    tmp = os.path.join(SAIDA, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = {r["id"]: r for r in csv.DictReader(fh)}

    fotos = [inv[i]["caminho"] for i in ESCOLHIDAS if i in inv]
    if len(fotos) < len(ESCOLHIDAS):
        print("Aviso: so encontrei %d das %d escolhidas" % (len(fotos), len(ESCOLHIDAS)))

    # ---- PARTE B primeiro, porque da os numeros que a Parte A vai anunciar.
    tira = os.path.join(tmp, "tira.jpg")
    largura, passo, larg_media = construir_esteira(fotos, tira)
    percurso = largura - L
    velocidade = percurso / DUR_ESTEIRA
    cadencia = passo / velocidade
    permanencia = (L + larg_media) / velocidade

    print("Esteira: %d fotos numa tira de %d px" % (len(fotos), largura))
    print("  entra uma foto a cada %.2f s" % cadencia)
    print("  cada foto fica visivel %.2f s" % permanencia)
    print("  a regra do briefing e nunca menos de 3 s: %s"
          % ("CUMPRE" if permanencia >= 3.0 else "NAO CUMPRE"))

    partes = []

    c0 = os.path.join(tmp, "c0.mp4")
    cartao(ff, "PARTE A", "ritmo do video original: uma foto de cada vez, 5 s", c0)
    partes.append(c0)

    for n, foto in enumerate(fotos[:6]):
        c = os.path.join(tmp, "a%02d.mp4" % n)
        clip_estilo_dela(ff, foto, c)
        partes.append(c)

    c1 = os.path.join(tmp, "c1.mp4")
    cartao(ff, "PARTE B", "esteira: as fotos acumulam-se e deslizam", c1)
    partes.append(c1)

    esteira = os.path.join(tmp, "esteira.mp4")
    info = ("entra uma foto a cada %.1f s   |   cada foto visivel %.1f s"
            % (cadencia, permanencia))
    correr([ff, "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-t", "%.2f" % DUR_ESTEIRA, "-i", tira,
            "-vf",
            "crop=%d:%d:x='(t/%.4f)*%d':y=0,%s,setsar=1"
            % (L, A, DUR_ESTEIRA, percurso, legenda(info, 34, A - 90)),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), esteira])
    partes.append(esteira)

    # Junta tudo. Parte A com crossfades de 1,5 s, como no original dela.
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w", encoding="utf-8") as fh:
        for p in partes:
            fh.write("file '%s'\n" % p.replace("\\", "/"))

    final = os.path.join(SAIDA, "teste_rajada.mp4")
    correr([ff, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", lista,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", final])

    print()
    print("Escrito: %s" % final)
    return cadencia, permanencia


if __name__ == "__main__":
    main()
