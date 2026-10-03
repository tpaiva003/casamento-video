# -*- coding: utf-8 -*-
"""O que cada letra do render desenha, para o Validar da Mesa avisar como o render (2 de outubro, a noite).

O PEDIDO. O Tiago escolheu que o filme desenhe os emojis a cores (render.texto_emojis). Ate aqui o
Validar da Mesa tinha uma regra positiva para o Arial Bold (VAL_LETRA) e marcava "Esta mal" qualquer
coisa fora dela, emojis incluidos, porque eram caixas vazias no filme. Agora um emoji sai a cores, e o
aviso so vale para o que o render.caracteres_sem_letra() diz: um caracter que nem a letra onde o texto
vai (o Arial Bold ou a do estilo) nem a letra de emojis desenham.

PORQUE E QUE VAI UMA TABELA E NAO UMA REGRA. O browser nao sabe que letras tem o PC do render: no
telemovel nem tem o Arial Bold nem a Segoe UI Emoji. O \\p{Extended_Pictographic} do JavaScript e uma
aproximacao (tem pontos de codigo reservados que nenhuma letra desenha, e nao tem o visto U+2713, que a
Segoe desenha). Por isso a Mesa recebe, medido aqui com os mesmos ficheiros que o render abre e pela
mesma regra (texto_emojis.tem_glifo: falta quando sai igual ao glifo de um nao-caracter):
  - `letras`: para cada letra de data/fontes.json que abre neste PC, os pontos de codigo que ela desenha;
  - `emojis`: os que a letra de emojis desenha e o render pode por a cores (texto_emojis._candidato);
  - `escuros`: os emojis de um so ponto de codigo que saem a cores e quase nao se veem no preto
    (texto_emojis.contraste_no_preto abaixo do CONTRASTE_MINIMO), com o contraste.

OS PONTOS DE CODIGO VEM DO CMAP DE CADA FICHEIRO, e cada um confirma-se com o tem_glifo(): um caracter
fora do cmap sai no glifo de falta (a Pillow nao vai buscar a outra letra), e um dentro dele pode sair
igual ao glifo de falta. Os espacos (str.isspace) contam como desenhados no render, e a Mesa salta-os.

O FORMATO: cada lista e uma cadeia de intervalos em hexadecimal, "20-7e,a0-17f,2013", para a pagina
procurar por bisseccao. Sao uns 12 KB na pagina e 0 ficheiros na publicacao.

Uso:  py -3.11 scripts/caracteres_para_mesa.py      (diz o que mediu, nao escreve nada)
"""
import io
import os
import struct
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)

# O CORPO EM QUE SE MEDE. O que uma letra tem nao muda com o corpo; mede-se no da legenda do render.
CORPO = 46


# ------------------------------------------------------------------ o cmap de um ficheiro de letra
def _tabelas(dados, inicio):
    """{etiqueta: (posicao, comprimento)} das tabelas de uma letra que comeca em `inicio`."""
    n = struct.unpack_from(">H", dados, inicio + 4)[0]
    saida = {}
    for k in range(n):
        etiqueta, _soma, pos, comp = struct.unpack_from(">4sIII", dados, inicio + 12 + 16 * k)
        saida[etiqueta.decode("latin-1")] = (pos, comp)
    return saida


def _formato_4(dados, p):
    segs = struct.unpack_from(">H", dados, p + 6)[0] // 2
    fins = struct.unpack_from(">%dH" % segs, dados, p + 14)
    inis = struct.unpack_from(">%dH" % segs, dados, p + 16 + 2 * segs)
    deltas = struct.unpack_from(">%dh" % segs, dados, p + 16 + 4 * segs)
    pos_ofs = p + 16 + 6 * segs
    ofs = struct.unpack_from(">%dH" % segs, dados, pos_ofs)
    saida = set()
    for k in range(segs):
        for c in range(inis[k], fins[k] + 1):
            if c == 0xFFFF:
                continue
            if ofs[k] == 0:
                g = (c + deltas[k]) & 0xFFFF
            else:
                onde = pos_ofs + 2 * k + ofs[k] + 2 * (c - inis[k])
                g = struct.unpack_from(">H", dados, onde)[0]
                if g:
                    g = (g + deltas[k]) & 0xFFFF
            if g:
                saida.add(c)
    return saida


