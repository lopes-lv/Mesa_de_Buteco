# Backlog de Melhorias do Projeto

Este documento armazena todas as ideias, melhorias e novas funcionalidades planejadas para o futuro do jogo.

## 1. Melhorar o Design Geral do Jogo (Concluído — Neobrutalismo Suave)
- [x] Estética "Neobrutalismo Suave / Dashboard Analítico" validada antes da implementação através de guias técnicos e mockups HTML (ver item 6) e depois aplicada a todas as telas do jogo (Menu, Configuração, Mesa) via `ui_theme.py`, substituindo a pixel art.
- [x] Mesa retangular arredondada, cartas maiores e legíveis na mão do jogador, bots com painel próprio (avatar, nome, saldo e status: "Pensando...", "Fold", "All-in").
- [x] Painel de **histórico de ações da rodada**, fixo no canto inferior direito da mesa.
- [x] Atalhos de teclado reais para as ações (`F` Fold, `C` Check/Call, `R` Raise, `Enter` confirmar), com os selos visuais correspondentes nos botões.
- [ ] Pendente: revisar o layout em janelas muito pequenas com 8 jogadores na mesa (um selo SB/BB pode encostar na borda superior da tela nesse caso extremo).

## 2. Sistema de Seleção de Baralhos (Reimplementado no motor vetorial)
- [x] ~~Menu de configuração com Pixel Art / Clássico / Dark Mode~~ — implementado na era pixel art, descontinuado na migração pro Neobrutalismo Suave (sistema de sprites `ui_pixelart.py` + `assets/assets.png`, mantido só como referência).
- [x] Seletor de skin de baralho reimplementado dentro do sistema vetorial atual: `Ajustes` ganhou uma linha "Baralho" (ciclo Padrão/Dark, `settings.ciclar_baralho_skin()`), sincronizada globalmente via `ui_theme.set_estilo_baralho()` (mesmo padrão de global usado no antigo `ui_pixelart.py`, agora sem sprites). Vale pros dois modos (Hold'em e Pif Paf), já que é uma opção visual de sessão, não de partida.
- [ ] Pendente: mais skins além de Padrão/Dark (ex.: um terceiro estilo neobrutalista com outra paleta de acento).

## 3. Ajustes no Desenho do Baralho Atual
- [ ] Refinar a carta neobrutalista atual (`desenhar_carta` em `ui_theme.py`): naipes, tipografia dos números e verso da carta.

## 4. Ferramenta de Criação de Baralhos (Modo Admin/Editor)
- [ ] Criar uma seção especial (voltada para o administrador ou criador).
- [ ] Permitir a criação de novos designs de cartas de forma visual ou guiada.
- [ ] Possibilidade de "montar" e salvar um baralho personalizado a partir dos assets criados para ser usado no jogo.

## 5. Novos Modos de Jogo
- [x] Expandir além do Texas Hold'em — tela de escolha de modo adicionada
  (`ModeSelectScreen` em `screens.py`), reaproveitando o conceito "Ativo/Em
  breve" dos mockups em `design/*/mockup.html`.
- [x] Implementar o modo de jogo **Pif Paf** — ver
  [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md) (`pifpaf_logic.py`, `pifpaf_bot_ai.py`,
  `pifpaf_screen.py`). A regra da "a louca" ficou de fora desta primeira
  versão (backlog).
- [x] Implementar o modo de jogo **Dominó** — bloqueio/compra livre-pra-todos
  (sem duplas), duplo-seis, 2 a 4 jogadores (`domino_logic.py`,
  `domino_bot_ai.py`, `domino_theme.py`, `domino_screen.py`). Comprar/passar
  não são ações do jogador — acontecem sozinhos quando não há jogada
  possível; o único gesto é clicar numa peça jogável e, se ela encaixar nas
  duas pontas, escolher qual lado. Já nasceu com multiplayer local (ver
  seção 7), diferente do Pif Paf que começou solo.
- [ ] Implementar e projetar um modo de jogo inédito/diferente — já existe
  um card "EM BREVE" reservado para ele na tela de escolha de modo.
- [x] Pif Paf: adicionada a regra tradicional de **"Mão Fechada"** (bater
  sem comprar, pagando o dobro, quando a mão já vem pronta na distribuição)
  — ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md#21-atualização-regra-mão-fechada-bater-sem-comprar).
  Sem essa regra, uma mão perfeita na distribuição ficava presa: a compra
  obrigatória a cada turno quase sempre quebrava a combinação de novo.
- [x] Pif Paf: corrigido bug real em que **bater descartando a carta que
  sobra** (o jeito normal de vencer nesse tipo de jogo) não era reconhecido
  — só valia bate se as 10 cartas já fechassem sozinhas, antes de descartar,
  o que é raro. Ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md#22-correção-bater-descartando-a-carta-que-sobra).
  Confirmado por simulação: 78% das vitórias passaram a vir desse caminho.
- [x] Pif Paf: corrigido o texto de "Comprar Monte"/"Comprar Descarte"
  ficando cortado pelo selo de atalho de teclado (botões estreitos demais
  para o texto); botões alargados em `pifpaf_screen.py`.

## 6. Ajustes de UI (Mesa e Menu)
- [x] Menu Inicial: adicionado botão "Configurações" (tela `SettingsScreen`
  em `screens.py`, ver `settings.py`) com ajustes básicos que valem para a
  próxima partida: tela cheia, velocidade dos bots, fichas iniciais e
  exibição dos atalhos de teclado.
- [x] Mesa (Hold'em): cartas da mão do jogador humano subidas
  (`DESLOCAMENTO_CARTAS_HUMANO` em `table_screen.py`) para não ficarem atrás
  dos botões Fold/Call/Raise em janelas menores; espaçamento real adicionado
  entre esses três botões (antes praticamente colados).

## 7. Multiplayer Local (Rede)
- [x] Implementado conforme o plano em [MULTIPLAYER_PLANO.md](MULTIPLAYER_PLANO.md):
  anfitrião cria sala (`AnfitriaoSala` em `rede/anfitriao.py`) e recebe um
  código curto (`rede/descoberta.py`), outros jogadores na mesma rede local
  entram com esse código (`ClienteSala` em `rede/cliente.py`) via descoberta
  UDP broadcast ou IP:porta manual como fallback. Arquitetura
  host-autoritativo: o host roda o `Table` de verdade (`table_screen.py`
  ganhou `sala_rede`, serialização de estado público e validação de ações
  remotas), clientes rodam `MesaRemotaScreen` (`mesa_remota_screen.py`) e só
  recebem snapshots + a própria mão, nunca as cartas alheias. Telas de sala
  em `multiplayer_screens.py` (`CriarSalaScreen`, `EntrarSalaScreen`,
  `LobbyScreen`), acessíveis por `ConfigScreen` → "Multiplayer Local".
- [x] Robustez básica (Fase 6 do plano): sala cheia recusa entrada,
  desconexão no meio de uma mão vira fold automático (`sala_rede.desconectados`,
  status "Desconectado" no painel do jogador), host fechar a sala avisa os
  clientes (`sala_encerrada`) que voltam ao menu.
- [x] Testado com automação (thread+socket real em `127.0.0.1`, sem UI):
  handshake completo, sala cheia, desconexão, broadcast de estado, e uma
  partida real de 2+ mãos entre um host local e um cliente de rede,
  confirmando que o snapshot público nunca inclui as cartas de ninguém.
- [x] **Código de sala simplificado**: de 5 caracteres com prefixo
  (`PIF-XXXXX`) para **3 letras + 1 número** (ex.: `KTR4`).
- [x] **Chat de texto** em toda sessão multiplayer (lobby + as duas mesas):
  aba no canto esquerdo da tela (`chat_widget.py`, `ChatWidget`), relay
  automático na camada de rede (`AnfitriaoSala`, tipo `CHAT`) — nenhuma tela
  duplica a lógica de "quem mandou pra quem". Ver
  [MULTIPLAYER_PLANO.md §11](MULTIPLAYER_PLANO.md#11-pif-paf-multiplayer-e-chat-de-texto).
- [x] **Multiplayer no Pif Paf**: mesmo host-autoritativo do Hold'em, com
  `PifPafPlayer.tipo` novo e `mesa_remota_pifpaf_screen.py`. Particularidade
  resolvida: a mão muda a cada compra/descarte (não só no fold como no
  Hold'em), então a tela remota reconcilia a mão nova preservando a
  organização manual do jogador em vez de substituir a lista inteira; um
  jogador remoto desconectado continua jogando sozinho via a IA de bots
  (não existe "fold" no Pif Paf para cobrir esse caso). Ver
  [MULTIPLAYER_PLANO.md §11](MULTIPLAYER_PLANO.md#11-pif-paf-multiplayer-e-chat-de-texto)
  para os detalhes técnicos.
- [x] **Multiplayer no Dominó**: já nasceu com rede (não foi retrofit como
  Pif Paf) — `DominoPlayer.tipo`, `domino_screen.py` (host) e
  `mesa_remota_domino_screen.py` (cliente). Como comprar/passar são
  automáticos (não são decisão de ninguém), o protocolo só precisa de uma
  ação de rede (`jogar`); a checagem de "essa peça é jogável?" roda igual
  dos dois lados via `domino_logic.jogadas_possiveis_em()`, uma função pura
  sobre a própria mão + as extremidades da mesa (públicas). Sala limitada a
  4 jogadores (`MAX_JOGADORES_POR_JOGO` em `multiplayer_screens.py`), já que
  o jogo duplo-seis não comporta mais que isso. Testado com automação
  (rede real): limite de 4 respeitado (5º recusado), chat na mesa, e uma
  partida real de 3+ mãos sem vazar a mão de ninguém no estado público.
- [ ] Pendente (fora do escopo, ver seção 9 do plano): teste manual com
  duas máquinas físicas na mesma Wi-Fi (só validado via `127.0.0.1` e
  automação até agora — falta confirmar o aviso de firewall do Windows e a
  descoberta UDP numa LAN real); reconexão após queda; chat de voz; revelar
  as cartas de todos no showdown/liquidação para os clientes remotos (hoje
  só o host vê as mãos reveladas — os clientes só veem o texto do resultado).

## 8. Documentação do Projeto
- [x] Escrever um **GDD (Game Design Document)** para consolidar todas as mecânicas, regras e visão do jogo em um único lugar (`GDD.md`).
- [x] Escrever um **Guia de Estilo** com as diretrizes visuais do projeto: em `design/`, foram criados guias técnicos (paleta, tipografia, dimensões e instruções de renderização em Pygame) e mockups HTML interativos para 3 das 5 estéticas propostas antes da migração:
  - `design/01_neobrutalismo_suave/` — **aplicada ao jogo** (ver item 1).
  - `design/03_casino_minimalista/` — validada em mockup, não implementada em Pygame.
  - `design/05_cozy_flat/` — validada em mockup, não implementada em Pygame.
- [ ] Pendente: os outros 2 estilos cogitados inicialmente (Dark Glassmorphism/Desktop Client Moderno e Terminal Tático/Sci-Fi Minimal) ainda não têm guia nem mockup, caso um dia se queira comparar mais opções.

---
*Atualizado conforme surgirem novas ideias.*
