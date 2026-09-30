# -*- coding: utf-8 -*-
"""Previa do ponto 4: os separadores (os cartoes de texto), hoje contra o futuro, cada um no seu sitio
do filme, com a foto de antes, a de depois e o som. Nao muda nada; escreve em saida/discussao/ponto4/.

    py -3.11 scripts/discussao/ponto4_separadores.py [--so-dizer] [texto ...]

Sem textos mostra todos os cartoes com texto da montagem; com textos, so os cartoes que os contem.

O desenho e o do proprio render (render.fotograma), com o encadeado de entrada e de saida de cada
cartao. No futuro troca-se em memoria so o desenho do cartao, o resto do filme fica igual. A proposta
de 28 de setembro (a partir do titulo do Oppenheimer, e sem o grao de filme):
- textos de 1 a 3 palavras: maiusculas bem espacadas (0,30 em), Arial Bold 100, em linhas que caibam;
- frases: as linhas, as minusculas e o corpo 78 de hoje (a mesma quebra do render.cartao);
- os dois: cor champanhe quente com um brilho quente fraco, sobre preto; as letras entram a partir do
  preto em 0,6 s, aproximam-se devagar (2,5% por segundo) e dissolvem-se na foto seguinte no encadeado
  de saida, como hoje.
A proposta de 28 de setembro apagava as letras 0,5 s antes da foto seguinte. Medido nesta previa, isso
tirava 0,4 s de leitura a todos os cartoes (1,8 s de letras inteiras contra 2,2 s hoje), e as frases ja
sao as que passam depressa de mais (082): ficou APAGA = 0. Com --apaga-antes mostra-se a de 28/09.
Os cartoes encontram-se pelo tipo; o numero de palavras conta-se na montagem do momento.
"""
import gc
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C                     # noqa: E402
from comum import render              # noqa: E402

CURTO_MAX_PALAVRAS = 3
TAM_CURTO, TRACK_CURTO = 100, 0.30
EMPURRA = 0.025           # a aproximacao, por segundo
ENTRA = 0.6               # as letras entram em ENTRA s a partir do preto
APAGA = 0.5 if "--apaga-antes" in sys.argv else 0.0   # apagam-se nos APAGA s antes do encadeado de saida
MARGEM = 360              # a mesma largura util do render.cartao: L - 360


def linhas_curtas(texto):
    """As palavras em maiusculas, partidas em linhas que caibam na largura util com o espacamento."""
    f = ImageFont.truetype(C.ARIALBD, TAM_CURTO)
    track = TRACK_CURTO * TAM_CURTO

    def largura(ln):
        return sum(f.getlength(c) for c in ln) + track * (len(ln) - 1)
    linhas, atual = [], ""
    for p in texto.upper().split():
        tenta = (atual + " " + p).strip()
        if atual and largura(tenta) > C.L - MARGEM:
            linhas.append(atual)
            atual = p
        else:
            atual = tenta
    return linhas + ([atual] if atual else [])


def mascara_frase(texto):
    """A mesma quebra e o mesmo corpo do render.cartao, como mascara para o letreiro."""
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    tamanho = 78
    fonte = ImageFont.truetype(render.FONTE_TEXTO, tamanho)
    linhas = render.quebrar_paragrafos(texto, fonte, C.L - MARGEM, d)
    while len(linhas) > 4 and tamanho > 44:
        tamanho -= 6
        fonte = ImageFont.truetype(render.FONTE_TEXTO, tamanho)
        linhas = render.quebrar_paragrafos(texto, fonte, C.L - MARGEM, d)
    return C._mascara(linhas, tamanho, 0.0, entrelinha=1.4)


def curto(texto):
    return 0 < len(texto.split()) <= CURTO_MAX_PALAVRAS


def letreiro_do_cartao(texto, seed):
    if curto(texto):
        return C.colorir(C._mascara(linhas_curtas(texto), TAM_CURTO, TRACK_CURTO), seed)
    return C.colorir(mascara_frase(texto), seed)


PREPARAR, DESENHAR = render.preparar, render.desenhar


def preparar_futuro(clip, inv):
    p = PREPARAR(clip, inv)
    if p.get("tipo") == "cartao":
        texto = (clip.get("texto_ecra") or "").strip()
        p["_let"] = letreiro_do_cartao(texto, 7 + int(clip.get("ordem") or 0)) if texto else None
        p["_sai"] = float(clip.get("_transicao_seguinte") or 0.0)
    return p


