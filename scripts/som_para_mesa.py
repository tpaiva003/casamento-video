# -*- coding: utf-8 -*-
"""A banda sonora como o render a toca, preparada para a Mesa a mostrar.

O Tiago: "Atualiza completamente a Mesa de Montagem assegurando que fica fiel ao que
ja temos no video renderizado em termos de scripts que tens vindo a falar como o
clair, etc." A Mesa so via as musicas que ele marcou. As que o montar_da_mesa.py poe
sozinho (o Lang Lang da abertura, o rebobinar, os foguetes, o Rei Leao, a retoma na
fita antes da Clara, a Clarinha) e o que ele muda (silencio saltado, cartao esticado
para os foguetes, duracao medida dos videos) nao apareciam em lado nenhum.

Le data/montagens/<nome>.csv e <nome>.som.csv, os mesmos que o render usa, e devolve
um dicionario pequeno. Cada faixa e cada clip leva uma chave que a Mesa sabe calcular
a partir do seu proprio estado (tipo mais id, fotos, texto ou ficheiro, e a ordem de
aparicao quando ha repetidos), para a Mesa encontrar o clip mesmo que ele tenha mudado
coisas de sitio depois da ultima montagem.
"""
import csv
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render          # noqa: E402  (depois do sys.path: e o vizinho, nao um instalado)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTAGENS = os.path.join(REPO, "data", "montagens")
EFEITOS = ("Candidato a vereador.mp3", "rebobinar.wav")


def chave_base(linha):
    """A mesma chave que a Mesa calcula em chaveDoClip()."""
    tipo = linha["tipo"]
    if tipo == "foto" or tipo in ("lado", "colagem", "pilha"):
        return tipo + ":" + (linha["id"] or "")
    if tipo == "video":
        return "video:" + (linha["ficheiro"] or "").strip()
    return tipo + ":" + " ".join((linha["texto_ecra"] or "").split())


def origem(nota):
    if nota.startswith("marcada na Mesa"):
        return "mesa"
    return "regra"


# As notas do montar_da_mesa.py sao para mim e estao sem acentos. Na Mesa quem as le e
# o Tiago: cada regra diz o que faz e de que decisao vem.
EXPLICACOES = (
    ("do pedido ate ao nascimento do Tiago", "música da abertura, até aos foguetes do nascimento do Tiago"),
    ("fita a rebobinar", "som da fita a rebobinar enquanto o contador recua"),
    ("foguetes, nascimento do Tiago", "foguetes e aleluia quando acende «Nasce o Tiago» (decisões 027 e 072)"),
    ("Rei Leao", "Rei Leão, dos foguetes do Tiago até a fita voltar antes da Clara (decisões 057 e 060)"),
    ("retoma a musica da abertura", "a música da abertura volta onde tinha parado, na fita antes da Clara (decisão 060)"),
    ("foguetes, no primeiro texto da Clara", "foguetes no primeiro texto da Clara (decisão 027)"),
    ("a musica da Clarinha", "a música da Clarinha que a mãe da Clara pôs no bloco dela"),
    ("voz do pedido", "voz gravada no dia do pedido, por cima das fotos do pedido (decisão 075)"),
    ("som do video", "o som do próprio vídeo, que toca enquanto ele passa no meio do filme"),
)

# O que a musica por baixo das vozes esta a fazer. Vem da coluna `abafar` do som.csv, que
# so existe quando ha vozes: o render baixa ali o leito sem o cortar, para ele voltar no
# ponto onde estaria se as vozes nao existissem. O texto e para a Mesa, logo com acentos.
ABAFADA = ", mais baixa por baixo %s"
PARADA = ", parada por baixo %s"
# QUEM ESTA POR CIMA. A coluna `abafar` so diz quando e quanto, nao diz quem, e desde 17 de
# setembro tanto pode ser uma voz do pedido como o som de um video do corpo. Dizer sempre
# "das vozes do pedido" era escrever ao Tiago uma coisa que nao e verdade, por isso
# procura-se quem esta a tocar naquela janela.
POR_BAIXO = {("voz",): "das vozes do pedido", ("video",): "do som do vídeo",
             ("video", "voz"): "das vozes do pedido e do som do vídeo",
             (): "do que entra por cima"}


def formas_do_abafar(abafa, quem):
    """O que a música faz por baixo de cada coisa, e não uma forma só para todas.

    A ESCOLHA ERA all(k <= 0.001): bastava uma janela que não parasse a música para todas
    passarem a «mais baixa». Ele punha o vídeo com «Música por baixo: parada» e uma foto ali
    perto com vozes e a música mais baixa, e a Mesa dizia-lhe «mais baixa» para as duas: por
    baixo do vídeo a música calava-se mesmo e ele não o sabia. Agora é uma frase por forma,
    cada uma com quem está por cima dela.
    """
    param = [j for j in abafa if j[2] <= 0.001]
    baixam = [j for j in abafa if j[2] > 0.001]
    pedacos = []
    if baixam:
        pedacos.append(ABAFADA % quem(baixam))
    if param:
        pedacos.append(PARADA % quem(param))
    return (pedacos[0] + " e" + pedacos[1][1:]) if len(pedacos) == 2 else "".join(pedacos)


