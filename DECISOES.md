# DECISOES

Registo cronológico das decisões deste projeto. Mais recente em baixo.

Serve para retomar o trabalho noutra sessão ou noutro dispositivo sem perder o
fio. Uma decisão registada aqui está fechada e não se reabre, salvo se surgir
informação nova que a invalide, e nesse caso escreve-se uma entrada nova que
substitui a anterior de forma explícita.

---

## Formato de registo

Uma entrada por decisão, por esta ordem:

```markdown
### AAAA-MM-DD | NNN | Título curto da decisão

**Decisão:** o que ficou decidido, numa frase afirmativa.

**Razão:** porquê. Se houver alternativa rejeitada, dizer qual e porquê não.

**Consequência:** o que muda na prática, que ficheiros ou fases são afetados.

**Quem:** Tiago, Clara, ou Tiago e Clara.

**Substitui:** número da entrada anterior, ou vazio.
```

Regras do registo:

- `NNN` é sequencial e nunca se reutiliza, mesmo que a entrada seja substituída.
- Data em formato AAAA-MM-DD, sempre absoluta, nunca "ontem" ou "na semana
  passada".
- Registar também as decisões de não fazer. "Fica de fora" é uma decisão.
- Não registar aqui operações de rotina nem resultados de scripts. Isto é para
  decisões, não para histórico de trabalho, que está no Git.
- As decisões em aberto vivem na secção "Em aberto", em baixo. Quando forem
  fechadas, passam a entrada numerada e saem de lá.

---

## Decisões

### 2026-09-10 | 001 | As marcas de assinatura da mãe da Clara atravessam todas as versões

**Decisão:** as três versões herdam as marcas visuais e sonoras que a mãe da
Clara criou. Em concreto, a abertura com fanfarra de estúdio e a vinheta que
anuncia o início de uma vida. As versões podem reordenar, aparar e mudar o
ritmo, mas não podem apagar a assinatura dela.

**Razão:** a extração do `.wlmp` mostrou que aquilo não são efeitos avulsos, é
um sistema construído de propósito. Fanfarra da 20th Century Fox a abrir o
vídeo, fanfarra da Paris Filmes ao contrário a abrir a secção do Tiago, e o
mesmo troço de `Candidato a vereador` (2:53 em diante) por cima dos dois
cartões "Era uma vez", a rimar a abertura de cada uma das duas vidas. Se as
versões novas perderem isto, deixam de ser o trabalho dela reordenado e passam
a ser um vídeo diferente, o que contraria o princípio do briefing.

**Consequência:** cada ficheiro em `data/montagens/` tem de conter as marcas.
Torna crítico recuperar `Paris Filmes Reversed.MP3` e `aleluia.mp3`, os dois
ficheiros que faltam em disco e que são precisamente parte da assinatura.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 002 | As versões constroem-se por tentativa e erro, não por desenho fechado

**Decisão:** as três versões arrancam a partir de uma votação única no
`decisoes.csv` e de ficheiros de montagem separados em `data/montagens/`, mas
sem assumir que essa arrumação aguenta até ao fim. Se uma versão precisar de
se soltar para ficheiro próprio, solta-se.

**Razão:** as três estruturas são suficientemente diferentes uma da outra para
que a partilha de dados possa vir a estorvar em vez de ajudar, sobretudo a
versão de flashback, que depende de datas e não de secções. Fechar a
arquitetura agora seria decidir sem informação.

**Consequência:** a fase de inventário produz o que serve as três (metadados,
datas, pessoa, evento, resolução) e adia o que é específico de cada uma.
Rever esta decisão depois da primeira montagem completa.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 003 | Preparar o material para projeção contra cortina

**Decisão:** o suporte final ainda não está escolhido, entre televisão e
projeção contra cortina. Até haver escolha, todo o material é preparado para
projeção, que é o cenário mais exigente.

**Razão:** a assimetria de custo é clara. Material preparado para projeção
fica bem numa televisão. Material preparado para televisão obriga a refazer
todos os recortes se depois formos para cortina, porque o tecido baixa o
contraste e come detalhe.

