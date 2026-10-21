# Requisitos e plano de testes

Fonte de verdade das regras: `holdem/README.md`, `pifpaf/README.md` e
`domino/README.md`. Quando o código divergir do README, o teste segue o README
e, se falhar, fica marcado `xfail(reason="...")` com o motivo, para o CI não
quebrar e o bug continuar registrado.

Cada teste leva o ID do requisito no nome (`test_he_03_...`) e a fonte no
docstring.

## Organização

```
poker_game/
  pytest.ini                  marcadores (lento) e pasta de testes
  tests/
    conftest.py               SDL em modo "dummy", sys.path, fábricas de cartas/jogadores, semente fixa
    REQUISITOS.md             este arquivo
    test_holdem_avaliador.py  HE-*
    test_holdem_apostas.py    HA-*
    test_holdem_potes.py      HP-*
    test_holdem_fluxo.py      HF-*
    test_holdem_bots.py       HB-*
    test_carteira.py          CA-*
    test_pifpaf_combinacoes.py PC-*
    test_pifpaf_mesa.py       PM-*
    test_pifpaf_bots.py       PB-*
    test_domino_pecas.py      DP-*
    test_domino_jogadas.py    DJ-*
    test_domino_pontuacao.py  DS-*
    test_domino_bots.py       DB-*
    test_simulacao.py         SI-*  (marcado lento)
    test_estrutura_layout.py  EL-*
    test_estrutura_rede.py    ER-*
    test_estrutura_telas.py   ET-*  (render headless)
    test_estrutura_modulos.py EM-*
```

Regras para os testes: nenhum toca em `config/layout.json` nem
`config/carteira.json` reais (usam `tmp_path` e `monkeypatch`); nenhum depende
de relógio real (o tempo da carteira é injetado); toda aleatoriedade usa
semente fixa.

## Hold'em

### HE — Avaliador (`hand_evaluator.py`)
| ID | Verifica |
|---|---|
| HE-01 | As 9 categorias saem na ordem certa: Carta Alta < Par < Dois Pares < Trinca < Sequência < Flush < Full House < Quadra < Straight Flush. |
| HE-02 | A roda A-2-3-4-5 é sequência de topo 5, e perde para 2-3-4-5-6. |
| HE-03 | Q-K-A-2-3 **não** é sequência. |
| HE-04 | Desempate por kicker: par de 9 com A vence par de 9 com K. |
| HE-05 | Dois pares: compara o par maior, depois o menor, depois o kicker. |
| HE-06 | Full house: a trinca pesa mais que o par. |
| HE-07 | Com 7 cartas, `melhor_mao` escolhe as 5 melhores (par na mesa que melhora com a mão). |
| HE-08 | Mãos idênticas em valor (naipes diferentes) empatam: `determinar_vencedores` devolve todos. |
| HE-09 | Flush compara carta a carta, da mais alta para a mais baixa. |

### HA — Rodada de apostas (`BettingRound`)
| ID | Verifica |
|---|---|
| HA-01 | A rodada só termina quando todos que podem agir agiram **e** igualaram a aposta. |
| HA-02 | Um raise reabre a ação para quem já tinha agido. |
| HA-03 | Fold tira o jogador da vez e da contagem de ativos; sobrando 1, a rodada termina. |
| HA-04 | Call com stack menor que o necessário vira all-in pelo que resta, sem stack negativo. |
| HA-05 | Jogador all-in não é mais chamado a agir. |
| HA-06 | `ultimo_raise_valor` e `aposta_alvo` acompanham o último raise. |
| HA-07 | **Ação inválida é rejeitada:** check com aposta aberta; raise menor que o mínimo; ação de quem não é da vez. *(Hoje o motor aceita; a validação está na tela do host. Ver HV-*.)* |

