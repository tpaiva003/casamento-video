# -*- coding: utf-8 -*-
"""Os emojis a cores e os sinais equivalentes, em todos os textos que o filme desenha (2 de outubro).

O PEDIDO, do Tiago a 2 de outubro: "Prefiro que faca o render de emojis se incluirmos." Ate aqui um
emoji saia como uma caixa vazia, porque o Arial Bold nao o tem e a Pillow desenha o glifo de falta sem
se queixar: na v3 ha um, no fim de "E porque nao ganhar uns EUR como modelo?" (clip 72, f0108).

UMA MANEIRA SO DE MEDIR E DE DESENHAR. O texto parte-se em pedacos de letra e pedacos de emoji. Os de
letra vao na letra de sempre; os de emoji na letra de emojis do Windows (Segoe UI Emoji), a cores
(embedded_color), na mesma linha de base e num corpo que bate com as maiusculas: o da amostra aprovada
desta tarde, o emoji a 42 para a letra 46 do Arial Bold, que tem as maiusculas com 33 px. A largura do
conjunto e a soma das larguras, e e com ela que se centra e se partem as linhas. Usam isto a legenda de
baixo, a legenda de cada foto dos grupos, os textos dentro das fotos, os cartoes e os nomes (o letreiro),
o nome do destaque, a fita e os contadores, e os creditos.

SEM EMOJIS NEM SINAIS EQUIVALENTES, NADA MUDA. Cada funcao daqui ve primeiro se o texto precisa: um
texto so com caracteres que a letra tem segue pela chamada de sempre, ao byte. Um caracter vai para a
letra de emojis so se a letra dele nao o tem (e ai saia uma caixa) ou se o texto pede o emoji com o
seletor U+FE0F. O coracao U+2665 que o Arial Bold tem continua a sair do Arial, como sempre.

OS EQUIVALENTES (render.EQUIVALENTES, 2 de outubro, nos creditos) valem agora em todo o lado: o hifen
U+2010 e o nao separavel U+2011 saem como o hifen de sempre, e os invisiveis U+2060, U+FEFF e U+200B
tiram-se.

O QUE A PILLOW DESTE PC NAO SABE JUNTAR. Sem a biblioteca raqm a Pillow desenha caracter a caracter e
nao junta as sequencias que fazem um emoji so. Medido a 2 de outubro com a Segoe UI Emoji:
  - o tom de pele (U+1F3FB a U+1F3FF) sai num quadrado da cor da pele ao lado do emoji amarelo;
  - as sequencias com o ZWJ (U+200D, a familia, a bandeira do arco-iris, a corredora) saem com as
    figuras separadas, lado a lado; o ZWJ, que a letra de emojis desenha como um risco, tira-se;
  - uma bandeira (dois indicadores regionais) sai como as duas letras do pais, pequenas ("PT");
  - uma tecla (o algarismo, U+FE0F e U+20E3) sai com o algarismo e um quadrado vazio;
  - uma bandeira de regiao (a preta com etiquetas, como a de Inglaterra) sai so preta.
Os seletores U+FE0E e U+FE0F tiram-se (a letra de emojis desenha o U+FE0F como um espaco do tamanho de
um emoji). Isto nao se inventa: avisa-se, no montar, no ponto5 e no guia do DaVinci (sequencias()).

OS SIMBOLOS DE UMA SO COR (corretor, 2 de outubro a noite). A letra de emojis tem 419 glifos sem cores
proprias (o visto U+2713, o quadrado U+2610, as setas, os indicadores das bandeiras), que se desenham
com a cor de quem escreve. Iam na camada dos emojis desenhados a branco: no letreiro saiam brancos e
nao champanhe (098), e na fita brancos enquanto o marco acendia, a saltar para a cor do texto no
ultimo passo. Agora vao como as letras: na cor do texto (escrever) e na mascara do letreiro
(render._pecas_do_letreiro). E so_uma_cor() que os conhece; os emojis a cores nao mudam.

OS EMOJIS ESCUROS AVISAM-SE (corretor, 2 de outubro a noite). Um emoji fica com as cores dele, e os
escuros quase desaparecem no preto: a nota U+1F3B5 da 1,6:1, contra 12,6:1 das letras dos creditos. O
contraste mede-se contra o preto pela luminancia media dos pixeis do emoji (contraste_no_preto), e
abaixo de CONTRASTE_MINIMO (3:1, o dos graficos) o montar e o ponto5 avisam. Nao muda nada.
"""
import math
import unicodedata

