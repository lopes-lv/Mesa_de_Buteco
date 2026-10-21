# Dominó

Corrida de pontos até **250**, livre-para-todos (sem duplas), com o jogo
**duplo-seis** e **3 ou 4 jogadores**, no estilo de mesa de bar. Joga-se solo
contra bots ou em multiplayer local (sala de 3 a 4).

## Arquivos

| Arquivo | Papel |
|---|---|
| `domino_logic.py` | `Peca`, `PecaNaMesa`, `DominoPlayer`, `DominoTable`: distribuição, jogadas legais, pontuação, passe e travamento |
| `domino_bot_ai.py` | IA dos bots |
| `domino_theme.py` | Desenho das peças (pips e verso) |
| `domino_screen.py` | Tela de mesa do host/jogo local |
| `mesa_remota_domino_screen.py` | Tela do cliente remoto |

## Regras implementadas

### Distribuição
Não existe monte nem compra.
- **4 jogadores:** jogo completo (28 peças), 7 para cada um.
- **3 jogadores:** a peça **0/0** sai do jogo, sobram 27 peças e cada um recebe
  9. Nos dois casos a divisão é exata (`criar_pecas()`).

### Jogar e passar
Quem não tem peça que encaixe clica em **Passar** (ação explícita; bots e
jogadores desconectados passam sozinhos). Quando a peça encaixa nas duas pontas
(ou em mais de uma direção), você escolhe onde colocá-la.

### Abertura
A primeira jogada de toda mão é **obrigatoriamente uma carroça** (peça dupla):
- **Primeira mão e toda mão depois de um travamento total:** quem tem a **6/6**
  abre e é obrigado a jogar justamente essa.
- **Demais mãos:** quem bateu por último abre, escolhendo qual carroça jogar
  entre as que tiver. Só abre com outra peça se não tiver nenhuma carroça.

### A mesa em cruz
Normalmente a mesa é uma linha (esquerda/direita). Se a peça de abertura é uma
carroça, ela vira um **spinner** (garantido quando a abertura é a 6/6 forçada,
opcional numa abertura livre). As pontas de **cima** e de **baixo** só passam
a valer depois que os dois lados do spinner já têm pelo menos uma peça (o
"bucho", `bucho_liberado()`). Só a peça de abertura gira: uma carroça jogada
depois, em qualquer ramo, apenas aparece deitada, sem criar ramo novo.

`jogadas_possiveis_em()` é a fonte única de quais pares `(peça, direção)` são
legais. Ela **não** elimina duplicatas entre direções, porque cada direção é um
lugar físico diferente, mesmo que duas pontas mostrem o mesmo número. O host
reconfere o bucho e a abertura em `jogar()`; o cliente remoto só espelha isso
para realçar jogadas.

### Pontuação

| Evento | Pontos |
|---|---|
| Uma jogada fecha as pontas da mesa num múltiplo de 5 | o total das pontas (carroça na ponta conta em dobro) |
| Bater (esvaziar a mão primeiro) | soma dos pontos que sobraram nas mãos dos outros, arredondada **para baixo** ao múltiplo de 5 |
| A peça que bateu é uma carroça | +30, somados ao bônus de bater |
| Jogar imediatamente antes de alguém passar | +10 |
| Trancar parcialmente (todos passam, a vez volta para você e você ainda joga; a mão continua) | +50 |
| Travamento total (ninguém consegue jogar) | quem tem menos pontos na mão ganha a mesma soma arredondada |

Exemplo do arredondamento: sobraram 3/5 e 5/5 → 8 + 10 = 18 → **15**.

As pontas de cima e de baixo só contam na pontuação quando já têm peça.

### Vitória
A pontuação acumula de mão em mão. Só ao **fim** de uma mão (nunca no meio) se
confere se alguém tem 250 pontos ou mais; quem tiver vence a partida.
`DominoTable.vencedor_do_jogo()` faz essa checagem. Ninguém é eliminado e não
há fichas.

## IA dos bots
Uma heurística única: prefere a jogada que **pontua** (fecha as pontas num
múltiplo de 5, via `DominoTable.pontuacao_se_jogar`), depois **carroças** (só
encaixam num número, então ficam mais fáceis de prender na mão) e, entre o que
sobra, a peça de **maior valor** (reduz o prejuízo se a mão travar).

## Interface
- **Arrastar e soltar:** apertar o botão sobre uma peça jogável da mão inicia o
  arraste (`peça_arrastando`). Ao soltar sobre uma zona de encaixe válida *para
  aquela peça*, a jogada é feita. Soltar em outro lugar não faz nada (a peça
  nunca saiu da mão).
- **Carroças deitadas:** cada ramo cresce no seu eixo, e uma carroça fica
  sempre perpendicular a ele. Por isso ela avança menos o cursor do que uma
  peça normal.
