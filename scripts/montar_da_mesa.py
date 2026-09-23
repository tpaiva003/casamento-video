# -*- coding: utf-8 -*-
"""Gera uma montagem a partir do que o Tiago fixou na Mesa de Montagem.

ISTO FECHA O CICLO, que era o ponto em aberto da decisao 034: ele decidia na
Mesa e eu escrevia os montar_*.py a mao. Agora a ordem, os textos, as duracoes
e os tratamentos vem de la, sem uma unica decisao minha pelo meio.

COMO CHEGA AQUI: o artefacto publicado guarda tudo num documento da sua propria
base de dados, `montagem/estado`. Eu leio-o com a ferramenta Artifact e guardo-o
em data/mesa_estado.json. Este script le esse ficheiro.

O QUE CONTINUA A SER MEU, e esta escrito para nao haver duvida:
  - resolver cada foto pelo ID, e so pelo nome quando o ID falha
  - montar o som, porque a Mesa ainda nao tem editor de som
  - a fanfarra e a abertura, que sao videos e nao clips de foto

Uso:
    py -3.11 scripts/montar_da_mesa.py demo_v3
    py -3.11 scripts/montar_da_mesa.py demo_v3 --nome v3_mesa
"""
import csv
import json
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")
ESTADO = os.path.join(REPO, "data", "mesa_estado.json")
DESTINO = os.path.join(REPO, "data", "montagens")
MEDIA = "C:/casamento-video-media/trabalho"
GERADOS = "C:/casamento-video-media/gerados"

COLUNAS = ["ordem", "id", "tipo", "seccao", "ficheiro", "duracao_s",
           "transicao_s", "inicio_s", "fim_s", "dominante_s", "solo_s",
           "movimento", "texto_ecra", "tratamento", "duracao_original_s",
           "variacao_pct", "fonte_imagem", "nota", "textos_fotos", "textos_opcoes"]
# O in_s e o out_s do esquema, que so os videos usam, entram a seguir a duracao_s E SO
# QUANDO HA UM TROCO PARA ESCREVER. E a mesma regra das colunas das vozes no som.csv: uma
# montagem que nao tem videos com troco tem de dar o ficheiro de sempre, byte a byte, e
# duas colunas vazias no cabecalho ja nao davam. Ver teste_v3_sem_vozes_igual_ao_byte.
COLUNAS_TROCO = ["in_s", "out_s"]
COLUNAS_SOM = ["ficheiro", "caminho", "quando_s", "in_s", "dura_s", "ganho", "nota"]

# OS VIDEOS VEM DA MESA, nao deste ficheiro.
#
# O Tiago: "inclui na mesa tudo o que ja tinhamos decidido na versao anterior
# do video". Enquanto a fanfarra e a abertura eram acrescentadas aqui, o que
# ele via na Mesa nao era o que saia no render. Agora a Mesa e a verdade
# completa: se esta la, sai; se nao esta, nao sai.

VINHETA = "Candidato a vereador.mp3"       # os foguetes
VINHETA_IN = 173.7
VINHETA_DURA = 7.5
LANG_LANG = "Lang Lang - Beauty and the Beast (From Lang Lang Plays Disney  Live).mp3"
LANG_LANG_IN = 5.0
# Trocado a 2026-09-14 pelo Tiago pela versao portuguesa. A antiga ja nao esta
# em disco. Entra do principio: o ficheiro nao tem silencio a abrir e o canto
# de abertura e a parte que toda a gente reconhece.
REI_LEAO = "O Rei Leão (PT-PT) Ciclo Sem Fim.mp3"
CLARINHA = "Ana Faria - Clara.mp3"         # a que a mae dela pos no bloco da Clara
CLARINHA_IN = 6.0
# O ALELUIA NAO E UM FICHEIRO A PARTE. O .wlmp da mae tinha um aleluia.mp3 de 35 s a
# seguir aos foguetes, que nunca chegou ao disco, e durante dias saiu aqui um aviso de
# musica em falta. O Tiago, a 16 de setembro: "Se ja apanhaste os foguetes e la que
# esta o aleluia". O troco de Candidato a vereador a partir de 2:53 e cantado (medido:
# nao e ruido de foguetes) e faz de foguetes e de aleluia. Nao se procura mais nada.
REBOBINAR = "rebobinar.wav"

# OS EFEITOS NAO SAO LEITOS. Os foguetes e o rebobinar vao POR CIMA do que estiver a
# tocar: nunca sao cortados por uma musica marcada, nunca retomam e nunca baixam por
# baixo das vozes. Estava escrito duas vezes dentro do main, uma para cada uso.
EFEITOS = (VINHETA, REBOBINAR)

# AS VOZES DO PEDIDO, decisao 075. O Tiago, a 17 de setembro: "Aqui vou meter a foto do
# pedido e meto os audios que ja cortamos do pedido, eu depois decido a sequencia dos
# audios". A regra do CLAUDE.md "nenhuma narracao falada" fica de pe para o resto do
# filme: isto nao e narracao, e o som do proprio momento, e por isso e que entra.
PEDACOS = GERADOS + "/pedido_pedacos"
VOZ_PAUSA = 0.4             # o ar entre duas pecas seguidas
VOZ_ALVO_LUFS = -20.0       # o conjunto das vozes de um clip fica aqui, 3 dB acima do leito
LEITO_ALVO_LUFS = -23.0     # onde o loudnorm do render poe cada musica; ver render.construir_som
AVISO_NIVEL_DB = 6.0        # so se avisa de um som que entre a mais do que isto do leito
VOZ_ABAIXA_DB = -12.0       # quanto o leito baixa por baixo delas, quando nao para
VOZ_RAMPA = 0.3             # a descida e a subida do leito, e a folga antes e depois
VOZ_MODOS = ("baixa", "parada")
# Foto solta, lado a lado, colagem e pilha. Nao um contador, nem uma fita, nem um cartao:
# a voz precisa de uma imagem quieta por baixo para se ouvir como som daquele momento e
# nao como locucao por cima de um grafico. E ate onde as vozes podem correr, no main.
TIPOS_COM_VOZ = ("foto", "lado", "colagem", "pilha")


EXT_MUSICA = (".mp3", ".wav", ".m4a", ".wma", ".flac", ".ogg")

# Quantas fotos cada tratamento de varias fotos aceita. Os mesmos limites que o
# render.py, que recusa o clip fora deles, e que o GRUPOS da Mesa: o Tiago pediu a 17 de
# setembro mais fotos na colagem e na pilha, e o teste_limites_dos_grupos_iguais le os tres.
LIMITES_MONTE = {"colagem": (2, 12), "pilha": (2, 20)}

# As disposicoes do lado a lado e quantas fotos leva cada uma, as do render.LAYOUTS_LADO. A
# de 6, duas filas de tres, e de 17 de setembro; com 5 fotos nao ha disposicao nenhuma.
LAYOUTS_LADO = {"2v": 2, "3v": 3, "3s": 3, "4q": 4, "6g": 6}
LADO_OMISSAO = {2: "2v", 3: "3v", 4: "4q", 6: "6g"}

# Os estilos de cada um, decisao 068, os mesmos do render.py. O primeiro e a omissao, e
# vai escrito quando a Mesa nao traz estilo ou traz um que o render nao conhece.
ESTILOS_MONTE = {"colagem": ("filas", "espalhada"), "pilha": ("monte", "leque")}

# O ZOOM DO FIM DO ENQUADRAMENTO "aproxima", 18 de setembro. Os mesmos numeros que o
# render.py e que a Mesa, e o teste_limites_do_aproxima_iguais le os tres. O zoom escrito
# na Mesa vai na propria coluna movimento, "Aproxima 2.6", porque e o unico enquadramento
# que leva um numero e uma coluna nova mudava o cabecalho de todas as montagens.
APROXIMA_OMISSAO = 2.2
APROXIMA_MIN = 1.2
APROXIMA_MAX = 4.0

# O TEXTO EM CADA FOTO DE UM GRUPO. O Tiago: "permite colocar o texto nas fotos mesmo as
# que ficam em leque e assim, tem de ser opcional ter o texto ou nao". A Mesa guarda no
# clip xf, um texto por foto pela ordem de fotos, e vf, que liga e desliga. A legenda de
# baixo do grupo continua a ser o x. Acima disto um texto ja nao se le a 15 metros numa
# foto que ocupa um terco do ecra, e o render corta-o em duas linhas com reticencias.
TEXTO_FOTO_MAX_CARACTERES = 32
TIPOS_COM_TEXTOS = ("lado", "colagem", "pilha")

# AS OPCOES DOS TEXTOS DAS FOTOS, coluna textos_opcoes. O Tiago, a 15 de setembro: "em vez
# de metermos o texto a aparecer em cada foto individualmente, metemos o texto master a
# alterar", "permite tambem que eu possa selecionar o tamanho que quero", e na pilha "a
# opcao para ficar la e para desaparecer ser algo que eu escolho". A Mesa guarda no clip:
#   vm  "legenda" quando os textos vao para a legenda de baixo, a trocar com cada foto;
#       ausente ou "foto", em cada foto
#   tt  o tamanho da letra em pixeis a 1080, inteiro entre 28 e 90; ausente e 46, o da
#       legenda de baixo
#   vt  "fica" quando, na pilha e em cada foto, os textos das fotos de baixo ficam a vista;
#       ausente ou "some", desaparecem quando a seguinte cai por cima
# Nenhum conta sem vf. A coluna so leva o que difere da omissao, e vai vazia quando
# textos_fotos vai vazia: o render le a coluna vazia como a omissao, e assim uma montagem
# de antes das opcoes e esta dao o mesmo video. Os valores sao os do render.OPCOES_TEXTO,
# e o teste_mesa_escreve_textos_opcoes falha se os dois se afastarem.
TEXTO_FOTO_TAMANHO = 46
TEXTO_FOTO_TAMANHOS = (28, 90)
MODOS_TEXTO = ("foto", "legenda")
TAPADAS_TEXTO = ("some", "fica")
OPCOES_OMISSAO = {"modo": MODOS_TEXTO[0], "tamanho": TEXTO_FOTO_TAMANHO, "tapadas": TAPADAS_TEXTO[0]}


def tamanho_da_letra(tt):
    """O tt da Mesa como inteiro entre 28 e 90, ou None quando nao presta.

    A Mesa guarda um numero, mas um estado editado a mao pode trazer "56", 56.0 ou true.
    O inteiro escrito como texto ou como 56.0 vale, como no render; o booleano e o que tem
    parte decimal nao, e o render tambem os recusa. Quem escreve a coluna e quem a le tem
    de concordar, senao a Mesa mostra um tamanho e o video sai com outro.
    """
    if isinstance(tt, bool):
        return None
    if isinstance(tt, str):
        tt = tt.strip()
        if not tt.isdigit():
            return None
        tt = int(tt)
    if isinstance(tt, float):
        if not tt.is_integer():
            return None
        tt = int(tt)
    if not isinstance(tt, int) or not TEXTO_FOTO_TAMANHOS[0] <= tt <= TEXTO_FOTO_TAMANHOS[1]:
        return None
    return tt


