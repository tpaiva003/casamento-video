# -*- coding: utf-8 -*-
"""Previa do ponto 3.2 (decisao 095): os pontos de entrada de sete musicas, hoje contra o futuro,
os dois ja com a regra da 094. Nao muda nada; escreve em saida/discussao/ponto3_2/.

    py -3.11 scripts/discussao/ponto3_2_entradas.py

Cada marca encontra-se pela musica e pelo ponto de entrada de hoje (comum.ENTRADAS_095). Se o
numero novo ja estiver na Mesa, hoje e futuro saem iguais (e hoje tambem conta a entrada num ataque
como inicio); se a marca tiver outro numero, o script avisa e salta-a, e diz no fim quais saltou.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C      # noqa: E402

ANTES_DEPOIS = {"Já Sei Namorar": (3, 8), "Inês Homem de Melo": (4, 7), "Bachman": (4, 7), "Filhos Do": (4, 7)}


def virgula(x):
    return ("%.2f" % x).rstrip("0").rstrip(".").replace(".", ",")


def main():
    pasta = C.pasta("ponto3_2")
    est = C.carregar()
    videos, saltadas = [], []
    for k, linha in enumerate(C.ENTRADAS_095, 1):
        prefixo, titulo, in_hoje, _in_novo, _ataque = linha
        hoje = C.entradas_de_som(est)
        e = C.marca_095(hoje, linha)
        if e is None:
            saltadas.append(titulo)
            continue
        in_novo = C.novo_095(hoje, linha)
        t = e["quando"]
        antes, depois = ANTES_DEPOIS.get(prefixo, (4, 6))
        base = os.path.join(pasta, "%d_%s" % (k, titulo.split(",")[0].replace(" ", "_")))
        C.aplicar_094(hoje, C.ataques_ja_escritos(hoje))
        C.excerto(C.CONSTRUIR_FUTURO, hoje, t, antes, depois, base + "_hoje.m4a")
        fut = C.entradas_de_som(est)
        ataques = C.aplicar_095(fut)
        C.aplicar_094(fut, ataques)
        C.excerto(C.CONSTRUIR_FUTURO, fut, t, antes, depois, base + "_futuro.m4a")
        videos.append(C.par_em_video(base + "_hoje.m4a", base + "_futuro.m4a", titulo,
                                     "entra aos %s s" % virgula(e["in_s"]), "entra aos %s s" % virgula(in_novo),
                                     base + ".mp4"))
        print("%-26s aos %.2f do corpo: entra aos %s s, passa a %s s" % (titulo, t, virgula(e["in_s"]), virgula(in_novo)),
              flush=True)
    if saltadas:
        print("ficaram de fora:", ", ".join(saltadas))
    print("escrito", C.juntar_videos(videos, os.path.join(pasta, "ponto3_2_todas.mp4")))


if __name__ == "__main__":
    main()
