# -*- coding: utf-8 -*-
"""Segunda fase do tirar_mascara: acertar a luz e a pele com um modelo de imagem local.

Tarefa paralela ao video (a foto "WhatsApp Image 2026-09-21 at 12.06.46", na pasta
04-Tratamento_Imagem_fora_video). O Tiago autorizou a instalacao a 22 de setembro "apenas
para usares neste projeto que disse que e fora do video". Nao se usa em nada do filme.

PORQUE: a composicao do tirar_mascara.py poe as feicoes verdadeiras (nariz, boca, barba de
outras fotos deles) no sitio das mascaras, mas com a luz e a pele de outra foto; o Tiago
viu o resultado e disse que pareciam ETs. Aqui o Stable Diffusion inpainting parte dessa
composicao (nao do zero) e refaz so dentro da zona da mascara, com uma forca (strength)
baixa o bastante para as feicoes ficarem e alta o bastante para a luz passar a ser a da
foto. Faz-se cada cara num recorte quadrado ampliado a 512 px, e so a zona da mascara,
com a borda suavizada, volta para a foto; o resto da foto nao muda um pixel.

CORRE NO AMBIENTE ISOLADO, nao no Python do video:
    "C:\\Users\\User 1\\sd_mascara\\venv\\Scripts\\python.exe" scripts\\tirar_mascara_sd.py
        --composto <png da composicao> --zonas <pasta com zona_ele.png e zona_ela.png>
        [--forcas 0.4,0.55,0.7] [--sementes 1,2] [--passos 30]
Escreve em gerados\\sem_mascara, nunca por cima de nada.
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
from PIL import Image, ImageFilter

MODELO = r"C:\Users\User 1\sd_mascara\modelo"
ORIGINAL = (r"C:\casamento-video-media\trabalho\04-Tratamento_Imagem_fora_video"
            r"\WhatsApp Image 2026-09-21 at 12.06.46.jpeg")
SAIDA = r"C:\casamento-video-media\gerados\sem_mascara"

# Recorte quadrado de cada cara (inclui os olhos, que ficam como estao: so a zona muda).
CARAS = {
    "ele": {"caixa": (491, 392, 691, 592),
            "prompt": "close-up photo of a man's face, short dark beard, trimmed mustache, "
                      "closed mouth with visible lips, natural skin, soft daylight in the shade, "
                      "realistic photograph, sharp focus",
            "negativo": "face mask, surgical mask, blue fabric, blurry, deformed, distorted, "
                        "cartoon, painting, plastic skin, open mouth, teeth"},
    "ela": {"caixa": (851, 551, 1031, 731),
            "prompt": "close-up photo of a woman's face, long dark hair, natural skin, "
                      "gentle closed-mouth smile, soft outdoor daylight, realistic photograph, "
                      "sharp focus",
            "negativo": "face mask, sequins, fabric, blurry, deformed, distorted, cartoon, "
                        "painting, plastic skin, open mouth, teeth, makeup"},
}


def novo(caminho):
    base, ext = os.path.splitext(caminho)
    k = 2
    while os.path.exists(caminho):
        caminho = "%s_%d%s" % (base, k, ext)
        k += 1
    return caminho


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--composto", required=True)
    ap.add_argument("--zonas", required=True)
    ap.add_argument("--forcas", default="0.4,0.55,0.7")
    ap.add_argument("--sementes", default="1")
    ap.add_argument("--passos", type=int, default=20)
    ap.add_argument("--so", default="")
    ap.add_argument("--prompt", default="", help="substitui o prompt da cara de --so")
    ap.add_argument("--negativo", default="", help="substitui o negativo da cara de --so")
    a = ap.parse_args()
    forcas = [float(x) for x in a.forcas.split(",")]
    if a.so and a.prompt:
        CARAS[a.so]["prompt"] = a.prompt
    if a.so and a.negativo:
        CARAS[a.so]["negativo"] = a.negativo
    sementes = [int(x) for x in a.sementes.split(",")]

    from diffusers import StableDiffusionInpaintPipeline
    torch.set_num_threads(os.cpu_count() or 4)
    t0 = time.time()
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        MODELO, variant="fp16", torch_dtype=torch.float32,
        safety_checker=None, requires_safety_checker=False)
    pipe.set_progress_bar_config(disable=True)
    # DPM++ chega ao mesmo sitio em menos passos: neste i5 cada passo custa ~28 s.
    from diffusers import DPMSolverMultistepScheduler
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config,
                                                             use_karras_sigmas=True)
    print("modelo carregado em %.0f s" % (time.time() - t0), flush=True)

    composto = Image.open(a.composto).convert("RGB")
    original = Image.open(ORIGINAL).convert("RGB")
    os.makedirs(SAIDA, exist_ok=True)
    resultados = {}
    for nome, c in CARAS.items():
        if a.so and nome != a.so:
            continue
        x0, y0, x1, y1 = c["caixa"]
        lado = x1 - x0
        zona = Image.open(os.path.join(a.zonas, "zona_%s.png" % nome)).convert("L")
        init = composto.crop(c["caixa"]).resize((512, 512), Image.LANCZOS)
        # A mascara para o modelo: a zona, um pouco alargada, para ele refazer a costura.
        m = zona.crop(c["caixa"]).filter(ImageFilter.MaxFilter(5)).resize((512, 512), Image.LANCZOS)
        m = m.point(lambda v: 255 if v > 64 else 0)
        # Para colar de volta: a zona alargada com borda macia.
        alfa = zona.crop(c["caixa"]).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
        for s in sementes:
            for f in forcas:
                t1 = time.time()
                g = torch.Generator().manual_seed(s)
                out = pipe(prompt=c["prompt"], negative_prompt=c["negativo"], image=init,
                           mask_image=m, strength=f, num_inference_steps=a.passos,
                           guidance_scale=6.5, generator=g, height=512, width=512).images[0]
                de_volta = out.resize((lado, lado), Image.LANCZOS)
                resultados[(nome, s, f)] = (de_volta, alfa)
                de_volta.save(novo(os.path.join(SAIDA, "_sd_%s_s%d_f%02d.png" % (nome, s, int(f * 100)))))
                print("%s semente %d forca %.2f: %.0f s" % (nome, s, f, time.time() - t1), flush=True)
    # Uma foto inteira por combinacao (mesma semente e forca nas duas caras).
    for s in sementes:
        for f in forcas:
            foto = original.copy()
            for nome, c in CARAS.items():
                if (nome, s, f) in resultados:
                    img, alfa = resultados[(nome, s, f)]
                    foto.paste(img, c["caixa"][:2], alfa)
            destino = novo(os.path.join(SAIDA, "sem mascara s%d f%02d.jpg" % (s, int(f * 100))))
            foto.save(destino, quality=95, subsampling=0)
            print("Escrito: %s" % destino, flush=True)


if __name__ == "__main__":
    main()
