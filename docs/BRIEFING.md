# BRIEFING: vídeo do casamento

Este ficheiro é a fonte de contexto deste repositório. Lê-o por inteiro no
início de cada sessão, juntamente com `CLAUDE.md` e `DECISOES.md`.

---

## 1. O que é isto

Reconstrução do vídeo do casamento de Clara e Tiago, a 4 de outubro de 2026,
na Quinta Pedras Salgadas, em Vila Nova de Gaia, para cerca de 140 convidados.

A mãe da Clara fez um vídeo de 22 minutos em Windows Movie Maker. O trabalho
dela é o ponto de partida e é para ser respeitado, não substituído. O objetivo
não é refazer do zero, é reordenar, aparar e dar-lhe a voz do casal.

Esta distinção não é sentimentalismo, é uma instrução de trabalho: sempre que
houver dúvida entre inventar e preservar, preserva, e pergunta.

---

## 2. Quem é quem

- **Tiago**: com quem estás a falar. Toma as decisões finais.
- **Clara**: a noiva. Vota nas escolhas de fotos. As colunas de voto no CSV
  refletem isso.
- **Mãe da Clara**: autora do vídeo original. Não participa na edição, mas o
  trabalho dela é a base.

Clara e Tiago conheceram-se na Escola Secundária de Valongo, em 2009/2010, e
ficaram juntos a 20 de maio de 2012.

---

## 3. Audiência e tom

A audiência é mista: família, amigos próximos e colegas de trabalho.

O registo é caloroso mas não íntimo. O filtro prático é este: se um colega
conservador repetisse aquilo ao café na segunda-feira, o Tiago sentir-se-ia
desconfortável? Se sim, não entra.

Aplica este filtro a qualquer texto que proponhas para o ecrã.

---

## 4. Condições de exibição

O vídeo passa **durante o jantar**, num bloco único de cerca de **15 minutos
(900 segundos)**.

Metade da sala estará de costas para o ecrã, com talheres e conversa. Isso
impõe restrições que não são estéticas, são funcionais:

- Planos fechados. Uma foto de grupo tirada de longe não se lê a 15 metros.
  Se uma foto importante estiver distante, corta e aproxima.
- Texto grande, poucas palavras, alto contraste. Branco sobre escuro.
- Nenhuma narração falada. A acústica mata a palavra. A música carrega tudo.
- Fim inequívoco, com fade a preto, para as pessoas saberem que podem aplaudir
  e o serviço retomar.

---

## 5. Estrutura narrativa acordada

O problema do vídeo original é estrutural: mostra a Clara do início ao fim,
depois o Tiago, depois viagens separadas com muitas fotos seguidas, depois
momentos soltos sem ordem. Falta narrativa.

A estrutura nova é um funil com abertura em flash-forward:

| # | Bloco | Alvo (s) | Conteúdo |
|---|-------|----------|----------|
| 0 | Abertura | 45 | Flash-forward. Eles agora, a casa, o pedido, sem explicação. Termina com um cartão e corte seco para uma foto de bebé. |
| 1 | Primeiros anos | 150 | 0 aos 6. Intercalado apertado: Clara bebé, Tiago bebé, Clara 3 anos, Tiago 3 anos. Uma ou duas fotos por idade. |
| 2 | Infância | 160 | 7 aos 12. Intercalado a alargar, blocos de 20 a 30 segundos por pessoa. |
| 3 | Adolescência | 160 | 13 aos 18. Mesmo ritmo. Termina em Valongo. |
| 4 | O encontro | 130 | 2009 a 2012. As duas linhas juntam-se. A partir daqui acaba a alternância. Muda a música. É o momento estrutural do vídeo. |
| 5 | A dois | 220 | 2012 a 2026. Fluxo único e cronológico até à casa e ao pedido. |
| 6 | Fecho | 35 | Volta a uma imagem da abertura, agora com contexto. Fade a preto. |

Total: 900 segundos.

A estrutura muda de andamento três vezes por dentro, e é isso que permite
aguentar 15 minutos sem cansar.

