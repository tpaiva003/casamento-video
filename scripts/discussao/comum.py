# -*- coding: utf-8 -*-
"""O que as previas da discussao dos cinco pontos partilham. O estado da discussao, o que o Tiago
disse e o plano de construcao estao em docs/DISCUSSAO.md.

AS PREVIAS NAO MUDAM NADA. Mostram HOJE contra FUTURO sem tocar no render, na montagem nem na Mesa:
o futuro faz-se em memoria, trocando linhas do codigo do render por outras so dentro deste processo
(remendar). Escrevem so em saida/discussao/, que esta no .gitignore.

TUDO SE PROCURA PELO NOME. A musica pelo inicio do nome do ficheiro, o nascimento pela data na fita
(12/09 e 24/11, decisao 088), a foto do bebe por ser a primeira foto depois dessa fita. Nunca pelo
numero do clip nem pelo segundo do corpo: o Tiago ainda pode mudar a ordem do filme, e as previas
tem de voltar a sair certas sem se mexer nelas. Quando uma coisa nao se encontra, o script para e
diz o que procurou, em vez de mostrar outra no lugar dela.

DEPOIS DE UM PONTO ESTAR CONSTRUIDO, o remendo dele falha de proposito (a linha que trocava ja nao
existe no render) e a previa desse ponto deixa de ser precisa: o render ja faz o futuro sozinho.
"""
import inspect
import os
import subprocess
import sys
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
os.chdir(REPO)
import render          # noqa: E402
import linha_tempo     # noqa: E402

FF = render.ffmpeg()
FP = os.path.join(os.path.dirname(FF), "ffprobe.exe")
L, A, FPS = render.L, render.A, render.FPS
ARIALBD = r"C:\Windows\Fonts\arialbd.ttf"
ARIAL = r"C:\Windows\Fonts\arial.ttf"
# A montagem e a pasta de saida podem vir de fora, para experimentar uma copia da montagem sem
# tocar na de verdade (foi assim que se provou que as previas sobrevivem a uma mudanca de ordem):
#   DISCUSSAO_MONTAGEM=nome  DISCUSSAO_MONTAGENS=pasta  DISCUSSAO_SAIDA=pasta
MONTAGEM = os.environ.get("DISCUSSAO_MONTAGEM") or "v3"
if os.environ.get("DISCUSSAO_MONTAGENS"):
    render.MONTAGENS = os.environ["DISCUSSAO_MONTAGENS"]
SAIDA = os.environ.get("DISCUSSAO_SAIDA") or os.path.join(REPO, "saida", "discussao")
NASCIMENTO = {"Tiago": (12, 9), "Clara": (24, 11)}     # o mesmo que montar_da_mesa.NASCIMENTO_NA_FITA


def pasta(ponto):
    p = os.path.join(SAIDA, ponto)
    os.makedirs(p, exist_ok=True)
    return p


def carregar():
    return render.carregar_montagem(MONTAGEM, None)


def entradas_de_som(est):
    return render.som_do_ficheiro(MONTAGEM, est["fim"])


# ---------------------------------------------------------------------------------------------
# REMENDOS EM MEMORIA
# ---------------------------------------------------------------------------------------------

def remendar(funcao, trocas, ponto):
    """A funcao com as linhas trocadas, compilada num espaco de nomes proprio (o modulo fica igual).
    trocas: [(texto de hoje, texto do futuro)], cada texto de hoje tem de aparecer uma so vez."""
    fonte = textwrap.dedent(inspect.getsource(funcao))
    for velho, novo in trocas:
        n = fonte.count(velho)
        if n != 1:
            raise SystemExit(
                "O remendo do %s nao encaixa em %s: a linha\n    %s\naparece %d vezes. Se o %s ja foi "
                "construido, esta previa ja nao e precisa (o render ja faz o futuro); senao, alguem mexeu "
                "nesta funcao e o remendo tem de ser refeito." % (ponto, funcao.__name__, velho, n, ponto))
        fonte = fonte.replace(velho, novo)
    modulo = sys.modules[funcao.__module__]
    ns = dict(modulo.__dict__)
    exec(compile(fonte, modulo.__file__, "exec"), ns)
    return ns[funcao.__name__], ns


