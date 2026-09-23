# -*- coding: utf-8 -*-
"""Junta a Mesa que o Tiago acabou de gravar com o que so existe na copia local.

PORQUE EXISTE: durante uma tarde a base de dados da Mesa recusou todas as escritas
(so aceita com if_version, e a ferramenta Artifact ainda nao o deixava passar). Os dois
videos de abertura, as tres partes da fita de 1995 e a Clair nos penteados ficaram so
na copia local data/mesa_estado.json, e cada gravacao dele vinha sem eles; sem a fita o
nascimento do Tiago nao e encontrado e o Lang Lang, os foguetes e o Rei Leao saem mudos.
A 14 de setembro a noite a escrita voltou a entrar e as pecas foram repostas na Mesa
(decisao 061). Continua a correr-se antes de cada render: se estiver tudo, diz "nada".

O QUE FAZ: parte SEMPRE da versao dele, e so acrescenta, nos mesmos vizinhos, o que a
copia local tem e a dele nao tem:
  - os videos do inicio
  - as partes da fita de 1995 com o Kobe (duas depois do contador, uma antes do
    cartao "nasce uma bebe")
  - a musica do cartao dos penteados, se ele nao tiver posto outra
Se ele ja tiver alguma destas pecas na Mesa, nao a duplica: deixa a dele.
Tudo o resto e dele e fica como ele deixou. A copia local anterior e guardada ao lado
da leitura antes de ser substituida.

Uso:
    (ler a base com Artifact read_db, out_dir saida/leitura_mesaN; o documento da Mesa
     e montagem/estado2 desde 15 de setembro, o antigo montagem/estado ja ninguem le)
    py -3.11 scripts/juntar_mesa.py saida/leitura_mesaN/montagem/estado2.json
    py -3.11 scripts/montar_da_mesa.py demo_v3 --nome v3
"""
import datetime
import json
import os
import shutil
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linha_tempo      # noqa: E402  (depois do sys.path: e o vizinho, nao um instalado)
import render           # noqa: E402  (so para a conta do bloco inicial ser UMA so)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(REPO, "data", "mesa_estado.json")
VERSAO = "demo_v3"


def sem_acentos(texto):
    return "".join(ch for ch in unicodedata.normalize("NFD", texto or "")
                   if unicodedata.category(ch) != "Mn").lower()


def versao(est):
    for v in est.get("versoes", []):
        if v.get("id") == VERSAO:
            return v
    sys.exit("Nao encontrei a versao %s" % VERSAO)


def e_fita_kobe(c):
    return c.get("t") == "marcos" and (c.get("x") or "").startswith("1995@") and "Kobe" in (c.get("x") or "")


def e_penteados(c):
    return c.get("t") == "cartao" and "penteado" in sem_acentos(c.get("x"))


def e_contador_da_abertura(c):
    """O contador que recua E ACABA EM 1995: e ao lado dele que a fita de 1995 entra.

    Ha outros contadores. O 1995>2011 avanca, e nunca foi este. Mas desde 17 de setembro
    a abertura tem DOIS a recuar, o das datas do casamento ate ao pedido e o de 2025 a
    1995, e "recua" passou a encontrar dois: o indice_unico parava a juncao inteira sem
    juntar nada, e quem corresse o render a seguir renderizava sem a fita.

    O que distingue este e onde ele ACABA. A fita de 1995 vem logo a seguir ao contador
    que chega a 1995, seja ele por anos ou por datas.
    """
    if c.get("t") != "contador":
        return False
    return (linha_tempo.contador_recua(c.get("x") or "")
            and linha_tempo.ano_de_chegada(c.get("x") or "") == 1995)


def bloco_inicial(clips):
    """Os clips de video que estao ANTES de qualquer outro clip: a fanfarra, e so ela.

    A conta e a do render (partir_em_fanfarra_e_corpo), para nao haver duas contas
    parecidas em dois ficheiros. Os clips t:"fanfarra", que as versoes v1a, v1b e v1c ainda
    trazem, saltam-se primeiro, porque e isso que o montar_da_mesa.py faz antes de contar:
    para ele um video a seguir a um desses continua a ser bloco inicial.
    """
    uteis = [c for c in clips if c.get("t") != "fanfarra"]
    inicio, _resto = render.partir_em_fanfarra_e_corpo(
        [{"tipo": c.get("t") or "foto"} for c in uteis])
    return uteis[:len(inicio)]


