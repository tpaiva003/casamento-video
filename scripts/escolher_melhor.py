# -*- coding: utf-8 -*-
"""Escolhe, para cada fotografia DO FILME, a versao que respeita a cara E tem pixeis que cheguem.

PORQUE EXISTE (23 de setembro, decisao 086). O consolidar.py escolhia pela ampliacao que a
fotografia precisava, e mais nada. Duas coisas ficaram de fora e deram nas vistas:

  1. O QUE A REDE FAZ AS CARAS. Medido no acervo: o caminho lanczos devolve uma cara com 90
     por cento da textura do original na mediana, e a rede com 73, e no pior caso 17. O
     travao dos 8 por cento media a fotografia INTEIRA, e uma cara e uma fraccao pequena do
     quadro: um olho redesenhado passava por la sem acusar.
  2. O ZOOM DO CLIP. A regra preparava a foto para o tamanho a que ela aparece PARADA. Uma
     foto com Aproxima 4.0 mostra no fim um recorte com um quarto da area, ou seja precisa de
     quatro vezes mais pixeis do que a regra lhe deu.

O QUE ISTO FAZ: para cada lugar de fotografia na montagem, poe as versoes que existem em
disco lado a lado, mede em cada uma a fidelidade da cara contra o ORIGINAL e os pixeis que
ela tem para o enquadramento mais apertado do clip, e escolhe. Nao escreve nada: propoe, e
diz porque. Quem muda o indice e o consolidar.py, com a guarda nova.

A ORDEM DE PREFERENCIA, quando mais do que uma serve: a mais fiel a cara. Entre duas
igualmente fieis, a que tem mais pixeis. O original ganha sempre que chegue, porque e a
unica que nao foi tocada por ninguem.

Uso:  py -3.11 scripts/escolher_melhor.py
      py -3.11 scripts/escolher_melhor.py --so-problemas
"""
import csv
import json
import os
import sys

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import render            # noqa: E402
import auditar_caras     # noqa: E402

MEDIA = r"C:\casamento-video-media\trabalho"
PASTAS = [("original", None),
          ("lanczos", r"C:\casamento-video-media\upscaled"),
          ("IA", r"C:\casamento-video-media\upscaled-ia"),
          ("restaurada", r"C:\casamento-video-media\restauradas")]
# A cara tem de ficar com pelo menos isto da textura do original para a versao ser aceite.
# Medido: o lanczos anda nos 0,90 e a rede nos 0,73; 0,80 deixa passar o lanczos e trava a
# rede quando ela alisa a serio, sem proibir a rede onde ela se porta bem.
CARA_MINIMA = 0.80
# E UM TECTO, que faltava. Uma cara com MAIS detalhe do que o original tem nao esta melhor:
# tem detalhe que ninguem fotografou. Foi assim que a f0560 ganhou olhos abertos onde o
# original tem duas manchas moles. Acima disto a versao e recusada, venha de onde vier.
CARA_MAXIMA = 1.25


def candidatas(ident, inv):
    """As versoes desta fotografia que existem em disco, por nome de caminho."""
    r = inv[ident]
    base, _ext = os.path.splitext(r["ficheiro"])
    saida = []
    for nome, pasta in PASTAS:
        if pasta is None:
            c = os.path.join(MEDIA, r["pasta"].replace("/", os.sep), r["ficheiro"])
            if os.path.exists(c):
                saida.append((nome, c))
            continue
        if not os.path.isdir(pasta):
            continue
        for f in os.listdir(pasta):
            sf, _e = os.path.splitext(f)
            if sf == base or sf.endswith("__" + base.replace(" ", "_")) or sf == ident + "__" + base:
                saida.append((nome, os.path.join(pasta, f)))
                break
    return saida


