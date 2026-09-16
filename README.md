# Texas Hold'em, Pif Paf & Dominó - Solo vs Bots ou Multiplayer Local

Jogo de cartas/peças em Python + Pygame, com três modos — **Texas Hold'em**,
**Pif Paf** (ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md)) e **Dominó** — jogáveis
solo contra bots ou em **multiplayer local** (mesma rede Wi-Fi/LAN, ver
[MULTIPLAYER_PLANO.md](MULTIPLAYER_PLANO.md)), com estética "Neobrutalismo
Suave / Dashboard Analítico" (ver `design/01_neobrutalismo_suave/`)
desenhada 100% via `pygame.draw` (sem imagens externas).

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
│   ├── ui_theme.py                 # Biblioteca de desenho neobrutalista (ativa)
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

## Compilando para .exe (Windows)

1. Instale as dependências em uma máquina/VM Windows (o `.exe` deve ser
   gerado no próprio Windows, o PyInstaller não faz cross-compile):

```bash
pip install pygame pyinstaller
```

2. Na pasta do projeto, rode:

```bash
pyinstaller --onefile --windowed --name "PixelPoker" main.py
```

   - `--onefile`: gera um único executável `.exe`.
   - `--windowed`: remove o console do terminal (janela gráfica pura).
   - `--name "PixelPoker"`: define o nome do executável final.

3. O executável final aparece em `dist/PixelPoker.exe`.

> Dica: se no futuro você adicionar imagens/sons externos, use também
> `--add-data "assets;assets"` para embutir a pasta de assets no exe.
