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
    py -3.11 scripts/render.py v3 --fatias 7       7 processos a desenhar, um encoder
    py -3.11 scripts/render.py v3 --fatias auto    os nucleos menos um, ate 8
    py -3.11 scripts/render.py v3 --guardar-quadros   deixa a cache dos videos do corpo
    py -3.11 scripts/render.py v3 --quadros-grandes   aceita mais de 30 s de video no corpo
"""
import csv
import datetime
import itertools
import json
import math
import os
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linha_tempo

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTAGENS = os.path.join(REPO, "data", "montagens")
FINAIS = r"C:\casamento-video-media\FINAIS"
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
SAIDA = r"C:\casamento-video-media\saida"
MEDIA = r"C:\casamento-video-media\trabalho\00-ORIGINAL-MAE"
# Os videos de abertura. A montagem nomeia-os na coluna `ficheiro`; estes sao
# os caminhos conhecidos. O "in_s" e onde comeca a parte util do ficheiro.
VIDEOS = {
    # O CAMINHO DA FOX ESTAVA ERRADO e ninguem dava por isso: apontava para a 02-NOVAS-MÚSICAS,
    # onde o ficheiro nao esta, e o caminho_de_video() safava-se sempre pela busca de recurso.
    # No dia em que aparecesse um ficheiro com este nome na pasta errada, a busca apanhava o
    # errado sem uma queixa. Corrigido a 23 de setembro.
    "20th Century Fox Intro HD.mp4": (
        os.path.join(MEDIA, "..", "03-NOVOS_VIDEOS", "20th Century Fox Intro HD.mp4"), 0.0),
    "Clara e Tiago-2.mp4": (os.path.join(MEDIA, "Clara e Tiago-2.mp4"), 1.796),
    "intro_clara_tiago.mp4": (
        os.path.join(r"C:\casamento-video-media\saida", "intro_clara_tiago.mp4"), 0.0),
    "intro_clara_tiago_5.mp4": (
        os.path.join(r"C:\casamento-video-media\gerados\intro_marvel",
                     "intro_clara_tiago_5.mp4"), 0.0),
    # AS COPIAS COM O SOM AO NIVEL DA MUSICA, decisao 084. Sao estas que a demo_v3 usa desde
    # 23 de setembro; os originais ficam intactos ao lado e continuam a ser encontrados pelo
    # nome de sempre. Quem as fez foi o scripts/igualar_abertura.py, por ganho directo.
    "20th Century Fox Intro HD igualado.mp4": (
        os.path.join(r"C:\casamento-video-media\gerados\som_igualado",
                     "20th Century Fox Intro HD igualado.mp4"), 0.0),
    "intro_clara_tiago_5 igualado.mp4": (
        os.path.join(r"C:\casamento-video-media\gerados\som_igualado",
                     "intro_clara_tiago_5 igualado.mp4"), 0.0),
}


def caminho_de_video(nome):
    """Encontra o ficheiro do video pelo nome, custe o que custar.

    Procura primeiro na tabela, depois em toda a pasta de media. Um video de
    abertura em falta nao pode fazer o render abortar a meio.
    """
    if nome in VIDEOS and os.path.exists(VIDEOS[nome][0]):
        return VIDEOS[nome]
    raiz = r"C:\casamento-video-media"
    for base, _, fs in os.walk(raiz):
        if "00-Backup" in base:
            continue
        for f in fs:
            if f.lower() == (nome or "").lower():
                return os.path.join(base, f), VIDEOS.get(nome, (None, 0.0))[1]
    return None, 0.0


def partir_em_fanfarra_e_corpo(clips):
    """(videos do bloco inicial, resto). UMA definicao so, para ninguem contar de outra maneira.

    ATE 17 DE SETEMBRO ERA "tipo == video" CONTRA O RESTO, e por isso um video posto a
    meio da montagem ia parar a frente do filme: os videos eram TODOS colados antes do
    corpo, com concat, e o corpo ficava com um buraco onde ele estava, porque o ciclo dos
    fotogramas, sem nenhum clip ativo, caia no ultimo do filme.

    O Tiago pediu (17 de setembro) o troco do Homer a seguir as fotos do pedido, no meio da
    abertura. Por isso a fanfarra passa a ser so o que ela sempre foi: os videos que estao
    ANTES de qualquer outro clip. Um video a seguir a um cartao, a uma foto ou a um
    contador e um clip do corpo como outro qualquer, com o seu encadeado e o seu lugar no
    relogio. Ver preparar() e extrair_quadros().

    A conta e a mesma no render, no montar_da_mesa.py e no som_para_mesa.py: tres contas
    parecidas em tres ficheiros foi como o render passou a usar a versao errada de cada
    foto, e nao se repete.
    """
    k = 0
    while k < len(clips) and clips[k]["tipo"] == "video":
        k += 1
    return clips[:k], clips[k:]


# ONDE FICAM OS FOTOGRAMAS DE UM VIDEO DO CORPO enquanto o render corre.
#
# Nao e a pasta dos renders (C:\casamento-video-media\saida): isto e trabalho temporario
# do render e mora ao lado dele, na saida do repositorio, que esta no gitignore. O
# processo principal enche a pasta ANTES de lancar as fatias e apaga-a no fim; as fatias
# so leem. Uma fatia que a criasse punha sete processos a chamar o ffmpeg sobre o mesmo
# ficheiro ao mesmo tempo, cada um a escrever por cima do outro.
#
# E UMA SUBPASTA, `saida/_cache`, E NAO A PROPRIA `saida`. A `saida` e a raiz das
# publicacoes da Mesa (root: saida, com as folhas das previas la dentro) e o link do
# artefacto so leva 255 entradas por publicacao: trabalho temporario do render, que pesa
# trinta megabytes por cada tres segundos e meio de video, nao mora onde se publica.
QUADROS = os.path.join(REPO, "saida", "_cache")

# QUANTO TEMPO UMA PASTA DE FOTOGRAMAS PODE FICAR ESQUECIDA. Um render que rebente deixa
# a sua; a corrida seguinte da MESMA montagem limpa-a pelo prefixo, mas a de outra
# montagem ficava ali para sempre. Passadas seis horas ninguem esta a renderizar aquilo
# (o filme inteiro leva minutos), e por isso e resto e apaga-se. Nao se varrem as
# recentes: dois renders de montagens DIFERENTES ao mesmo tempo sao legitimos e um nao
# pode apagar a cache do outro a meio.
SEGUNDOS_CACHE_VELHA = 6 * 3600

# QUANTO PESA UM FOTOGRAMA DA CACHE, e quanto video do corpo passa sem perguntar. Medido
# com o comando do extrair_quadros() a 1920x1080 e -q:v 2: 40 KB por fotograma no
# "Clara e Tiago-2.mp4" e 117 KB no troco do Homer, que e desenho animado e chapado. Fica
# o pior dos dois, porque o que esta em causa e nao encher o disco. Trinta segundos de
# video no corpo dao cerca de 0,1 GB e chegam de sobra para uma piada; o ficheiro inteiro
# de 1410 s que a lista do «+ Vídeo» oferece daria 4 GB. Ver cabe_no_disco().
BYTES_POR_QUADRO = 120 * 1024
SEGUNDOS_MAXIMOS_QUADROS = 30.0


def pasta_dos_quadros(nome, ordem):
    """A pasta dos fotogramas do video que esta na linha `ordem` da montagem `nome`."""
    return os.path.join(QUADROS, "_quadros_%s_%s" % (nome, ordem))


def quadros_da_cache(pasta):
    """Os JPEG da cache, pela ordem do nome, que e a ordem do tempo. Sem pasta, lista vazia."""
    if not pasta or not os.path.isdir(pasta):
        return []
    return [os.path.join(pasta, f) for f in sorted(os.listdir(pasta))
            if f.lower().endswith(".jpg")]


def extrair_quadros(ff, clip, pasta):
    """Enche `pasta` com um JPEG por fotograma do troco deste video. Devolve quantos saiu.

    O TROCO E O QUE A MESA PEDE: comeca no `in_s` da linha (o "Comeca no segundo" do
    inspetor) e dura o que a linha durar. O tamanho e o do render, que num render completo
    e 1920x1080; o scale com pad e o setsar=1 sao os mesmos da fanfarra, para um video 4:3
    entrar com barras pretas em vez de esticado, e o -r 25 poe-no na cadencia do filme,
    para o fotograma k ser mesmo o instante k/25 do clip.

    Qualidade alta de proposito (-q:v 2): isto e uma passagem intermedia e o x264 ainda vem
    a seguir. Guardar em PNG multiplicava por dez o disco sem se ver a diferenca no jantar.
    """
    origem, arranque = caminho_de_video(clip.get("ficheiro") or "")
    # A PASTA CRIA-SE SEMPRE, MESMO SEM FICHEIRO NENHUM EM DISCO.
    #
    # O nome do video pode ser escrito a mao na Mesa, e a lista dos ficheiros que ela leva
    # e um retrato do momento em que foi publicada: ele pode renomear ou mover o ficheiro
    # depois. Se nesse caso a pasta nem chegasse a existir, o preparar() de um clip de
    # video nao distinguia "o ficheiro nao esta la" de "a cache nunca foi feita" e saia com
    # sys.exit a meio de um render de quinze minutos, com uma mensagem a culpar as fatias.
    # Com a pasta criada e vazia cai na regra do imagem_da_marca(): o clip sai como sai uma
    # foto que nao abre e o nome vai para os faltaram, que o render lista no fim.
    import shutil
    shutil.rmtree(pasta, ignore_errors=True)
    os.makedirs(pasta, exist_ok=True)
    if not origem:
        return 0
    # O in_s da linha, quando vem escrito; senao o arranque da tabela VIDEOS, que e o que
    # a fanfarra de sempre usa. A linha chega do CSV, e ai tudo sao palavras.
    dentro = str(clip.get("in_s") or "").strip()
    dentro = float(dentro) if dentro else arranque
    dura = float(clip["duracao_s"])
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", "%.3f" % dentro, "-t", "%.3f" % dura, "-i", origem,
                        "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,"
                               "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1" % (L, A, L, A),
                        "-r", str(FPS), "-q:v", "2",
                        os.path.join(pasta, "q%05d.jpg")], capture_output=True, text=True)
    if r.returncode != 0:
        print("  ERRO a extrair os fotogramas de %s: %s"
              % (clip.get("ficheiro"), (r.stderr or "")[-200:]))
    return len(quadros_da_cache(pasta))


def apagar_quadros(pastas):
    """Apaga as pastas de fotogramas. Um render que rebente deixa-as, e a corrida seguinte limpa-as."""
    import shutil
    for pasta in pastas:
        shutil.rmtree(pasta, ignore_errors=True)


def cabe_no_disco(segundos_de_video):
    """Diz o que a cache vai ocupar e, se for de mais, devolve a queixa. Senao, None.

    O DEFEITO: nao havia conta nenhuma. A lista do botao «+ Vídeo» inclui o
    "Clara e Tiago-2.mp4", de 1410 s, e o botao cria o clip com duracao 0, que quer dizer
    o ficheiro inteiro; isso sao 35 250 JPEG a caminho de C:\\casamento-video\\saida, no
    disco do sistema, sem uma palavra. Medido com o mesmo comando do extrair_quadros():
    40 KB por fotograma nesse ficheiro e 117 KB no Homer, ou seja entre 1,4 e 4 GB.

    Nao se decide por ele: diz-se o tamanho e para-se, e ha uma opcao para insistir. Um
    render que enche o disco a meio nao e so um render perdido, e o PC inteiro.
    """
    quadros = int(math.ceil(segundos_de_video * FPS))
    bytes_ = quadros * BYTES_POR_QUADRO
    livre = None
    try:
        import shutil
        livre = shutil.disk_usage(os.path.dirname(QUADROS) or ".").free
    except OSError:
        pass
    quanto = "%.1f s de video no corpo, cerca de %d fotogramas e %.1f GB de cache" \
             % (segundos_de_video, quadros, bytes_ / 1e9)
    if "--quadros-grandes" in sys.argv:
        return None
    if segundos_de_video > SEGUNDOS_MAXIMOS_QUADROS:
        return ("%s. Sao mais do que os %.0f s que cabem sem perguntar: confirma o troco "
                "na Mesa, ou repete com --quadros-grandes."
                % (quanto, SEGUNDOS_MAXIMOS_QUADROS))
    if livre is not None and bytes_ > max(0, livre - 2 * 10 ** 9):
        return ("%s, e no disco so ha %.1f GB livres. Liberta espaco, ou repete com "
                "--quadros-grandes." % (quanto, livre / 1e9))
    return None


def preparar_quadros_dos_videos(ff, estado):
    """Extrai a cache de cada video do corpo. So o processo principal passa por aqui.

    Devolve as pastas criadas, para o fim do render as apagar. E ANTES DAS FATIAS porque
    cada uma delas vai abrir estes ficheiros e nenhuma os pode criar: ver preparar().
    """
    pastas = []
    # O TAMANHO DIZ-SE ANTES DE ESCREVER O PRIMEIRO FICHEIRO. Ver cabe_no_disco().
    segundos_de_video = sum(float(c["duracao_s"]) for c in estado["resto"]
                            if c["tipo"] == "video")
    if segundos_de_video > 0:
        queixa = cabe_no_disco(segundos_de_video)
        if queixa:
            sys.exit("  CACHE DOS VIDEOS DEMASIADO GRANDE: %s" % queixa)
    # Uma pasta que sobrou de um render que rebentou, de um clip que ja nao existe, so
    # ocupava disco e confundia quem fosse la ver. As dos videos de agora sao refeitas.
    #
    # E VARREM-SE TAMBEM AS DE OUTRAS MONTAGENS, mas so as velhas: a limpeza era so pelo
    # prefixo desta montagem e um resto de outra ficava ali indefinidamente. Uma pasta
    # tocada ha menos de SEGUNDOS_CACHE_VELHA pode ser de um render a correr agora ao lado,
    # e essa nao se toca.
    #
    # O NOME DA MONTAGEM COMPARA-SE POR INTEIRO, E NAO POR PREFIXO. A pasta chama-se
    # _quadros_<nome>_<ordem>, e com o teste antigo, um `startswith("_quadros_v3_")`, um
    # render do v3 dava a cache do v3_mesa como sua e apagava-a sem passar pelo teste das
    # seis horas, que existe exatamente para isso; o --nome v3_mesa esta escrito no
    # cabecalho do montar_da_mesa.py, portanto e caminho normal, nao caso raro. As fatias
    # do outro render ficavam a abrir ficheiros que ja nao existiam. O rsplit tira a
    # ordem, e o que fica e o nome da montagem, comparado tal e qual.
    meu = "_quadros_" + estado["nome"]
    if os.path.isdir(QUADROS):
        velhas = []
        for f in os.listdir(QUADROS):
            cam = os.path.join(QUADROS, f)
            if not f.startswith("_quadros_") or not os.path.isdir(cam):
                continue
            if f.rsplit("_", 1)[0] == meu:
                velhas.append(cam)
            else:
                try:
                    esquecida = time.time() - os.path.getmtime(cam) > SEGUNDOS_CACHE_VELHA
                except OSError:
                    esquecida = False
                if esquecida:
                    velhas.append(cam)
        apagar_quadros(velhas)
    for c in estado["resto"]:
        if c["tipo"] != "video":
            continue
        pasta = c["_quadros"]
        quantos = extrair_quadros(ff, c, pasta)
        pastas.append(pasta)
        precisos = int(math.ceil(float(c["duracao_s"]) * FPS))
        if not quantos:
            print("  VIDEO NO CORPO SEM FOTOGRAMAS: %s (clip %s)"
                  % (c.get("ficheiro") or "(sem nome)", c["ordem"]))
        else:
            print("  video no corpo: %s, %d fotogramas" % (c.get("ficheiro"), quantos))
            if quantos < precisos - 1:
                # O ultimo fotograma repete-se ate ao fim do clip, e isso ve-se como uma
                # imagem congelada. Vale mais ele saber agora do que no jantar.
                print("     o troco so deu %d dos %d fotogramas do clip: o fim fica parado"
                      % (quantos, precisos))
    return pastas


L, A, FPS = 1920, 1080, 25
# QUANTOS PROCESSOS DESENHAM OS FOTOGRAMAS quando ninguem diz --fatias. Sete, desde 16 de
# setembro (decisao 073): o Tiago so o queria "se realmente a qualidade for igual a que
# temos tido a fazer o render completo e se o tempo realmente baixar", e as medidas deram
# nove MP4 do filme real com o mesmo md5 com 1, 4 e 7 fatias, e 333 s a passarem a 164 s
# em 2200 fotogramas. A qualidade e a mesma por construcao: ha UM encoder, o de sempre, e
# as fatias so lhe entregam os fotogramas pela ordem, ver render_em_fatias(). --fatias 1
# continua a ser o caminho sequencial de antes.
FATIAS_OMISSAO = 7
FATIAS_MAXIMO = 8         # o que "--fatias auto" nunca passa; o os.cpu_count() conta nucleos logicos
FONTE_TEXTO = r"C:\Windows\Fonts\arialbd.ttf"
ZOOM = 0.12          # o zoom lento dela, ao centro
AFASTADA = 0.80      # enquadramento "afastada": a foto inteira a 80%, com margem
AFASTADA_RESPIRA = 0.04

# O ENQUADRAMENTO "APROXIMA", 18 de setembro. O Tiago, sobre a fotografia do anel:
# "Podes cortar e aproximar, mas tens de comecar do plano amplo para verem a arvore de
# natal". A alianca ocupa cerca de 2% da largura do ecra e a 15 metros nao se ve; a
# arvore de Natal ao fundo faz parte da historia e um corte fechado deitava-a fora.
#
# Entao nao se corta: o clip COMECA exatamente onde comecava sem enquadramento nenhum, a
# foto inteira, e fecha devagar ate ao ponto de foco. Quem ve tem o plano amplo primeiro
# e o pormenor no fim, no mesmo clip e sem um unico corte.
#
# OS LIMITES estao aqui e repetidos no montar_da_mesa.py e na Mesa, como os LIMITES_MONTE,
# e o teste_limites_do_aproxima_iguais falha se um deles mudar sozinho.
APROXIMA_OMISSAO = 2.2      # o zoom no fim, quando a Mesa nao diz outro
APROXIMA_MIN = 1.2          # abaixo disto o movimento nao se ve a 15 metros
APROXIMA_MAX = 4.0          # acima disto nem a melhor foto tem pixeis que cheguem


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


MARGEM = 2      # ver com_margem(), e a correcao do tremor na borda


def com_margem(im, modo, m=MARGEM):
    """Devolve a imagem com m pixeis a mais de cada lado.

    ISTO E A CORRECAO DO TREMOR QUE O TIAGO VIU DO LADO ESQUERDO.

    A composicao de sub-pixel pede a Pillow que amostre a fotografia numa
    posicao fracionaria. Na coluna de fora, essa posicao cai LIGEIRAMENTE FORA
    da imagem, e a Pillow nao devolve ai uma mistura: devolve preto, e devolve
    preto de repente. Medido num sprite branco puro, com escala 1:

        deslocamento 0,00  ->  coluna de fora a 255
        deslocamento 0,25  ->  coluna de fora a 255
        deslocamento 0,50  ->  coluna de fora a 255
        deslocamento 0,75  ->  coluna de fora a 0      <-- salta

    O zoom lento faz esse deslocamento variar ao longo do clip, e a coluna de
    fora acende e apaga. Uma linha preta de um pixel a piscar na vertical. E
    isso que se ve como tremor, e ve-se mais a esquerda porque nas fotos 4:3
    dentro de um ecra 16:9 as bordas verticais estao sempre dentro do quadro,
    enquanto as horizontais saem fora e sao cortadas.

    A correcao e dar a amostragem sitio onde cair, e o que la esta depende do
    que ha por tras da fotografia:

      "preto"   o fundo e preto (o aspeto dela, com barras). A borda passa a
                ser uma passagem suave da foto para o preto, que e exatamente
                o que devia ser.
      "esticar" o fundo e a propria foto desfocada. Ai o preto criava um risco
                escuro em volta, por isso repete-se a fila de fora. A borda
                fica quantizada a um pixel, o que e invisivel: durante o zoom
                ela anda a cerca de 22 pixeis por segundo.
    """
    if im.mode in ("RGBA", "RGBa"):
        # Sprite que ja traz a sua transparencia: as fotos rodadas da colagem e da
        # pilha, que chegam aqui em RGBa, pre-multiplicado. A margem e alfa zero, e
        # em pre-multiplicado zero e mesmo "nada", cor incluida: o bicubico esbate
        # a borda para o que estiver por tras sem ir buscar preto a lado nenhum.
        n = Image.new(im.mode, (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
        n.paste(im, (m, m))
        return n
    n = Image.new("RGB", (im.width + 2 * m, im.height + 2 * m), (0, 0, 0))
    n.paste(im, (m, m))
    if modo != "esticar":
        return n

    # MARGEM COM COR REPETIDA E ALFA ZERO.
    #
    # A primeira versao disto repetia so a cor, sem alfa, e o Tiago viu que o
    # tremor continuava. Tinha razao e a medida mostra porque: com a cor
    # repetida e sem alfa, a coluna da borda vale sempre 250, nos oito passos
    # de sub-pixel, e depois salta de uma vez. Ou seja a fotografia deixou de
    # piscar mas passou a ENCAIXAR de pixel em pixel, e por cima de um fundo
    # desfocado uma borda nitida a saltar de um em um pixel ve-se tao bem como
    # a linha preta que isto veio corrigir.
    #
    # A cor repetida serve para o bicubico nao ir buscar preto de lado nenhum.
    # O alfa a zero e que faz a borda esbater contra o que estiver por tras,
    # seja ele preto ou a propria foto desfocada.
    esq = im.crop((0, 0, 1, im.height)).resize((m, im.height))
    dto = im.crop((im.width - 1, 0, im.width, im.height)).resize((m, im.height))
    n.paste(esq, (0, m))
    n.paste(dto, (im.width + m, m))
    topo = n.crop((0, m, n.width, m + 1)).resize((n.width, m))
    base = n.crop((0, im.height + m - 1, n.width, im.height + m)).resize((n.width, m))
    n.paste(topo, (0, 0))
    n.paste(base, (0, im.height + m))

    alfa = Image.new("L", n.size, 0)
    alfa.paste(255, (m, m, m + im.width, m + im.height))
    n.putalpha(alfa)
    return n


def compor(tela, sprite, cx, cy, escala, alfa=1.0):
    """Coloca o sprite centrado com precisao de sub-pixel. Sem isto, treme.

    O `sprite` ja vem com margem de com_margem(), feita uma vez por clip. Por
    fotograma o custo e o mesmo de antes.

    Trabalha em RGB e cola sem mascara. As fotografias sao opacas, e compor
    com canal alfa em cada fotograma custava mais de metade do tempo de
    render sem mudar um unico pixel do resultado.

    `alfa` so conta para sprites RGBa, os da colagem e da pilha, que aparecem a
    desvanecer enquanto entram.
    """
    m = MARGEM
    larg = (sprite.width - 2 * m) * escala
    alt = (sprite.height - 2 * m) * escala
    x0, y0 = cx - larg / 2.0, cy - alt / 2.0
    ix, iy = math.floor(x0), math.floor(y0)
    fx, fy = x0 - ix, y0 - iy
    cw = int(math.ceil(larg + fx)) + m
    ch = int(math.ceil(alt + fy)) + m
    inv = 1.0 / escala
    # O +m nos dois termos constantes e o que poe a origem da fotografia
    # dentro da margem, em vez de na borda de fora.
    peca = sprite.transform((cw, ch), Image.AFFINE,
                            (inv, 0.0, -fx * inv + m, 0.0, inv, -fy * inv + m),
                            resample=Image.BICUBIC)
    px0, py0 = max(0, -ix), max(0, -iy)
    px1 = min(peca.width, tela.width - ix)
    py1 = min(peca.height, tela.height - iy)
    if px1 <= px0 or py1 <= py0:
        return
    recorte = peca.crop((px0, py0, px1, py1))
    if recorte.mode == "RGBa":
        # A foto rodada e amostrada em pre-multiplicado e so aqui volta a RGBA.
        # Amostrar em RGBA direto misturava a cor preta da parte transparente na
        # borda da moldura, e na pilha cada foto ganhava um contorno escuro.
        recorte = recorte.convert("RGBA")
        mascara = recorte.split()[3]
        if alfa < 1.0:
            mascara = mascara.point([int(v * alfa) for v in range(256)])
        tela.paste(recorte, (ix + px0, iy + py0), mascara)
    elif recorte.mode == "RGBA":
        # So o tratamento "fundo" paga este custo. No "fiel" o fundo e preto e
        # a margem preta ja da a mistura exata sem mascara nenhuma.
        tela.paste(recorte, (ix + px0, iy + py0), recorte)
    else:
        tela.paste(recorte, (ix + px0, iy + py0))


# A LINHA DO TEMPO MUDOU DE ORIENTACAO. A primeira versao corria na vertical e
# punha a data do casamento numa barra ao fundo do ecra. O Tiago corrigiu as
# duas coisas: horizontal, a fugir para a esquerda, e a data dentro da propria
# fita em vez de legenda a parte. Tudo isso vive agora em linha_tempo.py.


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


def quebrar_paragrafos(texto, fonte, largura, desenho):
    """Como quebrar(), mas cada mudanca de linha escrita na legenda fica.

    O DEFEITO: as legendas da mae com dialogo trazem uma fala por linha, e o
    render juntava tudo com " ".join(texto.split()) antes de quebrar. A frase
    saia partida a meio e as falas coladas umas as outras. Agora cada paragrafo
    quebra-se sozinho e as linhas somam-se.
    """
    linhas = []
    for paragrafo in (texto or "").splitlines():
        paragrafo = " ".join(paragrafo.split())
        if paragrafo:
            linhas += quebrar(paragrafo, fonte, largura, desenho)
    return linhas


LEGENDA_FUNDO = 34      # pixeis entre a faixa da legenda e o fundo do ecra
LEGENDA_TEXTO = 70      # pixeis entre o bloco das linhas da legenda e o fundo do ecra
LEGENDA_ALMOFADA = 26   # pixeis de faixa por cima do bloco das linhas
LEGENDA_TAMANHO = 46    # a letra da legenda de baixo, a 1080
LEGENDA_MIN = 30        # ate onde desce para caber em 4 linhas, com LEGENDA_TAMANHO
LEGENDA_LINHAS = 4
LEGENDA_ALFA = 165


def linhas_legenda(texto, tamanho=LEGENDA_TAMANHO, desenho=None):
    """Como o texto da legenda de baixo se parte: (tamanho, linhas, fonte).

    Desce de 4 em 4 ate caber em LEGENDA_LINHAS linhas, e nunca abaixo do minimo, que e
    proporcional ao tamanho pedido: LEGENDA_MIN para LEGENDA_TAMANHO. Com 46 a sequencia e
    a de sempre, 46, 42, 38, 34, 30. O tamanho vem da Mesa na opcao "na legenda de baixo";
    a legenda do grupo fica com o de sempre.
    """
    d = desenho or ImageDraw.Draw(Image.new("L", (1, 1)))
    minimo = int(math.floor(tamanho * LEGENDA_MIN / float(LEGENDA_TAMANHO) + 0.5))
    fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
    linhas = quebrar_paragrafos(texto, fonte, L - 260, d)
    while len(linhas) > LEGENDA_LINHAS and tamanho > minimo:
        tamanho = max(minimo, tamanho - 4)
        fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
        linhas = quebrar_paragrafos(texto, fonte, L - 260, d)
    return tamanho, linhas, fonte


def bloco_legenda(texto, tamanho=LEGENDA_TAMANHO):
    """Altura, em pixeis, do bloco das linhas que faixa_texto() escreve para este texto."""
    tamanho, linhas, _fonte = linhas_legenda(texto, tamanho)
    return int(tamanho * 1.35) * len(linhas)


def faixa_texto(texto, tamanho=LEGENDA_TAMANHO, bloco_max=None):
    """Desenha a legenda uma vez. Devolve (cor, mascara) para colagem rapida.

    `bloco_max` e a altura do bloco das linhas do texto mais alto que o clip vai mostrar,
    na opcao "na legenda de baixo": a faixa fica com essa altura em todo o clip, para as
    fotos nao mudarem de sitio quando o texto troca, e um texto mais baixo centra-se nela.
    Sem `bloco_max`, e com o tamanho de sempre, e a legenda de sempre, pixel a pixel.
    """
    if not texto:
        return None
    capa = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    # LEGENDA_FUNDO e a margem que a legenda guarda por baixo dela. Num projetor ou num
    # televisor com overscan os ultimos pixeis do ecra nao aparecem, e e por isso que esta
    # faixa nunca desce ate A: quem escrever outra faixa encostada ao fundo usa a mesma
    # linha, ver lado_faixas().
    tamanho, linhas, fonte = linhas_legenda(texto, tamanho, d)
    altura_linha = int(tamanho * 1.35)
    bloco = altura_linha * len(linhas)
    banda = bloco if bloco_max is None else max(bloco, bloco_max)
    topo = A - LEGENDA_TEXTO - banda + (banda - bloco) // 2
    d.rectangle([0, A - LEGENDA_TEXTO - banda - LEGENDA_ALMOFADA, L, A - LEGENDA_FUNDO],
                fill=(0, 0, 0, LEGENDA_ALFA))
    for i, linha in enumerate(linhas):
        w = d.textbbox((0, 0), linha, font=fonte)[2]
        d.text(((L - w) / 2, topo + i * altura_linha), linha, font=fonte,
               fill=(255, 255, 255, 255))
    return capa.convert("RGB"), capa.split()[3]


# ------------------------------------------------- os textos das fotos na legenda
# O Tiago, 15 de setembro: "Em vez de metermos o texto a aparecer em cada foto
# individualmente, metemos o texto master a alterar, assim pode ser uma forma mais facil
# de o texto ficar legivel. Esta e uma opcao adicional". A opcao "na legenda de baixo":
# os textos das fotos de um grupo vao para a faixa de baixo do ecra, com a letra grande da
# legenda, e a faixa troca de texto quando cada foto comeca a entrar. Nenhuma faixa dentro
# das fotos. Uma foto sem texto mostra o texto do grupo, se houver, e senao nada.
LEGENDA_TROCA = 0.2               # segundos do encadeado entre dois textos
LEGENDA_MINIMO_S = 1.5            # abaixo disto um texto nao se le a 15 metros, e avisa-se


def inicios_do_grupo(tipo, n, duracao, cross_entra=0.0, cross_sai=0.0):
    """Instante em que cada foto de um grupo comeca a entrar, em segundos do clip.

    No lado a lado e o atraso de cada celula; na colagem e na pilha e a agenda de
    agenda_monte(), com os encadeados. E a mesma conta que o desenho usa.
    """
    if tipo == "lado":
        return [LADO_ATRASO + k * LADO_INTERVALO for k in range(n)]
    inicios, _entrada = agenda_monte(n, duracao, COLAGEM_ENTRADA if tipo == "colagem" else PILHA_ENTRADA,
                                     cross_entra=cross_entra, cross_sai=cross_sai)
    return inicios


def tempos_da_agenda(inicios, duracao):
    """[(inicio, fim)] do texto de cada foto: desde que ela comeca a entrar ate a seguinte comecar.

    O da primeira comeca no zero, antes de ela entrar; o da ultima vai ate ao fim do clip.
    Na colagem e na pilha isto e a vez de cada foto de agenda_monte(): a ultima fica com as
    duas vezes que a agenda lhe da, mais o encadeado de saida.
    """
    n = len(inicios)
    return [(0.0 if k == 0 else inicios[k], inicios[k + 1] if k + 1 < n else duracao)
            for k in range(n)]


def tempos_legenda_grupo(tipo, n, duracao, cross_entra=0.0, cross_sai=0.0, estilo=None):
    """Quanto tempo o texto de cada foto fica na legenda de baixo: [(inicio, fim)] em segundos do clip.

    `tipo` e lado, colagem ou pilha, `n` quantas fotos (no lado a lado pode vir None com o
    `estilo` a dizer a disposicao), e os encadeados sao os de encadeados_do_corpo(). O
    estilo nao muda a agenda; aceita-se para a Mesa e o montar_da_mesa.py fazerem a mesma
    chamada com o que tem a mao.
    """
    if tipo == "lado" and n is None:
        n = LAYOUTS_LADO[estilo]
    return tempos_da_agenda(inicios_do_grupo(tipo, n, duracao, cross_entra, cross_sai), duracao)


def legendas_curtas(textos, tempos, minimo=LEGENDA_MINIMO_S):
    """[(k, texto, segundos)] dos textos que ficam menos de `minimo` na legenda de baixo.

    Textos iguais seguidos nao trocam, por isso somam-se: "Natal" em duas fotos de 1 s fica
    2 s no ecra. Os trocos sem texto nao contam, nao ha nada para ler.

    O CLIP PODE ACABAR ANTES DE UMA FOTO ENTRAR: no lado a lado as celulas entram aos 0,35 +
    k x 0,45 s, aconteca o que acontecer a duracao, e num 4q de 1,5 s a quarta entra aos
    1,7 s. O tempo de cada texto conta-se so ate ao fim do clip, que e o fim do ultimo
    troco; um texto cuja foto entra depois do fim vem com segundos NEGATIVOS, quanto
    depois do fim ela entra, e quem avisa diz que nunca aparece. Antes disto a ultima dava
    "fica so -0.2 s" e uma do meio dava 0,4 s de um texto que ninguem via.
    """
    saida, k = [], 0
    fim_do_clip = tempos[-1][1] if tempos else 0.0
    while k < len(textos):
        j = k
        while j + 1 < len(textos) and textos[j + 1] == textos[k]:
            j += 1
        dura = min(tempos[j][1], fim_do_clip) - tempos[k][0]
        if textos[k] and dura < minimo - 1e-9:
            saida.append((k, textos[k], dura))
        k = j + 1
    return saida


def avisar_legenda_curta(k, texto, dura):
    if dura <= 1e-9:
        print("  AVISO: o texto da foto %d do grupo nunca aparece na legenda de baixo: a foto so "
              "entra %.1f s depois de o clip acabar: %s" % (k + 1, max(0.0, -dura), texto))
        return
    print("  AVISO: o texto da foto %d do grupo fica so %.1f s na legenda de baixo, e a 15 "
          "metros nao da para ler: %s" % (k + 1, dura, texto))


def legenda_por_foto(textos, tamanho=LEGENDA_TAMANHO):
    """As faixas da opcao "na legenda de baixo", desenhadas uma vez por clip.

    `textos` e o que a legenda mostra em cada foto, ja com o texto do grupo no lugar dos
    vazios. Devolve {"textos", "faixas": {texto: (cor, mascara)}, "topo", "fundo"}, ou None
    se nao houver texto nenhum. Todas as faixas tem a altura do bloco mais alto, para as
    fotos pousarem acima dela e nao mudarem de sitio quando o texto troca.
    """
    distintos = [t for t in dict.fromkeys(textos) if t]
    if not distintos:
        return None
    banda = max(bloco_legenda(t, tamanho) for t in distintos)
    # O retangulo de faixa_texto() inclui a fila A - LEGENDA_FUNDO, por isso `fundo`, a
    # primeira fila abaixo da banda, e essa mais um: sem o mais um, a ultima fila da
    # faixa ficava fora da mistura da troca e piscava.
    return {"textos": list(textos), "tamanho": tamanho,
            "faixas": {t: faixa_texto(t, tamanho, banda) for t in distintos},
            "topo": A - LEGENDA_TEXTO - banda - LEGENDA_ALMOFADA, "fundo": A - LEGENDA_FUNDO + 1,
            "_bandas": {}}


def _banda_premultiplicada(legenda, texto):
    """A faixa de um texto, so as filas da banda, em RGBa: e nisto que duas se misturam."""
    if texto not in legenda["_bandas"]:
        topo, fundo = legenda["topo"], legenda["fundo"]
        capa = legenda["faixas"].get(texto)
        if capa is None:
            banda = Image.new("RGBa", (L, fundo - topo), (0, 0, 0, 0))
        else:
            cor, mascara = capa
            rgba = cor.crop((0, topo, L, fundo)).copy()
            rgba.putalpha(mascara.crop((0, topo, L, fundo)))
            banda = rgba.convert("RGBa")
        legenda["_bandas"][texto] = banda
    return legenda["_bandas"][texto]


def troca_da_legenda(tempos, i):
    """Quanto dura o encadeado para o texto da foto i: LEGENDA_TROCA, ou menos se a foto seguinte entra antes.

    `tempos` sao os de tempos_da_agenda(). A Mesa faz a mesma conta em legendaDoPalco().
    """
    troca = LEGENDA_TROCA
    if i + 1 < len(tempos):
        troca = min(troca, tempos[i + 1][0] - tempos[i][0])
    return max(0.0, troca)


def legenda_no_instante(pronto, t_rel, duracao, inicios):
    """O que se cola por cima no fim do fotograma: (cor, mascara, onde), ou None.

    Sem a opcao legenda e a capa do grupo de sempre, em (0, 0). Com ela, a faixa do texto
    da foto cujo troco contem t_rel, ver tempos_da_agenda(). Na troca entre dois textos
    diferentes ha LEGENDA_TROCA segundos de encadeado: as duas faixas misturam-se em
    pre-multiplicado, que e a mistura exata dos dois fotogramas compostos, e por isso a
    faixa escura, igual nas duas, nao pisca; so desvanece quando se passa de texto para
    nenhum ou o contrario. Textos iguais seguidos nao trocam.

    E CADA TROCA ACABA ANTES DE A SEGUINTE COMECAR. Numa pilha de 8 em 2 s as fotos entram
    de 0,186 em 0,186 s, menos do que LEGENDA_TROCA: a troca seguinte partia do texto
    anterior inteiro quando a legenda ainda estava a 78% dele, e a banda dava um salto de
    um fotograma para o outro. O encadeado encurta ao intervalo ate a foto seguinte, ver
    troca_da_legenda(), e assim no instante em que uma troca comeca a anterior ja esta
    completa. So muda alguma coisa em clips apertados de mais, que ja levam os avisos.
    """
    legenda = pronto.get("legenda")
    if legenda is None:
        capa = pronto.get("capa")
        return None if capa is None else (capa[0], capa[1], (0, 0))
    textos = legenda["textos"]
    tempos = tempos_da_agenda(inicios, duracao)
    i = 0
    for k, (inicio, _fim) in enumerate(tempos):
        if t_rel >= inicio:
            i = k
    atual = textos[i]
    anterior = textos[i - 1] if i > 0 else atual
    troca = troca_da_legenda(tempos, i)
    f = (t_rel - tempos[i][0]) / troca if troca > 0 else 1.0
    if anterior == atual or f >= 1.0:
        capa = legenda["faixas"].get(atual)
        return None if capa is None else (capa[0], capa[1], (0, 0))
    mistura = Image.blend(_banda_premultiplicada(legenda, anterior),
                          _banda_premultiplicada(legenda, atual), max(0.0, min(1.0, f)))
    mistura = mistura.convert("RGBA")
    return mistura.convert("RGB"), mistura.split()[3], (0, legenda["topo"])


def colar_legenda(tela, pronto, t_rel, duracao, inicios):
    """Cola a legenda de baixo no fotograma, a de sempre ou a da opcao legenda."""
    faixa = legenda_no_instante(pronto, t_rel, duracao, inicios)
    if faixa is not None:
        cor, mascara, onde = faixa
        tela.paste(cor, onde, mascara)


def cartao(texto):
    base = Image.new("RGB", (L, A), (8, 8, 10))
    d = ImageDraw.Draw(base)
    tamanho = 78
    fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
    linhas = quebrar_paragrafos(texto, fonte, L - 360, d)
    while len(linhas) > 4 and tamanho > 44:
        tamanho -= 6
        fonte = ImageFont.truetype(FONTE_TEXTO, tamanho)
        linhas = quebrar_paragrafos(texto, fonte, L - 360, d)
    altura_linha = int(tamanho * 1.4)
    topo = (A - altura_linha * len(linhas)) / 2
    for i, linha in enumerate(linhas):
        w = d.textbbox((0, 0), linha, font=fonte)[2]
        d.text(((L - w) / 2, topo + i * altura_linha), linha, font=fonte,
               fill=(238, 238, 244))
    return base


# ---------------------------------------------------------- texto em cada foto
# O Tiago: "permite colocar o texto nas fotos mesmo as que ficam em leque e assim, tem
# de ser opcional ter o texto ou nao". Um grupo (lado a lado, colagem, pilha) tinha uma
# legenda so, a faixa de baixo do ecra, e ao juntar fotos na Mesa o texto de cada uma
# perdia-se. Agora cada foto do grupo pode trazer o seu, numa faixa escura DENTRO da
# propria fotografia: na colagem e na pilha e desenhada na foto antes da moldura e da
# rotacao, por isso roda, entra e e tapada com ela. A legenda do grupo fica como estava.
# Sem textos o caminho de desenho e o de antes e nenhum pixel muda.
#
# O TAMANHO CONTA NO ECRA, COM A FOTO POUSADA. A 15 metros, abaixo do minimo nao se le:
# primeiro desce-se o tamanho para caber em TEXTO_FOTO_LINHAS linhas, e so depois se
# corta com reticencias, com aviso.
#
# O TAMANHO E O DA LEGENDA, E O TIAGO PODE MUDA-LO. Comecou em 36, e ele: "permite tambem
# que eu possa selecionar o tamanho que quero". A omissao passou a 46, o da legenda de
# baixo, e o minimo a que se desce e proporcional ao escolhido, TEXTO_FOTO_MIN_FRACAO: 46
# da 36, 36 da 28, que era o par de antes. A Mesa guarda a escolha em `tt` e o CSV em
# textos_opcoes, ver ler_textos_opcoes().
TEXTO_FOTO_TAMANHO = 46           # pixeis do ecra a 1080 de altura, omissao
TEXTO_FOTO_MIN_FRACAO = 0.78      # o minimo e esta fracao do tamanho escolhido
TEXTO_FOTO_TAMANHOS = (28, 90)    # o que a Mesa deixa escolher; fora disto fica a omissao
TEXTO_FOTO_LINHAS = 2
TEXTO_FOTO_FOLGA = 16             # entre o texto e cada borda da foto, a 1080
TEXTO_FOTO_ALFA = 165             # o da faixa da legenda
TEXTO_FOTO_ENTRELINHA = 1.2
TEXTO_FOTO_ALMOFADA = 0.3         # por cima e por baixo do texto, fracao do tamanho
TEXTO_FOTO_TAPADO = 0.10          # acima disto tapado pelas seguintes, avisa-se (pilha com "fica")
TEXTO_FOTO_PISADA = 0.01          # a partir disto uma faixa da colagem conta como pisada pelas seguintes
TEXTO_FOTO_SOME = 0.2             # segundos que o texto de uma foto da pilha leva a desaparecer
RETICENCIAS = "…"
_FONTES = {}


def minimo_texto_foto(tamanho=None):
    """Ate onde a letra do texto de uma foto desce, a 1080, para o tamanho escolhido."""
    tamanho = TEXTO_FOTO_TAMANHO if tamanho is None else tamanho
    # floor(x + 0.5) e nao round(): o round() do Python arredonda 58,5 para 58 e o
    # Math.round da Mesa para 59, e o tamanho tem de ser o mesmo nos dois.
    return int(math.floor(TEXTO_FOTO_MIN_FRACAO * tamanho + 0.5))


TEXTO_FOTO_MIN = minimo_texto_foto()      # 36, o minimo da omissao

# As opcoes dos textos das fotos, coluna textos_opcoes do CSV. So se escreve o que difere
# da omissao, e o render aceita a coluna vazia, ausente ou com so algumas chaves.
#   modo     "foto" (em cada foto) ou "legenda" (na legenda de baixo, a mudar com cada foto)
#   tamanho  a letra, em pixeis a 1080, entre TEXTO_FOTO_TAMANHOS
#   tapadas  na pilha com "foto": "some" (o texto de uma foto desaparece quando a seguinte
#            cai por cima) ou "fica" (fica la, tapado como a propria foto)
OPCOES_TEXTO = {"modo": "foto", "tamanho": TEXTO_FOTO_TAMANHO, "tapadas": "some"}
OPCOES_TEXTO_VALORES = {"modo": ("foto", "legenda"), "tapadas": ("some", "fica")}


def _fonte(tamanho):
    if tamanho not in _FONTES:
        _FONTES[tamanho] = ImageFont.truetype(FONTE_TEXTO, tamanho)
    return _FONTES[tamanho]


def no_ecra(pixeis_a_1080):
    """Uma medida escrita para 1080 de altura, no ecra deste render."""
    return max(1, int(round(pixeis_a_1080 * A / 1080.0)))


def ler_textos_opcoes(valor):
    """A coluna textos_opcoes: '{"modo": "legenda", "tamanho": 56}' -> as opcoes completas.

    Aceita a coluna vazia ou ausente, um JSON ou um dicionario ja lido. O que nao se
    conhece, ou nao e valido, fica na omissao COM AVISO: uma opcao mal escrita que caisse
    em silencio na omissao era um texto a sair de outra maneira sem ninguem saber porque.
    """
    opcoes = dict(OPCOES_TEXTO)
    if valor is None or valor == "":
        return opcoes
    lido = valor
    if not isinstance(valor, dict):
        try:
            lido = json.loads(valor)
        except (TypeError, ValueError):
            print("  AVISO: textos_opcoes ilegivel, ficam as opcoes de omissao: %r" % (valor,))
            return opcoes
    if not isinstance(lido, dict):
        print("  AVISO: textos_opcoes nao e um objeto, ficam as opcoes de omissao: %r" % (valor,))
        return opcoes
    for chave, v in lido.items():
        if chave in OPCOES_TEXTO_VALORES:
            if v in OPCOES_TEXTO_VALORES[chave]:
                opcoes[chave] = v
            else:
                print("  AVISO: textos_opcoes com %s=%r desconhecido, fica %r"
                      % (chave, v, OPCOES_TEXTO[chave]))
        elif chave == "tamanho":
            inteiro = (isinstance(v, int) and not isinstance(v, bool)) or \
                      (isinstance(v, float) and v.is_integer())
            if inteiro and TEXTO_FOTO_TAMANHOS[0] <= v <= TEXTO_FOTO_TAMANHOS[1]:
                opcoes["tamanho"] = int(v)
            else:
                print("  AVISO: textos_opcoes com tamanho %r, tem de ser inteiro entre %d e %d, fica %d"
                      % (v, TEXTO_FOTO_TAMANHOS[0], TEXTO_FOTO_TAMANHOS[1], TEXTO_FOTO_TAMANHO))
        else:
            print("  AVISO: textos_opcoes com a chave %r desconhecida, ignorada" % (chave,))
    return opcoes


def ler_textos_fotos(valor):
    """A coluna textos_fotos: '["Natal", ""]' -> ["Natal", ""]. Vazio, invalido ou todos vazios -> None."""
    lista = valor
    if not isinstance(valor, list):
        try:
            lista = json.loads(valor or "")
        except (TypeError, ValueError):
            return None
    if not isinstance(lista, list):
        return None
    textos = []
    for t in lista:
        if isinstance(t, str):
            textos.append(t.strip())
        elif isinstance(t, (int, float)) and not isinstance(t, bool):
            # Um ano escrito sem aspas no JSON. SEM A PARTE DECIMAL quando nao a tem: 2019.0
            # saia escrito "2019.0" na fotografia. O texto_de_xf() do montar_da_mesa.py faz
            # a mesma conta, e o booleano nao e texto nenhum nos dois.
            textos.append("%d" % t if float(t).is_integer() else str(t))
        else:
            textos.append("")
    return textos if any(textos) else None


def textos_do_grupo(textos, n):
    """Um texto por foto, n ao todo: a lista curta completa-se com vazios e a comprida corta-se.

    Devolve None quando nao ha nenhum texto, que e o que faz o desenho seguir o caminho
    de antes. O montar_da_mesa.py ja avisa das listas de outro tamanho.
    """
    if not textos:
        return None
    lista = [t.strip() if isinstance(t, str) else "" for t in list(textos)[:n]]
    lista += [""] * (n - len(lista))
    return lista if any(lista) else None


def linhas_texto_foto(texto, largura_px, tamanho=None):
    """Como o texto de uma foto cabe na largura dela: (tamanho, linhas, cortado).

    `largura_px` e a largura da foto no ecra final, pousada, e o tamanho vem em pixeis
    desse ecra, escalado com A. Comeca em `tamanho` (a 1080; TEXTO_FOTO_TAMANHO se nao
    vier) e desce de 2 em 2 ate minimo_texto_foto(tamanho), ate caber em TEXTO_FOTO_LINHAS
    linhas na largura menos a folga de cada lado. Se nem assim cabe, fica no minimo, a
    ultima linha leva o resto e acaba em reticencias, e `cortado` e True para quem prepara
    avisar. Uma palavra sozinha mais larga do que a foto tambem e cortada: nada se escreve
    fora da fotografia.
    """
    tamanho = TEXTO_FOTO_TAMANHO if tamanho is None else tamanho
    grande, pequeno = no_ecra(tamanho), no_ecra(minimo_texto_foto(tamanho))
    texto = (texto or "").strip()
    if not texto:
        return grande, [], False
    # OS PARAGRAFOS A MAIS JUNTAM-SE ANTES DE ESCOLHER O TAMANHO. Uma legenda da mae com
    # tres linhas curtas ("Natal\n2019\nPorto") nunca cabia em duas linhas, a letra descia
    # ao minimo sem faltar largura nenhuma e so depois se juntavam a 2.a e a 3.a, sem
    # aviso. Agora a descida so acontece por falta de largura. A Mesa faz o mesmo.
    paragrafos = [p for p in (" ".join(l.split()) for l in texto.splitlines()) if p]
    if len(paragrafos) > TEXTO_FOTO_LINHAS:
        paragrafos = paragrafos[:TEXTO_FOTO_LINHAS - 1] + [" ".join(paragrafos[TEXTO_FOTO_LINHAS - 1:])]
    texto = "\n".join(paragrafos)
    cabe = max(1.0, largura_px - 2 * no_ecra(TEXTO_FOTO_FOLGA))
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tamanho = grande
    while True:
        fonte = _fonte(tamanho)
        linhas = quebrar_paragrafos(texto, fonte, cabe, d)
        if (len(linhas) <= TEXTO_FOTO_LINHAS
                and all(d.textbbox((0, 0), l, font=fonte)[2] <= cabe for l in linhas)):
            return tamanho, linhas, False
        if tamanho <= pequeno:
            break
        tamanho = max(pequeno, tamanho - 2)
    if len(linhas) > TEXTO_FOTO_LINHAS:
        linhas = linhas[:TEXTO_FOTO_LINHAS - 1] + [" ".join(linhas[TEXTO_FOTO_LINHAS - 1:])]
    cortado = False
    for i, linha in enumerate(linhas):
        if d.textbbox((0, 0), linha, font=fonte)[2] <= cabe:
            continue
        while linha and d.textbbox((0, 0), linha.rstrip() + RETICENCIAS, font=fonte)[2] > cabe:
            linha = linha[:-1]
        linhas[i] = linha.rstrip() + RETICENCIAS
        cortado = True
    return tamanho, linhas, cortado


def largura_do_texto(largura_ecra, pisa=0.0):
    """A largura onde o texto de uma foto se conta: a da foto, menos a orla que a seguinte pode tapar."""
    return largura_ecra * (1.0 - 2.0 * pisa)


def capa_texto_foto(texto, largura, largura_ecra=None, pisa=0.0, tamanho=None):
    """A faixa do texto de uma foto, desenhada uma vez: (faixa RGBA da largura da foto, cortado).

    `largura` e a da imagem onde a faixa vai ser colada e `largura_ecra` a da foto pousada
    no ecra, quando nao sao a mesma: o sprite da colagem e feito COLAGEM_RESPIRA maior do
    que pousa, e o texto tem de sair no ecra com o tamanho que linhas_texto_foto() deu.
    Preto com o alfa da legenda e letra branca, como faixa_texto(). `tamanho` e a letra
    escolhida na Mesa, a 1080, ver linhas_texto_foto().

    `pisa` e a fracao de cada lado da foto que uma foto que chega depois pode tapar. A
    faixa continua com a largura da foto, mas o texto conta-se e centra-se sem essa orla.
    """
    largura = max(1, int(round(largura)))
    ecra = float(largura if largura_ecra is None else largura_ecra) or float(largura)
    tamanho, linhas, cortado = linhas_texto_foto(texto, largura_do_texto(ecra, pisa), tamanho)
    s = largura / ecra
    fonte = _fonte(max(1, int(round(tamanho * s))))
    alt_linha = int(round(tamanho * s * TEXTO_FOTO_ENTRELINHA))
    almofada = int(round(tamanho * s * TEXTO_FOTO_ALMOFADA))
    capa = Image.new("RGBA", (largura, len(linhas) * alt_linha + 2 * almofada),
                     (0, 0, 0, TEXTO_FOTO_ALFA))
    d = ImageDraw.Draw(capa)
    for i, linha in enumerate(linhas):
        d.text((largura / 2.0, almofada + (i + 0.5) * alt_linha), linha, font=fonte,
               fill=(255, 255, 255, 255), anchor="mm")
    return capa, cortado


def colocar_faixa(texto, largura, altura, largura_ecra=None, foco=None, pisa=0.0, sobe=0.0,
                  tamanho=None, em_cima=False):
    """Onde a faixa do texto fica dentro de uma foto de `largura` x `altura`: (capa, topo, altura, cortado).

    UMA CONTA SO, para quem desenha e para quem precisa de saber onde ela ficou sem
    desenhar: o faixa_na_foto() cola a capa e o preparar_monte() mede a zona dela no ecra,
    com a foto pousada, para ver se alguma das seguintes a tapa. Com duas contas, a medida
    e o desenho podiam discordar sem ninguem dar por isso.

    `sobe` e a fracao da altura da foto que a faixa sobe do fundo, e `pisa` o de
    capa_texto_foto(). Se o ponto de foco que o Tiago marcou cai na zona da faixa, a faixa
    vai para o topo: o foco e onde esta a cara, e uma faixa preta por cima dela a 15
    metros tapa-a. `em_cima` manda-a para o topo sem foco nenhum: e o que a colagem faz
    quando uma foto seguinte pisa a zona da faixa em baixo, ver sitio_da_faixa_na_colagem().
    """
    capa, cortado = capa_texto_foto(texto, largura, largura_ecra, pisa, tamanho)
    alt = min(capa.height, int(round(altura)))
    y = max(0, int(round(altura * (1.0 - sobe))) - alt)
    if em_cima or (foco is not None and foco[1] * altura >= y):
        y = 0
    return capa, y, alt, cortado


def faixa_na_foto(foto, texto, largura_ecra=None, foco=None, pisa=0.0, sobe=0.0, tamanho=None,
                  em_cima=False):
    """Desenha a faixa do texto na propria foto: devolve (topo da faixa, cortado). Ver colocar_faixa()."""
    capa, y, _alt, cortado = colocar_faixa(texto, foto.width, foto.height, largura_ecra,
                                           foco, pisa, sobe, tamanho, em_cima)
    foto.paste(capa.convert("RGB"), (0, y), capa.split()[3])
    return y, cortado


def avisar_texto_pisado(k, texto, fracao):
    print("  AVISO: a faixa do texto da foto %d do grupo e pisada pelas fotos que chegam depois, "
          "em baixo e em cima (%d%%), e fica em baixo: %s" % (k + 1, int(round(100 * fracao)), texto))


def avisar_texto_cortado(k, texto):
    print("  AVISO: o texto da foto %d do grupo nao cabe e fica cortado: %s" % (k + 1, texto))


def avisar_texto_tapado(k, texto, fracao):
    print("  AVISO: %d%% do texto da foto %d do grupo fica tapado pelas fotos que chegam "
          "depois, e a 15 metros le-se outra palavra: %s"
          % (int(round(100 * fracao)), k + 1, texto))


def cobrir(im, larg, alt):
    """Enche larg x alt cortando o excesso, sem deformar."""
    f = max(larg / im.width, alt / im.height)
    novo = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))),
                     Image.LANCZOS)
    x = (novo.width - larg) // 2
    y = (novo.height - alt) // 2
    return novo.crop((x, y, x + larg, y + alt))


# ---------------------------------------------------------------- lado a lado
# O Tiago: "permitir colocar fotos tipo lado a lado. Gostava de conseguir ter no
# maximo ate 4, sendo que ai seriam mais ou menos 4 retangulos iguais, mas queria
# que tenham movimento a entrar e que fiquem todas no ecra apos todas entrarem.
# Se forem 3 pode dividir em dois e a ultima aparece por cima ou colocar o ecra
# dividido em 3 iguais na vertical. Tambem quero dividir na vertical em dois."
LADO_FOLGA = 8          # linha preta entre as fotos, para se lerem como fotos
LADO_ENTRADA = 0.9      # segundos que cada foto leva a entrar
LADO_INTERVALO = 0.45   # atraso entre a entrada de uma e da seguinte
LADO_ATRASO = 0.35      # a primeira espera que o encadeado de entrada acabe
LADO_ZOOM = 0.04        # respiracao lenta depois de pousar
# O 6g e de 17 de setembro, quando o Tiago pediu mais fotos em cada tratamento: duas filas
# de tres, as celulas do 3v em altura e as do 4q em largura. Os mesmos nomes e numeros estao
# no montar_da_mesa.py e no LADO_N da Mesa.
LAYOUTS_LADO = {"2v": 2, "3v": 3, "3s": 3, "4q": 4, "6g": 6}


def lado_celulas(lay):
    """Retangulos (x, y, w, h) de cada foto e o lado por onde ela entra.

    A direcao escolhe-se para nenhuma foto atravessar outra ao entrar: as das
    pontas vem de fora pelo lado delas, a do meio e a de cima sobem de baixo. No 6g a do
    meio de cima sobe pela coluna do meio antes de a do meio de baixo entrar (entram a
    LADO_INTERVALO uma da outra, pela ordem das celulas), por isso tambem nao atravessa
    nenhuma.
    """
    W, H, g = L, A, LADO_FOLGA
    if lay == "2v":
        w = (W - g) // 2
        return [((0, 0, w, H), "esq"), ((W - w, 0, w, H), "dir")]
    if lay == "3v":
        w = (W - 2 * g) // 3
        return [((0, 0, w, H), "esq"), ((w + g, 0, W - 2 * (w + g), H), "baixo"),
                ((W - w, 0, w, H), "dir")]
    if lay == "4q":
        w, h = (W - g) // 2, (H - g) // 2
        return [((0, 0, w, h), "esq"), ((W - w, 0, w, h), "dir"),
                ((0, H - h, w, h), "esq"), ((W - w, H - h, w, h), "dir")]
    if lay == "3s":
        w = (W - g) // 2
        cw, ch = int(W * 0.46), int(H * 0.66)
        return [((0, 0, w, H), "esq"), ((W - w, 0, w, H), "dir"),
                (((W - cw) // 2, (H - ch) // 2, cw, ch), "baixo")]
    if lay == "6g":
        w, h = (W - 2 * g) // 3, (H - g) // 2
        meio = W - 2 * (w + g)
        return [((0, 0, w, h), "esq"), ((w + g, 0, meio, h), "baixo"), ((W - w, 0, w, h), "dir"),
                ((0, H - h, w, h), "esq"), ((w + g, H - h, meio, h), "baixo"), ((W - w, H - h, w, h), "dir")]
    raise ValueError("disposicao desconhecida: %r" % (lay,))


def cobrir_alto(im, larg, alt, vies=0.32):
    """Como cobrir(), mas quando corta em altura guarda mais o cimo da foto.

    E o desvio da abertura, decisao 033: numa celula larga uma foto em pe perde
    o cimo ou os pes, e as caras estao quase sempre no terco de cima.
    """
    f = max(larg / im.width, alt / im.height)
    novo = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))),
                     Image.LANCZOS)
    x = (novo.width - larg) // 2
    y = int((novo.height - alt) * vies)
    return novo.crop((x, y, x + larg, y + alt))


def ler_foco(texto):
    """"0.4120,0.3050" -> (0.412, 0.305). Vazio ou mal escrito -> None."""
    try:
        fx, fy = [float(v) for v in (texto or "").split(",")]
    except Exception:
        return None
    return (min(1.0, max(0.0, fx)), min(1.0, max(0.0, fy)))


def cobrir_foco(im, larg, alt, foco):
    """Enche larg x alt com a janela centrada no ponto de foco que o Tiago marcou.

    O PEDIDO: "Tens de me permitir ajustar o ponto do foco da foto, caso contrario
    pode acontecer de sugerires zona em que corta a pessoa". O corte automatico
    guarda o centro e um pouco mais o cimo, e no ensaio de 14 de setembro uma
    selfie a dois numa coluna estreita ficou com uma das caras cortada. A janela
    nunca sai da foto: junto a uma borda, encosta a essa borda.
    """
    if foco is None:
        return None
    nw, nh, x, y = janela_foco(im.size, larg, alt, foco)
    novo = im.resize((nw, nh), Image.LANCZOS)
    return novo.crop((x, y, x + larg, y + alt))


def janela_foco(tamanho, larg, alt, foco):
    """As contas de cobrir_foco(): (largura e altura ampliadas, x e y da janela).

    A parte. O texto de cada foto do lado a lado precisa de saber onde o foco cai
    dentro da celula, e uma segunda copia destas contas acabava por divergir.
    """
    f = max(larg / tamanho[0], alt / tamanho[1])
    nw, nh = max(1, round(tamanho[0] * f)), max(1, round(tamanho[1] * f))
    x = int(round(foco[0] * nw - larg / 2.0))
    y = int(round(foco[1] * nh - alt / 2.0))
    return nw, nh, max(0, min(nw - larg, x)), max(0, min(nh - alt, y))


# ------------------------------------------------------------ colagem e pilha
# Os tratamentos B e D da decisao 017, que o Tiago aprovou a 10 de setembro no
# ensaio do teste_estilos.py e que nunca tinham chegado ao render. A Mesa passa a
# escreve-los e ele pediu-os:
#   colagem  as fotos entram uma a uma, com moldura branca e ligeiramente tortas,
#            e FICAM. No fim o quadro inteiro respira com um zoom lento.
#   pilha    caem umas sobre as outras, tortas. Nada desaparece, o monte cresce.
#
# O ensaio tinha tempos fixos e cinco posicoes escritas a mao. Aqui e a Mesa que
# escolhe a duracao e quantas fotos, por isso a agenda e a disposicao sao contas.
# O aspeto, esse, e o do ensaio: foto inteira, moldura clara, os mesmos angulos,
# a mesma chegada. Nenhuma foto e cortada, e por isso o ponto de foco nao serve
# para recortar: na colagem serve para nenhuma foto que chega depois tapar o
# sitio que o Tiago marcou numa que ja la esta.
MOLDURA_COR = (240, 240, 242)     # a do ensaio
# O Tiago, 17 de setembro: "aumenta a quantidade das fotos possiveis nas diferentes opcoes
# no tratamento, em especial a colagem e a pilha". Eram 2 a 5 e 2 a 8. Os mesmos numeros
# estao no montar_da_mesa.py e no GRUPOS da Mesa, e o teste_limites_dos_grupos_iguais
# falha se um dos tres mudar sozinho. A Mesa avisa, sem impedir, a partir de 9 na colagem
# e de 13 na pilha: a 15 metros cada foto fica pequena de mais.
LIMITES_MONTE = {"colagem": (2, 12), "pilha": (2, 20)}
MONTE_ATRASO = 0.35               # a primeira espera o encadeado, como no lado a lado
MONTE_FOLGA = 1.4                 # a duracao minima: segundos com todas pousadas, ver duracao_minima_monte()
MONTE_FRACAO_FIM = 0.3            # so no aperto e na agenda de antes, ver _agenda_de_antes()
COLAGEM_ENTRADA = 0.32            # do ensaio
COLAGEM_CHEGA = 1.14              # escala de chegada, do ensaio
COLAGEM_RESPIRA = 0.03            # zoom lento do conjunto no fim, do ensaio
COLAGEM_INTERVALO_MAX = 1.6       # so na agenda de antes, ver agenda_monte_antiga()
COLAGEM_ANGULOS = (-3.5, 2.5, 2.0, -2.0, 4.0)     # os do ensaio
COLAGEM_CRESCE = 1.10             # cada foto cresce sobre a folga e pisa a vizinha
COLAGEM_DESVIOS = ((-0.008, 0.012), (0.009, -0.014), (-0.006, 0.016),
                   (0.008, -0.010), (-0.010, -0.012))   # fracoes de L e de A
PILHA_ENTRADA = 0.40              # do ensaio
PILHA_CHEGA = 1.16                # do ensaio
PILHA_QUEDA = 0.12                # cai de 130 pixeis acima, fracao de A
PILHA_AFASTA = 0.10               # o monte recua 10% no fim, do ensaio
PILHA_INTERVALO_MAX = 1.3         # so na agenda de antes, ver agenda_monte_antiga()
PILHA_ANGULOS = (-9, 6, -4, 11, -7, 3, -12, 8)   # os do ensaio
PILHA_LARG, PILHA_ALT = 0.50, 0.64               # caixa de cada foto, fracao do ecra
MONTE_BORDA = 0.012               # distancia minima ao bordo do ecra, fracao de A


def pousar(t):
    """Travagem no fim, a do ensaio: a foto chega depressa e assenta devagar."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def arrancar(t):
    """Arranca parado e acaba em andamento.

    O ensaio comecava o zoom final com pousar(), que arranca na velocidade maxima:
    num quadro parado ha segundo e meio, isso le-se como um solavanco. Este sai do
    repouso e chega ao fim do clip a andar, como o zoom lento das outras fotos.
    """
    t = max(0.0, min(1.0, t))
    return t * t * (2.0 - t)


