# -*- coding: utf-8 -*-
"""Exemplo do ponto 5: o fim do filme e os creditos, como na proposta de 28 de setembro e com o que o
Tiago pediu a 30 (DISCUSSAO.md, ponto 5). Nao muda nada; escreve em saida/discussao/ponto5/.

    py -3.11 scripts/discussao/ponto5_creditos.py [--so-dizer | --quadros | --colar | --master]
                                                  [--filme <render.mp4>] [--estado <estado2.json>]
                                                  [--master-em <pasta>] [--sem-telemovel]

--so-dizer so faz as contas; --quadros tira sete fotogramas soltos; --colar, alem do exemplo, cola os
creditos no fim do render mais recente e faz a copia do telemovel do filme inteiro (abaixo de 30 MB).
--master faz o mesmo que o --colar e ainda o FICHEIRO DE ENTREGA: o filme inteiro com os creditos em
1080p, em C:\\casamento-video-media\\saida\\<render>_com_creditos.mp4 (ver master_com_creditos). O
--master-em escolhe outra pasta para ele, e o --estado outra leitura da base. O --sem-telemovel, com o
--master, nao faz as copias do telemovel, a do exemplo e a do filme (o pacote do DaVinci,
scripts/davinci_pacote.py, so quer o master).

O QUE ENTRA:
- as fotos que ele marcou na Mesa com o grupo "Creditos" (lidas da leitura mais recente da base em
  saida/leitura_mesa_N, ou da copia em data/mesa_estado.json). A ORDEM e a dele, a que ele arruma no
  painel dos creditos da Mesa (est.creditos.ordem); sem ela, a de uma versao da Mesa chamada
  "Creditos"; senao, a do numero da Mesa (ver fotos_marcadas);
- os convidados da folha dele em C:\\casamento-video-media\\Convidados\\ (a mais recente), por grupos
  (as etiquetas de familia e de amigos) e por agregado (a coluna Familia), um agregado por linha. A
  folha NAO vai para o Git: sao dados de 140 pessoas;
- os textos que ele escrever no painel dos creditos da Mesa (est.creditos: os cargos, o titulo,
  a data e o titulo e o subtitulo de cada grupo, ver textos_dos_creditos). Sem eles, os de hoje
  (CARGOS, TITULO, DATA e GRUPOS, abaixo). Desde a noite de 2 de outubro (contrato dos cargos,
  saida/discussao/contrato_creditos_cargos.md): de 1 a 8 cargos, cada um com 1 a 4 pessoas, uma por
  linha, e a escolha est.creditos.cargos_primeiro = true, que poe os cargos antes do rolo;
- o estilo da Mesa, do data/montagens/<montagem>.estilo.json que o montar escreve, o mesmo com que o
  render fez o filme: a letra e as cores do letreiro (as do cartao) e a letra e a cor dos nomes (as da
  legenda). Sem ele, as de hoje;
- a musica que ele escolheu no painel dos creditos (est.creditos.musica, ligada a 2 de outubro, ver
  som_dos_creditos). Sem ela, a ultima musica do filme continua de onde o filme a deixa, como sempre.
  Com ela, a passagem e no corte, salvo est.creditos.musica.passagem = "frase" (PASSAGENS): a que sai
  acaba a frase e a dos creditos entra ate 3 s depois. Onde cai a passagem e como soa mede-se com o
  scripts/discussao/juncao_creditos.py.

SEM est.creditos E SEM estilo.json, OS CREDITOS SAEM COMO OS DE 1 DE OUTUBRO (provado a 2 de outubro
com os sete fotogramas do --quadros e o framemd5 do exemplo inteiro), com uma correcao pedida no mesmo
dia: o primeiro cargo entra com o fade de 0,6 s, como os outros, em vez de aparecer ja aceso 1 s depois
de o rolo acabar. Os cargos contam-se agora de onde o rolo acaba, e os creditos ficam 1 s mais
compridos; o rolo e as imagens de cada cargo e do titulo sao as mesmas, so um segundo mais tarde.

NUNCA VAO PARA O ECRA: as etiquetas dos convites e dos contactos, as notas, as que dizem onde alguem
nao pode ficar sentado, e os "Noivos". So as etiquetas de GRUPOS (abaixo) entram.

A FORMA (proposta de 28/09): sem preto entre a historia e os creditos (a sala aplaude no primeiro
preto); os nomes a subir como no cinema, com as fotos marcadas numa coluna ao lado; no fecho os tres
cargos, claros e visiveis; e o titulo "CLARA & TIAGO" com a data, ate ao preto. Letra: Arial Bold, com
o letreiro quente da 098 nos titulos (a letra do titulo final e decisao dele: Arial Bold ou Cormorant).
Tudo a 58 px ou mais, que e o minimo que se le a 15 m (084). Os corpos nao mudam com o estilo: uma letra
que precise de mais do que estes corpos para se ler a 15 m tem aviso, como no montar, e nao se corrige.

OS CARGOS PRIMEIRO (2 de outubro a noite, o Tiago: "permite-nos testar a possibilidade de aparecer
primeiro os tais cargos"): com est.creditos.cargos_primeiro = true vem os cargos, depois o rolo e no fim
o titulo. O primeiro cargo nasce da ultima imagem do filme sem preto, como hoje o rolo, e o rolo entra do
preto depois do ultimo cargo (tempos_dos_creditos diz as contas e porque). Sem a chave, e com tres cargos
de uma pessoa, os creditos sao os de sempre, ao byte: o desenho, a duracao e o som.

AS PARTES, OS NOMES CORRIDOS E A VELOCIDADE (3 de outubro, contrato saida/discussao/contrato_1003.md, pontos
5 e 5b; o Tiago: "Coloca este fecho exatamente com a mesma animacao antes dos creditos", "vamos abolir isso"
dos cargos, "so queremos os nomes dos convidados corridos" e "permite ajustar a velocidade dos nomes e/ou
das fotos"):
- est.creditos.partes: a lista, pela ordem, de "titulo", "cargos" e "rolo" (partes_da_escolha). Sem "cargos"
  nao ha cargo nenhum: nem fotograma, nem segundo, nem aviso. O rolo ou os cargos primeiro nascem do fim do
  filme sem preto; o titulo primeiro so acende depois de o filme se apagar (FILME_APAGA, 3 de outubro a
  tarde); as outras partes acendem do preto, e a ultima acaba no preto (tempos_dos_creditos diz as contas);
- est.creditos.nomes_corridos = true: o rolo so com as linhas dos nomes, sem titulos, subtitulos nem espaco
  entre grupos, pela mesma ordem (rolo_de_nomes);
- est.creditos.velocidade = {fotos, nomes} em px/s (velocidade_da_escolha, avisos_da_velocidade).
Sem estas chaves, tudo igual ao byte (teste_creditos_partes_e_nomes_corridos, teste_creditos_velocidade).

O TITULO POR CIMA DOS NOMES (4 de outubro, o Tiago: "ESCREVE \"Convidados\" NO TOPO DA LISTA DO SCROLL NOS CREDITOS em
cima dos nomes"): est.creditos.titulo_nomes = "Convidados" poe esse titulo no topo do rolo, por cima do primeiro nome, a
subir com ele, no letreiro dos titulos dos grupos (TITULO_CORPO). O rolo fica mais alto, e os tempos contam com isso.
Sem a chave, tudo igual ao byte (teste_creditos_titulo_dos_nomes).
"""
import csv
import glob
import json
import math
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C                     # noqa: E402
from comum import render              # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps   # noqa: E402

L, A, FPS = C.L, C.A, C.FPS
PASTA_CONVIDADOS = r"C:\casamento-video-media\Convidados"
GRUPOS = [  # (etiqueta da folha, titulo, subtitulo) pela ordem dos creditos
    ("Família Clara - Mãe", "FAMÍLIA DA CLARA", "do lado da mãe"),
    ("Família Clara - Pai", "FAMÍLIA DA CLARA", "do lado do pai"),
    ("Família Tiago - Mãe", "FAMÍLIA DO TIAGO", "do lado da mãe"),
    ("Família Tiago - Pai", "FAMÍLIA DO TIAGO", "do lado do pai"),
    ("Amigos ambos - Baltar/Valongo", "AMIGOS DOS DOIS", "Baltar e Valongo"),
    ("Amigos Clara - Morais Leitão", "AMIGOS DA CLARA", "Morais Leitão"),
    ("Amigos Clara - Faculdade", "AMIGOS DA CLARA", "da faculdade"),
    ("Amigos Tiago - Continental/AUMOVIO", "AMIGOS DO TIAGO", "Continental e AUMOVIO"),
    ("Amigos Tiago - PwC", "AMIGOS DO TIAGO", "PwC"),
    ("Amigos Tiago - FEP", "AMIGOS DO TIAGO", "FEP"),
    ("Amigos Tiago - SuperBock", "AMIGOS DO TIAGO", "Super Bock"),
]
CARGOS = [  # (cargo, quem): o texto e dele; estes sao os que o juiz recomendou a 30/09, so para o exemplo
    ("Ideia, textos, música e horas sem conta", "A MÃE DA CLARA"),
    ("Montagem, estrutura e «só mais uma versão»", "O TIAGO"),
    ("Aprovação final e direito de veto", "A CLARA"),
]
# OS CARGOS DELE (contrato dos cargos, 2 de outubro as 19:35). O Tiago: "permite tambem acrescentar mais
# cargos e mais pessoas". A lista vai de 1 a CARGOS_MAX, pela ordem em que aparecem, e cada cargo tem de 1
# a PESSOAS_MAX pessoas, uma por linha no letreiro do quem. Os tres primeiros sao os de hoje onde ele
# deixar um campo vazio; os outros sao so o que ele escreveu.
CARGOS_MAX, PESSOAS_MAX = 8, 4
# O cargo, como sempre foi desenhado: o quem no letreiro a 110 com 0,28 de espaco, centrado a A/2 + 40, e a
# linha do cargo a 58, a A/2 - 80. Com varias pessoas as linhas do letreiro ficam a QUEM_ENTRELINHA do corpo
# umas das outras (a do render.letreiro) e a linha do cargo sobe meio bloco por cada pessoa a mais (ver
# geometria_do_cargo). Cada cargo fica T_CARGO no ecra e acende e apaga em CARGO_ENTRA.
QUEM_CORPO, QUEM_ESPACO, QUEM_ENTRELINHA, QUEM_Y = 110, 0.28, 1.45, 40
CARGO_CORPO, CARGO_Y = 58, -80
T_CARGO, CARGO_ENTRA = 4.2, 0.6
# AS PARTES DOS CREDITOS E A ORDEM DELAS (contrato de 3 de outubro, pontos 5 e 5b). O Tiago: "Coloca este fecho
# exatamente com a mesma animacao antes dos creditos a subir com as fotos e com os nomes", "vamos abolir isso" (os
# cargos) e "quero mesmo poder remover integralmente". est.creditos.partes e a lista, pela ordem, de "titulo",
# "cargos" e "rolo": cada uma no maximo uma vez, e o "rolo" sempre. Ausente e a de hoje (PARTES_HOJE), ou a da 109
# com o cargos_primeiro (PARTES_CARGOS_PRIMEIRO). O titulo acende do preto em TITULO_ACENDE (o suave(u / 1.0) de
# sempre) e apaga-se em TITULO_APAGA_FIM quando e a ultima parte (o fade a preto do fim); a meio apaga-se com o fade
# dos cargos, CARGO_ENTRA (ver tempos_dos_creditos).
PARTES_VALIDAS = ("titulo", "cargos", "rolo")
PARTES_HOJE = ["rolo", "cargos", "titulo"]
PARTES_CARGOS_PRIMEIRO = ["cargos", "rolo", "titulo"]
TITULO_ACENDE, TITULO_APAGA_FIM = 1.0, 2.5
# O TITULO PRIMEIRO SO ACENDE DEPOIS DE O FILME SE APAGAR (3 de outubro a tarde). Ate ai o titulo primeiro nascia da
# ultima imagem do filme ja aceso, e durante cerca de 1 s o «2026» grande do contador do fim e as letras do titulo
# ficavam um por cima do outro (aos 10:15,6 do render das 10h). O Tiago: "o contador apaga-se primeiro, depois acende
# o titulo". Quando a primeira parte e o titulo, a ultima imagem do filme apaga-se para o preto em FILME_APAGA e so
# entao o titulo acende do preto, com a animacao de sempre (TITULO_ACENDE): os dois nunca se veem ao mesmo tempo. O
# preto entre os dois sao dois fotogramas (0,08 s; medido no fim do render das 10h), nao um intervalo: o titulo comeca
# a acender logo que o filme acaba de se apagar. Com o rolo ou os cargos primeiro nada muda (tempos_dos_creditos e
# com_o_fim_do_filme).
FILME_APAGA = 0.7
# A VELOCIDADE DOS CREDITOS (contrato de 3 de outubro, 5b): est.creditos.velocidade = {fotos, nomes} em px/s, cada um
# opcional. Fora destes limites fica como esta, com aviso. Avisa-se quando uma foto fica menos de FOTO_INTEIRA_MIN s
# inteira no ecra, e quando uma linha de nomes passa depressa de mais para a regua de leitura das legendas (XF_CPS
# da Mesa, 12 letras por segundo) no tempo em que esta no ecra.
VEL_FOTOS_LIMITES, VEL_NOMES_LIMITES = (60.0, 300.0), (30.0, 200.0)
FOTO_INTEIRA_MIN, LER_CPS = 2.0, 12.0
TITULO, DATA = "CLARA & TIAGO", "4 DE OUTUBRO DE 2026"
VELOCIDADE_NOMES = 150.0      # px/s: cada linha fica ~7 s no ecra, e o filme fica abaixo dos 900 s
# A COLUNA DAS FOTOS NAO PASSA DISTO. Com as 11 fotos de 30/09 subia a 108 px/s; com as 27 de 1/10
# subia a 286 px/s, e cada foto ficava 1,5 s inteira no ecra. Ele gosta da coluna, por isso fica a
# coluna: quando ela precisa de mais tempo, os creditos esticam e os nomes abrandam para acabarem
# juntos (a 150 px/s cada linha fica ~7 s; mais devagar, fica mais).
VELOCIDADE_FOTOS_MAX = 150.0
COR_NOME = (246, 238, 226)
COR_SUB = (226, 196, 160)
NOME_CORPO, SUB_CORPO = 58, 58
PAINEL_NOMES = (960, 1880)    # x de onde a onde vao os nomes
MARGEM_BRILHO = 60            # o rolo e mais largo do que o painel, para o brilho dos titulos nao ser cortado
LARGURA_FOTO = 760
CENTRO_FOTOS = 460
TITULO_CORPO, TITULO_ESPACO = 60, 0.18
# O TITULO POR CIMA DOS NOMES (est.creditos.titulo_nomes, 4 de outubro): o letreiro de um titulo de grupo, no topo do
# rolo. Com os nomes corridos nao ha subtitulo entre ele e o primeiro nome, e leva este espaco por baixo; por grupos, o
# primeiro titulo de grupo vem os 90 px de sempre depois dele.
TITULO_NOMES_GAP = 30
# OS TEXTOS DELE TEM DE CABER (2 de outubro). Um cargo, um titulo ou uma data que a Mesa deixe escrever
# mais compridos do que o ecra eram cortados nas pontas, e num projetor que ainda corta as bordas
# perdiam-se letras. Mede-se antes de desenhar, contra a zona segura dos titulos da EBU (R 95, 90% da
# largura), e os do rolo contra o painel dos nomes; o que nao cabe para tudo antes de se perder tempo.
# A EXCECAO SAO OS TITULOS DOS GRUPOS: um que nao caiba no painel encolhe ate caber, com aviso
# (corpo_do_titulo), em vez de parar os creditos depois da hora de render.
ZONA_SEGURA = 0.90
# O FICHEIRO DE ENTREGA (--master, 2 de outubro): o filme em 1080p com os creditos, para a sala. CRF 18
# e quase transparente para um render que ja e CRF 20, e o som fica no AAC a 192k do render. O x264 vai
# no veryfast, como a juncao final do render: medido a 2 de outubro no render de 1 de outubro (14:21 com
# os creditos), o medium levou 848 s e deu 359 MB a 49,2 dB do render; o veryfast 369 s, 333 MB e
# 47,6 dB. Os dois estao acima dos 45 dB em que a diferenca deixa de se ver, e sao 8 minutos a menos
# entre a ordem de render e o ficheiro pronto.
PASTA_MASTER = r"C:\casamento-video-media\saida"
MASTER_CRF, MASTER_PRESET, MASTER_SOM = 18, "veryfast", "192k"


