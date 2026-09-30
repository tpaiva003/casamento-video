# -*- coding: utf-8 -*-
"""Mede uma troca de musica como ela soa com tudo o que esta aprovado (097, 095 e 094, e o fim de frase
que se lhe passar). E a ferramenta para medir outra vez uma troca do ponto 3.3 (decisao 096), e
substitui o rascunho ponto3_3_mix33.py, que tinha os tempos de 29 de setembro escritos a mao: esta
encontra a troca pelos nomes das duas musicas. Nao muda nada.

    py -3.11 scripts/discussao/medir_troca.py <sai> <entra> <antes> <depois> <saida.wav> ['<mods>'] [--so A|B] [--sem-097]

<sai> e <entra> sao inicios dos nomes dos ficheiros (por exemplo "Lang Lang" "Mariah"). O excerto vai
de <antes> segundos antes do corte a <depois> segundos depois. <mods> e uma lista JSON:
    [{"quem": "sai", "sai_s": 13.5, "cauda": 0.95},      a que sai desce em sai_s (segundos DO FICHEIRO)
     {"quem": "entra", "subida": 0.5},                  a que entra sobe neste tempo
     {"quem": "entra", "in_s": 13.75}]                  outro ponto de entrada (para qualquer das duas)
--so A ou --so B deixa so a musica que sai, ou so a que entra, para medir cada uma sozinha.
Imprime o corte, onde esta cada musica no ficheiro, e o nivel (dBFS RMS de 200 ms) de 0,1 em 0,1 s.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
AQUI_CHAMADO = os.getcwd()
import comum as C      # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    so = sys.argv[sys.argv.index("--so") + 1] if "--so" in sys.argv else None
    if so:
        args.remove(so)
    if len(args) < 5:
        raise SystemExit(__doc__)
    sai, entra, antes, depois, saida = args[0], args[1], float(args[2]), float(args[3]), args[4]
    mods = json.loads(args[5]) if len(args) > 5 else []
    saida = os.path.join(AQUI_CHAMADO, saida)
    est = C.carregar()
    ent, t_cont = C.base_aprovada(est, com_097="--sem-097" not in sys.argv)
    a, b = C.troca(ent, sai, entra)
    for m in mods:
        e = a if m.get("quem") == "sai" else b
        if "in_s" in m:
            e["in_s"] = float(m["in_s"])
        if "sai_s" in m:
            C.acabar_na_frase(e, m["sai_s"], m.get("cauda", 0.8))
        if "subida" in m:
            e["subida"] = float(m["subida"])
    corte = b["quando"]
    print("corte aos %.2f s do corpo%s; a que sai (%s) esta aos %.2f s do ficheiro no corte, entrou aos %.2f; "
          "a que entra (%s) entra aos %.2f s do ficheiro, subida %s"
          % (corte, " (ja com a 097: o corpo andou %.2f s para tras)" % t_cont if t_cont else "",
             C.nome_da_musica(a["ficheiro"]), a["in_s"] + corte - a["quando"], a["in_s"],
             C.nome_da_musica(b["ficheiro"]), b["in_s"], b.get("subida")))
    if so == "A":
        ent = [a]
    elif so == "B":
        ent = [b]
    tmp = saida + ".m4a"
    C.excerto(C.CONSTRUIR_FUTURO, ent, corte, antes, depois, tmp)
    import subprocess
    subprocess.run([C.FF, "-v", "error", "-y", "-i", tmp, "-c:a", "pcm_s16le", saida], check=True)
    os.remove(tmp)
    for t, db in C.niveis(saida, 0.1, 0.2):
        print("%6.2f (corpo %7.2f) %6.1f dBFS %s" % (t, corte - antes + t, db, "#" * int(max(0, db + 50))))


if __name__ == "__main__":
    main()