from PIL import Image, ImageDraw, ImageFont

LETRA_EMOJIS = r"C:\Windows\Fonts\seguiemj.ttf"
# O CORPO DO EMOJI SAI DAS MAIUSCULAS DA LETRA: a amostra aprovada tem o emoji a 42 para a letra 46 do
# Arial Bold, cujas maiusculas medem 33 px. O emoji fica um pouco mais alto do que as maiusculas, centrado
# nelas (37 px acima da linha de base e 5 abaixo, contra 33 e 0), que e como se le como uma letra.
EMOJI_PELA_MAIUSCULA = 42 / 33.0
# Um nao-caracter, que nenhuma letra pode ter: o que sai dele e o glifo de falta.
NAO_CARACTER = "\uffff"
# OS QUE TEM UM IGUAL A VISTA: o hifen nao separavel e o hifen U+2010 desenham-se como o hifen de
# sempre, que e o que se ve na Mesa; os invisiveis tiram-se.
EQUIVALENTES = {"\u2010": "-", "\u2011": "-", "\u2060": "", "\ufeff": "", "\u200b": ""}
TEXTO, EMOJI = "\ufe0e", "\ufe0f"      # os seletores de apresentacao
ZWJ = "\u200d"
TECLA = "\u20e3"


def tom_de_pele(c):
    return 0x1F3FB <= ord(c) <= 0x1F3FF


def indicador(c):
    return 0x1F1E6 <= ord(c) <= 0x1F1FF


def etiqueta(c):
    return 0xE0020 <= ord(c) <= 0xE007F


def ignoravel(c):
    """Os que nao se desenham: os seletores de apresentacao, o ZWJ e as etiquetas das bandeiras."""
    return c == TEXTO or c == EMOJI or c == ZWJ or etiqueta(c)


def com_equivalentes(texto):
    """O texto com os EQUIVALENTES trocados: o mesmo texto quando nao tem nenhum."""
    if not texto or not any(c in texto for c in EQUIVALENTES):
        return texto
    return "".join(EQUIVALENTES.get(c, c) for c in texto)


def nome_do_caracter(c):
    """'U+2011 (NON-BREAKING HYPHEN)': para os avisos, que um caracter invisivel nao se le."""
    return "U+%04X%s" % (ord(c), (" (%s)" % unicodedata.name(c)) if unicodedata.name(c, "") else "")


# ------------------------------------------------------------------ que letra tem que caracter
_TEM = {}
_CORPOS = {}
_EMOJIS = {}


def _chave(fonte):
    return (getattr(fonte, "path", None) or id(fonte), getattr(fonte, "index", 0), getattr(fonte, "size", 0))


def tem_glifo(fonte, c):
    """Se a `fonte` (um ImageFont) desenha o caracter c, e nao o glifo de falta.

    A regra e a do caracteres_sem_letra() de 2 de outubro: falta quando sai igual, ao pixel e no
    avanco, ao de um nao-caracter. Os espacos contam como desenhados. Guarda-se por ficheiro, indice e
    corpo, e as duas medidas fazem-se sempre com o mesmo objeto (numa letra variavel o peso muda o
    desenho, nao o que ela tem).
    """
    if c.isspace():
        return True
    chave = (_chave(fonte), c)
    v = _TEM.get(chave)
    if v is None:
        falta = fonte.getmask(NAO_CARACTER)
        falta = (falta.size, bytes(falta), fonte.getlength(NAO_CARACTER))
        m = fonte.getmask(c)
        v = _TEM[chave] = (m.size, bytes(m), fonte.getlength(c)) != falta
    return v


