# -*- coding: utf-8 -*-
"""O que a Mesa precisa para mostrar e ajustar os creditos (2 de outubro).

O TIAGO, a 2 de outubro: "amanha vou ter um dia em cheio com a Clara e quero sermos capazes de com
ela ajustar ao maximo diretamente na Mesa e depois darmos so ordem para fazer render". Dos creditos
pediu duas coisas: "ajustar a ordem no final das fotos nos creditos de forma simples e pratica
enquanto os nomes movem" e "editar os textos que aparecem na parte final dos creditos".

Quem desenha os creditos e o scripts/discussao/ponto5_creditos.py. Isto nao desenha nada: le dele
o que a pre-visualizacao da Mesa precisa para fazer as mesmas contas, e o gerar_mesa.py poe-no na
pagina como window.CREDITOS_NOMES:

  grupos    pela ordem do GRUPOS do ponto5, cada um com a etiqueta da folha (a chave do
            est.creditos.grupos), o titulo, o subtitulo e as linhas de nomes ja partidas como o
            rolo_de_nomes() as parte (um agregado por linha, quebrado so entre pessoas), em Arial; e,
            em `quebras`, quantas pessoas leva cada linha nas outras letras de data/fontes.json que
            partem de outra maneira (o rolo do ponto5 parte na letra da legenda do estilo);
  omissoes  os CARGOS, o TITULO e a DATA de hoje, que sao o que vale quando o est.creditos nao diz
            outra coisa (contrato de 2 de outubro);
  fotos     de cada foto da FINAIS, a largura e a altura depois da rotacao do EXIF e a altura que
            ocupa na coluna (a 760 de largura, cortada a 900), as mesmas contas do coluna_de_fotos();
  medidas   as velocidades, os corpos de letra, os espacos e os tempos do ponto5.

OS NOMES DOS CONVIDADOS SO VAO PARA DENTRO DO saida/mesa.html MONTADO. Este ficheiro nao os
escreve em lado nenhum, e o gerar_mesa.py tambem nao: sao dados de 140 pessoas e nunca entram no
Git. Tambem nunca saem daqui as etiquetas que nao vao ao ecra (convites, contactos, lugares a mesa,
notas, os "Noivos"): so as do GRUPOS.

SEM A FOLHA, a Mesa funciona na mesma: os grupos vem sem nomes e a pagina diz que nao ha nomes.

AS MEDIDAS QUE O PONTO5 TEM ESCRITAS DENTRO DAS FUNCOES (os espacos do rolo, os tempos dos cargos e
do titulo) estao repetidas em MEDIDAS, abaixo. O scripts/testes_mesa_1002.py confirma no codigo do
ponto5 que continuam as mesmas, e mede a altura do rolo com o proprio rolo_de_nomes(): se alguem as
mudar la, o teste diz onde, em vez de a Mesa passar a mostrar outros tempos sem ninguem saber.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISCUSSAO = os.path.join(REPO, "scripts", "discussao")

# OS NUMEROS QUE O ponto5_creditos.py TEM ESCRITOS DENTRO DAS FUNCOES, e nao em constantes. Cada um
# diz de onde vem; o teste_medidas_dos_creditos_iguais_ao_ponto5 procura-os no codigo dele.
MEDIDAS = {
    # rolo_de_nomes(): 90 antes de um titulo novo, 40 entre dois grupos com o mesmo titulo, 14 depois
    # do subtitulo, 78 por linha, o letreiro do titulo cortado em 110 em cima e em baixo, e 20 no fim
    "gap_titulo": 90, "gap_mesmo_titulo": 40, "gap_sub": 14, "linha": 78, "corte_titulo": 110,
    "fim_rolo": 20, "meio_linha": 36,
    # coluna_de_fotos(): 70 entre fotos, 20 de margem a volta, cortada a 900 de altura
    "gap_fotos": 70, "margem_coluna": 20, "altura_max_foto": 900,
    # main(): os tempos e onde comecam o rolo e a coluna
    "t_entrada": 1.5, "t_cargo": 4.2, "t_titulo": 7.0,
    "fracao_nomes": 0.55, "fracao_fotos": 0.4, "inicio_nomes": 0.45, "inicio_fotos": 0.10,
    "fade_rolo": 0.8, "fim_do_rolo": 1.0,
    # os cargos: quem a 110 com 0,28 de espaco, a A/2+40; o cargo a 58, a A/2-80; 0,6 s a acender. Desde a decisao 109
    # (os cargos dele, 2 de outubro a noite) sao as constantes T_CARGO, QUEM_CORPO, QUEM_ESPACO, QUEM_Y, CARGO_CORPO,
    # CARGO_Y e CARGO_ENTRA do ponto5; com varias pessoas num cargo, cada linha a QUEM_ENTRELINHA (1,45) do corpo da
    # seguinte; e a lista vai ate CARGOS_MAX cargos (8), cada um ate PESSOAS_MAX pessoas (4)
    "quem_corpo": 110, "quem_espaco": 0.28, "quem_y": 40, "cargo_corpo": 58, "cargo_y": -80,
    "cargo_entra": 0.6, "quem_entrelinha": 1.45, "cargos_max": 8, "pessoas_max": 4,
    # o titulo final a 130 com 0,18, a aproximar-se (render.LETREIRO_EMPURRA); a data a 58 com 0,30,
    # a A/2+110; o titulo acende em 1 s e apaga-se nos ultimos 2,5 s
    "final_corpo": 130, "final_espaco": 0.18, "data_corpo": 58, "data_espaco": 0.30, "data_y": 110,
    "final_entra": 1.0, "final_sai": 2.5,
    # mascara_das_bordas(): as pontas de cima e de baixo desvanecem em 170 px
    "bordas": 170,
    # AS PARTES, OS NOMES CORRIDOS E A VELOCIDADE (contrato de 3 de outubro, pontos 5 e 5b). As constantes do ponto5
    # (TITULO_ACENDE, TITULO_APAGA_FIM, VEL_FOTOS_LIMITES, VEL_NOMES_LIMITES, FOTO_INTEIRA_MIN, LER_CPS, PARTES_HOJE e
    # PARTES_CARGOS_PRIMEIRO), com estes valores enquanto ele nao as tiver: o titulo que nasce do fim do filme ja aceso
    # comeca titulo_acende antes do fim da entrada e, sem ser a ultima parte, apaga-se com o fade dos cargos; a coluna
    # das fotos escolhe-se de 60 a 300 px/s e os nomes de 30 a 200; avisa-se quando uma foto fica menos de 2 s inteira
    # no ecra e quando uma linha de nomes pede mais do que as 12 letras por segundo das legendas
    "titulo_acende": 1.0, "titulo_apaga_fim": 2.5,
    "vel_fotos_limites": [60.0, 300.0], "vel_nomes_limites": [30.0, 200.0],
    "foto_inteira_min": 2.0, "ler_cps": 12.0,
    "partes_hoje": ["rolo", "cargos", "titulo"], "partes_cargos_primeiro": ["cargos", "rolo", "titulo"],
}
# as medidas de cima que o ponto5 tem em constantes: (chave do MEDIDAS, nome no ponto5, como se le)
CONSTANTES_DAS_PARTES = (("titulo_acende", "TITULO_ACENDE", float), ("titulo_apaga_fim", "TITULO_APAGA_FIM", float),
                         ("vel_fotos_limites", "VEL_FOTOS_LIMITES", lambda v: [float(x) for x in v]),
                         ("vel_nomes_limites", "VEL_NOMES_LIMITES", lambda v: [float(x) for x in v]),
                         ("foto_inteira_min", "FOTO_INTEIRA_MIN", float), ("ler_cps", "LER_CPS", float),
                         ("partes_hoje", "PARTES_HOJE", list), ("partes_cargos_primeiro", "PARTES_CARGOS_PRIMEIRO", list))


def _ponto5():
    """O modulo do ponto5. Importa-lo corre o comum.py, que precisa do ffmpeg (render.ffmpeg())."""
    if DISCUSSAO not in sys.path:
        sys.path.insert(0, DISCUSSAO)
    import ponto5_creditos
    return ponto5_creditos


def grupos_com_nomes(p5, convidados):
    """[{etiqueta, titulo, sub, linhas}] pela ordem do GRUPOS, com os grupos sem ninguem tambem.

    E O por_grupo() DO PONTO5 COM A ETIQUETA. O por_grupo() devolve (titulo, subtitulo, agregados)
    e salta os grupos vazios, e a Mesa precisa da etiqueta, que e a chave com que o est.creditos
    guarda o titulo e o subtitulo que ele escrever. A regra e a mesma: cada pessoa entra no primeiro
    grupo seu, um agregado (a coluna Familia) por linha. O teste_grupos_da_mesa_iguais_ao_ponto5
    compara as linhas com as do por_grupo(), para as duas contas nao se afastarem.
    """
    from PIL import ImageFont
    fonte = ImageFont.truetype(p5.render.FONTE_TEXTO, p5.NOME_CORPO)
    largura = p5.PAINEL_NOMES[1] - p5.PAINEL_NOMES[0]
    outras = letras_de_ler(p5.render, p5.NOME_CORPO)
    usados, saida = set(), []
    for etiqueta, titulo, sub in p5.GRUPOS:
        agregados = {}
        for k, c in enumerate(convidados):
            if k in usados or etiqueta not in c["etiquetas"] or not c["nome"]:
                continue
            usados.add(k)
            agregados.setdefault(c["familia"] or "%s-%d" % (c["nome"], k), []).append(
                ("%s %s" % (c["nome"], c["apelido"])).strip())
        linhas = [parte for pessoas in agregados.values() for parte in p5.quebrar(pessoas, fonte, largura)]
        grupo = {"etiqueta": etiqueta, "titulo": titulo, "sub": sub, "linhas": linhas}
        quebras = quebras_noutras_letras(p5, list(agregados.values()), linhas, fonte, outras, largura)
        if quebras:
            grupo["quebras"] = quebras
        saida.append(grupo)
    return saida


# AS LINHAS DOS NOMES NA LETRA DA LEGENDA DO ESTILO (2 de outubro, a tarde). O rolo_de_nomes() do ponto5
# parte cada agregado com a letra da legenda do estilo da Mesa (letra_de_ler), e uma letra mais larga do
# que o Arial Bold parte mais linhas: o rolo fica mais alto, os nomes andam mais depressa e os creditos
# duram outra coisa. A Mesa nao tem as larguras das letras do render (no telemovel nem tem as letras do
# Windows), por isso as linhas vem daqui, medidas com os mesmos ficheiros que o render abre: para cada letra
# de data/fontes.json que abre neste PC e parte diferente do Arial, quantas pessoas leva cada linha. Os
# nomes nao se repetem: a Mesa tira as pessoas das linhas do Arial (separadas por " · ") e volta a junta-las
# com estas contas (credLinhasDoGrupo). Uma letra que nao abre fica de fora, e a Mesa usa as linhas do
# Arial, que e o que o render faz com ela (render.letra cai no Arial Bold).
def letras_de_ler(render, corpo):
    """[(id, ImageFont)] das letras de data/fontes.json que abrem neste PC, no corpo pedido, sem o Arial Bold."""
    entradas = render.letras_da_mesa()
    saida = []
    for ident in sorted(entradas):
        if ident == render.LETRA_OMISSAO:
            continue
        f = render.abrir_letra(ident, corpo, entradas, avisar=False)
        if f is not None:
            saida.append((ident, f))
    return saida


def pessoas_por_linha(pessoas, linhas):
    """[n]: quantas pessoas seguidas leva cada linha, ou None se as linhas nao forem as pessoas juntas por " · "."""
    contas, k = [], 0
    for ln in linhas:
        n, atual = 0, ""
        while k < len(pessoas) and atual != ln and len(atual) < len(ln):
            atual = (atual + " · " + pessoas[k]) if atual else pessoas[k]
            k += 1
            n += 1
        if atual != ln:
            return None
        contas.append(n)
    return contas if k == len(pessoas) else None


def quebras_noutras_letras(p5, agregados, linhas, fonte_arial, outras, largura):
    """{id da letra: [pessoas por linha]} das letras que partem os nomes deste grupo de outra maneira.

    Vazio quando o grupo nao tem ninguem, ou quando as linhas do Arial nao se deixam separar nas pessoas
    (um nome com " · " la dentro): nesse caso a Mesa fica com as do Arial para esse grupo.
    """
    if not agregados:
        return {}
    pessoas = [p for ag in agregados for p in ag]
    if [p for ln in linhas for p in ln.split(" · ")] != pessoas:
        return {}
    arial = []
    for ag in agregados:
        contas = pessoas_por_linha(ag, p5.quebrar(ag, fonte_arial, largura))
        if contas is None:
            return {}
        arial += contas
    saida = {}
    for ident, f in outras:
        contas = []
        for ag in agregados:
            c = pessoas_por_linha(ag, p5.quebrar(ag, f, largura))
            if c is None:
                contas = None
                break
            contas += c
        if contas is not None and contas != arial:
            saida[ident] = contas
    return saida


def fotos_da_finais(render, largura_foto=760):
    """{id: [largura, altura, altura_na_coluna]} das fotos que tem ficheiro na FINAIS.

    A VERSAO DE CADA FOTO E A DO data/finais.csv (decisao 090), como no fotos_marcadas() do ponto5,
    e uma foto sem ficheiro la fica de fora dos creditos: a Mesa diz isso ao lado dela.

    A ROTACAO DO EXIF CONTA. O coluna_de_fotos() roda cada foto antes de a medir, e 51 das 719 da
    FINAIS estao gravadas deitadas com a marca de rodar: medidas sem rodar, uma foto ao alto
    entrava na conta como deitada e a duracao dos creditos saia errada. So se le o cabecalho de
    cada ficheiro (meio segundo para todas).

    A ALTURA NA COLUNA VEM DAQUI E NAO DA PAGINA: e o round() do Python, que arredonda os meios
    para o par, e o Math.round do browser arredonda-os para cima.
    """
    from PIL import Image
    caminho = os.path.join(REPO, "data", "finais.csv")
    if not os.path.exists(caminho):
        return {}
    saida = {}
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            ficheiro = os.path.join(render.FINAIS, r.get("final") or "")
            if not r.get("final") or not os.path.exists(ficheiro):
                continue
            try:
                with Image.open(ficheiro) as im:
                    w, h = im.size
                    if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):
                        w, h = h, w
            except Exception:
                continue
            if not w or not h:
                continue
            alt = round(h * largura_foto / w)      # como o coluna_de_fotos(), que corta a 900 a seguir
            saida[r["id"]] = [w, h, min(alt, MEDIDAS["altura_max_foto"])]
    return saida


def creditos_para_mesa():
    """O dicionario de window.CREDITOS_NOMES, ou None quando nem o ponto5 se consegue ler.

    Nunca para a geracao da Mesa: uma Mesa sem os creditos continua a ser util, e o que falta
    diz-se no aviso e na propria pagina.
    """
    try:
        p5 = _ponto5()
    except (SystemExit, Exception) as erro:
        print("  AVISO: nao consegui ler o ponto5_creditos.py (%s); a Mesa nao mostra os creditos" % erro)
        return None
    medidas = dict(MEDIDAS)
    try:
        medidas.update({
            "L": p5.L, "A": p5.A,
            "vel_nomes": p5.VELOCIDADE_NOMES, "vel_fotos_max": p5.VELOCIDADE_FOTOS_MAX,
            "nome_corpo": p5.NOME_CORPO, "sub_corpo": p5.SUB_CORPO,
            "cor_nome": list(p5.COR_NOME), "cor_sub": list(p5.COR_SUB),
            "painel_nomes": list(p5.PAINEL_NOMES), "margem_brilho": p5.MARGEM_BRILHO,
            "largura_foto": p5.LARGURA_FOTO, "centro_fotos": p5.CENTRO_FOTOS,
            "titulo_corpo": p5.TITULO_CORPO, "titulo_espaco": p5.TITULO_ESPACO,
            # a altura do titulo de um grupo no rolo: o letreiro a 1x menos os dois cortes. Mede-se
            # com o proprio letreiro, que nao depende do texto (so do corpo e do numero de linhas)
            "titulo_altura": p5.letreiro_1x(["X"], p5.TITULO_CORPO, p5.TITULO_ESPACO).height
                             - 2 * MEDIDAS["corte_titulo"],
            "letreiro_quente": list(p5.render.LETREIRO_QUENTE), "letreiro_claro": list(p5.render.LETREIRO_BRANCO),
            "letreiro_brilho": list(p5.render.LETREIRO_BRILHO), "letreiro_empurra": p5.render.LETREIRO_EMPURRA,
            "fade_fim_imagem": p5.render.FADE_FIM_IMAGEM,
            # os cargos, quem os fez, o titulo final e a data medem-se contra esta fracao da largura (a zona
            # segura dos titulos da EBU): mais largo, o --master do ponto5 para antes de desenhar
            "zona_segura": getattr(p5, "ZONA_SEGURA", 0.90),
        })
        # AS MEDIDAS DOS CARGOS, das constantes do ponto5 quando as tem (decisao 109); sem elas, as de sempre do MEDIDAS
        for chave, nome in (("t_cargo", "T_CARGO"), ("cargo_entra", "CARGO_ENTRA"), ("quem_corpo", "QUEM_CORPO"),
                            ("quem_espaco", "QUEM_ESPACO"), ("quem_entrelinha", "QUEM_ENTRELINHA"), ("quem_y", "QUEM_Y"),
                            ("cargo_corpo", "CARGO_CORPO"), ("cargo_y", "CARGO_Y"), ("cargos_max", "CARGOS_MAX"),
                            ("pessoas_max", "PESSOAS_MAX")):
            if hasattr(p5, nome):
                medidas[chave] = getattr(p5, nome)
        # AS PARTES E A VELOCIDADE (contrato de 3 de outubro), das constantes do ponto5 quando as tem
        for chave, nome, le in CONSTANTES_DAS_PARTES:
            if hasattr(p5, nome):
                medidas[chave] = le(getattr(p5, nome))
        omissoes = {"cargos": [{"cargo": c, "quem": q} for c, q in p5.CARGOS],
                    "titulo": p5.TITULO, "data": p5.DATA}
        vazios = [{"etiqueta": e, "titulo": t, "sub": s, "linhas": []} for e, t, s in p5.GRUPOS]
    except Exception as erro:
        print("  AVISO: o ponto5_creditos.py mudou e a Mesa ja nao o sabe ler (%s); sem creditos" % erro)
        return None
    saida = {"grupos": vazios, "omissoes": omissoes, "medidas": medidas, "fotos": {},
             "folha": "", "sem_nomes": ""}
    try:
        saida["fotos"] = fotos_da_finais(p5.render, p5.LARGURA_FOTO)
    except Exception as erro:
        print("  AVISO: nao consegui medir as fotos da FINAIS (%s); a Mesa usa as medidas da biblioteca" % erro)
    # A FOLHA DE CONVIDADOS: so a mais recente, como o ponto5. Sem ela, os grupos vao vazios.
    try:
        caminho = p5.folha_mais_recente()
        convidados = p5.ler_convidados(caminho)
        saida["grupos"] = grupos_com_nomes(p5, convidados)
        saida["folha"] = os.path.basename(caminho)
    except (SystemExit, Exception) as erro:
        saida["sem_nomes"] = "não encontrei a folha de convidados" if isinstance(erro, SystemExit) \
            else "não consegui ler a folha de convidados"
        print("  AVISO: %s (%s); a Mesa mostra os creditos sem nomes" % (saida["sem_nomes"], erro))
    return saida


def resumo(dados):
    """Uma linha para o gerar_mesa.py dizer o que foi: contagens, nunca nomes."""
    if not dados:
        return "sem creditos"
    linhas = sum(len(g["linhas"]) for g in dados["grupos"])
    com = sum(1 for g in dados["grupos"] if g["linhas"])
    letras = {k for g in dados["grupos"] for k in (g.get("quebras") or {})}
    return "%d linhas de nomes em %d grupos (%d letras partem de outra maneira), %d fotos medidas na FINAIS%s" % (
        linhas, com, len(letras), len(dados["fotos"]), (" (" + dados["sem_nomes"] + ")") if dados["sem_nomes"] else "")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(resumo(creditos_para_mesa()))
