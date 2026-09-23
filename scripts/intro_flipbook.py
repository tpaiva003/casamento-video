# -*- coding: utf-8 -*-
"""A abertura ao estilo do folhear de banda desenhada, com "Clara & Tiago".

O Tiago mandou um "Marvel Comics Intro" e pediu uma coisa parecida com fotos
deles, com o mesmo som, e o nome deles no lugar de MARVEL.

O QUE O ORIGINAL FAZ, medido fotograma a fotograma:

  0,0 a 1,2 s   preto
  1,2 a 6,3 s   paginas de banda desenhada a passar depressa, cada vez mais
                depressa, em tom quente de papel velho
  6,3 a 9,0 s   as letras formam-se POR CIMA das paginas: as imagens continuam
                a correr mas so se veem dentro das letras
  9,0 a 11,5 s  o letreiro fica solido, branco sobre vermelho
  11,5 a 13,4 s desvanece para preto

O PEDIDO DE 21 DE SETEMBRO, e o que mudou por causa dele.

  A Clara nao gostou do Homer nem da voz dela no pedido, e a abertura ficou:
  Fox, esta intro, uma pequena pausa, o rebobinar ate ao pedido. Sobre esta
  intro o Tiago pediu: "revermos a Intro da Marvel para ter uma distribuicao
  mais equitativa das fotos da Clara e do Tiago, sendo que idealmente deveria
  acabar com uma foto deles no final quando depois aparece a historia de
  Clara & Tiago". Daqui vem:

  - as fotos saem da montagem do filme (a demo_v3 da Mesa) e nao da v1a, e
    ficam de fora as do pedido, que aparecem logo a seguir a intro;
  - quem esta em cada foto diz-o o Tiago, pelas etiquetas que pos na Mesa, e na
    falta delas a coluna pessoa do inventario. Nada aqui olha para caras;
  - as posicoes antes das letras sao da Clara e do Tiago, repartidas por TEMPO
    DE ECRA e nao por contagem: a primeira foto do folhear fica muito mais tempo
    do que a ultima, e uma a uma a comecar pela Clara dava-lhe sempre a posicao
    mais longa de cada par. Com as letras, so fotos dos dois. Ver
    repartir_por_tempo();
  - o folhear acaba numa foto dos dois, que FICA: e por dentro dela que as
    letras se formam, e e ela que se ve quando aparece o nome;
  - um segundo de preto e silencio no fim, a pausa antes do rebobinar.

O QUE O TIAGO DISSE DA INTRO 3, a 22 de setembro: "agora as fotos estao muito
rapidas (diria que esta muito mais rapido desde o inicio que a versao anterior)
e a nossa foto no estadio aparece agora de forma pouco natural e fica muito tempo
ate desaparecer". Medido, tinha razao nas duas:

  - a intro 3 punha 48 fotos em 4,35 s, todas a ecra inteiro; a de 12 de
    setembro punha 64 em 7,85 s e as mais rapidas ja passavam por dentro das
    letras, escondidas. A primeira foto baixou de 0,44 s para 0,30, e no fim
    passava uma foto a cada fotograma e meio, a vista;
  - a selfie entrava em corte seco a seguir ao troco mais rapido, e via-se de
    5,5 a quase 10 s, com o vermelho a subir devagar a volta dela.

A intro 4 voltou ao ritmo de 12 de setembro e fez o folhear abrandar ate a
selfie. O Tiago, ainda a 22 de setembro: "Mas o folhear no audio nao parou, acho
que podemos incluir mais fotos antes das nossas selfies e ate acho que podem
continuar a passar selfies com as letras ja la desde que sejam nossas". Medido
no som: ha paginas a virar de 1,2 s ate perto dos 10 s, tambem por baixo das
letras, como no original.

Por isso, desde a intro 5, o folhear e o do original, ao ritmo de 12 de
setembro e sem parar (ver inicios_do_folhear): ate as letras, as fotos de cada
um, repartidas por tempo; quando as letras comecam, SO fotos dos dois, que
continuam a passar por dentro delas ate o som das paginas acabar; e a ultima e a
selfie do estadio, que fica por dentro do letreiro quando ele fica solido.

O TEMPO DESTA VERSAO:

  0,0 a 0,75 s    preto, como no original
  0,75 a 1,15 s   a primeira foto acende do preto, ja no corte do folhear
  1,15 a 6,3 s    35 fotos da Clara e do Tiago, cada vez mais depressa, ao
                  ritmo de 12 de setembro
  6,3 a 10,0 s    fotos dos dois, a passar por dentro das letras que se formam
  10,0 s          a selfie do estadio, a ultima, que fica dentro do letreiro
  9,0 a 11,6 s    o letreiro fica solido
  11,6 a 13,44 s  desvanece para preto
  13,44 a 14,44 s preto e silencio

AS DECISOES QUE NAO SAO COPIA:

  As fotografias sao tratadas em duotone quente e contraste forte. Sem isso
  parecem um album de familia a passar depressa e nao uma sequencia de abertura.
  O tratamento e o que faz fotografias de origens diferentes, algumas
  digitalizadas nos anos 90 e outras de telemovel, parecerem a mesma coisa.

  O nome vai numa linha so, como o original, e nao em duas. Duas linhas partem
  o "Clara & Tiago" ao meio e o & fica orfao.

  O som e o do ficheiro dele, sem uma nota mudada nem o nivel. Foi o que pediu.
  O ficheiro de origem ja nao existe em disco: a unica copia do som esta na
  intro de 12 de setembro, e tira-se de la sem recodificar.

A intro de 12 de setembro (saida\\intro_clara_tiago.mp4) nunca e tocada: e a
que a montagem usa hoje, e e dela que vem o som. Esta sai com outro nome, na
pasta gerados\\intro_marvel, e o script recusa escrever por cima de um ficheiro
que ja exista.

Uso:  py -3.11 scripts/intro_flipbook.py
      py -3.11 scripts/intro_flipbook.py --escala 0.5      rascunho rapido
      py -3.11 scripts/intro_flipbook.py --so-lista        so a lista, sem video
      py -3.11 scripts/intro_flipbook.py --nome outro.mp4  outro nome de saida
      py -3.11 scripts/intro_flipbook.py --versao v1c      fotos de outra montagem
      py -3.11 scripts/intro_flipbook.py --pouso f0123     outra foto para acabar
"""
import bisect
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
ESTADO_MESA = os.path.join(REPO, "data", "mesa_estado.json")
INDICE = os.path.join(REPO, "data", "finais.csv")
FINAIS = render.FINAIS
SAIDA = r"C:\casamento-video-media\saida"
SOM_ORIGEM = r"C:\Users\User 1\Downloads\Marvel Comics Intro.mp4"
# A intro de 12 de setembro. So se le: e a unica copia que resta do som.
INTRO_ANTIGA = os.path.join(SAIDA, "intro_clara_tiago.mp4")
DESTINO = r"C:\casamento-video-media\gerados\intro_marvel"
SOM_GUARDADO = os.path.join(DESTINO, "som_marvel.m4a")
NOME_SAIDA = "intro_clara_tiago_5.mp4"

