# -*- coding: utf-8 -*-
"""A musica dos creditos: o fim audivel de uma musica e o segundo em que ela entra (2 de outubro).

O TIAGO, a 2 de outubro: "Gostava de tambem poder alterar a musica que toca nos creditos, sendo que
idealmente gostava de tambem a conseguir editar na propria Mesa. Neste momento temos os Queen a vir
dos amigos, mas acho que gostava de voltar ao Taking care of business."

A ESCOLHA, no estado da Mesa (contrato de 2 de outubro): est.creditos.musica = {ficheiro, inicio},
com inicio "inicio", "fim" (a musica acaba com os creditos) ou um numero de segundos do ficheiro.
SEM ELA, "Como esta": a ultima musica do filme continua de onde o filme a deixa (ponto5_creditos.py),
e nada aqui e chamado. Todas as funcoes que recebem a escolha devolvem None quando ela nao existe.

UMA REGRA SO, PARA QUALQUER MUSICA DA BIBLIOTECA, igual na Mesa e no render:

1. O FIM AUDIVEL (fim_das_medidas, fim_audivel) e o inicio do ultimo silencio que chega ao fim do
   ficheiro, com a definicao de silencio que o projeto ja usa: -45 dB durante 0,3 s, o SILENCIO_DB do
   montar_da_mesa.silencio_no_inicio() e do audio_para_mesa.silencios_do_original(). Silencios
   separados por menos de JUNTAR_S (um estalido) contam como um so. Sem silencio no fim, e a duracao do
   ficheiro. A Mesa ja tem estes silencios de cada musica (window.AUDIO[f].silencios), medidos pela
   mesma funcao: o gerar_mesa.py so tem de chamar para_a_mesa() sobre o indice que ja tem, sem ler
   nenhum ficheiro de som. Medido a 2 de outubro nas 49 musicas que a Mesa oferece: o criterio "ultimo
   instante acima de -50 dBFS RMS em 400 ms" da o mesmo fim a menos de 0,6 s em 46, e no pior 1,24 s
   (o Careless Whisper; depois a Mariah, 1,11, e o Harry Potter, 0,73), sempre com o do silencio mais
   tarde. E o fim tirado do indice da Mesa e igual ao medido no original nas 48 que o indice tem.
   PORQUE NAO A DURACAO DO FICHEIRO: os Queen tem 245,55 s e calam-se aos 239,34; o Taking Care of
   Business tem 296,25 e cala-se aos 291,81; o "Dtmf" do Bad Bunny tem 19 s de silencio no fim. Contar
   pela duracao punha os creditos a acabar em silencio sem ninguem saber.

2. COMO ACABA (como_acaba_do_perfil): "seco" ou "a desvanecer", e ha quantos segundos. Pelo perfil de
   sonoridade segundo a segundo da copia da Mesa (window.AUDIO[f].perfil, decimas de LUFS): o ultimo
   segundo a menos de DESVANECER_LU da mediana dos 30 s antes do fim e onde o desvanecimento comeca.
   So informa (a Mesa mostra-o); nao muda a entrada.

3. A ENTRADA (entrada):
   - "inicio": o zero do ficheiro;
   - "fim": o fim audivel menos a duracao dos creditos, ou o zero se a musica for mais curta;
   - um numero: esse segundo.
   Depois, como em qualquer musica marcada na Mesa, salta o silencio que la comece (o
   montar_da_mesa.silencio_no_inicio(), aqui sobre os silencios ja medidos, como o somSilencioNoInicio
   da Mesa). Nao se encosta a nenhuma frase: ver ENTRADA_FIM_NAO_ENCOSTA. A Mesa avisa e nunca corrige
   (083): se a musica acaba antes dos creditos, se repete o que ja tocou no filme, e onde fica a frase
   medida mais perto (frase_mais_perto), para ele escrever esse numero se quiser.

4. A JUNCAO COM O FILME (faixas_dos_creditos) e uma troca de musica como as de dentro do filme, com as
   funcoes do render: a que sai continua CRUZAMENTO (2,2 s) por cima da que entra e desce nesse tempo,
   a que entra sobe no mesmo tempo, ou em 0,03 s se entra num inicio ou num ataque (094, 095), as duas
   com curve=qsin; e se a troca estiver medida em data/fins_de_frase.csv (096), a que sai acaba no fim
   da frase e a que entra sobe no tempo da cauda. O corte e o instante em que os creditos comecam: o fim
   do filme menos o render.FADE_FIM_IMAGEM, como no ponto5. No fim de tudo, o FADE_FIM_SOM do render.

Uso:  py -3.11 scripts/musica_creditos.py <musica> [inicio|fim|<segundos>] [--creditos <s>]
      py -3.11 scripts/musica_creditos.py --teste
So le. Nao escreve em lado nenhum (os silencios de cada musica ja estao no indice do audio_para_mesa).
"""
import csv
import io
import json
import math
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

FINS_DE_FRASE = os.path.join(REPO, "data", "fins_de_frase.csv")
ENTRADAS_ATAQUE = os.path.join(REPO, "data", "entradas_ataque.csv")
MUSICAS_BATIDAS = os.path.join(REPO, "data", "discussao", "musicas_batidas.json")
MONTAGENS = os.path.join(REPO, "data", "montagens")

# O SILENCIO E O DO PROJETO: o montar_da_mesa.SILENCIO_DB e o audio_para_mesa.SILENCIO_DB/SILENCIO_MIN.
# Se um dia mudarem la, os testes deste modulo dizem-no (teste_silencio_igual_ao_do_projeto).
SILENCIO_DB = -45.0
SILENCIO_MIN = 0.3
# Dois silencios separados por menos disto sao um so: entre eles ha um estalido, nao musica. Visto a 2
# de outubro na Ana Faria (1 ms entre 197,567 e 197,568), na Mariah (15 ms) e no Earth, Wind & Fire (0).
JUNTAR_S = 0.1
# O ultimo silencio "chega ao fim" se acabar a menos disto da duracao: o indice da Mesa guarda a duracao
# da copia AAC, que pode diferir uns milesimos da do original.
FOLGA_FIM_S = 0.1
# A janela do montar_da_mesa.silencio_no_inicio(): um silencio que enche os 20 s nao se salta.
JANELA_SILENCIO = 20.0
# Como acaba: o desvanecimento comeca no ultimo segundo a menos de 6 LU da mediana dos 30 s antes do fim
# (sem os ultimos 8, onde ele ja pode estar a descer); a partir de 2 s de descida chama-se desvanecer.
DESVANECER_LU = 6.0
DESVANECER_MIN_S = 2.0
# A musica que acaba antes dos creditos so se avisa a partir de meio segundo: o FADE_FIM_SOM (4 s) ja
# leva os ultimos instantes para zero.
FALTA_AVISO_S = 0.5
ESCOLHAS = ("inicio", "fim")

