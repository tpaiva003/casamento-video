# -*- coding: utf-8 -*-
"""O estado do filme em ingles: o estado do filme portugues com os textos trocados pela traducao revista.

Uso: py -3.11 scripts/compor_estado_en.py <estado.json> <traducao_final.json> <saida.json> [chave=valor dos creditos ...] [--intro <ficheiro>]
Para sem escrever nada se algum texto do estado ja nao for o que foi traduzido (a montagem mudou).
Nao toca no estado portugues nem na base.
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
origem, traducao, saida = sys.argv[1], sys.argv[2], sys.argv[3]
resto = sys.argv[4:]
intro = None
if "--intro" in resto:
    k = resto.index("--intro")
    intro = resto[k + 1]
    resto = resto[:k] + resto[k + 2:]

b = json.load(open(origem, encoding="utf-8"))
b = b.get("data", b)
t = json.load(open(traducao, encoding="utf-8"))
v = next(x for x in b["versoes"] if x["id"] == "demo_v3")
clips = v["clips"]

com_texto = set()
for n, c in enumerate(clips, 1):
    if c.get("t") == "video":
        continue
    if str(c.get("x") or "").strip() or any(str(s or "").strip() for s in (c.get("xf") or [])):
        com_texto.add(n)

feitos = set()
for e in t["clips"]:
    n = e["n"]
    c = clips[n - 1]
    assert c.get("t") == e["t"], ("tipo", n, c.get("t"), e["t"])
    assert (c.get("x") or "") == (e.get("x_pt") or ""), ("o texto do clip mudou", n, c.get("x"), e.get("x_pt"))
    if e.get("xf_pt") is not None:
        assert (c.get("xf") or []) == e["xf_pt"], ("os textos das fotos mudaram", n)
        assert len(e["xf_en"]) == len(e["xf_pt"]), ("xf de tamanho diferente", n)
        c["xf"] = e["xf_en"]
    if "x" in c or e.get("x_en"):
        c["x"] = e.get("x_en") or ""
    # os clips que eram fotos soltas antes de serem grupo guardam o original em "orig": nao vai ao ecra
    feitos.add(n)

faltam = sorted(com_texto - feitos)
assert not faltam, ("clips com texto sem traducao", faltam)

cr = b.setdefault("creditos", {})
tc = t.get("creditos") or {}
if tc.get("titulo_nomes"):
    assert cr.get("titulo_nomes"), "o estado nao tinha titulo por cima dos nomes"
    cr["titulo_nomes"] = tc["titulo_nomes"]
for par in resto:
    chave, _, valor = par.partition("=")
    cr[chave] = valor

if intro:
    videos = [(n, c) for n, c in enumerate(clips, 1) if c.get("t") == "video" and "intro_clara_tiago" in str(c.get("f") or "")]
    assert len(videos) == 1, ("esperava uma abertura", [(n, c.get("f")) for n, c in videos])
    n, c = videos[0]
    print("abertura: clip %d, %r -> %r" % (n, c.get("f"), intro))
    c["f"] = intro

b.pop("gravacao", None)
b.pop("cadeia", None)
json.dump(b, open(saida, "w", encoding="utf-8"), ensure_ascii=False)
print("clips traduzidos: %d de %d com texto | creditos: %s" % (len(feitos), len(com_texto), {k: cr.get(k) for k in ("titulo_nomes", "titulo", "data") if cr.get(k)}))
print("escrito:", saida)
