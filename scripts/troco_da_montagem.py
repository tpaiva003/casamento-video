# -*- coding: utf-8 -*-
"""Recorta um troco de uma montagem ja gerada, com o som acertado, para renderizar so ele.

PORQUE: o render.py so sabe cortar pelo principio (--ate). Para o Tiago ver o FIM do filme
sem esperar meia hora, o troco tem de sair para uma montagem a parte. O relogio do
v3.som.csv comeca onde os videos de abertura acabam, por isso cortar a cabeca obriga a
andar com o som para tras na mesma medida, e a faixa que atravessa o corte entra mais
adiante no ficheiro dela.

O corpo do render tira o seu zero do inicio_s do primeiro clip que sobra, por isso o CSV
dos clips vai como esta, sem tocar nos tempos.

Uso:  py -3.11 scripts/troco_da_montagem.py v3 173 <pasta_destino> <nome_novo>
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = r"C:\casamento-video"
MONTAGENS = os.path.join(REPO, "data", "montagens")


def main():
    nome, primeiro, destino, novo = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(MONTAGENS, nome + ".csv"), encoding="utf-8-sig", newline="") as fh:
        campos = csv.DictReader(fh).fieldnames
    with open(os.path.join(MONTAGENS, nome + ".csv"), encoding="utf-8-sig", newline="") as fh:
        clips = list(csv.DictReader(fh))

    # O desvio de origem: o primeiro clip que nao e video do bloco inicial.
    k = 0
    while k < len(clips) and clips[k]["tipo"] == "video":
        k += 1
    desvio_antigo = float(clips[k]["inicio_s"])

    fica = [c for c in clips if int(c["ordem"]) >= primeiro]
    if not fica:
        sys.exit("Nao sobrou nenhum clip a partir do %d" % primeiro)
    desvio_novo = float(fica[0]["inicio_s"])
    andar = desvio_novo - desvio_antigo
    print("troco: clips %s a %s, de %.1f s a %.1f s do filme (%.1f s)"
          % (fica[0]["ordem"], fica[-1]["ordem"], desvio_novo,
             max(float(c["fim_s"]) for c in fica),
             max(float(c["fim_s"]) for c in fica) - desvio_novo))
    print("o som anda %.2f s para tras" % andar)

    with open(os.path.join(destino, novo + ".csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for c in fica:
            w.writerow(c)

    caminho_som = os.path.join(MONTAGENS, nome + ".som.csv")
    if not os.path.exists(caminho_som):
        print("sem som para acertar")
        return
    with open(caminho_som, encoding="utf-8-sig", newline="") as fh:
        leitor = csv.DictReader(fh)
        campos_som, faixas = leitor.fieldnames, list(leitor)
    saida = []
    for r in faixas:
        quando = float(r["quando_s"]) - andar
        dura = float(r["dura_s"])
        in_s = float(r["in_s"] or 0)
        if quando + dura <= 0.05:
            continue                      # acabou antes do troco comecar
        if quando < 0:                    # atravessa o corte: entra mais adiante
            in_s += -quando
            dura += quando
            quando = 0.0
        if dura <= 0.4:
            continue
        novo_r = dict(r)
        novo_r["quando_s"] = "%.2f" % quando
        novo_r["in_s"] = "%.2f" % in_s
        novo_r["dura_s"] = "%.2f" % dura
        saida.append(novo_r)
        print("  %6.1f s  dura %5.1f s  entra aos %6.1f s de %s"
              % (quando, dura, in_s, r["ficheiro"][:44]))
    with open(os.path.join(destino, novo + ".som.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos_som)
        w.writeheader()
        for r in saida:
            w.writerow(r)
    print("Escritos em", destino)


main()