# "FIM" NAO SE ENCOSTA A UMA FRASE MEDIDA, e e de proposito:
# - a escolha promete que a musica acaba com os creditos. Encostar a entrada a frase de antes poe o fim
#   da musica depois do fim dos creditos, e o FADE_FIM_SOM (4 s) corta-o: numa musica que acaba a
#   desvanecer perde-se so a cauda, mas numa que acaba seca perde-se o acorde final. Encostar a frase de
#   depois deixa silencio debaixo do titulo final. As frases do Taking Care of Business tem 8 compassos,
#   14,9 s: o erro seria ate isso;
# - a duracao dos creditos muda com cada foto e cada nome que eles mexem na Mesa, e a entrada encostada
#   saltaria de frase em frase enquanto eles editam, com o fim a mudar ate 15 s de uma vez;
# - a entrada fica por baixo do cruzamento de 2,2 s com potencia igual (094), como todas as entradas a
#   meio do filme que nao sao um ataque (a retoma do Lang Lang, o proprio Taking Care of Business aos
#   60,8 s, os Filhos do Dragao).
# A frase medida mais perto, quando a musica foi analisada, mostra-se como proposta (frase_mais_perto).
ENTRADA_FIM_NAO_ENCOSTA = True


# --------------------------------------------------------------------------------- as medidas
def _segundos(x):
    return ("%.2f" % x).rstrip("0").rstrip(".").replace(".", ",")


def fim_das_medidas(silencios, duracao):
    """O fim audivel, a partir dos silencios (-45 dB, 0,3 s) do ficheiro inteiro e da duracao dele.

    `silencios` e a lista [[inicio, fim], ...] do audio_para_mesa.silencios_do_original(), por ordem,
    em que um silencio que chega ao fim do ficheiro fecha na duracao. Devolve o inicio do ultimo silencio
    que chega ao fim (juntando os separados por menos de JUNTAR_S), ou a duracao se nenhum chegar.
    Funcao pura: a mesma conta para a Mesa (sobre o indice dela) e para o render (sobre o ficheiro).
    """
    duracao = float(duracao or 0.0)
    lista = sorted([float(a), float(b)] for a, b in (silencios or []) if b is not None and a is not None)
    if not lista or lista[-1][1] < duracao - FOLGA_FIM_S:
        return round(duracao, 3)
    inicio = lista[-1][0]
    for a, b in reversed(lista[:-1]):
        if inicio - b < JUNTAR_S:
            inicio = min(inicio, a)
        else:
            break
    return round(max(0.0, inicio), 3)


