# -*- coding: utf-8 -*-
"""Entrada rapida: as fotos e as musicas novas prontas para publicar na Mesa, num comando so.

O Tiago, 3 de outubro, vespera do casamento: "a possibilidade de colocar fotos na pasta e
elas entrarem logo na Mesa de Montagem, e igual para as musicas". O scripts/vigiar_pastas.py
diz quando ha ficheiros novos; este script deixa tudo pronto para publicar e escreve
saida/entrada_rapida.json, o manifesto com o que entrou, os avisos, o build e a LISTA EXATA
dos ficheiros a publicar.

DA O MESMO QUE O atualizar_fotos.py, SO QUE MAIS DEPRESSA. Os passos sao os mesmos, pela
mesma ordem, e quem decide continua a ser cada script: este chama o main() de cada um e so
lhe guarda as contas que nao mudam. O atualizar_fotos.py gasta seis a oito minutos porque
refaz tudo de todas as fotos, mesmo quando so entraram tres:

  inventario.py      le e faz o sha256 das 741 fotos           aqui: so as que mudaram de
                                                               tamanho ou de data
  consolidar.py      mede a alteracao e as caras de todas, e   aqui: so mede os pares novos,
                     copia as 741 para a FINAIS                e so copia o que nao esta la igual
  gerar_editor.py    abre as 741 para as miniaturas            aqui: a miniatura fica guardada
  gerar_previas.py   abre as 741 e refaz as 47 folhas          aqui: a celula fica guardada, e
                                                               so se refazem as folhas que mudam

O upscale.py ja so fazia o que faltava, o estado_fotos.py e o gerar_montagens_editor.py sao
de um segundo, e o gerar_mesa.py (com o audio_para_mesa.py la dentro, que faz as copias de
som so das musicas novas) corre tal e qual, sem nenhuma mudanca. E ele que fica com a maior
parte do tempo: cerca de 25 segundos, 13 deles a medir os glifos das letras.

MEDIDO A 3 DE OUTUBRO, numa copia inteira do repositorio e dos media (741 fotos), com o PC
ocupado por outros trabalhos, e comparado ficheiro a ficheiro com o caminho completo
(data/, proxies/, saida/, a FINAIS e a upscaled, cerca de 2000 ficheiros, sem nenhuma diferenca):

                                          atualizar_fotos.py     entrada_rapida.py
  sem nada de novo                        8 min 12 s             33 s (2 s desde a correcao das 14h)
  3 fotos e 1 musica                      8 min 02 s             44 s
  1 nova, 1 trocada, 1 tirada, 3 musicas  7 min 56 s             34 s
  a primeira corrida, com a cache vazia                          3 min 28 s

A PRIMEIRA CORRIDA enche a cache e por isso demora mais; mesmo assim as contas que faltam
fazem-se em quatro fios (--fios) antes de cada passo, e fica em menos de metade do caminho
completo. O --aquecer faz so essa parte, sem mudar nada, para a primeira corrida a serio ja
ser das rapidas.

UMA FOTO NOVA MUDA TODAS AS FOLHAS QUE VEM DEPOIS DELA. As previas vao pela ordem da pasta e
do nome, 16 por folha, e uma foto que entra a meio empurra as seguintes: com 3 fotos novas na
01-NOVAS refizeram-se 27 das 47 folhas, 23 MB para publicar. Isso e o caminho completo que o
manda, e aqui tem de sair igual; as folhas que nao mudam ficam de fora da lista.

O QUE SE GUARDA, E ONDE. Tudo em saida/_cache/entrada_rapida/, fora do Git e fora da pasta
dos media. Cada conta guarda-se pelo caminho, pelo tamanho e pela data do ficheiro de onde
saiu: se o ficheiro mudar, a conta refaz-se. As miniaturas e as celulas guardam-se em PNG,
que nao perde nada, para a folha sair igual ao byte a que o caminho completo faz. Apagar a
pasta inteira nao estraga nada: a corrida seguinte demora o que demorava e volta a enche-la.

NUNCA APAGA, NAO MOVE E NAO ESCREVE POR CIMA de nada em C:\\casamento-video-media. Na FINAIS
so entra o que la nao esta igual (o consolidar.py copiava as 741 por cima a cada corrida;
aqui ate se escreve menos). Duplicados pelo hash so se reportam.

O QUE HA PARA PUBLICAR e o que mudou desde a ultima publicacao: a pagina, as folhas das
previas cujo conteudo mudou e as copias de som e de video novas. "Desde a ultima publicacao"
e desde o ultimo `--publicado`; na primeira corrida, sem esse registo, conta-se que o que
estava em saida/ antes dela ja esta publicado. Se correr duas vezes antes de publicar, a
lista junta as duas.

O QUE A CORRECAO DE 3 DE OUTUBRO (14h) ACRESCENTOU, depois de um cetico a ter posto a prova:
  - SEM NADA DE NOVO NAO CORRE NADA: escreve o manifesto com "nada_de_novo": true, o build fica
    o que estava e nenhum ficheiro e reescrito (2 segundos). O --forcar corre os passos na mesma.
  - UMA FOTO TROCADA por outra com o mesmo nome ficava com a versao ampliada da foto ANTIGA em
    upscaled\ (e na FINAIS, logo no filme) quando as dimensoes eram as mesmas. Agora a versao
    refaz-se (upscale.py --so-ids), aqui e no atualizar_fotos.py, e o consolidar.py recusa um
    lanczos que mude a foto mais do que o limite.
  - UMA CORRIDA QUE NAO ACABOU fica escrita em por_acabar.json: a seguinte acaba-a e diz bem
    o que entrou. A vigia, com --correr, volta a tentar sozinha depois de um FALHOU.
  - A TRANCA e do Windows (um byte trancado com o msvcrt): so uma corrida passa, mesmo
    arrancadas no mesmo instante, e uma corrida morta nao prende a seguinte. O atualizar_fotos.py
    pede a mesma. Os outros scripts que escrevem os mesmos ficheiros (o gerar_mesa.py de outra
    sessao) veem-se na lista dos processos: espera-se por eles ate dois minutos, e se ainda la
    estiverem a corrida segue e diz-o nos avisos.
  - UMA COPIA IGUAL de uma foto registada ja nao lhe leva o id (inventario.py): fica com id seu
    e sai nos avisos como duplicado.

Uso:
    py -3.11 scripts/entrada_rapida.py              faz tudo e escreve o manifesto
    py -3.11 scripts/entrada_rapida.py --forcar     corre os passos mesmo sem nada de novo nas pastas
    py -3.11 scripts/entrada_rapida.py --aquecer    so enche a cache, sem mudar nada (uns 3 min)
    py -3.11 scripts/entrada_rapida.py --publicado  depois de publicar: o que esta em saida/ e o publicado
    py -3.11 scripts/entrada_rapida.py --tudo       a lista leva tudo, e nao so o que mudou
    py -3.11 scripts/entrada_rapida.py --sem-mesa   para antes do gerar_mesa.py (para testes)
    py -3.11 scripts/entrada_rapida.py --fios 2     menos fios (4 por omissao), se houver um render a correr

Depois disto faltam os passos que so o Claude faz, com a ferramenta Artifact: publicar a
pagina e os ficheiros do manifesto, ler montagem/estado2 e confirmar a revisao, escrever
montagem/publicacao com {build, quando, fotos}, e correr o --publicado.
"""
import atexit
import contextlib
import csv
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

SAIDA = os.path.join(REPO, "saida")
CACHE = os.path.join(SAIDA, "_cache", "entrada_rapida")
MEDIDAS = os.path.join(CACHE, "medidas.json")
PUBLICADO = os.path.join(CACHE, "publicado.json")
JA_VISTOS = os.path.join(CACHE, "ja_vistos.json")
TRANCA = os.path.join(CACHE, "a_correr.txt")
FECHO = os.path.join(CACHE, "a_correr.tranca")
POR_ACABAR = os.path.join(CACHE, "por_acabar.json")
REGISTO = os.path.join(CACHE, "ultima_corrida.txt")
MANIFESTO = os.path.join(SAIDA, "entrada_rapida.json")
PAGINA = os.path.join(SAIDA, "mesa.html")
PY = sys.executable

VERSAO_CACHE = 1
MB = 1048576.0
# Os limites da publicacao, os do audio_para_mesa.py: 60 MB por lote (o endereco aceita 64),
# 15 MB por ficheiro, 256 ficheiros ao todo a contar com a pagina.
LOTE_MAX = 60 * MB
FICHEIRO_MAX = 15 * MB
FICHEIROS_MAX = 256
TIPOS = {".jpg": "image/jpeg", ".mp4": "video/mp4", ".m4a": "audio/mp4"}
# Quantas fotos se leem e quantas folhas se fazem ao mesmo tempo (--fios). O i5 tem 4 nucleos fisicos.
FIOS = 4
_TRANCA_DAS_CONTAS = threading.Lock()


