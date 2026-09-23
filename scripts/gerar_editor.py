# -*- coding: utf-8 -*-
"""Prepara os dados do editor visual: folhas de miniaturas e metadados.

O Tiago pediu um editor onde possa mexer na ordem, nos textos, nas transicoes e
nos grupos de pessoas, sem que eu esteja sempre a refazer renders. Para o editor
correr no telemovel e no portatil, tem de levar as fotografias consigo: nao ha
acesso ao disco dele a partir de uma pagina publicada.

PORQUE FOLHAS DE MINIATURAS E NAO 357 IMAGENS SOLTAS:
357 imagens embutidas uma a uma, mesmo pequenas, dao um ficheiro enorme e 357
descodificacoes separadas. Juntas em folhas de 64, sao 6 imagens e o CSS escolhe
o pedaco com background-position. Passa de perto de 5 MB para cerca de 1,5 MB.

AS FOTOS SAO AS DA PASTA FINAIS, que e a melhor versao de cada uma. O Tiago foi
explicito: "Quero que uses ja as fotos boas e melhores".

CADA FOTO ENTRA INTEIRA, encaixada num quadrado com fundo escuro, e nao cortada.
Num seletor, cortar esconde precisamente quem esta na fotografia, que e o que
ele precisa de ver para a poder atribuir a uma pessoa.

Escreve data/editor_dados.js, que e carregado pela pagina do editor.
"""
import base64
import csv
import io
import json
import os
import sys

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
V1A = os.path.join(REPO, "data", "montagens", "v1a.csv")
FINAIS = r"C:\casamento-video-media\FINAIS"
SAIDA = os.path.join(REPO, "data", "editor_dados.js")

CELULA = 200          # lado da celula, em pixeis
COLUNAS = 8
LINHAS = 8
POR_FOLHA = COLUNAS * LINHAS
QUALIDADE = 70
FUNDO = (24, 20, 26)


def caminho_final(r, finais):
    """A versao da FINAIS, se la estiver, senao o original."""
    base, ext = os.path.splitext(r["ficheiro"])
    for nome in ("%s__%s.jpg" % (r["id"], base), r["ficheiro"], base + ".jpg"):
        if nome.lower() in finais:
            return finais[nome.lower()]
    return r["caminho"]


def main():
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))

    legendas, seccoes = {}, {}
    if os.path.exists(V1A):
        with open(V1A, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["ficheiro"]:
                    legendas[r["ficheiro"].lower()] = " ".join(
                        (r["texto_ecra"] or "").split())
                    seccoes[r["ficheiro"].lower()] = r["seccao"]

    finais = {}
    if os.path.isdir(FINAIS):
        for n in os.listdir(FINAIS):
            finais[n.lower()] = os.path.join(FINAIS, n)

    inv.sort(key=lambda r: (r["pasta"], r["ficheiro"].lower()))

    fotos, folhas = [], []
    folha = None
    for i, r in enumerate(inv):
        pos = i % POR_FOLHA
        if pos == 0:
            if folha is not None:
                folhas.append(folha)
            folha = Image.new("RGB", (CELULA * COLUNAS, CELULA * LINHAS), FUNDO)
        cam = caminho_final(r, finais)
        try:
            with Image.open(cam) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((CELULA, CELULA), Image.LANCZOS)
        except Exception as e:
            print("  nao abriu %s: %s" % (r["ficheiro"][:40], e))
            continue
        cx = (pos % COLUNAS) * CELULA + (CELULA - im.width) // 2
        cy = (pos // COLUNAS) * CELULA + (CELULA - im.height) // 2
        folha.paste(im, (cx, cy))

        fotos.append({
            "id": r["id"],
            "f": r["ficheiro"],
            "p": r["pasta"].split("/")[-1][:28],
            "s": seccoes.get(r["ficheiro"].lower(), ""),
            "a": r["ano"] or "",
            # Grosseiro e vem do bloco da mae, nao e atribuicao de pessoa.
            "pe": r["pessoa"],
            "l": legendas.get(r["ficheiro"].lower(), ""),
            "usada": r["usada_pela_mae"] == "Sim",
            "w": int(r["largura"]), "h": int(r["altura"]),
            "fo": len(folhas), "cx": pos % COLUNAS, "cy": pos // COLUNAS,
        })
        if (i + 1) % 60 == 0:
            print("  %d/%d" % (i + 1, len(inv)), end="\r", flush=True)
    if folha is not None:
        folhas.append(folha)

    imagens = []
    for f in folhas:
        buf = io.BytesIO()
        f.save(buf, "JPEG", quality=QUALIDADE, optimize=True, progressive=False)
        imagens.append("data:image/jpeg;base64," +
                       base64.b64encode(buf.getvalue()).decode("ascii"))

    dados = {
        "celula": CELULA, "colunas": COLUNAS, "linhas": LINHAS,
        "folhas": imagens, "fotos": fotos,
    }
    with open(SAIDA, "w", encoding="utf-8") as fh:
        fh.write("window.DADOS = ")
        json.dump(dados, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(";\n")

    tam = os.path.getsize(SAIDA)
    print(" " * 20, end="\r")
    print("Fotos: %d   Folhas: %d   Ficheiro: %.1f MB"
          % (len(fotos), len(folhas), tam / 1024 / 1024))
    print("Escrito: %s" % SAIDA)


if __name__ == "__main__":
    main()
