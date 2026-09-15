# Texas Hold'em & Pif Paf - Solo vs Bots

Jogo de cartas (Solo vs Bots) em Python + Pygame, com dois modos —
**Texas Hold'em** e **Pif Paf** (ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md)) —
com estética "Neobrutalismo Suave / Dashboard Analítico" (ver
`design/01_neobrutalismo_suave/`) desenhada 100% via `pygame.draw` (sem
imagens externas).

## Estrutura do projeto

```
poker_game/
├── main.py             # Ponto de entrada, loop principal e state machine
├── screens.py          # Menu Inicial, Escolha de Modo e Configuração
├── table_screen.py      # Tela de Mesa do Texas Hold'em (gameplay + histórico)
├── game_logic.py        # Player, BettingRound, Table, blinds, pote/side-pots
├── hand_evaluator.py     # Avaliação de mãos (7 cartas -> melhor 5, ranking)
├── bot_ai.py             # IA dos bots do Hold'em (perfis, pot odds e blefe)
├── pifpaf_screen.py       # Tela de Mesa do Pif Paf (monte, descarte, mão, histórico)
├── pifpaf_logic.py         # Baralho duplo, coringa, trincas/sequências, turnos
├── pifpaf_bot_ai.py         # IA dos bots do Pif Paf (compra, descarte, batida)
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