def ler_abafar(celula):
    """A coluna `abafar` -> [(inicio, fim, fator)], no relógio do corpo. Vazia, nenhuma.

    A LEITURA E A DO RENDER, UMA SO. Havia aqui uma segunda cópia do mesmo parser, com
    arredondamento diferente, que é exatamente a receita que o CLAUDE.md regista como causa
    do defeito das três cópias da regra de ampliação: a que fazia o vídeo era a que estava
    por corrigir. Aqui só se arredonda à saída, que é o que a Mesa mostra.
    """
    return [(round(a, 2), round(b, 2), k) for a, b, k in render.ler_abafar(celula)]


def explica(nota):
    if nota.startswith("marcada na Mesa"):
        return "marcada por ti"
    for comeco, texto in EXPLICACOES:
        if nota.startswith(comeco):
            return texto
    return nota


def som_para_mesa(nome="v3", versao="demo_v3"):
    cam = os.path.join(MONTAGENS, nome + ".csv")
    cam_som = os.path.join(MONTAGENS, nome + ".som.csv")
    if not (os.path.exists(cam) and os.path.exists(cam_som)):
        return None
    with open(cam, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    with open(cam_som, encoding="utf-8-sig", newline="") as fh:
        faixas = list(csv.DictReader(fh))
    if not linhas:
        return None

    vistos, clips = {}, []
    for l in linhas:
        base = chave_base(l)
        vistos[base] = vistos.get(base, 0) + 1
        clips.append({"chave": "%s#%d" % (base, vistos[base]), "tipo": l["tipo"],
                      "inicio": round(float(l["inicio_s"]), 2), "fim": round(float(l["fim_s"]), 2),
                      "d": round(float(l["duracao_s"]), 2)})
    # O CORPO E O QUE NAO ESTA NO BLOCO INICIAL, e nao "tudo o que nao e video": desde 17
    # de setembro um video pode estar no meio da montagem e ai ele e um clip do corpo como
    # outro qualquer. A conta e a do render, para a Mesa marcar o som no instante certo.
    fanfarra, corpo = render.partir_em_fanfarra_e_corpo(clips)
    desvio = corpo[0]["inicio"] if corpo else 0.0
    # O render junta os videos da abertura inteiros antes do corpo, sem encadeado: o corpo
    # comeca no filme onde eles acabam, e nao no inicio_s do CSV.
    videos = sum(c["d"] for c in fanfarra)

    def clip_em(t_corpo):
        t = t_corpo + desvio
        dentro = [c for c in corpo if c["inicio"] - 0.001 <= t < c["fim"]]
        return (dentro[-1] if dentro else (corpo[-1] if corpo else None)), t

    por_cima = {}
    for coluna in ("voz", "video"):
        por_cima[coluna] = [(float(r["quando_s"]), float(r["quando_s"]) + float(r["dura_s"]))
                            for r in faixas if (r.get(coluna) or "").strip()]

    def quem_esta_por_cima(janelas):
        quais = tuple(sorted(c for c, tempos in por_cima.items()
                             if any(a < b2 and a2 < b for a, b, _k in janelas
                                    for a2, b2 in tempos)))
        return POR_BAIXO.get(quais, POR_BAIXO[()])

    saida = []
    for f in sorted(faixas, key=lambda r: float(r["quando_s"])):
        quando = float(f["quando_s"])
        clip, t = clip_em(quando)
        abafa = ler_abafar(f.get("abafar"))
        texto = explica(f["nota"])
        if abafa:
            texto += formas_do_abafar(abafa, quem_esta_por_cima)
        saida.append({
            "f": f["ficheiro"], "filme": round(videos + quando, 2), "corpo": round(quando, 2),
            "in": round(float(f["in_s"] or 0), 2), "dura": round(float(f["dura_s"]), 2),
            "nota": f["nota"], "explica": texto, "origem": origem(f["nota"]),
            "efeito": f["ficheiro"] in EFEITOS,
            "voz": bool((f.get("voz") or "").strip()),
            "video": bool((f.get("video") or "").strip()),
            "abafa": [[a, b, k] for a, b, k in abafa],
            "clip": clip["chave"] if clip else "", "dentro": round(t - clip["inicio"], 2) if clip else 0.0,
        })
    feito = datetime.datetime.fromtimestamp(os.path.getmtime(cam_som))
    # Instante de cada clip no filme final: os videos pela ordem, e o corpo a seguir.
    t_video = 0.0
    for c in fanfarra:
        c["filme"] = round(t_video, 2)
        t_video += c["d"]
    for c in corpo:
        c["filme"] = round(videos + c["inicio"] - desvio, 2)
    return {"montagem": nome, "versao": versao, "gerado": feito.strftime("%d/%m às %H:%M"),
            "videos": round(videos, 2), "fim": round(videos + max(c["fim"] for c in corpo) - desvio, 2) if corpo else 0,
            "faixas": saida, "clips": [{"chave": c["chave"], "d": c["d"], "filme": c["filme"]} for c in clips]}


if __name__ == "__main__":
    import json
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(som_para_mesa(), ensure_ascii=False, indent=1)[:3000])
