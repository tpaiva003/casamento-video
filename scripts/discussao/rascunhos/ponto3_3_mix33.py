# RASCUNHO do ponto 3.3, guardado a 29 de setembro a partir da pasta temporaria da sessao. Foi a
# ferramenta com que os agentes mediram as trocas (data/discussao/ponto3_3_analise.json). Os tempos
# de corpo e as entradas da 095 estao escritos a mao para a montagem de 29/09 (rev 903): noutra
# montagem, usar o scripts/discussao/comum.py, que procura pelo nome.
# -*- coding: utf-8 -*-
"""Ponto 3.3: faz o som de um troco do corpo da v3 como ficaria com as decisoes 094 e 095 ja
construidas, mais as mudancas que se quiserem experimentar, e mede-o. Fora do repositorio: o
render.py nao e tocado, a mudanca faz-se em memoria.

Uso em Python:
    import mix33
    mix33.excerto(mods, centro, antes, depois, saida)      # escreve saida (.wav ou .m4a)
    mix33.niveis(saida, passo=0.1)                           # lista (t, dBFS RMS 400 ms)

mods: lista de dicts, cada um escolhe uma faixa pelo inicio do nome e pelo quando de hoje:
    {"ficheiro": "Gilbert", "quando": 246.42,        # qual (quando no corpo, +-0.3 s)
     "in_s": 5.2,          # opcional: outro ponto de entrada no ficheiro
     "sai_s": 28.4,        # opcional: instante DO FICHEIRO onde a frase acaba; a faixa comeca a
                           #   descer ai e acaba "cauda" segundos depois (em vez de descer no corte)
     "cauda": 0.8,         # opcional, com sai_s: duracao da descida (omissao 0.8 s)
     "novo_quando": 272.0, # opcional: a faixa passa a comecar noutro instante do corpo
     "subida": 0.03}       # opcional: rampa de entrada (0.03 = sem rampa)
A 094 (curva qsin, sem rampa num inicio, rampa de 2,2 s a meio) e a 095 (pontos de entrada, e as
quatro entradas num ataque sem rampa) ja estao aplicadas antes das mods.
Linha de comando: py -3.11 mix33.py <centro> <antes> <depois> <saida> ['<json das mods>']
"""
import inspect, json, os, subprocess, sys, textwrap
AQUI_CHAMADO = os.getcwd()      # os caminhos relativos contam a partir daqui, nao do repositorio
import numpy as np
sys.path.insert(0, r"C:\casamento-video\scripts")
os.chdir(r"C:\casamento-video")
import render

FF = render.ffmpeg()
IN_095 = [(473.82, "Inês Homem de Melo", 2.7, True), (499.62, "Já Sei Namorar", 34.9, True),
          (37.87, "Lang Lang", 14.6, False), (344.32, "Tiago Celebration", 0.81, True),
          (712.52, "Bachman", 60.8, False), (573.22, "Steppenwolf", 0.55, True),
          (613.72, "Filhos Do", 7.0, False)]

_fonte = textwrap.dedent(inspect.getsource(render.construir_som))
for _v, _n in (
        ('subida = VOZ_FADE if voz else (1.0 if e["quando"] > 0.05 else 0.4)',
         'subida = e.get("subida") or (VOZ_FADE if voz else (1.0 if e["quando"] > 0.05 else 0.4))'),
        ('descida = VOZ_FADE if voz else max(1.0, e.get("cruza", 0.0))',
         'descida = e.get("descida") or (VOZ_FADE if voz else max(1.0, e.get("cruza", 0.0)))'),
        ('"afade=t=in:st=0:d=%.2f,afade=t=out:st=%.3f:d=%.2f,"',
         '"afade=t=in:st=0:d=%.2f:curve=%s,afade=t=out:st=%.3f:d=%.2f:curve=%s,"'),
        ('% (i, norma, subida, max(0.0, e["dura"] - descida), descida,',
         '% (i, norma, subida, e.get("curva", "tri"), max(0.0, e["dura"] - descida), descida, e.get("curva", "tri"),')):
    assert _fonte.count(_v) == 1, _v
    _fonte = _fonte.replace(_v, _n)
_ns = dict(render.__dict__)
exec(compile(_fonte, render.__file__, "exec"), _ns)
CONSTRUIR = _ns["construir_som"]

_EST = render.carregar_montagem("v3", None)


