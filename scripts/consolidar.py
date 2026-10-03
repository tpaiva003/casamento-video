# -*- coding: utf-8 -*-
"""Junta numa pasta so a melhor versao de cada fotografia.

O Tiago pediu uma pasta com todas as fotos melhoradas finais, e pos uma
condicao que manda em tudo o resto:

    "nao podemos estragar as feicoes nem as pessoas, o que nos queremos e
     melhorar a qualidade das fotos mantendo-as reais"

COMO ISSO E GARANTIDO, e nao e por promessa:

  1. O modelo usado e o realesrgan-x4plus, que e um ampliador generico. NAO
     foi usado, e esta proibido no CLAUDE.md, qualquer restauro de rostos
     (GFPGAN, CodeFormer). Esses nao ampliam a cara, redesenham-na, e inventam
     um rosto plausivel que nao e o da pessoa. E essa a diferenca entre
     melhorar e falsificar, e ela esta na escolha do modelo, nao num ajuste.

  2. Mede-se quanto e que cada foto MUDOU face ao original, em percentagem de
     diferenca media por pixel. Uma ampliacao honesta muda pouco: afina
     contornos e tira grao. Uma invencao muda muito. As fotos que mais mudaram
     sao listadas para se olhar, e ficam de fora da pasta final se passarem do
     limite.

  3. O original nunca e tocado. A pasta final e feita por copia.

ORDEM DE PREFERENCIA de cada foto:
  restauradas/    tratamento manual, quando existe
  upscaled-ia/    Real-ESRGAN, se a alteracao estiver dentro do limite
  upscaled/       lanczos com realce suave
  original        quando nenhuma das outras melhora

Uso:
    py -3.11 scripts/consolidar.py
    py -3.11 scripts/consolidar.py --limite 12     mais tolerante a alteracao
    py -3.11 scripts/consolidar.py --listar        diz o que faria, sem copiar
"""
import csv
import io
import os
import shutil
import sys

from PIL import Image, ImageChops, ImageOps, ImageStat

sys.stdout.reconfigure(encoding="utf-8")

# A GUARDA DAS CARAS PRECISA DO OPENCV, e se ele nao estiver este script continua a fazer o
# resto: uma consolidacao sem a guarda e pior do que com ela, mas e muito melhor do que uma
# consolidacao que nao corre. Quem for instalar: py -3.11 -m pip install "opencv-python==4.10.0.84"
_VE_CARAS = True
try:
    import cv2
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import auditar_caras
except Exception:
    _VE_CARAS = False

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
TRABALHO = os.path.normcase(os.path.abspath(r"C:\casamento-video-media\trabalho"))
FINAIS = r"C:\casamento-video-media\FINAIS"

FONTES = [(r"C:\casamento-video-media\restauradas", "restaurada"),
          (r"C:\casamento-video-media\upscaled-ia", "IA"),
          (r"C:\casamento-video-media\upscaled", "lanczos")]

# Percentagem de diferenca media por pixel acima da qual a foto e considerada
# demasiado alterada para entrar sem ser vista. 8 por cento e generoso para
# uma ampliacao e apertado para uma invencao.
LIMITE_ALTERACAO = 8.0

# E A GUARDA DAS CARAS, decisao 086, que e a que faltava.
#
# O Tiago, 23 de setembro: "algumas imagens que estao incluidas na minha mesa parece que
# perderam qualidade. Houve ate pelo menos uma que acho que os modelos foram para la editar
# os olhos e ficou estranho". Tinha razao, e a medicao de cima nao dava por nada: ela compara
# a fotografia INTEIRA, e uma cara e uma fraccao pequena do quadro. A foto onde a rede
# desenhou olhos abertos por cima de duas manchas moles mudou 1,64 por cento no total, muito
# abaixo dos 8 do limite.
#
# Medido no acervo, cara a cara, com o detector a dizer onde elas estao: o caminho lanczos
# devolve 90 por cento da textura do original na mediana e 77 no pior caso; a rede devolve 73
# na mediana e 17 no pior. Por isso o piso fica em 0,80: deixa passar o lanczos inteiro e
# trava a rede onde ela alisa a serio.
#
# E HA UM TECTO, que e a parte contra-intuitiva. Uma cara com MAIS detalhe do que o original
# tem nao esta melhor: tem detalhe que ninguem fotografou. E assim que uma mancha mole vira um
# olho aberto. Acima de 1,25 a versao e recusada, venha de onde vier.
CARA_MINIMA = 0.80
CARA_MAXIMA = 1.25


