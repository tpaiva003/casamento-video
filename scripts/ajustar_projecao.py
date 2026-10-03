# -*- coding: utf-8 -*-
"""O kit do projetor: acertar o filme pronto para a sala, sem voltar a fazer o render.

    py -3.11 scripts/ajustar_projecao.py <filme.mp4> [--gama G] [--contraste C] [--brilho B]
                                         [--saturacao S] [--margem M] [--volume V]
                                         [--amostra N [--desde T]] [--fino] [--saida <pasta>]
    py -3.11 scripts/ajustar_projecao.py --carta [--saida <pasta>]

PORQUE EXISTE. O Tiago, a 2 de outubro: "se no dia em que estiverem a testar o projetor chegarem a
conclusao que e preciso ajustar ligeiramente [...] eu gostava de ter o projeto no DaVinci ou assim,
pois acredito que fosse mais rapido". O render demora uma hora porque desenha cada fotograma; o que
um projetor costuma pedir nao precisa de desenhar nada de novo, so de mexer no filme que ja existe:

  --gama G        1 = como esta. Acima de 1 clareia os meios-tons e deixa o preto e o branco onde
                  estao: e o que se usa numa sala com luz ou num projetor fraco. 1,1 a 1,2 ja se ve.
  --contraste C   1 = como esta. Abre ou fecha a distancia entre o escuro e o claro, a volta do meio;
                  abaixo de 1 o preto tambem sobe.
  --brilho B      0 = como esta, de -0,2 a 0,2. LEVANTA TUDO, O PRETO INCLUIDO: o fade a preto do fim
                  passa a cinzento. Para clarear, a gama primeiro.
  --saturacao S   1 = como esta. Alguns projetores lavam a cor; 1,1 a 1,15 devolve-a.
  --margem M      0 = como esta, ate 10 (%). Encolhe a imagem M% e poe preto a volta, para um projetor
                  que corta as bordas. A legenda e os textos encolhem M% com ela.
  --volume V      0 = como esta, de -20 a +12 dB. Acima de 0 leva um limitador a -1 dBFS, porque o
                  filme ja chega perto dos 0 dBFS e cortaria a onda. Quem esta na mesa de som acerta o
                  volume da sala; isto so serve se o filme tiver de ficar mais alto ou mais baixo do
                  que a musica do DJ sem lhe mexerem no botao.
  --amostra N     so N segundos a partir de --desde T (segundos), para ver no projetor antes de fazer
                  o filme todo. Na amostra o som e a imagem saem pelo mesmo caminho do filme todo.
  --fino          o x264 no medium em vez do veryfast. Medido a 2 de outubro no filme de 14:21: o
                  veryfast levou 389 s e o medium 927 s; no master, com o mesmo CRF 18, os dois ficaram
                  acima dos 45 dB do render, onde a diferenca deixa de se ver. Por omissao vai o
                  veryfast, que e o que o dia do projetor pede.
  --carta         faz a carta de teste (carta_projetor.png e um .mp4 de 30 s): molduras a 1, 2, 3, 4,
                  5, 6, 8 e 10% da borda, para se ler logo quanto o projetor corta; degraus de cinzento,
                  os quase pretos e os quase brancos, para ver se o projetor os separa; a legenda do
                  filme no corpo dela; e as cores do letreiro e das peles. A carta passa pelo kit como
                  um filme: corre-se o kit sobre ela para ver o efeito de uma gama antes do filme todo.

O QUE NAO FAZ: mudar o tamanho de uma legenda ou de um cartao. O texto esta desenhado nos pixeis do
filme; aumenta-lo e voltar a desenha-lo, e isso e o render (ou a margem ao contrario, que corta).

NUNCA ESCREVE POR CIMA. O resultado fica ao lado do filme (ou na --saida), com o nome do filme e o
que mudou (..._projetor_g1.10_m3_v-2.mp4), e _2, _3... se ja existir; o ffmpeg escreve primeiro um
..._a_fazer.mp4 e so no fim se muda o nome. Recusa escrever na 00-Backup.

SEM NENHUM AJUSTE nao faz nada. So com o volume, a imagem passa sem se tocar (copia, segundos); so
com a imagem, o som passa sem se tocar.

A GAMA, O CONTRASTE E O BRILHO FAZEM-SE NA LUMA DO VIDEO, que no filme vai de 16 (preto) a 235
(branco), e nao de 0 a 255: o filtro eq do ffmpeg faz as contas de 0 a 255 e, com a gama a 1,2, o
preto subia de 16 para 25 (medido a 2 de outubro), cinzento no fade do fim. O lutyuv daqui faz a
conta dentro dos 16 a 235, por isso o preto fica preto e o branco fica branco. A saturacao abre o
croma a volta do 128.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import render        # noqa: E402

FF = render.ffmpeg()
FP = os.path.join(os.path.dirname(FF), "ffprobe.exe")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_CARTA = os.path.join(REPO, "saida", "projetor")
CRF = 18                      # o do master (ponto5_creditos.MASTER_CRF): esta passagem quase nao se ve
SOM = "192k"
LIMITE_SOM = 0.891            # -1 dBFS: o teto do limitador quando o volume sobe
# (opcao, omissao, minimo, maximo, letra no nome do ficheiro)
AJUSTES = [("gama", 1.0, 0.5, 2.0, "g"), ("contraste", 1.0, 0.5, 2.0, "c"), ("brilho", 0.0, -0.2, 0.2, "b"),
           ("saturacao", 1.0, 0.0, 2.0, "s"), ("margem", 0.0, 0.0, 10.0, "m"), ("volume", 0.0, -20.0, 12.0, "v")]


def ler_opcoes(argv):
    """{opcao: valor} so com os ajustes que diferem do "como esta". Um valor fora dos
    limites ou que nao e numero para tudo: um ajuste que caisse calado na omissao era o filme a ir
    para a sala sem a correcao que se pediu."""
    ajustes, problemas = {}, []
    for nome, omissao, baixo, alto, _letra in AJUSTES:
        chave = "--" + nome
        if chave not in argv:
            continue
        i = argv.index(chave)
        try:
            v = float(argv[i + 1].replace(",", "."))
        except (IndexError, ValueError):
            problemas.append("%s precisa de um numero" % chave)
            continue
        if not baixo <= v <= alto:
            problemas.append("%s %g esta fora de %g a %g" % (chave, v, baixo, alto))
            continue
        if abs(v - omissao) > 1e-9:
            ajustes[nome] = v
    if problemas:
        raise SystemExit("; ".join(problemas))
    return ajustes


def numero(argv, chave, omissao=None):
    if chave not in argv:
        return omissao
    try:
        return float(argv[argv.index(chave) + 1].replace(",", "."))
    except (IndexError, ValueError):
        raise SystemExit("%s precisa de um numero" % chave)


def medir(caminho):
    """{largura, altura, duracao, cor: {...}, tem_som} do ficheiro, pelo ffprobe (o primeiro video)."""
    r = subprocess.run([FP, "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,color_range,color_space,color_transfer,"
                        "color_primaries:format=duration", "-of", "json", caminho],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("Nao consegui ler %s: %s" % (caminho, (r.stderr or "").strip()[-200:]))
    dados = json.loads(r.stdout or "{}")
    fluxos = dados.get("streams") or []
    video = next((s for s in fluxos if s.get("codec_type") == "video"), None)
    if not video:
        raise SystemExit("%s nao tem imagem" % caminho)
    try:
        duracao = float((dados.get("format") or {}).get("duration") or 0.0)
    except ValueError:
        duracao = 0.0
    return {"largura": int(video["width"]), "altura": int(video["height"]), "duracao": duracao,
            "tem_som": any(s.get("codec_type") == "audio" for s in fluxos),
            "cor": {k: video[k] for k in ("color_range", "color_space", "color_transfer", "color_primaries")
                    if video.get(k) not in (None, "", "unknown")}}


def filtro_de_imagem(ajustes, largura, altura):
    """A cadeia do -vf, ou "" se a imagem fica como esta."""
    partes = []
    g, c, b = ajustes.get("gama", 1.0), ajustes.get("contraste", 1.0), ajustes.get("brilho", 0.0)
    s = ajustes.get("saturacao", 1.0)
    if g != 1.0 or c != 1.0 or b != 0.0 or s != 1.0:
        # a luma normaliza-se dentro dos 16 a 235, leva a gama, depois o contraste a volta do meio e o
        # brilho, e volta aos 16 a 235; o croma abre-se a volta do 128 (ver a nota do cimo)
        y = "val" if (g, c, b) == (1.0, 1.0, 0.0) else (
            "clip(16+219*((pow(clip((val-16)/219\\,0\\,1)\\,1/%r)-0.5)*%r+0.5+%r)\\,16\\,235)" % (g, c, b))
        uv = "val" if s == 1.0 else "clip(128+(val-128)*%r\\,16\\,240)" % s
        partes.append("lutyuv=y='%s':u='%s':v='%s'" % (y, uv, uv))
    m = ajustes.get("margem", 0.0)
    if m:
        # o par mais perto, para o yuv420p; a imagem encolhida fica ao centro, em preto
        w = int(round(largura * (1 - m / 100.0) / 2.0)) * 2
        h = int(round(altura * (1 - m / 100.0) / 2.0)) * 2
        partes.append("scale=%d:%d:flags=lanczos,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
                      % (w, h, largura, altura))
    return ",".join(partes)


def filtro_de_som(ajustes):
    v = ajustes.get("volume", 0.0)
    if not v:
        return ""
    f = "volume=%rdB" % v
    if v > 0:
        # level=0: sem ele o alimiter sobe a saida por 1/limite (a nota do render.construir_som)
        f += ",alimiter=limit=%r:level=0:attack=5:release=90:latency=1" % LIMITE_SOM
    return f


def etiqueta(ajustes):
    """O que mudou, para o nome do ficheiro: g1.10_c1.05_m3_v-2."""
    partes = []
    for nome, _omissao, _baixo, _alto, letra in AJUSTES:
        if nome in ajustes:
            v = ajustes[nome]
            if nome in ("margem", "volume"):
                texto = ("%+g" if nome == "volume" else "%g") % v
            else:
                texto = "%.2f" % v
            partes.append(letra + texto)
    return "_".join(partes)


def nome_livre(base, extensao=".mp4"):
    caminho, k = base + extensao, 2
    while os.path.exists(caminho):
        caminho = "%s_%d%s" % (base, k, extensao)
        k += 1
    return caminho


def ajustar(filme, ajustes, pasta=None, amostra=None, desde=0.0, fino=False):
    """Faz o ficheiro novo e devolve o caminho. Ver a nota do cimo."""
    if not os.path.isfile(filme):
        raise SystemExit("Nao encontro o filme %s" % filme)
    if not ajustes:
        raise SystemExit("Nenhum ajuste pedido: o filme fica como esta, e nao se escreve nada")
    info = medir(filme)
    pasta = os.path.abspath(pasta or os.path.dirname(os.path.abspath(filme)))
    if "00-backup" in pasta.lower().replace("/", "\\").split("\\"):
        raise SystemExit("Nao se escreve na 00-Backup (CLAUDE.md, regra 7)")
    if not os.path.isdir(pasta):
        raise SystemExit("A pasta %s nao existe" % pasta)
    base = os.path.join(pasta, os.path.splitext(os.path.basename(filme))[0] + "_projetor_" + etiqueta(ajustes))
    if amostra:
        base += "_amostra%gs" % amostra
    destino = nome_livre(base)
    a_fazer = nome_livre(destino[:-4] + "_a_fazer")
    vf = filtro_de_imagem(ajustes, info["largura"], info["altura"])
    af = filtro_de_som(ajustes) if info["tem_som"] else ""
    cmd = [FF, "-hide_banner", "-loglevel", "error", "-n"]
    if amostra:
        cmd += ["-ss", "%.3f" % desde, "-t", "%.3f" % amostra]
    cmd += ["-i", filme, "-map", "0:v:0"] + (["-map", "0:a:0"] if info["tem_som"] else [])
    # NA AMOSTRA NADA SE COPIA: um corte com copia so pode comecar num fotograma-chave, e a amostra
    # comecava uns segundos antes do pedido. Ela e curta, e assim sai pelo mesmo caminho do filme.
    if vf or amostra:
        cmd += (["-vf", vf] if vf else []) + [
            "-c:v", "libx264", "-crf", str(CRF), "-preset", "medium" if fino else "veryfast",
            "-pix_fmt", "yuv420p"]
        # as etiquetas de cor do filme passam para o novo, para o leitor o mostrar com as mesmas contas
        for k, opcao in (("color_range", "-color_range"), ("color_space", "-colorspace"),
                         ("color_transfer", "-color_trc"), ("color_primaries", "-color_primaries")):
            if k in info["cor"]:
                cmd += [opcao, info["cor"][k]]
    else:
        cmd += ["-c:v", "copy"]
    if info["tem_som"]:
        if af or amostra:
            cmd += (["-af", af] if af else []) + ["-c:a", "aac", "-b:a", SOM, "-ar", "48000", "-ac", "2"]
        else:
            cmd += ["-c:a", "copy"]
    cmd += ["-movflags", "+faststart", a_fazer]
    print("filme: %s (%dx%d, %.1f s)" % (filme, info["largura"], info["altura"], info.get("duracao", 0)))
    print("ajustes: %s%s" % (", ".join("%s %g" % (k, v) for k, v in ajustes.items()),
                             (" | amostra de %g s desde %g s" % (amostra, desde)) if amostra else ""))
    print("imagem: %s; som: %s" % ("refeita (CRF %d, %s)" % (CRF, "medium" if fino else "veryfast") if (vf or amostra)
                                   else "copiada, sem se tocar",
                                   "refeito" if (af or amostra) else "copiado, sem se tocar"))
    t0 = time.time()
    r = subprocess.run(cmd)
    if r.returncode != 0 or not os.path.exists(a_fazer):
        raise SystemExit("O ffmpeg parou (%d); o que ficou a meio esta em %s" % (r.returncode, a_fazer))
    os.rename(a_fazer, destino)          # no Windows o rename recusa um destino que ja exista
    print("PRONTO: %s (%.0f MB, em %.0f s)" % (destino, os.path.getsize(destino) / 1048576.0, time.time() - t0))
    return destino


# ---------------------------------------------------------------------------------------- a carta
def carta(pasta=None):
    """A carta de teste do projetor, em PNG e num MP4 de 30 s com som mudo. Ver a nota do cimo."""
    from PIL import Image, ImageDraw, ImageFont
    pasta = os.path.abspath(pasta or PASTA_CARTA)
    os.makedirs(pasta, exist_ok=True)
    L, A = render.L, render.A
    im = Image.new("RGB", (L, A), (0, 0, 0))
    d = ImageDraw.Draw(im)
    f_marca = ImageFont.truetype(render.FONTE_TEXTO, 30)
    f_titulo = ImageFont.truetype(render.FONTE_TEXTO, 58)
    # AS MOLDURAS: o que o projetor cortar le-se pela primeira que se ve inteira. As linhas estao a
    # 11 e 19 px umas das outras, menos do que a altura de um numero, por isso cada numero vai numa
    # caixa preta encostada a sua linha, em escada: os de cima dizem o corte de cima, os da esquerda
    # o da esquerda (o de baixo e o da direita veem-se pelas linhas)
    molduras = (1, 2, 3, 4, 5, 6, 8, 10)
    for k, pct in enumerate(molduras):
        mx, my = int(round(L * pct / 100.0)), int(round(A * pct / 100.0))
        cor = (255, 255, 255) if k % 2 == 0 else (255, 214, 0)
        d.rectangle((mx, my, L - 1 - mx, A - 1 - my), outline=cor, width=2)
    for k, pct in enumerate(molduras):
        mx, my = int(round(L * pct / 100.0)), int(round(A * pct / 100.0))
        cor = (255, 255, 255) if k % 2 == 0 else (255, 214, 0)
        texto = "%d%%" % pct
        w = int(f_marca.getlength(texto)) + 12
        x = 330 + k * 175
        d.rectangle((x, my + 2, x + w, my + 38), fill=(0, 0, 0))
        d.text((x + 6, my + 5), texto, font=f_marca, fill=cor)
        y = 300 + k * 60
        d.rectangle((mx + 2, y, mx + 2 + w, y + 36), fill=(0, 0, 0))
        d.text((mx + 8, y + 3), texto, font=f_marca, fill=cor)
    d.rectangle((0, 0, L - 1, A - 1), outline=(255, 0, 0), width=1)       # a borda do ficheiro, a vermelho
    d.text((L // 2, 205), "CARTA DO PROJETOR", font=f_titulo, fill=(255, 255, 255), anchor="mm")
    # OS DEGRAUS: onze do preto ao branco, e os quase pretos e quase brancos, que um projetor mal
    # acertado junta num so
    x0, larg, y = 300, 1320, 290
    passo = larg // 11
    for i in range(11):
        v = int(round(255 * i / 10.0))
        d.rectangle((x0 + i * passo, y, x0 + (i + 1) * passo - 1, y + 110), fill=(v, v, v))
        d.text((x0 + i * passo + passo // 2, y + 130), "%d%%" % (i * 10), font=f_marca, fill=(200, 200, 200),
               anchor="mm")
    y = 470
    for i, v in enumerate((0, 4, 8, 12, 16, 20)):
        d.rectangle((x0 + i * 110, y, x0 + i * 110 + 105, y + 90), fill=(v, v, v))
        d.text((x0 + i * 110 + 52, y + 110), str(v), font=f_marca, fill=(200, 200, 200), anchor="mm")
    for i, v in enumerate((235, 240, 245, 250, 255)):
        x = x0 + larg - (5 - i) * 110
        d.rectangle((x, y, x + 105, y + 90), fill=(v, v, v))
        d.text((x + 52, y + 110), str(v), font=f_marca, fill=(200, 200, 200), anchor="mm")
    # AS CORES: o champanhe do letreiro, peles clara e morena, e as primarias
    y = 650
    cores = [(render.LETREIRO_QUENTE, "letreiro"), (render.LETREIRO_BRANCO, "claro"), ((233, 190, 160), "pele"),
             ((160, 110, 80), "pele"), ((200, 30, 30), ""), ((30, 160, 60), ""), ((40, 70, 200), "")]
    for i, (cor, nome) in enumerate(cores):
        d.rectangle((x0 + i * 190, y, x0 + i * 190 + 180, y + 90), fill=tuple(cor))
        if nome:
            d.text((x0 + i * 190 + 90, y + 110), nome, font=f_marca, fill=(200, 200, 200), anchor="mm")
    # A LEGENDA DO FILME, no corpo e na faixa dela, para ver a 15 m se se le
    cor, mascara = render.faixa_texto("A legenda do filme, no tamanho dela")
    im.paste(cor, (0, 0), mascara)
    png = nome_livre(os.path.join(pasta, "carta_projetor"), ".png")
    im.save(png)
    mp4 = nome_livre(os.path.join(pasta, "carta_projetor"), ".mp4")
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-n", "-loop", "1", "-framerate", str(render.FPS),
                    "-i", png, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "30",
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", str(CRF), "-preset", "medium",
                    "-tune", "stillimage", "-c:a", "aac", "-b:a", SOM, "-shortest", "-movflags", "+faststart", mp4],
                   check=True)
    print("carta: %s e %s" % (png, mp4))
    return png, mp4


COM_VALOR = {"--" + a[0] for a in AJUSTES} | {"--amostra", "--desde", "--saida"}
SEM_VALOR = {"--fino", "--carta"}


def main():
    argv = sys.argv[1:]
    livres, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in COM_VALOR:
            i += 2
            continue
        if a.startswith("--") and a not in SEM_VALOR:
            raise SystemExit("Nao conheco a opcao %s\n%s" % (a, __doc__))
        if not a.startswith("--"):
            livres.append(a)
        i += 1
    pasta = argv[argv.index("--saida") + 1] if "--saida" in argv else None
    if "--carta" in argv:
        carta(pasta)
        return
    if len(livres) != 1:
        raise SystemExit(__doc__)
    ajustes = ler_opcoes(argv)
    amostra = numero(argv, "--amostra")
    if amostra is not None and amostra <= 0:
        raise SystemExit("--amostra precisa de segundos acima de 0")
    ajustar(livres[0], ajustes, pasta, amostra, numero(argv, "--desde", 0.0) or 0.0, "--fino" in argv)


if __name__ == "__main__":
    main()
