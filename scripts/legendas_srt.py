# -*- coding: utf-8 -*-
"""As legendas de baixo do filme num .srt, nos instantes em que o render as mostra (2 de outubro).

PORQUE EXISTE. O Tiago, a 2 de outubro: trabalhar na Mesa, "mas tambem colocarmos a opcao a certa
altura de criar o ficheiro como falaste para o Davinci, assim se comecar a apertar, mudo para o
davinci de forma mais facil". O teste do projetor e no proprio dia do casamento, e mudar o tamanho
da legenda pela Mesa e um render novo de quase uma hora. O render faz o filme sem a faixa de baixo
(render.py --sem-legendas) e isto faz o .srt que o DaVinci Resolve le: la, o tamanho de todas
muda-se de uma vez e a exportacao leva minutos. O pacote inteiro e o scripts/davinci_pacote.py.

OS TEMPOS SAO OS DO DESENHO, FOTOGRAMA A FOTOGRAMA. Para cada fotograma do corpo faz-se a conta do
render.fotograma(): os clips ativos, o encadeado entre eles, o nome do bebe a subir a foto do preto,
o fade do fim, e em cada clip o texto que a faixa mostra nesse instante (o da foto, o do grupo, ou o
da foto que esta a entrar, na opcao "na legenda de baixo", com a troca de 0,2 s do
legenda_no_instante()). Num encadeado as duas faixas misturam-se; o .srt nao tem misturas, e a
legenda e a que pesa mais no fotograma, metade ou mais. Por isso cada legenda comeca no fotograma
em que passa de metade e acaba no ultimo em que ainda esta acima dela, e duas legendas seguidas
trocam a meio do encadeado. Duas fotos seguidas com o mesmo texto sao uma legenda so, como no
filme, onde a faixa nao pisca.

O RELOGIO E O DO FILME INTEIRO: os videos de abertura a frente e o corpo a seguir. O corpo do render
comeca onde os videos acabam, e nao no inicio_s do CSV (o contador entra 0,7 s antes, por cima do
fim da intro, e no filme entra com corte seco a seguir). Quantos fotogramas sao os videos mede-se no
ficheiro (--filme): a duracao da imagem menos a do corpo. Sem filme preve-se pelas duracoes do CSV
arredondadas ao fotograma, e diz-se. Um render --ate nao leva os videos de abertura, e o seu .srt
tambem nao.

AS LINHAS SAO AS DO RENDER: as falas em linhas separadas, e cada fala partida como o render a parte
na largura da faixa (render.linhas_legenda()). O DaVinci nao parte linhas sozinho; com --corpo N as
linhas partem-se para outro corpo, para quem quiser a letra maior no DaVinci sem linhas fora do ecra.

Uso:
    py -3.11 scripts/legendas_srt.py v3                         previsto pelas duracoes do CSV
    py -3.11 scripts/legendas_srt.py v3 --filme <render.mp4>    a abertura medida no filme
    py -3.11 scripts/legendas_srt.py v3 --ate 120               o troco de um render --ate 120
    py -3.11 scripts/legendas_srt.py v3 --corpo 56              as linhas partidas para o corpo 56
    py -3.11 scripts/legendas_srt.py v3 --corte 680.5           nada depois deste segundo (o master)
    py -3.11 scripts/legendas_srt.py v3 --saida <ficheiro.srt>
"""
import contextlib
import io
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render       # noqa: E402

FPS = render.FPS
PESO_MINIMO = 0.5      # a legenda entra no .srt nos fotogramas em que pesa pelo menos isto