LIMITE_FUNDO_DESFOCADO = 1.55
LARGURA_ALVO, ALTURA_ALVO, FOLGA = 1920, 1080, 1.15


# ABAIXO DE 1,5 VEZES, O LANCZOS. Decisao 052.
#
# O Tiago viu oito recortes lado a lado das duas versoes, nas ampliacoes onde o
# lanczos mais perde, e escolheu: "gosto mais da lanczos". A rede neuronal amplia
# sempre 4 vezes e so depois se reduz, portanto retoca a pele e os contornos mesmo
# quando a foto so precisava de crescer um bocadinho; nas digitalizacoes antigas
# chega a desenhar contornos escuros que nao existem. A partir de 1,5 vezes o
# lanczos fica mole de mais, e ai continua a rede neuronal.
LIMITE_LANCZOS = 1.5

# A REDE NEURONAL SAIU DO FILME, decisao 090. So o lanczos pode entrar, e o original.
#
# O Tiago, 28 de setembro, com a 21-45-8 no ecra: "Precisamos tambem de assegurar que nao
# invencoes. [...] Ha muito olhos que ficaram todos defeituosos. Isso nao pode acontecer." A
# guarda das caras (decisao 086) so mede as caras que o detector encontra, e o detector nao
# encontra caras abaixo de uns 60 pixeis: nas fotos de grupo elas tem 25 a 45 no original, e
# e precisamente ai que a rede, sem informacao, desenha olhos e bocas plausiveis. Na 21-45-8
# as doze caras passaram sem ser medidas, com olhos fechados, desalinhados e desfeitos; no
# clip 131, a equipa de andebol, dezasseis. Nenhuma guarda que dependa de encontrar as caras
# garante zero invencoes, e zero e o que ele pediu. O lanczos so interpola pixeis e nao
# consegue desenhar um olho; tem o mesmo tamanho que a versao da rede, portanto nada estica
# mais, so fica mais macio. A restaurada sai pela mesma razao: redesenha.
#
# A LIMITE_LANCZOS fica, porque o estado_fotos e os testes ainda a leem para saber quanto
# cada foto cresce; ja nao escolhe entre duas versoes. As pastas upscaled-ia e restauradas
# continuam em disco e no FONTES, so para o indice e as auditorias dizerem o que existe.
VERSOES_PERMITIDAS = ("lanczos",)


def fator_ampliacao(larg, alt):
    """Quanto a foto tem de crescer, pela mesma regra do upscale.py."""
    if larg / alt < LIMITE_FUNDO_DESFOCADO:
        return (ALTURA_ALVO / alt) * FOLGA
    return max(LARGURA_ALVO / larg, ALTURA_ALVO / alt) * FOLGA


def precisa_crescer(larg, alt):
    """A mesma regra do upscale.py e do upscale_ia.py. Tem de ser a mesma."""
    if larg / alt < LIMITE_FUNDO_DESFOCADO:
        fator = (ALTURA_ALVO / alt) * FOLGA
    else:
        fator = max(LARGURA_ALVO / larg, ALTURA_ALVO / alt) * FOLGA
    return fator > 1.0


def vinhetas_da_fita():
    """Ficheiros que so aparecem como marca da linha do tempo, nunca inteiros.

    Uma marca da fita e desenhada com 20 por cento da altura do ecra, cerca de
    216 pixeis. Pedir-lhe a resolucao de quem vai encher 1080 e mandar a rede
    neuronal trabalhar oito minutos para nada: a `gravuras_coa.jpg`, de 500x375,
    dava fator 3,3 e ia ser vista a 287 pixeis de largura.

    A lista nao esta escrita a mao, sai do proprio estado da Mesa, para nao
    envelhecer. Um ficheiro que tambem seja usado como fotografia normal em
    qualquer versao sai da lista e volta a ter de crescer.
    """
    import json
    caminho = os.path.join(REPO, "data", "mesa_estado.json")
    if not os.path.exists(caminho):
        return set()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import linha_tempo
    estado = json.load(io.open(caminho, encoding="utf-8"))
    marcas, fotos = set(), set()
    for versao in estado.get("versoes", []):
        for c in versao.get("clips", []):
            if c.get("t") == "marcos":
                for _d, _m, _r, _g, img in linha_tempo.ler_meses(c.get("x", ""))[1]:
                    if img:
                        marcas.add(img.lower())
            elif c.get("f"):
                fotos.add(c["f"].lower())
    return marcas - fotos


def proteger():
    d = os.path.normcase(os.path.abspath(FINAIS))
    if d == TRABALHO or d.startswith(TRABALHO + os.sep):
        sys.exit("RECUSADO: o destino cai dentro da pasta de trabalho.")


