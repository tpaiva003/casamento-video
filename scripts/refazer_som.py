# -*- coding: utf-8 -*-
"""Refaz so o som de um filme ja desenhado, e junta-o outra vez, sem desenhar um fotograma.

PORQUE (4 de outubro, a madrugada do casamento): o desenho do filme leva 35 a 45 minutos e o som
uns dois. Quando o Tiago muda so uma passagem de musica (um fim de frase, uma marca que continua,
o tempo de uma descida), a imagem e a mesma: o data/montagens/<nome>.csv sai igual ao byte e so muda
o <nome>.som.csv. Este script parte do corpo que o render deixou em disco (_<nome>_corpo.mp4, so
imagem) e dos videos de abertura ja preparados (_<nome>_video0.mp4, ...), constroi o som pelas
funcoes do proprio render (som_do_ficheiro e construir_som) e faz a juncao com os mesmos comandos
do render.main(). O filme sai com nome novo, como todos os renders, e fica no data/renders.csv.

RECUSA-SE a trabalhar se o corpo em disco nao tiver a duracao da montagem de agora (a imagem mudou:
e preciso o render inteiro) ou se faltar algum video de abertura.

Uso:  py -3.11 scripts/refazer_som.py v3 [--cruzamento 4.0]
"""
import datetime
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402


def duracao(ff, caminho):
    sonda = os.path.join(os.path.dirname(ff), "ffprobe.exe")
    if not os.path.exists(sonda):
        sonda = "ffprobe"
    r = subprocess.run([sonda, "-v", "error", "-select_streams", "v:0", "-show_entries", "format=duration",
                        "-of", "csv=p=0", caminho], capture_output=True, text=True)
    return float((r.stdout or "0").strip() or 0)


def main():
    nome = sys.argv[1]
    if "--cruzamento" in sys.argv:
        render.CRUZAMENTO = float(sys.argv[sys.argv.index("--cruzamento") + 1])
    ff = render.ffmpeg()
    pasta = render.SAIDA
    estado = render.carregar_montagem(nome, None, falar=False)
    fim, resto, fanfarra = estado["fim"], estado["resto"], estado["fanfarra"]

    corpo = os.path.join(pasta, "_%s_corpo.mp4" % nome)
    if not os.path.exists(corpo):
        sys.exit("Nao ha corpo desenhado: %s. Faz o render inteiro." % corpo)
    d = duracao(ff, corpo)
    if abs(d - fim) > 0.25:
        sys.exit("O corpo em disco tem %.2f s e a montagem de agora tem %.2f s: a imagem mudou, "
                 "faz o render inteiro." % (d, fim))
    partes = []
    for n_v, _c in enumerate(fanfarra):
        fan = os.path.join(pasta, "_%s_video%d.mp4" % (nome, n_v))
        if not os.path.exists(fan):
            sys.exit("Falta o video de abertura ja preparado: %s. Faz o render inteiro." % fan)
        partes.append(fan)

    print("  a construir o som (cruzamento de %.1f s)" % render.CRUZAMENTO)
    som = os.path.join(pasta, "_%s_som_refeito.m4a" % nome)
    entradas = render.som_do_ficheiro(nome, fim)
    if entradas is None:
        sys.exit("A montagem %s nao traz %s.som.csv." % (nome, nome))
    for e in entradas:
        print("     %5.1f s  dura %5.1f s  %s" % (e["quando"], e["dura"], e["ficheiro"][:46]))
    if not render.construir_som(ff, entradas, fim, som, render.FADE_FIM_SOM):
        sys.exit("O som nao se construiu.")

    corpo_final = os.path.join(pasta, "_%s_corpo_som_refeito.mp4" % nome)
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", corpo, "-i", som, "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-ac", "2", "-ar", "48000",
                        "-shortest", corpo_final], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ERRO ao juntar o som ao corpo: %s" % (r.stderr or "")[-300:])
    partes.append(corpo_final)

    carimbo = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    final = render.caminho_do_final(pasta, "%s_%s" % (nome, carimbo), "")
    if len(partes) == 1:
        os.replace(partes[0], final)
    else:
        lista = os.path.join(pasta, "_%s_lista_refeito.txt" % nome)
        with open(lista, "w", encoding="utf-8") as fh:
            for p in partes:
                fh.write("file '%s'\n" % p.replace("\\", "/"))
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "concat", "-safe", "0", "-i", lista,
                            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            final], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("ERRO ao juntar: %s" % (r.stderr or "")[-300:])
    print("\nEscrito: %s" % final)
    render.registar_render(nome, final, "", False, len(resto) + len(fanfarra))


if __name__ == "__main__":
    main()
