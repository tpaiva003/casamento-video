# -*- coding: utf-8 -*-
"""Transplante da parte de baixo da cara verdadeira, com a pele inteira (volume incluido).

Diferenca para o tirar_mascara.py (que o Tiago rejeitou, "parecem ETs"): ali passava-se so
o pormenor fino, com o contraste a menos de metade, e as caras perdiam o volume. Aqui a
fonte vai inteira, com as suas sombras e relevo, e so se lhe acerta o tom (media e desvio
por canal em Lab) pela pele que se ve nas duas fotos: testa, nariz, por baixo dos olhos. A
costura resolve-se por Poisson com os gradientes INTEIROS da fonte (clonagem normal): so se
soma uma correcao suave que leva a borda ao valor da foto com mascara.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "tm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tirar_mascara.py"))
tm = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(tm)

D = tm.D
AQUI = os.path.dirname(os.path.abspath(__file__))


def para_lab(rgb):
    """RGB 0-255 -> Lab aproximado (sRGB linearizado, D65)."""
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116.0)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1]); b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def de_lab(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116.0; fx = fy + a / 500.0; fz = fy - b / 200.0
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f > 0.2069, f ** 3, (f - 16 / 116.0) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    M = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    c = xyz @ M.T
    c = np.where(c > 0.0031308, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255.0, 0, 255)


class TPS:
    """Thin-plate spline do alvo para a fonte, pelos pares de pontos (alvo -> fonte)."""
    def __init__(self, alvo_pts, fonte_pts, suave=0.0):
        p = np.asarray(alvo_pts, float); q = np.asarray(fonte_pts, float)
        n = len(p)
        def U(r2):
            return np.where(r2 > 0, r2 * np.log(r2 + 1e-12), 0.0)
        d2 = ((p[:, None, :] - p[None, :, :]) ** 2).sum(-1)
        K = U(d2) + suave * np.eye(n)
        Pm = np.hstack([np.ones((n, 1)), p])
        L = np.zeros((n + 3, n + 3)); L[:n, :n] = K; L[:n, n:] = Pm; L[n:, :n] = Pm.T
        Y = np.vstack([q, np.zeros((3, 2))])
        self.W = np.linalg.solve(L, Y); self.p = p; self.U = U

    def __call__(self, xs, ys):
        pts = np.stack([xs.ravel(), ys.ravel()], -1)
        d2 = ((pts[:, None, :] - self.p[None, :, :]) ** 2).sum(-1)
        n = len(self.p)
        out = self.U(d2) @ self.W[:n] + self.W[n] + pts @ self.W[n + 1:]
        return out[:, 0].reshape(xs.shape), out[:, 1].reshape(xs.shape)


def amostra_tps(img, tps, caixa):
    x0, y0, x1, y1 = caixa
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    sx, sy = tps(xs, ys)
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]
    return (img[iy, ix] * (1 - fx) * (1 - fy) + img[iy, ix + 1] * fx * (1 - fy)
            + img[iy + 1, ix] * (1 - fx) * fy + img[iy + 1, ix + 1] * fx * fy), sx, sy


def correr(pontos, saida, so=None):
    alvo = tm.abre(tm.ALVO)
    res = alvo.copy()
    for nome, P in pontos.items():
        if so and nome != so:
            continue
        fonte = tm.abre(os.path.join(D, P["fonte"]))
        M = tm.afim(P["fonte_pts"] + [P["fonte_queixo"]], P["alvo_pts"] + [P["alvo_queixo"]])
        x0, y0, x1, y1 = P["caixa"]
        A = alvo[y0:y1, x0:x1]
        if P.get("tps"):
            tps = TPS([t for t, f in P["tps"]], [f for t, f in P["tps"]], P.get("tps_suave", 0.0))
            F, sx_t, sy_t = amostra_tps(fonte, tps, P["caixa"])
        else:
            F = tm.amostra(fonte, M, P["caixa"])
        R = tm.regiao(P, P["caixa"], A)
        # Zona de pele para acertar o tom: os retangulos "pele" (no referencial do alvo).
        Z = np.zeros(R.shape, bool)
        for px0, py0, px1, py1 in P["pele"]:
            Z[py0 - y0:py1 - y0, px0 - x0:px1 - x0] = True
        Z &= ~R
        la, lf = para_lab(A), para_lab(F)
        ma, sa = la[Z].mean(0), la[Z].std(0)
        mf, sf = lf[Z].mean(0), lf[Z].std(0)
        ganho = np.clip(sa / np.maximum(sf, 1e-3), P.get("ganho_min", 0.6), 1.3)
        ganho[1:] = np.minimum(ganho[1:], P.get("ganho_cor_max", 1.0))   # a cor nunca se reforca
        lf2 = (lf - mf) * ganho + ma
        # DUAS ANCORAS PARA A LUZ (L): a pele (testa) e uma zona escura que se ve nas duas
        # (a barba por baixo da mascara, nele). Uma reta por esses dois pontos acerta o claro
        # e o escuro ao mesmo tempo; so com a pele, a barba dele caia no preto.
        if P.get("escuro"):
            E = np.zeros(R.shape, bool)
            for ex0, ey0, ex1, ey1 in P["escuro"]:
                E[ey0 - y0:ey1 - y0, ex0 - x0:ex1 - x0] = True
            E &= ~R
            La1, Lf1 = la[Z][:, 0].mean(), lf[Z][:, 0].mean()
            La2, Lf2 = la[E][:, 0].mean(), lf[E][:, 0].mean()
            if P.get("escuro_fonte"):
                # a mesma materia (barba) medida na fonte, no sitio dela: o que cai debaixo
                # da zona do alvo, depois de alinhado, pode ser gola ou pescoco
                lfonte = para_lab(fonte)
                Lf2 = np.concatenate([lfonte[b0:b1, a0:a1, 0].ravel()
                                      for a0, b0, a1, b1 in P["escuro_fonte"]]).mean()
            g = (La1 - La2) / max(Lf1 - Lf2, 1e-3)
            lf2[..., 0] = (lf[..., 0] - Lf1) * g + La1
            print("   L por duas ancoras: pele %.1f->%.1f, escuro %.1f->%.1f, ganho %.2f"
                  % (Lf1, La1, Lf2, La2, g))
        # Retoques de cor pedidos pelos avaliadores: menos rosado e um pouco mais de luz.
        if P.get("menos_rosa"):
            lf2[..., 1] = ma[1] + (lf2[..., 1] - ma[1]) * P["menos_rosa"]
        if P.get("clarear"):
            lf2[..., 0] = lf2[..., 0] * P["clarear"]
        F2 = de_lab(lf2)
        # MODO PROPORCIONAL: a sombra multiplica a luz, nao a desloca. Escala-se cada canal da
        # fonte pela razao entre a pele do alvo e a da fonte, e acerta-se o nivel do preto
        # (o mais escuro da cara que se ve no alvo). A barba fica tao mais escura do que a pele
        # como era na fonte, sem cair no preto cortado.
        if P.get("modo") == "proporcional":
            pa, pf = A[Z].mean(0), F[Z].mean(0)
            vis = np.zeros(R.shape, bool); vis[: max(1, int(R.shape[0] * 0.25))] = True
            vis &= ~R
            preto_a = np.percentile(A[vis], 2, axis=0)
            preto_f = np.percentile(F[Vf_pre > 0.5], 2, axis=0) if False else np.percentile(F[R], 2, axis=0)
            k = (pa - preto_a) / np.maximum(pf - preto_f, 1e-3)
            # A luz na sombra e difusa: as sombras da fonte (sol) encolhem com uma gama < 1.
            gama = P.get("gama", 1.0)
            r_ = np.clip((F - preto_f) / np.maximum(pf - preto_f, 1e-3), 0, None)
            F2 = np.clip(preto_a + (pa - preto_a) * r_ ** gama, 0, 255)
            print("   proporcional: k %s, preto alvo %s" % (np.round(k, 2), np.round(preto_a)))
        # Onde a fonte nao e cara (fundo, cabelo dela), nao se cola: fica a luz da borda.
        Mi = M
        ys, xs = np.mgrid[y0:y1, x0:x1]
        sx = Mi[0, 0] * xs + Mi[0, 1] * ys + Mi[0, 2]
        sy = Mi[1, 0] * xs + Mi[1, 1] * ys + Mi[1, 2]
        if P.get("tps"):
            sx, sy = sx_t, sy_t
        im = Image.new("L", (fonte.shape[1], fonte.shape[0]), 0)
        ImageDraw.Draw(im).polygon([tuple(p) for p in P["fonte_cara"]], fill=255)
        vm = np.asarray(im) > 127
        V = vm[np.clip(sy.round().astype(int), 0, fonte.shape[0] - 1),
               np.clip(sx.round().astype(int), 0, fonte.shape[1] - 1)]
        Vf = tm.gauss(V.astype(np.float64)[..., None], P.get("borda_cara", 2.0))[..., 0]
        H = tm.poisson(A, np.zeros_like(A), R)          # a luz da borda, lisa
        G = Vf[..., None] * F2 + (1 - Vf[..., None]) * H  # guia: a cara verdadeira inteira
        O = tm.poisson(A, G, R)
        # NITIDEZ E GRAO DA FOTO. A fonte, reduzida, sai mais lisa do que a testa e os olhos,
        # que tem o grao e os blocos do JPEG do WhatsApp: realca-se um pouco o pormenor da zona
        # nova (labios, pelos da barba) e junta-se grao ate o pormenor fino ficar ao nivel da
        # testa, medido nas duas.
        if P.get("grao", True):
            Z2 = Z.copy()
            hp_a = (A - tm.gauss(A, 1.0)).mean(axis=2)
            hp_o = (O - tm.gauss(O, 1.0)).mean(axis=2)
            O = O + P.get("realce", 0.5) * (O - tm.gauss(O, 1.2)) * R[..., None]
            hp_o2 = (O - tm.gauss(O, 1.0)).mean(axis=2)
            alvo_std = hp_a[Z2].std(); tem = hp_o2[R].std()
            falta = np.sqrt(max(alvo_std ** 2 - tem ** 2, 0.0))
            rng = np.random.default_rng(7)
            ruido = rng.normal(0, falta, O.shape[:2])[..., None] * np.array([1.0, 1.0, 1.0])
            ruido = ruido + rng.normal(0, falta * 0.35, O.shape)
            mR = tm.gauss(R.astype(np.float64)[..., None], 1.0)
            O = np.clip(O + ruido * mR, 0, 255)
            print("   grao: pormenor da testa %.2f, da zona %.2f -> junta %.2f" % (alvo_std, tem, falta))
        # OS DENTES: os intervalos escuros entre eles, na sombra, liam-se como falhas.
        if P.get("dentes"):
            dx0, dy0, dx1, dy1 = P["dentes"]
            sub = O[dy0 - y0:dy1 - y0, dx0 - x0:dx1 - x0]
            med = np.asarray(Image.fromarray(np.clip(sub, 0, 255).astype(np.uint8))
                             .filter(ImageFilter.MedianFilter(5)), dtype=np.float64)
            lum = sub.mean(axis=2); lmed = med.mean(axis=2)
            w = np.clip((lmed - lum - 6) / 20.0, 0, 1)[..., None]
            O[dy0 - y0:dy1 - y0, dx0 - x0:dx1 - x0] = sub * (1 - w) + med * w * 0.97
        res[y0:y1, x0:x1] = O
        print("%s: fonte %s, ganho Lab %s" % (nome, P["fonte"][:12], np.round(ganho, 2)))
    Image.fromarray(np.round(res).astype(np.uint8)).save(saida)
    return res


if __name__ == "__main__":
    pontos = json.load(open(os.path.join(AQUI, sys.argv[1]), encoding="utf-8"))
    correr(pontos, os.path.join(AQUI, sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None)
