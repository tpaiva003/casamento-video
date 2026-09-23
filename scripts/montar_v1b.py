# -*- coding: utf-8 -*-
"""Constroi a v1b: a v1a mais dois tratamentos, e por isso cabe nos 900 s.

REGRA DA v1b: tudo o que a v1a decidiu mantem-se. Mesma ordem, mesmos textos,
mesmos cartoes, nenhuma foto cortada nem acrescentada. O que muda e COMO as
fotos aparecem, e sao duas coisas so:

  FUNDO DESFOCADO nas verticais. 95 das 284 fotos dela sao verticais, ou seja
  33 por cento. Com barras pretas, um terco do filme aparece encaixotado numa
  faixa central. Nao custa um segundo de tempo, e numa cortina conta ainda
  mais, porque preto projetado e cinzento sujo.

  RAJADA nas corridas de fotos do mesmo assunto. E ela que paga a conta do
  tempo: a v1a precisou de 18:20 porque nao havia maneira de meter 297
  entradas em 900 s sem violar a regra dos 3 segundos. Comprimindo as corridas
  liberta-se o tempo que falta, e as fotos que ficam ganham MAIS tempo do que
  teriam na v1a, nao menos.

QUAIS AS CORRIDAS QUE VIRAM RAJADA, e porque. O criterio nao e o tamanho, e a
natureza do bloco:

  SIM, repeticao tematica. Caminhadas, colegas de trabalho dela, colegas dele,
  poses do mesmo genero. Sao blocos onde a leitura e coletiva: ninguem precisa
  de ler cada foto, o que se le e a quantidade e a energia.

  NAO, blocos de relacao. As 20 fotos sem legenda de "Cumplicidades" sao o
  casal junto e sao o centro emocional do filme. Acelerar ali seria acelerar
  precisamente a parte que deve respirar. Numa versao anterior deste calculo
  eu tinha-as classificado por engano como fotos do Baile de Finalistas e
  propus rajada. Estava errado e fica registado.

  A DECIDIR. Tres corridas ficam no meio e estao marcadas no CSV com nota:
  "Com o Henrique (o mano)", "Com o pai" e "E le glamour". Sao relacao, mas
  sao repetitivas. Entram com --agressivo.

Uso:
    py -3.11 scripts/montar_v1b.py
    py -3.11 scripts/montar_v1b.py --agressivo      inclui as tres duvidosas
    py -3.11 scripts/montar_v1b.py --total 900
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corridas as mod_corridas

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
DESTINO = os.path.join(REPO, "data", "montagens")

TOTAL_ALVO = 900.0
CROSSFADE = 0.7
PISO_DOMINANTE = 3.0
PISO_CARTAO = 3.6
TETO_DURACAO = 9.0
# 11/09/2026: o Tiago viu a demo e disse "as fotos dos desportos estao a mudar
# muito muito rapido, aumenta a velocidade em 25% para testar". Fotos a mudar
# depressa de mais pedem MAIS tempo, portanto o que se aumenta e a duracao:
# 0,45 -> 0,5625, ou seja 14 fotogramas em vez de 11. Fica dito de forma
# explicita porque a frase, a letra, diz o contrario do efeito pretendido.
DUR_RAJADA = 0.5625        # 14 fotogramas a 25 fps
MIN_CORRIDA = 4

# Corridas que viram rajada sem discussao, identificadas pela seccao e pelo
# instante em que comecam na timeline dela.
RAJADA_CERTAS = {
    (469.0, "Clara"),                          # Caminhadas pelo Parque das Serras
    (700.0, "Colegas de trabalho (dela)"),
    (866.0, "Tiago"),                          # Vendo o mundo de pernas p'ro ar
    (1023.0, "Colegas de trabalho (dele)"),
}
RAJADA_DUVIDOSAS = {
    (503.0, "Familia"),                        # Com o pai
    (534.0, "Familia"),                        # Com o Henrique (o mano)
    (1117.0, "O encontro"),                    # E le glamour
}
NUNCA = {(1234.0, "Cumplicidades")}            # o casal junto, nao se acelera

COLUNAS = ["ordem", "id", "tipo", "seccao", "ficheiro", "duracao_s",
           "transicao_s", "inicio_s", "fim_s", "dominante_s", "solo_s",
           "movimento", "texto_ecra", "tratamento", "duracao_original_s",
           "variacao_pct", "fonte_imagem", "nota"]


def perto(a, conjunto, seccao, margem=12.0):
    return any(s == seccao and abs(a - t) <= margem for t, s in conjunto)


def main():
    total = TOTAL_ALVO
    agressivo = "--agressivo" in sys.argv
    if "--total" in sys.argv:
        total = float(sys.argv[sys.argv.index("--total") + 1])

    video = mod_corridas.carregar()
    grupos = [c for c in mod_corridas.detetar(video) if len(c) >= MIN_CORRIDA]

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    por_nome = {r["ficheiro"].lower(): r for r in inv}

    em_rajada, duvidosas = set(), set()
    for c in grupos:
        ini, sec = float(c[0]["inicio_s"]), c[0]["_seccao"]
        if perto(ini, NUNCA, sec):
            continue
        if perto(ini, RAJADA_CERTAS, sec):
            for r in c:
                em_rajada.add(r["ordem"])
        elif perto(ini, RAJADA_DUVIDOSAS, sec):
            for r in c:
                duvidosas.add(r["ordem"])
                if agressivo:
                    em_rajada.add(r["ordem"])

    fixos = [r for r in video if r["tipo"] == "video"]
    rajada = [r for r in video if r["ordem"] in em_rajada]
    normais = [r for r in video if r["tipo"] != "video" and r["ordem"] not in em_rajada]

    orcamento = total + (len(video) - 1) * CROSSFADE
    orcamento -= sum(float(r["duracao_s"]) for r in fixos)
    # As rajadas nao tem transicao, portanto nao devolvem crossfade ao orcamento.
    orcamento -= len(rajada) * (DUR_RAJADA + CROSSFADE)

    pisos = [PISO_CARTAO if r["tipo"] == "cartao" else PISO_DOMINANTE + CROSSFADE
             for r in normais]
    pisos = [max(p, PISO_DOMINANTE + CROSSFADE) for p in pisos]
    folga = orcamento - sum(pisos)

    print("v1b  |  alvo %s  |  crossfade %.1f s  |  %s"
          % (mod_corridas.mmss(total), CROSSFADE,
             "agressivo" if agressivo else "conservador"))
    print("  entradas: %d   rajada: %d   normais: %d   fixas: %d"
          % (len(video), len(rajada), len(normais), len(fixos)))
    print("  duvidosas por decidir: %d fotos" % len(duvidosas))
    print("  orcamento de duracoes: %.0f s   pisos: %.0f s   folga: %.0f s"
          % (orcamento, sum(pisos), folga))
    if folga < 0:
        print("  NAO CABE. Faltam %.0f s. Alarga o total ou acrescenta rajadas."
              % -folga)
        return
    print()

    duracoes = sorted(float(r["duracao_s"]) for r in normais)
    mediana = duracoes[len(duracoes) // 2]
    pesos = [max(0.0, float(r["duracao_s"]) - mediana) for r in normais]
    soma = sum(pesos) or 1.0
    finais = [min(p + folga * w / soma, TETO_DURACAO) for p, w in zip(pisos, pesos)]
    sobra = orcamento - sum(finais)
    for _ in range(40):
        if abs(sobra) < 0.5:
            break
        margem = [i for i, d in enumerate(finais) if d < TETO_DURACAO - 0.01]
        if not margem:
            break
        por = sobra / len(margem)
        for i in margem:
            finais[i] = min(TETO_DURACAO, max(pisos[i], finais[i] + por))
        sobra = orcamento - sum(finais)

    mapa = {r["ordem"]: d for r, d in zip(normais, finais)}
    for r in rajada:
        mapa[r["ordem"]] = DUR_RAJADA
    for r in fixos:
        mapa[r["ordem"]] = float(r["duracao_s"])

    linhas, cursor = [], 0.0
    for i, r in enumerate(video, 1):
        d = mapa[r["ordem"]]
        e_rajada = r["ordem"] in em_rajada
        t = 0.0 if (i == 1 or e_rajada) else CROSSFADE
        inicio = cursor - t if i > 1 else 0.0
        fim = inicio + d
        cursor = fim
        rinv = por_nome.get((r["ficheiro"] or "").lower())
        vertical = bool(rinv) and rinv["orientacao"] == "vertical"
        if r["tipo"] == "cartao":
            trat = "fiel"
        elif e_rajada:
            trat = "rajada"
        elif vertical:
            trat = "fundo"
        else:
            trat = "fiel"
        nota = ""
        if r["ordem"] in duvidosas:
            nota = "corrida duvidosa: relacao mas repetitiva, decidir se vai a rajada"
        elif r["tipo"] == "video":
            nota = "fanfarra, fica inteira"
        linhas.append({
            "ordem": i, "id": (rinv or {}).get("id", ""), "tipo": r["tipo"],
            "seccao": r["_seccao"], "ficheiro": r["ficheiro"],
            "duracao_s": round(d, 2), "transicao_s": round(t, 2),
            "inicio_s": round(inicio, 2), "fim_s": round(fim, 2),
            "dominante_s": round(d - t, 2), "solo_s": round(d - 2 * t, 2),
            "movimento": "Nenhum" if e_rajada else r["movimento"],
            "texto_ecra": r["_legenda"], "tratamento": trat,
            "duracao_original_s": float(r["duracao_s"]),
            "variacao_pct": round(100 * (d - float(r["duracao_s"])) / float(r["duracao_s"]), 1),
            "fonte_imagem": "", "nota": nota,
        })

    os.makedirs(DESTINO, exist_ok=True)
    saida = os.path.join(DESTINO, "v1b.csv")
    with open(saida, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    real = linhas[-1]["fim_s"]
    fotos = [l for l in linhas if l["tipo"] == "foto" and l["tratamento"] != "rajada"]
    dom = sorted(l["dominante_s"] for l in fotos)
    print("Escrito %s" % saida)
    print("Duracao final: %s  (%.0f s)" % (mod_corridas.mmss(real), real))
    print()
    print("TRATAMENTOS")
    for t in ("fiel", "fundo", "rajada"):
        print("  %-8s %3d" % (t, sum(1 for l in linhas if l["tratamento"] == t)))
    print()
    print("TEMPO DOMINANTE, sem contar rajadas")
    print("  minimo %.2f s   mediana %.2f s   maximo %.2f s"
          % (dom[0], dom[len(dom) // 2], dom[-1]))
    print("  abaixo dos 3 s: %d de %d" % (sum(1 for d in dom if d < 2.99), len(dom)))
    print()
    print("FACE A v1a, que tem 1100 s")
    print("  poupanca das rajadas: %.0f s" % (sum(float(r["duracao_s"]) for r in rajada)
                                              - len(rajada) * DUR_RAJADA))
    print("  as fotos que ficam tem mediana %.2f s de dominancia, contra 3,00 s na v1a"
          % dom[len(dom) // 2])


if __name__ == "__main__":
    main()
