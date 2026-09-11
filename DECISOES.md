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

### 2026-09-10 | 013 | Os anos indicados pelo Tiago são indicativos, não factos

**Decisão:** os 95 anos que o Tiago preencheu ficam em `data/anos_tiago.csv` e
entram no inventário, mas marcados como `fonte_ano = Tiago (indicativo)`. Não
substituem uma data EXIF de máquina, que é mais fiável. Toda a interface os
mostra com etiqueta própria, verde, com o aviso "por validar com a Clara" ao
lado.

**Razão:** o próprio Tiago disse que não são finais e que quer validar com a
Clara. Um palpite dele vale muito mais do que nada, porque serve para ordenar
uma foto na década certa, mas se ficar indistinguível de uma data apurada
ninguém consegue mais tarde saber o que foi verificado e o que não foi.

**Consequência:** a cobertura de ano subiu de 80 para 84 por cento. A hierarquia
de fiabilidade, da mais forte para a mais fraca, é: EXIF de máquina, ano ou
idade escritos por ela nas legendas, ano no nome dado pelo Tiago, indicação do
Tiago na ferramenta, estimativa minha pela ordem da timeline dela.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 014 | Os id do inventário são estáveis e amarrados ao caminho

**Decisão:** o `id` de cada imagem no `inventario.csv` nunca muda. É atribuído
uma vez, guardado, e amarrado ao par pasta mais nome de ficheiro. Fotos novas
recebem números a seguir ao maior já atribuído.

**Razão:** as ferramentas HTML gravam por `id`. Quando entraram as 47 fotos
novas, a numeração sequencial teria deslocado tudo e os 95 anos do Tiago
passariam a apontar para as fotos erradas, em silêncio.

Amarrar ao conteúdo, por sha256, foi tentado e está errado: `10-1.jpg` e
`10-1 (2).jpg` são byte a byte iguais mas são duas entradas distintas do
inventário, e partilhar o id fazia desaparecer uma delas. A chave certa é o
caminho.

