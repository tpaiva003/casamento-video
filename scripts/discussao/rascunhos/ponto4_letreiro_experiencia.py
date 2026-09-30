# RASCUNHO do ponto 4 (os separadores), guardado a 29 de setembro a partir da pasta temporaria da
# sessao. Foi daqui que sairam o letreiro quente do comum.py (nomes dos bebes, 092) e a proposta dos
# separadores novos: compara o cartao de hoje com o letreiro, mede a legibilidade a 15 m e o custo.
# Uso: py -3.11 scripts/discussao/rascunhos/ponto4_letreiro_experiencia.py [pasta de saida]
# Omissao: saida/discussao/ponto4/experiencia. Le fotos da FINAIS; nao escreve mais nada.
# Experiencia fora do repositorio: o letreiro do titulo de Oppenheimer, feito com Pillow,
# ao lado do cartao que o render desenha hoje. Nada aqui toca no render nem na media.
import os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), "saida", "discussao", "ponto4", "experiencia")
os.makedirs(OUT, exist_ok=True)
FIN = r"C:\casamento-video-media\FINAIS"
L, A, FPS = 1920, 1080, 25
ARIALBD = r"C:\Windows\Fonts\arialbd.ttf"
SS = 2  # supersample da mascara do texto


# ------------------------------------------------------------------ o cartao de hoje
def cartao_atual(texto):
    """Igual ao render.cartao() para um texto de uma linha: Arial Bold 78, quase branco."""
    base = Image.new("RGB", (L, A), (8, 8, 10))
    d = ImageDraw.Draw(base)
    f = ImageFont.truetype(ARIALBD, 78)
    w = d.textbbox((0, 0), texto, font=f)[2]
    altura_linha = int(78 * 1.4)
    d.text(((L - w) / 2, (A - altura_linha) / 2), texto, font=f, fill=(238, 238, 244))
    return base


# ------------------------------------------------------------------ o letreiro novo
def mascara(linhas, tamanho, tracking_em, entrelinha=1.45):
    """Mascara L a SS vezes, letra a letra, com espacamento largo. Devolve (mascara, caixa)."""
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


