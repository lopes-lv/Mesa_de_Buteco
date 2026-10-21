# Texas Hold'em, Pif Paf & Dominó - Solo vs Bots ou Multiplayer Local

Jogo de cartas/peças em Python + Pygame, com três modos — **Texas Hold'em**,
**Pif Paf** (ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md)) e **Dominó** — jogáveis
solo contra bots ou em **multiplayer local** (mesma rede Wi-Fi/LAN, ver
[MULTIPLAYER_PLANO.md](MULTIPLAYER_PLANO.md)), com estética "Pixel Art Retrô
CRT" (ver `design/07_pixel_retro_crt/`) desenhada 100% via `pygame.draw`
(sem imagens externas).

## Estrutura do projeto

Os arquivos `.py` são organizados em pastas por módulo: um pacote por motor
de jogo (`holdem/`, `pifpaf/`, `domino/`), um para a base compartilhada
(`core/`) e um para as telas de pré-jogo/lobby (`menus/`). `main.py` fica na
raiz como ponto de entrada.

```
poker_game/
├── main.py                        # Ponto de entrada, loop principal e state machine
├── core/                           # Base compartilhada pelos 3 modos
│   ├── deck.py                     # Cartas e baralho
│   ├── settings.py                 # Configurações de sessão (em memória)
│   ├── layout.py                   # Tamanhos de carta/peça, espaçamentos e botões
│   │                                # das mesas (lê config/, ver "Ajustando o layout")
│   ├── ui_theme.py                 # Biblioteca de desenho Pixel Art Retrô CRT (ativa)
│   ├── ui_widgets.py               # Widgets pequenos reutilizáveis (CampoTexto)
│   ├── ui_pixelart.py              # Estética pixel art anterior (não usada mais;
│   │                                # mantida de referência para uma eventual
│   │                                # reintrodução como baralho alternativo, ver
│   │                                # GDD.md seção 3.2)
│   └── chat_widget.py              # Aba de chat de texto (lobby + mesas multiplayer)
├── holdem/                         # Motor do Texas Hold'em
│   ├── game_logic.py                # Player, BettingRound, Table, blinds, pote/side-pots
│   ├── hand_evaluator.py             # Avaliação de mãos (7 cartas -> melhor 5, ranking)
│   ├── bot_ai.py                     # IA dos bots (perfis, pot odds e blefe)
│   ├── table_screen.py               # Tela de Mesa (gameplay + histórico)
│   └── mesa_remota_screen.py          # Tela do cliente remoto
├── pifpaf/                         # Motor do Pif Paf
│   ├── pifpaf_logic.py              # Baralho duplo, coringa, trincas/sequências, turnos
│   ├── pifpaf_bot_ai.py              # IA dos bots (compra, descarte, batida)
│   ├── pifpaf_screen.py              # Tela de Mesa (monte, descarte, mão, histórico)
│   └── mesa_remota_pifpaf_screen.py   # Tela do cliente remoto
├── domino/                         # Motor do Dominó
│   ├── domino_logic.py              # Peça, DominoTable, pontuação (corrida aos 250), sem monte
│   ├── domino_bot_ai.py              # IA dos bots (prioriza jogada que pontua, depois carroça)
│   ├── domino_theme.py               # Desenho das peças de dominó (pips, verso)
│   ├── domino_screen.py              # Tela de Mesa (mesa, mão, histórico)
│   └── mesa_remota_domino_screen.py   # Tela do cliente remoto
├── menus/                          # Telas de pré-jogo/lobby, compartilhadas pelos 3 modos
│   ├── screens.py                   # Menu Inicial, Escolha de Modo e Configuração
│   └── multiplayer_screens.py        # Criar/Entrar em sala, Lobby de espera
├── rede/                           # Multiplayer local: protocolo, host (AnfitriaoSala),
│                                    # cliente (ClienteSala), descoberta por código/UDP
├── config/
│   ├── layout_padrao.json          # Valores padrão de layout (versionado)
│   ├── presets_padrao/             # Presets que vêm com o jogo (compacto, grande)
│   ├── layout.json                 # Seus ajustes (opcional, fora do git)
│   └── presets/                    # Seus presets (opcional, fora do git)
├── tools/                          # Ferramentas de desenvolvimento (fora do .exe)
│   ├── editor_visual.py            # Editor visual de layout (python tools/editor_visual.py)
│   ├── editor_widgets.py           # Campo numérico, botões -/+ com repetição
│   ├── editor_previas.py           # Prévias em tamanho real de cada item
│   └── editor_mesa.py              # Mesa completa: tela real do jogo + alertas
└── design/                         # Guias técnicos e mockups HTML dos estilos visuais
```

## Como executar (desenvolvimento)

```bash
pip install pygame
python main.py
```

A janela é redimensionável — todo o layout se adapta ao tamanho atual.

## Texas Hold'em - Regras implementadas

- Small Blind / Big Blind com **estrutura de blinds crescente** (estilo
  torneio), sobe a cada 5 mãos.
