# -*- coding: utf-8 -*-
"""Deteta corridas de fotos seguidas na timeline da mae da Clara.

Uma "corrida" e um grupo de fotos consecutivas que o espectador le como sendo
do mesmo assunto. Sao elas que cansam quando sao longas, e sao as candidatas
naturais a rajada.

CORRECAO IMPORTANTE face a primeira versao deste calculo. Eu cortava as
corridas apenas quando aparecia uma legenda nova. Isso estava errado por duas
razoes:

  1. Nao cortava nos cartoes de ecra inteiro. Resultado: as 21 fotos sem
     legenda que vem depois do cartao "Cumplicidades" herdavam a legenda da
     foto anterior ao cartao, e apareciam como "21 fotos do Baile de
     Finalistas". Nao sao. Sao 21 fotos do casal, sem legenda nenhuma.
  2. Nao distinguia corridas SEM legenda de corridas COM uma legenda so. Sao
     coisas diferentes: um bloco sem legenda nenhuma e uma sequencia livre,
     um bloco com uma legenda e um assunto declarado.

Agora corta em: cartao, mudanca de legenda, mudanca de seccao dela, e salto
grande no tempo.

Uso:  py -3.11 scripts/corridas.py
      py -3.11 scripts/corridas.py --min 3
"""
import csv
import os
import sys

import excluidas

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")

SECCOES = [
    (0.0, 20.4, "Fanfarra"),
    (20.4, 498.0, "Clara"),
    (498.0, 659.0, "Familia"),
    (659.0, 695.0, "Amigos e colegas"),
    (695.0, 761.0, "Colegas de trabalho (dela)"),
    (761.0, 1020.0, "Tiago"),
    (1020.0, 1071.0, "Colegas de trabalho (dele)"),
    (1071.0, 1228.0, "O encontro"),
    (1228.0, 1401.0, "Cumplicidades"),
    (1401.0, 9999.0, "The End"),
]


def seccao(t):
    for ini, fim, nome in SECCOES:
        if ini <= t < fim:
            return nome
    return ""


def mmss(s):
    s = float(s)
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def carregar():
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    video = sorted([r for r in linhas if r["faixa"] == "video"],
                   key=lambda r: float(r["inicio_s"]))
    textos = [r for r in linhas if r["faixa"] == "texto" and r["texto_ecra"]]
    for r in video:
        ini, fim = float(r["inicio_s"]), float(r["fim_s"])
        legs = [t["texto_ecra"] for t in textos
                if ini <= float(t["inicio_s"]) < fim]
        r["_legenda"] = legs[0] if legs else ""
        r["_seccao"] = seccao(ini)
    # As fotos que o Tiago mandou tirar saem aqui, uma vez so, para a v1b
    # e a v1c herdarem a decisao sem ter de a repetir. Ver excluidas.py.
    video = [r for r in video if excluidas.entra(r.get("ficheiro"))]
    return video


def detetar(video):
    corridas, atual = [], []
    for r in video:
        if r["tipo"] != "foto":
            # Cartao ou video de ecra inteiro fecha sempre a corrida. Isto era
            # o que faltava e o que produziu o numero errado.
            if atual:
                corridas.append(atual)
                atual = []
            continue
        if atual:
            anterior = atual[-1]
            quebra = (r["_seccao"] != anterior["_seccao"]
                      or (r["_legenda"] and r["_legenda"] != anterior["_legenda"]))
            if quebra:
                corridas.append(atual)
                atual = []
        atual.append(r)
    if atual:
        corridas.append(atual)
    return corridas


def main():
    minimo = 4
    if "--min" in sys.argv:
        minimo = int(sys.argv[sys.argv.index("--min") + 1])

    video = carregar()
    corridas = detetar(video)
    longas = [c for c in corridas if len(c) >= minimo]

    fotos = sum(len(c) for c in corridas)
    print("Fotos na timeline: %d   |   corridas: %d   |   com %d ou mais: %d"
          % (fotos, len(corridas), minimo, len(longas)))
    print()

    dentro = sum(len(c) for c in longas)
    segundos = sum(float(r["duracao_s"]) for c in longas for r in c)
    print("Nas corridas longas: %d fotos, %.0f s na versao dela" % (dentro, segundos))
    print()

    print("%-4s %-7s %-7s %-28s %s" % ("N", "ENTRA", "DURA", "SECCAO", "ASSUNTO"))
    print("-" * 100)
    for c in sorted(longas, key=len, reverse=True):
        dur = sum(float(r["duracao_s"]) for r in c)
        assunto = c[0]["_legenda"] or "(sem legenda nenhuma)"
        print("%-4d %-7s %5.0fs  %-28s %s"
              % (len(c), mmss(c[0]["inicio_s"]), dur, c[0]["_seccao"],
                 assunto.replace("\n", " ")[:52]))

    print()
    print("SEM LEGENDA contra COM LEGENDA")
    sem = [c for c in longas if not c[0]["_legenda"]]
    com = [c for c in longas if c[0]["_legenda"]]
    print("  sem legenda: %d corridas, %d fotos, %.0f s"
          % (len(sem), sum(len(c) for c in sem),
             sum(float(r["duracao_s"]) for c in sem for r in c)))
    print("  com legenda: %d corridas, %d fotos, %.0f s"
          % (len(com), sum(len(c) for c in com),
             sum(float(r["duracao_s"]) for c in com for r in c)))


if __name__ == "__main__":
    main()
