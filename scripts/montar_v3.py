# -*- coding: utf-8 -*-
"""Constroi a abertura da v3, ponto a ponto como o Tiago pediu.

ISTO E A ABERTURA, NAO A v3 INTEIRA. O corpo cronologico de 1995 ate hoje ainda
nao tem ordem decidida, e quem a decide e ele, na Mesa de Montagem.

O QUE ELE PEDIU, ponto a ponto:

  1. "Troca o video da paramout pelo novo que meti na pasta trabalho"
        -> "20th Century Fox Intro HD.mp4", 1280x534, contra 480x360 do antigo.

  2. "um video parecido com o que anexei com algumas fotos"
        -> scripts/intro_flipbook.py, que entra aqui como segundo video.

  3. "quando estamos a andar para tras e como se fizessemos um rewind"
        -> linha_tempo.anos, fita pela ordem do tempo com rasto de movimento.

  4. "o movimento nao esta natural na passagem da timeline por anos para a
      timeline por meses"
        -> linha_tempo.meses entra com um zoom da escala do ano para a do mes.

  5. "Comeca na data do pedido de casamento com as fotos que tens e com a
      musica Lang Lang" / "a timeline ... com o som de timeline a mexer"
        -> Lang Lang desde o pedido; som de rebobinar por cima da fita. O Rei
           Leao deixou de comecar no principio: so entra depois dos foguetes
           do Tiago, que era a queixa dele.

  6. "Depois aparece qualquer coisa como, mas como e que chegamos aqui"

  7. "este ano estava destinado para ser importantissimo para o futuro da
      humanidade"

  8. "quando ja so faltavam ~30% do ano acontece o nascimento do Tiago. A banda
      sonora ja sabes qual e. E depois passa para o rei leao."

  9. "o dia 24 foi cheio de acontecimentos [tom humoristico] a situacao do vale
      do Coa a tentar ficar com o protagonismo, mas a Clara nasce e rouba o
      spotlight"
        -> Nao foi preciso escrever a piada. O Coa e a Clara caem os DOIS a 24
           de novembro, portanto partilham o mesmo ponto da fita: a etiqueta
           troca de "Salvam-se as gravuras do Coa" para "Nasce a Clara" sem a
           fita se mexer um milimetro. A piada conta-se sozinha.

  "Antes de elas comecarem a aparecer da tempo para os foguetes terminarem"
        -> o cartao da data entre o nascimento e as fotografias tem a duracao
           CALCULADA para os foguetes acabarem primeiro. Se as duracoes dos
           clips mudarem, o calculo acompanha sozinho.

  "Nao meteste as fotos todas que tinha metido no Tiago em bebe"
        -> quatro de cada, pela ordem e com as legendas da mae da Clara.

AS DATAS, as duas confirmadas pelo Tiago:

    Tiago .... 12 de setembro de 1995
    Clara .... 24 de novembro de 1995

A da Clara comecou por ser uma conta minha a partir do "dois meses e doze dias
depois" que ele escreveu. Ficou em espera ate ele a confirmar, e confirmou em
12/09/2026: "sim e isso mesmo. a data dela". So a partir dai e que foi tratada
como facto, porque vai escrita num cartao e num marco da fita a frente das duas
familias, e uma data errada num casamento nao se desfaz.

E daqui sai a coincidencia que faz a piada do dia 24 funcionar sem ser escrita:
a Clara nasce no MESMO DIA em que se salvaram as gravuras do Coa.

Uso:  py -3.11 scripts/montar_v3.py
      py -3.11 scripts/render.py v3
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linha_tempo

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")
DESTINO = os.path.join(REPO, "data", "montagens")
MEDIA = "C:/casamento-video-media/trabalho"
GERADOS = "C:/casamento-video-media/gerados"

CROSSFADE = 0.7

COLUNAS = ["ordem", "id", "tipo", "seccao", "ficheiro", "duracao_s",
           "transicao_s", "inicio_s", "fim_s", "dominante_s", "solo_s",
           "movimento", "texto_ecra", "tratamento", "duracao_original_s",
           "variacao_pct", "fonte_imagem", "nota"]
COLUNAS_SOM = ["ficheiro", "caminho", "quando_s", "in_s", "dura_s", "ganho", "nota"]

VINHETA = "Candidato a vereador.mp3"
VINHETA_IN = 173.7          # 2:53,7, o instante exato que ela escolheu
VINHETA_DURA = 7.5

LANG_LANG = "Lang Lang - Beauty and the Beast (From Lang Lang Plays Disney  Live).mp3"
REI_LEAO = "Rei_Leão_Ciclo Sem FimNants’ Ingonyama.mp3"
CLARA_MUS = "Ana Faria - Clara.mp3"
CLARA_MUS_IN = 6.0          # o instante que a mae dela escolheu
REBOBINAR = "rebobinar.wav"
FITA_ANDAR = "fita_a_andar.wav"

# AS IMAGENS DAS MARCAS.
#
# As que existem entram; as que nao existem ficam so com palavras, sem erro e
# sem render a abortar. O Tiago pediu "inclui tambem imagens de kobe schengen e
# guterres" e ainda nao as largou, portanto os nomes ficam ja escritos: basta
# pos-los em 01-NOVAS com estes nomes exatos e correr o inventario.
ACONTECIMENTOS = (
    "17/01 Terramoto em Kobe, Japão @kobe.jpg;"
    "26/03 Abrem as fronteiras de Schengen @schengen.jpg;"
    "24/08 Sai o Windows 95 @Windows95.jpeg;"
    "04/09 Nasce o SAPO, em Aveiro @sapo_42c89ed355959aa80b08ddd3b3b79ffc3555d337.jpg;"
    "*12/09 Nasce o Tiago;"
    "01/10 Guterres ganha as eleições @guterres.jpg;"
    "24/11 Salvam-se as gravuras do Côa @coa.jpg;"
    "*24/11 Nasce a Clara"
)


def fr(dia, mes):
    return ((mes - 1) + (dia - 1) / 31.0) / 12.0


F_SAPO = fr(4, 9)
F_TIAGO = fr(12, 9)
F_CLARA = fr(24, 11)
N = 0.004                   # folga para nao repetir a marca da fronteira

BEBE_TIAGO = [("21-46.jpg", "Foi o segundo filho"),
              ("21-47.jpg", "E era amoroso"),
              ("21-48.jpg", "Com a mãe, o mano e as primas"),
              ("21-49.jpg", "E com o pai")]
BEBE_CLARA = [("1 (2).jpg", "E chamar-se-ia Clara"),
              ("2.jpg", "Era muito bem disposta"),
              ("5 (2).jpg", ""),
              ("6.jpg", "Muito curiosa")]

DUR_MARCOS_A = 15.0
DUR_MARCOS_TIAGO = 11.0
DUR_MARCOS_CLARA = 14.0

ESPEC_ANOS = "2026>1995|2026=4 de outubro de 2026"
ESPEC_A = "1995@0-%.6f|%s" % (F_SAPO, ACONTECIMENTOS)
ESPEC_TIAGO = "1995@%.6f-%.6fc|%s" % (F_SAPO + N, F_TIAGO, ACONTECIMENTOS)
ESPEC_CLARA = "1995@%.6f-%.6f|%s" % (F_TIAGO + N, F_CLARA, ACONTECIMENTOS)


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


def quando_acende(espec, duracao):
    """Instante, dentro do clip, em que a marca grande acende.

    Perguntado a propria linha do tempo. E a unica maneira de os foguetes nao
    se desalinharem quando as duracoes dos clips mudarem.
    """
    ano, marcas, troco, abre = linha_tempo.ler_meses(espec)
    dentro = [m for m in marcas
              if troco[0] - 1e-4 <= fr(m[0], m[1]) <= troco[1] + 1e-4]
    passos = []
    if not dentro or abs(fr(dentro[0][0], dentro[0][1]) - troco[0]) > 1e-4:
        passos.append(None)
    passos += dentro
    if not dentro or abs(fr(dentro[-1][0], dentro[-1][1]) - troco[1]) > 1e-4:
        passos.append(None)
    for i, m in enumerate(passos):
        if m and m[3]:
            return linha_tempo.inicio_da_paragem(
                i, len(passos), 0.70, parar_no_primeiro=abre) * duracao
    return duracao


ACENDE_TIAGO = quando_acende(ESPEC_TIAGO, DUR_MARCOS_TIAGO)
ACENDE_CLARA = quando_acende(ESPEC_CLARA, DUR_MARCOS_CLARA)


def respiro(dur_clip, acende):
    """Quanto tem de durar o cartao da data para os foguetes acabarem primeiro.

    O CROSSFADE TEM DE ENTRAR NA CONTA. A primeira versao somava so a duracao
    dos foguetes mais meio segundo, e as fotografias do bebe apareciam 0,9 s
    antes de os foguetes terminarem: o clip seguinte comeca 0,7 s antes de o
    cartao acabar, porque e isso que um encadeado faz.
    """
    ja_tocou = dur_clip - acende
    return max(2.6, VINHETA_DURA + 0.6 + CROSSFADE - ja_tocou)


RESPIRO_TIAGO = respiro(DUR_MARCOS_TIAGO, ACENDE_TIAGO)
RESPIRO_CLARA = respiro(DUR_MARCOS_CLARA, ACENDE_CLARA)

CLIPS = (
    [("video", "20th Century Fox Intro HD.mp4", 20.8, "", "fiel", 0.0),
     ("video", "intro_clara_tiago.mp4", 13.4, "", "fiel", 0.0),

     ("foto", "2025_Pedido_casamento_clara_1.jpg", 4.4, "Natal de 2025", "fundo", 0.0),
     ("foto", "2025_Pedido_casamento_clara_4.jpg", 3.8, "", "fundo", CROSSFADE),
     ("foto", "IMG_2067.jpeg", 5.2, "Ela disse que sim", "fundo", CROSSFADE),

     ("cartao", "", 4.2, "Mas como é que chegámos aqui?", "fiel", CROSSFADE),
     ("contador", "", 13.0, ESPEC_ANOS, "fiel", CROSSFADE),
     ("cartao", "", 4.4, "1995 prometia ser um ano importante", "fiel", CROSSFADE),

     ("marcos", "", DUR_MARCOS_A, ESPEC_A, "fiel", CROSSFADE),
     # CORTE SECO, nao encadeado: a fita continua onde estava e um encadeado
     # entre duas imagens quase iguais so produz fantasmas. Foi o "efeito
     # estranho apos o abre a sapo em aveiro".
     ("marcos", "", DUR_MARCOS_TIAGO, ESPEC_TIAGO, "fiel", 0.0),
     ("cartao", "", RESPIRO_TIAGO, "12 de setembro de 1995", "fiel", CROSSFADE)]
    + [("foto", f, 4.2, t, "fundo", CROSSFADE) for f, t in BEBE_TIAGO]
    + [("cartao", "", 4.2, "O ano ainda tinha surpresas", "fiel", CROSSFADE),
       ("marcos", "", DUR_MARCOS_CLARA, ESPEC_CLARA, "fiel", CROSSFADE),
       ("cartao", "", RESPIRO_CLARA, "24 de novembro de 1995", "fiel", CROSSFADE)]
    + [("foto", f, 4.2, t, "fundo", CROSSFADE) for f, t in BEBE_CLARA]
)


def main():
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        por_nome = {r["ficheiro"].lower(): r for r in csv.DictReader(fh)}

    linhas, cursor, faltam = [], 0.0, []
    for tipo, ficheiro, dur, texto, trat, trans in CLIPS:
        ident = ""
        if tipo == "foto":
            r = por_nome.get(ficheiro.lower())
            if not r:
                faltam.append(ficheiro)
                continue
            ident = r["id"]
        t = trans if linhas else 0.0
        inicio = cursor - t if linhas else 0.0
        fim = inicio + dur
        cursor = fim
        linhas.append({
            "ordem": len(linhas) + 1, "id": ident, "tipo": tipo,
            "seccao": "v3 abertura", "ficheiro": ficheiro,
            "duracao_s": round(dur, 2), "transicao_s": round(t, 2),
            "inicio_s": round(inicio, 2), "fim_s": round(fim, 2),
            "dominante_s": round(dur - t, 2), "solo_s": round(dur - 2 * t, 2),
            "movimento": ("Nenhum" if tipo in ("contador", "marcos", "video")
                          else "Zoom in"),
            "texto_ecra": texto, "tratamento": trat,
            "duracao_original_s": "", "variacao_pct": "",
            "fonte_imagem": "", "nota": "",
        })

    caminho = os.path.join(DESTINO, "v3.csv")
    with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    # ------------------------------------------------------------------ som
    mus = caminhos_de_musica()
    corpo = [l for l in linhas if l["tipo"] != "video"]
    desvio = corpo[0]["inicio_s"]
    fim_corpo = max(l["fim_s"] for l in corpo) - desvio

    def quando(tipo, marca):
        for l in linhas:
            if l["tipo"] == tipo and marca in (l["texto_ecra"], l["ficheiro"]):
                return l["inicio_s"] - desvio
        return 0.0

    t_contador = quando("contador", ESPEC_ANOS)
    t_tiago = quando("marcos", ESPEC_TIAGO) + ACENDE_TIAGO
    t_clara = quando("marcos", ESPEC_CLARA) + ACENDE_CLARA

    faixas = []

    def junta(nome, inicio, dura, ganho, nota, dentro=0.0):
        if dura <= 0.4:
            return
        if not mus.get(nome):
            print("  MUSICA EM FALTA: %s" % nome)
            return
        faixas.append({"ficheiro": nome, "caminho": mus[nome],
                       "quando_s": round(max(0.0, inicio), 2), "in_s": dentro,
                       "dura_s": round(dura, 2), "ganho": ganho, "nota": nota})

    # Do pedido ate aos foguetes do Tiago. O som de rebobinar vem POR CIMA da
    # musica, nao no lugar dela: cortar aqui deixava um buraco por baixo da fita.
    # O Lang Lang entra 5 s adiante do inicio da gravacao, a pedido do Tiago:
    # "mete o som do lang em vez de comecar no inicio a comecar 5s mais a frente".
    junta(LANG_LANG, 0.0, t_tiago, 1.0,
          "do pedido ate ao nascimento do Tiago, a partir dos 5 s da gravacao", 5.0)
    # O SOM SO ENQUANTO A FITA ANDA. Antes comecava no inicio do clip e a fita
    # ficava os primeiros quatro segundos parada em 2026, portanto ouvia-se
    # rebobinar sem nada a mexer.
    _de, _para, _marcos = linha_tempo.ler_anos(ESPEC_ANOS)
    mexe_de, mexe_ate = linha_tempo.janela_de_movimento(_de, _para, _marcos, 13.0)
    junta(REBOBINAR, t_contador + mexe_de - 0.25, (mexe_ate - mexe_de) + 0.7, 1.15,
          "fita a rebobinar, so enquanto a fita anda (%.1f a %.1f s do clip)"
          % (mexe_de, mexe_ate))
    junta(VINHETA, t_tiago, VINHETA_DURA, 2.0, "foguetes, nascimento do Tiago", VINHETA_IN)
    # O REI LEAO ACABA QUANDO A FITA VOLTA.
    #
    # O Tiago: "estou na duvida se deviamos manter o rei leao quando volta a
    # timeline apos o Tiago". A minha leitura, e e uma proposta que ele pode
    # virar numa linha: o Rei Leao pertence ao nascimento e as fotografias do
    # bebe. Por cima de uma fita a marcar eleicoes legislativas e a barragem do
    # Coa, aquilo soa a trailer e nao a memoria. Acaba no cartao que anuncia o
    # regresso a fita, e por baixo da fita fica o som dela a andar.
    t_volta = quando("cartao", "O ano ainda tinha surpresas")
    junta(REI_LEAO, t_tiago + VINHETA_DURA - 1.0,
          t_volta - (t_tiago + VINHETA_DURA - 1.0) + 1.2, 1.05,
          "Rei Leão, do nascimento do Tiago ate a fita voltar")

    # A fita dos meses anda para a FRENTE, portanto nao leva o som de rebobinar.
    # Leva um som proprio, mais calmo e sem o matraquear da rebobinagem.
    t_fita2 = quando("marcos", ESPEC_CLARA)
    ano_c, marcas_c, troco_c, abre_c = linha_tempo.ler_meses(ESPEC_CLARA)
    junta(FITA_ANDAR, t_fita2, t_clara - t_fita2 + 0.6, 0.85,
          "som da fita a andar, por baixo da segunda linha do tempo")
    junta(VINHETA, t_clara, VINHETA_DURA, 2.0, "foguetes, nascimento da Clara", VINHETA_IN)
    junta(CLARA_MUS, t_clara + VINHETA_DURA - 1.0,
          fim_corpo - (t_clara + VINHETA_DURA - 1.0), 1.0,
          "a musica que a mae da Clara pos para ela", CLARA_MUS_IN)

    with open(os.path.join(DESTINO, "v3.som.csv"), "w",
              encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_SOM)
        w.writeheader()
        w.writerows(faixas)

    total = max(l["fim_s"] for l in linhas)
    print("v3, abertura")
    print("  clips: %d    duracao: %d:%02d" % (len(linhas), int(total) // 60, int(total) % 60))
    for l in linhas:
        rot = l["ficheiro"] or l["texto_ecra"]
        print("   %2d  %-9s %6.1f-%6.1f  %s"
              % (l["ordem"], l["tipo"], l["inicio_s"], l["fim_s"], rot[:54]))
    print()
    print("  Nascimento do Tiago acende a %.1f s do corpo; a Clara a %.1f s." % (t_tiago, t_clara))
    print("  Respiro para os foguetes: %.1f s no Tiago, %.1f s na Clara."
          % (RESPIRO_TIAGO, RESPIRO_CLARA))
    print()
    print("  som: %d faixas" % len(faixas))
    for f in faixas:
        print("   %6.1fs  dura %5.1fs  x%.2f  %-38s %s"
              % (f["quando_s"], f["dura_s"], f["ganho"], f["ficheiro"][:38], f["nota"]))
    if faltam:
        print()
        print("  NAO ENCONTREI: %s" % ", ".join(faltam))
    print()
    print("Escrito: %s" % caminho)


if __name__ == "__main__":
    main()
