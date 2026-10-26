# Texas Hold'em

Modo principal do projeto: Texas Hold'em **No-Limit** contra bots, ou em
multiplayer local, com estrutura de torneio (a partida só acaba quando resta
um jogador com fichas).

## Arquivos

| Arquivo | Papel |
|---|---|
| `game_logic.py` | `Player`, `BettingRound` e `Table`: blinds, rodadas de apostas, all-in, pote e side pots, showdown |
| `hand_evaluator.py` | Avalia 7 cartas e devolve a melhor mão de 5 como uma tupla comparável |
| `bot_ai.py` | `decidir_acao_bot`: IA dos bots (perfis de risco, pot odds, blefe) |
| `table_screen.py` | Tela de mesa do host/jogo local (desenho, entrada do jogador, turno dos bots) |
| `mesa_remota_screen.py` | Tela do cliente remoto no multiplayer (só desenha o estado recebido do host) |

## Como funciona

### Fluxo de uma mão
Blinds → pré-flop → flop → turn → river → showdown. O jogador age com
**Fold**, **Check/Call** e **Raise** (valor escolhido num slider, com botão
de confirmar). Atalhos de teclado aparecem nos botões quando "Mostrar
atalhos" está ligado nos Ajustes.

### Blinds
Estrutura crescente, estilo torneio: o nível sobe a cada **5 mãos**
(`MAOS_POR_NIVEL`), de 10/20 até 400/800 (`ESTRUTURA_BLINDS`).

### Pote, side pots e empates
- `calcular_potes()` monta o pote principal e os side pots a partir do total
  apostado por cada jogador, o que cobre all-ins parciais, e junta potes
  consecutivos com o mesmo conjunto de elegíveis.
- Empates dividem o pote exatamente. O resto do arredondamento vai para quem
  está mais perto do dealer.
- A avaliação usa tuplas `(categoria, desempates...)`: maior tupla vence, e
  comparar, desempatar e detectar split pot é só comparação de tuplas do
  Python. Mantenha esse formato se estender o avaliador.

### Motor desacoplado
`Table` é uma máquina de estados pura: toda ação passa por
`rodada_atual.aplicar_acao(jogador, acao, valor)`, venha do mouse, do bot ou
de um pacote de rede. `Player.tipo` (`bot`, `humano_local`, `humano_remoto`)
só diz de onde vem a próxima ação; `Table`/`BettingRound` nunca o leem. Não
faça o motor depender de UI ou de entrada.

### Eliminação e espectador
Quem fica sem fichas é eliminado. Quem dá fold ou foi eliminado vira
**espectador** e vê as cartas de todos (no host e nos clientes remotos). O
croupiê aparece como uma pessoa em pé num recorte da mesa oval.

### IA dos bots
Cada bot recebe um perfil de risco fixo na partida: **tight**, **equilibrado**,
**agressivo** ou **tricky**. A decisão combina força da mão, draws, pot odds,
pressão da aposta, posição e número de oponentes ativos. Os bots roubam potes
sem aposta, pagam apostas grandes quando o preço compensa e blefam com
frequência controlada. A velocidade de jogada (lenta/normal/rápida) vem dos
Ajustes e de `geral.delay_bot_*_ms`.

### Fichas e carteira (solo)
No Hold'em solo o seu saldo é uma **carteira persistente**
(`core/carteira.py`, arquivo `config/carteira.json`, fora do git):

- Você entra na mesa com o saldo inteiro; o que sobrar volta para a carteira.
  Ganhou, acumula.
- O saldo é gravado ao fim de cada mão, ao clicar em Sair e ao fechar a
  janela. Sair no meio de uma mão perde a aposta já feita, como largar a mão.
- Se zerar, o botão "Iniciar Partida" fica bloqueado por **12 horas** (a tela
  de Configuração mostra o tempo restante). Depois disso a carteira volta a
  **2000** fichas.
- Os bots começam com o valor de "Fichas iniciais" dos Ajustes
  (`geral.fichas_iniciais`, padrão 1500).
- No multiplayer a carteira não é usada: todos começam com o mesmo valor.

### Layout da mesa (detalhes que importam)
Os tamanhos vêm de `config/layout_padrao.json` (chaves `holdem.*`), editáveis
pelo [editor visual](../tools/README.md). O host e o cliente remoto duplicam a
geometria, então **mudanças de posição precisam ser feitas nos dois arquivos**:

- O selo da aposta fica **ao lado** das cartas (o seu à direita, o dos bots
  voltado ao centro da mesa).
- O vão entre o painel de um bot e as cartas dele é `VAO_PAINEL_CARTAS_BOT`
  (10 px).
- Com 7 jogadores os ângulos dos assentos terminam em 35°; com 8 são
  `[90, 130, 165, 194, 228, 312, 348, 20]` (os 4 da esquerda ficam igualmente
  espaçados na vertical, o limite para painel + cartas não se sobreporem em
  768 px de altura).
- A linha Fold/Call/Raise e o painel de raise recuam em janelas estreitas para
  não encostar no histórico (`_limite_direito_controles`).
- Cada assento é limitado para o painel caber na tela (`MEIA_LARGURA_ASSENTO`).

## Notas de atualização

### Outubro de 2026
- **Blinds e showdown corrigidos.** O nível de blind agora sobe na 6ª mão (cada nível dura as 5 mãos
  prometidas; antes subia na 5ª). O showdown também passou a funcionar com ids de jogador que não são
  a posição do assento (no multiplayer, quem sai do lobby deixa um buraco nos ids), e o desempate da
  ficha ímpar continua indo para o primeiro empatado depois do dealer.
- **Carteira persistente** no Hold'em solo (veja acima). Antes, cada partida
  recomeçava com as fichas iniciais.
- **Layout em janelas menores (1024x768 a 1920x1080):** o detector do editor
  não acusa mais nenhum problema em nenhuma combinação de jogadores × janela ×
  cena. Mudou: selo de aposta ao lado das cartas (o seu ficava atrás dos
  botões de ação até em 1280x800; o dos bots invadia vizinhos e o histórico),
  vão painel-cartas dos bots de 14 para 10 px, ângulos de 7 e 8 jogadores
  refinados (as cartas do vizinho da esquerda invadiam o painel "Você" com 8),
  e Fold/Call/Raise cedendo espaço ao histórico em janelas estreitas.
- **Tamanhos configuráveis:** cartas, espaçamentos e botões deixaram de ser
  constantes nas telas e passaram a vir de `config/layout_padrao.json`
  (`core/layout.py`), com host e cliente remoto lendo as mesmas chaves.
- **Redesign "Pixel Art Retrô CRT":** nova paleta escura, cantos retos, bordas
  grossas, fonte monoespaçada e scanlines (antes: "Neobrutalismo Suave").
- **Baralhos:** 10 estilos de carta, escolhidos por setas na tela de
  Configuração (além do botão de ciclar nos Ajustes).

### Antes disso
- Mesa oval com recorte e croupiê em pé; espectador que vê as cartas de
  todos, no host e nos clientes remotos.
- Multiplayer local para o Hold'em (ver [`MULTIPLAYER_PLANO.md`](../MULTIPLAYER_PLANO.md)).
- IA dos bots com perfis estáveis por partida, pot odds e blefe.
- Blinds crescentes, side pots corretos e split pot exato.

## Pendências do modo
Ver `lista_tarefas.md` na raiz. As principais: testar o espectador em
multiplayer real e revisar a mesa com 8 jogadores em janelas muito pequenas.