L, A, FPS = 1920, 1080, 25
NOME = "CLARA & TIAGO"
FONTE = r"C:\Windows\Fonts\impact.ttf"

# Momentos, em segundos. Copiados do original, medidos e nao adivinhados.
T_TOTAL = 13.44
T_ARRANQUE = 1.15          # comeca o folhear
# O ACENDER, desde a segunda ronda de 21 de setembro. Na intro 2 a primeira foto
# subia do preto durante 1,15 s num corte mais largo e a 85%, e as 1,15 s saltava
# para o corte do folhear (22% mais apertado) e para o brilho inteiro: lia-se como
# um solavanco. E essa meia luz, meio segundo de uma foto da Clara, nao entrava na
# conta do equilibrio: contada, eram 2,48 s contra 1,84. Agora o preto fica, como
# no Marvel original, e a foto acende so nos ultimos T_ACENDER segundos, ja no
# enquadramento com que o folhear comeca, e o que dela se ve entra na conta.
T_ACENDER = 0.40
T_LETRAS = 6.30            # as letras comecam a formar-se
# O RITMO DO FOLHEAR E O DE 12 DE SETEMBRO: 64 fotos de T_ARRANQUE a 9,0 s pela
# curva p**1.45. A curva continua depois das 9,0 s ao mesmo passo, porque o som
# das paginas continua: a ultima pagina que se ouve e perto dos 10 s (medido no
# som_marvel.m4a, a 22 de setembro). Ver inicios_do_folhear().
RITMO_N = 64
RITMO_DUR = 9.00 - 1.15
T_FIM_FOLHEAR = 10.0       # ate aqui entram fotos; a ultima e a de pouso, que fica
T_SOLIDO = 9.00            # o letreiro fica solido
T_FIM = 11.60              # comeca a desvanecer
T_PAUSA = 1.0              # preto e silencio depois do fim, antes do rebobinar

VERMELHO = (150, 22, 28)
PAPEL = (247, 233, 210)
TINTA = (46, 14, 16)

NOME_PEQUENO = "A HISTÓRIA DE"
FONTE_PEQUENA = r"C:\Windows\Fonts\arialbd.ttf"

# DE ONDE VEM CADA FOTOGRAFIA, desde 21 de setembro.
#
# Da montagem do filme na Mesa, pela ordem do filme, e nao da v1a da mae da
# Clara: a intro abre o filme que se vai ver, e as fotos devem ser dele.
VERSAO = "demo_v3"
# A foto em que o folhear pousa: uma selfie dos dois, de 2025.
POUSO = "f0286"
# O pedido vem logo a seguir a intro: a arvore com o anel, o abraco e o brinde.
# Nao podem aparecer aqui primeiro, a passar num fotograma.
FOTOS_DO_PEDIDO = ("f0260", "f0052", "f0053")

# QUANTAS FOTOGRAFIAS, e porque e que nenhuma se repete.
#
# O Tiago viu duas coisas na primeira versao: "existe um certo engasgar nas
# imagens" e "nao quero que repitas imagens nesta intro. Temos muitas imagens".
#
# Eram o mesmo defeito. Com 24 fotografias a passar durante quase oito segundos
# e a acelerar, a lista dava a volta e recomecava, e cada vez que recomecava via
# se a mesma cara outra vez, fora de sitio. E isso o engasgo.
#
# Cada fotografia aparece UMA VEZ e a lista percorre-se do principio ao fim,
# sem voltar atras. Com 48 em 4,35 s, a primeira fica tres decimas de segundo
# e a ultima um fotograma e meio, que e o efeito do original; menos do que um
# fotograma por foto ja nao dava, porque havia fotos que nunca chegavam ao ecra.
SEGUIDAS_MAX = 2           # nunca mais de duas seguidas do mesmo
# Uma foto cuja versao final tem o lado menor abaixo disto nao enche o ecra sem
# se desfazer. E o mesmo corte das paginas guardadas, LADO_MINIMO_EM_FILES.
LADO_MINIMO = 600
# A folga com que a foto de pouso e preparada. Maior do que 1,04, a aproximacao
# toda, para cada fotograma ser uma reducao e a nitidez nao mudar pelo caminho.
FOLGA_POUSO = 1.25
# ONDE ESTAO AS CARAS NA FOTO DE POUSO, em fracao da largura e da altura. Na selfie
# do estadio as caras estao a 55 por cento da altura; com o corte de sempre (puxado
# para cima, 32 por cento) ficavam na metade de baixo do quadro e o letreiro, que
# esta ao meio, tapava o estadio e nao o casal. Se o Tiago marcar um ponto de foco
# para a foto na Mesa, e esse que manda.
FOCOS_POUSO = {"f0286": (0.55, 0.56)}