def opcoes_dos_textos(c, tipo, ordem, avisos):
    """As opcoes do clip, completas: {"modo", "tamanho", "tapadas"}, com aviso do que nao presta.

    O que a Mesa nao conhece cai na omissao COM AVISO, como no render: uma opcao mal
    escrita que caisse em silencio era um texto a sair de outra maneira sem ninguem saber
    porque. O tamanho ausente, vazio ou 46 e a omissao sem aviso.
    """
    o = dict(OPCOES_OMISSAO)
    vm = c.get("vm")
    if vm in (None, ""):
        pass
    elif vm in MODOS_TEXTO:
        o["modo"] = vm
    else:
        avisos.append("%s com vm=%r desconhecido, os textos ficam em cada foto (clip %d)"
                      % (tipo, vm, ordem))
    tt = c.get("tt")
    if tt not in (None, ""):
        n = tamanho_da_letra(tt)
        if n is None:
            avisos.append("%s com tamanho da letra %r, tem de ser inteiro entre %d e %d, fica %d (clip %d)"
                          % (tipo, tt, TEXTO_FOTO_TAMANHOS[0], TEXTO_FOTO_TAMANHOS[1],
                             TEXTO_FOTO_TAMANHO, ordem))
        else:
            o["tamanho"] = n
    vt = c.get("vt")
    if vt in (None, ""):
        pass
    elif vt in TAPADAS_TEXTO:
        o["tapadas"] = vt
    else:
        avisos.append("%s com vt=%r desconhecido, os textos das fotos de baixo desaparecem (clip %d)"
                      % (tipo, vt, ordem))
    return o


def coluna_das_opcoes(opcoes, tipo):
    """A coluna textos_opcoes: JSON so com o que difere da omissao, ou "" se nada difere.

    O vt SO SE ESCREVE NA PILHA E FORA DA OPCAO LEGENDA: e o unico sitio onde conta. Escrito
    noutro lado, o render ignorava-o, mas a coluna dizia uma coisa que o video nao faz.
    """
    o = {}
    if opcoes["modo"] != OPCOES_OMISSAO["modo"]:
        o["modo"] = opcoes["modo"]
    if opcoes["tamanho"] != OPCOES_OMISSAO["tamanho"]:
        o["tamanho"] = opcoes["tamanho"]
    if tipo == "pilha" and opcoes["modo"] == "foto" and opcoes["tapadas"] != OPCOES_OMISSAO["tapadas"]:
        o["tapadas"] = opcoes["tapadas"]
    return json.dumps(o, ensure_ascii=False) if o else ""


def legendas_curtas_da_linha(linha, entra, sai, render):
    """[(k, texto, segundos)] dos textos da linha que ficam pouco tempo na legenda de baixo.

    So na opcao legenda; nas outras a lista e vazia. `entra` e `sai` sao os encadeados de
    render.encadeados_do_corpo(), os mesmos que a agenda da colagem e da pilha conta: com
    outros, os inicios das fotos, e com eles os tempos, andavam. O texto do grupo entra no
    lugar dos vazios, como o render faz ao mostrar.
    """
    try:
        opcoes = json.loads(linha["textos_opcoes"] or "{}")
        textos = json.loads(linha["textos_fotos"] or "[]")
    except ValueError:
        return []
    if not isinstance(opcoes, dict) or opcoes.get("modo") != "legenda" or not textos:
        return []
    grupo = (linha["texto_ecra"] or "").strip()
    mostra = [t or grupo for t in textos]
    tempos = render.tempos_legenda_grupo(linha["tipo"], len(textos), float(linha["duracao_s"]),
                                         entra, sai)
    return render.legendas_curtas(mostra, tempos)


def linhas_na_legenda(texto, tamanho):
    """Quantas linhas o texto leva na legenda de baixo, pela conta do render com a letra escolhida."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    return len(render.linhas_legenda(texto, tamanho)[1])


def textos_e_opcoes(c, n, tipo, ordem, avisos):
    """(textos_fotos, textos_opcoes) de um grupo. As opcoes so contam, e so avisam, com textos.

    Um tt errado num grupo com o texto desligado nao vai a lado nenhum: avisar dele era
    ruido. Por isso as opcoes leem-se primeiro, mas os seus avisos so entram se a coluna
    dos textos nao for vazia. Fora dos grupos, textos_das_fotos() ja devolve vazio.
    """
    avisos_opcoes = []
    opcoes = opcoes_dos_textos(c, tipo, ordem, avisos_opcoes)
    textos = textos_das_fotos(c, n, tipo, ordem, avisos, opcoes)
    if not textos:
        return "", ""
    avisos.extend(avisos_opcoes)
    return textos, coluna_das_opcoes(opcoes, tipo)


def texto_de_xf(t):
    """Um valor do xf da Mesa como texto para a coluna: so as cadeias e os numeros contam.

    O NULL JA ERA TRATADO, O BOOLEANO NAO. Um True vindo de um estado editado a mao ou de
    outra pagina saia escrito "True" na foto, sem aviso nenhum, e um 2019.0 saia "2019.0".
    E a mesma regra do ler_textos_fotos() do render, que ja recusava o booleano: quem
    escreve a coluna e quem a le tem de concordar, senao o video mostra o que a Mesa nao
    mostrou.
    """
    if isinstance(t, str):
        return t.strip()
    if isinstance(t, bool) or not isinstance(t, (int, float)):
        return ""
    return "%d" % t if float(t).is_integer() else str(t)


def textos_das_fotos(c, n, tipo, ordem, avisos, opcoes=None):
    """A coluna textos_fotos de um grupo: JSON com n textos, ou "" quando nao aparecem.

    So se escreve com vf ligado e pelo menos um texto. Desligar na Mesa nao apaga os
    textos, e por isso vf desligado com textos la dentro tem de dar coluna vazia: se
    se olhasse so para xf, o texto que ele escondeu saia no video. `opcoes` sao as de
    opcoes_dos_textos(); sem elas contam as de omissao.
    """
    if tipo not in TIPOS_COM_TEXTOS or c.get("vf") is not True:
        return ""
    opcoes = opcoes or OPCOES_OMISSAO
    xf = c.get("xf")
    if not isinstance(xf, list):
        return ""              # grupo de antes dos textos: vale todos vazios
    textos = [texto_de_xf(t) for t in xf]
    if not any(textos):
        return ""
    if len(textos) != n:
        # UMA LISTA DE OUTRO TAMANHO DESENCONTRA TEXTOS E FOTOS sem nada se ver na Mesa,
        # que completa o que falta ao mostrar. Completa-se e corta-se como o render faz,
        # e diz-se, porque um texto cortado aqui nunca chega ao video.
        sobram = [t for t in textos[n:] if t]
        avisos.append("%s com %d textos para %d fotos: %s (clip %d)"
                      % (tipo, len(textos), n,
                         "completei com vazios" if len(textos) < n
                         else ("cortei os que sobram, %r" % sobram if sobram
                               else "cortei os que sobram, todos vazios"),
                         ordem))
        textos = (textos + [""] * n)[:n]
        if not any(textos):
            return ""
    # NA LEGENDA DE BAIXO NAO HA FOTO PEQUENA NEM FOTO POR CIMA: o texto vai na faixa do
    # ecra inteiro, em ate quatro linhas, e o aviso do comprimento e o da pilha eram os de
    # uma faixa dentro da foto. So a opcao em cada foto os leva.
    if opcoes["modo"] == "legenda":
        # MAS UM TEXTO QUE PARTE EM VARIAS LINHAS ENCOLHE AS FOTOS DO CLIP INTEIRO: a faixa
        # de baixo fica com a altura do texto mais alto durante todo o clip, para as fotos
        # nao mudarem de sitio quando o texto troca, e as fotos pousam acima dela. Numa
        # colagem espalhada de 4 um texto de 87 caracteres subia a faixa 62 pixeis e as
        # quatro fotos encolhiam, tambem nas que tinham "Natal" ou nada. Diz-se, com a
        # conta do render para a letra escolhida.
        for k, t in enumerate(textos):
            n_linhas = linhas_na_legenda(t, opcoes["tamanho"]) if t else 0
            if n_linhas > 1:
                avisos.append("%s, texto da foto %d leva %d linhas na legenda de baixo, e a faixa fica com "
                              "essa altura durante o clip inteiro: as fotos de todo o clip encolhem: %r (clip %d)"
                              % (tipo, k + 1, n_linhas, t, ordem))
        return json.dumps(textos, ensure_ascii=False)
    for k, t in enumerate(textos):
        if len(t) > TEXTO_FOTO_MAX_CARACTERES:
            avisos.append("%s, texto da foto %d com %d caracteres, mais de %d le-se mal a 15 "
                          "metros e pode sair cortado: %r (clip %d)"
                          % (tipo, k + 1, len(t), TEXTO_FOTO_MAX_CARACTERES, t, ordem))
    if tipo == "pilha" and opcoes["tapadas"] == "fica":
        avisos.append("pilha com textos nas fotos a ficar a vista: as seguintes tapam-nos como "
                      "tapam a foto, e o render diz quanto de cada um fica tapado (clip %d)" % ordem)
    elif tipo == "pilha":
        avisos.append("pilha com textos nas fotos: cada texto so se le enquanto a sua foto "
                      "esta por cima (clip %d)" % ordem)
    return json.dumps(textos, ensure_ascii=False)


def resolve_musica(nome, mus):
    """O nome da musica tal como o Tiago o escreveu na Mesa, levado ao ficheiro.

    O DEFEITO: na Mesa ele escreveu "Baha Men - Who Let The Dogs Out (Lyrics)",
    sem o ".mp3". A procura era pelo nome exato, as quatro musicas que marcou
    davam "em falta", e o leito anterior ja tinha sido cortado nesse ponto: o
    video ficava MUDO dos 3:51 ate ao fim. Aceita-se agora o nome sem extensao,
    com outra normalizacao de acentos, e sem distinguir maiusculas.
    """
    import unicodedata
    if not (nome or "").strip():
        return None
    nome = nome.strip()
    if nome in mus:
        return nome
    alvo = unicodedata.normalize("NFC", nome).lower()
    if os.path.splitext(alvo)[1] in EXT_MUSICA:
        alvo = os.path.splitext(alvo)[0]
    for k in mus:
        kn = unicodedata.normalize("NFC", k).lower()
        if os.path.splitext(kn)[0] == alvo:
            return k
    return None


def caminhos_de_musica():
    achados = {}
    for raiz, _, fs in os.walk(MEDIA):
        if "00-Backup" in raiz or "_files" in raiz:
            continue
        for f in fs:
            if f.lower().endswith((".mp3", ".wav", ".m4a", ".wma", ".flac", ".ogg")):
                achados.setdefault(f, os.path.join(raiz, f))
    if os.path.isdir(GERADOS):
        for f in os.listdir(GERADOS):
            achados.setdefault(f, os.path.join(GERADOS, f))
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["faixa"] == "musica" and r["caminho_disco"]:
                achados[r["ficheiro"]] = r["caminho_disco"]
    return achados


def caminhos_de_voz():
    """Os pedacos de audio do pedido, pelo nome do ficheiro. So leitura, so esta pasta.

    NAO SE MEXE EM COMO AS MUSICAS SAO ENCONTRADAS. O caminhos_de_musica() varre a pasta
    de trabalho inteira e a dos gerados, e uma peca do pedido chamada "02_03m53s..." nao
    tem nada que ser confundida com uma musica: mora na sua pasta e e ai que se procura.
    A lista e a que estiver em disco, pelo nome atual, porque ele renomeia e apaga pecas.
    """
    achados = {}
    if os.path.isdir(PEDACOS):
        for f in sorted(os.listdir(PEDACOS)):
            if f.lower().endswith(EXT_MUSICA):
                achados[f] = os.path.join(PEDACOS, f)
    return achados


_DURACOES_AUDIO = {}


def duracao_de_audio(caminho):
    """Comprimento real de um ficheiro de som, em segundos, ou None.

    A DURACAO DE UMA VOZ MEDE-SE, como a de um video. O nome dos pedacos ate a traz
    escrita ("..._dura01.2s.mp3"), mas ele renomeia-os, e um numero no nome que nao bate
    com o ficheiro arrastava a voz seguinte e todas as outras sem uma queixa.
    """
    import subprocess
    if caminho in _DURACOES_AUDIO:
        return _DURACOES_AUDIO[caminho]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    d = None
    if caminho and os.path.exists(caminho):
        pr = os.path.join(os.path.dirname(render.ffmpeg()), "ffprobe.exe")
        try:
            r = subprocess.run(
                [pr, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", caminho],
                capture_output=True, text=True)
            d = round(float(r.stdout.strip()), 2)
        except Exception:
            d = None
    _DURACOES_AUDIO[caminho] = d
    return d


_SONORIDADES = {}


def sonoridade_de(caminhos):
    """Sonoridade integrada, em LUFS, das pecas tocadas umas a seguir as outras, ou None.

    MEDE-SE O CONJUNTO, e nao cada peca. O render iguala cada musica sozinha com o
    loudnorm, e e isso que se quer entre um piano ao vivo e uma cancao dos anos 80. Nas
    vozes isso apagava a diferenca entre uma frase dita alto e outra dita baixo, que e a
    propria gravacao do pedido: media-se cada pedaco e todos saiam ao mesmo nivel. Aqui
    mede-se tudo junto, e o render poe UM ganho igual em todas.
    """
    import re
    import subprocess
    chave = tuple(caminhos)
    if chave in _SONORIDADES:
        return _SONORIDADES[chave]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    medido = None
    if caminhos:
        # MEDE-SE COM O EBUR128, e nao com as contas que o loudnorm imprime de passagem.
        # O loudnorm em uma passagem imprime numeros pensados para uma SEGUNDA passagem,
        # e dava 1,8 dB ao lado: as vozes sairam a -18,2 LUFS quando eram para sair a -20.
        # O ebur128 e o mesmo medidor com que se confere o resultado, e assim o que se
        # mede e o que se ouve.
        #
        # O aformat vai ANTES do concat, um por peca: as pecas podem vir com ritmos de
        # amostragem diferentes, e o concat so junta o que ja vem igual.
        entradas, cadeia, etiquetas = [], [], []
        forma = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
        for k, c in enumerate(caminhos):
            entradas += ["-i", c]
            cadeia.append("[%d:a]%s[v%d]" % (k, forma, k))
            etiquetas.append("[v%d]" % k)
        filtro = ";".join(cadeia) + ";%sconcat=n=%d:v=0:a=1,ebur128=framelog=quiet:peak=none[o]" \
            % ("".join(etiquetas), len(caminhos))
        try:
            r = subprocess.run(
                [render.ffmpeg(), "-hide_banner", "-nostats", "-y"] + entradas
                + ["-filter_complex", filtro, "-map", "[o]", "-f", "null", "-"],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
            achado = re.findall(r"^\s*I:\s+(-?[\d.]+) LUFS", r.stderr or "", re.M)
            if achado:
                medido = float(achado[-1])
        except Exception:
            medido = None
    _SONORIDADES[chave] = medido
    return medido


_SONORIDADES_TROCO = {}


def sonoridade_do_troco(caminho, dentro, dura):
    """Sonoridade integrada, em LUFS, de um pedaco de um ficheiro, ou None se nao se medir.

    O SOM DE UM VIDEO ERA A UNICA FAIXA DO FILME SEM MEDIDA NENHUMA. O leito passa pelo
    loudnorm e fica a -23 LUFS; as vozes sao medidas aqui ao lado e apontadas a -20; o som
    de um video do corpo entra com ganho 1,0, que e o que estiver em disco. O troco do
    Homer que ele pediu mede -23,2 LUFS e por sorte bate certo, mas a Mesa oferece-lhe
    seis videos numa lista e um campo "Comeca no segundo": dentro do proprio Homer os seis
    trocos vao de -20,8 a -27,5 LUFS, e o intro_clara_tiago.mp4 mede -49,5. Esse entrava
    sem uma queixa, com a musica 12 dB abaixo por baixo dele e nada no lugar.

    Nao se muda o ganho aqui, que e decisao dele: mede-se para poder avisar.
    """
    import re
    import subprocess
    chave = (caminho, round(dentro, 3), round(dura, 3))
    if chave in _SONORIDADES_TROCO:
        return _SONORIDADES_TROCO[chave]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    medido = None
    try:
        r = subprocess.run(
            [render.ffmpeg(), "-hide_banner", "-nostats", "-y",
             "-ss", "%.3f" % max(0.0, dentro), "-t", "%.3f" % max(0.05, dura), "-i", caminho,
             "-map", "0:a:0", "-af", "ebur128=framelog=quiet:peak=none", "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        achado = re.findall(r"^\s*I:\s+(-?[\d.]+) LUFS", r.stderr or "", re.M)
        if achado:
            medido = float(achado[-1])
    except Exception:
        medido = None
    _SONORIDADES_TROCO[chave] = medido
    return medido


def aviso_de_nivel(caminho, dentro, dura, quem):
    """O aviso de um som que entra muito longe do leito, ou None quando esta perto dele.

    O leito sai sempre a LEITO_ALVO_LUFS por causa do loudnorm. Um video que entre muito
    abaixo disso e um buraco na banda sonora; muito acima e um susto no meio do jantar. A
    tolerancia e larga de proposito: isto nao e para afinar niveis, e para ele nao ser
    apanhado de surpresa no ecra do jantar por um ficheiro que ninguem mediu.
    """
    medido = sonoridade_do_troco(caminho, dentro, dura)
    if medido is None or medido <= -70.0:
        return ("%s: nao consegui medir a sonoridade; se vier baixo, ninguem o ouve por "
                "cima da sala" % quem) if medido is None else \
               ("%s: praticamente nao tem som nenhum gravado (%.0f LUFS); a musica baixa "
                "12 dB por baixo dele e nao entra nada no lugar" % (quem, medido))
    fora = medido - LEITO_ALVO_LUFS
    if abs(fora) <= AVISO_NIVEL_DB:
        return None
    return ("%s mede %.1f LUFS, %.1f dB %s da musica (%.0f LUFS): %s. O nivel que sai e o "
            "do ficheiro, sem ninguem o igualar; diz-me se queres que o iguale."
            % (quem, medido, abs(fora), "abaixo" if fora < 0 else "acima", LEITO_ALVO_LUFS,
               "no jantar vai ouvir-se pouco" if fora < 0 else "entra bem mais alto do que a musica"))


def ganho_das_vozes(caminhos):
    """O ganho unico das vozes de um clip, para o conjunto ficar a VOZ_ALVO_LUFS. Ou None."""
    medido = sonoridade_de(caminhos)
    if medido is None or medido <= -70.0:
        return None
    return round(10 ** ((VOZ_ALVO_LUFS - medido) / 20.0), 3)


def escreve_abafar(janelas):
    """As janelas de abaixamento do leito numa celula: "12.30-19.80x0.251", no relogio do corpo.

    A COLUNA SO APARECE QUANDO HA VOZES. Uma montagem sem vozes tem de dar o mesmo
    ficheiro que dava antes de as vozes existirem, byte a byte, e um cabecalho com mais
    duas colunas ja nao dava.
    """
    return ";".join("%.2f-%.2fx%.3f" % (a, b, k) for a, b, k in janelas)


def e_leito(fx):
    """Um leito e a musica de fundo: nao e efeito, nem voz, nem o som de um video.

    E o leito que se corta quando entra uma musica marcada, o que retoma na fita antes
    da Clara e o que baixa por baixo das vozes. As vozes vao por cima como os foguetes:
    cortar uma voz a meio de uma frase por causa de uma musica marcada no clip seguinte
    era exatamente o que nao pode acontecer. O som de um video e igual: e o som daquela
    imagem e tem de tocar inteiro enquanto ela passa.
    """
    return fx["ficheiro"] not in EFEITOS and not fx.get("voz") and not fx.get("video")


def corpo_da_montagem(linhas):
    """As linhas que nao sao a fanfarra do bloco inicial.

    A conta e a do render, render.partir_em_fanfarra_e_corpo(), e nao uma parecida: desde
    que um video pode estar no meio da montagem, "tipo != video" ja nao e o corpo, e duas
    respostas diferentes punham o som num sitio e a imagem noutro.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    return render.partir_em_fanfarra_e_corpo(linhas)[1]


