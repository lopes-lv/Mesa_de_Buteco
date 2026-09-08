# Pixel Poker - Texas Hold'em Solo vs Bots

Jogo de Texas Hold'em (Solo vs Bots) em Python + Pygame, com estética
"pixel art" desenhada 100% via `pygame.draw` (sem imagens externas).

## Estrutura do projeto

```
poker_game/
├── main.py             # Ponto de entrada, loop principal e state machine
├── screens.py          # Tela de Menu Inicial e Configuração
├── table_screen.py      # Tela de Mesa (gameplay completo)
├── game_logic.py        # Player, BettingRound, Table, blinds, pote/side-pots
├── hand_evaluator.py     # Avaliação de mãos (7 cartas -> melhor 5, ranking)
├── bot_ai.py             # IA simples dos bots (baseada na força da mão)
├── deck.py               # Cartas e baralho
└── ui_pixelart.py        # Todas as funções de desenho pixel art
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

Os bots calculam um "score" de força de mão (0–100):
- Pré-flop: heurística de pares, cartas altas, conectadas e naipe igual.
- Pós-flop: categoria da melhor mão possível com as cartas comunitárias.

Com o score, decidem entre Fold / Check-Call / Raise, com uma pequena
variação aleatória para evitar decisões 100% mecânicas.

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