### HP — Potes (`calcular_potes`, `processar_showdown`)
| ID | Verifica |
|---|---|
| HP-01 | Sem all-in, um pote só, com todos os não-foldados elegíveis. |
| HP-02 | Um all-in curto cria pote principal + side pot, com os elegíveis certos. |
| HP-03 | Três all-ins de valores diferentes criam três potes. |
| HP-04 | Potes consecutivos com os mesmos elegíveis são fundidos. |
| HP-05 | A soma dos potes é igual ao total apostado por todos (inclui o dinheiro de quem foldou). |
| HP-06 | Quem foldou paga mas não é elegível. |
| HP-07 | Empate no showdown divide o pote; o resto vai para quem está mais perto do dealer. |
| HP-08 | O vencedor do pote principal pode perder o side pot para outro. |
| HP-09 | Todos foldam menos um: ele leva tudo sem mostrar mão. |
| HP-10 | O showdown acerta o dealer e o desempate por assento mesmo com `id` de jogador **não sequencial** (ex.: ids 3, 7, 9). |
| HP-11 | A soma das fichas de todos é igual antes e depois do showdown. |

### HF — Fluxo da mão (`Table`)
| ID | Verifica |
|---|---|
| HF-01 | Blinds: SB e BB saem dos assentos certos e o primeiro a agir no pré-flop é o seguinte ao BB. |
| HF-02 | Cada jogador ativo recebe 2 cartas; não há carta repetida entre mãos e mesa. |
| HF-03 | Flop 3, turn 1, river 1; chega a showdown. |
| HF-04 | O dealer avança a cada mão e pula eliminados. |
| HF-05 | Nível de blind sobe a cada 5 mãos até 400/800 e não passa disso. |
| HF-06 | Quem fica com stack 0 é eliminado em `marcar_eliminados`; sobrando 1, `jogo_tem_vencedor`. |
| HF-07 | Com 2 jogadores (heads-up) a mão ainda roda sem travar. |
| HF-08 | `Table` e `BettingRound` não leem `Player.tipo`. |

### HB — Bots (`bot_ai.py`)
| ID | Verifica |
|---|---|
| HB-01 | Sempre devolve `fold`, `check`, `call` ou `raise` válidos. |
| HB-02 | Nunca dá `check` quando há aposta a pagar. |
| HB-03 | Nunca aposta mais que o stack. |
| HB-04 | Com mão muito forte, não dá fold; com lixo e aposta alta, não dá raise (1000 amostras com semente). |
| HB-05 | O perfil do bot é fixo na partida (`id % 4`). |

### CA — Carteira (`core/carteira.py`)
| ID | Verifica |
|---|---|
| CA-01 | Sem arquivo: saldo inicial 2000. |
| CA-02 | Arquivo corrompido, saldo bool/texto: vira carteira nova. |
| CA-03 | Salvar e reler devolve o mesmo saldo. |
| CA-04 | Saldo zerado bloqueia por 12 h; antes disso, bloqueado; depois, volta a 2000. |
| CA-05 | `zerou_em` inválido é ignorado. |

## Pif Paf

### PC — Combinações (funções puras em `pifpaf_logic.py`)
| ID | Verifica |
|---|---|
| PC-01 | Trinca válida: 3 cartas do mesmo valor, naipes diferentes. Quadra válida. |
| PC-02 | Três cartas de mesmo valor e **mesmo naipe** (do baralho duplo) não são trinca. |
| PC-03 | Sequência de 3+ do mesmo naipe é válida. |
| PC-04 | O Ás vale alto (Q-K-A) e baixo (A-2-3). |
| PC-05 | Q-K-A-2 **não** é sequência. |
| PC-06 | O Joker completa trinca e sequência, e vale qualquer carta. |
| PC-07 | `pode_bater_mao` é verdadeiro só quando as 9 cartas fecham sem sobra; falso com 1 carta solta. |
| PC-08 | `agrupar_para_bater` devolve grupos que contêm exatamente as cartas da mão. |
| PC-09 | `calcular_pontos_soltos`: número = valor, J/Q/K = 10, Ás = 15, Joker = 20. |
| PC-10 | Duas cartas iguais do baralho duplo não ficam em grupos incompatíveis (a duplicata fica livre para outro grupo). |
| PC-11 | `criar_baralho_duplo()` tem 104 cartas; com Joker, 108. |

