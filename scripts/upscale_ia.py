# -*- coding: utf-8 -*-
"""Upscaling por rede neuronal (Real-ESRGAN), nao destrutivo.

Complementa o scripts/upscale.py, que usa lanczos. O lanczos chega bem ate
cerca de 1,5x. Acima disso comeca a faltar-lhe informacao para inventar e a
imagem fica mole. O Real-ESRGAN reconstroi textura e contorno de forma
convincente, e a diferenca ve-se sobretudo em padroes finos, tecido e cabelo.

MODELO: realesrgan-x4plus, que e o modelo generico para fotografia.
NAO usar realesrgan-x4plus-anime nem realesr-animevideov3: sao para desenho
animado e em fotografias de pessoas dao pele de plastico.
NAO usar restauro de rostos (GFPGAN, CodeFormer): esses nao ampliam a cara,
redesenham-na, e inventam um rosto plausivel que nao e o da pessoa. Numa sala
com 140 convidados que conhecem estas caras, isso nota-se.

Garantias, as mesmas do upscale.py:
  1. O original NUNCA e tocado. O script recusa-se a correr se o destino cair
     dentro da pasta de trabalho.
  2. Nada e reescrito. Se ja existir, salta.
  3. Cada foto e reduzida no fim para o tamanho exato de que precisa. Ampliar
     4x e deixar assim so gastava disco sem ganhar nada no ecra.

Uso, sempre a partir da pasta do repositorio:
    cd C:\casamento-video
    py -3.11 scripts/upscale_ia.py --todas       corrida da noite, ver abaixo
    py -3.11 scripts/upscale_ia.py --min 2.0     so as que precisam de 2x ou mais
    py -3.11 scripts/upscale_ia.py --listar      diz o que faria, sem fazer

--todas usa o limiar 0,6 em vez de 2,0. Isso cobre tudo o que pode vir a
precisar de pixeis, incluindo os planos fechados: uma foto a 0,6 cortada a 60
por cento da largura fica a 1,0. Abaixo de 0,6 o original ja tem mais
informacao do que o modelo consegue devolver, e nao se toca.

Pode ser interrompido com Ctrl+C e retomado: salta tudo o que ja esta feito.
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TRABALHO = os.path.normcase(os.path.abspath(r"C:\casamento-video-media\trabalho"))
DESTINO = r"C:\casamento-video-media\upscaled-ia"
EXE = (r"C:\casamento-video-media\ferramentas\realesrgan"
       r"\realesrgan-ncnn-vulkan-20220424-windows\realesrgan-ncnn-vulkan.exe")
MODELO = "realesrgan-x4plus"

LARGURA_ALVO, ALTURA_ALVO = 1920, 1080
FOLGA = 1.15    # margem para o pan e zoom, igual a do upscale.py
QUALIDADE = 95


def proteger_destino():
    d = os.path.normcase(os.path.abspath(DESTINO))
    if d == TRABALHO or d.startswith(TRABALHO + os.sep):
        sys.exit("RECUSADO: o destino cai dentro da pasta de trabalho.")


def nome_seguro(texto):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", texto).strip("_")[:60]


# Abaixo desta proporcao a foto e mostrada a altura toda com fundo desfocado
# (tratamento A, decisao 017) em vez de encher o ecra. Isso muda o alvo por
# completo: uma foto de 368x1067 precisava de 6x para encher os 1920 de
# largura, e precisa so de 1,2x para ter os 1080 de altura.
PROPORCAO_ECRA = LARGURA_ALVO / ALTURA_ALVO
LIMITE_FUNDO_DESFOCADO = 1.55


def alvo(larg, alt):
    """Tamanho de saida e fator de exibicao.

    O fator diz quanto e que a foto precisa de crescer para o modo como vai
    aparecer: encaixada com fundo desfocado, so a altura conta; a encher o
    ecra, contam os dois lados.

    O tamanho de saida NUNCA fica abaixo do original. Uma foto que ja tenha
    pixeis a mais para o ecra pode continuar a precisar deles para um plano
    fechado, e reduzi-la aqui deitava fora informacao que nao volta.
    """
    proporcao = larg / alt
    if proporcao < LIMITE_FUNDO_DESFOCADO:
        f = (ALTURA_ALVO / alt) * FOLGA
    else:
        f = max(LARGURA_ALVO / larg, ALTURA_ALVO / alt) * FOLGA
    nl = max(larg, round(larg * f))
    na = max(alt, round(alt * f))
    return nl, na, f


def mmss(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def main():
    proteger_destino()
    if not os.path.exists(EXE):
        sys.exit("Nao encontrei o Real-ESRGAN em:\n  %s" % EXE)

    listar = "--listar" in sys.argv
    todas = "--todas" in sys.argv
    # 0,6 cobre tudo o que pode vir a precisar de pixeis, incluindo os planos
    # fechados: uma foto a 0,6 cortada a 60 por cento da largura fica a 1,0.
    # Abaixo disso o original ja tem mais informacao do que o modelo consegue
    # devolver, e passa-lo pela rede so alterava a textura sem ganho nenhum.
    minimo = 0.6 if todas else 2.0
    if "--min" in sys.argv:
        minimo = float(sys.argv[sys.argv.index("--min") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))

    # Guarda de seguranca. Uma foto de 6016x4000 ampliada 4x da 385 megapixeis,
    # o que em CPU sao dezenas de minutos e pode esgotar a memoria a meio de uma
    # noite de processamento. Fotos assim nunca precisam de ampliacao nenhuma,
    # por isso o corte nao tira nada de util.
    MAX_MEGAPIXEIS = 16

    trabalho, grandes = [], []
    for r in linhas:
        larg, alt = int(r["largura"]), int(r["altura"])
        dims = alvo(larg, alt)
        if dims[2] < minimo:
            continue
        if larg * alt > MAX_MEGAPIXEIS * 1_000_000:
            grandes.append(r)
            continue
        trabalho.append((r, dims))
    trabalho.sort(key=lambda x: -x[1][2])

    os.makedirs(DESTINO, exist_ok=True)
    por_fazer = []
    for r, dims in trabalho:
        nome = "%s__%s.jpg" % (r["id"],
                               nome_seguro(os.path.splitext(r["ficheiro"])[0]))
        if not os.path.exists(os.path.join(DESTINO, nome)):
            por_fazer.append((r, dims, nome))

    print("Modelo: %s" % MODELO)
    print("Criterio: fator de ampliacao >= %.2f" % minimo)
    print("Elegiveis: %d    Ja feitas: %d    Por fazer: %d"
          % (len(trabalho), len(trabalho) - len(por_fazer), len(por_fazer)))
    if grandes:
        print("Saltadas por serem grandes de mais para valer a pena: %d" % len(grandes))
    print("Destino: %s" % DESTINO)
    print("Originais em %s: nao sao tocados." % TRABALHO)
    if por_fazer:
        print("Estimativa a 88 s por foto: cerca de %s" % mmss(len(por_fazer) * 88))
    print()

    if listar:
        for r, (nl, na, f), nome in por_fazer[:60]:
            print("  %.2fx  %5sx%-5s -> %5dx%-5d  %s"
                  % (f, r["largura"], r["altura"], nl, na, r["ficheiro"][:44]))
        return

    tmp = tempfile.mkdtemp(prefix="esrgan_")
    inicio = time.time()
    feitas = falhadas = 0
    try:
        for n, (r, (nl, na, f), nome) in enumerate(por_fazer, 1):
            bruto = os.path.join(tmp, "%s.png" % r["id"])
            cmd = [EXE, "-i", r["caminho"], "-o", bruto, "-n", MODELO, "-s", "4"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0 or not os.path.exists(bruto):
                falhadas += 1
                print("  FALHOU %s  %s" % (r["ficheiro"][:40],
                                           (proc.stderr or "")[-160:]))
                continue

            # Reduz do 4x para o tamanho exato de que precisa. Vir de uma
            # imagem 4x e reduzir da melhor resultado do que pedir menos ampliacao.
            with Image.open(bruto) as im:
                im = im.convert("RGB").resize((nl, na), Image.LANCZOS)
                im.save(os.path.join(DESTINO, nome), "JPEG",
                        quality=QUALIDADE, optimize=True)
            os.remove(bruto)
            feitas += 1

            decorrido = time.time() - inicio
            media = decorrido / n
            falta = media * (len(por_fazer) - n)
            print("  [%d/%d] %.2fx  %-40s  %s decorridos, faltam ~%s"
                  % (n, len(por_fazer), f, r["ficheiro"][:40],
                     mmss(decorrido), mmss(falta)), flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("Ampliadas: %d   Falhadas: %d   Tempo total: %s"
          % (feitas, falhadas, mmss(time.time() - inicio)))


if __name__ == "__main__":
    main()
