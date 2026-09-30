# RASCUNHO do ponto 3: a detecao dos vales de energia (fundo 6 dB abaixo da mediana movel de 3 s) que
# se usou para achar fins de frase. Guardado a 29 de setembro; le o transicoes.json da analise antiga.
"""Candidatos a fim de frase (vales curtos de energia) perto do corte de A, e a inicio de frase perto do in de B."""
import numpy as np, json, sys, csv, os
sys.path.insert(0,'.')
from analisar import decode, SR
tr=json.load(open('transicoes.json',encoding='utf-8'))
som={r['ficheiro']:r['caminho'] for r in csv.DictReader(open(r'C:\casamento-video\data\montagens\v3.som.csv',encoding='utf-8-sig'))}
def rms_env(path,a,b,h=0.05):
    a=max(0,a); x=decode(path,SR,1,start=a,dur=b-a)
    n=int(h*SR); k=len(x)//n
    r=np.sqrt((x[:k*n].reshape(k,n)**2).mean(axis=1)+1e-12)
    db=20*np.log10(r)
    t=a+(np.arange(k)+0.5)*h
    return t,db
def vales(t,db,h=0.05):
    # mediana movel de 3 s
    w=int(3.0/h)
    med=np.array([np.median(db[max(0,i-w//2):i+w//2+1]) for i in range(len(db))])
    sm=np.convolve(db,np.ones(3)/3,mode='same')
    fundo=sm-med
    out=[]
    i=0
    while i<len(fundo):
        if fundo[i]<-6:
            j=i
            while j<len(fundo) and fundo[j]<-6: j+=1
            k=i+int(np.argmin(fundo[i:j]))
            # o recomeco: primeiro instante depois do vale que volta a menos de 3 dB da mediana
            r=j
            while r<len(fundo) and fundo[r]<-3: r+=1
            out.append((round(float(t[k]),2), round(float(fundo[k]),1), round(float(t[min(r,len(t)-1)]),2)))
            i=j
        else: i+=1
    return out
res=[]
for x in tr:
    pA=som[x['sai']]; pB=som[x['entra']]
    cA=x['A_corte']; zA=x['A_zero']
    t,db=rms_env(pA,cA-10,zA+10)
    vA=vales(t,db)
    t2,db2=rms_env(pB,x['B_in']-6,x['B_in']+10)
    vB=vales(t2,db2)
    pre=db2[(t2>=x['B_in']-0.3)&(t2<x['B_in'])]
    silencio_antes = bool(len(pre)) and float(np.max(pre))<-50
    x['A_vales']=vA; x['B_vales']=vB; x['B_silencio_antes']=silencio_antes
    print('%7.2f %s -> %s'%(x['T_corpo'],x['sai'][:18],x['entra'][:18]))
    print('    A corte %.2f zero %.2f | vales (instante, fundo dB, recomeco): %s'%(cA,zA,vA))
    print('    B in %.2f silencio antes=%s | vales: %s'%(x['B_in'],silencio_antes,vB))
json.dump(tr,open('transicoes.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
