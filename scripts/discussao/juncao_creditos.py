# -*- coding: utf-8 -*-
"""A passagem da ultima musica do filme para a dos creditos: onde cai, o que se ouve, e copias para ouvir.

    py -3.11 scripts/discussao/juncao_creditos.py
    py -3.11 scripts/discussao/juncao_creditos.py --ouvir [--a <sai_s>,<cauda>] [--b <sai_s>,<cauda>]
                                                 [--saida <pasta>] [--creditos <s>] [--estado <estado2.json>]

Nao muda nada: nao escreve no data/fins_de_frase.csv, nem na base, nem na montagem. As copias e as
medidas vao para saida/discussao/juncao_creditos/ (ou para a --saida).

PORQUE EXISTE (2 de outubro, a noite). O Tiago escolheu o Taking Care of Business para os creditos, com
"fim". A passagem e uma troca de musica como as de dentro do filme (musica_creditos.faixas_dos_creditos),
e por isso cai na decisao 096: a musica que sai deve acabar no fim de uma frase, e um agente analisa e
outro verifica. Mas o sitio dela no ficheiro da que sai e o fim do filme menos o render.FADE_FIM_IMAGEM,
e muda com cada foto, cada duracao e cada clip que ele mexa no fim do filme. Este script mede-o outra vez
depressa, a partir da montagem que o ponto5 vai usar (data/montagens/v3, a do ultimo montar_da_mesa.py) e
da leitura mais recente da base (a escolha da musica e a duracao dos creditos):

1. ONDE CAI: o segundo do corpo em que os creditos comecam, a ultima musica e o segundo do ficheiro dela
   nesse instante, e a entrada da dos creditos (musica_creditos.entrada);
2. O QUE HA NA QUE SAI a volta do corte, de 3 s antes a 4,5 s depois: a mistura (RMS de 100 ms) e a voz ao
   centro (|M| - |S| entre 1 e 4 kHz, o metodo do verificador da t713), e as PAUSAS dessa voz, 9 dB abaixo
   do nivel das linhas durante 0,25 s ou mais. Cada pausa da um fim de linha candidato (o inicio dela), o
   primeiro sinal que volta (uma batida, uma anacruse) e a linha nova (a voz outra vez a 5 dB do nivel).
   Sao CANDIDATOS: a 096 pede que um agente analise e outro verifique antes de alguma linha entrar no
   data/fins_de_frase.csv;
3. AS DUAS SAIDAS, para as copias:
   (A) no corte: a que sai acaba no corte (sai_s no segundo do corte, ou no inicio da pausa em que ele
       caia) e cala-se na cauda, e a dos creditos entra no corte e sobe no tempo da cauda (096). E uma
       linha do data/fins_de_frase.csv com no_corte = o segundo do corte, e o render ja a faz;
   (B) no fim da frase: a que sai acaba a linha por cima dos creditos e a dos creditos entra quando ela
       acaba, ate 3 s depois (ponto5_creditos.PASSAGENS, est.creditos.musica.passagem = "frase"). E uma
       linha com no_corte = o fim da frase, e a entrada da dos creditos encurtados dessa espera;
4. com --ouvir, as copias de 20 s (os ultimos 8 s do filme e 12 s dos creditos, so som, AAC a 48 kHz num
   .mp4), feitas pelo ponto5_creditos.som_dos_creditos() e pelo render.construir_som(), como no --master,
   com o data/fins_de_frase.csv trocado em memoria por uma copia com a linha de cada saida: «hoje» (como o
   render faria agora, e como a Mesa toca no «Ouvir a entrada»), A e B. A que sai fica ao nivel a que o
   filme a toca nesses segundos (o exemplo do ponto5 mede o loudnorm dela so no troco curto, e o acerto
   diz-se); a dos creditos fica como o render a faz. E as medidas de cada uma, de 1 s antes a 2,5 s depois
   da troca: o vale da mistura, a maior queda em 200 ms, o tempo com duas vozes (as duas acima de -45 dB e
   a menos de 12 dB uma da outra, na voz ao centro de cada haste) e a voz da que sai depois da troca.

--a e --b dao a saida a mao (segundos do ficheiro da que sai, e cauda); sem eles, as das pausas, que sao
so candidatos (nao sabem, por exemplo, que a batida que fecha uma frase lhe pertence). --variantes hoje,A,B
escolhe as copias. --alongar <s> faz as contas com o fim do filme <s> segundos mais comprido e a ultima
musica a continuar: e a terceira saida, (C), acertar a imagem a musica para o corte cair num fim de frase
(o fim e dele, na Mesa; isto so mostra como soaria). --montagens <pasta> le a montagem de outra pasta (o
DISCUSSAO_MONTAGENS do comum), por exemplo uma leitura nova montada fora do data/montagens.
"""
import contextlib
import csv
import io
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

