# Backlog de Melhorias do Projeto

Este documento armazena todas as ideias, melhorias e novas funcionalidades planejadas para o futuro do jogo.

## 1. Melhorar o Design Geral do Jogo (Concluído — Neobrutalismo Suave)
- [x] Estética "Neobrutalismo Suave / Dashboard Analítico" validada antes da implementação através de guias técnicos e mockups HTML (ver item 6) e depois aplicada a todas as telas do jogo (Menu, Configuração, Mesa) via `ui_theme.py`, substituindo a pixel art.
- [x] Mesa retangular arredondada, cartas maiores e legíveis na mão do jogador, bots com painel próprio (avatar, nome, saldo e status: "Pensando...", "Fold", "All-in").
- [x] Painel de **histórico de ações da rodada**, fixo no canto inferior direito da mesa.
- [x] Atalhos de teclado reais para as ações (`F` Fold, `C` Check/Call, `R` Raise, `Enter` confirmar), com os selos visuais correspondentes nos botões.
- [ ] Pendente: revisar o layout em janelas muito pequenas com 8 jogadores na mesa (um selo SB/BB pode encostar na borda superior da tela nesse caso extremo).

## 2. Sistema de Seleção de Baralhos (Pausado na migração de estilo)
- [x] ~~Menu de configuração com Pixel Art / Clássico / Dark Mode~~ — implementado na era pixel art, hoje descontinuado.
- Ao migrar para o Neobrutalismo Suave, o seletor de estilos de baralho foi removido da tela de Configuração: o sistema antigo de sprites (`ui_pixelart.py` + `assets/assets.png`) ficou obsoleto e não é mais usado pelo jogo, mas foi mantido no projeto como referência. Hoje existe um único baralho, desenhado no novo estilo vetorial.
- [ ] Pendente: se fizer sentido no futuro, reimplementar a seleção de baralhos dentro do novo sistema visual (múltiplos "skins" de carta neobrutalistas, em vez de sprites).

## 3. Ajustes no Desenho do Baralho Atual
- [ ] Refinar a carta neobrutalista atual (`desenhar_carta` em `ui_theme.py`): naipes, tipografia dos números e verso da carta.

## 4. Ferramenta de Criação de Baralhos (Modo Admin/Editor)
- [ ] Criar uma seção especial (voltada para o administrador ou criador).
- [ ] Permitir a criação de novos designs de cartas de forma visual ou guiada.
- [ ] Possibilidade de "montar" e salvar um baralho personalizado a partir dos assets criados para ser usado no jogo.

## 5. Novos Modos de Jogo
- [ ] Expandir além do Texas Hold'em.
- [ ] Implementar o modo de jogo **Pif Paf**.
- [ ] Implementar e projetar um modo de jogo inédito/diferente.
- Nota: os mockups em `design/*/mockup.html` já preveem uma tela de menu com seleção de modos (cards "Ativo"/"Em breve"), mas isso ainda não foi implementado no menu real do jogo — o menu atual só tem Texas Hold'em porque é o único modo que existe de fato.

## 6. Documentação do Projeto
- [x] Escrever um **GDD (Game Design Document)** para consolidar todas as mecânicas, regras e visão do jogo em um único lugar (`GDD.md`).
- [x] Escrever um **Guia de Estilo** com as diretrizes visuais do projeto: em `design/`, foram criados guias técnicos (paleta, tipografia, dimensões e instruções de renderização em Pygame) e mockups HTML interativos para 3 das 5 estéticas propostas antes da migração:
  - `design/01_neobrutalismo_suave/` — **aplicada ao jogo** (ver item 1).
  - `design/03_casino_minimalista/` — validada em mockup, não implementada em Pygame.
  - `design/05_cozy_flat/` — validada em mockup, não implementada em Pygame.
- [ ] Pendente: os outros 2 estilos cogitados inicialmente (Dark Glassmorphism/Desktop Client Moderno e Terminal Tático/Sci-Fi Minimal) ainda não têm guia nem mockup, caso um dia se queira comparar mais opções.

---
*Atualizado conforme surgirem novas ideias.*