---

## 6. Regras fixas de edição

- **Máximo de 4 ou 5 fotos seguidas do mesmo evento ou viagem.** É esta regra
  que corta o excesso. Uma viagem representada por três fotos boas vale mais
  do que quinze.
- **Nunca menos de 3 segundos por foto.** Padrão 4. Fecho de bloco até 6.
- **Não forçar paridade entre Clara e Tiago.** A Clara tem muito material de
  infância, o Tiago tem pouco. Intercalado apertado só onde há material
  comparável. Ninguém conta fotos.
- **Texto no ecrã**: poucas palavras, datas e nomes, nunca frases.
- **Marcar `resolucao_ok = Nao`** em tudo o que precise de upscaling. A
  infância da Clara é digitalizada e vai ser projetada numa parede.
- **Música**: cada mudança de faixa tem de coincidir com uma mudança de bloco.
  Ver secção 8, é uma decisão em aberto.

---

## 7. Material de partida

Em `C:\casamento-video-media\trabalho\` existem duas pastas de topo idênticas
(mesmo tamanho, mesmo MD5 do `.wlmp`).

**Trabalha só numa. Ignora a outra. Não apagues nada.**

Por cópia:

- 305 fotos `.jpg`/`.jpeg`, em duas origens: `Originals/` (11 ficheiros) e
  `wetransfer_fotos_.../` (294 ficheiros)
- 1 `.png`
- 16 `.mp3`
- 2 `.mp4`: `Clara e Tiago-2.mp4` (896 MB, a exportação final dela) e
  `20th Century Fox   Abertura Clássic.mp4` (1 MB, clip de abertura)
- 1 `Clara e Tiago.wlmp` (817 KB), o projeto Movie Maker
- `photothumb.db`: cache do Windows, ignorar

**Avisos técnicos:**

- Extensões em maiúsculas e minúsculas misturadas (`.JPG`, `.MP3`). Filtra
  sempre sem distinguir maiúsculas.
- Ficheiros com nomes parecidos (`10-1.jpg` e `10-1 (2).jpg`, `11-3.JPG` e
  `11-3 - Cópia.JPG`) **não são necessariamente duplicados**. Fotos
  digitalizadas em lote recebem nomes sequenciais. Confirma sempre por hash
  do conteúdo antes de tratar como duplicado, e mesmo aí, apenas reporta.
- Os caminhos dentro do `.wlmp` são absolutos do computador da mãe da Clara e
  podem estar partidos. Faz correspondência por nome de ficheiro e reporta
  quantos não encontraste.

---

## 8. Decisões em aberto

Estas ainda não estão fechadas. Não assumas nem avances sem perguntar:

1. **Número de músicas.** A mãe usou 16 faixas em 22 minutos, uma mudança a
   cada minuto e meio. A proposta inicial era reduzir para 3, o que é uma
   alteração grande à intenção dela. Meio-termo em discussão: 4 ou 5. Decidir
   depois de ver o mapa musical extraído do `.wlmp`.
2. **O clip da 20th Century Fox.** Ela abriu com a fanfarra dos estúdios.
   Funciona bem como sinal de "vai começar" para 140 pessoas ao jantar.
   Decisão consciente do Tiago, não deixar cair por distração.
3. **Um bloco de vídeo dentro do vídeo.** Há 2 `.mp4`. Decidir se entram.

---

## 9. Arquitetura técnica

**Regra absoluta: media nunca entra no repositório.** Fotos, vídeos e músicas
ficam em `C:\casamento-video-media\`. O `.gitignore` já cobre isto. O que entra
no Git é: decisões, metadados, miniaturas e scripts.

Razão: o Tiago quer decidir a partir do telemóvel, via GitHub. O PC só é
preciso na ingestão inicial e na exportação final.

**Estrutura de pastas:**

```
casamento-video/
  CLAUDE.md              regras operacionais
  DECISOES.md            registo cronológico de decisões
  docs/BRIEFING.md       este ficheiro
  scripts/               código Python
  data/
    original_mae.csv     timeline da mãe da Clara, INTOCÁVEL
    inventario.csv       metadados de todo o media
    decisoes.csv         fonte única de verdade da edição
  proxies/               miniaturas 400px, versionadas
  saida/                 FCPXML e renders, no gitignore