MONTE_PISA = 0.08                 # a que chega depois tapa no maximo 8% de cada lado da de baixo
MONTE_RAIO_FOCO = 0.045           # meia largura da zona guardada a volta do foco, fracao de A
MONTE_LEGENDA_FOLGA = 0.02        # entre as fotos e a faixa da legenda, fracao de A
MONTE_PAUSA = 0.10                # cada foto fica parada isto antes de a seguinte comecar
MONTE_FOLGA_MIN = 0.6             # num clip curto de mais, parada isto antes do encadeado de saida
MONTE_ENTRADA_MIN = 0.12          # nem a entrada, 3 fotogramas
COLAGEM_POR_LINHA = 5             # ate COLAGEM_POUCAS fotos, ver colagem_particoes()
COLAGEM_TOLERANCIA = 0.90         # abdica-se ate 10% da area por uma foto mais pequena maior
COLAGEM_MENOR_BANDA = 0.95        # ...mas so entre as que dao quase a melhor foto mais pequena
COLAGEM_POUCAS = 5                # ate aqui experimentam-se todas as particoes, como sempre
COLAGEM_MUITAS_LINHAS = 4         # com mais fotos, filas equilibradas: ate 4 filas...
COLAGEM_MUITAS_POR_LINHA = 6      # ...de ate 6 fotos cada