- **Escala única:** um só fator de escala é escolhido para caber, de uma vez,
  a extensão horizontal (esquerda + direita) e a vertical (cima + baixo) no
  feltro, sem tamanho mínimo: um ramo longo apenas renderiza menor, nunca
  vaza. Os ramos são calculados com a peça central em (0, 0) e depois o
  conjunto todo (peças e zonas de encaixe) é transladado para que o **centro
  do conjunto** coincida com o centro do feltro.
- **Geometria da tela:** o feltro fica a 44% da altura (`CENTRO_MESA_Y`), e os
  assentos da metade de cima ficam mais perto dele (`FOLGA_ASSENTO_CIMA` /
  `FOLGA_ASSENTO_BAIXO`) para o assento de cima caber com 4 jogadores. O botão
  Passar fica ao lado da mão (`posicionar_botao_passar()`). Essas constantes
  são importadas pelo cliente remoto.
- Os tamanhos vêm das chaves `domino.*` de `config/layout_padrao.json`,
  editáveis pelo [editor visual](../tools/README.md).

## Multiplayer
Sala de 3 a 4 jogadores. O máximo vem de `MAX_JOGADORES_POR_JOGO`
(`menus/multiplayer_screens.py`) e o mínimo de `LobbyScreen._pode_iniciar`. A
ação de rede `acao_domino` aceita `"jogar"` e `"passar"`. Ver
[`MULTIPLAYER_PLANO.md`](../MULTIPLAYER_PLANO.md).

## Notas de atualização

### Reforma: corrida aos 250 pontos
Reformulação completa do modo. O Dominó deixou de ser uma variante
"bloqueio/compra" com fichas e virou uma corrida de pontos.

**O que mudou**
- **Visual:** as peças da mesa são retangulares de verdade (proporção 2:1),
  em vez do formato quase quadrado de antes.
- **Bug de encaixe corrigido:** os números que se tocam entre duas peças
  vizinhas agora sempre batem. Antes, uma peça jogada "virada" podia mostrar o
  número errado no lado que encosta na vizinha.
- **Jogadores:** só 3 ou 4 (bots ou pessoas, solo ou multiplayer).
- **Sem monte:** todo mundo recebe de saída as peças que terá na mão.
- **Botão Passar:** como não há compra, quem não tem peça que encaixe clica em
  Passar (antes era automático).
- **Abertura obrigatória com carroça** e regras de quem abre (acima).
- **Pontuação nova** e vitória aos 250, no lugar das fichas.
- **Mesa em cruz** com spinner e bucho, e **arrastar e soltar** no lugar de
  "clicar na peça e depois no lado".

**Decisões de design (pontos que não estavam 100% especificados)**
- **Travamento total:** sem número definido, reaproveitou-se a fórmula do bônus
  de bater (soma dos outros, arredondada para baixo a múltiplo de 5). Para
  mudar, ajuste `DominoTable._liquidar_bloqueio_total`.
- **Bônus acumulam na mesma jogada:** múltiplo de 5, bônus de bater e bônus de
  carroça se somam, e o +50 de trancar parcial soma com o múltiplo de 5 da
  mesma jogada.
- **Empate no travamento total:** se mais de um jogador empatar com a menor
  pontuação na mão, os pontos são divididos entre eles.

**Arquivos que mudaram**
- `domino_logic.py`: motor reescrito (sem monte, `PecaNaMesa` com orientação
  visual, pontuação, abertura/passe/trancar).
- `domino_theme.py`: `desenhar_peca` recebe valores já orientados, não um
  objeto `Peca`.
- `domino_screen.py` e `mesa_remota_domino_screen.py`: botão Passar, placar de
  pontos no lugar de fichas, mensagens de histórico com os bônus, peças
  retangulares.
- `domino_bot_ai.py`: bots preferem jogadas que pontuam.
- `menus/screens.py` e `menus/multiplayer_screens.py`: seleção de 3 a 4
  jogadores.
- `rede/protocolo.py`: `acao_domino` ganhou o tipo `"passar"`.

### Outubro de 2026 — ajustes de layout
- **Sem jogada:** as peças da mão ficavam por cima do botão Passar e da dica.
  Agora o Passar vai ao lado da mão e a dica fica embaixo dela.
- **4 jogadores:** o painel do assento de cima saía pela borda superior. O
  feltro passou de 36% para 44% da altura e os assentos da metade de cima de
  70 para 36 px do feltro.
- Tamanhos de peça e espaçamentos passaram a vir de `config/layout_padrao.json`.
- Estética "Pixel Art Retrô CRT" aplicada às peças e à mesa.

## Backlog do modo
- Validar o arrastar e soltar em jogo real (ver `lista_tarefas.md`).
