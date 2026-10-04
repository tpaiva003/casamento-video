# -*- coding: utf-8 -*-
"""Tira o buraco de som que a colagem dos creditos deixa aos 700,3 s, sem costura nenhuma.

O QUE A COLAGEM FEZ (medido): ate ao buraco o som da entrega e o do filme, amostra a amostra; no buraco
ha 52 ms de zeros (mais uns ms quase a zero de cada lado); depois dele o som continua, mas 32,2 ms
atrasado (1548 amostras) e com 20 ms do filme a menos. O remendo: o som do filme no lugar do buraco,
e tudo o que vem depois anda 1548 amostras para a frente, que e onde devia estar. Fica continuo dos
dois lados, e a musica dos creditos volta ao instante certo da imagem. No fim sobram 32 ms de silencio.

A imagem nao se toca (copia do fluxo de video). Sai um ficheiro NOVO.

Uso: py -3.11 scripts/remendar_som_creditos.py <entrega.mp4> <filme_sem_creditos.mp4> <saida.mp4>
"""
import os
import subprocess
import sys
import wave

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\casamento-video\scripts")
import render  # noqa: E402

entrega, filme, saida = sys.argv[1], sys.argv[2], sys.argv[3]
assert not os.path.exists(saida), "ja existe: %s" % saida
ff = render.ffmpeg()
pasta = os.path.join(r"C:\casamento-video\saida\discussao\final_1004", "remendo")
os.makedirs(pasta, exist_ok=True)
SR = 48000


def para_wav(origem, destino):
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", origem, "-vn",
                        "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2", destino], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-300:]


def ler(caminho):
    with wave.open(caminho, "rb") as w:
        assert w.getframerate() == SR and w.getnchannels() == 2 and w.getsampwidth() == 2
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).astype(np.float64)


wm, wf = os.path.join(pasta, "entrega.wav"), os.path.join(pasta, "filme.wav")
para_wav(entrega, wm)
para_wav(filme, wf)
m, f = ler(wm), ler(wf)

# 1. o buraco: a corrida de zeros mais comprida entre os 698 e os 703 s
a, b = int(698 * SR), int(703 * SR)
nulo = (np.abs(m[a:b]).max(axis=1) == 0)
melhor, ini = (0, 0), None
for k, z in enumerate(nulo):
    if z and ini is None:
        ini = k
    if not z and ini is not None:
        if k - ini > melhor[0]:
            melhor = (k - ini, ini)
        ini = None
tam, ini = melhor
g0, g1 = a + ini, a + ini + tam
print("buraco: %.4f a %.4f s (%.1f ms de zeros)" % (g0 / SR, g1 / SR, 1000.0 * tam / SR))
assert 0.02 * SR < tam < 0.2 * SR


def desvio(c0, c1, alcance=2400):
    x = m[c0:c1].mean(axis=1)
    melhor_d, melhor_c = 0, -2.0
    for d in range(-alcance, alcance + 1):
        c = float(np.corrcoef(x, f[c0 + d:c1 + d].mean(axis=1))[0, 1])
        if c > melhor_c:
            melhor_d, melhor_c = d, c
    return melhor_d, melhor_c


d_antes, c_antes = desvio(g0 - int(0.6 * SR), g0 - int(0.03 * SR))
d_depois, c_depois = desvio(g1 + int(0.03 * SR), g1 + int(0.6 * SR))
print("antes: desvio %d, correlacao %.4f | depois: desvio %d (%.1f ms), correlacao %.4f"
      % (d_antes, c_antes, d_depois, 1000.0 * d_depois / SR, c_depois))
assert d_antes == 0 and c_antes > 0.999, "antes do buraco o som da entrega tem de ser o do filme"
assert d_depois < 0 and c_depois > 0.99, "depois do buraco esperava o som do filme, atrasado"
atraso = -d_depois                                   # amostras que o som de depois esta atrasado

