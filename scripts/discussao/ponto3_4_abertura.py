# -*- coding: utf-8 -*-
"""Previa do ponto 3.4: a passagem da intro da Marvel para o contador, hoje contra o futuro. Nao
muda nada; escreve em saida/discussao/ponto3_4/.

    py -3.11 scripts/discussao/ponto3_4_abertura.py [--so-dizer]

Faz o que o render faz, sem render: o fim da intro sai do proprio ficheiro de video (com o som dele),
cortado como o render corta a fanfarra, e o comeco do corpo e desenhado pelo render.fotograma, com o
som do comum. As duas partes colam-se sem encadeado, como no filme.

O FUTURO, como foi proposto a 28 de setembro:
- a intro acaba no ultimo fotograma com imagem (medido no ficheiro: hoje fica ~1,2 s de preto);
- sai o cartao vazio que abre o corpo, e o contador passa a ser o primeiro clip;
- o primeiro Lang Lang entra no primeiro fotograma do contador, no acorde (5,45 s do ficheiro, sem
  rampa), e a retoma marcada acompanha (comum.retoma_nova).
Os dois lados levam o que ja esta aprovado (094 e 095). Tudo se encontra pelo tipo e pelo nome: o
ultimo video do bloco inicial, o cartao vazio se o corpo abrir com ele, o primeiro contador.
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C                     # noqa: E402
from comum import render              # noqa: E402

ANTES, DEPOIS = 6.0, 8.0       # segundos da intro e do corpo que a previa mostra


def fim_da_imagem(caminho, dura):
    """O instante, no ficheiro, a seguir ao ultimo fotograma que ainda tem imagem."""
    a = max(0.0, dura - 4.0)
    r = subprocess.run([C.FF, "-v", "error", "-ss", "%.3f" % a, "-i", caminho, "-vf", "scale=96:54,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    q = np.frombuffer(r.stdout, np.uint8).reshape(-1, 54, 96).reshape(-1, 96 * 54).mean(1)
    com = [i for i in range(len(q)) if q[i] > 2]
    return min(dura, a + (com[-1] + 1) / C.FPS) if com else dura


def pedaco_da_intro(caminho, de, ate, saida):
    """O troco da intro como o render o corta (mesma escala, mesmo som), de `de` a `ate` no ficheiro."""
    subprocess.run([C.FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.3f" % de, "-t", "%.3f" % (ate - de),
                    "-i", caminho, "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1"
                    % (C.L, C.A, C.L, C.A), "-r", str(C.FPS), "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000", saida], check=True)
    return saida


def pedaco_do_corpo(est, desloca, som, saida):
    """DEPOIS segundos do corpo a partir de `desloca`, desenhados pelo render, com o som dado."""
    enc = C.encoder(saida, DEPOIS, som)
    for k in range(int(round(DEPOIS * C.FPS))):
        enc.stdin.write(render.fotograma(int(round((desloca + k / C.FPS) * C.FPS)), est)[0].convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    return saida


def cartao(rotulo, sub, futuro, saida):
    png = saida + ".png"
    C.cartao_titulo(png, "Da intro da Marvel ao contador", rotulo, sub, futuro)
    subprocess.run([C.FF, "-v", "error", "-y", "-loop", "1", "-t", "1.8", "-i", png, "-f", "lavfi", "-t", "1.8",
                    "-i", "anullsrc=r=48000:cl=stereo", "-vf", "scale=%d:%d,fps=%d,format=yuv420p" % (C.L, C.A, C.FPS),
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", saida], check=True)
    os.remove(png)
    return saida


def colar(partes, saida):
    """Uma parte a seguir a outra, sem encadeado, como o render cola a fanfarra ao corpo. Com o filtro
    concat, que descodifica cada parte sozinha: o concat de ficheiros (o do render) da AAC corrompido
    quando as partes nao tem exatamente a mesma configuracao de som, e aqui o cartao, a intro e o corpo
    vem de tres sitios diferentes."""
    entradas, filtros = [], []
    for i, p in enumerate(partes):
        entradas += ["-i", p]
        filtros.append("[%d:v]fps=%d,format=yuv420p,setsar=1[v%d];[%d:a]aresample=48000,"
                       "aformat=sample_fmts=fltp:channel_layouts=stereo[a%d]" % (i, C.FPS, i, i, i))
    filtros.append("".join("[v%d][a%d]" % (i, i) for i in range(len(partes)))
                   + "concat=n=%d:v=1:a=1[v][a]" % len(partes))
    subprocess.run([C.FF, "-hide_banner", "-loglevel", "error", "-y"] + entradas +
                   ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", saida], check=True)
    return saida


def main():
    pasta = C.pasta("ponto3_4")
    est = C.carregar()
    if not est["fanfarra"]:
        raise SystemExit("A montagem nao abre com videos: nao ha intro para ligar ao contador.")
    intro = est["fanfarra"][-1]
    caminho, arranque = render.caminho_de_video(intro.get("ficheiro") or "")
    if str(intro.get("in_s") or "").strip():
        arranque = float(intro["in_s"])
    dura = float(intro["duracao_s"])
    fim_img = fim_da_imagem(caminho, arranque + dura) - arranque
    vazio, t_cont = C.abertura_do_corpo(est)
    if not any(c.get("tipo") == "contador" for c in est["resto"]):
        raise SystemExit("Nao ha contador no corpo.")
    print("intro: %s, %.2f s, com imagem ate aos %.2f s (%.2f s de preto no fim)" % (intro.get("ficheiro"), dura, fim_img, dura - fim_img))
    print("cartao vazio a abrir o corpo: %s; o contador comeca aos %.2f s do corpo"
          % ("sim, %.1f s" % float(vazio["duracao_s"]) if vazio else "nao", t_cont))
    if "--so-dizer" in sys.argv:
        return

    # HOJE: o que esta aprovado (094, 095), sem o 3.4
    hoje, _t = C.base_aprovada(est, com_097=False)
    som_h = C.som_do_troco(C.CONSTRUIR_FUTURO, hoje, 0.0, DEPOIS, os.path.join(pasta, "_som_corpo_hoje.m4a"))
    # FUTURO: o corpo comeca no contador; o primeiro Lang Lang entra ai, no acorde, sem rampa
    fut, _t = C.base_aprovada(est)
    primeiro = next(e for e in C.leitos(fut) if e["ficheiro"].startswith("Lang Lang"))
    print("futuro: o primeiro Lang Lang entra aos %.2f s do ficheiro no inicio do contador (subida %s)"
          % (primeiro["in_s"], primeiro.get("subida")))
    som_f = C.som_do_troco(C.CONSTRUIR_FUTURO, fut, 0.0, DEPOIS, os.path.join(pasta, "_som_corpo_futuro.m4a"))

    est_f = C.carregar()
    partes_h = [cartao("HOJE", "preto no fim da intro e o cartão vazio", False, os.path.join(pasta, "_c_hoje.mp4")),
                pedaco_da_intro(caminho, arranque + dura - ANTES, arranque + dura, os.path.join(pasta, "_intro_hoje.mp4")),
                pedaco_do_corpo(est, 0.0, som_h, os.path.join(pasta, "_corpo_hoje.mp4"))]
    partes_f = [cartao("FUTURO", "o contador e o piano logo a seguir", True, os.path.join(pasta, "_c_futuro.mp4")),
                pedaco_da_intro(caminho, arranque + fim_img - ANTES, arranque + fim_img, os.path.join(pasta, "_intro_futuro.mp4")),
                pedaco_do_corpo(est_f, t_cont, som_f, os.path.join(pasta, "_corpo_futuro.mp4"))]
    print("escrito", colar(partes_h + partes_f, os.path.join(pasta, "hoje_e_futuro.mp4")))
    for p in partes_h + partes_f + [som_h, som_f]:
        os.remove(p)


if __name__ == "__main__":
    main()
