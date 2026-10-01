# -*- coding: utf-8 -*-
"""Previa do mergulho em mais do que uma foto (decisao 102: "escolher como mergulha em mais do que
uma, a partir de previas"). As quatro maneiras, com as mesmas 20 fotos e tres mergulhos em cada, para
o Tiago escolher. Nao muda nada; escreve so em saida/discussao/mergulho/.

    py -3.11 scripts/discussao/previa_mergulho_varias.py [--quadros | --so-dizer]

Sem opcoes faz os quatro videos em separado, um video so com as quatro (1280x720, 25 fps, com
silencio, abaixo de 25 MB), a folha com 6 fotogramas de cada maneira e as medidas
(medidas_mergulho_varias.json). --quadros so tira os fotogramas (a folha e cada um em quadros/), para
rever depressa; --so-dizer so faz as contas da camara, sem abrir fotos.

AS QUATRO MANEIRAS (medidas a 1 de outubro, saida/discussao/propostas_1001/propostas_1001.txt):
  A  mergulha e volta: a camara mergulha numa foto, fica, volta a grelha inteira, a grelha fica
     ESPERA_ENTRE s e a camara mergulha na seguinte; acaba na ultima, que fica como hoje.
  B  passeia de perto: mergulha na primeira e, ja com ela a encher o ecra, desliza de lado ate a
     vizinha, fica, e assim ate a ultima. So entre vizinhas: as ultimas da fila de baixo.
  C  voo entre fotos: de uma foto a encher o ecra, a camara recua so o preciso para se verem as duas,
     anda e mergulha na seguinte, num so movimento. Perto da borda (a 20.a, no canto) o movimento
     de van Wijk sairia da grelha, e o voo e recuar e mergulhar, sem sair dela (voo_entre).
  D  sem codigo novo: tres grupos em mergulho seguidos (7, 7 e 6 fotos), cada um a acabar na sua
     ultima, com o encadeado normal de 0,7 s entre eles. E o render de hoje, tal e qual.

OS TEMPOS SAO OS DE HOJE: a grelha enche e respira como no render (mergulho_tempos), o mergulho dura
conforme o zoom (mergulho_desce, 1,74 s com 20), cada foto fica MERGULHO_FICA (0,8 s) e entre dois
mergulhos do A a grelha fica ESPERA_ENTRE (0,6 s). A volta do A e o mergulho ao contrario, com o mesmo
tempo. O DESLIZE DO B E O VOO DO C ANDAM A VELOCIDADE DO MERGULHO DE HOJE: duram o preciso para o
deslocamento medio do ecra por fotograma nunca passar do do mergulho que o render faz hoje nesta
grelha, o da ultima foto (fluxo(); 64 px por fotograma no pico, com 20). Um mergulho numa foto do meio
da grelha anda menos, 40 px, porque o centro do zoom fica perto do centro do ecra. Com o 1,0 s da
proposta o deslize andava 119 px por fotograma, quase o dobro do mergulho.
Cada clip conta com o encadeado normal de 0,7 s a entrar e a sair, como no filme: a primeira foto
espera 0,35 s, e no fim a ultima segura-se 0,7 s, que aqui se desfazem a preto.

O QUE E DO RENDER E O QUE E DAQUI. A grelha (mergulho_grelha), os tempos (mergulho_tempos,
mergulho_desce), os sprites (o preparar_mergulho, e a mesma conta para as outras fotos marcadas), a
composicao de sub-pixel (compor, com sprites de com_margem) e a camara por vistas presa a grelha
(mergulho_trocos e mergulho_vista_*) sao os do render, chamados e nunca copiados. Daqui sao so o
caminho da camara depois do primeiro mergulho e os sprites que cada troco compoe (o render compoe um;
o deslize e o voo compoem os dois). O script prova-o antes de desenhar: o sprite feito aqui e o do
render sao iguais ao byte, e um fotograma do D desenhado aqui e o do render.desenhar_mergulho tambem.

A FOTO QUE ENCHE O ECRA E SEMPRE O SPRITE DELA (decisao 090): o ficheiro que o data/finais.csv
escolhe, reduzido em Lanczos ao tamanho com que acaba o mergulho, e nunca uma celula esticada. As
vizinhas vem da grelha desenhada ao dobro (MERGULHO_DOBRO): acima da escala 2 saem esticadas, e
isso mede-se.

A CAMARA NUNCA MOSTRA NADA FORA DA GRELHA. No A, no B e no D cada vista e a mistura de duas vistas
dentro da grelha, com o mesmo peso na posicao e no tamanho, e fica dentro dela (a nota "A CAMARA
PRESA A GRELHA" do render). O voo do C e o caminho de van Wijk e Nuij so quando ele cabe na grelha;
quando sairia dela, sao dois trocos do render, recuar e mergulhar, e nenhuma vista e presa a meio
do movimento (prender uma vista dava um solavanco, ver voo_entre). Em todos, o que caisse fora da
grelha desenha-se na cor SENTINELA e conta-se em cada fotograma: tem de dar zero.

Se o render mudar (um destes nomes trocado, outros argumentos, ou outra grelha, outros tempos ou
outros sprites do que os daqui), o script para e diz o que nao encontrou.
"""
import csv
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C                     # noqa: E402
from comum import render              # noqa: E402

L, A, FPS = C.L, C.A, C.FPS
VL, VA = 1280, 720                    # o video das previas
CRF = "23"
LIMITE_BYTES = 25 * 1000 * 1000       # "abaixo de 25 MB", contado pelo lado curto
SAIDA = C.pasta("mergulho")

# AS 20 FOTOS, pela ordem da grelha de 5 por 4. Sao as viagens da v3: 11 da pilha das Viagens da
# Clara (ordem 116) e 9 das viagens a dois (pilhas 139 e 140), com formatos de 0,75 a 1,5. As
# mergulhadas sao fotos grandes e deitadas, para se julgar o movimento e nao o recorte de uma foto em
# pe (essa mostra no fim so 25% a 56% da altura, ja medido a 1 de outubro).
FOTOS = ["f0058", "f0065", "f0212", "f0073", "f0069", "f0068", "f0076",
         "f0040", "f0481", "f0070", "f0328", "f0430", "f0217", "f0427",
         "f0494", "f0416", "f0272", "f0412", "f0330", "f0331"]
# Onde se mergulha, pela posicao na grelha (0 = a primeira). A 7.a, a 14.a e a 20.a estao em filas
# e colunas diferentes e sao tambem as ultimas dos tres grupos do D; o B so anda entre vizinhas, e
# por isso mergulha nas tres ultimas da fila de baixo.
MANEIRAS = [
    # (letra, nome, uma linha para o cartao, onde mergulha, ficheiro)
    ("A", "Mergulha e volta", "volta à grelha inteira entre uma foto e a seguinte", [6, 13, 19],
     "mergulho_A_volta.mp4"),
    ("B", "Passeia de perto", "já de perto, desliza de lado até à vizinha", [17, 18, 19],
     "mergulho_B_passeia.mp4"),
    ("C", "Voo entre fotos", "recua só o preciso para ver as duas, e mergulha", [6, 13, 19],
     "mergulho_C_voo.mp4"),
    ("D", "Três grupos seguidos", "sem código novo: grupos de 7, 7 e 6 fotos", None,
     "mergulho_D_grupos.mp4"),
]
GRUPOS_D = [7, 7, 6]
JUNTAS = "mergulho_varias_ABCD.mp4"
FOLHA = "folha_mergulho_varias.jpg"
MEDIDAS = "medidas_mergulho_varias.json"