def vez_do_monte(n, duracao, cross_entra=0.0, cross_sai=0.0):
    """A vez de cada foto de uma colagem ou pilha, em segundos: ver agenda_monte().

    (duracao - espera pelo encadeado de entrada - encadeado de saida) / (n + 1). A Mesa
    mostra-a ao lado da Duracao, "cerca de X s por foto, a ultima o dobro", e reduz uma
    colagem ou pilha tirando uma vez a duracao; e esta a conta das duas.
    """
    return (duracao - max(MONTE_ATRASO, cross_entra) - cross_sai) / float(n + 1)


def agenda_monte(n, duracao, entrada, atraso=MONTE_ATRASO, cross_entra=0.0, cross_sai=0.0):
    """Instante em que cada foto comeca a entrar, e quanto dura a entrada.

    O PEDIDO, do Tiago a 17 de setembro: "nestes casos das colagens e da pilha permite que
    ao aumentar a duracao o que faca seja dividir o tempo pelo numero de fotos
    selecionadas", e logo a seguir "Pode ser com a ultima a ficar o dobro, e provavelmente
    tambem a primeira tem de descontar um bocadinho, caso contrario a primeira nunca tem o
    efeito". A agenda de antes, agenda_monte_antiga(), espalhava as entradas so ate 1,6 s
    na colagem e 1,3 s na pilha e deixava o resto para o fim com todas pousadas: numa pilha
    de 8 em 19 s as fotos entravam em 10 s e ficavam 9 s paradas. Aumentar a duracao so
    alongava o fim.

    A REGRA: vez = (duracao - atraso - sai) / (n + 1), com atraso = max(MONTE_ATRASO,
    cross_entra) e sai = cross_sai. A foto k comeca a entrar em atraso + k x vez. Cada foto
    tem a sua vez, da sua entrada ate a seguinte comecar, e A ULTIMA TEM DUAS, ate ao
    encadeado de saida, para se ver o conjunto completo. Sem intervalo maximo: o dobro da
    duracao e o dobro do tempo de cada foto.

    O ENCADEADO DE ENTRADA DESCONTA-SE ANTES DE DIVIDIR, e e esse o "descontar um bocadinho":
    a primeira so comeca a entrar depois de o clip anterior ter saido de todo, e tem a vez
    inteira com o efeito a vista. Sem isso a entrada dela acontecia por baixo do encadeado.
    `cross_entra` e zero no primeiro clip do corpo e `cross_sai` e o fade a preto de 2,5 s no
    ultimo, ver encadeados_do_corpo().

    NENHUMA FOTO E TAPADA ANTES DE PARAR. A entrada dura min(entrada, vez - MONTE_PAUSA), e
    assim cada foto fica parada pelo menos MONTE_PAUSA antes de a seguinte comecar, nunca
    abaixo de MONTE_ENTRADA_MIN. A respiracao da colagem e o recuo da pilha fazem-se depois
    de a ultima pousar, ate ao fim do clip, ver estado_monte().

    QUANDO O CLIP NAO CHEGA, com a vez abaixo de MONTE_ENTRADA_MIN + MONTE_PAUSA, aperta-se
    como antes, pelos passos de _agenda_de_antes(). A Mesa avisa bem antes disso, com
    duracao_minima_monte(), cuja formula nao mudou.
    """
    atraso = max(atraso, cross_entra)
    vez = (duracao - atraso - cross_sai) / float(n + 1)      # a conta de vez_do_monte()
    if vez < MONTE_ENTRADA_MIN + MONTE_PAUSA - 1e-9:
        # No aperto os intervalos ja sao a entrada mais a pausa, abaixo de qualquer maximo:
        # sem maximo nenhum da exatamente os numeros da agenda de antes.
        return _agenda_de_antes(n, duracao, entrada, float("inf"), atraso, cross_sai)
    return ([atraso + k * vez for k in range(n)],
            max(MONTE_ENTRADA_MIN, min(entrada, vez - MONTE_PAUSA)))


def agenda_monte_antiga(n, duracao, entrada, intervalo_max, atraso=MONTE_ATRASO,
                        cross_entra=0.0, cross_sai=0.0):
    """A agenda de ANTES de 17 de setembro, a letra. O render ja nao a usa.

    Fica para a prova de que a agenda nova so mudou o tempo: o render de agora com esta
    injetada da os fotogramas do render de antes, ao byte. Com tempo de sobra as entradas
    espalhavam-se ate intervalo_max (COLAGEM_INTERVALO_MAX ou PILHA_INTERVALO_MAX) e o
    resto ficava para o fim, com todas pousadas; ver _agenda_de_antes().
    """
    return _agenda_de_antes(n, duracao, entrada, intervalo_max, max(atraso, cross_entra), cross_sai)


def _agenda_de_antes(n, duracao, entrada, intervalo_max, atraso, cross_sai):
    """O corpo da agenda de antes, com o atraso ja a contar o encadeado de entrada.

    A REGRA DE ENTAO: todas pousadas com pelo menos MONTE_FOLGA segundos de clip pela
    frente (ou MONTE_FRACAO_FIM do clip, se for mais), mais o encadeado de saida, e as
    entradas espalhadas ate intervalo_max. A agenda nova so usa daqui o aperto.

    O ENCADEADO CONTA. `atraso` ja vem com o encadeado com o clip de antes e `cross_sai` e
    o do clip seguinte. A primeira versao ignorava-os: a primeira foto entrava aos 0,35 s,
    a meio de um encadeado de 0,7 s, e a folga do fim era comida pelo encadeado de saida.

    NENHUMA FOTO E TAPADA ANTES DE PARAR. Numa pilha de 8 em 3 a 5 s as entradas
    apertavam-se ate cada foto comecar a ser tapada pela seguinte antes de pousar,
    e havia fotos que so se viam a 0-4%. O intervalo entre entradas nunca e menor do
    que a entrada mais MONTE_PAUSA.

    QUANDO O CLIP NAO CHEGA, encolhe-se por esta ordem, cada passo so ate ao seu
    minimo e so se o anterior nao chegou:
      1. a folga do fim, mas so ate ao encadeado de saida mais MONTE_FOLGA_MIN: as
         fotos ficam sempre paradas e inteiras um bocado antes de o clip seguinte
         comecar a aparecer. A versao anterior levava-a ate 0,4 s contados com o
         encadeado, e num encadeado de 0,7 s a ultima foto pousava ja a desvanecer;
      2. a entrada, ate MONTE_ENTRADA_MIN;
      3. a espera pelo encadeado de entrada, ate zero;
      4. a folga que sobra dentro do encadeado de saida, ate MONTE_FOLGA_MIN;
      5. e so se nem assim couber se apertam as entradas e as pausas por igual.
    """
    folga = max(MONTE_FOLGA, MONTE_FRACAO_FIM * duracao) + cross_sai
    pausa = MONTE_PAUSA if n > 1 else 0.0

    def falta():
        return atraso + n * entrada + (n - 1) * pausa + folga - duracao

    def encolhe(valor, minimo, partes=1):
        """O valor menos o que falta, repartido por `partes`, sem descer abaixo do minimo."""
        if falta() <= 0:
            return valor
        return max(min(valor, minimo), valor - falta() / partes)

    folga = encolhe(folga, cross_sai + MONTE_FOLGA_MIN)
    entrada = encolhe(entrada, MONTE_ENTRADA_MIN, n)
    atraso = encolhe(atraso, 0.0)
    folga = encolhe(folga, MONTE_FOLGA_MIN)
    # Tolerancia e nao "> 0": depois dos passos anteriores falta() fica em 1e-16 e este
    # passo disparava na mesma, com um k maior do que 1 por esquecer o atraso. As entradas
    # cresciam em vez de encolher e a ultima foto pousava depois do fim do clip.
    if falta() > 1e-9:
        pedem = n * entrada + (n - 1) * pausa
        k = min(1.0, max(0.0, duracao - folga - atraso) / pedem) if pedem > 0 else 0.0
        entrada, pausa = entrada * k, pausa * k
    disponivel = max(0.0, duracao - folga)
    janela = max(0.0, disponivel - atraso - entrada)
    intervalo = 0.0
    if n > 1:
        intervalo = max(entrada + pausa, min(intervalo_max, janela / (n - 1)))
    return [atraso + i * intervalo for i in range(n)], entrada


def duracao_minima_monte(tipo, n, cross_entra=0.0, cross_sai=0.0):
    """Segundos que uma colagem ou pilha de n fotos precisa, e abaixo dos quais se avisa.

    A espera pelo encadeado, cada entrada inteira com a sua pausa, e MONTE_FOLGA de
    todas paradas antes do encadeado com o clip seguinte. Era onde a agenda de antes
    comecava a encolher; a agenda nova so aperta muito abaixo disto, ver agenda_monte(),
    mas a formula ficou, de proposito: e a que a Mesa e o montar_da_mesa.py usam para
    avisar o Tiago, e um aviso que mudasse de numero sem nada mudar no video confundia.
    Por isso e esta e mais nenhuma:

        max(MONTE_ATRASO, entra) + n x entrada + (n - 1) x MONTE_PAUSA + MONTE_FOLGA + sai

    `cross_entra` e `cross_sai` sao os de encadeados_do_corpo(): zero a entrar no
    primeiro clip do corpo, e FADE_FIM_IMAGEM a sair do ultimo clip do filme.
    """
    entrada = COLAGEM_ENTRADA if tipo == "colagem" else PILHA_ENTRADA
    return (max(MONTE_ATRASO, cross_entra) + n * entrada + (n - 1) * MONTE_PAUSA
            + MONTE_FOLGA + cross_sai)


def moldura_monte(larg, alt):
    """Espessura da moldura: a do ensaio, 8 a 9 pixeis em fotos de 600, a escala."""
    return max(6, int(round(0.016 * min(larg, alt))))


def caixa_rodada(larg, alt, angulo):
    """Meia largura e meia altura do retangulo depois de rodado."""
    c, s = abs(math.cos(math.radians(angulo))), abs(math.sin(math.radians(angulo)))
    return (larg * c + alt * s) / 2.0, (larg * s + alt * c) / 2.0


def cantos(cx, cy, meia_l, meia_a, angulo):
    """Os quatro cantos de um retangulo rodado como a Pillow roda, contra o relogio."""
    a = math.radians(angulo)
    c, s = math.cos(a), math.sin(a)
    return [(cx + u * c + v * s, cy - u * s + v * c)
            for u, v in ((-meia_l, -meia_a), (meia_l, -meia_a),
                         (meia_l, meia_a), (-meia_l, meia_a))]


def contorno_monte(f):
    """Os cantos de fora da moldura de uma foto pousada [cx, cy, largura, altura, angulo]."""
    t = moldura_monte(f[2], f[3])
    return cantos(f[0], f[1], f[2] / 2.0 + t, f[3] / 2.0 + t, f[4])


def meter_no_quadro(cx, cy, meia_l, meia_a, zoom):
    """Desloca o centro para a caixa, com o conjunto em `zoom` ao centro, caber no ecra."""
    borda = MONTE_BORDA * A

    def eixo(c, meia, lado):
        lo = lado / 2.0 + (borda + meia * zoom - lado / 2.0) / zoom
        hi = lado / 2.0 + (lado - borda - meia * zoom - lado / 2.0) / zoom
        return lado / 2.0 if lo > hi else min(hi, max(lo, c))

    return eixo(cx, meia_l, L), eixo(cy, meia_a, A)


def afastar(fixo, movel):
    """Quanto mover o poligono `movel` para deixar de pisar `fixo`, ou None se nao pisa.

    Dois convexos nao se tocam se houver uma direcao em que as sombras deles nao se
    cruzam. Das direcoes das arestas escolhe-se a que pede o empurrao mais curto, com
    um pixel de seguranca.

    Cada maximo e minimo das sombras conta-se uma vez: com 12 fotos numa espalhada isto corre
    centenas de milhares de vezes. As contas sao as mesmas, pela mesma ordem, e dao os mesmos
    numeros ao byte.
    """
    melhor = None
    melhor_abs = 0.0
    nf, nm = len(fixo), len(movel)
    for poli in (fixo, movel):
        lados = len(poli)
        for k in range(lados):
            x1, y1 = poli[k]
            x2, y2 = poli[(k + 1) % lados]
            nx, ny = y2 - y1, x1 - x2
            norma = math.hypot(nx, ny)
            if norma == 0:
                continue
            nx, ny = nx / norma, ny / norma
            pf = [x * nx + y * ny for x, y in fixo]
            pm = [x * nx + y * ny for x, y in movel]
            max_f, min_m = max(pf), min(pm)
            if max_f <= min_m:
                return None
            max_m, min_f = max(pm), min(pf)
            if max_m <= min_f:
                return None
            if sum(pm) / nm >= sum(pf) / nf:
                d = max_f - min_m + 1.0
            else:
                d = -(max_m - min_f + 1.0)
            if melhor is None or abs(d) < melhor_abs:
                melhor, melhor_abs = (d, nx, ny), abs(d)
    return melhor[0] * melhor[1], melhor[0] * melhor[2]


LONGE_FOLGA = 1e-3               # pixeis entre duas caixas para afastar() dar None de certeza


def caixa_de(poli):
    """(x0, y0, x1, y1) da caixa de um poligono, direita."""
    xs = [p[0] for p in poli]
    ys = [p[1] for p in poli]
    return min(xs), min(ys), max(xs), max(ys)


def longe(a, b):
    """Se as caixas de dois poligonos estao afastadas mais do que LONGE_FOLGA: entao afastar() da None.

    PORQUE E CERTO, E NAO SO RAPIDO: duas caixas separadas por g separam os poligonos por pelo
    menos g. Na diferenca de Minkowski de dois retangulos, as arestas tem as normais das
    arestas dos dois, e com a origem de fora a distancia d o ponto mais perto e uma aresta
    (sombra separada por d nessa normal) ou um canto, e ai a direcao para a origem fica entre
    as normais das duas arestas do canto, que em dois retangulos nunca fazem mais de 90 graus:
    a menos de 45 graus de uma delas, sombra separada por pelo menos 0,7 d. Com g de uma
    milesima de pixel, nenhum arredondamento de 1e-12 da a volta a isso, e afastar() encontra
    essa direcao e devolve None.
    """
    return (a[2] + LONGE_FOLGA < b[0] or b[2] + LONGE_FOLGA < a[0]
            or a[3] + LONGE_FOLGA < b[1] or b[3] + LONGE_FOLGA < a[1])


def dentro_do_poligono(ponto, poli):
    """Se o ponto cai dentro de um poligono convexo com os cantos por ordem."""
    x, y = ponto
    lados = [(p2[0] - p1[0]) * (y - p1[1]) - (p2[1] - p1[1]) * (x - p1[0])
             for p1, p2 in zip(poli, poli[1:] + poli[:1])]
    return all(v >= 0 for v in lados) or all(v <= 0 for v in lados)


def zona_da_faixa(lugar, topo, alt, largura):
    """Os cantos da faixa de texto de uma foto pousada [cx, cy, w, h, ang], em coordenadas do ecra.

    `topo` e `alt` sao os de colocar_faixa(), contados do cimo da foto, e `largura` a do
    texto, que na colagem ja vem sem a orla. O v roda como em colagem_guardado().
    """
    cx, cy, _w, h, ang = lugar
    a = math.radians(ang)
    v = topo + alt / 2.0 - h / 2.0
    return cantos(cx + v * math.sin(a), cy + v * math.cos(a), largura / 2.0, alt / 2.0, ang)


def parte_tapada(zona, contornos, passos=(24, 8)):
    """Fracao da zona que os contornos tapam, por amostragem regular em quadricula.

    PORQUE SE MEDE: uma faixa de texto meio tapada nao da erro nenhum, sai no video com
    meia palavra e le-se outra coisa. Na pilha as fotos tapam-se de proposito e so se
    avisa; na colagem a faixa sobe para a orla que ninguem pisa e isto confirma-o.
    """
    nu, nv = passos
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = zona
    tapados = 0
    for i in range(nu):
        u = (i + 0.5) / nu
        x0, y0 = ax + (bx - ax) * u, ay + (by - ay) * u
        x1, y1 = dx + (cx - dx) * u, dy + (cy - dy) * u
        for j in range(nv):
            v = (j + 0.5) / nv
            p = (x0 + (x1 - x0) * v, y0 + (y1 - y0) * v)
            if any(dentro_do_poligono(p, c) for c in contornos):
                tapados += 1
    return tapados / float(nu * nv)


def encaixar_grupo(fotos, x0, y0, x1, y1, zoom):
    """Encolhe e centra o conjunto para caber em (x0, y0, x1, y1) com `zoom` ao centro do ecra.

    O DEFEITO QUE ISTO SUBSTITUI: cada foto era empurrada para dentro do ecra sozinha,
    para caber a chegar e a respirar. Numa colagem que ja enche o ecra, empurrar para
    dentro e empurrar para cima da vizinha: nos fotogramas de controlo com fotos reais
    a segunda fila tapava a primeira em quase um terco, e a cara da Clara na foto das
    cataratas desaparecia. Escalar o conjunto inteiro guarda as distancias entre as
    fotos, e com elas o que cada uma tapa da outra.
    """
    ax0, ax1 = L / 2.0 + (x0 - L / 2.0) / zoom, L / 2.0 + (x1 - L / 2.0) / zoom
    ay0, ay1 = A / 2.0 + (y0 - A / 2.0) / zoom, A / 2.0 + (y1 - A / 2.0) / zoom
    for _ in range(6):
        pontos = [p for f in fotos for p in contorno_monte(f)]
        bx0, bx1 = min(p[0] for p in pontos), max(p[0] for p in pontos)
        by0, by1 = min(p[1] for p in pontos), max(p[1] for p in pontos)
        s = min(1.0, (ax1 - ax0) / (bx1 - bx0), (ay1 - ay0) / (by1 - by0))
        mx, my = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
        tx, ty = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
        if s > 0.9999 and abs(mx - tx) < 0.01 and abs(my - ty) < 0.01:
            break
        for f in fotos:
            f[0] = tx + (f[0] - mx) * s
            f[1] = ty + (f[1] - my) * s
            f[2] *= s
            f[3] *= s
    return fotos


def colagem_particoes(n):
    """As maneiras de partir as n fotos da colagem em filas, pela ordem: listas de filas de indices.

    ATE COLAGEM_POUCAS FOTOS, TODAS, como sempre: ate 3 filas de ate COLAGEM_POR_LINHA, pela
    ordem de itertools.product, que e a que desempata quando duas dao o mesmo.

    COM MAIS, SO FILAS EQUILIBRADAS: de 1 a COLAGEM_MUITAS_LINHAS filas, todas com o mesmo
    numero de fotos ou mais uma, ate COLAGEM_MUITAS_POR_LINHA. Com todas as particoes, os
    pesos que dao as filas curtas mais altura faziam de 8 fotos 4:3 uma fila de 2 com 22% do
    ecra cada e uma de 6 com 2,7%, e a regra da mais pequena nao as apanhava porque a outra
    ficava 20% abaixo em area. Medido em 6, 8, 10 e 12 fotos, 4:3, 3:4, 2:3, 16:9,
    panoramicas e duas misturas, com e sem legenda, contra todas as particoes de ate 3 filas
    de 5: a mais pequena nunca ficou menor; a area de todas desceu em tres formas
    panoramicas, a troco da mais pequena passar de 2% para 4 a 10% do ecra; e 12 verticais
    passam de tres filas de 4 com 40% do ecra para duas de 6 com 61%. E sao no maximo umas
    dezenas de particoes, em vez de pesar as 2048 de 12 fotos.
    """
    if n <= COLAGEM_POUCAS:
        for cortes in itertools.product((False, True), repeat=n - 1):
            linhas = [[0]]
            for i, corta in enumerate(cortes, 1):
                if corta:
                    linhas.append([i])
                else:
                    linhas[-1].append(i)
            if len(linhas) > 3 or max(len(l) for l in linhas) > COLAGEM_POR_LINHA:
                continue
            yield linhas
        return
    for filas in range(1, COLAGEM_MUITAS_LINHAS + 1):
        base, resto = divmod(n, filas)
        if base + (1 if resto else 0) > COLAGEM_MUITAS_POR_LINHA:
            continue
        for mais in itertools.combinations(range(filas), resto):
            linhas, k = [], 0
            for f in range(filas):
                conta = base + (1 if f in mais else 0)
                linhas.append(list(range(k, k + conta)))
                k += conta
            yield linhas


def colagem_disposicao(aspetos, focos=None, livre_ate=None):
    """Onde pousa cada foto da colagem: [cx, cy, largura, altura, angulo].

    Largura e altura sao da foto sem moldura, pousada, antes de respirar. `livre_ate`
    e a linha do ecra onde comeca a faixa da legenda, quando ha legenda.

    POR LINHAS, PELA ORDEM DA MESA. Experimentam-se as maneiras de partir a sequencia
    em linhas de colagem_particoes(), ate 5 fotos todas as de ate 3 linhas de ate
    COLAGEM_POR_LINHA fotos, e fica a que da mais area de fotografia, com o desempate de
    baixo. As linhas com menos fotos
    ficam mais altas, que e o que da ao quadro os tamanhos variados do ensaio em vez
    de uma grelha. Como cada
    linha e feita com as proporcoes verdadeiras, uma vertical no meio de horizontais
    nao deixa buraco: a linha dela e que se ajusta.

    A AREA QUE CONTA E A DO FIM, depois de afastar e encaixar. A primeira versao
    escolhia pela area antes disso e com ate 3 fotos por linha: 4 ou 5 verticais
    ficavam em duas filas que se empurravam uma a outra, o conjunto encolhia para
    caber, e as fotos acabavam com 18 a 21% do ecra. Numa fila so de 5 nao ha nada a
    empurrar na vertical e ficam com mais do dobro.

    A FOTO MAIS PEQUENA CONTA PELO TAMANHO, NAO PELA RAZAO. Entre as particoes que dao
    pelo menos COLAGEM_TOLERANCIA da maior area, fica a que da mais a foto mais
    pequena. A regra antes era multiplicar a area por 0,6 quando a mais pequena tinha
    menos de 30% da maior, e uma razao nao sabe de tamanhos: numa colagem de 16:9, 2:3,
    2:3, 16:9 e 3:4 com legenda preferia uma fila so com todas mais pequenas, a mais
    pequena tambem, e as fotos passavam de 43% para 26% do ecra. Sem regra nenhuma, uma
    16:9 sozinha numa fila deixava tres verticais com menos de 4% do ecra; com esta, por
    menos de 2% de area, ficam duas filas de duas e a mais pequena quase com o dobro.

    Depois cada foto cresce COLAGEM_CRESCE sobre a folga e desvia-se um pouco, para
    pisar a vizinha como numa colagem a mao. O que pisa sao as orlas: uma foto que
    chega depois nunca entra no miolo de uma que ja la esta, que e onde estao as
    caras, e so pode tapar ate MONTE_PISA de cada lado dela. Se o Tiago marcou um
    ponto de foco, tambem a volta dele fica a descoberto. No fim o conjunto inteiro
    encolhe o que for preciso para caber no ecra ja a respirar, e acima da legenda.
    """
    n = len(aspetos)
    mx, my = 0.035 * L, 0.05 * A
    baixo = A - my if livre_ate is None else max(0.5 * A, min(A - my, livre_ate))
    g = 0.018 * L
    larg_util, alt_util = L - 2 * mx, baixo - my
    focos = focos or []
    opcoes = []
    for linhas in colagem_particoes(n):
        tetos = [(larg_util - g * (len(l) - 1)) / sum(aspetos[i] for i in l) for l in linhas]
        pesos = [1.0 / math.sqrt(len(l)) for l in linhas]
        disponivel = alt_util - g * (len(linhas) - 1)
        # Enche como agua: cada linha sobe com o seu peso ate bater no teto dela.
        lo, hi = 0.0, max(t / p for t, p in zip(tetos, pesos))
        for _ in range(60):
            meio = (lo + hi) / 2.0
            if sum(min(t, meio * p) for t, p in zip(tetos, pesos)) > disponivel:
                hi = meio
            else:
                lo = meio
        alturas = [min(t, lo * p) for t, p in zip(tetos, pesos)]
        fotos = _colagem_assentar(aspetos, focos, linhas, alturas, (mx, my, g, alt_util, baixo))
        areas = [f[2] * f[3] for f in fotos]
        opcoes.append((sum(areas), min(areas), fotos))
    # Uma foto minuscula ao lado de uma enorme nao e colagem, e engano: das que dao quase
    # tanta area como a melhor, fica a de maior foto mais pequena.
    # Mas nao a troco de nada: o maximo estrito da mais pequena chegava a abdicar de 5 a
    # 10% da area para a mais pequena crescer 0,5%. Dentro da banda, ficam as que chegam a
    # COLAGEM_MENOR_BANDA da melhor foto mais pequena, e dessas a de maior area.
    topo = max(total for total, _menor, _fotos in opcoes)
    banda = [o for o in opcoes if o[0] >= COLAGEM_TOLERANCIA * topo - 1e-6]
    melhor_menor = max(menor for _total, menor, _fotos in banda)
    finalistas = [o for o in banda if o[1] >= COLAGEM_MENOR_BANDA * melhor_menor - 1e-9]
    return max(finalistas, key=lambda o: o[0])[2]


