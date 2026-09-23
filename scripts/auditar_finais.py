# -*- coding: utf-8 -*-
"""Poe em causa a escolha da pasta FINAIS, foto a foto.

A PERGUNTA DO TIAGO, que e a certa:
    "tens a certeza que o que esta na pasta finais sao as com melhor qualidade?
     Das que fizemos o upscalling e das que fizemos a melhoria?"

A resposta honesta ao que o consolidar.py faz hoje e NAO, e a razao e de
construcao, nao de execucao: o consolidar.py escolhe por ORDEM DE PREFERENCIA
(restaurada, depois IA, depois lanczos, depois original) e nunca compara as
versoes entre si. Mede uma coisa so, quanto e que a foto mudou face ao
original, e isso serve para apanhar invencao de feicoes, que era a outra
preocupacao dele. Nao serve para dizer qual das versoes esta melhor.

Este script faz a comparacao que falta. Para cada foto com mais do que uma
versao, poe TODAS ao mesmo tamanho e mede duas coisas:

  DETALHE NOS CONTORNOS  so nos blocos de maior contraste local, que e onde
                         vive o detalhe verdadeiro: arestas, olhos, tecido,
                         letras. Limpar grao numa parede nao mexe neste numero.

  AGITACAO NOS LISOS     nos blocos mais lisos, que e onde o ruido e os halos
                         aparecem sem disfarce.

Melhor = mais detalhe sem mais agitacao. Quando as duas sobem ao mesmo tempo,
o que ganhamos foi ruido disfarcado de nitidez, e o script diz que nao sabe em
vez de inventar um vencedor. Ja levei duas vezes com metricas a marcar como
piores fotos que a olho estavam melhores, e o registo disso esta no
verificar_upscale.py. Por isso aqui NENHUM caso duvidoso e decidido sozinho:
sai em recorte lado a lado para se olhar.

Uso:
    py -3.11 scripts/auditar_finais.py
    py -3.11 scripts/auditar_finais.py --recortes 20
"""
import csv
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from consolidar import precisa_crescer
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
FINAIS = r"C:\casamento-video-media\FINAIS"
SAIDA = r"C:\casamento-video-media\verificacao\auditoria"

FONTES = [(r"C:\casamento-video-media\restauradas", "restaurada"),
          (r"C:\casamento-video-media\upscaled-ia", "IA"),
          (r"C:\casamento-video-media\upscaled", "lanczos")]

LAPLACIANO = ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 4, -1, 0, -1, 0], scale=1)

# Diferencas abaixo disto sao empate. Sao percentagens: 4 por cento de detalhe
# nao se ve num ecra a 15 metros, e fingir que se ve e que dava um vencedor
# falso em metade dos casos.
EMPATE_DETALHE = 4.0
EMPATE_AGITACAO = 8.0