def folha_mais_recente():
    folhas = sorted(glob.glob(os.path.join(PASTA_CONVIDADOS, "*.xlsx")), key=os.path.getmtime)
    if not folhas:
        raise SystemExit("Nao ha nenhuma folha de convidados em %s" % PASTA_CONVIDADOS)
    return folhas[-1]


def ler_convidados(caminho):
    """A folha dele, so com o Python de base: um .xlsx e um zip de XML."""
    z = zipfile.ZipFile(caminho)
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    partilhadas = []
    if "xl/sharedStrings.xml" in z.namelist():
        partilhadas = ["".join(t.text or "" for t in si.iter(M + "t"))
                       for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si")]
    linhas = []
    for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(M + "row"):
        vals = {}
        for c in row.findall(M + "c"):
            col = re.match(r"([A-Z]+)", c.get("r")).group(1)
            v, t = c.find(M + "v"), c.get("t")
            if t == "s" and v is not None:
                vals[col] = partilhadas[int(v.text)]
            elif t == "inlineStr":
                vals[col] = "".join(x.text or "" for x in c.iter(M + "t"))
            elif v is not None:
                vals[col] = v.text
        linhas.append(vals)
    cab = {v.strip().lower(): k for k, v in linhas[0].items()}
    out = []
    for l in linhas[1:]:
        def col(nome):
            return (l.get(cab.get(nome, ""), "") or "").strip()
        out.append({"nome": col("nome"), "apelido": col("apelido"), "familia": col("família") or col("familia"),
                    "etiquetas": [x.strip() for x in col("labels").split(",") if x.strip()]})
    return out


def por_grupo(convidados, textos=None):
    """[(titulo, subtitulo, [linhas])]: um agregado por linha, cada pessoa no primeiro grupo seu.

    `textos` e o {etiqueta: (titulo, subtitulo)} que ele escreveu na Mesa (textos_dos_creditos);
    sem ele, os do GRUPOS. Muda so o que se escreve: quem entra em cada grupo e a ordem dos grupos
    sao sempre os do GRUPOS. Dois grupos seguidos com o mesmo titulo partilham-no no rolo, como a
    Mesa conta (credLayout).
    """
    usados, blocos = set(), []
    for etiqueta, titulo, sub in GRUPOS:
        if textos and etiqueta in textos:
            titulo, sub = textos[etiqueta]
        agregados = {}
        for k, c in enumerate(convidados):
            if k in usados or etiqueta not in c["etiquetas"] or not c["nome"]:
                continue
            usados.add(k)
            agregados.setdefault(c["familia"] or "%s-%d" % (c["nome"], k), []).append(
                ("%s %s" % (c["nome"], c["apelido"])).strip())
        if agregados:
            blocos.append((titulo, sub, list(agregados.values())))
    fora = [c for k, c in enumerate(convidados) if k not in usados
            and "Noivos" not in c["etiquetas"]]
    return blocos, fora


def quebrar(pessoas, fonte, largura):
    """Um agregado em linhas, quebrando so entre pessoas: um nome nunca fica partido em dois.

    A medida e a do render (texto_emojis.largura): um emoji num nome conta com a largura que tem a
    cores, e os equivalentes trocam-se; um nome sem nenhum mede-se como sempre, com o getlength().
    """
    linhas, atual = [], ""
    for p in pessoas:
        t = (atual + " · " + p) if atual else p
        if atual and render.texto_emojis.largura(t, fonte) > largura:
            linhas.append(atual)
            atual = p
        else:
            atual = t
    return linhas + ([atual] if atual else [])


def letreiro_1x(linhas, tamanho, espaco):
    let = render.letreiro(linhas, tamanho, espaco, 7)
    return let.resize((let.width // render.LETREIRO_SS, let.height // render.LETREIRO_SS), Image.LANCZOS)


def letra_de_ler(corpo):
    """A letra dos nomes, dos subtitulos e da linha do cargo: a da legenda do estilo da Mesa, que e a
    letra de leitura do filme (084). Sem estilo e o FONTE_TEXTO, aberto como sempre foi."""
    return render.letra("legenda", corpo)


def cor_dos_nomes():
    """A cor dos nomes: a da legenda do estilo, se ele a mudou; senao a COR_NOME de sempre. Os
    subtitulos e a linha do cargo ficam na COR_SUB, o champanhe do letreiro."""
    return render.cor_do_estilo("legenda", "cor", COR_NOME)


def corpo_do_titulo(titulo):
    """O corpo do titulo de um grupo no rolo: o TITULO_CORPO, ou o maior que caiba no painel dos nomes.

    UM TITULO DE GRUPO QUE NAO CABE ENCOLHE, NAO PARA OS CREDITOS (2 de outubro). Ate aqui um titulo
    mais largo do que os 920 px do painel parava tudo: o main() antes de desenhar, e o rolo_de_nomes()
    com um SystemExit. Com o --master isso era depois da hora de render, e o titulo e dele, escrito
    na Mesa. Agora desce de 1 em 1 px ate caber, e diz-se (titulos_que_encolhem); o montar avisa ja
    antes do render. A medida e a do largura_do_letreiro(), a mesma do textos_que_nao_cabem(), na
    letra do cartao do estilo. Um titulo que cabe fica nos 60 de sempre, e o rolo sai igual ao byte.
    """
    painel = PAINEL_NOMES[1] - PAINEL_NOMES[0]
    corpo = TITULO_CORPO
    while corpo > 1 and largura_do_letreiro(titulo, corpo, TITULO_ESPACO) > painel:
        corpo -= 1
    return corpo


def letreiro_do_titulo(titulo):
    """O letreiro do titulo de um grupo a 1x, no corpo do corpo_do_titulo().

    O TITULO ENCOLHIDO FICA NO LUGAR DE UM TITULO DE SEMPRE: o letreiro mais pequeno vai ao meio de
    uma imagem preta com a altura do letreiro a TITULO_CORPO. O rolo corta-o e conta-o como aos
    outros (os 110 px de cima e de baixo), e por isso o rolo tem a mesma altura, os nomes a mesma
    velocidade e os creditos a mesma duracao que com um titulo que cabe: so as letras ficam mais
    pequenas. A Mesa, que conta cada titulo com a mesma altura (titulo_altura), continua certa.
    """
    corpo = corpo_do_titulo(titulo)
    v = letreiro_1x([titulo], corpo, TITULO_ESPACO)
    if corpo == TITULO_CORPO:
        return v
    alto = letreiro_1x(["X"], TITULO_CORPO, TITULO_ESPACO).height     # nao depende do texto, so do corpo
    cheio = Image.new("RGB", (v.width, alto), (0, 0, 0))
    cheio.paste(v, (0, (alto - v.height) // 2))
    return cheio


def titulos_que_encolhem(blocos):
    """[aviso]: os titulos de grupo que nao cabem no painel dos nomes, e o corpo a que vao. Nao para nada.

    Cada titulo diz-se uma vez, como no textos_que_nao_cabem(). Abaixo do corpo minimo da letra do
    cartao (o de data/fontes.json, 58 no Arial Bold, decisao 084) diz-se tambem que nao se le a 15 m.
    """
    painel = PAINEL_NOMES[1] - PAINEL_NOMES[0]
    letras = render.letras_da_mesa()
    ident = render.estilo_ativo().get("cartao", {}).get("fonte") or render.LETRA_OMISSAO
    minimo = (letras.get(ident) or {}).get("corpo_minimo") or 58
    avisos, vistos = [], set()
    for titulo, _sub, _linhas in blocos:
        if titulo in vistos:
            continue
        vistos.add(titulo)
        corpo = corpo_do_titulo(titulo)
        if corpo < TITULO_CORPO:
            avisos.append("o titulo de grupo \"%s\" tem %d px e cabem %d: encolhe de %d para %d px%s; encurta-o na "
                          "Mesa para ficar como os outros"
                          % (titulo, round(largura_do_letreiro(titulo, TITULO_CORPO, TITULO_ESPACO)), painel,
                             TITULO_CORPO, corpo,
                             (", abaixo dos %d que esta letra precisa para se ler a 15 m" % minimo)
                             if corpo < minimo else ""))
    return avisos


def pessoas_do_quem(quem):
    """[pessoa]: as pessoas de um cargo, uma por linha do letreiro do quem.

    O texto vem do textos_dos_creditos(), ja limpo: as pessoas separadas por "\\n", cada uma sem
    espacos nas pontas, nenhuma vazia, ate PESSOAS_MAX. Um quem sem "\\n" e uma pessoa so, tal como
    esta escrito: e o de hoje, e desenha-se igual ao byte. Vazio (um cargo a mais so com o cargo
    escrito) nao tem ninguem.
    """
    if not quem:
        return []
    if "\n" not in quem:
        return [quem]
    return [p.strip() for p in quem.split("\n") if p.strip()]


def corpo_do_quem(pessoas):
    """O corpo do letreiro do quem: QUEM_CORPO (110), ou o maior em que a pessoa mais larga caiba.

    QUEM NAO CABE ENCOLHE, COMO O TITULO DE UM GRUPO (contrato dos cargos, 2 de outubro a noite): as
    pessoas de um cargo descem todas juntas de 1 em 1 px ate a mais larga caber na zona segura dos
    titulos (ZONA_SEGURA, 1728 px), medida como sempre no largura_do_letreiro(), na letra do cartao do
    estilo. Ate aqui um quem mais largo do que isso parava os creditos (textos_que_nao_cabem), e com o
    --master isso era depois da hora de render. Um quem que cabe fica nos 110 de sempre.

    Na altura cabem sempre: com quatro pessoas a 110 as letras, a linha do cargo incluida, vao dos 198
    aos 846 px do ecra, dentro dos 54 a 1026 da zona segura (geometria_do_cargo).
    """
    tela = L * ZONA_SEGURA
    corpo = QUEM_CORPO
    while corpo > 1 and pessoas and max(largura_do_letreiro(p, corpo, QUEM_ESPACO) for p in pessoas) > tela:
        corpo -= 1
    return corpo


def geometria_do_cargo(quem):
    """Onde fica cada coisa de um cargo no ecra: {pessoas, corpo, sobe, y_cargo, y_quem}.

    - `pessoas` e `corpo`: as do pessoas_do_quem() e do corpo_do_quem();
    - `y_quem`: o centro do letreiro do quem (A/2 + QUEM_Y, 580), sempre o de hoje. O letreiro das N
      pessoas e o render.letreiro() com as N linhas, a QUEM_ENTRELINHA (1,45) do corpo umas das outras,
      e cola-se com o meio da imagem neste y, como o de uma pessoa;
    - `sobe`: quanto a linha do cargo sobe para ficar a mesma distancia da primeira pessoa, metade do
      bloco das pessoas a mais, floor((N - 1) * corpo * 1,45 / 2 + 0,5), por esta ordem das contas;
    - `y_cargo`: o centro da linha do cargo, A/2 + CARGO_Y - sobe (460 com uma pessoa).
    Assim o cargo e as pessoas ficam juntos no meio do ecra como hoje: com uma pessoa nada muda (as
    letras vao dos 438 aos 602 px); com quatro a 110 o cargo sobe 239 px, para os 221, e as letras vao
    dos 198 aos 846 (medido nos fotogramas do desenho_dos_creditos).
    """
    pessoas = pessoas_do_quem(quem)
    corpo = corpo_do_quem(pessoas)
    sobe = int(math.floor((len(pessoas) - 1) * corpo * QUEM_ENTRELINHA / 2.0 + 0.5)) if len(pessoas) > 1 else 0
    return {"pessoas": pessoas, "corpo": corpo, "sobe": sobe, "y_cargo": A // 2 + CARGO_Y - sobe,
            "y_quem": A // 2 + QUEM_Y}


def quem_que_encolhe(textos):
    """[aviso]: os cargos cujas pessoas encolhem para caber (corpo_do_quem), e o corpo a que vao. Nao para nada.

    Como o titulos_que_encolhem(): diz-se sempre que encolhe, e abaixo do corpo minimo da letra do
    cartao (o de data/fontes.json, 58 no Arial Bold, decisao 084) diz-se tambem que nao se le a 15 m.
    """
    tela = L * ZONA_SEGURA
    letras = render.letras_da_mesa()
    ident = render.estilo_ativo().get("cartao", {}).get("fonte") or render.LETRA_OMISSAO
    minimo = (letras.get(ident) or {}).get("corpo_minimo") or 58
    avisos = []
    for k, (_cargo, quem) in enumerate(textos["cargos"]):
        pessoas = pessoas_do_quem(quem)
        if not pessoas:
            continue
        corpo = corpo_do_quem(pessoas)
        if corpo >= QUEM_CORPO:
            continue
        larga = max(pessoas, key=lambda p: largura_do_letreiro(p, QUEM_CORPO, QUEM_ESPACO))
        abaixo = (", abaixo dos %d que esta letra precisa para se ler a 15 m" % minimo) if corpo < minimo else ""
        if len(pessoas) == 1:
            avisos.append("quem fez o cargo %d (\"%s\") tem %d px e cabem %d: encolhe de %d para %d px%s; encurta-o "
                          "na Mesa para ficar como os outros"
                          % (k + 1, larga, round(largura_do_letreiro(larga, QUEM_CORPO, QUEM_ESPACO)), round(tela),
                             QUEM_CORPO, corpo, abaixo))
        else:
            avisos.append("as %d pessoas do cargo %d encolhem todas de %d para %d px%s, porque \"%s\" tem %d px e cabem "
                          "%d; encurta esse nome na Mesa para ficarem como os outros"
                          % (len(pessoas), k + 1, QUEM_CORPO, corpo, abaixo, larga,
                             round(largura_do_letreiro(larga, QUEM_CORPO, QUEM_ESPACO)), round(tela)))
    return avisos


def rolo_de_nomes(blocos, corridos=False, titulo_nomes=None):
    """Os nomes todos numa imagem alta, preta, com a largura do painel da direita.

    Um titulo de grupo mais largo do que o painel encolhe ate caber (letreiro_do_titulo) e nunca
    para os creditos; o main() diz quais (titulos_que_encolhem).

    OS NOMES CORRIDOS (contrato de 3 de outubro, ponto 5; o Tiago: "Retira dos creditos aquela parte das
    divisoes por grupinhos. Nos so queremos os nomes dos convidados corridos"): com `corridos` saem os
    titulos e os subtitulos dos grupos e o espaco entre grupos. Ficam so as linhas dos nomes, pela ordem
    de hoje (a dos grupos, e dentro de cada grupo a de hoje), cada uma nos 78 px de sempre.

    O TITULO POR CIMA DOS NOMES (4 de outubro; o Tiago: "ESCREVE \"Convidados\" NO TOPO DA LISTA DO SCROLL NOS
    CREDITOS em cima dos nomes"): com `titulo_nomes` o rolo comeca por esse titulo, no letreiro de um titulo de
    grupo (o mesmo corpo, a mesma letra, e encolhe se nao couber), e os nomes vem por baixo, a subir com ele. Com
    os nomes corridos leva TITULO_NOMES_GAP por baixo; por grupos, o primeiro grupo vem os 90 px de sempre depois.
    O rolo fica mais alto exatamente a altura do titulo mais esse espaco, e o resto e o de sempre, ao byte, mais
    abaixo. Sem ele (None ou ""), o rolo de sempre ao byte.
    """
    larg_texto = PAINEL_NOMES[1] - PAINEL_NOMES[0]
    larg = larg_texto + 2 * MARGEM_BRILHO
    # a letra e a cor do estilo da Mesa (2 de outubro); os titulos dos grupos sao o letreiro do render,
    # que ja traz a letra e as cores do cartao do estilo
    f_nome = letra_de_ler(NOME_CORPO)
    f_sub = letra_de_ler(SUB_CORPO)
    cor_nome = cor_dos_nomes()
    pecas, anterior = [], None
    if titulo_nomes:
        pecas.append(("titulo", letreiro_do_titulo(titulo_nomes)))
        if corridos:
            pecas.append(("gap", TITULO_NOMES_GAP))
    for titulo, sub, linhas in blocos:
        if corridos:
            for ln in linhas:
                for parte in quebrar(ln, f_nome, larg_texto):
                    pecas.append(("nome", parte))
            continue
        if titulo != anterior:
            pecas.append(("gap", 90 if pecas else 0))
            pecas.append(("titulo", letreiro_do_titulo(titulo)))
            anterior = titulo
        else:
            pecas.append(("gap", 40))
        pecas.append(("sub", sub))
        pecas.append(("gap", 14))
        for ln in linhas:
            for parte in quebrar(ln, f_nome, larg_texto):
                pecas.append(("nome", parte))
    altura = 0
    for tipo, v in pecas:
        altura += v if tipo == "gap" else (v.height - 2 * 110 if tipo == "titulo" else 78)
    img = Image.new("RGB", (larg, altura + 20), (0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 0
    for tipo, v in pecas:
        if tipo == "gap":
            y += v
        elif tipo == "titulo":
            corte = v.crop((0, 110, v.width, v.height - 110))       # a folga do letreiro (160), menos o brilho
            camada = Image.new("RGB", img.size, (0, 0, 0))
            camada.paste(corte, ((larg - corte.width) // 2, y))
            img = ImageChops.lighter(img, camada)
            d = ImageDraw.Draw(img)
            y += corte.height
        elif tipo == "sub":
            # um emoji a cores, na letra de emojis, e os equivalentes trocados (render.texto_emojis)
            render.texto_emojis.escrever(d, (larg // 2, y + 36), v, f_sub, COR_SUB, anchor="mm")
            y += 78
        else:
            render.texto_emojis.escrever(d, (larg // 2, y + 36), v, f_nome, cor_nome, anchor="mm")
            y += 78
    return img


def leitura_da_mesa():
    """(est, caminho): a copia mais recente da base da Mesa (saida/leitura_mesa_N, pela hora do
    ficheiro), ou a de data/mesa_estado.json se nao houver nenhuma. O --estado escolhe outra, que e
    como se prova uma ordem ou um texto sem mexer na base."""
    if "--estado" in sys.argv:
        fonte = sys.argv[sys.argv.index("--estado") + 1]
    else:
        leituras = sorted(glob.glob(os.path.join(C.REPO, "saida", "leitura_mesa_*", "montagem", "estado2.json")),
                          key=os.path.getmtime)
        fonte = leituras[-1] if leituras else os.path.join(C.REPO, "data", "mesa_estado.json")
    with open(fonte, encoding="utf-8") as fh:
        return json.load(fh), fonte


def _texto_dele(valor, onde, avisos, fica="fica o de hoje"):
    """Um texto do est.creditos limpo das pontas, ou None (vale o de hoje) se vier vazio ou nao for texto.

    OS SINAIS QUE A LETRA NAO TEM E TEM UM IGUAL A VISTA trocam-se por ele (render.EQUIVALENTES,
    corretor, 2 de outubro): o hifen nao separavel (U+2011) e o hifen U+2010 pelo hifen de sempre, e os
    invisiveis tiram-se. Na leitura 63 o cargo 3 traz o U+2011, que o Arial Bold desenha como uma caixa
    vazia; a Mesa mostra-o como um hifen, e e assim que sai. Um texto sem nenhum sai igual.

    `fica` e o que o aviso diz que fica no lugar de um valor que nao e texto: o de hoje, ou, num cargo
    acrescentado por ele, que nao tem texto de hoje, "fica vazio" (corretor, 2 de outubro a noite).
    """
    if valor is None:
        return None
    if not isinstance(valor, str):
        avisos.append("creditos.%s %r nao e texto, %s" % (onde, valor, fica))
        return None
    return render.com_equivalentes(valor.strip()).strip() or None


def _quem_dele(valor, onde, avisos, fica="fica o de hoje"):
    """O quem de um cargo limpo, ou None (vazio): de 1 a PESSOAS_MAX pessoas separadas por "\\n".

    MAIS PESSOAS POR CARGO (contrato dos cargos, 2 de outubro a noite): a Mesa separa as pessoas com
    uma mudanca de linha. Cada linha e limpa como um texto (_texto_dele: as pontas e os
    equivalentes), as vazias saem, e com mais de PESSOAS_MAX ficam as primeiras, com aviso. Um quem
    sem mudanca de linha e o _texto_dele() de sempre, ao caracter."""
    if isinstance(valor, str) and ("\n" in valor or "\r" in valor):
        linhas = [render.com_equivalentes(p.strip()).strip()
                  for p in valor.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        linhas = [p for p in linhas if p]
        if len(linhas) > PESSOAS_MAX:
            avisos.append("creditos.%s traz %d pessoas e cabem %d: as ultimas %d ficam de fora"
                          % (onde, len(linhas), PESSOAS_MAX, len(linhas) - PESSOAS_MAX))
            linhas = linhas[:PESSOAS_MAX]
        return "\n".join(linhas) or None
    return _texto_dele(valor, onde, avisos, fica)


def cargos_primeiro_da_escolha(cr, avisos):
    """True se o est.creditos pede os cargos antes do rolo (cargos_primeiro), False se nao.

    O CONTRATO DOS CARGOS (2 de outubro, 19:35): so o true poe os cargos primeiro. Ausente, false, null
    ou "" e «Como esta» (primeiro o rolo, depois os cargos), sem aviso. Qualquer outro valor (um "true"
    escrito, um 1) tambem fica «Como esta», com aviso: um valor que nao presta nao muda o filme calado.
    """
    v = cr.get("cargos_primeiro") if isinstance(cr, dict) else None
    if v is True:
        return True
    if v is None or v is False or (isinstance(v, str) and v == ""):
        return False
    avisos.append("creditos.cargos_primeiro %r nao e true: fica como esta (primeiro o rolo, depois os cargos)" % (v,))
    return False


def partes_da_escolha(cr, avisos):
    """A lista das partes dos creditos, pela ordem: o est.creditos.partes, ou a de hoje.

    O CONTRATO DE 3 DE OUTUBRO (ponto 5): uma lista de "titulo", "cargos" e "rolo", cada uma no maximo uma
    vez, com o "rolo" sempre. Ausente, null ou "" e a de hoje: PARTES_HOJE, ou PARTES_CARGOS_PRIMEIRO com o
    cargos_primeiro da 109 (e so ai esse se le, com o aviso de sempre). Uma lista que nao presta (nao e
    lista, uma parte que nao existe, uma repetida, sem o rolo) fica tambem na de hoje, com aviso: um valor
    mal escrito nao muda o filme calado. Maiusculas e espacos nas pontas nao contam.
    """
    v = cr.get("partes") if isinstance(cr, dict) else None
    if v is None or (isinstance(v, str) and v == ""):
        return list(PARTES_CARGOS_PRIMEIRO if cargos_primeiro_da_escolha(cr, avisos) else PARTES_HOJE)
    lista = [p.strip().lower() for p in v if isinstance(p, str)] if isinstance(v, list) else None
    if lista is None or len(lista) != len(v) or any(p not in PARTES_VALIDAS for p in lista) \
            or len(set(lista)) != len(lista) or "rolo" not in lista:
        avisos.append("creditos.partes %r nao e uma lista de \"titulo\", \"cargos\" e \"rolo\", cada uma uma vez e com "
                      "o rolo: fica como esta" % (v,))
        return list(PARTES_CARGOS_PRIMEIRO if cargos_primeiro_da_escolha(cr, avisos) else PARTES_HOJE)
    return lista


def nomes_corridos_da_escolha(cr, avisos):
    """True se o est.creditos.nomes_corridos e true; ausente, false, null ou "" e «Como esta». Outro valor fica
    «Como esta», com aviso (a regra do cargos_primeiro)."""
    v = cr.get("nomes_corridos") if isinstance(cr, dict) else None
    if v is True:
        return True
    if v is None or v is False or (isinstance(v, str) and v == ""):
        return False
    avisos.append("creditos.nomes_corridos %r nao e true: fica como esta (os nomes por grupos)" % (v,))
    return False


def velocidade_da_escolha(cr, avisos):
    """{"fotos": px/s, "nomes": px/s}, so com os que ele escolheu; {} e «Como esta».

    O CONTRATO DE 3 DE OUTUBRO (5b): est.creditos.velocidade = {fotos, nomes}, cada um opcional. As fotos
    vao de 60 a 300 px/s e os nomes de 30 a 200 (VEL_FOTOS_LIMITES, VEL_NOMES_LIMITES). Ausente, null ou ""
    e como esta. Um numero fora dos limites, ou um valor que nao e numero, fica como esta, com aviso.
    """
    v = cr.get("velocidade") if isinstance(cr, dict) else None
    if v is None or (isinstance(v, str) and v == "") or v == {}:
        return {}
    if not isinstance(v, dict):
        avisos.append("creditos.velocidade %r nao e um objeto: fica como esta" % (v,))
        return {}
    saida = {}
    for chave, (lo, hi) in (("fotos", VEL_FOTOS_LIMITES), ("nomes", VEL_NOMES_LIMITES)):
        x = v.get(chave)
        if x is None or (isinstance(x, str) and x == ""):
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not (lo <= float(x) <= hi):
            avisos.append("creditos.velocidade.%s %r nao e um numero de %d a %d px/s: fica como esta"
                          % (chave, x, lo, hi))
            continue
        saida[chave] = float(x)
    return saida


def textos_dos_creditos(est, avisos=None):
    """Os textos que ele escreveu no painel dos creditos da Mesa, com os de hoje onde nao escreveu.

    {"cargos": [(cargo, quem)], "titulo", "data", "grupos": {etiqueta: (titulo, subtitulo)},
    "cargos_primeiro": bool}. Os "grupos" so trazem os que ele mudou. O quem de um cargo com varias
    pessoas traz-as separadas por "\\n" (pessoas_do_quem).

    OS CARGOS DELE (contrato dos cargos, 2 de outubro as 19:35, que muda a regra dos tres juntos):
    est.creditos.cargos e a lista inteira, de 1 a CARGOS_MAX, pela ordem em que aparecem.
    - Nas tres primeiras entradas um campo vazio (ou a entrada vazia, ou null) e o de hoje, campo a
      campo, como sempre: uma lista de tres cargos de uma pessoa da o de sempre, ao byte.
    - Nas outras, um campo vazio fica vazio (so a linha do cargo, ou so as pessoas), e uma entrada com
      os dois vazios nao entra: e a que a Mesa acrescenta antes de ele escrever.
    - Com mais de CARGOS_MAX que entram ficam os primeiros, com aviso. Uma lista vazia, que o contrato
      nao preve (sao 1 a 8), fica nos tres de hoje, com aviso.
    - O quem tem de 1 a PESSOAS_MAX pessoas (_quem_dele).
    est.creditos.cargos_primeiro: ver cargos_primeiro_da_escolha().

    O CONTRATO DE 2 DE OUTUBRO (saida/discussao/contrato_mesa_1002.md): est.creditos = {cargos,
    titulo, data, grupos: {etiqueta: {titulo, sub}}, ordem, musica, cargos_primeiro}. Ausente, ou
    vazio, quer dizer o de hoje, campo a campo, como na Mesa (credCargo, credTitulo, credData,
    credGrupoTexto): um cargo em que ele so mudou o "quem" fica com o cargo de hoje. Os textos
    escrevem-se como ele os escreveu, maiusculas incluidas, que e como a Mesa os mostra.

    O QUE NAO PRESTA FICA NO DE HOJE, COM AVISO, como no estilo: um texto que nao fosse texto ou uma
    etiqueta que nao e de GRUPOS, a cair em silencio, eram creditos a sair diferentes do que ele viu
    sem ninguem saber porque.
    """
    avisos = [] if avisos is None else avisos
    saida = {"cargos": list(CARGOS), "titulo": TITULO, "data": DATA, "grupos": {}, "cargos_primeiro": False,
             "partes": list(PARTES_HOJE), "nomes_corridos": False, "velocidade": {}}
    cr = est.get("creditos")
    if cr in (None, "", {}):
        return saida
    if not isinstance(cr, dict):
        avisos.append("o est.creditos nao e um objeto, ficam os textos de hoje")
        return saida
    # AS PARTES (contrato de 3 de outubro): sem a chave e a ordem de hoje, ou a da 109 com o cargos_primeiro. O
    # cargos_primeiro fica True so na ordem da 109, que e a que o tempos_dos_creditos() de antes sabe fazer.
    saida["partes"] = partes_da_escolha(cr, avisos)
    saida["cargos_primeiro"] = saida["partes"] == PARTES_CARGOS_PRIMEIRO
    saida["nomes_corridos"] = nomes_corridos_da_escolha(cr, avisos)
    saida["velocidade"] = velocidade_da_escolha(cr, avisos)
    # SEM "cargos" NAS PARTES NAO HA CARGOS NENHUNS: nem fotograma, nem segundo, nem aviso (5b). Os textos deles
    # ficam na base (a Mesa guarda-os para os repor) e aqui nao se leem.
    cargos = cr.get("cargos") if "cargos" in saida["partes"] else None
    if "cargos" not in saida["partes"]:
        saida["cargos"] = []
    if cargos is not None:
        if not isinstance(cargos, list):
            avisos.append("creditos.cargos nao e uma lista, ficam os cargos de hoje")
        elif not cargos:
            avisos.append("creditos.cargos vem vazia, ficam os cargos de hoje")
        else:
            lista = []
            for k, c in enumerate(cargos):
                if k < len(CARGOS):
                    # os tres de hoje: vazio e o de hoje, campo a campo
                    cargo_hoje, quem_hoje = CARGOS[k]
                    if c is None:
                        lista.append(CARGOS[k])
                        continue
                    if not isinstance(c, dict):
                        avisos.append("creditos.cargos[%d] nao e um objeto, fica o de hoje" % k)
                        lista.append(CARGOS[k])
                        continue
                    lista.append((_texto_dele(c.get("cargo"), "cargos[%d].cargo" % k, avisos) or cargo_hoje,
                                  _quem_dele(c.get("quem"), "cargos[%d].quem" % k, avisos) or quem_hoje))
                    continue
                # os que ele acrescentou: so o que escreveu, e a entrada vazia nao entra
                if c is None:
                    continue
                if not isinstance(c, dict):
                    avisos.append("creditos.cargos[%d] nao e um objeto, fica de fora" % k)
                    continue
                # um campo que nao e texto fica vazio (nao ha o de hoje), e se nenhum dos dois presta o cargo
                # fica de fora: o aviso diz o que acontece de facto (corretor, 2 de outubro a noite)
                av_k = []
                par = (_texto_dele(c.get("cargo"), "cargos[%d].cargo" % k, av_k, "fica vazio") or "",
                       _quem_dele(c.get("quem"), "cargos[%d].quem" % k, av_k, "fica vazio") or "")
                if par != ("", ""):
                    lista.append(par)
                elif av_k:
                    av_k.append("creditos.cargos[%d] fica de fora: nao tem cargo nem quem escritos" % k)
                avisos.extend(av_k)
            if len(lista) > CARGOS_MAX:
                avisos.append("creditos.cargos traz %d cargos e cabem %d; os ultimos %d ficam de fora"
                              % (len(lista), CARGOS_MAX, len(lista) - CARGOS_MAX))
                lista = lista[:CARGOS_MAX]
            saida["cargos"] = lista
    saida["titulo"] = _texto_dele(cr.get("titulo"), "titulo", avisos) or TITULO
    saida["data"] = _texto_dele(cr.get("data"), "data", avisos) or DATA
    # O TITULO POR CIMA DOS NOMES (4 de outubro): a chave so existe na saida quando ele o escreveu, e por isso sem
    # ela o dicionario e o de sempre. Numa linha so: e um letreiro, e uma mudanca de linha fica um espaco.
    titulo_nomes = _texto_dele(cr.get("titulo_nomes"), "titulo_nomes", avisos, "fica sem titulo por cima dos nomes")
    if titulo_nomes:
        saida["titulo_nomes"] = " ".join(titulo_nomes.split())
    grupos = cr.get("grupos")
    if grupos is not None:
        if not isinstance(grupos, dict):
            avisos.append("creditos.grupos nao e um objeto, ficam os titulos de hoje")
        else:
            de_hoje = {e: (t, s) for e, t, s in GRUPOS}
            for etiqueta, m in grupos.items():
                if etiqueta not in de_hoje:
                    avisos.append("creditos.grupos com uma etiqueta que nao e de GRUPOS, ignorada")
                    continue
                if m is None:
                    continue
                if not isinstance(m, dict):
                    avisos.append("creditos.grupos[%s] nao e um objeto, fica o de hoje" % etiqueta)
                    continue
                t_hoje, s_hoje = de_hoje[etiqueta]
                par = (_texto_dele(m.get("titulo"), "grupos[%s].titulo" % etiqueta, avisos) or t_hoje,
                       _texto_dele(m.get("sub"), "grupos[%s].sub" % etiqueta, avisos) or s_hoje)
                if par != (t_hoje, s_hoje):
                    saida["grupos"][etiqueta] = par
    return saida


def textos_mudados(textos):
    """Onde os textos dos creditos nao sao os de hoje: ["cargo 2", "titulo", "grupo <etiqueta>"...].

    Um cargo a mais do que os tres de hoje diz-se como mudado; com menos, "cargos: N"; com os cargos
    primeiro, "a ordem (os cargos primeiro)"."""
    cargos = textos["cargos"]
    partes = textos.get("partes") or PARTES_HOJE
    # as partes (3 de outubro): a ordem da 109 diz-se como sempre; outra diz a lista, e sem cargos nao se contam
    novas = partes not in (PARTES_HOJE, PARTES_CARGOS_PRIMEIRO)
    return ([("cargo %d" % (k + 1)) for k, par in enumerate(cargos) if k >= len(CARGOS) or par != CARGOS[k]]
            + (["cargos: %d" % len(cargos)] if len(cargos) < len(CARGOS) and "cargos" in partes else [])
            + (["a ordem (os cargos primeiro)"] if textos.get("cargos_primeiro") else [])
            + (["as partes (%s)" % ", ".join(partes)] if novas else [])
            + (["os nomes corridos"] if textos.get("nomes_corridos") else [])
            + (["o titulo por cima dos nomes"] if textos.get("titulo_nomes") else [])
            + (["a velocidade (%s)" % ", ".join("%s %g px/s" % (k, v) for k, v in sorted(textos["velocidade"].items()))]
               if textos.get("velocidade") else [])
            + (["titulo"] if textos["titulo"] != TITULO else []) + (["data"] if textos["data"] != DATA else [])
            + ["grupo %s" % e for e in textos["grupos"]])


def ordem_das_fotos(est):
    """(ids, origem, avisos): as fotos da coluna, pela ordem, como o credFotos() da Mesa as conta.

    A ORDEM E A DELE, 1 de outubro: "Ajustar a ordem e que ainda nao percebi como posso fazer"; e a
    2 de outubro: "ajustar ordem no final das fotos nos creditos de forma simples e pratica enquanto
    os nomes movem". Por isso, pelo contrato de 2 de outubro, manda primeiro a ordem que ele arruma
    no painel dos creditos da Mesa (est.creditos.ordem); sem ela, uma versao da Mesa chamada
    "Creditos" (com ou sem acento, maiusculas ou nao); sem nenhuma, o numero da Mesa, que e a ordem
    em que as fotos entraram na biblioteca.

    - Na ordem dele, uma foto repetida conta uma vez. Uma foto da ordem a que ele tirou a etiqueta
      Creditos sai (com aviso), salvo se estiver na versao "Creditos", que conta como marcada.
    - Na versao "Creditos" conta tudo o que la estiver, pela ordem dos clips e por dentro dos grupos
      (lado a lado, colagem, pilha), mesmo sem a etiqueta, como desde 1 de outubro. Os cartoes nao
      contam.
    - O que tem lugar marcado e ainda nao entrou vai para o fim, com aviso: primeiro as fotos com a
      etiqueta, pelo numero da Mesa, e depois, com a ordem dele, as da versao "Creditos" que ele
      acrescentou depois de arrumar. Nada do que ele marcou desaparece calado.

    A Mesa faz esta mesma conta no browser (credFotos, no editor_base.html; a regra da versao dentro
    da ordem entrou la a 2 de outubro, e aqui com ela). O teste_creditos_seguem_a_ordem_da_mesa corre
    os dois lados sobre os mesmos casos e falha se derem colunas diferentes.
    """
    avisos = []
    pid = next((p["id"] for p in est.get("pessoas", []) if sem_acentos(p.get("nome", "")) == "creditos"), None)
    marcadas = sorted(fid for fid, t in est.get("tags", {}).items() if pid and pid in t)
    tem = set(marcadas)
    versao = next((v for v in est.get("versoes", []) if sem_acentos(v.get("nome", "")) == "creditos"), None)
    da_versao = []
    for c in (versao or {}).get("clips", []):
        for i in ([c["i"]] if c.get("t") == "foto" and c.get("i") else []) + list(c.get("fotos") or []):
            if i not in da_versao:
                da_versao.append(i)
    cr = est.get("creditos") if isinstance(est.get("creditos"), dict) else {}
    ids, vistos, origem = [], set(), "nada"
    if isinstance(cr.get("ordem"), list):
        origem = "ordem"
        perdidas = []
        for i in cr["ordem"]:
            if not isinstance(i, str) or i in vistos:
                continue
            vistos.add(i)
            (ids if (i in tem or i in da_versao) else perdidas).append(i)
        if perdidas:
            avisos.append("na ordem dos creditos mas ja sem a etiqueta Creditos, saem: %s" % ", ".join(perdidas))
    elif versao:
        origem = "versao \"%s\"" % versao.get("nome")
        ids = list(da_versao)
        vistos.update(da_versao)
    elif marcadas:
        origem = "numero"
    fora = []
    for i in marcadas + (da_versao if origem == "ordem" else []):
        if i not in vistos:
            vistos.add(i)
            fora.append(i)
    if fora and origem != "numero":
        avisos.append("com lugar marcado mas fora da %s, vao no fim: %s"
                      % ("ordem dos creditos" if origem == "ordem" else origem, ", ".join(fora)))
    return ids + fora, origem, avisos


def fotos_marcadas(leitura=None):
    """As fotos da coluna dos creditos, pela ordem (ordem_das_fotos), e a leitura da base de onde
    vieram: (caminhos na FINAIS, caminho da leitura). `leitura` e o (est, caminho) do
    leitura_da_mesa(), para nao ler a base duas vezes; sem ele, le-se aqui."""
    est, fonte = leitura or leitura_da_mesa()
    ids, origem, avisos = ordem_das_fotos(est)
    for a in avisos:
        print("  AVISO: %s" % a)
    if origem == "nada":
        if any(sem_acentos(p.get("nome", "")) == "creditos" for p in est.get("pessoas", [])):
            raise SystemExit("O grupo \"Creditos\" da Mesa nao tem fotos, e nao ha versao \"Creditos\" (%s)" % fonte)
        raise SystemExit("Nao ha grupo nem versao \"Creditos\" na Mesa (%s)" % fonte)
    if origem == "ordem":
        print("  ordem das fotos: a que ele arrumou no painel dos creditos da Mesa (%d fotos)" % len(ids))
    elif origem == "numero":
        print("  ordem das fotos: a do numero da Mesa (nao ha versao \"Creditos\")")
    else:
        print("  ordem das fotos: a da %s da Mesa (%d fotos)" % (origem, len(ids)))
    # a versao de cada foto e a do data/finais.csv, mais ninguem a escolhe (decisao 090)
    finais = {r["id"]: os.path.join(render.FINAIS, r["final"])
              for r in csv.DictReader(open(os.path.join(C.REPO, "data", "finais.csv"), encoding="utf-8-sig"))}
    em_falta = [i for i in ids if i not in finais or not os.path.exists(finais[i])]
    if em_falta:
        print("  AVISO: sem ficheiro na FINAIS, ficam de fora: %s" % ", ".join(sorted(em_falta)))
    return [finais[i] for i in ids if i not in em_falta], fonte


def apagar(caminho):
    """Um temporario que o Windows ainda tenha preso fica para tras, em vez de parar o exemplo
    (1 de outubro: o _som.m4a preso parou o --colar depois de os creditos estarem feitos)."""
    try:
        os.remove(caminho)
    except OSError as erro:
        print("  (nao apaguei %s: %s)" % (os.path.basename(caminho), erro))


def sem_acentos(texto):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", texto or "")
                   if not unicodedata.combining(c)).strip().lower()


def coluna_de_fotos(caminhos):
    ims = []
    for c in caminhos:
        im = ImageOps.exif_transpose(Image.open(c)).convert("RGB")      # a rotacao da foto, como o render faz
        im = im.resize((LARGURA_FOTO, round(im.height * LARGURA_FOTO / im.width)), Image.LANCZOS)
        if im.height > 900:
            im = im.crop((0, (im.height - 900) // 2, LARGURA_FOTO, (im.height - 900) // 2 + 900))
        ims.append(im)
    gap = 70
    alto = sum(i.height for i in ims) + gap * (len(ims) - 1)
    col = Image.new("RGB", (LARGURA_FOTO + 40, alto + 40), (0, 0, 0))
    y = 20
    for im in ims:
        # uma sombra quente muito leve a volta, para a foto nao ficar recortada no preto
        halo = Image.new("L", (im.width + 40, im.height + 40), 0)
        ImageDraw.Draw(halo).rectangle((20, 20, im.width + 20, im.height + 20), fill=90)
        halo = halo.filter(ImageFilter.GaussianBlur(10))
        col.paste(Image.new("RGB", halo.size, (120, 90, 60)), (0, y - 20), halo)
        col.paste(im, (20, y))
        y += im.height + gap
    return col


def mascara_das_bordas(margem=170):
    """As pontas de cima e de baixo desvanecem para preto: os nomes nascem e somem sem corte."""
    coluna = Image.new("L", (1, A), 255)
    for y in range(A):
        a = min(1.0, y / margem, (A - 1 - y) / margem)
        coluna.putpixel((0, y), int(255 * max(0.0, a)))
    return coluna.resize((L, A))


def largura_do_letreiro(texto, corpo, espaco):
    """A largura das letras de um letreiro do render a 1x, sem a folga do brilho: a conta do
    render._mascara_letreiro, com a letra do cartao do estilo. Um emoji conta como uma letra, com a
    largura que tem a cores (render.largura_das_letras)."""
    ss = render.LETREIRO_SS
    f = render.letra("cartao", corpo * ss)
    return render.largura_das_letras(texto, f, espaco * corpo * ss) / float(ss)


def textos_que_nao_cabem(textos, blocos, t_titulo=7.0):
    """[problema]: os textos dos creditos mais largos do que o sitio onde vao. Nao muda nada.

    Os subtitulos dos grupos vao no painel dos nomes (920 px). A linha de cada cargo, o titulo final
    e a data vao no ecra inteiro, e medem-se contra a zona segura (ZONA_SEGURA); o titulo final a
    aproximar-se, no tamanho a que chega (render.LETREIRO_EMPURRA por segundo).

    OS TITULOS DOS GRUPOS JA NAO ESTAO AQUI (2 de outubro): um titulo que nao cabe no painel encolhe
    ate caber, e diz-se no titulos_que_encolhem(); nao para os creditos. E QUEM FEZ CADA CARGO TAMBEM
    NAO (contrato dos cargos, 2 de outubro a noite): as pessoas de um cargo que nao cabem encolhem
    todas juntas ate caber (corpo_do_quem), e diz-se no quem_que_encolhe().
    """
    problemas = []
    painel = PAINEL_NOMES[1] - PAINEL_NOMES[0]
    tela = L * ZONA_SEGURA
    f_ler = letra_de_ler(58)

    def mede(o_que, largura, cabe):
        if largura > cabe:
            problemas.append("%s tem %d px e cabem %d: encurta-o na Mesa" % (o_que, round(largura), cabe))

    # o que nao vai ao ecra nao se mede (3 de outubro): com os nomes corridos nao ha subtitulos, e sem o
    # "titulo" nas partes nao ha titulo final nem data; os cargos ja vem vazios sem o "cargos"
    for _titulo, sub, _linhas in ([] if textos.get("nomes_corridos") else blocos):
        mede("o subtitulo \"%s\"" % sub, render.texto_emojis.largura(sub, f_ler), painel)
    for k, (cargo, _quem) in enumerate(textos["cargos"]):
        mede("o cargo %d (\"%s\")" % (k + 1, cargo), render.texto_emojis.largura(cargo, f_ler), tela)
    if "titulo" in (textos.get("partes") or PARTES_HOJE):
        mede("o titulo final \"%s\"" % textos["titulo"],
             largura_do_letreiro(textos["titulo"], 130, 0.18) * (1.0 + render.LETREIRO_EMPURRA * t_titulo), tela)
        mede("a data \"%s\"" % textos["data"], largura_do_letreiro(textos["data"], 58, 0.30), tela)
    return problemas


def caracteres_que_faltam(textos, blocos):
    """[aviso]: os textos dos creditos que nao saem como estao escritos. Nao para nada.

    DESDE A TARDE DE 2 DE OUTUBRO UM EMOJI SAI A CORES (render.texto_emojis), e por isso so se avisa
    de duas coisas: um caracter que nem a letra onde vai nem a letra de emojis tem, que a Pillow
    desenha com o glifo de falta, uma caixa vazia no Arial Bold, sem se queixar (render.caracteres_sem_letra);
    e um emoji de varios caracteres (tom de pele, ZWJ, bandeira, tecla) que esta Pillow, sem o raqm, nao
    junta, e o aviso diz o que sai (texto_emojis.sequencias). E, desde o corretor dessa noite, um emoji
    escuro, que quase nao se ve no preto (texto_emojis.emojis_escuros). Os hifens especiais ja vem trocados
    (_texto_dele) e saem como o hifen de sempre. Os nomes, os subtitulos e a linha do cargo vao na letra
    da legenda; os titulos, quem fez cada cargo, o titulo final e a data no letreiro, na letra do
    cartao. Dos convidados diz-se o grupo e quantos nomes, nunca o nome: estes avisos podem ir parar a
    um registo.
    """
    f_ler = letra_de_ler(58)
    f_cartao = render.letra("cartao", TITULO_CORPO)
    avisos, vistos = [], set()

    def ve(o_que, texto, fonte):
        if (o_que, texto) in vistos:
            return
        vistos.add((o_que, texto))
        fora = render.caracteres_sem_letra(texto, fonte)
        if fora:
            avisos.append("%s tem %s, que nem a letra nem a de emojis tem: no filme sai uma caixa vazia; "
                          "tira-o na Mesa" % (o_que, " e ".join(render.nome_do_caracter(c) for c in fora)))
        for seq, sai in render.texto_emojis.sequencias(texto):
            avisos.append("%s tem o emoji %s, que esta Pillow nao junta (falta-lhe o raqm): %s; troca-o na "
                          "Mesa por um emoji simples" % (o_que, render.texto_emojis.codigos(seq), sai))
        # um emoji escuro quase desaparece no preto dos creditos (corretor, 2 de outubro a noite)
        avisos.extend(a + " na Mesa" for a in render.texto_emojis.aviso_dos_escuros(o_que, texto, fonte))

    def mau(p):
        return render.caracteres_sem_letra(p, f_ler) or render.texto_emojis.sequencias(p)
    corridos = textos.get("nomes_corridos")
    if textos.get("titulo_nomes"):    # o titulo por cima dos nomes vai no letreiro, na letra do cartao (4 de outubro)
        ve("o titulo por cima dos nomes \"%s\"" % textos["titulo_nomes"], textos["titulo_nomes"], f_cartao)
    for titulo, sub, linhas in blocos:
        if not corridos:              # com os nomes corridos os titulos e os subtitulos nao vao ao ecra
            ve("o titulo de grupo \"%s\"" % titulo, titulo, f_cartao)
            ve("o subtitulo \"%s\"" % sub, sub, f_ler)
        maus = [p for ln in linhas for p in ln if mau(p)]
        if maus:
            avisos.append("%d nome%s do grupo \"%s\" (%s) tem caracteres que nao saem como estao escritos "
                          "(uma caixa vazia, ou um emoji que esta Pillow nao junta); corrige-os na folha dos "
                          "convidados" % (len(maus), "s" if len(maus) > 1 else "", titulo, sub))
    for k, (cargo, quem) in enumerate(textos["cargos"]):
        ve("o cargo %d (\"%s\")" % (k + 1, cargo), cargo, f_ler)
        # cada pessoa do cargo a sua vez, com o texto dela (uma pessoa so: o aviso de sempre)
        for pessoa in pessoas_do_quem(quem):
            ve("quem fez o cargo %d (\"%s\")" % (k + 1, pessoa), pessoa, f_cartao)
    if "titulo" in (textos.get("partes") or PARTES_HOJE):
        ve("o titulo final \"%s\"" % textos["titulo"], textos["titulo"], f_cartao)
        ve("a data \"%s\"" % textos["data"], textos["data"], f_cartao)
    return avisos


def avisos_da_letra():
    """O que o estilo le pior a 15 metros, nos creditos, do que a letra de hoje: [aviso]. Nao muda nada.

    A regra e a do montar (avisos_do_estilo, decisao 084 e data/fontes.json): um corpo le-se como
    hoje quando esta para o corpo_minimo da letra como o de hoje esta para o do Arial Bold. Os corpos
    dos creditos nao mudam com o estilo, por isso uma letra de minimo maior le-se pior, e diz-se quanto.
    """
    estilo = render.estilo_ativo()
    letras = render.letras_da_mesa()
    arial = (letras.get(render.LETRA_OMISSAO) or {}).get("corpo_minimo") or 58
    avisos = []
    for parte, usos in (("legenda", (("os nomes, os subtitulos e os cargos", NOME_CORPO),)),
                        ("cartao", (("a data", 58), ("os titulos dos grupos", TITULO_CORPO),
                                    ("quem fez cada cargo", 110), ("o titulo final", 130)))):
        ident = estilo.get(parte, {}).get("fonte")
        if not ident:
            continue
        entrada = letras.get(ident) or {}
        nome = entrada.get("nome") or ident
        minimo = entrada.get("corpo_minimo")
        if not minimo:
            avisos.append("nos creditos, %s ainda nao tem o corpo minimo medido (py -3.11 "
                          "scripts/medir_corpo_minimo.py)" % nome)
            continue
        for quem, corpo in usos:
            como = corpo * arial / float(minimo)
            if como < corpo - 0.5:
                avisos.append("nos creditos, %s em %s a %d: a 15 metros como o Arial Bold a %d, e hoje e %d"
                              % (quem, nome, corpo, int(math.floor(como + 0.5)), corpo))
    return avisos


def alturas_na_coluna(caminhos):
    """[altura]: a altura de cada foto na coluna dos creditos, como o coluna_de_fotos() a faz (a rotacao do
    EXIF, LARGURA_FOTO de largura, ate 900), sem abrir os pixeis."""
    alturas = []
    for c in caminhos:
        im = Image.open(c)
        w, h = im.size
        if im.getexif().get(274) in (5, 6, 7, 8):
            w, h = h, w
        alturas.append(min(900, round(h * LARGURA_FOTO / w)))
    return alturas


def linhas_dos_nomes(blocos):
    """[linha]: as linhas dos nomes do rolo, como o rolo_de_nomes() as parte (as mesmas com ou sem os nomes
    corridos). Ficam so em memoria: sao nomes de convidados."""
    f_nome = letra_de_ler(NOME_CORPO)
    larg = PAINEL_NOMES[1] - PAINEL_NOMES[0]
    return [parte for _t, _s, linhas in blocos for ln in linhas for parte in quebrar(ln, f_nome, larg)]


def letras_de_ler(texto):
    """As letras que contam para a regua de leitura, como a Mesa as conta (os caracteres, menos os invisiveis)."""
    return len(re.sub("[​‍⁠︎️﻿\U000e0020-\U000e007f]", "", texto))


def avisos_da_velocidade(T, alturas, linhas):
    """[aviso] da velocidade que ele escolheu (5b). Sem velocidade, nenhum: «Como esta» nao muda.

    - UMA FOTO QUE FICA MENOS DE FOTO_INTEIRA_MIN (2 s) INTEIRA NO ECRA: inteira e de quando a borda de baixo
      dela entra pelo fundo ate a de cima sair pelo topo, (A - altura) / vel_fotos.
    - OS NOMES QUE PASSAM DEPRESSA DE MAIS: cada linha fica A / vel_nomes no ecra (a 150 px/s, 7,2 s), e a
      regua das legendas pede as letras dela / LER_CPS (12 por segundo, o XF_CPS da Mesa).
    Nunca diz um nome: diz quantas e as letras da maior. As fotos so se dizem com a velocidade das fotos
    escolhida: so com a dos nomes a coluna nunca anda mais depressa do que hoje.
    """
    if not T.get("velocidade"):
        return []
    avisos = []
    vf, vn = T["vel_fotos"], T["vel_nomes"]
    inteiras = [(k + 1, (A - h) / vf) for k, h in enumerate(alturas)] if "fotos" in T["velocidade"] else []
    curtas = [(k, s) for k, s in inteiras if s < FOTO_INTEIRA_MIN]
    if curtas:
        k, s = min(curtas, key=lambda x: x[1])
        avisos.append("a coluna das fotos a %.0f px/s: %d das %d fotos ficam menos de %.0f s inteiras no ecra (a %d.a "
                      "fica %.1f s); abranda as fotos na Mesa" % (vf, len(curtas), len(alturas), FOTO_INTEIRA_MIN, k, s))
    no_ecra = A / vn
    longas = [letras_de_ler(ln) for ln in linhas if letras_de_ler(ln) / LER_CPS > no_ecra]
    if longas:
        avisos.append("os nomes a %.0f px/s: cada linha fica %.1f s no ecra, e %d linhas pedem mais para se lerem a 15 m "
                      "(%d letras por segundo; a maior tem %d letras e pede %.1f s); abranda os nomes na Mesa"
                      % (vn, no_ecra, len(longas), LER_CPS, max(longas), max(longas) / LER_CPS))
    return avisos


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def escolha_da_musica(est):
    """O est.creditos.musica da leitura da base ({ficheiro, inicio}), ou None: «Como esta»."""
    cr = est.get("creditos")
    return cr.get("musica") if isinstance(cr, dict) else None


# A PASSAGEM PARA A MUSICA DOS CREDITOS (2 de outubro, a noite; por decidir pelo Tiago, ver
# scripts/discussao/juncao_creditos.py). est.creditos.musica.passagem:
# - ausente, None, "" ou "corte": a de hoje, e e a omissao. A musica dos creditos entra no corte (o
#   inicio dos creditos), com o fim de frase da 096 se a troca estiver medida nesse sitio
#   (data/fins_de_frase.csv, como dentro do filme). Nada aqui e chamado, e o som sai igual ao byte;
# - "frase": a musica que sai acaba a frase por cima do inicio dos creditos, e a dos creditos so entra
#   quando ela acaba, ate render.TOLERANCIA_FIM_DE_FRASE (3 s) depois do corte. E a mesma troca da 096
#   com o corte do som mais tarde do que o da imagem: o sitio vem de uma linha de data/fins_de_frase.csv
#   com as duas musicas, o segundo da que sai quando a dos creditos entra (no_corte, depois do segundo
#   em que ela esta no corte da imagem) e a entrada da dos creditos nesse instante (entra_in). Com "fim"
#   a entrada anda o mesmo que a espera, e a musica continua a acabar com os creditos; com "inicio" ou um
#   numero fica a mesma, e toca menos esse tempo. Sem essa linha fica no corte, com aviso, como a Mesa.
# A imagem nao muda em nenhuma: os creditos comecam no mesmo fotograma.
PASSAGENS = ("corte", "frase")


def passagem_da_escolha(escolha, avisos=None):
    """"corte" (a omissao, a de hoje) ou "frase", do est.creditos.musica.passagem. O que nao vale e
    "corte", com aviso."""
    p = escolha.get("passagem") if isinstance(escolha, dict) else None
    if p is None or (isinstance(p, str) and not p.strip()):
        return "corte"
    if isinstance(p, str) and p.strip().lower() in PASSAGENS:
        return p.strip().lower()
    if avisos is not None:
        avisos.append("creditos.musica com passagem %r, que nao e corte nem frase: fica no corte" % (p,))
    return "corte"


def espera_pela_frase(sai, entra, no_corte, inicio, medidas, dur, avisos=None):
    """(espera, linha) da passagem "frase": quantos segundos depois do corte da imagem a musica dos
    creditos entra, pela linha de data/fins_de_frase.csv desta troca; (0.0, None) sem ela.

    A linha e a de uma troca da 096 com o corte do som `espera` segundos depois: sai e entra pelos nomes
    dos ficheiros, no_corte o segundo da que sai nesse instante (entre 0,05 s e TOLERANCIA_FIM_DE_FRASE
    depois do `no_corte` da imagem), e entra_in a entrada que a escolha da para os creditos encurtados
    dessa espera (musica_creditos.entrada(inicio, fim, dur - espera)), cada um a menos de 0,05 s. Uma
    linha de outro sitio nao serve: a troca tem de ser medida outra vez (096)."""
    import musica_creditos as mc
    achadas = []
    linhas = []
    if os.path.exists(mc.FINS_DE_FRASE):
        with open(mc.FINS_DE_FRASE, encoding="utf-8-sig", newline="") as fh:
            linhas = list(csv.DictReader(fh))
    for r in linhas:
        if r.get("sai") != sai or r.get("entra") != entra:
            continue
        try:
            nc, ein = float(r["no_corte"]), float(r["entra_in"])
        except (KeyError, TypeError, ValueError):
            continue
        espera = round(nc - float(no_corte), 3)
        if not (0.05 < espera <= render.TOLERANCIA_FIM_DE_FRASE + 1e-6) or espera >= dur:
            continue
        e = mc.entrada(inicio, medidas["fim"], float(dur) - espera, medidas["silencios"])
        if abs(e["in_s"] - ein) < 0.05:
            achadas.append((espera, r))
    if not achadas:
        if avisos is not None:
            avisos.append("musica dos creditos: passagem no fim da frase sem a frase medida (096) para %s aos %.2f s "
                          "do ficheiro no corte; fica no corte" % (sai[:30], float(no_corte)))
        return 0.0, None
    return achadas[-1]


def som_dos_creditos(ultima, pos, antes, dur, escolha, avisos=None, medidas=None, caminho=None):
    """(faixas, info): o som do exemplo dos creditos, para o render.construir_som(ff, faixas, antes + dur,
    saida, render.FADE_FIM_SOM). `info` e None em «Como esta».

    A MUSICA QUE ELE ESCOLHE NA MESA (est.creditos.musica, contrato de 2 de outubro, seccao 6; ligada
    pelo corretor no mesmo dia). Ate aqui a Mesa tocava-a e dizia "o render dos creditos ainda nao usa
    esta escolha", e o --master tocava a de sempre. A juncao e a do musica_creditos.faixas_dos_creditos(),
    a mesma que a Mesa toca (credMusicaJuncao): uma troca de musica como as de dentro do filme.

    «COMO ESTA», SEM ESCOLHA OU COM UMA QUE NAO VALE: a ultima musica do filme continua de onde o filme
    a deixa, como sempre, e o som sai igual ao byte. Uma escolha mal escrita, um ficheiro que ja nao
    esta, ou uma musica que nao chega a tocar, ficam em «Como esta» com aviso, como na Mesa.

    UM SEGUNDO DEPOIS DE A MUSICA SE CALAR VALE "fim", com aviso, como na Mesa (credMusicaEntrada): entre
    o fim audivel e o fim do ficheiro ha silencio (6,2 s nos Queen), e um numero ai deixava os creditos
    inteiros calados. `medidas` e `caminho` servem para os testes nao lerem a biblioteca.

    A PASSAGEM (est.creditos.musica.passagem, ver PASSAGENS): sem ela, ou com "corte", a de sempre; com
    "frase" e a troca medida em data/fins_de_frase.csv, a dos creditos entra `espera` segundos depois do
    inicio deles, quando a que sai acaba a frase, e o info diz passagem, espera e corte_da_imagem.
    """
    import musica_creditos as mc
    avisos = [] if avisos is None else avisos
    esc, erro = mc.escolha_valida(escolha)
    if erro:
        avisos.append(erro)
    if esc is not None:
        real = esc["ficheiro"]
        if caminho is None:
            real, caminho = mc.resolver(esc["ficheiro"])
        if not real:
            avisos.append("musica dos creditos nao encontrada, fica como esta: %s" % esc["ficheiro"])
        else:
            m = medidas or mc.medir(caminho)
            if not isinstance(esc["inicio"], str) and esc["inicio"] >= m["fim"]:
                avisos.append("musica dos creditos: aos %.2f s %s ja se calou (cala-se aos %.2f s): toca como "
                              "\"fim\", como na Mesa" % (esc["inicio"], real[:40], m["fim"]))
                esc = dict(esc, inicio="fim")
            # A PASSAGEM NO FIM DA FRASE (est.creditos.musica.passagem = "frase"): a mesma juncao, com o corte do
            # som `espera` segundos depois do da imagem. Sem ela (a omissao), a chamada de sempre.
            espera = 0.0
            if passagem_da_escolha(escolha, avisos) == "frase":
                espera, _linha = espera_pela_frase(ultima["ficheiro"], real, float(pos) + float(antes), esc["inicio"],
                                                   m, dur, avisos)
            if espera > 0:
                feito = mc.faixas_dos_creditos(ultima, pos, antes + espera, dur - espera, dict(esc, ficheiro=real),
                                               avisos, m, caminho)
                if feito and len(feito[0]) == 2:
                    feito[1].update({"passagem": "frase", "espera": espera,
                                     "corte_da_imagem": round(float(pos) + float(antes), 3)})
            else:
                feito = mc.faixas_dos_creditos(ultima, pos, antes, dur, dict(esc, ficheiro=real), avisos, m, caminho)
            if feito:
                return feito
            avisos.append("musica dos creditos: %s nao chega a tocar, fica como esta" % real[:40])
    # «Como esta»: a ultima musica do filme continua de onde o filme a deixa (as linhas de sempre)
    total = antes + dur
    livre = C.duracao(ultima["caminho"]) - pos
    e = dict(ultima)
    e.pop("_subida", None)
    e.update({"quando": 0.0, "in_s": pos, "dura": min(total, livre), "dura_medida": min(total, livre),
              "subida": render.SUBIDA_NUM_INICIO, "cruza": 0.0})
    return [e], None


def tempos_dos_creditos(alto_rolo, alto_coluna, n_cargos, cargos_primeiro=False, partes=None, velocidade=None):
    """Os tempos dos creditos, pelas alturas do rolo de nomes e da coluna de fotos: um dicionario com
    t_rolo, vel_nomes, vel_fotos, t_cargo, t_titulo, t_entrada, t_fim_rolo, t_cargos e dur, e ainda
    primeiro ("rolo" ou "cargos"), n_cargos, t_rolo_entra e t_titulo_entra.

    O relogio e o dos creditos: o zero e onde o fim do filme comeca a desfazer-se neles (t_entrada).
    - t_cargos: onde comeca a conta do primeiro cargo (o u = 0 dele); o cargo k comeca em
      t_cargos + k * t_cargo e fica t_cargo, a acender e a apagar em CARGO_ENTRA;
    - t_rolo_entra: onde o rolo comeca a entrar (o tr = -t_entrada do desenho), e t_titulo_entra onde o
      titulo final comeca a acender.

    «COMO ESTA» (cargos_primeiro False, a omissao): o rolo, os cargos e o titulo, com as contas e os
    numeros de sempre, ao bit: t_rolo_entra = 0, t_cargos = t_entrada + t_rolo + t_fim_rolo,
    t_titulo_entra = t_cargos + n_cargos * t_cargo e dur = t_titulo_entra + t_titulo.

    OS CARGOS PRIMEIRO (est.creditos.cargos_primeiro = true, contrato dos cargos de 2 de outubro):
    - O PRIMEIRO CARGO NASCE DA ULTIMA IMAGEM DO FILME, SEM PRETO, como hoje nasce o rolo: nos
      t_entrada (1,5 s) do inicio o fim do filme desfaz-se no cargo ja aceso (o main() faz esse
      encadeado, como sempre). Fica depois 3,0 s inteiro e apaga-se em 0,6 s, como os outros; por isso a
      conta dele comeca CARGO_ENTRA antes do fim da entrada, t_cargos = t_entrada - CARGO_ENTRA (0,9 s).
      Porque: a sala aplaude no primeiro preto (a forma de 28 de setembro). Com um preto entre a historia
      e o primeiro cargo, o aplauso cobria o cargo da mae da Clara; assim o primeiro preto vem depois dele.
    - Os outros cargos acendem e apagam do preto, como hoje.
    - O ROLO ENTRA DO PRETO DEPOIS DO ULTIMO CARGO, com a entrada de sempre: t_entrada (1,5 s) a acender,
      com os nomes e as fotos ja a andar, como hoje a sair do filme, so que a sair do preto em que o
      ultimo cargo acabou. t_rolo_entra = t_cargos + n_cargos * t_cargo. Dai para a frente e o rolo de
      sempre, a mesma imagem no mesmo tr: sobe, apaga-se e fica preto o t_fim_rolo.
    - O titulo final acende do preto no fim, como hoje: t_titulo_entra = t_rolo_entra + t_entrada +
      t_rolo + t_fim_rolo, e dur = t_titulo_entra + t_titulo.
    Fica t_entrada - CARGO_ENTRA (0,9 s) mais comprido do que «Como esta» com os mesmos cargos: o
    primeiro cargo entra em 1,5 s em vez de 0,6, e o rolo continua a entrar em 1,5 s.

    AS PARTES NOUTRA ORDEM (`partes`, contrato de 3 de outubro, ponto 5). Sem `partes` vale o
    cargos_primeiro; as duas ordens de antes (PARTES_HOJE e PARTES_CARGOS_PRIMEIRO) fazem as contas acima,
    ao bit. Outra lista faz-as parte a parte, pela ordem, e o T traz "janelas" [(parte, ini, fim)]:
    - O ROLO OU OS CARGOS PRIMEIRO NASCEM DA ULTIMA IMAGEM DO FILME, SEM PRETO, como os cargos primeiro da
      109: o main() desfaz o fim do filme neles em t_entrada (1,5 s), e ja estao acesos. O rolo comeca no
      zero, como hoje; o primeiro cargo t_entrada - CARGO_ENTRA (0,9 s) antes de ficar inteiro, como na 109.
    - O TITULO PRIMEIRO SO ACENDE DEPOIS DE O FILME SE APAGAR (3 de outubro a tarde, o Tiago: "o contador
      apaga-se primeiro, depois acende o titulo"): a ultima imagem do filme apaga-se para o preto em
      FILME_APAGA (0,7 s, o T["filme_apaga"], que so existe neste caso) e o titulo acende do preto a seguir,
      em TITULO_ACENDE, como quando nao e o primeiro: t_titulo_entra = FILME_APAGA. Fica inteiro o mesmo
      tempo que hoje, e os creditos FILME_APAGA mais compridos (ate ai eram 0,5 s: o filme desfazia-se no
      titulo ja aceso, e o ano do contador do fim e as letras do titulo viam-se um por cima do outro).
    - AS OUTRAS ACENDEM DO PRETO: o rolo com a entrada de sempre (t_entrada, ja a andar), cada cargo em
      CARGO_ENTRA, o titulo em TITULO_ACENDE, como hoje.
    - UMA PARTE QUE NAO E A ULTIMA APAGA-SE PARA O PRETO antes da seguinte: os cargos e o rolo como sempre
      (o rolo com o t_fim_rolo de hoje), e o titulo com o fade dos cargos (CARGO_ENTRA) em vez dos 2,5 s.
    - A ULTIMA ACABA COM O FADE A PRETO DO FIM: o titulo com os TITULO_APAGA_FIM de hoje (T["titulo_apaga"]),
      o rolo com o seu apagar e o t_fim_rolo, os cargos com o do ultimo cargo.
    Cada parte dura o de hoje: o titulo t_titulo (7,0 s), os cargos n_cargos x t_cargo, o rolo t_entrada +
    t_rolo + t_fim_rolo; e a primeira o que nasce antes (0, 0,9 ou 0,7 s). Sem "cargos" (ou sem cargos) nao
    ha segundo nenhum deles, e t_cargos e None; sem "titulo", t_titulo_entra e None.

    A VELOCIDADE (`velocidade`, {fotos, nomes} em px/s, contrato de 3 de outubro, 5b). Sem ela, a regra de
    sempre, ao bit. Com ela: cada um que ele escolheu anda a essa velocidade; o outro anda pela regra de hoje
    (ate 150 px/s, a acabar com o primeiro se der). t_rolo e o fim do que acaba depois, e o T traz
    "fim_nomes" e "fim_fotos" (o tr em que cada um acaba) e "parado" (quem acaba primeiro e quantos segundos
    fica parado no fim, ou None): o desenho para-o la (rolo_em).
    """
    if velocidade:
        dn, df = alto_rolo + A * 0.55, alto_coluna + A * 0.4
        vn_cap = velocidade.get("nomes") or VELOCIDADE_NOMES
        vf_cap = velocidade.get("fotos") or VELOCIDADE_FOTOS_MAX
        t_rolo = max(dn / vn_cap, df / vf_cap)
        vel_nomes = vn_cap if velocidade.get("nomes") else dn / t_rolo
        vel_fotos = vf_cap if velocidade.get("fotos") else df / t_rolo
        fim_nomes, fim_fotos = dn / vel_nomes, df / vel_fotos
        parado = None
        if abs(fim_nomes - fim_fotos) > 0.02:
            parado = ("nomes", t_rolo - fim_nomes) if fim_nomes < fim_fotos else ("fotos", t_rolo - fim_fotos)
        extra = {"fim_nomes": fim_nomes, "fim_fotos": fim_fotos, "parado": parado, "velocidade": dict(velocidade)}
    else:
        # do primeiro titulo a meio do ecra ate sair tudo; o que for mais lento, nomes ou fotos, manda
        t_rolo = max((alto_rolo + A * 0.55) / VELOCIDADE_NOMES, (alto_coluna + A * 0.4) / VELOCIDADE_FOTOS_MAX)
        vel_nomes = (alto_rolo + A * 0.55) / t_rolo
        vel_fotos = (alto_coluna + A * 0.4) / t_rolo
        extra = {}
    t_cargo, t_titulo, t_entrada = T_CARGO, 7.0, 1.5
    if partes is None:
        partes = PARTES_CARGOS_PRIMEIRO if cargos_primeiro else PARTES_HOJE
    partes = [p for p in partes if p != "cargos" or n_cargos > 0]
    cargos_primeiro = partes == PARTES_CARGOS_PRIMEIRO
    extra["partes"] = list(partes)
    if partes not in (PARTES_HOJE, PARTES_CARGOS_PRIMEIRO):
        t_fim_rolo = 1.0
        t, janelas = 0.0, []
        t_cargos = t_rolo_entra = t_titulo_entra = None
        for k, p in enumerate(partes):
            ini = t
            if p == "rolo":
                t_rolo_entra = t
                t = t + t_entrada + t_rolo + t_fim_rolo
            elif p == "cargos":
                t_cargos = (t + t_entrada - CARGO_ENTRA) if k == 0 else t
                t = t_cargos + n_cargos * t_cargo
            else:
                # o titulo primeiro acende do preto depois de o filme se apagar; a meio, logo que a de antes acaba
                t_titulo_entra = (t + FILME_APAGA) if k == 0 else t
                t = t_titulo_entra + t_titulo
            janelas.append((p, ini, t))
        extra.update({"janelas": janelas,
                      "titulo_apaga": TITULO_APAGA_FIM if partes[-1] == "titulo" else CARGO_ENTRA})
        if partes[0] == "titulo":
            extra["filme_apaga"] = FILME_APAGA        # so com o titulo primeiro: ver com_o_fim_do_filme()
        T = {"t_rolo": t_rolo, "vel_nomes": vel_nomes, "vel_fotos": vel_fotos, "t_cargo": t_cargo,
             "t_titulo": t_titulo, "t_entrada": t_entrada, "t_fim_rolo": t_fim_rolo, "t_cargos": t_cargos,
             "dur": t, "primeiro": partes[0], "n_cargos": n_cargos if "cargos" in partes else 0,
             "t_rolo_entra": t_rolo_entra, "t_titulo_entra": t_titulo_entra}
        T.update(extra)
        return T
    # O PRIMEIRO CARGO ENTRA COM O FADE, COMO OS OUTROS (2 de outubro). O rolo ainda ocupa o segundo a
    # seguir ao t_rolo (desvanece ate +0,8 s e fica preto ate +1,0, o "if tr < t_rolo + 1.0" do
    # desenho_dos_creditos), e os cargos contavam-se do t_rolo: o primeiro so aparecia com u = 1,0, ja
    # aceso, sem os 0,6 s de entrada, e ficava 2,6 s inteiro contra os 3,0 dos outros. Agora os cargos
    # contam-se de onde o rolo acaba (t_cargos), cada um com os mesmos 4,2 s, e os creditos ficam 1 s
    # mais compridos. A Mesa (credLayout e credDesenhaEm) tem de somar o mesmo segundo.
    t_fim_rolo = 1.0                     # o mesmo 1,0 do if do rolo, no desenho_dos_creditos
    if cargos_primeiro:
        t_cargos = t_entrada - CARGO_ENTRA                         # o primeiro ja aceso no fim da entrada
        t_rolo_entra = t_cargos + n_cargos * t_cargo
        t_titulo_entra = t_rolo_entra + t_entrada + t_rolo + t_fim_rolo
        dur = t_titulo_entra + t_titulo
    else:
        t_cargos = t_entrada + t_rolo + t_fim_rolo        # no relogio dos creditos, onde entra o primeiro cargo
        dur = t_cargos + n_cargos * t_cargo + t_titulo
        t_rolo_entra, t_titulo_entra = 0.0, t_cargos + n_cargos * t_cargo
    T = {"t_rolo": t_rolo, "vel_nomes": vel_nomes, "vel_fotos": vel_fotos, "t_cargo": t_cargo,
         "t_titulo": t_titulo, "t_entrada": t_entrada, "t_fim_rolo": t_fim_rolo, "t_cargos": t_cargos,
         "dur": dur, "primeiro": "cargos" if cargos_primeiro else "rolo", "n_cargos": n_cargos,
         "t_rolo_entra": t_rolo_entra, "t_titulo_entra": t_titulo_entra}
    T.update(extra)
    return T


def desenho_dos_creditos(rolo, coluna, textos, estilo, T):
    """creditos(t) -> o fotograma dos creditos no instante t (relogio dos creditos), em RGB 1920x1080.

    `textos` e o do textos_dos_creditos(), `estilo` o que o render.aplicar_estilo() devolveu, e `T` o
    do tempos_dos_creditos(). Fora do main() para se poder provar o desenho sem a folha dele nem as
    fotos da FINAIS (teste_creditos_primeiro_cargo_entra_com_fade).

    A ORDEM E A DO T (T["primeiro"], do tempos_dos_creditos, que diz porque). «Como esta» e o desenho
    de sempre, as mesmas contas pela mesma ordem; com os cargos primeiro, cada peca (um cargo, o rolo
    num tr, o titulo num u) e a mesma imagem, noutro instante. Um T sem "primeiro" (de antes desta
    noite) e «Como esta». Cada cargo desenha-se pela geometria_do_cargo(): uma pessoa como sempre,
    varias umas por baixo das outras no letreiro do quem.
    """
    t_rolo, vel_nomes, vel_fotos = T["t_rolo"], T["vel_nomes"], T["vel_fotos"]
    t_cargo, t_titulo, t_entrada, t_fim_rolo = T["t_cargo"], T["t_titulo"], T["t_entrada"], T["t_fim_rolo"]
    primeiro = T.get("primeiro", "rolo")
    # OS NOMES TITULO E DATA FICAM, AGORA COM O TEXTO DELE: o teste das medidas da Mesa
    # (teste_medidas_dos_creditos_iguais_ao_ponto5) procura as linhas do letreiro final por eles
    TITULO, DATA = textos["titulo"], textos["data"]
    preto = Image.new("RGB", (L, A), (0, 0, 0))
    bordas = mascara_das_bordas()
    cargos = []
    for cargo, quem in textos["cargos"]:
        g = geometria_do_cargo(quem)
        nome_img = letreiro_1x(g["pessoas"], g["corpo"], QUEM_ESPACO) if g["pessoas"] else None
        cargos.append((nome_img, cargo, g))
    # a linha do cargo na letra de ler do estilo; sem estilo, o Arial Bold aberto como sempre
    f_cargo = ImageFont.truetype(render.FONTE_TEXTO, CARGO_CORPO) if "fonte" not in estilo.get("legenda", {}) \
        else letra_de_ler(CARGO_CORPO)
    titulo_let = render.letreiro([TITULO], 130, 0.18, 11)
    data_let = letreiro_1x([DATA], 58, 0.30)

    # A VELOCIDADE DELE (5b): cada lado para no fim dele (fim_nomes, fim_fotos); sem ela, o de sempre
    fim_nomes, fim_fotos = T.get("fim_nomes"), T.get("fim_fotos")

    def rolo_em(tr):
        """O rolo dos nomes e a coluna das fotos no instante tr do rolo (0 = o primeiro titulo a meio)."""
        tela = preto.copy()
        y0 = int(A * 0.45 - tr * vel_nomes)                # o primeiro titulo comeca a meio do ecra
        if fim_nomes is not None and tr > fim_nomes:       # os nomes ja acabaram: parados no fim deles
            y0 = int(A * 0.45 - fim_nomes * vel_nomes)
        tela.paste(rolo, (PAINEL_NOMES[0] - MARGEM_BRILHO, y0))
        yf = int(A * 0.10 - tr * vel_fotos)
        if fim_fotos is not None and tr > fim_fotos:       # a coluna ja acabou: parada no fim dela
            yf = int(A * 0.10 - fim_fotos * vel_fotos)
        tela.paste(coluna, (CENTRO_FOTOS - coluna.width // 2, yf))
        tela = Image.composite(tela, preto, bordas)
        if tr > t_rolo - 0.8:
            tela = Image.blend(tela, preto, suave((tr - t_rolo + 0.8) / 1.6))
        return tela

    def cargo_em(k, u, ja_aceso=False):
        """O cargo k no instante u dele (0 a t_cargo); `ja_aceso`: o primeiro, com os cargos primeiro, nasce
        do fim do filme ja aceso (o encadeado e o do main()), e so se apaga."""
        tela = preto.copy()
        nome_img, cargo, g = cargos[k]
        entra = 1.0 if (ja_aceso and u < CARGO_ENTRA) else suave(u / CARGO_ENTRA)
        alfa = entra * (1.0 - suave((u - t_cargo + CARGO_ENTRA) / CARGO_ENTRA))
        if nome_img is not None:
            tela.paste(nome_img, ((L - nome_img.width) // 2, g["y_quem"] - nome_img.height // 2))
        if cargo:
            render.texto_emojis.escrever(ImageDraw.Draw(tela), (L // 2, g["y_cargo"]), cargo, f_cargo, COR_SUB,
                                         anchor="mm")
        return Image.eval(tela, lambda v, a=alfa: int(v * a))

    def titulo_em(u, apaga=2.5):
        """O titulo final e a data no instante u deles, a acender em 1 s e a apagar nos ultimos 2,5 s.

        Com as partes noutra ordem (3 de outubro): `apaga` e o fade do fim, ou o dos cargos se nao for a
        ultima. O TITULO ACENDE SEMPRE DO PRETO: quando e a primeira parte, depois de o filme se apagar
        (FILME_APAGA, 3 de outubro a tarde); antes do u = 0 e preto, e ja nao nasce aceso do fim do filme."""
        fundo = render.pousar_letreiro(titulo_let, u)
        camada = preto.copy()
        camada.paste(data_let, ((L - data_let.width) // 2, A // 2 + 110 - data_let.height // 2))
        fundo = ImageChops.screen(fundo, camada)
        alfa = suave(u / 1.0) * (1.0 - suave((u - (t_titulo - 2.5)) / 2.5))
        if apaga != 2.5:
            alfa = suave(u / TITULO_ACENDE) * (1.0 - suave((u - (t_titulo - apaga)) / apaga))
        return Image.eval(fundo, lambda v, a=alfa: int(v * a))

    def creditos_por_partes(t):
        """AS PARTES NOUTRA ORDEM (T["janelas"], tempos_dos_creditos): a parte em que t cai, ou a ultima."""
        janelas = T["janelas"]
        k = next((j for j, (_p, _ini, fim) in enumerate(janelas) if t < fim), len(janelas) - 1)
        parte = janelas[k][0]
        if parte == "rolo":
            tr = t - T["t_rolo_entra"] - t_entrada
            tela = rolo_em(tr)
            if k > 0 and tr < 0:                    # a primeira e o main() que a desfaz do filme
                tela = Image.blend(preto, tela, suave((tr + t_entrada) / t_entrada))
            return tela
        if parte == "cargos":
            tc = t - T["t_cargos"]
            j = min(int(tc // t_cargo) if tc > 0 else 0, len(cargos) - 1)
            return cargo_em(j, tc - j * t_cargo, ja_aceso=(k == 0 and j == 0))
        # o titulo primeiro tambem acende do preto: antes do t_titulo_entra (FILME_APAGA) o desenho e preto, e o
        # main() apaga o fim do filme nesse tempo (com_o_fim_do_filme)
        return titulo_em(t - T["t_titulo_entra"], apaga=T["titulo_apaga"])

    def creditos(t):
        if T.get("janelas"):
            return creditos_por_partes(t)
        if primeiro == "cargos":
            # OS CARGOS PRIMEIRO: o primeiro ja aceso desde o zero (o main() desfaz o fim do filme nele),
            # depois um de cada vez do preto; o rolo a entrar do preto; e o titulo
            tc = t - T["t_cargos"]
            k = int(tc // t_cargo) if tc > 0 else 0
            if k < len(cargos):
                return cargo_em(k, tc - k * t_cargo, ja_aceso=(k == 0))
            tr = t - T["t_rolo_entra"] - t_entrada
            if tr < t_rolo + 1.0:
                tela = rolo_em(tr)
                if tr < 0:
                    tela = Image.blend(preto, tela, suave((tr + t_entrada) / t_entrada))
                return tela
            return titulo_em(t - T["t_titulo_entra"])
        tr = t - t_entrada
        if tr < t_rolo + 1.0:
            return rolo_em(tr)
        # os cargos contam-se de onde o rolo acaba, e o primeiro acende do preto como os outros; o max()
        # guarda o primeiro fotograma de um arredondamento para baixo (k = -1 seria o ultimo cargo)
        tc = max(0.0, tr - t_rolo - t_fim_rolo)
        k = int(tc // t_cargo)
        if k < len(cargos):
            return cargo_em(k, tc - k * t_cargo)
        return titulo_em(tc - len(cargos) * t_cargo)
    return creditos


def com_o_fim_do_filme(ultimo, im, tt, T):
    """O fotograma `im` dos creditos, do instante tt deles, com a ultima imagem do filme (`ultimo`) ainda por cima.

    O ROLO OU OS CARGOS PRIMEIRO: o fim do filme desfaz-se neles, ja acesos, em t_entrada (1,5 s), sem preto. E a
    mistura de sempre, ao byte.

    O TITULO PRIMEIRO (T["filme_apaga"], 3 de outubro a tarde; o Tiago: "o contador apaga-se primeiro, depois acende
    o titulo"): o filme apaga-se para o preto em FILME_APAGA e o titulo so acende depois. Ate la o desenho dos
    creditos e preto (o titulo_em antes do u = 0), e por isso a mesma mistura e so o filme a apagar-se: o ano do
    contador do fim e as letras do titulo nunca estao no ecra ao mesmo tempo.
    """
    desfaz = T.get("filme_apaga") or T["t_entrada"]
    if tt < desfaz:
        return Image.blend(ultimo, im, suave(tt / desfaz))
    return im


def main():
    t_inicio = time.time()
    pasta = C.pasta("ponto5")
    # O ESTILO DA MESA (2 de outubro): o mesmo estilo.json com que o render fez o filme, para os
    # creditos terem a letra e as cores do resto. Sem ele, o de sempre.
    estilo = render.aplicar_estilo(render.ler_estilo(C.MONTAGEM))
    if estilo:
        print("estilo da Mesa (%s.estilo.json): %s" % (C.MONTAGEM, ", ".join(
            "%s.%s=%s" % (parte, chave, v) for parte in sorted(estilo) for chave, v in sorted(estilo[parte].items())
            if parte in ("legenda", "cartao"))))
    for a in avisos_da_letra():
        print("  AVISO: %s" % a)
    # OS TEXTOS DELE (est.creditos), da mesma leitura da base de onde vem a ordem das fotos
    leitura = leitura_da_mesa()
    avisos = []
    textos = textos_dos_creditos(leitura[0], avisos)
    for a in avisos:
        print("  AVISO: %s" % a)
    mudados = textos_mudados(textos)
    print("textos dos creditos: %s" % (("os dele em " + ", ".join(mudados)) if mudados else "os de hoje"))
    caminho = folha_mais_recente()
    convidados = ler_convidados(caminho)
    blocos, fora = por_grupo(convidados, textos["grupos"])
    fotos, fonte = fotos_marcadas(leitura)
    print("folha: %s, %d convidados; %d nos creditos em %d grupos; %d sem grupo de creditos"
          % (os.path.basename(caminho), len(convidados), sum(1 for c in convidados) - len(fora)
             - sum(1 for c in convidados if "Noivos" in c["etiquetas"]), len(blocos), len(fora)))
    # um --estado noutro disco nao tem caminho relativo ao repositorio: diz-se o caminho inteiro
    print("fotos marcadas: %d (%s)" % (len(fotos), os.path.relpath(fonte, C.REPO)
                                       if os.path.splitdrive(os.path.abspath(fonte))[0].lower()
                                       == os.path.splitdrive(C.REPO)[0].lower() else fonte))
    if not fotos:
        raise SystemExit("Nenhuma foto para a coluna dos creditos (%s)" % fonte)
    # com os nomes corridos os titulos dos grupos nao vao ao ecra, e nao se dizem (3 de outubro)
    corridos = textos["nomes_corridos"]
    # o titulo por cima dos nomes (4 de outubro) e um titulo como os dos grupos: se nao couber, encolhe e diz-se
    titulo_nomes = textos.get("titulo_nomes")
    for a in (titulos_que_encolhem(([(titulo_nomes, "", [])] if titulo_nomes else []) + ([] if corridos else blocos))
              + quem_que_encolhe(textos) + caracteres_que_faltam(textos, blocos)):
        print("  AVISO: %s" % a)
    nao_cabem = textos_que_nao_cabem(textos, blocos)
    for p in nao_cabem:
        print("  NAO CABE: %s" % p)
    if nao_cabem and "--so-dizer" not in sys.argv:
        raise SystemExit("%d textos dos creditos nao cabem no ecra; nada foi desenhado" % len(nao_cabem))
    rolo = rolo_de_nomes(blocos, corridos) if corridos else rolo_de_nomes(blocos)
    if titulo_nomes:
        # O TITULO POR CIMA DOS NOMES: o rolo comeca por ele, e os tempos contam com a altura que ele acrescenta
        sem_titulo = rolo.height
        rolo = rolo_de_nomes(blocos, corridos, titulo_nomes)
        print("titulo por cima dos nomes: \"%s\", no topo do rolo (mais %d px de rolo)"
              % (titulo_nomes, rolo.height - sem_titulo))
    coluna = coluna_de_fotos(fotos)
    T = tempos_dos_creditos(rolo.height, coluna.height, len(textos["cargos"]), textos["cargos_primeiro"],
                            textos["partes"], textos["velocidade"])
    t_rolo, vel_nomes, vel_fotos, dur = T["t_rolo"], T["vel_nomes"], T["vel_fotos"], T["dur"]
    t_cargo, t_cargos = T["t_cargo"], T["t_cargos"]
    print("rolo de nomes %d px a %.0f px/s; coluna de fotos %d px a %.0f px/s; rolo %.1f s; creditos %.1f s"
          % (rolo.height, vel_nomes, coluna.height, vel_fotos, t_rolo, dur))
    # AS PARTES, OS NOMES CORRIDOS E A VELOCIDADE (3 de outubro): diz-se o que nao e o de sempre
    if T["partes"] not in (PARTES_HOJE, PARTES_CARGOS_PRIMEIRO) or corridos:
        print("partes: %s%s; %s" % (" > ".join(T["partes"]), "" if "cargos" in T["partes"] else " (sem cargos)",
                                    ", ".join("%s de %.2f a %.2f s" % j for j in T["janelas"]) if T.get("janelas")
                                    else "a ordem de sempre"))
        if corridos:
            print("nomes corridos: sem titulos nem subtitulos de grupo, %d linhas de nomes" % len(linhas_dos_nomes(blocos)))
    for a in avisos_da_velocidade(T, alturas_na_coluna(fotos) if T.get("velocidade") else [],
                                  linhas_dos_nomes(blocos) if T.get("velocidade") else []):
        print("  AVISO: %s" % a)
    if T.get("parado"):
        print("velocidade: os %s acabam %.1f s antes e ficam parados no fim (fora do ecra) esse tempo"
              % (T["parado"][0], T["parado"][1]))
    # a ordem e as pessoas dizem-se quando nao sao as de sempre: os cargos primeiro, outro numero de cargos, ou
    # um cargo com mais de uma pessoa (corretor, 2 de outubro a noite: com tres cargos ficava calado das pessoas)
    if T["partes"] in (PARTES_HOJE, PARTES_CARGOS_PRIMEIRO) and (
            textos["cargos_primeiro"] or len(textos["cargos"]) != len(CARGOS)
            or any(len(pessoas_do_quem(q)) > 1 for _c, q in textos["cargos"])):
        print("ordem: %s; %d cargos (%s)" % (
            "os cargos primeiro, depois o rolo e o titulo" if textos["cargos_primeiro"]
            else "o rolo, depois os cargos e o titulo", len(textos["cargos"]),
            ", ".join("%d pessoa%s" % (len(pessoas_do_quem(q)), "" if len(pessoas_do_quem(q)) == 1 else "s")
                      for _c, q in textos["cargos"])))
    if "--so-dizer" in sys.argv:
        return
    creditos = desenho_dos_creditos(rolo, coluna, textos, estilo, T)

    if "--quadros" in sys.argv:
        # fotogramas soltos, para ver a composicao sem esperar pelo video
        # os cargos e o titulo no mesmo ponto de cada um de sempre (2 s depois de entrar, e 2,5 s o titulo),
        # agora contados de onde o rolo acaba (t_cargos); o rolo a 1, 12 e 40 s da entrada dele. Com os tres
        # cargos de sempre e o rolo primeiro sao os mesmos sete instantes de sempre.
        r0 = T["t_rolo_entra"]
        # sem cargos ou sem titulo nas partes (3 de outubro), so os que existem
        for t in ((r0 + 1.0, r0 + 12.0, r0 + 40.0)
                  + (tuple(t_cargos + k * t_cargo + 2.0 for k in range(len(textos["cargos"])))
                     if t_cargos is not None else ())
                  + ((T["t_titulo_entra"] + 2.5,) if T["t_titulo_entra"] is not None else ())):
            creditos(t).save(os.path.join(pasta, "_quadro_%05.1f.jpg" % t), quality=88)
        print("quadros em", pasta)
        return

    # o fim do filme: os ultimos 5 s do render de ensaio antes do fade, e a musica a continuar
    renders = sorted(glob.glob(r"C:\casamento-video-media\saida\v3_*[0-9].mp4"), key=os.path.getmtime)
    # um filme sem legendas (o do DaVinci) nunca e o filme da sala, nem com um _2 no fim do nome
    renders = [r for r in renders if "_sem_legendas" not in os.path.basename(r)]
    # --filme <caminho> escolhe o render; sem ele, o mais recente com nome de filme inteiro. Um render
    # a meia resolucao (--escala) chama-se ..._parcial.mp4 e so entra pelo --filme.
    final = sys.argv[sys.argv.index("--filme") + 1] if "--filme" in sys.argv else renders[-1]
    print("filme: %s" % final)
    pasta_master = None
    if "--master" in sys.argv:
        # o que pode falhar no master diz-se ja, antes dos cinco minutos do exemplo
        pasta_master = sys.argv[sys.argv.index("--master-em") + 1] if "--master-em" in sys.argv else PASTA_MASTER
        if not os.path.isdir(pasta_master):
            raise SystemExit("A pasta do master nao existe: %s" % pasta_master)
        w, h, fps = medir_video(final)
        if (w, h) != (L, A) or abs(fps - FPS) > 0.01:
            raise SystemExit("O --master pede um render inteiro de %dx%d a %d fps, e este e %dx%d a %.2f: %s"
                             % (L, A, FPS, w, h, fps, final))
    fim_filme = C.duracao(final) - render.FADE_FIM_IMAGEM
    antes = 5.0
    # os fotogramas do fim do filme leem-se um a um por um tubo: 5 s em memoria eram 780 MB
    leitor = subprocess.Popen([C.FF, "-v", "error", "-ss", "%.3f" % (fim_filme - antes), "-t", "%.3f" % antes,
                               "-i", final, "-an", "-vf", "fps=%d,scale=%d:%d" % (FPS, L, A),   # um render --escala tambem serve
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                              stdout=subprocess.PIPE)
    ultimo = None
    # a musica do fim continua de onde o filme a deixa, e acaba com os creditos. O relogio do som e o do
    # corpo, que comeca onde os videos de abertura acabam: o filme inteiro menos o corpo.
    est = C.carregar()
    ultima = C.leitos(C.entradas_de_som(est))[-1]
    abertura = C.duracao(final) - est["fim"]
    pos = ultima["in_s"] + (fim_filme - antes - abertura) - ultima["quando"]
    total = antes + dur
    # A MUSICA QUE ELE ESCOLHEU NA MESA, ou a de sempre (som_dos_creditos)
    avisos_som = []
    faixas, info = som_dos_creditos(ultima, pos, antes, dur, escolha_da_musica(leitura[0]), avisos_som)
    for a in avisos_som:
        print("  AVISO: %s" % a)
    # AS CONTAS DIZEM-SE PELO FIM AUDIVEL, e nao pela duracao do ficheiro (corretor, 2 de outubro): os
    # Queen tem 245,55 s e calam-se aos 239,34, e a conta pela duracao dizia 6 s de musica a mais.
    if info is None:
        import musica_creditos as mc
        cala = mc.fim_audivel(ultima["caminho"])
        toca, falta = max(0.0, min(total, cala - pos)), max(0.0, total - max(0.0, cala - pos))
        print("musica do fim (como esta): %s, dos %.1f s do ficheiro, que se cala aos %.1f s; toca %.1f dos %.1f s "
              "de exemplo%s" % (C.nome_da_musica(ultima["ficheiro"]), pos, cala, toca, total,
                                ("; OS ULTIMOS %.1f s FICAM EM SILENCIO" % falta) if falta > 0.5 else ""))
    else:
        print("musica dos creditos (a da Mesa): %s, entra aos %.2f s do ficheiro, que se cala aos %.1f s; toca %.1f "
              "dos %.1f s dos creditos%s" % (C.nome_da_musica(info["ficheiro"]), info["in_s"], info["fim"], info["toca"],
                                             dur, ("; OS ULTIMOS %.1f s FICAM EM SILENCIO" % info["falta"])
                                             if info["falta"] > 0.5 else ""))
        if info.get("passagem") == "frase":
            print("  passagem no fim da frase: %s acaba a frase e a dos creditos entra %.2f s depois do inicio deles "
                  "(aos %.2f s do ficheiro da que sai, em vez de %.2f)" % (C.nome_da_musica(ultima["ficheiro"]),
                                                                       info["espera"], info["no_corte"],
                                                                       info["corte_da_imagem"]))
    som_saida = os.path.join(pasta, "_som.m4a")
    render.construir_som(render.ffmpeg(), faixas, total, som_saida, render.FADE_FIM_SOM)
    # A MUSICA PODE ACABAR ANTES DOS CREDITOS (1 de outubro: os Queen acabam 2 s antes de o titulo se
    # apagar). O encoder corta a imagem pelo som (-shortest), e perdia-se o fim a desvanecer para o
    # preto, que e o que diz a sala que acabou: o som completa-se com silencio ate ao ultimo fotograma.
    if C.duracao(som_saida) < total - 0.05:
        cheio = os.path.join(pasta, "_som_cheio.m4a")
        subprocess.run([C.FF, "-v", "error", "-y", "-i", som_saida, "-af", "apad=whole_dur=%.3f" % total,
                        "-c:a", "aac", "-b:a", "192k", cheio], check=True)
        apagar(som_saida)
        som_saida = cheio

    saida = os.path.join(pasta, "exemplo_creditos.mp4")
    enc = C.encoder(saida, total, som_saida)
    for k in range(int(round(total * FPS))):
        t = k / FPS
        if t < antes:
            dados = leitor.stdout.read(L * A * 3)
            if len(dados) == L * A * 3:
                ultimo = Image.frombytes("RGB", (L, A), dados)
            im = ultimo
        else:
            tt = t - antes
            # a ultima imagem do filme desfaz-se na primeira parte; com o titulo primeiro, apaga-se antes dele
            im = com_o_fim_do_filme(ultimo, creditos(tt), tt, T)
        enc.stdin.write(im.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    leitor.stdout.close()
    leitor.wait()
    apagar(som_saida)
    if "--sem-telemovel" in sys.argv:
        # nenhuma copia do telemovel, nem a do exemplo: sao 2 minutos que o pacote do DaVinci nao usa
        print("escrito", saida)
    else:
        leve = os.path.join(pasta, "exemplo_creditos_telemovel.mp4")
        subprocess.run([C.FF, "-v", "error", "-y", "-i", saida, "-vf", "scale=1280:720", "-c:v", "libx264", "-crf", "24",
                        "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", leve], check=True)
        print("escrito", saida, "e", leve)
    print("  o exemplo dos creditos levou %.0f s" % (time.time() - t_inicio))
    # O --sem-telemovel salta a copia do telemovel do filme com os creditos (2 de outubro): o pacote do
    # DaVinci so precisa do master, e a copia de duas passagens eram mais uns minutos por cima do render.
    if ("--colar" in sys.argv or "--master" in sys.argv) and "--sem-telemovel" not in sys.argv:
        t0 = time.time()
        colar_no_filme(final, fim_filme - antes, saida, pasta)
        print("  a copia do telemovel levou %.0f s" % (time.time() - t0))
    if "--master" in sys.argv:
        master_com_creditos(final, fim_filme - antes, saida, pasta_master)
    if fora:
        print("sem grupo de creditos (ficam de fora): %d pessoas, com as etiquetas %s"
              % (len(fora), sorted({x for c in fora for x in c["etiquetas"] if not x.startswith(("Convite", "01."))})))


def colar_no_filme(final, corte, creditos, pasta):
    """O filme ate ao corte (5 s antes do fade, onde o exemplo comeca) e os creditos a seguir, numa so
    copia do telemovel. O exemplo comeca com esses 5 s do filme e a mesma musica no mesmo sitio, por
    isso a juncao nao se ve; o som dos dois lados passa pelo loudnorm e pode diferir um dB. Duas
    passagens por tamanho alvo, como o render.py faz a _telemovel: cabe sempre nos 30 MB do envio."""
    movel = os.path.join(pasta, os.path.basename(final)[:-4] + "_com_creditos_telemovel.mp4")
    total = corte + C.duracao(creditos)
    alvo, som_kbps = 28 * 1048576, 96
    video_kbps = max(80, int(alvo * 8 / total / 1000.0) - som_kbps)
    # as duas partes passam a 960x540 antes de se juntarem: o filme pode vir de um render --escala
    filtro = ("[0:v]trim=0:%.3f,setpts=PTS-STARTPTS,scale=960:540:flags=lanczos,setsar=1[v0];"
              "[0:a]atrim=0:%.3f,asetpts=PTS-STARTPTS[a0];"
              "[1:v]setpts=PTS-STARTPTS,scale=960:540:flags=lanczos,setsar=1[v1];[1:a]asetpts=PTS-STARTPTS[a1];"
              "[v0][a0][v1][a1]concat=n=2:v=1:a=1[vs][a]" % (corte, corte))
    passlog = os.path.join(pasta, "_passlog_colar")
    comum = [C.FF, "-hide_banner", "-loglevel", "error", "-y", "-i", final, "-i", creditos,
             "-filter_complex", filtro, "-map", "[vs]", "-c:v", "libx264", "-preset", "medium",
             "-b:v", "%dk" % video_kbps, "-pix_fmt", "yuv420p", "-passlogfile", passlog]
    # Na primeira passagem o som tambem sai: com o -an a saida [a] do concat ficava sem destino e o
    # ffmpeg recusava o filtro inteiro (1 de outubro).
    subprocess.run(comum + ["-map", "[a]", "-c:a", "aac", "-pass", "1", "-f", "mp4", os.devnull], check=True)
    subprocess.run(comum + ["-map", "[a]", "-pass", "2", "-c:a", "aac", "-b:a", "%dk" % som_kbps,
                            "-movflags", "+faststart", movel], check=True)
    for sobra in (passlog + "-0.log", passlog + "-0.log.mbtree"):
        if os.path.exists(sobra):
            os.remove(sobra)
    print("filme com creditos: %s (%.0f s, %.1f MB)" % (movel, total, os.path.getsize(movel) / 1048576.0))


def medir_video(caminho):
    """(largura, altura, fotogramas por segundo) do primeiro video do ficheiro, pelo ffprobe."""
    r = subprocess.run([C.FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate", "-of", "csv=p=0", caminho],
                       capture_output=True, text=True)
    try:
        w, h, taxa = r.stdout.strip().splitlines()[0].split(",")[:3]
        n, d = taxa.split("/")
        return int(w), int(h), float(n) / float(d)
    except (ValueError, IndexError, ZeroDivisionError):
        raise SystemExit("Nao consegui medir o video %s (%s)" % (caminho, (r.stderr or "").strip()[-200:]))


def nome_livre(base, extensao=".mp4"):
    """base + extensao, ou base_2, base_3... se ja existir: nenhum ficheiro de entrega e escrito por cima."""
    caminho, k = base + extensao, 2
    while os.path.exists(caminho):
        caminho = "%s_%d%s" % (base, k, extensao)
        k += 1
    return caminho


def master_com_creditos(final, corte, creditos, pasta_destino):
    """O FICHEIRO DE ENTREGA, 2 de outubro: o filme inteiro com os creditos, em 1080p, para a sala.

    O Tiago, a 2 de outubro, para o dia com a Clara: ajustar tudo na Mesa "e depois darmos so ordem
    para fazer render, que e a parte que demora mais tempo". O render da o filme sem creditos e o
    --colar so dava a copia do telemovel; faltava o ficheiro que vai ao projetor.

    A JUNCAO E A DO --colar (colar_no_filme): o filme ate 5 s antes do fade, e o exemplo a seguir,
    que comeca com esses mesmos 5 s e a mesma musica no mesmo sitio. Muda so o resto: as duas partes
    ficam em 1920x1080, a imagem sai a CRF 18 (o render e CRF 20, por isso esta segunda passagem quase
    nao se ve) e o som em AAC a 192k, como o do render. O som das duas partes passa por um aformat a
    48 kHz estereo, que e o que ja sao: so garante que o concat as aceita.

    NUNCA ESCREVE POR CIMA. O nome e o do render com _com_creditos, e _2, _3... se ja existir. O
    ffmpeg escreve primeiro um ..._a_fazer.mp4 e so no fim se muda o nome: um master que pare a meio
    nunca fica com o nome de um master pronto.
    """
    for caminho in (final, creditos):
        w, h, fps = medir_video(caminho)
        if (w, h) != (L, A) or abs(fps - FPS) > 0.01:
            raise SystemExit("O master pede %dx%d a %d fps, e %s e %dx%d a %.2f"
                             % (L, A, FPS, os.path.basename(caminho), w, h, fps))
    destino = nome_livre(os.path.join(pasta_destino, os.path.basename(final)[:-4] + "_com_creditos"))
    a_fazer = nome_livre(destino[:-4] + "_a_fazer")
    filtro = ("[0:v]trim=0:%.3f,setpts=PTS-STARTPTS,setsar=1[v0];"
              "[0:a]atrim=0:%.3f,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a0];"
              "[1:v]setpts=PTS-STARTPTS,setsar=1[v1];"
              "[1:a]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a1];"
              "[v0][a0][v1][a1]concat=n=2:v=1:a=1[vs][a]" % (corte, corte))
    print("master: a juntar o filme ate %.2f s e os creditos, CRF %d, som AAC %s" % (corte, MASTER_CRF, MASTER_SOM))
    t0 = time.time()
    r = subprocess.run([C.FF, "-hide_banner", "-loglevel", "error", "-n", "-i", final, "-i", creditos,
                        "-filter_complex", filtro, "-map", "[vs]", "-map", "[a]",
                        "-c:v", "libx264", "-crf", str(MASTER_CRF), "-preset", MASTER_PRESET, "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", MASTER_SOM, "-ar", "48000", "-ac", "2",
                        "-movflags", "+faststart", a_fazer])
    if r.returncode != 0 or not os.path.exists(a_fazer):
        raise SystemExit("O master nao saiu (ffmpeg %d); o que ficou a meio esta em %s" % (r.returncode, a_fazer))
    os.rename(a_fazer, destino)          # no Windows o rename recusa um destino que ja exista
    esperado = corte + C.duracao(creditos)
    dur = C.duracao(destino)
    print("MASTER: %s (%.1f s, %.0f MB, em %.0f s)" % (destino, dur, os.path.getsize(destino) / 1048576.0,
                                                       time.time() - t0))
    if abs(dur - esperado) > 0.2:
        print("  ATENCAO: o master tem %.2f s e devia ter %.2f; ve-o antes de o levar" % (dur, esperado))
    return destino


if __name__ == "__main__":
    main()
