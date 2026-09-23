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

### 2026-09-11 | 020 | Os bilhetes de admiradores saem de todas as versões

**Decisão:** as cinco fotografias de bilhetes manuscritos de admiradores da
Clara (`8-6`, `8-7`, `8-8`, `8-9`, `8-9-1`) não entram em nenhuma versão. Saem
com as legendas que a mãe da Clara lhes pôs, porque as legendas são sobre elas.
A aliança de argola de porta-chaves aos 8 anos (`8-9-2`) fica.

**Razão:** palavras do Tiago, "No demo 1a NÃO QUERO INCLUIR OS BILHETES DOs
namorados". A mãe da Clara construiu com eles uma piada de aula de português,
"Clube de Fãs", "Inspirou figuras de estilo", "Repetições e aliterações",
"Conotações", "Metáforas e hipérboles". A piada é boa e é dela, mas o vídeo
passa no jantar do casamento e são cartas de amor de outros homens para a
noiva, lidas por 140 convidados. É exatamente o que o filtro de tom existe para
apanhar. Um deles está datado de 14/11/07.

**Consequência:** a v1a passa de 297 para 292 entradas. Os 32,6 segundos
libertados NÃO encurtam o filme: são redistribuídos pelas fotos que ficam, que
passam a respirar mais. A duração mantém-se em 18:19. Se o Tiago preferir
encurtar o filme em vez de alargar as fotos, é `--total 1067`. A leitura fica
"criou uma grande empatia com colegas e amigos" e logo a seguir a aliança de
argola de porta-chaves, que é história de criança e não de namorado.
A lista vive em `scripts/excluidas.py` e é herdada pela v1b e pela v1c.

**Quem:** Tiago.

**Substitui:** abre a primeira exceção à regra da v1a de não cortar uma única
foto, fixada na decisão 011.

---

### 2026-09-11 | 021 | A rajada passa de 0,45 para 0,5625 segundos

**Decisão:** cada foto em rajada dura 0,5625 s, que são 14 fotogramas a 25 fps,
em vez dos 0,45 s anteriores.

**Razão:** o Tiago viu a demo e disse "as fotos dos desportos estão a mudar
muito muito rápido, aumenta a velocidade em 25% para testar". À letra, a frase
pede o contrário do efeito: fotos que mudam depressa de mais precisam de MAIS
tempo, não de menos. A leitura aplicada foi aumentar a duração em 25 por cento.
Fica registado por ser uma interpretação e não uma instrução literal.

**Consequência:** a v1b fica mais longa. Como ela tem de caber nos 900 s, o
tempo sai da folga de ênfase. Se não couber, o próximo passo é reduzir o número
de fotos em rajada, não voltar a acelerá-las.

**Quem:** Tiago, com a leitura registada acima.

**Substitui:**

---

### 2026-09-11 | 022 | O tremor era a coluna de fora a acender e a apagar

**Decisão:** cada fotografia é preparada com dois pixéis de margem antes de
entrar na composição de sub-pixel. A margem é preta quando o fundo é preto, e é
a repetição da fila de fora quando o fundo é a própria foto desfocada.

**Razão:** o Tiago viu "uma espécie de tremor que acontece especialmente do meu
lado esquerdo". A causa foi medida, não suposta. A composição pede à Pillow que
amostre a foto numa posição fracionária; na coluna de fora essa posição cai
ligeiramente fora da imagem e a Pillow não devolve ali uma mistura, devolve
preto, e devolve preto de repente. Medido num sprite branco puro:

| deslocamento | antes | depois | correto |
|---|---|---|---|
| 0,000 | 255 | 255 | 255 |
| 0,250 | 255 | 191 | 191 |
| 0,500 | 255 | 127 | 128 |
| 0,625 | **0** | 95 | 96 |
| 0,875 | 0 | 31 | 32 |

O zoom lento faz esse deslocamento variar ao longo do clip, e a coluna acendia
e apagava. Vê-se mais à esquerda porque numa foto 4:3 dentro de um ecrã 16:9 as
bordas verticais estão sempre dentro do quadro, enquanto as horizontais saem
fora e são cortadas.

**Consequência:** a correção é exata, não aproximada: passa a dar o valor
teórico da cobertura do pixel com um erro máximo de 1 em 255. O custo por
fotograma é zero, porque a margem é feita uma vez por clip. Todos os renders
anteriores têm o defeito e têm de ser refeitos. O `scripts/teste_estilos.py`
tem uma cópia própria da função e ainda não foi corrigido.

**Quem:** Tiago reportou, causa medida.

**Substitui:**

---

### 2026-09-11 | 023 | Cada montagem pode trazer a sua própria banda sonora

**Decisão:** existe `data/montagens/<nome>.som.csv`. Quando existe, o render
usa-o. Quando não existe, continua a ancorar a música à timeline da mãe da
Clara, que é o que a v1a quer.

**Razão:** as quatro demos saíram mudas e o Tiago viu logo. A música da v1a é
ancorada à FOTO sobre a qual ela a tinha posto, o que só funciona numa montagem
que mantenha a ordem dela. Numa demo de trinta segundos feita de fotos
escolhidas à mão não há âncora nenhuma, e o resultado era silêncio sem um único
aviso.

**Consequência:** cada demo leva a sua faixa de fundo e, por cima de cada
cartão, o troço de `Candidato a vereador` a partir de 2:53,7, que é a vinheta
dela. Isso mantém a assinatura da decisão 001 também nas demos.

**Quem:** Tiago reportou.

**Substitui:**

---

### 2026-09-11 | 024 | A pasta FINAIS escolhe por preferência, não por medição

**Decisão:** fica registado que o `consolidar.py` escolhe por ordem fixa
(restaurada, IA, lanczos, original) e nunca compara as versões entre si. O
`scripts/auditar_finais.py` faz a comparação que falta e diz onde a escolha
pode estar errada.

**Razão:** pergunta do Tiago, "tens a certeza que o que está na pasta finais são
as com melhor qualidade?". A resposta honesta é que o `consolidar.py` mede uma
coisa só, quanto é que a foto mudou face ao original, e isso serve para apanhar
invenção de feições, que era a outra preocupação dele. Não serve para dizer
qual das versões está melhor.

**Consequência:** a garantia sobre as feições mantém-se de pé e é forte. A
garantia sobre a qualidade passa a ter de ser verificada foto a foto, com
recortes lado a lado, e os empates vão a olho porque nenhuma métrica simples
separa "tirou grão" de "perdeu detalhe". Isso já falhou duas vezes, registado
no `verificar_upscale.py`.

**Quem:** Tiago perguntou.

**Substitui:**

---

### 2026-09-12 | 025 | O editor congelava 3,5 s por clique, e não era o prompt

**Decisão:** as seis folhas de miniaturas entram uma vez em classes CSS. Nenhuma
miniatura volta a levar a imagem no seu próprio atributo `style`. E nenhum
ficheiro deste projeto volta a usar `prompt()` ou `alert()`.

**Razão:** o Tiago disse que não conseguia marcar as pessoas nas fotos. Eu achei
que era o `prompt()`, que de facto é ignorado sem erro dentro da moldura
protegida onde a página publicada corre, e isso inutilizava criar pessoas,
mudar nomes e criar versões. Mas medido na página a correr, a causa maior era
outra:

| | Antes | Depois |
|---|---|---|
| Estilo de uma miniatura | 576 026 caracteres | 56 |
| HTML da grelha | 181,8 MB | 80 KB |
| Tempo por clique | 3 533 ms | 55 ms |

Cada uma das 357 miniaturas levava a folha inteira em base64 dentro do seu
`style`. A página congelava três segundos e meio a cada clique.

**Consequência:** marcar passa a ser instantâneo, e há um pincel: escolhe-se a
pessoa uma vez na barra por cima da biblioteca e depois é só carregar nas
fotos. O diálogo de gerir pessoas substitui o `prompt`. Verificado no browser:
pessoa criada, guardada, quatro fotos marcadas, filtro por pessoa a devolver
quatro de 357, e a desmarcar ao carregar outra vez.

**Quem:** Tiago reportou, causa medida.

**Substitui:**

---

### 2026-09-12 | 026 | A linha do tempo é horizontal e a data vive dentro dela

**Decisão:** existe `scripts/linha_tempo.py` com duas fitas horizontais. A dos
anos recua de 2026 para 1995 e desloca-se para a esquerda. A dos meses percorre
um ano e marca acontecimentos. A data do casamento é um **marco da fita**, não
uma legenda à parte.

**Razão:** palavras do Tiago. *"o facto de hoje 4 de outubro tem de ficar mais
dentro do timeline animation e não como uma espécie de legenda à parte"* e
*"Quero que o scrolling de timeline animation funcione na orizontal e não na
vertical e que como estamos a ir para trás se movimente para a esquerda até
chegar a 1995"*.

**Consequência:** a fita pára nos marcos e corre depressa entre eles, senão ou
não se lê nada ou perde-se a sensação de fuga. Mostra **uma etiqueta de cada
vez**: com todas acesas, entre 24 de agosto e 12 de setembro há três
acontecimentos e as palavras escreviam-se umas por cima das outras.

Três erros meus ficam registados porque nenhum deles dava aviso:

1. Escolher a marca mais próxima da cabeça de leitura parece o óbvio e está
   errado: o Côa e a Clara caem os dois em 24 de novembro, empatam, e o primeiro
   da lista ganhava sempre. **"Nasce a Clara" nunca chegou a aparecer no ecrã.**
2. Somar e subtrair 1 ao índice da paragem deixava a última marca de cada troço
   sem paragem, ou seja "Nasce o Tiago" não era dito no primeiro clip.
3. Formatar a fração do ano com quatro casas decimais excluía a própria marca
   que definia o fim do troço.

A correção foi deixar de fazer contas com índices: cada paragem sabe a que marca
pertence, ou a nenhuma.

**Quem:** Tiago definiu, erros medidos e corrigidos.

**Substitui:** a versão vertical da decisão 022 do contador.

---

### 2026-09-12 | 027 | Os foguetes tocam só nos dois nascimentos

**Decisão:** o troço de `Candidato a vereador` a partir de 2:53,7 entra duas
vezes e só duas, em cima dos dois anúncios de nascimento. O instante é
perguntado à própria linha do tempo, não escrito à mão.

**Razão:** palavras do Tiago, *"a música dos fguetes é só no momento em que o
Tiago é anunciado o nascimento e a Clara também"*. E é exatamente o que a mãe da
Clara fez: esse troço aparece no vídeo dela duas vezes, aos 32,4 s e aos
768,7 s, por cima dos dois cartões "Era uma vez". Confirmado nos dados.

**Consequência:** medido no MP4, o som passa de -26,9 dB antes do anúncio para
-14,4 dB no nascimento do Tiago, e de -23,9 dB para -13,3 dB no da Clara. Se as
durações dos clips mudarem, o instante acompanha sozinho.

**Quem:** Tiago.

**Substitui:** a regra "vinheta no primeiro cartão" da decisão 023.

---

### 2026-09-12 | 028 | As faixas cruzam-se em vez de encostarem

**Decisão:** quando uma faixa acaba no instante em que outra começa, a primeira
continua a tocar 2,2 segundos por cima da segunda, com descida e subida do mesmo
tamanho.

**Razão:** o Tiago ouviu, *"atenção às transições de músicas, pois está a saltar
estranho em alguns"*. A causa não dava aviso nenhum: a que saía desvanecia e a
que entrava subia ao mesmo tempo e no mesmo ponto, o que abre um vale de volume
no meio.

**Quem:** Tiago reportou.

**Substitui:**

---

### 2026-09-12 | 029 | Nunca recortar ficheiros entre marcadores sem os verificar

**Decisão:** qualquer alteração feita por recorte entre dois marcadores tem de
confirmar que **cada marcador existe uma só vez** antes de cortar.

**Razão:** apaguei metade do `scripts/editor_base.html` de uma vez. Usei o
comentário `/* ---------- apresentação ---------- */` como início do recorte, e
esse comentário existe **duas vezes**, uma no CSS e outra no JavaScript. O
recorte comeu tudo o que estava entre a ocorrência do CSS e o fim escolhido, ou
seja o resto do CSS, o HTML todo e quase todo o JavaScript. O ficheiro não está
no Git, portanto não havia como o repor a partir daí.

**Consequência:** recuperou-se da versão publicada do artefacto, que estava
intacta, com `Artifact action:"read"`. Fica também a lição de que **a versão
publicada serve de cópia de segurança** do editor. O `scripts/editor_base.html`
devia entrar no Git, e entra.

**Quem:** erro meu.

**Substitui:**

---

### 2026-09-12 | 030 | As datas de nascimento estão confirmadas

**Decisão:** os dois nascimentos são facto e podem ir ao ecrã.

| | |
|---|---|
| Tiago | **12 de setembro de 1995** |
| Clara | **24 de novembro de 1995** |

**Razão:** a data do Tiago é palavra dele desde 11/09/2026. A da Clara começou
por ser uma conta minha, a partir do "dois meses e doze dias depois" que ele
escreveu, e por isso ficou em espera: uma data errada projetada num casamento,
à frente das duas famílias, não se desfaz. Confirmou-a em 12/09/2026, nas
palavras dele, "sim e isso mesmo. a data dela".

**Consequência:** cai a ressalva que estava no cabeçalho do
`scripts/montar_v3.py`. E fica confirmada a coincidência que faz a piada do dia
24 funcionar sem ser escrita: **a Clara nasce no mesmo dia em que se salvaram as
gravuras do Côa**, 24 de novembro de 1995. Os dois partilham o mesmo risco da
linha do tempo, e a etiqueta troca de "Salvam-se as gravuras do Côa" para
"Nasce a Clara" sem a fita se mexer um milímetro. O tom humorístico que o Tiago
pediu sai da própria cronologia, não de uma frase que eu tenha escrito.

**Quem:** Tiago.

**Substitui:** a nota "falta confirmação" das decisões 026 e 027.

---

### 2026-09-12 | 031 | O som da fita toca só enquanto a fita anda

**Decisão:** o instante e a duração do som de rebobinar saem de
`linha_tempo.janela_de_movimento()`, não de números escritos à mão.

**Razão:** o Tiago ouviu, *"o som da timeline está a começar antes da timeline
começar a mexer"*. A conta dá-lhe razão: com duas paragens e 62 por cento do
tempo parado, a fita fica quieta os **primeiros 4,03 s** de um clip de 13, e o
som começava no segundo zero.

**Consequência:** medido no MP4, o som sobe aos 52 s, faz pico aos 54 e desce
aos 58. A fita anda dos 53,0 aos 58,0. Se as durações mudarem, acompanha.

**Quem:** Tiago ouviu.

**Substitui:**

---

### 2026-09-12 | 032 | A entrada com zoom só no primeiro clip de cada fita

**Decisão:** um clip de linha do tempo que **continua** a fita do anterior leva
um `c` no fim do intervalo e não reabre a entrada com zoom. Entre dois clips
seguidos da mesma fita há **corte seco**, não encadeado.

**Razão:** o Tiago viu, *"há um efeito estranho após o abre a sapo em Aveiro"*.
Eram **dois "1995" sobrepostos**, um pequeno no topo e outro grande por cima da
imagem do SAPO: cada clip recomeçava a entrada com zoom, portanto o seguinte
desenhava o ano outra vez em grande enquanto o anterior ainda desvanecia.

**Consequência:** um encadeado entre duas imagens quase iguais só produz
fantasmas. O corte seco é invisível porque a fita continua exactamente onde
estava. Regra geral: **conteúdo contínuo corta, conteúdo diferente encadeia.**

**Quem:** Tiago viu.

**Substitui:**

---

### 2026-09-12 | 033 | O detector de caras não se aguentou, e fica o desvio simples

**Decisão:** o corte das fotografias da abertura começa a **32 por cento da
folga** em vez de 50. Não há detecção de rostos.

**Razão:** o Tiago pediu, *"na intro eu focava mais se possível em caras, pois
por vezes vai para pernas ou assim"*. Fiz um detector barato por tom de pele e
detalhe e **ficou pior**. Medido, numa foto de corpo inteiro:

| Faixa | "Pele" | Detalhe |
|---|---|---|
| A cara | 13 % | 5,3 |
| Os sapatos | **79 %** | 3,1 |

A regra clássica de tom de pele dispara em calçada, areia, madeira e parede
bege. "Mais pele é melhor" leva direito ao chão, e foi lá que o corte foi parar.
Corrigi para exigir proporção **moderada** de pele, comparei nas oito fotos onde
mais muda o enquadramento, e mesmo assim não ficou melhor em nenhuma e ficou
pior em duas, a cortar a cara de cima numa foto de quatro irmãos.

**Consequência:** ficou o que se mede e se percebe. O corte nunca desce abaixo
do centro, portanto só pode aproximar-se das cabeças. Comparado nas mesmas oito
fotos: todas iguais ou melhores, nenhuma pior.

**Quem:** Tiago pediu; a heurística foi minha e falhou.

**Substitui:**

---

### 2026-09-12 | 034 | O que está frágil neste projeto