def fotos_do_filme(estado, versao):
    """Os ids das fotos de uma montagem da Mesa, pela ordem do filme, cada um uma vez.

    As fotos soltas trazem o id no campo "i"; um lado a lado, colagem ou pilha
    traz os seus no campo "fotos", e contam na posicao do grupo. As que o Tiago
    excluiu na Mesa ficam de fora.
    """
    v = next((v for v in estado.get("versoes") or [] if v.get("id") == versao), None)
    if v is None:
        raise ValueError("a montagem %r nao existe no data/mesa_estado.json" % versao)
    excluidas = {k for k, sim in (estado.get("excluidas") or {}).items() if sim}
    ids, vistos = [], set()
    for c in v.get("clips") or []:
        dentro = [c.get("i")] if c.get("t") == "foto" else []
        dentro += list(c.get("fotos") or [])
        for i in dentro:
            if i and i not in vistos and i not in excluidas:
                vistos.add(i)
                ids.append(i)
    return ids


def classe_da_foto(i, estado, inv_por_id):
    """Clara, Tiago, Ambos ou None, SO pelo que o Tiago disse.

    Primeiro as etiquetas dele na Mesa: uma pessoa com "Clara" e "Tiago" no nome
    e Ambos, so "Clara" e Clara, so "Tiago" e Tiago, e varias etiquetas que
    juntas deem os dois sao Ambos. Uma foto com etiquetas que nao nomeiam nenhum
    dos dois fica de fora: ele disse quem la esta, e nao sao eles. Sem etiqueta
    nenhuma, a coluna pessoa do inventario; Familia, Amigos e vazio ficam de fora.
    """
    nomes = {p.get("id"): p.get("nome") or "" for p in estado.get("pessoas") or []}
    etiquetas = (estado.get("tags") or {}).get(i) or []
    if etiquetas:
        clara = any("Clara" in nomes.get(p, "") for p in etiquetas)
        tiago = any("Tiago" in nomes.get(p, "") for p in etiquetas)
        if clara and tiago:
            return "Ambos"
        return "Clara" if clara else ("Tiago" if tiago else None)
    p = (inv_por_id.get(i) or {}).get("pessoa") or ""
    return p if p in ("Clara", "Tiago", "Ambos") else None


def amostrar(lista, k):
    """k elementos espalhados por igual de ponta a ponta, pela ordem da lista.

    Cada um e o do meio da sua fatia, e nao o do principio: assim nem a primeira
    foto do filme nem a ultima tem lugar garantido.
    """
    if len(lista) <= k:
        return list(lista)
    passo = len(lista) / float(k)
    return [lista[int((j + 0.5) * passo)] for j in range(k)]


def lado_menor(caminho):
    """O lado menor do ficheiro, lido do cabecalho. None se nao abrir."""
    try:
        with Image.open(caminho) as im:
            return min(im.size)
    except (OSError, ValueError):
        return None


def caminhos_das_finais(ids, inv_por_id):
    """O ficheiro a abrir de cada foto, e as que nao tem indice.

    QUEM ESCOLHE A VERSAO E O data/finais.csv, e a escolha faz-se na mesma
    funcao que o render usa, render.caminhos_pelo_indice(). Este script tinha a
    sua propria ordem de preferencia, por nome dentro da FINAIS, que e o que o
    CLAUDE.md proibe: quem procura por nome apanha os ficheiros de corridas
    antigas que la ficaram. O indice le-se como em render.carregar_montagem():
    uma entrada so conta se o ficheiro existir.
    """
    indice = {}
    if os.path.exists(INDICE):
        with open(INDICE, encoding="utf-8-sig", newline="") as fh:
            for linha in csv.DictReader(fh):
                p = os.path.join(FINAIS, linha["final"])
                if os.path.exists(p):
                    indice[linha["id"]] = p
    inv_por_nome = {r["ficheiro"].lower(): r for r in inv_por_id.values()}
    clips = [{"id": i, "ficheiro": "", "tipo": "foto"} for i in ids]
    sem_indice = render.caminhos_pelo_indice(clips, indice, inv_por_id, inv_por_nome)
    return {c["id"]: c["_caminho"] for c in clips}, sem_indice


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def inicio_na_curva(i):
    """O instante em que entra a posicao i, pela curva de 12 de setembro."""
    return T_ARRANQUE + RITMO_DUR * (i / float(RITMO_N)) ** (1 / 1.45)


def inicios_do_folhear(n):
    """O instante em que cada uma das n fotos do folhear entra, pela curva.

    A primeira fica 0,44 s e cada uma fica menos do que a anterior, como na intro
    de 12 de setembro. A foto de pouso entra onde entraria a seguinte.
    """
    return [inicio_na_curva(i) for i in range(n)]


def inicio_do_pouso(n):
    """Quando entra a foto de pouso, a seguir a n fotos de folhear."""
    return inicio_na_curva(n)


