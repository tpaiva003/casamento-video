# -*- coding: utf-8 -*-
"""Gera uma pagina HTML para preencher os anos em falta, sem precisar de Excel.

O Tiago nao tem Microsoft Office, por isso editar CSV a mao nao e opcao. Esta
pagina abre em qualquer browser, tem as fotos ja embutidas (nao depende de
caminhos nem de ligacao) e no fim grava um ficheiro pequeno que eu leio.

Mostra dois grupos:
  SEM ANO       as que nao tem ano nenhum, a prioridade
  ESTIMADO      as que tem ano estimado pela ordem da mae da Clara, para
                confirmar ou corrigir

Uso:  py -3.11 scripts/ferramenta_anos.py
"""
import base64
import csv
import html
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTARIO = os.path.join(REPO, "data", "inventario.csv")
DECISOES = os.path.join(REPO, "data", "decisoes.csv")
PROXIES = os.path.join(REPO, "proxies")
SAIDA = r"C:\casamento-video-media\ferramentas"
NASCIMENTO = 1995


def embutir(caminho):
    with open(caminho, "rb") as fh:
        return "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode("ascii")


# Cada origem de ano tem uma etiqueta propria e uma cor propria. O objetivo e
# que nunca haja duvida sobre o que e facto e o que e palpite, sobretudo
# depois de o Tiago ter dito que os anos dele sao para validar com a Clara.
ETIQUETAS = {
    "EXIF": ('<span class="et exif">data da m&aacute;quina</span>', ""),
    "legenda (ano escrito)": ('<span class="et dela">ano escrito por ela</span>', ""),
    "legenda (idade)": ('<span class="et dela">idade escrita por ela</span>', ""),
    "nome dado pelo Tiago": ('<span class="et teu">ano no nome que deste</span>', ""),
    "nome do ficheiro": ('<span class="et dela">data no nome do ficheiro</span>', ""),
    "Tiago (indicativo)":
        ('<span class="et teu">INDICADO POR TI</span>'
         '<span class="et aviso">por validar com a Clara</span>', "teu"),
    "estimado (ordem dela)":
        ('<span class="et est">ESTIMADO POR MIM</span>'
         '<span class="et aviso">pela ordem da timeline dela</span>', "est"),
}


def cartao(r, estimado=False):
    proxy = os.path.join(REPO, r["proxy"].replace("/", os.sep))
    img = embutir(proxy) if os.path.exists(proxy) else ""
    ano = html.escape(r["ano"] or "")
    legenda = html.escape(r["legenda_mae"] or r.get("_nota", "") or "")
    bloco = html.escape(r["bloco_original"] or r["pasta"])
    etiqueta, _classe = ETIQUETAS.get(r.get("fonte_ano", ""), ("", ""))
    marca = etiqueta
    if r["digitalizacao"] == "Sim":
        marca += '<span class="et scan">digitalizada</span>'
    return """
<div class="c" data-id="%s">
  <img src="%s" loading="lazy">
  <div class="m">
    <div class="id">%s &middot; %s</div>
    %s
    <div class="leg">%s</div>
    <input type="number" class="ano" min="1990" max="2026" step="1"
           placeholder="ano" value="%s">
    <div class="btns">
      <button type="button" data-a="rep">= anterior</button>
      <button type="button" data-a="mais">+1</button>
      <button type="button" data-a="menos">-1</button>
    </div>
  </div>
</div>""" % (html.escape(r["id"]), img, html.escape(r["id"]), bloco,
             marca, legenda or "<i>sem legenda</i>", ano)