# ------------------------------------------------------------------ o que cada clip mostra
def plano_da_legenda(clip, inv_por_nome=None):
    """O que a faixa de baixo do clip mostra, contado como o preparar() conta, sem abrir fotografia.

    Devolve None (nenhuma faixa), {"fixa": texto, "tamanho": None} (a faixa de sempre, com o corpo
    do estilo) ou {"por_foto": [texto de cada foto], "inicios": [...], "tamanho": corpo} (a opcao
    "na legenda de baixo" de um grupo, que troca de texto quando cada foto comeca a entrar). Os
    clips que o preparar() deixa pretos (uma foto em falta, um grupo com o numero errado de fotos)
    nao tem faixa. Os avisos que o ler_textos_opcoes() da ja os deu o montar e o render: calam-se.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        return _plano(clip, inv_por_nome or {})


def _plano(clip, inv_por_nome):
    tipo = clip.get("tipo")
    texto = clip.get("texto_ecra") or ""
    if tipo in ("foto", "video"):
        if tipo == "foto" and not _foto_existe(clip, inv_por_nome):
            return None
        return {"fixa": texto, "tamanho": None} if texto.strip() else None
    if tipo == "lado":
        lay = (clip.get("tratamento") or "").strip()
        caminhos = clip.get("_caminhos")
        if lay not in render.LAYOUTS_LADO:
            return None
        n = render.LAYOUTS_LADO[lay]
        if caminhos is not None and (len(caminhos) != n or not all(c and os.path.exists(c) for c in caminhos)):
            return None
        return _plano_do_grupo(clip, texto, n, [render.LADO_ATRASO + k * render.LADO_INTERVALO for k in range(n)])
    if tipo in render.LIMITES_MONTE:
        minimo, maximo = render.limites_do_grupo(tipo, clip.get("tratamento"))
        caminhos = clip.get("_caminhos")
        n = len(caminhos) if caminhos is not None else len((clip.get("id") or "").split("|"))
        if not (minimo <= n <= maximo):
            return None
        if caminhos is not None and not all(c and os.path.exists(c) for c in caminhos):
            return None
        if tipo == "colagem" and (clip.get("tratamento") or "").strip() == render.MERGULHO_ESTILO:
            # O MERGULHO SO TEM A LEGENDA DO GRUPO: os textos das fotos ficam guardados e nao se
            # mostram (decisao 103), ver preparar_mergulho().
            return {"fixa": texto, "tamanho": None} if texto.strip() else None
        entra = clip.get("_transicao_entrada")
        entra = float(clip.get("transicao_s") or 0.0) if entra in (None, "") else float(entra)
        sai = clip.get("_transicao_seguinte")
        sai = entra if sai in (None, "") else float(sai)
        inicios = render.inicios_do_grupo(tipo, n, float(clip.get("duracao_s") or 0.0), entra, sai)
        return _plano_do_grupo(clip, texto, n, inicios)
    return None


def _foto_existe(clip, inv_por_nome):
    """A mesma procura do preparar(): o ficheiro do indice, ou o do inventario pelo nome."""
    caminho = clip.get("_caminho")
    if "_caminho" not in clip:
        return True            # um clip que nao passou pelo carregar_montagem(): conta-se que existe
    if not caminho or not os.path.exists(caminho):
        r = inv_por_nome.get((clip.get("ficheiro") or "").lower())
        caminho = r["caminho"] if r else None
    return bool(caminho and os.path.exists(caminho))


def _plano_do_grupo(clip, texto, n, inicios):
    """A legenda de um lado a lado, colagem ou pilha: as contas do preparar_lado() e do preparar_monte()."""
    opcoes = render.ler_textos_opcoes(clip.get("textos_opcoes"))
    textos = render.textos_do_grupo(render.ler_textos_fotos(clip.get("textos_fotos")), n)
    if textos and opcoes["modo"] == "legenda":
        grupo = (texto or "").strip()
        lista = [t or grupo for t in textos]
        if any(lista):
            return {"por_foto": lista, "inicios": list(inicios), "tamanho": opcoes["tamanho"]}
        return None
    return {"fixa": texto, "tamanho": None} if texto.strip() else None


def texto_no_instante(plano, t_rel, duracao):
    """O texto que a faixa do clip mostra no instante t_rel, ou "": na troca, o que pesa mais.

    E o legenda_no_instante() sem desenhar: o troco da foto que contem t_rel, e nos LEGENDA_TROCA
    segundos da troca as duas faixas misturadas, com o texto novo a pesar f.
    """
    if plano is None:
        return ""
    if "fixa" in plano:
        return plano["fixa"]
    textos = plano["por_foto"]
    tempos = render.tempos_da_agenda(plano["inicios"], duracao)
    i = 0
    for k, (inicio, _fim) in enumerate(tempos):
        if t_rel >= inicio:
            i = k
    atual = textos[i]
    anterior = textos[i - 1] if i > 0 else atual
    troca = render.troca_da_legenda(tempos, i)
    f = (t_rel - tempos[i][0]) / troca if troca > 0 else 1.0
    if anterior == atual or f >= 1.0:
        return atual
    return atual if f >= PESO_MINIMO else anterior


def tamanho_do_plano(plano):
    """O corpo com que o render desenha a faixa deste clip (antes de descer para caber em 4 linhas)."""
    if plano is None or plano.get("tamanho") is None:
        return render.legenda_tamanho()
    return plano["tamanho"]


# ------------------------------------------------------------------ fotograma a fotograma
def clips_e_pesos(q, estado):
    """[(clip, peso)] do fotograma q do corpo: quanto cada clip pesa nele, pela conta do fotograma().

    Os ativos e a mistura sao os do render.fotograma(); com um clip "nome" ativo e a do
    compor_nome() (a foto seguinte sobe do preto, ou a de antes desce para ele, e o nome e
    letreiro por cima, sem faixa); no fim do filme o fade a preto escurece tudo, faixa incluida.
    """
    resto = estado["resto"]
    t = estado["desvio"] + q / float(FPS)
    ativos = [c for c in resto if float(c["inicio_s"]) - 0.001 <= t < float(c["fim_s"])]
    if not ativos:
        ativos = [resto[-1]]
    ativos = ativos[-2:]
    nomes = [c for c in ativos if c["tipo"] == "nome"]
    if nomes:
        nome = nomes[0]
        ini = float(nome["inicio_s"])
        antes = [c for c in ativos if c is not nome and float(c["inicio_s"]) < ini]
        depois = [c for c in ativos if c is not nome and float(c["inicio_s"]) > ini]
        if depois:
            c = depois[-1]
            u = t - float(c["inicio_s"])
            pesos = [(c, render._suave(u / (float(c["transicao_s"]) or 0.01)))]
        elif antes:
            entra = float(nome["transicao_s"]) or 0.01
            pesos = [(antes[-1], 1.0 - render._suave((t - ini) / entra))]
        else:
            pesos = []
    elif len(ativos) == 1:
        pesos = [(ativos[0], 1.0)]
    else:
        c2 = ativos[-1]
        trans = float(c2["transicao_s"]) or 0.01
        a = min(1.0, max(0.0, (t - float(c2["inicio_s"])) / trans))
        pesos = [(ativos[0], 1.0 - a), (c2, a)]
    if not estado["ate"]:
        fica = render.escuro_no_fim(q / float(FPS), estado["fim"])
        pesos = [(c, p * fica) for c, p in pesos]
    return pesos


def pesos_do_fotograma(q, estado, planos):
    """[(texto, peso, plano)] do fotograma q do corpo: o que a faixa de cada clip ativo pesa nele.

    O texto e o que a faixa do clip mostra nesse instante (texto_no_instante()); o peso, o do clip
    no fotograma (clips_e_pesos()). O peso que falta para 1 e o de nenhuma faixa.
    """
    t = estado["desvio"] + q / float(FPS)
    saida = []
    for c, peso in clips_e_pesos(q, estado):
        plano = planos.get(c["ordem"])
        saida.append((texto_no_instante(plano, t - float(c["inicio_s"]), float(c["duracao_s"])), peso, plano))
    return saida


def texto_do_fotograma(q, estado, planos):
    """(texto, plano) da legenda que o fotograma q mostra, ou ("", None): a que pesa PESO_MINIMO ou mais.

    Dois clips seguidos com o mesmo texto somam: a faixa e a mesma nos dois e nao se mistura com
    nada. Num empate a meio do encadeado fica a do clip que entra.
    """
    somas = {}
    for txt, p, plano in pesos_do_fotograma(q, estado, planos):
        if txt.strip():
            antes = somas.get(txt, (0.0, plano))
            somas[txt] = (antes[0] + p, plano)
    melhor, plano_melhor, peso = "", None, 0.0
    for txt, (p, plano) in somas.items():
        if p >= peso:
            melhor, plano_melhor, peso = txt, plano, p
    if peso >= PESO_MINIMO - 1e-9:
        return melhor, plano_melhor
    return "", None


def planos_do_estado(estado):
    """{ordem do clip: plano} de todos os clips do corpo."""
    return {c["ordem"]: plano_da_legenda(c, estado.get("inv_por_nome")) for c in estado["resto"]}


def legendas_do_corpo(estado):
    """As legendas do corpo, pela ordem: [{q0, q1, texto, tamanho}], em fotogramas do corpo (q1 exclusivo)."""
    planos = planos_do_estado(estado)
    saida = []
    atual = None
    for q in range(estado["total_quadros"]):
        txt, plano = texto_do_fotograma(q, estado, planos)
        if atual is not None and txt == atual["texto"] and q == atual["q1"]:
            atual["q1"] = q + 1
            continue
        if txt:
            atual = {"q0": q, "q1": q + 1, "texto": txt, "tamanho": tamanho_do_plano(plano)}
            saida.append(atual)
        else:
            atual = None
    return saida


# ------------------------------------------------------------------ o relogio do filme
def abertura_prevista(estado):
    """Fotogramas do filme antes do corpo, pelo CSV: a soma das duracoes dos videos de abertura.

    E o que a juncao do render da quando os videos existem e tem pelo menos a duracao pedida (o
    concat poe cada um a seguir a duracao do anterior, e o encoder poe o corpo no fotograma mais
    perto). Um render --ate nao leva os videos de abertura: zero.
    """
    if estado["ate"]:
        return 0
    return int(round(sum(float(c["duracao_s"] or 0.0) for c in estado["fanfarra"]) * FPS))


def ffprobe():
    return os.path.join(os.path.dirname(render.ffmpeg()), "ffprobe.exe")


def duracao_da_imagem(filme):
    """Segundos da imagem do filme (a duracao da primeira faixa de video), pelo ffprobe."""
    r = subprocess.run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=duration", "-of", "default=nw=1:nk=1", filme],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        sys.exit("Nao consegui medir a imagem de %s: %s" % (filme, (r.stderr or "").strip()[-200:]))


def abertura_medida(filme, estado):
    """Fotogramas do filme antes do corpo, medidos: a imagem do filme menos o corpo, que vem no fim.

    Serve para o filme do render e para o da juncao a cadencia certa do --sem-legendas: a
    duracao da imagem conta-se pelos tempos dos fotogramas, e nos dois o ultimo e o do corpo.

    UMA ABERTURA NEGATIVA PARA TUDO (corretor, 2 de outubro): quer dizer que o filme e mais curto do
    que o corpo da montagem, e e quase sempre um render --ate contado sem o mesmo --ate. Escrevia-se
    o .srt do filme inteiro com tempos negativos, sem queixa.
    """
    abertura = int(round(duracao_da_imagem(filme) * FPS)) - estado["total_quadros"]
    if abertura < 0:
        sys.exit("O filme %s tem menos %d fotogramas do que o corpo da montagem%s: se e um render --ate, "
                 "passa o mesmo --ate; se nao, e outro filme ou outra montagem. Nada foi escrito."
                 % (os.path.basename(filme), -abertura,
                    " ate aos %.0f s" % estado["ate"] if estado.get("ate") else ""))
    return abertura


# ------------------------------------------------------------------ o ficheiro
def linhas_da_legenda(texto, tamanho, corpo=None):
    """As linhas da legenda como o render as escreve: (linhas, corpo com que ficam no ecra).

    Com `corpo` partem-se para esse corpo, na mesma largura da faixa, para o DaVinci.
    """
    tam, linhas, _fonte = render.linhas_legenda(texto, corpo if corpo else tamanho)
    return linhas, tam


def tempo_srt(fotograma):
    """O fotograma do filme -> "HH:MM:SS,mmm", exato: a 25 fps cada fotograma sao 40 ms."""
    ms = int(round(fotograma * 1000.0 / FPS))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def entradas_do_filme(legendas, abertura, corte=None, corpo=None):
    """As legendas no relogio do filme: [{n, q0, q1, linhas, texto, tamanho, corpo_no_ecra}].

    `abertura` em fotogramas do filme antes do corpo; `corte` em fotogramas do filme, e nada passa
    dele (no master, onde os creditos comecam).
    """
    saida = []
    for leg in legendas:
        q0, q1 = leg["q0"] + abertura, leg["q1"] + abertura
        if corte is not None:
            if q0 >= corte:
                continue
            q1 = min(q1, corte)
        linhas, no_ecra = linhas_da_legenda(leg["texto"], leg["tamanho"], corpo)
        saida.append({"n": len(saida) + 1, "q0": q0, "q1": q1, "linhas": linhas,
                      "texto": leg["texto"], "tamanho": leg["tamanho"], "no_ecra": no_ecra})
    return saida


def texto_srt(entradas):
    """O .srt, com mudancas de linha do Windows. Cada legenda: numero, tempos, linhas, linha em branco."""
    partes = []
    for e in entradas:
        partes.append("%d\r\n%s --> %s\r\n%s\r\n" % (e["n"], tempo_srt(e["q0"]), tempo_srt(e["q1"]),
                                                   "\r\n".join(e["linhas"])))
    return "\r\n".join(partes)


def escrever_srt(caminho, entradas, por_cima=False):
    """Escreve o .srt em UTF-8 (sem marca no inicio). Por cima de outro so com `por_cima`.

    UM EMOJI VAI COMO TEXTO (2 de outubro): os quatro bytes dele em UTF-8, com o U+FE0F e o ZWJ que
    forem dele, e e o DaVinci que o desenha com as letras dele. No nosso render sai a cores, na letra
    de emojis do Windows (render.texto_emojis). As linhas sao as do render.linhas_legenda(), por isso
    os hifens especiais ja vem como o hifen de sempre e os invisiveis tirados, como no filme.
    """
    if os.path.exists(caminho) and not por_cima:
        sys.exit("Ja existe %s: escolhe outro nome, nao escrevo por cima" % caminho)
    with open(caminho, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto_srt(entradas))
    return caminho


def carregar(nome, ate=None, montagens=None):
    """O estado do render para a montagem, com o estilo dela: o mesmo carregar_montagem() do render, calado."""
    if montagens:
        render.MONTAGENS = montagens
    with contextlib.redirect_stdout(io.StringIO()):
        return render.carregar_montagem(nome, ate)


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit("Diz qual a montagem. Ex: py -3.11 scripts/legendas_srt.py v3")
    nome = sys.argv[1]

    def opcao(chave, conv=str):
        return conv(sys.argv[sys.argv.index(chave) + 1]) if chave in sys.argv else None
    ate, corpo, corte, filme = opcao("--ate", float), opcao("--corpo", int), opcao("--corte", float), opcao("--filme")
    estado = carregar(nome, ate, opcao("--montagens"))
    legendas = legendas_do_corpo(estado)
    if filme:
        abertura = abertura_medida(filme, estado)
        print("abertura medida em %s: %d fotogramas (%.2f s)" % (os.path.basename(filme), abertura, abertura / float(FPS)))
    else:
        abertura = abertura_prevista(estado)
        print("abertura prevista pelo CSV: %d fotogramas (%.2f s); com --filme mede-se no ficheiro"
              % (abertura, abertura / float(FPS)))
    entradas = entradas_do_filme(legendas, abertura, None if corte is None else int(math.floor(corte * FPS + 1e-9)),
                                 corpo)
    saida = opcao("--saida") or os.path.join(render.REPO, "saida", "legendas",
                                             "%s%s%s.srt" % (nome, "_ate%d" % ate if ate else "",
                                                             "_corpo%d" % corpo if corpo else ""))
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    # no saida/legendas do repositorio (no .gitignore) o de antes da lugar ao novo; noutro sitio nunca
    escrever_srt(saida, entradas, por_cima=opcao("--saida") is None)
    print("%d legendas em %s" % (len(entradas), saida))


if __name__ == "__main__":
    main()
