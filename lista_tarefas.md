---
estado: em andamento
proximo_passo: Jogar uma partida de verdade (não headless) nos 3 modos pra validar a estética Pixel Art Retrô CRT na prática (hover, drag-and-drop do Dominó, showdown, lobby multiplayer) e também as 10 skins de baralho no novo seletor de setas da tela de Configuração, e ajustar o que incomodar
bloqueios:
---
# poker_game

**Objetivo:** Texas Hold'em, Pif Paf e Dominó em Python + Pygame, solo contra bots ou multiplayer local, com estética "Pixel Art Retrô CRT".

## Tarefas
- [ ] Revisão visual manual do redesign Pixel Art Retrô CRT: só foi validado por render headless (telas estáticas); falta rodar `python main.py` de verdade e conferir hover/clique dos botões, o slider de raise, o drag-and-drop do Dominó, o skin "Dark" do baralho e as 8 skins novas no seletor de setas da tela de Configuração (nenhuma recapturada em uso real)
- [ ] Espectador de Hold'em: testar o modo espectador em partida multiplayer real (só validado por render headless do host)
- [ ] Design Geral: revisar o layout em janelas muito pequenas com 8 jogadores na mesa (selo SB/BB pode encostar na borda superior nesse caso extremo)
- [ ] Desenho do Baralho: refinar a carta "padrão"/"Dark" (`desenhar_carta` em `ui_theme.py`) — naipes, tipografia dos números, verso da carta
- [ ] Ferramenta de Criação de Baralhos (modo admin/editor): seção para criar e salvar baralhos personalizados de forma visual/guiada
- [ ] Novos Modos de Jogo: implementar um modo inédito (já existe card "EM BREVE" reservado na tela de escolha de modo)
- [ ] Multiplayer Local: testar com duas máquinas físicas reais na mesma Wi-Fi (só validado via 127.0.0.1 até agora); reconexão após queda; chat de voz; revelar cartas de todos no showdown para os clientes remotos
- [ ] Documentação: criar guia + mockup para os 2 estilos visuais ainda não explorados (Dark Glassmorphism e Terminal Tático/Sci-Fi Minimal)

## Concluído
- [x] Redesign da estética: `core/ui_theme.py` reimplementado do zero no estilo "Pixel Art Retrô CRT" (era "Neobrutalismo Suave") — cantos retos, bordas grossas, sombra sólida maior, paleta escura tipo tela de CRT (fundo azul-marinho, feltro verde-azulado, acentos dourado/verde/azul/vermelho/roxo saturados), fonte monoespaçada, avatares quadrados (eram círculos), texto de botão/tecla em caixa alta, overlay sutil de scanlines por cima de tudo (`ui_theme.aplicar_scanlines`, chamado em `main.py`). `domino_theme.py` (peças) e todas as telas (`menus/`, `holdem/`, `pifpaf/`, `domino/`, `core/chat_widget.py`, `core/ui_widgets.py`) foram ajustadas junto: contraste de texto sobre os novos fundos claros/escuros revisado call a call (fundo amarelo/verde passou a usar texto escuro; vermelho/azul/roxo, texto claro), feltro do Dominó (era bege, virou o mesmo verde-azulado dos outros modos), ícone do Dominó na escolha de modo (era um glifo Unicode quebrado, virou uma peça desenhada), acento que faltava em "CONFIGURAÇÃO DA MESA". O baralho "Padrão" nasceu pixel art; "Dark" segue como opção alternativa. Referência: `design/07_pixel_retro_crt/mockup.html`
- [x] **8 baralhos novos integrados** a partir de `design/baralhos/` (`GUIA_BARALHOS.md`): `design/baralhos/baralhos_skins.py` copiado para `core/baralhos_skins.py` (dados `SKINS` + desenhista `desenhar_carta_skin`, só `pygame.draw`); `core/settings.py` registra os 8 ids/rótulos (`ORDEM_BARALHO_SKINS`/`ROTULOS_BARALHO_SKIN` passam a ter 10 entradas: `padrao`, `dark` + `dark_glass`, `terminal`, `art_deco`, `pixel_crt`, `synthwave`, `papel_vintage`, `editorial`, `zen`); `ui_theme.desenhar_carta` desvia para `baralhos_skins.desenhar_carta_skin` quando a skin ativa é uma das 8 novas (os dois baralhos originais continuam no código vetorial atual); nova `ui_theme.desenhar_carta_vazia` cobre também o slot tracejado das comunitárias do Hold'em ainda não reveladas (antes um retângulo branco fixo em `table_screen.py`/`mesa_remota_screen.py`), coerente com a skin ativa. `settings.ciclar_baralho_skin()` ganhou parâmetro `direcao` (`1`/`-1`) para suportar avançar/voltar.
- [x] **Seletor de baralho na tela de Configuração**: setas `<`/`>` ladeando a prévia da carta em `ConfigScreen` (`menus/screens.py`), antes de "Iniciar Partida" — visíveis nos modos com cartas (Hold'em/Pif Paf; não aparecem no Dominó, cuja prévia é a peça). O botão de ciclar em Ajustes continua funcionando como atalho alternativo. Testado só por smoke test headless (compile + ciclo completo das 10 skins sem erro) — falta validação visual manual real, ver tarefa pendente acima.
- [x] Mesa de Hold'em oval com recorte; croupiê vira uma pessoa em pé no recorte (só o topo da cabeça visível); quem dá fold ou fica sem fichas vira espectador e vê as cartas de todos (host e clientes remotos)
- [x] Melhorar o Design Geral do Jogo (estética Neobrutalismo Suave aplicada a Menu, Configuração e Mesa) — substituída depois pelo Pixel Art Retrô CRT, ver item acima
- [x] Sistema de Seleção de Baralhos reimplementado no motor vetorial (Padrão/Dark)
- [x] Novos Modos de Jogo: Pif Paf e Dominó implementados, com multiplayer local nos três modos
- [x] Ajustes de UI (Mesa e Menu) e correção do bug grave do Esc fechando o jogo em qualquer tela
- [x] Multiplayer Local (Rede): salas host-autoritativo, descoberta UDP, chat de texto, robustez básica (sala cheia, desconexão, encerramento)
- [x] Documentação do Projeto: GDD.md, guias técnicos e mockups HTML das estéticas visuais

## Notas
Histórico completo (decisões técnicas, bugs corrigidos e o racional de cada mudança) preservado em `GDD.md`, `MULTIPLAYER_PLANO.md`, `PIF_PAF_GUIA.md` e `NOTAS_ATUALIZACAO_DOMINO.md` — este arquivo é só o resumo de estado/tarefas para o painel.
