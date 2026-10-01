# -*- coding: utf-8 -*-
"""Exemplo do ponto 5: o fim do filme e os creditos, como na proposta de 28 de setembro e com o que o
Tiago pediu a 30 (DISCUSSAO.md, ponto 5). Nao muda nada; escreve em saida/discussao/ponto5/.

    py -3.11 scripts/discussao/ponto5_creditos.py [--so-dizer | --quadros | --colar]

--so-dizer so faz as contas; --quadros tira sete fotogramas soltos; --colar, alem do exemplo, cola os
creditos no fim do render mais recente e faz a copia do telemovel do filme inteiro (abaixo de 30 MB).

O QUE ENTRA:
- as fotos que ele marcou na Mesa com o grupo "Creditos" (lidas da leitura mais recente da base em
  saida/leitura_mesa_N, ou da copia em data/mesa_estado.json). A ORDEM e a de uma versao da Mesa
  chamada "Creditos", se existir (ver fotos_marcadas); senao, a do numero da Mesa;
- os convidados da folha dele em C:\\casamento-video-media\\Convidados\\ (a mais recente), por grupos
  (as etiquetas de familia e de amigos) e por agregado (a coluna Familia), um agregado por linha. A
  folha NAO vai para o Git: sao dados de 140 pessoas;
- os cargos de quem fez o video (CARGOS, abaixo), que sao texto dele: aqui so para o exemplo.

NUNCA VAO PARA O ECRA: as etiquetas dos convites e dos contactos, as notas, as que dizem onde alguem
nao pode ficar sentado, e os "Noivos". So as etiquetas de GRUPOS (abaixo) entram.

A FORMA (proposta de 28/09): sem preto entre a historia e os creditos (a sala aplaude no primeiro
preto); os nomes a subir como no cinema, com as fotos marcadas numa coluna ao lado; no fecho os tres
cargos, claros e visiveis; e o titulo "CLARA & TIAGO" com a data, ate ao preto. Letra: Arial Bold, com
o letreiro quente da 098 nos titulos (a letra do titulo final e decisao dele: Arial Bold ou Cormorant).
Tudo a 58 px ou mais, que e o minimo que se le a 15 m (084).
"""
import csv
import glob
import json
import os
import re
import subprocess
import sys
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


def por_grupo(convidados):
    """[(titulo, subtitulo, [linhas])]: um agregado por linha, cada pessoa no primeiro grupo seu."""
    usados, blocos = set(), []
    for etiqueta, titulo, sub in GRUPOS:
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
    """Um agregado em linhas, quebrando so entre pessoas: um nome nunca fica partido em dois."""
    linhas, atual = [], ""
    for p in pessoas:
        t = (atual + " · " + p) if atual else p
        if atual and fonte.getlength(t) > largura:
            linhas.append(atual)
            atual = p
        else:
            atual = t
    return linhas + ([atual] if atual else [])


