# -*- coding: utf-8 -*-
"""Vigia a 01-NOVAS e a pasta das musicas, e diz quando ha ficheiros novos ja parados.

O Tiago, 3 de outubro, vespera do casamento: "a possibilidade de colocar fotos na pasta e
elas entrarem logo na Mesa de Montagem, e igual para as musicas". Este script e a primeira
metade: ve o que ele largou. A segunda e o scripts/entrada_rapida.py, que poe tudo pronto
para publicar. Este aqui SO LE: nao regista, nao copia, nao apaga, nao escreve em lado
nenhum.

O QUE E "NOVO":
  fotos    o que esta na 01-NOVAS (com subpastas) e nao esta no data/inventario.csv, pela
           pasta e pelo nome, com as regras do inventario.py: as mesmas extensoes, e dentro
           de uma pasta "<nome>_files" so o que for fotografia a serio (600 px de lado).
           Uma foto que la esta mas mudou de tamanho tambem conta: foi trocada por outra.
  musicas  o que esta na 02-NOVAS-MUSICAS (com subpastas) e nao esta no indice das copias
           de som da Mesa, saida/audio/indice.json, pelo caminho. Uma que la esta mas mudou
           de tamanho ou de data tambem conta.
  O que a entrada rapida ja viu e nao conseguiu por na Mesa (um formato que nao se le, uma
  musica com o nome de outra) nao volta a ser dito: fica em
  saida/_cache/entrada_rapida/ja_vistos.json, que e ela que escreve.

"JA PARADO": o tamanho e a data nao mudam ha --parado segundos (3 por omissao) e o ficheiro
deixa-se abrir. Uma copia a meio nao conta, e um lote so se diz quando TODOS os ficheiros
novos estao parados, para tres fotos largadas juntas darem uma linha e nao tres. Se algum
continuar a mexer ao fim de --espera-max segundos (120), dizem-se os que ja pararam.

O QUE ESCREVE, uma linha por lote, e continua a vigiar:

    NOVO: 3 fotos, 1 musica: 02.10.2026/IMG_1.jpg | IMG_2.jpg | Clara/x.png | Tema.mp3

Os nomes sao relativos a pasta vigiada, separados por " | " (ha nomes com virgulas). Um
ficheiro que nao e foto nem musica e aparece enquanto se vigia (um video, um formato que
nao se le) vai na mesma linha como "outro", para se poder dizer ao Tiago. A primeira linha
e sempre "VIGIA: ...", com o que ja era conhecido.

COM --correr, a seguir a cada linha NOVO corre o scripts/entrada_rapida.py e escreve outra linha:

    PRONTO: build 20261003-153012, 744 fotos; entraram 3 fotos e 1 musica; a publicar a pagina e
            28 ficheiros (31.3 MB); 2 avisos; 55 s; manifesto C:\\casamento-video\\saida\\entrada_rapida.json
    FALHOU: a entrada rapida saiu com o codigo 1 ao fim de 12 s: Parou no passo ...

(tudo numa linha). Publicar continua a ser com a ferramenta Artifact, a partir do manifesto.

Uso:
    py -3.11 scripts/vigiar_pastas.py                 vigia ate o pararem (Ctrl+C)
    py -3.11 scripts/vigiar_pastas.py --correr        vigia, e a cada lote deixa tudo pronto para publicar
    py -3.11 scripts/vigiar_pastas.py --uma-vez       diz o que ha de novo e sai
    py -3.11 scripts/vigiar_pastas.py --uma-vez --json
    opcoes: --intervalo 2  --parado 3  --espera-max 120
            --fotos PASTA  --musicas PASTA  --inventario CSV  --indice-som JSON
"""
import argparse
import csv
import io
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

import inventario  # noqa: E402  as extensoes, a regra das pastas "_files" e os caminhos sao os dele

ETIQUETA_FOTOS = "01-NOVAS"
FOTOS = dict(inventario.PASTAS)[ETIQUETA_FOTOS]
MUSICAS = os.path.join(inventario.BASE, "02-NOVAS-MÚSICAS")
INVENTARIO = inventario.OUT
INDICE_SOM = os.path.join(REPO, "saida", "audio", "indice.json")
JA_VISTOS = os.path.join(REPO, "saida", "_cache", "entrada_rapida", "ja_vistos.json")