def letra_emojis(corpo):
    """A letra de emojis no corpo pedido, ou None se este PC nao a tem."""
    corpo = max(1, int(corpo))
    f = _EMOJIS.get(corpo, False)
    if f is False:
        try:
            f = ImageFont.truetype(LETRA_EMOJIS, corpo)
        except OSError:
            f = None
        _EMOJIS[corpo] = f
    return f


def emoji_desenha(c):
    """Se a letra de emojis tem o caracter c."""
    f = letra_emojis(48)
    return f is not None and tem_glifo(f, c)


def corpo_do_emoji(fonte):
    """O corpo da letra de emojis ao lado da `fonte`: pela altura das maiusculas, EMOJI_PELA_MAIUSCULA."""
    k = _chave(fonte)
    v = _CORPOS.get(k)
    if v is None:
        topo = -fonte.getbbox("H", anchor="ls")[1]
        if topo <= 0:
            topo = 0.716 * getattr(fonte, "size", 46)
        v = _CORPOS[k] = max(1, int(math.floor(topo * EMOJI_PELA_MAIUSCULA + 0.5)))
    return v


def emojis_para(fonte):
    """A letra de emojis que vai ao lado da `fonte`."""
    return letra_emojis(corpo_do_emoji(fonte))


def _candidato(c):
    """Se c pode ser um emoji: os simbolos (So, Sk) e tudo a partir de U+2000. As letras nunca."""
    o = ord(c)
    return o >= 0x2000 or (o >= 0xA0 and unicodedata.category(c) in ("So", "Sk"))


def a_cores(c, seguinte, fonte):
    """Se o caracter c (seguido de `seguinte`) vai a cores, na letra de emojis.

    Vai se a letra dele nao o tem e a de emojis tem (sem isto saia uma caixa), ou se o texto o pede
    com o U+FE0F a seguir. Com o U+FE0E a seguir (o pedido do desenho de texto) fica na letra, se ela
    o tem.
    """
    if ord(c) < 0xA0 or c.isspace() or ignoravel(c) or not _candidato(c):
        return False
    if tem_glifo(fonte, c):
        return seguinte == EMOJI and emoji_desenha(c)
    return emoji_desenha(c)


# ------------------------------------------------------------------ o texto em pedacos
def pedacos(texto, fonte):
    """[(pedaco, a_cores)] do texto, ou None se ele se desenha todo na letra, como sempre.

    Os equivalentes ja vem trocados (com_equivalentes). Um pedaco a cores e um emoji com o que o
    acompanha: o tom de pele, a tecla, o segundo indicador de uma bandeira e o que se junta pelo ZWJ;
    os seletores, o ZWJ e as etiquetas nao se desenham. Os caracteres que nenhuma das duas letras
    tem ficam nos pedacos de letra, como hoje (caixa vazia), e avisa-se (sem_letra).
    """
    if not texto or texto.isascii():
        return None
    saida, letras, mudou = [], [], False
    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if ignoravel(c):
            mudou = True
            i += 1
            continue
        seguinte = texto[i + 1] if i + 1 < n else ""
        if not a_cores(c, seguinte, fonte):
            letras.append(c)
            i += 1
            continue
        mudou = True
        if letras:
            saida.append(("".join(letras), False))
            letras = []
        grupo = [c]
        i += 1
        if indicador(c) and i < n and indicador(texto[i]):
            grupo.append(texto[i])
            i += 1
        while i < n:
            d = texto[i]
            if d == TEXTO or d == EMOJI or etiqueta(d):
                i += 1
            elif tom_de_pele(d) or d == TECLA:
                grupo.append(d)
                i += 1
            elif d == ZWJ and i + 1 < n and not texto[i + 1].isspace():
                grupo.append(texto[i + 1])
                i += 2
            else:
                break
        saida.append(("".join(grupo), True))
    if not mudou:
        return None
    if letras:
        saida.append(("".join(letras), False))
    return saida


