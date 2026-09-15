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
- **Status:** Implementado (ver [PIF_PAF_GUIA.md](PIF_PAF_GUIA.md) para o guia completo)
- **Regras/Detalhes:** Baralho duplo (104 cartas). Cada jogador recebe 9 cartas.
  Existe curinga: a carta de valor seguinte à "vira" (virada do monte antes da
  distribuição) substitui qualquer carta em trincas (3-4 cartas, mesmo valor,
  naipes diferentes) ou sequências (3+ cartas seguidas do mesmo naipe). No
  turno, o jogador compra 1 carta (do monte ou do topo do descarte) e então
  bate (zera a mão em combinações válidas) ou descarta 1 carta. Quem não bate
  paga em fichas os pontos das cartas que sobraram soltas; quem bate embolsa
  o pote. A regra da "a louca" (bater fora da vez com o descarte alheio) não
  foi implementada nesta versão.
- **Economia/Fichas:** Mesmo esquema de "torneio até sobrar 1 jogador" do
  Hold'em, reaproveitando o valor inicial de fichas de `game_logic.py`.

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
