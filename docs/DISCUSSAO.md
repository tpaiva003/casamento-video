# A discussão dos cinco pontos

Estado, conversas e plano de construção da fase de discussão aberta a 28 de setembro de 2026.
Serve para retomar noutra sessão sem perder nada: voltar a fazer as prévias (mesmo depois de o Tiago
mudar a ordem do filme), recolher o que ele disser e, no fim, construir.

As decisões fechadas estão no `DECISOES.md` (092 em diante). Este ficheiro não as substitui: junta,
ponto a ponto, o que ele pediu, o que se decidiu, o que ele foi dizendo, como se refaz a prévia e o
que falta construir.

---

## O pedido, e as regras desta fase

A 28 de setembro, com três vídeos de referência dos Downloads dele (o título do Oppenheimer, "10
Cinematic Fonts" e "Film End Credits, 35 Cinematic Templates"):

> *"Não quero para fazer render. Vou partilhar aqui umas ideias ou dúvidas (...) sobre como poderemos
> fazer a transição da Intro da Marvel para a Intro do contador. Bem como podemos fechar."*
> 1. *"Quando temos o Contador a chegar a 12 de Setembro diz 'Nasce o Tiago', não me parece que
>    funcione bem, pois eu quero dizer na primeira foto que aparece da criança 'O Tiago'."*
> 2. *"Não gosto muito daquele cartão que fala de 2 meses de 12 dias (...) temos de repensar como fazer
>    aqui também."*
> 3. *"Não acho que as transições das músicas estejam ótimas, nota-se cortes e arranques de outras."*
> 4. *"Não gosto assim muito dos separadores que vou metendo pretos e com a letra branca, está
>    básico, um pouco amador."*
> 5. *"Não tenho ainda pensado o final do vídeo, gostava que tivesse movimento, que parecesse um filme
>    de Hollywood (...) Neste fim também posso meter como créditos todas as fotos de família (...) que
>    não consegui incluir."*

E depois: *"Vamos decidir cada ponto um de cada vez. Dá-me sempre uma preview de como está hoje e
como ficaria no futuro e explica em poucas palavras o benefício da alteração."*

**Regras desta fase:**
- **Sem render.** As prévias são feitas pelas funções do render, em memória, sem mudar o render, a
  montagem nem a Mesa.
- **Um ponto de cada vez.** Cada ponto leva uma prévia de hoje contra futuro e o benefício em poucas
  palavras, e só se passa ao seguinte quando ele fecha o anterior.
- **A construção vem no fim.** Só se constrói depois de os cinco pontos estarem fechados (ver
  "Construção", no fim).
- **Na Mesa não se escreve nada sem ele pedir.** As duas frases da fita foram escritas porque ele pediu
  (093). Os números da 095 escrevem-se na construção, como lhe foi dito antes de ele aprovar.
- **Para ouvir no telemóvel,** cada prévia de som vai num vídeo curto: primeiro o cartão HOJE com o
  som de hoje, depois o cartão FUTURO com o som do futuro. Quando são várias, vão também juntas num só
  vídeo: no 3.2 os sete já tinham seguido em separado, ele escreveu *"Precisava de ouvir"* (a mensagem
  ficou cortada) e mandou-se também um só vídeo, por iniciativa minha. Foi com esse que aprovou.

---

## Como retomar

1. Ler este ficheiro e o `DECISOES.md` a partir da 087. Da 087 à 091 está o mecanismo onde os
   nascimentos novos têm de encaixar: a fita parada até os foguetes acabarem, o eco da marca e o
   reconhecimento pela data.
2. Ver na tabela de estado qual é o ponto aberto.
3. **Se ele mexeu na Mesa**, refazer a montagem antes das prévias.
   - **A Mesa:** https://claude.ai/code/artifact/149b085c-b9db-48ac-8775-464616041be0, documento
     `montagem/estado2`.
   - **A base destas prévias:** a versão 904 (rev 904, 205 clips), escrita a 29 de setembro depois de
     a Clara pedir para tirar o pedido (099). Se a versão lida for maior do que 904, ele mexeu.
   - **O caminho de sempre:** ler o `montagem/estado2` para `saida/leitura_mesaN/`, e depois correr
     `py -3.11 scripts/juntar_mesa.py saida/leitura_mesaN/montagem/estado2.json` e
     `py -3.11 scripts/montar_da_mesa.py demo_v3 --nome v3`.

   O juntar escreve o `data/mesa_estado.json`, que é o que o montar lê. As prévias leem o
   `data/montagens/v3.csv` e o `v3.som.csv`.
4. Correr a prévia do ponto. Todas escrevem em `saida/discussao/<ponto>/`, que não entra no Git:

   | Ponto | Comando | Sai |
   |---|---|---|
   | 1 | `py -3.11 scripts/discussao/ponto1_2_nascimento.py Tiago` | `ponto1_tiago/hoje_e_futuro.mp4` |
   | 2 | `py -3.11 scripts/discussao/ponto1_2_nascimento.py Clara` | `ponto2_clara/hoje_e_futuro.mp4` |
   | 3.1 | `py -3.11 scripts/discussao/ponto3_1_regra.py` | `ponto3_1/ponto3_1_todas.mp4` |
   | 3.2 | `py -3.11 scripts/discussao/ponto3_2_entradas.py` | `ponto3_2/ponto3_2_todas.mp4` |
   | 3.3 | `py -3.11 scripts/discussao/ponto3_3_frases.py` | `ponto3_3/ponto3_3_todas.mp4` |
   | 3.4 | `py -3.11 scripts/discussao/ponto3_4_abertura.py` | `ponto3_4/hoje_e_futuro.mp4` |
   | 4 | `py -3.11 scripts/discussao/ponto4_separadores.py [texto ...]` | `ponto4/ponto4_todos.mp4` |
   | 5 | por escrever (ver o ponto) | |

5. Mandar-lhe o vídeo com o `SendUserFile`, com o benefício em poucas palavras e uma pergunta no fim.
6. **Registar o que ele disser** na secção do ponto, em "O que ele disse", com a data e as palavras
   dele. Quando fechar, acrescentar uma decisão ao `DECISOES.md` e mudar a tabela de estado.

**As prévias encontram tudo pelo nome, e é por isso que sobrevivem a uma mudança de ordem:**
- as músicas, pelo início do nome do ficheiro;
- o nascimento, pelo marco grande na data (12/09 e 24/11) ou com o nome, como o `montar_da_mesa.py`
  (decisão 088);
- a foto do bebé, por ser o clip logo a seguir a essa fita. Pode ser uma foto ou um grupo de fotos. Se
  for outra coisa (um cartão, por exemplo), a prévia pára e diz o que lá está;
- os foguetes, pelo instante em que o marco acende, com a mesma conta do montar;
- as marcas da 095, pela música e pelo ponto de entrada;
- as trocas do 3.3, pelas duas músicas e pelo segundo do ficheiro em que a música que sai chega ao
  corte.

Nunca se procura pelo número do clip nem pelo segundo do corpo. Quando uma coisa não se encontra, o
script pára e diz o que procurou, em vez de mostrar outra no lugar dela. O código comum está em
`scripts/discussao/comum.py`.

**Provado a 29 de setembro, numa cópia da montagem.** Na cópia, o bloco das Viagens passou para antes
do cartão dos penteados, e o cartão "Mas como é que chegámos aqui?" ficou 2 s mais longo. A cópia foi
montada com o `montar_da_mesa.py` para `saida/discussao/_prova_ordem/`. As prévias encontraram tudo
nos sítios novos:
- os dois nascimentos, 2 s mais tarde;
- a Fome de Viagem, que passou dos 473,82 s para os 248,42 s;
- a troca Clair para Who Let The Dogs Out, que passou dos 269,12 s para os 288,62 s;
- as outras marcas e trocas.

A Mesa, o `data/mesa_estado.json` e o `data/montagens` não foram tocados.

**Para experimentar uma prévia noutra montagem** sem tocar na verdadeira, há três variáveis de
ambiente:
- `DISCUSSAO_MONTAGEM`: o nome da montagem;
- `DISCUSSAO_MONTAGENS`: a pasta onde ela está;
- `DISCUSSAO_SAIDA`: para onde vão as prévias.

`--so-dizer` na prévia dos nascimentos só diz onde encontrou a fita, os foguetes e a foto, sem
desenhar nada: é a verificação rápida depois de ele mexer na ordem. Se duas músicas deixarem de se
seguir, a prévia do 3.1 avisa e salta essa troca.

**Depois de construído (30 de setembro), o HOJE das prévias dos pontos 3.3 e 4 já é o filme
construído.** A do 3.3 passou a ser a revisão da 096: lê o `data/fins_de_frase.csv` e compara com a
montagem (`--so-dizer`). A do 4 mostraria o construído contra o construído.

**Depois de um ponto estar construído, a prévia dele pára de propósito.** O remendo em memória já não
encaixa no render, e a mensagem diz isso. Nessa altura o render já faz o futuro sozinho, e a prévia
deixa de fazer falta. O remendo da 094 só se faz quando uma prévia o usa, por isso construir a 094 não
pára as prévias que não precisam dele.

**O render nunca importa o `comum.py`.** O `comum.py` muda de pasta, mexe no caminho dos módulos e
remenda o render. Na construção, o que for preciso de lá, como o letreiro, copia-se para o render.

---

## A abertura mudou a 29 de setembro (decisão 099)

A Clara pediu para tirar o pedido do início. A abertura passa a ser a intro da Marvel, um só
contador "2026>1995|4 de outubro de 2026" e a fita de 1995. Saem o contador do pedido, as três fotos
do pedido (com a marca da Mariah) e o cartão "Mas como é que chegámos aqui?" (com a retoma marcada do
Lang Lang). Feito na Mesa a pedido dele, na rev 904: a montagem tem agora 205 clips e o filme 789 s.
**A base das prévias passa a ser a versão 904.** A página publicada da Mesa ainda mostra o som da
publicação anterior, até à próxima publicação.

**O que muda nos pontos:**
- **3.2:** a linha da retoma marcada deixa de ter onde se aplicar.
- **3.3:** as trocas "Lang Lang para Mariah" e "Mariah para a retoma" desaparecem. A "Rei Leão para o
  Lang Lang automático" muda, porque o Lang Lang passa a voltar noutro sítio do ficheiro. Depois da
  mudança na Mesa, montar e correr o `ponto3_3_frases.py`, e medir outra vez o que ele disser.
- **3.4:** continua (097), agora para o contador único.
- **5:** o filme fica cerca de 40 s mais curto. Com os créditos fica perto dos 860 s.

## Estado

**A 30 de setembro construiu-se tudo o que estava fechado (decisão 100).** As prévias dos pontos
construídos ficam como registo: o remendo da 094 já não é preciso, porque o `comum.py` usa o render
construído. A ferramenta de medida das trocas (`medir_troca.py`) continua a servir para a revisão da
096. O render final espera pelos créditos e pela pergunta dos textos marcados (082).

| Ponto | O quê | Estado | Decisão |
|---|---|---|---|
| 1 | O nascimento do Tiago | construído (100) | 092 |
| 2 | O nascimento da Clara, e o cartão dos "2 meses e 12 dias" | construído (100) | 093 |
| 3.1 | A regra geral de subida e descida das músicas | construído (100) | 094 |
| 3.2 | Os pontos de entrada de sete músicas | construído, escrito na Mesa (100) | 095 |
| 3.3 | A música que sai acaba no fim da frase | construído (100); rever antes do render final | 096 |
| 3.4 | A passagem da intro da Marvel para o contador | construído, intro nova na Mesa (100) | 097 |
| 4 | Os separadores | construído (100) | 098 |
| 5 | O fim e os créditos | à espera das fotos e da lista de convidados dele | |

**O que ele já recebeu e ainda não decidiu:**
- **3.3,** a 28 de setembro: "agora contra proposta" em três trocas (O corpo é que paga para Fome de
  Viagem, Clair para Who Let The Dogs Out, e Ana Faria para Clair). Eram feitas com a análise antiga, e
  as prévias novas substituem-nas.
- **3.4,** a 28 de setembro: o excerto de como está hoje (`0_agora_intro_marvel_para_contador`).
- **4,** a 28 de setembro: as imagens paradas e um vídeo de 3,6 s do cartão "O trabalho" a mexer,
  ainda com grão de filme. O grão saiu depois da proposta.

---

## 1. O nascimento do Tiago (decisão 092, fechado)

**O que ficou decidido:**
- **Na fita, só o marco grande do nascimento muda.** A frase passa a Arial Bold 66 na cor quente
  (236,204,168), e a data passa a 58 px (de 40), na mesma cor e 18 px mais abaixo. Os outros marcos
  ficam iguais ao byte.
- **O texto da frase é dele,** "Nasce o 2º filho da Graça e do Alberto", nas três partes da fita.
- **"O TIAGO" nasce no preto** no último segundo dos foguetes, com o letreiro quente. A foto sobe por
  trás 1,6 s depois, e o nome apaga-se. A foto deixa de levar a legenda.
- **O Rei Leão entra com o nome,** a cruzar com os foguetes e sem rampa.

**O que ele disse, por ordem:**
- *"Gosto do futuro, mas na fita gostaria do texto tipo 'Nasce o 2º filho da Graça e do Alberto'."*
- *"A frase está com as letras muito grandes e gordas. A música do Rei Leão deve começar com as
  letras do Tiago a aparecer e não antes."* Mostraram-se então quatro letras.
- *"Há um segundinho de pausa entre os foguetes e a música do Rei Leão."* Na mesma mensagem escolheu
  a letra C.
- *"Agora trocaste todos os textos que passam no timeline. Pensava que íamos alterar apenas o 'Nasce
  o 2º filho' e o '12 de setembro'."* A primeira versão da C mudava a cor de todos os marcos, e isso
  foi corrigido.
- *"Sim fechamos."*

**Construção:**
- `linha_tempo.meses`: nos marcos grandes, letra 66, cor quente, e data a 58 em `y_linha + 82`. São
  exatamente as quatro trocas do `comum.meses_do_futuro()`.
- **O nome no preto.** É preciso uma peça nova, no `montar_da_mesa.py` e no render, que o desenhe
  no último segundo dos foguetes. A letra é a do `comum.letreiro()`, copiada para o render, que é
  também a proposta para os separadores do ponto 4.
- **Tem de encaixar no mecanismo das 089 e 091.** Hoje a fita fica parada no meio da paragem do
  nascimento (o `~segundos@instante` no CSV) até os foguetes acabarem. No futuro, a fita escurece nos
  últimos 0,7 s, dentro do último segundo dos foguetes, e o nome nasce aí.
- **A foto entra 1,6 s depois do nome.** No filme de 28 de setembro, isso punha-a 0,2 s mais tarde
  do que hoje. Tem de ficar dentro dos 3 s do eco (`MARCA_ECO_S`): a marca do Rei Leão na foto só é
  absorvida se a foto entrar a menos de 3 s da música automática.
- **O Rei Leão continua a entrar no último segundo dos foguetes,** como hoje (73,87 s no filme de 28 de
  setembro). Muda só a subida, de 1 s para 0,03 s, e isso vem sozinho da 094, porque a entrada no zero
  conta como início.
- **Fica um pendente da 091 para ver com o nome no preto.** Se houver outra música marcada na primeira
  foto do bebé, a automática toca 1,4 s antes dela e cruza.
- **A legenda da foto é texto dele.** Antes de a tirar, confirmar se é ele que a apaga na Mesa ou se
  sou eu, a pedido dele.
- **A Mesa tem de acompanhar.** O `som_para_mesa.py` (o instante e a duração no `SOM_RENDER`) e, se
  for preciso, o `editor_base.html` (o `duracaoNoRender`), para a Mesa não mostrar os instantes 0,2 s
  desviados.
- **Testes:**
  - os marcos que não são de nascimento continuam iguais ao byte;
  - a data do nascimento tem pelo menos 58 px;
  - a foto do bebé entra 1,6 s depois de o nome nascer;
  - o Rei Leão sobe em 0,03 s.

---

## 2. O nascimento da Clara (decisão 093, fechado)

**O que ficou decidido:**
- **Tudo o que a 092 diz do Tiago vale para a Clara.** A frase dele é "Nasce a 1ª filha de Rosa e
  Jorge", e "A CLARA" nasce no preto.
- **O marco do Côa fica como está.** Está no mesmo dia que o nascimento, e a coincidência lê-se
  sozinha.
- **A legenda dele na primeira foto fica.** Não é o anúncio do nascimento.
- **O som não muda.** A Ana Faria já entra no último segundo dos foguetes.
- **O cartão dos "2 meses e 12 dias" já não está na montagem.** Verificado a 29 de setembro, não
  há nenhum clip com esse texto no `v3.csv`.

**O que ele disse:** *"Troca a frase no timeline para Nasce a 1ª filha de Rosa e Jorge. De resto sim
aprovo."* As duas frases foram escritas na Mesa nesse dia (rev 903).

**Construção:** a mesma da 092. A diferença é que a legenda da foto fica e a Ana Faria não muda. A
Ana Faria entra a meio (aos 6,0 s do ficheiro) sem cruzar com nenhuma música. Pela 094 fica com a
subida de hoje e só ganha a curva `qsin`; é isso que mantém o "o som não muda". Leva um teste.

---

## 3. A música

Dividido em quatro partes, decididas uma a uma.

### 3.1 A regra geral de subida e descida (decisão 094, fechado)

**O que ficou decidido:**
- **A que entra num início entra sem rampa (0,03 s).** Conta como início um ponto de entrada no zero,
  ou quase silêncio nos 0,4 s antes da entrada e som logo a seguir.
- **A que entra a meio e cruza com uma música que sai sobe em 2,2 s,** o mesmo tempo que a outra leva
  a descer.
- **A que entra a meio sem cruzar fica com a subida de hoje,** só com a curva nova. São a Ana Faria
  depois dos foguetes e o primeiro Lang Lang, no zero do corpo.
- **As curvas passam a ser de potência igual** (`qsin`).
- **Os foguetes, o rebobinar, as vozes e o som dos vídeos ficam como estão.**

**O acrescento da 095:** uma entrada posta num ataque (a voz ou a primeira batida) conta como início.

**O que ele disse:** *"sim avança"*.

**Construção** (`render.construir_som`):
- **Cada faixa pode trazer a sua subida, a sua descida e a curva.** São as trocas do
  `comum.CONSTRUIR_FUTURO`.
- **A conta de quem sobe como** passa para o render ou para o `montar_da_mesa.py`. É o que o
  `comum.aplicar_094()` faz.
- **Como o render sabe que uma entrada está num ataque: tem de vir da marca da Mesa.** A medida da 094
  (silêncio antes e som depois) não reconhece nenhum dos quatro ataques da 095: a Fome de Viagem (2,7),
  o Já Sei Namorar (34,9), o Celebration (0,81) e o Born To Be Wild (0,55) dão todos "a meio". Medido a
  29 de setembro. A indicação na marca é campo novo na Mesa, a acrescentar na construção.
- **Testes:**
  - subida curta num início;
  - subida igual à descida num cruzamento;
  - `curve=qsin` no comando;
  - as vozes sem mudança.

### 3.2 Os pontos de entrada (decisão 095, fechado)

**O que ficou decidido:**

| Música | Entrava | Entra | Num ataque |
|---|---|---|---|
| Fome de Viagem | 0 s | 2,7 s | sim |
| Já Sei Namorar | 31,16 s | 34,9 s | sim |
| Lang Lang, a retoma marcada | 13,3 s | onde o primeiro parou (14,6 s hoje) | não |
| Tiago Celebration | 0 s | 0,81 s | sim |
| Taking Care of Business | 62 s | 60,8 s | não |
| Born To Be Wild | 0 s | 0,55 s | sim |
| Filhos do Dragão | 4 s | 7 s | não |

**O que ele disse:**
- *"Precisava de ouvir."* A mensagem ficou cortada. Os sete já tinham seguido em separado, e
  mandou-se também um só vídeo com os sete seguidos, por iniciativa minha.
- *"Aprovo todas."*

**Construção:**
- **Os sete números vão para as marcas dele na Mesa,** escritos por mim. Segue-se o procedimento de
  escrita do `CLAUDE.md`:
  - ler o `estado2`;
  - escrever com `if_version`, com `rev` a subir um e com o `quando` da hora da escrita;
  - nunca escrever enquanto se publica.
- **O Lang Lang toca três vezes, e há duas retomas.**
  - **A retoma marcada** é a dele, no cartão "Mas como é que chegámos aqui?". A 095 põe-na onde o
    primeiro Lang Lang parou. É uma regra, e não um número: a entrada do primeiro, mais o que ele toca
    até à música seguinte (hoje 5,0 + 9,6 = 14,6 s).
  - **A retoma automática** é a da fita antes da Clara. O montar calcula-a a partir da marcada (hoje
    13,3 + 29,5 = 42,8 s) e passa sozinha a 44,1 s quando a marcada mudar.
- **A retoma marcada anda com o 3.4.** Tirar o cartão vazio e pôr o piano no primeiro fotograma do
  contador também encurta o primeiro Lang Lang, de 9,6 para cerca de 8,3 s. Com a entrada a 5,45 s, a
  retoma fica em cerca de 13,75 s, e não nos 15,05 que a 095 dizia (esse número estava errado,
  corrigido a 29 de setembro). O `comum.retoma_nova()` faz a conta.
- **Na marca da Mesa pode estar um número diferente do que se ouve.** O `montar_da_mesa.py` salta o
  silêncio do início de uma música marcada (abaixo de -45 dB, pelo menos 0,3 s). O Já Sei Namorar,
  por exemplo, está marcado aos 30 s e toca a partir dos 31,16 s. Os números da tabela são os que se
  ouvem, lidos do `v3.som.csv`. Depois de os escrever nas marcas e montar, confirmar no `v3.som.csv`
  que as sete entradas saem com estes valores.

**Prévia:** no futuro entram as sete de uma vez, e é essa a versão real. Por isso, em três trocas (Já
Sei Namorar, Born To Be Wild e Filhos do Dragão), a música que sai também já está no ponto novo. A
retoma automática anda com a marcada, como no montar.

### 3.3 A música que sai acaba no fim da frase (decisão 096, fechado)

**O problema:** a música que sai começa a descer no corte, esteja onde estiver. Em 11 das 14 trocas
medidas a 28 de setembro, apanha uma frase a meio. Ele disse só *"nota-se cortes e arranques de
outras"*. Os piores casos, medidos por mim:
- **Clair para Who Let The Dogs Out:** a Clair é cortada a meio do verso.
- **Ana Faria para Clair:** ouvem-se duas vozes a cantar ao mesmo tempo.
- **Rei Leão para a retoma do Lang Lang,** e **Queen para Taking Care of Business.**

**O que fica como está:** o fim da Mariah foi posto num fim de frase de 8 compassos (70,27 s do
ficheiro, decisão 079), e o 3.3 não o desfaz.

**Uma ideia que é dele decidir.** O grito do Who Let The Dogs Out resultava melhor a responder à
pergunta do cartão "Um deles sofre de uma patologia grave por animais. Adivinham...". Para isso, a
música teria de mudar uns segundos depois do cartão. Isso vai contra a regra "cada mudança de faixa
coincide com mudança de bloco".

**A análise de 29 de setembro:**
- **O que se analisou:** 14 trocas, já com a 094 e a 095. Ficaram de fora as duas dos foguetes (092 e
  093) e o fim da última música, que é do ponto 5.
- **Como:** para cada troca, um agente mediu a música que sai: batidas, compassos, a energia da banda
  da voz, os vales e as fronteiras de frase. Depois comparou cinco soluções e mediu cada uma com o som
  refeito. Um segundo agente, independente, tentou refutar a proposta.
- **As cinco soluções:**
  - sair antes do corte, num fim de frase;
  - mudar a entrada da música que sai, para o fim de frase cair no corte;
  - deixá-la acabar a frase por cima do separador;
  - mudar o corte de sítio;
  - não mexer.
- **Onde está o trabalho:** tudo o que os agentes devolveram está em
  `data/discussao/ponto3_3_analise.json`, que diz também, para cada troca, em que segundo do
  ficheiro estava a música que sai no instante do corte. Os workflows foram o `wf_ca7737f0-f7b` e o
  `wf_c4fa5210-3a8`, este para repetir três trocas. As medidas de cada agente ficaram na pasta
  temporária desta sessão,
  `C:\Users\User 1\AppData\Local\Temp\claude\C--casamento-video\1b92fe8a-9bb1-4c48-abf6-9956af511886\scratchpad\ideias\p33`.
  Pode desaparecer. A lista das trocas (`trocas.py`) e a ferramenta de medida (`mix33.py`) foram
  copiadas para `scripts/discussao/rascunhos/`. Para medir outra vez uma troca, é com esse `mix33.py`,
  que faz o mesmo que o `comum.py`, com as mods da troca.
- **Prévia:** `py -3.11 scripts/discussao/ponto3_3_frases.py`. Os dois lados levam a 094 e a 095, e o
  futuro acrescenta só o fim de frase.

**O que se encontrou nas 14 trocas:**

| Troca | Hoje | Futuro | Confiança |
|---|---|---|---|
| Lang Lang para Mariah | o piano é cortado a meio do motivo e fica 1,2 s por baixo da primeira linha da Mariah | acaba na resolução do motivo e cala-se antes da nota seguinte; buraco de 0,8 s, no limite | média |
| Mariah para a retoma marcada | a Mariah começa uma linha nova no cartão e ouve-se 1,7 s por cima do piano | acaba a linha 0,67 s antes do cartão e cala-se em 0,5 s; o piano sobe em 0,5 s | média |
| Rei Leão para o Lang Lang | ouve-se 1 s do coro a começar outra linha por baixo do piano | sai dentro do respiro que fecha o período; o piano sobe em 0,3 s (medido outra vez a 30/09; era 1 s) | alta |
| Ana Faria para Clair | duas canções a cantar ao mesmo tempo | a Ana Faria acaba a frase e a Clair começa limpa com o cartão | alta |
| Clair para Who Let The Dogs Out | 1,85 s de duas vozes | a Clair acaba a linha; o grito entra sozinho depois de 0,3 s de respiração | alta |
| Who Let The Dogs Out para Tokyo Drift | ouve-se o arranque de um verso novo, cortado | o refrão acaba no fim do compasso, 0,8 s depois do corte | alta |
| Tokyo Drift para Tiago Celebration | 1,5 s de Tokyo por cima da introdução calma do reggae | o Tokyo acaba o compasso antes do corte | alta |
| Tiago Celebration para O corpo é que paga | uma linha nova começa e morre por cima do arranque | acaba com a frase; pausa de 0,3 a 0,5 s antes do cartão | alta |
| O corpo é que paga para Fome de Viagem | desce a meio da linha | toca a linha inteira até 1,1 s depois do corte e sai na pausa da voz | alta |
| Fome de Viagem para Já Sei Namorar | 1,4 s de duas vozes | acaba a linha 0,3 s antes da foto; a voz dos Tribalistas entra sozinha | média |
| Já Sei Namorar para Born To Be Wild | a linha seguinte começa por baixo do riff | acaba a nota longa e cala-se na pausa | média |
| Born To Be Wild para Filhos do Dragão | começa um bocado novo no corte e ouve-se 1,2 s por cima do hino | acaba no vale curto 0,27 s antes do corte; respira 0,2 s; o hino sobe em 0,3 s | baixa |
| Filhos do Dragão para Queen | ouve-se o arranque cortado da linha seguinte | a linha acaba inteira, 0,9 s depois do corte | média |
| Queen para Taking Care of Business | o corte já cai no fim de uma linha, mas a descida de 2,2 s deixa ouvir a linha seguinte por cima | a Queen cala-se em 0,5 s a partir do corte; o Taking Care of Business sobe em 0,5 s | média |

**Três trocas tiveram de ser repetidas,** porque o filtro de conteúdo bloqueou a primeira resposta,
provavelmente por causa das letras. Na repetição, os agentes estavam proibidos de escrever palavras
das letras. A do Born To Be Wild para Filhos do Dragão voltou a ser bloqueada. Foi medida por mim, só
com números e sem verificador independente, por isso a confiança é baixa: numa guitarra rock, a banda
da voz engana.

**O que as 14 têm em comum:**
- Nenhuma precisou de mudar uma entrada, nem de mudar o corte de sítio.
- A música que sai acaba num fim de frase entre 1,3 s antes e 1,1 s depois do corte.
- A cauda vai de 0,12 a 1,0 s, em vez dos 2,2 s de hoje.

**Uma regra que saiu das medidas e que acerta a 094: quando a música que sai desce depressa, a que
entra também sobe depressa.** A 094 diz que a que entra a meio sobe no mesmo tempo em que a outra
desce, e esse tempo era sempre 2,2 s. Com a descida curta do 3.3, uma subida de 2,2 s abre uma quebra
de volume de meio segundo a um segundo, medida em três trocas. Por isso, quando a música que sai acaba
no corte ou antes dele, a que entra sobe no tempo da cauda dela:
- na retoma marcada do Lang Lang, 0,5 s;
- no Filhos do Dragão, 0,3 s;
- no Taking Care of Business, 0,5 s.

Quando a música que sai prolonga a frase por cima do corte, a que entra fica com a subida dela.

**Aprovado com a 096, embora mexa no que já estava aprovado:**
- **As três subidas curtas.** A 095 tinha a retoma, o Taking Care of Business e os Filhos do Dragão a
  entrar a meio, com 2,2 s. As entradas não mudam, só a subida.
- **A Mariah deixa de descer no cartão.** A 079 diz que no cartão "Mas como é que chegámos aqui?" a
  Mariah desce em 2,2 s. Passa a acabar a linha 0,67 s antes do cartão. O cartão não sai do sítio.

**O que ele disse** (29 de setembro, depois de ouvir as 14 trocas num só vídeo): *"Sim, aprovo, mas
não te esqueças que este fluxo terá de ser revisto antes de fazer o render final ou com novas fotos e
assim."*

**A revisão que ele pediu:**
1. **Antes do render final, e sempre que a montagem mudar** (fotos novas, outra ordem, outras
   durações, outra entrada), corre-se `py -3.11 scripts/discussao/ponto3_3_frases.py`. As trocas em
   que a música chega ao corte noutro sítio aparecem como "MEDIR OUTRA VEZ".
2. **Essas medem-se outra vez** pelo mesmo método: um agente analisa e outro verifica. A ferramenta é
   o `py -3.11 scripts/discussao/medir_troca.py <sai> <entra> ...`, que encontra a troca pelos nomes e
   já leva tudo o que está aprovado. A análise musical está em
   `scripts/discussao/rascunhos/ponto3_analisar.py`, e as batidas e fronteiras de cada música em
   `data/discussao/musicas_batidas.json`. Na medida, não se escreve nenhuma palavra das letras, senão o
   filtro bloqueia a resposta.
3. **O resultado vai para o `data/discussao/ponto3_3_analise.json`,** e a prévia mostra-se ao Tiago
   antes do render.
4. **Na construção, o `montar_da_mesa.py` passa a avisar** quando uma troca com fim de frase chega ao
   corte noutro sítio do ficheiro, e diz qual (avisa, nunca corrige, 083).

**O que ele disse depois do render de ensaio** (30 de setembro, `v3_2026-09-30_0206`): *"Não adorei
as separações que há nas músicas agora, mas isso não é para resolver agora."* Fica em aberto, para
voltar a ele. Antes, perguntar-lhe em que trocas o sentiu mais, e se é o silêncio curto entre as duas
músicas (o respiro) ou a descida rápida da que sai.

**Os números em vigor** estão em `data/fins_de_frase.csv`, que é o que a montagem e o render usam, e
o que a revisão lê. A tabela da 096 é a de 29 de setembro. A 30 mudaram duas trocas: o Rei Leão para o
Lang Lang e a Ana Faria para a Clair (decisão 100).

**A 1 de outubro, com a revisão 966 da Mesa** (186 clips, 19 a menos do que no render de 30 de
setembro), seis das doze trocas chegam ao corte noutro sítio e descem no corte, como antes da 096:
- Rei Leão para Lang Lang;
- Ana Faria para Clair;
- Tokyo Drift para Tiago Celebration;
- Tiago Celebration para António Variações;
- Já Sei Namorar para Steppenwolf;
- Queen para Taking Care of Business.

O render de ensaio de 1 de outubro saiu assim. Medem-se outra vez antes do render final, ou quando ele
der a ordem por fechada; medir agora era trabalho perdido se ele ainda mexer.

**Duas coisas a dizer-lhe:**
- **A primeira troca depende do 3.4.** Se o primeiro Lang Lang passar a entrar aos 5,45 s, o buraco
  passa para 1,25 s e a proposta deixa de servir. Tem de ser medida outra vez.
- **A ideia dele do grito também foi medida.** O Who Let The Dogs Out passava a entrar na primeira foto
  do bloco dos cães, 3,8 s depois do cartão. Isso vai contra a regra dos blocos e obriga a medir outra
  vez a troca seguinte. A proposta dentro da regra já tira as duas vozes.

**Para sobreviver a uma mudança de ordem:**
- **Um fim de frase é um sítio da música.** Se ele mudar a ordem ou as durações, a música chega ao corte
  noutro sítio, e o fim de frase certo passa a ser outro.
- **Cada troca guarda em que segundo do ficheiro estava a música no corte.** A prévia do 3.3 compara-o
  com a montagem de hoje e, se mudou, diz "medir outra vez" e salta essa troca.
- **A construção precisa, no render, de uma descida por faixa** (o `sai_s` e a cauda, como faz o
  `comum.acabar_na_frase()`).
- **Os números de cada troca vêm da análise.** Numa troca que mudou, mede-se só essa, com o mesmo
  método: um agente analisa e outro verifica.
- **Pode valer a pena guardar mais de um fim de frase por música,** em
  `data/discussao/musicas_frases.json`, para a escolha ser automática. Decide-se na construção.

### 3.4 A passagem da intro da Marvel para o contador (decisão 097, fechado)

**O que se passa hoje:**
- o som da intro fica quase calado cerca de 3 s antes de o piano entrar;
- a intro acaba com 1,2 s de preto;
- vem depois um cartão vazio de 2 s.

A sala fica cerca de 5 s sem nada.

**Proposta:**
- **Cortar o preto do fim da intro,** depois de confirmar os últimos fotogramas. A intro passa de
  14,44 para cerca de 13,2 s.
- **Tirar o cartão vazio.** Atenção, isto reabre uma decisão fechada:
  - o cartão vazio é a pequena pausa que ele pediu na 079 (*"a Intro estilo marvel, uma pequena pausa
    depois o rebobinar até ao pedido"*);
  - a 27 de setembro disse que não queria mexer ainda no cartão.

  Dizer-lho assim, com a prévia do buraco de hoje (cerca de 5 s) contra o de depois (cerca de 1,5 s).
- **Pôr o primeiro acorde do Lang Lang no primeiro fotograma do contador.** A entrada do primeiro
  Lang Lang é automática, e não uma marca da Mesa: é a constante `LANG_LANG_IN = 5.0` do
  `montar_da_mesa.py`. Passa para 5,45 s. É um acorde, por isso conta como ataque e sobe em 0,03 s.
  A retoma marcada passa para cerca de 13,75 s (ver 3.2).

Com isto o buraco desce para cerca de 1,5 s, que é só o letreiro a escurecer. **A primeira troca do
3.3 (Lang Lang para Mariah) tem de ser medida outra vez**, porque com a entrada a 5,45 o buraco dela
passa para 1,25 s.

**Construção, se ele aprovar:**
1. Confirmar os últimos fotogramas e cortar a intro para cerca de 13,2 s num ficheiro de nome novo. O
   filme usa a cópia `intro_clara_tiago_5 igualado.mp4` de `gerados/som_igualado/`, e o
   `intro_flipbook.py` recusa escrever por cima.
2. Passá-la pelo `scripts/igualar_abertura.py`, com ganho direto e nunca loudnorm (084).
3. Trocar o ficheiro do clip de vídeo na Mesa. É uma escrita que ele tem de autorizar, feita por ele ou
   por mim, com o procedimento de escrita.
4. Confirmar o aviso de duração do `montar_da_mesa.py`. A duração é medida pelo ffprobe, nunca
   escrita à mão.
5. `LANG_LANG_IN` para 5,45, com o teste da retoma a acompanhar.

**Prévia:** `py -3.11 scripts/discussao/ponto3_4_abertura.py`, sem render. Mostra os últimos 6 s da
intro, cortados do próprio ficheiro como o render corta a fanfarra, e os primeiros 8 s do corpo
desenhados pelo `render.fotograma`. Cola as duas partes sem encadeado, como no filme. `--so-dizer`
só diz onde está o preto e o cartão.

**Medido na prévia de 29 de setembro:**

| | Hoje | Futuro |
|---|---|---|
| Ecrã quase preto | 2,8 s (1,24 s de preto da intro, e o cartão vazio até o contador acender) | 0,8 s (o letreiro a escurecer e o contador a acender) |
| Som abaixo de -40 dB | 3,6 s, com 1 s de silêncio total | 2,2 s, que é a própria intro a desvanecer |
| Duração do filme | | 2,5 s mais curto |

**O que ele disse** (29 de setembro, depois da prévia): *"Gostei da opção do futuro."* A pergunta
dizia-lhe que a pausa da 079 fica com cerca de 2 s em vez de 3,6.

**Consequência:** a primeira troca do 3.3 (Lang Lang para Mariah) mede-se outra vez com a abertura
nova. O piano chega ao anel aos 13,75 s do ficheiro, e não aos 14,6.

---

## 4. Os separadores (decisão 098, fechado)

**Porque parecem amadores:**
- a letra branca está apertada;
- o fundo é preto chapado;
- o cartão não mexe. Estão marcados com zoom, mas o render desenha-os parados.

**Proposta,** a partir do título do filme Oppenheimer (e não do fogo por dentro da letra, que o
tutorial faz):
- **Letra:** Arial Bold em maiúsculas bem espaçadas. A regra das letras (084) mantém-se.
- **Cor e brilho:** champanhe quente em vez de branco, com um brilho quente fraco. **Isto mexe numa
  regra do `CLAUDE.md`**, "alto contraste, branco sobre escuro". O contraste baixa de 15,2:1 para
  13,3:1, medido a 28 de setembro. É decisão dele, e se aprovar atualiza-se o `CLAUDE.md`.
- **Movimento:** aproxima-se devagar, 2,5 % por segundo. As letras entram a partir do preto em 0,6 s
  e dissolvem-se na foto seguinte no encadeado de saída, como hoje.
  - *Corrigido a 29 de setembro:* a proposta de 28 dizia que as letras se apagavam meio segundo antes
    da foto seguinte. Medido na prévia, isso tirava 0,4 s de leitura a todos os cartões: 1,8 s de
    letras inteiras contra 2,2 s hoje. As frases já são as que passam depressa de mais (082), por isso
    fica sem esse meio segundo. Com as letras até ao encadeado, ficam inteiras 2,3 s. A de 28 vê-se com
    `--apaga-antes`.
- **O espaçamento largo só nos textos de 1 a 3 palavras.** Na montagem da rev 903 há 14 cartões:
  - 6 curtos: Carro, Gosto pelo desporto, Viagens, Com os amigos, O trabalho e A faculdade;
  - 7 frases;
  - o cartão vazio.

  As frases, como "Mas como é que chegámos aqui?", mantêm as minúsculas e o corpo 78 de hoje. Levam só
  a cor, o brilho e o movimento. A prévia conta as palavras na montagem do momento, e não nesta lista.
- **Os textos são dele** e não se lhes toca.
- **Sem grão de filme:** o ficheiro fica 6 vezes maior, e a 15 m não se vê.
- **O custo no render:** uns 30 s.

**A mesma letra** é a dos nomes dos bebés (092), por isso os dois pontos ficam coerentes.

**O que ele disse** (29 de setembro, depois de ver os 13 cartões): *"Sim, aprovo com o champanhe."* A
regra "branco sobre escuro" do `CLAUDE.md` ficou atualizada.

**Rascunho:** `scripts/discussao/rascunhos/ponto4_letreiro_experiencia.py`. Compara o cartão de hoje
com o letreiro novo, mede a legibilidade a 15 m e o custo.

**Prévia:** `py -3.11 scripts/discussao/ponto4_separadores.py`. Mostra todos os cartões com texto, ou só
os que contêm os textos dados. Cada um aparece no sítio dele do filme, com a foto de antes, a de depois
e o som, primeiro HOJE e depois FUTURO. O desenho é o do `render.fotograma`, e em memória troca-se só
o desenho do cartão. Os curtos e as frases separam-se pelo número de palavras na montagem do momento.
`--so-dizer` lista os cartões e o tempo de leitura.

**Antes de fechar as letras dos pontos 4 e 5, falta saber a largura da tela.** É pergunta para o DJ ou
para a quinta, e estava na lista de adiados de 27 de setembro. As medidas de leitura a 15 m usaram
telas de 2, 2,5 e 3 m.

---

## 5. O fim e os créditos (proposta, maquetes paradas)

**O que ele disse** (30 de setembro): *"Eu marco as fotos que entram depois para o ponto 5. Os nomes
eu posso partilhar uma lista de todos os convidados confirmados. Quero colocar cargos curtos e
engraçados, por exemplo a Mãe da Clara foi quem teve a maior parte do trabalho a montar a ideia, os
textos etc. Eu tive a responsabilidade de dar conteúdo e estrutura ao esboço da Mãe da Clara e a
Clara foi tipo a validadora final. Quero que isto fique também claro e visível com um tom engraçado
para o fecho."*

**Por fazer no ponto 5, com o que ele mandar:**
- as fotos, marcadas por ele;
- a lista de convidados, de onde saem os nomes (os nomes são dele, nunca identificados por Claude);
- os cargos curtos e engraçados: duas ou três hipóteses para a mãe da Clara, o Tiago e a Clara, com o
  filtro do colega conservador. Ele escolhe, porque o texto no ecrã é dele;
- os três cargos têm de ficar claros e visíveis no fecho.

**Ele marcou e mandou** (30 de setembro): *"Já te marquei umas fotos para créditos e dei os
convidados, mostra-me um exemplo?"* As fotos são as do grupo "Créditos" da Mesa (11 a 30/09). Os
convidados estão na folha `C:\casamento-video-media\Convidados\convidados-*.xlsx`, que **não vai para
o Git** (são dados de 140 pessoas).

**O exemplo de 30 de setembro:** `py -3.11 scripts/discussao/ponto5_creditos.py` escreve
`saida/discussao/ponto5/exemplo_creditos.mp4` e a cópia do telemóvel. `--so-dizer` só faz as contas e
`--quadros` tira sete fotogramas soltos. Lê tudo pelo nome: o grupo "Créditos" na leitura mais recente da
base, a versão de cada foto no `data/finais.csv`, a folha de convidados mais recente e a última música
do `v3.som.csv`. Leva:
- os últimos 5 s do render de ensaio antes do fade, a desfazer-se em 1,5 s nos créditos, sem preto;
- os nomes a subir a 150 px/s à direita, Arial Bold 58, um agregado (a coluna Família) por linha, a
  quebrar só entre pessoas; os títulos no letreiro da 098 a 60 px, e o lado da família ou o sítio dos
  amigos em champanhe por baixo;
- as fotos marcadas numa coluna à esquerda, a subir ao mesmo tempo;
- os três cargos, 4,2 s cada, com os que o juiz recomendou (abaixo);
- "CLARA & TIAGO" e a data, 7 s, até ao preto;
- a música do fim a continuar de onde o filme a deixa, e a desvanecer nos últimos 4 s.

Dá 90 s de créditos, e o filme fica em cerca de 880 s.

**Só entram as etiquetas de grupo** (`GRUPOS` no script, pela ordem dos créditos). Nunca vão ao ecrã as
etiquetas dos convites e dos contactos, as que dizem onde alguém não pode ficar sentado, as notas, nem
os "Noivos". A 30/09 as 136 pessoas (138 menos os noivos) tinham todas uma etiqueta de grupo; as quatro
com "Irmão" também têm outra, e entram por essa.

**Os cargos** (dois agentes escreveram, um juiz filtrou pelo colega conservador, 30/09):

| | Recomendado | Alternativas |
|---|---|---|
| Mãe da Clara | Ideia, textos, música e horas sem conta | Ideia original, argumento e horas extraordinárias; Argumento original: sem ela não havia filme |
| Tiago | Montagem, estrutura e «só mais uma versão» | Assistente de realização, promovido a montador; Montagem e cortes, todos com dor de alma |
| Clara | Aprovação final e direito de veto | Validação final e o sim mais importante; Controlo de qualidade. Nada passou sem ela |

Eliminados pelo juiz: "Efeitos especiais em Windows Movie Maker" e "Realização original, versão alargada
de 23,5 minutos" (diminuem o trabalho dela), "Argumento adaptado, com a devida autorização" (piada de
sogra), "Supervisão final e o famoso hmm, não" (faz da noiva a do contra).

**O que ele disse do exemplo** (30 de setembro): *"Não desgosto destes créditos, mas claro que há alguns
ajustes que quero fazer seja nos labels sejam nas fotos, mas acredito que no conceito possa funcionar."*
O conceito fica; os ajustes são dele. Os grupos e os nomes mudam-se na folha de convidados (as
etiquetas) e as fotos no grupo "Créditos" da Mesa; o script lê as duas outra vez em cada corrida. Os
títulos de cada grupo estão em `GRUPOS`, no script.

**Por decidir por ele:** os ajustes aos grupos e às fotos, os cargos, como se chama a mãe da Clara no
ecrã e a letra do título final.

**1 de outubro:** *"Acrescentei mais algumas fotos aos créditos na mesa. Uma questão importante é como
é que está a ficar ordenado a aparecer no ecrã."* Passaram a ser 27 fotos (rev 990). O script ordenava
as fotos pelo número da Mesa (`sorted` dos ids), que não é a ordem dele nem a das datas. Com 27, a
coluna de ontem subia a mais de 200 px/s. O filme encolheu para cerca de 732 s, e há folga até aos
900 s. A medir e a propor: a ordem e a maneira de as mostrar.

**Ele respondeu** (1 de outubro): *"Sobre os créditos eu gosto da coluna a subir. Ajustar a ordem é
que ainda não percebi como posso fazer."* A coluna fica.

Construído no `ponto5_creditos.py`:
- **A ordem:** se houver na Mesa uma versão chamada "Créditos", a coluna segue a ordem dos clips dela.
  Os cartões são ignorados. As fotos marcadas que não estejam lá vão para o fim, com aviso.
- **A velocidade:** a coluna não passa dos 150 px/s; os créditos esticam e os nomes abrandam para
  acabarem juntos. Com 27 fotos dá 152,5 s de créditos, com os nomes a 79 px/s, e o filme fica em
  cerca de 882 s.
- **A alternativa por decidir:** as fotos ao alto mais pequenas (600 px de altura em vez de cortadas a
  900) dariam cerca de 137 s.

**Depois** (1 de outubro): *"Eu as fotos dos créditos ainda vou ajustar depois."* A duração dos créditos
depende de quantas fotos ficarem, por isso a escolha entre as fotos ao alto como estão e mais pequenas
espera por isso. Quando ele disser que estão prontas: ler a base, correr o `--so-dizer` para dar a
duração, e fazer o exemplo com `--colar`.

**Pedidos de 1 de outubro fora dos cinco pontos:** *"Estava a pensar se conseguimos aumentar o número
de fotos no mergulho, bem como o número de fotos a que fazemos o zoom in. Queria também aumentar o
número de fotos em que podemos fazer colagem ou pilha."* Hoje:
- o mergulho usa os limites da colagem e mergulha só na última;
- a colagem vai até 20 e a pilha até 40, com o leque só até 24 (decisões 087 e 091).

Estão a ser medidos antes de qualquer proposta.

**O que as medidas de 1 de outubro dizem** (oito agentes, quatro a medir e quatro a verificar). O
texto inteiro está em `saida/discussao/propostas_1001/`, fora do Git.
- **Créditos:**
  - Com 27 fotos a coluna sobe a 286 px/s, e cada foto fica 1,5 s inteira: não serve.
  - Recomenda-se uma versão "Créditos" na Mesa, onde ele põe a ordem, com cartões opcionais a ligar as
    fotos aos grupos de nomes. As fotos ficam paradas, a trocar no mesmo sítio, 3,5 s cada.
  - Os créditos ficam com cerca de 116 s e o filme com cerca de 845 s.
  - Muda o conceito que ele aprovou (a coluna a subir): pergunta-se.
  - 17 das 27 fotos estão no vídeo da mãe, com secção, e isso dá uma primeira ordem.
  - A duração dos créditos decide onde acaba o Taking Care of Business (096).
- **Mergulho:**
  - Já hoje, dentro dos 2 a 20, há defeitos:
    - a grelha sai em tiras com 3, 5, 7, 11, 13, 14, 17 e 19 fotos;
    - a meio do mergulho aparecem 80 a 149 px de preto na borda;
    - a legenda tapa 36 a 48% da última foto;
    - o `auditar_nitidez.py` rebenta;
    - a Mesa não mostra a grelha do render e propõe durações da colagem.
  - Proposta: corrigir isto primeiro, e depois um limite próprio de 36.
  - Para mergulhar em mais fotos há três maneiras, nenhuma vista por ele:
    - A, mergulha, volta à grelha e mergulha na seguinte;
    - B, desliza de perto entre vizinhas;
    - C, voa entre fotos.
  - Há também a alternativa sem código: vários grupos em mergulho seguidos.
  - Cada foto mergulhada fica 0,8 s a encher o ecrã.
  - Escolhe-se por prévias.
- **Colagem:**
  - Acima de 24 em filas o render rebenta (ValueError).
  - Proposta: subir a 30, com partições até 6 filas de 10 e o filtro de convergência só acima de 24.
    De 25 a 30 a foto mais pequena fica como hoje com 20; a partir de 36 cai.
  - Alternativa barata: 24, que já tem partições.
  - Os textos por foto não cabem acima de 20.
- **Pilha:**
  - O monte não parte até 80. O limite é a memória: cada fatia abre todas as fotos em resolução total,
    e a pilha de 15 deixou o PC com 84 MB livres no render desta noite.
  - Abrir uma foto de cada vez dá sprites iguais ao byte. Recomenda-se fazê-lo já, e subir o monte a 60.
  - O leque fica em 24, confirmado desenhado.
  - Numa pilha de 60 cada foto é um relance (0,5 s) e os textos por foto não se leem.
- **As regras fixas** ("máximo 4 ou 5 fotos seguidas do mesmo evento", "nunca menos de 3 s por foto")
  chocam com grupos grandes. A rajada é o precedente; diz-se-lhe.

**Ele decidiu** (1 de outubro): *"Avança com estes: o mergulho: corrigir os defeitos que já tem,
deixá-lo ir até 36 fotos e escolher como mergulha em mais do que uma, a partir de prévias. A colagem:
até 30 fotos. A pilha: até 60 fotos em monte, depois da correção de memória. Se houver mais alguma ideia
interessante em transições giras, criativas e diferentes diz-me."* Decisão 102. A construir:
- a correção de memória;
- a pilha até 60;
- a colagem até 30;
- as correções do mergulho e o limite de 36.

As prévias do mergulho em mais do que uma foto vêm a seguir, e as ideias de transições estão a ser
procuradas à parte.

**As ideias de transições** (1 de outubro): três agentes propuseram e um juiz filtrou-as pelas regras e
pelo que ele recusou a 30 de setembro. Tudo está em `saida/discussao/propostas_1001/ideias_transicoes.json`.
- **As três para prévia:**
  - **a grelha das duas vidas:** no encontro, as fotos dele à esquerda e as dela à direita acendem numa
    grelha, e o mergulho acaba na primeira foto dos dois. A primeira versão faz-se já na Mesa, sem
    código;
  - **a cara no mesmo sítio:** nos penteados, as fotos em corte seco com a cara dela sempre no mesmo
    ponto e tamanho;
  - **a fita até hoje:** antes dos créditos, o contador do princípio a andar para a frente até
    «4 de outubro de 2026». Sem código.
- **Ficaram atrás:**
  - rebobinar as fotos dele para ir buscar o nascimento dela;
  - a foto dentro da palavra, na primeira viagem;
  - o grande plano dentro da foto;
  - o corte no compasso, nos blocos com batida;
  - «Adivinham quem?», no bloco dos cães.
- **Deitadas fora,** com a razão no ficheiro: a passagem de foco, as metades que se juntam, as duas fitas,
  os diapositivos, a íris, o mosaico, a página de álbum e o carimbo.

**O pedido para o fim da construção** (1 de outubro, 18:04): *"Depois de tudo valida e faz render de
um vídeo incluindo os créditos."* Pela ordem:
1. Publicar a Mesa nova, com o retrato e o `montagem/publicacao`; ler o `estado2` e confirmar.
2. Juntar e montar a versão dele (rev 1042 ou a que houver), ver os avisos do montar e correr o
   `ponto3_3_frases.py --so-dizer`. Os textos marcados ficam como estão ("ajusto no fim"), mas
   diz-se-lhe quais são.
3. Fazer o render com `--so-telemovel`, e com as fatias que o aviso de memória propuser.
4. Correr `ponto5_creditos.py --colar`, para ter o filme com os créditos numa só cópia do telemóvel.

**O render rápido de 1 de outubro, à noite** (pedido dele, em paralelo com a revisão):
`saida/discussao/ponto5/v3_2026-10-01_2103_parcial_com_creditos_telemovel.mp4`.
- **Como se fez:** a Mesa na rev 1042, com 169 clips, montada numa pasta à parte
  (`saida/render_rapido_1001/montagens`, para não mexer nos ficheiros que os testes leem). O render foi
  a meia resolução (`--escala 0.5 --fatias 4`), e os créditos colaram-se com
  `ponto5_creditos.py --colar --filme`.
- **Duração:** 11:33 de filme mais 2:32 de créditos, 14:03 no total.
- **A ordem das músicas mudou:** o bloco do trabalho (Taking Care of Business) passou para antes dos
  Filhos do Dragão e dos Queen. O filme acaba agora nos Queen, e os créditos continuam-nos; a música
  acaba no fim verdadeiro dela, cerca de 2 s antes do último fotograma.
- **As trocas de música:**
  - só duas mantêm o fim de frase medido: Clair para Who Let The Dogs Out, e Filhos do Dragão para
    Queen;
  - cinco descem no corte até se medirem outra vez;
  - cinco são pares novos, por causa da ordem dele e da troca Steppenwolf e Fome de Viagem, e
    cruzam-se como antes da 096.

**O pedido de 2 de outubro, a Mesa para o dia com a Clara:** *"Agora precisa de aprofundar o que podemos
fazer na nossa Mesa, pois amanhã vou ter um dia em cheio com a Clara e quero sermos capazes de com ela
ajustar ao máximo diretamente na Mesa e depois darmos só ordem para fazer render."*

Na Mesa, nas palavras dele:
- o tamanho da letra e o tipo da letra;
- ajustar a ordem das fotos dos créditos "de forma simples e prática enquanto os nomes movem";
- pré-visualizar "da forma mais realista possível", para não ter de fazer render só para analisar;
- o vermelho da intro: *"A Clara pediu-me para alterarmos o vermelho que está na intro da Marvel, pois
  diz que parece demasiado Marvel"*. Quer a cor, o tamanho e o estilo personalizáveis na Mesa,
  "incluindo as linhas e os contornos que aparecem no contador do tempo";
- ouvir a música no tempo certo durante a pré-visualização;
- editar os textos do fim dos créditos;
- personalizar os textos dos cartões, porque a Clara pode querer mudá-los.

Fora da Mesa:
- marcar numa foto uma zona com mais destaque (*"umas fotos de equipa que se eu não assinalar quem eu
  sou as pessoas podem não perceber"*);
- o contador inicial: começa em 2026 dia a dia, mas *"quando chegamos a 1995, é como se fosse um contador
  diferente"*;
- mais espaço entre a data "12 de setembro de 1995" e o "SET" da régua.

A pergunta dele: se no teste do projetor for preciso ajustar as legendas, ter o projeto no DaVinci
Resolve, *"pois acredito que fosse mais rápido"*. *"Isto é possível e se sim como e a que custos?"*

**O que ele acrescentou às 02:23:**
- *"We should always be able to keep it as is, e.g. the contador."* Cada opção nova tem «Como está»,
  que é a omissão.
- *"Confirma que tens as fotos todas que estão na pasta final."* As 719 do índice estão todas na
  FINAIS. Há lá 44 ficheiros a mais: 33 sobras antigas e 11 cópias «- Copy», das quais 5 têm conteúdo
  diferente (a `DSC02954 - Copy.JPG` é de 1 de outubro). Não se mexe, regra 4.
- *"Em termos de fontes inclui estas pelo menos."* Mandou as letras dos convites. Candidatas
  acrescentadas a `data/fontes.json`: Great Vibes, Pinyon Script, Cormorant Garamond normal e itálica,
  Cinzel normal e Playfair Display.
- *"O marcar-me numa foto de equipa nem sempre é possível com zoom (...) precisamos de outra forma de
  realçar."* O destaque escurece à volta e desenha um contorno, sem zoom.
- *"No contador o que refiro é o movimentar em 1995 que não pode parecer outra peça."*
- O teste do projetor: *"Será no próprio dia, mas também há possibilidade de passar para um pc antigo
  com placa NVIDIA (...) será que se passasse o Claude para lá conseguiria melhores resultados?"*

**As respostas dele, às 02:33:**
- *"Sim, descarrega as quatro."* Descarregadas para `C:\casamento-video-media\gerados\fontes\`, do
  repositório do Google Fonts (OFL): Great Vibes, Pinyon Script, Cormorant Garamond itálica e
  Playfair Display.
- *"O meu comentário sobre o HP Pavilion de há 6 anos não é para projetar, mas sim para perceber se o
  render seria mais rápido e bom."*
- *"E se para já trabalharmos na Mesa, mas também colocarmos a opção a certa altura de criar o ficheiro
  como falaste para o DaVinci, assim se começar a apertar, mudo para o DaVinci de forma mais fácil."*
  Fica o pacote do DaVinci (`davinci_pacote.py`): o filme sem as legendas de baixo, as legendas num
  `.srt` e um guia. Constrói-se depois de a equipa do render libertar o `render.py`, com o contador
  contínuo como escolha e o destaque completo (`scratchpad/render_parte2.js`).

**A norma de cor, 2 de outubro de manhã.** O corpo do filme é gravado com a receita de cor antiga
(a das televisões normais) e o ficheiro diz que é a da alta definição; um leitor mostra as cores um
pouco desviadas (no render de 1 de outubro às 23:11: até 4% mais carregadas, vermelhos para laranja,
pele mais amarela). Imagens em `saida/discussao/cor/`. Ele: *"Sim, corrige, mas apenas se tiveres a
certeza"* e *"E se tiveres a certeza que é necessário."*
- Os critérios fixaram-se antes de medir. **Certa:** com a correção, o erro desce ao da compressão e
  nenhuma peça fica pior nem desencontrada. **Necessária:** uma cor escolhida na Mesa sai com
  ΔE2000 de 3 ou mais, ou a pele com mediana de 2 ou mais. Sem isso, não se mexe.
- Cuidado já visto: se os vídeos do meio do corpo forem lidos com o mesmo erro, os dois anulam-se
  hoje, e corrigir só a gravação estragava-os. O mesmo com a intro já gravada.
- A verificação corre só a ler (workflow `norma-de-cor-certeza-e-necessidade`). A mudança, se passar,
  só depois de a equipa do render libertar o `render.py`.
- **O veredicto (15:00): necessária sim, certa não, à letra.**
  - Necessária: o vermelho da intro, #96161C, sai #A1221B. São 3,6 a 3,8 de ΔE2000, conforme o
    descodificador, medido no próprio filme de 1/10, no Chromium e no leitor do Windows. O Vinho dá
    3,1 a 3,7. A pele não decide (1,2 a 2,3, conforme a definição).
  - Certa, à letra, não: nas fotos a correção baixa a mediana de 1,83 para 0,81, e nas 36 fotos fica
    melhor em todas. Mas nas bordas das letras cor de champanhe dos cartões e dos nomes fica
    ligeiramente pior: +0,09 de mediana em 12 de 13 textos, até +0,19. É invisível, mas falha o "nada
    pior". A razão está provada: hoje o erro de matriz satura as letras quentes, e isso compensa
    por acaso o croma que a compressão lava nas bordas.
  - A correção completa não é só uma linha: o encoder do corpo, a leitura dos vídeos do meio
    (sem ela o Homer piorava de 0,75 para 2,29), a fanfarra por RGB (converte as intros já feitas),
    o encoder dos créditos e a carta do projetor. Nunca opções de cor na junção pelo concat, que
    decide pela primeira parte e converteria tudo. Plano e provas em `scratchpad/cor_wf/`.
  - Pela regra dele ("só se tiveres a certeza"), não se aplica sem ele decidir.

**A música dos créditos, 2 de outubro de manhã.** Ele: *"Gostava de também poder alterar a música que
toca nos créditos, sendo que idealmente gostava de também a conseguir editar na própria Mesa. Neste
momento temos os Queen a vir dos amigos, mas acho que gostava de voltar ao Taking care of business."*
- Hoje os créditos continuam a última música do filme (os Queen) de onde o filme a deixa.
- O Taking Care of Business já toca no filme, no bloco do trabalho, dos 60,8 aos 103 s do ficheiro
  (296 s). Tocado do início nos créditos, repetia essa parte uns três minutos depois.
- Na Mesa, no painel dos créditos, entra a escolha `est.creditos.musica = {ficheiro, inicio}` com
  `inicio` em `"fim"` (acaba com os créditos), `"inicio"` ou um segundo, para ouvir na Mesa. Sem ela
  fica "Como está". Contrato em `saida/discussao/contrato_mesa_1002.md`. O render dos créditos
  (`ponto5_creditos.py`) lê-a depois de a equipa do render o libertar.
- Ele: *"Mete já o Taking Care."* Escrito na base às 11:52 (versão 1388 para 1389, rev 1389):
  `{ficheiro: "Bachman Turner Overdrive-Taking care of business_62s.mp3", inicio: "fim"}`. O resto da
  montagem ficou igual (só mudaram `creditos`, `rev` e `quando`). A Mesa publicada (v51) guarda o
  campo sem o mostrar; o painel novo mostra-o.

**Caracteres que a letra do filme não tem (2 de outubro).** Ao ler a base apareceram dois textos dele
que o Arial Bold desenha como um quadrado vazio (imagem em `saida/discussao/caracteres_em_falta.png`):
- o emoji no fim de *"E porque não ganhar uns € como modelo?"* (demo_v3, clip 72, foto f0108), que
  já estava no render de 1 de outubro;
- o hífen inseparável (U+2011) em *"Audio‑Visual Operations Maestro"*, o terceiro cargo dos créditos.
- Proposta: o render desenha o hífen inseparável como o hífen normal (é o mesmo sinal, o texto não
  muda), e a Mesa passa a avisar de qualquer carácter que a letra do filme não tenha. O emoji é
  decisão dele.
- Ele: *"Prefiro que faça o render de emojis se incluirmos."* O render passa a desenhar os emojis a
  cores, com a letra de emojis do Windows (`C:\Windows\Fonts\seguiemj.ttf`, que a Pillow 12.3 com o
  FreeType 2.14.3 desenha a cores com `embedded_color=True`; provado). Vale para todos os textos do
  filme: legendas, textos das fotos dos grupos, cartões, nomes e créditos. Amostra em
  `saida/discussao/emoji_a_cores_exemplo.png`. No telemóvel, a Mesa mostra os emojis com o desenho do
  próprio telemóvel, que é diferente do do Windows.

**As fotos da pilha, 2 de outubro à tarde.** Ele: *"As fotos da pilha estão agora muito pequenas, gostava
delas maiores como já estiveram antes, porque assim ficam quase impercetíveis, mas também o texto que
elas têm fica ilegível."*
- No filme não mudaram: as pilhas dos renders de 23 e 30 de setembro e de 1 de outubro às 23:11 têm o
  mesmo tamanho. Cada foto ocupa cerca de 48% da largura (caixa `render.PILHA_LARG` 0,50 por
  `PILHA_ALT` 0,64), e o texto lê-se. Fotogramas em `saida/discussao/pilha/`.
- Quem encolheu foi a Mesa. A pré-visualização desenha os grupos com o `mostraQuadro()`. A peça tem
  `min(W, H) × 0,52` (× 0,80 com legenda), cerca de 23 a 29% da largura, metade do filme. E desde a
  manhã de 2 de outubro a peça tem a forma da foto, em vez de um quadrado, o que a encolheu ainda mais.
- A correção é só na Mesa: os grupos na pré-visualização com a geometria do render (pilha em monte e
  em leque, colagem, lado a lado) e o texto das fotos no tamanho do render.
- Ele: *"Mas e quando fica a Mesa concluída? Nota que eu e a Clara temos de trabalhar ainda hoje no
  vídeo."* Fez-se logo um remendo só da pilha em monte, fora das equipas: `pilhaMonteDoRender()` no
  `editor_base.html` (o `render.pilha_disposicao()` com o `encaixar_grupo()`, os ângulos da Pillow
  com o sinal trocado para o CSS). Aplicado à página publicada de manhã e publicado às 15:00 como
  versão 52 da Mesa, com o mesmo retrato das fotos (nenhuma foto mudou desde a manhã). Visto no
  browser com a montagem dele: a pilha de 5 e a de 15 ficam do tamanho do filme. O leque e a
  colagem ficam para a equipa seguinte. Remendo em `scratchpad/hotfix_pilha/remendo.py`.
- Depois de publicar, a leitura da base para confirmar a montagem foi recusada pela ferramenta. Fica
  por confirmar que a montagem continua lá; pediu-se-lhe que confirme ao recarregar.

**A Mesa de 2 de outubro às 16:47 (versão 53).**
- **Fotos novas:** 5 na `01-NOVAS/02.10.2026`, deixadas por ele às 11:33. Duas são iguais pelo
  conteúdo (hash) a fotos que já existiam: `IMG_4073.JPG` (a mesma que está no vídeo da mãe) e
  `DSC07282.JPG` (a mesma que já estava na `01-NOVAS`). Só se reporta, nada se apagou. O
  `atualizar_fotos.py` deixou 724 prontas.
- **Publicado:** a página e as 46 folhas das prévias. A página traz a música dos créditos no painel,
  os créditos com os tempos do render, a data afastada, os avisos do estilo, o destaque igual ao do
  render, a guarda das duas gravações no mesmo instante (campos `gravacao` e `cadeia`) e o remendo
  das pilhas. A `montagem/publicacao` foi escrita: build `20261002-164356`, 724 fotos.
- **A base depois de publicar:** rev 1435, 169 clips na demo_v3, o Taking Care of Business mantido,
  34 fotos nos créditos. Ele e a Clara escolheram a intro Preto e dourado.
- Com o Preto e dourado, o desvio de cor da intro fica pequeno (fundo 0,6 e letra 1,4 de ΔE2000). O
  vermelho dos riscos da fita (#C83E56) continua a sair com 5,4 a 5,8.
- O texto da decisão da Mesa (música dos créditos, duas gravações) está guardado. Entra no
  DECISOES.md como 108, depois da 106 e da 107 da equipa do render que está a trabalhar.

**A passagem dos Queen para o Taking Care of Business (2 de outubro, 18:40).** Os 95,00 s da manhã
eram do fim do filme de 1/10, porque o `v3.csv` ainda é o de 1/10 às 22:40. Com a Mesa de hoje, o
filme acaba 21,5 s mais cedo, e no corte dos créditos os Queen estão aos 68,70 s do ficheiro, a meio
de uma linha. Hoje a linha nova ouve-se cerca de 1 s por baixo do Taking Care of Business. As saídas:
- **(A) trocar no corte:** no fim de hoje corta a linha a meio.
- **(B) os Queen acabam a linha:** o Taking Care of Business entra 2,7 s depois da imagem. Foge à
  regra de a música mudar com o bloco. Chave `est.creditos.musica.passagem = "frase"`, que o
  ponto5 já lê; a Mesa recebe a escolha na parte 4.
- **(C) alongar o último clip 2,7 s:** o corte cai no fim da linha, imagem e música mudam juntas.
  Mede-se outra vez quando o fim estiver fechado.
- Recomendação da equipa: a C, ou a B se ele não quiser mexer na imagem. Medido com dois métodos;
  a verificação por um segundo agente (096) faz-se no fecho, com o fim decidido. Cópias para ouvir
  em `saida/discussao/juncao_creditos/`. Script: `scripts/discussao/juncao_creditos.py`.
- Ele, às 18:47: *"c"*. Fica a (C). A Mesa passa a dizer, na aba Música dos créditos, quantos
  segundos faltam ao último clip para o corte cair no fim da frase. Avisa, não corrige: é ele que
  muda a duração. Antes do render final mede-se outra vez (096).

**Tirar fotos dos créditos (2 de outubro, 18:46).** Ele: *"Torna simples também na zona de editar os
créditos de remover fotos que já estão incluídas neste momento como sendo marcadas para crédito."*
Hoje uma foto dos créditos é uma foto com a etiqueta «Créditos» ou na versão «Créditos», e tirá-la
obriga a ir à foto. Vai um «Tirar dos créditos» em cada foto do painel. Tira a etiqueta, tira a foto
da versão «Créditos» e tira-a da ordem, com Anular. A foto continua no filme.

**Trocar uma foto por um recorte dele (2 de outubro, 19:30).** Ele: *"Quero também trocar esta:
IMG_20260922_192900 por esta IMG_20260922_192900 - Copy."*
- A original é a f0719 (`01-NOVAS/IMG_20260922_192900.jpg`, 2304 x 4096). É uma foto de uma foto, com o
  monitor e a barra do Windows em cima. Está na demo_v3, no clip 15.
- O recorte dele está em `FINAIS/IMG_20260922_192900 - Copy.jpg`, 2304 x 3375, deixado às 19:28. Corta
  o monitor. A `FINAIS` não é uma fonte: o filme só lê o que o `finais.csv` escolhe.
- O caminho: copiar o recorte para a `01-NOVAS` (ficheiro novo, nada se move nem apaga) e correr o
  `atualizar_fotos.py` depois de a equipa do render acabar os testes. Na Mesa publicada depois, troca-se
  a f0719 pela foto nova no clip 15, com escrita na base. A f0719 fica na biblioteca, não usada.
- A escrita na base só depois de a Mesa nova estar publicada. A Mesa de agora não conhece a foto nova,
  e um clip com uma foto que ela não conhece podia perder-se ao gravar.
- **3 de outubro, 01:00.** O recorte foi copiado para `01-NOVAS/IMG_20260922_192900 - Copy.jpg` (o
  mesmo hash) e registado como f0726. O `atualizar_fotos.py` encontrou também uma foto nova dele, a
  `01-NOVAS/5-3.jpg` (f0725, 592 x 911, digitalização). Ficam 726 fotos.
- **A Mesa versão 54, publicada à 01:06,** traz: a página da equipa da Mesa da noite (decisão 110),
  as cópias da intro Bernard e as 46 folhas. Build `20261003-010326`. Depois de publicar, a base
  estava na rev 1653, com 152 clips na demo_v3 (eles tiraram clips à noite). O Taking Care of
  Business, as 34 fotos dos créditos e o estilo com Playfair nas legendas e nos cartões estavam lá.
- A troca f0719 → f0726 no clip 15 foi recusada pela guarda (`version_mismatch`): a base passou de
  1653 a 1661 em dois minutos, porque eles estavam a gravar. Não se forçou. Faz-se quando pararem.

**Os cargos dos créditos (2 de outubro, 19:33).** Ele: *"Nos créditos permite-nos testar a
possibilidade de aparecer primeiro os tais cargos nos vídeos, permite também acrescentar mais cargos e
mais pessoas e depois as nossas pessoas com os convidados e fotos."* E: *"refiro-me a poder testar
naquele menu dos créditos que criámos."*
- Contrato em `saida/discussao/contrato_creditos_cargos.md`: `cargos_primeiro`, 1 a 8 cargos, e 1 a
  4 pessoas por cargo, separadas por mudança de linha.
- A Mesa faz o painel e a pré-visualização (acrescentado à equipa da Mesa desta noite, como etapa
  `cargos`). O render (`ponto5_creditos.py`) faz o mesmo a seguir à equipa que está a fechar.

**Os pedidos de 3 de outubro, de madrugada (04:50 e 05:05).** Uma lista longa, com a imagem do título
final dos créditos. Contrato em `saida/discussao/contrato_1003.md`, com as palavras dele em cada ponto:
- a letra do contador, com as letras das legendas;
- a legenda do clip 10 numa só linha;
- a posição das legendas, global e por clip, e a legenda do clip 69 (insígnias);
- o lado a lado com fotos inteiras;
- nos créditos: o título «CLARA & TIAGO» antes do rolo, os cargos removidos por inteiro (*"quero mesmo
  poder remover integralmente"*), os nomes corridos sem os grupos e a velocidade dos nomes e das
  fotos;
- o contador do fim de 2023 a 4 de outubro de 2026, parado mais 3 s;
- um contador até à data em que se conheceram. A data pergunta-se: a 011 diz 2009/2010 para se
  conhecerem e 20 de maio de 2012 para ficarem juntos;
- a música de todas as músicas novas, pela regra (094 a 096);
- 15 fotos trocadas por versões novas: o recorte do polícia, Veneza, Dubrovnik, Terceira, Iguaçu, o
  10-5, o 21-23, o 21-3, o 21-28 e as 82-x, mais o 1031. A `2016_tIAGO_AMIGOS_FACULDADE_2...` foi
  atualizada no mesmo sítio.
- **A data do contador, decidida:** *"Ensure also that we can conheceram-se em 2011 e o contador para em
  maio de 2012 onde começaram a namorar."* O contador vai de 1995 a 20/05/2012, com «Clara e Tiago
  conhecem-se» em 2011 e um texto de início de namoro no fim. **Muda a decisão 011**, que tinha «não se
  conheceram em 2011» confirmado por ele a 10 de setembro. Disse-se-lhe isto explicitamente.
- **As músicas são as que eles escolheram na Mesa (05:50).** Ele: *"Decidimos na Mesa de Montagem que
  músicas queríamos incluir, e umas tirámos e outras incluímos. Isso não é bem uma decisão. Quero ter
  a opcionalidade das músicas que quero."* Mandou o mapa por posição: Lang Lang no 1.º contador, Rei
  Leão (6), Céline Dion (7), Ana Faria (20), Mr. Blue Sky (37), Baha Men (42), António Variações (49),
  Lang Lang a continuar no contador 57, Tribalistas (58), Billy Joel (66), Vance Joy (72), Bachman
  Turner (74), Filhos do Dragão (89), Edward Sharpe (101), Queen (119), Olivia Dean (133) e Lang Lang
  a continuar no contador 143.
  - A lista dele é a verdade: só tocam estas músicas.
  - A parte da 001 sobre as canções com o nome da pessoa passa a ser escolha dele. Uma automática do
    montar que ele não listou não toca.
  - Os efeitos (foguetes, fita a rebobinar) mantêm-se e confirmam-se com ele.
  - As marcas das posições listadas já estavam todas certas na rev 2374. Faltava o Lang Lang a
    continuar nos contadores 57 e 143.
- **O render das 10h (pedido dele às 05:15):** *"Precisávamos de uma versão muito aproximada do resultado
  que metemos agora na Mesa e com as nossas instruções pronta de manhã pelas 9/10h."* E: *"depois para
  a versão final fazemos os ajustes finais de limar arestas."*
  - **Como se fez:**
    - três frentes do render em paralelo: legendas e lado a lado, contadores, créditos;
    - o mapa das músicas (um agente analisa, outro verifica);
    - um ensaio do filme inteiro a um quarto do tamanho, sem erros;
    - o estado composto em `scratchpad/render_10h/estado_para_o_render.json`: a leitura da rev 2374
      mais as instruções que a Mesa publicada ainda não guarda, sem escrever na base;
    - `montar_da_mesa.py demo_v3`, `render.py v3 --sem-copias --fatias 6` (07:27 a 08:04) e
      `ponto5_creditos.py --colar --estado ... --filme ...` (até às 08:17).
  - **O que saiu:** `C:\casamento-video-media\saida\v3_2026-10-03_0759.mp4` (1080p, 218 MB) e
    `saida/discussao/ponto5/v3_2026-10-03_0759_com_creditos_telemovel.mp4` (13:03, 28,6 MB), enviado
    às 08:18.
  - **O que leva:**
    - as 15 fotos trocadas;
    - o Lang Lang nos contadores 57 (in 43,7) e 143 (in 52), com a retoma da 060 mantida;
    - o clip 57 `1995>20/05/2012|2011=Clara e Tiago conhecem-se;20/05/2012=Começam a namorar`;
    - o clip 143 `2023>04/10/2026` com `cp` 3;
    - os créditos com `partes` título e rolo, e `nomes_corridos`;
    - `li` nos clips 107 e 108;
    - duas trocas curtas de 0,3 s: Rei Leão para Céline Dion, e Vance Joy para Bachman Turner.
  - **O que não deu:** a legenda do clip 10 numa linha. Precisa de 1762 px e há 1660, com Playfair
    a 59, por isso saiu em duas linhas.
  - **Por decidir por ele:**
    - a retoma do piano na fita antes da Clara (060), que não está na lista dele;
    - o lado a lado inteiro nos clips 45, 69, 70, 71, 115 e 129, que cortam mais de 25% (cinco têm
      foco escolhido por ele).
- **Fotos e músicas da pasta para a Mesa, sozinhas (11:20).** Ele: *"Há duas funcionalidades que
  precisamos, que é a possibilidade de colocar fotos na pasta e elas entrarem logo na Mesa de Montagem,
  e igual para as músicas. Estas funcionalidades têm de estar prontas até às 16h."*
  - O caminho: `scripts/vigiar_pastas.py` vigia a `01-NOVAS` e a `02-NOVAS-MÚSICAS` e avisa quando há
    ficheiros novos já parados. `scripts/entrada_rapida.py` faz só o trabalho das novas e escreve
    `saida/entrada_rapida.json` com a lista exata do que publicar.
  - A publicação continua a ser minha, com a ferramenta: a página e os ficheiros do manifesto, ler a
    `montagem/estado2`, e escrever a `montagem/publicacao`.
  - Só funciona com esta sessão aberta no PC.
  - Em construção, com hora limite às 15:30 (workflow `entrada-rapida-de-fotos-e-musicas`).
- **A Mesa versão 56, publicada às 12:15.** Traz as escolhas do contrato de 3 de outubro e os
  interruptores dos seis sons automáticos (botão «Som do render»). Logo a seguir escrevi na base o que
  entrou no render das 10h (versão 2374 para 2375), e a montagem da base ficou igual, clip a clip, ao
  estado que foi ao render:
  - clip 57: o texto novo e o piano (`m`, in 43,7);
  - clip 143: o texto novo, `cp` 3 e o piano (`m`, in 52);
  - clip 10: `x1`;
  - clips 107 e 108: `li`;
  - créditos: `partes` e `nomes_corridos`.
- **«Sê prático e eficiente na execução dos meus pedidos. Aplica um critério 80/20»** (11:40). Fica
  como regra de trabalho. O vigia das pastas ficou logo a correr com o caminho de hoje (6 a 8 minutos
  por lote), e a versão rápida entra quando estiver pronta.
- **As arestas limadas (12:45).** Propus nove pontos a partir da revisão do filme das 10h, e ele: *"Sim,
  aplica o que propões."*
  - **Na base (versão 2375 para 2376):**
    - clip 57 com 12 s, `cp` 3 e o piano em `in: "continua"`;
    - clip 143 com o piano em `"continua"`;
    - clip 90 com a foto direita: `IMG_20260922_191615 - rodada.jpg`, f0742, recortada e rodada a
      partir da f0714, com o `zd` recalculado;
    - `li` nos clips 115 e 129;
    - cinco gralhas: «Adivinham», «... Quem será?», «... 1 ano depois», «12.º ano», «Boca Juniors».
  - **No código:**
    - `render.LEGENDA_LARGURA_NUMA_LINHA` passa a 1762, e a legenda do clip 10 fica numa linha, a
      82 px das bordas;
    - `ponto5_creditos.FILME_APAGA` é 0,7 s: com o título primeiro, o filme apaga-se e só depois o
      título acende (muda a regra de 28 de setembro só nesse caso; ficam 2 fotogramas de preto).
  - **Ficam como estão, por escolha dele:** os 28 textos rápidos (082), o piano na fita antes da Clara
    (060) e o fim dos créditos.
  - **O render:** `v3_2026-10-03_1344.mp4` (13:10 a 13:48) e
    `saida/discussao/ponto5/v3_2026-10-03_1344_com_creditos_telemovel.mp4` (13:09, 28,6 MB), enviado às
    14:02. O `ponto3_3_frases.py --so-dizer` deu «certa» nas duas trocas medidas.
  - **A Mesa versão 57** foi publicada às 13:09 com a foto nova. A pré-visualização dos créditos ainda
    faz a entrada antiga do título, e um agente está a acertá-la.
- **A noite de 3 de outubro (decisão 114).**
  - **20:14, Mesa versão 59:** a vigia apanhou 12 fotos do WhatsApp das 20:07. Estão em disco duas
    vezes (na raiz da `01-NOVAS` e na subpasta `03.10.2026`), com o mesmo conteúdo: ficaram as 24
    registadas, f0743 a f0766, e só se reporta.
  - **20:35, ele:** *"ótimo estou a trabalhar, apenas para te informar acho que o pré-visualizar não
    está a funcionar, pois por vezes está a misturar fotos e legendas. Reparei agora a acontecer nas
    viagens."*
  - **O que era:** a folha 28 das prévias que estava no endereço era antiga e tinha as 16 células
    trocadas (Veneza, Dubrovnik, Ilha Terceira e Iguaçu estão lá). As folhas 29 a 48 tinham subido
    por cima com o mesmo nome às 20:12. Primeiro disse-lhe que era o browser, e depois de medir
    corrigi: era a folha do endereço.
  - **20:45, Mesa versão 60:** as 48 folhas com o conteúdo no nome. A montagem dele ficou intacta.
  - **Ele, a meio:** *"adicionalmente acrescentei uma música, mas não a consegui ouvir quando a incluí
    na mesa de montagem num separador."* É a do cartão do clip 102. A cópia de som ainda não estava
    publicada, porque a vigia esteve parada meia hora enquanto eu tratava do pré-visualizar; entrou
    na versão 60.
  - **Por lhe perguntar, se voltar a ver:** parado e a saltar de clip, o quadro fica um instante no
    clip anterior e a barra já diz o seguinte. Corrige-se em pouco tempo, se ele quiser.
  - **23:30, ele:** *"Antes de saltar o clip confirma se as fotos estão todas na mesa."* Conferi: 771 fotos
    registadas e publicadas, nenhuma em falta na montagem (decisão 115). Entrou a foto das 23:31
    (f0771). Depois corrigi o salto de clip do Pré-visualizar: parado, aterra com o clip inteiro.
  - **4 de outubro, 00:20 a 01:45, o render final (decisão 116).** Os cinco pedidos dele (descida em todas
    as músicas, os foguetes na primeira foto da Clara, os dois contadores do fim, o lado a lado da 111 e
    «Convidados» nos créditos) e as respostas ao ouvir as provas:
    - *"tres da manhã é realista? [...] assim que acordar tenho video pronto"*, e logo a seguir *"not
      true"* e *"se mo mandares o rehearsal dentro de momentos eu vejo"*: ficou acordado a validar.
    - *"fiz meia dúzia de ajustes nos créditos"* (entrou também uma foto no filme, e o render das 00:37
      parou); *"Está fechada. Não vou mexer mais."*
    - *"Agora temos duas vezes Ana Faria, está mal. E não percebi a pergunta dos 4s e dos 2s. Naquela
      parte do início entre rei leão e celine não quero o fadeout no rei leão, nem o fade in, pois isso
      faria com que nem se ouvisse, mas no resto é ok."*
    - *"Mas parece-te bem 2s ou 4 é melhor?"* Respondi que 2 s; ficou.
    - *"No rei leão e celine é importante que fique smooth e não se note um corte estranho."* Ouviu
      quatro versões e escolheu: *"C"*, *"PARECE-ME E MELHOR"*.
  - **4 de outubro, 02:10 a 04:00, a foto trocada e a validação (decisão 117).** *"Quero fazer uma
    alteração de troca de uma foto por outra na mesa e voltas a lançar novo vídeo com máximo de
    qualidade"*; *"feito. já troquei"*; *"Faz testes de validação [...] mantendo sempre real a pessoa, as
    feições. [...] este vai ser o vídeo que vai ficar na cabeça de 131 no nosso casamento."* O ficheiro
    da sala é o `v3_2026-10-04_0243_com_creditos_FINAL.mp4`.
- **Fica para depois, palavras dele:** «trocar a foto x por 5-3» (*"vamos vigiar, mas para já
  ignora"*). A `01-NOVAS/5-3.jpg` é igual à original (f0009), que já está no clip 24.
- As fotos de 04:29 a 04:31 estavam nas Transferências e foram copiadas para a `01-NOVAS`, sem mexer
  nas originais. A `04.15.49` está na `01-NOVAS` mas não está na lista dele: fica registada e não se
  usa.
- **Feito às 05:07.**
  - **Fotos:** `atualizar_fotos.py`, 741 fotos, build `20261003-050017`.
  - **Mesa versão 55:** publicada com a página, as 47 folhas e as cópias das 4 músicas novas (Billy
    Joel, Edward Sharpe, Olivia Dean, Vance Joy).
  - **Trocas:** escritas na base às 05:06 (versão 2373 para 2374). Mudaram as 15 fotos, em 12 clips
    da demo_v3: 16, 73 (Veneza, Dubrovnik, Terceira e Iguaçu), 99, 107, 122, 123, 124, 136, 137,
    138, 140 e 141.
    - As outras versões, os créditos e o estilo ficaram iguais.
    - As etiquetas passaram para as fotos novas; o ponto de foco não. A Terceira e o Iguaçu tinham
      foco e ficam sem ele.
    - A `21-28` é `21-28.jpeg`.
    - A `10-5` do filme é a f0004. A f0017, com o mesmo nome, é das versões da mãe e não se mexeu.
  - **A `2016_tIAGO_AMIGOS_FACULDADE_2...` (f0310):**
    - O inventário apanhou o conteúdo novo pelo mesmo caminho: 581 x 580, hash `8fc2e812`.
    - A versão Lanczos antiga (do conteúdo velho) foi recusada pela guarda das caras (2,39), e o
      filme usa o original novo.
    - É pequena, 581 x 580: o render amplia-a na hora.

**A letra da intro, 2 de outubro à tarde.** Ele: *"E já agora é possível alterar o tipo de letra da
intro da Marvel nos estilos como criaste?"* Mexe na 084 (e na 104), que diz que o Impact não se troca:
a foto vê-se por dentro das letras, e a máscara em Impact tem 250.835 pixéis contra 105.607 em Arial
Bold. Pergunta-se se ele quer abrir isto.
- Proposta: no Estilo, aba da intro, uma escolha de letra com «Impact (como está)» por omissão. Cada
  letra mostra quanto da foto se vê por dentro dela, medido como em setembro. Só se oferecem letras
  grossas o suficiente, e cada letra nova custa uns 3 minutos na montagem seguinte.
- Ele: *"Sim, abre a escolha da letra nesses termos."* Isto muda a 084 e a 104 (o Impact continua a
  ser a omissão, mas deixa de ser a única). A medida das letras que estão no PC corre já, só a ler
  (workflow `letra-da-intro-medir`, que propõe o limiar, a lista e o `data/fontes_intro.json`). A
  Mesa e o render ligam-se depois de as equipas que lá estão libertarem os ficheiros. Nada se
  descarrega sem ele dizer.
- **A medida (15:20).** 397 faces lidas, 124 candidatas medidas na caixa do nome em Impact a 288
  (1662 x 237 px). A medida de setembro reproduz-se ao píxel (250.835 e 105.607). O que decide é a
  letra ser estreita, não o peso: as pretas largas (Arial Black 44,9%, Segoe UI Black 52,9%) descem
  de corpo para caberem na largura.
- **O limiar:** dois terços da área do Impact (66,7%). Além disso, separar as maiúsculas a 15 m no
  mínimo da Mesa (132) e caber no máximo (309). A medida da 084 estendeu-se às maiúsculas (pares
  NN, HH e II), o que tira a Haettenschweiler (86%, mas só se lê a partir de 200).
- **As oito oferecidas:** Impact (como está), Bernard MT Condensed 80,9%, Showcard Gothic 78,7%,
  Gill Sans Ultra Bold Condensed 74,6%, Bahnschrift Bold Condensed 73,2%, Playbill 71,9%, Agency FB
  Bold 70,4% e Rockwell Condensed 68,2%. A Bebas Neue (67,4%) fica de fora pelo máximo de oito, e o
  & dela parece um E. Todas as medidas estão em `data/fontes_intro.json` (ficheiro novo, 124 letras).
  Folhas em `saida/discussao/intro/letras_oferecidas.jpg` e `letras_recusadas.jpg`.
- **O contrato** (para a construção): `est.estilo.intro.fonte = "<id>"`. Ausente ou `"impact"` é
  como está, igual ao byte. O tamanho da Mesa passa a querer dizer a altura do Impact a esse corpo,
  e cada letra vai a `round(corpo × corpo_que_cabe / 288)`. A linha «A HISTÓRIA DE» fica em Arial
  Bold, fora da troca. O nome da intro ganha `_<id>`, e as expressões que reconhecem as intros
  mudam em quatro sítios. A Mesa mostra a amostra por máscaras PNG feitas pelo próprio letreiro,
  porque o telemóvel não tem as letras do Windows. Pormenor em
  `scratchpad/letra_intro/proposta/`.

**O render de 1 de outubro, 23:11, o que ele pediu "depois de tudo":**
- **O filme:** `C:\casamento-video-media\saida\v3_2026-10-01_2311.mp4`, em resolução cheia, com
  `--fatias 6`.
- **Com os créditos:** `saida/discussao/ponto5/v3_2026-10-01_2311_com_creditos_telemovel.mp4`, 843 s, com
  o som a -21,8 LUFS.
- **A Mesa e a montagem:** a Mesa na rev 1042 e a Mesa 48 publicada. A montagem é igual à do render
  rápido das 21:03.
- **O que falta para o render final:** a cópia do filme com os créditos em resolução cheia, porque o
  `--colar` só faz a cópia do telemóvel. Fica para quando os créditos estiverem fechados.

**As prévias do mergulho em mais do que uma foto** (1 de outubro, 23:01):
`py -3.11 scripts/discussao/previa_mergulho_varias.py` faz `saida/discussao/mergulho/mergulho_varias_ABCD.mp4`
(73 s), as quatro em separado e uma folha de fotogramas. `--quadros` tira só os fotogramas.
- **Como se fez:** as mesmas 20 fotos das viagens (pilhas 116, 139 e 140) e três mergulhos em todas,
  com as funções do render.
- **Cada maneira, com 3 mergulhos:**
  - **A, mergulha e volta:** 18,0 s; cada mergulho a mais custa 4,9 s.
  - **B, passeia de perto:** 13,6 s; desliza 1,86 s entre vizinhas da fila de baixo, à velocidade do
    mergulho.
  - **C, voo entre fotos:** 13,9 s. No voo para o canto abranda quase até parar no ponto mais longe,
    porque encostado ao canto não tem para onde andar de lado.
  - **D, três grupos seguidos:** 14,9 s, sem código novo. As vizinhas nunca passam de 1,5x.
- **Para lhe dizer:**
  - cada foto mergulhada fica 0,8 s a encher o ecrã, contra a regra dos 3 s;
  - nas grelhas de 20 as vizinhas chegam esticadas a 2,5x perto do fim do mergulho (já acontece no
    render de hoje);
  - quando a câmara mostra a grelha inteira, a foto marcada é desenhada a partir do sprite reduzido
    cerca de 5 vezes sem filtro, e cintila um pouco. Vem do `render.compor` e corrige-se se ele usar o
    mergulho.
- **Depois de escolher:** constrói-se no render, no montar e na Mesa, e revêem-se os fins de frase
  (096).

**A troca de músicas** (1 de outubro): *"Estava a pensar trocar a música do Fome de Viagem com esta
música: Steppenwolf - Born To Be Wild (Lyrics). Não precisamos de fazer os ajustes todos de quando
começa e acaba, pois isso ainda vai ser ajustado mais tarde."* Feito na Mesa (rev 991), trocando as duas
de lugar:
- o cartão «Viagens» (clip 113) passa a ter o Steppenwolf, a entrar aos 0,55 s;
- a pilha do clip 137 passa a ter a Fome de Viagem, a entrar aos 2,7 s.

As trocas à volta das duas descem no corte até se medirem outra vez (096).

**A verificação do render de 1 de outubro:**
- **Som:** só ficam dois buracos de silêncio nas trocas (Clair para Who Let The Dogs Out, 0,25 s;
  Steppenwolf para Filhos do Dragão, 0,18 s); no de 30 de setembro havia cinco. São as "separações" de
  que ele não gostou? As seis que descem no corte não têm buraco, mas as duas músicas soam juntas 1,5 a
  2 s.
- **Para ele confirmar:**
  - "um família" (1:54), "periodo" (5:21) e "Advinham" (4:18);
  - a pilha "O primeiro veículo" com a legenda de baixo repetida, como a "Sintra" que ele tirou;
  - os textos das pilhas com 0,9 s cada;
  - a foto IMG_20260922 com a borda do papel à vista.
- **A legenda está no corpo 46,** abaixo do mínimo de 58 da 084. É informação nova sobre a 070, e
  diz-se-lhe.

**O que a referência ensina:** os modelos do vídeo dele são texto sobre imagem com letra de 21 a 27
px, e a 15 m nenhum se lê. Aproveita-se o movimento, não os tamanhos.

**Proposta, cerca de 68 s:**
- **6 cartões de nomes, 24 s:** uma foto de família em ecrã inteiro, com dois filetes que se abrem e o
  nome do grupo e das pessoas.
- **Parede de fotos a subir, 36 s:** umas 50 das 478 fotos que não entram no filme, com o nome do grupo
  numa faixa fixa.
- **Fecho, 8,5 s:** "CLARA & TIAGO" e a data desfocam até ao preto. A música acaba no fim verdadeiro
  dela.

**Cuidados:**
- **Nada de preto entre a história e os créditos.** A sala aplaude no primeiro preto, e os créditos
  passavam para ninguém.
- **A última música escolhe-se pelo fim dela.**

**Decisões dele:**
- **A duração.** Hoje o filme tem 833 s (fim do último clip do `v3.csv`, rev 903). Com cerca de 68 s de
  créditos fica em cerca de 902 s, praticamente no alvo de 900. Somam-se os 0,4 s dos nomes dos bebés
  e tira-se o que o 3.4 cortar. Como ele ainda mexe na ordem, refazer a conta a partir do `v3.csv`
  antes de lhe perguntar.
- **Quantas fotos na parede, e quais.** Ele pediu *"todas as fotos de família (...) que não consegui
  incluir"*. Das fotos que não entram, só 17 estão marcadas Família e 284 não têm pessoa marcada. A
  duração da parede depende disto.
- **A letra do título final.** Há duas hipóteses:
  - **Cormorant Garamond a 288,** a espelhar o Impact da intro. Mexe na regra de uma só letra de marca
    (084).
  - **Arial Bold,** sem mexer na regra.

**Trabalho de construção:**
- cartões de nomes, cerca de 1 dia;
- parede de fotos, 1,5 a 2 dias, a maior parte na Mesa, para ele escolher as fotos e os nomes;
- fecho, meio dia.

**Material:**
- **Rascunho das maquetes:** `scripts/discussao/rascunhos/ponto5_maquetes_creditos.py`. Lê os
  fotogramas da referência em `saida/discussao/ponto5/fotogramas_referencia`.
- **As fontes descarregadas** (licença OFL) estão em `C:\casamento-video-media\gerados\fontes\`. São
  a Cormorant e as outras que se compararam.
- **As vistas da quinta** (item M do "Em aberto") podiam servir para o fecho.
- **As vozes do pedido** (item I do "Em aberto", `gerados/pedido_pedacos`). Saíram da abertura na 079,
  e ele disse que há *"um ou outro bom material que posso incluir no fim do vídeo"*.
- **Os vídeos da `01-NOVAS` por decidir** (o botão "Vídeos por decidir" da Mesa). Só entram pela
  palavra dele.

---

## Construção, quando os cinco pontos estiverem fechados

Pela ordem:
1. **Mudar o código,** decisão a decisão, com os testes de cada ponto:
   - o `linha_tempo.py` (092);
   - o `montar_da_mesa.py` (092 e 093: o nome no preto e a foto 1,6 s depois; e o `LANG_LANG_IN`, se o
     3.4 passar);
   - o `render.py` (094, a descida por faixa da 3.3 com o sai_s e a cauda, a subida da que entra no
     tempo da cauda, o nome no preto e, se passar, o ponto 4);
   - o aviso do 3.3 no `montar_da_mesa.py`: uma troca com fim de frase cuja música chega ao corte
     noutro sítio do ficheiro;
   - o `som_para_mesa.py` e, se preciso, o `editor_base.html`, para a Mesa acompanhar;
   - uma nota nova no `montar_da_mesa.py` precisa da explicação em `EXPLICACOES`, que está no
     `scripts/som_para_mesa.py`;
   - a Mesa precisa de um campo novo na marca, para dizer que a entrada está num ataque (3.1).
2. **Correr o `py -3.11 scripts/testes.py` inteiro.** Há testes que guardam o byte e que vão mudar de
   propósito:
   - `teste_v3_sem_vozes_igual_ao_byte`, contra `data/montagens/referencia/`. Congela-se com
     `--congelar-referencia`;
   - a `ASSINATURA_CORPO_SINTETICO` do `teste_fatias_desenham_os_mesmos_fotogramas`. O corpo
     sintético tem uma fita com os dois nascimentos e um cartão, e refaz-se de propósito, como na 084.

   **As `ASSINATURAS_SEM_TEXTO` e `ASSINATURAS_TEXTO_36` dos grupos não podem mudar.** Nenhum dos
   cinco pontos mexe no desenho dos grupos: se mudarem, é uma regressão. Congelar é um ato deliberado,
   feito só depois de ele ver e ouvir.
3. **Publicar a Mesa primeiro,** pela ordem do `CLAUDE.md`:
   - refazer o retrato (`py -3.11 scripts/atualizar_fotos.py`) e montar a `saida/mesa.html`;
   - publicar com `files` e `root: saida`, as folhas de prévias incluídas, tirando com `null` as que
     sobrarem;
   - escrever o `montagem/publicacao` com `{build, quando, fotos}`, com `if_version` e o `build`
     copiado do `data/estado_fotos.json`.
4. **Ler o `montagem/estado2`** e confirmar que a revisão não desceu.
5. **Só então escrever na Mesa o que ele autorizou:**
   - os sete números da 095;
   - o ficheiro novo da intro, se o 3.4 passar;
   - a legenda da foto do Tiago, se ele disser que sou eu que a apago.

   Sempre ler primeiro, escrever com `if_version`, com `rev` a subir um e com o `quando` da hora da
   escrita, e dizer-lhe para recarregar a Mesa.
6. **Ler de novo o `estado2`** para `saida/leitura_mesaN`, e depois juntar, montar e `gerar_mesa.py`.
   Confirmar no `v3.som.csv` as entradas da 095. Publicar outra vez, se o som da Mesa mudou, e depois
   de publicar ler o `estado2` outra vez.
7. **Render só quando ele pedir,** e com `--so-telemovel` até ele dizer que é a versão final. Antes de
   cada render, perguntar pelos textos marcados (082).
8. **Antes do render final, rever o 3.3** (096): correr o `ponto3_3_frases.py`, medir outra vez as
   trocas que mudaram e mostrá-las ao Tiago. É também o que se faz depois de fotos novas.

---

## Fora dos cinco pontos, adiado por ele

- **O render com as imagens corrigidas:** *"Não quero fazer já isto"*, a 27 de setembro.
- **O cartão vazio que abre a demo_v3:** adiado a 27 de setembro. Volta no 3.4.
- **O emoji no texto "E porque não ganhar uns € como modelo?":** adiado.
- **As fotos quase iguais `DSC02953` e `DSC02954`:** parece resolvido por ele na rev 903. A `DSC02954`
  já não está na montagem, e a `DSC02953` está num lado a lado com a `DSC_0149`. Confirmar com ele.
- **A largura da tela:** pergunta para o DJ ou para a quinta (ver o ponto 4).
- **Os textos marcados pela Mesa (082):** *"Para já ficam como estão, ajusto no fim."*
- **Commits:** o trabalho até à decisão 100 está no `aa74fd7`, e o mergulho da outra sessão (101) no
  `68c18b7`, trazido para o `main` a 30 de setembro a pedido dele. Só se faz commit quando ele pedir.

---

## Ideia nova, 30 de setembro: uma intro alternativa ao estilo do 007 (em avaliação, nada decidido)

Com o vídeo "All Daniel Craig 007 Gunbarrels (2006-2021).mp4" dos Downloads dele (67,5 s, 1280x720):

> *"Gostava de avaliar a possibilidade uma intro alternativa inspirada neste video do 007. Basicamente
> a minha ideia era ser eu de um lado e Clara do outro que nos encontramos no meio e mandamos um beijo
> em vez de enviar um tiro e depois vai para o nome do video História da Clara e do Tiago. O caminhar
> gostei mais do video mais recente, mas o derivador para o nome o Quantum of Solace é o melhor."*

- **A caminhada de referência:** No Time To Die, dos 50 aos 59 s do ficheiro. Dois pontos brancos,
  cano cinzento com estrias, silhueta preta sobre círculo claro.
- **A passagem de referência:** Quantum of Solace, dos 13,5 aos 19,5 s. O círculo fica vermelho, entram
  arcos brancos a rodar que se fecham numa esfera e essa esfera vira o Q do título.
- **Depende de filmagem deles:** não há vídeo dos dois a caminhar. Silhuetas paradas recortadas de
  fotos não andam.
- **Mexe em decisões fechadas se substituir a Marvel:** 097 (passagem da intro para o contador) e 084
  (o Impact aparece uma vez, no letreiro da intro).

**1 de outubro, ele:** *"Ou seja não consegues tu criar com base nas nossas imagens, mesmo que seja aquela
opção mais escura"*. Fez-se a prévia sem filmagem: `py -3.11 scripts/discussao/intro_007.py` escreve
`saida/discussao/intro_007/previa_intro_007.mp4` (12,7 s; `--quadros` tira só fotogramas soltos).
- Silhuetas recortadas da f0166 (`30Abril18_125.jpg`) com o GrabCut, espelhadas para o Tiago ficar à
  esquerda. Deslizam com balanço de passo; as pernas não andam. No fim encostam as cabeças (2,4°).
- Som do próprio vídeo de referência: No Time To Die dos 51,10 aos 57,15 s (pára antes do tiro, que
  está aos 57,2) e Quantum of Solace dos 13,20 aos 19,85 s (depois do tiro, que está aos 12,5). Ganho
  direto para -21,9 LUFS.
- Sem sangue: o círculo fica vermelho e apaga-se. Os arcos fecham-se em duas alianças, e o título
  "HISTÓRIA DA CLARA / E DO TIAGO" entra em escada pela direita, no letreiro do render.

**1 de outubro, ele, depois da prévia 1:** *"Para já mantemos a da Marvel, mas ainda assim acho que esta tem
potencial para aparecer antes dos créditos, mas para isso tínhamos de a melhorar, consegues acrescentar
efeitos e movimento que se assemelhe o máximo possível à qualidade dos originais? Sabendo que estamos
apenas a fazer um demo, mas acredito no potencial."*
- **A intro da Marvel fica.** Esta passa a ser candidata para antes dos créditos, ou seja, ponto 5.
- **Prévia 2:** `py -3.11 scripts/discussao/intro_007_v2.py` escreve `previa_intro_007_v2.mp4` (12,7 s,
  17,6 MB; `--quadros` tira só fotogramas soltos). A prévia 1 fica como estava, para se poder comparar.
  O que tem a mais: o cano calculado em perspetiva (estrias em hélice, textura de metal, luz que vem
  da boca), a câmara a entrar no cano, as pernas dele a levantar e a saia dela a balançar, o reflexo
  no chão, o clarão quente no beijo, a cortina vermelha ondulada, os arcos em 3D com rasto, um brilho
  a passar no título e o título a fechar numa linha. Tem também desfoque de movimento, brilho, grão e
  barras 2,39:1.
- **As silhuetas passaram a ser simétricas,** cada uma feita do lado que se vê inteiro na f0166: na
  foto o braço dela tapa a manga dele, e o corte direito deixava uma aresta a pique. As pernas dele
  foram refeitas linha a linha, porque o muro entre as pernas tinha ficado meio dentro do recorte.
