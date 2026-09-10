#!/usr/bin/env bash
# Corrida da noite. Espera que o que esta a correr acabe, trata TODAS as fotos
# elegiveis com Real-ESRGAN, e no fim mede se cada uma melhorou ou piorou.
#
# Nada e substituido. Os originais ficam intactos em trabalho\ e as versoes
# tratadas vao para upscaled-ia\. A escolha de qual usar faz-se depois, foto a
# foto, com os numeros da verificacao a frente. E por isso que tratar tudo e
# seguro mesmo havendo casos em que o modelo piora a imagem.
set -u
cd /c/casamento-video

esperar() {
  while true; do
    n=$(tasklist 2>/dev/null | grep -ci "python.exe" || true)
    ativo=$(powershell.exe -NoProfile -Command "
      (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" |
       Where-Object { \$_.CommandLine -match 'upscale_ia|verificar_upscale' } |
       Measure-Object).Count" 2>/dev/null | tr -d '\r ')
    [ "${ativo:-0}" = "0" ] && break
    py -3.11 -c "import time; time.sleep(30)"
  done
}

echo "== a aguardar que os trabalhos em curso terminem =="
esperar

echo
echo "== upscaling de todas as fotos elegiveis =="
py -3.11 scripts/upscale_ia.py --min 0

echo
echo "== verificacao: melhorou ou piorou, foto a foto =="
py -3.11 scripts/verificar_upscale.py --recortes 30

echo
echo "== fim da corrida da noite =="
