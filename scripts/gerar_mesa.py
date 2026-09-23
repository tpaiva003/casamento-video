# -*- coding: utf-8 -*-
"""Junta a Mesa de Montagem num unico ficheiro, pronto a publicar.

A pagina vive em tres pedacos, e ate aqui eu colava-os a mao de cada vez, o que
e a melhor maneira de um dia colar mal:

  scripts/editor_base.html   a pagina, o estilo e o comportamento
  data/editor_dados.js       as 376 fotografias, em folhas de miniaturas
  data/editor_montagens.js   as montagens que os scripts ja geraram

O sitio da cola e o comentario <!--DADOS-->, que existe uma so vez. Se alguem
lhe tocar, isto para, em vez de escrever um ficheiro partido em silencio.

PORQUE E QUE OS DADOS VAO POR DENTRO E NAO EM FICHEIROS AO LADO: a pagina
publicada e aberta no telemovel dele, muitas vezes sem o portatil por perto.
Um unico ficheiro nao tem como chegar meio.

Uso:  py -3.11 scripts/gerar_mesa.py
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "scripts", "editor_base.html")
DADOS = os.path.join(REPO, "data", "editor_dados.js")
MONTAGENS = os.path.join(REPO, "data", "editor_montagens.js")
SAIDA = os.path.join(REPO, "saida", "mesa.html")

MARCA = "<!--DADOS-->"

# AS VOZES DO PEDIDO. Os pedacos que ja cortamos da gravacao do pedido, para ele os
# escolher e ordenar na Mesa. A pasta so se le: nada se escreve, nada se renomeia.
VOZES = r"C:\casamento-video-media\gerados\pedido_pedacos"
EXT_VOZ = (".mp3", ".wav", ".m4a", ".wma", ".flac", ".ogg")

# OS VIDEOS QUE ELE PODE POR NA MONTAGEM. Ate 17 de setembro o nome do ficheiro escrevia-se
# a mao na Mesa, e uma letra trocada so dava sinal no render. Agora a Mesa recebe a lista e
# o comprimento de cada um, para o campo do ficheiro escolher e para o inspetor poder dizer
# que o troco nao cabe. A pasta so se le.
VIDEOS_NOVOS = r"C:\casamento-video-media\trabalho\03-NOVOS_VIDEOS"
EXT_VIDEO = (".mp4", ".mov", ".m4v", ".avi", ".mkv", ".wmv")

# OS VIDEOS QUE ELE AINDA NAO DECIDIU. A 01-NOVAS e onde ele larga o que nao estava no video
# da mae da Clara, e ate hoje so se olhava para as fotografias: seis videos estavam la sem
# ninguem saber. O Tiago, 22 de setembro: "Podemos meter visivel na Mesa de montagem, mas
# adicionar os videos depende sempre de eu escrever no chat e nao na mesa. Mas meter na mesa
# ajuda-me a lembrar que estao la."
#
# Por isso entram na lista COM A MARCA `novo`, e a Mesa nao os poe no campo de escolher o
# ficheiro: mostra-os num painel a parte, como o "Estado das fotos" mostra o que esta em disco
# sem fingir que age. Quem os poe no filme sou eu, a partir do chat.
#
# VARRE-SE POR INTEIRO, ao contrario da 03-NOVOS_VIDEOS: cinco dos seis estao em Novas_Novas,
# e o CLAUDE.md diz que a 01-NOVAS pode ter subpastas. As pastas `<nome>_files` sao despejos
# de paginas guardadas e saltam-se, como no inventario.py. A pasta so se le.
VIDEOS_POR_DECIDIR = r"C:\casamento-video-media\trabalho\01-NOVAS"


def _ffprobe():
    """O caminho do ffprobe, ou None quando nao ha ffmpeg neste PC.

    O render.ffmpeg() sai do programa quando nao o encontra, e uma Mesa sem as duracoes
    continua a ser util: aqui a falta apanha-se e diz-se.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import render
        return os.path.join(os.path.dirname(render.ffmpeg()), "ffprobe.exe")
    except (SystemExit, Exception):
        return None


