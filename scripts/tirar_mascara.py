# -*- coding: utf-8 -*-
"""Tira as mascaras da foto "WhatsApp Image 2026-09-21 at 12.06.46" com as caras verdadeiras.

Tarefa paralela ao video, pedida pelo Tiago a 22 de setembro: "Precisa de ter uma foto com
qualidade deles sem a mascara apenas, mantendo tudo o resto e o espaco que a mascara tapa
deve ser igual as fotos deles."

NADA E INVENTADO. A parte de baixo de cada cara vem de outra foto dele, sem mascara:
  - ele: a das 14.25.05, do mesmo dia (mesma barba), de frente e com luz por igual;
  - ela: a 530093408..., de frente e a sombra de uma arvore. A do mesmo dia (14.24.57)
    tem sol de lado, e a aresta da sombra ao longo do nariz ficava como uma mancha escura
    na bochecha, que nenhum acerto de luz tirava sem achatar a cara.
E o contrario das redes que redesenham rostos (GFPGAN, CodeFormer), que o projeto proibe.

COMO: cada fonte e alinhada ao alvo por tres pontos (os dois olhos e o queixo, marcados a
mao numa grelha; o queixo do alvo esta por baixo da mascara e estima-se pela forma dela).
Passa so o pormenor da cara verdadeira (a imagem menos o seu desfoque de sigma px), com o
contraste acertado a zona dos olhos, que se ve nas duas fotos; a luz grande vem da propria
foto com mascara, por fusao de Poisson a partir da borda. Dentro do contorno da cara da
fonte, a base e a cor da pele do alvo (ela) ou a luz da borda (ele, por causa da barba);
fora dele (fundo, brinco), so a luz da borda. Junto aos olhos nao entra pormenor da fonte.
A borda da zona cresce sobre os pixeis azulados, para nunca ser mascara.

Uso:  py -3.11 scripts/tirar_mascara.py            escreve em gerados\sem_mascara
      py -3.11 scripts/tirar_mascara.py --ver      e as folhas de verificacao ao lado
Os pontos estao em data/sem_mascara_pontos.json. Nunca escreve por cima de um ficheiro.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = r"C:\casamento-video-media\gerados\sem_mascara"
D = r"C:\casamento-video-media\trabalho\04-Tratamento_Imagem_fora_video"
ALVO = os.path.join(D, "WhatsApp Image 2026-09-21 at 12.06.46.jpeg")
FONTE = os.path.join(D, "WhatsApp Image 2026-09-21 at 14.24.57.jpeg")

PESSOAS = json.load(open(os.path.join(REPO, "data", "sem_mascara_pontos.json"), encoding="utf-8"))


def abre(c):
    return np.asarray(ImageOps.exif_transpose(Image.open(c)).convert("RGB"), dtype=np.float64)


def afim(src_pts, dst_pts):
    """Matriz 2x3 que leva pontos do alvo (dst) a fonte (src), afim por minimos quadrados."""
    A = np.array([[x, y, 1] for x, y in dst_pts], dtype=np.float64)
    mx = np.linalg.lstsq(A, np.array([p[0] for p in src_pts], dtype=np.float64), rcond=None)[0]
    my = np.linalg.lstsq(A, np.array([p[1] for p in src_pts], dtype=np.float64), rcond=None)[0]
    return np.vstack([mx, my])


def gauss(a, sigma):
    """Desfoque gaussiano separavel, por canal."""
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    out = a.copy()
    for eixo in (0, 1):
        pad = [(0, 0)] * a.ndim; pad[eixo] = (r, r)
        b = np.pad(out, pad, mode="edge")
        acc = np.zeros_like(out)
        for i, w in enumerate(k):
            sl = [slice(None)] * a.ndim
            sl[eixo] = slice(i, i + out.shape[eixo])
            acc += w * b[tuple(sl)]
        out = acc
    return out


def semelhanca(src_pts, dst_pts):
    """Matriz 2x3 que leva pontos do alvo (dst) a fonte (src), por minimos quadrados.

    Semelhanca: x' = a x - b y + tx, y' = b x + a y + ty.
    """
    A, B = [], []
    for (xs, ys), (xd, yd) in zip(src_pts, dst_pts):
        A.append([xd, -yd, 1, 0]); B.append(xs)
        A.append([yd, xd, 0, 1]); B.append(ys)
    a, b, tx, ty = np.linalg.lstsq(np.array(A), np.array(B), rcond=None)[0]
    return np.array([[a, -b, tx], [b, a, ty]])


def amostra(img, M, caixa):
    """A fonte vista no referencial do alvo, dentro da caixa (x0,y0,x1,y1), bilinear."""
    x0, y0, x1, y1 = caixa
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    sx = M[0, 0] * xs + M[0, 1] * ys + M[0, 2]
    sy = M[1, 0] * xs + M[1, 1] * ys + M[1, 2]
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]
    p = (img[iy, ix] * (1 - fx) * (1 - fy) + img[iy, ix + 1] * fx * (1 - fy)
         + img[iy + 1, ix] * (1 - fx) * fy + img[iy + 1, ix + 1] * fx * fy)
    return p


def poisson(alvo, fonte, dentro, iters=3000):
    """Resolve Laplaciano(f) = Laplaciano(fonte) dentro, com f = alvo na borda. Por canal, CG."""
    out = alvo.copy()
    m = dentro.astype(bool)
    viz = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def desloca(a, dy, dx):
        r = np.zeros_like(a)
        h, w = a.shape
        r[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
            a[max(-dy, 0):h - max(dy, 0), max(-dx, 0):w - max(dx, 0)]
        return r

    for c in range(3):
        S = fonte[..., c]; T = alvo[..., c]
        b = np.zeros_like(S)
        for dy, dx in viz:
            Sq = desloca(S, dy, dx)
            mq = desloca(m.astype(np.float64), dy, dx)
            Tq = desloca(T, dy, dx)
            b += S - Sq
            b += (1 - mq) * Tq          # vizinho fora da regiao: valor fixo do alvo
        b *= m

        def A(f):
            r = 4 * f
            for dy, dx in viz:
                r -= desloca(f * m, dy, dx)
            return r * m

        f = T * m
        r = b - A(f); p = r.copy(); rs = np.sum(r * r)
        for _ in range(iters):
            Ap = A(p)
            al = rs / max(np.sum(p * Ap), 1e-12)
            f += al * p; r -= al * Ap
            rn = np.sum(r * r)
            if rn < 1e-6 * m.sum():
                break
            p = r + (rn / rs) * p; rs = rn
        out[..., c] = np.where(m, f, T)
    return np.clip(out, 0, 255)


def regiao(forma, caixa, alvo_crop):
    """A zona a substituir, na caixa: poligono da mascara (+ tiras), dilatado."""
    x0, y0, x1, y1 = caixa
    im = Image.new("L", (x1 - x0, y1 - y0), 0)
    d = ImageDraw.Draw(im)
    for poli in forma["poligonos"]:
        d.polygon([(x - x0, y - y0) for x, y in poli], fill=255)
    for (xa, ya, xb, yb, larg) in forma.get("tiras", []):
        d.line([(xa - x0, ya - y0), (xb - x0, yb - y0)], fill=255, width=larg)
    dil = forma.get("dilata", 5)
    if dil:
        im = im.filter(ImageFilter.MaxFilter(dil if dil % 2 else dil + 1))
    R = np.asarray(im) > 127
    # A BORDA TEM DE SER PELE, CABELO OU FUNDO, nunca mascara: um pixel azul na borda
    # tinge a cara toda por dentro. Cresce-se a zona sobre os pixeis azulados da borda,
    # so na metade de cima (em baixo ha a camisa branca, que a sombra tambem faz azulada).
    a = alvo_crop
    azul = (a[..., 2] > a[..., 0] + 8) & (a[..., 2] >= a[..., 1]) & (a.mean(axis=2) > 70)
    alto = np.zeros_like(R); alto[: int(R.shape[0] * forma.get("cresce_ate", 0.6))] = True
    for _ in range(forma.get("cresce", 8)):
        viz = np.asarray(Image.fromarray((R * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 127
        borda = viz & ~R
        novo = borda & azul & alto
        if not novo.any():
            break
        R = R | novo
    return R


def contraste(alvo_crop, fonte_crop, zona):
    """Quanto encolher o contraste da fonte para bater com o alvo, na zona dos olhos."""
    la = alvo_crop[zona].mean(axis=1); lf = fonte_crop[zona].mean(axis=1)
    return float(np.clip(la.std() / max(lf.std(), 1e-6), 0.4, 1.2))


def main():
    alvo = abre(ALVO)
    fontes = {}
    res = alvo.copy()
    so = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    ver = "--ver" in sys.argv
    os.makedirs(SAIDA, exist_ok=True)
    for nome, P in PESSOAS.items():
        if so and nome != so:
            continue
        if "alvo_queixo" in P:
            M = afim(P["fonte_pts"] + [P["fonte_queixo"]], P["alvo_pts"] + [P["alvo_queixo"]])
        else:
            M = semelhanca(P["fonte_pts"], P["alvo_pts"])
        esc = np.hypot(M[0, 0], M[1, 0])
        rot = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
        nome_f = P.get("fonte", FONTE)
        if nome_f not in fontes:
            fontes[nome_f] = abre(os.path.join(D, nome_f) if not os.path.isabs(nome_f) else nome_f)
        fonte = fontes[nome_f]
        cx = P["caixa"]
        x0, y0, x1, y1 = cx
        A = alvo[y0:y1, x0:x1]
        F = amostra(fonte, M, cx)
        R = regiao(P, cx, A)
        # a zona dos olhos, visivel nas duas, para medir contraste e cor
        zx0, zy0, zx1, zy1 = P["zona_olhos"]
        Z = np.zeros(R.shape, bool); Z[zy0 - y0:zy1 - y0, zx0 - x0:zx1 - x0] = True
        Z &= ~R
        # SO O PORMENOR DA CARA VERDADEIRA. A luz da foto das 14.24 e sol direto, e a do
        # alvo e sombra: tira-se a luz grande da fonte (o desfoque de sigma px) e fica o
        # pormenor (boca, barba, sombras pequenas); a luz grande vem da borda do alvo, pelo
        # Poisson. O contraste do pormenor acerta-se pela zona dos olhos, que se ve nas duas.
        sig = P.get("sigma", 8.0)
        Fhp = F - gauss(F, sig)
        Ahp = A - gauss(A, sig)
        la = Ahp[Z].mean(axis=1).std(); lf = Fhp[Z].mean(axis=1).std()
        k = float(np.clip(la / max(lf, 1e-6), 0.3, 1.5)) * P.get("contraste_extra", 1.0)
        # Onde a fonte nao e cara (fundo, brinco), nao ha pormenor: so a luz da borda.
        V = np.ones(R.shape, bool)
        if "fonte_cara" in P:
            Mi = np.vstack([M, [0, 0, 1]])
            ys, xs = np.mgrid[y0:y1, x0:x1]
            sx = Mi[0, 0] * xs + Mi[0, 1] * ys + Mi[0, 2]
            sy = Mi[1, 0] * xs + Mi[1, 1] * ys + Mi[1, 2]
            im = Image.new("L", (fonte.shape[1], fonte.shape[0]), 0)
            ImageDraw.Draw(im).polygon([tuple(p) for p in P["fonte_cara"]], fill=255)
            vm = np.asarray(im) > 127
            V = vm[np.clip(sy.round().astype(int), 0, fonte.shape[0] - 1),
                   np.clip(sx.round().astype(int), 0, fonte.shape[1] - 1)]
            Vf = gauss(V.astype(np.float64)[..., None], 1.5)[..., 0]
        else:
            Vf = V.astype(np.float64)
        # O PORMENOR VAI SOBRETUDO EM LUZ: o relevo (Y) inteiro, a cor (Cb, Cr) a meio, que
        # chega para os labios sem trazer o frio da sombra do sol da outra foto. Os picos
        # (a aresta dura entre sol e sombra) sao amaciados.
        Yw = np.array([0.299, 0.587, 0.114])
        Y = Fhp @ Yw
        C = Fhp - Y[..., None]
        teto = P.get("teto", 18.0)
        Y = teto * np.tanh(Y * k / teto)
        F2 = (Y[..., None] + C * k * P.get("cor", 0.5)) * Vf[..., None]
        # JUNTO AOS OLHOS NAO ENTRA PORMENOR DA FONTE: as olheiras e a sombra do olho da
        # outra foto, um pixel ao lado, liam-se como uma mancha. Rampa de 0 a 1 entre as
        # duas alturas (em pixeis do alvo).
        if P.get("rampa"):
            ya, yb = P["rampa"]
            yy = np.arange(y0, y1)[:, None]
            w = np.clip((yy - ya) / float(yb - ya), 0, 1)
            F2 = F2 * (w * w * (3 - 2 * w))[..., None]
        # A BASE: dentro do contorno da cara verdadeira, a cor da pele do alvo (medida por
        # baixo dos olhos); fora dele, o que a borda do alvo da (cabelo, pescoco). Sem isto
        # o cabelo escuro dos lados puxava a cara toda para baixo por dentro.
        if P.get("pele"):
            amostras = np.concatenate([A[py0 - y0:py1 - y0, px0 - x0:px1 - x0].reshape(-1, 3)
                                       for px0, py0, px1, py1 in P["pele"]])
            cor_pele = np.median(amostras, axis=0) * P.get("pele_ganho", 1.0)
            H = poisson(A, np.zeros_like(A), R)
            B = Vf[..., None] * cor_pele + (1 - Vf[..., None]) * H
            F2 = F2 + B
        O = poisson(A, F2, R)
        # A COR DA PELE, DEPOIS DA LUZ. O Poisson acerta a luz pela borda, mas a cor dos
        # lados vem das orelhas a sombra e do fundo, e saia cinzento-azulada. Dentro da
        # zona, a cor (Cb, Cr) puxa-se a meio caminho para a da pele do alvo; a luz (Y)
        # fica como estava. Na borda nao se mexe, para nao haver costura.
        if P.get("pele_cor"):
            am = np.concatenate([A[py0 - y0:py1 - y0, px0 - x0:px1 - x0].reshape(-1, 3)
                                 for px0, py0, px1, py1 in P["pele_cor"]])
            Yw = np.array([0.299, 0.587, 0.114])
            pele = np.median(am, axis=0); pele_c = pele - pele @ Yw
            Yo = O @ Yw; Co = O - Yo[..., None]
            dist = R.astype(np.float64)
            for _ in range(4):
                dist = gauss(dist[..., None], 1.5)[..., 0]
            b = np.clip((dist - 0.5) * 2.5, 0, 1) * P.get("pele_cor_forca", 0.5)
            Cn = Co * (1 - b[..., None]) + pele_c * b[..., None]
            O = np.where(R[..., None], np.clip(Yo[..., None] + Cn, 0, 255), O)
        res[y0:y1, x0:x1] = O
        print("%s: escala %.3f (fonte->alvo %.3f), rotacao %.1f graus, contraste x%.2f, %d px"
              % (nome, esc, 1 / esc, rot, k, R.sum()))
        if not ver:
            continue
        # folhas de verificacao
        z = 4
        def grande(a):
            return Image.fromarray(a.astype(np.uint8)).resize(((x1 - x0) * z, (y1 - y0) * z), Image.LANCZOS)
        mistura = (A * 0.5 + F * 0.5)
        contorno = A.copy(); borda = R & ~np.asarray(Image.fromarray((R * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))).astype(bool)
        contorno[borda] = [255, 255, 0]
        tiras = [grande(A), grande(mistura), grande(contorno), grande(O)]
        folha = Image.new("RGB", (tiras[0].width * 4 + 30, tiras[0].height), (30, 30, 30))
        for i, t in enumerate(tiras):
            folha.paste(t, (i * (t.width + 10), 0))
        folha.save(novo(os.path.join(SAIDA, "verificacao_%s.png" % nome)))
    if so:
        return
    final = novo(os.path.join(SAIDA, "WhatsApp Image 2026-09-21 at 12.06.46 sem mascara.jpg"))
    Image.fromarray(np.round(res).astype(np.uint8)).save(final, quality=95, subsampling=0)
    print("Escrito: %s" % final)


def novo(caminho):
    """O caminho, ou com _2, _3... se ja existir: nunca por cima de um ficheiro."""
    base, ext = os.path.splitext(caminho)
    k = 2
    while os.path.exists(caminho):
        caminho = "%s_%d%s" % (base, k, ext)
        k += 1
    return caminho


if __name__ == "__main__":
    main()
