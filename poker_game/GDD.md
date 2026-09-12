# Game Design Document (GDD) - Poker Game

## 1. Visão Geral (Overview)
- **Nome Provisório:** Poker Game
- **Gênero:** Jogo de Cartas / Cassino
- **Estilo Visual:** Pixel Art (ver Guia de Estilo a ser criado)
- **Plataforma:** PC
- **Premissa:** Um jogo de cartas com foco em uma experiência polida e moderna, suporte a múltiplos modos de jogo e um forte sistema de personalização visual (baralhos customizáveis).

## 2. Modos de Jogo (Gameplay)
O jogo suportará diferentes modalidades de jogos de baralho.

### 2.1 Texas Hold'em
- **Status:** Base do projeto
- **Regras/Detalhes:** Formato *No-Limit*, permitindo que o jogador aposte a quantidade de fichas que quiser (All-in) a qualquer momento.
- **Economia/Fichas:** O jogador inicia a sessão com 2.000 (2k) fichas. Se falir, perde a partida atual. Ao iniciar uma nova partida (sair e entrar no modo), as fichas são reiniciadas para 2.000.

### 2.2 Pif Paf
- **Status:** Planejado
- **Regras/Detalhes:** [A definir: Quantas cartas na mão? Tem curinga? Quais as regras de batida?]

### 2.3 Modo Inédito Original
- **Status:** Planejado
- **Conceito:** [A definir: Qual será a mecânica única desse modo?]

## 3. Mecânicas e Sistemas Principais

### 3.1 Inteligência Artificial (Bots)
- **Comportamento e Personalidade:** Os bots terão personalidades próprias (como agressivos, conservadores, blefadores, etc.).
- **Dinâmica por Partida:** A cada nova sessão/partida que o jogador inicia, os bots recebem uma personalidade diferente. Ou seja, as características não são fixas a um "nome" de bot, garantindo que toda partida traga um desafio e comportamento únicos.

### 3.2 Sistema de Seleção de Baralhos
- O jogador poderá escolher qual baralho usar durante a partida através de um menu de configurações.
- Suporte a múltiplos modelos. Cada baralho terá seus próprios *assets* desenhados (naipes, números, rostos de J, Q, K e verso).

### 3.3 Ferramenta de Criação de Baralhos (Modo Editor)
- Uma ferramenta/seção especial voltada para o administrador ou criador de conteúdo.
- Permitirá a montagem e criação de novos designs de cartas de forma visual e guiada.
- Possibilidade de salvar o baralho personalizado como um pacote de *assets* para uso no jogo.

## 4. Interface e Experiência do Usuário (UI/UX)
- **Estética:** Interface polida e moderna, mas mantendo a essência e o charme da pixel art.
- **Fluxo de Telas:**
  - Menu Principal
  - Configurações (Seleção de Baralho)
  - Tela de Jogo (Mesa)
  - Telas Finais (Fim de Jogo)
  - Modo Editor (Criador de Baralhos)

## 5. Arte e Áudio
- **Estilo de Arte:** Pixel Art.
- **Áudio e "Jukebox":** O jogo terá um sistema onde o próprio jogador poderá escolher o tipo de música/vibe que ele quer escutar durante a partida, permitindo uma maior personalização da experiência.

## 6. Escopo Técnico
- **Linguagem:** Python
- **Engine/Biblioteca Principal:** Pygame (com possibilidade de migração futura caso seja necessário para expandir o projeto).

---
*Este documento é vivo e deve ser atualizado conforme o jogo evolui.*
