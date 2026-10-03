# -*- coding: utf-8 -*-
"""O filme como o render o desenha, para o palco da Mesa (a pre-visualizacao, 2 de outubro).

O Tiago, a 2 de outubro: quer "pre-visualizar da forma mais realista possivel o video dentro da
Mesa antes de fazer render (poupando tempo ao nao precisar de fazer render so para analisar o
estado)". O palco da Mesa mostrava as miniaturas uma a uma, com o tempo escrito em cada clip e um
encadeado igual para todos. O filme nao e isso: o montar_da_mesa.py poe clips que a Mesa nao tem
(o nome do bebe no preto, decisoes 092 e 093), segura a fita parada na data acesa (089), estica o
cartao de um nascimento e da a foto a seguir ao nome 1 s para subir.

O QUE ISTO LE E O QUE O RENDER LE: data/montagens/<nome>.csv, a montagem que o montar escreveu da
Mesa. Uma linha por clip do filme, no relogio do filme inteiro (os videos de abertura primeiro, com
corte seco, e o corpo a seguir, como o render os cola), com a chave que a Mesa sabe calcular
(som_para_mesa.chave_base, mais a ordem de aparicao). A Mesa encontra assim cada clip dela no
filme mesmo que ele mude coisas de sitio depois da montagem; um clip que nao encontra conta-se
pela regra da Mesa e o palco diz que e aproximado.

E AS IMAGENS DOS MARCOS DA FITA DE 1995 ("@kobe, japao.png"), pequenas, a altura com que o
linha_tempo.meses() as poe (0,20 do ecra), em JPEG dentro da pagina: sao seis e pesam 80 KB. O
palco desenha-as onde o render as desenha. Procuram-se com o mesmo linha_tempo.imagem_da_marca().

So le. Nao escreve em lado nenhum: o gerar_mesa.py poe o resultado em window.PALCO.

Uso:  py -3.11 scripts/palco_para_mesa.py      (mostra o que a Mesa vai receber)
"""
import base64
import csv
import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTAGENS = os.path.join(REPO, "data", "montagens")
# a altura da imagem de um marco na fita: o linha_tempo.meses() pede imagem_da_marca(img, int(A * 0.20))
ALTURA_DA_MARCA = int(1080 * 0.20)
# A FITA PARADA (decisao 089) vem no fim do texto da fita: "...~5.45@12.34"
SEGURA = re.compile(r"~(\d+(?:\.\d+)?)(?:@(\d+(?:\.\d+)?))?\s*$")