# O SOM DO FUTURO (decisao 094, e o que a 095 e a 3.3 precisam): cada faixa pode trazer a sua
# subida, a sua descida e a curva. Sem esses campos, sai igual ao render de hoje. O remendo so se faz
# na primeira vez que e preciso: se a 094 ja estiver construida, param as previas que o usam, e nao
# todas as que importam este modulo.
_FUTURO = []


def CONSTRUIR_FUTURO(ff, entradas, duracao_total, saida, fade_fim=0.0):
    if not _FUTURO:
        _FUTURO.append(_remendo_094())
    return _FUTURO[0](ff, entradas, duracao_total, saida, fade_fim)


def _remendo_094():
    # DEPOIS DE CONSTRUIDA (30 de setembro) o render ja le a subida, a descida e a curva de cada
    # faixa: usa-se o dele, e o remendo so serve para um render de antes da construcao.
    if 'e.get("subida")' in inspect.getsource(render.construir_som):
        return render.construir_som
    f, _ns = remendar(render.construir_som, [
    ('subida = VOZ_FADE if voz else (1.0 if e["quando"] > 0.05 else 0.4)',
     'subida = e.get("subida") or (VOZ_FADE if voz else (1.0 if e["quando"] > 0.05 else 0.4))'),
    ('descida = VOZ_FADE if voz else max(1.0, e.get("cruza", 0.0))',
     'descida = e.get("descida") or (VOZ_FADE if voz else max(1.0, e.get("cruza", 0.0)))'),
    ('"afade=t=in:st=0:d=%.2f,afade=t=out:st=%.3f:d=%.2f,"',
     '"afade=t=in:st=0:d=%.2f:curve=%s,afade=t=out:st=%.3f:d=%.2f:curve=%s,"'),
    ('% (i, norma, subida, max(0.0, e["dura"] - descida), descida,',
     '% (i, norma, subida, e.get("curva", "tri"), max(0.0, e["dura"] - descida), descida, e.get("curva", "tri"),'),
    ], "ponto 3.1 (decisao 094)")
    return f


CONSTRUIR_HOJE = render.construir_som


# ---------------------------------------------------------------------------------------------
# AS MUSICAS, PELO NOME
# ---------------------------------------------------------------------------------------------

# O nome por que o Tiago conhece cada musica, pelo inicio do nome do ficheiro. So para os cartoes das
# previas; uma musica que nao esteja aqui aparece com o nome do ficheiro.
NOMES_DAS_MUSICAS = [
    ("Lang Lang", "Lang Lang"), ("Mariah", "Mariah"), ("O Rei Le", "Rei Leão"), ("Ana Faria", "Ana Faria"),
    ("Gilbert", "Clair"), ("Baha Men", "Who Let The Dogs Out"), ("Tokyo", "Tokyo Drift"),
    ("Tiago Celebration", "Tiago Celebration"), ("Antonio", "O corpo é que paga"), ("Inês", "Fome de Viagem"),
    ("Já Sei", "Já Sei Namorar"), ("Steppenwolf", "Born To Be Wild"), ("Filhos", "Filhos do Dragão"),
    ("Queen", "Queen"), ("Bachman", "Taking Care of Business"),
]


def nome_da_musica(ficheiro):
    for prefixo, nome in NOMES_DAS_MUSICAS:
        if ficheiro.startswith(prefixo):
            return nome
    return os.path.splitext(ficheiro)[0].split(" - ")[0].strip()


def e_efeito(e):
    return e["ficheiro"].startswith(("Candidato", "rebobinar"))


def leitos(ent):
    """As musicas de fundo, por ordem: sem vozes, sem o som dos videos, sem foguetes nem rebobinar."""
    return sorted([e for e in ent if not render.entra_depressa(e) and not e_efeito(e)],
                  key=lambda e: e["quando"])


def faixas(ent, prefixo):
    return [e for e in leitos(ent) if e["ficheiro"].startswith(prefixo)]


def trocas(ent):
    """[(a, b)]: a musica que sai e a que entra, pela ordem do filme. O corte e b["quando"]."""
    ls = leitos(ent)
    return list(zip(ls, ls[1:]))


