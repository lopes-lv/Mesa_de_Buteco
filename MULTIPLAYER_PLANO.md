# Plano — Multiplayer Local (Rede) com Código de Sala

Este documento é um **plano de arquitetura**, não uma implementação. Descreve
como adicionar um modo onde um jogador cria uma sala (fica "anfitrião"/host),
recebe um código curto, e outras pessoas na mesma rede local (Wi-Fi/LAN)
digitam esse código para entrar na mesma mesa — cada pessoa no seu próprio PC,
rodando sua própria cópia do jogo.

> Escopo: **rede local (LAN)**, não internet. Não há servidor externo,
> matchmaking online, nem NAT traversal — só descoberta na mesma rede.

## 1. Decisão de arquitetura: Host Autoritativo

A melhor opção para este projeto é **host-autoritativo**: a pessoa que cria a
sala roda o `Table`/`PifPafTable` de verdade (as mesmas classes que já
existem em `game_logic.py`/`pifpaf_logic.py`), exatamente como no modo solo
contra bots. Os outros jogadores conectados são "telas burras": só recebem o
estado da mesa e mandam de volta a ação escolhida quando é a vez deles.

Por que essa opção e não peer-to-peer (todo mundo roda a lógica e sincroniza
entre si):
- `game_logic.py` já é uma máquina de estados pura e centralizada (`Player`,
  `BettingRound`, `Table`) — ela **não sabe e não precisa saber** se uma ação
  veio do mouse do jogador local, de `bot_ai.decidir_acao_bot`, ou de um
  pacote de rede. Isso já foi validado no smoke test: qualquer ação passa
  por `rodada_atual.aplicar_acao(jogador, acao, valor)`.
- Evita o problema mais difícil de multiplayer (sincronizar estado
  divergente entre várias cópias da lógica); só uma cópia da verdade existe
  (a do host).
- É o único lugar seguro para esconder as cartas dos outros jogadores — ver
  seção 6 (Segurança).

Trade-off aceito: se o host cair, a sala cai junto (sem host migration).
Aceitável para v1 — ver seção 9.

## 2. Novo fluxo de telas (UX)

```
MenuScreen
  └─ Jogar → ModeSelectScreen (Hold'em / Pif Paf / ...)
       └─ ConfigScreen (modo escolhido)
            ├─ "Solo vs Bots"        (fluxo atual, inalterado)
            └─ "Multiplayer Local"   (NOVO)
                 ├─ Criar Sala  → CriarSalaScreen  → LobbyScreen (host)
                 └─ Entrar em Sala → EntrarSalaScreen → LobbyScreen (cliente)
```

- **CriarSalaScreen**: pede o nome do jogador, ao confirmar sobe o
  `AnfitriaoSala` (host), gera o código e mostra:
  - Código grande (ex.: `KTR4`), em destaque, fácil de ditar em voz alta.
  - IP local + porta como *fallback* (ver seção 4).
  - Lista ao vivo de quem já entrou (nome + "pronto").
  - Opção "completar vagas restantes com bots" (reaproveita `NOMES_BOTS` do
    `main.py`) — assim a sala não fica travada esperando gente.
  - Botão "Iniciar Partida" (habilitado com 2+ participantes no total).
- **EntrarSalaScreen**: campo de texto para o código (ou IP:porta manual),
  nome do jogador, botão "Conectar". Estados: conectando / erro (código
  inválido, sala cheia, sala já em jogo, host não encontrado).
- **LobbyScreen**: comum a host e clientes, mostra a lista de jogadores e
  aguarda o host apertar "Iniciar". Ao iniciar, cada tela transiciona para a
  tela de mesa correspondente (host → `TableScreen` normal; clientes → nova
  `MesaRemotaScreen`, seção 5).

Essas telas seguem o mesmo estilo visual (`ui_theme.py`: `desenhar_painel`,
`desenhar_botao`, `desenhar_badge`) já usado em `screens.py`.

## 3. Geração e descoberta do código de sala

