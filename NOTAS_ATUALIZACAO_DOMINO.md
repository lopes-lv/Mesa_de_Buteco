# Notas de Atualização — Dominó: Corrida aos 250 Pontos

Reforma completa do modo Dominó: visual das peças, encaixe, escolha de
lado, regra de abertura e um sistema de pontuação totalmente novo. Este
documento serve de modelo/rascunho pra divulgar a atualização — ajuste o
tom e o formato como preferir.

## Resumo em uma linha

O Dominó deixou de ser uma variante "bloqueio/compra" com fichas e virou
uma corrida de pontos até **250**, jogada só com **3 ou 4 pessoas**, no
estilo tradicional de mesa de bar.

## O que mudou

### Visual
- **Peças da mesa agora são retangulares de verdade** (proporção 2:1), em
  vez do formato quase quadrado de antes.
- **Bug de encaixe corrigido**: os números que se tocam entre duas peças
  vizinhas na mesa agora sempre batem. Antes, uma peça jogada "virada" podia
  mostrar o número errado do lado que encosta na vizinha.

### Jogadores e distribuição
- O modo agora só é jogado com **3 ou 4 jogadores** (bots ou pessoas,
  solo ou multiplayer local).
- **Com 4 jogadores**: jogo completo (28 peças), 7 na mão de cada um.
- **Com 3 jogadores**: a peça **0/0** é retirada do jogo, sobrando 27
  peças — 9 na mão de cada um.
- Não existe mais monte/compra: todo mundo já recebe, de saída, todas as
  peças que vai ter na mão a mão inteira.

### Escolha de peça e lado
- Continua sendo o jogador quem escolhe qual peça jogar e, quando ela
  encaixa nas duas pontas da mesa, em qual lado colocar.

### Botão de Passar
- Como não existe mais compra, quando o jogador não tem nenhuma peça que
  encaixe, aparece o botão **"Passar"** — precisa ser clicado, não é mais
  automático.

### Abertura da mão
- **Primeira mão da partida**: quem tiver a peça **6/6** na mão abre, e é
  obrigado a jogar justamente essa peça.
- **Mãos seguintes**: quem bateu (esvaziou a mão) na mão anterior abre a
  próxima, escolhendo qual carroça jogar entre as que tiver na mão (só
  abre com qualquer peça se não tiver carroça nenhuma).
- **Depois de um travamento total** (ver abaixo): a próxima mão volta a
  exigir abertura com a 6/6, igual à primeira mão.

### Pontuação — como marcar pontos

| Evento | Pontos |
|---|---|
| Jogada fecha as duas pontas da mesa num múltiplo de 5 | os pontos das pontas (carroça na ponta conta em dobro) |
| Bater (esvaziar a mão primeiro) | soma dos pontos das peças que sobraram nas mãos dos outros, arredondada **pra baixo** pro múltiplo de 5 mais próximo |
| Última peça jogada (a que bateu) é uma carroça | +30, somado ao bônus de bater |
| Jogar imediatamente antes de alguém passar | +10 |
| Travar parcialmente — todo mundo passa e a vez volta pra quem jogou, que ainda consegue jogar (o jogo continua) | +50 |
| Travamento total — ninguém, nem quem travou, consegue jogar mais | quem tem menos pontos na mão ganha a mesma soma arredondada (regra de "bater" acima) |

Exemplo do arredondamento: sobraram as peças 3/5 e 5/5 na mão do
adversário → 8 + 10 = 18 pontos → desce pro múltiplo de 5 mais próximo,
**15**.

### Vitória
- A pontuação de cada jogador é acumulada mão após mão (não zera entre
  mãos).
- Assim que uma mão termina (bateu ou travamento total), confere-se se
  alguém já tem 250 pontos ou mais — se sim, essa pessoa vence a partida
  inteira ali. Senão, começa outra mão.

## Decisões de design (pontos que não estavam 100% especificados)

Alguns detalhes não tinham uma regra explícita definida; usei o bom senso
pra fechar, documentados aqui pra revisão:

- **Pontuação de travamento total**: não foi dado um número específico pra
  quem vence um travamento total, então reaproveitei a mesma fórmula do
  bônus de bater (soma dos pontos dos outros, arredondada pra baixo em
  múltiplo de 5). Se preferir um valor fixo ou outra fórmula, é só ajustar
  `DominoTable._liquidar_bloqueio_total` em `domino_logic.py`.
- **Acúmulo de bônus na mesma jogada**: a pontuação por múltiplo de 5, o
  bônus de bater e o bônus de carroça podem se somar todos na mesma última
  jogada (são regras independentes no pedido original, então não são
  mutuamente exclusivas). Da mesma forma, o bônus de trancar parcial (+50)
  e a pontuação de múltiplo de 5 da mesma jogada também se somam.
- **Empate no travamento total**: se mais de um jogador empatar com a
  menor pontuação na mão, os pontos são divididos entre eles (não há uma
  regra de desempate no pedido original).

## Arquivos que mudaram

- `domino_logic.py` — motor reescrito (sem monte, `PecaNaMesa` com
  orientação visual, pontuação, regras de abertura/passe/trancar).
- `domino_theme.py` — `desenhar_peca` agora recebe os valores já
  orientados em vez de um objeto `Peca`.
- `domino_screen.py` / `mesa_remota_domino_screen.py` — botão de Passar,
  placar de pontuação no lugar de fichas, mensagens de histórico com os
  bônus, peças retangulares.
- `domino_bot_ai.py` — bots agora preferem jogadas que pontuam.
- `screens.py` / `multiplayer_screens.py` — seleção de 3 a 4 jogadores
  (solo e multiplayer).
- `rede/protocolo.py` — a ação de rede `acao_domino` ganhou o tipo
  `"passar"` (antes só existia `"jogar"`).