def como_acaba_do_perfil(perfil, fim, desde=0.0):
    """("seco" ou "a desvanecer", segundos de descida) pelo perfil segundo a segundo, em decimas de LUFS.

    `perfil[k]` e a sonoridade do segundo k (a partir de `desde`, o inicio da copia no original), como o
    audio_para_mesa.perfil_da_copia() a mede. A descida comeca no fim do ultimo segundo a menos de
    DESVANECER_LU da mediana dos 30 s antes do fim. Sem perfil, ("seco", 0.0).
    """
    if not perfil or fim is None:
        return "seco", 0.0
    fim_k = int(math.floor(fim - desde))
    janela = [perfil[k] / 10.0 for k in range(max(0, fim_k - 30), max(0, fim_k - 8))
              if 0 <= k < len(perfil) and perfil[k] > -700]
    if not janela:
        return "seco", 0.0
    janela.sort()
    mediana = janela[len(janela) // 2]
    ultimo = None
    for k in range(min(len(perfil) - 1, fim_k), max(-1, fim_k - 60), -1):
        if perfil[k] / 10.0 >= mediana - DESVANECER_LU:
            ultimo = k
            break
    if ultimo is None:
        return "seco", 0.0
    descida = max(0.0, round(fim - (desde + ultimo + 1), 1))
    return ("a desvanecer" if descida >= DESVANECER_MIN_S else "seco"), descida


def _ffmpeg():
    import render
    return render.ffmpeg()


def _duracao(caminho):
    pr = os.path.join(os.path.dirname(_ffmpeg()), "ffprobe.exe")
    r = subprocess.run([pr, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def _silencios(caminho):
    """Os silencios do ficheiro inteiro, pela funcao da Mesa (audio_para_mesa), ou pelo mesmo comando."""
    try:
        import audio_para_mesa
        return audio_para_mesa.silencios_do_original(caminho)
    except ImportError:
        pass
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-nostats", "-i", caminho, "-map", "0:a:0", "-af",
                        "silencedetect=noise=%.0fdB:d=%.2f" % (SILENCIO_DB, SILENCIO_MIN), "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    fora, aberto = [], None
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", r.stderr or ""):
        if m.group(1) == "start":
            aberto = max(0.0, float(m.group(2)))
        elif aberto is not None:
            fora.append([round(aberto, 3), round(float(m.group(2)), 3)])
            aberto = None
    if aberto is not None:
        fora.append([round(aberto, 3), round(_duracao(caminho), 3)])
    return fora


def medir(caminho):
    """{duracao, silencios, fim} de um ficheiro de musica. Le o ficheiro (cerca de 1 s por musica)."""
    duracao = _duracao(caminho)
    silencios = _silencios(caminho)
    return {"duracao": round(duracao, 3), "silencios": silencios, "fim": fim_das_medidas(silencios, duracao)}


def fim_audivel(caminho):
    """O fim audivel de um ficheiro, em segundos: ver fim_das_medidas()."""
    return medir(caminho)["fim"]


def para_a_mesa(audio):
    """{ficheiro: {fim, acaba, desvanece}} das musicas do indice da Mesa (o window.AUDIO que o
    audio_para_mesa.preparar() devolve em ["audio"]), sem ler nenhum ficheiro de som. O gerar_mesa.py
    pode po-lo na pagina como window.MUSICA_FIM; a Mesa usa o `fim` para a escolha "fim" e para os
    avisos, e o `acaba` so para dizer como ela acaba."""
    fora = {}
    for f, a in (audio or {}).items():
        if (a.get("tipo") or "musica") != "musica" or not a.get("duracao"):
            continue
        # o indice so poe os silencios quando os ha (audio_para_mesa.preparar): ausente quer dizer nenhum, e
        # entao a musica acaba no fim do ficheiro (O Rei Leao, o Manu Chao)
        fim = fim_das_medidas(a.get("silencios") or [], a["duracao"])
        acaba, descida = como_acaba_do_perfil(a.get("perfil"), fim, a.get("desde") or 0.0)
        fora[f] = {"fim": fim, "acaba": acaba, "desvanece": descida}
    return fora


# --------------------------------------------------------------------------------- a entrada
def silencio_no_inicio_das_medidas(silencios, dentro):
    """Os segundos de silencio que uma entrada em `dentro` salta, como o montar_da_mesa.silencio_no_inicio()
    e o somSilencioNoInicio da Mesa: o silencio que comeca ate 0,05 s depois do in e dura 0,3 s a partir
    dele, se acabar antes dos 20 s da janela."""
    for a, b in sorted([float(a), float(b)] for a, b in (silencios or [])):
        if b <= dentro + 1e-6:
            continue
        if a - dentro > 0.05 or b - max(a, dentro) < SILENCIO_MIN - 1e-6:
            return 0.0
        return 0.0 if b - dentro >= JANELA_SILENCIO - 0.05 else round(b - dentro, 2)
    return 0.0


def escolha_ausente(escolha):
    """True quando nao ha escolha nenhuma («Como esta», sem aviso): None, "", 0 ou False, os mesmos que o
    `if(!m)` do credMusicaEscolha() da Mesa. Um {} (ou uma lista) e uma escolha mal escrita, sem ficheiro, e
    avisa nos dois lados (contrato, seccoes 6 e 9): ate 2 de outubro, a noite, o `if not escolha` tratava-o
    como ausente, calado, e a Mesa dizia que nao tinha ficheiro."""
    if escolha is None:
        return True
    if isinstance(escolha, (dict, list, tuple)):
        return False
    return not escolha


def escolha_valida(escolha):
    """A escolha normalizada ({ficheiro, inicio}) ou None (Como esta), e um aviso se vinha mal escrita."""
    if escolha_ausente(escolha):
        return None, None
    if not isinstance(escolha, dict) or not str(escolha.get("ficheiro") or "").strip():
        return None, "creditos.musica sem ficheiro: fica como esta"
    inicio = escolha.get("inicio", "fim")
    if isinstance(inicio, str) and inicio.strip().lower() in ESCOLHAS:
        inicio = inicio.strip().lower()
    else:
        try:
            inicio = float(str(inicio).replace(",", "."))
        except (TypeError, ValueError):
            return None, "creditos.musica com inicio %r, que nao e inicio, fim nem um numero: fica como esta" % (inicio,)
        if not (inicio >= 0.0) or math.isinf(inicio):
            return None, "creditos.musica com inicio %r, que nao e um segundo do ficheiro: fica como esta" % (inicio,)
    return {"ficheiro": str(escolha["ficheiro"]).strip(), "inicio": inicio}, None


def entrada(inicio, fim, dur_creditos, silencios=None):
    """O segundo do ficheiro em que a musica entra nos creditos, e o que se diz dele.

    inicio: "inicio", "fim" ou segundos; fim: o fim audivel; dur_creditos: a duracao dos creditos (do
    tempos_dos_creditos() do ponto5, o Lay.dur da Mesa); silencios: os do ficheiro, para saltar o silencio
    em que a entrada caia. Devolve {in_s, pedido, saltou, toca, falta, avisos}: `toca` e quanto dela se
    ouve nos creditos e `falta` quantos segundos de silencio ficam no fim deles.
    """
    avisos = []
    fim, dur = float(fim), float(dur_creditos)
    if inicio == "inicio":
        pedido = 0.0
    elif inicio == "fim":
        pedido = max(0.0, fim - dur)
        if fim < dur:
            avisos.append("a musica so tem %s s ate se calar e os creditos tem %s: comeca do inicio"
                          % (_segundos(fim), _segundos(dur)))
    else:
        pedido = float(inicio)
    saltou = silencio_no_inicio_das_medidas(silencios, pedido)
    in_s = round(pedido + saltou, 2)
    if saltou:
        avisos.append("saltei %s s de silencio: entra aos %s s do ficheiro" % (_segundos(saltou), _segundos(in_s)))
    toca = max(0.0, min(dur, fim - in_s))
    falta = round(max(0.0, dur - toca), 2)
    if in_s >= fim:
        avisos.append("aos %s s a musica ja se calou (cala-se aos %s): os creditos ficam em silencio"
                      % (_segundos(in_s), _segundos(fim)))
    elif falta > FALTA_AVISO_S:
        avisos.append("acaba %s s antes do fim dos creditos: o fim fica em silencio" % _segundos(falta))
    return {"in_s": in_s, "pedido": round(pedido, 2), "saltou": saltou, "toca": round(toca, 2),
            "falta": falta, "avisos": avisos}


def ja_tocou(ficheiro, in_s, toca, linhas_som=None, nome="v3"):
    """O que os creditos tocam desta musica que ja tocou no filme, pelo som.csv da montagem.

    Devolve (segundos, [(de, ate) no ficheiro]). Conta so os trocos que o filme toca por inteiro (in_s
    a in_s + dura_s), sem os 2,2 s em que um leito desce por cima do seguinte.
    """
    if linhas_som is None:
        caminho = os.path.join(MONTAGENS, nome + ".som.csv")
        linhas_som = []
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8-sig", newline="") as fh:
                linhas_som = list(csv.DictReader(fh))
    a0, a1 = float(in_s), float(in_s) + float(toca)
    trocos = []
    for r in linhas_som:
        if r.get("ficheiro") != ficheiro or (r.get("voz") or "").strip() or (r.get("video") or "").strip():
            continue
        b0 = float(r.get("in_s") or 0.0)
        b1 = b0 + float(r.get("dura_s") or 0.0)
        de, ate = max(a0, b0), min(a1, b1)
        if ate - de > 0.05:
            trocos.append((round(de, 2), round(ate, 2)))
    return round(sum(b - a for a, b in trocos), 2), trocos


def frases_medidas(ficheiro):
    """[(segundo, forca)] dos inicios de frase medidos desta musica: as fronteiras de Foote a 4 s do
    data/discussao/musicas_batidas.json (o metodo da 095), cada uma levada a batida mais perto. Vazio
    para uma musica que nao foi analisada."""
    try:
        with open(MUSICAS_BATIDAS, encoding="utf-8") as fh:
            dados = json.load(fh).get(ficheiro)
    except (OSError, ValueError):
        return []
    if not dados or not dados.get("beats"):
        return []
    batidas = dados["beats"]
    fora = []
    for t, forca in dados.get("picos4") or []:
        b = min(batidas, key=lambda x: abs(x - t))
        fora.append((round(b, 2), round(forca, 2)))
    return fora


def frase_mais_perto(ficheiro, t, so_antes=False):
    """(segundo, forca) do inicio de frase medido mais perto de t (so os de antes, com so_antes), ou None."""
    lista = [x for x in frases_medidas(ficheiro) if not so_antes or x[0] <= t + 1e-6]
    return min(lista, key=lambda x: abs(x[0] - t)) if lista else None


# --------------------------------------------------------------------------------- a passagem no corte
# O TIAGO ESCOLHEU A (C), a 2 de outubro as 18:47 ("c"): alongar o ultimo clip do filme para o corte dos creditos
# cair no fim de uma frase da musica que sai, e a imagem e a musica mudarem juntas (docs/DISCUSSAO.md, "A passagem
# dos Queen para o Taking Care of Business"). A Mesa diz, na aba Musica dos creditos, em que segundo do ficheiro a
# musica do fim do filme esta no corte, se o corte cai a meio de uma frase, e quantos segundos faltam ao ultimo
# clip para cair no fim da frase mais perto. AVISA, NUNCA CORRIGE (083): e ele que muda a duracao do clip, como
# sempre. E antes do render final a passagem mede-se outra vez (096): um agente analisa, outro verifica.
#
# OS FINS DE FRASE DA MUSICA QUE SAI vem de tres medidas, por esta ordem de confianca (zonas_de_frase):
# 1. "verificada": o sai_s de uma linha de data/fins_de_frase.csv em que ela e a que sai (096, analisada e
#    verificada; a Mesa tem-nas no AUDIO_INFO.fins). Os Queen tem uma, aos 97,50 s (t713, 29 de setembro);
# 2. "voz": os fins de linha da voz, pela conta do scripts/discussao/juncao_creditos.py (a voz ao centro, |M| - |S|
#    de 1 a 4 kHz, e as pausas dela 9 dB abaixo do nivel das linhas durante 0,25 s ou mais), medidos no ficheiro
#    inteiro com a janela que o juncao usa a volta de um corte (3 s antes, 4,5 s depois), posta de meio em meio
#    segundo (fins_de_linha). Sao CANDIDATOS, como no juncao: a 096 pede que se oucam e verifiquem. Com a Mesa de 2
#    de outubro os Queen estao aos 68,70 s no corte, e a linha acaba aos 71,28 s (a voz cala-se; a batida que a
#    fecha bate aos 71,35 e a linha nova entra aos 72,16): sao os mesmos numeros do juncao_creditos.py nesse corte;
# 3. "batida": os inicios de frase da 095 (data/discussao/musicas_batidas.json, frases_medidas), SO numa musica sem
#    a medida da voz. Numa musica cantada nao servem: nos Queen a fronteira mais forte perto do corte (69,73 s) cai a
#    meio de uma linha cantada.
#
# O QUE E O CORTE NO FIM DE UMA FRASE (onde_cai): a menos de CERTO_S (0,1 s) de um fim verificado ou de uma batida; e
# num fim de linha da voz, de CERTO_ANTES_DA_VOZ (0,05 s) antes de a voz se calar ate CERTO_PAUSA_S (0,5 s) dentro da
# pausa, e sempre FOLGA_LINHA_NOVA (0,15 s) antes de a linha nova entrar. O comeco e o do juncao_creditos.propostas(),
# que so da o corte por dentro de uma pausa a partir de 0,05 s antes dela (p[0] - 0.05); ate ao corretor de 2 de
# outubro a noite era 0,1 s, e um corte entre os dois a Mesa dava por certo e o juncao por "a meio de uma linha". A
# pausa conta porque e o que o propostas() aceita para a saida no corte ("o corte cai numa pausa: acaba no corte e
# cala-se antes do sinal seguinte"), e porque a batida que fecha uma linha costuma pertencer-lhe: a equipa do render
# escolheu os 71,42 s, 0,14 s depois de a voz se calar, para os Queen. O FIM E DE PROPOSITO MAIS CURTO do que o do
# propostas(), que aceita a pausa inteira ate a linha nova (a cauda encolhe para caber antes do sinal seguinte): o meio
# segundo e o maior fim de frase das caudas da 096 a meio (CAUDA_MAX_B do juncao), e a Mesa so propoe o que e seguro.
#
# O QUE O MOVE: alongar o ultimo clip do filme D segundos poe o corte D segundos mais tarde no ficheiro (a musica do
# fim do filme comecou antes dele e continua). A Mesa confirma-o com o palco antes de o dizer (credMusicaPassagem).
LINHA_SR = 44100
LINHA_PAUSA_DB = 9.0               # juncao_creditos.PAUSA_DB
LINHA_PAUSA_MIN_S = 0.25           # juncao_creditos.PAUSA_MIN_S
LINHA_NOVA_DB = 5.0                # juncao_creditos.LINHA_DB
LINHA_ANTES, LINHA_DEPOIS = 3.0, 4.5   # a janela do juncao_creditos.main() a volta do corte
LINHA_PASSO = 0.5                  # de meio em meio segundo: cada instante fica em 15 janelas
LINHA_JUNTAR = 0.1                 # dois fins a menos disto sao o mesmo, achado com niveis diferentes
LINHA_VOTOS = 3                    # e so conta o que pelo menos 3 janelas acham (1 em 5 das que o veem)
CERTO_S = 0.1
CERTO_ANTES_DA_VOZ = 0.05           # juncao_creditos.propostas(): p[0] - 0.05
CERTO_PAUSA_S = 0.5
FOLGA_LINHA_NOVA = 0.15
LINHAS = os.path.join(REPO, "saida", "audio", "fins_de_linha.json")
RECEITA_LINHAS = ("voz ao centro |M|-|S| 1-4 kHz 2048/10 ms; pausas %.0f dB %.2f s, linha a %.0f dB; janela -%.1f/+%.1f s "
                  "de %.1f em %.1f s; juntar %.2f s; votos %d; v1"
                  % (LINHA_PAUSA_DB, LINHA_PAUSA_MIN_S, LINHA_NOVA_DB, LINHA_ANTES, LINHA_DEPOIS, LINHA_PASSO, LINHA_PASSO,
                     LINHA_JUNTAR, LINHA_VOTOS))


def _ler_estereo(caminho):
    """O ficheiro inteiro a 44,1 kHz, estereo, em float64 (como o juncao_creditos.ler)."""
    import numpy as np
    r = subprocess.run([_ffmpeg(), "-v", "error", "-i", caminho, "-ac", "2", "-ar", str(LINHA_SR), "-f", "f32le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def envelope_da_voz(x, de=0.0, passo=0.01):
    """(t, voz) em tramas de 10 ms: a voz ao centro do juncao_creditos.envelope() (|M| - |S| entre 1 e 4 kHz, janela
    de 2048, em dB), feita aos pedacos de 30 s para um ficheiro inteiro caber na memoria. A voz de uma trama so depende
    das amostras dela, por isso os pedacos dao o mesmo que o ficheiro de uma vez."""
    import numpy as np
    n, h = 2048, int(round(passo * LINHA_SR))
    if len(x) < n + h:
        return np.zeros(0), np.zeros(0)
    M, S = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    idx = np.arange(0, len(M) - n, h)
    w = np.hanning(n)
    fr = np.fft.rfftfreq(n, 1.0 / LINHA_SR)
    banda = (fr >= 1000) & (fr <= 4000)
    voz = np.empty(len(idx))
    for a in range(0, len(idx), 3000):
        parte = idx[a:a + 3000]
        FM = np.abs(np.fft.rfft(np.stack([M[i:i + n] for i in parte]) * w, axis=1))[:, banda]
        FS = np.abs(np.fft.rfft(np.stack([S[i:i + n] for i in parte]) * w, axis=1))[:, banda]
        voz[a:a + len(parte)] = 20 * np.log10(np.maximum(np.sqrt(np.sum(np.maximum(FM - FS, 0) ** 2, axis=1)) / (n / 4), 1e-9))
    return de + (idx + n // 2) / LINHA_SR, voz


def pausas_da_voz(t, voz, de, ate):
    """([(inicio, primeiro_sinal, linha_nova, fundo)], nivel): as pausas da voz entre de e ate, a mesma conta do
    juncao_creditos.pausas() (o teste compara as duas). O nivel das linhas e o percentil 80 da voz alisada na janela;
    uma pausa comeca quando ela cai LINHA_PAUSA_DB abaixo e dura LINHA_PAUSA_MIN_S ou mais; o primeiro sinal e onde
    volta a passar esse limiar, e a linha nova onde volta a menos de LINHA_NOVA_DB do nivel."""
    import numpy as np
    j = (t >= de) & (t <= ate)
    if not j.any():
        return [], None
    v = np.convolve(voz, np.ones(5) / 5, mode="same")
    nivel = np.percentile(v[j], 80)
    baixo = (v < nivel - LINHA_PAUSA_DB) & j
    corridas, ini = [], None
    for i in range(len(t)):
        if baixo[i] and ini is None:
            ini = i
        elif not baixo[i] and ini is not None:
            corridas.append([ini, i - 1])
            ini = None
    if ini is not None:
        corridas.append([ini, len(t) - 1])
    juntas = []
    for a, b in corridas:
        if juntas and (t[a] - t[juntas[-1][2]] < 0.06 or v[juntas[-1][2] + 1:a].max() < nivel - LINHA_NOVA_DB):
            juntas[-1][2] = b
        else:
            juntas.append([a, b, b])
    fora = []
    for a, b1, b in juntas:
        if t[b1] - t[a] < LINHA_PAUSA_MIN_S and t[b] - t[a] < LINHA_PAUSA_MIN_S:
            continue
        fora.append((round(float(t[a]), 2), round(float(t[min(b1 + 1, len(t) - 1)]), 2),
                     round(float(t[min(b + 1, len(t) - 1)]), 2), round(float(v[a:b + 1].min() - nivel), 1)))
    return fora, round(float(nivel), 1)


def fins_de_linha_da_voz(t, voz):
    """[[fim, primeiro_sinal, linha_nova, votos], ...]: os fins de linha da voz no ficheiro inteiro, por ordem.

    E o que o juncao_creditos.py diria com o corte em cada meio segundo do ficheiro (a janela de LINHA_ANTES antes a
    LINHA_DEPOIS depois), junto: os achados a menos de LINHA_JUNTAR uns dos outros sao o mesmo fim (o nivel da janela
    muda um pouco o sitio em que a voz passa o limiar), e fica so o que LINHA_VOTOS janelas ou mais acham. De cada um
    fica o que a janela posta nele mesmo diz (a do corte nesse fim), que e o que o juncao diria la."""
    import numpy as np
    if not len(t):
        return []
    achados = []                                     # (fim, sinal, nova, janela)
    s, fim_t = 0.0, float(t[-1])
    while s <= fim_t + LINHA_PASSO:
        de, ate = s - LINHA_ANTES, s + LINHA_DEPOIS
        i0, i1 = int(np.searchsorted(t, de)), int(np.searchsorted(t, ate, side="right"))
        if i1 > i0:
            # SO A JANELA E 3 TRAMAS DE CADA LADO: o alisamento (5 tramas) e o "primeiro instante depois" da pausa veem
            # o mesmo que no ficheiro inteiro, e a conta e a do juncao sem o percorrer todo
            a, b = max(0, i0 - 3), min(len(t), i1 + 3)
            for p in pausas_da_voz(t[a:b], voz[a:b], de, ate)[0]:
                achados.append((p[0], p[1], p[2], s))
        s = round(s + LINHA_PASSO, 6)
    achados.sort()
    grupos, ultimo = [], None
    for x in achados:
        if ultimo is None or x[0] - ultimo > LINHA_JUNTAR + 1e-9:
            grupos.append([])
        grupos[-1].append(x)
        ultimo = x[0]
    fora = []
    for g in grupos:
        votos = len(set(x[3] for x in g))
        if votos < LINHA_VOTOS:
            continue
        melhor = min(g, key=lambda x: (abs(x[3] - x[0]), -sum(1 for y in g if y[0] == x[0]), x[0]))
        fora.append([melhor[0], melhor[1], melhor[2], votos])
    return fora


def fins_de_linha(caminho):
    """Os fins de linha da voz de um ficheiro de musica (fins_de_linha_da_voz), uns 6 s por musica."""
    t, voz = envelope_da_voz(_ler_estereo(caminho))
    return fins_de_linha_da_voz(t, voz)


def _ler_linhas():
    try:
        with open(LINHAS, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and d.get("receita") == RECEITA_LINHAS:
            return d
    except (OSError, ValueError):
        pass
    return {"receita": RECEITA_LINHAS, "musicas": {}}


def linhas_para_a_mesa(nomes, fazer=True, caminhos=None):
    """{ficheiro: [[fim, linha nova], ...]} dos fins de linha da voz das musicas `nomes`, para o window.MUSICA_FIM
    (o primeiro sinal e os votos ficam so no ficheiro guardado: a Mesa nao os usa, e sao uns 20 KB a menos).

    Guardados em saida/audio/fins_de_linha.json (fora do Git) pelo caminho, tamanho e data do original, e medidos
    outra vez so quando um muda (a primeira vez sao uns 6 s por musica). Com fazer=False so le o que esta guardado.
    Le os originais em C:\\casamento-video-media, e so le."""
    import concurrent.futures
    if caminhos is None:
        import montar_da_mesa
        caminhos = montar_da_mesa.caminhos_de_musica()
    guardado = _ler_linhas()
    musicas = guardado["musicas"]
    fora, por_medir = {}, {}
    for f in sorted(set(nomes)):
        c = caminhos.get(f)
        if not c or not os.path.isfile(c):
            continue
        st = os.stat(c)
        chave = os.path.normcase(os.path.abspath(c))
        g = musicas.get(chave)
        if g and g.get("tamanho") == st.st_size and g.get("mtime") == st.st_mtime_ns:
            fora[f] = [[x[0], x[2]] for x in g["linhas"]]
        else:
            por_medir[f] = (chave, c, st)
    if por_medir and fazer:
        print("  frases: %d musicas por medir (os fins de linha da voz, uns 6 s cada)" % len(por_medir))
        with concurrent.futures.ThreadPoolExecutor(4) as ex:
            futuros = {ex.submit(fins_de_linha, c): f for f, (chave, c, st) in por_medir.items()}
            for fut in concurrent.futures.as_completed(futuros):
                f = futuros[fut]
                chave, c, st = por_medir[f]
                try:
                    linhas = fut.result()
                except Exception as erro:          # noqa: BLE001 - uma musica que falha nao para as outras
                    print("  AVISO: nao medi os fins de linha de %s (%s)" % (f, erro))
                    continue
                musicas[chave] = {"ficheiro": f, "tamanho": st.st_size, "mtime": st.st_mtime_ns, "linhas": linhas}
                fora[f] = [[x[0], x[2]] for x in linhas]
        os.makedirs(os.path.dirname(LINHAS), exist_ok=True)
        tmp = LINHAS + ".parte"
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(guardado, fh, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, LINHAS)
    elif por_medir:
        print("  frases: %d musicas sem os fins de linha medidos, e nao os meco aqui" % len(por_medir))
    return fora


def zonas_de_frase(sai, linhas=None, fins=None, frases=None):
    """Os fins de frase da musica que sai, como zonas [{de, ate, fim, tipo, nova}] por ordem, onde o corte esta "no
    fim de uma frase": ver o comentario acima. `linhas` sao os fins de linha da voz desta musica, `fins` as linhas do
    data/fins_de_frase.csv (sai, sai_s, ...; o AUDIO_INFO.fins da Mesa) e `frases` os inicios de frase da 095 desta
    musica [(segundo, forca)], que so contam sem as linhas. A mesma conta do credMusicaZonas() da Mesa."""
    zonas = []
    for r in fins or []:
        if r.get("sai") != sai:
            continue
        s = float(r["sai_s"])
        zonas.append({"de": round(s - CERTO_S, 3), "ate": round(s + CERTO_S, 3), "fim": s, "tipo": "verificada", "nova": None})
    for x in linhas or []:
        # [fim, linha nova] como vai para a Mesa, ou [fim, sinal, nova, votos] como o fins_de_linha() os da
        fim, nova = float(x[0]), float(x[2] if len(x) >= 3 else x[1])
        ate = min(fim + CERTO_PAUSA_S, nova - FOLGA_LINHA_NOVA)
        if ate < fim:
            ate = fim
        if any(z["tipo"] == "verificada" and z["de"] <= fim <= z["ate"] for z in zonas):
            continue
        zonas.append({"de": round(fim - CERTO_ANTES_DA_VOZ, 3), "ate": round(ate, 3), "fim": fim, "tipo": "voz", "nova": nova})
    if not linhas:
        for s, _forca in frases or []:
            s = float(s)
            if any(z["de"] <= s <= z["ate"] for z in zonas):
                continue
            zonas.append({"de": round(s - CERTO_S, 3), "ate": round(s + CERTO_S, 3), "fim": s, "tipo": "batida", "nova": None})
    return sorted(zonas, key=lambda z: (z["fim"], z["tipo"]))


def onde_cai(no_corte, zonas):
    """{certo, depois, antes}: a zona em que o corte cai (None se cai a meio de uma frase), a primeira que acaba depois
    dele e a ultima que acaba antes, com {zona, falta} (quanto falta ao clip para o corte chegar ao fim dessa frase;
    negativo para tras). A mesma conta do credMusicaOndeCai() da Mesa."""
    nc = float(no_corte)
    certo = [z for z in zonas if z["de"] - 1e-6 <= nc <= z["ate"] + 1e-6]
    depois = [z for z in zonas if z["de"] > nc + 1e-6]
    antes = [z for z in zonas if z["ate"] < nc - 1e-6]
    return {"certo": certo[0] if certo else None,
            "depois": {"zona": depois[0], "falta": round(depois[0]["fim"] - nc, 2)} if depois else None,
            "antes": {"zona": antes[-1], "falta": round(antes[-1]["fim"] - nc, 2)} if antes else None}


# --------------------------------------------------------------------------------- a juncao
def _linhas(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def e_ataque(ficheiro, in_s):
    """A entrada esta em data/entradas_ataque.csv (095, 097): entra sem rampa. Como o montar_da_mesa.ataque()."""
    return any(ficheiro.startswith(r["musica"]) and abs(float(in_s) - float(r["in_s"])) < 0.02
               for r in _linhas(ENTRADAS_ATAQUE))


def fim_de_frase(sai, entra, no_corte, entra_in, avisos=None):
    """A linha de data/fins_de_frase.csv desta troca (096), como o montar_da_mesa.escrever_fins_de_frase():
    as duas musicas pelo nome, o segundo do ficheiro da que sai no corte e a entrada da que entra, cada um
    a menos de 0,05 s. Devolve {sai_s, cauda, subida} ou None; avisa se a troca foi medida noutro sitio."""
    iguais = [r for r in _linhas(FINS_DE_FRASE) if r["sai"] == sai and r["entra"] == entra]
    certo = [r for r in iguais if abs(no_corte - float(r["no_corte"])) < 0.05
             and abs(float(entra_in) - float(r["entra_in"])) < 0.05]
    if not certo:
        if iguais and avisos is not None:
            avisos.append("fim de frase por medir outra vez (096): %s para %s chega ao corte aos %.2f s do "
                          "ficheiro, e foi medida aos %s; desce no corte, como antes"
                          % (sai[:30], entra[:30], no_corte, " ou ".join(r["no_corte"] for r in iguais)))
        return None
    r = certo[-1]
    return {"sai_s": float(r["sai_s"]), "cauda": float(r["cauda"]),
            "subida": float(r["subida_entra"]) if (r.get("subida_entra") or "").strip() else None}


def resolver(nome):
    """(nome do ficheiro, caminho) pela procura do montar (resolve_musica), ou (None, None)."""
    import montar_da_mesa
    mus = montar_da_mesa.caminhos_de_musica()
    real = montar_da_mesa.resolve_musica(nome, mus)
    return (real, mus[real]) if real else (None, None)


def faixas_dos_creditos(ultima, pos, antes, dur, escolha, avisos=None, medidas=None, caminho=None):
    """As duas faixas do som do exemplo dos creditos, para o render.construir_som(ff, faixas, antes + dur,
    saida, render.FADE_FIM_SOM). Com a escolha ausente devolve None, e o ponto5 faz o de hoje.

    O relogio e o do exemplo do ponto5: o zero e `antes` segundos antes do fim do filme (o fim do render
    menos o FADE_FIM_IMAGEM), e os creditos comecam em `antes`. `ultima` e a ultima musica do filme
    (C.leitos(...)[-1]) e `pos` o segundo do ficheiro dela no zero do exemplo, os dois do ponto5.
    `medidas` e `caminho` servem para os testes nao lerem a biblioteca.

    A JUNCAO E A DE UMA TROCA NO FILME, com as funcoes do render (som_do_ficheiro e subidas_e_descidas):
    - a que sai toca do zero ate ao corte (`antes`) e mais CRUZAMENTO, e desce nesses 2,2 s; no zero
      sobe em 0,03 s, porque continua o filme no mesmo sitio (como hoje no ponto5);
    - a que entra comeca no corte; sobe em 0,03 s se entra num inicio (render.entra_num_inicio) ou num
      ataque (data/entradas_ataque.csv), senao no tempo em que a outra desce;
    - com a troca medida em data/fins_de_frase.csv (096), a que sai desce no fim da frase e cala-se na
      cauda, e a que entra sobe no tempo da cauda;
    - as duas com curve=qsin, e o loudnorm medido no troco que cada uma toca (087).
    Devolve (faixas, info): info tem in_s, fim, toca, falta, ja_tocou, no_corte e o fim de frase usado.
    """
    import render
    avisos = avisos if avisos is not None else []
    esc, erro = escolha_valida(escolha)
    if erro:
        avisos.append(erro)
    if esc is None:
        return None
    if caminho is None:
        real, caminho = resolver(esc["ficheiro"])
        if not real:
            avisos.append("musica dos creditos nao encontrada, fica como esta: %s" % esc["ficheiro"])
            return None
    else:
        real = esc["ficheiro"]
    m = medidas or medir(caminho)
    e = entrada(esc["inicio"], m["fim"], dur, m["silencios"])
    avisos.extend("musica dos creditos: %s" % a for a in e["avisos"])
    if e["toca"] <= 0.4:
        return None
    repetido, trocos = ja_tocou(real, e["in_s"], e["toca"])
    if repetido > 0.5:
        avisos.append("musica dos creditos: repete %s s do que ja tocou no filme (%s do ficheiro)"
                      % (_segundos(repetido), ", ".join("%s a %s s" % (_segundos(a), _segundos(b)) for a, b in trocos)))
    cruza = render.CRUZAMENTO
    no_corte = round(float(pos) + float(antes), 3)
    sai = dict(ultima)
    for k in ("_subida", "_sai_s", "_cauda", "subida", "descida", "curva"):
        sai.pop(k, None)
    # A MESMA MUSICA NO MESMO SITIO NAO E UMA TROCA: cruzar um ficheiro consigo proprio somava o mesmo som duas
    # vezes. Continua, como o ponto5 faz hoje, ate ao fim dos creditos ou ate se calar.
    if sai["ficheiro"] == real and abs(e["in_s"] - no_corte) < 0.05:
        sai.update({"quando": 0.0, "in_s": float(pos), "dura": float(antes) + e["toca"], "cruza": 0.0,
                    "dura_medida": float(antes) + e["toca"], "subida": render.SUBIDA_NUM_INICIO, "curva": "qsin",
                    "voz": False, "video": False, "abafar": []})
        info = {"ficheiro": real, "in_s": e["in_s"], "pedido": e["pedido"], "fim": m["fim"], "toca": e["toca"],
                "falta": e["falta"], "ja_tocou": repetido, "trocos_repetidos": trocos, "no_corte": no_corte,
                "fim_de_frase": None}
        return [sai], info
    sai.update({"quando": 0.0, "in_s": float(pos), "dura": float(antes) + cruza, "cruza": cruza,
                "dura_medida": float(antes) + cruza, "_subida": render.SUBIDA_NUM_INICIO,
                "voz": False, "video": False, "abafar": []})
    nova = {"ficheiro": real, "caminho": caminho, "quando": float(antes), "in_s": e["in_s"],
            "dura": e["toca"], "dura_medida": e["toca"], "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0,
            "voz": False, "video": False, "abafar": []}
    if e_ataque(real, e["in_s"]):
        nova["_subida"] = render.SUBIDA_NUM_INICIO
    frase = fim_de_frase(sai["ficheiro"], real, no_corte, e["in_s"], avisos)
    if frase:
        sai["_sai_s"], sai["_cauda"] = frase["sai_s"], frase["cauda"]
        if frase["subida"] is not None:
            nova["_subida"] = frase["subida"]
    else:
        avisos.append("musica dos creditos: %s chega ao corte aos %.2f s do ficheiro, sem fim de frase medido "
                      "(096); desce no corte, em %.1f s" % (sai["ficheiro"][:30], no_corte, cruza))
    render.subidas_e_descidas([sai, nova], float(antes) + float(dur))
    info = {"ficheiro": real, "in_s": e["in_s"], "pedido": e["pedido"], "fim": m["fim"], "toca": e["toca"],
            "falta": e["falta"], "ja_tocou": repetido, "trocos_repetidos": trocos, "no_corte": no_corte,
            "fim_de_frase": frase}
    return [sai, nova], info


# --------------------------------------------------------------------------------- teste e linha de comandos
def teste():
    """Os casos da regra, sem ler a biblioteca, e as duas musicas de 2 de outubro em disco."""
    # o fim: o ultimo silencio que chega ao fim; os estalidos juntam-se; sem silencio no fim, a duracao
    assert fim_das_medidas([[0.0, 2.18], [291.814, 296.255]], 296.255) == 291.814
    assert fim_das_medidas([[196.914, 197.567], [197.568, 200.992]], 200.992) == 196.914
    assert fim_das_medidas([[296.758, 297.103], [297.941, 300.698]], 300.698) == 297.941
    assert fim_das_medidas([], 232.385) == 232.385
    assert fim_das_medidas([[8.76, 9.723]], 171.677) == 171.677
    assert fim_das_medidas([[0.0, 1.0], [263.495, 264.684]], 264.69) == 263.495   # a copia mede uns ms a mais
    # o silencio que uma entrada salta, como o montar
    sil = [[0.0, 2.18], [291.814, 296.255]]
    assert silencio_no_inicio_das_medidas(sil, 0.0) == 2.18
    assert silencio_no_inicio_das_medidas(sil, 1.0) == 1.18
    assert silencio_no_inicio_das_medidas(sil, 2.0) == 0.0          # menos de 0,3 s de silencio a partir dele
    assert silencio_no_inicio_das_medidas(sil, 60.8) == 0.0
    assert silencio_no_inicio_das_medidas([[10.0, 40.0]], 10.0) == 0.0   # enche a janela: nao se salta
    # as tres escolhas, com o Taking Care of Business e os creditos de 170,8 s
    e = entrada("inicio", 291.814, 170.8, sil)
    assert e["in_s"] == 2.18 and e["saltou"] == 2.18 and e["falta"] == 0.0, e
    e = entrada("fim", 291.814, 170.8, sil)
    assert e["in_s"] == 121.01 and e["falta"] == 0.0 and not [a for a in e["avisos"] if "silencio" in a], e
    e = entrada(103.0, 291.814, 170.8, sil)
    assert e["in_s"] == 103.0 and e["toca"] == 170.8 and e["falta"] == 0.0, e
    e = entrada(200.0, 291.814, 170.8, sil)
    assert abs(e["falta"] - 79.0) < 0.02 and any("antes do fim dos creditos" in a for a in e["avisos"]), e
    e = entrada("fim", 100.0, 170.8, [])
    assert e["in_s"] == 0.0 and e["falta"] == 70.8 and len(e["avisos"]) == 2, e
    # o que ja tocou no filme: o TCOB toca dos 60,8 aos 103 s no bloco do trabalho
    linhas = [{"ficheiro": "T.mp3", "in_s": "60.8", "dura_s": "42.2"}, {"ficheiro": "Q.mp3", "in_s": "28", "dura_s": "69.5"}]
    assert ja_tocou("T.mp3", 2.18, 170.8, linhas) == (42.2, [(60.8, 103.0)])
    assert ja_tocou("T.mp3", 121.01, 170.8, linhas) == (0.0, [])
    assert ja_tocou("T.mp3", 103.0, 170.8, linhas) == (0.0, [])
    # a escolha: ausente e como esta; mal escrita avisa e e como esta
    assert escolha_valida(None) == (None, None)
    assert escolha_valida({"ficheiro": "x.mp3"})[0] == {"ficheiro": "x.mp3", "inicio": "fim"}
    assert escolha_valida({"ficheiro": "x.mp3", "inicio": "Inicio"})[0]["inicio"] == "inicio"
    assert escolha_valida({"ficheiro": "x.mp3", "inicio": "12,5"})[0]["inicio"] == 12.5
    assert escolha_valida({"ficheiro": "x.mp3", "inicio": "talvez"})[0] is None
    assert escolha_valida({"ficheiro": "x.mp3", "inicio": -3})[0] is None
    assert escolha_valida({"inicio": "fim"})[0] is None
    # um {} e uma escolha sem ficheiro, e avisa (contrato, seccoes 6 e 9); None, "" e 0 sao a ausencia, calada,
    # como o `if(!m)` da Mesa
    for vazia in ({}, [], {"ficheiro": "  "}):
        assert escolha_valida(vazia)[0] is None and "sem ficheiro" in (escolha_valida(vazia)[1] or ""), vazia
    for nada in (None, "", 0, False):
        assert escolha_valida(nada) == (None, None), nada
    # como acaba: uma descida de 7 s e um corte seco
    plano = [-180] * 40
    assert como_acaba_do_perfil(plano + [-200, -250, -300, -350, -400, -450, -500], 47.0) == ("a desvanecer", 6.0)
    assert como_acaba_do_perfil(plano, 40.0)[0] == "seco"
    # o que vai para a Mesa, do indice dela: sem silencios no indice, acaba no fim do ficheiro; as vozes nao contam
    pm = para_a_mesa({"R.mp3": {"tipo": "musica", "duracao": 232.385, "perfil": [-180] * 233},
                      "T.mp3": {"tipo": "musica", "duracao": 296.255, "silencios": sil,
                                "perfil": [-165] * 285 + [-230, -280, -330, -380, -430, -500, -600] + [-700] * 5},
                      "v.mp3": {"tipo": "voz", "duracao": 3.0, "silencios": [[2.0, 3.0]]}})
    assert pm["R.mp3"] == {"fim": 232.385, "acaba": "seco", "desvanece": 0.0}, pm
    assert pm["T.mp3"]["fim"] == 291.814 and pm["T.mp3"]["acaba"] == "a desvanecer", pm
    assert "v.mp3" not in pm
    # a juncao, sem ler a biblioteca: os Queen saem como uma troca do filme, o TCOB entra no corte
    import render
    queen = {"ficheiro": "Q.mp3", "caminho": "nao_existe_q.mp3", "quando": 589.95, "in_s": 28.0, "dura": 69.5,
             "dura_medida": 69.5, "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0, "_subida": 2.2}
    med = {"fim": 291.814, "silencios": sil, "duracao": 296.255}
    av = []
    assert faixas_dos_creditos(queen, 90.0, 5.0, 170.8, None, av, med, "nao_existe_t.mp3") is None and not av
    (q, t), info = faixas_dos_creditos(queen, 90.0, 5.0, 170.8, {"ficheiro": "T.mp3", "inicio": "fim"}, av, med,
                                       "nao_existe_t.mp3")
    assert (q["quando"], q["in_s"], q["dura"], q["cruza"], q["subida"], q["curva"]) == \
        (0.0, 90.0, 5.0 + render.CRUZAMENTO, render.CRUZAMENTO, render.SUBIDA_NUM_INICIO, "qsin"), q
    assert (t["quando"], t["in_s"], t["dura"], t["subida"], t["curva"]) == (5.0, 121.01, 170.8, render.CRUZAMENTO, "qsin"), t
    assert info["no_corte"] == 95.0 and info["ja_tocou"] == 0.0 and info["fim_de_frase"] is None
    assert any("sem fim de frase medido" in a for a in av), av
    (q, t), info = faixas_dos_creditos(queen, 90.0, 5.0, 170.8, {"ficheiro": "T.mp3", "inicio": 0}, [], dict(med, silencios=[]),
                                       "nao_existe_t.mp3")
    assert t["in_s"] == 0.0 and t["subida"] == render.SUBIDA_NUM_INICIO, t      # num inicio: sem rampa (094)
    # os Queen escolhidos no sitio onde o filme os deixa: continuam, sem se cruzarem consigo proprios
    (q,), info = faixas_dos_creditos(queen, 90.0, 5.0, 170.8, {"ficheiro": "Q.mp3", "inicio": 95.0}, [],
                                     {"fim": 239.34, "silencios": [], "duracao": 245.55}, "nao_existe_q.mp3")
    assert (q["in_s"], round(q["dura"], 2), q["cruza"]) == (90.0, 149.34, 0.0) and info["falta"] == 26.46, (q, info)
    # com o fim de frase medido (096): os Queen calam-se na cauda e o TCOB sobe no mesmo tempo
    global fim_de_frase
    original = fim_de_frase
    fim_de_frase = lambda *a, **k: {"sai_s": 95.0, "cauda": 0.3, "subida": None}   # noqa: E731
    try:
        (q, t), info = faixas_dos_creditos(queen, 90.0, 5.0, 170.8, {"ficheiro": "T.mp3", "inicio": "fim"}, [], med,
                                           "nao_existe_t.mp3")
    finally:
        fim_de_frase = original
    assert (round(q["dura"], 3), q["descida"], q["cruza"], t["subida"]) == (5.3, 0.3, 0.0, 0.3), (q, t)
    # o silencio e o do projeto
    import montar_da_mesa
    import audio_para_mesa
    assert montar_da_mesa.SILENCIO_DB == SILENCIO_DB == audio_para_mesa.SILENCIO_DB, "o silencio mudou no projeto"
    assert audio_para_mesa.SILENCIO_MIN == SILENCIO_MIN and montar_da_mesa.JANELA_SILENCIO == JANELA_SILENCIO
    # as duas musicas de 2 de outubro, em disco
    for nome, fim_esperado in (("Bachman Turner Overdrive-Taking care of business_62s.mp3", 291.814),
                               ("Queen - Friends Will Be Friends (Lyrics).mp3", 239.34)):
        real, caminho = resolver(nome)
        if not real:
            print("  (sem %s em disco: so os casos puros)" % nome)
            continue
        m = medir(caminho)
        assert abs(m["fim"] - fim_esperado) < 0.01, (nome, m["fim"])
    print("musica_creditos: teste ok")


def main():
    if "--teste" in sys.argv:
        teste()
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dur = 170.8
    if "--creditos" in sys.argv:
        dur = float(sys.argv[sys.argv.index("--creditos") + 1])
        args = [a for a in args if a != sys.argv[sys.argv.index("--creditos") + 1]]
    if not args:
        raise SystemExit(__doc__)
    real, caminho = resolver(args[0])
    if not real:
        raise SystemExit("Nao encontrei a musica %r" % args[0])
    m = medir(caminho)
    print("%s: %.2f s no ficheiro, cala-se aos %.2f s" % (real, m["duracao"], m["fim"]))
    escolhas = [args[1]] if len(args) > 1 else ["inicio", "fim"]
    for x in escolhas:
        esc, erro = escolha_valida({"ficheiro": real, "inicio": x})
        if erro:
            print("  " + erro)
            continue
        e = entrada(esc["inicio"], m["fim"], dur, m["silencios"])
        rep, trocos = ja_tocou(real, e["in_s"], e["toca"])
        perto = frase_mais_perto(real, e["in_s"])
        print("  %-7s entra aos %6.2f s, toca %.1f de %.1f s; ja tocou no filme %.1f s%s%s"
              % (x, e["in_s"], e["toca"], dur, rep, (" %s" % trocos) if trocos else "",
                 ("; frase medida mais perto aos %.2f s (forca %.2f)" % perto) if perto else ""))
        for a in e["avisos"]:
            print("     " + a)


if __name__ == "__main__":
    main()
