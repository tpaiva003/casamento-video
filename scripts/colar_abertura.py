# -*- coding: utf-8 -*-
"""Cola os videos de abertura a frente de um corpo ja renderizado, como o render os cola.

PORQUE EXISTE: o render.py salta a fanfarra quando se lhe da --ate (linha 4275,
`if fanfarra and not ate`), portanto um render parcial da o corpo e mais nada. Eu mandei ao
Tiago duas "aberturas" que eram iguais ao byte, porque a unica diferenca estava nos videos
que nao la estavam. Isto repoe a parte que falta, com os MESMOS comandos do render, para o
troco que ele ve ser o troco que o filme tera.

Uso:  py -3.11 scripts/colar_abertura.py <montagem.csv> <corpo.mp4> <saida.mp4>
"""
import csv
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\casamento-video\scripts")
import render      # noqa: E402


def main():
    csv_montagem, corpo, saida = sys.argv[1], sys.argv[2], sys.argv[3]
    ff = render.ffmpeg()
    with open(csv_montagem, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    clips = [{"tipo": l["tipo"], "ficheiro": l["ficheiro"],
              "duracao_s": l["duracao_s"], "in_s": l.get("in_s", "")} for l in linhas]
    fanfarra, _resto = render.partir_em_fanfarra_e_corpo(clips)
    if not fanfarra:
        sys.exit("Esta montagem nao tem bloco inicial de videos")
    tmp = os.path.dirname(os.path.abspath(saida))
    partes = []
    for n_v, c in enumerate(fanfarra):
        origem, arranque = render.caminho_de_video(c.get("ficheiro") or "")
        if str(c.get("in_s") or "").strip():
            arranque = float(c["in_s"])
        if not origem:
            sys.exit("Nao encontrei o video %s" % c.get("ficheiro"))
        fan = os.path.join(tmp, "_fan_%d_%s.mp4"
                           % (n_v, os.path.splitext(os.path.basename(saida))[0]))
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-ss", "%.3f" % arranque,
                            "-t", "%.3f" % float(c["duracao_s"]),
                            "-i", origem,
                            "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,"
                                   "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1"
                                   % (render.L, render.A, render.L, render.A),
                            "-r", str(render.FPS), "-c:v", "libx264", "-crf", "20",
                            "-preset", "veryfast", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                            "-ar", "48000", fan], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("ffmpeg falhou no video %s:\n%s"
                     % (c.get("ficheiro"), (r.stderr or "")[-500:]))
        print("  video %d: %s  (%s s)" % (n_v + 1, os.path.basename(origem), c["duracao_s"]))
        partes.append(fan)
    partes.append(os.path.abspath(corpo))
    lista = os.path.join(tmp, "_lista_%s.txt" % os.path.splitext(os.path.basename(saida))[0])
    with open(lista, "w", encoding="utf-8") as fh:
        for p in partes:
            fh.write("file '%s'\n" % p.replace("\\", "/"))
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "concat", "-safe", "0", "-i", lista,
                        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                        saida], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg falhou ao juntar:\n%s" % (r.stderr or "")[-500:])
    print("Escrito:", saida)


main()
