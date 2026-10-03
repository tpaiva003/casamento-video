# -*- coding: utf-8 -*-
"""As copias leves de cada som que a Mesa pode tocar, para ouvir o filme no palco (2 de outubro).

O Tiago, a 2 de outubro: quer "conseguir ouvir [as musicas] no timing certo durante a
pre-visualizacao". A Mesa tem de tocar o som do filme preso ao relogio do palco, e de o seguir
quando eles mudam a ordem, as duracoes ou as musicas marcadas. Por isso nao chega um pedaco ja
misturado de cada faixa da ultima montagem: a Mesa recebe UMA COPIA INTEIRA DE CADA FICHEIRO, e e ela
que corta, sobe, desce e cruza, com as regras do render (editor_base.html, palcoSomPlano).

O QUE ENTRA (fontes_da_mesa):
  - as musicas que a Mesa oferece para marcar, listadas como o gerar_mesa.py as lista
    (montar_da_mesa.caminhos_de_musica(), so ficheiros), com os efeitos (os foguetes do
    "Candidato a vereador" e o rebobinar.wav) incluidos;
  - os ficheiros das faixas de data/montagens/<nome>.som.csv, pelo caminho que la esta;
  - as vozes do pedido (montar_da_mesa.caminhos_de_voz()), que a Mesa tambem deixa marcar;
  - o som dos videos da ultima montagem (os de abertura, que o render cola com o som que trazem, e os
    do corpo);
  - e as intros de outras cores ou de outra letra ja feitas (intros_feitas), som e copia pequena, para o
    palco mostrar a que a aba Intro do Estilo escolheu no lugar da de hoje.

OS NULLS: as copias que deixam de servir juntam-se no indice (por_tirar) e vao com null em cada
publicar.json ate a publicacao; depois dela, `py -3.11 scripts/audio_para_mesa.py --publicado`.

A COPIA: AAC-LC mono a 32 kbit/s e 24 kHz (KBPS, TAXA). Sao 4 KB por segundo de som: as cerca de tres
horas destas fontes dao uns 46 MB, que cabem numa publicacao so para elas (64 MB) com folga para mais
umas quinze musicas. A pagina e as 45 folhas das previas ja levam uns 47 MB da publicacao da Mesa, por
isso o som vai numa segunda publicacao para o mesmo endereco (lotes(), que o gerar_mesa.py escreve).
Mono porque o projetor e as colunas do DJ e que dao a imagem estereo, e a Mesa so tem de dizer onde
cada coisa entra; a 24 kHz o AAC nao gasta bits acima dos 12 kHz, que a 32 kbit/s seriam chiado. Chega
para julgar tempos, passagens e fins de frase; nao serve para julgar o som do projetor, e a Mesa diz
isso. O AAC le-se em qualquer browser, o Safari do iPhone incluido.

O NIVEL: O RESULTADO DO RENDER, NAO O PROCESSO. O render passa cada leito e cada efeito pelo loudnorm
(I=-23) e acerta o ganho quando ele falha por mais de 1 dB (render.falta_ao_loudnorm, decisao 087):
o troco que toca acaba a render.LEITO_SAIDA_LUFS, e o alimiter da mistura sobe-o para os -21,9 do
filme. Aqui mede-se a sonoridade da copia segundo a segundo (o `perfil`, ebur128 da copia tocada como
o browser a toca, os dois canais iguais), e a Mesa calcula a de cada troco que vai tocar e da-lhe o
ganho que o poe no mesmo alvo: o troco certo, o da montagem ou um marcado agora. O `ganho_db` e o do
ficheiro inteiro, para quando nao ha perfil. As vozes e o som dos videos nao levam loudnorm no
render: o `cru_db` e o que poe a copia ao nivel do ficheiro original.

E DUAS MEDIDAS DO ORIGINAL, para a Mesa decidir como o montar e o render decidem:
  - `silencios`: os silencios do silencio_no_inicio() do montar (silencedetect a -45 dB, 0,3 s), com
    que uma musica marcada salta o silencio do principio;
  - `inicios`: os segundos de entrada em que o render.entra_num_inicio() diz que sim (quase silencio
    nos 0,4 s antes e som logo a seguir), onde a musica entra sem rampa (decisao 094).

NAO REFAZ O QUE JA EXISTE IGUAL. Cada copia chama-se pelo conteudo do original (sha1) e pela receita
da copia: um ficheiro que nao mudou nao se volta a codificar nem a medir, e uma publicacao nova so
precisa de levar os nomes novos. O sha1 de cada original guarda-se pelo tamanho e pela data, em
saida/audio/indice.json, para nao se ler tudo outra vez a cada Mesa. As copias que deixam de ser
precisas saem da pasta (sao nossas, em saida/) e ficam em `tiradas`, para se tirarem com null.

So le em C:\\casamento-video-media. Escreve so em saida/audio e saida/video, fora do Git.

Uso:  py -3.11 scripts/audio_para_mesa.py          (faz o que faltar e diz o peso e os lotes)
      e o gerar_mesa.py chama-o sozinho, a cada Mesa.
"""
import concurrent.futures
import csv
import datetime
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import threading
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTAGENS = os.path.join(REPO, "data", "montagens")
SAIDA = os.path.join(REPO, "saida")
PASTA_AUDIO = os.path.join(SAIDA, "audio")
PASTA_VIDEO = os.path.join(SAIDA, "video")
INDICE = os.path.join(PASTA_AUDIO, "indice.json")
# O QUE SE PASSA A FERRAMENTA DE PUBLICAR, lote a lote: o mapa `files` (com root saida) e os que saem com null
PUBLICAR = os.path.join(PASTA_AUDIO, "publicar.json")
TIPOS = {".m4a": "audio/mp4", ".mp4": "video/mp4"}
FINS_DE_FRASE = os.path.join(REPO, "data", "fins_de_frase.csv")
ENTRADAS_ATAQUE = os.path.join(REPO, "data", "entradas_ataque.csv")