def posicoes_ate(t):
    """Quantas posicoes da curva entram antes do instante t."""
    k = 0
    while inicio_na_curva(k) < t - 1e-9:
        k += 1
    return k


# QUANTAS DE CADA, que a curva decide: as que entram antes das letras sao da Clara e
# do Tiago (35); as que entram depois, ate o som das paginas acabar, sao dos dois, e a
# ultima e a de pouso.
POSICOES = posicoes_ate(T_LETRAS)
AMBOS = posicoes_ate(T_FIM_FOLHEAR) - POSICOES - 1


def indice_da_foto(t, n):
    """Qual foto esta no ecra, e quanto ja passou DESSA foto.

    As n primeiras sao o folhear; a de indice n e a foto de pouso, que entra no
    fim do folhear (inicio_do_pouso) e fica. Percorre a lista uma so vez, do principio ao fim, sem
    repeticoes e sem o salto que se via quando a lista dava a volta.
    """
    pouso = inicio_do_pouso(n)
    if t >= pouso:
        return n, 0.0
    inicios = inicios_do_folhear(n)
    i = max(0, bisect.bisect_right(inicios, t) - 1)
    fim = inicios[i + 1] if i + 1 < n else pouso
    return i, max(0.0, min(1.0, (t - inicios[i]) / max(0.001, fim - inicios[i])))


def segundos_por_posicao(n):
    """Quanto tempo cada posicao do folhear fica no ecra, fotograma a fotograma.

    E a mesma conta que o desenho faz, fotograma a fotograma, e nao a curva
    teorica: uma foto de um fotograma e meio aparece em um ou em dois, e e isso
    que se ve.

    O ACENDER ENTRA, pelo que dela se ve: um fotograma a meio brilho conta meio
    fotograma. E o mesmo brilho_do_acender() que o desenho usa.
    """
    s = [0.0] * n
    for q in range(int(round(inicio_do_pouso(n) * FPS))):
        t = q / float(FPS)
        if t < T_ARRANQUE:
            if n:
                s[0] += brilho_do_acender(t) / FPS
            continue
        i, _ = indice_da_foto(t, n)
        if i < n:
            s[i] += 1.0 / FPS
    return s


def brilho_do_acender(t):
    """Quanto da primeira foto se ve antes do folhear: 0 no preto, 1 as T_ARRANQUE."""
    if t >= T_ARRANQUE:
        return 1.0
    return suave((t - (T_ARRANQUE - T_ACENDER)) / T_ACENDER)


def repartir_por_tempo(segundos, posicoes, disponiveis):
    """A classe de cada uma das primeiras posicoes: "Clara" ou "Tiago", pelo tempo de ecra.

    Cada posicao vai para quem tem menos segundos acumulados ate ali (empate: a
    Clara), com uma excecao: nunca mais de SEGUIDAS_MAX seguidas do mesmo, senao a
    compensacao da primeira foto, que e a mais longa, dava quatro do Tiago seguidas
    logo no principio, onde as fotos ainda se reconhecem. Quem fica sem fotos
    (disponiveis) deixa as posicoes que sobram ao outro.

    A contagem sai daqui e nao entra: o Tiago acaba com uma ou duas fotos a mais do
    que a Clara, porque as dele caem nas posicoes curtas que compensam a primeira.
    Medido a 22 de setembro, na demo_v3 e com o ritmo da intro 5: ver o que o
    script imprime.
    """
    resta = dict(disponiveis)
    tempo = {"Clara": 0.0, "Tiago": 0.0}
    seq = []
    for pos in range(min(posicoes, resta.get("Clara", 0) + resta.get("Tiago", 0))):
        # Os segundos sao somas de fotogramas de 0,04 s; sem a folga, um empate
        # exato podia sair desempatado por um arredondamento da virgula flutuante.
        quem = "Clara" if tempo["Clara"] <= tempo["Tiago"] + 1e-6 else "Tiago"
        outro = "Tiago" if quem == "Clara" else "Clara"
        if len(seq) >= SEGUIDAS_MAX and all(c == quem for c in seq[-SEGUIDAS_MAX:]):
            quem, outro = outro, quem
        if resta.get(quem, 0) <= 0:
            quem = outro
        seq.append(quem)
        resta[quem] -= 1
        tempo[quem] += segundos[pos]
    return seq


def fotos_dos_dois_etiquetadas(estado):
    """Os ids que o Tiago etiquetou na Mesa com os dois, fora os que excluiu."""
    excluidas = {k for k, sim in (estado.get("excluidas") or {}).items() if sim}
    nomes = {p.get("id"): p.get("nome") or "" for p in estado.get("pessoas") or []}
    ids = []
    for i, etiquetas in sorted((estado.get("tags") or {}).items()):
        if i in excluidas:
            continue
        clara = any("Clara" in nomes.get(p, "") for p in etiquetas)
        tiago = any("Tiago" in nomes.get(p, "") for p in etiquetas)
        if clara and tiago:
            ids.append(i)
    return ids


