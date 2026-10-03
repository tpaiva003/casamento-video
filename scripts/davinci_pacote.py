# -*- coding: utf-8 -*-
"""O pacote para o DaVinci Resolve: o filme sem a legenda de baixo, as legendas num .srt e um guia.

PORQUE EXISTE. O Tiago, a 2 de outubro: para ja trabalhar na Mesa, "mas tambem colocarmos a opcao a
certa altura de criar o ficheiro como falaste para o Davinci, assim se comecar a apertar, mudo para o
davinci de forma mais facil". O teste do projetor e no proprio dia do casamento. Se ai a legenda
pedir outro tamanho, pela Mesa sao um render novo e o master dos creditos, mais de uma hora; no
DaVinci Resolve (21.1 gratuito, ja instalado) e mudar um numero e exportar.

UM COMANDO SO, que faz uma pasta nova C:\\casamento-video-media\\saida\\davinci_<AAAA-MM-DD_HHMM>\\ com:
  - o filme sem a legenda de baixo: o render.py --sem-legendas, com o estilo da montagem (tudo o resto
    gravado na imagem: os cartoes, os nomes dos bebes, o texto dentro das fotos, a fita, o destaque);
  - o mesmo filme com os creditos colados pelo ponto5_creditos.py --master, em 1920x1080: e este que
    vai para o DaVinci;
  - legendas.srt, com as legendas de baixo nos instantes em que o render as mostra (legendas_srt.py),
    no relogio do filme com creditos, e legendas_filme_sem_creditos.srt, as mesmas para o outro;
  - referencia_N.png: um fotograma do filme com a legenda desenhada como o nosso render a desenha,
    para acertar o estilo no DaVinci a olho;
  - guia.txt, passo a passo, com a letra, o corpo, a cor, a faixa e os tempos a conferir.

Nada e escrito por cima: a pasta e nova, e o render e o master ficam dentro dela. O render faz-se na
subpasta "trabalho", com os seus ficheiros de trabalho (o _corpo, o _som, os videos de abertura), para
o que vai para o DaVinci ficar sozinho em cima; nada se apaga (CLAUDE.md, regra 3). O render conta-se
em data/renders.csv, como todos.

Uso:
    py -3.11 scripts/davinci_pacote.py v3                   o pacote inteiro (uma hora e pouco, ver o guia)
    py -3.11 scripts/davinci_pacote.py v3 --ate 120         prova com os primeiros 120 s do corpo, sem creditos
    py -3.11 scripts/davinci_pacote.py v3 --pasta <pasta>   noutra pasta (tem de nao existir ou estar vazia)
    py -3.11 scripts/davinci_pacote.py v3 --fatias 6        passa ao render (o aviso de memoria pode pedi-lo)
    py -3.11 scripts/davinci_pacote.py v3 --sem-creditos    so o filme sem legendas e o .srt
"""
import datetime
import math
import os
import re
import subprocess
import sys
import textwrap
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import legendas_srt as S       # noqa: E402
import render                  # noqa: E402

from PIL import Image          # noqa: E402

FPS = render.FPS
PONTO5 = os.path.join(render.REPO, "scripts", "discussao", "ponto5_creditos.py")
ZONA_SEGURA = 0.90       # a largura em que uma linha ainda se le inteira num projetor que corta as bordas
# QUANTO LEVA A EXPORTACAO NO DAVINCI. Nao se mede daqui: a versao gratuita nao deixa scripts de fora.
# O que se mediu a 2 de outubro neste portatil (i5-8265U, Intel UHD 620) foi o mesmo trabalho pelo
# ffmpeg: descodificar o filme e codifica-lo em H.264 a 40 Mb/s, o que o guia pede ao DaVinci. Nos 88,8 s
# da prova levou 109 s no preset medium e 154 s no fast (o portatil aquece): 1,2 a 1,7 vezes a duracao,
# 17 a 25 minutos para os 14 minutos do filme com os creditos.
EXPORTAR = ("não se mede daqui (a versão gratuita não deixa). O mesmo trabalho pelo ffmpeg, descodificar e "
            "codificar em H.264 a 40 Mb/s, levou neste portátil 1,2 a 1,7 vezes a duração do filme: conta com "
            "20 a 30 minutos para os 14 minutos com os créditos. Se o DaVinci oferecer a aceleração de hardware "
            "(Intel Quick Sync), menos.")
