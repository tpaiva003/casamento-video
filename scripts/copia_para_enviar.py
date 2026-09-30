# -*- coding: utf-8 -*-
"""Uma copia de um render que CABE no limite do envio, por tamanho alvo e nao por tentativa.

PORQUE EXISTE (23 de setembro): o render tinha uma escada de qualidade, crf 28, 31 e 34 a
960x540, e parava na primeira que coubesse em 29 MB. Com o filme a 14:28 nenhuma das tres
coube, a escada acabou, e o render imprimiu na mesma "Telemovel: ... (31,7 MB)" como se
estivesse feito. Um ficheiro que nao cabe no envio e um ficheiro que nao serve, e o aviso
nao existia.

O QUE MUDA: em vez de adivinhar a qualidade e medir o resultado, calcula-se o debito a
partir da DURACAO e do tamanho alvo, e faz-se o encode em duas passagens, que e o modo em
que o x264 acerta no tamanho pedido. Assim cabe sempre, e o que varia e a nitidez, que e o
que pode variar numa copia de revisao.

O ALVO E 28 MB e nao 29: o envio recusa acima de 30 e o MP4 leva cabecalhos por cima do que
as duas passagens contam.

Uso:  py -3.11 scripts/copia_para_enviar.py <ficheiro.mp4>
      py -3.11 scripts/copia_para_enviar.py <ficheiro.mp4> --mb 25
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render      # noqa: E402

ALVO_MB = 28.0
AUDIO_KBPS = 96
# Abaixo disto a imagem deixa de dizer alguma coisa, e mais vale dize-lo do que entregar
# um borrao. Medido no filme de 14:28: 174 kbps a 960x540 ainda deixa ler as caras.
MINIMO_VIDEO_KBPS = 110


def duracao(pr, caminho):
    r = subprocess.run([pr, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", caminho],
                       capture_output=True, text=True)
    return float((r.stdout or "0").strip() or 0)


def main():
    entrada = sys.argv[1]
    alvo_mb = float(sys.argv[sys.argv.index("--mb") + 1]) if "--mb" in sys.argv else ALVO_MB
    if not os.path.exists(entrada):
        sys.exit("Nao encontrei %s" % entrada)
    ff = render.ffmpeg()
    pr = os.path.join(os.path.dirname(ff), "ffprobe.exe")
    dur = duracao(pr, entrada)
    if dur <= 0:
        sys.exit("Nao consegui medir a duracao de %s" % entrada)
    total_kbps = alvo_mb * 1048576 * 8 / dur / 1000.0
    video_kbps = int(total_kbps - AUDIO_KBPS)
    print("%s: %.1f s, alvo %.0f MB" % (os.path.basename(entrada), dur, alvo_mb))
    print("  debito: %d kbps de video mais %d de som" % (video_kbps, AUDIO_KBPS))
    if video_kbps < MINIMO_VIDEO_KBPS:
        print("  AVISO: %d kbps e pouco para se ver alguma coisa. Fica feito na mesma, mas "
              "para um filme deste tamanho o melhor e mandar so um troco." % video_kbps)
    saida = entrada[:-4] + "_envio.mp4"
    passlog = os.path.join(os.path.dirname(saida), "_passlog")
    escala = "scale=960:540:flags=lanczos"
    base = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", entrada, "-vf", escala,
            "-c:v", "libx264", "-preset", "medium", "-b:v", "%dk" % video_kbps,
            "-pix_fmt", "yuv420p", "-passlogfile", passlog]
    r1 = subprocess.run(base + ["-pass", "1", "-an", "-f", "mp4", os.devnull],
                        capture_output=True, text=True)
    if r1.returncode != 0:
        sys.exit("a primeira passagem falhou:\n%s" % (r1.stderr or "")[-600:])
    r2 = subprocess.run(base + ["-pass", "2", "-c:a", "aac", "-b:a", "%dk" % AUDIO_KBPS, saida],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        sys.exit("a segunda passagem falhou:\n%s" % (r2.stderr or "")[-600:])
    for resto in (passlog + "-0.log", passlog + "-0.log.mbtree"):
        if os.path.exists(resto):
            os.remove(resto)
    mb = os.path.getsize(saida) / 1048576.0
    print("  escrito: %s  (%.1f MB)" % (saida, mb))
    if mb > 30:
        sys.exit("  E MESMO ASSIM NAO CABE: %.1f MB. Nao mandes este ficheiro." % mb)


# SO CORRE QUANDO E CHAMADO PELO NOME. Sem esta guarda, importar o modulo corria o
# programa todo: o consolidar.py importa o auditar_caras para a guarda das caras e
# arrancava uma auditoria de 719 fotografias sem ninguem pedir.
if __name__ == "__main__":
    main()