**Consequência:** os 306 id originais foram verificados um a um contra a versão
commitada e nenhum mudou de ficheiro. Renomear ou mover uma foto dentro de
`trabalho\` quebra o vínculo, por isso não se renomeia nada depois de
inventariado.

**Quem:** decisão técnica, registada para o Tiago poder contestar.

**Substitui:**

---

### 2026-09-10 | 015 | As 47 fotos novas trazem informação nos nomes e nas pastas

**Decisão:** a organização que o Tiago deu à `01-NOVAS` é tratada como dado,
não como arrumação. O nome da pasta define a coluna `pessoa`, o prefixo de ano
no nome do ficheiro define o ano, e as instruções de edição que ele escreveu
nos nomes são guardadas na coluna `nota`.

**Razão:** ele escreveu coisas como "ficar apenas com a foto no canto superior
esquerdo onde está o Tiago" e "há pessoas a cortar, talvez manter apenas a
Sandra, remover o Miguel". Isso são decisões de enquadramento já tomadas, e
perder-se-iam se eu tratasse os nomes como texto morto.

**Consequência:** `pessoa` vinda da pasta do Tiago tem prioridade sobre a
deduzida dos blocos da mãe da Clara, que é pouco fiável depois de 2012.

As pastas `*_files`, resultantes de páginas web guardadas, são ignoradas por
inteiro. São 57 imagens de interface e miniaturas de feed, não são fotos do
casal. Os vídeos do Facebook que o Tiago tentou guardar não vieram no processo,
ficou só o HTML.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-10 | 016 | Uma sugestão não tocada nunca conta como palavra do Tiago

**Decisão:** só conta como indicação do Tiago um valor que ele escreveu de
raiz, corrigiu, ou confirmou explicitamente. Um valor sugerido por mim que ele
simplesmente não tocou continua a ser estimativa minha. Todas as ferramentas
passam a gravar uma coluna `origem` com um de quatro valores: `escrito`,
`corrigido`, `confirmado`, `intacto`. A leitura só aceita os três primeiros.

**Razão:** o botão de gravar da primeira ferramenta exportava todos os campos
com valor, incluindo os 81 que eu tinha pré-preenchido com estimativas minhas.
Eu carimbei os 95 como indicação do Tiago. Ele deu por isso e corrigiu-me:
"estás a assumir que nos casos em que não editei fui eu que disse e isso é
mentira".

Estava certo. Dos 95, apenas **14** eram dele: 9 escritos de raiz e 5
correções a estimativas minhas. Os outros 81 eram meus, disfarçados da palavra
dele.

Isto não é um pormenor de contabilidade. Todo o valor deste registo está em
saber, mais tarde, o que foi verificado por uma pessoa e o que foi deduzido por
uma máquina. Uma estimativa minha com a assinatura dele é pior do que uma
estimativa assumida, porque ninguém a vai voltar a questionar.

**Consequência:** `data/anos_tiago.csv` reduzido de 95 para 14 registos, com
coluna `origem`. Os 81 voltaram a ser tratados como estimativa e vão marcados
como tal. A cobertura de ano manteve-se nos 84 por cento, o que muda é a
honestidade da etiqueta, não o número.

A ferramenta ganhou um botão `confirmo` por foto, para ele poder dar aval a uma
sugestão sem a alterar, e um aviso no topo a explicar que não tocar não é
concordar. Cada cartão mostra em texto o que aconteceu: "escrito por ti",
"corrigido por ti", "confirmado por ti", ou "sugestão minha, não tocaste".

**Quem:** Tiago.

**Substitui:** 013, que dizia que os anos indicados por ele eram 95.

---

### 2026-09-10 | 017 | Os quatro tratamentos visuais são todos aprovados

**Decisão:** os quatro tratamentos (A fundo desfocado, B colagem, C rajada, D
pilha) ficam todos disponíveis e podem ser usados em momentos diferentes do
vídeo, para ir variando o andamento.

**Razão:** o problema do vídeo original é andamento único do princípio ao fim,
com uma só transição e um só movimento. Ter quatro tratamentos distintos ataca
isso na raiz. O Tiago viu-os e aprovou-os todos.

**Consequência:** o vocabulário de ritmo do `CLAUDE.md` passa a mapear para
estes quatro. Falta decidir a atribuição, ou seja que tratamento serve que
bloco, e isso depende da montagem.

Nota sobre o tremor que ele apontou na primeira versão: eram dois defeitos meus
de implementação, não escolhas. Quantização a inteiro da posição e do tamanho
em cada fotograma, e reamostragem repetida a partir do original. Corrigido com
transformação afim de sub-pixel sobre uma imagem preparada uma só vez. Na
rajada o tremor era deliberado e foi removido.

**Quem:** Tiago.

**Substitui:** fecha o ponto D, que estava em aberto.

---

### 2026-09-11 | 018 | A versão fiel desdobra-se em três degraus

**Decisão:** a `v1_fiel` passa a ser três versões encadeadas, cada uma a
acrescentar exatamente uma coisa à anterior:

| | O que muda | Duração |
|---|---|---|
| `v1a` | Só durações e transições. Ordem, textos e cartões intactos. | 18:20 |
| `v1b` | Mais fundo desfocado nas verticais e rajada nas corridas. | 15:00 |
| `v1c` | Mais as correções narrativas de `docs/ENCADEAMENTOS.md`. | 15:56 |

**Razão:** o Tiago quis poder ver o efeito de cada alteração isoladamente, em
vez de receber uma versão nova e ter de adivinhar o que mudou. Cada degrau
responde a uma pergunta: a v1a mostra o que se ganha só com ritmo, a v1b o que
os tratamentos acrescentam, a v1c o que a narrativa muda.

**Consequência:** a v1a ficou nos 18:20 e não nos 900 segundos do briefing,
por decisão dele, depois de eu mostrar que não há crossfade nenhum que meta
297 entradas em 900 segundos sem violar a regra dos 3 segundos. **A v1b
resolve isso e cabe nos 900 exatos**, porque a rajada liberta 117 segundos.
A v1c volta a passar, para 15:56, porque as 16 entradas novas acrescentam 57
segundos. Fechar a v1c nos 900 obriga a rajada agressiva ou a largar uma das
edições.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-11 | 019 | A rajada aplica-se a repetição temática, nunca a blocos de relação

**Decisão:** só viram rajada as corridas onde a leitura é coletiva, ou seja
onde ninguém precisa de ler cada foto: caminhadas, colegas de trabalho, poses
do mesmo género. Nunca entram em rajada os blocos de relação.

Certas, 23 fotos: Caminhadas pelo Parque das Serras do Porto, colegas de
trabalho dela, "Vendo o mundo de pernas p'ró ar", colegas de trabalho dele.

Nunca, 20 fotos: a corrida sem legenda de "Cumplicidades". São o casal junto e
são o centro emocional do filme.

Por decidir, 18 fotos: "Com o Henrique (o mano)", "Com o pai" e "E le
glamour". São relação mas são repetitivas. Ficam marcadas na coluna `nota` do
`v1b.csv` e entram com `--agressivo`.

**Razão:** numa versão anterior deste cálculo eu classifiquei as 20 fotos de
"Cumplicidades" como sendo do Baile de Finalistas, por um erro no detetor de
corridas, e propus acelerá-las. O Tiago duvidou do número e tinha razão.
Acelerar ali seria acelerar precisamente a parte que deve respirar.

**Consequência:** com as 23 certas a v1b cabe nos 900 segundos, mas sobram só
50 segundos para dar ênfase, portanto a ênfase que a mãe da Clara deu fica
quase toda achatada. Com as 41 sobram 96 segundos e a ênfase máxima sobe de
4,25 para 6,81 segundos. É essa a escolha.

**Quem:** decisão técnica com o critério registado, para o Tiago poder
contestar a fronteira.

**Substitui:**

---

## Em aberto

Não assumir nenhuma destas sem decisão explícita do Tiago.

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
