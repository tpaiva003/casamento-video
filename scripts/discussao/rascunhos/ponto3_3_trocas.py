# RASCUNHO do ponto 3.3, guardado a 29 de setembro a partir da pasta temporaria da sessao. Faz a lista
# das trocas que os agentes mediram (data/discussao/ponto3_3_analise.json). Os tempos
# de corpo e as entradas da 095 estao escritos a mao para a montagem de 29/09 (rev 903): noutra
# montagem, usar o scripts/discussao/comum.py, que procura pelo nome.
# -*- coding: utf-8 -*-
"""Ponto 3.3: a lista das trocas entre leitos da v3 de hoje, ja com os pontos de entrada da 095.
Para cada troca: a musica que sai, onde esta no ficheiro quando comeca a descer, a que entra, e o
que esta no ecra a volta do corte. So le; escreve trocas.json nesta pasta."""
import json, os, sys
sys.path.insert(0, r"C:\casamento-video\scripts")
os.chdir(r"C:\casamento-video")
import render
D = os.path.join("C:/casamento-video", "saida", "discussao", "ponto3_3")
os.makedirs(D, exist_ok=True)
IN_095 = [(473.82, "Inês Homem de Melo", 2.7), (499.62, "Já Sei Namorar", 34.9), (37.87, "Lang Lang", 14.6),
          (344.32, "Tiago Celebration", 0.81), (712.52, "Bachman", 60.8), (573.22, "Steppenwolf", 0.55),
          (613.72, "Filhos Do", 7.0)]

est = render.carregar_montagem("v3", None)
ent = render.som_do_ficheiro("v3", est["fim"])
for t, pref, novo in IN_095:
    alvo = [e for e in ent if abs(e["quando"] - t) < 0.2 and e["ficheiro"].startswith(pref)]
    assert len(alvo) == 1, pref
    alvo[0]["in_s"] = novo
desvio = est["desvio"]
clips = []
for c in est["resto"]:
    ini = float(c["inicio_s"]) - desvio
    clips.append({"ordem": c.get("ordem"), "tipo": c.get("tipo"), "ini": round(ini, 2),
                  "dur": float(c["duracao_s"]), "texto": (c.get("texto_ecra") or "")[:90],
                  "ficheiro": (c.get("ficheiro") or "")[:40]})
leitos = sorted([e for e in ent if not render.entra_depressa(e)
                 and not e["ficheiro"].startswith(("Candidato", "rebobinar"))], key=lambda e: e["quando"])
efeitos = [e for e in ent if e["ficheiro"].startswith(("Candidato", "rebobinar"))]
trocas = []
for a, b in zip(leitos, leitos[1:]):
    corte = b["quando"]
    fim_a = a["quando"] + a["dura"]
    info = {"corte_corpo": round(corte, 2), "corte_filme": round(corte + render_fanfarra, 2) if (render_fanfarra := est.get("fanfarra_s", 0) or 0) else None,
            "sai": a["ficheiro"], "sai_caminho": a["caminho"], "sai_quando": a["quando"], "sai_in": a["in_s"],
            "sai_no_ficheiro_ao_corte": round(a["in_s"] + corte - a["quando"], 2),
            "sai_acaba_corpo": round(fim_a, 2), "sai_cruza": a.get("cruza"),
            "sai_dura_ficheiro": a.get("dura_medida"),
            "entra": b["ficheiro"], "entra_caminho": b["caminho"], "entra_in": b["in_s"],
            "entra_nota": b.get("nota", ""),
            "encosta": fim_a <= corte + 0.05 and not a.get("cruza"),
            "efeitos_perto": [(x["ficheiro"][:20], round(x["quando"], 2), round(x["dura"], 2)) for x in efeitos
                              if abs(x["quando"] - corte) < 10],
            "clips": [c for c in clips if c["ini"] < corte + 10 and c["ini"] + c["dur"] > corte - 12]}
    trocas.append(info)
json.dump({"desvio": desvio, "fim": est["fim"], "trocas": trocas}, open(os.path.join(D, "trocas.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for x in trocas:
    print("%7.2f  %-28s (no ficheiro %6.2f)  ->  %-28s in %.2f" % (x["corte_corpo"], x["sai"][:28],
          x["sai_no_ficheiro_ao_corte"], x["entra"][:28], x["entra_in"]))
    for c in x["clips"]:
        if abs(c["ini"] - x["corte_corpo"]) < 0.3:
            print("          no corte: clip %s %s %.1fs  %s" % (c["ordem"], c["tipo"], c["dur"], c["texto"][:60]))
