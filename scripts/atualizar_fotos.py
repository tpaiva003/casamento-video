# -*- coding: utf-8 -*-
"""Atualiza todas as fotografias da Mesa de Montagem, de ponta a ponta.

O Tiago: "Nao te esquecas de fazer update as fotos que tratares na mesa, alias
podias colocar la um botao para atualizar". A Mesa nao consegue correr nada neste
computador; o botao dela deixa um pedido na base de dados, e e este script que
faz a atualizacao. Um comando so, pela ordem certa, para nunca ficar um passo
esquecido pelo meio:

  1  inventario.py            regista o que ele largou na 01-NOVAS
  2  upscale.py               versao lanczos, usada abaixo de 1,5x (decisao 052)
  3  upscale_ia.py --min 1.5  rede neuronal so onde vai ser usada (decisao 052)
  4  consolidar.py            escolhe a versao de cada foto e escreve o indice
  5  gerar_editor.py          miniaturas da Mesa, a partir da FINAIS
  6  gerar_montagens_editor.py
  7  estado_fotos.py          o retrato do que ficou pronto e do que falta
  8  gerar_previas.py         a foto em grande, para o botao de ampliar da Mesa
  9  gerar_mesa.py            cola tudo em saida/mesa.html

A rede neuronal pode demorar horas. Com --sem-ia salta o passo 3: as fotos que
precisam dele ficam marcadas "a espera" no botao da Mesa, em vez de ficarem
escondidas.

Depois disto faltam dois passos que so o Claude faz, com a ferramenta Artifact:
publicar saida/mesa.html no link da Mesa, com as folhas saida/previas/folha_NN.jpg
como ficheiros ao lado (o link aceita no maximo 256 ficheiros ao todo; as folhas com
o mesmo nome substituem-se, e se passar a haver menos folhas as que sobram tiram-se
com null), e escrever o documento
montagem/publicacao com o build do data/estado_fotos.json, para as Mesas que
estejam abertas saberem que ha versao nova.

Uso:  py -3.11 scripts/atualizar_fotos.py
      py -3.11 scripts/atualizar_fotos.py --sem-ia
"""
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


def main():
    sem_ia = "--sem-ia" in sys.argv
    passo(1, "inventario.py")
    passo(2, "upscale.py")
    if sem_ia:
        print()
        print("[3] upscale_ia.py saltado (--sem-ia): essas fotos ficam a espera")
    else:
        passo(3, "upscale_ia.py", "--min", "1.5")
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