KBPS = 32
TAXA = 24000
# A RECEITA DA COPIA entra no nome: se um dia mudar, todas se refazem com nome novo, e as velhas saem.
RECEITA = "aac-lc mono %d Hz %d kbit/s faststart; perfil ebur128 1 s; v1" % (TAXA, KBPS)
EXT_SOM = (".mp3", ".wav", ".m4a", ".wma", ".flac", ".ogg")
# UM VIDEO MUITO LONGO SO LEVA O TROCO QUE A MONTAGEM USA (mais FOLGA_TROCO de cada lado): uma hora de
# som a 32 kbit/s sao 14 MB, perto do limite de 15 MB por ficheiro, e a Mesa so toca o troco.
VIDEO_INTEIRO_ATE_S = 1800.0
FOLGA_TROCO = 5.0
# OS LIMITES DA PUBLICACAO (CLAUDE.md e a ferramenta): 64 MB por publicacao, 15 MB por ficheiro,
# 256 ficheiros ao todo no endereco, a contar com a pagina. Os lotes ficam abaixo dos 60 MB.
MB = 1048576.0
LOTE_MAX = 60 * MB
FICHEIRO_MAX = 15 * MB
FICHEIROS_MAX = 256
# AS COPIAS PEQUENAS DOS VIDEOS DA MONTAGEM, para o palco: 640x360, 25 fps, sem som (o som vai a
# parte, nas copias de cima). Vem do palco de 2 de outubro, e ficam aqui para os nomes serem pelo
# conteudo, como as do som.
VIDEO_LARGURA, VIDEO_ALTURA, VIDEO_CRF = 640, 360, 30
RECEITA_VIDEO = "h264 640x360 crf %d 25 fps sem som; v1" % VIDEO_CRF
# O render (render.entra_num_inicio, _nivel_dbfs): 0,4 s antes e depois, a 16 kHz mono
JANELA_INICIO = 0.4
INICIO_ANTES_DB = -40.0
INICIO_SALTO_DB = 15.0
PASSO_INICIO = 0.01
# O montar (silencio_no_inicio): -45 dB durante 0,3 s
SILENCIO_DB = -45.0
SILENCIO_MIN = 0.3
TRABALHADORES = 4


def _ff():
    import render
    return render.ffmpeg()


def _ffprobe():
    return os.path.join(os.path.dirname(_ff()), "ffprobe.exe")


