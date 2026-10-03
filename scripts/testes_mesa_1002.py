# -*- coding: utf-8 -*-
"""Os testes do painel dos creditos da Mesa (2 de outubro).

O Tiago pediu, para o dia com a Clara: mudar a ordem das fotos dos creditos "de forma simples e
pratica enquanto os nomes movem" e editar os textos do fim. O painel faz as contas do
scripts/discussao/ponto5_creditos.py dentro do browser, e a ordem e os textos vao para o
est.creditos, que o ponto5 le. Isto guarda as tres coisas que podem partir sem ninguem ver:

  1. as contas da Mesa afastarem-se das do ponto5 (outra altura do rolo, outra coluna, outros
     tempos): a pre-visualizacao passava a mentir sobre a duracao e sobre que nomes estao no ecra
     quando cada foto passa;
  2. a ordem e os textos nao chegarem a base, ou chegarem com o que nao difere do de hoje;
  3. os nomes dos convidados irem parar a um ficheiro do Git.

E O PAINEL ESTILO (2 de outubro, o mesmo dia): a letra, os tamanhos e as cores das legendas, dos
cartoes, do contador e da intro, gravados em est.estilo. Aqui guarda-se que:

  4. as omissoes e os limites da Mesa sao os do render (um "como esta" que nao fosse o filme de hoje
     gravava um estilo que ninguem escolheu), so o que difere vai para a base, e o que vai ja passa
     limpo pelo render.normalizar_estilo();
  5. a Mesa avisa o mesmo que o montar_da_mesa.avisos_do_estilo() (a Mesa avisa, nunca corrige: 083);
  6. o gerar_mesa.py poe as letras de data/fontes.json na pagina, e pede-as ao Google Fonts com cada
     familia uma so vez.

E TIRAR FOTOS DOS CREDITOS (2 de outubro, a noite, contrato seccao 13): o «Tirar» tira a foto da etiqueta, da versao
«Créditos» e da ordem de uma vez, com uma entrada do Anular, sem voltar pela juncao com outro aparelho, e o ponto5 da as
mesmas fotos, a mesma coluna e a mesma duracao que a Mesa (teste_tirar_dos_creditos_*).

E OS CARGOS DOS CREDITOS (2 de outubro, a noite, contrato_creditos_cargos.md e seccao 14; o render e a decisao 109): os cargos
antes dos convidados, de 1 a 8 cargos e de 1 a 4 pessoas por cargo. A Mesa da os mesmos cargos, os mesmos tempos ao bit e o
mesmo desenho que o ponto5, grava so o que ele escolhe (com o Anular e a juncao por partes), e diz «ainda não chega ao filme»
enquanto o render nao os le (teste_cargos_*).

Uso:  py -3.11 scripts/testes_mesa_1002.py

Os testes de node saltam (e dizem-no) num PC sem node. NUNCA ESCREVEM NOMES DE CONVIDADOS: o que
se compara e dito por contagens e alturas.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITOR = os.path.join(REPO, "scripts", "editor_base.html")
PONTO5 = os.path.join(REPO, "scripts", "discussao", "ponto5_creditos.py")
FALHAS, PASSOU, SALTADOS = [], [], []


def _erro_do_node(r):
    """A linha do erro de um node que parou: a ultima e a versao do node (o v24 escreve-a no fim), e o erro vem antes."""
    linhas = [x for x in (r.stderr or r.stdout or "").strip().splitlines() if x.strip() and not x.startswith("Node.js v")]
    erro = next((x for x in reversed(linhas) if "Error" in x), linhas[-1] if linhas else "?")
    onde = next((x.strip() for x in linhas if x.strip().startswith("at ")), "")
    return (erro + (" (" + onde + ")" if onde else ""))[:300]


def verifica(nome, condicao, detalhe=""):
    (PASSOU if condicao else FALHAS).append((nome, detalhe))
    print("  %s  %-58s %s" % ("ok  " if condicao else "FALHA", nome, detalhe))


def salta(nome, motivo):
    SALTADOS.append((nome, motivo))
    print("  saltado  %-55s %s" % (nome, motivo))


def _bloco(html, inicio, problemas):
    """Uma declaracao do script da Mesa ate a chaveta que a fecha. O marcador tem de aparecer UMA
    SO VEZ (a regra que custou metade do editor_base.html a 12 de setembro)."""
    if html.count(inicio) != 1:
        problemas.append("o marcador %r aparece %d vezes no editor_base.html" % (inicio, html.count(inicio)))
        return ""
    i = html.index(inicio)
    prof = 0
    for p in range(html.index("{", i), len(html)):
        if html[p] == "{":
            prof += 1
        elif html[p] == "}":
            prof -= 1
            if prof == 0:
                return html[i:p + 1]
    problemas.append("o bloco de %r nao fecha" % inicio)
    return ""


FUNCOES_CRED = ["function credSemAcentos(", "function credSuave(", "function credPid(", "function credVersao(",
                "function credMarcadas(", "function credFotos(", "function credMedida(", "function credOmissoes(",
                "function credCargo(", "function credTitulo(", "function credData(", "function credGrupoTexto(",
                "function credGrupoPorEtiqueta(", "function credLayout(", "function credContas(",
                "function credNomesNaFoto(", "function credPoe(", "function credMudaTexto(",
                "function credTextosMudados(", "function credMover(", "function credGuardaDesfazer(",
                "function copiaFunda(", "function corpo(", "function aplicar("]


def _correr_node(prelude, corpo_js, problemas):
    """Corre as funcoes da Mesa no node, com `prelude` a fingir o resto da pagina. Devolve o JSON
    que o programa escrever, ou None."""
    node = shutil.which("node")
    html = io.open(EDITOR, encoding="utf-8").read()
    blocos = "\n".join(_bloco(html, m, problemas) for m in FUNCOES_CRED)
    if problemas:
        return None
    programa = '"use strict";\n' + prelude + "\n" + blocos + "\n" + corpo_js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        r = subprocess.run([node, caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if r.returncode != 0:
        problemas.append("o node parou: " + _erro_do_node(r))
        return None
    return json.loads(r.stdout)


PRELUDE = """
var window = {CREDITOS_NOMES: %(cred)s};
var CRED = window.CREDITOS_NOMES;
var credTemFinais = !!(CRED && CRED.fotos && Object.keys(CRED.fotos).length);
var credLay = null, credCampoAberto = null, marcas = 0, baseRev = 7, pilhaDesfazer = [];
var PAGINA_GERACAO = "ensaio", RENDER_LE = {};
var est = %(est)s;
var porId = %(porid)s;
function marcar(){ marcas++; }
function credPinta(){}
function credPintaTextos(){}
function credAberto(){ return false; }
function credMsg(){}
function versaoAtual(){ return est.versoes && est.versoes[0] || null; }
"""


def _montar_mesa_a_parte(prefixo):
    """O texto da Mesa montada pelo gerar_mesa.py numa pasta temporaria, que se apaga logo (a pagina leva os nomes
    dos convidados, e nao fica nenhuma copia dela pelo disco). O SOM SO SE LE (MESA_SOM=ler): um teste nao faz
    copias de som nem tira as que sobram de saida/audio, nem reescreve o indice e o publicar.json de la (o
    revisor de 2 de outubro viu a suite a reescreve-los)."""
    import contextlib
    import gerar_mesa
    import montar_da_mesa      # noqa: F401 - antes do redirect: ele mexe no sys.stdout ao ser importado
    pasta = tempfile.mkdtemp(prefix=prefixo)
    guardado, antes_som = gerar_mesa.SAIDA, os.environ.get("MESA_SOM")
    gerar_mesa.SAIDA = os.path.join(pasta, "mesa.html")
    os.environ["MESA_SOM"] = "ler"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            gerar_mesa.main()
        return io.open(gerar_mesa.SAIDA, encoding="utf-8").read()
    finally:
        gerar_mesa.SAIDA = guardado
        if antes_som is None:
            os.environ.pop("MESA_SOM", None)
        else:
            os.environ["MESA_SOM"] = antes_som
        shutil.rmtree(pasta, ignore_errors=True)


def _prelude(cred, est, porid=None):
    return PRELUDE % {"cred": json.dumps(cred, ensure_ascii=False), "est": json.dumps(est, ensure_ascii=False),
                      "porid": json.dumps(porid or {})}


# ------------------------------------------------------------------------------------------------
def teste_medidas_dos_creditos_iguais_ao_ponto5():
    """As medidas que o creditos_para_mesa.py repete do ponto5 continuam escritas la.

    O DEFEITO QUE ISTO APANHA: o ponto5 tem os espacos do rolo, os tempos dos cargos e do titulo e
    as posicoes escritos dentro das funcoes, e a Mesa repete-os em MEDIDAS. Se alguem mudar la os
    4,2 s de cada cargo, a Mesa continuava a dizer a duracao de antes e o Tiago decidia a ordem e
    os textos a olhar para outro filme.
    """
    import creditos_para_mesa as cm
    fonte = io.open(PONTO5, encoding="utf-8").read()
    M = cm.MEDIDAS
    esperas = [
        ("gap_titulo", r'pecas\.append\(\("gap", %d if pecas else 0\)\)' % M["gap_titulo"]),
        ("gap_mesmo_titulo", r'pecas\.append\(\("gap", %d\)\)' % M["gap_mesmo_titulo"]),
        ("gap_sub", r'pecas\.append\(\("gap", %d\)\)' % M["gap_sub"]),
        ("linha e corte_titulo", r'v\.height - 2 \* %d if tipo == "titulo" else %d' % (M["corte_titulo"], M["linha"])),
        ("fim_rolo", r'\(larg, altura \+ %d\)' % M["fim_rolo"]),
        # o nome escreve-se pelo render.texto_emojis.escrever() desde 2 de outubro a tarde (os emojis a cores): o meio da
        # linha e o mesmo, com font= ou sem ele
        ("meio_linha", r'y \+ %d\), v, (?:font=)?f_nome' % M["meio_linha"]),
        ("gap_fotos", r'gap = %d\b' % M["gap_fotos"]),
        ("margem_coluna", r'alto \+ %d\)' % (2 * M["margem_coluna"])),
        ("altura_max_foto", r'if im\.height > %d' % M["altura_max_foto"]),
        ("tempos", r't_cargo, t_titulo, t_entrada = T_CARGO, %s, %s' % (M["t_titulo"], M["t_entrada"])),
        ("fracao_nomes", r'A \* %s\) / VELOCIDADE_NOMES' % M["fracao_nomes"]),
        ("fracao_fotos", r'A \* %s\) / VELOCIDADE_FOTOS_MAX' % M["fracao_fotos"]),
        ("inicio_nomes", r'int\(A \* %s - tr \* vel_nomes\)' % M["inicio_nomes"]),
        ("inicio_fotos", r'int\(A \* %.2f - tr \* vel_fotos\)' % M["inicio_fotos"]),
        ("fim_do_rolo", r'if tr < t_rolo \+ %s:' % M["fim_do_rolo"]),
        # os cargos contam-se de onde o rolo acaba (2 de outubro): o mesmo segundo nos tempos e no desenho
        ("t_fim_rolo", r't_fim_rolo = %s\b' % M["fim_do_rolo"]),
        ("cargos depois do rolo", r'tc = max\(0\.0, tr - t_rolo - t_fim_rolo\)'),
        ("fade_rolo", r'\(tr - t_rolo \+ %s\) / %s' % (M["fade_rolo"], 2 * M["fade_rolo"])),
        # OS CARGOS (decisao 109): as medidas passaram a constantes do ponto5 (T_CARGO, QUEM_CORPO, QUEM_Y...), que se
        # comparam abaixo com o MEDIDAS; aqui confirma-se que o desenho as usa onde a Mesa as usa
        ("quem", r'letreiro_1x\(g\["pessoas"\], g\["corpo"\], QUEM_ESPACO\)'),
        ("quem_y", r'"y_quem": A // 2 \+ QUEM_Y'),
        ("quem_no_sitio", r'g\["y_quem"\] - nome_img\.height // 2'),
        ("cargo_y", r'"y_cargo": A // 2 \+ CARGO_Y - sobe'),
        ("cargo_sobe", r'math\.floor\(\(len\(pessoas\) - 1\) \* corpo \* QUEM_ENTRELINHA / 2\.0 \+ 0\.5\)'),
        ("cargo_corpo", r'f_cargo = ImageFont\.truetype\(render\.FONTE_TEXTO, CARGO_CORPO\)'),
        ("cargo_entra", r'1\.0 - suave\(\(u - t_cargo \+ CARGO_ENTRA\) / CARGO_ENTRA\)'),
        ("cargo_ja_aceso", r'entra = 1\.0 if \(ja_aceso and u < CARGO_ENTRA\) else suave\(u / CARGO_ENTRA\)'),
        ("quem_encolhe", r'max\(largura_do_letreiro\(p, corpo, QUEM_ESPACO\) for p in pessoas\) > tela'),
        ("final", r'render\.letreiro\(\[TITULO\], %d, %s, 11\)' % (M["final_corpo"], M["final_espaco"])),
        ("data", r'letreiro_1x\(\[DATA\], %d, %.2f\)' % (M["data_corpo"], M["data_espaco"])),
        ("data_y", r'A // 2 \+ %d - data_let\.height // 2' % M["data_y"]),
        ("final_entra_sai", r'suave\(u / %s\) \* \(1\.0 - suave\(\(u - \(t_titulo - %s\)\) / %s\)\)'
         % (M["final_entra"], M["final_sai"], M["final_sai"])),
        ("bordas", r'def mascara_das_bordas\(margem=%d\)' % M["bordas"]),
    ]
    faltam = [nome for nome, padrao in esperas if not re.search(padrao, fonte)]
    # AS CONSTANTES DOS CARGOS (decisao 109), lidas do proprio modulo
    try:
        p5 = cm._ponto5()
        for chave, nome in (("t_cargo", "T_CARGO"), ("cargo_entra", "CARGO_ENTRA"), ("quem_corpo", "QUEM_CORPO"),
                            ("quem_espaco", "QUEM_ESPACO"), ("quem_entrelinha", "QUEM_ENTRELINHA"), ("quem_y", "QUEM_Y"),
                            ("cargo_corpo", "CARGO_CORPO"), ("cargo_y", "CARGO_Y"), ("cargos_max", "CARGOS_MAX"),
                            ("pessoas_max", "PESSOAS_MAX")):
            if M.get(chave) != getattr(p5, nome, None):
                faltam.append("%s (Mesa %r, ponto5 %s = %r)" % (chave, M.get(chave), nome, getattr(p5, nome, None)))
        # AS CONSTANTES DAS PARTES E DA VELOCIDADE (contrato de 3 de outubro), as do MEDIDAS e as que a pagina tem escritas
        for chave, nome, le in cm.CONSTANTES_DAS_PARTES:
            if not hasattr(p5, nome) or M.get(chave) != le(getattr(p5, nome)):
                faltam.append("%s (Mesa %r, ponto5 %s = %r)" % (chave, M.get(chave), nome, getattr(p5, nome, None)))
        pagina = io.open(EDITOR, encoding="utf-8").read()
        if ('var CRED_PARTES_HOJE = %s, CRED_PARTES_PRIMEIRO = %s;' % (json.dumps(p5.PARTES_HOJE), json.dumps(p5.PARTES_CARGOS_PRIMEIRO))) not in pagina:
            faltam.append("as duas ordens de antes escritas na pagina (CRED_PARTES_HOJE e CRED_PARTES_PRIMEIRO)")
        if M.get("titulo_acende") != M.get("final_entra") or M.get("titulo_apaga_fim") != M.get("final_sai"):
            faltam.append("o titulo acende e apaga no fim como sempre (titulo_acende e titulo_apaga_fim contra final_entra e final_sai)")
    except Exception as erro:  # noqa: BLE001
        faltam.append("nao consegui ler o ponto5 (%s)" % erro)
    verifica("Mesa: as medidas dos creditos sao as do ponto5", not faltam,
             ("ja nao encontro no ponto5: %s; acerta o MEDIDAS do creditos_para_mesa.py" % ", ".join(faltam))
             if faltam else "%d medidas confirmadas no codigo do ponto5" % len(esperas))


def teste_rolo_e_coluna_da_mesa_iguais_ao_ponto5():
    """A Mesa faz o rolo, a coluna e os tempos com as mesmas alturas que o ponto5 desenha.

    O DEFEITO QUE ISTO APANHA: o painel decide a velocidade dos nomes e a duracao pela altura do
    rolo e da coluna. Uma conta parecida (um espaco a menos entre grupos, o EXIF esquecido numa
    das 51 fotos rodadas) dava outra duracao e punha outros nomes ao lado de cada foto, que e o
    que a lista existe para mostrar. Mede-se com o proprio rolo_de_nomes() e coluna_de_fotos().
    """
    if not shutil.which("node"):
        salta("Mesa: rolo e coluna iguais ao ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    cred = cm.creditos_para_mesa()
    if not cred:
        verifica("Mesa: rolo e coluna iguais ao ponto5", False, "o creditos_para_mesa nao devolveu nada")
        return
    p5 = cm._ponto5()
    problemas = []
    alturas = {}
    # as fotos marcadas e os textos, da mesma leitura da base que o ponto5 usa. OS TITULOS DOS GRUPOS SAO OS DELE
    # (est.creditos.grupos): a Mesa e o ponto5 juntam dois grupos seguidos com o mesmo titulo, e um titulo mudado
    # parte ou junta pecas do rolo. Ate 2 de outubro, a tarde, o ponto5 aqui usava os titulos de omissao, e o teste
    # falhava por 474 px (dois titulos mudados, 2 x (187 + 90 - 40)) sem haver defeito nenhum.
    caminhos, fonte = p5.fotos_marcadas()
    est = json.load(open(fonte, encoding="utf-8"))
    est = est.get("data", est) if isinstance(est.get("data"), dict) else est
    textos = p5.textos_dos_creditos(est)
    # O ROLO MEDE-SE NA LETRA DA LEGENDA DO ESTILO DELE (3 de outubro): o ponto5 parte os nomes com ela (letra_de_ler) e a
    # Mesa tambem, pelas quebras de cada letra. Sem o estilo posto no render, comparava-se o Arial com o Playfair dele
    # e o teste falhava por 234 px (3 linhas) sem haver defeito nenhum.
    import render
    estilo_dele = est.get("estilo") if isinstance(est.get("estilo"), dict) and est.get("estilo") else None
    blocos = None
    if cred["sem_nomes"]:
        salta("Mesa: rolo igual ao ponto5", "sem a folha de convidados: " + cred["sem_nomes"])
    else:
        blocos, _fora = p5.por_grupo(p5.ler_convidados(p5.folha_mais_recente()), textos["grupos"])
        from PIL import ImageFont
        f_nome = ImageFont.truetype(p5.render.FONTE_TEXTO, p5.NOME_CORPO)
        larg = p5.PAINEL_NOMES[1] - p5.PAINEL_NOMES[0]
        linhas_p5 = [[parte for ag in linhas for parte in p5.quebrar(ag, f_nome, larg)] for _t, _s, linhas in blocos]
        linhas_mesa = [g["linhas"] for g in cred["grupos"] if g["linhas"]]
        if linhas_p5 != linhas_mesa:
            problemas.append("as linhas de nomes da Mesa nao sao as do por_grupo() (%d grupos la, %d aqui)"
                             % (len(linhas_p5), len(linhas_mesa)))
        try:
            render.aplicar_estilo(estilo_dele, [])
            alturas["rolo"] = p5.rolo_de_nomes(blocos).height
            alturas["corridos"] = p5.rolo_de_nomes(blocos, True).height
        finally:
            render.aplicar_estilo(None, [])
    alturas["coluna"] = p5.coluna_de_fotos(caminhos).height if caminhos else 0
    porid = {}
    # OS CARGOS (decisao 109): na mesma leitura, com os cargos primeiro e com cinco cargos (dois acrescentados, um com duas
    # pessoas), os tempos da Mesa sao os do tempos_dos_creditos() ao bit
    saida = _correr_node(_prelude(cred, est, porid), """
var L = credLayout(), variantes = [];
[[false, 0], [true, 0], [false, 2], [true, 2]].forEach(function(v){
  var guarda = est.creditos, cr = JSON.parse(JSON.stringify(est.creditos || {}));
  /* as duas ordens de antes, por grupos e a velocidade de sempre, escolha ele o que escolher na base */
  delete cr.partes; delete cr.cargos_primeiro; delete cr.nomes_corridos; delete cr.velocidade;
  if(v[0]) cr.cargos_primeiro = true;
  if(v[1]) cr.cargos = [0, 1, 2].map(function(k){ return credCargo(k); }).concat([{cargo: "Fotografia", quem: "OS PADRINHOS\\nAS MADRINHAS"},
                                                                                  {cargo: "Bolo", quem: "A AVÓ"}]);
  est.creditos = cr; credLay = null;
  var X = credLayout();
  variantes.push({primeiro: v[0], n: X.nCargos, dur: X.dur, tCargos: X.tCargos, tRoloEntra: X.tRoloEntra, tTituloEntra: X.tTituloEntra});
  est.creditos = guarda; credLay = null;
});
/* AS PARTES, OS NOMES CORRIDOS E A VELOCIDADE (3 de outubro), na mesma leitura: a tabela do contrato, secao 10.6 */
var de3 = %s.map(function(mais){
  var guarda = est.creditos, cr = JSON.parse(JSON.stringify(est.creditos || {}));
  delete cr.partes; delete cr.cargos_primeiro; delete cr.nomes_corridos; delete cr.velocidade;
  Object.keys(mais).forEach(function(k){ cr[k] = mais[k]; });
  est.creditos = cr; credLay = null;
  var X = credLayout(), o = {creditos: cr, Hr: X.Hr, dur: X.dur, tRolo: X.tRolo, vn: X.vn, vf: X.vf, tRoloEntra: X.tRoloEntra, tTituloEntra: X.tTituloEntra,
                             tCargos: X.tCargos, n: X.nCargos, parado: X.parado ? [X.parado.quem, X.parado.s] : null};
  est.creditos = guarda; credLay = null;
  return o;
});
console.log(JSON.stringify({Hr: L.Hr, Hc: L.Hc, n: L.col.length, tRolo: L.tRolo, vn: L.vn, vf: L.vf, dur: L.dur, variantes: variantes, de3: de3}));
""" % json.dumps(VARIANTES_DE_3_DE_OUTUBRO), problemas)
    if saida:
        # O QUE ELE TIVER ESCOLHIDO NA BASE CONTA (3 de outubro): com os nomes corridos o rolo e o corrido, e os tempos
        # sao os da ordem, dos cargos e da velocidade que o textos_dos_creditos() le do est.creditos dele
        rolo_dele = "corridos" if textos["nomes_corridos"] else "rolo"
        if rolo_dele in alturas and saida["Hr"] != alturas[rolo_dele]:
            problemas.append("rolo%s: a Mesa conta %d px, o ponto5 desenha %d" % (" corrido" if textos["nomes_corridos"] else "",
                                                                                 saida["Hr"], alturas[rolo_dele]))
        if saida["Hc"] != alturas["coluna"]:
            problemas.append("coluna: a Mesa conta %d px, o ponto5 desenha %d" % (saida["Hc"], alturas["coluna"]))
        if saida["n"] != len(caminhos):
            problemas.append("fotos na coluna: a Mesa tem %d, o ponto5 %d" % (saida["n"], len(caminhos)))
        # OS TEMPOS SAO OS DO PROPRIO PONTO5 (tempos_dos_creditos), com as alturas dele: desde 2 de outubro os cargos
        # contam-se de onde o rolo acaba (t_rolo + 1,0), e uma conta escrita aqui a mao continuava a passar com a
        # duracao antiga (o render viu-o)
        hr = alturas.get("rolo", saida["Hr"])
        T = p5.tempos_dos_creditos(alturas.get(rolo_dele, saida["Hr"]), alturas["coluna"], len(textos["cargos"]), textos["cargos_primeiro"],
                                   textos["partes"], textos["velocidade"])
        t_rolo, dur = T["t_rolo"], T["dur"]
        if abs(saida["dur"] - dur) > 1e-6 or abs(saida["tRolo"] - t_rolo) > 1e-6:
            problemas.append("duracao: a Mesa da %.3f s, o ponto5 %.3f s" % (saida["dur"], dur))
        for v in saida["variantes"]:
            Tv = p5.tempos_dos_creditos(hr, alturas["coluna"], v["n"], v["primeiro"])
            if (v["dur"], v["tCargos"], v["tRoloEntra"], v["tTituloEntra"]) != (Tv["dur"], Tv["t_cargos"], Tv["t_rolo_entra"],
                                                                                Tv["t_titulo_entra"]):
                problemas.append("%d cargos%s: a Mesa da %.4f s, o ponto5 %.4f s" % (
                    v["n"], " primeiro" if v["primeiro"] else "", v["dur"], Tv["dur"]))
        # AS PARTES, OS NOMES CORRIDOS E A VELOCIDADE: o rolo corrido e o proprio rolo_de_nomes(blocos, True), e os
        # tempos os do tempos_dos_creditos() com o que o textos_dos_creditos() le do mesmo est.creditos
        for v in saida["de3"]:
            t3 = p5.textos_dos_creditos({"creditos": v["creditos"]}, [])
            hr3 = alturas.get("corridos" if t3["nomes_corridos"] else "rolo", v["Hr"])
            if v["Hr"] != hr3:
                problemas.append("rolo%s: a Mesa conta %d px, o ponto5 desenha %d" % (" corrido" if t3["nomes_corridos"] else "", v["Hr"], hr3))
            T3 = p5.tempos_dos_creditos(hr3, alturas["coluna"], len(t3["cargos"]), t3["cargos_primeiro"], t3["partes"], t3["velocidade"])
            da_mesa = (v["dur"], v["tRolo"], v["vn"], v["vf"], v["tRoloEntra"], v["tTituloEntra"], v["tCargos"], v["n"], v["parado"])
            do_p5 = (T3["dur"], T3["t_rolo"], T3["vel_nomes"], T3["vel_fotos"], T3["t_rolo_entra"], T3["t_titulo_entra"], T3["t_cargos"],
                     T3["n_cargos"], list(T3["parado"]) if T3.get("parado") else None)
            if da_mesa != do_p5:
                problemas.append("%s%s%s: a Mesa da %.4f s, o ponto5 %.4f s" % (
                    ", ".join(t3["partes"]), ", corridos" if t3["nomes_corridos"] else "",
                    (", " + str(t3["velocidade"])) if t3["velocidade"] else "", v["dur"], T3["dur"]))
    verifica("Mesa: rolo, coluna e tempos iguais ao ponto5", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "rolo %s px (corrido %s), coluna %d px de %d fotos, creditos %.4f s; com os cargos primeiro e com cinco cargos, ao bit: %s; "
             "e as partes, os corridos e a velocidade de 3 de outubro: %s"
             % (alturas.get("rolo", "sem nomes"), alturas.get("corridos", "sem nomes"), alturas["coluna"], len(caminhos), saida["dur"],
                ", ".join("%.4f" % v["dur"] for v in saida["variantes"]), ", ".join("%.3f" % v["dur"] for v in saida["de3"])))


# as linhas da tabela do contrato de 3 de outubro (saida/discussao/contrato_1003.md, secao 10.6), na leitura mais recente
VARIANTES_DE_3_DE_OUTUBRO = [
    {"partes": ["titulo", "rolo"]}, {"partes": ["titulo", "rolo"], "nomes_corridos": True}, {"partes": ["titulo", "cargos", "rolo"]},
    {"partes": ["rolo", "titulo"]}, {"partes": ["cargos", "titulo", "rolo"]},
    {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"fotos": 100}},
    {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"nomes": 60}},
    {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"fotos": 200, "nomes": 40}},
    {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"fotos": 300}},
]


def _cred_de_ensaio():
    """Um CREDITOS_NOMES pequeno, sem nomes verdadeiros, com as medidas de verdade."""
    import creditos_para_mesa as cm
    M = dict(cm.MEDIDAS)
    M.update({"L": 1920, "A": 1080, "vel_nomes": 150.0, "vel_fotos_max": 150.0, "nome_corpo": 58, "sub_corpo": 58,
              "largura_foto": 760, "titulo_altura": 187, "painel_nomes": [960, 1880], "margem_brilho": 60,
              "titulo_corpo": 60, "titulo_espaco": 0.18, "letreiro_empurra": 0.025, "fade_fim_imagem": 2.5})
    return {"medidas": M, "folha": "ensaio.xlsx", "sem_nomes": "",
            "omissoes": {"cargos": [{"cargo": "Cargo A", "quem": "QUEM A"}, {"cargo": "Cargo B", "quem": "QUEM B"},
                                    {"cargo": "Cargo C", "quem": "QUEM C"}], "titulo": "TITULO", "data": "DATA"},
            "grupos": [{"etiqueta": "Grupo 1", "titulo": "T1", "sub": "s1", "linhas": ["P1 · P2", "P3"]},
                       {"etiqueta": "Grupo 2", "titulo": "T1", "sub": "s2", "linhas": ["P4"]},
                       {"etiqueta": "Grupo 3", "titulo": "T3", "sub": "s3", "linhas": []}],
            # a f05 nao tem ficheiro na FINAIS: o ponto5 deixa-a de fora da coluna
            "fotos": {"f01": [4000, 3000, 570], "f02": [3000, 4000, 900], "f03": [1000, 1000, 760],
                      "f04": [4000, 3000, 570]}}


def teste_ordem_das_fotos_dos_creditos():
    """A lista das fotos dos creditos segue o contrato: a ordem dele, a versao, o numero da Mesa.

    O DEFEITO QUE ISTO APANHA: uma foto marcada que nao estivesse na ordem dele desaparecia da
    coluna sem ninguem saber, ou uma foto a que ele tirou a etiqueta continuava nos creditos. E o
    grupo "Créditos" tem de se encontrar como no ponto5, sem acentos e sem maiusculas.
    """
    if not shutil.which("node"):
        salta("Mesa: ordem das fotos dos creditos", "sem node neste PC")
        return
    problemas = []
    pessoas = [{"id": "p_a", "nome": "Clara"}, {"id": "p_c", "nome": " CRÉDITOS "}]
    base = {"pessoas": pessoas, "tags": {"f03": ["p_c"], "f01": ["p_c", "p_a"], "f05": ["p_c"], "f02": ["p_a"]},
            "versoes": [{"id": "v1", "nome": "demo", "clips": []}]}
    casos = []
    # 1. so a etiqueta: o numero da Mesa
    casos.append(("numero", base, ["f01", "f03", "f05"], "numero", 0, 0))
    # 2. a versao Creditos: a ordem dos clips, os grupos por dentro, os cartoes nao contam; uma marcada fora
    #    da versao vai para o fim como nova; uma da versao sem a etiqueta conta (como no ponto5)
    e2 = json.loads(json.dumps(base))
    e2["versoes"].append({"id": "vc", "nome": "Créditos", "clips": [
        {"t": "cartao", "x": "ola"}, {"t": "foto", "i": "f05"}, {"t": "colagem", "fotos": ["f02", "f03"]}]})
    casos.append(("versao", e2, ["f05", "f02", "f03", "f01"], "versao", 1, 1))
    # 3. a ordem dele manda: um repetido conta uma vez, uma marcada fora vai para o fim, e a f02, da versao
    #    sem a etiqueta, FICA (corretor, 2 de outubro: a primeira seta tirava-a da coluna sem ele lhe tocar;
    #    o ponto5_creditos.ordem_das_fotos() segue a mesma regra, e o teste_creditos_seguem_a_ordem_da_mesa
    #    corre os dois lados)
    e3 = json.loads(json.dumps(e2))
    e3["creditos"] = {"ordem": ["f05", "f02", "f05", "f03"]}
    casos.append(("ordem", e3, ["f05", "f02", "f03", "f01"], "ordem", 1, 1))
    # 4. sai so a que nao tem a etiqueta nem esta na versao (a f04); a f02, da versao e fora da ordem dele,
    #    vai para o fim como nova, depois das marcadas
    e4 = json.loads(json.dumps(e2))
    e4["creditos"] = {"ordem": ["f04", "f03", "f05"]}
    casos.append(("ordemSai", e4, ["f03", "f05", "f01", "f02"], "ordem", 2, 1))
    js = "var r = {};\n"
    for nome, est, _l, _o, _n, _s in casos:
        js += "est = %s; credLay = null; var F = credFotos(); r[%r] = {ids: F.lista.map(function(x){ return x.id; }), " \
              "origem: F.origem, novas: F.novas, semEtiqueta: F.semEtiqueta, perdidas: F.perdidas, faltam: F.faltam, " \
              "coluna: credLayout().col.map(function(p){ return p.id; })};\n" % (
                  json.dumps(est, ensure_ascii=False), nome)
    js += "console.log(JSON.stringify(r));"
    saida = _correr_node(_prelude(_cred_de_ensaio(), base), js, problemas)
    if saida:
        for nome, _e, ids, origem, novas, sem in casos:
            s = saida[nome]
            if s["ids"] != ids or s["origem"] != origem or s["novas"] != novas or s["semEtiqueta"] != sem:
                problemas.append("%s: deu %s (%s, %d novas, %d sem etiqueta), esperava %s"
                                 % (nome, s["ids"], s["origem"], s["novas"], s["semEtiqueta"], ids))
        if saida["ordem"]["perdidas"] != 0:
            problemas.append("ordem: a foto da versao sem a etiqueta foi contada como saida")
        if saida["ordemSai"]["perdidas"] != 1:
            problemas.append("ordem: a foto sem a etiqueta e fora da versao nao foi contada como saida")
        # a f05, sem versao final, fica na lista (marcada) e fora da coluna, como no fotos_marcadas()
        if saida["numero"]["faltam"] != 1 or saida["numero"]["coluna"] != ["f01", "f03"]:
            problemas.append("a foto sem versao final: %d marcadas, coluna %s" % (saida["numero"]["faltam"],
                                                                                saida["numero"]["coluna"]))
    verifica("Mesa: ordem das fotos dos creditos como no contrato", not problemas,
             "; ".join(problemas)[:300] if problemas else "%d casos: numero, versao Creditos, ordem dele" % len(casos))


def teste_creditos_gravam_so_o_que_difere():
    """O est.creditos so guarda o que ele mudou, vai para a base no corpo() e volta no aplicar().

    O DEFEITO QUE ISTO APANHA: um campo escrito com o valor de omissao ficava no est.creditos e o
    ponto5 passava a usar um texto fixo da Mesa em vez do seu, ou um texto voltado ao de hoje nao
    saia; e um corpo() que nao levasse os creditos gravava tudo menos eles, sem aviso nenhum (a
    Mesa so grava o que o corpo() leva: foi assim que o focos quase se perdeu).
    """
    if not shutil.which("node"):
        salta("Mesa: os creditos gravam so o que difere", "sem node neste PC")
        return
    problemas = []
    base = {"pessoas": [{"id": "p_c", "nome": "Creditos"}], "tags": {"f01": ["p_c"], "f02": ["p_c"], "f03": ["p_c"]},
            "versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}], "atual": "v1"}
    js = """
var r = {};
credMudaTexto("cargo", "1", "Outro cargo");
r.umCargo = JSON.parse(JSON.stringify(est.creditos));
credMudaTexto("cargo", "1", "Cargo B");
r.devolta = est.creditos === undefined ? null : JSON.parse(JSON.stringify(est.creditos));
credMudaTexto("gtitulo", "Grupo 2", "OUTRO");
credMudaTexto("titulo", "", "  CLARA E TIAGO  ");
r.grupo = JSON.parse(JSON.stringify(est.creditos));
credMudaTexto("gtitulo", "Grupo 2", "");
credMudaTexto("titulo", "", "");
r.vazio = est.creditos === undefined ? null : JSON.parse(JSON.stringify(est.creditos));
credMover(0, 2);
r.ordem = JSON.parse(JSON.stringify(est.creditos));
r.anular = pilhaDesfazer.length;
pilhaDesfazer[pilhaDesfazer.length - 1].aoAnular();
r.anulado = est.creditos === undefined ? null : est.creditos;
credMover(2, 0);
var c1 = corpo();
r.corpoCom = c1.creditos ? Object.keys(c1.creditos) : null;
delete est.creditos;
var c2 = corpo();
r.corpoSem = Object.prototype.hasOwnProperty.call(c2, "creditos");
aplicar({versoes: [{id: "v1", clips: []}], atual: "v1", creditos: {titulo: "X"}});
r.lido = est.creditos ? est.creditos.titulo : null;
aplicar({versoes: [{id: "v1", clips: []}], atual: "v1"});
r.lidoSem = est.creditos === undefined;
r.marcas = marcas;
console.log(JSON.stringify(r));
"""
    s = _correr_node(_prelude(_cred_de_ensaio(), base), js, problemas)
    if s:
        if not (s["umCargo"].keys() == {"cargos"} and len(s["umCargo"]["cargos"]) == 3
                and s["umCargo"]["cargos"][1] == {"cargo": "Outro cargo", "quem": "QUEM B"}):
            problemas.append("mudar um cargo nao guardou os tres: %s" % s["umCargo"])
        if s["devolta"] is not None:
            problemas.append("o cargo voltado ao de omissao continuou guardado: %s" % s["devolta"])
        if s["grupo"] != {"grupos": {"Grupo 2": {"titulo": "OUTRO", "sub": "s2"}}, "titulo": "CLARA E TIAGO"}:
            problemas.append("o titulo do grupo ou o titulo final nao ficaram como deviam: %s" % s["grupo"])
        if s["vazio"] is not None:
            problemas.append("campos vazios deviam voltar ao de omissao e o est.creditos sair: %s" % s["vazio"])
        if s["ordem"] != {"ordem": ["f02", "f03", "f01"]}:
            problemas.append("mover a 1.a para o 3.o lugar deu %s" % s["ordem"])
        if s["anular"] < 1 or s["anulado"] is not None:
            problemas.append("o anular da ordem nao repos o est.creditos de antes")
        if s["corpoCom"] != ["ordem"] or s["corpoSem"]:
            problemas.append("o corpo() nao leva os creditos so quando existem (%s, %s)" % (s["corpoCom"], s["corpoSem"]))
        if s["lido"] != "X" or not s["lidoSem"]:
            problemas.append("o aplicar() nao le os creditos da base")
        if s["marcas"] < 6:
            problemas.append("so %d gravacoes pedidas: cada mudanca tem de passar pelo marcar()" % s["marcas"])
    verifica("Mesa: os creditos gravam so o que difere", not problemas,
             "; ".join(problemas)[:300] if problemas else "cargos, grupos, titulo, ordem, anular, corpo e aplicar")


def teste_nomes_dos_convidados_so_na_mesa_montada():
    """Os nomes dos convidados so vao para o saida/mesa.html, e so os das etiquetas de GRUPOS.

    O DEFEITO QUE ISTO APANHA: a folha de convidados tem 140 pessoas, e o contrato diz que os nomes
    nunca entram num ficheiro do Git, nem as etiquetas que nao vao ao ecra (convites, contactos,
    lugares a mesa, notas, os Noivos). Monta-se a Mesa numa pasta de fora e confirma-se que nenhum
    ficheiro de data/, scripts/ ou docs/ mudou nem traz um nome da folha. Nunca diz qual nome.
    """
    import creditos_para_mesa as cm
    try:
        p5 = cm._ponto5()
        convidados = p5.ler_convidados(p5.folha_mais_recente())
    except (SystemExit, Exception) as erro:
        salta("Mesa: nomes so na Mesa montada", "sem a folha de convidados (%s)" % erro)
        return
    problemas = []
    nomes = {("%s %s" % (c["nome"], c["apelido"])).strip() for c in convidados
             if c["nome"] and c["apelido"] and "Noivos" not in c["etiquetas"]}
    etiquetas_grupos = {e for e, _t, _s in p5.GRUPOS}
    proibidas = {e for c in convidados for e in c["etiquetas"]} - etiquetas_grupos

    def com_nomes_em(caminho):
        try:
            texto = io.open(caminho, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            return 0
        return sum(1 for nome in nomes if nome in texto)

    # O QUE A MONTAGEM ESCREVER EM data/, scripts/ OU docs/ NAO PODE TER NOMES. Ve-se pela hora de
    # cada ficheiro, e nao pelo git status: outras equipas mexem na mesma arvore ao mesmo tempo.
    import time
    inicio = time.time() - 1
    montada = _montar_mesa_a_parte("mesa_1002_")
    escritos = []
    for pasta_repo in ("data", "scripts", "docs"):
        for raiz, _ds, fs in os.walk(os.path.join(REPO, pasta_repo)):
            for f in fs:
                c = os.path.join(raiz, f)
                if os.path.getmtime(c) >= inicio and com_nomes_em(c):
                    escritos.append(os.path.relpath(c, REPO))
    if escritos:
        problemas.append("montar a Mesa escreveu nomes em ficheiros do repositorio: %s" % ", ".join(escritos[:3]))
    m = re.search(r"window\.CREDITOS_NOMES = (\{.*?\});\n</script>", montada, re.S)
    cred = json.loads(m.group(1).replace("<\\/", "</")) if m else None
    if not cred:
        problemas.append("a Mesa montada nao traz o window.CREDITOS_NOMES")
    else:
        if {g["etiqueta"] for g in cred["grupos"]} - etiquetas_grupos:
            problemas.append("ha etiquetas na Mesa que nao sao de GRUPOS")
        texto = json.dumps(cred, ensure_ascii=False)
        vazadas = [e for e in proibidas if json.dumps(e, ensure_ascii=False) in texto]
        if vazadas:
            problemas.append("%d etiquetas que nao vao ao ecra estao na Mesa" % len(vazadas))
        if not any(n in montada for n in nomes):
            problemas.append("a Mesa montada nao tem os nomes (o painel ficava sem eles)")
    # NENHUM FICHEIRO DO GIT em data/, scripts/ ou docs/ traz um nome da folha. Um nome que ja vem
    # nas legendas do material da mae da Clara (o inventario.csv e o original_mae.csv, do .wlmp) nao
    # veio da folha: esta no ecra desde o video dela, e nao conta. A 2 de outubro havia um assim.
    material = "".join(io.open(os.path.join(REPO, "data", f), encoding="utf-8-sig").read()
                       for f in ("inventario.csv", "original_mae.csv"))
    nomes = {nome for nome in nomes if nome not in material}
    r = subprocess.run(["git", "ls-files", "--", "data", "scripts", "docs"], cwd=REPO, capture_output=True,
                       text=True, encoding="utf-8")
    com_nomes = []
    for rel in r.stdout.splitlines():
        caminho = os.path.join(REPO, rel)
        if not os.path.isfile(caminho) or os.path.getsize(caminho) > 20 * 1024 * 1024:
            continue
        n = com_nomes_em(caminho)
        if n:
            com_nomes.append("%s (%d)" % (rel, n))
    for rel in ("scripts/creditos_para_mesa.py", "scripts/testes_mesa_1002.py"):
        texto = io.open(os.path.join(REPO, rel), encoding="utf-8").read()
        if any(nome in texto for nome in nomes):
            com_nomes.append(rel)
    if com_nomes:
        problemas.append("ficheiros com nomes da folha: %s" % ", ".join(com_nomes[:6]))
    verifica("Mesa: os nomes dos convidados so na Mesa montada", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d nomes, %d etiquetas de fora, nenhum num ficheiro do Git" % (len(nomes), len(proibidas)))


def teste_script_da_mesa_compila():
    """O script da Mesa passa no node --check."""
    node = shutil.which("node")
    if not node:
        salta("Mesa: o script compila", "sem node neste PC")
        return
    html = io.open(EDITOR, encoding="utf-8").read()
    js = max(re.findall(r"<script[^>]*>(.*?)</script>", html, re.S), key=len)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(js)
        caminho = fh.name
    try:
        r = subprocess.run([node, "--check", caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    verifica("Mesa: o script passa no node --check", r.returncode == 0, (r.stderr or "").strip()[:200])


# ------------------------------------------------------------- dois aparelhos ao mesmo tempo (corretor)
DECLARACOES_JUNTAR = ["var PAGINA_GERACAO = ", "var CAMPOS_DA_BASE = ", "var NOMES_DOS_CAMPOS = ", "var CADEIA_MAX = "]
FUNCOES_JUNTAR = ["function textoDoCampo(", "function partesDe(", "function campoDaBaseLida(", "function camposDe(",
                  "function poeNoCaminho(", "function fotografia(", "function nomesDosCampos(", "function juntarComBase(",
                  "function depoisDeJuntar(", "function registarBase(", "function contarBase(", "function corpo(",
                  "function textoDaJuncao(", "function textoDosRepostos(", "function desfazer(",
                  "function credGuardaDesfazer(", "function estiloGuardaDesfazer(", "function copiaFunda(", "function cadeiaDe("]
PRELUDE_JUNTAR = """
var est = null, baseRev = 0, baseRemota = "", contagensBase = null, baseLida = null, pilhaDesfazer = [];
var clipAtivo = -1, selClips = [], ancoraSel = -1, credLay = null, credArrasto = null, credCampoAberto = null;
var estiloCampoAberto = null, marcas = 0, avisos = [];
var document = {activeElement: null, getElementById: function(){ return null; }};
function nada(){}
var pintaVersoes = nada, pintaGrelha = nada, pintaClips = nada, pintaPincel = nada, pintaInspetor = nada,
    pintaFiltroPessoas = nada, pintaBarraClips = nada, estiloNaPagina = nada, credPinta = nada, credPintaTextos = nada,
    estiloPinta = nada, credFimDoArrasto = nada;
function credAberto(){ return false; }
function estiloAberto(){ return false; }
var ocupado = false;
function aMeioDeClips(){ return ocupado; }
function marcar(){ marcas++; }
function avisar(t){ avisos.push(t); }
function versaoAtual(){ for(var k = 0; k < est.versoes.length; k++) if(est.versoes[k].id === est.atual) return est.versoes[k]; return null; }
function copia(x){ return JSON.parse(JSON.stringify(x)); }
/* uma pagina que leu a base B: o que o arranque faz (registarBase e aplicar, que liga est aos objetos) */
function abrir(B){ est = copia(B); registarBase(copia(B), false); est.focos = est.focos || {}; est.excluidas = est.excluidas || {};
  pilhaDesfazer.length = 0; }
"""


def teste_juntar_dois_aparelhos():
    """Dois aparelhos a mexer em partes diferentes juntam-se; na mesma parte, e o conflito de sempre.

    O DEFEITO QUE ISTO APANHA (corretor, 2 de outubro): com o Tiago e a Clara em dois aparelhos, uma
    gravacao de um punha o outro em conflito, e tudo o que esse fazia a seguir ia para a copia; o
    «Guardar esta cópia» apagava o que o primeiro tinha gravado. E uma Mesa antiga, que nao conhece os
    creditos nem o estilo, gravava sem eles e eles desapareciam da base. Tambem: o Anular dos paineis
    trocava a versao aberta.
    """
    if not shutil.which("node"):
        salta("Mesa: dois aparelhos juntam-se", "sem node neste PC")
        return
    problemas = []
    html = io.open(EDITOR, encoding="utf-8").read()
    blocos = "\n".join([_declaracao(html, m, problemas) for m in DECLARACOES_JUNTAR] +
                       [_bloco(html, m, problemas) for m in FUNCOES_JUNTAR])
    if problemas:
        verifica("Mesa: dois aparelhos juntam-se", False, "; ".join(problemas)[:300])
        return
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]},
                      {"id": "v2", "nome": "outra", "clips": []}],
          "pessoas": [{"id": "p_c", "nome": "Creditos"}], "tags": {"f01": ["p_c"]}, "atual": "v1",
          "quando": "2026-10-02T10:00:00Z", "rev": 5, "pagina": "2026-10-02"}
    js = """
var r = {}, B0 = %s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
// A. partes diferentes: aqui os creditos, la o estilo
abrir(B0); est.creditos = {titulo: "AQUI"};
var j = juntarComBase(com({estilo: {legenda: {tamanho: 56}}, rev: 6, quando: "2026-10-02T10:01:00Z"}));
var c = corpo();
r.A = {ok: j.ok, meus: j.meus, deles: j.deles, rev: baseRev, titulo: c.creditos && c.creditos.titulo,
       tam: c.estilo && c.estilo.legenda.tamanho, corpoRev: c.rev, pagina: c.pagina, texto: textoDaJuncao(j, 7)};
// B. a mesma parte: o conflito, e a pagina fica como estava
abrir(B0); est.creditos = {titulo: "AQUI"};
j = juntarComBase(com({creditos: {titulo: "LA"}, rev: 6}));
r.B = {ok: j.ok, choque: j.choque, titulo: est.creditos.titulo, rev: baseRev};
// C. uma Mesa antiga (sem pagina) gravou sem os creditos que a base tinha, e mudou a montagem
var B1 = com({creditos: {titulo: "T"}});
abrir(B1);
var antiga = com({creditos: undefined, pagina: undefined, rev: 6});
antiga.versoes[0].clips.push({t: "foto", i: "f02"});
j = juntarComBase(antiga);
c = corpo();
r.C = {ok: j.ok, deles: j.deles, repostos: j.repostos, titulo: c.creditos && c.creditos.titulo, clips: c.versoes[0].clips.length,
       meusDepois: juntarComBase(com({creditos: undefined, rev: 6, pagina: "x"})) ? "repetiu" : "", texto: textoDosRepostos(j.repostos)};
// D. uma Mesa nova tirou os creditos de proposito: saem tambem aqui
abrir(B1);
j = juntarComBase(com({creditos: undefined, rev: 6}));
r.D = {ok: j.ok, deles: j.deles, repostos: j.repostos, tem: est.creditos !== undefined};
// E. a montagem mudada nos dois: conflito; F. a montagem vazia na base: recusa
abrir(B0); est.versoes[0].clips.push({t: "foto", i: "f03"});
var outra = com({rev: 6}); outra.versoes[0].clips = [];
j = juntarComBase(outra);
r.E = {ok: j.ok, choque: j.choque};
abrir(B0);
j = juntarComBase(com({versoes: [], rev: 6}));
r.F = {ok: !!(j && j.ok), nulo: j === null};
// G. os focos e as excluidas que o arranque poe a {} nao sao mudancas desta pagina
abrir(B0);
j = juntarComBase(com({focos: {f01: {x: .5}}, rev: 6}));
r.G = {ok: j.ok, meus: j.meus, deles: j.deles};
// H. o anular: as entradas do que veio do outro aparelho saem, as outras ficam
abrir(B0);
pilhaDesfazer.push({v: "v1", clips: [], rotulo: "mover 1 clip"});
credGuardaDesfazer("mudar a ordem"); estiloGuardaDesfazer("mudar a letra");
juntarComBase(com({estilo: {legenda: {tamanho: 50}}, rev: 6}));
r.H1 = pilhaDesfazer.map(function(u){ return u.rotulo; });
juntarComBase(com({estilo: {legenda: {tamanho: 50}}, versoes: [{id: "v1", nome: "demo", clips: []}], rev: 7}));
r.H2 = pilhaDesfazer.map(function(u){ return u.rotulo; });
// J. no estilo, cada coisa e uma parte: a cor aqui e o tamanho la juntam-se; a mesma coisa nos dois e conflito
abrir(com({estilo: {intro: {fundo: "#132036"}}}));
est.estilo = {intro: {fundo: "#132036"}, legenda: {cor: "#FFF6E5"}};
j = juntarComBase(com({estilo: {intro: {fundo: "#132036"}, legenda: {tamanho: 50}}, rev: 6}));
r.J = {ok: j.ok, estilo: est.estilo, corpo: corpo().estilo};
abrir(B0); est.estilo = {legenda: {tamanho: 52}};
j = juntarComBase(com({estilo: {legenda: {tamanho: 50}}, rev: 6}));
r.J2 = {ok: j.ok, choque: j.choque};
// K. nos creditos: a ordem aqui e o titulo de um grupo la juntam-se; tirar la a unica coisa do estilo tira o estilo
abrir(com({creditos: {grupos: {"G.1": {titulo: "A", sub: "a"}}}, estilo: {nome: {tamanho: 130}}}));
est.creditos.ordem = ["f01"];
j = juntarComBase(com({creditos: {grupos: {"G.1": {titulo: "B", sub: "a"}}}, rev: 6}));
r.K = {ok: j.ok, deles: j.deles, creditos: est.creditos, estilo: est.estilo === undefined ? null : est.estilo};
// L. a meio de uma mudanca nos clips (a substituir uma foto, outra janela aberta), a montagem do outro nao entra
abrir(B0); ocupado = true;
var outraMont = com({rev: 6}); outraMont.versoes[0].clips.push({t: "foto", i: "f09"});
j = juntarComBase(outraMont);
var j2 = juntarComBase(com({estilo: {legenda: {tamanho: 50}}, rev: 6}));
ocupado = false;
r.L = {ok: j.ok, choque: j.choque, clips: est.versoes[0].clips.length, estiloOk: j2.ok};
// I. o anular de um painel nao troca a versao aberta
abrir(B0);
credGuardaDesfazer("mudar o titulo"); est.creditos = {titulo: "NOVO"};
est.atual = "v2";
desfazer();
r.I = {atual: est.atual, creditos: est.creditos === undefined ? null : est.creditos, marcas: marcas > 0};
console.log(JSON.stringify(r));
""" % json.dumps(B0)
    programa = '"use strict";\n' + PRELUDE_JUNTAR + "\n" + blocos + "\n" + js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        p = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if p.returncode != 0:
        verifica("Mesa: dois aparelhos juntam-se", False, "o node parou: " + " | ".join((p.stderr or p.stdout).strip().splitlines()[:5])[:300])
        return
    r = json.loads(p.stdout)
    A, B, C, D, E, F, G = (r[k] for k in "ABCDEFG")
    if not (A["ok"] and A["meus"] == ["creditos"] and A["deles"] == ["estilo"] and A["rev"] == 6 and A["titulo"] == "AQUI"
            and A["tam"] == 56 and A["corpoRev"] == 7 and A["pagina"] and "o estilo" in A["texto"]):
        problemas.append("partes diferentes: %s" % A)
    if B["ok"] or B["choque"] != ["creditos"] or B["titulo"] != "AQUI" or B["rev"] != 5:
        problemas.append("a mesma parte: %s" % B)
    if not (C["ok"] and C["deles"] == ["versoes"] and C["repostos"] == ["creditos"] and C["titulo"] == "T"
            and C["clips"] == 2 and "Mesa antiga" in C["texto"]):
        problemas.append("a Mesa antiga: %s" % C)
    if not D["ok"] or D["deles"] != ["creditos"] or D["repostos"] or D["tem"]:
        problemas.append("tirados de proposito: %s" % D)
    if E["ok"] or E["choque"] != ["versoes"]:
        problemas.append("a montagem nos dois: %s" % E)
    if F["ok"] or not F["nulo"]:
        problemas.append("a montagem vazia: %s" % F)
    if not G["ok"] or G["meus"] or G["deles"] != ["focos"]:
        problemas.append("os focos do arranque: %s" % G)
    if r["H1"] != ["mover 1 clip", "mudar a ordem"] or r["H2"] != ["mudar a ordem"]:
        problemas.append("o anular depois de juntar: %s, %s" % (r["H1"], r["H2"]))
    J = r["J"]
    if not J["ok"] or J["estilo"] != {"intro": {"fundo": "#132036"}, "legenda": {"cor": "#FFF6E5", "tamanho": 50}}             or J["corpo"] != J["estilo"]:
        problemas.append("o estilo, coisas diferentes: %s" % J)
    if r["J2"]["ok"] or r["J2"]["choque"] != ["estilo"]:
        problemas.append("o estilo, a mesma coisa: %s" % r["J2"])
    K = r["K"]
    if not K["ok"] or K["deles"] != ["creditos", "estilo"] or K["estilo"] is not None             or K["creditos"] != {"grupos": {"G.1": {"titulo": "B", "sub": "a"}}, "ordem": ["f01"]}:
        problemas.append("os creditos, coisas diferentes: %s" % K)
    if r["L"] != {"ok": False, "choque": ["versoes"], "clips": 1, "estiloOk": True}:
        problemas.append("a meio de uma mudanca nos clips: %s" % r["L"])
    if r["I"]["atual"] != "v2" or r["I"]["creditos"] is not None or not r["I"]["marcas"]:
        problemas.append("o anular do painel: %s" % r["I"])
    verifica("Mesa: dois aparelhos juntam-se, o anular nao troca a versao", not problemas,
             "; ".join(problemas)[:400] if problemas else
             "partes diferentes juntam, a mesma parte e conflito, a Mesa antiga nao apaga, o anular fica na versao")


def teste_dois_aparelhos_gravam_a_mesma_revisao():
    """Dois aparelhos que gravam no mesmo instante a mesma revisao nao perdem nada calados.

    O DEFEITO QUE ISTO APANHA (revisor de 2 de outubro): os dois leem a revisao N, os dois gravam a N+1, e a base fica
    com a ultima. A pagina que gravou primeiro dizia «guardado» e a mudanca dela ja nao estava na base; a vigia so olha
    para revisoes maiores e nao dava por isso, e com o `quando` dela mais tarde a gravacao seguinte apagava a do outro.
    Agora a base na revisao que a pagina gravou, com outro `quando` (escritaPorBaixo), poe a pagina outra vez na base
    em que se apoiava (voltarAoApoioDeAntes), e a juntarComBase() junta as duas, ou abre o conflito na mesma parte.
    """
    if not shutil.which("node"):
        salta("Mesa: dois aparelhos na mesma revisao", "sem node neste PC")
        return
    problemas = []
    html = io.open(EDITOR, encoding="utf-8").read()
    blocos = "\n".join([_declaracao(html, m, problemas) for m in DECLARACOES_JUNTAR + ["var antesDaEscrita = ", "var porBaixoPorDizer = "]] +
                       [_bloco(html, m, problemas) for m in FUNCOES_JUNTAR + ["function escritaPorBaixo(", "function voltarAoApoioDeAntes(",
                                                                            "function cadeiaNova(", "function novaGravacao("]])
    if problemas:
        verifica("Mesa: dois aparelhos na mesma revisao", False, "; ".join(problemas)[:300])
        return
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}],
          "pessoas": [], "tags": {}, "atual": "v1", "quando": "2026-10-02T10:00:00.000Z", "rev": 5, "pagina": "2026-10-02"}
    js = """
var r = {}, B0 = %s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
/* o que o gravar() faz a volta de um set() bem sucedido: a base em que se apoia, a cadeia que leva, e depois a base
   passa a ser o escrito */
function gravou(){
  var apoio = {lida: baseLida, rev: baseRev, quando: baseRemota, cadeia: cadeiaLida, gravacao: baseGravacao}, dados = corpo();
  dados.cadeia = cadeiaNova(); dados.gravacao = novaGravacao();
  antesDaEscrita = {lida: apoio.lida, rev: apoio.rev, quando: apoio.quando, cadeia: apoio.cadeia, gravacao: apoio.gravacao,
                    escrita: {quando: dados.quando, rev: dados.rev, id: dados.gravacao}};
  baseRemota = dados.quando; baseRev = dados.rev; baseLida = fotografia(dados); cadeiaLida = dados.cadeia; baseGravacao = dados.gravacao;
  return dados;
}
// A. aqui a data afastada, la a letra da legenda, os dois na revisao 6: junta-se, e grava-se a 7 com as duas
abrir(B0); est.estilo = {contador: {data_afastada: true}};
var meu = gravou();
var outro = com({estilo: {legenda: {tamanho: 48}}, rev: 6, quando: "2026-10-02T10:00:00.500Z"});
r.A = {meuRev: meu.rev, porBaixo: escritaPorBaixo(outro)};
voltarAoApoioDeAntes();
r.A.revDepois = baseRev; r.A.antes = antesDaEscrita; r.A.porDizer = porBaixoPorDizer;
var j = juntarComBase(outro), c = corpo();
r.A.ok = j && j.ok; r.A.deles = j && j.deles; r.A.estilo = c.estilo; r.A.corpoRev = c.rev;
// B. a base e a que esta pagina gravou: nada; avancou de proposito (rev 7): nao e isto, e a vigia de sempre
abrir(B0); est.estilo = {contador: {data_afastada: true}};
meu = gravou();
r.B = {propria: escritaPorBaixo(copia(meu)), avancou: escritaPorBaixo(com({rev: 7, quando: "2026-10-02T10:05:00.000Z"})),
       semGravar: (function(){ var a = antesDaEscrita; antesDaEscrita = null; var x = escritaPorBaixo(outro); antesDaEscrita = a; return x; })()};
// C. a pagina ja recebeu outra base depois de gravar (a vigia juntou a 7): a gravacao antiga ja nao conta
abrir(B0); est.estilo = {contador: {data_afastada: true}};
gravou();
registarBase(com({rev: 7, quando: "2026-10-02T10:06:00.000Z", estilo: {contador: {data_afastada: true}}}), false);
r.C = escritaPorBaixo(com({rev: 7, quando: "2026-10-02T10:07:00.000Z"}));
// D. a mesma parte nos dois (a letra da legenda): conflito, e a pagina fica com o seu
abrir(B0); est.estilo = {legenda: {tamanho: 52}};
gravou();
var outro2 = com({estilo: {legenda: {tamanho: 48}}, rev: 6, quando: "2026-10-02T09:59:59.000Z"});
r.D = {porBaixo: escritaPorBaixo(outro2)};
voltarAoApoioDeAntes();
j = juntarComBase(outro2);
r.D.ok = j && j.ok; r.D.choque = j && j.choque; r.D.estilo = est.estilo;
// E. o outro aparelho ja gravou outra vez (a 7, apoiada na 6 dele) antes de esta pagina dar por isso: a cadeia da 7 tem a
//    6 com o quando dele, e a pagina volta a 5 e junta as tres coisas
abrir(com({cadeia: [[4, "2026-10-02T09:59:00.000Z"]]}));
r.E = {cadeia5: cadeiaLida.length};
est.estilo = {contador: {data_afastada: true}};
meu = gravou();
r.E.cadeiaMinha = meu.cadeia;
var q6 = "2026-10-02T10:00:00.700Z";
var outro7 = com({estilo: {legenda: {tamanho: 48}}, creditos: {titulo: "LA"}, rev: 7, quando: "2026-10-02T10:00:05.000Z",
                  cadeia: [[4, "2026-10-02T09:59:00.000Z"], [5, B0.quando], [6, q6]]});
r.E.porBaixo = escritaPorBaixo(outro7);
voltarAoApoioDeAntes();
j = juntarComBase(outro7); c = corpo();
r.E.ok = j && j.ok; r.E.estilo = c.estilo; r.E.creditos = c.creditos; r.E.rev = baseRev; r.E.cadeiaDepois = cadeiaNova();
// F. a 7 apoiada na 6 desta pagina: nada; uma cadeia que nao acaba na 6 (copiada por um script) ou sem cadeia: nada
abrir(B0); est.estilo = {contador: {data_afastada: true}};
meu = gravou();
r.F = {
  minha: escritaPorBaixo(com({rev: 7, quando: "2026-10-02T10:00:05.000Z", cadeia: meu.cadeia.concat([[6, meu.quando, meu.gravacao]])})),
  velha: escritaPorBaixo(com({rev: 7, quando: "2026-10-02T10:00:05.000Z", cadeia: [[5, B0.quando]]})),
  semCadeia: escritaPorBaixo(com({rev: 7, quando: "2026-10-02T10:00:05.000Z"})),
  longe: escritaPorBaixo(com({rev: 9, quando: "2026-10-02T10:00:09.000Z", cadeia: [[8, "x"]]})),
  /* uma cadeia copiada de outro documento (acaba na 6 e a base e a 8): mesmo com a 6 de outro, nao prova nada */
  copiada: escritaPorBaixo(com({rev: 8, quando: "2026-10-02T10:00:08.000Z", cadeia: [[5, B0.quando], [6, "outro", "x"]]}))
};
// G. no mesmo milesimo: o mesmo quando e outra marca e outra gravacao; a propria, lida de volta, nao
abrir(B0); est.estilo = {contador: {data_afastada: true}};
meu = gravou();
r.G = {outra: escritaPorBaixo(com({rev: 6, quando: meu.quando, gravacao: "outra"})), propria: escritaPorBaixo(copia(meu)),
       semMarca: escritaPorBaixo(com({rev: 6, quando: meu.quando})),
       marcas: meu.gravacao.length >= 10 && meu.gravacao !== novaGravacao(),
       cadeiaComMarca: (function(){ var d = gravou(); return d.cadeia[d.cadeia.length - 1]; })()};
console.log(JSON.stringify(r));
""" % json.dumps(B0)
    programa = '"use strict";\n' + PRELUDE_JUNTAR + "\n" + blocos + "\n" + js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        p = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if p.returncode != 0:
        verifica("Mesa: dois aparelhos na mesma revisao", False, "o node parou: " + " | ".join((p.stderr or p.stdout).strip().splitlines()[:5])[:300])
        return
    r = json.loads(p.stdout)
    A = r["A"]
    if not (A["meuRev"] == 6 and A["porBaixo"] and A["revDepois"] == 5 and A["antes"] is None and A["porDizer"] and A["ok"]
            and A["deles"] == ["estilo"] and A["estilo"] == {"contador": {"data_afastada": True}, "legenda": {"tamanho": 48}}
            and A["corpoRev"] == 7):
        problemas.append("aqui e la em partes diferentes: %s" % A)
    if r["B"] != {"propria": False, "avancou": False, "semGravar": False}:
        problemas.append("so quando a gravacao desta pagina ficou por baixo: %s" % r["B"])
    if r["C"]:
        problemas.append("uma gravacao ja ultrapassada pela vigia ainda contava")
    D = r["D"]
    if not D["porBaixo"] or D["ok"] or D["choque"] != ["estilo"] or D["estilo"] != {"legenda": {"tamanho": 52}}:
        problemas.append("a mesma parte nos dois: %s" % D)
    E = r["E"]
    if not (E["cadeia5"] == 1 and E["cadeiaMinha"] == [[4, "2026-10-02T09:59:00.000Z"], [5, B0["quando"], ""]] and E["porBaixo"]
            and E["ok"] and E["estilo"] == {"contador": {"data_afastada": True}, "legenda": {"tamanho": 48}}
            and E["creditos"] == {"titulo": "LA"} and E["rev"] == 7 and E["cadeiaDepois"][-1][0] == 7):
        problemas.append("o outro ja gravou outra vez por cima: %s" % E)
    if r["F"] != {"minha": False, "velha": False, "semCadeia": False, "longe": False, "copiada": False}:
        problemas.append("so com a cadeia a prova-lo: %s" % r["F"])
    G = r["G"]
    if not (G["outra"] and not G["propria"] and G["semMarca"] and G["marcas"] and len(G["cadeiaComMarca"]) == 3
            and G["cadeiaComMarca"][0] == 6):
        problemas.append("no mesmo milesimo, pela marca: %s" % G)
    verifica("Mesa: dois aparelhos na mesma revisao", not problemas, "; ".join(problemas)[:400] if problemas else
             "a gravacao por baixo volta a base de antes e junta; na mesma parte e conflito; so quando e mesmo isso")


# ------------------------------------------------------------------------------------ o estilo
def _declaracao(html, inicio, problemas):
    """`var NOME = ...;` do script da Mesa ate ao ponto e virgula de fora de todos os parenteses.

    O _bloco() procura a primeira chaveta, e uma lista sem chavetas (o ESTILO_LEITURA) levava-o ate
    ao fim da funcao seguinte. O marcador tem de aparecer uma so vez, pela regra de sempre.
    """
    if html.count(inicio) != 1:
        problemas.append("o marcador %r aparece %d vezes no editor_base.html" % (inicio, html.count(inicio)))
        return ""
    i, prof, aspas = html.index(inicio), 0, None
    p = i + len(inicio)
    while p < len(html):
        ch = html[p]
        if aspas:
            if ch == "\\":
                p += 1
            elif ch == aspas:
                aspas = None
        elif ch in "\"'":
            aspas = ch
        elif ch in "([{":
            prof += 1
        elif ch in ")]}":
            prof -= 1
        elif ch == ";" and prof == 0:
            return html[i:p + 1]
        p += 1
    problemas.append("a declaracao %r nao acaba" % inicio)
    return ""


DECLARACOES_ESTILO = ["var ESTILO_OMISSAO = ", "var ESTILO_CORPOS = ", "var ESTILO_ALFA_HOJE = ",
                      "var ESTILO_ARIAL_MINIMO = ", "var ESTILO_FUNDO_CONTADOR = ", "var ESTILO_LEITURA = ",
                      "var ESTILO_PALETAS = ", "var ESTILO_INTRO_CORES = ", "var ESTILO_INTRO_FAMILIA = ",
                      "var ESTILO_HASTES_FINAS = ", "var ESTILO_NOME_DA_PARTE = ", "var ESTILO_PARTE_PLURAL = ",
                      "var ESTILO_ROTULOS = ",
                      "var ESTILO_ARIAL = ", "var ESTILO_DATA_AFASTA = ",
                      # a letra do letreiro da intro (2 de outubro, a noite)
                      "var FONTES_INTRO = ", "var ESTILO_IMPACT = ", "var ESTILO_INTRO_CUSTO = ",
                      # a posicao das legendas e a letra do contador (3 de outubro)
                      "var LEG_POS = ", "var ESTILO_TEXTOS_DO_CONTADOR = "]
FUNCOES_ESTILO = ["function estiloFontes(", "function estiloFonte(", "function estiloForaDoPc(", "function estiloLetra(",
                  "function estiloCss(", "function estiloHastesFinas(", "function estiloNotasDaLetra(",
                  "function estiloLetraExiste(", "function estiloMedidor(", "function estiloHex(", "function estiloRgb(",
                  "function estiloLimpo(", "function estiloIgualHoje(", "function estiloValor(", "function estiloMudado(",
                  "function estiloParteMudada(", "function estiloPoe(", "function estiloGuardaDesfazer(",
                  "function estiloContraste(", "function estiloNum(", "function estiloAvisos(",
                  "function estiloIntroQueFalta(", "function estiloIntroDoFilme(", "function estiloIntroFeita(",
                  "function estiloPaletaAtiva(", "function estiloVerbo(", "function estiloNomeMaiusculo(",
                  "function estiloRotulo(", "function estiloTextoDoValor(", "function estiloPartesDaAba(",
                  "function estiloAbaDe(", "function estiloMudancas(", "function estiloAvisoContinuo(",
                  "function estiloCampoLetra(", "function estiloValorDoCampo(", "function estiloReporParte(",
                  "function estiloVoltarAoMeu(", "function estiloEsqueceMeu(", "function estiloPoeContinuo(",
                  # a data do nascimento afastada (2 de outubro, a tarde)
                  "function estiloEscolhaDoContador(", "function estiloAvisoDataAfastada(", "function estiloPoeDataAfastada(",
                  # a letra do letreiro da intro (2 de outubro, a noite)
                  "function estiloLetrasDaIntro(", "function estiloLetraDaIntro(", "function estiloNomeDaLetraDaIntro(",
                  "function estiloCorpoDaLetraDaIntro(", "function estiloLetraIntroAtual(", "function estiloAvisosDaLetraIntro(",
                  "function estiloPct(", "function estiloIntroOQueMudou(", "function estiloCustoDaLetraIntro(",
                  "function estiloIntroFeitaComCopia(", "function estiloPoeLetraIntro(", "function estiloMomentoDaIntro(",
                  # a posicao das legendas e a letra do contador (3 de outubro): o estiloLimpo, o estiloPoe, o
                  # estiloTextoDoValor e o estiloAvisos passam por elas
                  "function estiloCorDoContador(", "function legInteiro(", "function legPosicaoLimpa(",
                  "function legPosicaoCompacta(", "function legPosicaoTexto(", "function estiloAvisosDaPosicao(",
                  "function estiloAvisosDaLetraDoContador(",
                  "function copiaFunda(", "function corpo(", "function aplicar("]
# as funcoes da Mesa que partem os textos dos creditos como o render, e o que elas chamam fora das regras puras
FUNCOES_COM_EMOJIS = ["function credLargura(", "function credLetreiro(", "function credTextoMeio("]
FUNCOES_EMOJIS_DOS_CREDITOS = ["function credCorpoDoEmoji(", "function credAvancoDoEmoji(", "function credUnidades(",
                               "function credLarguraDoEmoji(", "function letraDoTexto("]
PRELUDE_ESTILO = """
var window = {FONTES: %(fontes)s, FONTES_INTRO: %(fontes_intro)s};
var FONTES_MESA = window.FONTES;
var est = %(est)s;
var baseRev = 7, pilhaDesfazer = [], estiloCampoAberto = null, estiloMedidorCtx = null, estiloExisteCache = {}, naPagina = 0;
var PAGINA_GERACAO = "ensaio", RENDER_LE = {}, AUDIO_INFO = null, estiloMomento = "letras";
var estiloMeu = {}, estiloContadorVista = "cores", gravacoes = 0, mensagens = [];
function versaoAtual(){ return est.versoes && est.versoes[0] || null; }
function estiloVersao(){ return versaoAtual(); }
function estiloNaPagina(){ naPagina++; }
function estiloAberto(){ return false; }
function estiloPinta(){}
function estiloGravar(){ gravacoes++; }
function estiloDepois(){ naPagina++; gravacoes++; }
function estiloMsg(t){ mensagens.push(t); }
function esc(s){ return String(s); }
var document = {querySelectorAll: function(){ return []; }};
"""


_FONTES_INTRO = {}


def _fontes_intro_de_ensaio():
    """O window.FONTES_INTRO que o gerar_mesa.py poe na pagina, sem as mascaras (os testes do estilo nao desenham),
    lido uma vez; um teste pode por outro em _FONTES_INTRO["ensaio"] (uma medida falsa, por exemplo)."""
    import gerar_mesa
    if "ensaio" in _FONTES_INTRO:
        return _FONTES_INTRO["ensaio"]
    if "lido" not in _FONTES_INTRO:
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            _FONTES_INTRO["lido"] = gerar_mesa.fontes_intro_para_mesa(mascaras=False)
    return _FONTES_INTRO["lido"]


def _correr_estilo(est, corpo_js, problemas, mais=(), declaracoes=()):
    """Corre as funcoes do estilo da Mesa no node, com as letras que o gerar_mesa.py lhe da. `mais` sao
    outras funcoes da pagina a levar (as do palco que usam o estilo), e `declaracoes` outras `var` dela.

    AS FUNCOES QUE MEDEM OU DESENHAM OS TEXTOS DOS CREDITOS (2 de outubro, a noite) partem-nos como o render
    (pedacosDoTexto, das regras puras do Validar) e medem os emojis pelo LETRAS_RENDER: quando vao em `mais`, o
    programa leva tambem as regras puras, a letraDoTexto e o LETRAS_RENDER deste PC."""
    import gerar_mesa
    html = io.open(EDITOR, encoding="utf-8").read()
    mais = [m for m in mais if m not in FUNCOES_ESTILO]
    regras = ""
    if any(m in FUNCOES_COM_EMOJIS for m in mais):
        import caracteres_para_mesa
        mais += [m for m in FUNCOES_EMOJIS_DOS_CREDITOS if m not in mais]
        regras = ("var TT_OMISSAO = 46, TT_MIN = 28, TT_MAX = 90, MUS = [];\nvar LETRAS_RENDER = %s;\n"
                  % json.dumps(caracteres_para_mesa.letras_do_render())) + _regras_do_validador(html, problemas)
    blocos = "\n".join([_declaracao(html, m, problemas) for m in list(DECLARACOES_ESTILO) + list(declaracoes)] +
                       [_bloco(html, m, problemas) for m in list(FUNCOES_ESTILO) + list(mais)])
    if problemas:
        return None
    prelude = PRELUDE_ESTILO % {"fontes": json.dumps(gerar_mesa.fontes_para_mesa(), ensure_ascii=False),
                                "fontes_intro": json.dumps(_fontes_intro_de_ensaio(), ensure_ascii=False),
                                "est": json.dumps(est, ensure_ascii=False)}
    programa = '"use strict";\n' + prelude + "\n" + regras + "\n" + blocos + "\n" + corpo_js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        r = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if r.returncode != 0:
        problemas.append("o node parou: " + _erro_do_node(r))
        return None
    return json.loads(r.stdout)


def teste_estilo_da_mesa_igual_ao_render():
    """As omissoes e os limites do painel Estilo sao os do render, lidos do codigo dele.

    O DEFEITO QUE ISTO APANHA: o "como esta" da Mesa e a omissao. Se fosse outro numero que o do
    render (um 46 contra um 48, um "#FFFFFF" contra um branco de 254), a Mesa aberta e fechada sem
    mexer gravava um estilo "igual a hoje" que o montar via diferente, e o filme saia com o que
    ninguem escolheu. E um limite mais largo do que o do render deixava escolher um tamanho que ele
    deita fora com aviso, so no render.
    """
    if not shutil.which("node"):
        salta("Mesa: o estilo tem as omissoes do render", "sem node neste PC")
        return
    import render
    problemas = []
    s = _correr_estilo({}, "console.log(JSON.stringify({o: ESTILO_OMISSAO, c: ESTILO_CORPOS, a: ESTILO_ALFA_HOJE, "
                           "f: ESTILO_FUNDO_CONTADOR, m: ESTILO_ARIAL_MINIMO, l: ESTILO_LEITURA, d: ESTILO_DATA_AFASTA, "
                           "e: Object.keys(ESTILO_OMISSAO.contador).filter(estiloEscolhaDoContador)}));", problemas)
    if s:
        mesa = json.loads(json.dumps(s["o"]))
        # o "uma so peca" (contrato 1b) e a data afastada (2 de outubro, a tarde) sao escolhas, e nao cores: o
        # render.estilo_omissao() so tem as cores, e as escolhas sao as do render.ESCOLHAS_DO_CONTADOR
        for escolha in render.ESCOLHAS_DO_CONTADOR:
            v = mesa["contador"].pop(escolha, "falta")
            if v is not False:
                problemas.append("o contador.%s de omissao e %r, devia ser false (como esta)" % (escolha, v))
        # A POSICAO DAS LEGENDAS E A LETRA DO CONTADOR (3 de outubro) tambem ficam fora do render.estilo_omissao(): a
        # posicao e {0, 0, centro}, a legenda de hoje, e a letra do contador e a de hoje, o Arial Bold do render
        posicao = mesa["legenda"].pop("posicao", "falta")
        if posicao != {"dx": 0, "dy": 0, "alinhamento": render.POSICAO_ALINHAMENTOS[0]}:
            problemas.append("a posicao das legendas de omissao e %r, devia ser dx 0, dy 0, centro" % (posicao,))
        if "fonte" not in render.estilo_omissao()["contador"]:
            letra = mesa["contador"].pop("fonte", "falta")
            if letra != render.LETRA_OMISSAO:
                problemas.append("a letra do contador de omissao e %r, devia ser %r" % (letra, render.LETRA_OMISSAO))
        if sorted(s["e"]) != sorted(render.ESCOLHAS_DO_CONTADOR):
            problemas.append("as escolhas do contador da Mesa %s nao sao as do render %s" % (s["e"], list(render.ESCOLHAS_DO_CONTADOR)))
        import linha_tempo
        if s["d"] != linha_tempo.NASC_DATA_AFASTA:
            problemas.append("a data afastada desce %s na Mesa e %s no linha_tempo" % (s["d"], linha_tempo.NASC_DATA_AFASTA))
        if mesa != render.estilo_omissao():
            problemas.append("as omissoes da Mesa nao sao as do render: %s" % {
                p: {k: v for k, v in mesa[p].items() if render.estilo_omissao()[p].get(k) != v} for p in mesa})
        corpos = {"%s.%s" % k: list(v) for k, v in render.ESTILO_CORPOS.items()}
        if s["c"] != corpos:
            problemas.append("os limites da Mesa %s nao sao os do render %s" % (s["c"], corpos))
        if s["a"] != render.LEGENDA_ALFA:
            problemas.append("o alfa de hoje da Mesa e %s e o render tem %s" % (s["a"], render.LEGENDA_ALFA))
        import linha_tempo
        if tuple(s["f"]) != tuple(linha_tempo.FUNDO):
            problemas.append("o fundo do contador da Mesa e %s e o linha_tempo tem %s" % (s["f"], linha_tempo.FUNDO))
        try:
            import montar_da_mesa
            leitura = [list(x) for x in montar_da_mesa.LEITURA_DE_HOJE]
            if [x[:4] for x in s["l"]] != [x[:4] for x in leitura]:
                problemas.append("a tabela da leitura da Mesa nao e a do montar: %s" % s["l"])
            if s["m"] != montar_da_mesa.CORPO_MINIMO_ARIAL:
                problemas.append("o corpo minimo do Arial da Mesa e %s e o montar tem %s" % (s["m"], montar_da_mesa.CORPO_MINIMO_ARIAL))
        except (ImportError, AttributeError) as erro:
            problemas.append("o montar_da_mesa nao tem a tabela da leitura (%s)" % erro)
    verifica("Mesa: o estilo tem as omissoes e os limites do render", not problemas,
             "; ".join(problemas)[:300] if problemas else "5 partes, %d limites, a leitura do montar" % len(s["c"]))


def teste_estilo_grava_so_o_que_difere():
    """O est.estilo so guarda o que difere de hoje, ja limpo, passa pelo anular e vai no corpo().

    O DEFEITO QUE ISTO APANHA: um valor voltado a omissao que ficasse guardado (o render via-o como
    escolhido, e o filme deixava de seguir o de hoje), uma cor em minusculas ou um corpo em texto que
    o render reescrevesse com aviso, um corpo fora dos limites aceite pela Mesa, e um corpo() que nao
    levasse o estilo e o gravasse tudo menos ele, sem aviso nenhum.
    """
    if not shutil.which("node"):
        salta("Mesa: o estilo grava so o que difere", "sem node neste PC")
        return
    import render
    problemas = []
    base = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}], "atual": "v1",
            "pessoas": [], "tags": {}}
    js = """
var r = {}, copia = function(){ return est.estilo === undefined ? null : JSON.parse(JSON.stringify(est.estilo)); };
estiloPoe("legenda", "tamanho", 56); r.tam = copia();
estiloPoe("legenda", "tamanho", 46); r.tamHoje = copia();
/* o fundo compara-se no alfa que vai ao ecra, como no render: 0,65 e o alfa 166, e fica guardado; os
   0,646 a 0,649 sao o 165 de hoje; e a barra nos 65 % da os 0,647, para voltar a ela ser voltar a hoje */
estiloPoe("legenda", "fundo", 0.65); r.fundo65 = copia();
estiloPoe("legenda", "fundo", 0.646); r.fundo646 = copia();
var barra = function(v){ return {type: "range", value: String(v), getAttribute: function(a){ return {"data-ep": "legenda", "data-ec": "fundo"}[a]; }}; };
r.barra = [estiloValorDoCampo(barra(65)), estiloValorDoCampo(barra(64)), estiloValorDoCampo(barra(66))];
estiloPoe("legenda", "fundo", 0.8); estiloPoe("legenda", "cor", "#f3deb8"); r.corFundo = copia();
estiloPoe("legenda", "cor", "#fff"); r.corHoje = copia();
r.recusas = [estiloPoe("cartao", "curto", 500), estiloPoe("intro", "tamanho", 100), estiloPoe("legenda", "fonte", "nao_existe"),
             estiloPoe("legenda", "tamanho", "56.5"), estiloPoe("intro", "fonte", "arial_bold"), estiloPoe("contador", "linha", "verde")];
r.depoisDasRecusas = copia();
estiloPoe("contador", "continuo", true); r.continuo = copia().contador;
estiloPoe("contador", "continuo", false);
estiloGuardaDesfazer("ensaio");
estiloPoe("intro", "tamanho", 132); estiloPoe("intro", "fundo", "#132036"); estiloPoe("cartao", "fonte", "cinzel_bold");
estiloPoe("nome", "tamanho", 150); estiloPoe("contador", "marco", "#c9a45c"); estiloPoe("cartao", "brilho", "000");
r.rico = copia();
r.mudadas = ["legenda", "cartao", "contador", "intro"].filter(estiloParteMudada);
r.corpoCom = corpo().estilo ? Object.keys(corpo().estilo).sort() : null;
pilhaDesfazer[pilhaDesfazer.length - 1].aoAnular();
r.anulado = copia();
r.naPagina = naPagina;
delete est.estilo;
r.corpoSem = Object.prototype.hasOwnProperty.call(corpo(), "estilo");
aplicar({versoes: [{id: "v1", clips: []}], atual: "v1", estilo: {legenda: {tamanho: "300", cor: "azul", fonte: "bebas_neue"}}});
r.lidoMal = {tam: estiloValor("legenda", "tamanho"), cor: estiloValor("legenda", "cor"), fonte: estiloValor("legenda", "fonte")};
aplicar({versoes: [{id: "v1", clips: []}], atual: "v1"});
r.lidoSem = est.estilo === undefined;
r.paleta = estiloPaletaAtiva("intro", 0);
console.log(JSON.stringify(r));
"""
    s = _correr_estilo(base, js, problemas)
    if s:
        esperado = {
            "tam": {"legenda": {"tamanho": 56}}, "tamHoje": None, "fundo65": {"legenda": {"fundo": 0.65}},
            "fundo646": None, "barra": [0.647, 0.64, 0.66],
            "corFundo": {"legenda": {"fundo": 0.8, "cor": "#F3DEB8"}}, "corHoje": {"legenda": {"fundo": 0.8}},
            "recusas": [False] * 6, "depoisDasRecusas": {"legenda": {"fundo": 0.8}},
            "continuo": {"continuo": True}, "anulado": {"legenda": {"fundo": 0.8}},
            "mudadas": ["legenda", "cartao", "contador", "intro"],
            "corpoCom": ["cartao", "contador", "intro", "legenda", "nome"], "corpoSem": False,
            "lidoMal": {"tam": 46, "cor": "#FFFFFF", "fonte": "bebas_neue"}, "lidoSem": True, "paleta": True}
        for k, v in esperado.items():
            if s.get(k) != v:
                problemas.append("%s deu %s, devia ser %s" % (k, json.dumps(s.get(k), ensure_ascii=False), json.dumps(v, ensure_ascii=False)))
        if not s["naPagina"]:
            problemas.append("o anular nao pos o estilo de volta na pagina (estiloNaPagina)")
        # o que a Mesa grava ja vem como o render o quer: a limpeza dele nao muda nada nem avisa
        # e o render ve o fundo da mesma maneira: 0,65 e outro alfa, 0,646 e o de hoje
        if render.normalizar_estilo({"legenda": {"fundo": 0.65}}) != {"legenda": {"fundo": 0.65}} \
                or render.normalizar_estilo({"legenda": {"fundo": 0.646}}) != {}:
            problemas.append("o render compara o fundo de outra maneira: 0,65 da %s, 0,646 da %s" % (
                render.normalizar_estilo({"legenda": {"fundo": 0.65}}), render.normalizar_estilo({"legenda": {"fundo": 0.646}})))
        rico = s["rico"]
        avisos = []
        if render.normalizar_estilo(rico, avisos) != rico or avisos:
            problemas.append("o render limpa o estilo da Mesa de outra maneira: %s %s" % (render.normalizar_estilo(rico), avisos))
    verifica("Mesa: o estilo grava so o que difere, ja limpo", not problemas,
             "; ".join(problemas)[:400] if problemas else
             "omissoes fora, 6 recusas, anular, corpo, aplicar, e o render le-o sem mudar nada")


def teste_estilo_avisa_como_o_montar():
    """A Mesa avisa a leitura a 15 m e o contraste nos mesmos casos em que o montar avisa.

    O DEFEITO QUE ISTO APANHA: a Mesa calada num estilo que o montar depois diz que nao se le (ele so
    sabia no render, meia hora depois), ou a Mesa a avisar o que o montar deixa passar. Compara-se
    so se ha aviso de cada coisa, e nao o texto, que e de cada um.
    """
    if not shutil.which("node"):
        salta("Mesa: o estilo avisa como o montar", "sem node neste PC")
        return
    try:
        import montar_da_mesa
        montar_da_mesa.avisos_do_estilo
    except (ImportError, AttributeError) as erro:
        salta("Mesa: o estilo avisa como o montar", "o montar nao tem avisos_do_estilo (%s)" % erro)
        return
    import linha_tempo
    import render
    casos = [
        {},
        {"legenda": {"fonte": "bebas_neue"}},
        {"legenda": {"fonte": "bebas_neue", "tamanho": 78}},
        {"legenda": {"fonte": "calibri_bold", "tamanho": 50}},
        {"legenda": {"fonte": "montserrat_bold", "tamanho": 44}},
        {"legenda": {"tamanho": 40}},
        {"legenda": {"cor": "#7A7A7A", "fundo": 0.2}},
        {"legenda": {"fundo": 0.3}},
        {"legenda": {"fundo": 0.45}},            # 3,4 para 1: entre os 3 dos tracos e os 4,5 do texto
        {"cartao": {"fonte": "cormorant_bold"}},
        {"cartao": {"fonte": "cormorant_bold", "frase": 96, "curto": 124}, "nome": {"tamanho": 100}},
        {"cartao": {"quente": "#303030"}},
        {"contador": {"ponteiro": "#202020", "regua_texto": "#606060", "marco": "#C9A45C", "ano": "#FFD9A0"}},
        {"contador": {"nascimento": "#707070", "marco_texto": "#FFF1D6"}},     # 3 a 4 para 1, perto da regra
        # O QUE A MESA NAO VIA ATE 2 DE OUTUBRO, A TARDE (o montar ja via): a linha, os tracos grandes da regua e os
        # anos ao lado, que hoje ja ficam abaixo da regra de proposito (a linha a 2,6 e os anos ao lado a 3,3: so
        # se avisa se ficarem ainda mais apagados); a legenda escura numa foto escura; o letreiro a acabar escuro;
        # as letras da intro sobre o fundo; e o letreiro da intro mais pequeno, que leva a «A HISTÓRIA DE»
        {"contador": {"linha": "#141018", "regua": "#2A2228", "ano_longe": "#3A3238"}},
        {"contador": {"linha": "#7A6A76", "ano_longe": "#8A7E86", "regua": "#B0A0AA"}},
        {"contador": {"linha": "#5B4D57"}},                                     # a cor de hoje, um digito ao lado
        {"legenda": {"cor": "#202020"}},
        {"legenda": {"cor": "#3A3A3A", "fundo": 0.9}},
        {"legenda": {"cor": "#FFF6E5", "fundo": 0.1}},
        {"cartao": {"claro": "#303030"}},
        {"intro": {"letra": "#7A1A20"}},
        {"intro": {"tamanho": 200}},
        {"intro": {"tamanho": 300, "fundo": "#1A2C4E", "letra": "#D9B46A"}},
        {"legenda": {"fonte": "georgia_bold", "tamanho": 40}, "cartao": {"fonte": "cormorant_bold", "quente": "#C9A04E"}},
        # a letra do letreiro (2 de outubro, a noite): as oferecidas leem-se no minimo da Mesa, e nenhum avisa
        # (com uma medida que faz avisar: teste_letra_da_intro_igual_ao_render)
        {"intro": {"fonte": "bernard", "tamanho": 132}},
        {"intro": {"fonte": "rockcond", "tamanho": 132, "fundo": "#0C0B09", "letra": "#D4AA5A"}},
    ]
    js = """
var casos = %s, r = [];
casos.forEach(function(c){
  est.estilo = c;
  var t = [];
  ["legenda", "cartao", "contador", "intro"].forEach(function(p){ estiloAvisos(p).forEach(function(a){ t.push(a.t); }); });
  r.push(t);
});
console.log(JSON.stringify(r));
""" % json.dumps(casos)
    problemas = []
    s = _correr_estilo({}, js, problemas)

    def tipos_mesa(textos):
        t = set()
        for x in textos:
            for quem, chave in (("A legenda", "legenda"), ("A frase dos cartões", "frase"), ("O cartão curto", "curto"),
                                ("O nome do bebé", "nome")):
                if x.startswith(quem + " pode não se ler"):
                    t.add("leitura:" + chave)
            if x.startswith("Contraste fraco: a legenda"):
                t.add("contraste:legenda:" + ("clara" if "numa foto clara" in x else "escura" if "numa foto escura" in x else "?"))
            if x.startswith("Contraste fraco: o letreiro começa"):
                t.add("contraste:quente")
            if x.startswith("Contraste fraco: o letreiro acaba"):
                t.add("contraste:claro")
            for chave, quem in (("regua_texto", "os meses da régua"), ("marco_texto", "o texto dos marcos"), ("ano", "o ano aceso"),
                                ("ano_longe", "os anos ao lado"), ("nascimento", "os nascimentos"), ("ponteiro", "o ponteiro"),
                                ("marco", "o risco dos marcos"), ("linha", "a linha "), ("regua", "os traços grandes da régua")):
                if x.startswith("Contraste fraco: " + quem):
                    t.add("contraste:" + chave)
            if x.startswith("Contraste fraco: no fim, as letras do letreiro"):
                t.add("contraste:intro")
            if x.startswith("Com o letreiro a ") and "«A HISTÓRIA DE»" in x:
                t.add("intro:tamanho")
            if x.startswith("O letreiro em ") and "separa as letras a 15 metros" in x:
                t.add("intro:letra")
            if "ainda não foi medida" in x:
                t.add("leitura:por_medir")
            if "ainda não está no PC do render" in x:
                t.add("letra:fora_do_pc")
        return t

    def tipos_montar(textos):
        t = set()
        for x in textos:
            for quem, chave in (("a legenda em", "legenda"), ("a frase dos cartoes", "frase"), ("o cartao curto", "curto"),
                                ("o nome do bebe", "nome")):
                if x.startswith("estilo: " + quem) and "le-se a 15 metros como" in x:
                    t.add("leitura:" + chave)
            if x.startswith("estilo: a legenda ") and "numa foto clara" in x:
                t.add("contraste:legenda:clara")
            if x.startswith("estilo: a legenda ") and "numa foto escura" in x:
                t.add("contraste:legenda:escura")
            if x.startswith("estilo: o letreiro dos cartoes comeca"):
                t.add("contraste:quente")
            if x.startswith("estilo: o letreiro dos cartoes acaba"):
                t.add("contraste:claro")
            for chave, quem in (("regua_texto", "os nomes da regua"), ("marco_texto", "o texto dos marcos"), ("ano", "o ano aceso"),
                                ("ano_longe", "os anos ao lado"), ("nascimento", "os nascimentos"), ("ponteiro", "o ponteiro"),
                                ("marco", "o risco dos marcos"), ("linha", "a linha"), ("regua", "os tracos grandes da regua")):
                if x.startswith("estilo: no contador, " + quem + " "):
                    t.add("contraste:" + chave)
            if x.startswith("estilo: na intro, as letras"):
                t.add("contraste:intro")
            if x.startswith("estilo: com o letreiro da intro a"):
                t.add("intro:tamanho")
            if x.startswith("estilo: o letreiro da intro em"):
                t.add("intro:letra")
            if x.startswith("estilo: ") and "ainda nao tem o corpo minimo medido" in x:
                t.add("leitura:por_medir")
            if x.startswith("estilo: a letra ") and "nao esta em disco" in x:
                t.add("letra:fora_do_pc")
        return t

    contados = 0
    if s:
        for caso, textos in zip(casos, s):
            limpo = render.normalizar_estilo(caso)
            do_montar = montar_da_mesa.avisos_do_estilo(limpo, render, linha_tempo)
            a, b = tipos_mesa(textos), tipos_montar(do_montar)
            contados += len(b)
            if a != b:
                problemas.append("%s: a Mesa avisa %s e o montar %s" % (json.dumps(caso), sorted(a), sorted(b)))
            # um aviso novo do montar que este teste nao conhece passava calado: cada linha dele tem um tipo aqui
            for linha in do_montar:
                if not tipos_montar([linha]):
                    problemas.append("o montar avisa uma coisa que a Mesa nao compara: %r" % linha[:80])
    verifica("Mesa: o estilo avisa nos mesmos casos que o montar", not problemas and contados > 0,
             "; ".join(problemas)[:400] if problemas else "%d estilos, %d avisos iguais nos dois" % (len(casos), contados))


def teste_estilo_como_esta_em_cada_parte():
    """«Como está (original)» tira do est.estilo tudo o que a parte tinha, e o teu de há pouco volta.

    O Tiago, a 2 de outubro às 02:23: "we should always be able to keep it as is, e.g. the contador".
    O DEFEITO QUE ISTO APANHA: um «como está» que deixasse alguma coisa da parte (o nome do bebe na
    dos cartoes, o continuo no contador, o tamanho na intro), e o filme saia com o que ninguem via na
    Mesa; um voltar ao teu que gravasse uma coisa diferente da que la estava; um anular que nao
    repusesse; e o contador numa so peca sem dizer que ainda nao chega ao filme quando o render nao a
    le, ou a dizer que e uma escolha sem gravar o continuo.
    """
    if not shutil.which("node"):
        salta("Mesa: «como está» em cada parte", "sem node neste PC")
        return
    import render
    problemas = []
    base = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}], "atual": "v1",
            "pessoas": [], "tags": {}}
    js = """
var r = {}, copia = function(){ return est.estilo === undefined ? null : JSON.parse(JSON.stringify(est.estilo)); };
var rico = {legenda: {fonte: "montserrat_bold", tamanho: 56}, cartao: {quente: "#C9A04E"}, nome: {tamanho: 150},
            contador: {continuo: true, marco: "#5B8BD9"}, intro: {fundo: "#6B1E33", tamanho: 300}};
est.estilo = JSON.parse(JSON.stringify(rico));
r.mudancasCartao = estiloMudancas("cartao");
estiloReporParte("cartao"); r.semCartao = copia(); r.meu = JSON.parse(JSON.stringify(estiloMeu.cartao || null));
estiloVoltarAoMeu("cartao"); r.voltou = copia();
pilhaDesfazer[pilhaDesfazer.length - 1].aoAnular(); r.anulado = copia();
["legenda", "cartao", "contador", "intro"].forEach(estiloReporParte);
r.tudo = copia(); r.partes = ["legenda", "cartao", "contador", "intro"].filter(estiloParteMudada);
r.repetido = (estiloReporParte("legenda"), mensagens[mensagens.length - 1]);
/* o contador: como esta e a omissao; uma so peca grava o continuo, e diz que ainda nao chega ao filme */
RENDER_LE = {continuo: false};
r.contadorOmissao = [estiloValor("contador", "continuo"), estiloAvisoContinuo().forte || false];
estiloPoeContinuo(true); r.uma = copia(); r.vista = estiloContadorVista;
r.avisoUma = estiloAvisoContinuo(); r.avisosUma = estiloAvisos("contador").map(function(a){ return [!!a.forte, a.t]; });
r.valorUma = estiloTextoDoValor("contador", "continuo", true);
estiloPoeContinuo(false); r.semUma = copia();
RENDER_LE = {continuo: true}; estiloPoeContinuo(true);
r.avisoLido = estiloAvisoContinuo().t; r.avisosLido = estiloAvisos("contador").map(function(a){ return !!a.forte; });
console.log(JSON.stringify(r));
"""
    s = _correr_estilo(base, js, problemas)
    if s:
        if s["mudancasCartao"] != ["a cor quente", "o nome do bebé"]:
            problemas.append("as mudancas dos cartoes deram %s" % s["mudancasCartao"])
        sem = {k: v for k, v in s["semCartao"].items()} if s["semCartao"] else {}
        if "cartao" in sem or "nome" in sem or set(sem) != {"legenda", "contador", "intro"}:
            problemas.append("«como está» nos cartoes deixou %s" % sorted(sem))
        if s["meu"] != {"cartao": {"quente": "#C9A04E"}, "nome": {"tamanho": 150}}:
            problemas.append("o teu de ha pouco guardou %s" % s["meu"])
        rico = {"legenda": {"fonte": "montserrat_bold", "tamanho": 56}, "cartao": {"quente": "#C9A04E"},
                "nome": {"tamanho": 150}, "contador": {"continuo": True, "marco": "#5B8BD9"},
                "intro": {"fundo": "#6B1E33", "tamanho": 300}}
        if s["voltou"] != rico:
            problemas.append("voltar ao teu deu %s" % s["voltou"])
        if s["anulado"] != s["semCartao"]:
            problemas.append("o anular do voltar ao teu deu %s" % s["anulado"])
        if s["tudo"] is not None or s["partes"]:
            problemas.append("«como está» nas quatro partes deixou %s %s" % (s["tudo"], s["partes"]))
        if "já" not in (s["repetido"] or ""):
            problemas.append("«como está» numa parte ja como esta disse %r" % s["repetido"])
        if s["contadorOmissao"] != [False, False]:
            problemas.append("o contador de omissao: %s" % s["contadorOmissao"])
        if s["uma"] != {"contador": {"continuo": True}} or s["vista"] != "passagem":
            problemas.append("uma so peca gravou %s e a amostra ficou em %s" % (s["uma"], s["vista"]))
        if not (s["avisoUma"].get("forte") and "ainda não chega ao filme" in s["avisoUma"]["t"]):
            problemas.append("uma so peca sem o render a ler nao avisa: %s" % s["avisoUma"])
        if not any(f and "ainda não chega ao filme" in t for f, t in s["avisosUma"]):
            problemas.append("os avisos do contador nao dizem que nao chega ao filme: %s" % s["avisosUma"])
        if s["semUma"] is not None:
            problemas.append("voltar a como esta deixou %s" % s["semUma"])
        if s["avisoLido"] or any(s["avisosLido"]):
            problemas.append("com o render a ler, a Mesa continua a avisar: %r %s" % (s["avisoLido"], s["avisosLido"]))
        if s["valorUma"] != "uma só peça":
            problemas.append("o valor do continuo le-se %r" % s["valorUma"])
        # o «como está» e o filme de hoje para o render tambem: nada fica
        if render.normalizar_estilo(s["tudo"] or {}) != {}:
            problemas.append("o render ve estilo no «como está»: %s" % render.normalizar_estilo(s["tudo"] or {}))
    verifica("Mesa: «como está (original)» em cada parte", not problemas,
             "; ".join(problemas)[:400] if problemas else
             "4 partes, cartoes com o nome, o teu de ha pouco, anular, contador numa so peca como escolha")


def teste_estilo_letras_do_convite():
    """As letras do convite vem primeiro, as manuscritas e as de hastes finas dizem-no, e a Mesa avisa.

    O DEFEITO QUE ISTO APANHA: a lista a esconder as letras do convite no fim; uma manuscrita escolhida
    para a legenda sem aviso forte (a 15 m nao se le); o Cormorant ou o Playfair numa legenda sem o
    aviso das hastes finas, que o corpo_minimo (medido pelo espaco entre letras, 084) nao apanha; e
    uma letra que nao esteja no PC do render sem o dizer.
    """
    if not shutil.which("node"):
        salta("Mesa: as letras do convite", "sem node neste PC")
        return
    import gerar_mesa
    problemas = []
    js = """
var r = {};
var lista = function(parte){
  var h = estiloCampoLetra(parte, "Letra"), saida = [], re = /<optgroup label="([^"]*)">|<option value="([^"]*)"[^>]*>([^<]*)<\\/option>/g, m;
  while((m = re.exec(h))) saida.push(m[1] ? "[" + m[1] + "]" : m[2] + "|" + m[3]);
  return saida;
};
r.legenda = lista("legenda");
var aviso = function(parte, fonte){
  est.estilo = {}; est.estilo[parte] = {fonte: fonte};
  return estiloAvisos(parte).map(function(a){ return [!!a.forte, a.t]; });
};
r.vibesLegenda = aviso("legenda", "great_vibes");
r.vibesCartao = aviso("cartao", "great_vibes");
r.playfairLegenda = aviso("legenda", "playfair_display");
r.cormorantCartao = aviso("cartao", "cormorant_regular");
r.montserratLegenda = aviso("legenda", "montserrat_bold");
r.finas = estiloFontes().filter(estiloHastesFinas).map(function(f){ return f.id; });
FONTES_MESA.fontes.forEach(function(f){ if(f.id === "pinyon_script") f.em_disco = false; });
r.fora = lista("legenda").filter(function(x){ return x.indexOf("pinyon_script|") === 0; })[0];
r.foraAviso = aviso("cartao", "pinyon_script");
console.log(JSON.stringify(r));
"""
    s = _correr_estilo({}, js, problemas)
    if s:
        dados = json.load(io.open(gerar_mesa.FONTES, encoding="utf-8"))
        convite = [e["id"] for e in dados["fontes"] if e.get("do_convite")]
        outras = [e["id"] for e in dados["fontes"] if not e.get("do_convite") and e["id"] != dados["omissao"]]
        esperado = ([dados["omissao"]] + ["[Como no convite]"] + convite + ["[Outras letras de leitura]"] + outras)
        obtido = [x if x.startswith("[") else x.split("|")[0] for x in s["legenda"]]
        if obtido != esperado:
            problemas.append("a lista das letras e %s" % obtido)
        if "como está (original)" not in s["legenda"][0]:
            problemas.append("a primeira letra nao diz que e a original: %r" % s["legenda"][0])
        for e in dados["fontes"]:
            texto = [x for x in s["legenda"] if x.startswith(e["id"] + "|")][0]
            if e.get("manuscrita") and "só títulos curtos" not in texto:
                problemas.append("a manuscrita %s nao diz so titulos curtos: %r" % (e["id"], texto))
        if sorted(s["finas"]) != sorted(["cormorant_bold", "cormorant_regular", "cormorant_italico", "playfair_display",
                                         "great_vibes", "pinyon_script"]):
            problemas.append("as letras de hastes finas sao %s" % s["finas"])
        if not any(f and "manuscrita" in t and "títulos curtos" in t for f, t in s["vibesLegenda"]):
            problemas.append("a manuscrita na legenda nao avisa forte: %s" % s["vibesLegenda"])
        if not any("manuscrita" in t for _f, t in s["vibesCartao"]):
            problemas.append("a manuscrita nos cartoes nao diz que so serve para titulos curtos")
        if not any(f and "hastes finas" in t for f, t in s["playfairLegenda"]):
            problemas.append("o Playfair na legenda nao avisa das hastes finas: %s" % s["playfairLegenda"])
        if not any((not f) and "hastes finas" in t and "títulos" in t for f, t in s["cormorantCartao"]):
            problemas.append("o Cormorant nos cartoes nao diz usar grande, so em titulos: %s" % s["cormorantCartao"])
        if any("hastes finas" in t or "manuscrita" in t for _f, t in s["montserratLegenda"]):
            problemas.append("o Montserrat leva aviso de hastes finas")
        if "ainda não está no PC do render" not in (s["fora"] or ""):
            problemas.append("a letra fora do PC nao o diz na lista: %r" % s["fora"])
        if not any(f and "ainda não está no PC do render" in t for f, t in s["foraAviso"]):
            problemas.append("a letra fora do PC nao avisa: %s" % s["foraAviso"])
    verifica("Mesa: as letras do convite primeiro, e o que cada uma aguenta", not problemas,
             "; ".join(problemas)[:400] if problemas else
             "convite primeiro, manuscritas so titulos curtos, hastes finas avisadas, fora do PC dito")


# as quatro intros que a equipa do render fez a 2 de outubro, e a de hoje: (nome, fundo, letra, papel, tinta)
INTROS_DE_2_DE_OUTUBRO = [("Como está (original)", "#96161C", "#FCFAFA", "#F7E9D2", "#2E0E10"),
                          ("Vinho e champanhe", "#6B1E33", "#E2B88C", "#F4E4C8", "#1E070F"),
                          ("Azul noite e dourado", "#1A2C4E", "#D9B46A", "#F1E1BC", "#060C18"),
                          ("Verde garrafa e creme", "#1E4733", "#F3E8CF", "#F4EBD5", "#07140D"),
                          ("Preto e dourado", "#0C0B09", "#D4AA5A", "#EEDCAE", "#4A3B24")]


def teste_estilo_intros_ja_feitas():
    """As propostas da aba Intro sao as intros ja feitas, ao hex, e a Mesa diz o que custa outra.

    O DEFEITO QUE ISTO APANHA: uma proposta com um hex diferente do da intro feita (era assim ate 2 de
    outubro: as propostas da Mesa eram outras cores), e escolher uma "ja feita" custava os 3 minutos de
    fazer outra na montagem; a Mesa a dizer "ja feita" de uma que o montar nao aceita; ou calada
    quando uma cor a mao vai custar 3 minutos, ou quando a versao nem abre com a intro 5.
    """
    if not shutil.which("node"):
        salta("Mesa: as intros ja feitas", "sem node neste PC")
        return
    import gerar_mesa
    import intro_flipbook
    import render
    problemas = []
    feitas = gerar_mesa.intros_feitas()
    js = """
var r = {};
r.paletas = ESTILO_PALETAS.intro.map(function(p){ return [p.nome, p.v.fundo, p.v.letra, p.v.papel, p.v.tinta, p.v.tamanho]; });
RENDER_LE = {intros_feitas: %s};
var versao = function(f){ est.versoes = [{id: "v1", nome: "demo", clips: [{t: "video", f: "20th Century Fox Intro HD igualado.mp4"}, {t: "video", f: f}, {t: "contador", x: ""}]}]; };
versao("intro_clara_tiago_5 sem preto igualado.mp4");
r.semPreto = estiloIntroDoFilme().sem_preto;
r.feitas = ESTILO_PALETAS.intro.slice(1).map(function(p){ return !!estiloIntroFeita(true, p.v); });
est.estilo = {intro: {fundo: "#6B1E33", letra: "#E2B88C", papel: "#F4E4C8", tinta: "#1E070F"}};
r.avisoFeita = estiloAvisos("intro").map(function(a){ return [!!a.forte, a.t]; });
est.estilo.intro.fundo = "#6B1E34";
r.avisoMao = estiloAvisos("intro").map(function(a){ return [!!a.forte, a.t]; });
est.estilo = {intro: {fundo: "#6B1E33", letra: "#E2B88C", papel: "#F4E4C8", tinta: "#1E070F", tamanho: 300}};
r.avisoTamanho = estiloAvisos("intro").map(function(a){ return a.t; });
est.estilo = {intro: {fundo: "#6B1E33", letra: "#E2B88C", papel: "#F4E4C8", tinta: "#1E070F"}};
versao("intro_clara_tiago_5 igualado.mp4");
r.outraVariante = [estiloIntroDoFilme().sem_preto, estiloAvisos("intro").map(function(a){ return a.t; })];
versao("20th Century Fox Intro HD igualado.mp4");
r.semIntro5 = estiloAvisos("intro").map(function(a){ return [!!a.forte, a.t]; });
RENDER_LE = {};
versao("intro_clara_tiago_5 sem preto igualado.mp4");
r.semLista = ESTILO_PALETAS.intro.slice(1).map(function(p){ return !!estiloIntroFeita(true, p.v); });
console.log(JSON.stringify(r));
""" % json.dumps(feitas)
    s = _correr_estilo({"versoes": []}, js, problemas)
    if s:
        esperado = [list(x) + [288] for x in INTROS_DE_2_DE_OUTUBRO]
        if s["paletas"] != esperado:
            problemas.append("as propostas da intro sao %s" % s["paletas"])
        # e cada uma tem ficheiro igualado, com o nome e o comentario que o montar_da_mesa procura
        for nome, fundo, letra, papel, tinta in INTROS_DE_2_DE_OUTUBRO[1:]:
            cores = {k: render.cor_rgb(v) for k, v in (("fundo", fundo), ("letra", letra), ("papel", papel), ("tinta", tinta))}
            ficheiro = intro_flipbook.nome_da_intro(cores, 288, True).replace(".mp4", " igualado.mp4")
            if not os.path.exists(os.path.join(render.PASTA_SOM_IGUALADO, ficheiro)):
                problemas.append("a proposta %s nao tem a intro feita (%s)" % (nome, ficheiro))
        if feitas is None:
            problemas.append("o gerar_mesa nao conseguiu ler as intros feitas")
        if s["semPreto"] is not True or s["feitas"] != [True] * 4 or s["semLista"] != [True] * 4:
            problemas.append("as propostas nao contam como feitas: %s %s %s" % (s["semPreto"], s["feitas"], s["semLista"]))
        if not any("já está feita" in t and "Vinho" in t for _f, t in s["avisoFeita"]) or \
                any("3 minutos" in t for _f, t in s["avisoFeita"]):
            problemas.append("a proposta ja feita: %s" % s["avisoFeita"])
        if not any("3 minutos" in t and "cores" in t for _f, t in s["avisoMao"]):
            problemas.append("a cor a mao nao diz os 3 minutos: %s" % s["avisoMao"])
        if not any("3 minutos" in t and "tamanho" in t for t in s["avisoTamanho"]):
            problemas.append("o tamanho a mao nao diz os 3 minutos: %s" % s["avisoTamanho"])
        if s["outraVariante"][0] is not False or not any("3 minutos" in t for t in s["outraVariante"][1]):
            problemas.append("a intro 5 com o preto e as cores so feitas sem ele: %s" % s["outraVariante"])
        if not any(f and "não abre com a intro 5" in t for f, t in s["semIntro5"]):
            problemas.append("uma versao sem a intro 5 nao avisa: %s" % s["semIntro5"])
    verifica("Mesa: as propostas da intro sao as ja feitas", not problemas,
             "; ".join(problemas)[:400] if problemas else
             "4 propostas ao hex, com ficheiro e paleta, 3 minutos so a mao, e a intro 5 conferida")


def teste_letras_da_mesa_e_o_google_fonts():
    """O gerar_mesa.py da a Mesa todas as letras de data/fontes.json e pede cada familia uma vez.

    O DEFEITO QUE ISTO APANHA: uma letra que o render conhece e a Mesa nao oferece, ou o contrario; e
    um endereco do Google Fonts com a mesma familia duas vezes (o Cormorant e pedido tres vezes, o
    Cinzel duas), que arrisca vir recusado inteiro e deixar as amostras todas no Arial.
    """
    import gerar_mesa
    problemas = []
    casos = [(["Cinzel:wght@700", "Cinzel:wght@400"], ["family=Cinzel:wght@400;700"]),
             (["Cormorant+Garamond:wght@700", "Cormorant+Garamond:ital,wght@1,400", "Cormorant+Garamond:wght@400"],
              ["family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400"]),
             (["Bebas+Neue", None, "Playfair+Display:wght@400"], ["family=Bebas+Neue", "family=Playfair+Display"]),
             (["Montserrat:wght@700", "Montserrat:wght@700"], ["family=Montserrat:wght@700"])]
    for pedidos, certo in casos:
        if gerar_mesa.familias_google(pedidos) != certo:
            problemas.append("%s deu %s" % (pedidos, gerar_mesa.familias_google(pedidos)))
    f = gerar_mesa.fontes_para_mesa()
    dados = json.load(io.open(gerar_mesa.FONTES, encoding="utf-8"))
    ids = [e["id"] for e in dados["fontes"]]
    if not f or [x["id"] for x in f["fontes"]] != ids:
        problemas.append("as letras da Mesa nao sao as de data/fontes.json")
    else:
        familias = re.findall(r"family=([^:&]+)", f["css"])
        if len(familias) != len(set(familias)):
            problemas.append("ha familias repetidas no endereco: %s" % familias)
        pedidas = {e["web_google"].split(":")[0] for e in dados["fontes"] if e.get("web_google")}
        if pedidas - set(familias):
            problemas.append("letras do Google que nao se pedem: %s" % sorted(pedidas - set(familias)))
        if gerar_mesa.PARECIDA_COM_IMPACT not in familias:
            problemas.append("falta o Anton da amostra da intro")
        if any("ficheiro" in x for x in f["fontes"]):
            problemas.append("o caminho do ficheiro foi para a pagina")
        em_disco = {x["id"]: x["em_disco"] for x in f["fontes"]}
        errados = [e["id"] for e in dados["fontes"] if em_disco[e["id"]] != os.path.exists(e.get("ficheiro") or "")]
        if errados:
            problemas.append("o em_disco nao bate com o disco: %s" % errados)
        if f["omissao"] != "arial_bold":
            problemas.append("a letra de omissao e %r" % f["omissao"])
    # e a pagina pede o endereco sozinha, uma vez, e le o window.FONTES
    html = io.open(EDITOR, encoding="utf-8").read()
    for pedaco in ("window.FONTES", 'l.href = FONTES_MESA.css', "estiloPedeLetras(); estiloNaPagina();"):
        if pedaco not in html:
            problemas.append("o editor_base.html nao tem %r" % pedaco)
    verifica("Mesa: as letras de data/fontes.json e o Google Fonts", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d letras, %d familias pedidas uma vez cada" % (len(ids), len(re.findall(r"family=", f["css"]))))


def teste_mesa_montada_traz_as_letras():
    """A Mesa que o gerar_mesa.py monta traz o window.FONTES antes do script da pagina, uma vez."""
    import gerar_mesa
    problemas = []
    montada = _montar_mesa_a_parte("mesa_1002_letras_")
    # o mesmo <script> leva a seguir o window.RENDER_LE (corretor, 2 de outubro)
    m = re.findall(r"<script>\nwindow\.FONTES = (\{.*?\});\nwindow\.RENDER_LE = (\{[^\n]*\});\n</script>\n<script>\n\(function\(\)\{\n\"use strict\";", montada, re.S)
    if len(m) != 1:
        problemas.append("o window.FONTES aparece %d vezes antes do script da pagina" % len(m))
    else:
        f = json.loads(m[0][0].replace("<\\/", "</"))
        if len(f["fontes"]) < 2 or not f["css"].startswith(gerar_mesa.GOOGLE_FONTS):
            problemas.append("o window.FONTES montado nao traz as letras e o endereco")
        # e as intros de outras cores ja feitas (2 de outubro), que a aba Intro usa para dizer o que custa
        le = json.loads(m[0][1])
        if "intros_feitas" not in le or not (le["intros_feitas"] is None or isinstance(le["intros_feitas"], list)):
            problemas.append("o window.RENDER_LE nao traz as intros feitas: %s" % sorted(le))
        # e se o render ja afasta a data do nascimento (2 de outubro, a tarde): a Mesa diz quando nao chega ao filme
        if le.get("data_afastada") is not gerar_mesa.o_que_o_render_le().get("data_afastada"):
            problemas.append("o window.RENDER_LE.data_afastada e %r e o render diz outra coisa" % le.get("data_afastada"))
    # AS LINHAS DOS NOMES NAS OUTRAS LETRAS (credLayout): so contagens, nunca nomes a mais na pagina
    c = re.search(r"window\.CREDITOS_NOMES = (\{.*?\});\n</script>", montada, re.S)
    cred = json.loads(c.group(1).replace("<\\/", "</")) if c else None
    if cred and not cred.get("sem_nomes"):
        quebras = [q for g in cred["grupos"] for q in (g.get("quebras") or {}).values()]
        if not quebras or not all(isinstance(q, list) and all(isinstance(n, int) and n > 0 for n in q) for q in quebras):
            problemas.append("o window.CREDITOS_NOMES nao traz as quebras das outras letras, so com numeros")
        if (cred.get("medidas") or {}).get("zona_segura") != 0.90:
            problemas.append("o window.CREDITOS_NOMES nao traz a zona segura dos titulos")
    verifica("Mesa: a Mesa montada traz as letras", not problemas, "; ".join(problemas)[:200])


# ------------------------------------------------------------- o palco: o filme como o render o faz (2 de outubro)
# O Tiago, a 2 de outubro: "pre-visualizar da forma mais realista possivel o video dentro da Mesa antes de fazer
# render", e "ouvir [as musicas] no timing certo". O palco conta o filme (palcoFilme) e o som (palcoSomPlano) com
# o que o palco_para_mesa.py e o audio_para_mesa.py tiram da montagem que o render desenha. Aqui guarda-se que:
#   7. com a versao que foi montada, cada clip, o nome do bebe e o fim caem no instante da montagem, e sem a
#      montagem a regra da Mesa poe o nome do bebe nos mesmos sitios;
#   8. o som do palco e o do render: cada faixa no instante, com o "in", a duracao, o cruzamento, a subida e a
#      descida de la; anda com o clip quando ele muda de sitio; uma marca nova entra no clip marcado e corta o
#      leito anterior; nos creditos a ultima continua;
#   9. as contas da fita (as paragens, quem nasce) sao as do linha_tempo e do montar;
#  10. o som cabe nas publicacoes (64 MB cada, 15 MB por ficheiro, 256 ficheiros), o window.AUDIO e o mapa do
#      contrato, e o palco nunca escreve no estado (a Mesa avisa, nunca corrige: 083);
#  11. as medidas das copias (a sonoridade de cada troco, as entradas num inicio, o silencio que uma marca salta)
#      dao o que o render e o montar medem.
ESTADO_MONTADO = os.path.join(REPO, "data", "mesa_estado.json")
DECLARACOES_PALCO = ["var PALCO_R = ", "var PALCO_NASCE = ", "var PALCO_NOME_BEBE = ", "var SOM_R = "]
FUNCOES_PALCO = ["function palcoSuave(", "function palcoQuemNasce(", "function palcoBate(", "function palcoFilme(", "function palcoAtivos(",
                 "function palcoParagens(", "function palcoChaveFaixa(", "function palcoSomPlano(",
                 "function chaveDoClipBase(", "function chavesDaVersao(", "function srDaVersao(", "function renderPorClip(",
                 "function nomeFaixa(", "function duracaoNoRender(", "function duracaoDoClip(",
                 "function duracaoDoVideoNoFilme(", "function trocoDoVideo(", "function videoNoCorpo(",
                 "function pecaDoVideo(", "function duraDoVideo(", "function encadeadoDoClip(",
                 "function contadoresSeguidos(", "function pontoDoContador(", "function lerContador(",
                 "function eDataContador(", "function dataParaIso(", "function d2(", "function eGrupo(",
                 "function fitaLer(", "function fracaoDeData(", "function somR2(", "function somEfeito(", "function somFala(",
                 "function somPorIni(", "function somResolve(", "function somSilencioNoInicio(", "function somEntraNumInicio(",
                 "function somAtaque(", "function somSonoridade(", "function somAssinatura(", "function fmtS(",
                 # a musica dos creditos (2 de outubro, a tarde): o passo 11 do palcoSomPlano
                 "function credMusicaJuncao(", "function credMusicaEscolha(", "function credMusicaEntrada(",
                 "function credMusicaFim("]
PRELUDE_PALCO = """
var window = {PALCO: %(palco)s, SOM_RENDER: %(som)s};
var PALCO = window.PALCO, SR = window.SOM_RENDER, AUDIO = %(audio)s, AUDIO_INFO = %(info)s, VIDS = [], CRED = null;
var MUSICA_FIM = null, RENDER_LE = {}, est = {};
var CRED_FALSO = null, INTRO_FALSA = null;
function palcoCreditos(){ return CRED_FALSO; }
function palcoIntroDoEstilo(c){ return INTRO_FALSA ? INTRO_FALSA(c) : null; }
"""


def _estado_montado():
    e = json.load(io.open(ESTADO_MONTADO, encoding="utf-8"))
    return e.get("data", e)


def _correr_palco(palco, som, audio, corpo_js, problemas, info=None):
    """Corre as contas do palco da Mesa no node. palcoCreditos() e um falso que devolve CRED_FALSO, e
    palcoIntroDoEstilo() um que pergunta a INTRO_FALSA (o estilo testa-se no teste_palco_intro_do_estilo)."""
    html = io.open(EDITOR, encoding="utf-8").read()
    blocos = "\n".join([_declaracao(html, m, problemas) for m in DECLARACOES_PALCO] +
                       [_bloco(html, m, problemas) for m in FUNCOES_PALCO if m != "function palcoCreditos("])
    if problemas:
        return None
    prelude = PRELUDE_PALCO % {"palco": json.dumps(palco, ensure_ascii=False), "som": json.dumps(som, ensure_ascii=False),
                               "audio": json.dumps(audio, ensure_ascii=False), "info": json.dumps(info, ensure_ascii=False)}
    programa = '"use strict";\n' + prelude + "\n" + blocos + "\n" + corpo_js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        r = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if r.returncode != 0:
        problemas.append("o node parou: " + _erro_do_node(r))
        return None
    return json.loads(r.stdout)


def teste_palco_conta_o_filme_como_o_render():
    """O relogio do palco poe cada clip no instante em que a montagem o poe.

    O DEFEITO QUE ISTO APANHA: o palco a contar o filme de outra maneira que o render (o encadeado do
    primeiro clip do corpo, os videos de abertura, o nome do bebe que so o montar poe, a fita parada, a
    duracao esticada). Com a versao que foi montada (data/mesa_estado.json, a da montagem de data/montagens/
    v3.csv) cada clip tem de cair no instante do CSV ao centesimo, e o fim tambem. Sem a montagem
    (window.PALCO vazio), a regra da Mesa tem de por o nome do bebe nos mesmos sitios, e a unica diferenca
    que sobra e a fita parada, que so o montar sabe esticar: depois de cada fita parada o palco fica
    adiantado exatamente o tempo que ela segura. E com dois clips trocados a conta continua inteira.
    """
    if not shutil.which("node"):
        salta("Mesa: o palco conta o filme como o render", "sem node neste PC")
        return
    import palco_para_mesa
    import som_para_mesa
    problemas = []
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    if not filme or not som:
        salta("Mesa: o palco conta o filme como o render", "sem data/montagens/v3.csv")
        return
    est = _estado_montado()
    versao = [v for v in est["versoes"] if v["id"] == filme["versao"]][0]
    corpo_js = """
var v = %(v)s, F = palcoFilme(v);
var saida = {exato: F.segs.map(function(s){ return {i: s.i, t: s.t, ini: s.ini, dur: s.dur, x: s.t === "nome" ? s.c.x : null}; }),
             fim: F.fim, total: F.total, exatos: F.exatos, pela: F.pela.length, cred: F.cred};
window.PALCO = {}; PALCO = window.PALCO;
var G = palcoFilme(v);
saida.regra = G.segs.map(function(s){ return {i: s.i, t: s.t, ini: s.ini, dur: s.dur, x: s.t === "nome" ? s.c.x : null}; });
saida.regraFim = G.fim;
var guardaSR = SR; SR = null;
var G2 = palcoFilme(v);
saida.semSom = G2.segs.map(function(s){ return {i: s.i, t: s.t, ini: s.ini, dur: s.dur, x: s.t === "nome" ? s.c.x : null}; });
saida.semSomFim = G2.fim;
SR = guardaSR;
PALCO = %(palco)s;
var w = JSON.parse(JSON.stringify(v)), a = w.clips[40]; w.clips[40] = w.clips[41]; w.clips[41] = a;
var H = palcoFilme(w);
saida.trocado = {exatos: H.exatos, pela: H.pela.length, fim: H.fim, soma: 0};
CRED_FALSO = {dur: 100};
var C = palcoFilme(v);
saida.comCreditos = {ini: C.cred && C.cred.ini, total: C.total, fim: C.fim};
console.log(JSON.stringify(saida));
""" % {"v": json.dumps(versao, ensure_ascii=False), "palco": json.dumps({"filme": filme}, ensure_ascii=False)}
    r = _correr_palco({"filme": filme}, som, None, corpo_js, problemas)
    if r:
        linhas = filme["linhas"]
        segs = r["exato"]
        if r["exatos"] != len([l for l in linhas if l["t"] != "nome"]) or r["pela"]:
            problemas.append("com a versao montada, %d clips bateram e %d nao" % (r["exatos"], r["pela"]))
        if len(segs) != len(linhas):
            problemas.append("o palco tem %d clips e a montagem %d" % (len(segs), len(linhas)))
        else:
            for s, l in zip(segs, linhas):
                if s["t"] != l["t"] or abs(s["ini"] - l["filme"]) > 0.006 or abs(s["dur"] - l["d"]) > 0.006:
                    problemas.append("clip %s (%s) aos %.2f s com %.2f s, e na montagem aos %.2f s com %.2f s"
                                     % (s["i"] + 1, s["t"], s["ini"], s["dur"], l["filme"], l["d"]))
                    break
                if l["t"] == "nome" and s["x"] != l["x"]:
                    problemas.append("o nome %r saiu %r" % (l["x"], s["x"]))
        if abs(r["fim"] - filme["fim"]) > 0.006:
            problemas.append("o filme acaba aos %.2f s e a montagem aos %.2f s" % (r["fim"], filme["fim"]))
        if r["cred"] is not None or abs(r["total"] - r["fim"]) > 1e-6:
            problemas.append("sem creditos o total tem de ser o fim")
        # sem a montagem: o nome nos mesmos sitios pela regra do montar. Com o window.SOM_RENDER as duracoes
        # sao as do render (a fita parada incluida) e tudo bate; sem ele, a diferenca e so a fita parada
        nomes_m = [(k, l["x"]) for k, l in enumerate(linhas) if l["t"] == "nome"]
        seguras = sum(l.get("segura") or 0.0 for l in linhas)
        for nome_caso, lista, fim_caso, com_segura in (("sem a montagem", r["regra"], r["regraFim"], False),
                                                        ("sem a montagem nem o som", r["semSom"], r["semSomFim"], True)):
            nomes_r = [(k, s["x"]) for k, s in enumerate(lista) if s["t"] == "nome"]
            if nomes_m != nomes_r:
                problemas.append("%s, os nomes ficam em %s e na montagem em %s" % (nome_caso, nomes_r, nomes_m))
                continue
            atraso = 0.0
            for s, l in zip(lista, linhas):
                if abs(s["ini"] + atraso - l["filme"]) > 0.006:
                    problemas.append("%s, o clip %s (%s) fica aos %.2f s, e devia ficar aos %.2f s"
                                     % (nome_caso, s["i"] + 1, s["t"], s["ini"], l["filme"] - atraso))
                    break
                if com_segura:
                    atraso += l.get("segura") or 0.0
            if abs(fim_caso + (seguras if com_segura else 0.0) - filme["fim"]) > 0.006:
                problemas.append("%s o fim e %.2f s, e a montagem acaba aos %.2f s" % (nome_caso, fim_caso, filme["fim"]))
        if r["trocado"]["pela"] != 0 or abs(r["trocado"]["fim"] - filme["fim"]) > 0.006:
            problemas.append("com dois clips trocados de sitio: %s" % r["trocado"])
        cc = r["comCreditos"]
        if not cc["ini"] or abs(cc["ini"] - (filme["fim"] - 2.5)) > 0.006 or abs(cc["total"] - (cc["ini"] + 100)) > 1e-6:
            problemas.append("os creditos comecam aos %s, e deviam comecar 2,5 s antes do fim, no fade" % cc)
    verifica("Mesa: o palco conta o filme como o render", not problemas, "; ".join(problemas)[:300] if problemas else
             "%d clips ao centesimo, 2 nomes de bebe, as fitas paradas e o fim" % len(filme["linhas"]))


def teste_palco_segue_a_mesa_depois_da_montagem():
    """Um clip que mudou de duracao ou de encadeado depois da montagem conta-se com o que tem agora.

    O DEFEITO QUE ISTO APANHA (revisor de 2 de outubro): a chave de um clip (o tipo e as fotos, o texto ou o
    ficheiro) nao leva a duracao nem o encadeado, e o palco usava os da montagem sempre que a chave batia. No
    estado dele uma foto de 4 s passada a 41 s ficava com 4 s, duas pilhas esticadas ficavam com os tempos de
    antes, e a musica do resto do filme entrava ate 41 s antes do render. Aqui, sobre a versao que se montou:
    uma foto passa de 4 a 41 s, uma pilha encolhe 3 s (encolher nao pode ficar com a duracao maior do
    SOM_RENDER) e um encadeado passa a 2 s. Cada um conta-se com o que tem agora, diz que mudou, e tudo o que
    vem a seguir anda o mesmo, as musicas presas aos clips incluidas. Sem o que a Mesa tinha quando se montou
    (md, mc), a regra apanha as mesmas tres mudancas e a versao montada continua a bater toda.
    """
    if not shutil.which("node"):
        salta("Mesa: o palco segue a Mesa depois da montagem", "sem node neste PC")
        return
    import palco_para_mesa
    import som_para_mesa
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    if not filme or not som:
        salta("Mesa: o palco segue a Mesa depois da montagem", "sem data/montagens/v3.csv")
        return
    problemas = []
    if not filme.get("com_a_mesa") or not any("md" in l for l in filme["linhas"]):
        problemas.append("o palco_para_mesa nao trouxe o que a Mesa tinha quando se montou (md, mc)")
    sem_md = json.loads(json.dumps(filme))
    for l in sem_md["linhas"]:
        for k in ("md", "mc", "mv"):
            l.pop(k, None)
    est = _estado_montado()
    versao = [v for v in est["versoes"] if v["id"] == filme["versao"]][0]
    corpo_js = """
var v = %(v)s, F = palcoFilme(v), chaves = chavesDaVersao(v);
var foto = -1, pilha = -1, cross = -1;
F.segs.forEach(function(s){
  if(s.i < 0 || s.abertura || !s.r) return;
  var k = s.i;
  if(foto < 0 && k > 20 && s.t === "foto" && Math.abs(s.dur - 4) < 0.01) foto = k;
  else if(foto >= 0 && pilha < 0 && k > foto + 3 && s.t === "pilha" && s.dur > 6) pilha = k;
  else if(pilha >= 0 && cross < 0 && k > pilha + 3 && s.t === "foto" && Math.abs(s.entra - 0.7) < 0.01) cross = k;
});
var w = JSON.parse(JSON.stringify(v));
w.clips[foto].d = 41; w.clips[pilha].d = +(F.porI[pilha].dur - 3).toFixed(2); w.clips[cross].c = 2;
var resumo = function(G){ var o = {}; G.segs.forEach(function(s){ if(s.i >= 0) o[s.i] = {ini: s.ini, dur: s.dur, entra: s.entra, mudou: !!s.mudou}; });
  return {segs: o, mudaram: G.mudaram, pela: G.pela.slice(), fim: G.fim}; };
var plano = function(G){ var p = palcoSomPlano(G); return {notas: p.notas, l: p.plano.map(function(x){ return {f: x.f, ini: x.ini, k: chaves.indexOf(x.clip), tipo: x.tipo}; })}; };
var G = palcoFilme(w);
var saida = {foto: foto, pilha: pilha, cross: cross, F: resumo(F), G: resumo(G), pF: plano(F), pG: plano(G)};
/* e um cartao encurtado 1 s: so o que a Mesa tinha o apanha (pela regra, um cartao mais curto do que a montagem
   pode ser um que o montar esticou) */
var cartao = -1;
F.segs.forEach(function(s){ if(cartao < 0 && s.i > 20 && s.t === "cartao" && s.r && s.dur >= 3) cartao = s.i; });
if(cartao >= 0){
  var w2 = JSON.parse(JSON.stringify(v)); w2.clips[cartao].d = +(F.porI[cartao].dur - 1).toFixed(2);
  var G2 = palcoFilme(w2);
  saida.cartao = {k: cartao, antes: F.porI[cartao].dur, depois: G2.porI[cartao].dur, mudou: !!G2.porI[cartao].mudou, fimD: G2.fim - F.fim};
}
PALCO = %(sem)s;
saida.H = resumo(palcoFilme(w)); saida.Fsem = resumo(palcoFilme(v));
console.log(JSON.stringify(saida));
""" % {"v": json.dumps(versao, ensure_ascii=False), "sem": json.dumps({"filme": sem_md}, ensure_ascii=False)}
    audio, info = _som_da_mesa()
    r = _correr_palco({"filme": filme}, som, audio, corpo_js, problemas, info)
    detalhe = ""
    if r:
        foto, pilha, cross = r["foto"], r["pilha"], r["cross"]
        if min(foto, pilha, cross) < 0:
            problemas.append("nao encontrei a foto, a pilha e o encadeado para mudar: %s" % [foto, pilha, cross])
        else:
            F, G, H = r["F"], r["G"], r["H"]
            if F["mudaram"] or F["pela"]:
                problemas.append("com a versao montada %d clips dizem que mudaram" % len(F["pela"]))
            if r["Fsem"]["pela"]:
                problemas.append("sem o md, a regra diz que mudaram os clips %s da versao montada"
                                 % [i + 1 for i in r["Fsem"]["pela"][:6]])
            dp = F["segs"][str(pilha)]["dur"] - 3
            ef = F["segs"][str(cross)]["entra"]

            def anda(i):
                return 0.0 if i <= foto else 37.0 if i <= pilha else 34.0 if i < cross else 34.0 - (2 - ef)
            for nome_caso, X in (("com o que a Mesa tinha", G), ("pela regra", H)):
                s = X["segs"]
                if abs(s[str(foto)]["dur"] - 41) > 0.006 or not s[str(foto)]["mudou"]:
                    problemas.append("%s, a foto passada a 41 s ficou com %s" % (nome_caso, s[str(foto)]))
                if abs(s[str(pilha)]["dur"] - dp) > 0.006 or not s[str(pilha)]["mudou"]:
                    problemas.append("%s, a pilha encolhida para %.2f s ficou com %s" % (nome_caso, dp, s[str(pilha)]))
                if abs(s[str(cross)]["entra"] - 2) > 0.006 or not s[str(cross)]["mudou"]:
                    problemas.append("%s, o encadeado passado a 2 s ficou %s" % (nome_caso, s[str(cross)]))
                if sorted(X["mudaram"]) != [foto, pilha, cross]:
                    problemas.append("%s, mudaram %s" % (nome_caso, [i + 1 for i in X["mudaram"]]))
                # tudo o que vem a seguir anda o mesmo
                for i_txt, a in F["segs"].items():
                    if abs(s[i_txt]["ini"] - a["ini"] - anda(int(i_txt))) > 0.006:
                        problemas.append("%s, o clip %d andou %.2f s e devia andar %.2f s"
                                         % (nome_caso, int(i_txt) + 1, s[i_txt]["ini"] - a["ini"], anda(int(i_txt))))
                        break
                if abs(X["fim"] - F["fim"] - (34.0 - (2 - ef))) > 0.006:
                    problemas.append("%s, o fim andou %.2f s" % (nome_caso, X["fim"] - F["fim"]))
            ca = r.get("cartao")
            if not ca or abs(ca["depois"] - (ca["antes"] - 1)) > 0.006 or not ca["mudou"] or abs(ca["fimD"] + 1) > 0.006:
                problemas.append("um cartao encurtado 1 s depois da montagem: %s" % ca)
            # as musicas presas aos clips andam com eles
            antes = {(x["f"], x["k"]): x["ini"] for x in r["pF"]["l"] if x["k"] >= 0}
            andaram = 0
            for x in r["pG"]["l"]:
                if x["k"] < 0 or (x["f"], x["k"]) not in antes:
                    continue
                d = anda(x["k"])
                if abs(x["ini"] - antes[(x["f"], x["k"])] - d) > 0.011:
                    problemas.append("a faixa %s do clip %d andou %.2f s e devia andar %.2f s"
                                     % (x["f"][:24], x["k"] + 1, x["ini"] - antes[(x["f"], x["k"])], d))
                    break
                andaram += d > 0
            if audio and not andaram:
                problemas.append("nenhuma musica do resto do filme andou com os clips")
            detalhe = ("a foto a 41 s, a pilha encolhida e o encadeado a 2 s contam-se pela Mesa, com e sem o md, e o "
                       "cartao encurtado com o md; %d musicas andaram com os clips" % andaram)
    verifica("Mesa: o palco segue a Mesa depois da montagem", not problemas,
             "; ".join(problemas)[:400] if problemas else detalhe)


def teste_palco_intro_do_estilo():
    """Com outras cores na aba Intro do Estilo, o palco mostra e toca a intro que o montar vai por.

    O DEFEITO QUE ISTO APANHA (revisor de 2 de outubro): escolhida «Azul noite e dourado (ja feita)», o
    est.estilo.intro ficava gravado e o palco continuava a tocar a copia da intro vermelha, sem o dizer. O
    palcoIntroDoEstilo() tem de dar o ficheiro da intro feita com essas cores, na variante da versao (o
    montar_da_mesa.intro_da_paleta faz o mesmo), nada com a intro como esta ou num video que nao e a intro 5,
    e "por fazer" com uma cor a mao. E no palcoFilme a intro passa a ter a copia dela, a duracao dela e o
    som dela, e o resto do filme anda com a diferenca.
    """
    if not shutil.which("node"):
        salta("Mesa: a intro do Estilo no palco", "sem node neste PC")
        return
    import audio_para_mesa
    import palco_para_mesa
    import som_para_mesa
    problemas = []
    feitas = audio_para_mesa.intros_feitas()
    if not feitas:
        salta("Mesa: a intro do Estilo no palco", "sem as intros de outras cores neste PC")
        return
    azul = [x for x in feitas if x["fundo"] == "#1A2C4E" and x["sem_preto"]]
    js = """
var r = {};
RENDER_LE = {intros_feitas: %s};
est.versoes = [{id: "v1", nome: "demo", clips: [{t: "video", f: "20th Century Fox Intro HD igualado.mp4"}, {t: "video", f: "intro_clara_tiago_5 sem preto igualado.mp4"}, {t: "foto", i: "f1", d: 4}]}];
var c = est.versoes[0].clips;
r.comoEsta = palcoIntroDoEstilo(c[1]);
est.estilo = {intro: {fundo: "#1A2C4E", letra: "#D9B46A", papel: "#F1E1BC", tinta: "#060C18"}};
r.azul = palcoIntroDoEstilo(c[1]);
r.fox = palcoIntroDoEstilo(c[0]);
r.foto = palcoIntroDoEstilo(c[2]);
r.comPreto = palcoIntroDoEstilo({t: "video", f: "intro_clara_tiago_5 igualado.mp4"});
est.estilo.intro.fundo = "#1A2C4F";
r.mao = palcoIntroDoEstilo(c[1]);
console.log(JSON.stringify(r));
""" % json.dumps(feitas)
    s = _correr_estilo({"versoes": []}, js, problemas, mais=["function palcoIntroDoEstilo("])
    if s:
        if s["comoEsta"] is not None or s["fox"] is not None or s["foto"] is not None:
            problemas.append("sem cores na intro, ou fora da intro 5, devia dar nada: %s %s %s"
                             % (s["comoEsta"], s["fox"], s["foto"]))
        if not azul or not s["azul"] or s["azul"]["f"] != azul[0]["f"] or not s["azul"]["feita"] \
                or s["azul"]["nome"] != "Azul noite e dourado":
            problemas.append("o azul ja feito deu %s, e o ficheiro e %s" % (s["azul"], azul[0]["f"] if azul else None))
        if not s["comPreto"] or s["comPreto"]["f"] or s["comPreto"]["feita"]:
            problemas.append("a intro com o preto so tem o azul feito sem ele: %s" % s["comPreto"])
        if not s["mao"] or s["mao"]["f"] or s["mao"]["feita"]:
            problemas.append("uma cor a mao deu %s" % s["mao"])
    # no filme: a intro troca pela copia da azul, com a duracao dela, e o som e o dela
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    if azul and filme and som:
        audio = {"20th Century Fox Intro HD igualado.mp4": {"url": "audio/fox.m4a", "duracao": 20.8, "tipo": "video"},
                 "intro_clara_tiago_5 sem preto igualado.mp4": {"url": "audio/vermelha.m4a", "duracao": 13.21, "tipo": "video"},
                 azul[0]["f"]: {"url": "audio/azul.m4a", "duracao": 12.0, "tipo": "video"}}
        info = {"videos": {azul[0]["f"]: [{"url": "video/azul.mp4", "in": 0, "dura": 12.0, "de": 0}]}}
        versao = [v for v in _estado_montado()["versoes"] if v["id"] == filme["versao"]][0]
        corpo_js = """
var v = %(v)s, F = palcoFilme(v);
INTRO_FALSA = function(c){ return /^intro_clara_tiago_5 sem preto/.test(c.f || "") ? {nome: "Azul noite e dourado", f: %(f)s, feita: true} : null; };
var G = palcoFilme(v), p = palcoSomPlano(G).plano.filter(function(x){ return x.tipo === "abertura"; });
var ia = G.segs.filter(function(s){ return s.intro; })[0];
console.log(JSON.stringify({fv: ia && ia.fv, dur: ia && ia.dur, copia: ia && palcoCopiaDoVideo(ia), som: p.map(function(x){ return [x.f, x.url, x.ini, x.dura]; }),
                            antes: F.videos, depois: G.videos, fimAntes: F.fim, fimDepois: G.fim, ass: F.assinatura !== G.assinatura}));
""" % {"v": json.dumps(versao, ensure_ascii=False), "f": json.dumps(azul[0]["f"])}
        html = io.open(EDITOR, encoding="utf-8").read()
        copia_js = _bloco(html, "function palcoCopiaDoVideo(", problemas)
        r = _correr_palco({"filme": filme}, som, audio, copia_js + "\n" + corpo_js, problemas, info)
        if r:
            vermelha = [l for l in filme["linhas"] if l["t"] == "video" and "intro_clara_tiago_5" in l["chave"]]
            dv = vermelha[0]["d"] if vermelha else 0
            if r["fv"] != azul[0]["f"] or abs(r["dur"] - 12.0) > 1e-6 or not r["copia"] or r["copia"]["url"] != "video/azul.mp4":
                problemas.append("no filme a intro ficou %s, %s s, copia %s" % (r["fv"], r["dur"], r["copia"]))
            if not any(x[0] == azul[0]["f"] and x[1] == "audio/azul.m4a" and abs(x[3] - 12.0) < 1e-6 for x in r["som"]) or \
                    any(x[1] == "audio/vermelha.m4a" for x in r["som"]):
                problemas.append("o som da abertura ficou %s" % r["som"])
            if abs((r["depois"] - r["antes"]) - (12.0 - dv)) > 1e-6 or abs((r["fimDepois"] - r["fimAntes"]) - (12.0 - dv)) > 1e-6 \
                    or not r["ass"]:
                problemas.append("o resto do filme nao andou com a intro: %s" % {k: r[k] for k in ("antes", "depois", "fimAntes", "fimDepois", "ass")})
    verifica("Mesa: a intro do Estilo no palco", not problemas, "; ".join(problemas)[:400] if problemas else
             "a azul ja feita troca a intro (copia, duracao e som), e nada com a intro como esta, fora dela ou a mao")

def teste_palco_nao_diz_que_toca_a_marca_tirada():
    """Uma marca de um clip que ja nao existe nao toca, e o palco nao diz que toca.

    O DEFEITO QUE ISTO APANHA (revisor de 2 de outubro): com o estado dele, o Aproximado dizia «1 faixa comeca
    num clip que mudou desde a montagem: toca no instante em que tocava na montagem», e era a Fome de Viagem,
    marcada numa pilha que ele desfez. A faixa nao tocava (e bem: o montar tambem a tira), mas contava-se como
    solta antes de sair. Aqui tira-se da versao montada um clip cuja unica faixa e uma marca dele.
    """
    if not shutil.which("node"):
        salta("Mesa: a marca tirada nao toca nem se diz", "sem node neste PC")
        return
    import palco_para_mesa
    import som_para_mesa
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    audio, info = _som_da_mesa()
    if not filme or not som or not audio:
        salta("Mesa: a marca tirada nao toca nem se diz", "sem a montagem ou sem as copias do som")
        return
    problemas = []
    por_clip = {}
    for fx in som["faixas"]:
        por_clip.setdefault(fx["clip"], []).append(fx)
    so_marca = [k for k, l in por_clip.items() if all(fx["origem"] == "mesa" for fx in l)]
    versao = [v for v in _estado_montado()["versoes"] if v["id"] == filme["versao"]][0]
    corpo_js = """
var v = %(v)s, chaves = chavesDaVersao(v), so = %(so)s, k = -1;
for(var i = 0; i < chaves.length && k < 0; i++) if(so.indexOf(chaves[i]) >= 0) k = i;
var tirada = k >= 0 ? v.clips[k].m && v.clips[k].m.f : null;
var w = JSON.parse(JSON.stringify(v)); if(k >= 0) w.clips.splice(k, 1);
var G = palcoFilme(w), p = palcoSomPlano(G), F = palcoFilme(v), q = palcoSomPlano(F);
console.log(JSON.stringify({k: k, chave: chaves[k], notas: p.notas, notasAntes: q.notas,
                            toca: p.plano.filter(function(x){ return x.clip === chaves[k]; }).length,
                            soltas: p.plano.filter(function(x){ return x.solta; }).length}));
""" % {"v": json.dumps(versao, ensure_ascii=False), "so": json.dumps(so_marca, ensure_ascii=False)}
    r = _correr_palco({"filme": filme}, som, audio, corpo_js, problemas, info)
    if r:
        if r["k"] < 0:
            problemas.append("a montagem nao tem nenhum clip so com uma marca dele")
        else:
            if r["toca"]:
                problemas.append("a marca do clip tirado (%s) continua a tocar" % r["chave"][:40])
            fala = [n for n in r["notas"] if "começa num clip" in n or "começam em clips" in n]
            if fala and not r["soltas"]:
                problemas.append("o palco diz que toca uma faixa que nao toca: %s" % fala)
            if any("começa num clip" in n or "começam em clips" in n for n in r["notasAntes"]):
                problemas.append("com a versao montada ja diz que ha faixas soltas")
    verifica("Mesa: a marca tirada nao toca nem se diz", not problemas, "; ".join(problemas)[:300] if problemas else
             "o clip %d sai, a marca dele nao toca e o Aproximado nao fala dela" % (r["k"] + 1 if r else 0))


def teste_som_as_tiradas_nao_se_perdem():
    """As copias que deixam de servir continuam com null ate a publicacao, mesmo com a Mesa montada duas vezes.

    O DEFEITO QUE ISTO APANHA (revisor de 2 de outubro): o audio_para_mesa.preparar() apagava a copia e so a
    punha com null no publicar.json dessa corrida; na seguinte o ficheiro ja nao existia e o null perdia-se, e
    a copia velha ficava no endereco da Mesa para sempre. Corre-se numa pasta de ensaio, com duas copias que ja
    existem e uma que sobra: o null tem de estar nas duas corridas, sair com --publicado, e uma copia que volte
    a ser precisa nao pode ir com null.
    """
    import contextlib
    import audio_para_mesa as A
    import montar_da_mesa      # noqa: F401 - antes do redirect: ele mexe no sys.stdout ao ser importado
    ind = A._ler_indice()
    fontes = {}
    for caminho, g in sorted(ind.get("originais", {}).items()):
        f = os.path.basename(caminho)
        c = ind["copias"].get(A._id_da_copia(g["sha1"], None))
        if c and os.path.exists(caminho) and os.path.exists(os.path.join(A.PASTA_AUDIO, c.get("ficheiro", ""))) \
                and c["ficheiro"] == "%s_%s.m4a" % (A._slug(f), A._id_da_copia(g["sha1"], None)):
            fontes[f] = {"caminho": caminho, "tipo": "musica", "_copia": c["ficheiro"]}
        if len(fontes) == 2:
            break
    if len(fontes) < 2:
        salta("Mesa: as tiradas do som nao se perdem", "sem copias do som feitas neste PC")
        return
    problemas = []
    pasta = tempfile.mkdtemp(prefix="mesa_1002_tiradas_")
    guardado = {k: getattr(A, k) for k in ("PASTA_AUDIO", "PASTA_VIDEO", "INDICE", "PUBLICAR", "fontes_da_mesa")}
    try:
        aud = os.path.join(pasta, "audio")
        os.makedirs(aud)
        os.makedirs(os.path.join(pasta, "video"))
        for x in fontes.values():
            shutil.copy2(os.path.join(A.PASTA_AUDIO, x["_copia"]), aud)
        io.open(os.path.join(aud, "indice.json"), "w", encoding="utf-8").write(json.dumps(ind))
        io.open(os.path.join(aud, "musica_antiga_0123456789.m4a"), "wb").write(b"\0" * 16)
        A.PASTA_AUDIO, A.PASTA_VIDEO = aud, os.path.join(pasta, "video")
        A.INDICE, A.PUBLICAR = os.path.join(aud, "indice.json"), os.path.join(aud, "publicar.json")
        so = {f: {k: v for k, v in x.items() if k != "_copia"} for f, x in fontes.items()}
        A.fontes_da_mesa = lambda nome="v3": dict(so)

        def corre():
            with contextlib.redirect_stdout(io.StringIO()):
                p = A.preparar(fazer=True, com_video=False)
            pub = json.load(io.open(A.PUBLICAR, encoding="utf-8"))
            return p["info"]["tiradas"], [u for l in pub for u, v in l["files"].items() if v is None]
        velha = "audio/musica_antiga_0123456789.m4a"
        um, dois = corre(), corre()
        if os.path.exists(os.path.join(aud, "musica_antiga_0123456789.m4a")):
            problemas.append("a copia que sobra nao saiu da pasta")
        for k, (tiradas, nulls) in enumerate((um, dois)):
            if velha not in tiradas or velha not in nulls:
                problemas.append("na corrida %d a copia velha nao vai com null: %s %s" % (k + 1, tiradas, nulls))
        # uma que volta a ser precisa sai da lista: com outro nome no indice, a mesma sobra volta a aparecer
        ind2 = json.load(io.open(A.INDICE, encoding="utf-8"))
        ind2["por_tirar"] = ind2.get("por_tirar", []) + ["audio/" + list(fontes.values())[0]["_copia"]]
        io.open(A.INDICE, "w", encoding="utf-8").write(json.dumps(ind2))
        tres = corre()
        if "audio/" + list(fontes.values())[0]["_copia"] in tres[1]:
            problemas.append("uma copia em uso foi com null")
        with contextlib.redirect_stdout(io.StringIO()):
            A.publicado()
        quatro = corre()
        if quatro[0] or quatro[1]:
            problemas.append("depois de --publicado ainda ha null: %s" % (quatro,))
    finally:
        for k, v in guardado.items():
            setattr(A, k, v)
        shutil.rmtree(pasta, ignore_errors=True)
    verifica("Mesa: as tiradas do som nao se perdem", not problemas, "; ".join(problemas)[:300] if problemas else
             "o null fica nas duas corridas, nao vai para uma em uso e sai com --publicado")

def _som_da_mesa():
    """(audio, info) que o gerar_mesa poe na pagina, so lidos (sem fazer copias); (None, None) sem som."""
    import audio_para_mesa
    import contextlib
    import montar_da_mesa      # noqa: F401 - antes do redirect: ele mexe no sys.stdout ao ser importado
    with contextlib.redirect_stdout(io.StringIO()):
        p = audio_para_mesa.preparar(fazer=False, com_video=False)
    return (p["audio"], p["info"]) if p and p.get("audio") else (None, None)


def _entradas_do_render(nome="v3"):
    """(videos, fim do corpo, entradas do render.som_do_ficheiro) da montagem, como o render as toca."""
    import csv
    import render
    with open(os.path.join(REPO, "data", "montagens", nome + ".csv"), encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    fanfarra, corpo = render.partir_em_fanfarra_e_corpo(linhas)
    desvio = float(corpo[0]["inicio_s"])
    fim = max(float(c["fim_s"]) for c in corpo) - desvio
    videos = sum(float(c["duracao_s"]) for c in fanfarra)
    return videos, fim, sorted(render.som_do_ficheiro(nome, fim) or [], key=lambda e: e["quando"])


def teste_palco_toca_o_som_no_instante_da_montagem():
    """O som do palco e o som do render: cada faixa no instante, com o "in", a duracao, a subida e a descida de la.

    O DEFEITO QUE ISTO APANHA: o plano do palco (palcoSomPlano, que faz o som com as copias inteiras e as regras do
    render) afastar-se do que o render.som_do_ficheiro() toca: outro instante, outro sitio do ficheiro, outra
    duracao (o cruzamento, o fim de frase), outra subida ou descida, outro ganho; os videos de abertura sem o som
    deles; as marcas que o montar absorve (o eco da 087) a entrarem a dobrar. E depois o que o palco tem de fazer
    sozinho: a musica marcada vai com a foto quando ela muda de sitio, uma marca nova entra no clip marcado e corta
    o leito anterior (com o cruzamento), tirar uma marca estica o leito anterior ate a seguinte, e nos creditos a
    ultima continua ate ao fim deles. E o nivel de cada troco, medido com o ebur128 na copia, e o alvo do render.
    """
    if not shutil.which("node"):
        salta("Mesa: o som toca como o render", "sem node neste PC")
        return
    import palco_para_mesa
    import som_para_mesa
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    audio, info = _som_da_mesa()
    if not filme or not som:
        salta("Mesa: o som toca como o render", "sem data/montagens/v3.csv")
        return
    if not audio:
        salta("Mesa: o som toca como o render", "sem as copias do som: py -3.11 scripts/audio_para_mesa.py")
        return
    problemas = []
    videos, fim, entradas = _entradas_do_render()
    est = _estado_montado()
    versao = [v for v in est["versoes"] if v["id"] == filme["versao"]][0]
    marcada = next(fx for fx in som["faixas"] if fx["origem"] == "mesa" and fx["clip"].startswith("foto:"))
    clair = next(fx for fx in som["faixas"] if fx["origem"] == "mesa" and fx["f"].startswith("Gilbert"))
    corpo_js = """
var v = %(v)s, F = palcoFilme(v), p = palcoSomPlano(F);
var limpa = function(l){ return l.map(function(x){ return {k: x.k, tipo: x.tipo, f: x.f, ini: x.ini, "in": x["in"], dura: x.dura, subida: x.subida,
  descida: x.descida, curva: x.curva, ganho: x.ganho, gdb: x.gdb, cruza: x.cruza, nova: !!x.nova, creditos: !!x.creditos, url: x.url, clip: x.clip}; }); };
var saida = {plano: limpa(p.plano), notas: p.notas, videos: F.videos, total: F.total};
var chaves = chavesDaVersao(v), k = chaves.indexOf(%(clip)s);
/* a foto marcada seis clips mais a frente */
var w = JSON.parse(JSON.stringify(v)), c = w.clips.splice(k, 1)[0]; w.clips.splice(k + 6, 0, c);
var G = palcoFilme(w);
saida.movida = {ini: G.porI[k + 6].ini, plano: limpa(palcoSomPlano(G).plano)};
/* uma marca nova a meio do bloco da Ana Faria, e a do Clair tirada */
var x = JSON.parse(JSON.stringify(v)), kc = chaves.indexOf(%(clair)s), alvo = -1;
for(var i = 0; i < x.clips.length; i++){ var s = F.porI[i]; if(s && s.t === "foto" && s.ini > F.videos + 140 && s.ini < F.videos + 170){ alvo = i; break; } }
x.clips[alvo].m = {f: "Pharrell Williams - Happy (Lyrics)", "in": 0};
delete x.clips[kc].m;
var H = palcoFilme(x), ph = palcoSomPlano(H);
saida.nova = {ini: H.porI[alvo].ini, plano: limpa(ph.plano), notas: ph.notas};
CRED_FALSO = {dur: 60};
var C = palcoFilme(v), q = palcoSomPlano(C);
saida.creditos = {ini: C.cred.ini, total: C.total, plano: limpa(q.plano)};
console.log(JSON.stringify(saida));
""" % {"v": json.dumps(versao, ensure_ascii=False), "clip": json.dumps(marcada["clip"]), "clair": json.dumps(clair["clip"])}
    r = _correr_palco({"filme": filme}, som, audio, corpo_js, problemas, info)
    alvo = info["r"]["alvo"]
    if r:
        plano = r["plano"]
        corpo_p = [x for x in plano if x["tipo"] != "abertura"]
        aberturas = [x for x in plano if x["tipo"] == "abertura"]
        if len(corpo_p) != len(entradas):
            problemas.append("o palco toca %d faixas e o render %d" % (len(corpo_p), len(entradas)))
        for e in entradas:
            sub = e.get("subida") or (0.03 if e.get("voz") or e.get("video") else (1.0 if e["quando"] > 0.05 else 0.4))
            des = e.get("descida") or (0.03 if e.get("voz") or e.get("video") else max(1.0, e.get("cruza", 0.0)))
            p = [x for x in corpo_p if x["f"] == e["ficheiro"] and abs(x["ini"] - (videos + e["quando"])) < 0.011]
            if not p:
                problemas.append("a faixa %s dos %.2f s do corpo nao esta no palco" % (e["ficheiro"][:28], e["quando"]))
                continue
            p = p[0]
            for nome_c, a, b in (("o in", p["in"], e["in_s"]), ("a duracao", p["dura"], e["dura"]), ("a subida", p["subida"], sub),
                                 ("a descida", p["descida"], des), ("o ganho", p["ganho"], e["ganho"])):
                if abs(a - b) > 0.011:
                    problemas.append("%s de %s aos %.2f s: palco %.3f, render %.3f" % (nome_c, e["ficheiro"][:24], e["quando"], a, b))
            if p["curva"] != e.get("curva", "tri"):
                problemas.append("a curva de %s: palco %s, render %s" % (e["ficheiro"][:24], p["curva"], e.get("curva", "tri")))
            if not p["url"] or not os.path.exists(os.path.join(REPO, "saida", p["url"])):
                problemas.append("sem a copia de %s (%s)" % (e["ficheiro"][:28], p["url"]))
        for l in filme["linhas"]:
            if l["t"] == "video" and l["filme"] < videos - 0.01:
                if not any(abs(a["ini"] - l["filme"]) < 0.006 and abs(a["dura"] - l["d"]) < 0.006 for a in aberturas):
                    problemas.append("o som do video de abertura dos %.2f s nao toca" % l["filme"])
        # com a versao montada so pode dizer o que o montar tambem diz: os fins de frase por medir outra vez (096)
        outras = [n for n in r["notas"] if not n.startswith("Fim de frase por medir")]
        if outras:
            problemas.append("com a versao montada o palco diz: %s" % outras)
        # a foto marcada mudou de sitio: a musica vai com ela, e o leito de antes acaba onde ela entra agora
        m = r["movida"]
        ini_m = m["ini"] + marcada["dentro"]
        if not [x for x in m["plano"] if x["f"] == marcada["f"] and x["tipo"] == "leito" and abs(x["ini"] - ini_m) < 0.011]:
            problemas.append("a musica marcada nao foi com a foto: devia entrar aos %.2f s" % ini_m)
        else:
            antes = [x for x in m["plano"] if x["tipo"] == "leito" and x["ini"] < ini_m - 0.05]
            ult = max(antes, key=lambda x: x["ini"]) if antes else None
            if ult and abs(ult["ini"] + ult["dura"] - ult["cruza"] - ini_m) > 0.011 and ult["descida"] >= 1.0:
                problemas.append("o leito antes da foto movida acaba aos %.2f s e ela entra aos %.2f s"
                                 % (ult["ini"] + ult["dura"] - ult["cruza"], ini_m))
        # a marca nova entra no clip marcado e corta o leito de antes, a cruzar; a tirada deixa de tocar
        n = r["nova"]
        happy = [x for x in n["plano"] if x["f"].startswith("Pharrell") and abs(x["ini"] - n["ini"]) < 0.011]
        if not happy or not happy[0]["nova"]:
            problemas.append("a marca nova nao entrou no clip marcado (aos %.2f s)" % n["ini"])
        else:
            ana = [x for x in n["plano"] if x["f"].startswith("Ana Faria")]
            if not ana or abs(ana[0]["ini"] + ana[0]["dura"] - ana[0]["cruza"] - happy[0]["ini"]) > 0.011 or abs(ana[0]["cruza"] - 2.2) > 0.011:
                problemas.append("a Ana Faria nao acaba na marca nova com o cruzamento: %s" % (ana[:1],))
            seguinte = [x for x in n["plano"] if x["tipo"] == "leito" and x["ini"] > happy[0]["ini"] + 0.05]
            if seguinte and abs(happy[0]["ini"] + happy[0]["dura"] - happy[0]["cruza"] - min(x["ini"] for x in seguinte)) > 0.011:
                problemas.append("a marca nova nao acaba onde entra a seguinte")
        if any(x["f"].startswith("Gilbert") for x in n["plano"]):
            problemas.append("a marca do Clair foi tirada e o Clair continua a tocar")
        if not any("marca" in t for t in n["notas"]):
            problemas.append("o palco nao diz que a marca nova so chega ao render depois de montar: %s" % n["notas"])
        # os creditos: a ultima musica continua ate ao fim deles (ou ate ao fim do ficheiro)
        cr = r["creditos"]
        ult = max([x for x in cr["plano"] if x["tipo"] == "leito"], key=lambda x: x["ini"])
        resta = audio[ult["f"]]["duracao"] - ult["in"]
        if not ult["creditos"] or abs(ult["ini"] + ult["dura"] - min(cr["total"], ult["ini"] + resta)) > 0.011:
            problemas.append("nos creditos a ultima musica nao continua ate ao fim deles: %s" % {k: ult[k] for k in ("f", "ini", "dura")})
        # o nivel: o troco que toca fica ao alvo do render, vezes o ganho
        import audio_para_mesa
        import render
        for e in [x for x in corpo_p if x["tipo"] == "leito"][:3] + [x for x in corpo_p if x["tipo"] == "efeito"][:1]:
            ent = next((y for y in entradas if y["ficheiro"] == e["f"] and abs(videos + y["quando"] - e["ini"]) < 0.011), None)
            if ent is None:
                continue                    # uma faixa a mais ja esta dita em cima
            dm = ent.get("dura_medida") or ent["dura"]
            rr = subprocess.run([render.ffmpeg(), "-hide_banner", "-nostats", "-ss", "%.3f" % e["in"], "-t", "%.3f" % dm, "-i",
                                 os.path.join(REPO, "saida", e["url"]), "-af", "pan=stereo|c0=c0|c1=c0,ebur128=framelog=quiet",
                                 "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
            achado = audio_para_mesa.INTEGRADA.findall(rr.stderr or "")
            if not achado or abs(float(achado[-1]) + e["gdb"] - alvo) > 0.5:
                problemas.append("%s fica a %s LUFS e o alvo e %.2f" % (e["f"][:24], (float(achado[-1]) + e["gdb"]) if achado else "?", alvo))
    verifica("Mesa: o som toca como o render", not problemas, "; ".join(problemas)[:400] if problemas else
             "%d faixas e %d videos (in, duracao, subida, descida, curva, ganho ao centesimo), a marcada anda com a foto, "
             "a nova corta a anterior, a tirada some, os creditos continuam, o nivel bate com o ebur128"
             % (len(entradas), len([x for x in r["plano"] if x["tipo"] == "abertura"])))


def teste_palco_fita_como_o_linha_tempo():
    """As paragens da fita e quem nasce nela sao as contas do linha_tempo.py e do montar_da_mesa.py.

    O DEFEITO QUE ISTO APANHA: o palco a parar a fita noutro instante (a palavra acenderia antes ou depois
    dos foguetes), ou a por o nome de outro bebe. Compara-se o palcoParagens() com o
    linha_tempo.posicao_com_paragens() numa grelha de instantes, com e sem espera no primeiro, e o
    palcoQuemNasce() com o montar_da_mesa.quem_nasce_na_fita() em todas as fitas das versoes.
    """
    if not shutil.which("node"):
        salta("Mesa: a fita como o linha_tempo", "sem node neste PC")
        return
    import linha_tempo
    import montar_da_mesa
    problemas = []
    casos = [([0.0, 0.3, 0.3, 0.7, 1.0], 0.70, True), ([0.2, 0.5, 0.9], 0.70, False), ([31.0, 30.0, 16.0, 0.0], 0.62, True),
             ([4.0], 0.62, False), ([0.0, 280.0], 0.62, True), ([0.6787, 0.6962], 0.70, False)]
    ps = [k / 200.0 for k in range(201)]
    fitas = []
    for v in _estado_montado()["versoes"]:
        fitas += [c.get("x") or "" for c in v["clips"] if c.get("t") == "marcos"]
    fitas = sorted(set(fitas)) + ["1995@0-1|*12/09 Tiago;*24/11 Clara", "1995@0-0.5|*12/09 x;*24/11 y", "1995|*24/11 Nasce a Clara"]
    corpo_js = """
var casos = %(casos)s, ps = %(ps)s, fitas = %(fitas)s;
console.log(JSON.stringify({pos: casos.map(function(c){ return ps.map(function(p){ var r = palcoParagens(p, c[0], c[1], c[2]); return [r.pos, r.qual, r.dentro]; }); }),
                            quem: fitas.map(palcoQuemNasce)}));
""" % {"casos": json.dumps(casos), "ps": json.dumps(ps), "fitas": json.dumps(fitas, ensure_ascii=False)}
    r = _correr_palco({}, None, None, corpo_js, problemas)
    if r:
        for (paragens, fracao, primeiro), lista in zip(casos, r["pos"]):
            for p, (pos, qual, dentro) in zip(ps, lista):
                e = linha_tempo.posicao_com_paragens(p, paragens, fracao, primeiro)
                if abs(e[0] - pos) > 1e-9 or e[1] != qual or abs(e[2] - dentro) > 1e-9:
                    problemas.append("paragens %s em p=%.3f: palco %s, linha_tempo %s" % (paragens, p, (pos, qual, dentro), e))
                    break
        for x, quem in zip(fitas, r["quem"]):
            certo = montar_da_mesa.quem_nasce_na_fita(x) or ""
            if quem != certo:
                problemas.append("na fita %r nasce %r para o montar e %r para o palco" % (x[:40], certo, quem))
    verifica("Mesa: a fita como o linha_tempo", not problemas, "; ".join(problemas)[:300] if problemas else
             "%d paragens em %d instantes, %d fitas" % (len(casos), len(ps), len(fitas)))


def teste_som_da_mesa_cabe_e_o_palco_nao_escreve():
    """O som da Mesa cabe nas publicacoes, a pagina leva o mapa do contrato, e o palco so le o estado.

    O DEFEITO QUE ISTO APANHA: um ficheiro de som acima de 15 MB; um lote acima dos 64 MB de uma publicacao, ou o
    endereco com mais de 256 ficheiros a contar com a pagina e as previas; o window.AUDIO montado sem o url, o
    ganho e a duracao de cada som (o contrato), ou com um url que nao esta em saida/; e o palco a escrever no
    estado (gravar, anular, mudar um clip ou uma marca), que e o que a Mesa nunca faz sozinha (decisao 083).
    """
    import contextlib
    import gerar_mesa
    problemas = []
    audio, info = _som_da_mesa()
    detalhe = "sem som feito neste PC"
    if audio:
        for lote in info["lotes"]:
            if lote["bytes"] > 64 * 1048576 or len(lote["ficheiros"]) > 255:
                problemas.append("um lote de %.1f MB e %d ficheiros nao cabe numa publicacao" % (lote["bytes"] / 1048576.0, len(lote["ficheiros"])))
        if info["grandes"]:
            problemas.append("ficheiros acima de 15 MB: %s" % info["grandes"])
        previas = os.path.join(REPO, "saida", "previas")
        folhas = [f for f in os.listdir(previas) if f.endswith(".jpg")] if os.path.isdir(previas) else []
        n = 1 + len(folhas) + info["ficheiros"]
        if n > 256:
            problemas.append("a pagina, %d folhas e %d ficheiros de som e video sao %d ficheiros, e o endereco aceita 256"
                             % (len(folhas), info["ficheiros"], n))
        detalhe = ("%d ficheiros de som e video, %.1f MB (%.1f de som), em %d %s; com a pagina e as %d folhas sao %d ficheiros"
                   % (info["ficheiros"], info["bytes"] / 1048576.0, info["bytes_som"] / 1048576.0, len(info["lotes"]),
                      "publicacao" if len(info["lotes"]) == 1 else "publicacoes", len(folhas), n))
    pasta = tempfile.mkdtemp(prefix="mesa_1002_palco_")
    guardado = gerar_mesa.SAIDA
    gerar_mesa.SAIDA = os.path.join(pasta, "mesa.html")
    antes_som = os.environ.get("MESA_SOM")
    os.environ["MESA_SOM"] = "ler"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            gerar_mesa.main()
        montada = io.open(gerar_mesa.SAIDA, encoding="utf-8").read()
    finally:
        gerar_mesa.SAIDA = guardado
        if antes_som is None:
            os.environ.pop("MESA_SOM", None)
        else:
            os.environ["MESA_SOM"] = antes_som
        shutil.rmtree(pasta, ignore_errors=True)
    # o window.MUSICA_FIM (a musica dos creditos, 2 de outubro a tarde) vem no mesmo <script>, depois do AUDIO_INFO
    m = re.findall(r"<script>\nwindow\.PALCO = (\{.*?\});\nwindow\.AUDIO = (.*?);\nwindow\.AUDIO_INFO = (.*?);\n"
                   r"(?:window\.MUSICA_FIM = .*?;\n)?</script>\n", montada, re.S)
    if len(m) != 1:
        problemas.append("o window.PALCO aparece %d vezes na Mesa montada" % len(m))
    else:
        p = json.loads(m[0][0].replace("<\\/", "</"))
        if not p.get("filme") or not p["filme"].get("linhas"):
            problemas.append("o window.PALCO montado nao traz o filme")
        a = json.loads(m[0][1].replace("<\\/", "</"))
        if audio and not a:
            problemas.append("o window.AUDIO montado vem vazio")
        for nome, x in (a or {}).items():
            if not (isinstance(x, dict) and isinstance(x.get("url"), str) and isinstance(x.get("ganho_db"), (int, float))
                    and isinstance(x.get("duracao"), (int, float))):
                problemas.append("o window.AUDIO de %s nao tem url, ganho_db e duracao" % nome[:30])
                break
            if not os.path.exists(os.path.join(REPO, "saida", x["url"])):
                problemas.append("o url de %s nao esta em saida/: %s" % (nome[:30], x["url"]))
                break
        if audio and not json.loads(m[0][2].replace("<\\/", "</")):
            problemas.append("o window.AUDIO_INFO montado vem vazio")
    # o palco so le: no bloco dele nao ha gravacoes, anulares nem escritas num clip ou no estado
    html = io.open(EDITOR, encoding="utf-8").read()
    i, j = html.find("/* ---------- o filme no palco: o relogio, os clips e o som"), html.find("/* ---------- exportação ---------- */")
    if i < 0 or j < i:
        problemas.append("nao encontrei o bloco do palco no editor_base.html")
    else:
        bloco = html[i:j]
        for proibido in ("marcar(", "guardaDesfazer", "gravar(", "est.versoes =", "est.estilo =", "est.creditos =",
                         "c.x =", "c.d =", "c.c =", "c.m =", "c.vz =", ".clips.splice", ".clips.push"):
            if proibido in bloco:
                problemas.append("o palco tem %r" % proibido)
    verifica("Mesa: o som cabe e o palco so le", not problemas, "; ".join(problemas)[:300] if problemas else detalhe)


def teste_medidas_do_som_iguais_ao_render():
    """As medidas das copias dao o que o render e o montar medem nos originais.

    O DEFEITO QUE ISTO APANHA: o palco decidir de outra maneira o que o render decide pelo som do ficheiro. A
    entrada num inicio (render.entra_num_inicio, que tira a rampa da subida: os `inicios`), o silencio que uma
    musica marcada salta (montar_da_mesa.silencio_no_inicio: os `silencios`), e a sonoridade de cada troco, que
    o palco tira do `perfil` para lhe dar o nivel do render: comparada com o ebur128 do mesmo troco da copia.
    """
    import math
    import audio_para_mesa
    import montar_da_mesa
    import render
    audio, _info = _som_da_mesa()
    if not audio:
        salta("Mesa: as medidas do som iguais ao render", "sem as copias do som")
        return
    problemas = []
    _videos, _fim, entradas = _entradas_do_render()

    def sonoridade(f, a, b):
        x = audio[f]
        per, desde = x["perfil"], x.get("desde", 0.0)
        a, b = a - desde, b - desde
        bl = []
        for k in range(max(0, int(math.floor(a))), min(len(per), int(math.ceil(b)))):
            w = min(b, k + 1) - max(a, k)
            if w > 0 and per[k] / 10.0 > -70:
                bl.append((w, 10 ** (per[k] / 100.0)))

        def media(l):
            return sum(w * e for w, e in l) / sum(w for w, _e in l)
        rel = 10 * math.log10(media(bl)) - 10
        dentro = [q for q in bl if 10 * math.log10(q[1]) > rel]
        return 10 * math.log10(media(dentro or bl))
    pior = 0.0
    for e in entradas:
        f = e["ficheiro"]
        if f not in audio:
            problemas.append("sem copia de %s" % f[:30])
            continue
        js = e["in_s"] < 0.05 or any(a - 0.005 <= e["in_s"] <= b + 0.005 for a, b in audio[f].get("inicios", []))
        if js != render.entra_num_inicio(e):
            problemas.append("entra num inicio de %s aos %.2f s: copias %s, render %s" % (f[:24], e["in_s"], js, not js))
    for e in [x for x in entradas if not render.e_efeito_de_som(x)][:4] + [x for x in entradas if render.e_efeito_de_som(x)][:2]:
        f = e["ficheiro"]
        dm = e.get("dura_medida") or e["dura"]
        rr = subprocess.run([render.ffmpeg(), "-hide_banner", "-nostats", "-ss", "%.3f" % e["in_s"], "-t", "%.3f" % dm, "-i",
                             os.path.join(REPO, "saida", audio[f]["url"]), "-af", "pan=stereo|c0=c0|c1=c0,ebur128=framelog=quiet",
                             "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        achado = audio_para_mesa.INTEGRADA.findall(rr.stderr or "")
        if achado:
            pior = max(pior, abs(sonoridade(f, e["in_s"], e["in_s"] + dm) - float(achado[-1])))
    if pior > 0.5:
        problemas.append("a sonoridade de um troco tirada do perfil fica a %.2f dB do ebur128" % pior)
    # o silencio que uma marca salta: o do montar, do principio e do sitio onde cada musica da montagem entra
    mus = montar_da_mesa.caminhos_de_musica()
    vistos = 0
    for e in entradas:
        f = e["ficheiro"]
        if f not in mus or f not in audio or render.e_efeito_de_som(e):
            continue
        for dentro in (0.0, round(e["in_s"], 2)):
            certo = montar_da_mesa.silencio_no_inicio(mus[f], dentro)
            meu = 0.0
            for a, b in audio[f].get("silencios", []):
                if b <= dentro + 1e-6:
                    continue
                if a - dentro > 0.05 or b - max(a, dentro) < 0.3 - 1e-6:
                    break
                meu = 0.0 if b - dentro >= montar_da_mesa.JANELA_SILENCIO - 0.05 else round(b - dentro, 2)
                break
            vistos += 1
            if abs(meu - certo) > 0.011:
                problemas.append("silencio de %s a partir dos %.2f s: copias %.2f, montar %.2f" % (f[:24], dentro, meu, certo))
    verifica("Mesa: as medidas do som iguais ao render", not problemas, "; ".join(problemas)[:300] if problemas else
             "%d entradas num inicio, %d silencios e a sonoridade a %.2f dB do ebur128 no pior" % (len(entradas), vistos, pior))


# ------------------------------------------------------------------------- a zona de destaque (clip.zd)
# O Tiago, a 2 de outubro: marcar numa foto de equipa quem e quem, sem zoom (o contrato, seccao 1b). A Mesa
# desenha a zona (rato e dedo), grava clip.zd so com o que difere da omissao, mostra-a como o render, e avisa sem
# corrigir. Guarda-se aqui que:
#  12. o que a Mesa grava e o que o montar escreve na coluna destaque e o render le, sem avisos, e a Mesa le a
#      zona e conta quando acende como o render (destaque_janela, destaque_tempo_aceso);
#  13. a Mesa avisa nos casos do montar (pouco tempo aceso, com a mesma duracao que chega; um nome que e uma
#      frase; uma zona num grupo) e mais nos do pedido (maior do que metade da foto; em rajada, sempre);
#  14. cada gesto (desenhar, mudar pelo canto, mover pelo meio, o teclado, tirar) e uma entrada no anular e uma
#      gravacao, um toque ou um cancelamento nao mudam nada, e um clip que saiu da versao nao recebe nada.
DECLARACOES_ZD = ["var ZD = ", "var PALCO_DESTAQUE = ", "var LEGENDA_MINIMO_S = "]
FUNCOES_ZD_CONTAS = ["function zdLida(", "function zdPoe(", "function zdEscNormal(", "function zdTempoAceso(",
                     "function palcoDestaqueJanela(", "function zdS(", "function zdPct(", "function avisosDoDestaque(",
                     "function zdSeg(", "function zdForaDoEcra(", "function palcoCaixaDaFoto("]
FUNCOES_ZD_GESTOS = ["function zdParte(", "function zdPonto(", "function zdComeca(", "function zdMexe(",
                     "function zdLarga(", "function zdGrava(", "function zdTeclado(", "function guardaDesfazerCampos(",
                     "function desfazer("]
PRELUDE_ZD = """
var porId = %(porid)s, focos = {};
function focoDe(id){ return focos[id] || null; }
function aproximaAtivo(c){ return false; }
function palcoAproxima(){ return {r: 1, cx: 960, cy: 540}; }
var PALCO_R = {zoom: 0.12, afastada: 0.80, respira: 0.04};
/* o tempo de cada clip vem do teste: as duracoes e os encadeados que o render.encadeados_do_corpo da */
function encadeadosDe(v, i){ return v.e[i]; }
function duracaoNoRender(v, i){ return +v.clips[i].d; }
function zdLarguraDoNome(t){ return 36 + 25 * t.length; }
"""


def _correr_zd(funcoes, prelude, corpo_js, problemas):
    html = io.open(EDITOR, encoding="utf-8").read()
    blocos = "\n".join([_declaracao(html, m, problemas) for m in DECLARACOES_ZD] +
                       [_bloco(html, m, problemas) for m in funcoes])
    if problemas:
        return None
    programa = '"use strict";\n' + prelude + "\n" + blocos + "\n" + corpo_js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        r = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if r.returncode != 0:
        problemas.append("o node parou: " + " | ".join((r.stderr or r.stdout).strip().splitlines()[-4:])[:300])
        return None
    return json.loads(r.stdout)


def _montar_calado():
    # importado fora de qualquer redirect: ele faz sys.stdout.reconfigure() ao ser importado
    import montar_da_mesa
    return montar_da_mesa


def teste_destaque_grava_o_que_o_montar_e_o_render_leem():
    """A zona que a Mesa grava passa pelo montar sem avisos e o render le-a como a Mesa; os tempos sao os dele.

    O DEFEITO QUE ISTO APANHA: a Mesa a gravar a omissao (forma "retangulo", escurecer 0,45, um texto em
    branco), que fazia o montar escrever a coluna com o que nao difere; uma zona que passa da foto por
    arredondamento, que o montar cortava com aviso; o render a ler outra zona, outra forma ou outro escurecer do
    que a Mesa mostra; e a Mesa a dizer que a zona acende noutra altura, ou fica acesa outro tempo, do que o
    render.destaque_janela() e o destaque_tempo_aceso() contam.
    """
    if not shutil.which("node"):
        salta("Mesa: a zona grava o que o montar e o render leem", "sem node neste PC")
        return
    import render
    montar = _montar_calado()
    problemas = []
    casos = [{"x": 0.2, "y": 0.3, "w": 0.1, "h": 0.2, "forma": "retangulo", "texto": "", "escurecer": 0.45},
             {"x": 0.123456, "y": 0.654321, "w": 0.2, "h": 0.3, "forma": "elipse", "texto": "  Tiago  ", "escurecer": 0.6},
             {"x": -0.05, "y": 0.9, "w": 0.2, "h": 0.3, "forma": "retangulo", "texto": "", "escurecer": 0.45},
             {"x": 0.5, "y": 0.5, "w": 0.3, "h": 0.3, "forma": "retangulo", "texto": "   ", "escurecer": 0},
             {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "forma": "elipse", "texto": "Clara", "escurecer": 1.4},
             {"x": 0.33333, "y": 0.66667, "w": 0.33333, "h": 0.33333, "forma": "quadrado", "texto": "", "escurecer": None}]
    grelha = [[d, e, s] for d in (0.5625, 1.5, 2.2, 2.6, 3.0, 4.0, 6.0) for e in (0.0, 0.7, 1.0) for s in (0.0, 0.7, 2.5)]
    js = """
var casos = %s, grelha = %s, r = {poe: [], lida: [], janela: [], aceso: []};
casos.forEach(function(z){ var c = {t: "foto"}; zdPoe(c, z); r.poe.push(c.zd); r.lida.push(zdLida(c)); });
grelha.forEach(function(g){ r.janela.push(palcoDestaqueJanela(g[0], g[1], g[2])); r.aceso.push(zdTempoAceso(g[0], g[1], g[2])); });
r.semZona = [zdLida({}), zdLida({zd: {x: 0.5, y: 0.5, w: 0.004, h: 0.3}}), zdLida({zd: {x: true, y: 0, w: 0.2, h: 0.2}})];
console.log(JSON.stringify(r));
""" % (json.dumps(casos), json.dumps(grelha))
    r = _correr_zd(FUNCOES_ZD_CONTAS, PRELUDE_ZD % {"porid": "{}"}, js, problemas)
    if r:
        poe, lida = r["poe"], r["lida"]
        if set(poe[0]) != {"x", "y", "w", "h"}:
            problemas.append("a omissao foi gravada: %s" % poe[0])
        if poe[1] != {"x": 0.1235, "y": 0.6543, "w": 0.2, "h": 0.3, "forma": "elipse", "texto": "Tiago", "escurecer": 0.6}:
            problemas.append("forma, nome e escurecer: %s" % poe[1])
        if poe[2]["x"] != 0 or abs(poe[2]["y"] + poe[2]["h"] - 1) > 1e-9 or abs(poe[2]["w"] - 0.15) > 1e-9:
            problemas.append("a zona que passa da foto nao ficou dentro: %s" % poe[2])
        if "texto" in poe[3] or poe[3].get("escurecer") != 0:
            problemas.append("o nome em branco ou o escurecer 0: %s" % poe[3])
        if poe[4].get("escurecer") != 1:
            problemas.append("o escurecer acima de 1 nao ficou em 1: %s" % poe[4])
        if "forma" in poe[5] or "escurecer" in poe[5]:
            problemas.append("uma forma que nao existe ou um escurecer vazio foram gravados: %s" % poe[5])
        for k, zd in enumerate(poe):
            avisos = []
            coluna = montar.coluna_do_destaque({"zd": zd}, "foto", k + 1, avisos)
            if avisos:
                problemas.append("o montar avisou da zona %d: %s" % (k + 1, avisos))
            if json.loads(coluna) != zd:
                problemas.append("o montar escreveu %s e a Mesa gravou %s" % (coluna, zd))
            lido, aviso = render.ler_destaque(coluna)
            m = lida[k]
            if aviso or lido is None or any(abs(lido[c] - m[c]) > 1e-9 for c in "xywh") or \
                    (lido["forma"], lido["texto"], abs(lido["escurecer"] - m["escurecer"]) < 1e-9) != (m["forma"], m["texto"], True):
                problemas.append("o render le %s (%s) e a Mesa %s" % (lido, aviso, m))
        if r["semZona"] != [None, None, None]:
            problemas.append("uma zona sem tamanho ou com um booleano leu-se: %s" % r["semZona"])
        for g, j, a in zip(grelha, r["janela"], r["aceso"]):
            jr = render.destaque_janela(*g)
            if (j is None) != (jr is None) or (j and any(abs(x - y) > 1e-9 for x, y in zip(j, jr))):
                problemas.append("com %s a Mesa acende em %s e o render em %s" % (g, j, jr))
                break
            if abs(a - render.destaque_tempo_aceso(*g)) > 1e-9:
                problemas.append("com %s a Mesa diz %.3f s acesa e o render %.3f" % (g, a, render.destaque_tempo_aceso(*g)))
                break
    verifica("Mesa: a zona grava o que o montar e o render leem", not problemas, "; ".join(problemas)[:400] if problemas else
             "%d zonas sem avisos e iguais nos tres, %d tempos iguais ao render" % (len(casos), len(grelha)))


def teste_destaque_avisa_como_o_montar():
    """A Mesa avisa da zona nos casos do montar, com os mesmos numeros, e nos do pedido; nunca corrige.

    O DEFEITO QUE ISTO APANHA: a Mesa calada numa zona que acende pouco tempo, ou a dizer outra duracao que
    chega do que o montar (avisos_do_tempo_do_destaque); calada com um nome que e uma frase ou com uma zona que
    ficou num grupo (coluna_do_destaque); e calada nos dois avisos que o pedido manda dar e o montar nao da:
    a zona maior do que metade da foto, e a foto em rajada, onde a zona nao se ve.
    """
    if not shutil.which("node"):
        salta("Mesa: a zona avisa como o montar", "sem node neste PC")
        return
    import re as _re
    import render
    montar = _montar_calado()
    problemas = []
    zd = {"x": 0.4, "y": 0.3, "w": 0.15, "h": 0.25}
    # (nome, duracao, encadeado do clip, encadeado do seguinte, tratamento, tipo, zona)
    casos = [("curta", 2.5, 0.7, 0.7, "fundo", "foto", zd),
             ("quatro", 4.0, 0.7, 0.7, "fundo", "foto", zd),
             ("rajada", 0.5625, 0.0, 0.0, "rajada", "foto", zd),
             ("rajadaLonga", 4.0, 0.7, 0.7, "rajada", "foto", zd),
             ("frase", 4.0, 0.7, 0.7, "fiel", "foto", dict(zd, texto="O Tiago com o pai")),
             ("grande", 4.0, 0.7, 0.7, "fiel", "foto", {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}),
             ("grupo", 6.0, 0.7, 0.7, "filas", "colagem", zd)]
    montar_diz, clips, enc = {}, [], []
    for nome, d, e, s, trat, tipo, z in casos:
        corpo = [{"ordem": 1, "tipo": "foto", "duracao_s": "4", "transicao_s": "0.7", "tratamento": "fiel"},
                 {"ordem": 2, "tipo": tipo, "duracao_s": str(d), "transicao_s": str(e), "tratamento": trat,
                  "destaque": ""},
                 {"ordem": 3, "tipo": "foto", "duracao_s": "4", "transicao_s": str(s), "tratamento": "fiel"}]
        avisos = []
        corpo[1]["destaque"] = montar.coluna_do_destaque({"zd": z}, tipo, 2, avisos)
        avisos += montar.avisos_do_tempo_do_destaque(corpo, render)
        montar_diz[nome] = avisos
        entra, sai = render.encadeados_do_corpo(corpo)[1]
        clips.append({"t": tipo, "i": "f1", "d": d, "c": e, "r": trat, "zd": z})
        enc.append({"entra": entra, "sai": sai})
    js = """
var v = {clips: %s, e: %s}, nomes = %s, r = {};
nomes.forEach(function(n, i){ r[n] = avisosDoDestaque(v, i); });
r.semZona = avisosDoDestaque({clips: [{t: "foto", i: "f1", d: 4}], e: [{entra: 0.7, sai: 0.7}]}, 0);
/* a etiqueta da lista de clips, pela mesma regra: a rajada de 0,56 s nao se ve, a de 4 s ve-se (o render desenha-a) */
r.etiqueta = {};
nomes.forEach(function(n, i){ r.etiqueta[n] = {titulo: zdTituloDaEtiqueta(v.clips[i], v, i), vese: v.clips[i].r === "rajada" ? zdVeSeNaRajada(v, i) : null}; });
console.log(JSON.stringify(r));
""" % (json.dumps(clips), json.dumps(enc), json.dumps([c[0] for c in casos]))
    r = _correr_zd(FUNCOES_ZD_CONTAS + ["function zdVeSeNaRajada(", "function zdTituloDaEtiqueta("],
                   PRELUDE_ZD % {"porid": json.dumps({"f1": {"id": "f1", "w": 4000, "h": 3000}})}, js, problemas)
    if r:
        textos = lambda n: " ".join(a["texto"] for a in r[n])
        numero = lambda t: [float(x.replace(",", ".")) for x in _re.findall(r"\d+(?:[.,]\d+)?", t)]
        # pouco tempo acesa: os dois avisam, e com a mesma duracao que chega e o mesmo tempo aceso
        m = " ".join(montar_diz["curta"])
        mesa = [a for a in r["curta"] if "fica inteira só" in a["texto"]]
        if not mesa or "so " not in m:
            problemas.append("pouco tempo acesa: a Mesa %s, o montar %s" % (r["curta"], montar_diz["curta"]))
        else:
            nm, nmesa = numero(m.split("fica inteira so ", 1)[1]), numero(mesa[0]["texto"].split("fica inteira só ", 1)[1])
            # [aceso, 15 metros, a duracao que chega, o minimo], nos dois
            if len(nm) < 3 or len(nmesa) < 3 or abs(nm[0] - nmesa[0]) > 0.006 or abs(nm[2] - nmesa[2]) > 0.006:
                problemas.append("pouco tempo acesa: o montar diz %s e a Mesa %s" % (nm[:4], nmesa[:4]))
        if r["quatro"] or montar_diz["quatro"]:
            problemas.append("um clip de 4 s sem nada a dizer: a Mesa %s, o montar %s" % (r["quatro"], montar_diz["quatro"]))
        # em rajada: os dois na rajada da mecanica (0,56 s); a Mesa tambem numa rajada de 4 s, onde o montar se cala
        if not (r["rajada"] and r["rajada"][0]["grau"] == "erro" and "rajada" in textos("rajada") and montar_diz["rajada"]):
            problemas.append("rajada de 0,56 s: a Mesa %s, o montar %s" % (r["rajada"], montar_diz["rajada"]))
        if not (r["rajadaLonga"] and r["rajadaLonga"][0]["grau"] == "confirma" and "ainda se vê" in textos("rajadaLonga")):
            problemas.append("rajada de 4 s: a Mesa %s" % r["rajadaLonga"])
        if "5 palavras" not in textos("frase") or not any("palavras" in a for a in montar_diz["frase"]):
            problemas.append("um nome que e uma frase: a Mesa %s, o montar %s" % (r["frase"], montar_diz["frase"]))
        if "64 % da foto" not in textos("grande"):
            problemas.append("a zona de 64%% da foto: a Mesa %s" % r["grande"])
        if "fotos soltas" not in textos("grupo") or not any("fica de fora" in a for a in montar_diz["grupo"]):
            problemas.append("uma zona num grupo: a Mesa %s, o montar %s" % (r["grupo"], montar_diz["grupo"]))
        if r["semZona"]:
            problemas.append("uma foto sem zona tem avisos: %s" % r["semZona"])
        et = r["etiqueta"]
        if et["rajada"]["vese"] is not False or not et["rajada"]["titulo"].endswith("Em rajada não se vê"):
            problemas.append("a etiqueta da rajada de 0,56 s: %s" % et["rajada"])
        if et["rajadaLonga"]["vese"] is not True or "ainda se vê" not in et["rajadaLonga"]["titulo"]:
            problemas.append("a etiqueta da rajada de 4 s, que o render desenha e se ve: %s" % et["rajadaLonga"])
        if "rajada" in et["quatro"]["titulo"]:
            problemas.append("a etiqueta de uma foto solta fala de rajada: %s" % et["quatro"])
    verifica("Mesa: a zona avisa como o montar", not problemas, "; ".join(problemas)[:400] if problemas else
             "pouco tempo (com a mesma duracao que chega), frase, grupo, e os do pedido: zona grande e rajada (aviso e etiqueta)")


def teste_destaque_gestos_e_anular():
    """Desenhar, mudar pelo canto, mover pelo meio, o teclado e tirar: um gesto, uma entrada no anular.

    O DEFEITO QUE ISTO APANHA: um arrasto que grava a cada movimento (a base levava meias zonas e o anular
    voltava um pixel de cada vez); um toque sem arrastar, ou um gesto cancelado pelo browser, a mudar a zona; um
    canto que vira a zona do avesso ou a deixa sem tamanho; o meio a deixar a zona sair da foto; o teclado a
    abrir uma entrada no anular por tecla; o Ctrl+Z a nao voltar a zona de antes; e um gesto que acaba num clip
    que saiu da versao (o outro aparelho, um anular) a escrever num objeto que ja nao esta na montagem.
    Tambem que o resto da pagina sabe da zona: a juncao dos dois aparelhos espera o fim do gesto, o Validar diz
    os avisos, o palco le a zona pela mesma funcao, e a foto deixa o dedo desenhar (touch-action none).
    """
    if not shutil.which("node"):
        salta("Mesa: a zona, os gestos e o anular", "sem node neste PC")
        return
    problemas = []
    prelude = PRELUDE_ZD % {"porid": "{}"} + """
var est = null, pilhaDesfazer = [], clipAtivo = 0, zdGesto = null, zdEditor = null, zdJanela = null, zdTecla = null;
var marcas = 0, avisos = [], ED = null;
var document = {activeElement: null};
function nada(){}
var pintaClips = nada, pintaVersoes = nada, zdDesenha = nada, zdFilmeDepois = nada, zdPintaJanela = nada;
/* o inspetor repintado faz um editor novo, que le a zona do clip */
function pintaInspetor(){ if(ED) ED.z = zdLida(ED.c); }
function zdAtualiza(c){ if(ED && ED.c === c) ED.z = zdLida(c); }
function marcar(){ marcas++; }
function avisar(t){ avisos.push(t); }
function versaoAtual(){ for(var k = 0; k < est.versoes.length; k++) if(est.versoes[k].id === est.atual) return est.versoes[k]; return null; }
"""
    js = """
var tela = {getBoundingClientRect: function(){ return {left: 0, top: 0, width: 400, height: 300}; }, style: {},
            setPointerCapture: nada, releasePointerCapture: nada, hasPointerCapture: function(){ return true; }, focus: nada};
var c = {t: "foto", i: "f1", d: 4, c: 0.7, r: "fundo"};
est = {versoes: [{id: "v1", clips: [{t: "cartao", x: "antes"}, c]}], atual: "v1"};
ED = {tela: tela, c: c, z: null, caixa: {}};
function ev(p, tipo){ return {pointerId: 1, pointerType: tipo || "mouse", button: 0, clientX: p[0] * 400, clientY: p[1] * 300, preventDefault: nada}; }
function gesto(a, b, tipo, cancela){
  zdComeca(ED, ev(a, tipo));
  for(var k = 1; k <= 6; k++) zdMexe(ED, ev([a[0] + (b[0] - a[0]) * k / 6, a[1] + (b[1] - a[1]) * k / 6], tipo));
  zdLarga(ED, ev(b, tipo), !!cancela);
}
function tecla(k, shift){ zdTeclado(ED, {key: k, shiftKey: !!shift, altKey: false, ctrlKey: false, metaKey: false, preventDefault: nada, stopPropagation: nada}); }
function foto(){ return c.zd === undefined ? null : JSON.parse(JSON.stringify(c.zd)); }
var r = {};
gesto([0.3, 0.3], [0.3, 0.3]); r.toque = {zd: foto(), aviso: avisos[avisos.length - 1], anular: pilhaDesfazer.length, marcas: marcas};
gesto([0.2, 0.2], [0.4, 0.5]); r.desenho = {zd: foto(), anular: pilhaDesfazer.length, marcas: marcas};
gesto([0.4, 0.5], [0.5, 0.6], "touch"); r.canto = foto();
gesto([0.35, 0.4], [0.45, 0.5]); r.meio = foto();
gesto([0.45, 0.5], [1.4, 1.4]); r.borda = foto();
gesto([1.0, 0.6], [0.6, 0.45]); r.avesso = foto();
gesto([0.05, 0.05], [0.06, 0.06]); r.pequena = {zd: foto(), aviso: avisos[avisos.length - 1]};
var antes = pilhaDesfazer.length, m0 = marcas;
gesto([0.1, 0.1], [0.3, 0.3], "touch", true); r.cancelado = {zd: foto(), anular: pilhaDesfazer.length - antes, marcas: marcas - m0};
antes = pilhaDesfazer.length; zdTecla = null;
tecla("ArrowLeft"); tecla("ArrowLeft"); tecla("ArrowLeft"); tecla("ArrowUp", true);
r.teclado = {zd: foto(), anular: pilhaDesfazer.length - antes};
desfazer(); r.anulado = foto();
zdTecla = null; tecla("Delete"); r.tirada = foto(); desfazer(); r.voltou = foto();
r.anularTudo = []; while(pilhaDesfazer.length){ desfazer(); r.anularTudo.push(foto()); }
zdTecla = null; tecla("Enter"); r.enter = foto();
/* o clip saiu da versao a meio do gesto */
zdComeca(ED, ev([0.1, 0.1])); zdMexe(ED, ev([0.2, 0.25])); est.versoes[0].clips = [{t: "cartao"}]; var antesFora = foto(), mf = marcas;
zdLarga(ED, ev([0.2, 0.25]), false); r.fora = {igual: JSON.stringify(foto()) === JSON.stringify(antesFora), marcas: marcas - mf, aviso: avisos[avisos.length - 1]};
console.log(JSON.stringify(r));
"""
    r = _correr_zd(FUNCOES_ZD_CONTAS + FUNCOES_ZD_GESTOS, prelude, js, problemas)
    perto = lambda z, o: z is not None and o is not None and all(abs(z[k] - o[k]) < 1e-6 for k in "xywh")
    if r:
        if r["toque"]["zd"] is not None or r["toque"]["anular"] or r["toque"]["marcas"] or "arrasta" not in r["toque"]["aviso"]:
            problemas.append("um toque sem arrastar: %s" % r["toque"])
        if not perto(r["desenho"]["zd"], {"x": 0.2, "y": 0.2, "w": 0.2, "h": 0.3}) or r["desenho"]["anular"] != 1 or r["desenho"]["marcas"] != 1:
            problemas.append("desenhar: %s (uma entrada no anular e uma gravacao)" % r["desenho"])
        if not perto(r["canto"], {"x": 0.2, "y": 0.2, "w": 0.3, "h": 0.4}):
            problemas.append("o canto de baixo a direita, com o dedo: %s" % r["canto"])
        if not perto(r["meio"], {"x": 0.3, "y": 0.3, "w": 0.3, "h": 0.4}):
            problemas.append("o meio: %s" % r["meio"])
        if not perto(r["borda"], {"x": 0.7, "y": 0.6, "w": 0.3, "h": 0.4}):
            problemas.append("o meio ate fora da foto devia parar na borda: %s" % r["borda"])
        if not perto(r["avesso"], {"x": 0.6, "y": 0.45, "w": 0.1, "h": 0.55}):
            problemas.append("o canto de cima a direita passado para la do canto parado: %s" % r["avesso"])
        if not perto(r["pequena"]["zd"], r["avesso"]) or "pequena" not in r["pequena"]["aviso"]:
            problemas.append("uma zona pequena de mais: %s" % r["pequena"])
        if not perto(r["cancelado"]["zd"], r["avesso"]) or r["cancelado"]["anular"] or r["cancelado"]["marcas"]:
            problemas.append("um gesto cancelado mudou alguma coisa: %s" % r["cancelado"])
        if not perto(r["teclado"]["zd"], {"x": 0.57, "y": 0.45, "w": 0.1, "h": 0.54}):
            problemas.append("o teclado (tres setas para a esquerda, Shift e a seta para cima): %s" % r["teclado"])
        if r["teclado"]["anular"] != 1:
            problemas.append("o teclado abriu %d entradas no anular, e era uma" % r["teclado"]["anular"])
        if not perto(r["anulado"], r["avesso"]):
            problemas.append("o Ctrl+Z do teclado devolveu %s" % r["anulado"])
        if r["tirada"] is not None or not perto(r["voltou"], r["avesso"]):
            problemas.append("tirar com o Delete e anular: %s, %s" % (r["tirada"], r["voltou"]))
        if r["anularTudo"][-1] is not None:
            problemas.append("anular tudo nao deixou a foto sem zona: %s" % r["anularTudo"])
        if not perto(r["enter"], {"x": 0.4, "y": 0.35, "w": 0.2, "h": 0.3}):
            problemas.append("o Enter sem zona: %s" % r["enter"])
        if not r["fora"]["igual"] or r["fora"]["marcas"] or "não ficou guardada" not in r["fora"]["aviso"]:
            problemas.append("um gesto num clip que saiu da versao: %s" % r["fora"])
    html = io.open(EDITOR, encoding="utf-8").read()
    for funcao, tem in (("function aMeioDeClips(", "zdGesto"), ("function validar(", "avisosDoDestaque(v, i)"),
                        ("function palcoDestaqueConta(", "zdLida(c)"), ("function palcoDestaque(", "palcoDestaqueConta("),
                        ("function pintaInspetor(", "blocoDestaque(v, c, f)"),
                        ("function ligaInspetor(", "ligaDestaque("), ("function pintaClips(", "zdTituloDaEtiqueta(c, v, idx)")):
        if tem not in _bloco(html, funcao, problemas):
            problemas.append("o %s) nao tem %s" % (funcao.split()[1], tem))
    if not re.search(r"\.zdTela\{[^}]*touch-action:none", html):
        problemas.append("a foto da zona nao tem touch-action:none: o dedo deslizava a pagina em vez de desenhar")
    if html.count('<dialog id="dlgZona"') != 1:
        problemas.append("a janela «Desenhar em grande» nao esta uma vez")
    verifica("Mesa: a zona, os gestos e o anular", not problemas, "; ".join(problemas)[:400] if problemas else
             "toque, desenho, canto, meio, borda, avesso, pequena, cancelado, teclado, Delete, Enter e clip fora")


# ------------------------------------------------------- o destaque no palco igual ao render (2 de outubro, a tarde)
# O palco e o «Como fica no filme» do inspetor desenham a zona pelo palcoDestaque(), e as contas dele estao no
# palcoDestaqueConta(): quanto esta acesa, onde fica a zona no ecra e onde vai o nome. Aqui guarda-se que:
#  15. as contas sao as do render.py, num instante qualquer: o destaque_alfa() com a destaque_janela() (antes de
#      acender, a meio e aceso; num clip curto, aceso com a foto), a destaque_caixa() com a foto em qualquer sitio
#      (o zoom, a rajada a encher, o afastada), e a faixa do nome do preparar_destaque() e do onde_vai_o_nome(): por
#      baixo a 14 px, por cima quando passa do teto (com ou sem legenda, de uma ou de mais linhas), encostada ao teto
#      quando nem em cima cabe, e presa a 16 px dos lados, ou solta quando e mais larga do que o ecra; com o corpo
#      da legenda de omissao e com outro do estilo.
# A largura do nome e as linhas da legenda vem do render (a letra do browser mede-se no browser): o que se compara e
# a regra. O desenho, pixel a pixel, prova-se com um fotograma do render e a captura do palco no mesmo instante.
FUNCOES_ZD_PALCO = ["function zdLida(", "function palcoSuave(", "function palcoDestaqueJanela(", "function palcoDestaqueConta("]


def teste_destaque_do_palco_como_o_render():
    """A zona e o nome no palco nos sitios e com o alfa com que o render.py os desenha."""
    problemas = []
    if not shutil.which("node"):
        salta("Mesa: o destaque do palco como o render", "sem node neste PC")
        return
    import contextlib
    import render
    zonas = [{"x": 0.48, "y": 0.17, "w": 0.08, "h": 0.13, "texto": "Tiago"},
             {"x": 0.42, "y": 0.55, "w": 0.17, "h": 0.38, "forma": "elipse", "texto": "Pai", "escurecer": 0.6},
             {"x": 0.3, "y": 0.0, "w": 0.3, "h": 1.0, "texto": "Clara"},
             {"x": 0.0, "y": 0.3, "w": 0.05, "h": 0.1, "texto": "A avó"},
             {"x": 0.95, "y": 0.62, "w": 0.05, "h": 0.1, "texto": "Tiago"},
             {"x": 0.2, "y": 0.2, "w": 0.2, "h": 0.2},
             {"x": -0.1, "y": 0.9, "w": 0.3, "h": 0.3, "texto": "A mãe"},
             {"x": 0.4, "y": 0.4, "w": 0.1, "h": 0.1, "texto": "Os amigos todos do secundário e da faculdade, no Porto, em 2015"}]
    fotos = [[212.08, -20.94, 1495.85, 1121.89], [0.0, -250.0, 1920.0, 1580.0], [663.07, 101.14, 593.85, 877.71]]
    legendas = ["", "Com a Susana e com o Pai",
                "Uma legenda comprida que parte em várias linhas, para o teto do nome descer da faixa da legenda de "
                "baixo e o nome ir para cima da zona quando em baixo não couber, como no render."]
    tempos = [(4.0, 0.7, 0.7), (2.0, 0.7, 0.7), (6.0, 1.0, 0.7), (4.0, 0.0, 0.7)]
    instantes = [0.5, 1.15, 1.3, 2.4]
    casos, esperado, n = [], [], 0
    for corpo in (46, 60):
        avisos = []
        render.aplicar_estilo({"legenda": {"tamanho": corpo}} if corpo != render.LEGENDA_TAMANHO else None, avisos)
        try:
            larguras, linhas = {}, {}
            for leg in legendas:
                if leg:
                    tam, ls, _f = render.linhas_legenda(leg)
                    linhas[leg] = {"tam": tam, "linhas": ls}
            for zd in zonas:
                lido, _aviso = render.ler_destaque(json.dumps(zd))
                for leg in legendas:
                    for dur, entra, sai in tempos:
                        with contextlib.redirect_stdout(io.StringIO()):
                            d = render.preparar_destaque(lido, entra, sai, dur, leg, "")
                        if d["nome"] is not None:
                            larguras[zd["texto"]] = d["nome"].width - 2 * render.MARGEM
                        for foto in fotos:
                            for u in instantes:
                                alfa = render.destaque_alfa(d["janela"], u)
                                caixa = render.destaque_caixa(d, *foto)
                                e = None
                                if alfa > 0:
                                    e = {"alfa": alfa, "z": list(caixa) + [d["forma"]], "nome": None}
                                    if d["nome"] is not None:
                                        cx, cy = render.onde_vai_o_nome(d, caixa)
                                        altura, cima, baixo = d["nome_faixa"]
                                        e["nome"] = {"cx": cx, "ty": cy - (cima + altura + baixo) / 2.0 + cima,
                                                     "larg": larguras[zd["texto"]], "alt": altura}
                                casos.append({"corpo": corpo, "zd": zd, "x": leg, "seg": {"dur": dur, "entra": entra, "sai": sai},
                                              "u": u, "foto": foto})
                                esperado.append(e)
        finally:
            render.aplicar_estilo(None, [])
        casos_js = json.dumps(casos, ensure_ascii=False)
        prelude = """
var CORPO = 46, LARGURAS = %(larg)s, LINHAS = %(linhas)s;
function estiloValor(parte, chave){ return parte === "legenda" && chave === "tamanho" ? CORPO : null; }
function zdLarguraDoNome(t){ return LARGURAS[t]; }
function palcoLegendaLinhas(t){ return LINHAS[t]; }
""" % {"larg": json.dumps(larguras, ensure_ascii=False), "linhas": json.dumps(linhas, ensure_ascii=False)}
        js = """
var casos = %s, r = [];
casos.forEach(function(k){
  CORPO = k.corpo;
  var c = {t: "foto", zd: k.zd, x: k.x}, q = palcoDestaqueConta(c, k.seg, k.u, k.foto[0], k.foto[1], k.foto[2], k.foto[3]);
  r.push(q ? {alfa: q.alfa, z: q.z, nome: q.nome ? {cx: q.nome.cx, ty: q.nome.ty, larg: q.nome.larg, alt: q.nome.alt} : null} : null);
});
console.log(JSON.stringify(r));
""" % casos_js
        r = _correr_zd(FUNCOES_ZD_PALCO, prelude, js, problemas)
        if r is None:
            break
        if len(r) != len(casos):
            problemas.append("o palco devolveu %d contas para %d instantes" % (len(r), len(casos)))
        n += len(r)
        for k, (caso, e, p) in enumerate(zip(casos, esperado, r)):
            onde = "corpo %d, zona %s, legenda %d, tempos %s, foto %s, u %s" % (
                caso["corpo"], json.dumps(caso["zd"], ensure_ascii=False)[:40], legendas.index(caso["x"]),
                (caso["seg"]["dur"], caso["seg"]["entra"], caso["seg"]["sai"]), caso["foto"][:2], caso["u"])
            if (e is None) != (p is None):
                problemas.append("%s: o render %s e o palco %s" % (onde, "nao desenha" if e is None else "desenha",
                                                                   "nao desenha" if p is None else "desenha"))
                continue
            if e is None:
                continue
            if abs(e["alfa"] - p["alfa"]) > 1e-9:
                problemas.append("%s: alfa %.4f no render e %.4f no palco" % (onde, e["alfa"], p["alfa"]))
            if p["z"][4] != e["z"][4] or any(abs(a - b) > 1e-6 for a, b in zip(e["z"][:4], p["z"][:4])):
                problemas.append("%s: a zona %s no render e %s no palco" % (onde, e["z"], p["z"]))
            if (e["nome"] is None) != (p["nome"] is None):
                problemas.append("%s: o nome %s no render e %s no palco" % (onde, e["nome"], p["nome"]))
            elif e["nome"] is not None:
                if any(abs(e["nome"][q] - p["nome"][q]) > 1e-6 for q in ("cx", "ty", "larg", "alt")):
                    problemas.append("%s: o nome %s no render e %s no palco" % (
                        onde, {q: round(v, 3) for q, v in e["nome"].items()}, {q: round(v, 3) for q, v in p["nome"].items()}))
        casos, esperado = [], []
    verifica("Mesa: o destaque do palco como o render", not problemas, "; ".join(problemas[:3])[:500] if problemas else
             "alfa, zona e nome em %d instantes: por baixo, por cima, no teto, presos aos lados, com legenda e outro corpo" % n)



# ------------------------------------------------------------- a musica dos creditos (2 de outubro, a tarde)
# O Tiago, a 2 de outubro: "gostava de tambem poder alterar a musica que toca nos creditos, sendo que idealmente
# gostava de tambem a conseguir editar na propria Mesa ... gostava de voltar ao Taking care of business". O painel
# Creditos grava est.creditos.musica = {ficheiro, inicio} (contrato, seccao 6) e o palco toca-a. Aqui guarda-se que:
#  12. as contas da Mesa sao as do scripts/musica_creditos.py, que o render vai usar: o fim audivel, a escolha lida
#      como o escolha_valida(), a entrada (com o silencio do principio saltado) e o segundo depois do fim a valer «fim»;
#  13. a juncao que o palco toca e a do faixas_dos_creditos(): a que sai cruza 2,2 s, a nova sobe como o
#      render.subidas_e_descidas() a poe, a mesma musica no mesmo sitio continua, a 096 cala a que sai na cauda; e
#      sem a escolha o palco faz exatamente o de antes;
#  14. a escolha grava-se so quando existe, desfaz-se, sobrevive aos textos, a dois aparelhos e a uma Mesa antiga;
#  15. a Mesa montada traz onde cada musica se cala e sabe se o render ja le a escolha.
TCOB = "Bachman Turner Overdrive-Taking care of business_62s.mp3"
QUEEN = "Queen - Friends Will Be Friends (Lyrics).mp3"
CLAIR = "Gilbert O`Sullivan - CLAIR - ( The Sweetest `Clair ` video Ever !) - And Clair answers back !.mp3"
DECLARACOES_MUSICA = ["var SOM_R = "]
FUNCOES_MUSICA = ["function somR2(", "function somEfeito(", "function somPorIni(", "function somResolve(",
                  "function somSilencioNoInicio(", "function somEntraNumInicio(", "function somAtaque(",
                  "function somSonoridade(", "function nomeFaixa(", "function fmtS(",
                  "function credMusicaFim(", "function credMusicaNome(", "function credMusicaEscolha(",
                  "function credMusicaLista(", "function credMusicaEntrada(", "function credMusicaJuncao(",
                  "function credSemAcentos("]


def _correr_js(declaracoes, funcoes, prelude, corpo_js, problemas):
    """Corre no node as declaracoes e as funcoes da Mesa pedidas, com o `prelude` a fingir o resto da pagina."""
    html = io.open(EDITOR, encoding="utf-8").read()
    blocos = "\n".join([_declaracao(html, m, problemas) for m in declaracoes] + [_bloco(html, m, problemas) for m in funcoes])
    if problemas:
        return None
    programa = '"use strict";\n' + prelude + "\n" + blocos + "\n" + corpo_js
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        r = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(caminho)
    if r.returncode != 0:
        problemas.append("o node parou: " + " | ".join((r.stderr or r.stdout).strip().splitlines()[-3:])[:300])
        return None
    return json.loads(r.stdout)


def teste_musica_dos_creditos_conta_como_o_modulo():
    """O fim, a escolha e a entrada da Mesa sao os do scripts/musica_creditos.py.

    O DEFEITO QUE ISTO APANHA: a Mesa a dizer que a musica entra aos 121 s e o render a po-la aos 125, ou a Mesa a
    dizer que os Queen acabam 20 s antes quando se calam 26 s antes (a duracao do ficheiro em vez do fim audivel).
    A escolha "fim" depende do fim audivel ao centesimo, e ele vem do window.MUSICA_FIM, que o gerar_mesa faz com o
    para_a_mesa(); sem ele a Mesa refaz a mesma regra sobre o indice, e as duas tem de dar o mesmo nas 52 musicas.
    Um segundo depois de a musica se calar vale «fim» (contrato, seccao 6), e uma escolha mal escrita e «Como esta»
    nos dois lados.
    """
    if not shutil.which("node"):
        salta("Mesa: a musica dos creditos conta como o modulo", "sem node neste PC")
        return
    import musica_creditos as mc
    audio, _info = _som_da_mesa()
    if not audio or TCOB not in audio or QUEEN not in audio:
        salta("Mesa: a musica dos creditos conta como o modulo", "sem as copias do som do Taking Care of Business e dos Queen")
        return
    problemas = []
    musicas = {f: a for f, a in audio.items() if (a.get("tipo") or "musica") == "musica"}
    fim_modulo = {f: mc.fim_das_medidas(a.get("silencios") or [], a["duracao"]) for f, a in musicas.items()}
    escolhas = [None, {"ficheiro": TCOB}, {"ficheiro": TCOB, "inicio": "Inicio"}, {"ficheiro": TCOB, "inicio": " fim "},
                {"ficheiro": TCOB, "inicio": "12,5"}, {"ficheiro": TCOB, "inicio": 103}, {"ficheiro": TCOB, "inicio": "talvez"},
                {"ficheiro": TCOB, "inicio": -3}, {"ficheiro": TCOB, "inicio": None}, {"ficheiro": TCOB, "inicio": ""},
                {"inicio": "fim"}, {"ficheiro": "  "}, {}, "", []]
    casos = [(f, i, d) for f in (TCOB, QUEEN) for i in ("inicio", "fim", 0.0, 1.0, 60.8, 103.0, 118.72, 200.0)
             for d in (170.8, 179.9, 300.0)]
    corpo_js = """
var r = {fimPorto: {}, escolhas: [], entradas: [], nomes: {}, lista: null};
MUSICA_FIM = null;
Object.keys(AUDIO).forEach(function(f){ if((AUDIO[f].tipo || "musica") === "musica") r.fimPorto[f] = credMusicaFim(f); });
ESCOLHAS.forEach(function(m){ est = m === null ? {} : {creditos: {musica: m}}; r.escolhas.push(credMusicaEscolha()); });
MUSICA_FIM = MF;
CASOS.forEach(function(c){ r.entradas.push(credMusicaEntrada(c[0], c[1], c[2])); });
r.fora = credMusicaEntrada(TCOB_, 295.0, 170.8);
r.foraLimite = credMusicaEntrada(TCOB_, 291.814, 170.8);
NOMES.forEach(function(f){ r.nomes[f] = credMusicaNome(f); });
r.lista = credMusicaLista().map(function(m){ return m.f; });
console.log(JSON.stringify(r));
"""
    nomes = [TCOB, QUEEN, CLAIR, "Tokyo Drift - Teriyaki Boyz [ MUSIC VIDEO ] HD.mp3", "O Rei Leão (PT-PT) Ciclo Sem Fim.mp3"]
    prelude = ("var window = {};\nvar AUDIO = %s, AUDIO_INFO = null, MUSICA_FIM = null, est = {};\n"
               "var MF = %s, ESCOLHAS = %s, CASOS = %s, TCOB_ = %s, NOMES = %s;\n"
               % (json.dumps(audio, ensure_ascii=False), json.dumps(mc.para_a_mesa(audio), ensure_ascii=False),
                  json.dumps(escolhas, ensure_ascii=False), json.dumps(casos), json.dumps(TCOB), json.dumps(nomes, ensure_ascii=False)))
    r = _correr_js(DECLARACOES_MUSICA, FUNCOES_MUSICA, prelude, corpo_js, problemas)
    if r:
        # o fim: a regra da Mesa sem o MUSICA_FIM e a do modulo, em todas
        dif = [f for f in musicas if abs((r["fimPorto"].get(f) or -1) - fim_modulo[f]) > 0.0005]
        if dif:
            problemas.append("o fim pela regra da Mesa difere do do modulo em %d musicas: %s" % (len(dif), dif[:3]))
        if abs(fim_modulo[TCOB] - 291.814) > 0.001 or abs(fim_modulo[QUEEN] - 239.34) > 0.001:
            problemas.append("o fim do TCOB e dos Queen: %s e %s" % (fim_modulo[TCOB], fim_modulo[QUEEN]))
        # a escolha, como o escolha_valida()
        for m, mesa in zip(escolhas, r["escolhas"]):
            ok, erro = mc.escolha_valida(m)
            if ok is None and erro is None:
                bate = mesa is None
            elif ok is None:
                bate = bool(mesa and mesa.get("erro"))
            else:
                bate = bool(mesa) and not mesa.get("erro") and mesa.get("ficheiro") == ok["ficheiro"] and mesa.get("inicio") == ok["inicio"]
            if not bate:
                problemas.append("a escolha %r: Mesa %s, modulo %s" % (m, mesa, (ok, erro)))
        # a entrada, como o entrada(), com os silencios do indice
        for (f, ini, d), mesa in zip(casos, r["entradas"]):
            py = mc.entrada(ini, fim_modulo[f], d, audio[f].get("silencios") or [])
            for k in ("in_s", "toca", "falta", "saltou", "pedido"):
                if abs(mesa[k] - py[k]) > 0.006:
                    problemas.append("%s, %s, creditos de %s s: %s na Mesa %s, no modulo %s" % (f[:12], ini, d, k, mesa[k], py[k]))
                    break
        # o segundo depois de a musica se calar vale "fim"
        fim_e = mc.entrada("fim", fim_modulo[TCOB], 170.8, audio[TCOB]["silencios"])
        for nome_c in ("fora", "foraLimite"):
            if r[nome_c].get("fora") is None or abs(r[nome_c]["in_s"] - fim_e["in_s"]) > 0.006:
                problemas.append("o segundo %s (depois do fim) devia valer «fim» (%s): %s" % (nome_c, fim_e["in_s"], r[nome_c]))
        esperados = {TCOB: "Bachman Turner Overdrive - Taking care of business", QUEEN: "Queen - Friends Will Be Friends",
                     "Tokyo Drift - Teriyaki Boyz [ MUSIC VIDEO ] HD.mp3": "Tokyo Drift - Teriyaki Boyz",
                     "O Rei Leão (PT-PT) Ciclo Sem Fim.mp3": "O Rei Leão Ciclo Sem Fim"}
        for f, nome in esperados.items():
            if r["nomes"][f] != nome:
                problemas.append("o nome de %s saiu %r" % (f[:20], r["nomes"][f]))
        if " - - " in r["nomes"][CLAIR]:
            problemas.append("o nome do Clair ficou com dois tracos seguidos: %r" % r["nomes"][CLAIR])
        # sem os efeitos, e sem os sons que o projeto fez na pasta gerados (o andar da fita e o som do pedido; revisor
        # de 2 de outubro): o audio_para_mesa marca-os com `gerado`, e so a esses
        import montar_da_mesa
        gerados = os.path.normcase(os.path.normpath(montar_da_mesa.GERADOS))
        feitos = sorted(f for f, a in musicas.items() if a.get("gerado"))
        esperados_g = sorted(f for f, c in montar_da_mesa.caminhos_de_musica().items()
                             if f in musicas and os.path.normcase(os.path.dirname(os.path.normpath(c))) == gerados)
        if feitos != esperados_g or "fita_a_andar.wav" not in feitos or TCOB in feitos:
            problemas.append("o `gerado` do indice: %s, e os da pasta gerados sao %s" % (feitos, esperados_g))
        efeitos = [f for f in musicas if f.startswith(("Candidato a vereador", "rebobinar"))]
        fora = set(efeitos) | set(feitos)
        if sorted(r["lista"]) != sorted(f for f in musicas if f not in fora) or TCOB not in r["lista"]:
            problemas.append("a lista oferece %d musicas, e devia oferecer as %d sem os efeitos e sem os sons feitos pelo projeto"
                             % (len(r["lista"]), len(musicas) - len(fora)))
    verifica("Mesa: a musica dos creditos conta como o modulo", not problemas, "; ".join(problemas)[:400] if problemas else
             "o fim nas %d musicas, %d escolhas, %d entradas, o segundo depois do fim vale «fim», %d na lista"
             % (len(musicas), len(escolhas), len(casos), len(r["lista"])))


def teste_musica_dos_creditos_juncao_como_o_render():
    """O palco toca nos creditos a musica escolhida com a juncao do musica_creditos.faixas_dos_creditos().

    O DEFEITO QUE ISTO APANHA: a Mesa a deixar ouvir uma passagem que o render nao faz: outro instante de corte,
    outra subida (o Taking Care of Business "do inicio" entra num inicio e sobe em 0,03 s; "para acabar" entra a meio
    e sobe nos 2,2 s em que os Queen descem), a que sai sem o cruzamento ou sem a cauda da 096, a mesma musica no
    mesmo sitio cruzada consigo propria. E sem a escolha o palco tem de fazer exatamente o de antes, como o render.
    Compara-se o plano do palco (o filme montado, com os creditos) com as faixas que o modulo da ao render.
    """
    if not shutil.which("node"):
        salta("Mesa: a juncao dos creditos como o render", "sem node neste PC")
        return
    import musica_creditos as mc
    import palco_para_mesa
    import render
    import som_para_mesa
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    audio, info = _som_da_mesa()
    if not filme or not som or not audio or TCOB not in audio:
        salta("Mesa: a juncao dos creditos como o render", "sem a montagem ou sem as copias do som")
        return
    real_t, caminho_t = mc.resolver(TCOB)
    if not real_t:
        salta("Mesa: a juncao dos creditos como o render", "sem o Taking Care of Business em disco")
        return
    problemas = []
    est = _estado_montado()
    versao = [v for v in est["versoes"] if v["id"] == filme["versao"]][0]
    dur = 170.8
    escolhas = {"como": None, "fim": {"ficheiro": TCOB, "inicio": "fim"}, "inicio": {"ficheiro": TCOB, "inicio": "inicio"},
                "s103": {"ficheiro": TCOB, "inicio": 103}, "s250": {"ficheiro": TCOB, "inicio": 250.0},
                "fora": {"ficheiro": TCOB, "inicio": 400}, "sumiu": {"ficheiro": "Uma musica que ja nao esta.mp3", "inicio": "fim"}}
    corpo_js = """
var v = %(v)s, r = {};
CRED_FALSO = {dur: %(dur)s};
var limpa = function(p){ return p ? {f: p.f, ini: p.ini, "in": p["in"], dura: p.dura, cruza: p.cruza, subida: p.subida, descida: p.descida,
  curva: p.curva, gdb: p.gdb, url: p.url, creditos: !!p.creditos, credNova: !!p.credNova, sai_s: p.sai_s == null ? null : p.sai_s} : null; };
function corre(nome, m){
  est = m ? {creditos: {musica: m}} : {};
  var F = palcoFilme(v), sp = palcoSomPlano(F), J = sp.creditos;
  r[nome] = {ini: F.cred.ini, total: F.total, comoEsta: J.comoEsta, mesma: !!J.mesma, motivo: J.motivo || null, noCorte: J.noCorte,
             ult: limpa(J.ult), nova: limpa(sp.plano.filter(function(p){ return p.credNova; })[0]),
             assinatura: somAssinatura(sp.plano), notas: sp.notas, e: J.e || null};
}
var ESC = %(esc)s;
Object.keys(ESC).forEach(function(k){ corre(k, ESC[k]); });
/* a mesma musica no mesmo sitio: a ultima do filme a partir de onde o filme a deixa */
corre("mesma", {ficheiro: r.como.ult.f, inicio: r.como.noCorte});
/* a 096 medida para esta passagem (AUDIO_INFO.fins): a que sai acaba a frase e cala-se na cauda */
AUDIO_INFO.fins = (AUDIO_INFO.fins || []).concat([{sai: r.como.ult.f, entra: %(tcob)s, no_corte: r.como.noCorte, entra_in: r.fim.nova["in"],
                                                  sai_s: r.como.noCorte, cauda: 0.3, subida_entra: null}]);
corre("frase", ESC.fim);
console.log(JSON.stringify(r));
""" % {"v": json.dumps(versao, ensure_ascii=False), "dur": dur, "esc": json.dumps(escolhas, ensure_ascii=False), "tcob": json.dumps(TCOB)}
    r = _correr_palco({"filme": filme}, som, audio, corpo_js, problemas, info)
    if r:
        como = r["como"]
        ult = como["ult"]
        antes = 5.0
        pos = como["noCorte"] - antes
        ultima = {"ficheiro": ult["f"], "caminho": mc.resolver(ult["f"])[1], "quando": 0.0, "in_s": pos, "dura": 60.0,
                  "dura_medida": 60.0, "ganho": 1.0, "encontrado": "Sim", "cruza": 0.0, "_subida": 2.2}
        medidas = mc.medir(caminho_t)
        # sem escolha: o de antes (a ultima continua ate ao fim dos creditos ou do ficheiro), e nenhuma nova
        resta = audio[ult["f"]]["duracao"] - ult["in"]
        if (not como["comoEsta"] or como["nova"] or not ult["creditos"]
                or abs(ult["ini"] + ult["dura"] - min(como["total"], ult["ini"] + resta)) > 0.011 or ult["descida"] != 1.0):
            problemas.append("sem a escolha o palco nao faz o de antes: %s" % ult)
        if any(n.startswith("Nos créditos toca") for n in como["notas"]):
            problemas.append("sem a escolha o palco fala da musica escolhida")
        for nome_c in ("fim", "inicio", "s103", "s250", "fora"):
            x = r[nome_c]
            esc_py = dict(escolhas[nome_c])
            if nome_c == "fora":
                esc_py["inicio"] = "fim"          # o contrato: depois de a musica se calar vale «fim»
            feito = mc.faixas_dos_creditos(ultima, pos, antes, dur, esc_py, [], medidas, caminho_t)
            if not feito or x["comoEsta"] or not x["nova"]:
                problemas.append("%s: o modulo da %s e o palco comoEsta=%s" % (nome_c, bool(feito), x["comoEsta"]))
                continue
            (q, t), _inf = feito
            n, u = x["nova"], x["ult"]
            sub_py = t.get("subida") or (1.0 if t["quando"] > 0.05 else 0.4)
            des_q = q.get("descida") or max(1.0, q.get("cruza", 0.0))
            pares = (("o in da nova", n["in"], t["in_s"]), ("a duracao da nova", n["dura"], t["dura"]),
                     ("a subida da nova", n["subida"], sub_py), ("a descida da nova", n["descida"], t.get("descida") or 1.0),
                     ("o que a que sai toca depois do corte", u["ini"] + u["dura"] - x["ini"], q["dura"] - antes),
                     ("o cruzamento da que sai", u["cruza"], q.get("cruza", 0.0)), ("a descida da que sai", u["descida"], des_q))
            for nome_p, a, b in pares:
                if abs(a - b) > 0.011:
                    problemas.append("%s, %s: palco %.3f, modulo %.3f" % (nome_c, nome_p, a, b))
            if abs(n["ini"] - x["ini"]) > 1e-6:
                problemas.append("%s: a nova entra aos %.2f e os creditos comecam aos %.2f" % (nome_c, n["ini"], x["ini"]))
            if n["curva"] != t.get("curva") or u["curva"] != q.get("curva"):
                problemas.append("%s: as curvas %s/%s, no modulo %s/%s" % (nome_c, u["curva"], n["curva"], q.get("curva"), t.get("curva")))
            if not n["url"] or not os.path.exists(os.path.join(REPO, "saida", n["url"])):
                problemas.append("%s: sem a copia do Taking Care of Business (%s)" % (nome_c, n["url"]))
        if r["inicio"]["nova"] and r["inicio"]["nova"]["subida"] > 0.05:
            problemas.append("«do início» devia entrar num início, sem rampa")
        if r["fim"]["nova"] and abs(r["fim"]["nova"]["subida"] - render.CRUZAMENTO) > 0.011:
            problemas.append("«para acabar» entra a meio e devia subir nos %.1f s do cruzamento" % render.CRUZAMENTO)
        if not r["fora"]["e"] or r["fora"]["e"].get("fora") is None:
            problemas.append("o segundo 400 nao foi dito fora da musica")
        if not r["sumiu"]["comoEsta"] or r["sumiu"]["motivo"] != "sem_ficheiro" or r["sumiu"]["assinatura"] != como["assinatura"]:
            problemas.append("uma musica que ja nao esta na Mesa devia tocar como esta: %s" % r["sumiu"]["motivo"])
        me = r["mesma"]
        if not me["mesma"] or me["nova"] or not me["ult"]["creditos"] or me["ult"]["cruza"]:
            problemas.append("a mesma musica no mesmo sitio devia continuar sem se cruzar: %s" % me["ult"])
        fr = r["frase"]
        if not fr["nova"] or (abs(fr["ult"]["dura"] - (fr["ult"]["sai_s"] - fr["ult"]["in"] + 0.3)) > 0.011 or fr["ult"]["cruza"]
                              or abs(fr["ult"]["descida"] - 0.3) > 0.011 or abs(fr["nova"]["subida"] - 0.3) > 0.011):
            problemas.append("com a 096 medida: a que sai %s, a nova %s" % (fr["ult"], fr["nova"]))
        else:
            # e a 096 do modulo, com o mesmo fim de frase
            original = mc.fim_de_frase
            mc.fim_de_frase = lambda *a, **k: {"sai_s": como["noCorte"], "cauda": 0.3, "subida": None}
            try:
                (q, t), _inf = mc.faixas_dos_creditos(ultima, pos, antes, dur, escolhas["fim"], [], medidas, caminho_t)
            finally:
                mc.fim_de_frase = original
            if (abs((fr["ult"]["ini"] + fr["ult"]["dura"] - fr["ini"]) - (q["dura"] - antes)) > 0.011
                    or abs(fr["nova"]["subida"] - t["subida"]) > 0.011):
                problemas.append("a 096: palco %.3f s depois do corte e subida %.2f, modulo %.3f e %.2f"
                                 % (fr["ult"]["ini"] + fr["ult"]["dura"] - fr["ini"], fr["nova"]["subida"], q["dura"] - antes, t["subida"]))
        if not any("Nos créditos toca" in n for n in r["fim"]["notas"]):
            problemas.append("o palco nao diz que toca a musica escolhida: %s" % r["fim"]["notas"])
    verifica("Mesa: a juncao dos creditos como o render", not problemas, "; ".join(problemas)[:500] if problemas else
             "como esta igual ao de antes; fim, inicio, 103, 250 e fora iguais ao faixas_dos_creditos; a mesma continua; a 096; a que sumiu")


def teste_musica_dos_creditos_grava_desfaz_e_junta():
    """A escolha grava-se so quando existe, desfaz-se, e sobrevive aos textos, a dois aparelhos e a uma Mesa antiga.

    O DEFEITO QUE ISTO APANHA: a musica escolhida pelo Tiago a desaparecer quando a Clara muda um titulo noutro
    aparelho, quando ele carrega em «Repor os textos», ou quando um separador esquecido de uma Mesa antiga grava; ou
    o Anular a nao a tirar. E «Como está» tem de tirar a chave, para o render nao ver uma escolha que ninguem fez.
    """
    if not shutil.which("node"):
        salta("Mesa: a musica dos creditos grava, desfaz e junta", "sem node neste PC")
        return
    problemas = []
    funcoes = FUNCOES_JUNTAR + ["function credMusicaPoe(", "function credPoe(", "function credMudaTexto(", "function credRepor(",
                                "function credTextosMudados(", "function credOmissoes(", "function credCargo(",
                                "function credGrupoPorEtiqueta(", "function credGrupoTexto(", "function credMusicaEscolha("]
    funcoes = [f for i, f in enumerate(funcoes) if f not in funcoes[:i]]
    prelude = PRELUDE_JUNTAR + """
var CRED = {omissoes: {cargos: [{cargo: "C", quem: "Q"}], titulo: "TITULO", data: "DATA"}, grupos: []};
function credOuvirPara(){}
function credPintaMusica(){}
function credPintaAnular(){}
function credMsg(){}
"""
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}],
          "pessoas": [{"id": "p_c", "nome": "Creditos"}], "tags": {"f01": ["p_c"]}, "atual": "v1",
          "quando": "2026-10-02T10:00:00Z", "rev": 5, "pagina": "2026-10-02"}
    corpo_js = """
var r = {}, B0 = %(b0)s, M = {ficheiro: %(tcob)s, inicio: "fim"};
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
// A. escolher grava so a musica, e o Anular tira-a
abrir(B0); marcas = 0;
credGuardaDesfazer("escolher a música dos créditos"); credMusicaPoe(M);
r.A = {creditos: copia(est.creditos), corpo: copia(corpo().creditos), marcas: marcas, escolha: credMusicaEscolha(),
       partes: Object.keys(partesDe(corpo())).filter(function(k){ return k.indexOf("creditos") >= 0; })};
desfazer();
r.A.depois = est.creditos === undefined ? null : est.creditos;
// B. os textos nao lhe tocam: mudar um titulo, repor os textos
abrir(com({creditos: {musica: M}}));
credMudaTexto("titulo", "", "OUTRO"); r.B1 = copia(est.creditos);
credRepor(); r.B2 = copia(est.creditos);
// C. «Como está» tira a chave, e com ela os creditos que so a tinham
credMusicaPoe(null); r.C1 = est.creditos === undefined ? null : est.creditos;
abrir(com({creditos: {musica: M, titulo: "T"}})); credMusicaPoe(null); r.C2 = copia(est.creditos);
// D. dois aparelhos: aqui a musica, la um titulo; juntam-se
abrir(B0); credMusicaPoe(M);
var j = juntarComBase(com({creditos: {titulo: "LA"}, rev: 6}));
r.D = {ok: j.ok, meus: j.meus, deles: j.deles, creditos: copia(est.creditos)};
// E. os dois na musica, cada um a sua: conflito, e a pagina fica com a dela
abrir(B0); credMusicaPoe(M);
j = juntarComBase(com({creditos: {musica: {ficheiro: "Queen.mp3", inicio: "inicio"}}, rev: 6}));
r.E = {ok: j.ok, choque: j.choque, musica: est.creditos.musica};
// F. a musica veio do outro aparelho e aqui ninguem mexeu: entra
abrir(B0);
j = juntarComBase(com({creditos: {musica: M}, rev: 6}));
r.F = {ok: j.ok, deles: j.deles, musica: est.creditos && est.creditos.musica};
// G. uma Mesa antiga (sem pagina, nao conhece os creditos) grava sem eles: a musica volta a base
abrir(com({creditos: {musica: M}}));
var antiga = com({creditos: undefined, pagina: undefined, rev: 6}); antiga.versoes[0].clips.push({t: "foto", i: "f02"});
j = juntarComBase(antiga);
r.G = {ok: j.ok, repostos: j.repostos, musica: corpo().creditos && corpo().creditos.musica, clips: corpo().versoes[0].clips.length};
// H. uma Mesa de hoje que nao conhece a musica grava os creditos com ela (copia o est.creditos inteiro): nada muda
abrir(com({creditos: {musica: M}}));
j = juntarComBase(com({creditos: {musica: M, titulo: "DE HOJE"}, rev: 6}));
r.H = {ok: j.ok, deles: j.deles, creditos: copia(est.creditos)};
console.log(JSON.stringify(r));
""" % {"b0": json.dumps(B0), "tcob": json.dumps(TCOB)}
    r = _correr_js(DECLARACOES_JUNTAR, funcoes, prelude, corpo_js, problemas)
    if r:
        M = {"ficheiro": TCOB, "inicio": "fim"}
        A = r["A"]
        if A["creditos"] != {"musica": M} or A["corpo"] != {"musica": M} or not A["marcas"] or A["depois"] is not None:
            problemas.append("escolher e anular: %s" % A)
        if A["partes"] != ['["creditos","musica"]']:
            problemas.append("a musica nao e uma parte propria da juncao: %s" % A["partes"])
        if A["escolha"] != M:
            problemas.append("a escolha lida: %s" % A["escolha"])
        if r["B1"] != {"musica": M, "titulo": "OUTRO"} or r["B2"] != {"musica": M}:
            problemas.append("os textos mexeram na musica: %s, %s" % (r["B1"], r["B2"]))
        if r["C1"] is not None or r["C2"] != {"titulo": "T"}:
            problemas.append("«Como está» nao tirou so a musica: %s, %s" % (r["C1"], r["C2"]))
        D = r["D"]
        if not D["ok"] or D["creditos"] != {"musica": M, "titulo": "LA"}:
            problemas.append("musica aqui e titulo la: %s" % D)
        if r["E"]["ok"] or r["E"]["choque"] != ["creditos"] or r["E"]["musica"] != M:
            problemas.append("a musica nos dois: %s" % r["E"])
        if not r["F"]["ok"] or r["F"]["musica"] != M:
            problemas.append("a musica do outro aparelho: %s" % r["F"])
        if not r["G"]["ok"] or r["G"]["repostos"] != ["creditos"] or r["G"]["musica"] != M or r["G"]["clips"] != 2:
            problemas.append("a Mesa antiga: %s" % r["G"])
        if not r["H"]["ok"] or r["H"]["creditos"] != {"musica": M, "titulo": "DE HOJE"}:
            problemas.append("a Mesa de hoje: %s" % r["H"])
    verifica("Mesa: a musica dos creditos grava, desfaz e junta", not problemas, "; ".join(problemas)[:400] if problemas else
             "so quando existe, anular, textos, como esta, dois aparelhos (juntam e chocam), a Mesa antiga e a de hoje")


def teste_mesa_montada_traz_a_musica_dos_creditos():
    """A Mesa montada traz onde cada musica se cala, o painel da musica, e sabe se o render ja le a escolha.

    O DEFEITO QUE ISTO APANHA: o gerar_mesa sem o window.MUSICA_FIM (a Mesa contava pelo indice, mas um ficheiro
    medido de outra maneira dava outro «para acabar»), um fim que nao e o medido no original, e a Mesa a dizer que o
    render ja toca a musica escolhida quando o ponto5 ainda nao a le (ou o contrario, depois de ele a ler). A
    publicacao nao ganha ficheiros: as copias do som ja la estao.
    """
    import gerar_mesa
    import musica_creditos as mc
    problemas = []
    html = _montar_mesa_a_parte("mesa_musica_")
    m = re.search(r"window\.MUSICA_FIM = (.*?);\n", html)
    mf = json.loads(m.group(1)) if m else None
    a = re.search(r"window\.AUDIO = (.*?);\n", html)
    audio = json.loads(a.group(1)) if a else None
    if audio is None:
        salta("Mesa: a Mesa montada traz a musica dos creditos", "Mesa montada sem o som")
        return
    musicas = [f for f, x in audio.items() if (x.get("tipo") or "musica") == "musica"]
    if not mf or sorted(mf) != sorted(musicas):
        problemas.append("o window.MUSICA_FIM tem %s musicas e o window.AUDIO %d" % (len(mf) if mf else "nenhuma", len(musicas)))
    else:
        for f, esperado in ((TCOB, 291.814), (QUEEN, 239.34)):
            if f in mf and abs(mf[f]["fim"] - esperado) > 0.01:
                problemas.append("%s cala-se aos %s na Mesa, e aos %s medido" % (f[:20], mf[f]["fim"], esperado))
            real, caminho = mc.resolver(f)
            if real and f in mf and abs(mc.fim_audivel(caminho) - mf[f]["fim"]) > 0.01:
                problemas.append("o fim de %s na Mesa nao e o do original" % f[:20])
        if not (mf.get(TCOB) or {}).get("frases"):
            problemas.append("o Taking Care of Business vem sem as frases medidas")
        if (mf.get(TCOB) or {}).get("acaba") != "a desvanecer":
            problemas.append("o Taking Care of Business devia acabar a desvanecer")
    le = re.findall(r"window\.RENDER_LE = (\{.*?\});", html)
    le = json.loads(le[0]) if le else {}
    texto5 = io.open(PONTO5, encoding="utf-8").read()
    if le.get("creditos_musica") is not gerar_mesa.le_a_musica_dos_creditos(texto5):
        problemas.append("o RENDER_LE.creditos_musica (%s) nao e o que o ponto5 faz" % le.get("creditos_musica"))
    for texto, esperado in (("feito = musica_creditos.faixas_dos_creditos(ultima, pos, antes, dur, esc, avisos)", True),
                            ("(leitura[0].get(\"creditos\") or {}).get(\"musica\")", True),
                            ("escolha = cr['musica']", True),
                            ("# a musica do fim continua de onde o filme a deixa", False),
                            ("musica = ultima['ficheiro']", False)):
        if gerar_mesa.le_a_musica_dos_creditos(texto) is not esperado:
            problemas.append("le_a_musica_dos_creditos(%r) devia dar %s" % (texto[:40], esperado))
    for marca in ('id="credMusica"', 'data-caba="musica"', 'id="credOuvirEntrada"', 'id="credOuvirFim"', 'id="credOuvirTudo"'):
        if html.count(marca) != 1:
            problemas.append("a Mesa montada tem %d vezes %s" % (html.count(marca), marca))
    falta_copia = [f for f in musicas if not os.path.exists(os.path.join(REPO, "saida", audio[f].get("url") or "nada"))]
    if falta_copia:
        problemas.append("%d musicas sem copia em saida/audio: %s" % (len(falta_copia), falta_copia[:2]))
    verifica("Mesa: a Mesa montada traz a musica dos creditos", not problemas, "; ".join(problemas)[:400] if problemas else
             "%d musicas com o fim (%.1f KB, 0 ficheiros novos), o original confere, o render %s le a escolha"
             % (len(musicas), len(m.group(1).encode("utf-8")) / 1024.0 if m else 0, "ja" if le.get("creditos_musica") else "ainda nao"))


def teste_musica_dos_creditos_procura_larga_o_cursor():
    """Escolher uma musica com o cursor na procura pinta o painel de novo, e o Enter escolhe a primeira que se ve.

    O DEFEITO QUE ISTO APANHA (revisor de 2 de outubro): o Enter na procura gravava a primeira musica, mas o painel
    ficava em «escolhe na lista», com a lista aberta e sem o «Começa», porque o credPintaMusica() nao refaz os campos
    enquanto o cursor esta num campo da musica (para nao o tirar a quem escreve). No Safari um toque num botao tambem
    deixa o cursor na procura. Agora o credMusicaEscolhe() e o credMusicaModo() tiram-lhe o cursor antes de mudar.
    """
    if not shutil.which("node"):
        salta("Mesa: a procura larga o cursor", "sem node neste PC")
        return
    problemas = []
    prelude = """
var procura = {id: "credMusProcura", blur: function(){ if(document.activeElement === procura) document.activeElement = null; }};
var trocar = {focado: false, focus: function(){ document.activeElement = trocar; trocar.focado = true; }};
var document = {activeElement: null, getElementById: function(id){ return id === "credMusProcura" ? procura : null; },
                querySelector: function(q){ return /data-cmtrocar/.test(q) ? trocar : /credMusLista/.test(q) ? primeira : null; }};
var primeira = {getAttribute: function(){ return "B.mp3"; }};
var window = {matchMedia: null};
var est = {creditos: {musica: {ficheiro: "A.mp3", inicio: "inicio"}}}, credMusModo = "outra", credMusListaAberta = true;
var pintou = [], poe = [], msgs = [], desfazer = [];
function credMusicaEscolha(){ var m = est.creditos && est.creditos.musica; return m ? {ficheiro: m.ficheiro, inicio: m.inicio} : null; }
function credGuardaDesfazer(t){ desfazer.push(t); }
function credMusicaPoe(m){ poe.push({m: m, cursorNaProcura: document.activeElement === procura}); if(m) est.creditos = {musica: m}; else est.creditos = {}; credPintaMusica(); }
function credPintaMusica(){ pintou.push({cursorNaProcura: document.activeElement === procura, lista: credMusListaAberta}); }
function credMsg(t){ msgs.push(t); }
function credMusicaNome(f){ return f; }
"""
    corpo_js = """
var r = {};
document.activeElement = procura;
credMusicaEscolhe("B.mp3");
r.escolhe = {poe: poe.slice(), pintou: pintou.slice(), lista: credMusListaAberta, modo: credMusModo, desfazer: desfazer.slice()};
poe.length = 0; pintou.length = 0;
document.activeElement = procura;
credMusicaModo("como");
r.como = {poe: poe.slice(), pintou: pintou.slice()};
poe.length = 0; pintou.length = 0; est = {creditos: {}};
document.activeElement = procura;
credMusicaModo("como");
r.comoSemEscolha = {poe: poe.length, pintou: pintou.slice()};
console.log(JSON.stringify(r));
"""
    r = _correr_js([], ["function credMusLargaProcura(", "function credMusicaModo(", "function credMusicaEscolhe("],
                   prelude, corpo_js, problemas)
    if r:
        e = r["escolhe"]
        if not (len(e["poe"]) == 1 and e["poe"][0]["m"] == {"ficheiro": "B.mp3", "inicio": "inicio"} and not e["poe"][0]["cursorNaProcura"]
                and e["pintou"] and not any(x["cursorNaProcura"] for x in e["pintou"]) and e["lista"] is False and e["modo"] is None):
            problemas.append("escolher com o cursor na procura: %s" % e)
        if not (len(r["como"]["poe"]) == 1 and r["como"]["poe"][0]["m"] is None and not r["como"]["poe"][0]["cursorNaProcura"]):
            problemas.append("«Como está» com o cursor na procura: %s" % r["como"])
        if r["comoSemEscolha"]["poe"] or not r["comoSemEscolha"]["pintou"] or r["comoSemEscolha"]["pintou"][0]["cursorNaProcura"]:
            problemas.append("«Como está» sem escolha: %s" % r["comoSemEscolha"])
    html = io.open(EDITOR, encoding="utf-8").read()
    k = html.find('e.target.id === "credMusProcura" && e.key === "Enter"')
    trecho = html[k:k + 600] if k >= 0 else ""
    if not trecho or "credMusicaEscolhe(" not in trecho or "data-cmtrocar" not in trecho:
        problemas.append("o Enter na procura ja nao escolhe a primeira nem passa o foco ao «Trocar de música»")
    verifica("Mesa: a procura larga o cursor", not problemas, "; ".join(problemas)[:400] if problemas else
             "a escolha e o «Como está» pintam o painel sem o cursor na procura, e o Enter escolhe a primeira")


# ------------------------------------------------- a passagem no corte dos creditos (2 de outubro, a noite)
# O Tiago escolheu a (C) as 18:47 ("c"): alongar o ultimo clip do filme para o corte dos creditos cair no fim de uma
# frase da musica que sai, e a imagem e a musica mudarem juntas. A aba Musica dos creditos diz em que segundo do
# ficheiro esta a musica do fim do filme no corte, se o corte cai a meio de uma frase, e quanto falta ao ultimo clip
# (qual) para cair no fim da frase mais perto; avisa e nunca corrige (083). Aqui guarda-se que:
#  16. os fins de linha da voz sao a conta do scripts/discussao/juncao_creditos.py (as pausas iguais, e nos Queen aos
#      68,70 s a linha acaba aos 71,28 s), e as zonas e o que falta sao os do musica_creditos.py nos dois lados;
#  17. no palco, com a montagem e com a leitura dele, o que falta poe o corte no fim da frase quando ele muda a
#      duracao, a Mesa nao muda a versao, e sem passagem nao diz nada;
#  18. a chave passagem que venha na base nao se perde quando a Mesa grava a musica, e «Como está» tira tudo;
#  19. a Mesa montada traz os fins de linha (0 ficheiros novos), e o {} sem ficheiro avisa nos dois lados.
FUNCOES_PASSAGEM = ["function credMusicaZonas(", "function credMusicaOndeCai(", "function credS2(", "function credMusicaDuracaoPara(",
                    "function credMusicaClipNaFrase(", "function credMusicaPassagem(", "function credMusicaPassagemHtml(",
                    "function credMusicaNome(", "function nomeDoClip("]
DECLARACOES_PASSAGEM = ["var CRED_PASSAGEM = "]
# a janela do juncao_creditos.main() a volta do corte (nc - 3,0 a nc + 4,5), escrita la dentro do main
JANELA_DO_JUNCAO = (3.0, 4.5)


def _linhas_guardadas(nomes):
    """Os fins de linha que o gerar_mesa poe na pagina, so lidos do que esta guardado (sem medir nada)."""
    import contextlib
    import montar_da_mesa      # noqa: F401 - antes do redirect: ele mexe no sys.stdout ao ser importado
    import musica_creditos as mc
    with contextlib.redirect_stdout(io.StringIO()):
        return mc.linhas_para_a_mesa(nomes, fazer=False)


def teste_passagem_fins_de_linha_como_o_juncao():
    """Os fins de linha da voz da Mesa sao os do scripts/discussao/juncao_creditos.py, e as zonas as do modulo.

    O DEFEITO QUE ISTO APANHA: a Mesa a dizer que a frase dos Queen acaba noutro sitio do que o juncao_creditos.py diz
    (a conta das pausas copiada com um limiar trocado, ou o ficheiro inteiro a dar outra coisa do que a janela a volta
    do corte), o guardado em saida/audio/fins_de_linha.json a nao ser o que a conta da hoje, ou as zonas a aceitarem
    um corte a meio de uma linha. Os numeros de 2 de outubro: com a Mesa de hoje os Queen estao aos 68,70 s no corte,
    a linha acaba aos 71,28 s (a batida que a fecha aos 71,35 e a linha nova aos 72,16), e a equipa do render escolheu
    os 71,42 s, que tem de contar como fim de frase; os 95,00 s do filme de 1/10 caem numa pausa (94,95 a 95,22), e os
    97,50 s sao a linha verificada t713.
    """
    import musica_creditos as mc
    real, caminho = mc.resolver(QUEEN)
    if not real:
        salta("Mesa: os fins de linha como o juncao_creditos", "sem os Queen em disco")
        return
    sys.path.insert(0, os.path.join(REPO, "scripts", "discussao"))
    import juncao_creditos as jc
    problemas = []
    if (mc.LINHA_ANTES, mc.LINHA_DEPOIS) != JANELA_DO_JUNCAO or "nc - 3.0, nc + 4.5" not in io.open(jc.__file__, encoding="utf-8").read():
        problemas.append("a janela do modulo (%s, %s) nao e a do juncao_creditos.main()" % (mc.LINHA_ANTES, mc.LINHA_DEPOIS))
    for nome, a, b in (("PAUSA_DB", jc.PAUSA_DB, mc.LINHA_PAUSA_DB), ("PAUSA_MIN_S", jc.PAUSA_MIN_S, mc.LINHA_PAUSA_MIN_S),
                       ("LINHA_DB", jc.LINHA_DB, mc.LINHA_NOVA_DB), ("SR", jc.SR, mc.LINHA_SR)):
        if a != b:
            problemas.append("o %s do juncao (%s) nao e o do modulo (%s)" % (nome, a, b))
    t, voz = mc.envelope_da_voz(mc._ler_estereo(caminho))
    cortes = (68.70, 71.28, 71.42, 95.0, 97.5, 30.0, 150.0, 200.33, 5.0, 240.0)
    for nc in cortes:
        if jc.pausas(t, voz, nc - 3.0, nc + 4.5) != mc.pausas_da_voz(t, voz, nc - mc.LINHA_ANTES, nc + mc.LINHA_DEPOIS):
            problemas.append("as pausas aos %.2f s nao sao as do juncao_creditos" % nc)
    # a voz de uma trama e a mesma no ficheiro inteiro e na janela do juncao (o mesmo envelope, aos pedacos)
    x = mc._ler_estereo(caminho)[int(60 * mc.LINHA_SR):int(80 * mc.LINHA_SR)]
    tj, _tot, vj = jc.envelope(x, 60.0)
    tm, vm = mc.envelope_da_voz(x, 60.0)
    if len(tj) != len(tm) or float(abs(vj - vm).max()) > 1e-6:
        problemas.append("o envelope da voz aos pedacos nao e o do juncao")
    # a leitura do proprio juncao, a volta do corte de 2 de outubro: a primeira pausa depois dele
    xx = jc.ler(caminho, 68.70 - 3.0, 68.70 + 4.6)
    tt, _, vv = jc.envelope(xx, 68.70 - 3.0)
    dele = [p for p in jc.pausas(tt, vv, 68.70 - 3.0, 68.70 + 4.5)[0] if p[0] > 68.70][:1]
    linhas = mc.fins_de_linha_da_voz(t, voz)
    guardadas = _linhas_guardadas([QUEEN]).get(QUEEN)
    if guardadas is None:
        problemas.append("os fins de linha dos Queen nao estao guardados (corre o gerar_mesa.py)")
    elif guardadas != [[y[0], y[2]] for y in linhas]:
        problemas.append("o guardado em saida/audio/fins_de_linha.json nao e o que a conta da hoje")
    minha = [y for y in linhas if y[0] > 68.70][:1]
    if not dele or not minha or abs(dele[0][0] - minha[0][0]) > 0.02 or abs(dele[0][2] - minha[0][2]) > 0.02 \
            or abs(minha[0][0] - 71.28) > 0.02 or abs(minha[0][2] - 72.16) > 0.02:
        problemas.append("a linha depois dos 68,70: juncao %s, Mesa %s" % (dele, minha))
    # as zonas e o que falta, no modulo
    import audio_para_mesa
    fins = audio_para_mesa.fins_de_frase()
    Z = mc.zonas_de_frase(real, linhas, fins, mc.frases_medidas(real))
    esperado = {68.70: ("depois", 71.28, 2.58), 71.28: ("certo", 71.28, None), 71.42: ("certo", 71.28, None),
                71.80: ("certo", 71.43, None), 95.00: ("certo", 94.95, None), 97.50: ("certo", 97.5, None),
                72.20: ("depois", 72.35, 0.15), 93.00: ("depois", 94.95, 1.95),
                71.20: ("depois", 71.28, 0.08), 71.25: ("certo", 71.28, None)}
    # O COMECO DA ZONA DA VOZ E O DO juncao_creditos.propostas() (p[0] - 0.05; o revisor da paridade, 2 de outubro a noite:
    # a Mesa comecava 0,1 s antes e dava por certo um corte que o juncao dava "a meio de uma linha"). 0,08 s antes de a voz
    # se calar os dois dizem a meio; 0,03 s antes, os dois dizem que o corte cai na pausa.
    for nc, dentro in ((71.20, False), (71.25, True)):
        xj = jc.ler(caminho, nc - 3.0, nc + 4.6)
        tj2, _t2, vj2 = jc.envelope(xj, nc - 3.0)
        _fora, dizer = jc.propostas(nc, jc.pausas(tj2, vj2, nc - 3.0, nc + 4.5)[0])
        no_juncao, na_mesa = "numa pausa" in dizer[0], mc.onde_cai(nc, Z)["certo"] is not None
        if no_juncao != dentro or na_mesa != dentro:
            problemas.append("aos %.2f s o juncao diz %r e o modulo %s" % (nc, dizer[0][:60], "certo" if na_mesa else "a meio"))
    for nc, (onde, fim, falta) in sorted(esperado.items()):
        o = mc.onde_cai(nc, Z)
        z = o["certo"] if onde == "certo" else (o["depois"] or {}).get("zona")
        if onde == "depois" and o["certo"]:
            problemas.append("aos %.2f s o corte nao esta no fim de uma frase, e o modulo diz que esta (%s)" % (nc, o["certo"]))
        if not z or abs(z["fim"] - fim) > 0.011 or (falta is not None and abs(o["depois"]["falta"] - falta) > 0.011):
            problemas.append("aos %.2f s: %s, esperado %s %s %s" % (nc, o, onde, fim, falta))
    if not any(z["tipo"] == "verificada" and z["fim"] == 97.5 for z in Z) or any(z["tipo"] == "batida" for z in Z):
        problemas.append("os Queen: a t713 verificada e nenhuma batida (tem a voz): %s" % [z for z in Z if z["tipo"] != "voz"][:3])
    so_batida = mc.zonas_de_frase(real, [], [], mc.frases_medidas(real))
    if not so_batida or any(z["tipo"] != "batida" for z in so_batida) or not any(abs(z["fim"] - 69.73) < 0.01 for z in so_batida):
        problemas.append("sem a voz, as batidas da 095: %s" % so_batida[12:14])
    verifica("Mesa: os fins de linha como o juncao_creditos", not problemas, "; ".join(problemas)[:400] if problemas else
             "as pausas iguais em %d cortes, a linha depois dos 68,70 acaba aos %.2f (nova aos %.2f), %d fins nos Queen "
             "guardados como a conta, %d cortes nas zonas certas" % (len(cortes), minha[0][0], minha[0][2], len(linhas), len(esperado)))


def teste_passagem_da_mesa_como_o_modulo():
    """As zonas e o que falta da Mesa (credMusicaZonas, credMusicaOndeCai) sao os do musica_creditos.py.

    O DEFEITO QUE ISTO APANHA: a Mesa a dizer «está certo» num corte que o modulo poe a meio de uma frase, ou a contar
    o que falta a outra frase (uma zona da voz que cai dentro de uma verificada, as batidas usadas numa musica cantada,
    a linha nova lida do sitio errado do par que a pagina recebe).
    """
    if not shutil.which("node"):
        salta("Mesa: a passagem conta como o modulo", "sem node neste PC")
        return
    import musica_creditos as mc
    import audio_para_mesa
    problemas = []
    fins = audio_para_mesa.fins_de_frase()
    linhas = _linhas_guardadas([QUEEN, TCOB])
    if not linhas.get(QUEEN):
        salta("Mesa: a passagem conta como o modulo", "sem os fins de linha dos Queen guardados")
        return
    mf = {QUEEN: {"linhas": linhas[QUEEN], "frases": [list(x) for x in mc.frases_medidas(QUEEN)]},
          TCOB: {"linhas": linhas.get(TCOB) or [], "frases": [list(x) for x in mc.frases_medidas(TCOB)]},
          "Sem voz.mp3": {"frases": [[10.0, 0.5], [14.2, 0.3], [20.0, 0.9]]},
          "Nada.mp3": {}}
    fins = fins + [{"sai": "Sem voz.mp3", "sai_s": 14.25, "entra": "x", "no_corte": 14.25, "entra_in": 0, "cauda": 0.3}]
    cortes = {}
    for f in mf:
        pontos = [round(0.37 * k, 3) for k in range(0, 700)]
        for z in mc.zonas_de_frase(f, mf[f].get("linhas"), fins, mf[f].get("frases"))[:40]:
            pontos += [round(z["de"] - 0.002, 3), round(z["de"] + 0.002, 3), round(z["ate"] - 0.002, 3),
                       round(z["ate"] + 0.002, 3), z["fim"]]
        cortes[f] = pontos
    corpo_js = """
var r = {};
Object.keys(CORTES).forEach(function(f){
  var Z = credMusicaZonas(f);
  r[f] = {zonas: Z, onde: CORTES[f].map(function(nc){ var o = credMusicaOndeCai(nc, Z);
    return [o.certo ? o.certo.fim : null, o.depois ? [o.depois.zona.fim, o.depois.falta] : null, o.antes ? [o.antes.zona.fim, o.antes.falta] : null]; })};
});
console.log(JSON.stringify(r));
"""
    prelude = ("var AUDIO_INFO = {fins: %s}, MUSICA_FIM = %s, CORTES = %s;\nfunction somR2(x){ return Math.round(x * 100) / 100; }\n"
               % (json.dumps(fins, ensure_ascii=False), json.dumps(mf, ensure_ascii=False), json.dumps(cortes, ensure_ascii=False)))
    r = _correr_js(DECLARACOES_PASSAGEM, ["function credMusicaZonas(", "function credMusicaOndeCai("], prelude, corpo_js, problemas)
    n = 0

    def perto(a, b):
        if a is None or b is None:
            return a is None and b is None
        if isinstance(a, list):
            return all(abs(x - y) <= 0.0105 for x, y in zip(a, b))
        return abs(a - b) <= 0.0105
    if r:
        for f in mf:
            Z = mc.zonas_de_frase(f, mf[f].get("linhas"), fins, mf[f].get("frases"))
            zm = r[f]["zonas"]
            if len(Z) != len(zm) or any(abs(a[k] - b[k]) > 0.0005 for a, b in zip(Z, zm) for k in ("de", "ate", "fim")) \
                    or any(a["tipo"] != b["tipo"] for a, b in zip(Z, zm)):
                problemas.append("%s: %d zonas no modulo, %d na Mesa" % (f[:20], len(Z), len(zm)))
                continue
            for nc, mesa in zip(cortes[f], r[f]["onde"]):
                o = mc.onde_cai(nc, Z)
                py = [o["certo"]["fim"] if o["certo"] else None,
                      [o["depois"]["zona"]["fim"], o["depois"]["falta"]] if o["depois"] else None,
                      [o["antes"]["zona"]["fim"], o["antes"]["falta"]] if o["antes"] else None]
                n += 1
                if not all(perto(a, b) for a, b in zip(py, mesa)):
                    problemas.append("%s aos %.3f s: modulo %s, Mesa %s" % (f[:12], nc, py, mesa))
                    break
        tipos = {f: sorted(set(z["tipo"] for z in r[f]["zonas"])) for f in mf}
        if tipos[QUEEN] != ["verificada", "voz"] or tipos["Sem voz.mp3"] != ["batida", "verificada"] or tipos["Nada.mp3"]:
            problemas.append("os tipos das zonas: %s" % tipos)
        if any(z["fim"] == 14.2 for z in r["Sem voz.mp3"]["zonas"]):
            problemas.append("a batida dos 14,2 s cai dentro da verificada dos 14,25 e nao devia contar duas vezes")
    verifica("Mesa: a passagem conta como o modulo", not problemas, "; ".join(problemas)[:400] if problemas else
             "%d cortes em 4 musicas (voz e verificada, so batidas, nada): as mesmas zonas, o certo, o depois e o antes" % n)


def _passagem_no_palco(versoes, mf, escolha, problemas, dur=179.88, sem_fins=False):
    """Corre a passagem do palco (credMusicaPassagem sobre o palcoFilme e o palcoSomPlano) com a montagem, para cada
    versao de `versoes` ({nome: versao}); de cada uma, tambem a passagem depois de por a duracao que ela pede."""
    import palco_para_mesa
    import som_para_mesa
    filme = palco_para_mesa.linhas_do_filme()
    som = som_para_mesa.som_para_mesa()
    audio, info = _som_da_mesa()
    if not filme or not som or not audio:
        return None
    html = io.open(EDITOR, encoding="utf-8").read()
    # OS PROBLEMAS DESTA CORRIDA A PARTE: o _correr_palco nao corre nada com a lista ja cheia, e um caso que falhou antes
    # calava os seguintes
    meus = []
    extra = "\n".join([_declaracao(html, m, meus) for m in DECLARACOES_PASSAGEM] +
                      [_bloco(html, m, meus) for m in FUNCOES_PASSAGEM])
    corpo_js = """
var porId = {}, MARCAS = 0;
function esc(s){ return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
function versaoAtual(){ return null; }
function marcar(){ MARCAS++; }
%(extra)s
var VS = %(vs)s, r = {};
MUSICA_FIM = %(mf)s; CRED_FALSO = {dur: %(dur)s};
if(%(sem_fins)s) AUDIO_INFO = Object.assign({}, AUDIO_INFO, {fins: []});
est = {creditos: {musica: %(esc)s}};
if(%(esc)s === null) est = {};
function conta(v){ var F = palcoFilme(v), sp = palcoSomPlano(F); return {v: v, F: F, J: sp.creditos, plano: sp.plano}; }
function resumo(P){ return P ? JSON.parse(JSON.stringify({noCorte: P.noCorte, onde: P.onde, clip: P.clip, n: P.zonas.length, medida: P.medida})) : null; }
Object.keys(VS).forEach(function(k){
  var v = VS[k], antes = JSON.stringify(v), C = conta(v), P = credMusicaPassagem(C);
  r[k] = {P: resumo(P), html: credMusicaPassagemHtml(P), mudou: JSON.stringify(v) !== antes, marcas: MARCAS};
  ["depois", "antes"].forEach(function(q){
    var o = P && P.onde[q];
    if(!o || !P.clip) return;
    var w = JSON.parse(antes); w.clips[P.clip.i].d = o.d;
    var C2 = conta(w), P2 = credMusicaPassagem(C2);
    r[k][q] = {P: resumo(P2), html: credMusicaPassagemHtml(P2), sai: C2.J.sai || null, ult: C2.J.ult ? {ini: C2.J.ult.ini, f: C2.J.ult.f} : null,
               ini: C2.J.ini};
  });
});
console.log(JSON.stringify(r));
""" % {"extra": extra, "vs": json.dumps(versoes, ensure_ascii=False), "mf": json.dumps(mf, ensure_ascii=False), "dur": dur,
       "esc": json.dumps(escolha, ensure_ascii=False), "sem_fins": "true" if sem_fins else "false"}
    r = None if meus else _correr_palco({"filme": filme}, som, audio, corpo_js, meus, info)
    problemas.extend(meus)
    return r


def teste_passagem_no_palco_e_o_que_falta():
    """No palco, a duracao que a Mesa pede poe o corte no fim da frase; a Mesa nao muda nada; sem passagem nao diz nada.

    O DEFEITO QUE ISTO APANHA: a Mesa a pedir uma duracao que nao chega ao fim da frase (o corte nao anda com o ultimo
    clip como se conta, uma fita parada, o clip errado), a mudar a versao dele ao fazer as contas (083), a oferecer um
    encurtar que deixa a foto abaixo dos 3 s, ou a falar da passagem em «Como está», na mesma musica no mesmo sitio, ou
    numa escolha mal escrita. Com a montagem (o filme de 1/10, corte aos 95,00 s, numa pausa) e com a leitura de 2 de
    outubro (68,70 s, faltam 2,58 s, de 4 s para 6,58 s), como o Tiago a vai abrir.
    """
    if not shutil.which("node"):
        salta("Mesa: a passagem no palco e o que falta", "sem node neste PC")
        return
    import palco_para_mesa
    import musica_creditos as mc
    problemas = []
    filme = palco_para_mesa.linhas_do_filme()
    linhas = _linhas_guardadas([QUEEN])
    if not filme or not linhas.get(QUEEN):
        salta("Mesa: a passagem no palco e o que falta", "sem a montagem ou sem os fins de linha dos Queen")
        return
    est = _estado_montado()
    v = [x for x in est["versoes"] if x["id"] == filme["versao"]][0]
    ult = len(v["clips"]) - 1
    d0 = float(v["clips"][ult]["d"])
    versoes = {"montagem": v}
    for nome, mais in (("menos2", -2.0), ("mais1", 1.0)):
        w = json.loads(json.dumps(v))
        w["clips"][ult]["d"] = d0 + mais
        versoes[nome] = w
    leitura = os.path.join(REPO, "saida", "leitura_mesa_64", "montagem", "estado2.json")
    if os.path.exists(leitura):
        e64 = json.load(io.open(leitura, encoding="utf-8"))
        versoes["leitura64"] = [x for x in e64["versoes"] if x["id"] == filme["versao"]][0]
    mf = {QUEEN: {"fim": 239.34, "linhas": linhas[QUEEN], "frases": [list(x) for x in mc.frases_medidas(QUEEN)]}}
    M = {"ficheiro": TCOB, "inicio": "fim"}
    r = _passagem_no_palco(versoes, mf, M, problemas)
    if r is None and not problemas:
        salta("Mesa: a passagem no palco e o que falta", "sem a montagem ou sem as copias do som")
        return
    if r:
        for k, x in r.items():
            if x["mudou"] or x["marcas"]:
                problemas.append("%s: as contas da passagem mudaram a versao ou marcaram uma mudanca" % k)
            if not x["P"]:
                problemas.append("%s: com o Taking Care of Business nos creditos a Mesa nao diz a passagem" % k)
                continue
            for q in ("depois", "antes"):
                y = x.get(q)
                if not y:
                    continue
                o = x["P"]["onde"][q]
                if not y["P"] or not y["P"]["onde"]["certo"] or abs(y["P"]["noCorte"] - o["zona"]["fim"]) > 0.011:
                    problemas.append("%s: com %s s no ultimo clip (%s) o corte devia cair aos %s, e cai aos %s" % (
                        k, o["d"], q, o["zona"]["fim"], y["P"] and y["P"]["noCorte"]))
                elif "está certo" not in y["html"] or "data-cmclip" in y["html"]:
                    problemas.append("%s: depois de mudar a duracao (%s) a Mesa nao diz que esta certo" % (k, q))
                # a que sai toca ate ao corte novo e mais o cruzamento, e a dos creditos entra nele
                if y["sai"] and y["ult"] and abs(y["ult"]["ini"] + y["sai"]["dura"] - (y["ini"] + 2.2)) > 0.011:
                    problemas.append("%s: a que sai nao chega ao corte novo: %s" % (k, y))
        P = r["montagem"]["P"] if r.get("montagem") else None
        if P and (abs(P["noCorte"] - 95.0) > 0.011 or not P["onde"]["certo"] or abs(P["onde"]["certo"]["fim"] - 94.95) > 0.011):
            problemas.append("a montagem de 1/10: o corte aos %s devia estar na pausa dos 94,95" % (P and P["noCorte"]))
        if P and ("está certo" not in r["montagem"]["html"] or "data-cmclip" in r["montagem"]["html"]):
            problemas.append("a montagem de 1/10: a Mesa devia dizer que esta certo, sem «Ir ao clip»")
        P = r["menos2"]["P"] if r.get("menos2") else None
        if P:
            d = P["onde"]["depois"]
            if P["onde"]["certo"] or abs(P["noCorte"] - 93.0) > 0.011 or abs(d["zona"]["fim"] - 94.95) > 0.011 \
                    or abs(d["falta"] - 1.95) > 0.011 or abs(d["d"] - (d0 - 2.0 + 1.95)) > 0.011 or not d["ok"]:
                problemas.append("dois segundos a menos: %s" % P)
            h = r["menos2"]["html"]
            para = ("%.2f" % (d0 - 0.05)).rstrip("0").rstrip(".").replace(".", ",")
            for texto in ("a meio de uma frase", "faltam <b>1,95 s</b>", "o clip %d" % (ult + 1), "para <b>%s s</b>" % para,
                          "Antes do render final, a passagem mede-se outra vez (096)", "A Mesa não muda a duração"):
                if texto not in h:
                    problemas.append("dois segundos a menos, a linha nao diz %r: %s" % (texto, re.sub("<[^>]+>", "", h)[:300]))
            if "Ou tira-lhe" in h:
                problemas.append("dois segundos a menos: o encurtar deixava a foto com menos de 3 s, e oferece-se")
            if re.search(r"<(input|select)|data-cm(?!clip)[a-z]*=", h):
                problemas.append("a linha da passagem tem um controlo que muda alguma coisa (083)")
        P = r["mais1"]["P"] if r.get("mais1") else None
        if P:
            a, d = P["onde"]["antes"], P["onde"]["depois"]
            if P["onde"]["certo"] or abs(a["zona"]["fim"] - 94.95) > 0.011 or abs(d["zona"]["fim"] - 97.5) > 0.011 \
                    or d["zona"]["tipo"] != "verificada":
                problemas.append("um segundo a mais: %s" % P)
            if "Ou tira-lhe 1,05 s" not in r["mais1"]["html"]:
                problemas.append("um segundo a mais: devia oferecer tirar 1,05 s (a frase de antes esta mais perto)")
            if "verificado" not in (r["mais1"].get("depois") or {}).get("html", ""):
                problemas.append("na frase verificada (97,50) a Mesa devia dizer que e verificada")
        P = r["leitura64"]["P"] if r.get("leitura64") else None
        if P:
            d = P["onde"]["depois"]
            if abs(P["noCorte"] - 68.70) > 0.011 or abs(d["falta"] - 2.58) > 0.011 or abs(d["d"] - 6.58) > 0.011 \
                    or P["clip"]["n"] != 169 or "IMG_4098" not in P["clip"]["frase"] or abs(d["ate"] - 7.08) > 0.011:
                problemas.append("a leitura de 2 de outubro: %s" % P)
            # a frase de antes (66,59 s) esta mais perto, mas a foto ficava com 1,89 s: nao se oferece
            if "Ou tira-lhe" in r["leitura64"]["html"]:
                problemas.append("a leitura de 2 de outubro: oferece tirar 2,11 s a uma foto de 4 s")
    # a frase de antes mais perto (2,2 s contra 2,5), mas a foto ficava abaixo dos 3 s: so o para a frente (fins de
    # ensaio a volta do corte da montagem, sem a verificada; a foto da montagem tem 5 s, e ficava com 2,8)
    nc0 = r["montagem"]["P"]["noCorte"] if r and r.get("montagem") and r["montagem"]["P"] else 95.0
    x = _passagem_no_palco({"v": v}, {QUEEN: {"fim": 239.34, "linhas": [[round(nc0 - 2.2, 2), round(nc0 - 1.4, 2)],
                                                                          [round(nc0 + 2.5, 2), round(nc0 + 3.5, 2)]]}},
                           M, problemas, sem_fins=True)
    P = x and x["v"]["P"]
    if d0 - 2.2 < 3 and (not P or abs(P["onde"]["antes"]["falta"] + 2.2) > 0.011 or abs(P["onde"]["depois"]["falta"] - 2.5) > 0.011
                         or "Ou tira-lhe" in x["v"]["html"] or "faltam <b>2,5 s</b>" not in x["v"]["html"]):
        problemas.append("a frase de antes a 2,2 s com uma foto de %s s: %s" % (d0, x and re.sub("<[^>]+>", "", x["v"]["html"])[:300]))
    # sem passagem: «Como está», a mesma musica no mesmo sitio, uma escolha mal escrita, uma que nao chega a tocar; e sem
    # as frases medidas
    caladas = {}
    for nome, esc in (("como", None), ("erro", {"inicio": "fim"}), ("mesma", {"ficheiro": QUEEN, "inicio": 95.0}),
                      ("naoToca", {"ficheiro": TCOB, "inicio": 291.6}), ("semMedidas", M)):
        x = _passagem_no_palco({"v": v}, {} if nome == "semMedidas" else mf, esc, problemas, sem_fins=nome == "semMedidas")
        caladas[nome] = x and x["v"]
    for nome in ("como", "erro", "mesma", "naoToca"):
        if not caladas[nome] or caladas[nome]["P"] or caladas[nome]["html"]:
            problemas.append("%s: a Mesa fala da passagem sem haver passagem (%s)" % (nome, caladas[nome] and caladas[nome]["P"]))
    s = caladas.get("semMedidas")
    if not s or not s["P"] or "não tem as frases medidas" not in s["html"] or "data-cmclip" in s["html"]:
        problemas.append("sem frases medidas: %s" % (s and re.sub("<[^>]+>", "", s["html"])[:200]))
    verifica("Mesa: a passagem no palco e o que falta", not problemas, "; ".join(problemas)[:500] if problemas else
             "%d versoes: a duracao pedida poe o corte no fim da frase (para a frente e para tras), a versao fica igual, "
             "o encurtar so acima dos 3 s, a verificada dita, e calada em «Como está», na mesma e mal escrita" % len(r or {}))


def teste_passagem_guardada_ao_gravar_a_musica():
    """A chave passagem que venha na base (e outra que esta Mesa nao conheca) fica quando a Mesa grava a musica.

    O DEFEITO QUE ISTO APANHA (render3, 2 de outubro): o credMusicaPoe gravava so {ficheiro, inicio}, e uma passagem
    "frase" escrita na base (a saida B, que o ponto5 le) perdia-se na primeira mudanca do «Começa» ou da musica. A Mesa
    nao a mostra nem a poe: sem ela na base, nada muda no que grava. «Como está» tira a escolha inteira.
    """
    if not shutil.which("node"):
        salta("Mesa: a passagem fica ao gravar a musica", "sem node neste PC")
        return
    problemas = []
    funcoes = FUNCOES_JUNTAR + ["function credMusicaPoe(", "function credPoe(", "function credMusicaEscolha("]
    funcoes = [f for i, f in enumerate(funcoes) if f not in funcoes[:i]]
    prelude = PRELUDE_JUNTAR + """
var CRED = {omissoes: {cargos: [{cargo: "C", quem: "Q"}], titulo: "TITULO", data: "DATA"}, grupos: []};
function credOuvirPara(){}
function credPintaMusica(){}
function credPintaAnular(){}
function credMsg(){}
"""
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}],
          "pessoas": [], "tags": {}, "atual": "v1", "quando": "2026-10-02T10:00:00Z", "rev": 5, "pagina": "2026-10-02"}
    corpo_js = """
var r = {}, B0 = %(b0)s;
function com(m){ var b = copia(B0); b.creditos = {musica: m}; return b; }
abrir(com({ficheiro: %(tcob)s, inicio: "fim", passagem: "frase", outra: {a: 1}}));
credGuardaDesfazer("mudar onde começa a música dos créditos"); credMusicaPoe({ficheiro: %(tcob)s, inicio: "inicio"});
r.inicio = copia(corpo().creditos.musica);
credGuardaDesfazer("escolher a música dos créditos"); credMusicaPoe({ficheiro: %(queen)s, inicio: "fim"});
r.troca = copia(corpo().creditos.musica);
desfazer(); r.anular = copia(est.creditos.musica);
credMusicaPoe(null); r.como = est.creditos === undefined ? null : copia(est.creditos);
abrir(B0); credMusicaPoe({ficheiro: %(tcob)s, inicio: "fim"}); r.semNada = copia(corpo().creditos.musica);
abrir(com({ficheiro: %(tcob)s, inicio: "fim", passagem: "frase"})); r.escolha = credMusicaEscolha();
console.log(JSON.stringify(r));
""" % {"b0": json.dumps(B0), "tcob": json.dumps(TCOB), "queen": json.dumps(QUEEN)}
    r = _correr_js(DECLARACOES_JUNTAR, funcoes, prelude, corpo_js, problemas)
    if r:
        if r["inicio"] != {"ficheiro": TCOB, "inicio": "inicio", "passagem": "frase", "outra": {"a": 1}}:
            problemas.append("o «do início» perdeu a passagem: %s" % r["inicio"])
        if r["troca"] != {"ficheiro": QUEEN, "inicio": "fim", "passagem": "frase", "outra": {"a": 1}}:
            problemas.append("trocar de musica perdeu a passagem: %s" % r["troca"])
        if r["anular"] != r["inicio"]:
            problemas.append("o Anular nao voltou a escolha com a passagem: %s" % r["anular"])
        if r["como"] is not None:
            problemas.append("«Como está» deixou %s" % r["como"])
        if r["semNada"] != {"ficheiro": TCOB, "inicio": "fim"}:
            problemas.append("sem passagem na base a Mesa gravou outra coisa: %s" % r["semNada"])
        if r["escolha"] != {"ficheiro": TCOB, "inicio": "fim"}:
            problemas.append("a escolha lida com a passagem: %s" % r["escolha"])
    html = io.open(EDITOR, encoding="utf-8").read()
    if re.search(r'value="frase"|data-cmpassagem|passagem: "frase"', html):
        problemas.append("a Mesa mostra ou grava a escolha da passagem (B), que nao e para construir")
    verifica("Mesa: a passagem fica ao gravar a musica", not problemas, "; ".join(problemas)[:400] if problemas else
             "o «Começa», a troca de musica e o Anular guardam a passagem e o que a Mesa nao conhece; «Como está» tira tudo; "
             "sem ela, grava o mesmo")


def teste_mesa_montada_traz_os_fins_de_linha():
    """A Mesa montada traz os fins de linha da voz no window.MUSICA_FIM, a linha da passagem, e nada de novo a publicar.

    O DEFEITO QUE ISTO APANHA: o gerar_mesa sem os fins de linha (a Mesa diria que os Queen nao tem as frases medidas),
    um teste ou uma Mesa de ensaio a medir e a reescrever o guardado (o MESA_SOM=ler so le), e a passagem a pedir um
    ficheiro novo na publicacao. E o {} sem ficheiro: o modulo avisa, como a Mesa (contrato, seccoes 6 e 9).
    """
    import musica_creditos as mc
    problemas = []
    antes = os.path.getmtime(mc.LINHAS) if os.path.exists(mc.LINHAS) else None
    html = _montar_mesa_a_parte("mesa_passagem_")
    if antes is not None and os.path.getmtime(mc.LINHAS) != antes:
        problemas.append("a Mesa montada com MESA_SOM=ler reescreveu o %s" % os.path.basename(mc.LINHAS))
    m = re.search(r"window\.MUSICA_FIM = (.*?);\n", html)
    mf = json.loads(m.group(1)) if m else None
    if not mf:
        salta("Mesa: a Mesa montada traz os fins de linha", "Mesa montada sem o som")
        return
    q = (mf.get(QUEEN) or {}).get("linhas") or []
    if not any(abs(x[0] - 71.28) < 0.011 and abs(x[1] - 72.16) < 0.011 for x in q):
        problemas.append("os Queen sem a linha que acaba aos 71,28 s: %s" % [x for x in q if 68 < x[0] < 74])
    if any(len(x) != 2 for ls in (v.get("linhas") or [] for v in mf.values()) for x in ls):
        problemas.append("os fins de linha devem ir em pares [fim, linha nova]")
    com = sum(1 for v in mf.values() if v.get("linhas"))
    so_linhas = len(json.dumps({f: v.get("linhas") for f, v in mf.items() if v.get("linhas")}, separators=(",", ":")).encode("utf-8"))
    for marca in ('id="credMusPassagem"', "function credMusicaPassagem(", "function credIrAoClip("):
        if html.count(marca) != 1:
            problemas.append("a Mesa montada tem %d vezes %s" % (html.count(marca), marca))
    if re.search(r"(src|href)=\"[^\"]*fins_de_linha", html):
        problemas.append("a pagina pede o fins_de_linha.json como ficheiro")
    for vazia, aviso in (({}, True), ([], True), ("", False), (None, False), (0, False)):
        ok, erro = mc.escolha_valida(vazia)
        if ok is not None or bool(erro) is not aviso:
            problemas.append("escolha_valida(%r) deu %s" % (vazia, (ok, erro)))
    verifica("Mesa: a Mesa montada traz os fins de linha", not problemas, "; ".join(problemas)[:400] if problemas else
             "%d musicas com os fins de linha (%.1f KB na pagina, 0 ficheiros novos), os Queen aos 71,28 s, nada reescrito; "
             "o {} avisa" % (com, so_linhas / 1024.0))

# ------------------------------------------------- os creditos e o estilo a bater com o render (2 de outubro, a tarde)
# O ponto5_creditos.py desenha os creditos com a letra e as cores do estilo da Mesa (a legenda nos nomes, nos
# subtitulos e nos cargos; o cartao no letreiro dos titulos, de quem fez cada cargo, do titulo final e da data),
# acende o primeiro cargo do preto e conta os cargos de onde o rolo acaba, e encolhe um titulo de grupo que nao
# cabe. O contador ganhou a data do nascimento afastada (est.estilo.contador.data_afastada). Aqui guarda-se que:
#  12. o rolo da Mesa parte os nomes na letra da legenda como o rolo_de_nomes() do ponto5 (a altura, as linhas e
#      a duracao), com as quebras que o creditos_para_mesa.py mede com os ficheiros do render;
#  13. o desenho da Mesa usa a letra e a cor de cada texto como o ponto5, acende os cargos e o titulo como ele, e
#      os avisos dos textos (o titulo que encolhe e a que corpo, o que nao cabe) sao os do ponto5;
#  14. a data afastada grava-se so quando existe, desfaz-se, nao se perde nas propostas de cores nem na juncao de
#      dois aparelhos, o palco e a amostra descem-na o que o render desce, e a Mesa diz quando nao chega ao filme.
LETRAS_DO_ROLO = ("arial_bold", "georgia_bold", "bebas_neue", "montserrat_bold", "cinzel_bold", "cormorant_italico", "nao_existe")


def teste_creditos_rolo_na_letra_da_legenda():
    """A Mesa parte os nomes dos creditos na letra da legenda do estilo, como o rolo_de_nomes() do ponto5.

    O DEFEITO QUE ISTO APANHA: o ponto5 parte os nomes com a letra da legenda do estilo (letra_de_ler), e a Mesa
    partia-os sempre em Arial. Com o Georgia Bold na legenda o rolo do filme tem 110 linhas de nomes e a Mesa
    contava 92: outra altura, outra velocidade dos nomes, outra duracao dos creditos e outros nomes ao lado de cada
    foto. Compara-se, letra a letra, a altura do rolo, as linhas (sem as escrever) e a duracao. Uma letra que nao
    esta em data/fontes.json fica no Arial, nos dois.
    """
    if not shutil.which("node"):
        salta("Mesa: o rolo na letra da legenda como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    cred = cm.creditos_para_mesa()
    if not cred or cred["sem_nomes"]:
        salta("Mesa: o rolo na letra da legenda como o ponto5", "sem a folha de convidados")
        return
    p5 = cm._ponto5()
    problemas = []
    blocos, _fora = p5.por_grupo(p5.ler_convidados(p5.folha_mais_recente()))
    larg = p5.PAINEL_NOMES[1] - p5.PAINEL_NOMES[0]
    esperado = {}
    try:
        for letra in LETRAS_DO_ROLO:
            render.aplicar_estilo({"legenda": {"fonte": letra}} if letra != "arial_bold" else None, [])
            f = p5.letra_de_ler(p5.NOME_CORPO)
            linhas = [parte for _t, _s, ls in blocos for ag in ls for parte in p5.quebrar(ag, f, larg)]
            hr = p5.rolo_de_nomes(blocos).height
            esperado[letra] = (hr, linhas, p5.tempos_dos_creditos(hr, 0, len(p5.CARGOS))["dur"])
    finally:
        render.aplicar_estilo(None, [])
    corpo_js = """
var letras = %s, r = {};
letras.forEach(function(l){
  est.estilo = l === "arial_bold" ? undefined : {legenda: {fonte: l}};
  credLay = null;
  var L = credLayout();
  r[l] = {Hr: L.Hr, dur: L.dur, linhas: L.pecas.filter(function(q){ return q.tipo === "nome"; }).map(function(q){ return q.texto; })};
});
console.log(JSON.stringify(r));
""" % json.dumps(list(LETRAS_DO_ROLO))
    s = _correr_node(_prelude(cred, {"pessoas": [], "versoes": [], "tags": {}}), corpo_js, problemas)
    diferentes = 0
    if s:
        for letra in LETRAS_DO_ROLO:
            hr, linhas, dur = esperado[letra]
            m = s[letra]
            if m["Hr"] != hr:
                problemas.append("%s: o rolo da Mesa tem %d px e o do ponto5 %d" % (letra, m["Hr"], hr))
            if m["linhas"] != linhas:
                # nunca se escrevem os nomes: diz-se so quantas linhas e a primeira que difere
                k = next((i for i, (a, b) in enumerate(zip(m["linhas"], linhas)) if a != b), min(len(m["linhas"]), len(linhas)))
                problemas.append("%s: %d linhas de nomes na Mesa e %d no ponto5, a primeira diferente e a %d"
                                 % (letra, len(m["linhas"]), len(linhas), k + 1))
            if abs(m["dur"] - dur) > 1e-6:
                problemas.append("%s: os creditos duram %.2f s na Mesa e %.2f no ponto5" % (letra, m["dur"], dur))
            if letra not in ("arial_bold", "nao_existe") and linhas != esperado["arial_bold"][1]:
                diferentes += 1
        if diferentes < 3:
            problemas.append("so %d letras partem os nomes de outra maneira: o teste ja nao prova as quebras" % diferentes)
    verifica("Mesa: o rolo na letra da legenda como o ponto5", not problemas,
             "; ".join(problemas)[:400] if problemas else
             "%d letras (%d partem de outra maneira, de %d a %d linhas), a altura, as linhas e a duracao iguais"
             % (len(LETRAS_DO_ROLO), diferentes, min(len(v[1]) for v in esperado.values()),
                max(len(v[1]) for v in esperado.values())))


# os textos de ensaio dos avisos: nenhum e de um convidado
TEXTOS_DE_ENSAIO = {
    # o terceiro encolhe muito em todas as letras; o quarto fica a 56 em Montserrat, acima dos 54 dela e abaixo dos 58
    # do Arial (o minimo e o da letra, nao o do Arial)
    "gtitulo": ["FAMÍLIA DA CLARA", "AMIGOS DO MESTRADO", "OS AMIGOS DE SEMPRE DO TIAGO E DA CLARA", "AMIGOS DA FACULDADE"],
    "gsub": ["do lado da mãe", "os amigos de sempre do bairro, da escola, da faculdade e do trabalho"],
    "cargo": ["Ideia, textos, música e horas sem conta",
              "Ideia, textos, música, montagem, revisão, legendas, cores e horas e mais horas sem conta nenhuma"],
    # quem fez cada cargo (decisao 109): o segundo encolhe abaixo do corpo minimo da letra (de 110 para uns 50); o terceiro
    # sao tres pessoas, e a do meio faz encolher as tres (para uns 85); o quarto encolhe so um pouco (para uns 90)
    "quem": ["A MÃE DA CLARA", "A MÃE DA CLARA, O PAI DA CLARA E OS AVÓS",
             "OS PADRINHOS\nA FAMÍLIA TODA DO NOIVO\nAS MADRINHAS", "A MÃE DA CLARA E O PAI"],
    "titulo": ["CLARA & TIAGO", "CLARA & TIAGO PARA SEMPRE"],
    "data": ["4 DE OUTUBRO DE 2026", "SÁBADO, 4 DE OUTUBRO DE 2026, NA QUINTA PEDRAS SALGADAS"],
}
ESTILOS_DOS_CREDITOS = [
    {},
    {"legenda": {"fonte": "georgia_bold", "cor": "#FFF6E5"},
     "cartao": {"fonte": "georgia_bold", "quente": "#C9A04E", "claro": "#FFF2CF", "brilho": "#000000"}},
    {"legenda": {"fonte": "montserrat_bold"}, "cartao": {"fonte": "cormorant_bold"}},
    {"legenda": {"fonte": "cormorant_bold"}, "cartao": {"fonte": "montserrat_bold", "brilho": "#FF8C8C"}},
]


def _medidas_das_letras(render, estilos, letreiro, leitura):
    """As larguras que o PIL da com a letra de cada parte de cada estilo, para a Mesa medir no node como o ponto5
    mede: {letras: {css sem o corpo: id}, asc: {id: [asc, desc]}, letra: {id: {corpo: {c: largura}}},
    inteira: {"id|corpo|texto": largura}}. O letreiro mede-se letra a letra no dobro do corpo e a metade (o
    largura_do_letreiro do ponto5), a leitura o texto inteiro no corpo."""
    import gerar_mesa
    fontes = {f["id"]: f for f in gerar_mesa.fontes_para_mesa()["fontes"]}
    saida = {"letras": {}, "asc": {}, "letra": {}, "inteira": {}}
    try:
        for estilo in estilos:
            render.aplicar_estilo(estilo, [])
            for parte, corpos, textos in (("cartao", letreiro[0], letreiro[1]), ("legenda", leitura[0], leitura[1])):
                ident = (estilo.get(parte) or {}).get("fonte") or "arial_bold"
                f = fontes.get(ident) or fontes["arial_bold"]
                chave = ("i" if f.get("estilo_css") == "italic" else "") + str(f.get("peso_css") or 700) + "|" + (f.get("web") or "")
                saida["letras"][chave] = ident
                a, d = render.letra(parte, 1000).getmetrics()
                saida["asc"][ident] = [a / 1000.0, d / 1000.0]
                if parte == "cartao":
                    tabela = saida["letra"].setdefault(ident, {})
                    letras = sorted({c for t in textos for c in t})
                    for corpo in corpos:
                        g = render.letra("cartao", corpo * render.LETREIRO_SS)
                        tabela[str(corpo)] = {c: g.getlength(c) / float(render.LETREIRO_SS) for c in letras}
                else:
                    for corpo in corpos:
                        g = render.letra("legenda", corpo)
                        for t in textos:
                            saida["inteira"]["%s|%d|%s" % (ident, corpo, t)] = g.getlength(t)
    finally:
        render.aplicar_estilo(None, [])
    return saida


MEDIDOR_FALSO = """
var MED = %(med)s;
function medir(font, s){
  var m = /^(italic )?(\\d+) ([\\d.]+)px (.*)$/.exec(font), id = m ? MED.letras[(m[1] ? "i" : "") + m[2] + "|" + m[4]] : null;
  if(!id) throw new Error("letra sem medidas: " + font);
  var corpo = parseFloat(m[3]), ad = MED.asc[id];
  var r = {fontBoundingBoxAscent: ad[0] * corpo, fontBoundingBoxDescent: ad[1] * corpo, width: 0};
  if(s === "Hg") return r;
  var letras = Array.from(String(s));
  if(letras.length === 1 && MED.letra[id] && MED.letra[id][String(corpo)] && MED.letra[id][String(corpo)][s] !== undefined){
    r.width = MED.letra[id][String(corpo)][s]; return r;
  }
  var k = id + "|" + corpo + "|" + s;
  if(MED.inteira[k] === undefined){
    if(MED.letra[id] && MED.letra[id][String(corpo)]){ r.width = letras.reduce(function(a, c){ return a + MED.letra[id][String(corpo)][c]; }, 0); return r; }
    throw new Error("texto sem medida: " + k.slice(0, 60));
  }
  r.width = MED.inteira[k]; return r;
}
var credMedidor = {font: "", measureText: function(s){ return medir(this.font, s); }};
/* um canvas que so regista o que se escreve: o texto, a letra, a cor, a opacidade e se leva a sombra do brilho */
function telaFalsa(){
  var ops = [];
  var ctx = {ops: ops, globalAlpha: 1, font: "", fillStyle: "", strokeStyle: "", lineWidth: 1, lineCap: "", textAlign: "",
    textBaseline: "", shadowBlur: 0, shadowColor: "", imageSmoothingEnabled: true,
    setTransform: function(){}, save: function(){}, restore: function(){}, translate: function(){}, scale: function(){},
    fillRect: function(){}, beginPath: function(){}, moveTo: function(){}, lineTo: function(){}, stroke: function(){},
    arc: function(){}, fill: function(){}, strokeRect: function(){}, drawImage: function(){}, clearRect: function(){},
    createLinearGradient: function(){ var g = {grad: true, stops: []}; g.addColorStop = function(p, c){ g.stops.push([p, c]); }; return g; },
    measureText: function(s){ return medir(ctx.font, s); },
    fillText: function(s, x, y){ ops.push({t: String(s), x: x, y: y, font: ctx.font, fill: ctx.fillStyle, alfa: ctx.globalAlpha, sombra: ctx.shadowBlur > 0}); }
  };
  return {width: 1920, height: 1080, getContext: function(){ return ctx; }, ctx: ctx};
}
"""
FUNCOES_DESENHO_CRED = list(FUNCOES_CRED) + [
    "function credRgb(", "function credMistura(", "function credHex(", "function credLetraDe(", "function credCorDoEstilo(",
    "function credCoresLetreiro(", "function credCorDosNomes(", "function credFonte(", "function credAscDesc(",
    "function credLetreiro(", "function credTextoMeio(", "function credDesenhaEm(", "function credLargura(",
    "function credCorpoDoTitulo(", "function credMinimoDaLetra(", "function credAvisoDoTexto(", "function estiloEscolhaDoContador(",
    # os cargos (2 de outubro, a noite): as pessoas de cada um, o corpo a que cabem e onde fica cada coisa
    "function credPessoasDoQuem(", "function credCorpoDoQuem(", "function credGeometriaDoCargo("]


def teste_creditos_desenho_e_avisos_como_o_ponto5():
    """A Mesa desenha os creditos com a letra, a cor e os tempos do ponto5, e avisa o que ele avisa.

    O DEFEITO QUE ISTO APANHA, do lado da Mesa, com as larguras do PIL (as letras do render) no lugar das do browser:
    - os titulos, quem fez, o titulo final e a data noutra letra que nao a do cartao do estilo, ou os nomes, os
      subtitulos e os cargos noutra que nao a da legenda; os nomes sem a cor da legenda dele; o brilho desenhado
      quando ele o pos a preto;
    - o primeiro cargo a aparecer ja aceso, ou os cargos e o titulo a acender noutro instante do que no ponto5
      (comparado com os fotogramas do proprio desenho_dos_creditos);
    - um titulo de grupo a encolher para outro corpo, ou sem dizer que fica abaixo do corpo minimo da letra;
    - um texto que para o render dos creditos (textos_que_nao_cabem) sem a Mesa o dizer, ou a Mesa a dizer que
      nao cabe o que cabe.
    """
    if not shutil.which("node"):
        salta("Mesa: o desenho e os avisos dos creditos como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    from PIL import Image
    p5 = cm._ponto5()
    problemas = []
    M = dict(cm.MEDIDAS)
    M.update({"L": p5.L, "A": p5.A, "vel_nomes": p5.VELOCIDADE_NOMES, "vel_fotos_max": p5.VELOCIDADE_FOTOS_MAX,
              "nome_corpo": p5.NOME_CORPO, "sub_corpo": p5.SUB_CORPO, "cor_nome": list(p5.COR_NOME), "cor_sub": list(p5.COR_SUB),
              "painel_nomes": list(p5.PAINEL_NOMES), "margem_brilho": p5.MARGEM_BRILHO, "largura_foto": p5.LARGURA_FOTO,
              "centro_fotos": p5.CENTRO_FOTOS, "titulo_corpo": p5.TITULO_CORPO, "titulo_espaco": p5.TITULO_ESPACO,
              "titulo_altura": p5.letreiro_1x(["X"], p5.TITULO_CORPO, p5.TITULO_ESPACO).height - 2 * cm.MEDIDAS["corte_titulo"],
              "letreiro_quente": list(render.LETREIRO_QUENTE), "letreiro_claro": list(render.LETREIRO_BRANCO),
              "letreiro_brilho": list(render.LETREIRO_BRILHO), "letreiro_empurra": render.LETREIRO_EMPURRA,
              "fade_fim_imagem": render.FADE_FIM_IMAGEM, "zona_segura": p5.ZONA_SEGURA})
    T0 = TEXTOS_DE_ENSAIO
    cargos = [(c, q) for c, q in p5.CARGOS]
    cred = {"medidas": M, "folha": "ensaio", "sem_nomes": "", "fotos": {},
            "omissoes": {"cargos": [{"cargo": c, "quem": q} for c, q in cargos], "titulo": p5.TITULO, "data": p5.DATA},
            "grupos": [{"etiqueta": "G1", "titulo": T0["gtitulo"][1], "sub": T0["gsub"][0], "linhas": ["Pessoa Um · Pessoa Dois", "Pessoa Tres"]},
                       {"etiqueta": "G2", "titulo": T0["gtitulo"][2], "sub": "outro grupo", "linhas": ["Pessoa Quatro"]}]}
    letreiro_textos = (T0["gtitulo"] + [p for q in T0["quem"] for p in q.split("\n")] + T0["titulo"] + T0["data"] + [q for _c, q in cargos] + [p5.TITULO, p5.DATA])
    leitura_textos = T0["gsub"] + T0["cargo"] + [c for c, _q in cargos] + ["outro grupo", "Pessoa Um · Pessoa Dois", "Pessoa Tres", "Pessoa Quatro"]
    # o quem encolhe de 110 para baixo, 1 px de cada vez (decisao 109): o letreiro mede-se em todos os corpos ate la
    med = _medidas_das_letras(render, ESTILOS_DOS_CREDITOS, (list(range(1, max(p5.TITULO_CORPO, p5.QUEM_CORPO) + 1)) + [130], letreiro_textos),
                              ([58], leitura_textos))
    # O PONTO5, estilo a estilo: o corpo de cada titulo, se diz que fica abaixo do minimo, e o que nao cabe
    do_ponto5 = []
    try:
        for estilo in ESTILOS_DOS_CREDITOS:
            render.aplicar_estilo(estilo, [])
            corpos = {t: p5.corpo_do_titulo(t) for t in T0["gtitulo"]}
            abaixo = {t: any("abaixo dos" in a for a in p5.titulos_que_encolhem([(t, "", [])])) for t in T0["gtitulo"]}
            nao_cabem = {}
            for campo in ("gsub", "cargo", "quem", "titulo", "data"):
                for k, texto in enumerate(T0[campo]):
                    textos = {"cargos": list(cargos), "titulo": p5.TITULO, "data": p5.DATA}
                    blocos = [("T", "s", [])]
                    if campo == "gsub":
                        blocos = [("T", texto, [])]
                    elif campo == "cargo":
                        textos["cargos"][0] = (texto, cargos[0][1])
                    elif campo == "quem":
                        textos["cargos"][0] = (cargos[0][0], texto)
                    else:
                        textos[campo] = texto
                    # so o problema DESTE texto: os outros sao os de omissao, e com outra letra um deles podia nao caber
                    marca = {"gsub": 'o subtitulo "%s"', "cargo": 'o cargo 1 ("%s")', "quem": 'quem fez o cargo 1 ("%s")',
                             "titulo": 'o titulo final "%s"', "data": 'a data "%s"'}[campo] % texto
                    nao_cabem["%s|%d" % (campo, k)] = next((x for x in p5.textos_que_nao_cabem(textos, blocos)
                                                            if x.startswith(marca)), None)
            # QUEM FEZ O CARGO ENCOLHE (decisao 109): o corpo do corpo_do_quem e se fica abaixo do minimo (quem_que_encolhe)
            quem = [(p5.corpo_do_quem(p5.pessoas_do_quem(t)),
                     any("15 m" in a for a in p5.quem_que_encolhe({"cargos": [(cargos[0][0], t)]}))) for t in T0["quem"]]
            do_ponto5.append({"corpos": corpos, "abaixo": abaixo, "nao_cabem": nao_cabem, "quem": quem})
    finally:
        render.aplicar_estilo(None, [])
    # OS TEMPOS DO PONTO5: o desenho_dos_creditos com um rolo e uma coluna pretos (a medida e a opacidade do cargo e do
    # titulo, que nao dependem deles), com o T da altura do rolo que a Mesa conta
    corpo_js = MEDIDOR_FALSO % {"med": json.dumps(med, ensure_ascii=False)} + """
var CRED = %(cred)s, credLay = null, credTemFinais = false, porId = {};
function credAberto(){ return false; }
var estilos = %(estilos)s, textos = %(textos)s, r = {estilos: [], tempos: null};
estilos.forEach(function(e){
  est.estilo = JSON.parse(JSON.stringify(e)); credLay = null; credLargurasGuardadas = {};
  if(!Object.keys(est.estilo).length) delete est.estilo;
  var o = {corpos: {}, avisos: {}};
  textos.gtitulo.forEach(function(t){ o.corpos[t] = credCorpoDoTitulo(t); o.avisos["gtitulo|" + t] = credAvisoDoTexto("gtitulo", t); });
  ["gsub", "cargo", "quem", "titulo", "data"].forEach(function(c){ textos[c].forEach(function(t, k){ o.avisos[c + "|" + k] = credAvisoDoTexto(c, t); }); });
  var Lay = credContas(), M = CRED.medidas, fecho = M.t_entrada + Lay.tRolo + M.fim_do_rolo;
  var tela = telaFalsa();
  credDesenhaEm(tela, M.t_entrada + 3, false, false);
  o.rolo = tela.ctx.ops.map(function(x){ return {t: x.t, font: x.font, fill: x.fill && x.fill.grad ? {grad: x.fill.stops} : x.fill, sombra: x.sombra}; });
  tela = telaFalsa(); credDesenhaEm(tela, fecho + 2.0, false, false);
  o.cargo = tela.ctx.ops.map(function(x){ return {t: x.t, x: x.x, font: x.font, fill: x.fill && x.fill.grad ? {grad: x.fill.stops} : x.fill, sombra: x.sombra}; });
  tela = telaFalsa(); credDesenhaEm(tela, fecho + Lay.nCargos * M.t_cargo + 2.5, false, false);
  o.fim = tela.ctx.ops.map(function(x){ return {t: x.t, font: x.font, sombra: x.sombra}; });
  o.Hr = Lay.Hr; o.tRolo = Lay.tRolo;
  o.quem = textos.quem.map(function(t){ return credCorpoDoQuem(credPessoasDoQuem(t)); });
  r.estilos.push(o);
});
delete est.estilo; credLay = null;
var tempos = %(tempos)s;
r.tempos = tempos.map(function(t){
  var tela = telaFalsa(); credDesenhaEm(tela, t, false, false);
  return tela.ctx.ops.reduce(function(a, x){ return Math.max(a, x.alfa); }, 0);
});
console.log(JSON.stringify(r));
"""
    # os instantes: o rolo a acabar, o segundo preto, a entrada e a saida de cada cargo e a do titulo
    Hr0 = None
    s = None
    pre = _correr_estilo({"pessoas": [], "versoes": [], "tags": {}}, corpo_js % {
        "cred": json.dumps(cred, ensure_ascii=False), "estilos": json.dumps(ESTILOS_DOS_CREDITOS[:1]),
        "textos": json.dumps(T0, ensure_ascii=False), "tempos": "[]"}, problemas, mais=FUNCOES_DESENHO_CRED,
        declaracoes=["var CRED_ARIAL = ", "var credLetrasPedidas = "])
    if pre:
        Hr0 = pre["estilos"][0]["Hr"]
        T = p5.tempos_dos_creditos(Hr0, 0, len(cargos))
        if abs(T["t_rolo"] - pre["estilos"][0]["tRolo"]) > 1e-9:
            problemas.append("o rolo dura %.3f s na Mesa e %.3f no ponto5" % (pre["estilos"][0]["tRolo"], T["t_rolo"]))
        tc, tf = T["t_cargos"], T["t_cargos"] + len(cargos) * T["t_cargo"]
        instantes = ([T["t_entrada"] + T["t_rolo"] + 0.9] + [tc + k * T["t_cargo"] + u for k in range(len(cargos))
                                                           for u in (0.0, 0.1, 0.3, 0.45, 2.0, 3.75, 4.1)]
                     + [tf + u for u in (0.0, 0.4, 2.5, 5.5, 6.9)])
        s = _correr_estilo({"pessoas": [], "versoes": [], "tags": {}}, corpo_js % {
            "cred": json.dumps(cred, ensure_ascii=False), "estilos": json.dumps(ESTILOS_DOS_CREDITOS),
            "textos": json.dumps(T0, ensure_ascii=False), "tempos": json.dumps(instantes)}, problemas,
            mais=FUNCOES_DESENHO_CRED, declaracoes=["var CRED_ARIAL = ", "var credLetrasPedidas = "])
    if s:
        # 1. as opacidades contra os fotogramas do ponto5
        render.aplicar_estilo(None, [])
        desenho = p5.desenho_dos_creditos(Image.new("RGB", (1040, Hr0 + 20)), Image.new("RGB", (800, 40)),
                                          p5.textos_dos_creditos({}), {}, T)

        def brilho(t):
            return max(desenho(t).convert("L").getextrema()[1], 0)
        cheio = {k: brilho(tc + k * T["t_cargo"] + 2.0) for k in range(len(cargos))}
        cheio["fim"] = brilho(tf + 2.5)
        piores = []
        for t, alfa_mesa in zip(instantes, s["tempos"]):
            if t < tc:
                ref, alfa_p5 = None, brilho(t) / 255.0
            elif t < tf:
                k = int((t - tc) // T["t_cargo"])
                alfa_p5 = brilho(t) / float(cheio[k])
            else:
                alfa_p5 = brilho(t) / float(cheio["fim"])
            folga = 0.02 if t >= tf else 0.006
            if abs(alfa_mesa - alfa_p5) > folga:
                piores.append("%.2f s: Mesa %.3f, ponto5 %.3f" % (t, alfa_mesa, alfa_p5))
        if piores:
            problemas.append("os cargos e o titulo acendem noutro instante: %s" % "; ".join(piores[:4]))
        if s["tempos"][1] > 0.001:
            problemas.append("o primeiro cargo nao acende do preto: a Mesa da %.3f no primeiro fotograma" % s["tempos"][1])
        # 2. as letras e as cores, estilo a estilo
        import gerar_mesa
        fontes = {f["id"]: f for f in gerar_mesa.fontes_para_mesa()["fontes"]}

        def css(ident):
            f = fontes[ident]
            return ("italic " if f.get("estilo_css") == "italic" else "") + str(f.get("peso_css") or 700) + " %dpx " + f["web"]
        for estilo, o, q in zip(ESTILOS_DOS_CREDITOS, s["estilos"], do_ponto5):
            nome = json.dumps(estilo)[:50]
            cartao = css((estilo.get("cartao") or {}).get("fonte") or "arial_bold")
            leitura = css((estilo.get("legenda") or {}).get("fonte") or "arial_bold")
            cor = (estilo.get("legenda") or {}).get("cor")
            cor_nome = list(render.cor_rgb(cor)) if cor else list(p5.COR_NOME)
            semBrilho = (estilo.get("cartao") or {}).get("brilho") == "#000000"
            nomes = [x for x in o["rolo"] if x["t"].startswith("Pessoa")]
            subs = [x for x in o["rolo"] if x["t"] in (T0["gsub"][0], "outro grupo")]
            letras_titulo = [x for x in o["rolo"] if isinstance(x["fill"], dict)]
            if not nomes or any(x["font"] != leitura % 58 or x["fill"] != "rgba(%d,%d,%d,1)" % tuple(cor_nome) for x in nomes):
                problemas.append("%s: os nomes nao vao na letra e na cor da legenda (%s)" % (nome, nomes[:1]))
            if not subs or any(x["font"] != leitura % 58 or x["fill"] != "rgba(%d,%d,%d,1)" % tuple(p5.COR_SUB) for x in subs):
                problemas.append("%s: os subtitulos nao vao na letra da legenda e no champanhe" % nome)
            if not letras_titulo or any(not x["font"].endswith("px " + cartao.split("px ", 1)[1]) for x in letras_titulo):
                problemas.append("%s: os titulos dos grupos nao vao na letra do cartao" % nome)
            if any(x["sombra"] for x in letras_titulo) != (not semBrilho):
                problemas.append("%s: o brilho dos titulos %s" % (nome, "desenhado com o brilho a preto" if semBrilho else "nao foi desenhado"))
            quem = [x for x in o["cargo"] if isinstance(x["fill"], dict)]
            # AS LETRAS ESCREVEM-SE UMA VEZ, e o brilho fora do ecra (so a sombra cai no sitio): escritas tres vezes, a
            # meio de acender pareciam mais acesas do que no filme (a 0,5, a 0,88)
            no_sitio = [x for x in quem if not x["sombra"]]
            if len(no_sitio) != len(cargos[0][1]) or any(x["x"] < 3000 for x in quem if x["sombra"]):
                problemas.append("%s: as letras de quem fez o cargo escrevem-se %d vezes no sitio (%d letras)"
                                 % (nome, len([x for x in quem if x["x"] < 3000]), len(cargos[0][1])))
            linha = [x for x in o["cargo"] if not isinstance(x["fill"], dict)]
            if not quem or any(x["font"] != cartao % 110 for x in quem) or not linha or \
                    any(x["font"] != leitura % 58 or x["fill"] != "rgba(%d,%d,%d,1)" % tuple(p5.COR_SUB) for x in linha):
                problemas.append("%s: o cargo nao vai como no ponto5 (quem no letreiro a 110, o cargo na legenda a 58)" % nome)
            corpos_fim = sorted({x["font"] for x in o["fim"]})
            if corpos_fim != sorted({cartao % 130, cartao % 58}):
                problemas.append("%s: o titulo final e a data vao em %s" % (nome, corpos_fim))
            # 3. quem fez o cargo encolhe como no ponto5 (decisao 109): o mesmo corpo, o aviso diz-o, e o minimo
            for k, t in enumerate(T0["quem"]):
                cp, ab = q["quem"][k]
                av = o["avisos"]["quem|%d" % k]
                if o["quem"][k] != cp:
                    problemas.append("%s: quem %r encolhe para %d na Mesa e %d no ponto5" % (nome, t[:20], o["quem"][k], cp))
                if (cp < p5.QUEM_CORPO) != ("encolhe" in av and "para %d px" % cp in av) or ("abaixo dos" in av) != ab:
                    problemas.append("%s: o aviso de quem %r: %r (o ponto5 encolhe-o para %d%s)"
                                     % (nome, t[:20], av[:80], cp, ", abaixo do minimo" if ab else ""))
            # 4. o titulo que encolhe, e os avisos
            for t in T0["gtitulo"]:
                cm_, cp = o["corpos"][t], q["corpos"][t]
                if cm_ != cp:
                    problemas.append("%s: o titulo %r encolhe para %d na Mesa e %d no ponto5" % (nome, t[:20], cm_, cp))
                av = o["avisos"]["gtitulo|" + t]
                if (cp < p5.TITULO_CORPO) != bool(av) or (cp < p5.TITULO_CORPO and "para %d px" % cp not in av):
                    problemas.append("%s: o aviso do titulo %r nao diz o corpo: %r" % (nome, t[:20], av[:60]))
                if bool(av) and ("abaixo dos" in av) != q["abaixo"][t]:
                    problemas.append("%s: o titulo %r abaixo do minimo: Mesa %s, ponto5 %s" % (nome, t[:20], "abaixo dos" in av, q["abaixo"][t]))
            for chave, para in q["nao_cabem"].items():
                av = o["avisos"][chave]
                if para and not (av.startswith("Não cabe") or av.startswith("Está no limite")):
                    problemas.append("%s: %s para o render e a Mesa diz %r" % (nome, chave, av[:40]))
                if not para and av.startswith("Não cabe"):
                    problemas.append("%s: %s cabe no render e a Mesa diz que nao" % (nome, chave))
                # e as contas sao as dele: a largura e o que cabe (o painel, 920, ou a zona segura, 1728)
                if para and av:
                    mp = re.search(r"tem (\d+) px e cabem (\d+)", para)
                    mm = re.search(r"uns (\d+) px, cabem (\d+)", av)
                    if not (mp and mm and mp.group(2) == mm.group(2) and abs(int(mp.group(1)) - int(mm.group(1))) <= 1):
                        problemas.append("%s: %s, a Mesa diz %r e o ponto5 %r" % (nome, chave, av[:50], para[-40:]))
        paragens = sum(1 for q in do_ponto5 for v in q["nao_cabem"].values() if v)
        if not any(c < p5.QUEM_CORPO and not ab for q in do_ponto5 for c, ab in q["quem"]) or \
                not any(ab for q in do_ponto5 for _c, ab in q["quem"]):
            problemas.append("os quem de ensaio ja nao provam nada: nenhum encolhe acima do minimo, ou nenhum abaixo")
        if not any(q["corpos"].get(TEXTOS_DE_ENSAIO["gtitulo"][3], 60) in range(54, 58) for q in do_ponto5):
            problemas.append("nenhum titulo de ensaio fica entre o minimo da letra e os 58 do Arial")
        if paragens < 6 or not any(v < p5.TITULO_CORPO for q in do_ponto5 for v in q["corpos"].values()):
            problemas.append("os textos de ensaio ja nao provam nada: %d param o render" % paragens)
    verifica("Mesa: o desenho e os avisos dos creditos como o ponto5", not problemas,
             "; ".join(problemas)[:500] if problemas else
             "%d estilos: letra e cor de cada texto, brilho, %d instantes do fecho iguais aos fotogramas, titulos e quem que "
             "encolhem (com e sem o minimo) e textos que param o render" % (len(ESTILOS_DOS_CREDITOS), len(s["tempos"]) if s else 0))


def teste_estilo_data_afastada_grava_desfaz_e_junta():
    """A data do nascimento afastada grava-se so quando existe, e o palco e a amostra descem-na o que o render desce.

    O DEFEITO QUE ISTO APANHA: uma escolha que ninguem fez gravada como false (o render via um estilo e o montar
    escrevia um estilo.json), uma proposta de cores do contador a tira-la sem ele saber, o «Como está» a deixa-la,
    a juncao de dois aparelhos a perde-la (a Clara a mudar uma cor do contador e o Tiago a data), uma Mesa antiga
    a apaga-la, e o palco e a amostra a mostrar a data noutro sitio do que o render a poe. E a Mesa calada quando o
    render ainda nao a le, ou quando «uma só peça» a torna inutil.
    """
    if not shutil.which("node"):
        salta("Mesa: a data afastada grava, desfaz e junta", "sem node neste PC")
        return
    import gerar_mesa
    import linha_tempo
    import render
    problemas = []
    base = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "marcos", "x": "1995@0-1|*12/09 Nasce o Tiago"}]}],
            "atual": "v1", "pessoas": [], "tags": {}}
    mais = ["function estiloPoePaleta(", "function palcoCores(", "function palcoMistura(", "function palcoMeses(",
            "function palcoParagens(", "function palcoSuave(", "function fracaoDeData(", "function palcoLinha(",
            "function palcoTexto(", "function palcoRgb(", "function estiloTextoMeio(", "function estiloCoresContador(",
            "function fitaLer(", "function estiloDesenhaFita(", "function estiloFitaDoFilme(", "function estiloClipsDoFilme(",
            "function estiloLinha(", "function estiloRgbCss(", "function estiloMistura(", "function estiloReporParte(",
            "function estiloVoltarAoMeu(",
            # a letra do contador (3 de outubro): o palco e a amostra escrevem os textos da fita com ela
            "function palcoCssContador(", "function estiloCssContador("]
    js = """
var PALCO = {marcas: {}}, ESTILO_PALETAS_OK = true;
function tela(){
  var ops = [];
  var ctx = {ops: ops, fillRect: function(){}, beginPath: function(){}, moveTo: function(){}, lineTo: function(){}, stroke: function(){},
    arc: function(){}, fill: function(){}, save: function(){}, restore: function(){}, drawImage: function(){}, strokeRect: function(){},
    measureText: function(){ return {actualBoundingBoxAscent: 30, actualBoundingBoxDescent: 2}; },
    fillText: function(s, x, y){ ops.push({t: String(s), y: y}); }};
  return {ctx: ctx, s: 0.5};
}
function yDaData(ops){ var d = ops.filter(function(o){ return /^12 de setembro$/.test(o.t); })[0]; return d ? d.y : null; }
function noPalco(){
  var k = palcoCores(), fita = fitaLer("1995@0-1|*12/09 Nasce o Tiago");
  for(var i = 0; i <= 400; i++){ var t = tela(); palcoMeses(t.ctx, fita, i * 0.025, 10, k); var y = yDaData(t.ctx.ops); if(y !== null) return y; }
  return null;
}
function naAmostra(af){ var t = tela(); estiloDesenhaFita(t, af); return yDaData(t.ctx.ops); }
var r = {}, copia = function(){ return est.estilo === undefined ? null : JSON.parse(JSON.stringify(est.estilo)); };
RENDER_LE = {data_afastada: true};
estiloPoeDataAfastada(true); r.sim = copia(); r.vista = estiloContadorVista; r.valor = estiloTextoDoValor("contador", "data_afastada", true);
r.mudancas = estiloMudancas("contador"); r.parte = estiloParteMudada("contador");
pilhaDesfazer[pilhaDesfazer.length - 1].aoAnular(); r.anulado = copia();
estiloPoeDataAfastada(true); estiloPoeDataAfastada(false); r.nao = copia();
r.lixo = [estiloPoe("contador", "data_afastada", "sim"), estiloPoe("contador", "data_afastada", 1), estiloLimpo("contador", "data_afastada", null)];
/* as propostas de cores nao lhe tocam, e nao contam com ela para saber qual esta escolhida */
estiloPoeDataAfastada(true); estiloPoePaleta("contador", 2); r.paleta = copia(); r.paletaAtiva = estiloPaletaAtiva("contador", 2);
estiloPoePaleta("contador", 0); r.paleta0 = copia(); r.cores = Object.keys(estiloCoresContador()).sort();
/* «Como está (original)» tira-a com o resto do contador, e «O teu de há pouco» devolve-a */
estiloPoePaleta("contador", 1); estiloReporParte("contador"); r.comoEsta = copia(); estiloVoltarAoMeu("contador"); r.meu = copia();
/* o palco e a amostra: a data desce o que o render desce, so na fita de duas pecas e so se o render a faz */
delete est.estilo; r.palcoHoje = noPalco(); r.amostraHoje = naAmostra(false);
est.estilo = {contador: {data_afastada: true}}; r.palcoSim = noPalco(); r.amostraSim = naAmostra(true);
est.estilo = {contador: {data_afastada: true, continuo: true}}; r.palcoUma = noPalco();
RENDER_LE = {data_afastada: false}; est.estilo = {contador: {data_afastada: true}}; r.palcoNaoLe = noPalco();
/* o que a Mesa diz */
r.avisos = {};
[["le", {data_afastada: true}, {data_afastada: true}], ["naoLe", {data_afastada: false}, {data_afastada: true}],
 ["naoSei", {}, {data_afastada: true}], ["uma", {data_afastada: true}, {data_afastada: true, continuo: true}],
 ["semEscolha", {data_afastada: false}, null]].forEach(function(c){
  RENDER_LE = c[1];
  if(c[2]) est.estilo = {contador: c[2]}; else delete est.estilo;
  var a = estiloAvisoDataAfastada();
  r.avisos[c[0]] = {forte: !!a.forte, t: a.t, lista: estiloAvisos("contador").map(function(x){ return [!!x.forte, x.t]; })};
});
console.log(JSON.stringify(r));
"""
    s = _correr_estilo(base, js, problemas, mais=mais,
                       declaracoes=["var ESTILO_MESES = ", "var ESTILO_MESES_LONGOS = ", "var ESTILO_GUIA_HOJE = "])
    if s:
        sim = {"contador": {"data_afastada": True}}
        if s["sim"] != sim or s["vista"] != "data" or s["valor"] != "mais afastada":
            problemas.append("escolher gravou %s, a amostra ficou em %s e le-se %r" % (s["sim"], s["vista"], s["valor"]))
        if s["mudancas"] != ["a data do nascimento mais afastada"] or not s["parte"]:
            problemas.append("a mudanca le-se %s" % s["mudancas"])
        if s["anulado"] is not None or s["nao"] is not None:
            problemas.append("o anular deu %s e o «como está» %s" % (s["anulado"], s["nao"]))
        if s["lixo"] != [False, False, None]:
            problemas.append("valores que nao sao true nem false entraram: %s" % s["lixo"])
        if s["paleta"] != {"contador": {"data_afastada": True, "marco": "#5B8BD9", "marco_texto": "#E3EEFF", "nascimento": "#CFE0FF"}} \
                or not s["paletaAtiva"] or s["paleta0"] != sim or "data_afastada" in s["cores"] or "continuo" in s["cores"]:
            problemas.append("as propostas de cores mexeram na escolha: %s, %s" % (s["paleta"], s["paleta0"]))
        if s["comoEsta"] is not None or (s["meu"] or {}).get("contador", {}).get("data_afastada") is not True:
            problemas.append("«Como está» deixou %s e o teu de ha pouco voltou %s" % (s["comoEsta"], s["meu"]))
        afasta = linha_tempo.NASC_DATA_AFASTA
        if None in (s["palcoHoje"], s["palcoSim"], s["amostraHoje"], s["amostraSim"]):
            problemas.append("a data nao se desenhou no palco ou na amostra")
        else:
            if round(s["palcoSim"] - s["palcoHoje"], 6) != afasta or round(s["amostraSim"] - s["amostraHoje"], 6) != afasta:
                problemas.append("a data desce %s no palco e %s na amostra, e %d no render"
                                 % (s["palcoSim"] - s["palcoHoje"], s["amostraSim"] - s["amostraHoje"], afasta))
            if s["palcoUma"] != s["palcoHoje"] or s["palcoNaoLe"] != s["palcoHoje"]:
                problemas.append("o palco desce a data com uma so peca (%s) ou com o render sem a ler (%s)" % (s["palcoUma"], s["palcoNaoLe"]))
        a = s["avisos"]
        if a["le"]["t"] or any(f for f, _t in a["le"]["lista"]):
            problemas.append("com o render a ler, a Mesa avisa: %s" % a["le"])
        if not (a["naoLe"]["forte"] and "ainda não chega ao filme" in a["naoLe"]["t"]
                and any(f and "ainda não chega ao filme" in t for f, t in a["naoLe"]["lista"])):
            problemas.append("sem o render a ler, a Mesa nao diz que nao chega ao filme: %s" % a["naoLe"])
        if not a["naoSei"]["t"] or a["naoSei"]["forte"]:
            problemas.append("sem saber se o render le, a Mesa diz %r" % a["naoSei"]["t"])
        if "não muda nada" not in a["uma"]["t"] or a["uma"]["forte"]:
            problemas.append("com uma so peca, a Mesa diz %r" % a["uma"]["t"])
        # sem a escolha, por baixo dela pode dizer que ainda nao chega ao filme (como o «uma só peça»), mas nunca forte,
        # e nos avisos do contador nao fala dela
        if a["semEscolha"]["forte"] or a["semEscolha"]["lista"]:
            problemas.append("sem a escolha, a Mesa avisa dela: %s" % a["semEscolha"])
        # o que a Mesa grava e o que o render guarda, sem avisos
        av = []
        if render.normalizar_estilo(s["sim"], av) != s["sim"] or av or render.normalizar_estilo(s["paleta"], av) != s["paleta"] or av:
            problemas.append("o render limpa a escolha de outra maneira: %s %s" % (render.normalizar_estilo(s["sim"]), av))
    if gerar_mesa.o_que_o_render_le().get("data_afastada") is not True:
        problemas.append("o gerar_mesa nao ve que o render ja le a data afastada")
    # A JUNCAO POR PARTES: a data e uma parte propria, e sobrevive a dois aparelhos e a uma Mesa antiga
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}],
          "pessoas": [], "tags": {}, "atual": "v1", "estilo": {"contador": {"marco": "#5B8BD9"}},
          "quando": "2026-10-02T10:00:00Z", "rev": 5, "pagina": "2026-10-02"}
    corpo_js = """
var r = {}, B0 = %s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
/* A. aqui a data, la uma cor do contador: juntam-se */
abrir(B0); est.estilo = {contador: {marco: "#5B8BD9", data_afastada: true}};
var j = juntarComBase(com({estilo: {contador: {marco: "#5B8BD9", linha: "#7A6A76"}}, rev: 6}));
r.A = {ok: j.ok, estilo: copia(est.estilo), partes: Object.keys(partesDe(corpo())).filter(function(k){ return k.indexOf("data_afastada") >= 0; })};
/* B. os dois a afasta-la: nao e conflito */
abrir(B0); est.estilo = {contador: {marco: "#5B8BD9", data_afastada: true}};
j = juntarComBase(com({estilo: {contador: {marco: "#5B8BD9", data_afastada: true}}, rev: 6}));
r.B = {ok: j.ok, estilo: copia(est.estilo)};
/* C. uma Mesa antiga (sem pagina, sem o estilo) grava: a data volta a base */
abrir(com({estilo: {contador: {data_afastada: true}}}));
j = juntarComBase(com({estilo: undefined, pagina: undefined, rev: 6}));
r.C = {ok: j.ok, repostos: j.repostos, estilo: corpo().estilo};
/* D. uma Mesa de hoje que nao conhece a chave copia o est.estilo inteiro e muda uma cor: a data fica */
abrir(com({estilo: {contador: {marco: "#5B8BD9", data_afastada: true}}}));
j = juntarComBase(com({estilo: {contador: {marco: "#C9A45C", data_afastada: true}}, rev: 6}));
r.D = {ok: j.ok, estilo: copia(est.estilo)};
/* E. o outro aparelho pos o contador como esta: sai tudo, a data tambem (foi ele que escolheu) */
abrir(com({estilo: {contador: {marco: "#5B8BD9", data_afastada: true}}}));
j = juntarComBase(com({estilo: undefined, rev: 6}));
r.E = {ok: j.ok, estilo: est.estilo === undefined ? null : est.estilo};
console.log(JSON.stringify(r));
""" % json.dumps(B0)
    r = _correr_js(DECLARACOES_JUNTAR, FUNCOES_JUNTAR, PRELUDE_JUNTAR, corpo_js, problemas)
    if r:
        if not r["A"]["ok"] or r["A"]["estilo"] != {"contador": {"marco": "#5B8BD9", "data_afastada": True, "linha": "#7A6A76"}} \
                or r["A"]["partes"] != ['["estilo","contador","data_afastada"]']:
            problemas.append("a data aqui e uma cor la: %s" % r["A"])
        if not r["B"]["ok"] or r["B"]["estilo"] != {"contador": {"marco": "#5B8BD9", "data_afastada": True}}:
            problemas.append("a data nos dois: %s" % r["B"])
        if not r["C"]["ok"] or r["C"]["repostos"] != ["estilo"] or r["C"]["estilo"] != {"contador": {"data_afastada": True}}:
            problemas.append("a Mesa antiga: %s" % r["C"])
        if not r["D"]["ok"] or r["D"]["estilo"] != {"contador": {"marco": "#C9A45C", "data_afastada": True}}:
            problemas.append("a Mesa de hoje que nao a conhece: %s" % r["D"])
        if not r["E"]["ok"] or r["E"]["estilo"] is not None:
            problemas.append("o contador como esta no outro aparelho: %s" % r["E"])
    verifica("Mesa: a data afastada grava, desfaz e junta", not problemas, "; ".join(problemas)[:500] if problemas else
             "so o true, anular, lixo recusado, propostas e como esta, palco e amostra a %d px, avisos, o render e "
             "o gerar_mesa a ler, e cinco juncoes" % linha_tempo.NASC_DATA_AFASTA)


# ------------------------------------------------------------- a letra do letreiro da intro (2 de outubro, a noite)
# O Tiago pediu para mudar a letra da intro no Estilo, e ficou combinado: «Impact (como está)» por omissao, so as
# letras grossas o suficiente (data/fontes_intro.json, oferecida true), cada uma com quanto da foto se ve por dentro, e
# o custo de cada combinacao nova na montagem. O render le est.estilo.intro.fonte (render.normalizar_estilo), o montar
# faz a intro com essa letra (intro_flipbook --fonte) e o nome dela leva o id. Aqui guarda-se que:
#  12. a Mesa so grava ids oferecidos, «Impact» tira a chave, o anular, o «Como está» e as propostas de cores nao lhe
#      mexem por engano, e dois aparelhos juntam-se pela parte ["estilo","intro","fonte"];
#  13. «ja feita» e o que o montar aceita: as cores, o tamanho, a variante e a letra, e a letra vem do estilo de agora;
#  14. a lista, as mascaras e o corpo da letra da Mesa sao os do render (o round() do Python), e a Mesa avisa a leitura
#      quando o montar avisa;
#  15. o audio_para_mesa.py conhece os nomes e os comentarios das intros com letra, e nao conta como feita uma em que o
#      nome e os metadados dizem letras diferentes;
#  16. a Mesa montada traz a lista com as mascaras, sem ficheiros novos na publicacao.
def teste_letra_da_intro_grava_desfaz_e_junta():
    """A letra do letreiro grava so ids oferecidos, o Impact tira a chave, e o resto do estilo nao lhe mexe.

    O DEFEITO QUE ISTO APANHA: um «impact» gravado (o render via um estilo e o montar escrevia um estilo.json e fazia
    uma intro igual com outro nome), uma letra que a medida recusou ou uma das letras dos textos aceite pela Mesa e
    deitada fora pelo render, uma proposta de cores a tirar a letra (ou a dizer «já feita» de uma combinacao que nao
    esta), o «Como está» a deixa-la, a juncao de dois aparelhos a perde-la, e uma letra que a base tem e esta Mesa nao
    conhece a passar calada.
    """
    if not shutil.which("node"):
        salta("Mesa: a letra da intro grava, desfaz e junta", "sem node neste PC")
        return
    import audio_para_mesa
    import render
    problemas = []
    feitas = audio_para_mesa.intros_feitas()
    if not feitas or not any(x.get("fonte") == "bernard" and x["sem_preto"] for x in feitas):
        salta("Mesa: a letra da intro grava, desfaz e junta", "sem a intro da Bernard feita neste PC")
        return
    bernard = [x for x in feitas if x.get("fonte") == "bernard" and x["sem_preto"]][0]
    base = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "video", "f": "20th Century Fox Intro HD igualado.mp4"},
                                                                {"t": "video", "f": "intro_clara_tiago_5 sem preto igualado.mp4"},
                                                                {"t": "foto", "i": "f01"}]}],
            "atual": "v1", "pessoas": [], "tags": {}}
    mais = ["function estiloPoePaleta(", "function estiloReporParte(", "function estiloVoltarAoMeu(", "function palcoIntroDoEstilo(",
            "function estiloPaletaFeita("]
    js = """
var r = {}, copia = function(){ return est.estilo === undefined ? null : JSON.parse(JSON.stringify(est.estilo)); };
var selos = function(){ return ESTILO_PALETAS.intro.map(function(_p, k){ return estiloPaletaFeita("intro", k); }); };
var ultima = function(){ return mensagens[mensagens.length - 1] || ""; };
var custos = function(){ var c = {}; estiloLetrasDaIntro().forEach(function(f){ c[f.id] = estiloCustoDaLetraIntro(f.id).t; }); return c; };
var textos = function(){ return estiloAvisos("intro").map(function(a){ return [!!a.forte, a.t]; }); };
RENDER_LE = {intros_feitas: %(feitas)s, intro_fonte: true};
r.lista = estiloLetrasDaIntro().map(function(f){ return f.id; });
r.custosHoje = custos();
estiloPoeLetraIntro("bernard");
r.sim = copia(); r.msgSim = ultima(); r.valor = estiloTextoDoValor("intro", "fonte", "bernard");
r.mudancas = estiloMudancas("intro"); r.oQue = estiloIntroOQueMudou();
r.feita = estiloIntroFeita(true); r.custosBernard = custos(); r.avisosBernard = textos();
r.palco = palcoIntroDoEstilo(est.versoes[0].clips[1]);
r.palcoComPreto = palcoIntroDoEstilo({t: "video", f: "intro_clara_tiago_5 igualado.mp4"});
r.selosBernard = selos();
pilhaDesfazer[pilhaDesfazer.length - 1].aoAnular(); r.anulado = copia();
r.selosHoje = selos();
estiloPoeLetraIntro("bernard"); estiloPoeLetraIntro("impact"); r.impact = copia(); r.msgImpact = ultima(); r.selosImpact = selos();
var antes = copia();
r.recusas = [estiloPoe("intro", "fonte", "arial_bold"), estiloPoe("intro", "fonte", "haetten"), estiloPoe("intro", "fonte", "Bernard"),
             estiloPoe("intro", "fonte", 3), estiloPoe("intro", "fonte", "")];
estiloPoeLetraIntro("haetten"); estiloPoeLetraIntro("bebas");
r.depoisDasRecusas = copia(); r.mesmoQueAntes = JSON.stringify(antes) === JSON.stringify(r.depoisDasRecusas);
r.aceites = [estiloPoe("intro", "fonte", " showcard "), estiloLimpo("intro", "fonte", "rockcond"), estiloLimpo("intro", "fonte", "impact")];
r.showcard = copia(); delete est.estilo;
/* as propostas de cores nao mudam a letra, e o «já feita» delas passa a ser com a letra de agora */
estiloPoeLetraIntro("bernard"); estiloPoePaleta("intro", 4);
r.paleta = copia(); r.paletaAtiva = estiloPaletaAtiva("intro", 4); r.msgPaleta = ultima(); r.feitaPreto = estiloIntroFeita(true);
r.custosPreto = custos(); r.avisosPreto = textos(); r.oQuePreto = estiloIntroOQueMudou();
r.propostasComBernard = ESTILO_PALETAS.intro.slice(1).map(function(p){ return !!estiloIntroFeita(true, p.v); });
r.propostasEmImpact = ESTILO_PALETAS.intro.slice(1).map(function(p){ return !!estiloIntroFeita(true, p.v, "impact"); });
r.vermelhaComBernard = !!estiloIntroFeita(true, ESTILO_PALETAS.intro[0].v);
/* «Como está (original)» tira tudo, a letra tambem, e «O teu de há pouco» devolve-a */
estiloReporParte("intro"); r.comoEsta = copia(); estiloVoltarAoMeu("intro"); r.meu = copia();
/* sem a lista das feitas (uma Mesa montada sem ela) as quatro propostas sao em Impact: com outra letra, nada esta feito */
RENDER_LE = {};
est.estilo = {intro: {fonte: "bernard"}}; r.semListaBernard = estiloIntroFeita(true);
delete est.estilo; r.semListaPropostas = ESTILO_PALETAS.intro.slice(1).map(function(p){ return !!estiloIntroFeita(true, p.v); });
/* o render que ainda nao le a letra, e uma letra que a base tem e esta Mesa nao oferece */
RENDER_LE = {intro_fonte: false, intros_feitas: %(feitas)s}; est.estilo = {intro: {fonte: "bernard"}}; r.naoLe = textos();
RENDER_LE = {intro_fonte: true}; est.estilo = {intro: {fonte: "haetten"}};
r.desconhecida = {valor: estiloValor("intro", "fonte"), mudada: estiloParteMudada("intro"), avisos: textos()};
/* uma versao que nao abre com a intro 5 */
est.estilo = {intro: {fonte: "bernard"}}; est.versoes[0].clips = [{t: "foto", i: "f01"}];
r.semIntro5 = {avisos: textos(), custo: estiloCustoDaLetraIntro("bernard")};
console.log(JSON.stringify(r));
""" % {"feitas": json.dumps(feitas)}
    s = _correr_estilo(base, js, problemas, mais=mais)
    if s:
        letras = sorted(render.letras_da_intro().values(), key=lambda e: (e.get("ordem") or 999, e["id"]))
        if s["lista"] != [e["id"] for e in letras] or s["lista"][0] != "impact":
            problemas.append("a lista da Mesa e %s" % s["lista"])
        nova = "nova: cerca de 2 a 3 minutos na montagem"
        if s["custosHoje"].get("impact") != "a intro de hoje" or s["custosHoje"].get("bernard") != "já feita" or \
                any(v != nova for k, v in s["custosHoje"].items() if k not in ("impact", "bernard")):
            problemas.append("o custo de cada letra com as cores de hoje: %s" % s["custosHoje"])
        sim = {"intro": {"fonte": "bernard"}}
        if s["sim"] != sim or s["valor"] != "Bernard MT Condensed" or s["mudancas"] != ["a letra do letreiro"] or s["oQue"] != "a letra":
            problemas.append("escolher a Bernard gravou %s, le-se %r, %s, %r" % (s["sim"], s["valor"], s["mudancas"], s["oQue"]))
        if "81%" not in s["msgSim"] or "já está feita" not in s["msgSim"]:
            problemas.append("a mensagem da Bernard: %r" % s["msgSim"])
        if not s["feita"] or s["feita"]["f"] != bernard["f"] or s["feita"]["nome"] != "O vermelho de hoje, em Bernard MT Condensed":
            problemas.append("a Bernard nas cores de hoje nao conta como feita: %s" % s["feita"])
        if any(v != nova for k, v in s["custosBernard"].items() if k not in ("impact", "bernard")) or \
                s["custosBernard"]["bernard"] != "já feita" or s["custosBernard"]["impact"] != "a intro de hoje":
            problemas.append("o custo de cada letra com a Bernard escolhida: %s" % s["custosBernard"])
        if not any("já está feita" in t and "Bernard" in t for _f, t in s["avisosBernard"]) or \
                not any("vê-se 81%" in t for _f, t in s["avisosBernard"]) or any(f for f, _t in s["avisosBernard"]):
            problemas.append("os avisos da Bernard feita: %s" % s["avisosBernard"])
        if not s["palco"] or s["palco"]["f"] != bernard["f"] or not s["palco"]["feita"]:
            problemas.append("o palco nao toca a intro da Bernard: %s" % s["palco"])
        # O «já feita» das propostas e com a letra de agora (revisor do browser, 2 de outubro a noite: escolhida a Bernard,
        # as quatro propostas continuavam a dizer «já feita», que so o sao em Impact; o selo pinta-se no estiloAtualiza)
        selos_impact = [False] + [True] * (len(s["selosImpact"]) - 1)
        if (s["selosBernard"] != [True] + [False] * (len(s["selosBernard"]) - 1) or s["selosImpact"] != selos_impact
                or s["selosHoje"] != selos_impact):
            problemas.append("o «já feita» das propostas: com a Bernard %s, em Impact %s e %s" % (s["selosBernard"], s["selosImpact"], s["selosHoje"]))
        if not s["palcoComPreto"] or s["palcoComPreto"]["f"] or s["palcoComPreto"]["feita"]:
            problemas.append("a intro com o preto so tem a Bernard feita sem ele: %s" % s["palcoComPreto"])
        if s["anulado"] is not None or s["impact"] is not None or "Impact, como está" not in s["msgImpact"]:
            problemas.append("o anular deu %s e o Impact %s (%r)" % (s["anulado"], s["impact"], s["msgImpact"]))
        if s["recusas"] != [False] * 5 or not s["mesmoQueAntes"]:
            problemas.append("letras que nao sao oferecidas entraram: %s, %s" % (s["recusas"], s["depoisDasRecusas"]))
        if s["aceites"] != [True, "rockcond", "impact"] or s["showcard"] != {"intro": {"fonte": "showcard"}}:
            problemas.append("as oferecidas nao entraram como o render as guarda: %s %s" % (s["aceites"], s["showcard"]))
        preto = {"intro": {"fonte": "bernard", "fundo": "#0C0B09", "letra": "#D4AA5A", "papel": "#EEDCAE", "tinta": "#4A3B24"}}
        if s["paleta"] != preto or not s["paletaAtiva"] or s["feitaPreto"] is not None:
            problemas.append("a proposta Preto e dourado com a Bernard: %s, ativa %s, feita %s" % (s["paleta"], s["paletaAtiva"], s["feitaPreto"]))
        if "Bernard" not in s["msgPaleta"] or "ainda não está feita" not in s["msgPaleta"] or "2 a 3 minutos" not in s["msgPaleta"]:
            problemas.append("a mensagem da proposta com a Bernard: %r" % s["msgPaleta"])
        if s["custosPreto"]["impact"] != "já feita" or s["custosPreto"]["bernard"] != nova:
            problemas.append("o custo com o Preto e dourado: %s" % s["custosPreto"])
        if not any("A letra Bernard MT Condensed com estas cores ainda não está feita" in t and "2 a 3 minutos" in t
                   for _f, t in s["avisosPreto"]) or s["oQuePreto"] != "as cores e a letra":
            problemas.append("os avisos do Preto e dourado com a Bernard: %s (%r)" % (s["avisosPreto"], s["oQuePreto"]))
        if s["propostasComBernard"] != [False] * 4 or s["propostasEmImpact"] != [True] * 4 or not s["vermelhaComBernard"]:
            problemas.append("as propostas com a Bernard %s, em Impact %s, a vermelha %s"
                             % (s["propostasComBernard"], s["propostasEmImpact"], s["vermelhaComBernard"]))
        if s["comoEsta"] is not None or s["meu"] != preto:
            problemas.append("«Como está» deixou %s e o teu de ha pouco voltou %s" % (s["comoEsta"], s["meu"]))
        if s["semListaBernard"] is not None or s["semListaPropostas"] != [True] * 4:
            problemas.append("sem a lista das feitas: a Bernard %s, as propostas %s" % (s["semListaBernard"], s["semListaPropostas"]))
        if not any(f and "ainda não chega ao filme" in t for f, t in s["naoLe"]):
            problemas.append("com o render sem a letra, a Mesa nao diz que nao chega ao filme: %s" % s["naoLe"])
        d = s["desconhecida"]
        if d["valor"] != "impact" or d["mudada"] or not any(f and "haetten" in t for f, t in d["avisos"]):
            problemas.append("uma letra que a Mesa nao oferece: %s" % d)
        if not any(f and "não abre com a intro 5" in t and "a letra" in t for f, t in s["semIntro5"]["avisos"]) or \
                not s["semIntro5"]["custo"].get("forte"):
            problemas.append("uma versao sem a intro 5: %s" % s["semIntro5"])
        # o que a Mesa grava e o que o render guarda, sem avisos
        for x in (sim, preto, s["showcard"]):
            av = []
            if render.normalizar_estilo(x, av) != x or av:
                problemas.append("o render limpa %s de outra maneira: %s %s" % (x, render.normalizar_estilo(x), av))
    # A JUNCAO POR PARTES: a letra e uma parte propria
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}],
          "pessoas": [], "tags": {}, "atual": "v1", "estilo": {"intro": {"fundo": "#0C0B09"}},
          "quando": "2026-10-02T21:00:00Z", "rev": 5, "pagina": "2026-10-02"}
    corpo_js = """
var r = {}, B0 = %s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
/* A. aqui a letra, la uma cor da intro: juntam-se */
abrir(B0); est.estilo = {intro: {fundo: "#0C0B09", fonte: "bernard"}};
var j = juntarComBase(com({estilo: {intro: {fundo: "#0C0B09", letra: "#D4AA5A"}}, rev: 6}));
r.A = {ok: j.ok, estilo: copia(est.estilo), partes: Object.keys(partesDe(corpo())).filter(function(k){ return k.indexOf("fonte") >= 0; })};
/* B. letras diferentes nos dois: o conflito de sempre */
abrir(B0); est.estilo = {intro: {fundo: "#0C0B09", fonte: "bernard"}};
j = juntarComBase(com({estilo: {intro: {fundo: "#0C0B09", fonte: "showcard"}}, rev: 6}));
r.B = {ok: j.ok, choque: j.choque};
/* C. uma Mesa de hoje que ainda nao conhece a letra copia o est.estilo inteiro e muda uma cor: a letra fica */
abrir(com({estilo: {intro: {fundo: "#0C0B09", fonte: "bernard"}}}));
j = juntarComBase(com({estilo: {intro: {fundo: "#1A2C4E", fonte: "bernard"}}, rev: 6}));
r.C = {ok: j.ok, estilo: copia(est.estilo)};
/* D. uma Mesa antiga (sem pagina, sem o estilo) grava: a letra volta a base */
abrir(com({estilo: {intro: {fonte: "bernard"}}}));
j = juntarComBase(com({estilo: undefined, pagina: undefined, rev: 6}));
r.D = {ok: j.ok, repostos: j.repostos, estilo: corpo().estilo};
console.log(JSON.stringify(r));
""" % json.dumps(B0)
    r = _correr_js(DECLARACOES_JUNTAR, FUNCOES_JUNTAR, PRELUDE_JUNTAR, corpo_js, problemas)
    if r:
        if not r["A"]["ok"] or r["A"]["estilo"] != {"intro": {"fundo": "#0C0B09", "fonte": "bernard", "letra": "#D4AA5A"}} \
                or r["A"]["partes"] != ['["estilo","intro","fonte"]']:
            problemas.append("a letra aqui e uma cor la: %s" % r["A"])
        if r["B"]["ok"] or r["B"]["choque"] != ["estilo"]:
            problemas.append("letras diferentes nos dois: %s" % r["B"])
        if not r["C"]["ok"] or r["C"]["estilo"] != {"intro": {"fundo": "#1A2C4E", "fonte": "bernard"}}:
            problemas.append("a Mesa que nao conhece a letra: %s" % r["C"])
        if not r["D"]["ok"] or r["D"]["repostos"] != ["estilo"] or r["D"]["estilo"] != {"intro": {"fonte": "bernard"}}:
            problemas.append("a Mesa antiga: %s" % r["D"])
    verifica("Mesa: a letra da intro grava, desfaz e junta", not problemas, "; ".join(problemas)[:600] if problemas else
             "so ids oferecidos, o Impact tira a chave, ja feita com a letra de agora, propostas, como esta, o render "
             "ainda sem ela, a desconhecida, e quatro juncoes")


def teste_letra_da_intro_igual_ao_render():
    """A lista das letras, as mascaras, o corpo e o aviso da leitura da Mesa sao os do render e do montar.

    O DEFEITO QUE ISTO APANHA: a Mesa a oferecer uma letra que o render recusa (ou ao contrario), noutra ordem ou com
    outra percentagem; uma mascara que nao e o letreiro que o filme desenha (outra letra, outro corpo, ou o Impact a
    fingir de Bernard porque a letra saiu do PC); o corpo da letra com o Math.round, que manda as metades para cima
    e o render para o par (21 tamanhos de diferenca), e a Mesa calada num tamanho em que o montar diz que a letra nao
    se le; a familia da intro 5 da Mesa diferente da do montar; o RENDER_LE.intro_fonte a mentir.
    """
    if not shutil.which("node"):
        salta("Mesa: a letra da intro igual ao render", "sem node neste PC")
        return
    import base64
    import contextlib
    import math
    import gerar_mesa
    import intro_flipbook
    import linha_tempo
    import montar_da_mesa
    import render
    from PIL import Image
    problemas = []
    with contextlib.redirect_stdout(io.StringIO()):
        F = gerar_mesa.fontes_intro_para_mesa()
    letras = sorted(render.letras_da_intro().values(), key=lambda e: (e.get("ordem") or 999, e["id"]))
    if not F or [x["id"] for x in F["letras"]] != [e["id"] for e in letras]:
        problemas.append("a lista da Mesa %s nao e a do render %s" % (F and [x["id"] for x in F["letras"]], [e["id"] for e in letras]))
        F = None
    bytes_mascaras = 0
    if F:
        for x, e in zip(F["letras"], letras):
            for k in gerar_mesa.CAMPOS_DA_LETRA_DA_INTRO:
                if x.get(k) != e.get(k):
                    problemas.append("%s.%s e %r na Mesa e %r na medida" % (e["id"], k, x.get(k), e.get(k)))
            if not x.get("em_disco") or not x.get("mascara"):
                problemas.append("a letra %s sem mascara ou fora do PC" % e["id"])
                continue
            png = base64.b64decode(x["mascara"].split(",", 1)[1])
            bytes_mascaras += len(x["mascara"])
            im = Image.open(io.BytesIO(png))
            with contextlib.redirect_stdout(io.StringIO()):
                m = intro_flipbook.letreiro(int(intro_flipbook.L * 0.86), None, e["id"])
            certa = m.resize((intro_flipbook.L // 2, intro_flipbook.A // 2), Image.LANCZOS)
            if im.mode != "LA" or im.size != certa.size or im.getchannel("A").tobytes() != certa.tobytes() or \
                    im.getchannel("L").getextrema() != (255, 255):
                problemas.append("a mascara da %s nao e o letreiro do render (%s %s)" % (e["id"], im.mode, im.size))
            if x["area_mascara"] != e["area_px"] or sum(m.histogram()[129:]) != e["area_px"]:
                problemas.append("a %s tem %s px e a medida %s" % (e["id"], x["area_mascara"], e["area_px"]))
    # o corpo da letra em cada tamanho da Mesa, e o aviso da leitura, com uma medida falsa que faz avisar
    pasta = tempfile.mkdtemp(prefix="teste_letra_intro_mesa_")
    guardado = render.FONTES_DA_INTRO
    try:
        dados = json.load(io.open(render.FONTES_DA_INTRO, encoding="utf-8"))
        for e in dados["letras"]:
            if e["id"] == "bernard":
                e["corpo_minimo"] = 200          # a 132 e a 199 fica abaixo; a 200 e a 288 nao
            if e["id"] == "gillultra":
                e["corpo_minimo"] = 113          # a 135 o render da 112 (o par) e o Math.round daria 113
        falsa = os.path.join(pasta, "fontes_intro.json")
        with io.open(falsa, "w", encoding="utf-8") as fh:
            json.dump(dados, fh, ensure_ascii=False)
        render.FONTES_DA_INTRO = falsa
        with contextlib.redirect_stdout(io.StringIO()):
            _FONTES_INTRO["ensaio"] = gerar_mesa.fontes_intro_para_mesa(mascaras=False)
        casos = [{"intro": {"fonte": f, "tamanho": t}} for f, t in
                 (("bernard", 132), ("bernard", 199), ("bernard", 200), ("bernard", 288), ("gillultra", 135),
                  ("gillultra", 136), ("gillultra", 147), ("playbill", 198), ("rockcond", 309))]
        js = """
var tabela = {}, casos = %s, r = {};
estiloLetrasDaIntro().forEach(function(f){ var l = []; for(var T = 132; T <= 309; T++) l.push(estiloCorpoDaLetraDaIntro(f, T)); tabela[f.id] = l; });
r.tabela = tabela;
r.familia = String(ESTILO_INTRO_FAMILIA.source);
r.avisos = casos.map(function(c){ est.estilo = c; return estiloAvisos("intro").map(function(a){ return [!!a.forte, a.t]; }); });
console.log(JSON.stringify(r));
""" % json.dumps(casos)
        s = _correr_estilo({"versoes": []}, js, problemas)
        if s:
            difere_do_math_round = 0
            for e in render.letras_da_intro().values():
                certos = [render.corpo_da_letra_da_intro(e, T) for T in range(132, 310)]
                if s["tabela"].get(e["id"]) != certos:
                    problemas.append("o corpo da %s difere do render" % e["id"])
                difere_do_math_round += sum(1 for T in range(132, 310)
                                            if int(math.floor(T * float(e["corpo_que_cabe"]) / 288 + 0.5)) != render.corpo_da_letra_da_intro(e, T))
            # sao 19 (a gillultra de 135 a 303 de 12 em 12, a bahncond e a agency a 216, a playbill a 198 e a 270; a nota
            # do render dizia 21): sem nenhum, o teste deixava de ver as metades
            if not difere_do_math_round:
                problemas.append("nenhum tamanho em que o Math.round difere do render: o teste nao ve as metades")
            com_aviso = []
            for caso, textos in zip(casos, s["avisos"]):
                limpo = render.normalizar_estilo(caso)
                do_montar = [a for a in montar_da_mesa.avisos_do_estilo(limpo, render, linha_tempo)
                             if a.startswith("estilo: o letreiro da intro em")]
                da_mesa = [t for f, t in textos if f and t.startswith("O letreiro em ")]
                if do_montar:
                    com_aviso.append("%s a %d" % (caso["intro"]["fonte"], caso["intro"]["tamanho"]))
                if bool(do_montar) != bool(da_mesa):
                    problemas.append("%s: a Mesa avisa %s e o montar %s" % (json.dumps(caso), da_mesa, do_montar))
                elif do_montar:
                    numeros = re.findall(r"\d+", do_montar[0].split(" em ", 1)[1])
                    if re.findall(r"\d+", da_mesa[0].split(" em ", 1)[1])[:3] != numeros[:3]:
                        problemas.append("%s: a Mesa diz %r e o montar %r" % (json.dumps(caso), da_mesa[0], do_montar[0]))
            # a medida falsa faz o montar avisar nestes tres, e so nestes: a gillultra a 135 e a metade que o
            # Math.round punha do outro lado do minimo
            if com_aviso != ["bernard a 132", "bernard a 199", "gillultra a 135"]:
                problemas.append("o montar avisou %s com a medida de ensaio" % com_aviso)
            if s["familia"] != montar_da_mesa.INTRO_DA_FAMILIA.pattern:
                problemas.append("a familia da intro 5 da Mesa %r nao e a do montar %r" % (s["familia"], montar_da_mesa.INTRO_DA_FAMILIA.pattern))
    finally:
        render.FONTES_DA_INTRO = guardado
        _FONTES_INTRO.pop("ensaio", None)
        shutil.rmtree(pasta, ignore_errors=True)
    le = gerar_mesa.o_que_o_render_le()
    certo = bool((render.normalizar_estilo({"intro": {"fonte": "bernard"}}, []).get("intro") or {}).get("fonte"))
    if le.get("intro_fonte") is not certo:
        problemas.append("o RENDER_LE.intro_fonte e %r e o render diz %r" % (le.get("intro_fonte"), certo))
    verifica("Mesa: a letra da intro igual ao render", not problemas, "; ".join(problemas)[:600] if problemas else
             "%d letras na ordem da medida, as mascaras ao pixel (%.0f KB), o corpo em 178 tamanhos com o round do Python "
             "(%d metades), o aviso da leitura como o montar, a familia e o RENDER_LE"
             % (len(letras), bytes_mascaras / 1024.0, locals().get("difere_do_math_round", 0)))


def teste_letra_da_intro_nas_intros_feitas():
    """O audio_para_mesa.py conhece as intros com letra, pelo nome e pelos metadados, e so conta as que batem.

    O DEFEITO QUE ISTO APANHA: a expressao de antes ignorava em silencio a intro da Bernard (o palco nao a tinha e a
    Mesa dizia que custava a montagem), e uma intro com uma letra no nome e outra nos metadados (ou nenhuma) contava
    como feita, e o montar, que a procura pelo nome do resumo dos metadados, refazia-a.
    """
    import audio_para_mesa
    import intro_flipbook
    import render
    problemas = []
    paletas = [None] + [{k: render.cor_rgb(v) for k, v in zip(("fundo", "letra", "papel", "tinta"), x[1:])}
                        for x in INTROS_DE_2_DE_OUTUBRO[1:]]
    contados = 0
    for fonte in [None] + sorted(render.letras_da_intro()):
        for cores in paletas:
            for sp in (False, True):
                if not intro_flipbook.tem_paleta(cores, None, fonte):
                    continue
                nome = intro_flipbook.nome_da_intro(cores, None, sp, fonte).replace(".mp4", " igualado.mp4")
                n = audio_para_mesa.INTRO_IGUALADA.match(nome)
                c = audio_para_mesa.PALETA_NO_COMENTARIO.match(intro_flipbook.comentario_da_paleta(cores, None, True, fonte))
                letra = fonte if fonte not in (None, "impact") else None
                if not n or bool(n.group(1)) is not sp or n.group(2) != letra or not c or c.group(6) != letra:
                    problemas.append("%s: nome %s, comentario %s" % (nome, n and n.groups(), c and c.groups()))
                contados += 1
    # numa pasta de ensaio, quatro ficheiros pequenos com os metadados escritos pelo ffmpeg
    pasta = tempfile.mkdtemp(prefix="teste_intros_com_letra_")
    try:
        vinho = paletas[1]
        casos = {"bate": (intro_flipbook.nome_da_intro(None, None, True, "bernard"), intro_flipbook.comentario_da_paleta(None, None, True, "bernard")),
                 "sem_letra_nos_metadados": (intro_flipbook.nome_da_intro(vinho, None, True, "showcard"), intro_flipbook.comentario_da_paleta(vinho, None, True)),
                 "letra_so_nos_metadados": (intro_flipbook.nome_da_intro(vinho, None, True), intro_flipbook.comentario_da_paleta(vinho, None, True, "agency")),
                 "de_antes": (intro_flipbook.nome_da_intro(vinho, None, False), intro_flipbook.comentario_da_paleta(vinho, None, True))}
        ff = render.ffmpeg()
        for chave, (nome, comentario) in casos.items():
            destino = os.path.join(pasta, nome.replace(".mp4", " igualado.mp4"))
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=16x16:d=0.2",
                            "-metadata", "comment=" + comentario, "-c:v", "libx264", "-pix_fmt", "yuv420p", destino],
                           capture_output=True, text=True)
        saida = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(saida):
            feitas = audio_para_mesa.intros_feitas(pasta)
        por_nome = {x["f"]: x for x in feitas or []}
        bate = casos["bate"][0].replace(".mp4", " igualado.mp4")
        if (por_nome.get(bate) or {}).get("fonte") != "bernard" or not por_nome.get(bate, {}).get("sem_preto"):
            problemas.append("a intro da Bernard que bate nao conta: %s" % sorted(por_nome))
        errados = [f for f in por_nome if "showcard" in f]
        if errados or "showcard" not in saida.getvalue():
            problemas.append("a showcard sem a letra nos metadados contou, ou calada: %s" % errados)
        if any(x.get("fonte") == "agency" for x in por_nome.values()):
            problemas.append("a letra so nos metadados contou: %s" % sorted(por_nome))
        antes = [x for x in por_nome.values() if x.get("fonte") == "impact"]
        if len(antes) != 1:
            problemas.append("a intro de antes, sem letra, devia contar em Impact: %s" % sorted(por_nome))
        if len(por_nome) != 2:
            problemas.append("contaram %d intros, e sao 2 as que batem: %s" % (len(por_nome), sorted(por_nome)))
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
    # e as verdadeiras: a da Bernard esta la, com a letra, e com o comentario que o montar procura
    reais = audio_para_mesa.intros_feitas() or []
    b = [x for x in reais if x.get("fonte") == "bernard"]
    if b and intro_flipbook.nome_da_intro({k: render.cor_rgb(b[0][k]) for k in ("fundo", "letra", "papel", "tinta")},
                                          b[0]["tamanho"], b[0]["sem_preto"], "bernard").replace(".mp4", " igualado.mp4") != b[0]["f"]:
        problemas.append("a intro da Bernard em disco nao tem o nome que o montar procura: %s" % b[0])
    if any("fonte" not in x for x in reais):
        problemas.append("ha intros feitas sem a letra: %s" % [x["f"] for x in reais if "fonte" not in x])
    verifica("Mesa: as intros feitas com letra", not problemas, "; ".join(problemas)[:500] if problemas else
             "%d nomes e comentarios com e sem letra; numa pasta de ensaio so as 2 que batem; %d feitas em disco, %d com letra"
             % (contados, len(reais), len(b)))


def teste_mesa_montada_traz_a_letra_da_intro():
    """A Mesa montada traz o window.FONTES_INTRO com as mascaras, uma vez, e o RENDER_LE diz que o render a le.

    O DEFEITO QUE ISTO APANHA: uma Mesa montada sem a lista (a aba Intro so com o Impact, sem ninguem saber porque),
    as mascaras em ficheiros ao lado (contam no limite de 256 ficheiros da publicacao e chegam depois da pagina), e a
    Mesa a dizer que a letra nao chega ao filme quando o render ja a le.
    """
    problemas = []
    montada = _montar_mesa_a_parte("mesa_1002_letra_intro_")
    m = re.findall(r"<script>\nwindow\.FONTES_INTRO = (.*?);\n</script>\n<script>\nwindow\.FONTES = ", montada, re.S)
    kb = 0.0
    if len(m) != 1:
        problemas.append("o window.FONTES_INTRO aparece %d vezes antes das letras do Estilo" % len(m))
    else:
        F = json.loads(m[0].replace("<\\/", "</"))
        if not F or len(F["letras"]) < 2 or F["letras"][0]["id"] != "impact":
            problemas.append("o window.FONTES_INTRO nao traz as letras: %s" % (F and [x["id"] for x in F["letras"]]))
        else:
            sem = [x["id"] for x in F["letras"] if not (x.get("mascara") or "").startswith("data:image/png;base64,")]
            if sem:
                problemas.append("letras sem a mascara como data URI: %s" % sem)
            kb = sum(len(x.get("mascara") or "") for x in F["letras"]) / 1024.0
            if kb > 400:
                problemas.append("as mascaras pesam %.0f KB na pagina" % kb)
    r = re.search(r"window\.RENDER_LE = (\{[^\n]*\});", montada)
    le = json.loads(r.group(1)) if r else {}
    if le.get("intro_fonte") is not True:
        problemas.append("o RENDER_LE.intro_fonte e %r" % le.get("intro_fonte"))
    if not any((x or {}).get("fonte") == "bernard" for x in (le.get("intros_feitas") or [])):
        problemas.append("o RENDER_LE.intros_feitas nao traz a da Bernard")
    if re.search(r'["\'](?:mascaras|letras_intro)/[^"\']+\.png', montada):
        problemas.append("a pagina pede mascaras em ficheiros ao lado")
    verifica("Mesa: a Mesa montada traz a letra da intro", not problemas, "; ".join(problemas)[:300] if problemas else
             "%d letras com a mascara dentro da pagina (%.0f KB, 0 ficheiros novos), o render le a letra, a Bernard feita"
             % (len(F["letras"]) if len(m) == 1 else 0, kb))


# ------------------------------------------------- os avisos dos caracteres iguais ao render (2 de outubro, a noite)
MARCAS_VALIDADOR = ("/* <<< REGRAS PURAS DO VALIDADOR, PRINCIPIO >>> */", "/* <<< REGRAS PURAS DO VALIDADOR, FIM >>> */")
# o que o resto do bloco das regras puras chama (o testes.py leva as mesmas)
APOIO_VALIDADOR = ["function eGrupo(", "function modoTextos(", "function tamanhoValido(", "function textosDasFotos(",
                   "function temTextosFotos("]
FUNCOES_CARACTERES = ["function parteDoClip(", "function letraDoTexto(", "function textosComLetra(", "function caixasDoClip("]
FUNCOES_CRED_VALIDAR = ["function credTextosParaValidar(", "function credGrauDaLargura(", "function validarCreditos(",
                        "function credAvisoDosCaracteres(", "function credCargo(", "function credTitulo(", "function credData(",
                        "function credGrupoTexto(", "function credOmissoes(",
                        # os cargos que valem sao os do credLayout (2 de outubro, a noite: ate 8, sem os vazios)
                        "function credLayout(", "function credContas(", "function credFotos(", "function credMarcadas(",
                        "function credPid(", "function credVersao(", "function credMedida(", "function credSemAcentos(",
                        "function credGrupoPorEtiqueta(", "function credPessoasDoQuem("]
# OS TEXTOS DE ENSAIO: cada caso do texto_emojis (o emoji simples, os equivalentes, os invisiveis, os seletores, as
# sequencias de cada tipo, os simbolos de uma so cor, os escuros, o que nenhuma letra tem) e as fronteiras do laco
# (um ZWJ no fim, antes de um espaco, entre letras; um tom e um indicador sozinhos; a mesma sequencia duas vezes)
TEXTOS_CARACTERES = [
    "O pai ficou assim \U0001F62E quando soube do preço",
    "Audio\u2011Visual Operations Maestro e o h\u2010fen",
    "Parabéns \U0001F44D\U0001F3FD e \U0001F468\u200d\U0001F469\u200d\U0001F467 e \U0001F3F3\ufe0f\u200d\U0001F308",
    "Portugal \U0001F1F5\U0001F1F9 1\ufe0f\u20e3 \U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
    "Música \U0001F3B5 \U0001F5A4 \U0001F3A9 \U0001F393 \U0001F499 \U0001F48D",
    "Coração \u2665 e \u2665\ufe0f e \u2764 e \u2764\ufe0f e quadrado \u25aa e \u25aa\ufe0f e \u2b1b",
    "Visto \u2713 \u2610 \u2192 \u2190 \u2714",
    "Privado \ue000 e \uffff e \u0378",
    "Invisíveis\u2060aqui\ufeffe\u200bali",
    "Seletor de texto \u263a\ufe0e e \u263a\ufe0f e \u263a",
    "dois  espaços \U0001F62E\U0001F62E \U0001F62E",
    "ZWJ no fim \U0001F44D\u200d",
    "ZWJ antes do espaço \U0001F44D\u200d fim",
    "ZWJ entre letras a\u200db",
    "tom sozinho \U0001F3FD e indicador sozinho \U0001F1F5 e \U0001F1F5\U0001F1F9\U0001F1F5",
    "tecla #\ufe0f\u20e3 *\u20e3 e a mesma \U0001F44D\U0001F3FD outra vez \U0001F44D\U0001F3FD",
    "Grego \u03a9 cirílico \u0416 hebraico \u05d0 árabe \u0627 chinês \u4e2d coreano \ud55c",
    "Espaços do Python\u2003e\u3000e\u00a0e\u1680fim",
    "\U0001F600\U0001F603\U0001F604\U0001F601\U0001F606 \U0001F923 \U0001F970 \U0001FAE0 \U0001FA77",
]


def _regras_do_validador(html, problemas):
    a, b = MARCAS_VALIDADOR
    if html.count(a) != 1 or html.count(b) != 1:
        problemas.append("os marcadores das regras puras aparecem %d e %d vezes" % (html.count(a), html.count(b)))
        return ""
    return html[html.index(a):html.index(b) + len(b)]


def _node_programa(programa, problemas):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(programa)
        caminho = fh.name
    try:
        r = subprocess.run([shutil.which("node"), caminho], capture_output=True, text=True, encoding="utf-8", timeout=600)
    finally:
        os.remove(caminho)
    if r.returncode != 0:
        problemas.append("o node parou: " + _erro_do_node(r))
        return None
    return json.loads(r.stdout)


def _sem_acentos(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _letras_abertas(letras):
    """{id: ImageFont} das letras da tabela, abertas como o render as abre (o Arial Bold pelo FONTE_TEXTO)."""
    import render
    from PIL import ImageFont
    return {i: (ImageFont.truetype(render.FONTE_TEXTO, 46) if i == render.LETRA_OMISSAO
                else render.abrir_letra(i, 46, avisar=False)) for i in letras}


def _tipos_do_render(texto, fonte):
    """[tipo] dos avisos do texto_emojis.avisos_do_texto(), pela ordem: caixa, sequencia, escuro."""
    import texto_emojis
    tipos = []
    for a in texto_emojis.avisos_do_texto("o texto", texto, fonte):
        tipos.append("caixa" if "caixa vazia" in a else "sequencia" if "nao junta" in a else
                     "escuro" if "escuro" in a else "?")
    return tipos


def _correr_validador(est, corpo_js, problemas, letras, mais=()):
    """As regras puras do Validar, as funcoes dos caracteres e as do estilo (para a letra de cada texto, a de
    verdade), no node, com o LETRAS_RENDER que se der (None: a regra de reserva)."""
    import gerar_mesa
    html = io.open(EDITOR, encoding="utf-8").read()
    regiao = _regras_do_validador(html, problemas)
    blocos = "\n".join([_declaracao(html, m, problemas) for m in DECLARACOES_ESTILO] +
                       [_bloco(html, m, problemas) for m in FUNCOES_ESTILO + APOIO_VALIDADOR + FUNCOES_CARACTERES + list(mais)])
    if problemas:
        return None
    prelude = PRELUDE_ESTILO % {"fontes": json.dumps(gerar_mesa.fontes_para_mesa(), ensure_ascii=False),
                                "fontes_intro": json.dumps(_fontes_intro_de_ensaio(), ensure_ascii=False),
                                "est": json.dumps(est, ensure_ascii=False)}
    prelude += "\nvar TT_OMISSAO = 46, TT_MIN = 28, TT_MAX = 90, MUS = [];\nvar LETRAS_RENDER = %s;\n" % json.dumps(letras)
    return _node_programa('"use strict";\n' + prelude + "\n" + regiao + "\n" + blocos + "\n" + corpo_js, problemas)


def teste_validar_caracteres_como_o_render():
    """O Validar marca um caracter como o render.caracteres_sem_letra(): so o que nem a letra nem a de emojis desenham.

    O PEDIDO: o Tiago escolheu que o filme desenhe os emojis a cores (render.texto_emojis). O Validar (forasDaLetra,
    VAL_LETRA) marcava «Está mal» qualquer emoji, que ate entao saia numa caixa vazia. Compara-se, para cada letra que a
    Mesa pode dar ao texto (as de data/fontes.json que abrem neste PC), cada ponto de codigo de todas essas letras e da
    Segoe UI Emoji, 3000 tirados ao acaso do Unicode inteiro e os da montagem dele, com o texto_emojis.sem_letra() da
    mesma letra aberta como o render a abre. E os textos de ensaio, um a um: a caixa vazia, as sequencias que a Pillow
    sem o raqm nao junta (com a frase do SAI), os emojis escuros (com o contraste escrito como o render) e os graus.
    Sem a tabela, a regra de reserva tem de dar o mesmo que o render nos caracteres que o testes.py confere.
    """
    if not shutil.which("node"):
        salta("Mesa: os caracteres do Validar como o render", "sem node neste PC")
        return
    import random
    import unicodedata
    import caracteres_para_mesa as cpm
    import render
    import texto_emojis
    problemas = []
    L = cpm.letras_do_render()
    fontes = _letras_abertas(L["letras"])
    if any(f is None for f in fontes.values()):
        problemas.append("letras da tabela que o render nao abre: %s" % [i for i, f in fontes.items() if f is None])
    # o universo: os cmap de todas, a Segoe, 3000 ao acaso, os de controlo e os da montagem
    universo = set(cpm.cmap(texto_emojis.LETRA_EMOJIS))
    for f in fontes.values():
        if f is not None:
            universo |= cpm.cmap(f.path, f.index)
    atribuidos = [c for c in range(0x110000) if unicodedata.category(chr(c)) != "Cs"]
    universo |= set(random.Random(1002).sample(atribuidos, 3000))
    universo |= set(range(0x01, 0x20)) | {0xffff, 0xfffe, 0xe000, 0xf8ff, 0x10ffff, 0x0378}
    estado = os.path.join(REPO, "data", "mesa_estado.json")
    confere = set(" .,;:!?'\"()-–—…/&@#%€$ªº+*=<>|_~^`0123456789") | \
        set("AaÀàÁáÂâÃãÇçÉéÊêÍíÓóÔôÕõÚúÜüÑñŁłČčŠšŽžØøÅå") | set("\U0001F62E\U0001F389\u2764")
    if os.path.exists(estado):
        for v in json.load(open(estado, encoding="utf-8")).get("versoes", []):
            for c in v.get("clips", []):
                for t in [c.get("x")] + list(c.get("xf") or []):
                    if isinstance(t, str):
                        universo |= {ord(ch) for ch in t}
                        if c.get("t") not in ("contador", "marcos"):
                            confere |= set(t)
    for t in TEXTOS_CARACTERES:
        universo |= {ord(ch) for ch in t}
    universo |= {ord(ch) for ch in confere}
    universo = sorted(c for c in universo if not 0xD800 <= c <= 0xDFFF and c != 0)
    chars = [chr(c) for c in universo]
    ids = sorted(L["letras"])
    saida = _correr_validador({}, """
var CH = %s, IDS = %s, TX = %s;
var o = {fora: {}, textos: [], constantes: {sai: VAL_SAI, ordem: VAL_ORDEM_DAS_PARTES, equivalentes: VAL_EQUIVALENTES,
         espacos: []}};
IDS.forEach(function(id){ var l = []; CH.forEach(function(ch, k){ if(forasDaLetra(ch, id).length) l.push(k); }); o.fora[id] = l; });
for(var cp = 0; cp < 0x110000; cp++) if(valEspaco(cp)) o.constantes.espacos.push(cp);
IDS.forEach(function(id){
  TX.forEach(function(t){
    o.textos.push({id: id, fora: forasDaLetra(t, id), seqs: sequenciasDoTexto(t).map(function(q){ return [q.seq, q.sai]; }),
                   escuros: emojisEscurosDoTexto(t, id).map(function(q){ return [q.emoji, q.contraste]; }),
                   avisos: avisosDosCaracteres(t, id, "Arial Bold").map(function(q){ return [q.grau, q.tipo]; })});
  });
});
/* SEM A TABELA: a regra de reserva */
LETRAS_RENDER = null;
o.reserva = CH.map(function(ch){ return forasDaLetra(ch).length > 0; });
o.reservaEmoji = forasDaLetra("O pai ficou assim \\uD83D\\uDE2E quando soube do preço");
process.stdout.write(JSON.stringify(o));
""" % (json.dumps(chars, ensure_ascii=False), json.dumps(ids), json.dumps(TEXTOS_CARACTERES, ensure_ascii=False)),
        problemas, L)
    n_comparados = n_textos = reserva_difere = 0
    if saida:
        # 1. AS CONSTANTES SAO AS DO texto_emojis
        k = saida["constantes"]
        if {p: _sem_acentos(s) for p, s in k["sai"].items()} != texto_emojis.SAI:
            problemas.append("o VAL_SAI nao e o texto_emojis.SAI (sem os acentos)")
        if tuple(k["ordem"]) != texto_emojis.ORDEM_DAS_PARTES:
            problemas.append("o VAL_ORDEM_DAS_PARTES nao e o do texto_emojis")
        if {chr(int(c)): v for c, v in k["equivalentes"].items()} != texto_emojis.EQUIVALENTES:
            problemas.append("os VAL_EQUIVALENTES nao sao os render.EQUIVALENTES")
        if k["espacos"] != [c for c in range(0x110000) if chr(c).isspace()]:
            problemas.append("o valEspaco nao e o str.isspace() do Python")
        # 2. CARACTER A CARACTER, LETRA A LETRA: o Arial Bold no universo inteiro, as outras em 2500 dele tirados ao
        # acaso (cada um custa uma medida da Pillow por letra) e nos dos textos
        dos_textos = {j for j, ch in enumerate(chars) if any(ch in t for t in TEXTOS_CARACTERES) or ch in confere}
        amostra = set(random.Random(2).sample(range(len(chars)), min(2500, len(chars)))) | dos_textos
        for ident in ids:
            f = fontes.get(ident)
            if f is None:
                continue
            quais = range(len(chars)) if ident == render.LETRA_OMISSAO else sorted(amostra)
            mesa = set(saida["fora"][ident]) & set(quais)
            do_render = {j for j in quais if texto_emojis.sem_letra(chars[j], f)}
            n_comparados += len(quais)
            for j in sorted(do_render - mesa)[:3]:
                problemas.append("%s: o render nao desenha U+%04X e a Mesa deixa passar" % (ident, universo[j]))
            for j in sorted(mesa - do_render)[:3]:
                problemas.append("%s: a Mesa marca U+%04X e o render desenha-o" % (ident, universo[j]))
        # 3. OS TEXTOS DE ENSAIO
        por = {}
        for x in saida["textos"]:
            por.setdefault(x["id"], []).append(x)
        for ident in ids:
            f = fontes.get(ident)
            if f is None:
                continue
            for t, x in zip(TEXTOS_CARACTERES, por.get(ident, [])):
                n_textos += 1
                onde = "%s em %r" % (ident, t[:24])
                if x["fora"] != texto_emojis.sem_letra(t, f):
                    problemas.append("%s: caixas %s, o render %s" % (onde, x["fora"], texto_emojis.sem_letra(t, f)))
                if [[s, _sem_acentos(q)] for s, q in x["seqs"]] != [[s, q] for s, q in texto_emojis.sequencias(t)]:
                    problemas.append("%s: as sequencias nao sao as do render" % onde)
                esc_r = [[e, ("%.1f" % c).replace(".", ",")] for e, c in texto_emojis.emojis_escuros(t, f)]
                if x["escuros"] != esc_r:
                    problemas.append("%s: escuros %s, o render %s" % (onde, x["escuros"], esc_r))
                if [tp for _g, tp in x["avisos"]] != _tipos_do_render(t, f):
                    problemas.append("%s: avisos %s, o render %s" % (onde, x["avisos"], _tipos_do_render(t, f)))
                if any(g != ("erro" if tp == "caixa" else "confirma") for g, tp in x["avisos"]):
                    problemas.append("%s: os graus nao sao caixa = Está mal e o resto Confirma tu" % onde)
        # 4. A REGRA DE RESERVA, nos caracteres que o testes.py confere (os da montagem, as fronteiras e tres emojis)
        arial = fontes.get(render.LETRA_OMISSAO)
        difere = [ch for ch in sorted(confere) if ord(ch) in universo and
                  saida["reserva"][universo.index(ord(ch))] != bool(render.caracteres_sem_letra(ch, arial))]
        if difere:
            problemas.append("a regra de reserva difere do render em %s" % ["U+%04X" % ord(c) for c in difere[:5]])
        if saida["reservaEmoji"]:
            problemas.append("sem a tabela, o emoji do clip 72 ainda e marcado: %s" % saida["reservaEmoji"])
        reserva_difere = sum(1 for j, ch in enumerate(chars)
                             if saida["reserva"][j] != bool(texto_emojis.sem_letra(ch, arial)))
    verifica("Mesa: os caracteres do Validar como o render", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d letras x %d pontos de codigo (%d conferidos), %d textos de ensaio (caixa, sequencias com o SAI, escuros, "
             "graus); sem a tabela, a reserva acerta nos %d do testes.py e difere em %d de %d no universo"
             % (len(ids), len(chars), n_comparados, n_textos, len(confere), reserva_difere, len(chars)))


def _leitura_mais_recente():
    """O estado2.json da saida/leitura_mesa_N com a revisao mais alta (ha uma leitura_mesa_1809 de 17 de setembro, na
    revisao 341: o numero da pasta nao chega)."""
    melhor = None
    for nome in os.listdir(os.path.join(REPO, "saida")):
        p = os.path.join(REPO, "saida", nome, "montagem", "estado2.json")
        if not (re.match(r"leitura_mesa_(\d+)$", nome) and os.path.exists(p)):
            continue
        try:
            e = json.load(open(p, encoding="utf-8"))
            e = e.get("data", e) if isinstance(e.get("data"), dict) else e
            rev = int(e.get("rev") or 0)
        except (OSError, ValueError, TypeError):
            continue
        if melhor is None or rev > melhor[0]:
            melhor = (rev, p)
    return melhor[1] if melhor else None


def teste_validar_caracteres_na_montagem_dele():
    """Na montagem dele, cada texto que vai ao ecra avisa dos caracteres como o render, na letra onde vai.

    A LETRA DE CADA TEXTO E A DO render.avisos_dos_textos(): os cartoes na do cartao, a fita e os contadores no Arial
    Bold, o resto (legenda, textos das fotos, nome do destaque) na da legenda; uma letra do Estilo que o render nao abre
    vale o Arial Bold. Corre a Mesa (textosComLetra, com as funcoes do estilo de verdade) sobre a leitura mais recente,
    com o estilo dele e com dois estilos de ensaio, e compara cada texto com o texto_emojis.avisos_do_texto() na letra
    aberta como o render a abre. E a etiqueta da lista (caixasDoClip) acende so com a caixa vazia.
    """
    if not shutil.which("node"):
        salta("Mesa: os caracteres na montagem dele", "sem node neste PC")
        return
    import caracteres_para_mesa as cpm
    import texto_emojis
    problemas = []
    caminho = _leitura_mais_recente()
    if not caminho:
        salta("Mesa: os caracteres na montagem dele", "sem saida/leitura_mesa_N")
        return
    est = json.load(open(caminho, encoding="utf-8"))
    est = est.get("data", est) if isinstance(est.get("data"), dict) else est
    L = cpm.letras_do_render()
    fontes = _letras_abertas(L["letras"])
    # um clip de cada tipo com caracteres de ensaio, por cima da montagem dele (so em memoria)
    ensaio = {"id": "ensaio", "nome": "ensaio", "clips": [
        {"t": "foto", "i": "f0001", "x": "Assim \U0001F62E \ue000", "d": 4, "c": 0.7,
         "zd": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3, "texto": "Avó \U0001F44D\U0001F3FD"}},
        {"t": "cartao", "x": "Nasce \u2764\ufe0f \U0001F3B5 \u0416", "d": 5, "c": 0.7},
        {"t": "marcos", "x": "1995|SAPO \U0001F389*|Côa \U0001F1F5\U0001F1F9", "d": 6, "c": 0},
        {"t": "contador", "x": "04/10/2026>25/12/2025|4 de outubro \ue001", "d": 6, "c": 0},
        {"t": "colagem", "fotos": ["f0001", "f0002"], "x": "", "xf": ["Nos Açores \U0001F30A", "Grécia \u03a9 \u05d0"],
         "vf": True, "d": 8, "c": 0.7}]}
    casos = [("o estilo dele", est.get("estilo") or {}),
             ("legenda em Montserrat, cartao em Great Vibes", {"legenda": {"fonte": "montserrat_bold"},
                                                                "cartao": {"fonte": "great_vibes"}}),
             ("letras que nao existem", {"legenda": {"fonte": "nao_existe"}, "cartao": {"fonte": "Montserrat_Bold"}})]
    n_textos = n_avisos = n_caixas = 0
    contas = None
    for nome, estilo in casos:
        e = dict(est)
        e["estilo"] = estilo
        e["versoes"] = list(est.get("versoes") or []) + [ensaio]
        saida = _correr_validador(e, """
var o = [];
est.versoes.forEach(function(v){
  v.clips.forEach(function(c, i){
    var cx = caixasDoClip(c).length;
    textosComLetra(c).forEach(function(p){
      o.push({v: v.id, i: i, campo: p[0], texto: p[1], letra: p[2].id,
              avisos: avisosDosCaracteres(p[1], p[2].id, p[2].nome).map(function(q){ return [q.grau, q.tipo]; }),
              caixas: cx});
    });
  });
});
process.stdout.write(JSON.stringify(o));
""", problemas, L)
        if not saida:
            break

        def letra_do_render(parte):
            ident = (estilo.get(parte) or {}).get("fonte") if parte != "fita" else None
            return ident if ident in fontes and fontes[ident] is not None else "arial_bold"
        caixa_no_clip = {}
        for x in saida:
            caixa_no_clip.setdefault((x["v"], x["i"]), False)
            if texto_emojis.sem_letra(x["texto"], fontes[x["letra"]]):
                caixa_no_clip[(x["v"], x["i"])] = True
        for x in saida:
            c = next(v for v in e["versoes"] if v["id"] == x["v"])["clips"][x["i"]]
            parte = ("cartao" if c.get("t") in ("cartao", "nome") else "fita" if c.get("t") in ("contador", "marcos")
                     else "legenda")
            if x["campo"] == "nome do destaque":
                parte = "legenda"
            if x["letra"] != letra_do_render(parte):
                problemas.append("%s, clip %d de %s: a Mesa mede %s na letra %s e o render na %s"
                                 % (nome, x["i"] + 1, x["v"], x["campo"], x["letra"], letra_do_render(parte)))
                continue
            esperado = _tipos_do_render(x["texto"], fontes[x["letra"]])
            if [t for _g, t in x["avisos"]] != esperado:
                problemas.append("%s, clip %d de %s (%s): a Mesa %s, o render %s"
                                 % (nome, x["i"] + 1, x["v"], x["campo"], x["avisos"], esperado))
            if (x["caixas"] > 0) != caixa_no_clip[(x["v"], x["i"])]:
                problemas.append("%s, clip %d de %s: a etiqueta da caixa vazia nao bate" % (nome, x["i"] + 1, x["v"]))
            n_textos += 1
            n_avisos += len(x["avisos"])
            n_caixas += sum(1 for _g, t in x["avisos"] if t == "caixa")
        if nome == "o estilo dele":
            dele = [x for x in saida if x["v"] != "ensaio"]
            contas = (len(dele), sum(1 for x in dele for _g, t in x["avisos"] if t == "caixa"),
                      sum(1 for x in dele for _g, t in x["avisos"] if t == "sequencia"),
                      sum(1 for x in dele for _g, t in x["avisos"] if t == "escuro"),
                      len([x for x in dele if "\U0001F62E" in x["texto"]]))
            ens = {x["campo"] for x in saida if x["v"] == "ensaio"}
            for campo in ("texto no ecrã", "nome do destaque", "texto da fita", "texto do contador", "texto da foto 1",
                          "texto da foto 2"):
                if campo not in ens:
                    problemas.append("o clip de ensaio com %s nao foi visto" % campo)
    verifica("Mesa: os caracteres na montagem dele", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%s: %d textos (%d caixas, %d sequencias, %d escuros; o emoji do clip 72 em %d texto(s) ja nao e caixa), e "
             "3 estilos com 5 clips de ensaio: %d textos, %d avisos iguais ao render, %d caixas"
             % (os.path.basename(os.path.dirname(os.path.dirname(caminho))), contas[0], contas[1], contas[2], contas[3],
                contas[4], n_textos, n_avisos, n_caixas) if contas else "sem saida")


def teste_validar_creditos_como_o_ponto5():
    """O Validar olha para os textos dos creditos (decisao 105), e avisa dos caracteres como o ponto5.

    O ponto5_creditos.caracteres_que_faltam() mede cada texto na letra onde vai (os cargos, os subtitulos e os nomes na
    da legenda; quem fez cada cargo, o titulo final, a data e os titulos dos grupos na do cartao) e diz dos convidados o
    grupo e quantos nomes. A Mesa (validarCreditos) tem de dar os mesmos avisos aos mesmos textos, em Arial e com o
    Montserrat na legenda e o Great Vibes no cartao. E os da largura vao com o grau certo: o que para os creditos e
    «Está mal», o que esta no limite «Confirma tu», o titulo que encolhe so abaixo do corpo minimo.
    """
    if not shutil.which("node"):
        salta("Mesa: os textos dos creditos no Validar", "sem node neste PC")
        return
    import caracteres_para_mesa as cpm
    import creditos_para_mesa as cm
    import render
    problemas = []
    p5 = cm._ponto5()
    L = cpm.letras_do_render()
    cred = _cred_de_ensaio()
    cred["grupos"][0]["linhas"] = ["Ana \U0001F44D\U0001F3FD · Rui", "Eva \ue000"]
    cred["grupos"][1]["linhas"] = ["Zé \U0001F62E"]
    cred["grupos"][2]["linhas"] = ["Ivo"]
    cred["grupos"][2]["titulo"] = "T3 longo"
    creditos = {"cargos": [{"cargo": "Cargo \U0001F62E", "quem": "QUEM \ue000"}, {"cargo": "Cargo B \U0001F3B5 \u018c", "quem": "QUEM B"},
                           {"cargo": "Audio\u2011Visual", "quem": "QUEM \U0001F1F5\U0001F1F9 \u2150\nOUTRA \ue002"},
                           {"cargo": "Som \U0001F3B5", "quem": "DJ"}],
                "titulo": "FIM \u2764\ufe0f", "data": "4 \u0416 2026",
                "grupos": {"Grupo 1": {"titulo": "T1 \U0001F468\u200d\U0001F469\u200d\U0001F467", "sub": "s1 \U0001F5A4"}}}
    # o U+018C o Montserrat tem e o Great Vibes nao; o U+2150 ao contrario: um texto medido na letra errada muda o aviso.
    # O cargo 3 tem duas pessoas, uma por linha, e ha um quarto cargo (o contrato dos cargos, 2 de outubro as 19:35):
    # cada pessoa avisa a sua vez, como no ponto5 (pessoas_do_quem)
    casos = [("Arial", None), ("Montserrat e Great Vibes", {"legenda": {"fonte": "montserrat_bold"},
                                                             "cartao": {"fonte": "great_vibes"}})]
    n = 0
    for nome, estilo in casos:
        est = {"versoes": [], "pessoas": [], "tags": {}, "creditos": creditos, "estilo": estilo or {}}
        saida = _correr_validador(est, """
var CRED = %s, credLay = null, credTemFinais = false, porId = {};
function credAvisoDoTexto(campo, texto){
  if(campo === "quem" && texto === "QUEM B") return "Não cabe no ecrã (uns 2000 px, cabem 1728): com este texto o render dos créditos pára antes de desenhar. Encurta-o.";
  if(campo === "data") return "Está no limite do ecrã (uns 1700 px, cabem 1728). O montar mede-o com a letra do render antes do render; se não couber, o render dos créditos pára. Mais curto é mais seguro.";
  if(campo === "gtitulo" && /T3/.test(texto)) return "Não cabe no painel dos nomes: o render encolhe-o para 50 px (os outros títulos têm 60), abaixo dos 55 a partir dos quais se lê a 15 metros.";
  if(campo === "gtitulo" && /T1/.test(texto)) return "Não cabe no painel dos nomes: o render encolhe-o para 56 px (os outros títulos têm 60). Encurta-o para ficar como os outros.";
  return "";
}
function credCorpoDoTitulo(t){ return /T3/.test(t) ? 50 : 56; }
function credMinimoDaLetra(){ return 55; }
var a = validarCreditos();
process.stdout.write(JSON.stringify(a.map(function(x){ return {grau: x.grau, campo: x.cred.campo, k: x.cred.k, titulo: x.titulo,
  texto: x.detalhe}; })));
""" % json.dumps(cred, ensure_ascii=False), problemas, L, mais=FUNCOES_CRED_VALIDAR)
        if not saida:
            break
        # o ponto5, com o mesmo estilo e os textos ja limpos como o _texto_dele (troca os equivalentes)
        try:
            render.aplicar_estilo(estilo, [])
            eq = render.com_equivalentes
            textos = {"cargos": [(eq(c["cargo"]), eq(c["quem"])) for c in creditos["cargos"]],
                      "titulo": eq(creditos["titulo"]), "data": eq(creditos["data"])}
            blocos = []
            for g in cred["grupos"]:
                if g["linhas"]:
                    m = creditos["grupos"].get(g["etiqueta"], {})
                    blocos.append((eq(m.get("titulo") or g["titulo"]), eq(m.get("sub") or g["sub"]),
                                   [ln.split(" · ") for ln in g["linhas"]]))
            avisos_p5 = p5.caracteres_que_faltam(textos, blocos)
        finally:
            render.aplicar_estilo(None, [])

        def tipo_p5(a):
            return ("nomes" if " do grupo " in a.split(" tem ")[0] and a[0].isdigit() else
                    "caixa" if "caixa vazia" in a else "sequencia" if "nao junta" in a else "escuro" if "escuro" in a else "?")
        do_p5 = sorted((tipo_p5(a), a.split(" (")[0] if tipo_p5(a) == "nomes" else a.split(" tem ")[0]) for a in avisos_p5)
        rotulo = {"cargo": lambda x: 'o cargo %d ("%s")' % (int(x["k"]) + 1, render.com_equivalentes(x["texto"])),
                  "quem": lambda x: 'quem fez o cargo %d ("%s")' % (int(x["k"]) + 1, render.com_equivalentes(x["texto"])),
                  "titulo": lambda x: 'o titulo final "%s"' % x["texto"], "data": lambda x: 'a data "%s"' % x["texto"],
                  "gtitulo": lambda x: 'o titulo de grupo "%s"' % x["texto"], "gsub": lambda x: 'o subtitulo "%s"' % x["texto"]}
        da_mesa, graus = [], []
        for x in saida:
            t = x["titulo"]
            if t.startswith("Não cabe") or t.startswith("Está no limite"):
                esperado = ("erro" if t.startswith("Não cabe no ecrã") else "confirma" if t.startswith("Está no limite")
                            else "erro" if "T3" in x["texto"] else "confirma")
                graus.append((x["campo"], x["grau"], esperado))
                continue
            if " do grupo «" in t:
                k = int(t.split(" ")[0])
                g = next(g for g in cred["grupos"] if g["etiqueta"] == x["k"])
                tit = creditos["grupos"].get(g["etiqueta"], {}).get("titulo") or g["titulo"]
                da_mesa.append(("nomes", '%d nome%s do grupo "%s"' % (k, "s" if k > 1 else "", tit)))
                graus.append(("nomes", x["grau"], "erro" if "caixa vazia" in t else "confirma"))
                continue
            tp = "caixa" if "caixa vazia" in t else "sequencia" if "não os junta" in t else "escuro" if "escuro" in t else "?"
            da_mesa.append((tp, rotulo[x["campo"]](x)))
            graus.append((x["campo"], x["grau"], "erro" if tp == "caixa" else "confirma"))
        da_mesa.sort()
        if da_mesa != do_p5:
            problemas.append("%s: so a Mesa %s; so o ponto5 %s" % (nome, [d for d in da_mesa if d not in do_p5][:3],
                                                                   [d for d in do_p5 if d not in da_mesa][:3]))
        for campo, veio, era in graus:
            if veio != era:
                problemas.append("%s: um aviso de %s com o grau %s, devia ser %s" % (nome, campo, veio, era))
        larg = [g for g in graus if g[0] in ("quem", "data", "gtitulo") and g[2]]
        if len([g for g in larg if g[0] in ("quem", "data")]) < 2 or not any(g[0] == "gtitulo" for g in larg):
            problemas.append("%s: os avisos da largura nao chegaram ao Validar" % nome)
        n += len(saida)
    verifica("Mesa: os textos dos creditos no Validar", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d avisos em 2 estilos, os mesmos do ponto5 (caixa, sequencia, escuro e os nomes por grupo), e a largura "
             "com o grau do painel" % n)


def teste_rolo_parte_os_emojis_como_o_ponto5():
    """O rolo dos creditos da Mesa parte os nomes com um emoji como o ponto5, pelo texto_emojis.

    A Mesa nao mede nomes no browser: as linhas vem do creditos_para_mesa.grupos_com_nomes(), pelo p5.quebrar(), que
    mede com o texto_emojis.largura() (o emoji a 1,26 do corpo, com a letra de emojis; no browser seria 1,38). Aqui,
    com convidados de ensaio com emojis e equivalentes, as linhas e as quebras noutras letras sao as do ponto5, um
    emoji muda onde a linha parte (contra a medida da Pillow sem emojis), e o credLayout() da Mesa usa-as tal e qual.
    """
    if not shutil.which("node"):
        salta("Mesa: o rolo parte os emojis como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    from PIL import ImageFont
    problemas = []
    p5 = cm._ponto5()
    etiqueta = p5.GRUPOS[0][0]
    f_arial = ImageFont.truetype(render.FONTE_TEXTO, p5.NOME_CORPO)
    larg = p5.PAINEL_NOMES[1] - p5.PAINEL_NOMES[0]
    # nomes de ensaio com emojis numa so familia: a largura das linhas e o que decide onde parte
    nomes = ["Ana \U0001F62E", "Rui \U0001F389\U0001F389", "Eva\u2011Maria", "Zé \U0001F44D\U0001F3FD", "Lia",
             "Teo \U0001F30A\U0001F30A\U0001F30A", "Bia", "Gil \u2764\ufe0f", "Ivo", "Noa \U0001F3B5\U0001F3B5", "Rita",
             "Duarte \U0001F600\U0001F600", "Inês", "Tomé \U0001F1F5\U0001F1F9", "Leonor \U0001F970"] * 2
    convidados = [{"nome": n, "apelido": "", "familia": "F1", "etiquetas": [etiqueta]} for n in nomes]
    grupos = cm.grupos_com_nomes(p5, convidados)
    g = next(x for x in grupos if x["etiqueta"] == etiqueta)
    esperado = p5.quebrar(nomes, f_arial, larg)
    if g["linhas"] != esperado:
        problemas.append("as linhas da Mesa nao sao as do p5.quebrar (%d contra %d)" % (len(g["linhas"]), len(esperado)))
    # o emoji conta: com a medida da Pillow sem a letra de emojis (o getlength do glifo de falta) parte noutro sitio
    sem, atual = [], ""
    for p in nomes:
        t = (atual + " · " + p) if atual else p
        if atual and f_arial.getlength(t) > larg:
            sem.append(atual)
            atual = p
        else:
            atual = t
    sem += [atual] if atual else []
    if sem == esperado:
        problemas.append("o ensaio nao separa a medida com emojis da medida sem eles (escolhe outros nomes)")
    # noutras letras: as quebras sao as do p5.quebrar com essa letra
    outras = 0
    for ident, quebra in (g.get("quebras") or {}).items():
        f = render.abrir_letra(ident, p5.NOME_CORPO, avisar=False)
        contas = cm.pessoas_por_linha(nomes, p5.quebrar(nomes, f, larg))
        if contas != quebra:
            problemas.append("%s: quebras %s, o ponto5 %s" % (ident, quebra, contas))
        outras += 1
    # e o credLayout() da Mesa poe essas linhas no rolo, sem as medir outra vez
    cred = _cred_de_ensaio()
    cred["grupos"] = [dict(g, titulo="T", sub="s")]
    saida = _correr_node(_prelude(cred, {"versoes": [], "pessoas": [], "tags": {}}), """
var L = credLayout();
process.stdout.write(JSON.stringify(L.pecas.filter(function(q){ return q.tipo === "nome"; }).map(function(q){ return q.texto; })));
""", problemas)
    if saida is not None and saida != esperado:
        problemas.append("o credLayout() da Mesa nao poe as linhas do ponto5 (%d contra %d)" % (len(saida), len(esperado)))
    verifica("Mesa: o rolo parte os emojis como o ponto5", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d nomes com emojis em %d linhas (medidas sem a letra de emojis, %d delas partiam noutro sitio), %d letras "
             "com outras quebras iguais, e o credLayout() com as mesmas linhas"
             % (len(nomes), len(esperado), sum(1 for a, b in zip(sem, esperado) if a != b) + abs(len(sem) - len(esperado)),
                outras))


def teste_creditos_medem_os_emojis_como_o_render():
    """Um texto dos creditos com emojis mede-se na Mesa como no render, e o letreiro desenha-os como unidades.

    O DEFEITO QUE ISTO APANHA (2 de outubro, a noite): a Mesa media cada ponto de codigo como uma letra do letreiro,
    com o espaco dele, e o emoji com a letra do browser. Num quem com uma familia (U+1F469 U+200D U+1F467) o ZWJ e o
    segundo emoji levavam dois espacos a mais (2 x 0,28 x 110 = 62 px) e cada emoji uns 12 px a mais: a Mesa dizia
    «Não cabe no ecrã» a um quem que o render desenha. Aqui as letras medem-se com as larguras do PIL (as do render), e
    compara-se o credLargura() com o texto_emojis.largura() (a legenda) e o p5.largura_do_letreiro() (o letreiro), em
    Arial e com o Georgia na legenda e o Montserrat no cartao. E o credLetreiro() escreve cada emoji uma vez, na letra
    de emojis, sem o ZWJ nem o U+FE0F; sem emojis, as letras de sempre.
    """
    if not shutil.which("node"):
        salta("Mesa: os emojis dos creditos medem-se como no render", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    import texto_emojis
    problemas = []
    p5 = cm._ponto5()
    M = cm.MEDIDAS
    ss = render.LETREIRO_SS
    textos = [("gsub", "do lado da mãe \U0001F44D\U0001F3FD", 0), ("gsub", "os amigos \U0001F389\U0001F389\U0001F389", 0),
              ("cargo", "Ideia \U0001F4A1 e textos \u270d\ufe0f", 0), ("cargo", "Som \U0001F3B5", 0),
              ("quem", "A MÃE DA CLARA \U0001F469\u200d\U0001F467", 0), ("quem", "O TIAGO \U0001F1F5\U0001F1F9", 0),
              ("titulo", "CLARA & TIAGO \u2764\ufe0f", 0), ("data", "4 DE OUTUBRO \U0001F48D 2026", 0),
              ("gtitulo", "FAMÍLIA \U0001F468\u200d\U0001F469\u200d\U0001F467", 0), ("quem", "A MÃE DA CLARA", 0)]
    medida = {"gsub": (M.get("sub_corpo", 58), 0, "legenda"), "cargo": (M["cargo_corpo"], 0, "legenda"),
              "quem": (M["quem_corpo"], M["quem_espaco"], "cartao"), "titulo": (M["final_corpo"], M["final_espaco"], "cartao"),
              "data": (M["data_corpo"], M["data_espaco"], "cartao"), "gtitulo": (p5.TITULO_CORPO, p5.TITULO_ESPACO, "cartao")}
    estilos = [{}, {"legenda": {"fonte": "georgia_bold"}, "cartao": {"fonte": "montserrat_bold"}}]
    n, pior = 0, 0.0
    for estilo in estilos:
        # o que o render mede, e as larguras das letras do PIL para o medidor falso da Mesa
        tab, esperado = {}, []
        try:
            render.aplicar_estilo(estilo or None, [])
            for campo, t, _x in textos:
                corpo, espaco, parte = medida[campo]
                if parte == "legenda":
                    f = render.letra("legenda", corpo)
                    esperado.append(texto_emojis.largura(t, f))
                    for p, cores in (texto_emojis.pedacos(texto_emojis.com_equivalentes(t), f) or [(t, False)]):
                        if not cores:
                            tab["%d|%s" % (corpo, p)] = f.getlength(p)
                else:
                    f = render.letra("cartao", corpo * ss)
                    esperado.append(p5.largura_do_letreiro(t, corpo, espaco))
                    for u, cores in texto_emojis.unidades(t, f):
                        if not cores:
                            tab["%d|%s" % (corpo, u)] = f.getlength(u) / float(ss)
        finally:
            render.aplicar_estilo(None, [])
        saida = _correr_estilo({"pessoas": [], "versoes": [], "tags": {}, "estilo": estilo}, """
var TAB = %s, TX = %s, MED = %s;
var credMedidor = {font: "", measureText: function(s){
  var corpo = /(\\d+(?:\\.\\d+)?)px/.exec(this.font)[1], k = (+corpo) + "|" + s;
  if(s === "Hg") return {width: 0, fontBoundingBoxAscent: 0.905 * corpo, fontBoundingBoxDescent: 0.212 * corpo};
  if(TAB[k] === undefined) throw new Error("sem medida: " + k);
  return {width: TAB[k]};
}};
var o = {larg: TX.map(function(x){ var m = MED[x[0]]; return credLargura(x[1], m[0], m[1], m[2]); })};
/* o letreiro do quem com a familia: o que se escreve, numa tela que so regista */
var ops = [], ctx = {save: function(){}, restore: function(){}, measureText: function(s){ credMedidor.font = this.font; return credMedidor.measureText(s); },
  createLinearGradient: function(){ return {addColorStop: function(){}}; },
  fillText: function(s, x){ ops.push({t: s, x: x, font: this.font, sombra: this.shadowBlur > 0}); }, shadowBlur: 0, font: ""};
credLetreiro(ctx, TX[4][1], MED.quem[0], MED.quem[1], 960, 540, 1, {quente: [226, 184, 140], claro: [255, 247, 234], brilho: [0, 0, 0]});
o.letreiro = ops;
ops = []; credLetreiro(ctx, TX[9][1], MED.quem[0], MED.quem[1], 960, 540, 1, {quente: [226, 184, 140], claro: [255, 247, 234], brilho: [0, 0, 0]});
o.semEmoji = ops;
ops = []; credTextoMeio(ctx, TX[0][1], MED.gsub[0], [200, 200, 200], 960, 540, "legenda");
o.meio = ops;
process.stdout.write(JSON.stringify(o));
""" % (json.dumps(tab, ensure_ascii=False), json.dumps(textos, ensure_ascii=False), json.dumps(medida)),
            problemas, mais=FUNCOES_DESENHO_CRED, declaracoes=["var CRED_ARIAL = ", "var credLetrasPedidas = "])
        if not saida:
            break
        for (campo, t, _x), veio, era in zip(textos, saida["larg"], esperado):
            n += 1
            emojis = max(1, len(texto_emojis.emojis_do_texto(t, render.letra("legenda", 58))))
            pior = max(pior, abs(veio - era))
            if abs(veio - era) > 1.5 * emojis + 0.5:
                problemas.append("%s, %s %r: a Mesa mede %.1f px e o render %.1f" % (estilo or "Arial", campo, t, veio, era))
        letras = [x for x in saida["letreiro"] if not x["sombra"]]
        emo = [x for x in letras if "Emoji" in x["font"]]
        if [x["t"] for x in emo] != ["\U0001F469\U0001F467"] or any("\u200d" in x["t"] or "\ufe0f" in x["t"] for x in letras):
            problemas.append("o letreiro do quem com a familia escreve %s" % [x["t"] for x in letras][-4:])
        if [x["t"] for x in saida["semEmoji"] if not x["sombra"]] != list("A MÃE DA CLARA"):
            problemas.append("o letreiro sem emojis ja nao escreve as letras uma a uma")
        if not any("Emoji" in x["font"] and x["t"] == "\U0001F44D\U0001F3FD" for x in saida["meio"]):
            problemas.append("o subtitulo com o polegar nao escreve o emoji na letra de emojis: %s" % saida["meio"])
    verifica("Mesa: os emojis dos creditos medem-se como no render", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d larguras em 2 estilos a %.1f px do render no pior (legenda e letreiro, ZWJ, tom, bandeira, U+FE0F), o "
             "letreiro escreve a familia como uma unidade e sem emojis as letras de sempre" % (n, pior))


def teste_mesa_montada_traz_as_letras_do_render():
    """A Mesa montada traz o window.LETRAS_RENDER do caracteres_para_mesa.py, e nenhum ficheiro novo na publicacao."""
    import caracteres_para_mesa as cpm
    problemas = []
    montada = _montar_mesa_a_parte("teste_letras_render_")
    m = re.findall(r"\nwindow\.LETRAS_RENDER = (.*?);\n", montada)
    kb, n = 0.0, 0
    if len(m) != 1:
        problemas.append("o window.LETRAS_RENDER aparece %d vezes" % len(m))
    else:
        L = json.loads(m[0].replace("<\\/", "</"))
        kb = len(m[0].encode("utf-8")) / 1024.0
        n = len((L or {}).get("letras") or {})
        if L != cpm.letras_do_render():
            problemas.append("o window.LETRAS_RENDER nao e o letras_do_render() deste PC")
        if "arial_bold" not in ((L or {}).get("letras") or {}):
            problemas.append("falta o Arial Bold no window.LETRAS_RENDER")
        if kb > 40:
            problemas.append("o window.LETRAS_RENDER pesa %.1f KB" % kb)
        if montada.index("window.LETRAS_RENDER") > montada.index('<script>\n(function(){\n"use strict";'):
            problemas.append("o window.LETRAS_RENDER vem depois do script da pagina")
    if re.search(r'["\'](?:letras|caracteres)/[^"\']+\.(?:json|js)', montada):
        problemas.append("a pagina pede as letras em ficheiros ao lado")
    verifica("Mesa: a Mesa montada traz as letras do render", not problemas,
             "; ".join(problemas)[:300] if problemas else
             "%d letras, os emojis e os escuros (%.1f KB na pagina, 0 ficheiros novos)" % (n, kb))


# ------------------------------------------------------------------- tirar fotos dos creditos (2 de outubro, a noite)
FUNCOES_TIRAR = ["function credSemAcentos(", "function credSuave(", "function credPid(", "function credVersao(",
                 "function credMarcadas(", "function credFotos(", "function credMedida(", "function credOmissoes(",
                 "function credCargo(", "function credTitulo(", "function credData(", "function credGrupoTexto(",
                 "function credGrupoPorEtiqueta(", "function credLayout(", "function credContas(", "function credPoe(",
                 "function credMudaTexto(", "function credMover(", "function credGuardaDesfazer(", "function copiaFunda(",
                 "function corpo(", "function desfazer(", "function credOndeEsta(", "function credFotografaTres(",
                 "function credRepoeTres(", "function credVersaoSem(", "function credEntradaDasTres(", "function credTirar(",
                 "function credReporTirada(", "function credHoje(", "function credTiradasLer(", "function credTiradasJunta(",
                 "function credTiradasFora(", "function credResumo(", "function credMusicaResumo(", "function credTextoDoEfeito(",
                 "function credTextoCurtoDoEfeito(", "function credDepoisDeMexer(", "function credPintaEfeito(", "function credTirarDaLinha(",
                 "function credTirarEscolhidas(", "function eGrupo(", "function origAlinhado(", "function legendaDaSolta(",
                 "function textosDasFotos(", "function clipDaFoto(", "function layoutsPara(", "function nomeDaFoto(",
                 "function mmssDec(", "function fmtS(", "function esc(", "function credMusicaNome("]
DECLARACOES_TIRAR = ["var GRUPOS = ", "var CRED_TIRADAS = ", "var credEsc = ", "var credUltimaTirada = ",
                     "var credTiradasMem = ", "var credTiradasAberto = "]
PRELUDE_TIRAR = """
var window = {};
var CRED = %(cred)s;
var credTemFinais = !!(CRED && CRED.fotos && Object.keys(CRED.fotos).length);
var credLay = null, credCampoAberto = null, marcas = 0, baseRev = 7, pilhaDesfazer = [], clipAtivo = -1, selClips = [], ancoraSel = -1;
var PAGINA_GERACAO = "ensaio", RENDER_LE = {}, LETRAS_RENDER = null, msgs = [], pinturas = 0;
var est = %(est)s;
var porId = %(porid)s;
/* o localStorage do browser, em memoria: as tiradas de hoje guardam-se la */
var localStorage = (function(){ var m = {}; return {getItem: function(k){ return m.hasOwnProperty(k) ? m[k] : null; },
  setItem: function(k, v){ m[k] = String(v); }, removeItem: function(k){ delete m[k]; }}; })();
var document = {getElementById: function(){ return null; }, activeElement: null};
var MUSICA_J = null;
function credMusicaContas(){ return MUSICA_J ? {J: MUSICA_J(credContas().dur)} : null; }
function marcar(){ marcas++; }
function credPinta(){ pinturas++; }
function credPintaTextos(){}
function credAberto(){ return false; }
function credMsg(t){ msgs.push(t); }
function avisar(t){ msgs.push(t); }
function nada(){}
var pintaVersoes = nada, pintaClips = nada, pintaInspetor = nada, pintaGrelha = nada;
function versaoAtual(){ for(var k = 0; k < est.versoes.length; k++) if(est.versoes[k].id === est.atual) return est.versoes[k]; return null; }
function copia(x){ return JSON.parse(JSON.stringify(x)); }
function ids(){ return credFotos().lista.map(function(x){ return x.id; }); }
"""


def _base_para_tirar():
    """Uma Mesa de ensaio com as tres fontes dos creditos, sem nomes de ninguem: a etiqueta, a versao «Créditos» (uma
    foto solta, uma colagem de tres e um lado a lado de duas) e a ordem dele; o filme (v1) tem duas das mesmas fotos."""
    pessoas = [{"id": "p_a", "nome": "Clara"}, {"id": "p_c", "nome": " CRÉDITOS "}]
    tags = {"f01": ["p_c", "p_a"], "f02": ["p_a"], "f03": ["p_c"], "f04": ["p_c"], "f05": ["p_c"], "f06": ["p_a", "p_c"],
            "f07": ["p_c"]}
    vc = {"id": "vc", "nome": "Créditos", "clips": [
        {"t": "cartao", "x": "ola"}, {"t": "foto", "i": "f05", "f": "IMG_05.JPG", "x": "cinco", "d": 4},
        {"t": "colagem", "fotos": ["f02", "f03", "f04"], "xf": ["dois", "tres", "quatro"], "d": 7, "x": ""},
        {"t": "lado", "fotos": ["f06", "f01"], "lay": "2v", "x": "Lado", "xf": ["seis", "um"], "d": 5, "c": 0.7}]}
    v1 = {"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01", "f": "IMG_01.JPG"}, {"t": "foto", "i": "f03", "f": "IMG_03.JPG"}]}
    est = {"pessoas": pessoas, "tags": tags, "versoes": [v1, vc], "atual": "v1",
           "creditos": {"ordem": ["f05", "f02", "f03", "f04", "f06", "f01", "f07"], "titulo": "X"}}
    porid = {"f%02d" % k: {"id": "f%02d" % k, "f": "IMG_%02d.JPG" % k, "w": 4000, "h": 3000} for k in range(1, 9)}
    return est, porid


def _correr_tirar(est, porid, corpo_js, problemas, cred=None, mais=(), declaracoes=(), prelude_mais=""):
    html = io.open(EDITOR, encoding="utf-8").read()
    funcoes = list(FUNCOES_TIRAR) + [m for m in mais if m not in FUNCOES_TIRAR]
    prelude = PRELUDE_TIRAR % {"cred": json.dumps(cred or _cred_de_ensaio(), ensure_ascii=False),
                               "est": json.dumps(est, ensure_ascii=False), "porid": json.dumps(porid)}
    return _correr_js(list(DECLARACOES_TIRAR) + list(declaracoes), funcoes, prelude + prelude_mais, corpo_js, problemas)


def teste_tirar_dos_creditos_nas_tres_fontes():
    """«Tirar dos créditos» tira a foto da etiqueta, da versao «Créditos» e da ordem, e o ponto5 da as mesmas fotos.

    O PEDIDO, do Tiago a 2 de outubro as 18:46: "torna simples tambem na zona de editar os creditos de remover fotos que
    ja estao incluidas neste momento como sendo marcada para credito".
    O DEFEITO QUE ISTO APANHA: tirar so de um dos tres sitios e a foto voltar (a ordem sem a etiqueta poe-na no fim como
    nova; a etiqueta sem a versao deixa-a la); mexer no filme (a v1 tem as mesmas fotos) ou noutros clips da versao;
    escrever uma ordem que ele nunca fez («como está»); um Anular que nao repoe as tres coisas, ou que precisa de varios
    toques para uma acao; uma reposicao que a poe noutro sitio; e a Mesa e o ponto5_creditos.ordem_das_fotos() a darem
    colunas diferentes depois de tirar.
    """
    if not shutil.which("node"):
        salta("Mesa: tirar dos creditos nas tres fontes", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    p5 = cm._ponto5()
    problemas = []
    est, porid = _base_para_tirar()
    js = """
var r = {}, B = copia(est);
function foto(){ return {tags: copia(est.tags), versoes: copia(est.versoes), creditos: est.creditos === undefined ? null : copia(est.creditos),
                         ids: ids(), pilha: pilhaDesfazer.length, marcas: marcas}; }
function volta(){ est = copia(B); pilhaDesfazer.length = 0; credLay = null; }
r.antes = foto();
// A. uma foto com a etiqueta, numa colagem de tres da versao e na ordem
var t = credTirar(["f03"]);
r.A = foto(); r.A.partes = t.partes; r.A.fora = credTiradasFora(); r.A.rotulo = pilhaDesfazer[pilhaDesfazer.length - 1].rotulo;
r.A.entrada = {soEstado: pilhaDesfazer[0].soEstado, creditos: pilhaDesfazer[0].creditos};
desfazer();
r.Aanulado = foto(); r.Aanulado.fora = credTiradasFora();
// F. tirar e repor: volta ao mesmo lugar da ordem, a etiqueta, e um clip solto no lugar da colagem
credTirar(["f03"]);
var rep = credReporTirada("f03");
r.F = foto(); r.F.partes = rep && rep.partes; r.F.fora = credTiradasFora();
desfazer();
r.Fanulado = foto();
volta();
// B. a foto de um lado a lado de duas: o grupo passa a foto solta, com o texto da que fica
credTirar(["f06"]);
r.B = foto();
desfazer();
r.Banulado = foto();
volta();
// C. uma foto solta da versao: sai com o clip; nada mais na versao muda
credTirar(["f05"]);
r.C = foto();
volta();
// D. varias de uma vez, uma so entrada do Anular: f02 (so na versao), f04 (etiqueta e colagem), f01 (etiqueta, lado a lado e o filme)
credEsc = {f02: 1, f04: 1, f01: 1};
var m0 = marcas, p0 = pilhaDesfazer.length;
credTirarEscolhidas();
r.D = foto(); r.D.esc = credEsc; r.D.marcas = marcas - m0; r.D.pilha = pilhaDesfazer.length - p0; r.D.fora = credTiradasFora().map(function(x){ return [x.id, x.lugar]; });
desfazer();
r.Danulado = foto();
volta();
// E. sem a ordem e sem a versao: so a etiqueta, e nenhuma chave nova nos creditos
delete est.creditos; est.versoes = [est.versoes[0]];
var B2 = copia(est);
credTirar(["f07"]);
r.E = foto(); r.E.corpoTemCreditos = Object.prototype.hasOwnProperty.call(corpo(), "creditos"); r.E.est = copia(est);
desfazer();
r.Eanulado = foto(); r.E.B2 = B2;
volta();
// G. uma que nao esta nos creditos, e o duplo toque no «Tirar»
var m0 = marcas;
r.G = {nada: credTirar(["f99"]), marcas: marcas - m0, pilha: pilhaDesfazer.length};
credUltimaTirada = 0;
credTirarDaLinha(0); credTirarDaLinha(0);
r.G.duplo = ids(); r.G.pilhaDuplo = pilhaDesfazer.length;
console.log(JSON.stringify(r));
"""
    r = _correr_tirar(est, porid, js, problemas)
    if r:
        A = r["antes"]

        def cols(e):
            return p5.ordem_das_fotos(e)[0]

        def estado(f):
            return {"pessoas": est["pessoas"], "tags": f["tags"], "versoes": f["versoes"],
                    **({"creditos": f["creditos"]} if f["creditos"] is not None else {})}
        # a Mesa e o ponto5 dao a mesma coluna em todos os estados
        for nome in ("antes", "A", "Aanulado", "F", "Fanulado", "B", "Banulado", "C", "D", "Danulado", "E", "Eanulado"):
            f = r[nome]
            if f["ids"] != cols(estado(f)):
                problemas.append("%s: a Mesa da %s e o ponto5 %s" % (nome, f["ids"], cols(estado(f))))
        vc = lambda f: next(v for v in f["versoes"] if v["id"] == "vc")["clips"]     # noqa: E731
        v1 = lambda f: next(v for v in f["versoes"] if v["id"] == "v1")               # noqa: E731
        # A
        a = r["A"]
        if "f03" in a["ids"] or a["tags"]["f03"] != [] or a["tags"]["f01"] != ["p_c", "p_a"]:
            problemas.append("A: a etiqueta da f03: %s" % a["tags"]["f03"])
        if vc(a)[2] != {"t": "colagem", "fotos": ["f02", "f04"], "xf": ["dois", "quatro"], "d": 7, "x": ""} \
                or vc(a)[:2] != vc(A)[:2] or vc(a)[3] != vc(A)[3]:
            problemas.append("A: a versao Creditos: %s" % vc(a))
        if a["creditos"] != {"ordem": ["f05", "f02", "f04", "f06", "f01", "f07"], "titulo": "X"}:
            problemas.append("A: a ordem: %s" % a["creditos"])
        if v1(a) != v1(A):
            problemas.append("A: o filme (v1) mudou")
        if a["pilha"] != 1 or a["marcas"] != 1 or a["partes"] != ["creditos", "tags", "versoes"] \
                or a["entrada"] != {"soEstado": True, "creditos": True} or "IMG_03.JPG" not in a["rotulo"]:
            problemas.append("A: o anular e a gravacao: %s entradas, %s gravacoes, partes %s" % (a["pilha"], a["marcas"], a["partes"]))
        if [x["id"] for x in a["fora"]] != ["f03"] or a["fora"][0]["lugar"] != 3:
            problemas.append("A: as tiradas de hoje: %s" % a["fora"])
        an = r["Aanulado"]
        if (an["tags"], an["versoes"], an["creditos"], an["ids"]) != (A["tags"], A["versoes"], A["creditos"], A["ids"]) or an["fora"]:
            problemas.append("A: o Anular nao repos as tres coisas: %s" % an["ids"])
        # F
        f = r["F"]
        if f["ids"] != A["ids"] or f["tags"]["f03"] != ["p_c"] or f["creditos"] != A["creditos"] or f["fora"]:
            problemas.append("F: repor nao a pos no mesmo lugar: %s" % f["ids"])
        if [c.get("i") or c.get("fotos") for c in vc(f)] != [None, "f05", "f03", ["f02", "f04"], ["f06", "f01"]] \
                or f["partes"] != ["creditos", "versoes", "tags"]:
            problemas.append("F: a versao depois de repor: %s, partes %s" % ([c.get("i") or c.get("fotos") for c in vc(f)], f["partes"]))
        if "f03" in r["Fanulado"]["ids"]:
            problemas.append("F: anular a reposicao nao a voltou a tirar")
        # B
        b = vc(r["B"])
        if b[3].get("t") != "foto" or b[3].get("i") != "f01" or b[3].get("x") != "um" or b[3].get("c") != 0.7 \
                or r["B"]["tags"]["f06"] != ["p_a"] or "f06" in r["B"]["ids"]:
            problemas.append("B: o lado a lado de duas devia passar a foto solta f01 com o texto dela: %s" % b[3])
        if r["Banulado"]["versoes"] != A["versoes"] or r["Banulado"]["tags"] != A["tags"]:
            problemas.append("B: o Anular nao repos o lado a lado")
        # C
        c = r["C"]
        if [x.get("i") or x.get("fotos") for x in vc(c)] != [None, ["f02", "f03", "f04"], ["f06", "f01"]] or c["tags"]["f05"] != []:
            problemas.append("C: a foto solta: %s" % [x.get("i") or x.get("fotos") for x in vc(c)])
        # D
        d = r["D"]
        dv = vc(d)
        if d["pilha"] != 1 or d["marcas"] != 1 or d["esc"] is not None:
            problemas.append("D: varias de uma vez deviam ser uma entrada e uma gravacao: %s, %s" % (d["pilha"], d["marcas"]))
        if [x.get("i") or x.get("fotos") for x in dv] != [None, "f05", "f03", "f06"] or dv[2].get("x") != "tres" or dv[3].get("x") != "seis":
            problemas.append("D: a versao: %s" % [(x.get("i") or x.get("fotos"), x.get("x")) for x in dv])
        if set(d["ids"]) & {"f01", "f02", "f04"} or v1(d) != v1(A) or d["tags"]["f01"] != ["p_a"] or d["tags"]["f02"] != ["p_a"]:
            problemas.append("D: %s ficaram, ou o filme mudou" % d["ids"])
        if sorted(d["fora"]) != [["f01", 6], ["f02", 2], ["f04", 4]]:
            problemas.append("D: as tiradas de hoje: %s" % d["fora"])
        if (r["Danulado"]["tags"], r["Danulado"]["versoes"], r["Danulado"]["creditos"]) != (A["tags"], A["versoes"], A["creditos"]):
            problemas.append("D: um Anular nao repos as tres")
        # E: «como está» (sem ordem): nao nasce uma ordem
        e = r["E"]
        if e["creditos"] is not None or e["corpoTemCreditos"] or e["tags"]["f07"] != [] or "f07" in e["ids"]:
            problemas.append("E: sem ordem, tirar escreveu %s" % e["creditos"])
        if r["Eanulado"]["tags"] != e["B2"]["tags"]:
            problemas.append("E: o Anular da etiqueta")
        # G
        g = r["G"]
        if g["nada"] is not None or g["marcas"] or g["pilha"]:
            problemas.append("G: tirar uma foto que nao e dos creditos mexeu: %s" % g)
        if g["pilhaDuplo"] != 1 or g["duplo"] != A["ids"][1:]:
            problemas.append("G: o duplo toque tirou %d" % g["pilhaDuplo"])
    verifica("Mesa: tirar dos creditos nas tres fontes", not problemas, "; ".join(problemas)[:400] if problemas else
             "etiqueta, versao (solta, colagem, lado a lado), ordem, varias de uma vez, como esta, repor e anular; o ponto5 igual em 12 estados")


def teste_tirar_dos_creditos_e_a_juncao():
    """Uma foto tirada num aparelho nao volta pela juncao com outro, e o Anular dela sai quando o outro mexe no mesmo.

    O DEFEITO QUE ISTO APANHA: as tres fontes sao partes diferentes da juncao (["tags"], ["versoes"] e
    ["creditos","ordem"]). Se a juncao levasse do outro aparelho uma das partes que a tirada mudou, a foto voltava aos
    creditos sem ninguem ver: a etiqueta de volta punha-a no fim como nova. E um Anular guardado antes de juntar repunha
    as copias de antes por cima do que o outro aparelho fez.
    """
    if not shutil.which("node"):
        salta("Mesa: tirar dos creditos e a juncao", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    p5 = cm._ponto5()
    problemas = []
    est, porid = _base_para_tirar()
    B0 = dict(est, quando="2026-10-02T21:00:00Z", rev=5, pagina="2026-10-02")
    html = io.open(EDITOR, encoding="utf-8").read()
    extra = [m for m in FUNCOES_JUNTAR if m not in FUNCOES_TIRAR]
    prelude_mais = """
var baseRemota = "", contagensBase = null, baseLida = null, cadeiaLida = [], baseGravacao = "", estiloCampoAberto = null, credArrasto = null;
var ocupado = false;
function aMeioDeClips(){ return ocupado; }
var pintaPincel = nada, pintaFiltroPessoas = nada, pintaBarraClips = nada, estiloNaPagina = nada, estiloPinta = nada, credFimDoArrasto = nada;
function estiloAberto(){ return false; }
function abrir(X){ est = copia(X); registarBase(copia(X), false); est.focos = est.focos || {}; est.excluidas = est.excluidas || {};
  pilhaDesfazer.length = 0; credLay = null; }
"""
    js = """
var r = {}, B0 = %s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
function estado(){ return {pessoas: est.pessoas, tags: copia(est.tags), versoes: copia(est.versoes), creditos: est.creditos === undefined ? null : copia(est.creditos)}; }
// o outro aparelho tirou a f03 e gravou (rev 6)
abrir(B0); credTirar(["f03"]); var tirada = corpo(); tirada.rev = 6; tirada.quando = "2026-10-02T21:01:00Z";
// 1. aqui um titulo dos creditos e a letra da legenda; la a f03 tirada: junta-se, e a f03 fica fora daqui
abrir(B0); credGuardaDesfazer("mudar o titulo"); credMudaTexto("titulo", "", "AQUI"); est.estilo = {legenda: {tamanho: 52}};
var j = juntarComBase(tirada);
r.um = {ok: j.ok, deles: j.deles, meus: j.meus, est: estado(), ids: ids(), corpo: corpo(), pilha: pilhaDesfazer.map(function(u){ return u.rotulo; })};
// 2. aqui a f03 tirada; la o estilo (rev 6): junta-se, e a f03 continua fora
abrir(B0); credTirar(["f03"]);
j = juntarComBase(com({estilo: {legenda: {tamanho: 48}}, rev: 6}));
r.dois = {ok: j.ok, deles: j.deles, meus: j.meus, est: estado(), ids: ids(), estilo: corpo().estilo, pilha: pilhaDesfazer.length};
// 3. aqui a f07 tirada (so a etiqueta e a ordem); la um clip do filme mudou: junta-se, e o Anular da tirada fica (nao mexe na versao)
abrir(B0); credTirar(["f07"]);
var filme = com({rev: 6}); filme.versoes[0].clips.push({t: "foto", i: "f08"});
j = juntarComBase(filme);
r.tres = {ok: j.ok, deles: j.deles, ids: ids(), clipsFilme: est.versoes[0].clips.length, pilha: pilhaDesfazer.length};
desfazer();
r.tres.anulado = ids(); r.tres.clipsDepois = est.versoes[0].clips.length;
// 4. aqui a f03 tirada; la outra etiqueta (a f02 com Creditos): conflito, e nada volta
abrir(B0); credTirar(["f03"]);
var etiq = com({rev: 6}); etiq.tags.f02 = ["p_a", "p_c"];
j = juntarComBase(etiq);
r.quatro = {ok: j.ok, choque: j.choque, ids: ids(), tagF03: est.tags.f03};
// 5. aqui a f05 tirada (da versao); la um clip do filme: conflito na montagem, a f05 continua fora daqui
abrir(B0); credTirar(["f05"]);
j = juntarComBase(filme);
r.cinco = {ok: j.ok, choque: j.choque, ids: ids()};
// 6. aqui a f05 tirada e gravada; depois la mudam o filme: junta-se, e o Anular da tirada (que mexeu na versao) sai
abrir(B0); credTirar(["f05"]);
var minha = corpo(); minha.quando = "2026-10-02T21:02:00Z"; registarBase(copia(minha), false);
var depois = copia(minha); depois.rev = 7; depois.quando = "2026-10-02T21:03:00Z"; depois.versoes[0].clips.push({t: "foto", i: "f08"});
var naPilha = pilhaDesfazer.length;
j = juntarComBase(depois);
r.seis = {ok: j.ok, deles: j.deles, naPilha: naPilha, pilha: pilhaDesfazer.length, ids: ids()};
// 7. aqui a ordem mexida; la a f03 tirada: conflito na ordem dos creditos, e a f03 nao volta para la
abrir(B0); credMover(0, 1);
j = juntarComBase(tirada);
r.sete = {ok: j.ok, choque: j.choque};
console.log(JSON.stringify(r));
""" % json.dumps(B0, ensure_ascii=False)
    r = _correr_tirar(est, porid, js, problemas, mais=extra, declaracoes=DECLARACOES_JUNTAR, prelude_mais=prelude_mais)
    if r:
        def sem_f03(x, nome):
            e = {k: v for k, v in x["est"].items() if v is not None}
            if "f03" in x["ids"] or "f03" in p5.ordem_das_fotos(e)[0] or e["tags"]["f03"] != []:
                problemas.append("%s: a f03 voltou (%s)" % (nome, x["ids"]))
        um = r["um"]
        if not um["ok"] or um["deles"] != ["versoes", "tags", "creditos"] or um["meus"] != ["creditos", "estilo"] \
                or um["corpo"]["creditos"].get("titulo") != "AQUI" or um["corpo"]["estilo"] != {"legenda": {"tamanho": 52}}:
            problemas.append("1: o titulo aqui e a f03 tirada la: %s" % {k: um[k] for k in ("ok", "deles", "meus")})
        sem_f03(um, "1")
        if um["pilha"]:
            problemas.append("1: o Anular do titulo devia sair (o outro mudou os creditos): %s" % um["pilha"])
        dois = r["dois"]
        if not dois["ok"] or dois["deles"] != ["estilo"] or dois["estilo"] != {"legenda": {"tamanho": 48}} or dois["pilha"] != 1:
            problemas.append("2: a f03 aqui e o estilo la: %s" % {k: dois[k] for k in ("ok", "deles", "pilha")})
        sem_f03(dois, "2")
        tres = r["tres"]
        if not tres["ok"] or tres["deles"] != ["versoes"] or "f07" in tres["ids"] or tres["clipsFilme"] != 3 or tres["pilha"] != 1:
            problemas.append("3: a f07 aqui e o filme la: %s" % tres)
        if "f07" not in tres["anulado"] or tres["clipsDepois"] != 3:
            problemas.append("3: o Anular da f07 depois de juntar: %s, %d clips" % (tres["anulado"], tres["clipsDepois"]))
        q = r["quatro"]
        if q["ok"] or q["choque"] != ["tags"] or "f03" in q["ids"] or q["tagF03"] != []:
            problemas.append("4: outra etiqueta la: %s" % q)
        c5 = r["cinco"]
        if c5["ok"] or c5["choque"] != ["versoes"] or "f05" in c5["ids"]:
            problemas.append("5: o filme la e a versao aqui: %s" % c5)
        s = r["seis"]
        if not s["ok"] or s["deles"] != ["versoes"] or s["naPilha"] != 1 or s["pilha"] != 0 or "f05" in s["ids"]:
            problemas.append("6: o Anular da tirada depois de juntar a montagem de outro: %s" % s)
        if r["sete"]["ok"] or r["sete"]["choque"] != ["creditos"]:
            problemas.append("7: a ordem aqui e a f03 tirada la: %s" % r["sete"])
    verifica("Mesa: tirar dos creditos e a juncao", not problemas, "; ".join(problemas)[:400] if problemas else
             "7 juncoes: partes diferentes juntam e a foto nao volta; a mesma parte e conflito; o Anular sai quando o outro mexeu no mesmo")


def teste_tirar_dos_creditos_como_o_ponto5_na_leitura():
    """Na leitura mais recente, tirar fotos na Mesa da a mesma coluna, a mesma altura e a mesma duracao que o ponto5.

    O PEDIDO: "o ponto5 tem de dar exatamente as mesmas fotos que a Mesa depois de tirar". Corre-se o credTirar() da Mesa
    sobre o estado dele (a leitura da base com a revisao mais alta), e depois o fotos_marcadas() do ponto5 sobre o que a
    Mesa grava (corpo()), com a coluna_de_fotos() e o tempos_dos_creditos() dele. Faz-se tambem com uma versao «Créditos»
    de ensaio (fotos soltas e uma colagem) junta ao estado dele, e diz-se o que a musica dos creditos faz com «fim».
    """
    if not shutil.which("node"):
        salta("Mesa: tirar dos creditos como o ponto5 na leitura", "sem node neste PC")
        return
    import contextlib
    import csv
    import creditos_para_mesa as cm
    import musica_creditos as mc
    p5 = cm._ponto5()
    leitura = _leitura_mais_recente()
    if not leitura:
        salta("Mesa: tirar dos creditos como o ponto5 na leitura", "sem leitura da base em saida/")
        return
    with contextlib.redirect_stdout(io.StringIO()):
        cred = cm.creditos_para_mesa()
    est = json.load(open(leitura, encoding="utf-8"))
    est = est.get("data", est) if isinstance(est.get("data"), dict) else est
    problemas = []
    finais = {r_["id"]: os.path.normcase(os.path.join(p5.render.FINAIS, r_["final"]))
              for r_ in csv.DictReader(open(os.path.join(REPO, "data", "finais.csv"), encoding="utf-8-sig"))}
    por_caminho = {c: i for i, c in finais.items()}
    porid = {f: {"id": f, "f": f, "w": 4, "h": 3} for f in finais}
    audio, _info = _som_da_mesa()
    tem_som = bool(audio and TCOB in audio and QUEEN in audio)
    musica = ("MUSICA_J = function(dur){ var e = credMusicaEntrada(TCOB_, \"fim\", dur); "
              "return {comoEsta: false, f: TCOB_, escolha: {inicio: \"fim\"}, e: e, dur: dur}; };\n") if tem_som else ""
    js = """
var r = [], B = copia(est);
function mede(){ credLay = null; var L = credContas(); var m = credMusicaResumo();
  return {ids: ids(), col: L.col.map(function(p){ return p.id; }), Hc: L.Hc, Hr: L.Hr, dur: L.dur, corpo: copia(corpo()), musica: m}; }
%(musica)s
r.push(mede());
var lista = ids();
// 1. a primeira, a do meio e a ultima, uma de cada vez; 2. tres de uma vez
credTirar([lista[0]]); credTirar([lista[Math.floor(lista.length / 2)]]); credTirar([lista[lista.length - 1]]);
r.push(mede());
est = copia(B); pilhaDesfazer.length = 0;
credTirar([lista[1], lista[2], lista[5]]);
r.push(mede());
// 3. com uma versao «Créditos» de ensaio: as 4 primeiras soltas e uma colagem com a 5.a e a 6.a; tira-se uma solta e uma da colagem
est = copia(B); pilhaDesfazer.length = 0;
est.versoes.push({id: "v_cred_ensaio", nome: "Créditos", clips: [lista[0], lista[1], lista[2], lista[3]].map(function(i){ return {t: "foto", i: i}; })
  .concat([{t: "colagem", fotos: [lista[4], lista[5]], d: 6}])});
r.push(mede());
credTirar([lista[2], lista[5]]);
r.push(mede());
console.log(JSON.stringify(r));
""" % {"musica": musica}
    mais_m = ["function somR2(", "function somSilencioNoInicio(", "function credMusicaFim(", "function credMusicaEntrada("] if tem_som else []
    prelude_som = ("var AUDIO = %s, AUDIO_INFO = null, MUSICA_FIM = %s, TCOB_ = %s;\n"
                   % (json.dumps(audio, ensure_ascii=False), json.dumps(mc.para_a_mesa(audio), ensure_ascii=False), json.dumps(TCOB))) if tem_som else ""
    r = _correr_tirar(est, porid, js, problemas, cred=cred, mais=mais_m, prelude_mais=prelude_som,
                      declaracoes=DECLARACOES_MUSICA if tem_som else ())
    detalhe = ""
    if r:
        durs = []
        for k, m in enumerate(r):
            e = m["corpo"]
            with contextlib.redirect_stdout(io.StringIO()):
                caminhos, _f = p5.fotos_marcadas((e, "mesa de ensaio"))
            ids_p5 = [por_caminho.get(os.path.normcase(c)) for c in caminhos]
            if ids_p5 != m["col"]:
                problemas.append("passo %d: a coluna da Mesa %s e a do ponto5 %s" % (k, m["col"][:4], ids_p5[:4]))
                continue
            if p5.ordem_das_fotos(e)[0] != m["ids"]:
                problemas.append("passo %d: a lista da Mesa e a ordem_das_fotos() do ponto5 diferem" % k)
            alto = p5.coluna_de_fotos(caminhos).height if caminhos else 0
            # com a ordem, os cargos e a velocidade que ele tiver na base (3 de outubro), e nao so os tres cargos de hoje
            t_dele = p5.textos_dos_creditos(e, [])
            T = p5.tempos_dos_creditos(m["Hr"], alto, len(t_dele["cargos"]), t_dele["cargos_primeiro"], t_dele["partes"], t_dele["velocidade"])
            if alto != m["Hc"] or abs(T["dur"] - m["dur"]) > 1e-6:
                problemas.append("passo %d: coluna %d px e %.3f s no ponto5, %d px e %.3f s na Mesa" % (k, alto, T["dur"], m["Hc"], m["dur"]))
            durs.append(m["dur"])
            if tem_som and m["musica"]:
                fim = mc.fim_das_medidas(audio[TCOB].get("silencios") or [], audio[TCOB]["duracao"])
                py = mc.entrada("fim", fim, m["dur"], audio[TCOB].get("silencios") or [])
                if abs(py["in_s"] - m["musica"]["in_s"]) > 0.006:
                    problemas.append("passo %d: o TCOB «fim» entra aos %.2f na Mesa e aos %.2f no modulo" % (k, m["musica"]["in_s"], py["in_s"]))
        if len(durs) == 5:
            detalhe = ("%d fotos; tirar 3 uma a uma: %d e %.1f s para %.1f s; 3 de uma vez: %.1f s; com a versao de ensaio %.1f s para %.1f s"
                       % (len(r[0]["col"]), len(r[1]["col"]), durs[0], durs[1], durs[2], durs[3], durs[4]))
            if tem_som:
                detalhe += "; o TCOB «fim» de %.2f para %.2f s" % (r[0]["musica"]["in_s"], r[1]["musica"]["in_s"])
    verifica("Mesa: tirar dos creditos como o ponto5 na leitura", not problemas, "; ".join(problemas)[:400] if problemas else
             detalhe + " (%s)" % os.path.basename(os.path.dirname(os.path.dirname(leitura))))


def teste_tirar_dos_creditos_diz_o_que_muda():
    """Depois de tirar, a Mesa diz a duracao nova dos creditos e o que muda na musica, pelas contas do painel.

    O DEFEITO QUE ISTO APANHA: uma frase que diz que os creditos encurtam quando sao os nomes que mandam na duracao (so
    as fotos sobem mais devagar), ou que a musica «para acabar» fica igual quando a entrada anda com a duracao.
    """
    if not shutil.which("node"):
        salta("Mesa: tirar diz o que muda", "sem node neste PC")
        return
    problemas = []
    js = """
var r = {};
function R(dur, vf, m){ return {dur: dur, n: 30, vf: vf, vn: 140, musica: m}; }
var T = "Bachman Turner Overdrive-Taking care of business_62s.mp3", Q = "Queen - Friends Will Be Friends (Lyrics).mp3";
r.fim = credTextoDoEfeito(R(179.88, 150, {tipo: "escolhida", f: T, inicio: "fim", in_s: 111.93, toca: 179.88, falta: 0}),
                          R(174.6, 150, {tipo: "escolhida", f: T, inicio: "fim", in_s: 117.21, toca: 174.6, falta: 0}));
r.inicio = credTextoDoEfeito(R(179.88, 150, {tipo: "escolhida", f: T, inicio: "inicio", in_s: 2.18, toca: 179.88, falta: 0}),
                             R(174.6, 150, {tipo: "escolhida", f: T, inicio: "inicio", in_s: 2.18, toca: 174.6, falta: 0}));
r.nomes = credTextoDoEfeito(R(179.88, 120.4, {tipo: "continua", f: Q, toca: 150, falta: 29.88}),
                            R(179.88, 116.2, {tipo: "continua", f: Q, toca: 150, falta: 29.88}));
r.como = credTextoDoEfeito(R(179.88, 150, {tipo: "continua", f: Q, toca: 153.4, falta: 26.48}),
                           R(174.6, 150, {tipo: "continua", f: Q, toca: 153.4, falta: 21.2}));
r.sem = credTextoDoEfeito(R(179.88, 150, null), R(174.6, 150, null));
r.curto = credTextoCurtoDoEfeito(R(179.88, 150, {tipo: "escolhida", f: T, inicio: "fim", in_s: 111.93, toca: 179.88, falta: 0}),
                                 R(174.6, 150, {tipo: "escolhida", f: T, inicio: "fim", in_s: 117.21, toca: 174.6, falta: 0}));
r.curtoNomes = credTextoCurtoDoEfeito(R(179.88, 120.4, null), R(179.88, 116.2, null));
console.log(JSON.stringify(r));
"""
    est, porid = _base_para_tirar()
    r = _correr_tirar(est, porid, js, problemas)
    if r:
        esperas = {
            "fim": ["passam de 2:59,9 para <b>2:54,6</b> (menos 5,3 s)", "passa a entrar aos <b>1:57,2</b> do ficheiro (antes 1:51,9)"],
            "inicio": ["começa no mesmo sítio e toca menos 5,3 s"],
            "nomes": ["continuam com <b>2:59,9</b>: quem manda na duração são os nomes", "116 px/s (antes 120)", "cala-se 29,9 s antes do fim dos créditos."],
            "como": ["Com «Como está»", "cala-se 21,2 s antes do fim dos créditos (antes 26,5 s)"],
            "sem": ["passam de 2:59,9 para <b>2:54,6</b>"],
            "curto": ["Os créditos ficam com 2:54,6 (menos 5,3 s), e a música entra aos 1:57,2 do ficheiro (antes 1:51,9)."],
            "curtoNomes": ["Os créditos continuam com 2:59,9 (mandam os nomes)."],
        }
        for k, frases in esperas.items():
            for f in frases:
                if f not in r[k]:
                    problemas.append("%s: falta %r em %r" % (k, f, r[k][:200]))
        if "—" in "".join(r.values()) or "–" in "".join(r.values()):
            problemas.append("ha travessoes nas frases")
    verifica("Mesa: tirar diz o que muda na duracao e na musica", not problemas, "; ".join(problemas)[:400] if problemas else
             "«fim» anda com a duracao, «do início» toca menos, os nomes mandam, «Como está» cala-se mais perto do fim")


# ------------------------------------------------------------- os cargos dos creditos (2 de outubro, a noite)
# O Tiago, as 19:33: "Nos creditos permite-nos testar a possibilidade de aparecer primeiro os tais cargos nos videos,
# permite tambem acrescentar mais cargos e mais pessoas e depois as nossas pessoas com os convidados e fotos." O contrato
# esta em saida/discussao/contrato_creditos_cargos.md, e o render (ponto5_creditos.py, decisao 109) ja o faz.
FUNCOES_CARGOS = ["function credLimpaQuem(", "function credCargosGuardados(", "function credCargosIguaisAosDeHoje(",
                  "function credCargosMax(", "function credPessoasMax(", "function credPoeCargos(", "function credDepoisDosCargos(",
                  "function credAcrescentaCargo(", "function credTiraCargo(", "function credMoveCargo(",
                  "function credPuxaOsDeHoje(", "function credPessoasDoQuem(", "function credHtmlDosCargos(",
                  # a ordem dos cargos e, desde 3 de outubro, a ordem das partes dos creditos (credPoePartes): a da 109
                  # continua a gravar o cargos_primeiro: true
                  "function credListasIguais(", "function credPartesEmPalavras(", "function credPoePartes(",
                  "function credFraseDaOrdem("]
DECLARACOES_CARGOS = ["var CRED_PARTES_HOJE = ", "var CRED_PARTE_NOME = "]
FUNCOES_LAYOUT_CRED = ["function credSemAcentos(", "function credPid(", "function credVersao(", "function credMarcadas(",
                       "function credFotos(", "function credMedida(", "function credOmissoes(", "function credCargo(",
                       "function credTitulo(", "function credData(", "function credGrupoTexto(", "function credGrupoPorEtiqueta(",
                       "function credLayout(", "function credContas(", "function credPoe(", "function credMudaTexto(",
                       "function credTextosMudados(", "function credRepor("]
# A MESA 53 (a publicada as 16:47 de 2 de outubro), que ainda nao conhece os cargos novos: o credCargo e o credMudaTexto
# dela, tal e qual (so com outro nome), para provar o que uma Mesa aberta num separador esquecido faz a estes campos
MESA_53_CARGOS = r'''
function credCargoV53(k){
  var o = credOmissoes().cargos[k] || {cargo: "", quem: ""};
  var c = est.creditos && Array.isArray(est.creditos.cargos) ? est.creditos.cargos[k] : null;
  return {cargo: (c && c.cargo) || o.cargo, quem: (c && c.quem) || o.quem};
}
function credMudaTextoV53(campo, chave, valor){
  var om = credOmissoes(), cr = copiaFunda(est.creditos) || {};
  valor = String(valor == null ? "" : valor).trim();
  if(campo === "cargo" || campo === "quem"){
    var lista = om.cargos.map(function(o, k){ return credCargoV53(k); });
    lista[chave][campo] = valor || om.cargos[chave][campo];
    var iguais = lista.every(function(c, k){ return c.cargo === om.cargos[k].cargo && c.quem === om.cargos[k].quem; });
    if(iguais) delete cr.cargos; else cr.cargos = lista;
  } else if(campo === "titulo" || campo === "data"){
    if(!valor || valor === om[campo]) delete cr[campo]; else cr[campo] = valor;
  } else return;
  credPoe(cr);
}
'''
# OS CASOS DA LISTA: os de omissao, a lista do teste_creditos_cargos_primeiro_e_mais_cargos do testes.py (com os vazios,
# o None, as linhas vazias e o \r\n), menos de tres, um so, a vazia, mais de 8, mais de 4 pessoas, os vazios no meio, um
# campo so com espacos nos tres primeiros, um campo que nao e texto num acrescentado, e o cargos_primeiro mal escrito
CASOS_DE_CARGOS = [
    ("como esta", None),
    ("os tres dele", {"cargos": [{"cargo": "A", "quem": "QA"}, {"cargo": "B", "quem": "QB"}, {"cargo": "C", "quem": "QC"}]}),
    ("a lista do contrato", {"cargos_primeiro": True, "cargos": [
        {}, {"quem": "O NOIVO"}, None, {"cargo": "Fotografia", "quem": "  OS PADRINHOS \n\n AS MADRINHAS\r\nOS IRMAOS  \n"},
        {"cargo": "", "quem": "  "}, {"quem": "A AVÓ"}, {"cargo": "Bolo"}]}),
    ("dois", {"cargos": [{"cargo": "X", "quem": "Y"}, {"cargo": "Z", "quem": "W"}]}),
    ("um so, primeiro", {"cargos": [{"cargo": "So um", "quem": "ELE"}], "cargos_primeiro": True}),
    ("a lista vazia", {"cargos": []}),
    ("dez", {"cargos": [{"cargo": "C%d" % k, "quem": "Q%d" % k} for k in range(10)]}),
    ("seis pessoas", {"cargos": [{"quem": "\n".join("P%d" % k for k in range(6))}]}),
    ("vazios no meio", {"cargos": [{}, {}, {}, {"cargo": "", "quem": ""}, {"cargo": "D", "quem": "E"},
                                   {"cargo": "", "quem": ""}, {"cargo": "F", "quem": "G\nH"}]}),
    ("espacos e um numero", {"cargos": [{"cargo": "  ", "quem": " X "}, {}, {}, {"cargo": 5, "quem": "Y"}]}),
    ("nao e true", {"cargos_primeiro": "sim"}),
    ("false", {"cargos_primeiro": False, "titulo": "T"}),
]
EST_DOS_CARGOS = {"versoes": [], "pessoas": [{"id": "p_c", "nome": "Créditos"}],
                  "tags": {"f01": ["p_c"], "f02": ["p_c"], "f03": ["p_c"], "f04": ["p_c"]}}


def _cred_dos_cargos(p5):
    """O CREDITOS_NOMES de ensaio (_cred_de_ensaio), com os cargos de hoje do ponto5, que sao os que valem nos tres
    primeiros lugares quando um campo vem vazio."""
    cred = _cred_de_ensaio()
    cred["omissoes"] = {"cargos": [{"cargo": c, "quem": q} for c, q in p5.CARGOS], "titulo": p5.TITULO, "data": p5.DATA}
    return cred


def teste_cargos_lista_e_tempos_como_o_ponto5():
    """Os cargos que entram, a ordem e os tempos dos creditos da Mesa sao os do ponto5 (contrato dos cargos, decisao 109).

    O DEFEITO QUE ISTO APANHA: a pre-visualizacao com outros cargos do que o filme (um vazio a contar, mais de 8, uma
    pessoa a mais, os tres primeiros sem o texto de hoje num campo vazio, um cargos_primeiro mal escrito a valer), ou com
    outra duracao (os 4,2 s de cada cargo, os 0,9 s a mais dos cargos primeiro): a musica com «fim» entrava noutro sitio
    do ficheiro, e o Tiago e a Clara decidiam a olhar para outro filme. Os tempos comparam-se ao bit, com as alturas do
    rolo e da coluna da Mesa no tempos_dos_creditos() do ponto5.
    """
    if not shutil.which("node"):
        salta("Mesa: os cargos e os tempos como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    p5 = cm._ponto5()
    problemas = []
    corpo_js = """
var EST0 = %(est)s, casos = %(casos)s, r = [];
casos.forEach(function(c){
  est = JSON.parse(JSON.stringify(EST0));
  if(c[1] !== null) est.creditos = c[1];
  credLay = null;
  var L = credContas();
  r.push({cargos: L.cargos.map(function(x){ return [x.cargo, x.pessoas.join("\\n")]; }), primeiro: L.primeiro, Hr: L.Hr, Hc: L.Hc,
          k: L.cargos.map(function(x){ return x.k; }), fora: L.cargosFora,
          t: {dur: L.dur, tCargos: L.tCargos, tRoloEntra: L.tRoloEntra, tTituloEntra: L.tTituloEntra, tRolo: L.tRolo, n: L.nCargos}});
});
console.log(JSON.stringify(r));
""" % {"est": json.dumps(EST_DOS_CARGOS, ensure_ascii=False), "casos": json.dumps(CASOS_DE_CARGOS, ensure_ascii=False)}
    saida = _correr_node(_prelude(_cred_dos_cargos(p5), EST_DOS_CARGOS), corpo_js, problemas)
    n_tempos = 0
    for (nome, cr), m in zip(CASOS_DE_CARGOS, saida or []):
        t = p5.textos_dos_creditos({"creditos": cr} if cr is not None else {}, [])
        esperado = [[c, "\n".join(p5.pessoas_do_quem(q))] for c, q in t["cargos"]]
        if m["cargos"] != esperado:
            problemas.append("%s: a Mesa tem %s, o ponto5 %s" % (nome, m["cargos"], esperado))
        if (m["primeiro"] == "cargos") != t["cargos_primeiro"]:
            problemas.append("%s: a Mesa poe os cargos %s, o ponto5 %s" % (nome, m["primeiro"], t["cargos_primeiro"]))
        T = p5.tempos_dos_creditos(m["Hr"], m["Hc"], len(t["cargos"]), t["cargos_primeiro"])
        pares = (("dur", "dur"), ("tCargos", "t_cargos"), ("tRoloEntra", "t_rolo_entra"), ("tTituloEntra", "t_titulo_entra"),
                 ("tRolo", "t_rolo"), ("n", "n_cargos"))
        dif = ["%s %r contra %r" % (k, m["t"][k], T[kp]) for k, kp in pares if m["t"][k] != T[kp]]
        if dif:
            problemas.append("%s: os tempos nao sao os do ponto5 ao bit: %s" % (nome, "; ".join(dif)))
        n_tempos += len(pares)
    if saida:
        por = dict(zip([c[0] for c in CASOS_DE_CARGOS], saida))
        # os lugares que a Mesa diz (o k de cada cargo que entra, o do painel) saltam os vazios
        if por["vazios no meio"]["k"] != [0, 1, 2, 4, 6] or por["dez"]["fora"] != 2:
            problemas.append("os lugares dos cargos que entram: %s, %s a mais" % (por["vazios no meio"]["k"], por["dez"]["fora"]))
        # 4,2 s por cargo e 0,9 s com os cargos primeiro, com o mesmo rolo
        a, b, c = por["como esta"]["t"]["dur"], por["dois"]["t"]["dur"], por["a lista do contrato"]["t"]["dur"]
        if abs((a - b) - 4.2) > 1e-9 or abs(c - a - (3 * 4.2 + 0.9)) > 1e-9:
            problemas.append("a duracao nao anda 4,2 s por cargo e 0,9 s com os cargos primeiro: %.4f, %.4f, %.4f" % (a, b, c))
    verifica("Mesa: os cargos e os tempos como o ponto5", saida is not None and not problemas,
             "; ".join(problemas)[:500] if problemas else
             "%d casos (vazios, None, \\r\\n, mais de 8, mais de 4 pessoas, 1 e 2 cargos, a lista vazia, o true mal escrito): "
             "os mesmos cargos e pessoas, e %d tempos ao bit" % (len(CASOS_DE_CARGOS), n_tempos))


def teste_cargos_desenho_como_o_ponto5():
    """Com os cargos primeiro e varias pessoas, a Mesa desenha cada peca no instante e no sitio do ponto5 (decisao 109).

    O DEFEITO QUE ISTO APANHA, com as larguras do PIL no lugar das do browser:
    - um preto entre o fim do filme e o primeiro cargo (ele tem de nascer ja aceso: a sala aplaude no primeiro preto),
      os outros cargos a acender noutro instante, o rolo a aparecer de repente em vez de entrar do preto, ou o titulo
      fora do sitio (comparado com os fotogramas do proprio desenho_dos_creditos);
    - as pessoas de um cargo umas por cima das outras, fora do meio, noutro corpo (as que nao cabem encolhem todas para o
      corpo_do_quem), ou a linha do cargo no sitio de uma pessoa so.
    """
    if not shutil.which("node"):
        salta("Mesa: o desenho dos cargos como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    from PIL import Image
    p5 = cm._ponto5()
    problemas = []
    render.aplicar_estilo(None, [])
    M = dict(cm.MEDIDAS)
    M.update({"L": p5.L, "A": p5.A, "vel_nomes": p5.VELOCIDADE_NOMES, "vel_fotos_max": p5.VELOCIDADE_FOTOS_MAX,
              "nome_corpo": p5.NOME_CORPO, "sub_corpo": p5.SUB_CORPO, "cor_nome": list(p5.COR_NOME), "cor_sub": list(p5.COR_SUB),
              "painel_nomes": list(p5.PAINEL_NOMES), "margem_brilho": p5.MARGEM_BRILHO, "largura_foto": p5.LARGURA_FOTO,
              "centro_fotos": p5.CENTRO_FOTOS, "titulo_corpo": p5.TITULO_CORPO, "titulo_espaco": p5.TITULO_ESPACO,
              "titulo_altura": p5.letreiro_1x(["X"], p5.TITULO_CORPO, p5.TITULO_ESPACO).height - 2 * cm.MEDIDAS["corte_titulo"],
              "letreiro_quente": list(render.LETREIRO_QUENTE), "letreiro_claro": list(render.LETREIRO_BRANCO),
              "letreiro_brilho": list(render.LETREIRO_BRILHO), "letreiro_empurra": render.LETREIRO_EMPURRA,
              "fade_fim_imagem": render.FADE_FIM_IMAGEM, "zona_segura": p5.ZONA_SEGURA})
    creditos = {"cargos_primeiro": True, "cargos": [
        {}, {"quem": "O NOIVO\nA NOIVA"}, {"cargo": "Fotografia", "quem": "OS PADRINHOS\nA FAMÍLIA TODA DO NOIVO\nAS MADRINHAS"},
        {"cargo": "Som", "quem": "UM\nDOIS\nTRES\nQUATRO"}, {"quem": "SO QUEM, SEM CARGO"}]}
    textos = p5.textos_dos_creditos({"creditos": creditos})
    grupos = [{"etiqueta": "G1", "titulo": "FAMÍLIA DA CLARA", "sub": "do lado da mãe", "linhas": ["Pessoa Um · Pessoa Dois", "Pessoa Tres"]}]
    cred = {"medidas": M, "folha": "ensaio", "sem_nomes": "", "fotos": {}, "grupos": grupos,
            "omissoes": {"cargos": [{"cargo": c, "quem": q} for c, q in p5.CARGOS], "titulo": p5.TITULO, "data": p5.DATA}}
    pessoas = [p for _c, q in textos["cargos"] for p in p5.pessoas_do_quem(q)]
    med = _medidas_das_letras(render, [{}], (list(range(1, max(p5.QUEM_CORPO, p5.TITULO_CORPO) + 1)) + [130],
                                             pessoas + [p5.TITULO, p5.DATA, "FAMÍLIA DA CLARA"]),
                              ([58], [c for c, _q in textos["cargos"] if c] + ["do lado da mãe", "Pessoa Um · Pessoa Dois", "Pessoa Tres"]))
    corpo_js = MEDIDOR_FALSO % {"med": json.dumps(med, ensure_ascii=False)} + """
var CRED = %(cred)s, credLay = null, credTemFinais = false, porId = {};
function credAberto(){ return false; }
est.creditos = %(creditos)s;
var Lay = credContas(), M = CRED.medidas, I = [];
[0, 0.3, 0.7, 0.9, 2.0, 3.0, 3.75, 4.4].forEach(function(t){ I.push(t); });
for(var k = 1; k < Lay.nCargos; k++) [0.001, 0.1, 0.3, 0.45, 2.0, 3.75, 4.1].forEach(function(u){ I.push(Lay.tCargos + k * M.t_cargo + u); });
[0.02, 0.4, 0.75, 1.2, 1.6, 10].forEach(function(u){ I.push(Lay.tRoloEntra + u); });
[0.0, 0.4, 2.5, 5.5, 6.9].forEach(function(u){ I.push(Lay.tTituloEntra + u); });
var r = {Hr: Lay.Hr, I: I, tempos: [],
  geo: Lay.cargos.map(function(c){ var g = credGeometriaDoCargo(c); return {corpo: g.corpo, sobe: g.sobe, yCargo: g.yCargo, yQuem: g.yQuem, ys: g.ys}; })};
I.forEach(function(t){
  var tela = telaFalsa(); credDesenhaEm(tela, t, false, true);
  var ops = tela.ctx.ops;
  r.tempos.push({alfa: ops.reduce(function(a, x){ return Math.max(a, x.alfa); }, 0),
    tipo: ops.some(function(x){ return /^Pessoa/.test(x.t); }) ? "rolo" : ops.some(function(x){ return / 130px /.test(x.font); }) ? "titulo"
        : ops.length ? "cargo" : "preto",
    letras: ops.filter(function(x){ return x.fill && x.fill.grad && !x.sombra; }).length,
    linha: ops.filter(function(x){ return !(x.fill && x.fill.grad); }).map(function(x){ return x.t; })});
});
console.log(JSON.stringify(r));
""" % {"cred": json.dumps(cred, ensure_ascii=False), "creditos": json.dumps(creditos, ensure_ascii=False)}
    s = _correr_estilo({"pessoas": [], "versoes": [], "tags": {}}, corpo_js, problemas, mais=FUNCOES_DESENHO_CRED,
                       declaracoes=["var CRED_ARIAL = ", "var credLetrasPedidas = "])
    if s:
        n = len(textos["cargos"])
        T = p5.tempos_dos_creditos(s["Hr"], 0, n, True)
        desenho = p5.desenho_dos_creditos(Image.new("RGB", (1040, s["Hr"] + 20)), Image.new("RGB", (800, 40)), textos, {}, T)

        def brilho(t):
            return max(desenho(t).convert("L").getextrema()[1], 0)

        def suave(x):
            x = max(0.0, min(1.0, x))
            return x * x * (3 - 2 * x)
        cheio = {k: brilho(T["t_cargos"] + k * T["t_cargo"] + 2.0) for k in range(n)}
        cheio["titulo"] = brilho(T["t_titulo_entra"] + 2.5)
        piores = []
        for t, m in zip(s["I"], s["tempos"]):
            tc = t - T["t_cargos"]
            k = int(tc // T["t_cargo"]) if tc > 0 else 0
            tr = t - T["t_rolo_entra"] - T["t_entrada"]
            peca = "cargo" if k < n else "rolo" if tr < T["t_rolo"] + 1.0 else "titulo"
            if peca == "rolo":
                alfa = (suave((tr + T["t_entrada"]) / T["t_entrada"]) if tr < 0 else 1.0) * \
                       (1.0 - suave((tr - T["t_rolo"] + 0.8) / 1.6) if tr > T["t_rolo"] - 0.8 else 1.0)
            else:
                alfa = brilho(t) / float(cheio[k if peca == "cargo" else "titulo"])
            if m["tipo"] != peca and not (m["tipo"] == "preto" and alfa < 0.01):
                piores.append("%.2f s: a Mesa desenha %s, o ponto5 %s" % (t, m["tipo"], peca))
            elif abs(m["alfa"] - alfa) > (0.02 if peca == "titulo" else 0.006):
                piores.append("%.2f s (%s): Mesa %.3f, ponto5 %.3f" % (t, peca, m["alfa"], alfa))
            if peca == "cargo" and m["tipo"] == "cargo":
                c, q = textos["cargos"][k]
                if m["letras"] != sum(len(p) for p in p5.pessoas_do_quem(q)) or m["linha"] != ([c] if c else []):
                    piores.append("%.2f s: o cargo %d desenha %d letras e %s" % (t, k + 1, m["letras"], m["linha"]))
        if piores:
            problemas.append("as pecas e os instantes: %s" % "; ".join(piores[:5]))
        if s["tempos"][0]["alfa"] < 0.999:
            problemas.append("o primeiro cargo nao nasce aceso do fim do filme: %.3f no zero" % s["tempos"][0]["alfa"])
        # AS PESSOAS: o corpo, a subida da linha do cargo e o meio de cada pessoa, contra o letreiro do ponto5
        for k, (g, (c, q)) in enumerate(zip(s["geo"], textos["cargos"])):
            gp = p5.geometria_do_cargo(q)
            if (g["corpo"], g["sobe"], g["yCargo"], g["yQuem"]) != (gp["corpo"], gp["sobe"], gp["y_cargo"], gp["y_quem"]):
                problemas.append("cargo %d: Mesa %s, ponto5 %s" % (k + 1, (g["corpo"], g["sobe"], g["yCargo"], g["yQuem"]),
                                                                   (gp["corpo"], gp["sobe"], gp["y_cargo"], gp["y_quem"])))
                continue
            img = p5.letreiro_1x(gp["pessoas"], gp["corpo"], p5.QUEM_ESPACO)
            for i, y in enumerate(g["ys"]):
                topo_p5 = gp["y_quem"] - img.height // 2 + 160 + i * gp["corpo"] * p5.QUEM_ENTRELINHA
                topo_mesa = y - 0.725 * gp["corpo"]
                if abs(topo_p5 - topo_mesa) > 1.5:
                    problemas.append("cargo %d, pessoa %d: o topo das letras a %.1f na Mesa e %.1f no ponto5" % (k + 1, i + 1, topo_mesa, topo_p5))
        if not any(g["corpo"] < p5.QUEM_CORPO for g in s["geo"]) or max(len(g["ys"]) for g in s["geo"]) != 4:
            problemas.append("os cargos de ensaio ja nao provam nada: nenhum encolhe, ou nenhum tem 4 pessoas")
    verifica("Mesa: o desenho dos cargos como o ponto5", s is not None and not problemas,
             "; ".join(problemas)[:500] if problemas else
             "os cargos primeiro em %d instantes iguais aos fotogramas (o primeiro aceso desde o zero, o rolo a entrar do preto, "
             "o titulo), e %d cargos de 1 a 4 pessoas no corpo e no sitio do ponto5" % (len(s["I"]), len(s["geo"])))


def teste_cargos_gravam_desfazem_e_juntam():
    """Os cargos gravam-se so quando ele escolhe, desfazem-se, e sobrevivem a juncao por partes e a uma Mesa antiga.

    O DEFEITO QUE ISTO APANHA:
    - «como está» a gravar alguma coisa (abrir o painel, pintar os cargos, ou escolher «Depois dos convidados» quando ja
      esta assim), ou a lista dos tres de hoje a ficar escrita na base;
    - acrescentar, tirar e mudar a ordem a deixar um campo vazio num dos tres primeiros lugares a puxar o texto de hoje
      calado, a gravar uma lista vazia (o render volta aos tres de hoje), a gravar o quem com linhas vazias, ou o Anular a
      nao repor tudo;
    - o que a Mesa grava a dar outro filme no ponto5 (os cargos do textos_dos_creditos tem de ser os do painel, sem avisos);
    - a ordem num aparelho e um cargo no outro a nao se juntarem, ou os dois a mexer nos cargos sem conflito;
    - uma Mesa antiga a deitar fora a ordem ou os cargos a mais quando muda um titulo.
    """
    if not shutil.which("node"):
        salta("Mesa: os cargos gravam, desfazem e juntam", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    p5 = cm._ponto5()
    problemas = []
    cred = _cred_dos_cargos(p5)
    funcoes = FUNCOES_JUNTAR + FUNCOES_LAYOUT_CRED + FUNCOES_CARGOS
    funcoes = [f for i, f in enumerate(funcoes) if f not in funcoes[:i]]
    prelude = PRELUDE_JUNTAR + """
var CRED = %(cred)s, credTemFinais = false, porId = {}, RENDER_LE = {}, mensagens = [];
function credMsg(t){ mensagens.push(t); }
function esc(s){ return String(s); }
function credResumo(){ credLay = null; return {dur: credContas().dur}; }
function credTextoCurtoDoEfeito(a, d){ return "[" + a.dur.toFixed(4) + " -> " + d.dur.toFixed(4) + "]"; }
""" % {"cred": json.dumps(cred, ensure_ascii=False)} + MESA_53_CARGOS
    B0 = dict(EST_DOS_CARGOS, versoes=[{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}], atual="v1",
              quando="2026-10-02T21:00:00Z", rev=1435, pagina="2026-10-02",
              creditos={"titulo": "CLARA & TIAGO", "musica": {"ficheiro": "x.mp3", "inicio": "fim"}, "ordem": ["f02", "f01"]})
    corpo_js = """
var r = {}, B0 = %(b0)s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
function lista(){ credLay = null; return credContas().cargos.map(function(x){ return [x.cargo, x.pessoas.join("\\n")]; }); }
function foto(rot){ r.passos.push({rot: rot, creditos: est.creditos === undefined ? null : copia(est.creditos), lista: lista(),
  primeiro: credContas().primeiro, dur: credContas().dur, marcas: marcas, msg: mensagens[mensagens.length - 1] || ""}); }
r.passos = [];
// A. COMO ESTA: abrir, pintar os cargos e escolher «Depois dos convidados» nao grava nada
abrir(B0); marcas = 0; var antes = JSON.stringify(est.creditos);
credHtmlDosCargos(); credCargosGuardados(); credContas(); var naoMudou = credPoePartes(CRED_PARTES_HOJE);
r.A = {marcas: marcas, igual: JSON.stringify(est.creditos) === antes, devolveu: naoMudou, pilha: pilhaDesfazer.length};
// B. a ordem, e o anular
credPoePartes(CRED_PARTES_PRIMEIRO); foto("os cargos primeiro");
var de = copia(est.creditos); desfazer(); r.B = {depois: copia(est.creditos), antes: de};
// C. acrescentar, escrever, mudar a ordem, tirar
credPoePartes(CRED_PARTES_PRIMEIRO);
credAcrescentaCargo(); foto("acrescentar (vazio)");
credMudaTexto("cargo", "3", "Fotografia"); foto("o cargo do novo");
credMudaTexto("quem", "3", "  OS PADRINHOS \\n\\n AS MADRINHAS\\r\\nOS IRMAOS  "); foto("as pessoas do novo");
credMoveCargo(3, 0); foto("o novo para primeiro");
credMoveCargo(0, 3); foto("e de volta para o fim");
credAcrescentaCargo(); credMudaTexto("quem", "4", "SO QUEM"); foto("um quinto so com o quem");
credMoveCargo(4, 1); foto("o quinto para segundo (o cargo vazio puxa o de hoje)");
credTiraCargo(1); foto("tirar o segundo");
credTiraCargo(0); foto("tirar o primeiro");
var guardaPilha = pilhaDesfazer.length;
// D. tirar ate ficar um, e o ultimo fica
while(credCargosGuardados().length > 1) credTiraCargo(0);
foto("so um"); r.D = {tirou: credTiraCargo(0), n: credCargosGuardados().length};
// E. o anular repoe cada passo, ate ao principio
var desfeitos = [];
while(pilhaDesfazer.length){ desfazer(); desfeitos.push(est.creditos === undefined ? null : copia(est.creditos)); }
r.E = {fim: est.creditos === undefined ? null : copia(est.creditos), n: desfeitos.length, guardaPilha: guardaPilha};
// F. com os tres de hoje: acrescentar e tirar o acrescentado volta a nao ter a lista; tirar o primeiro grava dois
abrir(B0);
credAcrescentaCargo(); credTiraCargo(3); r.F1 = copia(est.creditos);
credTiraCargo(0); foto("os tres de hoje sem o primeiro"); r.F2 = copia(est.creditos);
// G. menos de tres: acrescentar no terceiro lugar nasce com o texto de hoje desse lugar
credAcrescentaCargo(); foto("acrescentar no terceiro lugar"); r.G = copia(est.creditos.cargos);
// H. dois aparelhos: aqui a ordem, la um cargo; juntam-se. Os dois nos cargos: conflito
abrir(B0); credPoePartes(CRED_PARTES_PRIMEIRO);
var la = com({creditos: Object.assign(copia(B0.creditos), {cargos: [{cargo: "A", quem: "QA"}, {cargo: "B", quem: "QB"}, {cargo: "C", quem: "QC"}, {cargo: "D", quem: "E\\nF"}]}), rev: 1436});
var j = juntarComBase(la);
r.H1 = {ok: j.ok, meus: j.meus, deles: j.deles, creditos: copia(est.creditos),
        partes: Object.keys(partesDe(corpo())).filter(function(k){ return k.indexOf("cargos") >= 0; })};
abrir(B0); credAcrescentaCargo(); credMudaTexto("cargo", "3", "AQUI");
j = juntarComBase(la);
r.H2 = {ok: j.ok, choque: j.choque, cargos: copia(est.creditos.cargos)};
abrir(B0); credPoePartes(CRED_PARTES_PRIMEIRO);
j = juntarComBase(com({creditos: Object.assign(copia(B0.creditos), {cargos_primeiro: true}), rev: 1436}));
r.H3 = {ok: j.ok, primeiro: est.creditos.cargos_primeiro};
// I. a Mesa 53 aberta num separador esquecido: muda o titulo e guarda a ordem e os cinco cargos (copia o est.creditos
//    inteiro); muda um cargo e fica com os tres primeiros (so conhece tres)
var cinco = [{cargo: "A", quem: "QA"}, {cargo: "B", quem: "QB\\nQB2"}, {cargo: "C", quem: "QC"}, {cargo: "D", quem: "QD"}, {cargo: "E", quem: "QE"}];
abrir(com({creditos: Object.assign(copia(B0.creditos), {cargos_primeiro: true, cargos: cinco})}));
credMudaTextoV53("titulo", "", "OUTRO TITULO"); r.I1 = copia(est.creditos);
credMudaTextoV53("cargo", 0, "A2"); r.I2 = copia(est.creditos);
// J. a pagina nova recebe a gravacao da Mesa 53 que so mudou o titulo: a ordem e os cinco cargos ficam
abrir(com({creditos: Object.assign(copia(B0.creditos), {cargos_primeiro: true, cargos: cinco})}));
j = juntarComBase(com({creditos: r.I1, rev: 1436}));
r.J = {ok: j.ok, deles: j.deles, creditos: copia(est.creditos)};
console.log(JSON.stringify(r));
""" % {"b0": json.dumps(B0, ensure_ascii=False)}
    r = _correr_js(DECLARACOES_JUNTAR + DECLARACOES_CARGOS, funcoes, prelude, corpo_js, problemas)
    if r:
        A = r["A"]
        if A["marcas"] or not A["igual"] or A["devolveu"] is not False or A["pilha"]:
            problemas.append("«como está» mexeu: %s" % A)
        if r["B"]["depois"] != B0["creditos"] or r["B"]["antes"].get("cargos_primeiro") is not True or "cargos" in r["B"]["antes"]:
            problemas.append("a ordem e o anular: %s" % r["B"])
        # o que a Mesa grava, lido pelo ponto5: os mesmos cargos que o painel mostra, e sem avisos
        for p in r["passos"]:
            av = []
            t = p5.textos_dos_creditos({"creditos": p["creditos"]} if p["creditos"] is not None else {}, av)
            esperado = [[c, "\n".join(p5.pessoas_do_quem(q))] for c, q in t["cargos"]]
            if av or esperado != p["lista"] or (p["primeiro"] == "cargos") != t["cargos_primeiro"]:
                problemas.append("%s: o ponto5 le %s%s, a Mesa mostra %s" % (p["rot"], esperado, (" e avisa " + "; ".join(av)) if av else "", p["lista"]))
            cs = (p["creditos"] or {}).get("cargos")
            if cs is not None and (not cs or any(set(c) != {"cargo", "quem"} for c in cs) or
                                   any("\n\n" in c["quem"] or c["quem"] != c["quem"].strip() for c in cs)):
                problemas.append("%s: a lista gravada nao esta limpa: %s" % (p["rot"], cs))
        passos = {p["rot"]: p for p in r["passos"]}
        novo = passos["as pessoas do novo"]
        if novo["lista"][3] != ["Fotografia", "OS PADRINHOS\nAS MADRINHAS\nOS IRMAOS"] or \
                passos["acrescentar (vazio)"]["creditos"]["cargos"][3] != {"cargo": "", "quem": ""} or \
                len(passos["acrescentar (vazio)"]["lista"]) != 3:
            problemas.append("o cargo acrescentado: %s" % novo["lista"])
        if abs(novo["dur"] - passos["acrescentar (vazio)"]["dur"] - 4.2) > 1e-9:
            problemas.append("o cargo novo nao acrescenta 4,2 s: %.4f" % (novo["dur"] - passos["acrescentar (vazio)"]["dur"]))
        if passos["o novo para primeiro"]["lista"][0][0] != "Fotografia" or passos["e de volta para o fim"]["creditos"]["cargos"] != novo["creditos"]["cargos"]:
            problemas.append("mudar a ordem: %s" % passos["o novo para primeiro"]["lista"])
        puxa = passos["o quinto para segundo (o cargo vazio puxa o de hoje)"]
        if puxa["lista"][1] != [p5.CARGOS[1][0], "SO QUEM"] or "vale o texto de hoje" not in puxa["msg"]:
            problemas.append("o vazio que sobe para os tres primeiros: %s, %r" % (puxa["lista"][1], puxa["msg"]))
        if r["D"] != {"tirou": False, "n": 1}:
            problemas.append("o ultimo cargo saiu: %s" % r["D"])
        if r["E"]["fim"] != B0["creditos"] or r["E"]["n"] < r["E"]["guardaPilha"]:
            problemas.append("o anular nao voltou ao principio: %s" % r["E"])
        if r["F1"] != B0["creditos"]:
            problemas.append("acrescentar e tirar o acrescentado deixou a lista: %s" % r["F1"])
        if r["F2"].get("cargos") != [{"cargo": c, "quem": q} for c, q in p5.CARGOS[1:]]:
            problemas.append("tirar o primeiro dos de hoje: %s" % r["F2"].get("cargos"))
        if r["G"] != [{"cargo": c, "quem": q} for c, q in p5.CARGOS[1:]] + [{"cargo": p5.CARGOS[2][0], "quem": p5.CARGOS[2][1]}]:
            problemas.append("acrescentar no terceiro lugar: %s" % r["G"])
        H1 = r["H1"]
        if not H1["ok"] or H1["creditos"].get("cargos_primeiro") is not True or len(H1["creditos"].get("cargos") or []) != 4 or \
                sorted(H1["partes"]) != ['["creditos","cargos"]', '["creditos","cargos_primeiro"]'] or \
                H1["meus"] != ["creditos"] or H1["deles"] != ["creditos"]:
            problemas.append("a ordem aqui e os cargos la: %s" % H1)
        if r["H2"]["ok"] or r["H2"]["choque"] != ["creditos"] or r["H2"]["cargos"][3]["cargo"] != "AQUI":
            problemas.append("os cargos nos dois: %s" % r["H2"])
        if not r["H3"]["ok"] or r["H3"]["primeiro"] is not True:
            problemas.append("a mesma ordem nos dois: %s" % r["H3"])
        if r["I1"].get("cargos_primeiro") is not True or len(r["I1"].get("cargos") or []) != 5 or r["I1"].get("titulo") != "OUTRO TITULO":
            problemas.append("a Mesa 53 a mudar o titulo perdeu a ordem ou os cargos: %s" % r["I1"])
        if not r["J"]["ok"] or r["J"]["creditos"].get("cargos_primeiro") is not True or len(r["J"]["creditos"]["cargos"]) != 5 or \
                r["J"]["creditos"].get("titulo") != "OUTRO TITULO":
            problemas.append("a pagina nova a receber a Mesa 53: %s" % r["J"])
    corta = r and len((r["I2"] or {}).get("cargos") or []) == 3
    verifica("Mesa: os cargos gravam, desfazem e juntam", r is not None and not problemas,
             "; ".join(problemas)[:500] if problemas else
             "como esta nao grava; ordem, acrescentar, escrever, mudar a ordem e tirar (%d passos lidos pelo ponto5 sem avisos); "
             "o ultimo fica; o anular volta ao principio; juntam e chocam; a Mesa 53 guarda-os ao mudar o titulo%s"
             % (len(r["passos"]) if r else 0, " (e corta para 3 ao mudar um cargo: recarregar as Mesas abertas)" if corta else ""))


def teste_cargos_o_render_le_e_a_mesa_avisa():
    """O gerar_mesa sabe se o render ja le os cargos, e a Mesa diz «ainda não chega ao filme» so enquanto nao le.

    O DEFEITO QUE ISTO APANHA: a Mesa a deixar escolher os cargos primeiro, ou mais cargos e mais pessoas, sem dizer que o
    filme ainda os ignora (o Tiago e a Clara decidiam a olhar para uma pre-visualizacao que o render nao faz), ou a dize-lo
    quando o render ja os le. E o aviso da largura de quem fez um cargo: com o render de agora encolhe (decisao 109); com
    um render antigo uma pessoa so que nao cabe ainda para o render.
    """
    if not shutil.which("node"):
        salta("Mesa: o render le os cargos e a Mesa avisa", "sem node neste PC")
        return
    import gerar_mesa
    import creditos_para_mesa as cm
    problemas = []
    texto = io.open(PONTO5, encoding="utf-8").read()
    hoje = gerar_mesa.le_os_cargos_dos_creditos(texto)
    if hoje != {"cargos_primeiro": True, "cargos_varios": True, "cargos_max": 8, "pessoas_max": 4}:
        problemas.append("o ponto5 de agora le os cargos, e o gerar_mesa diz %s" % hoje)
    antigo = re.sub(r"cargos_primeiro|^CARGOS_MAX.*$|^def geometria_do_cargo\(", "x", texto, flags=re.M)
    velho = gerar_mesa.le_os_cargos_dos_creditos(antigo)
    if velho != {"cargos_primeiro": False, "cargos_varios": False, "cargos_max": None, "pessoas_max": None}:
        problemas.append("um ponto5 sem os cargos: %s" % velho)
    p5 = cm._ponto5()
    cred = _cred_dos_cargos(p5)
    funcoes = FUNCOES_LAYOUT_CRED + FUNCOES_CARGOS + ["function credAvisoDoTexto(", "function credCorpoDoQuem(",
                                                      "function credMinimoDaLetra(", "function credLetraDe(", "function copiaFunda(",
                                                      # a ordem esta na aba «Ordem e velocidade» desde 3 de outubro
                                                      "function credHtmlDaOrdem(", "function fmtS(", "function mmssDec("]
    prelude = """
var est = %(est)s, CRED = %(cred)s, credLay = null, credTemFinais = false, porId = {}, RENDER_LE = {}, credLargurasGuardadas = {};
var CRED_ARIAL = {id: "arial_bold", nome: "Arial Bold", corpo_minimo: 58};
function esc(s){ return String(s); }
function estiloLetra(){ return null; }
function estiloForaDoPc(){ return false; }
function credFonte(corpo){ return "700 " + corpo + "px Arial"; }
/* a largura de ensaio: 60 px por letra no corpo 110, as outras na mesma proporcao (o desenho e as larguras do PIL ja tem
   o teste_creditos_desenho_e_avisos_como_o_ponto5; aqui so se ve que regra vale) */
function credLargura(t, corpo, espaco){ var n = Array.from(String(t)).length; return n * corpo * 0.55 + Math.max(0, n - 1) * espaco * corpo; }
""" % {"est": json.dumps(dict(EST_DOS_CARGOS, creditos={"cargos_primeiro": True, "cargos": [{}, {}, {}, {"cargo": "D", "quem": "E\nF"}]}),
                         ensure_ascii=False), "cred": json.dumps(cred, ensure_ascii=False)}
    corpo_js = """
var r = {}, largo = "UMA PESSOA COM UM NOME MUITO COMPRIDO";
[["hoje", {cargos_primeiro: true, cargos_varios: true}], ["antigo", {cargos_primeiro: false, cargos_varios: false}], ["sem dizer", {}]].forEach(function(x){
  RENDER_LE = x[1];
  var h = credHtmlDaOrdem() + credHtmlDosCargos();
  r[x[0]] = {ordem: /A ordem dos cargos ainda não chega ao filme/.test(h), cargos: /Mais cargos e mais pessoas ainda não chegam ao filme/.test(h),
             um: credAvisoDoTexto("quem", largo), varias: credAvisoDoTexto("quem", "OS PADRINHOS\\n" + largo),
             seis: credAvisoDoTexto("quem", "A\\nB\\nC\\nD\\nE\\nF")};
});
console.log(JSON.stringify(r));
"""
    r = _correr_js(DECLARACOES_CARGOS, funcoes, prelude, corpo_js, problemas)
    if r:
        if r["hoje"]["ordem"] or r["hoje"]["cargos"] or r["sem dizer"]["ordem"] or r["sem dizer"]["cargos"]:
            problemas.append("a Mesa diz que nao chega com um render que ja le, ou sem saber: %s" % r)
        if not (r["antigo"]["ordem"] and r["antigo"]["cargos"]):
            problemas.append("com um render antigo a Mesa nao diz que ainda nao chega: %s" % r["antigo"])
        for k in ("hoje", "sem dizer"):
            if not ("encolhe-o para" in r[k]["um"] and "encolhem todas para" in r[k]["varias"] and "pára" not in r[k]["um"]):
                problemas.append("%s: o quem que nao cabe nao encolhe: %r, %r" % (k, r[k]["um"][:80], r[k]["varias"][:80]))
            if "as últimas 2 ficam de fora" not in r[k]["seis"]:
                problemas.append("%s: seis pessoas sem aviso: %r" % (k, r[k]["seis"]))
        if not r["antigo"]["um"].startswith("Não cabe") or "pára" not in r["antigo"]["um"] or "encolhem todas" not in r["antigo"]["varias"]:
            problemas.append("com um render antigo: %r, %r" % (r["antigo"]["um"][:80], r["antigo"]["varias"][:80]))
    le = gerar_mesa.o_que_o_render_le()
    if not all(k in le for k in ("cargos_primeiro", "cargos_varios", "cargos_max", "pessoas_max")):
        problemas.append("o o_que_o_render_le nao traz os cargos: %s" % sorted(le))
    verifica("Mesa: o render le os cargos e a Mesa avisa", r is not None and not problemas,
             "; ".join(problemas)[:500] if problemas else
             "o ponto5 de agora le a ordem, 8 cargos e 4 pessoas; um ponto5 sem eles da false e a Mesa diz que ainda nao chega; "
             "o quem que nao cabe encolhe (com o render antigo, uma pessoa so ainda para)")


def teste_mesa_montada_traz_os_cargos():
    """A Mesa montada traz o que o render le dos cargos e as medidas deles, e o painel dos cargos."""
    if not shutil.which("node"):
        salta("Mesa: a Mesa montada traz os cargos", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    p5 = cm._ponto5()
    problemas = []
    html = _montar_mesa_a_parte("mesa_cargos_")
    m = re.search(r"window\.RENDER_LE = (\{.*?\});\n", html)
    le = json.loads(m.group(1)) if m else {}
    if (le.get("cargos_primeiro"), le.get("cargos_varios"), le.get("cargos_max"), le.get("pessoas_max")) != (True, True, 8, 4):
        problemas.append("o RENDER_LE da pagina: %s" % {k: le.get(k) for k in ("cargos_primeiro", "cargos_varios", "cargos_max", "pessoas_max")})
    m = re.search(r"\nwindow\.CREDITOS_NOMES = (.*?);\n</script>", html, re.S)
    medidas = json.loads(m.group(1).replace("<\\/", "</"))["medidas"] if m else {}
    for chave, nome in (("quem_entrelinha", "QUEM_ENTRELINHA"), ("cargos_max", "CARGOS_MAX"), ("pessoas_max", "PESSOAS_MAX"),
                        ("t_cargo", "T_CARGO"), ("cargo_entra", "CARGO_ENTRA"), ("quem_corpo", "QUEM_CORPO")):
        if medidas.get(chave) != getattr(p5, nome):
            problemas.append("%s na pagina %r, no ponto5 %r" % (chave, medidas.get(chave), getattr(p5, nome)))
    for marca in ("function credHtmlDosCargos(", "function credGeometriaDoCargo(", 'data-cpordem="hoje"', "credMaisCargo"):
        if marca not in html:
            problemas.append("a pagina nao traz %s" % marca)
    verifica("Mesa: a Mesa montada traz os cargos", not problemas, "; ".join(problemas)[:400] if problemas else
             "o render le a ordem e os cargos (8 e 4), as medidas dos cargos do ponto5, e o painel; 0 ficheiros novos")


def teste_texto_depressa_conta_as_letras_do_filme():
    """O «Passa depressa de mais» conta as letras que o filme mostra, e nao as metades UTF-16 do JavaScript.

    O DEFEITO QUE ISTO APANHA (revisor do browser, 2 de outubro a noite): o corridaDoTexto() contava o t.length, e com os
    emojis a cores (decisao do Tiago, render3) um emoji contava 2 letras e um com o tom de pele 4: «... fugir 👍🏽» dava 55
    letras e pedia 4,6 s. Conta-se cada ponto de codigo, sem os que o render nao desenha (ZWJ, seletores de variante,
    etiquetas) nem os que tira (U+200B, U+2060, U+FEFF); o tom de pele, que no filme sai num quadrado ao lado, conta.
    O testes.py (teste_mesa_marca_o_texto_que_passa_depressa) corre so estas funcoes, por isso a conta fica dentro do
    corridaDoTexto().
    """
    if not shutil.which("node"):
        salta("Mesa: o texto depressa conta as letras do filme", "sem node neste PC")
        return
    problemas = []
    textos = ["Agarrado pelo irmão mais velho, mas a tentar fugir 👍🏽", "Que surpresa 😮", "A MÃE DA CLARA 👩‍👧",
              "Gosto ❤️ muito", "a​b⁠c﻿", "Em Barcelona", "Bandeira 🇵🇹 e tecla 1️⃣",
              "Escócia 🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f", "  dois   espaços  "]
    # (um U+FEFF no meio do texto o \s do JavaScript ja o tinha feito espaco no textoNoEcraDoClip(); no fim, sai com ele)
    invisiveis = re.compile("[​‍⁠︎️﻿\U000e0020-\U000e007f]")
    esperado = [len(invisiveis.sub("", " ".join(t.split()))) for t in textos]
    funcoes = ["function eGrupo(", "function clipsDoCorpo(", "function encadeadoDoClip(", "function encadeadosDe(",
               "function videoNoCorpo(", "function pecaDoVideo(", "function duraDoVideo(", "function trocoDoVideo(",
               "function duracaoDoVideoNoFilme(", "function duracaoDoClip(", "function contadoresSeguidos(",
               "function pontoDoContador(", "function lerContador(", "function eDataContador(", "function dataParaIso(",
               "function d2(", "function modoTextos(", "function tamanhoValido(", "function chaveDoClipBase(",
               "function chavesDaVersao(", "function srDaVersao(", "function renderPorClip(", "function duracaoNoRender(",
               "function sozinhoNoEcra(", "function textoNoEcraDoClip(", "function corridaDoTexto(", "function textoDenso("]
    corpo_js = """
var r = TEXTOS.map(function(t){
  var v = {clips: [{t: "foto", x: "a", d: 4, c: 0.7}, {t: "foto", x: t, d: 4, c: 0.7}, {t: "foto", x: "z", d: 4, c: 0.7}]};
  return textoDenso(v, 1).letras;
});
console.log(JSON.stringify(r));
"""
    prelude = ("var XF_CPS = 12, XF_LONGO = 32, TT_OMISSAO = 46, TT_MIN = 28, TT_MAX = 90, VIDS = [], SR = null, TEXTOS = %s;"
               % json.dumps(textos, ensure_ascii=False))
    r = _correr_js(["var MONTE = "], ["function s1("] + funcoes, prelude, corpo_js, problemas)
    if r is not None and r != esperado:
        problemas.append("a Mesa conta %s letras e o filme mostra %s" % (r, esperado))
    verifica("Mesa: o texto depressa conta as letras do filme", not problemas, "; ".join(problemas)[:400] if problemas else
             "%d textos com emojis, tom de pele, ZWJ, bandeira, tecla, etiquetas e os que se tiram: %s letras, como o filme"
             % (len(textos), r))


# ------------------------------------------------- as legendas de 3 de outubro (contrato_1003, pontos 1 a 4)
# O Tiago, a 3 de outubro, de madrugada: a letra do contador, a legenda numa so linha, a posicao das legendas (a de todas e
# a de cada clip) e as fotos inteiras do lado a lado. O render faz (render.py, linha_tempo.py, montar_da_mesa.py); a Mesa
# deixa escolher, mostra com as mesmas contas e avisa. Guarda-se aqui que:
#  17. as contas da Mesa sao as do render: os limites, a posicao de todas mais a do clip, o dx que encosta a margem, o x de
#      cada linha, as celulas do lado a lado e quanto o enchimento corta;
#  18. «como esta» nao grava nada, cada escolha grava so a sua chave (est.estilo.legenda.posicao, est.estilo.contador.fonte,
#      clip.x1, clip.lp, clip.li), passa pelo anular, o montar e o render leem o que a Mesa grava sem um aviso, e a juncao
#      de dois aparelhos e uma Mesa antiga nao as perdem;
#  19. a Mesa avisa a legenda que nao cabe numa linha com as palavras do contrato, o lado a lado que corta mais de 25%, a
#      letra do contador que se le pior a 15 m nos casos em que o render avisa, e diz «ainda nao chega ao filme» enquanto o
#      render nao ler a chave;
#  20. o gerar_mesa pergunta ao desenho do render, e nao so a limpeza do estilo.
DECLARACOES_LEG = ["var LEGENDA_LADO = ", "var LADO_CORTE_AVISO = ", "var LADO_FOLGA_PX = ", "var LADO_INTEIRA = ",
                   "var PISO_DA_LEGENDA = ", "var lpUltimoToque = "]
FUNCOES_LEG = ["function lpDoClip(", "function x1Do(", "function liDo(", "function x1NoFilme(", "function liNoFilme(", "function legPosicao(", "function legDxEfetivo(",
               "function legXs(", "function legJunta(", "function legNumaLinha(", "function legLinhas(",
               "function legPisoDoGrupo(", "function ladoCelulas(", "function ladoCorte(", "function ladoCorteDoClip(",
               "function ladoPct(", "function ladoCortadas(", "function avisoLadoCorta(", "function avisosNumaLinha(",
               "function estiloMede(", "function estiloQuebra("]
FUNCOES_LEG_INSPETOR = ["function temLegendaDeBaixo(", "function textoDaLegendaDoClip(", "function notaNumaLinha(",
                        "function legNoLimite(", "function x1NaoCabe(", "function notaPosicaoDoClip(", "function lpSetaParada(",
                        "function lpPoe(", "function lpPasso(", "function lpRepor(", "function x1Poe(", "function liPoe(",
                        "function guardaDesfazerCampos(", "function desfazer(", "function ordemDoClip("]
FUNCOES_LEG_ESTILO = ["function estiloPoePosicao(", "function estiloSetaPosicao(", "function estiloComoEsta(",
                      "function estiloCssContador(", "function palcoCssContador(", "function estiloGaranteLetra("]
APOIO_LEG = """
var porId = %(porid)s, estiloPassoEm = 0, estiloLetrasPedidas = {}, clipAtivo = 0, selClips = [], ancoraSel = -1, marcas = 0, avisos = [];
function eGrupo(c){ return c && (c.t === "lado" || c.t === "colagem" || c.t === "pilha"); }
function modoTextos(c){ return c.vf ? (c.vm === "legenda" ? "legenda" : "foto") : ""; }
function temTextosFotos(c){ return (c.xf || []).some(function(t){ return String(t || "").trim(); }); }
function textosDasFotos(c){ return (c.fotos || []).map(function(_f, k){ return (c.xf || [])[k] || ""; }); }
function tamanhoTextos(c){ return c.tt || estiloValor("legenda", "tamanho"); }
function estiloDe(c){ return c.estilo || ""; }
function estiloEsqueceMeu(){}
function marcar(){ marcas++; }
function avisar(t){ avisos.push(t); }
function nada(){}
var pintaClips = nada, pintaVersoes = nada, pintaInspetor = nada, pintaGrelha = nada;
function aproximaAtivo(){ return false; }
function temVozes(){ return false; }
function videoNoCorpo(){ return false; }
function opcoesTextos(){ return undefined; }
"""


def teste_legendas_1003_como_o_render():
    """A posicao das legendas, o dx que encosta a margem, as celulas do lado a lado e o corte: as contas do render.

    O DEFEITO QUE ISTO APANHA: a Mesa a mostrar a legenda 40 px acima e o filme a po-la noutro sitio (outro limite, outra
    margem, a soma da de todas com a do clip cortada de outra maneira), uma legenda comprida que na Mesa anda os 200 px
    pedidos e no filme encosta a margem, e a Mesa a dizer que uma foto perde 34% quando o render corta 41% (outra celula,
    outra conta): ele decidia as «fotos inteiras» por um numero que nao e o do filme.
    """
    if not shutil.which("node"):
        salta("Mesa: as legendas de 3 de outubro como o render", "sem node neste PC")
        return
    import render
    problemas = []
    precisos = ("LEGENDA_MARGEM_LADO", "POSICAO_DX", "POSICAO_DY", "POSICAO_ALINHAMENTOS", "LP_DX", "LP_DY", "LADO_CORTE_AVISO",
                "LADO_FOLGA", "PISO_MINIMO_DA_LEGENDA", "posicao_da_legenda", "dx_efetivo", "x_das_linhas", "ler_opcoes_clip",
                "lado_celulas", "lado_corte", "piso_da_legenda")
    faltam = [n for n in precisos if not hasattr(render, n)]
    if faltam:
        salta("Mesa: as legendas de 3 de outubro como o render", "o render ainda nao tem %s" % ", ".join(faltam))
        return
    posicoes = [None, {}, {"dy": -40}, {"dx": 120, "dy": -500}, {"dx": -600, "alinhamento": "direita"}, {"dx": 601},
                {"dy": 10}, {"dy": -501}, {"dx": "40", "dy": "-80", "alinhamento": "esquerda"}, {"dx": 40.0, "dy": -80.5},
                {"dx": True, "alinhamento": "meio"}, {"alinhamento": "centro"}, "acima", {"dx": 300, "dy": -200, "x": 1}]
    lps = [None, {}, {"dx": 10, "dy": -40}, {"dy": 500}, {"dy": 501}, {"dx": -1200, "dy": -500}, {"dx": 1201}, {"dx": "abc"},
           {"dx": "-30", "dy": 40.0}, {"dy": 40.5}, [1, 2], {"dx": 900, "dy": 300}]
    larguras = [[], [400.0], [1660.0], [1700.5], [300.0, 1200.25, 80.0], [1659.0, 20.0]]
    dxs = [0, 1, -1, 130, -130, 229.75, 600, -600]
    tamanhos = [[(4000, 3000), (3000, 4000)], [(1600, 1200), (1080, 1920), (1920, 1080)], [(956, 1080), (1000, 1000)],
                [(4000, 3000)] * 4, [(3000, 4000)] * 6, [(4000, 3000), None, (0, 10)], [(2048, 1365), (1365, 2048), (4000, 3000)]]
    js = """
var r = {consts: {margem: LEGENDA_LADO, pos: LEG_POS, aviso: LADO_CORTE_AVISO, folga: LADO_FOLGA_PX, inteira: LADO_INTEIRA, piso: PISO_DA_LEGENDA,
                  textos: ESTILO_TEXTOS_DO_CONTADOR.map(function(x){ return x[1]; })}};
var P = %s, LP = %s, LARG = %s, DX = %s, TAM = %s;
r.posicao = P.map(function(p){
  return LP.map(function(lp){
    if(p === null) delete est.estilo; else est.estilo = {legenda: {posicao: p}};
    var q = legPosicao(lp === null ? {} : {lp: lp});
    return [q.dx, q.dy, q.alinhamento];
  });
});
r.limpa = P.map(function(p){ var l = p === null ? null : legPosicaoLimpa(p); return l ? legPosicaoCompacta(l) : {}; });
delete est.estilo;
r.xs = LARG.map(function(l){ return DX.map(function(dx){ return ["centro", "esquerda", "direita"].map(function(a){ return [legDxEfetivo(l, dx, a), legXs(l, dx, a)]; }); }); });
r.celulas = {}; r.corte = {};
["2v", "3v", "3s", "4q", "6g"].forEach(function(lay){
  r.celulas[lay] = ladoCelulas(lay);
  r.corte[lay] = TAM.map(function(t){ return ladoCorte(lay, t); });
});
r.piso = [0, -10, -200, -270, -400, -500].map(function(dy){ if(dy) est.estilo = {legenda: {posicao: {dy: dy}}}; else delete est.estilo; return legPisoDoGrupo({}, 1080); });
delete est.estilo;
/* numa so linha: junta as mudancas de linha, cabe ou parte como hoje (a medida do node e a de reserva, 0,58 do corpo por letra) */
var curto = "Clara\\ne Tiago", longo = new Array(40).join("palavra ");
r.linhas = {curtoHoje: legLinhas(curto, 46, false).linhas, curtoUma: legLinhas(curto, 46, true), longoHoje: legLinhas(longo, 46, false).linhas.length,
            longoUma: legLinhas(longo, 46, true).linhas.length, longoCabe: legNumaLinha(longo, 46), curtoCabe: legNumaLinha(curto, 46), ha: legNumaLinha("", 46)};
console.log(JSON.stringify(r));
""" % (json.dumps(posicoes), json.dumps(lps), json.dumps(larguras), json.dumps(dxs),
       json.dumps([[list(t) if t else None for t in grupo] for grupo in tamanhos]))
    s = _correr_estilo({}, js, problemas, mais=FUNCOES_LEG, declaracoes=DECLARACOES_LEG)
    contas = 0
    if s:
        c = s["consts"]
        esperado = {"margem": render.LEGENDA_MARGEM_LADO, "aviso": render.LADO_CORTE_AVISO, "folga": render.LADO_FOLGA,
                    "piso": render.PISO_MINIMO_DA_LEGENDA}
        for k, v in esperado.items():
            if c[k] != v:
                problemas.append("a Mesa tem %s = %s e o render %s" % (k, c[k], v))
        pos = c["pos"]
        if (tuple(pos["dx"]), tuple(pos["dy"]), tuple(pos["lpDx"]), tuple(pos["lpDy"]), tuple(pos["alinhamentos"])) != \
                (tuple(render.POSICAO_DX), tuple(render.POSICAO_DY), tuple(render.LP_DX), tuple(render.LP_DY), tuple(render.POSICAO_ALINHAMENTOS)):
            problemas.append("os limites da posicao da Mesa %s nao sao os do render" % pos)
        if hasattr(render, "CORPOS_DO_CONTADOR") and c["textos"] != [corpo for _q, corpo in render.CORPOS_DO_CONTADOR]:
            problemas.append("os corpos do contador da Mesa %s nao sao os do render %s" % (c["textos"], render.CORPOS_DO_CONTADOR))
        if hasattr(render, "lado_inteira"):
            import inspect
            fonte = inspect.getsource(render.lado_inteira)
            if "GaussianBlur(%d)" % c["inteira"]["desfoque"] not in fonte or ", %s)" % c["inteira"]["brilho"] not in fonte:
                problemas.append("o fundo das fotos inteiras da Mesa %s nao e o do render.lado_inteira()" % c["inteira"])
        try:
            for p, linha in zip(posicoes, s["posicao"]):
                avisos = []
                render.aplicar_estilo({} if p is None else {"legenda": {"posicao": p}}, avisos)
                limpo = (render.estilo_ativo().get("legenda") or {}).get("posicao") or {}
                if s["limpa"][posicoes.index(p)] != limpo:
                    problemas.append("a posicao %r limpa-se %s na Mesa e %s no render" % (p, s["limpa"][posicoes.index(p)], limpo))
                for lp, meu in zip(lps, linha):
                    o = render.ler_opcoes_clip(json.dumps({"lp": lp})) if lp is not None else None
                    dele = list(render.posicao_da_legenda(o))
                    contas += 1
                    if meu != dele:
                        problemas.append("posicao %r com lp %r: a Mesa da %s e o render %s" % (p, lp, meu, dele))
        finally:
            render.aplicar_estilo({}, [])
        for l, por_dx in zip(larguras, s["xs"]):
            for dx, por_al in zip(dxs, por_dx):
                for al, (ef, xs) in zip(("centro", "esquerda", "direita"), por_al):
                    contas += 1
                    if abs(ef - render.dx_efetivo(l, dx, al)) > 1e-9 or len(xs) != len(l) or \
                            any(abs(a - b) > 1e-9 for a, b in zip(xs, render.x_das_linhas(l, dx, al))):
                        problemas.append("larguras %s, dx %s, %s: a Mesa da %s %s e o render %s %s"
                                         % (l, dx, al, ef, xs, render.dx_efetivo(l, dx, al), render.x_das_linhas(l, dx, al)))
        for lay in ("2v", "3v", "3s", "4q", "6g"):
            dele = [list(r) for r, _vem in render.lado_celulas(lay)]
            if s["celulas"][lay] != dele:
                problemas.append("as celulas do %s: a Mesa %s e o render %s" % (lay, s["celulas"][lay], dele))
            for t, meu in zip(tamanhos, s["corte"][lay]):
                certo = render.lado_corte(lay, t)
                contas += 1
                if len(meu) != len(certo) or any((a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9)
                                                 for a, b in zip(meu, certo)):
                    problemas.append("o corte do %s com %s: a Mesa %s e o render %s" % (lay, t, meu, certo))
        for dy, meu in zip([0, -10, -200, -270, -400, -500], s["piso"]):
            certo = render.piso_da_legenda(None if dy == 0 else 0.5 * render.A + dy)
            if abs(meu - certo) > 1e-9:
                problemas.append("o piso das fotos com a legenda %d acima: a Mesa %s e o render %s" % (-dy, meu, certo))
        li = s["linhas"]
        if li["curtoHoje"] != ["Clara", "e Tiago"] or li["curtoUma"]["linhas"] != ["Clara e Tiago"] or not li["curtoUma"]["uma"] \
                or li["curtoUma"]["tam"] != 46:
            problemas.append("numa linha, o texto curto: %s e %s" % (li["curtoHoje"], li["curtoUma"]))
        if li["longoUma"] != li["longoHoje"] or li["longoHoje"] < 2 or li["longoCabe"]["cabe"] or not li["curtoCabe"]["cabe"]:
            problemas.append("numa linha, o texto que nao cabe devia partir como hoje: %s" % li)
        if li["ha"]["ha"] != render.L - 2 * render.LEGENDA_MARGEM_LADO or li["longoCabe"]["ha"] != li["ha"]["ha"]:
            problemas.append("a largura util da Mesa e %s e a do render %s" % (li["ha"]["ha"], render.L - 2 * render.LEGENDA_MARGEM_LADO))
    verifica("Mesa: as legendas de 3 de outubro como o render", not problemas and contas > 0, "; ".join(problemas)[:500] if problemas else
             "os limites, %d contas da posicao, da margem e do corte iguais, 5 disposicoes, o piso das fotos e a linha so" % contas)


def teste_legendas_1003_gravam_desfazem_e_juntam():
    """«Como está» nao grava nada; cada escolha grava a sua chave, desfaz-se, e o montar e o render leem-na sem aviso.

    O DEFEITO QUE ISTO APANHA: abrir e fechar a deixar um x1 false, um lp {0, 0} ou uma posicao vazia na base (o montar
    escrevia a coluna opcoes_clip e o estilo.json sem ninguem escolher nada, e o filme deixava de sair igual ao byte); uma
    seta a passar dos limites (a legenda abaixo do sitio de hoje, que o projetor corta); dez toques numa seta a dar dez
    entradas no anular; o «Como está (original)» das legendas a deixar a posicao; uma proposta de cores do contador a
    apagar a letra dele; o montar a recusar o que a Mesa grava; e dois aparelhos, ou uma Mesa antiga, a perder a posicao.
    """
    if not shutil.which("node"):
        salta("Mesa: as legendas de 3 de outubro gravam, desfazem e juntam", "sem node neste PC")
        return
    import render
    problemas = []
    base = {"versoes": [{"id": "v1", "nome": "demo", "clips": [
        {"t": "foto", "i": "f1", "x": "Com a avó", "d": 4, "c": 0.7, "r": "fundo"},
        {"t": "lado", "fotos": ["f1", "f2"], "lay": "2v", "x": "Os dois", "d": 5, "c": 0.7, "r": "fiel"},
        {"t": "cartao", "x": "1995", "d": 3, "c": 0.7}]}], "atual": "v1", "pessoas": [], "tags": {}}
    porid = {"f1": {"id": "f1", "w": 4000, "h": 3000}, "f2": {"id": "f2", "w": 3000, "h": 4000}}
    js = (APOIO_LEG % {"porid": json.dumps(porid)}) + """
var v = est.versoes[0], foto = v.clips[0], lado = v.clips[1], r = {};
function c1(c){ return JSON.parse(JSON.stringify({x1: c.x1, lp: c.lp, li: c.li})); }
function estilo(){ return est.estilo === undefined ? null : JSON.parse(JSON.stringify(est.estilo)); }
/* 1. como esta: desligar o que ja esta desligado, repor o que nao tem posicao, nao mexe em nada nem abre o anular */
r.nada = [x1Poe(foto, false), liPoe(lado, false), lpRepor(foto), estiloPoePosicao("dy", 0, "a"), estiloPoePosicao("alinhamento", "centro", "b"),
          c1(foto), c1(lado), estilo(), pilhaDesfazer.length, marcas];
/* 2. numa so linha e as fotos inteiras: so o true, e o anular tira a chave */
x1Poe(foto, true); liPoe(lado, true); r.sim = [c1(foto), c1(lado), pilhaDesfazer.length];
desfazer(); desfazer(); r.desfeito = [c1(foto), c1(lado), "x1" in foto, "li" in lado];
x1Poe(foto, true); x1Poe(foto, false); liPoe(lado, true); liPoe(lado, false); r.voltou = [c1(foto), c1(lado), "x1" in foto, "li" in lado];
pilhaDesfazer.length = 0;
/* 3. as setas do clip: 10 px, toques seguidos numa entrada do anular, e os limites do total */
for(var k = 0; k < 4; k++) lpPasso(foto, "cima");
lpPasso(foto, "dir"); r.setas = [c1(foto), pilhaDesfazer.length, notaPosicaoDoClip(foto)];
r.baixoNoZero = [lpPasso(lado, "baixo"), c1(lado), lpSetaParada(lado, "baixo"), lpSetaParada(lado, "cima")];
for(k = 0; k < 80; k++) lpPasso(lado, "cima");
for(k = 0; k < 80; k++) lpPasso(lado, "esq");
r.limites = [c1(lado), lpSetaParada(lado, "cima"), lpSetaParada(lado, "esq"), legPosicao(lado)];
desfazer(); r.anulaSetas = c1(lado);
lpRepor(foto); r.reposto = [c1(foto), "lp" in foto]; desfazer(); r.repostoAnulado = c1(foto);
/* com a de todas 100 acima, o clip pode descer ate ao sitio de hoje, e nao mais */
est.estilo = {legenda: {posicao: {dy: -100}}}; delete lado.lp; pilhaDesfazer.length = 0;
for(k = 0; k < 20; k++) lpPasso(lado, "baixo");
r.desce = [c1(lado), legPosicao(lado), lpSetaParada(lado, "baixo")];
delete est.estilo; delete lado.lp; delete foto.lp; pilhaDesfazer.length = 0;
/* um lp mal escrito na base: vale zero, e a primeira seta limpa-o */
foto.lp = {dx: "abc", dy: 9999}; r.lixo = [lpDoClip(foto), lpPasso(foto, "cima"), c1(foto)]; delete foto.lp; pilhaDesfazer.length = 0;
/* 4. a posicao de todas: as setas, as barras e o alinhamento gravam so o que difere, e o «original» e o «Como está» tiram-na */
for(k = 0; k < 6; k++) estiloSetaPosicao("cima");
estiloSetaPosicao("dir"); r.estiloSetas = [estilo(), pilhaDesfazer.length, estiloTextoDoValor("legenda", "posicao", estiloValor("legenda", "posicao")),
                                         estiloMudancas("legenda"), estiloParteMudada("legenda")];
estiloPoePosicao("alinhamento", "esquerda", "x1"); r.alinha = estilo();
estiloPoePosicao("dy", -700, "x2"); estiloPoePosicao("dx", 900, "x3"); r.estiloLimites = estilo();
r.baixo = [estiloPoePosicao("dy", 40, "x4"), estilo().legenda.posicao.dy];
estiloComoEsta("legenda.posicao"); r.original = estilo();
pilhaDesfazer[pilhaDesfazer.length - 1].aoAnular(); r.originalAnulado = estilo();
est.estilo.legenda.tamanho = 60; estiloReporParte("legenda"); r.comoEsta = estilo(); estiloVoltarAoMeu("legenda"); r.meu = estilo();
delete est.estilo; pilhaDesfazer.length = 0;
/* 5. a letra do contador: da lista das legendas, o Arial Bold tira a chave, e as propostas de cores nao lhe mexem */
r.letra = [estiloPoe("contador", "fonte", "georgia_bold"), estilo(), estiloPoe("contador", "fonte", "nao_ha"), estiloPoe("contador", "fonte", "impact")];
estiloPoePaleta("contador", 2); r.paleta = [estilo(), estiloPaletaAtiva("contador", 2), Object.keys(estiloCoresContador()).indexOf("fonte")];
estiloPoePaleta("contador", 0); r.paleta0 = estilo();
estiloPoe("contador", "fonte", "arial_bold"); r.arial = estilo();
r.css = [palcoCssContador(46)];
est.estilo = {contador: {fonte: "georgia_bold"}}; RENDER_LE = {contador_fonte: true}; r.css.push(palcoCssContador(46), estiloCssContador(46));
RENDER_LE = {contador_fonte: false}; r.css.push(palcoCssContador(46), estiloCssContador(46)); RENDER_LE = {};
delete est.estilo;
/* 6. o que vai nas «Ordens para o Claude» */
foto.x1 = true; foto.lp = {dx: 10, dy: -40}; lado.li = true;
r.ordens = [ordemDoClip(v, foto, 0), ordemDoClip(v, lado, 1), ordemDoClip(v, v.clips[2], 2)].map(function(o){
  return {x1: o.legenda_numa_linha, lp: o.legenda_posicao, li: o.fotos_inteiras}; });
r.clips = v.clips;
console.log(JSON.stringify(r));
"""
    s = _correr_estilo(base, js, problemas, mais=FUNCOES_LEG + FUNCOES_LEG_INSPETOR + FUNCOES_LEG_ESTILO + [
        "function estiloPoePaleta(", "function estiloCoresContador(", "function estiloRgb(", "function estiloCss("],
        declaracoes=DECLARACOES_LEG)
    vazio = {}
    if s:
        if s["nada"] != [False, False, False, False, False, vazio, vazio, None, 0, 0]:
            problemas.append("«como está» mexeu em alguma coisa: %s" % s["nada"])
        if s["sim"] != [{"x1": True}, {"li": True}, 2] or s["desfeito"] != [vazio, vazio, False, False] or s["voltou"] != [vazio, vazio, False, False]:
            problemas.append("numa linha e fotos inteiras: %s, desfeito %s, de volta %s" % (s["sim"], s["desfeito"], s["voltou"]))
        if s["setas"][:2] != [{"lp": {"dx": 10, "dy": -40}}, 1] or "40 px acima, 10 px à direita" not in s["setas"][2]:
            problemas.append("quatro toques para cima e um para a direita: %s" % s["setas"])
        if s["baixoNoZero"] != [False, vazio, True, False]:
            problemas.append("a seta para baixo no sitio de hoje devia nao fazer nada: %s" % s["baixoNoZero"])
        if s["limites"][0] != {"lp": {"dx": -600, "dy": -500}} or s["limites"][1:3] != [True, True] or \
                s["limites"][3] != {"dx": -600, "dy": -500, "alinhamento": "centro"} or s["anulaSetas"] != vazio:
            problemas.append("os limites das setas do clip: %s, e o anular deu %s" % (s["limites"], s["anulaSetas"]))
        if s["reposto"] != [vazio, False] or s["repostoAnulado"] != {"lp": {"dx": 10, "dy": -40}}:
            problemas.append("o repor: %s, anulado %s" % (s["reposto"], s["repostoAnulado"]))
        if s["desce"] != [{"lp": {"dx": 0, "dy": 100}}, {"dx": 0, "dy": 0, "alinhamento": "centro"}, True]:
            problemas.append("com todas 100 acima, o clip desce ate hoje e nao mais: %s" % s["desce"])
        if s["lixo"] != [{"dx": 0, "dy": 0}, True, {"lp": {"dx": 0, "dy": -10}}]:
            problemas.append("um lp mal escrito: %s" % s["lixo"])
        if s["estiloSetas"] != [{"legenda": {"posicao": {"dx": 10, "dy": -60}}}, 1, "60 px acima, 10 px à direita", ["a posição das legendas"], True]:
            problemas.append("as setas do estilo: %s" % s["estiloSetas"])
        if s["alinha"] != {"legenda": {"posicao": {"dx": 10, "dy": -60, "alinhamento": "esquerda"}}}:
            problemas.append("o alinhamento: %s" % s["alinha"])
        if s["estiloLimites"] != {"legenda": {"posicao": {"dx": 600, "dy": -500, "alinhamento": "esquerda"}}} or s["baixo"] != [True, None]:
            problemas.append("os limites da posicao de todas: %s, e para baixo %s" % (s["estiloLimites"], s["baixo"]))
        if s["original"] is not None or (s["originalAnulado"] or {}).get("legenda", {}).get("posicao", {}).get("alinhamento") != "esquerda":
            problemas.append("o «original» da posicao deixou %s, e o anular deu %s" % (s["original"], s["originalAnulado"]))
        if s["comoEsta"] is not None or "posicao" not in (s["meu"] or {}).get("legenda", {}) or s["meu"]["legenda"].get("tamanho") != 60:
            problemas.append("«Como está» das legendas deixou %s e o teu de ha pouco voltou %s" % (s["comoEsta"], s["meu"]))
        if s["letra"] != [True, {"contador": {"fonte": "georgia_bold"}}, False, False]:
            problemas.append("a letra do contador: %s" % s["letra"])
        if s["paleta"][0].get("contador", {}).get("fonte") != "georgia_bold" or not s["paleta"][1] or s["paleta"][2] != -1 or \
                s["paleta0"] != {"contador": {"fonte": "georgia_bold"}} or s["arial"] is not None:
            problemas.append("as propostas de cores mexeram na letra do contador: %s, %s, e o Arial deixou %s" % (s["paleta"], s["paleta0"], s["arial"]))
        arial = "700 46px Arial, Helvetica, sans-serif"
        if s["css"][0] != arial or "Georgia" not in s["css"][1] or "Georgia" not in s["css"][2] or s["css"][3] != arial or "Georgia" not in s["css"][4]:
            problemas.append("a letra do contador no palco e na amostra: %s" % s["css"])
        if s["ordens"] != [{"x1": True, "lp": {"dx": 10, "dy": -40}}, {"li": True}, {}]:
            problemas.append("as ordens para o Claude levam %s" % s["ordens"])
        # O QUE A MESA GRAVA E O QUE O RENDER E O MONTAR LEEM, sem um aviso
        for estilo in (s["estiloSetas"][0], s["alinha"], s["estiloLimites"], s["letra"][1], s["paleta"][0]):
            av = []
            if render.normalizar_estilo(estilo, av) != estilo or av:
                problemas.append("o render limpa %s de outra maneira: %s %s" % (estilo, render.normalizar_estilo(estilo), av))
        try:
            montar = _montar_calado()
            for c, tipo in zip(s["clips"], ("foto", "lado", "cartao")):
                av = []
                coluna = montar.coluna_das_opcoes_clip(c, tipo, 1, av, render)
                certo = {k: c[k] for k in ("x1", "lp", "li") if k in c}
                if av or (json.loads(coluna) if coluna else {}) != certo:
                    problemas.append("o montar escreve %r para %s, com os avisos %s" % (coluna, certo, av))
                lido = render.ler_opcoes_clip(coluna)
                if certo and (lido is None or lido["x1"] != (c.get("x1") is True) or lido["li"] != (c.get("li") is True)
                              or list(lido["lp"]) != [(c.get("lp") or {}).get("dx", 0), (c.get("lp") or {}).get("dy", 0)]):
                    problemas.append("o render le %s do que o montar escreve para %s" % (lido, certo))
        except AttributeError as erro:
            problemas.append("o montar ainda nao escreve a coluna opcoes_clip (%s)" % erro)
    # A JUNCAO POR PARTES: a posicao e a letra do contador sao partes proprias; os clips vao com a montagem
    B0 = {"versoes": [{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01", "x": "a"}]}],
          "pessoas": [], "tags": {}, "atual": "v1", "estilo": {"legenda": {"tamanho": 59}},
          "quando": "2026-10-03T05:00:00Z", "rev": 5, "pagina": "2026-10-02"}
    corpo_js = """
var r = {}, B0 = %s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
/* A. aqui a posicao das legendas, la o tamanho e a letra do contador: juntam-se */
abrir(B0); est.estilo = {legenda: {tamanho: 59, posicao: {dy: -40}}};
var j = juntarComBase(com({estilo: {legenda: {tamanho: 54}, contador: {fonte: "georgia_bold"}}, rev: 6}));
r.A = {ok: j.ok, estilo: copia(est.estilo), partes: Object.keys(partesDe(corpo())).filter(function(k){ return /posicao|fonte/.test(k); }).sort()};
/* B. os dois a mexer na posicao, de maneiras diferentes: e conflito, como dois na mesma parte */
abrir(B0); est.estilo = {legenda: {tamanho: 59, posicao: {dy: -40}}};
j = juntarComBase(com({estilo: {legenda: {tamanho: 59, posicao: {dx: 100}}}, rev: 6}));
r.B = {ok: j.ok, choque: j.choque};
/* C. uma Mesa antiga (sem pagina, sem o estilo) grava: a posicao e a letra do contador voltam a base */
abrir(com({estilo: {legenda: {posicao: {dy: -40, alinhamento: "esquerda"}}, contador: {fonte: "georgia_bold"}}}));
j = juntarComBase(com({estilo: undefined, pagina: undefined, rev: 6}));
r.C = {ok: j.ok, repostos: j.repostos, estilo: corpo().estilo};
/* D. uma Mesa de ontem, que nao conhece as chaves, muda o tamanho: copia o est.estilo inteiro e elas ficam */
abrir(com({estilo: {legenda: {tamanho: 59, posicao: {dy: -40}}, contador: {fonte: "georgia_bold"}}}));
j = juntarComBase(com({estilo: {legenda: {tamanho: 54, posicao: {dy: -40}}, contador: {fonte: "georgia_bold"}}, rev: 6}));
r.D = {ok: j.ok, estilo: copia(est.estilo)};
/* E. as escolhas dos clips vao com a montagem: la mexeram nos clips, aqui no estilo */
abrir(B0); est.estilo = {legenda: {tamanho: 59, posicao: {dy: -40}}};
j = juntarComBase(com({versoes: [{id: "v1", nome: "demo", clips: [{t: "foto", i: "f01", x: "a", x1: true, lp: {dx: 0, dy: -30}}]}], rev: 6}));
r.E = {ok: j.ok, clip: est.versoes[0].clips[0], estilo: copia(est.estilo)};
console.log(JSON.stringify(r));
""" % json.dumps(B0)
    r = _correr_js(DECLARACOES_JUNTAR, FUNCOES_JUNTAR, PRELUDE_JUNTAR, corpo_js, problemas)
    if r:
        if not r["A"]["ok"] or r["A"]["estilo"] != {"legenda": {"tamanho": 54, "posicao": {"dy": -40}}, "contador": {"fonte": "georgia_bold"}} \
                or r["A"]["partes"] != ['["estilo","contador","fonte"]', '["estilo","legenda","posicao"]']:
            problemas.append("a posicao aqui e o resto la: %s" % r["A"])
        if r["B"]["ok"] or "estilo" not in (r["B"].get("choque") or []):
            problemas.append("os dois na posicao, de maneiras diferentes, devia ser conflito: %s" % r["B"])
        if not r["C"]["ok"] or r["C"]["repostos"] != ["estilo"] or \
                r["C"]["estilo"] != {"legenda": {"posicao": {"dy": -40, "alinhamento": "esquerda"}}, "contador": {"fonte": "georgia_bold"}}:
            problemas.append("a Mesa antiga: %s" % r["C"])
        if not r["D"]["ok"] or r["D"]["estilo"] != {"legenda": {"tamanho": 54, "posicao": {"dy": -40}}, "contador": {"fonte": "georgia_bold"}}:
            problemas.append("a Mesa de ontem que nao conhece as chaves: %s" % r["D"])
        if not r["E"]["ok"] or r["E"]["clip"].get("x1") is not True or r["E"]["clip"].get("lp") != {"dx": 0, "dy": -30} or \
                r["E"]["estilo"] != {"legenda": {"tamanho": 59, "posicao": {"dy": -40}}}:
            problemas.append("os clips de la e o estilo daqui: %s" % r["E"])
    verifica("Mesa: as legendas de 3 de outubro gravam, desfazem e juntam", not problemas, "; ".join(problemas)[:600] if problemas else
             "como esta sem escritas, x1 e li so com true, as setas com limites e uma entrada no anular, a posicao e a letra do "
             "contador, o render e o montar a ler sem avisos, e cinco juncoes")


def teste_legendas_1003_avisam():
    """A legenda que nao cabe numa linha, o lado a lado que corta, a letra do contador, e o «ainda não chega ao filme».

    O DEFEITO QUE ISTO APANHA: ele a ligar «numa só linha» numa legenda que nao cabe e a Mesa calada (so via no filme,
    uma hora depois, que ela continuava em duas); um lado a lado a cortar metade de uma foto sem a Mesa o dizer; a letra
    do contador a ler-se pior a 15 m sem aviso, ou com aviso quando o render nao avisa; e um render que ainda nao le uma
    chave com a Mesa a mostrar a escolha como se fosse ao filme.
    """
    if not shutil.which("node"):
        salta("Mesa: as legendas de 3 de outubro avisam", "sem node neste PC")
        return
    import render
    problemas = []
    longo = " ".join(["palavra"] * 40)
    base = {"versoes": [{"id": "v1", "nome": "demo", "clips": [
        {"t": "foto", "i": "f1", "x": longo, "d": 4, "c": 0.7, "r": "fundo", "x1": True},
        {"t": "foto", "i": "f1", "x": "Curta", "d": 4, "c": 0.7, "r": "fundo", "x1": True},
        {"t": "lado", "fotos": ["f1", "f2"], "lay": "2v", "x": "Os dois", "d": 5, "c": 0.7, "r": "fiel"},
        {"t": "lado", "fotos": ["f2", "f2"], "lay": "2v", "x": "", "d": 5, "c": 0.7, "r": "fiel"},
        {"t": "lado", "fotos": ["f1", "f1", "f1"], "lay": "3s", "x": "", "d": 5, "c": 0.7, "r": "fiel"},
        {"t": "lado", "fotos": ["f2", "f2"], "lay": "2v", "x": "Curta", "xf": [longo, ""], "vf": True, "vm": "legenda", "d": 5, "c": 0.7, "x1": True},
        {"t": "foto", "i": "f1", "x": "", "d": 4, "c": 0.7, "r": "fundo"}]}], "atual": "v1", "pessoas": [], "tags": {}}
    porid = {"f1": {"id": "f1", "w": 4000, "h": 3000}, "f2": {"id": "f2", "w": 3000, "h": 4000}}
    letras = ["arial_bold", "georgia_bold", "montserrat_bold", "playfair_display", "bebas_neue", "calibri_bold", "great_vibes", "cinzel_regular"]
    js = (APOIO_LEG % {"porid": json.dumps(porid)}) + """
var v = est.versoes[0], r = {};
r.x1 = v.clips.map(function(_c, i){ return avisosNumaLinha(v, i).map(function(a){ return a.t; }); });
r.notas = v.clips.map(function(c, i){ return temLegendaDeBaixo(c) ? notaNumaLinha(v, i) : null; });
r.corta = v.clips.map(function(c){ return c.t === "lado" ? [avisoLadoCorta(c), ladoCorteDoClip(c)] : null; });
v.clips[2].li = true; r.inteiras = [avisoLadoCorta(v.clips[2]), ladoCortadas(v.clips[2])]; delete v.clips[2].li;
/* a letra do contador, letra a letra */
var LETRAS = %s;
r.letras = LETRAS.map(function(id){
  if(id === "arial_bold") delete est.estilo; else est.estilo = {contador: {fonte: id}};
  RENDER_LE = {contador_fonte: true};
  return estiloAvisos("contador").map(function(a){ return [!!a.forte, a.t]; });
});
/* o que ainda nao chega ao filme */
RENDER_LE = {contador_fonte: false, legenda_posicao: false, numa_linha: false, posicao_clip: false, fotos_inteiras: false};
est.estilo = {contador: {fonte: "georgia_bold"}, legenda: {posicao: {dy: -40}}};
v.clips[1].lp = {dx: 0, dy: -20};
r.falta = {contador: estiloAvisos("contador").filter(function(a){ return a.forte; }).map(function(a){ return a.t; }),
           legenda: estiloAvisos("legenda").filter(function(a){ return a.forte; }).map(function(a){ return a.t; }),
           x1: notaNumaLinha(v, 1), lp: notaPosicaoDoClip(v.clips[1]), css: palcoCssContador(46),
           /* o palco mostra o filme: sem o render a ler, a legenda fica no sitio de sempre, parte como hoje e as fotos enchem */
           palco: [legPosicao(v.clips[1], true), legPosicao(v.clips[1]), x1NoFilme(v.clips[1]), x1Do(v.clips[1]), legPisoDoGrupo(v.clips[2], 1080)]};
v.clips[2].li = true; r.falta.palco.push(liNoFilme(v.clips[2]), liDo(v.clips[2])); delete v.clips[2].li;
RENDER_LE = {contador_fonte: true, legenda_posicao: true, numa_linha: true, posicao_clip: true, fotos_inteiras: true};
r.chega = {contador: estiloAvisos("contador").map(function(a){ return a.t; }).join(" "), legenda: estiloAvisos("legenda").map(function(a){ return a.t; }).join(" "),
           x1: notaNumaLinha(v, 1), lp: notaPosicaoDoClip(v.clips[1])};
/* uma letra que a base tem e esta Mesa nao conhece */
est.estilo = {contador: {fonte: "letra_de_amanha"}}; r.desconhecida = [estiloValor("contador", "fonte"), estiloAvisos("contador").map(function(a){ return a.t; })];
console.log(JSON.stringify(r));
""" % json.dumps(letras)
    s = _correr_estilo(base, js, problemas, mais=FUNCOES_LEG + FUNCOES_LEG_INSPETOR + FUNCOES_LEG_ESTILO, declaracoes=DECLARACOES_LEG)
    if s:
        x1 = s["x1"]
        if len(x1[0]) != 1 or not re.fullmatch(r"A legenda do clip 1 não cabe numa linha: precisa de \d+ px e há 1660 px\. O filme parte-a como hoje\.", x1[0][0]):
            problemas.append("a legenda que nao cabe numa linha diz %r" % (x1[0],))
        if x1[1] or x1[2] or x1[6] or len(x1[5]) != 1 or "clip 6" not in x1[5][0]:
            problemas.append("avisos de numa linha onde nao deviam, ou a faltar no texto de cada foto: %s" % x1[1:])
        if "Fica numa linha" not in s["notas"][1] or "não cabe" not in s["notas"][0] or s["notas"][6] != "Este clip não tem legenda.":
            problemas.append("as notas do inspetor: %s" % s["notas"])
        corta = s["corta"]
        certo = render.lado_corte("2v", [(4000, 3000), (3000, 4000)])
        if not corta[2][0].startswith("A foto 1 fica %d %% de fora com o enchimento de hoje" % round(certo[0] * 100)) or "foto 2" in corta[2][0]:
            problemas.append("o lado a lado com uma foto deitada: %r (o render corta %s)" % (corta[2][0], certo))
        if corta[3][0] or any(x > render.LADO_CORTE_AVISO for x in corta[3][1]):
            problemas.append("duas fotos em pe nas colunas nao deviam avisar: %s" % corta[3])
        if "a foto 3" in corta[4][0] or corta[4][1][2] != 0 or "A foto 1 fica" not in corta[4][0] or " e a foto 2 fica" not in corta[4][0]:
            problemas.append("o cartao do meio do 3s vai inteiro: %s" % corta[4])
        if s["inteiras"] != ["", []]:
            problemas.append("com as fotos inteiras nao ha corte a avisar: %s" % s["inteiras"])
        # A LETRA DO CONTADOR: forte quando o render avisa a leitura (render._leitura_da_letra_do_contador), calada quando nao
        entradas = render.letras_da_mesa()
        for ident, lista in zip(letras, s["letras"]):
            mesa_pior = any(f and "pode não se ler a 15 metros" in t for f, t in lista)
            if hasattr(render, "_leitura_da_letra_do_contador"):
                dele = render._leitura_da_letra_do_contador(entradas.get(ident) or {})
                render_pior = any("pior" in a for a in dele)
                if ident != "arial_bold" and mesa_pior != render_pior:
                    problemas.append("a letra %s no contador: a Mesa %s e o render %s" % (ident, "avisa" if mesa_pior else "nao avisa", dele))
            if ident == "arial_bold" and lista:
                problemas.append("em Arial Bold o contador nao devia avisar nada: %s" % lista)
            if ident == "great_vibes" and not any(f and "manuscrita" in t for f, t in lista):
                problemas.append("uma manuscrita no contador devia avisar forte: %s" % lista)
        falta = s["falta"]
        if not any("ainda não chega ao filme" in t for t in falta["contador"]) or not any("ainda não chega ao filme" in t for t in falta["legenda"]) \
                or "Ainda não chega ao filme" not in falta["x1"] or "Ainda não chega ao filme" not in falta["lp"] \
                or falta["css"] != "700 46px Arial, Helvetica, sans-serif":
            problemas.append("com o render sem ler, a Mesa nao o diz em todo o lado: %s" % falta)
        if falta.get("palco") != [{"dx": 0, "dy": 0, "alinhamento": "centro"}, {"dx": 0, "dy": -60, "alinhamento": "centro"}, False, True, 540, False, True]:
            problemas.append("com o render sem ler, o palco devia mostrar o filme como esta, e o inspetor a escolha: %s" % falta.get("palco"))
        if any("chega ao filme" in t for t in s["chega"].values()):
            problemas.append("com o render a ler, a Mesa ainda diz que nao chega: %s" % s["chega"])
        if s["desconhecida"][0] != "arial_bold" or not any("não conhece" in t for t in s["desconhecida"][1]):
            problemas.append("uma letra do contador que esta Mesa nao conhece: %s" % s["desconhecida"])
    # quem chama: o inspetor, o Validar, o palco, a amostra e as ordens
    html = io.open(EDITOR, encoding="utf-8").read()
    for funcao, tem in (("function pintaInspetor(", "blocoLegendaDoClip(v, c)"), ("function pintaInspetor(", "blocoFotosInteiras(c)"),
                        ("function ligaInspetor(", "ligaLegendaDoClip(v, c)"), ("function validar(", "avisosNumaLinha(v, i)"),
                        ("function validar(", "avisoLadoCorta(c)"), ("function palcoLegenda(", "legDesenha("),
                        ("function estiloDesenhaLegenda(", "legDesenha("), ("function legendaDoPalco(", "legSpan("),
                        ("function mostraQuadro(", "liNoFilme(c)"), ("function mostraQuadro(", "legPisoDoGrupo(c, H)"),
                        ("function palcoTexto(", "palcoCssContador(corpo)"), ("function estiloHtmlControlos(", 'estiloCampoLetra("contador", "Letra")'),
                        ("function estiloHtmlControlos(", "estiloHtmlPosicao()"), ("function legendaDoMergulho(", "legPosicao(c, true).dy")):
        if tem not in _bloco(html, funcao, problemas):
            problemas.append("o %s deixou de chamar %s" % (funcao[9:-1], tem))
    verifica("Mesa: as legendas de 3 de outubro avisam", not problemas, "; ".join(problemas)[:600] if problemas else
             "a linha que nao cabe com as palavras do contrato, o corte acima de 25%%, %d letras do contador como o render, e o que "
             "ainda nao chega ao filme" % len(letras))


def teste_gerar_mesa_ve_as_legendas_de_3_de_outubro():
    """O gerar_mesa pergunta ao desenho do render pelos pontos 1 a 4, e nao so a limpeza do estilo.

    O DEFEITO QUE ISTO APANHA: a Mesa a dizer que a posicao das legendas chega ao filme porque o normalizar_estilo() a
    guarda, com o faixa_texto() ainda a desenha-las no sitio de sempre (era o estado do render as 05:10 de 3 de outubro);
    e um montar que nao escreve a coluna opcoes_clip com a Mesa a dar o x1 por lido.
    """
    import gerar_mesa
    import render
    problemas = []
    chaves = ("contador_fonte", "legenda_posicao", "numa_linha", "posicao_clip", "fotos_inteiras")
    montar = io.open(os.path.join(REPO, "scripts", "montar_da_mesa.py"), encoding="utf-8").read()
    le = gerar_mesa.le_as_legendas_de_3_de_outubro(render, montar)
    if sorted(le) != sorted(chaves):
        problemas.append("as chaves sao %s" % sorted(le))
    if render.estilo_ativo() != {}:
        problemas.append("a pergunta deixou um estilo posto no render: %s" % render.estilo_ativo())

    class RenderDeOntem:
        """um render que limpa o estilo como o de hoje e desenha como o de 2 de outubro"""
        LETRA_OMISSAO = render.LETRA_OMISSAO

        def __getattr__(self, nome):
            if nome in ("ler_opcoes_clip",):
                raise AttributeError(nome)
            return getattr(render, nome)

        def faixa_texto(self, texto, tamanho=None, bloco_max=None):
            guardado = render.estilo_ativo()
            render.aplicar_estilo({}, [])
            try:
                return render.faixa_texto(texto, tamanho, bloco_max)
            finally:
                render.aplicar_estilo(guardado, [])

    ontem = gerar_mesa.le_as_legendas_de_3_de_outubro(RenderDeOntem(), montar)
    if ontem.get("legenda_posicao") is not False or any(ontem.get(k) is not False for k in ("numa_linha", "posicao_clip", "fotos_inteiras")):
        problemas.append("com um render que nao desenha a posicao nem le as opcoes do clip, a pergunta deu %s" % ontem)
    sem_montar = gerar_mesa.le_as_legendas_de_3_de_outubro(render, "def main():\n    pass\n")
    if any(sem_montar.get(k) is not False for k in ("numa_linha", "posicao_clip", "fotos_inteiras")):
        problemas.append("com um montar que nao escreve a coluna opcoes_clip, a pergunta deu %s" % sem_montar)
    if sem_montar.get("legenda_posicao") != le.get("legenda_posicao") or sem_montar.get("contador_fonte") != le.get("contador_fonte"):
        problemas.append("a posicao e a letra do contador nao dependem do montar: %s contra %s" % (sem_montar, le))
    tudo = gerar_mesa.o_que_o_render_le()
    if any(k not in tudo for k in chaves) or any(tudo[k] != le[k] for k in chaves):
        problemas.append("o o_que_o_render_le() nao traz as mesmas respostas: %s" % {k: tudo.get(k) for k in chaves})
    verifica("Mesa: o gerar_mesa pergunta ao desenho do render pelas legendas", not problemas, "; ".join(problemas)[:500] if problemas else
             "hoje %s; um render de ontem e um montar sem a coluna dao False" % ", ".join("%s %s" % (k, le[k]) for k in chaves))


# ------------------------------------------------------------- a ordem, os nomes corridos e a velocidade (3 de outubro)
# O Tiago, as 04:50 e as 05:05 de 3 de outubro (saida/discussao/contrato_1003.md, pontos 5 e 5b): o titulo antes do rolo,
# "vamos abolir" os cargos ("quero mesmo poder remover integralmente"), "so queremos os nomes dos convidados corridos", e
# "permite ajustar a velocidade dos nomes e/ou das fotos". O render (ponto5_creditos.py) ja o faz; a Mesa deixa escolher
# na aba «Ordem e velocidade» dos Creditos, com as mesmas contas, e so grava o que ele escolhe.
CASOS_DAS_PARTES = [
    ("como esta", None),
    ("titulo, rolo", {"partes": ["titulo", "rolo"]}),
    ("titulo, rolo, corridos", {"partes": ["titulo", "rolo"], "nomes_corridos": True}),
    ("titulo, cargos, rolo", {"partes": ["titulo", "cargos", "rolo"]}),
    ("rolo, titulo", {"partes": ["rolo", "titulo"]}),
    ("cargos, titulo, rolo", {"partes": ["cargos", "titulo", "rolo"]}),
    ("so o rolo", {"partes": ["rolo"]}),
    ("rolo, cargos", {"partes": ["rolo", "cargos"]}),
    ("rolo, titulo, cargos com cinco", {"partes": ["rolo", "titulo", "cargos"],
                                        "cargos": [{}, {}, {}, {"cargo": "D", "quem": "E\nF"}, {"quem": "G"}]}),
    ("a de hoje escrita", {"partes": ["rolo", "cargos", "titulo"], "cargos_primeiro": True}),
    ("a da 109 escrita", {"partes": ["cargos", "rolo", "titulo"]}),
    ("a da 109 pela chave de sempre", {"cargos_primeiro": True}),
    ("maiusculas e espacos", {"partes": [" Titulo", "ROLO "]}),
    ("sem rolo", {"partes": ["titulo", "cargos"], "cargos_primeiro": True}),
    ("repetida", {"partes": ["rolo", "rolo"]}),
    ("outra palavra", {"partes": ["rolo", "fim"]}),
    ("um texto", {"partes": "titulo,rolo"}),
    ("vazia", {"partes": []}),
    ("null com a 109", {"partes": None, "cargos_primeiro": True}),
    ("um numero la dentro", {"partes": ["rolo", 3]}),
    ("sem cargos com a lista dele", {"partes": ["titulo", "rolo"],
                                     "cargos": [{"cargo": "A", "quem": "QA"}, {"cargo": "B", "quem": "QB"}]}),
    ("corridos nao e true", {"nomes_corridos": "sim"}),
    ("corridos false", {"nomes_corridos": False}),
    ("corridos", {"nomes_corridos": True}),
    ("fotos a 100", {"velocidade": {"fotos": 100}}),
    ("nomes a 60", {"velocidade": {"nomes": 60}}),
    ("fotos 200 nomes 40", {"velocidade": {"fotos": 200, "nomes": 40}}),
    ("fotos a 300", {"velocidade": {"fotos": 300}}),
    ("nomes a 30.5", {"velocidade": {"nomes": 30.5}}),
    ("os dois iguais ao de hoje", {"velocidade": {"fotos": 150, "nomes": 150}}),
    ("fora dos limites", {"velocidade": {"fotos": 59, "nomes": 201}}),
    ("um bom e um mau", {"velocidade": {"fotos": 120, "nomes": "depressa"}}),
    ("booleano", {"velocidade": {"fotos": True}}),
    ("nao e objeto", {"velocidade": 100}),
    ("uma lista", {"velocidade": [100, 50]}),
    ("vazio", {"velocidade": {}}),
    ("as 10h", {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"fotos": 100}}),
    ("as 10h e os nomes a 60", {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"nomes": 60}}),
    ("as 10h e fotos 200, nomes 40", {"partes": ["titulo", "rolo"], "nomes_corridos": True,
                                      "velocidade": {"fotos": 200, "nomes": 40}}),
]


def _blocos_do_cred(cred):
    """Os blocos do por_grupo() do ponto5 a partir dos grupos de um CREDITOS_NOMES de ensaio: (titulo, subtitulo, agregados),
    um agregado por linha, sem os grupos vazios."""
    return [(g["titulo"], g["sub"], [ln.split(" · ") for ln in g["linhas"]]) for g in cred["grupos"] if g["linhas"]]


def _lay_para_comparar():
    """O JavaScript que tira do credContas() o que se compara com o textos_dos_creditos() e o tempos_dos_creditos()."""
    return """
function layDe(){
  credLay = null;
  var L = credContas();
  return {cargos: L.cargos.map(function(x){ return [x.cargo, x.pessoas.join("\\n")]; }), escolhidas: L.partesEscolhidas, corridos: L.corridos,
          vel: L.vel, Hr: L.Hr, Hc: L.Hc, guardados: L.cargosGuardados, linhas: L.pecas.filter(function(q){ return q.tipo === "nome"; }).length,
          outras: L.pecas.filter(function(q){ return q.tipo !== "nome"; }).length,
          t: {dur: L.dur, tCargos: L.tCargos, tRoloEntra: L.tRoloEntra, tTituloEntra: L.tTituloEntra, tRolo: L.tRolo, n: L.nCargos,
              vn: L.vn, vf: L.vf, primeiro: L.primeiro, partes: L.partes,
              janelas: L.janelas ? L.janelas.map(function(j){ return [j.parte, j.ini, j.fim]; }) : null,
              tituloApaga: L.janelas ? L.tituloApaga : null, fimNomes: L.fimNomes, fimFotos: L.fimFotos,
              parado: L.parado ? [L.parado.quem, L.parado.s] : null}};
}
"""


def _tempos_diferentes(m, T):
    """As diferencas, ao bit, entre o que a Mesa conta (o `t` do layDe) e o T do tempos_dos_creditos()."""
    pares = (("dur", "dur"), ("tCargos", "t_cargos"), ("tRoloEntra", "t_rolo_entra"), ("tTituloEntra", "t_titulo_entra"),
             ("tRolo", "t_rolo"), ("n", "n_cargos"), ("vn", "vel_nomes"), ("vf", "vel_fotos"), ("primeiro", "primeiro"),
             ("partes", "partes"))
    dif = ["%s %r contra %r" % (k, m[k], T[kp]) for k, kp in pares if m[k] != T[kp]]
    janelas = [list(j) for j in T["janelas"]] if T.get("janelas") else None
    if m["janelas"] != janelas:
        dif.append("janelas %r contra %r" % (m["janelas"], janelas))
    if janelas and m["tituloApaga"] != T["titulo_apaga"]:
        dif.append("o fade do titulo %r contra %r" % (m["tituloApaga"], T["titulo_apaga"]))
    for k, kp in (("fimNomes", "fim_nomes"), ("fimFotos", "fim_fotos")):
        if m[k] != T.get(kp):
            dif.append("%s %r contra %r" % (k, m[k], T.get(kp)))
    parado = list(T["parado"]) if T.get("parado") else None
    if m["parado"] != parado:
        dif.append("parado %r contra %r" % (m["parado"], parado))
    return dif, len(pares) + 5


def teste_creditos_1003_partes_nomes_e_velocidade_como_o_ponto5():
    """A ordem das partes, os nomes corridos e a velocidade da Mesa sao os do ponto5, ao bit (contrato de 3 de outubro).

    O DEFEITO QUE ISTO APANHA: a pre-visualizacao com outra ordem, outros cargos, outro rolo ou outra duracao do que o
    filme. O titulo primeiro sem os 0,5 s a mais, os cargos a contar segundos com o «Sem cargos», os nomes corridos com
    os espacos dos grupos, a velocidade dele a mexer na do outro lado, ou um valor mal escrito (uma lista sem o rolo, um
    `true` que e um texto, 59 px/s) a valer: a musica com «fim» entrava noutro sitio do ficheiro, e o Tiago e a Clara
    decidiam a olhar para outro filme. Cada caso le-se dos dois lados: a lista, os cargos, os nomes corridos e a
    velocidade pelo textos_dos_creditos(); a altura do rolo pelo rolo_de_nomes(); e os tempos, as janelas de cada
    parte, o fim de cada lado e o que fica parado pelo tempos_dos_creditos(), com as alturas da Mesa.
    """
    if not shutil.which("node"):
        salta("Mesa: as partes, os nomes corridos e a velocidade como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    p5 = cm._ponto5()
    problemas = []
    cred = _cred_dos_cargos(p5)
    corpo_js = _lay_para_comparar() + """
var EST0 = %(est)s, casos = %(casos)s, r = [];
casos.forEach(function(c){
  est = JSON.parse(JSON.stringify(EST0));
  if(c[1] !== null) est.creditos = c[1];
  r.push(layDe());
});
console.log(JSON.stringify(r));
""" % {"est": json.dumps(EST_DOS_CARGOS, ensure_ascii=False), "casos": json.dumps(CASOS_DAS_PARTES, ensure_ascii=False)}
    saida = _correr_node(_prelude(cred, EST_DOS_CARGOS), corpo_js, problemas)
    render.aplicar_estilo(None, [])
    blocos = _blocos_do_cred(cred)
    alturas = {False: p5.rolo_de_nomes(blocos).height, True: p5.rolo_de_nomes(blocos, True).height}
    n_tempos, avisados = 0, 0
    for (nome, cr), m in zip(CASOS_DAS_PARTES, saida or []):
        avisos = []
        t = p5.textos_dos_creditos({"creditos": cr} if cr is not None else {}, avisos)
        avisados += 1 if avisos else 0
        esperado = [[c, "\n".join(p5.pessoas_do_quem(q))] for c, q in t["cargos"]]
        if m["cargos"] != esperado:
            problemas.append("%s: a Mesa tem os cargos %s, o ponto5 %s" % (nome, m["cargos"], esperado))
        if m["escolhidas"] != t["partes"]:
            problemas.append("%s: a Mesa le as partes %s, o ponto5 %s" % (nome, m["escolhidas"], t["partes"]))
        if m["corridos"] is not t["nomes_corridos"]:
            problemas.append("%s: nomes corridos na Mesa %s, no ponto5 %s" % (nome, m["corridos"], t["nomes_corridos"]))
        if {k: float(v) for k, v in m["vel"].items()} != t["velocidade"]:
            problemas.append("%s: a velocidade na Mesa %s, no ponto5 %s" % (nome, m["vel"], t["velocidade"]))
        if m["Hr"] != alturas[t["nomes_corridos"]]:
            problemas.append("%s: o rolo da Mesa tem %d px, o do ponto5 %d" % (nome, m["Hr"], alturas[t["nomes_corridos"]]))
        if t["nomes_corridos"] and m["outras"]:
            problemas.append("%s: com os nomes corridos a Mesa ainda tem %d titulos ou subtitulos no rolo" % (nome, m["outras"]))
        T = p5.tempos_dos_creditos(m["Hr"], m["Hc"], len(t["cargos"]), t["cargos_primeiro"], t["partes"], t["velocidade"])
        dif, n = _tempos_diferentes(m["t"], T)
        n_tempos += n
        if dif:
            problemas.append("%s: os tempos nao sao os do ponto5 ao bit: %s" % (nome, "; ".join(dif[:4])))
    if saida:
        por = dict(zip([c[0] for c in CASOS_DAS_PARTES], saida))
        hoje = por["como esta"]["t"]["dur"]
        # o que o contrato diz, em numeros: o titulo primeiro sao 0,5 s a mais; sem cargos, nem um segundo deles
        tr = por["titulo, rolo"]["t"]
        if abs(tr["dur"] - (hoje - 3 * 4.2 + 0.5)) > 1e-9 or tr["tCargos"] is not None or tr["n"] != 0 or por["titulo, rolo"]["cargos"]:
            problemas.append("o titulo antes e sem cargos: %.4f s contra os %.4f de hoje, %s cargos" % (tr["dur"], hoje, tr["n"]))
        if por["titulo, rolo"]["guardados"] != 3 or por["sem cargos com a lista dele"]["guardados"] != 2:
            problemas.append("sem cargos, os textos que ficam guardados: %s e %s" % (por["titulo, rolo"]["guardados"],
                                                                                    por["sem cargos com a lista dele"]["guardados"]))
        if abs(por["rolo, titulo"]["t"]["dur"] - (hoje - 3 * 4.2)) > 1e-9 or por["so o rolo"]["t"]["tTituloEntra"] is not None:
            problemas.append("o rolo e o titulo sem cargos: %.4f s; so o rolo com titulo aos %s" % (
                por["rolo, titulo"]["t"]["dur"], por["so o rolo"]["t"]["tTituloEntra"]))
        # os nomes corridos: as mesmas linhas, sem mais nada, a 78 px cada e 20 no fim
        c = por["corridos"]
        if c["linhas"] != por["como esta"]["linhas"] or c["Hr"] != 78 * c["linhas"] + 20 or c["Hr"] >= por["como esta"]["Hr"]:
            problemas.append("os nomes corridos: %d linhas e %d px (por grupos %d linhas e %d px)" % (
                c["linhas"], c["Hr"], por["como esta"]["linhas"], por["como esta"]["Hr"]))
        # a velocidade: a escolhida e a que anda, e ha quem fique parado
        if por["fotos a 100"]["t"]["vf"] != 100 or por["nomes a 60"]["t"]["vn"] != 60 or not por["fotos 200 nomes 40"]["t"]["parado"]:
            problemas.append("a velocidade escolhida nao e a que anda: %s, %s, %s" % (
                por["fotos a 100"]["t"]["vf"], por["nomes a 60"]["t"]["vn"], por["fotos 200 nomes 40"]["t"]["parado"]))
        for nome in ("fora dos limites", "booleano", "nao e objeto", "uma lista", "vazio", "sem rolo", "repetida", "vazia"):
            base = por["a da 109 pela chave de sempre"] if nome == "sem rolo" else por["como esta"]
            if por[nome]["t"] != base["t"]:
                problemas.append("%s nao fica como esta" % nome)
    verifica("Mesa: as partes, os nomes corridos e a velocidade como o ponto5", saida is not None and not problemas,
             "; ".join(problemas)[:600] if problemas else
             "%d casos (a ordem, sem cargos, sem titulo, corridos, cada velocidade e as duas, e %d mal escritos que ficam como "
             "esta): as mesmas partes, cargos, rolo e velocidades, e %d tempos ao bit" % (len(CASOS_DAS_PARTES), avisados, n_tempos))


def teste_creditos_1003_desenho_como_o_ponto5():
    """Com as partes noutra ordem e a velocidade dele, a Mesa desenha cada peca no instante e no sitio do ponto5.

    O DEFEITO QUE ISTO APANHA, contra os fotogramas do proprio desenho_dos_creditos():
    - o titulo primeiro a acender do preto (tem de nascer ja aceso da ultima imagem do filme: a sala aplaude no primeiro
      preto), a apagar-se em 2,5 s a meio dos creditos em vez dos 0,6 s dos cargos, ou o rolo a aparecer de repente depois
      dele em vez de entrar do preto;
    - um cargo a aparecer com o «Sem cargos», ou o titulo sem "titulo" na lista;
    - com a velocidade dele, os nomes ou as fotos noutro sitio do ecra do que no filme (o rolo e a coluna de ensaio tem
      uma risca branca de 500 em 500 px, e mede-se onde ela cai em cada fotograma), ou o lado que acaba primeiro a
      continuar a andar em vez de sair do ecra e ficar vazio.
    """
    if not shutil.which("node"):
        salta("Mesa: o desenho das partes e da velocidade como o ponto5", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    import render
    from PIL import Image, ImageDraw
    p5 = cm._ponto5()
    problemas = []
    render.aplicar_estilo(None, [])
    M = dict(cm.MEDIDAS)
    M.update({"L": p5.L, "A": p5.A, "vel_nomes": p5.VELOCIDADE_NOMES, "vel_fotos_max": p5.VELOCIDADE_FOTOS_MAX,
              "nome_corpo": p5.NOME_CORPO, "sub_corpo": p5.SUB_CORPO, "cor_nome": list(p5.COR_NOME), "cor_sub": list(p5.COR_SUB),
              "painel_nomes": list(p5.PAINEL_NOMES), "margem_brilho": p5.MARGEM_BRILHO, "largura_foto": p5.LARGURA_FOTO,
              "centro_fotos": p5.CENTRO_FOTOS, "titulo_corpo": p5.TITULO_CORPO, "titulo_espaco": p5.TITULO_ESPACO,
              "titulo_altura": p5.letreiro_1x(["X"], p5.TITULO_CORPO, p5.TITULO_ESPACO).height - 2 * cm.MEDIDAS["corte_titulo"],
              "letreiro_quente": list(render.LETREIRO_QUENTE), "letreiro_claro": list(render.LETREIRO_BRANCO),
              "letreiro_brilho": list(render.LETREIRO_BRILHO), "letreiro_empurra": render.LETREIRO_EMPURRA,
              "fade_fim_imagem": render.FADE_FIM_IMAGEM, "zona_segura": p5.ZONA_SEGURA})
    for chave, nome_p5, le in cm.CONSTANTES_DAS_PARTES:
        M[chave] = le(getattr(p5, nome_p5))
    linhas = ["Pessoa %d · Outra %d" % (k, k) for k in range(40)]
    grupos = [{"etiqueta": "G1", "titulo": "FAMÍLIA DA CLARA", "sub": "do lado da mãe", "linhas": linhas}]
    # quatro fotos de alturas diferentes na coluna, para se saber qual e cada retangulo
    fotos = {"f01": [4000, 3000, 570], "f02": [3000, 4000, 900], "f03": [1000, 1000, 760], "f04": [4000, 2000, 380]}
    cred = {"medidas": M, "folha": "ensaio", "sem_nomes": "", "fotos": fotos, "grupos": grupos,
            "omissoes": {"cargos": [{"cargo": c, "quem": q} for c, q in p5.CARGOS], "titulo": p5.TITULO, "data": p5.DATA}}
    casos = [
        ("titulo, cargos, rolo", {"partes": ["titulo", "cargos", "rolo"], "cargos": [{}, {"quem": "O NOIVO\nA NOIVA"}]}),
        ("titulo, rolo, corridos (o das 10h)", {"partes": ["titulo", "rolo"], "nomes_corridos": True}),
        ("rolo, titulo, fotos 200 e nomes 40", {"partes": ["rolo", "titulo"], "nomes_corridos": True, "velocidade": {"fotos": 200, "nomes": 40}}),
        ("titulo, rolo, fotos 60 e nomes 150", {"partes": ["titulo", "rolo"], "nomes_corridos": True, "velocidade": {"fotos": 60, "nomes": 150}}),
        ("so o rolo, nomes a 100", {"partes": ["rolo"], "nomes_corridos": True, "velocidade": {"nomes": 100}}),
    ]
    textos = {nome: p5.textos_dos_creditos({"creditos": cr}) for nome, cr in casos}
    pessoas = sorted({p for t in textos.values() for _c, q in t["cargos"] for p in p5.pessoas_do_quem(q)})
    cargos_txt = sorted({c for t in textos.values() for c, _q in t["cargos"] if c})
    med = _medidas_das_letras(render, [{}], (list(range(1, max(p5.QUEM_CORPO, p5.TITULO_CORPO) + 1)) + [130],
                                             pessoas + [p5.TITULO, p5.DATA, "FAMÍLIA DA CLARA"]),
                              ([58], cargos_txt + ["do lado da mãe"] + linhas))
    corpo_js = MEDIDOR_FALSO % {"med": json.dumps(med, ensure_ascii=False)} + """
var CRED = %(cred)s, credLay = null, credTemFinais = true, porId = {};
function credAberto(){ return false; }
function credFonteDaFoto(){ return null; }
var casos = %(casos)s, r = [];
casos.forEach(function(c){
  est.creditos = c[1]; credLay = null;
  var Lay = credContas(), M = CRED.medidas, I = [0, 0.2, 0.5, 0.75, 1.0, 1.49, 1.6, 2.5], qy = {};
  Lay.pecas.forEach(function(q){ if(q.tipo === "nome") qy[q.texto] = q.y; });
  /* a volta de cada fronteira entre partes, e dentro do rolo: a entrada, a andar, cada lado a acabar, e o fim */
  (Lay.janelas || []).forEach(function(j){ [-0.7, -0.45, -0.2, -0.01, 0.01, 0.2, 0.45, 0.8, 1.2, 1.6, 2.5, 4.0].forEach(function(u){ I.push(j.fim + u); I.push(j.ini + u); }); });
  var r0 = Lay.tRoloEntra + M.t_entrada;
  [0.3, 1, 2.4, 5, 9.7, 14, 21].forEach(function(u){ I.push(r0 + u); });
  [Lay.fimNomes, Lay.fimFotos, Lay.tRolo].forEach(function(f){ if(f != null) [-6, -2.5, -0.9, -0.5, -0.1, 0.1, 0.5, 0.75, 0.95, 2].forEach(function(u){ I.push(r0 + f + u); }); });
  I = I.filter(function(t){ return t >= 0 && t <= Lay.dur; });
  var linhasDoCaso = {Hr: Lay.Hr, Hc: Lay.Hc, I: I, tempos: [], colY: Lay.col.map(function(p){ return [p.h, p.y]; })};
  I.forEach(function(t){
    var tela = telaFalsa(), rects = [];
    tela.ctx.fillRect = function(x, y, w, h){ rects.push({x: x, y: y, w: w, h: h, fill: tela.ctx.fillStyle, alfa: tela.ctx.globalAlpha}); };
    credDesenhaEm(tela, t, false, true);
    var ops = tela.ctx.ops, nomes = ops.filter(function(x){ return qy[x.t] !== undefined; });
    var fotosR = rects.filter(function(x){ return x.fill === "#2a2226" && x.w === M.largura_foto; });
    var yf = null;
    fotosR.forEach(function(x){ Lay.col.forEach(function(p){ if(p.h === x.h) yf = x.y - p.y; }); });
    linhasDoCaso.tempos.push({alfa: ops.concat(fotosR).reduce(function(a, x){ return Math.max(a, x.alfa); }, 0),
      tipo: nomes.length || fotosR.length ? "rolo" : ops.some(function(x){ return / 130px /.test(x.font); }) ? "titulo" : ops.length ? "cargos" : "preto",
      nNomes: nomes.length, nFotos: fotosR.length, y0c: nomes.length ? nomes[0].y - qy[nomes[0].t] : null, yf: yf,
      letras: ops.filter(function(x){ return x.fill && x.fill.grad && !x.sombra; }).length});
  });
  r.push(linhasDoCaso);
});
console.log(JSON.stringify(r));
""" % {"cred": json.dumps(cred, ensure_ascii=False), "casos": json.dumps(casos, ensure_ascii=False)}
    est = {"pessoas": [{"id": "p_c", "nome": "Créditos"}], "versoes": [], "tags": {k: ["p_c"] for k in fotos}}
    s = _correr_estilo(est, corpo_js, problemas, mais=FUNCOES_DESENHO_CRED, declaracoes=["var CRED_ARIAL = ", "var credLetrasPedidas = "])

    def suave(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3 - 2 * x)

    def riscado(largura, altura):
        """uma imagem preta com uma risca branca de 4 px de 500 em 500 px, para se ver onde cai no fotograma"""
        im = Image.new("RGB", (largura, altura), (0, 0, 0))
        d = ImageDraw.Draw(im)
        for y in range(0, altura, 500):
            d.rectangle([0, y, largura, y + 3], fill=(255, 255, 255))
        return im

    def risca(quadro, x):
        """o y, modulo 500, da primeira linha de uma risca na coluna x do fotograma, ou None se la nao ha nenhuma"""
        col = quadro.convert("L").crop((x, 0, x + 1, quadro.height)).tobytes()      # um byte por linha
        for y in range(200, 880):          # fora das pontas que desvanecem (170 px em cima e em baixo)
            if col[y] > 0 and col[y - 1] == 0:
                return y % 500
        return None
    conferidos = {"pecas": 0, "nomes": 0, "fotos": 0, "vazios": 0}
    for (nome, cr), m in zip(casos, s or []):
        t = textos[nome]
        T = p5.tempos_dos_creditos(m["Hr"], m["Hc"], len(t["cargos"]), t["cargos_primeiro"], t["partes"], t["velocidade"])
        if not T.get("janelas"):
            problemas.append("%s: o caso nao passa pelas partes noutra ordem" % nome)
            continue
        desenho = p5.desenho_dos_creditos(riscado(1040, m["Hr"]), riscado(p5.LARGURA_FOTO, m["Hc"]), t, {}, T)
        preto = p5.desenho_dos_creditos(Image.new("RGB", (1040, m["Hr"])), Image.new("RGB", (p5.LARGURA_FOTO, m["Hc"])), t, {}, T)
        # e com o rolo e a coluna todos brancos, para saber se cada lado ainda esta no ecra
        branco = p5.desenho_dos_creditos(Image.new("RGB", (1040, m["Hr"]), (255, 255, 255)),
                                         Image.new("RGB", (p5.LARGURA_FOTO, m["Hc"]), (255, 255, 255)), t, {}, T)

        def brilho(x):
            return preto(x).convert("L").getextrema()[1]
        cheio = {"titulo": brilho(T["t_titulo_entra"] + 2.5) if T["t_titulo_entra"] is not None else None}
        for k in range(len(t["cargos"])):
            cheio[k] = brilho(T["t_cargos"] + k * T["t_cargo"] + 2.0)
        piores, consts = [], set()
        for x, mm in zip(m["I"], m["tempos"]):
            kj = next((j for j, (_p, _ini, fim) in enumerate(T["janelas"]) if x < fim), len(T["janelas"]) - 1)
            peca = T["janelas"][kj][0]
            conferidos["pecas"] += 1
            if peca == "rolo":
                tr = x - T["t_rolo_entra"] - T["t_entrada"]
                alfa = (suave((tr + T["t_entrada"]) / T["t_entrada"]) if (kj > 0 and tr < 0) else 1.0) * \
                       (1.0 - suave((tr - T["t_rolo"] + 0.8) / 1.6) if tr > T["t_rolo"] - 0.8 else 1.0)
                quadro, qb = desenho(x), branco(x).convert("L")
                yn, yf = risca(quadro, 1400), risca(quadro, p5.CENTRO_FOTOS)
                ve_nomes = qb.crop((1000, 0, 1900, p5.A)).getextrema()[1] > 0
                ve_fotos = qb.crop((100, 0, 800, p5.A)).getextrema()[1] > 0
                # OS NOMES: onde a Mesa escreve a primeira linha que esta no ecra, contra a risca do rolo do ponto5. A
                # distancia entre as duas e a mesma em todos os instantes (o meio da linha e a base da letra)
                if mm["nNomes"] and alfa > 0.02:
                    y0 = int(p5.A * 0.45 - min(tr, T.get("fim_nomes", tr) if T.get("fim_nomes") is not None else tr) * T["vel_nomes"])
                    consts.add(round(mm["y0c"] - y0, 3))
                    conferidos["nomes"] += 1
                    if yn is not None and (y0 % 500) != yn and alfa > 0.2:
                        piores.append("%.2f s: a risca dos nomes cai em %d e as contas dizem %d" % (x, yn, y0 % 500))
                if mm["yf"] is not None and alfa > 0.2:
                    conferidos["fotos"] += 1
                    if yf is not None and (mm["yf"] % 500) != yf:
                        piores.append("%.2f s: a coluna das fotos a %d na Mesa e a risca do ponto5 em %d" % (x, mm["yf"] % 500, yf))
                # UM LADO QUE JA ACABOU SAI DO ECRA E FICA VAZIO, nos dois
                for lado, fim, n_mesa, ve in (("nomes", T.get("fim_nomes"), mm["nNomes"], ve_nomes), ("fotos", T.get("fim_fotos"), mm["nFotos"], ve_fotos)):
                    if fim is not None and tr > fim + 0.05 and alfa > 0.02:
                        conferidos["vazios"] += 1
                        if n_mesa or ve:
                            piores.append("%.2f s: os %s ja acabaram e continuam no ecra (Mesa %d, ponto5 %s)" % (x, lado, n_mesa, ve))
                if mm["tipo"] == "preto" and not (ve_nomes or ve_fotos):
                    continue                # os dois lados ja sairam do ecra, nos dois: preto ate ao fim do rolo
            else:
                alfa = brilho(x) / float(cheio["titulo"] if peca == "titulo" else
                                         cheio[min(int((x - T["t_cargos"]) // T["t_cargo"]) if x > T["t_cargos"] else 0, len(t["cargos"]) - 1)])
            if mm["tipo"] != peca and not (mm["tipo"] == "preto" and alfa < 0.02):
                piores.append("%.2f s: a Mesa desenha %s, o ponto5 %s" % (x, mm["tipo"], peca))
            elif abs(mm["alfa"] - alfa) > (0.02 if peca == "titulo" else 0.008) and not (peca == "rolo" and mm["tipo"] == "preto"):
                piores.append("%.2f s (%s): Mesa %.3f, ponto5 %.3f" % (x, peca, mm["alfa"], alfa))
        if len(consts) > 1:
            piores.append("os nomes nao andam com o rolo do ponto5: a distancia a risca muda (%s)" % sorted(consts)[:4])
        if piores:
            problemas.append("%s: %s" % (nome, "; ".join(piores[:4])))
        # a primeira parte nasce do fim do filme ja acesa
        if t["partes"][0] in ("titulo", "cargos") and m["tempos"][0]["alfa"] < 0.999:
            problemas.append("%s: a primeira parte nao nasce acesa do fim do filme: %.3f no zero" % (nome, m["tempos"][0]["alfa"]))
        if "cargos" not in t["partes"] and any(mm["tipo"] == "cargos" for mm in m["tempos"]):
            problemas.append("%s: sem cargos, a Mesa desenhou um cargo" % nome)
        if "titulo" not in t["partes"] and any(mm["tipo"] == "titulo" for mm in m["tempos"]):
            problemas.append("%s: sem titulo, a Mesa desenhou o titulo" % nome)
    if s and not (conferidos["nomes"] > 20 and conferidos["fotos"] > 10 and conferidos["vazios"] > 5):
        problemas.append("o teste ja nao prova as posicoes: %s" % conferidos)
    verifica("Mesa: o desenho das partes e da velocidade como o ponto5", s is not None and not problemas,
             "; ".join(problemas)[:600] if problemas else
             "%d casos, %d instantes com a peca e a opacidade dos fotogramas (o titulo aceso desde o zero e a apagar em 0,6 s a "
             "meio, o rolo a entrar do preto), os nomes em %d e as fotos em %d no sitio da risca, e %d com o lado que acabou vazio"
             % (len(casos), conferidos["pecas"], conferidos["nomes"], conferidos["fotos"], conferidos["vazios"]))


DECLARACOES_FORMA = ["var CRED_PARTES_HOJE = ", "var CRED_PARTE_NOME = ", "var credVelModo = ", "var credVelGesto = ",
                     "var credVelPorMarcar = "]
FUNCOES_FORMA = ["function credListasIguais(", "function credPartesEmPalavras(", "function credContasCom(", "function credPoePartes(",
                 "function credFraseDaOrdem(", "function credMoveParte(", "function credTiraParte(", "function credRepoeParte(",
                 "function credNomesCorridos(", "function credVelLimites(", "function credVelMarcaJa(", "function credPoeVelocidade(",
                 "function credDepoisDaVelocidade(", "function credVelocidadeModo(", "function credVelocidadePasso(",
                 "function credLetrasDeLer(", "function credLeituraDaVelocidade(", "function credAvisosDaVelocidade(",
                 "function credMusicaFraseDaDuracao(", "function credFormaDiz(", "function credHtmlDaOrdem(",
                 "function credHtmlDosNomes(", "function credHtmlDaVelocidade(", "function credCampoNoFilme(",
                 "function fmtS(", "function mmssDec("]


def teste_creditos_1003_gravam_desfazem_e_juntam():
    """A ordem, o «Sem cargos», os nomes corridos e a velocidade gravam so o que ele escolhe, desfazem-se e juntam-se.

    O DEFEITO QUE ISTO APANHA:
    - «como está» a gravar (abrir a aba, pinta-la, ou escolher o que ja esta), ou as duas ordens de antes a ficarem
      escritas de outra maneira (a de hoje nao grava nada, e a da 109 e o cargos_primeiro: true de sempre);
    - o «Sem cargos» a apagar os textos dos cargos (tem de os guardar para os repor), ou a deixar um cargo no filme;
    - a regua da velocidade a encher o Anular (os acertos seguidos sao uma entrada), a gravar fora dos limites, ou o
      «Como está» de um lado a levar a velocidade do outro;
    - o que a Mesa grava a dar outro filme no ponto5: cada passo le-se pelo textos_dos_creditos(), sem avisos;
    - a ordem num aparelho e a velocidade no outro a nao se juntarem, os dois na ordem sem conflito, ou uma Mesa de
      ontem a deitar fora a ordem, os nomes corridos ou a velocidade quando muda um titulo.
    """
    if not shutil.which("node"):
        salta("Mesa: a ordem, os nomes e a velocidade gravam, desfazem e juntam", "sem node neste PC")
        return
    import creditos_para_mesa as cm
    p5 = cm._ponto5()
    problemas = []
    cred = _cred_dos_cargos(p5)
    funcoes = FUNCOES_JUNTAR + FUNCOES_LAYOUT_CRED + FUNCOES_CARGOS + FUNCOES_FORMA
    funcoes = [f for i, f in enumerate(funcoes) if f not in funcoes[:i]]
    prelude = PRELUDE_JUNTAR + """
var CRED = %(cred)s, credTemFinais = false, porId = {}, RENDER_LE = {}, mensagens = [];
function credMsg(t){ mensagens.push(t); }
function esc(s){ return String(s); }
function credResumo(){ credLay = null; return {dur: credContas().dur}; }
function credTextoCurtoDoEfeito(a, d){ return "[" + a.dur.toFixed(4) + " -> " + d.dur.toFixed(4) + "]"; }
function credMusicaEscolha(){ return null; }
var credPintaForma = nada;
""" % {"cred": json.dumps(cred, ensure_ascii=False)} + MESA_53_CARGOS
    quatro = [{"cargo": "A", "quem": "QA"}, {"cargo": "B", "quem": "QB"}, {"cargo": "C", "quem": "QC"}, {"cargo": "D", "quem": "E\nF"}]
    B0 = dict(EST_DOS_CARGOS, versoes=[{"id": "v1", "nome": "demo", "clips": [{"t": "foto", "i": "f01"}]}], atual="v1",
              quando="2026-10-03T06:00:00Z", rev=2373, pagina="2026-10-02",
              creditos={"titulo": "CLARA & TIAGO", "musica": {"ficheiro": "x.mp3", "inicio": "fim"}, "ordem": ["f02", "f01"],
                        "cargos": quatro})
    corpo_js = """
var r = {passos: []}, B0 = %(b0)s;
function com(m){ var b = copia(B0); Object.keys(m).forEach(function(k){ if(m[k] === undefined) delete b[k]; else b[k] = m[k]; }); return b; }
function foto(rot){
  credLay = null;
  var L = credContas();
  r.passos.push({rot: rot, creditos: est.creditos === undefined ? null : copia(est.creditos), partes: L.partesEscolhidas, corridos: L.corridos,
    vel: L.vel, dur: L.dur, cargos: L.cargos.map(function(x){ return [x.cargo, x.pessoas.join("\\n")]; }), guardados: L.cargosGuardados,
    marcas: marcas, pilha: pilhaDesfazer.length, msg: mensagens[mensagens.length - 1] || ""});
}
// A. COMO ESTA: abrir, pintar a aba e escolher o que ja esta nao grava nada
abrir(B0); marcas = 0; var antes = JSON.stringify(est.creditos);
credHtmlDaOrdem(); credHtmlDosNomes(); credHtmlDaVelocidade(); credFormaDiz(); credHtmlDosCargos(); credAvisosDaVelocidade();
var dev = [credPoePartes(CRED_PARTES_HOJE), credNomesCorridos(false), credVelocidadeModo("fotos", false), credVelocidadeModo("nomes", false),
           credVelocidadeModo("fotos", true), credRepoeParte("cargos"), credRepoeParte("titulo"), credMoveParte("rolo", -1),
           credMoveParte("titulo", 1), credTiraParte("rolo"), credPoeVelocidade("fotos", null), credPoeVelocidade("outra", 100)];
credHtmlDaVelocidade();
r.A = {marcas: marcas, igual: JSON.stringify(est.creditos) === antes, devolveu: dev, pilha: pilhaDesfazer.length};
// B. o que eles decidiram, passo a passo, e a velocidade
foto("o principio");
credTiraParte("cargos"); foto("sem cargos");
credMoveParte("titulo", -1); foto("o titulo primeiro");
credNomesCorridos(true); foto("nomes corridos");
var p0 = pilhaDesfazer.length;
credPoeVelocidade("fotos", 100); foto("fotos a 100");
credPoeVelocidade("fotos", 95); credPoeVelocidade("fotos", 90.4); foto("fotos a 90, o mesmo gesto");
r.gesto = pilhaDesfazer.length - p0;
credPoeVelocidade("nomes", 60); foto("nomes a 60");
credVelocidadePasso("nomes", 5); foto("nomes mais 5");
credPoeVelocidade("fotos", 1000); foto("fotos acima do limite");
credPoeVelocidade("nomes", 3); foto("nomes abaixo do limite");
credVelocidadeModo("fotos", false); foto("fotos como esta");
credVelocidadeModo("nomes", false); foto("nomes como esta");
credRepoeParte("cargos"); foto("repor os cargos");
credMoveParte("cargos", -1); foto("os cargos antes do rolo");
credMoveParte("cargos", -1); foto("os cargos primeiro de todos");
credMoveParte("titulo", 1); foto("a ordem da 109");
credMoveParte("cargos", 1); foto("a ordem de hoje");
credTiraParte("titulo"); foto("sem titulo");
credRepoeParte("titulo"); foto("repor o titulo");
credNomesCorridos(false); foto("por grupos");
r.B = {fim: copia(est.creditos), pilha: pilhaDesfazer.length};
// C. o anular repoe cada passo, ate ao principio
var n = 0;
while(pilhaDesfazer.length){ desfazer(); n++; }
r.C = {fim: copia(est.creditos), n: n};
// D. um valor mal escrito a mao, que ja valia como esta, sai ao escolher «Como está»
abrir(com({creditos: Object.assign(copia(B0.creditos), {partes: "titulo,rolo", velocidade: 100, nomes_corridos: "sim"})}));
r.D = {partes: credPoePartes(CRED_PARTES_HOJE), nomes: credNomesCorridos(false), vel: credVelocidadeModo("fotos", false), fim: copia(est.creditos)};
// E. a ordem da 109 e o «Sem cargos»: a lista sai escrita e o cargos_primeiro sai; repor poe-os a seguir aos convidados
abrir(com({creditos: Object.assign(copia(B0.creditos), {cargos_primeiro: true})}));
credTiraParte("cargos"); r.E1 = copia(est.creditos);
credRepoeParte("cargos"); r.E2 = copia(est.creditos);
// F. dois aparelhos: aqui a ordem, la a velocidade e os nomes corridos: juntam-se. Os dois na ordem: conflito
abrir(B0); credTiraParte("cargos"); credMoveParte("titulo", -1);
var la = com({creditos: Object.assign(copia(B0.creditos), {velocidade: {fotos: 100}, nomes_corridos: true}), rev: 2374});
var j = juntarComBase(la);
r.F1 = {ok: j.ok, meus: j.meus, deles: j.deles, creditos: copia(est.creditos),
        partes: Object.keys(partesDe(corpo())).filter(function(k){ return /partes|nomes_corridos|velocidade/.test(k); })};
abrir(B0); credTiraParte("cargos");
j = juntarComBase(com({creditos: Object.assign(copia(B0.creditos), {partes: ["titulo", "cargos", "rolo"]}), rev: 2374}));
r.F2 = {ok: j.ok, choque: j.choque, partes: copia(est.creditos.partes)};
abrir(B0); credPoeVelocidade("fotos", 100);
j = juntarComBase(com({creditos: Object.assign(copia(B0.creditos), {velocidade: {nomes: 60}}), rev: 2374}));
r.F3 = {ok: j.ok, choque: j.choque};
// G. depois de juntar o que o outro mudou nos creditos, o anular de antes sai: repunha a copia de antes por cima do dele
abrir(B0); credNomesCorridos(true);
j = juntarComBase(com({creditos: Object.assign(copia(B0.creditos), {partes: ["titulo", "rolo"]}), rev: 2374}));
r.G = {ok: j.ok, pilha: pilhaDesfazer.length, creditos: copia(est.creditos)};
// H. a Mesa de ontem (so conhece os textos e o cargos_primeiro): muda o titulo e guarda a ordem, os corridos e a velocidade
var tudo = {partes: ["titulo", "rolo"], nomes_corridos: true, velocidade: {fotos: 100, nomes: 60}};
abrir(com({creditos: Object.assign(copia(B0.creditos), tudo)}));
credMudaTextoV53("titulo", "", "OUTRO TITULO"); r.H1 = copia(est.creditos);
abrir(com({creditos: Object.assign(copia(B0.creditos), tudo)}));
j = juntarComBase(com({creditos: r.H1, rev: 2374}));
r.H2 = {ok: j.ok, creditos: copia(est.creditos)};
console.log(JSON.stringify(r));
""" % {"b0": json.dumps(B0, ensure_ascii=False)}
    r = _correr_js(DECLARACOES_JUNTAR + DECLARACOES_FORMA, funcoes, prelude, corpo_js, problemas)
    if r:
        A = r["A"]
        if A["marcas"] or not A["igual"] or any(A["devolveu"]) or A["pilha"]:
            problemas.append("«como está» mexeu: %s" % A)
        passos = {p["rot"]: p for p in r["passos"]}
        # o que a Mesa grava, lido pelo ponto5: as mesmas partes, cargos, nomes e velocidade, e sem avisos
        for p in r["passos"]:
            av = []
            t = p5.textos_dos_creditos({"creditos": p["creditos"]} if p["creditos"] is not None else {}, av)
            esperado = [[c, "\n".join(p5.pessoas_do_quem(q))] for c, q in t["cargos"]]
            if av or t["partes"] != p["partes"] or t["nomes_corridos"] is not p["corridos"] or esperado != p["cargos"] or \
                    t["velocidade"] != {k: float(v) for k, v in p["vel"].items()}:
                problemas.append("%s: o ponto5 le %s, %s, %s%s; a Mesa mostra %s, %s, %s" % (
                    p["rot"], t["partes"], t["nomes_corridos"], t["velocidade"], (" e avisa " + "; ".join(av)) if av else "",
                    p["partes"], p["corridos"], p["vel"]))
            if (p["creditos"] or {}).get("cargos") != quatro:
                problemas.append("%s: os textos dos cargos nao ficaram guardados: %s" % (p["rot"], (p["creditos"] or {}).get("cargos")))
        sc = passos["sem cargos"]
        if sc["creditos"].get("partes") != ["rolo", "titulo"] or sc["cargos"] or sc["guardados"] != 4 or "ficam guardados" not in sc["msg"] \
                or abs(sc["dur"] - (passos["o principio"]["dur"] - 4 * 4.2)) > 1e-9:
            problemas.append("o «Sem cargos»: %s, %d cargos no filme, %s guardados, %r" % (sc["creditos"].get("partes"), len(sc["cargos"]),
                                                                                      sc["guardados"], sc["msg"][:80]))
        tp = passos["o titulo primeiro"]
        if tp["creditos"].get("partes") != ["titulo", "rolo"] or "cargos_primeiro" in tp["creditos"] or \
                abs(tp["dur"] - sc["dur"] - 0.5) > 1e-9:
            problemas.append("o titulo primeiro: %s, %.4f s" % (tp["creditos"], tp["dur"] - sc["dur"]))
        if passos["nomes corridos"]["creditos"].get("nomes_corridos") is not True or "nomes_corridos" in passos["por grupos"]["creditos"]:
            problemas.append("os nomes corridos: %s" % passos["nomes corridos"]["creditos"])
        if passos["fotos a 100"]["creditos"].get("velocidade") != {"fotos": 100} or r["gesto"] != 1 or \
                passos["fotos a 90, o mesmo gesto"]["creditos"]["velocidade"] != {"fotos": 90}:
            problemas.append("a regua das fotos: %s, %s, %d entradas no anular para tres acertos" % (
                passos["fotos a 100"]["creditos"].get("velocidade"), passos["fotos a 90, o mesmo gesto"]["creditos"].get("velocidade"), r["gesto"]))
        if passos["nomes a 60"]["creditos"]["velocidade"] != {"fotos": 90, "nomes": 60} or \
                passos["nomes mais 5"]["creditos"]["velocidade"] != {"fotos": 90, "nomes": 65} or \
                passos["nomes mais 5"]["pilha"] != passos["nomes a 60"]["pilha"] or "[" not in passos["nomes mais 5"]["msg"]:
            problemas.append("a velocidade dos nomes: %s, %s, %r" % (passos["nomes a 60"]["creditos"].get("velocidade"),
                                                                    passos["nomes mais 5"]["creditos"].get("velocidade"), passos["nomes mais 5"]["msg"][:80]))
        if passos["fotos acima do limite"]["creditos"]["velocidade"]["fotos"] != 300 or \
                passos["nomes abaixo do limite"]["creditos"]["velocidade"]["nomes"] != 30:
            problemas.append("os limites: %s" % passos["nomes abaixo do limite"]["creditos"].get("velocidade"))
        if passos["fotos como esta"]["creditos"].get("velocidade") != {"nomes": 30} or "velocidade" in passos["nomes como esta"]["creditos"]:
            problemas.append("o «Como está» de cada velocidade: %s, %s" % (passos["fotos como esta"]["creditos"].get("velocidade"),
                                                                        passos["nomes como esta"]["creditos"].get("velocidade")))
        rc = passos["repor os cargos"]
        if rc["partes"] != ["titulo", "rolo", "cargos"] or [c[0] for c in rc["cargos"]] != ["A", "B", "C", "D"]:
            problemas.append("repor os cargos: %s, %s" % (rc["partes"], rc["cargos"]))
        d109, hoje = passos["a ordem da 109"]["creditos"], passos["a ordem de hoje"]["creditos"]
        if d109.get("cargos_primeiro") is not True or "partes" in d109 or "partes" in hoje or "cargos_primeiro" in hoje:
            problemas.append("as duas ordens de antes nao ficam escritas como sempre: %s; %s" % (
                {k: d109.get(k) for k in ("partes", "cargos_primeiro")}, {k: hoje.get(k) for k in ("partes", "cargos_primeiro")}))
        if passos["sem titulo"]["creditos"].get("partes") != ["rolo", "cargos"] or "partes" in passos["repor o titulo"]["creditos"]:
            problemas.append("sem o titulo e repo-lo: %s, %s" % (passos["sem titulo"]["creditos"].get("partes"),
                                                                passos["repor o titulo"]["creditos"].get("partes")))
        if r["B"]["fim"] != B0["creditos"] or r["C"]["fim"] != B0["creditos"] or r["C"]["n"] != r["B"]["pilha"] or r["C"]["n"] < 14:
            problemas.append("o fim e o anular: fica %s; %d anulados de %d" % (r["B"]["fim"], r["C"]["n"], r["B"]["pilha"]))
        if r["D"]["partes"] is not True or r["D"]["nomes"] is not True or r["D"]["vel"] is not True or r["D"]["fim"] != B0["creditos"]:
            problemas.append("o mal escrito nao sai com «Como está»: %s" % r["D"])
        if r["E1"].get("partes") != ["rolo", "titulo"] or "cargos_primeiro" in r["E1"] or "partes" in r["E2"] or "cargos_primeiro" in r["E2"]:
            problemas.append("a ordem da 109 e o «Sem cargos»: %s; %s" % (r["E1"], r["E2"]))
        F1 = r["F1"]
        if not F1["ok"] or F1["creditos"].get("partes") != ["titulo", "rolo"] or F1["creditos"].get("velocidade") != {"fotos": 100} or \
                F1["creditos"].get("nomes_corridos") is not True or F1["creditos"].get("cargos") != quatro or \
                sorted(F1["partes"]) != ['["creditos","nomes_corridos"]', '["creditos","partes"]', '["creditos","velocidade"]']:
            problemas.append("a ordem aqui e a velocidade la: %s" % F1)
        if r["F2"]["ok"] or r["F2"]["choque"] != ["creditos"] or r["F2"]["partes"] != ["rolo", "titulo"]:
            problemas.append("a ordem nos dois: %s" % r["F2"])
        if r["F3"]["ok"] or r["F3"]["choque"] != ["creditos"]:
            problemas.append("a velocidade nos dois: %s" % r["F3"])
        if not r["G"]["ok"] or r["G"]["pilha"] != 0 or r["G"]["creditos"].get("partes") != ["titulo", "rolo"] or \
                r["G"]["creditos"].get("nomes_corridos") is not True:
            problemas.append("o anular depois de juntar: %s" % r["G"])
        for nome, cr in (("a Mesa de ontem a mudar o titulo", r["H1"]), ("a pagina nova a recebe-la", r["H2"]["creditos"])):
            if cr.get("partes") != ["titulo", "rolo"] or cr.get("nomes_corridos") is not True or \
                    cr.get("velocidade") != {"fotos": 100, "nomes": 60} or cr.get("titulo") != "OUTRO TITULO" or cr.get("cargos") != quatro:
                problemas.append("%s perdeu a ordem, os corridos ou a velocidade: %s" % (nome, cr))
    verifica("Mesa: a ordem, os nomes e a velocidade gravam, desfazem e juntam", r is not None and not problemas,
             "; ".join(problemas)[:600] if problemas else
             "como esta nao grava; %d passos lidos pelo ponto5 sem avisos (sem cargos com os 4 textos guardados, o titulo primeiro, "
             "corridos, a regua numa so entrada do anular, os limites, repor); as ordens de antes como sempre; o anular volta ao "
             "principio; juntam e chocam; a Mesa de ontem guarda tudo ao mudar o titulo" % len(r["passos"]))


def teste_creditos_1003_avisam():
    """Os avisos da velocidade sao os do ponto5, o «Sem cargos» ve-se, e a Mesa diz o que ainda nao chega ao filme.

    O DEFEITO QUE ISTO APANHA:
    - a Mesa a contar outras fotos com menos de 2 s inteiras no ecra, ou outras linhas de nomes depressa de mais, do que o
      avisos_da_velocidade() do ponto5 (com as mesmas alturas e as mesmas linhas), ou a avisar sem velocidade escolhida;
    - o lado que fica parado sem se dizer quantos segundos;
    - o «Sem cargos» sem se ver no painel dos textos (os campos a continuarem la como se fossem ao filme), ou o Validar
      a avisar de um cargo, de um titulo de grupo ou do titulo final que ja nao vao ao ecra;
    - a Mesa a deixar escolher a ordem, os nomes corridos ou a velocidade sem dizer que o filme ainda os ignora, com um
      render que nao os le; ou a dize-lo com o de agora.
    """
    if not shutil.which("node"):
        salta("Mesa: os avisos da ordem, dos nomes e da velocidade", "sem node neste PC")
        return
    import gerar_mesa
    import caracteres_para_mesa as cpm
    import creditos_para_mesa as cm
    import render
    p5 = cm._ponto5()
    problemas = []
    render.aplicar_estilo(None, [])
    cred = _cred_dos_cargos(p5)
    # 24 linhas de ensaio, uma delas com mais de 100 letras numa pessoa so (o rolo so parte entre pessoas; a 150 px/s,
    # como esta, ja pedia mais do que os 7,2 s que fica no ecra, e mesmo assim nao se avisa sem velocidade escolhida), e
    # com os invisiveis, que nao contam
    linhas = ["Pessoa %d · Outra %d" % (k, k) for k in range(22)] + ["Maria\u200d " + "de Sousa e Vasconcelos\ufe0f " * 4 + "Pereira\u2060",
                                                                      "Ana\u200d \ufe0fRita\u2060"]
    cred["grupos"] = [{"etiqueta": "Grupo 1", "titulo": "T1", "sub": "s1", "linhas": linhas}]
    cred["fotos"] = {"f01": [4000, 3000, 570], "f02": [3000, 4000, 900], "f03": [1000, 1000, 760], "f04": [4000, 2000, 380]}
    casos = [("como esta", None), ("fotos a 300", {"velocidade": {"fotos": 300}}), ("fotos a 60", {"velocidade": {"fotos": 60}}),
             ("nomes a 200", {"velocidade": {"nomes": 200}}), ("nomes a 30", {"velocidade": {"nomes": 30}}),
             ("fotos 250 nomes 180", {"velocidade": {"fotos": 250, "nomes": 180}, "nomes_corridos": True}),
             ("fotos 150", {"velocidade": {"fotos": 150}, "partes": ["titulo", "rolo"]})]
    funcoes = FUNCOES_LAYOUT_CRED + FUNCOES_CARGOS + FUNCOES_FORMA + ["function copiaFunda(", "function credGuardaDesfazer("]
    funcoes = [f for i, f in enumerate(funcoes) if f not in funcoes[:i]]
    prelude = """
var est = %(est)s, CRED = %(cred)s, credLay = null, credTemFinais = true, porId = {}, RENDER_LE = {}, credCampoAberto = null, pilhaDesfazer = [];
function esc(s){ return String(s); }
function credMsg(){} function credPinta(){} function credPintaTextos(){} function credPintaForma(){} function marcar(){}
function credAberto(){ return false; }
function credResumo(){ return {dur: 0}; }
function credTextoCurtoDoEfeito(){ return ""; }
function credMusicaEscolha(){ return null; }
""" % {"est": json.dumps(EST_DOS_CARGOS, ensure_ascii=False), "cred": json.dumps(cred, ensure_ascii=False)}
    corpo_js = """
var casos = %(casos)s, r = {casos: [], le: {}};
casos.forEach(function(c){
  if(c[1] === null) delete est.creditos; else est.creditos = c[1];
  credLay = null;
  var L = credContas(), V = credLeituraDaVelocidade(L);
  r.casos.push({Hr: L.Hr, Hc: L.Hc, alturas: L.col.map(function(p){ return p.h; }), linhas: L.pecas.filter(function(q){ return q.tipo === "nome"; }).map(function(q){ return q.texto; }),
                V: V, avisos: credAvisosDaVelocidade(), parado: L.parado ? [L.parado.quem, L.parado.s] : null, diz: credFormaDiz()});
});
// o que ainda nao chega ao filme, com um render de ontem, com o de hoje e sem se saber
est.creditos = {partes: ["titulo", "rolo"], nomes_corridos: true, velocidade: {fotos: 100}}; credLay = null;
[["hoje", {creditos_partes: true, nomes_corridos: true, creditos_velocidade: true, cargos_primeiro: true}],
 ["ontem", {creditos_partes: false, nomes_corridos: false, creditos_velocidade: false, cargos_primeiro: true}], ["sem dizer", {}]].forEach(function(x){
  RENDER_LE = x[1];
  var h = credHtmlDaOrdem() + credHtmlDosNomes() + credHtmlDaVelocidade();
  r.le[x[0]] = {partes: /data-cainda="partes"/.test(h), corridos: /data-cainda="corridos"/.test(h), velocidade: /data-cainda="velocidade"/.test(h)};
});
// com tudo como esta, um render de ontem nao tem nada de que avisar; e a ordem da 109 nao e uma ordem nova
RENDER_LE = {creditos_partes: false, nomes_corridos: false, creditos_velocidade: false, cargos_primeiro: true};
delete est.creditos; credLay = null;
var h0 = credHtmlDaOrdem() + credHtmlDosNomes() + credHtmlDaVelocidade();
est.creditos = {cargos_primeiro: true}; credLay = null;
r.le.nada = /data-cainda/.test(h0) || /data-cainda/.test(credHtmlDaOrdem());
RENDER_LE = {};
// o «Sem cargos» no painel dos textos, e os cargos de volta
est.creditos = {partes: ["titulo", "rolo"], cargos: [{cargo: "A", quem: "QA"}, {cargo: "B", quem: "QB"}]}; credLay = null;
var hs = credHtmlDosCargos(), ho = credHtmlDaOrdem();
r.sem = {caixa: /data-csemcargos/.test(hs), repor: /data-cprepoe="cargos"/.test(hs), campos: /data-ccampo/.test(hs), dois: /dos 2 cargos/.test(hs),
         naOrdem: /Sem cargos/.test(ho) && /data-cprepoe="cargos"/.test(ho) && !/data-cptira="cargos"/.test(ho),
         noFilme: [credCampoNoFilme("cargo"), credCampoNoFilme("quem"), credCampoNoFilme("titulo"), credCampoNoFilme("gtitulo")]};
est.creditos = {nomes_corridos: true, partes: ["rolo", "cargos"]}; credLay = null;
var hc = credHtmlDosCargos();
r.com = {caixa: /data-csemcargos/.test(hc), campos: /data-ccampo="cargo"/.test(hc), irForma: /data-cabrir="forma"/.test(hc),
         noFilme: [credCampoNoFilme("cargo"), credCampoNoFilme("titulo"), credCampoNoFilme("data"), credCampoNoFilme("gtitulo"), credCampoNoFilme("gsub")]};
console.log(JSON.stringify(r));
""" % {"casos": json.dumps(casos, ensure_ascii=False)}
    r = _correr_js(DECLARACOES_FORMA, funcoes, prelude, corpo_js, problemas)
    conferidos = 0
    if r:
        for (nome, cr), m in zip(casos, r["casos"]):
            t = p5.textos_dos_creditos({"creditos": cr} if cr is not None else {}, [])
            T = p5.tempos_dos_creditos(m["Hr"], m["Hc"], len(t["cargos"]), t["cargos_primeiro"], t["partes"], t["velocidade"])
            do_p5 = p5.avisos_da_velocidade(T, m["alturas"], m["linhas"])
            fotos = next((re.search(r": (\d+) das (\d+) fotos .* \(a (\d+)\.a fica ([\d.]+) s\)", a) for a in do_p5 if "coluna das fotos" in a), None)
            nomes = next((re.search(r"cada linha fica ([\d.]+) s no ecra, e (\d+) linhas .* a maior tem (\d+) letras e pede ([\d.]+) s", a)
                          for a in do_p5 if a.startswith("os nomes")), None)
            V, da_mesa = m["V"], m["avisos"]
            av_fotos = next((a for a in da_mesa if a.startswith("Com as fotos")), None)
            av_nomes = next((a for a in da_mesa if a.startswith("Com os nomes")), None)
            av_parado = next((a for a in da_mesa if "acabam" in a), None)
            if bool(fotos) != bool(av_fotos) or bool(nomes) != bool(av_nomes):
                problemas.append("%s: o ponto5 avisa %s e a Mesa %s" % (nome, [a[:40] for a in do_p5], [a[:40] for a in da_mesa]))
                continue
            if fotos:
                esperado = (int(fotos.group(1)), int(fotos.group(2)), int(fotos.group(3)), fotos.group(4))
                if (V["fotos"]["curtas"], V["fotos"]["n"], V["fotos"]["pior"], "%.1f" % V["fotos"]["s"]) != esperado or \
                        ("%d das %d fotos" % esperado[:2]) not in av_fotos or ("a %d.ª fica" % esperado[2]) not in av_fotos:
                    problemas.append("%s: as fotos no ponto5 %s, na Mesa %s (%r)" % (nome, esperado, V["fotos"], av_fotos[:90]))
                conferidos += 1
            if nomes:
                esperado = (nomes.group(1), int(nomes.group(2)), int(nomes.group(3)), nomes.group(4))
                if ("%.1f" % V["nomes"]["noEcra"], V["nomes"]["longas"], V["nomes"]["maior"], "%.1f" % V["nomes"]["pede"]) != esperado or \
                        ("a maior tem %d letras" % esperado[2]) not in av_nomes:
                    problemas.append("%s: os nomes no ponto5 %s, na Mesa %s" % (nome, esperado, V["nomes"]))
                conferidos += 1
            parado = list(T["parado"]) if T.get("parado") else None
            if m["parado"] != parado or bool(parado) != bool(av_parado) or \
                    (parado and (("%.1f" % parado[1]).replace(".", ",").rstrip("0").rstrip(",") + " s antes") not in av_parado.replace(",0 s", " s")):
                problemas.append("%s: parado no ponto5 %s, na Mesa %s (%r)" % (nome, parado, m["parado"], (av_parado or "")[:70]))
            if not t["velocidade"] and (da_mesa or 'class="aviso"' in m["diz"]["vel"]):
                problemas.append("%s: sem velocidade escolhida a Mesa avisa: %s" % (nome, da_mesa))
            # o que a aba diz: a duracao de agora e, com a escolha, a de como esta
            if ("%d px/s" % round(T["vel_fotos"])) not in m["diz"]["vel"] or ("%d px/s" % round(T["vel_nomes"])) not in m["diz"]["vel"]:
                problemas.append("%s: a aba nao diz as velocidades de agora: %s" % (nome, m["diz"]["vel"][:120]))
            if bool(t["velocidade"]) != ("(à velocidade de sempre, " in m["diz"]["vel"]):
                problemas.append("%s: a aba diz (ou cala) a velocidade de sempre ao contrario: %s" % (nome, m["diz"]["vel"][:160]))
        por = dict(zip([c[0] for c in casos], r["casos"]))
        # o de sempre sabe-se sem escolher nada: as fotos altas ficam menos de 2 s inteiras ja hoje, e diz-se como nota
        if "Como está, " not in por["como esta"]["diz"]["vel"] or por["como esta"]["V"]["fotos"]["curtas"] < 1:
            problemas.append("como esta, a aba nao diz as fotos que ja ficam menos de 2 s inteiras: %s" % por["como esta"]["diz"]["vel"][:200])
        # as letras: os invisiveis nao contam (a linha comprida tem cinco, que o letras_de_ler() do ponto5 tira)
        if por["nomes a 200"]["V"]["nomes"]["maior"] != p5.letras_de_ler(linhas[-2]) or p5.letras_de_ler(linhas[-2]) != len(linhas[-2]) - 6                 or por["como esta"]["V"]["nomes"]["longas"] != 1:
            problemas.append("a maior linha tem %d letras e a Mesa conta %d" % (p5.letras_de_ler(linhas[-2]), por["nomes a 200"]["V"]["nomes"]["maior"]))
        le = r["le"]
        if le["hoje"] != {"partes": False, "corridos": False, "velocidade": False} or le["sem dizer"] != le["hoje"] or le["nada"]:
            problemas.append("a Mesa diz que nao chega ao filme com um render que ja le, sem saber, ou sem nada escolhido: %s" % le)
        if le["ontem"] != {"partes": True, "corridos": True, "velocidade": True}:
            problemas.append("com um render de ontem a Mesa nao diz que ainda nao chega: %s" % le["ontem"])
        if r["sem"] != {"caixa": True, "repor": True, "campos": False, "dois": True, "naOrdem": True, "noFilme": [False, False, True, True]}:
            problemas.append("o «Sem cargos» no painel: %s" % r["sem"])
        if r["com"] != {"caixa": False, "campos": True, "irForma": True, "noFilme": [True, False, False, False, False]}:
            problemas.append("com cargos, sem titulo e com os nomes corridos: %s" % r["com"])
    # O VALIDAR: so o que vai ao ecra, e os avisos da velocidade em «Confirma tu»
    L = cpm.letras_do_render()
    creditos = {"cargos": [{"cargo": "Cargo \ue000", "quem": "QUEM \ue000"}], "titulo": "FIM \ue000", "data": "4 \ue000",
                "grupos": {"Grupo 1": {"titulo": "T1 \ue000", "sub": "s1 \ue000"}}}
    feitos = {}
    for nome, mais in (("tudo", {}), ("sem cargos", {"partes": ["titulo", "rolo"]}), ("corridos", {"nomes_corridos": True}),
                       ("sem titulo", {"partes": ["rolo", "cargos"]}), ("depressa", {"velocidade": {"fotos": 300}})):
        est = dict(EST_DOS_CARGOS, creditos=dict(creditos, **mais), estilo={})
        saida = _correr_validador(est, """
var CRED = %s, credLay = null, credTemFinais = true, porId = {};
function credAvisoDoTexto(){ return ""; }
function credCorpoDoTitulo(){ return 60; }
function credMinimoDaLetra(){ return 58; }
var a = validarCreditos();
process.stdout.write(JSON.stringify(a.map(function(x){ return {grau: x.grau, campo: x.cred.campo, titulo: x.titulo}; })));
""" % json.dumps(cred, ensure_ascii=False), problemas, L,
                                  mais=FUNCOES_CRED_VALIDAR + ["function credAvisosDaVelocidade(", "function credLeituraDaVelocidade(",
                                                               "function credLetrasDeLer(", "function fmtS("])
        if saida is None:
            break
        feitos[nome] = sorted({x["campo"] for x in saida})
        if nome == "depressa":
            vel = [x for x in saida if x["campo"] == "forma"]
            if len(vel) < 1 or any(x["grau"] != "confirma" for x in vel) or not any("fotos ficam menos de 2 s" in x["titulo"] for x in vel):
                problemas.append("os avisos da velocidade no Validar: %s" % vel)
    if feitos:
        esperado = {"tudo": ["cargo", "data", "gsub", "gtitulo", "quem", "titulo"], "sem cargos": ["data", "gsub", "gtitulo", "titulo"],
                    "corridos": ["cargo", "data", "quem", "titulo"], "sem titulo": ["cargo", "gsub", "gtitulo", "quem"],
                    "depressa": ["cargo", "data", "forma", "gsub", "gtitulo", "quem", "titulo"]}
        if feitos != esperado:
            problemas.append("o Validar olha para textos que nao vao ao ecra: %s" % {k: v for k, v in feitos.items() if v != esperado.get(k)})
    # O GERAR_MESA: o ponto5 de agora faz as tres coisas, e um de ontem nao
    texto = io.open(PONTO5, encoding="utf-8").read()
    hoje = gerar_mesa.le_as_partes_dos_creditos(texto, p5)
    if hoje != {"creditos_partes": True, "nomes_corridos": True, "creditos_velocidade": True}:
        problemas.append("o ponto5 de agora faz as partes, os corridos e a velocidade, e o gerar_mesa diz %s" % hoje)
    ontem = gerar_mesa.le_as_partes_dos_creditos(re.sub(r'"partes"|"nomes_corridos"|"velocidade"', '"x"', texto))
    if ontem != {"creditos_partes": False, "nomes_corridos": False, "creditos_velocidade": False}:
        problemas.append("um ponto5 sem as chaves: %s" % ontem)

    class Ponto5DeOntem:
        """le as chaves no texto, mas faz as contas de 2 de outubro: sem as partes, o rolo corrido nem a velocidade"""
        def __getattr__(self, nome_):
            return getattr(p5, nome_)

        def tempos_dos_creditos(self, alto_rolo, alto_coluna, n_cargos, cargos_primeiro=False, partes=None, velocidade=None):
            return p5.tempos_dos_creditos(alto_rolo, alto_coluna, n_cargos, cargos_primeiro)

        def rolo_de_nomes(self, blocos, corridos=False):
            return p5.rolo_de_nomes(blocos)
    meio = gerar_mesa.le_as_partes_dos_creditos(texto, Ponto5DeOntem())
    if meio != {"creditos_partes": False, "nomes_corridos": False, "creditos_velocidade": False}:
        problemas.append("um ponto5 que le as chaves e nao as faz: %s" % meio)
    tudo = gerar_mesa.o_que_o_render_le()
    if any(tudo.get(k) is not True for k in hoje):
        problemas.append("o o_que_o_render_le() nao as traz: %s" % {k: tudo.get(k) for k in hoje})
    verifica("Mesa: os avisos da ordem, dos nomes e da velocidade", r is not None and not problemas,
             "; ".join(problemas)[:600] if problemas else
             "%d casos com as fotos e os nomes contados como o avisos_da_velocidade() (%d avisos iguais), o que fica parado, o «Sem "
             "cargos» no painel, o Validar so com o que vai ao ecra, e o render de ontem a dar «ainda não chega ao filme»"
             % (len(casos), conferidos))


def main():
    for nome, f in list(globals().items()):
        if nome.startswith("teste_") and callable(f):
            try:
                f()
            except Exception as erro:          # um teste que rebenta conta como falha, com o motivo
                verifica(nome, False, "rebentou: %s" % erro)
    print("\n%d passaram, %d falharam, %d saltados" % (len(PASSOU), len(FALHAS), len(SALTADOS)))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