# As extensoes que a Mesa toca: as do audio_para_mesa.EXT_SOM, que sao as do
# montar_da_mesa.caminhos_de_musica(). A entrada rapida confirma que continuam iguais.
EXT_MUSICA = (".mp3", ".wav", ".m4a", ".wma", ".flac", ".ogg")
# Os videos da 01-NOVAS nao entram sozinhos (decisao 083: passam pelo Tiago no chat), mas a
# Mesa mostra-os em "Videos por decidir"; as extensoes sao as do gerar_mesa.EXT_VIDEO.
EXT_VIDEO = (".mp4", ".mov", ".m4v", ".avi", ".mkv", ".wmv")
# O que o Windows e as paginas guardadas deixam nas pastas e nunca e para avisar.
EXT_CALADAS = (".db", ".ini", ".txt", ".html", ".htm", ".url", ".lnk", ".json", ".js", ".css",
               ".tmp", ".crdownload", ".part", ".partial", ".download")


def chave(caminho):
    """O caminho como o audio_para_mesa o guarda no indice: inteiro, em minusculas."""
    return os.path.normcase(os.path.abspath(caminho))


def assinatura(caminho):
    st = os.stat(caminho)
    return [st.st_size, st.st_mtime_ns]


def ler_inventario(caminho=None):
    """{(pasta, ficheiro): bytes} do inventario. Vazio se ainda nao existir."""
    caminho = caminho or INVENTARIO
    conhecidas = {}
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                try:
                    conhecidas[(r["pasta"], r["ficheiro"])] = int(r["bytes"])
                except (KeyError, ValueError):
                    conhecidas[(r.get("pasta", ""), r.get("ficheiro", ""))] = -1
    return conhecidas


def ler_indice_som(caminho=None):
    """{caminho em minusculas: [tamanho, mtime]} dos originais que ja tem copia para a Mesa."""
    caminho = caminho or INDICE_SOM
    try:
        with io.open(caminho, encoding="utf-8") as fh:
            ind = json.load(fh)
        return {k: [v.get("tamanho"), v.get("mtime")] for k, v in (ind.get("originais") or {}).items()}
    except (OSError, ValueError, AttributeError):
        return {}


def ler_ja_vistos(caminho=None):
    """{caminho em minusculas: [tamanho, mtime, porque]} do que a entrada rapida viu e nao pos na Mesa."""
    caminho = caminho or JA_VISTOS
    try:
        with io.open(caminho, encoding="utf-8") as fh:
            return {k: list(v) for k, v in json.load(fh).items()}
    except (OSError, ValueError, AttributeError, TypeError):
        return {}


_A_SERIO = {}


def _a_serio(caminho):
    """inventario.foto_a_serio(), uma vez por ficheiro e por tamanho: sao centenas de cromos."""
    try:
        k = (chave(caminho),) + tuple(assinatura(caminho))
    except OSError:
        return False
    if k not in _A_SERIO:
        _A_SERIO[k] = bool(inventario.foto_a_serio(caminho))
    return _A_SERIO[k]


def _percorrer(raiz):
    """(pasta relativa com barras, nome, caminho, dentro de uma pasta _files) de tudo o que la esta."""
    for base, dirs, ficheiros in os.walk(raiz):
        dirs.sort()
        rel = os.path.relpath(base, raiz)
        rel = "" if rel == "." else rel.replace("\\", "/")
        dentro_de_files = os.path.basename(base).endswith("_files")
        for nome in sorted(ficheiros):
            yield rel, nome, os.path.join(base, nome), dentro_de_files


