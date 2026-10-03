# -*- coding: utf-8 -*-
"""Previas grandes das fotografias, em folhas, para a Mesa as mostrar ampliadas.

O Tiago: "Quero tambem poder expandir as fotos, pois nem sempre consigo perceber
exatamente que foto e aquela". As miniaturas da Mesa tem 200 pixeis; para se
perceber quem esta numa foto e preciso mais do que isso.

PORQUE FOLHAS E NAO UMA IMAGEM POR FOTO: a primeira versao fazia um ficheiro por
fotografia, e a publicacao recusou-a: o link da Mesa aceita no maximo 256 ficheiros
ao todo, e sao 641 fotos. Em folhas de 4 por 4, a 720 pixeis cada, sao 41 ficheiros.
Dentro do HTML nao cabiam: seriam 35 MB e a pagina passava o limite de 16 MB.

Cada foto entra inteira, encaixada numa celula quadrada de fundo escuro, tal como
nas miniaturas. As previas saem da FINAIS, pelo indice data/finais.csv, que e a
versao que o video vai usar.

Escreve saida/previas/folha_NN.jpg e saida/previas/indice.json, com a folha e a
celula de cada foto. O gerar_mesa.py poe esse indice dentro da Mesa.

Uso:  py -3.11 scripts/gerar_previas.py
"""
import csv
import io
import json
import os
import sys

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDICE = os.path.join(REPO, "data", "finais.csv")
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
FINAIS = r"C:\casamento-video-media\FINAIS"
DESTINO = os.path.join(REPO, "saida", "previas")
CELULA = 720
COLUNAS = 4
LINHAS = 4
QUALIDADE = 72
FUNDO = (11, 10, 13)


# AS PECAS DE BAIXO estavam dentro do main() ate 3 de outubro. Sairam para o
# scripts/entrada_rapida.py poder guardar a celula de cada foto e saltar as folhas que nao
# mudaram, sem copiar para la a ordem, o encaixe nem a gravacao. Aqui nao ha cache nenhuma:
# quem corre o gerar_previas.py apaga e refaz as folhas todas, como sempre.
def limpar_antigas():
    """As previas antigas, uma por foto, deixam de servir; e as folhas refazem-se todas."""
    for n in os.listdir(DESTINO):
        if n.lower().endswith(".jpg") or n == "lista.json":
            os.remove(os.path.join(DESTINO, n))


def origem_de(r, finais):
    """O ficheiro de onde sai a previa: o da FINAIS, pelo indice, senao o original."""
    origem = os.path.join(FINAIS, finais[r["id"]]["final"]) if r["id"] in finais else r["caminho"]
    if not os.path.exists(origem):
        origem = r["caminho"]
    return origem


def celula(origem):
    """A foto inteira, rodada pelo EXIF, reduzida para caber na celula."""
    with Image.open(origem) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((CELULA, CELULA), Image.LANCZOS)
    return im


def fazer_folha(lote, finais, n_folha, caminho):
    """Desenha uma folha e grava-a. Devolve ({id: [folha, cx, cy]}, quantas deram erro)."""
    folha = Image.new("RGB", (COLUNAS * CELULA, LINHAS * CELULA), FUNDO)
    posicoes, erros = {}, 0
    for j, r in enumerate(lote):
        origem = origem_de(r, finais)
        cx, cy = j % COLUNAS, j // COLUNAS
        try:
            im = celula(origem)
            folha.paste(im, (cx * CELULA + (CELULA - im.width) // 2,
                             cy * CELULA + (CELULA - im.height) // 2))
            posicoes[r["id"]] = [n_folha, cx, cy]
        except Exception as e:
            erros += 1
            print("  ERRO %s %s: %s" % (r["id"], r["ficheiro"], e))
    folha.save(caminho, "JPEG", quality=QUALIDADE, optimize=True, progressive=True)
    return posicoes, erros


def fazer_folhas(tarefas):
    """Todas as folhas, uma a seguir a outra, pela ordem. Cada tarefa sao os argumentos do
    fazer_folha(). (A entrada rapida faz varias ao mesmo tempo; o resultado e o mesmo.)"""
    return [fazer_folha(*t) for t in tarefas]


def main():
    os.makedirs(DESTINO, exist_ok=True)
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    finais = {}
    if os.path.exists(INDICE):
        with open(INDICE, encoding="utf-8-sig", newline="") as fh:
            finais = {r["id"]: r for r in csv.DictReader(fh)}

    # A mesma ordem das miniaturas da Mesa, para as fotos vizinhas na grelha
    # ficarem normalmente na mesma folha e as setas nao descarregarem outra.
    inv.sort(key=lambda r: (r["pasta"], r["ficheiro"].lower()))

    limpar_antigas()

    por_folha = COLUNAS * LINHAS
    tarefas = []
    for k in range(0, len(inv), por_folha):
        n_folha = len(tarefas)
        nome = "folha_%02d.jpg" % (n_folha + 1)
        tarefas.append((inv[k:k + por_folha], finais, n_folha, os.path.join(DESTINO, nome)))
    posicoes, folhas, erros, total_bytes = {}, [], 0, 0
    for (_lote, _finais, _n, caminho), (da_folha, com_erro) in zip(tarefas, fazer_folhas(tarefas)):
        posicoes.update(da_folha)
        erros += com_erro
        total_bytes += os.path.getsize(caminho)
        folhas.append(os.path.basename(caminho))

    with io.open(os.path.join(DESTINO, "indice.json"), "w", encoding="utf-8") as fh:
        json.dump({"celula": CELULA, "colunas": COLUNAS, "linhas": LINHAS,
                   "folhas": folhas, "pos": posicoes}, fh, separators=(",", ":"))
    print("Previas: %d fotos em %d folhas, %.1f MB, %d com erro" % (
        len(posicoes), len(folhas), total_bytes / 1048576.0, erros))
    print("  maior folha: %.1f MB" % (max(os.path.getsize(os.path.join(DESTINO, f)) for f in folhas) / 1048576.0))


if __name__ == "__main__":
    main()
