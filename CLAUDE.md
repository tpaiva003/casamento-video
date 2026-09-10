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
com metade da sala de costas para o ecrã. Daí decorre:

- Planos fechados. Foto de grupo tirada de longe não se lê a 15 metros. Se uma
  foto importante estiver distante, corta e aproxima.
- Texto grande, poucas palavras, alto contraste, branco sobre escuro.
- Nenhuma narração falada. A acústica mata a palavra. A música carrega tudo.
- Fim inequívoco com fade a preto, para as pessoas saberem que podem aplaudir.

**Filtro de tom:** se um colega conservador repetisse aquilo ao café na segunda
feira, o Tiago sentir-se-ia desconfortável? Se sim, não entra. Aplica-o a todo
o texto que propuseres para o ecrã.

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

`Paris Filmes Reversed.MP3` e `aleluia.mp3` não existem em disco. São precisos.

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

**Duas pastas de saída, e nenhuma delas é o original:**

| Pasta | Técnica | Quando usar |
|---|---|---|
| `upscaled\` | Lanczos mais `cas`, rápido | Ampliações até cerca de 1,5x |
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

A mecânica da `rajada` está em aberto. Ver `DECISOES.md`, ponto D. Não a
implementar sem decisão.

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