def _formato_12(dados, p):
    n = struct.unpack_from(">I", dados, p + 12)[0]
    saida = set()
    for k in range(n):
        ini, fim, glifo = struct.unpack_from(">III", dados, p + 16 + 12 * k)
        for c in range(ini, fim + 1):
            if glifo + (c - ini):
                saida.add(c)
    return saida


def cmap(caminho, indice=0):
    """O conjunto dos pontos de codigo que o cmap da letra liga a um glifo que nao e o de falta.

    Le o subtabela Unicode mais larga (3,10 ou 0,4 no formato 12; senao 3,1 ou 0,3 no formato 4). Um
    .ttc le a letra `indice`, como o ImageFont.truetype(index=).
    """
    with io.open(caminho, "rb") as fh:
        dados = fh.read()
    inicio = 0
    if dados[:4] == b"ttcf":
        inicio = struct.unpack_from(">I", dados, 12 + 4 * indice)[0]
    tab = _tabelas(dados, inicio)
    if "cmap" not in tab:
        return set()
    base = tab["cmap"][0]
    n = struct.unpack_from(">H", dados, base + 2)[0]
    subs = {}
    for k in range(n):
        plat, cod, ofs = struct.unpack_from(">HHI", dados, base + 4 + 8 * k)
        fmt = struct.unpack_from(">H", dados, base + ofs)[0]
        subs[(plat, cod, fmt)] = base + ofs
    for chave in ((3, 10, 12), (0, 6, 12), (0, 4, 12), (0, 3, 12)):
        if chave in subs:
            return _formato_12(dados, subs[chave])
    for chave in ((3, 1, 4), (0, 3, 4), (0, 1, 4), (0, 0, 4)):
        if chave in subs:
            return _formato_4(dados, subs[chave])
    return set()


# ------------------------------------------------------------------ as tabelas
def intervalos(pontos):
    """'20-7e,a0-17f,2013': os pontos de codigo, ordenados, em intervalos em hexadecimal."""
    pontos = sorted(set(pontos))
    partes, k = [], 0
    while k < len(pontos):
        j = k
        while j + 1 < len(pontos) and pontos[j + 1] == pontos[j] + 1:
            j += 1
        partes.append("%x" % pontos[k] if j == k else "%x-%x" % (pontos[k], pontos[j]))
        k = j + 1
    return ",".join(partes)


def de_intervalos(texto):
    """O contrario do intervalos(): o conjunto dos pontos de codigo."""
    saida = set()
    for parte in (texto or "").split(","):
        if not parte:
            continue
        a, _, b = parte.partition("-")
        saida.update(range(int(a, 16), int(b or a, 16) + 1))
    return saida


def _caminho_da_letra(f):
    return getattr(f, "path", None) or getattr(getattr(f, "font", None), "path", None)


def desenhados(fonte, caminho=None, indice=0):
    """Os pontos de codigo que a `fonte` (um ImageFont) desenha pela regra do render (tem_glifo)."""
    import texto_emojis
    caminho = caminho or _caminho_da_letra(fonte)
    return {c for c in cmap(caminho, indice) if not chr(c).isspace() and texto_emojis.tem_glifo(fonte, chr(c))}


_MEDIDO = {}


