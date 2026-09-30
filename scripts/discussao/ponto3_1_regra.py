# -*- coding: utf-8 -*-
"""Previa do ponto 3.1 (decisao 094): a regra geral de subida e descida das musicas, hoje contra o
futuro, em quatro trocas. Nao muda nada; escreve em saida/discussao/ponto3_1/.

    py -3.11 scripts/discussao/ponto3_1_regra.py

HOJE: o render como esta (a que entra sobe sempre 1 s em linha recta, a que sai desce 2,2 s).
FUTURO: a que entra num inicio entra sem rampa; a que entra a meio sobe no mesmo tempo em que a
outra desce; curvas de potencia igual. As trocas encontram-se pelos nomes das musicas.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C      # noqa: E402

TROCAS = [  # (sai, entra, titulo)
    ("Mariah", "Lang Lang", "Mariah para Lang Lang"),
    ("Gilbert", "Baha Men", "Clair para Who Let The Dogs Out"),
    ("Já Sei Namorar", "Steppenwolf", "Já Sei Namorar para Born To Be Wild"),
    ("Queen", "Bachman", "Queen para Taking Care of Business"),
]


def main():
    pasta = C.pasta("ponto3_1")
    est = C.carregar()
    videos, saltadas = [], []
    for k, (sai, entra, titulo) in enumerate(TROCAS, 1):
        hoje = C.entradas_de_som(est)
        par = C.troca(hoje, sai, entra, obrigatoria=False)
        if par is None:
            saltadas.append(titulo)
            continue
        _a, b = par
        corte = b["quando"]
        base = os.path.join(pasta, "%d_%s" % (k, titulo.split(" para ")[0].replace(" ", "_")))
        C.excerto(C.CONSTRUIR_HOJE, hoje, corte, 4, 6, base + "_hoje.m4a")
        fut = C.aplicar_094(C.entradas_de_som(est))
        C.excerto(C.CONSTRUIR_FUTURO, fut, corte, 4, 6, base + "_futuro.m4a")
        videos.append(C.par_em_video(base + "_hoje.m4a", base + "_futuro.m4a", titulo,
                                     "como está", "regra nova", base + ".mp4"))
        print("%-40s corte aos %.2f do corpo" % (titulo, corte), flush=True)
    if saltadas:
        print("ficaram de fora:", ", ".join(saltadas))
    print("escrito", C.juntar_videos(videos, os.path.join(pasta, "ponto3_1_todas.mp4")))


if __name__ == "__main__":
    main()