1. **Código**: 3 letras + 1 número maiúsculos (ex.: `KTR4`), sem caracteres
   ambíguos (sem `O`/`0`, `I`/`1`), gerado pelo host ao criar a sala
   (`rede/descoberta.py:gerar_codigo()`). Curto o bastante para ser
   falado/digitado em voz alta entre pessoas na mesma sala física.
2. **Descoberta automática (caminho feliz)**: o host, além do socket TCP de
   jogo, abre um socket **UDP** escutando numa porta fixa
   (ex.: `52999`). Quando alguém digita um código em `EntrarSalaScreen`, o
   jogo manda um **broadcast UDP** na rede local perguntando
   `{"tipo": "procurar_sala", "codigo": "KTR4"}`. Todo host escutando
   aquele código responde (unicast, direto pro IP de quem perguntou) com
   `{"tipo": "sala_encontrada", "ip": "...", "porta_tcp": ..., "anfitriao": "..."}`.
   O cliente então conecta via TCP nesse IP/porta.
3. **Fallback manual**: nem toda rede permite broadcast UDP (redes
   corporativas, alguns roteadores/isolamento de clientes Wi-Fi). Por isso a
   tela do host **sempre mostra o IP local + porta** também. Se a descoberta
   automática falhar (timeout de ~3s sem resposta), `EntrarSalaScreen` deixa
   o usuário digitar IP:porta diretamente — o código deixa de ser
   obrigatório, é só um atalho.
4. **Firewall do Windows**: na primeira vez que o host abre um socket de
   escuta, o Windows normalmente mostra um popup pedindo permissão de rede
   para o `.exe`/`python.exe`. Isso precisa ser documentado no README para o
   usuário não achar que travou.

## 4. Protocolo de mensagens

- Transporte de jogo: **TCP** (uma conexão por cliente, confiável e
  ordenada — importante para não perder/trocar a ordem de ações).
- Framing: cada mensagem é um JSON serializado, prefixado por 4 bytes
  (big-endian) com o tamanho em bytes do JSON que vem a seguir. Isso evita
  o problema clássico de "onde termina uma mensagem e começa a próxima" em
  um stream TCP, sem depender de o JSON nunca conter `\n`.
- Tipos de mensagem (campo `"tipo"` em cada JSON):

  | Direção | Tipo | Conteúdo | Quando |
  |---|---|---|---|
  | cliente → host | `entrar` | `{nome}` | logo após conectar |
  | host → cliente | `entrada_ok` | `{seu_id, jogadores[]}` | aceita a entrada |
  | host → cliente | `recusado` | `{motivo}` | sala cheia / já em jogo |
  | host → todos | `lobby_atualizado` | `{jogadores[]}` | alguém entrou/saiu no lobby |
  | host → todos | `estado` | snapshot público da mesa (ver abaixo) | após qualquer ação, a cada estágio |
  | host → 1 cliente | `sua_mao` | `{cartas: [...]}` | **só** para o dono da mão, nunca broadcast |
  | cliente → host | `acao` | `{acao, valor}` (fold/check/call/raise) | quando é a vez dele |
  | host → todos | `erro_acao` | `{motivo}` | ação chegou fora de hora / inválida |
  | qualquer → outro lado | `sair` | — | saída voluntária |
  | host → todos | `fim_de_jogo` | `{vencedor}` | torneio acabou |

- **Snapshot de `estado`** é público (não contém as cartas de ninguém, exceto
  no showdown): mão atual, blinds, estágio, cartas comunitárias, pote, lista
  de jogadores com `{id, nome, stack, aposta_rodada, foldou, all_in,
  eliminado}`, de quem é a vez, e as últimas linhas do histórico. É
  essencialmente uma serialização do que `TableScreen._desenhar_*` já lê de
  `self.table` hoje — o trabalho aqui é **extrair isso pra um dict**, não
  reinventar o que mostrar.

## 5. Modelo de concorrência (threads + fila)

Sockets em Python bloqueiam; o loop do Pygame roda a 60 FPS num único
thread e não pode travar esperando rede. Solução (mesmo padrão que o jogo já
usa para o "delay" dos bots, só que com filas em vez de um timer):

