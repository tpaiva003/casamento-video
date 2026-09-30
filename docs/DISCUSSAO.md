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

**Os números em vigor** estão em `data/fins_de_frase.csv`, que é o que a montagem e o render usam, e
o que a revisão lê. A tabela da 096 é a de 29 de setembro. A 30 mudaram duas trocas: o Rei Leão para o
Lang Lang e a Ana Faria para a Clair (decisão 100).

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
- **O trabalho destes dias não está em nenhum commit.** Só se faz commit quando ele pedir.

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
