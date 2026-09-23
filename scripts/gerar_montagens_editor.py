# -*- coding: utf-8 -*-
"""Exporta as montagens ja feitas para dentro do editor.

Sem isto o editor abria vazio e o Tiago tinha de construir tudo do zero, o que e
o contrario do que ele pediu: "Nao invente nada. So quero isto pronto para
depois ser eficiente".

Com isto, ele abre e tem la a v1a com as 292 entradas na ordem da mae da Clara,
a v1b, a v1c e as quatro demos, prontas a reordenar, cortar e anotar.

Escreve data/editor_montagens.js.
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTAGENS = os.path.join(REPO, "data", "montagens")
SAIDA = os.path.join(REPO, "data", "editor_montagens.js")

# Nome curto -> como aparece no editor. A ordem e a de quem manda primeiro.
TITULOS = [
    ("v1a", "v1a, a dela com durações afinadas"),
    ("v1b", "v1b, com fundo desfocado e rajadas"),
    ("v1c", "v1c, com as correções de história"),
    ("demo_v1b", "demo v1b"),
    ("demo_v1c", "demo v1c, a corrente dos cães"),
    ("demo_v2", "demo v2, o funil com narração"),
    ("demo_v3", "demo v3, o flash-forward"),
]


def clips_de(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    saida = []
    for r in linhas:
        tipo = r["tipo"]
        if tipo == "video":
            tipo = "fanfarra"
        saida.append({
            "t": tipo,                                   # foto, cartao, fanfarra
            "i": r.get("id") or "",
            "f": r.get("ficheiro") or "",
            "x": " ".join((r.get("texto_ecra") or "").split()),
            "d": round(float(r["duracao_s"]), 2),
            "c": round(float(r.get("transicao_s") or 0), 2),
            "r": (r.get("tratamento") or "fiel").strip() or "fiel",
        })
    return saida


def main():
    versoes = []
    for nome, titulo in TITULOS:
        caminho = os.path.join(MONTAGENS, nome + ".csv")
        if not os.path.exists(caminho):
            print("  sem %s" % nome)
            continue
        clips = clips_de(caminho)
        versoes.append({
            "id": nome,
            "nome": titulo,
            "origem": "gerada pelos scripts",
            "notas": "",
            "clips": clips,
        })
        total = sum(c["d"] for c in clips) - sum(c["c"] for c in clips)
        print("  %-10s %3d clips   %d:%02d" % (nome, len(clips),
                                               int(total) // 60, int(total) % 60))

    with open(SAIDA, "w", encoding="utf-8") as fh:
        fh.write("window.MONTAGENS = ")
        json.dump(versoes, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(";\n")
    print("Escrito: %s  (%.0f KB)" % (SAIDA, os.path.getsize(SAIDA) / 1024))


if __name__ == "__main__":
    main()