def escolher_fotos(estado, inv_por_id, caminho_de, versao=VERSAO, pouso=POUSO):
    """A lista da intro, pela ordem do ecra: [{id, classe, caminho, segundos}] e avisos.

    As POSICOES antes das letras, da Clara e do Tiago, repartidas por tempo de
    ecra; as de cada um amostradas por igual ao longo do filme, na quantidade que a
    reparticao pede. Depois AMBOS fotos dos dois, por ordem de ano, e no fim a foto
    de pouso, que fica. Saltam-se as fotos do pedido, a de pouso, as que nao tem
    ficheiro e as minusculas.

    AS DOS DOIS NAO CHEGAM NO FILME: a demo_v3 tem umas 34, e com as letras passam
    41. Juntam-se as que o Tiago etiquetou como dos dois na Mesa e que o filme nao
    usa (extras), sem nunca repetir nenhuma. Primeiro as etiquetadas por ele.
    """
    avisos = []
    fora = set(FOTOS_DO_PEDIDO) | {pouso}
    grupos = {"Clara": [], "Tiago": [], "Ambos": []}
    do_filme = fotos_do_filme(estado, versao)
    extras = [i for i in fotos_dos_dois_etiquetadas(estado) if i not in set(do_filme)]
    for i in do_filme + extras:
        if i in fora:
            continue
        classe = classe_da_foto(i, estado, inv_por_id)
        if classe is None:
            continue
        caminho = caminho_de.get(i)
        lado = lado_menor(caminho) if caminho else None
        if lado is None:
            avisos.append("%s sem ficheiro que abra, fica de fora" % i)
            continue
        if lado < LADO_MINIMO:
            avisos.append("%s tem %d px de lado menor, fica de fora" % (i, lado))
            continue
        grupos[classe].append(i)

    # "DESDE QUE SEJAM NOSSAS": primeiro as que o Tiago etiquetou como dos dois, as do
    # filme e depois as outras; so se faltarem entram as que so o inventario diz que
    # sao dos dois, que ai sao muitas vezes fotos de grupo com os amigos.
    etiquetadas = set(fotos_dos_dois_etiquetadas(estado))
    camadas = [[i for i in grupos["Ambos"] if i in etiquetadas and i not in set(extras)],
               [i for i in grupos["Ambos"] if i in etiquetadas and i in set(extras)],
               [i for i in grupos["Ambos"] if i not in etiquetadas]]
    ambos = []
    for camada in camadas:
        falta = AMBOS - len(ambos)
        if falta <= 0:
            break
        ambos += amostrar(camada, falta) if len(camada) > falta else camada
    if len(ambos) < AMBOS:
        avisos.append("so ha %d fotos dos dois, queria %d" % (len(ambos), AMBOS))

    def ano(i):
        try:
            return int((inv_por_id.get(i) or {}).get("ano") or 0)
        except ValueError:
            return 0
    # POR ORDEM DE ANO, e dentro do mesmo ano pela ordem do filme: e a historia dos
    # dois a andar para a frente ate a selfie de 2025.
    ordem_filme = {i: k for k, i in enumerate(do_filme + extras)}
    ambos.sort(key=lambda i: (ano(i), ordem_filme.get(i, 0)))
    disponiveis = {"Clara": len(grupos["Clara"]), "Tiago": len(grupos["Tiago"])}
    n_ct = min(POSICOES, disponiveis["Clara"] + disponiveis["Tiago"])
    if n_ct < POSICOES:
        avisos.append("so ha %d fotos da Clara e do Tiago, queria %d" % (n_ct, POSICOES))

    segundos = segundos_por_posicao(n_ct + len(ambos))
    seq = repartir_por_tempo(segundos, n_ct, disponiveis)
    # As de cada um amostram-se DEPOIS de saber quantas sao, para irem de ponta a
    # ponta do filme; amostrar mais e usar as primeiras deixava o fim de fora.
    filas = {c: amostrar(grupos[c], seq.count(c)) for c in ("Clara", "Tiago")}
    ordem = [(filas[c].pop(0), c) for c in seq] + [(i, "Ambos") for i in ambos]
    lista = [{"id": i, "classe": c, "caminho": caminho_de.get(i), "segundos": segundos[k]}
             for k, (i, c) in enumerate(ordem)]

    caminho = caminho_de.get(pouso)
    if not caminho or lado_menor(caminho) is None:
        raise ValueError("a foto de pouso %s nao tem ficheiro que abra" % pouso)
    classe = classe_da_foto(pouso, estado, inv_por_id)
    if classe != "Ambos":
        avisos.append("a foto de pouso %s nao esta etiquetada como dos dois (%s)"
                      % (pouso, classe or "sem classe"))
    # A de pouso entra no fim do folhear, ja por dentro das letras, e fica ate o
    # letreiro a tapar. Os segundos sao ate ao T_FIM.
    foco = (estado.get("focos") or {}).get(pouso) or FOCOS_POUSO.get(pouso)
    lista.append({"id": pouso, "classe": classe or "", "caminho": caminho,
                  "segundos": T_FIM - inicio_do_pouso(len(ordem)), "pouso": True,
                  "foco": tuple(foco) if foco else None})
    return lista, avisos


def selecao(versao=VERSAO, pouso=POUSO):
    """Le a Mesa, o inventario e o indice, e devolve escolher_fotos(). Sem desenhar nada."""
    with open(ESTADO_MESA, encoding="utf-8") as fh:
        estado = json.load(fh)
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv_por_id = {r["id"]: r for r in csv.DictReader(fh)}
    ids = fotos_do_filme(estado, versao)
    ids += [i for i in fotos_dos_dois_etiquetadas(estado) if i not in set(ids)]
    caminho_de, sem_indice = caminhos_das_finais(ids + [pouso], inv_por_id)
    lista, avisos = escolher_fotos(estado, inv_por_id, caminho_de, versao, pouso)
    usadas = {f["id"] for f in lista}
    for f in sorted(set(sem_indice)):
        r = next((r for r in inv_por_id.values() if r["ficheiro"] == f), None)
        if r and r["id"] in usadas:
            avisos.append("%s sem entrada no data/finais.csv, vai o original" % r["id"])
    return lista, avisos