def _colagem_assentar(aspetos, focos, linhas, alturas, medidas):
    """Uma particao da colagem ja assente: empurrada para nao tapar caras e encaixada no ecra."""
    mx, my, g, alt_util, baixo = medidas
    n = len(aspetos)
    fotos = [None] * n
    y = my + (alt_util - sum(alturas) - g * (len(linhas) - 1)) / 2.0
    for l, h in zip(linhas, alturas):
        x = (L - sum(aspetos[i] * h for i in l) - g * (len(l) - 1)) / 2.0
        for i in l:
            w = aspetos[i] * h
            dx, dy = COLAGEM_DESVIOS[i % len(COLAGEM_DESVIOS)]
            fotos[i] = [x + w / 2.0 + dx * L, y + h / 2.0 + dy * A,
                        w * COLAGEM_CRESCE, h * COLAGEM_CRESCE,
                        COLAGEM_ANGULOS[i % len(COLAGEM_ANGULOS)]]
            x += w + g
        y += h + g
    colagem_afastar(fotos, focos, (mx, my, L - mx, baixo))
    return fotos


def colagem_guardado(fotos, focos, i):
    """O que da foto i nenhuma das seguintes pode tapar: o miolo e a volta do foco."""
    cx, cy, w, h, ang = fotos[i]
    zonas = [cantos(cx, cy, w * (0.5 - MONTE_PISA), h * (0.5 - MONTE_PISA), ang)]
    foco = focos[i] if i < len(focos) else None
    if foco is not None:
        a = math.radians(ang)
        u, v = (foco[0] - 0.5) * w, (foco[1] - 0.5) * h
        raio = MONTE_RAIO_FOCO * A
        zonas.append(cantos(cx + u * math.cos(a) + v * math.sin(a),
                            cy - u * math.sin(a) + v * math.cos(a), raio, raio, ang))
    return zonas


def colagem_afastar(fotos, focos, quadro):
    """Empurra as que chegam depois para fora do guardado das de baixo e encaixa no quadro.

    Devolve True quando a ultima volta ja nao empurrou nada, que e quando a garantia vale.
    Serve as duas colagens: a das filas e a espalhada.
    """
    x0, y0, x1, y1 = quadro
    n = len(fotos)
    # Empurra a que chegou depois pelo caminho mais curto e volta a encaixar o
    # conjunto no ecra. Encolher o conjunto por igual nao faz ninguem voltar a pisar
    # ninguem, por isso quando uma volta ja nao empurra nada o resultado e final.
    #
    # AS CONTAS SAO AS DE SEMPRE, SO NAO SE REPETEM. Com 12 fotos uma espalhada levava 23 s,
    # quase tudo em afastar() entre fotos que estao longe uma da outra. As zonas guardadas
    # de uma foto nao mudam enquanto as seguintes sao empurradas, por isso fazem-se uma vez
    # por volta; e duas caixas afastadas nao se pisam, ver longe(). Os numeros sao os mesmos,
    # ao byte, e e isso que a prova das disposicoes de antes confirma.
    for _volta in range(10):
        mexeu = False
        guardadas = []
        for j in range(1, n):
            guardadas.extend((zona, caixa_de(zona)) for zona in colagem_guardado(fotos, focos, j - 1))
            contorno = contorno_monte(fotos[j])
            caixa = caixa_de(contorno)
            for _passo in range(8):
                empurrou = False
                for zona, caixa_zona in guardadas:
                    if longe(caixa_zona, caixa):
                        continue
                    d = afastar(zona, contorno)
                    if d:
                        fotos[j][0] += d[0]
                        fotos[j][1] += d[1]
                        empurrou = mexeu = True
                        contorno = contorno_monte(fotos[j])
                        caixa = caixa_de(contorno)
                if not empurrou:
                    break
        encaixar_grupo(fotos, x0, y0, x1, y1, 1.0 + COLAGEM_RESPIRA)
        if not mexeu:
            return True
    return False


# ------------------------------------------------------- os estilos de cada um
# Decisao 068. O Tiago, perguntado se queria a colagem em filas ou espalhada e a pilha
# tapada ou a espreitar: "Mete ambas as opcoes, assim fica mais claro e mais facil e
# da-me opcoes para criar o video". A Mesa guarda o estilo no clip, o montar_da_mesa.py
# escreve-o na coluna tratamento e o preparar() le-o daqui. O primeiro de cada um e a
# omissao: qualquer outro valor, o "fiel" das montagens antigas incluido, da a omissao,
# e essas montagens saem iguais ao pixel.
ESTILOS_MONTE = {"colagem": ("filas", "espalhada"), "pilha": ("monte", "leque")}


def estilo_monte(tipo, valor):
    """O estilo pedido, se o tipo o conhece, ou a omissao do tipo."""
    estilos = ESTILOS_MONTE[tipo]
    valor = (valor or "").strip()
    return valor if valor in estilos else estilos[0]


# A ESPALHADA E A DO ENSAIO: cinco fotos pousadas a mao, a primeira com 760 pixeis de
# largura e as outras a descer ate 400, com os centros de POSICOES do teste_estilos.py.
# Aqui as larguras passam a tamanhos, a raiz da area, para uma vertical nao ficar com
# 1000 pixeis de altura por ter a largura de uma deitada; e para 2 a 4 fotos ha centros
# escolhidos com a mesma ideia, a maior em cima a esquerda e as outras a cair a volta. De 6 a
# 12 sao contas, ver espalhada_medidas().
ESPALHADA_TAMANHOS = (760, 660, 600, 540, 400)       # larguras do ensaio, por ordem
ESPALHADA_CENTROS = {                                # fracoes do ecra, como POSICOES
    2: ((0.33, 0.40), (0.69, 0.60)),
    3: ((0.29, 0.34), (0.71, 0.30), (0.52, 0.72)),
    4: ((0.28, 0.32), (0.70, 0.26), (0.36, 0.74), (0.74, 0.70)),
    5: ((0.281, 0.306), (0.693, 0.278), (0.292, 0.741), (0.615, 0.704), (0.839, 0.593)),
}
ESPALHADA_ABERTURAS = tuple(0.50 + 0.10 * k for k in range(21))  # afastamentos que se experimentam
ESPALHADA_RAZOES = (1.0, 0.85, 1.15, 0.7, 1.3, 0.55, 0.4, 0.25)   # a vertical sobre a horizontal
ESPALHADA_DESNIVEIS = (0.06, -0.06, 0.12, -0.12)  # sobe e desce alternado, fracao do ecra do ensaio
ESPALHADA_QUASE = 0.97            # das que dao quase a maior area, fica a mais parecida com o ensaio
ESPALHADA_FILA = 0.05             # duas com altura e centro a menos disto, fracao de A, leem-se em fila
ESPALHADA_BANDA = 0.5             # altura ocupada pelos centros, em alturas medias das fotos: abaixo le-se uma fila so
ESPALHADA_AREA_MIN = 0.20         # do ecra a respirar, todas juntas, para a preferida
ESPALHADA_PRIMEIRA_MIN = 0.07     # do ecra a respirar, a primeira, para a preferida
# DE 6 A 12 FOTOS nao ha ensaio: os centros e os tamanhos vem de uma regra, ver
# espalhada_medidas(), e experimentam-se metade dos afastamentos, que com 12 fotos cada um
# custa seis vezes o de 5 e uma espalhada de 12 levava 23 s. Medido em 6 e 7 fotos, deitadas,
# em pe e misturadas, com e sem legenda, contra todos: metade do tempo, e a area de todas
# nunca mais de 4% do ecra abaixo. Com metade das razoes tambem, uma de 6 deitadas com
# legenda caia de 40% para 21% do ecra. O que se garante esta no
# teste_colagem_e_pilha_com_muitas_fotos.
ESPALHADA_ABERTURAS_MUITAS = ESPALHADA_ABERTURAS[::2]
ESPALHADA_SEGUNDA = 660.0         # de 6 fotos para cima: a primeira e a do ensaio, 760...
ESPALHADA_ULTIMA = 440.0          # ...e as outras descem de 660 ate isto, pela mesma razao
ESPALHADA_SOBE = 0.12             # sobe e desce alternado dentro de cada fila, fracao da altura de uma fila


def espalhada_medidas(n):
    """(centros, tamanhos) da espalhada de n fotos: centros em fracoes do ecra e tamanhos em pixeis do ensaio.

    De 2 a 5 sao os de ESPALHADA_CENTROS e ESPALHADA_TAMANHOS, os do ensaio, ao byte.

    DE 6 A 12, FILAS DESENCONTRADAS, como o ensaio de 5 sao duas: filas = raiz de 0,75 x n
    arredondada, 2 ate 8 fotos e 3 de 9 a 12, com as fotos a mais nas de cima. Cada fila
    impar desvia-se meia foto para a direita, para nenhuma ficar por baixo da de cima, e
    dentro de cada fila as fotos sobem e descem alternadas, para nao se lerem numa linha.
    A primeira e a do ensaio, a maior, em cima a esquerda; as outras descem de
    ESPALHADA_SEGUNDA ate ESPALHADA_ULTIMA pela mesma razao, e por isso nenhuma cresce. Nao
    se exige a descida de 10% em area de uma para a seguinte das de 2 a 5: com 12 fotos a
    ultima ficava com 31% da primeira, e a 15 metros ja nao se via. Sao os mesmos passos do
    resto da espalhada que empurram, encaixam e escolhem o afastamento.
    """
    if n <= len(ESPALHADA_TAMANHOS):
        return ESPALHADA_CENTROS[n], ESPALHADA_TAMANHOS[:n]
    filas = max(2, int(round(math.sqrt(0.75 * n))))
    base, resto = divmod(n, filas)
    contas = [base + (1 if f < resto else 0) for f in range(filas)]
    mais_larga = max(contas)
    centros = []
    for f, conta in enumerate(contas):
        meia = 0.5 if f % 2 else 0.0
        for j in range(conta):
            sobe = ESPALHADA_SOBE if (j + f) % 2 else -ESPALHADA_SOBE
            centros.append(((j + 0.5 + meia) / (mais_larga + 0.5), (f + 0.5 + sobe) / filas))
    razao = (ESPALHADA_ULTIMA / ESPALHADA_SEGUNDA) ** (1.0 / (n - 2))
    tamanhos = [ESPALHADA_TAMANHOS[0]] + [ESPALHADA_SEGUNDA * razao ** k for k in range(n - 1)]
    return centros, tamanhos


def espalhada_em_fila(fotos, folga=ESPALHADA_FILA):
    """Os pares de fotos que se leem numa fila: a mesma altura e o centro a mesma altura do ecra."""
    return [(i, j) for i in range(len(fotos)) for j in range(i + 1, len(fotos))
            if abs(fotos[i][3] - fotos[j][3]) < folga * A and abs(fotos[i][1] - fotos[j][1]) < folga * A]


def espalhada_banda(fotos):
    """Maior menos menor altura dos centros, sobre a altura media das fotos. As cinco 4:3 do ensaio dao 1,20."""
    ys = [f[1] for f in fotos]
    return (max(ys) - min(ys)) / (sum(f[3] for f in fotos) / float(len(fotos)))


def espalhada_preferida(fotos, focos=None):
    """Se a disposicao sai espalhada de verdade: centros em altura, nenhuma solta, com os minimos de area e o miolo livre.

    O MIOLO MEDE-SE OUTRA VEZ. O colagem_afastar da por assente a volta que nao empurrou
    ninguem, mas o encaixe dessa volta ainda encolhe o conjunto, e a moldura nao desce de
    6 pixeis: numa colagem de tres 9:16 que so encolheu, a moldura ficou 1 a 2 px dentro do
    miolo da vizinha. Escolhidas pela maior area nunca calhava; preferidas por aqui, calhou.
    """
    ecra = L * A / (1.0 + COLAGEM_RESPIRA) ** 2
    focos = focos or []
    if not (espalhada_banda(fotos) >= ESPALHADA_BANDA
            and fotos[0][2] * fotos[0][3] >= ESPALHADA_PRIMEIRA_MIN * ecra
            and sum(f[2] * f[3] for f in fotos) >= ESPALHADA_AREA_MIN * ecra
            and not fotos_soltas(fotos)):
        return False
    contornos = [contorno_monte(f) for f in fotos]
    caixas = [caixa_de(c) for c in contornos]
    return not any(not longe(caixa_de(zona), caixas[j]) and afastar(zona, contornos[j])
                   for j in range(1, len(fotos)) for i in range(j)
                   for zona in colagem_guardado(fotos, focos, i))


def colagem_espalhada(aspetos, focos=None, livre_ate=None):
    """Onde pousa cada foto da colagem espalhada: [cx, cy, largura, altura, angulo].

    SEM FILAS NEM GRELHA. Cada foto tem um centro seu e um tamanho seu, a primeira a
    maior, e as que chegam depois pisam as de baixo nas orlas. As garantias sao as da
    colagem em filas, com as mesmas contas de colagem_afastar(): a que chega depois
    tapa no maximo MONTE_PISA de cada lado da de baixo e nunca o miolo nem o foco, e o
    conjunto cabe no ecra a respirar e acima da legenda.

    OS CENTROS E OS TAMANHOS CONTAM UNS COM OS OUTROS, como no ensaio, e o conjunto e
    que se encaixa no ecra. A primeira versao punha os centros em fracoes da area util:
    com legenda a altura mandava no tamanho, a largura ficava igual, e numa colagem de
    3 as duas de cima ficavam soltas com um buraco no meio.

    O AFASTAMENTO E O QUE DA MAIS AREA NO FIM. Juntas de mais empurram-se umas as
    outras e o conjunto fica comprido; afastadas de mais nao se pisam e o conjunto
    encolhe para caber. Experimentam-se os de ESPALHADA_ABERTURAS, so entre os que
    acabam sem ninguem por cima do guardado de ninguem.
    E NA VERTICAL PODE SER OUTRO. Com um afastamento so, numa colagem de 3 com legenda a
    altura mandava, as duas de cima ficavam com um buraco entre elas e a terceira, se se
    juntassem, era empurrada para baixo. Experimentam-se tambem as ESPALHADA_RAZOES, e
    das que chegam a ESPALHADA_QUASE da maior area fica a de razao mais perto do ensaio,
    e dessas a mais aberta, que e a que menos empurrou.

    E NUNCA EM FILA. Com a vertical apertada, cinco verticais com legenda acabavam com a
    terceira e a quarta da mesma altura e com o centro 3% de A uma da outra: uma fila, que
    e o que a espalhada nao e. Ficam de fora os afastamentos em que duas fotos se leem em
    fila, ver espalhada_em_fila(). Um afastamento que as poe em fila nao se deita fora
    logo: experimenta-se com as fotos a subir e a descer alternadas, ESPALHADA_DESNIVEIS,
    e fica a primeira que deixa de estar em fila. A primeira versao ficava com as filas
    quando nenhum afastamento sem desnivel escapava, e numa colagem de quatro 16:9 com
    legenda de duas linhas saia uma grelha de 2 por 2 torta. So se nem assim houver
    nenhuma se aceitam as que tem filas; nas formas medidas nao aconteceu.

    AS VERTICAIS ABREM NA HORIZONTAL. Com a razao entre 0,7 e 1,3 os centros afastavam-se
    quase igual nas duas direcoes, e numa foto alta e a altura que manda no encaixe: quatro
    ou cinco verticais com legenda fechavam-se numa coluna a meio do ecra, com 33 a 63% da
    largura vazia, e a mais pequena ficava com 1 a 2% do ecra. Por isso as razoes descem
    ate 0,25 e os afastamentos vao ate 2,5: a abertura na horizontal passa a poder ser
    quatro vezes a da vertical. A escolha continua a ser pela area no fim.

    E A PISAR-SE. Das que chegam a ESPALHADA_QUASE da maior area fica primeiro a que
    deixa menos fotos soltas, sem tocar em nenhuma outra, e so depois a mais parecida com
    o ensaio: sem desnivel, com a razao mais perto de 1 e a mais aberta, que e a que menos
    empurrou. A mais aberta sozinha deixava duas fotos, uma panoramica e uma alta, com um
    vazio largo entre elas.

    E NUNCA NUMA FILA SO, EM ESCADA. Sem pares em fila, 30 das 87 formas medidas acabavam
    com os centros quase todos a mesma altura, cada foto um degrau ao lado da outra: todas
    as de duas fotos com legenda ou verticais, e as verticais de tres a cinco. A de mais area
    era quase sempre essa, e 3% de tolerancia nao chegava para sair dela. Por isso, antes da
    area, ficam so as que sao espalhadas de verdade, ver espalhada_preferida(): os centros a
    ocupar pelo menos ESPALHADA_BANDA de altura de foto (as cinco 4:3 do ensaio ocupam 1,20),
    nenhuma solta, e ainda com ESPALHADA_AREA_MIN do ecra e ESPALHADA_PRIMEIRA_MIN na primeira,
    mesmo que com menos area do que a de hoje. So se nenhuma o for fica a escolha de sempre.
    Onde nao ha: duas verticais ou uma deitada e uma vertical, que com os centros meia foto
    desencontrados ja nao se tocam em nenhuma razao, e altas com legenda, em que as que
    cumprem ficam abaixo dos minimos.

    DE 6 A 12 FOTOS e tudo igual, com os centros e os tamanhos de espalhada_medidas() e so as
    aberturas de ESPALHADA_ABERTURAS_MUITAS. Com tantas fotos quase todas as disposicoes tem
    pares em fila, e fica-se muitas vezes com as de em_fila: o que se garante e o que as
    outras garantem, dentro do ecra, acima da legenda, nenhum miolo pisado e a primeira maior.
    """
    n = len(aspetos)
    mx, my = 0.035 * L, 0.05 * A
    baixo = A - my if livre_ate is None else max(0.5 * A, min(A - my, livre_ate))
    focos = focos or []
    centros, tamanhos = espalhada_medidas(n)
    aberturas = ESPALHADA_ABERTURAS if n <= len(ESPALHADA_TAMANHOS) else ESPALHADA_ABERTURAS_MUITAS
    # O dobro do ensaio, para o conjunto nunca comecar mais pequeno do que o ecra: o
    # encaixe so encolhe.
    base = 2.0 * L / 1920.0

    def pousadas(razao, abre, desnivel):
        """As fotos com este afastamento ja assentes, ou None se o afastamento nao assentou."""
        fotos = []
        for i, a in enumerate(aspetos):
            lado = base * tamanhos[i] / math.sqrt(4 / 3.0)
            fx, fy = centros[i]
            sobe = desnivel if i % 2 else -desnivel
            fotos.append([L / 2.0 + (fx - 0.5) * 1920.0 * base * abre,
                          A / 2.0 + ((fy - 0.5) * razao + sobe) * 1080.0 * base * abre,
                          lado * math.sqrt(a), lado / math.sqrt(a),
                          COLAGEM_ANGULOS[i % len(COLAGEM_ANGULOS)]])
        if colagem_afastar(fotos, focos, (mx, my, L - mx, baixo)):
            return fotos
        return None

    opcoes, em_fila = [], []
    for razao in ESPALHADA_RAZOES:
        for abre in aberturas:
            fotos = pousadas(razao, abre, 0.0)
            if fotos is None:
                continue
            opcao = (sum(f[2] * f[3] for f in fotos), 0.0, abs(razao - 1.0), abre, fotos)
            if not espalhada_em_fila(fotos):
                opcoes.append(opcao)
                continue
            em_fila.append(opcao)
            for desnivel in ESPALHADA_DESNIVEIS:
                outra = pousadas(razao, abre, desnivel)
                if outra is not None and not espalhada_em_fila(outra):
                    opcoes.append((sum(f[2] * f[3] for f in outra), abs(desnivel),
                                   abs(razao - 1.0), abre, outra))
                    break
    # Antes da area, que sejam espalhadas de verdade: ver espalhada_preferida(). So se
    # nenhuma o for fica a escolha de sempre, entre todas.
    opcoes = [o for o in opcoes if espalhada_preferida(o[4], focos)] or opcoes or em_fila
    if not opcoes:
        # Nenhum afastamento assentou em dez voltas. Nunca aconteceu nas formas medidas; se
        # acontecer, a das filas tem as mesmas garantias e e melhor do que nada.
        return colagem_disposicao(aspetos, focos, livre_ate)
    topo = max(o[0] for o in opcoes)
    quase = [o for o in opcoes if o[0] >= ESPALHADA_QUASE * topo]
    return min(quase, key=lambda o: (fotos_soltas(o[4]), o[1], o[2], -o[3]))[4]


def fotos_soltas(fotos):
    """Quantas fotos nao tocam em nenhuma outra."""
    contornos = [contorno_monte(f) for f in fotos]
    caixas = [caixa_de(c) for c in contornos]
    return sum(1 for j in range(len(fotos))
               if not any(not longe(caixas[i], caixas[j]) and afastar(contornos[i], contornos[j])
                          for i in range(len(fotos)) if i != j))


# O LEQUE. No monte, com os desvios do ensaio, uma foto do meio de uma pilha de oito
# acaba quase toda tapada. No leque abrem-se de fora para dentro: a primeira no extremo
# esquerdo, a segunda no direito, a terceira ao lado da primeira, e a de cima no meio.
# Cada uma que chega depois fica mais para dentro, por isso cada foto de baixo guarda a
# tira de fora a vista ate ao fim.
PILHA_LEQUE_VE = 0.20             # cada foto de baixo com pelo menos isto da area a vista no fim
PILHA_LEQUE_FOLGA = 0.06          # a disposicao procura esta margem a mais, contra o esbatido
PILHA_LEQUE_SOBES = (0.035, 0.06, 0.09)   # desvios de cima para baixo que se experimentam, fracao de A
PILHA_LEQUE_ABRE = 90.0 / 1920.0  # entre lugares vizinhos, fracao de L: o que o monte desvia, no minimo


def _no_convexo(px, py, poli):
    """Se o ponto esta dentro do poligono convexo, com os cantos pela ordem de cantos()."""
    dentro = None
    for k in range(len(poli)):
        (x1, y1), (x2, y2) = poli[k], poli[(k + 1) % len(poli)]
        lado = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1) >= 0
        if dentro is None:
            dentro = lado
        elif lado != dentro:
            return False
    return True


def fracao_a_vista(fotos, i, passos=24):
    """Parte da foto i, sem moldura, que as seguintes nao tapam. Contada numa grelha."""
    cx, cy, w, h, ang = fotos[i]
    cima = []
    for f in fotos[i + 1:]:
        poli = contorno_monte(f)
        xs, ys = [p[0] for p in poli], [p[1] for p in poli]
        cima.append((min(xs), max(xs), min(ys), max(ys), poli))
    if not cima:
        return 1.0
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    livres = 0
    for p in range(passos):
        u = ((p + 0.5) / passos - 0.5) * w
        for q in range(passos):
            v = ((q + 0.5) / passos - 0.5) * h
            px, py = cx + u * c + v * s, cy - u * s + v * c
            if not any(x0 <= px <= x1 and y0 <= py <= y1 and _no_convexo(px, py, poli)
                       for x0, x1, y0, y1, poli in cima):
                livres += 1
    return livres / float(passos * passos)


def pilha_leque(aspetos, livre_ate=None):
    """Onde pousa cada foto da pilha em leque: [cx, cy, largura, altura, angulo].

    As caixas e os angulos sao os do monte. Os lugares vao da esquerda para a direita,
    e as fotos ocupam-nos de fora para dentro. Cada lugar fica a distancia que deixa a
    descoberto uma tira de cada foto de baixo, pela largura verdadeira dela e pela
    largura rodada das que a tapam, e os lugares vizinhos desviam-se um para cima e o
    outro para baixo, o que deixa tambem a vista uma faixa por cima ou por baixo.

    A TIRA E A MAIS ESTREITA QUE CHEGA: procura-se por bisseccao a que ainda da, contada
    na grelha, PILHA_LEQUE_VE a vista em todas, com PILHA_LEQUE_FOLGA de margem. Com mais
    fotos o leque abre mais, e o conjunto encolhe para caber no ecra e acima da legenda,
    como o monte, o que nao muda a parte que se ve de cada uma. O desvio de cima para
    baixo e o de PILHA_LEQUE_SOBES que da mais area no fim: num leque de oito deitadas um
    desvio maior deixa a tira mais estreita e as fotos passam de 13% para 17% do ecra,
    mas com legenda, ou com verticais, e a altura que manda e o desvio so as encolhe.
    """
    n = len(aspetos)
    lugar = [0] * n
    esq, dto = 0, n - 1
    for i in range(n):
        if i % 2 == 0:
            lugar[i], esq = esq, esq + 1
        else:
            lugar[i], dto = dto, dto - 1
    por_lugar = sorted(range(n), key=lambda i: lugar[i])
    caixas = []
    for i, a in enumerate(aspetos):
        h = min(PILHA_ALT * A, PILHA_LARG * L / a)
        ang = PILHA_ANGULOS[i % len(PILHA_ANGULOS)]
        t = moldura_monte(a * h, h)
        caixas.append((a * h, h, ang, caixa_rodada(a * h + 2 * t, h + 2 * t, ang)[0]))

    def lugares(tira, sobe):
        xs = {}
        for k, i in enumerate(por_lugar):
            x = 0.0
            for j in por_lugar[:k]:
                wi, _hi, _ai, mli = caixas[i]
                wj, _hj, _aj, mlj = caixas[j]
                if j < i:
                    # j e de baixo e fica a esquerda: a borda esquerda de i deixa-lhe a tira
                    x = max(x, xs[j] - wj / 2.0 + tira * wj + mli)
                else:
                    # i e de baixo e fica a direita: a borda direita de j deixa-lhe a tira
                    x = max(x, xs[j] + mlj - wi / 2.0 + tira * wi)
                # Nunca abre menos do que o monte. Com uma larga por baixo de uma estreita a
                # tira zero ja chegava, e as duas ficavam no mesmo x, so a subir e a descer.
                x = max(x, xs[j] + PILHA_LEQUE_ABRE * L)
            xs[i] = x
        meio = (xs[por_lugar[0]] + xs[por_lugar[-1]]) / 2.0
        return [[L / 2.0 + xs[i] - meio, A / 2.0 + (sobe if lugar[i] % 2 else -sobe) * A,
                 caixas[i][0], caixas[i][1], caixas[i][2]] for i in range(n)]

    def chega(fotos):
        return all(fracao_a_vista(fotos, i) >= PILHA_LEQUE_VE + PILHA_LEQUE_FOLGA
                   for i in range(n - 1))

    b = MONTE_BORDA * A
    baixo = A - b if livre_ate is None else max(0.5 * A, min(A - b, livre_ate))
    melhor = None
    for sobe in PILHA_LEQUE_SOBES:
        # Com a tira maior do que a largura ninguem tapa ninguem, e isso chega sempre.
        lo, hi = 0.0, 1.5
        if chega(lugares(lo, sobe)):
            hi = lo
        else:
            for _ in range(8):
                meio = (lo + hi) / 2.0
                if chega(lugares(meio, sobe)):
                    hi = meio
                else:
                    lo = meio
        fotos = encaixar_grupo(lugares(hi, sobe), b, b, L - b, baixo, 1.0)
        area = sum(f[2] * f[3] for f in fotos)
        if melhor is None or area > melhor[0] + 1e-6:
            melhor = (area, fotos)
    return melhor[1]


def pilha_disposicao(aspetos, livre_ate=None):
    """Onde pousa cada foto da pilha: [cx, cy, largura, altura, angulo].

    Os desvios e os angulos sao os do ensaio. A diferenca e a caixa: o ensaio dava
    880 pixeis de largura a todas, e uma vertical assim tinha 1170 de altura e saia
    do ecra. Cada foto encaixa agora numa caixa, e o monte inteiro cabe no ecra, e
    acima da legenda quando ha legenda. A pilha so recua no fim, nunca cresce, por
    isso o que cabe pousado cabe ate ao fim.
    """
    fotos = []
    for i, a in enumerate(aspetos):
        h = min(PILHA_ALT * A, PILHA_LARG * L / a)
        cx = L / 2.0 + math.sin(i * 1.7) * 90.0 * L / 1920.0
        cy = A / 2.0 + math.cos(i * 2.1) * 46.0 * A / 1080.0
        fotos.append([cx, cy, a * h, h, PILHA_ANGULOS[i % len(PILHA_ANGULOS)]])
    b = MONTE_BORDA * A
    baixo = A - b if livre_ate is None else max(0.5 * A, min(A - b, livre_ate))
    return encaixar_grupo(fotos, b, b, L - b, baixo, 1.0)


def sprite_monte(im, larg, alt, moldura, angulo, texto="", largura_ecra=None, foco=None,
                 pisa=0.0, sobe=0.0, tamanho=None, em_cima=False):
    """A foto inteira, com moldura clara, rodada, pronta para compor com sub-pixel.

    Feita uma vez por clip, no maior tamanho que vai ter pousada. Roda-se em RGBa
    pre-multiplicado, com dois pixeis transparentes a volta antes de rodar, para a
    borda rodada sair esbatida em vez de em escada. No fim leva a margem de
    com_margem(), a regra do CLAUDE.md para tudo o que entra em sub-pixel.

    `texto` e o da propria foto. A faixa desenha-se na foto ja no tamanho do sprite,
    antes da moldura e da rotacao, e por isso roda, entra e e tapada com ela; ver
    faixa_na_foto(). `largura_ecra` e a largura com que a foto pousa no ecra, que na
    colagem e menor do que o sprite, e `foco` o ponto marcado, que a faixa nao tapa.
    `pisa` e a orla que as seguintes podem tapar e `sobe` quanto a faixa sobe do fundo
    por causa dela, ver capa_texto_foto() e colocar_faixa(); `tamanho` a letra escolhida e
    `em_cima` a faixa forcada ao topo.
    """
    cw, ch = max(1, int(round(larg))), max(1, int(round(alt)))
    quadro = Image.new("RGB", (cw + 2 * moldura, ch + 2 * moldura), MOLDURA_COR)
    foto = im.resize((cw, ch), Image.LANCZOS)
    if texto:
        faixa_na_foto(foto, texto, largura_ecra, foco, pisa, sobe, tamanho, em_cima)
    quadro.paste(foto, (moldura, moldura))
    folha = Image.new("RGBa", (quadro.width + 2 * MARGEM, quadro.height + 2 * MARGEM),
                      (0, 0, 0, 0))
    folha.paste(quadro.convert("RGBa"), (MARGEM, MARGEM))
    if angulo:
        folha = folha.rotate(angulo, resample=Image.BICUBIC, expand=True)
    return com_margem(folha, "alfa")