if "--montagens" in sys.argv:                  # antes do comum, que le a montagem por aqui
    os.environ["DISCUSSAO_MONTAGENS"] = sys.argv[sys.argv.index("--montagens") + 1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C                     # noqa: E402
from comum import render              # noqa: E402
import ponto5_creditos as p5          # noqa: E402
import musica_creditos as mc          # noqa: E402

SR = 44100
ANTES, DEPOIS = 8.0, 12.0             # as copias: os ultimos 8 s do filme e 12 s dos creditos
PAUSA_DB = 9.0                        # uma pausa da voz: 9 dB abaixo do nivel das linhas...
PAUSA_MIN_S = 0.25                    # ...durante 0,25 s ou mais (uma folga de silaba tem 0,1 a 0,15 s)
LINHA_DB = 5.0                        # e a linha nova volta a menos disto do nivel delas
CAUDA_MAX_A, CAUDA_MAX_B = 0.3, 0.5   # as caudas da 096 vao de 0,12 a 1 s; aqui curtas, antes da linha nova
FADE_LIVRE = render.FADE_FIM_SOM - render.FADE_FIM_IMAGEM + 0.1   # o nivel compara-se antes do fade do filme
COLUNAS_FINS = ["sai", "entra", "no_corte", "entra_in", "sai_s", "cauda", "subida_entra", "confianca", "id"]


def _arg(nome, omissao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else omissao


# --------------------------------------------------------------------------------- onde cai
def duracao_dos_creditos(leitura):
    """A duracao dos creditos pelas contas do ponto5 (o rolo de nomes, a coluna de fotos e os cargos)."""
    if _arg("--creditos"):
        return float(_arg("--creditos").replace(",", "."))
    with contextlib.redirect_stdout(io.StringIO()):
        textos = p5.textos_dos_creditos(leitura[0], [])
        blocos, _fora = p5.por_grupo(p5.ler_convidados(p5.folha_mais_recente()), textos["grupos"])
        fotos, _fonte = p5.fotos_marcadas(leitura)
        rolo, coluna = p5.rolo_de_nomes(blocos), p5.coluna_de_fotos(fotos)
    return p5.tempos_dos_creditos(rolo.height, coluna.height, len(textos["cargos"]))["dur"]


def situacao():
    """Onde cai a passagem: um dicionario com a montagem, a ultima musica, o corte e a escolha."""
    with contextlib.redirect_stdout(io.StringIO()):
        est = C.carregar()
        ent = C.entradas_de_som(est)
    ultima = C.leitos(ent)[-1]
    # --alongar X: o fim do filme X segundos mais comprido, com a ultima musica a continuar (a terceira saida:
    # acertar a imagem a musica, para o corte cair num fim de frase). So para as contas e as copias.
    mais = float(str(_arg("--alongar", "0")).replace(",", "."))
    if mais:
        est = dict(est, fim=est["fim"] + mais)
        ultima = dict(ultima, dura=ultima["dura"] + mais,
                      dura_medida=(ultima.get("dura_medida") or ultima["dura"]) + mais)
    corte_t = est["fim"] - render.FADE_FIM_IMAGEM
    no_corte = round(ultima["in_s"] + corte_t - ultima["quando"], 3)
    leitura = p5.leitura_da_mesa()
    escolha = p5.escolha_da_musica(leitura[0])
    esc, erro = mc.escolha_valida(escolha)
    s = {"est": est, "ent": ent, "ultima": ultima, "corte_t": corte_t, "no_corte": no_corte, "leitura": leitura,
         "mais": mais,
         "escolha": escolha, "esc": esc, "erro": erro, "dur": duracao_dos_creditos(leitura)}
    if esc:
        real, caminho = mc.resolver(esc["ficheiro"])
        s["real"], s["caminho"] = real, caminho
        if real:
            s["medidas"] = mc.medir(caminho)
            inicio = esc["inicio"]
            if not isinstance(inicio, str) and inicio >= s["medidas"]["fim"]:
                inicio = "fim"
            s["inicio"] = inicio
            s["entrada"] = mc.entrada(inicio, s["medidas"]["fim"], s["dur"], s["medidas"]["silencios"])
    return s


# --------------------------------------------------------------------------------- as medidas
def ler(caminho, de, ate):
    r = subprocess.run([C.FF, "-v", "error", "-ss", "%.3f" % max(0.0, de), "-t", "%.3f" % (ate - max(0.0, de)),
                        "-i", caminho, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def envelope(x, de, passo=0.01):
    """(t, total, voz) em tramas de 10 ms: o RMS de 100 ms da mistura e a voz ao centro (|M| - |S|, 1 a
    4 kHz, janela de 46 ms), em dB."""
    n, h = 2048, int(round(passo * SR))
    if len(x) < n + h:
        return np.zeros(0), np.zeros(0), np.zeros(0)
    M, S = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    idx = np.arange(0, len(M) - n, h)
    w = np.hanning(n)
    fr = np.fft.rfftfreq(n, 1.0 / SR)
    banda = (fr >= 1000) & (fr <= 4000)
    FM = np.abs(np.fft.rfft(np.stack([M[i:i + n] for i in idx]) * w, axis=1))[:, banda]
    FS = np.abs(np.fft.rfft(np.stack([S[i:i + n] for i in idx]) * w, axis=1))[:, banda]
    voz = 20 * np.log10(np.maximum(np.sqrt(np.sum(np.maximum(FM - FS, 0) ** 2, axis=1)) / (n / 4), 1e-9))
    q = (x ** 2).mean(axis=1)
    c = np.concatenate([[0.0], np.cumsum(q)])
    meio, k = idx + n // 2, int(0.05 * SR)
    a, b = np.clip(meio - k, 0, len(q)), np.clip(meio + k, 0, len(q))
    total = 10 * np.log10(np.maximum((c[b] - c[a]) / np.maximum(b - a, 1), 1e-18))
    return de + meio / SR, total, voz


def pausas(t, voz, de, ate):
    """([(inicio, primeiro_sinal, linha_nova, fundo)], nivel): as pausas da voz entre de e ate.

    O nivel das linhas e o percentil 80 da voz na janela. Uma pausa comeca quando a voz cai PAUSA_DB abaixo
    dele e dura PAUSA_MIN_S ou mais; o primeiro_sinal e o primeiro instante em que volta a passar desse
    limiar (uma batida, um acorde, uma anacruse), e a linha_nova o primeiro em que volta a menos de LINHA_DB
    do nivel. Duas pausas separadas por um sinal que nao chega a linha contam como uma so."""
    j = (t >= de) & (t <= ate)
    if not j.any():
        return [], None
    v = np.convolve(voz, np.ones(5) / 5, mode="same")
    nivel = np.percentile(v[j], 80)
    baixo = (v < nivel - PAUSA_DB) & j
    corridas, ini = [], None
    for i in range(len(t)):
        if baixo[i] and ini is None:
            ini = i
        elif not baixo[i] and ini is not None:
            corridas.append([ini, i - 1])
            ini = None
    if ini is not None:
        corridas.append([ini, len(t) - 1])
    # cada pausa: [inicio, fim da primeira corrida, fim da ultima corrida juntada]
    juntas = []
    for a, b in corridas:
        if juntas and (t[a] - t[juntas[-1][2]] < 0.06 or v[juntas[-1][2] + 1:a].max() < nivel - LINHA_DB):
            juntas[-1][2] = b
        else:
            juntas.append([a, b, b])
    fora = []
    for a, b1, b in juntas:
        if t[b1] - t[a] < PAUSA_MIN_S and t[b] - t[a] < PAUSA_MIN_S:
            continue
        fora.append((round(float(t[a]), 2), round(float(t[min(b1 + 1, len(t) - 1)]), 2),
                     round(float(t[min(b + 1, len(t) - 1)]), 2), round(float(v[a:b + 1].min() - nivel), 1)))
    return fora, round(float(nivel), 1)


def propostas(no_corte, lista):
    """As saidas A e B a partir das pausas: {"A": (sai_s, cauda), "B": (sai_s, cauda)} e o que se diz delas.
    A cauda acaba antes do primeiro sinal depois da pausa, e e no maximo CAUDA_MAX_A ou CAUDA_MAX_B."""
    fora, dizer = {}, []
    dentro = [p for p in lista if p[0] - 0.05 <= no_corte <= p[2]]
    if dentro:
        p = dentro[0]
        sinal = p[1] if no_corte < p[1] else p[2]
        cauda = round(max(0.1, min(CAUDA_MAX_A, sinal - no_corte - 0.05)), 2)
        fora["A"] = (round(no_corte, 2), cauda)
        dizer.append("A: o corte cai numa pausa (%.2f a %.2f): acaba no corte e cala-se em %.2f s, antes do sinal "
                     "seguinte aos %.2f (a linha nova aos %.2f)" % (p[0], p[2], cauda, sinal, p[2]))
    else:
        antes = [p for p in lista if p[2] < no_corte]
        fora["A"] = (round(no_corte, 2), 0.2)
        dizer.append("A: o corte cai A MEIO DE UMA LINHA (%s): acabar no corte e cortar a linha"
                     % ("a ultima pausa antes dele vai de %.2f a %.2f, %.2f s antes" % (antes[-1][0], antes[-1][2],
                                                                                  no_corte - antes[-1][2])
                        if antes else "nenhuma pausa da voz nos 3 s antes dele"))
    depois = [p for p in lista if no_corte + 0.3 < p[0] <= no_corte + render.TOLERANCIA_FIM_DE_FRASE]
    if depois:
        p = depois[0]
        cauda = round(max(0.1, min(CAUDA_MAX_B, p[1] - p[0] - 0.05)), 2)
        fora["B"] = (p[0], cauda)
        dizer.append("B: a linha acaba aos %.2f (%.2f s depois do corte), o primeiro sinal volta aos %.2f e a linha "
                     "nova aos %.2f: acaba ai e cala-se em %.2f s" % (p[0], p[0] - no_corte, p[1], p[2], cauda))
    else:
        dizer.append("B: nenhuma pausa da voz nos %.0f s depois do corte" % render.TOLERANCIA_FIM_DE_FRASE)
    return fora, dizer


# --------------------------------------------------------------------------------- as copias
def linha_fins(s, no_corte, entra_in, sai_s, cauda, subida, ident):
    return {"sai": s["ultima"]["ficheiro"], "entra": s["real"], "no_corte": "%.2f" % no_corte,
            "entra_in": "%.2f" % entra_in, "sai_s": "%.2f" % sai_s, "cauda": "%.2f" % cauda,
            "subida_entra": "%.2f" % subida if subida is not None else "", "confianca": "por verificar", "id": ident}


def linha_da_saida(s, qual, sai_s, cauda):
    """A linha do data/fins_de_frase.csv que faz a saida A ou B, e a escolha com que o ponto5 a toca."""
    no_corte, dur = s["no_corte"], s["dur"]
    if qual == "A":
        e = s["entrada"]
        return linha_fins(s, no_corte, e["in_s"], sai_s, cauda, None, "creditos_A"), dict(s["escolha"])
    espera = round(sai_s - no_corte, 3)
    e = mc.entrada(s["inicio"], s["medidas"]["fim"], dur - espera, s["medidas"]["silencios"])
    return (linha_fins(s, sai_s, e["in_s"], sai_s, cauda, cauda, "creditos_B"),
            dict(s["escolha"], passagem="frase"))


def faixas_com(s, linha, escolha, avisos):
    """As faixas do exemplo com ANTES s de filme, pelo ponto5, com o data/fins_de_frase.csv de hoje mais
    `linha` (None: so o de hoje), numa copia temporaria. O verdadeiro nao se toca."""
    pos = s["no_corte"] - ANTES
    original = mc.FINS_DE_FRASE
    pasta = tempfile.mkdtemp(prefix="juncao_")
    try:
        if linha is not None:
            copia = os.path.join(pasta, "fins_de_frase.csv")
            with open(original, encoding="utf-8-sig", newline="") as fh:
                linhas = list(csv.DictReader(fh))
            with open(copia, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=COLUNAS_FINS)
                w.writeheader()
                for r in linhas + [linha]:
                    w.writerow({k: r.get(k, "") for k in COLUNAS_FINS})
            mc.FINS_DE_FRASE = copia
        with contextlib.redirect_stdout(io.StringIO()):
            faixas, info = p5.som_dos_creditos(s["ultima"], pos, ANTES, s["dur"], escolha, avisos,
                                               s["medidas"], s["caminho"])
    finally:
        mc.FINS_DE_FRASE = original
        shutil.rmtree(pasta, ignore_errors=True)
    return faixas, info


def som(faixas, total, saida, fade=0.0):
    """O som das faixas pelo render.construir_som. As copias pedem so os primeiros ANTES + DEPOIS segundos e
    nenhum fade no fim: o loudnorm de cada faixa e medido no troco inteiro dela (dura_medida), e o FADE_FIM_SOM
    do exemplo so comeca 4 s antes do fim dos creditos, por isso essa janela sai igual a do exemplo inteiro."""
    with contextlib.redirect_stdout(io.StringIO()):
        ok = render.construir_som(C.FF, [dict(f) for f in faixas], total, saida, fade)
    if not ok:
        raise SystemExit("o som nao se fez: %s" % saida)
    return saida


def lufs(caminho, de=None, ate=None):
    cmd = [C.FF, "-hide_banner", "-nostats"]
    if de is not None:
        cmd += ["-ss", "%.3f" % de, "-t", "%.3f" % (ate - de)]
    r = subprocess.run(cmd + ["-i", caminho, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    import re
    achado = re.findall(r"^\s*I:\s+(-?[\d.]+) LUFS", r.stderr or "", re.M)
    return float(achado[-1]) if achado else None


def medir_mistura(mistura, haste_sai, haste_entra, troca):
    """O vale da mistura e as duas vozes, de 1 s antes a 2,5 s depois da troca (segundos da copia): a juncao,
    e nao as quedas da propria musica que entra (a do Taking Care of Business aos 118,4 s do ficheiro, que
    caia na janela de uma troca mais tardia). A mediana de referencia e a de 1,5 a 4 s depois."""
    de, ate = troca - 1.0, troca + 2.5
    t, total, _ = envelope(ler(mistura, 0, ANTES + DEPOIS), 0.0)
    ts, _, vs = envelope(ler(haste_sai, 0, ANTES + DEPOIS), 0.0)
    te, _, ve = envelope(ler(haste_entra, 0, ANTES + DEPOIS), 0.0)
    j = (t >= de) & (t <= ate)
    n = min(len(vs), len(ve), len(t))
    duas = ((vs[:n] > -45) & (ve[:n] > -45) & (np.abs(vs[:n] - ve[:n]) < 12) & j[:n]).sum() * 0.01
    mediana = float(np.median(total[(t >= troca + 1.5) & (t <= troca + 4.0)]))
    k = np.argmin(np.where(j, total, 99))
    passos = [total[i + 20] - total[i] for i in range(len(total) - 20) if j[i]]
    # o que a que sai deixa ouvir depois da troca: a voz dela acima de -45 dB, contra a da que entra
    depois = (ts >= troca + 0.3) & (ts <= ate)
    resto = float(vs[depois].max()) if depois.any() else -99.0
    return {"min": round(float(total[k]), 1), "min_t": round(float(t[k]) - troca, 2), "mediana": round(mediana, 1),
            "abaixo_6": round(float(((total < mediana - 6) & j).sum() * 0.01), 2),
            "queda_200ms": round(float(min(passos)) if passos else 0.0, 1),
            "duas_vozes": round(float(duas), 2), "voz_sai_depois": round(resto, 1),
            "voz_entra": round(float(np.median(ve[(te >= troca + 1.0) & (te <= ate)])), 1)}


def copia(s, nome, faixas, pasta, nivel_filme=None):
    """A copia de 20 s (so som, AAC num .mp4) e as duas hastes para as medidas, todas pelo construir_som.

    COM O NIVEL DO FILME (nivel_filme, LUFS da que sai nesses segundos no render do filme): o exemplo do ponto5
    mede o loudnorm da que sai so no troco curto que ela toca nele, e nao no troco inteiro do filme, por isso
    ela pode sair um pouco acima ou abaixo do filme. Mede-se a haste dela e acerta-se o ganho dela na copia ao
    do filme; o acerto diz-se (m["acerto_db"]), e a dos creditos fica como o render a faz."""
    total = ANTES + DEPOIS + 1.0
    tmp = tempfile.mkdtemp(prefix="juncao_som_")
    try:
        faixas = [dict(f) for f in faixas]
        acerto = 0.0
        if nivel_filme is not None:
            haste = som([faixas[0]], total, os.path.join(tmp, "haste_antes.m4a"))
            medido = lufs(haste, 0.0, ANTES - FADE_LIVRE)
            if medido is not None:
                acerto = round(nivel_filme - medido, 2)
                faixas[0]["ganho"] = faixas[0].get("ganho", 1.0) * 10 ** (acerto / 20.0)
        mistura = som(faixas, total, os.path.join(tmp, "mistura.m4a"))
        hastes = [som([f], total, os.path.join(tmp, "haste%d.m4a" % i)) for i, f in enumerate(faixas)]
        saida = os.path.join(pasta, nome + ".mp4")
        subprocess.run([C.FF, "-v", "error", "-y", "-i", mistura, "-t", "%.3f" % (ANTES + DEPOIS),
                        "-af", "afade=t=out:st=%.3f:d=0.5" % (ANTES + DEPOIS - 0.5), "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", saida], check=True)
        cortadas = []
        for i, h in enumerate([mistura] + hastes):
            c = os.path.join(tmp, "c%d.wav" % i)
            subprocess.run([C.FF, "-v", "error", "-y", "-i", h, "-t", "%.3f" % (ANTES + DEPOIS), c], check=True)
            cortadas.append(c)
        while len(cortadas) < 3:
            cortadas.append(cortadas[-1])
        troca = faixas[1]["quando"] if len(faixas) > 1 else ANTES      # na copia, o zero e 8 s antes do corte
        m = medir_mistura(cortadas[0], cortadas[1], cortadas[2], troca)
        m["lufs_filme"] = lufs(saida, 0.0, ANTES - FADE_LIVRE)
        m["lufs_creditos"] = lufs(saida, troca + 1.0, ANTES + DEPOIS - 0.5) if len(faixas) > 1 else None
        m["troca"], m["acerto_db"] = troca, acerto
        return saida, m
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def nivel_no_filme(s):
    """LUFS da ultima musica de 8 s a 1,6 s antes do corte, como o render do filme a toca (a faixa dela, com o
    loudnorm medido no troco inteiro que o filme toca). Acaba 1,6 s antes do corte porque o FADE_FIM_SOM do
    filme (4 s) comeca 1,5 s antes dele; o master usa o filme so ate 5 s antes do corte."""
    tmp = tempfile.mkdtemp(prefix="juncao_filme_")
    try:
        saida = som([dict(s["ultima"])], s["corte_t"], os.path.join(tmp, "filme.m4a"))
        return lufs(saida, s["corte_t"] - ANTES, s["corte_t"] - FADE_LIVRE)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mao(nome):
    v = _arg(nome)
    if not v:
        return None
    a, b = v.replace(";", ",").split(",")[:2]
    return float(a), float(b)


def main():
    s = situacao()
    u, nc = s["ultima"], s["no_corte"]
    print("montagem %s: o corpo acaba aos %.2f s e os creditos comecam aos %.2f (o fim menos %.1f s de fade)%s"
          % (C.MONTAGEM, s["est"]["fim"], s["corte_t"], render.FADE_FIM_IMAGEM,
             (" COM O FIM %.2f s MAIS COMPRIDO (--alongar)" % s["mais"]) if s["mais"] else ""))
    print("a que sai: %s, entrou aos %.2f s do corpo no segundo %.2f do ficheiro; no corte esta aos %.2f s"
          % (C.nome_da_musica(u["ficheiro"]), u["quando"], u["in_s"], nc))
    print("leitura: %s; creditos de %.2f s" % (os.path.relpath(s["leitura"][1], C.REPO), s["dur"]))
    if not s.get("esc") or not s.get("real"):
        print("sem musica dos creditos escolhida (ou ja nao esta): «Como esta», a que sai continua. Nada a medir.")
        return
    e = s["entrada"]
    print("a dos creditos: %s com %r, entra aos %.2f s do ficheiro (cala-se aos %.2f)"
          % (C.nome_da_musica(s["real"]), s["esc"]["inicio"], e["in_s"], s["medidas"]["fim"]))
    av = []
    medida = mc.fim_de_frase(u["ficheiro"], s["real"], nc, e["in_s"], av)
    print("data/fins_de_frase.csv no corte: %s" % (("medida, desce aos %.2f em %.2f s" % (medida["sai_s"], medida["cauda"]))
                                                  if medida else "por medir" + (" (%s)" % av[0] if av else "")))
    espera, linha = p5.espera_pela_frase(u["ficheiro"], s["real"], nc, s["inicio"], s["medidas"], s["dur"], [])
    if linha:
        print("data/fins_de_frase.csv no fim da frase: medida, %.2f s depois do corte (passagem \"frase\")" % espera)
    # o que ha na que sai, a volta do corte
    x = ler(u["caminho"], nc - 3.0, nc + 4.6)
    t, total, voz = envelope(x, nc - 3.0)
    lista, nivel = pausas(t, voz, nc - 3.0, nc + 4.5)
    print("\nA QUE SAI, de %.2f a %.2f s do ficheiro (voz ao centro 1 a 4 kHz; as linhas a %.1f dB):" % (nc - 3, nc + 4.5, nivel))
    for k in range(0, len(t), 10):
        marca = " <- corte" if abs(t[k] - nc) < 0.05 else ""
        print("  %7.2f  mistura %6.1f  voz %6.1f%s" % (t[k], total[k:k + 10].mean(), voz[k:k + 10].mean(), marca))
    print("pausas da voz (fim de linha candidato -> primeiro sinal -> linha nova, fundo): %s"
          % ("; ".join("%.2f -> %.2f -> %.2f (%+.1f dB)" % p for p in lista) or "nenhuma"))
    prop, dizer = propostas(nc, lista)
    for d in dizer:
        print("  " + d)
    for qual, nome in (("A", "--a"), ("B", "--b")):
        if mao(nome):
            prop[qual] = mao(nome)
    print("saidas para as copias: %s" % ", ".join("%s sai_s %.2f cauda %.2f" % (q, v[0], v[1]) for q, v in sorted(prop.items())))
    if "--ouvir" not in sys.argv:
        return
    pasta = _arg("--saida") or C.pasta("juncao_creditos")
    os.makedirs(pasta, exist_ok=True)
    base = "juncao_%s" % ("%.2f" % (nc - s["mais"])).replace(".", "_")
    if s["mais"]:
        base += "_mais_%s" % ("%.2f" % s["mais"]).replace(".", "_")
    quais = (_arg("--variantes") or "hoje,A,B").split(",")
    variantes = [("hoje", None, {k: v for k, v in s["escolha"].items() if k != "passagem"})] if "hoje" in quais else []
    for qual in ("A", "B"):
        if qual in prop and qual in quais:
            linha_q, escolha_q = linha_da_saida(s, qual, *prop[qual])
            variantes.append((qual, linha_q, escolha_q))
    nivel = nivel_no_filme(s)
    print("\nnivel da que sai no filme (o render dele), de 8 a %.1f s antes do corte: %.1f LUFS" % (FADE_LIVRE, nivel))
    for qual, linha_q, escolha_q in variantes:
        avisos = []
        faixas, info = faixas_com(s, linha_q, escolha_q, avisos)
        saida, m = copia(s, "%s_%s" % (base, qual), faixas, pasta, nivel)
        print("\n%s: %s" % (qual, saida))
        if linha_q:
            print("  linha: " + ",".join(linha_q[k] for k in COLUNAS_FINS))
        for f in faixas:
            print("  faixa %-24s quando %6.2f in %7.2f dura %6.2f subida %s descida %s"
                  % (C.nome_da_musica(f["ficheiro"]), f["quando"] - ANTES, f["in_s"], f["dura"], f.get("subida"),
                     f.get("descida", f.get("cruza"))))
        for a in avisos:
            print("  aviso: " + a)
        print("  troca %+.2f s do corte; mistura: minimo %.1f dBFS (%+.2f s), mediana depois %.1f, %.2f s 6 dB abaixo, "
              "maior queda em 200 ms %.1f dB; duas vozes %.2f s; voz da que sai depois da troca ate %.1f dB (a que entra "
              "%.1f); copia a %s LUFS antes do corte (a que sai acertada %+.2f dB ao filme) e %s nos creditos"
              % (m["troca"] - ANTES, m["min"], m["min_t"], m["mediana"], m["abaixo_6"], m["queda_200ms"], m["duas_vozes"],
                 m["voz_sai_depois"], m["voz_entra"], m["lufs_filme"], m["acerto_db"], m["lufs_creditos"]))


if __name__ == "__main__":
    main()