def troca(ent, sai, entra, obrigatoria=True):
    """A troca de uma musica para outra, pelos inicios dos nomes. Se nao houver uma so, para (ou,
    com obrigatoria=False, avisa e devolve None: a ordem mudou e essas duas ja nao se seguem)."""
    achadas = [(a, b) for a, b in trocas(ent) if a["ficheiro"].startswith(sai) and b["ficheiro"].startswith(entra)]
    if len(achadas) != 1:
        if not obrigatoria:
            print("  AVISO: nao ha uma so troca de '%s' para '%s' (ha %d); fica de fora" % (sai, entra, len(achadas)))
            return None
        raise SystemExit("Procurei a troca de '%s' para '%s' e encontrei %d. Trocas de hoje:\n%s"
                         % (sai, entra, len(achadas), "\n".join(
                             "  %7.2f  %s -> %s" % (b["quando"], a["ficheiro"][:30], b["ficheiro"][:30])
                             for a, b in trocas(ent))))
    return achadas[0]


def nivel_ficheiro(caminho, a, b):
    """dBFS RMS de um bocado de um ficheiro de musica (None se nao ha nada)."""
    if b <= a:
        return None
    r = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % max(0, a), "-t", "%.3f" % (b - max(0, a)),
                        "-i", caminho, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0
    return 20 * np.log10(max(1e-6, float(np.sqrt(np.mean(x * x))))) if len(x) else None


def entra_num_inicio(e):
    """Decisao 094: in no zero, ou quase silencio nos 0,4 s antes do in e som logo a seguir."""
    if e["in_s"] < 0.05:
        return True
    antes = nivel_ficheiro(e["caminho"], e["in_s"] - 0.4, e["in_s"])
    depois = nivel_ficheiro(e["caminho"], e["in_s"], e["in_s"] + 0.4)
    return antes is not None and depois is not None and antes < -40 and depois - antes > 15


def aplicar_094(ent, ataques=()):
    """A regra geral de subida e descida (decisao 094), em memoria. ataques: as faixas cuja entrada
    foi posta num ataque, que contam como inicio (o acrescento da 095)."""
    ls = leitos(ent)
    for e in ls:
        e["curva"] = "qsin"
        if "_subida" in e:
            continue            # a subida que o montar escreveu (um ataque, ou um fim de frase) manda
        anterior = [x for x in ls if x is not e and x.get("cruza")
                    and abs((x["quando"] + x["dura"] - x["cruza"]) - e["quando"]) < 0.35]
        if any(e is x for x in ataques) or entra_num_inicio(e):
            e["subida"] = 0.03
        elif anterior:
            e["subida"] = anterior[0]["cruza"]
    return ent


# Decisao 095. Cada linha escolhe a marca pela musica e pelo ponto de entrada de HOJE: e isso que a
# distingue das outras vezes que a mesma musica toca (o Lang Lang toca tres vezes). Se o Tiago ja
# tiver posto o numero novo, nao ha nada a fazer; se a marca tiver outro numero, avisa-se.
#
# O LANG LANG TOCA TRES VEZES, e ha duas retomas. A MARCADA e a dele, no cartao "Mas como e que
# chegamos aqui?": a 095 poe-na a continuar exatamente onde o primeiro Lang Lang (o da abertura, que e
# automatico: montar_da_mesa.LANG_LANG_IN) parou, por isso o numero novo e uma regra e nao um numero:
# a entrada do primeiro mais o tempo que ele toca ate a musica seguinte (hoje 5,0 + 9,6 = 14,6). Se o
# ponto 3.4 mudar a abertura, o numero muda sozinho. A AUTOMATICA e a da fita antes da Clara, que o
# montar calcula a partir da marcada (entrada dela + o que ela toca, hoje 13,3 + 29,5 = 42,8): anda o
# mesmo que a marcada.
ENTRADAS_095 = [
    # (musica, titulo, entrada de hoje, entrada nova (None = a regra da retoma), entra num ataque)
    ("Inês Homem de Melo", "Fome de Viagem", 0.0, 2.7, True),
    ("Já Sei Namorar", "Já Sei Namorar", 31.16, 34.9, True),
    # a retoma marcada do Lang Lang (13,3 para onde o primeiro parou) saiu com o cartao "Mas como e que
    # chegamos aqui?" na decisao 099: sem o cartao, o Lang Lang da abertura toca direto
    ("Tiago Celebration", "Tiago Celebration", 0.0, 0.81, True),
    ("Bachman", "Taking Care of Business", 62.0, 60.8, False),
    ("Steppenwolf", "Born To Be Wild", 0.0, 0.55, True),
    ("Filhos Do", "Filhos do Dragão", 4.0, 7.0, False),
]


