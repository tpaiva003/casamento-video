# -*- coding: utf-8 -*-
"""Quantas fotografias DO FILME chegam ao ecra sem esticar pixeis, e o que mudar na Mesa.

PORQUE EXISTE (23 de setembro, decisao 086): o Tiago perguntou qual e o impacto, em numeros,
das fotografias fracas que ELE escolheu para o video, e depois quais sao os zooms a ajustar e
para que valor. A auditoria das caras responde a realidade das feicoes; esta responde a
nitidez no ecra.

A CONTA E A DO RENDER, e nao uma parecida. A primeira versao deste script, de 23 de setembro,
tinha a sua propria geometria e errou-a em quatro sitios, que foram parar a tabela que o
Tiago levou para a Mesa (25 de setembro):
  - o "fiel" enchia o ecra; no render encaixa, com barras pretas, como o "fundo";
  - a rajada levava o zoom lento; no render a rajada nao tem movimento nenhum, e a Mesa
    nem mostra o Enquadramento;
  - os grupos eram uma celula de 960x540; no render o lado a lado 2v tem celulas de
    956x1080, e a pilha e a colagem poem cada foto no tamanho que a disposicao lhe da;
  - dizia "Nenhum" para tirar o zoom, e no render so o "Parada" o tira: "Nenhum" cai no
    ramo de sempre e leva os 12 por cento.
Por isso os grupos sao medidos com o proprio render.preparar(), e as fotos soltas com as
expressoes do render.desenhar(), escritas aqui ao lado de onde vem:

  foto fiel ou fundo   encaixa: min(1920/l, 1080/a), vezes o enquadramento no fim
                         "a encher, com zoom lento" (Zoom in)   1 + ZOOM = 1,12
                         "parada, sem zoom"         (Parada)    1,00
                         "afastada"                 (Afastada)  AFASTADA + AFASTADA_RESPIRA = 0,84
                         "aproxima"                 (Aproxima z) z
  foto em rajada       cobre o ecra, sem movimento: max(1920/l, 1080/a)
  lado a lado          cobre a celula de lado_celulas(), mais LADO_ZOOM de respiracao
  pilha e colagem      a foto inteira no tamanho do lugar que a disposicao lhe da;
                       a colagem ainda respira COLAGEM_RESPIRA no fim

Acima de 1,00 o render estica pixeis do ficheiro da FINAIS. A proposta e sempre o enquadramento
mais apertado que fica dentro da TOLERANCIA, com os nomes que a Mesa mostra. O numero do clip e a
posicao na Mesa: e igual a ordem do CSV da montagem, clip a clip (verificado a 25 de setembro).

Uso:  py -3.11 scripts/auditar_nitidez.py
      py -3.11 scripts/auditar_nitidez.py --montagem v3
"""
import contextlib
import csv
import io
import json
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import render      # noqa: E402

from PIL import Image      # noqa: E402

Image.MAX_IMAGE_PIXELS = None

# Ate 5 por cento de esticao ninguem ve, nem a um metro do ecra: um Lanczos a 1,05 nao
# acrescenta nada que se distinga. Serve para nao mandar o Tiago mexer num clip por nada.
TOLERANCIA = 1.05

# Os enquadramentos de uma foto solta: o nome no CSV, o nome na Mesa e o fator no fim.
FIM_ZOOM = 1.0 + render.ZOOM
FIM_AFASTADA = render.AFASTADA + render.AFASTADA_RESPIRA
NA_MESA = {"Zoom in": "a encher, com zoom lento", "Parada": "parada, sem zoom",
           "Afastada": "afastada", "Aproxima": "aproxima ao ponto de foco"}


def tamanho_real(caminho):
    """(largura, altura) como o render a ve, ja com a rotacao do EXIF."""
    try:
        with Image.open(caminho) as im:
            w, h = im.size
            try:
                orient = im.getexif().get(0x0112, 1)
            except Exception:
                orient = 1
    except Exception:
        return None
    return (h, w) if orient in (5, 6, 7, 8) else (w, h)


def enquadramento(mov):
    """(nome no CSV, fator no fim do movimento) de uma foto solta, como o render.desenhar()."""
    aproxima, az, _aviso = render.ler_aproxima(mov)
    if aproxima:
        return "Aproxima", az
    if mov == "Parada":
        return "Parada", 1.0
    if mov == "Afastada":
        return "Afastada", FIM_AFASTADA
    # "Zoom in", o "Nenhum" das v1 e o vazio caem todos no ramo de sempre do render
    return "Zoom in", FIM_ZOOM


def proposta_solta(nome, encaixe):
    """O enquadramento mais apertado que fica dentro da TOLERANCIA, com o nome da Mesa."""
    maximo = TOLERANCIA / encaixe
    if nome == "Aproxima" and maximo >= render.APROXIMA_MIN:
        z = math.floor(min(maximo, render.APROXIMA_MAX) * 10) / 10.0
        if z >= render.APROXIMA_MIN:
            return "aproxima com zoom %s" % ("%.1f" % z).replace(".", ",")
    if maximo >= FIM_ZOOM:
        return NA_MESA["Zoom in"]
    if maximo >= 1.0:
        return NA_MESA["Parada"]
    if maximo >= FIM_AFASTADA:
        return NA_MESA["Afastada"]
    return None


