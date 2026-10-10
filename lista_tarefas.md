---
estado: em andamento
proximo_passo: Jogar uma partida de verdade (não headless) nos 3 modos pra validar a estética Pixel Art Retrô CRT na prática (hover, drag-and-drop do Dominó, showdown, lobby multiplayer) e ajustar o que incomodar
bloqueios:
---
# poker_game

**Objetivo:** Texas Hold'em, Pif Paf e Dominó em Python + Pygame, solo contra bots ou multiplayer local, com estética "Pixel Art Retrô CRT".

## Tarefas
- [ ] Baralhos novos: integrar os 8 baralhos de `design/baralhos/` (siga `GUIA_BARALHOS.md`: copiar módulo, registrar em `settings.py`, desviar `ui_theme.desenhar_carta`) e testar no Hold'em/Pif Paf — o skin `pixel_crt` de lá não foi usado; a carta "padrão" do jogo agora já nasceu pixel art direto em `ui_theme.desenhar_carta`
- [ ] Revisão visual manual do redesign Pixel Art Retrô CRT: só foi validado por render headless (telas estáticas); falta rodar `python main.py` de verdade e conferir hover/clique dos botões, o slider de raise, o drag-and-drop do Dominó e o skin "Dark" do baralho (não recapturado)
- [ ] Espectador de Hold'em: testar o modo espectador em partida multiplayer real (só validado por render headless do host)
- [ ] Design Geral: revisar o layout em janelas muito pequenas com 8 jogadores na mesa (selo SB/BB pode encostar na borda superior nesse caso extremo)
- [ ] Seleção de Baralhos: adicionar mais skins além de Padrão/Dark (ex.: terceiro estilo neobrutalista com outra paleta de acento)
- [ ] Desenho do Baralho: refinar a carta neobrutalista (`desenhar_carta` em `ui_theme.py`) — naipes, tipografia dos números, verso da carta
- [ ] Ferramenta de Criação de Baralhos (modo admin/editor): seção para criar e salvar baralhos personalizados de forma visual/guiada
- [ ] Novos Modos de Jogo: implementar um modo inédito (já existe card "EM BREVE" reservado na tela de escolha de modo)
- [ ] Multiplayer Local: testar com duas máquinas físicas reais na mesma Wi-Fi (só validado via 127.0.0.1 até agora); reconexão após queda; chat de voz; revelar cartas de todos no showdown para os clientes remotos
- [ ] Documentação: criar guia + mockup para os 2 estilos visuais ainda não explorados (Dark Glassmorphism e Terminal Tático/Sci-Fi Minimal)

## Concluído
- [x] Redesign da estética: `core/ui_theme.py` reimplementado do zero no estilo "Pixel Art Retrô CRT" (era "Neobrutalismo Suave") — cantos retos, bordas grossas, sombra sólida maior, paleta escura tipo tela de CRT (fundo azul-marinho, feltro verde-azulado, acentos dourado/verde/azul/vermelho/roxo saturados), fonte monoespaçada, avatares quadrados (eram círculos), texto de botão/tecla em caixa alta, overlay sutil de scanlines por cima de tudo (`ui_theme.aplicar_scanlines`, chamado em `main.py`). `domino_theme.py` (peças) e todas as telas (`menus/`, `holdem/`, `pifpaf/`, `domino/`, `core/chat_widget.py`, `core/ui_widgets.py`) foram ajustadas junto: contraste de texto sobre os novos fundos claros/escuros revisado call a call (fundo amarelo/verde passou a usar texto escuro; vermelho/azul/roxo, texto claro), feltro do Dominó (era bege, virou o mesmo verde-azulado dos outros modos), ícone do Dominó na escolha de modo (era um glifo Unicode quebrado, virou uma peça desenhada), acento que faltava em "CONFIGURAÇÃO DA MESA". O baralho "Padrão" nasceu pixel art; "Dark" segue como opção alternativa. Referência: `design/07_pixel_retro_crt/mockup.html` e `design/baralhos/` (estes últimos não foram importados diretamente — ver tarefa pendente de integração dos 8 baralhos novos)
- [x] Mesa de Hold'em oval com recorte; croupiê vira uma pessoa em pé no recorte (só o topo da cabeça visível); quem dá fold ou fica sem fichas vira espectador e vê as cartas de todos (host e clientes remotos)
- [x] Melhorar o Design Geral do Jogo (estética Neobrutalismo Suave aplicada a Menu, Configuração e Mesa) — substituída depois pelo Pixel Art Retrô CRT, ver item acima
- [x] Sistema de Seleção de Baralhos reimplementado no motor vetorial (Padrão/Dark)
- [x] Novos Modos de Jogo: Pif Paf e Dominó implementados, com multiplayer local nos três modos
- [x] Ajustes de UI (Mesa e Menu) e correção do bug grave do Esc fechando o jogo em qualquer tela
- [x] Multiplayer Local (Rede): salas host-autoritativo, descoberta UDP, chat de texto, robustez básica (sala cheia, desconexão, encerramento)
- [x] Documentação do Projeto: GDD.md, guias técnicos e mockups HTML das estéticas visuais

## Notas
Histórico completo (decisões técnicas, bugs corrigidos e o racional de cada mudança) preservado em `GDD.md`, `MULTIPLAYER_PLANO.md`, `PIF_PAF_GUIA.md` e `NOTAS_ATUALIZACAO_DOMINO.md` — este arquivo é só o resumo de estado/tarefas para o painel.
