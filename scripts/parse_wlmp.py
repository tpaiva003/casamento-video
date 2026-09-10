# -*- coding: utf-8 -*-
"""Extrai a timeline do projeto Windows Movie Maker da mae da Clara.

Le o .wlmp (XML) e escreve data/original_mae.csv, o registo fiel do trabalho
dela. Este CSV e INTOCAVEL depois de criado: ver docs/BRIEFING.md, seccao 12.

Modelo de tempo (validado contra a duracao real do MP4 exportado, 1410.4s):
cada extent avanca o cursor por gapBefore, recua pela duracao da transicao de
entrada (o crossfade sobrepoe-se ao clip anterior) e avanca pela sua duracao.

Uso:  py -3.11 scripts/parse_wlmp.py
"""
import csv
import hashlib
import os
import sys
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

MEDIA = r"C:\casamento-video-media\trabalho\00-ORIGINAL-MAE"
WLMP = os.path.join(MEDIA, "Clara e Tiago.wlmp")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "original_mae.csv")

MOVIMENTO = {
    "PanAndZoomEffectZoomInFullToCenterTemplate": "Zoom in",
    "PanAndZoomEffectZoomOutFullToCenterTemplate": "Zoom out",
}
TRANSICAO = {"CrossfadeTransitionTemplate": "Crossfade"}

COLUNAS = [
    "ordem", "faixa", "tipo", "inicio_s", "fim_s", "duracao_s", "ficheiro",
    "caminho_original", "encontrado", "caminho_disco", "in_s", "out_s",
    "movimento", "transicao", "transicao_s", "texto_ecra", "largura",
    "altura", "resolucao_ok",
]


def normalizar(nome):
    """Reduz o nome a letras e digitos, sem extensao.

    O WeTransfer trocou separadores em alguns nomes (' - ' virou '   '), pelo
    que a correspondencia literal falha em ficheiros que existem mesmo. Isto
    e so para reconciliar nomes, nunca para declarar duplicados: para isso o
    BRIEFING seccao 12 exige hash do conteudo.
    """
    return re.sub(r"[^a-z0-9]+", "", os.path.splitext(nome)[0].lower())


def indexar_disco(raiz):
    """Devolve (mapa exato em minusculas, mapa normalizado)."""
    exato = defaultdict(list)
    aprox = defaultdict(list)
    for base, _dirs, ficheiros in os.walk(raiz):
        for f in ficheiros:
            caminho = os.path.join(base, f)
            exato[f.lower()].append(caminho)
            aprox[normalizar(f)].append(caminho)
    return exato, aprox


def texto_do_titulo(clip):
    for bp in clip.iter():
        if bp.get("Name") == "string":
            v = bp.get("Value")
            if v is None and len(bp):
                v = " ".join(e.get("Value") or "" for e in bp)
            return (v or "").replace("\r", " ").replace("\n", " ").strip()
    return ""


def duracao(clip):
    if clip.tag in ("ImageClip", "TitleClip"):
        return float(clip.get("duration") or 0)
    ini = float(clip.get("inTime") or 0)
    fim = float(clip.get("outTime") or 0)
    vel = float(clip.get("speed") or 1) or 1.0
    return (fim - ini) / vel


def transicao_de(clip):
    no = clip.find("Transitions")
    if no is None or not len(no):
        return "", 0.0
    e = no[0]
    return TRANSICAO.get(e.get("effectTemplateID"), e.get("effectTemplateID")), float(e.get("duration") or 0)


def movimento_de(clip):
    e = clip.find("Effects")
    if e is None:
        return "Nenhum"
    for f in e.iter("PanAndZoomShapeEffect"):
        return MOVIMENTO.get(f.get("effectTemplateID"), f.get("effectTemplateID"))
    return "Nenhum"


def percorrer(selector, extents_por_id):
    """Devolve (clip, inicio_s, fim_s) pela ordem da faixa."""
    cursor = 0.0
    saida = []
    for ref in selector.find("ExtentRefs"):
        clip = extents_por_id[ref.get("id")]
        cursor += float(clip.get("gapBefore") or 0)
        _, td = transicao_de(clip)
        cursor -= td
        inicio = cursor
        cursor += duracao(clip)
        saida.append((clip, inicio, cursor))
    return saida


