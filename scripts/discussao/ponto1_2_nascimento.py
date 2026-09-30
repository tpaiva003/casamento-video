# -*- coding: utf-8 -*-
"""Previa dos pontos 1 e 2 (decisoes 092 e 093): o nascimento do Tiago ou da Clara, hoje contra o
futuro, desenhado pelo proprio render e com o som dele. Nao muda nada; escreve em
saida/discussao/ponto1_tiago/ ou ponto2_clara/.

    py -3.11 scripts/discussao/ponto1_2_nascimento.py Tiago
    py -3.11 scripts/discussao/ponto1_2_nascimento.py Clara [--so-futuro] [--so-dizer]
(--so-dizer: so diz onde encontrou a fita, os foguetes e a foto, sem desenhar nada)

O FUTURO, como ficou decidido:
- na fita, so o marco grande do nascimento muda: a frase em Arial Bold 66 na cor quente e a data a
  58 px (os outros marcos ficam iguais); a frase e a que o Tiago escreveu na Mesa;
- no ultimo segundo dos foguetes a fita escurece e o nome ("O TIAGO", "A CLARA") nasce no preto com o
  letreiro quente; 1,6 s depois a foto sobe por tras e o nome apaga-se;
- a foto do Tiago deixa de levar a legenda; a da Clara fica com a dela (093);
- a musica do bebe entra com o nome, no ultimo segundo dos foguetes; a do Tiago (Rei Leao) sem rampa
  (092); a da Clara (Ana Faria) ja entra ai e o som nao muda (093);
- o resto do filme anda o que o nome acrescenta (uns 0,2 s).
Tudo se encontra pela data na fita, por isso a previa sai certa mesmo que a ordem do filme mude.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as C                     # noqa: E402
from comum import render, linha_tempo  # noqa: E402
from PIL import Image                  # noqa: E402

EXTRA = 1.6          # segundos entre o nome nascer e a foto comecar a subir
POR_QUEM = {
    "Tiago": {"nome": "O TIAGO", "musica": "O Rei Le", "sem_rampa": True, "legenda_fica": False,
              "pasta": "ponto1_tiago"},
    "Clara": {"nome": "A CLARA", "musica": "Ana Faria", "sem_rampa": False, "legenda_fica": True,
              "pasta": "ponto2_clara"},
}


def som_do_futuro(est, N, E_nome, E_foto, desloca, cfg, t0, t1, saida):
    """O som com a musica do bebe a entrar no nome e o resto do filme a andar desloca segundos."""
    ent = C.entradas_de_som(est)
    bebe = [e for e in C.leitos(ent) if e["ficheiro"].startswith(cfg["musica"])
            and N["foguetes"]["quando"] <= e["quando"] <= E_foto + 1.0]
    if len(bebe) != 1:
        raise SystemExit("Nao encontrei uma so '%s' a comecar entre os foguetes e a foto." % cfg["musica"])
    bebe = bebe[0]
    for e in ent:
        if e is bebe:
            continue
        if e["quando"] >= E_foto - 0.05:
            e["quando"] += desloca
        elif e["quando"] + e["dura"] > E_foto and not C.e_efeito(e):
            e["dura"] += desloca          # os foguetes nao esticam: tocavam mais do troco dos foguetes
        # as janelas em que a musica baixa por baixo de uma voz ou de um video andam com o resto
        if e.get("abafar"):
            e["abafar"] = [(a + desloca, b + desloca, f) if a >= E_foto - 0.05 else (a, b, f)
                           for a, b, f in e["abafar"]]
    fim = bebe["quando"] + bebe["dura"] + desloca
    if abs(bebe["quando"] - E_nome) > 0.05:
        print("  %s passa de %.2f para %.2f (o ultimo segundo dos foguetes)"
              % (bebe["ficheiro"][:30], bebe["quando"], E_nome))
    bebe["quando"], bebe["dura"] = E_nome, fim - E_nome
    if cfg["sem_rampa"]:
        bebe["subida"] = 0.03
    return C.som_do_troco(C.CONSTRUIR_FUTURO, ent, t0, t1, saida)


def main():
    quem = sys.argv[1] if len(sys.argv) > 1 else ""
    if quem not in POR_QUEM:
        raise SystemExit("uso: ponto1_2_nascimento.py Tiago|Clara [--so-futuro] [--so-dizer]")
    cfg = POR_QUEM[quem]
    so_futuro = "--so-futuro" in sys.argv
    pasta = C.pasta(cfg["pasta"])

    hoje_est, fut_est = C.carregar(), C.carregar()
    N = C.nascimento(fut_est, quem)
    fog = N["foguetes"]
    fita, foto = N["fita"], dict(N["foto"])
    legenda = (N["foto"].get("texto_ecra") or "")
    if not cfg["legenda_fica"]:
        # a legenda sai; num grupo de fotos saem tambem os textos de cada foto
        for c in (foto, N["foto"]):
            c["texto_ecra"] = ""
            if c.get("textos_fotos"):
                c["textos_fotos"] = ""
    E_foto = N["ini_foto"]
    fim_fog = fog["quando"] + fog["dura"] - fog.get("cruza", 0.0)
    E_nome = fim_fog - 1.0                                # o ultimo segundo dos foguetes
    desloca = E_nome + EXTRA - E_foto                     # o que o resto do filme anda
    ini_fita, dur_fita = N["ini_fita"], float(fita["duracao_s"])
    if not (ini_fita <= E_nome <= ini_fita + dur_fita) or desloca < -0.05:
        raise SystemExit("As contas do nascimento de %s nao batem: o nome nasceria aos %.2f s, a fita vai dos "
                         "%.2f aos %.2f s e a foto andaria %+.2f s. A previa so serve quando os foguetes acabam "
                         "durante a fita e a foto vem logo a seguir."
                         % (quem, E_nome, ini_fita, ini_fita + dur_fita, desloca))
    t0, t1 = fog["quando"] - 6.0, E_foto + 10.0
    videos = [c for c in fut_est["resto"] if c.get("tipo") == "video"
              and float(c["inicio_s"]) - fut_est["desvio"] < t1 + desloca
              and float(c["fim_s"]) - fut_est["desvio"] > t0]
    if videos:
        raise SystemExit("Ha um video no corpo dentro da janela da previa (clip %s): o render so o desenha a "
                         "partir da cache que o processo principal dele enche, e esta previa nao a tem."
                         % ", ".join(str(c.get("ordem")) for c in videos))
    ate_foto = max(0.7, float(foto.get("transicao_s") or 0.0))   # a foto desenha-se sozinha enquanto encadeia
    print("%s: fita aos %.2f, o marco acende aos %.2f, foguetes %.2f a %.2f, foto hoje aos %.2f; no futuro o "
          "nome aos %.2f e a foto aos %.2f (%+.2f s)" % (quem, ini_fita, N["acende"], fog["quando"], fim_fog,
                                                     E_foto, E_nome, E_nome + EXTRA, desloca), flush=True)
    print("  a seguir a fita: %s %s, com a legenda %r, que no futuro %s" % (
        N["foto"].get("tipo"), N["foto"].get("ficheiro"), legenda[:50], "fica" if cfg["legenda_fica"] else "sai"))
    if "--so-dizer" in sys.argv:
        return

    meses_hoje = linha_tempo.meses
    meses_fut = C.meses_do_futuro()
    p_fita = render.preparar(fita, fut_est["inv_por_nome"])
    p_foto = render.preparar(foto, fut_est["inv_por_nome"])
    dur_foto = float(foto["duracao_s"])
    nome = C.letreiro([cfg["nome"]])
    preto = Image.new("RGB", (C.L, C.A), (0, 0, 0))

    def hoje(t):
        linha_tempo.meses = meses_hoje
        return render.fotograma(int(round(t * C.FPS)), hoje_est)[0]

    def futuro(t):
        linha_tempo.meses = meses_fut
        if t < E_nome:
            return render.fotograma(int(round(t * C.FPS)), fut_est)[0]
        dt = t - E_nome
        if dt < 0.7:
            fundo = Image.blend(render.desenhar(p_fita, t - ini_fita, dur_fita), preto, C.suave(dt / 0.7))
        elif dt < EXTRA:
            fundo = preto
        else:
            u = dt - EXTRA
            f = (render.desenhar(p_foto, u, dur_foto) if u < ate_foto
                 else render.fotograma(int(round((t - desloca) * C.FPS)), fut_est)[0])
            fundo = Image.blend(preto, f, C.suave(u / 1.0)) if u < 1.0 else f
        alfa = C.suave(dt / 0.9) if dt < EXTRA + 0.4 else 1.0 - C.suave((dt - EXTRA - 0.4) / 0.6)
        if alfa <= 0.001:
            return fundo
        return C.ecra(fundo, C.pousar(nome, 1.0 + 0.025 * dt), alfa)

    som_hoje = C.som_do_troco(C.CONSTRUIR_HOJE, C.entradas_de_som(hoje_est), t0, t1,
                              os.path.join(pasta, "som_hoje.m4a"))
    som_fut = som_do_futuro(fut_est, N, E_nome, E_foto, desloca, cfg, t0, t1 + desloca,
                            os.path.join(pasta, "som_futuro.m4a"))
    tarefas = [("futuro.mp4", futuro, t1 - t0 + desloca, som_fut)]
    if not so_futuro:
        tarefas.insert(0, ("hoje.mp4", hoje, t1 - t0, som_hoje))
    feitos = []
    for nome_f, desenho, dura, som in tarefas:
        saida = os.path.join(pasta, nome_f)
        enc = C.encoder(saida, dura, som)
        for k in range(int(round(dura * C.FPS))):
            enc.stdin.write(desenho(t0 + k / C.FPS).convert("RGB").tobytes())
        enc.stdin.close()
        enc.wait()
        feitos.append(saida)
        print("escrito", saida, flush=True)
    linha_tempo.meses = meses_hoje
    if len(feitos) == 2:
        print("escrito", C.juntar_videos(feitos, os.path.join(pasta, "hoje_e_futuro.mp4")))


if __name__ == "__main__":
    main()