**Decisão:** fica registado o que ainda não está resolvido, para não se
descobrir tarde.

| | |
|---|---|
| **Sem testes automáticos** | Cada correcção foi verificada por medição pontual. Nada avisa se voltar a partir. É a maior dívida. |
| **Render lento** | 0,1 s por fotograma. Um filme de 15 minutos são 22 500 fotogramas, mais de 40 minutos por passagem. O mais longo já feito são 2:25. |
| **Memória por provar** | Nunca se renderizou 15 minutos seguidos. |
| **Ciclo aberto** | O Tiago decide na Mesa de Montagem mas os `montar_*.py` ainda são escritos à mão. A base de dados é legível daqui e ainda não foi usada para gerar uma montagem. |
| **Edições manuais perdem-se** | Os CSV são gerados por script. |
| **Cor não harmonizada** | 362 fotos de origens muito diferentes. Na abertura o duotone esconde; no corpo vai ver-se. |
| **Legibilidade não testada** | O texto a 15 metros está afirmado a partir dos tamanhos de letra, nunca foi visto à escala. |

**Razão:** o Tiago pediu uma avaliação técnica. Uma avaliação que só diz o que
está bem não é uma avaliação.

**O padrão dos meus erros**, porque é o mais útil de registar: confiar num número
derivado sem ir ao original. As dimensões do `.wlmp`, as datas EXIF dos
scanners, a atribuição dos anos, a detecção de corridas, a regra de preferência
da `FINAIS`, os 181 MB de HTML por clique, o detector de caras. Vários foram
apanhados por ele, não por mim.

**Quem:** Tiago pediu a avaliação.

**Substitui:**

---

### 2026-09-12 | 035 | As marcas da fita apontam para o nome real do ficheiro

**Decisão:** a especificação de cada marca da fita passa a trazer o nome do
ficheiro tal como ele está em disco, com espaços, vírgulas e parênteses
incluídos: `kobe, japao.png`, `Schengen_Agreement_(1985)_signatures.jpg`,
`gravuras_coa.jpg`. Nada se renomeia nem se move na pasta de media.

**Razão:** o Tiago largou as quatro imagens em falta na `01-NOVAS` com os nomes
que elas trazem da internet. A fita pedia `kobe.jpg`, `schengen.jpg` e
`coa.jpg`. Só o `Guterres.jpg` calhou coincidir. As outras três marcas saíram
no render de 2026-09-12 às 04:32 **só com palavras, e sem uma única queixa**,
porque `imagem_da_marca` devolve `None` em silêncio de propósito: uma imagem
em falta não pode parar um render de quinze minutos a meio.

