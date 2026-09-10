# -*- coding: utf-8 -*-
"""Upscaling nao destrutivo das fotos que nao chegam para 1920x1080.

Garantias, por esta ordem de importancia:

1. O ORIGINAL NUNCA E TOCADO. Nada e escrito dentro de
   C:\\casamento-video-media\\trabalho\\. A saida vai para uma pasta irma,
   C:\\casamento-video-media\\upscaled\\, e o script recusa-se a correr se o
   destino cair dentro da pasta de trabalho.
2. Nada e reescrito. Se o ficheiro de destino ja existir, salta. Para refazer
   e preciso apagar a mano, ou usar --refazer.
3. Ampliar nao remove informacao. O que estraga uma foto ampliada e o
   sharpening a mais, que cria halos, e a recompressao. Por isso: lanczos
   sobre zscale, "cas" fraco (0.30) em vez de unsharp, e JPEG de qualidade 2,
   praticamente sem perda visivel.

Cadeia: zscale lanczos -> cas 0.30 -> mjpeg q2

Cada foto e ampliada apenas o necessario para encher 1920x1080, vezes uma
folga para o pan e zoom (por omissao 1.15). Nao ampliar alem do preciso e o
que mais protege a imagem: cada decimo a mais e mais suavidade e mais halo.

Uso:
    py -3.11 scripts/upscale.py              executa tudo o que falta
    py -3.11 scripts/upscale.py --simular    so diz o que faria
    py -3.11 scripts/upscale.py --amostra 6  faz so as 6 piores, para veres
    py -3.11 scripts/upscale.py --refazer    reescreve o que ja existe
"""
import csv
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TRABALHO = os.path.normcase(os.path.abspath(r"C:\casamento-video-media\trabalho"))
DESTINO = r"C:\casamento-video-media\upscaled"
COMPARACOES = r"C:\casamento-video-media\upscaled\_comparacoes"

LARGURA_ALVO, ALTURA_ALVO = 1920, 1080
FOLGA = 1.15      # margem para o pan e zoom nao ficar a puxar pixeis do nada
CAS = 0.30        # sharpening fraco. Acima de 0.5 comecam a aparecer halos.
QUALIDADE = 2     # escala mjpeg do ffmpeg, 2 e quase sem perda

FFMPEG = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    r"Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")


def encontrar_ffmpeg():
    if os.path.exists(FFMPEG):
        return FFMPEG
    from shutil import which
    achado = which("ffmpeg")
    if achado:
        return achado
    sys.exit("Nao encontrei o ffmpeg. Instala com: winget install --id Gyan.FFmpeg -e")


def nome_seguro(texto):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", texto).strip("_")[:60]


def proteger_destino():
    """Recusa correr se a saida cair dentro da pasta de trabalho."""
    d = os.path.normcase(os.path.abspath(DESTINO))
    if d == TRABALHO or d.startswith(TRABALHO + os.sep):
        sys.exit("RECUSADO: o destino cai dentro da pasta de trabalho. "
                 "Os originais nunca podem ser escritos.")


def alvo(larg, alt):
    """Dimensoes de saida: encher 1920x1080 vezes a folga, mantendo o aspeto."""
    fator = max(LARGURA_ALVO / larg, ALTURA_ALVO / alt) * FOLGA
    if fator <= 1.0:
        return None
    nl = int(round(larg * fator / 2)) * 2
    na = int(round(alt * fator / 2)) * 2
    return nl, na, fator


def ampliar(ffmpeg, origem, saida, nl, na):
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", origem,
        "-vf", "zscale=w=%d:h=%d:filter=lanczos,cas=strength=%.2f" % (nl, na, CAS),
        "-q:v", str(QUALIDADE),
        saida,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # zscale falha em alguns espacos de cor. Cai para swscale lanczos.
        cmd[cmd.index("-vf") + 1] = (
            "scale=%d:%d:flags=lanczos+accurate_rnd+full_chroma_int,"
            "cas=strength=%.2f" % (nl, na, CAS))
        r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or "").strip()