ENTRA = SAI = 0.7          # o encadeado normal, dos dois lados de cada clip
ESPERA_ENTRE = 0.6         # A: a grelha inteira entre dois mergulhos
DESLIZA_PROPOSTA = 1.0     # B: o deslize da proposta de 1 de outubro, so para se dizer quanto corria
CARTAO_S = 2.5             # o cartao de titulo antes de cada maneira
SENTINELA = (255, 0, 255)  # a cor do que estivesse fora da grelha, para se contar
QUASE = 0.9                # "quase a encher": a foto em 90% do ecra
VIZINHA_CONTA = 0.01       # uma vizinha esticada conta quando tem pelo menos 1% do ecra
INTEIRA = (0.0, 0.0, 1.0)  # a vista da grelha inteira

PRECISA = ["mergulho_grelha", "mergulho_cobre", "mergulho_desce", "mergulho_tempos",
           "duracao_mergulho", "mergulho_trocos", "mergulho_vista_cobre", "mergulho_vista_aproxima",
           "mergulho_vista_no_troco", "preparar_mergulho", "desenhar_mergulho", "compor", "com_margem",
           "cobrir_foco", "cobrir_alto", "aberta", "FotoPorAbrir", "tamanho_da_foto", "suave",
           "MERGULHO_DOBRO", "MERGULHO_FOLGA", "MERGULHO_FICA", "MERGULHO_FICA_ZOOM",
           "MERGULHO_RESPIRA", "MERGULHO_ESPERA", "FINAIS"]


def verificar_render():
    falta = [n for n in PRECISA if not hasattr(render, n)]
    if falta:
        raise SystemExit("O render ja nao tem %s. Esta previa usa as funcoes do mergulho do render tal "
                         "como estavam a 1 de outubro; se o mergulho mudou, a previa tem de ser refeita."
                         % ", ".join(falta))
    if render.preparar_mergulho.__code__.co_argcount != 6:
        raise SystemExit("O preparar_mergulho do render mudou de argumentos (esperava imagens, focos, "
                         "texto, entra, sai, duracao): a previa tem de ser refeita.")


# ---------------------------------------------------------------------------------------------
# AS FOTOS, PELO ID, E O FICHEIRO QUE O data/finais.csv ESCOLHE
# ---------------------------------------------------------------------------------------------

def encontrar_fotos():
    """[{id, ficheiro, caminho, origem, clip, tamanho}] pela ordem de FOTOS. Para se uma nao estiver
    na montagem, no indice ou em disco: nunca se mostra outra no lugar dela."""
    with open(os.path.join(C.REPO, "data", "finais.csv"), encoding="utf-8-sig", newline="") as fh:
        finais = {r["id"]: r for r in csv.DictReader(fh)}
    with open(os.path.join(render.MONTAGENS, C.MONTAGEM + ".csv"), encoding="utf-8-sig", newline="") as fh:
        clips = list(csv.DictReader(fh))
    onde = {}
    for c in clips:
        for i in (c["id"] or "").split("|"):
            onde.setdefault(i, c)
    out = []
    for i in FOTOS:
        if i not in onde:
            raise SystemExit("A foto %s ja nao esta na montagem %s. Escolhe outra para FOTOS." % (i, C.MONTAGEM))
        if i not in finais:
            raise SystemExit("A foto %s nao tem linha no data/finais.csv." % i)
        caminho = os.path.join(render.FINAIS, finais[i]["final"])
        if not os.path.exists(caminho):
            raise SystemExit("O ficheiro que o finais.csv escolhe para %s nao esta em disco: %s" % (i, caminho))
        c = onde[i]
        out.append({"id": i, "ficheiro": finais[i]["ficheiro"], "caminho": caminho,
                    "origem": finais[i]["origem"], "clip": "%s %s" % (c["ordem"], c["tipo"]),
                    "tamanho": render.tamanho_da_foto(caminho)})
    return out


# ---------------------------------------------------------------------------------------------
# A CAMARA: TROCOS ENTRE VISTAS
# ---------------------------------------------------------------------------------------------
# Um troco daqui e {nome, de, ate, celulas, vista}: `vista(t)` da a vista (x0, y0, s) da camara no
# instante t do clip e `celulas` as fotos que se compoem por cima a partir do sprite delas. Os do
# render (mergulho_trocos) entram embrulhados, com a interpolacao dele.

def de_render(trocos):
    """Os trocos do render (espera, desce e fica) no formato daqui."""
    if len(trocos) != 3:
        raise SystemExit("O mergulho_trocos do render devolveu %d trocos e esta previa conta com 3 "
                         "(espera, desce, fica): tem de ser refeita." % len(trocos))
    return [{"nome": nome, "de": tr["de"], "ate": tr["ate"], "celulas": [tr["celula"]],
             "vista": (lambda t, tr=tr: render.mergulho_vista_no_troco(tr, t))}
            for nome, tr in zip(("espera", "desce", "fica"), trocos)]


def troco(nome, de, dura, v0, v1, modo, celulas):
    """Um troco entre duas vistas, com a interpolacao do render (mergulho_vista_no_troco)."""
    tr = {"de": de, "ate": de + dura, "v0": v0, "v1": v1, "modo": modo, "celula": celulas[-1]}
    return {"nome": nome, "de": de, "ate": de + dura, "celulas": list(celulas),
            "vista": (lambda t, tr=tr: render.mergulho_vista_no_troco(tr, t))}


def v_cobre(cel):
    return render.mergulho_vista_cobre(cel)


def v_fim(cel):
    """A vista no fim do fica: a celula a cobrir o ecra, 3% mais perto (MERGULHO_FICA_ZOOM)."""
    return render.mergulho_vista_aproxima(v_cobre(cel), cel, 1.0 + render.MERGULHO_FICA_ZOOM)


def v_respira(cel, espera):
    """A grelha inteira a respirar em torno da celula, a mesma velocidade da espera do render."""
    fator = (1.0 + render.MERGULHO_RESPIRA) ** (espera / render.MERGULHO_ESPERA)
    return render.mergulho_vista_aproxima(INTEIRA, cel, fator)


def desce_de(cel):
    return render.mergulho_desce(render.mergulho_cobre(cel))


