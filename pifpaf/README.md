# Pif Paf

Jogo brasileiro de compra e descarte (parente do Buraco e da Cacheta), com
baralho duplo. Não há apostas nem cartas comunitárias: cada jogador monta
trincas e sequências com a própria mão, comprando e descartando por turno, até
**bater** (fechar a mão). Joga-se solo contra bots ou em multiplayer local, de
2 a 8 jogadores.

## Arquivos

| Arquivo | Papel |
|---|---|
| `pifpaf_logic.py` | `PifPafPlayer`, `PifPafTable`, baralho duplo, validação de trincas/sequências, pontos soltos |
| `pifpaf_bot_ai.py` | IA dos bots: fonte da compra e carta a descartar |
| `pifpaf_screen.py` | Tela de mesa do host/jogo local |
| `mesa_remota_pifpaf_screen.py` | Tela do cliente remoto (importa a geometria de `pifpaf_screen.py`) |

## Regras implementadas

- **Baralho:** dois baralhos de 52 cartas (104). Cada jogador recebe **9
  cartas**, distribuídas de 3 em 3. A primeira carta do que sobra abre o
  descarte e o resto forma o monte.
- **Turno:** compra 1 carta (do monte **ou** do topo do descarte) e depois
  descarta 1 ou **bate**.
- **Combinações válidas:**
  - **Trinca/quadra:** 3 ou 4 cartas do mesmo valor, de naipes diferentes.
  - **Sequência:** 3 ou mais cartas seguidas do mesmo naipe. O Ás vale 14
    (acima do Rei) ou 1 (abaixo do 2), mas nunca liga Q-K-A-2.
- **Bater:** a mão inteira precisa ficar organizada em combinações, sem carta
  solta. Normalmente se faz isso **descartando a última carta que sobra** (o
  descarte é a própria batida; a tela avisa "Essa carta fecha sua mão!" e o
  botão vira "Bater!").
- **Mão fechada:** na primeira vez que é a sua vez na mão, se as 9 cartas já
  formam combinações sem sobra, você bate **sem comprar** (botão "Bater (2x)",
  tecla `B`). Vale **2 vitórias**. A janela é de uma chance por mão: depois da
  primeira compra ela fecha.
- **Placar, sem fichas:** quem bate ganha a mão (1 vitória) e a partida acaba
  quando alguém chega a **3 vitórias** (`VITORIAS_PARA_VENCER`). Ninguém é
  eliminado.
- **Pontos das cartas soltas:** número = valor, J/Q/K = 10, Ás = 15, Joker = 20.
  Aparecem na tela de resultado só como informação.
- **Mão empatada:** se ninguém bater em 200 turnos
  (`LIMITE_TURNOS_SEM_BATIDA`), a mão empata e ninguém pontua. É uma trava para
  a partida nunca ficar presa.
- **Coringa:** não há coringa por padrão. Em Ajustes, **"Joker no Pif Paf"**
  acrescenta 4 Jokers impressos (2 por baralho de 52, 108 cartas no total),
  que substituem qualquer carta em qualquer combinação. Não existe mais
  "vira".
- **Fora do escopo:** a regra da **"a louca"** (bater fora da vez com o
  descarte de outro jogador). Exigiria interromper o turno de qualquer
  jogador a qualquer momento, o que complicaria muito a máquina de estados e a
  IA.

## IA dos bots