def _so_letra(t, fonte):
    """(texto, None) quando o texto vai todo na letra (ja sem os ignoraveis), ou (texto, pedacos)."""
    p = pedacos(t, fonte)
    if p is None:
        return t, None
    if not any(cores for _x, cores in p):
        return "".join(x for x, _c in p), None
    return t, p


def simples(texto, fonte):
    """Se o texto se desenha com a chamada de sempre, sem trocar nada: sem equivalentes nem emojis."""
    return com_equivalentes(texto) == texto and pedacos(texto, fonte) is None


def _disposicao(p, fonte):
    """[(x, pedaco, letra, a_cores)] a partir de x = 0, e a largura do conjunto (a soma dos avancos)."""
    fe = emojis_para(fonte)
    x, saida = 0.0, []
    for t, cores in p:
        f = fe if cores else fonte
        saida.append((x, t, f, cores))
        x += f.getlength(t)
    return saida, x


def desce(fonte, v):
    """Quanto a linha de base fica abaixo do ponto de ancoragem, com a ancora vertical v da Pillow.

    As ancoras a, m, s e d da Pillow sao de metricas da letra; mede-se com a propria Pillow, pelo topo
    de um H com a ancora pedida e com a da linha de base.
    """
    if v == "s":
        return 0.0
    return float(fonte.getbbox("H", anchor="l" + v)[1] - fonte.getbbox("H", anchor="ls")[1])


def _ancora(anchor):
    a = anchor or "la"
    if a[0] not in "lmr" or a[1] not in "amsd":
        raise ValueError("ancora %r nao suportada com emojis" % (anchor,))
    return a[0], a[1]


def largura(texto, fonte):
    """O avanco do texto, como fonte.getlength(texto), com os emojis e os equivalentes."""
    t, p = _so_letra(com_equivalentes(texto or ""), fonte)
    if p is None:
        return fonte.getlength(t)
    return _disposicao(p, fonte)[1]


def caixa(texto, fonte, anchor=None, desenho=None):
    """A caixa da tinta do texto posto em (0, 0), como desenho.textbbox() ou fonte.getbbox().

    Sem emojis e a chamada de sempre (a do `desenho`, se vier). Com eles, a uniao das caixas dos
    pedacos, cada um na sua letra, na mesma linha de base.
    """
    t, p = _so_letra(com_equivalentes(texto or ""), fonte)
    if p is None:
        if desenho is not None:
            return desenho.textbbox((0, 0), t, font=fonte, anchor=anchor)
        return fonte.getbbox(t, anchor=anchor)
    h, v = _ancora(anchor)
    pos, W = _disposicao(p, fonte)
    dx = {"l": 0.0, "m": -W / 2.0, "r": -W}[h]
    base = desce(fonte, v)
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for x, t, f, _cores in pos:
        b = f.getbbox(t, anchor="ls")
        x0, y0 = min(x0, x + dx + b[0]), min(y0, base + b[1])
        x1, y1 = max(x1, x + dx + b[2]), max(y1, base + b[3])
    return (x0, y0, x1, y1)