def fanfarra_da_montagem(linhas):
    """Os videos do bloco inicial. A conta e a mesma do corpo_da_montagem(), uma so."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    return render.partir_em_fanfarra_e_corpo(linhas)[0]


def caminho_do_video(nome):
    """O ficheiro do video em disco, ou None. E o mesmo que o render abre."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    caminho, _arranque = render.caminho_de_video(nome)
    return caminho if caminho and os.path.exists(caminho) else None


def contadores_seguidos(texto_anterior, texto):
    """Dois contadores em que o segundo comeca exatamente onde o primeiro acabou.

    Duas datas comparam-se pelo dia; quando um deles anda por anos, pelo ano, que e tudo
    o que ele mostra. Um texto que nao se le nao e continuacao de nada.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import linha_tempo
    try:
        t1, _de1, para1, _m1 = linha_tempo.ler_contador(texto_anterior or "")
        t2, de2, _para2, _m2 = linha_tempo.ler_contador(texto or "")
    except (ValueError, AttributeError):
        return False
    if t1 == "datas" and t2 == "datas":
        return para1 == de2
    return (para1.year if t1 == "datas" else para1) == (de2.year if t2 == "datas" else de2)


def video_tem_som(caminho):
    """Este ficheiro de video tem stream de audio? A pergunta e a do render, uma so."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    return render.tem_stream_de_som(caminho)


_DURACOES = {}


def duracao_do_video(nome):
    """Comprimento real do ficheiro, em segundos, ou None se nao existir."""
    import subprocess
    if nome in _DURACOES:
        return _DURACOES[nome]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    caminho, _corte = render.caminho_de_video(nome)
    d = None
    if caminho and os.path.exists(caminho):
        ff = render.ffmpeg()
        pr = os.path.join(os.path.dirname(ff), "ffprobe.exe")
        try:
            r = subprocess.run(
                [pr, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", caminho],
                capture_output=True, text=True)
            d = float(r.stdout.strip())
        except Exception:
            d = None
    _DURACOES[nome] = d
    return d


def sem_acentos(texto):
    """Minusculas e sem acentos, para procurar palavras nos cartoes dele.

    O cartao da Clara diz "nasce uma bebe". Se ele o corrigir para "bebé", uma
    procura por "bebe" deixava de o encontrar, e com isso deixavam de acontecer os
    foguetes e o esticamento do cartao, sem aviso.
    """
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", texto or "")
                   if unicodedata.category(ch) != "Mn").lower()


def numero(x):
    """Um numero com as casas que tem ate duas: 4.36 fica 4.36, 2.20 fica 2.2 e 4 fica 4.0.

    Serve os avisos e a celula do zoom do "aproxima", que vai escrita na coluna movimento
    e e para ser lida por gente: "Aproxima 2.2" e nao "Aproxima 2.2000000000000002".
    """
    texto = ("%.2f" % float(x)).rstrip("0")
    return texto + "0" if texto.endswith(".") else texto


def segundos(x):
    """Uma duracao para um aviso, com as casas que tem ate duas: 4.36 fica 4.36 e 4 fica 4.0."""
    return numero(x)


NOMES_TIPO = {"cartao": "do cartao", "marcos": "da fita", "contador": "do contador",
              "video": "do video", "fanfarra": "da fanfarra"}


def _o_que_e(linha):
    """Como se diz num aviso o clip que esta a seguir, para ele saber o que interrompe o que.

    "as fotos seguidas acabam aos 6,3 s" nao diz a ninguem o que la esta: aqui diz-se o
    video pelo nome, porque e o unico caso em que ha dois sons a falar ao mesmo tempo.
    """
    if linha is None:
        return "do fim da montagem"
    nome = NOMES_TIPO.get(linha["tipo"], "do clip")
    if linha["tipo"] == "video" and (linha.get("ficheiro") or "").strip():
        return "%s %s (clip %d)" % (nome, linha["ficheiro"], linha["ordem"])
    return "%s do clip %d" % (nome, linha["ordem"])


SILENCIO_DB = -45.0     # abaixo disto, conta como silencio no inicio de uma musica
JANELA_SILENCIO = 20.0  # segundos do ficheiro que se olham a procura dele

