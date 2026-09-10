# -*- coding: utf-8 -*-
"""Rende uma montagem (data/montagens/*.csv) para MP4, com imagem e som.

Ate aqui as montagens eram planos em CSV. Isto transforma-as em filme.

COMO FUNCIONA
Cada clip e preparado UMA vez no tamanho maximo de que vai precisar, e depois
cada fotograma aplica-lhe uma transformacao afim com precisao de sub-pixel.
E a mesma correcao do tremor que foi feita no teste_estilos.py: redimensionar
o original em cada fotograma faz a textura fervilhar, e arredondar a posicao a
inteiro faz a imagem saltar.

A FANFARRA nao e redesenhada. E extraida do MP4 original com o seu proprio som
e colada a frente, porque e video verdadeiro e nao uma fotografia.

O SOM segue as mudancas de faixa dela, mas ancoradas a FOTO e nao ao relogio.
Como a v1a mantem a ordem das fotos, cada entrada musical dela e colocada no
instante em que aparece a mesma foto sobre a qual ela a tinha posto. Escalar o
tempo pelo relogio teria dessincronizado as mudancas dos blocos.

FIDELIDADE DA v1a: mantem-se o aspeto dela, incluindo as barras pretas nas
fotos verticais. O fundo desfocado e um tratamento da v1b e nao entra aqui.

Uso:
    py -3.11 scripts/render.py v1a
    py -3.11 scripts/render.py v1a --sem-som
    py -3.11 scripts/render.py v1a --ate 120     so os primeiros 120 segundos
"""
import csv
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTAGENS = os.path.join(REPO, "data", "montagens")
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
SAIDA = r"C:\casamento-video-media\saida"
MEDIA = r"C:\casamento-video-media\trabalho\00-ORIGINAL-MAE"
FANFARRA_MP4 = os.path.join(MEDIA, "Clara e Tiago-2.mp4")

L, A, FPS = 1920, 1080, 25
FONTE_TEXTO = r"C:\Windows\Fonts\arialbd.ttf"
ZOOM = 0.12          # o zoom lento dela, ao centro


def ffmpeg():
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Microsoft\WinGet\Packages"
                     r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                     r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
    if os.path.exists(p):
        return p
    from shutil import which
    return which("ffmpeg") or sys.exit("ffmpeg nao encontrado")


def encaixar(im, larg, alt):
    """Encaixa dentro do quadro sem cortar, com barras pretas. O aspeto dela."""
    f = min(larg / im.width, alt / im.height)
    return im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))),
                     Image.LANCZOS)


def compor(tela, sprite, cx, cy, escala):
    """Coloca o sprite centrado com precisao de sub-pixel. Sem isto, treme.

    Trabalha em RGB e cola sem mascara. As fotografias sao opacas, e compor
    com canal alfa em cada fotograma custava mais de metade do tempo de
    render sem mudar um unico pixel do resultado.
    """
    larg, alt = sprite.width * escala, sprite.height * escala
    x0, y0 = cx - larg / 2.0, cy - alt / 2.0
    ix, iy = math.floor(x0), math.floor(y0)
    fx, fy = x0 - ix, y0 - iy
    cw = int(math.ceil(larg + fx)) + 1
    ch = int(math.ceil(alt + fy)) + 1
    inv = 1.0 / escala
    peca = sprite.transform((cw, ch), Image.AFFINE,
                            (inv, 0.0, -fx * inv, 0.0, inv, -fy * inv),
                            resample=Image.BICUBIC)
    px0, py0 = max(0, -ix), max(0, -iy)
    px1 = min(peca.width, tela.width - ix)
    py1 = min(peca.height, tela.height - iy)
    if px1 <= px0 or py1 <= py0:
        return
    tela.paste(peca.crop((px0, py0, px1, py1)), (ix + px0, iy + py0))