def escrever(desenho, xy, texto, fonte, fill, anchor=None, alfa=1.0):
    """Escreve o texto como desenho.text(xy, texto, font=fonte, fill=fill, anchor=anchor).

    Sem emojis e essa chamada, ao byte (com os equivalentes trocados, se os houver). Com eles, cada
    pedaco na sua letra, na mesma linha de base; os emojis com as cores deles e nao com o `fill`. O
    `alfa` e o de quem acende o texto pela cor (a fita, que escurece a cor das letras): o emoji
    desvanece com ele por cima do que la esta. A imagem do `desenho` tem de ser RGB ou RGBA quando
    ha emojis.
    """
    t, p = _so_letra(com_equivalentes(texto or ""), fonte)
    if p is None:
        desenho.text(xy, t, font=fonte, fill=fill, anchor=anchor)
        return
    h, v = _ancora(anchor)
    pos, W = _disposicao(p, fonte)
    x = xy[0] + {"l": 0.0, "m": -W / 2.0, "r": -W}[h]
    y = xy[1] + desce(fonte, v)
    for dx, t, f, cores in pos:
        if not cores:
            desenho.text((x + dx, y), t, font=f, fill=fill, anchor="ls")
        elif alfa >= 1.0 or so_uma_cor(t):
            # um simbolo de uma so cor vai na cor de quem escreve, como as letras, tambem a acender
            # (a fita escurece o `fill`): a camada de cores desenhava-o a branco
            desenho.text((x + dx, y), t, font=f, fill=fill, anchor="ls", embedded_color=True)
        else:
            _emoji_esbatido(desenho, x + dx, y, t, f, alfa)


def emoji_rgba(t, f, x, base):
    """(imagem RGBA, (ix, iy)): o emoji t desenhado com a origem em (x, base), em alfa direto.

    A Pillow desenha o emoji a cores colando a cor com a mascara; numa tela transparente isso da a
    cor ja multiplicada pelo alfa, e por isso le-se como RGBa e passa-se a RGBA.
    """
    b = f.getbbox(t, anchor="ls")
    ix, iy = int(math.floor(x + b[0])) - 1, int(math.floor(base + b[1])) - 1
    w, h = int(math.ceil(x + b[2])) + 2 - ix, int(math.ceil(base + b[3])) + 2 - iy
    tela = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    ImageDraw.Draw(tela).text((x - ix, base - iy), t, font=f, fill=(255, 255, 255, 255), anchor="ls",
                              embedded_color=True)
    return Image.frombytes("RGBa", tela.size, tela.tobytes()).convert("RGBA"), (ix, iy)


def _emoji_esbatido(desenho, x, base, t, f, alfa):
    if alfa <= 0.0:
        return
    im, (ix, iy) = emoji_rgba(t, f, x, base)
    mascara = im.getchannel("A").point([int(v * alfa + 0.5) for v in range(256)])
    alvo = desenho.im.mode
    cor = im.convert("RGB") if alvo == "RGB" else im
    if alvo == "RGBA":
        cor = im.copy()
        cor.putalpha(255)
    desenho.im.paste(cor.im, (ix, iy, ix + im.width, iy + im.height), mascara.im)


_UMA_COR = {}
_CONTRASTE = {}


def so_uma_cor(t):
    """Se o emoji t (um pedaco a cores) e um simbolo de uma so cor, que a letra de emojis desenha com a
    cor de quem escreve: o visto U+2713, o quadrado U+2610, as setas, os indicadores das bandeiras.

    Mede-se desenhando-o com duas cores: um emoji a cores sai igual com as duas. Na Segoe UI Emoji de
    2 de outubro ha 419 destes e nenhum misto (com cores proprias e partes na cor de quem escreve).
    """
    v = _UMA_COR.get(t)
    if v is None:
        f = letra_emojis(48)
        if f is None:
            v = False
        else:
            a = emoji_rgba_com(t, f, (255, 0, 0, 255))
            b = emoji_rgba_com(t, f, (0, 0, 255, 255))
            v = a.tobytes() != b.tobytes()
        _UMA_COR[t] = v
    return v


