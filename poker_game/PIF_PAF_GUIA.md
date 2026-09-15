# Guia de Implementação — Modo "Pif Paf"

Este documento é o guia de trabalho para adicionar o modo de jogo **Pif Paf**
ao projeto, item já previsto em [`GDD.md`](GDD.md) (seção 2.2, status
"Planejado") e no backlog em [`MELHORIAS.md`](MELHORIAS.md) (item 5). Como o
GDD deixava as regras como "a definir", a primeira parte deste guia registra
a pesquisa sobre o jogo tradicional e as decisões tomadas para adaptá-lo a
este projeto; a segunda parte é o plano técnico de implementação.

---

## 1. O que é o Pif Paf (pesquisa)

Pif Paf é um jogo de cartas tradicional brasileiro da família dos jogos de
"compra e descarte" (parente de Buraco/Cacheta), bem diferente do Texas
Hold'em: não há apostas em rodadas nem cartas comunitárias — cada jogador
monta combinações com as próprias cartas na mão, comprando e descartando por
turno, até "bater" (zerar a mão).

Resumo das regras tradicionais levantadas (fontes ao final da seção):

- Usa-se **dois baralhos de 52 cartas** (104 cartas), sem os coringas impressos.
- De 3 a 8 jogadores. Cada jogador recebe **9 cartas**, distribuídas de 3 em 3.
- O restante forma o **monte** (compra); a primeira carta virada forma o
  **descarte**.
- Em variantes mais ricas, existe a **"vira"**: uma carta é virada do monte
  antes da distribuição, e a carta de valor imediatamente acima dela vira
  **coringa** (substitui qualquer carta em qualquer combinação) naquela mão.
  Algumas regiões jogam sem esse coringa.
- No seu turno, o jogador compra **1 carta** (do monte ou do topo do
  descarte) e depois **descarta 1 carta**, a menos que consiga "bater".
- **Bater** = formar combinações válidas com todas as cartas da mão:
  - **Trinca**: 3+ cartas de mesmo valor, naipes diferentes.
  - **Sequência**: 3+ cartas seguidas do mesmo naipe (Ás pode ser alto ou
    baixo, mas não "dá a volta" ligando Q-K-A-2).
- **"A louca"**: em algumas variantes, qualquer jogador pode aproveitar o
  descarte alheio fora da própria vez para completar o jogo e bater na hora.
- Quem declara bater errado recolhe as cartas e fica restrito a comprar
  apenas do monte pelo resto da mão.
- Cada mão/rodada é independente: quem bate primeiro vence aquela mão.