- `AnfitriaoSala` (host):
  - 1 thread aceitando novas conexões TCP.
  - 1 thread de leitura por cliente conectado, cada uma empurrando as
    mensagens recebidas numa `queue.Queue` compartilhada
    (`mensagens_entrantes`).
  - 1 thread UDP respondendo aos broadcasts de descoberta.
  - Envio (`enviar_para_todos`/`enviar_para`) acontece nas threads de
    escrita dedicadas (uma fila de saída por cliente) para nunca bloquear o
    thread principal do jogo esperando um cliente lento/travado responder.
- `ClienteSala` (cliente): 1 thread de leitura da conexão TCP, empurrando
  pra uma `queue.Queue` própria; escrita de ações (raras, pequenas) também
  por fila+thread dedicada, por simetria e segurança.
- Em ambos os casos, o loop do jogo (`TableScreen.atualizar` no host,
  `MesaRemotaScreen.atualizar` no cliente) só faz `queue.get_nowait()` em
  loop a cada frame — nunca bloqueia, exatamente como hoje `timer_bot`
  é checado a cada `atualizar(dt)`.

## 6. Segurança e validação (o ponto mais importante)

- **Nunca enviar as cartas de um jogador para os demais.** A mensagem
  `sua_mao` vai só pelo socket daquele cliente específico. Isso é o motivo
  pelo qual "host autoritativo" foi escolhido em vez de sincronizar um
  estado global compartilhado ingenuamente.
- O host **revalida toda ação recebida** antes de aplicar: confere se
  `jogador_id` bate com quem realmente é `rodada_atual.jogador_da_vez()`, se
  a ação é uma das permitidas (ex.: não deixar "check" quando há aposta a
  pagar) e se o valor de raise é válido — a mesma validação que hoje existe
  implicitamente na UI (`table_screen.py`, ao decidir se mostra o botão
  ativo) precisa ser explícita no host, porque um cliente malicioso ou com
  bug pode mandar qualquer coisa. Um `acao` inválida gera `erro_acao` de
  volta, sem aplicar nada.
- Nenhum dado sensível do usuário trafega (só nome, escolhido livremente,
  sem contas/login).

## 7. Mudanças necessárias no código existente

Mapeado arquivo por arquivo, para deixar claro o tamanho do trabalho:

- **`game_logic.py` / `pifpaf_logic.py`**: `Player`/`PifPafPlayer` ganham um
  jeito de diferenciar "bot" vs "humano local" vs "humano remoto" (hoje só
  existe `is_bot`). O mais simples é trocar por um campo `tipo` com os três
  valores — `BettingRound`/`Table` continuam nem olhando pra isso, só quem
  desenha e quem decide a origem da próxima ação (bot_ai vs mouse vs rede)
  usa esse campo.
- **`table_screen.py`**:
  - Extrair um método `_serializar_estado()` que devolve o dict público
    descrito na seção 4 (reaproveitando os mesmos campos que os métodos
    `_desenhar_*` já leem).
  - Generalizar `_aplicar_acao_humano(acao, valor)` para aceitar **qual**
    jogador está agindo (hoje é hardcoded pro humano local), pra poder
    aplicar ações que chegaram de um cliente de rede pelo mesmo caminho.
  - Em `atualizar(dt)`, quando `self.sala_rede` existir (só no host), além
    de checar bots, drenar `sala_rede.mensagens_entrantes` e tratar
    mensagens `acao`; depois de qualquer mudança de estado, chamar
    `sala_rede.enviar_para_todos({"tipo": "estado", ...})`.
  - Quando não há sala de rede (`self.sala_rede is None`), nada muda — é o
    modo solo de hoje, comportamento idêntico.