def emoji_rgba_com(t, f, fill):
    """O emoji t desenhado com o `fill` numa tela transparente a medida, em alfa direto (RGBA)."""
    b = f.getbbox(t, anchor="ls")
    w, h = int(math.ceil(b[2] - b[0])) + 4, int(math.ceil(b[3] - b[1])) + 4
    tela = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    ImageDraw.Draw(tela).text((2 - b[0], 2 - b[1]), t, font=f, fill=fill, anchor="ls", embedded_color=True)
    return Image.frombytes("RGBa", tela.size, tela.tobytes()).convert("RGBA")


# O contraste minimo de um emoji contra o preto, o dos graficos (WCAG 1.4.11, 3:1). As letras do filme
# tem mais de 12:1. Medido a 2 de outubro: a nota U+1F3B5 da 1,6, o coracao preto 1,7, a cartola 2,2, o
# chapeu de formatura 2,8; o coracao azul 4,1, o anel 9,7 e a cara do clip 72 11,7.
CONTRASTE_MINIMO = 3.0


def contraste_no_preto(t):
    """O contraste do emoji t contra o preto, (L + 0,05) / 0,05, com L a luminancia relativa media dos
    pixeis dele (os de alfa acima de meio), ou None para um simbolo de uma so cor (vai na cor do texto)."""
    v = _CONTRASTE.get(t, False)
    if v is False:
        f = letra_emojis(48)
        if f is None or so_uma_cor(t):
            v = None
        else:
            import numpy as np
            a = np.asarray(emoji_rgba_com(t, f, (255, 255, 255, 255)), np.float64)
            dentro = a[..., 3] > 127
            if not dentro.any():
                v = None
            else:
                c = a[..., :3][dentro] / 255.0
                c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
                lum = float((0.2126 * c[:, 0] + 0.7152 * c[:, 1] + 0.0722 * c[:, 2]).mean())
                v = (lum + 0.05) / 0.05
        _CONTRASTE[t] = v
    return v


def emojis_escuros(texto, fonte):
    """[(emoji, contraste)] dos emojis do texto que quase nao se veem no preto (abaixo de CONTRASTE_MINIMO),
    pela ordem e sem repetir. Os simbolos de uma so cor vao na cor do texto e nao contam."""
    saida = []
    for e in emojis_do_texto(texto, fonte):
        k = contraste_no_preto(e)
        if k is not None and k < CONTRASTE_MINIMO:
            saida.append((e, k))
    return saida


def aviso_dos_escuros(onde, texto, fonte):
    """[aviso] dos emojis escuros do texto (emojis_escuros), com `onde` como em avisos_do_texto()."""
    return ["%s tem o emoji %s, escuro: sobre o fundo escuro quase nao se ve (contraste %s:1 contra o "
            "preto, e o minimo e %d:1); troca-o por um emoji claro"
            % (onde, codigos(e), ("%.1f" % k).replace(".", ","), int(CONTRASTE_MINIMO))
            for e, k in emojis_escuros(texto, fonte)]


# ------------------------------------------------------------------ o letreiro, letra a letra
def unidades(texto, fonte):
    """O texto em unidades do letreiro, que vai letra a letra com espaco entre elas: [(unidade, a_cores)].

    Cada emoji, com o que o acompanha, e uma unidade so; as letras sao uma cada.
    """
    t, p = _so_letra(com_equivalentes(texto or ""), fonte)
    if p is None:
        return [(c, False) for c in t]
    saida = []
    for x, cores in p:
        if cores:
            saida.append((x, True))
        else:
            saida.extend((c, False) for c in x)
    return saida


def largura_das_unidades(texto, fonte, passo):
    """A largura do texto no letreiro: as unidades e um `passo` entre cada duas."""
    if simples(texto, fonte):
        return sum(fonte.getlength(c) for c in texto) + passo * (len(texto) - 1)
    us = unidades(texto, fonte)
    fe = emojis_para(fonte)
    return sum((fe if cores else fonte).getlength(u) for u, cores in us) + passo * (len(us) - 1)