PAGINA = """<!doctype html>
<meta charset="utf-8">
<title>Anos em falta</title>
<style>
:root{color-scheme:dark}
body{margin:0;background:#0e0e10;color:#e8e8ea;
  font:15px/1.5 "Segoe UI",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:#16161a;
  border-bottom:1px solid #2a2a30;padding:14px 20px;
  display:flex;gap:16px;align-items:center;flex-wrap:wrap}
h1{font-size:17px;margin:0;font-weight:600}
.cont{padding:20px;display:grid;gap:16px;
  grid-template-columns:repeat(auto-fill,minmax(290px,1fr))}
h2{grid-column:1/-1;margin:22px 0 2px;font-size:15px;color:#9aa;
  text-transform:uppercase;letter-spacing:.08em}
h2 span{color:#e8e8ea;text-transform:none;letter-spacing:0}
.c{background:#17171b;border:1px solid #26262c;border-radius:10px;
  overflow:hidden;display:flex;flex-direction:column}
.c.ok{border-color:#2f6b3f}
.c img{width:100%;height:190px;object-fit:contain;background:#000;cursor:zoom-in}
.c img.z{height:auto;max-height:82vh}
.m{padding:10px 12px 12px}
.id{font-size:11px;color:#8a8a94;margin-bottom:4px}
.leg{font-size:12.5px;color:#b9b9c2;min-height:34px;margin:6px 0 8px}
.et{display:inline-block;font-size:10px;padding:2px 7px;border-radius:20px;
  margin-right:5px}
.scan{background:#3a2d16;color:#e0b96a}
.est{background:#2a2340;color:#b3a2e8}
.teu{background:#123a2c;color:#6fd6a6;font-weight:700}
.exif{background:#1b2b3a;color:#7fb4de}
.dela{background:#2b2320;color:#d0a48a}
.aviso{background:#3d1f22;color:#f0a0a4}
.legenda-topo{padding:12px 20px;background:#141418;border-bottom:1px solid #26262c;
  display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:12px;color:#8a8a94}
input.ano{width:100%;padding:9px 10px;font-size:17px;font-weight:600;
  background:#0e0e10;color:#fff;border:1px solid #33333c;border-radius:7px;
  text-align:center}
input.ano:focus{outline:2px solid #4f7fd4;border-color:transparent}
.btns{display:flex;gap:6px;margin-top:7px}
.btns button{flex:1;padding:6px;font-size:12px;background:#22222a;color:#c9c9d2;
  border:1px solid #33333c;border-radius:6px;cursor:pointer}
.btns button:hover{background:#2c2c36}
button.p{background:#3a6ea5;color:#fff;border:0;padding:10px 18px;
  border-radius:7px;font-size:14px;font-weight:600;cursor:pointer}
button.p:hover{background:#4a7eb5}
.st{font-size:13px;color:#9aa}
.dica{padding:0 20px;color:#8a8a94;font-size:13px;max-width:900px}
</style>
<header>
  <h1>Anos em falta</h1>
  <span class="st" id="st"></span>
  <button class="p" id="grav">Gravar ficheiro</button>
</header>
<div class="legenda-topo">
  De onde vem cada ano:
  <span class="et exif">data da m&aacute;quina</span> fi&aacute;vel
  <span class="et dela">escrito por ela</span> fi&aacute;vel
  <span class="et teu">INDICADO POR TI</span> palpite teu, por validar com a Clara
  <span class="et est">ESTIMADO POR MIM</span> deduzido, o menos fi&aacute;vel de todos
</div>
<p class="dica">
Escreve o ano em que a foto foi <b>tirada</b>. Se nao souberes ao certo, um ano
aproximado vale mais do que nada, porque serve para ordenar. Deixa em branco o
que nao souberes mesmo. Clica na foto para a ver maior.
<b>Atalho:</b> com o cursor num campo, Enter salta para o seguinte e copia o
ano, que e o mais rapido quando vem uma serie do mesmo dia.
</p>
<div class="cont">{{CORPO}}</div>
<script>
const cs=[...document.querySelectorAll('.c')];
const st=document.getElementById('st');
function marcar(c){c.classList.toggle('ok',!!c.querySelector('.ano').value)}
function conta(){
  const n=cs.filter(c=>c.querySelector('.ano').value).length;
  st.textContent=n+' de '+cs.length+' preenchidas';
}
cs.forEach((c,i)=>{
  const inp=c.querySelector('.ano');
  inp.addEventListener('input',()=>{marcar(c);conta()});
  inp.addEventListener('keydown',e=>{
    if(e.key!=='Enter')return;
    e.preventDefault();
    const seg=cs[i+1]; if(!seg)return;
    const si=seg.querySelector('.ano');
    if(!si.value&&inp.value)si.value=inp.value;
    marcar(seg);conta();si.focus();si.select();
  });
  c.querySelector('img').addEventListener('click',ev=>ev.target.classList.toggle('z'));
  c.querySelectorAll('.btns button').forEach(b=>{
    b.addEventListener('click',()=>{
      const a=b.dataset.a;
      if(a==='rep'){
        for(let j=i-1;j>=0;j--){
          const v=cs[j].querySelector('.ano').value;
          if(v){inp.value=v;break}
        }
      }else if(inp.value){
        inp.value=(+inp.value)+(a==='mais'?1:-1);
      }
      marcar(c);conta();
    });
  });
  marcar(c);
});
conta();
document.getElementById('grav').addEventListener('click',()=>{
  let txt='id,ano\\n';
  cs.forEach(c=>{
    const v=c.querySelector('.ano').value.trim();
    if(v)txt+=c.dataset.id+','+v+'\\n';
  });
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([txt],{type:'text/csv'}));
  a.download='anos_preenchidos.csv';
  a.click();
});
</script>
"""


