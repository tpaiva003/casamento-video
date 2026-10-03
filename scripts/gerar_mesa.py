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
import re
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_previas  # noqa: E402 - aqui em cima e nao no main(): mexe no sys.stdout ao ser importado

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


# AS LETRAS DO ESTILO (2 de outubro). O Tiago, para o dia com a Clara: "tamanho da letra" e "tipo
# da letra". O painel Estilo da Mesa oferece as letras de data/fontes.json, e a amostra e a
# pre-visualizacao desenham-nas no browser com a familia `web`; as que nao vem com o Windows pedem-se
# ao Google Fonts pelo `web_google`. O render nao usa nada disto: abre o `ficheiro` de cada letra.
FONTES = os.path.join(REPO, "data", "fontes.json")
# so o que a pagina usa; o caminho do ficheiro fica no PC, e a Mesa so precisa de saber se ele la esta
# hastes_finas (opcional): a letra de traco fino que se perde a 15 m antes do espaco entre as letras;
# sem o campo, a Mesa conta as manuscritas e o Cormorant e o Playfair (estiloHastesFinas)
CAMPOS_DA_LETRA = ("id", "nome", "web", "web_google", "peso_css", "estilo_css", "so_maiusculas",
                   "corpo_minimo", "do_convite", "manuscrita", "a_descarregar", "hastes_finas")
# O LETREIRO DA INTRO E EM IMPACT POR OMISSAO (decisao 084), «como esta». Desde 2 de outubro, a noite, a
# letra pode trocar-se, mas so pelas de data/fontes_intro.json com oferecida true, e a amostra dessas
# desenha-se com as mascaras do proprio letreiro do render (fontes_intro_para_mesa). O Anton fica SO para a
# amostra do Impact: os telemoveis nao tem o Impact, e ela caia numa letra fina qualquer; e o mais parecido
# que o Google Fonts tem. O filme continua no Impact, ou na letra escolhida.
PARECIDA_COM_IMPACT = "Anton"
GOOGLE_FONTS = "https://fonts.googleapis.com/css2?"


def familias_google(pedidos):
    """Os pedidos `web_google` ("Cinzel:wght@700", "Cormorant+Garamond:ital,wght@1,400") -> as partes
    family= do endereco css2, UMA POR FAMILIA.

    PORQUE SE JUNTAM: o Cormorant Garamond e pedido tres vezes (700, 400 e o italico do convite) e o
    Cinzel duas. O css2 quer cada familia uma vez, com os pares (italico, peso) por ordem, e um
    endereco com a familia repetida arrisca vir recusado inteiro: era a Mesa sem nenhuma letra do
    Google, e as amostras todas no Arial sem ninguem perceber porque.
    """
    pares, ordem = {}, []
    for pedido in pedidos:
        if not pedido:
            continue
        nome, _, eixos = pedido.partition(":")
        if nome not in pares:
            pares[nome] = set()
            ordem.append(nome)
        if not eixos:
            pares[nome].add((0, 400))
            continue
        nomes, _, valores = eixos.partition("@")
        nomes = nomes.split(",")
        for tuplo in valores.split(";"):
            v = dict(zip(nomes, tuplo.split(",")))
            pares[nome].add((int(v.get("ital", 0)), int(v.get("wght", 400))))
    partes = []
    for nome in ordem:
        t = sorted(pares[nome])
        if t == [(0, 400)]:
            partes.append("family=" + nome)
        elif any(i for i, _p in t):
            partes.append("family=%s:ital,wght@%s" % (nome, ";".join("%d,%d" % x for x in t)))
        else:
            partes.append("family=%s:wght@%s" % (nome, ";".join(str(p) for _i, p in t)))
    return partes


def fontes_para_mesa():
    """{omissao, fontes, css} para o window.FONTES, ou None sem data/fontes.json.

    `em_disco` diz se o ficheiro que o render abre esta neste PC: uma letra que la nao esteja sai em
    Arial Bold no filme (o render avisa), e a Mesa diz isso antes de ele esperar meia hora. `css` e o
    endereco do Google Fonts com as letras que o Windows nao tem, mais o Anton da amostra da intro.
    """
    import json
    try:
        with io.open(FONTES, encoding="utf-8") as fh:
            dados = json.load(fh)
    except (OSError, ValueError) as erro:
        print("  AVISO: nao li %s (%s): o painel Estilo so oferece o Arial Bold" % (FONTES, erro))
        return None
    fontes = []
    for e in dados.get("fontes") or []:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str):
            continue
        x = {k: e[k] for k in CAMPOS_DA_LETRA if e.get(k) not in (None, False, "")}
        if "corpo_minimo" not in x:
            x["corpo_minimo"] = None          # null quer dizer "por medir", e a Mesa diz isso
        x["em_disco"] = bool(e.get("ficheiro")) and os.path.exists(e["ficheiro"])
        fontes.append(x)
    pedidos = [f.get("web_google") for f in fontes] + [PARECIDA_COM_IMPACT]
    return {"omissao": dados.get("omissao") or "arial_bold", "fontes": fontes,
            "css": GOOGLE_FONTS + "&".join(familias_google(pedidos)) + "&display=swap"}


# A LETRA DO LETREIRO DA INTRO (2 de outubro, a noite). O Tiago pediu para a mudar no Estilo, e ficou
# combinado: «Impact (como esta)» por omissao, e so as letras grossas o suficiente, cada uma com quanto da
# foto se ve por dentro dela. A medida e a lista estao em data/fontes_intro.json, e quem as le e o
# render.letras_da_intro() (so as oferecidas): a Mesa recebe as mesmas, pela `ordem` da medida.
#
# A AMOSTRA E O DESENHO DO RENDER. O browser nao tem a Bernard, a Showcard ou a Bahnschrift Condensed num
# telemovel, e a forma da letra e o que se esta a escolher: cada letra leva a mascara do letreiro feita pelo
# intro_flipbook.letreiro(), a mesma funcao que desenha a intro, a 1920 x 1080 e no tamanho de omissao (288),
# que tem de dar ao pixel a area_px medida. Vai a meio tamanho, branca com o alfa da mascara (PNG LA), como
# data URI dentro da pagina: oito imagens de uns 20 KB, nenhum ficheiro novo na publicacao. A Mesa encolhe-a
# ou estica-a a volta do centro para os outros tamanhos (a conta do letreiro e proporcional ao corpo do
# Impact). Uma mascara que nao da a area medida (a letra saiu do PC, e o letreiro caiu no Impact) nao vai, e a
# letra diz que nao esta no PC do render.
CAMPOS_DA_LETRA_DA_INTRO = ("id", "nome", "ordem", "pct_impact", "corpo_que_cabe", "corpo_minimo",
                            "tamanho_mesa_minimo", "area_px")