- Rodadas de apostas completas: pré-flop, flop, turn, river.
- Fold, Check, Call e Raise (com seletor de valor via slider).
- Side pots corretos para múltiplos all-ins com stacks diferentes.
- **Split pot exato** em caso de empate (mãos de força idêntica dividem
  o pote, com o resto do arredondamento distribuído a quem está mais
  perto do dealer).
- Eliminação de jogadores (stack chega a zero) — a partida termina
  quando resta 1 jogador (torneio).

### IA dos Bots (Hold'em)

Cada bot tem um perfil de risco estável, variando entre tight, equilibrado,
agressivo e tricky. A decisão combina força da mão, draws, pot odds, pressão
da aposta, posição na mesa e quantidade de oponentes ativos. Os bots podem
roubar um pote sem aposta, pagar apostas grandes quando o preço justifica e
blefar com frequência controlada, em vez de sempre foldar mãos fracas ou
copiar um check com outro check.

## Pif Paf - Regras implementadas

Ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md) para a pesquisa das regras
tradicionais e as decisões de design. Resumo:

- Baralho duplo (104 cartas, sem coringas impressos); cada jogador recebe
  9 cartas.
- **Vira/coringa**: uma carta é virada do monte no início da mão; a carta
  de valor seguinte é coringa e substitui qualquer carta em combinações.
- No turno: compra 1 carta (monte ou topo do descarte) e depois bate
  (zera a mão em trincas/sequências válidas) ou descarta 1 carta.
- Quem não bate paga em fichas os pontos das cartas soltas; quem bate
  embolsa o pote. Eliminação e fim de partida seguem o mesmo formato de
  torneio do Hold'em.
- Se uma mão passar de muitos turnos sem ninguém bater, ela empata
  automaticamente (ninguém paga) para a partida nunca travar.
- **Fora do escopo desta versão:** a regra da "a louca" (bater fora da
  vez usando o descarte de outro jogador).

### IA dos Bots (Pif Paf)

