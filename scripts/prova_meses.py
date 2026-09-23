# -*- coding: utf-8 -*-
"""Prova que a assinatura do corpo sintetico mudou POR CAUSA dos meses da fita e de mais nada.

Corrido a 23 de setembro, decisao 084: 47 dos 560 fotogramas mudaram, do 53 ao 99, todos com
o clip de marcos no ecra. Fica aqui como molde para a proxima vez que uma mudanca de proposito
no desenho obrigar a refazer a ASSINATURA_CORPO_SINTETICO: mede-se antes de refazer.

O precedente das duas vezes anteriores (testes.py, ASSINATURA_CORPO_SINTETICO) e este: antes de
refazer a assinatura, mostrar que o render de agora com o linha_tempo de ANTES da a assinatura
antiga, que com o de agora da a nova, e que os fotogramas que mudam sao so os que tem a peca
alterada no ecra.
"""
import hashlib
import importlib.util
import io
import contextlib
import os
import re
import shutil
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
REPO = r"C:\casamento-video"
sys.path.insert(0, os.path.join(REPO, "scripts"))
import testes      # noqa: E402
import render      # noqa: E402

AGORA = os.path.join(REPO, "scripts", "linha_tempo.py")


def modulo_de_antes():
    """O linha_tempo com os meses como estavam: fina 32, minusculas, (128,114,122)."""
    fonte = io.open(AGORA, encoding="utf-8").read()
    antes = fonte.replace(
        "    f_mes = ImageFont.truetype(FONTE, 38)",
        "    f_mes = ImageFont.truetype(FONTE_FINA, 32)")
    antes = antes.replace(
        "            cinza = tuple(int(c * k) for c in REGUA_TEXTO)\n"
        "            d.line([(x, y_linha - 9), (x, y_linha + 9)],\n"
        "                   fill=tuple(int(c * k) for c in LINHA), width=2)\n"
        "            _texto(d, MESES_CURTOS[m], f_mes, x, y_linha + 34, cinza)",
        "            cinza = tuple(int(c * k) for c in (128, 114, 122))\n"
        "            d.line([(x, y_linha - 9), (x, y_linha + 9)],\n"
        "                   fill=tuple(int(c * k) for c in LINHA), width=2)\n"
        "            _texto(d, _MESES_ANTIGOS[m], f_mes, x, y_linha + 34, cinza)")
    antes = antes.replace(
        "REGUA_TEXTO = (176, 164, 172)",
        "REGUA_TEXTO = (176, 164, 172)\n_MESES_ANTIGOS = [\"jan\", \"fev\", \"mar\", \"abr\", \"mai\","
        " \"jun\", \"jul\", \"ago\", \"set\", \"out\", \"nov\", \"dez\"]")
    if antes == fonte:
        sys.exit("Nao consegui reconstruir a versao de antes: o texto nao bateu certo")
    pasta = tempfile.mkdtemp(prefix="linha_tempo_antes_")
    caminho = os.path.join(pasta, "linha_tempo_antes.py")
    io.open(caminho, "w", encoding="utf-8").write(antes)
    spec = importlib.util.spec_from_file_location("linha_tempo_antes", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, pasta


def assinaturas():
    """{fotograma: md5} do corpo sintetico com o linha_tempo que estiver em render."""
    pasta = tempfile.mkdtemp(prefix="prova_meses_")
    guardado = testes._resolucao(render, 480, 270)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            nome, caminhos = testes._montagem_sintetica(pasta)
            estado = testes._estado_sintetico(render, pasta, nome, caminhos)
            total = estado["total_quadros"]
            saida, fila = {}, list(range(total))

            def escrever(bytes_):
                saida[fila.pop(0)] = hashlib.md5(bytes_).hexdigest()

            render.desenhar_fatia(range(total), estado, escrever)
        return saida, estado
    finally:
        testes._resolucao(render, *guardado) if isinstance(guardado, tuple) else None
        shutil.rmtree(pasta, ignore_errors=True)


def main():
    novo, estado = assinaturas()
    tudo_novo = hashlib.md5("".join(novo[q] for q in range(len(novo))).encode()).hexdigest()

    antigo_mod, pasta = modulo_de_antes()
    guarda = render.linha_tempo
    render.linha_tempo = antigo_mod
    try:
        velho, _e = assinaturas()
    finally:
        render.linha_tempo = guarda
        shutil.rmtree(pasta, ignore_errors=True)
    tudo_velho = hashlib.md5("".join(velho[q] for q in range(len(velho))).encode()).hexdigest()

    print("assinatura com o linha_tempo de ANTES: %s" % tudo_velho)
    print("assinatura com o linha_tempo de AGORA: %s" % tudo_novo)
    print("a que esta escrita no teste:           %s" % testes.ASSINATURA_CORPO_SINTETICO)
    print()
    mudam = sorted(q for q in novo if novo[q] != velho.get(q))
    print("fotogramas: %d ao todo, %d mudaram" % (len(novo), len(mudam)))
    if mudam:
        print("  do %d ao %d" % (mudam[0], mudam[-1]))
    # QUE CLIPS ESTAO NO ECRA EM CADA FOTOGRAMA QUE MUDOU
    tipos = {}
    for q in mudam:
        t = estado["desvio"] + q / render.FPS
        for c in estado["resto"]:
            if float(c["inicio_s"]) - 0.001 <= t < float(c["fim_s"]):
                tipos.setdefault(c["tipo"], set()).add(c["ordem"])
    print("  tipos de clip no ecra nesses fotogramas:",
          {k: sorted(v) for k, v in tipos.items()})
    iguais = [q for q in novo if novo[q] == velho.get(q)]
    print("  fotogramas iguais: %d" % len(iguais))


main()