# O ffmpeg no Windows nao tem fontconfig, por isso o drawtext precisa do
# caminho explicito da fonte, com os dois pontos escapados dentro do filtro.
FONTE = "C\\:/Windows/Fonts/arial.ttf"


def comparacao(ffmpeg, origem, ampliada, saida, nl, na):
    """Lado a lado: original esticado a bruta, contra o nosso tratamento.

    O lado esquerdo e o que se veria se a foto fosse simplesmente esticada no
    Resolve, sem tratamento nenhum. Serve para julgar o ganho real, e tambem
    para apanhar halos, que sao o unico modo real de estragar a imagem.
    """
    tam = max(24, na // 25)
    legenda = ("drawtext=fontfile='%s':text='%%s':x=24:y=24:fontsize=%d:"
               "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=12"
               % (FONTE, tam))
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", origem, "-i", ampliada,
        "-filter_complex",
        "[0:v]scale=%d:%d:flags=neighbor,%s[a];[1:v]%s[b];[a][b]hstack=inputs=2"
        % (nl, na, legenda % "SEM TRATAMENTO", legenda % "TRATADO"),
        "-q:v", "3", saida,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  (comparacao falhou para %s: %s)"
              % (os.path.basename(saida), (r.stderr or "").strip()[:150]))
    return r.returncode == 0


def main():
    proteger_destino()
    ffmpeg = encontrar_ffmpeg()
    simular = "--simular" in sys.argv
    refazer = "--refazer" in sys.argv
    amostra = 0
    if "--amostra" in sys.argv:
        amostra = int(sys.argv[sys.argv.index("--amostra") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))

    trabalho = []
    for r in linhas:
        dims = alvo(int(r["largura"]), int(r["altura"]))
        if dims:
            trabalho.append((r, dims))
    trabalho.sort(key=lambda x: -x[1][2])

    if amostra:
        trabalho = trabalho[:amostra]

    os.makedirs(DESTINO, exist_ok=True)
    os.makedirs(COMPARACOES, exist_ok=True)

    print("Fotos a ampliar: %d de %d" % (len(trabalho), len(linhas)))
    print("Alvo: encher %dx%d com folga de %.0f%% para pan e zoom"
          % (LARGURA_ALVO, ALTURA_ALVO, (FOLGA - 1) * 100))
    print("Destino: %s" % DESTINO)
    print("Originais em %s: nao sao tocados." % TRABALHO)
    print()

    feitas = saltadas = falhadas = 0
    piores = trabalho[:6]

    for r, (nl, na, fator) in trabalho:
        nome = "%s__%s.jpg" % (r["id"], nome_seguro(os.path.splitext(r["ficheiro"])[0]))
        saida = os.path.join(DESTINO, nome)
        if os.path.exists(saida) and not refazer:
            saltadas += 1
            continue
        if simular:
            print("  [simulado] %s  %sx%s -> %dx%d  (%.2fx)"
                  % (r["ficheiro"][:44], r["largura"], r["altura"], nl, na, fator))
            feitas += 1
            continue
        ok, erro = ampliar(ffmpeg, r["caminho"], saida, nl, na)
        if ok:
            feitas += 1
            if (r, (nl, na, fator)) in piores:
                comparacao(ffmpeg, r["caminho"], saida,
                           os.path.join(COMPARACOES, nome), nl, na)
        else:
            falhadas += 1
            print("  FALHOU %s  (%s)" % (r["ficheiro"], erro[:120]))

    print()
    print("Ampliadas: %d   Ja existiam: %d   Falhadas: %d" % (feitas, saltadas, falhadas))
    if not simular and feitas:
        print("Comparacoes lado a lado das 6 piores em: %s" % COMPARACOES)


if __name__ == "__main__":
    main()
