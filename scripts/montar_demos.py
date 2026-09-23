# -*- coding: utf-8 -*-
"""Constroi montagens curtas para demonstrar cada versao em discussao.

Nao sao versoes, sao DEMONSTRACOES. Cada uma pega num troco pequeno de
material real e mostra a ideia da versao, para se decidir a olhar em vez de a
discutir. A v1a ja foi renderizada por inteiro noutro sitio e serve de termo
de comparacao.

  v1b   a v1a mais dois tratamentos: fundo desfocado nas verticais e rajada
        nas corridas de fotos do mesmo assunto
  v1c   a v1b mais uma correcao narrativa, o encadeamento numero 1 do
        docs/ENCADEAMENTOS.md, os caes dela, o cao dele, a cadela dos dois
  v2    o funil do briefing: intercalado por idade em vez de uma vida de cada
        vez
  v3    o flash-forward: comeca no pedido de casamento e corta para o berco

Uso:  py -3.11 scripts/montar_demos.py
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
DESTINO = os.path.join(REPO, "data", "montagens")

# 11/09/2026: o Tiago viu a demo e disse "as fotos dos desportos estao a mudar
# muito muito rapido, aumenta a velocidade em 25% para testar". Fotos a mudar
# depressa de mais pedem MAIS tempo, portanto o que se aumenta e a duracao:
# 0,45 -> 0,5625, ou seja 14 fotogramas em vez de 11. Fica dito de forma
# explicita porque a frase, a letra, diz o contrario do efeito pretendido.
CROSSFADE = 0.7
TIMELINE = os.path.join(REPO, "data", "original_mae.csv")


# ---------------------------------------------------------------- banda sonora
#
# As quatro demos sairam MUDAS, e o Tiago viu logo: "Em todos os demos esta a
# faltar a banda sonora". A causa: o render tira a musica da timeline da mae da
# Clara, ancorada a foto sobre a qual ela a tinha posto. Numa demo de 30
# segundos, feita de fotos escolhidas a mao, nao ha nada a que ancorar, e o
# resultado e silencio sem uma linha de aviso.
#
# Passa a haver um ficheiro de som por montagem, <nome>.som.csv. O render usa-o
# quando existe, e so volta a ancorar a timeline dela quando nao existe (que e
# o caso da v1a, onde ancorar e precisamente o que se quer).
#
# DUAS MARCAS DELA QUE SE MANTEM, porque o Tiago pediu por elas:
#   - a fanfarra de estudio a abrir, que e video e traz o seu proprio som
#   - o troco de "Candidato a vereador" a partir de 2:53 por cima de cada
#     cartao de anuncio. Ela usou-o duas vezes, identico, nos dois nascimentos.
VINHETA = "Candidato a vereador.mp3"
VINHETA_IN = 173.7          # 2:53,7, o instante exato que ela escolheu
VINHETA_DURA = 6.5

COLUNAS_SOM = ["ficheiro", "caminho", "quando_s", "in_s", "dura_s", "ganho", "nota"]


def caminhos_de_musica():
    """Nome do ficheiro -> caminho em disco, tirado da timeline dela."""
    with open(TIMELINE, encoding="utf-8-sig", newline="") as fh:
        return {r["ficheiro"]: r["caminho_disco"]
                for r in csv.DictReader(fh) if r["faixa"] == "musica"}


def escrever_som(nome, demo, linhas):
    """Escreve <nome>.som.csv: uma faixa de fundo e a vinheta sobre os cartoes."""
    mus = caminhos_de_musica()
    fim = max(float(l["fim_s"]) for l in linhas)
    faixas = []

    # Uma faixa, ou varias com mudanca a meio. A regra do CLAUDE.md e que cada
    # mudanca de faixa coincide com mudanca de bloco, e o verificador apanhou
    # que a corrente dos caes atravessa do bloco dela para o dele sem mudar de
    # musica. Com duas faixas, a passagem ouve-se.
    lista = demo.get("musicas")
    if not lista and demo.get("musica"):
        lista = [(demo["musica"], demo.get("musica_in", 0.0), 0.0)]
    for i, (nome_m, ini_m, quando_m) in enumerate(lista or []):
        if not mus.get(nome_m):
            continue
        seguinte = lista[i + 1][2] if i + 1 < len(lista) else fim
        faixas.append({"ficheiro": nome_m, "caminho": mus[nome_m],
                       "quando_s": round(quando_m, 2), "in_s": ini_m,
                       "dura_s": round(min(seguinte, fim) - quando_m, 2),
                       "ganho": 1.0, "nota": "fundo da demo"})

    # A vinheta dela por cima de cada cartao. Mais alta do que o fundo, porque
    # e ela que marca a mudanca de bloco: e esse o efeito no original.
    if mus.get(VINHETA):
        # SO NO PRIMEIRO CARTAO. Ela usou este troco duas vezes no video todo,
        # nos dois cartoes "Era uma vez", que anunciam o inicio de cada vida.
        # Po-lo em cima de todos os cartoes transformava uma marca rara num
        # tique, e gastava exatamente aquilo que lhe da forca.
        cartoes = [l for l in linhas if l["tipo"] == "cartao"]
        for l in cartoes[:1]:
            faixas.append({"ficheiro": VINHETA, "caminho": mus[VINHETA],
                           "quando_s": round(float(l["inicio_s"]), 2),
                           "in_s": VINHETA_IN,
                           "dura_s": min(VINHETA_DURA, round(fim - float(l["inicio_s"]), 2)),
                           "ganho": 1.0, "nota": "vinheta dela sobre o cartao"})

    caminho = os.path.join(DESTINO, nome + ".som.csv")
    with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_SOM)
        w.writeheader()
        for f in faixas:
            w.writerow(f)
    return len(faixas)


COLUNAS = ["ordem", "id", "tipo", "seccao", "ficheiro", "duracao_s",
           "transicao_s", "inicio_s", "fim_s", "dominante_s", "solo_s",
           "movimento", "texto_ecra", "tratamento", "duracao_original_s",
           "variacao_pct", "fonte_imagem", "nota"]

# (ficheiro ou None para cartao, duracao, texto, tratamento, transicao)
DEMOS = {
    "v1b": {
        "musica": "OS TRIBALISTAS - VELHA INFÂNCIA (INSTRUMENTAL).MP3",
        "musica_in": 6.0,
        "clips": [
            ("20260623_201228.jpg", 4.4, "No Mundial de futebol 2026", "fundo", 0),
            ("9-24-7.JPG", 4.4, "Numa viagem de comboio, em ferias", "fundo", CROSSFADE),
            ("IMG_4477.JPG", 4.4, "Ferias 2026", "fundo", CROSSFADE),
            ("21-38.jpg", 0.5625, "Caminhadas pelo Parque das Serras do Porto", "rajada", 0),
            ("21-39.jpg", 0.5625, "", "rajada", 0),
            ("21-41.JPG", 0.5625, "", "rajada", 0),
            ("21-42.JPG", 0.5625, "", "rajada", 0),
            ("21-43.JPG", 0.5625, "", "rajada", 0),
            ("21-44.JPG", 0.5625, "", "rajada", 0),
            ("21-45.JPG", 0.5625, "", "rajada", 0),
            ("9-24-2.JPG", 0.5625, "", "rajada", 0),
            (None, 3.6, "Familia", "fiel", CROSSFADE),
            ("10-1 (2).jpg", 4.4, "Com o pai. Era pequenina e ja lhe dava ouras", "fundo", CROSSFADE),
            ("10-2.jpg", 4.4, "", "fundo", CROSSFADE),
        ],
    },
    "v1c": {
        # CORRENTE DOS CAES, com as correcoes do verificador e os dois factos
        # que o Tiago confirmou em 11/09/2026:
        #   a Sky e da MAE DELE, e a Sky veio DEPOIS da Mia.
        # E isso que permite o ultimo ecra existir. Sem esses dois factos ele
        # afirmava um parentesco por conta propria a frente das duas familias.
        #
        # Cortada face a primeira proposta: a 9-29, que e a mesma ocorrencia da
        # 9-28 dois segundos depois. Oito fotos seguidas de animais passavam o
        # limite de 4 a 5 do CLAUDE.md.
        #
        # A musica muda na foto da praia, que e onde a corrente passa do lado
        # dela para o lado dos dois. Mudanca de faixa em mudanca de bloco.
        #
        # OS DOIS ULTIMOS ECRAS SAO PALAVRAS DELA, nao minhas. Ela escreveu
        # "E com a Sky" por baixo da 21-49-54 e "Com a mae e com a avo" por
        # baixo da 21-49-53. Estao hoje aos 13:37 e aos 13:41, dentro do cartao
        # "Colegas de trabalho", a onze minutos das fotos dos caes dela. Postas
        # aqui, a corrente fecha-se com a letra dela e eu nao afirmo nada.
        #
        # A 21-49-55 foi posta de lado apesar de mostrar a mesma senhora: a
        # 21-49-53 mostra TRES geracoes com o mesmo cao, mae, avo e ele, e e
        # a unica que a propria mae da Clara legendou a dizer quem sao.
        #
        # ERRO MEU, corrigido pelo Tiago em 11/09/2026: eu disse que a senhora
        # de cabelo grisalho e oculos vermelhos da 21-49-54 nao era a mesma da
        # 21-49-53 e da 21-49-55. E a mesma pessoa, e e a mae dele. Mudou o
        # cabelo entre as fotos. Fica escrito porque eu afirmei o contrario com
        # confianca depois de "verificar", e o que eu verifiquei foi a cor do
        # cabelo, nao a pessoa.
        #
        # REGRA QUE SAI DAQUI: nao identificar nem distinguir pessoas a partir
        # de fotografias. Quem sabe quem e que esta nas fotos e o Tiago.
        "musicas": [("Ana Faria - Clara.mp3", 8.0, 0.0),
                    ("Tiago Celebration Song (Reggae).mp3", 0.8, 17.4)],
        "clips": [
            ("9-25.jpg", 4.2, "Gostava dos bichinhos todos", "fundo", 0),
            ("Scanner_20260814.jpg", 4.5, "E desde sempre apaixonada por caes",
             "fundo", CROSSFADE),
            ("9-27.JPG", 4.2, "Pelos dela...", "fundo", CROSSFADE),
            ("9-28.JPG", 4.0, "... e pelos dos outros", "fundo", 0),
            ("2014_Clara_Tiago_Praia_Mia_cadela_clara.jpg", 5.4, "A Mia", "fiel",
             CROSSFADE),
            ("21-49-54.jpg", 4.6, "E com a Sky", "fundo", CROSSFADE),
            ("21-49-53.jpg", 6.0, "Com a mae e com a avo", "fundo", CROSSFADE),
        ],
    },
    "v2": {
        # O FUNIL COM NARRACAO. O achado desta versao nao e meu nem do modelo,
        # e da mae da Clara: ela escreveu "Com o pai" por baixo de um bebe da
        # Clara ao colo do pai, e "E com o pai" por baixo de um bebe do Tiago
        # ao colo do pai. As duas legendas estao hoje a quatro minutos e meio
        # de distancia e ninguem as ve como par. Postas seguidas, a ponte
        # faz-se sozinha e nao precisa de uma unica palavra nova.
        #
        # Os dois cartoes "Era uma vez" dela NAO sao fundidos num so. A
        # proposta inicial juntava-os para poupar tempo, e isso apagava uma
        # marca de assinatura protegida pela decisao 001.
        "musica": "OS TRIBALISTAS - VELHA INFÂNCIA (INSTRUMENTAL).MP3",
        "musica_in": 0.0,
        "clips": [
            (None, 3.6, "1995", "fiel", 0),
            ("21-46.jpg", 4.4, "Nasce o segundo filho", "fundo", CROSSFADE),
            ("21-47.jpg", 3.8, "Tiago", "fundo", CROSSFADE),
            (None, 3.8, "Dois meses e doze dias depois", "fiel", CROSSFADE),
            ("1 (2).jpg", 4.4, "A poucos quilometros, a Clara", "fundo", CROSSFADE),
            ("2.jpg", 3.6, "", "fundo", CROSSFADE),
            ("10-1 (2).jpg", 4.8, "Com o pai", "fundo", CROSSFADE),
            ("21-49.jpg", 5.0, "E com o pai", "fundo", CROSSFADE),
            (None, 4.0, "Ainda nao se conheciam", "fiel", CROSSFADE),
        ],
    },
    "v3": {
        # O FLASH-FORWARD, agora com a timeline a fugir que o Tiago pediu. O
        # contador e desenhado fotograma a fotograma (ver render.contador) e e
        # o primeiro clip do projeto cujo conteudo depende do instante.
        #
        # O pedido fica em TRES fotos, como ele mandou: o bilhete de Feliz
        # Natal, o interior da caixa, e o anel com a arvore. A quarta e a do
        # anuncio saem.
        "musica": "Papillon - ¡ N.M.N ! (feat. Bárbara Tinoco) [1].MP3",
        "musica_in": 0.0,
        "clips": [
            ("2025_Pedido_casamento_clara_2.jpg", 4.0, "Natal de 2025", "fundo", 0),
            ("2025_Pedido_casamento_clara_3.jpg", 3.6, "", "fundo", CROSSFADE),
            ("2025_Pedido_casamento_clara_1.jpg", 4.4, "", "fundo", CROSSFADE),
            ("CONTADOR:2026>1995|4 de outubro de 2026", 9.0, "", "fiel", CROSSFADE),
            ("1 (2).jpg", 4.0, "Clara", "fundo", 0),
            ("21-46.jpg", 4.0, "Tiago", "fundo", CROSSFADE),
            (None, 3.6, "Era uma vez...", "fiel", CROSSFADE),
        ],
    },
}


def main():
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    por_nome = {r["ficheiro"].lower(): r for r in inv}

    os.makedirs(DESTINO, exist_ok=True)
    for nome, spec in DEMOS.items():
        linhas, cursor, faltam = [], 0.0, []
        for i, (ficheiro, dur, texto, tratamento, trans) in enumerate(spec["clips"], 1):
            if ficheiro and ficheiro.startswith("CONTADOR:"):
                # O contador e desenhado fotograma a fotograma pelo render.
                # Nao e uma foto e nao esta no inventario: o texto do ecra
                # leva o intervalo de anos, "2026>1995|4 de outubro de 2026".
                ident, tipo = "", "contador"
                texto = ficheiro.split(":", 1)[1]
                ficheiro = ""
            elif ficheiro:
                r = por_nome.get(ficheiro.lower())
                if not r:
                    faltam.append(ficheiro)
                    continue
                ident, tipo = r["id"], "foto"
            else:
                ident, tipo = "", "cartao"
            t = trans if i > 1 else 0.0
            inicio = cursor - t if i > 1 else 0.0
            fim = inicio + dur
            cursor = fim
            linhas.append({
                "ordem": len(linhas) + 1, "id": ident, "tipo": tipo,
                "seccao": nome, "ficheiro": ficheiro or "",
                "duracao_s": round(dur, 2), "transicao_s": round(t, 2),
                "inicio_s": round(inicio, 2), "fim_s": round(fim, 2),
                "dominante_s": round(dur - t, 2), "solo_s": round(dur - 2 * t, 2),
                "movimento": "Nenhum" if tratamento == "rajada" else "Zoom in",
                "texto_ecra": texto, "tratamento": tratamento,
                "duracao_original_s": "", "variacao_pct": "",
                "fonte_imagem": "", "nota": "",
            })
        caminho = os.path.join(DESTINO, "demo_%s.csv" % nome)
        with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUNAS)
            w.writeheader()
            w.writerows(linhas)
        faixas = escrever_som("demo_%s" % nome, spec, linhas)
        print("demo_%-4s  %2d clips  %5.1f s  %d faixas de som  %s"
              % (nome, len(linhas), cursor, faixas,
                 "FALTAM: " + ", ".join(faltam) if faltam else ""))


if __name__ == "__main__":
    main()