def zona_das_letras(lugar, texto, foco, pisa, sobe, tamanho=None, em_cima=False):
    """Os cantos, no ecra, do retangulo onde estao AS LETRAS do texto de uma foto pousada.

    A faixa vai de borda a borda da foto, mas as letras sao o miolo: a linha mais larga,
    centrada, sem a almofada de cima e de baixo. Um "2012" numa foto de 922 pixeis tem 104
    de letra, e e ai, no centro, que a foto seguinte da pilha cai. Medida a faixa inteira,
    o aviso dizia 52% tapado quando as letras estavam 100% escondidas.
    """
    _cx, _cy, w, h, _ang = lugar
    largura = largura_do_texto(w, pisa)
    tam, linhas, _cortado = linhas_texto_foto(texto, largura, tamanho)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    letras = max([d.textbbox((0, 0), l, font=_fonte(tam))[2] for l in linhas] or [1])
    almofada = int(round(tam * TEXTO_FOTO_ALMOFADA))
    _capa, topo, alto, _c = colocar_faixa(texto, w, h, w, foco, pisa, sobe, tamanho, em_cima)
    return zona_da_faixa(lugar, topo + almofada, max(1, alto - 2 * almofada), min(letras, largura))


def sitio_da_faixa_na_colagem(lugares, k, texto, foco, pisa, sobe, tamanho=None):
    """Se a faixa do texto da foto k da colagem vai para o topo, e quanto fica pisada: (em_cima, tapado).

    A ORLA QUE A SEGUINTE PISA JA FOI DESCONTADA, com `pisa` de lado e `sobe` em baixo, e
    nas formas medidas isso chega. Isto e a guarda para as que nao se mediram: se, mesmo
    assim, alguma foto seguinte pisa a zona da faixa em baixo, a faixa vai para o topo,
    a mesma regra do foco; se o topo tambem e pisado, fica em baixo e quem prepara avisa
    com a fracao. Mede-se a faixa pousada, com a foto no tamanho do ecra, e so a banda
    das letras, sem a almofada: a almofada tocada por um canto de moldura nao tapa letra.
    """
    _cx, _cy, w, h, _ang = lugares[k]
    seguintes = [contorno_monte(lugares[j]) for j in range(k + 1, len(lugares))]
    if not seguintes:
        return False, 0.0
    largura = largura_do_texto(w, pisa)
    almofada = int(round(linhas_texto_foto(texto, largura, tamanho)[0] * TEXTO_FOTO_ALMOFADA))

    def tapada(em_cima):
        _capa, topo, alto, _c = colocar_faixa(texto, w, h, w, foco, pisa, sobe, tamanho, em_cima)
        banda = max(1, alto - 2 * almofada)
        return parte_tapada(zona_da_faixa(lugares[k], topo + almofada, banda, largura), seguintes)

    baixo = tapada(False)
    if baixo <= TEXTO_FOTO_PISADA:
        return False, baixo
    cima = tapada(True)
    if cima <= TEXTO_FOTO_PISADA:
        return True, cima
    return False, baixo