def novidades(fotos=None, musicas=None, inventario_csv=None, indice_som=None, com_outros=False):
    """O que ha de novo nas duas pastas, sem olhar a se ja parou.

    Devolve {"fotos": [...], "musicas": [...], "outros": [...]}, cada item
    {"nome" (relativo a pasta vigiada), "caminho", "pasta", "ficheiro", "porque"}.
    `porque` e "nova" ou "mudou". Os "outros" (videos e formatos que nao se leem) so vem com
    com_outros=True, e nunca os de dentro de uma pasta "_files".
    """
    fotos = fotos or FOTOS
    musicas = musicas or MUSICAS
    conhecidas = ler_inventario(inventario_csv)
    com_copia = ler_indice_som(indice_som)
    vistos = ler_ja_vistos()
    saida = {"fotos": [], "musicas": [], "outros": []}

    def ja_visto(caminho):
        v = vistos.get(chave(caminho))
        if not v:
            return False
        try:
            return list(v[:2]) == assinatura(caminho)      # [tamanho, data, porque]
        except OSError:
            return True

    if os.path.isdir(fotos):
        for rel, nome, caminho, dentro_de_files in _percorrer(fotos):
            pasta = ETIQUETA_FOTOS if not rel else "%s/%s" % (ETIQUETA_FOTOS, rel)
            item = {"nome": (rel + "/" if rel else "") + nome, "caminho": caminho,
                    "pasta": pasta, "ficheiro": nome}
            baixo = nome.lower()
            if baixo.endswith(inventario.EXT):
                registada = conhecidas.get((pasta, nome))
                if registada is None:
                    if dentro_de_files and not _a_serio(caminho):
                        continue
                    if ja_visto(caminho):
                        continue
                    saida["fotos"].append(dict(item, porque="nova"))
                else:
                    try:
                        tamanho = os.path.getsize(caminho)
                    except OSError:
                        continue
                    if registada >= 0 and tamanho != registada:
                        saida["fotos"].append(dict(item, porque="mudou"))
            elif com_outros and not dentro_de_files and "_files" not in rel:
                if baixo.endswith(EXT_CALADAS) or nome.startswith((".", "~$")) or "." not in nome:
                    continue
                tipo = "video" if baixo.endswith(EXT_VIDEO) else "nao se le"
                saida["outros"].append(dict(item, porque=tipo))

    if os.path.isdir(musicas):
        etiqueta = os.path.basename(os.path.normpath(musicas))
        for rel, nome, caminho, dentro_de_files in _percorrer(musicas):
            # o montar_da_mesa.caminhos_de_musica() salta tudo o que tenha "_files" no caminho
            if dentro_de_files or "_files" in rel:
                continue
            item = {"nome": (rel + "/" if rel else "") + nome, "caminho": caminho,
                    "pasta": etiqueta if not rel else "%s/%s" % (etiqueta, rel), "ficheiro": nome}
            baixo = nome.lower()
            if baixo.endswith(EXT_MUSICA):
                guardado = com_copia.get(chave(caminho))
                if guardado is None:
                    if ja_visto(caminho):
                        continue
                    saida["musicas"].append(dict(item, porque="nova"))
                else:
                    try:
                        if list(guardado) != assinatura(caminho) and not ja_visto(caminho):
                            saida["musicas"].append(dict(item, porque="mudou"))
                    except OSError:
                        continue
            elif com_outros:
                if baixo.endswith(EXT_CALADAS) or nome.startswith((".", "~$")) or "." not in nome:
                    continue
                saida["outros"].append(dict(item, porque="nao se le"))
    return saida


def abre(caminho):
    """Deixa-se abrir e tem alguma coisa la dentro. O Explorador tranca o destino enquanto copia."""
    try:
        with open(caminho, "rb") as fh:
            return len(fh.read(1)) == 1
    except OSError:
        return False


def parados(itens, segundos):
    """Os itens cujo tamanho e data nao mudam durante `segundos`, e os que ainda mexem."""
    antes = {}
    for x in itens:
        try:
            antes[x["caminho"]] = assinatura(x["caminho"])
        except OSError:
            antes[x["caminho"]] = None
    if itens and segundos > 0:
        time.sleep(segundos)
    quietos, a_mexer = [], []
    for x in itens:
        try:
            agora = assinatura(x["caminho"])
        except OSError:
            agora = None
        if agora is not None and agora == antes[x["caminho"]] and abre(x["caminho"]):
            quietos.append(x)
        else:
            a_mexer.append(x)
    return quietos, a_mexer