def _duracao(pr, caminho):
    """Os segundos que o ficheiro tem, ou 0.0 quando nao se consegue medir."""
    if not pr:
        return 0.0
    import subprocess
    try:
        r = subprocess.run(
            [pr, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", caminho],
            capture_output=True, text=True)
        return round(float(r.stdout.strip()), 2)
    except Exception:
        return 0.0


def _tamanho(pr, caminho):
    """(largura, altura) do video, ou (0, 0) quando nao se consegue medir.

    MEDE-SE PELA MESMA RAZAO POR QUE A DURACAO SE MEDE: e o numero que diz se um video da
    01-NOVAS chega para encher o ecra, e escrito a mao aqui envelhecia no dia em que ele
    largasse outro ficheiro na pasta. So se mede o que leva a marca `novo`, que sao seis.
    """
    if not pr:
        return 0, 0
    import subprocess
    try:
        r = subprocess.run(
            [pr, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "default=nw=1:nk=1", caminho],
            capture_output=True, text=True)
        p = r.stdout.split()
        return int(p[0]), int(p[1])
    except Exception:
        return 0, 0


def vozes_do_pedido():
    """[{f, dura}] dos pedacos que estiverem na pasta, pelo nome, com a duracao medida.

    A DURACAO MEDE-SE, NAO SE LE DO NOME. Os nomes trazem "dura36.5s" de quando foram
    cortados, mas ele ja renomeou uns e apagou outros: a lista e a que estiver na pasta,
    e o numero tem de vir do ficheiro, senao a Mesa diz um tempo e o video faz outro.

    Sem a pasta devolve lista vazia, e a Mesa diz que nao ha vozes.
    """
    if not os.path.isdir(VOZES):
        return []
    nomes = sorted(f for f in os.listdir(VOZES) if f.lower().endswith(EXT_VOZ))
    if not nomes:
        return []
    pr = _ffprobe()
    saida = []
    for f in nomes:
        d = _duracao(pr, os.path.join(VOZES, f))
        if not d:
            print("  AVISO: nao consegui medir a voz %s; a Mesa mostra 0 s" % f)
        saida.append({"f": f, "dura": d})
    return saida


def _videos_das_montagens():
    """Os nomes de video escritos nas montagens que ja existem. Sao os nossos CSV, poucos."""
    import csv
    pasta = os.path.join(REPO, "data", "montagens")
    nomes = set()
    if not os.path.isdir(pasta):
        return nomes
    for f in sorted(os.listdir(pasta)):
        if not f.endswith(".csv") or f.endswith(".som.csv"):
            continue
        try:
            with open(os.path.join(pasta, f), encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    if r.get("tipo") == "video" and (r.get("ficheiro") or "").strip():
                        nomes.add(r["ficheiro"].strip())
        except OSError:
            continue
    return nomes


def videos_do_projeto():
    """[{f, dura}] dos videos que ele pode escolher na Mesa, pelo nome, com a duracao medida.

    DE ONDE SAEM. Da pasta 03-NOVOS_VIDEOS, que e onde ele larga os videos novos, e dos
    nomes que o render ja conhece na render.VIDEOS, que e por onde a fanfarra e a historia
    da Clara entram (a `intro_clara_tiago.mp4` vive na pasta de saida, a `Clara e Tiago-2.mp4`
    na 00-ORIGINAL-MAE).

    PORQUE E QUE A PASTA DE SAIDA NAO SE VARRE INTEIRA: a 17 de setembro tinha 51 ficheiros
    .mp4 e 50 deles eram renders nossos, alguns de 280 MB. Poe-los na lista dava-lhe 51
    escolhas onde ha uma so que e material. Da saida entra o que o render nomeia, e mais nada.

    A DURACAO MEDE-SE. E dela que sai o aviso de o troco nao caber no ficheiro, e um numero
    escrito a mao aqui deixava passar um troco que o render depois corta sem se queixar.
    """
    caminhos = {}
    if os.path.isdir(VIDEOS_NOVOS):
        for f in sorted(os.listdir(VIDEOS_NOVOS)):
            if f.lower().endswith(EXT_VIDEO):
                caminhos[f] = os.path.join(VIDEOS_NOVOS, f)
    # E OS QUE ESTAO NA 01-NOVAS E AINDA NAO FORAM DECIDIDOS, com subpastas e tudo (ver
    # VIDEOS_POR_DECIDIR). Entram na lista para o comprimento se saber, e levam a marca mais
    # abaixo; um que ja esteja numa montagem ja foi decidido e nao a leva.
    por_decidir = set()
    if os.path.isdir(VIDEOS_POR_DECIDIR):
        for base, pastas, fs in os.walk(VIDEOS_POR_DECIDIR):
            pastas[:] = [p for p in pastas if not p.endswith("_files")]
            for f in sorted(fs):
                if f.lower().endswith(EXT_VIDEO) and f not in caminhos:
                    caminhos[f] = os.path.join(base, f)
                    por_decidir.add(f)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import render
        # so o caminho da tabela; o caminho_de_video() cai num os.walk de toda a pasta de
        # media quando falha, e isso aqui custava minutos por um nome que nao existe
        for nome, (caminho, _corte) in render.VIDEOS.items():
            if nome not in caminhos and os.path.exists(caminho):
                caminhos[nome] = caminho
    except Exception:
        print("  AVISO: nao consegui ler a tabela de videos do render.py")
    # E OS QUE AS MONTAGENS JA USAM. O "20th Century Fox   Abertura Classic.mp4" das v1a,
    # v1b e v1c nao esta na 03-NOVOS_VIDEOS nem na tabela do render: mora numa pasta do
    # WeTransfer dentro do material original. O render encontra-o na mesma e o montar
    # tambem; so a Mesa e que nao o conhecia, e no inspetor daquele clip aparecia "nao esta
    # nas pastas dos videos", que e um aviso a mentir sobre um ficheiro que existe.
    #
    # PROCURA-SE SO ESTES NOMES, e nao a pasta de media inteira: sao os que estao escritos
    # nos nossos CSV, meia duzia, e e por isso que se pode pagar a procura do render.
    for nome in sorted(_videos_das_montagens()):
        if nome in caminhos:
            continue
        try:
            import render
            caminho, _corte = render.caminho_de_video(nome)
        except Exception:
            caminho = None
        if caminho and os.path.exists(caminho):
            caminhos[nome] = caminho
    if not caminhos:
        return []
    pr = _ffprobe()
    nas_montagens = _videos_das_montagens()
    saida = []
    for f in sorted(caminhos):
        d = _duracao(pr, caminhos[f])
        if not d:
            print("  AVISO: nao consegui medir o video %s; a Mesa mostra 0 s" % f)
        peca = {"f": f, "dura": d}
        # UM QUE JA ESTEJA NUMA MONTAGEM JA FOI DECIDIDO: a marca cai sozinha quando eu o
        # puser no filme, e nao ha um segundo sitio onde alguem se tenha de lembrar de a tirar.
        if f in por_decidir and f not in nas_montagens:
            peca["novo"] = True
            lar, alt = _tamanho(pr, caminhos[f])
            if lar:
                peca["lar"], peca["alt"] = lar, alt
        saida.append(peca)
    return saida


def musicas_do_projeto():
    """Os nomes das musicas que estao em disco, para a Mesa poder dizer que um nome nao existe.

    SO OS NOMES, e nao a duracao: sao 54 ficheiros e medi-los com o ffprobe custa minutos a
    cada geracao da Mesa, para um aviso que se faz com o nome. Se um dia for preciso avisar
    que o segundo de entrada cai para alem do fim da faixa, ai mede-se.

    A PROCURA E A MESMA DO MONTAR, de proposito: montar_da_mesa.caminhos_de_musica(). Duas
    procuras diferentes davam uma Mesa a dizer que falta o que o render encontra, e o campo
    da musica e texto livre: ate aqui o nome so se confirmava no render, e um leito que nao
    resolve corta o anterior e nao poe nada no lugar, ou seja o filme fica mudo dali para a
    frente (foi o que aconteceu a 14 de setembro, decisao 049).
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import montar_da_mesa
        return sorted(montar_da_mesa.caminhos_de_musica().keys())
    except (SystemExit, Exception):
        # COMO NO _ffprobe(): uma Mesa sem a lista continua a ser util, e o musicaConhecida()
        # da pagina cala-se quando a lista vem vazia. Nunca vale a pena parar a geracao aqui.
        print("  AVISO: nao consegui listar as musicas; a Mesa nao confirma os nomes")
        return []


def main():
    base = io.open(BASE, encoding="utf-8").read()

    # A regra que me custou metade do editor uma vez: confirmar que o marcador
    # aparece exatamente uma vez ANTES de cortar por ele.
    n = base.count(MARCA)
    if n != 1:
        sys.exit("O marcador %s aparece %d vezes em editor_base.html. "
                 "Tem de aparecer uma." % (MARCA, n))

    pedacos = []
    for caminho in (DADOS, MONTAGENS):
        if not os.path.exists(caminho):
            sys.exit("Falta %s. Corre primeiro gerar_editor.py e "
                     "gerar_montagens_editor.py." % os.path.basename(caminho))
        pedacos.append(io.open(caminho, encoding="utf-8").read())

    # O ESTADO DAS FOTOGRAFIAS vai tambem dentro da Mesa, para o botao "Estado
    # das fotos" mostrar o que esta pronto e o que falta, com a data do retrato.
    estado = "null"
    caminho_estado = os.path.join(REPO, "data", "estado_fotos.json")
    if os.path.exists(caminho_estado):
        estado = io.open(caminho_estado, encoding="utf-8").read().strip() or "null"
    else:
        print("  AVISO: falta data/estado_fotos.json, corre scripts/estado_fotos.py")

    # O INDICE DAS PREVIAS GRANDES diz em que folha e em que celula esta cada
    # foto. As folhas vao como ficheiros ao lado da pagina, em previas/.
    previas = "null"
    caminho_previas = os.path.join(REPO, "saida", "previas", "indice.json")
    if os.path.exists(caminho_previas):
        previas = io.open(caminho_previas, encoding="utf-8").read().strip() or "null"
    else:
        print("  AVISO: falta saida/previas/indice.json, corre scripts/gerar_previas.py")

    # A BANDA SONORA COMO O RENDER A TOCA, e as duracoes que o script mudou. Sai dos
    # mesmos data/montagens/v3.csv e v3.som.csv que o render usa, para a Mesa mostrar
    # tambem o que os scripts poem sozinhos (ver som_para_mesa.py).
    import json
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import som_para_mesa
    som = som_para_mesa.som_para_mesa()
    if som is None:
        print("  AVISO: sem data/montagens/v3.csv e v3.som.csv, a Mesa nao mostra o som do render")

    vozes = vozes_do_pedido()
    if not vozes:
        print("  AVISO: sem %s, a Mesa nao tem vozes do pedido para escolher" % VOZES)

    videos = videos_do_projeto()
    if not videos:
        print("  AVISO: sem videos, a Mesa pede o nome do ficheiro escrito a mao")

    musicas = musicas_do_projeto()

    corpo = base.replace(
        MARCA,
        "<script>\n%s\n</script>\n<script>\n%s\n</script>\n<script>\nwindow.ESTADO_FOTOS = %s;\nwindow.PREVIAS = %s;\nwindow.SOM_RENDER = %s;\nwindow.VOZES = %s;\nwindow.VIDEOS = %s;\nwindow.MUSICAS = %s;\n</script>"
        % (pedacos[0], pedacos[1], estado, previas, json.dumps(som, ensure_ascii=False),
           json.dumps(vozes, ensure_ascii=False), json.dumps(videos, ensure_ascii=False),
           json.dumps(musicas, ensure_ascii=False)),
        1)

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="\n").write(corpo)

    print("Mesa de Montagem: %s" % SAIDA)
    print("  pagina      %8.1f KB" % (len(base) / 1024.0))
    print("  fotografias %8.1f KB" % (len(pedacos[0]) / 1024.0))
    print("  montagens   %8.1f KB" % (len(pedacos[1]) / 1024.0))
    print("  vozes       %8d pedacos do pedido" % len(vozes))
    print("  videos      %8d para escolher" % len(videos))
    espera = [v for v in videos if v.get("novo")]
    if espera:
        print("  por decidir %8d na 01-NOVAS, so para ele ver na Mesa" % len(espera))
    print("  musicas     %8d em disco, para confirmar os nomes" % len(musicas))
    print("  total       %8.1f KB" % (len(corpo) / 1024.0))
    if len(corpo.encode("utf-8")) > 15 * 1024 * 1024:
        print("  AVISO: acima de 15 MB, o limite de publicacao e 16.")


if __name__ == "__main__":
    main()
