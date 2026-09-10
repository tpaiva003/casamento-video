# -*- coding: utf-8 -*-
"""Agrupa as fotos por evento, sugere bloco e gera data/decisoes.csv.

Tres passos:

1. ANO. Onde nao ha EXIF nem legenda, estima pela posicao na timeline dela.
   Dentro de cada bloco dela as fotos vao mais ou menos por idade, por isso
   da para interpolar entre ancoras conhecidas. E uma estimativa e vai
   marcada como tal, para ninguem a confundir com um facto.

2. EVENTO. Corta a sequencia dela em eventos. Comeca evento novo quando muda
   o dia do EXIF, quando muda o bloco, ou quando aparece uma legenda que nomeia
   outro sitio ou outra coisa.

3. BLOCO. Sugere um dos 7 blocos da estrutura nova, cruzando ano e pessoa.

O ficheiro que sai respeita o esquema fixo do BRIEFING seccao 9. Nao acrescenta
nem reordena colunas. A legenda original da mae da Clara fica em
data/inventario.csv, ligada pelo mesmo id.

Uso:  py -3.11 scripts/gerar_decisoes.py
"""
import csv
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
OUT = os.path.join(REPO, "data", "decisoes.csv")

NASCIMENTO = 1995
DURACAO_OMISSAO = 4

COLUNAS = [
    "id", "ordem", "bloco", "ficheiro", "tipo", "pessoa", "ano", "evento",
    "duracao_s", "in_s", "out_s", "movimento", "texto_ecra", "resolucao_ok",
    "voto_tiago", "voto_clara", "nota_tiago", "nota_clara", "estado",
]

BLOCOS = {
    0: "Abertura", 1: "Primeiros anos", 2: "Infancia", 3: "Adolescencia",
    4: "O encontro", 5: "A dois", 6: "Fecho",
}


def sugerir_bloco(ano, pessoa):
    """Cruza idade e pessoa. Ver BRIEFING seccao 5.

    O periodo 2009 a 2013 e ambiguo: e adolescencia dos dois E o encontro.
    Desempata a pessoa: se estao juntos na foto, e o bloco 4.
    """
    if not ano:
        return ""
    a = int(ano)
    if pessoa == "Ambos":
        if a <= 2012:
            return 4
        return 5
    if a <= 2001:
        return 1
    if a <= 2007:
        return 2
    if a <= 2013:
        return 3
    return 5


def texto_curto(legenda):
    """Extrai nome de sitio ou idade da legenda dela.

    A regra do briefing e "poucas palavras, datas e nomes, nunca frases". As
    legendas dela sao frases inteiras, por isso nao se copiam. Aproveita-se so
    o nucleo: "Em Veneza" -> "Veneza", "Aos 16 anos" -> "16 anos".
    """
    if not legenda:
        return ""
    t = legenda.strip()
    m = re.match(r"^(?:Em|Na|No|Nos|Nas)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'\-]*"
                 r"(?:\s+(?:de|da|do|dos|das)?\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'\-]*)?)"
                 r"\s*[,.;]?\s*(\d{4})?\s*\.?$", t)
    if m:
        return (m.group(1) + (", " + m.group(2) if m.group(2) else "")).strip()
    m = re.match(r"^[Aa]os\s+(\d{1,2})\s+anos\s*\.?$", t)
    if m:
        return "%s anos" % m.group(1)
    m = re.match(r"^[Cc]om\s+(\d{1,2})\s+anos\s*\.?$", t)
    if m:
        return "%s anos" % m.group(1)
    return ""


def nome_evento(legenda, ano, bloco_mae):
    if legenda:
        curto = texto_curto(legenda)
        if curto:
            return curto
        palavras = re.sub(r"\s+", " ", legenda).strip()
        return palavras[:38].rstrip(" ,.;") or (bloco_mae or "Sem evento")
    if ano:
        return "%s, %s" % (bloco_mae or "sem contexto", ano)
    return bloco_mae or "Por classificar"


