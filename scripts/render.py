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
    py -3.11 scripts/render.py v3 --sem-legendas      o filme sem a legenda de baixo, para o DaVinci
    py -3.11 scripts/render.py v3 --sem-copias        so o ficheiro final, sem a _leve nem a _telemovel
    py -3.11 scripts/render.py v3 --saida <pasta>     o filme e os ficheiros de trabalho noutra pasta

O pacote do DaVinci inteiro (o filme sem legendas, os creditos, o .srt e o guia) e um comando so:
    py -3.11 scripts/davinci_pacote.py v3
"""
import csv
import datetime
import itertools
import json
import math
import os
import re
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linha_tempo
# Os emojis a cores e os sinais equivalentes em todos os textos do filme (2 de outubro): a maneira unica
# de medir e de desenhar texto, a mesma no render, na fita e nos creditos. Sem emojis nem sinais
# equivalentes cada funcao dele e a chamada de sempre, ao byte.
import texto_emojis

# So se ha consola ou ficheiro (revisao de 2 de outubro): o montar_da_mesa.py importa o render dentro
# do main(), e quem monta com o stdout num StringIO (os testes calados) rebentava aqui.
if hasattr(sys.stdout, "reconfigure"):
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
    # A INTRO SEM O PRETO DO FIM, decisao 097: o _5 cortado aos 13,20 s, e a copia igualada.
    "intro_clara_tiago_5 sem preto.mp4": (
        os.path.join(r"C:\casamento-video-media\gerados\intro_marvel",
                     "intro_clara_tiago_5 sem preto.mp4"), 0.0),
    "intro_clara_tiago_5 sem preto igualado.mp4": (
        os.path.join(r"C:\casamento-video-media\gerados\som_igualado",
                     "intro_clara_tiago_5 sem preto igualado.mp4"), 0.0),
}


PASTA_INTRO_MARVEL = r"C:\casamento-video-media\gerados\intro_marvel"
PASTA_SOM_IGUALADO = r"C:\casamento-video-media\gerados\som_igualado"


def caminho_de_video(nome):
    """Encontra o ficheiro do video pelo nome, custe o que custar.

    Procura primeiro na tabela, depois em toda a pasta de media. Um video de
    abertura em falta nao pode fazer o render abortar a meio.
    """
    if nome in VIDEOS and os.path.exists(VIDEOS[nome][0]):
        return VIDEOS[nome]
    # AS INTROS DE OUTRAS CORES, desde 2 de outubro: o montar_da_mesa.py pede-as ao
    # intro_flipbook.py e ao igualar_abertura.py, com nome novo por paleta, e por isso nao
    # podem estar na tabela. Procuram-se primeiro nas duas pastas de onde saem, antes da busca
    # pela media toda, que apanhava o primeiro ficheiro com o nome em qualquer sitio.
    if (nome or "").lower().startswith("intro_clara_tiago"):
        for pasta in (PASTA_SOM_IGUALADO, PASTA_INTRO_MARVEL):
            caminho = os.path.join(pasta, nome)
            if os.path.exists(caminho):
                return caminho, 0.0
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
    """As palavras em linhas que cabem na `largura`. A medida e a do texto_emojis.caixa(): com um emoji,
    o emoji conta com a largura que tem a cores; sem nenhum, e o textbbox() de sempre."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if texto_emojis.caixa(teste, fonte, desenho=desenho)[2] <= largura:
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
    # OS EQUIVALENTES TROCAM-SE AQUI (2 de outubro): as linhas que saem sao as que se desenham, e e
    # delas que o .srt do DaVinci se escreve. Um texto sem nenhum fica o mesmo.
    linhas = []
    for paragrafo in texto_emojis.com_equivalentes(texto or "").splitlines():
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
LEGENDA_COR = (255, 255, 255)
# O FILME PARA O DAVINCI, SEM A LEGENDA DE BAIXO (2 de outubro). O Tiago: "se comecar a apertar,
# mudo para o davinci de forma mais facil". O teste do projetor e no proprio dia do casamento, e
# mudar o tamanho da legenda pela Mesa e um render novo de quase uma hora. Com --sem-legendas o
# render desenha tudo como sempre (as fotos pousam no mesmo sitio, acima de onde a faixa ia, e os
# cartoes, o nome do bebe, o texto dentro das fotos, a fita e o destaque ficam na imagem) e so nao
# cola a faixa de baixo: a dos clips de foto e de video, a legenda de cada grupo e a que muda com
# cada foto na opcao "na legenda de baixo". Essas vao para um .srt (scripts/legendas_srt.py), que
# o DaVinci le e deixa mudar de tamanho de uma vez. Falso, que e a omissao, nenhum pixel muda.
SEM_LEGENDAS = False

# ------------------------------------------- a posicao das legendas e a legenda numa so linha
# O Tiago, a 3 de outubro (contrato_1003, pontos 2 e 3): "Na foto na posicao 10, meter a legenda
# numa so linha, sem alterar o tamanho da letra" e "permite-me ajustar o posicionamento das
# legendas, cima, baixo, direita, esquerda".
#   est.estilo.legenda.posicao = {dx, dy, alinhamento}   para todas as legendas de baixo
#   clip.lp = {dx, dy}                                     soma-se a de todas, so neste clip
#   clip.x1 = true                                         este clip nao parte a legenda em linhas
# O clip leva as suas na coluna opcoes_clip do CSV (JSON so com o que difere, e a coluna so entra
# quando algum clip a tem, como a do destaque). SEM NADA DISTO, NENHUM PIXEL MUDA: a faixa e o texto
# desenham-se pelas contas de sempre.
#
# A FAIXA ESCURA ACOMPANHA O TEXTO NA ALTURA e continua de borda a borda. O dy so sobe: a legenda
# nunca desce abaixo de onde esta hoje, por causa do overscan do projetor (LEGENDA_FUNDO). O dx anda
# com o texto, mas o bloco das linhas nunca sai da largura util de hoje, L - 260: encosta a margem
# em vez de sair do ecra, que com o dx de todas as legendas e uma frase comprida acontecia. O
# alinhamento poe as linhas ao centro (como hoje), encostadas a margem da esquerda ou a da direita.
LEGENDA_MARGEM_LADO = 130            # a margem de cada lado, a da largura util de hoje (L - 260)
# A largura em que a legenda de um clip com x1 tem de caber para ficar numa linha: a largura util de
# hoje, 1660 px a 1080 (o contrato: "a mesma margem lateral das legendas de hoje"). E um numero so, usado
# pelo linhas_legenda() e pelo legenda_numa_linha(), para a regra se mudar num sitio se ele a mudar.
LEGENDA_LARGURA_NUMA_LINHA = L - 2 * LEGENDA_MARGEM_LADO
POSICAO_DX = (-600, 600)             # px a 1080, positivo para a direita
POSICAO_DY = (-500, 0)               # px a 1080, negativo para cima
POSICAO_ALINHAMENTOS = ("centro", "esquerda", "direita")
# O do clip soma-se ao de todas, e por isso pode ir ate ao dobro para desfazer o de todas; o total e
# que fica nos limites de cima.
LP_DX = (-1200, 1200)
LP_DY = (-500, 500)
COLUNA_OPCOES_CLIP = "opcoes_clip"


def _inteiro_com_sinal(v):
    """Um numero de pixeis como inteiro: -40, -40.0 e "-40" valem; o booleano e o que tem decimais nao."""
    if isinstance(v, bool):
        return None
    if isinstance(v, str):
        v = v.strip()
        return int(v) if re.fullmatch(r"[-+]?\d+", v) else None
    if isinstance(v, float):
        return int(v) if v.is_integer() else None
    return v if isinstance(v, int) else None


def ler_opcoes_clip(celula):
    """A coluna opcoes_clip -> {"x1": bool, "lp": (dx, dy), "li": bool}, ou None se nao traz nada.

    Ausente, vazia ou mal escrita valem todas o mesmo: nada, e o clip sai como sempre. Quem valida e
    avisa e o montar_da_mesa.py, que e onde ha uma lista para o Tiago ler; aqui um valor que nao
    presta (fora dos limites, que nao e numero) vale zero, como a omissao.
    """
    if isinstance(celula, dict):
        bruto = celula
    else:
        try:
            bruto = json.loads(celula) if (celula or "").strip() else {}
        except (ValueError, TypeError, AttributeError):
            return None
    if not isinstance(bruto, dict):
        return None
    lp = bruto.get("lp") if isinstance(bruto.get("lp"), dict) else {}
    dx, dy = _inteiro_com_sinal(lp.get("dx", 0)), _inteiro_com_sinal(lp.get("dy", 0))
    dx = dx if dx is not None and LP_DX[0] <= dx <= LP_DX[1] else 0
    dy = dy if dy is not None and LP_DY[0] <= dy <= LP_DY[1] else 0
    o = {"x1": bruto.get("x1") is True, "lp": (dx, dy), "li": bruto.get("li") is True}
    if not o["x1"] and not o["li"] and o["lp"] == (0, 0):
        return None
    return o


def posicao_da_legenda(clip_leg=None):
    """(dx, dy, alinhamento) da legenda de baixo: a de todas (o estilo) mais a do clip, nos limites.

    Sem posicao no estilo e sem lp no clip e (0, 0, "centro"), a legenda de sempre.
    """
    pos = _ESTILO.get("legenda", {}).get("posicao") or {}
    dx, dy = pos.get("dx", 0), pos.get("dy", 0)
    if clip_leg:
        dx, dy = dx + clip_leg["lp"][0], dy + clip_leg["lp"][1]
    dx = min(POSICAO_DX[1], max(POSICAO_DX[0], dx))
    dy = min(POSICAO_DY[1], max(POSICAO_DY[0], dy))
    return dx, dy, pos.get("alinhamento", "centro")


def x_das_linhas(larguras, dx, alinhamento):
    """O x de cada linha da legenda, com o bloco das linhas sempre dentro da largura util.

    Ao centro e sem dx e o (L - w) / 2 de sempre, ao bit. Encostada a esquerda as linhas comecam na
    margem, a direita acabam nela, e o dx anda com o bloco ate ele tocar numa das margens.
    """
    m = LEGENDA_MARGEM_LADO
    dx = dx_efetivo(larguras, dx, alinhamento)
    if alinhamento == "esquerda":
        return [m + dx for _w in larguras]
    if alinhamento == "direita":
        return [L - m - w + dx for w in larguras]
    if dx == 0:
        return [(L - w) / 2 for w in larguras]
    return [(L - w) / 2 + dx for w in larguras]


def dx_efetivo(larguras, dx, alinhamento):
    """O dx que o bloco das linhas anda de facto: o pedido, ate o bloco tocar numa margem."""
    folga = max(0, (L - 2 * LEGENDA_MARGEM_LADO) - (max(larguras) if larguras else 0))
    if alinhamento == "esquerda":
        return min(folga, max(0, dx))
    if alinhamento == "direita":
        return max(-folga, min(0, dx))
    return min(folga / 2.0, max(-folga / 2.0, dx))


def legenda_numa_linha(texto, tamanho=None):
    """(cabe, px que a linha precisa, px que ha) da legenda escrita numa so linha, no corpo de hoje.

    A largura e a de sempre, L - 260 (a margem lateral das legendas de hoje). E a conta que o clip.x1
    usa, e o aviso do montar e o do render dizem estes dois numeros.
    """
    tamanho = legenda_tamanho() if tamanho is None else tamanho
    linha = " ".join(texto_emojis.com_equivalentes(texto or "").split())
    precisa = texto_emojis.caixa(linha, letra("legenda", tamanho),
                                 desenho=ImageDraw.Draw(Image.new("L", (1, 1))))[2] if linha else 0
    return precisa <= LEGENDA_LARGURA_NUMA_LINHA, int(math.ceil(precisa)), LEGENDA_LARGURA_NUMA_LINHA


def linhas_legenda(texto, tamanho=None, desenho=None, uma_linha=False):
    """Como o texto da legenda de baixo se parte: (tamanho, linhas, fonte).

    Desce de 4 em 4 ate caber em LEGENDA_LINHAS linhas, e nunca abaixo do minimo, que e
    proporcional ao tamanho pedido: LEGENDA_MIN para LEGENDA_TAMANHO. Com 46 a sequencia e
    a de sempre, 46, 42, 38, 34, 30. O tamanho vem da Mesa na opcao "na legenda de baixo";
    a legenda do grupo fica com o de sempre. Sem tamanho e o do estilo da Mesa, e sem estilo
    o LEGENDA_TAMANHO; a letra e a da legenda do estilo, ver letra().

    `uma_linha` e o clip.x1 (3 de outubro): o texto todo numa linha, as mudancas de linha
    escritas incluidas, no mesmo corpo, se couber na largura util (legenda_numa_linha()). Se
    nao couber parte-se como sempre, e quem avisa e o carregar_montagem() e o montar.
    """
    tamanho = legenda_tamanho() if tamanho is None else tamanho
    d = desenho or ImageDraw.Draw(Image.new("L", (1, 1)))
    minimo = int(math.floor(tamanho * LEGENDA_MIN / float(LEGENDA_TAMANHO) + 0.5))
    fonte = letra("legenda", tamanho)
    if uma_linha:
        linha = " ".join(texto_emojis.com_equivalentes(texto or "").split())
        if linha and texto_emojis.caixa(linha, fonte, desenho=d)[2] <= LEGENDA_LARGURA_NUMA_LINHA:
            return tamanho, [linha], fonte
    linhas = quebrar_paragrafos(texto, fonte, L - 260, d)
    while len(linhas) > LEGENDA_LINHAS and tamanho > minimo:
        tamanho = max(minimo, tamanho - 4)
        fonte = letra("legenda", tamanho)
        linhas = quebrar_paragrafos(texto, fonte, L - 260, d)
    return tamanho, linhas, fonte


def bloco_legenda(texto, tamanho=None, uma_linha=False):
    """Altura, em pixeis, do bloco das linhas que faixa_texto() escreve para este texto."""
    tamanho, linhas, _fonte = linhas_legenda(texto, tamanho, uma_linha=uma_linha)
    return int(tamanho * 1.35) * len(linhas)


def faixa_texto(texto, tamanho=None, bloco_max=None, clip_leg=None):
    """Desenha a legenda uma vez. Devolve (cor, mascara) para colagem rapida.

    `bloco_max` e a altura do bloco das linhas do texto mais alto que o clip vai mostrar,
    na opcao "na legenda de baixo": a faixa fica com essa altura em todo o clip, para as
    fotos nao mudarem de sitio quando o texto troca, e um texto mais baixo centra-se nela.
    Sem `bloco_max`, e com o tamanho de sempre, e a legenda de sempre, pixel a pixel.
    `clip_leg` sao as opcoes do clip, de ler_opcoes_clip(): a legenda numa linha e o lp. A
    posicao de todas vem do estilo, ver posicao_da_legenda().
    """
    if not texto:
        return None
    capa = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    # LEGENDA_FUNDO e a margem que a legenda guarda por baixo dela. Num projetor ou num
    # televisor com overscan os ultimos pixeis do ecra nao aparecem, e e por isso que esta
    # faixa nunca desce ate A: quem escrever outra faixa encostada ao fundo usa a mesma
    # linha, ver lado_faixas().
    tamanho, linhas, fonte = linhas_legenda(texto, tamanho, d,
                                            uma_linha=bool(clip_leg and clip_leg["x1"]))
    altura_linha = int(tamanho * 1.35)
    bloco = altura_linha * len(linhas)
    banda = bloco if bloco_max is None else max(bloco, bloco_max)
    topo = A - LEGENDA_TEXTO - banda + (banda - bloco) // 2
    # A POSICAO (3 de outubro): a faixa e o texto sobem dy juntos, e o texto anda dx. Sem posicao
    # dy e 0 e os x sao os (L - w) / 2 de sempre.
    dx, dy, alinhamento = posicao_da_legenda(clip_leg)
    d.rectangle([0, A - LEGENDA_TEXTO - banda - LEGENDA_ALMOFADA + dy, L, A - LEGENDA_FUNDO + dy],
                fill=(0, 0, 0, fundo_da_legenda(LEGENDA_ALFA)))
    cor = legenda_cor() + (255,)
    # um emoji vai a cores, na letra de emojis, e os equivalentes trocam-se (texto_emojis); sem
    # eles e o textbbox() e o text() de sempre
    xs = x_das_linhas([texto_emojis.caixa(linha, fonte, desenho=d)[2] for linha in linhas], dx, alinhamento)
    for i, linha in enumerate(linhas):
        texto_emojis.escrever(d, (xs[i], topo + dy + i * altura_linha), linha, fonte, cor)
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