def medidas_do_grupo(clip, inv_por_nome):
    """[(indice da foto, largura no ecra, altura no ecra, cobre?)] tirados do proprio render."""
    with contextlib.redirect_stdout(io.StringIO()):
        pronto = render.preparar(clip, inv_por_nome)
    if not pronto:
        return []
    saida = []
    if pronto["tipo"] == "lado":
        lay = (clip.get("tratamento") or "").strip()
        for k, (rect, _vem) in enumerate(render.lado_celulas(lay)):
            _x, _y, w, h = rect
            if lay == "3s" and k == 2:
                # o cartao de cima: a foto inteira dentro da moldura de 14, sem respirar
                saida.append((k, w - 28, h - 28, False))
            else:
                saida.append((k, w * (1 + render.LADO_ZOOM), h * (1 + render.LADO_ZOOM), True))
        return saida
    cresce = pronto.get("cresce", 1.0)
    for k, f in enumerate(pronto["fotos"]):
        w, h = f["tamanho"]
        saida.append((k, w * cresce, h * cresce, False))
    return saida


def ampliacao(lw, la, w, h, cobre):
    """Quanto o render estica o ficheiro para o desenhar com lw x la no ecra."""
    return max(lw / w, la / h) if cobre else min(lw / w, la / h)


def main():
    nome = sys.argv[sys.argv.index("--montagem") + 1] if "--montagem" in sys.argv else "v3"
    clips = list(csv.DictReader(
        open(os.path.join(REPO, "data", "montagens", nome + ".csv"), encoding="utf-8-sig")))
    inv = list(csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig")))
    inv_por_nome = {r["ficheiro"].lower(): r for r in inv}
    inv_por_id = {r["id"]: r for r in inv}
    fin = {r["id"]: r for r in csv.DictReader(
        open(os.path.join(REPO, "data", "finais.csv"), encoding="utf-8-sig"))}
    indice = {i: os.path.join(render.FINAIS, r["final"]) for i, r in fin.items()
              if os.path.exists(os.path.join(render.FINAIS, r["final"]))}
    # os mesmos caminhos e os mesmos encadeados que o render poe antes de desenhar
    render.caminhos_pelo_indice(clips, indice, inv_por_id, inv_por_nome)
    render.ligar_transicoes(clips, fim_do_filme=True)
    caras = {}
    cam_caras = os.path.join(REPO, "data", "auditoria_caras.csv")
    if os.path.exists(cam_caras):
        caras = {r["id"]: r for r in csv.DictReader(open(cam_caras, encoding="utf-8-sig"))}

    casos = []
    for c in clips:
        tipo = c["tipo"]
        if tipo not in ("foto", "lado", "colagem", "pilha"):
            continue
        base = {"clip": int(c["ordem"]), "t": float(c["inicio_s"]), "tipo": tipo,
                "tratamento": (c.get("tratamento") or "fiel").strip() or "fiel"}
        if tipo == "foto":
            ident = c["id"]
            cam = c.get("_caminho")
            tam = tamanho_real(cam) if cam else None
            if not ident or not tam:
                continue
            w, h = tam
            if base["tratamento"] == "rajada":
                encaixe, mov, fator, cobre = max(1920.0 / w, 1080.0 / h), "rajada", 1.0, True
            else:
                encaixe = min(1920.0 / w, 1080.0 / h)
                mov, fator = enquadramento((c.get("movimento") or "").strip())
                cobre = False
            amp = encaixe * fator
            propor = None
            if amp > TOLERANCIA and mov != "rajada":
                propor = proposta_solta(mov, encaixe)
            casos.append(dict(base, id=ident, foto=1, de=1, ficheiro=fin.get(ident, {}).get("ficheiro", ""),
                              origem=fin.get(ident, {}).get("origem", ""), px="%dx%d" % (w, h),
                              enquadramento=mov, fator=fator, zoom=fator, ampliacao=amp,
                              largura_no_ecra=amp * w, cobre=cobre, proposta=propor))
            continue
        ids = [i for i in (c.get("id") or "").split("|")]
        medidas = medidas_do_grupo(c, inv_por_nome)
        caminhos = c.get("_caminhos") or []
        for k, lw, la, cobre in medidas:
            if k >= len(ids) or k >= len(caminhos) or not caminhos[k]:
                continue
            tam = tamanho_real(caminhos[k])
            if not tam:
                continue
            w, h = tam
            amp = ampliacao(lw, la, w, h, cobre)
            ident = ids[k]
            casos.append(dict(base, id=ident, foto=k + 1, de=len(ids),
                              ficheiro=fin.get(ident, {}).get("ficheiro", ""),
                              origem=fin.get(ident, {}).get("origem", ""), px="%dx%d" % (w, h),
                              enquadramento="", fator=1.0, zoom=1.0, ampliacao=amp,
                              largura_no_ecra=amp * w, cobre=cobre, proposta=None))

    for x in casos:
        x["detalhe_cara"] = float(caras[x["id"]]["detalhe_cara"]) if x["id"] in caras else None
        x["ssim_cara"] = float(caras[x["id"]]["ssim_cara"]) if x["id"] in caras else None

    casos.sort(key=lambda x: -x["ampliacao"])
    n = len(casos)

    def conta(f):
        return sum(1 for x in casos if f(x))

    print("AS FOTOGRAFIAS DO FILME: %d lugares, em %d clips"
          % (n, len({x["clip"] for x in casos})))
    print()
    print("NITIDEZ NO ECRA (1,00 e o limite; acima o render estica pixeis)")
    for rot, lo, hi in (("esticadas mais de 2x, muito visivel", 2.0, 99.0),
                        ("esticadas de 1,5 a 2x, ve-se", 1.5, 2.0),
                        ("esticadas de %.2f a 1,5x, nota-se pouco" % TOLERANCIA, TOLERANCIA, 1.5),
                        ("ate %.2f, nao se ve" % TOLERANCIA, 0.0, TOLERANCIA)):
        k = conta(lambda x: lo <= x["ampliacao"] < hi)
        print("  %-40s %3d  (%4.1f%%)" % (rot, k, 100.0 * k / max(1, n)))
    print()

    def minuto(t):
        return "%2d:%02d" % (int(t // 60), int(t % 60))

    soltas = [x for x in casos if x["tipo"] == "foto" and x["ampliacao"] > TOLERANCIA]
    mudar = sorted([x for x in soltas if x["proposta"]], key=lambda x: x["clip"])
    rajada = sorted([x for x in soltas if x["enquadramento"] == "rajada"], key=lambda x: x["clip"])
    sem = sorted([x for x in soltas if not x["proposta"] and x["enquadramento"] != "rajada"],
                 key=lambda x: x["clip"])
    print("FOTOS SOLTAS: O QUE MUDAR NO ENQUADRAMENTO DA MESA")
    print("  clip  minuto  hoje                         estica  passa a                      fica")
    for x in mudar:
        hoje = NA_MESA[x["enquadramento"]]
        if x["enquadramento"] == "Aproxima":
            hoje += " %s" % ("%.1f" % x["fator"]).replace(".", ",")
        enc = x["ampliacao"] / x["fator"]
        p = x["proposta"]
        if p.startswith("aproxima"):
            fica = enc * float(p.split()[-1].replace(",", "."))
        else:
            fica = enc * {NA_MESA["Zoom in"]: FIM_ZOOM, NA_MESA["Parada"]: 1.0,
                          NA_MESA["Afastada"]: FIM_AFASTADA}[p]
        print("  %4d   %s  %-28s %5.2fx  %-28s %4.2fx  %s"
              % (x["clip"], minuto(x["t"]), hoje[:28], x["ampliacao"], p[:28], fica, x["ficheiro"][:30]))
    if not mudar:
        print("  nenhuma")
    print()
    print("FOTOS SOLTAS QUE NEM PARADAS CHEGAM (o melhor e afastada; de resto, outra versao ou outra foto)")
    for x in sem:
        melhor = x["ampliacao"] / x["fator"] * FIM_AFASTADA
        print("  %4d   %s  %-11s %5.2fx  afastada fica %4.2fx  %s  %s"
              % (x["clip"], minuto(x["t"]), x["origem"], x["ampliacao"], melhor, x["px"],
                 x["ficheiro"][:40]))
    if not sem:
        print("  nenhuma")
    print()
    print("EM RAJADA (sem zoom: so outra foto, ou tira-la da rajada)")
    for x in rajada:
        print("  %4d   %s  %-11s %5.2fx  %s  %s"
              % (x["clip"], minuto(x["t"]), x["origem"], x["ampliacao"], x["px"], x["ficheiro"][:40]))
    if not rajada:
        print("  nenhuma")
    print()
    print("NOS GRUPOS (nao ha zoom: trocar a foto, ou por menos fotos no grupo)")
    grupos = sorted([x for x in casos if x["tipo"] != "foto" and x["ampliacao"] > TOLERANCIA],
                    key=lambda x: (x["clip"], x["foto"]))
    for x in grupos:
        print("  %4d   %s  %-7s %-9s foto %d de %d  %5.2fx  %-11s %s  %s"
              % (x["clip"], minuto(x["t"]), x["tipo"], x["tratamento"][:9], x["foto"], x["de"],
                 x["ampliacao"], x["origem"], x["px"], x["ficheiro"][:34]))
    if not grupos:
        print("  nenhum")
    for x in casos:
        x.pop("cobre", None)
    json.dump(casos, open(os.path.join(REPO, "data", "auditoria_nitidez.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("escrito: data/auditoria_nitidez.json")


# SO CORRE QUANDO E CHAMADO PELO NOME. Sem esta guarda, importar o modulo corria o
# programa todo: o consolidar.py importa o auditar_caras para a guarda das caras e
# arrancava uma auditoria de 719 fotografias sem ninguem pedir.
if __name__ == "__main__":
    main()
