# -*- coding: utf-8 -*-
"""Constroi a v1a: a versao da mae da Clara com durações e transições afinadas.

REGRA DA v1a, dada pelo Tiago: muda-se apenas duracao e transicao. Ordem das
fotos, textos, cartoes e estrutura ficam exatamente como ela os deixou. Nao se
corta nem se acrescenta uma unica foto.

O ALVO E 18:20 (1100 s), NAO 15:00. A razao esta na aritmetica e o Tiago
decidiu com ela a frente:

  Num encadeado, cada foto e tapada pela anterior no inicio e pela seguinte no
  fim. Ha duas leituras de "tempo no ecra":
     a solo    = duracao - 2T   (so ela visivel)
     dominante = duracao - T    (ela com mais de metade da opacidade)

  Para 900 s com as 297 entradas, o tempo a solo cai para 1,5 a 2,5 s conforme
  o crossfade, ou seja abaixo da regra dos 3 s do briefing, que existe por
  causa da sala de jantar. Nao ha crossfade nenhum que resolva isso mantendo
  todas as fotos. A unica saida sem cortar fotos e alargar o filme.

CRITERIO USADO: dominante, com piso de 3,0 s. Fica dito de forma explicita
porque o outro criterio, a solo, consome o orcamento todo e obriga a que todos
os clips fiquem no piso, que e precisamente o andamento unico que queremos
evitar e o principal defeito do original.

CROSSFADE: 0,7 s em vez de 1,5 s. E a segunda coisa que a v1a pode mexer. A
1,5 s, cada foto passa 3 dos seus segundos meio transparente, o que e a razao
pela qual o original parece mole.

FOLGA: sobram 208 s depois do piso. Sao distribuidos na proporcao da enfase
que ela deu: as fotos a que ela deu mais tempo continuam a ter mais tempo.
Isto preserva a intencao editorial dela em vez de achatar tudo.

Uso:  py -3.11 scripts/montar_v1a.py
      py -3.11 scripts/montar_v1a.py --total 1100 --cross 0.7
"""
import csv
import os
import sys

import excluidas

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
DESTINO = os.path.join(REPO, "data", "montagens")

TOTAL_ALVO = 1100.0     # 18:20
CROSSFADE = 0.7
PISO_DOMINANTE = 3.0    # regra do briefing
PISO_CARTAO = 3.6       # texto precisa de mais tempo do que uma foto
TETO_DURACAO = 9.0      # ela chegou aos 12,5 s; acima de 9 arrasta

SECCOES = [
    (0.0, 20.4, "Fanfarra"), (20.4, 498.0, "Clara"),
    (498.0, 659.0, "Familia"), (659.0, 695.0, "Amigos e colegas"),
    (695.0, 761.0, "Colegas de trabalho (dela)"), (761.0, 1020.0, "Tiago"),
    (1020.0, 1071.0, "Colegas de trabalho (dele)"),
    (1071.0, 1228.0, "O encontro"), (1228.0, 1401.0, "Cumplicidades"),
    (1401.0, 9999.0, "The End"),
]

COLUNAS = [
    "ordem", "id", "tipo", "seccao", "ficheiro", "duracao_s", "transicao_s",
    "inicio_s", "fim_s", "dominante_s", "solo_s", "movimento", "texto_ecra",
    "duracao_original_s", "variacao_pct", "fonte_imagem", "nota",
]


def seccao(t):
    for ini, fim, nome in SECCOES:
        if ini <= t < fim:
            return nome
    return ""


