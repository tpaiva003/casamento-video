# -*- coding: utf-8 -*-
"""Atualiza todas as fotografias da Mesa de Montagem, de ponta a ponta.

O Tiago: "Nao te esquecas de fazer update as fotos que tratares na mesa, alias
podias colocar la um botao para atualizar". A Mesa nao consegue correr nada neste
computador; o botao dela deixa um pedido na base de dados, e e este script que
faz a atualizacao. Um comando so, pela ordem certa, para nunca ficar um passo
esquecido pelo meio:

  1  inventario.py            regista o que ele largou na 01-NOVAS
  2  upscale.py               versao lanczos, a unica melhorada que entra (decisao 090)
  3  (upscale_ia.py)          ja nao corre: a rede neuronal saiu do filme (decisao 090)
  4  consolidar.py            escolhe a versao de cada foto e escreve o indice
  5  gerar_editor.py          miniaturas da Mesa, a partir da FINAIS
  6  gerar_montagens_editor.py
  7  estado_fotos.py          o retrato do que ficou pronto e do que falta
  8  gerar_previas.py         a foto em grande, para o botao de ampliar da Mesa
  9  gerar_mesa.py            cola tudo em saida/mesa.html

A rede neuronal podia demorar horas, e o --sem-ia saltava-a. Desde 28 de setembro nao corre
nunca: desenhava olhos e bocas nas caras pequenas das fotos de grupo, e o consolidar.py ja nao
escolhe a versao dela. O --sem-ia continua a ser aceite e nao faz nada.

Depois disto faltam dois passos que so o Claude faz, com a ferramenta Artifact:
publicar saida/mesa.html no link da Mesa, com as folhas das previas como ficheiros ao
lado (o link aceita no maximo 256 ficheiros ao todo), e escrever o documento
montagem/publicacao com o build do data/estado_fotos.json, para as Mesas saberem
que ha versao nova.

AS FOLHAS NUNCA SE PUBLICAM PELO NOME DO DISCO (3 de outubro, decisao 114). No endereco
chamam-se previas/folha_NN_<dez letras do sha256>.jpg, que e o nome que o gerar_mesa.py
poe no indice da pagina. A lista certa, com o `from` de cada folha e os null das que
sairam, e a do saida/entrada_rapida.json: depois deste script corre-se
py -3.11 scripts/entrada_rapida.py para a ter, publica-se por ela, e no fim o --publicado.

Desde 3 de outubro ha tambem o scripts/entrada_rapida.py, que da o mesmo resultado sem refazer
as contas das fotos que nao mudaram (cerca de um minuto em vez de seis) e escreve
saida/entrada_rapida.json com o que entrou, os avisos e a lista exata do que ha para publicar.
O --rapido deste script chama-o. Sem o --rapido, tudo aqui e como sempre foi, com duas coisas
a mais, de 3 de outubro: pede a mesma tranca da entrada rapida (as duas ao mesmo tempo escreviam o
mesmo inventario, a mesma FINAIS e a mesma pagina), e, se o consolidar recusar uma versao lanczos
pela alteracao (a foto foi trocada na pasta por outra com o mesmo nome e o mesmo tamanho, e a
versao que la esta e a da antiga), refaz so essa com o upscale.py --so-ids e consolida outra vez.

Uso:  py -3.11 scripts/atualizar_fotos.py
      py -3.11 scripts/atualizar_fotos.py --sem-ia
      py -3.11 scripts/atualizar_fotos.py --rapido     o mesmo, pelo scripts/entrada_rapida.py
"""
import csv
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def passo(n, nome, *args):
    print()
    print("[%d] %s %s" % (n, nome, " ".join(args)))
    inicio = time.time()
    r = subprocess.run([PY, os.path.join(AQUI, nome)] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    saida = [l for l in (r.stdout or "").replace("\r", "\n").splitlines() if l.strip()]
    for linha in saida[-8:]:
        print("    " + linha)
    if r.returncode != 0:
        print("    ERRO (codigo %d):" % r.returncode)
        for linha in (r.stderr or "").strip().splitlines()[-12:]:
            print("    " + linha)
        sys.exit("Parou no passo %d. Nada do que vem a seguir foi feito." % n)
    print("    feito em %.0f s" % (time.time() - inicio))


def conteudos():
    """{(pasta, ficheiro): (id, sha256)} do inventario como esta agora."""
    caminho = os.path.join(os.path.dirname(AQUI), "data", "inventario.csv")
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        return {(r["pasta"], r["ficheiro"]): (r["id"], r["sha256"]) for r in csv.DictReader(fh)}


def versoes_velhas():
    """Os id das fotos cuja versao lanczos o consolidar acabou de recusar pela alteracao."""
    caminho = os.path.join(os.path.dirname(AQUI), "data", "finais.csv")
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        return [r["id"] for r in csv.DictReader(fh) if "lanczos:alteracao" in (r.get("recusadas") or "")]


def main():
    if "--rapido" in sys.argv:
        resto = [a for a in sys.argv[1:] if a not in ("--rapido", "--sem-ia")]
        sys.exit(subprocess.call([PY, os.path.join(AQUI, "entrada_rapida.py")] + resto))
    sys.path.insert(0, AQUI)
    import entrada_rapida
    entrada_rapida.trancar("atualizar_fotos.py")
    antes = conteudos()
    passo(1, "inventario.py")
    # uma foto trocada por outra com o mesmo nome (o sha256 mudou no mesmo caminho): a versao
    # ampliada que la esta e a da foto antiga, e o passo 2 saltava-a por ter o tamanho certo
    trocadas = [i for k, (i, h) in conteudos().items() if k in antes and antes[k][1] != h]
    if trocadas:
        passo(2, "upscale.py", "--so-ids", ",".join(trocadas))
    passo(2, "upscale.py")
    print()
    print("[3] upscale_ia.py: nao corre, a rede neuronal saiu do filme (decisao 090)")
    passo(4, "consolidar.py")
    velhas = versoes_velhas()
    if velhas:
        print()
        print("    %d com a versao ampliada de outra fotografia (a foto foi trocada): refazem-se" % len(velhas))
        passo(2, "upscale.py", "--so-ids", ",".join(velhas))
        passo(4, "consolidar.py")
    passo(5, "gerar_editor.py")
    passo(6, "gerar_montagens_editor.py")
    passo(7, "estado_fotos.py")
    passo(8, "gerar_previas.py")
    passo(9, "gerar_mesa.py")
    print()
    print("Pronto neste computador. Falta publicar a Mesa e escrever montagem/publicacao.")


if __name__ == "__main__":
    main()