def indice_unico(clips, cond, o_que):
    idx = [k for k, c in enumerate(clips) if cond(c)]
    if len(idx) != 1:
        sys.exit("PAREI, sem mexer em nada: %s aparece %d vezes na versao dele" % (o_que, len(idx)))
    return idx[0]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    remoto_caminho = sys.argv[1]
    remoto = json.load(open(remoto_caminho, encoding="utf-8"))
    local = json.load(open(LOCAL, encoding="utf-8"))
    dele, meu = versao(remoto)["clips"], versao(local)["clips"]
    novo = list(dele)
    feito = []

    # SO O BLOCO INICIAL E QUE E FANFARRA, e so ele e que se repoe a cabeca.
    #
    # A conta era "tipo == video" contra o resto, escrita quando todo o video era abertura,
    # e desde 17 de setembro um video pode estar no MEIO da montagem. Com a conta antiga
    # havia duas maneiras de isto mentir: um video do meio da copia local ia parar a
    # fanfarra, colado a 20th Century Fox, e o corpo ficava sem ele; e uma Mesa que tivesse
    # perdido a abertura mas guardado o video do meio "ja tinha um video", a guarda nao
    # disparava, a fanfarra nao era reposta e o script imprimia "nada" com o filme a abrir
    # no contador, sem a 20th Century Fox nem a historia da Clara que a decisao 001 protege.
    #
    # Um video que na copia local esta no corpo nao e fanfarra e nao entra por aqui: nao se
    # sabe, sem os vizinhos, onde ele ficaria na versao dele. Fica o aviso.
    meus_iniciais = bloco_inicial(meu)
    if meus_iniciais and not bloco_inicial(dele):
        novo[0:0] = meus_iniciais
        feito.append("%d videos no inicio" % len(meus_iniciais))
    # Pela identidade e nao por igualdade: dois clips do mesmo video com os mesmos campos
    # sao dicionarios iguais, e um deles pode estar no inicio e o outro no meio.
    meus_do_meio = [c for c in meu
                    if c.get("t") == "video" and not any(c is x for x in meus_iniciais)]
    em_falta = [c for c in meus_do_meio
                if not [d for d in dele
                        if d.get("t") == "video" and d.get("f") == c.get("f")]]
    for c in em_falta:
        print("AVISO: o video %s esta no MEIO da copia local e nao esta na Mesa dele; "
              "nao o juntei, porque so ele sabe onde o quer. Poe-o na Mesa."
              % (c.get("f") or "(sem nome)"))

    fitas = [c for c in meu if e_fita_kobe(c)]
    if len(fitas) == 3 and not [c for c in dele if e_fita_kobe(c)]:
        k = indice_unico(novo, e_contador_da_abertura, "o contador da abertura")
        novo[k + 1:k + 1] = fitas[:2]
        k = indice_unico(novo, lambda c: c.get("t") == "cartao" and "nasce uma bebe" in sem_acentos(c.get("x")),
                         'o cartao "nasce uma bebe"')
        novo[k:k] = [fitas[2]]
        feito.append("3 partes da fita de 1995")
    elif fitas and len(fitas) != 3:
        print("AVISO: a copia local tem %d partes da fita de 1995 e nao 3; nao as juntei" % len(fitas))

    # A FITA VAZIA DE 1995 entre as viagens passou a contador 1995>2011 (decisao 061).
    # A 15 de setembro uma copia antiga de um separador trouxe-a de volta a Mesa.
    vazias = [k for k, c in enumerate(novo)
              if c.get("t") == "marcos" and (c.get("x") or "").startswith("1995@0.000000-0.384409c")]
    tem_2011 = any(c.get("t") == "contador" and (c.get("x") or "").partition("|")[0].replace(" ", "") == "1995>2011"
                   for c in novo)
    if len(vazias) == 1 and not tem_2011:
        k = vazias[0]
        novo[k] = {"t": "contador", "i": "", "f": "", "x": "1995>2011", "d": 9, "c": novo[k].get("c", 0.7), "r": "fiel"}
        feito.append("contador 1995>2011 no lugar da fita vazia de 1995")

    musica = next(((c.get("m") or {}) for c in meu if e_penteados(c) and (c.get("m") or {}).get("f")), None)
    if musica:
        k = indice_unico(novo, e_penteados, "o cartao dos penteados")
        if (novo[k].get("m") or {}).get("f"):
            print("A musica dos penteados e a dele (%s); nao lhe toquei" % novo[k]["m"]["f"])
        else:
            novo[k] = dict(novo[k], m=musica)
            feito.append("musica dos penteados")

    copia = os.path.join(os.path.dirname(os.path.abspath(remoto_caminho)), "mesa_estado_antes.json")
    shutil.copyfile(LOCAL, copia)
    versao(remoto)["clips"] = novo
    remoto["quando"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # A revisao sobe uma: a Mesa so grava por cima se a base estiver na revisao em que
    # ela se apoia, e assim uma Mesa aberta com a versao anterior ja nao passa.
    remoto["rev"] = int(remoto.get("rev") or 0) + 1
    with open(LOCAL, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(remoto, fh, ensure_ascii=False)
    print("Versao dele: %d clips. Juntada: %d clips." % (len(dele), len(novo)))
    print("Juntei: %s" % (", ".join(feito) if feito else "nada, ja estava tudo na Mesa dele"))
    print("Copia local anterior: %s" % copia)


if __name__ == "__main__":
    main()