def retoma_nova(ent):
    """Onde o primeiro Lang Lang parou: a entrada dele mais o que toca ate a musica seguinte."""
    ls = leitos(ent)
    primeiro = next((i for i, e in enumerate(ls) if e["ficheiro"].startswith("Lang Lang")), None)
    if primeiro is None or primeiro + 1 >= len(ls):
        return None
    a, b = ls[primeiro], ls[primeiro + 1]
    return round(a["in_s"] + b["quando"] - a["quando"], 3)


def novo_095(ent, linha):
    return linha[3] if linha[3] is not None else retoma_nova(ent)


def marca_095(ent, linha):
    """A faixa de uma linha da 095, ou None (com aviso) se a marca ja nao tem nem o numero de hoje
    nem o novo."""
    prefixo, titulo, hoje, _novo, _ataque = linha
    novo = novo_095(ent, linha)
    if novo is None:
        print("  AVISO 095: nao encontrei o primeiro Lang Lang, sem ele a retoma nao tem numero")
        return None
    fs = faixas(ent, prefixo)
    certas = [e for e in fs if abs(e["in_s"] - hoje) < 0.02 or abs(e["in_s"] - novo) < 0.02]
    if len(certas) != 1:
        print("  AVISO 095: %s nao tem uma so marca a entrar aos %s ou aos %s s (encontrei: %s)"
              % (titulo, hoje, novo, ", ".join("%.2f" % e["in_s"] for e in fs) or "nenhuma"))
        return None
    return certas[0]


def aplicar_095(ent):
    """Os pontos de entrada da 095, em memoria. Devolve as faixas que entram num ataque. Uma retoma
    automatica da mesma musica que comecava onde a marca acabava anda o mesmo que ela."""
    ataques = []
    for linha in ENTRADAS_095:
        e = marca_095(ent, linha)
        if e is None:
            continue
        novo = novo_095(ent, linha)
        acabava = e["in_s"] + e["dura"] - e.get("cruza", 0.0)
        delta = novo - e["in_s"]
        e["in_s"] = novo
        if abs(delta) > 1e-6:
            for x in faixas(ent, linha[0]):
                if x is not e and abs(x["in_s"] - acabava) < 0.05:
                    x["in_s"] += delta
        if linha[4]:
            ataques.append(e)
    return ataques


def ataques_ja_escritos(ent):
    """As marcas da 095 que entram num ataque e que ja tem o numero novo (o Tiago ou a construcao ja
    o escreveram): tambem hoje contam como inicio, senao hoje e futuro soavam diferentes com o mesmo
    numero."""
    out = []
    for linha in ENTRADAS_095:
        if not linha[4]:
            continue
        e = marca_095(ent, linha)
        if e is not None and abs(e["in_s"] - novo_095(ent, linha)) < 0.02:
            out.append(e)
    return out


LANG_LANG_NO_ACORDE = 5.45     # decisao 097: o primeiro acorde do Lang Lang no ficheiro


def abertura_do_corpo(est):
    """(cartao vazio a abrir o corpo, ou None; segundo do corpo em que o primeiro contador comeca)."""
    corpo = est["resto"]
    vazio = (corpo[0] if corpo and corpo[0].get("tipo") == "cartao"
             and not (corpo[0].get("texto_ecra") or "").strip() else None)
    contador = next((c for c in corpo if c.get("tipo") == "contador"), None)
    t_cont = float(contador["inicio_s"]) - est["desvio"] if (vazio and contador) else 0.0
    return vazio, t_cont