def prender(v, altura):
    """A vista presa a grelha, e quantos pixeis do ecra teria mostrado de fora dela (0 se nenhum).

    Nao toca numa vista que ja esta dentro, para os fotogramas do A, do B e do D sairem iguais aos
    do render ao byte.
    """
    x0, y0, s = v
    # o que a vista livre mostraria de fora, em pixeis do ecra
    fora = max(0.0, -x0, x0 + L / s - L, -y0, y0 + A / s - altura) * s
    if fora < 1e-6:
        return v, 0.0
    s = max(s, 1.0, A / float(altura))
    return (min(max(x0, 0.0), L - L / s), min(max(y0, 0.0), altura - A / s), s), fora


def camara(plano, t):
    """(vista presa, celulas a compor, pixeis que a vista livre teria mostrado fora, troco)."""
    trocos = plano["trocos"]
    tr = trocos[-1]
    for x in trocos:
        if t < x["ate"]:
            tr = x
            break
    v, fora = prender(tr["vista"](t), plano["altura"])
    return v, tr["celulas"], fora, tr


# ---------------------------------------------------------------------------------------------
# O VOO DO C: O CAMINHO DE VAN WIJK E NUIJ
# ---------------------------------------------------------------------------------------------
# "Smooth and efficient zooming and panning" (van Wijk e Nuij, 2003), o mesmo do d3.interpolateZoom:
# o caminho entre duas vistas que o olho le com velocidade constante, recuando enquanto anda. O rho
# diz quanto recua; aqui escolhe-se para o ponto mais afastado mostrar as duas fotos inteiras, com a
# linha preta a volta, e nada mais ("recua so o preciso para se verem as duas"). So se usa quando
# cabe na grelha inteiro; perto da borda o voo parte-se em dois, ver voo_entre.

def centro_largura(v):
    x0, y0, s = v
    return x0 + L / (2.0 * s), y0 + A / (2.0 * s), L / s


def van_wijk(p0, p1, rho):
    """(S, em): em(u) da (centro x, centro y, largura) para u de 0 a S."""
    ux0, uy0, w0 = p0
    ux1, uy1, w1 = p1
    dx, dy = ux1 - ux0, uy1 - uy0
    d = math.hypot(dx, dy)
    if d < 1e-6:
        raise SystemExit("O voo do C e entre duas fotos diferentes, e estas estao no mesmo sitio.")
    r2, r4 = rho * rho, rho ** 4
    b0 = (w1 * w1 - w0 * w0 + r4 * d * d) / (2.0 * w0 * r2 * d)
    b1 = (w1 * w1 - w0 * w0 - r4 * d * d) / (2.0 * w1 * r2 * d)
    r0, r1 = -math.asinh(b0), -math.asinh(b1)
    S = (r1 - r0) / rho
    ch0, sh0 = math.cosh(r0), math.sinh(r0)

    def em(u):
        a = rho * u + r0
        f = w0 / (r2 * d) * (ch0 * math.tanh(a) - sh0)
        return ux0 + f * dx, uy0 + f * dy, w0 * ch0 / math.cosh(a)
    return S, em


def contem(v, cel):
    """Se a vista mostra a celula inteira."""
    x0, y0, s = v
    x, y, w, h = cel
    return (x0 <= x + 1e-6 and y0 <= y + 1e-6 and x0 + L / s >= x + w - 1e-6
            and y0 + A / s >= y + h - 1e-6)


def voo_entre(ca, cb, altura):
    """O voo do fim do fica numa foto ate ela cobrir o ecra na seguinte.

    A velocidade e a do mergulho de hoje (a_velocidade_do_mergulho), com o arranque e a travagem
    do render (suave).

    PERTO DA BORDA O VOO PARTE-SE EM DOIS (verificacao de 1 de outubro). O caminho de van Wijk
    centra-se entre as duas fotos e, quando uma delas esta numa borda, sai da grelha: no voo da
    14.a para a 20.a, no canto, saia ate 313 px. Prender cada vista a grelha dava um solavanco: a
    camara ia para a esquerda a 32 px por fotograma e no fotograma seguinte ia para a direita a 10,
    e depois parava de repente. Por isso, quando o caminho livre sai da grelha, o voo sao dois
    trocos do render: recua ate a vista que mostra as duas (a mais pequena que as mostra, presa a
    grelha) e mergulha na seguinte. Nenhuma vista sai da grelha e a camara nunca salta; no ponto
    mais longe abranda ate quase parar, porque encostada ao canto ja nao tem para onde andar de
    lado. Quando o caminho cabe na grelha, fica o de van Wijk, num so movimento.
    """
    p0, p1 = centro_largura(v_fim(ca)), centro_largura(v_cobre(cb))
    f = render.MERGULHO_FOLGA
    bx0, bx1 = min(ca[0], cb[0]) - f, max(ca[0] + ca[2], cb[0] + cb[2]) + f
    by0, by1 = min(ca[1], cb[1]) - f, max(ca[1] + ca[3], cb[1] + cb[3]) + f
    precisa = min(max(bx1 - bx0, (by1 - by0) * L / A), L, altura * L / A)

    def pico(rho):
        S, em = van_wijk(p0, p1, rho)
        return max(em(S * i / 400.0)[2] for i in range(401))
    lo, hi = 1e-3, 8.0
    if pico(hi) < precisa:
        rho = hi
    elif pico(lo) >= precisa:
        rho = lo
    else:
        for _ in range(60):
            meio = (lo + hi) / 2.0
            if pico(meio) < precisa:
                lo = meio
            else:
                hi = meio
        rho = hi
    S, em = van_wijk(p0, p1, rho)
    fim = em(S)
    if max(abs(fim[0] - p1[0]), abs(fim[1] - p1[1]), abs(fim[2] - p1[2])) > 1e-6:
        raise SystemExit("O caminho do voo nao acaba na vista da foto seguinte: a conta esta errada.")

    def vista(p):
        ux, uy, w = em(render.suave(min(1.0, max(0.0, p))) * S)
        s = L / w
        return (ux - w / 2.0, uy - A / (2.0 * s), s)
    # quanto o caminho livre mostraria de fora da grelha, em pixeis do ecra
    livre_fora = max(prender(vista(i / 400.0), altura)[1] for i in range(401))
    if livre_fora < 1e-6:
        return {"vista": vista, "rho": rho, "recua": L / precisa, "partido": False, "livre_fora_px": 0.0}
    # a vista mais pequena que mostra as duas, centrada nelas e presa a grelha
    w = precisa
    vm = prender(((bx0 + bx1) / 2.0 - w / 2.0, (by0 + by1) / 2.0 - w * A / (2.0 * L), L / w), altura)[0]
    if not (contem(vm, ca) and contem(vm, cb)):
        raise SystemExit("A vista do ponto mais longe do voo nao mostra as duas fotos: a conta esta errada.")
    return {"vm": vm, "rho": rho, "recua": vm[2], "partido": True, "livre_fora_px": livre_fora}


# A VELOCIDADE NO ECRA. O deslocamento medio, por fotograma, de 81 pontos espalhados pelo ecra, com a
# vista ja presa a grelha. Num zoom o centro fica parado e as bordas correm; num deslize corre tudo
# por igual: a media e o que o olho ve mexer. O mergulho de 20 na ultima da 64 px no pico.
PONTOS_FLUXO = [(L * (i + 0.5) / 9.0, A * (j + 0.5) / 9.0) for i in range(9) for j in range(9)]


