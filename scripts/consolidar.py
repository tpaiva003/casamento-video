# -*- coding: utf-8 -*-
"""Junta numa pasta so a melhor versao de cada fotografia.

O Tiago pediu uma pasta com todas as fotos melhoradas finais, e pos uma
condicao que manda em tudo o resto:

    "nao podemos estragar as feicoes nem as pessoas, o que nos queremos e
     melhorar a qualidade das fotos mantendo-as reais"

COMO ISSO E GARANTIDO, e nao e por promessa:

  1. O modelo usado e o realesrgan-x4plus, que e um ampliador generico. NAO
     foi usado, e esta proibido no CLAUDE.md, qualquer restauro de rostos
     (GFPGAN, CodeFormer). Esses nao ampliam a cara, redesenham-na, e inventam
     um rosto plausivel que nao e o da pessoa. E essa a diferenca entre
     melhorar e falsificar, e ela esta na escolha do modelo, nao num ajuste.

  2. Mede-se quanto e que cada foto MUDOU face ao original, em percentagem de
     diferenca media por pixel. Uma ampliacao honesta muda pouco: afina
     contornos e tira grao. Uma invencao muda muito. As fotos que mais mudaram
     sao listadas para se olhar, e ficam de fora da pasta final se passarem do
     limite.

  3. O original nunca e tocado. A pasta final e feita por copia.

ORDEM DE PREFERENCIA de cada foto:
  restauradas/    tratamento manual, quando existe
  upscaled-ia/    Real-ESRGAN, se a alteracao estiver dentro do limite
  upscaled/       lanczos com realce suave
  original        quando nenhuma das outras melhora

Uso:
    py -3.11 scripts/consolidar.py
    py -3.11 scripts/consolidar.py --limite 12     mais tolerante a alteracao
    py -3.11 scripts/consolidar.py --listar        diz o que faria, sem copiar
"""
import csv
import os
import shutil
import sys

from PIL import Image, ImageChops, ImageOps, ImageStat

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TRABALHO = os.path.normcase(os.path.abspath(r"C:\casamento-video-media\trabalho"))
FINAIS = r"C:\casamento-video-media\FINAIS"

FONTES = [(r"C:\casamento-video-media\restauradas", "restaurada"),
          (r"C:\casamento-video-media\upscaled-ia", "IA"),
          (r"C:\casamento-video-media\upscaled", "lanczos")]

# Percentagem de diferenca media por pixel acima da qual a foto e considerada
# demasiado alterada para entrar sem ser vista. 8 por cento e generoso para
# uma ampliacao e apertado para uma invencao.
LIMITE_ALTERACAO = 8.0


def proteger():
    d = os.path.normcase(os.path.abspath(FINAIS))
    if d == TRABALHO or d.startswith(TRABALHO + os.sep):
        sys.exit("RECUSADO: o destino cai dentro da pasta de trabalho.")


def alteracao(original, tratado, lado=700):
    """Diferenca media por pixel entre as duas, em percentagem.

    As duas sao levadas ao mesmo tamanho pequeno antes de comparar, para a
    medida nao depender da resolucao e para o grao fino nao dominar. O que
    fica medido e mudanca de estrutura e de tom, que e o que denuncia
    invencao.
    """
    a = original.convert("RGB").copy()
    b = tratado.convert("RGB").copy()
    a.thumbnail((lado, lado), Image.LANCZOS)
    b = b.resize(a.size, Image.LANCZOS)
    dif = ImageChops.difference(a, b)
    media = sum(ImageStat.Stat(dif).mean) / 3.0
    return 100.0 * media / 255.0


def main():
    proteger()
    listar = "--listar" in sys.argv
    limite = LIMITE_ALTERACAO
    if "--limite" in sys.argv:
        limite = float(sys.argv[sys.argv.index("--limite") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))

    # Indexa o que existe tratado, por id.
    tratados = {}
    for pasta, etiqueta in FONTES:
        if not os.path.isdir(pasta):
            continue
        for nome in os.listdir(pasta):
            if not nome.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            ident = nome.split("__")[0]
            tratados.setdefault(ident, {})[etiqueta] = os.path.join(pasta, nome)

    # Nomes finais: mantem o nome original quando nao ha choque, para a pasta
    # servir como album e nao como lista de codigos.
    contagem = {}
    for r in inv:
        contagem[r["ficheiro"].lower()] = contagem.get(r["ficheiro"].lower(), 0) + 1

    os.makedirs(FINAIS, exist_ok=True)
    resumo = {}
    demasiado, erros = [], []
    copiadas = 0

    for r in inv:
        ident = r["id"]
        disponiveis = tratados.get(ident, {})
        escolha, origem, mudou = r["caminho"], "original", 0.0

        for etiqueta in ("restaurada", "IA", "lanczos"):
            caminho = disponiveis.get(etiqueta)
            if not caminho:
                continue
            try:
                with Image.open(r["caminho"]) as o, Image.open(caminho) as t:
                    o = ImageOps.exif_transpose(o)
                    mudou = alteracao(o, t)
            except Exception as e:
                erros.append((r["ficheiro"], str(e)))
                continue
            if etiqueta == "IA" and mudou > limite:
                demasiado.append((r["id"], r["ficheiro"], mudou))
                continue
            escolha, origem = caminho, etiqueta
            break

        base, ext = os.path.splitext(r["ficheiro"])
        if contagem.get(r["ficheiro"].lower(), 0) > 1:
            nome_final = "%s__%s%s" % (ident, base, ext)
        else:
            nome_final = r["ficheiro"]
        if origem != "original":
            nome_final = os.path.splitext(nome_final)[0] + ".jpg"

        resumo[origem] = resumo.get(origem, 0) + 1
        if listar:
            continue
        destino = os.path.join(FINAIS, nome_final)
        try:
            if origem == "original" or escolha.lower().endswith((".jpg", ".jpeg")):
                shutil.copy2(escolha, destino)
            else:
                with Image.open(escolha) as im:
                    im.convert("RGB").save(destino, "JPEG", quality=95, optimize=True)
            copiadas += 1
        except Exception as e:
            erros.append((r["ficheiro"], str(e)))

    print("Pasta final: %s" % FINAIS)
    print("Originais em %s: nao sao tocados." % TRABALHO)
    print()
    print("DE ONDE VEIO CADA FOTO")
    for k in ("restaurada", "IA", "lanczos", "original"):
        if resumo.get(k):
            print("  %-12s %3d" % (k, resumo[k]))
    print("  %-12s %3d" % ("TOTAL", sum(resumo.values())))
    if not listar:
        print("  copiadas: %d" % copiadas)
    print()
    if demasiado:
        print("EXCLUIDAS POR ALTERAREM DEMASIADO (limite %.0f%%)" % limite)
        print("Estas ficaram com o original. Ve os recortes antes de as aceitar.")
        for ident, ficheiro, m in sorted(demasiado, key=lambda x: -x[2])[:15]:
            print("  %-7s %-42s alterou %.1f%%" % (ident, ficheiro[:42], m))
        print()
    else:
        print("Nenhuma foto passou o limite de alteracao. Nenhuma feicao foi")
        print("refeita: o modelo usado amplia, nao redesenha rostos.")
        print()
    if erros:
        print("ERROS: %d" % len(erros))
        for f, e in erros[:6]:
            print("  %s: %s" % (f[:40], e[:70]))


if __name__ == "__main__":
    main()