def ffmpeg(nome="ffmpeg.exe"):
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Microsoft\WinGet\Packages"
                     r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                     r"\ffmpeg-9.0.1-full_build\bin", nome)
    if os.path.exists(p):
        return p
    from shutil import which
    return which(nome.replace(".exe", "")) or sys.exit("ffmpeg nao encontrado")


def som_da_intro(ff):
    """O som do Marvel, sem uma nota mudada.

    O ficheiro que o Tiago mandou ja nao esta nos Downloads. A unica copia do
    som esta dentro da intro de 12 de setembro, e tira-se de la sem recodificar
    (-c:a copy) para gerados\\intro_marvel\\som_marvel.m4a, uma vez so. A intro
    antiga so se le.
    """
    if os.path.exists(SOM_ORIGEM):
        return SOM_ORIGEM
    if os.path.exists(SOM_GUARDADO):
        return SOM_GUARDADO
    if not os.path.exists(INTRO_ANTIGA):
        sys.exit("Nao ha som: falta %s e falta %s." % (SOM_ORIGEM, INTRO_ANTIGA))
    os.makedirs(DESTINO, exist_ok=True)
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-n",
                        "-i", INTRO_ANTIGA, "-vn", "-c:a", "copy", SOM_GUARDADO],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(SOM_GUARDADO):
        sys.exit("ERRO a tirar o som da intro antiga: %s" % (r.stderr or "")[-300:])
    print("Som tirado da intro de 12 de setembro para %s" % SOM_GUARDADO)
    return SOM_GUARDADO


def duotone(im):
    """Cinzento com contraste forte, pintado de tinta escura a papel velho.

    E isto que faz fotografias de origens muito diferentes, digitalizacoes dos
    anos 90 ao lado de telemovel de 2026, parecerem a mesma sequencia.
    """
    g = ImageEnhance.Contrast(im.convert("L")).enhance(1.55)
    g = ImageEnhance.Brightness(g).enhance(1.06)
    paleta = []
    for i in range(256):
        f = i / 255.0
        f = f ** 0.85
        paleta += [int(TINTA[k] + (PAPEL[k] - TINTA[k]) * f) for k in range(3)]
    saida = g.convert("RGB")
    saida.putdata([tuple(paleta[3 * v:3 * v + 3]) for v in list(g.getdata())])
    return saida


def cobrir(im, larg, alt, procurar_caras=False, foco=None):
    """Enche larg x alt cortando o excesso, sem deformar.

    O CORTE DESVIA-SE PARA CIMA e a razao e uma queixa do Tiago: "na intro eu
    focava mais se possivel em caras, pois por vezes vai para pernas ou assim".
    Numa fotografia de corpo inteiro, cortar ao centro cai na cintura.

    TENTEI UMA COISA MAIS ESPERTA E NAO SE AGUENTOU. Fiz um detetor barato de
    caras, por tom de pele e detalhe, e comparei-o com o corte ao centro nas
    oito fotografias onde mais mudava o enquadramento: nao ficou melhor em
    nenhuma e ficou PIOR em duas, a cortar a cara de cima numa foto de quatro
    irmaos. O caminho errado ficou registado porque o defeito era interessante:

        foto de corpo inteiro em Nova Iorque, por faixa horizontal
          faixa da cara ........ 13% de "pele",  detalhe 5,3
          faixa dos sapatos .... 79% de "pele",  detalhe 3,1

    A regra classica de tom de pele dispara em calcada, areia, madeira e parede
    bege. "Mais pele e melhor" leva direito ao chao, que foi exatamente o que
    aconteceu: o corte passou da cara para os sapatos.

    Ficou o que se mede e se percebe: o corte comeca a 32 por cento da folga em
    vez de 50. Nunca desce abaixo do centro, portanto so pode aproximar-se das
    cabecas, nunca afastar-se delas. Numa foto ja bem enquadrada muda pouco;
    numa de corpo inteiro tira as pernas do quadro.

    COM UM PONTO DE FOCO (x, y, em fracao da foto), o corte centra-se nele, sem
    sair da foto. So a foto de pouso o usa: e a unica que fica tempo bastante para
    o enquadramento se ler.
    """
    f = max(larg / im.width, alt / im.height)
    novo = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))),
                     Image.LANCZOS)
    if foco:
        x = int(round(min(max(0.0, foco[0] * novo.width - larg / 2.0), novo.width - larg)))
        y = int(round(min(max(0.0, foco[1] * novo.height - alt / 2.0), novo.height - alt)))
        return novo.crop((x, y, x + larg, y + alt))
    x = (novo.width - larg) // 2
    folga = novo.height - alt
    y = int(round(folga * (0.32 if procurar_caras else 0.5)))
    return novo.crop((x, y, x + larg, y + alt))


def preparar(caminhos, folga=1.22, foco=None):
    """Uma vez por foto: cortar, tratar e guardar com folga para o movimento."""
    prontas = []
    for c in caminhos:
        with Image.open(c) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im = cobrir(im, int(L * folga), int(A * folga), procurar_caras=True, foco=foco)
            prontas.append(duotone(im))
    return prontas