def fluxo(vista, de, ate, altura):
    """O maior deslocamento medio do ecra por fotograma de 25 fps, entre de e ate (10 amostras por
    fotograma)."""
    passos = max(2, int(round((ate - de) * FPS * 10)))
    por_fotograma = passos / ((ate - de) * FPS)
    pico, ant = 0.0, None
    for i in range(passos + 1):
        x0, y0, s = prender(vista(de + (ate - de) * i / float(passos)), altura)[0]
        if ant is not None:
            ax0, ay0, as_ = ant
            soma = sum(math.hypot((ax0 + X / as_ - x0) * s - X, (ay0 + Y / as_ - y0) * s - Y)
                       for X, Y in PONTOS_FLUXO)
            pico = max(pico, soma / len(PONTOS_FLUXO) * por_fotograma)
        ant = (x0, y0, s)
    return pico


def a_velocidade_do_mergulho(vista_p, altura, ref):
    """Quanto dura um movimento (vista_p para p de 0 a 1) para o pico do fluxo ser o do mergulho. O
    caminho e o mesmo e so o tempo muda: o fluxo cai na proporcao em que a duracao cresce."""
    return fluxo(vista_p, 0.0, 1.0, altura) / ref


# ---------------------------------------------------------------------------------------------
# OS PLANOS: A GRELHA, OS TEMPOS E OS TROCOS DE CADA MANEIRA, SEM ABRIR FOTOS
# ---------------------------------------------------------------------------------------------

def base(n, altura=A):
    """A grelha e os tempos de hoje de um mergulho de n fotos sem legenda, como o render os faz."""
    celulas = render.mergulho_grelha(n, L, altura)
    cobre = render.mergulho_cobre(celulas[-1])
    dura = render.duracao_mergulho(n, ENTRA, SAI, cobre)
    tempos = render.mergulho_tempos(n, dura, ENTRA, SAI, cobre)
    todas = tempos["atraso"] + tempos["entra"] + tempos["entre"] * (n - 1)
    return {"n": n, "altura": altura, "celulas": celulas, "tempos": tempos, "todas": todas,
            "hoje": dura}


def plano_varias(letra, n, alvos):
    """O plano do A, do B ou do C: o primeiro mergulho e o do render, o resto e daqui."""
    p = base(n)
    cel, fica = p["celulas"], p["tempos"]["fica"]
    k0 = alvos[0]
    trocos = de_render(render.mergulho_trocos(p["tempos"], cel[k0], k0))
    t = trocos[-1]["ate"]
    # a velocidade do mergulho de hoje, o do render nesta grelha (na ultima): o deslize e o voo andam a ela
    hoje = de_render(render.mergulho_trocos(p["tempos"], cel[-1], len(cel) - 1))[1]
    ref = fluxo(hoje["vista"], hoje["de"], hoje["ate"], p["altura"])
    voos = []
    for a, b in zip(alvos, alvos[1:]):
        ca, cb = cel[a], cel[b]
        if letra == "A":
            trocos.append(troco("volta", t, desce_de(ca), v_fim(ca), INTEIRA, "suave", [a]))
            t = trocos[-1]["ate"]
            trocos.append(troco("espera", t, ESPERA_ENTRE, INTEIRA, v_respira(cb, ESPERA_ENTRE), "linear", [b]))
            t = trocos[-1]["ate"]
            trocos.append(troco("desce", t, desce_de(cb), v_respira(cb, ESPERA_ENTRE), v_cobre(cb), "suave", [b]))
        elif letra == "B":
            vizinhas = (abs(ca[1] - cb[1]) < 1e-6 and
                        abs(abs(cb[0] - ca[0]) - (ca[2] + render.MERGULHO_FOLGA)) < 1e-6)
            if not vizinhas:
                raise SystemExit("O B so anda entre vizinhas da mesma fila, e a %d.a e a %d.a nao sao."
                                 % (a + 1, b + 1))
            prova = troco("desliza", 0.0, 1.0, v_fim(ca), v_cobre(cb), "suave", [a, b])
            dura = a_velocidade_do_mergulho(prova["vista"], p["altura"], ref)
            trocos.append(troco("desliza", t, dura, v_fim(ca), v_cobre(cb), "suave", [a, b]))
        else:
            voo = voo_entre(ca, cb, p["altura"])
            if not voo["partido"]:
                dura = a_velocidade_do_mergulho(voo["vista"], p["altura"], ref)
                voos.append(dict(voo, dura=dura, de=t, ate=t + dura, de_foto=a, para_foto=b))
                trocos.append({"nome": "voo", "de": t, "ate": t + dura, "celulas": [a, b],
                               "vista": (lambda tt, t0=t, v=voo, d=dura: v["vista"]((tt - t0) / d))})
            else:
                # perto da borda: recua ate ver as duas e mergulha, dois trocos do render (voo_entre).
                # Os dois chamam-se "voo", para as medidas e a folha os contarem como o voo.
                vm = voo["vm"]
                recua = a_velocidade_do_mergulho(
                    troco("voo", 0.0, 1.0, v_fim(ca), vm, "suave", [a, b])["vista"], p["altura"], ref)
                desce = a_velocidade_do_mergulho(
                    troco("voo", 0.0, 1.0, vm, v_cobre(cb), "suave", [a, b])["vista"], p["altura"], ref)
                trocos.append(troco("voo", t, recua, v_fim(ca), vm, "suave", [a, b]))
                trocos.append(troco("voo", t + recua, desce, vm, v_cobre(cb), "suave", [a, b]))
                voos.append(dict(voo, dura=recua + desce, recua_s=recua, desce_s=desce, de=t,
                                 ate=t + recua + desce, de_foto=a, para_foto=b))
        t = trocos[-1]["ate"]
        trocos.append(troco("fica", t, fica, v_cobre(cb), v_fim(cb), "linear", [b]))
        t = trocos[-1]["ate"]
    p.update(letra=letra, alvos=list(alvos), trocos=trocos, duracao=t + SAI, voos=voos, ini=0.0,
             primeira=0, fluxo_mergulho=ref)
    if letra == "B":
        prova = troco("desliza", 0.0, DESLIZA_PROPOSTA, v_fim(cel[alvos[0]]), v_cobre(cel[alvos[1]]),
                      "suave", alvos[:2])
        p["fluxo_proposta"] = fluxo(prova["vista"], 0.0, DESLIZA_PROPOSTA, p["altura"])
    return p


def plano_D():
    """Tres clips em mergulho, cada um com os trocos do render, encadeados como no filme."""
    clips, ini, k = [], 0.0, 0
    for n in GRUPOS_D:
        p = base(n)
        p["trocos"] = de_render(render.mergulho_trocos(p["tempos"], p["celulas"][n - 1], n - 1))
        p.update(letra="D", alvos=[n - 1], duracao=p["hoje"], voos=[], ini=ini, primeira=k)
        clips.append(p)
        ini += p["hoje"] - ENTRA
        k += n
    return {"letra": "D", "clips": clips, "duracao": clips[-1]["ini"] + clips[-1]["duracao"]}