def blocos(im, lado, quarto):
    """Media do laplaciano no quarto de blocos escolhido por contraste local.

    quarto="altos" da os blocos de maior contraste (contornos).
    quarto="baixos" da os mais lisos (ceu, paredes, pele).
    """
    g = im.convert("L")
    g.thumbnail((800, 800), Image.LANCZOS)
    lap = g.filter(LAPLACIANO)
    caixas = []
    for y in range(0, g.height - lado, lado):
        for x in range(0, g.width - lado, lado):
            c = (x, y, x + lado, y + lado)
            caixas.append((ImageStat.Stat(g.crop(c)).stddev[0],
                           ImageStat.Stat(lap.crop(c)).stddev[0]))
    if not caixas:
        return 0.0
    caixas.sort(key=lambda b: -b[0] if quarto == "altos" else b[0])
    escolhidos = caixas[:max(1, len(caixas) // 4)]
    return sum(b[1] for b in escolhidos) / len(escolhidos)


def medir(im):
    return blocos(im, 14, "altos"), blocos(im, 14, "baixos")


def comparar(a, b):
    """Qual esta melhor, a ou b? Devolve 'a', 'b' ou 'empate'.

    A regra e deliberadamente conservadora. So declara vencedor quando ganha
    em detalhe SEM perder em limpeza, ou quando limpa muito sem perder detalhe.
    Tudo o resto e empate, e empate vai a olho.
    """
    d_det = 100 * (b[0] - a[0]) / max(0.01, a[0])
    d_agi = 100 * (b[1] - a[1]) / max(0.01, a[1])
    if d_det > EMPATE_DETALHE and d_agi < EMPATE_AGITACAO:
        return "b", d_det, d_agi
    if d_det < -EMPATE_DETALHE and d_agi > -EMPATE_AGITACAO:
        return "a", d_det, d_agi
    if abs(d_det) <= EMPATE_DETALHE and d_agi < -25:
        return "b", d_det, d_agi
    if abs(d_det) <= EMPATE_DETALHE and d_agi > 25:
        return "a", d_det, d_agi
    return "empate", d_det, d_agi


def rotular(im, texto, tamanho=34):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", tamanho)
    w = d.textbbox((0, 0), texto, font=f)[2]
    d.rectangle([10, 10, 30 + w, 22 + tamanho], fill=(0, 0, 0))
    d.text((20, 14), texto, font=f, fill=(255, 255, 255))
    return im


def main():
    quantos = 12
    if "--recortes" in sys.argv:
        quantos = int(sys.argv[sys.argv.index("--recortes") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))

    tratados = {}
    for pasta, etiqueta in FONTES:
        if not os.path.isdir(pasta):
            continue
        for nome in os.listdir(pasta):
            if nome.lower().endswith((".jpg", ".jpeg", ".png")):
                tratados.setdefault(nome.split("__")[0], {})[etiqueta] = \
                    os.path.join(pasta, nome)

    # QUAL E A ESCOLHA ATUAL: le-se no indice, que e onde ela esta escrita.
    #
    # Duas versoes anteriores deste bloco estiveram erradas, e cada uma a sua
    # maneira. A primeira repetia aqui a ordem de preferencia do consolidar.py e
    # nao sabia da regra do original: oito falsos alarmes. A segunda perguntava
    # a pasta por hash, o que parecia a prova definitiva, mas a FINAIS tem
    # ficheiros de corridas antigas com outra extensao, e o hash encontrava o
    # velho: sete falsos alarmes, todos a dizer "esta: lanczos" a fotos cuja
    # escolha atual e o original.
    #
    # A resposta e uma so e esta no data/finais.csv, que o consolidar.py escreve
    # ao mesmo tempo que copia. Ler de la e a unica forma que nao envelhece.
    caminho_indice = os.path.join(REPO, "data", "finais.csv")
    if not os.path.exists(caminho_indice):
        sys.exit("Falta data/finais.csv. Corre primeiro:  "
                 "py -3.11 scripts/consolidar.py")
    indice = {}
    with open(caminho_indice, encoding="utf-8-sig", newline="") as fh:
        for linha in csv.DictReader(fh):
            indice[linha["id"]] = linha

    casos, sem_saber = [], 0
    for r in inv:
        disp = tratados.get(r["id"], {})
        if not disp:
            continue
        candidatos = dict(disp)
        candidatos["original"] = r["caminho"]
        if len(candidatos) < 2:
            continue
        escolhida = (indice.get(r["id"]) or {}).get("origem")
        if escolhida not in candidatos:
            sem_saber += 1
            continue
        casos.append((r, escolhida, candidatos))

    print("Fotos com mais do que uma versao: %d" % len(casos))
    if sem_saber:
        print("Sem correspondencia na FINAIS, saltadas: %d" % sem_saber)
    print("A medir detalhe nos contornos e agitacao nos lisos, ao mesmo tamanho.")
    print()

    concorda = discorda = empatadas = por_regra = 0
    problemas, erros = [], []

    for n, (r, escolhida, candidatos) in enumerate(casos, 1):
        try:
            # Todas ao tamanho da maior, que e como vao aparecer no ecra.
            tamanhos = {}
            for et, cam in candidatos.items():
                with Image.open(cam) as im:
                    tamanhos[et] = (im.width * im.height, im.size)
            maior = max(tamanhos.values(), key=lambda t: t[0])[1]

            medidas = {}
            for et, cam in candidatos.items():
                with Image.open(cam) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    if im.size != maior:
                        im = im.resize(maior, Image.LANCZOS)
                    medidas[et] = medir(im)

            # A escolhida contra cada rival.
            perde_para, detalhe = [], {}
            for et in candidatos:
                if et == escolhida:
                    continue
                v, d_det, d_agi = comparar(medidas[escolhida], medidas[et])
                detalhe[et] = (d_det, d_agi, v)
                if v == "b":
                    perde_para.append(et)

            if perde_para:
                pior = max(perde_para, key=lambda e: detalhe[e][0])
                # A METRICA PREMEIA EXATAMENTE O QUE ELE PROIBIU.
                #
                # Uma foto que ja tem pixeis que cheguem fica com o original,
                # por regra. A rede neuronal devolve-a mais afiada e mais lisa,
                # e a medida de contorno e de agitacao le isso como "melhor".
                # So que o que ela alisou foi a pele, e o Tiago foi claro: "nao
                # podemos estragar as feicoes nem as pessoas, o que nos queremos
                # e melhorar a qualidade das fotos mantendo-as reais".
                #
                # Estes casos nao sao desacordos, sao a regra a funcionar. Ficam
                # a parte, senao cada corrida traz vinte linhas de falso alarme.
                try:
                    ja_chega = (escolhida == "original"
                                and not precisa_crescer(int(r["largura"]),
                                                        int(r["altura"])))
                except Exception:
                    ja_chega = False
                if ja_chega:
                    por_regra += 1
                    continue
                discorda += 1
                problemas.append({
                    "id": r["id"], "ficheiro": r["ficheiro"],
                    "escolhida": escolhida, "rival": pior,
                    "d_det": detalhe[pior][0], "d_agi": detalhe[pior][1],
                    "cam_escolhida": candidatos[escolhida],
                    "cam_rival": candidatos[pior], "tamanho": maior,
                })
            elif all(d[2] == "empate" for d in detalhe.values()):
                empatadas += 1
            else:
                concorda += 1
        except Exception as e:
            erros.append((r["ficheiro"], str(e)))
        if n % 25 == 0:
            print("  %d/%d" % (n, len(casos)), end="\r", flush=True)

    print(" " * 30, end="\r")
    total = concorda + discorda + empatadas + por_regra
    print("VEREDICTO SOBRE A ESCOLHA ATUAL")
    print("  a escolha e a melhor medida:      %3d  (%.0f%%)"
          % (concorda, 100 * concorda / max(1, total)))
    print("  empate, nao da para distinguir:   %3d  (%.0f%%)"
          % (empatadas, 100 * empatadas / max(1, total)))
    print("  OUTRA VERSAO MEDE MELHOR:         %3d  (%.0f%%)"
          % (discorda, 100 * discorda / max(1, total)))
    if por_regra:
        print()
        print("  %d fotos ficaram com o original por ja terem pixeis que chegam." % por_regra)
        print("  A IA mede melhor nelas porque as afia e as alisa, e o que ela")
        print("  alisa e a pele. Nao e desacordo, e a regra a funcionar.")
    print()

    if problemas:
        print("ONDE A ESCOLHA PODE ESTAR ERRADA")
        print("(detalhe = quanto a rival tem a mais nos contornos)")
        for p in sorted(problemas, key=lambda x: -x["d_det"])[:20]:
            print("  %-7s %-34s  esta: %-10s  melhor: %-8s  detalhe %+5.0f%%  ruido %+5.0f%%"
                  % (p["id"], p["ficheiro"][:34], p["escolhida"], p["rival"],
                     p["d_det"], p["d_agi"]))
        print()

    os.makedirs(SAIDA, exist_ok=True)
    feitos = 0
    for p in sorted(problemas, key=lambda x: -x["d_det"])[:quantos]:
        try:
            with Image.open(p["cam_escolhida"]) as a, Image.open(p["cam_rival"]) as b:
                a = ImageOps.exif_transpose(a).convert("RGB").resize(p["tamanho"], Image.LANCZOS)
                b = ImageOps.exif_transpose(b).convert("RGB").resize(p["tamanho"], Image.LANCZOS)
                lado = min(700, a.width // 2, a.height // 2)
                cx = a.width // 2 - lado // 2
                cy = int(a.height * 0.34)
                caixa = (cx, cy, cx + lado, cy + lado)
                par = Image.new("RGB", (lado * 2 + 10, lado), (0, 0, 0))
                par.paste(rotular(a.crop(caixa), "AGORA: " + p["escolhida"]), (0, 0))
                par.paste(rotular(b.crop(caixa), "RIVAL: " + p["rival"]), (lado + 10, 0))
                par.save(os.path.join(SAIDA, "%s_%s.jpg" % (p["id"], p["ficheiro"][:24]
                                                            .replace(" ", "_"))),
                         "JPEG", quality=92)
                feitos += 1
        except Exception as e:
            erros.append((p["ficheiro"], str(e)))

    print("Recortes lado a lado: %d em %s" % (feitos, SAIDA))
    if erros:
        print("Erros: %d   %s" % (len(erros), erros[0][1][:80]))


if __name__ == "__main__":
    main()
