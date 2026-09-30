# -*- coding: utf-8 -*-
"""Estado das fotografias: o que ja esta pronto e o que ainda espera melhoria.

O Tiago: "podias colocar la um botao para atualizar e para verificar se ja
analisou as fotos todas". A Mesa corre numa pagina publicada e nao ve o disco,
portanto a verificacao faz-se aqui, no fim de cada atualizacao, e vai dentro da
Mesa como um retrato com data e hora. O botao da Mesa mostra esse retrato.

Uma fotografia esta PRONTA quando a versao que a FINAIS usa e a que as regras
mandam usar:

  nao precisa de crescer              original                decisao 040
  cresce                              lanczos                 decisoes 052 e 090
  so aparece como marca da fita       qualquer uma            decisao 038

Desde 28 de setembro (decisao 090) a rede neuronal nao entra no filme: o que acima de 1,5
vezes era a rede passou a ser o lanczos. E uma foto cuja versao lanczos a guarda das caras
recusou fica com o original, e isso tambem e pronta: e uma escolha feita.

Tudo o resto fica "a espera", com o motivo: falta a versao lanczos, falta a da
rede neuronal, ou a versao existe mas o consolidar.py ainda nao correu.

Conta tambem as imagens da 01-NOVAS que ainda nao entraram no inventario, com a
mesma regra do inventario.py.

Escreve data/estado_fotos.json, que o gerar_mesa.py poe dentro da Mesa.

Uso:  py -3.11 scripts/estado_fotos.py
"""
import csv
import datetime
import io
import json
import os
import sys
from collections import Counter

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
INDICE = os.path.join(REPO, "data", "finais.csv")
SAIDA = os.path.join(REPO, "data", "estado_fotos.json")
NOVAS = r"C:\casamento-video-media\trabalho\01-NOVAS"
LANCZOS = r"C:\casamento-video-media\upscaled"
REDE = r"C:\casamento-video-media\upscaled-ia"

MOTIVOS = {
    "espera_lanczos": "falta a versão lanczos",
    "espera_ia": "falta a versão da rede neuronal",
    "falta_consolidar": "falta escolher a versão final",
}


def ids_em(pasta):
    if not os.path.isdir(pasta):
        return set()
    return {n.split("__")[0] for n in os.listdir(pasta)}


def por_registar(inv):
    """Imagens da 01-NOVAS que o inventario ainda nao tem, pela regra dele."""
    import inventario
    caminhos = {os.path.normcase(r["caminho"]) for r in inv}
    faltam = []
    for raiz, _, fs in os.walk(NOVAS):
        dentro_de_files = os.path.basename(raiz).endswith("_files")
        for f in sorted(fs):
            if not f.lower().endswith(inventario.EXT):
                continue
            p = os.path.join(raiz, f)
            if os.path.normcase(p) in caminhos:
                continue
            if dentro_de_files and not inventario.foto_a_serio(p):
                continue
            faltam.append(os.path.relpath(p, NOVAS))
    return faltam


def main():
    import consolidar

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    indice = {}
    if os.path.exists(INDICE):
        with open(INDICE, encoding="utf-8-sig", newline="") as fh:
            indice = {r["id"]: r for r in csv.DictReader(fh)}

    tem_lanczos, tem_rede = ids_em(LANCZOS), ids_em(REDE)
    vinhetas = consolidar.vinhetas_da_fita()
    estados, origens, espera = Counter(), Counter(), []
    guarda = 0

    for r in inv:
        fator = consolidar.fator_ampliacao(int(r["largura"]), int(r["altura"]))
        linha = indice.get(r["id"]) or {}
        origem = linha.get("origem")
        # A VERSAO DA REGRA PODE TER SIDO RECUSADA DE PROPOSITO, pela guarda das caras ou pelo
        # limite de alteracao (decisao 086). O consolidar.py escreve-o na coluna recusadas do
        # indice, "IA:cara 0.17;lanczos:cara 0.78", e isso e uma escolha feita, nao uma que
        # falta fazer: a 27 de setembro, sem esta leitura, a Mesa dizia 48 fotos "a espera".
        recusadas = {p.split(":")[0] for p in (linha.get("recusadas") or "").split(";") if p}
        if origem:
            origens[origem] += 1
        if not origem:
            estado = "falta_consolidar"
        elif fator <= 1.0 or r["ficheiro"].lower() in vinhetas:
            estado = "pronta"
        elif origem == "lanczos":
            estado = "pronta"
        elif "lanczos" in recusadas:
            estado = "pronta"
            guarda += 1
        else:
            estado = "espera_lanczos" if r["id"] not in tem_lanczos else "falta_consolidar"
        estados[estado] += 1
        if estado != "pronta":
            espera.append({"id": r["id"], "f": r["ficheiro"], "e": estado,
                           "m": MOTIVOS[estado], "x": round(fator, 2)})

    novas = por_registar(inv)
    agora = datetime.datetime.now()
    dados = {
        "build": agora.strftime("%Y%m%d-%H%M%S"),
        "gerado": agora.strftime("%Y-%m-%d %H:%M"),
        "total": len(inv),
        "prontas": estados["pronta"],
        "espera": espera,
        "origens": dict(origens),
        "por_registar": len(novas),
        "por_registar_lista": novas[:40],
    }
    with io.open(SAIDA, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=1)

    print("Estado das fotografias, %s" % dados["gerado"])
    print("  no inventario:            %d" % dados["total"])
    print("  prontas:                  %d" % dados["prontas"])
    if guarda:
        print("    das quais com a versao da regra recusada pela guarda: %d" % guarda)
    for chave, texto in MOTIVOS.items():
        if estados[chave]:
            print("  a espera, %-28s %d" % (texto + ":", estados[chave]))
    print("  na 01-NOVAS por registar: %d" % dados["por_registar"])
    print("  versoes na FINAIS: %s" % ", ".join("%s %d" % kv for kv in sorted(origens.items())))
    print("Escrito: %s" % SAIDA)


if __name__ == "__main__":
    main()