def letreiro(largura_alvo):
    """A mascara do letreiro: "A HISTORIA DE" pequeno por cima, o nome grande.

    O Tiago pediu "algo como a historia de Clara e Tiago, mantendo este texto
    igual ao video original". O nome grande fica exatamente como estava, que e
    o que faz a citacao funcionar; a linha de cima e pequena e espacada, e
    entra como um subtitulo por cima do letreiro.
    """
    corpo = 40
    while corpo < 900:
        f = ImageFont.truetype(FONTE, corpo)
        w = f.getbbox(NOME)[2] - f.getbbox(NOME)[0]
        if w >= largura_alvo:
            break
        corpo += 4
    f = ImageFont.truetype(FONTE, corpo)
    caixa = f.getbbox(NOME)
    alt_nome = caixa[3] - caixa[1]
    m = Image.new("L", (L, A), 0)
    d = ImageDraw.Draw(m)
    y_nome = (A - alt_nome) / 2 + alt_nome * 0.10
    d.text(((L - (caixa[2] - caixa[0])) / 2 - caixa[0], y_nome - caixa[1]),
           NOME, font=f, fill=255)

    espacado = " ".join(NOME_PEQUENO)
    fp = ImageFont.truetype(FONTE_PEQUENA, max(20, int(corpo * 0.19)))
    cp = fp.getbbox(espacado)
    d.text(((L - (cp[2] - cp[0])) / 2 - cp[0],
            y_nome - alt_nome * 0.30 - (cp[3] - cp[1]) - cp[1]),
           espacado, font=fp, fill=255)
    return m


def quadro_do_pouso(foto, t, t0):
    """A foto de pouso: uma aproximacao muito lenta ao centro, de 1,0 a 1,04.

    Vai de quando entra (t0) ao T_FIM e depois para, quando o letreiro ja a tapou. O corte
    e com precisao de sub-pixel (o box do resize aceita fracoes): cortar em
    pixeis inteiros, como no folhear, fazia a foto andar aos saltos de um pixel
    a cada dois fotogramas, e numa foto que fica oito segundos isso ve-se.
    O box fica sempre dentro da foto, portanto nao ha borda a piscar.
    """
    x = max(0.0, min(1.0, (t - t0) / max(0.001, T_FIM - t0)))
    escala = 1.0 + 0.04 * x
    larg, alt = foto.width / escala, foto.height / escala
    x0, y0 = (foto.width - larg) / 2.0, (foto.height - alt) / 2.0
    return foto.resize((L, A), Image.BICUBIC, box=(x0, y0, x0 + larg, y0 + alt))


def quadro_do_folhear(fotos, i, dentro):
    """A foto i do folhear, com a sua aproximacao propria (dentro vai de 0 a 1)."""
    foto = fotos[i]

    # MOVIMENTO SEM TREMOR.
    #
    # A primeira versao calculava a fase com o relogio global, (t*7,3 + i) % 1,
    # o que dava uma serra a sete hertz: a imagem crescia e voltava ao inicio
    # varias vezes por segundo. O Tiago viu isso: "as imagens ficam a tremer ate
    # desaparecerem".
    #
    # Agora a fase e o progresso DENTRO da propria fotografia, de 0 a 1. Cada
    # uma tem uma unica aproximacao, suave, e o corte para a seguinte e limpo.
    # O folhear acaba antes das letras; por dentro delas so esta a foto de
    # pouso, com o seu movimento proprio.
    # Dentro das letras a amplitude cai quase a zero: ali as imagens estao dentro de
    # um recorte pequeno e qualquer movimento le-se como vibracao.
    escala = 1.0 + (0.085 if inicio_na_curva(i) < T_LETRAS else 0.012) * dentro
    dx = (math.sin(i * 2.1) * 0.5) * (foto.width - L / escala) * 0.5
    dy = (math.cos(i * 1.7) * 0.5) * (foto.height - A / escala) * 0.5
    larg, alt = int(L / escala), int(A / escala)
    cx = int(foto.width / 2 + dx - larg / 2)
    cy = int(foto.height / 2 + dy - alt / 2)
    cx = max(0, min(foto.width - larg, cx))
    cy = max(0, min(foto.height - alt, cy))
    return foto.crop((cx, cy, cx + larg, cy + alt)).resize((L, A), Image.BILINEAR)


def desenhar(t, fotos, pouso, mascara):
    n = len(fotos)
    if t >= T_TOTAL:
        # A pausa depois do fim: preto.
        return Image.new("RGB", (L, A), (0, 0, 0))
    if t < T_ARRANQUE:
        # O ACENDER, no mesmo corte e no mesmo sitio com que o folhear comeca: as
        # T_ARRANQUE nao ha salto nenhum, so o brilho que chega a inteiro.
        k = brilho_do_acender(t)
        tela = Image.new("RGB", (L, A), (0, 0, 0))
        if k > 0.0:
            tela = Image.blend(tela, quadro_do_folhear(fotos, 0, 0.0), k)
        return tela

    t0 = inicio_do_pouso(n)
    if t >= t0:
        quadro = quadro_do_pouso(pouso, t, t0)
    else:
        i, dentro = indice_da_foto(t, n)
        quadro = quadro_do_folhear(fotos, i, dentro)

    if t < T_LETRAS:
        return quadro

    # As letras entram por cima: o fundo passa a vermelho e a foto de pouso so
    # se ve por dentro do nome.
    k = suave((t - T_LETRAS) / max(0.001, T_SOLIDO - T_LETRAS))
    fundo = Image.new("RGB", (L, A), VERMELHO)
    fundo_misto = Image.blend(quadro, fundo, k)
    dentro = Image.composite(quadro, fundo_misto, mascara)

    if t < T_SOLIDO:
        return dentro

    # O letreiro solidifica.
    s = suave((t - T_SOLIDO) / max(0.001, T_FIM - T_SOLIDO))
    branco = Image.new("RGB", (L, A), (252, 250, 250))
    solido = Image.composite(branco, fundo, mascara)
    saida = Image.blend(dentro, solido, min(1.0, s * 1.6))

    if t >= T_FIM:
        f = suave((t - T_FIM) / max(0.001, T_TOTAL - T_FIM))
        saida = Image.blend(saida, Image.new("RGB", (L, A), (0, 0, 0)), f)
    return saida


