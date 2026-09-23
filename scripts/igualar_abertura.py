# -*- coding: utf-8 -*-
"""Copia os dois videos de abertura com o som levado ao nivel da musica, por GANHO DIRECTO.

PORQUE EXISTE (decisao 084): a fanfarra da Fox media -30,4 LUFS e a intro da Marvel -49,5,
contra os -21,9 a que a musica do filme sai depois do render. O filme e PROJECTADO com as
colunas do DJ, e quem esta na mesa poe um volume para o filme inteiro: um desnivel de 27,6 dB
dentro do filme nao se corrige na sala. Ou a fanfarra que existe para calar a sala nao cala
ninguem, ou a Mariah entra a seguir 27 dB acima e leva as pessoas do lugar.

E o argumento que fechou a questao nao e tecnico: na copia que a mae da Clara usou, a mesma
fanfarra estava a -9,3 LUFS, treze decibeis ACIMA da musica. O silencio de hoje nao e escolha
de ninguem, e um acidente do ficheiro HD que o Tiago largou na pasta.

GANHO DIRECTO E NAO loudnorm. O loudnorm comprime quando o alcance e maior do que o alvo:
medido, levava a intro de LRA 18,2 para 12,5, e o alcance da intro e a subida do quase-silencio
ate as letras, que e precisamente o que ele mandou refazer tres vezes. O ganho move o nivel e
deixa a forma quieta. A imagem nao se toca, -c:v copy.

Os originais nunca sao tocados: as copias vao para gerados/som_igualado/.

Uso:  py -3.11 scripts/igualar_abertura.py
      py -3.11 scripts/igualar_abertura.py --alvo -21.9
"""
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render      # noqa: E402

DESTINO = r"C:\casamento-video-media\gerados\som_igualado"
# O NIVEL DA MUSICA MEDIDO A SAIDA DO RENDER, e nao os -23 do loudnorm: a opcao `level` do
# alimiter multiplica a saida por 1/0,94, que sao mais 0,54 dB (render.py, construir_som).
ALVO = -21.9
NOMES = ["20th Century Fox Intro HD.mp4", "intro_clara_tiago_5.mp4"]
SUFIXO = " igualado"


def medir(ff, caminho):
    """(LUFS integrado, true peak) do ficheiro, pela analise do loudnorm."""
    r = subprocess.run(
        [ff, "-hide_banner", "-i", caminho, "-af",
         "loudnorm=I=-23:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    texto = (r.stderr or "") + (r.stdout or "")
    m = re.findall(r"\{[^{}]*input_i[^{}]*\}", texto, re.S)
    if not m:
        sys.exit("Nao consegui medir %s:\n%s" % (caminho, texto[-800:]))
    d = json.loads(m[-1])
    return float(d["input_i"]), float(d["input_tp"])


def main():
    alvo = float(sys.argv[sys.argv.index("--alvo") + 1]) if "--alvo" in sys.argv else ALVO
    ff = render.ffmpeg()
    os.makedirs(DESTINO, exist_ok=True)
    for nome in NOMES:
        origem, _arranque = render.caminho_de_video(nome)
        if not origem:
            sys.exit("Nao encontrei o video %s" % nome)
        base, ext = os.path.splitext(nome)
        saida = os.path.join(DESTINO, base + SUFIXO + ext)
        lufs, tp = medir(ff, origem)
        ganho = alvo - lufs
        print(nome)
        print("  medido: %.2f LUFS, true peak %.2f dBTP" % (lufs, tp))
        print("  ganho para %.1f LUFS: %+.2f dB, true peak previsto %.2f dBTP"
              % (alvo, ganho, tp + ganho))
        if tp + ganho > -0.5:
            sys.exit("  O true peak passaria de -0,5 dBTP e ia clipar. Nao escrevi nada.")
        if os.path.exists(saida):
            print("  ja existe, nao escrevi por cima:", saida)
            continue
        r = subprocess.run(
            [ff, "-hide_banner", "-y", "-i", origem, "-map", "0:v:0", "-map", "0:a:0",
             "-c:v", "copy", "-af", "volume=%.2fdB" % ganho,
             "-c:a", "aac", "-b:a", "192k", saida],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            sys.exit("ffmpeg falhou em %s:\n%s" % (nome, (r.stderr or "")[-900:]))
        lufs2, tp2 = medir(ff, saida)
        print("  depois:  %.2f LUFS, true peak %.2f dBTP" % (lufs2, tp2))
        print("  escrito:", saida)


main()