def mede(caminho_o, caminho_v, caixas):
    """(fidelidade da cara, ssim da cara, largura, altura) de uma versao contra o original."""
    o = auditar_caras.ler(caminho_o)
    v = auditar_caras.ler(caminho_v)
    if o is None or v is None:
        return None
    lv, av = v.shape[1], v.shape[0]
    if (v.shape[1], v.shape[0]) != (o.shape[1], o.shape[0]):
        v = cv2.resize(v, (o.shape[1], o.shape[0]), interpolation=cv2.INTER_AREA)
    go = cv2.cvtColor(o, cv2.COLOR_BGR2GRAY)
    gv = cv2.cvtColor(v, cv2.COLOR_BGR2GRAY)
    if not caixas:
        return (1.0, 1.0, lv, av)
    dets, ss = [], []
    for (x, y, w, h) in caixas:
        a, b = go[y:y + h, x:x + w], gv[y:y + h, x:x + w]
        if min(a.shape) < 32:
            continue
        da = auditar_caras.detalhe(a)
        dets.append(auditar_caras.detalhe(b) / max(0.01, da))
        ss.append(float(ssim(a, b)))
    if not dets:
        return (1.0, 1.0, lv, av)
    return (float(np.min(dets)), float(np.min(ss)), lv, av)