def letreiro_1x(linhas, tamanho, espaco):
    let = render.letreiro(linhas, tamanho, espaco, 7)
    return let.resize((let.width // render.LETREIRO_SS, let.height // render.LETREIRO_SS), Image.LANCZOS)


def rolo_de_nomes(blocos):
    """Os nomes todos numa imagem alta, preta, com a largura do painel da direita."""
    larg_texto = PAINEL_NOMES[1] - PAINEL_NOMES[0]
    larg = larg_texto + 2 * MARGEM_BRILHO
    f_nome = ImageFont.truetype(render.FONTE_TEXTO, NOME_CORPO)
    f_sub = ImageFont.truetype(render.FONTE_TEXTO, SUB_CORPO)
    pecas, anterior = [], None
    for titulo, sub, linhas in blocos:
        if titulo != anterior:
            pecas.append(("gap", 90 if pecas else 0))
            pecas.append(("titulo", letreiro_1x([titulo], TITULO_CORPO, TITULO_ESPACO)))
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
            if v.width - 2 * 160 > larg_texto:                       # 160: a folga do letreiro a 1x
                raise SystemExit("um titulo dos creditos nao cabe no painel dos nomes")
            camada = Image.new("RGB", img.size, (0, 0, 0))
            camada.paste(corte, ((larg - corte.width) // 2, y))
            img = ImageChops.lighter(img, camada)
            d = ImageDraw.Draw(img)
            y += corte.height
        elif tipo == "sub":
            d.text((larg // 2, y + 36), v, font=f_sub, fill=COR_SUB, anchor="mm")
            y += 78
        else:
            d.text((larg // 2, y + 36), v, font=f_nome, fill=COR_NOME, anchor="mm")
            y += 78
    return img


def fotos_marcadas():
    """As fotos do grupo "Creditos" na copia mais recente da base da Mesa."""
    leituras = sorted(glob.glob(os.path.join(C.REPO, "saida", "leitura_mesa_*", "montagem", "estado2.json")),
                      key=os.path.getmtime)
    fonte = leituras[-1] if leituras else os.path.join(C.REPO, "data", "mesa_estado.json")
    est = json.load(open(fonte, encoding="utf-8"))
    pid = next((p["id"] for p in est.get("pessoas", []) if sem_acentos(p.get("nome", "")) == "creditos"), None)
    marcadas = sorted(fid for fid, t in est.get("tags", {}).items() if pid and pid in t)
    # A ORDEM E A DELE, 1 de outubro: "Ajustar a ordem e que ainda nao percebi como posso fazer".
    # Uma versao da Mesa chamada "Creditos" (com ou sem acento, maiusculas ou nao) manda na ordem:
    # as fotos pela ordem dos clips, e as de um grupo (lado a lado, colagem, pilha) pela ordem de
    # dentro. Os cartoes nao contam. Uma foto com a etiqueta Creditos que nao esteja na versao vai
    # para o fim, com aviso: nada do que ele marcou desaparece calado. Sem versao, a ordem e a do
    # numero da Mesa, que e a ordem em que as fotos entraram na biblioteca.
    versao = next((v for v in est.get("versoes", []) if sem_acentos(v.get("nome", "")) == "creditos"), None)
    if versao:
        ids, vistos = [], set()
        for c in versao.get("clips", []):
            for i in ([c["i"]] if c.get("t") == "foto" and c.get("i") else []) + list(c.get("fotos") or []):
                if i not in vistos:
                    vistos.add(i)
                    ids.append(i)
        fora = [i for i in marcadas if i not in vistos]
        if fora:
            print("  AVISO: com a etiqueta Creditos mas fora da versao \"%s\", vao no fim: %s"
                  % (versao.get("nome"), ", ".join(fora)))
        ids += fora
        print("  ordem das fotos: a da versao \"%s\" da Mesa (%d fotos)" % (versao.get("nome"), len(ids)))
    elif pid:
        ids = marcadas
        print("  ordem das fotos: a do numero da Mesa (nao ha versao \"Creditos\")")
    else:
        raise SystemExit("Nao ha grupo nem versao \"Creditos\" na Mesa (%s)" % fonte)
    # a versao de cada foto e a do data/finais.csv, mais ninguem a escolhe (decisao 090)
    finais = {r["id"]: os.path.join(render.FINAIS, r["final"])
              for r in csv.DictReader(open(os.path.join(C.REPO, "data", "finais.csv"), encoding="utf-8-sig"))}
    em_falta = [i for i in ids if i not in finais or not os.path.exists(finais[i])]
    if em_falta:
        print("  AVISO: sem ficheiro na FINAIS, ficam de fora: %s" % ", ".join(sorted(em_falta)))
    return [finais[i] for i in ids if i not in em_falta], fonte


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


def main():
    pasta = C.pasta("ponto5")
    caminho = folha_mais_recente()
    convidados = ler_convidados(caminho)
    blocos, fora = por_grupo(convidados)
    fotos, fonte = fotos_marcadas()
    print("folha: %s, %d convidados; %d nos creditos em %d grupos; %d sem grupo de creditos"
          % (os.path.basename(caminho), len(convidados), sum(1 for c in convidados) - len(fora)
             - sum(1 for c in convidados if "Noivos" in c["etiquetas"]), len(blocos), len(fora)))
    print("fotos marcadas: %d (%s)" % (len(fotos), os.path.relpath(fonte, C.REPO)))
    rolo = rolo_de_nomes(blocos)
    coluna = coluna_de_fotos(fotos)
    # tempos
    # do primeiro titulo a meio do ecra ate sair tudo; o que for mais lento, nomes ou fotos, manda
    t_rolo = max((rolo.height + A * 0.55) / VELOCIDADE_NOMES, (coluna.height + A * 0.4) / VELOCIDADE_FOTOS_MAX)
    vel_nomes = (rolo.height + A * 0.55) / t_rolo
    vel_fotos = (coluna.height + A * 0.4) / t_rolo
    t_cargo, t_titulo, t_entrada = 4.2, 7.0, 1.5
    dur = t_entrada + t_rolo + len(CARGOS) * t_cargo + t_titulo
    print("rolo de nomes %d px a %.0f px/s; coluna de fotos %d px a %.0f px/s; rolo %.1f s; creditos %.1f s"
          % (rolo.height, vel_nomes, coluna.height, vel_fotos, t_rolo, dur))
    if "--so-dizer" in sys.argv:
        return

    def suave(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3 - 2 * x)
    preto = Image.new("RGB", (L, A), (0, 0, 0))
    bordas = mascara_das_bordas()
    cargos = [(letreiro_1x([quem], 110, 0.28), cargo) for cargo, quem in CARGOS]
    f_cargo = ImageFont.truetype(render.FONTE_TEXTO, 58)
    titulo_let = render.letreiro([TITULO], 130, 0.18, 11)
    data_let = letreiro_1x([DATA], 58, 0.30)

    def creditos(t):
        tr = t - t_entrada
        tela = preto.copy()
        if tr < t_rolo + 1.0:
            y0 = int(A * 0.45 - tr * vel_nomes)                # o primeiro titulo comeca a meio do ecra
            tela.paste(rolo, (PAINEL_NOMES[0] - MARGEM_BRILHO, y0))
            yf = int(A * 0.10 - tr * vel_fotos)
            tela.paste(coluna, (CENTRO_FOTOS - coluna.width // 2, yf))
            tela = Image.composite(tela, preto, bordas)
            if tr > t_rolo - 0.8:
                tela = Image.blend(tela, preto, suave((tr - t_rolo + 0.8) / 1.6))
            return tela
        tc = tr - t_rolo
        k = int(tc // t_cargo)
        if k < len(cargos):
            u = tc - k * t_cargo
            nome_img, cargo = cargos[k]
            alfa = suave(u / 0.6) * (1.0 - suave((u - t_cargo + 0.6) / 0.6))
            tela.paste(nome_img, ((L - nome_img.width) // 2, A // 2 + 40 - nome_img.height // 2))
            ImageDraw.Draw(tela).text((L // 2, A // 2 - 80), cargo, font=f_cargo, fill=COR_SUB, anchor="mm")
            return Image.eval(tela, lambda v, a=alfa: int(v * a))
        u = tc - len(cargos) * t_cargo
        fundo = render.pousar_letreiro(titulo_let, u)
        camada = preto.copy()
        camada.paste(data_let, ((L - data_let.width) // 2, A // 2 + 110 - data_let.height // 2))
        fundo = ImageChops.screen(fundo, camada)
        alfa = suave(u / 1.0) * (1.0 - suave((u - (t_titulo - 2.5)) / 2.5))
        return Image.eval(fundo, lambda v, a=alfa: int(v * a))

    if "--quadros" in sys.argv:
        # fotogramas soltos, para ver a composicao sem esperar pelo video
        for t in (1.0, 12.0, 40.0, t_entrada + t_rolo + 2.0, t_entrada + t_rolo + t_cargo + 2.0,
                  t_entrada + t_rolo + 2 * t_cargo + 2.0, t_entrada + t_rolo + 3 * t_cargo + 2.5):
            creditos(t).save(os.path.join(pasta, "_quadro_%05.1f.jpg" % t), quality=88)
        print("quadros em", pasta)
        return

    # o fim do filme: os ultimos 5 s do render de ensaio antes do fade, e a musica a continuar
    renders = sorted(glob.glob(r"C:\casamento-video-media\saida\v3_*[0-9].mp4"), key=os.path.getmtime)
    final = renders[-1]
    fim_filme = C.duracao(final) - render.FADE_FIM_IMAGEM
    antes = 5.0
    # os fotogramas do fim do filme leem-se um a um por um tubo: 5 s em memoria eram 780 MB
    leitor = subprocess.Popen([C.FF, "-v", "error", "-ss", "%.3f" % (fim_filme - antes), "-t", "%.3f" % antes,
                               "-i", final, "-an", "-vf", "fps=%d" % FPS, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                              stdout=subprocess.PIPE)
    ultimo = None
    # a musica do fim continua de onde o filme a deixa, e acaba com os creditos. O relogio do som e o do
    # corpo, que comeca onde os videos de abertura acabam: o filme inteiro menos o corpo.
    est = C.carregar()
    ultima = C.leitos(C.entradas_de_som(est))[-1]
    abertura = C.duracao(final) - est["fim"]
    pos = ultima["in_s"] + (fim_filme - antes - abertura) - ultima["quando"]
    total = antes + dur
    livre = C.duracao(ultima["caminho"]) - pos
    print("musica do fim: %s, dos %.1f s do ficheiro; sobram %.0f s para %.0f s de exemplo"
          % (C.nome_da_musica(ultima["ficheiro"]), pos, livre, total))
    e = dict(ultima)
    e.pop("_subida", None)
    e.update({"quando": 0.0, "in_s": pos, "dura": min(total, livre), "dura_medida": min(total, livre),
              "subida": render.SUBIDA_NUM_INICIO, "cruza": 0.0})
    som_saida = os.path.join(pasta, "_som.m4a")
    render.construir_som(render.ffmpeg(), [e], total, som_saida, render.FADE_FIM_SOM)

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
            im = creditos(tt)
            if tt < t_entrada:
                im = Image.blend(ultimo, im, suave(tt / t_entrada))
        enc.stdin.write(im.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    leitor.stdout.close()
    leitor.wait()
    os.remove(som_saida)
    leve = os.path.join(pasta, "exemplo_creditos_telemovel.mp4")
    subprocess.run([C.FF, "-v", "error", "-y", "-i", saida, "-vf", "scale=1280:720", "-c:v", "libx264", "-crf", "24",
                    "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", leve], check=True)
    print("escrito", saida, "e", leve)
    if "--colar" in sys.argv:
        colar_no_filme(final, fim_filme - antes, saida, pasta)
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
    filtro = ("[0:v]trim=0:%.3f,setpts=PTS-STARTPTS[v0];[0:a]atrim=0:%.3f,asetpts=PTS-STARTPTS[a0];"
              "[1:v]setpts=PTS-STARTPTS[v1];[1:a]asetpts=PTS-STARTPTS[a1];"
              "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a];[v]scale=960:540:flags=lanczos[vs]" % (corte, corte))
    passlog = os.path.join(pasta, "_passlog_colar")
    comum = [C.FF, "-hide_banner", "-loglevel", "error", "-y", "-i", final, "-i", creditos,
             "-filter_complex", filtro, "-map", "[vs]", "-c:v", "libx264", "-preset", "medium",
             "-b:v", "%dk" % video_kbps, "-pix_fmt", "yuv420p", "-passlogfile", passlog]
    subprocess.run(comum + ["-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(comum + ["-map", "[a]", "-pass", "2", "-c:a", "aac", "-b:a", "%dk" % som_kbps,
                            "-movflags", "+faststart", movel], check=True)
    for sobra in (passlog + "-0.log", passlog + "-0.log.mbtree"):
        if os.path.exists(sobra):
            os.remove(sobra)
    print("filme com creditos: %s (%.0f s, %.1f MB)" % (movel, total, os.path.getsize(movel) / 1048576.0))


if __name__ == "__main__":
    main()
