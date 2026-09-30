# RASCUNHO do ponto 3, guardado a 29 de setembro a partir da pasta temporaria da sessao. As funcoes
# de analise musical (decode, logmel, onset_env, batidas, novidade) que os agentes do 3.3 usaram.
# Importa-se; o main() so serve para refazer a analise de 28 de setembro e escreve na pasta
# saida/discussao/ponto3/analise. As batidas e as fronteiras de cada musica, ja calculadas, estao em
# data/discussao/musicas_batidas.json.
"""Auditoria das transicoes entre leitos da v3.

So le: data/montagens/v3.som.csv, os ficheiros de musica, e o som construido pelo
construir.py nesta pasta. Escreve so nesta pasta.

Para cada musica usada como leito calcula, no ficheiro original:
  - sonoridade momentanea (K-weighting BS.1770, 400 ms, passo 100 ms)
  - forca de onsets (fluxo espectral em mel) e batidas (tempo por autocorrelacao +
    programacao dinamica a la Ellis 2007)
  - novidade de Foote (auto-semelhanca de log-mel) -> fronteiras de seccao/frase
E no som misturado do corpo, a sonoridade momentanea a volta de cada transicao.
"""
import csv
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal

AQUI = os.path.join("C:/casamento-video", "saida", "discussao", "ponto3", "analise")
os.makedirs(AQUI, exist_ok=True)
FF = r"C:\Users\User 1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
SOM_CSV = r"C:\casamento-video\data\montagens\v3.som.csv"
CRUZ = 2.2
EFEITOS = ("rebobinar.wav",)
FOGUETES = "Candidato a vereador.mp3"


def decode(path, sr, ch, start=None, dur=None):
    cmd = [FF, "-hide_banner", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", "%.3f" % start]
    if dur is not None:
        cmd += ["-t", "%.3f" % dur]
    cmd += ["-i", path, "-vn", "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    return x.reshape(-1, ch) if ch > 1 else x


# ---------------------------------------------------------------- sonoridade
KB1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585])
KB2 = ([1.0, -2.0, 1.0], [1, -1.99004745483398, 0.99007225036621])