def alteracao(original, tratado, lado=700):
    """Diferenca media por pixel entre as duas, em percentagem.

    As duas sao levadas ao mesmo tamanho pequeno antes de comparar, para a
    medida nao depender da resolucao e para o grao fino nao dominar. O que
    fica medido e mudanca de estrutura e de tom, que e o que denuncia
    invencao.
    """
    a = original.convert("RGB").copy()
    b = tratado.convert("RGB").copy()
    a.thumbnail((lado, lado), Image.LANCZOS)
    b = b.resize(a.size, Image.LANCZOS)
    dif = ImageChops.difference(a, b)
    media = sum(ImageStat.Stat(dif).mean) / 3.0
    return 100.0 * media / 255.0


def mudanca(caminho_original, caminho_versao):
    """A alteracao() entre o original (ja rodado pelo EXIF) e uma versao tratada, pelos caminhos.

    Esta fora do main() desde 3 de outubro, como a copiar() mais abaixo, para o
    scripts/entrada_rapida.py guardar a medida de cada foto e nao voltar a medir as 741 por
    causa de tres novas. Aqui nao ha cache nenhuma: o consolidar.py mede tudo, como sempre.
    """
    with Image.open(caminho_original) as o, Image.open(caminho_versao) as t:
        o = ImageOps.exif_transpose(o)
        return alteracao(o, t)


def copiar(escolha, destino, origem):
    """Poe a versao escolhida na FINAIS: copia tal e qual, ou reescreve em JPEG se nao for JPEG."""
    if origem == "original" or escolha.lower().endswith((".jpg", ".jpeg")):
        shutil.copy2(escolha, destino)
    else:
        with Image.open(escolha) as im:
            im.convert("RGB").save(destino, "JPEG", quality=95, optimize=True)


def caras_do_original(caminho, cache, ident):
    """Onde estao as caras no ORIGINAL, uma vez por fotografia. [] quando nao ha detector."""
    if ident in cache:
        return cache[ident]
    cache[ident] = []
    if not _VE_CARAS:
        return cache[ident]
    try:
        img = auditar_caras.ler(caminho)
        if img is not None:
            cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cache[ident] = auditar_caras.caras_de(cinza)
    except Exception:
        pass
    return cache[ident]


def fidelidade_da_cara(caminho_original, caminho_versao, cache, ident):
    """Quanta textura da cara sobra nesta versao, face ao original. None quando nao se mede.

    Devolve o PIOR valor de todas as caras: numa fotografia de grupo basta uma cara
    destruida para a versao nao servir.
    """
    if not _VE_CARAS:
        return None
    caixas = caras_do_original(caminho_original, cache, ident)
    if not caixas:
        return None
    try:
        o = auditar_caras.ler(caminho_original)
        v = auditar_caras.ler(caminho_versao)
        if o is None or v is None:
            return None
        if (v.shape[1], v.shape[0]) != (o.shape[1], o.shape[0]):
            v = cv2.resize(v, (o.shape[1], o.shape[0]), interpolation=cv2.INTER_AREA)
        go = cv2.cvtColor(o, cv2.COLOR_BGR2GRAY)
        gv = cv2.cvtColor(v, cv2.COLOR_BGR2GRAY)
        piores = []
        for (x, y, w, h) in caixas:
            a, b = go[y:y + h, x:x + w], gv[y:y + h, x:x + w]
            if min(a.shape) < 32:
                continue
            da = auditar_caras.detalhe(a)
            piores.append(auditar_caras.detalhe(b) / max(0.01, da))
        if not piores:
            return None
        # o mais longe de 1,00 para qualquer dos lados: apagar e inventar sao os dois maus
        return min(piores, key=lambda f: -abs(f - 1.0))
    except Exception:
        return None


