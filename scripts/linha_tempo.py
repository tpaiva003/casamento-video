# -*- coding: utf-8 -*-
"""A linha do tempo horizontal: anos e marcos a fugir para a esquerda.

O Tiago foi explicito nas duas correcoes que deram origem a este ficheiro:

  "o facto de hoje 4 de outubro tem de ficar mais dentro do timeline animation
   e nao como uma especie de legenda a parte"

  "Quero que o scrolling de timeline animation funcione na orizontal e nao na
   vertical e que como estamos a ir para tras se movimente para a esquerda ate
   chegar a 1995"

COMO ESTA FEITA, e porque assim:

A fita esta desenhada da esquerda para a direita por ordem de RECUO: 2026 a
esquerda, 1995 a direita. A fita desloca-se para a ESQUERDA, portanto os anos
passam da direita para a esquerda e o que chega ao centro e cada vez mais
antigo. E isso que da a sensacao de fugir para tras, e e literalmente o que ele
pediu.

A DATA DO CASAMENTO NAO E UMA LEGENDA POR BAIXO. E um marco DA PROPRIA FITA,
posto por cima do ano de onde parte, com o seu risco a tocar na linha. Era essa
a queixa: a data andava a flutuar ao fundo do ecra, sem pertencer a nada.

ANDAMENTO. A cabeca de leitura fica parada nos marcos e corre depressa entre
eles. Sem isso ou tudo passa depressa de mais para se ler, ou tudo passa devagar
de mais e a fuga deixa de se sentir. Quem manda no tempo sao os marcos, nao os
anos vazios.

A SALA MANDA. Bloco de 15 minutos ao jantar, metade das pessoas de costas, 15
metros ate ao ecra. Daqui vem o tamanho dos numeros, o contraste e o facto de
nenhum marco levar mais do que uma linha curta de texto.
"""
import datetime
import math

from PIL import Image, ImageDraw, ImageFont

FONTE = r"C:\Windows\Fonts\arialbd.ttf"
# A LETRA FINA JA NAO DESENHA NADA NO FILME, desde a decisao 084: era a dos meses da fita de
# 1995 e passou a negrito, como a regua do contador. Fica porque o teste dos meses da regua a
# usa para provar que a letra fina nao se leria (testes.py, teste_meses_da_regua_leem_se).
FONTE_FINA = r"C:\Windows\Fonts\arial.ttf"

FUNDO = (10, 8, 12)
LINHA = (92, 78, 88)
ANO_LONGE = (108, 96, 104)
ANO_PERTO = (246, 240, 244)
MARCO = (200, 62, 86)
MARCO_TEXTO = (255, 226, 232)

# ------------------------------------------------- os dois contadores sao a MESMA fita
# Ate 18 de setembro nao eram, e media-se: o algarismo grande tinha 131 px no contador de
# anos e 101 px no de datas, a legenda de um marco estava a duas alturas diferentes, o de
# anos nao tinha regua nenhuma e o ponteiro do centro era desenhado a (38,30,36) sobre o
# fundo (10,8,12), 1,27 para 1 de contraste. A 15 metros, com metade da sala de costas,
# isso e um ponteiro que nao existe e duas fitas que parecem duas pecas de filmes
# diferentes. Estes numeros sao de agora em diante os DOS DOIS, e o
# teste_contadores_sao_a_mesma_fita falha se um deles mudar sozinho.
CORPO_NUMERO = 0.17       # o algarismo grande, fracao de A: "2026" e "4 OUT 2026" a mesma altura
CORPO_ROTULO = 46         # a legenda de um marco
Y_ROTULO = 0.16           # ... e onde ela fica, fracao de A abaixo da linha
Y_REGUA_TEXTO = 58        # os nomes da regua, pixeis abaixo da linha
REGUA_MAIOR_ALTO = 22     # traco de ano (anos) ou de mes (datas)
REGUA_MENOR_ALTO = 10     # traco de mes (anos) ou de dia (datas)

# O PONTEIRO DO CENTRO, o unico ponto fixo do ecra. (38,30,36) dava 1,27 para 1 e durante
# a viagem nao se via: os numeros passavam por um sitio que ninguem distinguia do fundo.
# Este da 6,0 para 1, acima dos 4,5 que a regra do texto pede, e fica na mesma mais
# apagado do que o algarismo aceso (246,240,244), que continua a ser o que se le primeiro.
# As duas pontas levam um bico virado para dentro: e o que o faz ler como cabeca de
# leitura e nao como um risco a dividir o ecra ao meio.
#
# ONDE ELE COMECA E ACABA nao e simetrico, e a razao e o que ha por baixo da linha. O
# ecra esta repartido assim: o algarismo grande acaba aos 0,52 de A, a regua e os nomes
# dos meses ocupam a faixa logo abaixo da linha e a legenda do marco esta em Y_ROTULO. O
# ponteiro vai de um vao ao outro, e por isso nao atravessa nem o numero nem a legenda; o
# resto do desenho e feito por cima dele, que e como uma cabeca de leitura se ve.
PONTEIRO = (150, 138, 146)
PONTEIRO_LARGURA = 5
PONTEIRO_CIMA = 0.072         # acima da linha, fracao de A
PONTEIRO_BAIXO = 0.132        # abaixo da linha, fracao de A
PONTEIRO_BICO = (0.010, 0.024)    # meia base e altura do bico, fracao de A

# A REGUA. Os tracos de dentro da viagem sao mais claros do que a linha; os de fora ficam
# na cor da linha, porque a fita continua mas ali nao ha nada para contar. Os nomes a
# 8,3 para 1, no corpo da legenda: eram 32 px em letra fina a (128,114,122), 4,4 para 1,
# texto que so se le de perto.
REGUA_MAIOR = (150, 132, 144)
REGUA_FORA = LINHA
REGUA_MENOR = (92, 78, 88)
REGUA_TEXTO = (176, 164, 172)

# O NOME DE UM MES NAO ENCOSTA AO PONTEIRO. Com os nomes a 46 px, o "OUT" do dia 1 fica a
# 57 px do ponteiro quando a fita esta parada a 4 de outubro, e com cerca de 94 px de largura
# a tinta dele acaba a 7 px da linha do ponteiro: a 15 metros le-se "OUT|". Um nome que
# chegue a menos de NOME_LONGE px da linha do ponteiro desvanece, e a NOME_PERTO ja nao se
# desenha; o traco do mes fica. Em andamento, cada nome apaga-se ao passar pela cabeca de
# leitura e volta do outro lado, que e o que se ve numa regua de verdade atras de um cursor.
NOME_PERTO = 12
NOME_LONGE = 48


