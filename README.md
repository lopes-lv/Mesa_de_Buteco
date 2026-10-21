# Texas Hold'em, Pif Paf & Dominó — Solo vs Bots ou Multiplayer Local

Jogo de cartas e peças em Python + Pygame, com três modos jogáveis solo contra
bots ou em **multiplayer local** (mesma rede Wi-Fi/LAN). A estética é
**"Pixel Art Retrô CRT"** (paleta escura de arcade, cantos retos, bordas
grossas, fonte monoespaçada e scanlines), desenhada 100% via `pygame.draw`,
sem imagens externas (referência visual em `design/07_pixel_retro_crt/`).

Este documento reúne a visão geral do projeto (antes dividida entre README e
GDD), como rodar e a estrutura. As regras e as notas de atualização de cada
modo ficam no README da pasta do modo.

## Índice dos documentos

| Documento | Conteúdo |
|---|---|
| [`holdem/README.md`](holdem/README.md) | Regras, bots, carteira de fichas e notas de atualização do Texas Hold'em |
| [`pifpaf/README.md`](pifpaf/README.md) | Regras, bots, pesquisa e notas de atualização do Pif Paf |
| [`domino/README.md`](domino/README.md) | Regras, pontuação, mesa em cruz e notas de atualização do Dominó |
| [`tools/README.md`](tools/README.md) | O editor visual de layout |
| [`MULTIPLAYER_PLANO.md`](MULTIPLAYER_PLANO.md) | Arquitetura do multiplayer (host-autoritativo, protocolo, threads) |
| [`lista_tarefas.md`](lista_tarefas.md) | Estado do projeto, pendências e o que foi concluído |
| [`CLAUDE.md`](CLAUDE.md) | Guia técnico para quem (ou o que) mexe no código |

## Os modos

| Modo | Resumo | Jogadores | Economia |
|---|---|---|---|
| **Texas Hold'em** | No-Limit em formato de torneio, blinds crescentes, side pots, bots com perfis | 2 a 8 | Fichas; no solo, uma carteira persistente |
| **Pif Paf** | Compra e descarte com baralho duplo; bata formando trincas e sequências | 2 a 8 | Sem fichas: vence quem chegar a 3 vitórias de mão |
| **Dominó** | Duplo-seis, corrida de pontos até 250, mesa em cruz, sem monte | 3 a 4 | Pontos acumulados |

Os três compartilham a mesma estrutura (menu → escolha de modo → configuração →
mesa → fim de jogo), o mesmo estilo visual e o multiplayer local. Cada motor é
independente: um nunca importa o outro.

## Como executar (desenvolvimento)

```bash
pip install pygame
python main.py
```

A janela é redimensionável e todo o layout se adapta ao tamanho atual. Não há
suíte de testes: valide jogando o fluxo afetado.

## Estrutura do projeto

Os `.py` ficam em pacotes por módulo: um por motor de jogo (`holdem/`,
`pifpaf/`, `domino/`), um para a base compartilhada (`core/`) e um para as
telas de pré-jogo e lobby (`menus/`). `main.py` fica na raiz como ponto de
entrada.

```
poker_game/
├── main.py                        # Ponto de entrada, loop principal e state machine de telas
├── core/                          # Base compartilhada pelos 3 modos
│   ├── deck.py                    # Cartas e baralho
│   ├── settings.py                # Configurações de sessão (em memória)
│   ├── carteira.py                # Saldo de fichas do Hold'em solo (em disco)
│   ├── layout.py                  # Tamanhos de carta/peça, espaçamentos e botões das mesas
│   ├── ui_theme.py                # Biblioteca de desenho Pixel Art Retrô CRT (ativa)
│   ├── baralhos_skins.py          # As 8 skins de baralho extras
│   ├── ui_widgets.py              # Widgets pequenos (CampoTexto)
│   ├── ui_pixelart.py             # Estética pixel art antiga (não usada; mantida de referência)
│   └── chat_widget.py             # Aba de chat de texto (lobby e mesas multiplayer)
├── holdem/                        # Motor do Texas Hold'em (ver holdem/README.md)
├── pifpaf/                        # Motor do Pif Paf (ver pifpaf/README.md)
├── domino/                        # Motor do Dominó (ver domino/README.md)
├── menus/
│   ├── screens.py                 # Menu inicial, escolha de modo, configuração, ajustes
│   └── multiplayer_screens.py     # Criar/entrar em sala, lobby de espera
├── rede/                          # Multiplayer: protocolo, host, cliente, descoberta por código/UDP
├── config/
│   ├── layout_padrao.json         # Valores padrão de layout (versionado)
│   ├── presets_padrao/            # Presets que vêm com o jogo (compacto, grande)
│   ├── layout.json                # Seus ajustes (opcional, fora do git)
│   ├── presets/                   # Seus presets (opcional, fora do git)
│   └── carteira.json              # Seu saldo do Hold'em (criado ao jogar, fora do git)
├── tools/                         # Editor visual de layout (fora do .exe; ver tools/README.md)
└── design/                        # Guias técnicos e mockups HTML dos estilos visuais (fora do git)
```

## Sistemas compartilhados

### Bots
Cada modo tem a sua IA, sem dependência entre elas:
- **Hold'em:** perfil de risco fixo por partida (tight, equilibrado, agressivo,
  tricky), decidindo por força da mão, draws, pot odds, posição e blefe.
- **Pif Paf e Dominó:** uma heurística única cada.

A velocidade dos bots (lenta, normal, rápida) é escolhida nos Ajustes.