- **Nova `mesa_remota_screen.py`** (`MesaRemotaScreen`): tela "cliente".
  Não roda `Table` nenhuma — guarda o último snapshot de `estado` recebido e
  as próprias `cartas` recebidas via `sua_mao`. Reaproveita ao máximo as
  funções de desenho de `ui_theme.py` (o ideal é fatorar os métodos de
  desenho de jogadores/mesa/pote de `TableScreen` para aceitarem um "view
  model" simples em vez de ler `self.table` diretamente, e assim serem
  compartilhados entre `TableScreen` e `MesaRemotaScreen" — evita duplicar
  a parte visual). Quando é a vez do jogador local (segundo o snapshot),
  mostra os botões Fold/Call/Raise normalmente; ao clicar, manda `acao` pro
  host em vez de chamar `table.aplicar_acao` diretamente.
- **Novo pacote `rede/`**: `protocolo.py` (framing + constantes de tipo),
  `descoberta.py` (broadcast/response UDP + geração de código),
  `anfitriao.py` (`AnfitriaoSala`), `cliente.py` (`ClienteSala`).
- **Nova `multiplayer_screens.py`**: `CriarSalaScreen`, `EntrarSalaScreen`,
  `LobbyScreen` (seção 2).
- **`main.py`**: novos métodos `ir_para_multiplayer_criar()`,
  `ir_para_multiplayer_entrar()`, `iniciar_partida_como_anfitriao(sala, ...)`,
  `iniciar_partida_como_cliente(sala, ...)`.
- **`screens.py` (`ConfigScreen`)**: adicionar a escolha "Solo vs Bots" /
  "Multiplayer Local" antes do botão "Iniciar Partida" atual.

## 8. Casos de borda e robustez (v1)

- **Sala cheia**: host define um máximo (mesmo limite de 8 jogadores que já
  existe hoje); host responde `recusado` com motivo.
- **Jogador desconecta no meio de uma mão**: host detecta (erro de leitura
  no socket ou timeout de heartbeat) e trata como fold automático nas
  próximas vezes que for a vez dele, marcando `"Desconectado"` no painel
  (reaproveita o mesmo visual já usado para `"Eliminado"`/`"Fold"`).
- **Host fecha o jogo**: clientes recebem erro de conexão, voltam ao
  `MenuScreen` com uma mensagem "Sala encerrada pelo anfitrião".
- **Reconexão** (voltar pra mesma sala após cair): fica de fora do v1, vira
  item de backlog — exigiria guardar estado por jogador mesmo após
  desconectar e um jeito de reidentificar quem está voltando.

## 9. Fora do escopo desta primeira versão

- Jogar pela internet (isso exigiria um servidor relay/matchmaking e lidar
  com NAT — bem mais complexo que o pedido, que é "multiplayer local").
- Chat de voz, espectadores, host migration, reconexão. (Chat de **texto**
  foi implementado — ver seção 11.)
- ~~Multiplayer no Pif Paf~~ — implementado (ver seção 11): a arquitetura de
  rede era a mesma do Hold'em, só precisou de `tipo` em `PifPafPlayer`,
  serialização de estado equivalente e uma tela remota própria
  (`mesa_remota_pifpaf_screen.py`), já que `PifPafTable` muda de mão a cada
  compra/descarte (diferente do Hold'em, onde a mão só muda no fold).
- Revelar as cartas de todos no showdown/liquidação para os clientes remotos
  — hoje eles só veem o texto do resultado (vencedores, pote, categoria/
  pontos), não as cartas reveladas; o host continua vendo tudo normalmente.

## 10. Roteiro de implementação sugerido (fases)

- [x] **Fase 1 — Fundação de rede**: pacote `rede/` (protocolo, framing,
      `AnfitriaoSala`/`ClienteSala` com threads+filas), testado com um
      script simples de eco (sem UI ainda).
- [x] **Fase 2 — Descoberta e telas de sala**: geração de código,
      broadcast/response UDP, `CriarSalaScreen`/`EntrarSalaScreen`/
      `LobbyScreen`, fallback manual por IP.
- [x] **Fase 3 — Adaptar o motor de Hold'em**: campo `tipo` no `Player`,
      generalizar aplicação de ação por jogador, serialização de estado.
- [x] **Fase 4 — Mesa do lado do host**: `TableScreen` broadcasta estado a
      cada mudança e aceita ações vindas da fila de rede.
- [x] **Fase 5 — Mesa do lado do cliente**: `MesaRemotaScreen` renderizando
      snapshots e mandando ações. Reaproveita as primitivas de desenho de
      `ui_theme.py`, mas com sua própria lógica de layout (não uma extração
      literal dos métodos de `TableScreen`, que continuam acoplados a
      `self.table`) — suficiente pra ficar visualmente consistente sem um
      refactor maior de `table_screen.py`.
- [x] **Fase 6 — Robustez**: desconexão vira fold automático + "Desconectado"
      no painel, sala cheia recusa entrada, host encerrar a sala avisa os
      clientes. Timeout de heartbeat explícito (distinguir "devagar" de
      "caiu") ficou de fora do v1 — hoje a queda só é percebida quando o
      socket TCP realmente fecha.
- [~] **Fase 7 — Testes**: validado via automação (host real + cliente real
      por `127.0.0.1`, incluindo uma partida completa de várias mãos sem
      vazar cartas no estado público) — ver `MELHORIAS.md`, seção 7. Ainda
      falta o teste manual com 2 PCs físicos na mesma rede Wi-Fi (só isso
      valida de fato a descoberta UDP e o aviso de firewall do Windows).

## 11. Pif Paf multiplayer e chat de texto

Adicionados depois do v1 inicial (que só cobria Hold'em, sem chat):

- **Código de sala mais simples**: trocado de 5 caracteres com prefixo
  (`PIF-XXXXX`) para **3 letras + 1 número** (ex.: `KTR4`,
  `rede/descoberta.py:gerar_codigo()`), mais rápido de ditar/digitar.
- **Chat de texto** (`chat_widget.py`, classe `ChatWidget`): aba fixa no
  canto esquerdo da tela (fechada por padrão, com indicador "●" quando
  chegam mensagens novas), expande num painel com histórico + campo de
  texto. Presente na `LobbyScreen` e nas duas mesas (Hold'em e Pif Paf), dos
  dois lados (host e cliente). Protocolo novo: `CHAT` (`rede/protocolo.py`) —
  o **relay acontece na camada de rede** (`AnfitriaoSala._processar_mensagem`
  resolve o nome de quem mandou e reenvia pra todo mundo, inclusive de volta
  pra quem mandou), então nenhuma tela precisa duplicar essa lógica; o host
  só faz eco local quando é ele mesmo quem digita, já que não recebe suas
  próprias mensagens de volta pela rede. `CampoTexto` (usado no chat e nas
  telas de sala) foi extraído para `ui_widgets.py` para evitar import
  circular entre `chat_widget.py` e `multiplayer_screens.py`.
- **Multiplayer no Pif Paf**: mesmo padrão host-autoritativo do Hold'em,
  mas com uma diferença importante — no Pif Paf a mão do jogador muda a
  cada compra/descarte (não só no fold, como no Hold'em), então `sua_mao` é
  reenviada a cada `_broadcast_estado()`, e a tela remota
  (`mesa_remota_pifpaf_screen.py`) **reconcilia** a nova mão preservando a
  ordem que o jogador já tiver organizado manualmente (arrastar cartas é só
  cosmético/local) em vez de substituir a lista inteira a cada atualização.
  As checagens de "posso bater/mão fechada/bater descartando" são
  recalculadas do lado do cliente usando as mesmas funções puras de
  `pifpaf_logic.py` (`pode_bater_mao`) sobre a própria mão + o valor do
  coringa (que já é público via a carta vira) — evita ida-e-volta de rede a
  cada carta selecionada, sem duplicar a regra em si (a validação real,
  que decide o que de fato é aplicado, continua só no host, em
  `PifPafTableScreen._processar_acao_remota`). `PifPafPlayer` ganhou o mesmo
  campo `tipo` (`bot`/`humano_local`/`humano_remoto`) que `Player` do
  Hold'em, com `is_bot` como propriedade de compatibilidade.
- **Desconexão no Pif Paf**: como não existe "fold" nesse jogo, um jogador
  remoto desconectado no meio de uma mão continua jogando sozinho via a
  mesma IA de bots (`pifpaf_bot_ai.py`) até ser eliminado ou a mão acabar —
  em vez de travar a mesa esperando alguém que não vai mais responder.
- Testado com automação (rede real via `127.0.0.1`, sem UI): chat
  cliente→host→todos e host→todos, tanto na `LobbyScreen` quanto dentro das
  duas mesas; e uma partida real de Pif Paf multiplayer de várias mãos,
  confirmando que o estado público nunca inclui a mão de ninguém.

## 12. Multiplayer no Dominó

Diferente do Pif Paf (que ganhou rede depois, como retrofit), o Dominó já
nasceu com multiplayer local — mesmo padrão host-autoritativo, mas mais
simples de encaixar porque o próprio jogo tem menos "decisões":

- **Sem ação de comprar/passar na rede**: em Dominó, comprar do monte
  quando não se tem jogada (e passar, se o monte também secou) não são
  decisões do jogador — são automáticas. Por isso `DominoTableScreen.atualizar()`
  já resolve isso sozinho (pra bot, humano local ou humano remoto, sem
  diferença) *antes* de esperar por qualquer ação; a única mensagem que um
  cliente manda é `{"tipo": "acao_domino", "acao": "jogar", "peca": [a, b],
  "lado": "esquerda"|"direita"}`. Isso elimina uma classe inteira de mensagens
  de rede que os outros dois jogos precisam (`comprar`, `passar` nunca
  existem como tipo de mensagem).
- **Validação client-side sem duplicar regra**: para destacar quais peças da
  própria mão são jogáveis agora (e permitir escolher o lado quando uma peça
  encaixa nas duas pontas), o cliente chama
  `domino_logic.jogadas_possiveis_em(mao, extremidade_esquerda,
  extremidade_direita)` — a mesma função pura que `DominoTable` usa
  internamente, extraída pra ser chamável sem uma mesa de verdade. Isso é
  seguro porque as extremidades da mesa já são informação pública (todo
  mundo vê o tabuleiro); a decisão final de aplicar ou não continua só no
  host (`DominoTableScreen._processar_acao_remota`), que revalida tudo de
  novo contra o estado real (um cliente com uma cópia desatualizada da mesa
  — por exemplo, uma jogada que já não é mais válida porque outro jogador
  moveu antes da mensagem chegar — recebe `erro_acao` e simplesmente não
  aplica nada; isso é esperado, não é bug, e foi reproduzido e confirmado
  durante os testes automatizados).
- **Limite de 4 jogadores por sala**: diferente do limite de 8 usado no
  Hold'em/Pif Paf, uma sala de Dominó (`MAX_JOGADORES_POR_JOGO` em
  `multiplayer_screens.py`) aceita no máximo 4, porque o jogo duplo-seis (28
  peças, 7 por jogador) não sobra peça suficiente pra mais que isso.
- **Desconexão**: como não existe "fold" nem "mão fechada" em Dominó, um
  jogador remoto desconectado no meio de uma mão continua jogando sozinho
  via `domino_bot_ai.escolher_jogada_bot` (mesmo padrão do Pif Paf).
- Testado com automação (rede real via `127.0.0.1`): limite de 4 jogadores
  respeitado (5º recusado com "Sala cheia"), chat na `LobbyScreen` e dentro
  da mesa, e uma partida real de Dominó multiplayer de várias mãos —
  incluindo o caso de uma jogada rejeitada por estado desatualizado sendo
  corretamente recusada pelo host sem corromper o jogo.

## 13. Como testar sem precisar de duas máquinas

Durante o desenvolvimento, dá pra validar o essencial rodando **duas
instâncias do jogo no mesmo PC**: uma cria a sala, a outra entra digitando
`127.0.0.1` (localhost) como IP manual — o socket TCP funciona normalmente
entre dois processos na mesma máquina. Isso cobre protocolo, threads e
lógica de turnos sem depender de uma segunda máquina/rede Wi-Fi. O teste
"de verdade" com dois PCs fica pra validar a parte de descoberta UDP na
rede local (que não existe em `127.0.0.1` da mesma forma).

---
*Implementado (v1 Hold'em + Pif Paf/chat + Dominó, ver seções 10-12 e
`MELHORIAS.md` §7). Ver [GDD.md](GDD.md) e [MELHORIAS.md](MELHORIAS.md) para
o restante do backlog do projeto.*
