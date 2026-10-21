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

### 2.3 Dominó
- **Status:** Implementado (`domino_logic.py`, `domino_bot_ai.py`, `domino_screen.py`)
- **Regras/Detalhes:** Corrida de pontos até 250, livre-pra-todos (sem
  duplas), jogo duplo-seis, 3 ou 4 jogadores. Sem monte: com 4 jogadores
  usa-se o jogo completo (28 peças, 7 cada); com 3, a peça 0/0 é retirada
  (27 peças, 9 cada) — nos dois casos a divisão é exata, então cada jogador
  já recebe de saída todas as peças que vai ter na mão. Quem não tem jogada
  clica em "Passar" (ação explícita, não automática).
  - **Abertura:** a primeira jogada de toda mão é obrigatoriamente uma
    carroça. Na primeira mão do jogo (e em toda mão após um travamento
    total), quem tiver a peça 6/6 abre e é obrigado a jogar justo essa;
    nas demais mãos, quem bateu por último abre, escolhendo qual carroça
    jogar entre as que tiver (só abre com qualquer peça se não tiver
    carroça nenhuma na mão).
  - **Pontuação em jogo:** toda vez que uma jogada fecha as duas pontas da
    mesa num múltiplo de 5 (carroça na ponta conta em dobro, estilo
    "All Fives"), quem jogou marca esses pontos na hora.
  - **Bater:** quem esvazia a mão primeiro ganha a soma dos pontos das
    peças que sobraram na mão dos outros, arredondada pra baixo pro
    múltiplo de 5 mais próximo (ex.: sobrou 18 pontos → ganha 15); se a
    última peça jogada for carroça, +30 de bônus.
  - **Passar:** quem jogou imediatamente antes de alguém passar ganha +10.
  - **Trancar:** se todos os outros passarem em sequência e a vez voltar
    pra quem jogou, e essa pessoa ainda conseguir jogar, ela ganha +50 e o
    jogo continua normalmente. Se ninguém, nem essa pessoa, mais conseguir
    jogar (travamento total), a mão termina: quem tem menos pontos na mão
    vence a mesma soma arredondada dos demais, e a próxima mão volta a
    exigir abertura com 6/6.
  - **Vitória:** checada só ao final de cada mão (nunca no meio) — o
    primeiro a acumular 250 pontos ou mais vence a partida inteira.
- **Economia/Pontuação:** Não usa fichas nem o esquema de eliminação por
  falência do Hold'em/Pif Paf — ninguém é eliminado no meio do caminho.
  Todos os jogadores acumulam `pontuacao` mão após mão até alguém alcançar
  250 (ver regras acima).
- **Multiplayer local:** suportado desde o lançamento do modo (diferente do
  Pif Paf, que começou solo) — ver `MULTIPLAYER_PLANO.md`. Sala de 3 a 4
  jogadores (`MAX_JOGADORES_POR_JOGO` em `multiplayer_screens.py` pro
  máximo, `LobbyScreen._pode_iniciar` pro mínimo), diferente do limite de 8
  do Hold'em/Pif Paf.

### 2.4 Modo Inédito Original
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

### 3.4 Editor Visual de Layout (implementado)
- Ferramenta separada (`python tools/editor_visual.py`, ou o botão "Editor de layout" na tela de Ajustes quando o jogo roda pelo código-fonte) para ajustar sem programar: tamanho das cartas, peças e botões, espaçamentos, as 16 cores do tema, tamanho das fontes, borda/sombra, fichas iniciais e tempo de jogada dos bots.
- Cada valor tem botões -/+, campo digitável e "padrão"; as cores têm sliders RGB e aviso de contraste.
- Duas prévias: **ITEM** (o trecho afetado, em tamanho real) e **MESA COMPLETA** (a tela de verdade do jogo numa partida simulada, com escolha de cena, número de jogadores e tamanho de janela, e alertas automáticos do que sai da tela ou se sobrepõe).
- Os valores ficam em `config/layout_padrao.json` (padrão) e `config/layout.json` (ajustes do jogador). Um jogo aberto recarrega sozinho quando o editor salva (ou com F5).
- **Presets:** "compacto" (janelas pequenas e notebooks) e "grande" (telas de 1600x900 ou mais) vêm com o jogo; o jogador pode salvar os próprios e trocá-los copiando os `.json` da pasta `config/presets/`.
- A mesma infraestrutura (valores num JSON, prévia com o código real do jogo, recarga sem reiniciar) pode servir de base para a Ferramenta de Criação de Baralhos (3.3).

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