def imprimir(lista, avisos):
    """A lista pela ordem do ecra, e o tempo de cada um."""
    print("Pos  id      classe  segundos")
    totais = {}
    for k, f in enumerate(lista):
        marca = ("   pouso: entra as %.1f s, por dentro das letras, e fica ate ao fim"
                 % inicio_do_pouso(len(lista) - 1)) if f.get("pouso") else ""
        print("%3d  %-6s  %-6s  %5.2f%s" % (k + 1, f["id"], f["classe"], f["segundos"], marca))
        if not f.get("pouso"):
            totais[f["classe"]] = totais.get(f["classe"], 0.0) + f["segundos"]
    print("Segundos no ecra durante o folhear, por classe:")
    for classe in ("Clara", "Tiago", "Ambos"):
        n = sum(1 for f in lista if f["classe"] == classe and not f.get("pouso"))
        print("  %-6s %2d fotos  %5.2f s" % (classe, n, totais.get(classe, 0.0)))
    if lista and not lista[0].get("pouso"):
        print("  (a primeira, %s, acende do preto nos %.2f s antes das %.2f; o que dela se "
              "ve ja esta na conta)" % (lista[0]["id"], T_ACENDER, T_ARRANQUE))
    for a in avisos:
        print("  aviso: %s" % a)


def argumento(nome, omissao):
    if nome in sys.argv:
        return sys.argv[sys.argv.index(nome) + 1]
    return omissao


def main():
    global L, A
    escala = argumento("--escala", None)
    if escala:
        e = float(escala)
        L, A = int(L * e) // 2 * 2, int(A * e) // 2 * 2
        print("Rascunho a %dx%d" % (L, A))
    versao = argumento("--versao", VERSAO)
    pouso = argumento("--pouso", POUSO)
    # Um rascunho nao pode ocupar o nome da versao final: a seguinte recusava.
    omissao = NOME_SAIDA.replace(".mp4", "_rascunho.mp4") if escala else NOME_SAIDA
    final = os.path.join(DESTINO, argumento("--nome", omissao))

    try:
        lista, avisos = selecao(versao, pouso)
    except ValueError as e:
        sys.exit("ERRO: %s" % e)
    print("Fotografias da %s, pela ordem do ecra:" % versao)
    imprimir(lista, avisos)
    if "--so-lista" in sys.argv:
        return

    # NUNCA POR CIMA. A intro antiga e a unica copia do som, e uma nova com o mesmo
    # nome apagava a que o Tiago ja viu. Quem quiser outra, escolhe outro nome.
    if os.path.exists(final):
        sys.exit("Ja existe %s e nao escrevo por cima.\n"
                 "Para gerar outra, da-lhe outro nome:  --nome intro_clara_tiago_3.mp4"
                 % final)

    ff = ffmpeg()
    som = som_da_intro(ff)

    folhear = [f for f in lista if not f.get("pouso")]
    print("A preparar %d fotos e a de pouso (corte, duotone, folga)..." % len(folhear))
    fotos = preparar([f["caminho"] for f in folhear])
    pouso_pronta = preparar([lista[-1]["caminho"]], folga=FOLGA_POUSO,
                            foco=lista[-1].get("foco"))[0]
    mascara = letreiro(int(L * 0.86))

    # O video intermedio fica numa pasta temporaria do sistema, fora da media.
    tmp = tempfile.mkdtemp(prefix="intro_marvel_")
    try:
        corpo = os.path.join(tmp, "_intro_corpo.mp4")
        proc = subprocess.Popen(
            [ff, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (L, A),
             "-framerate", str(FPS), "-i", "-",
             "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", corpo], stdin=subprocess.PIPE)

        duracao = T_TOTAL + T_PAUSA
        total = int(round(duracao * FPS))
        for q in range(total):
            proc.stdin.write(desenhar(q / float(FPS), fotos, pouso_pronta, mascara).tobytes())
            if q % 40 == 0:
                print("  %d/%d" % (q, total), end="\r", flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            sys.exit("ERRO: o ffmpeg nao escreveu o video")
        print("  corpo escrito        ")

        # O SOM ACABA NO T_TOTAL E A PAUSA E SILENCIO. O atrim corta no fim da
        # intro, para um som de origem mais comprido nao tocar por cima da pausa;
        # o apad enche o resto de silencio e o -t fecha tudo na duracao certa. O
        # nivel nao se mexe.
        juntado = os.path.join(tmp, "intro.mp4")
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-i", corpo, "-i", som,
                            "-map", "0:v", "-map", "1:a",
                            "-c:v", "copy",
                            "-af", "atrim=end=%.2f,apad" % T_TOTAL,
                            "-c:a", "aac", "-b:a", "192k",
                            "-t", "%.2f" % duracao, juntado],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(juntado):
            sys.exit("ERRO ao juntar o som: %s" % (r.stderr or "")[-300:])

        os.makedirs(DESTINO, exist_ok=True)
        if os.path.exists(final):
            sys.exit("Apareceu entretanto %s; nao escrevo por cima." % final)
        try:
            os.rename(juntado, final)          # no Windows falha se o destino existir
        except OSError:
            if os.path.exists(final):
                sys.exit("Apareceu entretanto %s; nao escrevo por cima." % final)
            shutil.copyfile(juntado, final)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Escrito: %s" % final)


if __name__ == "__main__":
    main()