**Fontes:**
- [Pif-Paf — Blog Copag](https://blog.copag.com.br/regras/pifpaf)
- [Pif Paf: saiba como jogar — Copag](https://blog.copag.com.br/curiosidades/pif-paf-saiba-como-jogar-e-conheca-as-principais-regras)
- [Regras do Pif Paf — Copag Loja](https://www.copagloja.com.br/regras-jogos/pif-paf)
- [Pif Paf regras completas — Supercacheta](https://supercacheta.com.br/pif-paf/pif-paf-regras-completas/)
- [Como Jogar Pife e Pafe — Mundo Tabuleiro](https://mundotabuleiro.com/como-jogar-pife-e-pafe/)

## 2. Decisões de design para este projeto (V1)

O GDD listava três perguntas em aberto. Ficam assim decididas para a
primeira versão implementada:

| Pergunta do GDD | Decisão |
|---|---|
| Quantas cartas na mão? | **9 cartas**, distribuídas de 3 em 3 (regra tradicional). |
| Tem curinga? | **Sim — "vira"**: 1 carta é virada do monte antes da distribuição; a carta de valor seguinte (mesmo dentro do próprio naipe da vira não importa, vale para os 4 naipes) é coringa na mão. Se a vira for Ás, o coringa é o 2. Alternativa opcional (ligada em Ajustes): **Joker impresso**, ver seção 2.3. |
| Regras de batida? | Bate quem formar **trincas e/ou sequências válidas com as 9 (ou 10, sem descartar) cartas**, sempre comprando primeiro (do monte **ou** do topo do descarte) e podendo bater na própria vez. |

Outras decisões necessárias para encaixar o jogo na estrutura atual do
projeto (economia de fichas, elenco de bots, UI):

- **"A louca" (bater fora da vez com o descarte alheio) fica de fora da V1.**
  Motivo: exigiria interromper o turno de qualquer jogador a qualquer
  momento (inclusive bots), o que aumenta bastante a complexidade da máquina
  de estados e da IA para o primeiro corte. Fica registrado no backlog
  (seção 10) para uma iteração futura.
- **Pontuação/fichas:** para reaproveitar a mesma economia de fichas do
  Texas Hold'em (jogador começa com fichas, mesa é um "torneio" até sobrar
  um jogador), cada mão fora vencida por quem bate primeiro:
  - Cartas numéricas valem o próprio número, J/Q/K valem 10, Ás vale 15.
    Carta coringa não usada em nenhuma combinação vale 20 (penaliza segurar
    o coringa parado).
  - Ao final da mão, cada jogador que não bateu paga em fichas a soma dos
    pontos das cartas que ainda restaram na mão (não combinadas) para o
    pote da rodada; quem bateu embolsa o pote.
  - Jogador que zera as fichas é eliminado, igual ao Hold'em; a partida
    termina quando resta 1 jogador.
- **Jogadores por mesa:** mantém o intervalo já usado no Hold'em (você + 1 a
  7 bots = 2 a 8 jogadores), que cabe na regra tradicional de "3 a 8"
  (com 2 jogadores o jogo também funciona mecanicamente, então não vale a
  pena adicionar uma trava exclusiva para este modo).
- **Baralho:** dois baralhos de 52 (sem coringa impresso, sem "curinga de
  fábrica") combinados — implementado como uma extensão de `deck.py`, não
  como um novo tipo de carta.

## 2.1 Atualização: regra "Mão Fechada" (bater sem comprar)

Adicionada depois da V1, ao investigar um caso real de jogo: um jogador
recebeu, já na distribuição, uma mão de 9 cartas 100% fechada (trinca + duas
sequências, zero cartas soltas). Como a regra original exige **sempre**
comprar antes de poder bater, essa mão perfeita ficava efetivamente presa —
a compra obrigatória quase sempre adiciona 1 carta que não encaixa em nada,
quebrando a mão de novo a cada turno (só ~15-20% das cartas do baralho
"servem" para estendê-la ou são coringa). Sem essa regra, cair numa mão
fechada era mais azar do que sorte.

Regra adicionada (tradicional do Buraco):

- Na **primeira vez que é a vez do jogador em uma mão** (antes de qualquer
  compra dele nessa mão), se as 9 cartas já formam trincas/sequências
  válidas sem sobra nenhuma, ele pode **bater direto, sem comprar**.
- Essa batida paga **o dobro** dos pontos soltos de cada adversário (em vez
  do valor normal).
- É uma janela de uma única chance por mão: assim que o jogador compra pela
  primeira vez naquela mão (mesmo sem bater), a opção de mão fechada se
  fecha para o resto da mão — ele passa a depender só da batida normal
  (com compra) dali em diante.
- Vale tanto para o jogador humano (botão extra "Bater (2x)" ao lado dos
  botões de compra, tecla `B`) quanto para os bots (verificado automaticamente
  antes de decidirem a fonte de compra).

Implementado em `PifPafTable.pode_bater_mao_fechada()` /
`PifPafTable.bater_mao_fechada()` (`pifpaf_logic.py`), com o controle de "já
agiu nesta mão" em `jogadores_ja_agiram_na_mao`.

## 2.2 Correção: bater descartando a carta que sobra

Bug real encontrado logo depois da regra acima (mesmo sintoma percebido pelo
jogador — "eu tinha uma mão perfeita e o jogo não reconheceu" —, causa
diferente): a V1 só reconhecia "bater" quando as **10 cartas** (antes de
descartar) já fechavam sozinhas, sem sobra nenhuma. Isso é, na prática, o
caso raro. O jeito normal de fechar a mão em qualquer jogo de compra-e-
descarte é comprar, organizar, e **descartar a última carta que sobra** —
e isso não vencia a mão, só passava a vez (o jogador ficava com 9 cartas
"prontas" só até a próxima vez que fosse sua vez, quando podia já ter
perdido para outro jogador).

Confirmado por simulação: rodando 300 mãos só com bots, 78% das vitórias
passaram a acontecer por esse caminho (antes da correção, 0%).

Regra adicionada:
- Ao clicar "Descartar" com uma carta selecionada, o jogo confere se as 9
  cartas restantes fecham (trincas/sequências, zero sobra). Se fecharem,
  o descarte **é** a batida (mesma pontuação normal de sempre — sem bônus,
  diferente da mão fechada) em vez de só passar a vez.
- A UI avisa antes: quando a carta selecionada fecharia a mão, aparece o
  aviso "Essa carta fecha sua mão!" e o botão muda de "Descartar" para
  "Bater!".
- Funciona também para os bots (a escolha de descarte já tende a escolher
  justamente a carta solta, então na maioria das vezes o bot já "acerta"
  a batida sem precisar de lógica extra).

Implementado em `PifPafTable.pode_bater_descartando()` /
`PifPafTable.bater_descartando()` (`pifpaf_logic.py`).

## 2.3 Atualização: Joker impresso (opcional, alternativa à vira)

A linha "Tem curinga?" da tabela na seção 2 descreve o sistema da vira (a
carta seguinte à virada vale coringa). Depois disso foi adicionada uma
segunda opção, ligada em **Ajustes → "Joker no Pif Paf"** (desligada por
padrão, preservando o comportamento original):

- **Desligada (padrão):** exatamente o sistema da vira descrito acima —
  nada muda.
- **Ligada:** o baralho ganha **4 Jokers impressos de verdade** (2 por cópia
  de 52, no baralho duplo de 104+4=108 cartas) como **único** coringa da
  mão. A vira continua sendo virada e exibida (define só decoração/UI), mas
  **deixa de gerar coringa por valor** — só o Joker impresso é coringa
  quando essa opção está ligada. É uma troca de sistema inteiro, não uma
  soma: nunca há coringa por valor **e** Joker impresso ao mesmo tempo.
- Um Joker vale 20 pontos soltos se ninguém usar ele numa combinação (mesma
  regra que já existia pro coringa da vira).

Implementado via `deck.NAIPE_CORINGA`/`VALOR_CORINGA` (o Joker é uma carta
própria — `naipe="coringa"` — não uma carta comum "emprestada"), a função
`pifpaf_logic.eh_coringa(carta, coringa_valor)` (que unifica os dois
sistemas: uma carta é coringa se for um Joker impresso OU se
`coringa_valor` não for `None` e bater com o valor dela) e
`criar_baralho_duplo(usar_joker=...)`. `PifPafTable.usar_joker` guarda a
opção da mesa; `PifPafTable.coringa_valor` fica `None` quando `usar_joker`
está ligado.

## 3. Arquitetura técnica

### 3.1 Arquivos novos

- **`pifpaf_logic.py`** — motor do jogo, nos moldes de `game_logic.py`:
  - `criar_baralho_duplo()` (ou classe `DeckDuplo`) — 104 cartas.
  - `PifPafPlayer` — id, nome, stack, `mao` (lista de `Card`), `is_bot`,
    `eliminado`.
  - Funções puras de validação de combinações: `eh_trinca(cartas)`,
    `eh_sequencia(cartas)`, considerando o valor coringa da mão.
  - `melhor_organizacao(mao, coringa)` — tenta agrupar a mão em
    trinca(s)/sequência(s) + sobras, para checar se dá para bater e para
    calcular pontos de quem não bateu.
  - `PifPafRound`/`PifPafTable` — orquestra: define a vira/coringa, distribui
    9 cartas por jogador, controla turno (comprar → [bater] → descartar),
    monte e descarte, detecta fim de mão e faz a liquidação de fichas.
- **`pifpaf_bot_ai.py`** — decisão dos bots, nos moldes de `bot_ai.py`:
  - Escolher a fonte de compra (descarte só se completa/ajuda uma
    combinação real; senão monte).
  - Escolher a carta a descartar (a mais "solta", sem par/sequência
    próxima, priorizando não descartar o coringa nem cartas que já formam
    trinca/sequência).
  - Decidir se bate assim que possível (bate sempre que válido — não há
    razão estratégica para segurar, diferente do Hold'em).
- **`pifpaf_screen.py`** — tela de mesa do Pif Paf, equivalente a
  `table_screen.py`, reaproveitando os desenhos de `ui_theme.py`
  (`desenhar_carta`, `desenhar_painel`, `desenhar_botao`, `desenhar_avatar`,
  `desenhar_badge`, `desenhar_mesa`, `desenhar_glow_de_vez`, histórico de
  ações). Elementos próprios deste modo: pilha do monte, pilha do descarte
  (carta virada), badge da vira/coringa, mão do jogador com seleção de carta
  por clique, botões contextuais "Comprar do Monte", "Comprar do Descarte",
  "Bater", "Descartar".

### 3.2 Arquivos alterados

- **`screens.py`** — nova `ModeSelectScreen` (Menu → Escolha de Modo →
  Configuração), com os cards "Texas Hold'em" (ativo) e "Pif Paf" (ativo)
  reaproveitando o conceito "Ativo/Em breve" que já existe nos mockups em
  `design/*/mockup.html` (hoje não usado no jogo real, conforme observado em
  `MELHORIAS.md` item 5). `ConfigScreen` passa a receber o modo escolhido e
  chamar o método de início de partida correspondente.
- **`main.py`** — `App` ganha `ir_para_escolha_modo()` e
  `iniciar_partida_pifpaf(quantidade_bots)`, análogos aos métodos que já
  existem para o Hold'em; `tela_atual` continua sendo o único ponto de
  state machine.
- **`GDD.md`** — seção 2.2 atualizada de "Planejado" para "Implementado",
  com as regras finais (ligar para este guia).
- **`MELHORIAS.md`** — marca o item "Implementar o modo de jogo Pif Paf".
- **`README.md`** — menção ao novo modo e ao novo arquivo na estrutura do
  projeto.

Não é necessário mexer em `hand_evaluator.py` (é específico da avaliação de
mãos de pôquer) nem em `deck.py` além de adicionar o baralho duplo — o
`Card` já serve para os dois modos.

## 4. Fluxo de turno do Pif Paf

```
Início da mão:
  monta baralho duplo (104 cartas) → embaralha
  vira 1 carta → define coringa (valor seguinte)
  distribui 9 cartas por jogador (3 em 3)
  1 carta abre o descarte

Turno do jogador da vez:
  1. Compra 1 carta (monte OU topo do descarte)
  2. Se a mão inteira (10 cartas) forma combinações válidas → BATE, mão termina
  3. Senão, descarta 1 carta (volta a 9) → passa a vez ao próximo jogador

Fim da mão (alguém bateu):
  - calcula pontos das cartas soltas de cada jogador que não bateu
  - cada um paga esses pontos em fichas para o pote
  - quem bateu recebe o pote
  - jogador com fichas <= 0 é eliminado
  - resta 1 jogador → fim de partida (mesmo fluxo de "fim de jogo" do Hold'em)
```

## 5. Plano de implementação (checklist)

1. [x] `pifpaf_logic.py`: baralho duplo, `PifPafPlayer`, validação de
   trinca/sequência com coringa, motor de turno e liquidação de fichas.
2. [x] `pifpaf_bot_ai.py`: heurística de compra/descarte/batida.
3. [x] `pifpaf_screen.py`: renderização da mesa, interação do jogador humano
   (selecionar carta da mão, comprar, descartar, bater), histórico de ações,
   tela de resultado de mão e tela de fim de jogo (reaproveitando o padrão
   visual de `table_screen.py`).
4. [x] `screens.py` + `main.py`: tela de escolha de modo (`ModeSelectScreen`)
   e roteamento.
5. [x] Testado via simulação automatizada (bots jogando sozinhos, várias
   seeds e contagens de jogadores de 2 a 8) cobrindo: distribuição, compra do
   monte, compra do descarte, descarte, batida válida, fim de mão com
   liquidação de fichas, eliminação e fim de jogo; e via renderização
   headless de todas as telas (mesa em vários tamanhos de janela, mão
   selecionada, resultado, mão empatada, tela final). Durante os testes
   foram encontrados e corrigidos 3 bugs: distribuição dando 3 cartas por
   jogador em vez de 9, um ciclo infinito de compra/descarte quando a
   heurística de compra do bot divergia do critério de descarte, e um crash
   ao desenhar a mão com nenhuma carta selecionada (`Card.__eq__` não
   tratava comparação com `None`, corrigido em `deck.py`). Também foi
   adicionada uma trava de segurança (mão empata após muitos turnos sem
   batida) para o jogo nunca travar mesmo com uma distribuição ruim.
6. [x] Atualizar `GDD.md`, `MELHORIAS.md` e `README.md`.

## 6. Resumo do que será realmente implementado nesta versão

**Entra nesta versão:**
- Modo Pif Paf completo e jogável (você vs. bots), com tela de escolha de
  modo no menu.
- Baralho duplo (104 cartas), vira/coringa, distribuição de 9 cartas.
- Compra (monte ou descarte), descarte e batida com trincas/sequências.
- Liquidação de fichas por pontos das cartas não combinadas e eliminação de
  jogadores, reaproveitando a mesma lógica de "torneio até sobrar 1" do
  Hold'em.
- IA de bots própria para este modo (heurística, sem a profundidade
  estatística do `bot_ai.py` do Hold'em).
- Tela de mesa própria, no mesmo estilo visual "Neobrutalismo Suave" já
  usado no resto do jogo.

**Fica fora desta versão (backlog para depois):**
- Regra da **"a louca"** (bater fora da vez usando o descarte alheio).
- Seleção/customização de baralhos visuais (já é um item pendente separado
  no `MELHORIAS.md`, não específico do Pif Paf).
- Personalidades de bot diferenciadas por partida no Pif Paf (existe hoje só
  para o Hold'em); os bots do Pif Paf usam uma única heurística fixa nesta
  primeira versão.
