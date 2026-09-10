# -*- coding: utf-8 -*-
"""Relatorio legivel da timeline da mae da Clara, a partir de original_mae.csv.

Nao altera nada. Uso:  py -3.11 scripts/relatorio_original.py
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(REPO, "data", "original_mae.csv")


def mmss(s):
    s = float(s)
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def main():
    with open(CSV, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))

    video = [r for r in linhas if r["faixa"] == "video"]
    musica = [r for r in linhas if r["faixa"] == "musica"]
    texto = [r for r in linhas if r["faixa"] == "texto"]

    fim = max(float(r["fim_s"]) for r in video)
    print("=" * 74)
    print("TIMELINE ORIGINAL  |  %s  (%.0f s)" % (mmss(fim), fim))
    print("=" * 74)
    fotos = [r for r in video if r["tipo"] == "foto"]
    print("Faixa video : %d clips  (%d fotos, %d cartoes, %d video)"
          % (len(video), len(fotos),
             sum(1 for r in video if r["tipo"] == "cartao"),
             sum(1 for r in video if r["tipo"] == "video")))
    print("Faixa texto : %d legendas sobrepostas" % len(texto))
    print("Faixa musica: %d clips de audio" % len(musica))
    dur = sorted(float(r["duracao_s"]) for r in fotos)
    print("Duracao das fotos: min %.1fs  mediana %.1fs  max %.1fs  media %.1fs"
          % (dur[0], dur[len(dur) // 2], dur[-1], sum(dur) / len(dur)))
    baixa = [r for r in video if r["resolucao_ok"] == "Nao"]
    print("Fotos abaixo de 1280px de largura: %d de %d" % (len(baixa), len(fotos)))

    print()
    print("=" * 74)
    print("MAPA MUSICAL")
    print("=" * 74)
    print("%-6s %-6s %-7s  %-8s  %s" % ("ENTRA", "SAI", "DURA", "TROCO", "FAIXA"))
    for r in musica:
        ini, f, d = float(r["inicio_s"]), float(r["fim_s"]), float(r["duracao_s"])
        troco = "%s-%s" % (mmss(r["in_s"] or 0), mmss(r["out_s"] or 0))
        nome = r["ficheiro"] or "(?)"
        if len(nome) > 46:
            nome = nome[:43] + "..."
        falta = "  [FICHEIRO EM FALTA]" if r["encontrado"] == "Nao" else ""
        print("%-6s %-6s %5.1fs  %-8s  %s%s" % (mmss(ini), mmss(f), d, troco, nome, falta))
    tm = sum(float(r["duracao_s"]) for r in musica)
    print("-" * 74)
    print("Soma das faixas: %.0f s (%s). Timeline de video: %.0f s (%s)."
          % (tm, mmss(tm), fim, mmss(fim)))
    if tm > fim:
        print("EXCEDENTE: %.0f s de musica alem do fim do video, cortados na exportacao."
              % (tm - fim))

    print()
    print("=" * 74)
    print("TEXTO NO ECRA  (%d ocorrencias)" % len([r for r in linhas if r["texto_ecra"]]))
    print("=" * 74)
    for r in sorted([r for r in linhas if r["texto_ecra"]], key=lambda r: float(r["inicio_s"])):
        marca = "CARTAO " if r["faixa"] == "video" else "legenda"
        print("%-6s %s  %4.1fs  %s" % (mmss(r["inicio_s"]), marca,
                                       float(r["duracao_s"]), r["texto_ecra"]))

    print()
    print("=" * 74)
    print("SEQUENCIA DE VIDEO, agrupada por faixa musical")
    print("=" * 74)
    for i, m in enumerate(musica):
        ini, f = float(m["inicio_s"]), float(m["fim_s"])
        nome = m["ficheiro"] or "(?)"
        dentro = [r for r in video if ini <= float(r["inicio_s"]) < f]
        print()
        print("- FAIXA %d  %s a %s  |  %s" % (i + 1, mmss(ini), mmss(min(f, fim)), nome))
        print("  %d clips" % len(dentro))
        for r in dentro:
            et = ""
            if r["tipo"] == "cartao":
                et = "  <CARTAO> %s" % r["texto_ecra"]
            elif r["tipo"] == "video":
                et = "  <VIDEO>"
            leg = [t for t in texto
                   if float(r["inicio_s"]) <= float(t["inicio_s"]) < float(r["fim_s"])]
            if leg:
                et += "   texto: " + " / ".join(t["texto_ecra"] for t in leg)
            print("    %-6s %4.1fs  %-34s %-8s%s"
                  % (mmss(r["inicio_s"]), float(r["duracao_s"]),
                     (r["ficheiro"] or "")[:34], r["movimento"], et))


if __name__ == "__main__":
    main()