# Ancora no arranque de cada bloco dela, tirada dos cartoes que ela propria
# escreveu. "Era uma vez uma menina que nasceu no ano da graca de 1995" abre o
# bloco Clara, "um menino loiro que tambem nasceu em 1995" abre o do Tiago, e
# "Em 2011 a Clara e o Tiago conheceram-se" abre o do encontro.
SEMENTES = {"Clara": NASCIMENTO, "Tiago": NASCIMENTO, "O encontro": 2011}


def estimar_anos(linhas):
    """Interpola o ano dentro de cada bloco dela, entre ancoras conhecidas.

    Duas cautelas, porque a ordem dela so e cronologica na primeira parte de
    cada bloco e depois passa a tematica (viagens, passeios, gostos):

    1. Semeia o inicio do bloco com o ano que ela propria escreveu no cartao.
       Sem isto, as fotos de bebe herdam o ano da primeira foto digital que
       aparecer a seguir, que pode ser 15 anos mais tarde.
    2. So interpola entre ancoras que avancam no tempo. Se a ancora seguinte e
       anterior a atual, a ordem ali nao e cronologica e o honesto e deixar o
       ano em branco em vez de inventar um.

    Tudo o que sai daqui vai marcado como estimativa, nunca como facto.
    """
    por_bloco = defaultdict(list)
    for r in linhas:
        if r["usada_pela_mae"] == "Sim" and r["bloco_original"]:
            por_bloco[r["bloco_original"]].append(r)

    estimados = recusados = 0
    for bloco, fotos in por_bloco.items():
        fotos.sort(key=lambda r: float(r["inicio_original_s"]))
        ancoras = [(i, int(r["ano"])) for i, r in enumerate(fotos) if r["ano"]]
        if bloco in SEMENTES:
            ancoras.insert(0, (-1, SEMENTES[bloco]))
        if len(ancoras) < 2:
            continue
        for i, r in enumerate(fotos):
            if r["ano"]:
                continue
            antes = [a for a in ancoras if a[0] < i]
            depois = [a for a in ancoras if a[0] > i]
            if not (antes and depois):
                recusados += 1
                continue
            (i0, a0), (i1, a1) = antes[-1], depois[0]
            if a1 < a0:
                # Aqui a ordem dela nao e cronologica. Nao inventar.
                recusados += 1
                continue
            frac = (i - i0) / (i1 - i0)
            ano = int(round(a0 + frac * (a1 - a0)))
            r["ano"] = str(max(NASCIMENTO, min(2026, ano)))
            r["fonte_ano"] = "estimado (ordem dela)"
            estimados += 1
    return estimados, recusados


def movimento(indice, aspeto, orientacao):
    """Alterna o movimento para nao repetir o erro do vídeo original.

    Ela usou o mesmo Zoom in ao centro 252 vezes seguidas. Aqui alterna-se, e
    fotos muito panoramicas levam pan em vez de zoom, porque e onde o pan
    ganha alguma coisa.
    """
    if indice % 7 == 6:
        return "Nenhum"
    if orientacao == "horizontal" and aspeto >= 1.55:
        return "Pan E-D" if indice % 2 == 0 else "Pan D-E"
    return "Zoom in" if indice % 2 == 0 else "Zoom out"