**Consequência:** no inventário, limiar de resolução mais apertado e
sinalização das fotos que precisam de recorte de aproximação. Texto no ecrã
dimensionado para leitura a 15 metros.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 004 | Timeline a 1920x1080, 25 fps

**Decisão:** o projeto e a exportação final são 1920x1080 a 25 imagens por
segundo.

**Razão:** norma europeia, compatível com qualquer projetor ou televisão que
apareça na noite, sem conversões de última hora. Subir de 1080p não acrescenta
nada, porque 44 por cento das fotos estão abaixo de 1280 px de largura e o
excesso de resolução só amplia o defeito.

**Consequência:** fixa os parâmetros do FCPXML e do projeto no Resolve.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 005 | Número de camas musicais varia conforme a versão

**Decisão:** a `v1_fiel` fica com 7 ou 8 camas musicais. A `v2_funil` e a
`v3_flashback` ficam com 5. As vinhetas de assinatura da decisão 001 não
contam para esta contagem e existem em todas as versões.

**Razão:** a v1_fiel existe para ser fiel, e cortar de 17 faixas para 5
esvaziava o propósito dela. As outras duas são estruturas novas, onde cada
mudança de faixa marca um salto de bloco, e aí 5 dá cerca de 180 segundos por
faixa, que é a duração natural de uma canção e evita cortes a meio. Cinco
permite manter uma canção com o nome da Clara e uma com o nome do Tiago, mais
três de ligação, preservando a mecânica de espelho que ela construiu.

**Consequência:** cada ficheiro em `data/montagens/` traz o seu próprio plano
musical. As mudanças de faixa têm de coincidir com mudanças de bloco.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 006 | Fanfarra aparada a 10 ou 12 segundos nas versões novas

**Decisão:** na `v1_fiel` a fanfarra da 20th Century Fox mantém-se inteira,
20,4 segundos, porque essa versão segue a estrutura dela. Na `v2_funil` e na
`v3_flashback` é aparada para 10 a 12 segundos, guardando a subida final e o
acorde de resolução.

**Razão:** nas versões novas o bloco de abertura tem 45 segundos e tem de
carregar também o flash-forward, o cartão e o corte seco para a foto de bebé.
Vinte segundos de fanfarra comiam quase metade desse orçamento e deixavam a
abertura apressada. Dez a doze segundos chegam para calar a sala, que é a
função prática do clip, e sobram cerca de 33 segundos para o resto respirar.

**Consequência:** afeta apenas o bloco 0 das duas versões novas.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 007 | Fica tudo em fotografia, não entra vídeo

**Decisão:** o filme é feito só de fotografia. Não entra imagem em movimento,
com a única exceção da fanfarra de abertura, que é uma vinheta de assinatura e
não conteúdo.

**Razão:** informação nova vinda da extração do `.wlmp`. A secção 8 do
briefing dizia "há 2 MP4, decidir se entram", mas os dois ficheiros não são
matéria-prima: um é a exportação final dela, ou seja o resultado, e o outro é
a própria fanfarra. Em 23 minutos e meio de timeline há um único clip de
vídeo, e é a fanfarra. Não existe um segundo de imagem em movimento da Clara e
do Tiago em toda a pasta de media, e o Tiago confirmou que também não tem.

**Consequência:** fecha o ponto C da secção 8 do briefing. As colunas `in_s` e
`out_s` do `decisoes.csv` ficam vazias em todas as linhas. O bloco de abertura
em flash-forward resolve-se com as fotos do noivado, `20260101_011410.jpg`
(3000x4000 px, a maior resolução de todo o material) e `20260101_011607.jpg`,
que são as da árvore de Natal com a mão e o anel.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 008 | Pasta 01-NOVAS para fotos acrescentadas, verificada a cada sessão