def aplicar_097(ent, est):
    """Ponto 3.4 (decisao 097), no som e em memoria. Duas partes, que se aplicam cada uma so se ainda
    nao estiver feita:
    - se o corpo ainda abrir com o cartao vazio, sai o cartao: o corpo passa a comecar no contador e
      tudo anda t_cont segundos para tras (a 29 de setembro o Tiago tirou-o na Mesa, decisao 099);
    - o primeiro Lang Lang, o da abertura (montar_da_mesa.LANG_LANG_IN), entra no acorde, aos 5,45 s
      do ficheiro, e a retoma automatica que o montar calcula a partir dele (a entrada mais o que ele
      toca) anda o mesmo.
    Devolve (entradas, t_cont, o primeiro Lang Lang ou None). Tem de vir ANTES da 095."""
    vazio, t_cont = abertura_do_corpo(est)
    if vazio:
        for e in ent:
            fim = e["quando"] + e["dura"]
            e["quando"] = max(0.0, e["quando"] - t_cont)
            e["dura"] = fim - t_cont - e["quando"]
            if e.get("abafar"):
                e["abafar"] = [(a - t_cont, b - t_cont, f) for a, b, f in e["abafar"]]
        ent = [e for e in ent if e["dura"] > 0.4]
    primeiro = next((e for e in leitos(ent) if e["ficheiro"].startswith("Lang Lang")), None)
    if primeiro is None or primeiro["quando"] >= 0.05:
        return ent, t_cont, None
    delta = LANG_LANG_NO_ACORDE - primeiro["in_s"]
    if abs(delta) > 1e-6:
        acabava = primeiro["in_s"] + primeiro["dura"] - primeiro.get("cruza", 0.0)
        for x in faixas(ent, "Lang Lang"):
            if x is not primeiro and abs(x["in_s"] - acabava) < 0.05:
                x["in_s"] = round(x["in_s"] + delta, 3)      # a retoma automatica anda com ele
        primeiro["in_s"] = LANG_LANG_NO_ACORDE
    return ent, t_cont, primeiro


def base_aprovada(est, com_097=True):
    """O som com tudo o que esta aprovado e ainda nao construido, na ordem certa: 097, 095, 094. O
    fim de frase (096) fica de fora, porque depende de cada troca: ver ponto3_3_frases.py.
    Devolve (entradas, t_cont): t_cont e o que o corpo andou para tras com a 097."""
    ent = entradas_de_som(est)
    t_cont, primeiro = 0.0, None
    if com_097:
        ent, t_cont, primeiro = aplicar_097(ent, est)
    ataques = aplicar_095(ent)
    if primeiro is not None:
        ataques.append(primeiro)          # o acorde do Lang Lang conta como ataque (095, 097)
    aplicar_094(ent, ataques)
    return ent, t_cont


def acabar_na_frase(e, sai_s, cauda):
    """Ponto 3.3: a musica comeca a descer em sai_s (segundos DO FICHEIRO, o fim da frase) e chega a
    zero cauda segundos depois, em vez de descer 2,2 s a partir do corte. Pode acabar antes do corte
    ou um pouco depois dele. Precisa do CONSTRUIR_FUTURO (a descida por faixa)."""
    e["dura"] = max(0.5, float(sai_s) - e["in_s"] + float(cauda))
    e["descida"] = float(cauda)
    e["cruza"] = 0.0
    return e


# ---------------------------------------------------------------------------------------------
# O SOM: EXCERTOS E MEDIDAS
# ---------------------------------------------------------------------------------------------

def excerto(construir, ent, centro, antes, depois, saida):
    """O som do corpo entre centro-antes e centro+depois, feito pela funcao construir."""
    a, b = centro - antes, centro + depois
    janela = [dict(e) for e in ent if e["quando"] < b + 1 and e["quando"] + e["dura"] > a - 1]
    tmp = saida + ".todo.m4a"
    if not construir(FF, janela, b + 1, tmp, 0.0):
        raise SystemExit("o som nao se fez: %s" % saida)
    subprocess.run([FF, "-v", "error", "-y", "-ss", "%.3f" % a, "-t", "%.3f" % (b - a), "-i", tmp,
                    "-c:a", "aac", "-b:a", "192k", saida], check=True)
    os.remove(tmp)
    return saida


def som_do_troco(construir, ent, t0, t1, saida):
    """O som de t0 a t1 do corpo, para ir por baixo de um video de previa."""
    return excerto(construir, ent, t0, 0.0, t1 - t0, saida)