def mascara_da_letra_da_intro(ident):
    """(data URI, area) da mascara do letreiro na letra `ident`, como o intro_flipbook a desenha a 288.

    A area e a do letreiro inteiro a 1920 x 1080 (pixeis acima de 128), para se comparar com a area_px da
    medida; a imagem e a meio tamanho, branca, com a mascara no alfa.
    """
    import base64
    import contextlib
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import intro_flipbook
    from PIL import Image
    with contextlib.redirect_stdout(io.StringIO()):
        m = intro_flipbook.letreiro(int(intro_flipbook.L * 0.86), None, ident)
    area = sum(m.histogram()[129:])
    meia = m.resize((intro_flipbook.L // 2, intro_flipbook.A // 2), Image.LANCZOS)
    la = Image.merge("LA", (Image.new("L", meia.size, 255), meia))
    buf = io.BytesIO()
    la.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii"), area


def fontes_intro_para_mesa(mascaras=True):
    """{limiar_pct, letras} para o window.FONTES_INTRO, ou None sem data/fontes_intro.json.

    `letras` sao as oferecidas, pela `ordem` da medida (o Impact primeiro), cada uma com os campos de
    CAMPOS_DA_LETRA_DA_INTRO, `em_disco` (o ficheiro dela abre neste PC: o render.letra_da_intro() aceita-a) e,
    com mascaras=True, `mascara` (data URI) e `area_mascara`. Sem o ficheiro, ou com ele vazio, a Mesa so tem o
    Impact, como o render.
    """
    import json
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import render
        letras = render.letras_da_intro()
        with io.open(render.FONTES_DA_INTRO, encoding="utf-8") as fh:
            limiar = json.load(fh).get("limiar_pct")
    except Exception as erro:  # noqa: BLE001 - uma Mesa sem a lista continua a servir, so com o Impact
        print("  AVISO: nao li as letras da intro (%s): a aba Intro so oferece o Impact" % erro)
        return None
    if not letras:
        print("  AVISO: data/fontes_intro.json sem letras oferecidas: a aba Intro so oferece o Impact")
        return None
    saida = []
    for e in sorted(letras.values(), key=lambda x: (x.get("ordem") or 999, x["id"])):
        x = {k: e.get(k) for k in CAMPOS_DA_LETRA_DA_INTRO}
        avisos = []
        x["em_disco"] = e["id"] == render.INTRO_FONTE or render.letra_da_intro(e["id"], avisos) is not None
        if mascaras:
            try:
                uri, area = mascara_da_letra_da_intro(e["id"])
            except Exception as erro:  # noqa: BLE001 - sem a mascara a Mesa diz que nao tem a amostra
                print("  AVISO: nao fiz a mascara da letra %s (%s)" % (e["id"], erro))
                uri, area = None, None
            if area != e.get("area_px"):
                print("  AVISO: a mascara da letra %s tem %s px e a medida %s: fica sem amostra%s"
                      % (e["id"], area, e.get("area_px"), (" (%s)" % "; ".join(avisos)) if avisos else ""))
                uri = None
            x["mascara"], x["area_mascara"] = uri, area
        saida.append(x)
    return {"limiar_pct": limiar, "letras": saida}


# O QUE O RENDER JA SABE FAZER COM O QUE A MESA GRAVA (corretor, 2 de outubro). A Mesa grava os
# creditos (est.creditos) e o "uma so peca" do contador (est.estilo.contador.continuo) desde hoje, e a
# outra equipa liga o render a eles ao mesmo tempo. Ate estar ligado, a Mesa dizia "A ordem e a tua,
# feita aqui" e "Uma so peca ve-se no render", e um render feito a seguir saia com a ordem pelo numero
# da Mesa, os textos de hoje e o contador de sempre, sem ninguem saber. Pergunta-se ao codigo, na hora
# de montar a Mesa, em vez de o escrever a mao: quando a outra equipa acabar, a Mesa seguinte deixa de
# avisar sozinha.
PONTO5 = os.path.join(REPO, "scripts", "discussao", "ponto5_creditos.py")


def le_a_musica_dos_creditos(texto):
    """O ponto5_creditos.py (o texto dele) ja le o est.creditos.musica? (2 de outubro, a tarde)

    O contrato (seccao 6 do saida/discussao/contrato_mesa_1002.md) diz como: o ponto5 chama o
    musica_creditos.faixas_dos_creditos() com o (leitura.get("creditos") or {}).get("musica"). Conta
    qualquer das duas coisas escrita como codigo: a chamada, ou a chave "musica" lida com .get( ou [.
    Desde o ponto5 de 2 de outubro as 14:59 ha as duas (o som_dos_creditos chama o faixas_dos_creditos),
    e a Mesa deixou de dizer que a escolha nao chega ao filme. Se o ponto5 deixar de a ler, a Mesa montada
    a seguir volta a dize-lo sozinha, como nos creditos e no contador.
    """
    import re
    return bool(re.search(r"faixas_dos_creditos\s*\(", texto)
                or re.search(r"""(\.get\(\s*|\[\s*)["']musica["']""", texto))


def le_os_cargos_dos_creditos(texto):
    """O ponto5_creditos.py (o texto dele) ja le os cargos dele? (2 de outubro, a noite; contrato dos cargos e decisao 109)

    {cargos_primeiro, cargos_varios, cargos_max, pessoas_max}:
    - `cargos_primeiro`: le a chave est.creditos.cargos_primeiro (com .get( ou [), que poe os cargos antes do rolo;
    - `cargos_varios`: tem os limites da lista (CARGOS_MAX, PESSOAS_MAX = 8, 4) e desenha cada cargo pela
      geometria_do_cargo(), com as pessoas umas por baixo das outras: le de 1 a 8 cargos e de 1 a 4 pessoas por cargo;
    - `cargos_max` e `pessoas_max`: esses limites, para a Mesa deixar escrever o mesmo (None sem eles).
    Pelo texto, como os outros: importar o ponto5 corre o comum.py. Hoje (ponto5 das 22:16) da tudo True, 8 e 4. Se o
    ponto5 deixar de os ler, a Mesa montada a seguir volta a dizer que ainda nao chegam ao filme.
    """
    import re
    limites = re.search(r"^CARGOS_MAX,\s*PESSOAS_MAX\s*=\s*(\d+),\s*(\d+)", texto, re.M)
    return {"cargos_primeiro": bool(re.search(r"""(\.get\(\s*|\[\s*)["']cargos_primeiro["']""", texto)),
            "cargos_varios": bool(limites and re.search(r"^def geometria_do_cargo\(", texto, re.M)),
            "cargos_max": int(limites.group(1)) if limites else None,
            "pessoas_max": int(limites.group(2)) if limites else None}


def le_as_partes_dos_creditos(texto, p5=None):
    """O ponto5_creditos.py ja faz a ordem das partes, os nomes corridos e a velocidade? (3 de outubro; pontos 5 e 5b do
    saida/discussao/contrato_1003.md)

    {creditos_partes, nomes_corridos, creditos_velocidade}, cada um True ou False.
    PELO TEXTO, como os cargos: a chave do est.creditos lida com .get( ou [ ("partes", "nomes_corridos", "velocidade").
    E PELAS CONTAS quando o modulo se deixa importar (`p5`), porque ler a chave nao chega: na madrugada de 3 de outubro o
    render ja guardava a posicao das legendas e ainda nao a desenhava, e um True so por ler dizia ao Tiago que chegava ao
    filme.
    - `creditos_partes`: o textos_dos_creditos() devolve a lista e deixa os cargos vazios sem "cargos"; o
      tempos_dos_creditos() com o titulo primeiro da as janelas de cada parte; e o desenho sabe correr por elas.
    - `nomes_corridos`: o textos_dos_creditos() le o true, e o rolo_de_nomes(blocos, True) de um grupo de ensaio so tem
      a altura das linhas dos nomes.
    - `creditos_velocidade`: o textos_dos_creditos() le {fotos: 100}, e o tempos_dos_creditos() poe a coluna a 100 px/s.
    Com False a Mesa diz «ainda não chega ao filme» na aba «Ordem e velocidade» dos Creditos.
    """
    import re

    def chave(nome):
        return bool(re.search(r"""(\.get\(\s*|\[\s*)["']%s["']""" % nome, texto or ""))
    le = {"creditos_partes": chave("partes"), "nomes_corridos": chave("nomes_corridos"), "creditos_velocidade": chave("velocidade")}
    if p5 is None:
        return le
    try:
        t = p5.textos_dos_creditos({"creditos": {"partes": ["titulo", "rolo"]}}, [])
        T = p5.tempos_dos_creditos(1000, 5000, len(t["cargos"]), t.get("cargos_primeiro", False), t["partes"], None)
        le["creditos_partes"] = bool(le["creditos_partes"] and t["partes"] == ["titulo", "rolo"] and not t["cargos"]
                                     and T.get("janelas") and T.get("primeiro") == "titulo"
                                     and re.search(r"^\s*def creditos_por_partes\(", texto or "", re.M))
    except Exception:  # noqa: BLE001 - um ponto5 de antes (sem a chave, ou com outra assinatura) nao as faz
        le["creditos_partes"] = False
    try:
        t = p5.textos_dos_creditos({"creditos": {"nomes_corridos": True}}, [])
        rolo = p5.rolo_de_nomes([("TITULO", "subtitulo", [["Pessoa Um", "Pessoa Dois"]])], True)
        le["nomes_corridos"] = bool(le["nomes_corridos"] and t["nomes_corridos"] is True and rolo.height == 78 + 20)
    except Exception:  # noqa: BLE001
        le["nomes_corridos"] = False
    try:
        t = p5.textos_dos_creditos({"creditos": {"velocidade": {"fotos": 100}}}, [])
        T = p5.tempos_dos_creditos(1000, 5000, 3, False, None, t["velocidade"])
        le["creditos_velocidade"] = bool(le["creditos_velocidade"] and t["velocidade"] == {"fotos": 100.0}
                                         and T["vel_fotos"] == 100.0 and T.get("fim_fotos") is not None)
    except Exception:  # noqa: BLE001
        le["creditos_velocidade"] = False
    return le


def le_as_legendas_de_3_de_outubro(render, montar):
    """O render e o montar ja fazem os pontos 1 a 4 do contrato de 3 de outubro? (saida/discussao/contrato_1003.md)

    {contador_fonte, legenda_posicao, numa_linha, posicao_clip, fotos_inteiras}, cada um True, False ou None (nao se
    conseguiu ver). `render` e o modulo, ja importado; `montar` e o texto do montar_da_mesa.py.

    PERGUNTA-SE AO DESENHO, e nao so a limpeza do estilo: na madrugada de 3 de outubro o render.normalizar_estilo() ja
    guardava a posicao das legendas e o faixa_texto() ainda nao a desenhava. Um True so por guardar dizia ao Tiago que a
    posicao chegava ao filme, e nao chegava.
    - `legenda_posicao`: com est.estilo.legenda.posicao {dy: -100}, a faixa da legenda sobe 100 px.
    - `contador_fonte`: o normalizar_estilo() guarda o est.estilo.contador.fonte (uma letra de data/fontes.json que
      esta no PC e nao e o Arial Bold), e o contador de anos desenhado com ela sai diferente do de sempre.
    - `numa_linha`, `posicao_clip`, `fotos_inteiras` (clip.x1, clip.lp e clip.li): o montar escreve-os na coluna
      opcoes_clip (pelo texto dele, como o destaque: importa-lo mexe no sys.stdout), e o render, com as opcoes lidas
      pelo ler_opcoes_clip() dele, poe a legenda numa linha, sobe-a, e poe a foto inteira na celula do lado a lado.
    O estilo do render volta sempre ao de sempre no fim. Sao uns 0,5 s, uma vez por Mesa montada.
    """
    import json
    import re
    le = {"contador_fonte": None, "legenda_posicao": None, "numa_linha": None, "posicao_clip": None, "fotos_inteiras": None}
    texto = "Clara\ne Tiago"

    def topo(capa):
        caixa = capa[1].getbbox() if capa else None
        return caixa[1] if caixa else None

    try:
        try:
            render.aplicar_estilo({}, [])
            hoje = topo(render.faixa_texto(texto))
            limpo = render.normalizar_estilo({"legenda": {"posicao": {"dy": -100}}}, [])
            if not (limpo.get("legenda") or {}).get("posicao"):
                le["legenda_posicao"] = False
            else:
                render.aplicar_estilo({"legenda": {"posicao": {"dy": -100}}}, [])
                sobe = topo(render.faixa_texto(texto))
                le["legenda_posicao"] = hoje is not None and sobe == hoje - 100
        finally:
            render.aplicar_estilo({}, [])
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pela posicao das legendas (%s)" % erro)
    try:
        import linha_tempo
        letras = render.letras_da_mesa()
        outra = next((k for k in sorted(letras) if k != render.LETRA_OMISSAO and letras[k].get("ficheiro")
                      and os.path.exists(letras[k]["ficheiro"])), None)
        if outra is None:
            le["contador_fonte"] = None
        else:
            limpo = render.normalizar_estilo({"contador": {"fonte": outra}}, [])
            if (limpo.get("contador") or {}).get("fonte") != outra:
                le["contador_fonte"] = False
            else:
                try:
                    render.aplicar_estilo({}, [])
                    a = linha_tempo.anos(960, 540, 2026, 1995, [], 0.0, 9.0).tobytes()
                    render.aplicar_estilo({"contador": {"fonte": outra}}, [])
                    b = linha_tempo.anos(960, 540, 2026, 1995, [], 0.0, 9.0).tobytes()
                    le["contador_fonte"] = a != b
                finally:
                    render.aplicar_estilo({}, [])
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pela letra do contador (%s)" % erro)
    # AS OPCOES DO CLIP: o montar tem de as escrever (a coluna e a chave), e o render de as desenhar
    escreve = bool(re.search(r"""COLUNA_OPCOES_CLIP|["']opcoes_clip["']""", montar or ""))
    ler = getattr(render, "ler_opcoes_clip", None)
    for chave, campo in (("x1", "numa_linha"), ("lp", "posicao_clip"), ("li", "fotos_inteiras")):
        if not (escreve and re.search(r"""["']%s["']""" % chave, montar or "")) or not callable(ler):
            le[campo] = False
    try:
        if callable(ler) and le["numa_linha"] is None:
            try:
                le["numa_linha"] = topo(render.faixa_texto(texto, clip_leg=ler(json.dumps({"x1": True})))) > topo(render.faixa_texto(texto))
            except TypeError:
                le["numa_linha"] = False
        if callable(ler) and le["posicao_clip"] is None:
            try:
                le["posicao_clip"] = topo(render.faixa_texto(texto, clip_leg=ler(json.dumps({"lp": {"dx": 0, "dy": -100}})))) == \
                    topo(render.faixa_texto(texto)) - 100
            except TypeError:
                le["posicao_clip"] = False
        if callable(ler) and le["fotos_inteiras"] is None:
            from PIL import Image
            im = Image.new("RGB", (400, 300), (200, 30, 30))
            try:
                com = render.preparar_lado("2v", [im, im], [None, None], "", clip_leg=ler(json.dumps({"li": True})))
                sem = render.preparar_lado("2v", [im, im], [None, None], "")
                le["fotos_inteiras"] = com["celulas"][0]["sprite"].tobytes() != sem["celulas"][0]["sprite"].tobytes()
            except TypeError:
                le["fotos_inteiras"] = False
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pelas opcoes dos clips (%s)" % erro)
    return le


def le_os_contadores_de_3_de_outubro(render, montar):
    """O render e o montar ja fazem os pontos 6 e 7 do contrato de 3 de outubro? (saida/discussao/contrato_1003.md)

    {contador_data, contador_parado}, cada um True, False ou None (nao se conseguiu ver). `render` e o modulo, ja
    importado; `montar` e o texto do montar_da_mesa.py (importa-lo mexe no sys.stdout).

    PERGUNTA-SE AO DESENHO, como nas legendas: um True so por o texto se ler dizia ao Tiago que a data chegava ao filme.
    - `contador_data`: o contador de anos que acaba numa data inteira ("2023>04/10/2026"). O linha_tempo le-o como um
      contador de anos e da a data por extenso para a chegada (chegada_do_contador), o render.preparar() leva-a ao
      desenho, e o ultimo fotograma sai diferente do de "2023>2026": tem a data acesa.
    - `contador_parado`: o clip.cp. O montar escreve-o (parado_do_contador e a chave "cp", pelo texto dele), e o render,
      com o "~segundos" no fim do texto, anda no tempo que sobra e fica no fotograma da chegada: num clip de 12 s com 3
      parados, os 9 s e os 12 s sao o mesmo fotograma, e os 6 s nao sao os 6 s de um contador de 12 s sem paragem.
    Sao quatro ou cinco fotogramas do contador, menos de 1 s, uma vez por Mesa montada.
    """
    import re
    le = {"contador_data": None, "contador_parado": None}

    def clip(texto):
        return {"tipo": "contador", "texto_ecra": texto, "ficheiro": "", "duracao_s": "9", "ordem": "1", "tratamento": "fiel"}

    def prepara(texto):
        try:
            return render.preparar(clip(texto), {})
        except (ValueError, TypeError, AttributeError):
            return None

    try:
        import linha_tempo
        chegada = getattr(linha_tempo, "chegada_do_contador", None)
        if not callable(chegada) or chegada("2023>04/10/2026") != ["4 de outubro de 2026"]:
            le["contador_data"] = False
        else:
            com, sem = prepara("2023>04/10/2026"), prepara("2023>2026")
            le["contador_data"] = bool(com and sem and linha_tempo.ler_contador("2023>04/10/2026")[0] == "anos"
                                       and render.desenhar(com, 9.0, 9.0).tobytes() != render.desenhar(sem, 9.0, 9.0).tobytes())
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pelo contador ate uma data (%s)" % erro)
    try:
        if not (re.search(r"^def parado_do_contador\(", montar or "", re.M) and re.search(r"""["']cp["']""", montar or "")):
            le["contador_parado"] = False
        else:
            com, sem = prepara("2023>2026~3.0"), prepara("2023>2026")
            if not com or not sem or com.get("parado") != 3.0:
                le["contador_parado"] = False
            else:
                aos9, aos12 = render.desenhar(com, 9.0, 12.0).tobytes(), render.desenhar(com, 12.0, 12.0).tobytes()
                le["contador_parado"] = bool(aos9 == aos12 and
                                             render.desenhar(com, 6.0, 12.0).tobytes() != render.desenhar(sem, 6.0, 12.0).tobytes())
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pelo contador parado no fim (%s)" % erro)
    return le


def le_o_som_a_escolha(montar):
    """O montar ja le os sons automaticos a escolha e a marca que continua? (decisao 111, 3 de outubro)

    {som_auto, marca_continua}, cada um True ou False. `montar` e o texto do montar_da_mesa.py (importa-lo mexe no
    sys.stdout).
    - `som_auto`: a versao da Mesa leva som_auto = {nome: false}, e o montar le-o no ler_som_auto() com os nomes do
      SOM_AUTO. Com False a Mesa diz, nos interruptores do «Som do render», que ainda nao chega ao filme.
    - `marca_continua`: a marca m = {f, in: "continua"}, pela MARCA_CONTINUA do montar.
    """
    import re
    montar = montar or ""
    return {"som_auto": bool(re.search(r"^SOM_AUTO\s*=", montar, re.M) and re.search(r"^def ler_som_auto\(", montar, re.M)
                             and re.search(r"""\.get\(\s*["']som_auto["']""", montar)),
            "marca_continua": bool(re.search(r"""^MARCA_CONTINUA\s*=\s*["']continua["']""", montar, re.M))}


def o_que_o_render_le():
    """{creditos, continuo, destaque, creditos_musica, data_afastada}: True se o render ja os le, False se
    nao, None se nao se conseguiu ver.

    `continuo`: o render.normalizar_estilo() guarda o contador.continuo (hoje deita-o fora com aviso).
    `data_afastada`: o mesmo para o contador.data_afastada, a data do nascimento mais longe do "SET" na
    fita de duas pecas (render.ESCOLHAS_DO_CONTADOR desde 2 de outubro).
    `creditos`: o ponto5_creditos.py le o campo "creditos" do estado da Mesa (est.get("creditos") ou
    est["creditos"]). E uma leitura do texto do ficheiro, porque importa-lo le a folha de convidados.
    `destaque`: a zona de destaque das fotos (clip.zd) chega ao filme, o montar escreve-a na coluna
    destaque (coluna_do_destaque) e o render le essa coluna (ler_destaque). O montar le-se como texto,
    porque importa-lo mexe no sys.stdout.
    `creditos_musica`: o ponto5 ja toca nos creditos a musica que ele escolheu no painel Creditos
    (est.creditos.musica, ver le_a_musica_dos_creditos), tambem pelo texto do ficheiro.
    `intro_fonte`: o render.normalizar_estilo() guarda a letra do letreiro da intro (est.estilo.intro.fonte, uma
    das de data/fontes_intro.json; 2 de outubro, a noite). Um render que nao a conhece deita-a fora com aviso.
    `cargos_primeiro`, `cargos_varios`, `cargos_max`, `pessoas_max`: os cargos dos creditos (2 de outubro, a noite),
    ver le_os_cargos_dos_creditos. Com False a Mesa diz «ainda não chega ao filme» no painel dos Creditos.
    `contador_fonte`, `legenda_posicao`, `numa_linha`, `posicao_clip`, `fotos_inteiras`: os pontos 1 a 4 do contrato de 3
    de outubro, ver le_as_legendas_de_3_de_outubro. Com False a Mesa diz «ainda não chega ao filme» no Estilo e no
    inspetor do clip.
    `creditos_partes`, `nomes_corridos`, `creditos_velocidade`: os pontos 5 e 5b do mesmo contrato (a ordem das partes
    dos creditos com o «Sem cargos», os nomes corridos e a velocidade), ver le_as_partes_dos_creditos.
    `contador_data`, `contador_parado`: os pontos 6 e 7 (o contador de anos que acaba numa data inteira, e o clip.cp,
    parado no fim), ver le_os_contadores_de_3_de_outubro. Com False a Mesa diz no inspetor e no Validar que ainda nao
    chega ao filme, e o palco nao os desenha.
    """
    import re
    le = {"creditos": None, "continuo": None, "destaque": None, "creditos_musica": None, "data_afastada": None,
          "intro_fonte": None, "cargos_primeiro": None, "cargos_varios": None, "cargos_max": None, "pessoas_max": None,
          "contador_fonte": None, "legenda_posicao": None, "numa_linha": None, "posicao_clip": None, "fotos_inteiras": None,
          "creditos_partes": None, "nomes_corridos": None, "creditos_velocidade": None,
          "contador_data": None, "contador_parado": None,
          # os sons automaticos a escolha e a marca que continua (decisao 111), ver le_o_som_a_escolha
          "som_auto": None, "marca_continua": None,
          # a largura em que uma legenda numa linha tem de caber, em pixeis a 1080 (render.LEGENDA_LARGURA_NUMA_LINHA)
          "numa_linha_largura": None}
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import render
        limpo = render.normalizar_estilo({"contador": {"continuo": True}}, [])
        le["continuo"] = bool((limpo.get("contador") or {}).get("continuo"))
        # A DATA DO NASCIMENTO AFASTADA (2 de outubro, a tarde): a mesma pergunta. Um render que nao a conhece
        # deita-a fora com aviso e devolve {}; o de hoje guarda-a (render.ESCOLHAS_DO_CONTADOR)
        limpo = render.normalizar_estilo({"contador": {"data_afastada": True}}, [])
        le["data_afastada"] = bool((limpo.get("contador") or {}).get("data_afastada"))
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar, nunca para a geracao
        print("  AVISO: nao consegui perguntar ao render pelo contador continuo (%s)" % erro)
    try:
        # A LETRA DA INTRO: com uma das oferecidas (a primeira que nao e o Impact), o render guarda-a?
        import render
        outra = next((k for k in sorted(render.letras_da_intro(), key=lambda k: (render.letras_da_intro()[k].get("ordem") or 999, k))
                      if k != render.INTRO_FONTE), None)
        if outra:
            limpo = render.normalizar_estilo({"intro": {"fonte": outra}}, [])
            le["intro_fonte"] = bool((limpo.get("intro") or {}).get("fonte"))
        else:
            le["intro_fonte"] = False
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pela letra da intro (%s)" % erro)
    try:
        import render
        montar = io.open(os.path.join(REPO, "scripts", "montar_da_mesa.py"), encoding="utf-8").read()
        le["destaque"] = bool(callable(getattr(render, "ler_destaque", None))
                              and re.search(r"^def coluna_do_destaque\(", montar, re.M))
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pela zona de destaque (%s)" % erro)
    try:
        # A LETRA DO CONTADOR, A POSICAO DAS LEGENDAS, NUMA SO LINHA E AS FOTOS INTEIRAS (3 de outubro)
        import render
        montar = io.open(os.path.join(REPO, "scripts", "montar_da_mesa.py"), encoding="utf-8").read()
        le.update(le_as_legendas_de_3_de_outubro(render, montar))
        # A LARGURA EM QUE UMA LEGENDA NUMA LINHA TEM DE CABER (decisao 111): a Mesa le-a daqui em vez de a escrever. Hoje
        # e a largura util de sempre, 1660; se ele quiser a legenda do clip 10 numa linha com menos margem, muda-se a
        # constante do render e a Mesa segue na montagem seguinte.
        largura = getattr(render, "LEGENDA_LARGURA_NUMA_LINHA", None)
        if isinstance(largura, (int, float)) and not isinstance(largura, bool):
            le["numa_linha_largura"] = int(largura)
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pelas legendas de 3 de outubro (%s)" % erro)
    try:
        # O CONTADOR ATE UMA DATA E O PARADO NO FIM (3 de outubro, pontos 6 e 7)
        import render
        montar = io.open(os.path.join(REPO, "scripts", "montar_da_mesa.py"), encoding="utf-8").read()
        le.update(le_os_contadores_de_3_de_outubro(render, montar))
    except Exception as erro:  # noqa: BLE001 - so serve para a Mesa avisar
        print("  AVISO: nao consegui perguntar ao render pelos contadores de 3 de outubro (%s)" % erro)
    try:
        # OS SONS AUTOMATICOS A ESCOLHA E A MARCA QUE CONTINUA (3 de outubro, decisao 111): pelo texto do montar
        le.update(le_o_som_a_escolha(io.open(os.path.join(REPO, "scripts", "montar_da_mesa.py"), encoding="utf-8").read()))
    except OSError as erro:
        print("  AVISO: nao li o montar_da_mesa.py para lhe perguntar pelos sons a escolha (%s)" % erro)
    try:
        texto = io.open(PONTO5, encoding="utf-8").read()
        le["creditos"] = bool(re.search(r"""(\.get\(\s*|\[\s*)["']creditos["']""", texto))
        le["creditos_musica"] = le_a_musica_dos_creditos(texto)
        le.update(le_os_cargos_dos_creditos(texto))
        # A ORDEM DAS PARTES, OS NOMES CORRIDOS E A VELOCIDADE (3 de outubro): pelo texto e, se o ponto5 se deixar
        # importar (precisa do ffmpeg, pelo comum.py), pelas contas dele
        p5 = None
        try:
            import creditos_para_mesa
            p5 = creditos_para_mesa._ponto5()
        except (SystemExit, Exception) as erro:  # noqa: BLE001 - so serve para a Mesa avisar
            print("  AVISO: nao consegui importar o ponto5 para lhe perguntar pelas partes dos creditos (%s); fica pelo texto" % erro)
        le.update(le_as_partes_dos_creditos(texto, p5))
    except OSError as erro:
        print("  AVISO: nao li %s (%s)" % (PONTO5, erro))
    return le


# A MUSICA DOS CREDITOS (2 de outubro, a tarde). O Tiago: "gostava de tambem poder alterar a musica que
# toca nos creditos ... na propria Mesa ... gostava de voltar ao Taking care of business". A Mesa precisa
# de saber onde cada musica se cala, para a escolha "para acabar com o fim da musica" e para dizer quando
# ela acaba antes dos creditos: e o musica_creditos.para_a_mesa(), sobre o indice do som que o
# audio_para_mesa ja fez (os silencios de cada copia), sem ler nenhum ficheiro de som. A mesma funcao que o
# render vai usar, por isso a Mesa e o render dao o mesmo segundo. Junta-se, das musicas que foram
# analisadas (data/discussao/musicas_batidas.json, o metodo da 095), onde comeca cada frase, para a Mesa
# dizer a mais perto da entrada como proposta; nunca a usa sozinha (083).
#
# E OS FINS DE LINHA DA VOZ (2 de outubro, a noite). O Tiago escolheu alongar o ultimo clip do filme para o corte
# dos creditos cair no fim de uma frase da musica que sai (a saida C), e a Mesa diz quanto falta. Os fins de frase
# verificados (data/fins_de_frase.csv) sao poucos, e os inicios de frase da 095 caem a meio das linhas cantadas: por
# isso vao tambem, de cada musica, os fins de linha da voz pela conta do scripts/discussao/juncao_creditos.py
# (musica_creditos.linhas_para_a_mesa: [fim, linha nova]). Medem-se nos originais uma vez, uns 6 s por musica, e
# guardam-se em saida/audio/fins_de_linha.json; MESA_SOM=ler so le o que esta guardado. Uns 60 KB na pagina, 0
# ficheiros na publicacao.
def musica_fim_para_mesa(audio):
    """{ficheiro: {fim, acaba, desvanece[, frases][, linhas]}} para o window.MUSICA_FIM, ou None sem o indice do som."""
    if not audio:
        return None
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import musica_creditos
        fora = musica_creditos.para_a_mesa(audio)
        for f, m in fora.items():
            frases = musica_creditos.frases_medidas(f)
            if frases:
                m["frases"] = [[t, forca] for t, forca in frases]
    except Exception as erro:  # noqa: BLE001 - uma Mesa sem isto continua a servir (a pagina conta pelo indice)
        print("  AVISO: sem o fim das musicas para os creditos (%s): a Mesa conta-o pelo indice do som" % erro)
        return None
    try:
        import render
        efeitos = tuple(render.EFEITOS_SOM)
        nomes = [f for f in fora if not (audio.get(f) or {}).get("gerado") and not f.startswith(efeitos)]
        linhas = musica_creditos.linhas_para_a_mesa(nomes, fazer=os.environ.get("MESA_SOM") != "ler")
        for f, ls in linhas.items():
            if f in fora and ls:
                fora[f]["linhas"] = ls
    except Exception as erro:  # noqa: BLE001 - sem os fins de linha a Mesa diz que nao tem as frases medidas
        print("  AVISO: sem os fins de linha da voz (%s): a passagem dos creditos so conta com os fins verificados" % erro)
    return fora


# AS INTROS DE OUTRAS CORES QUE JA ESTAO FEITAS (2 de outubro). O montar_da_mesa.intro_da_paleta() faz
# uma intro nova, uns 3 minutos, quando as cores e o tamanho da intro do est.estilo nao tem ficheiro; e
# so usa um ficheiro cujo comentario dos metadados seja o da paleta com as fotos da intro 5. A Mesa diz
# "ja feita" ou "custa cerca de 3 minutos" a partir disto, lido dos mesmos ficheiros e do mesmo
# comentario, para nunca dizer feita uma que o montar nao aceita. A conta vive no audio_para_mesa.py, que
# faz tambem as copias delas para o palco (revisor de 2 de outubro): uma regra so, nos dois sitios.
def intros_feitas(pasta=None):
    """[{fundo, papel, tinta, letra, tamanho, sem_preto, f}] das intros de outras cores ja igualadas, ou
    None se nao se conseguiu ver (sem a pasta ou sem o ffprobe): a Mesa cai entao nas quatro propostas.
    Ver audio_para_mesa.intros_feitas(). So le, nunca escreve na pasta dos media."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import audio_para_mesa
    return audio_para_mesa.intros_feitas(pasta)


def letras_render_para_mesa():
    """{letras, emojis, escuros, minimo, sem_emojis} para o window.LETRAS_RENDER, ou None se nao se conseguiu medir
    (o Validar usa entao a regra de reserva). Ver caracteres_para_mesa.letras_do_render()."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import caracteres_para_mesa
        return caracteres_para_mesa.letras_do_render()
    except Exception as erro:  # noqa: BLE001 - uma Mesa sem isto continua a servir, com a regra de reserva
        print("  AVISO: sem o que cada letra do render desenha (%s): o Validar usa a regra de reserva" % erro)
        return None


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
    # OS NOMES SAO OS DO ENDERECO, que levam o conteudo (gerar_previas.indice_publicado): com o nome do
    # disco, o browser mostrava a folha antiga que tinha guardada com o indice novo, e as fotos saiam
    # trocadas com as legendas (3 de outubro).
    import json
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    previas = "null"
    indice_previas = gerar_previas.indice_publicado(os.path.join(REPO, "saida", "previas"))
    if indice_previas is not None:
        previas = json.dumps(indice_previas, separators=(",", ":"))
        sem_conteudo = [n for n in indice_previas.get("folhas") or [] if not re.match(r"^folha_\d+_[0-9a-f]{10}\.jpg$", n)]
        if sem_conteudo:
            print("  AVISO: %d folhas de previas faltam em saida/previas (%s): corre scripts/gerar_previas.py"
                  % (len(sem_conteudo), ", ".join(sem_conteudo[:4])))
    else:
        print("  AVISO: falta saida/previas/indice.json, corre scripts/gerar_previas.py")

    # A BANDA SONORA COMO O RENDER A TOCA, e as duracoes que o script mudou. Sai dos
    # mesmos data/montagens/v3.csv e v3.som.csv que o render usa, para a Mesa mostrar
    # tambem o que os scripts poem sozinhos (ver som_para_mesa.py).
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

    # OS CREDITOS (2 de outubro): os grupos de nomes, os textos de omissao e as medidas do
    # ponto5_creditos.py, para o painel Creditos da Mesa os mostrar a correr e deixar mudar a
    # ordem das fotos e os textos (ver scripts/creditos_para_mesa.py). OS NOMES DOS CONVIDADOS SO
    # ENTRAM AQUI, no saida/mesa.html montado, que nao vai para o Git: nunca num ficheiro de data/,
    # scripts/ ou docs/. Vai num <script> proprio, antes do script da pagina, e nao no bloco de cima,
    # para esta parte nao mexer nas linhas dos outros dados.
    import creditos_para_mesa
    creditos = creditos_para_mesa.creditos_para_mesa()
    INICIO_PAGINA = '<script>\n(function(){\n"use strict";'
    if corpo.count(INICIO_PAGINA) != 1:
        sys.exit("O inicio do script da Mesa aparece %d vezes em editor_base.html. "
                 "Tem de aparecer uma." % corpo.count(INICIO_PAGINA))
    # "</" escapa-se: um nome com "</script>" fechava o bloco a meio (nao ha nenhum, mas a folha e dele)
    corpo = corpo.replace(
        INICIO_PAGINA,
        "<script>\nwindow.CREDITOS_NOMES = %s;\n</script>\n%s"
        % (json.dumps(creditos, ensure_ascii=False).replace("</", "<\\/"), INICIO_PAGINA), 1)

    # O FILME PARA O PALCO E O SOM (2 de outubro): os tempos de cada clip como o render os desenha, com o
    # nome do bebe e a fita parada que o montar poe, as imagens dos marcos da fita de 1995 (palco_para_mesa),
    # e uma copia leve de cada som que a Mesa pode tocar, com a sonoridade medida (audio_para_mesa). O som
    # FAZ-SE AQUI, mas so o que falta: cada copia chama-se pelo conteudo do original, e uma Mesa sem musicas
    # novas nao demora mais do que ler o indice (a primeira vez leva uns minutos). MESA_SOM=ler so le.
    # window.AUDIO e o mapa do contrato (ficheiro -> url, ganho_db, duracao, e as medidas); window.AUDIO_INFO
    # tem os lotes da publicacao e as regras do render que o palco imita.
    # Num <script> proprio antes do da pagina, como as letras; vai antes do delas, que o teste das letras
    # quer o window.FONTES encostado ao script da pagina.
    import palco_para_mesa
    import audio_para_mesa
    palco = palco_para_mesa.palco_para_mesa()
    try:
        som_mesa = audio_para_mesa.preparar(fazer=os.environ.get("MESA_SOM") != "ler")
    except (SystemExit, Exception) as erro:   # noqa: BLE001 - uma Mesa sem som continua a servir
        print("  AVISO: sem o som da Mesa (%s)" % erro)
        som_mesa = None
    # e onde cada musica se cala, para a musica dos creditos (musica_fim_para_mesa): no mesmo <script> do
    # window.AUDIO, de onde vem
    musica_fim = musica_fim_para_mesa(som_mesa["audio"] if som_mesa else None)
    corpo = corpo.replace(
        INICIO_PAGINA,
        "<script>\nwindow.PALCO = %s;\nwindow.AUDIO = %s;\nwindow.AUDIO_INFO = %s;\nwindow.MUSICA_FIM = %s;\n</script>\n%s"
        % (json.dumps(palco, ensure_ascii=False).replace("</", "<\\/"),
           json.dumps(som_mesa["audio"] if som_mesa else None, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
           json.dumps(som_mesa["info"] if som_mesa else None, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
           json.dumps(musica_fim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
           INICIO_PAGINA), 1)

    # O QUE CADA LETRA DO RENDER DESENHA (2 de outubro, a noite), para o Validar avisar dos caracteres como o
    # render.caracteres_sem_letra(): os emojis saem a cores, e so e caixa vazia o que nem a letra nem a de emojis
    # tem (ver caracteres_para_mesa.py). Uns 15 KB na pagina, 0 ficheiros na publicacao. Sem a medida, a Mesa usa
    # a regra de reserva do Validar e diz-se aqui.
    letras_render = letras_render_para_mesa()
    corpo = corpo.replace(
        INICIO_PAGINA,
        "<script>\nwindow.LETRAS_RENDER = %s;\n</script>\n%s"
        % (json.dumps(letras_render, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), INICIO_PAGINA), 1)

    # AS LETRAS DO LETREIRO DA INTRO (2 de outubro, a noite), com a mascara de cada uma, num <script> proprio
    # antes do das letras do Estilo, que o teste das letras quer encostado ao script da pagina
    fontes_intro = fontes_intro_para_mesa()
    corpo = corpo.replace(
        INICIO_PAGINA,
        "<script>\nwindow.FONTES_INTRO = %s;\n</script>\n%s"
        % (json.dumps(fontes_intro, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), INICIO_PAGINA), 1)

    # AS LETRAS DO PAINEL ESTILO (2 de outubro), no mesmo sitio e pela mesma razao dos creditos: um
    # <script> proprio antes do da pagina, que nao mexe nas linhas dos outros dados. A pagina poe o
    # <link> do Google Fonts sozinha, a partir do window.FONTES.css.
    fontes = fontes_para_mesa()
    le = o_que_o_render_le()
    # e as intros de outras cores que ja estao feitas, para a aba Intro dizer o que custa (ver acima)
    le["intros_feitas"] = intros_feitas()
    corpo = corpo.replace(
        INICIO_PAGINA,
        "<script>\nwindow.FONTES = %s;\nwindow.RENDER_LE = %s;\n</script>\n%s"
        % (json.dumps(fontes, ensure_ascii=False).replace("</", "<\\/"), json.dumps(le), INICIO_PAGINA), 1)

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
    print("  creditos    %s" % creditos_para_mesa.resumo(creditos))
    falta = [n for n, k in (("os creditos da Mesa", "creditos"), ("o contador numa so peca", "continuo"),
                            ("a zona de destaque", "destaque"), ("a musica dos creditos", "creditos_musica"),
                            ("a data do nascimento afastada", "data_afastada"), ("a letra da intro", "intro_fonte"),
                            ("os cargos antes dos convidados", "cargos_primeiro"),
                            ("mais cargos e mais pessoas nos creditos", "cargos_varios"),
                            ("a ordem das partes dos creditos", "creditos_partes"),
                            ("os nomes corridos dos creditos", "nomes_corridos"),
                            ("a velocidade dos creditos", "creditos_velocidade"))
             if le[k] is False]
    if falta:
        print("  render      ainda nao le %s: a Mesa avisa" % " nem ".join(falta))
    if fontes:
        fora = [f["nome"] for f in fontes["fontes"] if not f["em_disco"]]
        print("  letras      %8d no painel Estilo%s" % (len(fontes["fontes"]),
              (", %d ainda nao estao no PC: %s" % (len(fora), ", ".join(fora))) if fora else ""))
    if le.get("intros_feitas") is not None:
        print("  intros      %8d de outras cores ou de outra letra ja feitas, a Mesa diz o que custa cada uma"
              % len(le["intros_feitas"]))
    if fontes_intro:
        com = [x for x in fontes_intro["letras"] if x.get("mascara")]
        fora = [x["nome"] for x in fontes_intro["letras"] if not x.get("em_disco")]
        print("  letra intro %8d letras para o letreiro, %d com a mascara (%.1f KB na pagina)%s"
              % (len(fontes_intro["letras"]), len(com), sum(len(x["mascara"]) for x in com) / 1024.0,
                 (", %d fora do PC: %s" % (len(fora), ", ".join(fora))) if fora else ""))
    if musica_fim is not None:
        print("  creditos    onde se cala cada uma das %d musicas, para a musica dos creditos (%d com as frases medidas, "
              "%d com os fins de linha da voz)"
              % (len(musica_fim), sum(1 for m in musica_fim.values() if m.get("frases")),
                 sum(1 for m in musica_fim.values() if m.get("linhas"))))
    try:
        import caracteres_para_mesa
        print("  caracteres  %s" % caracteres_para_mesa.resumo(letras_render))
    except ImportError:
        print("  caracteres  sem o caracteres_para_mesa.py: o Validar usa a regra de reserva")
    print("  palco       %s" % palco_para_mesa.resumo(palco))
    print("  som         %s" % audio_para_mesa.resumo(som_mesa))
    if som_mesa and som_mesa["info"]["lotes"]:
        # O QUE SE PUBLICA, alem da pagina e das folhas das previas (que ja levam uns 47 MB da primeira
        # publicacao): o som e os videos, em publicacoes seguintes para o MESMO endereco, cada uma com
        # `files` e root saida. Os ficheiros que uma publicacao nao leva ficam la; os nomes sao pelo
        # conteudo, por isso depois da primeira vez so vao os novos, e os tirados saem com null.
        info = som_mesa["info"]
        for k, lote in enumerate(info["lotes"]):
            print("  publicar    lote %d de som e video: %d ficheiros, %.1f MB" % (k + 1, len(lote["ficheiros"]), lote["bytes"] / 1048576.0))
        if info["tiradas"]:
            # juntadas desde a ultima publicacao (audio_para_mesa: por_tirar); so os null dos que estao no endereco
            print("  publicar    tirar com null: %s" % ", ".join(info["tiradas"][:8]) + (" ..." if len(info["tiradas"]) > 8 else ""))
            print("  publicar    (so os que a listagem do endereco mostrar; depois: py -3.11 scripts/audio_para_mesa.py --publicado)")
        if info["grandes"]:
            print("  AVISO: acima de 15 MB por ficheiro: %s" % ", ".join(info["grandes"]))
    print("  total       %8.1f KB" % (len(corpo) / 1024.0))
    if len(corpo.encode("utf-8")) > 15 * 1024 * 1024:
        print("  AVISO: acima de 15 MB, o limite de publicacao e 16.")


if __name__ == "__main__":
    main()