def clips_de(plano):
    return plano["clips"] if plano["letra"] == "D" else [plano]


# ---------------------------------------------------------------------------------------------
# AS MEDIDAS, SO PELA CAMARA
# ---------------------------------------------------------------------------------------------

def medir(plano):
    """Fotograma a fotograma: quanto tempo cada foto mergulhada enche o ecra, quanto se esticam as
    vizinhas, se a camara livre sairia da grelha, a escala dos sprites e a velocidade no ecra."""
    d = render.MERGULHO_DOBRO
    m = {"fotos": [], "estica": 0.0, "estica_area": [0.0, 0.0], "estica_qualquer": 0.0,
         "area_15": 0.0, "area_2": 0.0, "segundos_15": 0.0,
         "fora_max_px": 0.0, "quadros_presos": 0, "sprite_max": 0.0, "fluxo_max_px": 0.0,
         "linha_deslize_px": 0.0, "recua": [], "preto_fora_px": None}
    for clip in clips_de(plano):
        for tr in clip["trocos"]:
            m["fluxo_max_px"] = max(m["fluxo_max_px"], fluxo(tr["vista"], tr["de"], tr["ate"], clip["altura"]))
        cel = clip["celulas"]
        alvos = {k: {"posicao": clip["primeira"] + k + 1, "enche_s": 0.0, "encadeado_s": 0.0,
                     "quase_s": 0.0} for k in clip["alvos"]}
        for q in range(int(round(clip["duracao"] * FPS))):
            t = q / float(FPS)
            if t < clip["todas"]:
                continue
            (x0, y0, s), celulas, fora, tr = camara(clip, t)
            vw, vh = L / s, A / s
            if fora > 0:
                m["quadros_presos"] += 1
                m["fora_max_px"] = max(m["fora_max_px"], fora)
            area = area_15 = area_2 = 0.0
            for j, (cx, cy, cw, ch) in enumerate(cel):
                ix = min(x0 + vw, cx + cw) - max(x0, cx)
                iy = min(y0 + vh, cy + ch) - max(y0, cy)
                if ix <= 0 or iy <= 0:
                    continue
                frac = ix * iy / (vw * vh)
                if j in alvos:
                    dentro = (x0 >= cx - 1e-6 and y0 >= cy - 1e-6 and x0 + vw <= cx + cw + 1e-6
                              and y0 + vh <= cy + ch + 1e-6)
                    if dentro:
                        alvos[j]["encadeado_s" if t >= clip["duracao"] - SAI else "enche_s"] += 1.0 / FPS
                    if frac >= QUASE:
                        alvos[j]["quase_s"] += 1.0 / FPS
                if j in celulas:
                    m["sprite_max"] = max(m["sprite_max"], s / render.mergulho_cobre(cel[j]))
                    continue
                # uma vizinha: vem da grelha ao dobro, esticada s / d
                if s > d and ix * s >= 1 and iy * s >= 1:
                    m["estica_qualquer"] = max(m["estica_qualquer"], s / d)
                    area += frac
                    area_15 += frac if s / d > 1.5 else 0.0
                    area_2 += frac if s / d > 2.0 else 0.0
                    if frac >= VIZINHA_CONTA:
                        m["estica"] = max(m["estica"], s / d)
            if area > m["estica_area"][0]:
                m["estica_area"] = [area, s / d]
            m["area_15"], m["area_2"] = max(m["area_15"], area_15), max(m["area_2"], area_2)
            if area_15 >= 0.05:
                m["segundos_15"] += 1.0 / FPS
            if tr["nome"] == "desliza":
                m["linha_deslize_px"] = max(m["linha_deslize_px"], render.MERGULHO_FOLGA * s)
            if tr["nome"] == "voo":
                m["recua"].append(s)
        m["fotos"] += [dict(v, celula=k) for k, v in sorted(alvos.items())]
    m["recua_min"] = min(m["recua"]) if m["recua"] else None
    del m["recua"]
    return m


# ---------------------------------------------------------------------------------------------
# OS PRONTOS: O PREPARAR DO RENDER, E OS SPRITES DAS OUTRAS FOTOS MARCADAS
# ---------------------------------------------------------------------------------------------

def sprite_do_mergulho(foto, celula):
    """O sprite de uma foto mergulhada, com a conta do preparar_mergulho: a celula a cobrir o ecra,
    feita do ficheiro aberto, com a margem preta do com_margem. Sem ponto de foco: as pilhas de onde
    vem estas fotos nao o tem."""
    x, y, w, h = celula
    cobre = render.mergulho_cobre(celula)
    Wf, Hf = int(math.ceil(w * cobre)), int(math.ceil(h * cobre))
    im = render.aberta(foto)
    return render.com_margem(render.cobrir_foco(im, Wf, Hf, None) or render.cobrir_alto(im, Wf, Hf), "preto")


def preparar(fotos, planos):
    """Os prontos: um para o A, o B e o C (a mesma grelha de 20, com um sprite por foto marcada em
    qualquer delas) e um por grupo do D. Prova que os sprites daqui sao os do render."""
    caminhos = [f["caminho"] for f in fotos]
    n = len(caminhos)
    p0 = planos["A"]
    t0 = time.time()
    imagens = [render.FotoPorAbrir(c) for c in caminhos]
    pronto = render.preparar_mergulho(imagens, [None] * n, "", ENTRA, SAI, p0["hoje"])
    if pronto["celulas"] != p0["celulas"] or pronto["tempos"] != p0["tempos"]:
        raise SystemExit("O preparar_mergulho fez outra grelha ou outros tempos do que o mergulho_grelha "
                         "e o mergulho_tempos dao: a previa tem de ser refeita.")
    # A prova: o sprite da ultima, feito aqui, e o que o render fez.
    meu = sprite_do_mergulho(render.FotoPorAbrir(caminhos[-1]), pronto["celulas"][-1])
    if meu.tobytes() != pronto["alvos"][n - 1].tobytes():
        raise SystemExit("O sprite feito aqui nao e o do preparar_mergulho: a conta dos sprites mudou "
                         "no render, e a previa tem de ser refeita.")
    marcadas = sorted(set(k for letra in "ABC" for k in planos[letra]["alvos"]))
    for k in marcadas:
        if k not in pronto["alvos"]:
            pronto["alvos"][k] = sprite_do_mergulho(imagens[k], pronto["celulas"][k])
    print("  grelha de %d e %d sprites prontos em %.0f s" % (n, len(pronto["alvos"]), time.time() - t0))
    prontos = {}
    for letra in "ABC":
        prontos[letra] = [dict(pronto, _camada=None)]
    prontos["D"] = []
    for clip in planos["D"]["clips"]:
        t0 = time.time()
        k, m = clip["primeira"], clip["n"]
        grupo = [render.FotoPorAbrir(c) for c in caminhos[k:k + m]]
        pd = render.preparar_mergulho(grupo, [None] * m, "", ENTRA, SAI, clip["duracao"])
        if pd["celulas"] != clip["celulas"] or pd["tempos"] != clip["tempos"]:
            raise SystemExit("O preparar_mergulho fez outra grelha ou outros tempos no grupo de %d." % m)
        prontos["D"].append(pd)
        print("  grupo de %d pronto em %.0f s" % (m, time.time() - t0))
    return prontos