# 2. as costuras: 10 ms antes do buraco (onde a entrega ainda e o filme, amostra a amostra) e 20 ms
#    depois dele (para la do arranque do segundo troco). Entre as duas vai o som do filme.
e0 = g0 - int(0.010 * SR)
e1 = g1 + int(0.020 * SR)
meio = f[e0:e1 - atraso]                              # o filme de e0 ate ao instante que a entrega toca em e1
P = int(0.004 * SR)                                   # 4 ms de passagem em cada costura
sobe = np.linspace(0.0, 1.0, P)[:, None]
cauda = m[e1:].copy()
novo = np.concatenate([m[:e0], meio, cauda, np.zeros((atraso, 2))])
assert len(novo) == len(m)
# costura 1 (antes): a entrega e o filme sao iguais aqui, a passagem e so por cautela
novo[e0 - P:e0] = m[e0 - P:e0] * (1 - sobe) + f[e0 - P:e0] * sobe
# costura 2 (depois): do filme para o som da entrega, que e o mesmo filme recodificado
c2 = e0 + len(meio)
novo[c2:c2 + P] = f[e1 - atraso:e1 - atraso + P] * (1 - sobe) + m[e1:e1 + P] * sobe

# 3. conferir
jan = int(0.005 * SR)


def niveis(x, c0, c1):
    return np.array([20 * np.log10(max(1e-9, np.sqrt((x[k:k + jan] ** 2).mean()) / 32768.0)) for k in range(c0, c1, jan)])


zona = (g0 - int(0.3 * SR), g1 + int(0.3 * SR))
era, fica, ref = niveis(m, *zona), niveis(novo, *zona), niveis(f, *zona)
print("nivel em janelas de 5 ms, 0,3 s para cada lado: era minimo %.1f dB; fica minimo %.1f, mediana %.1f; "
      "o filme sem creditos no mesmo sitio: minimo %.1f, mediana %.1f"
      % (era.min(), fica.min(), float(np.median(fica)), ref.min(), float(np.median(ref))))
x = novo[zona[0]:c2].mean(axis=1)
y = f[zona[0]:c2].mean(axis=1)
print("ate a segunda costura o som e o do filme: correlacao %.5f, diferenca maxima %.1f em 32768"
      % (float(np.corrcoef(x, y)[0, 1]), float(np.abs(x - y).max())))
x2 = novo[c2 + P:c2 + P + int(0.5 * SR)].mean(axis=1)
y2 = f[c2 + P:c2 + P + int(0.5 * SR)].mean(axis=1)
print("depois da segunda costura continua a ser o filme, sem desvio: correlacao %.5f" % float(np.corrcoef(x2, y2)[0, 1]))
print("maior salto entre amostras nas costuras: %.4f e %.4f (na musica a volta: %.4f)"
      % (np.abs(np.diff(novo[e0 - P:e0 + P].mean(axis=1))).max() / 32768.0,
         np.abs(np.diff(novo[c2 - P:c2 + 2 * P].mean(axis=1))).max() / 32768.0,
         np.abs(np.diff(m[g0 - SR:g0].mean(axis=1))).max() / 32768.0))
print("antes da primeira costura igual amostra a amostra:", bool(np.array_equal(novo[:e0 - P], m[:e0 - P])))
print("depois da segunda costura igual ao som da entrega, %d amostras (%.1f ms) mais cedo:" % (atraso, 1000.0 * atraso / SR),
      bool(np.array_equal(novo[c2 + P:len(m) - atraso], m[e1 + P:])))
print("os ultimos 0,5 s da entrega eram silencio (pico %.0f em 32768)" % float(np.abs(m[-int(0.5 * SR):]).max()))

wn = os.path.join(pasta, "entrega_remendada2.wav")
with wave.open(wn, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(np.clip(np.round(novo), -32768, 32767).astype(np.int16).tobytes())
r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-i", entrega, "-i", wn,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ac", "2", "-ar", str(SR), "-movflags", "+faststart", saida], capture_output=True, text=True)
assert r.returncode == 0, r.stderr[-400:]
print("escrito:", saida, "%.1f MB" % (os.path.getsize(saida) / 1048576.0))
for x in (wm, wf):
    os.remove(x)
