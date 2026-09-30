# -*- coding: utf-8 -*-
"""A revisao do ponto 3.3 (decisao 096): que trocas continuam certas e quais e preciso medir outra vez.

    py -3.11 scripts/discussao/ponto3_3_frases.py [--so-dizer]

UMA SO FONTE, a do montar e do render: data/fins_de_frase.csv, uma linha por troca aprovada, com o
segundo do ficheiro em que a musica que sai chegava ao corte quando foi medida (no_corte) e a entrada
da que entra (entra_in). Um fim de frase e um sitio da musica: se a ordem, as duracoes, as entradas ou
as fotos mudarem, a musica chega ao corte noutro sitio e o fim de frase certo passa a ser outro. Antes
do render final, e depois de fotos novas ou de mudancas na montagem, corre-se isto (o Tiago, ao
aprovar: "este fluxo tera de ser revisto antes de fazer o render final ou com novas fotos").

As que mudaram medem-se outra vez com o scripts/discussao/medir_troca.py (um agente analisa, outro
verifica, sem escrever letras de cancoes), e a linha do CSV e substituida pela medida nova.

Sem --so-dizer, faz para cada troca certa um par de sons: a descer no corte (como era antes da 096)
contra o fim de frase aprovado, para lhe mostrar. Nao muda nada; escreve em saida/discussao/ponto3_3/.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C      # noqa: E402

FINS = os.path.join(C.REPO, "data", "fins_de_frase.csv")
TOLERANCIA_S = 0.05


def main():
    so_dizer = "--so-dizer" in sys.argv
    linhas = list(csv.DictReader(open(FINS, encoding="utf-8")))
    est = C.carregar()
    base = C.entradas_de_som(est)
    pares = C.trocas(base)
    certas, refazer, sumiram = [], [], []
    for r in linhas:
        achadas = [(a, b) for a, b in pares if a["ficheiro"] == r["sai"] and b["ficheiro"] == r["entra"]]
        nome = "%s para %s" % (C.nome_da_musica(r["sai"]), C.nome_da_musica(r["entra"]))
        if not achadas:
            sumiram.append(nome)
            continue
        a, b = achadas[0]
        no_corte = a["in_s"] + b["quando"] - a["quando"]
        if abs(no_corte - float(r["no_corte"])) > TOLERANCIA_S:
            refazer.append("%s: chega ao corte aos %.2f s do ficheiro, medida aos %s" % (nome, no_corte, r["no_corte"]))
            continue
        if abs(b["in_s"] - float(r["entra_in"])) > TOLERANCIA_S:
            refazer.append("%s: a que entra entra aos %.2f s, medida com %s" % (nome, b["in_s"], r["entra_in"]))
            continue
        certas.append((r, a, b, nome))
    for r, _a, b, nome in certas:
        print("  certa  %-42s corte aos %.2f" % (nome, b["quando"]))
    for x in sumiram:
        print("  JA NAO EXISTE (uma das musicas saiu ou mudou de sitio):", x)
    for x in refazer:
        print("  MEDIR OUTRA VEZ:", x)
    if so_dizer or not certas:
        return
    pasta = C.pasta("ponto3_3")
    videos = []
    for r, a, b, nome in certas:
        corte = b["quando"]
        # antes da 096: a que sai desce 2,2 s a partir do corte
        antes = [dict(e) for e in C.entradas_de_som(est)]
        for e in antes:
            if e["ficheiro"] == a["ficheiro"] and abs(e["quando"] - a["quando"]) < 0.01:
                e["dura"] = corte - e["quando"] + C.render.CRUZAMENTO
                e["cruza"] = C.render.CRUZAMENTO
                e.pop("descida", None)
        base_nome = os.path.join(pasta, r["id"])
        C.excerto(C.CONSTRUIR_FUTURO, antes, corte, 6, 5, base_nome + "_antes.m4a")
        C.excerto(C.CONSTRUIR_FUTURO, [dict(e) for e in base], corte, 6, 5, base_nome + "_agora.m4a")
        videos.append(C.par_em_video(base_nome + "_antes.m4a", base_nome + "_agora.m4a", nome,
                                     "desce no corte", "acaba no fim da frase", base_nome + ".mp4"))
    print("escrito", C.juntar_videos(videos, os.path.join(pasta, "ponto3_3_todas.mp4")))


if __name__ == "__main__":
    main()