PASTAS_DE_LETRAS = (r"C:\Windows\Fonts", os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"))


# ------------------------------------------------------------------ correr os outros scripts
def correr(cmd, env=None):
    """Corre um comando com o que ele diz a passar para o ecra; devolve (codigo, texto todo)."""
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    ambiente.update(env or {})
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=ambiente,
                            encoding="utf-8", errors="replace")
    texto = []
    for linha in proc.stdout:
        texto.append(linha)
        print("  | " + linha.rstrip("\r\n").split("\r")[-1], flush=True)
    return proc.wait(), "".join(texto)


def depois_de(texto, rotulo):
    """O caminho que vem depois de `rotulo` na ultima linha que o tem ("Escrito: C:\\...mp4" -> o caminho)."""
    achados = re.findall(r"%s\s*(.+?\.mp4)" % re.escape(rotulo), texto)
    return achados[-1].strip() if achados else None


def pasta_nova(base):
    """`base`, ou base_2, base_3...: a pasta do pacote e sempre nova, para nada ficar por cima de nada."""
    caminho, k = base, 2
    while os.path.exists(caminho) and os.listdir(caminho):
        caminho = "%s_%d" % (base, k)
        k += 1
    os.makedirs(caminho, exist_ok=True)
    return caminho


def medir(filme, *campos):
    """Campos da primeira faixa de video do filme pelo ffprobe, como texto: {campo: valor}."""
    r = subprocess.run([S.ffprobe(), "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=" + ",".join(campos), "-of", "default=nw=1", filme],
                       capture_output=True, text=True)
    return dict(l.split("=", 1) for l in r.stdout.strip().splitlines() if "=" in l)


def duracao_do_ficheiro(filme):
    """A duracao do ficheiro (a maior das faixas), a mesma que o ponto5 usa para saber onde corta."""
    r = subprocess.run([S.ffprobe(), "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", filme], capture_output=True, text=True)
    return float(r.stdout.strip())


def corte_do_master(filme):
    """O fotograma do master em que os creditos comecam a entrar: ate ai o master e o filme.

    As contas do ponto5_creditos.py: o filme vai ate 5 s antes do fade do fim (o trim ate ao corte
    da os fotogramas antes dele), e o exemplo dos creditos comeca com esses 5 s do mesmo filme; so
    depois e que os creditos se misturam. Uma legenda que ainda estivesse no ecra acaba ai.
    """
    fim_filme = duracao_do_ficheiro(filme) - render.FADE_FIM_IMAGEM
    corte = fim_filme - 5.0
    return int(math.ceil(corte * FPS - 1e-9)) + int(round(5.0 * FPS))