def main():
    with open(INVENTARIO, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))

    # Os anos estimados sao calculados em gerar_decisoes.py e so existem no
    # decisoes.csv. O inventario guarda apenas os anos apurados por EXIF,
    # legenda ou nome de ficheiro. Aqui juntam-se os dois.
    anos_finais = {}
    if os.path.exists(DECISOES):
        with open(DECISOES, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["ano"]:
                    anos_finais[r["id"]] = r["ano"]

    sem, teus, est = [], [], []
    for r in linhas:
        apurado = r["ano"]
        final = anos_finais.get(r["id"], "")
        r["ano"] = apurado or final
        if not apurado and final:
            r["fonte_ano"] = "estimado (ordem dela)"
        if not r["ano"]:
            sem.append(r)
        elif r["fonte_ano"] == "Tiago (indicativo)":
            teus.append(r)
        elif r["fonte_ano"] == "estimado (ordem dela)":
            est.append(r)

    def ordem(r):
        if r["usada_pela_mae"] == "Sim" and r["inicio_original_s"]:
            return (0, float(r["inicio_original_s"]))
        return (1, r["ficheiro"].lower())

    sem.sort(key=ordem)
    teus.sort(key=ordem)
    est.sort(key=ordem)

    corpo = ['<h2>Ainda sem ano <span>(%d)</span></h2>' % len(sem)]
    corpo += [cartao(r) for r in sem]
    corpo.append('<h2>Indicados por ti, por validar com a Clara '
                 '<span>(%d)</span></h2>' % len(teus))
    corpo += [cartao(r) for r in teus]
    if est:
        corpo.append('<h2>Estimados por mim, para confirmares '
                     '<span>(%d)</span></h2>' % len(est))
        corpo += [cartao(r) for r in est]

    os.makedirs(SAIDA, exist_ok=True)
    destino = os.path.join(SAIDA, "anos.html")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(PAGINA.replace("{{CORPO}}", "\n".join(corpo)))

    mb = os.path.getsize(destino) / 1048576
    print("Escrito: %s  (%.1f MB)" % (destino, mb))
    print("Ainda sem ano: %d" % len(sem))
    print("Indicados por ti (por validar com a Clara): %d" % len(teus))
    print("Estimados por mim: %d" % len(est))


if __name__ == "__main__":
    main()