def contraste(a, b):
    """O contraste entre duas cores pela regra do texto (WCAG): de 1 para 1 a 21 para 1.

    Esta aqui, e nao no teste, porque os numeros das cores de cima foram escolhidos com
    ela: quem mexer numa cor tem de poder voltar a fazer a conta no mesmo sitio.
    """
    def luz(cor):
        canais = []
        for v in cor[:3]:
            v /= 255.0
            canais.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]
    x, y = luz(a), luz(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


# Os meses, em maiusculas, na data grande do meio e na regua de baixo. Ate 18 de setembro
# a regua tinha a sua lista em minusculas, "uma leitura de perto"; so que na sala nao ha
# leitura de perto, e em maiusculas as tres letras leem-se melhor a 15 metros.
MESES_CURTOS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

# ATE ONDE UM CONTADOR POR DATAS DIZ ALGUMA COISA. Acima de tres anos a regua de meses
# passa depressa de mais para os nomes se lerem e cada fotograma salta semanas: ai o
# contador de anos conta a mesma historia melhor, e o preparar() do render troca e avisa.
DIAS_MAXIMOS_DATAS = 3 * 366


def suave(x):
    """Aceleracao e travagem, para nada comecar nem acabar aos solavancos."""
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def sem_repetidas(vals, tolerancia=1e-6):
    """Tira paragens coladas umas as outras.

    Interessa porque o fim de um troco costuma coincidir com a ultima marca:
    "vai ate ao nascimento do Tiago" da a mesma posicao duas vezes, e a fita
    ficava parada la o dobro do tempo com a palavra apagada na segunda metade.
    """
    fora = []
    for v in vals:
        if not fora or abs(v - fora[-1]) > tolerancia:
            fora.append(v)
    return fora


def inicio_da_paragem(k, n, fracao_parada=0.62, parar_no_primeiro=True):
    """Em que fracao do clip comeca a paragem k, de n. Ver posicao_com_paragens.

    Serve para o som: os foguetes tem de rebentar quando a palavra "Nasce o
    Tiago" acende, nao um segundo antes nem tres depois.

    TEM DE SABER DO `parar_no_primeiro`. Quando se tirou a espera inicial dos
    clips que continuam a fita, a agenda mudou e esta conta ficou a responder
    pela agenda velha: dava 7,15 s quando o certo eram 3,3 s. Um erro de quase
    quatro segundos entre o anuncio e os foguetes.
    """
    if n <= 0:
        return 0.0
    quantas_param = n if parar_no_primeiro else max(1, n - 1)
    t_parado = fracao_parada / quantas_param
    t_viagem = (1.0 - fracao_parada) / max(1, n - 1) if n > 1 else 0.0
    if parar_no_primeiro:
        return k * (t_parado + t_viagem)
    return k * t_viagem + max(0, k - 1) * t_parado + (t_parado if k > 0 else 0.0) * 0


def posicao_com_paragens(p, paragens, fracao_parada=0.62, parar_no_primeiro=True):
    """Onde esta a cabeca de leitura, em unidades da fita, no instante p.

    `paragens` sao as posicoes (em unidades da fita) onde se quer parar. O tempo
    reparte-se entre viajar e ficar parado: `fracao_parada` diz quanto do tempo
    total e gasto parado nos marcos. Devolve tambem quanto vale a paragem atual,
    de 0 a 1, para quem desenha poder acender o marco enquanto ele esta a ser
    lido.
    """
    if not paragens:
        return p, None, 0.0
    n = len(paragens)

    # SEM ESPERA NO PRIMEIRO, quando este clip continua a fita do anterior.
    #
    # O Tiago viu: "ha um gap no movimento na timeline no sapo para o tiago".
    # A causa eram DUAS PARAGENS SEGUIDAS no mesmo sitio: o clip anterior ficava
    # parado no SAPO ate acabar, e o seguinte voltava a ficar parado no mesmo
    # ponto antes de arrancar. Somadas, davam varios segundos de fita quieta a
    # meio de uma sequencia que devia estar a andar.
    #
    # Num clip que continua, a primeira paragem ja foi cumprida pelo anterior.
    # Arranca logo a andar, e o tempo dela vai para as outras.
    quantas_param = n if parar_no_primeiro else max(1, n - 1)
    t_parado = fracao_parada / quantas_param
    t_viagem = (1.0 - fracao_parada) / max(1, n - 1) if n > 1 else 0.0

    agenda = []
    t = 0.0
    for i in range(n):
        if i > 0 or parar_no_primeiro:
            agenda.append(("parar", i, t, t + t_parado))
            t += t_parado
        if i < n - 1:
            agenda.append(("viajar", i, t, t + t_viagem))
            t += t_viagem
    for tipo, i, a, b in agenda:
        if p <= b or (tipo, i) == agenda[-1][:2]:
            dentro = 0.0 if b <= a else (p - a) / (b - a)
            if tipo == "parar":
                return paragens[i], i, min(1.0, max(0.0, dentro))
            j = min(n - 1, i + 1)
            return (paragens[i] + (paragens[j] - paragens[i]) * suave(dentro)), None, 0.0
    return paragens[-1], n - 1, 1.0


_CACHE_IMG = {}


def imagem_da_marca(nome, alt_alvo):
    """Carrega e guarda a imagem de uma marca, ja com a altura que vai ter.

    Procura em FINAIS primeiro, que e a melhor versao de cada foto, e so depois
    na pasta de trabalho. Se nao existir, a marca fica so com palavras: uma
    imagem em falta nao pode parar um render.
    """
    import os
    from PIL import ImageOps
    chave = (nome, alt_alvo)
    if chave in _CACHE_IMG:
        return _CACHE_IMG[chave]
    achado = None
    for raiz in (r"C:\casamento-video-media\FINAIS",
                 r"C:\casamento-video-media\trabalho"):
        if not os.path.isdir(raiz):
            continue
        for base, _, fs in os.walk(raiz):
            if "00-Backup" in base:
                continue
            for f in fs:
                if f.lower() == nome.lower() or f.lower().endswith("__" + nome.lower()):
                    achado = os.path.join(base, f)
                    break
            if achado:
                break
        if achado:
            break
    im = None
    if achado:
        try:
            im = ImageOps.exif_transpose(Image.open(achado)).convert("RGB")
            f = alt_alvo / float(im.height)
            im = im.resize((max(1, int(im.width * f)), alt_alvo), Image.LANCZOS)
        except Exception:
            im = None
    _CACHE_IMG[chave] = im
    return im


def _texto(d, txt, fonte, x, y, cor, centro=True):
    caixa = d.textbbox((0, 0), txt, font=fonte)
    w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
    px = x - w / 2.0 if centro else x
    d.text((px - caixa[0], y - h / 2.0 - caixa[1]), txt, font=fonte, fill=cor)
    return w


def _ponteiro(d, L, A, y_linha):
    """A cabeca de leitura, parada ao centro. Igual nos dois contadores.

    DESENHA-SE ANTES DE TUDO O RESTO, de proposito: o algarismo grande, a regua e a
    legenda passam-lhe por cima, que e o que se ve numa cabeca de leitura verdadeira.
    """
    x = L // 2
    cima, baixo = y_linha - int(A * PONTEIRO_CIMA), y_linha + int(A * PONTEIRO_BAIXO)
    d.line([(x, cima), (x, baixo)], fill=PONTEIRO, width=PONTEIRO_LARGURA)
    meia, alto = int(A * PONTEIRO_BICO[0]), int(A * PONTEIRO_BICO[1])
    d.polygon([(x - meia, cima), (x + meia, cima), (x, cima + alto)], fill=PONTEIRO)
    d.polygon([(x - meia, baixo), (x + meia, baixo), (x, baixo - alto)], fill=PONTEIRO)


def _rasto(px_s, unidade):
    """Quantas copias esbatidas atras de cada numero, e quanto ocupam ao todo.

    A conta ja era a mesma nos dois contadores, escrita duas vezes: em anos por segundo
    la, em pixeis por segundo aqui. Passa a estar escrita uma vez, para "o mesmo rasto"
    deixar de depender de ninguem se lembrar de mexer nas duas.

    `unidade` e o passo de um ano, que e a distancia a que um numero se le como outro: e
    por isso que o rasto nunca passa 42 por cento dela, senao lia-se "2011 1111".
    """
    return min(4, int(px_s / unidade)), min(unidade * 0.42, px_s * 0.035)


def _tapado_pelo_ponteiro(x, L, nitidez):
    """Se o traco pequeno em x fica escondido pela cabeca de leitura: so com a fita PARADA.

    Parado num dia inteiro, o traco do dia cai exatamente na coluna do ponteiro e era
    pintado por cima dele, na cor da regua: um entalhe escuro de 2 x 10 px logo abaixo da
    linha, a 2,5 para 1, no unico ponto fixo do ecra, durante as duas paragens do contador
    por datas (verificador, 18 de setembro). No de anos nao se via porque o traco do ano,
    claro, cai no mesmo sitio e tapa o do mes, e por isso ai nada muda.

    A andar, os tracos continuam a passar-lhe por cima, que e o que o _ponteiro() quer: a
    regua a correr por cima de uma cabeca de leitura parada.
    """
    return nitidez >= 1.0 and abs(x - L / 2.0) < PONTEIRO_LARGURA / 2.0 + 1.0


def _regua(d, L, A, y_linha, ancora, menor_px, maiores, nitidez, fonte=None):
    """A regua por baixo da linha. A MESMA nos dois contadores, por construcao.

    `ancora` e o x de uma posicao inteira da fita e `menor_px` o passo dos tracos
    pequenos: meses no contador de anos, dias no de datas. `maiores` sao (x, dentro da
    viagem, nome ou None).

    OS TRACOS VAO DE BORDA A BORDA, SEMPRE. Antes so existiam dentro da viagem, e nos dois
    extremos metade da regua ficava vazia: a fita parecia acabar a meio do ecra, que e
    precisamente o contrario do que uma fita a correr deve parecer. Fora da viagem ficam
    na cor da linha, porque ali nao ha nada para contar.

    OS TRACOS PEQUENOS DESVANECEM COM A VELOCIDADE. Em movimento sao uma grade a bater
    contra a grelha de pixeis, e o que se ve nisso e tremor, nao velocidade. Quem fica a
    contar a corrida sao os maiores e o rasto.
    """
    if nitidez > 0.02 and menor_px >= 9.0:
        cor = tuple(int(FUNDO[i] + (REGUA_MENOR[i] - FUNDO[i]) * nitidez) for i in range(3))
        k = math.floor((-menor_px - ancora) / menor_px)
        while True:
            x = ancora + k * menor_px
            k += 1
            if x > L + menor_px:
                break
            if _tapado_pelo_ponteiro(x, L, nitidez):
                continue
            d.line([(x, y_linha + 1), (x, y_linha + REGUA_MENOR_ALTO)], fill=cor, width=2)
    for x, dentro, nome in maiores:
        if x < -menor_px or x > L + menor_px:
            continue
        d.line([(x, y_linha + 1), (x, y_linha + REGUA_MAIOR_ALTO)],
               fill=REGUA_MAIOR if dentro else REGUA_FORA, width=3)
        if nome and fonte is not None:
            caixa = d.textbbox((0, 0), nome, font=fonte)
            vao = abs(x - L / 2.0) - (caixa[2] - caixa[0]) / 2.0 - PONTEIRO_LARGURA / 2.0
            aceso = min(1.0, max(0.0, (vao - NOME_PERTO) / float(NOME_LONGE - NOME_PERTO)))
            if aceso <= 0.0:
                continue
            cor = REGUA_TEXTO if aceso >= 1.0 else tuple(
                int(FUNDO[i] + (REGUA_TEXTO[i] - FUNDO[i]) * aceso) for i in range(3))
            _texto(d, nome, fonte, x, y_linha + Y_REGUA_TEXTO, cor)


def _risco_do_marco(tela, d, x0, y_linha, alfa):
    """O risco vermelho de um marco, a acender por cima do que la esta. Igual nos dois contadores.

    ERA PINTADO A SUBIR DO PRETO, MARCO . alfa, e isso so nao se via enquanto o ponteiro era
    invisivel. Com o ponteiro claro, o risco fica mesmo em cima dele quando a fita para num
    marco, e durante o meio segundo em que a legenda acende e apaga abria-se um buraco escuro
    de 52 px no meio do unico ponto fixo do ecra: (15,4,6) aos 0,04 s, 1,05 para 1 contra o
    fundo (verificador, 18 de setembro; 14 fotogramas no contador de anos da v3 e 28 no de
    datas). Agora mistura-se o vermelho com o que esta por baixo, ponteiro, regua ou fundo.

    Aceso por inteiro e o risco de sempre, desenhado da mesma maneira.
    """
    if alfa >= 1.0:
        d.line([(x0, y_linha - 26), (x0, y_linha + 26)], fill=MARCO, width=6)
        return
    x_esq, y_cima = int(math.floor(x0)) - 5, y_linha - 30
    mascara = Image.new("L", (11, 61), 0)
    ImageDraw.Draw(mascara).line([(x0 - x_esq, y_linha - 26 - y_cima),
                                  (x0 - x_esq, y_linha + 26 - y_cima)],
                                 fill=int(round(255 * alfa)), width=6)
    tela.paste(MARCO, (x_esq, y_cima, x_esq + 11, y_cima + 61), mascara)


def janela_de_movimento(ano_de, ano_para, marcos, duracao, fracao_parada=0.62):
    """De quando a quando e que a fita dos anos esta MESMO a andar.

    O Tiago ouviu: "o som da timeline esta a comecar antes da timeline comecar
    a mexer". Tinha razao e a conta mostra porque: com duas paragens, a fita
    fica parada os primeiros 31 por cento do clip, o que num clip de 13
    segundos sao quatro segundos de som de rebobinar com a fita quieta.
    """
    paragens = {ano_de, ano_para}
    for ano, _ in (marcos or []):
        if min(ano_de, ano_para) <= ano <= max(ano_de, ano_para):
            paragens.add(ano)
    n = len(sem_repetidas(sorted(paragens, reverse=ano_para < ano_de)))
    t_parado = (fracao_parada / n) * duracao
    inicio = t_parado
    fim = inicio_da_paragem(n - 1, n, fracao_parada) * duracao
    return inicio, max(inicio + 0.5, fim)


def anos(L, A, ano_de, ano_para, marcos, t_rel, duracao):
    """A fita dos anos. A recuar no tempo, le-se como um REWIND.

    ISTO ESTAVA AO CONTRARIO e o Tiago apanhou: "Nota sobre a timeline. E ao
    contrario, quando estamos a andar para tras e como se fizessemos um rewind".

    A primeira versao desenhava 2026 a esquerda e 1995 a direita, e fazia a fita
    andar para a esquerda. Isso e uma fita desenhada ao contrario do tempo, e o
    movimento le-se como avanco, nao como recuo.

    Agora a fita esta pela ordem do tempo, o ano mais antigo a ESQUERDA e o mais
    recente a DIREITA, como qualquer linha do tempo desenhada em papel. Parte-se
    da ponta direita, 2026, e caminha-se para a esquerda ao longo da fita. Visto
    do ecra, os numeros deslizam para a DIREITA, que e exatamente o que se ve
    quando se rebobina uma cassete.

    O borrao de movimento existe pela mesma razao: quando a fita corre depressa
    entre marcos, cada ano deixa rasto atras de si. Parado nos marcos, o rasto
    desaparece e le-se o ano.
    """
    p = max(0.0, min(1.0, t_rel / duracao if duracao else 0.0))
    total = abs(ano_de - ano_para)
    passo = int(L * 0.30)
    recuo = ano_para < ano_de
    novo_ano = max(ano_de, ano_para)

    def posicao(ano):
        """Onde esta o ano na fita, em unidades de passo. Cresce com o tempo."""
        return ano - min(ano_de, ano_para)

    # Paragens: o ponto de partida, cada ano com marco, e o de chegada.
    paragens_anos = {ano_de, ano_para}
    por_ano = {}
    for ano, txt in (marcos or []):
        if min(ano_de, ano_para) <= ano <= max(ano_de, ano_para):
            paragens_anos.add(ano)
            por_ano[ano] = txt
    ordenados = sorted(paragens_anos, reverse=recuo)
    paragens = [posicao(x) for x in ordenados]
    pos, qual, dentro = posicao_com_paragens(p, paragens)

    # Velocidade, para o rasto. Mede-se com uma amostra vizinha no tempo.
    dt = 1.0 / 25.0
    p2 = max(0.0, min(1.0, (t_rel + dt) / duracao if duracao else 0.0))
    pos2, _, _ = posicao_com_paragens(p2, paragens)
    velocidade = abs(pos2 - pos) / dt        # anos por segundo

    tela = Image.new("RGB", (L, A), FUNDO)
    d = ImageDraw.Draw(tela)
    y_linha = int(A * 0.60)
    d.line([(0, y_linha), (L, y_linha)], fill=LINHA, width=2)

    f_grande = ImageFont.truetype(FONTE, int(A * CORPO_NUMERO))
    f_medio = ImageFont.truetype(FONTE, int(A * 0.10))
    f_marco = ImageFont.truetype(FONTE, CORPO_ROTULO)

    # Rasto: copias esbatidas atras do sentido do movimento. A recuar, o
    # movimento aparente e para a direita, logo o rasto fica a direita.
    # O rasto tem de sugerir velocidade sem duplicar os algarismos. No primeiro
    # ensaio ficava tao largo que se lia "2011 1111": a largura total esta agora
    # limitada a meio passo e a opacidade a pouco mais de um quinto.
    px_s = velocidade * passo
    rastos, largura_rasto = _rasto(px_s, passo)
    sentido = 1 if recuo else -1

    baixo = min(ano_de, ano_para)
    cima = max(ano_de, ano_para)
    primeiro = int(math.floor(pos - L / (2.0 * passo) - 1))
    ultimo = int(math.ceil(pos + L / (2.0 * passo) + 1))

    # A REGUA E A DO CONTADOR POR DATAS, com os meses no lugar dos dias: um traco maior em
    # cada ano, tracos pequenos de mes a mes, e de borda a borda do ecra mesmo nos dois
    # extremos da viagem. E a mesma peca, desenhada pelo mesmo codigo, para as duas fitas
    # se lerem como uma so. A cabeca de leitura e desenhada primeiro, e a regua e os
    # numeros passam-lhe por cima.
    ancora = L / 2.0 - pos * passo
    _ponteiro(d, L, A, y_linha)
    _regua(d, L, A, y_linha, ancora, passo / 12.0,
           [(ancora + k * passo, baixo <= baixo + k <= cima, None)
            for k in range(primeiro, ultimo + 1)],
           max(0.0, 1.0 - px_s / 700.0))

    for k in range(primeiro, ultimo + 1):
        ano = baixo + k
        if not (baixo <= ano <= cima):
            continue
        x0 = L / 2.0 + (k - pos) * passo
        if x0 < -passo or x0 > L + passo:
            continue
        dist = min(1.0, abs(k - pos))
        perto = 1.0 - dist
        cor = tuple(int(ANO_LONGE[i] + (ANO_PERTO[i] - ANO_LONGE[i]) * (perto ** 1.6))
                    for i in range(3))
        fonte = f_grande if dist < 0.5 else f_medio
        for r in range(rastos, -1, -1):
            x = x0 + sentido * largura_rasto * (r / max(1.0, rastos))
            fade = 1.0 if r == 0 else 0.22 * (1.0 - r / (rastos + 1.0))
            c = tuple(int(FUNDO[i] + (cor[i] - FUNDO[i]) * fade) for i in range(3))
            _texto(d, str(ano), fonte, x, y_linha - int(A * 0.14), c)

        # O ROTULO ACENDE E APAGA DENTRO DA PARAGEM, como os marcos dos meses.
        # Antes era cortado quando a velocidade passava de 1,2: a fita arranca
        # suave, mas a velocidade passa esse valor em dois fotogramas, e a data
        # do casamento sumia de 97% para nada em 40 ms, com a fita ainda parada.
        txt = por_ano.get(ano)
        aceso = 0.0
        if txt and qual is not None and ordenados[qual] == ano:
            aceso = min(1.0, dentro / 0.18) * min(1.0, (1.0 - dentro) / 0.18)
        if txt and perto > 0.02 and aceso > 0.02:
            alfa = perto ** 1.2 * aceso
            _risco_do_marco(tela, d, x0, y_linha, alfa)
            _texto(d, txt, f_marco, x0, y_linha + int(A * Y_ROTULO),
                   tuple(int(MARCO_TEXTO[i] * alfa) for i in range(3)))
    return tela


def texto_da_data(data):
    """A data como se le no meio do contador: "4 OUT 2026".

    Dia, mes por extenso curto e ano. Nao "04/10/2026": a 15 metros um numero de dois
    algarismos entre barras le-se mal e confunde-se com a hora; o nome do mes nao.
    """
    return "%d %s %d" % (data.day, MESES_CURTOS[data.month - 1], data.year)


def paragens_das_datas(de, para, marcos):
    """As datas onde a fita para, pela ordem do percurso, e o rotulo de cada uma.

    Sao a de partida, a de chegada, e cada marco que caia entre as duas. E a mesma
    regra do contador de anos, e por isso um contador por datas anda e para como o
    de anos: quem manda no tempo sao as paragens, nao os dias vazios.
    """
    baixo, cima = min(de, para), max(de, para)
    datas_paragem = {de, para}
    por_data = {}
    for d, txt in (marcos or []):
        if baixo <= d <= cima:
            datas_paragem.add(d)
            por_data[d] = txt
    return sorted(datas_paragem, reverse=para < de), por_data


def data_do_instante(de, para, marcos, t_rel, duracao):
    """(data ao centro, paragem acesa ou None, quanto dela ja passou, posicao em dias).

    A DATA E SEMPRE UMA DO CALENDARIO, e e por isso que a conta e em DIAS INTEIROS:
    escolhe-se um numero de dias e soma-se a data mais antiga das duas. Somar dias a
    uma data nunca inventa um 31 de fevereiro nem um 29 de fevereiro fora dos
    bissextos, que era exatamente o risco de andar por meses ou por fracoes de ano.

    A posicao continua a ser devolvida em virgula porque o desenho precisa dela para
    saber onde por a regua; o que se arredonda e so a data que se le.
    """
    baixo = min(de, para)
    ordenados, _ = paragens_das_datas(de, para, marcos)
    paragens = [(d - baixo).days for d in ordenados]
    p = max(0.0, min(1.0, t_rel / duracao if duracao else 0.0))
    pos, qual, dentro = posicao_com_paragens(p, paragens)
    return baixo + datetime.timedelta(days=int(round(pos))), qual, dentro, pos


def datas(L, A, de, para, marcos, t_rel, duracao):
    """A fita de duas datas, dia a dia. A mesma dos anos, com a lente aberta.

    O Tiago, a 17 de setembro: "O rebobinar inicial cria-me na mesa um que rebobina da
    data de hoje ate a data de 25 de dezembro de 2025". Entre 4 de outubro de 2026 e 25
    de dezembro de 2025 nao ha um unico ano para mostrar: ha nove meses. Por isso a fita
    passa a andar em DIAS e a regua de baixo passa a ser de MESES, com os nomes.

    Tudo o resto e o contador de anos: as mesmas cores, as mesmas fontes, o mesmo rasto,
    a mesma curva de movimento e as mesmas paragens do posicao_com_paragens. Isto e a
    mesma fita vista de mais perto, e nao um segundo desenho a competir com o primeiro.

    Serve nos dois sentidos. A recuar, a fita desliza para a DIREITA, como uma cassete
    a rebobinar; a avancar, para a esquerda. Quem decide e a ordem das duas datas.
    """
    baixo, cima = min(de, para), max(de, para)
    dias = (cima - baixo).days
    recua = para < de
    ordenados, por_data = paragens_das_datas(de, para, marcos)
    data_centro, qual, dentro, pos = data_do_instante(de, para, marcos, t_rel, duracao)

    # PIXEIS POR DIA. Um mes ocupa cerca de um terco do ecra num troco de meses, que e o
    # caso dele. Num troco de anos essa escala poria a regua a passar depressa de mais
    # para os nomes se lerem, por isso encolhe com a raiz da distancia: a tres anos, o
    # mes fica com pouco mais de metade da largura.
    largura_mes = L * 0.30 * min(1.0, math.sqrt(300.0 / max(1, dias)))
    passo = largura_mes / 30.44

    # Velocidade, para o rasto e para os dias. Mede-se como no contador de anos, com uma
    # amostra vizinha no tempo, mas guarda-se em PIXEIS por segundo: assim as contas do
    # rasto sao as mesmas que la, seja qual for a escala a que a fita esta.
    dt = 1.0 / 25.0
    _, _, _, pos2 = data_do_instante(de, para, marcos, t_rel + dt, duracao)
    px_s = abs(pos2 - pos) / dt * passo
    unidade = L * 0.30                      # o passo de um ano no contador de anos

    tela = Image.new("RGB", (L, A), FUNDO)
    d = ImageDraw.Draw(tela)
    y_linha = int(A * 0.60)
    d.line([(0, y_linha), (L, y_linha)], fill=LINHA, width=2)

    def x_de(data):
        return L / 2.0 + ((data - baixo).days - pos) * passo

    meia = L / (2.0 * passo) + 2

    # A REGUA DE MESES, por baixo da linha, com o NOME DE CADA MES. Eram 32 px em letra
    # fina a (128,114,122), 4,4 para 1 de contraste: texto que so se le de perto, e a sala
    # esta a 15 metros. Passam a ter o corpo da legenda e 8,3 para 1. O ano que ia em letra
    # miuda por baixo de janeiro saiu: a 30 px nao se lia de todo, e o ano ja esta escrito
    # por extenso na data grande, que e a que se le primeiro.
    f_mes = ImageFont.truetype(FONTE, CORPO_ROTULO)
    inicio_visivel = baixo + datetime.timedelta(days=int(math.floor(pos - meia)))
    mes = datetime.date(inicio_visivel.year, inicio_visivel.month, 1)
    maiores = []
    while True:
        x = x_de(mes)
        if x > L + largura_mes:
            break
        maiores.append((x, baixo <= mes <= cima,
                        MESES_CURTOS[mes.month - 1] if baixo <= mes <= cima else None))
        mes = datetime.date(mes.year + mes.month // 12, mes.month % 12 + 1, 1)

    # OS DIAS SO APARECEM COM A FITA QUASE PARADA, e a regua vai de borda a borda em
    # qualquer instante: ver _regua(), que e a mesma peca do contador de anos.
    nitidez = max(0.0, 1.0 - px_s / 700.0)
    _ponteiro(d, L, A, y_linha)
    _regua(d, L, A, y_linha, L / 2.0 - pos * passo, passo, maiores, nitidez, f_mes)

    # A DATA GRANDE AO CENTRO, com o rasto do contador de anos por tras. A conta do
    # rasto e a de la, escrita em pixeis: um passo de ano por segundo da uma copia, e a
    # largura total nunca passa 42 por cento desse passo, senao lia-se a data duplicada.
    f_data = ImageFont.truetype(FONTE, int(A * CORPO_NUMERO))
    rastos, largura_rasto = _rasto(px_s, unidade)
    sentido = 1 if recua else -1
    texto_data = texto_da_data(data_centro)
    y_data = y_linha - int(A * 0.14)
    for r in range(rastos, -1, -1):
        x = L / 2.0 + sentido * largura_rasto * (r / max(1.0, rastos))
        fade = 1.0 if r == 0 else 0.22 * (1.0 - r / (rastos + 1.0))
        c = tuple(int(FUNDO[i] + (ANO_PERTO[i] - FUNDO[i]) * fade) for i in range(3))
        _texto(d, texto_data, f_data, x, y_data, c)

    # OS ROTULOS ACENDEM E APAGAM DENTRO DA SUA PARAGEM, como no contador de anos: o de
    # partida por baixo da data de partida no arranque, o de chegada por baixo da data
    # de chegada quando ela para. Ficam abaixo da regua para nao lhe cairem em cima.
    f_marco = ImageFont.truetype(FONTE, CORPO_ROTULO)
    for data_m in ordenados:
        txt = por_data.get(data_m)
        if not txt:
            continue
        x0 = x_de(data_m)
        if x0 < -L or x0 > 2 * L:
            continue
        perto = 1.0 - min(1.0, abs((data_m - baixo).days - pos) / 30.44)
        aceso = 0.0
        if qual is not None and ordenados[qual] == data_m:
            aceso = min(1.0, dentro / 0.18) * min(1.0, (1.0 - dentro) / 0.18)
        if perto > 0.02 and aceso > 0.02:
            alfa = perto ** 1.2 * aceso
            _risco_do_marco(tela, d, x0, y_linha, alfa)
            _texto(d, txt, f_marco, x0, y_linha + int(A * Y_ROTULO),
                   tuple(int(MARCO_TEXTO[i] * alfa) for i in range(3)))
    return tela


def meses(L, A, ano, marcas, t_rel, duracao, troco=(0.0, 1.0), abre=True):
    """A fita de um ano so, mes a mes, com acontecimentos marcados.

    `marcas` e uma lista de (dia, mes, texto, grande). Os grandes sao os dois
    nascimentos, e sao os unicos que param a fita a serio. Esta fita anda no
    sentido NORMAL do tempo, da esquerda para a direita, porque aqui ja nao
    estamos a recuar: chegamos a 1995 e seguimos o ano.
    """
    p = max(0.0, min(1.0, t_rel / duracao if duracao else 0.0))

    # ENTRADA COM ZOOM, e a razao e uma queixa do Tiago: "o movimento nao esta
    # natural na passagem da timeline por anos para a timeline por meses".
    #
    # Antes, a fita dos anos acabava com 1995 grande ao centro e a dos meses
    # comecava logo na escala do mes, ou seja mudava de escala num corte sem
    # nada que explicasse a mudanca. Agora o primeiro segundo e meio abre a
    # escala do ano ate a do mes, como quem se aproxima de um ponto da fita.
    # Os meses e a linha aparecem a medida que ha espaco para eles.
    # A ENTRADA SO NO PRIMEIRO CLIP DA FITA.
    #
    # O Tiago viu: "ha um efeito estranho apos o abre a sapo em aveiro". Eram
    # DOIS "1995" sobrepostos, um pequeno no topo e outro grande por cima da
    # imagem do SAPO. A causa: cada clip de fita recomecava a entrada com zoom,
    # portanto o clip seguinte desenhava outra vez o ano grande e em baixo,
    # enquanto o anterior ainda estava no ecra a desvanecer.
    #
    # Num clip que CONTINUA a fita onde o anterior a deixou, nao ha nada para
    # abrir: a escala ja e a do mes. Marca-se com um "c" no fim do intervalo.
    T_ENTRADA = 1.5 if abre else 0.0
    entrada = 1.0 if not abre else suave(min(1.0, t_rel / T_ENTRADA))
    largura_ano = (L * 0.30) + (L * 2.4 - L * 0.30) * entrada
    # OS MESES SAO OS MESMOS DA REGUA DO CONTADOR, decisao 084 (sistema A do letreiro).
    # Esta fita tinha a sua propria lista em minusculas, e a regua do contador que passa
    # segundos antes ja usa a MESES_CURTOS em maiusculas desde 18 de setembro, precisamente
    # porque "na sala nao ha leitura de perto". Eram duas grafias do mesmo mes em duas pecas
    # vizinhas do mesmo bloco, e uma delas o projecto ja tinha declarado ilegivel.

    def fracao(dia, mes):
        return ((mes - 1) + (dia - 1) / 31.0) / 12.0

    # TROCO DO ANO A PERCORRER, e a lista de paragens feita a mao.
    #
    # Duas vezes tentei resolver isto com contas sobre indices e as duas vezes
    # saiu errado, de maneiras que so se viam a olhar para o video:
    #
    #   1. Tirar paragens repetidas juntava o Coa e a Clara numa so, porque sao
    #      os dois a 24 de novembro, e uma das duas nunca aparecia.
    #   2. Somar e subtrair 1 ao indice da paragem conforme o troco comecava ou
    #      nao numa marca deixava a ULTIMA marca de cada troco sem paragem, ou
    #      seja "Nasce o Tiago" nao chegava a ser dito no primeiro clip.
    #
    # Agora cada paragem sabe a que marca pertence, ou a nenhuma. Duas marcas no
    # mesmo dia sao duas paragens no mesmo sitio, que e precisamente o que se
    # quer: a fita fica parada e as palavras trocam.
    ini, fim = troco
    dentro_troco = [m for m in marcas
                    if ini - 1e-4 <= fracao(m[0], m[1]) <= fim + 1e-4]

    passos = []
    if not dentro_troco or abs(fracao(dentro_troco[0][0], dentro_troco[0][1]) - ini) > 1e-4:
        passos.append((ini, None))
    for m in dentro_troco:
        passos.append((fracao(m[0], m[1]), m))
    if not dentro_troco or abs(fracao(dentro_troco[-1][0], dentro_troco[-1][1]) - fim) > 1e-4:
        passos.append((fim, None))

    paragens = [x[0] for x in passos]
    pos, qual, dentro = posicao_com_paragens(p, paragens, 0.70, parar_no_primeiro=abre)
    atual = passos[qual][1] if qual is not None and 0 <= qual < len(passos) else None
    # Aparece e desaparece nas pontas da paragem, para nao piscar no corte.
    aceso = min(1.0, dentro / 0.18) * min(1.0, (1.0 - dentro) / 0.18) if atual else 0.0

    tela = Image.new("RGB", (L, A), FUNDO)
    d = ImageDraw.Draw(tela)
    y_linha = int(A * 0.56)
    d.line([(0, y_linha), (L, y_linha)], fill=LINHA, width=2)
    d.line([(L // 2, y_linha - 230), (L // 2, y_linha + 150)], fill=(38, 30, 36), width=3)

    f_ano = ImageFont.truetype(FONTE, int(A * 0.13))
    # 38 E NAO OS 46 DA REGUA, e a razao e a folga por baixo: os meses sao centrados em
    # y_linha + 34 e a data do marco em y_linha + 64. Medido com a Pillow, a faixa dos meses
    # acaba 2 px dentro da faixa da data a 38 px, 3 px a 32 px em letra fina (o que estava
    # ca antes) e 5,5 px a 46. Ou seja 38 em negrito le-se melhor E encosta menos do que o
    # que la estava. A 42 ja encostava mais.
    f_mes = ImageFont.truetype(FONTE, 38)
    f_data = ImageFont.truetype(FONTE, 40)
    f_txt = ImageFont.truetype(FONTE, 58)
    f_gr = ImageFont.truetype(FONTE, 96)

    # O ano comeca grande, no sitio onde estava na fita dos anos, e encolhe
    # para o alto enquanto os meses se abrem. E isso que costura as duas fitas.
    corpo_ano = int(A * (0.17 - 0.04 * entrada))
    y_ano = int(y_linha - A * 0.14 + (A * 0.16 - (y_linha - A * 0.14)) * entrada)
    _texto(d, str(ano), ImageFont.truetype(FONTE, corpo_ano), L / 2.0, y_ano,
           tuple(int(246 + (150 - 246) * entrada) for _ in range(1)) * 3)

    desvio = L / 2.0 - pos * largura_ano
    for m in range(12):
        x = desvio + fracao(1, m + 1) * largura_ano
        if -80 < x < L + 80 and entrada > 0.25:
            k = (entrada - 0.25) / 0.75
            cinza = tuple(int(c * k) for c in REGUA_TEXTO)
            d.line([(x, y_linha - 9), (x, y_linha + 9)],
                   fill=tuple(int(c * k) for c in LINHA), width=2)
            _texto(d, MESES_CURTOS[m], f_mes, x, y_linha + 34, cinza)

    for dia, mes, txt, grande, _img in marcas:
        fr = fracao(dia, mes)
        x = desvio + fr * largura_ano
        if x < -L or x > 2 * L:
            continue
        # Os riscos estao sempre todos la: e isso que da a sensacao de um ano
        # cheio. So as palavras e que sao uma de cada vez.
        visivel = max(0.0, 1.0 - abs(fr - pos) * 9.0)
        alto = 64 if grande else 34
        base = 0.28 + 0.72 * visivel
        cor = tuple(int(c * base) for c in MARCO)
        d.line([(x, y_linha - alto), (x, y_linha + 18)],
               fill=cor, width=9 if grande else 4)
        if grande:
            d.ellipse([x - 14, y_linha - alto - 14, x + 14, y_linha - alto + 14], fill=cor)

    if atual and aceso > 0.02:
        dia, mes, txt, grande, img = atual
        x = desvio + fracao(dia, mes) * largura_ano
        alto = 64 if grande else 34
        fonte = f_gr if grande else f_txt
        claro = tuple(int(MARCO_TEXTO[k] * aceso) for k in range(3))
        y_txt = y_linha - alto - (86 if grande else 46)
        if img:
            # 0,20 e nao 0,24: a 0,24 a imagem encostava ao "1995" do topo.
            miniatura = imagem_da_marca(img, int(A * 0.20))
            if miniatura is not None:
                cx = int(x - miniatura.width / 2)
                cy = int(y_txt - 38 - miniatura.height)
                if -miniatura.width < cx < L and cy > 0:
                    vinheta = Image.new("RGB", miniatura.size, FUNDO)
                    tela.paste(Image.blend(vinheta, miniatura, aceso), (cx, cy))
                    ImageDraw.Draw(tela).rectangle(
                        [cx - 2, cy - 2, cx + miniatura.width + 1,
                         cy + miniatura.height + 1],
                        outline=tuple(int(c * aceso) for c in MARCO), width=3)
        _texto(d, txt, fonte, x, y_txt, claro)
        _texto(d, "%d de %s" % (dia, ["janeiro", "fevereiro", "março", "abril", "maio",
                                      "junho", "julho", "agosto", "setembro", "outubro",
                                      "novembro", "dezembro"][mes - 1]),
               f_data, x, y_linha + 64,
               tuple(int(c * aceso) for c in (214, 182, 196)))
    return tela


def ler_anos(texto):
    """"2026>1995|2026=4 de outubro de 2026;2012=O encontro" -> parametros.

    Um rotulo sem "ano=" e do ano de partida. E o que a Mesa escreve por omissao,
    "2026>1995|4 de outubro de 2026", e ate 14 de setembro essa peca era deitada
    fora sem aviso: o contador saia sem a data do casamento que o Tiago escreveu.
    """
    corpo, _, resto = (texto or "").partition("|")
    de, _, para = corpo.partition(">")
    de, para = int(de.strip()), int(para.strip())
    marcos = []
    for peca in resto.split(";"):
        peca = peca.strip()
        if not peca:
            continue
        ano, igual, rot = peca.partition("=")
        if igual and ano.strip().isdigit():
            if rot.strip():
                marcos.append((int(ano.strip()), rot.strip()))
        else:
            marcos.append((de, peca))
    return de, para, marcos


def _data(texto):
    """"25/12/2025" -> datetime.date. Aceita "4/10/2026", sem o zero a frente."""
    dia, mes, ano = (p.strip() for p in (texto or "").strip().split("/"))
    return datetime.date(int(ano), int(mes), int(dia))


def _e_data(texto):
    try:
        _data(texto)
        return True
    except (ValueError, AttributeError):
        return False


def ler_datas(texto):
    """"04/10/2026>25/12/2025|a partida;25/12/2025=a chegada" -> parametros.

    As datas vao em dd/mm/aaaa e um rotulo sem "data=" e o da partida, tal e qual como
    no contador de anos: a Mesa escreve o rotulo de partida assim, e quem le um x
    escrito a mao nao tem de saber de duas convencoes diferentes.
    """
    corpo, _, resto = (texto or "").partition("|")
    de, _, para = corpo.partition(">")
    de, para = _data(de), _data(para)
    marcos = []
    for peca in resto.split(";"):
        peca = peca.strip()
        if not peca:
            continue
        data, igual, rot = peca.partition("=")
        if igual and _e_data(data):
            if rot.strip():
                marcos.append((_data(data), rot.strip()))
        else:
            marcos.append((de, peca))
    return de, para, marcos


def ler_contador(texto):
    """O tipo de contador e os seus parametros.

    Devolve ("anos", de, para, marcos) com os anos em inteiros, ou ("datas", de, para,
    marcos) com datetime.date. O formato de anos, "2026>1995|4 de outubro de 2026", nao
    mudou uma virgula; o de datas e de 17 de setembro, para a abertura rebobinar do dia
    do casamento ate ao dia do pedido antes de rebobinar ate 1995.

    QUEM DECIDE E A BARRA, e nao o comprimento do que esta antes do ">". Um ano nunca
    leva barra e uma data leva sempre duas, e assim um "4/10/2026" escrito a mao sem o
    zero a frente e lido como data, que e o que ele quer dizer.
    """
    corpo = (texto or "").partition("|")[0]
    if "/" in corpo:
        de, para, marcos = ler_datas(texto)
        return "datas", de, para, marcos
    de, para, marcos = ler_anos(texto)
    return "anos", de, para, marcos


def contador_recua(texto):
    """True quando o contador anda para tras no tempo, seja ele por anos ou por datas.

    SO OS QUE RECUAM LEVAM O REBOBINAR. O 1995>2011 avanca e sai sem som de fita; os
    dois da abertura recuam e levam-no os dois. Um x que nao se le nao recua nada: nao
    e aqui que se parte um render por causa de um contador mal escrito na Mesa.
    """
    try:
        _tipo, de, para, _marcos = ler_contador(texto)
    except (ValueError, AttributeError):
        return False
    return para < de


def ano_de_chegada(texto):
    """O ano onde o contador acaba, por anos ou por datas, ou None se o x nao se le.

    E o que distingue o contador da abertura dos outros desde que a abertura tem dois
    a recuar: o da abertura e o que acaba em 1995, logo antes das partes da fita.
    """
    try:
        tipo, _de, para, _marcos = ler_contador(texto)
    except (ValueError, AttributeError):
        return None
    return para if tipo == "anos" else para.year


def ler_meses(texto):
    """"1995|17/01 Kobe;*12/09 Nasce o Tiago" -> (ano, marcas, troco).

    O asterisco marca os grandes, que sao os dois nascimentos. O cabecalho pode
    levar o troco do ano a percorrer: "1995@0-0.70|..." faz a fita parar em
    setembro, para o clip seguinte poder ser a fotografia do bebe.
    """
    corpo, _, resto = (texto or "").partition("|")
    troco, abre = (0.0, 1.0), True
    if "@" in corpo:
        corpo, _, faixa = corpo.partition("@")
        if faixa.endswith("c"):      # continua a fita do clip anterior
            faixa, abre = faixa[:-1], False
        a, _, b = faixa.partition("-")
        troco = (float(a), float(b))
    marcas = []
    for peca in resto.split(";"):
        peca = peca.strip()
        if not peca:
            continue
        grande = peca.startswith("*")
        peca = peca.lstrip("*").strip()
        imagem = ""
        if "@" in peca:
            peca, _, imagem = peca.partition("@")
            peca, imagem = peca.strip(), imagem.strip()
        data, _, rot = peca.partition(" ")
        dia, _, mes = data.partition("/")
        marcas.append((int(dia), int(mes), rot.strip(), grande, imagem))
    marcas.sort(key=lambda m: (m[1], m[0]))
    return int(corpo.strip()), marcas, troco, abre