def letras_do_render(com_escuros=True):
    """{letras, emojis, escuros, minimo, sem_emojis, maiuscula, avanco, emoji_pela_maiuscula} para o
    window.LETRAS_RENDER (uns 8 s; guarda-se no processo).

    `maiuscula` e a altura do H de cada letra, e `avanco` quanto avanca cada emoji (milesimas do corpo; os que nao
    sao a `omissao` vao em `outros`, por avanco): com o EMOJI_PELA_MAIUSCULA e o LETREIRO_SS, a Mesa mede um texto dos
    creditos com emojis como o texto_emojis.largura(), e nao com o emoji do browser (1,38 do corpo da letra, contra
    1,26 no render).

    `letras` traz as letras de data/fontes.json que o render.abrir_letra() abre neste PC, mais o
    "arial_bold" (o render.FONTE_TEXTO, que e tambem a letra da fita e dos contadores). Duas entradas no
    mesmo ficheiro (a Cormorant normal e a negrita) tem o mesmo cmap e medem-se uma vez.
    """
    if com_escuros in _MEDIDO:
        return _MEDIDO[com_escuros]
    import render
    import texto_emojis
    from PIL import ImageFont
    letras, por_ficheiro, maiuscula = {}, {}, {}

    def mede(ident, f, f1000):
        chave = (os.path.normcase(os.path.abspath(_caminho_da_letra(f))), getattr(f, "index", 0))
        if chave not in por_ficheiro:
            por_ficheiro[chave] = intervalos(desenhados(f, chave[0], chave[1]))
        letras[ident] = por_ficheiro[chave]
        # a altura das maiusculas, em milesimas do corpo: e por ela que o render escolhe o corpo do emoji
        # (texto_emojis.corpo_do_emoji, o topo do H)
        maiuscula[ident] = round(-f1000.getbbox("H", anchor="ls")[1] / 1000.0, 4)

    mede(render.LETRA_OMISSAO, ImageFont.truetype(render.FONTE_TEXTO, CORPO), ImageFont.truetype(render.FONTE_TEXTO, 1000))
    entradas = render.letras_da_mesa()
    for ident in sorted(entradas):
        if ident == render.LETRA_OMISSAO:
            continue
        f = render.abrir_letra(ident, CORPO, entradas, avisar=False)
        if f is not None:
            mede(ident, f, render.abrir_letra(ident, 1000, entradas, avisar=False))
    fe = texto_emojis.letra_emojis(48)
    if fe is None:
        return {"letras": letras, "emojis": "", "escuros": {}, "minimo": texto_emojis.CONTRASTE_MINIMO,
                "sem_emojis": True, "maiuscula": maiuscula, "avanco": None,
                "emoji_pela_maiuscula": texto_emojis.EMOJI_PELA_MAIUSCULA, "letreiro_ss": render.LETREIRO_SS}
    emojis = sorted(c for c in cmap(texto_emojis.LETRA_EMOJIS)
                    if not chr(c).isspace() and texto_emojis._candidato(chr(c)) and texto_emojis.emoji_desenha(chr(c)))
    # QUANTO AVANCA CADA EMOJI, em milesimas do corpo da letra de emojis, para a Mesa medir os textos dos creditos
    # como o render (texto_emojis.largura): a maioria avanca 1,373 do corpo, e os simbolos de uma so cor outras coisas
    f1000 = ImageFont.truetype(texto_emojis.LETRA_EMOJIS, 1000)
    por_avanco = {}
    for c in emojis:
        por_avanco.setdefault(int(round(f1000.getlength(chr(c)))), []).append(c)
    omissao = max(por_avanco, key=lambda k: len(por_avanco[k]))
    avanco = {"omissao": omissao, "outros": {str(k): intervalos(v) for k, v in sorted(por_avanco.items()) if k != omissao}}
    escuros = {}
    if com_escuros:
        for c in emojis:
            k = texto_emojis.contraste_no_preto(chr(c))
            if k is not None and k < texto_emojis.CONTRASTE_MINIMO:
                # escrito como o render o escreve no aviso (aviso_dos_escuros), para a Mesa dizer o mesmo numero
                escuros["%x" % c] = ("%.1f" % k).replace(".", ",")
    _MEDIDO[com_escuros] = saida = {"letras": letras, "emojis": intervalos(emojis), "escuros": escuros,
                                    "minimo": texto_emojis.CONTRASTE_MINIMO, "sem_emojis": False,
                                    "maiuscula": maiuscula, "avanco": avanco,
                                    "emoji_pela_maiuscula": texto_emojis.EMOJI_PELA_MAIUSCULA,
                                    "letreiro_ss": render.LETREIRO_SS}
    return saida


def resumo(dados):
    if not dados:
        return "sem as letras do render: o Validar usa a regra de reserva"
    import json
    tam = len(json.dumps(dados, separators=(",", ":")))
    return "%d letras, %d emojis, %d escuros (%.1f KB na pagina)%s" % (
        len(dados["letras"]), len(de_intervalos(dados["emojis"])), len(dados["escuros"]), tam / 1024.0,
        ", SEM a letra de emojis neste PC" if dados.get("sem_emojis") else "")


if __name__ == "__main__":
    import time
    sys.stdout.reconfigure(encoding="utf-8")
    t = time.time()
    d = letras_do_render()
    print("medido em %.1f s: %s" % (time.time() - t, resumo(d)))
    for ident, v in sorted(d["letras"].items()):
        print("  %-22s %6d pontos de codigo, %5d bytes" % (ident, len(de_intervalos(v)), len(v)))