def preparar_monte(tipo, imagens, focos, texto, cross_entra=0.0, cross_sai=None, estilo=None,
                   textos=None, opcoes=None, duracao=None):
    """Colagem ou pilha, a partir das imagens ja abertas.

    `cross_entra` e o encadeado com o clip de antes e `cross_sai` o do seguinte; sem
    este, conta o mesmo que o de entrada. Ver agenda_monte(). `estilo` e o da coluna
    tratamento, ver ESTILOS_MONTE: so muda onde as fotos pousam, a agenda, a chegada,
    a respiracao e o recuo sao os mesmos. `textos` e um por foto, ver textos_do_grupo():
    cada um vai numa faixa dentro da sua foto, com o tamanho contado na foto pousada, ou,
    com a opcao legenda, na faixa de baixo do ecra, ver legenda_por_foto(). `opcoes` sao as
    de ler_textos_opcoes() e `duracao` a do clip, so para os avisos da opcao legenda.
    Nao mexe em onde as fotos pousam.
    """
    opcoes = ler_textos_opcoes(opcoes)
    textos = textos_do_grupo(textos, len(imagens))
    tamanho = opcoes["tamanho"]
    estilo = estilo_monte(tipo, estilo)
    aspetos = [im.width / float(im.height) for im in imagens]
    legenda = None
    if textos and opcoes["modo"] == "legenda":
        # NA LEGENDA DE BAIXO, E NAO NAS FOTOS. As fotos ficam como sem textos, e a faixa
        # de baixo, com a altura do texto mais alto, troca de texto com cada foto. Uma foto
        # sem texto mostra o do grupo, se houver.
        grupo = (texto or "").strip()
        legenda = legenda_por_foto([t or grupo for t in textos], tamanho)
        if legenda is not None and duracao:
            tempos = tempos_legenda_grupo(tipo, len(imagens), duracao, cross_entra,
                                          cross_entra if cross_sai is None else cross_sai)
            for k, t, dura in legendas_curtas(legenda["textos"], tempos):
                avisar_legenda_curta(k, t, dura)
        textos = None
    capa = None if legenda is not None else faixa_texto(texto)
    # A LEGENDA DESENHA-SE POR CIMA, como nos outros tipos, mas as fotos pousam acima
    # dela. Nos fotogramas de controlo a faixa tapava a fila de baixo da colagem, e a
    # 15 metros uma cara meio escondida por uma faixa preta nao se le.
    livre_ate = None
    if legenda is not None:
        livre_ate = legenda["topo"] - MONTE_LEGENDA_FOLGA * A
    elif capa is not None:
        caixa = capa[1].getbbox()
        if caixa:
            livre_ate = caixa[1] - MONTE_LEGENDA_FOLGA * A
    # NA PILHA O TEXTO DAS DE BAIXO DESAPARECE, salvo se o Tiago pedir que fique. Sobre a
    # pilha ele aceitou que os textos das fotos de baixo desaparecam quando a seguinte cai
    # por cima, "mas melhor ainda e a opcao para ficar la e para desaparecer ser algo que
    # eu escolho". Com "some", cada foto que tem uma seguinte leva um segundo sprite sem
    # texto, feito uma vez: e esse que entra nas camadas guardadas depois de a seguinte
    # comecar, ver sprite_no_instante().
    some = tipo == "pilha" and textos is not None and opcoes["tapadas"] == "some"
    if tipo == "colagem":
        if estilo == "espalhada":
            lugares = colagem_espalhada(aspetos, focos, livre_ate)
        else:
            lugares = colagem_disposicao(aspetos, focos, livre_ate)
        cresce = 1.0 + COLAGEM_RESPIRA      # no fim, a respirar, fica a 1:1
        fundo = cobrir(imagens[0], max(1, L // 4), max(1, A // 4))
        fundo = fundo.filter(ImageFilter.GaussianBlur(15)).resize((L, A), Image.BICUBIC)
        fundo = Image.blend(Image.new("RGB", (L, A), (8, 8, 10)), fundo, 0.28)
    else:
        if estilo == "leque":
            lugares = pilha_leque(aspetos, livre_ate)
        else:
            lugares = pilha_disposicao(aspetos, livre_ate)
        cresce = 1.0                        # a pilha so recua, nunca cresce
        fundo = Image.new("RGB", (L, A), (10, 10, 12))
    fotos = []
    for k, (im, (cx, cy, w, h, ang)) in enumerate(zip(imagens, lugares)):
        moldura = moldura_monte(w, h)
        chegada = (cx, cy)
        if tipo == "colagem":
            # Na colagem a foto chega 14% maior. Junto a borda do ecra isso saia fora
            # do quadro, e o ensaio corrigia-o afastando a disposicao inteira da borda.
            # Aqui e so o sitio de chegada que se afasta, e ela escorrega para o lugar
            # enquanto assenta.
            ml, ma = caixa_rodada(w + 2 * moldura, h + 2 * moldura, ang)
            chegada = meter_no_quadro(cx, cy, ml * COLAGEM_CHEGA, ma * COLAGEM_CHEGA, 1.0)
        # O texto conta com a foto POUSADA, w de largura no ecra, e nao com o sprite, que
        # na colagem e feito COLAGEM_RESPIRA maior para o fim da respiracao sair a 1:1.
        texto_foto = textos[k] if textos else ""
        foco = focos[k] if focos and k < len(focos) else None
        # A ORLA QUE A SEGUINTE PISA NAO LEVA LETRA. Na colagem uma foto que chega depois tapa
        # ate MONTE_PISA de cada lado da de baixo. O texto era medido e centrado na largura
        # inteira, e numa colagem espalhada de 4 o "m" de "fim" e metade das reticencias
        # ficavam por baixo da moldura da foto 4. So se desconta a quem tem alguma foto
        # seguinte a pisar: a de cima fica com a largura toda. A pilha tapa muito mais do que
        # a orla, e fica como esta ate o Tiago decidir.
        #
        # E A ORLA CONTA EM BAIXO, QUE E ONDE A FAIXA ESTA. So se descontava de lado: numa
        # colagem em filas de 5 a fila de baixo comia a base das letras da de cima, "2019"
        # lia-se "2010" com 13% da letra tapada, e ninguem avisava porque para o texto ele
        # cabia. O miolo que colagem_guardado() garante e a foto encolhida de MONTE_PISA
        # dos quatro lados, por isso a faixa levantada dessa orla fica dentro dele.
        pisa = sobe = 0.0
        em_cima = False
        if tipo == "colagem" and texto_foto:
            meu = contorno_monte(lugares[k])
            if any(afastar(meu, contorno_monte(lugares[j])) for j in range(k + 1, len(lugares))):
                pisa = sobe = MONTE_PISA
            # E SE MESMO ASSIM A FAIXA FICA PISADA, VAI PARA O TOPO. Ver sitio_da_faixa_na_colagem().
            em_cima, pisado = sitio_da_faixa_na_colagem(lugares, k, texto_foto, foco, pisa, sobe, tamanho)
            if not em_cima and pisado > TEXTO_FOTO_PISADA:
                avisar_texto_pisado(k, texto_foto, pisado)
        sprite = sprite_monte(im, w * cresce, h * cresce, int(round(moldura * cresce)), ang,
                              texto_foto, w, foco, pisa, sobe, tamanho, em_cima)
        sprite_sem = None
        if texto_foto:
            if linhas_texto_foto(texto_foto, largura_do_texto(w, pisa), tamanho)[2]:
                avisar_texto_cortado(k, texto_foto)
            if some and k + 1 < len(imagens):
                sprite_sem = sprite_monte(im, w * cresce, h * cresce, int(round(moldura * cresce)), ang)
            elif tipo == "pilha":
                # O QUE AS SEGUINTES TAPAM DIZ-SE, quando o Tiago pediu que o texto fique: as
                # fotos da pilha tapam-se de proposito, e assim pelo menos sabe quais e que
                # saem aos pedacos, em vez de o descobrir no jantar. Mede-se a zona das LETRAS
                # da foto pousada, no tamanho do ecra, e nao a faixa inteira: a faixa tem a
                # largura da foto e as letras estao no centro, precisamente onde a seguinte
                # cai, ver zona_das_letras().
                tapado = parte_tapada(zona_das_letras(lugares[k], texto_foto, foco, pisa, sobe, tamanho),
                                      [contorno_monte(lugares[j]) for j in range(k + 1, len(lugares))])
                if tapado > TEXTO_FOTO_TAPADO:
                    avisar_texto_tapado(k, texto_foto, tapado)
        fotos.append({"centro": (cx, cy), "chegada": chegada, "tamanho": (w, h),
                      "angulo": ang, "moldura": moldura, "sprite": sprite, "texto": texto_foto,
                      "sprite_sem": sprite_sem})
    cross = (cross_entra, cross_entra if cross_sai is None else cross_sai)
    return {"tipo": tipo, "estilo": estilo, "fotos": fotos, "cresce": cresce, "fundo": fundo,
            "capa": capa, "legenda": legenda, "opcoes": opcoes, "cross": cross, "_camada": None}


def alfa_texto_pilha(t_rel, inicio_seguinte, entrada):
    """Quanto do texto de uma foto da pilha ainda se ve, de 1 a 0, com "some".

    Inteiro ate a seguinte comecar a entrar; depois desaparece em TEXTO_FOTO_SOME segundos
    e nao volta. Nunca mais devagar do que a entrada: num clip apertado a entrada encolhe
    ate 0,12 s, e o texto tem de ter desaparecido quando a ultima foto pousa, que e quando
    o desenho passa para a camada do conjunto, onde as tapadas ja nao tem texto.
    """
    if t_rel < inicio_seguinte:
        return 1.0
    some = min(TEXTO_FOTO_SOME, entrada)
    if some <= 0:
        return 0.0
    return max(0.0, 1.0 - (t_rel - inicio_seguinte) / some)


def sprite_no_instante(pronto, k, t_rel, inicios, entrada):
    """O sprite da foto k neste instante, e quanto do texto dela se ve: (sprite, alfa ou None).

    Sem "some", ou na ultima foto, e o sprite de sempre e None. Com "some" e uma seguinte
    ja a entrar, o texto desvanece: os dois sprites, com e sem texto, misturam-se em
    pre-multiplicado, que e exatamente o texto a desvanecer sobre a mesma fotografia, e nas
    pontas sao os proprios sprites, byte a byte.
    """
    f = pronto["fotos"][k]
    sem = f.get("sprite_sem")
    if sem is None:
        return f["sprite"], None
    alfa = alfa_texto_pilha(t_rel, inicios[k + 1], entrada)
    if alfa >= 1.0:
        return f["sprite"], 1.0
    if alfa <= 0.0:
        return sem, 0.0
    return Image.blend(sem, f["sprite"], alfa), alfa


def estado_monte(pronto, t_rel, duracao):
    """Tempos do clip: inicio de cada entrada, duracao da entrada e o zoom do conjunto."""
    colagem = pronto["tipo"] == "colagem"
    cross_entra, cross_sai = pronto.get("cross", (0.0, 0.0))
    inicios, entrada = agenda_monte(
        len(pronto["fotos"]), duracao,
        COLAGEM_ENTRADA if colagem else PILHA_ENTRADA,
        cross_entra=cross_entra, cross_sai=cross_sai)
    pousa = inicios[-1] + entrada
    if duracao > pousa:
        fim = arrancar((t_rel - pousa) / (duracao - pousa))
    else:
        fim = 1.0 if t_rel >= pousa else 0.0
    zoom = 1.0 + COLAGEM_RESPIRA * fim if colagem else 1.0 - PILHA_AFASTA * fim
    return inicios, entrada, zoom


def poses_monte(pronto, t_rel, duracao):
    """Onde esta cada foto no instante t_rel: ([(k, x, y, tamanho, alfa, pousada)], zoom).

    `tamanho` e em relacao a foto pousada sem zoom. So vem as que ja comecaram a
    entrar, pela ordem em que se compoem. O desenhar_monte desenha isto e os testes
    medem isto, para a posicao de uma foto ter uma conta so.
    """
    colagem = pronto["tipo"] == "colagem"
    inicios, entrada, zoom = estado_monte(pronto, t_rel, duracao)
    chega = COLAGEM_CHEGA if colagem else PILHA_CHEGA
    poses = []
    for k, f in enumerate(pronto["fotos"]):
        pousada = entrada <= 0 or t_rel >= inicios[k] + entrada
        if pousada:
            p = 1.0
        elif t_rel <= inicios[k]:
            continue
        else:
            p = pousar((t_rel - inicios[k]) / entrada)
        cx, cy = f["centro"]
        if colagem:
            ax, ay = f["chegada"]
            cx, cy = ax + (cx - ax) * p, ay + (cy - ay) * p
            alfa = min(1.0, p * 1.4)
        else:
            alfa = min(1.0, p * 1.5)
        x = L / 2.0 + (cx - L / 2.0) * zoom
        y = A / 2.0 + (cy - A / 2.0) * zoom
        if not colagem:
            y -= (1.0 - p) * PILHA_QUEDA * A      # cai de cima, de proposito
        poses.append((k, x, y, (chega - (chega - 1.0) * p) * zoom, alfa, pousada))
    return poses, zoom


def conjunto_monte(pronto):
    """As fotos pousadas numa camada so, pre-multiplicada e com margem: (topo, desvio, camada).

    PORQUE: depois de pousadas, na respiracao da colagem e no recuo da pilha, mexem-se
    todas ao mesmo tempo e a camada das pousadas deixa de servir. Compor oito fotos
    rodadas em cada fotograma custava 600 ms na pilha de 8, e um clip de 9 s eram
    mais de dois minutos de render. Nessa fase as fotos nao mudam umas em relacao as
    outras, so o zoom do conjunto, por isso compoe-se o conjunto uma vez e cada
    fotograma so o escala.

    A CAMADA E FEITA NO TAMANHO POUSADO, COM AS MESMAS CONTAS DO FOTOGRAMA PARADO.
    Na colagem era feita no tamanho do fim da respiracao, 3% maior, para o ultimo
    fotograma sair a 1:1. O preco via-se no fotograma da troca: cada foto era
    amostrada duas vezes, uma na posicao de sub-pixel dentro da camada e outra ao
    escalar, e as bordas das molduras saltavam ate 56 de 255 de um fotograma para o
    seguinte. Feita com os mesmos compor() do fotograma parado, a origem da camada
    cai num pixel inteiro e no primeiro fotograma a escala e 1,00001: a segunda
    amostragem e quase a identidade e o salto desce para 3 a 5. O ultimo fotograma
    passa a ser a camada ampliada 3%, o que num zoom lento nao se distingue.

    A cor compoe-se sobre preto e o alfa com a silhueta branca de cada sprite: colar
    com mascara sobre preto da exatamente a cor pre-multiplicada, e o alfa da mesma
    maneira, sem a borda escura que daria compor em RGBA direto.
    """
    if pronto.get("_conjunto") is None:
        topo = 1.0
        cw, ch = L, A
        cor = Image.new("RGB", (cw, ch), (0, 0, 0))
        alfa = Image.new("RGB", (cw, ch), (0, 0, 0))
        for f in pronto["fotos"]:
            x, y = f["centro"]
            escala = 1.0 / pronto["cresce"]
            # Na pilha com "some" as tapadas ja nao tem texto quando o conjunto entra em
            # cena: o sprite sem texto, feito uma vez, ver sprite_no_instante().
            sprite = f["sprite"] if f.get("sprite_sem") is None else f["sprite_sem"]
            compor(cor, sprite, x, y, escala)
            a = sprite.split()[3]
            compor(alfa, Image.merge("RGBa", (a, a, a, a)), x, y, escala)
        camada = Image.merge("RGBa", cor.split() + (alfa.split()[0],))
        # So o retangulo onde ha fotografia, com dois pixeis de vazio a volta. A pilha
        # ocupa metade do ecra, e escalar a camada inteira era escalar vazio. O desvio
        # e o centro desse retangulo em relacao ao centro da camada.
        caixa = alfa.getbbox() or (0, 0, cw, ch)
        x0, y0 = max(0, caixa[0] - 2), max(0, caixa[1] - 2)
        x1, y1 = min(cw, caixa[2] + 2), min(ch, caixa[3] + 2)
        desvio = ((x0 + x1) / 2.0 - cw / 2.0, (y0 + y1) / 2.0 - ch / 2.0)
        pronto["_conjunto"] = (topo, desvio, com_margem(camada.crop((x0, y0, x1, y1)), "alfa"))
    return pronto["_conjunto"]


def desenhar_monte(pronto, t_rel, duracao, por_foto=False):
    """Um fotograma da colagem ou da pilha. `por_foto` desliga a camada do conjunto, para os testes."""
    poses, zoom = poses_monte(pronto, t_rel, duracao)
    inicios, entrada, _zoom = estado_monte(pronto, t_rel, duracao)
    fotos, cresce = pronto["fotos"], pronto["cresce"]
    assentes = 0
    while assentes < len(poses) and poses[assentes][5]:
        assentes += 1

    # AS QUE JA ESTAO PARADAS COMPOEM-SE UMA VEZ. Enquanto as outras entram e o
    # conjunto ainda nao se mexe, as pousadas nao mudam de um fotograma para o
    # seguinte: guarda-se essa camada e so a que esta a chegar e composta de novo.
    # A chave inclui a duracao, e a camada so se usa quando nada mais se mexe,
    # por isso a ordem por que se pedem os fotogramas nao muda nenhum pixel.
    #
    # NA PILHA COM "some" A CAMADA TAMBEM DEPENDE DO TEXTO DA POUSADA DE CIMA: as de
    # baixo ja nao tem texto, deterministicamente, mas o da de cima esta a desaparecer
    # enquanto a seguinte entra. Esse alfa entra na chave: durante os cinco fotogramas
    # do desvanecer a camada refaz-se, e fora deles guarda-se como sempre.
    if zoom == 1.0:
        alfa_topo = None
        if assentes:
            alfa_topo = sprite_no_instante(pronto, poses[assentes - 1][0], t_rel, inicios, entrada)[1]
        chave = (round(duracao, 4), assentes, alfa_topo)
        if pronto.get("_camada") is None or pronto["_camada"][0] != chave:
            base = pronto["fundo"].copy()
            for k, x, y, tam, alfa, _ in poses[:assentes]:
                compor(base, sprite_no_instante(pronto, k, t_rel, inicios, entrada)[0],
                       x, y, tam / cresce, alfa)
            pronto["_camada"] = (chave, base)
        tela = pronto["_camada"][1].copy()
    elif assentes == len(fotos) and not por_foto:
        topo, (ox, oy), camada = conjunto_monte(pronto)
        tela = pronto["fundo"].copy()
        s = zoom / topo
        compor(tela, camada, L / 2.0 + ox * s, A / 2.0 + oy * s, s)
    else:
        tela = pronto["fundo"].copy()
        for k, x, y, tam, alfa, _ in poses[:assentes]:
            compor(tela, sprite_no_instante(pronto, k, t_rel, inicios, entrada)[0],
                   x, y, tam / cresce, alfa)
    for k, x, y, tam, alfa, _ in poses[assentes:]:
        compor(tela, sprite_no_instante(pronto, k, t_rel, inicios, entrada)[0],
               x, y, tam / cresce, alfa)
    colar_legenda(tela, pronto, t_rel, duracao, inicios)
    return tela


def preparar_lado(lay, imagens, focos, texto, textos=None, opcoes=None, duracao=None):
    """O lado a lado, a partir das imagens ja abertas, uma por celula de lado_celulas(lay).

    `focos` e um por foto, como na coluna fonte_imagem, e `texto` a legenda do grupo.
    `textos` e um por foto, ver textos_do_grupo(): cada um numa faixa dentro da sua
    celula, ver lado_faixas(), ou, com a opcao legenda, na faixa de baixo do ecra a trocar
    com cada celula, ver legenda_por_foto(). `opcoes` sao as de ler_textos_opcoes() e
    `duracao` a do clip, so para os avisos. Sem textos as celulas sao as de antes, pixel
    a pixel.
    """
    opcoes = ler_textos_opcoes(opcoes)
    celulas = []
    for k, ((x, y, w, h), vem) in enumerate(lado_celulas(lay)):
        im = imagens[k]
        respira = True
        foco = focos[k] if focos and k < len(focos) else None
        foto, foco_na_celula = (0, 0, w, h), None     # onde ha fotografia, e o foco, na celula
        if lay == "3s" and k == 2:
            # A de cima e um cartao: a foto inteira, sem cortar, com moldura
            # clara para se ler por cima das outras duas. Nao respira, senao a
            # moldura era cortada pelo zoom.
            moldura = 14
            dentro = encaixar(im, w - 2 * moldura, h - 2 * moldura)
            cw, ch = dentro.width + 2 * moldura, dentro.height + 2 * moldura
            x, y, w, h = x + (w - cw) // 2, y + (h - ch) // 2, cw, ch
            img = Image.new("RGB", (w, h), (236, 232, 226))
            img.paste(dentro, (moldura, moldura))
            img = img.resize((int(math.ceil(w * (1 + LADO_ZOOM))),
                              int(math.ceil(h * (1 + LADO_ZOOM)))), Image.LANCZOS)
            respira = False
            foto = (moldura, moldura, moldura + dentro.width, moldura + dentro.height)
            if foco:
                foco_na_celula = [(moldura + foco[0] * dentro.width, moldura + foco[1] * dentro.height)]
        else:
            sw = int(math.ceil(w * (1 + LADO_ZOOM)))
            sh = int(math.ceil(h * (1 + LADO_ZOOM)))
            img = cobrir_foco(im, sw, sh, foco) if foco else cobrir_alto(im, sw, sh)
            if foco:
                nw, nh, jx, jy = janela_foco(im.size, sw, sh, foco)
                px, py = foco[0] * nw - jx, foco[1] * nh - jy
                # O zoom lento leva o ponto de 1/(1 + LADO_ZOOM) ate 1: contam as duas pontas.
                foco_na_celula = [(w / 2.0 + (px - sw / 2.0) * e, h / 2.0 + (py - sh / 2.0) * e)
                                  for e in (1.0 / (1.0 + LADO_ZOOM), 1.0)]
        celulas.append({"rect": (x, y, w, h), "vem": vem, "respira": respira,
                        "sprite": com_margem(img, "preto"),
                        "atraso": LADO_ATRASO + k * LADO_INTERVALO,
                        "foto": foto, "foco": foco_na_celula})
    textos = textos_do_grupo(textos, len(celulas))
    legenda = None
    if textos and opcoes["modo"] == "legenda":
        grupo = (texto or "").strip()
        legenda = legenda_por_foto([t or grupo for t in textos], opcoes["tamanho"])
        if legenda is not None and duracao:
            tempos = tempos_legenda_grupo("lado", len(celulas), duracao)
            for k, t, dura in legendas_curtas(legenda["textos"], tempos):
                avisar_legenda_curta(k, t, dura)
        textos = None
    capa = None if legenda is not None else faixa_texto(texto)
    if textos:
        lado_faixas(celulas, textos, capa, lay, opcoes["tamanho"])
    return {"tipo": "lado", "celulas": celulas, "capa": capa, "legenda": legenda, "opcoes": opcoes}


def limite_da_faixa_no_lado(texto, largura, tamanho=None):
    """A linha do ecra abaixo da qual a faixa de uma celula do lado a lado nao desce.

    A LEGENDA GUARDA LEGENDA_TEXTO DO FUNDO DO ECRA, E ESTA FAIXA GUARDA O MESMO. A
    primeira versao guardava so LEGENDA_FUNDO, a linha onde a faixa da legenda acaba, e
    as letras de uma celula que chega ao fundo ficavam a 54 pixeis do rebordo, fora da
    zona segura onde a legenda escreve. Agora e o bloco das linhas que fica em A -
    LEGENDA_TEXTO, como o da legenda: a faixa acaba uma almofada abaixo disso.
    """
    tamanho_px = linhas_texto_foto(texto, largura, tamanho)[0]
    return A - LEGENDA_TEXTO + int(round(tamanho_px * TEXTO_FOTO_ALMOFADA))


def lado_faixas(celulas, textos, capa, lay, tamanho=None):
    """Poe em cada celula com texto a sua faixa: cel["faixa"] = (cor, mascara, (x, y) na celula).

    A faixa fica no fundo da fotografia da celula, com a largura dela, e cola-se na celula
    depois do zoom lento: nao respira, nao e cortada pelo zoom e entra com a celula. Quatro
    coisas a mudam de sitio:
      - A LEGENDA DO GRUPO. A faixa da legenda e desenhada por cima de tudo, e uma faixa
        de foto por baixo dela ficava com duas camadas de preto e o texto ilegivel. Uma
        celula que desce ate a legenda leva a faixa para cima dela, com a folga do monte.
      - O FUNDO DO ECRA. Sem legenda, uma celula que acaba em A punha as letras a 20 pixeis
        do rebordo. Um projetor ou um televisor com overscan de 3 a 5% come mais do que
        isso: as letras saiam cortadas em baixo. Agora o bloco das linhas guarda do fundo
        o mesmo que o da legenda, ver limite_da_faixa_no_lado().
      - O FOCO. Se o ponto marcado cai na faixa OU ABAIXO DELA, em qualquer ponta do zoom
        lento, a faixa vai para o topo da fotografia da celula: o foco e onde esta a cara,
        e a regra e a de colocar_faixa(), que na colagem e na pilha manda a faixa para cima
        sempre que o foco esta do topo da faixa para baixo. Enquanto a faixa acabava no
        fundo do ecra, "na faixa" e "abaixo dela" eram o mesmo; desde que guarda a margem
        da legenda ha 22 pixeis de fotografia por baixo dela, e um foco marcado ai ficava
        com uma faixa preta em cima de metade da cara, sem subir.
      - O CARTAO DO 3s. As colunas dos lados tem a parte de dentro tapada pelo cartao, e
        com legenda a faixa delas sobe para a altura dele: o texto ficava meio escondido.
        Uma faixa que passe por tras do cartao encolhe para a parte da coluna que se ve.
    `tamanho` e a letra escolhida na Mesa, ver linhas_texto_foto().
    """
    limite_legenda = None
    if capa is not None:
        caixa = capa[1].getbbox()
        if caixa:
            limite_legenda = caixa[1] - MONTE_LEGENDA_FOLGA * A
    cartao = celulas[2]["rect"] if lay == "3s" and len(celulas) > 2 else None
    for k, cel in enumerate(celulas):
        texto = textos[k] if k < len(textos) else ""
        if not texto:
            continue
        x, y, w, h = cel["rect"]
        fx0, fy0, fx1, fy1 = cel.get("foto") or (0, 0, w, h)
        bx0, bx1 = fx0, fx1
        for _tentativa in range(3):
            faixa, cortado = capa_texto_foto(texto, bx1 - bx0, tamanho=tamanho)
            alt = min(faixa.height, fy1 - fy0)
            limite = limite_da_faixa_no_lado(texto, bx1 - bx0, tamanho)
            if limite_legenda is not None:
                limite = min(limite, limite_legenda)
            fundo = fy1
            if y + fundo > limite:
                fundo = max(fy0 + alt, min(fy1, int(math.floor(limite - y))))
            topo = fundo - alt
            if cel.get("foco") and any(py >= topo for _px, py in cel["foco"]):
                topo = fy0
            if cartao is None or k == 2:
                break
            cx, cy, cw, ch = cartao
            if not (y + topo < cy + ch and y + topo + alt > cy and x + bx0 < cx + cw and x + bx1 > cx):
                break
            if cx > x + bx0:
                bx1 = max(bx0 + 1, cx - x)
            else:
                bx0 = min(bx1 - 1, cx + cw - x)
        if alt < faixa.height:
            faixa = faixa.crop((0, 0, faixa.width, alt))
        cel["faixa"] = (faixa.convert("RGB"), faixa.split()[3], (int(bx0), int(topo)))
        if cortado:
            avisar_texto_cortado(k, texto)


def duracao_do_clip(clip):
    """A duracao_s do clip como numero, ou None se nao vier: so para os avisos da opcao legenda."""
    try:
        return float(clip.get("duracao_s") or 0.0) or None
    except (TypeError, ValueError):
        return None


def contador_legivel(texto):
    """O x deste contador le-se? A pergunta e a mesma que o preparar() faz, uma so.

    Existe para o carregar_montagem() poder dizer ao arrancar o que so se via no fotograma
    em que o contador entrava, a meio de um render de quinze minutos.
    """
    try:
        linha_tempo.ler_contador(texto)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def ler_aproxima(mov):
    """A coluna movimento -> (e aproxima?, zoom do fim, aviso).

    O zoom vai na mesma celula, "Aproxima 2.6", e nao numa coluna nova: e o unico
    enquadramento que tem um numero, e uma coluna a mais mudava o cabecalho de todas as
    montagens que existem. Escrito assim tambem se le: quem abrir o CSV ve o que vai ver.

    UM NUMERO FORA DOS LIMITES E RECUSADO, nao e cortado para a ponta mais proxima. A
    Mesa so deixa escolher entre APROXIMA_MIN e APROXIMA_MAX; um valor fora disto veio de
    alguem a escrever no CSV a mao, e calar um 12 transformando-o em 4 era esconder um
    engano. Fica a omissao, e o preparar diz que ficou.
    """
    pecas = (mov or "").split()
    if not pecas or pecas[0] != "Aproxima":
        return False, 0.0, ""
    if len(pecas) < 2:
        return True, APROXIMA_OMISSAO, ""
    try:
        az = float(pecas[1].replace(",", "."))
    except ValueError:
        return True, APROXIMA_OMISSAO, ("zoom %r que nao e um numero, fica %s"
                                        % (pecas[1], APROXIMA_OMISSAO))
    if not APROXIMA_MIN <= az <= APROXIMA_MAX:
        return True, APROXIMA_OMISSAO, ("zoom %g fora dos limites %g a %g, fica %s"
                                        % (az, APROXIMA_MIN, APROXIMA_MAX, APROXIMA_OMISSAO))
    return True, az, ""


# QUANTO A FOTO FICA PARA LA DA BORDA DO ECRA quando o travao a encosta, em pixeis do ecra.
# Encostada ao pixel, a fila de fora ja era amostrada pelo bicubico com a margem do sprite
# ao lado, e saia com outro brilho: medido numa foto lisa a 200, a fila 0 a 210 durante
# todo o tempo em que o travao atua, em "fiel" e em "fundo". E a borda que pisca do
# CLAUDE.md, em pequeno. Com a margem inteira e mais um pixel fora do ecra, a fila de fora
# e amostrada so de dentro da foto. Os mesmos 3 px estao na Mesa (APROXIMA_SOBRA).
APROXIMA_SOBRA = MARGEM + 1


def aproxima_centro(lado, tamanho, f):
    """Onde fica o centro da foto para o ponto de foco cair no meio do ecra.

    E A REGRA DE A FOTO NUNCA DESCOBRIR BORDA, escrita numa conta so. Com a foto a ocupar
    `tamanho` neste eixo, o centro dela so pode andar entre `lado - tamanho/2` e
    `tamanho/2`: fora disso entrava fundo por um dos lados. Enquanto a foto for mais
    pequena do que o ecra nesse eixo (o intervalo fica vazio) fica ao meio, que e onde o
    primeiro fotograma a poe e o que o aspeto dela manda.

    O intervalo e encolhido de APROXIMA_SOBRA de cada lado: quando o travao atua, a borda
    fica 3 px fora do ecra e nao em cima dele (ver a constante).

    E por isso que "aproxima-se so ate onde a foto chega": num zoom pequeno o ponto de
    foco ainda nao pode chegar ao centro, e a foto vai ate onde pode em vez de mostrar
    borda. Quem quiser o foco mesmo ao centro sobe o zoom, e o preparar diz quanto.

    Desde 18 de setembro a tarde so conta o FIM do movimento (preparar_aproxima()); o
    caminho ate la e o do aproxima_quadro().
    """
    return aproxima_trava(lado, tamanho, lado / 2.0 - (f - 0.5) * tamanho)


def aproxima_trava(lado, tamanho, c):
    """O centro `c` puxado para dentro do intervalo em que a foto nao descobre borda.

    A mesma conta que o aproxima_centro() sempre fez, separada dele porque o caminho do
    movimento tambem a usa, com outro centro que nao o do ponto de foco. Com a foto mais
    pequena do que o ecra nesse eixo o intervalo e vazio e fica ao meio.
    """
    baixo, cima = lado - tamanho / 2.0 + APROXIMA_SOBRA, tamanho / 2.0 - APROXIMA_SOBRA
    if baixo > cima:
        return lado / 2.0
    return min(cima, max(baixo, c))


def aproxima_zoom_que_centra(lado, tamanho_a_um, f):
    """O zoom a partir do qual o ponto de foco ja pode ficar ao centro. None se nunca.

    So serve para o aviso: e o numero que o Tiago escreve na Mesa se quiser o foco mesmo
    no meio. Sai da mesma desigualdade do aproxima_centro(): |0,5 - f| . tamanho . z
    tem de caber em tamanho . z / 2 - lado / 2 - APROXIMA_SOBRA.
    """
    folga = 0.5 - abs(f - 0.5)
    if folga <= 1e-9:
        return None
    return (lado / 2.0 + APROXIMA_SOBRA) / (tamanho_a_um * folga)


def aproxima_zoom_sugerido(precisos):
    """O zoom que se sugere ao Tiago, a partir do zoom que centra cada eixo que ficou preso.

    ARREDONDA PARA CIMA, A DECIMA, e e o mesmo numero que a Mesa diz (zoomQueCentra). Ate 18
    de setembro o preparar imprimia com "%.1f", ao mais proximo: na foto do anel o zoom que
    centra e 2,73, o preparar dizia 2,7 e a Mesa 2,8, e com 2,7 posto o preparar voltava a
    queixar-se e a sugerir o mesmo 2,7. Um numero sugerido tem de funcionar quando e escrito.

    None quando um eixo nunca centra (o ponto de foco na propria borda da foto) ou quando
    nem o zoom maximo chega: nesse caso nao ha numero para escrever, e diz-se isso.
    """
    if not precisos or any(p is None for p in precisos):
        return None
    z = math.ceil(max(precisos) * 10) / 10.0
    return z if z <= APROXIMA_MAX else None


def aproxima_alvo(ap, nivel):
    """(largura, altura) do alvo de um nivel, sem o fazer: as mesmas contas do encaixar().

    O NIVEL NUNCA PASSA O TAMANHO DO FICHEIRO. Os niveis eram reducoes Lanczos do original
    cada vez maiores, e a partir de certo zoom deixavam de ser reducoes: a 4,0 o nivel de
    cima de uma foto de 12 MP era uma AMPLIACAO para cerca de 6300x4700, sem um unico
    pormenor a ganhar, feita por cada uma das sete fatias. Medido pelo verificador: 442 MB
    de pico num processo a 4,0, contra 111 MB no zoom lento de sempre. Acima do ficheiro fica
    o proprio ficheiro, e o que falta crescer cresce no compor().

    E NUNCA FICA ABAIXO DO NIVEL 0. Numa foto mais pequena do que o ecra o nivel 0 ja e uma
    ampliacao (o sprite de sempre), e trocar para o ficheiro original a meio do clip era
    passar para uma imagem mais pequena: fica o sprite de sempre ate ao fim.
    """
    if nivel <= 0:
        return ap["alvo0"]
    w, h = ap["im"].size
    k = (1.0 + ZOOM) ** (nivel + 1)
    f = min(int(L * k) / w, int(A * k) / h)
    if f < 1.0:
        return max(1, round(w * f)), max(1, round(h * f))
    return ap["alvo0"] if ap["alvo0"][0] >= w else (w, h)


def aproxima_nivel_de(r):
    """O nivel do zoom r: o mais pequeno que ainda da uma reducao (escala ate 1) no compor()."""
    return max(0, int(math.ceil(math.log(r) / math.log(1.0 + ZOOM))) - 1)


def preparar_aproxima(im, alvo, modo, az, foco, nome=""):
    """O que o enquadramento "aproxima" precisa de saber, contado uma vez por clip.

    O PRIMEIRO FOTOGRAMA TEM DE SER O DE HOJE, ao byte, senao isto deixa de ser "comeca
    como esta" e passa a ser outro enquadramento. Por isso o nivel 0 e o sprite de sempre,
    o mesmo `alvo` que o preparar() ja fez, e a escala de partida e a mesma expressao de
    sempre, 1/(1+ZOOM), com o centro em L/2 e A/2 (que e onde o aproxima_centro() poe uma
    foto encaixada, porque encaixada ela nunca passa o ecra).

    E DEPOIS O SPRITE TEM DE CRESCER COM O MOVIMENTO. Com um sprite so, o de hoje, um
    zoom de 2,2 pedia a Pillow que ampliasse quase duas vezes uma imagem ja reduzida, e o
    anel chegava ao fim desfocado, que e exatamente o que este enquadramento existe para
    resolver. Com um sprite grande desde o inicio era pior ao contrario: o primeiro
    fotograma seria uma reducao de 1 para 2,2 feita pelo transform(), que amostra sem
    alargar o filtro e por isso serrilha.

    Entao ha NIVEIS, cada um 1+ZOOM maior do que o anterior, e o clip vai trocando de
    nivel a medida que fecha. A escala pedida ao compor() fica sempre entre 1/(1+ZOOM) e
    1, que e a gama em que o resto do filme ja trabalha, e cada nivel e uma reducao
    Lanczos tirada do ficheiro original. Na troca, o que se ve de um lado e de outro e a
    mesma imagem no mesmo tamanho, feita por dois caminhos que diferem abaixo do pixel.
    """
    base = 1.0 / (1.0 + ZOOM)
    ap = {"im": im, "modo": modo, "az": az, "base": base,
          "sprite0": com_margem(alvo, modo), "alvo0": alvo.size,
          "fw": alvo.width * base, "fh": alvo.height * base,
          "foco": foco or (0.5, 0.5), "_nivel": None}
    quem = " (%s)" % nome if nome else ""
    if foco is None:
        print("  aproxima sem ponto de foco marcado%s: fecha ao centro da foto" % quem)
    # QUANTO FOI, quando nao foi ate ao fim. Vale a pena dizer porque a correcao e de uma
    # palavra na Mesa: sobe-se o zoom e o foco fica onde ele o marcou. Conta-se no tamanho
    # que vai mesmo ao ecra no fim, o do sprite do nivel de cima (ver aproxima_quadro()).
    aw, ah = aproxima_alvo(ap, aproxima_nivel_de(az))
    faltou, precisos = [], []
    for eixo, lado, tamanho, f in (("largura", L, ap["fw"], ap["foco"][0]),
                                   ("altura", A, ap["fw"] * ah / aw, ap["foco"][1])):
        ideal = lado / 2.0 - (f - 0.5) * tamanho * az
        desvio = abs(aproxima_centro(lado, tamanho * az, f) - ideal)
        if desvio < 1.0:
            continue
        faltou.append((eixo, desvio))
        precisos.append(aproxima_zoom_que_centra(lado, tamanho, f))
    ap["faltou"], ap["sugerido"] = faltou, aproxima_zoom_sugerido(precisos)
    # O CAMINHO E PLANEADO UMA VEZ, do centro do primeiro fotograma ao do ultimo (ver
    # aproxima_quadro()). O do fim conta-se com o tamanho do sprite que la vai estar, o
    # mesmo que o aproxima_quadro() desenha em p = 1, e por isso o ultimo fotograma e o de
    # antes, ao byte. `enche` diz em que eixo a foto ja enche o ecra no primeiro fotograma:
    # o encaixar() poe um dos lados no ecra, a menos de meio pixel do arredondamento.
    larg1, alt1 = aproxima_tamanho(ap, 1.0 + (az - 1.0) * aproxima_curva(1.0))
    ap["fim"] = (aproxima_centro(L, larg1, ap["foco"][0]), aproxima_centro(A, alt1, ap["foco"][1]))
    ap["enche"] = (ap["fw"] >= L - 1.0, ap["fh"] >= A - 1.0)
    if faltou:
        print("  aproxima com o zoom %g%s: no fim o ponto de foco fica a %s, porque a foto "
              "acaba antes e nao se mostra borda; %s"
              % (az, quem, " e ".join("%d px na %s" % (round(d), e) for e, d in faltou),
                 ("ficaria ao centro com o zoom %.1f" % ap["sugerido"]) if ap["sugerido"] else
                 ("nem com o zoom maximo, %.1f, ficava ao centro" % APROXIMA_MAX)))
    return ap


def aproxima_nivel(ap, nivel):
    """(sprite, fator de escala) de um nivel, feito a primeira vez que e preciso.

    Guarda-se so o ultimo: dentro de um clip o zoom so cresce, portanto cada nivel e
    feito uma vez e o anterior nao volta a servir. Guardar todos eram centenas de MB por
    clip, vezes o numero de fatias. A chave e o tamanho do alvo e nao o numero do nivel:
    acima do tamanho do ficheiro todos os niveis sao o mesmo sprite (aproxima_alvo()), e
    refaze-lo a cada troca era trabalho deitado fora.
    """
    medidas = aproxima_alvo(ap, nivel)
    if ap["_nivel"] is not None and ap["_nivel"][0] == medidas:
        return ap["_nivel"][1], ap["_nivel"][2]
    if medidas == ap["alvo0"]:
        sprite, fator = ap["sprite0"], ap["base"]
    elif medidas == ap["im"].size:
        sprite, fator = com_margem(ap["im"], ap["modo"]), ap["fw"] / ap["im"].width
    else:
        k = (1.0 + ZOOM) ** (nivel + 1)
        alvo = encaixar(ap["im"], int(L * k), int(A * k))
        sprite, fator = com_margem(alvo, ap["modo"]), ap["fw"] / alvo.width
    ap["_nivel"] = (medidas, sprite, fator)
    return sprite, fator


def aproxima_tamanho(ap, r):
    """(largura, altura) da foto no ecra ao zoom r, sem fazer o sprite.

    As mesmas contas do aproxima_nivel() e do aproxima_quadro(): o alvo do nivel, que e o
    tamanho do encaixar() sem a margem, vezes a escala r . fator. Serve para planear o fim
    do movimento no preparar sem fazer o sprite do nivel de cima, que numa foto de 12 MP e
    uma reducao Lanczos cara e que o aproxima_nivel() so guarda um de cada vez.
    """
    aw, ah = aproxima_alvo(ap, aproxima_nivel_de(r))
    fator = ap["base"] if (aw, ah) == ap["alvo0"] else ap["fw"] / aw
    escala = r * fator
    return aw * escala, ah * escala


# O MOVIMENTO CABE ENTRE OS DOIS ENCADEADOS, 18 de setembro. O Tiago pediu "comecar do
# plano amplo para verem a arvore de natal", e o movimento ocupava o clip inteiro: comecava
# debaixo do encadeado de entrada, com a foto a pesar 3%, e acabava debaixo do de saida. Na
# foto do anel (f0260, a seguir ao contador, 0,7 s de cada lado) a arvore via-se inteira
# durante meio segundo, e o zoom pedido so se atingia no ultimo fotograma, com a foto a
# desaparecer: com ela sozinha no ecra o anel nunca passava de 2,06 (verificador).
#
# Agora a foto entra parada, inteira, exatamente o primeiro fotograma de hoje; so quando o
# encadeado de entrada acaba e que comeca a aproximar; e chega ao zoom pedido no instante
# em que a seguinte comeca a entrar, e fica ali, parada, enquanto a outra aparece.
#
# NUM CLIP CURTO DE MAIS o movimento volta a ocupar o clip inteiro: com menos de
# APROXIMA_MOVIMENTO_MIN entre os dois encadeados, ir de 1 a 2,2 era um salto, e um salto e
# pior do que o fim ficar debaixo do encadeado. O preparar diz quando isso acontece.
APROXIMA_MOVIMENTO_MIN = 1.0
# PARADO NO PLANO AMPLO E PARADO NO FIM. O Tiago, sobre a foto do anel: "tens de comecar do
# plano amplo para verem a arvore de natal". Com o movimento a arrancar logo que a foto
# acabava de entrar, a arvore inteira via-se 0,72 s e o anel no tamanho final menos de 1 s,
# e o fim parava a seco a 94% do zoom (verificador, 18 de setembro). A janela passa a
# guardar este tempo parado em cada ponta; num clip apertado as duas paragens encolhem por
# igual, e o movimento nunca fica abaixo de APROXIMA_MOVIMENTO_MIN.
APROXIMA_PARADO = 1.0


def aproxima_curva(p):
    """Sai do repouso e chega em repouso: o zoom arranca devagar e trava devagar.

    Com a paragem no fim (APROXIMA_PARADO) a curva tem de chegar parada. O arrancar(), que
    chega a andar, dava ali o solavanco de um carro a travar a fundo.
    """
    p = max(0.0, min(1.0, p))
    return p * p * (3.0 - 2.0 * p)


def aproxima_janela(duracao, entra, sai):
    """(comeco, fim) do movimento do aproxima, em segundos do clip. Ver APROXIMA_MOVIMENTO_MIN.

    `entra` e o encadeado de entrada do clip e `sai` o do clip seguinte (ou o fade do fim),
    os mesmos que a colagem e a pilha usam (ligar_transicoes). Sem encadeados, o clip
    inteiro, que e onde o movimento estava antes: os fotogramas sao os mesmos.
    """
    duracao = float(duracao)
    a = max(0.0, float(entra or 0.0))
    b = duracao - max(0.0, float(sai or 0.0))
    if b - a < APROXIMA_MOVIMENTO_MIN:
        return 0.0, duracao
    parado = min(APROXIMA_PARADO, (b - a - APROXIMA_MOVIMENTO_MIN) / 2.0)
    return a + parado, b - parado


def aproxima_progresso(ap, t_rel, duracao):
    """O p do aproxima_quadro() no instante t_rel: 0 ate o encadeado de entrada acabar, 1 desde o de saida."""
    a, b = aproxima_janela(duracao, ap.get("entra", 0.0), ap.get("sai", 0.0))
    if b <= a:
        return 0.0
    return min(1.0, max(0.0, (t_rel - a) / (b - a)))


def aproxima_quadro(ap, p):
    """(sprite, escala, cx, cy) do fotograma em p, de 0 a 1, o avanco do movimento.

    A CURVA E A DO aproxima_curva(): sai do repouso e chega em repouso. Comecar a andar de
    repente num quadro parado le-se como solavanco, e parar de repente tambem. O movimento
    fica entre as duas paragens de APROXIMA_PARADO (aproxima_janela()): o plano amplo parado
    depois de a foto entrar, e o fim parado antes de a seguinte comecar.

    O CENTRO ANDA EM LINHA RECTA, com a mesma curva do zoom: do centro do primeiro
    fotograma, o meio do ecra, ao do ultimo, ap["fim"], que e o aproxima_centro() no zoom
    pedido. Ate 18 de setembro a tarde o travao da borda era aplicado fotograma a
    fotograma ao centro ideal de cada zoom, e cada vez que prendia ou largava um eixo a
    velocidade mudava de repente: na foto do anel a 2,2, tres quebras no ultimo segundo, a
    ultima uma guinada para a direita antes de parar, e a 2,8 a pedra ia para a esquerda e
    voltava para a direita (verificador). Em linha recta todos os pontos do ecra andam com
    a velocidade do arrancar(), sem quebras nem inversoes, e cada borda da foto anda
    sempre para fora: a barra que a foto tinha no primeiro fotograma so diminui, e acaba
    onde o aproxima_centro() a poe.

    O TRAVAO SO FICA NO EIXO QUE A FOTO JA ENCHE NO PRIMEIRO FOTOGRAMA (ap["enche"]). Ai a
    linha recta passa no maximo a sobra e meio pixel fora do intervalo sem borda, e sem o
    travao, com o ponto de foco preso a borda, a borda da foto ficava quase parada dentro
    da sobra durante o clip inteiro, a trocar de brilho a cada troca de nivel (a borda que
    pisca do CLAUDE.md). Com ele fica APROXIMA_SOBRA px fora do ecra, como antes. O preco e
    uma quebra so, no arranque, com a foto quase parada: medido na foto do anel, a pedra
    desce menos de 2 px e passa a subir, uma mudanca de cerca de 1 px por fotograma, que
    tambem havia antes. No outro eixo a foto comeca com barras e o travao nao pode atuar
    sem dar um salto: quando ela passa a cobrir o ecra, o unico centro sem borda e o meio,
    e a linha recta ja la nao esta; ai a barra da borda so diminui e fecha no fim.
    """
    e = aproxima_curva(p)
    r = 1.0 + (ap["az"] - 1.0) * e
    sprite, fator = aproxima_nivel(ap, aproxima_nivel_de(r))
    escala = r * fator
    # O TAMANHO QUE VAI AO ECRA E O DO SPRITE DESTE NIVEL, e nao o do nivel 0 vezes r. Cada
    # nivel e um encaixar() com o seu arredondamento, e numa foto de 2248x4000 a altura do
    # nivel 4 fica 1,6 px abaixo de fh . r. Com a conta do nivel 0 o travao encostava a
    # foto ao cimo do ecra numa altura que ela nao tinha, e a fila de cima ficava por
    # cobrir: escura, e com outro brilho a cada troca de nivel, a borda que pisca do
    # CLAUDE.md (verificador, 18 de setembro: a fila 0 a valer 36, 101, 0 e 86 sobre uma
    # foto a 124). No nivel 0 as duas contas sao a mesma, e o primeiro fotograma nao muda.
    larg = (sprite.width - 2 * MARGEM) * escala
    alt = (sprite.height - 2 * MARGEM) * escala
    # (1 - e) . meio + e . fim, e nao meio + (fim - meio) . e: assim p = 0 da o meio e p = 1
    # da o fim exatos, sem o arredondamento da subtracao, e os dois fotogramas das pontas
    # sao os de antes ao byte.
    centro = []
    for lado, tamanho, fim, enche in ((L, larg, ap["fim"][0], ap["enche"][0]),
                                      (A, alt, ap["fim"][1], ap["enche"][1])):
        c = (lado / 2.0) * (1.0 - e) + fim * e
        centro.append(aproxima_trava(lado, tamanho, c) if enche else c)
    return sprite, escala, centro[0], centro[1]


def compor_visivel(tela, sprite, cx, cy, escala):
    """O compor(), mas a amostrar so a parte da foto que cai dentro da tela. Igual ao byte.

    O compor() amostra a foto inteira no tamanho a que ela vai e so depois recorta o que
    cabe no ecra. No zoom lento de sempre isso e quase o mesmo, mas no "aproxima" a 2,2 a
    foto vai a 3600x2400 e a 4,0 passa os 6000 px de largura, e cada fotograma amostrava
    tres a doze ecras inteiros para deitar fora tudo menos um. Com o nivel de cima, era
    isso que punha um fotograma a levar mais de dois segundos.

    As contas sao as do compor() com a origem deslocada para o canto que se ve, e o
    teste_aproxima_comeca_igual_e_acaba_no_foco confirma que os pixeis saem iguais aos do
    compor(). E so o aproxima que passa por aqui: os outros clips nao mudam de caminho.
    """
    m = MARGEM
    larg = (sprite.width - 2 * m) * escala
    alt = (sprite.height - 2 * m) * escala
    x0, y0 = cx - larg / 2.0, cy - alt / 2.0
    ix, iy = math.floor(x0), math.floor(y0)
    fx, fy = x0 - ix, y0 - iy
    cw = int(math.ceil(larg + fx)) + m
    ch = int(math.ceil(alt + fy)) + m
    px0, py0 = max(0, -ix), max(0, -iy)
    px1 = min(cw, tela.width - ix)
    py1 = min(ch, tela.height - iy)
    if px1 <= px0 or py1 <= py0:
        return
    inv = 1.0 / escala
    recorte = sprite.transform((px1 - px0, py1 - py0), Image.AFFINE,
                               (inv, 0.0, -fx * inv + m + px0 * inv,
                                0.0, inv, -fy * inv + m + py0 * inv),
                               resample=Image.BICUBIC)
    if recorte.mode == "RGBA":
        tela.paste(recorte, (ix + px0, iy + py0), recorte)
    else:
        tela.paste(recorte, (ix + px0, iy + py0))


def preparar(clip, inv_por_nome):
    """Prepara o clip uma vez: sprite no tamanho maximo e legenda em camada.

    A coluna `tratamento` da montagem escolhe o aspeto:
      fiel    o da mae da Clara: encaixa com barras pretas e zoom lento
      fundo   o fundo passa a ser a propria foto ampliada e desfocada
      rajada  enche o ecra, sem movimento, para cortes secos
    No lado a lado e a disposicao, e na colagem e na pilha o estilo, ver ESTILOS_MONTE.
    """
    texto = clip["texto_ecra"]
    if clip["tipo"] == "cartao":
        return {"tipo": "cartao", "base": cartao(texto), "capa": None}
    if clip["tipo"] == "contador":
        # DOIS FORMATOS, UM SO TIPO DE CLIP. O de anos, "2026>1995|...", e o de sempre;
        # o de datas, "04/10/2026>25/12/2025|...", e de 17 de setembro, para a abertura
        # rebobinar do dia do casamento ate ao dia do pedido antes de ir a 1995.
        #
        # UM X MAL ESCRITO NAO PARA UM RENDER DE QUINZE MINUTOS. E a regra do
        # imagem_da_marca(): o campo do contador aceita texto livre, e "04/10/2026>1995"
        # (uma ponta data, a outra ano) fazia o ler_datas rebentar com ValueError no
        # fotograma em que o contador entra, ou seja la a meio; com fatias, a fatia morre e
        # o pai apaga o _corpo.mp4 e perde tudo o que ja estava desenhado. Vale o mesmo que
        # uma foto que nao abre: cartao preto, o nome nos faltaram, e o filme continua. O
        # carregar_montagem() ja avisou ao arrancar, que e onde isto se ve a tempo.
        try:
            modo, de, para, marcos = linha_tempo.ler_contador(texto)
        except (ValueError, AttributeError, TypeError):
            return None
        if modo == "datas" and abs((para - de).days) > linha_tempo.DIAS_MAXIMOS_DATAS:
            # ACIMA DE TRES ANOS A REGUA DE MESES NAO SE LE e cada fotograma salta
            # semanas. Em vez de desenhar uma coisa ilegivel sem ninguem saber porque,
            # desenha-se o contador de anos das duas datas, que e o que serve ali, e
            # diz-se. Silencio aqui era um clip de nove segundos a nao dizer nada.
            print("  contador de %s a %s: %d dias e mais de %d, fica o contador de anos"
                  % (de.isoformat(), para.isoformat(), abs((para - de).days),
                     linha_tempo.DIAS_MAXIMOS_DATAS))
            modo, de, para = "anos", de.year, para.year
            marcos = [(d.year, t) for d, t in marcos]
        return {"tipo": "contador", "modo": modo, "de": de, "para": para,
                "marcos": marcos}
    if clip["tipo"] == "marcos":
        ano, marcas, troco, abre = linha_tempo.ler_meses(texto)
        return {"tipo": "marcos", "ano": ano, "marcas": marcas,
                "troco": troco, "abre": abre}

    if clip["tipo"] == "video":
        # UM VIDEO DO CORPO DESENHA-SE COMO QUALQUER OUTRO CLIP, e o que ele tem para
        # desenhar sao os fotogramas que o processo principal ja extraiu para a cache. Nao
        # se abre aqui o MP4: a Pillow nao le video, e mandar o ffmpeg buscar um fotograma
        # de cada vez, sete fatias ao mesmo tempo, era mais lento do que o filme todo.
        pasta = clip.get("_quadros") or ""
        if not pasta or not os.path.isdir(pasta):
            # NAO SE CRIA A CACHE AQUI. Se a pasta nem existe, quem falhou foi o passo de
            # antes, e dizer-se isto e melhor do que sete fatias a extrair o mesmo video ao
            # mesmo tempo. Numa fatia a mensagem vai para o stderr e o pai repete-a.
            sys.exit("os fotogramas do video %s nao estao na cache %s: quem os extrai e o "
                     "processo principal do render, antes de lancar as fatias, ou a pasta "
                     "foi apagada por outro render da mesma montagem a correr ao lado"
                     % (clip.get("ficheiro") or "(sem nome)", pasta or "(sem pasta)"))
        quadros = quadros_da_cache(pasta)
        if not quadros:
            # A pasta existe e esta vazia: o processo principal tentou, nao conseguiu (o
            # ficheiro nao esta em disco, ou o ffmpeg queixou-se) e ja o disse. Aqui vale a
            # regra do imagem_da_marca(): um ficheiro em falta nao pode parar um render de
            # quinze minutos a meio. Fica o cartao preto que fica uma foto que nao abre, e
            # o nome vai para os faltaram, que o render lista no fim.
            return None
        return {"tipo": "video", "quadros": quadros, "capa": faixa_texto(texto)}

    if clip["tipo"] == "lado":
        lay = (clip.get("tratamento") or "").strip()
        caminhos = clip.get("_caminhos") or []
        focos = [ler_foco(p) for p in (clip.get("fonte_imagem") or "").split("|")]
        if lay not in LAYOUTS_LADO or len(caminhos) != LAYOUTS_LADO[lay]:
            return None
        if not all(c and os.path.exists(c) for c in caminhos):
            return None
        imagens = [ImageOps.exif_transpose(Image.open(c)).convert("RGB") for c in caminhos]
        return preparar_lado(lay, imagens, focos, texto,
                             ler_textos_fotos(clip.get("textos_fotos")),
                             ler_textos_opcoes(clip.get("textos_opcoes")),
                             duracao_do_clip(clip))

    if clip["tipo"] in LIMITES_MONTE:
        minimo, maximo = LIMITES_MONTE[clip["tipo"]]
        caminhos = clip.get("_caminhos") or []
        if not (minimo <= len(caminhos) <= maximo):
            return None
        imagens = []
        for c in caminhos:
            if not c or not os.path.exists(c):
                return None
            imagens.append(ImageOps.exif_transpose(Image.open(c)).convert("RGB"))
        focos = [ler_foco(p) for p in (clip.get("fonte_imagem") or "").split("|")]
        # Os encadeados vem do main, por ligar_transicoes: _transicao_entrada, que e
        # zero no primeiro clip do corpo, e _transicao_seguinte, que e o do clip
        # seguinte ou o fade a preto do fim. Sem eles contam o do proprio clip.
        entra = clip.get("_transicao_entrada")
        entra = float(clip.get("transicao_s") or 0.0) if entra in (None, "") else float(entra)
        sai = clip.get("_transicao_seguinte")
        sai = entra if sai in (None, "") else float(sai)
        # O estilo vem na coluna tratamento, decisao 068. O "fiel" das montagens de antes
        # e qualquer valor desconhecido dao a omissao, ver estilo_monte().
        return preparar_monte(clip["tipo"], imagens, focos, texto, entra, sai,
                              clip.get("tratamento"),
                              textos=ler_textos_fotos(clip.get("textos_fotos")),
                              opcoes=ler_textos_opcoes(clip.get("textos_opcoes")),
                              duracao=duracao_do_clip(clip))

    caminho = clip.get("_caminho")
    if not caminho or not os.path.exists(caminho):
        r = inv_por_nome.get((clip["ficheiro"] or "").lower())
        caminho = r["caminho"] if r else None
    if not caminho or not os.path.exists(caminho):
        return None

    tratamento = (clip.get("tratamento") or "fiel").strip() or "fiel"
    im = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")

    if tratamento == "rajada":
        return {"tipo": "rajada",
                "base": cobrir_foco(im, L, A, ler_foco(clip.get("fonte_imagem"))) or cobrir(im, L, A),
                "capa": faixa_texto(texto)}

    escala_max = 1.0 + ZOOM
    alvo = encaixar(im, int(L * escala_max), int(A * escala_max))
    fundo = None
    if tratamento == "fundo":
        fundo = cobrir(im, L, A).filter(ImageFilter.GaussianBlur(46))
        fundo = Image.blend(Image.new("RGB", (L, A), (0, 0, 0)), fundo, 0.55)
    # A margem depende do que fica por tras: preto no aspeto dela, repeticao
    # da fila de fora quando o fundo e a propria foto desfocada. Ver com_margem().
    modo = "esticar" if fundo is not None else "preto"
    mov = (clip.get("movimento") or "").strip()
    pronto = {"tipo": "foto", "sprite": com_margem(alvo, modo), "fundo": fundo,
              "capa": faixa_texto(texto), "mov": mov}
    # O "aproxima" traz mais contas e mais um sprite, e por isso so se prepara quando e
    # pedido: sem ele o clip fica byte a byte o que era antes deste enquadramento existir.
    aproxima, az, aviso = ler_aproxima(mov)
    if aproxima:
        if aviso:
            print("  aproxima do clip %s com %s" % (clip.get("ordem", "?"), aviso))
        ap = preparar_aproxima(im, alvo, modo, az, ler_foco(clip.get("fonte_imagem")),
                               clip.get("ficheiro") or "")
        # OS ENCADEADOS, para o movimento caber entre eles (aproxima_janela()). Vem do main,
        # por ligar_transicoes, como os da colagem e da pilha; sem eles conta o do proprio
        # clip, dos dois lados.
        entra = clip.get("_transicao_entrada")
        entra = float(clip.get("transicao_s") or 0.0) if entra in (None, "") else float(entra)
        sai = clip.get("_transicao_seguinte")
        sai = entra if sai in (None, "") else float(sai)
        ap["entra"], ap["sai"] = entra, sai
        dur = float(clip.get("duracao_s") or 0.0)
        if (entra or sai) and aproxima_janela(dur, entra, sai) == (0.0, dur):
            print("  aproxima do clip %s: entre os encadeados ficam %.1f s, menos de %.1f; o "
                  "movimento ocupa o clip inteiro e acaba debaixo do encadeado de saida"
                  % (clip.get("ordem", "?"), max(0.0, dur - entra - sai), APROXIMA_MOVIMENTO_MIN))
        pronto["aproxima"] = ap
    return pronto


def desenhar(pronto, t_rel, duracao):
    """Um fotograma do clip, no instante t_rel."""
    if pronto["tipo"] == "cartao":
        tela = Image.new("RGB", (L, A), (0, 0, 0))
        tela.paste(pronto["base"], (0, 0))
        return tela
    if pronto["tipo"] == "contador":
        # O modo foi decidido no preparar, e so la: um clip preparado como anos desenha
        # sempre anos, mesmo que as duas datas de onde veio ainda estejam no texto.
        desenho = linha_tempo.datas if pronto.get("modo") == "datas" else linha_tempo.anos
        return desenho(L, A, pronto["de"], pronto["para"],
                       pronto["marcos"], t_rel, duracao)
    if pronto["tipo"] == "video":
        # O FOTOGRAMA MAIS PROXIMO, SEM INTERPOLAR. A cache foi extraida a 25 fps, a
        # cadencia do filme, portanto o fotograma k e o instante k/25 do troco e a conta e
        # exata. Misturar dois fotogramas vizinhos so borrava o movimento.
        quadros = pronto["quadros"]
        k = min(len(quadros) - 1, max(0, int(round(t_rel * FPS))))
        with Image.open(quadros[k]) as ficheiro:
            im = ficheiro.convert("RGB")
        tela = Image.new("RGB", (L, A), (0, 0, 0))
        # A REGRA DOS SPRITES VALE AQUI TAMBEM: tudo o que entra numa composicao de
        # sub-pixel vem de com_margem(). Com escala 1 e ao centro a amostragem cai em
        # posicoes inteiras e os pixeis sao os mesmos, mas um encadeado ou uma margem
        # esquecida sao exatamente como nasce a borda que pisca.
        compor(tela, com_margem(im, "preto"), L / 2.0, A / 2.0, 1.0)
        if pronto["capa"] is not None:
            cor, mascara = pronto["capa"]
            tela.paste(cor, (0, 0), mascara)
        return tela
    if pronto["tipo"] == "marcos":
        return linha_tempo.meses(L, A, pronto["ano"], pronto["marcas"],
                                 t_rel, duracao, pronto["troco"],
                                 pronto.get("abre", True))
    if pronto["tipo"] == "lado":
        # Cada foto e composta na sua propria celula, com sub-pixel e margem, e
        # so depois colada no ecra. A celula e que corta, portanto o zoom lento
        # nunca invade a foto do lado. A entrada anda depressa, a pixeis
        # inteiros chega; o que tem de ser sub-pixel e o movimento lento.
        tela = Image.new("RGB", (L, A), (0, 0, 0))
        for cel in pronto["celulas"]:
            x, y, w, h = cel["rect"]
            e = (t_rel - cel["atraso"]) / LADO_ENTRADA
            if e <= 0:
                continue
            e = 1.0 - (1.0 - min(1.0, e)) ** 3      # entra depressa e pousa devagar
            pousa = cel["atraso"] + LADO_ENTRADA
            resp = 0.0
            if cel["respira"] and duracao > pousa:
                resp = min(1.0, max(0.0, t_rel - pousa) / (duracao - pousa))
            escala = (1.0 + LADO_ZOOM * resp) / (1.0 + LADO_ZOOM)
            peca = Image.new("RGB", (w, h), (0, 0, 0))
            compor(peca, cel["sprite"], w / 2.0, h / 2.0, escala)
            if cel.get("faixa") is not None:
                # Depois do zoom lento e antes da entrada: a faixa do texto da foto nao
                # respira nem sai pela borda com o zoom, e entra com a celula.
                faixa_cor, faixa_mascara, onde = cel["faixa"]
                peca.paste(faixa_cor, onde, faixa_mascara)
            dx = dy = 0
            if cel["vem"] == "esq":
                dx = -int(round((1.0 - e) * (x + w)))
            elif cel["vem"] == "dir":
                dx = int(round((1.0 - e) * (L - x)))
            else:
                dy = int(round((1.0 - e) * (A - y)))
            tela.paste(peca, (x + dx, y + dy))
        colar_legenda(tela, pronto, t_rel, duracao, [c["atraso"] for c in pronto["celulas"]])
        return tela
    if pronto["tipo"] in LIMITES_MONTE:
        return desenhar_monte(pronto, t_rel, duracao)
    if pronto["tipo"] == "rajada":
        tela = pronto["base"].copy()
        if pronto["capa"] is not None:
            cor, mascara = pronto["capa"]
            tela.paste(cor, (0, 0), mascara)
        return tela
    if pronto.get("fundo") is not None:
        tela = pronto["fundo"].copy()
    else:
        tela = Image.new("RGB", (L, A), (0, 0, 0))
    p = t_rel / duracao if duracao else 0.0
    # O "APROXIMA" TEM CENTRO E SPRITE PROPRIOS, e por isso sai antes dos outros: comeca
    # onde eles comecam e acaba fechado no ponto de foco. Ver preparar_aproxima().
    if pronto.get("aproxima") is not None:
        ap = pronto["aproxima"]
        sprite, escala, cx, cy = aproxima_quadro(ap, aproxima_progresso(ap, t_rel, duracao))
        compor_visivel(tela, sprite, cx, cy, escala)
        if pronto["capa"] is not None:
            cor, mascara = pronto["capa"]
            tela.paste(cor, (0, 0), mascara)
        return tela
    # O ENQUADRAMENTO vem da Mesa, na coluna movimento. O Tiago, sobre a IMG_0622:
    # "Esta com um zoom muito grande na foto do Tiago". A foto e um plano apertado
    # de 1,5 que ja enche a altura, e o zoom lento ainda a aproxima 12%. Afastada
    # mostra-a inteira a 80% com a margem a volta; parada tira o zoom. Os outros
    # valores ("Zoom in", "Nenhum" das v1) continuam como sempre foram.
    mov = pronto.get("mov", "")
    if mov == "Parada":
        escala = 1.0 / (1.0 + ZOOM)
    elif mov == "Afastada":
        escala = (AFASTADA + AFASTADA_RESPIRA * p) / (1.0 + ZOOM)
    else:
        escala = (1.0 + ZOOM * p) / (1.0 + ZOOM)
    compor(tela, pronto["sprite"], L / 2.0, A / 2.0, escala)
    if pronto["capa"] is not None:
        cor, mascara = pronto["capa"]
        tela.paste(cor, (0, 0), mascara)
    return tela


def ler_abafar(celula):
    """A coluna `abafar` do som.csv -> [(inicio, fim, fator)], no relogio do corpo.

    E onde o leito tem de estar mais baixo por causa das vozes do pedido. A coluna so
    existe quando ha vozes, e um som.csv de antes delas nao a tem: ausente, vazia ou mal
    escrita valem todas o mesmo, nenhuma janela, e o leito toca como sempre tocou.
    """
    fora = []
    for peca in (celula or "").split(";"):
        peca = peca.strip()
        if not peca:
            continue
        faixa, _, fator = peca.partition("x")
        a, _, b = faixa.partition("-")
        try:
            fora.append((float(a), float(b), float(fator)))
        except ValueError:
            continue
    return fora


def entra_depressa(e):
    """As faixas que nao sao musica de fundo: as vozes do pedido e o som de um video do corpo.

    As tres coisas que as distinguem de uma musica sao as mesmas nas duas, e por isso a
    pergunta e uma so: nao levam loudnorm (igualar o «D'oh» do Homer ou uma frase
    sussurrada do pedido a uma cancao dos anos 80 destroi exatamente o que elas tem),
    entram e saem em VOZ_FADE em vez de um segundo (um segundo de subida num «D'oh» de 3,5
    s da-lhe um volume que ele nao tem) e nunca sao esticadas pelo cruzamento, que as poria
    a tocar por cima do que vem a seguir.
    """
    return bool(e.get("voz")) or bool(e.get("video"))


# QUANTO A FAIXA QUE SAI CONTINUA A TOCAR POR CIMA DA QUE ENTRA. Ver som_do_ficheiro(),
# que e quem o aplica.
#
# ESTA AQUI, A NIVEL DO MODULO, PARA O montar_da_mesa.py O PODER LER. Ele escreve as
# janelas em que o leito baixa por baixo das vozes e do som dos videos, e escrevia-as
# sobre a duracao que poe no CSV; mas quem toca e este cruzamento, que a estica ate 2,2 s
# para a frente. Um leito que acabasse pouco antes de uma voz ficava sem janela nenhuma e
# depois era esticado para dentro dela: tocava por cima, sem baixar os 12 dB, e com
# «parada» tocava onde tinha de haver silencio. Medido a 18 de setembro, +8,8 dB no pior
# instante. As duas contas passam a olhar para este numero, e nao para duas copias dele,
# pela mesma razao que ja levou o ler_abafar a ficar num sitio so.
CRUZAMENTO = 2.2


def som_do_ficheiro(nome, fim_corpo):
    """Le data/montagens/<nome>.som.csv, se existir. Senao devolve None.

    Existe porque as demos sairam mudas. A musica da v1a e ancorada as fotos
    DELA, o que so funciona numa montagem que mantenha a ordem dela. Numa demo
    de trinta segundos nao ha ancora nenhuma, e o resultado era silencio sem um
    unico aviso. Agora cada montagem pode trazer o seu som escrito a mao, e a
    ancoragem a timeline dela fica para quem a mantem, que e a v1a.
    """
    caminho = os.path.join(MONTAGENS, nome + ".som.csv")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    entradas = []
    for r in linhas:
        quando = float(r["quando_s"])
        dura = min(float(r["dura_s"]), max(0.0, fim_corpo - quando))
        if dura <= 0.4:
            continue
        entradas.append({"ficheiro": r["ficheiro"], "caminho": r["caminho"],
                         "quando": quando, "in_s": float(r["in_s"] or 0),
                         "dura": dura, "ganho": float(r.get("ganho") or 1.0),
                         "encontrado": "Sim", "cruza": 0.0,
                         "voz": bool((r.get("voz") or "").strip()),
                         "video": bool((r.get("video") or "").strip()),
                         "abafar": ler_abafar(r.get("abafar"))})

    # CRUZAR EM VEZ DE ENCOSTAR.
    #
    # O Tiago ouviu: "atencao as transicoes de musicas, pois esta a saltar
    # estranho em alguns". A causa era simples e nao dava aviso nenhum: uma
    # faixa acabava exatamente no instante em que a seguinte comecava. Com a
    # que sai a desvanecer e a que entra a subir ao mesmo tempo, no mesmo
    # ponto, ha um vale de volume no meio e ouve-se como um solavanco.
    #
    # Agora a que sai continua a tocar por cima da que entra durante CRUZAMENTO
    # segundos. As duas somam-se nesse troco, que e o que faz uma passagem
    # soar continua.
    #
    # UMA VOZ NUNCA CRUZA. O cruzamento estica a faixa que sai por cima da que entra,
    # e entre duas frases do pedido isso seria as duas a falarem ao mesmo tempo; esticar
    # uma voz por cima da musica que comeca a seguir seria o mesmo. As vozes ficam de
    # fora dos dois lados da conta.
    pela_hora = sorted(entradas, key=lambda e: e["quando"])
    for i, e in enumerate(pela_hora):
        if entra_depressa(e):
            continue
        seguintes = [x for x in pela_hora[i + 1:]
                     if not entra_depressa(x)
                     and abs(x["quando"] - (e["quando"] + e["dura"])) < 0.35]
        if seguintes:
            extra = min(CRUZAMENTO, max(0.0, fim_corpo - (e["quando"] + e["dura"])))
            e["dura"] += extra
            e["cruza"] = extra
    return entradas


def musica_reancorada(clips, desvio, fim_corpo):
    """Coloca cada entrada musical dela sobre a MESMA foto, no tempo novo.

    TRES ERROS QUE ESTA VERSAO CORRIGE, e que juntos tornaram o primeiro teste
    inaudivel. Ficam escritos porque nenhum deles dava erro nem aviso:

    1. Faixas cuja foto de ancoragem cai fora do troco renderizado apanhavam o
       valor por omissao 0.0 e iam todas para o segundo zero. Num teste de 98
       segundos, treze musicas comecavam ao mesmo tempo. Agora sao DESCARTADAS.
    2. O tempo era absoluto, mas o corpo do video comeca depois da fanfarra.
       Toda a musica ficava adiantada 20,4 segundos. Agora desconta-se o desvio.
    3. A ultima faixa tinha 60 segundos por omissao, entrando pelo fim fora.
       Agora vai ate ao fim do corpo e nem um segundo alem.

    No fim ha uma verificacao explicita de sobreposicoes. Se duas faixas se
    pisarem, o script diz. Silencio nao e prova de que esta certo.
    """
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    musica = sorted([r for r in linhas if r["faixa"] == "musica"],
                    key=lambda r: float(r["inicio_s"]))
    video = sorted([r for r in linhas if r["faixa"] == "video"],
                   key=lambda r: float(r["inicio_s"]))

    novo_inicio = {int(c["ordem"]): float(c["inicio_s"]) - desvio for c in clips}

    entradas = []
    for m in musica:
        t = float(m["inicio_s"])
        indice = None
        for i, v in enumerate(video):
            if float(v["inicio_s"]) <= t + 0.001:
                indice = i
            else:
                break
        if indice is None:
            continue
        ordem = indice + 1
        if ordem not in novo_inicio:
            continue                      # a foto dela nao esta neste troco
        entradas.append({
            "ficheiro": m["ficheiro"],
            "caminho": m["caminho_disco"],
            "quando": max(0.0, novo_inicio[ordem]),
            "in_s": float(m["in_s"] or 0),
            "encontrado": m["encontrado"],
        })

    entradas.sort(key=lambda e: e["quando"])
    for i, e in enumerate(entradas):
        fim = entradas[i + 1]["quando"] if i + 1 < len(entradas) else fim_corpo
        e["dura"] = max(0.0, min(fim, fim_corpo) - e["quando"])

    sobrepostas = [(entradas[i], entradas[i + 1]) for i in range(len(entradas) - 1)
                   if entradas[i]["quando"] + entradas[i]["dura"]
                   > entradas[i + 1]["quando"] + 0.05 + entradas[i].get("cruza", 0.0)]
    if sobrepostas:
        print("  AVISO: %d sobreposicoes de musica" % len(sobrepostas))
        for a, b in sobrepostas[:5]:
            print("     %s pisa %s" % (a["ficheiro"][:34], b["ficheiro"][:34]))
    return entradas


# O FIM TEM DE SER INEQUIVOCO, regra do CLAUDE.md: fade a preto, para a sala saber
# que pode aplaudir. Ate 14 de setembro o ultimo fotograma era a ultima foto em
# cheio e a musica cortava a meio de um refrao com um desvanecimento de um segundo.
# A imagem escurece nos ultimos segundos e o som desce mais cedo e mais devagar,
# para acabarem os dois juntos.
FADE_FIM_IMAGEM = 2.5
FADE_FIM_SOM = 4.0


def escuro_no_fim(t, fim, dura=FADE_FIM_IMAGEM):
    """Quanto da imagem fica, de 1 a 0, no instante t de um corpo que acaba em fim."""
    if dura <= 0:
        return 1.0
    return max(0.0, min(1.0, (fim - t) / dura))


def aplicar_fim(quadro, q, fim, ate):
    """O fotograma q do corpo, escurecido se estiver nos ultimos segundos do filme.

    Num render parcial (--ate) nao: esse acaba onde calhou, e um escurecer ali
    fingia um fim que nao existe.
    """
    if ate:
        return quadro
    fica = escuro_no_fim(q / float(FPS), fim)
    if fica >= 1.0:
        return quadro
    return Image.blend(Image.new("RGB", quadro.size, (0, 0, 0)), quadro, fica)


# Entrada e saida de uma voz do pedido, em segundos. Ver construir_som().
VOZ_FADE = 0.03

# O tempo que o leito demora a baixar e a voltar a subir por baixo das vozes, e a folga
# que ha antes da primeira e depois da ultima. E o VOZ_RAMPA do montar_da_mesa.py.
VOZ_FADE_LEITO = 0.3


def volume_da_faixa(e):
    """O filtro `volume` de uma faixa: o ganho dela, e as janelas em que baixa.

    SEM JANELAS SAI EXATAMENTE O QUE SAIA ANTES DAS VOZES, "volume=1.000". Uma montagem
    sem vozes tem de dar o mesmo comando de ffmpeg, e com ele o mesmo ficheiro de som.

    COM JANELAS, o leito continua a correr e o que muda e so o volume. Escrever isto com
    dois cortes e um pedaco novo no meio parecia mais simples, mas perdia o sitio dentro
    da musica, que e a coisa que nao pode acontecer: a retoma antes da Clara conta com
    ele. Aqui a musica nunca e interrompida, so abaixada.

    A forma de cada janela e um trapezio: desce durante VOZ_FADE_LEITO antes de comecar,
    fica em baixo enquanto as vozes tocam, e sobe no mesmo tempo depois. O `t` do filtro
    conta do inicio do troco desta faixa, que e antes do adelay, por isso as janelas, que
    vem no relogio do corpo, sao trazidas para ca.
    """
    ganho = e.get("ganho", 1.0)
    janelas = e.get("abafar") or []
    if not janelas:
        return "volume=%.3f" % ganho
    termos = []
    for a, b, fator in janelas:
        ra, rb = a - e["quando"], b - e["quando"]
        termos.append("(1-%.4f*min(clip((t-%.3f)/%.2f\\,0\\,1)\\,clip((%.3f-t)/%.2f\\,0\\,1)))"
                      % (1.0 - fator, ra - VOZ_FADE_LEITO, VOZ_FADE_LEITO,
                         rb + VOZ_FADE_LEITO, VOZ_FADE_LEITO))
    # DUAS JANELAS SOBREPOSTAS NAO BAIXAM O DOBRO. Os termos eram multiplicados, e onde uma
    # voz do pedido e o som de um video se cruzavam o leito ia a 0,251 x 0,251, ou seja 24
    # dB abaixo em vez dos 12 que o contrato pede (com tres coisas por cima, 36). O que
    # manda e a coisa que pede mais silencio, por isso a conta e o MINIMO dos fatores: com
    # uma janela so da o mesmo de sempre, e uma janela que pede a musica parada continua a
    # levar tudo a zero.
    return "volume=eval=frame:volume='%.3f*%s'" % (ganho, minimo_de(termos))


def minimo_de(termos):
    """O menor de varios termos, em expressao de ffmpeg. Com um so, o proprio termo.

    Com UM termo tem de sair exatamente o que saia antes: uma montagem com uma unica
    janela da o mesmo comando de ffmpeg e com ele o mesmo ficheiro de som ao byte.
    """
    expr = termos[0]
    for t in termos[1:]:
        expr = "min(%s\\,%s)" % (expr, t)
    return expr


_TEM_SOM = {}


def tem_stream_de_som(caminho):
    """Este ficheiro tem mesmo audio la dentro? Sem conseguir perguntar, diz que sim.

    PORQUE EXISTE: um MP4 pode nao ter stream de audio nenhum, e a pasta dos videos ja tem
    um assim. Pedir [i:a] a esse ficheiro faz o ffmpeg recusar o FILTERGRAPH INTEIRO, e com
    ele todas as outras faixas: o filme saia sem banda sonora nenhuma, com o convidado a
    ouvir a fanfarra e depois quinze minutos de silencio, e a unica pista era uma linha
    «ERRO no som» no meio do registo. Vale aqui a regra do imagem_da_marca(): um ficheiro
    estranho nao pode calar quinze minutos de filme.
    """
    if caminho in _TEM_SOM:
        return _TEM_SOM[caminho]
    tem = True
    try:
        pr = os.path.join(os.path.dirname(ffmpeg()), "ffprobe.exe")
        r = subprocess.run([pr, "-v", "error", "-select_streams", "a",
                            "-show_entries", "stream=codec_type", "-of", "csv=p=0", caminho],
                           capture_output=True, text=True)
        if r.returncode == 0:
            tem = "audio" in (r.stdout or "")
    except Exception:
        tem = True
    _TEM_SOM[caminho] = tem
    return tem


def construir_som(ff, entradas, duracao_total, saida, fade_fim=0.0):
    usaveis = [e for e in entradas if e["encontrado"] != "Nao"
               and e["caminho"] and os.path.exists(e["caminho"]) and e["dura"] > 0.4]
    faltam = [e for e in entradas if e not in usaveis]
    if faltam:
        print("  sem ficheiro, ficam em silencio: %s"
              % ", ".join(sorted({e["ficheiro"] for e in faltam})))
    # Uma entrada sem stream de audio deitava abaixo o som TODO. Sai ela, ficam as outras.
    mudas = [e for e in usaveis if not tem_stream_de_som(e["caminho"])]
    if mudas:
        print("  sem stream de audio, fica de fora (as outras faixas tocam na mesma): %s"
              % ", ".join(sorted({e["ficheiro"] for e in mudas})))
        usaveis = [e for e in usaveis if e not in mudas]
    if not usaveis:
        return False

    entradas_cmd, filtros, etiquetas = [], [], []
    for i, e in enumerate(usaveis):
        entradas_cmd += ["-ss", "%.3f" % e["in_s"], "-t", "%.3f" % e["dura"],
                         "-i", e["caminho"]]
        # A subida e a descida sao do tamanho do cruzamento, quando ele existe.
        # Uma faixa que acaba sozinha desvanece com calma; uma que passa o
        # testemunho desvanece ao mesmo ritmo a que a outra sobe.
        # NAO chamar "saida" a isto: e o nome do parametro com o caminho do
        # ficheiro de som, e dar-lhe outro valor fazia o ffmpeg receber um
        # numero onde esperava um nome.
        # AS VOZES ENTRAM E SAEM DEPRESSA. Um segundo de subida e um de descida numa
        # peca de 1,2 s do pedido apagava-a quase toda: a palavra so chegava ao volume
        # cheio quando ja estava a acabar. Trinta milissegundos chegam para nao dar
        # estalo no corte e nao comem nada da frase.
        voz = entra_depressa(e)
        descida = VOZ_FADE if voz else max(1.0, e.get("cruza", 0.0))
        subida = VOZ_FADE if voz else (1.0 if e["quando"] > 0.05 else 0.4)
        # IGUALAR O VOLUME PERCEBIDO, e nao o volume do ficheiro.
        #
        # Medido no primeiro render da v3: o Lang Lang ficava a -35 dB e os
        # foguetes a -16 dB. Dezanove decibeis de diferenca, num jantar, nao e
        # contraste, e um susto. A causa nao e o codigo, sao os ficheiros: uma
        # gravacao de piano ao vivo e um excerto de uma cancao dos anos 80 nao
        # tem nada a ver um com o outro em nivel de masterizacao.
        #
        # O loudnorm poe todas a mesma sonoridade percebida, e so DEPOIS e que o
        # ganho da montagem decide quem manda. Assim o ganho passa a significar
        # o que parece significar: 1,0 e o leito, 2,0 sao os foguetes a
        # sobressair sete decibeis, e nao "o que der".
        # O LOUDNORM E POR FAIXA, E AS VOZES NAO O LEVAM. Igualar cada peca do pedido
        # sozinha punha uma frase sussurrada ao mesmo nivel de uma dita em voz alta, e o
        # que se perdia era a gravacao. O ganho delas ja vem medido sobre as pecas
        # JUNTAS, do montar_da_mesa.py, e e o mesmo em todas as vozes do mesmo clip.
        norma = "" if voz else "loudnorm=I=-23:TP=-2:LRA=11,"
        # O LOUDNORM CEGA O RELOGIO DO `volume` NOS ULTIMOS TRES SEGUNDOS DA FAIXA.
        #
        # Ele guarda tres segundos de antecipacao e no fim despeja-os de uma vez, num so
        # fotograma de audio. O `volume=eval=frame` avalia a expressao UMA vez por
        # fotograma, e por isso essa cauda inteira fica com o ganho do instante em que o
        # fotograma comeca: o relogio para 2,9 s antes do fim. Uma janela cujo levantamento
        # caia ali nunca se levanta, e a musica fica em baixo (ou calada, com «parada») ate
        # ao fim da faixa, sem aviso nenhum. Medido: faixa de 18,17 s com a janela a acabar
        # aos 16,67 s ficava a -12,0 dB ate aos 18,05 s em vez de voltar aos 16,97 s.
        #
        # O asetnsamples volta a cortar essa cauda em fotogramas pequenos e o relogio segue
        # ate ao fim. So se poe nas faixas QUE TEM JANELAS: uma faixa sem janelas tem de dar
        # o mesmo comando de ffmpeg de sempre, para o som de hoje sair igual ao byte.
        if norma and (e.get("abafar") or []):
            norma += "asetnsamples=n=1024:p=0,"
        filtros.append(
            "[%d:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            "%s"
            "afade=t=in:st=0:d=%.2f,afade=t=out:st=%.3f:d=%.2f,"
            "%s,adelay=%d|%d[a%d]"
            % (i, norma, subida, max(0.0, e["dura"] - descida), descida,
               volume_da_faixa(e),
               int(e["quando"] * 1000), int(e["quando"] * 1000), i))
        etiquetas.append("[a%d]" % i)
    # O limitador no fim existe porque o ganho dos foguetes passa dos 0 dB: sem
    # ele, somar duas faixas com um pico a +6 dB corta a onda e ouve-se a
    # distorcer exatamente no momento que devia ser o mais bonito.
    #
    # E SOBE A MISTURA INTEIRA 0,54 dB, de propósito do ffmpeg e não nosso: a opção `level`
    # do alimiter fica ligada na omissão e multiplica a saída por 1/limit, aqui 1/0,94. Medido
    # a 18 de setembro degrau a degrau: as vozes do pedido, escritas para -20,0 LUFS, saem do
    # ficheiro a -19,50, e o pico vai a 0,00 dBFS em vez dos -0,16 com que entram. Todas as
    # faixas levam o mesmo desvio, por isso o equilibrio entre elas nao se perde e ninguem
    # ouve a diferenca; o que nao e verdade e o "o que se mede e o que se ouve" do
    # sonoridade_de(), que fica meio decibel ao lado. Corrigir (level=disabled, ou descontar
    # os 0,54 dB no VOZ_ALVO_LUFS) muda o ficheiro de som da v3 ao byte, e por isso e decisao
    # dele: fica aqui escrito para a proxima pessoa nao perder a tarde a procurar meio dB.
    descida_final = ""
    if fade_fim > 0 and duracao_total > fade_fim:
        descida_final = "afade=t=out:st=%.3f:d=%.2f," % (duracao_total - fade_fim, fade_fim)
    filtros.append("%samix=inputs=%d:normalize=0:dropout_transition=0,"
                   "alimiter=level_in=1:level_out=1:limit=0.94:attack=5:release=90,"
                   "%satrim=0:%.3f,asetpts=N/SR/TB[out]"
                   % ("".join(etiquetas), len(usaveis), descida_final, duracao_total))

    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y"] + entradas_cmd + [
        "-filter_complex", ";".join(filtros), "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k", saida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  ERRO no som: %s" % (r.stderr or "")[-400:])
        return False
    return True


RENDERS = os.path.join(REPO, "data", "renders.csv")
COLUNAS_RENDER = ["quando", "montagem", "ficheiro", "leve", "duracao_s", "mb",
                  "clips", "parcial", "musicas"]


def registar_render(nome, final, leve, parcial, clips):
    """Uma linha por render em data/renders.csv, para as versoes se distinguirem.

    O nome do ficheiro diz quando. Esta linha diz o que la esta: quanto dura,
    quantos clips, e que musicas tocam, que e o que muda de versao para versao.
    """
    ff = ffmpeg()
    pr = os.path.join(os.path.dirname(ff), "ffprobe.exe")
    try:
        dur = float(subprocess.run(
            [pr, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", final],
            capture_output=True, text=True).stdout.strip())
    except Exception:
        dur = 0.0
    musicas = []
    som = os.path.join(MONTAGENS, nome + ".som.csv")
    if os.path.exists(som):
        with open(som, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                f = os.path.splitext(r["ficheiro"])[0]
                if f not in musicas and r["ficheiro"] not in ("rebobinar.wav",):
                    musicas.append(f[:40])
    novo = not os.path.exists(RENDERS)
    with open(RENDERS, "a", encoding="utf-8-sig" if novo else "utf-8",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_RENDER)
        if novo:
            w.writeheader()
        w.writerow({
            "quando": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "montagem": nome, "ficheiro": os.path.basename(final),
            "leve": os.path.basename(leve) if leve else "",
            "duracao_s": "%.1f" % dur,
            "mb": "%.1f" % (os.path.getsize(final) / 1048576.0),
            "clips": clips, "parcial": "Sim" if parcial else "Nao",
            "musicas": " | ".join(musicas),
        })


def caminhos_pelo_indice(clips, indice, inv_por_id, inv_por_nome):
    """Poe em cada clip o ficheiro que o indice manda abrir. Devolve as fotos sem indice.

    Uma foto solta vai para `_caminho`; as de um lado a lado, colagem ou pilha, pela
    ordem do id partido por "|", para `_caminhos`. Sem indice nao se adivinha entre
    versoes: fica o original, que e a unica escolha que nunca inventa nada, e a foto
    entra na lista do aviso. As fotos dos grupos caiam no original sem aviso nenhum.
    Saiu do main para ter teste: o main deixar de preencher os `_caminhos` da colagem
    e da pilha dava um cartao preto no lugar delas, e nenhum teste o via.
    """
    sem_indice = []
    for c in clips:
        r = inv_por_id.get(c["id"]) or inv_por_nome.get((c["ficheiro"] or "").lower())
        c["_caminho"] = None
        if r:
            c["_caminho"] = indice.get(r["id"])
            if not c["_caminho"]:
                sem_indice.append(r["ficheiro"])
                c["_caminho"] = r["caminho"]
        if c["tipo"] == "lado" or c["tipo"] in LIMITES_MONTE:
            c["_caminhos"] = []
            for i in (c["id"] or "").split("|"):
                r = inv_por_id.get(i)
                p = indice.get(i)
                if not p and r:
                    sem_indice.append(r["ficheiro"])
                    p = r["caminho"]
                c["_caminhos"].append(p)
    return sem_indice


def encadeados_do_corpo(corpo, fim_do_filme=True):
    """(entra, sai) de cada clip do corpo, pela ordem: o que a agenda da colagem e da pilha conta.

    `corpo` e o que partir_em_fanfarra_e_corpo() deixa de fora do bloco inicial, pela
    ordem do filme; um video do meio da montagem esta la dentro. A conta e uma so,
    para o render e para o aviso do montar_da_mesa.py:
      entra  o encadeado do proprio clip, mas ZERO no primeiro do corpo. Os videos
             sao colados antes com corte seco, e no render so ha encadeado quando ha
             dois clips de fotos ativos: a primeira foto esperava um encadeado que
             nao existe;
      sai    o encadeado do clip seguinte; no ultimo clip do filme, FADE_FIM_IMAGEM,
             porque o fade a preto escurece as fotos como um encadeado. Num render
             parcial (fim_do_filme=False) nao ha fade, e fica zero.
    """
    pares = []
    for k, c in enumerate(corpo):
        entra = 0.0 if k == 0 else float(c["transicao_s"] or 0.0)
        if k + 1 < len(corpo):
            sai = float(corpo[k + 1]["transicao_s"] or 0.0)
        else:
            sai = FADE_FIM_IMAGEM if fim_do_filme else 0.0
        pares.append((entra, sai))
    return pares


def ligar_transicoes(clips, fim_do_filme=True):
    """Poe em cada clip de fotos os encadeados de encadeados_do_corpo().

    Vao em `_transicao_entrada` e `_transicao_seguinte`. A colagem e a pilha precisam
    deles para a primeira foto esperar o encadeado de entrada e as fotos estarem todas
    paradas antes de o clip seguinte, ou o fade do fim, comecar. Os videos do bloco
    inicial nao contam: saem antes do corpo, com corte seco. Um video do corpo conta como
    qualquer outro clip. `fim_do_filme` e falso num render parcial.
    """
    _fanfarra, corpo = partir_em_fanfarra_e_corpo(clips)
    for c, (entra, sai) in zip(corpo, encadeados_do_corpo(corpo, fim_do_filme)):
        c["_transicao_entrada"] = entra
        c["_transicao_seguinte"] = sai


# ------------------------------------------------------------------ o corpo, fotograma a fotograma
LIMPEZA_A_CADA = 200      # fotogramas do corpo entre limpezas dos prontos, e entre linhas de progresso
PROGRESSO_A_CADA_S = 30   # em fatias o pai diz por onde vai pelo menos de 30 em 30 segundos
SCRIPT = os.path.abspath(__file__)


def fatias_pedidas(argv):
    """Quantos processos desenham o corpo: o --fatias da linha de comando, ou FATIAS_OMISSAO.

    "0" e "auto" deixam um nucleo para o encoder e para o resto da maquina, ate FATIAS_MAXIMO.
    """
    if "--fatias" not in argv:
        return FATIAS_OMISSAO
    if argv.index("--fatias") + 1 >= len(argv):
        sys.exit("--fatias pede um numero de 1 para cima, ou auto, e nao veio nada a seguir")
    valor = argv[argv.index("--fatias") + 1].strip().lower()
    if valor in ("0", "auto"):
        return max(1, min(FATIAS_MAXIMO, (os.cpu_count() or 2) - 1))
    try:
        n = int(valor)
    except ValueError:
        n = 0
    if n < 1:
        sys.exit("--fatias pede um numero de 1 para cima, ou auto, e nao %r" % valor)
    # Um erro de dedo (--fatias 70) lancava dezenas de processos, cada um com a Pillow e
    # os prontos de um bloco inteiro; acima de 2 x FATIAS_MAXIMO nao ha maquina que ganhe.
    if n > 2 * FATIAS_MAXIMO:
        sys.exit("--fatias %d e de mais: o maximo e %d" % (n, 2 * FATIAS_MAXIMO))
    return n


def quadros_da_fatia(k, n, total):
    """Os fotogramas que a fatia k de n desenha: alternados, os q com q % n == k.

    Alternados, e nao um troco seguido para cada fatia, por duas razoes. O pai le o
    fotograma q da fatia q % n, entrega-o ao encoder e passa ao seguinte: cada fatia
    so avanca quando o pai le, porque o pipe a bloqueia, e nenhuma acumula fotogramas
    em memoria a espera da sua vez. E o trabalho reparte-se por igual: uma pilha de
    8, cara de desenhar, cai em todas as fatias e nao so numa.
    """
    return range(k, total, n)


def carregar_montagem(nome, ate):
    """Tudo o que o render conta antes de desenhar, numa funcao so, para o pai e para as fatias.

    Le a montagem e o inventario, poe em cada clip o ficheiro que o data/finais.csv manda
    abrir, liga os encadeados e corta no --ate. Devolve o estado de que fotograma() precisa.
    O pai e cada fatia partem daqui, e por isso contam o mesmo desvio, o mesmo fim e o
    mesmo numero de fotogramas: um que contasse de outra maneira desenhava outro filme.
    """
    caminho_csv = os.path.join(MONTAGENS, nome + ".csv")
    with open(caminho_csv, encoding="utf-8-sig", newline="") as fh:
        clips = list(csv.DictReader(fh))
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    inv_por_nome = {r["ficheiro"].lower(): r for r in inv}
    inv_por_id = {r["id"]: r for r in inv}

    # A MELHOR VERSAO DE CADA IMAGEM VEM DO INDICE, NAO DE UM PALPITE.
    #
    # Isto esteve errado desde sempre e so se viu hoje. O render repetia aqui a
    # ordem de preferencia antiga, "restaurada, IA, lanczos, original", e nunca
    # soube da regra que o consolidar.py ganhou: uma foto que ja tem pixeis que
    # chegam fica com o ORIGINAL. Resultado: o video era feito com a versao da
    # rede neuronal tambem em fotografias que nao precisavam dela, e numa delas
    # a rede alisa a pele e redesenha as rugas a volta do olho. O Tiago tinha
    # sido explicito: melhorar a qualidade mantendo as pessoas reais.
    #
    # Tres copias da mesma regra, em tres ficheiros, e a que fazia o video era a
    # que estava por corrigir. Agora ha uma resposta so, o data/finais.csv, que
    # o consolidar.py escreve, e quem precisa le-a.
    indice = {}
    caminho_indice = os.path.join(REPO, "data", "finais.csv")
    if os.path.exists(caminho_indice):
        with open(caminho_indice, encoding="utf-8-sig", newline="") as fh:
            for linha in csv.DictReader(fh):
                p = os.path.join(FINAIS, linha["final"])
                if os.path.exists(p):
                    indice[linha["id"]] = p

    sem_indice = caminhos_pelo_indice(clips, indice, inv_por_id, inv_por_nome)
    # Antes de cortar no --ate: o ultimo clip de um render parcial que nao chega ao fim
    # do filme continua a contar com o encadeado do clip que o segue no filme.
    ligar_transicoes(clips, fim_do_filme=not ate)

    # A FANFARRA E O BLOCO INICIAL, e nao todos os videos que houver: ver
    # partir_em_fanfarra_e_corpo(). Um video do meio fica no `resto` e e desenhado.
    fanfarra, resto = partir_em_fanfarra_e_corpo(clips)
    if ate:
        resto = [c for c in resto if float(c["inicio_s"]) < ate]
    # ONDE CADA VIDEO DO CORPO VAI BUSCAR OS SEUS FOTOGRAMAS. Fica escrito no clip, aqui,
    # porque e aqui que se sabe o nome da montagem, e porque o pai e as fatias passam
    # todos por esta funcao: assim apontam para a mesma pasta sem ninguem a passar a mao.
    for c in resto:
        if c["tipo"] == "video":
            c["_quadros"] = pasta_dos_quadros(nome, c["ordem"])

    # OS CONTADORES LEEM-SE TODOS AGORA, E NAO AO MINUTO DOZE.
    #
    # O x de um contador e texto livre escrito na Mesa, e ha formas que a Mesa aceita sem
    # aviso nenhum e que o Python nao le (uma ponta em data e a outra em ano, ou 29/02 de um
    # ano que nao o tem). O preparar() ja nao morre com elas, mas o clip sai preto: e melhor
    # ele saber ao arrancar, enquanto ainda pode corrigir o x, do que descobrir no filme.
    maus = [c for c in resto if c["tipo"] == "contador" and not contador_legivel(c["texto_ecra"])]
    for c in maus:
        print("  CONTADOR QUE NAO CONSIGO LER, sai preto: clip %s, %r"
              % (c["ordem"], (c["texto_ecra"] or "")[:60]))

    desvio = float(resto[0]["inicio_s"]) if resto else 0.0
    fim = max(float(c["fim_s"]) for c in resto) - desvio
    return {"nome": nome, "clips": clips, "fanfarra": fanfarra, "resto": resto,
            "inv_por_nome": inv_por_nome, "sem_indice": sem_indice,
            "desvio": desvio, "fim": fim, "ate": ate,
            "total_quadros": int(round(fim * FPS)),
            "prontos": {}, "faltaram": []}


def fotograma(q, estado):
    """O fotograma q do corpo, como vai para o encoder, e os clips ativos nele.

    E o corpo do ciclo de sempre, tirado para fora para o caminho sequencial e as fatias
    desenharem pelo mesmo codigo, e a igualdade ficar garantida por construcao e nao so
    pelo teste. O q e o numero GLOBAL do fotograma, contado do principio do corpo: e com
    ele que o fade do fim sabe onde esta, numa fatia que so desenha um em cada n. Os
    prontos e os faltaram vivem no estado, e cada processo tem o seu.
    """
    resto, prontos = estado["resto"], estado["prontos"]
    t = estado["desvio"] + q / FPS
    ativos = [c for c in resto
              if float(c["inicio_s"]) - 0.001 <= t < float(c["fim_s"])]
    if not ativos:
        ativos = [resto[-1]]
    ativos = ativos[-2:]

    camadas = []
    for c in ativos:
        k = c["ordem"]
        if k not in prontos:
            p = preparar(c, estado["inv_por_nome"])
            if p is None:
                # UM CLIP SEM FICHEIRO TAMBEM TEM DE SE DIZER PELO NOME. Um contador que
                # nao se le nao tem ficheiro nenhum, e a lista do fim ficava com uma linha
                # em branco a dizer que faltou "": quem a lesse nao sabia o que procurar.
                estado["faltaram"].append(
                    c["ficheiro"] or ("%s %s" % (c["tipo"], (c["texto_ecra"] or "")[:40])).strip())
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

    # Fade a preto no fim do filme, so em render completo.
    return aplicar_fim(quadro, q, estado["fim"], estado["ate"]), ativos


def libertar_prontos(estado, ativos):
    """Liberta a memoria dos clips que ja passaram. O tempo so anda para a frente, nenhum volta."""
    vivos = {c["ordem"] for c in ativos}
    for k in list(estado["prontos"]):
        if k not in vivos:
            del estado["prontos"][k]


def desenhar_fatia(quadros, estado, escrever, ao_limpar=None):
    """Desenha os fotogramas `quadros`, pela ordem, e entrega os bytes de cada um a `escrever`.

    A limpeza dos prontos e por bloco de LIMPEZA_A_CADA fotogramas DO CORPO, e nao dos que
    esta fatia desenha: no caminho sequencial da o q % 200 == 0 de sempre, e numa fatia de
    sete a limpeza continua de 8 em 8 segundos de filme. Contada nos fotogramas da fatia,
    cada uma guardava 56 segundos de clips preparados, sete vezes.
    """
    bloco = -1
    for q in quadros:
        quadro, ativos = fotograma(q, estado)
        escrever(quadro.tobytes())
        if q // LIMPEZA_A_CADA != bloco:
            bloco = q // LIMPEZA_A_CADA
            libertar_prontos(estado, ativos)
            if ao_limpar is not None:
                ao_limpar(q)


def progresso(q, total):
    print("  %d/%d fotogramas (%.0f%%)" % (q, total, 100 * q / total), end="\r", flush=True)


def encoder_do_corpo(ff, corpo):
    """O UNICO ffmpeg que codifica o corpo, com os parametros de sempre. Recebe rgb24 pelo stdin.

    Com ou sem fatias e este, e recebe os mesmos bytes pela mesma ordem: o x264 e
    determinista com os mesmos parametros, e o _corpo.mp4 sai igual ao byte.
    """
    return subprocess.Popen(
        [ff, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (L, A),
         "-framerate", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", corpo], stdin=subprocess.PIPE)


# ------------------------------------------------------------------ as fatias
def ler_fatia(valor):
    """O "k/n" da linha de comando de uma fatia: (k, n), com 0 <= k < n."""
    k, _, n = valor.partition("/")
    try:
        k, n = int(k), int(n)
    except ValueError:
        sys.exit("--fatia pede k/n, e nao %r" % valor)
    if n < 1 or not 0 <= k < n:
        sys.exit("--fatia pede k/n com 0 <= k < n, e nao %r" % valor)
    return k, n


def canal_da_fatia():
    """Numa fatia o stdout e dos fotogramas: devolve o canal binario e manda os prints para o stderr.

    Um print que fosse parar ao meio dos bytes de um fotograma desalinhava tudo o que
    vinha a seguir, sem erro nenhum: o pai le tamanhos exatos, e o encoder codificava
    lixo. Por isso o desvio e feito antes de qualquer palavra.
    """
    sys.stdout.flush()
    canal = sys.stdout.buffer
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout = sys.stderr
    return canal


def correr_fatia(estado, k, n, canal):
    """Uma fatia: desenha os seus fotogramas e escreve os bytes de cada um no canal, pela ordem.

    No fim vai para o stderr uma linha "FALTARAM: [...]" com as imagens que nao abriu,
    que o pai junta as das outras fatias. Os avisos do preparar ja la vao, ver
    canal_da_fatia().
    """
    desenhar_fatia(quadros_da_fatia(k, n, estado["total_quadros"]), estado, canal.write)
    canal.flush()
    print("FALTARAM: " + json.dumps(estado["faltaram"], ensure_ascii=False),
          file=sys.stderr, flush=True)


def comando_da_fatia(nome, k, n, argv):
    """A linha de comando de uma fatia: este script, pelo mesmo Python, com o --ate e o --escala do pai.

    Vao as palavras que o pai recebeu, e nao os numeros convertidos, para a fatia ler
    exatamente o mesmo valor. A pasta das montagens vai sempre: os testes rendem uma
    montagem fora do repositorio.
    """
    cmd = [sys.executable, SCRIPT, nome, "--fatia", "%d/%d" % (k, n), "--montagens", MONTAGENS]
    for opcao in ("--ate", "--escala"):
        if opcao in argv:
            cmd += [opcao, argv[argv.index(opcao) + 1]]
    return cmd


def _ler_stderr(filho, linhas, mostrar):
    """Numa thread, para a fatia nunca encravar com o stderr cheio. A fatia 0 fala pelo pai."""
    for bruta in iter(filho.stderr.readline, b""):
        linha = bruta.decode("utf-8", "replace").rstrip("\r\n")
        linhas.append(linha)
        if mostrar and not linha.startswith("FALTARAM: "):
            print(linha, flush=True)


def render_em_fatias(ff, corpo, estado, n, argv):
    """Desenha o corpo com n fatias e UM encoder, o de sempre. Devolve os faltaram, juntos.

    O QUE MUDA E QUEM DESENHA, NAO QUEM CODIFICA. Cada fatia e este script outra vez, com
    --fatia k/n, a desenhar os fotogramas q com q % n == k e a escreve-los no seu stdout.
    O pai le o fotograma q da fatia q % n, os L*A*3 bytes exatos, escreve-o no encoder e
    passa ao seguinte. Uma fatia so avanca quando o pai lhe le o fotograma anterior, o
    pipe bloqueia-a, e por isso nenhuma tem mais do que um fotograma a espera.

    Uma fatia que morra, ou devolva menos bytes, para tudo: matam-se as outras e o
    encoder, o _corpo.mp4 a meio e apagado, e o erro diz qual foi e o que ela escreveu
    no stderr. Nunca fica um ficheiro final meio feito.
    """
    import threading
    import time
    total = estado["total_quadros"]
    filhos = [subprocess.Popen(comando_da_fatia(estado["nome"], k, n, argv),
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
              for k in range(n)]
    linhas = [[] for _ in filhos]
    leitores = [threading.Thread(target=_ler_stderr, args=(f, linhas[k], k == 0), daemon=True)
                for k, f in enumerate(filhos)]
    for th in leitores:
        th.start()
    proc = encoder_do_corpo(ff, corpo)
    tamanho = L * A * 3
    ultimo = time.time()
    try:
        for q in range(total):
            k = q % n
            dados = filhos[k].stdout.read(tamanho)
            if len(dados) != tamanho:
                raise RuntimeError("a fatia %d/%d parou no fotograma %d: devolveu %d bytes em vez de %d\n%s"
                                   % (k, n, q, len(dados), tamanho, "\n".join(linhas[k][-12:])))
            proc.stdin.write(dados)
            if q % LIMPEZA_A_CADA == 0 or time.time() - ultimo >= PROGRESSO_A_CADA_S:
                ultimo = time.time()
                progresso(q, total)
        for k, f in enumerate(filhos):
            sobra = f.stdout.read()
            if sobra:
                raise RuntimeError("a fatia %d/%d escreveu %d bytes a mais do que os seus fotogramas"
                                   % (k, n, len(sobra)))
            f.wait()
        proc.stdin.close()
        codigo = proc.wait()
        if codigo != 0:
            raise RuntimeError("o encoder acabou com o codigo %d" % codigo)
        for th in leitores:
            th.join()
        faltaram = []
        for k, f in enumerate(filhos):
            if f.returncode != 0:
                raise RuntimeError("a fatia %d/%d acabou com o codigo %d\n%s"
                                   % (k, n, f.returncode, "\n".join(linhas[k][-12:])))
            ditos = [l for l in linhas[k] if l.startswith("FALTARAM: ")]
            if not ditos:
                raise RuntimeError("a fatia %d/%d acabou sem dizer o que lhe faltou\n%s"
                                   % (k, n, "\n".join(linhas[k][-12:])))
            for ficheiro in json.loads(ditos[-1][len("FALTARAM: "):]):
                if ficheiro not in faltaram:
                    faltaram.append(ficheiro)
        return faltaram
    except BaseException as e:
        for f in filhos:
            if f.poll() is None:
                f.kill()
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        for f in filhos:
            f.wait()
        try:
            os.remove(corpo)
        except OSError:
            pass
        if not isinstance(e, Exception):
            raise
        sys.exit("\nERRO no render em fatias: %s\n  Nenhum ficheiro ficou escrito." % e)


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit("Diz qual a montagem. Ex: py -3.11 scripts/render.py v1a")
    nome = sys.argv[1]
    fatia = None
    if "--fatia" in sys.argv:
        # Isto e uma fatia de um render em fatias: o stdout passa a ser dos fotogramas
        # antes de qualquer palavra, ver canal_da_fatia().
        fatia = ler_fatia(sys.argv[sys.argv.index("--fatia") + 1])
        canal = canal_da_fatia()
    sem_som = "--sem-som" in sys.argv
    fatias = fatias_pedidas(sys.argv)
    ate = None
    if "--ate" in sys.argv:
        ate = float(sys.argv[sys.argv.index("--ate") + 1])
    if "--escala" in sys.argv:
        # 720p para testes: 2,25 vezes menos pixeis, chega para julgar ritmo.
        global L, A
        f = float(sys.argv[sys.argv.index("--escala") + 1])
        L, A = int(L * f) // 2 * 2, int(A * f) // 2 * 2
        if fatia is None:
            print("Render a %dx%d" % (L, A))
    if "--montagens" in sys.argv:
        # A pasta das montagens, que o pai passa as fatias: pode nao ser a do repositorio.
        global MONTAGENS
        MONTAGENS = sys.argv[sys.argv.index("--montagens") + 1]

    if fatia is None:
        ff = ffmpeg()
        os.makedirs(SAIDA, exist_ok=True)
    estado = carregar_montagem(nome, ate)
    if fatia is not None:
        correr_fatia(estado, fatia[0], fatia[1], canal)
        return

    if estado["sem_indice"]:
        sem_indice = estado["sem_indice"]
        print("  SEM INDICE, usei o original: %d fotos (%s%s)"
              % (len(sem_indice), ", ".join(sem_indice[:3]),
                 ", ..." if len(sem_indice) > 3 else ""))
        print("  Corre:  py -3.11 scripts/consolidar.py")
    fanfarra, resto = estado["fanfarra"], estado["resto"]
    desvio, fim, total_quadros = estado["desvio"], estado["fim"], estado["total_quadros"]

    print("Render de %s" % nome)
    print("  clips: %d fotos e cartoes + %d fanfarra" % (len(resto), len(fanfarra)))
    print("  duracao da parte de fotos: %.0f s  (%d fotogramas)" % (fim, total_quadros))
    print()

    # OS VIDEOS DO CORPO SAO EXTRAIDOS ANTES DE QUALQUER FOTOGRAMA SER DESENHADO.
    # As fatias leem esta cache e nenhuma a cria, ver preparar().
    quadros_criados = preparar_quadros_dos_videos(ff, estado)

    corpo = os.path.join(SAIDA, "_%s_corpo.mp4" % nome)
    # Com menos fotogramas do que fatias, so ha fatias que tenham fotogramas; com uma
    # so, e o caminho de sempre, sem processos filhos.
    fatias = max(1, min(fatias, total_quadros))
    if fatias > 1:
        print("  em %d fatias" % fatias)
        faltaram = render_em_fatias(ff, corpo, estado, fatias, sys.argv)
    else:
        proc = encoder_do_corpo(ff, corpo)
        desenhar_fatia(range(total_quadros), estado, proc.stdin.write,
                       lambda q: progresso(q, total_quadros))
        proc.stdin.close()
        proc.wait()
        faltaram = estado["faltaram"]
    print("\n  corpo escrito")

    partes = []
    if fanfarra and not ate:
        for n_v, c in enumerate(fanfarra):
            origem, arranque = caminho_de_video(c.get("ficheiro") or "")
            # O in_s da linha manda sobre o arranque da tabela VIDEOS, quando vem escrito.
            # Sem ele (a v3 de hoje) fica o de sempre, e a fanfarra sai igual ao byte.
            if str(c.get("in_s") or "").strip():
                arranque = float(c["in_s"])
            if not origem:
                print("  VIDEO EM FALTA, saltado: %s" % (c.get("ficheiro") or "(sem nome)"))
                continue
            fan = os.path.join(SAIDA, "_%s_video%d.mp4" % (nome, n_v))
            r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                                "-ss", "%.3f" % arranque,
                                "-t", "%.3f" % float(c["duracao_s"]),
                                "-i", origem,
                                "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,"
                                       "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1"
                                       % (L, A, L, A),
                                "-r", str(FPS), "-c:v", "libx264", "-crf", "20",
                                "-preset", "veryfast", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                                "-ar", "48000", fan], capture_output=True, text=True)
            if r.returncode != 0:
                print("  ERRO no video %s: %s"
                      % (c.get("ficheiro"), (r.stderr or "")[-200:]))
                continue
            print("  video %d: %s" % (n_v + 1, os.path.basename(origem)))
            partes.append(fan)

    som = None
    if not sem_som:
        print("  a construir o som")
        som = os.path.join(SAIDA, "_%s_som.m4a" % nome)
        entradas = som_do_ficheiro(nome, fim)
        if entradas is None:
            entradas = musica_reancorada(resto, desvio, fim)
        for e in entradas:
            print("     %5.1f s  dura %5.1f s  %s"
                  % (e["quando"], e["dura"], e["ficheiro"][:46]))
        if not construir_som(ff, entradas, fim, som, 0.0 if ate else FADE_FIM_SOM):
            som = None

    corpo_final = corpo
    if som:
        corpo_final = os.path.join(SAIDA, "_%s_corpo_som.mp4" % nome)
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", corpo, "-i", som, "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-ac", "2", "-ar", "48000",
                        "-shortest", corpo_final], capture_output=True, text=True)
    partes.append(corpo_final)

    # CADA RENDER E UMA VERSAO, E NENHUMA ESCREVE POR CIMA DE OUTRA.
    #
    # Ate 13 de setembro isto escrevia sempre "v3.mp4", e a v3 de 12 de
    # setembro desapareceu quando saiu a seguinte. O Tiago: "Quero guardar
    # versoes". O nome leva a data e a hora, e um render parcial (--ate ou
    # --escala) diz que o e, para nunca se confundir com um filme inteiro.
    carimbo = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    parcial = bool(ate) or L != 1920
    base_nome = "%s_%s%s" % (nome, carimbo, "_parcial" if parcial else "")
    final = os.path.join(SAIDA, base_nome + ".mp4")
    k = 2
    while os.path.exists(final):
        final = os.path.join(SAIDA, "%s_%d.mp4" % (base_nome, k))
        k += 1
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
    # A copia leve, a que vai para o telemovel, passa a sair sempre com o render
    # e com o mesmo nome. Antes era feita a mao, e a mao esquece-se.
    leve = ""
    if os.path.exists(final) and not parcial:
        leve = final[:-4] + "_leve.mp4"
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-i", final, "-vf", "scale=1280:720:flags=lanczos",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "26",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                            leve], capture_output=True, text=True)
        if r.returncode != 0:
            print("  ERRO na copia leve: %s" % (r.stderr or "")[-300:])
            leve = ""

    # A COPIA PARA O TELEMOVEL. O Tiago acompanha muitas vezes a partir do
    # telemovel, e o envio para la tem um limite de 30 MB. A copia leve de um filme
    # de 6:30 ja tem 41 MB e nao chegava. Quando a leve passa dos 29 MB, sai tambem
    # uma copia a 960x540, apertada ate caber.
    if leve and os.path.exists(leve) and os.path.getsize(leve) > 29 * 1048576:
        movel = final[:-4] + "_telemovel.mp4"
        for crf in (28, 31, 34):
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-i", final, "-vf", "scale=960:540:flags=lanczos",
                            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                            movel], capture_output=True, text=True)
            if os.path.exists(movel) and os.path.getsize(movel) <= 29 * 1048576:
                break
        if os.path.exists(movel):
            print("Telemovel: %s  (%.1f MB)" % (movel, os.path.getsize(movel) / 1048576.0))

    if os.path.exists(final):
        registar_render(nome, final, leve, parcial, len(resto) + len(fanfarra))

    if quadros_criados and "--guardar-quadros" not in sys.argv:
        apagar_quadros(quadros_criados)
    elif quadros_criados:
        print("Fotogramas dos videos guardados em: %s" % ", ".join(quadros_criados))

    print()
    print("Escrito: %s" % final)
    if leve:
        print("Leve:    %s" % leve)


if __name__ == "__main__":
    main()