def mmss(s):
    return "%d:%02d" % (int(float(s)) // 60, int(float(s)) % 60)


def carregar():
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    video = sorted([r for r in linhas if r["faixa"] == "video"],
                   key=lambda r: float(r["inicio_s"]))
    textos = [r for r in linhas if r["faixa"] == "texto" and r["texto_ecra"]]
    for r in video:
        ini, fim = float(r["inicio_s"]), float(r["fim_s"])
        legs = [t["texto_ecra"] for t in textos
                if ini <= float(t["inicio_s"]) < fim]
        r["_texto"] = " / ".join(legs)
        r["_seccao"] = seccao(ini)
    return video


def melhor_imagem(inv_por_nome, ficheiro):
    """Diz de onde vem a imagem: restaurada, ampliada por IA, ou original."""
    r = inv_por_nome.get((ficheiro or "").lower())
    if not r:
        return "", ""
    ident = r["id"]
    for pasta, etiqueta in ((r"C:\casamento-video-media\restauradas", "restaurada"),
                            (r"C:\casamento-video-media\upscaled-ia", "IA"),
                            (r"C:\casamento-video-media\upscaled", "lanczos")):
        if not os.path.isdir(pasta):
            continue
        for nome in os.listdir(pasta):
            if nome.startswith(ident + "__"):
                return etiqueta, os.path.join(pasta, nome)
    return "original", r["caminho"]


def main():
    total = TOTAL_ALVO
    cross = CROSSFADE
    if "--total" in sys.argv:
        total = float(sys.argv[sys.argv.index("--total") + 1])
    if "--cross" in sys.argv:
        cross = float(sys.argv[sys.argv.index("--cross") + 1])

    video = carregar()
    video, cortadas = excluidas.filtrar(video)
    if cortadas:
        print("  fora por decisao do Tiago: %d (ver scripts/excluidas.py)"
              % cortadas)
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    inv_por_nome = {r["ficheiro"].lower(): r for r in inv}

    n = len(video)
    orcamento = total + (n - 1) * cross     # soma das duracoes necessaria

    # A fanfarra fica inteira (decisao 006). Nao entra na redistribuicao.
    fixos = [r for r in video if r["tipo"] == "video"]
    ajustaveis = [r for r in video if r["tipo"] != "video"]
    orcamento -= sum(float(r["duracao_s"]) for r in fixos)

    pisos = [PISO_CARTAO if r["tipo"] == "cartao" else PISO_DOMINANTE + cross
             for r in ajustaveis]
    pisos = [max(p, PISO_DOMINANTE + cross) for p in pisos]
    soma_pisos = sum(pisos)
    folga = orcamento - soma_pisos

    print("v1a  |  alvo %s  |  crossfade %.1f s" % (mmss(total), cross))
    print("  entradas: %d   (%d ajustaveis + %d fixas)" % (n, len(ajustaveis), len(fixos)))
    print("  orcamento de duracoes: %.0f s" % orcamento)
    print("  soma dos pisos:        %.0f s" % soma_pisos)
    print("  folga para enfase:     %.0f s" % folga)
    if folga < 0:
        print("  IMPOSSIVEL: os pisos ja excedem o orcamento. Alarga o total.")
        return
    print()

    # A folga vai para quem ela destacou. O peso e o excesso da duracao dela
    # sobre a mediana: quem ela poe acima da mediana e quem ela quis destacar.
    duracoes = sorted(float(r["duracao_s"]) for r in ajustaveis)
    mediana = duracoes[len(duracoes) // 2]
    pesos = [max(0.0, float(r["duracao_s"]) - mediana) for r in ajustaveis]
    soma_pesos = sum(pesos) or 1.0

    finais = []
    for r, piso, peso in zip(ajustaveis, pisos, pesos):
        d = piso + folga * peso / soma_pesos
        finais.append(min(d, TETO_DURACAO))

    # O teto corta algum tempo: devolve-o a quem ainda tem margem.
    sobra = orcamento - sum(finais)
    for _ in range(40):
        if abs(sobra) < 0.5:
            break
        margem = [i for i, d in enumerate(finais) if d < TETO_DURACAO - 0.01]
        if not margem:
            break
        por_cada = sobra / len(margem)
        for i in margem:
            finais[i] = min(TETO_DURACAO, max(pisos[i], finais[i] + por_cada))
        sobra = orcamento - sum(finais)

    mapa = {}
    for r, d in zip(ajustaveis, finais):
        mapa[r["ordem"]] = d
    for r in fixos:
        mapa[r["ordem"]] = float(r["duracao_s"])

    linhas, cursor = [], 0.0
    for i, r in enumerate(video, 1):
        d = mapa[r["ordem"]]
        t = 0.0 if i == 1 else cross
        inicio = cursor - t if i > 1 else 0.0
        fim = inicio + d
        cursor = fim
        origem, caminho = melhor_imagem(inv_por_nome, r["ficheiro"])
        original = float(r["duracao_s"])
        linhas.append({
            "ordem": i,
            "id": (inv_por_nome.get((r["ficheiro"] or "").lower()) or {}).get("id", ""),
            "tipo": r["tipo"],
            "seccao": r["_seccao"],
            "ficheiro": r["ficheiro"],
            "duracao_s": round(d, 2),
            "transicao_s": round(t, 2),
            "inicio_s": round(inicio, 2),
            "fim_s": round(fim, 2),
            "dominante_s": round(d - t, 2),
            "solo_s": round(d - 2 * cross, 2),
            "movimento": r["movimento"],
            "texto_ecra": r["_texto"],
            "duracao_original_s": original,
            "variacao_pct": round(100 * (d - original) / original, 1) if original else "",
            "fonte_imagem": origem,
            "nota": "fanfarra, fica inteira" if r["tipo"] == "video" else "",
        })

    os.makedirs(DESTINO, exist_ok=True)
    saida = os.path.join(DESTINO, "v1a.csv")
    with open(saida, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    real = linhas[-1]["fim_s"]
    fotos = [l for l in linhas if l["tipo"] == "foto"]
    dom = sorted(l["dominante_s"] for l in fotos)
    print("Escrito %s" % saida)
    print("Duracao final: %s  (%.0f s)" % (mmss(real), real))
    print()
    print("TEMPO DOMINANTE POR FOTO")
    print("  minimo %.2f s   mediana %.2f s   maximo %.2f s"
          % (dom[0], dom[len(dom) // 2], dom[-1]))
    print("  abaixo dos 3 s: %d de %d" % (sum(1 for d in dom if d < 2.99), len(dom)))
    print()
    print("VARIACAO FACE A VERSAO DELA")
    var = sorted(l["variacao_pct"] for l in fotos)
    print("  as mais encurtadas: %.0f%%   mediana: %.0f%%   as menos: %.0f%%"
          % (var[0], var[len(var) // 2], var[-1]))
    print()
    print("%-28s %6s %8s %8s" % ("SECCAO", "CLIPS", "DELA", "v1a"))
    for _, _, nome in SECCOES:
        c = [l for l in linhas if l["seccao"] == nome]
        if not c:
            continue
        antes = sum(l["duracao_original_s"] for l in c)
        depois = sum(l["duracao_s"] for l in c)
        print("%-28s %6d %7.0fs %7.0fs" % (nome, len(c), antes, depois))


if __name__ == "__main__":
    main()