def plural(n, um, varios):
    return "%d %s" % (n, um if n == 1 else varios)


def linha_do_lote(fotos, musicas, outros=()):
    partes = [plural(len(fotos), "foto", "fotos"), plural(len(musicas), "musica", "musicas")]
    if outros:
        partes.append(plural(len(outros), "outro", "outros"))
    nomes = [x["nome"] for x in fotos] + [x["nome"] for x in musicas]
    nomes += ["%s (%s)" % (x["nome"], "video, fica por decidir" if x["porque"] == "video"
                           else "formato que nao se le") for x in outros]
    return "NOVO: %s: %s" % (", ".join(partes), " | ".join(nomes))


def json_do_lote(fotos, musicas, outros=()):
    def limpo(lista):
        return [{k: x[k] for k in ("nome", "pasta", "ficheiro", "caminho", "porque")} for x in lista]
    return json.dumps({"fotos": limpo(fotos), "musicas": limpo(musicas), "outros": limpo(outros)},
                      ensure_ascii=False)


def dizer(texto):
    print(texto)
    sys.stdout.flush()


def correr_entrada():
    """Corre o scripts/entrada_rapida.py e diz numa linha como ficou (so com --correr)."""
    import subprocess
    inicio = time.time()
    r = subprocess.run([sys.executable, os.path.join(AQUI, "entrada_rapida.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        with io.open(os.path.join(REPO, "saida", "entrada_rapida.json"), encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError):
        m = None
    if r.returncode != 0 or not m or m.get("erro"):
        ultima = [l for l in (r.stdout or "").splitlines() + (r.stderr or "").splitlines() if l.strip()][-1:]
        dizer("FALHOU: a entrada rapida saiu com o codigo %d ao fim de %.0f s: %s"
              % (r.returncode, time.time() - inicio, (m or {}).get("erro") or " ".join(ultima)))
        return
    dizer("PRONTO: build %s, %s fotos; entraram %s e %s; a publicar a pagina e %s (%.1f MB); %s; %.0f s; manifesto %s"
          % (m.get("build"), m.get("fotos"), plural(len(m["entrou"]["fotos"]), "foto", "fotos"),
             plural(len(m["entrou"]["musicas"]), "musica", "musicas"),
             plural(len(m["publicar"]["ficheiros"]), "ficheiro", "ficheiros"), m["publicar"]["bytes"] / 1048576.0,
             plural(len(m["avisos"]), "aviso", "avisos"), time.time() - inicio,
             os.path.join(REPO, "saida", "entrada_rapida.json")))


def uma_vez(args):
    n = novidades(args.fotos, args.musicas, args.inventario, args.indice_som)
    todos = n["fotos"] + n["musicas"]
    quietos, a_mexer = parados(todos, args.parado if todos else 0)
    fotos = [x for x in n["fotos"] if x in quietos]
    musicas = [x for x in n["musicas"] if x in quietos]
    if args.json:
        dizer(json_do_lote(fotos, musicas))
    elif fotos or musicas:
        dizer(linha_do_lote(fotos, musicas))
    else:
        dizer("NADA DE NOVO")
    if a_mexer and not args.json:
        dizer("A COPIAR: %s ainda a mexer: %s" % (plural(len(a_mexer), "ficheiro", "ficheiros"),
                                                  " | ".join(x["nome"] for x in a_mexer)))
    return 0


def vigiar(args):
    ditos = {}            # caminho -> assinatura com que ja foi dito
    pendentes = {}        # caminho -> [assinatura, desde quando esta assim]
    primeiro_parado = None
    inicio = novidades(args.fotos, args.musicas, args.inventario, args.indice_som, com_outros=True)
    # Os videos e os formatos que nao se leem que JA la estavam nao sao noticia: so os que chegarem.
    for x in inicio["outros"]:
        try:
            ditos[x["caminho"]] = assinatura(x["caminho"])
        except OSError:
            pass
    dizer("VIGIA: %s e %s, de %g em %g s; no inventario %d fotos, no indice do som %d originais%s"
          % (args.fotos or FOTOS, args.musicas or MUSICAS, args.intervalo, args.intervalo,
             len(ler_inventario(args.inventario)), len(ler_indice_som(args.indice_som)),
             "" if os.path.isdir(args.musicas or MUSICAS) else " (a pasta das musicas nao existe)"))
    while True:
        try:
            n = novidades(args.fotos, args.musicas, args.inventario, args.indice_som, com_outros=True)
        except OSError as erro:                 # uma pasta a ser mexida a meio da leitura
            dizer("AVISO: nao consegui ler as pastas (%s); volto a tentar" % erro)
            time.sleep(args.intervalo)
            continue
        agora = time.time()
        vivos = set()
        por_dizer = {"fotos": [], "musicas": [], "outros": []}
        a_mexer = 0
        for tipo in ("fotos", "musicas", "outros"):
            for x in n[tipo]:
                c = x["caminho"]
                try:
                    ass = assinatura(c)
                except OSError:
                    continue
                if ditos.get(c) == ass:
                    continue
                vivos.add(c)
                p = pendentes.get(c)
                if not p or p[0] != ass:
                    pendentes[c] = [ass, agora]
                    a_mexer += 1
                elif agora - p[1] < args.parado:
                    a_mexer += 1
                elif abre(c):
                    por_dizer[tipo].append((x, ass))
                elif agora - p[1] < args.espera_max:
                    a_mexer += 1              # parado mas vazio ou trancado: ainda pode ser uma copia
                # senao esta vazio ou trancado ha muito tempo, e nao prende o lote dos outros
        for c in list(pendentes):
            if c not in vivos:
                del pendentes[c]
        ha = por_dizer["fotos"] or por_dizer["musicas"] or por_dizer["outros"]
        if ha and primeiro_parado is None:
            primeiro_parado = agora
        if not ha:
            primeiro_parado = None
        if ha and (a_mexer == 0 or agora - primeiro_parado >= args.espera_max):
            fotos = [x for x, _ in por_dizer["fotos"]]
            musicas = [x for x, _ in por_dizer["musicas"]]
            outros = [x for x, _ in por_dizer["outros"]]
            dizer(json_do_lote(fotos, musicas, outros) if args.json else linha_do_lote(fotos, musicas, outros))
            if args.correr and (fotos or musicas):
                correr_entrada()
            for tipo in por_dizer:
                for x, ass in por_dizer[tipo]:
                    ditos[x["caminho"]] = ass
                    pendentes.pop(x["caminho"], None)
            primeiro_parado = None
        time.sleep(args.intervalo)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Vigia a 01-NOVAS e a pasta das musicas.")
    ap.add_argument("--uma-vez", action="store_true", help="diz o que ha de novo e sai")
    ap.add_argument("--json", action="store_true", help="cada lote como um objeto JSON numa linha")
    ap.add_argument("--correr", action="store_true",
                    help="a cada lote corre o entrada_rapida.py e diz PRONTO ou FALHOU numa linha")
    ap.add_argument("--intervalo", type=float, default=2.0, help="segundos entre duas voltas (2)")
    ap.add_argument("--parado", type=float, default=3.0, help="segundos sem mudar para contar como parado (3)")
    ap.add_argument("--espera-max", type=float, default=120.0,
                    help="ao fim disto diz os que ja pararam, mesmo com outros a mexer (120)")
    ap.add_argument("--fotos", help="a pasta das fotos novas, em vez da 01-NOVAS")
    ap.add_argument("--musicas", help="a pasta das musicas novas, em vez da 02-NOVAS-MUSICAS")
    ap.add_argument("--inventario", help="o inventario, em vez de data/inventario.csv")
    ap.add_argument("--indice-som", help="o indice das copias de som, em vez de saida/audio/indice.json")
    args = ap.parse_args()
    if args.uma_vez:
        return uma_vez(args)
    try:
        vigiar(args)
    except KeyboardInterrupt:
        dizer("VIGIA: parada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