# O QUE CONTA COMO BURACO NA MISTURA, quando a musica esta parada por baixo. Medido a 18
# de setembro: com «parada» a mistura desce abaixo de -50 dBFS em cinco sitios, e num deles
# marca -164 dBFS de RMS, que sao zeros; com «mais baixa» nao ha um unico buraco de um
# decimo de segundo e o mesmo ar entre as vozes mede -38,5 dBFS. Numa sala com 140 pessoas,
# zeros leem-se como o som a falhar. Menos de BURACO_MINIMO passa por respiracao.
BURACO_DB = -50.0
BURACO_MINIMO = 0.15


def buracos_de_som(caminho, dentro, dura):
    """[(inicio, fim)] dos silencios deste troco, contados do inicio dele. Sem nada, lista vazia.

    Serve o aviso do «musica parada»: com a janela a zero, o que resta na mistura e so
    isto, a voz ou o som do video, e onde eles nao tem nada nao fica nada. O aviso antigo
    so contava as pausas ENTRE pecas, e por isso nao via nem os 0,20 s dentro da propria
    voz nem os dois buracos dentro do troco do Homer.

    Mede-se, nao se calcula: a unica maneira de saber onde uma voz respira e ouvir o
    ficheiro. E so se mede com «parada», que e quando isto importa.
    """
    import re
    import subprocess
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    try:
        r = subprocess.run(
            [render.ffmpeg(), "-hide_banner", "-nostats", "-ss", "%.3f" % dentro,
             "-t", "%.3f" % dura, "-i", caminho, "-af",
             "silencedetect=noise=%.0fdB:d=%.2f" % (BURACO_DB, BURACO_MINIMO),
             "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
    except Exception:
        return []
    fora, aberto = [], None
    # O ffmpeg escreve os dois em linhas separadas e pela ordem do tempo. Um troco que
    # acabe calado deixa um `silence_start` sem par: esse fecha no fim do troco.
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", r.stderr or ""):
        if m.group(1) == "start":
            aberto = max(0.0, float(m.group(2)))
        elif aberto is not None:
            fora.append((round(aberto, 2), round(min(dura, float(m.group(2))), 2)))
            aberto = None
    if aberto is not None and dura - aberto >= BURACO_MINIMO:
        fora.append((round(aberto, 2), round(dura, 2)))
    return [(a, b) for a, b in fora if b - a >= BURACO_MINIMO - 0.005]


def frase_dos_buracos(buracos):
    """"2 buracos de silencio (0.2 s aos 9.4 s, 0.6 s aos 10.16 s)", para um aviso.

    Os avisos do montar sao para mim e vao sem acentos, com o ponto decimal do segundos();
    quem os poe em portugues para a Mesa e o som_para_mesa.py.
    """
    pecas = ["%s s aos %s s" % (segundos(b - a), segundos(a)) for a, b in buracos[:4]]
    if len(buracos) > 4:
        pecas.append("e mais %d" % (len(buracos) - 4))
    return "%d %s de silencio (%s)" % (len(buracos),
                                       "buraco" if len(buracos) == 1 else "buracos",
                                       ", ".join(pecas))


def silencio_no_inicio(caminho, dentro=0.0):
    """Segundos de silencio no ficheiro a partir de `dentro`, ou 0.

    O DEFEITO: "Antonio variacoes - o corpo e que paga" comeca com 2,47 s de
    silencio. O cruzamento do render faz a musica que sai continuar 2,2 s por
    cima da que entra, mas a que entra so se ouvia depois do silencio dela, e no
    meio ficava um vale mudo no cartao "Paixao pelo desporto". Uma musica
    marcada na Mesa comeca a tocar no clip onde ele a pos, e nao dois segundos
    depois.
    """
    import re
    import subprocess
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    try:
        r = subprocess.run(
            [render.ffmpeg(), "-hide_banner", "-nostats", "-ss", "%.3f" % dentro,
             "-t", "%.0f" % JANELA_SILENCIO, "-i", caminho, "-af",
             "silencedetect=noise=%.0fdB:d=0.3" % SILENCIO_DB, "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
    except Exception:
        return 0.0
    inicio = re.search(r"silence_start: (-?[\d.]+)", r.stderr or "")
    fim = re.search(r"silence_end: ([\d.]+)", r.stderr or "")
    if not inicio or not fim or float(inicio.group(1)) > 0.05:
        return 0.0
    # Um silencio que enche a janela toda nao e uma abertura muda, e um in_s
    # caido a meio de um silencio longo: o ffmpeg poe o fim no fim da janela.
    # Saltar ali 20 s as cegas era pior do que nao saltar nada.
    if float(fim.group(1)) >= JANELA_SILENCIO - 0.05:
        return 0.0
    return round(float(fim.group(1)), 2)


def main():
    if len(sys.argv) < 2:
        sys.exit("Diz qual a versao. Ex: py -3.11 scripts/montar_da_mesa.py demo_v3")
    qual = sys.argv[1]
    nome = sys.argv[sys.argv.index("--nome") + 1] if "--nome" in sys.argv else "v3"

    if not os.path.exists(ESTADO):
        sys.exit("Falta %s. Le a base de dados do artefacto primeiro." % ESTADO)
    estado = json.load(open(ESTADO, encoding="utf-8"))

    versao = None
    for v in estado.get("versoes", []):
        if v.get("id") == qual or v.get("nome") == qual:
            versao = v
            break
    if not versao:
        sys.exit("Nao encontrei a versao %r. Ha: %s"
                 % (qual, ", ".join(v.get("id", "?") for v in estado.get("versoes", []))))

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    por_id = {r["id"]: r for r in inv}
    por_nome = {r["ficheiro"].lower(): r for r in inv}

    import linha_tempo

    def _acende(linhas, desvio0, quem):
        """Instante, no corpo, em que o nascimento de `quem` e anunciado.

        Na fita e a palavra a acender; sem fita, e o cartao que ele escreveu.
        """
        for l in linhas:
            if l["tipo"] != "marcos":
                continue
            ano, marcas, troco, abre = linha_tempo.ler_meses(l["texto_ecra"])

            def fr(m):
                return ((m[1] - 1) + (m[0] - 1) / 31.0) / 12.0

            dentro = [m for m in marcas
                      if troco[0] - 1e-4 <= fr(m) <= troco[1] + 1e-4]
            passos = []
            if not dentro or abs(fr(dentro[0]) - troco[0]) > 1e-4:
                passos.append(None)
            passos += dentro
            if not dentro or abs(fr(dentro[-1]) - troco[1]) > 1e-4:
                passos.append(None)
            for i, m in enumerate(passos):
                if m and m[3] and quem in m[2]:
                    return (l["inicio_s"] - desvio0
                            + linha_tempo.inicio_da_paragem(
                                i, len(passos), 0.70, parar_no_primeiro=abre)
                            * l["duracao_s"])
        chave = "bebe" if quem == "Clara" else quem
        for l in linhas:
            if l["tipo"] == "cartao" and sem_acentos(chave) in sem_acentos(l["texto_ecra"]):
                return l["inicio_s"] - desvio0
        return None

    linhas, cursor, avisos, esticados = [], 0.0, [], []

    # O PONTO DE FOCO de cada fotografia vem da Mesa e e por fotografia, nao por
    # clip: onde esta a pessoa numa foto nao muda de um clip para outro. Vai na
    # coluna fonte_imagem, "fx,fy", e num lado a lado uma por foto separadas por
    # "|". Sem ponto marcado fica vazio e o render usa o corte automatico.
    focos_mesa = estado.get("focos") or {}

    def foco_de(i):
        p = focos_mesa.get(i)
        try:
            return "%.4f,%.4f" % (float(p[0]), float(p[1]))
        except Exception:
            return ""

    # O enquadramento que a Mesa guarda em "e" vai na coluna movimento, que o render le.
    ENQUADRAMENTOS = {"afastada": "Afastada", "parada": "Parada", "aproxima": "Aproxima"}

    def enquadramento_de(c, ordem, foco_txt):
        """A celula da coluna movimento de uma foto. No "aproxima" leva o zoom do fim.

        O NUMERO E VALIDADO AQUI, e nao so no render: e aqui que ha uma lista de avisos
        para o Tiago ler ao montar. Um zoom fora dos limites e recusado e fica a omissao,
        porque cortar um 12 para 4 em silencio era esconder o engano de quem o escreveu.
        Sem az nenhum e a omissao, sem aviso: e o que a Mesa escreve quando ele nao mexe.

        O ponto de foco que conta e o `foco_txt`, o que vai mesmo na coluna fonte_imagem,
        e nao o que a Mesa tem para o id do clip: um id resolvido pelo nome e outro id.
        """
        nome = ENQUADRAMENTOS.get(str(c.get("e") or "").strip(), "")
        # NA RAJADA O APROXIMA NAO EXISTE. O render sai pelo ramo da rajada antes de ler o
        # movimento, e a Mesa esconde o Enquadramento quando o tratamento e rajada; mas o
        # `e` fica guardado no clip, e passar uma foto com aproxima a rajada deixava aqui
        # "Aproxima 2.2" e um aviso de ponto de foco sobre uma coisa que nao vai ao video.
        # Fica o que ficava antes de o aproxima existir, sem aviso nenhum.
        if nome == "Aproxima" and str(c.get("r") or "").strip() == "rajada":
            return ""
        if nome != "Aproxima":
            return nome
        bruto = c.get("az")
        az = APROXIMA_OMISSAO
        if bruto not in (None, ""):
            try:
                az = float(str(bruto).replace(",", "."))
            except (TypeError, ValueError):
                avisos.append("clip %d com zoom do aproxima %r, que nao e um numero; fica %s"
                              % (ordem, bruto, numero(APROXIMA_OMISSAO)))
                az = APROXIMA_OMISSAO
        if not APROXIMA_MIN <= az <= APROXIMA_MAX:
            avisos.append("clip %d com zoom do aproxima %s, fora de %s a %s; fica %s"
                          % (ordem, bruto, numero(APROXIMA_MIN),
                             numero(APROXIMA_MAX), numero(APROXIMA_OMISSAO)))
            az = APROXIMA_OMISSAO
        if not foco_txt:
            avisos.append("clip %d com o enquadramento «aproxima ao ponto de foco» e sem "
                          "ponto de foco marcado: fecha ao centro da foto" % ordem)
        return "%s %s" % (nome, numero(az))

    def junta_clip(tipo, ficheiro, ident, dur, texto, trat, trans, foco="", mov="", textos="",
                   opcoes="", dentro=None):
        nonlocal cursor
        t = trans if linhas else 0.0
        inicio = cursor - t if linhas else 0.0
        fim = inicio + dur
        cursor = fim
        linhas.append({
            "ordem": len(linhas) + 1, "id": ident, "tipo": tipo,
            # O TROCO DE UM VIDEO, do esquema: in_s onde comeca no ficheiro, out_s onde
            # acaba. Vazio em tudo o resto, e vazio tambem num video que entre do zero e
            # dure o ficheiro inteiro, que e a fanfarra de sempre.
            "in_s": "" if dentro is None else round(dentro, 2),
            "out_s": "" if dentro is None else round(dentro + dur, 2),
            "seccao": versao.get("nome", qual)[:40], "ficheiro": ficheiro,
            "duracao_s": round(dur, 2), "transicao_s": round(t, 2),
            "inicio_s": round(inicio, 2), "fim_s": round(fim, 2),
            "dominante_s": round(dur - t, 2), "solo_s": round(dur - 2 * t, 2),
            "movimento": ("Nenhum" if tipo in ("contador", "marcos", "video")
                          else (mov or "Zoom in")),
            "texto_ecra": texto, "tratamento": trat,
            "duracao_original_s": "", "variacao_pct": "",
            "fonte_imagem": foco, "nota": "", "textos_fotos": textos,
            "textos_opcoes": opcoes,
        })

    # O CARTAO DO NASCIMENTO E ESTICADO PELA CONTA, nao por uma constante.
    #
    # A regra e dele, a letra: "Antes de elas comecarem a aparecer da tempo
    # para os foguetes terminarem (aplica isto tambem na Clara)". Mas quanto e
    # preciso esticar depende de ONDE os foguetes rebentam, e isso so se sabe
    # depois de montar: com a fita no sitio, eles rebentam na palavra a acender,
    # que pode estar a meio de um clip de catorze segundos.
    #
    # Por isso a montagem e feita duas vezes. Na primeira mede-se, na segunda
    # aplica-se. Uma constante escrita a mao acertava num caso e falhava no
    # outro, e foi o que aconteceu: o Tiago passava e a Clara entrava 2,1 s
    # cedo de mais.
    def e_nascimento(c):
        if c.get("t") != "cartao":
            return False
        x = (c.get("x") or "").lower()
        return "nasce" in x or "nascimento" in x

    clips = [dict(c) for c in versao.get("clips", [])]

    # OS AVISOS SAO DE CADA PASSAGEM. A lista era uma so para as duas, e tudo o que se
    # queixava na primeira voltava a queixar-se na segunda: o Tiago lia cada aviso
    # duas vezes. Fica a lista da ultima, mais o que so a primeira viu, como o video
    # cuja duracao ja foi corrigida quando a segunda passa.
    avisos_passagens = []
    for _passagem in (1, 2):
      linhas, cursor, avisos = [], 0.0, []
      avisos_passagens.append(avisos)
      musicas_marcadas, vozes_marcadas, videos_marcados = [], [], []
      for c in clips:
        tipo = c.get("t", "foto")
        if tipo == "fanfarra":
            continue            # a abertura ja entrou acima
        ficheiro, ident = c.get("f", ""), c.get("i", "")
        troco, video_no_corpo = None, False
        if tipo == "video":
            # A DURACAO DE UM VIDEO NAO SE ESCREVE, MEDE-SE.
            #
            # Na montagem, o som e colocado pelo relogio do corpo, e o corpo
            # comeca onde os videos acabam. Se o numero na Mesa nao for o
            # comprimento real do ficheiro, toda a banda sonora anda para o lado
            # e nada se queixa. Agora que ele pode trocar de video na Mesa, isso
            # deixava de ser hipotese e passava a ser questao de tempo.
            #
            # UM VIDEO DO MEIO DA MONTAGEM NAO E O FICHEIRO INTEIRO, E UM TROCO. O Tiago,
            # a 17 de setembro, sobre o Homer: "apenas um dos trechos em que ele diz o seu
            # Doh, preferencialmente o mais longo". Ai o ficheiro ja nao manda na duracao,
            # so no que cabe: o troco comeca no `vin` e a conta e vin + d <= comprimento.
            # A fanfarra, que entra do zero e dura o ficheiro todo, continua como sempre.
            video_no_corpo = any(l["tipo"] != "video" for l in linhas)
            vin = float(c.get("vin") or 0.0)
            real = duracao_do_video(ficheiro)
            if not real:
                avisos.append("VIDEO EM FALTA: %s" % ficheiro)
                if video_no_corpo or vin:
                    troco = vin
            elif video_no_corpo or vin:
                troco = vin
                # SEM DURACAO ESCRITA, O TROCO VAI DO `vin` ATE AO FIM DO FICHEIRO.
                #
                # E o que a Mesa promete por palavras: o botao «+ Vídeo» cria o clip com
                # d = 0, a etiqueta na lista diz "o ficheiro inteiro" e o inspetor diz "com
                # o comprimento medido quando eu montar". Mas so o ramo da fanfarra media o
                # ficheiro, e um video do corpo caia aqui e ficava com 0,00 s: duracao zero,
                # inicio igual ao fim, nunca ativo no ciclo dos fotogramas e sem faixa de
                # som. Desaparecia do filme, e o unico sinal era um aviso a falar de som.
                # E o caminho por omissao da funcionalidade: abrir um clip, carregar em
                # «+ Vídeo», escolher o ficheiro e nao escrever duracao nenhuma.
                # A DURACAO QUE ELE ESCREVEU GUARDA-SE, porque o main() passa por aqui mais
                # do que uma vez e a primeira passagem ja lhe mexeu no `d`. Com o `vin`
                # para la do fim do ficheiro a primeira corta para zero, e na segunda esse
                # zero era lido como "ele nao escreveu duracao nenhuma": ele apanhava os
                # dois avisos seguidos, e o segundo dizia-lhe que o ficheiro entra "do
                # segundo 18.5 ao fim, 0.0 s", que e falso. O resultado no filme era o
                # mesmo; o que enganava era a explicacao.
                if "_d_escrita" not in c:
                    c["_d_escrita"] = float(c.get("d", 0) or 0)
                d_escrita = c["_d_escrita"]
                if d_escrita <= 0:
                    c["d"] = round(max(0.0, real - vin), 2)
                    avisos.append("video %s: sem duracao escrita, medi o ficheiro e entra "
                                  "do segundo %s ao fim, %s s"
                                  % (ficheiro, segundos(vin), segundos(c["d"])))
                elif vin + d_escrita > real + 0.05:
                    cabe = round(max(0.0, real - vin), 2)
                    if cabe <= 0:
                        # O corte deu zero: o problema nao e a duracao, e o segundo de
                        # entrada estar depois do fim do ficheiro. Dizer "corto em 0.0 s"
                        # mandava-o afinar a duracao, que nao e onde esta o erro.
                        avisos.append("video %s: comeca no segundo %s e o ficheiro so tem "
                                      "%.2f s; o clip fica vazio e desaparece do filme. "
                                      "Baixa o «Começa no segundo»."
                                      % (ficheiro, segundos(vin), real))
                    else:
                        avisos.append("video %s: o troco pedido vai dos %s s aos %s s e o "
                                      "ficheiro tem %.2f s; corto em %s s"
                                      % (ficheiro, segundos(vin),
                                         segundos(vin + d_escrita), real,
                                         segundos(cabe)))
                    c["d"] = cabe
            elif abs(real - float(c.get("d", 0))) > 0.05:
                avisos.append("video %s: %s s na Mesa, %.2f s no ficheiro, "
                              "usei o ficheiro" % (ficheiro, c.get("d"), real))
                c["d"] = round(real, 2)
        if tipo == "lado":
            # LADO A LADO: varias fotografias num so clip. Cada uma resolve-se
            # pelo id, como as soltas; o id e o ficheiro da linha levam as varias
            # separadas por "|", e a disposicao vai no tratamento.
            fotos = [por_id.get(i) for i in (c.get("fotos") or [])]
            if len(fotos) not in LADO_OMISSAO:
                avisos.append("lado a lado saltado, tem %d fotos e as disposicoes levam %s: %s"
                              % (len(fotos), ", ".join(str(k) for k in sorted(LADO_OMISSAO)), c.get("fotos")))
                continue
            if not all(fotos):
                avisos.append("lado a lado com fotos em falta: %s" % (c.get("fotos"),))
                continue
            lay = c.get("lay") or LADO_OMISSAO[len(fotos)]
            # UMA DISPOSICAO DE OUTRO NUMERO DE FOTOS saia no render como nada: o preparar()
            # recusa-a e o clip ficava de fora sem ninguem saber porque. Desde que a Mesa tira
            # e troca fotos de um grupo, um lay antigo pode ficar para tras.
            if LAYOUTS_LADO.get(lay) != len(fotos):
                avisos.append("lado a lado com a disposicao %r para %d fotos, fica %s (clip %d)"
                              % (lay, len(fotos), LADO_OMISSAO[len(fotos)], len(linhas) + 1))
                lay = LADO_OMISSAO[len(fotos)]
            ident = "|".join(r["id"] for r in fotos)
            ficheiro = "|".join(r["ficheiro"] for r in fotos)
            c = dict(c, r=lay)
        if tipo in LIMITES_MONTE:
            # COLAGEM E PILHA, os tratamentos B e D da decisao 017, pedidos pelo
            # Tiago na Mesa. Seguem o caminho do lado a lado: cada foto pelo id, o id
            # e o ficheiro da linha com as varias separadas por "|". Uma foto que
            # falte salta o clip inteiro com aviso, em vez de sair uma colagem com
            # buraco que ninguem pediu.
            minimo, maximo = LIMITES_MONTE[tipo]
            pedidas = c.get("fotos") or []
            fotos = [por_id.get(i) for i in pedidas]
            if not (minimo <= len(fotos) <= maximo) or not all(fotos):
                faltam = [i for i, r in zip(pedidas, fotos) if not r]
                avisos.append("%s saltada, pede %d a %d fotos e tem %d%s: %s"
                              % (tipo, minimo, maximo, len(pedidas),
                                 (", em falta " + ", ".join(faltam)) if faltam else "",
                                 pedidas))
                continue
            ident = "|".join(r["id"] for r in fotos)
            ficheiro = "|".join(r["ficheiro"] for r in fotos)
            # O ESTILO VAI NA COLUNA TRATAMENTO, que e o que o render le nestes dois tipos.
            # Antes ia o "r" do clip, "fiel", que o render ignorava. Um estilo que o render
            # nao conhece dava la a omissao sem ninguem saber: fica a omissao escrita e o
            # aviso aqui.
            estilos = ESTILOS_MONTE[tipo]
            pedido = str(c.get("estilo") or "").strip()
            estilo = pedido if pedido in estilos else estilos[0]
            if pedido and pedido not in estilos:
                avisos.append("%s com estilo %r desconhecido, fica %s (clip %d): os estilos sao %s"
                              % (tipo, pedido, estilo, len(linhas) + 1, " e ".join(estilos)))
            c = dict(c, r=estilo)
        if tipo == "foto":
            # POR ID PRIMEIRO. Ha nomes repetidos em pastas diferentes, e o ID
            # e o unico que nao engana: a 6.jpg existe duas vezes no inventario.
            r = por_id.get(ident) or por_nome.get((ficheiro or "").lower())
            if not r:
                avisos.append("sem foto: %s (%s)" % (ficheiro, ident))
                continue
            ficheiro, ident = r["ficheiro"], r["id"]
            if r["id"] != c.get("i"):
                avisos.append("id %s nao existe, usei %s pelo nome %s"
                              % (c.get("i"), r["id"], ficheiro))
        if tipo == "lado" or tipo in LIMITES_MONTE:
            foco_txt = "|".join(foco_de(i) for i in ident.split("|"))
            foco_txt = foco_txt if foco_txt.strip("|") else ""
        else:
            foco_txt = foco_de(ident) if tipo == "foto" else ""
        # O indice k de xf e o de fotos, e o id da linha foi escrito pela mesma ordem: o
        # texto fica na sua foto. So os grupos o levam; numa solta o texto e o x. As
        # opcoes (onde, tamanho, tapadas) vao ao lado, so com o que difere da omissao.
        textos_txt, opcoes_txt = textos_e_opcoes(c, len(ident.split("|")), tipo,
                                                 len(linhas) + 1, avisos)
        # CONTEUDO CONTINUO CORTA, e dois contadores encadeados dao o fantasma.
        #
        # A regra e do CLAUDE.md e nasceu deste mesmo defeito: "na v3 apareciam dois '1995'
        # sobrepostos a seguir ao SAPO". Desde 17 de setembro a abertura tem o contador de
        # datas a acabar em 25/12/2025 e o de anos a comecar em 2025 logo a seguir, e os
        # dois desenhos sao quase iguais: mesmo fundo, mesma linha, numeros grandes quase a
        # mesma altura. Com os 0,7 s de encadeado da omissao, a meio da passagem leem-se
        # dois numeros um por cima do outro, duas legendas empilhadas e duas reguas
        # diferentes na mesma linha, e durante meio segundo ninguem le nada.
        #
        # Nao e um encadeado entre duas imagens diferentes: e a MESMA fita a continuar de
        # onde ficou, e por isso junta-se com corte seco. So quando o segundo comeca mesmo
        # onde o primeiro acabou; dois contadores de sitios diferentes encadeiam como antes.
        trans = float(c.get("c", 0.7))
        if (tipo == "contador" and linhas and linhas[-1]["tipo"] == "contador"
                and contadores_seguidos(linhas[-1]["texto_ecra"], c.get("x", ""))):
            if trans > 0:
                avisos.append("os contadores dos clips %d e %d sao a mesma fita a continuar: "
                              "entram com corte seco, sem o encadeado de %s s, senao leem-se "
                              "os dois numeros sobrepostos"
                              % (len(linhas), len(linhas) + 1, segundos(trans)))
            trans = 0.0
        junta_clip(tipo, ficheiro, ident, float(c.get("d", 4.0)),
                   c.get("x", ""), c.get("r", "fiel"), trans, foco_txt,
                   enquadramento_de(c, len(linhas) + 1, foco_txt) if tipo == "foto" else "",
                   textos_txt,
                   opcoes_txt, dentro=troco),
        # O SOM DE UM VIDEO DO CORPO E UMA FAIXA COMO AS OUTRAS. A fanfarra leva o seu som
        # colado com a imagem, pelo concat; um video do meio nao passa por ai, e sem isto
        # saia mudo. O `vzm` diz o que a musica por baixo faz, como nas vozes do pedido.
        if video_no_corpo:
            modo = str(c.get("vzm") or VOZ_MODOS[0]).strip()
            if modo not in VOZ_MODOS:
                avisos.append("video do clip %d com «musica por baixo» %r, que nao existe; "
                              "fica %s" % (len(linhas), modo, VOZ_MODOS[0]))
                modo = VOZ_MODOS[0]
            videos_marcados.append((len(linhas) - 1, modo))
        m = c.get("m") or {}
        if (m.get("f") or "").strip():
            musicas_marcadas.append((len(linhas) - 1, m["f"].strip(),
                                     float(m.get("in") or 0.0)))
        # AS VOZES DO PEDIDO, pela ordem que ele deu na Mesa. Ficam presas ao indice do
        # clip e nao ao instante: o cartao do nascimento estica-se entre as duas
        # passagens, e um instante guardado aqui ficava a apontar para o sitio errado.
        vz = [str(f).strip() for f in (c.get("vz") or []) if str(f).strip()]
        if vz and tipo in TIPOS_COM_VOZ:
            modo = str(c.get("vzm") or VOZ_MODOS[0]).strip()
            if modo not in VOZ_MODOS:
                avisos.append("vozes do clip %d com «musica por baixo» %r, que nao existe; "
                              "fica %s" % (len(linhas), modo, VOZ_MODOS[0]))
                modo = VOZ_MODOS[0]
            vozes_marcadas.append((len(linhas) - 1, vz, modo))
        elif vz:
            avisos.append("vozes do pedido num clip de %s, que nao e foto nem grupo: "
                          "ficam de fora (clip %d)" % (tipo, len(linhas)))

      if _passagem == 2:
        break
      corpo0 = corpo_da_montagem(linhas)
      if not corpo0:
        break
      desvio0 = corpo0[0]["inicio_s"]
      faltou = False
      for quem in ("Tiago", "Clara"):
        t = _acende(linhas, desvio0, quem)
        if t is None:
          continue
        fim_fog = t + VINHETA_DURA + 0.4
        prox = None
        for l in linhas:
          # Uma colagem, pilha ou lado a lado logo a seguir ao cartao tambem sao fotos
          # a entrar. Contar so as soltas deixava-as rebentar por baixo dos foguetes.
          e_fotos = l["tipo"] in ("foto", "lado") or l["tipo"] in LIMITES_MONTE
          if e_fotos and (l["inicio_s"] - desvio0) > t:
            prox = l["inicio_s"] - desvio0
            break
        if prox is None or prox >= fim_fog:
          continue
        falta = fim_fog - prox
        # A MESMA CHAVE QUE O _acende USA. O cartao da Clara que ele escreveu
        # diz "nasce uma bebe" e nao contem a palavra "Clara": procurar pelo
        # nome nao encontrava nada e o esticamento nunca acontecia.
        chave_c = "bebe" if quem == "Clara" else quem.lower()
        for c in clips:
          if e_nascimento(c) and chave_c in sem_acentos(c.get("x")):
            antes = float(c.get("d", 0))
            c["d"] = round(antes + falta, 2)
            esticados.append((c.get("x", "")[:44], antes, c["d"]))
            faltou = True
            break
      if not faltou:
        break

    antes = [a for lista in avisos_passagens[:-1] for a in lista if a not in avisos]
    avisos = [a for k, a in enumerate(antes) if a not in antes[:k]] + avisos

    # UMA COLAGEM OU PILHA CURTA DE MAIS APERTA-SE SEM SE QUEIXAR. O render encolhe a
    # folga do fim e as entradas para nenhuma foto ser tapada antes de parar, e isso
    # nao se ve na Mesa. Diz-se aqui quanto cada uma precisa. Os encadeados vem de
    # render.encadeados_do_corpo(), a mesma funcao que o render usa: o primeiro clip do
    # corpo entra sem encadeado, e o ultimo sai no fade a preto do fim.
    #
    # E UM TEXTO NA LEGENDA DE BAIXO QUE FICA MENOS DE render.LEGENDA_MINIMO_S NAO SE LE. Na
    # opcao legenda cada texto esta no ecra desde que a sua foto comeca a entrar ate a
    # seguinte comecar, e numa colagem de cinco em quatro segundos isso e menos de um
    # segundo por texto. A conta e a de render.tempos_legenda_grupo(), com os mesmos
    # encadeados, e o render avisa do mesmo ao preparar; aqui avisa-se antes de ele o ver
    # no jantar. Textos iguais seguidos nao trocam e somam-se, e os vazios mostram o do
    # grupo, ver render.legendas_curtas().
    corpo_m = corpo_da_montagem(linhas)
    if any(l["tipo"] in LIMITES_MONTE or l["textos_opcoes"] for l in corpo_m):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import render
        for k, (l, (entra, sai)) in enumerate(zip(corpo_m, render.encadeados_do_corpo(corpo_m))):
            n_fotos = len(l["id"].split("|"))
            if l["tipo"] in LIMITES_MONTE:
                minimo = render.duracao_minima_monte(l["tipo"], n_fotos, entra, sai)
                if l["duracao_s"] < minimo - 0.005:
                    # A duracao vai com as casas que tem e o minimo arredondado para cima.
                    # Com as duas a uma casa, 4,36 s contra 4,38 s dizia "com 4.4 s e curta:
                    # precisa de pelo menos 4.4 s".
                    avisos.append("%s de %d fotos com %s s e curta: precisa de pelo menos %.1f s "
                                  "para cada foto parar antes da seguinte e ficarem todas a vista "
                                  "antes %s (clip %d)"
                                  % (l["tipo"], n_fotos, segundos(l["duracao_s"]),
                                     math.ceil(minimo * 10 - 1e-6) / 10.0,
                                     "do fade do fim" if k + 1 == len(corpo_m) else "do encadeado",
                                     l["ordem"]))
            if l["textos_fotos"] and l["textos_opcoes"]:
                for kk, t, dura in legendas_curtas_da_linha(l, entra, sai, render):
                    if dura <= 1e-9:
                        # No lado a lado as celulas entram aos 0,35 + k x 0,45 s seja qual for a
                        # duracao: num 4q de 1,5 s a quarta entra depois do fim, e o aviso dizia
                        # "fica so -0.2 s". Os segundos negativos de legendas_curtas() sao quanto
                        # depois do fim a foto entra.
                        avisos.append("%s: o texto da foto %d nunca aparece na legenda de baixo, a foto so "
                                      "entra %.1f s depois de o clip acabar: %r (clip %d)"
                                      % (l["tipo"], kk + 1, max(0.0, -dura), t, l["ordem"]))
                        continue
                    avisos.append("%s: o texto da foto %d fica so %.1f s na legenda de baixo, pouco "
                                  "para ler a 15 metros: %r (clip %d)"
                                  % (l["tipo"], kk + 1, dura, t, l["ordem"]))

    caminho = os.path.join(DESTINO, nome + ".csv")
    colunas = list(COLUNAS)
    if any(l["in_s"] != "" for l in linhas):
        colunas[colunas.index("duracao_s") + 1:colunas.index("duracao_s") + 1] = COLUNAS_TROCO
    with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=colunas, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)

    # ------------------------------------------------------------------ som
    #
    # A NOTA DELE NA MESA, a letra:
    #   "Foguetes e Aleluia e depois Gostava que tivesse a musica do Rei Leao no
    #    nascimento do Tiago. Na Clara quero que tenha foguetes no primeiro
    #    texto e depois passe para uma das musicas da Clarinha"
    mus = caminhos_de_musica()
    corpo = corpo_da_montagem(linhas)
    desvio = corpo[0]["inicio_s"]
    fim_corpo = max(l["fim_s"] for l in corpo) - desvio

    t_tiago = _acende(linhas, desvio, "Tiago")
    t_clara = _acende(linhas, desvio, "Clara")

    # OS VIDEOS DA FANFARRA NAO PASSAM PELO LOUDNORM. Eles sao recodificados e colados com
    # concat, com o nivel que trazem do ficheiro; tudo o que e som do corpo e igualado a
    # LEITO_ALVO_LUFS. Medido a 18 de setembro no filme renderizado: o 20th Century Fox sai
    # a -30,8 LUFS, a historia da Clara a -49,6, e o leito entra a seguir a -19,4. Sao 27,9
    # dB de salto do segundo video para a musica, e num jantar isso le-se como avaria.
    # Igualar os dois muda o ficheiro da v3 ao byte e e decisao dele; medir e dizer, nao.
    for l in fanfarra_da_montagem(linhas):
        # A DURACAO PRIMEIRO, que ja esta medida e em cache: um video que nao esta em disco
        # ja foi dito la em cima, e assim nao se paga outra vez a procura pela pasta toda.
        if not duracao_do_video(l["ficheiro"]):
            continue
        caminho_f = caminho_do_video(l["ficheiro"])
        if not caminho_f or not video_tem_som(caminho_f):
            continue
        aviso_f = aviso_de_nivel(caminho_f, float(l["in_s"] or 0.0), l["duracao_s"],
                                 "o som do video de abertura %s" % l["ficheiro"])
        if aviso_f:
            avisos.append(aviso_f)

    faixas = []

    def junta_som(ficheiro, quando, dura, ganho, nota, dentro=0.0, caminho=None, voz=False,
                  video=False):
        if quando is None or dura <= 0.4:
            return
        # As vozes trazem o caminho consigo, da pasta do pedido; as musicas continuam a
        # ser procuradas como sempre foram, no `mus`.
        caminho = caminho or mus.get(ficheiro)
        if not caminho:
            avisos.append("MUSICA EM FALTA: %s (%s)" % (ficheiro, nota))
            return
        faixas.append({"ficheiro": ficheiro, "caminho": caminho,
                       "quando_s": round(max(0.0, quando), 2), "in_s": dentro,
                       "dura_s": round(dura, 2), "ganho": ganho, "nota": nota,
                       "voz": "1" if voz else "", "abafar": "",
                       "video": "1" if video else ""})

    if t_tiago is not None:
        junta_som(LANG_LANG, 0.0, t_tiago, 1.0,
                  "do pedido ate ao nascimento do Tiago", LANG_LANG_IN)

    # O REBOBINAR E DE CADA CONTADOR QUE RECUA, e nao do primeiro contador que aparecer.
    #
    # Desde 17 de setembro a abertura tem DOIS a recuar: o das datas, do dia do casamento
    # ate ao dia do pedido, e o de 2025 a 1995. Procurar "o contador" dava som de fita so
    # ao primeiro, e o segundo recuava trinta anos em silencio. Os que avancam, como o
    # 1995>2011, continuam sem ele: uma fita a avancar nao rebobina.
    #
    # E deixou de depender do nascimento do Tiago: o som de fita e do contador, nao do
    # bloco dele, e uma montagem sem fita de 1995 ficava sem ele por tabela.
    for l in linhas:
        if l["tipo"] != "contador":
            continue
        # E DE CAMINHO OLHA-SE PARA O X. Um contador mal escrito nao para o render aqui,
        # para-o la, a meio de quinze minutos de fotogramas; e um de datas com mais de tres
        # anos troca de desenho sozinho. Vale mais ele saber agora, ao montar.
        try:
            tipo_c, de_c, para_c, _marcos_c = linha_tempo.ler_contador(l["texto_ecra"])
        except (ValueError, AttributeError):
            avisos.append("contador %d com o texto %r, que nao consigo ler: as datas vao em "
                          "dd/mm/aaaa e os anos em 2026>1995"
                          % (l["ordem"], (l["texto_ecra"] or "")[:44]))
            continue
        if tipo_c == "datas" and abs((para_c - de_c).days) > linha_tempo.DIAS_MAXIMOS_DATAS:
            avisos.append("contador %d vai de %s a %s, mais de %d anos: a regua de meses nao "
                          "se le a essa velocidade e sai o contador de anos"
                          % (l["ordem"], de_c.isoformat(), para_c.isoformat(),
                             linha_tempo.DIAS_MAXIMOS_DATAS // 366))
        if linha_tempo.contador_recua(l["texto_ecra"]):
            t_cont = l["inicio_s"] - desvio
            junta_som(REBOBINAR, t_cont + l["duracao_s"] * 0.30,
                      l["duracao_s"] * 0.42, 1.15, "fita a rebobinar")

    if t_tiago is not None:
        junta_som(VINHETA, t_tiago, VINHETA_DURA, 2.0,
                  "foguetes, nascimento do Tiago", VINHETA_IN)
        fim_tiago = t_clara if t_clara is not None else fim_corpo
        junta_som(REI_LEAO, t_tiago + VINHETA_DURA - 1.0,
                  fim_tiago - (t_tiago + VINHETA_DURA - 1.0), 1.05,
                  "Rei Leao, do nascimento do Tiago ate ao da Clara")
    if t_clara is not None:
        junta_som(VINHETA, t_clara, VINHETA_DURA, 2.0,
                  "foguetes, no primeiro texto da Clara", VINHETA_IN)
        junta_som(CLARINHA, t_clara + VINHETA_DURA - 1.0,
                  fim_corpo - (t_clara + VINHETA_DURA - 1.0), 1.0,
                  "a musica da Clarinha que a mae dela pos", CLARINHA_IN)

    # ------------------------------------------------------- as vozes do pedido
    #
    # O Tiago, a 17 de setembro: "meto os audios que ja cortamos do pedido, eu depois
    # decido a sequencia dos audios". A ordem e a dele, a coluna vz do clip. Comecam no
    # inicio do clip onde ele as pos e tocam seguidas, com VOZ_PAUSA entre cada duas.
    #
    # ATE ONDE PODEM IR: pelas fotos e grupos seguidos, a comecar neste clip, e param no
    # primeiro clip que nao seja foto nem grupo. Uma voz por cima de um contador, de uma
    # fita ou de um cartao nao se le como o som daquela imagem, le-se como locucao.
    vozes = caminhos_de_voz()
    janelas_vozes = []
    foguetes = [(fx["quando_s"], fx["quando_s"] + fx["dura_s"])
                for fx in faixas if fx["ficheiro"] == VINHETA]
    for i, nomes, modo in vozes_marcadas:
        ordem = linhas[i]["ordem"]
        t0 = linhas[i]["inicio_s"] - desvio
        limite, quem_limita = fim_corpo, None
        # UM VIDEO DO CORPO PARA AS VOZES, como um contador ou um cartao: ele traz o seu
        # proprio som e uma voz do pedido por cima dele eram os dois a falar ao mesmo
        # tempo. Aqui nao ha videos da fanfarra, que ficam todos antes deste clip.
        for l in linhas[i + 1:]:
            if l["tipo"] not in TIPOS_COM_VOZ:
                limite = l["inicio_s"] - desvio
                quem_limita = l
                break
        postos, t = [], t0
        for voz_nome in nomes:
            real = resolve_musica(voz_nome, vozes)
            voz_dura = duracao_de_audio(vozes[real]) if real else None
            if not real or not voz_dura:
                # SALTA-SE SEM DEIXAR BURACO. Nao se sabe quanto durava a que falta, por
                # isso nao se pode guardar-lhe o lugar: as que existem continuam a tocar
                # umas a seguir as outras, com a mesma pausa, e ele fica a saber.
                avisos.append("VOZ DO PEDIDO EM FALTA: %s (clip %d); as outras tocam "
                              "seguidas na mesma" % (voz_nome, ordem))
                continue
            if voz_dura <= 0.4:
                avisos.append("voz %s dura %.2f s, curta de mais para o som a levar; "
                              "fica de fora (clip %d)" % (voz_nome, voz_dura, ordem))
                continue
            if any(a - 0.2 < t + voz_dura and t < b + 0.2 for a, b in foguetes):
                # Os foguetes vao a mais do dobro do volume das vozes: uma voz por baixo
                # deles nao se percebe, e pior do que nao estar la e estar la e nao se
                # ouvir. Fica de fora com o aviso, e o lugar dela e que nao se guarda.
                avisos.append("voz %s cairia por cima dos foguetes e nao se ouviria; "
                              "fica de fora (clip %d)" % (voz_nome, ordem))
                continue
            if t + voz_dura > limite + 0.05:
                # O LIMITE CORTA MESMO, e nao so avisa. Isto estava escrito no comentario
                # la em cima ("um video do corpo para as vozes") e era mentira: o limite
                # so alimentava um aviso no fim e a voz era colocada na mesma. Medido a 18
                # de setembro com tres pecas na foto do pedido: a terceira cobria os 3,47 s
                # do troco do Homer e ficava 4,7 dB acima do "D'oh", os dois a falar ao
                # mesmo tempo, os dois fora do loudnorm. E a mesma regra dos foguetes, pela
                # mesma razao, e por isso o remedio e o mesmo: fica de fora e ele fica a
                # saber, em vez de ir ao jantar um som por cima do outro.
                if quem_limita is None:
                    avisos.append("voz %s passaria do fim da montagem; fica de fora "
                                  "(clip %d). Estica as fotos ou tira uma voz."
                                  % (voz_nome, ordem))
                else:
                    avisos.append("voz %s cairia por cima %s e os dois falavam ao mesmo "
                                  "tempo; fica de fora (clip %d). Estica as fotos ou tira "
                                  "uma voz." % (voz_nome, _o_que_e(quem_limita), ordem))
                continue
            postos.append((real, vozes[real], t, voz_dura))
            t += voz_dura + VOZ_PAUSA
        if not postos:
            continue
        ganho = ganho_das_vozes([caminho_voz for _n, caminho_voz, _q, _d in postos])
        if ganho is None:
            ganho = 1.0
            avisos.append("nao consegui medir a sonoridade das vozes do clip %d; "
                          "ficam com o ganho do leito" % ordem)
        for voz_nome, voz_caminho, voz_quando, voz_dura in postos:
            junta_som(voz_nome, voz_quando, voz_dura, ganho,
                      "voz do pedido, no clip %d" % ordem, caminho=voz_caminho, voz=True)
        fim_vozes = postos[-1][2] + postos[-1][3]
        janelas_vozes.append((postos[0][2], fim_vozes, modo))
        # O AR COM A MUSICA PARADA E SILENCIO ABSOLUTO, e isso ouve-se como uma avaria e
        # nao como uma pausa: a janela cobre o grupo inteiro e medido da RMS a -inf. Nao se
        # muda sozinho, porque tanto o silencio como a musica a subir e a descer no meio
        # das vozes sao escolhas de som dele; diz-se, que e o que ele precisa para escolher.
        #
        # E CONTAM-SE TODOS OS BURACOS, nao so as pausas entre pecas. O aviso antigo so
        # falava do ar entre cada duas vozes e calava os 0,20 s dentro da propria voz, que
        # medidos sao silencio digital na mesma. Com um numero a frente, ele escolhe
        # «parada» ou «mais baixa» a saber o que compra.
        if modo == "parada":
            buracos = []
            for k, (_n, voz_caminho, voz_quando, voz_dura) in enumerate(postos):
                buracos += [(voz_quando + a, voz_quando + b)
                            for a, b in buracos_de_som(voz_caminho, 0.0, voz_dura)]
                if k + 1 < len(postos):
                    buracos.append((voz_quando + voz_dura, postos[k + 1][2]))
            buracos.sort()
            if buracos:
                avisos.append("clip %d com a musica parada por baixo de %d %s: %s. Se "
                              "preferires ouvir a musica por baixo delas, poe «mais baixa»"
                              % (ordem, len(postos),
                                 "voz" if len(postos) == 1 else "vozes",
                                 frase_dos_buracos(buracos)))

    # ------------------------------------------------- o som dos videos do corpo
    #
    # O Tiago, a 17 de setembro, sobre o troco do Homer a seguir as fotos do pedido: "Aqui
    # quero o video e o som". A imagem e desenhada pelo render dentro do corpo; o som entra
    # aqui, numa faixa que aponta para o proprio ficheiro de video, do segundo de entrada
    # ate ao fim do troco. Um video da fanfarra nao passa por aqui: esse leva o seu som
    # colado a imagem pelo concat, e uma faixa aqui punha-o a tocar duas vezes.
    #
    # Nao e leito (ver e_leito): uma musica marcada no clip seguinte nao o corta, e o
    # render nao lhe poe loudnorm nem cruzamento, como nao poe as vozes.
    for i, modo in videos_marcados:
        l = linhas[i]
        caminho_v = caminho_do_video(l["ficheiro"])
        if not caminho_v:
            avisos.append("o video %s nao esta em disco: o clip %d fica mudo"
                          % (l["ficheiro"], l["ordem"]))
            continue
        if l["duracao_s"] <= 0.4:
            avisos.append("o video do clip %d dura %s s, curto de mais para o som a levar; "
                          "fica mudo" % (l["ordem"], segundos(l["duracao_s"])))
            continue
        # UM VIDEO SEM STREAM DE AUDIO NAO LEVA FAIXA NENHUMA.
        #
        # A pasta dos videos ja tem um ficheiro so com imagem, e a Mesa oferece-o na lista
        # como oferece os outros. Uma faixa a apontar para ele fazia o ffmpeg recusar o
        # filtergraph inteiro no render, e o filme saia SEM BANDA SONORA NENHUMA, nao so
        # sem este clip. O render tambem ja sobrevive a isso, mas o sitio de dar a noticia
        # e aqui, antes do render de quinze minutos.
        if not video_tem_som(caminho_v):
            avisos.append("o video %s nao tem som nenhum gravado: o clip %d passa mudo"
                          % (l["ficheiro"], l["ordem"]))
            continue
        t0_v = l["inicio_s"] - desvio
        # OS FOGUETES ABAFAM-NO, COMO ABAFAM UMA VOZ DO PEDIDO. Vao a mais do dobro do
        # volume e nao sao leito, por isso a janela de abafar nao lhes toca. A voz que
        # caia ali fica de fora; o video NAO, porque a imagem dele tem de passar na mesma,
        # e por isso aqui so se avisa. Sem isto ele so dava por ela ao ouvir o render.
        if any(a - 0.2 < t0_v + l["duracao_s"] and t0_v < b + 0.2 for a, b in foguetes):
            avisos.append("o som do video do clip %d cai por cima dos foguetes e quase nao "
                          "se ouve; a imagem passa na mesma. Muda-o de sitio ou aceita-o "
                          "mudo" % l["ordem"])
        # E MEDE-SE ANTES DE O ESCREVER. O ganho fica em 1,0, como o contrato pede, mas o
        # numero e dele: um video que entre 20 dB abaixo do leito faz a musica baixar 12 dB
        # e nao poe nada no lugar, e isso hoje so se descobria a ouvir o render.
        aviso_nivel = aviso_de_nivel(caminho_v, float(l["in_s"] or 0.0), l["duracao_s"],
                                     "o som do video do clip %d (%s)"
                                     % (l["ordem"], l["ficheiro"]))
        if aviso_nivel:
            avisos.append(aviso_nivel)
        junta_som(l["ficheiro"], t0_v, l["duracao_s"], 1.0, "som do video",
                  float(l["in_s"] or 0.0), caminho=caminho_v, video=True)
        # O LEITO BAIXA POR BAIXO DELE, pelo mesmo mecanismo das vozes: a musica continua a
        # correr por baixo sem perder o sitio, so mais baixa, ou parada se ele o pedir.
        janelas_vozes.append((t0_v, t0_v + l["duracao_s"], modo))
        # E COM A MUSICA PARADA, O AR DENTRO DO VIDEO E SILENCIO DIGITAL. Entre dois «D'oh»
        # o troco do Homer nao tem nada, e com o leito a zero nao fica nada a tocar. E a
        # mesma conta das vozes, pela mesma razao. Ver buracos_de_som().
        if modo == "parada":
            buracos = buracos_de_som(caminho_v, float(l["in_s"] or 0.0), l["duracao_s"])
            if buracos:
                avisos.append("clip %d com a musica parada por baixo do video: %s. Se "
                              "preferires ouvir a musica por baixo dele, poe «mais baixa»"
                              % (l["ordem"],
                                 frase_dos_buracos([(t0_v + a, t0_v + b)
                                                    for a, b in buracos])))

    # A MUSICA MARCADA NA MESA MANDA A PARTIR DO CLIP ONDE ESTA.
    #
    # O Tiago: "gostava de ter outra musica a comecar ai". Uma musica marcada
    # num clip corta o leito que estiver a tocar nesse instante e toca ate a
    # proxima marcada, ou ate ao proximo leito que os nascimentos imponham, ou
    # ate ao fim. Os foguetes, o rebobinar e as vozes nao sao leitos e nunca se
    # cortam: vao por cima. Ver e_leito().
    # Uma musica marcada que nao se encontra NAO corta o leito anterior. Antes
    # cortava, e o resultado era silencio sem aviso nenhum no video.
    marcas_t = []
    for i, f, dentro in musicas_marcadas:
        t_marca = linhas[i]["inicio_s"] - desvio
        real = resolve_musica(f, mus)
        if real:
            calado = silencio_no_inicio(mus[real], dentro)
            if calado:
                avisos.append("musica marcada %s: saltei %.2f s de silencio no inicio, "
                              "entra aos %.2f s do ficheiro" % (real[:40], calado, dentro + calado))
            marcas_t.append((t_marca, real, round(dentro + calado, 2)))
        else:
            avisos.append("MUSICA MARCADA NA MESA NAO ENCONTRADA, continua a anterior: "
                          "%s (clip das %.1f s)" % (f, t_marca))
    marcas_t.sort()
    for k, (t, f, dentro) in enumerate(marcas_t):
        # UMA MARCA NO PRIMEIRO CLIP DO CORPO, OU NUM VIDEO, CAI EM t <= 0. O corte era
        # estrito (quando < t) e o leito que comeca no zero nunca era cortado: a musica
        # marcada e o Lang Lang tocavam as duas ao mesmo tempo na abertura.
        t = max(0.0, t)
        for fx in faixas:
            if not e_leito(fx):
                continue
            if fx["quando_s"] - 0.05 <= t < fx["quando_s"] + fx["dura_s"]:
                fx["dura_s"] = round(max(0.0, t - fx["quando_s"]), 2)
        fim = marcas_t[k + 1][0] if k + 1 < len(marcas_t) else fim_corpo
        for fx in faixas:
            if e_leito(fx) and t < fx["quando_s"] < fim:
                fim = fx["quando_s"]
        # E PARA NOS FOGUETES DE UM NASCIMENTO, como o Lang Lang automatico para no do
        # Tiago. Os foguetes nao sao leito, por isso nao cortavam nada: a 21 de setembro o
        # Lang Lang marcado no cartao "Mas como e que chegamos aqui?" tocava a volume de
        # leito por baixo dos foguetes do Tiago inteiros e ainda cruzava com o Rei Leao
        # (verificador, medido no render). Parado aqui, o cruzamento do render da-lhe os
        # mesmos 2,2 s a descer por cima dos foguetes que o automatico sempre teve, e a
        # retoma depois da fita encontra-o como encontrava o automatico.
        for t_nasce in (t_tiago, t_clara):
            if t_nasce is not None and t < t_nasce < fim:
                fim = t_nasce
        junta_som(f, t, fim - t, 1.0, "marcada na Mesa, no clip das %.1f s" % t, dentro)

    # A MUSICA DA ABERTURA RETOMA QUANDO A FITA VOLTA, e nao o Rei Leao.
    #
    # O Tiago: "Quando voltamos a timeline depois do Tiago para a vitoria do
    # Guterres e noticias seguintes ate ao nascimento da Clara, nao quero que volte
    # a musica do Rei Leao. Preferia que continuasse onde estava na outra musica
    # antes do nascimento do Tiago. Este comentario e valido independentemente da
    # musica que usar para a intro inicial."
    #
    # Por isso nao se procura o Lang Lang pelo nome. Procura-se o leito que tocava
    # mesmo antes dos foguetes do Tiago, seja ele qual for, marcado na Mesa ou nao, e
    # retoma-se no segundo do ficheiro onde parou. Vai da primeira fita depois do
    # nascimento do Tiago ate onde ia o leito que ela interrompe.
    if t_tiago is not None and t_clara is not None:
        t_volta = next((l["inicio_s"] - desvio for l in linhas
                        if l["tipo"] == "marcos" and t_tiago < l["inicio_s"] - desvio < t_clara), None)
        antes = [fx for fx in faixas if e_leito(fx)
                 and fx["quando_s"] < t_tiago - 0.1 < fx["quando_s"] + fx["dura_s"]]
        depois = [fx for fx in faixas if e_leito(fx) and t_volta is not None
                  and t_tiago < fx["quando_s"] < t_volta < fx["quando_s"] + fx["dura_s"]]
        if t_volta is not None and antes and depois:
            abertura, interrompido = antes[-1], depois[-1]
            # Nunca por cima dos foguetes da Clara: la comeca o bloco dela.
            ate = min(interrompido["quando_s"] + interrompido["dura_s"], t_clara)
            interrompido["dura_s"] = round(t_volta - interrompido["quando_s"], 2)
            junta_som(abertura["ficheiro"], t_volta, ate - t_volta, abertura["ganho"],
                      "retoma a musica da abertura onde parou, na fita que volta antes da Clara",
                      round(abertura["in_s"] + abertura["dura_s"], 2))

    # O LEITO BAIXA POR BAIXO DAS VOZES, E NAO PARA NEM PERDE O SITIO.
    #
    # Era tentador cortar a musica no inicio das vozes e voltar a mete-la a seguir, que e
    # como as musicas marcadas funcionam. Mas cortar e recomecar perde o sitio dentro do
    # ficheiro: voltava ao mesmo compasso, ou a um compasso escolhido a mao, e a retoma
    # do Lang Lang na fita antes da Clara (que conta com in_s + dura_s para saber onde ia)
    # passava a apontar para outro ponto da musica.
    #
    # Por isso o leito NAO E TOCADO. Fica escrita a janela em que ele tem de estar mais
    # baixo, e e o render que lhe puxa o volume para baixo enquanto continua a correr por
    # debaixo. Quando volta a subir esta no ponto em que estaria se as vozes nao
    # existissem, que e a unica maneira de a musica nao dar um salto.
    #
    # A janela vai de VOZ_RAMPA antes da primeira voz ate VOZ_RAMPA depois da ultima, e a
    # descida e a subida demoram esse mesmo tempo: quando a primeira palavra sai, o leito
    # ja la esta em baixo. O som de um video do corpo usa o mesmo mecanismo e a mesma lista.
    #
    # E A CONTA CONTA COM O CRUZAMENTO DO RENDER, que e quem manda no que se ouve. A faixa
    # que sai continua a tocar ate render.CRUZAMENTO segundos por cima da que entra, e a
    # janela era escrita sobre a duracao que fica no CSV, que e a de antes dessa esticada.
    # Um leito que acabasse entre 2,2 s e 0,3 s antes das vozes nao levava janela nenhuma e
    # era esticado para dentro delas: tocava por cima sem baixar os 12 dB e, com «parada»,
    # tocava onde tinha de haver silencio. Bastava uma musica marcada num cartao curto
    # antes da foto do pedido, e na intro que ele pediu a folga era de 0,4 s. A duracao no
    # CSV nao se toca (o render e que estica, e a coluna tem de continuar a dizer o que ele
    # pediu): o que se alarga e a pergunta, com o numero do render e nao com uma copia dele.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render
    for t0_v, t1_v, modo in janelas_vozes:
        alvo = 0.0 if modo == "parada" else 10 ** (VOZ_ABAIXA_DB / 20.0)
        for fx in faixas:
            if not e_leito(fx):
                continue
            if (fx["quando_s"] < t1_v + VOZ_RAMPA
                    and t0_v - VOZ_RAMPA < fx["quando_s"] + fx["dura_s"] + render.CRUZAMENTO):
                fx["abafar"] = ((fx["abafar"] + ";") if fx["abafar"] else "") \
                    + escreve_abafar([(t0_v, t1_v, alvo)])
    faixas.sort(key=lambda fx: fx["quando_s"])

    # AS COLUNAS NOVAS SO ENTRAM QUANDO HA O QUE ESCREVER NELAS. Sem vozes e sem videos no
    # corpo o ficheiro e o mesmo de sempre, byte a byte, e o teste_v3_sem_vozes_igual_ao_byte
    # falha se deixar de ser. A ordem e sempre esta, para uma coluna nova nunca mexer nas
    # anteriores.
    extra = [c for c in ("voz", "abafar", "video") if any(fx.get(c) for fx in faixas)]
    with open(os.path.join(DESTINO, nome + ".som.csv"), "w",
              encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_SOM + extra, extrasaction="ignore")
        w.writeheader()
        w.writerows(faixas)

    total = max(l["fim_s"] for l in linhas)
    print("Montagem %r, a partir da Mesa (%s)" % (nome, versao.get("nome", qual)))
    if versao.get("notas"):
        print("  nota dele: %s" % " ".join(versao["notas"].split()))
    print("  clips: %d    duracao: %d:%02d" % (len(linhas), int(total) // 60, int(total) % 60))
    print()
    for l in linhas:
        print("   %2d  %-8s %6.1f-%6.1f  %-9s %s"
              % (l["ordem"], l["tipo"], l["inicio_s"], l["fim_s"], l["tratamento"],
                 (l["ficheiro"] or l["texto_ecra"])[:52]))
    print()
    print("  som: %d faixas" % len(faixas))
    for f in faixas:
        print("   %6.1fs  dura %5.1fs  x%.2f  %-38s %s"
              % (f["quando_s"], f["dura_s"], f["ganho"], f["ficheiro"][:38], f["nota"]))
    if esticados:
        print()
        print("  ESTICADO POR MIM, para os foguetes acabarem antes das fotos:")
        for txt, antes, depois in esticados:
            print("   cartao %-46s %.1f s -> %.1f s" % ('"' + txt + '"', antes, depois))
    if avisos:
        print()
        print("  AVISOS")
        for a in avisos:
            print("   %s" % a)
    print()
    print("Escrito: %s" % caminho)


if __name__ == "__main__":
    main()
