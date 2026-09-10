# -*- coding: utf-8 -*-
"""Restauro de fotografias estragadas, a resolucao original.

Isto e diferente do upscale_ia.py. Aquele serve o video: prepara a foto para o
tamanho a que vai aparecer. Este serve a fotografia em si, para o Tiago ficar
com ela melhor do que estava, entre ou nao entre no filme.

A cadeia, por ordem, e cada passo tem uma razao:

  1. EQUILIBRIO DE BRANCOS por percentil alto. Fotografias de interior com luz
     de tungstenio ficam com dominante laranja. Corrige-se escalando cada canal
     para que o seu percentil 97 chegue ao mesmo valor. E mais robusto do que a
     media (mundo-cinzento), que se deixa enganar por uma parede colorida ou
     por roupa escura a ocupar meio quadro.
  2. NLMEANS para o grao. Medias nao-locais: procura zonas parecidas por toda a
     imagem e faz a media entre elas. Preserva contorno muito melhor do que um
     filtro de mediana, que amassa tudo por igual.
  3. UNSHARP com raio grande. Contra desfocagem, o raio tem de acompanhar o
     tamanho do borrao. Raio pequeno so realca grao.
  4. CONTRASTE e SATURACAO ligeiros, porque denoise tira sempre algum dos dois.

O que NAO faz, e porque nao:
  - Nao desfaz tremura de mao. Isso exige deconvolucao com o nucleo do
    movimento, que nao esta disponivel aqui e que, mesmo quando esta, deixa
    artefactos em fotografia de pessoas. O que se ganha e nitidez aparente,
    nao detalhe verdadeiro.
  - Nao redesenha rostos. Ver a nota do upscale_ia.py.

Uso:
    py -3.11 scripts/restaurar.py f0357
    py -3.11 scripts/restaurar.py f0357 --forca 1.4    mais agressivo
    py -3.11 scripts/restaurar.py --piores 10          as 10 menos nitidas
"""
import csv
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageFilter, ImageOps, ImageStat

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TRABALHO = os.path.normcase(os.path.abspath(r"C:\casamento-video-media\trabalho"))
DESTINO = r"C:\casamento-video-media\restauradas"

LAPLACIANO = ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 4, -1, 0, -1, 0], scale=1)


def ffmpeg():
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Microsoft\WinGet\Packages"
                     r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                     r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
    if os.path.exists(p):
        return p
    from shutil import which
    return which("ffmpeg") or sys.exit("ffmpeg nao encontrado")


def proteger_destino():
    d = os.path.normcase(os.path.abspath(DESTINO))
    if d == TRABALHO or d.startswith(TRABALHO + os.sep):
        sys.exit("RECUSADO: o destino cai dentro da pasta de trabalho.")


def nitidez(caminho, lado=900):
    with Image.open(caminho) as im:
        g = ImageOps.exif_transpose(im).convert("L")
        g.thumbnail((lado, lado), Image.LANCZOS)
        return ImageStat.Stat(g.filter(LAPLACIANO)).stddev[0]


def percentil_canal(hist, total, p=0.97):
    """Valor abaixo do qual esta a fracao p dos pixeis deste canal."""
    limite = total * p
    acumulado = 0
    for valor, quantos in enumerate(hist):
        acumulado += quantos
        if acumulado >= limite:
            return max(1, valor)
    return 255


def media_tons_medios(canal, baixo=40, alto=225):
    """Media do canal ignorando sombras fechadas e luzes queimadas.

    As luzes de teto queimadas ja estao a branco e nao trazem informacao sobre
    a dominante. As sombras fechadas tambem nao. A dominante le-se nos tons
    medios, que sao a pele, a roupa e o chao.
    """
    hist = canal.histogram()
    soma = quantos = 0
    for valor in range(baixo, alto + 1):
        soma += valor * hist[valor]
        quantos += hist[valor]
    return (soma / quantos) if quantos else 128.0