### PM — Mesa (`PifPafTable`)
| ID | Verifica |
|---|---|
| PM-01 | Cada jogador recebe 9 cartas, o descarte começa com 1 carta e o monte tem o resto. |
| PM-02 | Ordem de distribuição e do primeiro a jogar giram a cada mão (dealer). |
| PM-03 | Só se compra uma vez por vez; depois de comprar não compra de novo. |
| PM-04 | Compra do descarte tira a carta do topo do descarte. |
| PM-05 | `bater_descartando` só funciona se as 9 restantes fecham; devolve `None` caso contrário. |
| PM-06 | Bater dá **1 vitória**; ninguém é eliminado. |
| PM-07 | Mão fechada: só antes da 1ª compra do jogador na mão; vale 2 vitórias. |
| PM-08 | Depois que o jogador comprou, `pode_bater_mao_fechada` é falso. |
| PM-09 | Com 3 vitórias, `vencedor_do_jogo` aponta o jogador; antes disso, `None`. |
| PM-10 | Mão fechada de quem tem 2 vitórias: o placar não quebra o limite (documentar o comportamento: passa de 3 e vence). |
| PM-11 | Monte vazio é reciclado do descarte e o topo do descarte fica intocado. |
| PM-12 | Monte e descarte esgotados nunca travam o turno. |
| PM-13 | 200 descartes sem bater encerram a mão como empate, sem vitória para ninguém. |
| PM-14 | Cartas totais (mãos + monte + descarte) são constantes em qualquer ponto. |

### PB — Bots (`pifpaf_bot_ai.py`)
| ID | Verifica |
|---|---|
| PB-01 | `decidir_fonte_compra_bot` devolve só `monte` ou `descarte`; descarte vazio → `monte`. |
| PB-02 | Compra do descarte só quando a carta forma grupo ou reduz os pontos soltos. |
| PB-03 | `escolher_descarte_bot` devolve sempre uma carta que está na mão. |
| PB-04 | Nunca descarta o Joker, enquanto houver outra carta. |
| PB-05 | Descarta a carta solta de maior valor. |

## Dominó

### DP — Peças e distribuição
| ID | Verifica |
|---|---|
| DP-01 | `Peca(3,5) == Peca(5,3)` e o hash é igual. |
| DP-02 | `criar_pecas(4)` tem 28 peças únicas; `criar_pecas(3)` tem 27, sem a 0/0. |
| DP-03 | 4 jogadores: 7 peças cada; 3 jogadores: 9 cada; sem sobra. |
| DP-04 | Não há peça repetida entre jogadores. |
| DP-05 | `eh_carroca`, `pontos`, `combina` e `outro_lado` corretos. |

### DJ — Jogadas
| ID | Verifica |
|---|---|
| DJ-01 | 1ª mão: quem tem a 6/6 abre e só pode jogá-la. |
| DJ-02 | Demais mãos: o vencedor da anterior abre, com qualquer carroça que tiver. |
| DJ-03 | Abertura sem carroça na mão é livre. |
| DJ-04 | Abertura com peça comum havendo carroça na mão é recusada por `jogar()`. |
| DJ-05 | Depois de um bloqueio total, a abertura volta a ser a 6/6 forçada. |
| DJ-06 | Peça que não encaixa na ponta é recusada. |
| DJ-07 | Abertura com carroça cria spinner; sem carroça, não. |
| DJ-08 | Cima/baixo só ficam jogáveis depois de ter peça dos dois lados (bucho). Tentar antes é recusado pelo host. |
| DJ-09 | Pontas iguais sem spinner não geram jogadas duplicadas; **com** spinner geram uma por direção. |
| DJ-10 | Carroça jogada depois, em qualquer ramo, não cria ramo novo. |
| DJ-11 | Peça que não está na mão do jogador é recusada. |
| DJ-12 | **Fora da vez** é recusado. *(Hoje o motor aceita; a validação está na tela do host. Ver HV-*.)* |
| DJ-13 | **Passar com jogada possível** é recusado. *(Idem.)* |