def quebrar(texto, fonte, largura, desenho):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if desenho.textbbox((0, 0), teste, font=fonte)[2] <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def faixa_texto(texto):
    """Desenha a legenda uma vez. Devolve (cor, mascara) para colagem rapida."""
    if not texto:
        return None
    capa = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    tamanho = 46
    fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
    linhas = quebrar(" ".join(texto.split()), fonte, L - 260, d)
    while len(linhas) > 4 and tamanho > 30:
        tamanho -= 4
        fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
        linhas = quebrar(" ".join(texto.split()), fonte, L - 260, d)
    altura_linha = int(tamanho * 1.35)
    bloco = altura_linha * len(linhas)
    topo = A - 70 - bloco
    d.rectangle([0, topo - 26, L, A - 34], fill=(0, 0, 0, 165))
    for i, linha in enumerate(linhas):
        w = d.textbbox((0, 0), linha, font=fonte)[2]
        d.text(((L - w) / 2, topo + i * altura_linha), linha, font=fonte,
               fill=(255, 255, 255, 255))
    return capa.convert("RGB"), capa.split()[3]


def cartao(texto):
    base = Image.new("RGB", (L, A), (8, 8, 10))
    d = ImageDraw.Draw(base)
    tamanho = 78
    fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
    linhas = quebrar(" ".join(texto.split()), fonte, L - 360, d)
    while len(linhas) > 4 and tamanho > 44:
        tamanho -= 6
        fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
        linhas = quebrar(" ".join(texto.split()), fonte, L - 360, d)
    altura_linha = int(tamanho * 1.4)
    topo = (A - altura_linha * len(linhas)) / 2
    for i, linha in enumerate(linhas):
        w = d.textbbox((0, 0), linha, font=fonte)[2]
        d.text(((L - w) / 2, topo + i * altura_linha), linha, font=fonte,
               fill=(238, 238, 244))
    return base


def preparar(clip, inv_por_nome):
    """Prepara o clip uma vez: sprite no tamanho maximo e legenda em camada."""
    texto = clip["texto_ecra"]
    if clip["tipo"] == "cartao":
        return {"tipo": "cartao", "base": cartao(texto), "capa": None}

    caminho = clip.get("_caminho")
    if not caminho or not os.path.exists(caminho):
        r = inv_por_nome.get((clip["ficheiro"] or "").lower())
        caminho = r["caminho"] if r else None
    if not caminho or not os.path.exists(caminho):
        return None

    im = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    escala_max = 1.0 + ZOOM
    alvo = encaixar(im, int(L * escala_max), int(A * escala_max))
    return {"tipo": "foto", "sprite": alvo, "capa": faixa_texto(texto)}


def desenhar(pronto, t_rel, duracao):
    """Um fotograma do clip, no instante t_rel."""
    tela = Image.new("RGB", (L, A), (0, 0, 0))
    if pronto["tipo"] == "cartao":
        tela.paste(pronto["base"], (0, 0))
        return tela
    p = t_rel / duracao if duracao else 0.0
    escala = (1.0 + ZOOM * p) / (1.0 + ZOOM)
    compor(tela, pronto["sprite"], L / 2.0, A / 2.0, escala)
    if pronto["capa"] is not None:
        cor, mascara = pronto["capa"]
        tela.paste(cor, (0, 0), mascara)
    return tela


def musica_reancorada(clips):
    """Coloca cada entrada musical dela sobre a MESMA foto, no tempo novo."""
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    musica = sorted([r for r in linhas if r["faixa"] == "musica"],
                    key=lambda r: float(r["inicio_s"]))
    video = sorted([r for r in linhas if r["faixa"] == "video"],
                   key=lambda r: float(r["inicio_s"]))

    novo_inicio = {}
    for c in clips:
        novo_inicio[int(c["ordem"])] = float(c["inicio_s"])

    entradas = []
    for m in musica:
        t = float(m["inicio_s"])
        indice = 0
        for i, v in enumerate(video):
            if float(v["inicio_s"]) <= t:
                indice = i
            else:
                break
        quando = novo_inicio.get(indice + 1, 0.0)
        entradas.append({
            "ficheiro": m["ficheiro"],
            "caminho": m["caminho_disco"],
            "quando": quando,
            "in_s": float(m["in_s"] or 0),
            "encontrado": m["encontrado"],
        })
    for i, e in enumerate(entradas):
        proximo = entradas[i + 1]["quando"] if i + 1 < len(entradas) else None
        e["dura"] = (proximo - e["quando"]) if proximo else 60.0
    return entradas