def momentanea(x48, passo=0.1, janela=0.4):
    """x48: (n, 2) a 48 kHz. Devolve (tempos do centro, LUFS momentaneo)."""
    y = signal.lfilter(KB1[0], KB1[1], x48, axis=0)
    y = signal.lfilter(KB2[0], KB2[1], y, axis=0)
    p = (y.astype(np.float64) ** 2).sum(axis=1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    w, h = int(janela * 48000), int(passo * 48000)
    ini = np.arange(0, len(p) - w, h)
    m = (c[ini + w] - c[ini]) / w
    lufs = -0.691 + 10 * np.log10(np.maximum(m, 1e-12))
    return (ini + w / 2) / 48000.0, lufs


# ---------------------------------------------------------------- espectro
SR = 22050
NFFT, HOP = 2048, 512
FPS_F = SR / HOP


def mel_fb(n_mels=64, fmin=40, fmax=10000):
    def hz2mel(f):
        return 2595 * np.log10(1 + f / 700.0)

    def mel2hz(m):
        return 700 * (10 ** (m / 2595.0) - 1)
    mels = np.linspace(hz2mel(fmin), hz2mel(fmax), n_mels + 2)
    hz = mel2hz(mels)
    freqs = np.linspace(0, SR / 2, NFFT // 2 + 1)
    fb = np.zeros((n_mels, len(freqs)), dtype=np.float32)
    for i in range(n_mels):
        l, c, r = hz[i], hz[i + 1], hz[i + 2]
        fb[i] = np.maximum(0, np.minimum((freqs - l) / (c - l), (r - freqs) / (r - c)))
    return fb


FB = mel_fb()


def logmel(x):
    n = 1 + (len(x) - NFFT) // HOP
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
    win = np.hanning(NFFT).astype(np.float32)
    S = np.abs(np.fft.rfft(x[idx] * win, axis=1)).astype(np.float32)
    M = S @ FB.T
    return np.log(1 + 100 * M)  # (frames, mels)


def onset_env(L):
    d = np.maximum(0, np.diff(L, axis=0)).sum(axis=1)
    d = np.concatenate([[0], d])
    # tirar a media local (1 s) e normalizar
    k = int(FPS_F)
    base = np.convolve(d, np.ones(k) / k, mode="same")
    o = np.maximum(0, d - base)
    return o / (o.std() + 1e-9)


def tempo(o):
    o = o - o.mean()
    ac = np.correlate(o, o, mode="full")[len(o) - 1:]
    lags = np.arange(len(ac))
    bpm = 60 * FPS_F / np.maximum(lags, 1)
    ok = (bpm >= 60) & (bpm <= 190)
    # preferencia suave por 120 BPM (log-gaussiana), como no Ellis
    peso = np.exp(-0.5 * (np.log2(bpm / 120.0) / 1.0) ** 2)
    sc = np.where(ok, ac * peso, -np.inf)
    lag = int(np.argmax(sc))
    return 60 * FPS_F / lag, lag


def batidas(o, periodo, alpha=100.0):
    n = len(o)
    score = o.copy().astype(np.float64)
    back = -np.ones(n, dtype=int)
    lo, hi = int(round(periodo / 2)), int(round(periodo * 2))
    for t in range(hi, n):
        prev = np.arange(t - hi, t - lo + 1)
        pen = -alpha * (np.log((t - prev) / periodo)) ** 2
        cand = score[prev] + pen
        j = int(np.argmax(cand))
        score[t] = o[t] + cand[j]
        back[t] = prev[j]
    # recuar a partir do melhor na ultima janela
    t = int(np.argmax(score[-hi:])) + n - hi
    bs = []
    while t >= 0:
        bs.append(t)
        t = back[t]
    return np.array(bs[::-1]) / FPS_F


def novidade(L, passo_s=0.25, meia_s=4.0):
    """Novidade de Foote sobre log-mel medio por blocos de passo_s."""
    k = max(1, int(round(passo_s * FPS_F)))
    n = len(L) // k
    F = L[:n * k].reshape(n, k, -1).mean(axis=1)
    F = F - F.mean(axis=0)
    F = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)
    S = F @ F.T
    m = int(round(meia_s / passo_s))
    g = np.arange(-m, m) + 0.5
    G = np.exp(-0.5 * (g / (m / 2.0)) ** 2)
    K = np.outer(G, G) * np.sign(np.outer(g, g))
    nov = np.zeros(n)
    Sp = np.pad(S, m, mode="constant")
    for i in range(n):
        nov[i] = (Sp[i:i + 2 * m, i:i + 2 * m] * K).sum()
    nov = np.maximum(nov, 0)
    nov = nov / (nov.max() + 1e-9)
    t = (np.arange(n) + 0.5) * passo_s
    picos, props = signal.find_peaks(nov, prominence=0.08, distance=int(2.0 / passo_s))
    return t, nov, [(float(t[p]), float(nov[p])) for p in picos]


def analisar_ficheiro(path):
    x48 = decode(path, 48000, 2)
    tm, lm = momentanea(x48)
    del x48
    x = decode(path, SR, 1)
    L = logmel(x)
    o = onset_env(L)
    bpm, lag = tempo(o)
    bs = batidas(o, lag)
    tn, nov, picos = novidade(L)
    tn8, nov8, picos8 = novidade(L, meia_s=8.0)
    ativo = lm[lm > -45]
    ref = float(np.percentile(ativo, 50)) if len(ativo) else -30.0
    return {"tm": tm, "lm": lm, "ref": ref, "bpm": bpm, "beats": bs, "onset": o,
            "picos4": picos, "picos8": picos8, "dur": len(x) / SR}


def nivel(a, t0, t1, fn=np.median):
    sel = (a["tm"] >= t0) & (a["tm"] < t1)
    if not sel.any():
        return float("nan")
    return float(fn(a["lm"][sel]))


def onset_em(a, t, raio=0.06):
    i0, i1 = int((t - raio) * FPS_F), int((t + raio) * FPS_F) + 1
    seg = a["onset"][max(0, i0):max(1, i1)]
    return float(seg.max()) if len(seg) else 0.0


def mais_perto(lista, t):
    if len(lista) == 0:
        return None
    arr = np.array(lista)
    j = int(np.argmin(np.abs(arr - t)))
    return float(arr[j])


def main():
    with open(SOM_CSV, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    for r in linhas:
        r["quando"], r["in"], r["dura"] = float(r["quando_s"]), float(r["in_s"]), float(r["dura_s"])
    leitos = [r for r in linhas if r["ficheiro"] not in EFEITOS]
    # a mesma conta do render: cruza se ha outra (nao efeito) a comecar a < 0,35 s do fim
    for r in leitos:
        fim = r["quando"] + r["dura"]
        r["cruza"] = any(x is not r and abs(x["quando"] - fim) < 0.35 for x in leitos)

    cache = {}
    for r in leitos:
        p = r["caminho"]
        if p not in cache:
            print("a analisar", r["ficheiro"][:50], flush=True)
            cache[p] = analisar_ficheiro(p)

    # o som misturado do corpo
    mix = decode(os.path.join(AQUI, "corpo_som.wav"), 48000, 2)
    mt, ml = momentanea(mix)
    MIX = {"tm": mt, "lm": ml}
    np.save(os.path.join(AQUI, "mix_momentanea.npy"), np.vstack([mt, ml]))

    ordenados = sorted(leitos, key=lambda r: r["quando"])
    trans = []
    for i, a in enumerate(ordenados):
        fim = a["quando"] + a["dura"]
        seg = [b for b in ordenados if b is not a and b["quando"] > a["quando"] and abs(b["quando"] - fim) < 1.2]
        for b in seg:
            trans.append((a, b))
    # a entrada do corpo: o som do video de abertura acaba e entra o primeiro leito
    out = []
    for a, b in trans:
        A, B = cache[a["caminho"]], cache[b["caminho"]]
        cA = a["in"] + a["dura"]                 # onde comeca a descer, no ficheiro de A
        desc = CRUZ if a["cruza"] else 1.0
        fimA = cA + desc                         # onde fica a zero
        iB = b["in"]
        T = b["quando"]
        # A: o que se ouve antes do corte, durante a descida, e o que vinha depois
        A_antes = nivel(A, cA - 3, cA) - A["ref"]
        A_desc = nivel(A, cA, fimA) - A["ref"]
        A_depois = nivel(A, fimA, fimA + 3) - A["ref"]
        A_maxantes = nivel(A, cA - 1, cA, np.max) - A["ref"]
        # B: o que vinha antes do in (se a musica ja estava a tocar alto, entra a meio)
        B_antes = nivel(B, iB - 2, iB) - B["ref"] if iB > 0.5 else float("nan")
        B_prim = nivel(B, iB, iB + 3) - B["ref"]
        B_1s = nivel(B, iB, iB + 1.0) - B["ref"]
        # primeiro instante depois do in com som (> ref - 20)
        sel = (B["tm"] >= iB) & (B["lm"] > B["ref"] - 20)
        B_som = float(B["tm"][sel][0] - iB) if sel.any() else float("nan")
        # batidas e fronteiras
        bA, bB = mais_perto(B["beats"], iB), mais_perto(A["beats"], cA)
        fA4 = [p for p in A["picos4"] if cA - 12 <= p[0] <= fimA + 6]
        fB4 = [p for p in B["picos4"] if iB - 10 <= p[0] <= iB + 12]
        fA8 = [p for p in A["picos8"] if cA - 15 <= p[0] <= fimA + 8]
        fB8 = [p for p in B["picos8"] if iB - 12 <= p[0] <= iB + 15]
        # mistura: a volta de T (relogio do corpo)
        pre = nivel(MIX, T - 7, T - 2.5)
        pos = nivel(MIX, T + 3.5, T + 9)
        vale = nivel(MIX, T - 1.0, T + 3.0, np.min)
        pico = nivel(MIX, T - 0.5, T + desc + 0.5, np.max)
        # procurar um in de B melhor: fronteira de seccao com batida e som logo a seguir
        out.append({
            "T_corpo": T, "T_filme": T + 35.24,
            "sai": a["ficheiro"], "entra": b["ficheiro"],
            "A_in": a["in"], "A_corte": cA, "A_zero": fimA, "A_dur_fich": A["dur"], "desc": desc,
            "A_antes_dB": A_antes, "A_desc_dB": A_desc, "A_depois_dB": A_depois, "A_max1s_dB": A_maxantes,
            "B_in": iB, "B_antes_dB": B_antes, "B_prim3_dB": B_prim, "B_prim1_dB": B_1s, "B_som_apos_s": B_som,
            "B_onset_no_in": onset_em(B, iB), "B_batida_mais_perto": bA, "A_batida_mais_perto": bB,
            "A_bpm": A["bpm"], "B_bpm": B["bpm"],
            "A_fronteiras4": fA4, "B_fronteiras4": fB4, "A_fronteiras8": fA8, "B_fronteiras8": fB8,
            "mix_pre": pre, "mix_pos": pos, "mix_vale": vale, "mix_pico": pico,
            "A_ref": A["ref"], "B_ref": B["ref"],
        })

    with open(os.path.join(AQUI, "transicoes.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    # guardar as analises por ficheiro, para propostas
    resumo = {}
    for p, a in cache.items():
        resumo[os.path.basename(p)] = {"ref": a["ref"], "bpm": a["bpm"], "dur": a["dur"],
                                       "picos4": a["picos4"], "picos8": a["picos8"],
                                       "beats": [round(float(b), 3) for b in a["beats"]]}
        np.save(os.path.join(AQUI, "lm_%s.npy" % os.path.basename(p)[:20].replace(" ", "_")),
                np.vstack([a["tm"], a["lm"]]))
    with open(os.path.join(AQUI, "ficheiros.json"), "w", encoding="utf-8") as fh:
        json.dump(resumo, fh, ensure_ascii=False, indent=1)

    for t in out:
        print("\n== %6.2f s (filme %6.2f)  %s  ->  %s" % (t["T_corpo"], t["T_filme"], t["sai"][:30], t["entra"][:30]))
        print("   sai:   corte %.2f (zero %.2f) de %.1f; antes %+.1f  desc %+.1f  depois %+.1f dB (ref %.1f) bpm %.0f"
              % (t["A_corte"], t["A_zero"], t["A_dur_fich"], t["A_antes_dB"], t["A_desc_dB"], t["A_depois_dB"], t["A_ref"], t["A_bpm"]))
        print("          fronteiras4 %s" % ["%.2f(%.2f)" % p for p in t["A_fronteiras4"]])
        print("          fronteiras8 %s" % ["%.2f(%.2f)" % p for p in t["A_fronteiras8"]])
        print("   entra: in %.2f; antes %+.1f  1s %+.1f  3s %+.1f dB; som apos %.2f s; onset %.2f; batida %.2f bpm %.0f"
              % (t["B_in"], t["B_antes_dB"], t["B_prim1_dB"], t["B_prim3_dB"], t["B_som_apos_s"], t["B_onset_no_in"],
                 t["B_batida_mais_perto"] or -1, t["B_bpm"]))
        print("          fronteiras4 %s" % ["%.2f(%.2f)" % p for p in t["B_fronteiras4"]])
        print("          fronteiras8 %s" % ["%.2f(%.2f)" % p for p in t["B_fronteiras8"]])
        print("   mistura: pre %.1f  pos %.1f  vale %.1f  pico %.1f LUFS" % (t["mix_pre"], t["mix_pos"], t["mix_vale"], t["mix_pico"]))


if __name__ == "__main__":
    main()