def textura_quente(W, H, seed):
    """Enchimento: branco quente em cima, champanhe em baixo, com manchas lentas.
    O chao de brilho e alto de proposito: nenhuma letra fica escura (e o que falha no tutorial)."""
    rng = np.random.default_rng(seed)
    baixa = rng.random((5, 16))
    baixa = np.asarray(Image.fromarray((baixa * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                       dtype=np.float32) / 255.0
    grad = np.linspace(1.0, 0.0, H, dtype=np.float32)[:, None]
    v = np.clip(0.5 * baixa + 0.5 * grad, 0, 1)
    quente = np.array([226, 184, 140], np.float32)
    branco = np.array([255, 247, 234], np.float32)
    return quente + (branco - quente) * v[..., None]


def textura_fogo_com_buracos(W, H, seed):
    """O que o tutorial faz: um video de chamas por dentro da letra. Onde a chama e preta, a letra some."""
    rng = np.random.default_rng(seed)
    baixa = rng.random((4, 22))
    v = np.asarray(Image.fromarray((baixa * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                   dtype=np.float32) / 255.0
    v = np.clip((v - 0.30) / 0.55, 0, 1)
    preto = np.array([0, 0, 0], np.float32)
    laranja = np.array([230, 90, 10], np.float32)
    amarelo = np.array([255, 220, 120], np.float32)
    cor = np.where(v[..., None] < 0.5, preto + (laranja - preto) * (v[..., None] * 2),
                   laranja + (amarelo - laranja) * ((v[..., None] - 0.5) * 2))
    return cor


def letreiro(linhas, tamanho=100, tracking_em=0.30, seed=7, textura=textura_quente, brilho=True):
    """Compoe uma vez: letra com enchimento + brilho quente a volta. RGB sobre preto, a SS."""
    m = mascara(linhas, tamanho, tracking_em)
    W, H = m.size
    mk = np.asarray(m, np.float32)[..., None] / 255.0
    cor = textura(W, H, seed) * mk
    if brilho:
        # O brilho calcula-se a um quarto e sobe: o desfoque grande e o que custa.
        q = m.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(q.filter(ImageFilter.GaussianBlur(18 * SS / 4)).resize((W, H), Image.BILINEAR),
                        np.float32)[..., None] / 255.0
        g2 = np.asarray(q.filter(ImageFilter.GaussianBlur(60 * SS / 4)).resize((W, H), Image.BILINEAR),
                        np.float32)[..., None] / 255.0
        halo = np.array([255, 150, 70], np.float32) * (0.55 * g1 + 0.30 * g2)
        cor = 255 - (255 - cor) * (1 - halo / 255.0)  # ecra
    return Image.fromarray(np.clip(cor, 0, 255).astype(np.uint8), "RGB")


def pousar(let, escala, cx=L / 2, cy=A / 2):
    """Coloca o letreiro (a SS) no quadro 1920x1080 com escala fracionaria, sem saltos de pixel."""
    k = escala / SS
    W, H = let.size
    # afim de saida -> entrada: xi = (x - cx)/k + W/2
    return let.transform((L, A), Image.AFFINE,
                         (1 / k, 0, W / 2 - cx / k, 0, 1 / k, H / 2 - cy / k),
                         resample=Image.BICUBIC, fillcolor=(0, 0, 0))


def grao(im, quadro, sigma=3.5):
    """Grao de pelicula com semente = numero do fotograma: o render em fatias continua igual ao byte."""
    rng = np.random.default_rng(1000 + quadro)
    a = np.asarray(im, np.float32)
    n = rng.normal(0, sigma, (A, L, 1)).astype(np.float32)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8), "RGB")


def foto_no_ecra(nome):
    """Aproximacao do render: vertical encaixada com fundo desfocado, larga enche."""
    im = Image.open(os.path.join(FIN, nome)).convert("RGB")
    if im.width / im.height >= 1.55:
        f = max(L / im.width, A / im.height)
        im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
        x, y = (im.width - L) // 2, (im.height - A) // 2
        return im.crop((x, y, x + L, y + A))
    f = max(L / im.width, A / im.height)
    fundo = im.resize((round(im.width * f), round(im.height * f)), Image.BILINEAR)
    x, y = (fundo.width - L) // 2, (fundo.height - A) // 2
    fundo = fundo.crop((x, y, x + L, y + A)).filter(ImageFilter.GaussianBlur(40))
    fundo = Image.eval(fundo, lambda v: int(v * 0.55))
    f = A / im.height
    fr = im.resize((round(im.width * f), A), Image.LANCZOS)
    fundo.paste(fr, ((L - fr.width) // 2, 0))
    return fundo


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ o cartao animado
def quadro_cartao(let, t, dur, antes, depois, quadro, enc=0.7, empurra=0.025):
    """Um fotograma do cartao de dur segundos, com os encadeados de enc do render.
    Dentro do cartao: letra entra em 0,9 s, aproxima 2,5% por segundo, grao."""
    alfa = suave((t - 0.05) / 0.9)
    base = pousar(let, 1.0 + empurra * t)
    base = Image.eval(base, lambda v, a=alfa: int(v * a))
    base = grao(base, quadro)
    if t < enc and antes is not None:
        return Image.blend(antes, base, t / enc)
    if t > dur - enc and depois is not None:
        return Image.blend(base, depois, (t - (dur - enc)) / enc)
    return base


def main():
    t0 = time.perf_counter()
    atual = cartao_atual("O trabalho")
    atual.save(os.path.join(OUT, "A_cartao_de_hoje_O_trabalho.png"))

    let = letreiro(["O TRABALHO"], tamanho=100, tracking_em=0.30)
    t1 = time.perf_counter()
    novo = grao(pousar(let, 1.0), 0)
    novo.save(os.path.join(OUT, "B_cartao_estilo_titulo_O_TRABALHO.png"))
    print("compor o letreiro uma vez: %.0f ms" % ((t1 - t0) * 1000))

    let2 = letreiro(["GOSTO PELO", "DESPORTO"], tamanho=100, tracking_em=0.30, seed=11)
    grao(pousar(let2, 1.0), 0).save(os.path.join(OUT, "B2_cartao_duas_linhas_GOSTO_PELO_DESPORTO.png"))

    fogo = letreiro(["O TRABALHO"], tamanho=150, tracking_em=0.02, textura=textura_fogo_com_buracos,
                    brilho=False, seed=3)
    fogo_q = pousar(fogo, 1.0)
    fogo_q.save(os.path.join(OUT, "C_como_o_tutorial_fogo_por_dentro.png"))

    # --- custo por fotograma do cartao animado
    antes = foto_no_ecra("DSC09844.JPG")
    depois = foto_no_ecra("IMG-20181102-WA0000.jpg")
    dur = 3.6
    n = int(dur * FPS)
    tempos = []
    for q in range(n):
        s = time.perf_counter()
        quadro_cartao(let, q / FPS, dur, antes, depois, q)
        tempos.append(time.perf_counter() - s)
    print("fotograma do cartao: media %.0f ms, max %.0f ms, %d fotogramas = %.1f s por cartao"
          % (1000 * np.mean(tempos), 1000 * np.max(tempos), n, sum(tempos)))

    # --- folha da sequencia do cartao
    instantes = [0.0, 0.2, 0.4, 0.7, 1.2, 2.0, 2.9, 3.1, 3.3, 3.6 - 1 / FPS]
    cel_w, cel_h = 640, 360
    fonte = ImageFont.truetype(ARIALBD, 26)
    cols = 5
    folha = Image.new("RGB", (cols * (cel_w + 8) + 8, 2 * (cel_h + 8) + 8), (40, 40, 40))
    d = ImageDraw.Draw(folha)
    for i, t in enumerate(instantes):
        q = int(round(t * FPS))
        im = quadro_cartao(let, t, dur, antes, depois, q).resize((cel_w, cel_h), Image.LANCZOS)
        x, y = 8 + (i % cols) * (cel_w + 8), 8 + (i // cols) * (cel_h + 8)
        folha.paste(im, (x, y))
        d.rectangle([x, y, x + 96, y + 34], fill=(255, 210, 0))
        d.text((x + 6, y + 3), "%.1fs" % t, font=fonte, fill=(0, 0, 0))
    folha.save(os.path.join(OUT, "folha_cartao_animado_3_6s.jpg"), quality=90)

    # --- nomes dos bebes na primeira foto
    for nome_foto, texto, seed, saida in [("21-46.jpg", "O TIAGO", 21, "D_primeira_foto_O_TIAGO.png"),
                                          ("1 (2).jpg", "A CLARA", 22, "D_primeira_foto_A_CLARA.png")]:
        foto = foto_no_ecra(nome_foto)
        # sombra de baixo para garantir o contraste, como a faixa da legenda mas sem caixa
        a = np.asarray(foto, np.float32)
        rampa = np.clip((np.arange(A, dtype=np.float32) - A * 0.55) / (A * 0.45), 0, 1)[:, None, None]
        a = a * (1 - 0.70 * rampa)
        let_n = letreiro([texto], tamanho=120, tracking_em=0.32, seed=seed)
        camada = np.asarray(pousar(let_n, 1.0, cy=A * 0.83), np.float32)
        comp = 255 - (255 - a) * (1 - camada / 255.0)  # ecra
        Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).save(os.path.join(OUT, saida))

    # --- vista a 15 m: tela de 3 m e de 2 m, acuidade 1,5 minutos de arco
    import math
    linhas = [("hoje: Arial Bold 78, branco", atual),
              ("proposta: Arial Bold 100, espacada 0,30, quente", novo),
              ("tutorial: fogo por dentro da letra", fogo_q)]
    fonte2 = ImageFont.truetype(ARIALBD, 30)
    celw, celh = 800, 450
    folha = Image.new("RGB", (3 * (celw + 10) + 10, 3 * (celh + 50) + 10), (30, 30, 30))
    d = ImageDraw.Draw(folha)
    colunas = [("no ecra", None), ("15 m, tela 3 m", 3.0), ("15 m, tela 2 m", 2.0)]
    for j, (titulo, tela_m) in enumerate(colunas):
        for i, (rot, im) in enumerate(linhas):
            if tela_m is None:
                v = im
            else:
                arco = 2 * math.degrees(math.atan(tela_m / 2 / 15)) * 60  # minutos de arco
                px = int(arco / 1.5)
                v = im.resize((px, round(px * A / L)), Image.LANCZOS).resize((L, A), Image.BICUBIC)
            x, y = 10 + j * (celw + 10), 10 + i * (celh + 50)
            folha.paste(v.resize((celw, celh), Image.LANCZOS), (x, y + 40))
            d.text((x, y + 4), f"{titulo}  |  {rot}", font=fonte2, fill=(255, 210, 0))
    folha.save(os.path.join(OUT, "folha_legibilidade_15m.jpg"), quality=90)
    for tela_m in (3.0, 2.0):
        arco = 2 * math.degrees(math.atan(tela_m / 2 / 15)) * 60
        print("tela %.0f m a 15 m: %.0f minutos de arco, %d px uteis a 1,5'" % (tela_m, arco, arco / 1.5))

    # --- cartao animado em mp4 de 3,6 s, so para ver o movimento (nao e o render do filme)
    import subprocess
    ff = r"C:\Users\User 1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
    p = subprocess.Popen([ff, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L}x{A}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                          os.path.join(OUT, "teste_cartao_O_TRABALHO_3_6s.mp4")], stdin=subprocess.PIPE)
    for q in range(n):
        p.stdin.write(quadro_cartao(let, q / FPS, dur, antes, depois, q).tobytes())
    p.stdin.close(); p.wait()
    print("feito em %.1f s" % (time.perf_counter() - t0))


if __name__ == "__main__":
    main()