### DS — Pontuação
| ID | Verifica |
|---|---|
| DS-01 | Pontas que somam múltiplo de 5 dão o total das pontas ao jogador. |
| DS-02 | Carroça na ponta conta em dobro. |
| DS-03 | A abertura sozinha soma as duas pontas, sem dobrar. |
| DS-04 | Cima/baixo só contam depois de terem peça. |
| DS-05 | Bater: soma das mãos dos outros, arredondada para baixo (3/5 + 5/5 = 18 → 15). |
| DS-06 | Última peça carroça: +30. |
| DS-07 | `passar` dá +10 a quem jogou antes (inclusive na volta do índice 0). |
| DS-08 | Trancar parcial: todos passam, volta para quem jogou e ele ainda joga → +50, e a mão continua. |
| DS-09 | Bloqueio total: o menor total de mão vence e leva a soma dos outros arredondada. |
| DS-10 | Empate no bloqueio: divide, e o resto vai para o primeiro. |
| DS-11 | Vitória só confere ao fim da mão; com 250+ vence quem tem mais. |
| DS-12 | A pontuação acumula entre mãos e não zera. |
| DS-13 | `pontuacao_se_jogar` prevê o mesmo valor que `jogar` realmente aplica (para qualquer jogada de uma mão simulada). |

### DB — Bots (`domino_bot_ai.py`)
| ID | Verifica |
|---|---|
| DB-01 | Sem jogada → `None`. |
| DB-02 | Prefere a jogada que pontua. |
| DB-03 | Entre as que não pontuam, prefere carroça, depois a de maior valor. |
| DB-04 | A jogada devolvida está sempre em `jogadas_possiveis`. |

## SI — Simulações (marcador `lento`)
| ID | Verifica |
|---|---|
| SI-01 | Hold'em: partidas completas só de bots (2 a 8 jogadores, várias sementes) terminam; soma das fichas é constante; nenhum stack negativo; nenhuma carta repetida. |
| SI-02 | Pif Paf: partidas completas (2 a 8 jogadores, com e sem Joker) terminam em 3 vitórias; total de cartas constante. |
| SI-03 | Dominó: partidas completas (3 e 4 jogadores) terminam em 250+; a cada ação, peças em mãos + mesa = 27 ou 28 sem repetição. |
| SI-04 | Nenhum bot trava a mesa: limite de ações por mão; estourar o limite reprova. |
| SI-05 | Propriedades com Hypothesis: `calcular_potes` conserva o total para qualquer combinação de apostas; `melhor_mao` nunca devolve menos que qualquer subconjunto de 5 cartas. |

## Estrutura

### EL — Layout (`core/layout.py`, `config/`)
| ID | Verifica |
|---|---|
| EL-01 | `layout_padrao.json`: todo item tem `valor`, e `min ≤ valor ≤ max`. |
| EL-02 | Toda chave de `layout.chaves()` tem entrada em `tools/editor_previas.PREVIAS`, e vice-versa. |
| EL-03 | Todo preset de `config/presets_padrao/` aplica sem erro e só com chaves existentes. |
| EL-04 | Arquivo do usuário corrompido, ausente ou com tipo errado → cai no padrão, sem exceção. |
| EL-05 | Valor fora da faixa é limitado. |
| EL-06 | `salvar()` grava só o que mudou e `recarregar()` lê de volta (em `tmp_path`). |
| EL-07 | Chave inexistente em `obter()` levanta `KeyError`. |
| EL-08 | `aplicar_tema` muda as cores no lugar (o mesmo objeto) e não troca o nome da cor. |