def equilibrar_brancos(im, percentil=0.97):
    """Corrige a dominante de cor, pelo mais forte de dois metodos.

    O metodo do percentil alto funciona quando ha um branco verdadeiro na
    imagem. Falha quando os pixeis mais claros sao lampadas queimadas, que ja
    estao a branco e portanto nao denunciam a dominante nenhuma.

    O metodo dos tons medios nao tem esse problema, mas engana-se quando a cena
    e genuinamente colorida. Aplicar o mais forte dos dois cobre os dois casos,
    e nesta colecao as fotos de interior sao quase sempre o primeiro caso.
    """
    canais = im.split()
    total = im.width * im.height

    picos = [percentil_canal(c.histogram(), total, percentil) for c in canais]
    alvo_pico = max(picos)
    f_percentil = [alvo_pico / p for p in picos]

    medias = [media_tons_medios(c) for c in canais]
    alvo_medio = sum(medias) / 3
    f_medios = [alvo_medio / m for m in medias]

    # "Mais forte" = o que mais se afasta de nao fazer nada.
    forca_p = sum(abs(f - 1) for f in f_percentil)
    forca_m = sum(abs(f - 1) for f in f_medios)
    fatores, metodo = ((f_medios, "tons medios") if forca_m > forca_p
                       else (f_percentil, "percentil alto"))

    corrigidos = [c.point(lambda v, f=f: max(0, min(255, int(v * f))))
                  for c, f in zip(canais, fatores)]
    return Image.merge("RGB", corrigidos), metodo, fatores


def restaurar(ff, entrada, saida, forca=1.0):
    im = ImageOps.exif_transpose(Image.open(entrada)).convert("RGB")
    largura, altura = im.size

    wb, metodo, fatores = equilibrar_brancos(im)
    print("   equilibrio de brancos por %s: R x%.2f  G x%.2f  B x%.2f"
          % (metodo, fatores[0], fatores[1], fatores[2]))

    tmp = tempfile.mkdtemp(prefix="restauro_")
    intermedio = os.path.join(tmp, "wb.png")
    wb.save(intermedio)

    # O raio do unsharp acompanha o tamanho da imagem, senao em fotos grandes
    # so realca grao em vez de atacar o borrao.
    raio = 5 if max(largura, altura) < 2500 else 9
    # O realce entrou a mais na primeira versao e acendeu o grao nas sombras.
    # Menos quantidade, mais denoise antes, e nada de realce na crominancia,
    # que e onde o grao de ISO alto mais se ve.
    quantidade = 0.65 * forca
    cadeia = ("hqdn3d=%.1f:%.1f:%.1f:%.1f,"
              "nlmeans=s=%.1f:p=7:r=15,"
              "unsharp=%d:%d:%.2f:%d:%d:0.0,"
              "eq=contrast=%.2f:saturation=%.2f"
              % (4.0 * forca, 3.0 * forca, 6.0 * forca, 4.5 * forca,
                 4.5 * forca, raio, raio, quantidade, raio, raio,
                 1.0 + 0.10 * forca, 1.0 + 0.06 * forca))

    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y",
           "-i", intermedio, "-vf", cadeia, "-q:v", "2", saida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        os.remove(intermedio)
        os.rmdir(tmp)
    except OSError:
        pass
    if r.returncode != 0:
        print("   ERRO: %s" % (r.stderr or "")[-300:])
        return False
    return True


def main():
    proteger_destino()
    ff = ffmpeg()
    os.makedirs(DESTINO, exist_ok=True)

    forca = 1.0
    if "--forca" in sys.argv:
        forca = float(sys.argv[sys.argv.index("--forca") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    por_id = {r["id"]: r for r in inv}

    alvos = []
    if "--piores" in sys.argv:
        n = int(sys.argv[sys.argv.index("--piores") + 1])
        print("A medir a nitidez de %d fotografias..." % len(inv))
        medidas = []
        for r in inv:
            try:
                medidas.append((nitidez(r["caminho"]), r))
            except Exception:
                pass
        medidas.sort(key=lambda x: x[0])
        alvos = [r for _, r in medidas[:n]]
    else:
        for a in sys.argv[1:]:
            if a.startswith("-"):
                continue
            if a in por_id:
                alvos.append(por_id[a])
            else:
                achados = [r for r in inv if a.lower() in r["ficheiro"].lower()]
                alvos.extend(achados)

    if not alvos:
        sys.exit("Nada para restaurar. Da um id (f0357) ou parte de um nome.")

    print("A restaurar %d fotografia(s), forca %.1f" % (len(alvos), forca))
    print("Destino: %s" % DESTINO)
    print("Originais: nao sao tocados.")
    print()

    for r in alvos:
        base = os.path.splitext(r["ficheiro"])[0][:60]
        saida = os.path.join(DESTINO, "%s__%s.jpg" % (r["id"], base))
        antes = nitidez(r["caminho"])
        print("%s  %s  (%sx%s, nitidez %.1f)"
              % (r["id"], r["ficheiro"][:44], r["largura"], r["altura"], antes))
        if restaurar(ff, r["caminho"], saida, forca):
            depois = nitidez(saida)
            print("   feito: nitidez %.1f -> %.1f   %s"
                  % (antes, depois, os.path.basename(saida)))
        print()


if __name__ == "__main__":
    main()
