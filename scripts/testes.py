# -*- coding: utf-8 -*-
"""Testes de regressao. Cada um existe porque alguma coisa PARTIU de verdade.

Esta era a maior divida tecnica do projeto e estava escrita na decisao 034: cada
correcao ficava de pe so porque eu voltava a medir a mao, e nada avisava se
voltasse a partir. Isto avisa.

REGRA PARA QUEM ACRESCENTAR AQUI: um teste so entra se houver um defeito real
que ele teria apanhado. Nao ha testes de "isto parece bem". Cada um tem escrito
o que aconteceu.

Uso:  py -3.11 scripts/testes.py
      py -3.11 scripts/testes.py --rapido     salta os que leem muitos ficheiros
"""
import csv
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from PIL import Image

import linha_tempo

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALHAS = []
PASSOU = []
SALTADOS = []


def verifica(nome, condicao, detalhe=""):
    (PASSOU if condicao else FALHAS).append((nome, detalhe))
    print("  %s  %-52s %s" % ("ok  " if condicao else "FALHA", nome, detalhe))


def salta(nome, motivo):
    """Um teste que nao pode correr NESTE PC, contado e dito no fim.

    O DEFEITO: os quatro testes da Mesa que precisam de node voltavam para tras com um
    aviso e sem chamar o verifica(). Noutra maquina, ou numa sessao sem node no PATH, o
    total descia de 143 para 139 sem uma unica falha, e quem lesse so o numero do fim nao
    sabia que a Mesa tinha deixado de ser verificada, que e justamente a parte que nao tem
    mais nenhuma guarda. Agora o numero dos saltados sai ao lado dos que passaram.
    """
    SALTADOS.append((nome, motivo))
    print("  saltado  %-49s %s" % (nome, motivo))


# ---------------------------------------------------------------- composicao
def teste_borda_de_subpixel():
    """A coluna de fora tem de dar a cobertura exata, nao um degrau.

    O DEFEITO: a Pillow, ao amostrar fora da imagem, devolvia preto de repente.
    Num sprite branco, deslocamento 0,50 dava 255 e 0,625 dava 0. Num zoom lento
    isso fazia a coluna de fora acender e apagar, e o Tiago via tremor.
    """
    import render
    sp = Image.new("RGB", (400, 400), (255, 255, 255))
    spm = render.com_margem(sp, "preto")
    pior = 0.0
    for k in range(9):
        fx = k / 8.0
        tela = Image.new("RGB", (900, 900), (0, 0, 0))
        render.compor(tela, spm, 400 + fx, 450, 1.0)
        obtido = tela.getpixel((200, 450))[0]
        esperado = 255 * (1 - fx)
        pior = max(pior, abs(obtido - esperado))
    verifica("borda de sub-pixel da a cobertura exata", pior <= 2,
             "erro maximo %.0f de 255" % pior)


def teste_borda_sobre_fundo():
    """Com fundo desfocado a borda tem de esbater, nao encaixar de pixel em pixel.

    O DEFEITO: a primeira correcao do tremor trocou a linha preta a piscar por
    uma borda que saltava de um pixel para o outro. Medido, a coluna ficava nos
    250 durante os oito passos e depois saltava.
    """
    import render
    sp = Image.new("RGB", (400, 400), (255, 255, 255))
    spm = render.com_margem(sp, "esticar")
    vals = []
    for k in range(9):
        fx = k / 8.0
        tela = Image.new("RGB", (900, 900), (60, 60, 60))
        render.compor(tela, spm, 400 + fx, 450, 1.0)
        vals.append(tela.getpixel((200, 450))[0])
    saltos = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
    verifica("borda sobre fundo desfocado esbate", max(saltos) < 60,
             "maior salto %d" % max(saltos))


# ------------------------------------------------------------- linha do tempo
def teste_agenda_das_paragens():
    """A formula tem de bater certo com a agenda real, nos dois modos.

    O DEFEITO: ao tirar a espera inicial dos clips que continuam a fita, a
    agenda mudou e a formula ficou a responder pela agenda velha. Dava 7,15 s
    quando o certo eram 3,3 s: quase quatro segundos entre o anuncio do
    nascimento e os foguetes.
    """
    pior = 0.0
    for n, pnp in ((5, True), (2, False), (4, True), (3, False), (6, True)):
        par = [i / float(max(1, n - 1)) for i in range(n)]
        for k in range(n):
            medido = None
            for q in range(4000):
                p = q / 4000.0
                _, qual, _ = linha_tempo.posicao_com_paragens(
                    p, par, 0.70, parar_no_primeiro=pnp)
                if qual == k:
                    medido = p
                    break
            if medido is None:
                continue
            formula = linha_tempo.inicio_da_paragem(k, n, 0.70, parar_no_primeiro=pnp)
            pior = max(pior, abs(medido - formula))
    verifica("inicio_da_paragem bate com a agenda real", pior < 0.005,
             "erro maximo %.4f" % pior)


def teste_todas_as_marcas_aparecem():
    """Nenhuma marca pode ficar sem o seu momento no ecra.

    O DEFEITO: o Coa e a Clara caem os dois a 24 de novembro. Escolher a marca
    mais proxima da cabeca de leitura fazia empate e o primeiro da lista ganhava
    sempre. "Nasce a Clara" NUNCA chegou a aparecer.
    """
    import montar_v3
    for nome, espec, dur in (("clip A", montar_v3.ESPEC_A, montar_v3.DUR_MARCOS_A),
                             ("clip Tiago", montar_v3.ESPEC_TIAGO, montar_v3.DUR_MARCOS_TIAGO),
                             ("clip Clara", montar_v3.ESPEC_CLARA, montar_v3.DUR_MARCOS_CLARA)):
        ano, marcas, troco, abre = linha_tempo.ler_meses(espec)

        def fr(m):
            return ((m[1] - 1) + (m[0] - 1) / 31.0) / 12.0

        dentro = [m for m in marcas if troco[0] - 1e-4 <= fr(m) <= troco[1] + 1e-4]
        passos = []
        if not dentro or abs(fr(dentro[0]) - troco[0]) > 1e-4:
            passos.append((troco[0], None))
        passos += [(fr(m), m) for m in dentro]
        if not dentro or abs(fr(dentro[-1]) - troco[1]) > 1e-4:
            passos.append((troco[1], None))
        vistas = set()
        for q in range(int(dur * 25)):
            _, qual, _ = linha_tempo.posicao_com_paragens(
                q / 25.0 / dur, [x[0] for x in passos], 0.70, parar_no_primeiro=abre)
            if qual is not None and passos[qual][1]:
                vistas.add(passos[qual][1][2])
        faltam = [m[2] for m in dentro if m[2] not in vistas]
        verifica("%s: todas as marcas aparecem" % nome, not faltam,
                 ("em falta: " + ", ".join(faltam)) if faltam else "%d marcas" % len(dentro))


def teste_marcas_com_imagem_encontram_o_ficheiro():
    """Uma marca que declara imagem tem de a encontrar em disco.

    O DEFEITO: o Tiago largou as quatro imagens em falta na 01-NOVAS, mas com
    os nomes que elas trazem da internet: "kobe, japao.png",
    "Schengen_Agreement_(1985)_signatures.jpg", "gravuras_coa.jpg". A fita
    pedia "kobe.jpg", "schengen.jpg" e "coa.jpg". Tres das quatro marcas
    sairam no render so com palavras, e NADA se queixou: uma imagem em falta
    nao pode parar um render, por isso `imagem_da_marca` devolve None em
    silencio. Aqui e que tem de dar erro.
    """
    import io
    import json
    estado = json.load(io.open(
        os.path.join(REPO, "data", "mesa_estado.json"), encoding="utf-8"))
    faltam, total = [], 0
    for versao in estado.get("versoes", []):
        for c in versao.get("clips", []):
            if c.get("t") != "marcos":
                continue
            _, marcas, _, _ = linha_tempo.ler_meses(c.get("x", ""))
            for dia, mes, rot, _grande, img in marcas:
                if not img:
                    continue
                total += 1
                if linha_tempo.imagem_da_marca(img, 216) is None:
                    faltam.append("%s -> %s" % (rot, img))
    faltam = sorted(set(faltam))
    verifica("marcas com imagem encontram o ficheiro", not faltam,
             ("sem ficheiro: " + "; ".join(faltam)) if faltam
             else "%d referencias" % total)


def teste_fita_da_mesa_e_percorrivel():
    """Uma fita feita na Mesa tem de poder ser andada.

    O DEFEITO A EVITAR: a partir de agora e o Tiago que cria fitas, com o botao
    "+ Fita", e nada o impede de deixar um troco ao contrario (de novembro ate
    janeiro) ou um troco onde nao cai acontecimento nenhum. Nos dois casos o
    render nao rebenta: desenha uma fita vazia a andar sozinha durante catorze
    segundos, que e pior do que rebentar, porque passa despercebido ate ao
    jantar.
    """
    import io
    import json
    estado = json.load(io.open(
        os.path.join(REPO, "data", "mesa_estado.json"), encoding="utf-8"))
    problemas, quantas = [], 0
    for versao in estado.get("versoes", []):
        for j, c in enumerate(versao.get("clips", []), 1):
            if c.get("t") != "marcos":
                continue
            quantas += 1
            onde = "%s clip %d" % (versao.get("id", "?"), j)
            try:
                ano, marcas, troco, _abre = linha_tempo.ler_meses(c.get("x", ""))
            except Exception as e:
                problemas.append("%s: nao se le (%s)" % (onde, e))
                continue
            if troco[1] <= troco[0]:
                problemas.append("%s: troco ao contrario %s" % (onde, troco))
                continue

            def fr(m):
                return ((m[1] - 1) + (m[0] - 1) / 31.0) / 12.0

            dentro = [m for m in marcas
                      if troco[0] - 1e-4 <= fr(m) <= troco[1] + 1e-4]
            if not dentro:
                problemas.append("%s: nenhum acontecimento no troco" % onde)
    verifica("fitas da Mesa sao percorriveis", not problemas,
             ("; ".join(problemas)) if problemas else "%d clips de fita" % quantas)


def teste_musicas_marcadas_encontram_ficheiro():
    """Toda a musica marcada num clip da Mesa tem de chegar a um ficheiro.

    O DEFEITO: os nomes escritos sem ".mp3" davam "em falta" e o video ficava
    mudo do ponto da primeira marca ate ao fim.
    """
    import io
    import json
    import montar_da_mesa
    mus = montar_da_mesa.caminhos_de_musica()
    estado = json.load(io.open(os.path.join(REPO, "data", "mesa_estado.json"), encoding="utf-8"))
    faltam, total = [], 0
    for versao in estado.get("versoes", []):
        for c in versao.get("clips", []):
            f = ((c.get("m") or {}).get("f") or "").strip()
            if not f:
                continue
            total += 1
            if not montar_da_mesa.resolve_musica(f, mus):
                faltam.append("%s: %s" % (versao.get("id"), f))
    verifica("musicas marcadas na Mesa encontram o ficheiro", not faltam,
             ("sem ficheiro: " + "; ".join(faltam)) if faltam else "%d marcas" % total)


def teste_fita_continua_arranca_a_andar():
    """Um clip que continua a fita nao pode comecar parado.

    O DEFEITO: o Tiago viu "ha um gap no movimento na timeline no sapo para o
    tiago". Eram duas paragens seguidas no mesmo sitio, uma no fim do clip
    anterior e outra no inicio do seguinte.
    """
    import montar_v3
    ano, marcas, troco, abre = linha_tempo.ler_meses(montar_v3.ESPEC_TIAGO)
    verifica("clip de continuacao marcado como tal", abre is False, "abre=%s" % abre)

    def fr(m):
        return ((m[1] - 1) + (m[0] - 1) / 31.0) / 12.0

    dentro = [m for m in marcas if troco[0] - 1e-4 <= fr(m) <= troco[1] + 1e-4]
    passos = [troco[0]] if (not dentro or abs(fr(dentro[0]) - troco[0]) > 1e-4) else []
    passos += [fr(m) for m in dentro]
    p0, _, _ = linha_tempo.posicao_com_paragens(0.0, passos, 0.70, parar_no_primeiro=abre)
    p1, _, _ = linha_tempo.posicao_com_paragens(0.01, passos, 0.70, parar_no_primeiro=abre)
    verifica("clip de continuacao arranca a andar", abs(p1 - p0) > 1e-9,
             "deslocou %.5f" % abs(p1 - p0))


def teste_fita_dos_anos_e_cronologica():
    """O ano mais antigo fica a ESQUERDA. A recuar, os numeros vao para a direita.

    O DEFEITO: a primeira versao desenhava 2026 a esquerda e 1995 a direita, ou
    seja a fita ao contrario do tempo. O Tiago: "e ao contrario, quando estamos
    a andar para tras e como se fizessemos um rewind".
    """
    from PIL import ImageStat
    L, A = 960, 540
    a = linha_tempo.anos(L, A, 2026, 1995, [], 0.5, 12.0)
    b = linha_tempo.anos(L, A, 2026, 1995, [], 6.0, 12.0)
    # Ao recuar no tempo, o conteudo desloca-se para a direita: a metade
    # esquerda do ecra fica mais cheia a medida que anos novos entram por la.
    esq = ImageStat.Stat(b.crop((0, 0, L // 2, A))).mean[0]
    verifica("fita dos anos desenhada pela ordem do tempo", esq > 1.0,
             "ha conteudo a esquerda (%.1f)" % esq)


# ------------------------------------------------------------------- imagens
def teste_regra_de_ampliacao_igual():
    """upscale.py e upscale_ia.py tem de dar o MESMO alvo.

    O DEFEITO: 123 dos 134 ficheiros lanczos ficaram com o tamanho da regra
    velha porque o script saltava o que ja existia. Um ficou a 2208x4886 quando
    precisava de 562x1242.
    """
    import upscale, upscale_ia
    piores = []
    for larg, alt in ((368, 1067), (1215, 911), (1125, 2000), (4000, 2672),
                      (805, 1233), (2048, 1536), (1536, 2048), (462, 540),
                      (780, 400), (1315, 1536)):
        b = upscale_ia.alvo(larg, alt)
        a = upscale.alvo(larg, alt)
        # O upscale.py devolve None quando nao ha nada a ampliar, portanto so
        # da para comparar os tamanhos nos casos em que os dois ampliam. Nos
        # outros compara-se o FATOR, que e o que a regra manda ser igual.
        if b[2] <= 1.0:
            if a is not None:
                piores.append("%dx%d: ia nao amplia mas upscale sim" % (larg, alt))
            continue
        if a is None:
            piores.append("%dx%d: upscale nao amplia mas ia sim (%.3f)" % (larg, alt, b[2]))
        elif abs(a[2] - b[2]) > 0.005 or abs(a[0] - b[0]) > 3 or abs(a[1] - b[1]) > 3:
            piores.append("%dx%d: %dx%d f=%.3f vs %dx%d f=%.3f"
                          % (larg, alt, a[0], a[1], a[2], b[0], b[1], b[2]))
    verifica("regra de ampliacao igual nos dois scripts", not piores,
             "; ".join(piores) if piores else "10 casos")


def teste_ampliacao_pequena_usa_lanczos(rapido=False):
    """Abaixo de 1,5 vezes a FINAIS usa o lanczos, decisao 052.

    O DEFEITO QUE ISTO GUARDA: o briefing dizia desde o primeiro dia que ate 1,5
    vezes chegava o lanczos, e o consolidar.py punha sempre a rede neuronal a
    frente. Eram 89 fotografias.
    """
    if rapido:
        return
    import consolidar
    d = "C:/casamento-video-media/upscaled"
    caminho = os.path.join(REPO, "data", "finais.csv")
    if not os.path.isdir(d) or not os.path.exists(caminho):
        return
    tem = {n.split("__")[0] for n in os.listdir(d)}
    indice = {r["id"]: r for r in csv.DictReader(open(caminho, encoding="utf-8-sig"))}
    inv = list(csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig")))
    erradas, total = [], 0
    for r in inv:
        f = consolidar.fator_ampliacao(int(r["largura"]), int(r["altura"]))
        if 1.0 < f < consolidar.LIMITE_LANCZOS and r["id"] in tem:
            total += 1
            origem = indice.get(r["id"], {}).get("origem")
            if origem not in ("lanczos", "restaurada"):
                erradas.append("%s (%s)" % (r["ficheiro"], origem))
    verifica("ampliacao abaixo de 1,5 usa lanczos", not erradas,
             ("%d fora da regra: %s" % (len(erradas), ", ".join(erradas[:3]))) if erradas
             else "%d fotos" % total)


def teste_finais_cobre_o_que_precisa(rapido=False):
    """Nenhuma foto que precise de crescer pode ficar sem tratamento.

    O DEFEITO: o consolidar.py escolhia por ordem de preferencia e nunca
    comparava. 21 fotos ficaram na FINAIS ampliadas sem necessidade, logo mais
    moles do que os proprios originais.
    """
    if rapido:
        return
    import consolidar
    inv = list(csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                   encoding="utf-8-sig")))
    d = r"C:\casamento-video-media\upscaled-ia"
    if not os.path.isdir(d):
        return
    tem = {n.split("__")[0] for n in os.listdir(d)}
    # As vinhetas da fita aparecem a 216 pixeis de altura e nunca inteiras.
    # Exigir-lhes resolucao de ecra cheio mandava a rede neuronal trabalhar
    # oito minutos por imagem para nada.
    vinhetas = consolidar.vinhetas_da_fita()
    # Desde a decisao 052 a rede neuronal so e usada a partir de 1,5 vezes; abaixo
    # disso a FINAIS usa o lanczos, e exigir ali a versao IA mandava trabalhar a
    # rede para nada.
    falta = [r["ficheiro"] for r in inv
             if consolidar.fator_ampliacao(int(r["largura"]), int(r["altura"])) >= consolidar.LIMITE_LANCZOS
             and r["id"] not in tem
             and r["ficheiro"].lower() not in vinhetas]
    verifica("toda a foto que cresce 1,5x ou mais tem versao IA", not falta,
             ("%d em falta" % len(falta)) if falta else "%d fotos" % len(inv))


# ----------------------------------------------------------------- montagens
def teste_render_usa_o_indice(rapido=False):
    """O ficheiro que o render abre tem de ser o que o indice manda.

    O DEFEITO: durante todo o projeto o render.py nunca olhou para a FINAIS.
    Repetia a ordem de preferencia antiga, "restaurada, IA, lanczos, original",
    e por isso usava a versao da rede neuronal tambem em fotografias que ja
    tinham pixeis que chegavam. Eram 62 fotos no inventario e 47 so na v1a.

    Tres copias da mesma regra em tres ficheiros, e a que fazia o video era a
    que estava por corrigir. Este teste existe para que nunca mais haja duas
    respostas a mesma pergunta.
    """
    import io
    import re
    fonte = io.open(os.path.join(REPO, "scripts", "render.py"),
                    encoding="utf-8").read()
    corpo = fonte[fonte.index("def preparar("):] if "def preparar(" in fonte else fonte
    # Nenhuma escolha de versao pode voltar a ser feita a mao dentro do render.
    escolhe_a_mao = re.search(r'for pasta in \(\s*r"C:\\casamento-video-media\\restauradas"',
                              fonte)
    verifica("render nao volta a escolher versao a mao", not escolhe_a_mao,
             "escolhe pelo data/finais.csv")

    caminho = os.path.join(REPO, "data", "finais.csv")
    if not os.path.exists(caminho):
        verifica("indice da FINAIS existe", False, "falta data/finais.csv")
        return
    indice = {r["id"]: r for r in csv.DictReader(
        open(caminho, encoding="utf-8-sig"))}
    finais = r"C:\casamento-video-media\FINAIS"
    if not os.path.isdir(finais):
        return
    faltam = [r["ficheiro"] for r in indice.values()
              if not os.path.exists(os.path.join(finais, r["final"]))]
    verifica("todo o indice aponta para ficheiro que existe", not faltam,
             ("%d em falta" % len(faltam)) if faltam else "%d fotos" % len(indice))

    if rapido:
        return
    # E o render tem de resolver cada clip das montagens sem cair no original
    # por falta de indice.
    import consolidar
    orfas = []
    d = os.path.join(REPO, "data", "montagens")
    for nome in sorted(os.listdir(d)):
        if not nome.endswith(".csv") or nome.endswith(".som.csv"):
            continue
        for r in csv.DictReader(open(os.path.join(d, nome),
                                     encoding="utf-8-sig")):
            # Um lado a lado, colagem ou pilha leva as fotos no id separadas por "|".
            # Comparar o id inteiro com o indice nunca dava com nada, e essas fotos
            # passavam sem se ver se tinham entrada.
            if r.get("tipo") in ("foto", "lado", "colagem", "pilha"):
                for i in (r.get("id") or "").split("|"):
                    if i and i not in indice:
                        orfas.append("%s:%s" % (nome[:-4], i))
    verifica("todo o clip de foto tem entrada no indice", not orfas,
             ("%d sem indice: %s" % (len(orfas), ", ".join(sorted(set(orfas))[:4])))
             if orfas else "8 montagens")


def teste_lado_a_lado():
    """Fotos lado a lado: cabem no ecra, entram de fora e ficam todas no fim.

    O PEDIDO: ate 4 fotos em retangulos iguais, com movimento a entrar, e todas
    no ecra depois de entrarem. Tres em colunas, ou duas com a terceira por cima.
    """
    import render
    for lay, n in render.LAYOUTS_LADO.items():
        cel = render.lado_celulas(lay)
        dentro = all(x >= 0 and y >= 0 and x + w <= render.L and y + h <= render.A
                     for (x, y, w, h), _ in cel)
        verifica("lado %s: %d fotos dentro do ecra" % (lay, n), len(cel) == n and dentro)
        if lay != "3s":
            larguras = [w for (x, y, w, h), _ in cel]
            area = sum(w * h for (x, y, w, h), _ in cel)
            verifica("lado %s: retangulos iguais" % lay, max(larguras) - min(larguras) <= 2,
                     "%.1f%% do ecra com foto" % (100.0 * area / (render.L * render.A)))
    cores = [(200, 30, 30), (30, 200, 30), (30, 30, 200), (200, 200, 30)]
    celulas = []
    for k, ((x, y, w, h), vem) in enumerate(render.lado_celulas("4q")):
        sw = int(math.ceil(w * (1 + render.LADO_ZOOM)))
        sh = int(math.ceil(h * (1 + render.LADO_ZOOM)))
        celulas.append({"rect": (x, y, w, h), "vem": vem, "respira": True,
                        "sprite": render.com_margem(Image.new("RGB", (sw, sh), cores[k]), "preto"),
                        "atraso": render.LADO_ATRASO + k * render.LADO_INTERVALO})
    pronto = {"tipo": "lado", "celulas": celulas, "capa": None}
    ini = render.desenhar(pronto, 0.0, 8.0)
    meio = render.desenhar(pronto, render.LADO_ATRASO + 0.3, 8.0)
    fim = render.desenhar(pronto, 7.9, 8.0)
    centros = [(x + w // 2, y + h // 2) for (x, y, w, h), _ in render.lado_celulas("4q")]
    vazio = all(ini.getpixel(p) == (0, 0, 0) for p in centros)
    a_entrar = meio.getpixel(centros[1]) == (0, 0, 0)
    certas = all(max(abs(a - b) for a, b in zip(fim.getpixel(p), cores[k])) <= 3
                 for k, p in enumerate(centros))
    verifica("lado a lado: vazio, a entrar, e todas no sitio no fim", vazio and a_entrar and certas)


def teste_ponto_de_foco():
    """O corte segue o ponto de foco marcado na Mesa e nunca sai da fotografia.

    O PEDIDO: "tens de me permitir ajustar o ponto do foco da foto, caso contrario
    pode acontecer de sugerires zona em que corta a pessoa".
    """
    import render
    # Uma foto de 2000x1000 em que o valor de cada pixel diz a coluna onde esta.
    im = Image.new("L", (2000, 1000))
    im.putdata([x * 255 // 1999 for y in range(1000) for x in range(2000)])
    im = im.convert("RGB")
    auto = render.cobrir(im, 600, 1000)
    direita = render.cobrir_foco(im, 600, 1000, (0.875, 0.5))
    esquerda = render.cobrir_foco(im, 600, 1000, (0.0, 0.5))
    ok_auto = abs(auto.getpixel((0, 500))[0] - 700 * 255 // 1999) <= 1
    ok_dir = abs(direita.getpixel((0, 500))[0] - 1400 * 255 // 1999) <= 1   # encosta a borda
    ok_esq = esquerda.getpixel((0, 500))[0] == 0 and esquerda.size == (600, 1000)
    verifica("ponto de foco: segue o ponto e encosta as bordas", ok_auto and ok_dir and ok_esq)
    verifica("ponto de foco: le e rejeita o que vem mal escrito",
             render.ler_foco("0.25,0.75") == (0.25, 0.75) and render.ler_foco("") is None
             and render.ler_foco("lixo") is None and render.ler_foco("2,-1") == (1.0, 0.0))


def teste_estado_das_fotos():
    """O botao "Estado das fotos" da Mesa conta cada fotografia uma vez, e so uma.

    O PEDIDO: "podias colocar la um botao para atualizar e para verificar se ja
    analisou as fotos todas". Um retrato que contasse a mesma foto duas vezes, ou
    que deixasse alguma de fora, dizia "em dia" quando nao estava.
    """
    import json
    caminho = os.path.join(REPO, "data", "estado_fotos.json")
    if not os.path.exists(caminho):
        verifica("estado das fotos existe", False, "falta data/estado_fotos.json")
        return
    e = json.load(open(caminho, encoding="utf-8"))
    inv = list(csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig")))
    ids_espera = [x["id"] for x in e["espera"]]
    certo = (e["total"] == len(inv) and e["prontas"] + len(ids_espera) == e["total"]
             and len(set(ids_espera)) == len(ids_espera))
    verifica("estado das fotos conta cada foto uma vez", certo,
             "%d prontas, %d a espera, %d por registar" % (e["prontas"], len(ids_espera), e["por_registar"]))


def teste_previas_cobrem_todas_as_fotos():
    """Toda a fotografia da Mesa tem previa grande, e as folhas cabem na publicacao.

    O DEFEITO: a primeira versao fazia uma previa por foto, 641 ficheiros, e a
    publicacao recusou-a porque o link da Mesa aceita no maximo 256 ficheiros.
    """
    import json
    caminho = os.path.join(REPO, "saida", "previas", "indice.json")
    if not os.path.exists(caminho):
        return
    ind = json.load(open(caminho, encoding="utf-8"))
    inv = list(csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig")))
    faltam = [r["ficheiro"] for r in inv if r["id"] not in ind["pos"]]
    pasta = os.path.join(REPO, "saida", "previas")
    grandes = [f for f in ind["folhas"] if os.path.getsize(os.path.join(pasta, f)) > 15 * 1048576]
    verifica("previas grandes para todas as fotos", not faltam and not grandes and len(ind["folhas"]) < 250,
             ("sem previa: %d" % len(faltam)) if faltam else "%d fotos em %d folhas" % (len(ind["pos"]), len(ind["folhas"])))


def teste_foguetes_antes_das_fotos():
    """As fotografias do bebe so entram depois de os foguetes acabarem.

    O DEFEITO: a conta esquecia o encadeado, e as fotos entravam 0,9 s antes.
    """
    cam = os.path.join(REPO, "data", "montagens", "v3.csv")
    som = os.path.join(REPO, "data", "montagens", "v3.som.csv")
    if not (os.path.exists(cam) and os.path.exists(som)):
        return
    L = list(csv.DictReader(open(cam, encoding="utf-8-sig")))
    S = list(csv.DictReader(open(som, encoding="utf-8-sig")))
    corpo = [r for r in L if r["tipo"] != "video"]
    desvio = float(corpo[0]["inicio_s"])
    fog = sorted([f for f in S if "Candidato" in f["ficheiro"]],
                 key=lambda x: float(x["quando_s"]))
    for f, prox, quem in zip(fog, ("21-46.jpg", "1 (2).jpg"), ("Tiago", "Clara")):
        fim = float(f["quando_s"]) + float(f["dura_s"])
        for r in L:
            if r["ficheiro"] == prox:
                folga = (float(r["inicio_s"]) - desvio) - fim
                verifica("foguetes do %s acabam antes da 1a foto" % quem, folga >= -0.2,
                         "folga %+.1f s" % folga)
                break


def teste_intro_sem_repetir(rapido=False):
    """A abertura nao pode repetir fotografias.

    O DEFEITO: com 24 fotos e uma volta ao principio, via-se a mesma cara duas
    vezes. O Tiago: "existe um certo engasgar nas imagens".
    """
    if rapido:
        return
    import intro_flipbook
    if not os.path.isdir(intro_flipbook.FINAIS):
        salta("abertura nao repete fotografias", "sem a FINAIS neste PC")
        return
    # Desde 21 de setembro a lista sai da montagem do filme, e a ultima e a foto de
    # pouso, que entra no fim do folhear e fica. Tem de aparecer cada uma, uma vez.
    lista, _avisos = intro_flipbook.selecao()
    ids = [f["id"] for f in lista]
    n = len(lista) - 1
    vistas, ultimo = [], None
    for q in range(int(round(intro_flipbook.T_TOTAL * 25))):
        t = q / 25.0
        if t < intro_flipbook.T_ARRANQUE:
            continue
        i, _ = intro_flipbook.indice_da_foto(t, n)
        if i != ultimo:
            vistas.append(i)
            ultimo = i
    verifica("abertura nao repete fotografias",
             len(vistas) == len(set(vistas)) == n + 1 and len(set(ids)) == len(ids),
             "%d mostradas, %d distintas, %d na lista" % (len(vistas), len(set(vistas)), n + 1))


def teste_intro_reparte_clara_e_tiago():
    """A intro Marvel da a Clara e ao Tiago o mesmo tempo de ecra, e acaba nos dois.

    O PEDIDO: a 21 de setembro o Tiago pediu "revermos a Intro da Marvel para ter uma
    distribuicao mais equitativa das fotos da Clara e do Tiago, sendo que idealmente
    deveria acabar com uma foto deles no final quando depois aparece a historia de
    Clara & Tiago". A intro de 12 de setembro tirava 64 fotos da v1a por aritmetica,
    sem saber quem estava em cada uma: pelas etiquetas de hoje, 24 da Clara e 14 do
    Tiago, 4,00 s de ecra contra 1,40.

    Guarda-se: nenhuma foto duas vezes; as tres do pedido (a arvore, o abraco, o brinde)
    e a de pouso fora do folhear, porque o pedido vem logo a seguir a intro; a de pouso
    em ultimo; as POSICOES primeiras todas da Clara e do Tiago, nunca mais de
    SEGUIDAS_MAX seguidas do mesmo; a Clara e o Tiago a menos de 5 por cento em segundos
    de ecra; e as fotos dos dois todas depois.

    O TEMPO MEDE-SE PELO DESENHO, e nao pelos segundos que a lista traz: fotograma a
    fotograma, com o indice_da_foto() e o brilho_do_acender() que o desenhar() usa. Um
    verificador mostrou a 21 de setembro que, medido pela lista, um segundos_por_posicao()
    ao contrario passava (1,48 contra 1,60) quando no ecra ficava 2,08 contra 1,76.

    MUTACOES: (1) metade e metade com as da Clara todas primeiro; (2) o
    segundos_por_posicao() ao contrario. As duas tem de falhar a medida do tempo.
    """
    import intro_flipbook as ib
    nome = "intro reparte a Clara e o Tiago e acaba nos dois"
    if not os.path.isdir(ib.FINAIS):
        salta(nome, "sem a FINAIS neste PC")
        return

    def no_ecra(n):
        """Segundos de cada posicao do folhear, pelo desenho."""
        seg = [0.0] * n
        for q in range(int(round(ib.T_LETRAS * 25))):
            t = q / 25.0
            if t < ib.T_ARRANQUE:
                seg[0] += ib.brilho_do_acender(t) / 25.0
                continue
            i, _ = ib.indice_da_foto(t, n)
            if i < n:
                seg[i] += 1.0 / 25.0
        return seg

    def mede(lista):
        """Os problemas de uma lista, e os segundos da Clara e do Tiago."""
        problemas = []
        ids = [f["id"] for f in lista]
        folhear = lista[:-1]
        if len(set(ids)) != len(ids):
            problemas.append("fotos repetidas")
        no_folhear = {f["id"] for f in folhear}
        dentro = [i for i in list(ib.FOTOS_DO_PEDIDO) + [ib.POUSO] if i in no_folhear]
        if dentro:
            problemas.append("no folhear: %s" % ", ".join(dentro))
        if not lista or lista[-1]["id"] != ib.POUSO or not lista[-1].get("pouso"):
            problemas.append("a ultima nao e a de pouso")
        tempos = no_ecra(len(folhear))
        seg = {"Clara": 0.0, "Tiago": 0.0}
        for k, f in enumerate(folhear):
            if f["classe"] in seg:
                seg[f["classe"]] += tempos[k]
        maior = max(seg.values())
        if maior <= 0 or abs(seg["Clara"] - seg["Tiago"]) / maior >= 0.05:
            problemas.append("Clara %.2f s, Tiago %.2f s" % (seg["Clara"], seg["Tiago"]))
        classes = [f["classe"] for f in folhear]
        primeiras = classes[:ib.POSICOES]
        if any(c not in ("Clara", "Tiago") for c in primeiras):
            problemas.append("nas %d primeiras ha fotos que nao sao da Clara nem do Tiago"
                             % ib.POSICOES)
        seguidas, maior_seguida = 1, 1
        for a, b in zip(primeiras, primeiras[1:]):
            seguidas = seguidas + 1 if a == b else 1
            maior_seguida = max(maior_seguida, seguidas)
        if maior_seguida > ib.SEGUIDAS_MAX:
            problemas.append("%d seguidas do mesmo" % maior_seguida)
        dos_dois = [k for k, c in enumerate(classes) if c == "Ambos"]
        if not dos_dois or min(dos_dois) < ib.POSICOES:
            problemas.append("fotos dos dois fora do fim do folhear")
        return problemas, seg

    lista, _avisos = ib.selecao()
    problemas, seg = mede(lista)
    quantas = {c: sum(1 for f in lista[:-1] if f["classe"] == c) for c in ("Clara", "Tiago")}

    medidas = []
    certa_rep, certa_seg = ib.repartir_por_tempo, ib.segundos_por_posicao
    for rotulo, rep, segf in (
            ("metade e metade com a Clara primeiro",
             lambda segundos, posicoes, disp:
             ["Clara"] * (posicoes // 2) + ["Tiago"] * (posicoes - posicoes // 2), certa_seg),
            ("segundos_por_posicao ao contrario",
             certa_rep, lambda n: list(reversed(certa_seg(n))))):
        try:
            ib.repartir_por_tempo, ib.segundos_por_posicao = rep, segf
            mutada, _ = ib.selecao()
        finally:
            ib.repartir_por_tempo, ib.segundos_por_posicao = certa_rep, certa_seg
        erros_mutada, seg_mutada = mede(mutada)
        medidas.append("%.2f/%.2f" % (seg_mutada["Clara"], seg_mutada["Tiago"]))
        if not any(p.startswith("Clara ") or "seguidas" in p for p in erros_mutada):
            problemas.append("a mutacao %r passou (%.2f s contra %.2f)"
                             % (rotulo, seg_mutada["Clara"], seg_mutada["Tiago"]))
    verifica(nome, not problemas,
             "; ".join(problemas)[:200] if problemas else
             "Clara %d fotos %.2f s, Tiago %d fotos %.2f s; mutacoes %s"
             % (quantas["Clara"], seg["Clara"], quantas["Tiago"], seg["Tiago"],
                ", ".join(medidas)))


def teste_corte_da_intro_nunca_desce():
    """O corte da abertura nunca pode ir abaixo do centro.

    O DEFEITO: o detetor de caras por tom de pele mandou o corte para os
    sapatos, porque calcada e areia contam como pele.
    """
    import intro_flipbook
    im = Image.new("RGB", (600, 1600), (200, 150, 120))
    a = intro_flipbook.cobrir(im, 320, 180, procurar_caras=False)
    b = intro_flipbook.cobrir(im, 320, 180, procurar_caras=True)
    verifica("corte da abertura nao desce abaixo do centro",
             a.size == b.size == (320, 180), "%s" % (b.size,))


def teste_excluidas_saem():
    """As fotos que o Tiago mandou tirar nao podem voltar a entrar."""
    # Verificava so a v1a, e a v1c continuou com os cinco bilhetes durante tres
    # dias: foi gerada antes da decisao 020 e nunca mais refeita.
    import excluidas
    for nome in ("v1a", "v1b", "v1c"):
        cam = os.path.join(REPO, "data", "montagens", nome + ".csv")
        if not os.path.exists(cam):
            continue
        L = list(csv.DictReader(open(cam, encoding="utf-8-sig")))
        dentro = [r["ficheiro"] for r in L if not excluidas.entra(r["ficheiro"])]
        verifica("bilhetes de admiradores fora da %s" % nome, not dentro,
                 ", ".join(dentro) if dentro else "%d excluidas" % len(excluidas.EXCLUIDAS))


def teste_contador_mostra_a_data():
    """A data que o Tiago escreve no contador tem de chegar ao ecra.

    O DEFEITO: a Mesa escreve "2026>1995|4 de outubro de 2026" e o ler_anos so
    aceitava "2026=4 de outubro de 2026". A peca sem "=" era deitada fora e o
    contador saia sem a data do casamento, sem aviso nenhum.
    """
    _, _, marcos = linha_tempo.ler_anos("2026>1995|4 de outubro de 2026")
    _, _, antigos = linha_tempo.ler_anos("2026>1995|2026=4 de outubro de 2026;2012=O encontro")
    # O de datas segue a mesma convencao: um rotulo sem "data=" e o da partida.
    import datetime
    _t, _d, _p, por_datas = linha_tempo.ler_contador(
        "04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido")
    esperadas = [(datetime.date(2026, 10, 4), "4 de outubro de 2026"),
                 (datetime.date(2025, 12, 25), "o pedido")]
    perdidos = [] if por_datas == esperadas else ["o contador por datas deu %r" % (por_datas,)]
    for nome in os.listdir(os.path.join(REPO, "data", "montagens")):
        if not nome.endswith(".csv") or nome.endswith(".som.csv"):
            continue
        for r in csv.DictReader(open(os.path.join(REPO, "data", "montagens", nome), encoding="utf-8-sig")):
            if r.get("tipo") == "contador" and (r["texto_ecra"] or "").partition("|")[2].strip():
                # PELO ler_contador, que le os dois formatos. Com o ler_anos, um x por
                # datas rebentava aqui a tentar ler "04/10/2026" como um ano.
                if not linha_tempo.ler_contador(r["texto_ecra"])[3]:
                    perdidos.append("%s %s" % (nome, r["ordem"]))
    verifica("contador mostra a data escrita na Mesa",
             marcos == [(2026, "4 de outubro de 2026")]
             and antigos == [(2026, "4 de outubro de 2026"), (2012, "O encontro")] and not perdidos,
             ", ".join(perdidos) if perdidos else "%s" % (marcos,))


def _faixas_de_texto(imagem, limiar):
    """Quantas linhas de texto estao desenhadas numa imagem: faixas horizontais
    com pixeis acima do limiar, separadas por filas vazias."""
    so_texto = imagem.convert("L").point(lambda v: 255 if v >= limiar else 0)
    reduzida = so_texto.resize((64, so_texto.height), Image.BOX)
    faixas, dentro = 0, False
    for y in range(reduzida.height):
        tem = reduzida.crop((0, y, 64, y + 1)).getextrema()[1] > 0
        if tem and not dentro:
            faixas += 1
        dentro = tem
    return faixas


def teste_legenda_guarda_as_falas():
    """Cada linha escrita numa legenda continua a ser uma linha no ecra.

    O DEFEITO: as legendas de dialogo da v3 tem uma fala por linha, e o render
    juntava tudo antes de quebrar. As falas colavam-se e a frase partia a meio.
    Mede-se o que o render desenha de facto, na legenda e no cartao, para o
    teste falhar se alguem voltar a achatar o texto em qualquer um dos dois.
    """
    import render
    fala = "- Clara, gostas dessa canção do Ed Sheeran? \n- Gosto! \n- Então não a estragues..."
    _, mascara = render.faixa_texto(fala)
    na_legenda = _faixas_de_texto(mascara, 250)
    no_cartao = _faixas_de_texto(render.cartao("- Queres?\n- Quero muito."), 200)
    verifica("legenda e cartao guardam uma fala por linha", na_legenda == 3 and no_cartao == 2,
             "legenda com %d linhas, cartao com %d" % (na_legenda, no_cartao))


def teste_fim_em_fade_a_preto():
    """O ultimo fotograma do filme e preto, e o som acaba a descer com ele.

    O DEFEITO: o filme acabava na ultima foto em cheio e a musica cortava a meio
    de um refrao. A regra do CLAUDE.md pede um fim inequivoco, com fade a preto.
    Testa-se a funcao que o ciclo dos fotogramas chama e o som construido pelo
    construir_som, e nao so a conta.
    """
    import re
    import subprocess
    import tempfile
    import render
    fim = 100.0
    total = int(round(fim * render.FPS))
    cheio = Image.new("RGB", (32, 18), (200, 200, 200))
    antes = render.aplicar_fim(cheio, total - int((render.FADE_FIM_IMAGEM + 0.5) * render.FPS), fim, None)
    ultimo = render.aplicar_fim(cheio, total - 1, fim, None)
    parcial = render.aplicar_fim(cheio, total - 1, fim, 40.0)
    imagem_ok = (antes.getpixel((0, 0))[0] == 200 and ultimo.getpixel((0, 0))[0] <= 10
                 and parcial.getpixel((0, 0))[0] == 200)

    ff = render.ffmpeg()
    pasta = tempfile.gettempdir()
    tom = os.path.join(pasta, "teste_fim_tom.wav")
    som = os.path.join(pasta, "teste_fim_som.m4a")
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=12:sample_rate=48000", tom], capture_output=True)
    entradas = [{"ficheiro": "tom", "caminho": tom, "quando": 0.0, "in_s": 0.0, "dura": 10.0,
                 "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0}]
    render.construir_som(ff, entradas, 10.0, som, render.FADE_FIM_SOM)

    def volume(ss, t):
        r = subprocess.run([ff, "-hide_banner", "-nostats", "-ss", str(ss), "-t", str(t), "-i", som,
                            "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        m = re.search(r"mean_volume: ([-\d.]+) dB", r.stderr or "")
        return float(m.group(1)) if m else 0.0

    # A descida propria da faixa so comeca 1 s antes do fim; aos 7,5 s so a do fim do
    # filme, que comeca aos 6 s, ja pode estar a baixar o som.
    meio, a_descer = volume(3.0, 1.0), volume(7.5, 0.5)
    verifica("o filme acaba em fade a preto, imagem e som",
             imagem_ok and a_descer < meio - 3.0,
             "ultimo fotograma %d de 200; som %.1f dB a meio, %.1f dB a descer"
             % (ultimo.getpixel((0, 0))[0], meio, a_descer))


def teste_musica_marcada_sem_silencio_a_abrir():
    """Uma musica marcada na Mesa ouve-se no clip onde ele a pos.

    O DEFEITO: a do Antonio Variacoes tem 2,47 s de silencio no inicio do ficheiro.
    A anterior ja tinha acabado de desvanecer e ficava um vale mudo no cartao
    "Paixao pelo desporto". Verifica-se a funcao, o caso de um silencio mais
    comprido do que a janela, e que a montagem v3 a usa mesmo: nenhuma musica
    marcada pode ficar a comecar em silencio.
    """
    import subprocess
    import tempfile
    import montar_da_mesa
    import render
    ff = render.ffmpeg()

    def sintetico(nome, calado):
        caminho = os.path.join(tempfile.gettempdir(), nome)
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=%g" % calado,
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=3:sample_rate=48000",
                        "-filter_complex", "[1]aformat=channel_layouts=stereo[s];[0][s]concat=n=2:v=0:a=1",
                        caminho], capture_output=True)
        return caminho

    curto = sintetico("teste_silencio_a_abrir.wav", 2)
    longo = sintetico("teste_silencio_longo.wav", 25)
    a = montar_da_mesa.silencio_no_inicio(curto)
    b = montar_da_mesa.silencio_no_inicio(curto, 2.5)
    c = montar_da_mesa.silencio_no_inicio(longo)
    presas = []
    cam_som = os.path.join(REPO, "data", "montagens", "v3.som.csv")
    if os.path.exists(cam_som):
        for r in csv.DictReader(open(cam_som, encoding="utf-8-sig")):
            if (r.get("nota") or "").startswith("marcada na Mesa") and os.path.exists(r["caminho"]):
                s = montar_da_mesa.silencio_no_inicio(r["caminho"], float(r["in_s"] or 0))
                if s:
                    presas.append("%s com %.2f s mudos" % (r["ficheiro"][:30], s))
    verifica("musica marcada salta o silencio a abrir",
             abs(a - 2.0) < 0.2 and b == 0.0 and c == 0.0 and not presas,
             "; ".join(presas) if presas else "%.2f s a abrir, %.2f a meio, %.2f num silencio longo" % (a, b, c))


def teste_musica_da_abertura_retoma_na_fita_da_clara():
    """Quando a fita volta para as noticias antes da Clara, volta a musica da abertura.

    O PEDIDO: o Tiago nao queria que o Rei Leao continuasse pela fita do Guterres ate
    ao nascimento da Clara, e sim que a musica de antes do nascimento do Tiago
    continuasse onde tinha parado, fosse ela qual fosse.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # antes do redirect: o render mexe no sys.stdout ao ser importado
    caminho_estado = os.path.join(REPO, "data", "mesa_estado.json")
    if not os.path.exists(caminho_estado):
        return
    est = json.load(open(caminho_estado, encoding="utf-8"))
    v = next((x for x in est.get("versoes", []) if x.get("id") == "demo_v3"), None)
    if not v:
        verifica("musica da abertura retoma na fita antes da Clara", False, "sem a demo_v3 na copia local")
        return
    # A abertura verdadeira, sem os videos, ate umas fotos depois do cartao da Clara.
    clips = [dict(c) for c in v["clips"] if c.get("t") != "video"]
    fim = next(k for k, c in enumerate(clips)
               if c.get("t") == "cartao" and "nasce uma bebe" in montar_da_mesa.sem_acentos(c.get("x")))
    base = clips[:fim + 4]
    for c in base:
        c.pop("m", None)

    def monta(cl):
        pasta = tempfile.mkdtemp(prefix="teste_retoma_")
        caminho = os.path.join(pasta, "estado.json")
        json.dump({"versoes": [{"id": "t", "nome": "t", "clips": cl}]}, open(caminho, "w", encoding="utf-8"),
                  ensure_ascii=False)
        guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
        sys.argv = ["montar_da_mesa.py", "t", "--nome", "t"]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                montar_da_mesa.main()
        finally:
            montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
        return (list(csv.DictReader(open(os.path.join(pasta, "t.csv"), encoding="utf-8-sig"))),
                list(csv.DictReader(open(os.path.join(pasta, "t.som.csv"), encoding="utf-8-sig"))))

    efeitos = (montar_da_mesa.VINHETA, montar_da_mesa.REBOBINAR)

    def confere(linhas, som, esperada):
        desvio = next(float(l["inicio_s"]) for l in linhas if l["tipo"] != "video")
        leitos = [r for r in som if r["ficheiro"] not in efeitos and float(r["dura_s"]) > 0.4]
        foguetes = sorted(float(r["quando_s"]) for r in som if "foguetes" in r["nota"])
        if len(foguetes) < 2:
            return "sem os foguetes dos dois nascimentos"
        t_tiago, t_clara = foguetes[0], foguetes[1]
        voltas = [float(l["inicio_s"]) - desvio for l in linhas
                  if l["tipo"] == "marcos" and t_tiago < float(l["inicio_s"]) - desvio < t_clara]
        if not voltas:
            return "sem fita entre os dois nascimentos"

        def a_tocar(t):
            return [r for r in leitos if float(r["quando_s"]) - 0.01 <= t < float(r["quando_s"]) + float(r["dura_s"])]
        abertura = a_tocar(1.0)
        if len(abertura) != 1 or not abertura[0]["ficheiro"].startswith(esperada):
            return "na abertura tocam %s" % [r["ficheiro"][:24] for r in abertura]
        onde = float(abertura[0]["in_s"]) + float(abertura[0]["dura_s"])
        volta = a_tocar(voltas[0] + 1.0)
        if (len(volta) != 1 or volta[0]["ficheiro"] != abertura[0]["ficheiro"]
                or abs(float(volta[0]["in_s"]) - onde) > 0.05):
            return "na fita que volta tocam %s" % [(r["ficheiro"][:24], r["in_s"]) for r in volta]
        if float(volta[0]["quando_s"]) + float(volta[0]["dura_s"]) > t_clara + 0.05:
            return "a retoma passa por cima dos foguetes da Clara"
        return ""

    erros = []
    e = confere(*monta(base), esperada="Lang Lang")
    if e:
        erros.append("sem marcas: " + e)
    # A abertura marcada na Mesa, no primeiro clip do corpo: e ela que retoma, e toca sozinha.
    com_abertura = [dict(c) for c in base]
    com_abertura[0]["m"] = {"f": "Tiago Celebration Song (Reggae)", "in": 0}
    e = confere(*monta(com_abertura), esperada="Tiago Celebration")
    if e:
        erros.append("abertura marcada: " + e)
    # Uma musica marcada numa foto do Tiago: a retoma e da abertura e acaba nos foguetes da Clara.
    com_tiago = [dict(c) for c in base]
    k = next(k for k, c in enumerate(com_tiago)
             if c.get("t") == "foto" and k > next(j for j, x in enumerate(com_tiago) if x.get("t") == "cartao"))
    com_tiago[k]["m"] = {"f": "Tiago Celebration Song (Reggae)", "in": 0}
    e = confere(*monta(com_tiago), esperada="Lang Lang")
    if e:
        erros.append("musica nas fotos do Tiago: " + e)
    verifica("musica da abertura retoma na fita antes da Clara", not erros,
             "; ".join(erros) if erros else "sem marcas, com a abertura marcada e com musica nas fotos do Tiago")


def teste_cartao_da_bebe_com_acento():
    """O cartao do nascimento da Clara e encontrado com "bebe" ou com "bebé".

    O DEFEITO que isto evita: a procura era por "bebe" tal e qual. Se o Tiago
    corrigir o cartao para "bebé", os foguetes da Clara e o esticamento do cartao
    deixavam de acontecer, sem aviso.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # antes do redirect: o render mexe no sys.stdout ao ser importado
    # Monta de verdade uma versao pequena, sem fita, com o cartao escrito com acento,
    # numa pasta temporaria: os foguetes da Clara tem de aparecer no som.
    pasta = tempfile.mkdtemp(prefix="teste_bebe_")
    estado = {"versoes": [{"id": "teste_bebe", "nome": "teste bebe", "clips": [
        {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0041", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "cartao", "x": "2 meses e 12 dias depois, nasce uma bebé", "d": 3.6, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0169", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0172", "d": 4, "c": 0.7, "r": "fiel"}]}]}
    caminho = os.path.join(pasta, "estado.json")
    json.dump(estado, open(caminho, "w", encoding="utf-8"), ensure_ascii=False)
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    sys.argv = ["montar_da_mesa.py", "teste_bebe", "--nome", "teste_bebe"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
    notas = [r["nota"] for r in csv.DictReader(open(os.path.join(pasta, "teste_bebe.som.csv"), encoding="utf-8-sig"))]
    verifica("cartao da bebe encontrado com ou sem acento",
             any("primeiro texto da Clara" in n for n in notas) and montar_da_mesa.sem_acentos(None) == "",
             "%d faixas no som de ensaio" % len(notas))


def teste_data_do_contador_nao_pisca():
    """A data do casamento no contador acende e apaga a desvanecer.

    O DEFEITO: o rotulo era cortado quando a velocidade da fita passava de 1,2, o
    que acontece dois fotogramas depois de ela arrancar. A data sumia de 97% para
    nada em 40 ms. Mede-se o brilho da faixa do rotulo em todos os fotogramas do
    contador da v3 e a maior queda de um fotograma para o seguinte.
    """
    marcos = [(2026, "4 de outubro de 2026")]
    # A faixa desceu a 18 de setembro com a legenda: passou de 0,10 para 0,16 de A abaixo
    # da linha, a mesma altura do contador por datas (teste_contadores_sao_a_mesma_fita).
    # Comeca aos 796 e nao antes porque ate aos 790 esta o bico de baixo do ponteiro, que
    # e fixo e punha o "vazio" alto de mais para a medida dizer alguma coisa.
    faixa = (460, 796, 1460, 856)
    vazio = linha_tempo.anos(1920, 1080, 2026, 1995, [], 1.5, 9.0).crop(faixa).convert("L").getextrema()[1]
    picos = [linha_tempo.anos(1920, 1080, 2026, 1995, marcos, q / 25.0, 9.0).crop(faixa).convert("L").getextrema()[1]
             for q in range(0, 9 * 25)]
    topo = max(picos) - vazio
    queda = max(picos[i] - picos[i + 1] for i in range(len(picos) - 1))
    verifica("data do contador desvanece em vez de piscar", topo > 100 and queda <= 0.35 * topo,
             "maior queda %d num brilho de %d" % (queda, topo))


# --------------------------------------------- o contador por datas, 17 de setembro
# O Tiago: "O rebobinar inicial cria-me na mesa um que rebobina da data de hoje ate a
# data de 25 de dezembro de 2025 (...) Depois rebobina para 1995 como ja esta
# implementado." A abertura passou a ter DOIS contadores a recuar.

# REFEITAS A 18 DE SETEMBRO, E DE PROPOSITO. As de 17 de setembro eram do desenho em que
# o ponteiro nao se via (1,27 para 1), o contador de anos nao tinha regua e a legenda
# estava a outra altura da do contador por datas; o Tiago aceitou a correcao de
# legibilidade, e ela passa por todos os fotogramas deste contador, porque o ponteiro esta
# em todos. Foram tiradas do render.py e do linha_tempo.py desta ronda, pelo caminho do
# render: preparar() e desenhar(). Na prova da v3 inteira contra o codigo de antes, os
# dois contadores foram os unicos clips com fotogramas diferentes (scratchpad
# aproxima/prova/prova_v3.py).
#
# O ANDAMENTO NAO MUDOU, e ve-se aqui: os fotogramas que eram iguais entre si continuam a
# se-lo. Os quatro 1995 parados tem uma assinatura so (antes 8c798b0e..., agora
# c67cc0b4...), e as duas partidas de 2026 tambem. Uma correcao que mexesse na agenda
# das paragens partia estas classes.
#
# Uma Pillow nova pode mudar a reamostragem e com ela todas: ai refazem-se a partir do
# render.py e do linha_tempo.py anteriores a essa mudanca, nunca dos de agora.
ASSINATURAS_CONTADOR_ANOS = {
    "1995>2011 @ 0.00": "c67cc0b496164960fce487a71b28708f",
    "1995>2011 @ 2.00": "c67cc0b496164960fce487a71b28708f",
    "1995>2011 @ 5.00": "d7be916c45ce3b8fb183e558f0fd111d",
    "1995>2011 @ 8.90": "312041b96fc9974448188a67c8cee414",
    "2026>1995|2026=4 de outubro  @ 0.00": "634f7e8cd3dcf64b092a54fc4bd3140e",
    "2026>1995|2026=4 de outubro  @ 12.90": "c67cc0b496164960fce487a71b28708f",
    "2026>1995|2026=4 de outubro  @ 3.30": "6cc13d26e6e84723a64f0e9ba07b6110",
    "2026>1995|2026=4 de outubro  @ 7.15": "cf57344aa0e02bd226ffd17305c70678",
    "2026>1995|4 de outubro de 20 @ 0.00": "634f7e8cd3dcf64b092a54fc4bd3140e",
    "2026>1995|4 de outubro de 20 @ 1.50": "64ace1ac9567035d219592600f684653",
    "2026>1995|4 de outubro de 20 @ 2.80": "5610ccc1a5eeb32ece06984e82d96ce5",
    "2026>1995|4 de outubro de 20 @ 4.50": "d0c66cbdfcc4d4704c00e81db2c43c9b",
    "2026>1995|4 de outubro de 20 @ 6.20": "ca6ca3c482fdd8e3a40fd5236d6d26af",
    "2026>1995|4 de outubro de 20 @ 8.90": "c67cc0b496164960fce487a71b28708f",
}
CASOS_CONTADOR_ANOS = (
    ("2026>1995|4 de outubro de 2026", 9.0, (0.0, 1.5, 2.8, 4.5, 6.2, 8.9)),
    ("2026>1995|2026=4 de outubro de 2026;2012=O encontro", 13.0, (0.0, 3.3, 7.15, 12.9)),
    ("1995>2011", 9.0, (0.0, 2.0, 5.0, 8.9)),
)


def _assinaturas_do_contador(render):
    """md5 de cada fotograma do contador de anos, pelo caminho do render."""
    import hashlib
    fora = {}
    for x, dur, ts in CASOS_CONTADOR_ANOS:
        pronto = render.preparar({"tipo": "contador", "texto_ecra": x}, {})
        for t in ts:
            im = render.desenhar(pronto, t, dur)
            fora["%s @ %.2f" % (x[:28], t)] = hashlib.md5(im.tobytes()).hexdigest()
    return fora


def teste_contador_de_anos_igual_ao_byte():
    """O contador de anos desenha exatamente o que foi aprovado, ao byte.

    O PEDIDO de 17 de setembro: o de anos fica como esta. E a peca que ja esta no filme,
    com a data do casamento por cima do 2026 e o rasto a rebobinar ate 1995; o contador
    por datas entra ANTES dela e nao no lugar dela. Mede-se pelo caminho do render, o
    mesmo que faz o video: um preparar() que mandasse o x de anos para o desenho novo dava
    outro filme sem falhar coisa nenhuma, e era isso que ninguem ia ver.

    A 18 de setembro o desenho mudou de proposito (ponteiro, regua e legenda legiveis a
    15 metros, ver ASSINATURAS_CONTADOR_ANOS) e as assinaturas foram refeitas. O teste
    continua a guardar a mesma coisa: que ninguem o muda sem querer.
    """
    import hashlib
    import render
    agora = _assinaturas_do_contador(render)
    problemas = []
    if sorted(agora) != sorted(ASSINATURAS_CONTADOR_ANOS):
        problemas.append("os casos de controlo mudaram: %s" % sorted(agora))
    diferentes = sorted(k for k in agora if agora[k] != ASSINATURAS_CONTADOR_ANOS.get(k))
    if diferentes:
        problemas.append("diferente de antes em %s" % ", ".join(diferentes))
    # E O X POR DATAS TEM DE DAR OUTRA COISA. Se desse um destes fotogramas era porque nao
    # chegou ao desenho novo, e a igualdade de cima nao provava nada.
    pronto = render.preparar({"tipo": "contador",
                              "texto_ecra": "04/10/2026>25/12/2025|4 de outubro de 2026"}, {})
    if pronto.get("modo") != "datas":
        problemas.append("o x por datas foi preparado como %r" % pronto.get("modo"))
    conhecidas = set(ASSINATURAS_CONTADOR_ANOS.values())
    for t in (0.5, 4.5, 8.5):
        if hashlib.md5(render.desenhar(pronto, t, 9.0).tobytes()).hexdigest() in conhecidas:
            problemas.append("o de datas aos %.1f s desenha um fotograma do de anos" % t)
    verifica("contador de anos igual ao byte ao de antes", not problemas,
             "; ".join(problemas)[:200] if problemas else "%d fotogramas" % len(agora))


def teste_contador_por_datas_anda_dia_a_dia():
    """A fita das datas anda dia a dia, so por datas que existem, e para nas duas pontas.

    O DEFEITO QUE ISTO EVITA: contar em meses ou em fracoes de ano para desenhar uma data
    inventa dias que nao existem, e um "30 FEV 2026" ao centro do ecra do casamento nao e
    um pormenor. Conta-se em dias inteiros somados a uma data, que nunca inventa nenhuma, e
    mede-se o que sai: as duas pontas certas, nada fora do intervalo, e nenhum salto de
    mais de um dia enquanto a fita anda devagar, que e quando se le.

    E mede-se que o DESENHO segue esta conta: numa paragem a faixa da data nao pode mexer
    um pixel, e quando a data muda tem de mudar. Sem isso o desenho podia estar a fazer a
    sua propria conta e estes numeros nao diziam nada sobre o ecra.
    """
    import contextlib
    import datetime
    import hashlib
    import io
    import render
    problemas = []
    casos = (("04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido", 9.0),
             ("25/12/2025>04/10/2026|o pedido", 9.0),        # tambem serve a avancar
             ("01/03/2026>29/02/2024|x", 12.0),              # tres anos, e um 29 de fevereiro
             ("10/01/2026>05/01/2026|x", 6.0))               # cinco dias
    for x, dur in casos:
        tipo, de, para, marcos = linha_tempo.ler_contador(x)
        if tipo != "datas":
            problemas.append("%s lido como %s" % (x[:20], tipo))
            continue
        seq = [linha_tempo.data_do_instante(de, para, marcos, q / 25.0, dur)
               for q in range(int(dur * 25) + 1)]
        datas = [s[0] for s in seq]
        if datas[0] != de or datas[-1] != para:
            problemas.append("%s: comeca em %s e acaba em %s" % (x[:20], datas[0], datas[-1]))
        if min(datas) < min(de, para) or max(datas) > max(de, para):
            problemas.append("%s: sai do intervalo" % x[:20])
        for i in range(len(seq) - 1):
            if abs(seq[i + 1][3] - seq[i][3]) <= 1.0 and abs((datas[i + 1] - datas[i]).days) > 1:
                problemas.append("%s: salta %d dias com a fita devagar"
                                 % (x[:20], abs((datas[i + 1] - datas[i]).days)))
                break
        # E A DATA E A DO DIA MAIS PROXIMO, e nao a do dia ja passado. Trocar o
        # int(round(pos)) por int(pos) trunca, e a data ao centro fica ate um dia atras em
        # quase todo o percurso; nada aqui distinguia as duas coisas, porque as pontas, o
        # intervalo e os saltos sobrevivem as duas. Mede-se FORA das paragens, que e onde
        # elas se separam.
        baixo = min(de, para)
        fora_das_paragens = [s for s in seq if s[1] is None]
        errados = [s for s in fora_das_paragens
                   if s[0] != baixo + datetime.timedelta(days=int(round(s[3])))]
        if errados:
            problemas.append("%s: %d instantes em que a data nao e a do dia mais proximo "
                             "(%s com pos %.3f)"
                             % (x[:20], len(errados), errados[0][0], errados[0][3]))
        if len(fora_das_paragens) < 10:
            problemas.append("%s: so %d instantes fora das paragens, nao se mede nada"
                             % (x[:20], len(fora_das_paragens)))
    # SO DATAS DO CALENDARIO: o texto do meio tem de voltar a dar a data de onde veio, em
    # todos os dias de tres anos. Um "31 ABR" ou um "29 FEV 2025" nao passam aqui.
    meses = {m: k + 1 for k, m in enumerate(linha_tempo.MESES_CURTOS)}
    dia = datetime.date(2024, 1, 1)
    while dia < datetime.date(2027, 1, 1):
        d, m, a = linha_tempo.texto_da_data(dia).split()
        if datetime.date(int(a), meses[m], int(d)) != dia:
            problemas.append("texto_da_data nao volta a dar %s" % dia)
            break
        dia += datetime.timedelta(days=1)
    # O DESENHO SEGUE A CONTA. Mede-se a faixa da data grande, acima da linha, E TAMBEM A
    # BANDA DA REGUA, por baixo dela.
    #
    # O DEFEITO QUE A SEGUNDA FAIXA APANHA: o recorte era so (0, 400, 1920, 600) e a linha
    # da regua esta em y = 0,60 x 1080 = 648, ou seja fora dele. Somar um dia dentro do
    # x_de() da funcao datas() desenhava a regua e os nomes dos meses uma casa ao lado,
    # 18,9 px, com a data grande ao centro parada onde estava: o ponteiro do meio deixava
    # de bater no dia que o numero anuncia e a suite inteira passava na mesma. Num contador
    # de 9 s na abertura isso vai ao jantar sem uma queixa.
    faixa = (0, 400, 1920, 600)
    # A banda da regua e so a dos NOMES DOS MESES e do ano de janeiro, por baixo da linha
    # (676 a 790). Acima disso passa a marca vermelha do marco, que acende e apaga dentro
    # da propria paragem, e abaixo esta o rotulo, que faz o mesmo: os dois punham a banda a
    # mexer com a fita parada e a medida nao dizia nada sobre a regua.
    faixa_regua = (0, 676, 1920, 790)
    tipo, de, para, marcos = linha_tempo.ler_contador(casos[0][0])
    # Guardam-se DUAS imagens, nao mais: o ciclo compara sempre q com q+1, e 225
    # fotogramas de 1920x1080 em memoria sao 1,4 GB.
    feitas = {}

    def imagem(t):
        if t not in feitas:
            if len(feitas) > 2:
                feitas.clear()
            feitas[t] = linha_tempo.datas(1920, 1080, de, para, marcos, t, 9.0)
        return feitas[t]

    def assina(t, onde=faixa):
        return hashlib.md5(imagem(t).crop(onde).tobytes()).hexdigest()

    parados, mexeu, regua_parada, regua_mexeu = [], 0, [], 0
    for q in range(int(9.0 * 25)):
        a = linha_tempo.data_do_instante(de, para, marcos, q / 25.0, 9.0)
        b = linha_tempo.data_do_instante(de, para, marcos, (q + 1) / 25.0, 9.0)
        if a[0] == b[0] and a[1] is not None and b[1] is not None and a[3] == b[3]:
            parados.append(assina(q / 25.0) == assina((q + 1) / 25.0))
            regua_parada.append(assina(q / 25.0, faixa_regua) == assina((q + 1) / 25.0, faixa_regua))
        elif a[0] != b[0]:
            mexeu += assina(q / 25.0) != assina((q + 1) / 25.0)
            regua_mexeu += assina(q / 25.0, faixa_regua) != assina((q + 1) / 25.0, faixa_regua)
    if not all(parados) or len(parados) < 30:
        problemas.append("a faixa da data mexe com a fita parada (%d de %d)"
                         % (sum(1 for v in parados if not v), len(parados)))
    if mexeu < 20:
        problemas.append("a faixa da data so mudou %d vezes com a data a mudar" % mexeu)
    if not all(regua_parada):
        problemas.append("a regua mexe com a fita parada (%d de %d)"
                         % (sum(1 for v in regua_parada if not v), len(regua_parada)))
    if regua_mexeu < 20:
        problemas.append("a regua so mudou %d vezes com a data a mudar" % regua_mexeu)
    # E O PONTEIRO BATE NO DIA QUE O NUMERO ANUNCIA. Com a fita parada num marco, a marca
    # vermelha desse marco e desenhada em x_de(data) e tem de cair no meio do ecra, que e
    # onde esta o ponteiro. E a unica medida que prende a regua ao numero: as assinaturas
    # de cima dizem se ela mexe, nao dizem onde ela esta.
    def centro_da_marca(t):
        px = imagem(t).load()
        colunas = [x for x in range(1920)
                   if any(px[x, y][0] > 90 and px[x, y][0] > px[x, y][1] + 40
                          for y in range(int(1080 * 0.60) - 20, int(1080 * 0.60) + 20))]
        return (colunas[0] + colunas[-1]) / 2.0 if colunas else None

    centros = [(q / 25.0, centro_da_marca(q / 25.0)) for q in range(int(9.0 * 25))]
    marcados = [(t, x) for t, x in centros if x is not None]
    if len(marcados) < 10:
        problemas.append("a marca vermelha so aparece em %d fotogramas" % len(marcados))
    fora = [(t, x) for t, x in marcados if abs(x - 960) > 3]
    if fora:
        problemas.append("a marca do dia em que a fita para cai em x=%.0f e o ponteiro "
                         "esta em 960 (t=%.2f s)" % (fora[0][1], fora[0][0]))
    # E MOSTRA A DATA DA CONTA, nao uma qualquer. Dois contadores parados no arranque, com
    # datas de PARTIDA a um dia de distancia, tem de desenhar faixas diferentes; com a
    # mesma partida e chegadas diferentes, iguais. Parados nao ha rasto a mascarar nada.
    def faixa_parada(x):
        _t, d2, p2, m2 = linha_tempo.ler_contador(x)
        return hashlib.md5(linha_tempo.datas(1920, 1080, d2, p2, m2, 0.2, 9.0)
                           .crop(faixa).tobytes()).hexdigest()

    if faixa_parada("04/10/2026>25/12/2025|x") == faixa_parada("05/10/2026>25/12/2025|x"):
        problemas.append("4 e 5 de outubro desenham a mesma faixa")
    if faixa_parada("04/10/2026>25/12/2025|x") != faixa_parada("04/10/2026>26/12/2025|x"):
        problemas.append("a data de partida desenhada mudou com a de chegada")
    # ACIMA DE TRES ANOS NAO SE USA: a regua de meses nao se le e cada fotograma salta
    # semanas. O preparar troca para o contador de anos e diz que trocou.
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        largo = render.preparar({"tipo": "contador", "texto_ecra": "04/10/2026>04/10/2020|x"}, {})
    if largo.get("modo") != "anos" or largo["de"] != 2026 or largo["para"] != 2020:
        problemas.append("seis anos ficaram em %r" % (largo,))
    if "contador de anos" not in log.getvalue():
        problemas.append("seis anos trocaram de desenho sem aviso")
    verifica("contador por datas anda dia a dia, so por datas que existem", not problemas,
             "; ".join(problemas)[:220] if problemas else
             "4 pares de datas, 1096 dias de texto, %d fotogramas parados iguais" % len(parados))


# ------------------------------------- os dois contadores leem-se a 15 metros, 18 set
# O QUE ESTAVA MEDIDO, e que o Tiago aceitou corrigir: o ponteiro do centro era desenhado
# a (38,30,36) sobre o fundo (10,8,12), 1,27 para 1, invisivel durante a viagem; os nomes
# dos meses da regua estavam a 32 px em cinzento escuro; nos dois extremos metade da regua
# ficava sem um unico traco; e as duas fitas nao se liam como a mesma peca, com o algarismo
# grande a 131 px numa e 101 px na outra e a legenda a duas alturas.
Y_LINHA = int(1080 * 0.60)


def _filas_com_tinta(imagem, faixa, limiar, maximo=None):
    """As filas da faixa que tem pixeis acima do limiar. (primeira, ultima, quantas).

    Com `maximo`, uma fila so conta se tiver MENOS do que esse numero de pixeis acesos:
    e como se separa a regua da linha do tempo, que atravessa o ecra inteiro.
    """
    recorte = imagem.crop(faixa).convert("L")
    filas = []
    for y in range(recorte.height):
        linha = recorte.crop((0, y, recorte.width, y + 1))
        quantos = sum(1 for v in linha.getdata() if v >= limiar)
        if quantos and (maximo is None or quantos < maximo):
            filas.append(faixa[1] + y)
    return (filas[0], filas[-1], len(filas)) if filas else (None, None, 0)


def _contadores_de_ensaio(com_marco=False):
    """Um fotograma de cada contador no mesmo momento da viagem: parado na partida."""
    import datetime
    marcos_anos = [(2026, "4 de outubro de 2026")] if com_marco else []
    marcos_datas = ([(datetime.date(2026, 10, 4), "4 de outubro de 2026")] if com_marco else [])
    return (linha_tempo.anos(1920, 1080, 2026, 1995, marcos_anos, 1.5, 9.0),
            linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                              datetime.date(2025, 12, 25), marcos_datas, 1.5, 9.0))


def teste_contadores_sao_a_mesma_fita():
    """O contador de anos e o de datas leem-se como a MESMA fita.

    O DEFEITO: eram duas pecas diferentes no mesmo filme, a seguir uma a outra. O
    algarismo grande tinha 131 px num e 101 px no outro, a legenda do marco estava a
    0,10 de A num e a 0,16 no outro, e o de anos nem regua tinha. A 15 metros isso nao se
    le como uma fita a rebobinar de 2026 ate 1995: le-se como dois desenhos que alguem
    juntou. Mede-se nos fotogramas, que e o que vai ao jantar.
    """
    import datetime
    problemas = []
    a, d = _contadores_de_ensaio()
    # 1. O ALGARISMO GRANDE. So a coluna do meio, para os anos vizinhos, que sao mais
    # pequenos de proposito, nao entrarem na conta.
    meio = (760, 380, 1160, 620)
    alto_a = _filas_com_tinta(a, meio, 200)
    alto_d = _filas_com_tinta(d, meio, 200)
    if abs(alto_a[2] - alto_d[2]) > 4:
        problemas.append("o algarismo grande tem %d px nos anos e %d nas datas"
                         % (alto_a[2], alto_d[2]))
    # E A MESMA ALTURA NO ECRA, e nao so o mesmo tamanho: com a data 30 px acima do ano, na
    # passagem a corte seco de um contador para o outro o numero saltava (verificador,
    # mutacao C11). A primeira e a ultima fila de tinta, com 2 px de folga, como a legenda.
    if None in alto_a[:2] or None in alto_d[:2] or \
            abs(alto_a[0] - alto_d[0]) > 2 or abs(alto_a[1] - alto_d[1]) > 2:
        problemas.append("o algarismo grande vai de %s nos anos e de %s nas datas"
                         % (alto_a[:2], alto_d[:2]))
    if alto_a[2] < 120:
        problemas.append("o algarismo grande tem so %d px: a 15 metros nao se le" % alto_a[2])
    # 2. A LEGENDA DO MARCO, a mesma altura nos dois.
    am, dm = _contadores_de_ensaio(com_marco=True)
    faixa_rotulo = (0, Y_LINHA + 100, 1920, Y_LINHA + 250)
    rot_a = _filas_com_tinta(am, faixa_rotulo, 150)
    rot_d = _filas_com_tinta(dm, faixa_rotulo, 150)
    if rot_a[0] is None or rot_d[0] is None:
        problemas.append("a legenda nao aparece num deles (%s, %s)" % (rot_a, rot_d))
    elif abs(rot_a[0] - rot_d[0]) > 2 or abs(rot_a[1] - rot_d[1]) > 2:
        problemas.append("a legenda vai de %s nos anos e de %s nas datas"
                         % (rot_a[:2], rot_d[:2]))
    # 3. A REGUA, do mesmo lado e com o mesmo aspeto. As filas da regua sao as que tem
    # tinta mas nao atravessam o ecra: a linha do tempo tem 1920 pixeis acesos.
    # SEM A COLUNA DO MEIO: o ponteiro tambem e uma linha vertical por baixo da linha do
    # tempo, e a contar com ele todas as filas tinham tinta e a medida nao dizia nada. E
    # ate 30 px abaixo da linha: dai para baixo comecam os nomes dos meses, que so o
    # contador por datas tem, e sao medidos no teste deles.
    faixa_regua = (0, Y_LINHA - 40, 900, Y_LINHA + 30)
    reg_a = _filas_com_tinta(a, faixa_regua, 40, maximo=400)
    reg_d = _filas_com_tinta(d, faixa_regua, 40, maximo=400)
    for nome, reg in (("anos", reg_a), ("datas", reg_d)):
        if reg[0] is None or reg[0] <= Y_LINHA:
            problemas.append("a regua do contador de %s nao esta toda por baixo da linha (%s)"
                             % (nome, reg[:2]))
    if reg_a[:2] != reg_d[:2]:
        problemas.append("a regua ocupa %s nos anos e %s nas datas" % (reg_a[:2], reg_d[:2]))
    # 4. O MESMO RASTO, e a prova e que os dois passam pela mesma conta: tirar-lhe a conta
    # tem de mudar os dois fotogramas. Mede-se a meio da viagem, que e onde ha rasto.
    def a_correr():
        return (linha_tempo.anos(1920, 1080, 2026, 1995, [], 4.5, 9.0),
                linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                  datetime.date(2025, 12, 25), [], 4.5, 9.0))

    viagem = a_correr()
    certo = linha_tempo._rasto
    try:
        linha_tempo._rasto = lambda px_s, unidade: (0, 0.0)
        sem = a_correr()
    finally:
        linha_tempo._rasto = certo
    quietos = [n for n, (x, y) in zip(("anos", "datas"), zip(viagem, sem))
               if x.tobytes() == y.tobytes()]
    if quietos:
        problemas.append("o rasto de %s nao passa pelo _rasto(): tirar a conta nao mudou "
                         "o fotograma" % ", ".join(quietos))
    # E PELA MESMA CONTA COM A MESMA UNIDADE. Passar pelo _rasto() nao chegava: com o passo
    # de um dia no lugar do de um ano, o contador por datas dava quatro copias sempre que a
    # fita andava e um rasto preso a 7,6 px, outro rasto a mesma velocidade (verificador,
    # mutacao C12). A unidade e o passo de um ano do contador de anos, L . 0,30, nos dois.
    unidades = []
    try:
        linha_tempo._rasto = lambda px_s, unidade: (unidades.append(unidade) or certo(px_s, unidade))
        a_correr()
    finally:
        linha_tempo._rasto = certo
    if len(unidades) != 2 or any(abs(u - 1920 * 0.30) > 1.0 for u in unidades):
        problemas.append("o rasto e contado com as unidades %s, e nos dois devia ser o passo "
                         "de um ano, %.0f px" % (["%.1f" % u for u in unidades], 1920 * 0.30))
    # MUTACOES: cada uma e o estado de ANTES de uma das tres medidas, posta so no contador
    # por datas, que e como um deles se separava do outro sem ninguem dar por isso.
    real = linha_tempo.ImageFont.truetype

    def com(mudanca):
        """Desenha o contador por datas com uma alteracao so nele."""
        guardado = {k: getattr(linha_tempo, k) for k in mudanca}
        try:
            for k, v in mudanca.items():
                setattr(linha_tempo, k, v)
            return linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                     datetime.date(2025, 12, 25),
                                     [(datetime.date(2026, 10, 4), "4 de outubro de 2026")],
                                     1.5, 9.0)
        finally:
            for k, v in guardado.items():
                setattr(linha_tempo, k, v)

    def encolhe(caminho, tamanho=10, *a_, **k):
        return real(caminho, int(1080 * 0.13) if tamanho == int(1080 * linha_tempo.CORPO_NUMERO)
                    else tamanho, *a_, **k)

    try:
        linha_tempo.ImageFont.truetype = encolhe
        pequeno = linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                    datetime.date(2025, 12, 25), [], 1.5, 9.0)
    finally:
        linha_tempo.ImageFont.truetype = real
    if abs(_filas_com_tinta(pequeno, meio, 200)[2] - alto_a[2]) <= 4:
        problemas.append("com o algarismo de antes (0,13 de A) a medida deu o mesmo: nao "
                         "distingue os dois tamanhos")
    # A data 30 px mais acima so no contador por datas: e a unica peca com espacos no
    # algarismo grande, e e por ai que se separa do ano.
    texto_real = linha_tempo._texto
    corpo_grande = int(1080 * linha_tempo.CORPO_NUMERO)

    def acima(d_, txt, fonte, x, y, cor, centro=True):
        subir = 30 if (" " in txt and getattr(fonte, "size", 0) == corpo_grande) else 0
        return texto_real(d_, txt, fonte, x, y - subir, cor, centro)
    try:
        linha_tempo._texto = acima
        subida = _filas_com_tinta(linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                                    datetime.date(2025, 12, 25), [], 1.5, 9.0),
                                  meio, 200)
    finally:
        linha_tempo._texto = texto_real
    if subida[:2] == alto_d[:2] or (subida[0] is not None and abs(subida[0] - alto_a[0]) <= 2):
        problemas.append("com a data 30 px acima a medida deu o mesmo (%s)" % (subida[:2],))
    if _filas_com_tinta(com({"Y_ROTULO": 0.10}), faixa_rotulo, 150)[:2] == rot_d[:2]:
        problemas.append("com a legenda a 0,10 de A a medida deu o mesmo")
    if _filas_com_tinta(com({"REGUA_MAIOR_ALTO": 40}), faixa_regua, 40, maximo=400)[:2] == reg_d[:2]:
        problemas.append("com a regua mais alta a medida deu o mesmo")
    verifica("os dois contadores sao a mesma fita", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "algarismo %d px, legenda em %s, regua em %s nos dois"
             % (alto_a[2], rot_a[:2], reg_a[:2]))


def teste_ponteiro_do_contador_le_se():
    """O ponteiro do centro tem de se ver durante a viagem, nos dois contadores, e inteiro.

    O DEFEITO, medido: era desenhado a (38,30,36) sobre o fundo (10,8,12), 1,27 para 1.
    O ponteiro e o UNICO ponto fixo do ecra, e e por ele que se percebe que os numeros
    estao a passar por algum sitio; invisivel, a fita e so numeros a deslizar. A regra de
    contraste e a do texto do CLAUDE.md, 4,5 para 1.
    """
    import datetime
    problemas = []
    quadros = {"anos": linha_tempo.anos(1920, 1080, 2026, 1995, [], 4.5, 9.0),
               "datas": linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                          datetime.date(2025, 12, 25), [], 4.5, 9.0)}
    # A 120 px abaixo da linha nao passa mais nada: os nomes da regua ficam acima e a
    # legenda do marco abaixo. O que estiver ali e o ponteiro.
    medidos = {}
    for nome, im in quadros.items():
        cor = im.getpixel((960, Y_LINHA + 120))
        medidos[nome] = linha_tempo.contraste(cor, linha_tempo.FUNDO)
        if medidos[nome] < 4.5:
            problemas.append("o ponteiro do contador de %s da %.2f para 1 em %s"
                             % (nome, medidos[nome], (cor,)))
    # E O MESMO PONTEIRO NOS DOIS, inteiro: a mesma largura e os mesmos bicos. Um pixel so
    # nao dizia nada da forma, e um fio de 1 px sem bicos no contador por datas passava
    # (verificador, mutacao C16): a 15 metros nao se ve, e as duas fitas deixavam de ter a
    # mesma cabeca de leitura. Conta-se, fila a fila, quantas colunas acesas ha a volta do
    # centro, nas filas onde so passa o ponteiro: entre o fim do algarismo e a linha, e
    # entre os nomes dos meses e a legenda.
    def perfil(im):
        filas = list(range(Y_LINHA - int(1080 * linha_tempo.PONTEIRO_CIMA), Y_LINHA - 45)) + \
            list(range(Y_LINHA + 85, Y_LINHA + int(1080 * linha_tempo.PONTEIRO_BAIXO) + 1))
        cinza = im.crop((930, 0, 991, 1080)).convert("L")
        return [sum(1 for v in cinza.crop((0, y, 61, y + 1)).getdata() if v >= 60) for y in filas]

    perfis = {nome: perfil(im) for nome, im in quadros.items()}
    if perfis["anos"] != perfis["datas"]:
        problemas.append("o ponteiro nao e o mesmo nos dois contadores (colunas acesas por fila: "
                         "%s e %s)" % (perfis["anos"][:6], perfis["datas"][:6]))
    for nome, pf in perfis.items():
        if not pf or min(pf) < linha_tempo.PONTEIRO_LARGURA or max(pf) < 3 * linha_tempo.PONTEIRO_LARGURA:
            problemas.append("o ponteiro do contador de %s tem de %s a %s colunas: sem a largura "
                             "ou sem os bicos" % (nome, min(pf or [0]), max(pf or [0])))
    certo_p = linha_tempo._ponteiro

    def fino(d_, L_, A_, y_):
        d_.line([(L_ // 2, y_ - int(A_ * linha_tempo.PONTEIRO_CIMA)),
                 (L_ // 2, y_ + int(A_ * linha_tempo.PONTEIRO_BAIXO))], fill=linha_tempo.PONTEIRO, width=1)
    try:
        linha_tempo._ponteiro = fino
        perfil_fino = perfil(linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                               datetime.date(2025, 12, 25), [], 4.5, 9.0))
    finally:
        linha_tempo._ponteiro = certo_p
    if perfil_fino == perfis["anos"]:
        problemas.append("com um ponteiro de 1 px sem bicos nas datas a medida deu o mesmo")
    # E PARADO NUM DIA, O TRACO DO DIA NAO LHE ABRE UM ENTALHE. Caia na coluna do ponteiro e
    # era pintado por cima, na cor da regua: 2 x 10 px a 2,5 para 1 logo abaixo da linha,
    # nas duas paragens do contador por datas (verificador, 18 de setembro).
    def pior_entalhe():
        pior = 99.0
        for faz in (lambda t: linha_tempo.anos(1920, 1080, 2026, 1995, [], t, 9.0),
                    lambda t: linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                                datetime.date(2025, 12, 25), [], t, 9.0)):
            for t in (0.0, 1.5, 8.9):
                im = faz(t)
                for x in range(959, 962):
                    for y in range(Y_LINHA + 3, Y_LINHA + 10):
                        pior = min(pior, linha_tempo.contraste(im.getpixel((x, y)), linha_tempo.FUNDO))
        return pior
    entalhe = pior_entalhe()
    if entalhe < 4.5:
        problemas.append("parado, o ponteiro tem um entalhe logo abaixo da linha: %.2f para 1" % entalhe)
    certo_t = linha_tempo._tapado_pelo_ponteiro
    try:
        linha_tempo._tapado_pelo_ponteiro = lambda x, L_, nitidez: False
        entalhe_antes = pior_entalhe()
    finally:
        linha_tempo._tapado_pelo_ponteiro = certo_t
    if entalhe_antes >= 4.5:
        problemas.append("com o traco do dia por cima do ponteiro a medida nao viu o entalhe (%.2f)"
                         % entalhe_antes)
    # MUTACAO: a cor de antes. Se a medida nao descer abaixo de 4,5 com ela, nao estava a
    # medir o ponteiro nenhum.
    certa = linha_tempo.PONTEIRO
    try:
        linha_tempo.PONTEIRO = (38, 30, 36)
        antigo = linha_tempo.anos(1920, 1080, 2026, 1995, [], 4.5, 9.0)
    finally:
        linha_tempo.PONTEIRO = certa
    if linha_tempo.contraste(antigo.getpixel((960, Y_LINHA + 120)), linha_tempo.FUNDO) >= 4.5:
        problemas.append("com a cor de antes a medida continuou acima de 4,5: o ponto "
                         "medido nao e o do ponteiro")
    # E NAO SE ABRE UM BURACO NELE QUANDO O MARCO ACENDE. O risco vermelho do marco fica em
    # cima do ponteiro quando a fita para num marco, e era pintado a subir do preto: nos
    # 0,5 s em que a legenda acende e apaga, o meio do ponteiro ficava a (15,4,6), 1,05 para
    # 1, e ele partia-se em dois (verificador, 18 de setembro: 14 fotogramas no contador de
    # anos da v3, 28 no de datas). Mede-se junto a linha, onde o risco passa.
    marcados = {
        "anos": lambda t: linha_tempo.anos(1920, 1080, 2026, 1995, [(2026, "4 de outubro de 2026")], t, 9.0),
        "datas": lambda t: linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                             datetime.date(2025, 12, 25),
                                             [(datetime.date(2026, 10, 4), "4 de outubro de 2026")], t, 9.0)}
    piores = {}
    for nome, faz in marcados.items():
        for t in (0.04, 0.08, 0.2, 2.6, 2.7):
            cor = faz(t).getpixel((960, Y_LINHA - 15))
            piores[nome] = min(piores.get(nome, 99), linha_tempo.contraste(cor, linha_tempo.FUNDO))
            if linha_tempo.contraste(cor, linha_tempo.FUNDO) < 3.0:
                problemas.append("aos %.2f s o meio do ponteiro do contador de %s fica %s, %.2f "
                                 "para 1" % (t, nome, (cor,), linha_tempo.contraste(cor, linha_tempo.FUNDO)))
                break
    # MUTACAO: o risco a subir do preto, como estava.
    certo_risco = linha_tempo._risco_do_marco
    try:
        linha_tempo._risco_do_marco = lambda tela, d, x0, y, alfa: d.line(
            [(x0, y - 26), (x0, y + 26)], fill=tuple(int(c * alfa) for c in linha_tempo.MARCO), width=6)
        buraco = marcados["anos"](0.08).getpixel((960, Y_LINHA - 15))
    finally:
        linha_tempo._risco_do_marco = certo_risco
    if linha_tempo.contraste(buraco, linha_tempo.FUNDO) >= 3.0:
        problemas.append("com o risco a subir do preto a medida nao viu o buraco: %s" % (buraco,))
    verifica("o ponteiro do contador ve-se durante a viagem", not problemas,
             "; ".join(problemas)[:200] if problemas else
             "anos %.1f para 1, datas %.1f para 1; com o marco a acender, pelo menos %.1f e %.1f; "
             "de %d a %d colunas nos dois; parado, %.1f para 1 debaixo da linha"
             % (medidos["anos"], medidos["datas"], piores["anos"], piores["datas"],
                min(perfis["anos"]), max(perfis["anos"]), entalhe))


def teste_meses_da_regua_leem_se():
    """Os nomes dos meses da regua com tamanho e contraste de quem le a 15 metros.

    O DEFEITO: 32 px em (128,114,122), que da 4,4 para 1. Numa sala com metade das pessoas
    de costas e o ecra a 15 metros, isso e texto que so quem esta na primeira mesa le, e a
    regra do CLAUDE.md e clara: texto grande, alto contraste, branco sobre escuro. Ou se
    le, ou sai do ecra. O ano em letra miuda por baixo de janeiro saiu, e a razao esta na
    funcao: o ano ja vai por extenso na data grande.
    """
    import datetime
    problemas = []
    im = linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                           datetime.date(2025, 12, 25), [], 1.5, 9.0)
    # Sem a coluna do meio, que e a do ponteiro, e sem a metade direita, para o nome que
    # calha ao pe do centro nao se colar ao ponteiro na medida.
    faixa = (0, Y_LINHA + 30, 900, Y_LINHA + 100)
    primeira, ultima, quantas = _filas_com_tinta(im, faixa, 100)
    if quantas < 30:
        problemas.append("as letras dos meses tem %d px de altura" % quantas)
    # O CONTRASTE E O TRACO MEDEM-SE NOS PIXEIS, e nao na constante: desenhar os nomes na
    # cor de antes com a constante intacta, ou em letra fina, passava (verificador, C5 e C6).
    def letras(imagem):
        """(contraste da cor mais clara das letras, corrida horizontal mediana de tinta)."""
        rec = imagem.crop(faixa)
        dados = rec.tobytes()
        clara = max((dados[k:k + 3] for k in range(0, len(dados), 3)),
                    key=lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
        cinza = rec.convert("L")
        corridas = []
        for y in range(cinza.height):
            fila, n = cinza.crop((0, y, cinza.width, y + 1)).tobytes(), 0
            for v in fila:
                if v >= 100:
                    n += 1
                elif n:
                    corridas.append(n)
                    n = 0
            if n:
                corridas.append(n)
        corridas.sort()
        return (linha_tempo.contraste(tuple(clara), linha_tempo.FUNDO),
                corridas[len(corridas) // 2] if corridas else 0)
    contraste_px, traco = letras(im)
    if contraste_px < 4.5:
        problemas.append("as letras dos meses dao %.2f para 1 no fotograma" % contraste_px)
    if traco < 6:
        problemas.append("o traco das letras dos meses tem %d px: letra fina" % traco)
    # E NADA DE LETRA MIUDA POR BAIXO: entre a regua e a legenda do marco nao pode ficar
    # texto que so se le de perto. Na partida, na viagem e na chegada, e na largura toda
    # menos as colunas do ponteiro: o ano miudo por baixo de janeiro so aparecia a partir do
    # meio da viagem e na paragem final, a direita, e uma guarda so aos 1,5 s e na metade
    # esquerda deixava-o voltar (verificador, mutacao C19). Sem marcos nao ha ali nada; com
    # o marco, cada bloco de tinta tem de ter pelo menos o corpo da legenda.
    def miudas(com_marco, regua=None):
        """[(t, altura)] dos blocos de tinta abaixo dos nomes que nao podiam estar la."""
        maus = []
        guardada = linha_tempo._regua
        try:
            if regua:
                linha_tempo._regua = regua
            for t in (0.0, 1.5, 4.5, 6.5, 8.9):
                fot = linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                        datetime.date(2025, 12, 25),
                                        [(datetime.date(2025, 12, 25), "Natal de 2025")] if com_marco else [],
                                        t, 9.0)
                cinza = fot.crop((0, Y_LINHA + 90, 1920, Y_LINHA + 300)).convert("L")
                px = cinza.load()
                colunas = list(range(0, 944)) + list(range(977, 1920))
                filas = [y for y in range(cinza.height) if any(px[x, y] >= 60 for x in colunas)]
                ini = None
                for k, y in enumerate(filas):
                    if ini is None:
                        ini = y
                    if k + 1 == len(filas) or filas[k + 1] > y + 3:
                        if not com_marco or y - ini + 1 < 30:
                            maus.append((t, y - ini + 1))
                        ini = None
        finally:
            linha_tempo._regua = guardada
        return maus
    miudos = miudas(False) + miudas(True)
    if miudos:
        problemas.append("ha letra miuda por baixo dos nomes dos meses: %s" % miudos[:4])
    regua_real = linha_tempo._regua

    def com_ano_miudo(d_, L_, A_, y_, ancora, menor, maiores, nitidez, fonte=None):
        regua_real(d_, L_, A_, y_, ancora, menor, maiores, nitidez, fonte)
        f30 = linha_tempo.ImageFont.truetype(linha_tempo.FONTE, 30)
        for x, _dentro, nome in maiores:
            if nome == "JAN":
                linha_tempo._texto(d_, "2026", f30, x, y_ + 130, linha_tempo.ANO_LONGE)
    if not miudas(False, com_ano_miudo):
        problemas.append("com o ano miudo de volta por baixo de janeiro a medida nao o viu")
    # MUTACAO: o tamanho e a cor de antes.
    guardado = (linha_tempo.CORPO_ROTULO, linha_tempo.REGUA_TEXTO)
    try:
        linha_tempo.CORPO_ROTULO, linha_tempo.REGUA_TEXTO = 32, (128, 114, 122)
        antigo = linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                   datetime.date(2025, 12, 25), [], 1.5, 9.0)
        antes_altura = _filas_com_tinta(antigo, faixa, 100)[2]
    finally:
        linha_tempo.CORPO_ROTULO, linha_tempo.REGUA_TEXTO = guardado
    if antes_altura >= 30:
        problemas.append("com os 32 px de antes a medida deu %d: nao distingue os dois"
                         % antes_altura)
    # MUTACOES das duas medidas de pixel: a cor de antes so no desenho, e a letra fina.
    guardado = linha_tempo.REGUA_TEXTO
    try:
        linha_tempo.REGUA_TEXTO = (128, 114, 122)
        cor_antiga = letras(linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                              datetime.date(2025, 12, 25), [], 1.5, 9.0))[0]
    finally:
        linha_tempo.REGUA_TEXTO = guardado
    real = linha_tempo.ImageFont.truetype

    def fina(caminho, tamanho=10, *a, **k):
        return real(linha_tempo.FONTE_FINA if (caminho == linha_tempo.FONTE and tamanho == linha_tempo.CORPO_ROTULO)
                    else caminho, tamanho, *a, **k)
    try:
        linha_tempo.ImageFont.truetype = fina
        traco_fino = letras(linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                              datetime.date(2025, 12, 25), [], 1.5, 9.0))[1]
    finally:
        linha_tempo.ImageFont.truetype = real
    if cor_antiga >= 4.5 or traco_fino >= 6:
        problemas.append("com a cor de antes (%.2f) ou a letra fina (%d px) a medida nao mudou"
                         % (cor_antiga, traco_fino))
    # E NENHUM NOME ENCOSTA AO PONTEIRO. Parada a 4 de outubro, a tinta do "OUT" acabava a
    # 7 px da linha do ponteiro, e a 15 metros lia-se "OUT|" (verificador, 18 de setembro).
    # Nas colunas ate 12 px de cada lado da linha nao pode haver letra, parada ou a andar.
    def encostados(faz):
        quando = []
        for k in range(0, 37):
            t = 9.0 * k / 36.0
            fotograma = faz(t)
            for x0, x1 in ((946, 957), (963, 975)):
                if fotograma.crop((x0, Y_LINHA + 40, x1, Y_LINHA + 78)).convert("L").getextrema()[1] >= 60:
                    quando.append(round(t, 2))
                    break
        return quando

    def faz_datas(t):
        return linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4), datetime.date(2025, 12, 25),
                                 [], t, 9.0)
    colados = encostados(faz_datas)
    if colados:
        problemas.append("um nome de mes encosta ao ponteiro aos %s s" % colados[:5])
    guardados = (linha_tempo.NOME_PERTO, linha_tempo.NOME_LONGE)
    try:
        linha_tempo.NOME_PERTO, linha_tempo.NOME_LONGE = -1000, -999
        colados_sem = encostados(faz_datas)
    finally:
        linha_tempo.NOME_PERTO, linha_tempo.NOME_LONGE = guardados
    if 1.5 not in colados_sem and 1.25 not in colados_sem:
        problemas.append("sem o desvanecer a medida nao viu o OUT encostado na partida (%s)"
                         % colados_sem[:5])
    verifica("os nomes dos meses da regua leem-se a 15 metros", not problemas,
             "; ".join(problemas)[:200] if problemas else
             "%d px de altura, %.1f para 1 no fotograma, traco de %d px, nenhum colado ao ponteiro"
             % (quantas, contraste_px, traco))


def teste_regua_atravessa_o_ecra():
    """A regua tem tracos de uma borda a outra em qualquer instante, nos dois contadores.

    O DEFEITO: os tracos so existiam dentro da viagem. Nos dois extremos, que e onde a
    fita esta parada e onde toda a gente esta a ler, metade do ecra ficava sem um unico
    traco e a fita parecia acabar a meio. Uma fita que acaba a meio do ecra nao e uma
    fita: e uma barra. Mede-se onde estao os tracos GRANDES, os que passam da altura dos
    pequenos, porque sao esses que dao a estrutura.
    """
    import datetime
    problemas = []
    limite = 1920 * 0.32        # um pouco mais do que o maior passo, o de um ano ou de um mes
    # (o buraco da mutacao vai do centro a borda, perto de 960 px, e nao ha ponteiro a meio)
    faixa = (Y_LINHA + linha_tempo.REGUA_MENOR_ALTO + 2, Y_LINHA + linha_tempo.REGUA_MAIOR_ALTO)

    def colunas(im):
        """Os x que tem traco grande nesta faixa de filas.

        O ponteiro tambem passa por aqui, ao centro, e conta como um traco. Nao faz mal e
        nao se tira: o buraco que isto procura vai do centro a uma das bordas, com o
        ponteiro numa das pontas, e tem quase mil pixeis na mesma. Tira-lo era pior,
        porque apagava tambem o traco verdadeiro que calha no meio do ecra.
        """
        px = im.load()
        return [x for x in range(1920)
                if any(px[x, y][0] > 40 for y in range(faixa[0], faixa[1]))]

    def mede(nome, faz):
        for k in range(10):
            xs = colunas(faz(9.0 * k / 9.0))
            if not xs:
                problemas.append("%s aos %.1f s: a regua nao tem traco nenhum" % (nome, k))
                return
            saltos = max([xs[0] + 1] + [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
                         + [1920 - xs[-1]])
            if saltos > limite:
                problemas.append("%s aos %.1f s: %d px de ecra sem um traco"
                                 % (nome, k, saltos))
                return

    mede("anos", lambda t: linha_tempo.anos(1920, 1080, 2026, 1995, [], t, 9.0))
    mede("datas", lambda t: linha_tempo.datas(1920, 1080, datetime.date(2026, 10, 4),
                                              datetime.date(2025, 12, 25), [], t, 9.0))
    # MUTACAO: a regua so dentro da viagem, que era o que estava no filme.
    certa = linha_tempo._regua
    achou = []
    try:
        linha_tempo._regua = (lambda d, L, A, y, ancora, menor, maiores, nitidez, fonte=None:
                              certa(d, L, A, y, ancora, menor,
                                    [m for m in maiores if m[1]], nitidez, fonte))
        for nome, faz in (("anos", lambda t: linha_tempo.anos(1920, 1080, 2026, 1995, [], t, 9.0)),
                          ("datas", lambda t: linha_tempo.datas(
                              1920, 1080, datetime.date(2026, 10, 4),
                              datetime.date(2025, 12, 25), [], t, 9.0))):
            xs = colunas(faz(0.0))
            saltos = max([xs[0] + 1] + [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
                         + [1920 - xs[-1]]) if xs else 1920
            achou.append((nome, saltos))
    finally:
        linha_tempo._regua = certa
    quietos = [n for n, s in achou if s <= limite]
    if quietos:
        problemas.append("com a regua so dentro da viagem, %s continuou sem buraco: a "
                         "medida nao apanha o defeito de antes" % ", ".join(quietos))
    verifica("a regua atravessa o ecra em qualquer instante", not problemas,
             "; ".join(problemas)[:200] if problemas else
             "10 instantes em cada contador, buraco maior %d px na mutacao"
             % max(s for _n, s in achou))


# A pasta da ultima montagem de ensaio, para quem precisar dos ficheiros e nao so das
# linhas: o som_para_mesa.py e o render.som_do_ficheiro() leem do disco, pelo nome.
ULTIMA_PASTA_MONTAGEM = [""]


def _monta_em_pasta(clips, nome="t", focos=None):
    """Corre o montar_da_mesa sobre estes clips, numa pasta temporaria. Devolve (linhas, som, saida).

    `focos` sao os pontos de foco da Mesa (est.focos), {id: [x, y]}.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # antes do redirect: o render mexe no sys.stdout ao ser importado
    pasta = tempfile.mkdtemp(prefix="teste_monta_")
    ULTIMA_PASTA_MONTAGEM[0] = pasta
    caminho = os.path.join(pasta, "estado.json")
    estado = {"versoes": [{"id": "t", "nome": "t", "clips": clips}]}
    if focos:
        estado["focos"] = focos
    json.dump(estado, open(caminho, "w", encoding="utf-8"), ensure_ascii=False)
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    sys.argv = ["montar_da_mesa.py", "t", "--nome", nome]
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
    return (list(csv.DictReader(open(os.path.join(pasta, nome + ".csv"), encoding="utf-8-sig"))),
            list(csv.DictReader(open(os.path.join(pasta, nome + ".som.csv"), encoding="utf-8-sig"))),
            log.getvalue())


def teste_rebobinar_em_cada_contador_que_recua():
    """O som de fita vai por cima de cada contador que recua, e so desses.

    O DEFEITO: o som era colocado com uma procura por "o contador", a primeira linha de
    tipo contador que aparecesse, e so acontecia dentro do bloco do nascimento do Tiago.
    Com dois contadores a recuar na abertura, o segundo recuava trinta anos em silencio, e
    ninguem se queixava porque nao ha aviso nenhum para som que nao existe.
    """
    import montar_da_mesa
    clips = [
        {"t": "contador", "x": "04/10/2026>25/12/2025|hoje;25/12/2025=o pedido",
         "d": 9, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "contador", "x": "2025>1995|25 de dezembro de 2025", "d": 9, "c": 0.7, "r": "fiel"},
        {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0041", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "contador", "x": "1995>2011", "d": 9, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0169", "d": 4, "c": 0.7, "r": "fiel"},
    ]
    linhas, som, _saida = _monta_em_pasta(clips)
    desvio = float(linhas[0]["inicio_s"])
    fitas = sorted(float(r["quando_s"]) for r in som
                   if r["ficheiro"] == montar_da_mesa.REBOBINAR)
    esperado = []
    for l in linhas:
        if l["tipo"] == "contador" and linha_tempo.contador_recua(l["texto_ecra"]):
            esperado.append(round(float(l["inicio_s"]) - desvio + float(l["duracao_s"]) * 0.30, 2))
    problemas = []
    if len(esperado) != 2:
        problemas.append("a montagem de ensaio tem %d contadores a recuar" % len(esperado))
    if len(fitas) != len(esperado) or any(abs(a - b) > 0.02 for a, b in zip(fitas, esperado)):
        problemas.append("rebobinar em %s, esperava %s" % (fitas, esperado))
    duracoes = {round(float(r["dura_s"]), 2) for r in som
                if r["ficheiro"] == montar_da_mesa.REBOBINAR}
    if duracoes != {round(9 * 0.42, 2)}:
        problemas.append("duracoes do rebobinar: %s" % duracoes)
    # O 1995>2011 avanca e nao leva nenhum: a fita a avancar nao rebobina.
    t_avanca = next(float(l["inicio_s"]) - desvio for l in linhas
                    if l["tipo"] == "contador" and l["texto_ecra"].startswith("1995>2011"))
    if any(t_avanca <= t < t_avanca + 9 for t in fitas):
        problemas.append("o contador que avanca levou som de fita")
    verifica("rebobinar em cada contador que recua", not problemas,
             "; ".join(problemas)[:200] if problemas else
             "2 a recuar com som aos %s s, 1 a avancar sem" % fitas)


def teste_juncao_com_dois_contadores():
    """A juncao continua a encontrar UM contador da abertura com dois a recuar.

    O DEFEITO: o e_contador_da_abertura devolvia True para qualquer contador que recuasse,
    e e ao lado dele que as partes da fita de 1995 sao juntas. Com o contador por datas na
    abertura passaram a ser dois, o indice_unico parava a juncao inteira sem juntar nada, e
    quem corresse o render a seguir renderizava sem a fita: sem ela o nascimento do Tiago
    nao e encontrado e o Lang Lang, os foguetes e o Rei Leao saem mudos.

    Corre-se a juncao a serio, sobre duas entradas construidas a partir da Mesa dele, uma
    com um contador a recuar e outra com dois, e nas duas a copia local vai para uma pasta
    temporaria: a de data/ nunca e tocada por um teste.
    """
    import contextlib
    import io
    import json
    import tempfile
    import juntar_mesa
    caminho_estado = os.path.join(REPO, "data", "mesa_estado.json")
    if not os.path.exists(caminho_estado):
        salta("juncao com dois contadores a recuar",
              "sem o data/mesa_estado.json neste PC")
        return
    novos = [{"t": "contador", "i": "", "f": "",
              "x": "04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido",
              "d": 9, "c": 0.7, "r": "fiel"},
             {"t": "foto", "i": "f0347", "f": "", "x": "", "d": 6, "c": 0.7, "r": "fiel"},
             {"t": "foto", "i": "f0348", "f": "", "x": "", "d": 6, "c": 0.7, "r": "fiel"}]

    def recua_e_nao_chega_a_1995(c):
        return (c.get("t") == "contador"
                and linha_tempo.contador_recua(c.get("x") or "")
                and not juntar_mesa.e_contador_da_abertura(c))

    def quantos_recuam(cs):
        return len([c for c in cs if c.get("t") == "contador"
                    and linha_tempo.contador_recua(c.get("x") or "")])

    # OS DOIS CASOS CONSTROEM-SE, NAO SE ASSUMEM. Ate 22 de setembro a abertura dele tinha
    # UM contador a recuar, e o caso dos dois fazia-se acrescentando o das datas por cima do
    # estado vivo. Nesse dia a abertura nova entrou na demo_v3 e ele passou a ter os dois:
    # o teste acrescentava um terceiro e falhava com tres contadores e dois da abertura, sem
    # uma linha de codigo ter mudado. E o mesmo defeito do teste do byte, que falhava por o
    # Tiago trabalhar. Agora tira-se o que recua e nao chega a 1995 para ter o caso de um, e
    # acrescenta-se o das datas a esse para ter o caso de dois: as duas entradas sao sempre
    # as mesmas, esteja a Mesa dele como estiver.
    vivos = [dict(c) for c in juntar_mesa.versao(
        json.load(open(caminho_estado, encoding="utf-8")))["clips"]]
    um = [c for c in vivos if not recua_e_nao_chega_a_1995(c)]
    dois = list(um)
    k = next((i for i, c in enumerate(dois) if juntar_mesa.e_contador_da_abertura(c)), None)
    if k is None:
        verifica("juncao com dois contadores a recuar", False,
                 "a demo_v3 de hoje nao tem nenhum contador a chegar a 1995")
        return
    dois[k:k] = [dict(c) for c in novos]

    def junta(clips, tirar):
        est = json.load(open(caminho_estado, encoding="utf-8"))
        v = juntar_mesa.versao(est)
        pasta = tempfile.mkdtemp(prefix="teste_junc_")
        local = os.path.join(pasta, "local.json")
        v["clips"] = [dict(c) for c in clips]
        json.dump(est, open(local, "w", encoding="utf-8"), ensure_ascii=False)
        if tirar:      # a versao dele sem o que so existe na copia local
            v["clips"] = [c for c in clips if not (c.get("t") == "video"
                                                   or juntar_mesa.e_fita_kobe(c))]
        remoto = os.path.join(pasta, "remoto.json")
        json.dump(est, open(remoto, "w", encoding="utf-8"), ensure_ascii=False)
        guardado = (juntar_mesa.LOCAL, sys.argv)
        juntar_mesa.LOCAL, sys.argv = local, ["juntar_mesa.py", remoto]
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log):
                juntar_mesa.main()
        except SystemExit as e:
            return None, "%s %s" % (log.getvalue(), e)
        finally:
            juntar_mesa.LOCAL, sys.argv = guardado
        return juntar_mesa.versao(json.load(open(local, encoding="utf-8")))["clips"], log.getvalue()

    problemas = []
    for nome_caso, entrada in (("com um contador a recuar", um),
                               ("com o contador por datas", dois)):
        for tirar in (False, True):
            qual = "%s, dele %s" % (nome_caso, "sem as pecas" if tirar else "completo")
            clips, log = junta(entrada, tirar)
            if clips is None:
                problemas.append("%s: parou (%s)" % (qual, " ".join(log.split())[-90:]))
                continue
            fitas = [k for k, c in enumerate(clips) if juntar_mesa.e_fita_kobe(c)]
            videos = [c for c in clips if c.get("t") == "video"]
            abertura = [k for k, c in enumerate(clips) if juntar_mesa.e_contador_da_abertura(c)]
            if len(fitas) != 3 or len(videos) != 2:
                problemas.append("%s: %d fitas e %d videos" % (qual, len(fitas), len(videos)))
            if len(abertura) != 1:
                problemas.append("%s: %d contadores da abertura" % (qual, len(abertura)))
            elif fitas[:2] != [abertura[0] + 1, abertura[0] + 2]:
                problemas.append("%s: as duas fitas ficaram em %s e o contador em %d"
                                 % (qual, fitas[:2], abertura[0]))
            # A JUNCAO NAO MEXE NOS CONTADORES: os que saem sao os que entraram.
            if quantos_recuam(clips) != quantos_recuam(entrada):
                problemas.append("%s: %d contadores a recuar, a entrada tinha %d"
                                 % (qual, quantos_recuam(clips), quantos_recuam(entrada)))
    verifica("juncao com dois contadores a recuar", not problemas,
             "; ".join(problemas)[:220] if problemas else
             "4 combinacoes, fita sempre a seguir ao contador que acaba em 1995")


# ------------------------------------------------- as vozes do pedido, 17 de setembro
# O Tiago: "Aqui vou meter a foto do pedido e meto os audios que ja cortamos do pedido, eu
# depois decido a sequencia dos audios". A regra do CLAUDE.md "nenhuma narracao falada"
# fica de pe para o resto do filme: isto e o som do proprio momento, decisao 075.
#
# As pecas de ensaio sao feitas com o ffmpeg, com duracoes exatas, e nao as do disco: ele
# renomeia e apaga pecas, e um teste que dependesse dos nomes de hoje falhava amanha sem
# nada estar partido. A pasta das verdadeiras e so espreitada, no fim, se existir.


def _pecas_de_voz(pasta, duracoes=(2.4, 1.2, 3.1)):
    """Pecas de som com duracoes exatas, para fazerem de vozes do pedido."""
    import subprocess
    import render
    ff = render.ffmpeg()
    nomes = []
    for k, d in enumerate(duracoes):
        nome = "voz_%d.mp3" % (k + 1)
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "sine=frequency=%d:duration=%.3f:sample_rate=48000"
                        % (300 + 90 * k, d), "-b:a", "128k", os.path.join(pasta, nome)],
                       capture_output=True)
        nomes.append(nome)
    return nomes


def teste_vozes_do_pedido_no_som():
    """As vozes entram no som pela ordem dele, e a musica por baixo baixa sem perder o sitio.

    O QUE ISTO GUARDA, ponto a ponto, porque cada um falha calado:
      - comecam no inicio do clip e tocam seguidas, com VOZ_PAUSA entre cada duas;
      - todas as do mesmo clip levam o MESMO ganho, medido sobre elas juntas;
      - uma que falte e saltada com aviso e as outras continuam seguidas;
      - o leito nao e cortado nem encurtado, so marcado para baixar: e por isso que a
        retoma da musica da abertura antes da Clara continua a apontar para o mesmo ponto
        do ficheiro. Cortar e recomecar era o caminho obvio e era o que estragava isso;
      - "parada" poe o leito a zero por baixo delas, e nao a -12 dB;
      - uma musica marcada na Mesa nao corta uma voz: as vozes nao sao leito;
      - as vozes que passam das fotos seguidas levam aviso, e as que cairiam por cima dos
        foguetes ficam de fora.
    """
    import shutil
    import tempfile
    import montar_da_mesa
    import render  # noqa: F401  (mexe no sys.stdout ao ser importado; antes de qualquer redirect)
    pasta = tempfile.mkdtemp(prefix="teste_vozes_")
    nomes = _pecas_de_voz(pasta)
    duras = [montar_da_mesa.duracao_de_audio(os.path.join(pasta, n)) for n in nomes]
    guardado = montar_da_mesa.PEDACOS
    montar_da_mesa.PEDACOS = pasta
    problemas = []
    try:
        base = [
            {"t": "contador", "x": "04/10/2026>25/12/2025|hoje", "d": 9, "c": 0.7, "r": "fiel"},
            # A primeira foto e mais curta do que as vozes de proposito: elas podem
            # continuar pelas fotos SEGUIDAS, e so param no primeiro clip que nao e foto
            # nem grupo. Um limite que fosse so o clip seguinte avisava aqui sem razao.
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel", "vz": list(nomes)},
            {"t": "foto", "i": "f0348", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "contador", "x": "2025>1995|x", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0041", "d": 4, "c": 0.7, "r": "fiel"},
            {"t": "cartao", "x": "Nasce uma bebe", "d": 3.6, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0169", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        linhas, som, saida = _monta_em_pasta([dict(c) for c in base])
        if "as vozes do clip" in saida:
            problemas.append("as vozes cabem nas duas fotos e mesmo assim avisou")
        desvio = float(linhas[0]["inicio_s"])
        t_clip = float(linhas[1]["inicio_s"]) - desvio
        vozes = [r for r in som if (r.get("voz") or "").strip()]
        if len(vozes) != 3:
            problemas.append("%d vozes no som, esperava 3" % len(vozes))
        else:
            esperado, t = [], t_clip
            for d in duras:
                esperado.append(round(t, 2))
                t += d + montar_da_mesa.VOZ_PAUSA
            quando = [round(float(r["quando_s"]), 2) for r in vozes]
            if any(abs(a - b) > 0.02 for a, b in zip(quando, esperado)):
                problemas.append("vozes aos %s, esperava %s" % (quando, esperado))
            if len({r["ganho"] for r in vozes}) != 1:
                problemas.append("ganhos diferentes: %s" % [r["ganho"] for r in vozes])
            if not all(r["nota"].startswith("voz do pedido") for r in vozes):
                problemas.append("notas: %s" % [r["nota"] for r in vozes])
        # O LEITO NAO E CORTADO, SO MARCADO. E a retoma da abertura tem de continuar certa.
        leitos = [r for r in som if not (r.get("voz") or "").strip()
                  and r["ficheiro"] not in montar_da_mesa.EFEITOS]
        abertura = [r for r in leitos if r["nota"].startswith("do pedido")]
        retoma = [r for r in leitos if r["nota"].startswith("retoma")]
        if not abertura:
            problemas.append("sem a musica da abertura")
        else:
            a = abertura[0]
            janelas = render.ler_abafar(a.get("abafar"))
            fim_vozes = float(vozes[-1]["quando_s"]) + float(vozes[-1]["dura_s"]) if vozes else 0
            if len(janelas) != 1:
                problemas.append("a abertura tem %d janelas de abaixamento" % len(janelas))
            elif (abs(janelas[0][0] - t_clip) > 0.02 or abs(janelas[0][1] - fim_vozes) > 0.02
                  or abs(janelas[0][2] - 10 ** (montar_da_mesa.VOZ_ABAIXA_DB / 20.0)) > 0.001):
                problemas.append("janela da abertura: %s" % (janelas,))
            if retoma and abs(float(retoma[0]["in_s"])
                              - (float(a["in_s"]) + float(a["dura_s"]))) > 0.05:
                problemas.append("a retoma perdeu o sitio: in_s %s, a abertura ia em %.2f"
                                 % (retoma[0]["in_s"], float(a["in_s"]) + float(a["dura_s"])))
        # SEM AS VOZES, o mesmo estado da o mesmo leito inteiro e sem colunas novas.
        sem = [dict(c) for c in base]
        sem[1].pop("vz")
        _l2, som2, _s2 = _monta_em_pasta(sem, nome="t2")
        a2 = [r for r in som2 if r["nota"].startswith("do pedido")]
        if a2 and abertura and (a2[0]["dura_s"] != abertura[0]["dura_s"]
                                or a2[0]["in_s"] != abertura[0]["in_s"]):
            problemas.append("as vozes mexeram no leito: %s e %s"
                             % ((abertura[0]["in_s"], abertura[0]["dura_s"]),
                                (a2[0]["in_s"], a2[0]["dura_s"])))
        if any("voz" in r or "abafar" in r for r in som2):
            problemas.append("colunas das vozes num som sem vozes")
        # A MUSICA PARADA POR BAIXO DAS VOZES.
        parada = [dict(c) for c in base]
        parada[1] = dict(parada[1], vzm="parada")
        _l3, som3, _s3 = _monta_em_pasta(parada, nome="t3")
        j3 = render.ler_abafar(next(r for r in som3 if r["nota"].startswith("do pedido"))
                               .get("abafar"))
        if not j3 or j3[0][2] != 0.0:
            problemas.append("com «parada» o leito ficou em %s" % (j3,))
        # UMA VOZ QUE FALTA e saltada, e as outras continuam seguidas.
        falta = [dict(c) for c in base]
        falta[1] = dict(falta[1], vz=[nomes[0], "nao_existe.mp3", nomes[2]])
        _l4, som4, saida4 = _monta_em_pasta(falta, nome="t4")
        v4 = [round(float(r["quando_s"]), 2) for r in som4 if (r.get("voz") or "").strip()]
        if v4 != [round(t_clip, 2), round(t_clip + duras[0] + montar_da_mesa.VOZ_PAUSA, 2)]:
            problemas.append("com uma voz em falta: %s" % (v4,))
        if "VOZ DO PEDIDO EM FALTA" not in saida4:
            problemas.append("uma voz em falta nao avisou")
        # UMA MUSICA MARCADA NO CLIP DAS VOZES nao pode cortar nenhuma delas: uma voz nao
        # e leito. E o leito novo que ela traz tambem tem de baixar por baixo das vozes.
        marcada = [dict(c) for c in base]
        marcada[1] = dict(marcada[1], m={"f": "Tiago Celebration Song (Reggae)", "in": 0})
        _l5, som5, _s5 = _monta_em_pasta(marcada, nome="t5")
        v5 = [(r["ficheiro"], float(r["dura_s"])) for r in som5 if (r.get("voz") or "").strip()]
        if sorted(v5) != sorted((n, d) for n, d in zip(nomes, duras)):
            problemas.append("a musica marcada mexeu nas vozes: %s" % (v5,))
        if any(render.ler_abafar(r.get("abafar")) for r in som5 if (r.get("voz") or "").strip()):
            problemas.append("uma voz ficou marcada para baixar por baixo dela propria")
        nova = [r for r in som5 if r["nota"].startswith("marcada na Mesa")]
        if not nova or not render.ler_abafar(nova[0].get("abafar")):
            problemas.append("a musica marcada no clip das vozes nao baixa por baixo delas")
        # O REBOBINAR TAMBEM NAO E LEITO. Com um encadeado grande, o clip seguinte comeca
        # por cima do som da fita; uma musica marcada ai corta o leito, mas nao o efeito.
        sobre = [dict(c) for c in base]
        sobre[1] = dict(sobre[1], c=3, m={"f": "Tiago Celebration Song (Reggae)", "in": 0})
        _l8, som8, _s8 = _monta_em_pasta(sobre, nome="t8")
        fitas8 = [float(r["dura_s"]) for r in som8
                  if r["ficheiro"] == montar_da_mesa.REBOBINAR]
        if not fitas8 or any(abs(d - round(9 * 0.42, 2)) > 0.01 for d in fitas8):
            problemas.append("uma musica marcada cortou o som da fita: %s" % (fitas8,))
        # AS VOZES QUE PASSAM DAS FOTOS SEGUIDAS FICAM DE FORA, com aviso, como as que
        # caem por cima dos foguetes: com as duas fotos curtas, a ultima cairia ja em cima
        # do contador que vem a seguir. Ate 18 de setembro o limite estava calculado, o
        # comentario dizia que parava as vozes, e so saia um aviso: a voz tocava na mesma
        # por cima do que la estivesse, e o pior caso e um video, que traz o seu som.
        curto = [dict(c) for c in base]
        curto[1], curto[2] = dict(curto[1], d=3), dict(curto[2], d=3)
        l6, som6, saida6 = _monta_em_pasta(curto, nome="t6")
        d6 = float(l6[0]["inicio_s"])
        limite6 = next(float(l["inicio_s"]) - d6 for l in l6[2:]
                       if l["tipo"] not in montar_da_mesa.TIPOS_COM_VOZ)
        v6 = [(float(r["quando_s"]), float(r["quando_s"]) + float(r["dura_s"]))
              for r in som6 if (r.get("voz") or "").strip()]
        if any(b > limite6 + 0.05 for _a, b in v6):
            problemas.append("uma voz continua a tocar por cima do que vem a seguir as "
                             "fotos: %s, limite %.2f" % (v6, limite6))
        if len(v6) >= len(nomes):
            problemas.append("as tres vozes couberam em duas fotos de 3 s")
        if "fica de fora" not in saida6:
            problemas.append("a voz que nao cabe nas fotos seguidas saiu sem aviso")
        # AS QUE CAIRIAM POR CIMA DOS FOGUETES ficam de fora, com aviso. Numa foto logo
        # ANTES do cartao do nascimento: as que vem depois dele nunca la caem, porque o
        # cartao e esticado ate os foguetes acabarem.
        fogo = [dict(c) for c in base]
        fogo[3] = dict(fogo[3], vz=list(nomes), d=4)
        fogo[3]["t"], fogo[3]["i"], fogo[3]["x"] = "foto", "f0172", ""
        _l7, som7, saida7 = _monta_em_pasta(fogo, nome="t7")
        fog = [(float(r["quando_s"]), float(r["quando_s"]) + float(r["dura_s"]))
               for r in som7 if r["ficheiro"] == montar_da_mesa.VINHETA]
        v7 = [(float(r["quando_s"]), float(r["quando_s"]) + float(r["dura_s"]))
              for r in som7 if (r.get("voz") or "").strip()]
        if any(a < d and c < b for a, b in fog for c, d in v7):
            problemas.append("uma voz ficou por cima dos foguetes")
        if "foguetes" not in saida7 or "fica de fora" not in saida7:
            problemas.append("a voz por cima dos foguetes saiu sem aviso")
    finally:
        montar_da_mesa.PEDACOS = guardado
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("vozes do pedido no som, e o leito por baixo", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "3 vozes seguidas, mesmo ganho, leito inteiro e marcado para -12 dB")


def teste_vozes_no_render_com_o_leito_em_baixo():
    """O render toca as vozes inteiras e poe o leito exatamente 12 dB abaixo, sem o cortar.

    O DEFEITO QUE AS FAIXAS CURTAS TERIAM: as musicas entram e saem com um segundo de
    desvanecimento. Numa peca de 1,2 s do pedido isso apagava-a quase toda, e a palavra so
    chegava ao volume cheio quando ja estava a acabar.

    E O QUE O LEITO NAO PODE FAZER: parar e voltar a comecar. Mede-se o MESMO troco da
    MESMA musica com e sem a janela, que e a unica maneira de a queda se medir sem o
    conteudo da musica pelo meio, e tem de dar 12,0 dB certos e 0,0 dB antes e depois.

    E SEM VOZES NENHUMAS o ficheiro tem de sair igual ao byte ao de antes delas existirem.
    """
    import hashlib
    import re
    import shutil
    import subprocess
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_som_vozes_")
    ff = render.ffmpeg()
    problemas = []
    try:
        leito_f = os.path.join(pasta, "leito.wav")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "sine=frequency=220:duration=30:sample_rate=48000", leito_f],
                       capture_output=True)
        nomes = _pecas_de_voz(pasta, (2.4, 1.2))
        duras = [2.4, 1.2]
        t0, t1 = 10.0, 10.0 + 2.4 + 0.4 + 1.2
        leito = {"ficheiro": "leito.wav", "caminho": leito_f, "quando": 0.0, "in_s": 0.0,
                 "dura": 26.0, "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0,
                 "voz": False, "abafar": [(t0, t1, 10 ** (-12.0 / 20.0))]}

        def constroi(nome, entradas, fim=26.0):
            saida = os.path.join(pasta, nome)
            if not render.construir_som(ff, entradas, fim, saida, 0.0):
                problemas.append("o construir_som falhou em %s" % nome)
            return saida

        def media(caminho, ss, dur):
            r = subprocess.run([ff, "-hide_banner", "-nostats", "-ss", "%.3f" % ss,
                                "-t", "%.3f" % dur, "-i", caminho, "-af", "volumedetect",
                                "-f", "null", "-"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            achado = re.search(r"mean_volume: ([-\d.]+) dB", r.stderr or "")
            return float(achado.group(1)) if achado else 0.0

        com = constroi("com_janela.m4a", [dict(leito)])
        sem = constroi("sem_janela.m4a", [dict(leito, abafar=[])])
        for etiqueta, ss, dur, esperado in (("no meio", t0 + 0.6, 2.0, -12.0),
                                            ("antes", 5.0, 3.0, 0.0),
                                            ("depois", t1 + 1.0, 3.0, 0.0)):
            queda = media(com, ss, dur) - media(sem, ss, dur)
            if abs(queda - esperado) > 0.3:
                problemas.append("%s: %+.2f dB, esperava %+.1f" % (etiqueta, queda, esperado))
        # PARADA: o leito fica mesmo calado por baixo das vozes.
        calado = constroi("parada.m4a", [dict(leito, abafar=[(t0, t1, 0.0)])])
        if media(calado, t0 + 0.6, 2.0) > -80.0:
            problemas.append("com «parada» o leito ainda se ouve (%.1f dB)"
                             % media(calado, t0 + 0.6, 2.0))
        # A VOZ CURTA INTEIRA: com a entrada das musicas o primeiro decimo fica muito
        # abaixo do resto; com a entrada das vozes, nao.
        curta = {"ficheiro": nomes[1], "caminho": os.path.join(pasta, nomes[1]),
                 "quando": 0.0, "in_s": 0.0, "dura": duras[1], "ganho": 1.0,
                 "encontrado": "Sim", "cruza": 0.0, "voz": True, "abafar": []}
        def fatias(e):
            f = constroi("curta_%s.m4a" % ("voz" if e["voz"] else "musica"), [e], duras[1] + 0.4)
            return [media(f, k * 0.1, 0.1) for k in range(int(duras[1] / 0.1))]
        como_voz = fatias(dict(curta))
        como_musica = fatias(dict(curta, voz=False))
        meio = max(como_voz)
        if meio - como_voz[0] > 2.0:
            problemas.append("a voz curta entra %.1f dB abaixo do resto" % (meio - como_voz[0]))
        if meio - como_voz[-2] > 2.0:
            problemas.append("a voz curta sai %.1f dB abaixo do resto" % (meio - como_voz[-2]))
        if (meio - como_musica[0]) - (meio - como_voz[0]) < 6.0:
            problemas.append("a entrada de voz nao se distingue da das musicas: %.1f e %.1f"
                             % (como_voz[0], como_musica[0]))
        # O MESMO GANHO, E A DIFERENCA ENTRE AS PECAS MANTIDA. Duas pecas gravadas a
        # niveis diferentes tem de sair com a MESMA diferenca entre elas: e o que se perde
        # se cada uma levar o loudnorm por si, que e o que as musicas levam. Uma frase dita
        # baixinho no pedido tem de continuar a ouvir-se baixinho.
        alto = os.path.join(pasta, "alto.wav")
        baixo = os.path.join(pasta, "baixo.wav")
        for f, amp in ((alto, 0.5), (baixo, 0.05)):
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                            "-i", "sine=frequency=440:duration=3:sample_rate=48000",
                            "-af", "volume=%.3f" % amp, f], capture_output=True)
        niveis = []
        for f in (alto, baixo):
            e = {"ficheiro": os.path.basename(f), "caminho": f, "quando": 0.0, "in_s": 0.0,
                 "dura": 3.0, "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0,
                 "voz": True, "abafar": []}
            niveis.append(media(constroi("nivel_%s.m4a" % os.path.basename(f), [e], 3.0), 0.5, 2.0))
        if abs((niveis[0] - niveis[1]) - 20.0) > 1.5:
            problemas.append("a diferenca entre as duas pecas saiu %.1f dB e eram 20"
                             % (niveis[0] - niveis[1]))
        # SEM VOZES E SEM JANELAS, o mesmo ficheiro de sempre: a entrada escrita como era
        # antes de as vozes existirem e a escrita com as chaves novas tem de dar o mesmo.
        antiga = {"ficheiro": "leito.wav", "caminho": leito_f, "quando": 0.0, "in_s": 0.0,
                  "dura": 12.0, "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0}
        a = constroi("antiga.m4a", [dict(antiga)], 12.0)
        b = constroi("nova.m4a", [dict(antiga, voz=False, abafar=[])], 12.0)
        if hashlib.md5(open(a, "rb").read()).hexdigest() != hashlib.md5(open(b, "rb").read()).hexdigest():
            problemas.append("uma faixa sem vozes deixou de dar o mesmo ficheiro")
        if render.volume_da_faixa(dict(antiga)) != "volume=1.000":
            problemas.append("o filtro de volume sem janelas mudou: %r"
                             % render.volume_da_faixa(dict(antiga)))
        # O CRUZAMENTO NAO PEGA NAS VOZES. Uma voz que acaba onde a musica seguinte comeca
        # seria esticada 2,2 s por cima dela, e ouviam-se as duas ao mesmo tempo. Le-se um
        # som.csv de verdade, pelo som_do_ficheiro, que e por onde o render entra.
        som_csv = os.path.join(pasta, "x.som.csv")
        with open(som_csv, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ficheiro", "caminho", "quando_s", "in_s", "dura_s", "ganho",
                        "nota", "voz", "abafar"])
            w.writerow([nomes[0], os.path.join(pasta, nomes[0]), 0.0, 0.0, 2.4, 1.0,
                        "voz do pedido, no clip 1", "1", ""])
            w.writerow(["leito.wav", leito_f, 2.4, 0.0, 6.0, 1.0,
                        "marcada na Mesa, no clip das 2.4 s", "", "3.00-5.00x0.251"])
        guardadas = render.MONTAGENS
        render.MONTAGENS = pasta
        try:
            lidas = render.som_do_ficheiro("x", 20.0)
        finally:
            render.MONTAGENS = guardadas
        fala = next((e for e in lidas if e["voz"]), None)
        musica = next((e for e in lidas if not e["voz"]), None)
        if fala is None or abs(fala["dura"] - 2.4) > 0.01 or fala["cruza"] != 0.0:
            problemas.append("a voz foi esticada pelo cruzamento: %s"
                             % ((fala and (fala["dura"], fala["cruza"])),))
        if musica is None or musica["abafar"] != [(3.0, 5.0, 0.251)]:
            problemas.append("a coluna abafar nao chegou ao render: %s"
                             % (musica and musica["abafar"],))
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("vozes no render, com o leito 12 dB abaixo", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "queda de 12,0 dB certos, 0,0 antes e depois, e a voz de 1,2 s inteira")


def _monta_v3_de(estado, comparar_com):
    """Monta a demo_v3 de `estado` (um dicionario) numa pasta temporaria, como o fluxo normal.

    Devolve (None, [nomes dos ficheiros de comparar_com que sairam diferentes]). O estado e
    escrito numa copia temporaria: nem o data/mesa_estado.json nem a copia congelada sao
    escritos por um teste.
    """
    import contextlib
    import hashlib
    import io
    import json
    import shutil
    import tempfile
    import montar_da_mesa
    import render  # noqa: F401
    pasta = tempfile.mkdtemp(prefix="teste_v3_byte_")
    copia = os.path.join(pasta, "estado.json")
    json.dump(estado, open(copia, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = copia, pasta
    sys.argv = ["montar_da_mesa.py", "demo_v3", "--nome", "v3"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado

    def md5(p):
        return hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None

    diferentes = [os.path.basename(a) for a in comparar_com
                  if md5(a) != md5(os.path.join(pasta, os.path.basename(a)))]
    shutil.rmtree(pasta, ignore_errors=True)
    return None, diferentes


def teste_v3_sem_vozes_igual_ao_byte():
    """Com o estado congelado da referencia, o montar_da_mesa da o v3.csv e o v3.som.csv dela.

    O PEDIDO: o contador por datas e as vozes entram sem mexer no que ja esta. Uma coluna
    nova no som.csv, uma casa decimal a mais num ganho ou uma faixa colocada por outra
    ordem mudam a banda sonora inteira e nao ha nada que se queixe. Aqui compara-se byte a
    byte com os dois ficheiros que fizeram o ultimo render.

    A REFERENCIA E UMA COPIA CONGELADA, em data/montagens/referencia/, e nao o
    data/montagens/v3.csv. O teste comparava-se com a SAIDA DO PROPRIO montar_da_mesa.py:
    basta uma corrida normal do fluxo (juntar, montar, gerar_mesa) para a referencia passar
    a ser a saida de agora, e a partir dai o teste compara o codigo consigo proprio e passa
    para sempre. Sao trinta quilobytes de texto, nao e media, e e o que impede isto de
    deslizar.

    E O ESTADO DE ONDE SE MONTA TAMBEM E CONGELADO, desde 18 de setembro. O teste montava do
    data/mesa_estado.json vivo, e esse muda sempre que o Tiago mexe na Mesa e o Claude o le:
    na manha de 18 de setembro a demo_v3 dele ja nao era a que fez a referencia, e o teste
    falhava sem nenhuma linha de codigo ter mudado. Um teste que falha por o Tiago trabalhar
    deixa de dizer alguma coisa sobre o codigo. A copia, mesa_estado_v3.json, e a do estado
    que fez a referencia (rev 242), so com a versao demo_v3 e os pontos de foco, que e tudo o
    que o montar_da_mesa.py le; e com ela o montar de hoje da a referencia ao byte.

    E CONGELAR A REFERENCIA E UM ATO DELIBERADO, com --congelar-referencia. O ramo de
    arranque copiava-a sozinho DO PROPRIO v3.csv sempre que a pasta faltasse, e isso e o
    mesmo defeito por outra porta: quem mexesse no montar, corresse o fluxo normal e depois
    perdesse a pasta (ou trabalhasse noutra maquina, onde ela nunca foi commitada)
    congelava a saida ja alterada e passava para sempre, com uma linha de aviso perdida no
    meio de cento e tal. Congela os tres juntos, o estado e as duas saidas, porque um sem os
    outros volta a comparar coisas de dias diferentes.

    E A FALTA DOS FICHEIROS DE TRABALHO DIZ-SE, com salta(). Era um `return` calado, e como
    o data/mesa_estado.json e a montagem v3 nao estao no git, num clone novo, que e o modo
    de trabalho que o CLAUDE.md descreve, a suite imprimia o numero do costume e esta
    garantia nunca corria nem se queixava. E o desaparecimento silencioso que o salta() veio
    resolver.

    A copia do estado vai para uma pasta temporaria e e de la que se le: nem o
    data/mesa_estado.json nem a copia congelada sao escritos por um teste.
    """
    import hashlib
    import json
    import shutil
    import tempfile
    caminho_estado = os.path.join(REPO, "data", "mesa_estado.json")
    atuais = [os.path.join(REPO, "data", "montagens", n) for n in ("v3.csv", "v3.som.csv")]
    referencia = os.path.join(REPO, "data", "montagens", "referencia")
    alvos = [os.path.join(referencia, os.path.basename(a)) for a in atuais]
    congelado = os.path.join(referencia, "mesa_estado_v3.json")
    if not all(os.path.exists(a) for a in alvos + [congelado]):
        if not os.path.exists(caminho_estado) or not all(os.path.exists(a) for a in atuais):
            salta("v3 sem vozes igual ao byte",
                  "sem a referencia congelada e sem o data/mesa_estado.json ou a montagem v3 "
                  "neste PC para a congelar")
            return
        if "--congelar-referencia" not in sys.argv:
            verifica("v3 sem vozes igual ao byte", False,
                     "falta a referencia em data/montagens/referencia (v3.csv, v3.som.csv e "
                     "mesa_estado_v3.json): congela-a de proposito com "
                     "py -3.11 scripts/testes.py --congelar-referencia")
            return
        vivo = json.load(open(caminho_estado, encoding="utf-8"))
        v_vivo = [x for x in vivo.get("versoes", []) if x.get("id") == "demo_v3"]
        if not v_vivo:
            verifica("v3 sem vozes igual ao byte", False, "sem a demo_v3 no data/mesa_estado.json")
            return
        estado_a_congelar = {"_origem": "Copia congelada do data/mesa_estado.json que fez a v3.csv e a "
                                        "v3.som.csv desta pasta, so com a demo_v3 e os pontos de foco.",
                             "rev": vivo.get("rev"), "quando": vivo.get("quando"),
                             "focos": vivo.get("focos") or {}, "versoes": v_vivo}
        # OS TRES JUNTOS, do mesmo instante: o estado e o que o montar fez com ele. E isso
        # CONFIRMA-SE antes de copiar, montando o estado que vai ser congelado. O v3.csv em
        # disco e o do ultimo montar, e o data/mesa_estado.json muda sempre que o Tiago mexe na
        # Mesa: a 18 de setembro o v3.csv era do rev 242 e o estado ja ia no 343 (verificador).
        # Congelar os dois assim dava tres ficheiros de instantes diferentes, e o teste falhava
        # logo na corrida seguinte a mandar procurar no sitio errado.
        _pasta_c, diferentes_c = _monta_v3_de(estado_a_congelar, atuais)
        if diferentes_c:
            verifica("v3 sem vozes igual ao byte", False,
                     "nao congelei: o %s em disco nao %s do data/mesa_estado.json de agora (rev %s). "
                     "Corre primeiro o montar_da_mesa.py demo_v3 --nome v3 e congela depois"
                     % (" e o ".join(diferentes_c), "saem" if len(diferentes_c) > 1 else "sai",
                        vivo.get("rev")))
            return
        os.makedirs(referencia, exist_ok=True)
        for de, para in zip(atuais, alvos):
            shutil.copyfile(de, para)
        json.dump(estado_a_congelar, open(congelado, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  aviso  %-52s %s" % ("v3 sem vozes igual ao byte",
                                     "congelei a referencia de hoje em data/montagens/referencia"))
    est = json.load(open(congelado, encoding="utf-8"))
    v = next((x for x in est.get("versoes", []) if x.get("id") == "demo_v3"), None)
    if not v:
        verifica("v3 sem vozes igual ao byte", False, "sem a demo_v3 na copia congelada")
        return
    _pasta, diferentes = _monta_v3_de(est, alvos)
    verifica("v3 sem vozes igual ao byte", not diferentes,
             "diferente da referencia: %s" % ", ".join(diferentes) if diferentes
             else "v3.csv e v3.som.csv iguais aos da referencia, montados do estado congelado "
                  "(rev %s)" % est.get("rev"))


# ------------------------------------------------------------ colagem e pilha
# As oito primeiras sao as de sempre, e as assinaturas dependem delas. As outras doze sao de
# 17 de setembro, para a colagem de 12 e a pilha de 20: cada foto com uma cor que nenhuma
# outra, nem a moldura, nem o fundo escuro, tem.
CORES_MONTE = [(210, 40, 40), (40, 170, 60), (40, 70, 210), (220, 180, 30),
               (150, 50, 170), (30, 170, 170), (230, 110, 30), (120, 90, 60),
               (245, 160, 200), (100, 210, 100), (100, 140, 250), (250, 230, 120),
               (200, 120, 240), (120, 230, 230), (250, 190, 140), (180, 150, 110),
               (60, 120, 60), (170, 40, 100), (40, 120, 140), (140, 140, 40)]


def _monte_de_cores(tipo, aspetos, texto="", focos=None, estilo=None):
    """Uma colagem ou pilha feita de fotos de uma cor so, para se medir o que se ve."""
    import render
    imagens = [Image.new("RGB", (max(1, int(round(600 * a))), 600), CORES_MONTE[k])
               for k, a in enumerate(aspetos)]
    return render.preparar_monte(tipo, imagens, focos, texto, estilo=estilo)


def _formas_monte(n):
    return {"deitadas": [4 / 3.0] * n, "em pe": [3 / 4.0] * n,
            "misturadas": [(4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0)[k % 4] for k in range(n)]}


def _visivel(tela, cor):
    """Pixeis do ecra com exatamente esta cor."""
    return sum(c for c, v in (tela.getcolors(1 << 22) or []) if v == cor)


def teste_colagem_e_pilha_pousam_dentro_do_quadro():
    """Todas pousadas com folga antes do fim, e nada fora do ecra em nenhum fotograma.

    O PEDIDO: a Mesa escolhe a duracao e quantas fotos, e as fotos tem de estar todas
    no ecra, paradas, antes do fim, qualquer que seja a combinacao. Sem encadeados, o
    que se exige esta escrito aqui e nao lido do render:
      - desde 17 de setembro o tempo divide-se pelas fotos, vez = (duracao - 0,35) / (n + 1),
        e a ultima tem duas vezes: pousa e fica parada 2 x vez menos a entrada, que e
        min(0,32 ou 0,40; vez - 0,1). Antes eram 1,4 s fixos acima da duracao minima;
      - com a vez abaixo de 0,22 s aperta-se como antes, e a folga nunca desce abaixo de
        0,6 s enquanto couberem as entradas de 3 fotogramas com as pausas.
    O DEFEITO QUE ISTO APANHA: no ensaio a pilha dava 880 pixeis de largura a todas,
    e uma vertical com essa largura saia do ecra por cima e por baixo; e a colagem,
    a chegar 14% maior, saia pela borda. E numa revisao a folga de um clip curto
    passou a descer ate 0,4 s sem que o teste, que so olhava acima do minimo, desse
    por isso.
    Corre nos dois estilos de cada um, decisao 068: a espalhada e o leque pousam noutros
    sitios e tem de cumprir o mesmo.
    """
    import render
    problemas, casos = [], 0
    for tipo, quantas, estilo in [(t, q, e) for t, q in (("colagem", (2, 3, 4, 5)), ("pilha", (2, 3, 5, 8)))
                                  for e in render.ESTILOS_MONTE[t]]:
        for n in quantas:
            for forma, aspetos in sorted(_formas_monte(n).items()):
                texto = "Amigos" if (n + len(forma)) % 2 else ""
                pronto = _monte_de_cores(tipo, aspetos, texto, estilo=estilo)
                proposta = 3 + 1.6 * n if tipo == "colagem" else 2.6 + 0.85 * n
                for dur in (3.0, proposta, 20.0):
                    casos += 1
                    nome = "%s %s de %d %s em %.1f s" % (tipo, estilo, n, forma, dur)
                    inicios, entrada, _ = render.estado_monte(pronto, 0.0, dur)
                    folga = dur - (inicios[-1] + entrada)
                    vez = (dur - 0.35) / (n + 1)
                    if vez >= 0.22 - 1e-9:
                        exige = 2 * vez - max(0.12, min(0.32 if tipo == "colagem" else 0.40, vez - 0.1))
                        if abs(folga - exige) > 1e-6:
                            problemas.append("%s: a ultima pousada %.3f s antes do fim, a regra da %.3f s"
                                             % (nome, folga, exige))
                    elif dur >= 0.6 + n * 0.12 + (n - 1) * 0.1 - 1e-9:
                        exige = 0.6
                    else:
                        exige = 0.0
                    if folga < exige - 1e-6:
                        problemas.append("%s: todas pousadas so %.2f s antes do fim, exige-se %.1f s"
                                         % (nome, folga, exige))
                    fora = None
                    for q in range(int(round(dur * render.FPS))):
                        poses, _ = render.poses_monte(pronto, q / float(render.FPS), dur)
                        for k, x, y, tam, _alfa, pousada in poses:
                            if tipo == "pilha" and not pousada:
                                continue        # a pilha cai de cima, de proposito
                            f = pronto["fotos"][k]
                            w, h = f["tamanho"]
                            pts = render.cantos(x, y, (w / 2.0 + f["moldura"]) * tam,
                                                (h / 2.0 + f["moldura"]) * tam, f["angulo"])
                            if any(px < -0.5 or py < -0.5 or px > render.L + 0.5 or py > render.A + 0.5
                                   for px, py in pts):
                                fora = "%s: foto %d fora do ecra aos %.2f s" % (nome, k + 1, q / 25.0)
                                break
                        if fora:
                            break
                    if fora:
                        problemas.append(fora)
    verifica("colagem e pilha: pousam cedo e dentro do ecra", not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d combinacoes, todos os fotogramas" % casos)


def teste_colagem_nao_tapa_caras():
    """Na colagem nenhuma foto tapa o miolo de outra, nem o foco, nem fica sob a legenda.

    O DEFEITO: nos primeiros fotogramas de controlo com fotos reais, a disposicao
    empurrava cada foto para dentro do ecra sozinha, a segunda fila subia para cima
    da primeira, e na foto das cataratas a cara da Clara ficava tapada por inteiro.
    A faixa da legenda tapava tambem a fila de baixo. Mede-se no ultimo fotograma
    desenhado: o miolo de cada foto tem de se ver com a cor dela. Nos dois estilos.
    """
    import render
    problemas, casos = [], 0
    miolo = 0.5 - render.MONTE_PISA - 0.02
    for n, estilo in [(n, e) for n in (2, 3, 4, 5) for e in render.ESTILOS_MONTE["colagem"]]:
        for forma, aspetos in sorted(_formas_monte(n).items()):
            for texto in ("", "Amigos de sempre"):
                casos += 1
                pronto = _monte_de_cores("colagem", aspetos, texto, estilo=estilo)
                dur = 3 + 1.6 * n
                tela = render.desenhar(pronto, dur - 1.0 / render.FPS, dur)
                poses, zoom = render.poses_monte(pronto, dur - 1.0 / render.FPS, dur)
                for k, x, y, tam, _alfa, _ in poses:
                    f = pronto["fotos"][k]
                    w, h = f["tamanho"]
                    tapados = 0
                    for a in (-1, -0.5, 0, 0.5, 1):
                        for b in (-1, -0.5, 0, 0.5, 1):
                            px, py = render.cantos(x, y, a * miolo * w * tam, b * miolo * h * tam,
                                                   f["angulo"])[2]
                            if tela.getpixel((int(px), int(py))) != CORES_MONTE[k]:
                                tapados += 1
                    if tapados:
                        problemas.append("%s %d %s%s: foto %d com %d de 25 pontos do miolo tapados"
                                         % (estilo, n, forma, " com legenda" if texto else "", k + 1, tapados))
    # Um foco marcado na orla de baixo da segunda foto, que a quarta tapa quando nao ha
    # foco nenhum, fica a descoberto quando o Tiago o marca.
    aspetos = _formas_monte(4)["deitadas"]
    foco = (0.1, 0.97)
    sem = _monte_de_cores("colagem", aspetos)
    com = _monte_de_cores("colagem", aspetos, focos=[None, foco])
    dur = 3 + 1.6 * 4

    def cor_no_foco(pronto):
        tela = render.desenhar(pronto, dur - 0.04, dur)
        poses, _ = render.poses_monte(pronto, dur - 0.04, dur)
        k, x, y, tam, _a, _p = poses[1]
        f = pronto["fotos"][1]
        w, h = f["tamanho"]
        u, v = (foco[0] - 0.5) * w * tam, (foco[1] - 0.5) * h * tam
        ang = math.radians(f["angulo"])
        return tela.getpixel((int(x + u * math.cos(ang) + v * math.sin(ang)),
                              int(y - u * math.sin(ang) + v * math.cos(ang))))

    foco_ok = cor_no_foco(com) == CORES_MONTE[1]
    foco_sem = cor_no_foco(sem) == CORES_MONTE[1]
    verifica("colagem: miolo de cada foto a vista, acima da legenda", not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d colagens" % casos)
    verifica("colagem: o ponto de foco fica a descoberto", foco_ok and not foco_sem,
             "sem foco o ponto %s, com foco %s" % ("ja se via, o teste perdeu o sentido" if foco_sem
                                                   else "ficava tapado", "ve-se" if foco_ok else "continua tapado"))

    # NA ESPALHADA as fotos pousam noutros sitios, e o ponto da orla que fica tapado nao e o
    # mesmo. Procura-se, em cada forma, um ponto da orla de uma foto que as seguintes tapam
    # sem foco; marcado como foco, tem de ficar a descoberto.
    def cor_em(pronto, tela, k, ponto, t):
        poses, _ = render.poses_monte(pronto, t, dur5)
        _k, x, y, tam, _a, _p = poses[k]
        f = pronto["fotos"][k]
        w, h = f["tamanho"]
        u, v = (ponto[0] - 0.5) * w * tam, (ponto[1] - 0.5) * h * tam
        ang = math.radians(f["angulo"])
        return tela.getpixel((int(x + u * math.cos(ang) + v * math.sin(ang)),
                              int(y - u * math.sin(ang) + v * math.cos(ang))))

    orla = [(a / 20.0, b / 20.0) for a in range(1, 20) for b in range(1, 20)
            if min(a, 20 - a, b, 20 - b) == 1]
    espalhada, procuradas = [], 0
    for aspetos in (_formas_monte(4)["deitadas"], _formas_monte(5)["misturadas"], _formas_monte(3)["em pe"]):
        n = len(aspetos)
        dur5 = 3 + 1.6 * n
        t = dur5 - 0.04
        sem = _monte_de_cores("colagem", aspetos, estilo="espalhada")
        tela = render.desenhar(sem, t, dur5)
        achado = None
        for k in range(n - 1):
            for ponto in orla:
                if cor_em(sem, tela, k, ponto, t) != CORES_MONTE[k]:
                    achado = (k, ponto)
                    break
            if achado:
                break
        if not achado:
            continue
        procuradas += 1
        k, ponto = achado
        focos = [None] * n
        focos[k] = ponto
        com = _monte_de_cores("colagem", aspetos, focos=focos, estilo="espalhada")
        if cor_em(com, render.desenhar(com, t, dur5), k, ponto, t) != CORES_MONTE[k]:
            espalhada.append("%d fotos: o foco (%.2f, %.2f) da foto %d continua tapado" % (n, ponto[0], ponto[1], k + 1))
    verifica("colagem espalhada: o ponto de foco fica a descoberto", procuradas and not espalhada,
             "; ".join(espalhada) if espalhada else
             ("%d colagens com um ponto da orla tapado sem foco" % procuradas if procuradas
              else "nenhuma orla tapada sem foco, o teste perdeu o sentido"))


def teste_pilha_nada_desaparece():
    """Na pilha cada foto ve-se inteira quando pousa, e a de cima ve-se inteira no fim.

    O PEDIDO, da decisao 017: "caem umas sobre as outras, tortas, nada desaparece,
    o monte cresce". Nada desaparece no sentido do ensaio: nenhuma sai do ecra nem se
    desvanece, e nenhuma e tapada pela seguinte antes de ter pousado a vista. Numa
    pilha de oito, com os desvios do ensaio, uma foto do meio pode acabar quase toda
    tapada pelas de cima, e isso e o monte a crescer, nao um defeito.
    O DEFEITO QUE ISTO APANHA: com as entradas apertadas de mais, a seguinte comecava
    a cair antes de a anterior pousar, e havia fotos que nunca se chegavam a ver.
    Tambem a legenda, que ja tapou a fila de baixo da colagem, nao pode tapar a pilha.
    Nos dois estilos, o monte e o leque.
    """
    import render
    problemas, casos = [], 0
    # A pilha de 8 em 3 e 5 s e o caso da revisao: as entradas apertavam-se ate a
    # seguinte comecar a cair antes de a anterior parar, e havia fotos que so se viam a
    # 0-4% quando pousavam.
    for (n, dur), estilo in [(c, e) for c in ((3, 2.6 + 0.85 * 3), (8, 2.6 + 0.85 * 8), (8, 3.0), (8, 5.0))
                             for e in render.ESTILOS_MONTE["pilha"]]:
        for forma, aspetos in sorted(_formas_monte(n).items()):
            texto = "Viagens" if len(forma) % 2 else ""
            casos += 1
            pronto = _monte_de_cores("pilha", aspetos, texto, estilo=estilo)
            inicios, entrada, _ = render.estado_monte(pronto, 0.0, dur)
            # A conta da area deixa de fora dois pixeis de cada lado: a borda rodada e
            # esbatida nunca tem a cor exata, e numa vertical pequena a 90% esse anel
            # ja pesava mais de 1% e fazia falhar uma foto que estava inteira a vista.
            for k in range(n):
                tela = render.desenhar(pronto, inicios[k] + entrada, dur)
                w, h = pronto["fotos"][k]["tamanho"]
                cheia = _visivel(tela, CORES_MONTE[k]) / float((w - 4) * (h - 4))
                if cheia < 0.97:
                    problemas.append("%s %d %s%s em %.1f s: foto %d so %.0f%% a vista quando pousa"
                                     % (estilo, n, forma, " com legenda" if texto else "", dur, k + 1, 100 * cheia))
            tela = render.desenhar(pronto, dur - 1.0 / render.FPS, dur)
            _, zoom = render.poses_monte(pronto, dur - 1.0 / render.FPS, dur)
            w, h = pronto["fotos"][-1]["tamanho"]
            cheia = _visivel(tela, CORES_MONTE[n - 1]) / ((w * zoom - 4) * (h * zoom - 4))
            if cheia < 0.97:
                problemas.append("%s %d %s: a de cima so %.0f%% a vista no fim" % (estilo, n, forma, 100 * cheia))
    verifica("pilha: cada foto a vista quando pousa, a de cima no fim", not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d pilhas" % casos)


def teste_camada_do_conjunto_igual_as_fotos():
    """Na respiracao e no recuo, a camada do conjunto da o mesmo fotograma que foto a foto.

    O render compoe as fotos pousadas uma vez numa camada e escala-a, porque compor
    oito fotos rodadas por fotograma custava 600 ms. Se a camada ficasse deslocada
    meio pixel, ou com a borda escura de uma composicao em alfa direto, via-se um
    salto no instante em que a ultima foto pousa. Compara-se com o caminho foto a foto.
    """
    from PIL import ImageChops, ImageFilter
    import render

    def diferenca(a, b):
        r, g, bb = ImageChops.difference(a, b).split()
        return ImageChops.lighter(ImageChops.lighter(r, g), bb)

    piores, trocas = [], []
    for tipo, aspetos, dur, estilo in (("colagem", _formas_monte(5)["misturadas"], 11.0, "filas"),
                                       ("pilha", _formas_monte(8)["misturadas"], 9.4, "monte"),
                                       ("colagem", _formas_monte(5)["misturadas"], 11.0, "espalhada"),
                                       ("pilha", _formas_monte(8)["misturadas"], 9.4, "leque")):
        pronto = _monte_de_cores(tipo, aspetos, "2015", estilo=estilo)
        tipo = estilo
        for t in (dur * 0.8, dur - 0.04):
            camada = render.desenhar_monte(pronto, t, dur)
            fotos = render.desenhar_monte(pronto, t, dur, por_foto=True)
            hist = diferenca(camada, fotos).histogram()
            total = float(sum(hist))
            media = sum(v * c for v, c in enumerate(hist)) / total
            grandes = sum(hist[41:]) / total
            piores.append((tipo, media, grandes))
        # O FOTOGRAMA DA TROCA. Com a camada feita 3% maior, nesse fotograma as bordas
        # das molduras saltavam ate 51 de 255 contra o anterior, com a media do ecra
        # inteiro abaixo de 1: a media escondia-o. Mede-se o maximo, e so junto as
        # bordas, onde o salto se ve.
        # E SEPARA-SE O SALTO DA CAMADA DO MOVIMENTO. O fotograma anterior a troca e sempre
        # o fim da chegada da ultima foto, que ainda anda uma fracao de pixel: com a agenda de
        # 17 de setembro a pilha de 8 em 9,4 s pousa 0,029 s depois dele em vez de 0,02, e so
        # esse resto da chegada ja muda as bordas 18 de 255 desenhado foto a foto, sem camada
        # nenhuma. Por isso mede-se o fotograma da troca contra o mesmo instante foto a foto,
        # que e o salto que a camada acrescenta, e o salto contra o anterior so pode passar o
        # movimento foto a foto por uma margem pequena.
        inicios, entrada, _ = render.estado_monte(pronto, 0.0, dur)
        q = int(math.ceil((inicios[-1] + entrada) * render.FPS - 1e-9))
        ultimo = int(round(dur * render.FPS)) - 1
        # Ate ao ultimo fotograma, nao mais: um conjunto que nunca se mexe prendia aqui
        # a suite inteira em vez de falhar.
        while q < ultimo and render.estado_monte(pronto, q / float(render.FPS), dur)[2] == 1.0:
            q += 1
        if render.estado_monte(pronto, q / float(render.FPS), dur)[2] == 1.0:
            trocas.append((tipo, 255))
            continue
        anterior = render.desenhar_monte(pronto, (q - 1) / float(render.FPS), dur)
        troca = render.desenhar_monte(pronto, q / float(render.FPS), dur)
        troca_foto = render.desenhar_monte(pronto, q / float(render.FPS), dur, por_foto=True)
        bordas = anterior.convert("L").filter(ImageFilter.FIND_EDGES).point(
            lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(5))

        def maximo(a, b):
            hist = diferenca(a, b).histogram(mask=bordas)
            return max([v for v, c in enumerate(hist) if c] or [0])
        trocas.append((tipo, maximo(troca, troca_foto), maximo(anterior, troca), maximo(anterior, troca_foto)))
    certo = all(m < 0.8 and g < 0.002 for _, m, g in piores)
    verifica("colagem e pilha: camada do conjunto igual a foto a foto", certo,
             "; ".join("%s media %.2f, %.2f%% com diferenca > 40" % (t, m, 100 * g) for t, m, g in piores))
    verifica("colagem e pilha: as bordas nao saltam quando passa para a camada",
             all(camada <= 12 and salto <= movimento + 6 for _, camada, salto, movimento in trocas),
             "; ".join("%s: a camada muda as bordas %d de 255, o salto contra o anterior %d com %d de movimento"
                       % (t, camada, salto, movimento) for t, camada, salto, movimento in trocas))


def teste_borda_da_colagem_nao_pisca():
    """A moldura da colagem e da pilha esbate na borda em sub-pixel, sem degrau.

    A regra do CLAUDE.md para qualquer sprite numa composicao de sub-pixel: vem de
    com_margem(), com alfa zero. Sem essa margem a Pillow amostra fora da imagem, a
    coluna de fora acende e apaga, e na respiracao lenta do fim le-se como tremor.
    """
    import render
    sp = render.sprite_monte(Image.new("RGB", (400, 300), (255, 255, 255)), 400, 300, 0, 0)
    alfa = sp.split()[3]
    w, h, m = sp.width, sp.height, render.MARGEM
    anel = max(alfa.crop(r).getextrema()[1] for r in
               ((0, 0, w, m), (0, h - m, w, h), (0, 0, m, h), (w - m, 0, w, h)))
    pior = 0.0
    for k in range(9):
        fx = k / 8.0
        tela = Image.new("RGB", (900, 900), (0, 0, 0))
        render.compor(tela, sp, 400 + fx, 450, 1.0)
        pior = max(pior, abs(tela.getpixel((200, 450))[0] - 255 * (1 - fx)))
    rodado = render.sprite_monte(Image.new("RGB", (400, 300), (255, 255, 255)), 400, 300, 8, -3.5)
    alfa_r = rodado.split()[3]
    anel_r = max(alfa_r.crop(r).getextrema()[1] for r in
                 ((0, 0, rodado.width, m), (0, rodado.height - m, rodado.width, rodado.height),
                  (0, 0, m, rodado.height), (rodado.width - m, 0, rodado.width, rodado.height)))
    verifica("colagem e pilha: borda com margem esbate em sub-pixel",
             anel == 0 and anel_r == 0 and pior <= 3,
             "margem com alfa %d e %d, erro maximo %.0f de 255" % (anel, anel_r, pior))


def teste_colagem_e_pilha_deterministicas():
    """O mesmo fotograma sai igual, pixel a pixel, qualquer que seja a ordem em que se pede.

    O render guarda a camada das fotos ja pousadas para nao as compor em cada
    fotograma. Se essa camada ficasse com uma foto a mais ou a menos, o fotograma
    dependia do que tinha sido desenhado antes, e no render as transicoes pedem o
    mesmo clip duas vezes por fotograma.
    """
    import render
    diferentes = []
    for tipo, aspetos, dur, estilo in [(t, a, d, e) for t, a, d in (
            ("colagem", [4 / 3.0, 3 / 4.0, 4 / 3.0, 16 / 9.0], 6.0),
            ("pilha", [4 / 3.0, 3 / 4.0, 4 / 3.0, 2 / 3.0, 4 / 3.0], 6.0))
            for e in render.ESTILOS_MONTE[t]]:
        a = _monte_de_cores(tipo, aspetos, "2015", estilo=estilo)
        b = _monte_de_cores(tipo, aspetos, "2015", estilo=estilo)
        tipo = estilo
        tempos = [0.0, 0.5, 0.9, 1.7, 2.6, 3.3, 4.4, 5.2, dur - 0.04]
        ida = [render.desenhar(a, t, dur).tobytes() for t in tempos]
        volta = [render.desenhar(b, t, dur).tobytes() for t in reversed(tempos)][::-1]
        salto = [render.desenhar(b, t, dur).tobytes() for t in tempos[::2]]
        mesmos_lugares = [f["centro"] for f in a["fotos"]] == [f["centro"] for f in b["fotos"]]
        if ida != volta or ida[::2] != salto or not mesmos_lugares:
            diferentes.append(tipo)
    verifica("colagem e pilha: fotogramas iguais em qualquer ordem", not diferentes,
             ("diferem: " + ", ".join(diferentes)) if diferentes else "4 estilos, 9 instantes, tres ordens")


def teste_mesa_escreve_colagem_e_pilha():
    """A colagem e a pilha da Mesa chegam a montagem com as fotos pelo id, e as incompletas saltam.

    O PEDIDO: a Mesa escreve {t:"colagem"|"pilha", fotos:[ids], x, d, c, r, orig}. A
    linha da montagem tem de levar o tipo igual ao t, as fotos por id separadas por
    "|" e o foco de cada uma, senao o render recebe um clip que nao conhece e sai um
    cartao preto no lugar da colagem, sem aviso nenhum.

    E OS LIMITES DE 17 DE SETEMBRO, escritos aqui: a colagem de 12 e a pilha de 20 entram, a
    de 13 e a de 21 saltam com o aviso que diz os limites. O lado a lado de 6 entra com o 6g,
    o de 5 salta, e uma disposicao de outro numero de fotos fica a do numero certo, com aviso.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # antes do redirect: o render mexe no sys.stdout ao ser importado
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    oito = ["f0331", "f0327", "f0308", "f0334", "f0315", "f0336", "f0316", "f0328"]
    if not all(i in inv for i in set(tres + oito + ["f0012"])):
        verifica("Mesa escreve colagem e pilha", False, "fotos do ensaio fora do inventario")
        return
    pasta = tempfile.mkdtemp(prefix="teste_monte_")
    estado = {"focos": {"f0334": [0.3, 0.2]}, "versoes": [{"id": "teste_monte", "nome": "teste monte", "clips": [
        {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "colagem", "i": "", "f": "", "fotos": tres, "x": "Amigos", "d": 7.8, "c": 0.7,
         "r": "fiel", "orig": []},
        {"t": "pilha", "i": "", "f": "", "fotos": oito, "x": "", "d": 9.4, "c": 0.6, "r": "fiel", "orig": []},
        {"t": "colagem", "fotos": ["f0331", "f9999"], "d": 6, "c": 0.7, "r": "fiel"},
        {"t": "pilha", "fotos": ["f0331"], "d": 5, "c": 0.7, "r": "fiel"},
        {"t": "colagem", "fotos": (oito * 2)[:13], "d": 6, "c": 0.7, "r": "fiel"},
        {"t": "colagem", "fotos": (oito * 2)[:12], "d": 12, "c": 0.7, "r": "fiel"},
        {"t": "pilha", "fotos": (oito * 3)[:20], "d": 20, "c": 0.7, "r": "fiel"},
        {"t": "pilha", "fotos": (oito * 3)[:21], "d": 20, "c": 0.7, "r": "fiel"},
        {"t": "lado", "fotos": oito[:6], "d": 11, "c": 0.7, "r": "fiel"},
        {"t": "lado", "fotos": oito[:5], "d": 9, "c": 0.7, "r": "fiel"},
        {"t": "lado", "fotos": oito[:3], "lay": "2v", "d": 6, "c": 0.7, "r": "fiel"}]}]}
    caminho = os.path.join(pasta, "estado.json")
    json.dump(estado, open(caminho, "w", encoding="utf-8"), ensure_ascii=False)
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    sys.argv = ["montar_da_mesa.py", "teste_monte", "--nome", "teste_monte"]
    saida = io.StringIO()
    try:
        with contextlib.redirect_stdout(saida):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
    linhas = list(csv.DictReader(open(os.path.join(pasta, "teste_monte.csv"), encoding="utf-8-sig")))
    grupos = [l for l in linhas if l["tipo"] in ("colagem", "pilha")]
    texto = saida.getvalue()
    saltadas = texto.count("saltada")
    certo = (len(grupos) == 4 and len([l for l in linhas if l["tipo"] != "lado"]) == 5 and saltadas == 4
             and grupos[0]["tipo"] == "colagem" and grupos[0]["id"].split("|") == tres
             and len(grupos[0]["ficheiro"].split("|")) == 3 and grupos[0]["texto_ecra"] == "Amigos"
             and grupos[0]["fonte_imagem"].split("|") == ["", "0.3000,0.2000", ""]
             and grupos[1]["tipo"] == "pilha" and grupos[1]["id"].split("|") == oito
             and abs(float(grupos[1]["duracao_s"]) - 9.4) < 1e-6
             and all(g["tipo"] in render.LIMITES_MONTE for g in grupos))
    verifica("Mesa escreve colagem e pilha com as fotos por id", certo,
             "%d linhas, %s, %d saltadas" % (len(linhas), [g["tipo"] for g in grupos], saltadas))
    lados = [l for l in linhas if l["tipo"] == "lado"]
    certo = (len(grupos) == 4 and grupos[2]["tipo"] == "colagem" and len(grupos[2]["id"].split("|")) == 12
             and grupos[3]["tipo"] == "pilha" and len(grupos[3]["id"].split("|")) == 20
             and "colagem saltada, pede 2 a 12 fotos e tem 13" in texto
             and "pilha saltada, pede 2 a 20 fotos e tem 21" in texto
             and [(l["tratamento"], len(l["id"].split("|"))) for l in lados] == [("6g", 6), ("3v", 3)]
             and "lado a lado saltado, tem 5 fotos" in texto
             and "lado a lado com a disposicao '2v' para 3 fotos, fica 3v" in texto)
    verifica("Mesa: colagem ate 12, pilha ate 20 e lado a lado de 6, e salta o que passa com aviso", certo,
             "grupos %s, lados %s, avisos %s" % ([(g["tipo"], len(g["id"].split("|"))) for g in grupos],
                                                [(l["tratamento"], len(l["id"].split("|"))) for l in lados],
                                                [l.strip() for l in texto.splitlines() if "salta" in l or "disposicao" in l]))


def teste_colagem_enche_o_ecra():
    """Numa colagem as fotos ocupam uma parte do ecra que se le a 15 metros, e nenhuma fica minuscula.

    OS DEFEITOS: a disposicao limitava as linhas a 3 fotos e escolhia a particao pela area
    antes de afastar as fotos umas das outras. Quatro ou cinco verticais iam para duas
    filas, as filas empurravam-se, o conjunto encolhia para caber e as fotos acabavam
    com 18 a 21% do ecra, com legenda.
    Depois, ja com a area certa, a regra contra a foto minuscula era uma razao entre a
    mais pequena e a maior, e uma razao nao sabe de tamanhos: numa colagem de 16:9, 2:3,
    2:3, 16:9 e 3:4 com legenda preferia uma fila so com todas mais pequenas, e as fotos
    passavam de 43% para 26% do ecra. Sem regra nenhuma, uma 16:9 sozinha numa fila
    deixava tres verticais com menos de 4% do ecra cada uma.
    """
    import render
    capa = render.faixa_texto("Amigos")
    livre = capa[1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * render.A
    ecra = render.L * render.A / (1 + render.COLAGEM_RESPIRA) ** 2
    H, V, W, T = 4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0
    nomes = {H: "4:3", V: "3:4", W: "16:9", T: "2:3"}
    # (aspetos, legenda, area minima de todas, area minima da mais pequena), fracoes do ecra
    exigencias = [([a] * n, legenda, 0.35, 0.0)
                  for a in (V, T) for n in (4, 5) for legenda in (None, livre)]
    exigencias += [(aspetos, livre, 0.33, 0.0)
                   for aspetos in ([W, T, T, W, V], [W, V, T, W, T], [T, W, V, T, W], [V, W, T, W, V],
                                   [H, V, W, T], [H, V, W, T, H])]
    exigencias += [(aspetos, None, 0.35, 0.05) for aspetos in ([W, V, V, T], [T, T, T, W])]
    # A 16:9, 3:4, 3:4, 2:3 fica em duas filas de duas: 1+3 dava a mais pequena com 3,7%.
    exigencias += [([W, V, V, T], None, 0.35, 0.065)]
    # E sem abdicar de area a troco de quase nada: o maximo estrito da mais pequena dava
    # 44,9%, 53,6% e 33,9% nestas tres, para a mais pequena crescer 0,5 a 3%.
    exigencias += [([T, T, T, H, H], None, 0.47, 0.0), ([H, H, V, T, W], None, 0.56, 0.0),
                   ([T, V, T, H, H], livre, 0.355, 0.0)]
    problemas = []
    for aspetos, legenda, area_min, menor_min in exigencias:
        areas = [f[2] * f[3] / ecra for f in render.colagem_disposicao(aspetos, None, legenda)]
        if sum(areas) < area_min or min(areas) < menor_min:
            problemas.append("%s%s: fotos com %.0f%% do ecra, a mais pequena com %.1f%%"
                             % (",".join(nomes[a] for a in aspetos), " com legenda" if legenda else "",
                                100 * sum(areas), 100 * min(areas)))
    verifica("colagem: enche o ecra e nenhuma foto fica minuscula", not problemas,
             "; ".join(problemas[:3]) if problemas else "%d colagens, verticais e misturadas" % len(exigencias))


def teste_monte_espera_o_encadeado():
    """A agenda da colagem e da pilha divide o tempo pelas fotos: a mesma vez a cada uma, a ultima com duas.

    O PEDIDO, do Tiago a 17 de setembro: "nestes casos das colagens e da pilha permite que ao
    aumentar a duracao o que faca seja dividir o tempo pelo numero de fotos selecionadas", e
    "Pode ser com a ultima a ficar o dobro, e provavelmente tambem a primeira tem de descontar
    um bocadinho, caso contrario a primeira nunca tem o efeito". A agenda de antes espalhava
    as entradas so ate 1,6 s na colagem e 1,3 s na pilha, e o resto ia para o fim com todas
    pousadas: numa pilha de 8 em 19 s aumentar a duracao so alongava o fim.

    OS NUMEROS ESTAO ESCRITOS AQUI, e nao lidos do render, porque a Mesa faz as mesmas contas:
      vez = (duracao - max(0,35; entra) - sai) / (n + 1)
      a foto k comeca a entrar em max(0,35; entra) + k x vez
      a entrada dura min(0,32 na colagem ou 0,40 na pilha; vez - 0,1), nunca menos de 0,12
    e a duracao minima que a Mesa avisa continua a ser
      max(0,35; entra) + n x entrada + (n - 1) x 0,1 + 1,4 + sai.
    Mede-se tambem nos fotogramas, pelo poses_monte() de clips preparados: cada foto aparece
    a sua vez depois da anterior a menos de um fotograma, a ultima fica duas vezes ate ao
    encadeado de saida, nenhuma aparece antes de o encadeado de entrada acabar, e o conjunto
    so respira ou recua depois de a ultima pousar. Com mais duracao cada vez cresce o mesmo, e
    sem teto: uma pilha de 8 em 60 s da 6,5 s a cada foto.
    ABAIXO DE 0,22 S POR FOTO aperta-se como antes: os numeros sao os que o render de 16 de
    setembro dava, escritos a letra, e nenhuma foto e tapada antes de parar.
    """
    import render
    problemas, casos = [], 0
    for tipo, quantas in (("colagem", (2, 3, 5, 12)), ("pilha", (2, 5, 8, 20))):
        cheia = 0.32 if tipo == "colagem" else 0.40
        for n in quantas:
            for entra, sai in ((0.0, 0.0), (0.7, 0.7), (0.7, 1.2), (1.0, 0.3), (0.0, 2.5)):
                minimo = render.duracao_minima_monte(tipo, n, entra, sai)
                conta = max(0.35, entra) + n * cheia + (n - 1) * 0.1 + 1.4 + sai
                if abs(minimo - conta) > 1e-9:
                    problemas.append("%s de %d com encadeados %.1f/%.1f: duracao minima %.3f, a conta da Mesa da %.3f"
                                     % (tipo, n, entra, sai, minimo, conta))
                for dur in (minimo - 1.0, minimo, 3 + 1.6 * n, 19.0, 60.0):
                    vez = (dur - max(0.35, entra) - sai) / (n + 1)
                    if vez < 0.22:
                        continue
                    casos += 1
                    nome = "%s de %d em %.2f s com encadeados %.1f/%.1f" % (tipo, n, dur, entra, sai)
                    inicios, entrada = render.agenda_monte(n, dur, cheia, cross_entra=entra, cross_sai=sai)
                    esperados = [max(0.35, entra) + k * vez for k in range(n)]
                    entrada_certa = max(0.12, min(cheia, vez - 0.1))
                    if (len(inicios) != n or max(abs(a - b) for a, b in zip(inicios, esperados)) > 1e-9
                            or abs(entrada - entrada_certa) > 1e-9):
                        problemas.append("%s: inicios %s e entrada %.3f, a regra da %s e %.3f"
                                         % (nome, [round(i, 3) for i in inicios], entrada,
                                            [round(i, 3) for i in esperados], entrada_certa))
                        continue
                    if abs(render.vez_do_monte(n, dur, entra, sai) - vez) > 1e-9:
                        problemas.append("%s: vez_do_monte da %.4f e nao %.4f" % (nome, render.vez_do_monte(n, dur, entra, sai), vez))
                    # e com mais 1 s cada vez cresce 1/(n + 1) s, todas o mesmo
                    mais, _e = render.agenda_monte(n, dur + 1.0, cheia, cross_entra=entra, cross_sai=sai)
                    passos = [b - a for a, b in zip(inicios, inicios[1:])]
                    passos_mais = [b - a for a, b in zip(mais, mais[1:])]
                    if any(abs(pm - p - 1.0 / (n + 1)) > 1e-9 for p, pm in zip(passos, passos_mais)):
                        problemas.append("%s: com mais 1 s os passos passam de %.3f para %s"
                                         % (nome, passos[0] if passos else 0, [round(p, 3) for p in passos_mais]))
    # NOS FOTOGRAMAS: clips preparados com os encadeados, e o que o poses_monte() poe no ecra.
    fps = float(render.FPS)
    for tipo, n, dur, entra, sai in (("colagem", 5, 11.0, 0.7, 1.2), ("pilha", 8, 19.0, 0.7, 0.7),
                                     ("pilha", 3, 9.4, 0.0, 2.5), ("colagem", 12, 8.0, 1.0, 0.3),
                                     ("pilha", 20, 12.0, 0.7, 0.7)):
        casos += 1
        nome = "%s de %d em %.1f s com %.1f/%.1f" % (tipo, n, dur, entra, sai)
        imagens = [Image.new("RGB", (40, 30), CORES_MONTE[k]) for k in range(n)]
        pronto = render.preparar_monte(tipo, imagens, None, "", entra, sai)
        vez = (dur - max(0.35, entra) - sai) / (n + 1)
        aparece = {}
        pousou = zoom_antes = None
        for q in range(int(round(dur * fps))):
            poses, zoom = render.poses_monte(pronto, q / fps, dur)
            for k, _x, _y, _t, _a, pousada in poses:
                aparece.setdefault(k, q)
            if len(poses) == n and all(p[5] for p in poses) and pousou is None:
                pousou = q
            if zoom != 1.0 and zoom_antes is None:
                zoom_antes = q
        if sorted(aparece) != list(range(n)):
            problemas.append("%s: so aparecem as fotos %s" % (nome, sorted(aparece)))
            continue
        passos = [(aparece[k + 1] - aparece[k]) / fps for k in range(n - 1)]
        ultima = (dur - sai) - aparece[n - 1] / fps
        if max(abs(p - vez) for p in passos) > 1.0 / fps + 1e-9:
            problemas.append("%s: as fotos aparecem de %s em %s s, a vez e %.3f" % (
                nome, min(passos), max(passos), vez))
        if abs(ultima - 2 * vez) > 1.0 / fps + 1e-9:
            problemas.append("%s: a ultima fica %.3f s ate ao encadeado de saida, o dobro da vez e %.3f" % (nome, ultima, 2 * vez))
        if aparece[0] / fps < max(0.35, entra) - 1e-9 or aparece[0] / fps > max(0.35, entra) + 1.0 / fps + 1e-9:
            problemas.append("%s: a primeira aparece aos %.2f s, com o encadeado de entrada de %.1f s"
                             % (nome, aparece[0] / fps, entra))
        if pousou is None or zoom_antes is None or zoom_antes < pousou:
            problemas.append("%s: o conjunto mexe-se aos %s e a ultima pousa aos %s" % (nome, zoom_antes, pousou))
    # O APERTO, a letra do render de 16 de setembro: (tipo, n, duracao, entra, sai, primeira, passo, entrada)
    aperto = [("colagem", 5, 2.5, 0.7, 0.7, 0.2, 0.22, 0.12),
              ("pilha", 8, 2.0, 0.7, 0.7, 0.0, 0.185542169, 0.101204819),
              ("pilha", 20, 5.0, 0.7, 0.7, 0.0, 0.22, 0.12),
              ("colagem", 2, 1.0, 0.0, 0.0, 0.06, 0.22, 0.12),
              ("pilha", 5, 1.0, 1.0, 0.3, 0.0, 0.088, 0.048),
              ("colagem", 12, 3.0, 0.7, 2.5, 0.0, 0.207874016, 0.113385827),
              ("colagem", 3, 1.5, 0.7, 1.2, 0.0, 0.22, 0.12)]
    for tipo, n, dur, entra, sai, primeira, passo, entrada_antes in aperto:
        casos += 1
        inicios, entrada = render.agenda_monte(n, dur, 0.32 if tipo == "colagem" else 0.40,
                                               cross_entra=entra, cross_sai=sai)
        esperados = [primeira + k * passo for k in range(n)]
        if (max(abs(a - b) for a, b in zip(inicios, esperados)) > 1e-6 or abs(entrada - entrada_antes) > 1e-6
                or inicios[-1] + entrada > dur + 1e-9
                or any(b - a < entrada - 1e-9 for a, b in zip(inicios, inicios[1:]))):
            problemas.append("%s de %d em %.1f s com %.1f/%.1f, apertado: inicios de %.3f em %.3f e entrada %.3f; "
                             "antes era de %.3f em %.3f e %.3f" % (tipo, n, dur, entra, sai, inicios[0],
                                                                   inicios[1] - inicios[0], entrada, primeira,
                                                                   passo, entrada_antes))
    verifica("colagem e pilha: o tempo dividido pelas fotos, a ultima com o dobro, depois do encadeado", not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d agendas, 5 clips medidos fotograma a fotograma, 7 apertos como antes" % casos)


def teste_limites_dos_grupos_iguais():
    """Colagem de 2 a 12, pilha de 2 a 20 e as disposicoes do lado a lado, iguais no render, no montar_da_mesa e na Mesa.

    O PEDIDO, do Tiago a 17 de setembro: "aumenta a quantidade das fotos possiveis nas
    diferentes opcoes no tratamento, em especial a colagem e a pilha". Os limites vivem em
    tres sitios: a Mesa nao deixa juntar mais, o montar_da_mesa.py salta o clip com aviso e o
    render recusa-o. Um que mudasse sozinho dava na Mesa uma colagem de 12 que o video deitava
    fora. Os numeros estao escritos aqui, e a Mesa le-se como texto: o GRUPOS e o LADO_N do
    scripts/editor_base.html, que e de onde a pagina publicada e montada.
    """
    import re
    import montar_da_mesa
    import render
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    grupos = {}
    m = re.search(r"var GRUPOS\s*=\s*\{(.*?)\};", html, re.S)
    if m:
        for tipo, minimo, maximo in re.findall(r"(\w+)\s*:\s*\{\s*min\s*:\s*(\d+)\s*,\s*max\s*:\s*(\d+)", m.group(1)):
            grupos[tipo] = (int(minimo), int(maximo))
    escritos = {"colagem": (2, 12), "pilha": (2, 20)}
    na_mesa = {t: grupos.get(t) for t in escritos}
    verifica("colagem ate 12 e pilha ate 20, iguais no render, no montar_da_mesa e na Mesa",
             render.LIMITES_MONTE == escritos and montar_da_mesa.LIMITES_MONTE == escritos and na_mesa == escritos,
             "render %s, montar_da_mesa %s, Mesa %s" % (render.LIMITES_MONTE, montar_da_mesa.LIMITES_MONTE, na_mesa))
    lado_n = {}
    m = re.search(r"var LADO_N\s*=\s*\{(.*?)\};", html, re.S)
    if m:
        lado_n = {k: int(v) for k, v in re.findall(r'"(\w+)"\s*:\s*(\d+)', m.group(1))}
    lados = {"2v": 2, "3v": 3, "3s": 3, "4q": 4, "6g": 6}
    omissao = montar_da_mesa.LADO_OMISSAO
    certo = (render.LAYOUTS_LADO == lados and montar_da_mesa.LAYOUTS_LADO == lados and lado_n == lados
             and sorted(omissao) == [2, 3, 4, 6] and all(lados[lay] == n for n, lay in omissao.items())
             and grupos.get("lado") == (2, 6))
    verifica("lado a lado: as disposicoes, o 6g incluido, iguais no render, no montar_da_mesa e na Mesa", certo,
             "render %s, montar_da_mesa %s e %s, Mesa %s e GRUPOS.lado %s"
             % (render.LAYOUTS_LADO, montar_da_mesa.LAYOUTS_LADO, omissao, lado_n, grupos.get("lado")))


def teste_lado_6g():
    """O lado a lado de 6 sao duas filas de tres: as celulas certas, entram sem se atravessar, e ficam no sitio.

    O PEDIDO, do Tiago a 17 de setembro, mais fotos em cada tratamento, e no lado a lado
    passou a haver o 6g. Os numeros estao escritos aqui: as colunas do 3v (634, 636 e 634 de
    largura a 1920) e as filas do 4q (536 de altura a 1080), com a linha preta de 8 entre
    todas, e a cobrir o ecra de ponta a ponta. A entrada mede-se fotograma a fotograma com a
    conta do desenhar(): nenhuma celula ja no ecra pisa outra, enquanto entram e depois. No
    fim cada celula tem a cor da sua foto. E pelo preparar() o 6g com 6 fotos chega ao desenho
    e com 5 nao, e a legenda de baixo troca seis vezes.
    """
    import tempfile
    import render
    problemas = []
    L, A = render.L, render.A
    esperadas = [(0, 0, 634, 536), (642, 0, 636, 536), (1286, 0, 634, 536),
                 (0, 544, 634, 536), (642, 544, 636, 536), (1286, 544, 634, 536)]
    escala = [(round(x * L / 1920.0), round(y * A / 1080.0), round(w * L / 1920.0), round(h * A / 1080.0))
              for x, y, w, h in esperadas]
    celulas = render.lado_celulas("6g")
    rects = [r for r, _vem in celulas]
    if (L, A) == (1920, 1080) and rects != esperadas:
        problemas.append("celulas %s, esperadas %s" % (rects, esperadas))
    elif (L, A) != (1920, 1080) and any(max(abs(a - b) for a, b in zip(r, e)) > 2 for r, e in zip(rects, escala)):
        problemas.append("celulas %s a %dx%d" % (rects, L, A))
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                problemas.append("as celulas %d e %d pisam-se" % (i + 1, j + 1))
    cores = CORES_MONTE[:6]
    pronto_celulas = []
    for k, ((x, y, w, h), vem) in enumerate(celulas):
        sw, sh = int(math.ceil(w * (1 + render.LADO_ZOOM))), int(math.ceil(h * (1 + render.LADO_ZOOM)))
        pronto_celulas.append({"rect": (x, y, w, h), "vem": vem, "respira": True,
                               "sprite": render.com_margem(Image.new("RGB", (sw, sh), cores[k]), "preto"),
                               "atraso": render.LADO_ATRASO + k * render.LADO_INTERVALO})
    pronto = {"tipo": "lado", "celulas": pronto_celulas, "capa": None}
    dur = 6.0

    def no_ecra(cel, t):
        """O retangulo onde a celula esta no instante t, com as contas do desenhar(), ou None antes de entrar."""
        x, y, w, h = cel["rect"]
        e = (t - cel["atraso"]) / render.LADO_ENTRADA
        if e <= 0:
            return None
        e = 1.0 - (1.0 - min(1.0, e)) ** 3
        dx = dy = 0
        if cel["vem"] == "esq":
            dx = -int(round((1.0 - e) * (x + w)))
        elif cel["vem"] == "dir":
            dx = int(round((1.0 - e) * (L - x)))
        else:
            dy = int(round((1.0 - e) * (A - y)))
        return (x + dx, y + dy, w, h)

    cruzam = set()
    for q in range(int(dur * render.FPS)):
        t = q / float(render.FPS)
        agora = [(k, no_ecra(c, t)) for k, c in enumerate(pronto_celulas)]
        agora = [(k, r) for k, r in agora if r]
        for i in range(len(agora)):
            for j in range(i + 1, len(agora)):
                (ka, a), (kb, b) = agora[i], agora[j]
                if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                    cruzam.add((ka + 1, kb + 1))
    if cruzam:
        problemas.append("celulas a atravessar outras ao entrar: %s" % sorted(cruzam))
    fim = render.desenhar(pronto, dur - 0.04, dur)
    for k, (x, y, w, h) in enumerate(rects):
        cor = fim.getpixel((x + w // 2, y + h // 2))
        if max(abs(a - b) for a, b in zip(cor, cores[k])) > 3:
            problemas.append("celula %d com %s no fim e nao %s" % (k + 1, cor, cores[k]))
    inicio = render.desenhar(pronto, 0.0, dur)
    if any(inicio.getpixel((x + w // 2, y + h // 2)) != (0, 0, 0) for x, y, w, h in rects):
        problemas.append("no instante zero ja ha celulas no ecra")
    # pelo preparar
    pasta = tempfile.mkdtemp(prefix="teste_lado_6g_")
    caminhos = []
    for k in range(6):
        caminho = os.path.join(pasta, "cor%d.png" % k)
        Image.new("RGB", (800, 600) if k % 2 else (450, 600), CORES_MONTE[k]).save(caminho)
        caminhos.append(caminho)
    clip = {"tipo": "lado", "texto_ecra": "", "tratamento": "6g", "fonte_imagem": "", "ficheiro": "",
            "id": "", "transicao_s": "0.7", "_caminhos": caminhos}
    seis = render.preparar(clip, {})
    cinco = render.preparar(dict(clip, _caminhos=caminhos[:5]), {})
    if not seis or len(seis.get("celulas", [])) != 6 or cinco is not None:
        problemas.append("pelo preparar: 6 fotos %s, 5 fotos %s" % (
            len(seis["celulas"]) if seis else None, "None" if cinco is None else "um clip"))
    else:
        quadro = render.desenhar(seis, dur - 0.04, dur)
        for k, (x, y, w, h) in enumerate(rects):
            if max(abs(a - b) for a, b in zip(quadro.getpixel((x + w // 2, y + h // 2)), CORES_MONTE[k])) > 3:
                problemas.append("pelo preparar, a celula %d nao tem a foto %d" % (k + 1, k + 1))
    tempos = render.tempos_legenda_grupo("lado", None, dur, estilo="6g")
    if [round(a, 6) for a, _b in tempos] != [0.0] + [round(0.35 + k * 0.45, 6) for k in range(1, 6)]:
        problemas.append("tempos da legenda do 6g %s" % tempos)
    verifica("lado a lado 6g: duas filas de tres, entram sem se atravessar e ficam no sitio", not problemas,
             "; ".join(problemas[:3]) if problemas else
             "celulas %s, %d fotogramas da entrada, pelo preparar e na legenda" % (rects[:2], int(dur * render.FPS)))


def teste_colagem_e_pilha_com_muitas_fotos():
    """A colagem de 6 a 12 e a pilha de 9 a 20, nos dois estilos: dentro do ecra, acima da legenda, e com as garantias de cada um.

    O PEDIDO, do Tiago a 17 de setembro: mais fotos na colagem e na pilha. Os testes de antes
    medem ate 5 e 8. Aqui, para todos os numeros novos, deitadas e misturadas, com legenda de
    duas linhas nos pares e sem legenda nos impares:
      - todas as fotos pousadas dentro do ecra, a respirar e a recuar, e acima da faixa da
        legenda;
      - na colagem, nenhuma foto que chega depois entra no miolo nem no foco de uma de baixo
        (a conta das orlas, colagem_guardado()), e os angulos sao os do ensaio pela ordem;
      - em filas, com fotos todas da mesma forma, a mais pequena tem pelo menos 45% da maior:
        com todas as particoes, 8 fotos 4:3 davam duas com 22% do ecra e seis com 2,7%;
      - em filas, as particoes que se experimentam sao as de colagem_particoes() escritas aqui
        a mao, e a escolhida da pelo menos a area medida a 17 de setembro menos 15%, em quatro
        formas uniformes. Sem isto, COLAGEM_MUITAS_LINHAS e COLAGEM_MUITAS_POR_LINHA nao tinham
        teste nenhum: duas filas de ate 11 passavam a suite inteira e punham 12 fotos 4:3 com
        metade do tamanho;
      - na espalhada a primeira e a maior, nenhuma das seguintes passa de 90% dela, e nenhuma
        cresce em relacao a anterior; e todas juntas tem pelo menos 25% do ecra;
      - no leque cada foto de baixo fica com pelo menos PILHA_LEQUE_VE a vista, e abre de fora
        para dentro; no monte, as caixas e os desvios do ensaio para qualquer numero.
    E desenhado, numa de cada estilo com o maximo e legenda, pelas cores das fotos: todos os
    fotogramas pares dentro do ecra (a pilha a cair fica de fora, de proposito), o miolo de
    cada foto da colagem a vista no fim, cada foto da pilha a vista quando pousa, no leque as
    de baixo com a parte exigida e a de cima inteira no fim.
    """
    import render
    problemas, casos = [], 0
    L, A = render.L, render.A
    ecra = L * A / (1 + render.COLAGEM_RESPIRA) ** 2
    texto_duas = "Verao de 2014\nParis com os amigos"
    livre = render.faixa_texto(texto_duas)[1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * A

    def dentro(fotos, zoom, limite):
        pior = None
        for k, f in enumerate(fotos):
            for px, py in render.contorno_monte(f):
                x, y = L / 2.0 + (px - L / 2.0) * zoom, A / 2.0 + (py - A / 2.0) * zoom
                if x < -0.5 or y < -0.5 or x > L + 0.5 or y > A + 0.5:
                    return "foto %d fora do ecra, em (%.0f, %.0f)" % (k + 1, x, y)
                if limite is not None and y > limite + 0.5 and (pior is None or y > pior[1]):
                    pior = (k, y)
        return None if pior is None else "foto %d desce a %.0f, a legenda comeca em %.0f" % (pior[0] + 1, pior[1], limite)

    def miolo_pisado(fotos, focos):
        for j in range(1, len(fotos)):
            for i in range(j):
                for zona in render.colagem_guardado(fotos, focos, i):
                    d = render.afastar(zona, render.contorno_monte(fotos[j]))
                    if d and math.hypot(d[0], d[1]) - 1.0 > 1.0:
                        return "a foto %d entra %.1f px no miolo da %d" % (j + 1, math.hypot(d[0], d[1]) - 1.0, i + 1)
        return None

    for n in range(6, 13):
        for forma, aspetos, legenda, estilos in [
                (forma, aspetos, legenda, ("filas", "espalhada") if (legenda is None) == (n % 2 == 1) else ("filas",))
                for forma, aspetos in (("deitadas", [4 / 3.0] * n), ("misturadas", _formas_monte(n)["misturadas"]))
                for legenda in (None, livre)]:
            # As filas medem-se com e sem legenda em todos os numeros, que sao rapidas: 8 fotos 4:3
            # sem legenda e que partiam em 6 e 2. A espalhada leva segundos e alterna.
            focos = [None] * n
            focos[1] = (0.1, 0.97)
            for estilo in estilos:
                casos += 1
                nome = "colagem %s de %d %s%s" % (estilo, n, forma, " com legenda" if legenda else "")
                funcao = render.colagem_disposicao if estilo == "filas" else render.colagem_espalhada
                fotos = funcao(aspetos, focos, legenda)
                areas = [f[2] * f[3] / ecra for f in fotos]
                erro = dentro(fotos, 1.0 + render.COLAGEM_RESPIRA, legenda) or miolo_pisado(fotos, focos)
                if erro:
                    problemas.append("%s: %s" % (nome, erro))
                if [f[4] for f in fotos] != [render.COLAGEM_ANGULOS[k % 5] for k in range(n)]:
                    problemas.append("%s: angulos %s" % (nome, [f[4] for f in fotos]))
                if estilo == "filas" and forma == "deitadas" and min(areas) < 0.45 * max(areas):
                    problemas.append("%s: a mais pequena com %.1f%% do ecra e a maior com %.1f%%"
                                     % (nome, 100 * min(areas), 100 * max(areas)))
                if estilo == "espalhada":
                    if (any(a > 0.9 * areas[0] for a in areas[1:])
                            or any(areas[k + 1] > areas[k] * 1.0001 for k in range(n - 1))):
                        problemas.append("%s: tamanhos %s, a primeira nao e a maior ou ha uma a crescer"
                                         % (nome, " ".join("%.1f%%" % (100 * a) for a in areas)))
                    if sum(areas) < 0.25:
                        problemas.append("%s: todas juntas com %.0f%% do ecra" % (nome, 100 * sum(areas)))

    # AS FILAS DE MUITAS FOTOS TEM DE FICAR EQUILIBRADAS, e nada prendia isso. Quem decide e
    # colagem_particoes(): acima de COLAGEM_POUCAS so filas equilibradas, ate
    # COLAGEM_MUITAS_LINHAS filas de ate COLAGEM_MUITAS_POR_LINHA fotos. O DEFEITO QUE ISTO
    # APANHA: com 2 filas de ate 11 a suite passava inteira e a colagem de 12 fotos 4:3 sem
    # legenda caia de 70% para 35% do ecra, duas filas compridas com as fotos a metade do
    # tamanho; com panoramicas caia para 19%. A 15 metros e a diferenca entre ver as caras e
    # nao ver nada. A regra de cima nao mordia porque so exige a mais pequena com 45% da maior
    # E com fotos todas da mesma forma, e nesse caso uma fila so da todas iguais, logo 100%.
    # Prende-se por duas vias, que apanham coisas diferentes: as particoes que se experimentam,
    # literais (as constantes), e a area que a escolhida da no fim (a escolha entre elas).
    particoes = {6: "6 33 222 2211 2121 2112 1221 1212 1122",
                 7: "43 34 322 232 223 2221 2212 2122 1222",
                 8: "44 332 323 233 2222",
                 9: "54 45 333 3222 2322 2232 2223",
                 10: "55 433 343 334 3322 3232 3223 2332 2323 2233",
                 11: "65 56 443 434 344 3332 3323 3233 2333",
                 12: "66 444 3333"}
    for n, esperadas in sorted(particoes.items()):
        # a ordem conta: e ela que desempata quando duas particoes dao a mesma area. Uma fila
        # com mais de 9 fotos escreve-se com dois algarismos e nunca bate com nenhuma destas.
        vistas = " ".join("".join(str(len(l)) for l in p) for p in render.colagem_particoes(n))
        if vistas != esperadas:
            problemas.append("as particoes de %d fotos sao %r, esperadas %r" % (n, vistas, esperadas))
    # A AREA QUE A ESCOLHIDA DA, com fotos todas da mesma forma, em % do ecra a respirar.
    # Medido a 17 de setembro no codigo de agora, com 15% de folga por baixo: e um chao, nao um
    # alvo. Se uma revisao futura o baixar de proposito, muda-se o numero e diz-se porque.
    for forma, aspeto, chaos in (
            ("deitadas 4:3", 4 / 3.0, ((63, 55, 46, 44, 49, 54, 59), (42, 49, 46, 41, 36, 33, 36))),
            ("altas 3:4", 3 / 4.0, ((39, 45, 52, 58, 64, 58, 51), (26, 28, 33, 36, 41, 44, 48))),
            ("quadradas", 1.0, ((51, 59, 61, 54, 48, 44, 45), (32, 37, 43, 48, 48, 44, 39))),
            ("panoramicas 2,4", 2.4, ((51, 58, 63, 53, 45, 50, 55), (36, 36, 41, 48, 49, 44, 39)))):
        for legenda, chao_por_n in ((None, chaos[0]), (livre, chaos[1])):
            for n in range(6, 13):
                casos += 1
                fotos = render.colagem_disposicao([aspeto] * n, [None] * n, legenda)
                total = 100 * sum(f[2] * f[3] / ecra for f in fotos)
                chao = chao_por_n[n - 6]
                if total < chao:
                    problemas.append("colagem em filas de %d %s%s: todas juntas com %.1f%% do ecra, o chao e %d%%"
                                     % (n, forma, " com legenda" if legenda else "", total, chao))
    for n in range(9, 21):
        for forma, aspetos in (("deitadas", [4 / 3.0] * n), ("misturadas", _formas_monte(n)["misturadas"])):
            legenda = livre if n % 2 == 0 else None
            for estilo in ("monte", "leque"):
                casos += 1
                nome = "pilha %s de %d %s%s" % (estilo, n, forma, " com legenda" if legenda else "")
                fotos = (render.pilha_leque if estilo == "leque" else render.pilha_disposicao)(aspetos, legenda)
                erro = dentro(fotos, 1.0, legenda)
                if erro:
                    problemas.append("%s: %s" % (nome, erro))
                if [f[4] for f in fotos] != [render.PILHA_ANGULOS[k % 8] for k in range(n)]:
                    problemas.append("%s: angulos %s" % (nome, [f[4] for f in fotos]))
                if estilo == "leque":
                    pouco = [k + 1 for k in range(n - 1) if render.fracao_a_vista(fotos, k) < render.PILHA_LEQUE_VE]
                    xs = [f[0] for f in fotos]
                    if pouco or not (xs[0] == min(xs) and xs[1] == max(xs) and min(xs[:-1]) < xs[-1] < max(xs[:-1])):
                        problemas.append("%s: fotos com menos de %.0f%% a vista %s, centros %s"
                                         % (nome, 100 * render.PILHA_LEQUE_VE, pouco, [int(x) for x in xs]))

    # DESENHADAS: o maximo de cada estilo, misturadas, com legenda, pelas cores.
    desenhadas = 0
    for tipo, estilo, n in (("colagem", "filas", 12), ("colagem", "espalhada", 12), ("pilha", "monte", 20),
                            ("pilha", "leque", 20)):
        desenhadas += 1
        aspetos = _formas_monte(n)["misturadas"]
        pronto = _monte_de_cores(tipo, aspetos, texto_duas, estilo=estilo)
        nome = "%s %s de %d desenhada" % (tipo, estilo, n)
        dur = 20.0
        limite = pronto["capa"][1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * A
        fora = None
        for q in range(0, int(round(dur * render.FPS)), 2):
            poses, _z = render.poses_monte(pronto, q / float(render.FPS), dur)
            for k, x, y, tam, _alfa, pousada in poses:
                if tipo == "pilha" and not pousada:
                    continue
                f = pronto["fotos"][k]
                w, h = f["tamanho"]
                pts = render.cantos(x, y, (w / 2.0 + f["moldura"]) * tam, (h / 2.0 + f["moldura"]) * tam, f["angulo"])
                if any(px < -0.5 or py < -0.5 or px > L + 0.5 or py > A + 0.5 for px, py in pts):
                    fora = "foto %d fora do ecra aos %.2f s" % (k + 1, q / 25.0)
                elif pousada and max(py for _px, py in pts) > limite + 0.5:
                    fora = "foto %d abaixo da legenda aos %.2f s" % (k + 1, q / 25.0)
                if fora:
                    break
            if fora:
                break
        if fora:
            problemas.append("%s: %s" % (nome, fora))
        inicios, entrada, _z = render.estado_monte(pronto, 0.0, dur)
        fim = dur - 1.0 / render.FPS
        tela_fim = render.desenhar(pronto, fim, dur)
        poses_fim, zoom = render.poses_monte(pronto, fim, dur)
        if tipo == "colagem":
            miolo = 0.5 - render.MONTE_PISA - 0.02
            for k, x, y, tam, _a, _p in poses_fim:
                f = pronto["fotos"][k]
                w, h = f["tamanho"]
                tapados = sum(1 for a in (-1, 0, 1) for b in (-1, 0, 1)
                              if tela_fim.getpixel(tuple(int(v) for v in render.cantos(
                                  x, y, a * miolo * w * tam, b * miolo * h * tam, f["angulo"])[2])) != CORES_MONTE[k])
                if tapados:
                    problemas.append("%s: foto %d com %d de 9 pontos do miolo tapados no fim" % (nome, k + 1, tapados))
        else:
            for k in range(n):
                tela = render.desenhar(pronto, inicios[k] + entrada, dur)
                w, h = pronto["fotos"][k]["tamanho"]
                cheia = _visivel(tela, CORES_MONTE[k]) / float((w - 4) * (h - 4))
                if cheia < 0.97:
                    problemas.append("%s: foto %d so %.0f%% a vista quando pousa" % (nome, k + 1, 100 * cheia))
            # Tres pixeis de anel e nao dois, como nos outros: no fim a camada do conjunto e
            # escalada, e numa foto de 230 pixeis o esbatido da borda de duas amostragens ja
            # pesa 1,5% (medido: 96,7% com dois pixeis, 98,3% com tres, 98,9% foto a foto).
            w, h = pronto["fotos"][-1]["tamanho"]
            if _visivel(tela_fim, CORES_MONTE[n - 1]) / ((w * zoom - 6) * (h * zoom - 6)) < 0.97:
                problemas.append("%s: a de cima nao esta inteira no fim" % nome)
            if estilo == "leque":
                for k in range(n - 1):
                    w, h = pronto["fotos"][k]["tamanho"]
                    ve = _visivel(tela_fim, CORES_MONTE[k]) / (w * zoom * h * zoom)
                    if ve < render.PILHA_LEQUE_VE:
                        problemas.append("%s: foto %d com %.0f%% a vista no fim" % (nome, k + 1, 100 * ve))
    verifica("colagem ate 12 e pilha ate 20: dentro do ecra, acima da legenda, com as garantias de cada estilo",
             not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d disposicoes e %d desenhadas pelas cores" % (casos, desenhadas))


def teste_agenda_nova_na_legenda_e_nas_tapadas():
    """A legenda de baixo, o desvanecer das tapadas e os avisos do montar_da_mesa seguem a agenda nova.

    O PEDIDO: dividir a duracao pelas fotos. Tudo o que depende de quando cada foto entra tem
    de mudar com a agenda, e com uma conta so: a troca da legenda de baixo, o texto das fotos
    de baixo da pilha que desaparece quando a seguinte cai, os avisos de texto curto do
    render e do montar_da_mesa.py. Os tempos estao escritos aqui pela regra, vez = (duracao -
    max(0,35; entra) - sai) / (n + 1), em clips longos em que a agenda de antes dava outros
    (entradas de 1,3 s na pilha e 1,6 s na colagem):
      - tempos_legenda_grupo() de uma colagem de 4 em 12 s e de uma pilha de 3 em 10 s;
      - legendas_curtas() de uma colagem de 5 em 4 s a abrir o corpo: 0,84 s, 0,49 s, 0,49 s e
        0,49 s, e a ultima nao;
      - numa pilha de 4 em 12 s com "some", o texto da foto k ainda la esta 0,02 s antes de a
        seguinte comecar, e ja desapareceu 0,02 s depois do desvanecer, com a vez de 2,12 s;
      - e o montar_da_mesa.py nao avisa essa pilha na legenda de baixo (a agenda de antes dava
        1,3 s a cada texto do meio, e avisava dois), e avisa a colagem de 5 em 4 s quatro vezes.
    """
    import contextlib
    import io
    import render
    problemas = []

    def perto(a, b, tol=1e-9):
        return len(a) == len(b) and all(abs(x[0] - y[0]) <= tol and abs(x[1] - y[1]) <= tol for x, y in zip(a, b))

    vez = (12.0 - 0.7 - 0.7) / 5
    esperados = [(0.0, 0.7 + vez), (0.7 + vez, 0.7 + 2 * vez), (0.7 + 2 * vez, 0.7 + 3 * vez), (0.7 + 3 * vez, 12.0)]
    obtidos = render.tempos_legenda_grupo("colagem", 4, 12.0, 0.7, 0.7)
    if not perto(obtidos, esperados):
        problemas.append("colagem de 4 em 12 s: tempos %s, a regra da %s" % (obtidos, esperados))
    vez = (10.0 - 0.35 - 2.5) / 4
    esperados = [(0.0, 0.35 + vez), (0.35 + vez, 0.35 + 2 * vez), (0.35 + 2 * vez, 10.0)]
    obtidos = render.tempos_legenda_grupo("pilha", 3, 10.0, 0.0, 2.5)
    if not perto(obtidos, esperados):
        problemas.append("pilha de 3 em 10 s: tempos %s, a regra da %s" % (obtidos, esperados))
    vez = (4.0 - 0.35 - 0.7) / 6
    curtas = render.legendas_curtas(["A", "B", "C", "D", "E"], render.tempos_legenda_grupo("colagem", 5, 4.0, 0.0, 0.7))
    esperadas = [(0, "A", 0.35 + vez), (1, "B", vez), (2, "C", vez), (3, "D", vez)]
    if len(curtas) != 4 or any(c[:2] != e[:2] or abs(c[2] - e[2]) > 1e-9 for c, e in zip(curtas, esperadas)):
        problemas.append("colagem de 5 em 4 s: curtas %s, a regra da %s" % (curtas, esperadas))

    # O desvanecer das tapadas, desenhado: as referencias sao a mesma pilha com "fica" e os
    # textos das primeiras k fotos em branco.
    textos = ["NATAL", "2019", "Verao", "Porto"]
    imagens = _fotos_lisas(4)
    dur = 12.0
    with contextlib.redirect_stdout(io.StringIO()):
        some = render.preparar_monte("pilha", imagens, None, "", 0.7, 0.7, "monte", textos=textos)
        brancos = [render.preparar_monte("pilha", imagens, None, "", 0.7, 0.7, "monte",
                                         textos=[""] * k + textos[k:], opcoes={"tapadas": "fica"})
                   for k in range(5)]
    vez = (dur - 0.7 - 0.7) / 5
    for k in range(3):
        seguinte = 0.7 + (k + 1) * vez
        antes_q = render.desenhar(some, seguinte - 0.02, dur).tobytes()
        depois_q = render.desenhar(some, seguinte + 0.2 + 0.02, dur).tobytes()
        if antes_q != render.desenhar(brancos[k], seguinte - 0.02, dur).tobytes():
            problemas.append("pilha de 4 em 12 s: aos %.2f s o texto da foto %d ja nao esta" % (seguinte - 0.02, k + 1))
        if depois_q != render.desenhar(brancos[k + 1], seguinte + 0.22, dur).tobytes():
            problemas.append("pilha de 4 em 12 s: aos %.2f s o texto da foto %d ainda nao desapareceu"
                             % (seguinte + 0.22, k + 1))
        if abs(render.alfa_texto_pilha(seguinte + 0.1, render.inicios_do_grupo("pilha", 4, dur, 0.7, 0.7)[k + 1],
                                       0.4) - 0.5) > 1e-6:
            problemas.append("pilha de 4 em 12 s: a meio do desvanecer da foto %d o texto nao esta a metade" % (k + 1))

    # O montar_da_mesa.py, com os avisos da legenda de baixo.
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"), encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        problemas.append("fotos do ensaio fora do inventario")
    else:
        grupo = {"x": "", "c": 0.7, "r": "fiel", "vf": True, "vm": "legenda"}
        clips = [dict(grupo, t="colagem", fotos=(tres * 2)[:5], d=4.0, xf=["A", "B", "C", "D", "E"]),
                 dict(grupo, t="pilha", fotos=tres + tres[:1], d=12.0, xf=["P1", "P2", "P3", "P4"]),
                 dict(grupo, t="foto", i="f0331", d=4.0, vf=False, vm=None)]
        linhas, _cab, saida, _av = _mesa_de_ensaio(clips, "teste_agenda_nova_")
        avisos = [l.strip() for l in saida.splitlines() if "na legenda de baixo" in l]
        vez = (4.0 - 0.35 - 0.7) / 6
        esperados = ["colagem: o texto da foto %d fica so %.1f s na legenda de baixo, pouco para ler a 15 metros: "
                     "'%s' (clip 1)" % (k + 1, (0.35 + vez) if k == 0 else vez, t) for k, t in enumerate("ABCD")]
        if sorted(avisos) != sorted(esperados):
            problemas.append("montar_da_mesa avisa %s, a regra da %s" % (avisos, esperados))
    verifica("a legenda de baixo, as tapadas e os avisos seguem a agenda nova", not problemas,
             "; ".join(problemas[:3]) if problemas else
             "tempos de 2 grupos, 4 curtas, 3 desvanecimentos desenhados, avisos da Mesa")


def teste_colagem_e_pilha_pelo_preparar():
    """A colagem e a pilha chegam ao desenho pelo caminho do render, com ficheiros, legenda e encadeados.

    O DEFEITO QUE ISTO APANHA: os outros testes entram por preparar_monte com imagens em
    memoria. Uma revisao estragou de proposito o preparar() para deixar de encaminhar a
    colagem, o main para deixar de preencher os _caminhos, a legenda para nao ser colada,
    a foto em falta para nao devolver None, e os limites do render para serem outros que
    os do montar_da_mesa.py. Nenhum teste falhou, e cada uma dava no video um cartao
    preto ou uma colagem sem legenda.
    """
    import tempfile
    import montar_da_mesa
    import render
    pasta = tempfile.mkdtemp(prefix="teste_preparar_monte_")
    ficheiros = []
    for k in range(8):
        caminho = os.path.join(pasta, "cor%d.png" % k)
        Image.new("RGB", (800, 600) if k % 2 else (450, 600), CORES_MONTE[k]).save(caminho)
        ficheiros.append(caminho)
    problemas = []

    def preparar(clip):
        try:
            return render.preparar(clip, {})
        except Exception as erro:
            problemas.append("preparar rebentou: %r" % erro)
            return None

    def clip(tipo, caminhos, texto="", **extra):
        c = {"tipo": tipo, "texto_ecra": texto, "tratamento": "fiel", "fonte_imagem": "",
             "ficheiro": "|".join(os.path.basename(p) for p in caminhos), "id": "",
             "transicao_s": "0.7", "_caminhos": caminhos}
        c.update(extra)
        return c

    # Os pixeis onde a letra da legenda e opaca. Contar brancos no ecra inteiro nao
    # serve: a moldura clara ampliada pela respiracao da pixeis a 255 nas bordas.
    letra = render.faixa_texto("Amigos")[1].point(lambda v: 255 if v == 255 else 0)
    n_letra = float(letra.histogram()[255])

    def na_letra(tela):
        """Fracao dos pixeis da letra que estao brancos puros neste fotograma."""
        branco = tela.convert("L").point(lambda v: 255 if v == 255 else 0)
        return branco.histogram(mask=letra)[255] / n_letra

    for tipo, n, dur in (("colagem", 5, 11.0), ("pilha", 8, 9.4)):
        pronto = preparar(clip(tipo, ficheiros[:n], "Amigos", _transicao_seguinte="1.2"))
        if not pronto or pronto.get("tipo") != tipo or len(pronto.get("fotos", [])) != n:
            problemas.append("%s de %d nao chega ao desenho como %s" % (tipo, n, tipo))
            continue
        if pronto["cross"] != (0.7, 1.2):
            problemas.append("%s: encadeados %s em vez de (0.7, 1.2)" % (tipo, pronto["cross"]))
        sem_seguinte = preparar(clip(tipo, ficheiros[:n]))
        if not sem_seguinte or sem_seguinte["cross"] != (0.7, 0.7):
            problemas.append("%s sem clip seguinte nao conta o encadeado de entrada" % tipo)
        fim = dur - 1.0 / render.FPS
        tela = render.desenhar(pronto, fim, dur)
        sem_texto = render.desenhar(sem_seguinte, fim, dur) if sem_seguinte else tela
        com, sem = na_letra(tela), na_letra(sem_texto)
        if com < 0.99 or sem > 0.2:
            problemas.append("%s: letra da legenda branca em %.0f%% com texto e %.0f%% sem texto"
                             % (tipo, 100 * com, 100 * sem))
        a_vista = [k for k in range(n) if _visivel(tela, CORES_MONTE[k]) > 500]
        if len(a_vista) < (n if tipo == "colagem" else 1):
            problemas.append("%s: so %d fotos a vista no fim" % (tipo, len(a_vista)))
        zoom = render.estado_monte(pronto, fim, dur)[2]
        if (tipo == "colagem" and zoom < 1.02) or (tipo == "pilha" and zoom > 0.92):
            problemas.append("%s: zoom do fim %.3f, nao respira nem recua" % (tipo, zoom))
        # A agenda do desenho tem de contar os encadeados que o preparar guardou: a
        # primeira foto so depois dos 0,7 s de entrada, e a ultima parada as suas duas vezes
        # menos a entrada antes dos 1,2 s do encadeado de saida, com a vez dividida so pelo
        # tempo entre os dois encadeados.
        inicios, entrada, _ = render.estado_monte(pronto, 0.0, dur)
        folga = dur - inicios[-1] - entrada
        vez = (dur - 0.7 - 1.2) / (n + 1)
        if abs(inicios[0] - 0.7) > 1e-9 or abs(folga - (2 * vez - entrada + 1.2)) > 1e-9:
            problemas.append("%s: primeira aos %.2f s e folga de %.2f s, a agenda nao conta os encadeados 0.7/1.2"
                             % (tipo, inicios[0], folga))
        em_falta = ficheiros[:n - 1] + [os.path.join(pasta, "nao_existe.png")]
        if preparar(clip(tipo, em_falta)) is not None:
            problemas.append("%s com uma foto em falta nao devolve None" % tipo)
        minimo, maximo = render.LIMITES_MONTE[tipo]
        if preparar(clip(tipo, (ficheiros * 3)[:maximo + 1])) is not None:
            problemas.append("%s com %d fotos nao devolve None" % (tipo, maximo + 1))
        # OS DOIS LIMITES ACEITES CHEGAM AO DESENHO. So se via o maximo mais um recusado: com o
        # `<=` do preparar() trocado por `<`, a colagem de 12 e a pilha de 20 que a Mesa e o
        # montar_da_mesa aceitam saiam do video sem aviso, e a suite inteira passava.
        for conta in (minimo, maximo):
            aceite = preparar(clip(tipo, (ficheiros * 3)[:conta]))
            if not aceite or aceite.get("tipo") != tipo or len(aceite.get("fotos", [])) != conta:
                problemas.append("%s de %d fotos, dentro dos limites, nao chega ao desenho" % (tipo, conta))
        if preparar(clip(tipo, ficheiros[:minimo - 1])) is not None:
            problemas.append("%s com %d fotos nao devolve None" % (tipo, minimo - 1))
    verifica("colagem e pilha: pelo preparar do render, com legenda e encadeados", not problemas,
             "; ".join(problemas[:3]) if problemas else "colagem de 5 e pilha de 8 a partir de ficheiros, os limites aceites e recusados")
    verifica("colagem e pilha: limites iguais no render e no montar_da_mesa",
             render.LIMITES_MONTE == montar_da_mesa.LIMITES_MONTE,
             "%s e %s" % (render.LIMITES_MONTE, montar_da_mesa.LIMITES_MONTE))

    # O main poe os ficheiros nos clips por caminhos_pelo_indice e os encadeados por
    # ligar_transicoes. Uma foto de um grupo sem indice fica com o original e entra no aviso.
    inv_por_id = {"a": {"id": "a", "ficheiro": "a.jpg", "caminho": "orig_a"},
                  "b": {"id": "b", "ficheiro": "b.jpg", "caminho": "orig_b"},
                  "s": {"id": "s", "ficheiro": "s.jpg", "caminho": "orig_s"}}
    inv_por_nome = {r["ficheiro"]: r for r in inv_por_id.values()}
    indice = {"a": "final_a"}
    clips = [{"tipo": "video", "id": "", "ficheiro": "abre.mp4", "transicao_s": "0"},
             {"tipo": "colagem", "id": "a|b|z", "ficheiro": "a.jpg|b.jpg|z.jpg", "transicao_s": "0.7"},
             {"tipo": "foto", "id": "s", "ficheiro": "s.jpg", "transicao_s": "0.3"},
             {"tipo": "pilha", "id": "b|a", "ficheiro": "b.jpg|a.jpg", "transicao_s": "0.5"},
             {"tipo": "cartao", "id": "", "ficheiro": "", "transicao_s": "1.2"},
             {"tipo": "colagem", "id": "a|b", "ficheiro": "a.jpg|b.jpg", "transicao_s": "0.9"}]
    sem = render.caminhos_pelo_indice(clips, indice, inv_por_id, inv_por_nome)
    certo = (clips[2]["_caminho"] == "orig_s" and clips[1]["_caminhos"] == ["final_a", "orig_b", None]
             and clips[3]["_caminhos"] == ["orig_b", "final_a"] and clips[5]["_caminhos"] == ["final_a", "orig_b"]
             and sorted(sem) == ["b.jpg", "b.jpg", "b.jpg", "s.jpg"])
    verifica("render: fotos dos grupos pelo indice, com aviso", certo,
             "sem indice %s, colagem %s" % (sorted(sem), clips[1].get("_caminhos")))

    # OS ENCADEADOS DAS PONTAS. O primeiro clip do corpo nao se encadeia com nada: os videos
    # antes dele sao colados com corte seco, e a primeira foto de uma colagem ali esperava
    # 0,7 s por um encadeado que nao existe. O ultimo do filme sai no fade a preto de 2,5 s,
    # que escurece as fotos como um encadeado; num render parcial nao ha fade.
    render.ligar_transicoes(clips)
    encadeados = [(c.get("_transicao_entrada"), c.get("_transicao_seguinte")) for c in clips[1:]]
    certo = (encadeados == [(0.0, 0.3), (0.3, 0.5), (0.5, 1.2), (1.2, 0.9), (0.9, 2.5)]
             and render.FADE_FIM_IMAGEM == 2.5 and "_transicao_seguinte" not in clips[0])
    render.ligar_transicoes(clips, fim_do_filme=False)
    parcial = (clips[1]["_transicao_entrada"], clips[5]["_transicao_seguinte"])
    certo = certo and parcial == (0.0, 0.0)
    render.ligar_transicoes(clips)
    agendas = []
    for k, caminhos, dur in ((1, ficheiros[:3], 7.8), (5, ficheiros[:2], 6.0)):
        pronto = preparar(clip(clips[k]["tipo"], caminhos, transicao_s=clips[k]["transicao_s"],
                               _transicao_entrada=clips[k]["_transicao_entrada"],
                               _transicao_seguinte=clips[k]["_transicao_seguinte"]))
        if not pronto:
            agendas.append(None)
            continue
        inicios, entrada, _ = render.estado_monte(pronto, 0.0, dur)
        agendas.append((pronto["cross"], round(inicios[0], 3), round(dur - inicios[-1] - entrada, 3)))
    # a ultima, colagem de 2 em 6 s entre 0,9 e o fade de 2,5: vez (6 - 0,9 - 2,5) / 3, parada
    # 2 vezes menos a entrada de 0,32 antes do fade
    certo = (certo and None not in agendas
             and agendas[0][0] == (0.0, 0.3) and abs(agendas[0][1] - 0.35) < 1e-6
             and agendas[1][0] == (0.9, 2.5) and abs(agendas[1][2] - (2 * (6.0 - 0.9 - 2.5) / 3 - 0.32 + 2.5)) < 2e-3)
    verifica("render: o primeiro clip do corpo entra sem encadeado e o ultimo sai no fade", certo,
             "encadeados %s, parcial %s, agendas da primeira e da ultima %s" % (encadeados, parcial, agendas))


def teste_monte_acima_da_legenda():
    """Pousadas, a pilha e a colagem ficam acima da faixa da legenda, em todas as formas e em todos os fotogramas.

    O DEFEITO: a faixa da legenda tapava a fila de baixo da colagem, e a pilha, sem o
    encaixe no ecra, descia ate 1046 com a faixa a comecar nos 900. Nenhum teste media
    a pilha contra a faixa: uma revisao tirou-lhe o encaixe e a suite passou.
    Nos dois estilos de cada um.
    """
    import render
    problemas, casos = [], 0
    for tipo, quantas, estilo in [(t, q, e) for t, q in (("pilha", (2, 3, 5, 8)), ("colagem", (2, 4, 5)))
                                  for e in render.ESTILOS_MONTE[t]]:
        for n in quantas:
            for forma, aspetos in sorted(_formas_monte(n).items()):
                for texto in ("Viagens", "Verao de 2014\nParis com os amigos"):
                    casos += 1
                    pronto = _monte_de_cores(tipo, aspetos, texto, estilo=estilo)
                    limite = pronto["capa"][1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * render.A
                    dur = 3 + 1.6 * n if tipo == "colagem" else 2.6 + 0.85 * n
                    pior = None
                    for q in range(0, int(round(dur * render.FPS)), 2):
                        poses, _ = render.poses_monte(pronto, q / float(render.FPS), dur)
                        for k, x, y, tam, _alfa, pousada in poses:
                            if not pousada:
                                continue
                            f = pronto["fotos"][k]
                            w, h = f["tamanho"]
                            fundo = max(py for _px, py in render.cantos(
                                x, y, (w / 2.0 + f["moldura"]) * tam, (h / 2.0 + f["moldura"]) * tam, f["angulo"]))
                            if fundo > limite + 0.5 and (pior is None or fundo > pior[0]):
                                pior = (fundo, k, q)
                    if pior:
                        problemas.append("%s %s de %d %s, legenda de %d linhas: foto %d desce a %.0f, faixa a %.0f"
                                         % (tipo, estilo, n, forma, texto.count("\n") + 1, pior[1] + 1, pior[0], limite))
    verifica("colagem e pilha: pousadas acima da faixa da legenda", not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d montes, todos os fotogramas pares" % casos)


def teste_mesa_nascimento_colagem_e_avisos():
    """Na Mesa: o cartao do nascimento estica para uma colagem, cada aviso sai uma vez, e a colagem curta avisa.

    OS DEFEITOS: o esticamento do cartao passou a contar lado a lado, colagem e pilha e
    nenhum teste o via; os avisos acumulavam nas duas passagens e saiam repetidos; e uma
    colagem ou pilha mais curta do que precisa apertava-se sem ninguem saber.
    Depois o aviso contava a entrada no primeiro clip do corpo, que nao se encadeia com
    nada, e esquecia o fade do fim no ultimo; e com 4,36 s contra 4,38 s dizia "com 4.4 s
    e curta: precisa de pelo menos 4.4 s". As duracoes minimas estao escritas aqui a mao,
    com a formula que a Mesa vai usar, e nao pedidas ao render.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # antes do redirect: o render mexe no sys.stdout ao ser importado
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    cinco = ["f0331", "f0334", "f0336", "f0308", "f0315"]
    if not all(i in inv for i in cinco):
        verifica("Mesa: nascimento, colagem e avisos", False, "fotos do ensaio fora do inventario")
        return
    pasta = tempfile.mkdtemp(prefix="teste_mesa_avisos_")
    # As tres curtas, com a conta escrita a mao:
    #   colagem de 2, primeira do corpo, entra sem encadeado e sai no cartao de 0,65 s:
    #     0,35 + 2 x 0,32 + 0,1 + 1,4 + 0,65 = 3,14, pede 3.2 s arredondado para cima; tem 3,12 s
    #     (arredondado ao mais proximo diria "com 3.12 s e curta: precisa de pelo menos 3.1 s")
    #   colagem de 5, sai na pilha de 1,2 s: 0,7 + 5 x 0,32 + 4 x 0,1 + 1,4 + 1,2 = 5,3; tem 4 s
    #   pilha de 5, ultimo clip, sai no fade de 2,5 s: 1,2 + 5 x 0,4 + 4 x 0,1 + 1,4 + 2,5 = 7,5; tem 7,2 s
    estado = {"versoes": [{"id": "t", "nome": "t", "clips": [
        {"t": "video", "f": "abertura_de_teste.mp4", "d": 4, "c": 0.7},
        {"t": "colagem", "fotos": tres[:2], "x": "", "d": 3.12, "c": 0.7, "r": "fiel"},
        {"t": "cartao", "x": "Nasce o Tiago", "d": 4, "c": 0.65},
        {"t": "colagem", "fotos": tres, "x": "", "d": 7.8, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f9999", "f": "", "d": 4, "c": 0.7, "r": "fiel"},
        {"t": "colagem", "fotos": cinco, "x": "", "d": 4.0, "c": 0.7, "r": "fiel"},
        {"t": "pilha", "fotos": cinco, "x": "", "d": 7.2, "c": 1.2, "r": "fiel"}]}]}
    caminho = os.path.join(pasta, "estado.json")
    json.dump(estado, open(caminho, "w", encoding="utf-8"))
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv, montar_da_mesa.duracao_do_video)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    montar_da_mesa.duracao_do_video = lambda nome: 5.0     # so a primeira passagem se queixa dele
    sys.argv = ["montar_da_mesa.py", "t", "--nome", "t"]
    saida = io.StringIO()
    try:
        with contextlib.redirect_stdout(saida):
            montar_da_mesa.main()
    finally:
        (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv,
         montar_da_mesa.duracao_do_video) = guardado
    texto = saida.getvalue()
    linhas = list(csv.DictReader(open(os.path.join(pasta, "t.csv"), encoding="utf-8-sig")))
    cartao = next(l for l in linhas if l["tipo"] == "cartao")
    colagem = next(l for l in linhas
                   if l["tipo"] == "colagem" and float(l["inicio_s"]) > float(cartao["inicio_s"]))
    folga = float(colagem["inicio_s"]) - float(cartao["inicio_s"])
    # Os foguetes duram VINHETA_DURA, e a colagem so pode comecar 0,4 s depois de acabarem.
    precisa = montar_da_mesa.VINHETA_DURA + 0.4
    verifica("Mesa: o cartao do nascimento estica para a colagem que vem a seguir", folga >= precisa - 0.01,
             "a colagem entra %.2f s depois do cartao, precisa de %.2f s" % (folga, precisa))
    video = texto.count("usei o ficheiro")
    sem_foto = texto.count("sem foto: ")
    curtas = [l.strip() for l in texto.splitlines() if "e curta" in l]
    verifica("Mesa: cada aviso sai uma vez, tambem os que so a primeira passagem ve",
             video == 1 and sem_foto == 1, "video %d vez(es), foto em falta %d vez(es)" % (video, sem_foto))
    esperadas = [("colagem de 2 fotos com 3.12 s", "3.2"), ("colagem de 5 fotos com 4.0 s", "5.3"),
                 ("pilha de 5 fotos com 7.2 s", "7.5")]
    contradiz = []
    for l in curtas:
        m = re.search(r"com ([\d.]+) s e curta: precisa de pelo menos ([\d.]+) s", l)
        if not m or float(m.group(1)) >= float(m.group(2)):
            contradiz.append(l)
    certo = (len(curtas) == len(esperadas) and not contradiz
             and all(any(l.startswith(q) and ("pelo menos %s s " % v) in l for l in curtas)
                     for q, v in esperadas)
             and any(l.startswith("pilha de 5") and "antes do fade do fim" in l for l in curtas)
             and any(l.startswith("colagem de 5") and "antes do encadeado" in l for l in curtas))
    verifica("Mesa: avisa a colagem e a pilha curtas com a conta das pontas", certo,
             " | ".join(curtas) if curtas else "sem aviso")


def teste_colagem_espalhada():
    """A colagem espalhada e a do ensaio: a primeira maior, as outras a descer, sem filas, e com area que se le.

    O PEDIDO, decisao 068: "espalhada", como no ensaio de 10 de setembro, a primeira maior e
    as outras de tamanho a descer, tortas, a pisar-se nas orlas, sem grelha nem filas. Sem
    este teste a espalhada podia voltar a ser uma grelha, ou ficar com as fotos todas iguais,
    e as garantias de pousar e de nao tapar caras passavam na mesma.
    Duas fotos estao na mesma fila quando tem a mesma altura e o centro a mesma altura do
    ecra, com 5% de A de folga: e o que a colagem em filas faz, e confirma-se que ela o
    apanha, para o criterio nao passar por nao medir nada. A area minima e 20% do ecra e a
    primeira com 7%: as fotos a descer somam menos do que em filas, mas a 15 metros a
    primeira nunca pode ficar pequena. E alguma foto tem de pisar outra, que e o que faz a
    colagem, e nenhuma pode entrar no miolo de uma de baixo.
    """
    import render
    livres = {}
    for texto in ("Amigos", "Verao de 2014\nParis com os amigos"):
        livres[texto] = render.faixa_texto(texto)[1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * render.A
    livre = livres["Amigos"]
    ecra = render.L * render.A / (1 + render.COLAGEM_RESPIRA) ** 2
    tol = 0.05 * render.A

    def em_fila(fotos):
        return [(i + 1, j + 1) for i in range(len(fotos)) for j in range(i + 1, len(fotos))
                if abs(fotos[i][3] - fotos[j][3]) < tol and abs(fotos[i][1] - fotos[j][1]) < tol]

    def tocam(fotos):
        return [(i + 1, j + 1) for i in range(len(fotos)) for j in range(i + 1, len(fotos))
                if render.afastar(render.contorno_monte(fotos[i]), render.contorno_monte(fotos[j]))]

    def pisa_guardado(fotos):
        """O maior pedaco, em pixeis, de uma foto que chega depois dentro do guardado de uma de baixo."""
        pior = 0.0
        for j in range(1, len(fotos)):
            for i in range(j):
                for zona in render.colagem_guardado(fotos, [], i):
                    d = render.afastar(zona, render.contorno_monte(fotos[j]))
                    if d:
                        pior = max(pior, math.hypot(d[0], d[1]) - 1.0)
        return pior

    def banda(fotos):
        """Maior menos menor altura dos centros, em alturas medias das fotos."""
        ys = [f[1] for f in fotos]
        return (max(ys) - min(ys)) / (sum(f[3] for f in fotos) / float(len(fotos)))

    def soltas(fotos):
        juntas = set(k for par in tocam(fotos) for k in par)
        return [k + 1 for k in range(len(fotos)) if k + 1 not in juntas]

    def com_minimos(fotos):
        areas = [f[2] * f[3] / ecra for f in fotos]
        return sum(areas) >= 0.20 and areas[0] >= 0.07

    def miolo_livre(fotos):
        """Nenhuma foto que chega depois dentro do guardado de uma de baixo, sem tolerancia nenhuma."""
        return not any(render.afastar(zona, render.contorno_monte(fotos[j]))
                       for j in range(1, len(fotos)) for i in range(j)
                       for zona in render.colagem_guardado(fotos, [], i))

    def espalhada_de_verdade(fotos):
        return (banda(fotos) >= 0.5 and com_minimos(fotos) and not em_fila(fotos) and not soltas(fotos)
                and miolo_livre(fotos))

    def resumo(lista):
        return ("; ".join(lista[:3]) + (" (+%d)" % (len(lista) - 3) if len(lista) > 3 else "")) if lista else ""

    # AS FORMAS. As da decisao 068, e as que a revisao de 15 de setembro achou fora do
    # criterio: tres a cinco verticais altas com legenda de duas linhas fechavam-se numa
    # coluna a meio do ecra, com a mais pequena a 1 ou 2% do ecra; e quatro 16:9 com duas
    # linhas, cinco panoramicas ou cinco 4:3 com duas linhas acabavam em filas. As altas
    # so entram de tres para cima: duas fotos de 0,45 com duas linhas, lado a lado e da
    # altura toda, nao passam de 24% do ecra, e o limite de 20% deixava de medir a espalhada.
    # A de 0,56 0,47 1 0,6 0,6 e a que precisa das aberturas ate 2,5: com legenda de duas
    # linhas e aberturas so ate 1,5 a primeira ficava com 6,5% do ecra.
    #
    # NUMA FILA SO, EM ESCADA. Sem filas de pares, 30 das formas acabavam com os centros
    # todos a mesma altura, cada foto um degrau ao lado da outra: duas verticais, tres a
    # cinco altas. As cinco 4:3 do ensaio ocupam 1,20 alturas de foto com os centros. Exige-se
    # pelo menos 0,5 e nenhuma foto solta, sem tocar em nenhuma, sempre que HA COMO: guarda-se
    # cada disposicao que o colagem_afastar deu por assente, e se a que saiu nao cumpre,
    # nenhuma dessas podia cumprir com os minimos de area e sem filas. Para o criterio nao
    # passar por nao medir nada, confirma-se que em alguma forma a de mais area nao cumpre.
    original = render.colagem_afastar
    assentes = []

    def regista(fotos, focos, quadro):
        assenta = original(fotos, focos, quadro)
        if assenta:
            assentes.append([list(f) for f in fotos])
        return assenta

    problemas, escada, tortas, sem_como, morde, casos = [], [], [], [], [], 0
    angulos = [render.COLAGEM_ANGULOS[i % len(render.COLAGEM_ANGULOS)] for i in range(5)]
    try:
        render.colagem_afastar = regista
        for n in (2, 3, 4, 5):
            formas = sorted(_formas_monte(n).items())
            formas += [("16:9", [16 / 9.0] * n), ("panoramicas", [2.3] * n)]
            if n >= 3:
                formas += [("2:3", [2 / 3.0] * n), ("9:16", [9 / 16.0] * n), ("0,45", [0.45] * n)]
            if n == 5:
                formas.append(("16:9 2:3 2:3 16:9 3:4", [16 / 9.0, 2 / 3.0, 2 / 3.0, 16 / 9.0, 3 / 4.0]))
                formas.append(("0,56 0,47 1 0,6 0,6", [0.56, 0.47, 1.0, 0.6, 0.6]))
            for forma, aspetos in formas:
                for texto, legenda in [("", None)] + sorted(livres.items()):
                    casos += 1
                    nome = "%d %s%s" % (n, forma, " com legenda de %d linhas" % (texto.count("\n") + 1) if texto else "")
                    assentes[:] = []
                    fotos = render.colagem_espalhada(aspetos, None, legenda)
                    areas = [f[2] * f[3] / ecra for f in fotos]
                    descem = all(areas[k + 1] <= 0.9 * areas[k] for k in range(n - 1))
                    if not descem:
                        problemas.append("%s: tamanhos %s nao descem" % (nome, " ".join("%.1f%%" % (100 * a) for a in areas)))
                    if em_fila(fotos):
                        problemas.append("%s: fotos %s em fila" % (nome, em_fila(fotos)))
                    if sum(areas) < 0.20 or areas[0] < 0.07:
                        problemas.append("%s: fotos com %.0f%% do ecra, a primeira com %.1f%%"
                                         % (nome, 100 * sum(areas), 100 * areas[0]))
                    if not tocam(fotos):
                        problemas.append("%s: nenhuma foto pisa outra" % nome)
                    if pisa_guardado(fotos) > 1.0:
                        problemas.append("%s: uma foto %.1f px dentro do miolo de outra" % (nome, pisa_guardado(fotos)))
                    if [f[4] for f in fotos] != angulos[:n]:
                        tortas.append("%s: angulos %s" % (nome, [f[4] for f in fotos]))
                    possiveis = [c for c in assentes if espalhada_de_verdade(c)]
                    if not espalhada_de_verdade(fotos):
                        if possiveis:
                            escada.append("%s: banda %.2f, soltas %s, e havia %d com banda de 0,5, sem soltas e com os minimos"
                                          % (nome, banda(fotos), soltas(fotos), len(possiveis)))
                        else:
                            sem_como.append(nome)
                    sem_fila = [c for c in assentes if not em_fila(c)]
                    if possiveis and sem_fila and not espalhada_de_verdade(max(sem_fila, key=lambda c: sum(f[2] * f[3] for f in c))):
                        morde.append(nome)
    finally:
        render.colagem_afastar = original
    filas_apanhadas = all(em_fila(render.colagem_disposicao(asp, None, leg)) for asp, leg in
                          (([4 / 3.0] * 4, None), ([3 / 4.0] * 3, livre), ([3 / 4.0] * 5, None)))
    verifica("colagem espalhada: a descer, sem filas, e com area", not problemas and filas_apanhadas,
             resumo(problemas) if problemas else ("%d colagens" % casos if filas_apanhadas
                                                  else "a colagem em filas nao tem filas, o criterio perdeu o sentido"))
    verifica("colagem espalhada: nunca numa fila so nem com soltas, se ha como", not escada and morde,
             resumo(escada) if escada else (
                 "%d colagens; em %d a de mais area era em escada ou com soltas; sem como em %d: %s"
                 % (casos, len(morde), len(sem_como), ", ".join(sem_como)) if morde
                 else "a de mais area ja cumpre em todas, o criterio perdeu o sentido"))

    # TORTAS. As fotos da espalhada saem com os angulos do ensaio de 10 de setembro, os de
    # POSICOES do teste_estilos.py, pela ordem, e chegam assim ao desenho. Ninguem o exigia:
    # pousadas direitas passavam todos os testes.
    pronto = _monte_de_cores("colagem", [4 / 3.0] * 5, estilo="espalhada")
    if [f["angulo"] for f in pronto["fotos"]] != angulos:
        tortas.append("pelo preparar: angulos %s" % [f["angulo"] for f in pronto["fotos"]])
    verifica("colagem espalhada: tortas, com os angulos do ensaio",
             not tortas and tuple(render.COLAGEM_ANGULOS) == (-3.5, 2.5, 2.0, -2.0, 4.0),
             resumo(tortas) if tortas else "angulos %s" % (tuple(render.COLAGEM_ANGULOS),))

    # SO CONTA O AFASTAMENTO QUE ASSENTA. Um afastamento que ao fim de dez voltas ainda
    # empurrava nao tem a garantia do miolo, e numa revisao trocou-se o teste por um "ou
    # True" sem nenhum teste falhar: as formas medidas escolhiam por acaso uma que assentava.
    # Aqui obriga-se: o colagem_afastar so diz que assentou numa chamada, e tem de ser essa
    # a que sai; se nunca diz, sai a colagem em filas.
    aspetos = [4 / 3.0] * 4
    original = render.colagem_afastar
    chamadas, aceite = [], []

    def so_uma(fotos, focos, quadro):
        assenta = original(fotos, focos, quadro)
        chamadas.append(fotos)
        if assenta and not aceite and len(chamadas) >= 40:
            aceite.append(fotos)
            return True
        return False

    def nunca(fotos, focos, quadro):
        original(fotos, focos, quadro)
        return False
    try:
        render.colagem_afastar = so_uma
        uma = render.colagem_espalhada(aspetos, None, None)
        render.colagem_afastar = nunca
        nenhuma = render.colagem_espalhada(aspetos, None, None)
    finally:
        render.colagem_afastar = original
    filas = render.colagem_disposicao(aspetos, None, None)
    verifica("colagem espalhada: so sai um afastamento que assentou",
             bool(aceite) and uma is aceite[0] and nenhuma == filas,
             "com um so assente sai %s; sem nenhum sai %s" % (
                 "esse" if aceite and uma is aceite[0] else "outro",
                 "a das filas" if nenhuma == filas else "uma espalhada que nao assentou"))

    # PARECIDA COM O ENSAIO. Com cinco 4:3 sem legenda os centros tem de ser os do ensaio
    # de 10 de setembro, POSICOES do teste_estilos.py, medidos a partir do meio do conjunto
    # e em lados da primeira foto. A escolha da mais aberta e o que os guarda: a menos
    # aberta empurra mais e afasta-os 0,10; a mais aberta fica a 0,03.
    ensaio = [(540, 330, 760), (1330, 300, 660), (560, 800, 600), (1180, 760, 540), (1610, 640, 400)]

    def normalizados(g):
        mx, my = sum(x[0] for x in g) / len(g), sum(x[1] for x in g) / len(g)
        lado = math.sqrt(g[0][2] * g[0][3])
        return [((x[0] - mx) / lado, (x[1] - my) / lado) for x in g]
    esperado = normalizados([(x, y, w, w * 3 / 4.0) for x, y, w in ensaio])
    obtido = normalizados(render.colagem_espalhada([4 / 3.0] * 5, None, None))
    desvio = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(esperado, obtido))
    verifica("colagem espalhada: cinco 4:3 pousam como no ensaio", desvio <= 0.07,
             "centros a %.2f lados da primeira dos do ensaio" % desvio)


def teste_pilha_leque():
    """Na pilha em leque cada foto de baixo fica com pelo menos 20% a vista no fim, e a de cima inteira.

    O PEDIDO, decisao 068: no monte as de baixo ficam quase todas tapadas, e o Tiago quis a
    opcao em que as de baixo espreitam sempre. Mede-se no ultimo fotograma desenhado, pela
    cor de cada foto, e nao pela grelha com que a disposicao se escolhe: se as duas contas
    se enganassem da mesma maneira, o teste nao via. Para o criterio nao passar por nao medir
    nada, confirma-se que no monte de oito ha fotos abaixo dos 20%.
    """
    import render
    problemas, casos, monte, tortas = [], 0, [], []
    for n in (2, 3, 5, 8):
        formas = sorted(_formas_monte(n).items())
        if n == 8:
            formas.append(("16:9 e 2:3", [(16 / 9.0, 2 / 3.0)[k % 2] for k in range(n)]))
        for forma, aspetos in formas:
            for texto in ("", "Verao de 2014\nParis com os amigos"):
                casos += 1
                dur = 2.6 + 0.85 * n
                fim = dur - 1.0 / render.FPS
                pronto = _monte_de_cores("pilha", aspetos, texto, estilo="leque")
                if [f["angulo"] for f in pronto["fotos"]] != [render.PILHA_ANGULOS[k % len(render.PILHA_ANGULOS)] for k in range(n)]:
                    tortas.append("%d %s%s: angulos %s" % (n, forma, " com legenda" if texto else "",
                                                           [f["angulo"] for f in pronto["fotos"]]))
                tela = render.desenhar(pronto, fim, dur)
                _, zoom = render.poses_monte(pronto, fim, dur)
                for k in range(n):
                    w, h = pronto["fotos"][k]["tamanho"]
                    if k == n - 1:
                        ve = _visivel(tela, CORES_MONTE[k]) / ((w * zoom - 4) * (h * zoom - 4))
                        exige = 0.97
                    else:
                        ve = _visivel(tela, CORES_MONTE[k]) / (w * zoom * h * zoom)
                        exige = render.PILHA_LEQUE_VE
                    if ve < exige:
                        problemas.append("%d %s%s: foto %d com %.0f%% a vista no fim, exige-se %.0f%%"
                                         % (n, forma, " com legenda" if texto else "", k + 1, 100 * ve, 100 * exige))
                if n == 8 and not texto and forma == "deitadas":
                    tapado = _monte_de_cores("pilha", aspetos, estilo="monte")
                    tela = render.desenhar(tapado, fim, dur)
                    _, zoom = render.poses_monte(tapado, fim, dur)
                    monte = [k + 1 for k in range(n - 1) if _visivel(tela, CORES_MONTE[k])
                             < 0.20 * tapado["fotos"][k]["tamanho"][0] * tapado["fotos"][k]["tamanho"][1] * zoom * zoom]
    verifica("pilha em leque: as de baixo espreitam, a de cima inteira", not problemas and monte
             and render.PILHA_LEQUE_VE >= 0.20,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else ("%d leques; no monte de 8 ficam abaixo de 20%% as fotos %s" % (casos, monte)
                                if monte else "no monte ninguem fica tapado, o criterio perdeu o sentido"))

    # TORTAS. O leque tem os angulos do monte, que sao os do ensaio de 10 de setembro, pela
    # ordem de chegada. Ninguem o exigia: um leque direito passava a parte a vista na mesma.
    verifica("pilha em leque: tortas, com os angulos do ensaio",
             not tortas and tuple(render.PILHA_ANGULOS) == (-9, 6, -4, 11, -7, 3, -12, 8),
             ("; ".join(tortas[:3]) + (" (+%d)" % (len(tortas) - 3) if len(tortas) > 3 else ""))
             if tortas else "angulos %s em %d leques" % (tuple(render.PILHA_ANGULOS), casos))

    # O TAMANHO. O leque de oito deitadas era uma tira fina a meio do ecra, com fotos de 13%;
    # com o desvio de cima para baixo e a tira mais estreita que chega ficam com 17 a 18%. A
    # revisao de 15 de setembro desfez as duas coisas sem nenhum teste falhar, porque so se
    # media a parte a vista. Exige-se 15% a cada uma, e que o desvio escolhido seja o que da
    # mais area: experimenta-se cada um sozinho e nenhum pode dar mais.
    H, V, W, T = 4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0
    oito = render.pilha_leque([H] * 8)
    menor = min(f[2] * f[3] for f in oito) / float(render.L * render.A)
    livre = render.faixa_texto("Verao de 2014\nParis com os amigos")[1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * render.A
    sobes, perde = render.PILHA_LEQUE_SOBES, []
    try:
        for aspetos in ([H] * 8, [(H, V, W, T)[k % 4] for k in range(8)], [H] * 5, [V] * 5):
            for legenda in (None, livre):
                render.PILHA_LEQUE_SOBES = sobes
                area = sum(f[2] * f[3] for f in render.pilha_leque(aspetos, legenda))
                for sobe in sobes:
                    render.PILHA_LEQUE_SOBES = (sobe,)
                    so = sum(f[2] * f[3] for f in render.pilha_leque(aspetos, legenda))
                    if so > area + 1.0:
                        perde.append("%d fotos%s: com o desvio %.3f dava %.1f%% e ficou %.1f%%" % (
                            len(aspetos), " com legenda" if legenda else "", sobe,
                            100 * so / (render.L * render.A), 100 * area / (render.L * render.A)))
    finally:
        render.PILHA_LEQUE_SOBES = sobes
    verifica("pilha em leque: fotos que se leem, pelo desvio de mais area", menor >= 0.15 and not perde,
             "; ".join(perde) if perde else "no leque de 8 deitadas a mais pequena com %.1f%% do ecra" % (100 * menor))

    # DE FORA PARA DENTRO. A primeira no extremo esquerdo, a segunda no direito e a de cima
    # entre as outras: e o que deixa a tira de fora de cada uma a vista. E nunca abre menos
    # do que o monte: com uma deitada por baixo de uma vertical a tira zero ja chegava, e as
    # duas ficavam no mesmo x, so a subir e a descer, mais fechadas do que no monte.
    fora = []
    for aspetos in ([H] * 5, [V] * 8, [(H, V, W, T)[k % 4] for k in range(8)]):
        xs = [f["centro"][0] for f in _monte_de_cores("pilha", aspetos, estilo="leque")["fotos"]]
        if not (xs[0] == min(xs) and xs[1] == max(xs) and min(xs[:-1]) < xs[-1] < max(xs[:-1])):
            fora.append("%d fotos com os centros em %s" % (len(aspetos), [int(x) for x in xs]))
    for aspetos in ([H, V], [W, T]):
        fotos = _monte_de_cores("pilha", aspetos, estilo="leque")["fotos"]
        abre = abs(fotos[1]["centro"][0] - fotos[0]["centro"][0])
        if abre < 0.04 * render.L:
            fora.append("duas fotos %.2f e %.2f a %d px uma da outra" % (aspetos[0], aspetos[1], abre))
    verifica("pilha em leque: abre de fora para dentro", not fora,
             "; ".join(fora) if fora else "a de cima entre as outras, e duas a abrir como o monte")


# As disposicoes de omissao ANTES da decisao 068, tiradas do render de entao a duas casas:
# (tipo, aspetos, focos, com legenda "Amigos", [cx, cy, largura, altura, angulo] de cada foto)
_H, _V, _W, _T = 4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0
OMISSAO_ANTES = [
    ("colagem", [_H, _V, _W, _T], [None, (0.1, 0.97), None, None], True,
     [(360.93, 487.40, 500.75, 375.56, -3.50), (778.35, 461.59, 281.67, 375.56, 2.50),
      (1240.50, 490.48, 667.67, 375.56, 2.00), (1688.92, 465.56, 250.38, 375.56, -2.00)]),
    ("colagem", [_W, _T, _T, _W, _V], None, False,
     [(784.83, 354.26, 882.87, 496.61, -3.50), (1395.41, 329.69, 331.08, 496.61, 2.50),
      (457.67, 798.31, 270.32, 405.48, 2.00), (961.44, 788.64, 720.86, 405.48, -2.00),
      (1438.46, 771.12, 304.11, 405.48, 4.00)]),
    ("colagem", [_V, _V, _V], None, True,
     [(413.87, 489.22, 562.05, 749.40, -3.50), (984.84, 464.14, 562.05, 749.40, 2.50),
      (1515.80, 492.55, 562.05, 749.40, 2.00)]),
    ("pilha", [_H, _V, _W, _T, _H, _V, _W, _T], None, True,
     [(980.45, 483.71, 900.83, 675.62, -9.00), (1067.69, 416.05, 506.72, 675.62, 6.00),
      (957.97, 416.70, 938.37, 527.83, -4.00), (899.01, 483.70, 450.42, 675.62, 11.00),
      (1023.92, 415.40, 900.83, 675.62, -7.00), (1050.70, 417.36, 506.72, 675.62, 3.00),
      (918.88, 483.68, 938.37, 527.83, -12.00), (926.07, 414.75, 450.42, 675.62, 8.00)]),
    ("pilha", [_H, _H, _H], None, False,
     [(923.02, 563.59, 921.60, 691.20, -9.00), (1012.27, 494.36, 921.60, 691.20, 6.00),
      (900.02, 495.03, 921.60, 691.20, -4.00)]),
]


def teste_estilos_de_omissao_iguais_a_antes():
    """A colagem em filas e a pilha em monte pousam onde pousavam antes dos estilos, e o tratamento antigo da o mesmo.

    O PEDIDO, decisao 068: sem estilo, ou com um valor desconhecido, fica a omissao, e as
    montagens ja feitas nao mudam. As disposicoes de antes estao escritas em OMISSAO_ANTES,
    tiradas do render de entao, e nao lidas do render de agora. E o que vem na coluna
    tratamento, vazio, o "fiel" das montagens antigas, o nome da omissao ou um valor
    desconhecido, tem de dar o mesmo fotograma byte a byte pelo preparar do render. Para a
    igualdade nao ser por o estilo nao chegar a lado nenhum, a espalhada e o leque tem de
    dar outro fotograma.
    """
    import tempfile
    import render
    livre = render.faixa_texto("Amigos")[1].getbbox()[1] - render.MONTE_LEGENDA_FOLGA * render.A
    problemas = []
    for tipo, aspetos, focos, legenda, antes in OMISSAO_ANTES:
        if tipo == "colagem":
            agora = render.colagem_disposicao(aspetos, focos, livre if legenda else None)
        else:
            agora = render.pilha_disposicao(aspetos, livre if legenda else None)
        pior = max(abs(a - b) for fa, fb in zip(antes, agora) for a, b in zip(fa, fb)) if len(agora) == len(antes) else 1e9
        if pior > 0.006:
            problemas.append("%s de %d%s: disposicao diferente da de antes em %.2f px"
                             % (tipo, len(aspetos), " com legenda" if legenda else "", pior))

    pasta = tempfile.mkdtemp(prefix="teste_omissao_")
    for tipo, aspetos, novo in (("colagem", [_H, _V, _W, _T], "espalhada"), ("pilha", [_H, _V, _W, _T, _H, _V], "leque")):
        caminhos = []
        for k, a in enumerate(aspetos):
            caminho = os.path.join(pasta, "%s%d.png" % (tipo, k))
            Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k]).save(caminho)
            caminhos.append(caminho)
        dur = 3 + 1.6 * len(aspetos) if tipo == "colagem" else 2.6 + 0.85 * len(aspetos)
        quadros = {}
        # " espalhada " e " leque " tem de dar o fotograma do estilo: com " filas " so nao se
        # via se os espacos eram tirados, porque um valor desconhecido tambem da a omissao.
        for tratamento in (None, "", "fiel", " %s " % render.ESTILOS_MONTE[tipo][0], "xpto", novo, " %s " % novo):
            clip = {"tipo": tipo, "texto_ecra": "Amigos", "fonte_imagem": "|0.1000,0.9700",
                    "ficheiro": "", "id": "", "transicao_s": "0.7", "_caminhos": caminhos}
            if tratamento is not None:
                clip["tratamento"] = tratamento
            pronto = render.preparar(clip, {})
            quadros[tratamento] = [render.desenhar(pronto, t, dur).tobytes() for t in (1.0, dur / 2.0, dur - 0.04)]
        diferentes = [repr(t) for t in quadros if novo not in (t or "") and quadros[t] != quadros[None]]
        if diferentes:
            problemas.append("%s: o tratamento %s nao da o fotograma da omissao" % (tipo, ", ".join(diferentes)))
        if quadros[novo] == quadros[None]:
            problemas.append("%s: %s da o mesmo fotograma da omissao, o estilo nao chega ao desenho" % (tipo, novo))
        if quadros[" %s " % novo] != quadros[novo]:
            problemas.append("%s: ' %s ' com espacos nao da o fotograma de %s" % (tipo, novo, novo))
    verifica("colagem e pilha: a omissao igual a antes dos estilos", not problemas,
             "; ".join(problemas) if problemas else
             "%d disposicoes a duas casas; vazio, fiel, omissao e desconhecido ao byte" % len(OMISSAO_ANTES))


# As disposicoes de ANTES de 17 de setembro, ao byte: md5 do float.hex de cada numero de
# [cx, cy, largura, altura, angulo], por estilo, forma e legenda, com n de 2 a 5 na colagem e de
# 2 a 8 na pilha, seguidos. Tiradas da copia do render de antes desta ronda
# (scratchpad grupos/antes/render.py) pelo grupos/corretor1/literais.py, que confirmou o render
# de agora igual. "com legenda" e livre_ate = 830 pixeis.
FORMAS_DE_ANTES = {
    "4:3": [4 / 3.0] * 8,
    "3:4": [3 / 4.0] * 8,
    "misturadas": [4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0, 1.0, 4 / 3.0, 3 / 4.0, 2.2],
    "panoramicas": [2.6] * 8,
}
FOCOS_DE_ANTES = {
    "misturadas com focos nos cantos": ("misturadas", [(0.05, 0.05), (0.95, 0.95), (0.05, 0.95), (0.95, 0.05), (0.5, 0.5)]),
    "4:3 com focos aos lados": ("4:3", [(0.9, 0.5), (0.1, 0.5), (0.9, 0.5), (0.1, 0.5), (0.9, 0.5)]),
}
DISPOSICOES_DE_ANTES = {
    "filas|4:3|sem legenda": "afa5d8538433a8dcfe1f4f57e3bd69eb",
    "filas|4:3|com legenda": "dad6a443eca290019d91bab8284c5be4",
    "filas|3:4|sem legenda": "c8ed3772224d10a3346e6c3ff9acbc32",
    "filas|3:4|com legenda": "9562960aff5dda0e53d9f6ddd1eef2c9",
    "filas|misturadas|sem legenda": "35237673140d77dbc06f8f2224c39295",
    "filas|misturadas|com legenda": "367033713e06057622b8acbdfbcb15e1",
    "filas|panoramicas|sem legenda": "a1223c7fcb792eba646b27b69dec5324",
    "filas|panoramicas|com legenda": "240d9a568e2703dfc5befb40fdfd2ddb",
    "filas|misturadas com focos nos cantos|sem legenda": "727b05b4197d40bd9c1132ac00914354",
    "filas|misturadas com focos nos cantos|com legenda": "223098c3dc138ff556735c2af9251360",
    "filas|4:3 com focos aos lados|sem legenda": "7bf7f09a98ccabe4a874e5a596ad0212",
    "filas|4:3 com focos aos lados|com legenda": "7a2ad6b07189b98dd22406a4a98a7bb2",
    "espalhada|4:3|sem legenda": "e490a3746f728bca170b6d09f82adf99",
    "espalhada|4:3|com legenda": "fbce0769c034a600d420972d372f8c16",
    "espalhada|3:4|sem legenda": "2873cdb9f9c88f2146df23f491d0873e",
    "espalhada|3:4|com legenda": "2cce88ed06a13eaa172f42379227913b",
    "espalhada|misturadas|sem legenda": "2edc4eef63f0dba6fbdf6958a5fbc18e",
    "espalhada|misturadas|com legenda": "8403d241c067b6fab714080c54ead80c",
    "espalhada|panoramicas|sem legenda": "e1321412b7b78c4fc452a4f93c50a32a",
    "espalhada|panoramicas|com legenda": "52fbd6f00937ed09bfba5ee61e27d47d",
    "espalhada|misturadas com focos nos cantos|sem legenda": "a1c6a4763667e76c6d379413a57a0c2a",
    "espalhada|misturadas com focos nos cantos|com legenda": "939d95a925714043be82b11bcd0dab00",
    "espalhada|4:3 com focos aos lados|sem legenda": "7d81a5881061166dae310f17e1cee6de",
    "espalhada|4:3 com focos aos lados|com legenda": "08d058465b6c82a868ab2d8787fcfac7",
    "monte|4:3|sem legenda": "7ad5e1ba00a90d5cd46775cf6118d868",
    "monte|4:3|com legenda": "7610d01062a4e63f34a91245e2f6ec44",
    "monte|3:4|sem legenda": "b3446bd14cb681540836667fb7a23a68",
    "monte|3:4|com legenda": "4b9adcc63f6eef59c1538c6702a65d4a",
    "monte|misturadas|sem legenda": "0eeff7a4424d47d5f12f05c09d3f07fe",
    "monte|misturadas|com legenda": "85bd0016f9beab6d22a052d56524d4cf",
    "monte|panoramicas|sem legenda": "5c3ad20d59294808cb78e980cfade0a2",
    "monte|panoramicas|com legenda": "4175900bb34160137279fb4500c8d075",
    "leque|4:3|sem legenda": "520337276feca569ed073fbd58b0bc8c",
    "leque|4:3|com legenda": "0b8f39cdb882d5f73de6f793a83d7a4f",
    "leque|3:4|sem legenda": "6fea75f1ed489ad77bad5d5464f3dadf",
    "leque|3:4|com legenda": "04e9d74d443a0c8ed08a470b3497372f",
    "leque|misturadas|sem legenda": "6ea37bae41fc0700c782be4ff1fa488e",
    "leque|misturadas|com legenda": "368cd3ab46bf93cb4cf6b5633f9c7963",
    "leque|panoramicas|sem legenda": "9e8d39c9ae763782ce53103e57ff7ace",
    "leque|panoramicas|com legenda": "94d3080593a5098e405585e4966db641",
}


def teste_disposicoes_de_antes_ao_byte():
    """A colagem de 2 a 5 e a pilha de 2 a 8 pousam ao byte onde pousavam antes de 17 de setembro, nos quatro estilos.

    O PEDIDO, do Tiago a 17 de setembro: mais fotos em cada tratamento, sem mudar as colagens
    e pilhas que ele ja tem. O DEFEITO QUE ISTO APANHA: a revisao dessa ronda mexeu num centro
    da espalhada de 2, 4 e 5 fotos, num tamanho do ensaio, e desceu o COLAGEM_POUCAS de 5 para
    4 (a colagem em filas de 5 passava as filas equilibradas). Cada mutacao mudava as
    disposicoes e a suite inteira passava: da espalhada so a de 3 tinha assinatura, o teste das
    cinco 4:3 aceitava 0,07 de desvio, e as filas so estavam presas do lado de cima.

    As assinaturas estao escritas em DISPOSICOES_DE_ANTES, tiradas da copia do render de
    antes, e nao lidas do render de agora. E a colagem em filas de 2 a 5 experimenta todas as
    particoes de ate 3 filas de ate 5, pela ordem de itertools.product, que e a que desempata.
    """
    import hashlib
    import itertools
    import render
    problemas = []

    def assinatura(disposicoes):
        texto = "|".join(";".join(",".join(v.hex() if isinstance(v, float) else repr(v) for v in l) for l in lugares)
                         for lugares in disposicoes)
        return hashlib.md5(texto.encode("ascii")).hexdigest()

    medidas = 0
    for estilo, ns in (("filas", range(2, 6)), ("espalhada", range(2, 6)), ("monte", range(2, 9)), ("leque", range(2, 9))):
        formas = [(nome, aspetos, None) for nome, aspetos in FORMAS_DE_ANTES.items()]
        if estilo in ("filas", "espalhada"):
            formas += [(nome, FORMAS_DE_ANTES[base], focos) for nome, (base, focos) in FOCOS_DE_ANTES.items()]
        for forma, aspetos, focos in formas:
            for legenda, livre in (("sem legenda", None), ("com legenda", 830.0)):
                disposicoes = []
                for n in ns:
                    f = focos[:n] if focos else None
                    if estilo == "filas":
                        disposicoes.append(render.colagem_disposicao(list(aspetos[:n]), f, livre))
                    elif estilo == "espalhada":
                        disposicoes.append(render.colagem_espalhada(list(aspetos[:n]), f, livre))
                    elif estilo == "monte":
                        disposicoes.append(render.pilha_disposicao(list(aspetos[:n]), livre))
                    else:
                        disposicoes.append(render.pilha_leque(list(aspetos[:n]), livre))
                    medidas += 1
                chave = "%s|%s|%s" % (estilo, forma, legenda)
                if assinatura(disposicoes) != DISPOSICOES_DE_ANTES.get(chave):
                    problemas.append(chave)
    verifica("colagem de 2 a 5 e pilha de 2 a 8: onde pousam, ao byte como antes", not problemas,
             ("mudaram: " + "; ".join(problemas[:4]) + (" (+%d)" % (len(problemas) - 4) if len(problemas) > 4 else ""))
             if problemas else "%d disposicoes em %d assinaturas, 4 estilos, com e sem legenda" % (medidas, len(DISPOSICOES_DE_ANTES)))

    erradas = []
    for n in range(2, 6):
        esperadas = []
        for cortes in itertools.product((False, True), repeat=n - 1):
            linhas = [[0]]
            for i, corta in enumerate(cortes, 1):
                if corta:
                    linhas.append([i])
                else:
                    linhas[-1].append(i)
            if len(linhas) <= 3 and max(len(l) for l in linhas) <= 5:
                esperadas.append(linhas)
        if list(render.colagem_particoes(n)) != esperadas or len(esperadas) != {2: 2, 3: 4, 4: 7, 5: 11}[n]:
            erradas.append("%d fotos: %d particoes" % (n, len(list(render.colagem_particoes(n)))))
    verifica("colagem em filas de 2 a 5: todas as particoes de ate 3 filas, pela ordem de antes", not erradas,
             "; ".join(erradas) if erradas else "2, 4, 7 e 11 particoes")


def _bloco_do_editor(html, inicio, problemas):
    """Um bloco do script da Mesa, da declaracao ate a chaveta que a fecha, para correr no node.

    O marcador tem de aparecer UMA SO VEZ, senao nao se corta: ja se apagou meio
    editor_base.html por recortar entre um comentario que existia duas vezes.
    """
    if html.count(inicio) != 1:
        problemas.append("o marcador %r aparece %d vezes no editor_base.html" % (inicio, html.count(inicio)))
        return ""
    i = html.index(inicio)
    prof = 0
    for p in range(html.index("{", i), len(html)):
        if html[p] == "{":
            prof += 1
        elif html[p] == "}":
            prof -= 1
            if prof == 0:
                return html[i:p + 1] + (";" if html[p + 1:p + 2] == ";" else "")
    problemas.append("o bloco de %r nao fecha" % inicio)
    return ""


def _regiao_do_editor(html, inicio, fim, problemas):
    """O pedaco do script da Mesa entre dois marcadores, para correr no node.

    O _bloco_do_editor() so sabe cortar uma declaracao com chavetas, e as regras do validador
    sao listas, expressoes regulares e numeros. Por isso vao marcadas por comentario, e o corte
    e entre os dois. CADA MARCADOR TEM DE APARECER UMA SO VEZ, que e a regra que custou metade
    do editor_base.html a 12 de setembro.
    """
    for m in (inicio, fim):
        if html.count(m) != 1:
            problemas.append("o marcador %r aparece %d vezes no editor_base.html" % (m, html.count(m)))
            return ""
    i, j = html.index(inicio), html.index(fim)
    if j <= i:
        problemas.append("o marcador %r vem antes de %r" % (fim, inicio))
        return ""
    return html[i + len(inicio):j]


def _numero_do_editor(html, nome, problemas):
    """O valor de um `var <nome> = <numero>;` da Mesa, lido do ficheiro e nao escrito aqui.

    Escrever o numero neste ficheiro fazia dele uma segunda copia, e a suite continuava verde
    com a Mesa a dizer outra coisa: e o defeito das tres copias da regra do upscaling.
    """
    m = re.search(r"var\s+%s\s*=\s*(-?\d+(?:\.\d+)?)\s*;" % re.escape(nome), html)
    if not m:
        problemas.append("nao encontrei `var %s = <numero>;` no editor_base.html" % nome)
        return None
    return float(m.group(1))


def _js_s1(x):
    """O s1() da Mesa em Python: uma casa decimal, arredondada como o Math.round, com virgula."""
    v = math.floor(x * 10 + 0.5) / 10.0
    return (("%d" % v) if float(v).is_integer() else repr(v)).replace(".", ",")


def teste_mesa_no_sitio_do_clip():
    """As contas da Mesa que dependem do sitio do clip na montagem dao o mesmo que o render.

    O PEDIDO, do Tiago a 17 de setembro: a duracao repartida pelas fotos, e poder tirar uma foto
    de um grupo. A nota "cerca de X s por foto, a ultima o dobro" e a duracao que o Reduzir
    escreve saem de agendaDoClip(), que junta a agenda aos encadeados DO SITIO do clip: zero a
    entrar no primeiro clip do corpo, o fade a preto de 2,5 s a sair do ultimo.

    O DEFEITO QUE ISTO APANHA: nada media essas funcoes. Tres revisoes diferentes passavam a
    suite inteira, medidas por mutacao: agendaDoClip sem os encadeados (numa pilha de 8 em 19 s
    no fim do filme a Mesa dizia 2,1 s por foto e o render dava 1,8 s, e o Reduzir escrevia uma
    duracao que mudava o tempo por foto em vez de o manter), o Reduzir a tirar duas vezes em vez
    de uma, e o ultimo clip a deixar de contar o fade. Em qualquer delas o Tiago decidia a
    duracao por um numero que o video nao tem.

    Corre no node, sobre montagens de ensaio com o grupo no primeiro clip do corpo depois de
    videos, no meio, no ultimo clip e antes de um video no fim da lista. O esperado vem do
    render: encadeados_do_corpo(), vez_do_monte() e duracao_minima_monte(). Tambem prende o
    legendaDaSolta(), que e quem faz a legenda do grupo passar para a foto que fica quando o
    Reduzir o deixa com uma so: o c.x nao era lido e a legenda perdia-se sem aviso. Sem node,
    diz-se e nao conta.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import render
    node = shutil.which("node")
    if not node:
        salta("Mesa no sitio do clip: as contas do render", "sem node neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []
    marcas = ["var GRUPOS = ", "var LADO_N = ", "var NOMES_LADO = ", "function layoutsPara(", "function duracaoLado(",
              "var MONTE = ", "var LADO_TEMPOS = ", "function clipsDoCorpo(", "function encadeadosDe(",
              # o encadeadosDe pergunta ao encadeadoDoClip, que precisa de saber ler um contador
              "function encadeadoDoClip(", "function contadoresSeguidos(", "function pontoDoContador(",
              "function lerContador(", "function eDataContador(", "function dataParaIso(", "function d2(",
              "function duracaoMinimaMonte(",
              "function duracaoMinimaGrupo(", "function agendaMonte(", "function agendaDeAntes(",
              "function agendaDoClip(", "function textoPorFoto(", "function porFotoApertada(",
              "function minimaArredondada(", "function s1(", "function nomeDoGrupo(", "function oGrupo(",
              "function doGrupo(", "function nomeDaFoto(", "function planoReduzir(", "function legendaDaSolta("]
    js = "var porId = {};\n" + "\n".join(_bloco_do_editor(html, m, problemas) for m in marcas)

    # OS SITIOS: o que muda e o par de encadeados que o render da ao clip. "primeiro" e o
    # primeiro do corpo, que entra sem encadeado porque os videos vao antes com corte seco;
    # "ultimo" sai com o fade a preto; "antes de video" tambem, porque um video posto a seguir
    # na lista sai no inicio do filme e nao ha mais nenhum clip de fotos depois.
    # "video no meio" e de 17 de setembro: um video a seguir ao grupo JA NAO SAI do corpo,
    # e o encadeado que conta a sair passa a ser o dele. A Mesa contava todos os videos como
    # estando fora do corpo e ia buscar o da foto seguinte, 0,9 s em vez de 0: dizia ao
    # Tiago que o grupo precisava de quase um segundo a mais do que precisa.
    sitios = {"primeiro": (["video"], []), "meio": (["foto"], ["foto"]),
              "ultimo": (["video", "foto"], []), "antes de video": (["foto"], ["video"]),
              "video no meio": (["video", "foto"], ["video", "foto"])}
    # O video do corpo nasce com encadeado 0 (e o que o botao «+ Vídeo» escreve), e e por
    # isso que ele se distingue da foto que vem a seguir.
    CROSS_DEPOIS = {"video": 0.0, "foto": 0.9}
    casos = []
    for sitio, (antes, depois) in sorted(sitios.items()):
        for tipo, ns in (("colagem", (2, 3, 7, 12)), ("pilha", (2, 9, 20)), ("lado", (2, 3, 4, 6))):
            for n in ns:
                for cc in (0.0, 0.35, 0.7, 2.5):
                    minima = render.duracao_minima_monte("pilha" if tipo == "lado" else tipo, n, cc, 0.7)
                    for d in (0.4, 0.3 * minima, minima - 0.1, minima, minima + 2.7, 2 * minima + 9.3):
                        clips = [{"t": t, "i": 1, "d": 4, "c": 0.4} for t in antes]
                        grupo = {"t": tipo, "fotos": list(range(100, 100 + n)),
                                 "d": math.floor(d * 10 + 0.5) / 10.0, "c": cc}
                        if tipo == "lado":
                            grupo["lay"] = {2: "2v", 3: "3v", 4: "4q", 6: "6g"}[n]
                        i = len(clips)
                        clips.append(grupo)
                        clips += [{"t": t, "i": 2, "d": 3, "c": CROSS_DEPOIS[t]} for t in depois]
                        casos.append({"clips": clips, "i": i, "k": n // 2, "sitio": sitio})
    # AS LEGENDAS DA FOTO QUE FICA, quando o Reduzir deixa o grupo com uma so foto.
    legendas = [
        # {x do grupo, xf}, j, x da original, o que tem de ficar
        ({"x": "Viagem a Roma 2019"}, ["", ""], 1, "", "Viagem a Roma 2019"),
        ({"x": "Viagem a Roma 2019"}, ["", "No Coliseu"], 1, "", "No Coliseu"),
        ({"x": ""}, ["", ""], 1, "Praia em 2007", "Praia em 2007"),
        ({"x": "Praia  em 2007\n"}, ["", ""], 0, "Praia em 2007", "Praia em 2007"),
        ({"x": "Viagem a Roma 2019"}, ["", ""], 0, "Praia em 2007", "Viagem a Roma 2019"),
        ({}, ["", ""], 0, "Praia em 2007", "Praia em 2007"),
        ({"x": "Viagem a Roma 2019"}, ["Viagem a Roma 2019", ""], 0, "", "Viagem a Roma 2019"),
    ]
    programa = js + "\nvar casos = %s, legendas = %s;\n" % (json.dumps(casos), json.dumps(legendas)) + """
process.stdout.write(JSON.stringify({
  r: casos.map(function(m){
    var v = {clips: m.clips}, c = m.clips[m.i];
    return {e: encadeadosDe(v, m.i), nota: textoPorFoto(v, c), aperto: porFotoApertada(v, c),
            plano: planoReduzir(v, c, m.k)};
  }),
  legendas: legendas.map(function(g){ return legendaDaSolta(g[0], g[1], g[2], g[3]); })
}));
"""
    pasta = tempfile.mkdtemp(prefix="teste_mesa_sitio_")
    caminho = os.path.join(pasta, "mesa_no_sitio.js")
    open(caminho, "w", encoding="utf-8").write(programa)
    saida = None
    if not problemas:
        r = subprocess.run([node, caminho], capture_output=True, text=True, encoding="utf-8", timeout=300)
        if r.returncode != 0:
            problemas.append("o node nao correu as contas da Mesa: %s" % r.stderr.strip()[:300])
        else:
            saida = json.loads(r.stdout)
    contas = {"notas": 0, "apertos": 0, "reduzir": 0, "presos na minima": 0, "abaixo da minima": 0,
              "soltas": 0, "lado": 0}
    if saida:
        for g, veio in zip(legendas, saida["legendas"]):
            if veio != g[4]:
                problemas.append("legendaDaSolta com x=%r e xf=%r deu %r, esperado %r" % (g[0].get("x"), g[1], veio, g[4]))
        for m, o in zip(casos, saida["r"]):
            clips, i, k = m["clips"], m["i"], m["k"]
            c = clips[i]
            n = len(c["fotos"])
            # O CORPO E O QUE O RENDER DIZ QUE E: o bloco inicial e so os videos que vem
            # antes de qualquer outro clip, e um video a meio fica ca dentro.
            inicio_do_filme, _resto = render.partir_em_fanfarra_e_corpo(
                [{"tipo": x["t"]} for x in clips])
            corpo = clips[len(inicio_do_filme):]
            entra, sai = render.encadeados_do_corpo([{"transicao_s": x["c"]} for x in corpo])[corpo.index(c)]
            nome = "%s de %d em %s s, %s (%.2f/%.2f)" % (c["t"], n, c["d"], m["sitio"], entra, sai)
            if abs(o["e"]["entra"] - entra) > 1e-12 or abs(o["e"]["sai"] - sai) > 1e-12:
                problemas.append("%s: encadeados da Mesa %s, do render %.2f/%.2f" % (nome, o["e"], entra, sai))
                continue
            plano = o["plano"]
            if c["t"] == "lado":
                contas["lado"] += 1
                if o["nota"] != "":
                    problemas.append("%s: nota no lado a lado %r, devia ser vazia" % (nome, o["nota"]))
                if n == 2 and not (plano.get("pode") and plano.get("solta")):
                    problemas.append("%s: com 2 fotos nao passa a solta: %s" % (nome, plano))
                if n == 6 and plano.get("pode") is not False:
                    problemas.append("%s: com 6 fotos o reduzir devia recusar (nao ha 5): %s" % (nome, plano))
                if n in (3, 4) and not (plano.get("pode") and plano.get("lay") == {3: "2v", 4: "3v"}[n]
                                        and abs(plano.get("d", -1) - (2.0 + 1.5 * (n - 1))) < 1e-9):
                    problemas.append("%s: plano do lado a lado %s" % (nome, plano))
                continue
            vez = render.vez_do_monte(n, c["d"], entra, sai)
            apertado = vez < render.MONTE_ENTRADA_MIN + render.MONTE_PAUSA - 1e-9
            minima = math.ceil(render.duracao_minima_monte(c["t"], n, entra, sai) * 10) / 10.0
            if apertado:
                contas["apertos"] += 1
                nota = "curta de mais para repartir pelas fotos: a mínima com estes encadeados é %s s" % _js_s1(minima)
            else:
                contas["notas"] += 1
                nota = "cerca de %s s por foto, a última o dobro" % _js_s1(vez)
            if o["nota"] != nota or bool(o["aperto"]) != apertado:
                problemas.append("%s: nota %r, esperada %r" % (nome, o["nota"], nota))
            if n == 2:
                contas["soltas"] += 1
                if not (plano.get("pode") and plano.get("solta")):
                    problemas.append("%s: com 2 fotos nao passa a solta: %s" % (nome, plano))
                continue
            contas["reduzir"] += 1
            # A DURACAO QUE O REDUZIR ESCREVE: desce UMA vez da agenda, arredondada a 0,1 s,
            # presa na minima com uma foto a menos, e nunca sobe.
            dmin = math.ceil(render.duracao_minima_monte(c["t"], n - 1, entra, sai) * 10) / 10.0
            esperado = max(0.2, math.floor((c["d"] - max(0.0, vez)) * 10 + 0.5) / 10.0, min(dmin, c["d"]))
            if not plano.get("pode") or abs(plano.get("d", -1) - esperado) > 1e-9:
                problemas.append("%s: reduzir da %s, esperado d = %.1f" % (nome, plano, esperado))
                continue
            if plano["d"] > c["d"] + 1e-9:
                problemas.append("%s: reduzir aumenta a duracao, de %s para %s" % (nome, c["d"], plano["d"]))
            # A NOTA DA JANELA. Sao tres casos e tem de se distinguir: a duracao desce; fica
            # presa na minima; ou ja estava abaixo dela, e ai dizer "a Mesa nao a encolhe abaixo
            # da minima" lia-se como se a duracao de agora fosse a minima.
            desce = abs(esperado - c["d"]) >= 0.05
            abaixo = c["d"] < dmin - 0.001
            texto = plano.get("texto", "")
            if desce:
                if "passa de" not in texto or "continua em" in texto:
                    problemas.append("%s: a duracao desce para %.1f e a janela diz %r" % (nome, esperado, texto))
            elif abaixo:
                contas["abaixo da minima"] += 1
                if "já está abaixo da mínima" not in texto or "não a encolhe abaixo disso" in texto:
                    problemas.append("%s: %s s ja esta abaixo da minima de %s s e a janela diz %r"
                                     % (nome, c["d"], dmin, texto))
            else:
                contas["presos na minima"] += 1
                if "não a encolhe abaixo disso" not in texto:
                    problemas.append("%s: presa na minima de %s s e a janela diz %r" % (nome, dmin, texto))
            desceu_uma_vez = abs(esperado - math.floor((c["d"] - vez) * 10 + 0.5) / 10.0) < 1e-9
            if desce and desceu_uma_vez and not apertado and esperado > 0.2:
                # QUANDO A DURACAO DESCE MESMO UMA VEZ (nao esta presa na minima com uma foto a
                # menos) o tempo por foto tem de se manter: so o arredondamento a 0,1 s o mexe
                nova = render.vez_do_monte(n - 1, esperado, entra, sai)
                if abs(nova - vez) > 0.05 / n + 1e-9:
                    problemas.append("%s: depois de reduzir a vez passa de %.3f para %.3f s" % (nome, vez, nova))
    verifica("Mesa no sitio do clip: encadeados, nota por foto e Reduzir", not problemas and saida is not None,
             "; ".join(problemas[:3]) if problemas else
             "%d montagens no node, %s, %d legendas" % (len(casos), ", ".join("%d %s" % (v, nome) for nome, v in sorted(contas.items())), len(legendas)))


def teste_agenda_da_mesa_igual_ao_render():
    """A replica da agenda na Mesa da os numeros do render, na colagem, na pilha e no lado a lado.

    O PEDIDO, do Tiago a 17 de setembro: a duracao de uma colagem ou pilha dividida pelas fotos,
    a ultima com o dobro. A Mesa repete a conta em JavaScript (agendaMonte, agendaDeAntes,
    temposLegendaGrupo, duracaoMinimaMonte e as constantes MONTE e LADO_TEMPOS): e dela que vem
    a nota "cerca de X s por foto, a ultima o dobro", a duracao do Reduzir e os avisos de texto
    curto. O DEFEITO QUE ISTO APANHA: a revisao dessa ronda trocou na agendaMonte da Mesa o
    /(n + 1) por /n e a suite passou; so um comparador fora dela, a correr no node, o via. A
    Mesa dizia um tempo por foto que o video nao tinha.

    Cada bloco tira-se do scripts/editor_base.html so depois de confirmar que o seu marcador
    aparece uma so vez, corre-se no node numa grelha (colagem de 2 a 12, pilha de 2 a 20, lado a
    lado de 2 a 6, duracoes com e sem aperto, encadeados de 0, 0,7 e 2,5 s) e compara-se com o
    render.agenda_monte, vez_do_monte, duracao_minima_monte e tempos_legenda_grupo. Sem node,
    diz-se e nao conta.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import render
    node = shutil.which("node")
    if not node:
        salta("Mesa e render: a mesma agenda", "sem node neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []

    js = "\n".join(_bloco_do_editor(html, m, problemas)
                   for m in ("var MONTE = ", "var LADO_TEMPOS = ", "function duracaoMinimaMonte(",
                             "function agendaMonte(", "function agendaDeAntes(", "function temposLegendaGrupo("))
    casos = []
    for tipo, maximo in (("colagem", 12), ("pilha", 20), ("lado", 6)):
        for n in range(2, maximo + 1):
            for ce, cs in ((0.0, 2.5), (0.7, 0.7), (2.5, 0.0), (0.7, 2.5)):
                minima = render.duracao_minima_monte("pilha" if tipo == "lado" else tipo, n, ce, cs)
                for d in (0.4, 0.3 * minima, 0.6 * minima, minima, minima + 2.7, 2 * minima + 9.3):
                    casos.append([tipo, n, round(d, 6), ce, cs])
    programa = js + """
var casos = %s;
console.log(JSON.stringify({
  monte: MONTE, lado: LADO_TEMPOS,
  r: casos.map(function(c){
    var tipo = c[0], n = c[1], d = c[2], ce = c[3], cs = c[4];
    var r = {tempos: temposLegendaGrupo(tipo, n, d, ce, cs)};
    if(tipo !== "lado"){
      var a = agendaMonte(n, d, MONTE.entrada[tipo], ce, cs);
      r.inicios = a.inicios; r.entrada = a.entrada; r.vez = a.vez;
      r.minimo = duracaoMinimaMonte(tipo, n, ce, cs);
    }
    return r;
  })
}));
""" % json.dumps(casos)
    pasta = tempfile.mkdtemp(prefix="teste_agenda_mesa_")
    caminho = os.path.join(pasta, "agenda_da_mesa.js")
    open(caminho, "w", encoding="utf-8").write(programa)
    saida = None
    if not problemas:
        r = subprocess.run([node, caminho], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            problemas.append("o node nao correu a agenda da Mesa: %s" % r.stderr.strip()[:300])
        else:
            saida = json.loads(r.stdout)
    difs, apertos = [], 0
    if saida:
        m, lado = saida["monte"], saida["lado"]
        constantes = {"atraso": render.MONTE_ATRASO, "pausa": render.MONTE_PAUSA, "folga": render.MONTE_FOLGA,
                      "entradaMin": render.MONTE_ENTRADA_MIN, "fracaoFim": render.MONTE_FRACAO_FIM,
                      "folgaMin": render.MONTE_FOLGA_MIN, "fimFade": render.FADE_FIM_IMAGEM}
        for nome, valor in constantes.items():
            if abs(m.get(nome, -1) - valor) > 1e-12:
                problemas.append("MONTE.%s na Mesa %s, no render %s" % (nome, m.get(nome), valor))
        if m["entrada"] != {"colagem": render.COLAGEM_ENTRADA, "pilha": render.PILHA_ENTRADA}:
            problemas.append("MONTE.entrada na Mesa %s" % m["entrada"])
        if (lado["atraso"], lado["intervalo"]) != (render.LADO_ATRASO, render.LADO_INTERVALO):
            problemas.append("LADO_TEMPOS na Mesa %s" % lado)

        def longe(a, b):
            return len(a) != len(b) or any(abs(x - y) > 1e-9 for x, y in zip(a, b))

        for (tipo, n, d, ce, cs), rj in zip(casos, saida["r"]):
            tp = render.tempos_legenda_grupo(tipo, n, d, ce, cs)
            mau = len(tp) != len(rj["tempos"]) or any(longe(a, b) for a, b in zip(tp, rj["tempos"]))
            if tipo != "lado":
                entrada = render.COLAGEM_ENTRADA if tipo == "colagem" else render.PILHA_ENTRADA
                inicios, ep = render.agenda_monte(n, d, entrada, cross_entra=ce, cross_sai=cs)
                vez = render.vez_do_monte(n, d, ce, cs)
                apertos += vez < render.MONTE_ENTRADA_MIN + render.MONTE_PAUSA
                mau = (mau or longe(inicios, rj["inicios"]) or abs(ep - rj["entrada"]) > 1e-9
                       or abs(max(0.0, vez) - rj["vez"]) > 1e-9
                       or abs(render.duracao_minima_monte(tipo, n, ce, cs) - rj["minimo"]) > 1e-9)
            if mau:
                difs.append("%s de %d em %.2f s, %.1f/%.1f" % (tipo, n, d, ce, cs))
    if difs:
        problemas.append("%d casos diferentes, por exemplo %s" % (len(difs), "; ".join(difs[:3])))
    verifica("Mesa e render: a mesma agenda, a mesma vez e a mesma minima", not problemas and saida is not None,
             "; ".join(problemas[:3]) if problemas else
             "%d casos no node, %d no aperto, constantes iguais" % (len(casos), apertos))


def teste_mesa_esconde_as_da_montagem():
    """A caixa "Esconder as que já estão nesta montagem" esconde exatamente as desta versao.

    O PEDIDO, do Tiago a 17 de setembro: "para evitar que fotos que ja estejam na montagem
    voltem a ser selecionadas, cria um filtro de checkbox que permita nao mostrar todas as
    fotos que ja estao na montagem".

    O DEFEITO QUE ISTO APANHA: o filtro nasceu sem teste nenhum, verificado so a mao no
    browser. Quatro revisoes diferentes passavam a suite inteira, medidas por mutacao:
      - o idsNaMontagem a correr todas as versoes em vez da aberta, e entao as fotos que ele
        poe na v1 desapareciam da biblioteca enquanto trabalha na v3;
      - o idsNaMontagem a contar so as fotos soltas, e entao as que estao dentro de uma
        colagem ou de uma pilha voltavam a aparecer, que e precisamente o que ele pediu para
        nao acontecer;
      - a caixa a filtrar ANTES dos outros filtros, e entao o contador "34 escondidas" dizia
        um numero que nao tem nada a ver com o que os outros filtros mostravam;
      - o tiraEscolhidasEscondidas sem a guarda do esconderUsadas, e entao com a caixa
        desligada uma foto deixava de estar escolhida sem ninguem lhe tocar.
    Em qualquer delas o Tiago escolhia fotos repetidas, que e o que a caixa existe para evitar.

    Corre no node. O idsNaMontagem, o fotosFiltradas, o tiraEscolhidasEscondidas, o
    chaveDeIds, o eGrupo, o versaoAtual e o pessoaPorId saem do editor_base.html pelo
    _bloco_do_editor, cada um so depois de se confirmar que o marcador aparece uma so vez. Do
    DOM so se finge o que o fotosFiltradas le, os cinco campos de filtro, e um campo novo que
    ele va ler estoira em vez de passar calado. Sem node, diz-se e nao conta.

    O que fica POR VERIFICAR AQUI: a pintura da grelha (pintaGrelha) e a nota "N escondidas"
    sao DOM e nao correm no node; veem-se a mao no browser, com o harness da Mesa.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    node = shutil.which("node")
    if not node:
        salta("Mesa: esconder as que ja estao na montagem", "sem node neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []
    marcas = ["function eGrupo(", "function versaoAtual(", "function pessoaPorId(",
              "function idsNaMontagem(", "function chaveDeIds(",
              "function tiraEscolhidasEscondidas(", "function fotosFiltradas("]
    blocos = "\n".join(_bloco_do_editor(html, m, problemas) for m in marcas)

    # AS FOTOS DE ENSAIO. O que o fotosFiltradas le de cada uma: id, ficheiro, legenda,
    # pessoas do nome, seccao, ano e se ela a usou.
    fotos = [{"id": "f%02d" % k, "f": "f%02d.jpg" % k, "l": "", "p": "",
              "s": "Bloco %d" % (1 + k % 3), "a": 2000 + k % 4, "usada": k % 2 == 0}
             for k in range(1, 13)]
    anos = {f["id"]: f["a"] for f in fotos}

    # A MONTAGEM DE ENSAIO. Na versao aberta ha de tudo: video (nao conta), foto solta, foto
    # solta por preencher (o i vazio nao pode virar uma chave), lado a lado, colagem, pilha, e
    # uma colagem sem a lista de fotos, que e o que um clip a meio de ser feito parece.
    va = {"id": "va", "clips": [
        {"t": "video", "i": "v1"},
        {"t": "foto", "i": "f01"},
        {"t": "foto", "i": ""},
        {"t": "lado", "fotos": ["f02", "f03"]},
        {"t": "colagem", "fotos": ["f04", "f05", "f06"]},
        {"t": "pilha", "fotos": ["f07"]},
        {"t": "colagem"}]}
    vb = {"id": "vb", "clips": [{"t": "foto", "i": "f09"}, {"t": "pilha", "fotos": ["f10", "f11"]}]}
    na_va = ["f01", "f02", "f03", "f04", "f05", "f06", "f07"]
    na_vb = ["f09", "f10", "f11"]
    todas = [f["id"] for f in fotos]

    def fora(ids, mais=()):
        return [i for i in todas if i not in ids and i not in mais]

    # CADA CASO: filtros, versao aberta, caixa ligada, escolhidas antes.
    # Esperado: a lista, quantas a caixa escondeu, o que sobra de escolhido e quantas tirou.
    de_2001 = [i for i in todas if anos[i] == 2001]
    casos = [
        # a caixa desligada nao mexe em nada
        ({}, "va", False, {}, todas, 0, {}, 0),
        # ligada, esconde as sete da versao aberta e nenhuma das outras
        ({}, "va", True, {}, fora(na_va), len(na_va), {}, 0),
        # a versao aberta e a outra: as da va voltam e escondem-se as da vb
        ({}, "vb", True, {}, fora(na_vb), len(na_vb), {}, 0),
        # o contador conta so o que os outros filtros mostravam, por isso o ano manda primeiro
        ({"fAno": "2001"}, "va", True, {}, [i for i in de_2001 if i not in na_va],
         len([i for i in de_2001 if i in na_va]), {}, 0),
        # uma busca que so apanha fotos de fora da montagem: o contador fica a zero
        ({"busca": "f09"}, "va", True, {}, ["f09"], 0, {}, 0),
        # a busca pelo nome do ficheiro tambem manda primeiro
        ({"busca": "f01"}, "va", True, {}, [], 1, {}, 0),
        # uma escolhida que a caixa esconde deixa de estar escolhida; as outras ficam
        ({}, "va", True, {"f01": 1, "f06": 1, "f08": 1}, fora(na_va), len(na_va), {"f08": 1}, 2),
        # com a caixa desligada ninguem lhe toca
        ({}, "va", False, {"f01": 1, "f08": 1}, todas, 0, {"f01": 1, "f08": 1}, 0),
    ]
    programa = """
'use strict';
/* do DOM finge-se so o que o fotosFiltradas le: um campo novo estoira em vez de passar calado */
var filtros = {};
var document = {getElementById: function(id){
  if(!(id in filtros)) throw new Error("campo do DOM que o teste nao finge: " + id);
  return {value: filtros[id]};
}};
var D = {fotos: %s};
var est = {versoes: %s, atual: "va", tags: {}, pessoas: [], excluidas: {}};
var sel = {}, marcadasNestaVista = {};
var esconderUsadas = false, escondidasNaVista = 0, chaveUsadasLista = null, chaveUsadasPintada = null;
%s
var casos = %s;
console.log(JSON.stringify(casos.map(function(c){
  filtros = {busca: "", fSeccao: "", fPessoa: "", fAno: "", fUso: ""};
  Object.keys(c[0]).forEach(function(k){ filtros[k] = c[0][k]; });
  est.atual = c[1];
  esconderUsadas = c[2];
  sel = {}; Object.keys(c[3]).forEach(function(k){ sel[k] = 1; });
  var tiradas = tiraEscolhidasEscondidas();
  var lista = fotosFiltradas();
  return {lista: lista.map(function(f){ return f.id; }), escondidas: escondidasNaVista,
          sel: Object.keys(sel).sort(), tiradas: tiradas, chave: chaveUsadasLista,
          ids: Object.keys(idsNaMontagem(versaoAtual())).sort(),
          vazia: Object.keys(idsNaMontagem(null)).length};
})));
""" % (json.dumps(fotos), json.dumps([va, vb]), blocos, json.dumps(casos))
    pasta = tempfile.mkdtemp(prefix="teste_esconder_usadas_")
    caminho = os.path.join(pasta, "esconder_usadas.js")
    open(caminho, "w", encoding="utf-8").write(programa)
    saida = None
    if not problemas:
        r = subprocess.run([node, caminho], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            problemas.append("o node nao correu o filtro da Mesa: %s" % r.stderr.strip()[:300])
        else:
            saida = json.loads(r.stdout)
    if saida:
        for caso, rj in zip(casos, saida):
            filtros, versao, caixa, _escolhidas, lista, escondidas, fica, tiradas = caso
            nome = "%s, %s, caixa %s" % (filtros or "sem filtros", versao, "ligada" if caixa else "desligada")
            esperado_ids = na_va if versao == "va" else na_vb
            if rj["ids"] != sorted(esperado_ids):
                problemas.append("%s: na montagem %s" % (nome, rj["ids"]))
            if rj["vazia"]:
                problemas.append("%s: sem versao aberta o idsNaMontagem devolveu %d" % (nome, rj["vazia"]))
            if rj["lista"] != lista:
                problemas.append("%s: a lista e %s e devia ser %s" % (nome, rj["lista"], lista))
            if rj["escondidas"] != escondidas:
                problemas.append("%s: diz %d escondidas e sao %d" % (nome, rj["escondidas"], escondidas))
            if rj["sel"] != sorted(fica) or rj["tiradas"] != tiradas:
                problemas.append("%s: escolhidas %s, tirou %d" % (nome, rj["sel"], rj["tiradas"]))
            # a chave da lista e o que o pintaGrelha compara para repintar quando a montagem muda
            chave = "|".join(sorted(esperado_ids)) if caixa else None
            if rj["chave"] != chave:
                problemas.append("%s: a chave da lista e %r" % (nome, rj["chave"]))
    verifica("Mesa: esconder as que ja estao nesta montagem", not problemas and saida is not None,
             "; ".join(problemas[:3]) if problemas else
             "%d casos no node, grupos e soltas, duas versoes" % len(casos))


def teste_mesa_sem_nomes_repetidos():
    """Nenhum nome e declarado duas vezes no nivel de cima do script da Mesa.

    O DEFEITO QUE ISTO APANHA: a 17 de setembro o modo de substituir uma foto de um grupo
    ganhou um `var troca = null`, e a Mesa ja tinha uma `function troca(a, i, j)`, a que as
    setas de subir e descer um clip usam. As duas estavam na mesma funcao de fora; a declaracao
    da funcao sobe ao inicio e o `troca = null` escreve-lhe por cima. Carregar numa seta dava
    "troca is not a function", o clip nao saia do sitio e ficava no anular uma entrada que nao
    mudava nada. O "use strict" nao se queixa disto, e o testes.py so lia o HTML como texto.

    Le-se o scripts/editor_base.html: os nomes de `function`, `var`, `let` e `const` que
    comecam na coluna 0, que e onde estao as declaracoes do nivel de cima, com cada `var` de
    varios nomes partido pelas virgulas de fora de parenteses, chavetas e aspas.
    """
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    js = max(scripts, key=len) if scripts else ""
    antes_do_script = html.count("\n", 0, html.find(js)) if js else 0   # para dizer a linha do editor_base.html
    declarados = {}

    def nomes_da_declaracao(texto):
        """Os nomes de `var a = 1, b = f(x, y), c;` ate ao ; de fora, sem entrar em aspas nem comentarios."""
        partes, atual, prof, p, aspa = [], [], 0, 0, None
        while p < len(texto):
            ch = texto[p]
            if aspa:
                atual.append(ch)
                if ch == "\\":
                    atual.append(texto[p + 1:p + 2])
                    p += 1
                elif ch == aspa:
                    aspa = None
            elif texto.startswith("/*", p):
                fim = texto.find("*/", p + 2)
                p = len(texto) if fim < 0 else fim + 1
            elif texto.startswith("//", p):
                fim = texto.find("\n", p)
                p = len(texto) if fim < 0 else fim - 1
            elif ch in "'\"`":
                aspa = ch
                atual.append(ch)
            elif ch in "([{":
                prof += 1
                atual.append(ch)
            elif ch in ")]}":
                prof -= 1
                atual.append(ch)
            elif ch == "," and prof == 0:
                partes.append("".join(atual))
                atual = []
            elif ch == ";" and prof == 0:
                break
            else:
                atual.append(ch)
            p += 1
        partes.append("".join(atual))
        return [m.group(1) for m in (re.match(r"\s*([A-Za-z_$][\w$]*)\s*(=|$)", x) for x in partes) if m]

    for m in re.finditer(r"^(function|var|let|const)\s+", js, re.M):
        linha = antes_do_script + js.count("\n", 0, m.start()) + 1
        if m.group(1) == "function":
            nome = re.match(r"\s*([A-Za-z_$][\w$]*)", js[m.end():])
            nomes = [nome.group(1)] if nome else []
        else:
            nomes = nomes_da_declaracao(js[m.end():])
        for nome in nomes:
            declarados.setdefault(nome, []).append((m.group(1), linha))
    repetidos = {n: d for n, d in declarados.items() if len(d) > 1}
    funcoes = sum(1 for d in declarados.values() for tipo, _l in d if tipo == "function")
    verifica("Mesa: nenhum nome declarado duas vezes no nivel de cima", not repetidos and funcoes > 150 and len(declarados) - funcoes > 40,
             ("; ".join("%s: %s" % (n, ", ".join("%s na linha %d" % x for x in d)) for n, d in list(repetidos.items())[:4]))
             if repetidos else "%d nomes, %d deles funcoes" % (len(declarados), funcoes))


def teste_mesa_escreve_o_estilo():
    """O estilo que a Mesa guarda no clip chega a coluna tratamento, e o render le-o de la.

    O PEDIDO, decisao 068: o clip da Mesa leva estilo "filas" ou "espalhada" na colagem e
    "monte" ou "leque" na pilha. O montar_da_mesa.py punha na coluna tratamento o "r" do
    clip, que e "fiel": a escolha do Tiago perdia-se ali e o video saia sempre com a
    omissao, sem aviso. Um estilo que nao existe, ou o de uma pilha numa colagem, fica a
    omissao escrita e um aviso, uma vez. E o estilo so muda onde as fotos pousam: a agenda
    e a mesma, que e o que deixa a Mesa usar a mesma duracao minima.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # antes do redirect: o render mexe no sys.stdout ao ser importado
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        verifica("Mesa escreve o estilo e o render le-o", False, "fotos do ensaio fora do inventario")
        return
    pasta = tempfile.mkdtemp(prefix="teste_estilo_")
    estado = {"versoes": [{"id": "t", "nome": "t", "clips": [
        {"t": "colagem", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel", "estilo": "espalhada"},
        {"t": "pilha", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel", "estilo": "leque"},
        {"t": "colagem", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel"},
        {"t": "pilha", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel", "estilo": "torta"},
        {"t": "colagem", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel", "estilo": "leque"},
        {"t": "pilha", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel", "estilo": "monte"},
        {"t": "pilha", "fotos": tres, "x": "", "d": 8, "c": 0.7, "r": "fiel", "estilo": " leque "}]}]}
    caminho = os.path.join(pasta, "estado.json")
    json.dump(estado, open(caminho, "w", encoding="utf-8"))
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    sys.argv = ["montar_da_mesa.py", "t", "--nome", "t"]
    saida = io.StringIO()
    try:
        with contextlib.redirect_stdout(saida):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
    linhas = list(csv.DictReader(open(os.path.join(pasta, "t.csv"), encoding="utf-8-sig")))
    escritos = [l["tratamento"] for l in linhas]
    # O ultimo traz " leque " com espacos, como pode vir de um campo escrito a mao: tem de
    # ficar leque e sem aviso. E o aviso diz o clip certo, pela ordem da montagem.
    esperados = ["espalhada", "leque", "filas", "monte", "filas", "monte", "leque"]
    avisos = [l.strip() for l in saida.getvalue().splitlines() if "desconhecido" in l]
    certo = (escritos == esperados and len(avisos) == 2
             and any("'torta'" in a and "fica monte" in a and "(clip 4)" in a for a in avisos)
             and any("'leque'" in a and "fica filas" in a and "(clip 5)" in a for a in avisos)
             and render.ESTILOS_MONTE == montar_da_mesa.ESTILOS_MONTE)
    verifica("Mesa escreve o estilo na coluna tratamento", certo,
             "tratamentos %s, avisos %s" % (escritos, avisos))

    # O render le a coluna: cada linha, com fotos de uma cor so no lugar das verdadeiras.
    caminhos = []
    for k, a in enumerate((4 / 3.0, 3 / 4.0, 16 / 9.0)):
        c = os.path.join(pasta, "cor%d.png" % k)
        Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k]).save(c)
        caminhos.append(c)
    prontos = []
    for l in linhas:
        clip = dict(l, _caminhos=caminhos, _transicao_entrada=0.7, _transicao_seguinte=0.7)
        prontos.append(render.preparar(clip, {}))
    lidos = [p["estilo"] if p else None for p in prontos]
    centros = [[f["centro"] for f in p["fotos"]] if p else None for p in prontos]
    agendas = [render.estado_monte(p, 0.0, 8.0)[:2] if p else None for p in prontos]
    certo = (lidos == esperados and centros[0] != centros[2] and centros[1] != centros[3]
             and centros[3] == centros[5] and centros[2] == centros[4]
             and agendas[0] == agendas[2] and agendas[1] == agendas[3])
    verifica("render le o estilo da coluna tratamento", certo,
             "estilos lidos %s, espalhada %s das filas, leque %s do monte, mesma agenda %s"
             % (lidos, "diferente" if centros[0] != centros[2] else "igual",
                "diferente" if centros[1] != centros[3] else "igual",
                agendas[0] == agendas[2] and agendas[1] == agendas[3]))


def _mesa_de_ensaio(clips, prefixo):
    """Corre o montar_da_mesa.main() sobre uma versao feita a mao: (linhas do CSV, cabecalho, saida)."""
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render  # noqa: F401  antes do redirect: o render mexe no sys.stdout ao ser importado
    pasta = tempfile.mkdtemp(prefix=prefixo)
    caminho = os.path.join(pasta, "estado.json")
    json.dump({"versoes": [{"id": "t", "nome": "t", "clips": clips}]},
              open(caminho, "w", encoding="utf-8"), ensure_ascii=False)
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    sys.argv = ["montar_da_mesa.py", "t", "--nome", "t"]
    saida = io.StringIO()
    try:
        with contextlib.redirect_stdout(saida):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
    # Lido como o render le a montagem: utf-8-sig e newline="".
    with open(os.path.join(pasta, "t.csv"), encoding="utf-8-sig", newline="") as fh:
        leitor = csv.DictReader(fh)
        linhas = list(leitor)
    return linhas, leitor.fieldnames, saida.getvalue(), pasta


def teste_mesa_escreve_textos_das_fotos():
    """O texto de cada foto de um grupo chega a coluna textos_fotos so quando ele o liga na Mesa.

    O PEDIDO: "permite colocar o texto nas fotos mesmo as que ficam em leque e assim, tem
    de ser opcional ter o texto ou nao". A Mesa guarda xf, um texto por foto, e vf, que
    liga e desliga sem apagar. Se o montar_da_mesa.py olhasse so para xf, um texto que ele
    desligou saia no video; se trocasse a ordem, cada texto caia na foto do lado. Um
    grupo de antes dos textos nao tem xf, e uma foto solta tem o texto no x.
    """
    import json
    import montar_da_mesa
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres + ["f0012"]):
        verifica("Mesa escreve textos_fotos com vf ligado", False, "fotos do ensaio fora do inventario")
        return
    tres_trocadas = ["f0336", "f0331", "f0334"]
    grupo = {"x": "", "d": 8, "c": 0.7, "r": "fiel"}
    clips = [
        {"t": "foto", "i": "f0012", "f": "", "x": "Natal", "d": 4, "c": 0.7, "r": "fiel",
         "xf": ["Natal"], "vf": True},
        dict(grupo, t="colagem", fotos=tres, x="Amigos", xf=["  Verão de 2014 ", "", "2019"], vf=True),
        dict(grupo, t="colagem", fotos=tres, xf=["Natal", "Porto", "2019"], vf=False),
        dict(grupo, t="colagem", fotos=tres, xf=["Natal", "Porto", "2019"]),
        dict(grupo, t="pilha", fotos=tres, vf=True),
        dict(grupo, t="colagem", fotos=tres, xf=["", "  ", ""], vf=True),
        dict(grupo, t="lado", fotos=tres[:2], xf=["Natal", "Porto"], vf=True),
        dict(grupo, t="colagem", fotos=tres_trocadas, xf=["2019", "Natal", "Porto"], vf=True),
        # UM NULL NO XF E UM TEXTO VAZIO, nunca a palavra None: um estado antigo ou editado a
        # mao pode traze-lo, e o render desenhava "None" na foto.
        dict(grupo, t="colagem", fotos=tres, xf=["Natal", None, "2019"], vf=True),
        # E O MESMO AO BOOLEANO E AO NUMERO COM PARTE DECIMAL: um true saia escrito "True" na
        # fotografia e um 2019.0 saia "2019.0". O ler_textos_fotos() do render ja recusava o
        # booleano, quem escrevia a coluna e que nao, e assim os dois discordavam.
        dict(grupo, t="colagem", fotos=tres, xf=[True, 2019.0, 20.5], vf=True),
    ]
    linhas, cabecalho, saida, _ = _mesa_de_ensaio(clips, "teste_textos_")
    col = [l.get("textos_fotos") for l in linhas]
    if len(linhas) != len(clips):
        verifica("Mesa escreve textos_fotos com vf ligado", False,
                 "%d linhas para %d clips" % (len(linhas), len(clips)))
        return
    # O texto e o JSON escrito com os acentos a vista e com strip(), e a chave de cada
    # texto e a foto na mesma posicao do id da linha.
    trocadas = linhas[7]["id"].split("|")
    pares = dict(zip(trocadas, json.loads(col[7]))) if col[7] else {}
    certo = (col[1] == '["Verão de 2014", "", "2019"]' and linhas[1]["texto_ecra"] == "Amigos"
             and col[6] == '["Natal", "Porto"]'
             and trocadas == tres_trocadas and pares == {"f0336": "2019", "f0331": "Natal", "f0334": "Porto"}
             and col[8] == '["Natal", "", "2019"]' and col[9] == '["", "2019", "20.5"]'
             and cabecalho == montar_da_mesa.COLUNAS
             and cabecalho[-3:] == ["nota", "textos_fotos", "textos_opcoes"])
    verifica("Mesa escreve textos_fotos com vf ligado, pela ordem das fotos", certo,
             "colagem %s, lado %s, trocadas %s, com null %s, com booleano %s, colunas no fim %s"
             % (col[1], col[6], pares, col[8], col[9], cabecalho[-3:]))
    avisos = [l.strip() for l in saida.splitlines()
              if "textos para" in l or "caracteres" in l or "so se le" in l]
    certo = col[0] == col[2] == col[3] == col[4] == col[5] == "" and not avisos
    verifica("Mesa deixa textos_fotos vazia sem vf, sem xf, sem texto e nas soltas", certo,
             "solta %r, vf desligado %r, sem vf %r, sem xf %r, vazios %r, avisos %s"
             % (col[0], col[2], col[3], col[4], col[5], avisos))


def teste_mesa_avisa_textos_das_fotos():
    """Uma lista de textos de outro tamanho completa-se ou corta-se com aviso, e o texto longo e a pilha avisam.

    O PORQUE: a Mesa completa xf ao mostrar, e uma lista curta ou comprida nao se ve la.
    Cortada em silencio, um texto que ele escreveu nunca chega ao video. Um texto acima
    de 32 caracteres sai cortado a reticencias numa foto pequena, e numa pilha cada texto
    so se le enquanto a sua foto esta por cima: ele tem de saber antes do render. Com o
    texto desligado nada disto interessa e nada se diz.
    """
    import json
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        verifica("Mesa completa e corta textos_fotos com aviso", False, "fotos do ensaio fora do inventario")
        return
    t32 = ("Natal 2019 " * 3).strip()            # 32 caracteres, no limite: sem aviso
    t33 = t32 + "!"
    grupo = {"x": "", "d": 8, "c": 0.7, "r": "fiel"}
    clips = [
        dict(grupo, t="colagem", fotos=tres, xf=["Natal"], vf=True),                       # clip 1
        dict(grupo, t="lado", fotos=tres[:2], xf=["Natal", "Porto", "2019"], vf=True),     # clip 2
        dict(grupo, t="colagem", fotos=tres, xf=["", "", "", "Porto"], vf=True),           # clip 3
        dict(grupo, t="colagem", fotos=tres, xf=["Natal"], vf=False),                      # clip 4
        dict(grupo, t="pilha", fotos=tres, xf=["Natal", "", "2019"], vf=True),             # clip 5
        dict(grupo, t="pilha", fotos=tres, xf=["Natal", "", ""], vf=False),                # clip 6
        dict(grupo, t="colagem", fotos=tres, xf=[t33, t32, ""], vf=True),                  # clip 7
        dict(grupo, t="pilha", fotos=tres, xf=["", "", ""], vf=True),                      # clip 8
    ]
    linhas, _, saida, _ = _mesa_de_ensaio(clips, "teste_textos_avisos_")
    if len(linhas) != len(clips) or len(t32) != 32:
        verifica("Mesa completa e corta textos_fotos com aviso", False,
                 "%d linhas para %d clips" % (len(linhas), len(clips)))
        return
    col = [l.get("textos_fotos") for l in linhas]
    ler = [json.loads(c) if c else None for c in col]
    tamanho = [l.strip() for l in saida.splitlines() if "textos para" in l]
    certo = (ler[0] == ["Natal", "", ""] and ler[1] == ["Natal", "Porto"] and col[2] == "" and col[3] == ""
             and len(tamanho) == 3
             and any("com 1 textos para 3 fotos" in a and "completei" in a and "(clip 1)" in a for a in tamanho)
             and any("com 3 textos para 2 fotos" in a and "'2019'" in a and "(clip 2)" in a for a in tamanho)
             and any("com 4 textos para 3 fotos" in a and "'Porto'" in a and "(clip 3)" in a for a in tamanho))
    verifica("Mesa completa e corta textos_fotos com aviso", certo,
             "colunas %s, avisos %s" % (col[:4], tamanho))
    longos = [l.strip() for l in saida.splitlines() if "caracteres" in l]
    pilhas = [l.strip() for l in saida.splitlines() if "so se le" in l]
    certo = (ler[4] == ["Natal", "", "2019"] and col[5] == "" and col[7] == ""
             and ler[6] == [t33, t32, ""]
             and len(longos) == 1 and "foto 1 com 33 caracteres" in longos[0] and "(clip 7)" in longos[0]
             and len(pilhas) == 1 and "(clip 5)" in pilhas[0])
    verifica("Mesa avisa texto comprido e pilha com textos", certo,
             "longos %s, pilhas %s" % (longos, pilhas))


def teste_textos_das_fotos_chegam_ao_render():
    """Aspas, "|", acentos e mudancas de linha nos textos das fotos chegam iguais ao preparar do render.

    O PORQUE: o texto e escrito a mao pelo Tiago num campo da Mesa e atravessa tres
    formatos, o JSON da base, a coluna do CSV e o JSON dentro dela. O "|" e o separador
    das fotos nas outras colunas, as aspas sao as do JSON e as do CSV, e uma mudanca de
    linha numa celula e onde um CSV costuma partir. Um texto que chegasse ao render com
    outras letras saia no ecra do jantar sem ninguem o ter escrito.
    """
    import contextlib
    import inspect
    import io
    import tempfile
    import render
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        verifica("textos das fotos chegam ao render", False, "fotos do ensaio fora do inventario")
        return
    grupo = {"d": 8, "c": 0.7, "r": "fiel"}
    pedidos = [
        dict(grupo, t="lado", fotos=tres, lay="3v", x="",
             xf=['Diz "olá" à porta', "Porto | Gaia", "Verão\nde 2014"], vf=True),
        dict(grupo, t="colagem", fotos=tres, x="2019",
             xf=["  Natal, 2019  ", "", 'Ano "novo" | 2020\n'], vf=True),
        dict(grupo, t="pilha", fotos=tres, x="", estilo="leque",
             xf=["São João", "Natal \\o/", "2019;2020"], vf=True),
    ]
    esperados = [['Diz "olá" à porta', "Porto | Gaia", "Verão\nde 2014"],
                 ["Natal, 2019", "", 'Ano "novo" | 2020'],
                 ["São João", "Natal \\o/", "2019;2020"]]
    linhas, _, _, pasta = _mesa_de_ensaio(pedidos, "teste_textos_render_")
    lidos = [render.ler_textos_fotos(l.get("textos_fotos")) for l in linhas]
    verifica("textos das fotos voltam iguais da coluna do CSV", lidos == esperados,
             "lidos %r" % (lidos,))

    # E pelo preparar, que e por onde o render os usa: apanha-se o que ele entrega a quem
    # desenha, com fotos de uma cor so no lugar das verdadeiras.
    caminhos = []
    for k, a in enumerate((4 / 3.0, 3 / 4.0, 16 / 9.0)):
        c = os.path.join(pasta, "cor%d.png" % k)
        Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k]).save(c)
        caminhos.append(c)
    entregues = []
    originais = (render.preparar_monte, render.preparar_lado)

    def espia(original):
        def f(*args, **kw):
            entregues.append(inspect.signature(original).bind(*args, **kw).arguments.get("textos"))
            return original(*args, **kw)
        return f

    render.preparar_monte, render.preparar_lado = espia(originais[0]), espia(originais[1])
    prontos = []
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            for l in linhas:
                clip = dict(l, _caminhos=caminhos, _transicao_entrada=0.7, _transicao_seguinte=0.7)
                prontos.append(render.preparar(clip, {}))
    finally:
        render.preparar_monte, render.preparar_lado = originais
    tipos = [p.get("tipo") if p else None for p in prontos]
    verifica("textos das fotos chegam iguais ao preparar do render",
             entregues == esperados and tipos == ["lado", "colagem", "pilha"],
             "entregues %r, preparados %s" % (entregues, tipos))


def teste_mesa_escreve_textos_opcoes():
    """A coluna textos_opcoes leva so o que difere da omissao, e vai vazia sempre que nada conta.

    O PEDIDO, a 15 de setembro: a opcao "na legenda de baixo" (vm), o tamanho da letra a
    escolha dele (tt) e, na pilha, os textos das fotos de baixo a ficar ou a desaparecer
    (vt). O render le a coluna vazia como a omissao, por isso escrever a omissao por
    extenso nao muda o video, mas escrever um vt fora da pilha, ou na opcao legenda, dizia
    uma coisa que o video nao faz; e um tamanho fora de 28..90 que passasse era um texto a
    sair de outra maneira. Nada conta sem vf nem sem textos: um tt errado num grupo com o
    texto desligado nao vai a lado nenhum e avisar dele era ruido.
    """
    import montar_da_mesa
    import render
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres + ["f0012"]):
        verifica("Mesa escreve textos_opcoes so com o que difere da omissao", False,
                 "fotos do ensaio fora do inventario")
        return
    xf3 = ["Natal", "Porto", "2019"]
    t33 = ("Natal 2019 " * 3).strip() + "!"
    grupo = {"x": "", "d": 8, "c": 0.7, "r": "fiel"}
    clips = [
        dict(grupo, t="colagem", fotos=tres, xf=["Verão", "Porto", "2019"], vf=True, vm="legenda"),  # 1
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=56),                         # 2
        dict(grupo, t="pilha", fotos=tres, xf=xf3, vf=True, vt="fica"),                       # 3
        dict(grupo, t="pilha", fotos=tres, xf=xf3, vf=True, vm="legenda", tt=60, vt="fica"),  # 4
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, vt="fica"),                     # 5
        dict(grupo, t="lado", fotos=tres[:2], xf=xf3[:2], vf=True, vt="fica", tt=46),         # 6
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, vm="foto", tt=46, vt="some"),   # 7
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=False, vm="legenda", tt=56),          # 8
        dict(grupo, t="colagem", fotos=tres, xf=["", "", ""], vf=True, vm="legenda", tt=56),  # 9
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=20),                         # 10
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=91),                         # 11
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=57.5),                       # 12
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=True),                       # 13
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt="56"),                       # 14
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=28.0),                       # 15
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=90),                         # 16
        {"t": "foto", "i": "f0012", "f": "", "x": "Natal", "d": 4, "c": 0.7, "r": "fiel",
         "xf": ["Natal"], "vf": True, "vm": "legenda", "tt": 56},                             # 17
        dict(grupo, t="pilha", fotos=tres, xf=xf3, vf=True, vm="estranho", vt="fica"),        # 18
        dict(grupo, t="pilha", fotos=tres, xf=xf3, vf=True, vt="x"),                          # 19
        dict(grupo, t="pilha", fotos=tres, xf=xf3, vf=False, tt=20),                          # 20
        dict(grupo, t="lado", fotos=tres[:2], xf=xf3[:2], vf=True, vm="legenda", tt="  72 "), # 21
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=""),                         # 22
        dict(grupo, t="colagem", fotos=tres, xf=xf3, vf=True, tt=None, vm=None, vt=None),     # 23
        dict(grupo, t="colagem", fotos=tres, xf=[t33, "", ""], vf=True, vm="legenda"),        # 24
        dict(grupo, t="colagem", fotos=tres, xf=[t33, "", ""], vf=True),                      # 25
    ]
    esperado = ['{"modo": "legenda"}', '{"tamanho": 56}', '{"tapadas": "fica"}',
                '{"modo": "legenda", "tamanho": 60}', "", "", "", "", "",
                "", "", "", "", '{"tamanho": 56}', '{"tamanho": 28}', '{"tamanho": 90}',
                "", '{"tapadas": "fica"}', "", "", '{"modo": "legenda", "tamanho": 72}',
                "", "", '{"modo": "legenda"}', ""]
    linhas, cabecalho, saida, _ = _mesa_de_ensaio(clips, "teste_opcoes_")
    if len(linhas) != len(clips):
        verifica("Mesa escreve textos_opcoes so com o que difere da omissao", False,
                 "%d linhas para %d clips" % (len(linhas), len(clips)))
        return
    col = [l.get("textos_opcoes") for l in linhas]
    textos = [l.get("textos_fotos") for l in linhas]
    diferentes = [(k + 1, c, e) for k, (c, e) in enumerate(zip(col, esperado)) if c != e]
    # Os textos continuam a ir na sua coluna, tambem na opcao legenda, com os acentos a
    # vista, e com o tamanho.
    com_textos = [k + 1 for k, t in enumerate(textos) if t]
    sem_textos = [8, 9, 17, 20]
    certo = (not diferentes and cabecalho == montar_da_mesa.COLUNAS
             and cabecalho[-3:] == ["nota", "textos_fotos", "textos_opcoes"]
             and textos[0] == '["Verão", "Porto", "2019"]'
             and com_textos == [k for k in range(1, len(clips) + 1) if k not in sem_textos])
    verifica("Mesa escreve textos_opcoes so com o que difere da omissao", certo,
             "diferentes (clip, escrito, esperado) %s, colunas no fim %s, textos na legenda %s, com textos %s"
             % (diferentes[:5], cabecalho[-3:], textos[0], com_textos))
    # Os nomes e os valores sao os do render: se um dos lados mudar sozinho, o outro le a
    # coluna como desconhecida e cai na omissao com aviso.
    verifica("Mesa e render concordam nas opcoes dos textos",
             montar_da_mesa.OPCOES_OMISSAO == render.OPCOES_TEXTO
             and montar_da_mesa.TEXTO_FOTO_TAMANHOS == render.TEXTO_FOTO_TAMANHOS
             and montar_da_mesa.MODOS_TEXTO == render.OPCOES_TEXTO_VALORES["modo"]
             and montar_da_mesa.TAPADAS_TEXTO == render.OPCOES_TEXTO_VALORES["tapadas"]
             and montar_da_mesa.TEXTO_FOTO_TAMANHO == render.TEXTO_FOTO_TAMANHO == 46,
             "montar %s %s, render %s %s" % (montar_da_mesa.OPCOES_OMISSAO, montar_da_mesa.TEXTO_FOTO_TAMANHOS,
                                             render.OPCOES_TEXTO, render.TEXTO_FOTO_TAMANHOS))
    # O tamanho invalido cai na omissao com um aviso por clip, com o valor e o clip; o
    # ausente, o vazio, o 46 e o tt de um grupo com o texto desligado nao avisam.
    avisos = [l.strip() for l in saida.splitlines() if "tamanho da letra" in l]
    clips_avisados = sorted(int(a.rsplit("(clip ", 1)[1].rstrip(")")) for a in avisos)
    certo = (clips_avisados == [10, 11, 12, 13]
             and all("fica 46" in a and "entre 28 e 90" in a for a in avisos)
             and any(" 20," in a and "(clip 10)" in a for a in avisos)
             and any(" 91," in a and "(clip 11)" in a for a in avisos)
             and any(" 57.5," in a and "(clip 12)" in a for a in avisos)
             and any(" True," in a and "(clip 13)" in a for a in avisos))
    verifica("Mesa avisa o tamanho da letra invalido e deixa a omissao", certo,
             "avisos nos clips %s: %s" % (clips_avisados, avisos[:2]))
    # Um vm ou vt que a Mesa nao conhece cai na omissao com aviso, e o resto do clip fica.
    vm = [l.strip() for l in saida.splitlines() if "vm=" in l]
    vt = [l.strip() for l in saida.splitlines() if "vt=" in l]
    certo = (len(vm) == 1 and "'estranho'" in vm[0] and "(clip 18)" in vm[0]
             and len(vt) == 1 and "'x'" in vt[0] and "(clip 19)" in vt[0])
    verifica("Mesa avisa vm e vt desconhecidos e fica na omissao", certo, "vm %s, vt %s" % (vm, vt))
    # OS AVISOS DA FAIXA DENTRO DA FOTO SO NA OPCAO EM CADA FOTO. Na legenda de baixo o
    # texto vai em ate quatro linhas no ecra inteiro, e nao ha foto por cima dele.
    pilhas = [l.strip() for l in saida.splitlines() if "so se le" in l]
    vista = [l.strip() for l in saida.splitlines() if "a ficar a vista" in l]
    longos = [l.strip() for l in saida.splitlines() if "caracteres" in l]
    certo = (sorted(int(a.rsplit("(clip ", 1)[1].rstrip(")")) for a in pilhas) == [19]
             and sorted(int(a.rsplit("(clip ", 1)[1].rstrip(")")) for a in vista) == [3, 18]
             and len(longos) == 1 and "(clip 25)" in longos[0])
    verifica("Mesa: os avisos da faixa na foto so na opcao em cada foto, e a pilha diz se fica",
             certo, "so se le %s, a vista %s, longos %s"
             % ([a[-10:] for a in pilhas], [a[-10:] for a in vista], [a[-10:] for a in longos]))


def teste_mesa_avisa_legenda_curta():
    """Na opcao legenda, um texto que fica menos de 1,5 s na legenda de baixo avisa, com a conta do render.

    O PORQUE: o texto da foto k esta no ecra desde que ela comeca a entrar ate a seguinte
    comecar, e numa colagem de cinco em quatro segundos sao quatro decimas por texto, que
    a 15 metros nao se leem. A conta e a de render.tempos_legenda_grupo() com os
    encadeados de encadeados_do_corpo(): o primeiro clip do corpo entra sem encadeado e o
    ultimo sai no fade do fim, e com os encadeados errados os tempos andam. Textos iguais
    seguidos somam-se, os vazios mostram o do grupo, e sem texto do grupo nao ha nada
    para ler nem para avisar. Fora da opcao legenda nao se avisa nada disto.
    """
    import re
    import render
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        verifica("Mesa avisa o texto que fica pouco tempo na legenda de baixo", False,
                 "fotos do ensaio fora do inventario")
        return
    cinco, oito = (tres * 2)[:5], (tres * 3)[:8]
    oito_textos = ["T%d" % k for k in range(8)]
    grupo = {"x": "", "c": 0.7, "r": "fiel", "vf": True, "vm": "legenda"}
    clips = [
        dict(grupo, t="colagem", fotos=cinco, d=4.0, xf=["A", "B", "C", "D", "E"]),           # 1, abre o corpo
        dict(grupo, t="pilha", fotos=tres + tres[:1], d=4.0, xf=["Natal", "Natal", "2019", "2019"]),
        dict(grupo, t="colagem", fotos=tres, d=3.0, x="Amigos", xf=["", "Porto", ""]),        # 3
        dict(grupo, t="colagem", fotos=tres, d=3.0, xf=["", "Porto", ""]),                    # 4
        dict(grupo, t="colagem", fotos=tres, d=3.0, xf=["A", "B", "C"], vm=None, tt=56),      # 5, em cada foto
        dict(grupo, t="lado", fotos=tres, d=4.0, xf=["A", "B", "C"]),                          # 6
        dict(grupo, t="pilha", fotos=oito, d=5.0, xf=oito_textos),                            # 7, fecha o filme
    ]
    # Os encadeados de cada um, escritos a mao: zero a entrar no primeiro do corpo, o fade
    # do fim (2,5 s) a sair do ultimo, e o 0,7 dos clips entre eles.
    casos = [("colagem", 5, 4.0, 0.0, 0.7, ["A", "B", "C", "D", "E"]),
             ("pilha", 4, 4.0, 0.7, 0.7, ["Natal", "Natal", "2019", "2019"]),
             ("colagem", 3, 3.0, 0.7, 0.7, ["Amigos", "Porto", "Amigos"]),
             ("colagem", 3, 3.0, 0.7, 0.7, ["", "Porto", ""]),
             None,
             ("lado", 3, 4.0, 0.7, 0.7, ["A", "B", "C"]),
             ("pilha", 8, 5.0, 0.7, 2.5, oito_textos)]
    esperados = set()
    for ordem, caso in enumerate(casos, 1):
        if not caso:
            continue
        tipo, n, d, entra, sai, mostra = caso
        tempos = render.tempos_legenda_grupo(tipo, n, d, entra, sai)
        for k, t, dura in render.legendas_curtas(mostra, tempos):
            esperados.add((ordem, k + 1, "%.1f" % dura, t))
    linhas, _, saida, _ = _mesa_de_ensaio(clips, "teste_legenda_curta_")
    if len(linhas) != len(clips):
        verifica("Mesa avisa o texto que fica pouco tempo na legenda de baixo", False,
                 "%d linhas para %d clips" % (len(linhas), len(clips)))
        return
    padrao = re.compile(r"^(\w+): o texto da foto (\d+) fica so ([\d.]+) s na legenda de baixo, "
                        r"pouco para ler a 15 metros: '(.*)' \(clip (\d+)\)$")
    avisos = [l.strip() for l in saida.splitlines() if "na legenda de baixo" in l]
    lidos, mal = set(), []
    for a in avisos:
        m = padrao.match(a)
        if not m:
            mal.append(a)
            continue
        lidos.add((int(m.group(5)), int(m.group(2)), m.group(3), m.group(4)))
    por_clip = {k: sorted(x[1:] for x in lidos if x[0] == k) for k in range(1, 8)}
    # Os numeros escritos por extenso, para o teste nao depender so da conta do render: a
    # colagem de 5 a abrir o corpo da 0,8 s ao primeiro texto (1,1 s com o encadeado do
    # proprio clip), e a pilha de 8 a fechar o filme 0,5 s (1,1 s sem o fade do fim). O
    # clip 5 esta em cada foto com o tamanho 56: a coluna das opcoes nao vai vazia, e
    # mesmo assim nao e um caso da legenda de baixo.
    certo = (lidos == esperados and not mal and len(esperados) == 16
             and (1, 1, "0.8", "A") in lidos and (7, 1, "0.5", "T0") in lidos
             and len(por_clip[1]) == 4 and por_clip[2] == [] and len(por_clip[3]) == 2
             and por_clip[4] == [(2, "0.4", "Porto")] and por_clip[5] == []
             and len(por_clip[6]) == 2 and len(por_clip[7]) == 7)
    verifica("Mesa avisa o texto que fica pouco tempo na legenda de baixo, com os encadeados certos",
             certo, "a mais %s, a menos %s, mal escritos %s, por clip %s"
             % (sorted(lidos - esperados)[:4], sorted(esperados - lidos)[:4], mal[:2],
                {k: len(v) for k, v in por_clip.items()}))
    # A pilha na opcao legenda nao leva o aviso da faixa dentro da foto.
    pilhas = [l for l in saida.splitlines() if "so se le" in l or "a ficar a vista" in l]
    verifica("Mesa: a pilha na opcao legenda nao avisa da faixa dentro da foto", not pilhas,
             "%s" % pilhas)
    # E UMA MONTAGEM SO COM LADO A LADO TAMBEM AVISA: a conta vive no render, e o
    # montar_da_mesa.py so o importava quando havia colagem ou pilha.
    so_lado = [dict(grupo, t="lado", fotos=tres, d=4.0, xf=["A", "B", "C"])]
    _, _, saida2, _ = _mesa_de_ensaio(so_lado, "teste_legenda_curta_lado_")
    avisos2 = sorted(padrao.match(l.strip()).group(2, 3)
                     for l in saida2.splitlines() if padrao.match(l.strip()))
    verifica("Mesa avisa o texto curto na legenda de baixo tambem so com lado a lado",
             avisos2 == [("1", "0.8"), ("2", "%.1f" % (1.25 - 0.8))], "%s" % avisos2)


def teste_mesa_avisa_legenda_comprida_e_foto_depois_do_fim():
    """Na opcao legenda, um texto que parte em varias linhas avisa, e uma foto que entra depois do fim do clip tambem.

    O PORQUE, das duas coisas que o montar_da_mesa.py deixava passar caladas:
      - a faixa de baixo fica com a altura do texto mais alto durante o clip inteiro, para as
        fotos nao mudarem de sitio quando o texto troca. Um texto que parte em duas linhas
        sobe a faixa 62 pixeis e encolhe as fotos de todo o clip, tambem as que tem "Natal"
        ou nada, e o aviso dos 32 caracteres esta desligado nesta opcao porque a faixa do ecra
        inteiro leva muito mais. O aviso conta as linhas com a conta do render, para a letra
        escolhida, e so na opcao legenda;
      - no lado a lado as celulas entram aos 0,35 + k x 0,45 s seja qual for a duracao, e num
        4q de 1,5 s a quarta entra aos 1,7: o texto dela nunca aparece, e o aviso dizia "fica
        so -0.2 s". A terceira, que entra aos 1,25, fica 0,2 s e nao 0,5.
    """
    import render
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        verifica("Mesa avisa o texto que parte em varias linhas na legenda de baixo", False,
                 "fotos do ensaio fora do inventario")
        return
    grupo = {"x": "", "d": 8, "c": 0.7, "r": "fiel", "vf": True}
    clips = [
        dict(grupo, t="colagem", fotos=tres, xf=[TEXTO_LONGO, "Natal", "2019"], vm="legenda"),           # 1
        dict(grupo, t="colagem", fotos=tres, xf=[TEXTO_LONGO, "Natal", "2019"], vm="legenda", tt=90),    # 2
        dict(grupo, t="colagem", fotos=tres, xf=[TEXTO_LONGO, "Natal", "2019"]),                         # 3, em cada foto
        dict(grupo, t="colagem", fotos=tres, xf=["Natal", "", "2019"], vm="legenda"),                    # 4
        dict(grupo, t="lado", fotos=(tres * 2)[:4], lay="4q", d=1.5, xf=["A", "B", "C", "D"], vm="legenda"),  # 5
    ]
    linhas, _, saida, _ = _mesa_de_ensaio(clips, "teste_legenda_linhas_")
    if len(linhas) != len(clips):
        verifica("Mesa avisa o texto que parte em varias linhas na legenda de baixo", False,
                 "%d linhas para %d clips" % (len(linhas), len(clips)))
        return
    a46 = len(render.linhas_legenda(TEXTO_LONGO, 46)[1])
    a90 = len(render.linhas_legenda(TEXTO_LONGO, 90)[1])
    varias = [l.strip() for l in saida.splitlines() if "linhas na legenda de baixo" in l]
    certo = (a46 >= 2 and a90 > a46 and len(varias) == 2
             and any("colagem, texto da foto 1 leva %d linhas" % a46 in a and "(clip 1)" in a and "encolhem" in a
                     for a in varias)
             and any("texto da foto 1 leva %d linhas" % a90 in a and "(clip 2)" in a for a in varias)
             and any("caracteres" in l and "(clip 3)" in l for l in saida.splitlines()))
    verifica("Mesa avisa o texto que parte em varias linhas na legenda de baixo", certo,
             "%d linhas a 46 e %d a 90, avisos %s" % (a46, a90, varias))
    depois = [l.strip() for l in saida.splitlines() if "nunca aparece" in l]
    curto = [l.strip() for l in saida.splitlines() if "fica so" in l and "(clip 5)" in l]
    certo = (len(depois) == 1 and "lado: o texto da foto 4 nunca aparece na legenda de baixo, a foto so entra 0.2 s "
             "depois de o clip acabar: 'D' (clip 5)" == depois[0]
             and any("foto 3 fica so 0.2 s" in l for l in curto) and not any("-" in l for l in curto))
    verifica("Mesa avisa a foto que so entra depois do fim do clip na legenda de baixo", certo,
             "depois do fim %s, curtos %s" % (depois, curto))


def teste_textos_opcoes_chegam_ao_render():
    """As opcoes escritas pela Mesa chegam ao preparar do render, e os dois avisam do mesmo.

    O PORQUE: a coluna atravessa o JSON da base, o CSV e o JSON dentro dele, e o render le
    o que nao conhece como a omissao com aviso. Se o montar_da_mesa.py escrevesse um nome
    que o render nao le, a Mesa mostrava a opcao e o video saia sem ela. E o aviso do
    texto curto na legenda de baixo tem de dar o mesmo nos dois, senao ele corrige na Mesa
    o que o render nao viu, ou ao contrario.
    """
    import contextlib
    import inspect
    import io
    import re
    import render
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        verifica("textos_opcoes chegam ao preparar do render", False, "fotos do ensaio fora do inventario")
        return
    grupo = {"d": 8, "c": 0.7, "r": "fiel", "vf": True}
    xf3 = ["Natal", "", "2019"]
    pedidos = [
        dict(grupo, t="lado", fotos=tres, lay="3v", x="Amigos", xf=xf3, vm="legenda", tt=56),
        dict(grupo, t="colagem", fotos=tres, x="", xf=xf3, tt=64),
        dict(grupo, t="pilha", fotos=tres, x="", xf=xf3, vt="fica"),
        dict(grupo, t="pilha", fotos=tres, x="", xf=xf3, d=3.0, vm="legenda", vt="fica", tt=60),
        dict(grupo, t="colagem", fotos=tres, x="2019", xf=xf3),
    ]
    omissao = {"modo": "foto", "tamanho": 46, "tapadas": "some"}
    esperados = [dict(omissao, modo="legenda", tamanho=56), dict(omissao, tamanho=64),
                 dict(omissao, tapadas="fica"), dict(omissao, modo="legenda", tamanho=60), omissao]
    linhas, _, saida_mesa, pasta = _mesa_de_ensaio(pedidos, "teste_opcoes_render_")
    if len(linhas) != len(pedidos):
        verifica("textos_opcoes chegam ao preparar do render", False,
                 "%d linhas para %d clips" % (len(linhas), len(pedidos)))
        return
    lidos = [render.ler_textos_opcoes(l.get("textos_opcoes")) for l in linhas]
    verifica("textos_opcoes voltam iguais da coluna do CSV", lidos == esperados, "lidos %r" % (lidos,))

    # E pelo preparar, com os encadeados que o render poe (ligar_transicoes), que sao os que
    # o montar_da_mesa.py contou: o que chega a quem desenha, e o que sai preparado.
    caminhos = []
    for k, a in enumerate((4 / 3.0, 3 / 4.0, 16 / 9.0)):
        c = os.path.join(pasta, "cor%d.png" % k)
        Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k]).save(c)
        caminhos.append(c)
    clips = [dict(l, _caminhos=caminhos) for l in linhas]
    render.ligar_transicoes(clips)
    entregues = []
    originais = (render.preparar_monte, render.preparar_lado)

    def espia(original):
        def f(*args, **kw):
            entregues.append(inspect.signature(original).bind(*args, **kw).arguments.get("opcoes"))
            return original(*args, **kw)
        return f

    render.preparar_monte, render.preparar_lado = espia(originais[0]), espia(originais[1])
    prontos, saidas = [], []
    try:
        for clip in clips:
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                prontos.append(render.preparar(clip, {}))
            saidas.append(saida.getvalue())
    finally:
        render.preparar_monte, render.preparar_lado = originais
    if any(p is None for p in prontos):
        verifica("textos_opcoes chegam ao preparar do render", False, "preparar devolveu None")
        return
    dentro = [p.get("opcoes") for p in prontos]
    legendas = [p.get("legenda") is not None for p in prontos]
    # com "fica" nenhuma foto da pilha leva o sprite sem texto; com "some" as tapadas levam
    sem_texto = [[f.get("sprite_sem") is not None for f in p["fotos"]] if "fotos" in p else None
                 for p in prontos]
    textos_nas_fotos = [[f.get("texto") for f in p["fotos"]] if "fotos" in p else None for p in prontos]
    certo = (entregues == esperados and dentro == esperados
             and legendas == [True, False, False, True, False]
             and prontos[0]["legenda"]["textos"] == ["Natal", "Amigos", "2019"]
             and prontos[0]["legenda"]["tamanho"] == 56
             and prontos[3]["legenda"]["textos"] == ["Natal", "", "2019"]
             and prontos[3]["legenda"]["tamanho"] == 60
             and sem_texto[2] == [False, False, False] and sem_texto[3] == [False, False, False]
             and textos_nas_fotos[3] == ["", "", ""] and textos_nas_fotos[1] == ["Natal", "", "2019"]
             and textos_nas_fotos[2] == ["Natal", "", "2019"])
    verifica("textos_opcoes chegam iguais ao preparar do render, e o preparado segue-as",
             certo, "entregues %r, dentro %r, legendas %s, sprites sem texto %s, textos nas fotos %s"
             % (entregues, dentro, legendas, sem_texto, textos_nas_fotos))
    # O AVISO DO TEXTO CURTO E O MESMO NOS DOIS, clip a clip: o lado a lado em 8 s (0,8 s e
    # 0,45 s aos dois primeiros textos) e a pilha de 3 em 3,0 s tem textos a menos de 1,5 s
    # na opcao legenda, e a Mesa e o render dizem as mesmas fotos com os mesmos decimos; os
    # outros clips, em cada foto, nao avisam disto em lado nenhum.
    pares, com_aviso = [], []
    for k in range(len(clips)):
        da_mesa = set(re.findall(r"o texto da foto (\d+) fica so ([\d.]+) s na legenda de baixo[^\n]*\(clip %d\)"
                                 % (k + 1), saida_mesa))
        do_render = set(re.findall(r"o texto da foto (\d+) do grupo fica so ([\d.]+) s", saidas[k]))
        pares.append((sorted(da_mesa), sorted(do_render)))
        if da_mesa or do_render:
            com_aviso.append(k + 1)
    verifica("Mesa e render avisam do mesmo texto curto na legenda de baixo",
             all(a == b for a, b in pares) and com_aviso == [1, 4] and pares[0][0] == [("1", "0.8"), ("2", "0.4")],
             "clips com aviso %s, (Mesa, render) %s" % (com_aviso, [p for p in pares if p[0] or p[1]]))


def teste_enquadramento_afastada_e_parada():
    """O enquadramento marcado na Mesa chega ao render.

    O PEDIDO: a IMG_0622 e um plano apertado que ja enche a altura, e o zoom lento
    aproximava-a mais. Afastada tem de deixar margem a volta e parada nao pode mexer.
    """
    import contextlib
    import io
    import json
    import tempfile
    import montar_da_mesa
    import render
    pasta = tempfile.mkdtemp(prefix="teste_enq_")
    foto = os.path.join(pasta, "plano.png")
    Image.new("RGB", (1500, 1000), (200, 30, 30)).save(foto)

    def quadro(mov, t):
        clip = {"tipo": "foto", "ficheiro": "plano.png", "id": "x", "texto_ecra": "", "tratamento": "fiel",
                "fonte_imagem": "", "_caminho": foto, "movimento": mov, "duracao_s": "4", "ordem": 1}
        return render.desenhar(render.preparar(clip, {}), t, 4.0)
    normal = quadro("Zoom in", 0.0).getpixel((960, 20))[0]
    afastada = quadro("Afastada", 0.0).getpixel((960, 20))[0]
    parada = quadro("Parada", 0.0).tobytes() == quadro("Parada", 3.9).tobytes()
    # e a montagem tem de levar o "e" da Mesa para a coluna movimento
    estado = {"versoes": [{"id": "t", "nome": "t", "clips": [
        {"t": "foto", "i": "f0593", "d": 4, "c": 0.7, "r": "fundo", "e": "afastada"},
        {"t": "foto", "i": "f0592", "d": 4, "c": 0.7, "r": "fundo"}]}]}
    caminho = os.path.join(pasta, "estado.json")
    json.dump(estado, open(caminho, "w", encoding="utf-8"))
    guardado = (montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv)
    montar_da_mesa.ESTADO, montar_da_mesa.DESTINO = caminho, pasta
    sys.argv = ["montar_da_mesa.py", "t", "--nome", "t"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            montar_da_mesa.main()
    finally:
        montar_da_mesa.ESTADO, montar_da_mesa.DESTINO, sys.argv = guardado
    movs = [r["movimento"] for r in csv.DictReader(open(os.path.join(pasta, "t.csv"), encoding="utf-8-sig"))]
    verifica("enquadramento afastada e parada chegam ao render",
             normal > 150 and afastada < 20 and parada and movs == ["Afastada", "Zoom in"],
             "topo normal %d, afastada %d, parada imovel %s, movimento %s" % (normal, afastada, parada, movs))


# ------------------------------------------- «aproxima ao ponto de foco», 18 de setembro
# O Tiago, depois de ver o conceito da intro do pedido: "Podes cortar e aproximar, mas
# tens de comecar do plano amplo para verem a arvore de natal." A foto do anel (IMG_2067)
# tem a alianca a ocupar 2% da largura do ecra, que a 15 metros nao existe, e a arvore de
# Natal ao fundo, que faz parte da historia. Um corte fechado resolvia uma coisa e perdia
# a outra, e por isso o clip comeca inteiro e fecha ate ao ponto de foco.
APROXIMA_FOTO = (3000, 2000)     # 3:2, encaixa em 1620x1080 dentro do ecra
APROXIMA_FOCO = (0.35, 0.40)     # longe do centro, mas alcancavel com o zoom da omissao
APROXIMA_MARCA = 40              # lado do quadrado de cor que marca o ponto de foco


def _foto_com_marca(pasta, nome="aproxima.png", tamanho=APROXIMA_FOTO, foco=APROXIMA_FOCO):
    """Uma foto de ensaio com um quadrado de cor no ponto de foco.

    O fundo nao tem um unico pixel preto, de proposito: no tratamento "fiel" o que fica
    por tras da foto e preto, e e assim que se conta quanta borda esta no quadro sem
    confundir borda com a propria fotografia.
    """
    from PIL import ImageDraw
    im = Image.new("RGB", tamanho)
    px = im.load()
    for y in range(tamanho[1]):
        for x in range(0, tamanho[0], 8):
            # O verde nunca desce dos 100: e o que separa a foto da marca cor de rosa, que
            # e o unico sitio da imagem com verde em baixo e vermelho e azul em cima.
            cor = (60 + (x * 7) % 160, 100 + (y * 5) % 120, 80 + ((x + y) * 3) % 140)
            for k in range(min(8, tamanho[0] - x)):
                px[x + k, y] = cor
    d = ImageDraw.Draw(im)
    cx, cy = foco[0] * tamanho[0], foco[1] * tamanho[1]
    meia = APROXIMA_MARCA / 2.0
    d.rectangle([cx - meia, cy - meia, cx + meia, cy + meia], fill=(255, 0, 255))
    caminho = os.path.join(pasta, nome)
    im.save(caminho)
    return caminho


def _centro_da_marca(imagem):
    """(x, y, largura) da marca cor de rosa no fotograma, ou None se nao aparecer."""
    px = imagem.load()
    xs, ys = [], []
    for y in range(0, imagem.height, 2):
        for x in range(0, imagem.width, 2):
            r, g, b = px[x, y]
            if r > 200 and b > 200 and g < 70:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, max(xs) - min(xs))


def _clip_aproxima(caminho, mov, foco=APROXIMA_FOCO, tratamento="fiel"):
    return {"tipo": "foto", "ficheiro": os.path.basename(caminho), "id": "x", "texto_ecra": "",
            "tratamento": tratamento, "_caminho": caminho, "movimento": mov, "ordem": 1,
            "duracao_s": "5", "fonte_imagem": "" if foco is None else "%.4f,%.4f" % foco}


def _caixa_da_marca(imagem):
    """(x0, y0, x1, y1) da marca cor de rosa no fotograma, ao pixel, ou None se nao aparecer.

    Ao pixel e nao de dois em dois: a amostra antiga tinha 2 px de incerteza, e com uma
    tolerancia de 4 px passava um fim a 2,07 em vez de 2,2 (verificador, mutacao A3).
    """
    from PIL import ImageChops
    r, g, b = imagem.convert("RGB").split()
    mascara = ImageChops.multiply(
        ImageChops.multiply(r.point(lambda v: 255 if v > 200 else 0),
                            b.point(lambda v: 255 if v > 200 else 0)),
        g.point(lambda v: 255 if v < 70 else 0))
    return mascara.getbbox()


def _zoom_mostrado(render, ap, p):
    """O zoom que vai ao ecra no instante p: a largura da foto no fotograma sobre a da foto inteira.

    E o que se ve, e nao a escala pedida ao compor(): essa salta em cada troca de nivel, e um
    teste que a media dizia "arranca a andar" quando uma troca calhava no primeiro quinto de
    segundo, e apanhava as curvas erradas por acaso (verificador, mutacoes A2 e A12).
    """
    sprite, escala, _cx, _cy = render.aproxima_quadro(ap, p)
    return (sprite.width - 2 * render.MARGEM) * escala / ap["fw"]


def teste_aproxima_comeca_igual_e_acaba_no_foco():
    """Comeca o fotograma de hoje, ao byte, e acaba com o ponto de foco ao centro no zoom pedido.

    AS DUAS METADES DO PEDIDO, e nenhuma delas vale sozinha: se o primeiro fotograma nao
    for o de hoje deixou de ser "comeca como esta" e a arvore de Natal aparece ja cortada;
    se o fim nao chegar ao ponto de foco, o anel continua a nao se ver a 15 metros.

    Mede-se o fim pela MARCA na propria fotografia, e nao pelas contas que o render fez:
    as contas podem estar certas e o sprite ser colado noutro sitio, e e o sprite que vai
    ao jantar. A largura da marca diz o zoom: 41 px da foto, encaixados a 0,54, dao 22 px
    no primeiro fotograma e az vezes isso no ultimo.

    O QUE O VERIFICADOR MOSTROU QUE PASSAVA, a 18 de setembro, e que agora falha:
      - o aproxima nunca era desenhado com "fundo", e pintar sobre preto esquecendo o fundo
        desfocado passava (A15). A foto do anel e com fundo;
      - so se desenhava 2,2, e um render que ignorasse o zoom da Mesa passava (A5), tal como
        um fim a 2,07 em vez de 2,2 (A3). Desenha-se tambem 3,0, ao pixel;
      - "chega ao fim a andar" nao era medido, e uma curva que chegasse ao zoom aos 90% e
        parasse passava (A2b). Mede-se o zoom que vai ao ecra no principio e no fim;
      - o compor_visivel() amostra so o que se ve; tem de dar o mesmo pixel que o compor().
    """
    import contextlib
    import io
    import random
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aprox_")
    foto = _foto_com_marca(pasta)
    fs = render.encaixar(Image.new("RGB", APROXIMA_FOTO), int(1920 * 1.12), int(1080 * 1.12))
    um = (APROXIMA_MARCA + 1) * fs.width / (1.12 * APROXIMA_FOTO[0])   # a marca a zoom 1

    # 1. O PRIMEIRO FOTOGRAMA E O DE HOJE, com fiel e com fundo.
    prontos = {}
    for trat in ("fiel", "fundo"):
        hoje = render.preparar(_clip_aproxima(foto, "Zoom in", tratamento=trat), {})
        with contextlib.redirect_stdout(io.StringIO()):
            perto = render.preparar(_clip_aproxima(foto, "Aproxima 2.2", tratamento=trat), {})
        prontos[trat] = (hoje, perto)
        if render.desenhar(hoje, 0.0, 5.0).tobytes() != render.desenhar(perto, 0.0, 5.0).tobytes():
            problemas.append("o primeiro fotograma do aproxima com %s nao e o de hoje" % trat)

    # 2. O FIM: a marca ao centro e com o tamanho do zoom pedido, ao pixel.
    fins = []
    for trat, mov, az in (("fiel", "Aproxima 2.2", 2.2), ("fiel", "Aproxima 3", 3.0),
                          ("fundo", "Aproxima 3", 3.0)):
        if mov == "Aproxima 2.2":
            pronto = prontos[trat][1]
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                pronto = render.preparar(_clip_aproxima(foto, mov, tratamento=trat), {})
        caixa = _caixa_da_marca(render.desenhar(pronto, 5.0, 5.0))
        if caixa is None:
            problemas.append("com %s e %s a marca nao aparece no fim" % (trat, mov))
            continue
        cx, cy = (caixa[0] + caixa[2]) / 2.0, (caixa[1] + caixa[3]) / 2.0
        largura = caixa[2] - caixa[0]
        fins.append("%s %.1f: %d px" % (trat, az, largura))
        if abs(cx - 960) > 2 or abs(cy - 540) > 2:
            problemas.append("com %s e %s a marca acaba em %.1f,%.1f e nao ao centro"
                             % (trat, mov, cx, cy))
        if abs(largura - um * az) > 2:
            problemas.append("com %s e %s a marca acaba com %d px e ao zoom %.1f devia ter %.1f"
                             % (trat, mov, largura, az, um * az))

    # 3. A CURVA, no zoom que vai ao ecra: sai do repouso e chega em repouso, porque a seguir
    # vem o segundo parado no anel (APROXIMA_PARADO). Com o arrancar(), que chegava a andar,
    # o fim parava a seco a 94% (verificador, 18 de setembro).
    def curva(ap):
        media = ap["az"] - 1.0
        comeco = (_zoom_mostrado(render, ap, 0.02) - _zoom_mostrado(render, ap, 0.0)) / 0.02
        fecho = (_zoom_mostrado(render, ap, 1.0) - _zoom_mostrado(render, ap, 0.95)) / 0.05
        return comeco / media, fecho / media

    ap = prontos["fiel"][1]["aproxima"]
    comeco, fecho = curva(ap)
    if comeco > 0.1:
        problemas.append("arranca a andar: %.2f da velocidade media logo no principio" % comeco)
    if fecho > 0.2:
        problemas.append("chega ao fim a andar: %.2f da velocidade media no ultimo vigesimo"
                         % fecho)
    if abs(_zoom_mostrado(render, ap, 1.0) - 2.2) > 1e-6:
        problemas.append("no fim o zoom mostrado e %.4f e nao 2,2" % _zoom_mostrado(render, ap, 1.0))

    # 4. O COMPOR_VISIVEL DA O MESMO PIXEL QUE O COMPOR, em "fiel" e em "fundo".
    rnd = random.Random(18)
    for modo in ("preto", "esticar"):
        sprite = render.com_margem(render.encaixar(Image.open(foto).convert("RGB"), 1500, 1000), modo)
        for _k in range(12):
            escala = rnd.uniform(0.9, 1.6)
            cx, cy = rnd.uniform(-300, 2200), rnd.uniform(-300, 1400)
            a = Image.new("RGB", (1920, 1080), (30, 60, 90))
            b = a.copy()
            render.compor(a, sprite, cx, cy, escala)
            render.compor_visivel(b, sprite, cx, cy, escala)
            if a.tobytes() != b.tobytes():
                problemas.append("o compor_visivel deu outro pixel que o compor (%s, %.3f)"
                                 % (modo, escala))
                break

    # MUTACAO 1: um sprite so, o maior, desde o principio. O primeiro fotograma passa a
    # ser uma reducao feita pelo transform(), que serrilha, e deixa de ser o de hoje.
    hoje, perto = prontos["fiel"]
    certo = render.aproxima_nivel
    try:
        render.aproxima_nivel = lambda ap_, nivel: certo(ap_, 7)
        igual = render.desenhar(hoje, 0.0, 5.0).tobytes() == render.desenhar(perto, 0.0, 5.0).tobytes()
    finally:
        render.aproxima_nivel = certo
        perto["aproxima"]["_nivel"] = None
    if igual:
        problemas.append("com um sprite so o primeiro fotograma continuou igual: a medida "
                         "nao diz nada sobre de onde vem o pixel")
    # MUTACOES 2 e 3: a curva linear arranca a andar; a do arrancar() chega a andar e para a
    # seco. As duas acabam no mesmo sitio, e so a curva medida as separa.
    certa = render.aproxima_curva
    for rotulo, falsa, indice in (
            ("linear", lambda t: max(0.0, min(1.0, t)), 0),
            ("do arrancar()", render.arrancar, 1)):
        try:
            render.aproxima_curva = falsa
            medida = curva(ap)
        finally:
            render.aproxima_curva = certa
            ap["_nivel"] = None
        if (indice == 0 and medida[0] <= 0.1) or (indice == 1 and medida[1] <= 0.2):
            problemas.append("com a curva %s a medida nao mudou: %.2f e %.2f" % ((rotulo,) + medida))
    # MUTACAO 4: o aproxima a pintar sobre preto no tratamento fundo. E o que o teste antigo
    # deixava passar, porque so desenhava fiel.
    hoje_f, perto_f = prontos["fundo"]
    guardado = perto_f["fundo"]
    try:
        perto_f["fundo"] = None
        igual = render.desenhar(hoje_f, 0.0, 5.0).tobytes() == render.desenhar(perto_f, 0.0, 5.0).tobytes()
    finally:
        perto_f["fundo"] = guardado
    if igual:
        problemas.append("sem o fundo desfocado o primeiro fotograma continuou igual")
    verifica("aproxima comeca no fotograma de hoje e acaba com o foco ao centro",
             not problemas, "; ".join(problemas)[:240] if problemas else
             "fiel e fundo, %s; curva %.2f no principio e %.2f no fim" % (", ".join(fins), comeco, fecho))


def teste_aproxima_entre_os_encadeados():
    """O aproxima so anda depois de a foto entrar, e chega ao zoom pedido antes de a seguinte entrar.

    O PEDIDO, do Tiago: "tens de comecar do plano amplo para verem a arvore de natal". O
    movimento ocupava o clip inteiro, e por isso comecava debaixo do encadeado de entrada,
    com a foto a pesar 3%, e acabava debaixo do de saida. Na foto do anel a arvore via-se
    inteira durante meio segundo, e o zoom pedido so se atingia no ultimo fotograma, com a
    foto a desaparecer (verificador, 18 de setembro).

    Monta-se como o render monta, com ligar_transicoes, uma foto no meio de outras duas com
    0,7 s de encadeado de cada lado, com o tratamento "fundo" da foto do anel:
      - durante o encadeado de entrada todos os fotogramas sao o primeiro, que e o de hoje;
      - no instante em que a seguinte comeca a entrar a marca ja esta ao centro e com o
        tamanho do zoom pedido, e dai ate ao fim o fotograma nao muda;
      - pelo meio anda;
      - num clip curto de mais o movimento volta ao clip inteiro, e o preparar diz porque.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aproxe_")
    foto = _foto_com_marca(pasta)
    fs = render.encaixar(Image.new("RGB", APROXIMA_FOTO), int(1920 * 1.12), int(1080 * 1.12))
    um = (APROXIMA_MARCA + 1) * fs.width / (1.12 * APROXIMA_FOTO[0])   # a marca a zoom 1
    DUR, TRANS, AZ = 5.0, 0.7, 3.0

    def tres(dur, trans):
        clips = []
        for k, mov in enumerate(("Zoom in", "Aproxima %g" % AZ, "Zoom in")):
            c = _clip_aproxima(foto, mov, tratamento="fundo")
            c.update({"ordem": k + 1, "duracao_s": str(dur), "transicao_s": str(trans)})
            clips.append(c)
        render.ligar_transicoes(clips, fim_do_filme=False)
        return clips

    clips = tres(DUR, TRANS)
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        hoje = render.preparar(dict(clips[1], movimento="Zoom in"), {})
        perto = render.preparar(clips[1], {})
    ap = perto["aproxima"]
    if (ap.get("entra"), ap.get("sai")) != (TRANS, TRANS):
        problemas.append("o preparar leu os encadeados %s e %s" % (ap.get("entra"), ap.get("sai")))
    primeiro = render.desenhar(perto, 0.0, DUR).tobytes()
    if primeiro != render.desenhar(hoje, 0.0, DUR).tobytes():
        problemas.append("o primeiro fotograma nao e o de hoje")
    for t in (0.2, 0.5, TRANS - 0.01):
        if render.desenhar(perto, t, DUR).tobytes() != primeiro:
            problemas.append("aos %.2f s, ainda a entrar, a foto ja se mexeu" % t)
            break
    if render.desenhar(perto, 2.5, DUR).tobytes() == primeiro:
        problemas.append("aos 2,5 s a foto ainda nao se mexeu")
    fim = render.desenhar(perto, DUR - TRANS, DUR)
    caixa = _caixa_da_marca(fim)
    if caixa is None:
        problemas.append("quando a seguinte comeca a entrar a marca nao aparece")
    else:
        cx, cy = (caixa[0] + caixa[2]) / 2.0, (caixa[1] + caixa[3]) / 2.0
        largura = caixa[2] - caixa[0]
        if abs(cx - 960) > 2 or abs(cy - 540) > 2 or abs(largura - um * AZ) > 2:
            problemas.append("quando a seguinte comeca a entrar a marca esta em %.1f,%.1f com %d "
                             "px, e devia estar ao centro com %.1f" % (cx, cy, largura, um * AZ))
    for t in (DUR - TRANS + 0.2, DUR - 0.01):
        if render.desenhar(perto, t, DUR).tobytes() != fim.tobytes():
            problemas.append("aos %.2f s, com a seguinte a entrar, a foto ainda se mexe" % t)
            break
    # MUTACAO: o movimento no clip inteiro, como estava. A foto mexe-se a entrar e o fim
    # ainda nao chegou ao zoom quando a seguinte comeca.
    guardados = ap["entra"], ap["sai"]
    parado_certo = render.APROXIMA_PARADO
    try:
        ap["entra"], ap["sai"] = 0.0, 0.0
        render.APROXIMA_PARADO = 0.0
        mexe = render.desenhar(perto, 0.5, DUR).tobytes() != primeiro
        fim_m = render.desenhar(perto, DUR - TRANS, DUR).tobytes()
    finally:
        ap["entra"], ap["sai"] = guardados
        render.APROXIMA_PARADO = parado_certo
    if not mexe or fim_m == fim.tobytes():
        problemas.append("com o movimento no clip inteiro a medida nao mudou")
    # O CLIP CURTO DE MAIS: 2 s com 0,7 de cada lado deixava 0,6 s para ir de 1 a 3.
    curtos = tres(2.0, TRANS)
    saida_c = io.StringIO()
    with contextlib.redirect_stdout(saida_c):
        curto = render.preparar(curtos[1], {})
    if render.aproxima_progresso(curto["aproxima"], 0.5, 2.0) <= 0.0 or \
            "ocupa o clip inteiro" not in saida_c.getvalue():
        problemas.append("no clip de 2 s o movimento nao voltou ao clip inteiro com aviso: %r"
                         % saida_c.getvalue().strip()[-120:])
    if "ocupa o clip inteiro" in saida.getvalue():
        problemas.append("o clip de 5 s tambem avisou que era curto")

    # O FIM DO MOVIMENTO, MEDIDO E NAO SO VISTO PARADO. Olhar para o fotograma quando a
    # seguinte comeca a entrar e para os de depois deixava passar um movimento que chegasse
    # ao zoom 0,3 s antes e parasse ali de repente (verificador, mutacao A3b): parado ao
    # centro e com o tamanho certo, igual ao fotograma final. Mede-se o zoom que vai ao ecra
    # pelo caminho do desenhar() em DUR - TRANS - 0,1 e - 0,04: tem de ser o do arrancar()
    # contado na janela entre os dois encadeados, ainda abaixo do pedido e a crescer.
    vistos = []
    certo_q = render.aproxima_quadro

    def espia(ap_, p):
        feito = certo_q(ap_, p)
        vistos.append((feito[0].width - 2 * render.MARGEM) * feito[1] / ap_["fw"])
        return feito

    def zoom_desenhado(pronto_, t, dur):
        del vistos[:]
        try:
            render.aproxima_quadro = espia
            render.desenhar(pronto_, t, dur)
        finally:
            render.aproxima_quadro = certo_q
        return vistos[-1] if vistos else None

    # AS DUAS PARAGENS DO TIAGO, escritas aqui e nao lidas do render: um segundo parado no
    # plano amplo depois de a foto entrar, e um no anel antes de a seguinte comecar.
    PARADO = 1.0
    a_mov, b_mov = TRANS + PARADO, DUR - TRANS - PARADO

    def zoom_certo(t, a, b):
        p = min(1.0, max(0.0, (t - a) / (b - a)))
        return 1.0 + (AZ - 1.0) * p * p * (3.0 - 2.0 * p)

    fins_m = []
    for antes_s in (0.1, 0.04):
        t = b_mov - antes_s
        z = zoom_desenhado(perto, t, DUR)
        fins_m.append(z)
        certo_z = zoom_certo(t, a_mov, b_mov)
        if z is None or abs(z - certo_z) > 1e-3 or z >= AZ - 1e-6:
            problemas.append("%.2f s antes de parar no anel o zoom mostrado e %s, e com a curva "
                             "na janela devia ser %.4f, ainda abaixo de %.1f"
                             % (antes_s, z if z is None else "%.4f" % z, certo_z, AZ))
    if None not in fins_m and fins_m[1] <= fins_m[0]:
        problemas.append("no fim da janela o zoom ja nao cresce: %.4f e %.4f" % tuple(fins_m))
    if render.desenhar(perto, a_mov - 0.02, DUR).tobytes() != primeiro:
        problemas.append("antes de acabar o segundo parado no plano amplo a foto ja se mexeu")
    if render.desenhar(perto, b_mov + 0.02, DUR).tobytes() != fim.tobytes():
        problemas.append("depois de chegar ao anel a foto nao ficou parada ate a seguinte entrar")

    # ENCADEADOS DIFERENTES A ENTRAR E A SAIR. Com o mesmo 0,7 s dos dois lados, um preparar
    # que lesse so um deles, ou o encadeado do proprio clip no lugar do de entrada, passava
    # (verificador, mutacoes A11 e A12). Montam-se tres casos com ligar_transicoes(): a
    # entrar a corte seco e a sair com encadeado, o contrario, e o aproxima como primeiro
    # clip do corpo, que entra sempre a corte seco mesmo com transicao_s de 0,7.
    def monta(movs, transicoes):
        clips = []
        for k, (mov, trans) in enumerate(zip(movs, transicoes)):
            c = _clip_aproxima(foto, mov, tratamento="fundo")
            c.update({"ordem": k + 1, "duracao_s": str(DUR), "transicao_s": str(trans)})
            clips.append(c)
        render.ligar_transicoes(clips, fim_do_filme=False)
        return clips

    mov_a = "Aproxima %g" % AZ
    casos_e = [("a entrar a seco e a sair com 0,7", ["Zoom in", mov_a, "Zoom in"], [0.7, 0.0, 0.7], 1, 0.0, 0.7),
               ("a entrar com 0,7 e a sair a seco", ["Zoom in", mov_a, "Zoom in"], [0.7, 0.7, 0.0], 1, 0.7, 0.0),
               ("primeiro clip do corpo", [mov_a, "Zoom in"], [0.7, 0.7], 0, 0.0, 0.7)]

    def anda_na_janela(pronto_, entra, sai):
        """O que falha na agenda do movimento com estes encadeados, ou [].

        O movimento anda entre o fim do encadeado de entrada mais o segundo parado no plano
        amplo, e o comeco do de saida menos o segundo parado no fim; sem encadeado de saida
        continua a parar um segundo antes do fim do clip, para o anel se ver.
        """
        maus = []
        parado = min(PARADO, (DUR - entra - sai - 1.0) / 2.0)
        a_, b_ = entra + parado, DUR - sai - parado
        zero = render.desenhar(pronto_, 0.0, DUR).tobytes()
        if render.desenhar(pronto_, a_ - 0.01, DUR).tobytes() != zero:
            maus.append("mexe-se antes de acabar o encadeado de entrada e o segundo parado")
        if render.desenhar(pronto_, a_ + 0.3, DUR).tobytes() == zero:
            maus.append("0,3 s depois do segundo parado ainda nao se mexeu")
        fim_ = render.desenhar(pronto_, b_ + 0.02, DUR).tobytes()
        if render.desenhar(pronto_, DUR - 0.01, DUR).tobytes() != fim_:
            maus.append("ainda se mexe no segundo parado do fim")
        if render.desenhar(pronto_, b_ - 0.08, DUR).tobytes() == fim_:
            maus.append("ja estava parado antes do segundo parado do fim")
        return maus

    medidos_e = 0
    for rotulo_e, movs, trans, qual, entra_c, sai_c in casos_e:
        clips_e = monta(movs, trans)
        with contextlib.redirect_stdout(io.StringIO()):
            pronto_e = render.preparar(clips_e[qual], {})
        ap_e = pronto_e["aproxima"]
        if (ap_e.get("entra"), ap_e.get("sai")) != (entra_c, sai_c):
            problemas.append("%s: o preparar leu os encadeados %s e %s, e sao %s e %s"
                             % (rotulo_e, ap_e.get("entra"), ap_e.get("sai"), entra_c, sai_c))
            continue
        maus = anda_na_janela(pronto_e, entra_c, sai_c)
        if maus:
            problemas.append("%s: %s" % (rotulo_e, "; ".join(maus)))
        medidos_e += 1
        # MUTACOES da leitura, postas no que o preparar guardou: a saida igual a entrada
        # (A11) e a entrada tirada do proprio clip (A12). A medida dos fotogramas tem de ver
        # a que muda alguma coisa neste caso.
        for rot_m, entra_m, sai_m in (("sai = entra", entra_c, entra_c),
                                      ("a entrada do proprio clip", float(clips_e[qual]["transicao_s"]), sai_c)):
            if (entra_m, sai_m) == (entra_c, sai_c):
                continue
            try:
                ap_e["entra"], ap_e["sai"] = entra_m, sai_m
                viu = anda_na_janela(pronto_e, entra_c, sai_c)
            finally:
                ap_e["entra"], ap_e["sai"] = entra_c, sai_c
            if not viu:
                problemas.append("%s: com %s a medida dos fotogramas nao mudou" % (rotulo_e, rot_m))
    verifica("aproxima anda entre os encadeados", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "parado nos %.1f s de entrada, %.1f vezes ao centro quando a seguinte entra, e parado "
             "dai ao fim; a %.4f e %.4f 0,1 e 0,04 s antes; %d casos de encadeados diferentes"
             % (TRANS, AZ, fins_m[0], fins_m[1], medidos_e))


def teste_aproxima_nunca_descobre_borda():
    """Ao fechar, a borda da foto nunca entra no quadro.

    A foto encaixada comeca com as suas barras, que sao o aspeto da mae da Clara. Dai para
    a frente o preto so pode DIMINUIR: se a aproximacao arrastasse a foto ate ao ponto de
    foco sem olhar a onde ela acaba, entrava fundo por um dos lados a meio do movimento, e
    numa foto com fundo desfocado isso le-se como um erro, nao como um enquadramento.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aproxb_")
    # DUAS FOTOS, porque ha duas maneiras de isto correr mal. A larga acaba a encher o
    # ecra, e ai a borda tem de desaparecer de vez; a alta e a do anel, que nem ao zoom
    # 2,2 chega aos 1920 de largura: fica com as barras dela ate ao fim, e o que nao pode
    # acontecer e uma delas CRESCER para o lado do ponto de foco.
    larga = _foto_com_marca(pasta, "larga.png")
    alta = _foto_com_marca(pasta, "alta.png", (2000, 3000), (0.30, 0.70))
    # A TERCEIRA E A FORMA DA DO ANEL (3024x3661, o foco onde ele o marcou): ao alto, so
    # passa a cobrir a largura do ecra perto do fim, e ai o travao prende o fim encostado a
    # borda. E o caso em que um centro sem guarda acaba com borda a mostra.
    anel = _foto_com_marca(pasta, "anel.png", (3024, 3661), (0.393, 0.741))
    focos_de = {"larga": APROXIMA_FOCO, "alta": (0.30, 0.70), "anel": (0.393, 0.741)}
    fotos_de = {"larga": larga, "alta": alta, "anel": anel}

    def prepara_todas():
        with contextlib.redirect_stdout(io.StringIO()):
            return {q: render.preparar(_clip_aproxima(fotos_de[q], "Aproxima 2.2", foco=focos_de[q]), {})
                    for q in fotos_de}

    prontos = prepara_todas()

    def barras(qual, p):
        """(pixeis pretos, os da metade esquerda, os da direita) no instante p."""
        im = render.desenhar(prontos[qual], 5.0 * p, 5.0).convert("L")
        esq = sum(1 for v in im.crop((0, 0, 960, 1080)).getdata() if v == 0)
        dto = sum(1 for v in im.crop((960, 0, 1920, 1080)).getdata() if v == 0)
        return esq + dto, esq, dto

    def mede(qual):
        contas = [barras(qual, q / 20.0) for q in range(21)]
        maus = []
        for q in range(1, len(contas)):
            if contas[q][0] > contas[q - 1][0]:
                maus.append("%s: o preto subiu de %d para %d no passo %d"
                            % (qual, contas[q - 1][0], contas[q][0], q))
                break
        # E NENHUMA DAS BARRAS CRESCE. Desde 18 de setembro a tarde o centro anda em linha
        # recta ate ao fim (aproxima_quadro()), e por isso uma foto que fecha num ponto fora
        # do meio perde primeiro a barra do lado para onde vai: as duas barras deixam de ser
        # iguais a meio, e isso e o movimento, nao um defeito. O defeito que isto guarda e
        # uma barra a CRESCER enquanto a outra desaparece, que e a borda a entrar por um lado.
        for lado_, i in (("esquerda", 1), ("direita", 2)):
            for q in range(1, len(contas)):
                if contas[q][i] > contas[q - 1][i]:
                    maus.append("%s: a barra da %s cresceu de %d para %d no passo %d"
                                % (qual, lado_, contas[q - 1][i], contas[q][i], q))
                    break
        # E NO FIM, NUM EIXO QUE A FOTO NAO COBRE, AS BARRAS SAO AS DELA: iguais dos dois
        # lados, com a foto ao meio, como o aproxima_centro() a poe.
        tudo, esq, dto = contas[-1]
        if tudo and abs(esq - dto) > 1200:
            maus.append("%s: no fim a barra da esquerda tem %d pixeis e a da direita %d"
                        % (qual, esq, dto))
        return contas, maus

    medidas_b = {}
    for q in ("larga", "alta", "anel"):
        medidas_b[q], maus = mede(q)
        problemas += maus
    contas_larga, contas_alta = medidas_b["larga"], medidas_b["alta"]
    for q in ("larga", "anel"):
        if medidas_b[q][-1][0] != 0:
            problemas.append("a %s acaba com %d pixeis de borda" % (q, medidas_b[q][-1][0]))
    if min(medidas_b[q][0][0] for q in medidas_b) < 10000:
        problemas.append("as fotos de ensaio nao tem barras nenhumas no inicio (%s): o teste "
                         "nao estava a medir nada" % [medidas_b[q][0][0] for q in medidas_b])
    if contas_alta[-1][0] == 0:
        problemas.append("a foto alta acabou a encher o ecra: o caso em que a foto acaba "
                         "antes deixou de estar medido")
    # MUTACAO: o fim sem a guarda, a ir sempre para o ponto de foco. E a versao ingenua, a
    # que parece certa ate se olhar para o fotograma. O fim e planeado no preparar, e por
    # isso prepara-se outra vez com ela. Na larga o ponto de foco ja fica ao centro no fim
    # e a guarda nao tem nada a fazer; na alta e na do anel tem, e a medida tem de o ver.
    certo = render.aproxima_centro
    try:
        render.aproxima_centro = lambda lado, tamanho, f: lado / 2.0 - (f - 0.5) * tamanho
        prontos = prepara_todas()
        soltas = {}
        for q in ("alta", "anel"):
            contas_m, maus_m = mede(q)
            soltas[q] = maus_m + (["acaba com borda"] if q == "anel" and contas_m[-1][0] else [])
    finally:
        render.aproxima_centro = certo
        prontos = prepara_todas()
    sem_queixa = [q for q, m in soltas.items() if not m]
    if sem_queixa:
        problemas.append("sem a guarda a borda continuou sem aparecer em %s: a medida nao "
                         "distingue as duas versoes" % ", ".join(sem_queixa))
    # A FILA DE FORA, quando o travao encosta a foto ao cimo ou ao fundo do ecra. O teste de
    # cima so contava pixeis iguais a 0, e as duas fotos arredondavam certo. O verificador
    # (18 de setembro) mediu, numa foto de 2248x4000 com o foco a 0,2 de altura, a fila 0 a
    # valer 36, 101, 0 e 86 sobre uma foto a 124, a mudar a cada troca de nivel: o travao
    # usava a altura do nivel 0 e desenhava o sprite de outro. E mesmo com a altura certa, a
    # foto encostada ao pixel dava a fila 0 a 210 sobre 200, com o bicubico a ir buscar a
    # margem. Numa foto lisa, a fila de fora tem de ser a propria foto.
    lisa = os.path.join(pasta, "lisa.png")
    Image.new("RGB", (2248, 4000), (200, 200, 200)).save(lisa)
    filas = []

    def fila_de_fora(trat, foco):
        """(fotogramas medidos, os que tem a fila de fora diferente da foto)."""
        with contextlib.redirect_stdout(io.StringIO()):
            pr = render.preparar(_clip_aproxima(lisa, "Aproxima 2.2", foco=foco, tratamento=trat), {})
        ap_ = pr["aproxima"]
        medidos, maus = 0, []
        for q in range(0, 126, 3):
            p = q / 125.0
            _sp, escala_, _cx, cy_ = render.aproxima_quadro(ap_, p)
            alt_ = (_sp.height - 2 * render.MARGEM) * escala_
            if alt_ < 1080 + 2 * render.APROXIMA_SOBRA + 1:
                continue        # ainda nao cobre a altura: as barras sao as dela
            a_j, b_j = render.aproxima_janela(5.0, ap_.get("entra", 0.0), ap_.get("sai", 0.0))
            im = render.desenhar(pr, a_j + p * (b_j - a_j), 5.0).convert("L")
            fora, dentro = (0, 4) if foco[1] < 0.5 else (1079, 1075)
            a = im.crop((900, fora, 1020, fora + 1)).tobytes()
            b = im.crop((900, dentro, 1020, dentro + 1)).tobytes()
            medidos += 1
            if abs(sum(a) / 120.0 - sum(b) / 120.0) > 3:
                maus.append("%.2f s: %.0f contra %.0f" % (5.0 * p, sum(a) / 120.0, sum(b) / 120.0))
        return medidos, maus

    for trat, foco in (("fiel", (0.5, 0.2)), ("fundo", (0.5, 0.2)), ("fiel", (0.5, 0.85))):
        medidos, maus = fila_de_fora(trat, foco)
        filas.append(medidos)
        if not medidos:
            problemas.append("com %s e foco %s a foto nunca cobriu a altura: nada medido" % (trat, foco))
        if maus:
            problemas.append("com %s e foco %s a fila de fora nao e a foto: %s"
                             % (trat, foco, "; ".join(maus[:3])))
    # MUTACAO: a foto encostada ao pixel, sem a sobra. E o defeito que ficava depois de
    # acertar a altura, e a medida tem de o ver.
    guardada = render.APROXIMA_SOBRA
    try:
        render.APROXIMA_SOBRA = 0
        _m, maus = fila_de_fora("fiel", (0.5, 0.2))
    finally:
        render.APROXIMA_SOBRA = guardada
    if not maus:
        problemas.append("com a foto encostada ao pixel a fila de fora continuou igual: a "
                         "medida nao ve a borda")
    # A MARGEM DOS NIVEIS COM FUNDO. Cada nivel e um sprite novo, e com o fundo desfocado a
    # margem tem de repetir a fila de fora com alfa zero, como a do nivel 0 (com_margem
    # "esticar"). Com margem preta, a borda da foto ganhava um risco escuro por cima do
    # fundo a cada troca de nivel (verificador, mutacao A14).
    with contextlib.redirect_stdout(io.StringIO()):
        pr_f = render.preparar(_clip_aproxima(lisa, "Aproxima 2.2", foco=(0.5, 0.2),
                                              tratamento="fundo"), {})
    nivel_alto = render.aproxima_nivel_de(2.0)
    sp_alto, _f = render.aproxima_nivel(pr_f["aproxima"], nivel_alto)
    if sp_alto.mode != "RGBA" or sp_alto.getpixel((0, sp_alto.height // 2))[:3] != (200, 200, 200):
        problemas.append("o nivel %d com fundo tem a margem %s %s, e devia repetir a foto com "
                         "alfa zero" % (nivel_alto, sp_alto.mode, sp_alto.getpixel((0, sp_alto.height // 2))))
    im_f = render.desenhar(pr_f, 5.0 * 0.8, 5.0).convert("L")
    linha = list(im_f.crop((0, 540, 1920, 541)).tobytes())
    x_foto = next((x for x in range(960, 0, -1) if linha[x] < 195), None)
    if x_foto is None or min(linha[x_foto - 3:x_foto + 1]) < min(linha[x_foto - 20], 200) - 3:
        problemas.append("com fundo, a borda da foto tem um risco escuro: %s"
                         % (linha[x_foto - 6:x_foto + 3] if x_foto else "sem borda"))
    # E A CONTA DO TRAVAO E FEITA COM O SPRITE QUE VAI AO ECRA. A sobra de 3 px tapava o
    # defeito do nivel 0 nesta foto, e por isso a medida dos pixeis nao o via: com a altura
    # do nivel 0 (fh . r) e o sprite de outro nivel, a borda ficava a 2,55 px fora do ecra e
    # nao a 3, e uma foto com outro arredondamento voltava a pisca-la (verificador, mutacao
    # B1). Mede-se a geometria: no eixo que a foto ja enche no primeiro fotograma, sempre que
    # ela o cobre cada borda fica pelo menos APROXIMA_SOBRA px fora dele, contada no sprite
    # desenhado. No outro eixo a foto comeca com barras, a borda anda sempre para fora e so
    # tem de chegar la no fim (ver aproxima_quadro()): mede-se no ultimo instante.
    def fora_do_ecra(quadro, ap_):
        maus = []
        for q in range(0, 201):
            sp_, esc_, cx_, cy_ = quadro(ap_, q / 200.0)
            for lado, tam, c, enche in ((1920, (sp_.width - 2 * render.MARGEM) * esc_, cx_, ap_["enche"][0]),
                                        (1080, (sp_.height - 2 * render.MARGEM) * esc_, cy_, ap_["enche"][1])):
                if (enche or q == 200) and tam >= lado + 2 * render.APROXIMA_SOBRA and (
                        c - tam / 2.0 > -render.APROXIMA_SOBRA + 1e-6 or
                        c + tam / 2.0 < lado + render.APROXIMA_SOBRA - 1e-6):
                    maus.append("p %.3f: de %.2f a %.2f em %d" % (q / 200.0, c - tam / 2.0,
                                                                   c + tam / 2.0, lado))
        return maus

    def travao_do_nivel_0(ap_, p):
        """A conta de antes: o tamanho do nivel 0 vezes r, com o sprite do nivel de agora."""
        r_ = 1.0 + (ap_["az"] - 1.0) * render.aproxima_curva(p)
        sp_, fator_ = render.aproxima_nivel(ap_, render.aproxima_nivel_de(r_))
        return (sp_, r_ * fator_, render.aproxima_centro(1920, ap_["fw"] * r_, ap_["foco"][0]),
                render.aproxima_centro(1080, ap_["fh"] * r_, ap_["foco"][1]))

    geometria = 0
    # A do anel e a unica que passa a cobrir a largura so perto do fim, com o fim preso a
    # borda: e ai que a borda de fora tem de acabar a APROXIMA_SOBRA px, nem mais nem menos.
    lisa_anel = os.path.join(pasta, "lisa_anel.png")
    Image.new("RGB", (3024, 3661), (200, 200, 200)).save(lisa_anel)
    for foto_g, foco in ((lisa, (0.5, 0.2)), (lisa, (0.5, 0.85)), (lisa, (0.1, 0.5)),
                         (lisa_anel, (0.393, 0.741))):
        with contextlib.redirect_stdout(io.StringIO()):
            ap_g = render.preparar(_clip_aproxima(foto_g, "Aproxima 2.2", foco=foco), {})["aproxima"]
        maus = fora_do_ecra(render.aproxima_quadro, ap_g)
        if maus:
            problemas.append("com o foco %s a borda fica dentro da sobra: %s" % (foco, "; ".join(maus[:2])))
        geometria += 201
        if foco == (0.5, 0.2) and not fora_do_ecra(travao_do_nivel_0, ap_g):
            problemas.append("com o travao contado no nivel 0 a geometria continuou certa: a "
                             "medida nao ve o defeito")
    verifica("aproxima nunca descobre borda", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "larga de %d pixeis de barra a 0, alta de %d a %d; fila de fora igual a foto em %s "
             "fotogramas; borda a %d px fora em %d instantes"
             % (contas_larga[0][0], contas_alta[0][0], contas_alta[-1][0], "+".join(str(f) for f in filas),
                render.APROXIMA_SOBRA, geometria))


def teste_aproxima_anda_sem_quebras():
    """O caminho do aproxima nao tem quebras de velocidade nem inversoes: todo o ecra anda com a curva.

    O DEFEITO, medido pelo verificador a 18 de setembro na foto do anel (f0260, 6,6 s, 0,7 s
    de encadeado de cada lado): o travao da borda era aplicado fotograma a fotograma ao
    centro ideal de cada zoom, e cada vez que prendia ou largava um eixo a velocidade mudava
    de repente. A 2,2, a pedra deixava de subir aos 4,94 s e aos 5,74 s dava uma guinada
    para a direita, com o ecra a passar de 5,1 para 9,0 px por fotograma; a 2,8, ia para a
    esquerda e voltava para a direita aos 4,4 s, e o ecra saltava de 9,5 para 17. Sem saltos
    de posicao, so de velocidade, e a 15 metros isso le-se como a imagem a dar um toque.

    Mede-se o que vai ao ecra fotograma a fotograma, pelo aproxima_progresso() e pelo
    aproxima_quadro() que o desenhar() usa, na forma da foto do anel a 2,2 e a 2,8 e numa foto
    deitada a 3,0: a pedra (o ponto de foco) nunca muda de sentido, e nem ela nem o ponto do
    ecra que mais anda tem quebras. Uma quebra e a mudanca de velocidade a SALTAR: com a
    curva do arrancar() a velocidade muda sempre um pouco de fotograma para fotograma, e
    isso e o movimento; o que nao pode e essa mudanca passar de repente de quase nada para
    varios pixeis. Medido a 18 de setembro: com o caminho de antes o salto era de 2,7 a 8,7
    px por fotograma, com o de agora nunca passa de 0,6 (as trocas de nivel do sprite, que
    arredondam a altura). O limite e 1.
    Fica de fora o primeiro decimo do movimento: ai o travao do eixo que a foto ja enche
    (ver aproxima_quadro()) segura a borda com a foto quase parada, e a pedra desce menos de
    2 px antes de subir, abaixo do que se ve.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aproxq_")
    DUR, TRANS, FPS = 6.6, 0.7, 25
    casos = [("anel 2,2", (3024, 3661), (0.393, 0.741), 2.2), ("anel 2,8", (3024, 3661), (0.393, 0.741), 2.8),
             ("deitada 3,0", APROXIMA_FOTO, APROXIMA_FOCO, 3.0)]
    fotos = {}

    def mede(ap, foco):
        """(pior salto da pedra, pior salto do ecra, inversoes, fotogramas medidos) no movimento.

        O salto e a diferenca entre duas mudancas de velocidade seguidas, em px por fotograma.
        """
        # o movimento fica entre o segundo parado no plano amplo e o do fim (APROXIMA_PARADO)
        parado = min(1.0, (DUR - 2 * TRANS - 1.0) / 2.0)
        a, b = TRANS + parado, DUR - TRANS - parado
        pontos = []
        for k in range(int(round(DUR * FPS)) + 1):
            t = k / float(FPS)
            if t < a + 0.1 * (b - a) or t > b:
                continue
            sp, esc, cx, cy = render.aproxima_quadro(ap, render.aproxima_progresso(ap, t, DUR))
            larg, alt = (sp.width - 2 * render.MARGEM) * esc, (sp.height - 2 * render.MARGEM) * esc
            pontos.append((cx, cy, larg, alt))
        pedra, ecra, inversoes = 0.0, 0.0, []
        vels, fluxos = [], []
        for (cx0, cy0, l0, a0), (cx1, cy1, l1, a1) in zip(pontos, pontos[1:]):
            vels.append((cx1 + (foco[0] - 0.5) * l1 - cx0 - (foco[0] - 0.5) * l0,
                         cy1 + (foco[1] - 0.5) * a1 - cy0 - (foco[1] - 0.5) * a0))
            # o ponto do ecra que mais anda e um dos cantos: o ponto da foto que esta nele
            # vai para c1 + u . T1
            pior = 0.0
            for sx, sy in ((0, 0), (1920, 0), (0, 1080), (1920, 1080)):
                ux, uy = (sx - cx0) / l0, (sy - cy0) / a0
                pior = max(pior, math.hypot(cx1 + ux * l1 - sx, cy1 + uy * a1 - sy))
            fluxos.append(pior)
        def saltos(serie):
            muda = [serie[k] - serie[k - 1] for k in range(1, len(serie))]
            return [abs(muda[k] - muda[k - 1]) for k in range(1, len(muda))] or [0.0]
        pedra = max(max(saltos([v[0] for v in vels])), max(saltos([v[1] for v in vels])))
        ecra = max(saltos(fluxos))
        for eixo in (0, 1):
            sinais = [1 if v[eixo] > 0.05 else -1 for v in vels if abs(v[eixo]) > 0.05]
            if any(x != y for x, y in zip(sinais, sinais[1:])):
                inversoes.append("xy"[eixo])
        return pedra, ecra, inversoes, len(pontos)

    def prepara(rotulo, tamanho, foco, az):
        if tamanho not in fotos:
            fotos[tamanho] = _foto_com_marca(pasta, "q%dx%d.png" % tamanho, tamanho, foco)
        clip = _clip_aproxima(fotos[tamanho], "Aproxima %g" % az, foco=foco, tratamento="fundo")
        clip.update({"duracao_s": str(DUR), "transicao_s": str(TRANS)})
        with contextlib.redirect_stdout(io.StringIO()):
            return render.preparar(clip, {})["aproxima"]

    resumo = []
    aps = {}
    for rotulo, tamanho, foco, az in casos:
        aps[rotulo] = (prepara(rotulo, tamanho, foco, az), foco)
        pedra, ecra, inversoes, n = mede(*aps[rotulo])
        resumo.append("%s %.2f/%.2f" % (rotulo, pedra, ecra))
        # 3,2 s de movimento entre as duas paragens, menos o primeiro decimo: 72 fotogramas
        if n < 60:
            problemas.append("%s: so %d fotogramas medidos" % (rotulo, n))
        if inversoes:
            problemas.append("%s: a pedra muda de sentido em %s" % (rotulo, "".join(inversoes)))
        if pedra > 1.0 or ecra > 1.0:
            problemas.append("%s: a velocidade muda de repente, saltos de %.2f px por fotograma na "
                             "pedra e %.2f no ecra" % (rotulo, pedra, ecra))

    # MUTACOES: o travao fotograma a fotograma ao centro ideal, que e o de antes, e o travao
    # tambem no eixo que a foto so cobre no fim, que da um salto quando ela o passa a cobrir.
    certo = render.aproxima_quadro

    def de_antes(ap, p):
        sp, esc, _cx, _cy = certo(ap, p)
        larg, alt = (sp.width - 2 * render.MARGEM) * esc, (sp.height - 2 * render.MARGEM) * esc
        return (sp, esc, render.aproxima_centro(1920, larg, ap["foco"][0]),
                render.aproxima_centro(1080, alt, ap["foco"][1]))

    def trava_tudo(ap, p):
        sp, esc, cx, cy = certo(ap, p)
        larg, alt = (sp.width - 2 * render.MARGEM) * esc, (sp.height - 2 * render.MARGEM) * esc
        return sp, esc, render.aproxima_trava(1920, larg, cx), render.aproxima_trava(1080, alt, cy)

    for rotulo_m, falsa in (("de antes", de_antes), ("com o travao nos dois eixos", trava_tudo)):
        try:
            render.aproxima_quadro = falsa
            pedra, ecra, inversoes, _n = mede(*aps["anel 2,2"])
        finally:
            render.aproxima_quadro = certo
        if pedra <= 1.0 and ecra <= 1.0 and not inversoes:
            problemas.append("com o caminho %s a medida nao mudou (%.2f, %.2f)" % (rotulo_m, pedra, ecra))
    verifica("aproxima anda sem quebras nem inversoes", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "pior salto de velocidade, pedra/ecra em px por fotograma: " + ", ".join(resumo))


def teste_aproxima_sem_foco_vai_ao_centro_e_avisa():
    """Sem ponto de foco marcado, fecha ao centro da foto, e diz que foi isso que fez.

    O SILENCIO E QUE SERIA MAU: a Mesa deixa marcar o ponto de foco mas nao obriga, e um
    clip que feche ao centro quando ele queria fechar na cara de alguem e um clip que ele
    so descobre no jantar. Fecha ao centro, que e o unico sitio defensavel, e avisa.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aproxf_")
    foto = _foto_com_marca(pasta)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        sem = render.preparar(_clip_aproxima(foto, "Aproxima 2.2", foco=None), {})
        meio = render.preparar(_clip_aproxima(foto, "Aproxima 2.2", foco=(0.5, 0.5)), {})
    if "sem ponto de foco" not in log.getvalue():
        problemas.append("o preparar nao avisou: %r" % log.getvalue()[:120])
    for p in (0.0, 0.5, 1.0):
        a = render.desenhar(sem, 5.0 * p, 5.0).tobytes()
        b = render.desenhar(meio, 5.0 * p, 5.0).tobytes()
        if a != b:
            problemas.append("sem foco, o fotograma em %.1f nao e o do centro" % p)
    marca = _centro_da_marca(render.desenhar(sem, 5.0, 5.0))
    if marca is not None and abs(marca[0] - 960) < 40 and abs(marca[1] - 540) < 40:
        problemas.append("sem foco a marca ficou ao centro na mesma: a foto de ensaio tem "
                         "a marca no meio e o teste nao distingue nada")
    verifica("aproxima sem ponto de foco fecha ao centro e avisa", not problemas,
             "; ".join(problemas)[:200] if problemas else "avisou e desenhou ao centro")


def teste_aproxima_diz_quanto_faltou_e_o_zoom_que_centra():
    """Quando o foco nao chega ao centro, o preparar diz quanto faltou e um zoom que centra MESMO.

    O CONTRATO (A4): se o zoom pedido descobre borda, aproxima-se so ate onde a foto chega, e
    o preparar diz quanto foi. O Tiago decide a partir desta frase, e ela nao era testada: o
    verificador tirou-lhe o "quanto faltou" (A8), dobrou o zoom sugerido (A9) e tirou o aviso
    de foco do montar (M2), e a suite passou nas tres.

    E O NUMERO TEM DE FUNCIONAR QUANDO E ESCRITO. Com as medidas do anel (3024x3661) e o
    foco a 0,3942, o zoom que centra e 2,73: o preparar arredondava ao mais proximo e dizia
    2,7, e com 2,7 posto voltava a queixar-se e a sugerir 2,7. A Mesa dizia 2,8. Agora e o
    mesmo numero nos dois, arredondado para cima, e um decimo abaixo dele ainda nao centra.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aproxav_")
    foco = (0.3942, 0.5)
    # Lisa e com a marca: o padrao do _foto_com_marca() nao faz falta aqui e numa foto do
    # tamanho da do anel levava segundos a desenhar pixel a pixel.
    from PIL import ImageDraw
    anel = os.path.join(pasta, "anel.png")
    lisa = Image.new("RGB", (3024, 3661), (150, 170, 140))
    meia = APROXIMA_MARCA / 2.0
    ImageDraw.Draw(lisa).rectangle([foco[0] * 3024 - meia, foco[1] * 3661 - meia,
                                    foco[0] * 3024 + meia, foco[1] * 3661 + meia], fill=(255, 0, 255))
    lisa.save(anel)

    def prepara(mov, f=foco):
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            pr = render.preparar(_clip_aproxima(anel, mov, foco=f), {})
        return pr, log.getvalue()

    pr, log = prepara("Aproxima 2.2")
    caixa = _caixa_da_marca(render.desenhar(pr, 5.0, 5.0))
    medido = abs((caixa[0] + caixa[2]) / 2.0 - 960) if caixa else None
    m = re.search(r"fica a (\d+) px na largura", log)
    if not m or medido is None or abs(int(m.group(1)) - medido) > 3:
        problemas.append("a 2,2 o preparar disse %r e a marca ficou a %s px do centro"
                         % (log.strip()[-160:], medido))
    m = re.search(r"ficaria ao centro com o zoom (\d+\.\d)", log)
    if not m:
        problemas.append("a 2,2 o preparar nao sugeriu zoom nenhum: %r" % log.strip()[-160:])
    else:
        sugerido = float(m.group(1))
        pr2, log2 = prepara("Aproxima %.1f" % sugerido)
        caixa2 = _caixa_da_marca(render.desenhar(pr2, 5.0, 5.0))
        if "fica a" in log2 or not caixa2 or abs((caixa2[0] + caixa2[2]) / 2.0 - 960) > 2:
            problemas.append("com o zoom sugerido, %.1f, o foco nao ficou ao centro: %r"
                             % (sugerido, log2.strip()[-120:]))
        _pr3, log3 = prepara("Aproxima %.1f" % (sugerido - 0.1))
        if "fica a" not in log3:
            problemas.append("um decimo abaixo do sugerido (%.1f) ja centrava: o sugerido nao e "
                             "o mais pequeno que serve" % (sugerido - 0.1))
    # NEM O MAXIMO CHEGA: diz-se, e nao se sugere um numero que a Mesa nao deixa escrever.
    _pr4, log4 = prepara("Aproxima 2.2", (0.05, 0.5))
    if "nem com o zoom maximo" not in log4 or "ficaria ao centro" in log4:
        problemas.append("com o foco na ponta o preparar disse %r" % log4.strip()[-160:])
    # E PELA MESA: o montar avisa do aproxima sem ponto de foco, e cala-se quando ha um.
    linhas, _som, saida = _monta_em_pasta(
        [{"t": "foto", "i": "f0593", "d": 4, "c": 0.7, "r": "fundo", "e": "aproxima"},
         {"t": "foto", "i": "f0592", "d": 4, "c": 0.7, "r": "fundo", "e": "aproxima"}],
        focos={"f0592": [0.4, 0.6]})
    avisos = [l for l in saida.splitlines() if "sem ponto de foco" in l]
    if len(avisos) != 1 or "clip 1" not in avisos[0]:
        problemas.append("o montar avisou do foco em falta assim: %s" % avisos)
    verifica("aproxima diz quanto faltou e o zoom que centra", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "anel a 2,2: %.0f px, sugerido %s" % (medido, m.group(1) if m else "?"))


def teste_aproxima_acaba_nitido():
    """No fim do aproxima o pormenor e o do ficheiro: os niveis servem para isso.

    O zoom de 2,2 com o sprite de sempre pedia a Pillow que ampliasse quase duas vezes uma
    imagem ja reduzida, e o anel chegava ao fim mole. Os niveis existem para o fim ser uma
    REDUCAO do ficheiro original, e isso nao era medido: com o nivel desfasado de um (a
    escala a passar de 1, ou seja a ampliar) a suite passava (verificador, mutacao A11).

    Mede-se a energia de alta frequencia do fim contra um recorte Lanczos do ficheiro no
    mesmo tamanho. A foto de ensaio e ruido, que tem pormenor em todas as frequencias, e e
    grande o bastante para o nivel de cima a 2,2 ainda ser uma reducao.
    """
    import contextlib
    import io
    import inspect
    import tempfile
    from PIL import ImageFilter, ImageStat
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_aproxn_")
    ruido = os.path.join(pasta, "ruido.jpg")
    Image.effect_noise((4800, 3200), 70).convert("RGB").save(ruido, quality=95)

    def energia(im):
        g = im.convert("L").crop((660, 340, 1260, 740))
        lap = g.filter(ImageFilter.Kernel((3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), scale=1, offset=128))
        return ImageStat.Stat(lap).stddev[0]

    def razao():
        with contextlib.redirect_stdout(io.StringIO()):
            pr = render.preparar(_clip_aproxima(ruido, "Aproxima 2.2", foco=(0.5, 0.5)), {})
        ap = pr["aproxima"]
        s_ = ap["fw"] * 2.2 / ap["im"].width
        ref = ap["im"].resize((round(ap["im"].width * s_), round(ap["im"].height * s_)), Image.LANCZOS)
        x0, y0 = (ref.width - 1920) // 2, (ref.height - 1080) // 2
        ref = ref.crop((x0, y0, x0 + 1920, y0 + 1080))
        return energia(render.desenhar(pr, 5.0, 5.0)) / energia(ref)

    # O LIMIAR fica a meio das duas medidas: a certa da 0,95 a 0,96 e a desfasada 0,87.
    certa = razao()
    if certa < 0.91:
        problemas.append("o fim tem %.2f do pormenor de um recorte Lanczos do ficheiro" % certa)
    # MUTACAO: o nivel desfasado de um, k = 1,12^nivel. Cada nivel fica uma vez mais pequeno
    # e o compor() passa a ampliar ate 1,12 vezes.
    guardadas = render.aproxima_alvo, render.aproxima_nivel
    desfasada = None
    try:
        for nome in ("aproxima_alvo", "aproxima_nivel"):
            fonte = inspect.getsource(getattr(render, nome))
            if fonte.count("k = (1.0 + ZOOM) ** (nivel + 1)") != 1:
                problemas.append("a mutacao de controlo ja nao se aplica ao %s: o codigo dos niveis "
                                 "mudou, e este teste tem de mudar com ele" % nome)
                break
            exec(compile(fonte.replace("k = (1.0 + ZOOM) ** (nivel + 1)", "k = (1.0 + ZOOM) ** nivel"),
                         render.__file__, "exec"), render.__dict__)
        else:
            desfasada = razao()
    finally:
        render.aproxima_alvo, render.aproxima_nivel = guardadas
    if desfasada is not None and desfasada >= 0.91:
        problemas.append("com o nivel desfasado o fim continuou com %.2f: a medida nao ve a "
                         "diferenca" % desfasada)
    # E OS NIVEIS NUNCA PASSAM O FICHEIRO. Acima do tamanho dele, um nivel era uma AMPLIACAO
    # Lanczos sem pormenor nenhum a ganhar, e a 4,0 uma foto de 12 MP pedia a cada fatia
    # um sprite de 6300x4700 (verificador: 442 MB de pico num processo, contra 111 MB no zoom
    # lento). Acima do ficheiro fica o proprio ficheiro.
    with contextlib.redirect_stdout(io.StringIO()):
        pr4 = render.preparar(_clip_aproxima(ruido, "Aproxima 4", foco=(0.5, 0.5)), {})
    ap4 = pr4["aproxima"]
    for nivel in range(render.aproxima_nivel_de(4.0) + 1):
        w_, h_ = render.aproxima_alvo(ap4, nivel)
        if w_ > ap4["im"].width or h_ > ap4["im"].height:
            problemas.append("o nivel %d do aproxima a 4,0 tem %dx%d, maior do que o ficheiro %dx%d"
                             % (nivel, w_, h_, ap4["im"].width, ap4["im"].height))
            break
    verifica("aproxima acaba com o pormenor do ficheiro", not problemas,
             "; ".join(problemas)[:220] if problemas else
             "%.2f do recorte Lanczos (desfasado de um nivel: %.2f)" % (certa, desfasada or 0))


def teste_aproxima_com_zoom_fora_dos_limites_recusado():
    """Um zoom fora de 1,2 a 4,0 e recusado, fica a omissao, e alguem e avisado.

    CORTAR PARA A PONTA MAIS PROXIMA SERIA PIOR: quem escreve 12 no CSV enganou-se, e um
    12 que vira 4 em silencio e um engano que ninguem ve. Ficam os 2,2 da omissao, o
    montar_da_mesa poe o aviso na lista que ele le e o render diz no arranque.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    casos = {"Aproxima": (2.2, False), "Aproxima 1.2": (1.2, False), "Aproxima 4": (4.0, False),
             "Aproxima 2,6": (2.6, False), "Aproxima 1.19": (2.2, True), "Aproxima 4.01": (2.2, True),
             "Aproxima 12": (2.2, True), "Aproxima muito": (2.2, True)}
    for mov, (az, avisa) in casos.items():
        e, valor, aviso = render.ler_aproxima(mov)
        if not e or abs(valor - az) > 1e-9 or bool(aviso) != avisa:
            problemas.append("%r deu (%s, %s, %r)" % (mov, e, valor, aviso[:40]))
    if render.ler_aproxima("Afastada")[0] or render.ler_aproxima("")[0]:
        problemas.append("um enquadramento que nao e o aproxima foi lido como aproxima")
    # E O QUE FOI RECUSADO NAO CHEGA AO ECRA: o fotograma tem de ser o da omissao.
    pasta = tempfile.mkdtemp(prefix="teste_aproxz_")
    foto = _foto_com_marca(pasta)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        mau = render.preparar(_clip_aproxima(foto, "Aproxima 12"), {})
        bom = render.preparar(_clip_aproxima(foto, "Aproxima 2.2"), {})
    if render.desenhar(mau, 5.0, 5.0).tobytes() != render.desenhar(bom, 5.0, 5.0).tobytes():
        problemas.append("o zoom recusado desenhou outra coisa que nao a omissao")
    if "fora dos limites" not in log.getvalue():
        problemas.append("o render nao disse que recusou: %r" % log.getvalue()[:120])
    # E PELA MESA: o montar escreve a omissao e poe o aviso na lista dele.
    linhas, _som, saida = _monta_em_pasta([
        {"t": "foto", "i": "f0593", "d": 4, "c": 0.7, "r": "fundo", "e": "aproxima", "az": 12},
        {"t": "foto", "i": "f0592", "d": 4, "c": 0.7, "r": "fundo", "e": "aproxima", "az": 2.6},
        {"t": "foto", "i": "f0592", "d": 4, "c": 0.7, "r": "fundo", "e": "aproxima"}])
    movs = [l["movimento"] for l in linhas]
    if movs != ["Aproxima 2.2", "Aproxima 2.6", "Aproxima 2.2"]:
        problemas.append("a montagem escreveu %s" % movs)
    if "fora de 1.2 a 4.0" not in saida:
        problemas.append("o montar nao avisou do zoom fora dos limites")
    # NA RAJADA O APROXIMA NAO EXISTE: o render sai pelo ramo da rajada antes de ler o
    # movimento. Uma foto que ficou com o aproxima guardado e passou a rajada escreve o que
    # escrevia antes do aproxima existir, e sem aviso de foco sobre uma coisa que nao vai ao
    # filme (verificador, 18 de setembro).
    linhas_r, _som_r, saida_r = _monta_em_pasta([
        {"t": "foto", "i": "f0593", "d": 4, "c": 0.7, "r": "rajada", "e": "aproxima", "az": 2.8}])
    if linhas_r[0]["movimento"] != "Zoom in" or "aproxima" in saida_r.lower():
        problemas.append("a rajada com aproxima escreveu %r e disse %r"
                         % (linhas_r[0]["movimento"], [l for l in saida_r.splitlines() if "aproxima" in l.lower()][:1]))
    verifica("zoom do aproxima fora dos limites e recusado", not problemas,
             "; ".join(problemas)[:200] if problemas else "%d escritas, %d casos" % (len(movs), len(casos)))


def teste_limites_do_aproxima_iguais():
    """O zoom do aproxima: os mesmos 1,2 a 4,0 e a mesma omissao no render, no montar e na Mesa.

    A MESMA RAZAO DOS LIMITES DOS GRUPOS: sao tres copias do mesmo numero. Se a Mesa
    deixasse escolher 6 e o render recusasse, o Tiago escolhia 6 na Mesa e via 2,2 no
    video, sem nada a dizer-lhe porque.
    """
    import re
    import montar_da_mesa
    import render
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    na_mesa = {}
    for chave in ("min", "max", "omissao"):
        m = re.search(r"APROXIMA_%s\s*=\s*([0-9.]+)"
                      % {"min": "MIN", "max": "MAX", "omissao": "OMISSAO"}[chave], html)
        na_mesa[chave] = float(m.group(1)) if m else None
    escritos = {"min": 1.2, "max": 4.0, "omissao": 2.2}
    dos_scripts = [(render.APROXIMA_MIN, render.APROXIMA_MAX, render.APROXIMA_OMISSAO),
                   (montar_da_mesa.APROXIMA_MIN, montar_da_mesa.APROXIMA_MAX,
                    montar_da_mesa.APROXIMA_OMISSAO)]
    certo = (all(x == (1.2, 4.0, 2.2) for x in dos_scripts)
             and {k: na_mesa.get(k) for k in escritos} == escritos)
    verifica("zoom do aproxima de 1,2 a 4,0 igual no render, no montar_da_mesa e na Mesa", certo,
             "render e montar %s, Mesa %s" % (dos_scripts, na_mesa))


# ---------------------------------------------------------- texto em cada foto
# O Tiago: "permite colocar o texto nas fotos mesmo as que ficam em leque e assim, tem de
# ser opcional ter o texto ou nao". Cada foto de um grupo pode trazer o seu texto, numa
# faixa escura dentro dela, e a legenda do grupo continua. Os testes medem os pixeis que
# o texto muda, comparando o mesmo fotograma com e sem textos: fotos de uma cor so, e o
# texto e o que fica claro, a faixa o que fica escuro.
TEXTO_LONGO = ("Paris com os amigos no verao de 2014 junto ao rio e depois a praia "
               "no fim de um dia de sol muito comprido com a familia toda")

# Tiradas do render de ANTES dos textos (a copia de 15 de setembro), com Pillow 12.3.0, por
# assinaturas_sem_texto(). Uma Pillow nova pode mudar a reamostragem e com ela todas: ai
# refazem-se a partir do render.py do git anterior aos textos, nunca do de agora.
# AS DUAS PILHAS FORAM REFEITAS A 17 DE SETEMBRO, com a agenda que divide a duracao pelas
# fotos: a de 5 em 6,85 s entrava de 0,75 em 0,75 s e passou a entrar de 0,91 em 0,91 s, a de 4
# em 6 s de 0,8 em 0,8 s para 0,92, e os fotogramas aos 0,9 s e a meio mudaram. Tiradas do render
# de antes desta ronda com a agenda nova injetada, escrita a partir da regra, e iguais as do
# render novo (scratchpad grupos/render/refazer_assinaturas.py). Eram 58dc803ead1c4979bd9c75dc18eeeb0a
# e 847b9393695a387d69df816365bc1c25. As colagens nao mudaram: a de 4 em 9,4 s e a de 3 em 7,8 s
# ja entravam de 1,6 em 1,6 s, que e a vez da regra nova nessas duracoes.
ASSINATURAS_SEM_TEXTO = {
    "colagem filas de 4": "3f7e539b4827228d8976b99ea261111f",
    "colagem filas de 4 com legenda": "ffee7e68478735fe6d04ec414b2d17bc",
    "colagem espalhada de 3 com legenda": "6974cb12b10f85847763107c3661a8d1",
    "pilha monte de 5": "68c4d080d593842f884c5437eae571cd",
    "pilha leque de 4 com legenda": "90265113de49f8e7ec89cbcabb7aacba",
    "lado 2v de 2": "605e1f1c55d28083e0b378961f348bae",
    "lado 3v de 3 com legenda": "8bd06df7d4d572f4134d7f6dc8126c3f",
    "lado 3s de 3 com legenda": "f3d939a2ea55b128a30f6304f356c5d2",
    "lado 4q de 4 com legenda": "66bccffed4a0e5fd8c63df2f45e1da31",
}


def _foto_gradiente(k, a, lado=480):
    """Foto sintetica com gradiente: um corte, uma escala ou uma faixa a mais mudam os bytes."""
    w, h = max(1, int(round(lado * a))), lado
    g = Image.linear_gradient("L")
    return Image.merge("RGB", (g.resize((w, h)), g.rotate(90).resize((w, h)),
                               Image.new("L", (w, h), CORES_MONTE[k % 8][2])))


def assinaturas_sem_texto(render, pasta, extra=None):
    """md5 de tres fotogramas de cada grupo de controlo, pelo preparar() do `render` dado.

    Serve o render de agora e o de antes dos textos, que nao conhece a coluna textos_fotos:
    `extra` sao colunas a mais no clip, e o de antes ignora-as.
    """
    import hashlib
    formas = [4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0, 1.0]
    caminhos = []
    for k, a in enumerate(formas):
        c = os.path.join(pasta, "gradiente%d.png" % k)
        if not os.path.exists(c):
            _foto_gradiente(k, a).save(c)
        caminhos.append(c)
    casos = [("colagem", "filas", 4, "", ""), ("colagem", "filas", 4, "Amigos", "|0.5000,0.9700"),
             ("colagem", "espalhada", 3, "Amigos", ""), ("pilha", "monte", 5, "", "0.5,0.95"),
             ("pilha", "leque", 4, "Amigos", ""), ("lado", "2v", 2, "", "|0.5000,0.9700"),
             ("lado", "3v", 3, "Natal", ""), ("lado", "3s", 3, "Amigos", "0.2,0.2||0.5,0.95"),
             ("lado", "4q", 4, "Verao de 2014\nParis com os amigos", "0.3000,0.4100|0.6000,0.5500||0.5,0.45")]
    # O 4q LEVA FOCOS QUE NAO BATEM NA BORDA. Nos outros o foco empurra a janela de
    # cobrir_foco() contra a borda da foto e a conta que janela_foco() arredonda nunca
    # chegava a contar: truncar em vez de arredondar passava. Numa celula de 4q a foto
    # 4:3 sobra na altura, e a janela fica a meio.
    saida = {}
    for tipo, tratamento, n, legenda, focos in casos:
        clip = {"tipo": tipo, "texto_ecra": legenda, "tratamento": tratamento, "fonte_imagem": focos,
                "ficheiro": "", "id": "", "transicao_s": "0.7", "_caminhos": caminhos[:n]}
        clip.update(extra or {})
        pronto = render.preparar(clip, {})
        if tipo == "lado":
            dur = 6.0
        else:
            dur = 3 + 1.6 * n if tipo == "colagem" else 2.6 + 0.85 * n
        md5 = hashlib.md5()
        for t in (0.9, dur / 2.0, dur - 0.04):
            md5.update(render.desenhar(pronto, t, dur).tobytes())
        saida["%s %s de %d%s" % (tipo, tratamento, n, " com legenda" if legenda else "")] = md5.hexdigest()
    return saida


def _mudou(com, sem, limiar=10):
    """Mascara dos pixeis que diferem entre dois fotogramas, pelo canal que mais muda."""
    from PIL import ImageChops
    r, g, b = ImageChops.difference(com, sem).split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v > limiar else 0)


def _letra_e_faixa(com, sem, mudou):
    """(letra, faixa): o que o texto pos claro, e o que escureceu para menos de 3/4.

    A LETRA E BRANCA: um pixel claro com um canal escuro nao e letra. A borda de baixo da
    faixa numa foto amarela, rodada e composta com dois BICUBIC, ganha um anel de amarelo
    mais claro do que o amarelo, e com a letra a 46 esse anel passava de 200 de claro e
    contava como letra a 30 pixeis abaixo dela: "NATAL" media 178 x 60. O amarelo tem 30 de
    azul, e a reamostragem nao o leva a 150; um pixel de letra que passa os 200 de claro
    tem todos os canais acima de 170, seja qual for a cor da foto por baixo da faixa.
    """
    from PIL import ImageChops
    r, g, b = com.split()
    branco = ImageChops.darker(ImageChops.darker(r, g), b).point(lambda v: 255 if v >= 150 else 0)
    claro = ImageChops.multiply(com.convert("L").point(lambda v: 255 if v >= 200 else 0), branco)
    escuro = ImageChops.subtract(sem.convert("L").point(lambda v: int(v * 0.75)),
                                 com.convert("L")).point(lambda v: 255 if v > 0 else 0)
    return ImageChops.multiply(mudou, claro), ImageChops.multiply(mudou, escuro)


def _pontos(mascara):
    """Os (x, y) acesos de uma mascara."""
    caixa = mascara.getbbox()
    if not caixa:
        return []
    x0, y0, x1, _y1 = caixa
    w = x1 - x0
    return [(x0 + i % w, y0 + i // w) for i, v in enumerate(mascara.crop(caixa).getdata()) if v]


def _altura_das_maiusculas(render, tamanho_a_1080):
    from PIL import ImageFont
    caixa = ImageFont.truetype(render.FONTE_TEXTO, render.no_ecra(tamanho_a_1080)).getbbox("NATAL")
    return caixa[3] - caixa[1]


def _largura_na_capa(render, texto, largura, tamanho=None):
    """Largura da letra na capa_texto_foto() sem rodar, contada como no ecra: mais de 200 em todos os canais.

    E o que o sprite leva: a tinta da fonte (getbbox) inclui os bearings e a borda esbatida,
    que a contagem a partir de 200 de claro deixa de fora, e a diferenca cresce com a letra.
    """
    from PIL import ImageChops
    capa, _cortado = render.capa_texto_foto(texto, largura, largura, 0.0, tamanho)
    r, g, b, _a = capa.split()
    caixa = ImageChops.darker(ImageChops.darker(r, g), b).point(lambda v: 255 if v > 200 else 0).getbbox()
    return caixa[2] - caixa[0] if caixa else 0


def teste_grupos_sem_texto_iguais_a_antes():
    """Sem textos nas fotos, os grupos dao os mesmos bytes que antes de os textos existirem.

    O PEDIDO: o texto em cada foto e opcional, e sem ele nada pode mudar nas montagens ja
    feitas. Os fotogramas de colagem, pilha e lado a lado, com e sem legenda e com focos,
    comparam-se com assinaturas tiradas do render de antes, e nao com o de agora: a coluna
    ausente, uma lista de vazios e uma coluna mal escrita tem de dar essas assinaturas. E
    com textos na coluna nenhum grupo pode dar o mesmo, senao a igualdade era por o texto
    nao chegar ao desenho. Uma lista vazia ou de vazios direto no preparar_monte e no
    preparar_lado da o mesmo que nenhuma.
    """
    import tempfile
    import PIL
    import render
    pasta = tempfile.mkdtemp(prefix="teste_sem_texto_")
    problemas = []
    for extra in ({}, {"textos_fotos": '["", " ", "", "", ""]'}):
        agora = assinaturas_sem_texto(render, pasta, extra)
        if not ASSINATURAS_SEM_TEXTO or sorted(agora) != sorted(ASSINATURAS_SEM_TEXTO):
            problemas.append("grupos de controlo diferentes dos das assinaturas: %s" % sorted(agora))
            break
        diferentes = sorted(k for k in agora if agora[k] != ASSINATURAS_SEM_TEXTO[k])
        if diferentes:
            problemas.append("%s: diferente de antes em %s" % (extra or "sem coluna", ", ".join(diferentes)))
    lidos = [render.ler_textos_fotos(v) for v in (None, "", "[]", '["", "  "]', "lixo", '{"a": 1}', "[1, 2",
                                                  "[true, false]", "[null, null]")]
    if any(l is not None for l in lidos):
        problemas.append("colunas sem texto lidas como textos: %s" % lidos)
    # UM NUMERO SEM ASPAS E UM ANO, UM BOOLEANO NAO E TEXTO NENHUM. O true saia escrito
    # "True" na fotografia e o 2019.0 saia "2019.0"; o montar_da_mesa.py faz a mesma conta
    # ao escrever a coluna, ver texto_de_xf().
    lido = render.ler_textos_fotos('[" Natal ", "", 2019, 2019.0, true, 20.5]')
    if lido != ["Natal", "", "2019", "2019", "", "20.5"]:
        problemas.append("coluna com textos mal lida: %r" % (lido,))
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):     # a pilha avisa que tapa as de baixo
        com = assinaturas_sem_texto(render, pasta, {"textos_fotos": '["NATAL", "", "2019", "", "Porto"]'})
    iguais = sorted(k for k in com if com[k] == ASSINATURAS_SEM_TEXTO.get(k))
    if iguais:
        problemas.append("com textos na coluna, iguais a sem texto: %s" % ", ".join(iguais))

    imagens = [Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k])
               for k, a in enumerate(_formas_monte(4)["misturadas"])]
    for tipo, estilo in (("colagem", "filas"), ("pilha", "leque")):
        base = render.preparar_monte(tipo, imagens, None, "Amigos", estilo=estilo)
        quadros = [render.desenhar(base, t, 9.0).tobytes() for t in (1.2, 8.9)]
        for textos in ([], [""] * 4, [" "] * 6):
            p = render.preparar_monte(tipo, imagens, None, "Amigos", estilo=estilo, textos=textos)
            if [render.desenhar(p, t, 9.0).tobytes() for t in (1.2, 8.9)] != quadros:
                problemas.append("%s %s com textos=%r diferente de sem textos" % (tipo, estilo, textos))
    base = render.preparar_lado("3s", imagens[:3], [], "Amigos")
    quadros = [render.desenhar(base, t, 6.0).tobytes() for t in (1.2, 5.9)]
    for textos in ([], ["", "", ""], ["  "]):
        p = render.preparar_lado("3s", imagens[:3], [], "Amigos", textos)
        if [render.desenhar(p, t, 6.0).tobytes() for t in (1.2, 5.9)] != quadros:
            problemas.append("lado 3s com textos=%r diferente de sem textos" % (textos,))
    verifica("texto nas fotos: sem textos, os grupos iguais a antes", not problemas,
             "; ".join(problemas[:3]) if problemas else
             "%d grupos ao byte com o render de antes (Pillow %s)" % (len(ASSINATURAS_SEM_TEXTO), PIL.__version__))


def teste_texto_nas_fotos_do_monte():
    """Na colagem e na pilha, cada texto fica numa faixa escura dentro da sua foto, e so ai.

    O PEDIDO: texto em cada foto, "mesmo as que ficam em leque". A faixa e desenhada na
    foto antes da moldura e da rotacao, por isso roda com ela, entra com ela e na pilha e
    tapada pela seguinte como a propria foto. Nos quatro estilos, com metade das fotos com
    texto e a outra metade sem, mede-se o que o texto muda no fotograma:
      - nada fora do contorno das fotos com texto, descontado o que as seguintes tapam, e
        nada antes de entrarem, nem a meio da entrada fora do sitio onde a foto vai;
      - letra clara sobre faixa escura em cada foto com texto que se ve, com a letra
        dentro da faixa, a faixa encostada ao fundo e com a largura da foto;
      - com o foco marcado na zona da faixa, a faixa passa para o topo;
      - nada por baixo da faixa da legenda do grupo;
      - e as letras no ecra, com a foto pousada, com a altura das maiusculas entre a de
        TEXTO_FOTO_MIN e a de TEXTO_FOTO_TAMANHO. O sprite da colagem e feito maior do que
        pousa, e um texto medido no sprite saia com outro tamanho.
    """
    import contextlib
    import io
    from PIL import ImageChops, ImageDraw
    import render
    problemas, alturas = [], []
    cap_min = _altura_das_maiusculas(render, render.TEXTO_FOTO_MIN)
    cap_max = _altura_das_maiusculas(render, render.TEXTO_FOTO_TAMANHO)
    ecra = (render.L, render.A)
    for tipo, estilo, n, legenda in (("colagem", "filas", 4, "Amigos"), ("colagem", "espalhada", 3, ""),
                                     ("pilha", "monte", 5, ""), ("pilha", "leque", 4, "Amigos")):
        aspetos = _formas_monte(n)["misturadas"]
        imagens = [Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k]) for k, a in enumerate(aspetos)]
        focos = [None] * (n - 1) + [(0.5, 0.95)]
        dur = 3 + 1.6 * n if tipo == "colagem" else 2.6 + 0.85 * n
        sem = render.preparar_monte(tipo, imagens, focos, legenda, estilo=estilo)
        inicios, entrada, _ = render.estado_monte(sem, 0.0, dur)
        pousa = inicios[-1] + entrada
        tempos = (0.0, inicios[-1] + 0.5 * entrada, pousa)
        quadros_sem = [render.desenhar(sem, t, dur) for t in tempos]
        topo_legenda = sem["capa"][1].getbbox()[1] if sem["capa"] else render.A
        corridas = [("pares", [k % 2 == 0 for k in range(n)], focos),
                    ("impares", [k % 2 == 1 for k in range(n)], focos)]
        if tipo == "pilha":
            # a disposicao da pilha nao depende dos focos: o fotograma sem texto e o mesmo
            corridas.append(("a de cima sem foco", [k == n - 1 for k in range(n)], None))
        for rotulo, marca, focos_corrida in corridas:
            nome = "%s %s, texto nas %s" % (tipo, estilo, rotulo)
            textos = ["NATAL" if m else "" for m in marca]
            # a pilha avisa que as de baixo ficam tapadas, e aqui isso e de proposito
            with contextlib.redirect_stdout(io.StringIO()):
                pronto = render.preparar_monte(tipo, imagens, focos_corrida, legenda,
                                               estilo=estilo, textos=textos)
            for t, quadro_sem in zip(tempos, quadros_sem):
                com = render.desenhar(pronto, t, dur)
                mudou = _mudou(com, quadro_sem)
                poses, _zoom = render.poses_monte(pronto, t, dur)
                # Onde o texto de cada foto se pode ver: dentro da foto, sem a moldura, com 3 px
                # de esbatido, menos o que as que entraram depois tapam. E o miolo, 4 px para
                # dentro: a letra mede-se ai, porque a borda da faixa contra a moldura branca
                # tambem fica clara e mudou.
                # TRES E NAO DOIS: a rotacao do sprite e o compor() sao os dois BICUBIC, e a
                # borda escura da faixa no fundo da foto espalha-se ate 1,8 px para dentro da
                # moldura (12 de 255 no vermelho, na colagem em filas). O polygon arredonda os
                # cantos e com 2 px esses pixeis caiam fora, sem haver texto fora da foto.
                # A faixa pintada na moldura continua a ser apanhada: a moldura tem 6 px.
                onde, miolo = {}, {}
                for k, x, y, tam, _alfa, _p in poses:
                    f = pronto["fotos"][k]
                    w, h = f["tamanho"]
                    for folga, destino in ((3, onde), (-4, miolo)):
                        m = Image.new("L", ecra, 0)
                        d = ImageDraw.Draw(m)
                        d.polygon(render.cantos(x, y, w / 2.0 * tam + folga, h / 2.0 * tam + folga, f["angulo"]),
                                  fill=255)
                        for j, xj, yj, tj, _a, _pj in poses:
                            if j > k:
                                g = pronto["fotos"][j]
                                wj, hj = g["tamanho"]
                                d.polygon(render.cantos(xj, yj, (wj / 2.0 + g["moldura"]) * tj - 2,
                                                        (hj / 2.0 + g["moldura"]) * tj - 2, g["angulo"]), fill=0)
                        destino[k] = m
                uniao = Image.new("L", ecra, 0)
                for k in onde:
                    if textos[k]:
                        uniao = ImageChops.lighter(uniao, onde[k])
                fora = ImageChops.subtract(mudou, uniao).getbbox()
                if fora:
                    problemas.append("%s aos %.2f s: o texto muda pixeis fora das fotos com texto, em %s"
                                     % (nome, t, fora))
                caixa = mudou.getbbox()
                if legenda and caixa and caixa[3] > topo_legenda:
                    problemas.append("%s: texto a descer ate %d, a legenda comeca em %d" % (nome, caixa[3], topo_legenda))
                if t != pousa:
                    continue
                letra, faixa = _letra_e_faixa(com, quadro_sem, mudou)
                por_k = {p[0]: p for p in poses}
                # Na pilha as de baixo ficam tapadas de proposito: so a de cima tem de se ver.
                ver = [k for k in range(n) if textos[k] and (tipo == "colagem" or k == n - 1)]
                for k in ver:
                    f = pronto["fotos"][k]
                    w, h = f["tamanho"]
                    _k, x, y, tam, _a, _p = por_k[k]
                    a = math.radians(f["angulo"])
                    c, s = math.cos(a), math.sin(a)

                    def local(pontos):
                        return [((px + 0.5 - x) * c - (py + 0.5 - y) * s, (px + 0.5 - x) * s + (py + 0.5 - y) * c)
                                for px, py in pontos]
                    lt = local(_pontos(ImageChops.multiply(letra, miolo[k])))
                    fx = local(_pontos(ImageChops.multiply(faixa, onde[k])))
                    if len(lt) < 25 or len(fx) < 300:
                        problemas.append("%s: foto %d com %d pixeis de letra clara e %d de faixa escura"
                                         % (nome, k + 1, len(lt), len(fx)))
                        continue
                    fu = (min(u for u, _v in fx), max(u for u, _v in fx))
                    fv = (min(v for _u, v in fx), max(v for _u, v in fx))
                    lu = (min(u for u, _v in lt), max(u for u, _v in lt))
                    lv = (min(v for _u, v in lt), max(v for _u, v in lt))
                    if lu[0] < fu[0] - 3 or lu[1] > fu[1] + 3 or lv[0] < fv[0] - 3 or lv[1] > fv[1] + 3:
                        problemas.append("%s: foto %d com a letra fora da faixa" % (nome, k + 1))
                    # CENTRADA NA FAIXA. Encostada a esquerda a letra continuava dentro da faixa
                    # e nenhuma medida acima o via: numa faixa de 600 px, "Natal" ia do centro
                    # 300 para o 60. Mede-se na de cima, que nenhuma outra tapa.
                    if k == n - 1 and abs((lu[0] + lu[1]) / 2.0 - (fu[0] + fu[1]) / 2.0) > 3:
                        problemas.append("%s: foto %d com a letra centrada em %.1f e a faixa em %.1f"
                                         % (nome, k + 1, (lu[0] + lu[1]) / 2.0, (fu[0] + fu[1]) / 2.0))
                    em_cima = bool(focos_corrida) and focos_corrida[k] is not None
                    if em_cima and not fv[1] < 0:
                        problemas.append("%s: foto %d com o foco na faixa e a faixa nao sobe (v %.0f a %.0f)"
                                         % (nome, k + 1, fv[0], fv[1]))
                    if not em_cima and not fv[0] > 0:
                        problemas.append("%s: foto %d com a faixa fora do fundo (v %.0f a %.0f)"
                                         % (nome, k + 1, fv[0], fv[1]))
                    if k == n - 1:
                        encostada = fv[0] <= -h / 2.0 + 4 if em_cima else fv[1] >= h / 2.0 - 4
                        if not encostada or fu[0] > -w / 2.0 + 4 or fu[1] < w / 2.0 - 4:
                            problemas.append("%s: faixa da foto de cima nao encosta a borda nem tem a largura dela "
                                             "(u %.0f a %.0f, v %.0f a %.0f, foto %.0f x %.0f)"
                                             % (nome, fu[0], fu[1], fv[0], fv[1], w, h))
                        altura = lv[1] - lv[0] + 1
                        largura = lu[1] - lu[0] + 1
                        alturas.append(altura)
                        if not cap_min - 2 <= altura <= cap_max + 2:
                            problemas.append("%s: maiusculas com %.1f px no ecra, entre %d e %d"
                                             % (nome, altura, cap_min, cap_max))
                        # E NO TAMANHO QUE linhas_texto_foto() ESCOLHEU PARA A FOTO POUSADA, nao so
                        # dentro da janela: com a letra a 70% a janela de +-2 px deixava passar, e
                        # um texto medido no sprite da colagem, 3% maior do que pousa, sai 3,5 px
                        # mais estreito em NATAL sem mudar a altura mais do que um pixel.
                        # A ALTURA PRENDE O TAMANHO, contra a tinta da fonte, a um pixel. A LARGURA
                        # PRENDE A ESCALA, contra a letra da propria capa_texto_foto() sem rodar,
                        # contada como no ecra: a tinta da fonte inclui os bearings e a borda
                        # esbatida fica de fora a partir de 200 de claro, e essa perda cresce com
                        # a letra (4,7 px a 36, 5,7 a 46 no leque a 11 graus); uma janela fixa
                        # calibrada a 36 acusava o render certo a 46. Contra a capa a diferenca e
                        # so a da rotacao e do compor(): medido +0,3 a +1,3 a 46 nos quatro
                        # estilos, +2,3 a 60; o texto medido no sprite da colagem fica 3% mais
                        # estreito, -3,3. Por isso -2 a +3,5.
                        tamanho = render.linhas_texto_foto(textos[k], w)[0]
                        tinta = render.ImageFont.truetype(render.FONTE_TEXTO, tamanho).getbbox(textos[k])
                        na_capa = _largura_na_capa(render, textos[k], w)
                        if abs(altura - (tinta[3] - tinta[1])) > 1 or not -2 <= largura - na_capa <= 3.5:
                            problemas.append("%s: foto %d com o texto a %.1f x %.1f px no ecra, e a %d px a fonte "
                                             "da %d de altura e a capa %d de largura"
                                             % (nome, k + 1, largura, altura, tamanho, tinta[3] - tinta[1], na_capa))
    verifica("texto nas fotos: colagem e pilha, dentro de cada foto", not problemas,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "4 estilos, texto nas pares e nas impares, antes, a entrar e pousadas")

    # ---- a lista curta, o aviso do corte e a orla que a seguinte pisa
    import tempfile
    outros = []
    # UMA LISTA MAIS CURTA DO QUE AS FOTOS COMPLETA-SE COM VAZIOS. O montar_da_mesa.py ja a
    # completa, mas uma coluna escrita a mao chega assim, e sem completar a pilha e a
    # colagem rebentavam com IndexError a meio do render. Direto e pelo preparar().
    aspetos = _formas_monte(3)["misturadas"]
    imagens = [Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k]) for k, a in enumerate(aspetos)]
    pasta = tempfile.mkdtemp(prefix="teste_texto_curto_")
    caminhos = []
    for k, im in enumerate(imagens):
        caminhos.append(os.path.join(pasta, "cor%d.png" % k))
        im.save(caminhos[-1])
    for tipo, estilo in (("pilha", "leque"), ("colagem", "filas")):
        dur = 3 + 1.6 * 3 if tipo == "colagem" else 2.6 + 0.85 * 3
        quadros = {}
        for rotulo, textos in (("direto ['NATAL']", ["NATAL"]), ("direto completa", ["NATAL", "", ""]),
                               ("coluna ['NATAL']", '["NATAL"]'), ("coluna completa", '["NATAL", "", ""]')):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    if rotulo.startswith("direto"):
                        p = render.preparar_monte(tipo, imagens, None, "", estilo=estilo, textos=textos)
                    else:
                        p = render.preparar({"tipo": tipo, "texto_ecra": "", "tratamento": estilo,
                                             "fonte_imagem": "", "ficheiro": "", "id": "", "transicao_s": "0",
                                             "_caminhos": caminhos, "textos_fotos": textos}, {})
                quadros[rotulo] = render.desenhar(p, dur - 0.04, dur).tobytes()
            except Exception as e:
                outros.append("%s %s, %s: %r" % (tipo, estilo, rotulo, e))
        if len(quadros) == 4 and len(set(quadros.values())) != 1:
            outros.append("%s %s: lista curta diferente da completa" % (tipo, estilo))

    # O CORTE AVISA TAMBEM NA COLAGEM E NA PILHA, e so quando corta.
    for textos, deve in (([TEXTO_LONGO] * 3, True), (["NATAL"] * 3, False)):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            render.preparar_monte("colagem", imagens, None, "", estilo="espalhada", textos=textos)
        avisou = "AVISO" in saida.getvalue() and "foto 1" in saida.getvalue()
        if avisou != deve:
            outros.append("colagem espalhada com %r: aviso %s" % (textos[0][:20], avisou))

    # A ORLA QUE A SEGUINTE PISA NAO LEVA LETRA. Numa colagem espalhada de 4 o fim de um
    # texto que enchia a largura ficava por baixo da moldura da foto seguinte. Em cada foto
    # que uma seguinte pisa, nenhuma letra a vista pode chegar a orla de MONTE_PISA.
    pisadas = so_pela_orla = 0
    texto_largo = "Verao de 2014 na praia ao fim da tarde"
    for estilo in ("espalhada", "filas"):
        n = 4
        imagens4 = [Image.new("RGB", (int(round(600 * a)), 600), CORES_MONTE[k])
                    for k, a in enumerate(_formas_monte(n)["misturadas"])]
        dur = 3 + 1.6 * n
        sem = render.preparar_monte("colagem", imagens4, None, "", estilo=estilo)
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            com = render.preparar_monte("colagem", imagens4, None, "", estilo=estilo, textos=[texto_largo] * n)
        inicios, entrada, _ = render.estado_monte(sem, 0.0, dur)
        t = inicios[-1] + entrada
        q_sem, q_com = render.desenhar(sem, t, dur), render.desenhar(com, t, dur)
        letra, _faixa = _letra_e_faixa(q_com, q_sem, _mudou(q_com, q_sem))
        poses, _zoom = render.poses_monte(com, t, dur)
        for k, x, y, tam, _a, _p in poses:
            f = com["fotos"][k]
            w, h = f["tamanho"]
            foto = render.cantos(x, y, w / 2.0 * tam, h / 2.0 * tam, f["angulo"])
            m = Image.new("L", ecra, 0)
            d = ImageDraw.Draw(m)
            d.polygon(render.cantos(x, y, w / 2.0 * tam - 4, h / 2.0 * tam - 4, f["angulo"]), fill=255)
            pisada = False
            for j, xj, yj, tj, _aj, _pj in poses:
                if j <= k:
                    continue
                g = com["fotos"][j]
                wj, hj = g["tamanho"]
                if render.afastar(foto, render.cantos(xj, yj, (wj / 2.0 + g["moldura"]) * tj,
                                                      (hj / 2.0 + g["moldura"]) * tj, g["angulo"])):
                    pisada = True
                # DOIS PIXEIS PARA FORA da moldura da seguinte, e nao para dentro: a borda
                # esbatida dessa moldura clara muda de cor por cima da faixa escura e fica
                # acima de 200, e com -2 contava como letra na orla (17 pixeis numa fila).
                d.polygon(render.cantos(xj, yj, (wj / 2.0 + g["moldura"]) * tj + 2,
                                        (hj / 2.0 + g["moldura"]) * tj + 2, g["angulo"]), fill=0)
            if not pisada:
                continue
            pisadas += 1
            a = math.radians(f["angulo"])
            c, s = math.cos(a), math.sin(a)
            us = [abs((px + 0.5 - x) * c - (py + 0.5 - y) * s) for px, py in _pontos(ImageChops.multiply(letra, m))]
            limite = w * (0.5 - render.MONTE_PISA) * tam + 2
            if len(us) < 25 or max(us) > limite:
                outros.append("colagem %s: foto %d pisada com %d pixeis de letra, ate %.1f do centro, limite %.1f"
                              % (estilo, k + 1, len(us), max(us or [0]), limite))
            # O AVISO CONTA COM A ORLA, como o desenho. Um texto que so corta por causa dela
            # sai com reticencias no video, e contado na largura inteira nao avisava.
            corta_com = render.linhas_texto_foto(texto_largo, render.largura_do_texto(w, render.MONTE_PISA))[2]
            corta_sem = render.linhas_texto_foto(texto_largo, w)[2]
            if corta_com and not corta_sem:
                so_pela_orla += 1
                if ("da foto %d do grupo" % (k + 1)) not in saida.getvalue():
                    outros.append("colagem %s: foto %d cortada so pela orla e sem aviso" % (estilo, k + 1))
    if not pisadas:
        outros.append("nenhuma foto pisada pelas seguintes nas colagens de ensaio")
    if not so_pela_orla:
        outros.append("nenhuma foto pisada com o texto cortado so pela orla: o aviso ficou por medir")

    # TODA A LETRA DESENHADA TEM DE SE VER, e nao so a que sobra. A orla so era descontada
    # de lado, e a faixa continuava encostada ao fundo, que e precisamente onde a fila
    # seguinte pisa: numa colagem em filas de 5 a base das letras da foto 1 ficava debaixo
    # da fila de baixo, "2019" lia-se "2010" com 13% da letra tapada, e ninguem avisava
    # porque para o texto ele cabia. Os testes de cima nao podiam ver isto: o contorno de
    # cada foto ja e desenhado com as seguintes apagadas, portanto a letra tapada nunca
    # contava. Aqui compara-se com a mesma foto composta sozinha na mesma pose: o que
    # desapareceu, desapareceu porque alguem passou por cima.
    from PIL import ImageChops as IC

    def _letra_branca(com, sem):
        """Pixeis quase brancos com texto que nao o eram sem ele: a letra, sem a moldura."""
        def branco(img):
            r, g, b = img.split()
            return IC.darker(IC.darker(r, g), b).point(lambda v: 255 if v > 200 else 0)
        return IC.subtract(branco(com), branco(sem))

    tapadas = []
    for estilo, formas in (("filas", [4 / 3.0, 3 / 4.0, 4 / 3.0, 3 / 4.0, 4 / 3.0]),
                           ("filas", [4 / 3.0] * 5), ("espalhada", [3 / 4.0] * 5),
                           ("espalhada", [4 / 3.0] * 4)):
        n = len(formas)
        ims = [Image.new("RGB", (int(round(400 * a)), 400), CORES_MONTE[k]) for k, a in enumerate(formas)]
        dur = 3 + 1.6 * n
        with contextlib.redirect_stdout(io.StringIO()):
            sem = render.preparar_monte("colagem", ims, [None] * n, "", estilo=estilo)
            com = render.preparar_monte("colagem", ims, [None] * n, "", estilo=estilo,
                                        textos=["NATAL 2019"] * n)
        inicios, entrada, _ = render.estado_monte(sem, 0.0, dur)
        t = inicios[-1] + entrada
        visivel = _letra_branca(render.desenhar_monte(com, t, dur, por_foto=True),
                                render.desenhar_monte(sem, t, dur, por_foto=True))
        poses, _zoom = render.poses_monte(com, t, dur)
        for k, x, y, tam, alfa, _p in poses:
            so_com, so_sem = Image.new("RGB", ecra), Image.new("RGB", ecra)
            render.compor(so_com, com["fotos"][k]["sprite"], x, y, tam / com["cresce"], alfa)
            render.compor(so_sem, sem["fotos"][k]["sprite"], x, y, tam / sem["cresce"], alfa)
            desenhada = _letra_branca(so_com, so_sem)
            posta = desenhada.histogram()[255]
            falta = IC.subtract(desenhada, visivel).histogram()[255]
            if posta < 300 or falta > 0.005 * posta:
                tapadas.append("colagem %s de %d, foto %d: %d de %d pixeis de letra tapados"
                               % (estilo, n, k + 1, falta, posta))
    if tapadas:
        outros += tapadas
    verifica("texto nas fotos: lista curta, aviso do corte e orla pisada no monte", not outros,
             "; ".join(outros[:3]) if outros else
             "pilha e colagem completam a lista, a colagem avisa o corte, %d fotos pisadas sem letra na orla" % pisadas)
    verifica("texto nas fotos: tamanho no ecra com a foto pousada",
             bool(alturas) and all(cap_min - 2 <= a <= cap_max + 2 for a in alturas),
             "maiusculas com %s px, entre %d e %d" % (", ".join("%.0f" % a for a in alturas), cap_min, cap_max))


def teste_texto_nas_fotos_lado_a_lado():
    """No lado a lado, cada texto fica no fundo da sua celula, acima da legenda, e entra com ela.

    O PEDIDO: o texto de cada foto tambem no lado a lado. A faixa cola-se na celula depois
    do zoom lento, por isso fica dentro do retangulo da celula e entra com ela. Mede-se em
    2v, 3v, 3s e 4q, com e sem legenda:
      - nada fora das celulas com texto, antes de entrarem, a entrar e pousadas;
      - letra clara dentro de uma faixa escura, encostada ao fundo da celula;
      - com legenda, nada abaixo do topo da faixa da legenda: duas camadas de preto e o
        texto de baixo nao se lia;
      - no 3s o cartao de cima e uma foto com moldura: a faixa fica dentro da foto dele. E
        as colunas dos lados, com a faixa a subir para cima da legenda, ficavam com o texto
        meio escondido atras do cartao: a letra delas nao chega ao cartao;
      - com o foco na zona da faixa, a faixa vai para o topo da celula, e da foto do cartao;
      - o tamanho das maiusculas no ecra entre o de TEXTO_FOTO_MIN e o de TEXTO_FOTO_TAMANHO;
      - um texto comprido de mais sai em duas linhas, cortado, e com aviso.
    """
    import contextlib
    import io
    from PIL import ImageChops, ImageDraw
    import render
    problemas, alturas = [], []
    cap_min = _altura_das_maiusculas(render, render.TEXTO_FOTO_MIN)
    cap_max = _altura_das_maiusculas(render, render.TEXTO_FOTO_TAMANHO)
    ecra = (render.L, render.A)
    dur = 6.0

    def posicoes(pronto, t):
        """Retangulo de cada celula ja a entrar no instante t, como o desenhar a poe."""
        saida = {}
        for k, cel in enumerate(pronto["celulas"]):
            x, y, w, h = cel["rect"]
            e = (t - cel["atraso"]) / render.LADO_ENTRADA
            if e <= 0:
                continue
            e = 1.0 - (1.0 - min(1.0, e)) ** 3
            dx = dy = 0
            if cel["vem"] == "esq":
                dx = -int(round((1.0 - e) * (x + w)))
            elif cel["vem"] == "dir":
                dx = int(round((1.0 - e) * (render.L - x)))
            else:
                dy = int(round((1.0 - e) * (render.A - y)))
            saida[k] = (x + dx, y + dy, w, h)
        return saida

    def regioes(lay, pos):
        """Onde o texto de cada celula se pode ver: a foto da celula, menos o cartao do 3s por cima."""
        saida = {}
        for k, (x, y, w, h) in pos.items():
            borda = 14 if lay == "3s" and k == 2 else 0
            m = Image.new("L", ecra, 0)
            d = ImageDraw.Draw(m)
            d.rectangle([x + borda, y + borda, x + w - borda - 1, y + h - borda - 1], fill=255)
            if lay == "3s" and k != 2 and 2 in pos:
                cx, cy, cw, ch = pos[2]
                d.rectangle([cx, cy, cx + cw - 1, cy + ch - 1], fill=0)
            saida[k] = m
        return saida

    for lay, n in sorted(render.LAYOUTS_LADO.items()):
        imagens = [Image.new("RGB", (800, 600) if k % 2 == 0 else (450, 600), CORES_MONTE[k]) for k in range(n)]
        textos = ["Verao de 2014" if k != 1 else "" for k in range(n)]
        for legenda in ("", "Verao de 2014\nParis com os amigos"):
            nome = "lado %s%s" % (lay, " com legenda" if legenda else "")
            sem = render.preparar_lado(lay, imagens, [], legenda)
            com = render.preparar_lado(lay, imagens, [], legenda, textos)
            topo_legenda = sem["capa"][1].getbbox()[1] if sem["capa"] else render.A
            ultimo = max(c["atraso"] for c in sem["celulas"])
            for t in (0.0, ultimo + 0.3, dur - 0.04):
                quadro_sem, quadro = render.desenhar(sem, t, dur), render.desenhar(com, t, dur)
                mudou = _mudou(quadro, quadro_sem)
                pos = posicoes(com, t)
                onde = regioes(lay, pos)
                uniao = Image.new("L", ecra, 0)
                for k in onde:
                    if textos[k]:
                        uniao = ImageChops.lighter(uniao, onde[k])
                fora = ImageChops.subtract(mudou, uniao).getbbox()
                if fora:
                    problemas.append("%s aos %.2f s: o texto muda pixeis fora das celulas com texto, em %s"
                                     % (nome, t, fora))
                if t != dur - 0.04:
                    continue        # a entrar, a celula de baixo atravessa a legenda de proposito
                caixa = mudou.getbbox()
                if legenda and caixa and caixa[3] > topo_legenda:
                    problemas.append("%s: faixa de foto a descer ate %d, por baixo da legenda que comeca em %d"
                                     % (nome, caixa[3], topo_legenda))
                letra, faixa = _letra_e_faixa(quadro, quadro_sem, mudou)
                for k in range(n):
                    if not textos[k]:
                        continue
                    lt = ImageChops.multiply(letra, onde[k]).getbbox()
                    fx = ImageChops.multiply(faixa, onde[k])
                    fc = fx.getbbox()
                    if not lt or not fc or fx.histogram()[255] < 300:
                        problemas.append("%s: celula %d sem letra clara sobre faixa escura" % (nome, k + 1))
                        continue
                    if lt[0] < fc[0] or lt[1] < fc[1] or lt[2] > fc[2] or lt[3] > fc[3]:
                        problemas.append("%s: celula %d com a letra %s fora da faixa %s" % (nome, k + 1, lt, fc))
                    # centrada na faixa que se ve, como no monte
                    if abs((lt[0] + lt[2]) / 2.0 - (fc[0] + fc[2]) / 2.0) > 3:
                        problemas.append("%s: celula %d com a letra centrada em %.1f e a faixa em %.1f"
                                         % (nome, k + 1, (lt[0] + lt[2]) / 2.0, (fc[0] + fc[2]) / 2.0))
                    x, y, w, h = pos[k]
                    borda = 14 if lay == "3s" and k == 2 else 0
                    # Acima da legenda com a folga das fotos do monte: a celula que chega a essa
                    # linha leva a faixa para cima dela. E NUNCA COM AS LETRAS ABAIXO DA LINHA
                    # ONDE A LEGENDA ESCREVE, mesmo sem legenda: uma celula que chega ao fundo do
                    # ecra punha as letras a 20 pixeis do rebordo, depois a 54, e um projetor
                    # com overscan de 3 a 5% come mais do que isso. O bloco das linhas da legenda
                    # acaba em A - LEGENDA_TEXTO e o desta faixa acaba na mesma linha: a faixa
                    # acaba uma almofada abaixo, ver limite_da_faixa_no_lado().
                    fundo = y + h - borda
                    # Com o 70 escrito e a almofada contada aqui, e nao por
                    # limite_da_faixa_no_lado(): uma conta do render que mudasse mudava o
                    # esperado com ela, e o teste nao prendia nada.
                    tamanho_px = render.linhas_texto_foto(textos[k], w - 2 * borda)[0]
                    limite = render.A - 70 + int(round(tamanho_px * render.TEXTO_FOTO_ALMOFADA))
                    if limite != render.limite_da_faixa_no_lado(textos[k], w - 2 * borda):
                        problemas.append("%s: limite_da_faixa_no_lado da %d e nao %d" % (
                            nome, render.limite_da_faixa_no_lado(textos[k], w - 2 * borda), limite))
                    if legenda:
                        limite = min(limite, topo_legenda - render.MONTE_LEGENDA_FOLGA * render.A)
                    if fundo > limite:
                        fundo = int(math.floor(limite))
                    if abs(fc[3] - fundo) > 1:
                        problemas.append("%s: celula %d com a faixa a acabar em %d e nao em %d"
                                         % (nome, k + 1, fc[3], fundo))
                    # com o 70 escrito, e nao LEGENDA_TEXTO: e a margem que tem de existir, e
                    # uma constante mais pequena tambem desce a legenda para o rebordo
                    if lt[3] > render.A - 70:
                        problemas.append("%s: celula %d com a letra a descer ate %d, a %d pixeis do "
                                         "fundo do ecra" % (nome, k + 1, lt[3], render.A - lt[3]))
                    if lay == "3s" and k != 2:
                        cx, cy, cw, ch = pos[2]
                        atras = lt[1] < cy + ch and lt[3] > cy and lt[0] < cx + cw and lt[2] > cx
                        if atras or (legenda and ((k == 0 and lt[2] > cx - 2) or (k == 1 and lt[0] < cx + cw + 2))):
                            problemas.append("%s: letra da coluna %d a chegar ao cartao (%s, cartao %s)"
                                             % (nome, k + 1, lt, (cx, cy, cx + cw, cy + ch)))

    # A FAIXA ENTRA COM A CELULA, e nao fica parada a espera dela. Colada na tela na posicao
    # final ficava imovel por cima de uma foto que ainda estava a chegar, e nada disto se via:
    # os testes de cima so exigem que o que muda fique dentro do retangulo da celula, e uma
    # faixa parada tambem la esta. Mede-se a meio da entrada de cada celula e compara-se com a
    # posicao do fim deslocada do mesmo dx e dy que a celula levou, que e o que posicoes() ja
    # conta. A meio da entrada a faixa pode sair do ecra, e ai compara-se so a parte que fica.
    entradas = []
    for lay, n in sorted(render.LAYOUTS_LADO.items()):
        imagens = [Image.new("RGB", (800, 600) if k % 2 == 0 else (450, 600), CORES_MONTE[k]) for k in range(n)]
        sem = render.preparar_lado(lay, imagens, [], "")
        com = render.preparar_lado(lay, imagens, [], "", ["Verao de 2014"] * n)
        fim = dur - 0.04
        q_sem, q_com = render.desenhar(sem, fim, dur), render.desenhar(com, fim, dur)
        _letra, faixa_fim = _letra_e_faixa(q_com, q_sem, _mudou(q_com, q_sem))
        onde_fim = regioes(lay, posicoes(com, fim))
        for k, cel in enumerate(com["celulas"]):
            parada = ImageChops.multiply(faixa_fim, onde_fim[k]).getbbox()
            if not parada:
                problemas.append("lado %s: celula %d sem faixa para medir a entrada" % (lay, k + 1))
                continue
            # A que sobe de baixo leva a faixa para fora do ecra a meio da entrada, e ai nao
            # ha nada para comparar: escolhe-se o primeiro instante em que ela ja se ve
            # inteira e a celula ainda esta a mais de 6 pixeis do lugar.
            esperado = dx = dy = pos = None
            for parte in (0.5, 0.7, 0.85):
                sitio = posicoes(com, cel["atraso"] + parte * render.LADO_ENTRADA)
                if k not in sitio:
                    continue
                ax, ay = sitio[k][0] - cel["rect"][0], sitio[k][1] - cel["rect"][1]
                caixa = (parada[0] + ax, parada[1] + ay, parada[2] + ax, parada[3] + ay)
                if (abs(ax) + abs(ay) >= 6 and 0 <= caixa[1] and caixa[3] <= render.A
                        and max(0, caixa[0]) < min(render.L, caixa[2])):
                    esperado, dx, dy, pos = caixa, ax, ay, sitio
                    t = cel["atraso"] + parte * render.LADO_ENTRADA
                    break
            if esperado is None:
                problemas.append("lado %s: celula %d sem instante para medir a entrada" % (lay, k + 1))
                continue
            a_sem, a_com = render.desenhar(sem, t, dur), render.desenhar(com, t, dur)
            _l, faixa_meio = _letra_e_faixa(a_com, a_sem, _mudou(a_com, a_sem))
            meio = ImageChops.multiply(faixa_meio, regioes(lay, pos)[k]).getbbox()
            esperado = (max(0, esperado[0]), esperado[1], min(render.L, esperado[2]), esperado[3])
            if not meio or max(abs(a - b) for a, b in zip(meio, esperado)) > 2:
                problemas.append("lado %s: a faixa da celula %d a meio da entrada esta em %s e "
                                 "devia estar em %s, com a celula a %d, %d do lugar"
                                 % (lay, k + 1, meio, esperado, dx, dy))
            else:
                entradas.append("%s %d" % (lay, k + 1))

    # O foco na zona da faixa leva-a para o topo: numa coluna do 2v e na foto do cartao do 3s.
    # O do 2v, a 0,94, so cai na faixa no inicio do zoom lento: no fim a respiracao ja o
    # levou para fora da faixa. Um foco que so contasse no fim deixava a faixa em cima da cara
    # durante a entrada. Mais abaixo caia na faixa nas duas pontas e isso nao se via. Era 0,99
    # enquanto a faixa acabava no fundo do ecra, 0,96 quando guardava LEGENDA_FUNDO; desde que
    # o bloco das linhas guarda LEGENDA_TEXTO, a faixa de "NATAL" a 46 vai de 941 a 1024 e o
    # foco a 0,94 cai em 1016 no inicio do zoom e em 1035 no fim.
    # E O FOCO ABAIXO DA FAIXA TAMBEM A MANDA PARA CIMA: a 0,97 o ponto cai em 1048, nos 22
    # pixeis de fotografia que ficam por baixo da faixa desde que ela guarda a margem da
    # legenda. Com a regra do ponto seco a faixa ficava em baixo, 18 pixeis acima do centro
    # da cara, e tapava-lhe a metade de cima; e a regra da colagem e da pilha, colocar_faixa(),
    # que sobe a faixa com o foco do topo dela para baixo.
    # E UM FOCO ENTRE AS DUAS PONTAS DO ZOOM: a 0,865 o ponto cai em 934 no inicio do zoom
    # lento, 7 pixeis ACIMA do topo da faixa de "NATAL" (941), e em 950 no fim, 9 abaixo. Desde
    # a regra "do topo para baixo" os focos de cima caem na faixa nas duas pontas, e contar so
    # a ponta inicial deixava esta faixa em baixo, em cima da cara no fim do zoom. Contar so a
    # ponta final e o mesmo que contar as duas para qualquer foco abaixo do centro da celula.
    for lay, focos, textos in (("2v", [(0.5, 0.94), None], ["NATAL", "NATAL"]),
                               ("2v", [(0.5, 0.865), None], ["NATAL", "NATAL"]),
                               ("2v", [None, (0.5, 0.97)], ["NATAL", "NATAL"]),
                               ("3v", [(0.5, 0.99), None, None], ["NATAL", "", "NATAL"]),
                               ("3s", [None, None, (0.5, 0.95)], ["", "", "NATAL"])):
        n = len(textos)
        imagens = [Image.new("RGB", (800, 600), CORES_MONTE[k]) for k in range(n)]
        sem = render.preparar_lado(lay, imagens, focos, "")
        com = render.preparar_lado(lay, imagens, focos, "", textos)
        quadro_sem, quadro = render.desenhar(sem, dur - 0.04, dur), render.desenhar(com, dur - 0.04, dur)
        mudou = _mudou(quadro, quadro_sem)
        _letra, faixa = _letra_e_faixa(quadro, quadro_sem, mudou)
        onde = regioes(lay, posicoes(com, dur - 0.04))
        for k in range(n):
            if not textos[k]:
                continue
            x, y, w, h = com["celulas"][k]["rect"]
            borda = 14 if lay == "3s" and k == 2 else 0
            fc = ImageChops.multiply(faixa, onde[k]).getbbox()
            esperado = y + borda if focos[k] else min(y + h - borda,
                                                     render.limite_da_faixa_no_lado(textos[k], w - 2 * borda))
            obtido = (fc[1] if focos[k] else fc[3]) if fc else None
            if obtido is None or abs(obtido - esperado) > 1:
                problemas.append("lado %s: celula %d com foco %s e faixa a %s em vez de %d"
                                 % (lay, k + 1, focos[k], obtido, esperado))

    # O tamanho no ecra: quatro celulas de 4q, sem legenda.
    imagens = [Image.new("RGB", (800, 600), CORES_MONTE[k]) for k in range(4)]
    sem = render.preparar_lado("4q", imagens, [], "")
    com = render.preparar_lado("4q", imagens, [], "", ["NATAL"] * 4)
    quadro_sem, quadro = render.desenhar(sem, dur - 0.04, dur), render.desenhar(com, dur - 0.04, dur)
    letra, _faixa = _letra_e_faixa(quadro, quadro_sem, _mudou(quadro, quadro_sem))
    for k, (x, y, w, h) in posicoes(com, dur - 0.04).items():
        caixa = letra.crop((x, y, x + w, y + h)).getbbox()
        alturas.append(caixa[3] - caixa[1] if caixa else 0)

    # O comprido: duas linhas desenhadas, cortado, e o aviso.
    imagens = [Image.new("RGB", (800, 600), CORES_MONTE[k]) for k in range(3)]
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        longo = render.preparar_lado("3v", imagens, [], "", [TEXTO_LONGO, "", ""])
    x, y, w, h = longo["celulas"][0]["rect"]
    linhas = _faixas_de_texto(render.desenhar(longo, dur - 0.04, dur).crop((x, y, x + w, y + h)), 240)
    tamanho, escritas, cortado = render.linhas_texto_foto(TEXTO_LONGO, w)
    avisou = "AVISO" in saida.getvalue() and "foto 1" in saida.getvalue()
    if linhas != 2 or not cortado or len(escritas) != 2 or not avisou:
        problemas.append("texto comprido: %d linhas desenhadas, %d escritas, cortado %s, aviso %s"
                         % (linhas, len(escritas), cortado, avisou))
    verifica("texto nas fotos: lado a lado, dentro de cada celula", not problemas and len(entradas) >= 8,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else
             "2v, 3v, 3s e 4q, com e sem legenda, com foco e comprido, %d faixas a entrar com a celula"
             % len(entradas))
    verifica("texto nas fotos: tamanho no ecra no lado a lado",
             len(alturas) == 4 and all(cap_min - 1 <= a <= cap_max + 1 for a in alturas),
             "maiusculas com %s px, entre %d e %d" % (alturas, cap_min, cap_max))


def teste_linhas_texto_foto():
    """O texto de uma foto desce de tamanho para caber em duas linhas, nunca abaixo do minimo, e so entao corta.

    O PEDIDO: texto grande, que se leia a 15 metros, e nunca a sair da fotografia. Para
    muitas larguras e textos: o tamanho fica entre TEXTO_FOTO_MIN e TEXTO_FOTO_TAMANHO
    (escalados com A), no maximo TEXTO_FOTO_LINHAS linhas, cada uma dentro da largura menos
    a folga; sem corte nenhuma palavra se perde, e com corte o tamanho e o minimo e a ultima
    linha acaba em reticencias. E tem de haver casos que descem de tamanho sem cortar, senao
    a descida nao estava a fazer nada.
    """
    from PIL import ImageDraw, ImageFont
    import render
    problemas = []
    # O ALFA E O DA LEGENDA, 165, E NAO CHEGA VERIFICAR A CONSTANTE: e o que a faixa deixa
    # passar do que esta por baixo que decide se o branco sobre escuro do CLAUDE.md o e.
    # Com 120 a faixa deixava passar 135 de 255 em vez de 90, sobre uma foto clara o texto
    # deixava de se ler a 15 metros, e tudo passava; so um alfa muito alto era apanhado.
    # Mede-se onde a capa nao tem letra, que e a faixa lisa.
    # O TAMANHO E O DA LEGENDA, 46, E O MINIMO E PROPORCIONAL: 46 da 36 e 36 da 28, o par
    # de antes. Ver minimo_texto_foto().
    if (render.TEXTO_FOTO_TAMANHO, render.TEXTO_FOTO_MIN, render.TEXTO_FOTO_LINHAS,
            render.TEXTO_FOTO_ALFA) != (46, 36, 2, 165):
        problemas.append("constantes %s em vez de 46, 36, 2 e 165" % (
            (render.TEXTO_FOTO_TAMANHO, render.TEXTO_FOTO_MIN, render.TEXTO_FOTO_LINHAS,
             render.TEXTO_FOTO_ALFA),))
    minimos = [render.minimo_texto_foto(t) for t in (28, 36, 46, 60, 75, 90)]
    if minimos != [22, 28, 36, 47, 59, 70] or render.minimo_texto_foto() != 36:
        problemas.append("minimos %s em vez de 22, 28, 36, 47, 59, 70" % (minimos,))
    # o minimo da capa e a faixa lisa; a letra e os seus esbatidos ficam acima
    capa_alfa = render.capa_texto_foto("Natal", 400)[0].split()[3].getextrema()[0]
    legenda_alfa = render.faixa_texto("Natal")[1].getpixel((2, render.A - render.LEGENDA_FUNDO - 6))
    if capa_alfa != 165 or legenda_alfa != 165:
        problemas.append("alfa %d na faixa da foto e %d na da legenda, tem de ser 165 nas duas"
                         % (capa_alfa, legenda_alfa))
    # E O ESCURECIMENTO MEDE-SE NO FOTOGRAMA, nao so na capa: sobre branco, a faixa lisa
    # tem de ficar a 255 x (1 - 165/255) = 90, na foto, na celula do lado a lado e na
    # legenda. Uma mascara aclarada ao colar passava pela verificacao da capa.
    branca = Image.new("RGB", (400, 300), (255, 255, 255))
    topo_faixa, _c = render.faixa_na_foto(branca, "NATAL")
    escuros = [branca.getpixel((6, topo_faixa + 4))[0]]
    lado = render.preparar_lado("2v", [Image.new("RGB", (800, 600), (255, 255, 255))] * 2, [], "",
                                ["NATAL", "NATAL"])
    quadro = render.desenhar(lado, 5.9, 6.0)
    x0, y0 = lado["celulas"][0]["faixa"][2]
    escuros.append(quadro.getpixel((x0 + 6, y0 + 4))[0])
    quadro = Image.new("RGB", (render.L, render.A), (255, 255, 255))
    cor, mascara = render.faixa_texto("NATAL")
    quadro.paste(cor, (0, 0), mascara)
    escuros.append(quadro.getpixel((6, render.A - render.LEGENDA_FUNDO - 6))[0])
    if any(abs(v - 90) > 1 for v in escuros):
        problemas.append("faixa sobre branco a %s, tem de ficar a 90 na foto, no lado a lado e na legenda"
                         % (escuros,))
    grande, pequeno = render.no_ecra(render.TEXTO_FOTO_TAMANHO), render.no_ecra(render.TEXTO_FOTO_MIN)
    folga = 2 * render.no_ecra(render.TEXTO_FOTO_FOLGA)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    desceram = cortaram = 0
    for texto in ("Natal", "2019", "Verao de 2014", "Verao de 2014 em Paris",
                  "Paris com os amigos no verao de 2014", TEXTO_LONGO, "Supercalifragilisticoespialidoso"):
        for largura in range(160, 1000, 12):
            tamanho, linhas, cortado = render.linhas_texto_foto(texto, largura)
            fonte = ImageFont.truetype(render.FONTE_TEXTO, tamanho)
            larguras = [d.textbbox((0, 0), l, font=fonte)[2] for l in linhas]
            caso = "%r em %d px" % (texto[:20], largura)
            if not pequeno <= tamanho <= grande:
                problemas.append("%s: tamanho %d fora de %d a %d" % (caso, tamanho, pequeno, grande))
            if not 1 <= len(linhas) <= render.TEXTO_FOTO_LINHAS or max(larguras) > largura - folga:
                problemas.append("%s: %d linhas, a mais larga com %d px" % (caso, len(linhas), max(larguras or [0])))
            if cortado:
                cortaram += 1
                if tamanho != pequeno or not linhas[-1].endswith(render.RETICENCIAS):
                    problemas.append("%s: cortado a %d px sem reticencias no fim" % (caso, tamanho))
            elif " ".join(linhas).split() != texto.split():
                problemas.append("%s: sem corte, mas as linhas %s nao sao o texto" % (caso, linhas))
            elif tamanho < grande:
                desceram += 1
                cabe = render.quebrar_paragrafos(texto, ImageFont.truetype(render.FONTE_TEXTO, tamanho + 2),
                                                 largura - folga, d)
                maior = ImageFont.truetype(render.FONTE_TEXTO, tamanho + 2)
                if len(cabe) <= 2 and all(d.textbbox((0, 0), l, font=maior)[2] <= largura - folga for l in cabe):
                    problemas.append("%s: desceu a %d quando %d ja cabia" % (caso, tamanho, tamanho + 2))
    vazio = render.linhas_texto_foto("", 400)
    curto = render.linhas_texto_foto("Natal", 400)
    longo = render.linhas_texto_foto(TEXTO_LONGO, 300)
    if vazio != (grande, [], False) or curto != (grande, ["Natal"], False):
        problemas.append("vazio %s e curto %s" % (vazio, curto))
    if not (longo[0] == pequeno and len(longo[1]) == 2 and longo[2]):
        problemas.append("comprido em 300 px: %s" % (longo,))

    # A FAIXA TEM A ALTURA DAS LINHAS TODAS. Com a altura de uma so, a 2.a linha saia
    # quase toda fora, e o teste do lado a lado contava na mesma duas linhas pelas pontas
    # das letras que sobravam. Mede-se a capa: a altura certa, e letra nas duas bandas.
    tam_longo, linhas_longo, _c = render.linhas_texto_foto(TEXTO_LONGO, 300)
    capa, _c = render.capa_texto_foto(TEXTO_LONGO, 300)
    alt_linha = int(round(tam_longo * render.TEXTO_FOTO_ENTRELINHA))
    almofada = int(round(tam_longo * render.TEXTO_FOTO_ALMOFADA))
    branco = capa.convert("L").point(lambda v: 255 if v >= 200 else 0)
    bandas = [branco.crop((0, almofada + i * alt_linha, capa.width, almofada + (i + 1) * alt_linha)).histogram()[255]
              for i in range(2)]
    if (capa.height != len(linhas_longo) * alt_linha + 2 * almofada or len(linhas_longo) != 2
            or min(bandas) < 0.5 * max(bandas)):
        problemas.append("faixa de 2 linhas com %d px de altura (%d linhas a %d), letra por banda %s"
                         % (capa.height, len(linhas_longo), alt_linha, bandas))

    # OS PARAGRAFOS A MAIS JUNTAM-SE ANTES DE ESCOLHER O TAMANHO: tres linhas curtas cabem a
    # 36, e a Mesa mostra o mesmo. Antes desciam ao minimo sem faltar largura.
    tres = render.linhas_texto_foto("Natal\n2019\nPorto", 600)
    if tres != (grande, ["Natal", "2019 Porto"], False):
        problemas.append("tres paragrafos curtos em 600 px: %s" % (tres,))

    # O TAMANHO ESCALA COM A. Os testes correm a 1080, onde um no_ecra() sem A e igual, mas
    # o render --escala muda L e A: a 720 a letra de 36 tem de ser 24, a de 46 tem de ser
    # 31, e a faixa dois tercos.
    capa_1080 = render.capa_texto_foto("Natal", 400)[0].height
    guardado = (render.L, render.A)
    try:
        render.L, render.A = 1280, 720
        tam_720 = render.linhas_texto_foto("Natal", 400, 36)[0]
        tam_720_omissao = render.linhas_texto_foto("Natal", 400)[0]
        capa_720 = render.capa_texto_foto("Natal", 400)[0].height
    finally:
        render.L, render.A = guardado
    if tam_720 != 24 or tam_720_omissao != 31 or abs(capa_720 - capa_1080 * 720 / 1080.0) > 1:
        problemas.append("a 1280x720: letra %d em vez de 24 e %d em vez de 31, faixa %d px contra %d a 1080"
                         % (tam_720, tam_720_omissao, capa_720, capa_1080))
    verifica("texto nas fotos: tamanho desce ate ao minimo e so depois corta",
             not problemas and desceram > 0 and cortaram > 0,
             "; ".join(problemas[:3]) if problemas else
             "%d casos desceram sem cortar, %d cortaram no minimo" % (desceram, cortaram))


# Tiradas do render do FIM DA RONDA ANTERIOR (texto em cada foto a 36, sem opcoes), com
# Pillow 12.3.0, por assinaturas_texto_36(). Com {"tamanho": 36, "tapadas": "fica"} o render
# de agora tem de dar estes bytes: e a prova de que o tamanho novo e o desaparecer na pilha
# nao mexeram em mais nada. So grupos que o H2 nao muda: no lado a lado, com legenda.
# REFEITAS A 17 DE SETEMBRO, pela agenda que divide a duracao pelas fotos, e da mesma maneira
# que as ASSINATURAS_SEM_TEXTO: a colagem de 5 em 11 s entrava de 1,5 em 1,5 s e passou a 1,6 s,
# e as duas pilhas como la. Eram 68cdd36b696bae860ec261291bdbabfc, 0f128f7d279179f124917e545631487a
# e ba3f0e4d55af372adea1bc71957703d4.
ASSINATURAS_TEXTO_36 = {
    "colagem filas de 4": "64b0ff1be580c77e42d430f860e1229f",
    "colagem filas de 5 com legenda": "2b0317298cb096287f774ba432d28d4e",
    "colagem espalhada de 3 com legenda": "f80aeecf1da3890e1590cf58797d0496",
    "pilha monte de 5": "ac61bcf2b0aa217b013c4b3d00b30aec",
    "pilha leque de 4 com legenda": "e38025185fe8decbd02a3805f321b911",
    # REFEITA A 16 DE SETEMBRO, com o render desta ronda: o foco a 0,97 da 2.a celula cai
    # abaixo da faixa, e desde a correcao do lado_faixas() manda-a para o topo, como na
    # colagem e na pilha; a ronda anterior deixava-a em baixo (era 70a113340886cc97d5679763e6d81f2c).
    # O que muda esta so nessa celula, acima da legenda, medido contra o render de antes.
    "lado 2v de 2 com legenda": "e57a46fae43ffc703b04b8072123aeef",
    "lado 3v de 3 com legenda": "c22d472ead17129fec62d0be72b74f24",
    "lado 3s de 3 com legenda": "07746acfcc540ba85cf0ca8970b856fe",
    "lado 4q de 4 com legenda": "577c217f2fb618d61f7e2b320335c0a5",
}
TEXTOS_36 = ["Natal", "Verao de 2014", "", "2019", "Natal de 2019 em casa"]


def assinaturas_texto_36(render, pasta, opcoes=None):
    """md5 de tres fotogramas de cada grupo de controlo COM textos, pelo preparar() do `render` dado.

    `opcoes` e a coluna textos_opcoes; o render da ronda anterior ignora-a, e e assim que
    se tiram as assinaturas. As fotos sao as de assinaturas_sem_texto().
    """
    import hashlib
    import json
    formas = [4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0, 1.0]
    caminhos = []
    for k, a in enumerate(formas):
        c = os.path.join(pasta, "gradiente%d.png" % k)
        if not os.path.exists(c):
            _foto_gradiente(k, a).save(c)
        caminhos.append(c)
    casos = [("colagem", "filas", 4, "", "|0.5000,0.9700"), ("colagem", "filas", 5, "Amigos", ""),
             ("colagem", "espalhada", 3, "Amigos", "||0.5,0.95"), ("pilha", "monte", 5, "", "0.5,0.95"),
             ("pilha", "leque", 4, "Amigos", ""), ("lado", "2v", 2, "Natal", "|0.5000,0.9700"),
             ("lado", "3v", 3, "Natal", ""), ("lado", "3s", 3, "Amigos", "0.2,0.2||0.5,0.95"),
             ("lado", "4q", 4, "Verao de 2014\nParis com os amigos", "0.3000,0.4100|0.6000,0.5500||0.5,0.45")]
    saida = {}
    import contextlib
    import io
    for tipo, tratamento, n, legenda, focos in casos:
        clip = {"tipo": tipo, "texto_ecra": legenda, "tratamento": tratamento, "fonte_imagem": focos,
                "ficheiro": "", "id": "", "transicao_s": "0.7", "duracao_s": "7", "_caminhos": caminhos[:n],
                "textos_fotos": json.dumps(TEXTOS_36[:n])}
        if opcoes is not None:
            clip["textos_opcoes"] = opcoes
        with contextlib.redirect_stdout(io.StringIO()):
            pronto = render.preparar(clip, {})
        if tipo == "lado":
            dur = 6.0
        else:
            dur = 3 + 1.6 * n if tipo == "colagem" else 2.6 + 0.85 * n
        md5 = hashlib.md5()
        for t in (0.9, dur / 2.0, dur - 0.04):
            md5.update(render.desenhar(pronto, t, dur).tobytes())
        saida["%s %s de %d%s" % (tipo, tratamento, n, " com legenda" if legenda else "")] = md5.hexdigest()
    return saida


def _letra_branca(com, sem):
    """Pixeis quase brancos com texto que nao o eram sem ele: a letra, sem a moldura."""
    from PIL import ImageChops as IC

    def branco(img):
        r, g, b = img.split()
        return IC.darker(IC.darker(r, g), b).point(lambda v: 255 if v > 200 else 0)
    return IC.subtract(branco(com), branco(sem))


def _fotos_lisas(n, lado=600):
    """Fotos de uma cor so, com as formas misturadas do monte."""
    return [Image.new("RGB", (int(round(lado * a)), lado), CORES_MONTE[k])
            for k, a in enumerate(_formas_monte(n)["misturadas"])]


def teste_legenda_por_foto():
    """Na opcao "na legenda de baixo", a faixa de baixo mostra o texto da foto que esta a entrar, e nada muda nas fotos.

    O PEDIDO, do Tiago a 15 de setembro: "Em vez de metermos o texto a aparecer em cada foto
    individualmente, metemos o texto master a alterar, assim pode ser uma forma mais facil de
    o texto ficar legivel. Esta e uma opcao adicional". Nos quatro estilos da colagem e da
    pilha e nas quatro disposicoes do lado a lado, com e sem texto do grupo, cada fotograma
    compara-se BYTE A BYTE com o mesmo grupo sem textos (as fotos, pousadas para a legenda do
    texto mais alto) mais a faixa_texto() do texto certo por cima:
      - o texto e o da foto cujo troco de tempos_legenda_grupo() contem o instante, e antes
        de a primeira entrar ja e o dela; uma foto sem texto mostra o do grupo, e sem grupo
        nao ha faixa nesse troco;
      - a faixa tem sempre a altura do texto mais alto, e as fotos nao mudam de sitio;
      - nenhuma faixa dentro das fotos (as fotos sao as de sem textos);
      - com 46, cada faixa e a faixa_texto() de hoje com essa altura;
      - a troca leva LEGENDA_TROCA com as duas faixas misturadas, a faixa escura fica igual
        quando ha texto dos dois lados e desvanece a meio quando um deles e nenhum;
      - e a um quarto, a meio e a tres quartos da troca o fotograma e a mistura EXATA dos dois
        fotogramas compostos, a menos de 3 de arredondamento: e o pre-multiplicado que o
        garante, e sem ele as letras afundavam a meio da troca;
      - textos iguais seguidos nao trocam;
      - com outro tamanho a letra muda na proporcao;
      - o preparar avisa dos textos que ficam menos de LEGENDA_MINIMO_S, e so desses.
    """
    import contextlib
    import io
    import tempfile
    from PIL import ImageChops
    import render
    problemas, comparados, misturas = [], 0, 0
    # O quinto texto tem duas linhas, para a banda ser mais alta do que os outros: e isso que
    # prende a altura constante, com os de uma linha centrados nela.
    textos = ["Natal", "", "Verao de 2014", "Verao de 2014",
              "Paris com os amigos no verao de 2014\njunto ao rio e depois a praia"]
    # Com e sem texto do grupo alternados entre os grupos, para nao dobrar o tempo: o vazio
    # da foto 2 cai no do grupo onde o ha, e fica sem faixa onde nao ha.
    grupos = [("colagem", "filas", 5, ("", "Amigos")), ("colagem", "espalhada", 4, ("",)),
              ("pilha", "monte", 5, ("Amigos",)), ("pilha", "leque", 4, ("",)),
              ("lado", "2v", 2, ("",)), ("lado", "3v", 3, ("Amigos",)), ("lado", "3s", 3, ("Amigos", "")),
              ("lado", "4q", 4, ("",))]
    for tipo, estilo, n, grupos_texto in grupos:
        imagens = _fotos_lisas(n)
        focos = [None, (0.5, 0.95)] + [None] * (n - 2)
        for grupo in grupos_texto:
            nome = "%s %s%s" % (tipo, estilo, " com grupo" if grupo else "")
            dur = 7.0 if tipo == "lado" else (3 + 1.6 * n if tipo == "colagem" else 2.6 + 0.85 * n)
            mostrados = [t or grupo for t in textos[:n]]
            mais_alto = max((t for t in mostrados if t), key=lambda t: render.bloco_legenda(t))
            with contextlib.redirect_stdout(io.StringIO()):
                if tipo == "lado":
                    com = render.preparar_lado(estilo, imagens, focos, grupo, textos[:n], {"modo": "legenda"})
                    ref = render.preparar_lado(estilo, imagens, focos, mais_alto)
                    inicios = [c["atraso"] for c in ref["celulas"]]
                else:
                    com = render.preparar_monte(tipo, imagens, focos, grupo, estilo=estilo, textos=textos[:n],
                                                opcoes={"modo": "legenda"})
                    ref = render.preparar_monte(tipo, imagens, focos, mais_alto, estilo=estilo)
                    inicios = render.estado_monte(ref, 0.0, dur)[0]
            ref["capa"] = None          # so as fotos, pousadas para a legenda do texto mais alto
            banda = render.bloco_legenda(mais_alto)
            faixas = {t: render.faixa_texto(t, 46, banda) for t in set(mostrados) if t}
            tempos = render.tempos_legenda_grupo(tipo, n, dur, 0.0, 0.0, estilo)
            if [round(a, 6) for a, _b in tempos] != [0.0] + [round(i, 6) for i in inicios[1:]] \
                    or [round(b, 6) for _a, b in tempos] != [round(i, 6) for i in inicios[1:]] + [dur]:
                problemas.append("%s: tempos %s nao sao os inicios %s" % (nome, tempos, inicios))
            if com.get("legenda") is None or com["legenda"]["topo"] != render.A - 70 - banda - 26:
                problemas.append("%s: a faixa nao tem a altura do texto mais alto" % nome)

            def esperado(t, texto):
                quadro = render.desenhar(ref, t, dur)
                if texto:
                    cor, mascara = faixas[texto]
                    quadro.paste(cor, (0, 0), mascara)
                return quadro

            for i, (ini, fim) in enumerate(tempos):
                instantes = [(ini + render.LEGENDA_TROCA + 0.05, "depois da troca"), (fim - 0.02, "no fim do troco")]
                if i == 0:
                    instantes.append((0.0, "antes de a primeira entrar"))
                if i > 0 and mostrados[i - 1] == mostrados[i]:
                    instantes.append((ini + render.LEGENDA_TROCA / 2.0, "a meio de uma troca entre iguais"))
                for t, rotulo in instantes:
                    comparados += 1
                    if render.desenhar(com, t, dur).tobytes() != esperado(t, mostrados[i]).tobytes():
                        problemas.append("%s, foto %d, %s (%.2f s): o fotograma nao e as fotos mais a faixa %r"
                                         % (nome, i + 1, rotulo, t, mostrados[i]))
                if i == 0 or mostrados[i - 1] == mostrados[i]:
                    continue
                # A MEIO DA TROCA: nem um nem outro, e a faixa escura igual (texto dos dois lados)
                # ou a meio caminho (um lado sem texto). Mede-se num pixel da banda sem letra.
                misturas += 1
                t = ini + render.LEGENDA_TROCA / 2.0
                meio = render.desenhar(com, t, dur)
                antes, depois = esperado(t, mostrados[i - 1]), esperado(t, mostrados[i])
                if meio.tobytes() in (antes.tobytes(), depois.tobytes()):
                    problemas.append("%s, foto %d: sem encadeado na troca de %r para %r"
                                     % (nome, i + 1, mostrados[i - 1], mostrados[i]))
                    continue
                # E A MISTURA E A EXATA DOS DOIS FOTOGRAMAS COMPOSTOS, a um quarto, a meio e a
                # tres quartos da troca: e o que faz a faixa escura nao piscar e a letra nao
                # afundar. As pontas e o "ha mistura" de cima nao o prendiam: com as duas bandas
                # misturadas em RGBA direto em vez de em pre-multiplicado, as letras afundavam
                # sobre preto a meio da troca (medido: 18 a 23 de 255 entre dois textos, 48 a 64
                # de texto para nenhum) e tudo passava. O render certo fica a 2, que e so o
                # arredondamento de ir e voltar do pre-multiplicado. Compara-se com o
                # Image.blend dos dois fotogramas que o proprio teste ja constroi.
                troca = render.troca_da_legenda(tempos, i)
                for fracao in (0.25, 0.5, 0.75):
                    t_f = ini + fracao * troca
                    exata = Image.blend(esperado(t_f, mostrados[i - 1]), esperado(t_f, mostrados[i]), fracao)
                    pior = max(hi for _lo, hi in ImageChops.difference(render.desenhar(com, t_f, dur), exata).getextrema())
                    if pior > 3:
                        problemas.append("%s, foto %d: a %.2f da troca de %r para %r o fotograma difere ate %d "
                                         "de 255 da mistura exata dos dois" % (nome, i + 1, fracao, mostrados[i - 1],
                                                                                mostrados[i], pior))
                # na primeira fila da banda e na ultima, a de A - LEGENDA_FUNDO: a ultima ficava
                # de fora da mistura e piscava
                so_fotos = render.desenhar(ref, t, dur)
                for y in (com["legenda"]["topo"] + 6, render.A - render.LEGENDA_FUNDO):
                    fundo = so_fotos.getpixel((6, y))
                    obtido = meio.getpixel((6, y))
                    if mostrados[i - 1] and mostrados[i]:
                        alvo = depois.getpixel((6, y))
                    else:
                        alvo = tuple(int(round(f * (1 - 0.5 * 165 / 255.0))) for f in fundo)
                    if max(abs(a - b) for a, b in zip(obtido, alvo)) > 2:
                        problemas.append("%s, foto %d: a faixa escura a meio da troca, na fila %d, esta a %s e devia "
                                         "estar a %s" % (nome, i + 1, y, obtido, alvo))
                # e o que mudou em relacao aos dois lados fica dentro da banda, que inclui a
                # fila A - LEGENDA_FUNDO: o retangulo da legenda e desenhado ate ela
                for outro in (antes, depois):
                    caixa = _mudou(meio, outro).getbbox()
                    if caixa and (caixa[1] < com["legenda"]["topo"] or caixa[3] > render.A - render.LEGENDA_FUNDO + 1):
                        problemas.append("%s, foto %d: a troca mexe fora da banda, em %s" % (nome, i + 1, caixa))
    # OUTRO TAMANHO: a letra da faixa muda na proporcao, e a banda continua a de faixa_texto().
    # NO LADO A LADO, NA COLAGEM E NA PILHA: cada preparar passa o tamanho a legenda_por_foto()
    # por sua conta, e so o do lado a lado estava preso. Um preparar_monte que o deixasse cair
    # dava a letra de 46 no video a quem escolheu 60 na Mesa, com a Mesa a mostrar 60.
    imagens = _fotos_lisas(3)
    alturas = {}
    dur_monte = 3 + 1.6 * 3
    for tam in (46, 60):
        for tipo, estilo in (("lado", "3v"), ("colagem", "filas"), ("pilha", "monte")):
            with contextlib.redirect_stdout(io.StringIO()):
                if tipo == "lado":
                    p = render.preparar_lado("3v", imagens, [], "", ["NATAL", "NATAL", "NATAL"],
                                             {"modo": "legenda", "tamanho": tam})
                    quadro = render.desenhar(p, 6.9, 7.0)
                    sem = render.desenhar(render.preparar_lado("3v", imagens, [], ""), 6.9, 7.0)
                else:
                    p = render.preparar_monte(tipo, imagens, None, "", estilo=estilo, textos=["NATAL"] * 3,
                                              opcoes={"modo": "legenda", "tamanho": tam})
                    # as fotos pousam para a legenda deste tamanho: a referencia e o mesmo grupo
                    # com "NATAL" no grupo, com a mesma letra, e a capa tirada
                    ref = render.preparar_monte(tipo, imagens, None, "", estilo=estilo, textos=["NATAL"] * 3,
                                                opcoes={"modo": "legenda", "tamanho": tam})
                    ref["legenda"] = None
                    quadro = render.desenhar(p, dur_monte - 0.04, dur_monte)
                    sem = render.desenhar(ref, dur_monte - 0.04, dur_monte)
            caixa = _letra_branca(quadro, sem).getbbox()
            alturas[(tam, tipo)] = caixa[3] - caixa[1] if caixa else 0
            esperada = _altura_das_maiusculas(render, tam)
            if abs(alturas[(tam, tipo)] - esperada) > 2 or p["legenda"]["tamanho"] != tam:
                problemas.append("legenda a %d no %s: maiusculas com %d px em vez de %d, tamanho preparado %s"
                                 % (tam, tipo, alturas[(tam, tipo)], esperada, p["legenda"]["tamanho"]))
    # E O MINIMO A QUE A LEGENDA DESCE ESCALA COM O TAMANHO: 30 para 46, que e a sequencia de
    # sempre, 39 para 60, 33 para 50 e 20 para 30. Um minimo fixo em 30 deixava um texto
    # comprido a 60 descer para metade da letra pedida. O texto tem de ser comprido de mais
    # para caber em quatro linhas EM QUALQUER DESTES TAMANHOS, senao a descida para antes do
    # minimo e nao e o minimo que se mede: quatro vezes TEXTO_LONGO cabia a 26 e o teste
    # pedia 20 a um render certo. E o 50 e o que distingue floor(x + 0,5), que da 33 e e o
    # que a Mesa faz com Math.round, de um floor seco, que da 32.
    muito = " ".join([TEXTO_LONGO] * 8)
    descidas = {tam: render.linhas_legenda(muito, tam)[0] for tam in (46, 60, 50, 30)}
    if descidas != {46: 30, 60: 39, 50: 33, 30: 20} or render.linhas_legenda("Natal", 60)[0] != 60:
        problemas.append("minimo da legenda por tamanho: %s, e 'Natal' a 60 fica a %d"
                         % (descidas, render.linhas_legenda("Natal", 60)[0]))
    # UM TEXTO DE UMA LINHA CENTRA-SE NA BANDA DE DUAS. Medido pela tinta e nao pela conta de
    # faixa_texto(): a banda cresce para cima, com o fundo fixo em A - LEGENDA_TEXTO, e a
    # mesma letra numa banda mais alta tem de SUBIR exatamente metade do que a banda cresceu
    # em relacao a sua propria faixa. Encostada ao fundo da banda nao subia nada.
    bloco_1 = int(46 * 1.35)
    banda_2 = 2 * bloco_1
    so_ela = render.faixa_texto("Natal", 46)[1].getbbox()
    tinta_1 = _letra_branca(render.faixa_texto("Natal", 46)[0], Image.new("RGB", (render.L, render.A))).getbbox()
    tinta_2 = _letra_branca(render.faixa_texto("Natal", 46, banda_2)[0], Image.new("RGB", (render.L, render.A))).getbbox()
    if (not tinta_1 or not tinta_2 or render.bloco_legenda("Natal") != bloco_1
            or tinta_1[1] - tinta_2[1] != (banda_2 - bloco_1) // 2 or tinta_1[3] - tinta_2[3] != (banda_2 - bloco_1) // 2
            or so_ela[3] != render.A - render.LEGENDA_FUNDO + 1):
        problemas.append("uma linha numa banda de duas: tinta em %s contra %s na propria faixa, banda %d, bloco %d"
                         % (tinta_2, tinta_1, banda_2, bloco_1))
    # TROCAS MAIS APERTADAS DO QUE LEGENDA_TROCA: numa pilha de 8 em 2 s as fotos entram de
    # 0,186 em 0,186 s. Cada troca tem de estar completa quando a seguinte comeca, senao a
    # banda salta: no instante antes de uma troca o fotograma e o texto anterior inteiro, e a
    # meio dela e uma mistura.
    imagens8 = _fotos_lisas(8)
    with contextlib.redirect_stdout(io.StringIO()):
        apertada = render.preparar_monte("pilha", imagens8, None, "", 0.7, 0.7, "monte",
                                         textos=["T%d" % k for k in range(8)], opcoes={"modo": "legenda"},
                                         duracao=2.0)
        ref8 = render.preparar_monte("pilha", imagens8, None, "", 0.7, 0.7, "monte",
                                     textos=["T%d" % k for k in range(8)], opcoes={"modo": "legenda"})
    ref8["legenda"] = None
    tempos8 = render.tempos_legenda_grupo("pilha", 8, 2.0, 0.7, 0.7)
    intervalos = [b[0] - a[0] for a, b in zip(tempos8[1:], tempos8[2:])]
    if not intervalos or max(intervalos) >= render.LEGENDA_TROCA:
        problemas.append("a pilha de 8 em 2 s nao aperta as trocas: intervalos %s" % intervalos)
    def so_com_o_texto(t, texto):
        quadro = render.desenhar(ref8, t, 2.0)
        cor, mascara = apertada["legenda"]["faixas"][texto]
        quadro.paste(cor, (0, 0), mascara)
        return quadro

    for i in (2, 4, 6):
        t = tempos8[i][0] - 0.001
        pior = max(hi for _lo, hi in ImageChops.difference(render.desenhar(apertada, t, 2.0),
                                                            so_com_o_texto(t, "T%d" % (i - 1))).getextrema())
        if pior > 3:
            problemas.append("troca apertada da foto %d: no instante antes da troca a legenda difere ate %d do "
                             "texto anterior inteiro, a troca de antes ainda nao acabou" % (i + 1, pior))
        t = tempos8[i][0] + intervalos[0] / 2.0
        meio = render.desenhar(apertada, t, 2.0).tobytes()
        if meio in (so_com_o_texto(t, "T%d" % (i - 1)).tobytes(), so_com_o_texto(t, "T%d" % i).tobytes()):
            problemas.append("troca apertada da foto %d: sem mistura a meio" % (i + 1))
    # PELO PREPARAR, com a coluna: o mesmo que direto.
    pasta = tempfile.mkdtemp(prefix="teste_legenda_")
    caminhos = []
    for k, im in enumerate(imagens):
        caminhos.append(os.path.join(pasta, "cor%d.png" % k))
        im.save(caminhos[-1])
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        pela_coluna = render.preparar({"tipo": "colagem", "texto_ecra": "Amigos", "tratamento": "filas",
                                       "fonte_imagem": "", "ficheiro": "", "id": "", "transicao_s": "0.7",
                                       "duracao_s": "4.5", "_caminhos": caminhos,
                                       "textos_fotos": '["Natal", "", "2019"]',
                                       "textos_opcoes": '{"modo": "legenda"}'}, {})
        direto = render.preparar_monte("colagem", imagens, [None] * 3, "Amigos", 0.7, 0.7, "filas",
                                       ["Natal", "", "2019"], {"modo": "legenda"})
    if any(render.desenhar(pela_coluna, t, 4.5).tobytes() != render.desenhar(direto, t, 4.5).tobytes()
           for t in (0.0, 1.5, 2.9, 4.46)):
        problemas.append("pela coluna textos_opcoes diferente do direto")
    # O AVISO DOS CURTOS: numa colagem de 3 em 4,5 s o do meio fica menos de 1,5 s; em 12 s nenhum.
    curtos = [l for l in saida.getvalue().splitlines() if "fica so" in l]
    with contextlib.redirect_stdout(io.StringIO()) as longa:
        render.preparar_monte("colagem", imagens, [None] * 3, "Amigos", 0.7, 0.7, "filas",
                              ["Natal", "", "2019"], {"modo": "legenda"}, duracao=12.0)
    tempos = render.tempos_legenda_grupo("colagem", 3, 4.5, 0.7, 0.7)
    esperados = [k for k, t, d in render.legendas_curtas(["Natal", "Amigos", "2019"], tempos)]
    if not esperados or len(curtos) != len(esperados) or "fica so" in longa.getvalue():
        problemas.append("avisos dos curtos: %d avisos para %s curtos em 4,5 s (%s), e %d em 12 s"
                         % (len(curtos), esperados, tempos, longa.getvalue().count("fica so")))
    # E A FOTO QUE ENTRA DEPOIS DO FIM DO CLIP: no lado a lado as celulas entram aos 0,35 +
    # k x 0,45 s seja qual for a duracao, e num 4q de 1,5 s a quarta entra aos 1,7. O texto
    # dela nunca aparece, e o aviso dizia "fica so -0.2 s"; com 1,0 s a terceira, que entra
    # aos 1,25, dava 0,4 s de um texto que ninguem via. Conta-se so ate ao fim do clip, e o
    # aviso diz quanto depois do fim a foto entra.
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        render.preparar_lado("4q", _fotos_lisas(4), [], "", ["A", "B", "C", "D"], {"modo": "legenda"}, duracao=1.5)
    avisos_4q = saida.getvalue()
    curtas_1s = [(k, t, round(d, 2)) for k, t, d in
                 render.legendas_curtas(["A", "B", "C", "D"], render.tempos_legenda_grupo("lado", 4, 1.0))]
    if ("foto 4 do grupo nunca aparece" not in avisos_4q or "0.2 s depois de o clip acabar: D" not in avisos_4q
            or "foto 3 do grupo fica so 0.2 s" not in avisos_4q or "-" in avisos_4q
            or curtas_1s != [(0, "A", 0.8), (1, "B", 0.2), (2, "C", -0.25), (3, "D", -0.7)]):
        problemas.append("lado 4q curto de mais: avisos %r, curtas em 1 s %s" % (avisos_4q.strip(), curtas_1s))
    verifica("texto na legenda de baixo: o texto da foto certa, a trocar com cada foto",
             not problemas and comparados > 60 and misturas >= 12,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d fotogramas ao byte em 8 grupos, %d trocas medidas, letra %s" % (
                 comparados, misturas, alturas))


def teste_tamanho_do_texto_das_fotos():
    """O tamanho escolhido na Mesa muda a letra do texto das fotos na proporcao, e 36 com "fica" e a ronda anterior.

    O PEDIDO: "permite tambem que eu possa selecionar o tamanho que quero". Mede-se:
      - a altura das maiusculas no ecra com 36, 46 e 64, no lado a lado e na colagem, contra
        a da fonte nesse tamanho;
      - o minimo a que a letra desce e proporcional, minimo_texto_foto();
      - pela coluna textos_opcoes o mesmo que direto;
      - e com {"tamanho": 36, "tapadas": "fica"} os grupos de controlo dao os bytes do render
        da ronda anterior, ASSINATURAS_TEXTO_36: o tamanho novo e o desaparecer na pilha nao
        mexeram em mais nada.
    """
    import contextlib
    import io
    import tempfile
    import PIL
    from PIL import ImageChops
    import render
    problemas, medidas = [], []
    # o minimo proporcional, na conta e no que se desenha
    for tam in (28, 36, 46, 64, 90):
        minimo = render.no_ecra(render.minimo_texto_foto(tam))
        obtido = render.linhas_texto_foto(TEXTO_LONGO, 300, tam)
        if obtido[0] != minimo or not obtido[2] or len(obtido[1]) != 2:
            problemas.append("comprido em 300 px a %d: %s, o minimo e %d" % (tam, obtido, minimo))
        if render.linhas_texto_foto("Natal", 600, tam)[0] != render.no_ecra(tam):
            problemas.append("curto a %d nao fica a %d" % (tam, tam))
    # a letra no ecra: lado a lado 4q, celula 1, e colagem em filas de 4, a ultima foto
    imagens = [Image.new("RGB", (800, 600), CORES_MONTE[k]) for k in range(4)]
    sem_lado = render.desenhar(render.preparar_lado("4q", imagens, [], ""), 5.9, 6.0)
    sem_col = render.preparar_monte("colagem", imagens, None, "", estilo="filas")
    dur = 3 + 1.6 * 4
    for tam in (36, 46, 64):
        esperada = _altura_das_maiusculas(render, tam)
        com = render.preparar_lado("4q", imagens, [], "", ["NATAL"] * 4, {"tamanho": tam})
        x, y, w, h = com["celulas"][0]["rect"]
        caixa = _letra_branca(render.desenhar(com, 5.9, 6.0), sem_lado).crop((x, y, x + w, y + h)).getbbox()
        alt_lado = caixa[3] - caixa[1] if caixa else 0
        with contextlib.redirect_stdout(io.StringIO()):
            com = render.preparar_monte("colagem", imagens, None, "", estilo="filas", textos=["NATAL"] * 4,
                                        opcoes={"tamanho": tam})
        letra = _letra_branca(render.desenhar(com, dur - 0.04, dur), render.desenhar(sem_col, dur - 0.04, dur))
        poses, _z = render.poses_monte(com, dur - 0.04, dur)
        k, cx, cy, escala, _a, _p = poses[-1]
        f = com["fotos"][k]
        a = math.radians(f["angulo"])
        c, s = math.cos(a), math.sin(a)
        # so a ultima foto, que ninguem tapa, e em coordenadas dela, para a rotacao nao contar
        mascara = Image.new("L", (render.L, render.A), 0)
        render.ImageDraw.Draw(mascara).polygon(render.cantos(cx, cy, f["tamanho"][0] / 2.0 * escala - 4,
                                                              f["tamanho"][1] / 2.0 * escala - 4, f["angulo"]), fill=255)
        vs = [(px + 0.5 - cx) * s + (py + 0.5 - cy) * c for px, py in _pontos(ImageChops.multiply(letra, mascara))]
        alt_col = (max(vs) - min(vs) + 1) / escala if vs else 0
        medidas.append((tam, alt_lado, round(alt_col, 1), esperada))
        if abs(alt_lado - esperada) > 2 or abs(alt_col - esperada) > 2.5:
            problemas.append("a %d: maiusculas com %d px no lado a lado e %.1f na colagem, a fonte da %d"
                             % (tam, alt_lado, alt_col, esperada))
    if not medidas[0][1] < medidas[1][1] < medidas[2][1]:
        problemas.append("a letra nao cresce com o tamanho: %s" % (medidas,))
    # pela coluna
    pasta = tempfile.mkdtemp(prefix="teste_tamanho_")
    caminhos = []
    for k, im in enumerate(imagens):
        caminhos.append(os.path.join(pasta, "cor%d.png" % k))
        im.save(caminhos[-1])
    with contextlib.redirect_stdout(io.StringIO()):
        pela_coluna = render.preparar({"tipo": "lado", "texto_ecra": "", "tratamento": "4q", "fonte_imagem": "",
                                       "ficheiro": "", "id": "", "transicao_s": "0.7", "duracao_s": "6",
                                       "_caminhos": caminhos, "textos_fotos": '["NATAL", "", "2019", "Natal"]',
                                       "textos_opcoes": '{"tamanho": 64}'}, {})
        direto = render.preparar_lado("4q", imagens, [None] * 4, "", ["NATAL", "", "2019", "Natal"], {"tamanho": 64})
        omissao = render.preparar_lado("4q", imagens, [None] * 4, "", ["NATAL", "", "2019", "Natal"])
    q = render.desenhar(pela_coluna, 5.9, 6.0).tobytes()
    if q != render.desenhar(direto, 5.9, 6.0).tobytes() or q == render.desenhar(omissao, 5.9, 6.0).tobytes():
        problemas.append("pela coluna textos_opcoes o tamanho 64 nao chega, ou nao muda nada")
    # 36 com "fica" e a ronda anterior, ao byte
    pasta = tempfile.mkdtemp(prefix="teste_texto36_")
    agora = assinaturas_texto_36(render, pasta, '{"tamanho": 36, "tapadas": "fica"}')
    if sorted(agora) != sorted(ASSINATURAS_TEXTO_36):
        problemas.append("grupos de controlo diferentes dos das assinaturas: %s" % sorted(agora))
    else:
        diferentes = sorted(k for k in agora if agora[k] != ASSINATURAS_TEXTO_36[k])
        if diferentes:
            problemas.append("36 com fica diferente da ronda anterior em %s" % ", ".join(diferentes))
    verifica("texto nas fotos: o tamanho escolhido muda a letra, e 36 com fica e a ronda anterior",
             not problemas,
             "; ".join(problemas[:3]) if problemas else
             "maiusculas %s, %d grupos ao byte com a ronda anterior (Pillow %s)"
             % (["%d: %d e %.1f px, fonte %d" % m for m in medidas], len(ASSINATURAS_TEXTO_36), PIL.__version__))


def teste_pilha_texto_das_tapadas():
    """Na pilha, o texto de uma foto de baixo desaparece quando a seguinte cai por cima, salvo se o Tiago pedir que fique.

    O PEDIDO: sobre o texto das fotos de baixo da pilha, "melhor ainda e a opcao para ficar la
    e para desaparecer ser algo que eu escolho". No monte e no leque, com texto em todas:
      - antes de a seguinte comecar, "some" e "fica" dao o mesmo fotograma;
      - depois do desvanecer, "some" da BYTE A BYTE o fotograma da mesma pilha com os textos
        das fotos ja tapadas em branco, e "fica" ainda mostra a faixa e, onde a seguinte nao
        a tapa, a letra dessas fotos;
      - a meio do desvanecer o fotograma e a mistura dos dois, na proporcao, e nao e nenhum
        dos dois;
      - a ultima mantem o texto ate ao fim;
      - a camada guardada e o conjunto dao o mesmo que foto a foto, tambem num clip apertado
        em que a entrada e mais curta do que TEXTO_FOTO_SOME;
      - cada foto tapada tem um sprite sem texto feito uma vez, e a ultima nao.
    """
    import contextlib
    import io
    from PIL import ImageChops
    import render
    problemas, medidos, com_letra = [], 0, 0

    def diferenca(a, b):
        r, g, bb = ImageChops.difference(a, b).split()
        return ImageChops.lighter(ImageChops.lighter(r, g), bb).histogram()

    def como_o_conjunto(a, b):
        """A medida do teste_camada_do_conjunto_igual_as_fotos: media abaixo de 0,8 e menos de 0,2% acima de 40."""
        hist = diferenca(a, b)
        total = float(sum(hist))
        return sum(v * c for v, c in enumerate(hist)) / total < 0.8 and sum(hist[41:]) / total < 0.002

    textos = ["NATAL", "2019", "Verao", "Porto"]
    for estilo in ("monte", "leque"):
        n = 4
        imagens = _fotos_lisas(n)
        dur = 2.6 + 0.85 * n
        # As referencias sao pilhas com "fica" e os textos das primeiras k fotos em branco:
        # com "fica" nada desvanece, por isso o que la esta e exatamente o que "some" deve
        # mostrar depois de as k primeiras terem sido tapadas.
        with contextlib.redirect_stdout(io.StringIO()):
            some = render.preparar_monte("pilha", imagens, None, "", estilo=estilo, textos=textos)
            fica = render.preparar_monte("pilha", imagens, None, "", estilo=estilo, textos=textos,
                                         opcoes={"tapadas": "fica"})
            brancos = [render.preparar_monte("pilha", imagens, None, "", estilo=estilo,
                                             textos=[""] * k + textos[k:], opcoes={"tapadas": "fica"})
                       for k in range(n + 1)]
        if some["opcoes"]["tapadas"] != "some" or fica["opcoes"]["tapadas"] != "fica":
            problemas.append("%s: a omissao nao e some" % estilo)
        sprites = [f.get("sprite_sem") is not None for f in some["fotos"]]
        if sprites != [True, True, True, False] or any(f.get("sprite_sem") is not None for f in fica["fotos"]):
            problemas.append("%s: sprites sem texto %s com some, e com fica %s" % (
                estilo, sprites, [f.get("sprite_sem") is not None for f in fica["fotos"]]))
        inicios, entrada, _z = render.estado_monte(some, 0.0, dur)
        desvanece = min(render.TEXTO_FOTO_SOME, entrada)
        lugares = [[f["centro"][0], f["centro"][1], f["tamanho"][0], f["tamanho"][1], f["angulo"]]
                   for f in fica["fotos"]]
        for k in range(n - 1):
            # antes de a seguinte entrar, o texto de k ainda la esta: e a referencia com as
            # primeiras k em branco (a foto 1 com a "fica" inteira)
            t0 = inicios[k + 1] - 0.02
            if render.desenhar(some, t0, dur).tobytes() != render.desenhar(brancos[k], t0, dur).tobytes():
                problemas.append("%s: antes de a foto %d entrar, o texto da foto %d ja nao e o de fica"
                                 % (estilo, k + 2, k + 1))
            # O QUE A SEGUINTE TAPA DA LETRA E DA FAIXA de k, so ela, que e a unica que ja
            # entrou nestes instantes. As pilhas tapam-se de proposito: no monte a 2:3 cai em
            # cheio sobre o "Verao" centrado da 16:9 e nao sobra letra nenhuma, com "fica" ou
            # sem ela. A letra so se exige onde pelo menos metade dela fica a vista; a faixa,
            # que tem a largura da foto inteira, quase sempre espreita.
            w, h = fica["fotos"][k]["tamanho"]
            _capa, topo, alto, _c = render.colocar_faixa(textos[k], w, h, w)
            tam, _linhas, _c = render.linhas_texto_foto(textos[k], w)
            almofada = int(round(tam * render.TEXTO_FOTO_ALMOFADA))
            largura_letra = render.ImageFont.truetype(render.FONTE_TEXTO, tam).getbbox(textos[k])[2]
            seguinte = [render.contorno_monte(lugares[k + 1])]
            letra_tapada = render.parte_tapada(render.zona_da_faixa(
                lugares[k], topo + almofada, alto - 2 * almofada, largura_letra), seguinte)
            faixa_tapada = render.parte_tapada(render.zona_da_faixa(lugares[k], topo, alto, w), seguinte)
            for t in (inicios[k + 1] + desvanece + 0.02, inicios[k + 1] + entrada + 0.05):
                medidos += 1
                q_some = render.desenhar(some, t, dur)
                q_branco = render.desenhar(brancos[k + 1], t, dur)
                if q_some.tobytes() != q_branco.tobytes():
                    problemas.append("%s aos %.2f s: com some, o texto da foto %d nao desapareceu como devia"
                                     % (estilo, t, k + 1))
                q_fica = render.desenhar(brancos[k], t, dur)
                letra = _letra_branca(q_fica, q_branco).histogram()[255]
                if letra_tapada < 0.5:
                    com_letra += 1
                    if letra < 25:
                        problemas.append("%s aos %.2f s: com fica, a foto %d ficou sem letra a vista (%d px, "
                                         "com %d%% da letra tapada)" % (estilo, t, k + 1, letra, 100 * letra_tapada))
                elif letra > 0 and letra_tapada >= 0.999:
                    problemas.append("%s aos %.2f s: a foto %d tem a letra toda tapada e ve-se %d px dela"
                                     % (estilo, t, k + 1, letra))
                if faixa_tapada < 0.98 and _mudou(q_fica, q_branco).histogram()[255] < 200:
                    problemas.append("%s aos %.2f s: com fica, a faixa da foto %d desapareceu (%d%% tapada)"
                                     % (estilo, t, k + 1, 100 * faixa_tapada))
            # A MEIO DO DESVANECER: a mistura dos dois, na proporcao, e nenhum deles. A mistura
            # dos sprites em pre-multiplicado e a dos fotogramas so diferem nas bordas da letra e
            # da faixa: o BICUBIC do compor() passa dos 255 num degrau de branco sobre a faixa e
            # e cortado, e na mistura, com metade do degrau, nao e. Medido: ate 29 de 255 em
            # 0,04% dos pixeis. Sem desvanecer nenhum a diferenca era 90 na letra inteira.
            # E A UM QUARTO E A TRES QUARTOS, QUE E O QUE DIZ O SENTIDO: a meio a mistura e
            # simetrica, e um desvanecer ao contrario (o texto some logo e volta antes de
            # sumir de vez) passava. A um quarto o texto tem de estar a 75%, a tres quartos a
            # 25%; ao contrario da 143 de diferenca em 3,8% dos pixeis. A janela e mais larga
            # do que a meio porque a mistura assimetrica dos sprites difere mais nas bordas
            # (medido: ate 43 em 0,04% dos pixeis).
            for fracao, pior_max in ((0.25, 60), (0.5, 40), (0.75, 60)):
                t = inicios[k + 1] + fracao * desvanece
                meio = render.desenhar(some, t, dur)
                antes, depois = render.desenhar(brancos[k], t, dur), render.desenhar(brancos[k + 1], t, dur)
                alvo = Image.blend(depois, antes, 1.0 - fracao)
                hist = diferenca(meio, alvo)
                pior = max([v for v, c in enumerate(hist) if c] or [0])
                fora = sum(hist[4:]) / float(sum(hist))
                if pior > pior_max or fora > 0.005:
                    problemas.append("%s: a %.2f do desvanecer da foto %d o fotograma difere ate %d de 255 da "
                                     "mistura, em %.2f%% dos pixeis" % (estilo, fracao, k + 1, pior, 100 * fora))
                if meio.tobytes() in (antes.tobytes(), depois.tobytes()):
                    problemas.append("%s: a %.2f do desvanecer da foto %d o fotograma e uma das pontas, sem mistura"
                                     % (estilo, fracao, k + 1))
        fim = dur - 0.04
        if render.desenhar(some, fim, dur).tobytes() != render.desenhar(brancos[n - 1], fim, dur).tobytes():
            problemas.append("%s: no fim, some nao e a pilha so com o texto da ultima" % estilo)
        if _letra_branca(render.desenhar(some, fim, dur), render.desenhar(brancos[n], fim, dur)).histogram()[255] < 25:
            problemas.append("%s: no fim, a ultima ficou sem texto" % estilo)
        if render.desenhar(fica, fim, dur).tobytes() == render.desenhar(brancos[n - 1], fim, dur).tobytes():
            problemas.append("%s: no fim, fica perdeu os textos das de baixo" % estilo)
        # A CAMADA GUARDADA E O CONJUNTO CONTRA FOTO A FOTO: ao byte enquanto as fotos entram,
        # que ai a camada e feita com os mesmos compor(); depois de pousadas o conjunto e
        # escalado e mede-se como no teste_camada_do_conjunto_igual_as_fotos.
        for t in (inicios[1] + 0.05, inicios[2] + desvanece / 2.0, inicios[3] + entrada + 0.1, fim):
            a = render.desenhar_monte(some, t, dur)
            b = render.desenhar_monte(some, t, dur, por_foto=True)
            if t < inicios[-1] + entrada:
                certo = a.tobytes() == b.tobytes()
            else:
                certo = como_o_conjunto(a, b)
            if not certo:
                problemas.append("%s aos %.2f s: a camada guardada difere de foto a foto" % (estilo, t))
    # O CLIP APERTADO: oito fotos em 2 s, a entrada encolhe para 0,10 s, metade de
    # TEXTO_FOTO_SOME, e o texto tem de ter desaparecido quando a ultima pousa e o desenho
    # passa para o conjunto, onde as tapadas nao tem texto. Prende-se de duas maneiras:
    #   - alfa_texto_pilha() da zero no instante em que a ultima pousa: um desvanecer sempre
    #     de 0,2 s, em vez de encurtado a entrada, deixava o texto da penultima a 49% nesse
    #     instante, e ele saltava para zero de um fotograma para o seguinte;
    #   - logo depois de pousar, o conjunto contra foto a foto com a tolerancia APERTADA,
    #     maximo 40 e menos de 1% dos pixeis acima de 3, e nao a do teste_camada_do_conjunto.
    #     Era em 4 s, com a entrada a 0,16 s: o mesmo defeito deixava 19% do texto e a
    #     tolerancia larga (media abaixo de 0,8 e 0,2% acima de 40) engolia-o, medido maximo
    #     38 e nada acima de 40. Em 2 s da 124 em 2,5% dos pixeis, e o render certo 9 em 0,2%.
    #     A 0,2 s, ja a meio do recuo, o conjunto escalado mede-se como sempre.
    imagens = _fotos_lisas(8)
    dur8 = 2.0
    with contextlib.redirect_stdout(io.StringIO()):
        apertada = render.preparar_monte("pilha", imagens, None, "", 0.7, 0.7, "monte", textos=["NATAL"] * 8,
                                         duracao=dur8)
    inicios, entrada, _z = render.estado_monte(apertada, 0.0, dur8)
    if entrada > 0.6 * render.TEXTO_FOTO_SOME:
        problemas.append("clip apertado com entrada %.3f, nao aperta" % entrada)
    pousa = inicios[-1] + entrada
    alfa_ao_pousar = render.alfa_texto_pilha(pousa, inicios[-1], entrada)
    if alfa_ao_pousar > 1e-6:
        problemas.append("clip apertado: quando a ultima pousa o texto da penultima ainda esta a %d%%"
                         % int(round(100 * alfa_ao_pousar)))
    for t in (pousa - 0.01, pousa + 0.01, pousa + 0.2):
        a = render.desenhar_monte(apertada, t, dur8)
        b = render.desenhar_monte(apertada, t, dur8, por_foto=True)
        if t < pousa:
            certo = a.tobytes() == b.tobytes()
        elif t < pousa + 0.1:
            hist = diferenca(a, b)
            pior = max([v for v, c in enumerate(hist) if c] or [0])
            certo = pior <= 40 and sum(hist[4:]) / float(sum(hist)) < 0.01
        else:
            certo = como_o_conjunto(a, b)
        if not certo:
            problemas.append("clip apertado aos %.2f s: conjunto e foto a foto diferem" % t)
    # O AVISO DE "FICA" DIZ QUANTO DAS LETRAS FICA TAPADO, E NAO DA FAIXA. Num monte de 5 o
    # "2012" da 1.a foto tem 104 pixeis de letra numa faixa de 922, e a seguinte cai em cheio
    # no centro: as letras ficam 100% escondidas com a faixa a 52%, e o aviso dizia 52. Mede-se
    # aqui a zona das letras, a linha mais larga centrada e sem a almofada, contra os mesmos
    # contornos, e o numero do aviso tem de ser esse; e o caso da 1.a foto so vale se a faixa
    # inteira nao estiver tambem toda tapada.
    import re
    from PIL import ImageDraw
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        cinco = render.preparar_monte("pilha", _fotos_lisas(5), None, "", estilo="monte",
                                      textos=["2012", "", "Natal", "Verao de 2014", "2019"],
                                      opcoes={"tapadas": "fica"})
    lugares5 = [[f["centro"][0], f["centro"][1], f["tamanho"][0], f["tamanho"][1], f["angulo"]]
                for f in cinco["fotos"]]
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    esperados = {}
    for k, f in enumerate(cinco["fotos"]):
        if not f["texto"] or k + 1 >= len(lugares5):
            continue
        w, h = f["tamanho"]
        seguintes = [render.contorno_monte(lugares5[j]) for j in range(k + 1, len(lugares5))]
        _capa, topo, alto, _c = render.colocar_faixa(f["texto"], w, h, w)
        tam, linhas, _c = render.linhas_texto_foto(f["texto"], w)
        almofada = int(round(tam * render.TEXTO_FOTO_ALMOFADA))
        letras = max(d.textbbox((0, 0), l, font=render._fonte(tam))[2] for l in linhas)
        faixa_tapada = render.parte_tapada(render.zona_da_faixa(lugares5[k], topo, alto, w), seguintes)
        letras_tapadas = render.parte_tapada(render.zona_da_faixa(lugares5[k], topo + almofada, alto - 2 * almofada,
                                                                  letras), seguintes)
        esperados[k + 1] = (int(round(100 * letras_tapadas)), int(round(100 * faixa_tapada)))
    lidos = {int(foto): int(pct) for pct, foto in re.findall(r"AVISO: (\d+)% do texto da foto (\d+)", saida.getvalue())}
    devidos = {k: e[0] for k, e in esperados.items() if e[0] > 100 * render.TEXTO_FOTO_TAPADO}
    if lidos != devidos or devidos.get(1) != 100 or esperados[1][1] > 90:
        problemas.append("monte de 5 com fica: os avisos dizem %s e as letras tapadas sao %s (faixa %s)"
                         % (lidos, devidos, {k: e[1] for k, e in esperados.items()}))
    verifica("pilha: o texto das fotos de baixo desaparece, ou fica, como o Tiago escolher",
             not problemas and medidos >= 12 and com_letra >= 2,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "monte e leque, %d instantes ao byte, %d com letra a vista com fica, "
             "desvanecer medido, clip apertado" % (medidos, com_letra))


def teste_textos_opcoes_invalidas():
    """Uma coluna textos_opcoes mal escrita cai na omissao COM AVISO, e uma bem escrita chega toda.

    O PORQUE: a coluna e JSON escrito pelo montar_da_mesa.py, e um valor fora do que o render
    conhece que caisse em silencio na omissao era um texto a sair de outra maneira sem
    ninguem saber porque. Cada caso invalido tem de dar a omissao e um aviso; os validos
    nenhum aviso; e pelo preparar, uma coluna ilegivel da o fotograma da coluna vazia.
    """
    import contextlib
    import io
    import tempfile
    import render
    problemas = []
    omissao = {"modo": "foto", "tamanho": 46, "tapadas": "some"}
    if render.OPCOES_TEXTO != omissao:
        problemas.append("omissao %s" % (render.OPCOES_TEXTO,))
    invalidos = ["lixo", "[1, 2]", '{"modo": "x"}', '{"tapadas": "y"}', '{"tamanho": 20}', '{"tamanho": 100}',
                 '{"tamanho": 40.5}', '{"tamanho": "46"}', '{"tamanho": true}', '{"cor": "azul"}', "{", "42"]
    for valor in invalidos:
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            lido = render.ler_textos_opcoes(valor)
        if lido != omissao or saida.getvalue().count("AVISO") != 1:
            problemas.append("%r deu %s com %d avisos" % (valor, lido, saida.getvalue().count("AVISO")))
    validos = [(None, omissao), ("", omissao), ("{}", omissao),
               ('{"modo": "legenda"}', dict(omissao, modo="legenda")),
               ('{"tamanho": 56}', dict(omissao, tamanho=56)), ('{"tamanho": 28.0}', dict(omissao, tamanho=28)),
               ('{"tapadas": "fica"}', dict(omissao, tapadas="fica")),
               ('{"modo": "legenda", "tamanho": 90, "tapadas": "fica"}', {"modo": "legenda", "tamanho": 90, "tapadas": "fica"}),
               ({"tamanho": 36, "tapadas": "fica"}, dict(omissao, tamanho=36, tapadas="fica"))]
    for valor, esperado in validos:
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            lido = render.ler_textos_opcoes(valor)
        if lido != esperado or "AVISO" in saida.getvalue():
            problemas.append("%r deu %s (%s)" % (valor, lido, saida.getvalue().strip()))
    # uma chave a mais avisa e as outras entram
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        lido = render.ler_textos_opcoes('{"tamanho": 60, "cor": 1}')
    if lido != dict(omissao, tamanho=60) or saida.getvalue().count("AVISO") != 1:
        problemas.append("chave a mais: %s com %d avisos" % (lido, saida.getvalue().count("AVISO")))
    # pelo preparar: coluna ilegivel = coluna vazia, com aviso
    pasta = tempfile.mkdtemp(prefix="teste_opcoes_")
    imagens = _fotos_lisas(3)
    caminhos = []
    for k, im in enumerate(imagens):
        caminhos.append(os.path.join(pasta, "cor%d.png" % k))
        im.save(caminhos[-1])
    clip = {"tipo": "colagem", "texto_ecra": "", "tratamento": "filas", "fonte_imagem": "", "ficheiro": "",
            "id": "", "transicao_s": "0.7", "duracao_s": "6", "_caminhos": caminhos,
            "textos_fotos": '["Natal", "", "2019"]'}
    quadros = {}
    avisos = {}
    for rotulo, coluna in (("vazia", ""), ("lixo", "lixo"), ("chave", '{"modo": "grande"}')):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            p = render.preparar(dict(clip, textos_opcoes=coluna), {})
        quadros[rotulo] = render.desenhar(p, 5.9, 6.0).tobytes()
        avisos[rotulo] = "textos_opcoes" in saida.getvalue()
    if len(set(quadros.values())) != 1 or avisos != {"vazia": False, "lixo": True, "chave": True}:
        problemas.append("pelo preparar: fotogramas %s, avisos %s"
                         % ("iguais" if len(set(quadros.values())) == 1 else "diferentes", avisos))
    verifica("textos_opcoes: o invalido cai na omissao com aviso, o valido chega",
             not problemas, "; ".join(problemas[:3]) if problemas else
             "%d invalidos, %d validos, e pelo preparar" % (len(invalidos), len(validos)))


def teste_colagem_faixa_fora_do_que_as_seguintes_tapam():
    """Na colagem, toda a letra desenhada se ve: se a faixa em baixo fosse pisada, vai para o topo, e se o topo tambem, avisa.

    O DEFEITO HERDADO (H1): a foto que chega depois tapava a parte de BAIXO da faixa da
    anterior, numa colagem em filas de 5 a linha de baixo de "Natal de 2019 em casa" ficava
    ilegivel e ninguem avisava. A orla passou a contar em baixo, e isto prende-o de duas
    maneiras:
      - em muitas formas, com uma e duas linhas, com e sem legenda e com focos, nenhuma letra
        desenhada fica por baixo de uma foto seguinte, comparando cada foto composta sozinha
        na mesma pose com o fotograma inteiro;
      - com uma disposicao feita a mao em que a foto seguinte pisa o fundo da anterior, a
        faixa vai para o topo; com uma que pisa o fundo e o topo, fica em baixo e o preparar
        avisa, ver sitio_da_faixa_na_colagem();
      - e com pisadas PARCIAIS, um terco da banda das letras com o topo livre, que sobe sem
        aviso, e um quarto em baixo e em cima, que fica em baixo com o aviso a dizer a fracao
        medida: uma guarda que so subisse a faixa com mais de metade pisada passava em tudo
        o resto.
    """
    import contextlib
    import io
    from PIL import ImageChops
    import render
    problemas, medidas = [], 0
    ecra = (render.L, render.A)
    # O texto do exemplo do defeito, em duas linhas na maior parte das fotos. O de uma linha
    # ja e medido em teste_texto_nas_fotos_do_monte(). Cinco formas e nao mais, que cada
    # colagem espalhada leva segundos a assentar.
    texto = "Natal de 2019 em casa"
    formas = ([4 / 3.0] * 5, [4 / 3.0, 3 / 4.0, 4 / 3.0, 3 / 4.0, 4 / 3.0], [3 / 4.0] * 5,
              [16 / 9.0, 2 / 3.0, 2 / 3.0, 16 / 9.0, 3 / 4.0], [4 / 3.0] * 4)
    for estilo in ("filas", "espalhada"):
        for aspetos in formas:
            n = len(aspetos)
            for legenda, focos in (("", [None] * n), ("Amigos", [None] * n), ("", [(0.5, 0.95)] * n)):
                ims = [Image.new("RGB", (int(round(400 * a)), 400), CORES_MONTE[k]) for k, a in enumerate(aspetos)]
                dur = 3 + 1.6 * n
                with contextlib.redirect_stdout(io.StringIO()):
                    sem = render.preparar_monte("colagem", ims, focos, legenda, estilo=estilo)
                    com = render.preparar_monte("colagem", ims, focos, legenda, estilo=estilo, textos=[texto] * n)
                inicios, entrada, _ = render.estado_monte(sem, 0.0, dur)
                t = inicios[-1] + entrada
                visivel = _letra_branca(render.desenhar_monte(com, t, dur, por_foto=True),
                                        render.desenhar_monte(sem, t, dur, por_foto=True))
                poses, _zoom = render.poses_monte(com, t, dur)
                for k, x, y, tam, alfa, _p in poses:
                    so_com, so_sem = Image.new("RGB", ecra), Image.new("RGB", ecra)
                    render.compor(so_com, com["fotos"][k]["sprite"], x, y, tam / com["cresce"], alfa)
                    render.compor(so_sem, sem["fotos"][k]["sprite"], x, y, tam / sem["cresce"], alfa)
                    desenhada = _letra_branca(so_com, so_sem)
                    posta = desenhada.histogram()[255]
                    falta = ImageChops.subtract(desenhada, visivel).histogram()[255]
                    medidas += 1
                    if posta < 300 or falta > 0.005 * posta:
                        problemas.append("colagem %s de %d %s%s%s, foto %d: %d de %d pixeis de letra tapados"
                                         % (estilo, n, texto[:12], " com legenda" if legenda else "",
                                            " com focos" if focos[0] else "", k + 1, falta, posta))
    # A REGRA, com disposicoes feitas a mao. A foto 2 pisa o fundo da foto 1: a faixa da 1 vai
    # para o topo. A foto 2 pisa o meio da foto 1, fundo e topo: fica em baixo, e avisa.
    # E COM TRES FOTOS, EM QUE E A TERCEIRA QUE PISA E A SEGUNDA NAO TOCA NA PRIMEIRA: numa
    # colagem em filas de 5 quem pisa o fundo da foto 1 e a foto 4, nao a 2. Uma guarda que
    # so olhasse para a foto imediatamente a seguir passava nos casos de duas fotos e nas
    # colagens medidas, onde a orla descontada chega e ela nunca dispara.
    # E COM UMA PISADA PARCIAL, que e a que se le mal: nas colagens medidas e nos casos de
    # cima a banda das letras ou nao e pisada ou e-o toda, e uma guarda que so subisse a
    # faixa com mais de metade da banda pisada passava em tudo. A foto 2 no canto de baixo
    # esquerdo pisa um terco da banda das letras da 1 com o topo livre: a faixa sobe, sem
    # aviso. Uma foto alta e estreita a esquerda pisa um quarto da banda em baixo e o mesmo
    # em cima: fica em baixo, e o aviso diz a fracao que sitio_da_faixa_na_colagem() mediu.
    original = render.colagem_disposicao
    longe = [1500.0, 400.0, 600.0, 450.0, 0.0]
    primeira = [600.0, 400.0, 600.0, 450.0, 0.0]
    casos = (("pisa o fundo", [primeira, [600.0, 720.0, 600.0, 450.0, 0.0]], True, False),
             ("pisa o meio", [primeira, [600.0, 400.0, 400.0, 600.0, 0.0]], False, False),
             ("a terceira pisa o fundo", [primeira, longe, [600.0, 720.0, 600.0, 450.0, 0.0]], True, False),
             ("a terceira pisa o meio", [primeira, longe, [600.0, 400.0, 400.0, 600.0, 0.0]], False, False),
             ("pisa um terco do fundo", [primeira, [330.0, 720.0, 500.0, 375.0, 0.0]], True, True),
             ("pisa um quarto do fundo e do topo", [primeira, [445.0, 400.0, 220.0, 700.0, 0.0]], False, True))
    import re
    for rotulo, lugares, em_cima, parcial in casos:
        ims = [Image.new("RGB", (800, 600), CORES_MONTE[k]) for k in range(len(lugares))]
        render.colagem_disposicao = lambda aspetos, focos=None, livre_ate=None, lugares=lugares: [list(l) for l in lugares]
        try:
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                sem = render.preparar_monte("colagem", ims, None, "", estilo="filas")
                com = render.preparar_monte("colagem", ims, None, "", estilo="filas",
                                            textos=["NATAL"] + [""] * (len(lugares) - 1))
            sitio = render.sitio_da_faixa_na_colagem(lugares, 0, "NATAL", None, render.MONTE_PISA, render.MONTE_PISA)
        finally:
            render.colagem_disposicao = original
        dur = 3 + 1.6 * len(lugares)
        inicios, entrada, _ = render.estado_monte(sem, 0.0, dur)
        t = inicios[0] + entrada + 0.01     # so a primeira pousada, a segunda ainda nao entrou
        q_sem, q_com = render.desenhar(sem, t, dur), render.desenhar(com, t, dur)
        _letra, faixa = _letra_e_faixa(q_com, q_sem, _mudou(q_com, q_sem))
        caixa = faixa.getbbox()
        cx, cy, w, h, _ang = lugares[0]
        avisou = "pisada" in saida.getvalue()
        if parcial:
            # a banda das LETRAS em baixo, medida por fora, com a mesma zona do aviso da pilha:
            # entre 15 e 45% pisada, senao o caso nao e parcial e nao prende nada
            seguintes = [render.contorno_monte(l) for l in lugares[1:]]
            em_baixo = render.parte_tapada(render.zona_das_letras(lugares[0], "NATAL", None, render.MONTE_PISA,
                                                                  render.MONTE_PISA), seguintes)
            if not 0.15 <= em_baixo <= 0.45:
                problemas.append("%s: a banda das letras em baixo esta %d%% pisada, o caso nao e parcial"
                                 % (rotulo, int(round(100 * em_baixo))))
        if not caixa:
            problemas.append("%s: sem faixa na foto 1" % rotulo)
        elif em_cima:
            if sitio[0] is not True or abs(caixa[1] - (cy - h / 2.0)) > 4 or avisou:
                problemas.append("%s: a faixa devia ir para o topo (%d) e esta em %s, sitio %s, aviso %s"
                                 % (rotulo, cy - h / 2.0, caixa, sitio, avisou))
        else:
            # em baixo, levantada da orla que a seguinte pisa: o fundo da faixa a h x (1 - MONTE_PISA) do topo
            fundo = cy - h / 2.0 + h * (1 - render.MONTE_PISA)
            if sitio[0] is not False or sitio[1] <= render.TEXTO_FOTO_PISADA \
                    or abs(caixa[3] - fundo) > 4 or not avisou:
                problemas.append("%s: a faixa devia ficar em baixo (%d) com aviso e esta em %s, sitio %s, aviso %s"
                                 % (rotulo, fundo, caixa, sitio, avisou))
            # e o aviso diz a fracao medida, que numa pisada parcial e parcial
            ditos = [int(p) for p in re.findall(r"em baixo e em cima \((\d+)%\)", saida.getvalue())]
            if ditos != [int(round(100 * sitio[1]))] or (parcial and not 0.15 <= sitio[1] <= 0.5):
                problemas.append("%s: o aviso diz %s%% e a faixa esta pisada em %d%%"
                                 % (rotulo, ditos, int(round(100 * sitio[1]))))
    verifica("colagem: a letra das fotos fica fora do que as seguintes tapam, ou sobe, ou avisa",
             not problemas and medidas > 100,
             ("; ".join(problemas[:3]) + (" (+%d)" % (len(problemas) - 3) if len(problemas) > 3 else ""))
             if problemas else "%d fotos medidas em %d colagens, e a regra do topo com %d disposicoes a mao"
             % (medidas, len(formas) * 2 * 3, len(casos)))


# ---------------------------------------------------------------- render em fatias
COLUNAS_MONTAGEM_SINTETICA = ["ordem", "id", "tipo", "ficheiro", "duracao_s", "transicao_s", "inicio_s",
                              "fim_s", "movimento", "texto_ecra", "tratamento", "fonte_imagem",
                              "textos_fotos", "textos_opcoes", "in_s", "out_s"]
# md5 dos fotogramas do corpo sintetico de _montagem_sintetica(), a 480x270, desenhados pelo
# ciclo do render de ANTES das fatias (a copia de 16 de setembro, o ciclo do main copiado
# a letra). Se mudar, o caminho sequencial deixou de dar o que dava, com ou sem fatias.
# REFEITA A 17 DE SETEMBRO: as duas colagens e as duas pilhas do corpo passaram a dividir a
# duracao pelas fotos. Tirada do render de antes desta ronda com a agenda nova injetada e igual a
# do render novo; com a agenda de antes injetada, o render novo ainda da a de antes,
# e943a525dd7cc0f88879b2d32ae6db6e (scratchpad grupos/render/prova_b.py).
# REFEITA A 18 DE SETEMBRO: o corpo sintetico abre com um contador de anos, e o contador
# passou a ler-se a 15 metros (ponteiro, regua, legenda). Era 23e3a13e65370f97e52fed353812844e.
# Medido com as copias de antes desta ronda (scratchpad aproxima/prova/prova_sintetica.py):
# o render de antes com o linha_tempo de antes da a antiga; o render de antes com o
# linha_tempo de agora da exatamente esta, a mesma que o render de agora; e dos 560
# fotogramas mudam 50, os 50 em que o contador esta no ecra, e nenhum outro.
# REFEITA OUTRA VEZ A 18 DE SETEMBRO, na correcao: o risco vermelho do marco deixou de ser
# pintado a subir do preto por cima do ponteiro (abria-lhe um buraco escuro enquanto a
# legenda acende), e passou a misturar-se com o que la esta. Era 6d04f11e3c4b229ec5504fb89f69a292.
# Medido (scratchpad aproxima/corretor/prova_sintetica_corretor.py): o render e o linha_tempo
# do construtor dao a anterior; o render do construtor com o linha_tempo de agora da esta, a
# mesma do render de agora; mudam 5 fotogramas, do 1 ao 15, todos com o contador no ecra.
# REFEITA A 23 DE SETEMBRO, decisao 084, sistema A do letreiro: os meses da fita de 1995
# passaram de Arial fina 32 em minusculas na cor (128,114,122) para Arial Bold 38 em
# maiusculas na REGUA_TEXTO, que e o que a regua do contador ja usava. Era
# 911939f322ef8b47ed4eb4c4c8daa43d. Medido (scratchpad/prova_meses.py, que reconstroi o
# linha_tempo de antes e troca o modulo no render): o render de agora com o linha_tempo de
# ANTES da a antiga; com o de agora da esta; e dos 560 fotogramas mudam 47, do 53 ao 99,
# todos com o clip de marcos no ecra, e os outros 513 ficam byte a byte iguais.
ASSINATURA_CORPO_SINTETICO = "49cc671c82189f7ab0f0afba91a00ad4"


def _escrever_montagem(pasta, nome, clips):
    """Escreve uma montagem como o montar_da_mesa.py a escreve: inicio e fim contados dos encadeados."""
    t = 0.0
    linhas = []
    for k, c in enumerate(clips):
        linha = {col: "" for col in COLUNAS_MONTAGEM_SINTETICA}
        linha.update(c)
        linha["ordem"] = str(k + 1)
        dur, trans = float(c["duracao_s"]), float(c.get("transicao_s") or 0.0)
        if k:
            t -= trans
        linha["inicio_s"], linha["fim_s"] = "%.3f" % t, "%.3f" % (t + dur)
        t += dur
        linhas.append(linha)
    with open(os.path.join(pasta, nome + ".csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_MONTAGEM_SINTETICA)
        w.writeheader()
        w.writerows(linhas)
    return linhas


def _montagem_sintetica(pasta):
    """Treze clips de todos os tipos, com fotos de gradiente, para comparar fotogramas ao byte.

    Encadeados entre quase todos, cortes secos nas rajadas, colagens e pilhas que usam as
    camadas guardadas, textos nas fotos com e sem legenda de baixo, e uma foto de 3 s a
    fechar, para o fade do fim ter onde cair. Devolve (nome, caminhos por id).
    """
    formas = [4 / 3.0, 3 / 4.0, 16 / 9.0, 2 / 3.0, 1.0]
    caminhos = {}
    for k, a in enumerate(formas):
        c = os.path.join(pasta, "gradiente%d.png" % k)
        if not os.path.exists(c):
            _foto_gradiente(k, a).save(c)
        caminhos["g%d" % k] = c
    clips = [
        dict(tipo="contador", duracao_s="2.0", transicao_s="0",
             texto_ecra="2026>1995|4 de outubro de 2026"),
        dict(tipo="marcos", duracao_s="2.4", transicao_s="0.4",
             texto_ecra="1995@0-0.7|17/01 Terramoto em Kobe;*12/09 Nasce o Tiago;"
                        "24/11 Salvam-se as gravuras do Coa;*24/11 Nasce a Clara"),
        dict(tipo="cartao", duracao_s="1.2", transicao_s="0.4", texto_ecra="Era uma vez"),
        dict(tipo="foto", id="g0", ficheiro="g0.png", duracao_s="1.6", transicao_s="0.4",
             movimento="Zoom in", texto_ecra="Tiago", tratamento="fiel"),
        dict(tipo="foto", id="g1", ficheiro="g1.png", duracao_s="1.6", transicao_s="0.4",
             movimento="Afastada", texto_ecra="Clara", tratamento="fundo"),
        dict(tipo="foto", id="g2", ficheiro="g2.png", duracao_s="0.8", transicao_s="0",
             movimento="Nenhum", texto_ecra="", tratamento="rajada", fonte_imagem="0.5,0.9"),
        dict(tipo="foto", id="g3", ficheiro="g3.png", duracao_s="0.8", transicao_s="0",
             movimento="Nenhum", texto_ecra="", tratamento="rajada"),
        dict(tipo="lado", id="g1|g3", duracao_s="2.0", transicao_s="0.4", texto_ecra="Amigos",
             tratamento="2v", fonte_imagem="|0.5,0.9", textos_fotos='["Porto", "Gaia"]'),
        dict(tipo="colagem", id="g0|g1|g2|g3", duracao_s="2.8", transicao_s="0.4", texto_ecra="2015",
             tratamento="filas"),
        dict(tipo="colagem", id="g0|g1|g2", duracao_s="2.8", transicao_s="0.4", texto_ecra="",
             tratamento="espalhada", textos_fotos='["Natal", "", "2019"]',
             textos_opcoes='{"modo": "legenda"}'),
        dict(tipo="pilha", id="g0|g1|g2|g3|g4", duracao_s="2.8", transicao_s="0.4", texto_ecra="",
             tratamento="monte", textos_fotos='["Um", "Dois", "", "Quatro", ""]'),
        dict(tipo="pilha", id="g1|g2|g3", duracao_s="2.6", transicao_s="0.4", texto_ecra="Amigos",
             tratamento="leque", textos_fotos='["Um", "", "Tres"]',
             textos_opcoes='{"tapadas": "fica", "tamanho": 60}'),
        dict(tipo="foto", id="g4", ficheiro="g4.png", duracao_s="3.0", transicao_s="0.4",
             movimento="Parada", texto_ecra="Fim", tratamento="fundo"),
    ]
    _escrever_montagem(pasta, "sintetica", clips)
    return "sintetica", caminhos


def _estado_sintetico(render, pasta, nome, caminhos, ate=None):
    """O estado que o render carrega da montagem sintetica, com as fotos de gradiente no lugar das do inventario.

    Passa pelo carregar_montagem() verdadeiro, a mesma conta do desvio, do fim e dos
    fotogramas do pai e das fatias; so os caminhos, que o inventario nao conhece, sao
    postos a mao.
    """
    guardado = render.MONTAGENS
    render.MONTAGENS = pasta
    try:
        estado = render.carregar_montagem(nome, ate)
    finally:
        render.MONTAGENS = guardado
    for c in estado["resto"]:
        if c["tipo"] == "foto":
            c["_caminho"] = caminhos[c["id"]]
        elif c["tipo"] in ("lado", "colagem", "pilha"):
            c["_caminhos"] = [caminhos[i] for i in c["id"].split("|")]
    return estado


def _resolucao(render, larg, alt):
    guardado = (render.L, render.A)
    render.L, render.A = larg, alt
    return guardado


def teste_fatias_desenham_os_mesmos_fotogramas():
    """Os fotogramas das fatias sao, byte a byte, os do caminho sequencial, para 2 a 8 fatias.

    O PEDIDO DO TIAGO (16 de setembro): o render em paralelo so se a qualidade for A MESMA
    do render completo. A fatia k de n desenha os fotogramas q com q % n == k com o q
    global, a partir de um estado seu, com os seus prontos, e com uma historia diferente
    da do caminho sequencial: as camadas guardadas da colagem e da pilha, o fade do fim,
    os encadeados e a limpeza dos prontos tem de dar o mesmo, venha o fotograma de onde
    vier. E o caminho sequencial tem de continuar a dar o que o render de antes dava, ver
    ASSINATURA_CORPO_SINTETICO. A memoria de cada fatia fica limitada: os prontos sao
    limpos por bloco de fotogramas do corpo, e nao dos que a fatia desenha.
    """
    import contextlib
    import hashlib
    import io
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_fatias_")
    nome, caminhos = _montagem_sintetica(pasta)
    guardado = _resolucao(render, 480, 270)
    problemas = []
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            estado = _estado_sintetico(render, pasta, nome, caminhos)
            total = estado["total_quadros"]
            sequencial, maximo = {}, {"sequencial": 0, "fatias": 0}

            def recolher(destino, quadros, estado_x, qual):
                """O que a fatia escreveria no pipe, guardado por fotograma; e quantos prontos tinha."""
                fila = list(quadros)

                def escrever(bytes_):
                    destino[fila.pop(0)] = hashlib.md5(bytes_).hexdigest()
                    maximo[qual] = max(maximo[qual], len(estado_x["prontos"]))
                return escrever

            render.desenhar_fatia(range(total), estado, recolher(sequencial, range(total), estado, "sequencial"))
            tudo = hashlib.md5("".join(sequencial[q] for q in range(total)).encode()).hexdigest()
            if len(sequencial) != total or total < 400:
                problemas.append("sequencial: %d fotogramas de %d" % (len(sequencial), total))
            if tudo != ASSINATURA_CORPO_SINTETICO:
                problemas.append("o caminho sequencial mudou: assinatura %s" % tudo)
            ultimo = render.fotograma(total - 1, estado)[0]
            if max(ultimo.convert("L").getextrema()) > 10:
                problemas.append("o ultimo fotograma nao e preto: o fade do fim nao entrou")
            for n in range(2, 9):
                fatias = {}
                cobertos = []
                for k in range(n):
                    estado_k = _estado_sintetico(render, pasta, nome, caminhos)
                    quadros = render.quadros_da_fatia(k, n, total)
                    cobertos += list(quadros)
                    render.desenhar_fatia(quadros, estado_k, recolher(fatias, quadros, estado_k, "fatias"))
                    if (estado_k["desvio"], estado_k["fim"], estado_k["total_quadros"]) != (
                            estado["desvio"], estado["fim"], total):
                        problemas.append("%d fatias: a fatia %d conta outro filme" % (n, k))
                if sorted(cobertos) != list(range(total)):
                    problemas.append("%d fatias: nao cobrem os %d fotogramas uma vez cada" % (n, total))
                diferentes = [q for q in range(total) if fatias.get(q) != sequencial[q]]
                if diferentes:
                    problemas.append("%d fatias: %d fotogramas diferentes, o primeiro e o %d"
                                     % (n, len(diferentes), diferentes[0]))
            # Sem --ate ha fade; com --ate nao, e a conta do fim muda: as fatias recebem o mesmo --ate.
            parcial = _estado_sintetico(render, pasta, nome, caminhos, ate=12.0)
            if parcial["total_quadros"] >= total or parcial["ate"] != 12.0:
                problemas.append("--ate 12: %d fotogramas, ate %r" % (parcial["total_quadros"], parcial["ate"]))
            fim_parcial = render.fotograma(parcial["total_quadros"] - 1, parcial)[0]
            if max(fim_parcial.convert("L").getextrema()) <= 10:
                problemas.append("com --ate o ultimo fotograma saiu preto: o fade entrou num render parcial")
    finally:
        render.L, render.A = guardado
    # Uma fatia limpa no seu primeiro fotograma de cada bloco de 200 do corpo, que pode vir
    # um ou dois fotogramas depois do do caminho sequencial: no maximo um clip a mais.
    if maximo["sequencial"] >= len(estado["resto"]) - 3 or maximo["fatias"] > maximo["sequencial"] + 1:
        problemas.append("clips preparados ao mesmo tempo: %d no sequencial e %d numa fatia, de %d clips: "
                         "a limpeza nao e por bloco do corpo" % (maximo["sequencial"], maximo["fatias"],
                                                                  len(estado["resto"])))
    verifica("fatias: os mesmos fotogramas do caminho sequencial, de 2 a 8", not problemas,
             "; ".join(problemas[:3]) if problemas else
             "%d fotogramas, 13 clips de todos os tipos, ate %d clips preparados por fatia, %d no sequencial"
             % (total, maximo["fatias"], maximo["sequencial"]))


def teste_fatias_repartem_todos_os_fotogramas():
    """A reparticao cobre todos os fotogramas uma vez, de 1 a 8 fatias, mesmo com menos fotogramas do que fatias.

    Um fotograma repetido ou em falta nao dava erro nenhum: o encoder recebia os bytes
    que lhe chegassem. E o --fatias tem de ler o que o Tiago escreve: um numero, auto ou
    0 para os nucleos menos um ate 8, a omissao FATIAS_OMISSAO sem a opcao, e recusar
    o resto.
    """
    import render
    problemas = []
    for n in range(1, 9):
        for total in (0, 1, n - 1, n, n + 1, 17, 200, 401, 1001):
            if total < 0:
                continue
            fatias = [list(render.quadros_da_fatia(k, n, total)) for k in range(n)]
            juntos = sorted(q for f in fatias for q in f)
            if juntos != list(range(total)) or any(f != sorted(f) for f in fatias):
                problemas.append("%d fatias com %d fotogramas: %s" % (n, total, fatias if total < 20 else "..."))
            if total >= n and any(abs(len(f) - total / float(n)) >= 1.0 for f in fatias):
                problemas.append("%d fatias com %d fotogramas: repartidos por desigual %s"
                                 % (n, total, [len(f) for f in fatias]))
            if total < n and sum(1 for f in fatias if f) != total:
                problemas.append("%d fatias com %d fotogramas: %d com trabalho" % (n, total, sum(1 for f in fatias if f)))
    nucleos = max(1, min(8, (os.cpu_count() or 2) - 1))
    lidos = [render.fatias_pedidas(["r", "v3"]), render.fatias_pedidas(["r", "v3", "--fatias", "1"]),
             render.fatias_pedidas(["r", "v3", "--fatias", "7"]), render.fatias_pedidas(["r", "v3", "--fatias", "auto"]),
             render.fatias_pedidas(["r", "v3", "--fatias", "0"]), render.fatias_pedidas(["r", "--fatias", "AUTO"])]
    if lidos != [render.FATIAS_OMISSAO, 1, 7, nucleos, nucleos, nucleos] or render.FATIAS_OMISSAO != 7:
        problemas.append("--fatias lido como %s (omissao %d)" % (lidos, render.FATIAS_OMISSAO))
    # O auto numa maquina grande para nos 8, e numa de 2 nucleos, ou que nao os conte, fica em 1.
    contar = render.os.cpu_count
    automaticos = []
    try:
        for nucleos_da_maquina in (32, 9, 8, 2, 1, None):
            render.os.cpu_count = lambda n=nucleos_da_maquina: n
            automaticos.append(render.fatias_pedidas(["r", "v3", "--fatias", "auto"]))
    finally:
        render.os.cpu_count = contar
    if automaticos != [8, 8, 7, 1, 1, 1]:
        problemas.append("--fatias auto com 32, 9, 8, 2, 1 e ? nucleos: %s" % automaticos)
    recusados = []
    # "17" e a tampa (2 x FATIAS_MAXIMO) e "SEM VALOR" e --fatias em ultimo lugar, que
    # rebentava com IndexError em vez de uma mensagem.
    for valor in ("abc", "-1", "1.5", "", "17", "SEM VALOR"):
        try:
            render.fatias_pedidas(["r", "v3", "--fatias"] + ([] if valor == "SEM VALOR" else [valor]))
        except SystemExit:
            recusados.append(valor)
        except IndexError:
            problemas.append("--fatias sem valor rebenta com IndexError em vez de uma mensagem")
    if recusados != ["abc", "-1", "1.5", "", "17", "SEM VALOR"]:
        problemas.append("--fatias aceitou o que devia recusar: recusou so %s" % recusados)
    if render.fatias_pedidas(["r", "v3", "--fatias", "16"]) != 16:
        problemas.append("--fatias 16 devia ser aceite")
    if render.ler_fatia("2/7") != (2, 7) or render.ler_fatia("0/1") != (0, 1):
        problemas.append("--fatia k/n mal lido")
    for valor in ("7/7", "-1/3", "a/3", "3"):
        try:
            render.ler_fatia(valor)
            problemas.append("--fatia aceitou %r" % valor)
        except SystemExit:
            pass
    verifica("fatias: repartem todos os fotogramas uma vez, de 1 a 8", not problemas,
             "; ".join(problemas[:3]) if problemas else "8 x 9 casos, e as opcoes")


def teste_fatia_fala_so_pelo_stderr():
    """No stdout de uma fatia vao os bytes dos fotogramas e mais nada; as palavras vao para o stderr.

    O pai le do stdout da fatia L*A*3 bytes por fotograma, sem marcas: um aviso do
    preparar que la fosse parar, um "AVISO: textos_opcoes ..." por exemplo, desalinhava
    todos os fotogramas seguintes sem erro nenhum, e o encoder codificava lixo. Corre-se a
    fatia em processo, com um stdout e um stderr de mentira, sobre a montagem sintetica com
    uma opcao desconhecida que faz o preparar avisar: os bytes tem de ser exatamente os
    fotogramas dela, e o aviso e a linha FALTARAM tem de estar no stderr.
    """
    import hashlib
    import io
    import json
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_fatia_stderr_")
    nome, caminhos = _montagem_sintetica(pasta)
    guardado = _resolucao(render, 480, 270)
    stdout, stderr = sys.stdout, sys.stderr
    falso_out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    falso_err = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    problemas = []
    try:
        estado = _estado_sintetico(render, pasta, nome, caminhos)
        for c in estado["resto"]:
            if c["tipo"] == "lado":
                c["textos_opcoes"] = '{"lixo": 1}'
            if c["tipo"] == "colagem" and c["tratamento"] == "filas":
                c["_caminhos"][0] = os.path.join(pasta, "nao_existe.png")     # uma que falta
        total = estado["total_quadros"]
        k, n = 2, 5
        esperados = _estado_sintetico(render, pasta, nome, caminhos)
        for c in esperados["resto"]:
            if c["tipo"] == "lado":
                c["textos_opcoes"] = '{"lixo": 1}'
            if c["tipo"] == "colagem" and c["tratamento"] == "filas":
                c["_caminhos"][0] = os.path.join(pasta, "nao_existe.png")
        sys.stdout, sys.stderr = falso_out, falso_err
        try:
            canal = render.canal_da_fatia()
            print("isto e uma palavra a mais")       # o que um print perdido faria
            render.correr_fatia(estado, k, n, canal)
        finally:
            sys.stdout, sys.stderr = stdout, stderr
        falso_err.flush()
        bytes_ = falso_out.buffer.getvalue()
        texto = falso_err.buffer.getvalue().decode("utf-8", "replace")     # fotogramas no stderr nao sao utf-8
        tamanho = render.L * render.A * 3
        quadros = list(render.quadros_da_fatia(k, n, total))
        if len(bytes_) != tamanho * len(quadros):
            problemas.append("%d bytes no stdout, esperados %d x %d" % (len(bytes_), len(quadros), tamanho))
        else:
            with contextlib_silencio():
                diferentes = [q for i, q in enumerate(quadros)
                              if hashlib.md5(bytes_[i * tamanho:(i + 1) * tamanho]).hexdigest()
                              != hashlib.md5(render.fotograma(q, esperados)[0].tobytes()).hexdigest()]
            if diferentes:
                problemas.append("%d fotogramas diferentes no stdout, o primeiro e o %d" % (len(diferentes), diferentes[0]))
        linhas = texto.splitlines()
        if "isto e uma palavra a mais" not in linhas or "AVISO: textos_opcoes com a chave 'lixo' desconhecida" not in texto:
            problemas.append("o stderr nao tem as palavras: %r" % (linhas[:4],))
        faltaram = [l for l in linhas if l.startswith("FALTARAM: ")]
        if len(faltaram) != 1 or linhas[-1] != faltaram[0]:
            problemas.append("linha FALTARAM: %s" % (faltaram,))
        else:
            # O QUE VAI NA LISTA: o ficheiro, e quando o clip nao tem ficheiro (uma colagem,
            # um contador que nao se le) o tipo e o texto do ecra. Antes ia uma string
            # vazia: a lista do fim do render ficava com uma linha em branco e quem a lesse
            # nao sabia o que procurar.
            lidos = json.loads(faltaram[0][len("FALTARAM: "):])
            if len(lidos) != 1 or not lidos[0].startswith("colagem"):
                problemas.append("faltaram lidos %r" % (lidos,))
    finally:
        sys.stdout, sys.stderr = stdout, stderr
        render.L, render.A = guardado
    verifica("fatia: so fotogramas no stdout, as palavras no stderr", not problemas,
             "; ".join(problemas[:3]) if problemas else
             "%d fotogramas de %d, aviso e FALTARAM no stderr" % (len(quadros), total))


def contextlib_silencio():
    """Cala o stdout enquanto se preparam clips que avisam."""
    import contextlib
    import io
    return contextlib.redirect_stdout(io.StringIO())


def _correr_render(render, argv, montagens, saida):
    """Corre o render.main() em processo com as pastas trocadas: (texto, ficheiros mp4 na saida)."""
    import contextlib
    import io
    guardado = (render.MONTAGENS, render.SAIDA, render.RENDERS, render.L, render.A, sys.argv)
    render.MONTAGENS, render.SAIDA, render.RENDERS = montagens, saida, os.path.join(saida, "renders.csv")
    sys.argv = ["render.py"] + argv
    texto = io.StringIO()
    erro = None
    try:
        with contextlib.redirect_stdout(texto):
            render.main()
    except SystemExit as e:
        erro = str(e)
    finally:
        render.MONTAGENS, render.SAIDA, render.RENDERS, render.L, render.A, sys.argv = guardado
    ficheiros = sorted(f for f in os.listdir(saida) if f.lower().endswith(".mp4")) if os.path.isdir(saida) else []
    return texto.getvalue(), ficheiros, erro


def _montagem_real(pasta):
    """Cinco clips com fotos do inventario, que as fatias, noutros processos, conseguem abrir.

    Uma foto que nao existe, para os faltaram das fatias chegarem ao pai; uma opcao
    desconhecida, para um aviso do preparar ter de ir para o stderr da fatia e nao para
    o canal dos fotogramas; e uma colagem a fechar, cuja agenda conta com o encadeado de
    saida, que muda com o --ate.
    """
    inv = {r["id"] for r in csv.DictReader(open(os.path.join(REPO, "data", "inventario.csv"),
                                                encoding="utf-8-sig"))}
    tres = ["f0331", "f0334", "f0336"]
    if not all(i in inv for i in tres):
        return None
    clips = [
        dict(tipo="contador", duracao_s="1.6", transicao_s="0", texto_ecra="2026>1995|4 de outubro de 2026"),
        dict(tipo="foto", id="f0334", ficheiro="", duracao_s="1.6", transicao_s="0.5", movimento="Zoom in",
             texto_ecra="Amigos", tratamento="fundo"),
        dict(tipo="foto", id="f9999", ficheiro="nao_existe_fatias.jpg", duracao_s="1.0", transicao_s="0.5",
             movimento="Zoom in", texto_ecra="", tratamento="fiel"),
        dict(tipo="lado", id="f0334|f0336", duracao_s="2.0", transicao_s="0.5", texto_ecra="",
             tratamento="2v", textos_fotos='["Porto", "Gaia"]', textos_opcoes='{"lixo": 1}'),
        dict(tipo="colagem", id="f0331|f0334|f0336", duracao_s="2.8", transicao_s="0.5", texto_ecra="2015",
             tratamento="filas"),
    ]
    _escrever_montagem(pasta, "fatias_ensaio", clips)
    _escrever_montagem(pasta, "fatias_curta", [dict(tipo="cartao", duracao_s="0.2", transicao_s="0",
                                                    texto_ecra="Era uma vez")])
    return "fatias_ensaio"


def teste_fatias_pelo_main_dao_o_mesmo_ficheiro():
    """Pelo main, com as fatias em processos, o ficheiro sai igual ao byte ao de --fatias 1.

    Corre o render inteiro, com o encoder e os filhos verdadeiros, com --ate, --escala e
    --sem-som, uma vez com --fatias 1 e outra com --fatias 3, e compara os dois mp4 ao
    byte. Os faltaram de cada fatia chegam ao pai e o aviso do preparar sai uma vez, pela
    fatia 0. E com mais fatias do que fotogramas so ha fatias com fotogramas: 5 fotogramas
    com --fatias 8 dao o mesmo ficheiro que com --fatias 1.
    """
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_fatias_main_")
    nome = _montagem_real(pasta)
    if not nome:
        verifica("fatias pelo main: o mesmo ficheiro", False, "fotos do ensaio fora do inventario")
        return
    problemas = []
    saidas = {}
    for fatias in (1, 3):
        saida = os.path.join(pasta, "saida_%d" % fatias)
        texto, ficheiros, erro = _correr_render(
            render, [nome, "--ate", "8", "--escala", "0.25", "--sem-som", "--fatias", str(fatias)], pasta, saida)
        saidas[fatias] = texto
        if erro or len(ficheiros) != 1 or not ficheiros[0].endswith("_parcial.mp4"):
            problemas.append("--fatias %d: erro %r, ficheiros %s" % (fatias, erro, ficheiros))
            continue
        saidas[fatias] = (texto, open(os.path.join(saida, ficheiros[0]), "rb").read())
        if "imagens que nao consegui abrir: 1" not in texto or "nao_existe_fatias.jpg" not in texto:
            problemas.append("--fatias %d: a imagem em falta nao chegou ao fim: %s" % (fatias, texto[-300:]))
        if texto.count("AVISO: textos_opcoes com a chave 'lixo' desconhecida") != 1:
            problemas.append("--fatias %d: o aviso do preparar saiu %d vezes"
                             % (fatias, texto.count("AVISO: textos_opcoes com a chave")))
        if ("em 3 fatias" in texto) != (fatias == 3):
            problemas.append("--fatias %d: %s" % (fatias, "diz que foi em fatias" if fatias == 1 else "nao diz que foi em fatias"))
        if not os.path.exists(os.path.join(saida, "renders.csv")):
            problemas.append("--fatias %d: nao registou o render" % fatias)
    if not problemas:
        um, tres = saidas[1][1], saidas[3][1]
        if um != tres:
            problemas.append("os mp4 de --fatias 1 e --fatias 3 diferem: %d e %d bytes" % (len(um), len(tres)))
        elif len(um) < 10000:
            problemas.append("mp4 com %d bytes" % len(um))
    curtos = {}
    for fatias in (1, 8):
        saida = os.path.join(pasta, "curta_%d" % fatias)
        texto, ficheiros, erro = _correr_render(
            render, ["fatias_curta", "--escala", "0.25", "--sem-som", "--fatias", str(fatias)], pasta, saida)
        if erro or len(ficheiros) != 1:
            problemas.append("curta com --fatias %d: erro %r, ficheiros %s" % (fatias, erro, ficheiros))
            continue
        curtos[fatias] = open(os.path.join(saida, ficheiros[0]), "rb").read()
        if fatias == 8 and "em 5 fatias" not in texto:
            problemas.append("5 fotogramas com --fatias 8: %s" % texto.strip().splitlines()[-4:])
    if len(curtos) == 2 and curtos[1] != curtos[8]:
        problemas.append("a montagem de 5 fotogramas difere entre --fatias 1 e 8")
    verifica("fatias pelo main: o mesmo ficheiro ao byte que --fatias 1", not problemas,
             "; ".join(problemas[:3]) if problemas else
             "%d bytes iguais com 1 e 3 fatias; 5 fotogramas em 5 fatias" % len(saidas[1][1]))


def teste_fatia_que_morre_nao_deixa_ficheiro():
    """Uma fatia que morre a meio para o render com erro claro, e nao fica ficheiro nenhum.

    O pai le da fatia os bytes exatos de cada fotograma: uma que morra devolve menos, e
    sem esta guarda o encoder fechava o ficheiro com os fotogramas que tinha, e o render
    seguia para a fanfarra e o som como se nada fosse. As outras fatias, bloqueadas no
    pipe, tem de ser mortas, senao ficavam a espera para sempre.
    """
    import tempfile
    import time
    import render
    pasta = tempfile.mkdtemp(prefix="teste_fatia_morre_")
    nome = _montagem_real(pasta)
    if not nome:
        verifica("fatia que morre: erro e nenhum ficheiro", False, "fotos do ensaio fora do inventario")
        return
    # A fatia 1/3 e este script, que morre no quarto fotograma; as outras sao o render de sempre.
    stub = os.path.join(pasta, "fatia_que_morre.py")
    with open(stub, "w", encoding="utf-8") as fh:
        fh.write("import sys\nsys.path.insert(0, %r)\nimport render\n"
                 "if sys.argv[sys.argv.index('--fatia') + 1] == '1/3':\n"
                 "    original = render.fotograma\n"
                 "    def morre(q, estado):\n"
                 "        if q >= 4:\n"
                 "            raise RuntimeError('morri de proposito no fotograma %%d' %% q)\n"
                 "        return original(q, estado)\n"
                 "    render.fotograma = morre\n"
                 "render.main()\n" % os.path.join(REPO, "scripts"))
    guardado = render.SCRIPT
    render.SCRIPT = stub
    saida = os.path.join(pasta, "saida")
    t0 = time.time()
    try:
        texto, ficheiros, erro = _correr_render(
            render, [nome, "--ate", "8", "--escala", "0.25", "--sem-som", "--fatias", "3"], pasta, saida)
    finally:
        render.SCRIPT = guardado
    demorou = time.time() - t0
    restos = [f for f in os.listdir(saida)] if os.path.isdir(saida) else []
    problemas = []
    # O erro e o do pai, que diz qual a fatia, em que fotograma parou e quantos bytes devolveu,
    # e traz o que ela escreveu no stderr; "fotograma 4" sozinho ja vinha no traceback dela.
    if (not erro or "a fatia 1/3 parou no fotograma 4" not in erro or "devolveu 0 bytes em vez de" not in erro
            or "morri de proposito" not in erro):
        problemas.append("erro %r" % (erro,))
    if ficheiros or restos:
        problemas.append("ficou na saida: %s" % (restos,))
    if "Escrito:" in texto:
        problemas.append("o render seguiu ate ao fim")
    if demorou > 60:
        problemas.append("demorou %.0f s: as outras fatias nao foram mortas" % demorou)
    verifica("fatia que morre: erro claro e nenhum ficheiro", not problemas,
             "; ".join(problemas[:3]) if problemas else "erro no fotograma 4 em %.0f s, saida vazia" % demorou)


# --------------------------------------- um video no meio do corpo, 17 de setembro
# O Tiago, a 17 de setembro, para a intro nova: as fotos do pedido, a seguir o troco do
# Homer a dizer o seu "D'oh" ("aqui quero o video e o som"), e depois o filme como estava.
#
# O DEFEITO QUE ISTO GUARDA: ate aqui TODOS os clips de tipo video eram colados a frente
# do filme com o concat, fosse qual fosse o sitio deles na montagem. Um video posto a meio
# ia parar ao inicio e o corpo ficava com um BURACO onde ele estava: o ciclo dos
# fotogramas, sem nenhum clip ativo naquele instante, cai no ultimo clip do filme
# ("ativos = [resto[-1]]") e o que se via ali era a ultima foto parada. Sem erro nenhum.
#
# O VIDEO DE ENSAIO E FEITO COM O FFMPEG e nao e um ficheiro do disco: os do Tiago mudam de
# nome e de sitio, e um teste preso a eles falhava amanha sem nada estar partido. A
# luminancia de cada fotograma e o numero do fotograma vezes 3,2, o que faz dele um relogio
# que se le com UM pixel: da para dizer QUAL o fotograma que saiu, e nao so que saiu algum.


def _video_sintetico(pasta, nome, dura=3.0, tom=520):
    """Um video de `dura` segundos: imagem que conta os fotogramas e um tom para o som."""
    import subprocess
    import render
    caminho = os.path.join(pasta, nome)
    subprocess.run(
        [render.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=%.2f,"
                              "geq=lum='3.2*N':cb=128:cr=128" % dura,
         "-f", "lavfi", "-i", "sine=frequency=%d:duration=%.2f:sample_rate=48000" % (tom, dura),
         "-c:v", "libx264", "-crf", "10", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-shortest", caminho], capture_output=True)
    return caminho


def _relogio(imagem):
    """O pixel do centro, em luminancia. No video de ensaio isso diz que fotograma e este.

    O centro e nao a media: um video 4:3 entra no ecra 16:9 com barras pretas, e a media
    do quadro inteiro depende da largura das barras.
    """
    return imagem.convert("L").getpixel((imagem.width // 2, imagem.height // 2))


def _quadro_avulso(ff, caminho, quando, pasta, etiqueta):
    """Um fotograma do ficheiro, tirado a parte pelo ffmpeg: a leitura independente da cache."""
    import subprocess
    alvo = os.path.join(pasta, "avulso_%s.png" % etiqueta)
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.3f" % quando,
                    "-i", caminho, "-frames:v", "1", alvo], capture_output=True)
    return _relogio(Image.open(alvo))


def teste_video_no_meio_do_corpo():
    """Um video a meio da montagem e desenhado DENTRO do corpo, no fotograma certo, e a fanfarra fica na mesma.

    O que isto guarda, ponto a ponto, porque cada um falha calado:
      - a fanfarra passa a ser so o BLOCO INICIAL, e o video do meio fica no corpo, com o
        seu lugar no relogio: com a divisao antiga nao havia clip nenhum ativo ali;
      - o fotograma que sai e o do instante, conferido contra o mesmo instante do ficheiro
        tirado a parte pelo ffmpeg, e uma casa ao lado ja se ve;
      - a cache dos fotogramas e do processo principal: uma fatia que nao a encontre para
        com uma mensagem que diz isso, e NUNCA a cria (sete a extrair o mesmo video ao
        mesmo tempo era o que acontecia se ela a criasse);
      - pelo main, a cache e apagada no fim, o --guardar-quadros deixa-a la, e os
        fotogramas do video estao mesmo no filme, depois da fanfarra intacta.
    """
    import shutil
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_video_meio_")
    problemas = []
    ff = render.ffmpeg()
    filme = _video_sintetico(pasta, "meio_ensaio.mp4")
    VIN, TROCO = 0.6, 2.0
    guardadas_v, guardadas_m = dict(render.VIDEOS), render.MONTAGENS
    render.VIDEOS["fanfarra_ensaio.mp4"] = (filme, 0.0)
    render.VIDEOS["meio_ensaio.mp4"] = (filme, 0.0)
    guardado = _resolucao(render, 480, 270)
    pastas, quadros, t0 = [], [], 0.0
    try:
        caminhos = {}
        for k, a in ((0, 4 / 3.0), (1, 3 / 4.0)):
            c = os.path.join(pasta, "g%d.png" % k)
            _foto_gradiente(k, a).save(c)
            caminhos["g%d" % k] = c
        clips = [
            dict(tipo="video", ficheiro="fanfarra_ensaio.mp4", duracao_s="3.0", transicao_s="0"),
            dict(tipo="cartao", duracao_s="1.2", transicao_s="0.4", texto_ecra="Era uma vez"),
            dict(tipo="foto", id="g0", ficheiro="g0.png", duracao_s="1.6", transicao_s="0.4",
                 movimento="Zoom in", tratamento="fiel"),
            dict(tipo="video", ficheiro="meio_ensaio.mp4", duracao_s="%.2f" % TROCO,
                 transicao_s="0.4", in_s="%.2f" % VIN, out_s="%.2f" % (VIN + TROCO)),
            dict(tipo="foto", id="g1", ficheiro="g1.png", duracao_s="2.0", transicao_s="0.4",
                 movimento="Parada", tratamento="fundo"),
        ]
        _escrever_montagem(pasta, "video_meio", clips)
        render.MONTAGENS = pasta
        estado = render.carregar_montagem("video_meio", None)
        for c in estado["resto"]:
            if c["tipo"] == "foto":
                c["_caminho"] = caminhos[c["id"]]

        # 1. A FANFARRA E SO O BLOCO INICIAL, e o video do meio esta no corpo.
        if [c["ficheiro"] for c in estado["fanfarra"]] != ["fanfarra_ensaio.mp4"]:
            problemas.append("fanfarra: %s" % [c["ficheiro"] for c in estado["fanfarra"]])
        meios = [c for c in estado["resto"] if c["tipo"] == "video"]
        if len(meios) != 1:
            verifica("video no meio do corpo, no fotograma certo", False,
                     "%d videos no corpo, esperava 1" % len(meios))
            return
        meio = meios[0]
        t0 = float(meio["inicio_s"]) - estado["desvio"]
        if meio.get("_quadros") != render.pasta_dos_quadros("video_meio", meio["ordem"]):
            problemas.append("a pasta dos fotogramas do clip: %r" % meio.get("_quadros"))

        # 2. A CACHE E DO PROCESSO PRINCIPAL, e sai com um fotograma por 1/25 s de troco.
        with contextlib_silencio():
            pastas = render.preparar_quadros_dos_videos(ff, estado)
        quadros = render.quadros_da_cache(pastas[0] if pastas else "")
        if len(pastas) != 1 or abs(len(quadros) - TROCO * render.FPS) > 1:
            problemas.append("cache: %d pastas, %d fotogramas para %.1f s"
                             % (len(pastas), len(quadros), TROCO))

        # 3. O FOTOGRAMA DO INSTANTE, conferido contra o ficheiro lido a parte.
        pronto = render.preparar(meio, {})
        for t_rel in (0.0, 0.36, 1.0, 1.92):
            desenhado = _relogio(render.desenhar(pronto, t_rel, TROCO))
            avulso = _quadro_avulso(ff, filme, VIN + t_rel, pasta, "%.2f" % t_rel)
            seguinte = _quadro_avulso(ff, filme, VIN + t_rel + 1.0 / render.FPS, pasta,
                                      "s%.2f" % t_rel)
            if abs(seguinte - avulso) < 2:
                problemas.append("o video de ensaio nao distingue dois fotogramas seguidos")
            elif abs(desenhado - avulso) > 4:
                problemas.append("aos %.2f s do troco saiu o fotograma que le %d e o do "
                                 "ficheiro no mesmo instante le %d" % (t_rel, desenhado, avulso))
        if render.desenhar(pronto, 0.0, TROCO).size != (render.L, render.A):
            problemas.append("o fotograma do video nao sai do tamanho do ecra")
        # Uma casa ao lado: a mutacao que nao da erro nenhum, so um video fora de sitio.
        ao_lado = dict(pronto, quadros=pronto["quadros"][1:])
        if _relogio(render.desenhar(ao_lado, 1.0, TROCO)) == _relogio(render.desenhar(pronto, 1.0, TROCO)):
            problemas.append("com os fotogramas deslocados uma casa sai o mesmo: "
                             "a leitura nao prova nada")

        # 4. UMA FATIA SEM A CACHE PARA COM UMA MENSAGEM CLARA, e nao a cria.
        nao_existe = os.path.join(pasta, "cache_que_nao_existe")
        erro = ""
        try:
            render.preparar(dict(meio, _quadros=nao_existe), {})
        except SystemExit as e:
            erro = str(e)
        if "cache" not in erro or "processo principal" not in erro:
            problemas.append("uma fatia sem a cache diz: %r" % erro[:110])
        if os.path.exists(nao_existe):
            problemas.append("o preparar criou a cache: uma fatia nunca a pode criar")
        # Pasta vazia e outra coisa: o principal tentou e nao conseguiu, e ja avisou. Ai
        # vale a regra da marca sem imagem, um ficheiro em falta nao para um render de
        # quinze minutos a meio, e o clip sai como sai uma foto que nao abre.
        vazia = os.path.join(pasta, "cache_vazia")
        os.makedirs(vazia, exist_ok=True)
        if render.preparar(dict(meio, _quadros=vazia), {}) is not None:
            problemas.append("uma cache vazia devia dar o mesmo que uma foto que nao abre")

        # 5. MUTACAO: a divisao antiga, em que todo o video era fanfarra. O video saia do
        # corpo e no instante dele nao ficava clip nenhum ativo.
        certa = render.partir_em_fanfarra_e_corpo
        try:
            render.partir_em_fanfarra_e_corpo = lambda cs: (
                [c for c in cs if c["tipo"] == "video"], [c for c in cs if c["tipo"] != "video"])
            antigo = render.carregar_montagem("video_meio", None)
        finally:
            render.partir_em_fanfarra_e_corpo = certa
        meio_do_troco = estado["desvio"] + t0 + TROCO / 2.0
        if [c for c in antigo["resto"]
                if float(c["inicio_s"]) - 0.001 <= meio_do_troco < float(c["fim_s"])]:
            problemas.append("com a divisao antiga ainda havia clip ativo no meio do video: "
                             "a mutacao nao mudou nada")
        _quadro, ativos = render.fotograma(int(round((t0 + TROCO / 2.0) * render.FPS)), estado)
        if not any(c["tipo"] == "video" for c in ativos):
            problemas.append("no meio do troco o clip ativo e %s" % [c["tipo"] for c in ativos])

        # 6. PELO MAIN: a cache apaga-se, o --guardar-quadros deixa-a, e os fotogramas do
        # video estao no filme, a seguir a fanfarra.
        render.L, render.A = guardado
        cache = render.pasta_dos_quadros("video_meio", meio["ordem"])
        filmes = {}
        for opcoes, etiqueta in (([], "limpa"), (["--guardar-quadros"], "guardada")):
            saida = os.path.join(pasta, "saida_%s" % etiqueta)
            texto, ficheiros, falhou = _correr_render(
                render, ["video_meio", "--escala", "0.25", "--sem-som", "--fatias", "3"] + opcoes,
                pasta, saida)
            # Com fanfarra o filme e feito por concat e as pecas ficam ao lado, com "_" a
            # frente; o filme e o unico que nao tem.
            finais = [f for f in ficheiros if not f.startswith("_")]
            if falhou or len(finais) != 1:
                problemas.append("%s: erro %r, ficheiros %s" % (etiqueta, falhou, ficheiros))
                continue
            filmes[etiqueta] = os.path.join(saida, finais[0])
            if "+ 1 fanfarra" not in texto:
                problemas.append("%s: a fanfarra deixou de ser 1" % etiqueta)
            if os.path.isdir(cache) != (etiqueta == "guardada"):
                problemas.append("%s: a cache %s" % (etiqueta,
                                                     "ficou" if os.path.isdir(cache) else "sumiu"))
        if "limpa" in filmes:
            # O filme e a fanfarra (3 s) e o corpo a seguir, com corte seco: o troco do
            # video comeca aos 3 + t0 do filme. Fora dos encadeados dos dois lados.
            for quando, esperado, o_que in (
                    (1.0, _quadro_avulso(ff, filme, 1.0, pasta, "fan"), "a fanfarra"),
                    (3.0 + t0 + 1.0, _quadro_avulso(ff, filme, VIN + 1.0, pasta, "corpo"),
                     "o video do meio")):
                lido = _quadro_avulso(ff, filmes["limpa"], quando, pasta, "f%.2f" % quando)
                if abs(lido - esperado) > 8:
                    problemas.append("%s: aos %.2f s o filme le %d e devia ler %d"
                                     % (o_que, quando, lido, esperado))
    finally:
        render.L, render.A = guardado
        render.MONTAGENS = guardadas_m
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        render.apagar_quadros(pastas + [render.pasta_dos_quadros("video_meio", o)
                                        for o in ("1", "2", "3", "4", "5")])
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("video no meio do corpo, no fotograma certo", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "troco de 2,0 s aos %.1f s do corpo, cache de %d fotogramas, fanfarra intacta"
             % (t0, len(quadros)))


def teste_som_do_video_no_meio():
    """O som de um video do corpo entra no som.csv, com o in_s certo, e a musica baixa por baixo dele.

    O Tiago: "Aqui quero o video e o som". A fanfarra leva o som colado a imagem pelo
    concat; um video do meio do filme nao passa por ai, e sem esta faixa saia mudo, sem
    aviso nenhum, que e exatamente o que ja tinha acontecido as quatro demos.

    E O QUE NAO PODE ACONTECER: o som do video ser tratado como leito. Uma musica marcada
    no clip seguinte corta o leito que estiver a tocar, e cortar ali o "D'oh" a meio era
    o mesmo defeito das vozes do pedido. Nem ser ele proprio marcado para baixar por baixo
    de si. E um troco que nao cabe no ficheiro tem de ser cortado com aviso, e nao ficar a
    pedir fotogramas que nao existem.
    """
    import shutil
    import tempfile
    import montar_da_mesa
    import render
    pasta = tempfile.mkdtemp(prefix="teste_som_video_")
    problemas = []
    filme = _video_sintetico(pasta, "homer_ensaio.mp4")       # 3,00 s
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_ensaio.mp4"] = (filme, 0.0)
    render.VIDEOS["homer_ensaio.mp4"] = (filme, 0.0)
    montar_da_mesa._DURACOES.clear()
    VIN, TROCO = 0.6, 2.0
    t0 = 0.0
    try:
        base = [
            {"t": "video", "f": "fanfarra_ensaio.mp4", "d": 3.0, "c": 0},
            {"t": "contador", "x": "04/10/2026>25/12/2025|hoje", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "homer_ensaio.mp4", "vin": VIN, "d": TROCO, "c": 0.7},
            {"t": "foto", "i": "f0348", "d": 6, "c": 0.7, "r": "fiel"},
            {"t": "contador", "x": "2025>1995|x", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        linhas, som, saida = _monta_em_pasta([dict(c) for c in base])
        feito = ULTIMA_PASTA_MONTAGEM[0]
        # 1. O TROCO NO CSV, e so no video do meio: a fanfarra entra do zero e inteira.
        if linhas[0]["in_s"] or linhas[0]["out_s"]:
            problemas.append("a fanfarra ficou com troco: %s %s"
                             % (linhas[0]["in_s"], linhas[0]["out_s"]))
        if (round(float(linhas[3]["in_s"]), 2),
                round(float(linhas[3]["out_s"]), 2)) != (VIN, VIN + TROCO):
            problemas.append("troco do video do meio: %s a %s"
                             % (linhas[3]["in_s"], linhas[3]["out_s"]))
        # 2. A FAIXA DE SOM, uma so, a do video do meio, com o in_s do troco.
        sons = [r for r in som if r["ficheiro"] == "homer_ensaio.mp4"]
        if any(r["ficheiro"] == "fanfarra_ensaio.mp4" for r in som):
            problemas.append("a fanfarra levou faixa de som: tocava duas vezes")
        desvio = float(linhas[1]["inicio_s"])
        t0 = float(linhas[3]["inicio_s"]) - desvio
        if len(sons) != 1:
            problemas.append("%d faixas do video, esperava 1" % len(sons))
        else:
            s = sons[0]
            if (round(float(s["quando_s"]), 2), round(float(s["in_s"]), 2),
                    round(float(s["dura_s"]), 2),
                    float(s["ganho"])) != (round(t0, 2), VIN, TROCO, 1.0):
                problemas.append("faixa do video: %s"
                                 % ((s["quando_s"], s["in_s"], s["dura_s"], s["ganho"]),))
            if not s["nota"].startswith("som do video") or (s.get("video") or "").strip() != "1":
                problemas.append("faixa do video sem marca: %r %r" % (s["nota"], s.get("video")))
            if render.ler_abafar(s.get("abafar")):
                problemas.append("o som do video ficou marcado para baixar por baixo dele proprio")
        # 3. O LEITO BAIXA POR BAIXO DELE, e nao e cortado.
        abertura = [r for r in som if r["nota"].startswith("do pedido")]
        if not abertura:
            problemas.append("sem a musica da abertura")
        else:
            janelas = render.ler_abafar(abertura[0].get("abafar"))
            alvo = 10 ** (montar_da_mesa.VOZ_ABAIXA_DB / 20.0)
            if (len(janelas) != 1 or abs(janelas[0][0] - t0) > 0.02
                    or abs(janelas[0][1] - (t0 + TROCO)) > 0.02
                    or abs(janelas[0][2] - alvo) > 0.001):
                problemas.append("janela do leito por baixo do video: %s" % (janelas,))
        # "parada" poe o leito a zero, como nas vozes.
        parada = [dict(c) for c in base]
        parada[3] = dict(parada[3], vzm="parada")
        _l2, som2, _s2 = _monta_em_pasta(parada, nome="t2")
        j2 = render.ler_abafar(next(r for r in som2
                                    if r["nota"].startswith("do pedido")).get("abafar"))
        if not j2 or j2[0][2] != 0.0:
            problemas.append("com «parada» o leito ficou em %s" % (j2,))
        # 4. UMA MUSICA MARCADA NO CLIP SEGUINTE NAO CORTA O SOM DO VIDEO.
        marcada = [dict(c) for c in base]
        marcada[4] = dict(marcada[4], m={"f": "Tiago Celebration Song (Reggae)", "in": 0})
        _l3, som3, _s3 = _monta_em_pasta(marcada, nome="t3")
        cortado = [round(float(r["dura_s"]), 2) for r in som3
                   if r["ficheiro"] == "homer_ensaio.mp4"]
        if cortado != [TROCO]:
            problemas.append("a musica marcada mexeu no som do video: %s" % (cortado,))
        # 5. UM TROCO QUE NAO CABE NO FICHEIRO e cortado, com aviso.
        fora = [dict(c) for c in base]
        fora[3] = dict(fora[3], vin=2.0, d=2.0)         # 2,0 + 2,0 num ficheiro de 3,00 s
        l4, _som4, saida4 = _monta_em_pasta(fora, nome="t4")
        if "o troco pedido" not in saida4 or "corto em" not in saida4:
            problemas.append("um troco que nao cabe passou sem aviso")
        if abs(float(l4[3]["duracao_s"]) - 1.0) > 0.06:
            problemas.append("o troco que nao cabia ficou com %s s" % l4[3]["duracao_s"])
        # 5b. O VIN DEPOIS DO FIM DO FICHEIRO da UM aviso, e o aviso diz onde esta o erro.
        #
        # O DEFEITO: o main passa por aqui mais do que uma vez. A primeira cortava a
        # duracao para zero e a segunda lia esse zero como "ele nao escreveu duracao
        # nenhuma", por isso ele apanhava dois avisos seguidos que se contradiziam, e o
        # segundo dizia-lhe que o video entra "do segundo 18.5 ao fim, 0.0 s", que e falso.
        depois = [dict(c) for c in base]
        depois[3] = dict(depois[3], vin=4.0, d=2.0)     # comeca depois do fim dos 3,00 s
        l6, _som6, saida6 = _monta_em_pasta(depois, nome="t6")
        if "sem duracao escrita" in saida6:
            problemas.append("o vin para la do fim foi lido como duracao por escrever")
        if "o ficheiro so tem" not in saida6 or "Começa no segundo" not in saida6:
            problemas.append("o vin para la do fim nao diz onde esta o erro: %r"
                             % saida6[-300:])
        if float(l6[3]["duracao_s"]) > 0.001:
            problemas.append("o clip do vin impossivel ficou com %s s" % l6[3]["duracao_s"])
        # 6. SEM VIDEO NO CORPO nao ha colunas de troco nenhumas, nem faixa nova.
        sem = [dict(c) for c in base if c.get("f") != "homer_ensaio.mp4"]
        _l5, som5, _s5 = _monta_em_pasta(sem, nome="t5")
        cabecalho = open(os.path.join(ULTIMA_PASTA_MONTAGEM[0], "t5.csv"),
                         encoding="utf-8-sig").readline().strip().split(",")
        if "in_s" in cabecalho or "out_s" in cabecalho:
            problemas.append("uma montagem sem troco ganhou colunas: %s" % cabecalho)
        if any("video" in r for r in som5):
            problemas.append("coluna video num som sem videos no corpo")
        # 7. O RENDER LE A COLUNA, e nao estica o som do video com o cruzamento.
        guardadas = render.MONTAGENS
        render.MONTAGENS = feito
        try:
            lidas = render.som_do_ficheiro("t", 60.0)
        finally:
            render.MONTAGENS = guardadas
        do_video = [e for e in lidas if e["ficheiro"] == "homer_ensaio.mp4"]
        if len(do_video) != 1 or not render.entra_depressa(do_video[0]) \
                or do_video[0]["cruza"] != 0.0:
            problemas.append("o som do video no render: %s"
                             % [(e["ficheiro"], e.get("video"), e["cruza"]) for e in do_video])
        # 8. A MESA EXPLICA-O EM PORTUGUES, e nao mostra ao Tiago a nota tecnica.
        import som_para_mesa
        guardadas_s = som_para_mesa.MONTAGENS
        som_para_mesa.MONTAGENS = feito
        try:
            mesa = som_para_mesa.som_para_mesa("t", "t")
        finally:
            som_para_mesa.MONTAGENS = guardadas_s
        do_video_mesa = [f for f in mesa["faixas"] if f["f"] == "homer_ensaio.mp4"]
        leito_mesa = [f for f in mesa["faixas"] if f["abafa"]]
        if not do_video_mesa or do_video_mesa[0]["explica"] == do_video_mesa[0]["nota"]:
            problemas.append("a Mesa mostra a nota tecnica do som do video: %s"
                             % [(f["nota"], f["explica"]) for f in do_video_mesa])
        if not leito_mesa or "vídeo" not in leito_mesa[0]["explica"]:
            problemas.append("a Mesa diz que o leito baixa por baixo de quem? %s"
                             % [f["explica"] for f in leito_mesa])
        # O instante no filme conta so os videos da abertura: o do meio ja esta no corpo.
        if abs(mesa["videos"] - 3.0) > 0.06:
            problemas.append("a Mesa poe %s s de abertura antes do corpo" % mesa["videos"])
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("som do video no meio, e o leito por baixo", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "faixa aos %.1f s, in_s %.1f, leito a -12 dB e troco cortado ao ficheiro"
             % (t0, VIN))


def teste_corpo_da_montagem_e_o_do_render():
    """O corpo do montar_da_mesa e, clip a clip, o corpo do render. Uma conta so.

    O DEFEITO QUE ISTO PRENDE: ate 17 de setembro o corpo era "tudo o que nao e video", e a
    docstring do corpo_da_montagem() diz que essa conta ja nao vale. Mas nada a prendia:
    trocar o `render.partir_em_fanfarra_e_corpo(linhas)[1]` pelo filtro antigo passa a suite
    inteira, porque os testes de som olham para o desvio e para os instantes das faixas e
    nao para a lista.

    O que parte com a conta antiga, e nenhum deles se queixa:
      - o zip(corpo, render.encadeados_do_corpo(corpo)) fica desalinhado a partir do video,
        e os avisos das legendas passam a falar do clip errado;
      - com um video no FIM, o fim_corpo desce para o fim da foto anterior e a banda sonora
        sai mais curta do que o filme, calada nos ultimos segundos.
    """
    import shutil
    import tempfile
    import montar_da_mesa
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_corpo_")
    filme = _video_sintetico(pasta, "corpo_ensaio.mp4", dura=4.0)
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_corpo.mp4"] = (filme, 0.0)
    render.VIDEOS["corpo_ensaio.mp4"] = (filme, 0.0)
    montar_da_mesa._DURACOES.clear()
    TROCO = 2.5
    try:
        meio = [
            {"t": "video", "f": "fanfarra_corpo.mp4", "d": 4.0, "c": 0},
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "corpo_ensaio.mp4", "vin": 0.5, "d": TROCO, "c": 0.7},
            {"t": "foto", "i": "f0348", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        fim = [dict(c) for c in meio[:2]] + [dict(meio[3]), dict(meio[2])]
        for quais, onde in ((meio, "no meio"), (fim, "no fim")):
            linhas, som, _saida = _monta_em_pasta([dict(c) for c in quais],
                                                  nome="corpo_%s" % onde.split()[-1])
            meu = montar_da_mesa.corpo_da_montagem(linhas)
            dele = render.partir_em_fanfarra_e_corpo(linhas)[1]
            if [l["ordem"] for l in meu] != [l["ordem"] for l in dele]:
                problemas.append("video %s: corpo do montar %s, corpo do render %s"
                                 % (onde, [l["tipo"] for l in meu], [l["tipo"] for l in dele]))
            if not any(l["tipo"] == "video" for l in meu):
                problemas.append("video %s: o corpo ficou sem o video" % onde)
            # E OS ENCADEADOS EMPARELHAM: e sobre este zip que os avisos das legendas
            # falam, e com um clip a menos falavam do clip errado.
            if len(list(render.encadeados_do_corpo(meu))) != len(meu):
                problemas.append("video %s: %d encadeados para %d clips"
                                 % (onde, len(list(render.encadeados_do_corpo(meu))), len(meu)))
        # O FIM DO CORPO INCLUI O VIDEO QUE ESTA NO FIM. Mede-se pelo som, que e quem sofre:
        # a ultima faixa nao pode acabar antes do ultimo clip do filme.
        linhas_fim, som_fim, _s = _monta_em_pasta([dict(c) for c in fim], nome="corpo_fim2")
        corpo = montar_da_mesa.corpo_da_montagem(linhas_fim)
        # As linhas vem do CSV, logo tudo sao palavras: a conta e a mesma do montar, com
        # os numeros lidos.
        desvio = float(corpo[0]["inicio_s"])
        fim_corpo = max(float(l["fim_s"]) for l in corpo) - desvio
        ultimo = max(float(r["quando_s"]) + float(r["dura_s"]) for r in som_fim)
        if abs(fim_corpo - (max(float(l["fim_s"]) for l in linhas_fim) - desvio)) > 0.01:
            problemas.append("o fim do corpo (%.2f s) nao chega ao fim do filme" % fim_corpo)
        if ultimo < fim_corpo - 0.5:
            problemas.append("a banda sonora acaba aos %.2f s e o corpo aos %.2f s"
                             % (ultimo, fim_corpo))
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("o corpo do montar e o corpo do render, clip a clip", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "video no meio e no fim, encadeados emparelhados e som ate ao fim")


def teste_janela_do_leito_conta_com_o_cruzamento():
    """A janela que baixa o leito cobre tambem o que o cruzamento do render lhe estica.

    O DEFEITO: o montar escrevia a janela sobre a `dura_s` do CSV, e o render estica cada
    leito ate render.CRUZAMENTO segundos por cima do seguinte. Um leito que acabasse entre
    2,2 s e 0,3 s antes do som do video (ou das vozes) nao levava janela nenhuma, e depois
    era esticado para dentro dele: tocava por cima sem baixar os 12 dB e, com «parada»,
    tocava onde tinha de haver silencio. Medido a 18 de setembro: +8,8 dB no pior instante
    e 1,8 dB de media acima do alvo na voz inteira.

    Basta uma musica marcada num clip curto antes do video, que e coisa de dois cliques na
    Mesa. Aqui esse clip e um cartao de 1,7 s.
    """
    import shutil
    import tempfile
    import montar_da_mesa
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_janela_")
    filme = _video_sintetico(pasta, "janela_ensaio.mp4", dura=4.0)
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_janela.mp4"] = (filme, 0.0)
    render.VIDEOS["janela_ensaio.mp4"] = (filme, 0.0)
    montar_da_mesa._DURACOES.clear()
    try:
        clips = [
            {"t": "video", "f": "fanfarra_janela.mp4", "d": 4.0, "c": 0},
            {"t": "contador", "x": "04/10/2026>25/12/2025|hoje", "d": 9, "c": 0.7, "r": "fiel"},
            # Duas musicas marcadas seguidas: a primeira e cortada onde a segunda entra, e
            # e nessa emenda que o render cruza. O cartao e curto de proposito, 1,7 s, e o
            # video vem logo a seguir: a primeira acaba menos de 2,2 s antes dele.
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel",
             "m": {"f": "Ana Faria - Clara", "in": 0}},
            {"t": "cartao", "x": "O pedido", "d": 1.7, "c": 0.7, "r": "fiel",
             "m": {"f": "Tiago Celebration Song (Reggae)", "in": 0}},
            {"t": "video", "f": "janela_ensaio.mp4", "vin": 0.5, "d": 2.5, "c": 0.4},
            {"t": "foto", "i": "f0348", "d": 6, "c": 0.7, "r": "fiel"},
        ]
        linhas, som, _saida = _monta_em_pasta([dict(c) for c in clips], nome="janela")
        feito = ULTIMA_PASTA_MONTAGEM[0]
        video = [r for r in som if (r.get("video") or "").strip()]
        if len(video) != 1:
            problemas.append("%d faixas de video" % len(video))
        else:
            t0 = float(video[0]["quando_s"])
            # O QUE O RENDER VAI MESMO TOCAR, com o cruzamento ja aplicado.
            guardadas = render.MONTAGENS
            render.MONTAGENS = feito
            try:
                lidas = render.som_do_ficheiro("janela", 60.0)
            finally:
                render.MONTAGENS = guardadas
            esticados = [e for e in lidas if e["cruza"] > 0.01]
            if not esticados:
                problemas.append("nenhum leito foi esticado: o caso nao chegou a existir")
            for e in lidas:
                if render.entra_depressa(e):
                    continue
                if e["quando"] + e["dura"] <= t0 + 0.01:
                    continue          # acaba mesmo antes do video: nao lhe toca
                janelas = e["abafar"]
                if not any(a <= t0 + 0.05 and b >= t0 for a, b, _k in janelas):
                    problemas.append("o leito %s toca ate aos %.2f s, por cima do video que "
                                     "comeca aos %.2f s, e nao leva janela nenhuma: %s"
                                     % (e["ficheiro"][:28], e["quando"] + e["dura"], t0, janelas))
        # E A CONSTANTE E A DO RENDER, nao uma copia. Uma copia foi como o render passou a
        # usar a versao errada de cada foto.
        if "CRUZAMENTO" not in vars(render):
            problemas.append("o render deixou de exportar o CRUZAMENTO")
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("a janela do leito conta com o cruzamento do render", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "leito esticado %.1f s e coberto pela janela" % render.CRUZAMENTO)


def teste_musica_parada_conta_os_buracos():
    """Com «musica parada por baixo», o aviso conta os buracos MEDIDOS, e nao so as pausas.

    O DEFEITO: o aviso so falava do ar entre duas pecas de voz. Com a janela a zero o que
    resta na mistura e so a voz, ou o som do video, e onde eles nao tem nada nao fica nada:
    medido, cinco buracos, um deles a -164 dBFS de RMS, que sao zeros. Dentro do troco do
    Homer ha dois, entre «D'oh» e «D'oh», e o aviso nao dizia uma palavra sobre eles. Numa
    sala com 140 pessoas, zeros leem-se como o som a falhar.

    Nao se muda a janela, que e escolha de som dele; o que se exige e que ele escolha com
    o numero a frente.
    """
    import shutil
    import subprocess
    import tempfile
    import montar_da_mesa
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_buracos_")
    caminho = os.path.join(pasta, "buraco_ensaio.mp4")
    # Um tom de 3 s com 0,6 s calados no meio: e a forma do troco do Homer, som, ar, som.
    subprocess.run(
        [render.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=3.0",
         "-f", "lavfi", "-i", "sine=frequency=520:duration=3.0:sample_rate=48000",
         "-af", "volume=0:enable='between(t,1.0,1.6)'",
         "-c:v", "libx264", "-crf", "10", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-shortest", caminho], capture_output=True)
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_buraco.mp4"] = (caminho, 0.0)
    render.VIDEOS["buraco_ensaio.mp4"] = (caminho, 0.0)
    montar_da_mesa._DURACOES.clear()
    try:
        # 1. A MEDIDA, sozinha: o buraco aparece onde ele foi posto.
        medidos = montar_da_mesa.buracos_de_som(caminho, 0.0, 3.0)
        if not any(abs(a - 1.0) < 0.15 and abs(b - 1.6) < 0.15 for a, b in medidos):
            problemas.append("o buraco de 1,0 a 1,6 s nao foi medido: %s" % (medidos,))
        if montar_da_mesa.buracos_de_som(caminho, 0.0, 0.9):
            problemas.append("um troco sem buracos deu buracos: %s"
                             % (montar_da_mesa.buracos_de_som(caminho, 0.0, 0.9),))
        base = [
            {"t": "video", "f": "fanfarra_buraco.mp4", "d": 3.0, "c": 0},
            {"t": "contador", "x": "04/10/2026>25/12/2025|hoje", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "buraco_ensaio.mp4", "vin": 0.0, "d": 3.0, "c": 0.7,
             "vzm": "parada"},
            {"t": "foto", "i": "f0348", "d": 6, "c": 0.7, "r": "fiel"},
        ]
        _l, _som, saida = _monta_em_pasta([dict(c) for c in base], nome="buraco")
        if "buraco de silencio" not in saida and "buracos de silencio" not in saida:
            problemas.append("com «parada» o aviso nao conta os buracos: %r" % saida[-400:])
        # 2. COM «MAIS BAIXA» NAO HA AVISO NENHUM: ali a musica continua a tocar no ar.
        baixa = [dict(c) for c in base]
        baixa[3] = dict(baixa[3])
        baixa[3].pop("vzm")
        _l2, _som2, saida2 = _monta_em_pasta(baixa, nome="buraco2")
        if "buracos de silencio" in saida2:
            problemas.append("com «mais baixa» avisou de buracos que nao existem")
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("com a musica parada, o aviso conta os buracos medidos", not problemas,
             "; ".join(problemas)[:220] if problemas else
             "buraco de 0,6 s medido e contado, e nenhum aviso com «mais baixa»")


def teste_cache_de_quadros_nao_apaga_a_de_outra_montagem():
    """A varredura da cache so apaga as pastas DESTA montagem, e nao as de nome parecido.

    O DEFEITO: a comparacao era por prefixo, "_quadros_v3_", e "_quadros_v3_mesa_6" comeca
    por ai. Um render do v3 apagava a cache de um render do v3_mesa a decorrer ao lado, sem
    passar pelo teste das seis horas que existe exatamente para isso, e as fatias do outro
    ficavam a abrir ficheiros que ja nao existiam. O --nome v3_mesa esta escrito no
    cabecalho do montar_da_mesa.py: e caminho normal, nao caso raro.
    """
    import shutil
    import tempfile
    import render
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_cache_")
    guardada = render.QUADROS
    render.QUADROS = pasta
    try:
        vizinhas = ["_quadros_v3_mesa_6", "_quadros_demo_v3_4", "_quadros_v3_2"]
        for nome in vizinhas:
            os.makedirs(os.path.join(pasta, nome), exist_ok=True)
        render.preparar_quadros_dos_videos(render.ffmpeg(), {"nome": "v3", "resto": []})
        ficaram = sorted(os.listdir(pasta))
        if "_quadros_v3_mesa_6" not in ficaram:
            problemas.append("a cache do v3_mesa foi apagada por um render do v3: %s" % ficaram)
        if "_quadros_demo_v3_4" not in ficaram:
            problemas.append("a cache do demo_v3 foi apagada: %s" % ficaram)
        if "_quadros_v3_2" in ficaram:
            problemas.append("a cache da propria montagem nao foi refeita: %s" % ficaram)
        # UMA PASTA VELHA DE OUTRA MONTAGEM APAGA-SE NA MESMA: e o outro lado da regra.
        import time
        velha = os.path.join(pasta, "_quadros_v9_1")
        os.makedirs(velha, exist_ok=True)
        antiga = time.time() - render.SEGUNDOS_CACHE_VELHA - 60
        os.utime(velha, (antiga, antiga))
        render.preparar_quadros_dos_videos(render.ffmpeg(), {"nome": "v3", "resto": []})
        if os.path.isdir(velha):
            problemas.append("uma pasta esquecida ha mais de seis horas ficou por apagar")
    finally:
        render.QUADROS = guardada
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("a cache de quadros nao apaga a de outra montagem", not problemas,
             "; ".join(problemas)[:200] if problemas else
             "v3 nao toca no v3_mesa nem no demo_v3, e apaga a velha")


def teste_cache_de_quadros_grande_para_antes_de_encher_o_disco():
    """Muito video no corpo para o render antes de escrever, em vez de encher o disco.

    O DEFEITO: nao havia conta nenhuma. A lista do «+ Vídeo» da Mesa inclui um ficheiro de
    1410 s e o botao cria o clip com duracao 0, que quer dizer o ficheiro inteiro; isso sao
    35 250 JPEG a caminho do disco do sistema, entre 1,4 e 4 GB, sem uma palavra.
    """
    import render
    problemas = []
    if render.cabe_no_disco(3.5):
        problemas.append("3,5 s de video (a piada do Homer) foram recusados")
    queixa = render.cabe_no_disco(1410.0)
    if not queixa:
        problemas.append("1410 s de video passaram sem uma palavra")
    elif "GB" not in queixa:
        problemas.append("a queixa nao diz quanto disco e: %r" % queixa)
    guardado = list(sys.argv)
    try:
        sys.argv = guardado + ["--quadros-grandes"]
        if render.cabe_no_disco(1410.0):
            problemas.append("o --quadros-grandes nao deixou passar")
    finally:
        sys.argv = guardado
    verifica("cache de quadros grande para antes de encher o disco", not problemas,
             "; ".join(problemas)[:200] if problemas else
             "3,5 s passam, 1410 s param e dizem os GB, e ha maneira de insistir")


def _video_sem_som(pasta, nome, dura=3.0):
    """Um video SO COM IMAGEM, sem stream de audio nenhum.

    Existe um assim na pasta dos videos do projeto, e a Mesa oferece-o na lista como
    oferece os outros. Aqui e sintetico, para o teste nao depender daquele ficheiro.
    """
    import subprocess
    import render
    caminho = os.path.join(pasta, nome)
    subprocess.run(
        [render.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=%.2f,"
                              "geq=lum='3.2*N':cb=128:cr=128" % dura,
         "-an", "-c:v", "libx264", "-crf", "10", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", caminho], capture_output=True)
    return caminho


def teste_video_mudo_nao_cala_o_filme():
    """Um video do corpo sem stream de audio passa mudo, e o resto da banda sonora toca na mesma.

    O DEFEITO, e nao e pequeno: o montar escrevia sempre uma faixa a apontar para o
    proprio MP4 do video do corpo. O construir_som pede [i:a] a cada entrada; um ficheiro
    sem audio nao tem [i:a], o ffmpeg recusa o FILTERGRAPH INTEIRO, a funcao devolve False
    e o filme e fechado SEM BANDA SONORA NENHUMA. Nao so sem este clip: sem o Lang Lang,
    sem os foguetes, sem o Rei Leao, sem tudo. O render nao falha, escreve o MP4 e
    regista-o, e a unica pista e uma linha "ERRO no som" no meio do registo. A pasta dos
    videos do projeto ja tem hoje um ficheiro assim, e a Mesa oferece-o na lista.

    As duas metades da correcao estao aqui: o montar nao escreve a faixa e avisa, e o
    render, se ela la chegar por outro caminho, salta a entrada em vez de calar o filme.
    Vale a regra do imagem_da_marca(): um ficheiro estranho nao para nem cala quinze
    minutos de filme.
    """
    import shutil
    import subprocess
    import tempfile
    import montar_da_mesa
    import render
    pasta = tempfile.mkdtemp(prefix="teste_video_mudo_")
    problemas = []
    com_som = _video_sintetico(pasta, "com_som_ensaio.mp4")
    mudo = _video_sem_som(pasta, "mudo_ensaio.mp4")
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_ensaio.mp4"] = (com_som, 0.0)
    render.VIDEOS["com_som_ensaio.mp4"] = (com_som, 0.0)
    render.VIDEOS["mudo_ensaio.mp4"] = (mudo, 0.0)
    montar_da_mesa._DURACOES.clear()
    render._TEM_SOM.clear()
    try:
        # 0. O ficheiro de ensaio e mesmo mudo, e o outro tem mesmo som. Sem isto o resto
        #    do teste podia estar a passar por nao haver defeito nenhum para ver.
        if render.tem_stream_de_som(mudo) or not render.tem_stream_de_som(com_som):
            problemas.append("os videos de ensaio nao sao o que o teste julga")
        base = [
            {"t": "video", "f": "fanfarra_ensaio.mp4", "d": 3.0, "c": 0},
            {"t": "contador", "x": "2025>1995|x", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "mudo_ensaio.mp4", "vin": 0.5, "d": 2.0, "c": 0.7},
            {"t": "foto", "i": "f0348", "d": 6, "c": 0.7, "r": "fiel"},
            {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        # 1. O MONTAR NAO ESCREVE A FAIXA, e diz porque. A imagem do clip fica na mesma.
        linhas, som, saida = _monta_em_pasta([dict(c) for c in base], nome="mudo")
        if [r for r in som if r["ficheiro"] == "mudo_ensaio.mp4"]:
            problemas.append("o montar escreveu faixa de som para um video sem audio")
        if "nao tem som" not in saida:
            problemas.append("o montar nao avisou que o video e mudo: %r" % saida[-300:])
        if abs(float(linhas[3]["duracao_s"]) - 2.0) > 0.06:
            problemas.append("a imagem do video mudo mudou de duracao: %s" % linhas[3]["duracao_s"])
        # E nao fica janela nenhuma a baixar o leito por baixo de um clip que nao faz som.
        abertura = [r for r in som if r["nota"].startswith("do pedido")]
        if abertura and render.ler_abafar(abertura[0].get("abafar")):
            problemas.append("o leito baixou por baixo de um video mudo")
        # 2. O MESMO SITIO COM UM VIDEO QUE TEM SOM leva faixa: o aviso e do ficheiro e nao
        #    do sitio onde ele esta.
        outro = [dict(c) for c in base]
        outro[3] = dict(outro[3], f="com_som_ensaio.mp4")
        _l2, som2, _s2 = _monta_em_pasta(outro, nome="mudo2")
        if len([r for r in som2 if r["ficheiro"] == "com_som_ensaio.mp4"]) != 1:
            problemas.append("o video com som ficou sem faixa")
        # 3. O RENDER SOBREVIVE A UMA ENTRADA MUDA. Se ela chegar la por outro caminho, as
        #    outras faixas tem de tocar na mesma.
        def entrada(ficheiro, caminho, quando, dura, video=False):
            return {"ficheiro": ficheiro, "caminho": caminho, "encontrado": "Sim",
                    "quando": quando, "in_s": 0.0, "dura": dura, "ganho": 1.0,
                    "cruza": 0.0, "abafar": [], "voz": "", "video": "1" if video else ""}

        musica = os.path.join(pasta, "leito.wav")
        subprocess.run([render.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "sine=frequency=330:duration=8:sample_rate=48000", musica],
                       capture_output=True)
        entradas = [entrada("leito.wav", musica, 0.0, 8.0),
                    entrada("mudo_ensaio.mp4", mudo, 2.0, 2.0, video=True)]
        alvo = os.path.join(pasta, "som_com_mudo.m4a")
        with contextlib_silencio():
            ok = render.construir_som(render.ffmpeg(), entradas, 8.0, alvo)
        if not ok or not os.path.exists(alvo) or os.path.getsize(alvo) < 5000:
            problemas.append("com uma entrada muda o som do filme inteiro caiu: ok=%s, %d bytes"
                             % (ok, os.path.getsize(alvo) if os.path.exists(alvo) else -1))
        # A MUTACAO: sem a pergunta ao ffprobe, a mesma chamada deita tudo abaixo. Se isto
        # passasse, a guarda acima nao provava nada.
        certo = render.tem_stream_de_som
        alvo2 = os.path.join(pasta, "som_sem_guarda.m4a")
        try:
            render.tem_stream_de_som = lambda _c: True
            with contextlib_silencio():
                ok2 = render.construir_som(render.ffmpeg(), entradas, 8.0, alvo2)
        finally:
            render.tem_stream_de_som = certo
        if ok2:
            problemas.append("sem a guarda o ffmpeg aceitou a entrada muda: a guarda nao "
                             "prova nada")
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        render._TEM_SOM.clear()
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("video mudo no corpo nao cala o filme", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "sem faixa e com aviso no montar, e o leito toca na mesma no render")


def teste_video_do_meio_sem_duracao_mede_o_ficheiro():
    """Um video do corpo com a duracao que o botao «+ Video» lhe da (0) entra do `vin` ate ao fim.

    E O CAMINHO POR OMISSAO DA FUNCIONALIDADE: abrir um clip, carregar em «+ Video»,
    escolher o ficheiro e nao escrever duracao nenhuma. A Mesa promete-o por palavras em
    dois sitios, a etiqueta da lista e a nota do inspetor ("com o comprimento medido quando
    eu montar"), mas so o ramo da fanfarra media o ficheiro: um video do corpo caia no ramo
    do troco e ficava com d = 0. Duracao zero, inicio igual ao fim, nunca ativo no ciclo dos
    fotogramas, sem faixa de som, desaparecido do filme, e o unico sinal era um aviso a
    falar de som.
    """
    import shutil
    import tempfile
    import montar_da_mesa
    import render
    pasta = tempfile.mkdtemp(prefix="teste_video_d0_")
    problemas = []
    filme = _video_sintetico(pasta, "d0_ensaio.mp4", dura=3.0)
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_ensaio.mp4"] = (filme, 0.0)
    render.VIDEOS["d0_ensaio.mp4"] = (filme, 0.0)
    montar_da_mesa._DURACOES.clear()
    try:
        real = montar_da_mesa.duracao_do_video("d0_ensaio.mp4")
        base = [
            {"t": "video", "f": "fanfarra_ensaio.mp4", "d": 3.0, "c": 0},
            {"t": "contador", "x": "2025>1995|x", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "d0_ensaio.mp4", "d": 0, "c": 0.7},
            {"t": "foto", "i": "f0348", "d": 6, "c": 0.7, "r": "fiel"},
            {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        # 1. SEM vin: o ficheiro inteiro, medido.
        linhas, som, saida = _monta_em_pasta([dict(c) for c in base], nome="d0")
        l = linhas[3]
        if abs(float(l["duracao_s"]) - real) > 0.06:
            problemas.append("d = 0 no corpo deu %s s, o ficheiro tem %.2f s"
                             % (l["duracao_s"], real))
        if float(l["fim_s"]) - float(l["inicio_s"]) < 0.5:
            problemas.append("o clip do video ficou sem tempo nenhum no filme: %s a %s"
                             % (l["inicio_s"], l["fim_s"]))
        if abs(float(l["out_s"] or 0) - real) > 0.06 or float(l["in_s"] or 0) != 0.0:
            problemas.append("troco escrito: %s a %s" % (l["in_s"], l["out_s"]))
        if len([r for r in som if r["ficheiro"] == "d0_ensaio.mp4"]) != 1:
            problemas.append("um video com d = 0 ficou sem faixa de som")
        if "sem duracao escrita" not in saida:
            problemas.append("o montar mediu o ficheiro sem o dizer")
        # 2. COM vin: do vin ate ao fim, e nao o ficheiro todo.
        com_vin = [dict(c) for c in base]
        com_vin[3] = dict(com_vin[3], vin=1.2)
        l2, _som2, _s2 = _monta_em_pasta(com_vin, nome="d0v")
        if abs(float(l2[3]["duracao_s"]) - (real - 1.2)) > 0.06:
            problemas.append("com vin 1,2 deu %s s, esperava %.2f s"
                             % (l2[3]["duracao_s"], real - 1.2))
        if abs(float(l2[3]["in_s"]) - 1.2) > 0.01:
            problemas.append("com vin 1,2 o in_s ficou %s" % l2[3]["in_s"])
        # 3. NO BLOCO INICIAL COM vin: o mesmo, porque o montar corta-o na mesma la.
        inicial = [dict(c) for c in base]
        inicial[0] = {"t": "video", "f": "d0_ensaio.mp4", "d": 0, "vin": 1.2, "c": 0}
        l3, _som3, _s3 = _monta_em_pasta(inicial, nome="d0i")
        if abs(float(l3[0]["duracao_s"]) - (real - 1.2)) > 0.06:
            problemas.append("no bloco inicial com vin deu %s s" % l3[0]["duracao_s"])
        # 4. A FANFARRA DE SEMPRE (sem vin, sem troco) continua a ser medida pelo ficheiro.
        if abs(float(linhas[0]["duracao_s"]) - real) > 0.06 or linhas[0]["in_s"]:
            problemas.append("a fanfarra mudou: %s s, in_s %r"
                             % (linhas[0]["duracao_s"], linhas[0]["in_s"]))
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("video do corpo sem duracao mede o ficheiro", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "d = 0 vira o ficheiro inteiro, e com vin vai do vin ao fim")


def teste_video_em_falta_nao_para_o_render():
    """Um video do corpo cujo ficheiro nao esta em disco nao faz o render morrer a meio.

    O NOME PODE SER ESCRITO A MAO na Mesa, e a lista dos ficheiros que ela leva e um
    retrato do momento da publicacao: ele pode renomear ou mover o ficheiro depois. O
    montar avisa e mantem o clip com a sua duracao. No render, o extrair_quadros desistia
    ANTES de criar a pasta, e por isso o preparar() de um clip de video encontrava uma
    pasta inexistente e saia com sys.exit, a meio de quinze minutos, com uma mensagem a
    culpar o mecanismo das fatias. A regra e a do imagem_da_marca(), e esta escrita no
    proprio caminho_de_video(): "Um video de abertura em falta nao pode fazer o render
    abortar a meio".
    """
    import shutil
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_video_falta_")
    problemas = []
    guardadas_m = render.MONTAGENS
    guardado = _resolucao(render, 480, 270)
    pastas = []
    try:
        clips = [
            dict(tipo="cartao", duracao_s="1.2", transicao_s="0", texto_ecra="Era uma vez"),
            dict(tipo="video", ficheiro="nao_existe_em_disco.mp4", duracao_s="2.0",
                 transicao_s="0.4", in_s="1.0", out_s="3.0"),
            dict(tipo="cartao", duracao_s="1.2", transicao_s="0.4", texto_ecra="Fim"),
        ]
        _escrever_montagem(pasta, "falta", clips)
        render.MONTAGENS = pasta
        estado = render.carregar_montagem("falta", None)
        with contextlib_silencio():
            pastas = render.preparar_quadros_dos_videos(render.ffmpeg(), estado)
        em_falta = [c for c in estado["resto"] if c["tipo"] == "video"][0]
        if not os.path.isdir(em_falta["_quadros"]):
            problemas.append("a pasta da cache nem chegou a existir: o preparar() vai sair "
                             "com sys.exit a meio do render")
        if render.quadros_da_cache(em_falta["_quadros"]):
            problemas.append("uma cache de um ficheiro que nao existe ficou com fotogramas")
        saiu, pronto = "", None
        try:
            pronto = render.preparar(em_falta, {})
        except SystemExit as e:
            saiu = str(e)
        if saiu:
            problemas.append("o render parou a meio: %r" % saiu[:120])
        elif pronto is not None:
            problemas.append("um video em falta devia dar o mesmo que uma foto que nao abre")
        # E A MENSAGEM DA CACHE QUE FALTA CONTINUA A EXISTIR para o caso que ela descreve:
        # uma fatia a chegar a um clip cuja pasta o processo principal nunca criou.
        erro = ""
        try:
            render.preparar(dict(em_falta, _quadros=os.path.join(pasta, "nunca_criada")), {})
        except SystemExit as e:
            erro = str(e)
        if "cache" not in erro or "processo principal" not in erro:
            problemas.append("uma fatia sem cache nenhuma diz: %r" % erro[:110])
    finally:
        render.L, render.A = guardado
        render.MONTAGENS = guardadas_m
        render.apagar_quadros(pastas)
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("video em falta nao para o render a meio", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "cache vazia criada, clip sai como uma foto que nao abre")


def teste_juntar_repoe_so_o_bloco_inicial():
    """A juncao antes do render repoe a FANFARRA, e nao "todos os videos".

    A conta era "tipo == video" contra o resto, escrita quando todo o video era abertura.
    Com um video no meio da montagem ela mentia de duas maneiras, e as duas em silencio:
      A. a Mesa dele fica sem videos (foi para isto que o script nasceu) e a copia local
         tem a fanfarra mais o video do meio: os TRES iam a cabeca, o video do meio saia
         colado a 20th Century Fox e o corpo ficava sem ele, com o script a dizer
         "Juntei: 3 videos no inicio" como se estivesse certo;
      B. a Mesa dele perde a fanfarra mas guarda o video do meio: como "ja tem um video",
         a guarda nao disparava, a fanfarra nao era reposta e o script imprimia "nada". O
         filme passava a abrir no contador, sem a 20th Century Fox nem a historia da
         Clara, que a decisao 001 diz que nenhuma versao pode apagar.
    O data/mesa_estado.json do repositorio nao e tocado: o LOCAL aponta para uma copia.
    """
    import contextlib
    import io
    import json
    import shutil
    import tempfile
    import juntar_mesa
    problemas = []
    pasta = tempfile.mkdtemp(prefix="teste_juntar_")
    guardado = (juntar_mesa.LOCAL, sys.argv)

    FANFARRA = {"t": "video", "i": "", "f": "20th Century Fox Intro HD.mp4", "d": 20.4, "c": 0}
    HISTORIA = {"t": "video", "i": "", "f": "intro_clara_tiago.mp4", "d": 8.0, "c": 0}
    MEIO = {"t": "video", "i": "", "f": "Homer.mp4", "d": 3.5, "vin": 6.1, "c": 0.7}
    FOTO = {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"}
    CONTADOR = {"t": "contador", "x": "2025>1995|x", "d": 9, "c": 0.7, "r": "fiel"}

    def corre(meus, dele):
        def est(cs):
            return {"rev": 3, "versoes": [{"id": "demo_v3", "nome": "v3", "clips": cs}]}
        local = os.path.join(pasta, "local.json")
        remoto = os.path.join(pasta, "remoto.json")
        json.dump(est(meus), open(local, "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(est(dele), open(remoto, "w", encoding="utf-8"), ensure_ascii=False)
        juntar_mesa.LOCAL = local
        sys.argv = ["juntar_mesa.py", remoto]
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            juntar_mesa.main()
        saiu = json.load(open(local, encoding="utf-8"))
        return [c.get("f") or c.get("t") for c in saiu["versoes"][0]["clips"]], log.getvalue()

    try:
        # A. Ele sem videos nenhuns; eu com a fanfarra a cabeca e o Homer no meio.
        meus = [FANFARRA, HISTORIA, CONTADOR, dict(FOTO), MEIO, dict(FOTO)]
        ordem, texto = corre(meus, [CONTADOR, dict(FOTO), dict(FOTO)])
        if ordem[:2] != ["20th Century Fox Intro HD.mp4", "intro_clara_tiago.mp4"]:
            problemas.append("A: a abertura nao foi reposta: %s" % ordem[:3])
        if "Homer.mp4" in ordem:
            problemas.append("A: o video do meio foi juntado sozinho, e so ele sabe onde o quer")
        if "Homer.mp4" not in texto:
            problemas.append("A: o video do meio ficou de fora sem uma palavra")
        if "2 videos no inicio" not in texto:
            problemas.append("A: o script diz %r" % texto.strip()[-120:])
        # B. Ele sem a abertura, mas com o Homer no meio: a fanfarra tem de voltar.
        ordem, texto = corre(meus, [CONTADOR, dict(FOTO), MEIO, dict(FOTO)])
        if ordem[:2] != ["20th Century Fox Intro HD.mp4", "intro_clara_tiago.mp4"]:
            problemas.append("B: com um video no meio a abertura nao voltou: %s" % ordem[:4])
        if ordem.count("Homer.mp4") != 1:
            problemas.append("B: o Homer ficou %d vezes na montagem" % ordem.count("Homer.mp4"))
        # C. Ele com tudo: nao se mexe em nada.
        ordem, texto = corre(meus, list(meus))
        if "nada" not in texto or ordem != [c.get("f") or c.get("t") for c in meus]:
            problemas.append("C: com tudo no sitio o script mexeu: %r" % texto.strip()[-120:])
        # D. O clip legado t:"fanfarra" nao conta: um video a seguir a ele e bloco inicial,
        #    que e o que o montar_da_mesa.py faz quando o salta.
        legado = [{"t": "fanfarra", "x": "", "d": 1, "c": 0}, FANFARRA, CONTADOR, dict(FOTO)]
        if [c.get("f") for c in juntar_mesa.bloco_inicial(legado)] != ["20th Century Fox Intro HD.mp4"]:
            problemas.append("D: o bloco inicial com um clip legado a frente: %s"
                             % [c.get("t") for c in juntar_mesa.bloco_inicial(legado)])
    finally:
        juntar_mesa.LOCAL, sys.argv = guardado
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("a juncao repoe so o bloco inicial", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "abertura reposta nos dois casos, video do meio deixado com aviso")


def teste_janelas_do_leito_sobrepostas_e_no_fim():
    """Duas janelas sobrepostas baixam 12 dB e nao 24, e uma janela no fim do leito levanta-se.

    OS DOIS DEFEITOS, medidos no som que sai e nao no comando que entra:
      1. os termos das janelas eram MULTIPLICADOS. Uma voz do pedido e o som de um video a
         cruzarem-se punham o leito a 0,251 x 0,251, que sao 24 dB abaixo em vez dos 12 do
         contrato; com tres coisas por cima, 36. O que manda e a coisa que pede mais
         silencio, por isso a conta e o minimo;
      2. o loudnorm guarda tres segundos de antecipacao e despeja-os num so fotograma de
         audio. Como o volume=eval=frame avalia a expressao uma vez por fotograma, essa
         cauda ficava toda com o ganho do instante em que ela comeca: o relogio parava 2,9 s
         antes do fim da faixa. Uma janela cujo levantamento caisse ali NUNCA SE LEVANTAVA,
         e a musica ficava em baixo (ou calada) ate ao fim, sem aviso nenhum.
    """
    import array
    import math
    import shutil
    import subprocess
    import tempfile
    import render
    pasta = tempfile.mkdtemp(prefix="teste_janelas_")
    problemas = []
    ff = render.ffmpeg()
    SR, DURA = 48000, 18.17
    try:
        fonte = os.path.join(pasta, "leito.wav")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "sine=frequency=330:duration=%.2f:sample_rate=48000" % DURA,
                        fonte], capture_output=True)

        def constroi(janelas, etiqueta):
            e = {"ficheiro": "leito.wav", "caminho": fonte, "encontrado": "Sim",
                 "quando": 0.0, "in_s": 0.0, "dura": DURA, "ganho": 1.0, "cruza": 0.0,
                 "abafar": janelas, "voz": "", "video": ""}
            alvo = os.path.join(pasta, "s_%s.m4a" % etiqueta)
            with contextlib_silencio():
                ok = render.construir_som(ff, [e], DURA, alvo)
            if not ok:
                problemas.append("%s: o som nao foi construido" % etiqueta)
                return None
            cru = os.path.join(pasta, "s_%s.raw" % etiqueta)
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", alvo,
                            "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(SR),
                            cru], capture_output=True)
            d = array.array("h")
            d.frombytes(open(cru, "rb").read())
            return d

        def razao(com, sem):
            """dB do leito com janelas contra o mesmo leito sem nenhuma, de 0,2 em 0,2 s."""
            n = min(len(com), len(sem))
            p = int(SR * 0.2)
            return [(k / float(SR),
                     20 * math.log10((max(abs(v) for v in com[k:k + p]) or 1)
                                     / float(max(abs(v) for v in sem[k:k + p]) or 1)))
                    for k in range(0, n - p, p)]

        BAIXA = 10 ** (-12.0 / 20.0)
        sem = constroi([], "sem")
        # 1. DUAS JANELAS SOBREPOSTAS: 6,0-12,0 e 10,0-14,0, cruzadas entre os 10 e os 12.
        duas = constroi([(6.0, 12.0, BAIXA), (10.0, 14.0, BAIXA)], "duas")
        if sem and duas:
            r = razao(duas, sem)
            cruzado = [v for t, v in r if 10.6 < t < 11.4]
            so_uma = [v for t, v in r if 7.0 < t < 9.4] + [v for t, v in r if 12.6 < t < 13.4]
            if not cruzado or max(abs(v + 12.0) for v in cruzado) > 1.0:
                problemas.append("onde as duas janelas se cruzam o leito ficou a %s dB"
                                 % ["%.1f" % v for v in cruzado[:4]])
            if not so_uma or max(abs(v + 12.0) for v in so_uma) > 1.0:
                problemas.append("com uma janela so o leito ficou a %s dB"
                                 % ["%.1f" % v for v in so_uma[:4]])
        # 2. UMA JANELA QUE ACABA NOS ULTIMOS TRES SEGUNDOS tem de voltar a 0 dB.
        fim = constroi([(13.2, 16.67, BAIXA)], "fim")
        if sem and fim:
            r = razao(fim, sem)
            depois = [v for t, v in r if 17.2 < t < DURA - 0.4]
            dentro = [v for t, v in r if 14.0 < t < 16.0]
            if not depois or max(abs(v) for v in depois) > 1.2:
                problemas.append("depois do levantamento o leito ficou a %s dB em vez de 0"
                                 % ["%.1f" % v for v in depois[:4]])
            if not dentro or max(abs(v + 12.0) for v in dentro) > 1.0:
                problemas.append("dentro da janela do fim o leito ficou a %s dB"
                                 % ["%.1f" % v for v in dentro[:4]])
        # 3. UMA FAIXA SEM JANELAS DA O COMANDO DE SEMPRE, ao caracter: e o que faz o som
        #    de hoje sair igual ao byte.
        so_ganho = render.volume_da_faixa({"ganho": 1.0, "quando": 0.0, "abafar": []})
        if so_ganho != "volume=1.000":
            problemas.append("uma faixa sem janelas mudou de comando: %r" % so_ganho)
        uma = render.volume_da_faixa({"ganho": 1.0, "quando": 0.0, "abafar": [(1.0, 2.0, 0.251)]})
        if "min(1-" in uma or uma.count("(1-") != 1 or uma.startswith("volume=eval=frame:volume='1.000*min"):
            problemas.append("uma janela so deixou de dar o comando de antes: %r" % uma[:90])
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("janelas do leito: sobrepostas e no fim da faixa", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "duas sobrepostas dao -12 dB, e a do fim volta a 0 dB")


def teste_mesa_diz_o_que_a_musica_faz_por_baixo_de_cada_um():
    """Com uma janela parada e outra so mais baixa, a Mesa diz as duas coisas.

    A escolha era all(k <= 0.001): bastava uma janela que nao parasse a musica para TODAS
    passarem a "mais baixa". O caso e o da intro que ele pediu: o video com «Musica por
    baixo: parada» e uma foto ali perto com vozes e a musica mais baixa. Por baixo do video
    a musica calava-se mesmo, e a Mesa dizia-lhe que ela continuava a tocar.
    """
    import render
    import som_para_mesa
    problemas = []
    quem = {"voz": "das vozes do pedido", "video": "do som do vídeo"}

    def so(qual):
        return lambda _janelas: quem[qual]

    casos = [([(6.3, 12.2, 0.251)], so("voz"),
              "mais baixa por baixo das vozes do pedido", "parada"),
             ([(6.3, 12.2, 0.0)], so("voz"),
              "parada por baixo das vozes do pedido", "mais baixa")]
    for janelas, q, tem, nao_tem in casos:
        texto = som_para_mesa.formas_do_abafar(janelas, q)
        if tem not in texto or nao_tem in texto:
            problemas.append("%s deu %r" % (janelas, texto))

    # AS DUAS AO MESMO TEMPO: uma frase para cada, com quem esta por cima de cada uma.
    def por_janela(js):
        return quem["video"] if all(k <= 0.001 for _a, _b, k in js) else quem["voz"]

    misto = som_para_mesa.formas_do_abafar([(6.3, 12.2, 0.251), (16.5, 19.97, 0.0)], por_janela)
    if "mais baixa por baixo das vozes do pedido" not in misto \
            or "parada por baixo do som do vídeo" not in misto:
        problemas.append("com uma parada e uma mais baixa a Mesa diz %r" % misto)
    # E O PARSER DA COLUNA E O DO RENDER, UM SO: tres copias da mesma regra ja fizeram o
    # render usar a versao errada de cada foto.
    celula = "6.30-12.20x0.251;16.50-19.97x0.000"
    if [(a, b, k) for a, b, k in render.ler_abafar(celula)] != som_para_mesa.ler_abafar(celula):
        problemas.append("o som_para_mesa le a coluna abafar de outra maneira que o render")
    verifica("a Mesa diz o que a musica faz por baixo de cada um", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "uma frase por forma, e a coluna lida pelo render")


def teste_mesa_conta_o_video_do_meio_como_o_montar():
    """As contas da Mesa sobre um video do meio dao o mesmo que o montar_da_mesa.py.

    TRES DESENCONTROS, todos na fronteira com um video do corpo, que e o que esta ronda
    tornou possivel:
      - videoNoCorpo() contava o clip legado t:"fanfarra" como "outro clip", e um video a
        seguir a um desses mostrava os campos do troco na Mesa e ia para a fanfarra no
        montar. As versoes v1a, v1b e v1c tem cada uma um clip assim;
      - duracaoNoTempo() tirava ao clip o encadeado DELE PROPRIO, e o relogio do montar tira
        o do clip SEGUINTE. Numa fila de fotos todas com 0,7 as duas contas dao o mesmo; com
        um video a nascer com encadeado 0, a Mesa dizia que as vozes acabavam 0,7 s mais a
        dentro do que acabam, e o botao "Ajustar as fotos ao tempo das vozes" repartia um
        tempo que nao e o certo;
      - trocoDoVideo() avisava "nao cabe" com uma folga cinquenta vezes mais apertada do que
        a do montar, e havia uma faixa em que a Mesa dizia que ia cortar e o montar nao
        cortava nada.
    Corre no node, sobre a MESMA montagem que o montar_da_mesa.py mede. Sem node, diz-se e
    nao conta.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import montar_da_mesa
    import render
    node = shutil.which("node")
    if not node:
        salta("Mesa e montar: o video do meio", "sem node neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []
    marcas = ["function eGrupo(", "function clipsDoCorpo(", "function videoNoCorpo(",
              "function duracaoNoTempo(", "function pecaDoVideo(", "function duraDoVideo(",
              "function trocoDoVideo(", "function etiquetaDoTroco(", "function s1(",
              "function duracaoDoVideoNoFilme(", "function duracaoDoClip(",
              "function ocupaNaLista(", "function encadeadoDoClip(",
              "function contadoresSeguidos(", "function pontoDoContador(",
              "function lerContador(", "function eDataContador(", "function dataParaIso(",
              "function d2("]
    js = "\n".join(_bloco_do_editor(html, m, problemas) for m in marcas)

    pasta = tempfile.mkdtemp(prefix="teste_mesa_video_")
    filme = _video_sintetico(pasta, "meio_mesa.mp4", dura=6.0)
    guardadas_v = dict(render.VIDEOS)
    render.VIDEOS["fanfarra_mesa.mp4"] = (filme, 0.0)
    render.VIDEOS["meio_mesa.mp4"] = (filme, 0.0)
    montar_da_mesa._DURACOES.clear()
    try:
        real = montar_da_mesa.duracao_do_video("meio_mesa.mp4")
        clips = [
            {"t": "video", "f": "fanfarra_mesa.mp4", "d": 3.0, "c": 0},
            # A ABERTURA DE 17 DE SETEMBRO: o contador de datas e, logo a seguir, o de anos
            # que comeca onde ele acaba. O montar junta-os com corte seco e a Mesa mostrava
            # "cross 0,7s" nos dois e descontava esses 0,7 s: dali para a frente tudo o que
            # ela dizia ficava adiantado.
            {"t": "contador", "x": "04/10/2026>25/12/2025|hoje;25/12/2025=o pedido",
             "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "contador", "x": "2025>1995|x", "d": 9, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0347", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0348", "d": 4, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "meio_mesa.mp4", "vin": 1.5, "d": 2.5, "c": 0},
            {"t": "foto", "i": "f0012", "d": 6, "c": 0.9, "r": "fiel"},
            {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
            # SEM DURACAO ESCRITA o montar mede o ficheiro e mete-o inteiro a partir do
            # vin; a Mesa contava zero segundos e dizia que o filme era mais curto do que e.
            {"t": "video", "f": "meio_mesa.mp4", "d": 0, "c": 0},
            {"t": "foto", "i": "f0041", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        linhas, _som, _saida = _monta_em_pasta([dict(c) for c in clips], nome="mesavid")
        # O AVANCO REAL DE CADA CLIP, tirado das linhas que o montar escreveu: de onde este
        # comeca ate onde o seguinte comeca. O ultimo ocupa o seu tempo inteiro.
        avanco = [round(float(linhas[k + 1]["inicio_s"]) - float(linhas[k]["inicio_s"]), 2)
                  for k in range(len(linhas) - 1)]
        avanco.append(round(float(linhas[-1]["duracao_s"]), 2))
        # Os clips com o d que o montar mediu, que e o que a Mesa tem em rp depois de uma
        # montagem, e a mesma lista com um clip legado t:"fanfarra" a frente.
        rp = {str(k): {"d": round(float(l["duracao_s"]), 2)} for k, l in enumerate(linhas)}
        com_legado = [{"t": "fanfarra", "x": "", "d": 1, "c": 0}] + [dict(c) for c in clips]
        cabecalho = (js + "\nvar VIDS = %s;\nvar clips = %s, rp = %s, comLegado = %s;\n"
                     % (json.dumps([{"f": "meio_mesa.mp4", "dura": round(real, 2)},
                                    {"f": "fanfarra_mesa.mp4", "dura": round(real, 2)}]),
                        json.dumps(clips), json.dumps(rp), json.dumps(com_legado)))
        corpo_js = """
var v = {clips: clips}, vl = {clips: comLegado};
function tr(vin, d){ return trocoDoVideo({f: "meio_mesa.mp4", vin: vin, d: d}); }
function et(vin, d){ return etiquetaDoTroco({f: "meio_mesa.mp4", vin: vin, d: d}); }
process.stdout.write(JSON.stringify({
  avanco: clips.map(function(c, i){ return Math.round(duracaoNoTempo(v, i, rp) * 100) / 100; }),
  /* SEM MONTAGEM ANTERIOR (um clip acabado de juntar) a Mesa nao tem o rp e tem de contar
     pelo ficheiro, que e o que o montar vai fazer. */
  semRp: clips.map(function(c, i){ return Math.round(duracaoNoTempo(v, i, null) * 100) / 100; }),
  ocupa: clips.map(function(c, i){ return Math.round(ocupaNaLista(v, i) * 100) / 100; }),
  cross: clips.map(function(c, i){ return encadeadoDoClip(v, i); }),
  corpo: clips.map(function(c, i){ return videoNoCorpo(v, i); }),
  corpoLegado: comLegado.map(function(c, i){ return videoNoCorpo(vl, i); }),
  cabe: [tr(1.5, 2.5).cabe, tr(COMP_MENOS, 0.05).cabe, tr(0, COMP_MAIS).cabe],
  semD: et(1.5, 0)
}));
""".replace("COMP_MENOS", "%.2f" % round(real - 0.01, 2)) \
   .replace("COMP_MAIS", "%.2f" % round(real + 1.0, 2))
        caminho = os.path.join(pasta, "mesa_video.js")
        open(caminho, "w", encoding="utf-8").write(cabecalho + corpo_js)
        saida = None
        if not problemas:
            r = subprocess.run([node, caminho], capture_output=True, text=True,
                               encoding="utf-8", timeout=120)
            if r.returncode != 0:
                problemas.append("o node nao correu as contas da Mesa: %s" % r.stderr.strip()[:300])
            else:
                saida = json.loads(r.stdout)
        if saida:
            # 1. O AVANCO, clip a clip, igual ao do montar, com e sem montagem anterior.
            if [round(x, 2) for x in saida["avanco"]] != avanco:
                problemas.append("avanco da Mesa %s, do montar %s" % (saida["avanco"], avanco))
            if [round(x, 2) for x in saida["semRp"]] != avanco:
                problemas.append("sem montagem anterior a Mesa conta %s, o montar %s"
                                 % (saida["semRp"], avanco))
            # 2. QUEM ESTA NO CORPO: os dois videos do meio, e o clip legado nao muda a conta.
            corpo_esperado = [c["t"] == "video" and i > 0 for i, c in enumerate(clips)]
            if saida["corpo"] != corpo_esperado:
                problemas.append("videoNoCorpo: %s" % saida["corpo"])
            if saida["corpoLegado"][1] is not False:
                problemas.append("um video a seguir a um clip legado t:fanfarra ficou no corpo")
            if saida["corpoLegado"][6] is not True:
                problemas.append("com o clip legado a frente o video do meio saiu do corpo")
            # 3. O RELOGIO DA MESA: o tempo que cada clip ocupa e o encadeado com que entra.
            # O segundo contador continua o primeiro, logo entra a corte seco, e o video sem
            # duracao ocupa o comprimento do ficheiro.
            cross = [round(float(l["transicao_s"]), 2) for l in linhas]
            if [round(float(x), 2) for x in saida["cross"]] != cross:
                problemas.append("encadeados da Mesa %s, do montar %s" % (saida["cross"], cross))
            ocupa = [round(float(l["duracao_s"]) - float(l["transicao_s"]), 2) for l in linhas]
            if [round(x, 2) for x in saida["ocupa"]] != ocupa:
                problemas.append("o tempo de cada clip na Mesa %s, no montar %s"
                                 % (saida["ocupa"], ocupa))
            if abs(sum(saida["ocupa"]) - sum(ocupa)) > 0.05:
                problemas.append("o relogio do cabecalho da %.2f s e o filme %.2f s"
                                 % (sum(saida["ocupa"]), sum(ocupa)))
            # 3. A FOLGA DO "NAO CABE" E A DO MONTAR, 0,05 s.
            if not saida["cabe"][0]:
                problemas.append("um troco que cabe foi dado como fora do ficheiro")
            if not saida["cabe"][1]:
                problemas.append("a Mesa avisa «nao cabe» onde o montar nao corta nada")
            if saida["cabe"][2]:
                problemas.append("um troco de um segundo a mais do que o ficheiro passou")
            if saida["semD"] == "o ficheiro inteiro":
                problemas.append("com vin e sem duracao a etiqueta promete o ficheiro inteiro")
    finally:
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("Mesa e montar: o video do meio", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "avanco, tempo e encadeado iguais ao montar nos 10 clips, com e sem montagem feita")


def teste_contadores_seguidos_cortam_a_seco():
    """Dois contadores em que o segundo comeca onde o primeiro acabou entram com corte seco.

    CONTEUDO CONTINUO CORTA, e esta e a regra do CLAUDE.md que nasceu deste mesmo defeito:
    "na v3 apareciam dois '1995' sobrepostos a seguir ao SAPO". A intro de 17 de setembro
    acaba o contador de datas em 25/12/2025 e comeca o de anos em 2025 logo a seguir. Os
    dois desenhos sao quase iguais (mesmo fundo, mesma linha, numeros grandes quase a mesma
    altura) e com os 0,7 s de encadeado da omissao le-se, a meio da passagem, "25 DEZ 2025"
    com um segundo "2025" trinta por cento maior por cima, duas legendas empilhadas e duas
    reguas diferentes na mesma linha. Durante meio segundo ninguem le nada.

    Dois contadores de sitios DIFERENTES continuam a encadear: ai sao mesmo duas imagens
    diferentes, e a regra e a outra.
    """
    import montar_da_mesa
    problemas = []
    DATAS = "04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido"
    base = [
        {"t": "contador", "x": DATAS, "d": 9, "c": 0.7, "r": "fiel"},
        {"t": "contador", "x": "2025>1995|25 de dezembro de 2025", "d": 9, "c": 0.7, "r": "fiel"},
        {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
        {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"},
    ]
    linhas, _som, saida = _monta_em_pasta([dict(c) for c in base], nome="cont")
    if float(linhas[1]["transicao_s"]) != 0.0:
        problemas.append("o contador de anos a seguir ao de datas entrou com %s s de encadeado"
                         % linhas[1]["transicao_s"])
    if abs(float(linhas[1]["inicio_s"]) - float(linhas[0]["fim_s"])) > 0.001:
        problemas.append("o corte nao e seco: o segundo comeca aos %s e o primeiro acaba aos %s"
                         % (linhas[1]["inicio_s"], linhas[0]["fim_s"]))
    if "corte seco" not in saida:
        problemas.append("tirou o encadeado sem o dizer")
    if float(linhas[2]["transicao_s"]) != 0.7:
        problemas.append("o cartao a seguir perdeu o encadeado dele: %s" % linhas[2]["transicao_s"])
    # DOIS CONTADORES QUE NAO SE SEGUEM continuam a encadear: sao duas imagens diferentes.
    solto = [dict(c) for c in base]
    solto[1] = dict(solto[1], x="2011>2019|x")
    l2, _s2, _t2 = _monta_em_pasta(solto, nome="cont2")
    if float(l2[1]["transicao_s"]) != 0.7:
        problemas.append("dois contadores de sitios diferentes perderam o encadeado")
    # E A CONTA EM SI, nas combinacoes de datas e anos.
    casos = [("04/10/2026>25/12/2025|x", "2025>1995|x", True),
             ("04/10/2026>25/12/2025|x", "25/12/2025>01/01/2025|x", True),
             ("04/10/2026>25/12/2025|x", "24/12/2025>01/01/2025|x", False),
             ("2026>1995|x", "1995>2011|x", True),
             ("2026>1995|x", "2011>2019|x", False),
             ("2026>2025|x", "25/12/2025>01/01/2025|x", True),
             ("nao se le isto", "2025>1995|x", False)]
    for a, b, esperado in casos:
        if montar_da_mesa.contadores_seguidos(a, b) != esperado:
            problemas.append("%r -> %r devia dar %s" % (a[:18], b[:18], esperado))
    verifica("contadores seguidos cortam a seco", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "o de anos entra a corte seco a seguir ao de datas, e os soltos encadeiam")


def teste_gerar_mesa_oferece_o_que_o_montar_resolve():
    """Tudo o que a Mesa oferece nas listas tem de ser encontrado por quem monta o filme.

    O window.VIDEOS e o window.VOZES sao a porta de entrada dos videos do corpo e das vozes
    do pedido: e dali que sai o nome que fica escrito no clip e o comprimento com que o
    inspetor diz «o troco nao cabe». O gerar_mesa.py nao tinha UM UNICO teste. Bastava
    trocar o -show_entries do ffprobe, enganar-se numa extensao aceite, ou deixar de juntar
    a render.VIDEOS a pasta 03-NOVOS_VIDEOS, para a lista sair vazia ou com as duracoes a
    zero, e a suite inteira continuava verde: so se descobria ao abrir a Mesa publicada, com
    ele do outro lado sem conseguir escolher o video.

    Noutro PC, sem as pastas do media, nao ha o que comparar, e isso conta-se como saltado.
    """
    import gerar_mesa
    import montar_da_mesa
    problemas = []
    tem_videos = os.path.isdir(gerar_mesa.VIDEOS_NOVOS)
    tem_vozes = os.path.isdir(gerar_mesa.VOZES)
    if not tem_videos and not tem_vozes:
        salta("Mesa: as listas de videos e de vozes", "sem as pastas do media neste PC")
        return
    videos, vozes = gerar_mesa.videos_do_projeto(), gerar_mesa.vozes_do_pedido()
    if tem_videos and not videos:
        problemas.append("a pasta dos videos existe e a lista da Mesa saiu vazia")
    if tem_vozes and not vozes:
        problemas.append("a pasta dos pedacos existe e a lista das vozes saiu vazia")
    for v in videos:
        if not v.get("dura"):
            problemas.append("video %s oferecido com 0 s" % v["f"])
        if not montar_da_mesa.caminho_do_video(v["f"]):
            problemas.append("video %s oferecido na Mesa e o montar nao o encontra" % v["f"])
            continue
        real = montar_da_mesa.duracao_do_video(v["f"])
        if real is None or abs(real - v["dura"]) > 0.05:
            problemas.append("video %s: a Mesa diz %s s e o montar mede %s"
                             % (v["f"], v["dura"], real))
    # E O QUE JA ESTA NAS MONTAGENS TEM DE ESTAR NA LISTA. E por ela que o inspetor sabe o
    # comprimento do ficheiro e diz se o troco cabe; um video que o montar encontra e que a
    # Mesa nao oferece aparece-lhe com o aviso "nao esta nas pastas dos videos", que e um
    # aviso a mentir. E onde se apanha a lista que deixe de juntar a tabela do render a
    # pasta 03-NOVOS_VIDEOS: a intro da historia da Clara vive na pasta de saida.
    oferecidos = {v["f"] for v in videos}
    pasta_m = os.path.join(REPO, "data", "montagens")
    usados = set()
    for f in sorted(os.listdir(pasta_m)) if os.path.isdir(pasta_m) else []:
        if not f.endswith(".csv") or f.endswith(".som.csv"):
            continue
        with open(os.path.join(pasta_m, f), encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("tipo") == "video" and (r.get("ficheiro") or "").strip():
                    usados.add(r["ficheiro"].strip())
    for nome in sorted(usados):
        if montar_da_mesa.caminho_do_video(nome) and nome not in oferecidos:
            problemas.append("o video %s esta numa montagem e a Mesa nao o oferece" % nome)
    # A MARCA `novo` TEM DE QUERER DIZER O QUE DIZ. Desde 22 de setembro a lista traz tambem
    # os videos que estao na 01-NOVAS e que ele ainda nao decidiu (decisao 082, ponto 2): a
    # Mesa mostra-os num painel proprio e NAO os oferece no campo do ficheiro, porque quem os
    # poe no filme e ele, pelo chat. Um marcado tem de estar debaixo da 01-NOVAS e nao pode
    # estar em nenhuma montagem; assim que eu o montar, a marca cai sozinha e ele volta a ser
    # oferecido. Foi por isto que o numero desta linha subiu de 16 para 22 videos.
    for v in videos:
        if not v.get("novo"):
            continue
        caminho = montar_da_mesa.caminho_do_video(v["f"]) or ""
        if gerar_mesa.VIDEOS_POR_DECIDIR.lower() not in caminho.lower():
            problemas.append("o video %s esta marcado por decidir e nao esta na 01-NOVAS" % v["f"])
        if v["f"] in usados:
            problemas.append("o video %s ja esta numa montagem e continua marcado por decidir" % v["f"])
    # E A MESA NAO OS PODE OFERECER NO CAMPO DO FICHEIRO. Isso so se ve no browser, por isso
    # prende-se pelo texto, como as outras guardas da Mesa que nao correm no node.
    html_mesa = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    if "vidsParaEscolher(nome).map(" not in html_mesa:
        problemas.append("o campo do ficheiro do video voltou a oferecer a lista VIDS inteira")
    caminhos_voz = montar_da_mesa.caminhos_de_voz()
    for z in vozes:
        if not z.get("dura"):
            problemas.append("voz %s oferecida com 0 s" % z["f"])
        real_nome = montar_da_mesa.resolve_musica(z["f"], caminhos_voz)
        if not real_nome:
            problemas.append("voz %s oferecida na Mesa e o montar nao a resolve" % z["f"])
            continue
        d = montar_da_mesa.duracao_de_audio(caminhos_voz[real_nome])
        if d is None or abs(d - z["dura"]) > 0.05:
            problemas.append("voz %s: a Mesa diz %s s e o montar mede %s" % (z["f"], z["dura"], d))
    verifica("Mesa: as listas de videos e de vozes", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "%d videos (%d por decidir na 01-NOVAS) e %d vozes, todos resolvidos e com a "
             "duracao a bater" % (len(videos), len([v for v in videos if v.get("novo")]), len(vozes)))


def teste_mesa_marca_o_texto_que_passa_depressa():
    """O tempo sozinho com que a Mesa marca um texto e o mesmo que o render da ao clip.

    O PEDIDO, do Tiago a 22 de setembro (decisao 082, ponto 4): "podes deixar uma pequena
    mencao com um icon por exemplo na mesa e assim eu edito. Depois antes de fazer render
    podes perguntar-me se devem ficar". A Mesa marca, ele edita, ninguem corrige por ele.

    PORQUE E QUE ISTO PRECISA DE TESTE. A conta do tempo sozinho ja tem QUATRO copias neste
    projecto, e uma delas esta errada: a coluna `solo_s` dos CSV e `dur - 2 x o encadeado do
    PROPRIO clip`, e o render usa o encadeado do proprio a entrar e o do clip SEGUINTE a sair.
    Nos 200 clips do corpo da v3 as duas dao numeros diferentes em 8. Ninguem le a coluna, so
    se escreve, por isso hoje nao faz mal a ninguem e fica como esta (mexer-lhe partia o
    teste_v3_sem_vozes_igual_ao_byte, que congela o ficheiro byte a byte). Mas se a Mesa
    tivesse copiado ESSA conta, marcava clips que estao bem e deixava passar os que nao estao,
    e o Tiago cortava palavras onde nao era preciso. E o mesmo defeito das tres copias da regra
    do upscaling, onde a que fazia o video era a que estava por corrigir.

    O NUMERO DE LETRAS POR SEGUNDO TAMBEM SE PRENDE: 12 nao e um palpite, e o XF_LONGO = 32 (o
    maximo ja declarado legivel a 15 metros, decisao 003) dentro dos 2,6 s que um clip corrente
    de fotos tem sozinho, 4 s com 0,7 s de encadeado de cada lado. Quem mexer num tem de mexer
    no outro, e e isso que aqui se verifica.

    Corre no node sobre as montagens verdadeiras, em data/montagens. Sem node, diz-se e nao conta.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import render
    node = shutil.which("node")
    if not node:
        salta("Mesa: o texto que passa depressa de mais", "sem node neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []
    marcas = ["var MONTE = ", "function s1(", "function eGrupo(", "function clipsDoCorpo(",
              "function encadeadoDoClip(", "function encadeadosDe(", "function videoNoCorpo(",
              "function pecaDoVideo(", "function duraDoVideo(", "function trocoDoVideo(",
              "function duracaoDoVideoNoFilme(", "function duracaoDoClip(",
              "function contadoresSeguidos(", "function pontoDoContador(", "function lerContador(",
              "function eDataContador(", "function dataParaIso(", "function d2(",
              "function modoTextos(", "function tamanhoValido(",
              # A DURACAO COM QUE O RENDER DESENHA, que o montar estica no cartao de um
              # nascimento. Sem estas quatro o sozinhoNoEcra() usava so o numero escrito na
              # Mesa e o validador marcava um cartao que esta bem: ver o caso "esticado".
              "function chaveDoClipBase(", "function chavesDaVersao(", "function srDaVersao(",
              "function renderPorClip(", "function duracaoNoRender(",
              "function sozinhoNoEcra(", "function textoNoEcraDoClip(", "function corridaDoTexto(",
              "function textoDenso("]
    js = "\n".join(_bloco_do_editor(html, m, problemas) for m in marcas)
    xf_cps = _numero_do_editor(html, "XF_CPS", problemas)
    xf_longo = _numero_do_editor(html, "XF_LONGO", problemas)
    # SR = null e o caso de sempre: sem SOM_RENDER, ou numa versao que nao e a da ultima
    # montagem, a duracao e a que ele escreveu. O caso "esticado" abaixo poe-lhe um valor.
    js = ("var XF_CPS = %s, XF_LONGO = %s, TT_OMISSAO = 46, TT_MIN = 28, TT_MAX = 90, "
          "VIDS = [], SR = null;\n" % (xf_cps, xf_longo)) + js

    # 1. O LIMITE AMARRADO AO QUE JA EXISTE. O clip corrente de fotos, 4 s com 0,7 s de cada lado.
    if xf_cps is not None and xf_longo is not None:
        esperado = int(xf_longo / (4.0 - 0.7 - 0.7))
        if int(xf_cps) != esperado:
            problemas.append("XF_CPS e %s e XF_LONGO = %s no clip corrente pede %s"
                             % (xf_cps, xf_longo, esperado))

    # 2. AS MONTAGENS VERDADEIRAS. Os clips vao com a duracao e o encadeado que o montar
    # escreveu; sem lista de videos o duracaoDoClip() da Mesa devolve o que la esta escrito,
    # que e exactamente o que o render leu do ficheiro quando montou.
    pasta_m = os.path.join(REPO, "data", "montagens")
    montagens, esperado_solo, solo_csv = {}, {}, {}
    for f in sorted(os.listdir(pasta_m)) if os.path.isdir(pasta_m) else []:
        if not f.endswith(".csv") or f.endswith(".som.csv"):
            continue
        with open(os.path.join(pasta_m, f), encoding="utf-8-sig", newline="") as fh:
            linhas = list(csv.DictReader(fh))
        if not linhas:
            continue
        nome = f[:-4]
        montagens[nome] = [{"t": r["tipo"], "x": r.get("texto_ecra") or "",
                            "d": float(r["duracao_s"] or 0), "c": float(r["transicao_s"] or 0)}
                           for r in linhas]
        inicio, _resto = render.partir_em_fanfarra_e_corpo([{"tipo": r["tipo"]} for r in linhas])
        corpo = linhas[len(inicio):]
        pares = render.encadeados_do_corpo([{"transicao_s": r["transicao_s"]} for r in corpo])
        solo = []
        for k, r in enumerate(linhas):
            if k < len(inicio):
                solo.append(round(float(r["duracao_s"] or 0), 4))   # bloco inicial: corte seco
            else:
                entra, sai = pares[k - len(inicio)]
                solo.append(round(max(0.0, float(r["duracao_s"] or 0) - entra - sai), 4))
        esperado_solo[nome] = solo
        solo_csv[nome] = [(float(r["solo_s"]) if (r.get("solo_s") or "").strip() else None)
                          for r in linhas]

    # 3. E CASOS A MAO para as fronteiras que as montagens nao tem: o texto que cabe, o que
    # nao cabe por pouco, e a corrida de clips com o mesmo texto, que e UM texto no ecra.
    mao = [
        # nome, clips, indice, marcado?
        ["cabe", [{"t": "foto", "x": "Em Barcelona", "d": 4, "c": 0.7},
                  {"t": "foto", "x": "b", "d": 4, "c": 0.7},
                  {"t": "foto", "x": "c", "d": 4, "c": 0.7}], 1, False],
        ["nao cabe", [{"t": "foto", "x": "a", "d": 4, "c": 0.7},
                      {"t": "foto", "x": "Durante este periodo tambem o Tiago comprou o primeiro carro",
                       "d": 4, "c": 0.7},
                      {"t": "foto", "x": "c", "d": 4, "c": 0.7}], 1, True],
        # a mesma legenda em quatro fotos de rajada: o encadeado mistura duas copias iguais,
        # logo le-se durante os quatro, e so o primeiro leva o sinal
        ["corrida, o primeiro", [{"t": "foto", "x": "a", "d": 4, "c": 0.7}] +
            [{"t": "foto", "x": "Caminhadas pelo Parque das Serras", "d": 2, "c": 0.4}] * 4 +
            [{"t": "foto", "x": "z", "d": 4, "c": 0.7}], 1, False],
        ["corrida, o do meio", [{"t": "foto", "x": "a", "d": 4, "c": 0.7}] +
            [{"t": "foto", "x": "Caminhadas pelo Parque das Serras", "d": 2, "c": 0.4}] * 4 +
            [{"t": "foto", "x": "z", "d": 4, "c": 0.7}], 3, False],
        # sozinho um deles nao chegava: 33 letras em 1,6 s
        ["um so da corrida", [{"t": "foto", "x": "a", "d": 4, "c": 0.7},
                              {"t": "foto", "x": "Caminhadas pelo Parque das Serras", "d": 2, "c": 0.4},
                              {"t": "foto", "x": "z", "d": 4, "c": 0.7}], 1, True],
        # um contador nao se marca: o x dele e instrucao em bruto e ninguem a le no ecra
        ["contador", [{"t": "foto", "x": "a", "d": 4, "c": 0.7},
                      {"t": "contador", "x": "04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido",
                       "d": 4, "c": 0.7},
                      {"t": "foto", "x": "z", "d": 4, "c": 0.7}], 1, False],
    ]

    pasta = tempfile.mkdtemp(prefix="teste_mesa_denso_")
    saida = None
    try:
        programa = js + "\nvar MONT = %s, MAO = %s;\n" % (
            json.dumps(montagens, ensure_ascii=False),
            json.dumps([m[1] for m in mao], ensure_ascii=False)) + """
var solo = {};
Object.keys(MONT).forEach(function(nome){
  var v = {clips: MONT[nome]};
  solo[nome] = v.clips.map(function(_c, i){ return Math.round(sozinhoNoEcra(v, i) * 10000) / 10000; });
});
process.stdout.write(JSON.stringify({
  solo: solo,
  /* quantos e que cada montagem marca hoje: nao e uma condicao, e o numero que eu leio para
     lhe perguntar antes do render */
  densos: Object.keys(MONT).map(function(nome){
    var v = {clips: MONT[nome]}, n = 0;
    v.clips.forEach(function(_c, i){ var d = textoDenso(v, i); if(d && d.demais && d.primeiro) n++; });
    return [nome, n];
  }),
  mao: MAO.map(function(clips, k){
    var v = {clips: clips}, d = textoDenso(v, [1, 1, 1, 3, 1, 1][k]);
    return d ? {demais: d.demais, primeiro: d.primeiro, letras: d.letras,
                sozinho: Math.round(d.sozinho * 100) / 100} : null;
  }),
  /* O CARTAO QUE O MONTAR ESTICA. O mesmo clip, duas vezes: com a duracao que ele escreveu
     e com a que o render desenha. O segundo nao se marca. */
  esticado: (function(){
    var CARTAO = "2 meses e 12 dias depois a poucos kms, nasce uma bebé";
    var clips = [{t: "foto", x: "a", d: 4, c: 0.7},
                 {t: "cartao", x: CARTAO, d: 3.6, c: 0.7},
                 {t: "foto", x: "z", d: 4, c: 0.7}];
    var v = {id: "ensaio", clips: clips};
    var sem = textoDenso(v, 1);
    SR = {versao: "ensaio", faixas: [], clips: [
      {chave: "foto:#1", d: 4}, {chave: "cartao:" + CARTAO + "#1", d: 6.15},
      {chave: "foto:#2", d: 4}]};
    var com = textoDenso(v, 1);
    SR = null;
    return {sem: {demais: sem.demais, sozinho: Math.round(sem.sozinho * 100) / 100},
            com: {demais: com.demais, sozinho: Math.round(com.sozinho * 100) / 100}};
  })()
}));
"""
        caminho = os.path.join(pasta, "mesa_denso.js")
        open(caminho, "w", encoding="utf-8").write(programa)
        if not problemas:
            r = subprocess.run([node, caminho], capture_output=True, text=True,
                               encoding="utf-8", timeout=180)
            if r.returncode != 0:
                problemas.append("o node nao correu as contas da Mesa: %s" % r.stderr.strip()[:300])
            else:
                saida = json.loads(r.stdout)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    clips_vistos, divergem_do_csv = 0, 0
    if saida:
        for nome in sorted(esperado_solo):
            veio, era = saida["solo"].get(nome), esperado_solo[nome]
            if veio is None:
                problemas.append("a Mesa nao deu o tempo sozinho da montagem %s" % nome)
                continue
            for k, (a, b) in enumerate(zip(veio, era)):
                clips_vistos += 1
                if abs(a - b) > 0.005:
                    problemas.append("%s clip %d: a Mesa da %.3f s sozinho e o render %.3f s"
                                     % (nome, k + 1, a, b))
                    break
            # SO PARA SE VER QUE O TESTE TEM DENTES: a coluna solo_s do CSV, que e a quarta
            # copia da regra, nao da o mesmo numero em todos os clips.
            for a, b in zip(solo_csv[nome], era):
                if a is not None and abs(a - b) > 0.005:
                    divergem_do_csv += 1
        for (nome, clips, i, marcado), veio in zip(mao, saida["mao"]):
            if nome == "contador":
                if veio is not None:
                    problemas.append("a Mesa marcou o texto em bruto de um contador")
                continue
            if veio is None:
                problemas.append("caso %r: a Mesa nao viu texto nenhum" % nome)
            elif veio["demais"] != marcado:
                problemas.append("caso %r: a Mesa %s (%s letras em %s s)"
                                 % (nome, "marcou" if veio["demais"] else "nao marcou",
                                    veio["letras"], veio["sozinho"]))
            elif nome == "corrida, o do meio" and veio["primeiro"]:
                problemas.append("na corrida com o mesmo texto o clip do meio abria a corrida")
        # O CARTAO QUE O MONTAR ESTICA. Com a duracao escrita na Mesa (3,6 s) o cartao do
        # nascimento da Clara nao cabe, e era isso que o validador lhe dizia; com a que o
        # render desenha (6,15 s) cabe, e e essa que manda. Foi um verificador que apanhou
        # este falso positivo a 22 de setembro.
        est = saida.get("esticado") or {}
        if not est.get("sem", {}).get("demais"):
            problemas.append("o cartao do nascimento com 3,6 s devia ser marcado e nao foi")
        if est.get("com", {}).get("demais"):
            problemas.append("o cartao do nascimento com a duracao esticada do render "
                             "(%.2f s sozinho) continua marcado"
                             % est.get("com", {}).get("sozinho", 0))
    marcados = sum(n for _nome, n in (saida or {}).get("densos", []))
    verifica("Mesa: o texto que passa depressa de mais", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "%d clips de %d montagens com o tempo sozinho do render (a coluna solo_s difere em %d), "
             "XF_CPS %g de XF_LONGO %g, %d textos marcados, e os 6 casos a mao"
             % (clips_vistos, len(esperado_solo), divergem_do_csv, xf_cps or 0, xf_longo or 0,
                marcados))


def teste_validador_apanha_o_emoji_e_os_erros_de_escrita():
    """As regras do validador da Mesa apanham o que ja esta la e nao acusam o que esta bem.

    O PEDIDO, do Tiago a 22 de setembro (decisao 082, ponto 5): "Isso e um validador no final.
    Podes meter na mesa um validador que e acionado se eu carregar no botao".

    O DEFEITO QUE ISTO GUARDA E O DO EMOJI. A Pillow desenha o .notdef sem se queixar: um
    caracter que a Arial a negrito nao tem sai RECTANGULO VAZIO no video e nao ha aviso nenhum,
    nem no render nem em lado nenhum. O clip 94 da demo_v3 tem um, e passava projectado no meio
    do jantar. A regra da Mesa e positiva (o que a Arial garante) e nao uma lista negra de
    emojis, que envelhecia; por isso o que aqui se mede e se a regra da Mesa CONCORDA COM A
    PILLOW, letra a letra, sobre a mesma letra que o render usa (render.FONTE_TEXTO).

    E os erros de escrita: a proposta e construida a partir do texto inteiro e nao do pedaco
    apanhado, senao o par do "12ºano" propunha "2º" para "2º", porque a letra que vem a seguir
    nao esta no pedaco.

    Corre no node. Sem node, diz-se e nao conta.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    from PIL import ImageDraw, ImageFont
    import render
    node = shutil.which("node")
    if not node:
        salta("Mesa: o validador", "sem node neste PC")
        return
    if not os.path.exists(render.FONTE_TEXTO):
        salta("Mesa: o validador", "sem a letra do render neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []
    regras = _regiao_do_editor(html, "/* <<< REGRAS PURAS DO VALIDADOR, PRINCIPIO >>> */",
                               "/* <<< REGRAS PURAS DO VALIDADOR, FIM >>> */", problemas)
    apoio = "\n".join(_bloco_do_editor(html, m, problemas) for m in
                      ("function eGrupo(", "function modoTextos(", "function tamanhoValido(",
                       "function textosDasFotos(", "function temTextosFotos("))
    js = ("var TT_OMISSAO = 46, TT_MIN = 28, TT_MAX = 90;\n"
          "var MUS = [\"Lang Lang - Beauty and the Beast (From Lang Lang Plays Disney  Live).mp3\",\n"
          "           \"Inês Homem de Melo – Fome de Viagem (Music Video).mp3\"];\n") + apoio + "\n" + regras

    # 1. O QUE TEM DE APANHAR, e como. Todos vieram do estado de 22 de setembro.
    escrita = [
        ("Hiratação obrigatóra pós corrida", [("Hiratação", "Hidratação"), ("obrigatóra", "obrigatória")]),
        ("Em barcelona", [("barcelona", "Barcelona")]),
        ("Baile Finalistas 12ºano (2013)", [("12ºano", "12.º ano")]),
        ("Na Alemanha. Em Dinkelsbuhl;", [("Dinkelsbuhl;", "Dinkelsbühl;")]),
        ("Com a mae e com a avo", [("mae", "mãe"), ("avo", "avó")]),
        ("Não incluindo ainda no sitio certo", [("sitio", "sítio")]),
        # e o que NAO se toca: as mesmas palavras ja escritas como devem ser
        ("Hidratação obrigatória pós corrida", []),
        ("Em Barcelona", []),
        ("Baile Finalistas 12.º ano (2013)", []),
        ("Na Alemanha. Em Dinkelsbühl", []),
        ("Com a mãe e com a avó", []),
        ("Com o avô, à beira-mar", []),
    ]
    sinais = [
        ("Orgulhosa do primeiro automóvel. ", ["erro"]),
        ("o resto normalmente....", ["erro"]),
        ("Na Croácia .", ["erro"]),
        ("Em Sintra / Em Setúbal", ["confirma"]),
        ("Na Alemanha. Em Dinkelsbuhl;", ["confirma"]),
        ("Em Barcelona", []),
        ("24/08 abre o SAPO", []),          # a barra sem espacos nao e duas legendas juntas
    ]
    # 2. A LETRA: cada caracter que ja esta em texto de ecra, mais uma mao cheia de casos de
    # fronteira. O esperado vem da Pillow, com a letra que o render usa.
    estado = os.path.join(REPO, "data", "mesa_estado.json")
    letras = set(" .,;:!?'\"()-–—…/&@#%€$ªº+*=<>|_~^`0123456789")
    letras |= set("AaÀàÁáÂâÃãÇçÉéÊêÍíÓóÔôÕõÚúÜüÑñŁłČčŠšŽžØøÅå")
    letras |= set("😮🎉❤")
    if os.path.exists(estado):
        with open(estado, encoding="utf-8") as fh:
            est = json.load(fh)
        for v in est.get("versoes", []):
            for c in v.get("clips", []):
                if c.get("t") in ("contador", "marcos"):
                    continue
                for t in [c.get("x")] + list(c.get("xf") or []):
                    if isinstance(t, str):
                        letras |= set(t)
    letras = sorted(letras)

    fonte = ImageFont.truetype(render.FONTE_TEXTO, 46)

    def _desenha(ch):
        im = Image.new("L", (110, 110), 0)
        ImageDraw.Draw(im).text((5, 5), ch, font=fonte, fill=255)
        return im.tobytes()

    # O .notdef, desenhado a partir de um ponto de codigo de uso privado que nenhuma letra
    # tem. Um caracter que saia igual a isto e um rectangulo vazio no video.
    sem_glifo = _desenha("")
    pillow_nao_desenha = {ch for ch in letras if _desenha(ch) == sem_glifo}

    musicas = [("Lang Lang - Beauty and the Beast (From Lang Lang Plays Disney  Live)", True),
               ("Inês Homem de Melo – Fome de Viagem (Music Video).mp3", True),
               ("lang lang - beauty and the beast (from lang lang plays disney  live).MP3", True),
               ("", True),
               ("Uma que não existe.mp3", False)]
    recados = [("Vai ser para o fecho se usar o heli no fim", True),
               ("Não incluindo ainda no sitio certo", True),
               ("Em Barcelona", False)]

    pasta = tempfile.mkdtemp(prefix="teste_validador_")
    saida = None
    try:
        programa = js + "\nvar ESCRITA = %s, SINAIS = %s, LETRAS = %s, MUSICAS = %s, RECADOS = %s;\n" % (
            json.dumps([e[0] for e in escrita], ensure_ascii=False),
            json.dumps([s[0] for s in sinais], ensure_ascii=False),
            json.dumps(letras, ensure_ascii=False),
            json.dumps([m[0] for m in musicas], ensure_ascii=False),
            json.dumps([r[0] for r in recados], ensure_ascii=False)) + """
process.stdout.write(JSON.stringify({
  escrita: ESCRITA.map(function(t){
    return errosDeEscrita(t).map(function(e){ return [e.achou, e.certo]; }); }),
  sinais: SINAIS.map(function(t){
    return sinaisDoTexto(t).map(function(s){ return s.grau; }); }),
  fora: LETRAS.map(function(ch){ return forasDaLetra(ch).length > 0; }),
  /* UM EMOJI CONTA UMA VEZ. Sao dois pedacos de texto em JavaScript, e sem o salto do par
     substituto a mensagem saia com dois rectangulos partidos em vez de um caracter. */
  emojiNoTexto: forasDaLetra("O pai ficou assim 😮 quando soube do preço"),
  musicas: MUSICAS.map(musicaConhecida),
  recados: RECADOS.map(eRecado),
  /* o texto de ecra e o de cada foto de um grupo, EM BRUTO: o espaco nas pontas so se ve
     assim, e por isso o textosDoClip nao pode aparar nada ao recolher */
  textos: textosDoClip({t: "colagem", x: " Viagens ", fotos: [1, 2], vf: true,
                        xf: [" Nos Açores", ""]})
}));
"""
        caminho = os.path.join(pasta, "validador.js")
        open(caminho, "w", encoding="utf-8").write(programa)
        if not problemas:
            r = subprocess.run([node, caminho], capture_output=True, text=True,
                               encoding="utf-8", timeout=120)
            if r.returncode != 0:
                problemas.append("o node nao correu as regras do validador: %s" % r.stderr.strip()[:300])
            else:
                saida = json.loads(r.stdout)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    if saida:
        for (texto, era), veio in zip(escrita, saida["escrita"]):
            if sorted(tuple(x) for x in veio) != sorted(era):
                problemas.append("escrita em %r: o validador diz %s, esperado %s"
                                 % (texto[:40], veio, era))
        for (texto, era), veio in zip(sinais, saida["sinais"]):
            if sorted(veio) != sorted(era):
                problemas.append("sinais em %r: o validador diz %s, esperado %s"
                                 % (texto[:40], veio, era))
        marcados = {ch for ch, mau in zip(letras, saida["fora"]) if mau}
        # A. O QUE A PILLOW NAO DESENHA TEM DE SER MARCADO. E a direccao que importa: um
        # caracter sem glifo sai rectangulo vazio no video, e ninguem avisa.
        for ch in sorted(pillow_nao_desenha - marcados)[:6]:
            problemas.append("a Arial nao desenha %r e a Mesa deixa passar" % ch)
        # B. E O QUE A MESA MARCA TEM MESMO DE FALTAR. Um validador que grita por letras que
        # a Arial desenha bem (os acentos, o euro, o travessao) nao se volta a abrir.
        for ch in sorted(marcados - pillow_nao_desenha)[:6]:
            problemas.append("a Mesa marca %r e a Arial desenha-o bem" % ch)
        if "\U0001F62E" not in marcados:
            problemas.append("o emoji do clip 94 da demo_v3 passou pelo validador")
        if saida["emojiNoTexto"] != ["\U0001F62E"]:
            problemas.append("o emoji dentro de uma frase saiu como %s, esperado um caracter so"
                             % (saida["emojiNoTexto"],))
        for (nome, era), veio in zip(musicas, saida["musicas"]):
            if veio != era:
                problemas.append("a musica %r deu %s, esperado %s" % (nome[:40], veio, era))
        for (texto, era), veio in zip(recados, saida["recados"]):
            if veio != era:
                problemas.append("o recado %r deu %s, esperado %s" % (texto[:40], veio, era))
        if saida["textos"] != [["texto no ecrã", " Viagens "], ["texto da foto 1", " Nos Açores"]]:
            problemas.append("os textos do clip vieram aparados ou em falta: %s" % (saida["textos"],))
    verifica("Mesa: o validador", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "%d caracteres conferidos com a Pillow (%d sem glifo, o emoji incluido), "
             "%d textos de escrita, %d de sinais" % (len(letras), len(pillow_nao_desenha),
                                                     len(escrita), len(sinais)))


# O QUE O montar_da_mesa.py LE DE UM CLIP, e com que nome isso sai no botao «Ordens para o
# Claude». A esquerda estao os campos do estado da Mesa, a direita a chave do JSON. Um campo
# novo no montar entra aqui e no exportar() da Mesa, ou o teste falha: foi assim que vin, vz,
# vzm, e, estilo e m ficaram de fora sem ninguem dar por isso.
CAMPOS_EXPORTADOS = {
    "t": "tipo", "f": "ficheiro", "i": "id", "x": "texto", "d": "duracao_s", "c": "cross_s",
    "r": "tratamento", "fotos": "fotos", "lay": "disposicao", "e": "enquadramento",
    # o zoom do fim do «aproxima», 18 de setembro, que a Mesa exporta ja resolvido
    "az": "zoom_final",
    "estilo": "estilo", "m": "musica", "vin": "vin", "vz": "vozes", "vzm": "musica_por_baixo",
    # os textos de cada foto e as suas opcoes saem ja tratados, nao em bruto
    "xf": "textos_fotos", "vf": "textos_opcoes", "vm": "textos_opcoes",
    "tt": "textos_opcoes", "vt": "textos_opcoes",
}


def teste_mesa_exporta_os_campos_do_montar():
    """O botao «Ordens para o Claude» leva tudo o que o montar_da_mesa.py le de um clip.

    O DEFEITO: o exportar() montava o objeto com uma lista fixa de campos, escrita quando
    havia menos, e cada campo novo ficou para tras. A 17 de setembro o clip do Homer saia
    {tipo:"video", ficheiro:"...", duracao_s:3.5, cross_s:0, tratamento:"fiel"} e mais nada:
    sem o vin, ou seja a comecar no segundo 0, que e outro «D'oh» ou nenhum; e a foto das
    vozes saia sem vz e sem vzm, ou seja muda. Ja antes desta ronda faltavam o enquadramento,
    o estilo e a musica marcada. Quem reconstruisse a montagem a partir desse texto perdia
    tudo isso sem um aviso em lado nenhum.
    """
    problemas = []
    fonte = open(os.path.join(REPO, "scripts", "montar_da_mesa.py"), encoding="utf-8").read()
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    lidos = set(re.findall(r'\bc\.get\("([A-Za-z_]+)"', fonte))
    novos = lidos - set(CAMPOS_EXPORTADOS)
    if novos:
        problemas.append("o montar le campos que a tabela nao conhece: %s; poe-os no "
                         "exportar() da Mesa e aqui" % ", ".join(sorted(novos)))
    # O objeto de cada clip vive no ordemDoClip() desde 18 de setembro, para o teste da Mesa
    # o poder correr no node; o exportar() chama-o.
    bloco = _bloco_do_editor(html, "function exportar(", problemas) + \
        _bloco_do_editor(html, "function ordemDoClip(", problemas)
    if "ordemDoClip(v, c, i)" not in _bloco_do_editor(html, "function exportar(", problemas):
        problemas.append("o exportar() deixou de chamar o ordemDoClip()")
    for campo in sorted(lidos & set(CAMPOS_EXPORTADOS)):
        chave = CAMPOS_EXPORTADOS[campo]
        if chave + ":" not in bloco:
            problemas.append("o campo %s (que o montar le) nao sai no exportar() como %s"
                             % (campo, chave))
    verifica("a Mesa exporta os campos que o montar le", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "%d campos do montar, todos no botao das ordens" % len(lidos))


def teste_mesa_aproxima_diz_o_que_o_render_faz():
    """O que a Mesa diz do aproxima e o que o render faz: o travao, o zoom que centra, a zona e o palco.

    O DEFEITO, medido pelo verificador a 18 de setembro: sete mutacoes no codigo novo da Mesa
    passavam a suite inteira. O travao desligado (a Mesa deixava de dizer que o anel nao fica
    ao centro a 2,2), a janela do fim a sair da foto, o palco a mostrar o principio em vez do
    fim, o aviso de foco em falta, as ordens sem o zoom, o poeAz sem trava e a opcao fora da
    lista. A copia a mao das funcoes que o construtor corria no node vivia no scratchpad.

    Corre no node as funcoes recortadas do proprio editor_base.html, numa grelha de fotos,
    pontos de foco e zooms, e compara com as contas do render: aproxima_centro(),
    aproxima_zoom_que_centra() e aproxima_zoom_sugerido(). O palco mede-se em janelas com
    outras formas, porque a zona que ele mostra tem de ser a do ecra 16:9 do filme, e o
    Tiago decide a partir do telemovel. Sem node, diz-se e nao conta.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import render
    node = shutil.which("node")
    if not node:
        salta("Mesa e render: o aproxima", "sem node neste PC")
        return
    html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
    problemas = []
    marcas = ["function s1(", "function az1(", "function azLido(", "function azRecusado(",
              "function azDe(", "function poeAz(", "function aproximaAtivo(",
              "function avisoDoEnquadramento(", "function zonaAproxima(", "function travaAproxima(",
              "function zoomQueCentra(", "function notaTravaoAproxima(", "function aproximaNoPalco(",
              "function ordemDoClip(", "function videoNoCorpo(",
              "function vozesDe(", "function temVozes(", "function musicaDasVozes(",
              "function eGrupo(", "function focoDe("]
    constantes = []
    for padrao in (r"var APROXIMA_OMISSAO = [^;]*;", r"var APROXIMA_SOBRA = [^;]*;",
                   r"var OPCOES_ENQUADRAMENTO = \[.*?\]\];"):
        achados = re.findall(padrao, html, re.S)
        if len(achados) != 1:
            problemas.append("%r aparece %d vezes no editor_base.html" % (padrao[:30], len(achados)))
        constantes += achados[:1]
    if "OPCOES_ENQUADRAMENTO.map(" not in html:
        problemas.append("a escolha do Enquadramento deixou de usar OPCOES_ENQUADRAMENTO")
    bloco_enq = html[html.find('liga("cEnq"'):html.find('liga("cEnq"') + 900]
    if "avisoDoEnquadramento(c)" not in bloco_enq:
        problemas.append("ao escolher o enquadramento a Mesa deixou de chamar o avisoDoEnquadramento()")
    # O QUE SO O BROWSER MOSTRA, e que o node nao corre: preso aqui pelo texto, porque cada
    # um foi medido a falhar no browser pelo verificador a 18 de setembro.
    #   - o scroll anchoring descia o inspetor a cada clique no ponto de foco, e o segundo
    #     clique no mesmo sitio marcava outro ponto da foto;
    #   - marcar o foco nao repintava a lista, e a etiqueta do aproxima ficava errada;
    #   - o campo do zoom era number, e num browser em ingles "2,6" chegava como 26;
    #   - mudar o zoom nao entrava no anular, e o Ctrl+Z levava o aproxima inteiro.
    guardas = [
        ("#inspetor{overflow-anchor:none}", "o inspetor voltou a ancorar o scroll"),
        ('id="cAz"', "o campo do zoom desapareceu"),
        ('type="text" inputmode="decimal" id="cAz"', "o campo do zoom voltou a ser number"),
        ('guardaDesfazerCampos("mudar o zoom do aproxima", c, ["az"])', "o zoom saiu do anular"),
        # e de 18 de setembro a tarde, tambem medidos a falhar no browser pelo verificador:
        #   - a sombra da caixa169 tapava a barra do palco e a nota fora do 16:9;
        #   - a folha inteira no quadro mostrava as vizinhas dentro do ecra 16:9;
        #   - o change do zoom repintava o inspetor: o Tab ia para o body e o primeiro clique
        #     no ponto de foco perdia-se.
        ("#palco .nota, #palco .calha, #palco .hud{z-index:5}", "os comandos do palco voltaram a ficar por baixo da mascara"),
        ("el.innerHTML = (apx ? fotoDoAproxima(c, f, apx) : \"\") +", "o palco do aproxima voltou a mostrar a folha inteira"),
        ("e.target.value = az1(azDe(c));", "o change do zoom deixou de escrever o numero guardado no campo"),
    ]
    for texto, queixa in guardas:
        if html.count(texto) != 1:
            problemas.append("%s (%r aparece %d vezes)" % (queixa, texto, html.count(texto)))
    bloco_az = html[html.find('liga("cAz","change"'):html.find('liga("cAz","change"') + 400]
    if not bloco_az or "pintaInspetor" in bloco_az.split("});")[0]:
        problemas.append("o change do zoom voltou a repintar o inspetor")
    for marca in ("function marcarFoco(", 'data-focoreset]").forEach(function(b){'):
        inicio = html.find(marca)
        if inicio < 0 or "pintaClips()" not in html[inicio:inicio + 1200]:
            problemas.append("%s deixou de repintar a lista" % marca)
    js = ("var window = {innerWidth: 1280, innerHeight: 720};\n" + "\n".join(constantes) + "\n" +
          "function temTextosFotos(){ return false; } function textosDasFotos(){ return []; }\n" +
          "function opcoesTextos(){ return undefined; }\n" +
          "\n".join(_bloco_do_editor(html, m, problemas) for m in marcas))

    medidas = [(3000, 2000), (2000, 3000), (3024, 3661), (4032, 3024), (1920, 1080), (700, 1242),
               (4000, 3000)]
    focos = [(0.5, 0.5), (0.35, 0.4), (0.393, 0.741), (0.1, 0.9), (0.05, 0.5), (0.9, 0.2)]
    zooms = [1.2, 1.6, 2.2, 2.8, 3.3, 4.0]
    casos = [{"w": w, "h": h, "f": f, "az": z} for w, h in medidas for f in focos for z in zooms]
    janelas = [(1280, 720), (1280, 800), (1440, 900), (390, 844), (844, 390)]
    palcos = [{"w": w, "h": h, "f": f, "az": z, "W": W, "H": H}
              for (w, h, f) in ((3024, 3661, (0.393, 0.741)), (3000, 2000, (0.35, 0.4)),
                                (2000, 3000, (0.1, 0.9)))
              for z in (1.2, 2.2, 2.8) for W, H in janelas]
    programa = js + "\nvar casos = %s, palcos = %s;\n" % (json.dumps(casos), json.dumps(palcos)) + """
var est = {focos: {}};
function ff(k){ return {id: "x", w: k.w, h: k.h}; }
function comFoco(k, fn){ est.focos = {x: k.f}; try { return fn(); } finally { est.focos = {}; } }
function el(W, H){ return {getBoundingClientRect: function(){ return {width: W, height: H}; }}; }
var azCasos = [undefined, 2.6, "2,6", 9, 1.19, "abc", 0, 4, 1.2];
var poeCasos = ["9", "2,6", "2.2", "", "1", "3.14159"];
var v = {clips: [
  {t: "video", f: "a.mp4", d: 3},
  {t: "foto", i: "x", e: "aproxima", az: 3, r: "fundo"},
  {t: "foto", i: "x", e: "aproxima", az: 3, r: "rajada"},
  {t: "foto", i: "x", e: "aproxima", r: "fiel"},
  {t: "video", f: "b.mp4", d: 0.8, vin: 0},
  {t: "foto", i: "y", e: "afastada", r: "fiel"}]};
process.stdout.write(JSON.stringify({
  trava: casos.map(function(k){ return comFoco(k, function(){
    var t = travaAproxima(ff(k), k.az);
    return {tx: t[0].travado, ty: t[1].travado, precisa: zoomQueCentra(ff(k), k.az),
            zona: zonaAproxima(ff(k), 1000, k.az)}; }); }),
  palco: palcos.map(function(k){ return comFoco(k, function(){
    return aproximaNoPalco({t: "foto", e: "aproxima", az: k.az}, ff(k), el(k.W, k.H)); }); }),
  az: azCasos.map(function(z){ var c = z === undefined ? {} : {az: z}; return [azDe(c), azRecusado(c)]; }),
  poe: poeCasos.map(function(x){ var c = {az: 3}; var z = poeAz(c, x); return [z, c.hasOwnProperty("az") ? c.az : null]; }),
  aviso: [avisoDoEnquadramento({t: "foto", i: "x", e: "aproxima"}),
          comFoco({f: [0.4, 0.6]}, function(){ return avisoDoEnquadramento({t: "foto", i: "x", e: "aproxima"}); }),
          avisoDoEnquadramento({t: "foto", i: "x", e: "aproxima", r: "rajada"})],
  ativo: [aproximaAtivo({t: "foto", e: "aproxima"}), aproximaAtivo({t: "foto", e: "aproxima", r: "rajada"}),
          aproximaAtivo({t: "foto", e: "parada"})],
  ordens: v.clips.map(function(c, i){ return ordemDoClip(v, c, i); }),
  opcoes: OPCOES_ENQUADRAMENTO.map(function(o){ return o[0]; })
}));
"""
    pasta = tempfile.mkdtemp(prefix="teste_mesa_aprox_")
    caminho = os.path.join(pasta, "mesa_aproxima.js")
    open(caminho, "w", encoding="utf-8").write(programa)
    saida = None
    if not problemas:
        r = subprocess.run([node, caminho], capture_output=True, text=True, encoding="utf-8", timeout=120)
        if r.returncode != 0:
            problemas.append("o node nao correu as contas da Mesa: %s" % r.stderr.strip()[:300])
        else:
            saida = json.loads(r.stdout)
    L, A = render.L, render.A

    def geometria(w, h, az):
        """A foto no fim do movimento, com as contas do render, sem arredondar: (fw, fh) . az."""
        esc = min(L * (1 + render.ZOOM) / w, A * (1 + render.ZOOM) / h) / (1 + render.ZOOM)
        return w * esc * az, h * esc * az, w * esc, h * esc

    def janela(tamanho, lado, f):
        """(inicio, largura) do ecra dentro da foto, em fracao da foto, no fim do movimento."""
        c = render.aproxima_centro(lado, tamanho, f)
        inicio = max(0.0, (tamanho / 2.0 - c) / tamanho)
        return inicio, min(1.0, lado / tamanho)

    def compara_palcos(lista):
        """(queixas, palcos certos) do que o aproximaNoPalco() devolveu para cada palco."""
        maus, certos = [], 0
        for k, o in zip(palcos, lista):
            tw, th, _fw, _fh = geometria(k["w"], k["h"], k["az"])
            s_ = o["lado"] / max(k["w"], k["h"])
            pw, ph = k["w"] * s_, k["h"] * s_
            cx, cy = k["W"] / 2.0 + o["dx"], k["H"] / 2.0 + o["dy"]
            cx_ = o["caixa"]
            # o ecra 16:9 do palco dentro da foto, como a janela() do render: onde comeca e
            # quanto mostra, em fracao da foto
            mesa = (max(0.0, (cx_["x"] - (cx - pw / 2)) / pw), min(1.0, cx_["w"] / pw),
                    max(0.0, (cx_["y"] - (cy - ph / 2)) / ph), min(1.0, cx_["h"] / ph))
            certo = janela(tw, L, k["f"][0]) + janela(th, A, k["f"][1])
            # E O CENTRO DA FOTO, SEM CORTAR A NADA. A comparacao de cima corta o principio da
            # janela a zero, e isso apagava um desvio para fora da foto: um palco sem o travao
            # na largura (dx = qx) passava na foto do anel, com a borda a mostra, por 0,0015
            # dentro da tolerancia (verificador, mutacao J2). O dx e o dy, em fracao do ecra
            # 16:9, tem de ser os do aproxima_centro() do render, eixo a eixo.
            centro_r = ((render.aproxima_centro(L, tw, k["f"][0]) - L / 2.0) / L,
                        (render.aproxima_centro(A, th, k["f"][1]) - A / 2.0) / A)
            centro_m = (o["dx"] / cx_["w"], o["dy"] / cx_["h"])
            if abs(cx_["w"] / cx_["h"] - 16 / 9.0) > 1e-6 or any(abs(a - b) > 0.003 for a, b in zip(mesa, certo)) \
                    or any(abs(a - b) > 1e-4 for a, b in zip(centro_m, centro_r)):
                maus.append("palco %dx%d, %dx%d foco %s zoom %s: mostra %s com o centro em %s, e o "
                            "render %s com o centro em %s"
                            % (k["W"], k["H"], k["w"], k["h"], k["f"], k["az"],
                               ["%.3f" % x for x in mesa], ["%.4f" % x for x in centro_m],
                               ["%.3f" % x for x in certo], ["%.4f" % x for x in centro_r]))
            else:
                certos += 1
        return maus, certos

    contas = {"travoes": 0, "zooms": 0, "zonas": 0, "palcos": 0}
    if saida:
        for k, o in zip(casos, saida["trava"]):
            tw, th, fw, fh = geometria(k["w"], k["h"], k["az"])
            precisos = []
            for eixo, lado, tamanho, um, f, travado in (("largura", L, tw, fw, k["f"][0], o["tx"]),
                                                        ("altura", A, th, fh, k["f"][1], o["ty"])):
                ideal = lado / 2.0 - (f - 0.5) * tamanho
                desvio = abs(render.aproxima_centro(lado, tamanho, f) - ideal)
                if (desvio > 1.0) != travado:
                    problemas.append("%dx%d foco %s zoom %s na %s: o render desvia %.2f px e a Mesa "
                                     "diz travado=%s" % (k["w"], k["h"], k["f"], k["az"], eixo, desvio, travado))
                if travado:
                    contas["travoes"] += 1
                    precisos.append(render.aproxima_zoom_que_centra(lado, um, f))
            alvo = render.aproxima_zoom_sugerido(precisos) if precisos else None
            if (alvo or 0) != (o["precisa"] or 0):
                problemas.append("%dx%d foco %s zoom %s: o render sugere %s e a Mesa %s"
                                 % (k["w"], k["h"], k["f"], k["az"], alvo, o["precisa"]))
            elif alvo:
                contas["zooms"] += 1
            # A ZONA DO EDITOR DO PONTO DE FOCO, em fracao da foto.
            s_ = min(1000.0 / k["w"], 1000.0 / k["h"])
            pw, ph = k["w"] * s_, k["h"] * s_
            z = o["zona"]
            mesa = ((z["x"] - (1000 - pw) / 2) / pw, z["w"] / pw, (z["y"] - (1000 - ph) / 2) / ph, z["h"] / ph)
            certo = janela(tw, L, k["f"][0]) + janela(th, A, k["f"][1])
            if any(abs(a - b) > 0.002 for a, b in zip(mesa, certo)):
                problemas.append("%dx%d foco %s zoom %s: a zona da Mesa e %s e o render mostra %s"
                                 % (k["w"], k["h"], k["f"], k["az"], ["%.3f" % x for x in mesa],
                                    ["%.3f" % x for x in certo]))
            else:
                contas["zonas"] += 1
        palcos_maus, contas["palcos"] = compara_palcos(saida["palco"])
        problemas += palcos_maus
        # O ZOOM GUARDADO: a regra do montar e do render (ler_aproxima), incluindo a recusa.
        for z, (valor, recusado) in zip([None, 2.6, "2,6", 9, 1.19, "abc", 0, 4, 1.2], saida["az"]):
            if z is None:
                certo_z = (2.2, False)
            else:
                _e, certo_v, aviso = render.ler_aproxima("Aproxima %s" % z)
                certo_z = (certo_v, bool(aviso))
            if abs(valor - certo_z[0]) > 1e-9 or recusado != certo_z[1]:
                problemas.append("azDe(%r) deu %s (recusado %s) e o render le %s" % (z, valor, recusado, certo_z))
        # O QUE SE ESCREVE NO CAMPO: travado nos limites, e a omissao nao se guarda.
        if saida["poe"] != [[4, 4], [2.6, 2.6], [2.2, None], [2.2, None], [1.2, 1.2], [3.14, 3.14]]:
            problemas.append("o poeAz guardou %s" % saida["poe"])
        aviso = saida["aviso"]
        if not aviso[0] or aviso[1] or aviso[2]:
            problemas.append("o aviso do foco em falta ficou %s" % aviso)
        if saida["ativo"] != [True, False, False]:
            problemas.append("aproximaAtivo deu %s" % saida["ativo"])
        ordens = saida["ordens"]
        quer = [("zoom_final", None), ("zoom_final", 3), ("zoom_final", None), ("zoom_final", 2.2),
                ("zoom_final", None), ("zoom_final", None)]
        for k, (chave, valor) in enumerate(quer):
            if ordens[k].get(chave) != valor:
                problemas.append("as ordens do clip %d dizem %s=%r" % (k + 1, chave, ordens[k].get(chave)))
        if "enquadramento" in ordens[2]:
            problemas.append("a foto em rajada saiu nas ordens com o enquadramento %r" % ordens[2]["enquadramento"])
        import montar_da_mesa
        fonte = open(montar_da_mesa.__file__, encoding="utf-8").read()
        m = re.search(r"ENQUADRAMENTOS = \{([^}]*)\}", fonte)
        conhecidos = set(re.findall(r'"([a-z]+)":', m.group(1))) if m else set()
        if set(saida["opcoes"]) != {"", "afastada", "parada", "aproxima"} or \
                set(o for o in saida["opcoes"] if o) - conhecidos:
            problemas.append("a lista do Enquadramento tem %s e o montar conhece %s"
                             % (saida["opcoes"], sorted(conhecidos)))
    # MUTACAO J2: o palco sem o travao na largura. Corre-se o mesmo programa com essa linha
    # mudada, e a comparacao dos palcos tem de se queixar.
    linha_j2 = "var dx = Math.max(-limx, Math.min(limx, qx))"
    if saida and programa.count(linha_j2) != 1:
        problemas.append("a linha do travao do palco aparece %d vezes" % programa.count(linha_j2))
    elif saida:
        mutado = os.path.join(pasta, "mesa_aproxima_j2.js")
        open(mutado, "w", encoding="utf-8").write(programa.replace(linha_j2, "var dx = qx"))
        r2 = subprocess.run([node, mutado], capture_output=True, text=True, encoding="utf-8", timeout=120)
        if r2.returncode != 0 or not compara_palcos(json.loads(r2.stdout)["palco"])[0]:
            problemas.append("com o palco sem o travao na largura a comparacao dos palcos nao se queixou")
    verifica("Mesa diz do aproxima o que o render faz", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "%d casos, %d travoes, %d zooms sugeridos, %d zonas, %d palcos em 5 janelas"
             % (len(casos), contas["travoes"], contas["zooms"], contas["zonas"], contas["palcos"]))


def teste_voz_nao_toca_por_cima_do_som_do_video():
    """Uma voz do pedido que caia no troco de um video do corpo fica de fora, com aviso.

    O DEFEITO, medido a 18 de setembro: o limite existia, estava calculado e escrito no
    comentario ("um video do corpo para as vozes"), e so alimentava um aviso generico no
    fim. A voz era colocada na mesma. Com tres pecas na foto do pedido, a terceira cobria os
    3,47 s do troco do Homer e ficava 4,7 dB acima do «D'oh»: dois sons a falar ao mesmo
    tempo, os dois fora do loudnorm, com metade da sala de costas. Uma voz por cima dos
    FOGUETES ja era saltada; a mesma guarda nao tinha sido estendida ao som do video, que e
    a coisa alta que esta ronda acrescentou.
    """
    import shutil
    import tempfile
    import montar_da_mesa
    import render
    pasta = tempfile.mkdtemp(prefix="teste_voz_video_")
    nomes = _pecas_de_voz(pasta, (2.0, 3.5, 5.5))
    filme = _video_sintetico(pasta, "homer_ensaio.mp4", dura=6.0)
    guardado = montar_da_mesa.PEDACOS
    guardadas_v = dict(render.VIDEOS)
    montar_da_mesa.PEDACOS = pasta
    render.VIDEOS["homer_ensaio.mp4"] = (filme, 0.0)
    montar_da_mesa._DURACOES.clear()
    problemas = []
    try:
        base = [
            {"t": "foto", "i": "f0347", "d": 4, "c": 0, "r": "fiel", "vz": list(nomes)},
            {"t": "foto", "i": "f0348", "d": 4, "c": 0.7, "r": "fiel"},
            {"t": "video", "f": "homer_ensaio.mp4", "vin": 1.0, "d": 3.5, "c": 0},
            {"t": "foto", "i": "f0012", "d": 5, "c": 0.7, "r": "fiel"},
            {"t": "cartao", "x": "Nasce o Tiago", "d": 3.6, "c": 0.7, "r": "fiel"},
            {"t": "foto", "i": "f0041", "d": 4, "c": 0.7, "r": "fiel"},
        ]
        _linhas, som, saida = _monta_em_pasta([dict(c) for c in base], nome="vozvid")
        vozes = [(float(r["quando_s"]), float(r["quando_s"]) + float(r["dura_s"]))
                 for r in som if (r.get("voz") or "").strip()]
        video = [(float(r["quando_s"]), float(r["quando_s"]) + float(r["dura_s"]))
                 for r in som if (r.get("video") or "").strip()]
        if len(video) != 1:
            problemas.append("%d faixas de som do video" % len(video))
        if len(vozes) != 2:
            problemas.append("%d vozes colocadas, esperava 2 (a terceira nao cabe)" % len(vozes))
        for a, b in vozes:
            for c, d in video:
                if a < d and c < b:
                    problemas.append("uma voz (%.2f-%.2f) toca por cima do som do video "
                                     "(%.2f-%.2f)" % (a, b, c, d))
        if "fica de fora" not in saida or "homer_ensaio.mp4" not in saida:
            problemas.append("a voz que cairia no video saiu sem aviso que nomeie o video")
        # E O AVISO DE NIVEL: o som de um video entra com ganho 1,0, sem ninguem o medir.
        # Um ficheiro 20 dB abaixo do leito faz a musica baixar 12 dB e nao poe nada no
        # lugar. Nao se muda o ganho, que e decisao dele; mede-se e diz-se.
        baixo = os.path.join(pasta, "baixinho.mp4")
        import subprocess
        subprocess.run([render.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                        "-i", filme, "-af", "volume=0.01", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "128k", baixo], capture_output=True)
        render.VIDEOS["baixinho.mp4"] = (baixo, 0.0)
        montar_da_mesa._DURACOES.clear()
        mudo = [dict(c) for c in base]
        mudo[0] = dict(mudo[0]); mudo[0].pop("vz")
        mudo[2] = dict(mudo[2], f="baixinho.mp4")
        _l2, _som2, saida2 = _monta_em_pasta(mudo, nome="vozvid2")
        if "LUFS" not in saida2:
            problemas.append("um video 40 dB abaixo do leito entrou sem uma palavra")
    finally:
        montar_da_mesa.PEDACOS = guardado
        render.VIDEOS.clear()
        render.VIDEOS.update(guardadas_v)
        montar_da_mesa._DURACOES.clear()
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("a voz do pedido nao fala por cima do som do video", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "a terceira voz fica de fora com aviso, e o nivel do video e medido")


def teste_contador_mal_escrito_nao_para_o_render():
    """Um x de contador que nao se le da clip preto, nao mata o render, e a Mesa avisa.

    O DEFEITO: o campo do contador aceita texto livre. "04/10/2026>1995|do casamento ate
    1995" (uma ponta data, a outra ano) e a forma que ele escreve para rebobinar do dia do
    casamento ate 1995, e era a unica que passava calada dos dois lados: a Mesa chamava-lhe
    «anos», porque so dizia «datas» com AS DUAS pontas em dd/mm/aaaa, e nao dava aviso
    nenhum; o Python decide pela barra, lia-o como datas e o ler_datas rebentava com
    ValueError DENTRO do preparar(), ou seja no fotograma em que o contador entra, a meio
    de um render de quinze minutos. Com fatias, a fatia morre e o pai apaga o _corpo.mp4:
    perde-se tudo o que ja estava desenhado. E a mesma regra do imagem_da_marca(), que o
    CLAUDE.md escreve: um dado mal escrito nao pode parar um render a meio.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import montar_da_mesa
    import render
    problemas = []
    maus = ["04/10/2026>1995|do casamento ate 1995", "2026>25/12/2025|x",
            "29/02/2025>01/01/2025|x", "04/10/2026>|x"]
    for x in maus:
        if render.contador_legivel(x):
            continue
        clip = {"tipo": "contador", "texto_ecra": x, "ficheiro": "", "duracao_s": "9",
                "ordem": "3", "tratamento": "fiel"}
        try:
            if render.preparar(clip, {}) is not None:
                problemas.append("%r preparou-se como se fosse legivel" % x[:24])
        except Exception as erro:
            problemas.append("%r ainda parte o render: %s" % (x[:24], type(erro).__name__))
    # O de datas e o de anos, bem escritos, continuam a preparar-se como sempre.
    for x in ("04/10/2026>25/12/2025|4 de outubro de 2026", "2026>1995|x"):
        if render.preparar({"tipo": "contador", "texto_ecra": x, "ficheiro": "",
                            "duracao_s": "9", "ordem": "1", "tratamento": "fiel"}, {}) is None:
            problemas.append("um contador bem escrito deixou de se preparar: %r" % x[:24])
    # E O MONTAR ESCREVE O CSV NA MESMA, com aviso: e o render que tem de aguentar.
    linhas, _som, saida = _monta_em_pasta(
        [{"t": "contador", "x": maus[0], "d": 9, "c": 0.7, "r": "fiel"},
         {"t": "foto", "i": "f0012", "d": 4, "c": 0.7, "r": "fiel"}], nome="contmau")
    if "nao consigo ler" not in saida:
        problemas.append("o montar escreveu o contador ilegivel sem aviso")
    if not linhas:
        problemas.append("o montar deixou de escrever o CSV")
    # A MESA TEM DE CHAMAR-LHE O MESMO QUE O PYTHON, e avisar. Era aqui que o silencio
    # comecava: com a Mesa a dizer "anos" e o Python a dizer "datas", o inspetor nao tinha
    # razao nenhuma para se queixar.
    node = shutil.which("node")
    if not node:
        salta("contador mal escrito nao para o render", "sem node neste PC para a parte da Mesa")
    else:
        html = open(os.path.join(REPO, "scripts", "editor_base.html"), encoding="utf-8").read()
        js = "\n".join(_bloco_do_editor(html, m, problemas) for m in
                       ("function eDataContador(", "function dataValida(", "function lerContador(",
                        "function dataParaIso(", "function d2(", "function diasEntre(",
                        "function pontoDoContador(", "function contadoresSeguidos(",
                        "function avisosDoContador("))
        casos = list(maus) + ["04/10/2026>25/12/2025|x", "2026>1995|x"]
        seguidos = [("04/10/2026>25/12/2025|x", "2025>1995|x"),
                    ("04/10/2026>25/12/2025|x", "24/12/2025>01/01/2025|x"),
                    ("2026>1995|x", "1995>2011|x"),
                    ("2026>1995|x", "2011>2019|x"),
                    ("2026>2025|x", "25/12/2025>01/01/2025|x"),
                    ("nao se le isto", "2025>1995|x"),
                    ("04/10/2026>1995|x", "1995>2011|x")]
        pasta = tempfile.mkdtemp(prefix="teste_cont_mesa_")
        try:
            caminho = os.path.join(pasta, "cont.js")
            open(caminho, "w", encoding="utf-8").write(
                js + "\nvar CONTADOR_DIAS_MAX = 3 * 366;\nvar casos = %s, pares = %s;\n"
                % (json.dumps(casos), json.dumps(seguidos)) + """
process.stdout.write(JSON.stringify({
  tipos: casos.map(function(x){ return lerContador(x).tipo; }),
  avisos: casos.map(function(x){ return avisosDoContador(lerContador(x)).length; }),
  seguidos: pares.map(function(p){ return contadoresSeguidos(p[0], p[1]); })
}));
""")
            r = subprocess.run([node, caminho], capture_output=True, text=True,
                               encoding="utf-8", timeout=120)
            if r.returncode != 0:
                problemas.append("o node nao correu as contas do contador: %s"
                                 % r.stderr.strip()[:200])
            else:
                saida_js = json.loads(r.stdout)
                for k, x in enumerate(casos):
                    tipo_py = "datas" if "/" in x.partition("|")[0] else "anos"
                    if saida_js["tipos"][k] != tipo_py:
                        problemas.append("a Mesa chama %r a %r e o Python chama %r"
                                         % (saida_js["tipos"][k], x[:24], tipo_py))
                for k, x in enumerate(maus):
                    if not saida_js["avisos"][k]:
                        problemas.append("a Mesa nao avisa de %r" % x[:24])
                for k in (len(maus), len(maus) + 1):
                    if saida_js["avisos"][k]:
                        problemas.append("a Mesa avisa de um contador bem escrito")
                for k, (a, b) in enumerate(seguidos):
                    if saida_js["seguidos"][k] != montar_da_mesa.contadores_seguidos(a, b):
                        problemas.append("contadores seguidos: a Mesa diz %s e o montar %s "
                                         "em %r -> %r" % (saida_js["seguidos"][k],
                                                          montar_da_mesa.contadores_seguidos(a, b),
                                                          a[:16], b[:16]))
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
    verifica("contador mal escrito nao para o render", not problemas,
             "; ".join(problemas)[:240] if problemas else
             "sai preto com aviso, e a Mesa le o tipo como o Python")


def main():
    rapido = "--rapido" in sys.argv
    print("TESTES DE REGRESSAO")
    print("Cada um existe porque alguma coisa partiu de verdade.")
    print()
    print("composicao de imagem")
    teste_borda_de_subpixel()
    teste_borda_sobre_fundo()
    print("linha do tempo")
    teste_agenda_das_paragens()
    teste_todas_as_marcas_aparecem()
    teste_marcas_com_imagem_encontram_o_ficheiro()
    teste_fita_da_mesa_e_percorrivel()
    teste_musicas_marcadas_encontram_ficheiro()
    teste_fita_continua_arranca_a_andar()
    teste_fita_dos_anos_e_cronologica()
    teste_contador_mostra_a_data()
    teste_data_do_contador_nao_pisca()
    teste_contador_de_anos_igual_ao_byte()
    teste_contador_por_datas_anda_dia_a_dia()
    teste_contadores_sao_a_mesma_fita()
    teste_ponteiro_do_contador_le_se()
    teste_meses_da_regua_leem_se()
    teste_regua_atravessa_o_ecra()
    teste_contadores_seguidos_cortam_a_seco()
    teste_rebobinar_em_cada_contador_que_recua()
    teste_juncao_com_dois_contadores()
    teste_vozes_do_pedido_no_som()
    teste_vozes_no_render_com_o_leito_em_baixo()
    teste_janelas_do_leito_sobrepostas_e_no_fim()
    teste_mesa_diz_o_que_a_musica_faz_por_baixo_de_cada_um()
    teste_v3_sem_vozes_igual_ao_byte()
    teste_musica_marcada_sem_silencio_a_abrir()
    teste_musica_da_abertura_retoma_na_fita_da_clara()
    teste_cartao_da_bebe_com_acento()
    teste_legenda_guarda_as_falas()
    teste_fim_em_fade_a_preto()
    teste_enquadramento_afastada_e_parada()
    teste_aproxima_comeca_igual_e_acaba_no_foco()
    teste_aproxima_entre_os_encadeados()
    teste_aproxima_nunca_descobre_borda()
    teste_aproxima_anda_sem_quebras()
    teste_aproxima_diz_quanto_faltou_e_o_zoom_que_centra()
    teste_aproxima_acaba_nitido()
    teste_aproxima_sem_foco_vai_ao_centro_e_avisa()
    teste_aproxima_com_zoom_fora_dos_limites_recusado()
    teste_limites_do_aproxima_iguais()
    print("imagens")
    teste_regra_de_ampliacao_igual()
    teste_finais_cobre_o_que_precisa(rapido)
    teste_ampliacao_pequena_usa_lanczos(rapido)
    print("montagens")
    teste_render_usa_o_indice(rapido)
    teste_lado_a_lado()
    teste_ponto_de_foco()
    teste_colagem_e_pilha_pousam_dentro_do_quadro()
    teste_colagem_nao_tapa_caras()
    teste_colagem_enche_o_ecra()
    teste_colagem_espalhada()
    teste_pilha_nada_desaparece()
    teste_pilha_leque()
    teste_estilos_de_omissao_iguais_a_antes()
    teste_disposicoes_de_antes_ao_byte()
    teste_monte_espera_o_encadeado()
    teste_limites_dos_grupos_iguais()
    teste_lado_6g()
    teste_colagem_e_pilha_com_muitas_fotos()
    teste_agenda_nova_na_legenda_e_nas_tapadas()
    teste_monte_acima_da_legenda()
    teste_linhas_texto_foto()
    teste_grupos_sem_texto_iguais_a_antes()
    teste_texto_nas_fotos_do_monte()
    teste_texto_nas_fotos_lado_a_lado()
    teste_colagem_faixa_fora_do_que_as_seguintes_tapam()
    teste_textos_opcoes_invalidas()
    teste_tamanho_do_texto_das_fotos()
    teste_pilha_texto_das_tapadas()
    teste_legenda_por_foto()
    teste_camada_do_conjunto_igual_as_fotos()
    teste_borda_da_colagem_nao_pisca()
    teste_colagem_e_pilha_deterministicas()
    teste_colagem_e_pilha_pelo_preparar()
    teste_mesa_escreve_colagem_e_pilha()
    teste_agenda_da_mesa_igual_ao_render()
    teste_mesa_no_sitio_do_clip()
    teste_mesa_sem_nomes_repetidos()
    teste_mesa_esconde_as_da_montagem()
    teste_mesa_nascimento_colagem_e_avisos()
    teste_mesa_escreve_o_estilo()
    teste_mesa_escreve_textos_das_fotos()
    teste_mesa_avisa_textos_das_fotos()
    teste_textos_das_fotos_chegam_ao_render()
    teste_mesa_escreve_textos_opcoes()
    teste_mesa_avisa_legenda_curta()
    teste_mesa_avisa_legenda_comprida_e_foto_depois_do_fim()
    teste_textos_opcoes_chegam_ao_render()
    teste_estado_das_fotos()
    teste_previas_cobrem_todas_as_fotos()
    teste_foguetes_antes_das_fotos()
    teste_intro_sem_repetir(rapido)
    teste_intro_reparte_clara_e_tiago()
    teste_corte_da_intro_nunca_desce()
    teste_excluidas_saem()
    print("video no meio do corpo")
    teste_video_no_meio_do_corpo()
    teste_som_do_video_no_meio()
    teste_corpo_da_montagem_e_o_do_render()
    teste_janela_do_leito_conta_com_o_cruzamento()
    teste_musica_parada_conta_os_buracos()
    teste_cache_de_quadros_nao_apaga_a_de_outra_montagem()
    teste_cache_de_quadros_grande_para_antes_de_encher_o_disco()
    teste_video_do_meio_sem_duracao_mede_o_ficheiro()
    teste_video_mudo_nao_cala_o_filme()
    teste_video_em_falta_nao_para_o_render()
    teste_juntar_repoe_so_o_bloco_inicial()
    teste_mesa_conta_o_video_do_meio_como_o_montar()
    teste_voz_nao_toca_por_cima_do_som_do_video()
    teste_contador_mal_escrito_nao_para_o_render()
    teste_gerar_mesa_oferece_o_que_o_montar_resolve()
    teste_mesa_marca_o_texto_que_passa_depressa()
    teste_validador_apanha_o_emoji_e_os_erros_de_escrita()
    teste_mesa_exporta_os_campos_do_montar()
    teste_mesa_aproxima_diz_o_que_o_render_faz()
    print("render em fatias")
    teste_fatias_repartem_todos_os_fotogramas()
    teste_fatias_desenham_os_mesmos_fotogramas()
    teste_fatia_fala_so_pelo_stderr()
    teste_fatias_pelo_main_dao_o_mesmo_ficheiro()
    teste_fatia_que_morre_nao_deixa_ficheiro()
    print()
    print("%d passaram, %d falharam%s"
          % (len(PASSOU), len(FALHAS),
             ", %d saltados" % len(SALTADOS) if SALTADOS else ""))
    for nome, motivo in SALTADOS:
        print("  SALTADO: %s  %s" % (nome, motivo))
    if FALHAS:
        print()
        for nome, detalhe in FALHAS:
            print("  FALHOU: %s  %s" % (nome, detalhe))
        sys.exit(1)


if __name__ == "__main__":
    main()