# ----------------------------------------------------------------------------- utilitarios
def chave(caminho):
    return os.path.normcase(os.path.abspath(caminho))


def receita_da_pillow():
    """A versao da Pillow, que entra na chave de tudo o que ela calcula (miniaturas, celulas, alteracao):
    uma versao nova pode reduzir uma foto de outra maneira, e a conta guardada deixava de ser a de agora."""
    import PIL
    return "Pillow %s" % PIL.__version__


def assinatura(caminho):
    st = os.stat(caminho)
    return [st.st_size, st.st_mtime_ns]


def sha256_de(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_json(caminho, omissao):
    try:
        with io.open(caminho, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return omissao


def escrever_json(caminho, dados, indent=None):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = caminho + ".parte"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=indent,
                  separators=None if indent else (",", ":"))
    os.replace(tmp, caminho)


def ler_csv(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def plural(n, um, varios):
    return "%d %s" % (n, um if n == 1 else varios)


def dizer(texto=""):
    print(texto)
    sys.stdout.flush()


def conta(relato, nome, mais=1):
    """Soma ao relato; com tranca, que ha contas feitas em varios fios."""
    with _TRANCA_DAS_CONTAS:
        if isinstance(relato[nome], list):
            relato[nome].append(mais)
        else:
            relato[nome] += mais


def em_paralelo(funcao, itens):
    """funcao(item) para cada item, em FIOS fios. Serve so para ADIANTAR contas que ficam guardadas:
    uma excecao aqui nao conta, porque o main() do script volta a pedir a mesma conta e e ele que a ve."""
    itens = list(itens)

    def uma(x):
        try:
            funcao(x)
        except Exception:                           # noqa: BLE001
            pass
    if FIOS <= 1 or len(itens) < 2:
        for x in itens:
            uma(x)
        return
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(FIOS) as ex:
        list(ex.map(uma, itens))


# ------------------------------------------------------------------------------ a cache
def abrir_medidas():
    g = ler_json(MEDIDAS, {})
    if not isinstance(g, dict) or g.get("versao") != VERSAO_CACHE:
        g = {"versao": VERSAO_CACHE}
    for k in ("medir", "a_serio", "mudanca", "cara", "folhas", "refeitas"):
        g.setdefault(k, {})
    return g


def guardar_medidas(g):
    escrever_json(MEDIDAS, g)


def novo_relato():
    return {"lidas": 0, "ilegiveis": [], "medidas": 0, "caras": 0, "finais_copiadas": [],
            "finais_iguais": 0, "miniaturas": 0, "celulas": 0, "folhas_feitas": [], "folhas_iguais": 0}


def ligar_inventario(inventario, g, relato):
    """O medir() e o foto_a_serio() do inventario, com a resposta guardada por ficheiro."""
    medir_a_serio, a_serio_a_serio = inventario.medir, inventario.foto_a_serio

    def medir(caminho):
        k, ass = chave(caminho), assinatura(caminho)
        v = g["medir"].get(k)
        if v and v[0] == ass:
            h, larg, alt, dexif, equip = v[1]
            # a miniatura de proxies/ faz-se dentro do medir() a serio: se faltar, e por ele que se vai
            if os.path.exists(os.path.join(inventario.PROXIES, h[:12] + ".jpg")):
                return h, larg, alt, dexif, equip
        try:
            r = medir_a_serio(caminho)
        except Exception as e:
            conta(relato, "ilegiveis", (caminho, type(e).__name__))
            raise
        g["medir"][k] = [ass, list(r)]
        conta(relato, "lidas")
        return r

    def foto_a_serio(caminho):
        try:
            k, ass = chave(caminho), assinatura(caminho)
        except OSError:
            return a_serio_a_serio(caminho)
        v = g["a_serio"].get(k)
        if v and v[0] == ass:
            return v[1]
        r = bool(a_serio_a_serio(caminho))
        g["a_serio"][k] = [ass, r]
        return r

    inventario.medir, inventario.foto_a_serio = medir, foto_a_serio


class _VigiaDoCv2(object):
    """O cv2 do consolidar, a contar as excecoes que la dentro se engolem (ver ligar_consolidar)."""

    def __init__(self, cv2, falhas):
        self._cv2, self._falhas = cv2, falhas

    def __getattr__(self, nome):
        x = getattr(self._cv2, nome)
        if not callable(x):
            return x
        falhas = self._falhas

        def vigiada(*a, **k):
            try:
                return x(*a, **k)
            except BaseException:
                falhas[0] += 1
                raise
        return vigiada


def ligar_consolidar(consolidar, g, relato):
    """A alteracao e a fidelidade da cara guardadas por par (original, versao), e a copia para a
    FINAIS so quando la nao esta igual.

    A GUARDA DAS CARAS ENGOLE AS EXCECOES e devolve None, que quer dizer "sem caras, nao se mede".
    Uma falta de memoria a meio de um render dava um None que nao e verdade, e guarda-lo era
    aceitar essa versao para sempre. Por isso contam-se as excecoes la dentro, e uma medida em que
    houve alguma nao se guarda: fica para a corrida seguinte, como no caminho completo.
    """
    mudanca_a_serio, fidelidade_a_serio = consolidar.mudanca, consolidar.fidelidade_da_cara
    copiar_a_serio = consolidar.copiar
    falhas = [0]
    receita = "sem opencv"
    if consolidar._VE_CARAS:
        ac = consolidar.auditar_caras

        def vigiada(fn):
            def w(*a, **k):
                try:
                    return fn(*a, **k)
                except BaseException:
                    falhas[0] += 1
                    raise
            return w
        ac.ler, ac.caras_de, ac.detalhe = vigiada(ac.ler), vigiada(ac.caras_de), vigiada(ac.detalhe)
        receita = "opencv %s" % consolidar.cv2.__version__
        consolidar.cv2 = _VigiaDoCv2(consolidar.cv2, falhas)

    def par(original, versao):
        return "%s|%s" % (chave(original), chave(versao))

    pillow = receita_da_pillow()

    def mudanca(original, versao):
        k, ass = par(original, versao), [assinatura(original), assinatura(versao), pillow]
        v = g["mudanca"].get(k)
        if v and v[0] == ass:
            return v[1]
        r = mudanca_a_serio(original, versao)
        g["mudanca"][k] = [ass, r]
        conta(relato, "medidas")
        return r

    def fidelidade_da_cara(original, versao, cache, ident):
        if not consolidar._VE_CARAS:
            return fidelidade_a_serio(original, versao, cache, ident)
        try:
            k, ass = par(original, versao), [assinatura(original), assinatura(versao), receita]
        except OSError:
            return fidelidade_a_serio(original, versao, cache, ident)
        v = g["cara"].get(k)
        if v and v[0] == ass:
            return v[1]
        antes = falhas[0]
        r = fidelidade_a_serio(original, versao, cache, ident)
        if falhas[0] == antes:
            g["cara"][k] = [ass, r]
        conta(relato, "caras")
        return r

    def copiar(escolha, destino, origem):
        # O copy2 leva a data do original: um destino com o mesmo tamanho e a mesma data e a
        # copia que ja la esta, e nao se escreve por cima dela.
        if origem == "original" or escolha.lower().endswith((".jpg", ".jpeg")):
            try:
                a, b = os.stat(escolha), os.stat(destino)
                if a.st_size == b.st_size and a.st_mtime_ns == b.st_mtime_ns:
                    relato["finais_iguais"] += 1
                    return
            except OSError:
                pass
        copiar_a_serio(escolha, destino, origem)
        relato["finais_copiadas"].append(os.path.basename(destino))

    consolidar.mudanca, consolidar.fidelidade_da_cara, consolidar.copiar = mudanca, fidelidade_da_cara, copiar


def _guardada_em_png(pasta, a_serio, relato, qual):
    """Uma funcao que devolve a imagem que `a_serio(caminho)` daria, guardada em PNG (sem perda)
    pelo caminho, tamanho e data do ficheiro."""
    from PIL import Image
    os.makedirs(pasta, exist_ok=True)
    pillow = receita_da_pillow()

    def onde(caminho):
        ass = assinatura(caminho)
        nome = hashlib.sha1(("%s|%d|%d|%s" % (chave(caminho), ass[0], ass[1], pillow)).encode("utf-8")).hexdigest()[:24]
        return os.path.join(pasta, nome + ".png")

    def falta(caminho):
        try:
            return not os.path.exists(onde(caminho))
        except OSError:
            return False                          # um ficheiro que nao esta la nao se adianta

    def f(caminho):
        guardada = onde(caminho)
        if os.path.exists(guardada):
            try:
                with Image.open(guardada) as im:
                    im.load()
                    if im.mode == "RGB":
                        return im.copy()
            except Exception:
                pass                              # uma PNG partida refaz-se
        im = a_serio(caminho)
        tmp = guardada + ".parte"
        try:
            im.save(tmp, "PNG", compress_level=1)
            os.replace(tmp, guardada)
        except OSError:
            pass                                  # sem cache continua a dar o resultado certo
        conta(relato, qual)
        return im
    f.falta = falta
    return f


def ligar_editor(gerar_editor, relato):
    gerar_editor.miniatura = _guardada_em_png(os.path.join(CACHE, "mini%d" % gerar_editor.CELULA),
                                              gerar_editor.miniatura, relato, "miniaturas")


def ligar_previas(gp, g, relato):
    """A celula de cada foto guardada, e as folhas que nao mudaram ficam como estao."""
    fazer_a_serio = gp.fazer_folha
    gp.celula = _guardada_em_png(os.path.join(CACHE, "cel%d" % gp.CELULA), gp.celula, relato, "celulas")
    receita = [gp.CELULA, gp.COLUNAS, gp.LINHAS, gp.QUALIDADE, list(gp.FUNDO), receita_da_pillow()]

    def fazer_folha(lote, finais, n_folha, caminho):
        nome = os.path.basename(caminho)
        de = [receita, n_folha]
        completa = True
        for r in lote:
            origem = gp.origem_de(r, finais)
            try:
                de.append([r["id"], chave(origem)] + assinatura(origem))
            except OSError:
                completa = False
        v = g["folhas"].get(nome)
        if completa and v and v.get("de") == de and os.path.exists(caminho) \
                and os.path.getsize(caminho) == v.get("bytes") and sha256_de(caminho) == v.get("sha256"):
            conta(relato, "folhas_iguais")
            return dict(v["pos"]), 0
        pos, erros = fazer_a_serio(lote, finais, n_folha, caminho)
        if completa and not erros:
            g["folhas"][nome] = {"de": de, "bytes": os.path.getsize(caminho),
                                 "sha256": sha256_de(caminho), "pos": pos}
        else:
            g["folhas"].pop(nome, None)
        conta(relato, "folhas_feitas", nome)
        return pos, erros

    def fazer_folhas(tarefas):
        # Cada folha e um ficheiro seu, feito das suas 16 fotos: fazem-se FIOS de cada vez e
        # devolvem-se pela ordem, que e a unica coisa de que o main() precisa.
        if FIOS <= 1 or len(tarefas) < 2:
            return [gp.fazer_folha(*t) for t in tarefas]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(FIOS) as ex:
            return list(ex.map(lambda t: gp.fazer_folha(*t), tarefas))

    def limpar_antigas():
        # As folhas ficam: cada uma e refeita ou confirmada pelo fazer_folha(). So sai o que nao
        # e folha (as previas antigas, uma por foto); as folhas a mais saem no fim, pelo indice.
        for n in os.listdir(gp.DESTINO):
            if n == "lista.json" or (n.lower().endswith(".jpg") and not re.match(r"^folha_\d+\.jpg$", n)):
                os.remove(os.path.join(gp.DESTINO, n))

    gp.fazer_folha, gp.fazer_folhas, gp.limpar_antigas = fazer_folha, fazer_folhas, limpar_antigas


# ---------------------------------------------------------------- adiantar, em varios fios
# O main() de cada script pede as contas uma a uma. Quando a cache esta vazia (a primeira corrida) ou
# quando entram muitas fotos de uma vez, as contas que faltam fazem-se antes, em varios fios, e ficam
# guardadas: o main() corre a seguir e encontra-as feitas. Nada aqui decide: so se adianta trabalho.
def adiantar_inventario(inventario, g, relato, so=None):
    """Le as fotos que a cache ainda nao tem. `so`: so estes caminhos (para o --aquecer)."""
    por_ler = []
    for _etiqueta, raiz in inventario.PASTAS:
        for base, _dirs, fs in os.walk(raiz):
            dentro_de_files = os.path.basename(base).endswith("_files")
            for nome in fs:
                if not nome.lower().endswith(inventario.EXT):
                    continue
                caminho = os.path.join(base, nome)
                if so is not None and chave(caminho) not in so:
                    continue
                if dentro_de_files and not inventario.foto_a_serio(caminho):
                    continue
                try:
                    v = g["medir"].get(chave(caminho))
                    if v and v[0] == assinatura(caminho):
                        continue
                except OSError:
                    continue
                por_ler.append(caminho)
    em_paralelo(inventario.medir, por_ler)
    del relato["ilegiveis"][:]                    # as que nao se leem, e o main() que as conta
    return len(por_ler)


def adiantar_consolidar(consolidar):
    """Mede os pares (original, versao) que o consolidar.main() vai pedir.

    Quais sao, pergunta-se ao proprio main(): corre com --listar (nao copia nem escreve o indice)
    e com as duas medidas trocadas por quem so toma nota. Assim a lista nunca diverge da regra dele.
    """
    pares = []
    mudanca, fidelidade = consolidar.mudanca, consolidar.fidelidade_da_cara

    def anota(original, versao):
        pares.append((original, versao))
        return 0.0

    consolidar.mudanca, consolidar.fidelidade_da_cara = anota, (lambda *a, **k: None)
    guardado = sys.argv
    sys.argv = ["consolidar.py", "--listar"]
    try:
        with contextlib.redirect_stdout(Fita()):
            consolidar.main()
    except (SystemExit, Exception):                 # noqa: BLE001 - quem se queixa e o main() a serio
        pares = []
    finally:
        consolidar.mudanca, consolidar.fidelidade_da_cara = mudanca, fidelidade
        sys.argv = guardado

    def par(p):
        mudanca(p[0], p[1])
        fidelidade(p[0], p[1], {}, "")
    em_paralelo(par, pares)
    return len(pares)


def adiantar_editor(gerar_editor):
    """Faz as miniaturas que a cache ainda nao tem, das fotos que o gerar_editor.main() vai abrir."""
    finais = {}
    if os.path.isdir(gerar_editor.FINAIS):
        for n in os.listdir(gerar_editor.FINAIS):
            finais[n.lower()] = os.path.join(gerar_editor.FINAIS, n)
    caminhos = [gerar_editor.caminho_final(r, finais) for r in ler_csv(gerar_editor.INVENTARIO)]
    faltam = [c for c in caminhos if gerar_editor.miniatura.falta(c)]
    em_paralelo(gerar_editor.miniatura, faltam)
    return len(faltam)


def folhas_a_mais(gp, g):
    """As folhas que o indice ja nao tem saem da pasta, como no caminho completo (que as apaga
    todas antes de refazer). A pasta e nossa, saida/previas. Devolve os nomes."""
    indice = ler_json(os.path.join(gp.DESTINO, "indice.json"), {})
    validas = set(indice.get("folhas") or [])
    fora = []
    if not validas:
        return fora
    for n in sorted(os.listdir(gp.DESTINO)):
        if re.match(r"^folha_\d+\.jpg$", n) and n not in validas:
            os.remove(os.path.join(gp.DESTINO, n))
            g["folhas"].pop(n, None)
            fora.append(n)
    return fora


# ------------------------------------------------------------------------------ os passos
class Parou(Exception):
    pass


class NadaDeNovo(Exception):
    pass


def motivos_para_correr(inventario, g, novidades, inv_antes, retomada, args):
    """Porque e que os passos tem de correr. Lista vazia = nao ha nada de novo.

    Conta: o que a vigia ve (fotos e musicas novas ou de outro tamanho), uma foto do inventario que
    saiu da pasta ou que mudou de data com o mesmo tamanho (trocada por outra do mesmo peso), uma
    corrida anterior que nao acabou, e um ficheiro de saida que falte. Nao conta o que e de outros
    scripts (a montagem, a pagina base): para isso ha o gerar_mesa.py, ou o --forcar.
    """
    motivos = []
    if getattr(args, "forcar", False):
        motivos.append("--forcar")
    if retomada:
        motivos.append("a corrida anterior nao acabou")
    fotos = novidades["fotos"]
    if fotos:
        motivos.append("%s: %s" % (plural(len(fotos), "foto nova ou trocada", "fotos novas ou trocadas"),
                                   ", ".join(x["nome"] for x in fotos[:4])))
    if novidades["musicas"]:
        motivos.append("%s: %s" % (plural(len(novidades["musicas"]), "musica nova", "musicas novas"),
                                   ", ".join(x["nome"] for x in novidades["musicas"][:4])))
    raizes = dict(inventario.PASTAS)
    sairam, mudaram = [], []
    for r in inv_antes:
        etiqueta, _, resto = r["pasta"].partition("/")
        if etiqueta not in raizes:
            continue
        caminho = os.path.join(raizes[etiqueta], resto.replace("/", os.sep), r["ficheiro"])
        try:
            ass = assinatura(caminho)
        except OSError:
            sairam.append(r["ficheiro"])
            continue
        v = g["medir"].get(chave(caminho))
        if v and v[0] != ass:
            mudaram.append(r["ficheiro"])
    if sairam:
        motivos.append("%s do inventario: %s" % (plural(len(sairam), "foto saiu", "fotos sairam"), ", ".join(sairam[:4])))
    if mudaram:
        motivos.append("%s: %s" % (plural(len(mudaram), "foto mudou de data ou de tamanho",
                                          "fotos mudaram de data ou de tamanho"), ", ".join(mudaram[:4])))
    for nome, caminho in (("data/inventario.csv", inventario.OUT),
                          ("data/finais.csv", os.path.join(REPO, "data", "finais.csv")),
                          ("data/editor_dados.js", os.path.join(REPO, "data", "editor_dados.js")),
                          ("data/estado_fotos.json", os.path.join(REPO, "data", "estado_fotos.json")),
                          ("saida/previas/indice.json", os.path.join(SAIDA, "previas", "indice.json")),
                          ("saida/mesa.html", PAGINA)):
        if not os.path.exists(caminho):
            motivos.append("falta %s" % nome)
    return motivos


def versoes_velhas(inventario, g):
    """As fotos cuja versao lanczos o consolidar recusou pela ALTERACAO (e de outra fotografia), e que
    ainda nao foram refeitas a partir do original que la esta agora. Linhas do inventario."""
    inv = {r["id"]: r for r in ler_csv(inventario.OUT)}
    velhas = []
    for f in ler_csv(os.path.join(REPO, "data", "finais.csv")):
        if "lanczos:alteracao" not in (f.get("recusadas") or ""):
            continue
        r = inv.get(f["id"])
        if not r:
            continue
        try:
            if g["refeitas"].get(r["id"]) == assinatura(r["caminho"]):
                continue
        except OSError:
            continue
        velhas.append(r)
    return velhas


class Fita(io.StringIO):
    """Onde fica o que o main() de cada script escreve. Alguns scripts fazem
    sys.stdout.reconfigure() ao serem importados, e um StringIO nao o tem."""

    def reconfigure(self, **_k):
        pass


PASSOS = []
_REGISTO = []


def _mostrar(nome, inicio, texto, erro=None):
    linhas = [l for l in (texto or "").replace("\r", "\n").splitlines() if l.strip()]
    for l in linhas[-8:]:
        dizer("    " + l.rstrip())
    segundos = time.time() - inicio
    _REGISTO.append("[%s] %.1f s\n%s\n" % (nome, segundos, texto or ""))
    PASSOS.append({"passo": nome, "segundos": round(segundos, 1), "fim": [l.strip() for l in linhas[-8:]],
                   "avisos": [l.strip() for l in linhas
                              if "AVISO" in l or "ERRO" in l or "FALHOU" in l or " por fazer: " in l]})
    if erro:
        dizer("    ERRO: %s" % erro)
        PASSOS[-1]["erro"] = str(erro)
        raise Parou("Parou no passo %s. Nada do que vem a seguir foi feito." % nome)
    dizer("    feito em %.1f s" % segundos)


def passo(nome, funcao, argv=()):
    """Corre o main() de um script aqui dentro, com o que ele escreve guardado."""
    dizer()
    dizer("[%d] %s" % (len(PASSOS) + 1, nome))
    inicio, fita, erro = time.time(), Fita(), None
    guardado = sys.argv
    sys.argv = [nome] + list(argv)
    try:
        with contextlib.redirect_stdout(fita):
            funcao()
    except SystemExit as e:
        if e.code not in (None, 0):
            erro = e.code
    except Exception as e:                          # noqa: BLE001 - diz-se qual foi e para-se
        erro = "%s: %s" % (type(e).__name__, e)
    finally:
        sys.argv = guardado
    _mostrar(nome, inicio, fita.getvalue(), erro)


def passo_a_parte(nome, *args):
    """Corre um script tal e qual, noutro processo, como o atualizar_fotos.py faz."""
    dizer()
    dizer("[%d] %s %s" % (len(PASSOS) + 1, nome, " ".join(args)))
    inicio = time.time()
    r = subprocess.run([PY, os.path.join(AQUI, nome)] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    erro = None
    if r.returncode != 0:
        erro = "codigo %d: %s" % (r.returncode, " / ".join((r.stderr or "").strip().splitlines()[-6:]))
    _mostrar(nome, inicio, r.stdout or "", erro)


# ------------------------------------------------------------------------- o que se publica
def publicavel():
    """{caminho publicado: {"bytes", "sha256"}} do que vai para o endereco da Mesa ao lado da pagina,
    mais a pagina, com a chave "mesa.html". As copias de som e de video chamam-se pelo conteudo
    (audio_para_mesa.py), por isso o nome chega e nao se leem outra vez."""
    saida = {}
    if os.path.exists(PAGINA):
        saida["mesa.html"] = {"bytes": os.path.getsize(PAGINA), "sha256": sha256_de(PAGINA)}
    previas = os.path.join(SAIDA, "previas")
    folhas = (ler_json(os.path.join(previas, "indice.json"), {}) or {}).get("folhas")
    if folhas is None and os.path.isdir(previas):
        folhas = sorted(n for n in os.listdir(previas) if re.match(r"^folha_\d+\.jpg$", n))
    # AS FOLHAS PUBLICAM-SE COM O CONTEUDO NO NOME (gerar_previas.nome_publicado), e o "de" diz de que
    # ficheiro do disco saem: e o nome que o gerar_mesa.py poe no indice da pagina. Uma folha que muda
    # passa a ser um ficheiro novo no endereco, e a antiga sai com null (lista_a_publicar).
    import gerar_previas
    for n in folhas or []:
        p = os.path.join(previas, n)
        if os.path.exists(p):
            sha = sha256_de(p)
            saida["previas/" + gerar_previas.nome_publicado(n, sha)] = {"bytes": os.path.getsize(p), "sha256": sha,
                                                                      "de": "previas/" + n}
    for pasta in ("audio", "video"):
        d = os.path.join(SAIDA, pasta)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if n.lower().endswith((".mp4", ".m4a")) and ".parte" not in n:
                saida["%s/%s" % (pasta, n)] = {"bytes": os.path.getsize(os.path.join(d, n)), "sha256": "nome"}
    return saida


def nulls_do_som():
    """As copias que o audio_para_mesa.py mandou tirar com null (saida/audio/publicar.json)."""
    lotes = ler_json(os.path.join(SAIDA, "audio", "publicar.json"), [])
    fora = []
    for lote in lotes if isinstance(lotes, list) else []:
        fora += [u for u, v in (lote.get("files") or {}).items() if v is None]
    return sorted(set(fora))


def lista_a_publicar(base, agora, tudo=False):
    """(ficheiros, tirar): o que mudou face ao que estava publicado, sem a pagina."""
    ficheiros = []
    # AS FOLHAS A FRENTE: a pagina pede-as pelo nome do conteudo, e tem de as encontrar na mesma publicacao em
    # que ela muda. Pela ordem do nome iam atras das copias de som, e com dois lotes ficavam no segundo.
    for u in sorted(agora, key=lambda x: (not x.startswith("previas/"), x)):
        if u == "mesa.html":
            continue
        antes = base.get(u)
        if tudo or antes is None or antes != agora[u]:
            origem = agora[u].get("de") or u          # o ficheiro do disco, que nas folhas tem outro nome
            ficheiros.append({"publicado": u, "origem": origem, "de": os.path.join(SAIDA, origem.replace("/", os.sep)),
                              "bytes": agora[u]["bytes"],
                              "porque": "tudo" if tudo and antes == agora[u] else ("novo" if antes is None else "mudou")})
    tirar = sorted(set(u for u in base if u not in agora and u != "mesa.html") | set(nulls_do_som()))
    tirar = [u for u in tirar if u not in agora]
    return ficheiros, tirar


def em_lotes(ficheiros, bytes_da_pagina):
    """Lotes de ate 60 MB e 250 ficheiros; a pagina vai no primeiro e conta para o peso dele."""
    lotes, atual, peso = [], [], bytes_da_pagina
    for x in ficheiros:
        if atual and (peso + x["bytes"] > LOTE_MAX or len(atual) >= 250):
            lotes.append(atual)
            atual, peso = [], 0
        atual.append(x)
        peso += x["bytes"]
    lotes.append(atual)
    saida = []
    for k, lote in enumerate(lotes):
        files = {x["publicado"]: {"from": x.get("origem") or x["publicado"],
                                  "contentType": TIPOS.get(os.path.splitext(x["publicado"])[1].lower(),
                                                           "application/octet-stream")} for x in lote}
        saida.append({"lote": k + 1, "com_pagina": k == 0, "n": len(lote),
                      "bytes": sum(x["bytes"] for x in lote) + (bytes_da_pagina if k == 0 else 0),
                      "files": files})
    return saida


# --------------------------------------------------------------------------------- avisos
def avisos_das_fotos(novas, inv, finais, consolidar):
    avisos = []
    por_hash = {}
    for r in inv:
        por_hash.setdefault(r["sha256"], []).append(r)
    for r in novas:
        iguais = [x for x in por_hash.get(r["sha256"], []) if x["id"] != r["id"]]
        if iguais:
            avisos.append({"tipo": "duplicado", "id": r["id"], "ficheiro": r["ficheiro"],
                           "igual_a": [{"id": x["id"], "pasta": x["pasta"], "ficheiro": x["ficheiro"]} for x in iguais],
                           "texto": "%s %s tem o mesmo conteudo (sha256) que %s. So se reporta: ficam as duas registadas."
                                    % (r["id"], r["ficheiro"],
                                       ", ".join("%s %s/%s" % (x["id"], x["pasta"], x["ficheiro"]) for x in iguais))})
        try:
            larg, alt = int(r["largura"]), int(r["altura"])
        except ValueError:
            continue
        fator = consolidar.fator_ampliacao(larg, alt)
        f = finais.get(r["id"]) or {}
        if max(larg, alt) < 400:
            avisos.append({"tipo": "pequena", "id": r["id"], "ficheiro": r["ficheiro"], "fator": round(fator, 2),
                           "texto": "%s %s tem %dx%d: e uma miniatura, a 15 metros nao se le."
                                    % (r["id"], r["ficheiro"], larg, alt)})
        elif fator > 1.0:
            como = "cresce com o Lanczos" if f.get("origem") == "lanczos" else "fica o original"
            if f.get("recusadas"):
                como = "fica o original, a guarda recusou a versao (%s)" % f["recusadas"]
            avisos.append({"tipo": "pequena", "id": r["id"], "ficheiro": r["ficheiro"], "fator": round(fator, 2),
                           "texto": "%s %s tem %dx%d e precisa de crescer %.2f vezes para a projecao: %s%s."
                                    % (r["id"], r["ficheiro"], larg, alt, fator, como,
                                       "; acima de 2 vezes fica mole" if fator > 2.0 else "")})
    return avisos


# ---------------------------------------------------------------------------------- a tranca
_FECHO = []                # o ficheiro trancado fica aberto ate o processo acabar


def trancar(quem="entrada rapida"):
    """Uma atualizacao das fotos de cada vez: duas a escrever o inventario e as folhas davam um estado
    misturado. Vale para a entrada rapida e para o atualizar_fotos.py, que pede a mesma tranca.

    A TRANCA E DO WINDOWS, e nao um ficheiro que se ve se existe (3 de outubro): com "existe? entao
    escrevo", duas corridas arrancadas no mesmo instante passavam as duas (14 em 20 ensaios). Aqui
    tranca-se um byte do ficheiro com o msvcrt, que so um processo consegue, e o Windows solta-o
    sozinho quando o processo acaba ou morre: uma corrida morta nunca prende a seguinte.
    """
    os.makedirs(CACHE, exist_ok=True)
    try:
        import msvcrt
    except ImportError:                                    # fora do Windows nao ha tranca
        return
    fh = open(FECHO, "a+b")
    try:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        fh.close()
        try:
            texto = io.open(TRANCA, encoding="utf-8").read().strip()
        except OSError:
            texto = ""
        sys.exit("Ja ha uma entrada rapida a correr (%s). Espera que acabe." % (texto or "outra atualizacao das fotos"))
    _FECHO.append(fh)
    try:
        with io.open(TRANCA, "w", encoding="utf-8") as txt:
            txt.write("%s, pid %d, desde %s" % (quem, os.getpid(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    except OSError:
        pass

    def destrancar():
        try:
            os.remove(TRANCA)
        except OSError:
            pass
        try:
            fh.close()
        except OSError:
            pass
    atexit.register(destrancar)


# Os scripts que escrevem o inventario, a FINAIS, as folhas ou a pagina. O atualizar_fotos.py pede a
# tranca de cima; os outros, corridos a mao ou por outra sessao (o gerar_mesa.py), so se veem na
# lista dos processos.
MEXEM = ("atualizar_fotos.py", "gerar_mesa.py", "inventario.py", "upscale.py", "consolidar.py",
         "gerar_editor.py", "gerar_montagens_editor.py", "estado_fotos.py", "gerar_previas.py")


def outros_a_mexer():
    """Os scripts de MEXEM que estao a correr NESTE repositorio noutro processo (nao este nem quem o
    chamou). Uma lista de nomes; vazia se nao houver ou se nao se conseguir perguntar ao Windows."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like 'py%'\" | "
             "ForEach-Object { '{0}|{1}|{2}' -f $_.ProcessId,$_.ParentProcessId,$_.CommandLine }"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
    except Exception:                                      # noqa: BLE001
        return []
    processos = {}
    for linha in (r.stdout or "").splitlines():
        partes = linha.strip().split("|", 2)
        if len(partes) == 3 and partes[0].isdigit():
            processos[int(partes[0])] = (int(partes[1]) if partes[1].isdigit() else 0, partes[2])
    meus, p = set(), os.getpid()
    while p in processos and p not in meus:                # este processo e os que o chamaram
        meus.add(p)
        p = processos[p][0]
    for pid, (pai, _linha) in processos.items():           # o py.exe e o python.exe sao o mesmo comando
        if pai in meus:
            meus.add(pid)
    aqui = os.path.normcase(AQUI)
    vistos = set()
    for pid, (pai, linha) in processos.items():
        if pid in meus:
            continue
        baixo = linha.lower().replace("/", "\\")
        for nome in MEXEM:
            m = re.search(r'(?:^|[\s"])([^\s"]*)' + re.escape(nome), baixo)
            if not m:
                continue
            # o caminho inteiro do script, ou "scripts\nome" corrido da raiz do repositorio (de fora
            # nao se sabe de que pasta: conta, que esperar a toa custa menos do que misturar)
            if os.path.join(aqui, nome) in baixo or m.group(1) in ("scripts\\", ".\\scripts\\", ""):
                vistos.add(nome)
    return sorted(vistos)


def esperar_pelos_outros(segundos=120):
    """Espera que os outros scripts que mexem nos mesmos ficheiros acabem. Devolve os que ainda la
    estavam no fim da espera (e ai a corrida segue, com aviso)."""
    limite = time.time() + segundos
    outros = outros_a_mexer()
    while outros and time.time() < limite:
        dizer("  a espera de %s, que esta a correr noutra sessao..." % ", ".join(outros))
        time.sleep(5)
        outros = outros_a_mexer()
    return outros


# ------------------------------------------------------------------------------- os modos
def marcar_publicado():
    agora = publicavel()
    escrever_json(PUBLICADO, {"quando": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              "ficheiros": agora}, indent=1)
    esquecidas = 0
    if nulls_do_som():
        import audio_para_mesa
        esquecidas = audio_para_mesa.publicado()
    dizer("Publicado: %d ficheiros em saida/ passam a contar como publicados%s."
          % (len(agora), (", e %d copias tiradas com null ficam esquecidas" % esquecidas) if esquecidas else ""))


def aquecer():
    """Enche a cache sem mudar nada: nem data/, nem saida/ (fora da cache), nem a pasta dos media."""
    import inventario
    import consolidar
    import gerar_editor
    import gerar_previas
    import estado_fotos
    trancar()
    g, relato = abrir_medidas(), novo_relato()
    ligar_inventario(inventario, g, relato)
    ligar_consolidar(consolidar, g, relato)
    ligar_editor(gerar_editor, relato)
    ligar_previas(gerar_previas, g, relato)
    inv = ler_csv(inventario.OUT)
    dizer("A aquecer a cache com as %d fotos do inventario. Nada muda fora de %s" % (len(inv), CACHE))

    t = time.time()
    # so as que ja estao no inventario e ja tem a miniatura de proxies/: assim o medir() nao escreve nada
    so = {chave(r["caminho"]) for r in inv
          if os.path.exists(r["caminho"]) and os.path.exists(os.path.join(REPO, r["proxy"].replace("/", os.sep)))}
    adiantar_inventario(inventario, g, relato, so=so)
    estado_fotos.por_registar(inv)
    guardar_medidas(g)
    dizer("  inventario: %d ficheiros lidos, %.0f s" % (relato["lidas"], time.time() - t))

    t = time.time()
    adiantar_consolidar(consolidar)                    # com --listar: mede e nao copia nem escreve o indice
    guardar_medidas(g)
    dizer("  consolidar: %d alteracoes e %d caras medidas, %.0f s" % (relato["medidas"], relato["caras"], time.time() - t))

    t = time.time()
    adiantar_editor(gerar_editor)
    a_serio = gerar_editor.SAIDA
    gerar_editor.SAIDA = os.path.join(CACHE, "_aquecer_editor_dados.js")
    try:
        with contextlib.redirect_stdout(Fita()):
            gerar_editor.main()
        igual = os.path.exists(a_serio) and sha256_de(a_serio) == sha256_de(gerar_editor.SAIDA)
    finally:
        if os.path.exists(gerar_editor.SAIDA):
            os.remove(gerar_editor.SAIDA)
        gerar_editor.SAIDA = a_serio
    dizer("  miniaturas: %d guardadas, %.0f s; o data/editor_dados.js em disco %s"
          % (relato["miniaturas"], time.time() - t,
             "e igual ao que sairia agora" if igual else "NAO e igual ao que sairia agora: a primeira corrida muda-o"))

    t = time.time()
    a_serio = gerar_previas.DESTINO
    gerar_previas.DESTINO = os.path.join(CACHE, "_aquecer_previas")
    try:
        with contextlib.redirect_stdout(Fita()):
            gerar_previas.main()
        iguais, total = 0, 0
        for nome, v in g["folhas"].items():
            total += 1
            p = os.path.join(a_serio, nome)
            if os.path.exists(p) and sha256_de(p) == v["sha256"]:
                iguais += 1
    finally:
        shutil.rmtree(gerar_previas.DESTINO, ignore_errors=True)
        gerar_previas.DESTINO = a_serio
    guardar_medidas(g)
    dizer("  previas: %d celulas guardadas, %.0f s; %d das %d folhas em disco sao iguais as que sairiam agora"
          % (relato["celulas"], time.time() - t, iguais, total))
    dizer("Cache pronta em %s" % CACHE)


def correr(args):
    import inventario
    import upscale
    import consolidar
    import gerar_editor
    import estado_fotos
    import gerar_previas
    import vigiar_pastas
    inicio = time.time()
    trancar()
    ainda_a_mexer = esperar_pelos_outros()
    g, relato = abrir_medidas(), novo_relato()
    ligar_inventario(inventario, g, relato)
    ligar_consolidar(consolidar, g, relato)
    ligar_editor(gerar_editor, relato)
    ligar_previas(gerar_previas, g, relato)

    # UMA COPIA A MEIO NAO SE LE. Quem chama isto pela vigia ja so vem com ficheiros parados, mas quem
    # o chama a mao pode apanhar o Explorador a meio: espera-se ate um minuto que tudo pare de crescer.
    # Um ficheiro VAZIO nao e uma copia a meio: nao cresce, e nao se espera por ele (sai nos avisos).
    novidades = vigiar_pastas.novidades(com_outros=True)
    limite = time.time() + 60
    while True:
        _quietos, a_mexer = vigiar_pastas.parados(novidades["fotos"] + novidades["musicas"], 1.0)
        a_mexer = [x for x in a_mexer if not vigiar_pastas.vazio(x["caminho"])]
        if not a_mexer or time.time() > limite:
            break
        dizer("  a espera de %s que ainda estao a ser copiados..." % plural(len(a_mexer), "ficheiro", "ficheiros"))
        time.sleep(2)
        novidades = vigiar_pastas.novidades(com_outros=True)

    # O QUE HAVIA ANTES, para dizer no fim o que entrou. UMA CORRIDA QUE NAO ACABOU (um passo que
    # falhou, um processo morto) ja deixou as fotos no inventario: a corrida seguinte via-as la e
    # dizia "ENTROU: 0 fotos" precisamente quando elas chegavam a pagina. O "antes" fica escrito
    # em por_acabar.json ao arrancar e so sai quando a corrida chega ao fim sem erro.
    inv_antes = {(r["pasta"], r["ficheiro"]): r for r in ler_csv(inventario.OUT)}
    musicas_novas = novidades["musicas"]
    por_acabar = ler_json(POR_ACABAR, None)
    retomada = isinstance(por_acabar, dict) and isinstance(por_acabar.get("inventario"), list)
    if retomada:
        inv_antes = {(r["pasta"], r["ficheiro"]): r for r in por_acabar["inventario"]}
        ja = {chave(x["caminho"]) for x in musicas_novas}
        musicas_novas = musicas_novas + [x for x in por_acabar.get("musicas") or []
                                         if chave(x["caminho"]) not in ja and os.path.exists(x["caminho"])]

    # SEM NADA DE NOVO NAO SE FAZ NADA. Os oito passos davam os mesmos ficheiros, mas com um build
    # novo: quem publicasse pelo manifesto acendia a barra "Ha uma versao mais nova" sem razao.
    motivos = motivos_para_correr(inventario, g, novidades, list(inv_antes.values()), retomada, args)
    nada_de_novo = not motivos
    if not nada_de_novo:
        escrever_json(POR_ACABAR, {
            "desde": (por_acabar or {}).get("desde") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "inventario": [{k: r.get(k, "") for k in ("id", "pasta", "ficheiro", "sha256")} for r in inv_antes.values()],
            "musicas": [{k: x[k] for k in ("nome", "caminho", "pasta", "ficheiro", "porque")} for x in musicas_novas]})
    registo = ler_json(PUBLICADO, None)
    primeira_vez = not (isinstance(registo, dict) and isinstance(registo.get("ficheiros"), dict))
    if primeira_vez:
        # sem registo de publicacao, conta-se que o que esta em saida/ ja esta publicado
        registo = {"quando": "antes da primeira entrada rapida", "ficheiros": publicavel()}
        escrever_json(PUBLICADO, registo, indent=1)
    base = registo["ficheiros"]

    dizer("Entrada rapida, %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if retomada:
        dizer("  a acabar a corrida de %s, que nao chegou ao fim" % por_acabar.get("desde"))
    dizer("  na 01-NOVAS: %s por registar%s; na pasta das musicas: %s"
          % (plural(sum(1 for x in novidades["fotos"] if x["porque"] == "nova"), "foto", "fotos"),
             (", " + plural(sum(1 for x in novidades["fotos"] if x["porque"] == "mudou"), "trocada", "trocadas"))
             if any(x["porque"] == "mudou" for x in novidades["fotos"]) else "",
             plural(len(musicas_novas), "nova", "novas")))

    erro = None
    fora = []
    refeitas = []
    try:
        if nada_de_novo:
            raise NadaDeNovo()
        dizer("  porque: %s" % "; ".join(motivos[:6]))
        passo("inventario.py", lambda: (adiantar_inventario(inventario, g, relato), inventario.main()))
        guardar_medidas(g)
        # A VERSAO AMPLIADA DE UMA FOTO TROCADA. Uma foto trocada por outra com o mesmo nome e as
        # mesmas dimensoes ficava em upscaled\ com a versao da foto ANTIGA (o upscale.py salta o
        # que ja existe com o tamanho certo), e a FINAIS, logo o filme, com a imagem velha. O
        # sinal e direto: o sha256 mudou no mesmo caminho. Refaz-se a versao so dessas, antes do
        # passo de sempre. O atualizar_fotos.py faz a mesma conta, para os dois darem o mesmo.
        trocadas = [r for r in ler_csv(inventario.OUT)
                    if inv_antes.get((r["pasta"], r["ficheiro"]))
                    and inv_antes[(r["pasta"], r["ficheiro"])]["sha256"] != r["sha256"]]
        if trocadas:
            ids = ",".join(r["id"] for r in trocadas)
            passo("upscale.py --so-ids %s" % ids, upscale.main, ["--so-ids", ids])
            for r in trocadas:
                g["refeitas"][r["id"]] = assinatura(r["caminho"])
        passo("upscale.py", upscale.main)
        passo("consolidar.py", lambda: (adiantar_consolidar(consolidar), consolidar.main()))
        guardar_medidas(g)
        # E A REDE POR BAIXO: se mesmo assim o consolidar recusar um lanczos pela ALTERACAO (a
        # troca aconteceu numa corrida que nao deixou rasto), refaz-se a versao e consolida-se
        # outra vez. Uma vez por original: se continuar recusada, nao e por estar velha.
        velhas = versoes_velhas(inventario, g)
        if velhas:
            ids = ",".join(r["id"] for r in velhas)
            passo("upscale.py --so-ids %s" % ids, upscale.main, ["--so-ids", ids])
            for r in velhas:
                g["refeitas"][r["id"]] = assinatura(r["caminho"])
                refeitas.append(r)
            passo("consolidar.py (outra vez)", lambda: (adiantar_consolidar(consolidar), consolidar.main()))
            guardar_medidas(g)
        passo("gerar_editor.py", lambda: (adiantar_editor(gerar_editor), gerar_editor.main()))
        passo_a_parte("gerar_montagens_editor.py")
        passo("estado_fotos.py", estado_fotos.main)
        passo("gerar_previas.py", gerar_previas.main)
        fora = folhas_a_mais(gerar_previas, g)
        guardar_medidas(g)
        if not args.sem_mesa:
            passo_a_parte("gerar_mesa.py")
    except NadaDeNovo:
        dizer()
        dizer("NADA DE NOVO: nenhum passo correu, e o build fica o que estava. (--forcar corre-os na mesma.)")
    except Parou as e:
        erro = str(e)
        dizer()
        dizer(erro)
    finally:
        guardar_medidas(g)
        os.makedirs(CACHE, exist_ok=True)
        with io.open(REGISTO, "w", encoding="utf-8") as fh:
            fh.write("\n".join(_REGISTO))

    # ------------------------------------------------------------------ o que entrou
    inv = ler_csv(inventario.OUT)
    finais = {r["id"]: r for r in ler_csv(os.path.join(REPO, "data", "finais.csv"))}
    previas = ler_json(os.path.join(SAIDA, "previas", "indice.json"), {}) or {}
    estado = ler_json(os.path.join(REPO, "data", "estado_fotos.json"), {}) or {}
    ids_antes = {r["id"]: r for r in inv_antes.values()}
    novas, mudadas, movidas = [], [], []
    for r in inv:
        antes = inv_antes.get((r["pasta"], r["ficheiro"]))
        if antes is None:
            # o inventario deixa o id acompanhar um ficheiro que mudou de pasta: essa nao e nova
            (movidas if r["id"] in ids_antes else novas).append(r)
        elif antes["sha256"] != r["sha256"]:
            mudadas.append(r)
    agora_chaves = {(r["pasta"], r["ficheiro"]) for r in inv}
    agora_ids = {r["id"] for r in inv}
    saidas = [r for k, r in inv_antes.items() if k not in agora_chaves and r["id"] not in agora_ids] if inv else []

    def da_foto(r):
        f = finais.get(r["id"]) or {}
        pos = (previas.get("pos") or {}).get(r["id"])
        x = {"id": r["id"], "ficheiro": r["ficheiro"], "pasta": r["pasta"],
             "largura": int(r["largura"]), "altura": int(r["altura"]), "ano": r["ano"],
             "final": f.get("final", ""), "origem": f.get("origem", "")}
        if pos and previas.get("folhas"):
            x["folha"] = "previas/" + previas["folhas"][pos[0]]
        return x

    avisos = []
    if ainda_a_mexer:
        avisos.append({"tipo": "passo", "texto": "Enquanto isto correu havia outra sessao a correr %s, que mexe nos "
                       "mesmos ficheiros: confirma a pagina antes de publicar, ou corre outra vez com --forcar."
                       % ", ".join(ainda_a_mexer)})
    avisos += avisos_das_fotos(novas + mudadas, inv, finais, consolidar)
    for r in refeitas:
        f = finais.get(r["id"]) or {}
        avisos.append({"tipo": "refeita", "id": r["id"], "ficheiro": r["ficheiro"],
                       "texto": "%s %s: a versao ampliada que havia era de outra fotografia (a foto foi trocada "
                                "por outra com o mesmo nome). Foi refeita; ficou %s%s."
                                % (r["id"], r["ficheiro"], f.get("origem", "?"),
                                   (", recusada: " + f["recusadas"]) if f.get("recusadas") else "")})
    ja_vistos = {k: v for k, v in (ler_json(JA_VISTOS, {}) or {}).items() if os.path.exists(k)}
    for caminho, porque in relato["ilegiveis"]:
        dica = ""
        if caminho.lower().endswith((".heic", ".heif")):
            dica = " As .heic do iPhone nao se abrem neste PC: exporta-a em JPEG e larga outra vez."
        avisos.append({"tipo": "nao_se_le", "ficheiro": os.path.basename(caminho), "caminho": caminho,
                       "texto": "%s nao se consegue abrir (%s): nao entrou.%s" % (os.path.basename(caminho), porque, dica)})
        try:
            ja_vistos[chave(caminho)] = assinatura(caminho) + ["nao se le: " + porque]
        except OSError:
            pass
    for x in novidades["outros"]:
        k = chave(x["caminho"])
        try:
            ass = assinatura(x["caminho"])
        except OSError:
            continue
        if k in ja_vistos and list(ja_vistos[k][:2]) == ass:
            continue                                 # ja foi dito numa corrida anterior
        if x["porque"] == "video":
            avisos.append({"tipo": "video", "ficheiro": x["nome"], "caminho": x["caminho"],
                           "texto": "%s e um video: aparece na Mesa em «Videos por decidir» e so entra no filme "
                                    "pelo chat (decisao 083)." % x["nome"]})
        else:
            avisos.append({"tipo": "nao_se_le", "ficheiro": x["nome"], "caminho": x["caminho"],
                           "texto": "%s tem um formato que nem o inventario nem a Mesa leem: nao entrou." % x["nome"]})
        ja_vistos[k] = ass + [x["porque"]]

    # as musicas: entrou a que tem copia no indice do som
    musicas = []
    if musicas_novas and not args.sem_mesa:
        import audio_para_mesa
        if tuple(audio_para_mesa.EXT_SOM) != tuple(vigiar_pastas.EXT_MUSICA):
            avisos.append({"tipo": "passo", "texto": "As extensoes de som do vigiar_pastas.py ja nao sao as do "
                           "audio_para_mesa.py (%s): acerta o EXT_MUSICA." % ", ".join(audio_para_mesa.EXT_SOM)})
        ind = ler_json(audio_para_mesa.INDICE, {}) or {}
        originais, copias = ind.get("originais") or {}, ind.get("copias") or {}
        por_sha = {}
        for k, v in originais.items():
            por_sha.setdefault(v.get("sha1"), []).append(k)
        for x in musicas_novas:
            o = originais.get(chave(x["caminho"]))
            c = copias.get(audio_para_mesa._id_da_copia(o["sha1"], None)) if o else None
            if o and c and os.path.exists(os.path.join(audio_para_mesa.PASTA_AUDIO, c["ficheiro"])):
                musicas.append({"ficheiro": x["ficheiro"], "pasta": x["pasta"], "copia": "audio/" + c["ficheiro"],
                                "duracao": c.get("duracao"), "bytes": c.get("bytes")})
                iguais = [k for k in por_sha.get(o["sha1"], []) if k != chave(x["caminho"]) and os.path.exists(k)]
                if iguais:
                    avisos.append({"tipo": "duplicado", "ficheiro": x["ficheiro"], "igual_a": iguais,
                                   "texto": "%s tem o mesmo conteudo (sha1) que %s. So se reporta."
                                            % (x["ficheiro"], ", ".join(iguais))})
                continue
            if o:
                texto = "%s nao ficou com copia de som: o ffmpeg nao a conseguiu ler. Nao toca na Mesa." % x["nome"]
                tipo = "copia_falhou"
            else:
                texto = ("%s nao entrou: a Mesa encontra as musicas pelo nome do ficheiro, e ja ha outra com este "
                         "nome noutra pasta. Muda-lhe o nome." % x["nome"])
                tipo = "nome_repetido"
            avisos.append({"tipo": tipo, "ficheiro": x["nome"], "caminho": x["caminho"], "texto": texto})
            try:
                ja_vistos[chave(x["caminho"])] = assinatura(x["caminho"]) + [tipo]
            except OSError:
                pass
    escrever_json(JA_VISTOS, ja_vistos, indent=1)

    if estado.get("espera"):
        avisos.append({"tipo": "estado", "texto": "A espera de melhoria, %s: %s" % (
            plural(len(estado["espera"]), "foto", "fotos"),
            ", ".join("%s (%s)" % (e["f"], e["m"]) for e in estado["espera"][:6]))})
    if estado.get("por_registar"):
        avisos.append({"tipo": "estado", "texto": "Por registar na 01-NOVAS, %s: %s" % (
            plural(estado["por_registar"], "imagem", "imagens"),
            ", ".join(estado.get("por_registar_lista", [])[:6]))})
    for r in saidas:
        avisos.append({"tipo": "saiu", "id": r["id"], "ficheiro": r["ficheiro"],
                       "texto": "%s %s ja nao esta em %s: saiu do inventario. Se estiver na montagem, a Mesa fica "
                                "sem ela, e se o ficheiro voltar entra como foto nova, com outro id."
                                % (r["id"], r["ficheiro"], r["pasta"])})
    for passo_feito in PASSOS:
        for l in passo_feito["avisos"]:
            if " por fazer: " in l:
                # e do audio_para_mesa.py, que corre tal e qual: uma musica igual a outra com outro
                # nome so fica com copia na corrida seguinte, e um ficheiro que o ffmpeg nao le nunca
                avisos.append({"tipo": "som", "passo": passo_feito["passo"],
                               "texto": "Ha copias de som por fazer (%s). Se for uma musica igual a outra com "
                                        "outro nome, a copia faz-se na corrida seguinte: py -3.11 "
                                        "scripts/entrada_rapida.py --forcar. Se for um ficheiro que nao e musica "
                                        "ou esta vazio, tira-se da pasta." % l.split(" por fazer: ", 1)[1]})
                continue
            avisos.append({"tipo": "passo", "passo": passo_feito["passo"], "texto": l})

    # ------------------------------------------------------------------ o que se publica
    agora = publicavel()
    ficheiros, tirar = lista_a_publicar(base, agora, tudo=args.tudo)
    pagina_bytes = agora.get("mesa.html", {}).get("bytes", 0)
    pagina_mudou = args.tudo or base.get("mesa.html") != agora.get("mesa.html")
    grandes = [x["publicado"] for x in ficheiros if x["bytes"] > FICHEIRO_MAX]
    if grandes:
        avisos.append({"tipo": "limite", "texto": "Acima de 15 MB por ficheiro: %s" % ", ".join(grandes)})
    if len(agora) > FICHEIROS_MAX:
        avisos.append({"tipo": "limite", "texto": "O endereco fica com %d ficheiros, e o limite sao %d."
                                                  % (len(agora), FICHEIROS_MAX)})
    lotes = em_lotes(ficheiros, pagina_bytes)
    if tirar:
        lotes[0]["files"].update({u: None for u in tirar})

    manifesto = {
        "feito": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "segundos": round(time.time() - inicio, 1),
        "erro": erro,
        "nada_de_novo": nada_de_novo,
        "porque": motivos,
        "build": estado.get("build"),
        "fotos": estado.get("total", len(inv)),
        "entrou": {"fotos": [da_foto(r) for r in novas], "fotos_mudadas": [da_foto(r) for r in mudadas],
                   "fotos_movidas": [da_foto(r) for r in movidas],
                   "fotos_saidas": [{"id": r["id"], "ficheiro": r["ficheiro"], "pasta": r["pasta"]} for r in saidas],
                   "musicas": musicas},
        "avisos": avisos,
        "publicar": {
            "pagina": {"de": PAGINA, "bytes": pagina_bytes, "mudou": bool(pagina_mudou)},
            "root": SAIDA,
            "ficheiros": ficheiros,
            "tirar": tirar,
            "bytes": pagina_bytes + sum(x["bytes"] for x in ficheiros),
            "lotes": lotes,
            "no_endereco": len(agora),
            "desde": registo.get("quando"),
            "nota": ("A pagina publica-se com file_path; os ficheiros de cada lote com `files` e root = publicar.root, "
                     "para o mesmo endereco. Os null tiram do endereco o que deixou de servir: antes, listar os "
                     "ficheiros do endereco e deixar so os null dos que la estao. Publicar primeiro, ler "
                     "montagem/estado2 depois, e so entao escrever montagem/publicacao. No fim: "
                     "py -3.11 scripts/entrada_rapida.py --publicado"),
        },
        "publicacao": {"documento": "montagem/publicacao",
                       "dados": {"build": estado.get("build"), "quando": "a hora da escrita",
                                 "fotos": estado.get("total", len(inv))}},
        "passos": [{k: p[k] for k in p if k != "avisos"} for p in PASSOS],
        "cache": {"fotos_lidas": relato["lidas"], "alteracoes_medidas": relato["medidas"],
                  "caras_medidas": relato["caras"], "finais_copiadas": relato["finais_copiadas"],
                  "finais_iguais": relato["finais_iguais"], "miniaturas_feitas": relato["miniaturas"],
                  "celulas_feitas": relato["celulas"], "folhas_feitas": sorted(relato["folhas_feitas"]),
                  "folhas_iguais": relato["folhas_iguais"], "folhas_tiradas": fora},
    }
    escrever_json(MANIFESTO, manifesto, indent=1)

    dizer()
    dizer("ENTROU: %s%s, %s" % (plural(len(novas), "foto", "fotos"),
                                (" (e %s)" % plural(len(mudadas), "trocada", "trocadas")) if mudadas else "",
                                plural(len(musicas), "musica", "musicas")))
    for x in manifesto["entrou"]["fotos"] + manifesto["entrou"]["fotos_mudadas"]:
        dizer("  %s  %-44s %dx%d  %s  %s" % (x["id"], x["ficheiro"][:44], x["largura"], x["altura"],
                                           x["origem"], x.get("folha", "")))
    for x in musicas:
        dizer("  musica  %-40s %s" % (x["ficheiro"][:40], x["copia"]))
    for x in manifesto["entrou"]["fotos_movidas"]:
        dizer("  mudou de pasta, com o mesmo id: %s  %s -> %s" % (x["id"], x["ficheiro"][:44], x["pasta"]))
    if saidas:
        dizer("SAIU DA PASTA: %s (sai do inventario e da Mesa; na FINAIS nada se apaga)"
              % ", ".join("%s %s" % (r["id"], r["ficheiro"]) for r in saidas[:8]))
    if avisos:
        dizer("AVISOS: %d" % len(avisos))
        for a in avisos[:20]:
            dizer("  [%s] %s" % (a["tipo"], a["texto"]))
        if len(avisos) > 20:
            dizer("  e mais %d, no manifesto" % (len(avisos) - 20))
    dizer("PUBLICAR: a pagina (%.1f MB) e %s, %.1f MB ao todo, em %s%s"
          % (pagina_bytes / MB, plural(len(ficheiros), "ficheiro", "ficheiros"), manifesto["publicar"]["bytes"] / MB,
             plural(len(lotes), "lote", "lotes"), (", e %d a tirar com null" % len(tirar)) if tirar else ""))
    dizer("  folhas: %d refeitas, %d ficaram como estavam; FINAIS: %d copiadas, %d ja la estavam iguais"
          % (len(relato["folhas_feitas"]), relato["folhas_iguais"], len(relato["finais_copiadas"]),
             relato["finais_iguais"]))
    dizer("BUILD: %s, %s fotos" % (manifesto["build"], manifesto["fotos"]))
    dizer("Manifesto: %s  (%.0f s)" % (MANIFESTO, time.time() - inicio))
    if erro:
        return 1
    try:
        os.remove(POR_ACABAR)                       # chegou ao fim: a proxima corrida parte do que ha agora
    except OSError:
        pass
    if nada_de_novo and not ficheiros and not tirar and not pagina_mudou:
        dizer("Nada para publicar: o que esta em saida/ e o que foi publicado.")
    elif nada_de_novo:
        dizer("Nada de novo nas pastas, mas o que esta acima ainda nao foi dado como publicado (--publicado).")
    else:
        dizer("Pronto neste computador. Falta publicar a Mesa, escrever montagem/publicacao e correr o --publicado.")
    return 0


def main():
    global FIOS
    sys.stdout.reconfigure(encoding="utf-8")
    import argparse
    ap = argparse.ArgumentParser(description="Fotos e musicas novas prontas para publicar na Mesa.")
    ap.add_argument("--aquecer", action="store_true", help="so enche a cache, sem mudar nada")
    ap.add_argument("--publicado", action="store_true", help="depois de publicar: o que esta em saida/ e o publicado")
    ap.add_argument("--tudo", action="store_true", help="a lista a publicar leva tudo, e nao so o que mudou")
    ap.add_argument("--forcar", action="store_true", help="corre os passos mesmo sem nada de novo nas pastas")
    ap.add_argument("--sem-mesa", action="store_true", help="para antes do gerar_mesa.py (para testes)")
    ap.add_argument("--fios", type=int, default=FIOS,
                    help="quantas fotos se leem e quantas folhas se fazem ao mesmo tempo (%d)" % FIOS)
    args = ap.parse_args()
    FIOS = max(1, args.fios)
    if args.publicado:
        marcar_publicado()
        return 0
    if args.aquecer:
        aquecer()
        return 0
    return correr(args)


if __name__ == "__main__":
    sys.exit(main())