# ------------------------------------------------------------------ o que avisar
def sem_letra(texto, fonte):
    """Os caracteres do texto que nem a `fonte` nem a letra de emojis desenham: no filme, caixas vazias.

    Pela ordem e sem repetir. Os espacos, os EQUIVALENTES (saem como o seu igual) e os ignoraveis (os
    seletores, o ZWJ, as etiquetas: nao se desenham) nao contam.
    """
    if not texto:
        return []
    vistos, fora = set(), []
    for c in str(texto):
        if c in vistos or c.isspace():
            continue
        vistos.add(c)
        if c in EQUIVALENTES or ignoravel(c) or tem_glifo(fonte, c):
            continue
        if _candidato(c) and emoji_desenha(c):
            continue
        fora.append(c)
    return fora


def emojis_do_texto(texto, fonte):
    """Os emojis que o texto leva a cores, pela ordem e sem repetir."""
    t, p = _so_letra(com_equivalentes(texto or ""), fonte)
    vistos = []
    for x, cores in (p or []):
        if cores and x not in vistos:
            vistos.append(x)
    return vistos


def sequencias(texto):
    """[(sequencia, o que sai)]: os emojis de varios caracteres que a Pillow sem o raqm nao junta.

    O que sai foi medido a 2 de outubro com a Segoe UI Emoji (ver o comentario do principio).
    """
    if not texto or texto.isascii():
        return []
    saida, vistos = [], set()
    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        j, partes = i + 1, set()
        if indicador(c) and j < n and indicador(texto[j]):
            partes.add("bandeira")
            j += 1
        while j < n:
            d = texto[j]
            if d == TEXTO or d == EMOJI:
                j += 1
            elif tom_de_pele(d):
                partes.add("tom")
                j += 1
            elif d == TECLA:
                partes.add("tecla")
                j += 1
            elif etiqueta(d):
                partes.add("regiao")
                j += 1
            elif d == ZWJ and j + 1 < n and not texto[j + 1].isspace():
                partes.add("zwj")
                j += 2
            else:
                break
        if partes:
            seq = texto[i:j]
            if seq not in vistos:
                vistos.add(seq)
                saida.append((seq, "; ".join(SAI[p] for p in ORDEM_DAS_PARTES if p in partes)))
        i = j
    return saida


ORDEM_DAS_PARTES = ("zwj", "tom", "bandeira", "tecla", "regiao")
SAI = {"zwj": "as figuras saem separadas, lado a lado",
       "tom": "o tom de pele sai num quadrado da cor da pele ao lado do emoji amarelo",
       "bandeira": "a bandeira sai como as duas letras do pais, pequenas",
       "tecla": "a tecla sai como o algarismo e um quadrado vazio",
       "regiao": "a bandeira da regiao sai so preta"}


def codigos(seq):
    """'U+1F44D U+1F3FD': uma sequencia pelos codigos, que nos avisos o emoji pode nao se ler."""
    return " ".join("U+%04X" % ord(c) for c in seq)


def avisos_do_texto(onde, texto, fonte):
    """[aviso] dos caracteres de um texto: o que sai numa caixa vazia, as sequencias sem o raqm, e os
    emojis escuros, que quase nao se veem no preto (aviso_dos_escuros, corretor de 2 de outubro).

    `onde` diz de que texto se fala ("o texto do clip 72", "o cargo 2"). Nao muda nada.
    """
    avisos = []
    fora = sem_letra(texto, fonte)
    if fora:
        avisos.append("%s tem %s, que nem a letra nem a de emojis tem: no filme sai uma caixa vazia"
                      % (onde, " e ".join(nome_do_caracter(c) for c in fora)))
    for seq, sai in sequencias(texto):
        avisos.append("%s tem o emoji %s, que esta Pillow nao junta (falta-lhe o raqm): %s; troca-o por "
                      "um emoji simples" % (onde, codigos(seq), sai))
    avisos.extend(aviso_dos_escuros(onde, texto, fonte))
    return avisos