def main():
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))

    estimados, recusados = estimar_anos(linhas)

    # Ordena pela timeline dela; as que ela nao usou vao para o fim.
    def chave(r):
        if r["usada_pela_mae"] == "Sim" and r["inicio_original_s"]:
            return (0, float(r["inicio_original_s"]))
        return (1, r["ficheiro"].lower())

    linhas.sort(key=chave)

    # Passo 2: cortar em eventos.
    eventos, atual, ultima = [], [], None
    for r in linhas:
        novo = False
        if ultima is None:
            novo = True
        else:
            if r["bloco_original"] != ultima["bloco_original"]:
                novo = True
            if r["data_exif"] and ultima["data_exif"] and r["data_exif"] != ultima["data_exif"]:
                novo = True
            if r["legenda_mae"] and r["legenda_mae"] != ultima["legenda_mae"]:
                novo = True
            if r["usada_pela_mae"] != ultima["usada_pela_mae"]:
                novo = True
        if novo and atual:
            eventos.append(atual)
            atual = []
        atual.append(r)
        ultima = r
    if atual:
        eventos.append(atual)

    for grupo in eventos:
        cabeca = grupo[0]
        nome = nome_evento(cabeca["legenda_mae"], cabeca["ano"], cabeca["bloco_original"])
        for r in grupo:
            r["_evento"] = nome

    # Passo 3: bloco sugerido, e ordenacao final por bloco e ano.
    for r in linhas:
        r["_bloco"] = sugerir_bloco(r["ano"], r["pessoa"])

    def chave_final(r):
        b = r["_bloco"] if r["_bloco"] != "" else 9
        return (b, int(r["ano"]) if r["ano"] else 9999, r["_evento"], r["ficheiro"].lower())

    linhas.sort(key=chave_final)

    saida = []
    contador = defaultdict(int)
    for i, r in enumerate(linhas):
        b = r["_bloco"]
        contador[b] += 1
        saida.append({
            "id": r["id"],
            "ordem": contador[b],
            "bloco": b,
            "ficheiro": r["ficheiro"],
            "tipo": "foto",
            "pessoa": r["pessoa"],
            "ano": r["ano"],
            "evento": r["_evento"],
            "duracao_s": DURACAO_OMISSAO,
            "in_s": "",
            "out_s": "",
            "movimento": movimento(i, float(r["aspeto"]), r["orientacao"]),
            "texto_ecra": texto_curto(r["legenda_mae"]),
            "resolucao_ok": r["resolucao_ok"],
            "voto_tiago": "",
            "voto_clara": "",
            "nota_tiago": "",
            "nota_clara": "",
            "estado": "",
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(saida)

    print("Escrito %s (%d linhas)" % (OUT, len(saida)))
    print("Anos estimados pela ordem dela: %d" % estimados)
    print("Anos que recusei estimar (ordem dela nao e cronologica ali): %d" % recusados)
    com_ano = sum(1 for r in saida if r["ano"])
    print("Com ano: %d de %d (%.0f%%)" % (com_ano, len(saida), 100 * com_ano / len(saida)))
    print("Eventos identificados: %d" % len({r["evento"] for r in saida}))
    print()
    print("%-6s %-18s %6s %8s   %s" % ("BLOCO", "NOME", "FOTOS", "SE 4s", "ALVO"))
    alvos = {0: 45, 1: 150, 2: 160, 3: 160, 4: 130, 5: 220, 6: 35}
    for b in [0, 1, 2, 3, 4, 5, 6, ""]:
        n = sum(1 for r in saida if r["bloco"] == b)
        if not n:
            continue
        nome = BLOCOS.get(b, "POR CLASSIFICAR")
        alvo = alvos.get(b)
        seg = n * DURACAO_OMISSAO
        marca = "%ds" % alvo if alvo else "n/a"
        excesso = ""
        if alvo:
            excesso = "  %+.0f%%" % (100 * (seg - alvo) / alvo)
        print("%-6s %-18s %6d %7ds   %s%s" % (b if b != "" else "?", nome, n, seg, marca, excesso))
    print()
    print("%-4s %s" % ("N", "MAIORES EVENTOS (a regra e maximo 4 ou 5 fotos seguidas)"))
    cont = defaultdict(int)
    for r in saida:
        cont[r["evento"]] += 1
    for nome, n in sorted(cont.items(), key=lambda x: -x[1])[:15]:
        print("%-4d %s" % (n, nome[:70]))


if __name__ == "__main__":
    main()