def ampliacao(foto, celula):
    """Quanto o Lanczos amplia o ficheiro para fazer o sprite (abaixo de 1 e reducao)."""
    x, y, w, h = celula
    cobre = render.mergulho_cobre(celula)
    W, H = foto["tamanho"]
    return max(math.ceil(w * cobre) / float(W), math.ceil(h * cobre) / float(H))


# ---------------------------------------------------------------------------------------------
# O DESENHO
# ---------------------------------------------------------------------------------------------
PRETO = Image.new("RGB", (L, A), (0, 0, 0))


def desenhar(pronto, clip, t, conta):
    """Um fotograma de um clip no instante t dele.

    Enquanto as fotos aparecem a camara esta parada e o desenho e o do render. Depois e o do
    desenhar_mergulho do render, com duas diferencas: a vista vem da camara daqui, e compoem-se por
    cima os sprites de todas as celulas do troco (uma no render; duas no deslize e no voo). O que
    caisse fora da grelha sai na cor SENTINELA, conta-se e pinta-se de preto.
    """
    if t < clip["todas"]:
        return render.desenhar_mergulho(pronto, t, clip["duracao"])
    (x0, y0, s), celulas, _fora, _tr = camara(clip, t)
    d = render.MERGULHO_DOBRO
    tela = pronto["grande"].transform((L, A), Image.AFFINE, (d / s, 0.0, d * x0, 0.0, d / s, d * y0),
                                      resample=Image.BICUBIC, fillcolor=SENTINELA)
    a = np.asarray(tela)
    fora = (a[..., 0] == SENTINELA[0]) & (a[..., 1] == SENTINELA[1]) & (a[..., 2] == SENTINELA[2])
    nf = int(fora.sum())
    if nf:
        conta["px"] += nf
        conta["quadros"] += 1
        b = a.copy()
        b[fora] = 0
        tela = Image.fromarray(b)
    for k in celulas:
        x, y, w, h = pronto["celulas"][k]
        render.compor(tela, pronto["alvos"][k], (x + w / 2.0 - x0) * s, (y + h / 2.0 - y0) * s,
                      s / render.mergulho_cobre((x, y, w, h)))
    if pronto["capa"] is not None:
        cor, mascara = pronto["capa"]
        tela.paste(cor, (0, 0), mascara)
    return tela


def quadro(letra, t, planos, prontos, conta):
    """O fotograma t da maneira: no D os clips encadeiam-se como no render.fotograma; no fim de todas
    a ultima desfaz-se a preto no tempo do encadeado de saida."""
    plano = planos[letra]
    clips = clips_de(plano)
    ativos = [i for i, c in enumerate(clips) if c["ini"] - 0.001 <= t < c["ini"] + c["duracao"]]
    ativos = (ativos or [len(clips) - 1])[-2:]
    ims = [desenhar(prontos[letra][i], clips[i], t - clips[i]["ini"], conta) for i in ativos]
    if len(ims) == 1:
        im = ims[0]
    else:
        im = Image.blend(ims[0], ims[1], min(1.0, max(0.0, (t - clips[ativos[-1]]["ini"]) / ENTRA)))
    fim = plano["duracao"]
    if t > fim - SAI:
        im = Image.blend(im, PRETO, min(1.0, (t - (fim - SAI)) / SAI))
    return im


def provar_igual_ao_render(planos, prontos):
    """Tres fotogramas do primeiro grupo do D, desenhados aqui e pelo render.desenhar_mergulho."""
    clip, pronto = planos["D"]["clips"][0], prontos["D"][0]
    desce = [tr for tr in clip["trocos"] if tr["nome"] == "desce"][0]
    conta = {"px": 0, "quadros": 0}
    for t in (desce["de"] + 0.2, (desce["de"] + desce["ate"]) / 2.0, desce["ate"] + 0.3):
        meu = desenhar(pronto, clip, t, conta)
        dele = render.desenhar_mergulho(pronto, t, clip["duracao"])
        if meu.tobytes() != dele.tobytes():
            raise SystemExit("O fotograma de %.2f s do D desenhado aqui nao e o do render: a previa "
                             "deixou de desenhar como o render." % t)
    print("  sprites e fotogramas iguais ao byte aos do render")


# ---------------------------------------------------------------------------------------------
# OS MOMENTOS DA FOLHA
# ---------------------------------------------------------------------------------------------

def _trocos(clip, nome):
    return [tr for tr in clip["trocos"] if tr["nome"] == nome]


def _meio(tr, f=0.5):
    return tr["de"] + f * (tr["ate"] - tr["de"])


def _pico(clip, voo):
    """O instante do voo em que a camara esta mais longe (a escala mais pequena). `voo` e um dos
    plano["voos"], que pode ser um troco so ou dois (voo_entre)."""
    ts = [_meio(voo, i / 200.0) for i in range(201)]
    return min(ts, key=lambda t: camara(clip, t)[0][2])


def momentos(letra, planos):
    """Seis (instante, o que se ve) de cada maneira, em segundos da maneira."""
    p = planos[letra]
    if letra == "D":
        c1, c2, c3 = p["clips"]
        return [(_meio(_trocos(c1, "espera")[0]), "grelha do 1.º grupo"),
                (_meio(_trocos(c1, "fica")[0]), "a 7.ª enche o ecrã"),
                (c2["ini"] + ENTRA / 2.0, "o encadeado para o 2.º grupo"),
                (c2["ini"] + _meio(_trocos(c2, "espera")[0]), "grelha do 2.º grupo"),
                (c3["ini"] + _meio(_trocos(c3, "desce")[0]), "a mergulhar na 20.ª"),
                (c3["ini"] + _meio(_trocos(c3, "fica")[0]), "a 20.ª enche o ecrã")]
    a = [k + 1 for k in p["alvos"]]
    fica, desce = _trocos(p, "fica"), _trocos(p, "desce")
    out = [(_meio(_trocos(p, "espera")[0]), "a grelha inteira"),
           (_meio(desce[0]), "a mergulhar na %d.ª" % a[0])]
    if letra == "A":
        out += [(_meio(fica[0]), "a %d.ª enche o ecrã" % a[0]),
                (_meio(_trocos(p, "volta")[0]), "a voltar à grelha"),
                (_meio(desce[1]), "a mergulhar na %d.ª" % a[1])]
    elif letra == "B":
        out += [(_meio(fica[0]), "a %d.ª enche o ecrã" % a[0]),
                (_meio(_trocos(p, "desliza")[0]), "a deslizar para a %d.ª" % a[1]),
                (_meio(fica[1]), "a %d.ª enche o ecrã" % a[1])]
    else:
        voos = p["voos"]
        out += [(_meio(fica[0]), "a %d.ª enche o ecrã" % a[0]),
                (_pico(p, voos[0]), "o voo, mais longe (%d.ª para %d.ª)" % (a[0], a[1])),
                (_pico(p, voos[1]), "o voo, mais longe (%d.ª para %d.ª)" % (a[1], a[2]))]
    return out + [(_meio(fica[-1]), "a %d.ª enche o ecrã" % a[-1])]