def niveis(caminho, passo=0.1, janela=0.4):
    r = subprocess.run([FF, "-v", "error", "-i", caminho, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True)
    x = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0
    n, h = int(janela * 16000), int(passo * 16000)
    return [(round(i / 16000 + janela / 2, 2), round(20 * np.log10(max(1e-6, float(np.sqrt(np.mean(x[i:i + n] ** 2))))), 1))
            for i in range(0, max(1, len(x) - n), h)]


def duracao(caminho):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


# ---------------------------------------------------------------------------------------------
# OS VIDEOS DAS PREVIAS
# ---------------------------------------------------------------------------------------------

def cartao_titulo(caminho, titulo, rotulo, sub, futuro):
    im = Image.new("RGB", (1280, 720), (12, 12, 14))
    d = ImageDraw.Draw(im)
    corpo = 64
    while corpo > 30 and ImageFont.truetype(ARIALBD, corpo).getlength(titulo) > 1200:
        corpo -= 2                     # um titulo comprido encolhe em vez de sair do cartao
    d.text((640, 250), titulo, font=ImageFont.truetype(ARIALBD, corpo), fill=(240, 240, 240), anchor="mm")
    d.text((640, 380), rotulo, font=ImageFont.truetype(ARIALBD, 64),
           fill=(255, 205, 90) if futuro else (235, 235, 235), anchor="mm")
    d.text((640, 470), sub, font=ImageFont.truetype(ARIAL, 44), fill=(190, 190, 190), anchor="mm")
    im.save(caminho)


def par_em_video(som_hoje, som_futuro, titulo, sub_hoje, sub_futuro, saida):
    """Um video so: o som de hoje com o cartao HOJE, 1,2 s de silencio, e o do futuro com o cartao
    FUTURO. E o formato que o Tiago ouve no telemovel."""
    ca, cd = saida + "_a.png", saida + "_d.png"
    cartao_titulo(ca, titulo, "HOJE", sub_hoje, False)
    cartao_titulo(cd, titulo, "FUTURO", sub_futuro, True)
    da, dd = duracao(som_hoje) + 1.2, duracao(som_futuro)
    subprocess.run([FF, "-v", "error", "-y",
                    "-loop", "1", "-t", "%.3f" % da, "-i", ca, "-i", som_hoje,
                    "-loop", "1", "-t", "%.3f" % dd, "-i", cd, "-i", som_futuro,
                    "-filter_complex",
                    "[1:a]apad=whole_dur=%.3f[a1];[0:v]fps=25,format=yuv420p[v0];[2:v]fps=25,format=yuv420p[v1];"
                    "[v0][a1][v1][3:a]concat=n=2:v=1:a=1[v][s]" % da,
                    "-map", "[v]", "-map", "[s]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], check=True)
    os.remove(ca)
    os.remove(cd)
    return saida


def juntar_videos(videos, saida):
    """Varios videos com a mesma codificacao, seguidos, num so ficheiro."""
    if not videos:
        raise SystemExit("Nao ha nada para juntar: nenhuma troca ou marca foi encontrada na montagem.")
    lista = saida + ".lista.txt"
    with open(lista, "w", encoding="utf-8") as fh:
        for v in videos:
            fh.write("file '%s'\n" % v.replace("\\", "/"))
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy",
                    "-movflags", "+faststart", saida], check=True)
    os.remove(lista)
    return saida


def colar_com_filtro(partes, saida):
    """Videos seguidos num so, sem encadeado, descodificando cada parte sozinha (o filtro concat). Ao
    contrario do juntar_videos, aguenta partes com configuracoes de som diferentes."""
    entradas, filtros = [], []
    for i, p in enumerate(partes):
        entradas += ["-i", p]
        filtros.append("[%d:v]fps=%d,format=yuv420p,setsar=1[v%d];[%d:a]aresample=48000,"
                       "aformat=sample_fmts=fltp:channel_layouts=stereo[a%d]" % (i, FPS, i, i, i))
    filtros.append("".join("[v%d][a%d]" % (i, i) for i in range(len(partes)))
                   + "concat=n=%d:v=1:a=1[v][a]" % len(partes))
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y"] + entradas +
                   ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", saida], check=True)
    return saida


def encoder(saida, dura, som):
    """Um ffmpeg que recebe fotogramas RGB pela entrada e junta o som (que ja comeca no inicio)."""
    return subprocess.Popen(
        [FF, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (L, A), "-r", str(FPS), "-i", "-",
         "-t", "%.3f" % dura, "-i", som,
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", saida],
        stdin=subprocess.PIPE)


# ---------------------------------------------------------------------------------------------
# O LETREIRO (o dos nomes dos bebes, 092 e 093, e o dos separadores novos do ponto 4)
# ---------------------------------------------------------------------------------------------

SS = 2


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _mascara(linhas, tamanho, tracking_em, entrelinha=1.45):
    f = ImageFont.truetype(ARIALBD, tamanho * SS)
    track = tracking_em * tamanho * SS
    larg = [sum(f.getlength(c) for c in ln) + track * (len(ln) - 1) for ln in linhas]
    folga = 160 * SS
    W = int(max(larg)) + 2 * folga
    H = int(tamanho * SS * entrelinha * len(linhas)) + 2 * folga
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    y = folga
    for ln, w in zip(linhas, larg):
        x = (W - w) / 2
        for c in ln:
            d.text((x, y), c, font=f, fill=255)
            x += f.getlength(c) + track
        y += tamanho * SS * entrelinha
    return m


def letreiro(linhas, tamanho=120, tracking_em=0.30, seed=7, entrelinha=1.45):
    """Arial Bold maiusculas espacadas, cor quente a subir para branco, com brilho quente (092)."""
    return colorir(_mascara(linhas, tamanho, tracking_em, entrelinha), seed)


def colorir(m, seed=7):
    """A cor e o brilho do letreiro sobre uma mascara de letras (a SS vezes o tamanho do ecra)."""
    W, H = m.size
    rng = np.random.default_rng(seed)
    baixa = rng.random((5, 16))
    baixa = np.asarray(Image.fromarray((baixa * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                       dtype=np.float32) / 255.0
    grad = np.linspace(1.0, 0.0, H, dtype=np.float32)[:, None]
    v = np.clip(0.5 * baixa + 0.5 * grad, 0, 1)
    quente = np.array([226, 184, 140], np.float32)
    branco = np.array([255, 247, 234], np.float32)
    mk = np.asarray(m, np.float32)[..., None] / 255.0
    cor = (quente + (branco - quente) * v[..., None]) * mk
    q = m.resize((W // 4, H // 4), Image.BILINEAR)
    g1 = np.asarray(q.filter(ImageFilter.GaussianBlur(18 * SS / 4)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255.0
    g2 = np.asarray(q.filter(ImageFilter.GaussianBlur(60 * SS / 4)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255.0
    halo = np.array([255, 150, 70], np.float32) * (0.55 * g1 + 0.30 * g2)
    cor = 255 - (255 - cor) * (1 - halo / 255.0)
    return Image.fromarray(np.clip(cor, 0, 255).astype(np.uint8), "RGB")


def pousar(let, escala, cx=L / 2, cy=A / 2):
    k = escala / SS
    W, H = let.size
    return let.transform((L, A), Image.AFFINE, (1 / k, 0, W / 2 - cx / k, 0, 1 / k, H / 2 - cy / k),
                         resample=Image.BICUBIC, fillcolor=(0, 0, 0))


def ecra(fundo, cima, alfa):
    """Modo ecra, com a camada de cima multiplicada por alfa."""
    a = np.asarray(fundo, np.float32)
    b = np.asarray(cima, np.float32) * alfa
    return Image.fromarray(np.clip(255 - (255 - a) * (255 - b) / 255.0, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------------------------------------
# O NASCIMENTO NA FITA, PELA DATA
# ---------------------------------------------------------------------------------------------

def _fracao(m):
    return ((m[1] - 1) + (m[0] - 1) / 31.0) / 12.0


TIPOS_DE_FOTO = ("foto", "lado", "colagem", "pilha")      # os que o montar_da_mesa conta como fotos


def _marco_do_nascimento(m, quem):
    """O marco grande (asterisco) na data do nascimento ou com o nome, como o _acende do montar (088)."""
    return m[3] and ((m[0], m[1]) == NASCIMENTO[quem] or quem in m[2])


def nascimento(est, quem):
    """A fita onde acende o nascimento, o instante em que acende, o clip de fotos logo a seguir e os
    foguetes. A conta do instante e a do _acende do montar_da_mesa: os passos da fita dentro do troco,
    e o inicio da paragem no marco. Para com uma mensagem clara se a seguir a fita nao vier uma foto
    (ou um grupo de fotos), ou se nao houver uma so explosao nesse instante."""
    clips = est["resto"]
    desvio = est["desvio"]
    for i, c in enumerate(clips):
        if c.get("tipo") != "marcos":
            continue
        texto = c.get("texto_ecra") or ""
        _ano, marcas, troco, abre = linha_tempo.ler_meses(texto)
        dentro = [m for m in marcas if troco[0] - 1e-4 <= _fracao(m) <= troco[1] + 1e-4]
        passos = []
        if not dentro or abs(_fracao(dentro[0]) - troco[0]) > 1e-4:
            passos.append(None)
        passos += dentro
        if not dentro or abs(_fracao(dentro[-1]) - troco[1]) > 1e-4:
            passos.append(None)
        k = next((k for k, m in enumerate(passos) if m and _marco_do_nascimento(m, quem)), None)
        if k is None:
            continue
        ini_fita = float(c["inicio_s"]) - desvio
        anda = float(c["duracao_s"]) - linha_tempo.segura_de(texto)
        acende = ini_fita + linha_tempo.inicio_da_paragem(k, len(passos), 0.70, parar_no_primeiro=abre) * anda
        foto = clips[i + 1] if i + 1 < len(clips) else None
        if foto is None or foto.get("tipo") not in TIPOS_DE_FOTO:
            raise SystemExit(
                "A seguir a fita do nascimento de %s esta %s (clip %s%s). A previa so desenha a fita seguida "
                "de uma foto ou de um grupo de fotos; o montar tambem sabe tratar um cartao ai (089), mas "
                "esta previa nao." % (quem, "nada" if foto is None else "um clip do tipo " + foto.get("tipo", "?"),
                                     "" if foto is None else foto.get("ordem"),
                                     "" if foto is None else ", texto %r" % (foto.get("texto_ecra") or "")[:40]))
        todos = [e for e in entradas_de_som(est) if e["ficheiro"].startswith("Candidato")]
        perto = [e for e in todos if abs(e["quando"] - acende) < 0.3]
        if len(perto) != 1:
            raise SystemExit(
                "O marco do nascimento de %s acende aos %.2f s e devia haver ai uma so explosao; ha %d. "
                "Foguetes na montagem: %s" % (quem, acende, len(perto),
                                               ", ".join("%.2f" % e["quando"] for e in todos) or "nenhuns"))
        return {"fita": c, "foto": foto, "foguetes": perto[0], "ini_fita": ini_fita, "acende": acende,
                "ini_foto": float(foto["inicio_s"]) - desvio}
    raise SystemExit("Nao encontrei na montagem nenhuma fita com o marco grande do nascimento de %s "
                     "(o dia %02d/%02d, ou o nome no marco com asterisco)." % ((quem,) + NASCIMENTO[quem]))


def meses_do_futuro():
    """A fita das decisoes 092 e 093: SO os marcos de nascimento (os grandes) mudam: a frase em
    Arial Bold 66 na cor quente, e a data a 58 px, na mesma cor e 18 px mais abaixo."""
    f, ns = remendar(linha_tempo.meses, [
        ("f_gr = ImageFont.truetype(FONTE, 96)", "f_gr = ImageFont.truetype(FONTE, 66)"),
        ("claro = tuple(int(MARCO_TEXTO[k] * aceso) for k in range(3))",
         "claro = tuple(int((NASC_COR if grande else MARCO_TEXTO)[k] * aceso) for k in range(3))"),
        ("f_data, x, y_linha + 64,",
         "(NASC_DATA if grande else f_data), x, y_linha + (82 if grande else 64),"),
        ("tuple(int(c * aceso) for c in (214, 182, 196)))",
         "tuple(int(c * aceso) for c in (NASC_COR if grande else (214, 182, 196))))"),
    ], "ponto 1 (decisao 092)")
    ns["NASC_COR"] = (236, 204, 168)
    ns["NASC_DATA"] = ImageFont.truetype(linha_tempo.FONTE, 58)
    return f