Heurística única (sem perfis por partida como no Hold'em): só compra do
descarte quando a carta realmente reduz os pontos soltos da mão (mesmo
critério usado para decidir o que descartar), bate sempre que possível e
nunca descarta o coringa.

## Dominó - Regras implementadas

Variante **corrida de pontos até 250**, livre-pra-todos (sem duplas), jogo
duplo-seis, **3 ou 4 jogadores** — ver
[NOTAS_ATUALIZACAO_DOMINO.md](NOTAS_ATUALIZACAO_DOMINO.md) para as notas
completas da reforma:

- Sem monte: com 4 jogadores usa-se o jogo completo (28 peças, 7 cada); com
  3, a peça 0/0 sai do jogo (27 peças, 9 cada) — a divisão sempre é exata.
- Quem não tem jogada clica no botão **Passar** (ação explícita).
- Toda mão abre obrigatoriamente com uma carroça: a peça 6/6 na primeira
  mão (e depois de todo travamento total); nas demais, quem bateu por
  último abre escolhendo qual carroça jogar entre as que tiver.
- Peças da mesa em cruz: se a carroça de abertura permitir (o "bucho"),
  o jogo também cresce pra cima/baixo, não só esquerda/direita.
- Pontua quem fecha as pontas da mesa num múltiplo de 5 (carroça na ponta
  conta em dobro); quem bate ganha a soma dos pontos que sobraram nos
  outros, arredondada pra baixo pro múltiplo de 5 (+30 se a última peça for
  carroça); quem joga antes de alguém passar ganha +10; quem tranca
  parcialmente o jogo (todos passam e a vez volta pra ele, que ainda
  consegue jogar) ganha +50; travamento total (ninguém mais consegue jogar)
  encerra a mão a favor de quem tem menos pontos na mão.
- Primeiro a acumular 250 pontos, checado só ao final de cada mão, vence a
  partida inteira.

### IA dos Bots (Dominó)

Heurística única: prioriza jogadas que pontuam (fecham as pontas num
múltiplo de 5), depois carroças (peças duplas) — só encaixam num número,
então ficam mais fáceis de prender na mão — e, entre as opções restantes, a
peça de maior pontuação (reduz o prejuízo se a mão travar antes do bot
conseguir bater).

## Multiplayer Local

Os três modos podem ser jogados com outras pessoas na mesma rede Wi-Fi/LAN
(sem servidor externo, sem internet): um jogador cria a sala e vira o
"anfitrião" (roda o jogo de verdade), os outros entram digitando um código
curto (3 letras + 1 número, ex. `KTR4`) ou o IP:porta manual como fallback.
Inclui chat de texto (aba no canto esquerdo da tela, no lobby e nas mesas).
Ver [MULTIPLAYER_PLANO.md](MULTIPLAYER_PLANO.md) para a arquitetura
completa (host-autoritativo, protocolo, threads).

> Na primeira vez que você criar uma sala, o Firewall do Windows deve
> mostrar um popup pedindo permissão de rede para o jogo/`.exe` — isso é
> esperado (o host abre sockets TCP/UDP), não é o jogo travando.

## Ajustando o layout (tamanho de cartas, peças, botões)

Os tamanhos de carta/peça, espaçamentos e botões das mesas dos 3 modos, as
cores do tema, o tamanho das fontes, a borda/sombra de botões e painéis, as
fichas iniciais e o tempo de jogada dos bots ficam em
`config/layout_padrao.json` (lidos por `core/layout.py`), não espalhados pelo
código. O jeito mais fácil de mudar é o editor visual (também abre pelo botão
"Editor de layout" na tela de Ajustes do jogo):

```bash
python tools/editor_visual.py
```

- À esquerda, as variáveis por aba (Hold'em, Pif Paf, Dominó, Geral, Cores).
  Cada uma tem `-`/`+` (Shift = passo 5x maior, segurar o botão repete), um
  campo onde dá pra digitar o número (Enter confirma, Esc cancela) e `PADRÃO`
  para voltar ao valor original. A roda do mouse sobre o número também ajusta.
- Na aba **CORES**, cada cor tem amostra e código hexadecimal (`#E6A92E`,
  digitável); selecionada, ganha sliders R/G/B e o contraste com o texto
  (aviso em vermelho abaixo de 4.5:1). ←→ e a roda clareiam/escurecem. Os
  botões escolhem texto claro ou escuro sozinhos pelo contraste; selos com cor
  de texto fixa no código não acompanham — confira na MESA COMPLETA.
- A interface do editor fica sempre nas cores/fonte padrão; só as prévias
  usam o que você está editando.
- À direita, duas vistas (tecla `M` alterna):
  - **ITEM**: o trecho da mesa afetado, em tamanho real e desenhado com o
    mesmo código do jogo, com troca de baralho e opção de virar as cartas.
  - **MESA COMPLETA**: a tela de verdade do jogo, numa partida simulada contra
    bots congelada numa cena (ex.: "sua vez no flop", "raise aberto", "sua vez
    no pré-flop", "sem jogada" no Dominó), com escolha de número de jogadores e de tamanho de
    janela (1280x800 a 1920x1080). O que sai da tela ou se sobrepõe fica
    contornado em vermelho e listado embaixo; o item selecionado fica em
    amarelo. O número de problemas aparece na aba mesmo enquanto você edita
    na vista ITEM. Clique na mesa (ou `F`) para ampliar.
- "Manter proporção" faz largura e altura de cartas/peças andarem juntas.
- `Salvar` (Ctrl+S) grava `config/layout.json`. Um jogo aberto percebe o
  arquivo novo em até 1 segundo e recarrega sozinho; **F5** no jogo força a
  recarga. Teclado no editor: ↑↓ escolhe o item, ←→ ajusta, 1-5/Tab troca de aba.
- **Presets** (botão no rodapé): conjuntos prontos de ajustes. Vêm com o jogo
  o "compacto" (janelas pequenas e notebooks) e o "grande" (telas de 1600x900
  ou mais); você pode salvar os seus com um nome. Aplicar troca todos os
  valores pelos do preset (falta Salvar pra valer no jogo). Os seus ficam em
  `config/presets/` — pra exportar ou importar, copie o `.json` de/pra essa
  pasta (o botão "Abrir pasta" abre ela).

Também dá pra editar à mão: crie `config/layout.json` só com o que quer
alterar, por exemplo para aumentar a sua carta no Hold'em:

```json
{"holdem": {"carta_jogador": [120, 168]}}
```

Tamanhos são `[largura, altura]` em pixels e cores `[r, g, b]` (0 a 255);
tempos dos bots em milissegundos. Cada item do arquivo padrão tem
`min`/`max` (valores fora da faixa são limitados) e um `rotulo` explicando o
que é. Um `layout.json` ausente, com erro de digitação ou com valor de
formato errado não quebra o jogo: o item afetado volta ao padrão. O host e o
cliente remoto de cada modo leem as mesmas chaves.

## Compilando para .exe (Windows)

1. Instale as dependências em uma máquina/VM Windows (o `.exe` deve ser
   gerado no próprio Windows, o PyInstaller não faz cross-compile):

```bash
pip install pygame pyinstaller
```

2. Na pasta do projeto, rode:

```bash
pyinstaller PixelPoker.spec
```

   O `PixelPoker.spec` equivale a
   `pyinstaller --onefile --windowed --name "PixelPoker" --add-data "config/layout_padrao.json;config" --add-data "config/presets_padrao/*.json;config/presets_padrao" main.py`:
   - `--onefile`: gera um único executável `.exe`.
   - `--windowed`: remove o console do terminal (janela gráfica pura).
   - `--name "PixelPoker"`: define o nome do executável final.
   - `--add-data`: embute os valores padrão de layout (sem eles o jogo não
     abre) e os presets do jogo. Se usar a linha de comando em vez do
     `.spec`, não esqueça essas opções.

3. O executável final aparece em `dist/PixelPoker.exe`. Para usar ajustes de
   layout com o exe, coloque um `config/layout.json` na mesma pasta dele (o
   editor e o botão "Editor de layout" não vão no exe - `tools/` fica de fora).

> Dica: se no futuro você adicionar imagens/sons externos, use também
> `--add-data "assets;assets"` para embutir a pasta de assets no exe.