def fazer_folha(planos, prontos, pasta_quadros=None):
    TW, TH, ESQ, TOPO, LEG, ESP = 400, 225, 190, 86, 62, 12
    W = ESQ + 6 * (TW + ESP) + ESP
    H = TOPO + 4 * (TH + LEG + ESP) + ESP
    folha = Image.new("RGB", (W, H), (20, 20, 22))
    d = ImageDraw.Draw(folha)
    f_tit = ImageFont.truetype(C.ARIALBD, 34)
    f_letra = ImageFont.truetype(C.ARIALBD, 72)
    f_nome = ImageFont.truetype(C.ARIALBD, 21)
    f_leg = ImageFont.truetype(C.ARIAL, 19)
    d.text((ESP, 22), "Mergulho em mais do que uma foto: 6 momentos de cada maneira (as mesmas 20 "
           "fotos, 3 mergulhos)", font=f_tit, fill=(240, 240, 240))
    conta = {"px": 0, "quadros": 0}
    for r, (letra, nome, _linha, _alvos, _fich) in enumerate(MANEIRAS):
        y = TOPO + r * (TH + LEG + ESP)
        d.text((ESP + 6, y + 10), letra, font=f_letra, fill=(255, 205, 90))
        for i, linha in enumerate(_partir(nome, 15)):
            d.text((ESP + 6, y + 98 + i * 26), linha, font=f_nome, fill=(235, 235, 235))
        d.text((ESP + 6, y + 160), _seg(planos[letra]["duracao"]), font=f_nome, fill=(255, 205, 90))
        for c, (t, texto) in enumerate(momentos(letra, planos)):
            im = quadro(letra, t, planos, prontos, conta)
            if pasta_quadros:
                im.save(os.path.join(pasta_quadros, "%s_%d_%05.2fs.jpg" % (letra, c + 1, t)), quality=90)
            x = ESQ + c * (TW + ESP)
            folha.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
            d.text((x, y + TH + 6), "%s  %s" % (_seg(t), texto), font=f_leg, fill=(225, 225, 225))
    caminho = os.path.join(SAIDA, FOLHA)
    folha.save(caminho, quality=88)
    return caminho, conta


def _partir(texto, largura):
    linhas, atual = [], ""
    for p in texto.split():
        if atual and len(atual) + 1 + len(p) > largura:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
    return linhas + [atual]


def _seg(x):
    return ("%.1f s" % x).replace(".", ",")


# ---------------------------------------------------------------------------------------------
# OS VIDEOS
# ---------------------------------------------------------------------------------------------

def abrir_encoder(saida):
    """Fotogramas RGB de 1920x1080 pela entrada, 1280x720 a 25 fps a saida, com uma faixa de silencio
    (alguns telemoveis tratam um video sem som como um GIF)."""
    return subprocess.Popen(
        [C.FF, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (L, A), "-r", str(FPS), "-i", "-",
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-map", "0:v", "-map", "1:a", "-vf", "scale=%d:%d:flags=lanczos" % (VL, VA),
         "-c:v", "libx264", "-crf", CRF, "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", saida],
        stdin=subprocess.PIPE)


def cartao(titulo, rotulo, sub):
    """O cartao das previas (comum.cartao_titulo), ao tamanho do ecra."""
    if ImageFont.truetype(C.ARIAL, 44).getlength(sub) > 1240:
        print("  AVISO: a linha do cartao nao cabe: %s" % sub)
    tmp = os.path.join(SAIDA, "_cartao.png")
    C.cartao_titulo(tmp, titulo, rotulo, sub, True)
    im = Image.open(tmp).convert("RGB").resize((L, A), Image.LANCZOS)
    os.remove(tmp)
    return im


def escrever_cartao(enc, im):
    b = im.tobytes()
    for _ in range(int(round(CARTAO_S * FPS))):
        enc.stdin.write(b)


def video_da_maneira(letra, nome, linha, ficheiro, planos, prontos):
    saida = os.path.join(SAIDA, ficheiro)
    plano = planos[letra]
    enc = abrir_encoder(saida)
    escrever_cartao(enc, cartao("%s. %s" % (letra, nome), _seg(plano["duracao"]), linha))
    conta = {"px": 0, "quadros": 0}
    nq = int(round(plano["duracao"] * FPS))
    t0 = time.time()
    for q in range(nq):
        enc.stdin.write(quadro(letra, q / float(FPS), planos, prontos, conta).tobytes())
        if q and q % 100 == 0:
            print("    %s: %d de %d fotogramas, %.0f s" % (letra, q, nq, time.time() - t0))
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("O ffmpeg falhou ao escrever %s" % saida)
    print("  %s feito em %.0f s: %s (%.1f MB)" % (letra, time.time() - t0, saida, os.path.getsize(saida) / 1e6))
    return saida, conta


def video_de_abertura():
    saida = os.path.join(SAIDA, "_abertura.mp4")
    enc = abrir_encoder(saida)
    escrever_cartao(enc, cartao("Mergulho em mais do que uma foto", "A, B, C e D",
                                "as mesmas 20 fotos de viagens, três mergulhos"))
    enc.stdin.close()
    enc.wait()
    return saida