**Decisão:** existe `C:\casamento-video-media\trabalho\01-NOVAS\` onde o Tiago
larga fotos que não estavam no vídeo original. Em cada sessão essa pasta é
verificada contra o `data/inventario.csv`, as imagens novas são analisadas e
acrescentadas, e o número encontrado é sempre reportado, mesmo quando for zero.

**Razão:** o material da mãe da Clara é um conjunto fechado de 305 fotos, mas
o Tiago tem outras que podem valer a pena. Sem um sítio definido e sem uma
verificação sistemática, fotos novas entram por mensagens soltas e perdem-se
entre sessões.

**Consequência:** regra acrescentada ao `CLAUDE.md`, em "Fazer no início de
cada sessão". A pasta tem um `LEIA-ME.txt` com as instruções. Não é preciso
organizar nem renomear nada, e podem existir subpastas. Uma foto que já lá
esteve nunca se apaga: se não for usada, fica registada como não usada.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 009 | Upscaling não destrutivo, para pasta separada

**Decisão:** as fotos que não chegam para encher 1920x1080 são ampliadas por
`scripts/upscale.py` para `C:\casamento-video-media\upscaled\`. Os originais
nunca são tocados nem reescritos. Foram ampliadas 134 imagens.

**Razão:** ampliar não remove informação, portanto não destrói a foto. O que
destrói é o sharpening a mais, que cria halos nos contornos, e a recompressão
agressiva. Por isso a cadeia é lanczos sobre `zscale`, seguido de `cas`
(sharpening adaptativo ao contraste) a força 0,30, que é fraca de propósito, e
JPEG de qualidade 2. Cada foto é ampliada só o necessário para encher o ecrã
mais 15 por cento de folga para o pan e zoom, porque cada décimo a mais de
ampliação é mais suavidade e mais halo.

**Consequência:** o script recusa-se a correr se o destino cair dentro da
pasta de trabalho, e nunca reescreve um ficheiro que já exista. Guarda seis
comparações lado a lado em `upscaled\_comparacoes\`, com o mesmo enquadramento
sem tratamento e com tratamento, para julgar o resultado a olho.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 010 | As datas EXIF das digitalizações são descartadas

**Decisão:** o ano de uma foto nunca vem do EXIF quando a imagem foi
produzida por um scanner. Nesses casos o ano vem das legendas da mãe da Clara,
ou é estimado pela posição dela na timeline, ou fica em branco.

**Razão:** 87 das 306 imagens saíram de `HP Scanjet djf21` ou `HP ojj3600`. A
data EXIF dessas é o dia da digitalização. Sem esta regra, fotos de bebé
ficavam datadas de 2013 e 2014, e a versão cronológica saía completamente
errada. Foi detetado porque o bloco do Tiago, que abre com o cartão "nasceu em
1995", tinha a primeira foto datada de 2013.

**Consequência:** 244 das 306 fotos têm ano, 80 por cento. Destas, 86 são
estimadas pela ordem dela e vão marcadas como tal em `fonte_ano`. Em 54 casos
recusei estimar, porque as âncoras à volta andavam para trás no tempo, sinal
de que ali a ordem dela é temática e não cronológica. Inventar um ano nesses
casos seria pior do que deixar em branco.

**Quem:** decisão técnica, tomada por mim e registada para o Tiago poder
contestar.

**Substitui:**

---

### 2026-09-10 | 011 | O cartão dela sobre 2011 está factualmente errado

**Decisão:** a cronologia do casal é a do briefing e a do Tiago: conheceram-se
na Escola Secundária de Valongo em 2009/2010, e começaram a namorar a 20 de
maio de 2012. O cartão da mãe da Clara que diz "Em 2011 a Clara e o Tiago
conheceram-se" está errado e não se reproduz tal e qual em nenhuma versão.

**Razão:** o Tiago confirmou explicitamente que não se conheceram em 2011 e
que o namoro começou em 2012. A decisão 001 protege a assinatura dela, as
fanfarras e as vinhetas, não protege um erro de facto sobre a vida deles. São
coisas diferentes: preservar o gesto não é preservar a data errada.

**Consequência:** a semente de interpolação de anos do bloco "O encontro"
passou de 2011 para 2010 em `scripts/gerar_decisoes.py`. Na `v1_fiel`, que
mantém os cartões dela, o texto deste cartão tem de ser reescrito com a data
certa, ou reescrito sem data nenhuma. Fica por decidir qual, na montagem.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 012 | Sem Microsoft Office, nada de edição manual de CSV

**Decisão:** o Tiago não tem Microsoft Office. Os CSV continuam a ser o
formato de dados, porque é o que funciona no Git e no telemóvel, mas ele nunca
os edita à mão. Toda a introdução de dados passa por páginas HTML geradas por
mim, que abrem em qualquer browser, ou por instruções em linguagem natural que
eu converto em alterações ao CSV.

**Razão:** um CSV de 306 linhas no Notepad é inutilizável. E a fase 2 do
briefing já previa instruções em linguagem natural, portanto isto não é um
desvio, é uma confirmação do plano com uma restrição técnica a mais.

**Consequência:** primeira ferramenta feita, `scripts/ferramenta_anos.py`, que
gera `C:\casamento-video-media\ferramentas\anos.html` com as fotos embutidas
em base64, portanto autónoma e sem dependências. Todas as ferramentas futuras
seguem o mesmo padrão: HTML autónomo, grava um ficheiro pequeno que eu leio.

**Quem:** Tiago.

**Substitui:**

---

## Em aberto

Não assumir nenhuma destas sem decisão explícita do Tiago.

### D. Ritmo de rajada, a decidir depois de um teste em vídeo

**Estado:** o Tiago decidiu não decidir no escuro. Na fase de montagem faço um
teste de 15 segundos com fotos reais de amigos ou viagens, e ele decide a ver.

O que o teste tem de responder, e que não se resolve a discutir:

1. Duas ou três fotos ao mesmo tempo ainda se leem a 15 metros numa cortina?
2. O deslize lateral cansa ao fim de dez fotos?

Contexto abaixo, para não se perder.

A regra fixa do briefing diz "nunca menos de 3 segundos por foto", e existe
por causa da sala de jantar, com gente de costas e a conversar. Uma rajada de
fotos a 1 segundo entra em conflito direto com ela.

O Tiago propôs uma saída que possivelmente resolve o conflito em vez de o
contornar: **as fotos não desaparecem quando entra a seguinte**. Uma foto
entra ao centro, e quando chega a próxima desloca-se para o lado em vez de
sair. Ficam duas ou três visíveis ao mesmo tempo, em movimento contínuo.

Se assim for, cada foto continua no ecrã 3 segundos ou mais, apenas deixa de
estar centrada durante todo esse tempo. A cadência de entrada fica rápida e
mexida, a permanência mantém-se dentro da regra, e não é preciso abrir
exceção. Fica por confirmar em teste real: legibilidade a 15 metros com duas
ou três fotos simultâneas, e se o movimento lateral cansa ao fim de 10 fotos.

Aplicação prevista: amigos, colegas, viagens, festas. Nunca em retratos nem
em fotos de infância a solo.

### G. Recuperar os dois ficheiros de som em falta

`Paris Filmes Reversed.MP3` e `aleluia.mp3` são referidos no `.wlmp` mas não
existem em disco. Os dois pertencem à assinatura protegida pela decisão 001: o
primeiro é a fanfarra ao contrário que abre a secção do Tiago, a espelhar a da
20th Century Fox que abre o vídeo.

Ação pendente: pedir os dois à mãe da Clara. Se não aparecerem, decidir se se
reconstrói o efeito com outra fanfarra invertida ou se se abandona o espelho.

### H. Suporte de exibição, decisão final

Fechada por agora pela decisão 003, que manda preparar para o caso mais
exigente. Reabre quando o Tiago souber se é televisão ou projeção, e nessa
altura, se for televisão, há trabalho de recorte que se pode poupar.
