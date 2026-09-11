# -*- coding: utf-8 -*-
"""Constroi a v1c: a v1b mais as correcoes narrativas.

REGRA DA v1c: tudo o que a v1b decidiu mantem-se, incluindo os tratamentos.
O que muda e o ALINHAVO da historia. Aqui sim mexe-se na ordem, acrescentam-se
fotos que nao estavam no video dela, e escreve-se texto novo onde e preciso.

As edicoes sao DECLARADAS uma a uma na lista EDICOES, cada uma com o numero do
encadeamento de docs/ENCADEAMENTOS.md que a justifica. Isso e de proposito: o
Tiago aprova ou rejeita item a item, e cada linha do CSV diz que edicao a pos
ali. Nada entra sem ficar escrito porque entrou.

O que NAO se faz aqui, e fica dito para nao haver confusao com a v2: a v1c
mantem a arquitetura dela, uma vida de cada vez. Intercalar por idade e outra
versao. A v1c so aproxima o que ja existe e tapa buracos.

Uso:  py -3.11 scripts/montar_v1c.py
      py -3.11 scripts/montar_v1c.py --so 1,3,8      aplica so essas edicoes
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "data", "montagens", "v1b.csv")
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
DESTINO = os.path.join(REPO, "data", "montagens")

CROSSFADE = 0.7
COLUNAS = ["ordem", "id", "tipo", "seccao", "ficheiro", "duracao_s",
           "transicao_s", "inicio_s", "fim_s", "dominante_s", "solo_s",
           "movimento", "texto_ecra", "tratamento", "duracao_original_s",
           "variacao_pct", "fonte_imagem", "nota"]

# Cada edicao diz: o encadeamento que a justifica, onde entra (ancora pelo
# ficheiro ou pelo texto que ja la esta), e o que entra.
#
#   ancora_ficheiro / ancora_texto  a entrada da v1b a seguir a qual se mete
#   fotos     lista de (ficheiro, duracao, texto, tratamento)
#   cartao    texto de um cartao de ecra inteiro, em vez de fotos
EDICOES = [
    {
        "n": 8,
        "titulo": "Os dois cartoes de 1995, encostados",
        "porque": "Ela escreveu 'tambem nasceu em 1995' no cartao dele. A "
                  "palavra 'tambem' e uma rima que hoje morre a doze minutos "
                  "de distancia. Encostados, a sala percebe no primeiro "
                  "minuto que esta a ver uma historia com duas personagens.",
        "ancora_texto": "Era muito bem disposta",
        "cartao": "Era uma vez um menino loiro, de olhos azuis, que tambem nasceu em 1995",
        "fotos": [("21-46.jpg", 4.2, "Foi o segundo filho", "auto"),
                  ("1996_tiago_e_irmao_mais_velho.jpg", 4.2, "Com o irmao mais velho", "auto")],
        "depois_cartao": "E ela",
    },
    {
        "n": 1,
        "titulo": "Os caes dela, o cao dele, a cadela dos dois",
        "porque": "A legenda dela diz 'pelos dela e pelos dos outros'. A Sky "
                  "dele esta a treze minutos e meio dali. E existe uma foto "
                  "dos dois com a Mia que nunca entrou no video.",
        "ancora_texto": "E pelos dos outros",
        "fotos": [("21-49-54.jpg", 4.2, "E o Tiago, com a Sky", "auto"),
                  ("2014_Clara_Tiago_Praia_Mia_cadela_clara.jpg", 5.5,
                   "2014, os dois com a Mia", "auto")],
    },
    {
        "n": 2,
        "titulo": "As insignias trocadas",
        "porque": "Ela impoe-lhe as insignias em 2016, ele esta ao lado dela "
                  "em 2018. Hoje as duas metades estao a catorze minutos e "
                  "meio uma da outra, e a de 2016 nem sequer esta no video.",
        "ancora_texto": "Imposicao de Insignias",
        "ancora_alternativa": "Imposição de Insígnias",
        "fotos": [("2016_Clara_impoe_insignias_tiago.jpg", 5.0,
                   "2016, ela impoe as insignias a ele", "auto"),
                  ("2016_Familia_Tiago_imposicao_insignias.jpg", 4.2, "", "auto")],
    },
    {
        "n": 7,
        "titulo": "Os amigos do secundario ja eram os mesmos",
        "porque": "Poe o Tiago dentro da vida dela seis minutos e meio antes "
                  "do cartao 'O Encontro', sem inventar um facto: as datas "
                  "estao escritas nos nomes dos ficheiros pelo proprio.",
        "ancora_texto": "Com amigos da Secund",
        "fotos": [("2011_Tiago_e_clara_aniversario_CLARA_POUCO_ANTES_DE_COMEÇAR_A_NAMORAR.jpg",
                   4.6, "2011, antes de namorarem", "auto"),
                  ("2013_Tiago_Na_latada_da_Clara_amigos secundario.jpg", 4.2,
                   "2013, na latada dela", "auto"),
                  ("2015_CLARA_TIAGO_AMIGOS_SECUNDARIO.jpg", 4.2, "2015", "auto"),
                  ("2016_CLARA_TIAGO_AMIGOS_SECUNDARIO.jpg", 4.2, "2016", "auto")],
    },
    {
        "n": 3,
        "titulo": "O pedido de casamento, que hoje nao se ve",
        "porque": "O video mostra o anuncio do noivado mas nunca mostra o "
                  "pedido. Aos 2:18 ela ate conta o primeiro pedido de "
                  "casamento, aos 8 anos, com uma argola de porta-chaves. "
                  "Mostrar a causa antes do efeito fecha esse arco.",
        "ancora_texto": "Primeiros minutos de 2026",
        "antes": True,
        "fotos": [("2025_Pedido_casamento_clara_1.jpg", 4.2, "2025, o pedido", "auto"),
                  ("2025_Pedido_casamento_clara_2.jpg", 3.8, "", "auto"),
                  ("2025_Pedido_casamento_clara_3.jpg", 3.8, "", "auto"),
                  ("2025_Pedido_casamento_clara_4.jpg", 4.2, "", "auto")],
    },
]


def mmss(s):
    return "%d:%02d" % (int(float(s)) // 60, int(float(s)) % 60)


def normalizar(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.lower().split())


def main():
    so = None
    if "--so" in sys.argv:
        so = {int(x) for x in sys.argv[sys.argv.index("--so") + 1].split(",")}

    with open(BASE, encoding="utf-8-sig", newline="") as fh:
        base = list(csv.DictReader(fh))
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))
    por_nome = {r["ficheiro"].lower(): r for r in inv}

    def entrada(ficheiro, dur, texto, tratamento, nota):
        r = por_nome.get(ficheiro.lower())
        if not r:
            return None
        trat = tratamento
        if trat == "auto":
            trat = "fundo" if r["orientacao"] == "vertical" else "fiel"
        return {"ordem": 0, "id": r["id"], "tipo": "foto", "seccao": "",
                "ficheiro": ficheiro, "duracao_s": dur, "transicao_s": CROSSFADE,
                "inicio_s": 0, "fim_s": 0, "dominante_s": 0, "solo_s": 0,
                "movimento": "Zoom in", "texto_ecra": texto,
                "tratamento": trat, "duracao_original_s": "",
                "variacao_pct": "", "fonte_imagem": "", "nota": nota}

    saida = list(base)
    aplicadas, falhadas = [], []

    for ed in EDICOES:
        if so and ed["n"] not in so:
            continue
        chaves = [ed.get("ancora_texto"), ed.get("ancora_alternativa")]
        chaves = [normalizar(k) for k in chaves if k]
        alvo = None
        for i, r in enumerate(saida):
            texto = normalizar(r.get("texto_ecra"))
            if texto and any(k in texto for k in chaves):
                alvo = i
                break
        if alvo is None:
            falhadas.append((ed["n"], ed["titulo"], "ancora nao encontrada"))
            continue

        novos, em_falta = [], []
        nota = "encadeamento %d: %s" % (ed["n"], ed["titulo"])
        if ed.get("cartao"):
            novos.append({"ordem": 0, "id": "", "tipo": "cartao", "seccao": "",
                          "ficheiro": "", "duracao_s": 4.2,
                          "transicao_s": CROSSFADE, "inicio_s": 0, "fim_s": 0,
                          "dominante_s": 0, "solo_s": 0, "movimento": "",
                          "texto_ecra": ed["cartao"], "tratamento": "fiel",
                          "duracao_original_s": "", "variacao_pct": "",
                          "fonte_imagem": "", "nota": nota})
        for ficheiro, dur, texto, trat in ed.get("fotos", []):
            e = entrada(ficheiro, dur, texto, trat, nota)
            if e:
                novos.append(e)
            else:
                em_falta.append(ficheiro)
        if ed.get("depois_cartao"):
            novos.append({"ordem": 0, "id": "", "tipo": "cartao", "seccao": "",
                          "ficheiro": "", "duracao_s": 3.2,
                          "transicao_s": CROSSFADE, "inicio_s": 0, "fim_s": 0,
                          "dominante_s": 0, "solo_s": 0, "movimento": "",
                          "texto_ecra": ed["depois_cartao"], "tratamento": "fiel",
                          "duracao_original_s": "", "variacao_pct": "",
                          "fonte_imagem": "", "nota": nota})
        if em_falta:
            falhadas.append((ed["n"], ed["titulo"], "sem ficheiro: " + ", ".join(em_falta)))
        if not novos:
            continue
        pos = alvo if ed.get("antes") else alvo + 1
        saida[pos:pos] = novos
        aplicadas.append((ed["n"], ed["titulo"], len(novos),
                          mmss(base[min(alvo, len(base) - 1)]["inicio_s"])))

    cursor = 0.0
    for i, r in enumerate(saida, 1):
        d = float(r["duracao_s"])
        t = 0.0 if i == 1 else float(r["transicao_s"] or 0)
        inicio = cursor - t if i > 1 else 0.0
        fim = inicio + d
        cursor = fim
        r.update({"ordem": i, "inicio_s": round(inicio, 2), "fim_s": round(fim, 2),
                  "dominante_s": round(d - t, 2), "solo_s": round(d - 2 * t, 2)})

    os.makedirs(DESTINO, exist_ok=True)
    caminho = os.path.join(DESTINO, "v1c.csv")
    with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(saida)

    print("v1c, a partir da v1b")
    print()
    print("EDICOES APLICADAS")
    for n, titulo, quantos, onde in aplicadas:
        print("  encadeamento %-2d  %-46s %d entradas, perto dos %s"
              % (n, titulo[:46], quantos, onde))
    if falhadas:
        print()
        print("EDICOES QUE FALHARAM")
        for n, titulo, motivo in falhadas:
            print("  encadeamento %-2d  %-40s %s" % (n, titulo[:40], motivo))
    print()
    print("Escrito %s" % caminho)
    print("  entradas: %d  (v1b tinha %d, entraram %d)"
          % (len(saida), len(base), len(saida) - len(base)))
    print("  duracao: %s  (v1b tem 15:00)" % mmss(saida[-1]["fim_s"]))
    print()
    print("As entradas novas ficam marcadas na coluna nota com o encadeamento")
    print("que as justifica, para se poder aprovar ou rejeitar uma a uma.")


if __name__ == "__main__":
    main()
