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

CROSSFADE = 0.7

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
            ("21-38.jpg", 0.45, "Caminhadas pelo Parque das Serras do Porto", "rajada", 0),
            ("21-39.jpg", 0.45, "", "rajada", 0),
            ("21-41.JPG", 0.45, "", "rajada", 0),
            ("21-42.JPG", 0.45, "", "rajada", 0),
            ("21-43.JPG", 0.45, "", "rajada", 0),
            ("21-44.JPG", 0.45, "", "rajada", 0),
            ("21-45.JPG", 0.45, "", "rajada", 0),
            ("9-24-2.JPG", 0.45, "", "rajada", 0),
            (None, 3.6, "Familia", "fiel", CROSSFADE),
            ("10-1 (2).jpg", 4.4, "Com o pai. Era pequenina e ja lhe dava ouras", "fundo", CROSSFADE),
            ("10-2.jpg", 4.4, "", "fundo", CROSSFADE),
        ],
    },
    "v1c": {
        "musica": "Ana Faria - Clara.mp3",
        "musica_in": 8.0,
        "clips": [
            ("Scanner_20260814.jpg", 4.4, "E desde sempre apaixonada por caes", "fundo", 0),
            ("9-26.JPG", 3.7, "Pelos dela", "fundo", CROSSFADE),
            ("9-28.JPG", 3.7, "E pelos dos outros", "fundo", CROSSFADE),
            ("21-49-54.jpg", 4.4, "E o Tiago, com a Sky", "fundo", CROSSFADE),
            ("2014_Clara_Tiago_Praia_Mia_cadela_clara.jpg", 6.5,
             "2014, os dois com a Mia", "fundo", CROSSFADE),
        ],
    },
    "v2": {
        "musica": "OS TRIBALISTAS - VELHA INFÂNCIA (INSTRUMENTAL).MP3",
        "musica_in": 0.0,
        "clips": [
            (None, 3.4, "1995", "fiel", 0),
            ("1 (2).jpg", 3.7, "Clara", "fundo", CROSSFADE),
            ("21-46.jpg", 3.7, "Tiago", "fundo", CROSSFADE),
            ("2.jpg", 3.7, "", "fundo", CROSSFADE),
            ("21-47.jpg", 3.7, "", "fundo", CROSSFADE),
            ("5 (2).jpg", 3.7, "", "fundo", CROSSFADE),
            ("21-49.jpg", 3.7, "", "fundo", CROSSFADE),
            ("6.jpg", 3.7, "", "fundo", CROSSFADE),
            ("21-49-2.jpg", 3.7, "", "fundo", CROSSFADE),
            ("7.jpg", 3.7, "", "fundo", CROSSFADE),
            ("21-49-3.jpg", 4.4, "", "fundo", CROSSFADE),
        ],
    },
    "v3": {
        "musica": "Papillon - ¡ N.M.N ! (feat. Bárbara Tinoco) [1].MP3",
        "musica_in": 0.0,
        "clips": [
            ("2025_Pedido_casamento_clara_1.jpg", 4.2, "", "fundo", 0),
            ("2025_Pedido_casamento_clara_2.jpg", 3.6, "", "fundo", CROSSFADE),
            ("2025_Pedido_casamento_clara_3.jpg", 3.6, "", "fundo", CROSSFADE),
            ("2025_Pedido_casamento_clara_4.jpg", 3.6, "", "fundo", CROSSFADE),
            ("20260101_011410.jpg", 4.6, "1 de janeiro de 2026", "fundo", CROSSFADE),
            (None, 3.4, "Trinta e um anos antes", "fiel", CROSSFADE),
            ("1 (2).jpg", 4.0, "", "fiel", 0),
            ("21-46.jpg", 4.0, "", "fiel", 0),
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
            if ficheiro:
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
        print("demo_%-4s  %2d clips  %5.1f s  %s"
              % (nome, len(linhas), cursor, "FALTAM: " + ", ".join(faltam) if faltam else ""))


if __name__ == "__main__":
    main()