A alternativa era renomear os ficheiros dele para o que o código esperava. Fica
rejeitada por duas razões: mexer em `C:\casamento-video-media\` está proibido
pelo CLAUDE.md, e o nome que ele larga é informação, não ruído.

**Consequência:** o silêncio deixa de ser possível. O
`teste_marcas_com_imagem_encontram_o_ficheiro` percorre todos os clips de fita
do `data/mesa_estado.json` e falha se alguma marca declarar uma imagem que não
existe em disco. São 18 referências, todas resolvidas. O render continua a não
parar por uma imagem em falta; é a bateria de testes que apanha.

**Quem:** Tiago largou as imagens, eu não as liguei.

**Substitui:**

---

### 2026-09-12 | 036 | As pastas `_files` das páginas guardadas passam a ser lidas, com corte por tamanho

**Decisão:** o `inventario.py` deixa de ignorar o ramo inteiro de uma pasta
`<nome>_files`. Passa a entrar tudo o que tenha pelo menos 600 pixéis no lado
menor. Abaixo disso fica de fora.

**Razão:** o Tiago pediu para aproveitar o que desse. Uma página do Facebook
guardada traz a interface toda, mas traz também as fotografias verdadeiras, e
só ali: nove fotos da maratona, até 3024x4032, e uma da FEP de 2014. A separação
é limpa e não precisa de julgamento nenhum, porque não há nada pelo meio: o
maior cromo de interface tem 206 pixéis de lado, o menor retrato tem 805. Entre
um e outro há um vazio de 599 pixéis.

Alternativas rejeitadas: escolher à mão, que não sobrevive à próxima página
guardada; e filtrar pelo nome, que aqui é um identificador do Facebook e não
diz nada.

**Consequência:** o inventário passa de 362 para 376 imagens. Das 14 novas, 10
vêm destas pastas e 4 são as imagens da fita de 1995. As 57 restantes, que são
avatares de 150 e 206 pixéis e emojis de 16, ficam onde estão. Nada foi movido
nem apagado.

**O que eu não sei e não vou adivinhar:** quem está nestas dez fotografias.
Estão na Mesa e é lá que ele decide.

**Quem:** Tiago, "se conseguires sim quero que aproveites as fotos que
conseguires".

**Substitui:**

---

### 2026-09-12 | 037 | A fita da linha do tempo passa a ser editável na Mesa

**Decisão:** a Mesa ganha os botões "+ Fita" e "+ Vídeo", e o inspetor mostra
uma fita por dentro: o ano, o troço que o clip percorre em datas, se continua a
fita anterior, e a lista de acontecimentos com data, texto, imagem e estrela.
As marcas são partilhadas por todos os clips de fita do mesmo ano.

**Razão:** a fita só entrava na montagem por um script meu, e ele não lhe podia
tocar sem me pedir. Isso é o contrário do que a Mesa é para ser. Ele já tinha
dito o que queria dela: "eu quero é ter uma forma de meter as fotos e ordem é
para isso que serve a mesa, mantém a timeline, windows, etc.".

As marcas andarem juntas não é comodidade, é correção: a fita de 1995 é UMA
fita, cortada em três clips para as fotografias poderem entrar pelo meio. Um
acontecimento que existisse num clip e não nos outros punha a fita a
contradizer-se dentro do mesmo ano.

**Consequência:** três armadilhas fechadas pelo caminho.

| | |
|---|---|
| A lista não se reordena enquanto ele escreve | Ordenar a cada tecla trocava as marcas de sítio na cadeia guardada sem trocar as linhas no ecrã, e a partir daí cada campo editava a marca errada. Ordena quando ele larga o campo da data, e o `ler_meses()` volta a ordenar do lado do Python. |
| Um troço que comece em cima de uma marca é afastado | Senão o acontecimento pára duas vezes, uma em cada clip. Foi o engasgo entre o SAPO e o Tiago. |
| A duração de um vídeo mede-se, não se escreve | O som é colocado pelo relógio do corpo, e o corpo começa onde os vídeos acabam. Um número errado na Mesa arrastava a banda sonora inteira sem uma queixa. O `montar_da_mesa.py` mede com o `ffprobe` e avisa quando difere. |

**Quem:** Tiago, "prepara tudo para conseguir alterar na mesa de montagem".

**Substitui:**

---

### 2026-09-12 | 038 | As vinhetas da fita não passam pela rede neuronal

**Decisão:** uma imagem que só apareça como marca da linha do tempo fica de
fora do lote de ampliação. A lista sai do estado da Mesa, não está escrita à
mão, e um ficheiro que também seja usado como fotografia normal deixa de ser
vinheta.

**Razão:** uma marca é desenhada com 20 por cento da altura do ecrã, cerca de
216 pixéis. A `gravuras_coa.jpg`, de 500x375, dava fator 3,3 pela regra geral e
ia ser vista a 287 pixéis de largura. Seis minutos de Real-ESRGAN para deitar
fora o resultado.

**Consequência:** o lote da noite baixou de 12 para 8. O
`teste_finais_cobre_o_que_precisa` deixa de acusar falsas faltas.

**Quem:** eu, e digo-o porque é uma regra minha e não dele.

**Substitui:**

---

### 2026-09-12 | 039 | A auditoria pergunta à pasta qual é a escolha, em vez de a adivinhar

**Decisão:** o `auditar_finais.py` passa a descobrir que versão está na `FINAIS`
comparando o conteúdo por sha256, ficheiro a ficheiro. Deixa de repetir a ordem
de preferência do `consolidar.py`.

**Razão:** repetia. A auditoria tinha escrita a mesma lista, "restaurada, IA,
lanczos", e dava por adquirido que era essa que ganhava. Só que o `consolidar.py`
ganhou entretanto a regra de que uma foto que não precisa de crescer fica com o
original, e a auditoria não soube. Resultado: oito fotografias acusadas de
estarem na `FINAIS` em versão IA quando o que lá está é o original, e três delas
com a diferença a ser enorme, +63 por cento de detalhe. Falso do princípio ao
fim.

Duas cópias da mesma regra em ficheiros diferentes acabam sempre assim. E é a
terceira vez que este projeto tropeça no mesmo padrão: confiar num número
derivado sem ir ao original. As dimensões do `.wlmp`, as datas EXIF dos
scanners, e agora isto.

**Consequência:** a coluna "esta:" passa a ser facto verificado e não palpite.
Uma foto cujo conteúdo não bata certo com nada na `FINAIS` é contada à parte em
vez de ser julgada com o rótulo errado.

**Quem:** eu.

**Substitui:**

---

### 2026-09-12 | 040 | Há um índice da FINAIS, e o render passa a lê-lo

**Decisão:** o `consolidar.py` escreve `data/finais.csv` com uma linha por
fotografia: id, ficheiro original, ficheiro final, de onde veio e quanto mudou.
O `render.py` deixa de escolher a versão e passa a ler esse índice. Sem índice,
usa o original e diz que o fez.

**Razão:** o `render.py` nunca olhou para a `FINAIS`. Tinha escrita a ordem de
preferência antiga, "restaurada, IA, lanczos, original", e por isso usava a
versão da rede neuronal também em fotografias que já tinham pixéis que chegavam.
**Eram 62 no inventário e 47 só na v1a, 17 por cento dos clips.**

Isto é grave por uma razão que não é técnica. Uma dessas fotografias é a
`clara_e_padrinho_a_rir.jpg`, e no recorte lado a lado vê-se o que a rede lhe
faz: o ecrã do telemóvel passa a ler-se, as calças ficam lisas, e a pele fica de
cera, com as rugas à volta do olho redesenhadas. O Tiago tinha posto a condição
ao contrário: *"não podemos estragar as feições nem as pessoas, o que nós
queremos é melhorar a qualidade das fotos mantendo-as reais"*.

A regra certa já existia desde a entrada anterior sobre as 21 fotos ampliadas
sem necessidade. O que faltava era ela chegar a quem faz o vídeo.

**Consequência:** a `v3` que ele já tem **não muda**, porque nenhuma das suas 21
fotografias estava neste caso. Mudam a v1a, a v1b e a v1c, que ainda não foram
renderizadas desde a correção do tremor. O `teste_render_usa_o_indice` falha se
alguém voltar a escolher a versão à mão dentro do render.

**Sobra por resolver:** a `FINAIS` tem 29 ficheiros de corridas antigas, com o
nome em `.jpg` onde hoje se escreve `.jpeg`, alguns com 2208 pixéis de largura.
Não apago nada dentro da pasta de media, regra 3 do CLAUDE.md. O `consolidar.py`
passa a listá-los no fim de cada corrida. Decisão dele.

**O padrão, outra vez:** três cópias da mesma regra em três ficheiros, e a que
fazia o vídeo era a que estava por corrigir. É o mesmo que na entrada 039, com
duas horas de intervalo.

**Quem:** eu.

**Substitui:**

---

### 2026-09-12 | 041 | A auditoria lê o índice, e não tenta descobrir a escolha sozinha

**Decisão:** o `auditar_finais.py` passa a ler a escolha atual do
`data/finais.csv`. Substitui a entrada 039, que mandava descobri-la por hash do
conteúdo.

**Razão:** o hash parecia a prova definitiva e não era. A `FINAIS` tem 29
ficheiros de corridas antigas, com o nome em `.jpg` onde hoje se escreve
`.jpeg`, e o hash encontrava o velho. Resultado, sete fotografias acusadas de
estar em lanczos quando a escolha atual é o original.

Três tentativas, três erros, cada um mais convincente que o anterior:

| Tentativa | Porque falhou |
|---|---|
| Repetir a ordem de preferência | Não sabia da regra do original |
| Perguntar à pasta por hash | Encontrava as sobras de corridas antigas |
| Ler o índice | É escrito ao mesmo tempo que a cópia |

**Consequência:** os números passam a ser fiáveis. De 177 fotografias com mais
do que uma versão, a escolha é a melhor medida em 95, é empate em 45, **33 estão
no original por já terem pixéis que chegam**, e restam **4 desacordos a sério**.

**Quem:** eu.

**Substitui:** 039.

---

### 2026-09-13 | 042 | A Mesa deixa de gravar por cima, e cada clip pode trazer a sua música

**Decisão:** antes de gravar, a Mesa lê o `quando` do documento na base. Se ele
mudou desde que a página carregou, não escreve: guarda uma cópia neste aparelho
e pede para recarregar. E qualquer clip pode dizer "a partir daqui toca esta
música", com o segundo onde ela entra; o `montar_da_mesa.py` obedece.

**Razão:** a v3 dele na Mesa, lida a 13 de setembro, tinha perdido os dois vídeos
de abertura, os três clips da fita de 1995 e as notas que eu lá tinha escrito. As
notas terem voltado ao texto antigo é o que mostra que não foi ele: um separador
aberto desde antes da minha escrita de 12 de setembro gravou a cópia velha por
cima, porque cada gravação substituía o documento inteiro sem olhar.

Testado com uma base falsa no browser: com outro separador a gravar entretanto,
a Mesa não escreveu, o documento do outro ficou intacto, o aviso apareceu e a
cópia de segurança ficou guardada.

**Consequência:** para o render desta data repus os vídeos e a fita a partir da
cópia de 12 de setembro, sem tocar em nenhum clip dele. Não escrevi na Mesa
porque ele estava a editar nesse momento: escrever ali era repetir o defeito.

**Quem:** eu. A música por clip responde ao pedido dele: "gostava de ter outra
música a começar aí".

**Substitui:**

---

### 2026-09-13 | 043 | A Clair entra nos penteados da Clara

**Decisão:** o bloco "Já teve muitas fases penteados" da v3 abre com `Clair`, do
Gilbert O'Sullivan, a entrar no ficheiro aos 6,5 s. Está marcada no próprio
cartão, com o campo de música por clip da Mesa.

**Razão:** foi a mãe da Clara que pôs esta canção por baixo de quatro das seis
fotografias deste bloco, e é uma das canções com o nome dela, que é a
assinatura protegida pela decisão 001. O Tiago ouviu o render com ela e ficou.

**Alternativa rejeitada:** `Me Gustas Tu`, do Manu Chao. Fica registado como ele
a usaria, se um dia voltar a ser hipótese: **só a partir dos 23 s do ficheiro, e
a entrar com um fade curto**, para tirar a introdução que o ficheiro traz.

**Consequência:** fechado o ponto L. A v3 de 13 de setembro, com 3:24, já está
assim e não precisa de novo render.

**Quem:** Tiago, "mantemos a Clair".

**Substitui:**

---

### 2026-09-13 | 044 | Cada render fica guardado como versão, com data e hora

**Decisão:** o `render.py` deixa de escrever sempre `<montagem>.mp4`. Cada render
sai como `<montagem>_AAAA-MM-DD_HHMM.mp4`, com a cópia leve ao lado com o mesmo
nome e `_leve` no fim, e acrescenta uma linha a `data/renders.csv` com a duração,
o tamanho, o número de clips e as músicas que tocam. Um render parcial, com
`--ate` ou `--escala`, leva `_parcial` no nome e não gera cópia leve.

**Razão:** o Tiago: "Quero guardar versões, é melhor". A v3 de 12 de setembro, de
2:42, desapareceu quando saiu a de 13, porque as duas se chamavam `v3.mp4`.

**Consequência:** nada é escrito por cima; se dois renders caírem no mesmo
minuto, o segundo leva `_2`. A cópia leve passa a sair sempre com o render, em vez
de ser feita à mão. A v3 de 13 de setembro foi **copiada** para o nome com data;
os ficheiros `v3.mp4` e `v3_leve.mp4` ficam onde estão, porque na pasta de media
não se apaga nem se move nada. A v3 de 12 de setembro não se recupera.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 045 | As 173 fotos de `Novas_Novas` entram, e as repetidas só se reportam

**Decisão:** entram no inventário as 173 imagens que o Tiago largou em
`01-NOVAS/Novas_Novas` na noite de 13 para 14 de setembro. O `inventario.py`
passa a aceitar `.webp`, porque uma delas, de 1438x1440, vinha nesse formato e
ficava de fora sem aviso. O inventário passa de 376 para 549.

**Razão:** é para isso que a pasta existe, decisão 008. Os quatro vídeos `.mp4`
que vieram na mesma pasta não entram no inventário de fotografias.

**Repetidas, só reportadas, nada foi apagado nem escondido:**

| | |
|---|---|
| Iguais byte a byte | `30Abril18_125.jpg` já estava no material da mãe; `20220314_051539.jpg` é a `2022_Tiago_e_sky.jpg` |
| Cópias de WhatsApp de fotos que já existiam | `IMG-20190622-WA0008` ≈ `IMG_3547.JPG`; `IMG-20181006-WA0007` ≈ `IMG_9283 (1).jpg`; `IMG-20181006-WA0013` ≈ `IMG_4751.JPG`. A de WhatsApp é a pior das duas |
| Quase iguais entre si | `20240728_194710` e `_194711`; `IMG_1498 (2)` e a versão `-EFFECTS`; `DSC02953` e `DSC02954` |

**Consequência:** 171 das 172 fotos não trazem pessoa, porque a pasta e os nomes
de câmara não dizem quem lá está. Têm ano em 163 casos, pelo EXIF ou pelo nome.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 046 | A rede neuronal só corre nas fotos que precisam de crescer

**Decisão:** para as fotos novas, o `upscale_ia.py` corre com `--min 1.0` e não
com `--todas`.

**Razão:** o `--todas` punha 66 fotos na fila, perto de dez horas, e mais de
metade já tinha pixéis que chegam. Desde a decisão 040 essas ficam com o
original na `FINAIS` e o render nunca usa a versão da rede nelas. Era trabalho
para deitar fora. Com `--min 1.0` ficam só as que o índice pode de facto usar.

**Consequência:** nenhuma foto muda de versão por causa disto. Se um dia um plano
fechado precisar de mais pixéis numa foto que hoje não cresce, corre-se só essa.

**Quem:** eu, dentro da regra da decisão 040.

**Substitui:**

---

### 2026-09-14 | 047 | Não há reconhecimento de caras, nem agora nem mais tarde

**Decisão:** eu não identifico nem distingo pessoas pela cara nas fotografias,
mesmo com fotos de referência marcadas pelo Tiago. Quem está numa fotografia é
dito por ele. O que posso fazer é sugerir a partir de texto que ele ou a mãe da
Clara escreveram, nomes de pastas, nomes de ficheiros e legendas, sempre marcado
como sugestão.

**Razão:** o Tiago perguntou, *"Achas que já consegues fazer reconhecimento de
quem é o Tiago e quem não é?"*. Comparar caras entre fotografias é
reconhecimento facial, e não o faço. Além disso já errei aqui a ver pessoas:
tratei duas senhoras como pessoas diferentes quando eram a mesma. Um erro destes
num vídeo projetado para as duas famílias não se desfaz.

**Consequência:** as sugestões por texto seguem a decisão 016: uma sugestão que
ele não tocou nunca conta como palavra dele. Para as 173 fotos novas quase não há
texto de onde sugerir, portanto aí a marcação é mesmo dele, com o pincel da Mesa.

**Quem:** eu, em resposta ao Tiago.

**Substitui:**

---

### 2026-09-14 | 048 | Na Mesa escolhem-se vários clips, move-se por número e junta-se no sítio certo

**Decisão:** a lista da montagem passa a ter:

| | Como se faz |
|---|---|
| Escolher vários | Caixa em cada clip; Shift escolhe um intervalo; Ctrl ou Cmd no clip junta à escolha |
| Mover para uma posição | Carregar no número do clip e escrever outro; ou, com vários escolhidos, a barra "mover para a posição". O primeiro dos movidos fica nesse número e os outros vão atrás pela ordem que tinham |
| Arrastar | Um clip escolhido arrasta todos os escolhidos. Larga-se antes do clip onde aparece o traço |
| Juntar da biblioteca | "Juntar à montagem" deixa de pôr no fim. Aparecem linhas "Juntar aqui" entre os clips, a lista continua a deixar fazer scroll, e também se pode escrever a posição. As fotos entram pela ordem em que foram escolhidas |
| Arrastar da biblioteca | Uma foto, ou as escolhidas, largam-se diretamente no sítio |
| Anular | Botão "Anular" e Ctrl+Z, para mover, juntar, subir, descer e remover. Delete remove os escolhidos. Esc cancela |

**Razão:** o Tiago, *"quero poder selecionar várias fotos e mover de sítio"*,
*"escrever a posição no número"*, e ao juntar *"em vez de irem sempre para o fim
poder clicar na posição na montagem e perguntar o número da posição que quero
(tem de deixar fazer scroll na montagem para escolher bem onde quero)"*. É uma
alteração para ele trabalhar mais depressa.

Por isso nada disto é uma janela modal: uma janela modal bloqueia o scroll da
lista, e escolher o sítio obriga a andar pela lista. A barra fica por cima da
lista e a lista continua livre.

**Consequência:** três escolhas minhas que ficam à vista para ele contestar.

1. Arrastar para baixo largava o clip **depois** do alvo, ao contrário do traço,
   que se desenha por cima. Agora larga sempre **antes**, como o traço mostra.
2. As fotos juntas entram pela ordem do clique e não pela ordem da biblioteca.
3. O "Anular" desfaz a **ordem** da montagem. Não desfaz textos nem durações.

A escolha guarda-se pelo próprio clip e não pelo número, porque depois de mover
os números mudam todos e uma escolha guardada por número apontava para os clips
errados.

Testado no browser com uma base de dados falsa, na v1a de 292 clips: mover três
para a posição 10 com o resto intacto, anular, número escrito à mão, intervalo
com Shift, Delete e Ctrl+Z, juntar três fotos numa linha pela ordem do clique,
juntar escrevendo a posição 1, arrastar um clip, arrastar uma foto da biblioteca,
e a gravação. Todas as verificações passaram e a consola ficou sem erros.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 049 | A música marcada na Mesa encontra-se mesmo sem a extensão

**Decisão:** o `montar_da_mesa.py` aceita o nome de uma música escrito na Mesa sem
`.mp3`, com outra forma de acentos, e sem distinguir maiúsculas. Uma música
marcada que não se encontre continua a dar aviso, mas **já não corta** a música
que vinha a tocar. O inventário passa também a aceitar `.gif`.

**Razão:** o Tiago marcou quatro músicas na v3 (Baha Men, Tokyo Drift, Tiago
Celebration Song, António Variações) sem o `.mp3` no fim. A procura era pelo nome
exato, as quatro davam "em falta", e como a música anterior já tinha sido cortada
nesse ponto, o vídeo ficava **mudo dos 3:51 até ao fim**. Foi apanhado antes do
render. O `.gif` é uma animação do Google Fotos que estava na `01-NOVAS` desde 10
de setembro e nunca tinha sido vista; entra como fotografia, o primeiro fotograma.

**Consequência:** o `teste_musicas_marcadas_encontram_ficheiro` falha se alguma
música marcada na Mesa não chegar a um ficheiro. A `2026_Corrida_José.jpg`, largada
às 12:28 de 14 de setembro, e o `.gif` entram no inventário.

**Quem:** eu, ao preparar o render que o Tiago pediu.

**Substitui:**

---

### 2026-09-14 | 050 | Há um terceiro efeito: fotografias lado a lado

**Decisão:** existe o clip `lado`, com 2 a 4 fotografias no mesmo ecrã, em quatro
disposições:

| Disposição | Fotos | Como fica |
|---|---|---|
| duas colunas | 2 | o ecrã dividido ao meio na vertical |
| três colunas | 3 | três colunas iguais |
| duas e uma por cima | 3 | duas colunas e a terceira num cartão com moldura clara, por cima, ao centro |
| quatro quadrados | 4 | quatro retângulos iguais |

Cada foto entra de fora, uma a seguir à outra, com 0,45 s de intervalo, e fica. As
das pontas entram pelo seu lado e a do meio sobe de baixo, para nenhuma atravessar
outra. Depois de todas pousarem, cada uma respira com um zoom lento dentro da sua
própria célula, sem invadir a do lado. Entre as fotos fica uma linha preta de 8
pixéis, para se lerem como fotografias separadas.

Na Mesa escolhem-se 2 a 4 fotografias na montagem e carrega-se em "Lado a lado".
A disposição e a ordem de entrada mudam-se no inspetor. "Separar em fotos soltas"
devolve as originais tal e qual, com as legendas, durações e música que tinham.

**Razão:** o Tiago, *"permitir colocar fotos tipo lado a lado ... no máximo até 4
... com movimento a entrar e que fiquem todas no ecrã após todas entrarem. Se forem
3 pode dividir em dois e a última aparece por cima ou colocar o ecrã dividido em 3
iguais na vertical. Também quero dividir na vertical em dois"*. Como ele deu duas
hipóteses para as três fotos, ficaram as duas, à escolha em cada clip.

**Consequência:** o corte de cada foto guarda mais o cimo do que o fundo, o mesmo
desvio da decisão 033, porque numa célula as caras ficam quase sempre no terço de
cima. A duração proposta é 2 s mais 1,5 s por foto. **Aviso de exibição:** quatro
quadrados a 15 metros fazem cada foto do tamanho de um quarto de ecrã; funciona com
planos fechados e não com fotos de grupo tiradas de longe.

Testado: geometria das quatro disposições, entrada que começa vazia e acaba com
todas no sítio, um render de ensaio com as quatro, e na Mesa juntar, mudar a
disposição, reordenar, pré-visualizar, separar com as legendas de volta, anular e
gravar. A Mesa não deixa juntar cartões nem vídeos.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 051 | A v1c foi refeita sem os bilhetes de admiradores

**Decisão:** o `data/montagens/v1c.csv` foi gerado outra vez com o
`montar_v1c.py`, a partir da v1b atual. O teste das fotos excluídas passa a
verificar a v1a, a v1b e a v1c.

**Razão:** a decisão 020 tirou de todas as versões os cinco bilhetes de
admiradores. A v1c tinha sido gerada nesse mesmo dia, mas **antes** da decisão, e
nunca mais foi refeita: continuava com o `8-6` a `8-9-1` e com as legendas "Clube
de Fãs", "Inspirou figuras de estilo" e as restantes. Ninguém deu por isso porque o
teste só olhava para a v1a. Foi apanhado ao preparar as comparações do ponto K.

**Consequência:** a v1c fica com 308 entradas e 15:56. A versão v1c que está
guardada na Mesa do Tiago é uma cópia antiga e ainda tem os bilhetes; não lhe
toquei, porque é o estado dele.

**Quem:** eu, em cumprimento da decisão 020.

**Substitui:**

---

### 2026-09-14 | 052 | Abaixo de 1,5 vezes usa-se o lanczos

**Decisão:** quando uma fotografia precisa de crescer menos de 1,5 vezes, a pasta
FINAIS fica com a versão lanczos. A partir de 1,5 vezes continua a rede neuronal.
Nenhuma versão é apagada: as duas continuam no disco.

**Razão:** o Tiago viu oito recortes lado a lado, a 100 por cento, das duas
versões, escolhidos nas ampliações onde o lanczos mais perde, e decidiu: *"gosto
mais da lanczos"*. A rede neuronal amplia sempre 4 vezes e só depois se reduz, por
isso retoca a pele e os contornos mesmo quando a foto só precisava de crescer um
bocadinho; nas digitalizações antigas desenha contornos escuros que não existem. É
também o que o briefing dizia desde o primeiro dia, e que o `consolidar.py` nunca
tinha implementado.

**Consequência:** mudam 89 fotografias, 23 delas na v3. O
`teste_ampliacao_pequena_usa_lanczos` falha se alguma foto abaixo de 1,5 vezes
voltar a ficar com a rede neuronal. A regra acima de 1,5 vezes não foi vista em
recortes e fica como estava.

**Quem:** Tiago.

**Substitui:** fecha o ponto K.

---

### 2026-09-14 | 053 | Cada fotografia pode ter um ponto de foco, marcado na Mesa

**Decisão:** na Mesa, cada fotografia que vai ser cortada mostra um editor com a
foto, o retângulo exato que fica no ecrã e um ponto. Carregar onde está a pessoa
centra o corte nesse sítio. O ponto é da fotografia e não do clip: marca-se uma vez
e vale em todos os sítios onde ela for cortada, no lado a lado e na rajada. "Voltar
ao automático" apaga-o.

**Razão:** o Tiago, depois de ver o ensaio do lado a lado: *"Tens de me permitir
ajustar o ponto do foco da foto, caso contrário pode acontecer de sugerires zona em
que corta a pessoa como num dos exemplos que deste"*. Tinha razão, e o caso era pior
do que um corte: no "duas e uma por cima", o corte automático pôs a cara de uma
pessoa **atrás do cartão de cima**.

**Consequência:**

| | |
|---|---|
| Na montagem | O ponto vai na coluna `fonte_imagem`, "fx,fy", e num lado a lado um por foto separados por "\|" |
| No render | `cobrir_foco()` centra a janela no ponto e encosta às bordas quando não há mais foto |
| Na Mesa | No "duas e uma por cima", a zona de cada metade que o cartão tapa aparece às riscas, calculada com as mesmas contas do render. Tapa perto de metade do lado de dentro |
| Sem ponto | Fica o corte de antes, igual ao que ele já viu |

Provado com um render de ensaio: a mesma foto de Dubrovnik, com o corte automático
tem a cara meio escondida atrás do cartão, e com o ponto marcado aparece inteira do
lado de fora. Na Mesa, com uma base de dados falsa: o retângulo acompanha o clique
para a direita e para a esquerda, a zona tapada aparece do lado certo das duas
metades, o ponto grava-se, e a consola ficou sem erros.

**Aviso para ele:** numa coluna estreita, das "três colunas", uma foto deitada com
duas pessoas lado a lado não cabe inteira. O ponto de foco escolhe uma das duas; não
faz milagres. Para essas, é melhor "duas colunas" ou uma foto em pé.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 054 | Cada render traz uma cópia que cabe no telemóvel

**Decisão:** quando a cópia leve de um render passa dos 29 MB, o `render.py` faz
também `<render>_telemovel.mp4`, a 960x540, apertada até caber abaixo dos 30 MB.

**Razão:** o Tiago acompanha muitas vezes a partir do telemóvel, e o envio para lá
tem um limite de 30 MB. A cópia leve da v3 de 6:30 tinha 41 MB e só ficou visível
na app do computador, sem aviso nenhum do lado dele.

**Consequência:** a v3 de 14 de setembro às 14:13 saiu com as três: completa com
138 MB, leve com 41 MB e telemóvel com 22,5 MB. Para mandar ao Tiago, a de
telemóvel quando existir; senão, a leve.

**Quem:** eu.

**Substitui:**

---

### 2026-09-14 | 055 | Entram mais 90 imagens, e 40 delas não são fotos do casal

**Decisão:** entram no inventário as 90 imagens que o Tiago largou na `01-NOVAS` na
tarde de 14 de setembro. O inventário passa de 551 para 641.

**O que são:**

| | Imagens |
|---|---|
| Fotos do casal, da família e dos amigos, na raiz da pasta | 50 |
| Da página de Instagram da quinta, em `Quinta/Instagram_files` | 40 |

As 40 da página da quinta **não são fotografias do casal**: são casamentos de outros
noivos, mesas decoradas, vistas aéreas da quinta, logótipos e capturas de ecrã de
histórias. Não foram escondidas nem apagadas, porque uma foto que entra nunca se
apaga, mas ficam à parte até o Tiago dizer o que fazer com elas. Ver ponto M.

**Repetidas, só reportadas:** `20170204_200730.jpg`, `20170805181124.jpg` e
`A Happy Year (16).jpg` são iguais byte a byte a fotos que já estavam no material
da mãe da Clara. O vídeo `DSCN8638.MOV` não entra no inventário de fotografias.

**Consequência:** a rede neuronal corre só nas que precisam de crescer 1,5 vezes
ou mais, e o teste que exigia a versão IA passa a exigi-la só a partir desse
limite, de acordo com a decisão 052.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 056 | A Mesa mostra o estado das fotos e deixa pedir uma atualização

**Decisão:** a Mesa ganha um botão "Estado das fotos" na Biblioteca. Mostra quantas
fotos estão prontas, quais estão à espera e porquê, e quantas imagens da pasta
NOVAS ainda não foram registadas, com a data e a hora da verificação. Tem dois
botões: "Procurar versão nova", que pergunta à base de dados se já foi publicada uma
Mesa mais recente, e "Pedir atualização", que deixa um pedido guardado. As fotos à
espera levam uma pequena marca dourada na grelha.

**Razão:** o Tiago, *"Não te esqueças de fazer update às fotos que tratares na mesa,
aliás podias colocar lá um botão para atualizar e para verificar se já analisou as
fotos todas"*.

A Mesa corre numa página publicada e **não consegue ver a pasta nem correr nada no
computador**. Um botão "Atualizar" que prometesse fazê-lo na hora estaria a mentir.
Por isso ficou dividido no que cada lado consegue fazer de verdade:

| Lado | O que faz |
|---|---|
| Computador | `scripts/atualizar_fotos.py` faz tudo por ordem, e `scripts/estado_fotos.py` tira o retrato do que ficou pronto |
| Mesa | Mostra esse retrato, avisa quando há versão nova publicada e guarda o pedido em `montagem/pedido` |
| Claude | No início de cada sessão lê o pedido; depois de publicar escreve `montagem/publicacao` |

**Consequência:** quando uma Mesa aberta há horas encontra uma publicação mais
recente, aparece uma barra "Há uma versão mais nova da Mesa" com o botão Recarregar.
Isto também protege contra o separador antigo que um dia gravou uma cópia velha por
cima, na decisão 042.

Testado no browser com uma base de dados falsa: contagens certas, lista das 90 à
espera, aviso quando já é a versão mais recente, barra quando há uma mais nova,
pedido gravado e lembrado ao reabrir, consola sem erros. O
`teste_estado_das_fotos` confirma que cada foto é contada uma vez.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 057 | O Rei Leão passa a ser a versão portuguesa

**Decisão:** a música entre o nascimento do Tiago e o da Clara é `O Rei Leão (PT-PT)
Ciclo Sem Fim.mp3`, a entrar do princípio do ficheiro.

**Razão:** o Tiago trocou o ficheiro na pasta de músicas, *"Troquei a música do Rei
Leão por outra versão: O Rei Leão (PT-PT) Ciclo Sem Fim. Mete lá direitinho"*. A
versão antiga já não está em disco, e o `montar_da_mesa.py` procurava-a pelo nome:
sem a troca, aquele troço saía mudo. Medido o ficheiro, não tem silêncio a abrir, e o
canto de abertura é a parte que toda a gente reconhece, por isso entra do segundo 0.

**Consequência:** na v3 atual o Rei Leão toca dos 32,5 s aos 112 s do corpo. Na mesma
altura foram repostos na cópia local `data/mesa_estado.json`, e não na Mesa dele, os
dois vídeos de abertura (decisão 001), a fita de 1995 em três partes (037) e a Clair
nos penteados (043). A escrita na base da Mesa foi recusada (`version_mismatch`, ver
CLAUDE.md), e as leituras seguintes confirmam que a Mesa dele continua sem eles: cada
vez que ele grava, a junção tem de ser refeita antes do render. Sem a fita, o nascimento do Tiago não era encontrado, porque o cartão dele
passou a dizer "Nasce o segundo filho de Graça e Alberto", e caíam em silêncio o Lang
Lang, os foguetes do Tiago e o próprio Rei Leão.

Ficou por tocar, porque é dele: um clip de fita que ele criou entre as viagens, que
percorre de 1 de janeiro a 21 de maio e não tem nenhum acontecimento pelo caminho.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 058 | Na Mesa exclui-se em bloco e vê-se cada foto em grande

**Decisão:** a Biblioteca da Mesa ganha:

| | Como se faz |
|---|---|
| Escolher muitas de uma vez | Shift com um clique escolhe todas entre a última e esta |
| Excluir da Mesa | Botão "Excluir da Mesa" com fotos escolhidas. Somem da vista; em "Só as excluídas da Mesa" vêem-se e repõem-se |
| Ver em grande | O símbolo ⤢ em cada miniatura, ou carregar na miniatura de um clip da montagem. Mostra a foto a 720 pixéis, o ano, o tamanho, a pasta, as pessoas e a legenda da mãe, com setas para a anterior e a seguinte |

**Razão:** o Tiago, *"Permite-me também excluir fotos da mesa ao carregar nelas em bulk
e eliminar da mesa. Quero também poder expandir as fotos, pois nem sempre consigo
perceber exatamente que foto é aquela"*.

**Excluir da Mesa não apaga nada:** a regra 3 do CLAUDE.md não deixa apagar ficheiros
na pasta de media, e uma foto que entra nunca se apaga. A exclusão é da vista, guarda-se
no estado da Mesa, e se a foto estiver numa montagem continua lá, com aviso.

**As fotos em grande vêm em folhas ao lado da página**, `previas/folha_NN.jpg`, 16 fotos
por folha a 720 pixéis cada, feitas pelo `scripts/gerar_previas.py` a partir da FINAIS.
Dentro do HTML seriam perto de 35 MB e a Mesa passava o limite e demorava a abrir no
telemóvel; assim só se descarrega a folha da foto que se abre. A primeira tentativa foi
um ficheiro por foto e a publicação recusou-a: o link da Mesa aceita no máximo 256
ficheiros ao todo, e são 641 fotos. Em folhas são 41. Enquanto a folha descarrega, ou
se não estiver publicada, mostra-se a miniatura ampliada.

Testado no browser com uma base de dados falsa: Shift escolheu cinco, excluir tirou-as
e avisou que quatro estavam na montagem, repor devolveu duas, a prévia abriu a 720
pixéis, as setas passaram à seguinte, a miniatura da montagem abriu a foto, e a consola
ficou sem erros.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-14 | 059 | Cinco defeitos do render corrigidos antes da v3 com o Rei Leão novo

**Decisão:** antes de voltar a renderizar a v3, corrigir o que uma verificação em
paralelo encontrou e confirmou, com um segundo revisor a tentar refutar cada problema:

| Defeito | Correção |
|---|---|
| O contador saía sem "4 de outubro de 2026". A Mesa escreve `2026>1995\|4 de outubro de 2026` e o `ler_anos` só lia `2026=...` | Um rótulo sem `ano=` é do ano de partida |
| As legendas de diálogo da mãe perdiam as mudanças de linha e a frase partia a meio | `quebrar_paragrafos` no `render.py`, para legendas e cartões |
| O filme acabava na última foto em cheio e a música cortava com 1 s de descida | Fade a preto de 2,5 s na imagem e descida de 4 s no som, só em render completo |
| Vale mudo na entrada do António Variações, que tem 2,44 s de silêncio no ficheiro | O `montar_da_mesa.py` salta o silêncio inicial das músicas marcadas e avisa. Também Baha Men 1,69 s e Tokyo Drift 0,64 s |
| Se o Tiago corrigir "bebe" para "bebé", os foguetes da Clara deixavam de ser encontrados | A procura do cartão ignora acentos |
| Já com a data no contador, ela sumia de 97% para nada em 40 ms quando a fita arrancava, porque o rótulo era cortado pela velocidade | O rótulo acende e apaga dentro da paragem, como os marcos da fita dos meses |

Uma segunda revisão às correções encontrou a data a piscar e três testes que passavam
mesmo com a correção desfeita. Os testes passaram a medir o que o render desenha e o
som que constrói, e cada correção foi desfeita em memória para confirmar que o teste
respetivo falha. A pré-visualização da Mesa passou também a mostrar as falas em linhas
separadas, como o render.

**Razão:** o CLAUDE.md pede fim inequívoco com fade a preto, e os outros quatro saíam
errados sem aviso nenhum. Cada um tem teste em `scripts/testes.py`.

**Não corrigido, porque é texto dele:** a nota "Vai ser para o fecho se usar o heli..."
na última foto, "(faltam fotos)" no cartão do carro, "Advinham", "Com um família",
"bebe" e "kms". Vão ao ecrã tal como estão até ele decidir.

**Quem:** Claude, a pedido do Tiago ("dá-me um render novo").

**Substitui:**

---

### 2026-09-14 | 060 | Na fita que volta antes da Clara, retoma a música da abertura

**Decisão:** o Rei Leão toca dos foguetes do Tiago até à primeira fita que vem depois
dele (a do Guterres e das notícias até ao nascimento da Clara). Aí volta a música que
tocava antes dos foguetes do Tiago, no segundo do ficheiro onde tinha parado, e toca
até aos foguetes da Clara. Na v3 de hoje é o Lang Lang, retomado aos 31 s do ficheiro.

**Razão:** o Tiago, *"Quando voltamos à timeline depois do Tiago para a vitória do
Guterres e notícias seguintes até ao nascimento da Clara, não quero que volte à música
do Rei Leão. Preferia que continuasse onde estava na outra música antes do nascimento
do Tiago. Este comentário é válido independentemente da música que usar para a intro
inicial"*. Por isso o `montar_da_mesa.py` não procura o Lang Lang pelo nome: procura o
leito que tocava antes dos foguetes do Tiago, seja ele o de omissão ou um marcado na Mesa.

**Quem:** Tiago.

**Substitui:** a parte da 057 que punha o Rei Leão até ao nascimento da Clara.

---

### 2026-09-14 | 061 | A viagem até 2011 é um contador, e a Mesa volta a receber escrita

**Decisão:** o clip da posição 133 da Mesa, uma fita de 1995 sem acontecimentos, passa a
ser um contador `1995>2011` de 9 s. A fita só percorre os meses de um ano; o que anda
de ano em ano, e para no ano de chegada, é o contador, o mesmo da abertura, agora para
a frente.

Na mesma escrita foram repostos na Mesa dele, e desta vez chegaram, os dois vídeos de
abertura, as três partes da fita de 1995 e a Clair nos penteados. A ferramenta Artifact
passou a aceitar `if_version`, e a escrita foi feita presa à versão 1116 que ele gravou,
para não passar por cima de nada mais recente.

**Razão:** o Tiago, *"o que queria era levar para o ano de 2011 que foi quando a Clara e
o Tiago se começaram a interagir. Corrige diretamente na mesa"*. O rótulo por baixo de
2011 fica vazio: é texto para o ecrã e é ele que o escreve, no formato
`1995>2011|2011=texto`.

**Quem:** Tiago.

**Substitui:** o limite de escrita na Mesa descrito no CLAUDE.md a 14 de setembro.

---

### 2026-09-14 | 062 | Lado a lado no campo Tratamento, e as fotos por marcar

**Decisão:** na Mesa,

| | Como se faz |
|---|---|
| Lado a lado a partir de uma foto | Campo Tratamento, grupo "Lado a lado, com as fotos seguintes": junta esta foto com as seguintes da montagem, as que a disposição pede. Se a seguir houver um cartão, uma fita ou o fim, avisa e não muda nada |
| Mudar ou desfazer um lado a lado | No clip lado a lado, o Tratamento mostra as disposições possíveis e "separar em fotos soltas" |
| Ver só as fotos por marcar | Filtro de pessoas, "Sem ninguém marcado" |
| Escolher todas as que o filtro mostra | Botão "Escolher as que estão à vista"; com uma pessoa escolhida na barra de marcar, "Aplicar às escolhidas" marca-as todas |

**Razão:** o Tiago, *"Não está ainda no Tratamento as opções que criamos"* e *"permite-me
selecionar as fotos que ainda não tinham um label marcar"*. O lado a lado só existia na
barra que aparece ao escolher vários clips, e ele procurava-o no Tratamento.

Testado no browser com uma base de dados falsa: juntar três em três colunas e anular,
recusa antes de um cartão, mudar a disposição e separar, 442 fotos sem marcação de 614
à vista, escolher as 442 e marcá-las de uma vez, consola sem erros.

**Depois de uma revisão com um segundo revisor a tentar refutar cada problema:**

| Problema confirmado | Correção |
|---|---|
| Lado a lado pelo Tratamento engolia a música de uma das fotos seguintes, que passava a entrar mais cedo | Não junta, e diz qual foto começa que música |
| A recusa dizia sempre "cartão, fita ou fim" | Diz o que há de facto a seguir, e avisa quantos segundos a montagem perde ("12 s passam a 6,5 s") |
| "Escolher as que estão à vista" somava à escolha anterior, e o pincel marcava fotos fora da vista | Fica só com as da vista |
| Com o pincel no filtro "Sem ninguém marcado", a foto marcada sumia e a seguinte saltava para o lugar dela | A foto marcada fica na grelha até o filtro mudar |
| A ajuda do contador levava a pôr o rodapé em 1995 e não em 2011 | A ajuda explica `1995>2011\|2011=texto` |
| Uma música de abertura marcada no primeiro clip não cortava o Lang Lang: tocavam as duas (060) | A marca no zero corta o leito que começa no zero |
| Com música marcada nas fotos do Tiago, a retoma passava por cima dos foguetes da Clara (060) | A retoma acaba sempre nos foguetes da Clara |
| O `juntar_mesa.py` parava com dois contadores | Procura o contador que recua, o da abertura |

O teste da retoma passou a montar de verdade três casos (sem marcas, abertura marcada,
música nas fotos do Tiago), e cada correção foi desfeita em memória para confirmar que
ele falha.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-15 | 063 | A Mesa mostra o que o render faz, e uma cópia velha já não ganha à base

**Decisão:**

| | Na Mesa |
|---|---|
| Som do render | Botão "Som do render" com todas as faixas pela ordem do filme: as marcadas por ele e as que o script põe sozinho (música da abertura, rebobinar, foguetes, Rei Leão, retoma, Clarinha), em que clip entram, de que segundo do ficheiro e quanto tocam, e de que decisão vem cada regra |
| Na lista da montagem | Etiquetas ♪ e ✦ nos clips onde entra uma música ou efeito do script, "render 6,2s" quando o render usa outra duração, "corta 38%" numa rajada que corta muito, "sai no início do filme" num vídeo fora do topo, "excluída" e "à espera" |
| No inspetor | Bloco "No render": quando o clip entra no filme, a duração verdadeira e porquê, e o que começa a tocar nele |

Os dados vêm de `scripts/som_para_mesa.py`, que lê os mesmos `data/montagens/v3.csv` e
`v3.som.csv` do render, e o `gerar_mesa.py` põe-nos na página. Cada faixa aponta para o
clip por uma chave (tipo e fotos, texto ou ficheiro), por isso segue o clip se ele mudar
de posição; os instantes só se atualizam quando se volta a montar.

**A guarda do arranque:** a Mesa abria a cópia do aparelho sempre que ela tinha data
mais recente do que a base, e ficava com a data da base como ponto de partida. A
gravação seguinte passava a guarda e escrevia por cima. Foi o que aconteceu na versão
1143: desapareceram outra vez os vídeos, as fitas de 1995, a Clair e o contador de 2011
repostos na 1117. Agora a cópia do aparelho leva a versão em que se apoia e só ganha se
essa ainda for a da base; senão abre a guardada e a outra fica de lado, com aviso.

**Razão:** o Tiago, *"Atualiza completamente a Mesa de Montagem assegurando que fica
fiel ao que já temos no vídeo renderizado em termos de scripts que tens vindo a falar
como o clair, etc."* e *"nota que músicas tocavam"*.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-15 | 064 | O que a auditoria da Mesa encontrou e ficou corrigido

**Decisão:** uma auditoria comparou tudo o que o render sabe fazer com o que a Mesa deixa
fazer e mostrar. Corrigido:

| Defeito | Correção |
|---|---|
| O campo Ano da fita tinha o mesmo id do filtro de anos: não fazia nada, e mudar o filtro reescrevia o ano da fita aberta | id próprio |
| "+ Vídeo" punha o vídeo no fim; o render junta os vídeos antes das fotos e deixava um buraco | Entra a seguir aos vídeos do início |
| Lado a lado pela barra mudava a música de sítio | Recusa, como pelo Tratamento |
| Rajada sem o ritmo decidido | Botão "Pôr 0,56 s e corte seco" (decisão 021), que se pode anular |
| "Continua a fita anterior" com cross | Põe cross 0 (decisão 032) |
| Não se via que marcas disparam os foguetes | A fita diz-o, e avisa numa estrela sem "Tiago" nem "Clara" |
| O contador na pré-visualização mostrava o rodapé em bruto | Mostra "2011: texto", com a regra do ler_anos |

Ficam por fazer, porque são maiores e não estragam o vídeo: pré-visualização com fundo
desfocado e corte verdadeiro, paragens da fita com o segundo de cada uma, o rebobinar a
seguir `janela_de_movimento()` (decisão 031), e a fanfarra das v1a a v1c, que o
`montar_da_mesa.py` deita fora.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-15 | 065 | Cinco fotos novas na NOVAS, tratadas pela regra, sem duplicados

**Decisão:** registadas e tratadas pela regra de sempre (decisão 052), com o
`atualizar_fotos.py`:

| id | Ficheiro | Tamanho | Precisa de | Versão na FINAIS |
|---|---|---|---|---|
| f0642 | `509259470_..._n.jpg` (raiz da NOVAS) | 2048x887 | 1,22x | lanczos |
| f0643 | `digitalizar0001.jpg` | 1218x819, HP ojj3600 | 1,58x | rede neuronal |
| f0644 | `digitalizar0002.jpg` | 1213x811, HP ojj3600 | 1,58x | rede neuronal |
| f0645 | `digitalizar0006.jpg` | 1235x816, HP ojj3600 | 1,55x | rede neuronal |
| f0646 | `IMG_0226.JPG` | 2592x1944, 22/05/2011 | não cresce | original |

Nenhuma tem o mesmo conteúdo de outra (sha256). A `digitalizar0002.jpg` tem nome parecido
com a `digitalizar0002 (2).jpg` (f0561), mas o conteúdo é diferente: não é duplicado.
As três digitalizações têm data EXIF de março de 2014, que é o dia do scanner e não o da
fotografia. Ficam 646 fotos, todas prontas.

Comparados recortes do original e da versão final: as feições ficam as mesmas nas cinco.
Na `digitalizar0006.jpg` a rede neuronal alisou o grão da digitalização, e a pele do
senhor fica mais lisa do que na foto; as três estão mesmo acima do limite de 1,5x. A
`digitalizar0002.jpg` e a `digitalizar0006.jpg` trazem margem branca do scanner nas
bordas. Nada disto foi mudado sem o Tiago.

**Razão:** o Tiago, *"analisa as fotos novas que meti na pasta. Revê se é preciso
tratá-las"*.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-15 | 066 | Enquadramento por foto, e a Mesa guarda por número de revisão

**Decisão:** cada foto em fiel ou fundo passa a ter, na Mesa, o campo Enquadramento:

| Valor | No render |
|---|---|
| a encher, com zoom lento (omissão) | Como sempre: encaixada a 112% e a aproximar |
| afastada | Inteira a 80% do tamanho, com o fundo à volta, a respirar 4% |
| parada | Encaixada, sem zoom |

Vai no campo `e` do clip, e o `montar_da_mesa.py` põe-no na coluna `movimento`
("Afastada" ou "Parada"), que o render passou a ler. Os valores antigos ("Zoom in",
"Nenhum" das v1) continuam a dar o que davam. A `IMG_0622.JPG` (f0593) ficou afastada.

**Razão do enquadramento:** o Tiago, *"Está com um zoom muito grande na foto do Tiago"*,
e depois *"a do zoom era esta"* com a IMG_0622. O render não a cortava: é um plano
apertado de proporção 1,5 que já enche a altura, e o zoom lento de 12% aproximava-o
mais. A primeira pista, a `21-49-4.jpg` em rajada, era outra foto.

**A guarda por revisão:** a 15 de setembro, às 09:01, uma Mesa com a cópia de 00:04
gravou outra vez por cima da reposição das 08:14 (versão 1145 igual à 1143). A base
aceita qualquer gravação da página, e a guarda por data deixava passar uma cópia com
data mais recente. O documento leva agora `rev`, que sobe a cada gravação, e a Mesa só
grava se a base ainda estiver na revisão que ela abriu. Uma Mesa aberta com a página
antiga não tem esta guarda: tem de ser recarregada.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-15 | 067 | A colagem e a pilha chegam ao render e à Mesa

**Decisão:** os tratamentos B e D do menu aprovado (decisão 017) passam do ensaio
`teste_estilos.py` para o render, a montagem e a Mesa, como grupos de fotos:
`{t:"colagem"|"pilha", fotos, x, d, c, r, orig}`.

| | Colagem | Pilha |
|---|---|---|
| Fotos | 2 a 5 | 2 a 8 |
| Como entra | Uma a uma, inteiras, com moldura clara e os ângulos do ensaio, a chegar 14% maiores e a assentar | Caem de cima, tortas, com os ângulos e desvios do ensaio, e o monte cresce |
| No fim | O quadro inteiro respira 3% | O monte recua 10% |
| Fundo | A primeira foto desfocada e escurecida | Escuro liso |
| Duração proposta na Mesa | 3 + 1,6 por foto | 2,6 + 0,85 por foto |

**Garantias medidas, com testes:** nenhuma foto pousada sai do quadro nem fica por
baixo da legenda; na colagem as caras (miolo e terço de cima) ficam à vista e o ponto
de foco nunca é tapado pelas que chegam depois; cada foto pousa antes de a seguinte a
tapar; a composição sub-pixel usa sprites com margem de alfa zero; fotos em falta não
param o render. A duração mínima é `max(0,35; encadeado de entrada) + n × entrada +
(n - 1) × 0,1 + 1,4 + encadeado de saída`, com 0 de entrada no primeiro clip do corpo e
o fade a preto como saída no último. Abaixo dela, o `montar_da_mesa.py` avisa e a Mesa
marca o clip como "curta".

Na Mesa: Tratamento de uma foto ("colagem de 3, esta e as 2 seguintes"), botões na barra
dos clips escolhidos, mudar entre lado a lado, colagem e pilha, ordem das fotos,
separar, pré-visualização aproximada. O esticamento do cartão do nascimento passou a
contar também um grupo de fotos logo a seguir.

**Disposição da colagem:** filas de até 5 fotos, com as proporções verdadeiras, e a
partição escolhe-se pela área final, depois de afastar as fotos para não taparem caras.
Entre as que dão pelo menos 90% da maior área, ficam as que chegam a 95% da melhor foto
mais pequena, e dessas a de maior área. Assim 4 ou 5 verticais ficam numa fila com 37 a
54% do ecrã, e nenhuma disposição abdica de área a troco de quase nada.

**Clip curto de mais:** a agenda encolhe por esta ordem, e cada foto pousa sempre antes
de a seguinte a tapar e antes do fim do clip: a folga até 0,6 s parada antes do
encadeado de saída, a entrada até 0,12 s, a espera pelo encadeado de entrada.

Três rondas de revisão, cada problema confirmado por um segundo revisor e cada correção
desfeita em memória para confirmar que um teste falha. 64 testes a passar.

**Decidido a seguir (068):** o Tiago quis as duas opções em cada uma.

**Razão:** o Tiago, *"No tratamento também falta o efeito Colagem que já tínhamos
criado antes"* e *"Garante que as funcionalidades que já desenvolvemos ficam já
preparadas para utilização na mesa de montagem"*.

**Quem:** Tiago.

**Substitui:**

---

### 2026-09-15 | 068 | Dois estilos na colagem e dois na pilha, à escolha em cada clip

**Decisão:**

| Tratamento | Estilo | Como fica |
|---|---|---|
| colagem | em filas (omissão) | Fotos grandes arrumadas em filas, como ficou na 067 |
| colagem | espalhada | Como no ensaio de 10 de setembro: a primeira maior e as outras de tamanho a descer, espalhadas e tortas |
| pilha | em monte (omissão) | Como no ensaio: as de baixo ficam quase tapadas |
| pilha | em leque | Abrem-se para as de baixo espreitarem sempre |

Na Mesa escolhe-se no Tratamento do grupo ("colagem espalhada, como no ensaio",
"pilha em leque, as de baixo a espreitar"), e o clip guarda `estilo`. O
`montar_da_mesa.py` põe-no na coluna `tratamento`, que o render lê nestes dois tipos.
Sem estilo, ou com um valor desconhecido, fica a omissão, e as montagens já feitas não
mudam. Os estilos novos têm as mesmas garantias e a mesma duração mínima dos de omissão.

**Espalhada:** tamanhos do ensaio (760, 660, 600, 540, 400 px, passados a área), centros
por número de fotos, ângulos do ensaio. Prefere as disposições espalhadas de verdade:
os centros ocupam pelo menos metade da altura média das fotos, nenhuma foto fica solta,
e a área total fica acima de 20% do ecrã com a primeira acima de 7%. Isto custa área (3
verticais sem legenda passam de 65% para 41% do ecrã), mas é o que a faz parecer o
ensaio. Onde não há nenhuma assim, fica a de mais área: duas verticais ou uma deitada e
uma vertical continuam lado a lado, e algumas colagens altas com legenda ficam em escada.

**Leque:** as fotos ocupam lugares da esquerda para a direita de fora para dentro (a 1.ª
no extremo esquerdo, a 2.ª no direito, a de cima no meio), com os ângulos da pilha; cada
foto de baixo fica com pelo menos 20% à vista no fim.

Colagem em filas e pilha em monte continuam iguais byte a byte ao que eram. 77 testes a
passar, e cada garantia nova desfeita em memória para confirmar que um teste falha.

**Razão:** o Tiago, perguntado se queria a colagem em filas ou espalhada e a pilha
tapada ou a espreitar: *"Mete ambas as opções, assim fica mais claro e mais fácil e
dá-me opções para criar o vídeo"*.

**Quem:** Tiago.

**Substitui:** o "por decidir" da 067.

---

### 2026-09-15 | 069 | A Mesa passa para um documento novo e só grava depois de ler a base

**O que aconteceu:** às 12:15 a montagem voltou a ser apagada, desta vez com a demo com
que a Mesa arranca: o flash-forward ficou com 7 clips, sem marcações nem exclusões
(versões 1147 e 1148). Uma Mesa que não conseguiu ler a base ficou com a demo, e as
páginas antigas gravavam sem esperar pela leitura. O Tiago deu por isso ao abrir a Mesa:
*"parece que a ordem que eu tinha definido e que estávamos a fazer render já não é a
versão"*. Foi a terceira vez no dia, depois das duas cópias velhas da 066.

**Decisão:**

| | |
|---|---|
| Documento | A Mesa lê e grava em `montagem/estado2`. As páginas antigas continuam a escrever em `montagem/estado`, que já ninguém lê |
| Leitura antes de gravar | Nada vai para a base antes de a Mesa ler a versão guardada. Se a leitura falhar, avisa e tenta outra vez sozinha |
| Documento novo em falta | Traz o antigo uma só vez; nunca grava a demo |
| Revisão | Mantém-se a guarda por número de revisão da 066 |

A montagem foi reposta a partir da 1146 (versão 1149 do documento antigo, com revisão
2) e copiada para o `estado2`.

**Às 12:25, quarta perda, já no documento novo:** ficou lá outra vez a demo de 7 clips,
com revisão 1, segundos depois de a página ser publicada ao mesmo tempo que o `estado2`
era gravado. Uma Mesa aberta nesse intervalo não encontrou o documento novo e gravou
sozinha o que tinha. As horas das perdas anteriores coincidem também com publicações.
Foi reposta (versão 3 do `estado2`, revisão 3) e juntaram-se duas guardas:

| | |
|---|---|
| Ao abrir nunca se grava | A Mesa só grava quando o Tiago muda alguma coisa, e só depois de ter lido uma montagem que existe. Sem documento novo nem antigo, avisa e não grava nada |
| Nunca encolher a metade | Recusa substituir uma versão da base por outra com menos de metade dos clips, e avisa |

E eu deixo de gravar na base ao mesmo tempo que publico: publica-se primeiro, e só
depois se confirma e, se for preciso, se grava. Testado no browser com uma base falsa: migração do
documento antigo, gravação só no novo, e duas leituras falhadas sem nenhuma gravação e
com a montagem certa no fim.

**Quem:** Claude, por causa do defeito que o Tiago viu.

**Substitui:** o documento `montagem/estado` das decisões anteriores.

---

### 2026-09-15 | 070 | Texto opcional em cada foto das colagens, pilhas e lado a lado

**O que o Tiago pediu:** *"gosto muito permite colocar o texto nas fotos mesmo as que
ficam em leque e assim, tem de ser opcional ter o texto ou não"*.

**Decisão:** cada grupo de fotos (lado a lado, colagem em filas ou espalhada, pilha em
monte ou em leque) passa a poder levar um texto em cada foto, além da legenda de baixo,
que fica como estava.

| | |
|---|---|
| Na Mesa | caixa "Texto em cada foto" no inspetor do grupo (`vf`) e um campo por foto (`xf`, na ordem de entrada). Ao juntar, cada foto traz o texto que tinha, desligado. Desligar não apaga. Subir e descer trocam também o texto. Separar devolve o texto à foto solta |
| No CSV | coluna `textos_fotos`, JSON da lista, só com a caixa ligada e algum texto |
| No render | faixa escura (alfa 165, o da legenda) dentro da foto, encostada ao fundo e dentro da moldura, texto Arial bold branco centrado, tamanho 36 a descer até 28 para caber em 2 linhas, reticências e aviso se não couber. Desenhada na foto antes da moldura e da rotação: roda, entra e é tapada com ela. Ponto de foco na faixa manda-a para o topo. No lado a lado fica no fundo da célula, acima da legenda do grupo |
| Sem textos | nenhum pixel muda: 1090 casos e 7730 fotogramas comparados byte a byte com o render de antes, e um teste de assinaturas md5 na suite |

**Verificado:** 90 testes (eram 77), 23 mutações do render e 9 dos testes novos
apanhadas, Mesa testada no browser com uma base falsa. Publicada como versão 28, e o
`estado2` continua na versão 3 com 156 clips.

**Fica por corrigir na ronda seguinte (decisão 071):** na colagem a fila de baixo tapa
a faixa da de cima; no lado a lado sem legenda o texto fica a 20 px do fundo do ecrã; a
pré-visualização do 3s com legenda esconde texto atrás do cartão; a letra é pequena para
15 metros (maiúsculas de 20 a 27 px contra 33 na legenda); na pilha o texto das fotos de
baixo fica tapado pela seguinte.

**Quem:** o Tiago pediu; Claude construiu e verificou com agentes.

---

### 2026-09-16 | 071 | Textos dos grupos: na legenda de baixo a mudar, tamanho da letra, texto tapado na pilha, ponto de foco

**O que o Tiago pediu (15 de setembro à noite):** a opção de os textos irem para a
legenda de baixo *"a alterar, assim pode ser uma forma mais fácil de o texto ficar
legível"*; na pilha, que o texto das fotos de baixo *"ficar lá e para desaparecer ser algo
que eu escolho"*; letra maior, *"mas permite também que eu possa selecionar o tamanho que
quero"*; e o ponto de foco em cada foto com texto, para a faixa não tapar caras.

**Decisão:**

| | |
|---|---|
| Onde aparece o texto (`vm`) | sem texto por foto; em cada foto; na legenda de baixo a mudar com cada foto. Na legenda, o texto da foto k entra quando ela começa a entrar e fica até a seguinte começar; foto sem texto mostra a legenda do grupo; a faixa tem a altura do texto mais alto do clip e as fotos não mudam de sítio; troca com encadeado de 0,2 s; textos iguais seguidos não trocam. `tempos_legenda_grupo()` no render e a mesma conta na Mesa, que avisa abaixo de 1,5 s |
| Tamanho da letra (`tt`) | 28 a 90, omissão 46 (o da legenda). O mínimo é 0,78 do tamanho, para caber em 2 linhas |
| Pilha, texto das fotos de baixo (`vt`) | omissão: desaparece em 0,2 s quando a seguinte cai; "fica à vista" mantém-no |
| Ponto de foco | em cada foto com texto, no inspetor, com a zona da faixa desenhada; foco na faixa manda-a para o topo |
| CSV | coluna `textos_opcoes`, JSON só com o que difere da omissão: `{"modo": "legenda", "tamanho": 56, "tapadas": "fica"}` |

**Corrigido do 070:** a fila de baixo da colagem já não tapa a faixa (vai para o topo, e
avisa se o topo também for pisado); no lado a lado a faixa guarda a margem da legenda
(texto até A-70) e o foco do topo da faixa para baixo manda-a para cima; a
pré-visualização do 3s; booleanos no texto; avisos com contagens certas.

**Verificado:** 108 testes (eram 90), 46 mutações do render apanhadas mais as dos
verificadores; sem textos, igual ao byte às duas versões anteriores; com letra 36 e
"fica", igual ao byte à versão 28. Mesa testada no browser com uma base falsa. Publicada
como versão 29; o `estado2` continua na versão 3 com 156 clips.

**Limites:** na pilha em monte, com "fica", uma foto pode tapar o texto de baixo por
inteiro (a montagem avisa com a percentagem das letras tapadas); no lado a lado 3s com
legenda e texto nas três ficam quatro faixas escuras em três alturas (por decidir); na
opção legenda um texto de duas linhas deixa a faixa alta o clip inteiro (avisa).

**Quem:** o Tiago pediu e escolheu; Claude construiu e verificou com agentes (Fable 5.1).

---

### 2026-09-16 | 072 | O aleluia está dentro dos foguetes, não é um ficheiro à parte

**O que aconteceu:** desde 12 de setembro a montagem tentava pôr `aleluia.mp3` por cima
dos foguetes do Tiago, porque o `.wlmp` da mãe da Clara tem um `aleluia.mp3` de 35 s a
seguir aos 7,5 s de `Candidato a vereador`, e como o ficheiro nunca chegou ao disco saía
um aviso de música em falta em cada montagem. O Tiago, ao ler o aviso: *"Não falei em
aleluia, referia-me aos foguetes. Se já apanhaste os foguetes é lá que está o aleluia."*

**Decisão:** o troço de `Candidato a vereador.mp3` a partir de 2:53 faz de foguetes e de
aleluia. A montagem deixa de procurar `aleluia.mp3`, o aviso desaparece, e o ficheiro sai
do ponto G. O som do vídeo não muda: o ficheiro em falta nunca tinha sido colocado.

**Verificado:** o troço é cantado e não ruído (planura espetral 0,01 em 173 a 180,5 s,
contra 0,05 no início do mesmo ficheiro). O ficheiro continua por mais 11 s depois do
troço usado, se um dia se quiser um aleluia mais comprido.

**Quem:** o Tiago.

---

### 2026-09-16 | 073 | O render desenha em fatias, com um só encoder

**O que o Tiago pediu:** *"se isso reduz o tempo de render sim quero isso implementado nos
próximos"*, com a condição *"só o quero se realmente a qualidade for igual à que temos tido
a fazer o render completo e se o tempo realmente baixar"*.

**Decisão:** o `render.py` lança 7 processos que desenham os fotogramas alternados (a
fatia k desenha os q com q % 7 == k) e o processo principal lê-os por ordem e entrega-os ao
único encoder, o ffmpeg de sempre com os mesmos parâmetros. Não há pedaços colados nem
segunda compressão: o encoder recebe os mesmos bytes pela mesma ordem. `--fatias 1` é o
caminho de antes; `--fatias auto` deixa um núcleo livre; `FATIAS_OMISSAO = 7`.

**Qualidade, provada igual e não parecida:** o mesmo troço do filme real (`--ate 120`)
renderizado nove vezes com 1, 4 e 7 fatias deu nove MP4 com o mesmo md5, e `ffmpeg -f
framemd5` igual nas 2200 linhas; o mesmo com `--ate 60` e `--ate 150`, e contra o
`render.py` de antes desta decisão. Numa montagem sintética com clips de todos os tipos,
os fotogramas em bruto são iguais ao byte para 2 a 8 fatias.

**Tempo, medido com a máquina sozinha:** 2200 fotogramas do filme real em 333 s
sequenciais e 164 s com 7 fatias (178 s com 4): 2,04x nos fotogramas. Não é 7x porque o
PC é um i5-8265U de portátil, 4 núcleos físicos e 8 lógicos a 15 W, e cada fatia prepara
todos os clips. No filme inteiro os fotogramas passam de cerca de 45 min para 19 a 24, e o
render completo de cerca de 66 min para cerca de 44. O que sobra é sobretudo a cópia leve e
a do telemóvel, 15 min a `preset slow`, que não se mexeu.

**Guardas:** uma fatia que morre ou devolve menos bytes pára tudo com erro claro, mata as
outras e o encoder e apaga o `_corpo.mp4`; `--fatias` sem valor ou acima de 16 recusa-se.
Memória: cerca de 1,6 GB com 7 fatias, contra 0,6 GB sequencial.

**Verificado:** 113 testes (eram 108), 28 mutações apanhadas, revisão sem defeitos acima de
baixo. Oito renders parciais de prova ficaram registados no `renders.csv` e na pasta de
saída.

**Quem:** o Tiago pediu e pôs a condição; Claude construiu e mediu com agentes (Fable 5.1).

---

### 2026-09-16 | 074 | A Mesa nunca tinha lido a base: `data()` é uma função, não um campo

**O que aconteceu:** o Tiago viu no render das 08h41 que as colagens que fez na Mesa não
apareciam. A base (`montagem/estado2`) estava na revisão 3 desde 15/09 às 16h23 e nenhuma
gravação da Mesa dele tinha entrado desde então. A causa de raiz: o contrato 0.2.45 da
base devolve cada documento com o corpo numa função `data()`, e a Mesa lia `s.data` como
campo, que é `undefined`. **A Mesa nunca conseguiu ler a montagem guardada, em nenhuma
versão.** Isso explica os três apagamentos de 15/09 (as Mesas antigas, sem encontrarem nada
na base, gravavam por cima a cópia do aparelho) e o silêncio desde a versão 27 (as Mesas
novas, que só gravam depois de ler, nunca mais gravaram). Os testes não o apanharam porque
a base falsa do harness devolvia um campo.

**Decisão:** a Mesa lê o documento por `dadosDe(s)`, que aceita as duas formas e copia em
profundidade (o corpo vem congelado). E ganhou o que faltava para nunca mais perder
trabalho em silêncio:

| | |
|---|---|
| Leitura persistente | tenta ler a base até conseguir (4, 8, 16, 32, 60 s), com uma faixa fixa a dizer o erro devolvido e a hora da próxima tentativa, e "Tentar agora" |
| Erros visíveis | um `get()` ou `set()` que falha mostra a mensagem; novas tentativas com espera a crescer, sem repetir em erros definitivos |
| "Guardar agora" | ao lado do ponto de sincronização; se não grava, diz exatamente porquê |
| Faixa de por gravar | mudanças locais que ainda não estão na base, com o motivo e desde quando |
| Cópias do aparelho | `mesa_montagem_conflito` passa a ser uma lista, lida no arranque: faixa com a data da cópia e os clips por versão contra a base, e os botões Ver, Guardar e Apagar esta cópia. A decisão de guardar uma cópia de lado é por conteúdo e linhagem, nunca por datas |
| Cada edição em disco | `marcar()` escreve `mesa_montagem` no próprio momento, antes de tentar gravar |

As guardas de 069 ficam todas: nunca gravar ao abrir, nunca gravar sem ler, nunca encolher a
menos de metade, conflito por revisão.

**Verificado:** quatro rondas no browser com uma base falsa refeita à imagem do contrato
(`data()` como função, corpo congelado, rejeições com código), incluindo o caso do Tiago:
cópia local com uma colagem, base reescrita depois por fora, a cópia aparece na faixa e
"Guardar esta cópia" grava-a. Publicada como versão 30.

**Limites conhecidos, por corrigir se aparecerem:** se o armazenamento do browser recusar
escrever (janela privada, quota), a faixa pode afirmar uma cópia que não ficou em disco; com
a base só no documento antigo (não é o caso: o `estado2` existe) a guarda de encolher não
corre; dois separadores com a mesma cópia aberta podem deixar uma cópia fantasma igual à
base.

**O que se segue:** o Tiago abre a Mesa no aparelho das colagens e carrega em "Guardar esta
cópia"; depois a junção, a montagem e o render.

**Quem:** o Tiago deu por isso; Claude encontrou a causa e corrigiu com agentes (Fable 5.1).

---

### 2026-09-17 | 076 | Grupos maiores, a duração repartida por foto, tirar e substituir, e o filtro das usadas

**O que o Tiago pediu:** *"aumenta a quantidade das fotos possíveis nas diferentes opções no
tratamento, em especial a colagem e a pilha"*; *"nestes casos das colagens e da pilha permite que
ao aumentar a duração o que faça seja dividir o tempo pelo número de fotos selecionadas"*, e a
seguir *"pode ser com a última a ficar o dobro, e provavelmente também a primeira tem de descontar
um bocadinho, caso contrário a primeira nunca tem o efeito"*; *"permite que se uma foto estiver
numa pilha nos possamos eliminar e depois pergunta se quero substituir por outra ou quero reduzir o
número de fotos da pilha"*; e *"cria um filtro de checkbox que permita não mostrar todas as fotos
que já estão na montagem"*.

| | |
|---|---|
| Quantas fotos | colagem 2 a 12, pilha 2 a 20, lado a lado com a disposição nova 6g, duas filas de três |
| Tempo | `vez = (duração − atraso − saída) / (n + 1)`: cada foto tem uma vez e a última duas, para se ver o conjunto completo. O encadeado de entrada desconta-se antes de dividir, por isso a entrada da primeira vê-se inteira. Sem intervalo máximo: aumentar a duração aumenta o tempo de cada foto |
| Tirar uma foto | o `×` em cada linha do grupo pergunta: substituir por outra, escolhida na biblioteca, ou reduzir o grupo. A reduzir, o tempo por foto mantém-se e a duração desce uma vez; com uma foto só, o grupo passa a foto solta |
| Filtro | "Esconder as que já estão nesta montagem", por versão, guardado no aparelho, com o número de escondidas |
| Lembrete | num grupo acima do limite legível e com texto em todas as fotos, a Mesa lembra que a faixa tapa quem lá está e oferece "Pôr na legenda de baixo". Nunca impede |

**Verificado:** 127 testes (eram 121), as disposições e os sprites iguais ao byte aos de antes em
2990 casos, e o render com a agenda antiga injetada dá os mesmos fotogramas, o que prova que só o
tempo mudou. Sete erros postos de propósito que passavam sem teste ficaram presos, incluindo a
conta do tempo da Mesa contra a do render. Publicada como versão 31.

**O que ele viu e aprovou (folha dos grupos grandes, 17 de setembro):** a partir de 9 ou 10 fotos o
grupo passa a ser um efeito de conjunto. O leque de 15 achata numa faixa, a espalhada de 12 lê-se
como uma grelha e um monte de 20 acaba com 12 fotos tapadas. *"Todos os exemplos que enviaste gostei
bastante"*: fica assim, com avisos e sem travões.

**Quem:** o Tiago pediu e escolheu; Claude construiu com agentes e fechou o lembrete à mão.

---

### 2026-09-17 | 075 | O pedido entra na abertura, entre dois rebobinares

**O que o Tiago decidiu (fecha o ponto I em aberto):** *"O rebobinar inicial cria-me na mesa um que
rebobina da data de hoje até à data de 25 de dezembro de 2025. Aqui vou meter a foto do pedido e
os áudios que já cortámos do pedido, eu depois decido a sequência dos áudios, mas aqui vão ser 2
fotos e esses áudios. Depois rebobina para 1995 como já está implementado."*

**Decisão:** a abertura da v3 passa a ser: os dois vídeos, um contador por datas de 4 de outubro
de 2026 a 25 de dezembro de 2025, duas fotos do pedido com as vozes do pedido por cima, o contador
2025>1995 e a fita de 1995 como está. As vozes são os pedaços de `gerados/pedido_pedacos`, na
ordem que ele escolher na Mesa; a música da abertura continua mais baixa por baixo delas. A regra
"nenhuma narração falada" fica de lado neste momento por escolha dele: é o som do pedido, não
narração.

**A data é 25 de dezembro de 2025, de manhã**, confirmada por ele. O EXIF das quatro fotos do
pedido (f0347 a f0350) diz 24/12/2025 e está errado; o inventário continua com o EXIF, mas a
data que vai ao ecrã é a dele.

**Quem:** o Tiago.

---

### 2026-09-18 | 077 | Um vídeo pode estar no meio do filme, e é desenhado lá dentro

**O que o Tiago pediu:** para a intro nova, a seguir à fanfarra da 20th Century Fox e ao vídeo
da história da Clara, *"Fotos: Anel: IMG_2067 & Reação ao ANúncio:20260101_011410, 20260101_011607.
Som: 1_07_04m09s_dura02.0s e curta pausa 2_13_04m40s_dura03.5s. Após as fotos: Video do Homer
Simpson que meti em videos. Mas apenas um dos trechos em que ele diz o seu Doh, preferencialmente
o mais longo. Aqui quero o video e o som. E depois continuava como estava."*

**Decisão:** o render deixa de mandar todos os vídeos para a frente do filme. A fanfarra passa a
ser só o **bloco inicial**, ou seja os vídeos que estão antes de qualquer outro clip; um vídeo a
seguir a uma foto, a um cartão ou a um contador é um clip do corpo como outro qualquer, com o seu
encadeado, o seu lugar no relógio e o som dele. A conta é uma só,
`render.partir_em_fanfarra_e_corpo()`, e o `montar_da_mesa.py` e o `som_para_mesa.py` leem-na de
lá em vez de terem uma parecida.

| | |
|---|---|
| Como é desenhado | antes de lançar as fatias, o processo principal extrai os fotogramas do troço para `saida/_cache/_quadros_<montagem>_<ordem>/` (JPEG, 1920x1080, 25 fps) e apaga a pasta no fim. `--guardar-quadros` deixa-a; `--quadros-grandes` aceita mais de 30 s de vídeo no corpo, que é o travão para não encher o disco |
| Campos do clip | `f` (ficheiro), `vin` (segundo de entrada), `d` (duração do troço; 0 quer dizer o ficheiro inteiro a partir do `vin`). O montar mede o ficheiro com o ffprobe, avisa quando o troço não cabe e corta ao comprimento |
| Colunas novas | `in_s` e `out_s` no CSV da montagem; `voz`, `abafar` e `video` no `som.csv`. Só aparecem quando há o que escrever nelas: sem vozes e sem vídeos no corpo, os dois ficheiros saem iguais ao byte aos de antes |
| Som do vídeo | uma faixa que aponta para o próprio ficheiro, com o segundo de entrada e a duração do troço, ganho 1,0 e a nota «som do vídeo». Não é leito: nem leva loudnorm, nem cruzamento, nem é cortada por uma música marcada |
| A música por baixo | baixa 12 dB, ou pára, pelo campo `vzm` do clip, o mesmo mecanismo das vozes do pedido. A janela conta com o cruzamento de 2,2 s do render, senão o leito que sai toca por cima sem baixar |
| Contador por datas | `04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido` anda dia a dia, com a régua dos meses por baixo. Acima de três anos troca sozinho para o contador de anos e diz que trocou. Dois contadores encostados entram com **corte seco**, pela regra do conteúdo diferente |
| Vozes do pedido | campos `vz` (lista de ficheiros) e `vzm` num clip; os pedaços vêm de `gerados/pedido_pedacos` e a Mesa mostra-os no inspetor |
| Referência do byte | `data/montagens/referencia/` guarda o v3.csv e o v3.som.csv que fizeram o último render. Congelá-la é um acto deliberado, `py -3.11 scripts/testes.py --congelar-referencia` |

**Razão:** um vídeo posto a meio da montagem ia parar ao início do filme com o concat, e o corpo
ficava com um buraco onde ele estava, porque o ciclo dos fotogramas, sem nenhum clip activo, caía
no último clip do filme. A piada do Homer só existe se ele passar onde ele o pôs.

**O que fica na mão do Tiago:** o troço do Homer que ele escolheu tem sete «D'oh» de sete cenas
diferentes e oito planos em 3,47 s, e duas das três fotografias do pedido não se leem a 15 metros.
Está tudo medido e escrito no relatório da ronda; nada disso se muda sem ele.

**Quem:** o Tiago pediu; Claude construiu e mediu.

---

### 2026-09-21 | 078 | A intro do pedido: aproximar ao anel, o D'oh parado, e contadores que se leem

**O que o Tiago pediu, depois de ver os dois primeiros conceitos:** *"Podes cortar e aproximar, mas
tens de começar do plano amplo para verem a árvore de Natal"*; *"o Homer está a entrar e sair muito
rápido. Será que conseguimos meter o vídeo ainda sem play, esperar 1 s e depois reproduzir"*; as duas
vozes antes das fotos do anúncio, porque a segunda fala de o contar às pessoas; um só D'oh, o dos
6 segundos, um pouco mais lento; e o cartão "Mas como é que chegámos aqui?" antes do rebobinar para
1995.

| | |
|---|---|
| Enquadramento "aproxima" | campo `e = "aproxima"` e `az` (zoom no fim, 1,2 a 4,0, omissão 2,2). A foto começa exatamente como qualquer outra, fica **1 s parada no plano amplo** depois de o clip anterior sair, aproxima até o ponto de foco ficar ao centro com uma curva que arranca e trava devagar, e fica **1 s parada** antes do encadeado de saída. Num clip curto as duas paragens encolhem por igual (`APROXIMA_PARADO`, `aproxima_curva()`). A borda da foto nunca entra no quadro |
| Contadores | o de anos e o de datas passam a ser a mesma fita: algarismo com o mesmo tamanho, legenda à mesma altura, ponteiro visível (6 para 1 de contraste, era 1,27), meses em maiúsculas a 46 px, régua de borda a borda. Muda de propósito o contador que já estava no filme |
| O D'oh | `gerados/homer_doh/homer_doh_parado_e_lento.mp4`: o plano dos 5,99 aos 6,44 s, abrandado para 60%, com 1 s do primeiro fotograma parado à frente. 1,8 s no total |
| O conceito | versão `conceito_pedido`, só no `data/mesa_estado.json` até ele dizer que a quer na Mesa: anel com 8,5 s, zoom 3,5 e foco na aliança (0,393; 0,741), as duas vozes por cima dele, as duas fotos do anúncio, o D'oh, o cartão, o contador 2025>1995 e o filme como estava |

**Porque as paragens:** sem elas a árvore via-se inteira 0,72 s e o anel no tamanho final menos de
1 s, e o fim parava a seco a 94% do zoom (verificador, 18 de setembro). É o pedido dele à letra.

**Aviso que fica:** os dois vídeos de abertura estão muito abaixo da música (a fanfarra a -30,7 LUFS e
o vídeo da Clara a -49,5, contra -23). O montar avisa; igualá-los muda o ficheiro da v3 e fica para
ele decidir.

**Quem:** o Tiago pediu e escolheu; Claude construiu com agentes e fez as paragens à mão.

---

### 2026-09-21 | 079 | A abertura fica sem o Homer e sem as vozes, e o pedido anda ao compasso da Mariah

**O que o Tiago decidiu:** *"A Clara não gostou do conceito inicial do Homer e da voz dela.
Portanto acabamos por ficar com a Intro estilo marvel, uma pequena pausa depois o rebobinar até
ao pedido, as fotos da árvore com close up no anel e a foto da celebração com os abraços que já
está."* A música no pedido é a *All I Want for Christmas Is You (Make My Wish Come True
Edition)*, a partir dos 42 s. E pediu a intro da Marvel *"com uma distribuição mais equitativa das
fotos da Clara e do Tiago"*, a acabar numa foto dos dois antes de aparecer o letreiro.

**A música, medida e não adivinhada:** aos 42,5 s começa a última frase lenta; a nota longa do
"you" vai de 53,3 a 57,4 s; a bateria entra aos **57,47 s**, a 150 bpm (compasso de 1,60 s).
Daqui saem os tempos, todos em cima de compassos:

| Clip | Entra | Na música |
|---|---|---|
| O anel (f0260, aproxima 3,5) | com a música | 42,0 s |
| O abraço (f0052, aproxima 2,0 ao abraço) | corte seco | 57,47 s, a bateria |
| O brinde (f0053) | corte seco | 63,87 s, 4 compassos depois |
| O cartão "Mas como é que chegámos aqui?" | encadeado | 70,27 s, fim da frase de 8 compassos |

No cartão a Mariah desce em 2,2 s e o Lang Lang volta onde tinha parado no rebobinar das datas
(13,3 s do ficheiro), para o rebobinar até 1995. O anel fica 15,47 s: a aproximação chega ao anel
durante o "you", e o abraço entra na bateria. Medido no render: o corte para o abraço cai 24 ms
depois do ataque do bombo, menos de um fotograma.

**A intro da Marvel, terceira versão** (`gerados/intro_marvel/intro_clara_tiago_3.mp4`; a de 12 de
setembro e a 2 ficam intactas, e a de 12 é a única cópia do som):

| | |
|---|---|
| As fotos | vêm da demo_v3, pela ordem do filme, e a classe vem só das etiquetas dele na Mesa ou da coluna `pessoa` do inventário |
| O equilíbrio | as 40 primeiras posições são repartidas por **tempo de ecrã**, nunca mais de duas seguidas do mesmo: Clara 19 fotos e 1,99 s, Tiago 21 fotos e 2,04 s. Na de 12 de setembro eram 4,00 s contra 1,40 |
| O fim | 8 fotos dos dois e o pouso na f0286 (a selfie do estádio, 2025), cortada centrada nas caras, que fica enquanto as letras se formam por cima |
| O início | preto como no Marvel original, e a primeira foto acende só nos últimos 0,4 s, já no corte do folhear (acabou o salto das 1,15 s) |
| A pausa | 1 s de preto e silêncio no fim da intro |

**A 22 de setembro, depois de ver a intro 3:** *"agora as fotos estão muito rápidas (diria que está
muito mais rápido desde o início que a versão anterior) e a nossa foto no estádio aparece agora de
forma pouco natural e fica muito tempo até desaparecer."* Tinha razão nas duas, medido: a intro 3
punha 48 fotos em 4,35 s a ecrã inteiro (a primeira com 0,30 s, as últimas a fotograma e meio), e a
de 12 de setembro punha 64 em 7,85 s, com as mais rápidas já escondidas dentro das letras; e a selfie
entrava em corte seco a seguir ao troço mais rápido e via-se de 5,5 s a quase 10 s. A **intro 4**
(`intro_clara_tiago_4.mp4`) volta à curva de 12 de setembro (a primeira foto com 0,45 s), abranda as
3 últimas fotos, já dos dois (0,12, 0,16 e 0,21 s), faz a selfie entrar às 6,3 s, quando as letras
começam, e sobe o vermelho à volta das letras em 1,3 s em vez de 2,7. Com menos posições a repartir:
Clara 13 fotos e 2,27 s, Tiago 14 fotos e 2,24 s, e 6 dos dois. O pedido fica como está: *"para já
fica como está e depois vemos se precisamos de ajustar mais"*.

**Depois de ver a intro 4:** *"Mas o folhear no áudio não parou, acho que podemos incluir mais fotos
antes das nossas selfies e até acho que podem continuar a passar selfies com as letras já lá desde
que sejam nossas."* Medido no som: há páginas a virar de 1,2 s até perto dos 10 s. A **intro 5**
(`intro_clara_tiago_5.mp4`) folheia como o original, sem parar, à curva de 12 de setembro:
antes das letras, 35 fotos de cada um (Clara 17 e 2,67 s, Tiago 18 e 2,68 s); quando as letras
começam, às 6,3 s, só fotos dos dois, 41, todas etiquetadas por ele como "Clara e Tiago" (a demo_v3
não tem tantas; as outras vêm das etiquetas dele, sem repetir), a passar por dentro das letras até às
10 s; e a selfie do estádio é a última, dentro do letreiro quando ele fica sólido. O vermelho volta
aos 2,7 s do original.

**Uma correção que vale para o filme todo:** uma música marcada na Mesa passa a parar nos foguetes
de um nascimento, como o Lang Lang automático. Sem isso o Lang Lang retomado no cartão tocava por
baixo dos foguetes do Tiago inteiros. A demo_v3 de hoje sai igual ao byte.

**Fica com ele:** a versão `conceito_mariah` só existe no `data/mesa_estado.json`, e o
`juntar_mesa.py` reescreve esse ficheiro com a base; o nível dos dois vídeos de abertura (a Fox a
-30,7 LUFS e a intro a -49,5, contra -23 da música), que agora se nota mais porque a Mariah entra
logo a seguir.

**Quem:** o Tiago e a Clara decidiram; Claude mediu a música, construiu com agentes e verificou.

---

### 2026-09-22 | 080 | Tirar as máscaras de uma foto, com as caras verdadeiras e nunca inventadas

**O pedido, tarefa paralela ao vídeo:** na pasta `trabalho/04-Tratamento_Imagem_fora_video`, a foto
*"WhatsApp Image 2026-09-21 at 12.06.46"* tem um casal de máscara. *"Precisa de ter uma foto com
qualidade deles sem a máscara apenas, mantendo tudo o resto e o espaço que a máscara tapa deve ser
igual às fotos deles."* Deixou 14 fotos de referência na mesma pasta.

**Como se fez, e porquê assim:** a parte de baixo de cada cara vem de uma foto verdadeira dele e
dela, e nada é desenhado de novo, pela mesma razão que proíbe o GFPGAN e o CodeFormer. Para ele, a
das 14.25.05, do mesmo dia, de frente e com luz por igual. Para ela, a `530093408...`, de frente e
à sombra: a do mesmo dia (14.24.57) tem sol de lado e a aresta da sombra do nariz ficava como uma
mancha escura na bochecha. Alinhamento por olhos e queixo marcados à mão; passa só o pormenor da cara
verdadeira, e a luz e a cor vêm da própria foto com máscara, por fusão de Poisson. Não foi preciso
instalar nada: numpy e Pillow chegaram. `scripts/tirar_mascara.py`, pontos em
`data/sem_mascara_pontos.json`, saída em `gerados/sem_mascara/` (nunca por cima de nada).

**O que muda na foto:** 18 406 pixéis, só dentro das duas caras; o resto é a foto dele.

**Rejeitado pelo Tiago, com razão:** *"parecem mais estranhos que ETs agora"*. Passar só o pormenor e
baixar o contraste para menos de metade tirou o volume às caras (a sombra do nariz, as bochechas, o
queixo), e sem volume uma cara parece uma máscara de pele. Uma segunda tentativa com a cara inteira,
volume incluído, também não se aguenta: a barba dele sai um bloco escuro e a luz das fontes não é a
da foto. Juntar à mão caras de outras fotos, com outra luz e outro ângulo, a 100 pixéis de largura,
não chega a parecer natural. A proposta seguinte é um modelo de imagem local (Stable Diffusion
inpainting, em CPU) a partir desta composição com as feições verdadeiras, só para acertar a luz e a
pele; fica à espera da autorização dele para instalar.

**Autorizado a 22 de setembro** (*"sim autorizo, mas apenas para usares neste projeto que disse
que é fora do vídeo"*), tudo num ambiente isolado em `C:\Users\User 1\sd_mascara\` (venv próprio,
nada no Python do vídeo): Stable Diffusion inpainting (2,0 GB, para uma cara-base sem máscara),
insightface com o pacote `buffalo_l` (deteção, 106 pontos e vetor de identidade ArcFace) e a rede
`inswapper_128.onnx` (554 MB, do FaceFusion, descarregada pelo Tiago à mão porque a ferramenta
recusou o descarregamento; CRC32 `7057c6ea` confirmado). O modelo de imagem sozinho fazia
"um homem de barba" e "uma mulher a sorrir" genéricos (rejeitado: *"não se parecem nada eles"*).

**O método que ficou (v15):** (1) a análise automática das 15 fotos diz a pose de cada cara; na
foto com máscara ele está virado 19° e ela quase de frente, e as referências mais frontais e maiores
são a 14 e a 15 (do próprio dia) para os dois, mais a 5, 4, 2, 6 para ele e a 2, 9, 10 para ela;
(2) limpa-se no original o reflexo azul da máscara na pele à volta (`limpar_azul.py`), senão a
colagem arrasta ciano para dentro; (3) a cara-base é a parte de baixo de uma foto verdadeira (ele: a
15, do dia; ela: a 7, à sombra e de boca fechada, como pediu, *"conforme estava numa das fotos do
próprio dia com a Avó"*), deformada pelos 106 pontos para o sítio certo e colada por Poisson só
dentro do contorno (`base_real.py`); (4) a rede de identidade reescreve só a zona da máscara a
partir dessa base, com a identidade média de 4 a 5 fotos, os olhos e a testa ficam originais, e a
cor da pele nova acerta-se pela testa (`trocar_identidade2.py`); (5) avaliadores independentes
(semelhança, retoque, cético) comparam com as fotos dele, e a semelhança medida por ArcFace sobe
de 0,3 (cara genérica) para 0,77 nele e 0,81 nela. Proporções da boca e do maxilar medidas
(`medir.py`) contra as referências, para não sair estreita nem alta como saía do modelo.

**A entregue (v27, 22 de setembro à tarde), depois de treze rondas de avaliadores:** a zona
reconstruída fica presa ao contorno da cara (mais 6 px), sem as orelhas nem o colarinho; os restos
da máscara fora do contorno (as alças, o canto azul em cima do colarinho, o arame na cana do nariz,
a fiada de lantejoulas) são preenchidos a partir da vizinhança antes de qualquer colagem
(`limpar_fora`); a faixa exterior vem da cara-base do modelo, gerada com a zona alargada para ele
próprio pintar o pescoço; a cor da pele nova acerta-se pela testa medida pelos 106 pontos; a
reconstrução pára 2 px acima do rebordo da máscara, com rampa, para os olhos ficarem originais.
Notas dos seis avaliadores: ele 6 a 7 em semelhança e 6 a 7 em natural; ela 6 a 7 e 6 a 8, um
deles a dá como pronta. O que ficou por resolver e eles apontam: o nariz dele com pouco volume e
uma costura de luz sob os olhos que ao tamanho real passa por sombra; o nariz dela um pouco
estreito, e a pele nova mais lisa do que a testa. Ficheiro:
`gerados/sem_mascara/WhatsApp Image 2026-09-21 at 12.06.46 sem mascara v27.jpg`.

**Rejeitada pelo Tiago (22 de setembro à noite):** *"Piorou muito. Nesta versão estávamos a ir no bom
caminho e talvez o que precisasses fossem apenas ajustes"*, a apontar para a **v4 prévia**: a cara-base
do modelo de imagem e a rede de identidade a reescrever a cara inteira (semelhança medida 0,94 nos
dois). Ao restringir a rede à zona da máscara para proteger os olhos, e ao trocar a base por fotos
verdadeiras deformadas, a identidade caiu para 0,7 e a cara ganhou costuras. Lição: a força da v4
estava na rede a reescrever a cara toda; os olhos reescritos não incomodaram ninguém, as costuras sim.
E ela **não fica de boca fechada**: *"Prefiro a esboçar um sorriso, pois o comentário é que parecia que
não estavam contentes."*

**A v31 (entregue):** o caminho da v4 com dois ajustes. Ele: a mesma cara-base da v4, mas as alças e
o canto azul da máscara no colarinho preenchidos a partir da vizinhança antes da rede (`limpar_fora`).
Ela: a base é a foto 7 (à sombra, lábios fechados a sorrir) deformada para o sítio pelos 106 pontos, e
a rede reescreve a cara inteira por cima, como na v4. Semelhança medida 0,94 nele e 0,93 nela. Bases
do modelo com "sorriso suave" (sementes 8 e 9) saíram sérias e foram postas de lado.

**Quem:** o Tiago pediu e forneceu as referências; Claude escolheu as fontes e fez a composição.

---

### 2026-09-22 | 081 | A abertura nova entra na demo_v3, e a Mesa passa a ser a dele com ela

**O que o Tiago decidiu:** *"Quero sim, pois assim posso voltar à edição do vídeo para ver se o
fecho hoje."* A abertura da decisão 079 deixa de viver só na cópia local e passa a estar na montagem
dele, para ele poder trabalhar a partir dela.

**O que mudou na demo_v3:** os três primeiros clips (a Fox, a `intro_clara_tiago.mp4` de 12 de
setembro e o contador `2026>1995`) saem, e entram oito: a Fox, a `intro_clara_tiago_5.mp4` de 14,44 s,
o contador por datas até ao pedido, o anel, o abraço, o brinde, o cartão *"Mas como é que chegámos
aqui?"* e o contador `2025>1995`. Os restantes 193 clips são dele e ficam como estavam. A montagem
passa de 197 para 202 clips e o filme de 757 s para 798 s.

**E o contador de 1995 passa a corte seco para a fita**, `c: 0`, pela regra do conteúdo contínuo. A
demo_v3 ainda tinha o encadeado de 0,7 s que punha dois "1995" sobrepostos; o conceito já estava
corrigido, a montagem dele não.

**O que ficou na Mesa a mais:** a versão `conceito_mariah`, com os 16 clips da abertura, como versão
à parte. Serve para rever só a abertura sem esperar os quinze minutos do filme inteiro. Os pontos de
foco `f0052` e `f0260` entraram nos focos da Mesa, que são partilhados por todas as versões.

**A ordem da gravação, que é a de sempre:** ler a base, `juntar_mesa.py` (disse "nada", já estava
tudo), `montar_da_mesa.py demo_v3 --nome v3`, `gerar_mesa.py`, publicar, e só depois ler outra vez e
gravar o `montagem/estado2` com o `if_version` da leitura e o `rev` lido mais um.

**Um teste teve de deixar de assumir a abertura antiga.** O `teste_juncao_com_dois_contadores`
construía o caso dos dois contadores acrescentando o das datas ao estado vivo, e como a demo_v3
passou a tê-lo, ficava com três e falhava sem nenhuma linha de código ter mudado. É o mesmo defeito
do teste do byte, que falhava por o Tiago trabalhar. Agora as duas entradas constroem-se: tira-se o
que recua e não chega a 1995 para ter o caso de um, e acrescenta-se o das datas a esse para ter o de
dois. A junção em si estava certa, e continua a encontrar um só contador da abertura.

**E 46 fotografias novas na `01-NOVAS`**, largadas por ele a 21 de setembro à noite e na madrugada
de 22. Nenhuma repetida, confirmado por hash, nem entre elas nem contra as 646 já registadas. O
`atualizar_fotos.py` correu de ponta a ponta: 692 fotos, todas prontas, a rede neuronal em 6 delas
(79 no total), 44 folhas de prévias. A mesma corrida repôs os três ficheiros que faltavam na FINAIS
(f0375, f0636, f0638). Mesa publicada na versão 33, com o `montagem/publicacao` no build
`20260922-192947`.

**Fica com ele:** o nível dos dois vídeos de abertura (Fox a -30,7 LUFS, intro a -49,5, contra -23
da música), que continua por decidir.

**Quem:** o Tiago decidiu; Claude montou, publicou e gravou.

---

### 2026-09-22 | 082 | As quinze respostas do Tiago, e o que passa a ser trabalho da Mesa

**Como se chegou aqui:** ele pediu *"Diz-me de forma concreta o que pretendes que eu decida, se
tiver mais do que uma versão aponta-me para eu ver e decidir"*. Quatro agentes levantaram o que
estava em aberto, um crítico cortou o que não era decisão dele, e sobraram quinze. Ele respondeu a
todas.

| # | Decisão | O que ele disse |
|---|---|---|
| 1 | O fim do filme | Decide ele, na Mesa. Não se mexe |
| 2 | Os seis vídeos da `01-NOVAS` | Ficam visíveis na Mesa para ele se lembrar, mas quem os põe no filme é ele pelo chat, nunca pela Mesa |
| 3 | O nível dos dois vídeos de abertura | Fica como está, por agora |
| 4 | Os textos que passam depressa de mais | Não se corrigem: a Mesa marca-os com um sinal e ele edita. Antes de cada render pergunta-se-lhe se ficam |
| 5 | Os erros de escrita e o emoji | Vão para um validador na Mesa, acionado por um botão |
| 6 | As três piadas sobre a Clara | Ficam |
| 7 | Quais das 46 fotografias entram | Revê na Mesa |
| 8 | O ritmo igual do princípio ao fim | Não percebeu a proposta, portanto não se faz nada |
| 9 | A Clara vê o filme antes | Provavelmente não vê, e vai ser difícil |
| 10 | Como o filme chega à sala | **Projetado, com as colunas do DJ** |
| 11 | A fanfarra da Fox | Fica inteira, 20,8 s |
| 12 | Televisão ou projeção | **Projeção** |
| 13 | As dez vistas da quinta | Talvez no fecho, decide ele na Mesa |
| 14 | O voo sobre o mapa | Fica fora, por agora |
| 15 | Ponto G, as sobras da FINAIS, as versões v1 | Não se faz nada |

**O que isto fecha no registo:**

- **O ponto H fecha-se: é projeção**, com o som pelas colunas do DJ. A decisão 003 já mandava
  preparar para o caso mais exigente e continua a valer, agora por saber e não por precaução.
- **A fanfarra da Fox fica inteira, e isso substitui a decisão 006**, que mandava apará-la para 10 a
  12 segundos na v3. Ele: *"acho que fica inteira, nem me lembro de alguma vez ter sido outra
  opção"*. Há folga de tempo, o filme está abaixo do alvo.
- **O nível dos dois vídeos de abertura fica como está.** As cópias igualadas a -23 LUFS ficam
  guardadas em `gerados/som_igualado/`, prontas caso ele mude de ideias. Há uma informação nova que
  ele já tinha quando decidiu: sendo projeção com as colunas do DJ, quem está na mesa põe um volume
  para o filme inteiro, e os 27,6 dB entre a intro e a música não se corrigem na sala.

**O que passa a ser trabalho meu, na Mesa:** o sinal nos clips com texto a mais para o tempo que
têm, o validador por botão, e os seis vídeos da `01-NOVAS` visíveis na lista, marcados como ainda
não decididos.

**E uma regra nova de processo, que é dele:** antes de cada render pergunta-se-lhe se os textos
marcados ficam como estão ou se quer ajustar. Não se corrige texto dele sem ele dizer.

**O letreiro:** ele pediu que o texto do filme fique coerente com o *A HISTÓRIA DE / CLARA & TIAGO*
da intro, e abriu a porta a mudar a própria intro se fizer mais sentido. Hoje a intro usa Impact no
nome e Arial Bold espacado na linha de cima, e o filme inteiro usa Arial Bold. Fica por decidir com
amostras à frente.

**Um erro meu, para não se repetir:** mandei-lhe duas aberturas para comparar o som e eram iguais ao
byte. O `render.py` salta o bloco inicial de vídeos quando se lhe dá `--ate` (`if fanfarra and not
ate`), portanto um render parcial nunca mostra a abertura. As duas versões verdadeiras foram feitas
colando os vídeos à frente do corpo com os mesmos comandos do render.

**Quem:** o Tiago decidiu as quinze; Claude levantou, mediu e mostrou.

---
### 2026-09-22 | 083 | O validador, o sinal nos textos e os vídeos por decidir na Mesa

**O que ele pediu**, na decisão 082: os textos que passam depressa de mais levam *"uma pequena
menção com um icon"* para ele editar na Mesa; os erros de escrita vão para *"um validador que é
acionado se eu carregar no botão"*; e os seis vídeos da `01-NOVAS` ficam *"visíveis na Mesa"* mas
quem os põe no filme é ele pelo chat.

**O que ficou construído**, em `scripts/editor_base.html` e `scripts/gerar_mesa.py`:

| Peça | O que faz |
|---|---|
| Botão **Validar** | Corre as verificações na montagem aberta e mostra duas listas, «Está mal» e «Confirma tu». Não corrige nada, e não há um único botão que corrija |
| Etiqueta `⚠ texto` | No clip cujo texto não cabe no tempo que ele tem sozinho no ecrã. 31 na demo_v3 |
| Contador no cabeçalho | «N textos a rever», para ele saber quando acabou de os rever |
| Nota no inspetor | Por baixo da caixa do texto, quanto tempo aquele texto tem e quanto precisava |
| Botão **Vídeos por decidir** | Os seis da `01-NOVAS`, com a duração e os pixéis. Sem nenhum botão que os ponha na montagem |

**A conta do tempo é uma só.** O tempo que conta é o **sozinho no ecrã**, a duração menos o
encadeado com que o clip entra e o do clip que entra a seguir, que é o par de
`render.encadeados_do_corpo()`. Não é a coluna `solo_s` dos CSV, que é `dur - 2x` o encadeado do
próprio clip e difere em 51 dos 1147 clips das nove montagens. O limite, 12 letras por segundo,
sai de números que já existiam: `XF_LONGO = 32` letras no clip corrente de 4 s com 0,7 s de cada
lado. O `teste_mesa_marca_o_texto_que_passa_depressa` prende um ao outro.

**Dois defeitos que um verificador apanhou, e que ficaram corrigidos:**

- **O aviso que mentia.** O cartão do nascimento da Clara tem 3,6 s escritos na Mesa, mas o
  `montar_da_mesa.py` estica-o sozinho para 6,15 s, para os foguetes acabarem antes de a primeira
  foto entrar. A Mesa só via o número dele e marcava a vermelho um cartão que está bem. Agora a
  `duracaoNoRender()` usa a duração com que o render desenha, que já chega à página em
  `window.SOM_RENDER`, e fica sempre **o maior dos dois**: o montar só estica, nunca encurta, e se
  ele encurtar o clip na Mesa o número dele é o mais novo. Os marcados passaram de 32 para 31.
- **Os avisos que falhavam por pouco.** Cinco dos 32 falhavam o orçamento por menos de 0,3 s e
  estavam na secção que diz «isto sai errado no render». Um texto que pedia 2,7 s e tem 2,6 não
  está errado: o limite é uma escolha, não uma medida do ficheiro. Passam para «Confirma tu» todos
  os que falham por um segundo ou menos.

**E o contador do cabeçalho passou a contar também os textos de dentro de um grupo**, pela mesma
condição do validador, porque senão dizia menos do que parecia dizer.

**Mais 9 fotografias**, largadas por ele depois das 19:30 do mesmo dia: 701 no inventário, todas
prontas, 44 folhas de prévias. Mesa publicada na versão 35.

**Quem:** o Tiago pediu; Claude construiu com agentes, um verificador adversarial apanhou os dois
defeitos e Claude corrigiu-os à mão.

---
### 2026-09-23 | 084 | O som da abertura ao nível da música, e o letreiro fica com uma regra escrita

**O que ele decidiu:** *"Iguala o som. Fica o A. Largura da tela ainda não sei. O fim ainda não
decidi. Os vídeos vou decidindo à medida que vou fazendo."*

**O som da abertura.** Os dois vídeos passam a ter o som ao nível da música do filme.

| | Antes | Ganho | Depois |
|---|---|---|---|
| Fanfarra da Fox | -30,38 LUFS | +8,48 dB | -21,96 LUFS, true peak -6,61 dBTP |
| Intro da Marvel | -49,54 LUFS | +27,64 dB | -22,16 LUFS, true peak -2,57 dBTP |
| A música do filme, para comparar | | | -21,9 LUFS |

**O argumento que fechou a questão não foi técnico.** Na cópia da fanfarra que a mãe da Clara
usou, a mesma peça está a -9,3 LUFS, treze decibéis **acima** da música. O silêncio de hoje nunca
foi escolha de ninguém: é um acidente do ficheiro HD que o Tiago largou na pasta. E sendo
projeção com as colunas do DJ (decisão 082), quem está na mesa de som põe um volume para o filme
inteiro e o desnível de 27,6 dB não se corrige na sala.

**Ganho direto e não `loudnorm`.** O loudnorm comprime quando o alcance é maior do que o alvo:
medido, levava a intro de LRA 18,2 para 12,5, e esse alcance é a subida do quase-silêncio até às
letras, que é precisamente o que ele mandou refazer três vezes. O ganho move o nível e deixa a
forma quieta. Nenhum dos dois clipa, e o chão de ruído da intro fica a cerca de -68 dBFS, 46 dB
debaixo da música. A imagem não se tocou, `-c:v copy`.

Os ficheiros saem do `scripts/igualar_abertura.py` para `gerados/som_igualado/`, com o sufixo
`igualado`. **Os originais ficam intactos**, e a `render.VIDEOS` conhece agora os quatro nomes.
Aproveitou-se para corrigir o caminho da Fox nessa tabela, que apontava para uma pasta onde o
ficheiro não está: o render safava-se sempre pela busca de recurso, e no dia em que aparecesse um
ficheiro com esse nome na pasta errada apanhava o errado sem uma queixa.

**O letreiro: o sistema A.** A conclusão do levantamento é que não havia incoerência para
corrigir, havia uma regra por escrever, e agora está escrita: **uma letra de marca e uma letra de
leitura**. O Impact fica onde já está, quatro palavras a 288 px, uma vez só; tudo o que é para ler
fica em Arial Bold. A medição explica porquê: o Arial Bold separa as letras a partir do corpo 58 e
o Impact só a partir do 106, ou seja o Impact precisa de quase o dobro do tamanho para se ler
igual a 15 metros. Acima de 132 px é excelente, e é onde ele está.

**Não se mexe na intro**, e a razão é uma contagem: o efeito dela é a fotografia aparecer por
dentro das letras, e isso precisa de área de letra. A máscara do letreiro em Impact tem 250.835
pixéis; em Arial Bold teria 105.607, menos 58 por cento da janela por onde a fotografia se vê.

**A única mudança do sistema A** são os meses da fita de 1995, em `scripts/linha_tempo.py`: eram
Arial fina, 32 px, minúsculas, na cor (128,114,122), que é exatamente a letra, o tamanho e a cor
que o projeto já tinha declarado ilegível para a régua do contador que passa segundos antes. Duas
grafias do mesmo mês em duas peças vizinhas. Passam a Arial Bold 38 em maiúsculas, na
`REGUA_TEXTO`. Os 38 e não os 46 da régua por causa da folga por baixo, medida com a Pillow: a 38
a faixa dos meses acaba 2 px dentro da faixa da data do marco, contra 3 px como estava antes e 5,5
px a 46. Lê-se melhor e encosta menos.

**E a assinatura do corpo sintético foi refeita, que é um ato deliberado.** Mudar o desenho muda
os pixéis, e o `teste_fatias_desenham_os_mesmos_fotogramas` guarda uma assinatura congelada de 560
fotogramas. Antes de a refazer mediu-se, como das duas vezes anteriores: o `scripts/prova_meses.py`
reconstrói o `linha_tempo` de antes e troca o módulo dentro do render. O render de agora com o
desenho de antes dá a assinatura antiga, `911939f3`, com o de agora dá `49cc671c`, e dos 560
fotogramas mudam 47, do 53 ao 99, todos com o clip da fita no ecrã. Os outros 513 ficam byte a byte
iguais. Só depois disso é que a constante foi trocada.

**O que fica à espera dele:** a largura da tela, que é a pergunta ao DJ ou à quinta e que manda
mais na legibilidade do que qualquer letra; o fim do filme, que ele faz na Mesa; e os seis vídeos,
que decide à medida que trabalha.

**Quem:** o Tiago decidiu as duas; Claude mediu, construiu e mostrou as alternativas.

---
### 2026-09-23 | 085 | O sorriso dele, e a armadilha de numerar referências pela posição na pasta

**O que o Tiago escolheu para ela:** o **v32 A**, o sorriso aberto. Comparados os três ao tamanho
real, é o único em que os olhos, as maçãs do rosto e a boca contam a mesma história, e os dentes
assentam na luz de fim de tarde da foto; no B o branco dos dentes é mais forte do que a luz justifica.
A cara dela fica fechada a partir daqui: tudo o que se fez a seguir devolve só o retângulo dele
`(455, 320, 730, 650)` à v32 A, e confirma-se a cada gravação que fora desse retângulo há **zero**
pixéis diferentes.

**Depois pediu sorriso para ele, e a seguir que fosse mais pronunciado.** O modelo de imagem só tem
dois registos: pedindo lábios fechados devolve uma cara quase séria, pedindo sorriso devolve um riso
largo com dentes, e o negativo "no teeth" não o segura (sementes 21, 22, 23 contra 31, 32, 33, e
depois 21 e 23 com pedidos mais fortes, todas em `gerados/sem_mascara/_sd_ele_s*_f90*.png`). O meio
termo não se consegue por palavras.

**O que deu o meio termo foi misturar, não pedir.** Duas bases da **mesma semente** ficam alinhadas
pixel a pixel, porque a semente fixa o formato da cara e a barba; misturando a contida com a larga a
35, 50 e 65 por cento obtém-se uma escada de intensidade, e a rede de identidade, que reescreve a
cara inteira por cima, resolve a mistura numa boca coerente em vez de a deixar esborratada. É o
`v34 esboco mais` (mistura a 50).

**O caminho das fotos verdadeiras falhou com as referências antigas e resultou com as novas.** Pela
foto 2 (de dentro de casa, barba mais curta) a pele saía mais clara do que o pescoço e a barba mais
rala do que a do próprio dia, e montada sobre o original ainda vinha halo azul, porque a máscara azul
toca o limite da zona; montar sobre a própria v32 A tira o azul, mas não a barba. Com as fotos de
andebol que o Tiago deixou a 23 de setembro às 09:01, a `649886673` tem um sorriso verdadeiro dele,
de frente, com a cara a 151 px, e dá o `v35 sorriso dele`, com semelhança 0,94, a mesma da séria.
Nestas fontes o acerto de cor pela testa estraga tudo (testa ao sol, boca à sombra): `--cor-por
nenhum` e deixar o Poisson tratar do tom.

**A armadilha, e é a lição a guardar:** os scripts numeram as referências por `sorted(os.listdir())`,
ou seja pela **posição** na pasta. A 22 de setembro às 20:18 apareceu na pasta das referências uma
pasta chamada `FRAMEFOTO`, que ordena antes das `WhatsApp` e ficou na posição 13; tudo a partir daí
andou uma casa e a **referência 14 passou a ser a própria foto com as máscaras**. Resultado: a
identidade média de ontem à noite e de hoje de manhã incluía uma cara tapada por uma máscara
cirúrgica. Mediu-se: a semelhança dele caiu de 0,94 (v31, v32) para 0,91 (v33). A 23 às 09:01
entraram mais sete fotos e a numeração andou outra vez. **As referências passam a ser presas ao nome
do ficheiro**, nunca à posição (`refs_fixas.py`, com a ordem original das 15). Como controlo, as
fotos verdadeiras dele medem 0,87 entre si e as dela 0,78, portanto 0,94 é bom e 0,91 é perda real.
O `v33` fica no disco, mas está ultrapassado pelo `v34`.

**Por decidir:** qual fica, o `v34 esboco mais` ou o `v35 sorriso dele`. E continuam em aberto os
ajustes antigos: grão e nitidez da zona nova iguais ao resto da foto, e o nariz dele com mais volume.

**Quem:** o Tiago escolheu o sorriso dela, pediu o dele e forneceu as fotos de andebol; Claude fez a
escada, encontrou a troca das referências e mediu.

---

## Em aberto

Não assumir nenhuma destas sem decisão explícita do Tiago.

### I. Os trechos do áudio do pedido (DECIDIDO a 17/09, decisão 075)

O Tiago acrescentou em 12/09/2026 um vídeo do pedido, 760 MB, em
`trabalho/03-NOVOS_VIDEOS/`. Não quer a imagem, só o áudio a partir dos 3:12.

Estão cortados em catorze pedaços em
`C:\casamento-video-media\gerados\pedido_pedacos\`, com um `LEIA-ME.md` que
diz a que instante do vídeo corresponde cada um.

**Decisão adiada por ele:** *"Afinal não vou decidir já onde vou meter estes
trechos do pedido. Vou deixar ficar para já, pois há um ou outro bom material
que posso incluir no fim do vídeo ou agora."*

Ação pendente: ele ouve e diz quais entram, e se entram no princípio, junto às
fotografias do pedido, ou no fecho do filme.

### G. Recuperar o ficheiro de som em falta

`Paris Filmes Reversed.MP3` é referido no `.wlmp` mas não existe em disco. Pertence à
assinatura protegida pela decisão 001: é a fanfarra ao contrário que abre a secção do
Tiago, a espelhar a da 20th Century Fox que abre o vídeo. (O `aleluia.mp3` saiu desta
lista a 16 de setembro, decisão 072: o aleluia está dentro do troço dos foguetes.)

Ação pendente: pedir o ficheiro à mãe da Clara. Se não aparecer, decidir se se
reconstrói o efeito com outra fanfarra invertida ou se se abandona o espelho.

### J. As 29 sobras na pasta FINAIS

Ficheiros escritos por corridas antigas, com o nome em `.jpg` onde hoje se
escreve `.jpeg`, alguns com 2208 pixéis de largura por causa da regra antiga.
Não apago nada dentro de `C:\casamento-video-media\`, regra 3. Enquanto lá
estiverem, qualquer coisa que procure por nome em vez de pelo índice apanha o
ficheiro errado.

Ação pendente: o Tiago diz se os apago ou se ficam.

### M. As 40 imagens da página de Instagram da quinta

Estão em `01-NOVAS/Quinta/Instagram_files`. Não são fotos do casal: há casamentos
de outros noivos, com pessoas que não conhecemos, mesas decoradas, vistas aéreas da
quinta, logótipos e capturas de ecrã. As fotografias com outros noivos não devem
entrar no vídeo. As vistas da quinta e as mesas vazias podiam servir para o fecho,
por exemplo com a data e o sítio do casamento.

Ação pendente: o Tiago diz se alguma entra e para quê.

### H. Suporte de exibição (FECHADO a 22/09, decisão 082)

É **projeção**, com o som pelas colunas do DJ. O trabalho de recorte que se
podia poupar numa televisão não se poupa: a decisão 003 continua a valer, agora
por se saber e não por precaução.