def apertar(caminho, limite):
    """Se o video junto passar do limite, volta a codificar-se com o debito que cabe."""
    if os.path.getsize(caminho) < limite:
        return
    dura = C.duracao(caminho)
    kbps = int((limite * 8 * 0.94 / dura - 64000) / 1000)
    tmp = caminho + ".tmp.mp4"
    subprocess.run([C.FF, "-hide_banner", "-loglevel", "error", "-y", "-i", caminho,
                    "-c:v", "libx264", "-preset", "medium", "-b:v", "%dk" % kbps,
                    "-maxrate", "%dk" % int(kbps * 1.5), "-bufsize", "%dk" % (kbps * 2),
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, caminho)
    print("  o video junto passava de %d MB: refeito a %d kb/s" % (limite // 1000000, kbps))


# ---------------------------------------------------------------------------------------------
# DIZER
# ---------------------------------------------------------------------------------------------

def dizer(fotos, planos, medidas):
    print("\nAS 20 FOTOS (viagens da %s), pela ordem da grelha de 5 por 4:" % C.MONTAGEM)
    for k, f in enumerate(fotos):
        w, h = f["tamanho"]
        print("  %2d. %s  %-48s %5dx%-5d %.2f  clip %s  (%s)" % (k + 1, f["id"], f["ficheiro"][:48], w, h,
                                                               w / float(h), f["clip"], f["origem"]))
    hoje = planos["A"]["hoje"]
    print("\nHoje, um mergulho so, com 20 fotos: %s (com 0,7 s de encadeado a entrar e a sair)." % _seg(hoje))
    for letra, nome, _l, _a, _f in MANEIRAS:
        p, m = planos[letra], medidas[letra]
        print("\n%s. %s: %s" % (letra, nome, _seg(p["duracao"])))
        if letra != "D":
            print("   cada foto a mais custa %.2f s (um mergulho so: %.2f s)"
                  % ((p["duracao"] - hoje) / (len(p["alvos"]) - 1), hoje))
            print("   " + ", ".join("%s %.2f" % (tr["nome"], tr["ate"] - tr["de"]) for tr in p["trocos"]))
        else:
            for c in p["clips"]:
                print("   grupo de %d: %.2f s, a comecar aos %.2f s (grelha de %d celulas de %.0fx%.0f, "
                      "mergulho de %.2f s)" % (c["n"], c["duracao"], c["ini"], len(c["celulas"]),
                                               c["celulas"][0][2], c["celulas"][0][3], c["tempos"]["desce"]))
        for v in p.get("voos", []):
            if v["partido"]:
                print("   voo da %d.a para a %d.a: %.2f s, recua %.2f s ate a escala %.2f e mergulha %.2f s "
                      "(o caminho de van Wijk sairia da grelha ate %.0f px, por isso parte-se em dois)"
                      % (v["de_foto"] + 1, v["para_foto"] + 1, v["dura"], v["recua_s"], v["recua"],
                         v["desce_s"], v["livre_fora_px"]))
            else:
                print("   voo da %d.a para a %d.a: %.2f s, recua ate a escala %.2f (rho %.2f), num so movimento"
                      % (v["de_foto"] + 1, v["para_foto"] + 1, v["dura"], v["recua"], v["rho"]))
        for f in m["fotos"]:
            print("   a %d.a (%s) enche o ecra %.2f s%s; em 90%% ou mais %.2f s"
                  % (f["posicao"], fotos[f["posicao"] - 1]["id"], f["enche_s"],
                     (" + %.2f s do encadeado de saida" % f["encadeado_s"]) if f["encadeado_s"] else "",
                     f["quase_s"]))
        print("   vizinhas esticadas: ate %.2fx com 1%% do ecra ou mais (qualquer lasca: %.2fx); "
              "no pior fotograma %.0f%% do ecra esticado %.2fx"
              % (m["estica"], m["estica_qualquer"], 100 * m["estica_area"][0], m["estica_area"][1]))
        print("   mais de 1,5x: ate %.0f%% do ecra, %.2f s com 5%% ou mais; mais de 2x: ate %.0f%% do ecra"
              % (100 * m["area_15"], m["segundos_15"], 100 * m["area_2"]))
        print("   sprite das mergulhadas ate %.3fx; o ecra anda no maximo %.1f px por fotograma, em media"
              % (m["sprite_max"], m["fluxo_max_px"]))
        if p.get("fluxo_proposta"):
            print("   (com o deslize de %.1f s da proposta andava %.1f px por fotograma)"
                  % (DESLIZA_PROPOSTA, p["fluxo_proposta"]))
        if m["linha_deslize_px"]:
            print("   a linha preta entre fotos atravessa o ecra com %.0f px no deslize" % m["linha_deslize_px"])
        print("   fora da grelha: a camara livre mostraria ate %.1f px (%d fotogramas presos)%s"
              % (m["fora_max_px"], m["quadros_presos"],
                 "" if m["preto_fora_px"] is None else "; desenhado: %d px de preto fora" % m["preto_fora_px"]))


def main():
    verificar_render()
    so_dizer, so_quadros = "--so-dizer" in sys.argv, "--quadros" in sys.argv
    fotos = encontrar_fotos()
    planos = {}
    for letra, _n, _l, alvos, _f in MANEIRAS:
        planos[letra] = plano_D() if letra == "D" else plano_varias(letra, len(fotos), alvos)
    medidas = {letra: medir(planos[letra]) for letra in planos}
    for letra in planos:
        for f in medidas[letra]["fotos"]:
            k = f["posicao"] - 1
            clip = [c for c in clips_de(planos[letra]) if c["primeira"] <= k < c["primeira"] + c["n"]][0]
            f["id"] = fotos[k]["id"]
            f["ampliacao"] = round(ampliacao(fotos[k], clip["celulas"][k - clip["primeira"]]), 3)
    if so_dizer:
        dizer(fotos, planos, medidas)
        return
    print("A preparar as fotos (o preparar_mergulho do render)...")
    prontos = preparar(fotos, planos)
    provar_igual_ao_render(planos, prontos)
    pasta_quadros = None
    if so_quadros:
        pasta_quadros = os.path.join(SAIDA, "quadros")
        os.makedirs(pasta_quadros, exist_ok=True)
    folha, _conta = fazer_folha(planos, prontos, pasta_quadros)
    print("  folha: %s" % folha)
    videos = []
    if not so_quadros:
        partes = [video_de_abertura()]
        for letra, nome, linha, _a, ficheiro in MANEIRAS:
            saida, conta = video_da_maneira(letra, nome, linha, ficheiro, planos, prontos)
            medidas[letra]["preto_fora_px"] = conta["px"]
            medidas[letra]["preto_fora_quadros"] = conta["quadros"]
            partes.append(saida)
            videos.append(saida)
        juntas = os.path.join(SAIDA, JUNTAS)
        C.juntar_videos(partes, juntas)
        os.remove(partes[0])
        apertar(juntas, LIMITE_BYTES)
        videos.insert(0, juntas)
    dizer(fotos, planos, medidas)
    for v in videos:
        print("  %-28s %6.2f s  %5.1f MB" % (os.path.basename(v), C.duracao(v), os.path.getsize(v) / 1e6))
    resumo = {"fotos": [{k: f[k] for k in ("id", "ficheiro", "clip", "origem", "tamanho")} for f in fotos],
              "hoje_um_mergulho_s": planos["A"]["hoje"], "maneiras": {}}
    for letra, nome, linha, alvos, ficheiro in MANEIRAS:
        p = planos[letra]
        resumo["maneiras"][letra] = {
            "nome": nome, "linha": linha, "duracao_s": round(p["duracao"], 3), "video": ficheiro,
            "trocos": [[tr["nome"], round(c["ini"] + tr["de"], 3), round(c["ini"] + tr["ate"], 3)]
                       for c in clips_de(p) for tr in c["trocos"]],
            "voos": [{k: (round(v[k], 3) if isinstance(v[k], float) else v[k])
                      for k in ("de_foto", "para_foto", "dura", "recua", "rho", "partido", "livre_fora_px",
                                "recua_s", "desce_s") if k in v} for v in p.get("voos", [])],
            "medidas": medidas[letra]}
    with open(os.path.join(SAIDA, MEDIDAS), "w", encoding="utf-8") as fh:
        json.dump(resumo, fh, ensure_ascii=False, indent=1)
    print("  medidas: %s" % os.path.join(SAIDA, MEDIDAS))


if __name__ == "__main__":
    main()
