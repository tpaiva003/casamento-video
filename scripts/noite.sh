#!/usr/bin/env bash
# Corrida da noite, em duas voltas por ordem de utilidade.
#
# A primeira versao deste ficheiro mandava tratar TODAS as fotos e foi um erro
# caro: fotos ja grandes produziam saidas de 20 a 30 megapixeis, a memoria da
# maquina esgotava-se, o modelo passava a trocar para disco e cada foto demorava
# 17 minutos em vez de 90 segundos. Em quase quatro horas fez treze.
#
# Agora trata primeiro o que precisa mesmo de crescer, e so depois a margem
# para planos fechados. Nada e substituido: os originais ficam intactos em
# trabalho\ e o tratado vai para upscaled-ia\. A escolha de qual usar faz-se
# depois, foto a foto, com a verificacao a frente.
set -u
cd /c/casamento-video

echo "== volta 1: as que nao chegam para o ecra =="
py -3.11 -u scripts/upscale_ia.py --min 1.0

echo
echo "== volta 2: margem para planos fechados =="
py -3.11 -u scripts/upscale_ia.py --min 0.6

echo
echo "== verificacao: melhorou ou piorou, foto a foto =="
py -3.11 -u scripts/verificar_upscale.py --recortes 30

echo
echo "== fim =="