### Baralhos
Dez estilos de carta (Padrão, Dark e 8 skins), escolhidos por setas na tela de
Configuração ou no botão dos Ajustes. As skins vêm de `design/baralhos/` e
rodam em `core/baralhos_skins.py`, só com `pygame.draw`.

### Multiplayer local
Os três modos podem ser jogados com outras pessoas na mesma rede, sem servidor
externo nem internet: um jogador cria a sala e vira o **anfitrião** (roda o jogo
de verdade) e os outros entram digitando um código curto (3 letras + 1 número,
como `KTR4`) ou o `IP:porta` manual. Há chat de texto (aba no canto esquerdo, no
lobby e nas mesas). A arquitetura completa está em
[`MULTIPLAYER_PLANO.md`](MULTIPLAYER_PLANO.md).

> Na primeira vez que você criar uma sala, o Firewall do Windows deve mostrar
> um popup pedindo permissão de rede para o jogo ou o `.exe`. Isso é esperado
> (o host abre sockets TCP/UDP), não é o jogo travando.

### Layout e editor visual
Os tamanhos de carta e peça, espaçamentos e botões das mesas, as cores do tema,
a fonte, a borda e a sombra, as fichas iniciais e o tempo dos bots ficam em
`config/layout_padrao.json` (lidos por `core/layout.py`), não espalhados pelo
código. O jeito mais fácil de mudar é o **editor visual** (também no botão
"Editor de layout" dos Ajustes):

```bash
python tools/editor_visual.py
```

Salvar grava `config/layout.json` e um jogo aberto se atualiza sozinho em até 1
segundo (ou com **F5**). Guia completo, incluindo presets e a vista "mesa
completa" que acusa sobreposições, em [`tools/README.md`](tools/README.md).

Também dá para editar à mão: crie `config/layout.json` só com o que quer mudar,
por exemplo para aumentar a sua carta no Hold'em:

```json
{"holdem": {"carta_jogador": [120, 168]}}
```

Tamanhos são `[largura, altura]` em pixels, cores são `[r, g, b]` (0 a 255) e
tempos dos bots são em milissegundos. Cada item do arquivo padrão tem
`min`/`max` (fora da faixa é limitado) e um `rotulo`. Um `layout.json` ausente,
com erro de digitação ou com valor de formato errado não quebra o jogo: o item
afetado volta ao padrão.

## Interface

- **Fluxo de telas:** Menu principal → Escolha de modo → Configuração (número de
  bots, baralho, solo ou multiplayer) → Mesa → Fim de jogo. Há também Ajustes.
- **Estética:** moderna e polida, mantendo o charme da pixel art.
- **Janelas:** a geometria das mesas cabe em qualquer janela de 1024x768 a
  1920x1080; o detector do editor acusa zero problemas com os valores padrão.

## Compilando para .exe (Windows)

1. Instale as dependências numa máquina Windows (o PyInstaller não faz
   cross-compile):

```bash
pip install pygame pyinstaller
```

2. Na pasta do projeto, rode:

```bash
pyinstaller PixelPoker.spec
```

   O `PixelPoker.spec` equivale a
   `pyinstaller --onefile --windowed --name "PixelPoker" --add-data "config/layout_padrao.json;config" --add-data "config/presets_padrao/*.json;config/presets_padrao" main.py`:
   - `--onefile`: um único executável.
   - `--windowed`: sem console.
   - `--name "PixelPoker"`: nome do executável.
   - `--add-data`: embute os valores padrão de layout (sem eles o jogo não abre)
     e os presets. Se usar a linha de comando em vez do `.spec`, não esqueça
     essas opções.

3. O executável sai em `dist/PixelPoker.exe`. Para usar ajustes de layout com
   ele, coloque um `config/layout.json` na mesma pasta do `.exe`. A carteira
   (`config/carteira.json`) também é criada ao lado dele. O editor e o botão
   "Editor de layout" não vão no `.exe` (`tools/` fica de fora).

> Se um dia houver imagens ou sons externos, use também
> `--add-data "assets;assets"` para embutir a pasta de assets.

## Visão e planos futuros

Ideias de produto ainda **não implementadas** (o estado real das pendências
está em [`lista_tarefas.md`](lista_tarefas.md)):

- **Modo inédito original:** uma mecânica única, ainda a definir. Já existe um
  card "EM BREVE" reservado na tela de escolha de modo.
- **Bots com personalidade por partida:** hoje o perfil é fixo por partida só no
  Hold'em; a ideia original é que os bots de todos os modos recebam uma
  personalidade nova a cada partida, sem ficar presa ao nome do bot.
- **Ferramenta de criação de baralhos (modo editor):** uma seção para montar e
  salvar baralhos próprios de forma visual e guiada, como pacote de assets. A
  infraestrutura do editor de layout (valores em JSON, prévia com o código real
  do jogo, recarga sem reiniciar) pode servir de base.
- **Áudio e "jukebox":** o jogador escolheria o tipo de música que quer ouvir
  durante a partida.
- **Pif Paf:** a regra da "a louca" (bater fora da vez com o descarte alheio).

## Escopo técnico

- **Linguagem:** Python.
- **Biblioteca:** Pygame, com possibilidade de migrar no futuro se o projeto
  precisar.
- **Plataforma:** PC (Windows, com `.exe` por PyInstaller).
- **Dependência única:** `pygame`. Não há `requirements.txt`, suíte de testes
  nem linter.

---
*Este documento é vivo e deve ser atualizado conforme o jogo evolui.*
