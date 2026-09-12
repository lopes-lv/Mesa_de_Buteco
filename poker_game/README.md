# Texas Hold'em Solo vs Bots

Jogo de Texas Hold'em (Solo vs Bots) em Python + Pygame, com estética
"Neobrutalismo Suave / Dashboard Analítico" (ver `design/01_neobrutalismo_suave/`)
desenhada 100% via `pygame.draw` (sem imagens externas).

## Estrutura do projeto

```
poker_game/
├── main.py             # Ponto de entrada, loop principal e state machine
├── screens.py          # Tela de Menu Inicial e Configuração
├── table_screen.py      # Tela de Mesa (gameplay completo + histórico de ações)
├── game_logic.py        # Player, BettingRound, Table, blinds, pote/side-pots
├── hand_evaluator.py     # Avaliação de mãos (7 cartas -> melhor 5, ranking)
├── bot_ai.py             # IA dos bots (perfis, pot odds e blefe)
├── deck.py               # Cartas e baralho
├── ui_theme.py            # Biblioteca de desenho neobrutalista (ativa)
├── ui_pixelart.py         # Estética pixel art anterior (não usada mais; mantida
│                          # de referência para uma eventual reintrodução como
│                          # baralho alternativo, ver GDD.md seção 3.2)
└── design/                # Guias técnicos e mockups HTML dos estilos visuais
```

## Como executar (desenvolvimento)

```bash
pip install pygame
python main.py
```

A janela é redimensionável — todo o layout se adapta ao tamanho atual.

## Regras implementadas

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

## IA dos Bots

Cada bot tem um perfil de risco estável, variando entre tight, equilibrado,
agressivo e tricky. A decisão combina força da mão, draws, pot odds, pressão
da aposta, posição na mesa e quantidade de oponentes ativos. Os bots podem
roubar um pote sem aposta, pagar apostas grandes quando o preço justifica e
blefar com frequência controlada, em vez de sempre foldar mãos fracas ou
copiar um check com outro check.

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