# ------------------------------------------------------------------ as imagens de referencia
def fotograma_do_filme(filme, q):
    """O fotograma q do filme (a 25 fps, sem buracos), em RGB.

    O -ss pede o meio do fotograma de antes, (q - 0,5) / 25 (corretor, 2 de outubro): o ffmpeg deita
    fora os fotogramas que comecam antes do -ss, e o primeiro que fica e o q. Com q / 25 + 0,001, como
    estava, o proprio q (que comeca em q / 25) ia fora e a referencia saia um fotograma depois do
    timecode que o guia diz.
    """
    r = subprocess.run([render.ffmpeg(), "-v", "error", "-ss", "%.3f" % max(0.0, (q - 0.5) / float(FPS)), "-i", filme,
                        "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    if len(r.stdout) < render.L * render.A * 3:
        return None
    return Image.frombytes("RGB", (render.L, render.A), r.stdout[:render.L * render.A * 3])


def escolher_referencias(entradas, quantas=3):
    """As legendas que servem de referencia: a primeira, a de mais linhas e a de linha mais comprida."""
    if not entradas:
        return []
    escolha = [entradas[0], max(entradas, key=lambda e: (len(e["linhas"]), e["q1"] - e["q0"])),
               max(entradas, key=lambda e: max(len(l) for l in e["linhas"]))]
    vistas, saida = set(), []
    for e in escolha:
        if e["n"] not in vistas:
            vistas.add(e["n"])
            saida.append(e)
    return saida[:quantas]


def referencias(pasta, filme, entradas):
    """referencia_N.png: o fotograma do meio de cada legenda escolhida, com a faixa do nosso render por cima."""
    feitas = []
    for k, e in enumerate(escolher_referencias(entradas), 1):
        q = (e["q0"] + e["q1"]) // 2
        im = fotograma_do_filme(filme, q)
        if im is None:
            continue
        capa = render.faixa_texto(e["texto"], e["tamanho"])
        if capa is not None:
            im.paste(capa[0], (0, 0), capa[1])
        caminho = os.path.join(pasta, "referencia_%d.png" % k)
        im.save(caminho)
        feitas.append((caminho, e, q))
    return feitas


# ------------------------------------------------------------------ o estilo da faixa, para o guia
PESOS = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold",
         700: "Bold", 800: "ExtraBold", 900: "Black"}


def letra_da_legenda():
    """(familia, face, ficheiro, instalada) da letra da legenda do estilo da montagem.

    A face de uma letra variavel e a do peso que o render lhe pede (o eixo_peso de data/fontes.json),
    e nao a do ficheiro, que abre no Thin. Instalada quer dizer que o Windows a tem (na pasta das
    letras dele ou na do utilizador, com o mesmo nome de ficheiro): so essas aparecem no DaVinci.
    """
    ident = render.estilo_ativo().get("legenda", {}).get("fonte")
    ficheiro, entrada = render.FONTE_TEXTO, {}
    if ident:
        entrada = render.letras_da_mesa().get(ident) or {}
        if entrada.get("ficheiro") and render.abrir_letra(ident, 46, avisar=False) is not None:
            ficheiro = entrada["ficheiro"]
        else:
            entrada = {}
    familia, face = render.letra("legenda", 46).getname()
    if entrada.get("eixo_peso"):
        face = PESOS.get(int(entrada["eixo_peso"]), face)
    if entrada.get("estilo_css") == "italic":
        face = (face + " Italic") if face != "Regular" else "Italic"
    base = os.path.basename(ficheiro).lower()
    instalada = any(os.path.normcase(os.path.dirname(os.path.abspath(ficheiro))) == os.path.normcase(p)
                    or (os.path.isdir(p) and base in (f.lower() for f in os.listdir(p)))
                    for p in PASTAS_DE_LETRAS if p)
    return familia, face, ficheiro, instalada


def corpo_maximo(entradas, corpo):
    """O maior corpo em que a linha mais comprida ainda cabe em ZONA_SEGURA da largura, com as linhas de hoje."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    linhas = [l for e in entradas for l in e["linhas"]]
    if not linhas:
        return None, None
    largura = max(d.textbbox((0, 0), l, font=render.letra("legenda", corpo))[2] for l in linhas)
    maximo = corpo
    while maximo < 200:
        f = render.letra("legenda", maximo + 1)
        if max(d.textbbox((0, 0), l, font=f)[2] for l in linhas) > ZONA_SEGURA * render.L:
            break
        maximo += 1
    return maximo, largura


def tc(q):
    """O fotograma do filme no timecode do DaVinci a 25 fps, HH:MM:SS:FF, numa timeline que comeca no zero."""
    s, f = divmod(int(q), FPS)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return "%02d:%02d:%02d:%02d" % (h, m, s, f)


def minutos(segundos):
    return "%d min" % max(1, int(round(segundos / 60.0))) if segundos >= 60 else "%d s" % int(round(segundos))


def guia(montagem, pasta, filme_davinci, filme_sem_creditos, srt, entradas, refs, tempos, parcial, ate=None):
    """O texto do guia.txt, com os valores deste pacote: o estilo da montagem, os tempos a conferir e as horas.

    `ate` e o --ate da prova: o comando do passo 6 tem de o levar, senao o legendas_srt.py conta as
    legendas do filme inteiro contra o filme da prova (corretor, 2 de outubro).
    """
    corpo = render.legenda_tamanho()
    cor = render.cor_hex(render.legenda_cor())
    alfa = render.fundo_da_legenda(render.LEGENDA_ALFA)
    familia, face, ficheiro, instalada = letra_da_legenda()
    maximo, _largura = corpo_maximo(entradas, corpo)
    entrelinha = int(corpo * 1.35)
    outros = [e for e in entradas if e["no_ecra"] != corpo]
    falas = [e for e in entradas if "\n" in e["texto"].strip()]
    conferir = [entradas[0]] if entradas else []
    if len(entradas) > 2:
        conferir.append(entradas[len(entradas) // 2])
    if len(entradas) > 1:
        conferir.append(entradas[-1])
    com_creditos = not parcial and filme_sem_creditos != filme_davinci
    nome = os.path.basename

    def aqui(caminho):
        """O caminho a partir da pasta do pacote: o render fica na pasta trabalho, o master em cima."""
        try:
            return os.path.relpath(caminho, pasta)
        except ValueError:
            return caminho
    L = []

    def w(texto):
        # as linhas compridas partem-se a 100 colunas, com o recuo da propria linha
        recuo = len(texto) - len(texto.lstrip(" "))
        if texto.lstrip().startswith("py -3.11"):
            L.append(texto)          # um comando fica numa linha so, para se copiar inteiro
            return
        # e a continuacao de um passo ("a. ...") fica por baixo do texto dele, nao da letra
        pendurado = recuo + (3 if re.match(r"[a-z0-9][.] ", texto.lstrip(" ")) else 2)
        L.extend(textwrap.wrap(texto.lstrip(" "), 100, initial_indent=" " * recuo, subsequent_indent=" " * pendurado,
                               break_long_words=False, break_on_hyphens=False) or [""])
    w("O FILME NO DAVINCI RESOLVE, COM AS LEGENDAS DE BAIXO À PARTE")
    w("Pacote de %s, montagem %s%s" % (datetime.datetime.now().strftime("%d/%m/%Y às %H:%M"), montagem,
                                       ". PROVA SÓ COM O INÍCIO DO FILME" if parcial else ""))
    w("")
    w("PARA QUE SERVE")
    w("O filme desta pasta tem tudo gravado na imagem menos a legenda de baixo, a dos textos por baixo")
    w("das fotos. As legendas estão em %s, nos tempos exatos em que o nosso render as mostra." % nome(srt))
    w("No DaVinci muda-se o tamanho de todas de uma vez e exporta-se, sem esperar por um render novo.")
    w("Se não for preciso mudar nada, o filme da sala continua a ser o do render normal, com os créditos.")
    w("")
    w("O QUE ESTÁ NESTA PASTA")
    w("  %s" % aqui(filme_davinci))
    w("      o filme %s, sem a legenda de baixo. É ESTE que vai para o DaVinci."
      % ("da prova, só o início" if parcial else "inteiro com os créditos" if com_creditos else "inteiro, sem os créditos"))
    if com_creditos:
        w("  %s" % aqui(filme_sem_creditos))
        w("      o mesmo filme sem os créditos (o render), só para comparar. O resto da pasta trabalho são")
        w("      os ficheiros de trabalho do render.")
    elif parcial:
        w("  trabalho\\")
        w("      os ficheiros de trabalho do render.")
    w("  %s" % nome(srt))
    w("      as %d legendas, no relógio de %s." % (len(entradas), nome(filme_davinci)))
    if com_creditos:
        w("  legendas_filme_sem_creditos.srt")
        w("      as mesmas legendas, com os mesmos tempos, para o filme sem os créditos.")
    for caminho, e, q in refs:
        w("  %s" % nome(caminho))
        w("      o fotograma %s com a legenda %d desenhada pelo nosso render: é assim que deve ficar." % (tc(q), e["n"]))
    w("")
    w("1. O PROJETO (uma vez)")
    w("  a. Abre o DaVinci Resolve. No Project Manager: New Project, com o nome Casamento.")
    w("  b. Antes de importar o filme: File > Project Settings > Master Settings.")
    w("     Timeline resolution: 1920 x 1080 HD. Timeline frame rate: 25. Playback frame rate: 25.")
    w("     Save. A cadência só se escolhe antes de haver ficheiros no projeto.")
    w("")
    w("2. O FILME")
    w("  a. Página Edit (em baixo). File > Import > Media (Ctrl+I) e escolhe %s." % aqui(filme_davinci))
    w("     Se perguntar se quer mudar a cadência do projeto para a do ficheiro, carrega em Change.")
    w("  b. File > New Timeline (Ctrl+N). Start Timecode: 00:00:00:00. O DaVinci propõe 01:00:00:00;")
    w("     muda para zeros, senão as legendas ficam uma hora ao lado. Timeline Name: Filme. Create.")
    w("  c. Arrasta o filme do Media Pool para a timeline, encostado ao início (00:00:00:00).")
    w("")
    w("3. AS LEGENDAS")
    w("  a. File > Import > Subtitle (ou, no Media Pool, botão direito > Import Subtitle) e escolhe")
    w("     %s. Aparece no Media Pool com o símbolo de legenda." % nome(srt))
    w("  b. Botão direito em cima dela > Insert Selected Subtitles to Timeline Using Timecode.")
    w("     Aparece a faixa ST1 por cima do vídeo, com cada legenda no seu sítio.")
    w("  c. Confere três, pondo o cursor da timeline nestes tempos (clica no tempo por cima do visor,")
    w("     escreve-o e Enter):")
    for e in conferir:
        w("       de %s a %s   %s" % (tc(e["q0"]), tc(e["q1"]), e["linhas"][0][:60]))
    w("     Cada uma começa e acaba nesses fotogramas. Se não aparece nenhuma legenda, a timeline começa")
    w("     em 01:00:00:00: Timeline > Timeline Settings > Start Timecode 00:00:00:00, e repete o b.")
    w("")
    w("4. O ESTILO, PARA FICAR COMO O NOSSO (uma vez, vale para todas)")
    w("  Clica no nome da faixa ST1, abre o Inspector (em cima, à direita) e o separador Track.")
    w("  Font: %s. Face: %s." % (familia, face))
    if not instalada:
        w("    ESTA LETRA NÃO ESTÁ INSTALADA NO WINDOWS, e sem isso o DaVinci não a mostra. Fecha o DaVinci,")
        w("    abre com duplo clique o ficheiro")
        w("      %s" % ficheiro.replace("/", "\\"))
        w("    carrega em Install, e volta a abrir o DaVinci.")
    w("  Size: começa em %d. No nosso render a letra tem %d píxeis de corpo num ecrã de 1080, mas o" % (corpo, corpo))
    w("    número do DaVinci pode não ser o mesmo: acerta-o a olho com a referência (passo 5).")
    w("  Line Spacing: no nosso as linhas estão a %d píxeis umas das outras (1,35 corpos)." % entrelinha)
    w("  Color: %s. Opacity: 100." % cor)
    w("  Alignment: ao centro. Position: centrada, com a última linha a assentar a %d píxeis do fundo"
      % render.LEGENDA_TEXTO)
    w("    do ecrã.")
    w("  Stroke e Drop Shadow: desligados.")
    w("  Background: ligado, cor preta (#000000), Opacity %d%% (no nosso render é preto a %d em 255)."
      % (int(round(100.0 * alfa / 255)), alfa))
    w("    A diferença que fica: no nosso render a faixa escura ocupa a largura toda do ecrã e desce")
    w("    até %d píxeis do fundo; no DaVinci a caixa escura fica à volta do texto. Se o Background tiver"
      % render.LEGENDA_FUNDO)
    w("    largura ou margem, alarga-o; se não tiver, a caixa também se lê bem.")
    w("  Guarda o estilo: menu dos três pontos do Inspector > Save Track as Preset > Casamento.")
    w("")
    w("5. ACERTAR A OLHO COM A REFERÊNCIA (5 minutos)")
    if refs:
        caminho, e, q = refs[0]
        w("  a. Importa %s (Ctrl+I) e põe-no na faixa V2, por cima do filme, a começar em %s."
          % (nome(caminho), tc(q)))
        w("  b. No Inspector, separador Video, baixa a Opacity da imagem para 50. Vês as duas legendas, uma")
        w("     por cima da outra. Muda o Size e a Position da faixa ST1 até as letras coincidirem.")
        w("  c. Apaga a imagem da V2 (seleciona-a e Delete). Só serve para acertar.")
    else:
        w("  (este pacote não tem legendas)")
    w("")
    w("6. MUDAR O TAMANHO DE TODAS DE UMA VEZ")
    w("  Faixa ST1 > Inspector > Track > Size. Todas as legendas mudam juntas (o Zoom X e Y também dá).")
    w("  O DaVinci não parte as linhas sozinho: ficam partidas como no nosso render.")
    if maximo:
        w("  Com estas linhas, até ao corpo %d do nosso render a linha mais comprida cabe em 90%% da largura."
          % maximo)
        w("  Para maior do que isso, faz o .srt com as linhas partidas para o corpo novo (leva segundos),")
        w("  apaga a faixa ST1 e repete o passo 3 com ele:")
        w("    py -3.11 scripts/legendas_srt.py %s --filme \"%s\" --corpo 60%s%s --saida \"%s\""
          % (montagem, filme_sem_creditos or filme_davinci,
             (" --ate %s" % ate) if parcial and ate is not None else "",
             (" --corte %.2f" % (tempos["corte_q"] / float(FPS))) if com_creditos and tempos.get("corte_q") else "",
             os.path.join(pasta, "legendas_corpo60.srt")))
    w("  Uma legenda só: seleciona-a na faixa, Inspector > Caption > Customize Caption.")
    if falas:
        w("  As falas estão em linhas separadas, como no nosso: legenda%s %s."
          % ("s" if len(falas) > 1 else "", ", ".join(str(e["n"]) for e in falas[:12])))
    if outros:
        w("  ATENÇÃO: estas o nosso render desenha noutro corpo (desce para caber em 4 linhas, ou o grupo")
        w("  tem o seu): %s." % ", ".join("%d (corpo %d)" % (e["n"], e["no_ecra"]) for e in outros[:12]))
    # OS EMOJIS (2 de outubro, a tarde): o emoji da legenda 39 da v3 vai tal e qual para o .srt, e o
    # DaVinci desenha-o com as letras dele; no nosso render sai a cores, na letra de emojis do Windows
    # (render.texto_emojis). Como sai no DaVinci nao se mediu daqui, e por isso o guia manda confirmar.
    # Avisa-se a parte o que no nosso render sai numa caixa vazia (nem a letra nem a de emojis o tem,
    # render.caracteres_sem_letra) e os emojis de varios caracteres que a Pillow sem o raqm nao junta.
    f_leg = render.letra("legenda", corpo)
    com_emojis = [(e, render.texto_emojis.emojis_do_texto(e["texto"], f_leg)) for e in entradas]
    com_emojis = [(e, em) for e, em in com_emojis if em]
    if com_emojis:
        w("  EMOJIS: %s. No nosso render saem a cores, na letra de emojis do Windows (Segoe UI Emoji)."
          % "; ".join("legenda %d, %s" % (e["n"], ", ".join(render.texto_emojis.codigos(x) for x in em))
                      for e, em in com_emojis[:8]))
        w("  No .srt vão como texto e é o DaVinci que os desenha: confirma na faixa ST1 se saem como queres")
        w("  (a cores, a preto e branco ou numa caixa). Para os tirar: na Mesa, ou aqui, com a legenda")
        w("  selecionada na faixa ST1, no texto dela no Inspector.")
    sem_letra = [(e, render.caracteres_sem_letra(e["texto"], f_leg)) for e in entradas]
    sem_letra = [(e, fora) for e, fora in sem_letra if fora]
    if sem_letra:
        w("  ATENÇÃO, CARACTERES QUE A LETRA NÃO TEM (nem ela nem a de emojis): %s. No nosso render saem"
          % "; ".join("legenda %d, %s" % (e["n"], ", ".join(render.nome_do_caracter(c) for c in fora))
                      for e, fora in sem_letra[:8]))
        w("  como uma caixa vazia; no DaVinci podem sair com outra letra ou também numa caixa. Para os tirar:")
        w("  na Mesa, ou aqui, com a legenda selecionada na faixa ST1, no texto dela no Inspector.")
    juntos = [(e, render.texto_emojis.sequencias(e["texto"])) for e in entradas]
    juntos = [(e, sq) for e, sq in juntos if sq]
    if juntos:
        w("  ATENÇÃO, EMOJIS QUE O NOSSO RENDER NÃO JUNTA (falta à Pillow o raqm): %s."
          % "; ".join("legenda %d, %s: %s" % (e["n"], render.texto_emojis.codigos(q), sai)
                      for e, sq in juntos[:8] for q, sai in sq))
    w("")
    w("7. EXPORTAR")
    w("  a. Página Deliver (o foguete, em baixo). Render Settings > Custom Export.")
    w("     Filename: Casamento. Location: uma pasta tua.")
    w("  b. Separador Video: Format MP4. Codec H.264. Resolution 1920 x 1080 HD. Frame rate 25.")
    w("     Quality: Restrict to 40000 Kb/s. Se aparecer Use hardware acceleration if available, liga-o.")
    w("  c. No fim do separador Video, em Subtitle Settings: liga Export Subtitle e escolhe")
    w("     Format: Burn into video. SEM ISTO O FILME SAI SEM LEGENDAS.")
    w("  d. Separador Audio: Export Audio ligado, Codec AAC, Data Rate 320 Kb/s.")
    w("  e. Add to Render Queue e, à direita, Render All.")
    w("  Quanto tempo: %s" % tempos.get("exportar", EXPORTAR))
    w("")
    w("8. ANTES DE O LEVAR")
    # os creditos so se dizem quando o filme os tem (corretor, 2 de outubro): a prova e o --sem-creditos nao
    fim = "os créditos no fim e o fade a preto" if com_creditos else \
        ("o fim da prova" if parcial else "o fade a preto no fim")
    if conferir:
        w("  Abre o ficheiro exportado no VLC e vê: a legenda \"%s\" em %s; %s."
          % (conferir[0]["linhas"][0][:40], tc(conferir[0]["q0"] + FPS // 2), fim))
    else:
        w("  Abre o ficheiro exportado no VLC e vê %s." % fim)
    w("")
    w("QUANTO TEMPO LEVOU ESTE PACOTE")
    for chave, rotulo in (("render", "o render sem legendas"), ("master", "os créditos colados (master)"),
                          ("legendas", "as legendas, as referências e o guia"), ("total", "tudo")):
        if chave in tempos:
            w("  %-38s %s" % (rotulo, minutos(tempos[chave])))
    if parcial and "previsao" in tempos:
        w("  %s" % tempos["previsao"])
    w("")
    w("REFAZER O PACOTE (depois de mudar alguma coisa na Mesa, e de juntar e montar como sempre)")
    w("  py -3.11 scripts/davinci_pacote.py %s" % montagem)
    return "\r\n".join(L) + "\r\n"


# ------------------------------------------------------------------ o comando
def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit("Diz qual a montagem. Ex: py -3.11 scripts/davinci_pacote.py v3")
    montagem = sys.argv[1]

    def opcao(chave):
        return sys.argv[sys.argv.index(chave) + 1] if chave in sys.argv else None
    ate = opcao("--ate")
    parcial = ate is not None
    carimbo = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    pasta = pasta_nova(opcao("--pasta") or os.path.join(render.SAIDA, "davinci_" + carimbo))
    print("Pacote do DaVinci em %s" % pasta)
    tempos = {}
    t_inicio = time.time()

    # 1. O FILME SEM A LEGENDA DE BAIXO
    cmd = [sys.executable, os.path.join(render.REPO, "scripts", "render.py"), montagem,
           "--sem-legendas", "--sem-copias", "--saida", os.path.join(pasta, "trabalho")]
    if parcial:
        cmd += ["--ate", ate]
    if opcao("--fatias"):
        cmd += ["--fatias", opcao("--fatias")]
    print("\n1. render sem legendas: %s" % " ".join(cmd[1:]))
    t0 = time.time()
    codigo, texto = correr(cmd)
    tempos["render"] = time.time() - t0
    filme = depois_de(texto, "Escrito:")
    if codigo != 0 or not filme or not os.path.exists(filme):
        sys.exit("O render nao acabou (codigo %d); nada mais foi feito. Ve o que ele disse acima." % codigo)
    m = medir(filme, "nb_read_packets", "duration")
    quadros = int(m.get("nb_read_packets") or 0)
    if abs(quadros - float(m.get("duration") or 0) * FPS) > 0.5:
        print("  ATENCAO: o filme tem %d fotogramas e %.2f s de imagem; devia ter um a cada 0,04 s" %
              (quadros, float(m.get("duration") or 0)))

    # 2. OS CREDITOS, NO MASTER EM 1080p
    master = None
    if not parcial and "--sem-creditos" not in sys.argv:
        cmd = [sys.executable, PONTO5, "--master", "--filme", filme, "--master-em", pasta, "--sem-telemovel"]
        print("\n2. creditos: %s" % " ".join(cmd[1:]))
        t0 = time.time()
        codigo, texto = correr(cmd, {"DISCUSSAO_MONTAGEM": montagem})
        tempos["master"] = time.time() - t0
        master = depois_de(texto, "MASTER:")
        if codigo != 0 or not master or not os.path.exists(master):
            print("  OS CREDITOS NAO SAIRAM (codigo %d). O filme sem legendas e o .srt dele ficam; o guia diz"
                  " qual usar." % codigo)
            master = None

    # 3. AS LEGENDAS, AS REFERENCIAS E O GUIA
    print("\n3. legendas")
    t0 = time.time()
    estado = S.carregar(montagem, float(ate) if parcial else None)
    render.aplicar_estilo(render.ler_estilo(montagem))
    legendas = S.legendas_do_corpo(estado)
    abertura = S.abertura_medida(filme, estado)
    prevista = S.abertura_prevista(estado)
    print("  %d legendas; os videos de abertura ocupam %d fotogramas (%.2f s)%s"
          % (len(legendas), abertura, abertura / float(FPS),
             "" if abertura == prevista else ", e o CSV previa %d" % prevista))
    entradas_filme = S.entradas_do_filme(legendas, abertura)
    filme_davinci, srt = filme, os.path.join(pasta, "legendas.srt")
    if master:
        corte = corte_do_master(filme)
        tempos["corte_q"] = corte
        entradas = S.entradas_do_filme(legendas, abertura, corte)
        S.escrever_srt(srt, entradas)
        S.escrever_srt(os.path.join(pasta, "legendas_filme_sem_creditos.srt"), entradas_filme)
        filme_davinci = master
        cortadas = len(entradas_filme) - len(entradas) + sum(
            1 for a, b in zip(entradas, entradas_filme) if a["q1"] != b["q1"])
        if cortadas:
            print("  %d legendas encurtadas onde os creditos comecam" % cortadas)
    else:
        entradas = entradas_filme
        S.escrever_srt(srt, entradas)
    refs = referencias(pasta, filme_davinci, entradas)
    tempos["legendas"] = time.time() - t0
    tempos["total"] = time.time() - t_inicio
    if parcial:
        # A PREVISAO PARA O FILME INTEIRO, pelo ritmo desta prova: o render e quase so desenhar
        # fotogramas, e o resto (o som, a juncao) e pequeno ao pe disso.
        inteiro = S.carregar(montagem, None)
        fator = inteiro["total_quadros"] / float(max(1, estado["total_quadros"]))
        # O RITMO DO INICIO E O MAIS LEVE (corretor, 2 de outubro): os primeiros minutos sao o contador, a
        # fita e fotos soltas, e as pilhas, as colagens e os mergulhos vem depois. A conta direta e o minimo.
        tempos["previsao"] = ("O filme inteiro tem %d fotogramas, %s vezes os desta prova: pelo ritmo dela o render"
                              " levaria pelo menos %s (o resto do filme tem as pilhas e as colagens, que pesam"
                              " mais; o render de sempre, sem as cópias, anda pelos 45 min), mais uns 20 a 25 min"
                              " dos créditos (medidos a 2 de outubro: o exemplo 12 min, o master 12 min)."
                              % (inteiro["total_quadros"], ("%.1f" % fator).replace(".", ","),
                                 minutos(tempos["render"] * fator)))
    texto_guia = guia(montagem, pasta, filme_davinci, filme, srt, entradas, refs, tempos, parcial, ate)
    caminho_guia = os.path.join(pasta, "guia.txt")
    with open(caminho_guia, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(texto_guia)

    print("\nPRONTO em %s (%s)" % (pasta, minutos(tempos["total"])))
    print("  filme para o DaVinci: %s" % os.path.basename(filme_davinci))
    print("  legendas: %s (%d)" % (os.path.basename(srt), len(entradas)))
    print("  guia: %s" % caminho_guia)
    for chave in ("render", "master", "legendas"):
        if chave in tempos:
            print("  %s: %s" % (chave, minutos(tempos[chave])))
    if "previsao" in tempos:
        print("  " + tempos["previsao"])


if __name__ == "__main__":
    main()
