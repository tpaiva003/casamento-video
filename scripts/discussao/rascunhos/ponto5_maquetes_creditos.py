# RASCUNHO do ponto 5 (o fim e os creditos), guardado a 29 de setembro a partir da pasta temporaria
# da sessao. Desenha as maquetes paradas mostradas ao Tiago (nomes sobre foto, parede de fotos a
# subir, fecho) e cada uma vista a 15 m pelo metodo da 084. Os fotogramas do video de referencia
# ficam em saida/discussao/ponto5/fotogramas_referencia (t_<segundo>.jpg, tirados com o ffmpeg do
# video "Film End Credits _ 35 Cinematic Templates..." nos Downloads do Tiago).
# -*- coding: utf-8 -*-
"""Maquetes paradas dos creditos, a 1920x1080, e a mesma imagem vista a 15 metros.

Nao e render. Cada ficheiro e um fotograma desenhado com a Pillow para o Tiago ver
tamanhos e composicao. A "vista a 15 m" usa o metodo da decisao 084
(lettering/medir2.py): ecra de 2,50 m, 15 m, borrao gaussiano de 1,5 arcmin (20/30).
So le da FINAIS; escreve so nesta pasta.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

AQUI = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                    "saida", "discussao", "ponto5")
OUT = os.path.join(AQUI, "maquetes")
FINAIS = r"C:\casamento-video-media\FINAIS"
os.makedirs(OUT, exist_ok=True)
L, A = 1920, 1080
BOLD = r"C:\Windows\Fonts\arialbd.ttf"
PX_POR_ARCMIN = (math.radians(1 / 60.0) * 15000.0) / (2500.0 / 1920.0)
SIGMA = 1.5 * PX_POR_ARCMIN            # 5,0 px do ecra

FOTOS = {k: v for k, v in [
    (1, "2014_cLARA_E_TIAGO_30set.jpg"), (4, "20170916_164437.jpg"), (8, "20190627_164727.jpg"),
    (10, "21-31.jpg"), (16, "DSC00075.JPG"), (19, "82-1.JPG"), (20, "DSC02744.JPG"),
    (22, "2016_tIAGO_AMIGOS_FACULDADE.jpg"), (24, "DSC00780.JPG"), (32, "IMG_3993.JPG"),
    (33, "digitalizar0002.jpg"), (35, "11-20.jpg"), (39, "22-5.JPG"),
    (11, "2016_CLARA_TIAGO_AMIGOS_SECUNDARIO_2.jpg"), (23, "IMG-20260704-WA0009.jpg"),
    (27, "21-52.JPG"), (12, "11-12.JPG"), (45, "20170521_162505.jpg"), (3, "21-49-33.jpg"),
    (7, "IMG-20260614-WA0003.jpg"), (6, "2016_CLARA_TIAGO_AMIGOS_SECUNDARIO.jpg"),
    (34, "IMG-20181003-WA0000.jpg"), (42, "21-11-1.JPG"), (2, "WP_20161029_18_40_17_Pro.jpg")]}
_cache = {}


def foto(k):
    if k not in _cache:
        im = Image.open(os.path.join(FINAIS, FOTOS[k]))
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((2400, 2400))
        _cache[k] = im
    return _cache[k]


def cobrir(im, w, h, vies=0.35):
    r = max(w / im.width, h / im.height)
    t = im.resize((max(w, round(im.width * r)), max(h, round(im.height * r))), Image.LANCZOS)
    x = (t.width - w) // 2
    y = int((t.height - h) * vies)
    return t.crop((x, y, x + w, y + h))


def fonte(n):
    return ImageFont.truetype(BOLD, n)


def texto_espacado(d, xy_centro, texto, f, fill, espaco=0, ancora_y="top"):
    """Texto centrado em x com espacamento entre letras (tracking), como nos modelos."""
    larguras = [d.textlength(c, font=f) for c in texto]
    total = sum(larguras) + espaco * (len(texto) - 1)
    x = xy_centro[0] - total / 2
    for c, w in zip(texto, larguras):
        d.text((x, xy_centro[1]), c, font=f, fill=fill)
        x += w + espaco
    return total


def a_15m(im):
    return im.filter(ImageFilter.GaussianBlur(SIGMA))


def lado_a_lado(a, b, rot_a="1920x1080", rot_b="a 15 m (ecra 2,5 m, 20/30)"):
    esc = 0.5
    wa, ha = int(a.width * esc), int(a.height * esc)
    fol = Image.new("RGB", (wa * 2 + 30, ha + 56), (28, 28, 30))
    fol.paste(a.resize((wa, ha), Image.LANCZOS), (10, 46))
    fol.paste(b.resize((wa, ha), Image.LANCZOS), (20 + wa, 46))
    d = ImageDraw.Draw(fol)
    d.text((10, 10), rot_a, font=fonte(26), fill=(230, 230, 230))
    d.text((20 + wa, 10), rot_b, font=fonte(26), fill=(230, 230, 230))
    return fol


# ------------------------------------------------ 0. os modelos do video, a 15 m
def prova_modelos():
    base = os.path.join(AQUI, "fotogramas_referencia")
    tiras = []
    for nome, rot in [("t_038.5.jpg", "Modelo A: nomes entre filetes, corpo ~21 px a 1080"),
                      ("t_041.5.jpg", "Modelo B: banda emoldurada, corpo ~27 px a 1080"),
                      ("t_060.6.jpg", "Modelo G: bloco em preto, corpo ~22 px a 1080")]:
        im = Image.open(os.path.join(base, nome)).convert("RGB").resize((L, A), Image.LANCZOS)
        f = lado_a_lado(im, a_15m(im), rot, "o mesmo, visto a 15 m")
        tiras.append(f)
    W = tiras[0].width
    fol = Image.new("RGB", (W, sum(t.height for t in tiras)), (28, 28, 30))
    y = 0
    for t in tiras:
        fol.paste(t, (0, y)); y += t.height
    fol.save(os.path.join(OUT, "0_modelos_do_video_a_15m.jpg"), quality=86)


# ------------------------------------------------ 1. faixa entre filetes sobre a foto
def faixa_sobre_foto(k, rotulo, nomes, p_linha=1.0, a_rot=1.0, a_nom=1.0, sobe=0.0):
    im = cobrir(foto(k), L, A, vies=0.15)
    # a foto fica a 85%, e escurece de baixo para cima por tras do texto (como o fundo
    # escuro dos modelos, que as nossas fotos de dia nao tem)
    im = Image.blend(Image.new("RGB", (L, A), (0, 0, 0)), im, 0.85)
    cy = 872
    mascara = Image.new("L", (L, A), 0)
    md = ImageDraw.Draw(mascara)
    for y in range(A):
        v = 0 if y < 600 else min(205, int(205 * (y - 600) / 170))
        md.line([(0, y), (L, y)], fill=v)
    im = Image.composite(Image.new("RGB", (L, A), (0, 0, 0)), im, mascara)
    camada = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    meia = 700 * p_linha
    d.rectangle((L / 2 - meia, cy - 112, L / 2 + meia, cy - 109), fill=(255, 255, 255, 235))
    d.rectangle((L / 2 - meia, cy + 110, L / 2 + meia, cy + 113), fill=(255, 255, 255, 235))
    texto_espacado(d, (L / 2, cy - 92), rotulo, fonte(58), (205, 205, 212, int(255 * a_rot)), espaco=10)
    texto_espacado(d, (L / 2, cy - 12 + int(14 * (1 - sobe))), nomes, fonte(84), (255, 255, 255, int(255 * a_nom)), espaco=2)
    return Image.alpha_composite(im.convert("RGBA"), camada).convert("RGB")


def proposta1():
    im = faixa_sobre_foto(16, "OS PADRINHOS", "Nome Apelido  —  Nome Apelido")
    lado_a_lado(im, a_15m(im)).save(os.path.join(OUT, "1_faixa_sobre_foto.jpg"), quality=86)
    im.save(os.path.join(OUT, "1_faixa_sobre_foto_1080.jpg"), quality=90)
    # o movimento, em quatro tempos
    passos = [("0,0 s  a foto entra, zoom lento", dict(p_linha=0.0, a_rot=0, a_nom=0)),
              ("0,4 s  os filetes abrem do centro", dict(p_linha=0.55, a_rot=0, a_nom=0)),
              ("0,8 s  o rotulo acende", dict(p_linha=1.0, a_rot=1.0, a_nom=0.35, sobe=0.3)),
              ("1,2 s a 4 s  os nomes pousam e ficam", dict(p_linha=1.0, a_rot=1.0, a_nom=1.0, sobe=1.0))]
    w, h = 640, 360
    fol = Image.new("RGB", (w * 2 + 30, (h + 44) * 2 + 10), (28, 28, 30))
    for i, (rot, kw) in enumerate(passos):
        q = faixa_sobre_foto(16, "OS PADRINHOS", "Nome Apelido  —  Nome Apelido", **kw).resize((w, h), Image.LANCZOS)
        x = 10 + (i % 2) * (w + 10); y = 10 + (i // 2) * (h + 44)
        ImageDraw.Draw(fol).text((x, y), rot, font=fonte(24), fill=(230, 230, 230))
        fol.paste(q, (x, y + 34))
    fol.save(os.path.join(OUT, "1_faixa_sobre_foto_movimento.jpg"), quality=86)


# ------------------------------------------------ 2. rolar classico com fotos dos lados
def moldura(im, w, h, borda=8):
    c = cobrir(im, w - 2 * borda, h - 2 * borda, vies=0.3)
    m = Image.new("RGB", (w, h), (240, 240, 242))
    m.paste(c, (borda, borda))
    return m


def proposta2():
    tela = Image.new("RGB", (L, A), (6, 6, 8))
    d = ImageDraw.Draw(tela)
    # fotos: esquerda e direita, desencontradas meia altura, como se tivessem entrado por baixo
    fw, fh = 520, 390
    esq = [(19, -250), (4, 190), (24, 630)]
    dir_ = [(1, -30), (16, 410), (35, 850)]
    for k, y in esq:
        tela.paste(moldura(foto(k), fw, fh), (70, y))
    for k, y in dir_:
        tela.paste(moldura(foto(k), fw, fh), (L - 70 - fw, y))
    # coluna do meio: rotulo 58 cinzento, nomes 72 brancos, centrados
    cx = L / 2
    y = -40
    blocos = [("OS AVÓS", ["Nome Apelido", "Nome Apelido"]),
              ("OS TIOS", ["Nome e Nome", "Nome e Nome"]),
              ("OS PRIMOS", ["Nome", "Nome", "Nome"])]
    for rot, nomes in blocos:
        texto_espacado(d, (cx, y), rot, fonte(58), (170, 170, 178), espaco=8)
        y += 84
        for n in nomes:
            texto_espacado(d, (cx, y), n, fonte(72), (255, 255, 255))
            y += 92
        y += 70
    lado_a_lado(tela, a_15m(tela)).save(os.path.join(OUT, "2_rolar_com_fotos.jpg"), quality=86)
    tela.save(os.path.join(OUT, "2_rolar_com_fotos_1080.jpg"), quality=90)


# ------------------------------------------------ 3. parede de fotos a subir, faixa fixa
def proposta3(colunas=4):
    tela = Image.new("RGB", (L, A), (6, 6, 8))
    folga = 22
    fw = (L - folga * (colunas + 1)) // colunas
    fh = int(fw * 0.75)
    ordem = [19, 4, 8, 10, 16, 1, 20, 22, 24, 32, 33, 35, 39, 11, 23, 27, 12, 45, 3, 7, 6, 34, 42, 2]
    k = 0
    for c in range(colunas):
        # colunas desencontradas: a parede nao e uma grelha de escritorio
        y = -int(fh * (0.15 + 0.45 * (c % 2)))
        while y < A:
            im = cobrir(foto(ordem[k % len(ordem)]), fw, fh, vies=0.3)
            tela.paste(im, (folga + c * (fw + folga), y))
            k += 1
            y += fh + folga
    # faixa fixa ao centro, a mesma da proposta 1, com o rotulo que muda por grupo
    cy = A // 2
    faixa = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(faixa)
    d.rectangle((0, cy - 95, L, cy + 95), fill=(0, 0, 0, 200))
    d.rectangle((L / 2 - 560, cy - 95, L / 2 + 560, cy - 92), fill=(255, 255, 255, 235))
    d.rectangle((L / 2 - 560, cy + 92, L / 2 + 560, cy + 95), fill=(255, 255, 255, 235))
    texto_espacado(d, (L / 2, cy - 44), "A FAMÍLIA", fonte(84), (255, 255, 255, 255), espaco=14)
    tela = Image.alpha_composite(tela.convert("RGBA"), faixa).convert("RGB")
    nome = "3_parede_de_fotos_%dcol" % colunas
    lado_a_lado(tela, a_15m(tela)).save(os.path.join(OUT, nome + ".jpg"), quality=86)
    tela.save(os.path.join(OUT, nome + "_1080.jpg"), quality=90)


# ------------------------------------------------ fim comum: bloco em preto e saida desfocada
def cartao_final(p_nomes=1.0, p_data=1.0, sai=0.0):
    tela = Image.new("RGB", (L, A), (0, 0, 0))
    d = ImageDraw.Draw(tela)
    cy = A // 2
    texto_espacado(d, (L / 2, cy - 110), "CLARA & TIAGO", fonte(132), (255, 255, 255), espaco=12)
    d.rectangle((L / 2 - 300 * p_data, cy + 60, L / 2 + 300 * p_data, cy + 63), fill=(255, 255, 255))
    cor = int(200 * p_data)
    texto_espacado(d, (L / 2, cy + 90), "4 · 10 · 2026", fonte(58), (cor, cor, cor + 6 if cor else 0), espaco=10)
    if sai > 0:
        tela = tela.filter(ImageFilter.GaussianBlur(14 * sai))
        tela = Image.blend(tela, Image.new("RGB", (L, A), (0, 0, 0)), min(1.0, sai))
    return tela


def fim():
    passos = [("0 s  o nome acende", cartao_final(p_data=0.0)),
              ("0,8 s  o filete abre e a data acende", cartao_final(p_data=1.0)),
              ("6 s  desfoca e escurece (o fecho do modelo J)", cartao_final(sai=0.45)),
              ("8,5 s  preto; a musica acaba com ele", cartao_final(sai=1.0))]
    w, h = 640, 360
    fol = Image.new("RGB", (w * 2 + 30, (h + 44) * 2 + 10), (28, 28, 30))
    for i, (rot, q) in enumerate(passos):
        x = 10 + (i % 2) * (w + 10); y = 10 + (i // 2) * (h + 44)
        ImageDraw.Draw(fol).text((x, y), rot, font=fonte(24), fill=(230, 230, 230))
        fol.paste(q.resize((w, h), Image.LANCZOS), (x, y + 34))
    fol.save(os.path.join(OUT, "4_fim_bloco_em_preto.jpg"), quality=86)
    im = cartao_final()
    lado_a_lado(im, a_15m(im)).save(os.path.join(OUT, "4_fim_bloco_em_preto_a_15m.jpg"), quality=86)


if __name__ == "__main__":
    print("1 arcmin = %.2f px; sigma = %.2f px" % (PX_POR_ARCMIN, SIGMA))
    prova_modelos()
    proposta1()
    proposta2()
    proposta3(4)
    proposta3(5)
    fim()
    print(sorted(os.listdir(OUT)))