Uma heurística única, sem perfis por partida (diferente do Hold'em):

- Compra do descarte **só** quando a carta realmente reduz os pontos soltos da
  mão (mesmo critério usado para escolher o descarte, o que evita comprar uma
  carta e devolvê-la em seguida). Senão compra do monte.
- Bate sempre que possível, inclusive de mão fechada, que é verificada antes
  da compra.
- Ao descartar, livra-se da carta solta de maior valor e nunca descarta um
  Joker.

## Multiplayer

O host roda o jogo e os clientes só desenham o estado que recebem. No cliente,
"posso bater?" é recalculado localmente com as funções puras de
`pifpaf_logic.py` (`pode_bater_mao`), só sobre a própria mão, para evitar
ida e volta de rede a cada carta selecionada. A validação que vale continua
só no host. Ver [`MULTIPLAYER_PLANO.md`](../MULTIPLAYER_PLANO.md).

## Geometria da mesa

`pifpaf_screen.py` exporta o que o cliente remoto reutiliza:
`mesa_rect_para()`, `posicoes_assentos()`, `topo_da_mao()` (a mão nunca começa
acima da base do painel "Você") e `posicao_selo_historico()` (o selo da última
ação desce quando cobriria um painel de assento). Os tamanhos vêm das chaves
`pifpaf.*` do `config/layout_padrao.json`, editáveis pelo
[editor visual](../tools/README.md).

## Notas de atualização

### Outubro de 2026 — sem fichas e sem vira
- **Sem fichas.** O Pif Paf deixou de ter economia: ninguém paga nem é
  eliminado. Quem bate ganha a mão (`PifPafPlayer.vitorias`), e a partida
  termina em 3 vitórias (`PifPafTable.vencedor_do_jogo()`). A mão fechada, que
  antes cobrava o dobro das fichas, agora vale 2 vitórias. O seletor "Fichas
  iniciais" dos Ajustes e a carteira do Hold'em não afetam este modo.
- **Sem vira.** Nenhuma carta é virada e não existe mais coringa por valor.
  `eh_coringa(carta)` é verdadeiro só para o Joker impresso, e as funções de
  combinação perderam o parâmetro `coringa_valor`.
- **Joker opcional** continua nos Ajustes, desligado por padrão. Antes ele
  *substituía* a vira; agora, desligado, não há coringa nenhum.
- Telas (host e cliente remoto): placar "VOCE: n/3 VITORIAS" no topo, "N vit."
  nos assentos, texto de resultado sem fichas. Mudou também o estado enviado
  pela rede (`vitorias` no lugar de `stack`/`eliminado`; saíram `vira` e
  `coringa_valor`).

### Joker impresso (opcional)
Criado como alternativa à vira. O Joker é uma carta própria
(`naipe="coringa"`, via `deck.NAIPE_CORINGA`/`VALOR_CORINGA`), e
`criar_baralho_duplo(usar_joker=...)` o inclui. Um Joker solto vale 20 pontos.

### Correção — bater descartando a carta que sobra
Bug real: a primeira versão só reconhecia a batida quando as **10 cartas**
(antes de descartar) fechavam sozinhas, o caso raro. O jeito normal de fechar
uma mão é comprar e descartar a última sobra, e isso só passava a vez. Agora o
descarte que deixa as 9 cartas restantes 100% combinadas **é** a batida
(`pode_bater_descartando`/`bater_descartando`). Numa simulação de 300 mãos só
com bots, 78% das vitórias passaram a vir desse caminho (antes, 0%).

### Regra "Mão Fechada"
Adicionada ao investigar uma mão real de 9 cartas já fechada na distribuição,
que ficava presa porque a compra obrigatória quase sempre quebrava a
combinação (só 15-20% das cartas do baralho servem para estender uma mão
fechada). Implementada em `pode_bater_mao_fechada`/`bater_mao_fechada`, com o
controle "já agiu nesta mão" em `jogadores_ja_agiram_na_mao`.

### Versão inicial (V1)
Modo completo e jogável contra bots, com a tela de escolha de modo. Testado por
simulação (bots jogando sozinhos, várias sementes, 2 a 8 jogadores) e por
renderização de todas as telas. Bugs achados e corrigidos na época: a
distribuição dava 3 cartas em vez de 9; um ciclo infinito de compra/descarte
quando a heurística de compra do bot divergia do critério de descarte; e um
crash ao desenhar a mão sem carta selecionada (`Card.__eq__` não tratava
comparação com `None`, corrigido em `core/deck.py`).

## Pesquisa das regras tradicionais

Resumo do que se levantou antes de implementar (o jogo tradicional tem
variações regionais):

- Dois baralhos de 52, de 3 a 8 jogadores, 9 cartas cada.
- Variantes mais ricas viram uma carta ("vira") e tornam coringa a de valor
  seguinte; outras regiões jogam sem coringa. Este projeto não usa a vira.
- **"A louca":** em algumas variantes qualquer jogador aproveita o descarte
  alheio, fora da vez, para bater na hora.
- Quem declara uma batida errada recolhe as cartas e só pode comprar do monte
  pelo resto da mão (regra não implementada: o jogo só deixa bater quando é
  válido).

**Fontes:**
- [Pif-Paf — Blog Copag](https://blog.copag.com.br/regras/pifpaf)
- [Pif Paf: saiba como jogar — Copag](https://blog.copag.com.br/curiosidades/pif-paf-saiba-como-jogar-e-conheca-as-principais-regras)
- [Regras do Pif Paf — Copag Loja](https://www.copagloja.com.br/regras-jogos/pif-paf)
- [Pif Paf regras completas — Supercacheta](https://supercacheta.com.br/pif-paf/pif-paf-regras-completas/)
- [Como Jogar Pife e Pafe — Mundo Tabuleiro](https://mundotabuleiro.com/como-jogar-pife-e-pafe/)

## Backlog do modo
- Regra da "a louca".
- Personalidades de bot por partida (hoje é uma heurística fixa).
- Conferir em jogo real o placar de vitórias, a tela de fim de jogo e se 3
  vitórias é o limite certo (ver `lista_tarefas.md`).