def desenhar_futuro(pronto, t_rel, duracao):
    if pronto.get("tipo") != "cartao" or "_let" not in pronto:
        return DESENHAR(pronto, t_rel, duracao)
    if pronto["_let"] is None:
        return Image.new("RGB", (C.L, C.A), (0, 0, 0))
    fim = duracao - pronto["_sai"]
    alfa = C.suave(t_rel / ENTRA) * ((1.0 - C.suave((t_rel - (fim - APAGA)) / APAGA)) if APAGA > 0 else 1.0)
    if alfa <= 0.001:
        return Image.new("RGB", (C.L, C.A), (0, 0, 0))
    im = C.pousar(pronto["_let"], 1.0 + EMPURRA * t_rel)
    return Image.fromarray((np.asarray(im, np.float32) * alfa).astype(np.uint8), "RGB")


def rotulo(im, texto):
    d = ImageDraw.Draw(im)
    d.rectangle([24, 22, 24 + 30 + 26 * len(texto), 78], fill=(0, 0, 0))
    d.text((40, 30), texto, font=ImageFont.truetype(C.ARIALBD, 38), fill=(255, 205, 90) if texto == "FUTURO" else (235, 235, 235))
    return im


def segmento(est, t0, t1, som, saida, texto_rotulo):
    enc = C.encoder(saida, t1 - t0, som)
    for k in range(int(round((t1 - t0) * C.FPS))):
        im = render.fotograma(int(round((t0 + k / C.FPS) * C.FPS)), est)[0].convert("RGB")
        enc.stdin.write(rotulo(im, texto_rotulo).tobytes())
    enc.stdin.close()
    enc.wait()
    return saida


def main():
    filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = C.pasta("ponto4")
    hoje_est, fut_est = C.carregar(), C.carregar()
    desvio = hoje_est["desvio"]
    cartoes = [c for c in hoje_est["resto"] if c.get("tipo") == "cartao" and (c.get("texto_ecra") or "").strip()]
    if filtro:
        cartoes = [c for c in cartoes if any(f.lower() in c["texto_ecra"].lower() for f in filtro)]
    if not cartoes:
        raise SystemExit("Nenhum cartao com texto encontrado%s." % (" com " + ", ".join(filtro) if filtro else ""))
    for c in cartoes:
        dur, sai = float(c["duracao_s"]), float(c.get("_transicao_seguinte") or 0.0)
        cheio = dur - float(c.get("_transicao_entrada") or 0.0) - sai
        print("clip %-4s %-6s %4.1f s  hoje sozinho %.1f s, futuro com as letras cheias %.1f s  %r"
              % (c["ordem"], "curto" if curto(c["texto_ecra"]) else "frase", dur, cheio,
                 max(0.0, dur - sai - APAGA - ENTRA), c["texto_ecra"][:50]))
    print("(letras cheias no futuro: dos %.1f s ate a foto seguinte comecar a entrar%s)"
          % (ENTRA, ", menos %.1f s" % APAGA if APAGA else ""))
    if "--so-dizer" in sys.argv:
        return
    ent, _t = C.base_aprovada(hoje_est, com_097=False)     # o som aprovado, no relogio destes fotogramas
    partes = []
    for c in cartoes:
        ini = float(c["inicio_s"]) - desvio
        t0, t1 = max(0.0, ini - 1.2), ini + float(c["duracao_s"]) + 1.2
        base = os.path.join(pasta, "_%s" % c["ordem"])
        som = C.som_do_troco(C.CONSTRUIR_FUTURO, ent, t0, t1, base + "_som.m4a")
        render.preparar, render.desenhar = PREPARAR, DESENHAR
        partes.append(segmento(hoje_est, t0, t1, som, base + "_hoje.mp4", "HOJE"))
        render.preparar, render.desenhar = preparar_futuro, desenhar_futuro
        partes.append(segmento(fut_est, t0, t1, som, base + "_futuro.mp4", "FUTURO"))
        render.preparar, render.desenhar = PREPARAR, DESENHAR
        # AS FOTOS PREPARADAS FICAM NA MEMORIA DE CADA ESTADO, e com os 13 cartoes nos dois estados o
        # processo morria sem mensagem a meio (29 de setembro, ao terceiro cartao). Esvazia-se a cada um.
        hoje_est["prontos"].clear()
        fut_est["prontos"].clear()
        gc.collect()
        print("feito", c["texto_ecra"][:40], flush=True)
    saida = C.colar_com_filtro(partes, os.path.join(pasta, "ponto4_todos.mp4"))
    for p in partes:
        os.remove(p)
    for f in os.listdir(pasta):
        if f.startswith("_") and f.endswith("_som.m4a"):
            os.remove(os.path.join(pasta, f))
    print("escrito", saida)


if __name__ == "__main__":
    main()
