# CLAUDE.md

Regras operacionais deste repositório. Condensado de `docs/BRIEFING.md`, que
continua a ser a fonte completa de contexto.

**No início de cada sessão, lê `docs/BRIEFING.md` e `DECISOES.md` por inteiro.**
Este ficheiro é o resumo executivo, não substitui o briefing.

---

## O projeto em três linhas

Vídeo do casamento de Clara e Tiago, 4 de outubro de 2026, Quinta Pedras
Salgadas, Vila Nova de Gaia, cerca de 140 convidados. A mãe da Clara fez um
vídeo de 23,5 minutos em Windows Movie Maker. Esse trabalho é a base e é para
ser respeitado, não substituído. Reordenar, aparar e dar-lhe a voz do casal.

**Em caso de dúvida entre inventar e preservar, preserva e pergunta.**

---

## Fazer no início de cada sessão

1. Ler `docs/BRIEFING.md` e `DECISOES.md`.
2. **Verificar `C:\casamento-video-media\trabalho\01-NOVAS\`** e comparar com o
   que já está registado em `data/inventario.csv`. Analisar e acrescentar
   qualquer imagem nova, e **dizer sempre ao Tiago quantas foram encontradas**,
   mesmo que sejam zero.

3. **Ler o documento `montagem/pedido` da base de dados da Mesa** (`read_db`). Se
   o botão "Pedir atualização" deixou lá um pedido mais recente do que o último
   `montagem/publicacao`, a atualização das fotos é a primeira coisa a fazer, e
   diz-se isso ao Tiago.

**Atualizar as fotos é um comando só:** `py -3.11 scripts/atualizar_fotos.py`.
Regista, melhora, escolhe a versão, refaz as miniaturas, tira o retrato do estado
e monta `saida/mesa.html`. Depois, com a ferramenta Artifact, publica-se a Mesa e
escreve-se `montagem/publicacao` com `{build, quando, fotos}`, copiando o `build`
do `data/estado_fotos.json`: é isso que faz aparecer a barra "Há uma versão mais
nova" nas Mesas que estejam abertas. Nunca publicar a Mesa sem refazer o retrato,
senão o botão mostra um estado antigo.

**Escrever na Mesa pede sempre a versão.** Um documento que já existe na base da Mesa
(`montagem/estado`, `montagem/publicacao`) só aceita escrita com `if_version`, a versão
lida por último. Até 14 de setembro à tarde a ferramenta não deixava passar esse valor e
todas as escritas eram recusadas; à noite já deixava, e a escrita presa à versão 1116
entrou. Ler primeiro, escrever com a versão lida, e se vier `version_mismatch` é porque
ele gravou entretanto: ler outra vez e refazer, nunca forçar. Escrever pôr o `quando`
na hora da escrita, e dizer-lhe para recarregar a Mesa.

**O documento da Mesa é `montagem/estado2`, desde 15 de setembro.** Nesse dia páginas
antigas da Mesa, abertas ou em cache num browser, apagaram a montagem três vezes: duas
com uma cópia velha e uma com a demo de arranque, porque não tinham conseguido ler a
base. A Mesa passou a ler e gravar em `montagem/estado2`, a nunca gravar antes de ler a
base, e a trazer o documento antigo uma só vez se o novo não existir. O antigo,
`montagem/estado`, já ninguém lê: é onde as páginas antigas continuam a escrever. Ler e
escrever sempre o `estado2`.

**Nunca gravar na base ao mesmo tempo que se publica a Mesa.** A 15 de setembro, às
12:25, uma Mesa aberta logo a seguir a uma publicação feita em paralelo com a gravação do
`estado2` gravou a demo por cima. Publicar primeiro, ler a base depois, e só então gravar
se for preciso. Depois de cada publicação, ler `montagem/estado2` e confirmar que a
montagem continua lá.

**E pôr `rev` = a revisão lida + 1.** A base aceita qualquer gravação da página (o último
ganha), e a 15 de setembro uma Mesa com uma cópia antiga gravou duas vezes por cima da
versão reposta, porque a guarda era por data. A Mesa passou a guardar por número de
revisão: só grava se a base estiver na revisão em que se apoia. O `juntar_mesa.py` já
sobe a revisão; quem escrever o estado à mão tem de fazer o mesmo.

**Antes de cada render da v3, confirma-se a junção.** Até à escrita de 14 de setembro à
noite, a Mesa dele não tinha os dois vídeos de abertura, as três partes da fita de 1995
nem a Clair nos penteados; sem a fita, o Lang Lang, os foguetes do Tiago e o Rei Leão
saem mudos. Depois de ler `montagem/estado` para `saida/leitura_mesaN`, correr
`py -3.11 scripts/juntar_mesa.py saida/leitura_mesaN/montagem/estado.json` e só depois
o `montar_da_mesa.py`. Parte sempre da versão dele, não duplica o que ele já tiver, e
se estiver tudo diz "nada".

**As prévias grandes vão em folhas, nunca uma por foto.** O link da Mesa aceita no
máximo 256 ficheiros ao todo, contando a página, e 255 entradas por publicação. Com
641 fotos, um ficheiro por foto foi recusado. O `gerar_previas.py` faz folhas de 4 por
4 (`previas/folha_NN.jpg`) e o índice vai dentro da página. Publicam-se com `files` e
`root: saida`; as folhas com o mesmo nome substituem-se, e se houver menos folhas do
que antes as que sobram tiram-se com `null`.

A pasta `01-NOVAS` é onde o Tiago larga fotos que não estavam no vídeo
original. Não estão organizadas nem renomeadas, e pode haver subpastas. Uma
foto que já lá esteve nunca se apaga: se não for usada, fica registada como
não usada.

---

## Nunca fazer

1. Commitar media. Fotos, vídeos, música, o MP4 de 896 MB. Nunca.
2. Alterar `data/original_mae.csv` depois de criado e commitado.
3. Apagar ou mover ficheiros em `C:\casamento-video-media\`.
4. Tratar nomes parecidos como duplicados sem confirmar por hash do conteúdo,
   e mesmo com hash confirmado, apenas reportar, nunca agir.
5. Assumir uma decisão em aberto da secção 8 do briefing sem perguntar.
6. Avançar para a fase seguinte sem confirmação explícita do Tiago.
7. Escrever na pasta `00-Backup`. É a rede de segurança e fica intacta.

---

## Condições de exibição, que mandam em tudo

Passa durante o jantar, bloco único de cerca de 15 minutos (900 segundos),
com metade da sala de costas para o ecrã. **É projeção, e o som sai pelas
colunas do DJ**, confirmado pelo Tiago a 22 de setembro, decisão 082. Quem está
na mesa de som põe um volume para o filme inteiro: um desnível de decibéis
dentro do filme não se corrige na sala. Daí decorre:

- Planos fechados. Foto de grupo tirada de longe não se lê a 15 metros. Se uma
  foto importante estiver distante, corta e aproxima.
- Texto grande, poucas palavras, alto contraste, branco sobre escuro.
- Nenhuma narração falada. A acústica mata a palavra. A música carrega tudo.
- Fim inequívoco com fade a preto, para as pessoas saberem que podem aplaudir.

**Filtro de tom:** se um colega conservador repetisse aquilo ao café na segunda
feira, o Tiago sentir-se-ia desconfortável? Se sim, não entra. Aplica-o a todo
o texto que propuseres para o ecrã.

---

## As datas que podem ir ao ecrã

Confirmadas pelo Tiago, decisão 030. São as únicas duas datas de nascimento que
podem ser escritas.

| | |
|---|---|
| Tiago | 12 de setembro de 1995 |
| Clara | 24 de novembro de 1995 |

A Clara nasce **no mesmo dia** em que se salvaram as gravuras do Côa. Essa
coincidência é verdadeira e é o que faz a piada do dia 24 na v3 funcionar sem
ser escrita.

---

## Regras fixas de edição

- Máximo de 4 ou 5 fotos seguidas do mesmo evento ou viagem.
- Nunca menos de 3 segundos por foto. Padrão 4. Fecho de bloco até 6.
- Não forçar paridade entre Clara e Tiago. Ela tem muito material de infância,
  ele tem pouco. Intercalado apertado só onde há material comparável.
- Texto no ecrã: poucas palavras, datas e nomes, nunca frases.
- `resolucao_ok = Nao` em tudo o que precise de upscaling.
- Cada mudança de faixa musical coincide com mudança de bloco.

---

## Estrutura alvo, 900 segundos

| # | Bloco | Alvo (s) |
|---|-------|----------|
| 0 | Abertura, flash-forward | 45 |
| 1 | Primeiros anos, 0 aos 6 | 150 |
| 2 | Infância, 7 aos 12 | 160 |
| 3 | Adolescência, 13 aos 18 | 160 |
| 4 | O encontro, 2009 a 2012 | 130 |
| 5 | A dois, 2012 a 2026 | 220 |
| 6 | Fecho | 35 |

O bloco 4 é o momento estrutural: as duas linhas juntam-se, acaba a
alternância, muda a música.

Esta é a estrutura da versão `v2_funil`. Há três versões em construção, todas
com o mesmo alvo de 900 segundos. Ver `DECISOES.md`, entrada 002.

| Versão | Ideia |
|---|---|
| `v1_fiel` | A dela, com correções de lógica. Mantém secções, cartões e mecânica musical. Corrige o desequilíbrio, o excesso de fotos seguidas e o fim cortado. |
| `v2_funil` | A tabela acima. Intercalado por idades, charneira no encontro. |
| `v3_flashback` | Abre no presente, salta ao nascimento, segue cronológico. Depende de datas fiáveis, logo o EXIF no inventário é crítico. |

---

## Marcas de assinatura, transversais a todas as versões

Decisão 001. As três versões herdam a assinatura da mãe da Clara. Não é
decoração, é um sistema que ela construiu de propósito:

- Fanfarra de estúdio a abrir o vídeo (20th Century Fox, 20,4 s)
- Fanfarra ao contrário a abrir a segunda vida (Paris Filmes Reversed, 7,1 s)
- A mesma vinheta sonora por cima de cada cartão "Era uma vez": troço de
  `Candidato a vereador` a partir de 2:53, usado duas vezes, idêntico
- Canções que dizem o nome da pessoa por baixo do bloco dessa pessoa

Nenhuma versão pode apagar isto. Reordenar e aparar, sim. Apagar, não.

`Paris Filmes Reversed.MP3` não existe em disco e é preciso. O `aleluia.mp3` do `.wlmp`
também não existe, mas **não se procura**: o Tiago disse a 16 de setembro que o aleluia
está dentro do troço dos foguetes (`Candidato a vereador.mp3` a partir de 2:53), decisão 072.

---

## O letreiro, e o som dos vídeos de abertura

**Uma letra de marca e uma letra de leitura, decisão 084.** O Impact é a letra de marca: aparece
uma vez, no letreiro da intro, a 288 px. Tudo o que é para ler é Arial Bold. A regra não é de
gosto, é medida: o Arial Bold separa as letras a partir do corpo 58 e o Impact só a partir do 106,
ou seja precisa de quase o dobro do tamanho para se ler igual a 15 metros. Nada de Impact abaixo
de 132 px, e nada de trocar a letra do letreiro: o efeito da intro é a fotografia aparecer por
dentro das letras, e a máscara em Impact tem 250.835 pixéis contra 105.607 em Arial Bold.

**O som dos vídeos de abertura é igualado à música, decisão 084.** A demo_v3 usa as cópias
`... igualado.mp4` de `gerados/som_igualado/`, feitas pelo `scripts/igualar_abertura.py` com ganho
directo, nunca `loudnorm`: o loudnorm comprime e achata a subida da intro. Os originais ficam
intactos. Um vídeo de abertura novo passa pelo mesmo caminho antes de entrar na montagem.

**O nível da música do filme é -21,9 LUFS e não os -23 do loudnorm**, porque a opção `level` do
alimiter multiplica a saída por 1/0,94. É contra -21,9 que se compara qualquer coisa.

---

## Quanto ampliar cada foto

O alvo de ampliação depende de **como a foto vai aparecer**, não só do seu
tamanho. Regra única, tem de ser igual em `scripts/upscale.py` e em
`scripts/upscale_ia.py`:

| Proporção da foto | Como aparece | Alvo |
|---|---|---|
| menos de 1,55 (vertical ou quadrada) | Encaixada, com fundo desfocado | Só a altura conta: `1080 / altura` |
| 1,55 ou mais | Enche o ecrã | `max(1920 / largura, 1080 / altura)` |

Em ambos os casos multiplica-se por 1,15 de folga para o pan e zoom não ficar
a puxar pixéis do nada.

Isto não é um pormenor. A `82-11-1.jpg`, de 368x1067, precisava de 5,2x para
encher os 1920 de largura e precisa de 1,01x para ter os 1080 de altura.
Aplicar a regra certa reduziu o lote de upscaling por rede neuronal de 170
fotos para 109, e o lote urgente de 68 para 15.

**Quem escolhe a versão de cada foto é o `data/finais.csv`, mais ninguém.**

O `consolidar.py` escreve esse índice ao mesmo tempo que copia para a `FINAIS`:
uma linha por fotografia, com o id, o ficheiro final, de onde veio e quanto
mudou. O `render.py`, o `gerar_editor.py` e o `auditar_finais.py` leem de lá.

Nenhum deles pode voltar a decidir sozinho. Já houve três cópias da mesma regra
em três ficheiros e a que fazia o vídeo era a que estava por corrigir: o render
usava a versão da rede neuronal em 62 fotografias que já tinham pixéis que
chegavam. O `teste_render_usa_o_indice` falha se alguém repetir a escolha à mão.

A `FINAIS` também guarda ficheiros de corridas antigas, com outra extensão. Não
se apagam, regra 3. O `consolidar.py` lista-os no fim de cada corrida, e quem
procurar por nome em vez de pelo índice apanha o ficheiro errado.

**Duas pastas de saída, e nenhuma delas é o original:**

| Pasta | Técnica | Quando usar |
|---|---|---|
| `upscaled\` | Lanczos mais `cas`, rápido | Ampliações abaixo de 1,5x. É esta que a FINAIS usa, decisão 052 |
| `upscaled-ia\` | Real-ESRGAN `realesrgan-x4plus`, 88 s por foto em CPU | Acima de 1,5x |

Nunca usar `realesrgan-x4plus-anime` nem `realesr-animevideov3`: são para
desenho animado e em fotografias de pessoas dão pele de plástico. Nunca usar
restauro de rostos (GFPGAN, CodeFormer): esses não ampliam a cara,
redesenham-na, e inventam um rosto plausível que não é o da pessoa.

---

## Vocabulário de ritmo

O ritmo é propriedade do bloco, não da foto. Coluna `ritmo` nos ficheiros de
montagem:

| Valor | Duração | Uso |
|---|---|---|
| `retrato` | 5 a 6 s, zoom lento, crossfade 1 s | Fotos únicas e importantes |
| `normal` | 4 s, pan ou zoom alternado | Corrente geral |
| `rajada` | Entrada rápida, fotos acumulam no ecrã | Amigos, colegas, viagens, festas |
| `respiro` | 6 s com fade | Fecho de bloco |

A mecânica da `rajada` **está fechada** desde 10 de setembro, decisões 017, 019
e 021: 0,5625 s por foto, corte seco, e está implementada no `render.py` e na
Mesa. Esta linha dizia o contrário até 22 de setembro, e era só ela que ficou
por limpar.

---

## Arquitetura

Media em `C:\casamento-video-media\trabalho\`, em três pastas:

| Pasta | O que é |
|---|---|
| `00-Backup` | Cópia idêntica da original. Rede de segurança. Nunca escrever. |
| `00-ORIGINAL-MAE` | Material do vídeo dela. É aqui que se trabalha. Não apagar. |
| `01-NOVAS` | Fotos que o Tiago acrescenta. Verificar em cada sessão. |

No Git entram decisões, metadados, miniaturas e scripts. Nunca media. A razão
é operacional: o Tiago decide a partir do telemóvel, via GitHub. O PC só é
preciso na ingestão inicial e na exportação final.

```
casamento-video/
  CLAUDE.md              este ficheiro
  DECISOES.md            registo cronológico de decisões
  docs/BRIEFING.md       contexto completo
  scripts/               código Python
  data/
    original_mae.csv     timeline da mãe da Clara, INTOCÁVEL
    inventario.csv       metadados de todo o media
    decisoes.csv         fonte única de verdade da edição
  proxies/               miniaturas 400px, versionadas
  saida/                 FCPXML e renders, no gitignore