def main():
    if not os.path.exists(WLMP):
        sys.exit("Nao encontrei o .wlmp em %s" % WLMP)

    raiz = ET.parse(WLMP).getroot()
    itens = {m.get("id"): m for m in raiz.find("MediaItems")}
    extents = raiz.find("Extents")
    por_id = {c.get("extentID"): c for c in extents}
    selectors = [c for c in extents if c.tag == "ExtentSelector"]

    principal = next(s for s in selectors if s.get("primaryTrack") == "true")
    outras = [s for s in selectors if s is not principal and len(s.find("ExtentRefs"))]

    faixas = [("video", principal)]
    for s in outras:
        tags = {por_id[r.get("id")].tag for r in s.find("ExtentRefs")}
        nome = "musica" if tags == {"AudioClip"} else "texto"
        faixas.append((nome, s))

    disco, disco_aprox = indexar_disco(MEDIA)
    linhas = []
    em_falta = []
    renomeados = set()

    for nome_faixa, selector in faixas:
        for clip, inicio, fim in percorrer(selector, por_id):
            mid = clip.get("mediaItemID")
            item = itens.get(mid)
            caminho_orig = item.get("filePath") if item is not None else ""
            ficheiro = os.path.basename(caminho_orig.replace("\\", "/")) if caminho_orig else ""

            caminho_disco, encontrado = "", ""
            if ficheiro:
                achados = disco.get(ficheiro.lower(), [])
                encontrado = "Sim"
                if not achados:
                    achados = disco_aprox.get(normalizar(ficheiro), [])
                    encontrado = "Sim (nome aproximado)" if achados else "Nao"
                caminho_disco = achados[0] if achados else ""
                if not achados:
                    em_falta.append((ficheiro, caminho_orig))
                elif encontrado.startswith("Sim ("):
                    renomeados.add((ficheiro, os.path.basename(achados[0])))

            larg = item.get("arWidth") if item is not None else ""
            alt = item.get("arHeight") if item is not None else ""

            if clip.tag == "ImageClip":
                tipo = "foto"
            elif clip.tag == "VideoClip":
                tipo = "video"
            elif clip.tag == "AudioClip":
                tipo = "musica"
            else:
                tipo = "cartao"

            transicao, td = transicao_de(clip)

            # A infancia da Clara e digitalizada. Marca para upscaling tudo o
            # que nao chegue a 1280 de largura. Ver BRIEFING seccao 6.
            resolucao_ok = ""
            if tipo in ("foto", "video") and larg:
                resolucao_ok = "Sim" if int(larg) >= 1280 else "Nao"

            linhas.append({
                "ordem": 0,
                "faixa": nome_faixa,
                "tipo": tipo,
                "inicio_s": round(inicio, 3),
                "fim_s": round(fim, 3),
                "duracao_s": round(fim - inicio, 3),
                "ficheiro": ficheiro,
                "caminho_original": caminho_orig,
                "encontrado": encontrado,
                "caminho_disco": caminho_disco,
                "in_s": round(float(clip.get("inTime")), 3) if clip.get("inTime") else "",
                "out_s": round(float(clip.get("outTime")), 3) if clip.get("outTime") else "",
                "movimento": movimento_de(clip) if clip.tag == "ImageClip" else "",
                "transicao": transicao,
                "transicao_s": round(td, 3) if td else "",
                "texto_ecra": texto_do_titulo(clip) if clip.tag == "TitleClip" else "",
                "largura": larg or "",
                "altura": alt or "",
                "resolucao_ok": resolucao_ok,
            })

    ordem_faixa = {"video": 0, "texto": 1, "musica": 2}
    linhas.sort(key=lambda r: (r["inicio_s"], ordem_faixa.get(r["faixa"], 9)))
    for i, r in enumerate(linhas, 1):
        r["ordem"] = i

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    print("Escrito %s (%d linhas)" % (OUT, len(linhas)))
    if renomeados:
        print("Reconciliados por nome aproximado: %d" % len(renomeados))
        for antigo, novo in sorted(renomeados):
            print("   .wlmp: %s" % antigo)
            print("   disco: %s" % novo)
    unicos = sorted({f for f, _ in em_falta})
    print("Referencias sem ficheiro em disco: %d ocorrencias, %d nomes unicos"
          % (len(em_falta), len(unicos)))
    for f in unicos:
        print("   FALTA  %s" % f)


if __name__ == "__main__":
    main()