def construir_som(ff, entradas, duracao_total, saida):
    usaveis = [e for e in entradas if e["encontrado"] != "Nao"
               and e["caminho"] and os.path.exists(e["caminho"]) and e["dura"] > 0.4]
    faltam = [e for e in entradas if e not in usaveis]
    if faltam:
        print("  sem ficheiro, ficam em silencio: %s"
              % ", ".join(sorted({e["ficheiro"] for e in faltam})))
    if not usaveis:
        return False

    entradas_cmd, filtros, etiquetas = [], [], []
    for i, e in enumerate(usaveis):
        entradas_cmd += ["-ss", "%.3f" % e["in_s"], "-t", "%.3f" % e["dura"],
                         "-i", e["caminho"]]
        filtros.append(
            "[%d:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            "afade=t=in:st=0:d=0.35,afade=t=out:st=%.3f:d=0.9,"
            "adelay=%d|%d[a%d]"
            % (i, max(0.0, e["dura"] - 0.9), int(e["quando"] * 1000),
               int(e["quando"] * 1000), i))
        etiquetas.append("[a%d]" % i)
    filtros.append("%samix=inputs=%d:normalize=0:dropout_transition=0,"
                   "atrim=0:%.3f,asetpts=N/SR/TB[out]"
                   % ("".join(etiquetas), len(usaveis), duracao_total))

    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y"] + entradas_cmd + [
        "-filter_complex", ";".join(filtros), "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k", saida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  ERRO no som: %s" % (r.stderr or "")[-400:])
        return False
    return True


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit("Diz qual a montagem. Ex: py -3.11 scripts/render.py v1a")
    nome = sys.argv[1]
    sem_som = "--sem-som" in sys.argv
    ate = None
    if "--ate" in sys.argv:
        ate = float(sys.argv[sys.argv.index("--ate") + 1])
    if "--escala" in sys.argv:
        # 720p para testes: 2,25 vezes menos pixeis, chega para julgar ritmo.
        global L, A
        f = float(sys.argv[sys.argv.index("--escala") + 1])
        L, A = int(L * f) // 2 * 2, int(A * f) // 2 * 2
        print("Render a %dx%d" % (L, A))

    ff = ffmpeg()
    os.makedirs(SAIDA, exist_ok=True)
    caminho_csv = os.path.join(MONTAGENS, nome + ".csv")
    with open(caminho_csv, encoding="utf-8-sig", newline="") as fh:
        clips = list(csv.DictReader(fh))
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    inv_por_nome = {r["ficheiro"].lower(): r for r in inv}
    inv_por_id = {r["id"]: r for r in inv}

    # A melhor versao de cada imagem: restaurada, IA, lanczos, original.
    for c in clips:
        r = inv_por_id.get(c["id"]) or inv_por_nome.get((c["ficheiro"] or "").lower())
        c["_caminho"] = None
        if not r:
            continue
        for pasta in (r"C:\casamento-video-media\restauradas",
                      r"C:\casamento-video-media\upscaled-ia",
                      r"C:\casamento-video-media\upscaled"):
            if os.path.isdir(pasta):
                for f in os.listdir(pasta):
                    if f.startswith(r["id"] + "__"):
                        c["_caminho"] = os.path.join(pasta, f)
                        break
            if c["_caminho"]:
                break
        if not c["_caminho"]:
            c["_caminho"] = r["caminho"]

    fanfarra = [c for c in clips if c["tipo"] == "video"]
    resto = [c for c in clips if c["tipo"] != "video"]
    if ate:
        resto = [c for c in resto if float(c["inicio_s"]) < ate]

    desvio = float(resto[0]["inicio_s"]) if resto else 0.0
    fim = max(float(c["fim_s"]) for c in resto) - desvio
    total_quadros = int(round(fim * FPS))

    print("Render de %s" % nome)
    print("  clips: %d fotos e cartoes + %d fanfarra" % (len(resto), len(fanfarra)))
    print("  duracao da parte de fotos: %.0f s  (%d fotogramas)" % (fim, total_quadros))
    print()

    corpo = os.path.join(SAIDA, "_%s_corpo.mp4" % nome)
    proc = subprocess.Popen(
        [ff, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (L, A),
         "-framerate", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", corpo], stdin=subprocess.PIPE)

    prontos = {}
    faltaram = []
    for q in range(total_quadros):
        t = desvio + q / FPS
        ativos = [c for c in resto
                  if float(c["inicio_s"]) - 0.001 <= t < float(c["fim_s"])]
        if not ativos:
            ativos = [resto[-1]]
        ativos = ativos[-2:]

        camadas = []
        for c in ativos:
            k = c["ordem"]
            if k not in prontos:
                p = preparar(c, inv_por_nome)
                if p is None:
                    faltaram.append(c["ficheiro"])
                    p = {"tipo": "cartao", "base": cartao(""), "capa": None}
                prontos[k] = p
            ini, dur = float(c["inicio_s"]), float(c["duracao_s"])
            camadas.append((c, desenhar(prontos[k], t - ini, dur)))

        if len(camadas) == 1:
            quadro = camadas[0][1]
        else:
            c2, img2 = camadas[-1]
            _, img1 = camadas[0]
            trans = float(c2["transicao_s"]) or 0.01
            a = min(1.0, max(0.0, (t - float(c2["inicio_s"])) / trans))
            quadro = Image.blend(img1, img2, a)

        proc.stdin.write(quadro.tobytes())

        # Liberta a memoria dos clips que ja passaram.
        if q % 200 == 0:
            vivos = {c["ordem"] for c in ativos}
            for k in list(prontos):
                if k not in vivos:
                    del prontos[k]
            print("  %d/%d fotogramas (%.0f%%)"
                  % (q, total_quadros, 100 * q / total_quadros), end="\r", flush=True)

    proc.stdin.close()
    proc.wait()
    print("\n  corpo escrito")

    partes = []
    if fanfarra and not ate:
        fan = os.path.join(SAIDA, "_%s_fanfarra.mp4" % nome)
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", "1.796", "-t", "%.3f" % float(fanfarra[0]["duracao_s"]),
                        "-i", FANFARRA_MP4,
                        "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,"
                               "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1" % (L, A, L, A),
                        "-r", str(FPS), "-c:v", "libx264", "-crf", "20",
                        "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
                        fan], capture_output=True, text=True)
        partes.append(fan)

    som = None
    if not sem_som:
        print("  a construir o som")
        som = os.path.join(SAIDA, "_%s_som.m4a" % nome)
        if not construir_som(ff, musica_reancorada(resto), fim, som):
            som = None

    corpo_final = corpo
    if som:
        corpo_final = os.path.join(SAIDA, "_%s_corpo_som.mp4" % nome)
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", corpo, "-i", som, "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-ac", "2", "-ar", "48000",
                        "-shortest", corpo_final], capture_output=True, text=True)
    partes.append(corpo_final)

    final = os.path.join(SAIDA, "%s.mp4" % nome)
    if len(partes) == 1:
        os.replace(partes[0], final)
    else:
        lista = os.path.join(SAIDA, "_%s_lista.txt" % nome)
        with open(lista, "w", encoding="utf-8") as fh:
            for p in partes:
                fh.write("file '%s'\n" % p.replace("\\", "/"))
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "concat", "-safe", "0", "-i", lista,
                            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            final], capture_output=True, text=True)
        if r.returncode != 0:
            print("  ERRO ao juntar: %s" % (r.stderr or "")[-300:])

    if faltaram:
        print("  imagens que nao consegui abrir: %d" % len(faltaram))
        for f in sorted(set(faltaram))[:8]:
            print("     %s" % f)
    print()
    print("Escrito: %s" % final)


if __name__ == "__main__":
    main()