def main():
    inv = {r["id"]: r for r in csv.DictReader(
        open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig"))}
    casos = json.load(open(os.path.join(REPO, "data", "auditoria_nitidez.json"),
                           encoding="utf-8"))
    so_problemas = "--so-problemas" in sys.argv
    saida = []
    for c in casos:
        ident = c["id"]
        if ident not in inv:
            continue
        cands = candidatas(ident, inv)
        if len(cands) < 2:
            continue
        caminho_o = next((p for n, p in cands if n == "original"), None)
        if not caminho_o:
            continue
        o = auditar_caras.ler(caminho_o)
        caixas = auditar_caras.caras_de(cv2.cvtColor(o, cv2.COLOR_BGR2GRAY))
        # a ampliacao que o clip pede, referida ao ORIGINAL
        pede = c["ampliacao"] * max(1.0, 1.0)  # a ampliacao ja foi medida sobre o final
        linhas = []
        for nome, p in cands:
            m = mede(caminho_o, p, caixas)
            if not m:
                continue
            fid, s, lv, av = m
            # PIXEIS QUE ESTA VERSAO TEM PARA O ENQUADRAMENTO DESTE CLIP. A largura com que a
            # foto e desenhada no ecra vem do auditar_nitidez.py, que a tira das contas do
            # render; uma versao com lv pixeis de largura e esticada largura/lv. Aqui havia uma
            # copia da geometria, "fundo encaixa, o resto enche", e estava errada no "fiel",
            # na rajada e nos grupos (decisao 086): uma regra, um sitio.
            linhas.append({"versao": nome, "caminho": p, "cara": fid, "ssim": s,
                           "px": "%dx%d" % (lv, av),
                           "ampliacao": c["largura_no_ecra"] / float(lv)})
        if not linhas:
            continue
        # FIDELIDADE E DISTANCIA A 1,00, PARA OS DOIS LADOS. Abaixo de 1 o modelo APAGOU
        # textura da cara; acima de 1 ACRESCENTOU detalhe que o original nao tem, e isso e
        # invencao, nao melhoria. A primeira versao desta regra premiava o valor mais alto e
        # chegou a propor trocar o ORIGINAL por uma versao da rede com 1,10, ou seja trocar a
        # verdade por uma cara inventada. O ideal e 1,00, que e o que o original vale sempre.
        def desvio(l):
            return abs(l["cara"] - 1.0)

        for l in linhas:
            l["desvio"] = desvio(l)
        aceitaveis = [l for l in linhas if l["cara"] >= CARA_MINIMA and l["cara"] <= CARA_MAXIMA]
        servem = [l for l in aceitaveis if l["ampliacao"] <= 1.02]
        if servem:
            melhor = min(servem, key=lambda l: (round(l["desvio"], 2), l["ampliacao"]))
            motivo = "cara fiel e pixeis que chegam"
        elif aceitaveis:
            melhor = min(aceitaveis, key=lambda l: l["ampliacao"])
            motivo = "a que menos estica das fieis; ainda estica %.2fx" % melhor["ampliacao"]
        else:
            melhor = min(linhas, key=lambda l: l["desvio"])
            motivo = "nenhuma respeita a cara; esta e a menos ma (%.2f)" % melhor["cara"]
        atual = next((l for l in linhas if l["versao"] == c["origem"]), None)

        # E NAO SE TROCA POR TROCAR. Se a que la esta ja respeita a cara e ja tem pixeis que
        # cheguem, fica: uma troca que nao melhora nada e ruido no indice e no git, e obriga a
        # refazer a FINAIS sem razao. So se troca quando ha ganho a serio.
        if atual and atual["cara"] >= CARA_MINIMA and atual["cara"] <= CARA_MAXIMA \
                and atual["ampliacao"] <= 1.02:
            melhor, motivo = atual, "a que la esta ja serve"
        elif atual and melhor["versao"] != atual["versao"]:
            ganho_cara = atual["desvio"] - melhor["desvio"]
            ganho_px = atual["ampliacao"] - melhor["ampliacao"]
            if ganho_cara < 0.05 and ganho_px < 0.05:
                melhor, motivo = atual, "a alternativa nao melhora o suficiente"
        muda = atual is not None and melhor["versao"] != atual["versao"]
        if so_problemas and not muda and melhor["ampliacao"] <= 1.02:
            continue
        saida.append({"clip": c["clip"], "t": c["t"], "id": ident, "ficheiro": c["ficheiro"],
                      "agora": c["origem"], "proposta": melhor["versao"], "muda": muda,
                      "motivo": motivo, "zoom": c["zoom"],
                      "cara_agora": atual["cara"] if atual else None,
                      "cara_proposta": melhor["cara"],
                      "ampliacao_proposta": melhor["ampliacao"],
                      "alternativas": linhas})
    saida.sort(key=lambda s: s["clip"])
    cam = os.path.join(REPO, "data", "escolha_proposta.json")
    json.dump(saida, open(cam, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    mudam = [s for s in saida if s["muda"]]
    esticam = [s for s in saida if s["ampliacao_proposta"] > 1.02]
    print("lugares examinados: %d" % len(saida))
    print("  trocam de versao: %d" % len(mudam))
    print("  continuam a esticar depois da troca: %d" % len(esticam))
    print()
    print("TROCAS PROPOSTAS")
    print("  clip  minuto  de          para        cara antes  cara depois")
    for s in mudam:
        print("  %4d   %2d:%02d  %-11s %-11s %9s  %11.2f"
              % (s["clip"], int(s["t"] // 60), int(s["t"] % 60), s["agora"], s["proposta"],
                 ("%.2f" % s["cara_agora"]) if s["cara_agora"] is not None else "-",
                 s["cara_proposta"]))
    print()
    print("AINDA ESTICAM, E AI O QUE SE BAIXA E O ZOOM")
    print("  clip  minuto  zoom  ampliacao  zoom maximo honesto")
    for s in esticam:
        maximo = s["zoom"] / s["ampliacao_proposta"]
        print("  %4d   %2d:%02d  %4.1f     %5.2fx      %.2f"
              % (s["clip"], int(s["t"] // 60), int(s["t"] % 60), s["zoom"],
                 s["ampliacao_proposta"], maximo))
    print()
    print("escrito: %s" % cam)


# SO CORRE QUANDO E CHAMADO PELO NOME. Sem esta guarda, importar o modulo corria o
# programa todo: o consolidar.py importa o auditar_caras para a guarda das caras e
# arrancava uma auditoria de 719 fotografias sem ninguem pedir.
if __name__ == "__main__":
    main()