```

### Esquema de `data/decisoes.csv`

Não alterar nomes nem ordem de colunas.

```
id, ordem, bloco, ficheiro, tipo, pessoa, ano, evento, duracao_s,
in_s, out_s, movimento, texto_ecra, resolucao_ok, voto_tiago,
voto_clara, nota_tiago, nota_clara, estado
```

- `tipo`: foto ou video
- `pessoa`: Clara, Tiago, Ambos, Familia, Amigos
- `in_s`/`out_s`: só para vídeos. Vazio nas fotos.
- `duracao_s`: 4 por omissão nas fotos
- `movimento`: Nenhum, Zoom in, Zoom out, Pan E-D, Pan D-E
- `estado`: Fica se ambos votarem Fica, Corta se ambos votarem Corta,
  Discutir em qualquer outro caso, vazio se a linha estiver por preencher

---

## Ambiente

Windows. **Python 3.11 obrigatório, invocado como `py -3.11`.** O módulo de
scripting do DaVinci Resolve não funciona com 3.12 ou superior, porque ainda
importa `imp`.

DaVinci Resolve 21.1 versão gratuita. A gratuita bloqueia scripting externo,
mas `Workspace > Scripts` não está bloqueado e um script lançado daí recebe o
objeto `resolve`. Caminho principal: gerar FCPXML e importar por
`File > Import > Timeline`. Caminho alternativo: script pelo menu. Não é
preciso comprar a Studio.

FFmpeg 9.0.1 instalado por winget em
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-9.0.1-full_build\bin\`.
A entrada de PATH existe, mas sessões de terminal abertas antes da instalação
não a veem. Nesses casos usar o caminho completo.

Pillow 12.3.0 instalado no Python 3.11.

---

## Avisos técnicos sobre o material

- Extensões maiúsculas e minúsculas misturadas (`.JPG`, `.MP3`). Filtrar
  sempre sem distinguir maiúsculas.
- Nomes parecidos (`10-1.jpg` e `10-1 (2).jpg`) **não são necessariamente
  duplicados**. Fotos digitalizadas em lote recebem nomes sequenciais.
- Caminhos dentro do `.wlmp` são absolutos do PC da mãe da Clara
  (`C:\Users\Rosa Moreira\Desktop\Casamento-Selecionadas\`) e estão partidos.
  A correspondência faz-se por nome de ficheiro.
- O WeTransfer renomeou pelo menos um ficheiro, trocando ` - ` por espaços.
  A reconciliação por nome normalizado está em `scripts/parse_wlmp.py`.
- `photothumb.db` é cache do Windows, ignorar.

### A armadilha do EXIF nas fotos digitalizadas

**Nunca confiar na data EXIF sem olhar ao equipamento.** 87 das 306 imagens
são digitalizações feitas em `HP Scanjet djf21` e `HP ojj3600`, que são
scanners. A data EXIF dessas fotos é o dia em que a mãe da Clara as passou a
scanner, não o dia em que foram tiradas. Uma foto de bebé do Tiago aparece
datada de 2013 por esta razão.

O `scripts/inventario.py` deteta isto por duas vias, e a coluna `digitalizacao`
diz o resultado:

1. Marca e modelo do EXIF contra uma lista de scanners e multifunções.
2. Nome em padrão de lote de digitalização (`8-5.jpg`, `21-49-13.JPG`) sem
   câmara declarada.

### As páginas guardadas trazem fotografias verdadeiras

Uma pasta `<nome>_files` é o despejo de uma página guardada: interface, avatares
e emojis. Durante muito tempo o ramo inteiro era ignorado, e isso deitava fora
fotos que só existem ali. O corte é por tamanho, `LADO_MINIMO_EM_FILES = 600`,
porque a separação é limpa: o maior avatar tem 206 pixéis de lado, o menor
retrato tem 805.

### Conteúdo contínuo corta, conteúdo diferente encadeia

Dois clips seguidos da **mesma** linha do tempo, ou de qualquer coisa que
continue onde a anterior ficou, juntam-se com **corte seco**. Um encadeado entre
duas imagens quase iguais não suaviza nada, produz fantasmas: na v3 apareciam
dois "1995" sobrepostos a seguir ao SAPO.

### O JPEG progressivo que o modelo não lê

O `realesrgan-ncnn-vulkan` usa o descodificador `stb_image`, que **não lê JPEG
progressivo**. Duas fotos falharam com `decode image failed` e isso não é
defeito da foto nem do GPU: a Pillow abre-as sem se queixar. O
`scripts/upscale_ia.py` já reescreve em PNG e tenta outra vez, sozinho. Se
aparecer `decode image failed` noutro sítio, é este o motivo.

### A borda que pisca, e que não é jitter de posição

A composição de sub-pixel pede à Pillow que amostre a foto numa posição
fracionária. Na fila de fora essa posição cai ligeiramente **fora** da imagem, e
a Pillow não devolve ali uma mistura: devolve preto, e de repente. Num sprite
branco, deslocamento 0,50 dá 255 e deslocamento 0,625 dá 0.

Num zoom lento isso faz a coluna de fora acender e apagar, e lê-se como tremor.
Vê-se nas bordas **verticais** porque numa foto 4:3 dentro de 16:9 são as que
ficam dentro do quadro.

**A regra:** qualquer sprite que entre numa composição de sub-pixel tem de vir
de `com_margem()`, com dois pixéis de margem. Preta quando o fundo é preto,
repetição da fila de fora quando o fundo é a própria foto desfocada, alfa zero
em RGBA. Existe em `scripts/render.py` e em `scripts/teste_estilos.py`.

### A Mesa de Montagem, e como se volta a publicar

A Mesa vive em três pedaços e só existe montada:

| | |
|---|---|
| `scripts/editor_base.html` | a página, o estilo e o comportamento |
| `data/editor_dados.js` | as fotografias, em folhas de miniaturas |
| `data/editor_montagens.js` | as montagens que os scripts já geraram |

```
py -3.11 scripts/inventario.py            se houver fotos novas
py -3.11 scripts/gerar_editor.py          folhas de miniaturas
py -3.11 scripts/gerar_montagens_editor.py
py -3.11 scripts/gerar_mesa.py            cola tudo em saida/mesa.html
```

Publicar é `Artifact` com `saida/mesa.html` e o URL do artefacto existente.

**A Mesa leva o som do render.** O `gerar_mesa.py` põe na página o que o
`scripts/som_para_mesa.py` lê de `data/montagens/v3.csv` e `v3.som.csv`: as faixas que o
script põe sozinho, as durações que o render muda e o instante de cada clip. Por isso a
ordem é sempre juntar, montar, e só depois `gerar_mesa.py`. Uma nota nova no
`montar_da_mesa.py` precisa de explicação em português em `EXPLICACOES`, senão o Tiago lê
a nota técnica.

**A Mesa avisa, nunca corrige (decisão 083).** O botão `Validar` corre as verificações na
montagem aberta e mostra «Está mal» e «Confirma tu»; a etiqueta `⚠ texto` marca o clip cujo
texto não cabe no tempo em que está sozinho no ecrã; o botão `Vídeos por decidir` mostra os
vídeos da `01-NOVAS` que não estão no filme, sem nenhuma maneira de os lá pôr, porque isso
passa por ele no chat. Nenhuma destas peças muda nada sozinha, e não se lhes acrescenta um
botão de corrigir.

**O tempo de um texto é o sozinho no ecrã, e a duração é a do render.** Sozinho é a duração
menos o encadeado com que o clip entra e o do clip que entra a seguir, que é o par de
`render.encadeados_do_corpo()` e **não** a coluna `solo_s` dos CSV, que é outra conta e difere
em 51 dos 1147 clips. E a duração é a `duracaoNoRender()`, o maior entre o que ele escreveu e o
que vem em `window.SOM_RENDER`: o `montar_da_mesa.py` estica sozinho o cartão de um nascimento
para os foguetes acabarem antes das fotos, e sem isso a Mesa marcava a vermelho um cartão que
está bem.

**Os textos dos grupos (decisões 070 e 071).** Um clip de lado a lado, colagem ou pilha
leva `xf` (um texto por foto, na ordem de entrada), `vf` (true = ligados), `vm`
(`"legenda"` = na legenda de baixo a mudar com cada foto; ausente = dentro de cada foto),
`tt` (tamanho da letra, omissão 46) e `vt` (`"fica"` = na pilha o texto das de baixo fica
à vista; ausente = desaparece). O `montar_da_mesa.py` escreve `textos_fotos` (JSON da
lista) e `textos_opcoes` (JSON só com o que difere da omissão) no fim do CSV; o render
lê-as em `ler_textos_fotos()` e `ler_textos_opcoes()`. **Sem textos, nenhum pixel muda**:
`teste_grupos_sem_texto_iguais_a_antes` compara assinaturas md5 tiradas do render de antes
dos textos (Pillow 12.3.0) e falha se alguém tocar no desenho dos grupos sem querer.

**Um vídeo pode estar no meio do filme (decisão 077).** A fanfarra é só o **bloco
inicial**, os vídeos que estão antes de qualquer outro clip; a conta é
`render.partir_em_fanfarra_e_corpo()` e o `montar_da_mesa.py` e o `som_para_mesa.py`
leem-na de lá, nunca uma parecida. Um vídeo em qualquer outro sítio é desenhado dentro do
corpo, a partir de uma cache de fotogramas em `saida/_cache/_quadros_<montagem>_<ordem>/`
que o processo principal enche antes das fatias e apaga no fim (`--guardar-quadros`
deixa-a, `--quadros-grandes` aceita mais de 30 s de vídeo no corpo). O clip leva `f`,
`vin` (segundo de entrada) e `d` (duração do troço; 0 = o ficheiro inteiro a partir do
`vin`), e quem mede o ficheiro é o `ffprobe`, nunca um número escrito à mão. No CSV da
montagem isso sai em `in_s` e `out_s`; no `som.csv` há `voz`, `abafar` e `video`. **Estas
colunas só aparecem quando há o que escrever nelas**, senão os dois ficheiros deixavam de
sair iguais ao byte aos do último render, que é o que o
`teste_v3_sem_vozes_igual_ao_byte` guarda contra `data/montagens/referencia/`. Congelar
essa referência é um acto deliberado: `py -3.11 scripts/testes.py --congelar-referencia`.

**O som de um vídeo do corpo, e a música por baixo.** O montar escreve uma faixa que
aponta para o próprio ficheiro, com o `in_s` do troço e a nota «som do vídeo». Não é leito:
não leva loudnorm nem cruzamento, e uma música marcada no clip seguinte não a corta. A
música que estiver a tocar baixa 12 dB por baixo dela, ou pára, pelo campo `vzm` do clip
(`"parada"`, ou ausente = mais baixa), que é o mesmo mecanismo das vozes do pedido (`vz`).
**A janela desse abaixamento conta com `render.CRUZAMENTO`**, os 2,2 s em que a faixa que
sai continua a tocar por cima da que entra: sem isso um leito que acabasse pouco antes era
esticado para dentro da voz e tocava por cima sem baixar nada.

**O contador por datas.** `04/10/2026>25/12/2025|4 de outubro de 2026;25/12/2025=o pedido`
anda dia a dia, com a régua dos meses por baixo; acima de três anos o `preparar` troca
sozinho para o contador de anos e diz que trocou. Cada contador que recua leva o
`rebobinar.wav` por cima. **Dois contadores encostados entram com corte seco**, pela regra
do conteúdo diferente: encadeá-los punha os dois números sobrepostos.

**Uma música marcada pára nos foguetes de um nascimento (decisão 079)**, como o Lang Lang
automático: os foguetes não são leito e não cortavam nada, e o Lang Lang retomado no cartão do
conceito tocava por baixo deles inteiros. A intro da Marvel sai do `scripts/intro_flipbook.py` para
`gerados/intro_marvel/` com nome novo a cada versão (o script recusa escrever por cima); a
`saida/intro_clara_tiago.mp4` de 12 de setembro é a única cópia do som e só se lê.

**A base devolve `data()` como função, e a Mesa só o soube a 16 de setembro (decisão 074).**
Até aí lia `s.data` como campo, `undefined`, e nunca leu a montagem guardada: as Mesas
antigas gravavam por cima a cópia do aparelho e as novas não gravavam nada. Qualquer código
novo que leia a base passa por `dadosDe(s)`. O harness `scratchpad/guardar/harness_mesa.py`
imita o contrato verdadeiro (`data()` função, corpo congelado, rejeições `{code, message}`);
o harness antigo, com o campo, não serve para provar nada sobre a base. Depois de cada
publicação, ler `montagem/estado2` e confirmar que a revisão não desceu.

**O estado dele não está no HTML.** Está na base de dados do artefacto, em
`montagem/estado`, e uma cópia fica em `data/mesa_estado.json`. Republicar a
página não lhe apaga o trabalho. Mas se eu editar o JSON e o escrever de volta,
**tenho de pôr o `quando` na hora a que o fiz**: o editor resolve conflitos por
esse campo, e uma cópia remota mais antiga do que a do browser dele perde, em
silêncio.

### A duração de um vídeo mede-se, não se escreve

O som é colocado pelo relógio do corpo, e o corpo começa onde os vídeos acabam.
Um número errado na Mesa arrasta a banda sonora inteira sem uma queixa. O
`montar_da_mesa.py` mede com o `ffprobe` e avisa quando difere do que lá está.

### Cada render é uma versão

O `render.py` escreve `C:\casamento-video-media\saida\<montagem>_AAAA-MM-DD_HHMM.mp4`
e a cópia leve `..._leve.mp4` ao lado, e regista cada render em `data/renders.csv`.
Nunca voltar a dar ao render um nome fixo: foi assim que se perdeu a v3 de 12 de
setembro. Para mandar ao Tiago, a `_telemovel` do render mais recente, que cabe no
limite de 30 MB do envio; se não existir, a `_leve`.

**O render desenha em fatias, com um só encoder (decisão 073).** Por omissão 7 processos
desenham os fotogramas alternados (`q % 7`) e o processo principal entrega-os por ordem ao
único ffmpeg, o de sempre: o MP4 sai igual ao byte ao de um render sequencial, provado em
nove renders do filme real. `--fatias 1` é o caminho sequencial de antes; `--fatias auto`
deixa um núcleo livre. Neste i5 de 4 núcleos físicos o ganho nos fotogramas é 2x (0,15 s
para 0,075 s por fotograma), não 7x: cada fatia prepara todos os clips e os núcleos lógicos
partilham os físicos. Uma fatia que morre pára tudo com erro e apaga o `_corpo.mp4`.

**O `--ate` não leva os vídeos de abertura.** O `render.py` tem `if fanfarra and not ate`,
portanto um render parcial dá o corpo e mais nada. A 22 de setembro mandei ao Tiago duas
"aberturas" para ele comparar o som e eram iguais ao byte, porque a única diferença estava nos
vídeos que não lá estavam. Para lhe mostrar a abertura, colam-se os vídeos à frente do corpo com
os mesmos comandos do render, `scripts/colar_abertura.py`, ou faz-se o render inteiro.
E para lhe mostrar o **fim** do filme sem esperar meia hora, recorta-se um troço da montagem com
o `scripts/troco_da_montagem.py`: o corpo tira o seu zero do `inicio_s` do primeiro clip que
sobra, mas o relógio do `som.csv` não, e por isso o som tem de andar para trás na mesma medida.

**Antes de cada render, perguntar ao Tiago pelos textos marcados.** Decisão 082: os textos que
passam depressa de mais não se corrigem sozinhos. A Mesa marca-os, ele edita, e antes de cada
render pergunta-se-lhe se ficam como estão. Não se corrige texto dele sem ele dizer.

### A marca da fita que falha sem se queixar

`imagem_da_marca()` devolve `None` quando não encontra o ficheiro, de propósito:
uma imagem em falta não pode parar um render de quinze minutos a meio. O preço é
que uma marca mal escrita sai **só com palavras e sem aviso nenhum**. Aconteceu
com três das quatro imagens de 1995, porque o Tiago as largou com o nome que
elas trazem da internet e a fita pedia outro.

**A regra:** o nome na marca é o nome que está em disco, com espaços, vírgulas e
parênteses. Nunca renomear nada dentro de `C:\casamento-video-media\`. Quem
apanha o erro é o `teste_marcas_com_imagem_encontram_o_ficheiro`.

### Som: a âncora só funciona na v1a

A música da mãe da Clara é colocada por **âncora à foto**, não pelo relógio.
Isso só funciona numa montagem que mantenha a ordem dela. Qualquer outra
montagem tem de trazer `data/montagens/<nome>.som.csv`, senão sai **muda e sem
aviso**. Já aconteceu nas quatro demos.

### Nunca recortar ficheiros entre dois marcadores sem os verificar

Apaguei metade do `scripts/editor_base.html` por usar como início de recorte um
comentário que existia **duas vezes**, no CSS e no JavaScript. Antes de qualquer
recorte entre marcadores, confirmar que cada um aparece **uma só vez**.

A versão publicada de um artefacto serve de cópia de segurança: recupera-se com
`Artifact action:"read"`.

### As dimensões no .wlmp não são as reais

O Movie Maker guarda em `arWidth` e `arHeight` dimensões de apresentação, não
a resolução do ficheiro. Em 302 referências, 137 divergem da realidade. O
`10-5.JPG` aparece como 96x72 e tem 4320x3240. **Ler sempre o ficheiro.**

---

## Como comunicar com o Tiago

- Português europeu, sempre.
- **Sem travessões.**
- Raciocínio antes do resultado. Ele quer perceber o porquê antes da proposta.
- Direto. Se algo não vai funcionar, dizer.
- Não reabrir decisões fechadas. Se surgir informação nova que invalide uma
  decisão, dizê-lo explicitamente em vez de reavaliar em silêncio.
- Uma pergunta de cada vez, no fim, quando for mesmo precisa.

---

## Manutenção

Sempre que uma decisão for tomada, acrescentar linha a `DECISOES.md` com data,
decisão e razão. É isso que permite retomar o trabalho noutra sessão, noutro
dispositivo, sem perder o fio.