### ER — Rede (`rede/protocolo.py`)
| ID | Verifica |
|---|---|
| ER-01 | `empacotar` → `DecodificadorFrames` devolve o mesmo dict, com acentos e emoji. |
| ER-02 | Mensagem partida em pedaços (byte a byte) é remontada. |
| ER-03 | Duas mensagens coladas no mesmo `recv` saem separadas. |
| ER-04 | Mensagem maior que 1 MiB levanta `ValueError`. |
| ER-05 | JSON inválido no corpo não deixa o decodificador num estado quebrado. |
| ER-06 | `MAX_JOGADORES_POR_JOGO`: 8 para Hold'em e Pif Paf, 4 para Dominó. |

### ET — Telas (render headless)
| ID | Verifica |
|---|---|
| ET-01 | Cada tela de menu (menu, escolha de modo, configuração, ajustes) desenha em 1280x800 e 1024x768, sem exceção. |
| ET-02 | As três mesas (host) desenham em cena de início, meio e fim de mão, nas duas resoluções. |
| ET-03 | As três mesas remotas desenham a partir de um estado simulado. |
| ET-04 | Todo baralho de `ORDEM_BARALHO_SKINS` desenha uma carta, o verso e o slot vazio. |
| ET-05 | O detector do editor (`editor_mesa.calcular_alertas`) dá zero alertas na matriz modo × jogadores × janela × cena. *(lento)* |

### EM — Módulos
| ID | Verifica |
|---|---|
| EM-01 | Todo módulo de `core/`, `holdem/`, `pifpaf/`, `domino/`, `menus/`, `rede/` e `main` importa sem erro. |
| EM-02 | `main.App` sobe com tela falsa e executa N quadros (smoke). |
| EM-03 | As telas host e remota de cada modo importam a mesma geometria compartilhada (sem cópia local). |
| EM-04 | `PixelPoker.spec` cita arquivos que existem (`config/layout_padrao.json`, `config/presets_padrao`). |

## Ordem de implementação sugerida
1. Esqueleto: `pytest.ini`, `conftest.py` e marcador `lento`.
2. Dominó (DP, DJ, DS, DB): regras mais precisas e tabela de pontuação.
3. Pif Paf (PC, PM, PB).
4. Hold'em (HE, HA, HP, HF, HB, CA).
5. Estrutura (EL, ER, EM, ET).
6. Simulações (SI).
7. `.github/workflows/ci.yml`.
8. Ajustar o `qa.toml` e rodar o QA de novo.

## Anexo — o que mudou na implementação

Itens acrescentados ao plano, além dos requisitos acima:

| ID | Verifica |
|---|---|
| HV-01 a HV-07 | Hold'em, host: recusa ação fora da vez, check com aposta, raise acima do stack, ação desconhecida, jogador desconhecido; aceita ação válida. **HV-07:** raise abaixo do mínimo deveria ser recusado (hoje não é). |
| HV-10 a HV-14 | Dominó, host: recusa jogada fora da vez, passar com jogada, peça que não tem, jogada mal formada; aceita jogada válida. |
| HV-20 a HV-25 | Pif Paf, host: recusa ação fora da vez, descartar antes de comprar, comprar duas vezes, bater sem poder, mão fechada indisponível, carta que não tem. |
| PC-12 | `carta_completa_combinacao`: fecha trinca, não ajuda com carta solta, o Joker sempre ajuda. |
| ET-06 | As salas de espera (anfitrião e cliente) desenham. |
| EM-05 | Nenhum módulo do jogo importa `tools/` (que não vai no `.exe`). |
| EM-06 | Os motores dos três modos não importam um ao outro. |
| EL-09 | As cores do tema são `pygame.Color` mutáveis. |
| CA-06 | `formatar_espera`. |

Decisão 2 (o motor deve recusar ação inválida?): a leitura do código mostrou que
as telas do host já validam tudo o que chega pela rede (vez, check com aposta,
passar com jogada, descartar antes de comprar). O que falta nos motores
(HA-07, DJ-12, DJ-13) ficou como `xfail` de defesa em profundidade. A única
lacuna real de regra é o **raise mínimo** (HV-07 e HA-07).