def nivel_ficheiro(caminho, a, b):
    if b <= a:
        return None
    r = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % max(0, a), "-t", "%.3f" % (b - max(0, a)),
                        "-i", caminho, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0
    return 20 * np.log10(max(1e-6, float(np.sqrt(np.mean(x * x))))) if len(x) else None


def entra_num_inicio(e):
    if e["in_s"] < 0.05:
        return True
    a = nivel_ficheiro(e["caminho"], e["in_s"] - 0.4, e["in_s"])
    d = nivel_ficheiro(e["caminho"], e["in_s"], e["in_s"] + 0.4)
    return a is not None and d is not None and a < -40 and d - a > 15


def base():
    """As entradas do corpo com a 095 e a 094 aplicadas."""
    ent = render.som_do_ficheiro("v3", _EST["fim"])
    ataque = []
    for t, pref, novo, atq in IN_095:
        alvo = [e for e in ent if abs(e["quando"] - t) < 0.2 and e["ficheiro"].startswith(pref)]
        assert len(alvo) == 1, pref
        alvo[0]["in_s"] = novo
        if atq:
            ataque.append(alvo[0])
    leitos = sorted([e for e in ent if not render.entra_depressa(e)], key=lambda e: e["quando"])
    for e in leitos:
        if e["ficheiro"].startswith(("Candidato", "rebobinar")):
            continue
        e["curva"] = "qsin"
        anterior = [x for x in leitos if x is not e and x.get("cruza")
                    and abs((x["quando"] + x["dura"] - x["cruza"]) - e["quando"]) < 0.35]
        if e in ataque or entra_num_inicio(e):
            e["subida"] = 0.03
        elif anterior:
            e["subida"] = anterior[0]["cruza"]
    return ent


def aplicar(ent, mods):
    for m in mods or []:
        alvo = [e for e in ent if abs(e["quando"] - m["quando"]) < 0.3 and e["ficheiro"].startswith(m["ficheiro"])]
        assert len(alvo) == 1, ("mod sem faixa unica", m, [(e["ficheiro"][:20], e["quando"]) for e in ent
                                                           if abs(e["quando"] - m["quando"]) < 3])
        e = alvo[0]
        if "in_s" in m:
            e["in_s"] = float(m["in_s"])
        if "novo_quando" in m:
            fim = e["quando"] + e["dura"]
            e["quando"] = float(m["novo_quando"])
            e["dura"] = max(0.5, fim - e["quando"])
        if "sai_s" in m:
            cauda = float(m.get("cauda", 0.8))
            e["dura"] = max(0.5, float(m["sai_s"]) - e["in_s"] + cauda)
            e["descida"] = cauda
            e["cruza"] = 0.0
        if "subida" in m:
            e["subida"] = float(m["subida"])
    return ent


def excerto(mods, centro, antes, depois, saida):
    saida = os.path.join(AQUI_CHAMADO, saida)
    ent = aplicar(base(), mods)
    a, b = centro - antes, centro + depois
    janela = [dict(e) for e in ent if e["quando"] < b + 1 and e["quando"] + e["dura"] > a - 1]
    tmp = saida + ".todo.m4a"
    if not CONSTRUIR(FF, janela, b + 1, tmp, 0.0):
        raise RuntimeError("o som nao se fez")
    ext = os.path.splitext(saida)[1].lower()
    cod = ["-c:a", "aac", "-b:a", "192k"] if ext == ".m4a" else ["-c:a", "pcm_s16le"]
    subprocess.run([FF, "-v", "error", "-y", "-ss", "%.3f" % a, "-t", "%.3f" % (b - a), "-i", tmp] + cod + [saida],
                   check=True)
    os.remove(tmp)
    return saida


def niveis(caminho, passo=0.1, janela=0.4):
    caminho = os.path.join(AQUI_CHAMADO, caminho)
    r = subprocess.run([FF, "-v", "error", "-i", caminho, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True)
    x = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0
    n, h = int(janela * 16000), int(passo * 16000)
    out = []
    for i in range(0, max(1, len(x) - n), h):
        s = x[i:i + n]
        out.append((round(i / 16000 + janela / 2, 2), round(20 * np.log10(max(1e-6, float(np.sqrt(np.mean(s * s))))), 1)))
    return out


if __name__ == "__main__":
    centro, antes, depois, saida = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    mods = json.loads(sys.argv[5]) if len(sys.argv) > 5 else []
    excerto(mods, centro, antes, depois, saida)
    for t, db in niveis(saida, 0.2):
        print("%6.2f (corpo %7.2f) %6.1f dBFS %s" % (t, centro - antes + t, db, "#" * int(max(0, db + 50))))