def _f(x, omissao=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return omissao


# O QUE A MESA TINHA QUANDO SE MONTOU (revisor de 2 de outubro). A chave de um clip (o tipo e as fotos, o
# texto ou o ficheiro) nao leva a duracao nem o encadeado: uma foto de 4 s que ele passou a 41 s depois da
# montagem continuava a bater com a linha dela, e o palco punha-a com os 4 s da montagem; a musica do resto
# do filme entrava ate 41 s antes do render. O montar_da_mesa.py le data/mesa_estado.json (ESTADO), e e
# esse ficheiro que diz o que cada clip tinha: com ele ao lado de cada linha (md, mc, mv), a Mesa compara o
# clip de agora com o que se montou, ao centesimo, e o que mudou conta-se pela regra dela.
ESTADO_DA_MONTAGEM = os.path.join(REPO, "data", "mesa_estado.json")
# o estado tem de ser o que o montar leu: escreve-se antes do CSV. Um estado mais novo do que a montagem
# (lido da base e ainda nao montado) ja nao diz o que se montou, e a Mesa usa entao a regra sem ele.
FOLGA_DO_ESTADO_S = 2.0


def chave_da_mesa(c):
    """A chave base de um clip da Mesa, a do chaveDoClipBase() do editor_base.html."""
    t = c.get("t") or "foto"
    if t == "foto":
        return "foto:" + str(c.get("i") or "")
    if t in ("lado", "colagem", "pilha"):
        return t + ":" + "|".join(str(x) for x in (c.get("fotos") or []))
    if t == "video":
        return "video:" + str(c.get("f") or "").strip()
    return t + ":" + " ".join(str(c.get("x") or "").split())


def o_que_a_mesa_tinha(versao, montagem_feita):
    """{chave: {md, mc, mv}} dos clips da versao no data/mesa_estado.json que o montar leu, ou {} se o
    ficheiro nao existir, nao se ler, ou for mais novo do que a montagem."""
    try:
        if os.path.getmtime(ESTADO_DA_MONTAGEM) > montagem_feita + FOLGA_DO_ESTADO_S:
            return {}
        with io.open(ESTADO_DA_MONTAGEM, encoding="utf-8") as fh:
            e = json.load(fh)
    except (OSError, ValueError):
        return {}
    e = e.get("data", e) if isinstance(e, dict) else {}
    v = next((v for v in e.get("versoes") or [] if v.get("id") == versao), None)
    if not v:
        return {}
    vistos, saida = {}, {}
    for c in v.get("clips") or []:
        base = chave_da_mesa(c)
        vistos[base] = vistos.get(base, 0) + 1
        x = {"md": c.get("d"), "mc": c.get("c")}
        if (c.get("t") or "foto") == "video":
            x["mv"] = c.get("vin")
        saida["%s#%d" % (base, vistos[base])] = x
    return saida


def linhas_do_filme(nome="v3", versao="demo_v3"):
    """{montagem, versao, gerado, videos, fim, linhas: [...]} ou None sem a montagem.

    Cada linha: {chave, t (tipo), filme, d, c (encadeado com que entra), e no "nome" o x, e na fita
    parada segura e congela, e md, mc e mv (o d, o c e o vin que o clip tinha na Mesa quando se montou,
    ver o_que_a_mesa_tinha)}. `filme` e o instante no filme inteiro, a mesma conta do
    som_para_mesa.py: os videos do bloco inicial um a seguir ao outro, e o corpo a partir do fim
    deles, contado do inicio_s do primeiro clip do corpo.
    """
    import som_para_mesa
    import render
    cam = os.path.join(MONTAGENS, nome + ".csv")
    if not os.path.exists(cam):
        return None
    with open(cam, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    if not linhas:
        return None
    vistos, todas = {}, []
    for l in linhas:
        base = som_para_mesa.chave_base(l)
        vistos[base] = vistos.get(base, 0) + 1
        todas.append({"l": l, "chave": "%s#%d" % (base, vistos[base]), "tipo": l["tipo"],
                      "inicio": _f(l["inicio_s"]), "d": _f(l["duracao_s"]),
                      "c": _f(l["transicao_s"])})
    fanfarra, corpo = render.partir_em_fanfarra_e_corpo(todas)
    videos = sum(x["d"] for x in fanfarra)
    desvio = corpo[0]["inicio"] if corpo else 0.0
    saida, t = [], 0.0
    for x in fanfarra:
        saida.append({"chave": x["chave"], "t": "video", "filme": round(t, 3), "d": round(x["d"], 3), "c": 0})
        t += x["d"]
    for k, x in enumerate(corpo):
        linha = {"chave": x["chave"], "t": x["tipo"], "filme": round(videos + x["inicio"] - desvio, 3),
                 "d": round(x["d"], 3), "c": 0 if k == 0 else round(x["c"], 3)}
        texto = x["l"].get("texto_ecra") or ""
        if x["tipo"] == "nome":
            linha["x"] = texto.strip()
        elif x["tipo"] == "marcos":
            m = SEGURA.search(texto)
            if m:
                linha["segura"] = _f(m.group(1))
                if m.group(2):
                    linha["congela"] = _f(m.group(2))
        saida.append(linha)
    fim = max((videos + x["inicio"] - desvio + x["d"]) for x in corpo) if corpo else videos
    import datetime
    feito_s = os.path.getmtime(cam)
    feito = datetime.datetime.fromtimestamp(feito_s)
    # o que cada clip tinha na Mesa quando se montou (ver o_que_a_mesa_tinha)
    tinha = o_que_a_mesa_tinha(versao, feito_s)
    for linha in saida:
        if linha["chave"] in tinha:
            linha.update(tinha[linha["chave"]])
    return {"montagem": nome, "versao": versao, "gerado": feito.strftime("%d/%m às %H:%M"),
            "videos": round(videos, 3), "fim": round(fim, 3), "linhas": saida, "com_a_mesa": bool(tinha)}


def _textos_de_fitas():
    """Os textos das fitas de 1995 que a Mesa pode mostrar: os da montagem e os das ultimas leituras
    da base (a copia do Git e a leitura mais recente em saida/). Uma fita que ele escreva depois so
    tem as imagens na geracao seguinte da Mesa."""
    textos = []
    cam = os.path.join(MONTAGENS, "v3.csv")
    if os.path.exists(cam):
        with open(cam, encoding="utf-8-sig", newline="") as fh:
            textos += [r.get("texto_ecra") or "" for r in csv.DictReader(fh) if r.get("tipo") == "marcos"]
    estados = [os.path.join(REPO, "data", "mesa_estado.json")]
    leituras = glob.glob(os.path.join(REPO, "saida", "leitura_mesa*", "montagem", "estado2.json"))
    if leituras:
        estados.append(max(leituras, key=os.path.getmtime))
    for caminho in estados:
        try:
            with io.open(caminho, encoding="utf-8") as fh:
                e = json.load(fh)
        except (OSError, ValueError):
            continue
        e = e.get("data", e) if isinstance(e, dict) else {}
        for v in e.get("versoes") or []:
            for c in v.get("clips") or []:
                if c.get("t") == "marcos":
                    textos.append(c.get("x") or "")
    return textos


def imagens_das_marcas():
    """{nome do ficheiro como esta na fita: "data:image/jpeg;base64,..."}, so as que existem em disco.

    O nome e o que esta escrito na marca, com espacos e virgulas (CLAUDE.md, "a marca da fita que
    falha sem se queixar"): o palco procura pelo mesmo nome que o render procura.
    """
    import linha_tempo
    nomes = []
    for texto in _textos_de_fitas():
        corpo = linha_tempo.sem_segura(texto).partition("|")[2]
        for peca in corpo.split(";"):
            if "@" in peca:
                nome = peca.partition("@")[2].strip()
                if nome and nome not in nomes:
                    nomes.append(nome)
    saida = {}
    for nome in nomes:
        im = linha_tempo.imagem_da_marca(nome, ALTURA_DA_MARCA)
        if im is None:
            continue
        buf = io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=82, optimize=True)
        saida[nome] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    return saida


def palco_para_mesa():
    """O que vai para window.PALCO: {filme, marcas}. Nunca para a geracao da Mesa: sem montagem ou
    sem imagens, fica o que houver, e o palco conta pela regra da Mesa."""
    try:
        filme = linhas_do_filme()
    except Exception as erro:  # noqa: BLE001 - uma Mesa sem isto continua a servir
        print("  AVISO: nao li o filme da montagem para o palco (%s)" % erro)
        filme = None
    try:
        marcas = imagens_das_marcas()
    except Exception as erro:  # noqa: BLE001
        print("  AVISO: nao li as imagens dos marcos da fita (%s)" % erro)
        marcas = {}
    return {"filme": filme, "marcas": marcas}


def resumo(p):
    f = p.get("filme")
    kb = sum(len(v) for v in (p.get("marcas") or {}).values()) / 1024.0
    if not f:
        return "sem montagem: o palco conta pela Mesa; %d imagens de marcos (%.0f KB)" % (len(p.get("marcas") or {}), kb)
    nomes = sum(1 for l in f["linhas"] if l["t"] == "nome")
    paradas = sum(1 for l in f["linhas"] if l.get("segura"))
    com = sum(1 for l in f["linhas"] if "md" in l)
    return ("%d clips da montagem de %s, %d nomes de bebe, %d fitas paradas, %d imagens de marcos (%.0f KB); %s"
            % (len(f["linhas"]), f["gerado"], nomes, paradas, len(p.get("marcas") or {}), kb,
               ("%d com a duracao e o encadeado que tinham na Mesa" % com) if com else
               "sem o estado que se montou (data/mesa_estado.json mais novo): a Mesa ve o que mudou pela regra"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    p = palco_para_mesa()
    print(resumo(p))
    if p["filme"]:
        for l in p["filme"]["linhas"][:12]:
            print(" ", l)