def _corre(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _sha1_ficheiro(caminho):
    h = hashlib.sha1()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _slug(nome, maximo=36):
    base = os.path.splitext(nome)[0]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return (base[:maximo].strip("_")) or "som"


def _duracao(caminho):
    r = _corre([_ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", caminho])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# ------------------------------------------------------------------------------------- as fontes
def _linhas_csv(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fontes_da_mesa(nome="v3"):
    """{nome do ficheiro: {caminho, tipo, arranque, troco}} de cada som que a Mesa pode tocar.

    `tipo` e "musica", "voz" ou "video". O nome e a chave do window.AUDIO, a mesma que o som.csv, a
    marca da Mesa (depois do resolve_musica) e o clip de video usam. `troco` (so nos videos muito
    longos) e o (inicio, fim) da copia dentro do original.
    """
    import montar_da_mesa
    import render
    fontes = {}
    # AS MUSICAS QUE A MESA OFERECE, como o gerar_mesa.musicas_do_projeto() as lista. A lista traz
    # tambem as pastas de gerados/ (fontes, voo, ...), que nao sao som: so entram ficheiros.
    # Os da pasta gerados (o andar da fita, o som do pedido, o rebobinar) levam `gerado`: tocam-se como os
    # outros, mas nao sao musicas, e a lista da musica dos creditos deixa-os de fora (revisor, 2 de outubro).
    gerados = os.path.normcase(os.path.normpath(montar_da_mesa.GERADOS))
    for f, caminho in montar_da_mesa.caminhos_de_musica().items():
        if f.lower().endswith(EXT_SOM) and os.path.isfile(caminho):
            fontes[f] = {"caminho": caminho, "tipo": "musica"}
            if os.path.normcase(os.path.dirname(os.path.normpath(caminho))) == gerados:
                fontes[f]["gerado"] = True
    # AS FAIXAS DA MONTAGEM, pelo caminho que o render vai abrir
    for r in _linhas_csv(os.path.join(MONTAGENS, nome + ".som.csv")):
        f, caminho = r.get("ficheiro") or "", r.get("caminho") or ""
        if f and f not in fontes and caminho and os.path.isfile(caminho):
            tipo = "voz" if (r.get("voz") or "").strip() else "video" if (r.get("video") or "").strip() else "musica"
            fontes[f] = {"caminho": caminho, "tipo": tipo}
    # AS VOZES DO PEDIDO
    try:
        for f, caminho in montar_da_mesa.caminhos_de_voz().items():
            if os.path.isfile(caminho):
                fontes.setdefault(f, {"caminho": caminho, "tipo": "voz"})
    except Exception as erro:                        # noqa: BLE001
        print("  AVISO: nao consegui listar as vozes do pedido (%s)" % erro)
    # O SOM DOS VIDEOS DA MONTAGEM. So os da montagem: a lista da Mesa tem videos de hora e meia, e o
    # som de todos nao cabia; um video novo na montagem entra na Mesa seguinte.
    linhas = _linhas_csv(os.path.join(MONTAGENS, nome + ".csv"))
    for l in linhas:
        if l.get("tipo") != "video" or not (l.get("ficheiro") or "").strip():
            continue
        f = l["ficheiro"].strip()
        caminho, arranque = render.caminho_de_video(f)
        if not caminho or not os.path.isfile(caminho) or not render.tem_stream_de_som(caminho):
            continue
        item = fontes.get(f) or {"caminho": caminho, "tipo": "video", "arranque": float(arranque or 0.0)}
        dentro = float(l.get("in_s") or 0.0) if str(l.get("in_s") or "").strip() else float(arranque or 0.0)
        item.setdefault("trocos", []).append((dentro, dentro + float(l.get("duracao_s") or 0.0)))
        fontes[f] = item
    # AS INTROS DE OUTRAS CORES JA FEITAS (revisor de 2 de outubro): com outras cores na aba Intro do Estilo o
    # montar troca a intro 5 pela dessas cores, e o palco tocava a de hoje. Sao poucas e curtas (uns 50 KB de
    # som cada), e entram inteiras.
    for x in intros_do_estilo():
        if x["f"] not in fontes and render.tem_stream_de_som(x["caminho"]):
            fontes[x["f"]] = {"caminho": x["caminho"], "tipo": "video", "arranque": 0.0}
    for f, item in fontes.items():
        if item["tipo"] == "video" and item.get("trocos"):
            total = _duracao(item["caminho"])
            if total > VIDEO_INTEIRO_ATE_S:
                a = max(0.0, min(x for x, _y in item["trocos"]) - FOLGA_TROCO)
                b = min(total, max(y for _x, y in item["trocos"]) + FOLGA_TROCO)
                item["troco"] = (round(a, 3), round(b, 3))
            item.pop("trocos", None)
    return fontes


# AS INTROS DE OUTRAS CORES QUE JA ESTAO FEITAS (2 de outubro). O montar_da_mesa.intro_da_paleta() so usa um
# ficheiro igualado cujo comentario dos metadados seja o da paleta com as fotos da intro 5; a Mesa diz "ja
# feita" a partir disto (gerar_mesa.intros_feitas, que chama esta) e o palco toca a copia dela.
#
# E A LETRA DO LETREIRO (2 de outubro, a noite): uma intro feita com outra letra leva o id dela no nome, a
# seguir aos 6 hex (intro_clara_tiago_5 sem preto_<6 hex>_<id> igualado.mp4), e " fonte <id>" no comentario,
# a seguir ao tamanho (intro_flipbook.nome_da_intro e resumo_da_paleta). Sem letra os dois ficam como eram, e
# a letra e o Impact. As duas expressoes sao as que a equipa do render deu (render3_para_a_mesa, letra_intro).
PALETA_NO_COMENTARIO = re.compile(r"^paleta fundo (#[0-9A-F]{6}) papel (#[0-9A-F]{6}) tinta (#[0-9A-F]{6}) "
                                  r"letra (#[0-9A-F]{6}) tamanho (\d+)(?: fonte ([a-z0-9]+))?; fotos da intro 5$")
INTRO_IGUALADA = re.compile(r"^intro_clara_tiago_5( sem preto)?_[0-9a-f]{6}(?:_([a-z0-9]+))? igualado\.mp4$",
                            re.IGNORECASE)
LETRA_DE_SEMPRE = "impact"         # render.INTRO_FONTE: a letra de uma intro sem " fonte <id>" no comentario


def intros_feitas(pasta=None):
    """[{fundo, papel, tinta, letra, tamanho, fonte, sem_preto, f}] das intros de outras cores (ou de outra
    letra) ja igualadas, ou None se nao se conseguiu ver (sem a pasta ou sem o ffprobe): a Mesa cai entao nas
    quatro propostas. `f` e o nome do ficheiro e `fonte` o id da letra do letreiro ("impact" sem letra).
    So le (o ffprobe dos metadados), nunca escreve na pasta dos media.

    A LETRA DO NOME E A DO COMENTARIO TEM DE SER A MESMA. O montar acha a intro pelo nome que o resumo do
    comentario da (intro_flipbook.nome_da_intro): um ficheiro com o _bernard no nome e outra letra (ou
    nenhuma) no comentario nunca seria o que ele procura, e a Mesa dizia "ja feita" de uma intro que a
    montagem refaz. Esse fica de fora, com aviso."""
    try:
        import render
        pasta = pasta or render.PASTA_SOM_IGUALADO
        sonda = _ffprobe()
        nomes = sorted(n for n in os.listdir(pasta) if INTRO_IGUALADA.match(n))
    except (OSError, SystemExit, ImportError, AttributeError) as erro:
        print("  AVISO: nao vi as intros ja feitas (%s): a Mesa conta so com as quatro propostas" % erro)
        return None
    feitas = []
    for nome in nomes:
        try:
            r = _corre([sonda, "-v", "error", "-show_entries", "format_tags=comment", "-of", "default=nw=1:nk=1",
                        os.path.join(pasta, nome)])
        except OSError as erro:
            print("  AVISO: nao li a paleta de %s (%s): a Mesa conta so com as quatro propostas" % (nome, erro))
            return None
        m = PALETA_NO_COMENTARIO.match((r.stdout or "").strip())
        if not m:
            continue
        n = INTRO_IGUALADA.match(nome)
        fonte = m.group(6) or LETRA_DE_SEMPRE
        no_nome = (n.group(2) or LETRA_DE_SEMPRE).lower()
        if no_nome != fonte:
            print("  AVISO: %s tem a letra %s no nome e %s nos metadados: a montagem nao a usa, e a Mesa nao a "
                  "conta como feita" % (nome, no_nome, fonte))
            continue
        feitas.append({"fundo": m.group(1), "papel": m.group(2), "tinta": m.group(3), "letra": m.group(4),
                       "tamanho": int(m.group(5)), "fonte": fonte, "sem_preto": bool(n.group(1)), "f": nome})
    return feitas


def intros_do_estilo():
    """[{f, caminho}] das intros de outras cores ja igualadas que o montar aceita, para as copias do palco.
    Vazio sem a pasta ou sem o ffprobe."""
    import render
    saida = []
    for x in intros_feitas() or []:
        caminho = os.path.join(render.PASTA_SOM_IGUALADO, x["f"])
        if os.path.isfile(caminho):
            saida.append({"f": x["f"], "caminho": caminho})
    return saida


# ------------------------------------------------------------------------------- copiar e medir
def _codificar(origem, destino, troco=None):
    tmp = destino + ".parte.mp4"
    cmd = [_ff(), "-hide_banner", "-loglevel", "error", "-y"]
    if troco:
        cmd += ["-ss", "%.3f" % troco[0], "-t", "%.3f" % (troco[1] - troco[0])]
    cmd += ["-i", origem, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(TAXA), "-c:a", "aac", "-b:a",
            "%dk" % KBPS, "-movflags", "+faststart", tmp]
    r = _corre(cmd)
    if r.returncode != 0 or not os.path.exists(tmp):
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError((r.stderr or "")[-300:])
    os.replace(tmp, destino)


MOMENTO = re.compile(r"t:\s*([\d.]+)\s+TARGET:\S+ LUFS\s+M:\s*(-?[\d.]+|-inf)")
INTEGRADA = re.compile(r"^\s*I:\s+(-?[\d.]+) LUFS", re.M)


def perfil_da_copia(copia):
    """(perfil, integrada): a sonoridade da copia segundo a segundo, em decimas de LUFS, e a do
    ficheiro inteiro. Mede-se a copia como o browser a toca: mono para os dois canais, igual nos dois.

    CADA SEGUNDO k e a media da energia das janelas momentaneas de 400 ms do ebur128 que cabem em
    [k, k + 1] (t de k + 0,4 a k + 1). Abaixo de -70 LUFS fica -700 (o portao absoluto do BS.1770)."""
    r = _corre([_ff(), "-hide_banner", "-nostats", "-i", copia, "-af",
                "pan=stereo|c0=c0|c1=c0,ebur128=framelog=info", "-f", "null", "-"])
    por_segundo = {}
    for m in MOMENTO.finditer(r.stderr or ""):
        t = round(float(m.group(1)), 2)          # o ebur128 escreve 0.399979 para os 0,4 s
        valor = m.group(2)
        e = 0.0 if valor == "-inf" else 10 ** (float(valor) / 10.0)
        k = int(math.floor(t - 0.4 + 1e-9))
        if k < 0 or t - k > 1.0 + 1e-9:
            continue
        por_segundo.setdefault(k, []).append(e)
    n = int(math.ceil(_duracao(copia)))
    perfil = []
    for k in range(n):
        es = por_segundo.get(k) or por_segundo.get(k - 1) or [0.0]
        media = sum(es) / len(es)
        db = 10 * math.log10(media) if media > 0 else -99.0
        perfil.append(int(round(max(-70.0, db) * 10)))
    achado = INTEGRADA.findall(r.stderr or "")
    integrada = float(achado[-1]) if achado else None
    return perfil, integrada


def integrada_do_original(origem, troco=None):
    """A sonoridade do original como o render o le (estereo a 48 kHz, o aformat do construir_som)."""
    cmd = [_ff(), "-hide_banner", "-nostats"]
    if troco:
        cmd += ["-ss", "%.3f" % troco[0], "-t", "%.3f" % (troco[1] - troco[0])]
    cmd += ["-i", origem, "-map", "0:a:0", "-af",
            "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,ebur128=framelog=quiet",
            "-f", "null", "-"]
    achado = INTEGRADA.findall(_corre(cmd).stderr or "")
    return float(achado[-1]) if achado else None


def silencios_do_original(origem):
    """[[inicio, fim]] dos silencios do original, como o montar_da_mesa.silencio_no_inicio() os ve."""
    r = _corre([_ff(), "-hide_banner", "-nostats", "-i", origem, "-map", "0:a:0", "-af",
                "silencedetect=noise=%.0fdB:d=%.2f" % (SILENCIO_DB, SILENCIO_MIN), "-f", "null", "-"])
    fora, aberto = [], None
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", r.stderr or ""):
        if m.group(1) == "start":
            aberto = max(0.0, float(m.group(2)))
        elif aberto is not None:
            fora.append([round(aberto, 3), round(float(m.group(2)), 3)])
            aberto = None
    if aberto is not None:
        fora.append([round(aberto, 3), round(_duracao(origem), 3)])
    return fora


def inicios_do_original(origem):
    """[[a, b]] dos segundos de entrada em que o render.entra_num_inicio() diz que sim, de PASSO_INICIO
    em PASSO_INICIO: o nivel nos 0,4 s antes abaixo de -40 dBFS e o de depois 15 dB acima. A mesma
    leitura do _nivel_dbfs do render (mono, 16 kHz, s16), sobre o ficheiro inteiro. O "in no zero" a
    Mesa sabe sozinha."""
    import numpy as np
    r = subprocess.run([_ff(), "-v", "error", "-i", origem, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                        "-f", "s16le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout[: len(r.stdout) // 2 * 2], dtype="<i2").astype(np.float64)
    if not len(x):
        return []
    soma = np.concatenate([[0.0], np.cumsum(x * x)])
    n = len(x)
    j = int(round(JANELA_INICIO * 16000))
    grelha = np.arange(int(round(0.05 / PASSO_INICIO)), int(n / 16000.0 / PASSO_INICIO))
    i = np.round(grelha * PASSO_INICIO * 16000).astype(np.int64)
    a0 = np.maximum(0, i - j)
    na = i - a0
    nb = np.minimum(n, i + j) - i
    ok = (na > 0) & (nb > 0)
    rms_a = np.sqrt((soma[i] - soma[a0]) / np.maximum(1, na)) / 32768.0
    rms_b = np.sqrt((soma[np.minimum(n, i + j)] - soma[i]) / np.maximum(1, nb)) / 32768.0
    db_a = 20 * np.log10(np.maximum(1e-6, rms_a))
    db_b = 20 * np.log10(np.maximum(1e-6, rms_b))
    sim = ok & (db_a < INICIO_ANTES_DB) & (db_b - db_a > INICIO_SALTO_DB)
    fora, aberto = [], None
    for g, s in zip(grelha.tolist(), sim.tolist()):
        if s and aberto is None:
            aberto = g
        elif not s and aberto is not None:
            fora.append([round(aberto * PASSO_INICIO, 2), round((g - 1) * PASSO_INICIO, 2)])
            aberto = None
    if aberto is not None:
        fora.append([round(aberto * PASSO_INICIO, 2), round(grelha[-1] * PASSO_INICIO, 2)])
    return fora


def medir_copia(nome, item, copia):
    """O que a Mesa precisa de saber desta copia (sem o url, que vem do nome)."""
    perfil, integrada = perfil_da_copia(copia)
    original = integrada_do_original(item["caminho"], item.get("troco"))
    m = {"duracao": round(_duracao(copia), 3), "perfil": perfil,
         "integrada": None if integrada is None else round(integrada, 2),
         "original": None if original is None else round(original, 2),
         "bytes": os.path.getsize(copia)}
    if item["tipo"] == "musica":
        m["silencios"] = silencios_do_original(item["caminho"])
        m["inicios"] = inicios_do_original(item["caminho"])
    return m


# ------------------------------------------------------------------------------- o indice
_TRANCA = threading.Lock()


def _ler_indice():
    try:
        with io.open(INDICE, encoding="utf-8") as fh:
            ind = json.load(fh)
        if isinstance(ind, dict) and ind.get("receita") == RECEITA:
            return ind
    except (OSError, ValueError):
        pass
    return {"receita": RECEITA, "originais": {}, "copias": {}, "videos": {}}


def _escrever_indice(ind):
    tmp = INDICE + ".parte"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ind, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, INDICE)


def _sha1_guardado(ind, caminho):
    """O sha1 do original, lido de novo so quando o tamanho ou a data mudam."""
    st = os.stat(caminho)
    chave = os.path.normcase(os.path.abspath(caminho))
    g = ind["originais"].get(chave)
    if g and g.get("tamanho") == st.st_size and g.get("mtime") == st.st_mtime_ns:
        return g["sha1"]
    sha = _sha1_ficheiro(caminho)
    with _TRANCA:
        ind["originais"][chave] = {"tamanho": st.st_size, "mtime": st.st_mtime_ns, "sha1": sha}
    return sha


def _id_da_copia(sha, troco):
    h = hashlib.sha1(("%s|%s|%s" % (sha, RECEITA, troco or "")).encode("utf-8")).hexdigest()
    return h[:10]


# --------------------------------------------------------------------- as copias dos videos
def _copia_do_video(origem, inicio, dura, saida):
    vf = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25"
          % (VIDEO_LARGURA, VIDEO_ALTURA, VIDEO_LARGURA, VIDEO_ALTURA))
    tmp = saida + ".parte.mp4"
    r = _corre([_ff(), "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.3f" % inicio, "-t", "%.3f" % dura,
                "-i", origem, "-an", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", str(VIDEO_CRF),
                "-maxrate", "900k", "-bufsize", "1800k", "-pix_fmt", "yuv420p", "-profile:v", "main",
                "-movflags", "+faststart", tmp])
    if r.returncode != 0 or not os.path.exists(tmp):
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError((r.stderr or "")[-300:])
    os.replace(tmp, saida)


def videos_do_palco(ind, nome="v3"):
    """{ficheiro: [{url, in, dura, de}]} das copias pequenas dos videos da montagem, para o palco.
    `de` e o segundo do original onde a copia comeca; a copia vai de 0 a dura."""
    import render
    saida, escritos = {}, []
    os.makedirs(PASTA_VIDEO, exist_ok=True)
    for l in _linhas_csv(os.path.join(MONTAGENS, nome + ".csv")):
        if l.get("tipo") != "video" or not (l.get("ficheiro") or "").strip():
            continue
        f = l["ficheiro"].strip()
        origem, arranque = render.caminho_de_video(f)
        if not origem or not os.path.isfile(origem):
            continue
        dentro = float(l["in_s"]) if str(l.get("in_s") or "").strip() else float(arranque or 0.0)
        dura = float(l.get("duracao_s") or 0.0)
        if dura <= 0.04:
            continue
        sha = _sha1_guardado(ind, origem)
        vid = hashlib.sha1(("%s|%s|%.3f|%.3f" % (sha, RECEITA_VIDEO, dentro, dura)).encode("utf-8")).hexdigest()[:10]
        nome_v = "%s_%s.mp4" % (_slug(f, 28), vid)
        destino = os.path.join(PASTA_VIDEO, nome_v)
        if not os.path.exists(destino):
            try:
                _copia_do_video(origem, dentro, dura, destino)
                print("  video  %-40s %.1f s do segundo %.1f" % (nome_v, dura, dentro))
            except RuntimeError as erro:
                print("  ERRO na copia do video %s: %s" % (f, erro))
                continue
        escritos.append(nome_v)
        saida.setdefault(f, []).append({"url": "video/" + nome_v, "in": round(dentro, 3), "dura": round(dura, 3),
                                        "de": round(dentro, 3)})
    # E AS INTROS DE OUTRAS CORES JA FEITAS, inteiras: o palco mostra a que o Estilo escolheu no lugar da de hoje
    # (palcoIntroDoEstilo), com a duracao da copia, que e a que o montar mede no ficheiro
    for x in intros_do_estilo():
        if x["f"] in saida:
            continue
        dura = _duracao(x["caminho"])
        if dura <= 0.04:
            continue
        sha = _sha1_guardado(ind, x["caminho"])
        vid = hashlib.sha1(("%s|%s|%.3f|%.3f" % (sha, RECEITA_VIDEO, 0.0, dura)).encode("utf-8")).hexdigest()[:10]
        nome_v = "%s_%s.mp4" % (_slug(x["f"], 40), vid)
        destino = os.path.join(PASTA_VIDEO, nome_v)
        if not os.path.exists(destino):
            try:
                _copia_do_video(x["caminho"], 0.0, dura, destino)
                print("  video  %-40s %.1f s, a intro de outras cores" % (nome_v, dura))
            except RuntimeError as erro:
                print("  ERRO na copia da intro %s: %s" % (x["f"], erro))
                continue
        escritos.append(nome_v)
        saida[x["f"]] = [{"url": "video/" + nome_v, "in": 0.0, "dura": round(dura, 3), "de": 0.0}]
    return saida, escritos


# ----------------------------------------------------------------------------- o que se faz
def preparar(nome="v3", fazer=True, com_video=True):
    """Faz as copias que faltam e devolve o indice da Mesa: {audio, info}.

    `audio` e o window.AUDIO: {ficheiro: {url, ganho_db, duracao, cru_db, perfil, ...}}.
    `info` e o window.AUDIO_INFO: a receita, os lotes da publicacao, as regras do render que a Mesa
    imita (constantes, fins de frase, entradas num ataque) e o que cada faixa da montagem leva.
    Com fazer=False so le o que ja esta feito (sem ffmpeg, por exemplo)."""
    import render
    os.makedirs(PASTA_AUDIO, exist_ok=True)
    ind = _ler_indice()
    # SO SE APAGA O QUE SOBRA DEPOIS DE UMA LISTAGEM INTEIRA. A 2 de outubro uma listagem que falhou (o montar
    # nao se deixou importar) deu zero fontes, e a limpeza levou as 64 copias: com a lista vazia ou partida, nada
    # sai da pasta.
    listou = True
    try:
        fontes = fontes_da_mesa(nome)
    except (SystemExit, Exception) as erro:         # noqa: BLE001 - uma Mesa sem som continua a servir
        print("  AVISO: nao consegui ver as fontes do som (%s)" % erro)
        fontes, listou = {}, False
    if not fontes:
        listou = False

    # OS NOMES DAS COPIAS, pelo conteudo
    planeadas = {}
    for f, item in sorted(fontes.items()):
        try:
            sha = _sha1_guardado(ind, item["caminho"])
        except OSError as erro:
            print("  AVISO: nao li %s (%s)" % (item["caminho"], erro))
            continue
        cid = _id_da_copia(sha, item.get("troco"))
        # .mp4 e nao .m4a (2 de outubro): o mesmo AAC em MP4, mas o endereco da Mesa so serve .mp4, .mp3,
        # .ogg, .wav e .webm, e recusou a publicacao inteira por causa da extensao .m4a.
        planeadas[f] = (cid, "%s_%s.mp4" % (_slug(f), cid), item)

    # AS QUE FALTAM: codificar e medir, quatro de cada vez (sao processos do ffmpeg)
    por_fazer = {}
    for f, (cid, ficheiro, item) in planeadas.items():
        feita = ind["copias"].get(cid)
        if not (feita and os.path.exists(os.path.join(PASTA_AUDIO, ficheiro)) and feita.get("ficheiro") == ficheiro):
            por_fazer.setdefault(cid, (f, ficheiro, item))

    def trabalho(args):
        f, ficheiro, item = args
        destino = os.path.join(PASTA_AUDIO, ficheiro)
        if not os.path.exists(destino):
            _codificar(item["caminho"], destino, item.get("troco"))
        m = medir_copia(f, item, destino)
        m["ficheiro"] = ficheiro
        return m

    if por_fazer and fazer:
        print("  som: %d copias por fazer (das %d fontes)" % (len(por_fazer), len(planeadas)))
        with concurrent.futures.ThreadPoolExecutor(TRABALHADORES) as ex:
            futuros = {ex.submit(trabalho, args): cid for cid, args in por_fazer.items()}
            for fut in concurrent.futures.as_completed(futuros):
                cid = futuros[fut]
                f = por_fazer[cid][0]
                try:
                    ind["copias"][cid] = fut.result()
                    print("    %-48s %5.1f MB" % (por_fazer[cid][1][:48], ind["copias"][cid]["bytes"] / MB))
                except Exception as erro:          # noqa: BLE001 - uma copia que falha nao para as outras
                    print("  ERRO na copia de %s: %s" % (f, erro))
        _escrever_indice(ind)
    elif por_fazer:
        print("  som: %d copias por fazer, e nao as faco aqui" % len(por_fazer))

    videos, escritos_v, videos_ok = ({}, [], False)
    if com_video and fazer:
        try:
            videos, escritos_v = videos_do_palco(ind, nome)
            videos_ok = True
        except Exception as erro:                  # noqa: BLE001
            print("  AVISO: nao fiz as copias dos videos (%s)" % erro)
        _escrever_indice(ind)
    elif os.path.isdir(PASTA_VIDEO):
        videos = ind.get("ultimos_videos") or {}
        escritos_v = [v["url"].split("/", 1)[1] for lista in videos.values() for v in lista
                      if os.path.exists(os.path.join(SAIDA, v["url"]))]

    # O window.AUDIO
    audio, usadas = {}, set()
    for f, (cid, ficheiro, item) in sorted(planeadas.items()):
        c = ind["copias"].get(cid)
        if not c or not os.path.exists(os.path.join(PASTA_AUDIO, ficheiro)):
            continue
        usadas.add(ficheiro)
        x = {"url": "audio/" + ficheiro, "duracao": c["duracao"], "tipo": item["tipo"], "perfil": c["perfil"]}
        if c.get("integrada") is not None and c["integrada"] > -70:
            x["ganho_db"] = round(render.LEITO_SAIDA_LUFS - c["integrada"], 2)
            if c.get("original") is not None and c["original"] > -70:
                x["cru_db"] = round(c["original"] - c["integrada"], 2)
        else:
            x["ganho_db"] = 0.0
        x.setdefault("cru_db", 0.0)
        if item.get("troco"):
            x["desde"] = item["troco"][0]
        if item.get("gerado"):
            x["gerado"] = True
        if item["tipo"] == "video":
            x["arranque"] = round(item.get("arranque") or 0.0, 3)
        for k in ("silencios", "inicios"):
            if c.get(k):
                x[k] = c[k]
        audio[f] = x

    # O QUE SOBROU DE CORRIDAS ANTERIORES: sai da pasta, e diz-se, para se tirar com null
    tiradas = []
    # (as ".parte" sao copias a meio, talvez de outra corrida ao mesmo tempo: nunca se tocam)
    # (so quem faz as copias apaga, e so depois de uma listagem inteira: uma leitura so diz o que sobra)
    apaga = fazer and listou
    for f in sorted(os.listdir(PASTA_AUDIO)):
        if f.lower().endswith((".m4a", ".mp4")) and f not in usadas and ".parte" not in f:
            if apaga:
                os.remove(os.path.join(PASTA_AUDIO, f))
            tiradas.append("audio/" + f)
    if com_video and apaga and videos_ok and os.path.isdir(PASTA_VIDEO):
        for f in sorted(os.listdir(PASTA_VIDEO)):
            if f.lower().endswith(".mp4") and f not in escritos_v and ".parte" not in f:
                os.remove(os.path.join(PASTA_VIDEO, f))
                tiradas.append("video/" + f)
    # OS NULLS NAO SE PERDEM DE UMA CORRIDA PARA A OUTRA (revisor de 2 de outubro). Uma copia que deixa de servir
    # sai da pasta na corrida que a tira, e so essa a via: se a Mesa se montasse outra vez antes de publicar, o
    # publicar.json saia sem o null e a copia velha ficava no endereco para sempre. As tiradas juntam-se no
    # indice (por_tirar) ate alguem dizer que publicou (--publicado); uma que volte a ser precisa sai da lista.
    em_uso = set("audio/" + f for f in usadas) | set("video/" + f for f in escritos_v)
    tiradas_agora = tiradas
    tiradas = sorted((set(ind.get("por_tirar") or []) | set(tiradas_agora)) - em_uso)
    if fazer:
        ind["por_tirar"] = tiradas
        if videos_ok:
            ind["ultimos_videos"] = videos
        # "feito" e quando as copias mudaram, e nao a ultima vez que a Mesa se montou
        if (por_fazer and fazer) or tiradas_agora or not ind.get("feito"):
            ind["feito"] = datetime.datetime.now().strftime("%d/%m às %H:%M")
        _escrever_indice(ind)

    ficheiros = sorted(set("audio/" + f for f in usadas)) + sorted("video/" + f for f in escritos_v)
    tamanhos = {u: os.path.getsize(os.path.join(SAIDA, u)) for u in ficheiros}
    info = {"receita": RECEITA, "kbps": KBPS, "taxa": TAXA, "feito": ind.get("feito"),
            "ficheiros": len(ficheiros), "bytes": sum(tamanhos.values()),
            "bytes_som": sum(v for u, v in tamanhos.items() if u.startswith("audio/")),
            "lotes": lotes(tamanhos), "tiradas": tiradas,
            "grandes": [u for u, v in tamanhos.items() if v > FICHEIRO_MAX],
            "videos": videos, "r": regras_do_render(), "faixas": faixas_da_montagem(nome),
            "fins": fins_de_frase(), "ataques": entradas_num_ataque(),
            "sem_copia": sorted(f for f in fontes if f not in audio)}
    if fazer:
        escrever_publicar(info)
    return {"audio": audio, "info": info}


NOTA_DOS_NULLS = ("Os null tiram do endereco as copias que deixaram de servir, juntadas desde a ultima publicacao. "
                  "Antes de publicar, listar os ficheiros do endereco (scope files) e deixar so os null dos que la estao. "
                  "Depois de publicar: py -3.11 scripts/audio_para_mesa.py --publicado")


def escrever_publicar(info):
    """saida/audio/publicar.json: um `files` por lote, pronto para a publicacao com root saida para o endereco da
    Mesa (depois da da pagina e das previas). Os tirados vao com null no primeiro lote, e sao todos os que se
    juntaram desde a ultima publicacao (ver preparar e --publicado)."""
    saida = []
    for k, lote in enumerate(info["lotes"]):
        files = {u: {"from": u, "contentType": TIPOS.get(os.path.splitext(u)[1].lower(), "application/octet-stream")}
                 for u in lote["ficheiros"]}
        x = {"lote": k + 1, "root": "saida", "bytes": lote["bytes"], "n": len(lote["ficheiros"]), "files": files}
        if k == 0 and info["tiradas"]:
            files.update({u: None for u in info["tiradas"]})
            x["nota"] = NOTA_DOS_NULLS
        saida.append(x)
    tmp = PUBLICAR + ".parte"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, PUBLICAR)


def lotes(tamanhos):
    """Os ficheiros em lotes de ate LOTE_MAX, pela ordem do nome: cada lote e uma publicacao com
    `files` e root saida para o mesmo endereco da Mesa (os ficheiros que ficam de fora mantem-se)."""
    saida, atual, peso = [], [], 0
    for u in sorted(tamanhos):
        if atual and (peso + tamanhos[u] > LOTE_MAX or len(atual) >= 250):
            saida.append({"ficheiros": atual, "bytes": peso})
            atual, peso = [], 0
        atual.append(u)
        peso += tamanhos[u]
    if atual:
        saida.append({"ficheiros": atual, "bytes": peso})
    return saida


def regras_do_render():
    """Os numeros do render e do montar que o palco imita, lidos de la (nunca uma copia escrita a mao)."""
    import render
    import montar_da_mesa as M
    return {"alvo": round(render.LEITO_SAIDA_LUFS, 3), "cruzamento": render.CRUZAMENTO,
            "subida_inicio": render.SUBIDA_NUM_INICIO, "tol_frase": render.TOLERANCIA_FIM_DE_FRASE,
            "voz_fade": render.VOZ_FADE, "voz_fade_leito": render.VOZ_FADE_LEITO,
            "fade_fim_som": render.FADE_FIM_SOM, "limite": 0.94,
            "voz_alvo": M.VOZ_ALVO_LUFS, "voz_abaixa_db": M.VOZ_ABAIXA_DB, "voz_pausa": M.VOZ_PAUSA,
            "eco": M.MARCA_ECO_S, "vinheta": M.VINHETA, "vinheta_in": M.VINHETA_IN, "vinheta_dura": M.VINHETA_DURA,
            "rebobinar": M.REBOBINAR, "efeitos": list(render.EFEITOS_SOM), "ext": list(M.EXT_MUSICA),
            "silencio_janela": M.JANELA_SILENCIO}


def chave_da_faixa(ficheiro, quando, entrada):
    """A chave com que a Mesa encontra a faixa no window.SOM_RENDER (f, corpo, in, a duas casas)."""
    return "%s|%.2f|%.2f" % (ficheiro, round(float(quando), 2), round(float(entrada), 2))


def faixas_da_montagem(nome="v3"):
    """{chave: {ganho, subida, sai_s, cauda}} do som.csv: o que o window.SOM_RENDER nao traz e a Mesa
    precisa para tocar cada faixa como o render (o ganho dos foguetes, do rebobinar, das vozes)."""
    saida = {}
    for r in _linhas_csv(os.path.join(MONTAGENS, nome + ".som.csv")):
        try:
            x = {"ganho": float(r.get("ganho") or 1.0)}
            for k in ("subida", "sai_s", "cauda"):
                if str(r.get(k) or "").strip():
                    x[k] = float(str(r[k]).replace(",", "."))
            saida[chave_da_faixa(r["ficheiro"], r["quando_s"], r.get("in_s") or 0)] = x
        except (ValueError, KeyError):
            continue
    return saida


def fins_de_frase():
    """As trocas medidas (decisao 096), com os campos que o montar_da_mesa.escrever_fins_de_frase() usa."""
    saida = []
    for r in _linhas_csv(FINS_DE_FRASE):
        try:
            saida.append({"sai": r["sai"], "entra": r["entra"], "no_corte": float(r["no_corte"]),
                          "entra_in": float(r["entra_in"]), "sai_s": float(r["sai_s"]), "cauda": float(r["cauda"]),
                          "subida_entra": float(r["subida_entra"]) if str(r.get("subida_entra") or "").strip() else None})
        except (ValueError, KeyError):
            continue
    return saida


def entradas_num_ataque():
    """As entradas aprovadas num ataque (095, 097): a musica (o comeco do nome) e o segundo."""
    saida = []
    for r in _linhas_csv(ENTRADAS_ATAQUE):
        try:
            saida.append({"musica": r["musica"], "in_s": float(r["in_s"])})
        except (ValueError, KeyError):
            continue
    return saida


def resumo(p):
    if not p or not p.get("audio"):
        return "sem som (falta o ffmpeg, ou nenhuma musica em disco)"
    i = p["info"]
    lt = i["lotes"]
    return ("%d copias de som e %d videos, %.1f MB (%.1f de som), feito a %s; publica-se em %d %s de ate %.0f MB%s"
            % (len(p["audio"]), sum(len(v) for v in i["videos"].values()), i["bytes"] / MB, i["bytes_som"] / MB,
               i.get("feito") or "?", len(lt), "lote" if len(lt) == 1 else "lotes", LOTE_MAX / MB,
               (", e %d por fazer: %s" % (len(i["sem_copia"]), ", ".join(i["sem_copia"][:3]))) if i["sem_copia"] else ""))


def publicado():
    """Depois de uma publicacao do som: esquece as tiradas que ja foram com null, e reescreve o publicar.json."""
    ind = _ler_indice()
    antes = len(ind.get("por_tirar") or [])
    ind["por_tirar"] = []
    _escrever_indice(ind)
    return antes


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--publicado" in sys.argv:
        print("  esquecidas %d copias tiradas, ja publicadas com null" % publicado())
    p = preparar(com_video="--sem-video" not in sys.argv)
    print(resumo(p))
    for k, lote in enumerate(p["info"]["lotes"]):
        print("  lote %d: %d ficheiros, %.1f MB" % (k + 1, len(lote["ficheiros"]), lote["bytes"] / MB))
    if p["info"]["tiradas"]:
        print("  tirar com null na publicacao: %s" % ", ".join(p["info"]["tiradas"]))
    print("  o mapa `files` de cada lote: %s" % PUBLICAR)
    if p["info"]["grandes"]:
        print("  AVISO: acima de 15 MB: %s" % ", ".join(p["info"]["grandes"]))