def main():
    proteger()
    listar = "--listar" in sys.argv
    caras_por_id, caras_recusadas = {}, []
    limite = LIMITE_ALTERACAO
    if "--limite" in sys.argv:
        limite = float(sys.argv[sys.argv.index("--limite") + 1])

    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        inv = list(csv.DictReader(fh))

    # Indexa o que existe tratado, por id.
    tratados = {}
    for pasta, etiqueta in FONTES:
        if not os.path.isdir(pasta):
            continue
        for nome in os.listdir(pasta):
            if not nome.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            ident = nome.split("__")[0]
            tratados.setdefault(ident, {})[etiqueta] = os.path.join(pasta, nome)

    # Nomes finais: mantem o nome original quando nao ha choque, para a pasta
    # servir como album e nao como lista de codigos.
    contagem = {}
    for r in inv:
        contagem[r["ficheiro"].lower()] = contagem.get(r["ficheiro"].lower(), 0) + 1

    os.makedirs(FINAIS, exist_ok=True)
    resumo = {}
    demasiado, erros = [], []
    copiadas = 0
    indice = []
    antes = set()
    if os.path.isdir(FINAIS):
        antes = {n for n in os.listdir(FINAIS)
                 if n.lower().endswith((".jpg", ".jpeg", ".png"))}

    for r in inv:
        ident = r["id"]
        disponiveis = tratados.get(ident, {})
        escolha, origem, mudou = r["caminho"], "original", 0.0

        # SE A FOTO NAO PRECISA DE CRESCER, O ORIGINAL GANHA SEMPRE.
        #
        # Isto nao estava aqui e custou 21 fotos. A pasta upscaled\ tem
        # ficheiros feitos com a regra antiga, que ampliava tudo ate encher
        # 1920 de largura mesmo em fotos verticais que ja tinham pixeis a
        # mais. Como a ordem de preferencia punha lanczos acima de original,
        # a FINAIS ficou com versoes ampliadas sem necessidade, e uma foto
        # ampliada sem necessidade e simplesmente mais mole do que ela propria.
        #
        # Nenhuma metrica apanhou isto porque nenhuma estava a comparar. A
        # auditoria e que o encontrou, ao achar estranho que o lanczos medisse
        # melhor do que a IA em tres fotos: media melhor porque era maior.
        try:
            if precisa_crescer(int(r["largura"]), int(r["altura"])) is False:
                disponiveis = {k: v for k, v in disponiveis.items()
                               if k == "restaurada"}
        except Exception:
            pass

        # AS VERSOES RECUSADAS, E PORQUE, vao para o indice (coluna recusadas). Sem isto quem
        # le o indice so via "ficou o original" e concluia que faltava escolher a versao: a 27
        # de setembro o estado_fotos.py pos 48 fotos "a espera" na Mesa, todas elas com a versao
        # da regra recusada de proposito pela guarda das caras (decisao 086).
        recusas = []
        for etiqueta in VERSOES_PERMITIDAS:
            caminho = disponiveis.get(etiqueta)
            if not caminho:
                continue
            try:
                mudou = mudanca(r["caminho"], caminho)
            except Exception as e:
                erros.append((r["ficheiro"], str(e)))
                continue
            if etiqueta == "IA" and mudou > limite:
                demasiado.append((r["id"], r["ficheiro"], mudou))
                recusas.append("%s:alteracao %.1f" % (etiqueta, mudou))
                continue
            # A GUARDA DAS CARAS, e vale para TODAS as fontes e nao so para a rede: a unica
            # restaurada do acervo deixava a cara com 62 por cento da textura e tambem nao
            # passa. So o original esta sempre isento, porque e ele a referencia.
            fid = fidelidade_da_cara(r["caminho"], caminho, caras_por_id, ident)
            if fid is not None and not (CARA_MINIMA <= fid <= CARA_MAXIMA):
                caras_recusadas.append((ident, r["ficheiro"], etiqueta, fid))
                recusas.append("%s:cara %.2f" % (etiqueta, fid))
                continue
            escolha, origem = caminho, etiqueta
            break

        base, ext = os.path.splitext(r["ficheiro"])
        if contagem.get(r["ficheiro"].lower(), 0) > 1:
            nome_final = "%s__%s%s" % (ident, base, ext)
        else:
            nome_final = r["ficheiro"]
        if origem != "original":
            nome_final = os.path.splitext(nome_final)[0] + ".jpg"

        resumo[origem] = resumo.get(origem, 0) + 1
        indice.append({"id": ident, "ficheiro": r["ficheiro"],
                       "final": nome_final, "origem": origem,
                       "mudou_pct": "%.2f" % mudou, "recusadas": ";".join(recusas)})
        if listar:
            continue
        destino = os.path.join(FINAIS, nome_final)
        try:
            copiar(escolha, destino, origem)
            copiadas += 1
        except Exception as e:
            erros.append((r["ficheiro"], str(e)))

    # O INDICE, que e o que acaba com os palpites.
    #
    # Ate aqui cada consumidor adivinhava qual era o ficheiro certo. O render.py
    # nem sequer olhava para a FINAIS: repetia a ordem de preferencia antiga e
    # ficava com a versao IA mesmo em fotos que nao precisavam de crescer, que e
    # precisamente o que o Tiago proibiu. Tres copias da mesma regra, e a que
    # fazia o video era a que estava por corrigir.
    #
    # A partir daqui ha uma resposta so, escrita, e quem precisar le-a.
    if not listar:
        caminho_indice = os.path.join(REPO, "data", "finais.csv")
        with open(caminho_indice, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["id", "ficheiro", "final",
                                               "origem", "mudou_pct", "recusadas"])
            w.writeheader()
            for linha in indice:
                w.writerow(linha)

    # FICHEIROS QUE SOBRARAM DE CORRIDAS ANTIGAS.
    #
    # A regra mudou e com ela o nome de saida: uma foto que antes ia como
    # "9-24-4.jpg" por ser lanczos vai hoje como "9-24-4.jpeg" por ser original.
    # A antiga fica la, com 2208 pixeis de largura, e o consumidor seguinte pode
    # apanha-la pelo nome. NAO SE APAGA NADA: a regra 3 do CLAUDE.md e clara.
    # Reporta-se, e ele decide.
    sobras = sorted(antes - {l["final"] for l in indice})

    print("Pasta final: %s" % FINAIS)
    print("Originais em %s: nao sao tocados." % TRABALHO)
    print()
    print("DE ONDE VEIO CADA FOTO")
    for k in ("restaurada", "IA", "lanczos", "original"):
        if resumo.get(k):
            print("  %-12s %3d" % (k, resumo[k]))
    print("  %-12s %3d" % ("TOTAL", sum(resumo.values())))
    if not listar:
        print("  copiadas: %d" % copiadas)
        print("  indice:   data/finais.csv")
    print()
    if sobras:
        print("SOBRAS DE CORRIDAS ANTIGAS, %d ficheiros" % len(sobras))
        print("Nenhum destes foi escrito agora. Ficam onde estao, nao apago nada")
        print("dentro da pasta de media, mas um consumidor distraido pode")
        print("apanha-los pelo nome:")
        for n in sobras[:12]:
            print("   %s" % n)
        if len(sobras) > 12:
            print("   e mais %d" % (len(sobras) - 12))
        print()
    if demasiado:
        print("EXCLUIDAS POR ALTERAREM DEMASIADO (limite %.0f%%)" % limite)
        print("Estas ficaram com o original. Ve os recortes antes de as aceitar.")
        for ident, ficheiro, m in sorted(demasiado, key=lambda x: -x[2])[:15]:
            print("  %-7s %-42s alterou %.1f%%" % (ident, ficheiro[:42], m))
        print()
    else:
        print("Nenhuma foto passou o limite de alteracao da imagem inteira.")
        print()

    # O QUE A GUARDA DAS CARAS FEZ, E PORQUE E QUE ISTO SE DIZ SEMPRE.
    #
    # Ate 23 de setembro este sitio dizia "Nenhuma feicao foi refeita: o modelo usado amplia,
    # nao redesenha rostos". Era uma promessa que a medicao nao sustentava: media a imagem
    # inteira, e a foto onde a rede desenhou olhos abertos por cima de duas manchas moles
    # passou com 1,64 por cento. A frase foi-se abaixo no dia em que o Tiago olhou para o
    # ecra. Agora nao se promete nada: diz-se o que foi medido e o que foi recusado.
    if not _VE_CARAS:
        print("SEM A GUARDA DAS CARAS: o opencv nao esta instalado neste PC, e por isso")
        print("ninguem verificou o que os modelos fizeram aos rostos. Instala com")
        print('  py -3.11 -m pip install "opencv-python==4.10.0.84" scikit-image')
        print()
    elif caras_recusadas:
        print("RECUSADAS PELA GUARDA DAS CARAS: %d versoes" % len(caras_recusadas))
        print("A cara tem de ficar entre %.0f%% e %.0f%% da textura do original. Abaixo, o"
              % (CARA_MINIMA * 100, CARA_MAXIMA * 100))
        print("modelo apagou a cara; acima, desenhou detalhe que ninguem fotografou.")
        for ident, ficheiro, etiqueta, fid in sorted(caras_recusadas, key=lambda x: x[3])[:15]:
            print("  %-7s %-38s %-11s cara a %.0f%%" % (ident, ficheiro[:38], etiqueta, fid * 100))
        if len(caras_recusadas) > 15:
            print("  e mais %d" % (len(caras_recusadas) - 15))
        print()
    else:
        print("A guarda das caras nao recusou nenhuma versao.")
        print()
    if erros:
        print("ERROS: %d" % len(erros))
        for f, e in erros[:6]:
            print("  %s: %s" % (f[:40], e[:70]))


if __name__ == "__main__":
    main()