```

**Esquema de `data/decisoes.csv`** (não alterar nomes nem ordem de colunas):

```
id, ordem, bloco, ficheiro, tipo, pessoa, ano, evento, duracao_s,
in_s, out_s, movimento, texto_ecra, resolucao_ok, voto_tiago,
voto_clara, nota_tiago, nota_clara, estado
```

- `tipo`: foto ou video
- `pessoa`: Clara, Tiago, Ambos, Familia, Amigos
- `in_s`/`out_s`: só para vídeos, marcam o troço usado. Vazio nas fotos.
- `duracao_s`: 4 por omissão nas fotos
- `movimento`: Nenhum, Zoom in, Zoom out, Pan E-D, Pan D-E
- `estado`: Fica se ambos votarem Fica, Corta se ambos votarem Corta,
  Discutir em qualquer outro caso, vazio se a linha estiver por preencher

**Ambiente:** Windows. Python 3.11 (`py -3.11`), Git, FFmpeg 9.0.1,
DaVinci Resolve 21.1 versão gratuita.

**Importante sobre o Resolve:** a versão gratuita bloqueia scripting externo,
mas o menu `Workspace > Scripts` não está bloqueado e um script lançado daí
recebe o objeto `resolve`. O caminho principal é gerar FCPXML e importar por
`File > Import > Timeline`. O caminho alternativo é o script pelo menu. Não é
preciso comprar a versão Studio.

O módulo de scripting do Resolve não funciona com Python 3.12 ou superior,
porque ainda importa `imp`. Usa sempre 3.11 nesse caminho.

---

## 10. Fases

**Fase 1, ingestão** (no PC, uma vez):
1. Parse do `.wlmp` para `data/original_mae.csv`
2. Inventário de todo o media para `data/inventario.csv`
3. Agrupamento por evento e sugestão de bloco
4. Miniaturas de 400px para `proxies/`
5. Geração de `data/decisoes.csv` pré-preenchido

**Fase 2, decisão** (a partir do telemóvel):
`decisoes.csv` é a fonte única de verdade. O Tiago dá instruções em linguagem
natural e tu editas o CSV. Depois de cada alteração, mostra sempre a duração
por bloco face ao alvo.

**Fase 3, montagem**:
Gerar `saida/timeline.fcpxml` com ordem, durações, pan e zoom e cartões de
texto, para importar no Resolve.

---

## 11. Como comunicar com o Tiago

- **Português europeu**, sempre.
- **Sem travessões.**
- **Raciocínio antes do resultado.** Ele quer perceber o porquê antes de ver a
  proposta final.
- **Direto.** Se algo não vai funcionar, diz. Ele corrige de forma breve e
  pontual, e espera o mesmo de volta.
- **Não reabrir decisões já fechadas.** Se ele já decidiu, executa. Se surgir
  informação nova que a invalide, di-lo explicitamente em vez de reavaliar em
  silêncio.
- **Uma pergunta de cada vez**, no fim, quando for mesmo precisa.

---

## 12. Nunca fazer

- Commitar media (fotos, vídeos, música, o MP4 de 896 MB)
- Alterar `data/original_mae.csv` depois de criado
- Apagar ficheiros na pasta de media
- Tratar nomes parecidos como duplicados sem confirmar por hash
- Assumir uma decisão da secção 8 sem perguntar
- Avançar para a fase seguinte sem confirmação explícita

---

## 13. Manutenção deste contexto

Sempre que uma decisão for tomada, acrescenta uma linha a `DECISOES.md` com a
data, a decisão e a razão. É isso que permite retomar o trabalho noutra sessão,
noutro dispositivo, sem perder o fio.