def legenda_por_foto(textos, tamanho=None, clip_leg=None):
    """As faixas da opcao "na legenda de baixo", desenhadas uma vez por clip.

    `textos` e o que a legenda mostra em cada foto, ja com o texto do grupo no lugar dos
    vazios. Devolve {"textos", "faixas": {texto: (cor, mascara)}, "topo", "fundo"}, ou None
    se nao houver texto nenhum. Todas as faixas tem a altura do bloco mais alto, para as
    fotos pousarem acima dela e nao mudarem de sitio quando o texto troca. `clip_leg` sao as
    opcoes do clip (a legenda numa linha e o lp), que valem para cada texto.
    """
    distintos = [t for t in dict.fromkeys(textos) if t]
    if not distintos:
        return None
    tamanho = legenda_tamanho() if tamanho is None else tamanho
    uma = bool(clip_leg and clip_leg["x1"])
    banda = max(bloco_legenda(t, tamanho, uma_linha=uma) for t in distintos)
    _dx, dy, _alinhamento = posicao_da_legenda(clip_leg)
    # O retangulo de faixa_texto() inclui a fila A - LEGENDA_FUNDO, por isso `fundo`, a
    # primeira fila abaixo da banda, e essa mais um: sem o mais um, a ultima fila da
    # faixa ficava fora da mistura da troca e piscava. Com a posicao (3 de outubro) as duas
    # sobem o dy da faixa.
    return {"textos": list(textos), "tamanho": tamanho,
            "faixas": {t: faixa_texto(t, tamanho, banda, clip_leg) for t in distintos},
            "topo": A - LEGENDA_TEXTO - banda - LEGENDA_ALMOFADA + dy, "fundo": A - LEGENDA_FUNDO + 1 + dy,
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
    """Cola a legenda de baixo no fotograma, a de sempre ou a da opcao legenda. Nada, com SEM_LEGENDAS."""
    if SEM_LEGENDAS:
        return
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
        w = texto_emojis.caixa(linha, fonte, desenho=d)[2]
        texto_emojis.escrever(d, ((L - w) / 2, topo + i * altura_linha), linha, fonte, (238, 238, 244))
    return base


# ---------------------------------------------------------- o letreiro, decisoes 092, 093 e 098
# O Tiago, a 28 de setembro, sobre os cartoes: "nao gosto assim muito dos separadores que vou
# metendo pretos e com a letra branca, esta basico, um pouco amador". A 29 aprovou o letreiro do
# titulo do filme Oppenheimer (sem o fogo por dentro da letra do tutorial que ele mandou, e sem
# grao, que fazia o ficheiro seis vezes maior e a 15 m nao se ve): Arial Bold na cor champanhe
# quente a subir para um branco quente, com um brilho quente fraco a volta, sobre preto. As letras
# acendem a partir do preto e aproximam-se devagar, e dissolvem-se na foto seguinte no encadeado
# de saida, como os cartoes de sempre. Com o champanhe em vez do branco (098): 13,3:1 contra 15,2:1.
#
# E O MESMO LETREIRO DOS NOMES DOS BEBES (092, 093): "O TIAGO" e "A CLARA" nascem no preto no
# ultimo segundo dos foguetes, num clip "nome" que o montar_da_mesa.py poe entre a fita e a
# primeira foto. As previas estao em scripts/discussao/ (comum.letreiro); esta e a copia que o
# filme usa, porque o render nunca importa o comum.
#
# OS TEXTOS CURTOS E AS FRASES. Ate 3 palavras: maiusculas espacadas 0,30 em, a 100 px, em linhas
# que caibam na largura do cartao de sempre. Uma frase fica com as linhas, as minusculas e o corpo
# 78 do cartao de sempre: espacada ficava lenta de ler, e as frases ja sao as que passam depressa
# (082). As letras ficam inteiras do fim da subida ate ao encadeado de saida, 2,3 s num cartao de
# 3,6 s contra 2,2 s de hoje: a proposta de 28 de setembro apagava-as 0,5 s antes, e isso tirava
# 0,4 s de leitura a todos os cartoes.
LETREIRO_SS = 2
LETREIRO_CURTO_PALAVRAS = 3
LETREIRO_CURTO_TAMANHO, LETREIRO_ESPACO = 100, 0.30
LETREIRO_FRASE_TAMANHO, LETREIRO_FRASE_MIN = 78, 44   # a frase: o corpo do cartao de sempre, e ate onde desce
NOME_TAMANHO, NOME_ESPACO = 120, 0.30
LETREIRO_ENTRA = 0.6            # segundos que as letras de um cartao levam a acender do preto
NOME_ENTRA = 0.9                # e as do nome do bebe
LETREIRO_EMPURRA = 0.025        # quanto se aproxima, por segundo
LETREIRO_QUENTE = (226, 184, 140)
LETREIRO_BRANCO = (255, 247, 234)
LETREIRO_BRILHO = (255, 150, 70)


def largura_das_letras(ln, f, passo):
    """A largura de uma linha do letreiro, letra a letra com `passo` entre elas.

    Um emoji (com o tom, a tecla ou o que o ZWJ junta) conta como uma letra, com a largura que tem na
    letra de emojis (texto_emojis.largura_das_unidades). Sem emojis nem equivalentes e a conta de
    sempre, a mesma soma pela mesma ordem.
    """
    return texto_emojis.largura_das_unidades(ln, f, passo)


def _pecas_do_letreiro(linhas, tamanho, espaco, entrelinha=1.45):
    """(mascara, emojis): as letras em branco sobre preto, LETREIRO_SS vezes maiores, uma a uma para o
    espacamento, e os emojis a cores numa camada a parte (RGBA, a cor ja multiplicada pelo alfa), ou
    None quando nao ha nenhum.

    A letra e a do cartao do estilo da Mesa (2 de outubro), a mesma no nome do bebe; sem estilo,
    o FONTE_TEXTO de sempre. UM EMOJI NAO LEVA O DEGRADE: fica com as cores dele, na mesma linha de
    base, no corpo que bate com as maiusculas, e acende e aproxima-se com as letras porque vai no
    mesmo letreiro (letreiro()). Uma linha sem emojis nem equivalentes desenha-se como sempre. Um
    simbolo de uma so cor (texto_emojis.so_uma_cor) nao e um emoji a cores: vai na mascara, com as letras.
    """
    f = letra("cartao", tamanho * LETREIRO_SS)
    passo = espaco * tamanho * LETREIRO_SS
    larguras = [largura_das_letras(ln, f, passo) for ln in linhas]
    folga = 160 * LETREIRO_SS
    W = int(max(larguras)) + 2 * folga
    H = int(tamanho * LETREIRO_SS * entrelinha * len(linhas)) + 2 * folga
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    cores = None
    y = folga
    for ln, w in zip(linhas, larguras):
        x = (W - w) / 2
        if texto_emojis.simples(ln, f):
            for c in ln:
                d.text((x, y), c, font=f, fill=255)
                x += f.getlength(c) + passo
        else:
            fe = texto_emojis.emojis_para(f)
            base = y + texto_emojis.desce(f, "a")
            for u, a_cores in texto_emojis.unidades(ln, f):
                if a_cores and texto_emojis.so_uma_cor(u):
                    # UM SIMBOLO DE UMA SO COR (o visto, as setas, as letras de uma bandeira) vai na
                    # mascara, como as letras, e leva o champanhe (098); na camada das cores saia branco
                    # (corretor, 2 de outubro a noite)
                    d.text((x, base), u, font=fe, fill=255, anchor="ls")
                    x += fe.getlength(u) + passo
                elif a_cores:
                    if cores is None:
                        cores = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    ImageDraw.Draw(cores).text((x, base), u, font=fe, fill=(255, 255, 255, 255), anchor="ls",
                                               embedded_color=True)
                    x += fe.getlength(u) + passo
                else:
                    d.text((x, y), u, font=f, fill=255)
                    x += f.getlength(u) + passo
        y += tamanho * LETREIRO_SS * entrelinha
    return m, cores


def _mascara_letreiro(linhas, tamanho, espaco, entrelinha=1.45):
    """As letras em branco sobre preto, LETREIRO_SS vezes maiores, uma a uma para o espacamento."""
    return _pecas_do_letreiro(linhas, tamanho, espaco, entrelinha)[0]


def _colorir_letreiro(m, semente, brilho_de=None):
    """Champanhe quente a subir para branco quente, com manchas lentas, e o brilho a volta.

    As tres cores vem do cartao do estilo da Mesa (quente, claro, brilho), e sem estilo sao as
    LETREIRO_* de sempre. `brilho_de` e a mascara de onde sai o brilho quando nao e a das letras: com
    emojis, as letras e os emojis juntos, para o brilho quente os envolver como as letras.
    """
    import numpy as np
    W, H = m.size
    rng = np.random.default_rng(semente)
    baixa = (rng.random((5, 16)) * 255).astype(np.uint8)
    baixa = np.asarray(Image.fromarray(baixa).resize((W, H), Image.BICUBIC), np.float32) / 255.0
    grad = np.linspace(1.0, 0.0, H, dtype=np.float32)[:, None]
    v = np.clip(0.5 * baixa + 0.5 * grad, 0, 1)
    quente = np.array(cor_do_estilo("cartao", "quente", LETREIRO_QUENTE), np.float32)
    branco = np.array(cor_do_estilo("cartao", "claro", LETREIRO_BRANCO), np.float32)
    mk = np.asarray(m, np.float32)[..., None] / 255.0
    cor = (quente + (branco - quente) * v[..., None]) * mk
    q = (m if brilho_de is None else brilho_de).resize((W // 4, H // 4), Image.BILINEAR)
    s1, s2 = 18 * LETREIRO_SS / 4, 60 * LETREIRO_SS / 4
    g1 = np.asarray(q.filter(ImageFilter.GaussianBlur(s1)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255.0
    g2 = np.asarray(q.filter(ImageFilter.GaussianBlur(s2)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255.0
    brilho = np.array(cor_do_estilo("cartao", "brilho", LETREIRO_BRILHO), np.float32) * (0.55 * g1 + 0.30 * g2)
    cor = 255 - (255 - cor) * (1 - brilho / 255.0)
    return Image.fromarray(np.clip(cor, 0, 255).astype(np.uint8), "RGB")


def letreiro(linhas, tamanho, espaco, semente=7, entrelinha=1.45):
    m, cores = _pecas_do_letreiro(linhas, tamanho, espaco, entrelinha)
    if cores is None:
        return _colorir_letreiro(m, semente)
    from PIL import ImageChops
    return _por_os_emojis(_colorir_letreiro(m, semente, ImageChops.lighter(m, cores.getchannel("A"))), cores)


def _por_os_emojis(let, cores):
    """O letreiro com os emojis por cima, com as cores deles: `cores` vem com a cor multiplicada pelo alfa."""
    import numpy as np
    a = np.asarray(cores.getchannel("A"), np.float32)[..., None] / 255.0
    rgb = np.asarray(cores.convert("RGB"), np.float32)
    out = np.asarray(let, np.float32) * (1.0 - a) + rgb
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB")


def _linhas_curtas(texto, tamanho=LETREIRO_CURTO_TAMANHO):
    f = letra("cartao", tamanho)
    passo = LETREIRO_ESPACO * tamanho

    def largura(ln):
        return largura_das_letras(ln, f, passo)
    linhas, atual = [], ""
    for p in texto.upper().split():
        tenta = (atual + " " + p).strip()
        if atual and largura(tenta) > L - 360:
            linhas.append(atual)
            atual = p
        else:
            atual = tenta
    return linhas + ([atual] if atual else [])


def letreiro_do_cartao(texto):
    """O letreiro de um cartao com texto: curto (ate 3 palavras) espacado, frase como a de sempre.

    Os dois corpos vem do cartao do estilo da Mesa (curto e frase, 2 de outubro). A frase desce
    de 6 em 6 ate caber em 4 linhas e nunca abaixo de um minimo proporcional ao corpo pedido:
    LETREIRO_FRASE_MIN para LETREIRO_FRASE_TAMANHO, que com 78 e o 44 de sempre.

    OS EQUIVALENTES TROCAM-SE ANTES DE TUDO (2 de outubro), a semente das manchas incluida: um cartao
    com o hifen U+2011 sai igual ao pixel ao do mesmo texto com o hifen de sempre. Sem nenhum, o texto
    e o mesmo e a semente tambem. Um emoji vai a cores, ver _pecas_do_letreiro().
    """
    texto = texto_emojis.com_equivalentes(texto)
    semente = 7 + sum(ord(c) for c in texto) % 97
    if len(texto.split()) <= LETREIRO_CURTO_PALAVRAS:
        curto = corpo_do_estilo("cartao", "curto", LETREIRO_CURTO_TAMANHO)
        return letreiro(_linhas_curtas(texto, curto), curto, LETREIRO_ESPACO, semente)
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    tamanho = corpo_do_estilo("cartao", "frase", LETREIRO_FRASE_TAMANHO)
    minimo = int(math.floor(tamanho * LETREIRO_FRASE_MIN / float(LETREIRO_FRASE_TAMANHO) + 0.5))
    fonte = letra("cartao", tamanho)
    linhas = quebrar_paragrafos(texto, fonte, L - 360, d)
    while len(linhas) > 4 and tamanho > minimo:
        tamanho -= 6
        fonte = letra("cartao", tamanho)
        linhas = quebrar_paragrafos(texto, fonte, L - 360, d)
    return letreiro(linhas, tamanho, 0.0, semente, entrelinha=1.4)


def pousar_letreiro(let, t_rel):
    """O letreiro no quadro, a aproximar-se devagar. A escala e fracionaria e a amostragem e bicubica
    sobre preto (o letreiro tem borda a zero), por isso nao ha borda que pisque."""
    k = (1.0 + LETREIRO_EMPURRA * max(0.0, t_rel)) / LETREIRO_SS
    W, H = let.size
    return let.transform((L, A), Image.AFFINE, (1 / k, 0, W / 2 - (L / 2) / k, 0, 1 / k, H / 2 - (A / 2) / k),
                         resample=Image.BICUBIC, fillcolor=(0, 0, 0))


def _suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def desenhar_letreiro(let, t_rel, entra):
    """O letreiro a acender do preto em `entra` s e a aproximar-se devagar."""
    tela = pousar_letreiro(let, t_rel)
    alfa = _suave(t_rel / entra) if entra > 0 else 1.0
    if alfa >= 0.999:
        return tela
    return Image.eval(tela, lambda v, a=alfa: int(v * a))


# O NOME DO BEBE COMPOE-SE COMO NA PREVIA APROVADA (092, "sim fechamos"), e nao como um encadeado de
# dois clips. A fita escurece para preto (suave) no encadeado de entrada do nome; a foto sobe do
# preto (suave) no encadeado dela; e o nome fica POR CIMA dos dois em modo ecra, inteiro ate
# NOME_APAGA_DEPOIS s depois de a foto comecar a subir, e apaga-se em NOME_APAGA s. Como encadeado
# normal, o nome comecava a apagar-se no primeiro fotograma da foto e ficava inteiro 0,7 s em vez de
# 1,1 s (revisores, 30 de setembro).
NOME_APAGA_DEPOIS = 0.4
NOME_APAGA = 0.6


def compor_nome(camadas, nome, t):
    """O fotograma quando um clip "nome" esta ativo. camadas: [(clip, imagem)] dos clips ativos."""
    from PIL import ImageChops
    ini = float(nome["inicio_s"])
    dt = t - ini
    antes = [(c, im) for c, im in camadas if c is not nome and float(c["inicio_s"]) < ini]
    depois = [(c, im) for c, im in camadas if c is not nome and float(c["inicio_s"]) > ini]
    preto = Image.new("RGB", (L, A), (0, 0, 0))
    if depois:
        c_foto, im_foto = depois[-1]
        u = t - float(c_foto["inicio_s"])
        fundo = Image.blend(preto, im_foto.convert("RGB"), _suave(u / (float(c_foto["transicao_s"]) or 0.01)))
    elif antes:
        entra = float(nome["transicao_s"]) or 0.01
        fundo = Image.blend(antes[-1][1].convert("RGB"), preto, _suave(dt / entra))
    else:
        fundo = preto
    # quando a foto comeca a subir (o fim do nome menos o encadeado dela)
    foto_sobe = float(nome["duracao_s"]) - (float(depois[-1][0]["transicao_s"]) if depois else NOME_FOTO_SOBE_OMISSAO)
    if dt < foto_sobe + NOME_APAGA_DEPOIS:
        alfa = _suave(dt / NOME_ENTRA)
    else:
        alfa = 1.0 - _suave((dt - foto_sobe - NOME_APAGA_DEPOIS) / NOME_APAGA)
    if alfa <= 0.001:
        return fundo
    let = pousar_letreiro(nome["_pronto"]["let"], dt)
    if alfa < 0.999:
        let = Image.eval(let, lambda v, a=alfa: int(v * a))
    return ImageChops.screen(fundo, let)


NOME_FOTO_SOBE_OMISSAO = 1.0


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


# ---------------------------------------------------------- o estilo da Mesa, 2 de outubro
# O Tiago, a 2 de outubro, para o dia com a Clara: a Mesa passa a deixar mudar o tipo e o tamanho
# da letra, as cores dos cartoes, do contador e da fita de 1995, e as da intro ("A Clara pediu-me
# para alterarmos o vermelho que esta na intro da Marvel, pois diz que parece demasiado Marvel").
# A Mesa guarda isso no topo do estado, em est.estilo; o montar_da_mesa.py escreve
# data/montagens/<nome>.estilo.json so com o que difere da omissao, e o render le-o no
# carregar_montagem(), por onde passam o pai e cada fatia: o estilo chega a todas sem ninguem o
# passar a mao, e todas desenham o mesmo filme.
#
#   legenda   a faixa de baixo e o texto dentro das fotos dos grupos: fonte, tamanho (o corpo a
#             1080, que nos grupos e o de omissao quando o clip nao traz o seu tt), cor e fundo
#             (a opacidade da faixa, de 0 a 1); e a posicao da faixa de baixo, {dx, dy,
#             alinhamento} (3 de outubro), ver posicao_da_legenda()
#   cartao    o letreiro dos cartoes: fonte, curto (ate 3 palavras), frase, e as cores quente,
#             claro e brilho; o nome do bebe e o mesmo letreiro, com a mesma letra e cores
#   nome      o tamanho do nome do bebe
#   contador  as cores do contador e da fita de 1995, ver linha_tempo.CORES_DO_ESTILO, o
#             continuo (true = a fita de 1995 numa so peca com o contador, ver
#             linha_tempo._meses_numa_peca(); ausente = como esta) e a data_afastada (true = a
#             data do nascimento mais longe do "SET" tambem na fita de duas pecas, ver
#             linha_tempo.DATA_AFASTADA; ausente = como esta); e a fonte (3 de outubro), a letra
#             de todos os textos do contador e da fita, um id de data/fontes.json como a das
#             legendas, com o Arial Bold por omissao
#   intro    as cores (fundo, papel, tinta, letra), o tamanho e a letra (fonte) do letreiro da
#             intro. Quem a faz e o intro_flipbook.py, e quem a troca na fanfarra e o
#             montar_da_mesa.py (intro_da_paleta()): o render so le o nome do ficheiro no CSV,
#             como sempre
#
# SEM ESTILO, NENHUM PIXEL MUDA. As omissoes sao as constantes de sempre, lidas delas e nao
# copiadas (estilo_omissao()), e a letra de omissao abre pelo FONTE_TEXTO, como sempre abriu,
# sem passar pelo data/fontes.json.
#
# A LETRA DA INTRO, desde 2 de outubro a noite. A decisao 084 fechou o letreiro em Impact porque o
# efeito da intro e a fotografia aparecer por dentro das letras, e isso precisa de area: o Arial
# Bold mostrava menos 58% da foto. O Tiago pediu para a poder mudar, e abriu-se nos termos dela: so
# as letras de data/fontes_intro.json com oferecida true, as que mostram pelo menos dois tercos da
# foto que o Impact mostra e separam as letras a 15 m no minimo da Mesa (132). A omissao continua a
# ser o Impact, "como esta", e sem a chave (ou com "impact") nada muda, nem o nome do ficheiro. O
# tamanho nunca abaixo de 132 e quer dizer sempre a altura do Impact a esse corpo. E o contador ficava
# em Arial Bold (o contrato de 2 de outubro so lhe dava cores); desde 3 de outubro tem a sua fonte,
# est.estilo.contador.fonte, com o Arial Bold por omissao.
FONTES_DA_INTRO = os.path.join(REPO, "data", "fontes_intro.json")
INTRO_FONTE = "impact"
# A caixa em que cada letra da intro foi medida: o nome em Impact a 288. Uma letra vai ao corpo
# round(corpo do Impact x corpo_que_cabe / 288), sempre na caixa do Impact ao mesmo corpo.
INTRO_CORPO_DA_CAIXA = 288
FONTES_DA_MESA = os.path.join(REPO, "data", "fontes.json")
LETRA_OMISSAO = "arial_bold"
INTRO_FUNDO, INTRO_PAPEL, INTRO_TINTA = (150, 22, 28), (247, 233, 210), (46, 14, 16)   # os do intro_flipbook
# A COR DAS LETRAS DO LETREIRO SOLIDO, acrescentada ao contrato a 2 de outubro: as paletas que a
# Clara vai ver chamam-se pelas duas cores ("vinho e champanhe", "preto e dourado"), e a segunda e
# a das letras. Sem ela as quatro tinham as letras brancas da Marvel. A omissao e o branco de
# sempre do intro_flipbook.LETRA.
INTRO_LETRA = (252, 250, 250)
# O corpo do letreiro: nunca abaixo de 132 (decisao 084) e nunca acima de 309, o maior que deixa
# o nome dentro de 93% da largura (intro_flipbook.TAMANHO_MAX, medido a 2 de outubro). O contrato
# dizia ate 400, e o Impact a 400 da 2308 px num quadro de 1920: o nome cortado nas duas pontas.
INTRO_TAMANHO, INTRO_TAMANHO_MIN, INTRO_TAMANHO_MAX = 288, 132, 309
# Os corpos que se aceitam, a 1080. Fora disto fica a omissao, com aviso, como no tt dos grupos. O
# da legenda e o do TEXTO_FOTO_TAMANHOS, porque o mesmo numero serve a faixa e o texto das fotos.
ESTILO_CORPOS = {("legenda", "tamanho"): TEXTO_FOTO_TAMANHOS, ("cartao", "curto"): (60, 160),
                 ("cartao", "frase"): (44, 120), ("nome", "tamanho"): (60, 200),
                 ("intro", "tamanho"): (INTRO_TAMANHO_MIN, INTRO_TAMANHO_MAX)}
# As escolhas do contador que nao sao cores, true ou "como esta" (2 de outubro): a fita de 1995
# numa so peca, e a data do nascimento afastada do "SET" na fita de duas pecas.
ESCOLHAS_DO_CONTADOR = ("continuo", "data_afastada")
_ESTILO = {}            # o estilo da montagem que se esta a fazer, so com o que difere
_LETRAS = {}              # (id da letra, corpo) -> ImageFont
_ENTRADAS = None          # as letras de data/fontes.json, lidas uma vez por estilo
_LETRAS_AVISADAS = set()


def cor_rgb(valor):
    """"#E2B88C" (ou "#ebc", ou sem o cardinal) -> (226, 184, 140); None se nao for uma cor."""
    if not isinstance(valor, str):
        return None
    m = re.fullmatch(r"\s*#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\s*", valor)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cor_hex(rgb):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb[:3])


def estilo_omissao():
    """O estilo de hoje, {parte: {chave: valor}}, tirado das constantes do codigo.

    E a tabela do contrato de 2 de outubro lida do codigo e nao copiada: se o contrato e o
    codigo discordarem, vale o codigo. O fundo da legenda e a fracao com tres casas do
    LEGENDA_ALFA, 0,647 para 165.
    """
    return {
        "legenda": {"fonte": LETRA_OMISSAO, "tamanho": LEGENDA_TAMANHO, "cor": cor_hex(LEGENDA_COR),
                    "fundo": round(LEGENDA_ALFA / 255.0, 3)},
        "cartao": {"fonte": LETRA_OMISSAO, "curto": LETREIRO_CURTO_TAMANHO,
                   "frase": LETREIRO_FRASE_TAMANHO, "quente": cor_hex(LETREIRO_QUENTE),
                   "claro": cor_hex(LETREIRO_BRANCO), "brilho": cor_hex(LETREIRO_BRILHO)},
        "nome": {"tamanho": NOME_TAMANHO},
        "contador": dict({chave: cor_hex(linha_tempo._CORES_DE_SEMPRE[const])
                          for chave, const in linha_tempo.CORES_DO_ESTILO.items()},
                         # a letra do contador (3 de outubro), como a das legendas: o Arial Bold de sempre
                         fonte=LETRA_OMISSAO),
        "intro": {"fundo": cor_hex(INTRO_FUNDO), "papel": cor_hex(INTRO_PAPEL),
                  "tinta": cor_hex(INTRO_TINTA), "letra": cor_hex(INTRO_LETRA),
                  "tamanho": INTRO_TAMANHO, "fonte": INTRO_FONTE},
    }


def letras_da_mesa():
    """{id: entrada} das letras de data/fontes.json; {} se o ficheiro nao estiver ou nao se ler."""
    try:
        with open(FONTES_DA_MESA, encoding="utf-8") as fh:
            dados = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {e["id"]: e for e in (dados.get("fontes") or [])
            if isinstance(e, dict) and isinstance(e.get("id"), str)}


def letras_da_intro(caminho=None):
    """{id: entrada} das letras OFERECIDAS para o letreiro da intro, de data/fontes_intro.json.

    So as que tem oferecida true: as outras estao no ficheiro para se ver porque ficaram de fora,
    e nenhuma delas pode chegar ao filme, nem escrita a mao no estado. {} se o ficheiro nao estiver
    ou nao se ler, e entao so ha o Impact.
    """
    try:
        with open(caminho or FONTES_DA_INTRO, encoding="utf-8") as fh:
            dados = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {e["id"]: e for e in (dados.get("letras") or [])
            if isinstance(e, dict) and e.get("oferecida") is True and isinstance(e.get("id"), str)}


def abrir_letra_da_intro(entrada, corpo):
    """A letra de uma entrada de data/fontes_intro.json no corpo pedido. Levanta OSError se nao abre.

    O FICHEIRO, O INDICE E OS EIXOS, como foi medida. A Bahnschrift Condensed e uma letra variavel
    aberta no peso 700 e na largura 75: o abrir_letra() so poe o peso, e ela saia na largura 100,
    que e outra letra. Os eixos vao todos, pela ordem do fvar, que e a ordem em que a medida os
    guardou; um ficheiro com outros eixos (uma versao nova da letra) nao abre, em vez de abrir
    noutra forma sem ninguem dar por isso.
    """
    try:
        f = ImageFont.truetype(entrada["ficheiro"], corpo, index=int(entrada.get("indice") or 0))
        eixos = entrada.get("eixos")
        if eixos:
            do_ficheiro = f.get_variation_axes()
            if len(do_ficheiro) != len(eixos):
                raise OSError("tem %d eixos e a medida %d" % (len(do_ficheiro), len(eixos)))
            for eixo, v in zip(do_ficheiro, eixos):
                if not eixo["minimum"] <= float(v) <= eixo["maximum"]:
                    raise OSError("o eixo %s vai de %s a %s e a medida pede %s"
                                  % (eixo.get("name"), eixo["minimum"], eixo["maximum"], v))
            f.set_variation_by_axes([float(v) for v in eixos])
        return f
    except OSError:
        raise
    except (ValueError, KeyError, TypeError, AttributeError) as erro:
        raise OSError(str(erro))


def letra_da_intro(fonte, avisos=None, letras=None):
    """A entrada da letra pedida para o letreiro da intro, ou None, que e o Impact de sempre.

    Sem letra, ou com "impact", e None sem aviso. Um id que nao se conhece, que nao e oferecido
    ou cujo ficheiro nao abre da None COM AVISO, e entao o Impact vale para tudo: o desenho, o
    resumo e o nome do ficheiro. Nunca uma letra a meio: ou a pedida inteira, ou o Impact.
    """
    avisos = [] if avisos is None else avisos
    if fonte is None or (isinstance(fonte, str) and fonte.strip() in ("", INTRO_FONTE)):
        return None
    letras = letras_da_intro() if letras is None else letras
    e = letras.get(fonte.strip()) if isinstance(fonte, str) else None
    if e is None:
        avisos.append("estilo.intro.fonte %r nao e uma das letras oferecidas para a intro "
                      "(data/fontes_intro.json): fica o Impact" % (fonte,))
        return None
    try:
        abrir_letra_da_intro(e, 40)
    except OSError as erro:
        avisos.append("estilo.intro.fonte %r nao abre (%s): fica o Impact" % (fonte, erro))
        return None
    return e


def corpo_da_letra_da_intro(entrada, corpo_impact):
    """O corpo da letra da intro que poe o nome na caixa do nome em Impact a corpo_impact.

    A medida guardou o corpo_que_cabe a 288; a outro corpo do Impact, a letra vai a proporcao,
    arredondada pelo round() do Python (as metades para o par). A Mesa, se fizer a mesma conta,
    tem de arredondar igual.
    """
    return max(1, int(round(corpo_impact * float(entrada["corpo_que_cabe"]) / INTRO_CORPO_DA_CAIXA)))


def _corpo_inteiro(v):
    """Um corpo como inteiro: 56, 56.0 e "56" valem; o booleano e o que tem decimais nao."""
    if isinstance(v, bool):
        return None
    if isinstance(v, str):
        v = v.strip()
        return int(v) if v.isdigit() else None
    if isinstance(v, float):
        return int(v) if v.is_integer() else None
    return v if isinstance(v, int) else None


def _valor_do_estilo(parte, chave, v, letras, avisos):
    """Um valor do estilo limpo ("#RRGGBB", inteiro, id, fracao), ou None com aviso se nao presta."""
    omissao = estilo_omissao()[parte][chave]
    if chave == "fonte":
        if isinstance(v, str) and v.strip() in letras:
            return v.strip()
        avisos.append("estilo.%s.fonte %r nao esta em data/fontes.json, fica o Arial Bold" % (parte, v))
        return None
    if (parte, chave) in ESTILO_CORPOS:
        n = _corpo_inteiro(v)
        baixo, alto = ESTILO_CORPOS[(parte, chave)]
        if n is None or not baixo <= n <= alto:
            avisos.append("estilo.%s.%s %r tem de ser inteiro entre %d e %d, fica %d"
                          % (parte, chave, v, baixo, alto, omissao))
            return None
        return n
    if (parte, chave) == ("legenda", "fundo"):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            avisos.append("estilo.legenda.fundo %r tem de ser um numero de 0 a 1, fica %s" % (v, omissao))
            return None
        return round(float(v), 3)
    rgb = cor_rgb(v)
    if rgb is None:
        avisos.append("estilo.%s.%s %r nao e uma cor #RRGGBB, fica %s" % (parte, chave, v, omissao))
        return None
    return cor_hex(rgb)


def _posicao_do_estilo(v, avisos):
    """O est.estilo.legenda.posicao limpo, so com o que difere de {dx: 0, dy: 0, "centro"}; {} sem nada.

    Um dx ou dy que nao e inteiro, ou fora de POSICAO_DX e POSICAO_DY, fica 0 com aviso, como um
    corpo fora dos limites; um alinhamento que nao existe fica "centro", com aviso.
    """
    if v in (None, "") or v == {}:
        return {}
    if not isinstance(v, dict):
        avisos.append("estilo.legenda.posicao nao e um objeto {dx, dy, alinhamento}, fica como esta: %r" % (v,))
        return {}
    limpo = {}
    for chave, (baixo, alto) in (("dx", POSICAO_DX), ("dy", POSICAO_DY)):
        bruto = v.get(chave)
        if bruto in (None, ""):
            continue
        n = _inteiro_com_sinal(bruto)
        if n is None or not baixo <= n <= alto:
            avisos.append("estilo.legenda.posicao.%s %r tem de ser inteiro entre %d e %d, fica 0"
                          % (chave, bruto, baixo, alto))
            continue
        if n:
            limpo[chave] = n
    alinhamento = v.get("alinhamento")
    if alinhamento not in (None, ""):
        if alinhamento in POSICAO_ALINHAMENTOS:
            if alinhamento != POSICAO_ALINHAMENTOS[0]:
                limpo["alinhamento"] = alinhamento
        else:
            avisos.append("estilo.legenda.posicao.alinhamento %r nao existe (%s), fica centro"
                          % (alinhamento, ", ".join(POSICAO_ALINHAMENTOS)))
    for chave in v:
        if chave not in ("dx", "dy", "alinhamento"):
            avisos.append("estilo.legenda.posicao com a chave %r, que nao existe, ignorada" % (chave,))
    return limpo


# OS CORPOS DOS TEXTOS DO CONTADOR E DA FITA DE 1995, a 1080 (linha_tempo): o rotulo e a data de
# chegada, os meses da regua, os meses e as datas da fita, o texto dos marcos e os nascimentos.
CORPOS_DO_CONTADOR = (("o rotulo e a data de chegada do contador", 46), ("os meses da fita de 1995", 38),
                      ("as datas da fita de 1995", 40), ("o texto dos marcos da fita", 58))


def _leitura_da_letra_do_contador(entrada):
    """[aviso] da letra do contador a 15 m, pela regra das legendas (corpo_minimo, decisao 084).

    Le-se como hoje quando o corpo esta para o minimo da letra como o de hoje esta para os 58 do
    Arial Bold. Os corpos do contador nao mudam com a letra, e por isso diz-se o que cada um passa
    a valer. Nao muda nada.
    """
    nome = entrada.get("nome") or entrada.get("id") or "a letra"
    if entrada.get("ficheiro") and not os.path.exists(entrada["ficheiro"]):
        return ["estilo: a letra %s nao esta em disco (%s): o contador sai em Arial Bold ate ela estar"
                % (nome, entrada["ficheiro"])]
    minimo = entrada.get("corpo_minimo")
    if not minimo:
        return ["estilo: o contador em %s: a letra ainda nao tem o corpo minimo medido, nao sei dizer se "
                "se le a 15 metros" % nome]
    piores = []
    for quem, corpo in CORPOS_DO_CONTADOR:
        como = corpo * 58.0 / float(minimo)
        if como < corpo - 0.5:
            piores.append("%s, a %d, como o Arial Bold a %d" % (quem, corpo, int(math.floor(como + 0.5))))
    if not piores:
        return []
    return ["estilo: o contador em %s le-se a 15 metros pior do que em Arial Bold (corpo minimo %d contra "
            "58): %s" % (nome, minimo, "; ".join(piores))]


def normalizar_estilo(bruto, avisos=None):
    """O est.estilo da Mesa, ou o estilo.json, -> so o que difere da omissao, ja limpo.

    Cores em "#RRGGBB" maiusculas, corpos inteiros, a letra pelo id de data/fontes.json e o
    fundo da legenda em fracao com tres casas. O que nao presta fica na omissao COM AVISO, como
    nas opcoes dos textos: uma cor mal escrita que caisse em silencio era o filme a sair com
    outra cor sem ninguem saber porque. Um valor igual ao de omissao nao se guarda (o fundo
    compara-se no alfa que vai ao ecra, 165), e e isso que faz um estilo vazio e um estilo todo
    na omissao darem o filme de sempre. O montar_da_mesa.py e o render passam os dois por aqui:
    um estilo.json escrito a mao tem a mesma guarda que o da Mesa.
    """
    avisos = [] if avisos is None else avisos
    if bruto in (None, "") or bruto == {}:
        return {}
    if not isinstance(bruto, dict):
        avisos.append("o estilo nao e um objeto, fica o de sempre: %r" % (bruto,))
        return {}
    omissao = estilo_omissao()
    letras = None
    saida = {}
    for parte, valores in bruto.items():
        if parte not in omissao:
            avisos.append("estilo com a parte %r, que nao existe, ignorada" % (parte,))
            continue
        if valores in (None, ""):
            continue
        if not isinstance(valores, dict):
            avisos.append("estilo.%s nao e um objeto, fica o de sempre" % parte)
            continue
        for chave, v in valores.items():
            if parte == "contador" and chave in ESCOLHAS_DO_CONTADOR:
                # O CONTADOR NUMA SO PECA (contrato 1b, 2 de outubro): true desenha a fita de 1995
                # como o contador, ver linha_tempo._meses_numa_peca(). E A DATA AFASTADA, do mesmo
                # dia: true poe a data do nascimento mais longe do "SET" na fita de duas pecas, ver
                # linha_tempo.DATA_AFASTADA. False e ausente sao "como esta", e por isso so o true
                # se guarda. Ficam fora do estilo_omissao(), que e so de cores, como a Mesa o compara
                # (testes_mesa_1002, teste_estilo_da_mesa_igual_ao_render).
                if v is True:
                    saida.setdefault(parte, {})[chave] = True
                elif v is not False and v not in (None, ""):
                    avisos.append("estilo.contador.%s %r tem de ser true ou false, fica como esta" % (chave, v))
                continue
            if (parte, chave) == ("contador", "fonte"):
                # A LETRA DO CONTADOR (contrato de 3 de outubro, ponto 1): a mesma lista e a mesma regra
                # das legendas, um id de data/fontes.json. Fica fora do estilo_omissao(), como as
                # escolhas do contador, e o Arial Bold (a omissao) nao se guarda: "como esta".
                if v in (None, ""):
                    continue
                if letras is None:
                    letras = letras_da_mesa()
                    letras.setdefault(LETRA_OMISSAO, {})
                if isinstance(v, str) and v.strip() in letras:
                    if v.strip() != LETRA_OMISSAO:
                        saida.setdefault(parte, {})[chave] = v.strip()
                        avisos.extend(_leitura_da_letra_do_contador(letras.get(v.strip()) or {}))
                else:
                    avisos.append("estilo.contador.fonte %r nao esta em data/fontes.json, fica o Arial Bold" % (v,))
                continue
            if (parte, chave) == ("legenda", "posicao"):
                # A POSICAO DAS LEGENDAS (contrato de 3 de outubro, ponto 3), fora do estilo_omissao()
                # como as escolhas do contador: so o que difere de {0, 0, "centro"} se guarda.
                limpo = _posicao_do_estilo(v, avisos)
                if limpo:
                    saida.setdefault(parte, {})[chave] = limpo
                continue
            if chave not in omissao[parte]:
                avisos.append("estilo.%s com a chave %r, que nao existe, ignorada" % (parte, chave))
                continue
            if v is None or v == "":
                continue
            if (parte, chave) == ("intro", "fonte"):
                # A LETRA DA INTRO (2 de outubro, a noite) nao e uma das de data/fontes.json: e uma das
                # oferecidas em data/fontes_intro.json. O Impact e a omissao e nao se guarda; o que nao
                # vale fica no Impact, com aviso (letra_da_intro).
                e = letra_da_intro(v, avisos)
                if e is not None and e["id"] != INTRO_FONTE:
                    saida.setdefault(parte, {})[chave] = e["id"]
                continue
            if chave == "fonte" and letras is None:
                letras = letras_da_mesa()
                letras.setdefault(LETRA_OMISSAO, {})
            limpo = _valor_do_estilo(parte, chave, v, letras, avisos)
            if limpo is None:
                continue
            if (parte, chave) == ("legenda", "fundo"):
                igual = alfa_do_fundo(limpo) == LEGENDA_ALFA
            else:
                igual = limpo == omissao[parte][chave]
            if not igual:
                saida.setdefault(parte, {})[chave] = limpo
    return saida


def ler_estilo(nome, pasta=None):
    """O estilo.json da montagem `nome`, tal como esta no ficheiro; {} se nao houver."""
    caminho = os.path.join(pasta or MONTAGENS, nome + ".estilo.json")
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as erro:
        print("  AVISO: o estilo %s nao se le (%s), fica o de sempre" % (caminho, erro))
        return {}


def aplicar_estilo(estilo=None, avisos=None):
    """Poe um estilo a valer neste processo e devolve-o limpo; sem nada, volta o de sempre.

    Limpa-o outra vez com normalizar_estilo(), esquece as letras abertas com o estilo de antes
    e poe as cores do contador no linha_tempo. Os avisos vao para a lista `avisos`; sem lista,
    imprimem-se.
    """
    global _ESTILO, _ENTRADAS
    proprios = [] if avisos is None else avisos
    _ESTILO = normalizar_estilo(estilo, proprios)
    _ENTRADAS = None
    _LETRAS.clear()
    _FONTES.clear()
    _LETRAS_AVISADAS.clear()
    contador = _ESTILO.get("contador", {})
    # A letra do contador (3 de outubro): o linha_tempo abre-a por aqui, com o peso das letras variaveis;
    # sem ela fica o Arial Bold de sempre, aberto como sempre.
    letra_contador = contador.get("fonte")
    linha_tempo.aplicar_cores({k: cor_rgb(v) for k, v in contador.items()
                               if k not in ESCOLHAS_DO_CONTADOR and k != "fonte"},
                              continuo=contador.get("continuo") is True,
                              data_afastada=contador.get("data_afastada") is True,
                              letra=(lambda corpo: abrir_letra(letra_contador, corpo)) if letra_contador else None)
    if avisos is None:
        for a in proprios:
            print("  AVISO: %s" % a)
    return _ESTILO


def estilo_ativo():
    """O estilo que esta a valer, so com o que difere da omissao."""
    return json.loads(json.dumps(_ESTILO))


def corpo_do_estilo(parte, chave, omissao):
    return _ESTILO.get(parte, {}).get(chave, omissao)


def cor_do_estilo(parte, chave, omissao):
    v = _ESTILO.get(parte, {}).get(chave)
    return omissao if v is None else cor_rgb(v)


def legenda_tamanho():
    """O corpo da legenda: o do estilo, ou o LEGENDA_TAMANHO."""
    return corpo_do_estilo("legenda", "tamanho", LEGENDA_TAMANHO)


def texto_foto_tamanho():
    """O corpo do texto das fotos de um grupo sem tt: o da legenda do estilo, ou o TEXTO_FOTO_TAMANHO."""
    return corpo_do_estilo("legenda", "tamanho", TEXTO_FOTO_TAMANHO)


def legenda_cor():
    return cor_do_estilo("legenda", "cor", LEGENDA_COR)


def alfa_do_fundo(f):
    """O fundo da legenda do estilo (0 a 1) no alfa que vai ao ecra, de 0 a 255.

    ARREDONDA COMO A MESA, metade para cima (o Math.round do editor_base.html), e nao como o round
    do Python, que manda as metades para o par. A barra da Mesa oferece fundos com meio exato: 0,3
    da 76,5 e 0,7 da 178,5, e o filme saia um nivel abaixo do que a Mesa desenhava e dizia "como o
    render" (revisao de 2 de outubro). No 0,647 de sempre os dois dao 165.
    """
    return int(math.floor(float(f) * 255 + 0.5))


def fundo_da_legenda(omissao):
    """O alfa da faixa escura (a de baixo e a das fotos): o do estilo, ou o de sempre."""
    f = _ESTILO.get("legenda", {}).get("fundo")
    return omissao if f is None else alfa_do_fundo(f)


def _avisar_letra(ident, porque):
    if ident not in _LETRAS_AVISADAS:
        _LETRAS_AVISADAS.add(ident)
        print("  AVISO: a letra %s nao abre (%s): fica o Arial Bold" % (ident, porque))


def abrir_letra(ident, corpo, entradas=None, avisar=True):
    """A letra `ident` de data/fontes.json no corpo pedido, ou None se nao abre.

    NAS LETRAS VARIAVEIS O PESO PE-SE PELO NOME DO EIXO, e os outros eixos ficam na omissao do
    ficheiro, que e o que a Mesa mostra com a letra pedida a Google so pelo peso. Sem isto o
    ficheiro abre no seu peso de omissao, e esse nao e o pedido: o Montserrat e o League Spartan
    abrem no Thin (100), e o Fraunces no Black (900). Medido a 2 de outubro, o eixo a 700 da a
    mesma tinta que a instancia "Bold" do proprio ficheiro, ver teste_letra_variavel_no_peso_pedido.
    """
    global _ENTRADAS
    if entradas is None:
        if _ENTRADAS is None:
            _ENTRADAS = letras_da_mesa()
        entradas = _ENTRADAS
    e = entradas.get(ident)
    try:
        if not e or not e.get("ficheiro"):
            raise OSError("nao esta em data/fontes.json")
        f = ImageFont.truetype(e["ficheiro"], corpo)
        peso = e.get("eixo_peso")
        if peso:
            valores, achou = [], False
            for eixo in f.get_variation_axes():
                nome = eixo.get("name")
                nome = nome.decode("utf-8", "replace") if isinstance(nome, bytes) else str(nome)
                if nome.strip().lower() in ("weight", "wght"):
                    valores.append(max(eixo["minimum"], min(eixo["maximum"], peso)))
                    achou = True
                else:
                    valores.append(eixo["default"])
            if not achou:
                raise OSError("nao tem eixo de peso")
            f.set_variation_by_axes(valores)
        return f
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as erro:
        if avisar:
            _avisar_letra(ident, erro)
        return None


def letra(parte, corpo):
    """A letra da `parte` do estilo ("legenda" ou "cartao") no corpo pedido, como ImageFont.

    Sem estilo e o FONTE_TEXTO, aberto como sempre foi. Uma letra que nao abre cai no Arial
    Bold com um aviso, uma vez por processo, e o render continua: a regra do imagem_da_marca(),
    uma letra em falta nao para um render de quinze minutos a meio.
    """
    ident = _ESTILO.get(parte, {}).get("fonte")
    chave = (ident, corpo)
    if chave not in _LETRAS:
        f = abrir_letra(ident, corpo) if ident else None
        _LETRAS[chave] = f if f is not None else ImageFont.truetype(FONTE_TEXTO, corpo)
    return _LETRAS[chave]


# OS CARACTERES QUE A LETRA NAO TEM (corretor, 2 de outubro). A Pillow desenha um caracter que a
# letra nao tem com o glifo de falta (.notdef), que no Arial Bold e uma caixa vazia, e nao se
# queixa. O browser da Mesa mostra o mesmo texto com outra letra, e por isso o filme saia diferente
# do que a Mesa mostra, sem aviso: na leitura 63 o cargo 3 dos creditos, "Audio-Visual Operations
# Maestro", traz o hifen nao separavel (U+2011), e saia "Audio" + caixa + "Visual". O Arial Bold
# tambem nao tem o hifen U+2010, os emojis nem os invisiveis U+2060 e U+FEFF.
# Um caracter falta quando sai igual, ao pixel, ao de um nao-caracter (U+FFFF), que nenhuma letra
# pode ter. A Mesa tem a sua regra (forasDaLetra, no Validar), para os textos dos clips.
#
# DESDE A TARDE DE 2 DE OUTUBRO OS EMOJIS SAEM A CORES (texto_emojis), e os equivalentes valem em todos
# os textos do filme. Estas quatro ficam aqui com os nomes de sempre, e sao as de la.
NAO_CARACTER = texto_emojis.NAO_CARACTER
# OS QUE TEM UM IGUAL A VISTA. O hifen nao separavel e o hifen U+2010 desenham-se como o hifen de
# sempre, que e o que se ve na Mesa; os invisiveis tiram-se. Nao muda o texto dele: e o mesmo
# sinal, desenhado com o glifo que a letra tem.
EQUIVALENTES = texto_emojis.EQUIVALENTES


def caracteres_sem_letra(texto, fonte):
    """Os caracteres de `texto` que o filme nao desenha: nem a `fonte` (um ImageFont) nem a letra de
    emojis os tem. Pela ordem e sem repetir; no filme saem como uma caixa vazia.

    DESDE A TARDE DE 2 DE OUTUBRO conta so isso. Um emoji que a letra de emojis tem sai a cores, os
    EQUIVALENTES saem como o seu igual, e os seletores, o ZWJ e as etiquetas nao se desenham: nenhum
    deles e caixa vazia. Os espacos nao contam (um espaco e vazio em qualquer letra, como pode ser o
    glifo de falta). As sequencias que esta Pillow nao junta dizem-se a parte, texto_emojis.sequencias().
    """
    return texto_emojis.sem_letra(texto, fonte)


def com_equivalentes(texto):
    """O texto com os EQUIVALENTES trocados: o mesmo texto quando nao tem nenhum."""
    return texto_emojis.com_equivalentes(texto)


def nome_do_caracter(c):
    """'U+2011 (NON-BREAKING HYPHEN)': para os avisos, que um caracter invisivel nao se le."""
    return texto_emojis.nome_do_caracter(c)


def avisos_dos_caracteres(onde, texto, fonte):
    """[aviso] de um texto do filme: os caracteres que saem numa caixa vazia (caracteres_sem_letra) e
    os emojis de varios caracteres que esta Pillow nao junta (sem o raqm). Nao muda nada."""
    return texto_emojis.avisos_do_texto(onde, texto, fonte)


def avisos_dos_textos(clips):
    """[aviso] dos textos dos clips que o filme nao desenha como estao escritos. Nao muda nada.

    Os caracteres que nem a letra nem a de emojis tem (caixa vazia), os emojis de varios caracteres
    que esta Pillow nao junta (texto_emojis.sequencias) e os emojis escuros, que quase nao se veem no
    preto (texto_emojis.emojis_escuros, corretor de 2 de outubro). `clips` sao linhas do CSV da montagem, ou as
    do montar_da_mesa.py, com tipo, ordem, texto_ecra, textos_fotos e destaque. Cada texto mede-se na
    letra onde vai: os cartoes e os nomes na do cartao, a fita e os contadores no Arial Bold da
    linha_tempo, o resto na da legenda. Cada aviso diz o clip ("clip N"), que o montar renumera.
    """
    avisos = []
    fontes = {}
    for c in clips:
        tipo = c.get("tipo") or ""
        textos = []
        t = c.get("texto_ecra") or ""
        if t.strip():
            textos.append(("o texto do clip %s" % c.get("ordem"), t))
        for k, x in enumerate(ler_textos_fotos(c.get("textos_fotos") or "") or []):
            if x:
                textos.append(("o texto da foto %d do clip %s" % (k + 1, c.get("ordem")), x))
        zd = c.get("destaque") or ""
        if isinstance(zd, str) and zd.strip():
            try:
                zd = json.loads(zd)
            except ValueError:
                zd = None
        if isinstance(zd, dict) and isinstance(zd.get("texto"), str) and zd["texto"].strip():
            textos.append(("o nome do destaque do clip %s" % c.get("ordem"), zd["texto"]))
        if not textos:
            continue
        qual = "cartao" if tipo in ("cartao", "nome") else "fita" if tipo in ("contador", "marcos") else "legenda"
        if qual not in fontes:
            fontes[qual] = (letra("cartao", LETREIRO_CURTO_TAMANHO) if qual == "cartao" else
                            ImageFont.truetype(linha_tempo.FONTE, linha_tempo.CORPO_ROTULO) if qual == "fita" else
                            letra("legenda", legenda_tamanho()))
        for onde, x in textos:
            avisos.extend(texto_emojis.avisos_do_texto(onde, x, fontes[qual]))
    return avisos


# Os clips que tem a legenda de baixo. Os cartoes, o nome do bebe, o contador e a fita escrevem o texto
# de outra maneira, e a posicao e a legenda numa linha nao lhes tocam.
TIPOS_COM_LEGENDA = ("foto", "video", "lado", "colagem", "pilha")


def legendas_do_clip(c):
    """[(texto, tamanho)] do que um clip mostra na legenda de baixo, com o tamanho de cada (None = o do estilo).

    A legenda do clip; e, na opcao "na legenda de baixo" dos grupos, o texto de cada foto (o do grupo
    nos vazios), no tamanho do grupo. No mergulho so a legenda do clip, como no preparar().
    """
    if (c.get("tipo") or "") not in TIPOS_COM_LEGENDA:
        return []
    texto = (c.get("texto_ecra") or "").strip()
    textos = ler_textos_fotos(c.get("textos_fotos") or "") or []
    mergulho = c.get("tipo") == "colagem" and (c.get("tratamento") or "").strip() == MERGULHO_ESTILO
    if c.get("tipo") in ("lado", "colagem", "pilha") and textos and any(textos) and not mergulho:
        # CALADO: o ler_textos_opcoes() avisa do que nao presta na coluna, e quem diz esse aviso e o
        # preparar(), uma vez (teste_fatias_pelo_main_dao_o_mesmo_ficheiro). Aqui so se le.
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            opcoes = ler_textos_opcoes(c.get("textos_opcoes") or "")
        if opcoes["modo"] == "legenda":
            return [(t, opcoes["tamanho"]) for t in dict.fromkeys(x or texto for x in textos) if t]
    return [(texto, None)] if texto else []


def avisos_das_legendas(clips):
    """[aviso] da legenda numa linha que nao cabe e da posicao que nao chega onde foi pedida. Nao muda nada.

    Contrato de 3 de outubro, pontos 2 e 3:
      - com clip.x1, uma legenda que nao cabe numa linha na largura util parte-se como hoje, e diz-se
        quanto precisa e quanto ha (legenda_numa_linha());
      - a posicao de todas mais a do clip fora de POSICAO_DX e POSICAO_DY fica no limite;
      - o bloco das linhas nunca sai da largura util, e um dx que o levava para la encosta a margem.
    `clips` sao linhas do CSV, com tipo, ordem, texto_ecra, textos_fotos, textos_opcoes e opcoes_clip.
    Cada aviso diz o clip ("clip N"), que o montar renumera para o numero da Mesa.
    """
    avisos = []
    pos = _ESTILO.get("legenda", {}).get("posicao") or {}
    for c in clips:
        mostrados = legendas_do_clip(c)
        if not mostrados:
            continue
        o = ler_opcoes_clip(c.get(COLUNA_OPCOES_CLIP))
        uma = bool(o and o["x1"])
        quem = "a legenda do clip %s" % c.get("ordem")
        if uma:
            for t, tam in mostrados:
                cabe, precisa, ha = legenda_numa_linha(t, tam)
                if not cabe:
                    avisos.append("%s nao cabe numa linha: precisa de %d px e ha %d px; parte-se como hoje (%s)"
                                  % (quem, precisa, ha, " ".join(t.split())))
        if o and o["lp"] != (0, 0):
            pedido = (pos.get("dx", 0) + o["lp"][0], pos.get("dy", 0) + o["lp"][1])
            fica = posicao_da_legenda(o)[:2]
            if pedido != fica:
                avisos.append("%s pede a posicao dx %d, dy %d (a de todas mais a do clip), fora de %d a %d e de "
                              "%d a %d: fica dx %d, dy %d"
                              % (quem, pedido[0], pedido[1], POSICAO_DX[0], POSICAO_DX[1], POSICAO_DY[0],
                                 POSICAO_DY[1], fica[0], fica[1]))
        dx, _dy, alinhamento = posicao_da_legenda(o)
        if dx == 0:
            continue
        for t, tam in mostrados:
            _tam, linhas, fonte = linhas_legenda(t, tam, uma_linha=uma)
            d = ImageDraw.Draw(Image.new("L", (1, 1)))
            anda = dx_efetivo([texto_emojis.caixa(x, fonte, desenho=d)[2] for x in linhas], dx, alinhamento)
            if abs(anda - dx) >= 1:
                avisos.append("%s encosta a margem: anda %d px dos %d pedidos, para nao sair da largura util (%s)"
                              % (quem, int(round(anda)), dx, " ".join(t.split())))
                break
    return avisos


def _fonte(tamanho):
    if tamanho not in _FONTES:
        _FONTES[tamanho] = letra("legenda", tamanho)
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
    # O TAMANHO DE OMISSAO E O DA LEGENDA DO ESTILO DA MESA (2 de outubro): um grupo sem tt
    # escreve com a letra da legenda. Sem estilo e o TEXTO_FOTO_TAMANHO de sempre.
    opcoes["tamanho"] = texto_foto_tamanho()
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
                      % (v, TEXTO_FOTO_TAMANHOS[0], TEXTO_FOTO_TAMANHOS[1], opcoes["tamanho"]))
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
    tamanho = texto_foto_tamanho() if tamanho is None else tamanho
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
                and all(texto_emojis.caixa(l, fonte, desenho=d)[2] <= cabe for l in linhas)):
            return tamanho, linhas, False
        if tamanho <= pequeno:
            break
        tamanho = max(pequeno, tamanho - 2)
    if len(linhas) > TEXTO_FOTO_LINHAS:
        linhas = linhas[:TEXTO_FOTO_LINHAS - 1] + [" ".join(linhas[TEXTO_FOTO_LINHAS - 1:])]
    cortado = False
    for i, linha in enumerate(linhas):
        if texto_emojis.caixa(linha, fonte, desenho=d)[2] <= cabe:
            continue
        while linha and texto_emojis.caixa(linha.rstrip() + RETICENCIAS, fonte, desenho=d)[2] > cabe:
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
                     (0, 0, 0, fundo_da_legenda(TEXTO_FOTO_ALFA)))
    d = ImageDraw.Draw(capa)
    cor = legenda_cor() + (255,)
    for i, linha in enumerate(linhas):
        # um emoji a cores, na letra de emojis, ao centro com o resto (texto_emojis)
        texto_emojis.escrever(d, (largura / 2.0, almofada + (i + 0.5) * alt_linha), linha, fonte, cor,
                              anchor="mm")
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
#
# 28 DE SETEMBRO, decisao 087: a colagem sobe a 20 e a pilha a 40. O Tiago: "sobe o limite
# para 20 e para a pilha mete tambem o maximo que der, pois a pilha e um registo
# interessante". Medido antes de subir:
#   colagem  270 disposicoes de 13 a 20 fotos, filas e espalhada, com e sem legenda: nenhuma
#            sai do ecra nem pisa miolo, cada foto fica pelo menos 81% a vista; a mais
#            pequena desce a cerca de 0,8% do ecra, na ordem do pior caso aceite para 12. O
#            colagem_particoes() so vai ate 24 (4 filas de 6), e por isso 20 tem folga.
#   pilha    o monte nao parte com nenhum numero; o que trava e o leque, que a partir de
#            ~20 ocupa a largura toda e encolhe as fotos (desenhado a serio, so ate 24, ver
#            PILHA_LEQUE_MAX). E a memoria: cada fatia abria as fotos todas em resolucao
#            total, e uma pilha de 40 fotos de 5 MP pedia cerca de 850 MB por processo, 6 GB
#            com as 7 fatias.
# 1 DE OUTUBRO: o preparar() ja nao abre as fotos todas, abre uma de cada vez (ver FotoPorAbrir),
# e o aviso do main() conta os pixeis verdadeiros, ver aviso_de_memoria().
#
# 1 DE OUTUBRO, decisao 102: a pilha sobe a 60, so em monte; o leque fica em 24. O Tiago: "A
# pilha: ate 60 fotos em monte, depois da correcao de memoria." Medido antes de subir:
#   o monte desenhado ate 80 fica sempre dentro do quadro e a foto de cima com 10 a 31% do
#   ecra; mais fotos so alongam o clip. O travao era a memoria. Com a abertura uma a uma, o
#   pico de uma fatia (preparar e desenhar os seus fotogramas) com 60 fotos da FINAIS foi de
#   247 MB sem textos, 404 MB com um texto em cada foto e 395 MB com as 60 maiores, a de 48
#   MP incluida: 2,8 GB com 7 fatias no pior caso. O aviso_de_memoria() conta por cima, e com
#   textos ja propoe menos fatias. A camada das pousadas passou a incremental, ver
#   camada_das_pousadas(): refeita do zero eram cerca de 3245 composicoes por fatia.
#   O PRECO: com 60 fotos e encadeados de 0,7 s a minima e de 32,7 s, e cada foto fica 0,5 s,
#   um relance como na rajada; um texto em cada foto nao se le (LEGENDA_MINIMO_S), e a Mesa
#   avisa. Medido a 1 de outubro.
#
# 1 DE OUTUBRO, decisao 102: a colagem sobe a 30, em filas e espalhada. O Tiago: "A colagem: ate
# 30 fotos." Medido antes de subir, com as proporcoes do inventario e da FINAIS: de 25 a 30, com
# as filas novas de colagem_particoes() (4 a COLAGEM_MAIS_LINHAS filas de ate
# COLAGEM_MAIS_POR_LINHA) e so as particoes em que o colagem_afastar() assentou (acima de 20, ver
# COLAGEM_SO_ASSENTADAS_ACIMA), nenhuma foto sai
# do ecra nem pisa o miolo de outra, e a mais pequena fica como com 20 (mediana de 1,0 a 1,2% do
# ecra, 12 em 30 casos abaixo de 100 px de lado). A 36 e a 40 cai para 0,7 a 0,8% e 23 em 30
# abaixo de 100 px: a 15 metros as fotos de grupo passam a textura, e por isso fica nos 30.
# Antes disto uma colagem de 25 em filas rebentava com ValueError e parava o render.
LIMITES_MONTE = {"colagem": (2, 30), "pilha": (2, 60)}
# O LIMITE DE UM ESTILO, quando nao e o do tipo. O mergulho na grelha (decisao 101) e um estilo da
# colagem, mas a grelha aguenta mais do que as filas: ate 36, decisao 102, medido a 1 de outubro
# (36 fotos dao uma grelha de 6 por 6 com celulas de 311 por 171 px). Os mesmos numeros estao no
# montar_da_mesa.LIMITES_ESTILO e no GRUPOS_ESTILO da Mesa, e o teste_limites_dos_grupos_iguais le
# os tres. Quem pergunta pelo limite de um grupo passa por limites_do_grupo().
LIMITES_ESTILO = {("colagem", "mergulho"): (2, 36)}


def limites_do_grupo(tipo, estilo=None):
    """(minimo, maximo) de fotos de um grupo deste tipo, no estilo da coluna tratamento.

    O do estilo em LIMITES_ESTILO se o houver, senao o do tipo em LIMITES_MONTE. Um estilo
    desconhecido, o "fiel" das montagens de antes ou nenhum dao o do tipo, que e o da omissao.
    """
    return LIMITES_ESTILO.get((tipo, (estilo or "").strip()), LIMITES_MONTE[tipo])


MONTE_ATRASO = 0.35              # a primeira espera o encadeado, como no lado a lado
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
COLAGEM_MAIS_LINHAS = 6           # acima de 24 (4 x 6), de 4 ate 6 filas equilibradas...
COLAGEM_MAIS_POR_LINHA = 10       # ...de ate 10 fotos cada, ver colagem_particoes()
# Acima disto a colagem_disposicao() so escolhe entre as particoes que assentaram. E o limite da
# colagem ate 1 de outubro: de 2 a 20 as disposicoes ficam iguais ao byte as de antes, e de 21
# para cima nenhuma colagem podia ter ido ao filme. Ver colagem_disposicao().
COLAGEM_SO_ASSENTADAS_ACIMA = 20


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

    ACIMA DE COLAGEM_MUITAS_LINHAS x COLAGEM_MUITAS_POR_LINHA (24), MAIS FILAS. Ate 24 tudo fica
    como estava, ao byte. Com 25 ou mais nao havia particao nenhuma, e o colagem_disposicao()
    rebentava com ValueError (o max de uma lista vazia) e parava o render. Agora, como acima, so
    filas equilibradas, de COLAGEM_MUITAS_LINHAS ate COLAGEM_MAIS_LINHAS filas de ate
    COLAGEM_MAIS_POR_LINHA fotos: com 30, 8877, 7887 e as outras de 4 filas, 66666 e as de 6 filas.
    Medido a 1 de outubro de 25 a 30 com proporcoes reais: as fotos ficam do tamanho das de 20.
    Para nunca voltar a nao haver particao nenhuma, com mais fotos do que COLAGEM_MAIS_LINHAS x
    COLAGEM_MAIS_POR_LINHA (60, que nenhum limite deixa chegar) ha uma so, com as filas que forem
    precisas e as fotos a mais nas de cima.
    """
    teto = COLAGEM_MUITAS_LINHAS * COLAGEM_MUITAS_POR_LINHA
    if n > teto:
        for filas in range(COLAGEM_MUITAS_LINHAS, COLAGEM_MAIS_LINHAS + 1):
            base, resto = divmod(n, filas)
            if base + (1 if resto else 0) > COLAGEM_MAIS_POR_LINHA:
                continue
            for mais in itertools.combinations(range(filas), resto):
                linhas, k = [], 0
                for f in range(filas):
                    conta = base + (1 if f in mais else 0)
                    linhas.append(list(range(k, k + conta)))
                    k += conta
                yield linhas
        if n > COLAGEM_MAIS_LINHAS * COLAGEM_MAIS_POR_LINHA:
            filas = -(-n // COLAGEM_MAIS_POR_LINHA)
            base, resto = divmod(n, filas)
            linhas, k = [], 0
            for f in range(filas):
                conta = base + (1 if f < resto else 0)
                linhas.append(list(range(k, k + conta)))
                k += conta
            yield linhas
        return
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


# ATE ONDE AS FOTOS DE UM GRUPO DESCEM, com legenda: nunca acima de metade do ecra, mesmo com uma
# legenda alta (quatro linhas a 90). COM A LEGENDA SUBIDA (3 de outubro) a metade sobe com ela, porque
# as fotos continuam acima da legenda onde quer que ela esteja, mas nunca acima de um quarto do ecra:
# abaixo disso nao ha onde as pousar. O `piso` e o que o preparar_monte() conta; sem ele e a metade.
PISO_MINIMO_DA_LEGENDA = 0.25


def piso_da_legenda(piso=None):
    """A linha do ecra acima da qual a legenda nunca empurra as fotos de um grupo: 0,5 A, ou o `piso`."""
    return 0.5 * A if piso is None else max(PISO_MINIMO_DA_LEGENDA * A, piso)


def colagem_disposicao(aspetos, focos=None, livre_ate=None, piso=None):
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
    baixo = A - my if livre_ate is None else max(piso_da_legenda(piso), min(A - my, livre_ate))
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
        fotos, assentou = _colagem_assentar(aspetos, focos, linhas, alturas, (mx, my, g, alt_util, baixo))
        areas = [f[2] * f[3] for f in fotos]
        opcoes.append((sum(areas), min(areas), fotos, assentou))
    # ACIMA DE 20 FOTOS, SO AS PARTICOES QUE ASSENTARAM. Com as filas novas de
    # colagem_particoes() a escolha de sempre ficava por vezes com uma em que o colagem_afastar()
    # nao chegou a parar de empurrar em dez voltas, e ai a garantia do miolo nao vale: medido a 1
    # de outubro, 6 em 30 colagens de 30 com proporcoes reais tinham a foto 25 ou a 20 a entrar
    # 4 a 13 px no miolo da 18 ou da 13. So com as que assentaram, 0 em 30 a 25, a 30, a 36 e a 40.
    # De 21 a 24 as particoes sao as de sempre, mas so passaram a poder ir ao filme com o limite
    # a 30, e acontece o mesmo: na revisao de 1 de outubro, 3 em 256 colagens de 21 e 22 com
    # proporcoes reais pisavam um miolo 1,1 a 1,6 px, e com o filtro nenhuma, com a foto mais
    # pequena quase igual. Ate COLAGEM_SO_ASSENTADAS_ACIMA fica como estava, com todas, para as
    # disposicoes de antes sairem iguais ao byte; e se nenhuma assentar fica a escolha de sempre
    # entre todas, que e melhor do que nada.
    if n > COLAGEM_SO_ASSENTADAS_ACIMA:
        opcoes = [o for o in opcoes if o[3]] or opcoes
    # Uma foto minuscula ao lado de uma enorme nao e colagem, e engano: das que dao quase
    # tanta area como a melhor, fica a de maior foto mais pequena.
    # Mas nao a troco de nada: o maximo estrito da mais pequena chegava a abdicar de 5 a
    # 10% da area para a mais pequena crescer 0,5%. Dentro da banda, ficam as que chegam a
    # COLAGEM_MENOR_BANDA da melhor foto mais pequena, e dessas a de maior area.
    topo = max(o[0] for o in opcoes)
    banda = [o for o in opcoes if o[0] >= COLAGEM_TOLERANCIA * topo - 1e-6]
    melhor_menor = max(o[1] for o in banda)
    finalistas = [o for o in banda if o[1] >= COLAGEM_MENOR_BANDA * melhor_menor - 1e-9]
    return max(finalistas, key=lambda o: o[0])[2]


def _colagem_assentar(aspetos, focos, linhas, alturas, medidas):
    """Uma particao da colagem ja assente: empurrada para nao tapar caras e encaixada no ecra.

    Devolve (fotos, assentou): assentou e o que o colagem_afastar() devolve, True quando a
    ultima volta ja nao empurrou ninguem, que e quando a garantia do miolo vale.
    """
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
    assentou = colagem_afastar(fotos, focos, (mx, my, L - mx, baixo))
    return fotos, assentou


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
# DE 13 A 30 (decisoes 087 e 102) sao as mesmas contas, sem nada de novo. Medido a 1 de outubro em
# 48 espalhadas de 25 a 30 com proporcoes do inventario, com e sem legenda e foco: nenhuma fora do
# ecra, nenhum miolo pisado, a mais pequena com pelo menos 0,56% do ecra, e cerca de 11 s de CPU por
# disposicao (ate 17 s), que cada fatia faz ao preparar o clip. Nenhuma passa no espalhada_preferida():
# com tantas fotos le-se como filas desencontradas, e nao como uma colagem solta.
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


def colagem_espalhada(aspetos, focos=None, livre_ate=None, piso=None):
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
    baixo = A - my if livre_ate is None else max(piso_da_legenda(piso), min(A - my, livre_ate))
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
        return colagem_disposicao(aspetos, focos, livre_ate, **({} if piso is None else {"piso": piso}))
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
# O LEQUE SO ATE 24 FOTOS, decisao 087. A pilha vai ate 60 (decisao 102), mas so em monte,
# onde as de baixo ficam tapadas de proposito. No leque cada foto de baixo tem de ficar com
# PILHA_LEQUE_VE a vista no fim, e desenhado a serio (e nao so pela geometria, que dizia 23% a
# 40) isso cumpre-se em todas as formas ate 24 e falha a partir de 25 (17,8% com fotos
# misturadas) e a 40 (16,6%): a moldura de 6 pixeis e o esbatido comem a tira de fora quando as
# fotos encolhem. Medido a 28 de setembro e confirmado desenhado a 1 de outubro; o
# montar_da_mesa.py poe em monte um leque com mais do que isto, e diz-lo.
PILHA_LEQUE_MAX = 24


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


def pilha_leque(aspetos, livre_ate=None, piso=None):
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
    baixo = A - b if livre_ate is None else max(piso_da_legenda(piso), min(A - b, livre_ate))
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


def pilha_disposicao(aspetos, livre_ate=None, piso=None):
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
    baixo = A - b if livre_ate is None else max(piso_da_legenda(piso), min(A - b, livre_ate))
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
    letras = max([texto_emojis.caixa(l, _fonte(tam), desenho=d)[2] for l in linhas] or [1])
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


# ---------------------------------------------------------------- as fotos de um grupo
# UMA FOTO ABERTA DE CADA VEZ (1 de outubro). O preparar() abria as fotos todas de uma colagem
# ou pilha em resolucao total antes de fazer os sprites, e as 7 fatias preparam o mesmo clip ao
# mesmo tempo. No render da madrugada de 1 de outubro a pilha de 15 levou cada fatia de 310 para
# 910 MB e deixou o PC com 84 MB livres; com as 40 maiores fotos da FINAIS seriam cerca de
# 3,6 GB por fatia. O preparar_monte() so precisa do tamanho de todas para as dispor e de cada
# uma aberta para lhe fazer os sprites: o tamanho le-se do cabecalho, e cada foto abre-se na sua
# vez e sai antes de a seguinte abrir. Os sprites sao os mesmos, ao byte.
ORIENTACAO_EXIF = 0x0112                 # a etiqueta que o ImageOps.exif_transpose() le
ORIENTACOES_DE_LADO = (5, 6, 7, 8)       # as que rodam um quarto de volta e trocam largura e altura


def tamanho_da_foto(caminho):
    """(largura, altura) da foto como o render a abre, lidas do cabecalho, sem a descodificar.

    E o tamanho DEPOIS do exif_transpose(): as orientacoes 5 a 8 rodam a foto um quarto de
    volta. A orientacao le-se como ele a le, pelo getexif(); num PNG sem EXIF no cabecalho
    isso descodifica a foto, e na FINAIS ha um.

    A TIFF JA VEM RODADA (1 de outubro). Na Pillow 12.3 o TiffImageFile._setup() ja da o
    tamanho de pe quando a orientacao e 5 a 8, e o load() roda os pixeis; trocar outra vez
    dispunha uma TIFF de 1200x800 com a orientacao 6 como deitada, e o sprite_monte() esticava
    a foto de pe para esse lugar. Hoje nao ha nenhuma TIFF na FINAIS, mas o inventario.py
    aceita-as e o consolidar.py copia o original tal como esta.
    """
    with Image.open(caminho) as im:
        w, h = im.size
        if im.format == "TIFF":
            return (w, h)
        orientacao = im.getexif().get(ORIENTACAO_EXIF, 1)
    return (h, w) if orientacao in ORIENTACOES_DE_LADO else (w, h)


def abrir_foto(caminho):
    """A foto de pe e em RGB, com os pixeis do ImageOps.exif_transpose(Image.open(c)).convert("RGB").

    SEM AS DUAS COPIAS DE ANTES. O exif_transpose() de omissao devolve uma copia mesmo quando
    nao roda nada, e o convert("RGB") de uma foto que ja e RGB outra: no instante de abrir uma
    foto de 48 MP havia 384 MB dela em memoria em vez de 192, em cada fatia. Aqui roda-se no
    sitio e so se converte o que nao e RGB, como a foto RGBA da FINAIS. Os pixeis sao os
    mesmos, ao byte, nas 719 fotos da FINAIS (1 de outubro).
    """
    im = Image.open(caminho)
    ImageOps.exif_transpose(im, in_place=True)
    if im.mode != "RGB":
        im = im.convert("RGB")
    return im


class FotoPorAbrir:
    """Uma foto de um grupo que so se abre quando lhe chega a vez: o tamanho vem do cabecalho.

    Tem o width e o height de uma imagem aberta, que e tudo o que o preparar_monte() e o
    preparar_mergulho() usam antes de fazer os sprites, e abre-se com aberta().
    """

    def __init__(self, caminho):
        self.caminho = caminho
        self.width, self.height = tamanho_da_foto(caminho)
        self.size = (self.width, self.height)

    def abrir(self):
        im = abrir_foto(self.caminho)
        if im.size != self.size:
            # Nao acontece em nenhuma foto da FINAIS. Se acontecer, o grupo foi disposto com a
            # forma do cabecalho e esta foto sai esticada: diz-se, nao se corrige sozinho.
            print("  AVISO: a foto %s abriu com %dx%d e o cabecalho dizia %dx%d; no grupo sai "
                  "esticada" % (os.path.basename(self.caminho), im.width, im.height,
                                self.width, self.height))
        return im


def aberta(foto):
    """A imagem aberta: uma FotoPorAbrir abre-se agora, uma imagem ja aberta passa como esta."""
    return foto.abrir() if isinstance(foto, FotoPorAbrir) else foto


# O AVISO DE MEMORIA DO main() CONTA OS PIXEIS VERDADEIROS (1 de outubro). Contava 0,021 GB por
# foto, que sao 5 MP, e so disparava acima de 20 fotos; as fotos da FINAIS tem em media 7 MP e
# ate 48, e a pilha de 15 da madrugada de 1 de outubro, com 519 MB de fotos, nao disparou nada.
# Com a abertura uma a uma, o que cada fatia chega a ter de um grupo e a maior foto aberta, os
# sprites que ficam e os ecras inteiros do desenho; medido com fotos reais, ver memoria_do_grupo().
MEMORIA_POR_PIXEL = 4                    # a Pillow guarda uma foto RGB em 4 bytes por pixel
ORIENTACOES_QUE_RODAM = (2, 3, 4, 5, 6, 7, 8)   # as que o exif_transpose() vira ou roda
MEMORIA_SPRITE = 3.5e6                   # um sprite de pilha: medidos 2,8 a 3,3 MB em media
MEMORIA_ECRAS = 4                        # o fundo, a camada, a de baixo e a tela do fotograma
# O LIMITE DO AVISO, somado nas fatias. A pilha de 15 juntou 3,6 GB as 7 fatias e deixou o PC
# com 84 MB livres: 3 GB deixa margem. E o nivel a que o aviso de antes disparava com 7 fatias,
# 20 fotos x 0,021 GB x 7 = 2,9 GB.
MEMORIA_AVISO = 3.0e9


def memoria_ao_abrir(caminho):
    """Bytes que a foto chega a ter em memoria no abrir_foto(): ela, mais a copia se a roda ou converte.

    Rodar no sitio ainda faz uma copia, e converter tambem: uma foto de 48 MP com a orientacao
    6 chega a 384 MB no instante de abrir, e de pe so a 192 (medido a 1 de outubro). Pelo
    cabecalho, sem a descodificar.
    """
    with Image.open(caminho) as im:
        w, h = im.size
        copia = im.getexif().get(ORIENTACAO_EXIF, 1) in ORIENTACOES_QUE_RODAM or im.mode != "RGB"
    return MEMORIA_POR_PIXEL * w * h * (2 if copia else 1)


def memoria_do_grupo(clip):
    """Os bytes que preparar e desenhar este grupo chegam a pedir a cada fatia.

    A maior foto aberta, que e a unica em resolucao total de cada vez; os sprites que ficam,
    um por foto e dois na pilha com o texto que some; e os ecras inteiros do desenho. Medido
    a 1 de outubro, so o preparar() com fotos reais: a pilha de 8 da v3 com a foto de 48 MP
    rodada 394 MB (a conta da 445), a de 15 com textos 165 MB (a conta da 187), 40 sorteadas
    da FINAIS com textos 333 MB (a conta da 441) e as 40 maiores 396 MB (a conta da 557). A
    conta fica por cima de proposito: a maior pode abrir depois de os sprites estarem feitos.
    """
    aberta, fica = memoria_do_grupo_em_partes(clip)
    return aberta + fica


def memoria_do_grupo_em_partes(clip):
    """(a maior foto aberta, o que fica preparado): as duas partes de memoria_do_grupo(), em bytes.

    O que fica sao os sprites e os ecras inteiros, que vivem no pronto do grupo enquanto ele
    nao sai da fatia; a foto aberta so existe enquanto se prepara. Sem fotos que abram, (0, 0).
    """
    caminhos = [c for c in (clip.get("_caminhos") or []) if c and os.path.exists(c)]
    ao_abrir = []
    for c in caminhos:
        try:
            ao_abrir.append(memoria_ao_abrir(c))
        except OSError:
            pass        # uma foto que nao abre fica para o preparar(), como sempre: o aviso nao para nada
    if not ao_abrir:
        return 0, 0
    textos = ler_textos_fotos(clip.get("textos_fotos"))
    opcoes = ler_textos_opcoes(clip.get("textos_opcoes"))
    dois = (clip.get("tipo") == "pilha" and textos is not None and opcoes["modo"] != "legenda"
            and opcoes["tapadas"] == "some")
    return (max(ao_abrir),
            len(caminhos) * (2 if dois else 1) * MEMORIA_SPRITE + MEMORIA_ECRAS * MEMORIA_POR_PIXEL * L * A)


def _segundos_ou_nada(valor):
    """O valor de uma coluna de segundos como float, ou None se estiver vazio ou nao for numero."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def aviso_de_memoria(clips, fatias):
    """O aviso do main() se o grupo mais pesado, com estas fatias, passa de MEMORIA_AVISO; senao None.

    As fatias preparam o mesmo clip ao mesmo tempo, e por isso o pico soma-se nelas. Diz-se
    antes de comecar, com o remedio, e nao se muda nada sozinho: uma fatia que morre por falta
    de memoria para o render inteiro a meio, e uma maquina a paginar fica muito mais lenta.

    DOIS GRUPOS SEGUIDOS SOMAM-SE (revisao de 1 de outubro). Numa fatia o pronto de um grupo so
    sai no libertar_prontos() do primeiro bloco de LIMPEZA_A_CADA fotogramas em que ja nao esta
    ativo, ate 8 s depois de acabar: um grupo que comece antes disso prepara-se e desenha-se com
    os sprites e os ecras do anterior ainda em memoria. Medido com duas pilhas de 60 seguidas,
    sem textos: 256 MB por fatia so com a primeira e 492 MB com as duas, 3,44 GB com 7 fatias,
    e o aviso, que contava cada grupo sozinho, calava-se nos 2,6 GB. Conta-se por isso, a cada
    grupo, o que fica dos que comecaram antes e podem ainda nao ter saido, por cima como o
    resto da conta: a limpeza pode calhar mais cedo (a v3 tem duas pilhas seguidas, a 139 e a
    140, e com elas a conta passa de 3,1 para 3,5 GB com 7 fatias; continua a propor 6). Sem
    inicio_s e fim_s, um grupo conta sozinho.
    """
    grupos = []
    for c in clips:
        if c.get("tipo") not in LIMITES_MONTE:
            continue
        aberta, fica = memoria_do_grupo_em_partes(c)
        grupos.append({"clip": c, "pede": aberta + fica, "fica": fica,
                       "inicio": _segundos_ou_nada(c.get("inicio_s")), "fim": _segundos_ou_nada(c.get("fim_s"))})
    if not grupos:
        return None
    sai_depois = LIMPEZA_A_CADA / float(FPS)
    pico, grupo, antes = 0, None, []
    for g in grupos:
        presos = [o for o in grupos if o is not g and None not in (g["inicio"], o["inicio"], o["fim"])
                  and o["inicio"] < g["inicio"] < o["fim"] + sai_depois]
        pede = g["pede"] + sum(o["fica"] for o in presos)
        if grupo is None or pede > pico:
            pico, grupo, antes = pede, g, presos
    if pico * fatias <= MEMORIA_AVISO:
        return None
    clip = grupo["clip"]
    onde = "" if grupo["inicio"] is None else " aos %d:%02d" % (int(grupo["inicio"]) // 60, int(grupo["inicio"]) % 60)
    if len(antes) == 1:
        junto = (", com a %s de %d fotos de antes ainda em memoria,"
                 % (antes[0]["clip"].get("tipo"), len(antes[0]["clip"].get("_caminhos") or [])))
    elif antes:
        junto = ", com %d grupos de antes ainda em memoria," % len(antes)
    else:
        junto = ""
    return ("  ATENCAO: a %s de %d fotos%s%s pede ate %s GB a cada fatia, %s GB com %d fatias, "
            "acima dos %s GB de folga (no render de 1 de outubro, 3,6 GB a mais deixaram o PC "
            "com 84 MB livres). Se tiver pouca memoria livre, corre com --fatias %d."
            % (clip.get("tipo"), len(clip.get("_caminhos") or []), onde, junto,
               ("%.2f" % (pico / 1e9)).replace(".", ","), ("%.1f" % (pico * fatias / 1e9)).replace(".", ","),
               fatias, ("%.0f" % (MEMORIA_AVISO / 1e9)), max(1, int(MEMORIA_AVISO // pico))))


def preparar_monte(tipo, imagens, focos, texto, cross_entra=0.0, cross_sai=None, estilo=None,
                   textos=None, opcoes=None, duracao=None, clip_leg=None):
    """Colagem ou pilha, a partir das imagens, abertas ou por abrir (FotoPorAbrir).

    `cross_entra` e o encadeado com o clip de antes e `cross_sai` o do seguinte; sem
    este, conta o mesmo que o de entrada. Ver agenda_monte(). `estilo` e o da coluna
    tratamento, ver ESTILOS_MONTE: so muda onde as fotos pousam, a agenda, a chegada,
    a respiracao e o recuo sao os mesmos. `textos` e um por foto, ver textos_do_grupo():
    cada um vai numa faixa dentro da sua foto, com o tamanho contado na foto pousada, ou,
    com a opcao legenda, na faixa de baixo do ecra, ver legenda_por_foto(). `opcoes` sao as
    de ler_textos_opcoes() e `duracao` a do clip, so para os avisos da opcao legenda.
    Nao mexe em onde as fotos pousam. `clip_leg` sao as opcoes do clip, de ler_opcoes_clip():
    a legenda numa linha e o lp; com a legenda subida as fotos continuam acima dela.
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
        legenda = legenda_por_foto([t or grupo for t in textos], tamanho, clip_leg)
        if legenda is not None and duracao:
            tempos = tempos_legenda_grupo(tipo, len(imagens), duracao, cross_entra,
                                          cross_entra if cross_sai is None else cross_sai)
            for k, t, dura in legendas_curtas(legenda["textos"], tempos):
                avisar_legenda_curta(k, t, dura)
        textos = None
    capa = None if legenda is not None else faixa_texto(texto, clip_leg=clip_leg)
    # A LEGENDA DESENHA-SE POR CIMA, como nos outros tipos, mas as fotos pousam acima
    # dela. Nos fotogramas de controlo a faixa tapava a fila de baixo da colagem, e a
    # 15 metros uma cara meio escondida por uma faixa preta nao se le. Com a legenda subida
    # (3 de outubro) o piso sobe com ela, ver piso_da_legenda(); sem posicao fica a metade.
    # O piso so vai as disposicoes quando ha: sem posicao a chamada e a de sempre, com os argumentos
    # de sempre (ha testes que trocam uma disposicao por uma funcao de tres argumentos).
    _dx, dy_legenda, _alinhamento = posicao_da_legenda(clip_leg)
    com_piso = {} if dy_legenda == 0 else {"piso": 0.5 * A + dy_legenda}
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
            lugares = colagem_espalhada(aspetos, focos, livre_ate, **com_piso)
        else:
            lugares = colagem_disposicao(aspetos, focos, livre_ate, **com_piso)
        cresce = 1.0 + COLAGEM_RESPIRA      # no fim, a respirar, fica a 1:1
        fundo = None                        # a primeira foto desfocada, feita no ciclo com ela aberta
    else:
        if estilo == "leque":
            lugares = pilha_leque(aspetos, livre_ate, **com_piso)
        else:
            lugares = pilha_disposicao(aspetos, livre_ate, **com_piso)
        cresce = 1.0                        # a pilha so recua, nunca cresce
        fundo = Image.new("RGB", (L, A), (10, 10, 12))
    fotos = []
    for k, (foto, (cx, cy, w, h, ang)) in enumerate(zip(imagens, lugares)):
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
        # A FOTO SO ABRE AQUI, para os seus dois sprites, e sai antes de a seguinte abrir: ver
        # FotoPorAbrir. O fundo da colagem e a primeira desfocada, e faz-se com ela aberta.
        im = aberta(foto)
        if fundo is None:
            fundo = cobrir(im, max(1, L // 4), max(1, A // 4))
            fundo = fundo.filter(ImageFilter.GaussianBlur(15)).resize((L, A), Image.BICUBIC)
            fundo = Image.blend(Image.new("RGB", (L, A), (8, 8, 10)), fundo, 0.28)
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
        im = None
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


def camada_das_pousadas(pronto, pousadas, t_rel, duracao, inicios, entrada):
    """O fundo com as fotos pousadas por cima, pela ordem: ao byte, o mesmo que compo-las todas de novo.

    PORQUE (1 de outubro): a camada das pousadas refazia-se do zero cada vez que mais uma
    pousava, n(n+1)/2 composicoes por fatia, e com textos e o "some" ainda mais, porque a
    chave muda durante o desvanecer. Numa pilha de 60 com textos eram cerca de 3245
    composicoes por fatia, de 4 a 18 minutos com a maquina carregada (estimativa da
    verificacao de 1 de outubro). Agora guarda-se tambem a camada DE BAIXO, com as pousadas
    que ja nao mudam, e cada camada nova e essa mais as de cima: uma composicao por foto.

    O QUE JA NAO MUDA: uma pousada cujo sprite ja e o do fim, o de sempre, ou com o "some" o
    sem texto. Uma pousada com outra pousada por cima esta sempre assim, que o texto dela
    acabou de desaparecer antes de a seguinte pousar, ver alfa_texto_pilha(); a de cima so
    quando nao tem texto a desaparecer. Nao se presume: o sprite_no_instante() de cada uma
    tem de o dizer, e a primeira que ainda nao estiver no fim compoe-se de novo, com as de
    cima dela, em cada camada nova.

    A de baixo serve enquanto o tempo anda para a frente, com a mesma duracao e as mesmas
    fotos por baixo, que e como o render e cada fatia pedem os fotogramas: uma foto no fim
    fica no fim. Um fotograma para tras, ou outra duracao, refaz a de baixo a partir do
    fundo: da o mesmo, mais devagar. A composicao e sempre a mesma, as mesmas fotos pela
    mesma ordem sobre o mesmo fundo, so feita em dois tempos, e por isso os bytes sao os
    mesmos.
    """
    cresce = pronto["cresce"]
    dur = round(duracao, 4)
    baixo = pronto.get("_baixo")
    if (baixo is None or baixo["duracao"] != dur or t_rel < baixo["desde"]
            or baixo["fotos"] != [p[0] for p in pousadas[:len(baixo["fotos"])]]):
        baixo = {"duracao": dur, "desde": float("-inf"), "fotos": [], "tela": pronto["fundo"].copy()}
        pronto["_baixo"] = baixo
    while len(baixo["fotos"]) < len(pousadas):
        k, x, y, tam, alfa, _ = pousadas[len(baixo["fotos"])]
        sprite, texto = sprite_no_instante(pronto, k, t_rel, inicios, entrada)
        if texto not in (None, 0.0):
            break
        compor(baixo["tela"], sprite, x, y, tam / cresce, alfa)
        baixo["fotos"].append(k)
        baixo["desde"] = t_rel
    tela = baixo["tela"].copy()
    for k, x, y, tam, alfa, _ in pousadas[len(baixo["fotos"]):]:
        compor(tela, sprite_no_instante(pronto, k, t_rel, inicios, entrada)[0], x, y, tam / cresce, alfa)
    return tela


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
    # E a camada nova faz-se sobre a de baixo, sem recompor as de baixo, ver
    # camada_das_pousadas().
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
            pronto["_camada"] = (chave, camada_das_pousadas(pronto, poses[:assentes], t_rel, duracao,
                                                            inicios, entrada))
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


# ---------------------------------------------------------------- o mergulho na grelha
# 30 de setembro. O Tiago mandou um tutorial de Premiere em que uma grelha de 3 por 3 da
# lugar a uma so imagem: a camara mergulha numa das celulas ate ela encher o ecra. Aqui e
# um terceiro estilo da colagem, "mergulho": as fotos aparecem uma a uma em grelha, a
# grelha respira um pouco, e a camara mergulha na ULTIMA, que fica sozinha a encher o
# ecra antes do encadeado de saida. O clip seguinte entra a partir de uma foto inteira.
#
# A FOTO DO MERGULHO NAO E AMPLIADA A PARTIR DA GRELHA. A grelha desenha-se uma vez ao
# dobro do ecra e cada fotograma e uma so transformacao dela; a ultima foto e um sprite a
# parte, ja no tamanho com que acaba o mergulho, e compoe-se por cima da sua celula com a
# composicao de sub-pixel de sempre. No fim do mergulho e a foto verdadeira que esta no
# ecra, e nao uma celula esticada quatro vezes.
MERGULHO_ESTILO = "mergulho"
MERGULHO_FOLGA = 8          # linha preta entre as fotos, a do lado a lado
MERGULHO_ATRASO = 0.35      # a primeira espera que o encadeado de entrada acabe
MERGULHO_ENTRA = 0.35       # segundos que cada foto leva a aparecer
MERGULHO_ENTRE = 0.18       # atraso entre uma foto e a seguinte, ver mergulho_entre()
MERGULHO_ESPERA = 1.0       # a grelha inteira no ecra, antes de mergulhar
MERGULHO_DESCE = 1.2        # o mergulho na grelha de 3 por 3, ver mergulho_desce()
MERGULHO_FICA = 0.8         # a ultima sozinha, antes do encadeado de saida
MERGULHO_RESPIRA = 0.03     # o que a grelha aproxima enquanto espera
MERGULHO_FICA_ZOOM = 0.03   # o que a ultima aproxima depois do mergulho
MERGULHO_DOBRO = 2          # a grelha desenha-se a esta escala do ecra
# A CELULA TEM FORMATO DE FOTOGRAFIA (1 de outubro, decisao 102). A regra de 30 de setembro punha
# primeiro as celulas vazias, e todo o numero com poucos divisores dava tiras em pe: 5 fotos numa
# fila so de 374 x 1064 (0,35), 13 em 139 x 528 (0,26), 3, 7, 11, 14, 17, 19, 22, 23, 26 e 29 entre
# 0,26 e 0,59. Agora o formato da celula vem primeiro, entre MERGULHO_ASPETO_MIN e _MAX, e so depois
# as vazias, com a ultima fila centrada; por fim o mais perto de 3:2. O 9, o 12, o 16 e o 20 ficam
# como estavam. O TETO E 2,2 E NAO 2,1 por causa da legenda: com uma legenda de uma linha a grelha
# fica com 900 de altura, e com 2,1 o 9 passava a 4, 4 e 1 e o 4 a 3 e 1; com 2,2 ficam 3 por 3 e
# 2 por 2, com celulas de 2,17 e 2,16. Com 2 fotos nao ha nenhuma dentro e fica a menos fora, 2 por
# 1, de 0,89.
MERGULHO_ASPETO_MIN = 1.0
MERGULHO_ASPETO_MAX = 2.2
MERGULHO_ASPETO_ALVO = 1.5  # 3:2, o formato da maior parte das fotos
# A GRELHA ENCHE EM ATE 4 S (1 de outubro). Com os 0,18 s entre fotos de sempre, 36 levavam 6,7 s a
# aparecer. Ate 19 fotos fica como estava; acima o intervalo encolhe para a grelha encher em
# MERGULHO_ENCHE_MAX, contando a espera da primeira e a entrada da ultima: 0,174 s com 20 e 0,094 s
# com 36. Com 36 aparecem tres a quatro ao mesmo tempo, e ja nao e uma a uma.
MERGULHO_ENCHE_MAX = 4.0
# NADA ENCOLHE ABAIXO DE 40% do que devia. Quando o clip e curto encolhe por esta ordem: o encher, a
# espera, a ultima sozinha e so por fim o mergulho, que e o que se veio ver (1 de outubro; antes
# encolhia tudo por igual, o mergulho incluido).
MERGULHO_MINIMO = 0.4


def mergulho_grelha(n, larg, alt, folga=MERGULHO_FOLGA):
    """As celulas da grelha de n fotos: [(x, y, w, h)] em pixeis, pela ordem das fotos.

    `alt` e a altura que a grelha ocupa a partir do cimo do ecra: o ecra inteiro, ou ate a legenda
    do clip, ver mergulho_altura(). As colunas escolhem-se pela nota (fora, vazias, longe de 3:2):
    primeiro a celula dentro do formato de fotografia, MERGULHO_ASPETO_MIN a MERGULHO_ASPETO_MAX, ou
    a menos fora dele; depois as menos celulas vazias; depois a mais perto de 3:2. A ultima fila,
    se tiver menos fotos, fica centrada: uma celula preta vazia num canto lia-se como uma foto em
    falta. A Mesa tem a mesma conta, em grelhaMergulho().
    """
    melhor = None
    for cols in range(1, n + 1):
        filas = int(math.ceil(n / float(cols)))
        vazias = cols * filas - n
        cw = (larg - folga * (cols + 1)) / float(cols)
        ch = (alt - folga * (filas + 1)) / float(filas)
        aspeto = cw / ch
        fora = max(0.0, math.log(MERGULHO_ASPETO_MIN / aspeto), math.log(aspeto / MERGULHO_ASPETO_MAX))
        nota = (fora, vazias, abs(math.log(aspeto / MERGULHO_ASPETO_ALVO)))
        if melhor is None or nota < melhor[0]:
            melhor = (nota, cols, filas, cw, ch)
    _, cols, filas, cw, ch = melhor
    celulas = []
    for k in range(n):
        f, c = divmod(k, cols)
        na_fila = min(cols, n - f * cols)
        desvio = (cols - na_fila) * (cw + folga) / 2.0
        celulas.append((folga + c * (cw + folga) + desvio, folga + f * (ch + folga), cw, ch))
    return celulas


def mergulho_altura(capa):
    """A altura da grelha: o ecra inteiro, ou com legenda ate MONTE_LEGENDA_FOLGA acima da faixa dela.

    O LUGAR DA LEGENDA FICA LIVRE (1 de outubro), como na colagem em filas. A faixa de uma linha
    vai de 922 a 1047, com alfa 165, e com a grelha no ecra inteiro tapava 36% da ultima celula
    com 9 fotos, 48% com 20 e 73% com 36: justamente a foto onde se mergulha. Durante o mergulho a
    grelha desce para o lugar da legenda, e no fim a legenda fica por cima da ultima a encher o
    ecra, como numa foto sozinha. `capa` e a de faixa_texto(), ou None sem legenda.
    """
    if capa is None:
        return float(A)
    caixa = capa[1].getbbox()
    # Nunca abaixo de um quarto do ecra, como o piso dos outros grupos (3 de outubro): so uma legenda
    # subida com a posicao la chega; a mais alta de hoje, quatro linhas a 90, deixa 476 px.
    return float(max(PISO_MINIMO_DA_LEGENDA * A, caixa[1] - MONTE_LEGENDA_FOLGA * A)) if caixa else float(A)


def mergulho_cobre(celula):
    """Quanto a celula tem de crescer para cobrir o ecra: e a escala da camara no fim do mergulho."""
    _x, _y, w, h = celula
    return max(L / float(w), A / float(h))


# A VELOCIDADE DO MERGULHO E A DA GRELHA DE 3 POR 3 (1 de outubro). Numa grelha maior a celula e
# mais pequena e o zoom maior: em 1,2 s, o mergulho numa de 36 (6,3 vezes) parecia o dobro da
# velocidade do de 9 (3,1 vezes). Dura em proporcao ao logaritmo do zoom, que e o que o olho le
# numa escala geometrica: 1,74 s com 20 e 1,96 s com 36. Abaixo de 9 fica nos 1,2 s de sempre.
MERGULHO_COBRE_REF = mergulho_cobre(mergulho_grelha(9, L, A)[-1])


def mergulho_entre(n):
    """O intervalo entre uma foto e a seguinte: MERGULHO_ENTRE, ou menos para encher em MERGULHO_ENCHE_MAX."""
    if n < 2:
        return MERGULHO_ENTRE
    return min(MERGULHO_ENTRE, (MERGULHO_ENCHE_MAX - MERGULHO_ATRASO - MERGULHO_ENTRA) / float(n - 1))


def mergulho_desce(cobre):
    """Quanto dura o mergulho ate a celula cobrir o ecra, ver MERGULHO_COBRE_REF."""
    return MERGULHO_DESCE * max(1.0, math.log(cobre) / math.log(MERGULHO_COBRE_REF))


def _mergulho_partes(n, cobre):
    """O que cada parte pede, pela ordem em que encolhe: encher, espera, a ultima sozinha e o mergulho."""
    return [MERGULHO_ENTRA + mergulho_entre(n) * (n - 1), MERGULHO_ESPERA, MERGULHO_FICA,
            mergulho_desce(cobre or MERGULHO_COBRE_REF)]


def mergulho_tempos(n, duracao, entra=0.0, sai=0.0, cobre=None):
    """Os tempos do mergulho a caber na duracao, e os trocos em que a camara se move.

    Devolve {atraso, entra, entre, espera, desce, fica, trocos}: `entra` e o que cada foto leva a
    aparecer, `entre` o intervalo entre fotos, e `trocos` a lista [(nome, inicio, fim)] em segundos
    do clip: encher, espera, desce e fica. `cobre` e o da celula onde se mergulha, que da a duracao
    do mergulho (mergulho_desce); sem ele, o da grelha de 3 por 3.

    Com tempo a mais, a sobra vai para a espera, com a grelha inteira no ecra. Com tempo a menos
    encolhe primeiro o encher (a entrada e o intervalo pelo mesmo fator), depois a espera, depois a
    ultima sozinha e por fim o mergulho, cada um ate MERGULHO_MINIMO do que pedia. Abaixo disso o
    clip acaba antes de a camara parar, e e por isso que o montar_da_mesa.py e a Mesa avisam abaixo
    de duracao_minima_mergulho().
    """
    atraso = min(MERGULHO_ATRASO, max(entra, 0.0))
    partes = _mergulho_partes(n, cobre)
    livre = max(0.0, duracao - atraso - max(sai, 0.0))
    falta = sum(partes) - livre
    ficam = []
    for p in partes:
        tira = min(max(falta, 0.0), p * (1.0 - MERGULHO_MINIMO))
        ficam.append(p - tira)
        falta -= tira
    encher, espera, fica, desce = ficam
    f = encher / partes[0] if partes[0] else 1.0
    espera += max(0.0, -falta)
    entra_foto, entre = MERGULHO_ENTRA * f, mergulho_entre(n) * f
    todas = atraso + entra_foto + entre * (n - 1)
    comeca = todas + espera
    return {"atraso": atraso, "entra": entra_foto, "entre": entre, "espera": espera, "desce": desce,
            "fica": fica, "trocos": [("encher", 0.0, todas), ("espera", todas, comeca),
                                     ("desce", comeca, comeca + desce),
                                     ("fica", comeca + desce, comeca + desce + fica)]}


def duracao_mergulho(n, entra=0.0, sai=0.0, cobre=None):
    """A duracao em que nada encolhe nem sobra: a que a Mesa propoe ao juntar."""
    return min(MERGULHO_ATRASO, max(entra, 0.0)) + sum(_mergulho_partes(n, cobre)) + max(sai, 0.0)


def duracao_minima_mergulho(n, entra=0.0, sai=0.0, cobre=None):
    """Abaixo disto avisa-se: o encher e a espera ja estao no minimo, e o mergulho ou a ultima encolhem.

    Nao e a duracao_minima_monte() da colagem, que conta cada foto a entrar e a pousar com a sua
    pausa: num mergulho de 20 pedia 11,1 s, quando o mergulho cabe inteiro em 8,2 (1 de outubro).
    """
    encher, espera, fica, desce = _mergulho_partes(n, cobre)
    return (min(MERGULHO_ATRASO, max(entra, 0.0)) + MERGULHO_MINIMO * (encher + espera) + fica + desce
            + max(sai, 0.0))


def mergulho_do_texto(n, texto, clip_leg=None):
    """(altura da grelha, cobre da ultima) de um mergulho de n fotos com esta legenda, sem abrir fotos.

    Para quem precisa dos tempos antes do render, o montar_da_mesa.py: com legenda a grelha e mais
    baixa, a celula muda e o mergulho dura outro tanto. `clip_leg` sao as opcoes do clip.
    """
    alt = mergulho_altura(faixa_texto(texto, clip_leg=clip_leg))
    return alt, mergulho_cobre(mergulho_grelha(n, L, alt)[-1])


# A CAMARA PRESA A GRELHA (1 de outubro). A camara de 30 de setembro levava o centro da celula ao
# centro do ecra em linha reta enquanto a escala crescia em progressao geometrica, e a meio do
# mergulho saia da grelha: 80 pixeis seguidos de preto na borda direita com 9 fotos e 149 com 20.
# Agora a camara e uma VISTA, (x0, y0, s): o ecra mostra a regiao da grelha de (x0, y0) a
# (x0 + L/s, y0 + A/s), em pixeis do ecra a escala 1. Cada troco vai de uma vista a outra, e as do
# meio sao a mistura das duas com o mesmo peso na posicao e no tamanho, com o peso tirado da
# escala. Uma mistura de dois retangulos dentro da grelha fica dentro da grelha, por isso nenhum
# fotograma mostra o que esta fora dela. E o mesmo que um zoom com um ponto parado no ecra: a
# celula cresce do sitio onde esta ate encher o ecra. Com legenda, a grelha so desce para o lugar
# dela, que no inicio ja estava livre.
def mergulho_vista_cobre(celula):
    """A vista em que a celula cobre o ecra, centrada nela: a do fim do mergulho."""
    x, y, w, h = celula
    s = mergulho_cobre(celula)
    return (x + w / 2.0 - L / (2.0 * s), y + h / 2.0 - A / (2.0 * s), s)


def mergulho_vista_aproxima(vista, celula, fator):
    """A vista com mais `fator` de zoom, com o centro da celula parado no ecra."""
    x0, y0, s = vista
    x, y, w, h = celula
    px, py = x + w / 2.0, y + h / 2.0
    return (px - (px - x0) / fator, py - (py - y0) / fator, s * fator)


def mergulho_trocos(tempos, celula, k):
    """Os trocos da camara para um mergulho na celula k: [{de, ate, v0, v1, modo, celula}].

    A grelha respira em torno da celula, a camara mergulha da vista inteira para a vista em que
    ela cobre o ecra, e a foto continua a aproximar devagar. Mais do que um mergulho seria mais
    trocos nesta lista, com a sua celula cada um.
    """
    trocos = dict((nome, (de, ate)) for nome, de, ate in tempos["trocos"])
    inteira = (0.0, 0.0, 1.0)
    respira = mergulho_vista_aproxima(inteira, celula, 1.0 + MERGULHO_RESPIRA)
    cobre = mergulho_vista_cobre(celula)
    fim = mergulho_vista_aproxima(cobre, celula, 1.0 + MERGULHO_FICA_ZOOM)
    return [{"de": trocos["espera"][0], "ate": trocos["espera"][1], "v0": inteira, "v1": respira,
             "modo": "linear", "celula": k},
            {"de": trocos["desce"][0], "ate": trocos["desce"][1], "v0": respira, "v1": cobre,
             "modo": "suave", "celula": k},
            {"de": trocos["fica"][0], "ate": trocos["fica"][1], "v0": cobre, "v1": fim,
             "modo": "linear", "celula": k}]


def mergulho_vista_no_troco(troco, t):
    """A vista (x0, y0, s) da camara no instante t, dentro do troco ou segura nas pontas dele."""
    de, ate = troco["de"], troco["ate"]
    p = min(1.0, max(0.0, (t - de) / (ate - de))) if ate > de else float(t >= de)
    v0, v1 = troco["v0"], troco["v1"]
    s0, s1 = v0[2], v1[2]
    if troco["modo"] == "suave":
        # Em escala geometrica: um zoom de 1 a 4 que anda em linha reta parece acelerar no fim.
        s = s0 * math.exp(suave(p) * math.log(s1 / s0))
    else:
        s = s0 + (s1 - s0) * p
    w0, w1 = L / s0, L / s1
    # o peso de v0 tirado da largura da vista; sem mudar de escala, anda com o tempo
    peso = (L / s - w1) / (w0 - w1) if abs(w0 - w1) > 1e-9 else 1.0 - p
    return (v1[0] + (v0[0] - v1[0]) * peso, v1[1] + (v0[1] - v1[1]) * peso, s)


def mergulho_camara(pronto, t):
    """A vista (x0, y0, s) da camara no instante t, e a celula do troco em que esta.

    Antes do primeiro troco a camara esta na vista inteira; depois do ultimo segura-se nele, ate
    ao fim do encadeado de saida.
    """
    trocos = pronto["trocos"]
    troco = trocos[-1]
    for tr in trocos:
        if t < tr["ate"]:
            troco = tr
            break
    return mergulho_vista_no_troco(troco, t), troco["celula"]


def preparar_mergulho(imagens, focos, texto, entra=0.0, sai=0.0, duracao=4.0, clip_leg=None):
    """A colagem em grelha com mergulho na ultima foto. Ver MERGULHO_ESTILO. `clip_leg`: ler_opcoes_clip()."""
    n = len(imagens)
    focos = list(focos) + [None] * (n - len(focos))
    d = MERGULHO_DOBRO
    capa = faixa_texto(texto, clip_leg=clip_leg)
    altura = mergulho_altura(capa)
    celulas = mergulho_grelha(n, L, altura)
    mergulhos = [n - 1]       # as celulas onde se mergulha: hoje so a ultima
    grande = Image.new("RGB", (L * d, A * d), (0, 0, 0))
    pequenas = []
    alvos = {}
    for k, ((x, y, w, h), foto, foco) in enumerate(zip(celulas, imagens, focos)):
        # Uma foto aberta de cada vez, ver FotoPorAbrir: a anterior sai antes de esta abrir.
        im = None
        im = aberta(foto)
        W, H = max(1, int(round(w * d))), max(1, int(round(h * d)))
        cel = cobrir_foco(im, W, H, foco) or cobrir_alto(im, W, H)
        grande.paste(cel, (int(round(x * d)), int(round(y * d))))
        pequenas.append((cel.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS),
                         (int(round(x)), int(round(y)))))
        if k in mergulhos:
            # A FOTO DO MERGULHO, no tamanho com que acaba: a celula a cobrir o ecra inteiro, feita
            # do ficheiro enquanto esta aberto. So esta fica, nunca a foto em resolucao total.
            cobre = mergulho_cobre((x, y, w, h))
            Wf, Hf = int(math.ceil(w * cobre)), int(math.ceil(h * cobre))
            alvos[k] = com_margem(cobrir_foco(im, Wf, Hf, foco) or cobrir_alto(im, Wf, Hf), "preto")
    im = None
    ultima = mergulhos[-1]
    cobre = mergulho_cobre(celulas[ultima])
    tempos = mergulho_tempos(n, duracao, entra, sai, cobre)
    return {"tipo": "mergulho", "n": n, "celulas": celulas, "altura": altura, "grande": grande,
            "pequenas": pequenas, "alvos": alvos, "alvo": alvos[ultima], "cobre": cobre,
            "tempos": tempos, "trocos": mergulho_trocos(tempos, celulas[ultima], ultima),
            "capa": capa, "_camada": None}


def suave(p):
    """Arranca e trava devagar, de 0 a 1."""
    p = min(1.0, max(0.0, p))
    return p * p * (3.0 - 2.0 * p)


def desenhar_mergulho(pronto, t_rel, duracao):
    """Um fotograma do mergulho."""
    tempos = pronto["tempos"]
    atraso, entra_foto, entre = tempos["atraso"], tempos["entra"], tempos["entre"]
    n = pronto["n"]
    todas = atraso + entra_foto + entre * (n - 1)
    if t_rel < todas:
        # AS FOTOS A APARECER: a camara esta parada e a grelha e a de tamanho natural, por
        # isso cola-se sem transformacao nenhuma. As que ja apareceram guardam-se numa camada.
        prontas = 0
        while prontas < n and t_rel >= atraso + prontas * entre + entra_foto:
            prontas += 1
        if pronto["_camada"] is None or pronto["_camada"][0] != prontas:
            base = Image.new("RGB", (L, A), (0, 0, 0))
            for cel, pos in pronto["pequenas"][:prontas]:
                base.paste(cel, pos)
            pronto["_camada"] = (prontas, base)
        tela = pronto["_camada"][1].copy()
        for k in range(prontas, n):
            a = (t_rel - atraso - k * entre) / entra_foto if entra_foto else 1.0
            if a <= 0:
                break
            cel, pos = pronto["pequenas"][k]
            tela.paste(Image.blend(tela.crop((pos[0], pos[1], pos[0] + cel.width, pos[1] + cel.height)),
                                   cel, min(1.0, a)), pos)
    else:
        (x0, y0, s), k = mergulho_camara(pronto, t_rel)
        d = MERGULHO_DOBRO
        # ponto do ecra (X, Y) -> ponto da grelha grande: d * (x0 + X / s, y0 + Y / s)
        tela = pronto["grande"].transform(
            (L, A), Image.AFFINE, (d / s, 0.0, d * x0, 0.0, d / s, d * y0), resample=Image.BICUBIC)
        alvo = pronto["alvos"].get(k)
        if alvo is not None:
            # A foto do mergulho por cima da sua celula, no sitio exato, a partir do sprite do fim.
            x, y, w, h = pronto["celulas"][k]
            compor(tela, alvo, (x + w / 2.0 - x0) * s, (y + h / 2.0 - y0) * s, s / mergulho_cobre((x, y, w, h)))
    if pronto["capa"] is not None and not SEM_LEGENDAS:
        cor, mascara = pronto["capa"]
        tela.paste(cor, (0, 0), mascara)
    return tela


def preparar_lado(lay, imagens, focos, texto, textos=None, opcoes=None, duracao=None, clip_leg=None):
    """O lado a lado, a partir das imagens ja abertas, uma por celula de lado_celulas(lay).

    `focos` e um por foto, como na coluna fonte_imagem, e `texto` a legenda do grupo.
    `textos` e um por foto, ver textos_do_grupo(): cada um numa faixa dentro da sua
    celula, ver lado_faixas(), ou, com a opcao legenda, na faixa de baixo do ecra a trocar
    com cada celula, ver legenda_por_foto(). `opcoes` sao as de ler_textos_opcoes() e
    `duracao` a do clip, so para os avisos. Sem textos as celulas sao as de antes, pixel
    a pixel. `clip_leg` sao as opcoes do clip, de ler_opcoes_clip(): a legenda numa linha,
    o lp e as fotos inteiras (li), ver lado_inteira().
    """
    opcoes = ler_textos_opcoes(opcoes)
    inteiras = bool(clip_leg and clip_leg["li"])
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
        elif inteiras:
            # AS FOTOS INTEIRAS (clip.li, 3 de outubro): a foto encaixada na celula, sem cortar, com o
            # fundo da celula desfocado a partir dela. Respira como as outras, e cabe inteira ate no
            # fim do zoom lento. A FAIXA DO TEXTO CONTINUA A SER A DA CELULA, de lado a lado e em
            # baixo, como hoje: dentro de cada foto, duas fotos de formas diferentes ficavam com os
            # textos a alturas e larguras diferentes (visto no clip 71), e por cima da foto tapava
            # gente. Na celula fica sobre o desfocado sempre que a foto nao chega ao fundo.
            img, (pw, ph) = lado_inteira(im, w, h)
            e0 = 1.0 / (1.0 + LADO_ZOOM)
            if foco:
                foco_na_celula = [(w / 2.0 + (foco[0] - 0.5) * pw * e, h / 2.0 + (foco[1] - 0.5) * ph * e)
                                  for e in (e0, 1.0)]
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
        legenda = legenda_por_foto([t or grupo for t in textos], opcoes["tamanho"], clip_leg)
        if legenda is not None and duracao:
            tempos = tempos_legenda_grupo("lado", len(celulas), duracao)
            for k, t, dura in legendas_curtas(legenda["textos"], tempos):
                avisar_legenda_curta(k, t, dura)
        textos = None
    capa = None if legenda is not None else faixa_texto(texto, clip_leg=clip_leg)
    if textos:
        lado_faixas(celulas, textos, capa, lay, opcoes["tamanho"])
    return {"tipo": "lado", "celulas": celulas, "capa": capa, "legenda": legenda, "opcoes": opcoes}


# O LADO A LADO SEM CORTAR PESSOAS (contrato de 3 de outubro, ponto 4). O Tiago: "quando meto lado a
# lado esta a focar em excesso, acabando por cortar pessoas". Hoje cada foto enche a sua celula e o
# que sobra corta-se: uma foto deitada numa celula de 2v (956 x 1080) perde mais de metade da largura.
# Com clip.li cada foto entra inteira, encaixada, e o resto da celula e a propria foto desfocada e
# escurecida, como o tratamento "fundo" de uma foto sozinha (desfoque 46 e 55%). Sem li, nada muda.
LADO_CORTE_AVISO = 0.25          # a Mesa e o montar avisam quando o enchimento corta mais do que isto


def lado_inteira(im, w, h):
    """O sprite de uma celula com a foto inteira: (imagem do tamanho do sprite, (pw, ph) da foto nele).

    O sprite e o de sempre, (w, h) mais LADO_ZOOM, e o zoom lento leva-o de caber na celula a 1:1. A
    foto vai encaixada em (w, h) no meio dele: no fim do zoom enche a celula num dos lados sem perder
    nada, e no principio fica 2% para dentro. Por tras, a foto a cobrir o sprite, desfocada.
    """
    sw, sh = int(math.ceil(w * (1 + LADO_ZOOM))), int(math.ceil(h * (1 + LADO_ZOOM)))
    fundo = cobrir(im, sw, sh).filter(ImageFilter.GaussianBlur(46))
    fundo = Image.blend(Image.new("RGB", (sw, sh), (0, 0, 0)), fundo, 0.55)
    dentro = encaixar(im, w, h)
    fundo.paste(dentro, ((sw - dentro.width) // 2, (sh - dentro.height) // 2))
    return fundo, dentro.size


def lado_corte(lay, tamanhos):
    """A fracao de cada foto que o enchimento de hoje deixa de fora, [0..1], pela ordem das celulas.

    `tamanhos` sao (largura, altura) de cada foto ja rodada pelo EXIF. A conta e a do cobrir(): a foto
    cresce ate cobrir a celula e o que passa corta-se, 1 - min(r, 1/r), com r a razao entre a forma da
    foto e a da celula. Nao conta o zoom lento (mais 4% no fim) nem o ponto de foco, que so escolhe o
    que se corta. O cartao do meio do 3s vai inteiro e da 0. A Mesa faz a mesma conta.
    """
    cortes = []
    for k, ((_x, _y, w, h), _vem) in enumerate(lado_celulas(lay)):
        if k >= len(tamanhos) or not tamanhos[k] or not tamanhos[k][0] or not tamanhos[k][1]:
            cortes.append(None)
            continue
        if lay == "3s" and k == 2:
            cortes.append(0.0)
            continue
        r = (tamanhos[k][0] / float(tamanhos[k][1])) / (w / float(h))
        cortes.append(1.0 - min(r, 1.0 / r))
    return cortes


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


# ------------------------------------------------------------ a zona de destaque
# O PEDIDO, 2 de outubro: "Permite-me dentro de uma foto marcar uma zona para ter mais detalhe,
# por exemplo eu tenho umas fotos de equipa que se eu nao assinalar quem eu sou as pessoas podem
# nao perceber." E as 02:23, no contrato da Mesa: "nem sempre e possivel com zoom, pois a
# qualidade da foto pode nao ser otima e precisamos de outra forma de realcar".
#
# POR ISSO O DESTAQUE NAO APROXIMA. Depois de a foto entrar e assentar, o que esta fora da zona
# escurece devagar e um contorno fino na cor quente do letreiro desenha-se a volta dela; com
# `texto`, um nome curto por baixo, na letra e na faixa da legenda. Fica ate a foto sair. Nenhum
# pixel e esticado nem inventado (decisao 090): dentro da zona a foto fica exatamente a que era,
# e fora dela so muda o brilho. A Mesa grava clip.zd = {x, y, w, h} em fracoes da foto, mais
# forma, texto e escurecer, e o montar escreve-o na coluna destaque, so com o que difere da
# omissao. Sem a coluna nada disto corre, e o filme sai igual ao byte.
#
# A ZONA E DA FOTO, NAO DO ECRA. Conta-se a cada fotograma a partir do retangulo onde a foto
# acabou de ser composta, e por isso acompanha o zoom lento, o afastada, o aproxima e o corte da
# rajada sem contas proprias. O escurecer e o de todo o ecra fora da zona, fundo desfocado
# incluido, como a Mesa o mostra (palcoDestaque). E desenha-se com a cobertura exata de cada
# pixel (destaque_distancia()), porque com o zoom lento a zona anda menos de um pixel por
# fotograma, e uma borda a pixeis inteiros saltava de pixel em pixel: e a borda que pisca do
# CLAUDE.md, outra vez. O nome vai pelo compor(), com a margem do com_margem(), pela mesma razao.
DESTAQUE_ESPERA = 1.0       # segundos do clip antes de comecar a escurecer, no minimo
DESTAQUE_ASSENTA = 0.3      # e depois de o encadeado de entrada acabar, para a foto assentar
DESTAQUE_SOBE = 0.6         # segundos a escurecer, e o contorno e o nome a acender com ele
DESTAQUE_PLENO_MIN = 1.0    # segundos aceso antes do encadeado de saida; sem eles, entra com a foto
DESTAQUE_ESCURECER = 0.45   # a omissao do contrato: fora da zona fica a 55% do brilho
DESTAQUE_FORMAS = ("retangulo", "elipse")
DESTAQUE_LINHA = 4.0        # espessura do contorno a 1080, todo por fora da zona
DESTAQUE_RAIO = 6.0         # raio dos cantos da zona a 1080; por fora do contorno fica 10
DESTAQUE_TEXTO_FOLGA = 14   # entre a zona e a faixa do nome, a 1080, o da Mesa
DESTAQUE_TEXTO_BORDA = 16   # a faixa do nome nunca chega mais perto do que isto da borda do ecra
DESTAQUE_LADO_MIN = 0.01    # um lado abaixo disto, em fracao da foto, e um clique e nao uma zona
DESTAQUE_FORA_AVISO = 0.10  # acima disto da zona fora do ecra, o preparar avisa


def ler_destaque(valor):
    """A coluna destaque -> ({x, y, w, h, forma, texto, escurecer}, aviso), ou (None, aviso).

    O montar ja validou e so escreve o que difere da omissao. Aqui volta-se a ver pela regra do
    imagem_da_marca(): um CSV mexido a mao nao para um render de quinze minutos a meio. Uma coluna
    que nao se le fica sem destaque e o aviso diz porque; uma forma, um escurecer ou um texto que
    nao servem ficam na omissao, tambem com aviso. A zona e cortada a foto: a Mesa so a deixa
    desenhar dentro dela, e o que sobra para fora e arredondamento de quem arrasta.
    """
    if not (valor or "").strip():
        return None, ""
    try:
        d = json.loads(valor)
        bruto = [d[k] for k in ("x", "y", "w", "h")]
        if any(isinstance(v, bool) for v in bruto):
            raise TypeError("booleano")
        x, y, w, h = (float(v) for v in bruto)
    except (ValueError, TypeError, KeyError, AttributeError):
        return None, "a coluna destaque %r nao se le, fica sem destaque" % valor[:60]
    if not all(math.isfinite(v) for v in (x, y, w, h)):
        return None, "a coluna destaque %r nao se le, fica sem destaque" % valor[:60]
    x0, y0 = max(0.0, x), max(0.0, y)
    x1, y1 = min(1.0, x + w), min(1.0, y + h)
    if x1 - x0 < DESTAQUE_LADO_MIN or y1 - y0 < DESTAQUE_LADO_MIN:
        return None, "a zona de destaque %r nao tem tamanho dentro da foto, fica sem destaque" % valor[:60]
    avisos = []
    forma = d.get("forma")
    if forma in (None, ""):
        forma = DESTAQUE_FORMAS[0]
    elif forma not in DESTAQUE_FORMAS:
        avisos.append("forma %r, fica %s" % (forma, DESTAQUE_FORMAS[0]))
        forma = DESTAQUE_FORMAS[0]
    esc = d.get("escurecer")
    if esc is None:
        esc = DESTAQUE_ESCURECER
    else:
        try:
            if isinstance(esc, bool):
                raise TypeError("booleano")
            esc = float(esc)
            if not 0.0 <= esc <= 1.0:
                raise ValueError("fora de 0 a 1")
        except (ValueError, TypeError):
            avisos.append("escurecer %r, fica %s" % (d.get("escurecer"), DESTAQUE_ESCURECER))
            esc = DESTAQUE_ESCURECER
    texto = d.get("texto")
    texto = texto.strip() if isinstance(texto, str) else ""
    return ({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "forma": forma, "texto": texto,
             "escurecer": esc}, "; ".join(avisos))


def destaque_janela(duracao, entra=0.0, sai=0.0):
    """(comeco, aceso) do destaque em segundos do clip, ou None quando ele entra com a foto.

    A FOTO ENTRA PRIMEIRO E SO DEPOIS SE APONTA. Escurecer enquanto ela ainda aparece era mostrar
    duas coisas ao mesmo tempo, e a 15 metros nao se le nenhuma. Comeca DESTAQUE_ASSENTA depois de
    o encadeado de entrada acabar e nunca antes de DESTAQUE_ESPERA, e leva DESTAQUE_SOBE a acender.

    NUM CLIP CURTO, mais cedo, ate ao fim do encadeado de entrada, para ficar DESTAQUE_PLENO_MIN
    aceso antes de a seguinte comecar a entrar. Se nem assim cabe (a rajada, um clip de dois
    segundos), entra aceso com a foto, como a legenda: um destaque que acendesse durante o
    encadeado de saida nunca se via inteiro. E a regra do aproxima_janela() num clip curto.
    """
    a = max(0.0, float(entra or 0.0))
    b = float(duracao) - max(0.0, float(sai or 0.0))
    comeco = min(max(DESTAQUE_ESPERA, a + DESTAQUE_ASSENTA), b - DESTAQUE_SOBE - DESTAQUE_PLENO_MIN)
    if comeco < a - 1e-9:
        return None
    return comeco, comeco + DESTAQUE_SOBE


def destaque_alfa(janela, t_rel):
    """Quanto do destaque esta aceso no instante t_rel, de 0 a 1: sai do repouso e chega em repouso."""
    if janela is None:
        return 1.0
    comeco, aceso = janela
    return _suave((t_rel - comeco) / (aceso - comeco))


def destaque_tempo_aceso(duracao, entra=0.0, sai=0.0):
    """Segundos com o destaque inteiro e a foto sozinha no ecra: o que o montar compara com o minimo."""
    b = float(duracao) - max(0.0, float(sai or 0.0))
    janela = destaque_janela(duracao, entra, sai)
    inicio = max(0.0, float(entra or 0.0)) if janela is None else janela[1]
    return max(0.0, b - inicio)


def destaque_caixa(zd, x0, y0, larg, alt):
    """(x0, y0, x1, y1) da zona no ecra, com a foto composta em (x0, y0) com larg x alt."""
    return (x0 + zd["x"] * larg, y0 + zd["y"] * alt,
            x0 + (zd["x"] + zd["w"]) * larg, y0 + (zd["y"] + zd["h"]) * alt)


def destaque_distancia(xs, ys, caixa, forma, raio):
    """A distancia com sinal de cada centro de pixel a borda da zona: negativa dentro, em pixeis.

    E DELA QUE SAI A COBERTURA, clip(0,5 - d): numa borda direita e exatamente a parte do pixel que
    a zona cobre, e por isso a borda anda ao sub-pixel com o zoom lento em vez de saltar. O
    contorno e a mesma conta com a borda empurrada DESTAQUE_LINHA para fora. No retangulo os cantos
    sao arredondados com `raio`; na elipse a distancia e a aproximacao de primeira ordem, a que
    erra menos de um decimo de pixel a menos de dez pixeis da borda, onde a cobertura se decide.
    """
    import numpy as np
    zx0, zy0, zx1, zy1 = caixa
    cx, cy = (zx0 + zx1) / 2.0, (zy0 + zy1) / 2.0
    hx, hy = max(1e-6, (zx1 - zx0) / 2.0), max(1e-6, (zy1 - zy0) / 2.0)
    px, py = np.abs(xs - cx), np.abs(ys - cy)
    if forma == "elipse":
        k0 = np.sqrt((px / hx) ** 2 + (py / hy) ** 2)
        k1 = np.sqrt((px / (hx * hx)) ** 2 + (py / (hy * hy)) ** 2)
        return np.where(k1 > 1e-12, k0 * (k0 - 1.0) / np.maximum(k1, 1e-12), -min(hx, hy))
    r = min(raio, hx, hy)
    qx, qy = px - (hx - r), py - (hy - r)
    return (np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
            + np.minimum(np.maximum(qx, qy), 0.0) - r)


def preparar_destaque(zd, entra, sai, duracao, legenda="", nome="", clip_leg=None):
    """O que o destaque precisa de saber, contado uma vez por clip: a janela, a cor e o nome feito."""
    d = dict(zd, janela=destaque_janela(duracao, entra, sai),
             cor=cor_do_estilo("cartao", "quente", LETREIRO_QUENTE),
             linha=DESTAQUE_LINHA * A / 1080.0, raio=DESTAQUE_RAIO * A / 1080.0,
             folga=DESTAQUE_TEXTO_FOLGA * A / 1080.0, nome=None)
    # O TETO DO NOME: com legenda em baixo, a faixa do nome nunca desce ate ela. A Mesa poe o nome
    # ate 1,6 corpos do fundo do ecra, e a faixa da legenda comeca bem acima disso.
    tam = legenda_tamanho()
    d["teto"] = A - tam * 1.6
    if (legenda or "").strip():
        # COM A LEGENDA NOUTRO SITIO (3 de outubro) o teto sobe com ela, e uma legenda numa linha so
        # (x1) tem o bloco de uma linha. Sem nada disso e a conta de sempre.
        uma = bool(clip_leg and clip_leg["x1"])
        _dx, dy, _alinhamento = posicao_da_legenda(clip_leg)
        d["teto"] = min(d["teto"], A - LEGENDA_TEXTO - bloco_legenda(legenda, uma_linha=uma) - LEGENDA_ALMOFADA
                        - d["folga"] - tam * 1.45 + dy)
    if zd.get("texto"):
        # A FAIXA E A DA MESA: o texto centrado, 18 px de cada lado, 1,45 corpos de altura, a letra
        # a 0,22 corpos do cimo; o alfa da faixa e o da legenda do estilo, e a cor tambem.
        # A largura e a do avanco da letra, a mesma que o measureText() da Mesa.
        fonte = letra("legenda", tam)
        # com um emoji, o emoji a cores conta com a largura dele, e os equivalentes trocam-se (texto_emojis)
        largura = int(math.ceil(texto_emojis.largura(zd["texto"], fonte))) + 36
        altura = int(math.ceil(tam * 1.45))
        # AS PERNAS DAS LETRAS NAO SE CORTAM (revisao de 2 de outubro). A faixa tem 1,45 corpos, como
        # na Mesa, e o desenho era feito dentro dela: numa letra de descendentes compridos (Playfair,
        # Great Vibes, Pinyon) o "g" de "Tiago" perdia a ponta, ate 39 px a 46. A Mesa pinta a faixa
        # e escreve por cima sem cortar, e aqui tambem: a tela cresce o que a tinta passa da faixa,
        # para cima e para baixo, e a faixa fica onde estava. A parte de fora e transparente na cor
        # da letra, para a borda da tinta sair na cor dela e nao escurecida. Sem tinta de fora (o
        # Arial Bold tem 7 px de folga) a tela e a faixa, ao byte como antes.
        cor = legenda_cor()
        topo = tam * 0.22
        _x0, t0, _x1, t1 = texto_emojis.caixa(zd["texto"], fonte, anchor="ma")
        cima = max(0, int(math.ceil(-(topo + t0))))
        baixo = max(0, int(math.ceil(topo + t1)) - altura)
        faixa = Image.new("RGBA", (largura, cima + altura + baixo), cor + (0,))
        faixa.paste((0, 0, 0, fundo_da_legenda(LEGENDA_ALFA)), (0, cima, largura, cima + altura))
        texto_emojis.escrever(ImageDraw.Draw(faixa), (largura / 2.0, cima + topo), zd["texto"], fonte,
                              cor + (255,), anchor="ma")
        d["nome"] = com_margem(faixa.convert("RGBa"), "preto")
        d["nome_faixa"] = (altura, cima, baixo)
        if largura > L - 2 * DESTAQUE_TEXTO_BORDA:
            print("  destaque%s: o nome %r tem %d px e o ecra %d; sai cortado dos lados"
                  % (nome, zd["texto"], largura, L))
    return d


def onde_vai_o_nome(d, caixa):
    """(cx, cy) da faixa do nome no ecra: por baixo da zona, ou por cima se em baixo nao couber.

    POR BAIXO, A 14 PX, como a Mesa. Mas a Mesa encosta-o ao fundo do ecra quando a zona esta em
    baixo, e ai a faixa pisava a propria zona, que e o que se quer mostrar: aqui vai para cima da
    zona, se couber; so se nem em cima couber e que fica encostado ao teto, como na Mesa. Nos
    lados nunca passa a DESTAQUE_TEXTO_BORDA da borda do ecra.
    """
    largura = d["nome"].width - 2 * MARGEM
    # A conta e da faixa, e nao da tela: a tela pode ter por cima e por baixo a tinta que passa
    # dela (preparar_destaque), e o que volta e o centro da tela com a faixa no sitio de sempre.
    altura, cima, baixo = d.get("nome_faixa") or (d["nome"].height - 2 * MARGEM, 0, 0)
    ty = caixa[3] + d["linha"] + d["folga"]
    if ty > d["teto"]:
        acima = caixa[1] - d["linha"] - d["folga"] - altura
        ty = acima if acima >= LEGENDA_FUNDO else d["teto"]
    cx = (caixa[0] + caixa[2]) / 2.0
    borda = DESTAQUE_TEXTO_BORDA + largura / 2.0
    if L - borda >= borda:
        cx = min(L - borda, max(borda, cx))
    return cx, ty - cima + (cima + altura + baixo) / 2.0


def destacar(tela, d, x0, y0, larg, alt, t_rel):
    """O fotograma `tela` com o destaque `d` no instante t_rel, a foto composta em (x0, y0, larg, alt).

    Devolve a mesma tela antes de o destaque comecar, ao byte: e assim que a foto entra e assenta
    igual a de sempre. Fora da zona, cada pixel multiplicado pelo mesmo fator (uma tabela, a mesma
    dentro e fora da caixa onde a zona se conta); dentro, o pixel da foto, ao byte; na borda, a
    mistura dos dois pela cobertura; e por cima o contorno na cor quente, que acende com o resto.
    """
    alfa = destaque_alfa(d["janela"], t_rel)
    if alfa <= 0.0:
        return tela
    k = d["escurecer"] * alfa
    tabela = [int(v * (1.0 - k) + 0.5) for v in range(256)]
    escura = tela.point(tabela * len(tela.getbands()))
    caixa = destaque_caixa(d, x0, y0, larg, alt)
    folga = d["linha"] + 2.0
    bx0, by0 = max(0, int(math.floor(caixa[0] - folga))), max(0, int(math.floor(caixa[1] - folga)))
    bx1 = min(tela.width, int(math.ceil(caixa[2] + folga)))
    by1 = min(tela.height, int(math.ceil(caixa[3] + folga)))
    if bx1 > bx0 and by1 > by0:
        # O MEIO DA ZONA E A FOTO, AO BYTE, e cola-se sem contas: uma zona grande era um ecra
        # inteiro de distancias por fotograma, e so a faixa a volta da borda as precisa. O miolo
        # e o retangulo cujos cantos ficam a mais de meio pixel para dentro da borda (a zona e
        # convexa, e entao o retangulo todo fica), e as contas fazem-se nas quatro tiras a volta.
        ix0, iy0, ix1, iy1 = destaque_miolo(caixa, d["forma"], d["raio"], (bx0, by0, bx1, by1))
        tiras = [(bx0, by0, bx1, iy0), (bx0, iy1, bx1, by1),
                 (bx0, iy0, ix0, iy1), (ix1, iy0, bx1, iy1)]
        if ix1 > ix0 and iy1 > iy0:
            escura.paste(tela.crop((ix0, iy0, ix1, iy1)), (ix0, iy0))
        for perto in tiras:
            if perto[2] > perto[0] and perto[3] > perto[1]:
                _destacar_tira(tela, escura, perto, caixa, d, alfa)
    if d["nome"] is not None:
        cx, cy = onde_vai_o_nome(d, caixa)
        compor(escura, d["nome"], cx, cy, 1.0, alfa)
    return escura


def destaque_miolo(caixa, forma, raio, perto):
    """(x0, y0, x1, y1) inteiros, dentro de `perto`, onde a zona cobre cada pixel por inteiro.

    No retangulo e a zona encolhida do raio e de mais um pixel: ai a distancia a borda e pelo menos
    um pixel. Na elipse e o retangulo inscrito a 0,7 dos semieixos, encolhido ate o canto ficar a
    mais de meio pixel da borda pela propria destaque_distancia(); uma zona pequena demais fica sem
    miolo, e conta-se toda. Vazio quando nao ha miolo: as tiras cobrem entao a caixa inteira.
    """
    import numpy as np
    zx0, zy0, zx1, zy1 = caixa
    cx, cy = (zx0 + zx1) / 2.0, (zy0 + zy1) / 2.0
    if forma == "elipse":
        mx, my = 0.7 * (zx1 - zx0) / 2.0 - 1.0, 0.7 * (zy1 - zy0) / 2.0 - 1.0
        while mx > 0 and my > 0:
            canto = destaque_distancia(np.array([cx + mx]), np.array([cy + my]), caixa, forma, raio)
            if float(canto[0]) <= -1.0:
                break
            mx, my = mx - 1.0, my - 1.0
    else:
        mx = (zx1 - zx0) / 2.0 - min(raio, (zx1 - zx0) / 2.0) - 1.0
        my = (zy1 - zy0) / 2.0 - min(raio, (zy1 - zy0) / 2.0) - 1.0
    if mx <= 0 or my <= 0:
        return perto[0], perto[1], perto[0], perto[1]
    # So os pixeis inteiros dentro: o pixel i vai de i a i+1.
    ix0 = max(perto[0], int(math.ceil(cx - mx)))
    iy0 = max(perto[1], int(math.ceil(cy - my)))
    ix1 = min(perto[2], int(math.floor(cx + mx)))
    iy1 = min(perto[3], int(math.floor(cy + my)))
    if ix1 <= ix0 or iy1 <= iy0:
        return perto[0], perto[1], perto[0], perto[1]
    return ix0, iy0, ix1, iy1


def _destacar_tira(tela, escura, perto, caixa, d, alfa):
    """Uma tira da caixa da zona: a foto e a sombra misturadas pela cobertura, e o contorno por cima."""
    import numpy as np
    bx0, by0, bx1, by1 = perto
    ys, xs = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
    dist = destaque_distancia(xs + 0.5, ys + 0.5, caixa, d["forma"], d["raio"])
    dentro = np.clip(0.5 - dist, 0.0, 1.0).astype(np.float32)
    traco = (np.clip(0.5 - (dist - d["linha"]), 0.0, 1.0) - dentro).astype(np.float32) * alfa
    foto = np.asarray(tela.crop(perto), dtype=np.float32)
    sombra = np.asarray(escura.crop(perto), dtype=np.float32)
    junto = sombra + (foto - sombra) * dentro[..., None]
    junto += (np.array(d["cor"], dtype=np.float32) - junto) * traco[..., None]
    escura.paste(Image.fromarray(np.floor(junto + 0.5).astype(np.uint8), "RGB"), (bx0, by0))


def destaque_na_foto(tela, d, sprite, escala, cx, cy, t_rel):
    """O destacar() de uma foto composta pelo compor() ou pelo compor_visivel(): o retangulo e o deles.

    As mesmas contas do compor(): a foto sem a margem, vezes a escala, centrada em (cx, cy), com
    as casas decimais todas. E isso que prende a zona a foto ao sub-pixel durante o zoom.
    """
    larg = (sprite.width - 2 * MARGEM) * escala
    alt = (sprite.height - 2 * MARGEM) * escala
    return destacar(tela, d, cx - larg / 2.0, cy - alt / 2.0, larg, alt, t_rel)


def destaque_fora_do_ecra(zd, x0, y0, larg, alt):
    """A fracao da zona que fica fora do ecra, com a foto em (x0, y0, larg, alt). So para o aviso."""
    caixa = destaque_caixa(zd, x0, y0, larg, alt)
    area = (caixa[2] - caixa[0]) * (caixa[3] - caixa[1])
    if area <= 0:
        return 0.0
    vx = max(0.0, min(L, caixa[2]) - max(0.0, caixa[0]))
    vy = max(0.0, min(A, caixa[3]) - max(0.0, caixa[1]))
    return 1.0 - vx * vy / area


def destaque_do_clip(clip, legenda="", clip_leg=None):
    """O destaque preparado de uma foto solta, ou None se a coluna destaque nao o traz.

    Os encadeados sao os do aproxima, que vem do main por ligar_transicoes: _transicao_entrada, e
    _transicao_seguinte, o do clip seguinte ou o fade do fim. Sem eles conta o do proprio clip.
    `clip_leg` sao as opcoes do clip: o teto do nome e o da legenda, onde ela estiver.
    """
    zd, aviso = ler_destaque(clip.get("destaque"))
    quem = " do clip %s" % clip.get("ordem", "?")
    if aviso:
        print("  destaque%s: %s" % (quem, aviso))
    if zd is None:
        return None
    entra = clip.get("_transicao_entrada")
    entra = float(clip.get("transicao_s") or 0.0) if entra in (None, "") else float(entra)
    sai = clip.get("_transicao_seguinte")
    sai = entra if sai in (None, "") else float(sai)
    return preparar_destaque(zd, entra, sai, duracao_do_clip(clip) or 4.0, legenda, quem, clip_leg)


def caixa_da_rajada(tamanho, foco):
    """(x0, y0, largura, altura) da foto inteira no ecra, na rajada: as contas do cobrir_foco() e do cobrir()."""
    if foco is not None:
        nw, nh, x, y = janela_foco(tamanho, L, A, foco)
    else:
        f = max(L / tamanho[0], A / tamanho[1])
        nw, nh = max(1, round(tamanho[0] * f)), max(1, round(tamanho[1] * f))
        x, y = (nw - L) // 2, (nh - A) // 2
    return -x, -y, nw, nh


def preparar(clip, inv_por_nome):
    """Prepara o clip uma vez: sprite no tamanho maximo e legenda em camada.

    A coluna `tratamento` da montagem escolhe o aspeto:
      fiel    o da mae da Clara: encaixa com barras pretas e zoom lento
      fundo   o fundo passa a ser a propria foto ampliada e desfocada
      rajada  enche o ecra, sem movimento, para cortes secos
    No lado a lado e a disposicao, e na colagem e na pilha o estilo, ver ESTILOS_MONTE.
    """
    texto = clip["texto_ecra"]
    # AS OPCOES DO CLIP (3 de outubro): a legenda numa linha (x1), o lp e as fotos inteiras do lado
    # a lado (li). Sem a coluna, ou sem nada nela, e None, e tudo abaixo e o de sempre.
    clip_leg = ler_opcoes_clip(clip.get(COLUNA_OPCOES_CLIP))
    if clip["tipo"] == "cartao":
        # Um cartao vazio continua a ser preto (e o de uma foto que falta, em carregar_montagem).
        if (texto or "").strip():
            return {"tipo": "cartao", "let": letreiro_do_cartao(texto.strip()), "capa": None}
        return {"tipo": "cartao", "base": cartao(texto), "capa": None}
    if clip["tipo"] == "nome":
        return {"tipo": "nome", "let": letreiro([(texto or "").strip().upper()],
                                                corpo_do_estilo("nome", "tamanho", NOME_TAMANHO),
                                                NOME_ESPACO, 7), "capa": None}
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
            # O DE ANOS ATE UMA DATA E O PARADO NO FIM (contrato de 3 de outubro, pontos 6 e 7):
            # "1995>20/05/2012" acende na chegada a data inteira e o texto dela, e o "~segundos"
            # que o montar escreve com o clip.cp deixa o contador parado na chegada esse tempo.
            # Sem os dois, o pronto e o de sempre, sem chaves novas.
            chegada = linha_tempo.chegada_do_contador(texto)
            parado = linha_tempo.segura_de(texto)
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
        if chegada is not None or parado > 0:
            return {"tipo": "contador", "modo": modo, "de": de, "para": para,
                    "marcos": marcos, "chegada": chegada, "parado": parado}
        return {"tipo": "contador", "modo": modo, "de": de, "para": para,
                "marcos": marcos}
    if clip["tipo"] == "marcos":
        ano, marcas, troco, abre = linha_tempo.ler_meses(texto)
        return {"tipo": "marcos", "ano": ano, "marcas": marcas,
                "troco": troco, "abre": abre, "segura": linha_tempo.segura_de(texto),
                "congela": linha_tempo.congela_de(texto)}

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
        return {"tipo": "video", "quadros": quadros, "capa": faixa_texto(texto, clip_leg=clip_leg)}

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
                             duracao_do_clip(clip), clip_leg=clip_leg)

    if clip["tipo"] in LIMITES_MONTE:
        # o limite do estilo, que no mergulho e outro (decisao 102), ver limites_do_grupo()
        minimo, maximo = limites_do_grupo(clip["tipo"], clip.get("tratamento"))
        caminhos = clip.get("_caminhos") or []
        if not (minimo <= len(caminhos) <= maximo):
            return None
        if not all(c and os.path.exists(c) for c in caminhos):
            return None
        # POR ABRIR: so o tamanho, do cabecalho. Cada uma abre-se na sua vez dentro do
        # preparar_monte() ou do preparar_mergulho(), ver FotoPorAbrir (1 de outubro).
        imagens = [FotoPorAbrir(c) for c in caminhos]
        focos = [ler_foco(p) for p in (clip.get("fonte_imagem") or "").split("|")]
        # Os encadeados vem do main, por ligar_transicoes: _transicao_entrada, que e
        # zero no primeiro clip do corpo, e _transicao_seguinte, que e o do clip
        # seguinte ou o fade a preto do fim. Sem eles contam o do proprio clip.
        entra = clip.get("_transicao_entrada")
        entra = float(clip.get("transicao_s") or 0.0) if entra in (None, "") else float(entra)
        sai = clip.get("_transicao_seguinte")
        sai = entra if sai in (None, "") else float(sai)
        # O MERGULHO NA GRELHA e um estilo da colagem, mas desenha-se a parte: nao ha
        # agenda de monte nem poses, ver preparar_mergulho().
        if clip["tipo"] == "colagem" and (clip.get("tratamento") or "").strip() == MERGULHO_ESTILO:
            return preparar_mergulho(imagens, focos, texto, entra, sai,
                                     duracao_do_clip(clip) or 4.0, clip_leg=clip_leg)
        # O estilo vem na coluna tratamento, decisao 068. O "fiel" das montagens de antes
        # e qualquer valor desconhecido dao a omissao, ver estilo_monte().
        return preparar_monte(clip["tipo"], imagens, focos, texto, entra, sai,
                              clip.get("tratamento"),
                              textos=ler_textos_fotos(clip.get("textos_fotos")),
                              opcoes=ler_textos_opcoes(clip.get("textos_opcoes")),
                              duracao=duracao_do_clip(clip), clip_leg=clip_leg)

    caminho = clip.get("_caminho")
    if not caminho or not os.path.exists(caminho):
        r = inv_por_nome.get((clip["ficheiro"] or "").lower())
        caminho = r["caminho"] if r else None
    if not caminho or not os.path.exists(caminho):
        return None

    tratamento = (clip.get("tratamento") or "fiel").strip() or "fiel"
    im = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    # A ZONA DE DESTAQUE so existe com a coluna destaque; sem ela fica None e nada abaixo muda.
    destaque = destaque_do_clip(clip, texto, clip_leg)

    if tratamento == "rajada":
        pronto = {"tipo": "rajada",
                  "base": cobrir_foco(im, L, A, ler_foco(clip.get("fonte_imagem"))) or cobrir(im, L, A),
                  "capa": faixa_texto(texto, clip_leg=clip_leg)}
        if destaque is not None:
            # A rajada nao se mexe: a foto fica onde o corte a pos, e a zona com ela.
            destaque["foto"] = caixa_da_rajada(im.size, ler_foco(clip.get("fonte_imagem")))
            fora = destaque_fora_do_ecra(destaque, *destaque["foto"])
            if fora > DESTAQUE_FORA_AVISO:
                print("  destaque do clip %s: na rajada a foto enche o ecra e o corte deixa %d%% da "
                      "zona de fora; marca o ponto de foco dentro da zona"
                      % (clip.get("ordem", "?"), round(100 * fora)))
            pronto["destaque"] = destaque
        return pronto

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
              "capa": faixa_texto(texto, clip_leg=clip_leg), "mov": mov}
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
        if destaque is not None:
            # O APROXIMA FECHA NO PONTO DE FOCO, e a zona vai com a foto: se o ponto de foco nao
            # estiver dentro dela, no fim a zona pode ficar fora do ecra. Conta-se no fim do
            # movimento, com o tamanho e o centro que o aproxima_quadro() la vai usar.
            larg1, alt1 = aproxima_tamanho(ap, 1.0 + (az - 1.0) * aproxima_curva(1.0))
            fora = destaque_fora_do_ecra(destaque, ap["fim"][0] - larg1 / 2.0,
                                         ap["fim"][1] - alt1 / 2.0, larg1, alt1)
            if fora > DESTAQUE_FORA_AVISO:
                print("  destaque do clip %s: no fim do aproxima %d%% da zona fica fora do ecra; "
                      "poe o ponto de foco dentro da zona, ou baixa o zoom"
                      % (clip.get("ordem", "?"), round(100 * fora)))
    if destaque is not None:
        pronto["destaque"] = destaque
    return pronto


def desenhar(pronto, t_rel, duracao):
    """Um fotograma do clip, no instante t_rel."""
    if pronto["tipo"] == "cartao":
        if pronto.get("let") is not None:
            return desenhar_letreiro(pronto["let"], t_rel, LETREIRO_ENTRA)
        tela = Image.new("RGB", (L, A), (0, 0, 0))
        tela.paste(pronto["base"], (0, 0))
        return tela
    if pronto["tipo"] == "nome":
        return desenhar_letreiro(pronto["let"], t_rel, NOME_ENTRA)
    if pronto["tipo"] == "contador":
        # O modo foi decidido no preparar, e so la: um clip preparado como anos desenha
        # sempre anos, mesmo que as duas datas de onde veio ainda estejam no texto.
        desenho = linha_tempo.datas if pronto.get("modo") == "datas" else linha_tempo.anos
        if "parado" in pronto:
            # PARADO NA CHEGADA (clip.cp, 3 de outubro): o contador anda no tempo de sempre, a
            # duracao menos os segundos parados, e fica no ultimo fotograma ate ao fim do clip, com
            # o rotulo da chegada aceso. A data inteira da chegada vai no de anos (`chegada`).
            anda = max(1.0 / FPS, duracao - pronto["parado"])
            extra = {"fim_aceso": True}
            if pronto.get("modo") != "datas" and pronto.get("chegada"):
                extra["chegada"] = pronto["chegada"]
            return desenho(L, A, pronto["de"], pronto["para"],
                           pronto["marcos"], min(t_rel, anda), anda, **extra)
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
        if pronto["capa"] is not None and not SEM_LEGENDAS:
            cor, mascara = pronto["capa"]
            tela.paste(cor, (0, 0), mascara)
        return tela
    if pronto["tipo"] == "marcos":
        # A FITA PARADA NA DATA ACESA, decisao 089: com "~segundos@instante" no texto a fita
        # anda no tempo de sempre ate ao instante (o meio da paragem do nascimento, palavra
        # acesa a 100%) e fica nesse fotograma ate ao fim do clip, enquanto os foguetes
        # acabam; so depois entra a foto do bebe. Sem "@" fica no ultimo fotograma da parte
        # que anda. Sem paragem nenhuma a conta e a de sempre, ao bit.
        segura = pronto.get("segura", 0.0)
        if segura > 0:
            anda = max(1.0 / FPS, duracao - segura)
            congela = pronto.get("congela")
            ate = anda - 1.0 / FPS if congela is None else min(congela, anda - 1.0 / FPS)
            return linha_tempo.meses(L, A, pronto["ano"], pronto["marcas"],
                                     min(t_rel, ate), anda, pronto["troco"],
                                     pronto.get("abre", True))
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
    if pronto["tipo"] == "mergulho":
        return desenhar_mergulho(pronto, t_rel, duracao)
    if pronto["tipo"] in LIMITES_MONTE:
        return desenhar_monte(pronto, t_rel, duracao)
    if pronto["tipo"] == "rajada":
        tela = pronto["base"].copy()
        if pronto.get("destaque") is not None:
            tela = destacar(tela, pronto["destaque"], *pronto["destaque"]["foto"], t_rel=t_rel)
        if pronto["capa"] is not None and not SEM_LEGENDAS:
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
        if pronto.get("destaque") is not None:
            tela = destaque_na_foto(tela, pronto["destaque"], sprite, escala, cx, cy, t_rel)
        if pronto["capa"] is not None and not SEM_LEGENDAS:
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
    if pronto.get("destaque") is not None:
        tela = destaque_na_foto(tela, pronto["destaque"], pronto["sprite"], escala, L / 2.0, A / 2.0, t_rel)
    if pronto["capa"] is not None and not SEM_LEGENDAS:
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

    # A DURACAO QUE CADA FAIXA TEM NO FILME INTEIRO, com o cruzamento que la leva, para a
    # medida do nivel (falta_ao_loudnorm, decisao 087). Um render parcial corta as faixas no
    # --ate, e a medida sobre o bocado cortado dava outro ganho: um parcial ate aos 80 s tocava
    # o Rei Leao 2 dB abaixo do que o filme vai ter (revisores, 28 de setembro). Com a medida
    # sobre a faixa inteira, o parcial soa como o filme; no filme inteiro nada muda.
    def fala(r):
        return bool((r.get("voz") or "").strip()) or bool((r.get("video") or "").strip())
    no_filme = {}
    for r in linhas:
        fim_r = float(r["quando_s"]) + float(r["dura_s"])
        cruza = (not fala(r)) and any(
            x is not r and not fala(x) and abs(float(x["quando_s"]) - fim_r) < 0.35 for x in linhas)
        no_filme[id(r)] = float(r["dura_s"]) + (CRUZAMENTO if cruza else 0.0)

    entradas = []
    for r in linhas:
        quando = float(r["quando_s"])
        dura = min(float(r["dura_s"]), max(0.0, fim_corpo - quando))
        if dura <= 0.4:
            continue
        entradas.append({"ficheiro": r["ficheiro"], "caminho": r["caminho"],
                         "dura_medida": no_filme[id(r)],
                         "quando": quando, "in_s": float(r["in_s"] or 0),
                         "dura": dura, "ganho": float(r.get("ganho") or 1.0),
                         "encontrado": "Sim", "cruza": 0.0,
                         "voz": bool((r.get("voz") or "").strip()),
                         "video": bool((r.get("video") or "").strip()),
                         "abafar": ler_abafar(r.get("abafar"))})
        # AS COLUNAS DA 094 E DA 096, que o montar_da_mesa.py so escreve quando ha o que dizer:
        # a subida desta faixa, e o fim de frase (sai_s, em segundos do ficheiro) com a cauda.
        for coluna in ("subida", "sai_s", "cauda"):
            valor = str(r.get(coluna) or "").strip()
            if valor:
                # Uma celula mal escrita nao pode matar o render ao fim de meia hora: o som so se
                # constroi depois de os fotogramas todos estarem desenhados. Ignora-se essa coluna.
                try:
                    entradas[-1]["_" + coluna] = float(valor.replace(",", "."))
                except ValueError:
                    print("  AVISO: %s, coluna %s com %r, que nao e um numero: fica de fora"
                          % (r["ficheiro"][:40], coluna, valor))

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
    subidas_e_descidas(pela_hora, fim_corpo)
    return entradas


# A MUSICA QUE SAI ACABA NO FIM DA FRASE, decisao 096. Ate 29 de setembro a que saia descia sempre
# CRUZAMENTO segundos a partir do corte, estivesse onde estivesse, e quase sempre apanhava o comeco
# da frase seguinte: duas vozes ao mesmo tempo, ou uma linha nova a morrer por baixo da outra
# musica. O Tiago: "nota-se cortes e arranques de outras". Cada troca foi medida (um agente analisa,
# outro verifica) e o fim de frase ficou em data/fins_de_frase.csv; o montar poe-no na faixa que sai
# (sai_s e cauda) quando a musica chega ao corte no mesmo sitio do ficheiro, e avisa quando nao.
#
# E A SUBIDA E A DESCIDA DE CADA FAIXA, decisao 094. A que entra num inicio (in no zero, ou quase
# silencio antes e som logo a seguir) ou num ataque (o montar escreve a subida, 095 e 097) entra sem
# rampa; a que entra a meio e cruza com a que sai sobe no mesmo tempo em que a outra desce; as curvas
# sao de potencia igual (afade curve=qsin), sem o vale a meio que as rectas davam. Os efeitos, as
# vozes e o som dos videos ficam como estavam.
SUBIDA_NUM_INICIO = 0.03
EFEITOS_SOM = ("Candidato a vereador", "rebobinar")


def _nivel_dbfs(caminho, a, b):
    if b <= a or not caminho or not os.path.exists(caminho):
        return None
    try:
        r = subprocess.run([ffmpeg(), "-v", "error", "-ss", "%.3f" % max(0.0, a), "-t", "%.3f" % (b - max(0.0, a)),
                            "-i", caminho, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                           capture_output=True)
    except OSError:
        return None
    n = len(r.stdout) // 2
    if not n:
        return None
    import struct
    amostras = struct.unpack("<%dh" % n, r.stdout[:2 * n])
    rms = math.sqrt(sum(x * x for x in amostras) / n) / 32768.0
    return 20 * math.log10(max(1e-6, rms))


def entra_num_inicio(e):
    """In no zero, ou quase silencio nos 0,4 s antes do in e som logo a seguir (decisao 094)."""
    if e["in_s"] < 0.05:
        return True
    antes = _nivel_dbfs(e.get("caminho"), e["in_s"] - 0.4, e["in_s"])
    depois = _nivel_dbfs(e.get("caminho"), e["in_s"], e["in_s"] + 0.4)
    return antes is not None and depois is not None and antes < -40 and depois - antes > 15


def e_efeito_de_som(e):
    return e["ficheiro"].startswith(EFEITOS_SOM)


# UM FIM DE FRASE LONGE DO CORTE E UM ERRO DE ESCRITA, e nao uma frase: os da 096 ficam todos entre
# 1,3 s antes e 1,1 s depois do corte. Um sai_s de 4,755 em vez de 47,55 calava o Rei Leao ao fim de
# 0,5 s e deixava o bloco dele mudo, sem aviso (revisores, 30 de setembro).
TOLERANCIA_FIM_DE_FRASE = 3.0


def subidas_e_descidas(pela_hora, fim_corpo):
    """Poe em cada faixa de musica a curva, a subida e, com fim de frase, a descida (094, 096)."""
    leitos = [e for e in pela_hora if not entra_depressa(e) and not e_efeito_de_som(e)]
    # AS SUBIDAS PRIMEIRO, com os cruzamentos de sempre: a de uma faixa que entra a meio e cruza e o
    # tempo em que a outra desce (094).
    for e in leitos:
        e["curva"] = "qsin"
        if "_subida" in e:
            e["subida"] = e["_subida"]
        elif entra_num_inicio(e):
            e["subida"] = SUBIDA_NUM_INICIO
        else:
            anterior = [x for x in leitos if x is not e and x.get("cruza")
                        and abs((x["quando"] + x["dura"] - x["cruza"]) - e["quando"]) < 0.35]
            if anterior:
                e["subida"] = anterior[0]["cruza"]
    # DEPOIS O FIM DE FRASE (096): muda o fim da faixa e a descida, e ela deixa de cruzar. Se acabar
    # no corte ou antes, a que entra sobe no tempo da cauda, salvo se o montar escreveu outra subida.
    for i, e in enumerate(leitos):
        if "_sai_s" not in e:
            continue
        cauda = e.get("_cauda", 0.8)
        no_corte = e["in_s"] + e["dura"] - e["cruza"]
        corte_t = e["quando"] + e["dura"] - e["cruza"]
        if not (e["in_s"] < e["_sai_s"] and abs(e["_sai_s"] - no_corte) <= TOLERANCIA_FIM_DE_FRASE):
            print("  AVISO: %s com fim de frase aos %.2f s do ficheiro, e chega ao corte aos %.2f: "
                  "longe de mais, fica a descer no corte" % (e["ficheiro"][:40], e["_sai_s"], no_corte))
            continue
        e["dura"] = max(0.5, min(e["_sai_s"] - e["in_s"] + cauda, fim_corpo - e["quando"]))
        # O loudnorm mede o troco que toca, e nao o de antes (087).
        e["dura_medida"] = max(0.5, e["_sai_s"] - e["in_s"] + cauda)
        e["descida"] = cauda
        seguinte = next((x for x in leitos if x is not e and abs(x["quando"] - corte_t) < 0.35), None)
        if seguinte is not None and "_subida" not in seguinte and e["_sai_s"] <= no_corte + 0.05:
            seguinte["subida"] = cauda
        e["cruza"] = 0.0


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


# O NIVEL DE CADA LEITO NO FILME, decisao 087.
#
# O loudnorm de uma passagem guarda tres segundos de antecipacao e decide o ganho com eles.
# Uma musica que ARRANCA muito mais alto do que o resto do troco fica toda em baixo: medido a
# 28 de setembro, o Rei Leao (arranque +6,0 dB acima do troco) saia a -25,4 LUFS no filme, a
# retoma do Lang Lang (+3,4) a -25,2 e a Fome de Viagem (+5,6) a -25,0, contra os -21,9 do
# resto. Nao e o alcance dinamico: a Mariah tem LRA 13,2 e sai certa. Com projecao e as colunas
# do DJ um volume serve o filme inteiro, e 3,5 dB a menos num bloco inteiro ouve-se.
#
# O loudnorm fica como esta, e e por isso que os leitos certos nao mudam um bit. Mede-se a
# saida dele NESTE troco (mesmo in, mesma duracao) e, se estiver a mais de TOLERANCIA_LEITO_DB
# do alvo, multiplica-se o ganho da faixa pela diferenca. O ganho da montagem continua a
# significar o mesmo por cima: os foguetes a 2,0 ficam o dobro do leito. O alvo a saida do
# loudnorm e -21,9 menos o +0,54 dB que o alimiter da mistura acrescenta (1/0,94).
# Duas passagens com linear=true foram medidas e rejeitadas: acertavam nos tres mas mudavam
# a Mariah, a Clara e os Queen, que estavam certos.
NORMA_LEITO = "loudnorm=I=-23:TP=-2:LRA=11"
LEITO_NO_FILME_LUFS = -21.9
LEITO_SAIDA_LUFS = LEITO_NO_FILME_LUFS - 20 * math.log10(1 / 0.94)
TOLERANCIA_LEITO_DB = 1.0
_FALTA_LOUDNORM = {}


def falta_ao_loudnorm(ff, e):
    """dB que faltam a saida do loudnorm DESTE troco para LEITO_SAIDA_LUFS; 0.0 sem medida.

    Uma medida que falha nao para o render: fica o ganho de sempre. Guardado por ficheiro,
    tamanho, data, entrada e duracao, porque as fatias e o render inteiro pedem o mesmo.
    """
    dura = e.get("dura_medida") or e["dura"]
    chave = (e["caminho"], os.path.getsize(e["caminho"]), os.path.getmtime(e["caminho"]),
             round(e["in_s"], 3), round(dura, 3))
    if chave in _FALTA_LOUDNORM:
        return _FALTA_LOUDNORM[chave]
    falta = 0.0
    try:
        r = subprocess.run(
            [ff, "-hide_banner", "-nostats", "-ss", "%.3f" % e["in_s"], "-t", "%.3f" % dura,
             "-i", e["caminho"], "-map", "0:a:0", "-af",
             "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,%s,"
             "ebur128=framelog=quiet" % NORMA_LEITO, "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        achado = re.findall(r"^\s*I:\s+(-?[\d.]+) LUFS", r.stderr or "", re.M)
        if achado and float(achado[-1]) > -70.0:
            falta = LEITO_SAIDA_LUFS - float(achado[-1])
    except Exception:
        falta = 0.0
    _FALTA_LOUDNORM[chave] = falta
    return falta


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
        descida = e.get("descida") or (VOZ_FADE if voz else max(1.0, e.get("cruza", 0.0)))
        subida = e.get("subida") or (VOZ_FADE if voz else (1.0 if e["quando"] > 0.05 else 0.4))
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
        norma = "" if voz else NORMA_LEITO + ","
        # E O LOUDNORM DE UMA PASSAGEM NEM SEMPRE ACERTA, decisao 087: mede-se o que ele fez
        # a este troco e acerta-se o ganho, ver falta_ao_loudnorm().
        if not voz:
            falta = falta_ao_loudnorm(ff, e)
            if abs(falta) > TOLERANCIA_LEITO_DB:
                print("  %s: o loudnorm deixou-a a %+.1f dB do alvo, corrijo o ganho"
                      % (e["ficheiro"][:40], -falta))
                e = dict(e, ganho=round(e.get("ganho", 1.0) * 10 ** (falta / 20.0), 3))
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
            "afade=t=in:st=0:d=%.2f:curve=%s,afade=t=out:st=%.3f:d=%.2f:curve=%s,"
            "%s,adelay=%d|%d[a%d]"
            % (i, norma, subida, e.get("curva", "tri"), max(0.0, e["dura"] - descida), descida,
               e.get("curva", "tri"),
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


def caminho_do_final(pasta, base_nome, sufixo=""):
    """O caminho do filme: pasta/base_nome + sufixo + .mp4, ou base_nome_2 + sufixo, _3... se ja existir.

    O SUFIXO FICA SEMPRE NO FIM DO NOME, DEPOIS DO NUMERO (corretor, 2 de outubro). O filme sem
    legendas (o "_sem_legendas") nunca pode passar por um filme da sala: o ponto5 procura o render
    mais recente pelos nomes que acabam num algarismo (v3_*[0-9].mp4). Com o numero depois do
    sufixo, dois renders --sem-legendas no mesmo minuto davam "..._sem_legendas_2.mp4", que acaba
    num algarismo, e um --master sem --filme fazia o ficheiro da sala sem legendas. Sem sufixo, o
    nome e o de sempre.
    """
    final = os.path.join(pasta, base_nome + sufixo + ".mp4")
    k = 2
    while os.path.exists(final):
        final = os.path.join(pasta, "%s_%d%s.mp4" % (base_nome, k, sufixo))
        k += 1
    return final


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


def carregar_montagem(nome, ate, falar=True):
    """Tudo o que o render conta antes de desenhar, numa funcao so, para o pai e para as fatias.

    Le a montagem e o inventario, poe em cada clip o ficheiro que o data/finais.csv manda
    abrir, liga os encadeados e corta no --ate. Devolve o estado de que fotograma() precisa.
    O pai e cada fatia partem daqui, e por isso contam o mesmo desvio, o mesmo fim e o
    mesmo numero de fotogramas: um que contasse de outra maneira desenhava outro filme.

    E O ESTILO DA MESA PASSA A VALER AQUI (2 de outubro), pela mesma razao: o pai e cada fatia
    leem o mesmo <nome>.estilo.json da mesma pasta, e desenham com as mesmas letras e cores. Sem
    ficheiro volta o de sempre, mesmo que este processo tenha feito antes outra montagem com
    estilo. `falar` e falso nas fatias: o pai ja disse o que havia a dizer do estilo.
    """
    caminho_csv = os.path.join(MONTAGENS, nome + ".csv")
    with open(caminho_csv, encoding="utf-8-sig", newline="") as fh:
        clips = list(csv.DictReader(fh))
    avisos_estilo = []
    estilo = aplicar_estilo(ler_estilo(nome), avisos_estilo)
    if falar:
        for a in avisos_estilo:
            print("  AVISO: %s" % a)
        if estilo:
            print("  estilo da Mesa: %s" % ", ".join(
                "%s.%s=%s" % (parte, chave, v) for parte in sorted(estilo) for chave, v in sorted(estilo[parte].items())))
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
    # OS TEXTOS QUE NAO SAEM COMO ESTAO ESCRITOS (2 de outubro): um caracter que nem a letra nem a de
    # emojis tem (caixa vazia), ou um emoji de varios caracteres que esta Pillow nao junta. Os emojis
    # simples saem a cores e nao se dizem. So o pai fala; o montar ja o disse antes.
    if falar:
        for a in avisos_dos_textos(resto):
            print("  AVISO: %s" % a)
        # a legenda numa linha que nao cabe, e a posicao que nao chega onde foi pedida (3 de outubro)
        for a in avisos_das_legendas(resto):
            print("  AVISO: %s" % a)

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

    nomes = [c for c, _im in camadas if c["tipo"] == "nome"]
    if nomes:
        nome = dict(nomes[0], _pronto=prontos[nomes[0]["ordem"]])
        camadas = [(nome if c is nomes[0] else c, im) for c, im in camadas]
        quadro = compor_nome(camadas, nome, t)
    elif len(camadas) == 1:
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
    # O --sem-legendas desenha outros fotogramas, e por isso vai para cada fatia, como o estilo:
    # so no pai, o encoder recebia um fotograma com faixa e o seguinte sem ela, alternados. Sem
    # ele a linha de comando e a de sempre.
    if "--sem-legendas" in argv:
        cmd.append("--sem-legendas")
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
    # SO A COPIA DO TELEMOVEL, ate o Tiago dizer que e a versao final (27 de setembro): "ate eu
    # dizer que esta e a versao final e que quero fazer um de alta qualidade a versao do
    # telemovel e suficiente". Salta a copia leve, que eram 10 dos cerca de 57 minutos do render
    # de 23 de setembro, e faz a do telemovel direto do ficheiro final. O ficheiro final sai na
    # mesma: e ele que o desenho dos fotogramas produz, e e dele que a copia do telemovel sai.
    so_telemovel = "--so-telemovel" in sys.argv
    # O FILME PARA O DAVINCI (2 de outubro), ver SEM_LEGENDAS: sem a faixa de baixo, com o nome a
    # dize-lo, e as legendas num .srt a parte. Posto aqui a cada chamada, e nao so quando vem: um
    # main() corrido dentro de outro processo (os testes) nao herda o de uma chamada anterior.
    global SEM_LEGENDAS
    SEM_LEGENDAS = "--sem-legendas" in sys.argv
    # SO O FICHEIRO FINAL, sem a copia leve nem a do telemovel: o pacote do DaVinci so precisa dele,
    # e as duas copias eram 5 a 10 minutos a mais de um render que ja e o mais demorado.
    sem_copias = "--sem-copias" in sys.argv
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
    if "--saida" in sys.argv and fatia is None:
        # OUTRA PASTA PARA O FILME E PARA OS FICHEIROS DE TRABALHO (o _corpo, o _som, os videos de
        # abertura): o pacote do DaVinci faz tudo dentro da sua pasta nova, e nada do que la fica
        # escreve por cima de um ficheiro de outro render. Sem ele e a SAIDA de sempre.
        global SAIDA
        SAIDA = sys.argv[sys.argv.index("--saida") + 1]

    if fatia is None:
        ff = ffmpeg()
        os.makedirs(SAIDA, exist_ok=True)
    estado = carregar_montagem(nome, ate, falar=fatia is None)
    if fatia is not None:
        correr_fatia(estado, fatia[0], fatia[1], canal)
        return

    # UM GRUPO GRANDE PEDE MEMORIA EM CADA FATIA (decisao 087), e as fatias preparam o mesmo
    # clip ao mesmo tempo. Conta-se pelos pixeis verdadeiros do grupo mais pesado, com o que
    # fica dos grupos de antes que ainda nao sairam, e dispara pelo valor, ver
    # aviso_de_memoria() (1 de outubro).
    aviso = aviso_de_memoria(estado["clips"], fatias)
    if aviso:
        print(aviso)

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
    final = caminho_do_final(SAIDA, base_nome, "_sem_legendas" if SEM_LEGENDAS else "")
    if len(partes) == 1:
        os.replace(partes[0], final)
    else:
        lista = os.path.join(SAIDA, "_%s_lista.txt" % nome)
        with open(lista, "w", encoding="utf-8") as fh:
            for p in partes:
                fh.write("file '%s'\n" % p.replace("\\", "/"))
        # NO FILME PARA O DAVINCI, UM FOTOGRAMA A CADA 0,04 S, SEM BURACOS. O primeiro video de
        # abertura da 518 fotogramas para 20,8 s (o som e mais comprido do que a imagem), e a juncao
        # deixa um buraco de 0,12 s entre ele e o seguinte: um leitor segura o ultimo fotograma, um
        # programa de montagem pode contar fotogramas, e entao tudo o que vem a seguir chega 2
        # fotogramas mais cedo do que o .srt diz. Com fotogramas a cadencia certa o buraco enche-se
        # com o mesmo fotograma, que e o que o leitor ja mostrava, e as duas contas dao o mesmo. So
        # aqui: sem --sem-legendas a juncao e a de sempre, ao byte.
        cadencia = ["-fps_mode", "cfr", "-r", str(FPS)] if SEM_LEGENDAS else []
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "concat", "-safe", "0", "-i", lista]
                           + cadencia +
                           ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
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
    if os.path.exists(final) and not parcial and not so_telemovel and not sem_copias:
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
    if not sem_copias and ((so_telemovel and os.path.exists(final) and not parcial)
            or (leve and os.path.exists(leve) and os.path.getsize(leve) > 29 * 1048576)):
        movel = final[:-4] + "_telemovel.mp4"
        # POR TAMANHO ALVO, E NAO POR TENTATIVA. Isto era uma escada de qualidade, crf 28, 31
        # e 34, que parava na primeira que coubesse. A 23 de setembro, com o filme a 14:28,
        # nenhuma das tres coube, a escada acabou, e imprimia-se na mesma "Telemovel ... (31,7
        # MB)" como se estivesse feito: um ficheiro que nao cabe no envio nao serve para nada
        # e ninguem era avisado. Agora o debito sai da duracao e o encode e em duas passagens,
        # que e o modo em que o x264 acerta no tamanho pedido: cabe sempre, e o que varia e a
        # nitidez, que e o que pode variar numa copia de revisao.
        alvo = 28 * 1048576
        som_kbps = 96
        # A DURACAO DO FICHEIRO FINAL, com os videos de abertura, e nao so a do corpo: com o
        # `fim` do corpo o debito saia 4% alto de mais e a copia passava os 29 MB (revisores, 28
        # de setembro). Mede-se o ficheiro, como o registar_render() faz.
        dur_final = fim
        try:
            dur_final = float(subprocess.run(
                [os.path.join(os.path.dirname(ff), "ffprobe.exe"), "-v", "error",
                 "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", final],
                capture_output=True, text=True).stdout.strip()) or fim
        except (ValueError, OSError):
            dur_final = fim
        video_kbps = int(alvo * 8 / max(0.1, dur_final) / 1000.0) - som_kbps
        passlog = os.path.join(SAIDA, "_passlog_%s" % nome)
        comum = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", final,
                 "-vf", "scale=960:540:flags=lanczos", "-c:v", "libx264",
                 "-preset", "medium", "-b:v", "%dk" % max(80, video_kbps),
                 "-pix_fmt", "yuv420p", "-passlogfile", passlog]
        p1 = subprocess.run(comum + ["-pass", "1", "-an", "-f", "mp4", os.devnull],
                            capture_output=True, text=True)
        if p1.returncode == 0:
            subprocess.run(comum + ["-pass", "2", "-c:a", "aac", "-b:a", "%dk" % som_kbps,
                                    movel], capture_output=True, text=True)
        # NAO chamar "resto" a isto: e a lista dos clips do corpo, e o registar_render() la em
        # baixo conta-a; com o nome reutilizado o renders.csv registava 57 clips em vez de 225.
        for sobra in (passlog + "-0.log", passlog + "-0.log.mbtree"):
            if os.path.exists(sobra):
                os.remove(sobra)
        if os.path.exists(movel):
            mb = os.path.getsize(movel) / 1048576.0
            print("Telemovel: %s  (%.1f MB, video a %d kbps)" % (movel, mb, max(80, video_kbps)))
            if mb > 29:
                print("  ATENCAO: passa dos 29 MB e nao cabe no envio. Manda so um troco.")
        else:
            print("  NAO CONSEGUI FAZER A COPIA PARA O TELEMOVEL.")

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
