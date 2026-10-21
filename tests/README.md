# Testes do Pixel Poker

297 testes automáticos para as regras dos três modos (Hold'em, Pif Paf, Dominó)
e para a estrutura do projeto (layout, rede, telas, módulos). Rodam sem janela
e sem som, em cerca de 10 segundos.

A lista de requisitos de onde saíram, com ID e fonte, está em
[REQUISITOS.md](REQUISITOS.md). As regras vêm dos READMEs de cada modo
([Hold'em](../holdem/README.md), [Pif Paf](../pifpaf/README.md),
[Dominó](../domino/README.md)): quando o código diverge do README, o teste segue
o README.

## Como rodar

```bash
pip install -r requirements-dev.txt
pytest -m "not lento"
```

| Comando | O que roda |
|---|---|
| `pytest -m "not lento"` | Tudo menos as simulações e a matriz do editor (≈ 3 s). É o que o CI roda a cada push. |
| `pytest -m lento` | Partidas completas só de bots e o detector de sobreposição do editor (≈ 10 s). |
| `pytest` | Tudo. |
| `pytest tests/test_domino_pontuacao.py` | Um arquivo. |
| `pytest -k ds_08` | Um requisito pelo ID (o ID está no nome do teste). |
| `pytest -rx` | Mostra o motivo de cada falha conhecida (`xfail`). |
| `pytest --runxfail` | Roda as falhas conhecidas como testes normais, para ver o erro real. |

No Windows com PowerShell o comando é o mesmo. O `conftest.py` já configura
`SDL_VIDEODRIVER=dummy`, então não é preciso definir variável nenhuma.

## O que cada arquivo testa

| Arquivo | IDs | O que verifica |
|---|---|---|
| `test_holdem_avaliador.py` | HE | As 9 categorias de mão na ordem certa, a roda A-2-3-4-5, kickers, empate exato, melhor mão entre 7 cartas. |
| `test_holdem_apostas.py` | HA | Rodada de apostas: quando termina, raise reabre a ação, fold, all-in, aposta alvo. |
| `test_holdem_potes.py` | HP | Pote principal e side pots, junção de potes, split com resto, showdown, conservação das fichas. |
| `test_holdem_fluxo.py` | HF | Blinds, dealer, flop/turn/river, níveis de blind, eliminação, heads-up, motor desacoplado. |
| `test_holdem_bots.py` | HB | A IA devolve ações válidas, respeita stack e aposta a pagar, perfis se comportam diferente. |
| `test_carteira.py` | CA | Carteira persistente: saldo inicial, arquivo corrompido, espera de 12 h, reposição. |
| `test_pifpaf_combinacoes.py` | PC | Trinca, sequência, Ás alto e baixo, Joker, bater, pontos soltos, baralho duplo. |
| `test_pifpaf_mesa.py` | PM | Distribuição, compra, bater descartando, mão fechada (2 vitórias), 3 vitórias, monte vazio, empate em 200 turnos. |
| `test_pifpaf_bots.py` | PB | Escolha entre monte e descarte, descarte da solta mais alta, nunca descarta Joker. |
| `test_domino_pecas.py` | DP | 28 ou 27 peças, divisão exata, peça normalizada. |
| `test_domino_jogadas.py` | DJ | Abertura (6/6, carroça), spinner, bucho, jogadas por direção, validação de jogada. |
| `test_domino_pontuacao.py` | DS | Pontas em múltiplo de 5, carroça em dobro, bater e arredondamento, +30, +10 do passe, +50 de trancar, bloqueio total e empate, vitória em 250, `pontuacao_se_jogar` igual ao que `jogar` aplica. |
| `test_domino_bots.py` | DB | Prefere a jogada que pontua, depois carroça, depois a maior peça. |
| `test_host_validacao.py` | HV | O host recusa ação remota inválida nos três modos (fora da vez, check com aposta, passar com jogada, descartar antes de comprar...). |
| `test_estrutura_layout.py` | EL | `layout_padrao.json` coerente, toda chave tem prévia no editor, presets válidos, arquivo do usuário estragado, limites, salvar/recarregar, tema. |
| `test_estrutura_rede.py` | ER | Protocolo de rede: ida e volta, mensagem partida, mensagens coladas, limite de tamanho, JSON inválido. |
| `test_estrutura_modulos.py` | EM | Todo módulo importa, o app sobe e navega, host e cliente compartilham a geometria, o `.spec` aponta para arquivos que existem, `tools/` não entra no jogo. |
| `test_estrutura_telas.py` | ET | Todas as telas desenham em 1280x800 e 1024x768: menus, mesas do host, mesas do cliente remoto (com o estado real do host, passando por JSON), os 10 baralhos, salas de espera. A matriz do detector do editor (`lento`) não pode acusar erro. |
| `test_simulacao.py` | SI | Partidas completas só de bots: terminam, conservam fichas/cartas/peças, sem repetição. Propriedades com Hypothesis. |

## Como os testes são escritos

- **Cartas** (`tests/helpers.py`): `cartas("Ae Ke 10c")`. Valor + naipe, onde
  `c` copas, `o` ouros, `p` paus, `e` espadas, e `*` é o Joker.
- **Dominó**: `mesa_domino("4-4 4-2", "4-1 0-3", "5-5")` monta uma mesa com as
  mãos escolhidas a dedo; `jogar(mesa, jogador, "4-4")` joga e confere que foi
  aceita.
- **Semente fixa**: o `conftest.py` fixa `random.seed` antes de cada teste, então
  um teste que falha falha sempre.
- **Isolamento**: nenhum teste lê ou grava o `config/layout.json` e o
  `config/carteira.json` reais. O layout do usuário e a carteira são trocados
  por pastas temporárias para a sessão inteira, e o relógio da carteira é
  injetado. Pode rodar com o jogo aberto.
- **Telas sem janela**: as telas rodam sobre uma superfície em memória
  (`pygame.Surface`) e o `editor_mesa.AppFalso`, o mesmo usado pelo editor.

## Falhas conhecidas (`xfail`)

Um teste marcado `xfail` descreve uma regra do README que o código ainda não
cumpre. O CI continua verde, o motivo fica registrado e, quando o bug for
corrigido, o teste passa a aparecer como `XPASS`: aí é só tirar a marca.

| Teste | Problema |
|---|---|
| `test_et_06_a_sala_de_espera_do_anfitriao_desenha` | `menus/multiplayer_screens.py:324` usa `SOMBRA` sem importar. Nenhum host consegue abrir uma sala multiplayer. O mesmo erro faz o passo `ruff` do CI falhar. |
| `test_pc_06_o_joker_estende_a_ponta_de_uma_sequencia` | O Joker só preenche buraco no meio da sequência. `4e 5e *` e `Ke Ae *` deveriam fechar. |
| `test_hf_05_cada_nivel_de_blind_dura_cinco_maos` | O nível 10/20 dura 4 mãos, não 5 (off-by-one em `iniciar_nova_mao`). |
| `test_hp_10_o_showdown_funciona_com_ids_...` | `processar_showdown` usa o id do jogador como posição do assento. Com ids que não sejam 0..n-1 (sala multiplayer em que alguém saiu do lobby), levanta `ValueError`. |
| `test_hv_07_holdem_raise_abaixo_do_minimo_e_recusado` e `test_ha_07_raise_abaixo_do_minimo_e_recusado` | Não existe raise mínimo, nem no motor nem no host. |
| `test_hb_03_o_raise_nunca_passa_do_que_o_bot_tem` | O bot às vezes devolve raise de um big blind inteiro com stack menor. |
| `test_dj_12`, `test_dj_13`, `test_ha_07_check...`, `test_ha_07_acao_fora_da_vez...` | Defesa em profundidade: os motores aceitam jogar fora da vez, passar tendo jogada e check com aposta aberta. Hoje quem recusa é a tela do host (testes `HV`, que passam). Só importa se algum dia outra parte do código chamar o motor direto. |

## Integração contínua

`.github/workflows/ci.yml` roda no GitHub Actions:

| Job | Quando | O que faz |
|---|---|---|
| `rapido` | todo push e PR | `ruff` (só erros de verdade) e `pytest -m "not lento"`. |
| `completo` | PR, toda manhã e disparo manual | `pytest -m lento`: simulações e matriz do editor. |
| `windows` | PR e disparo manual | A suíte rápida no Windows. |
| `exe` | só disparo manual | Gera o `PixelPoker.exe` com o `PixelPoker.spec` e guarda como artefato. |

## Como acrescentar um teste

1. Escolha o ID do requisito (ou crie um novo em `REQUISITOS.md`).
2. Escreva o teste no arquivo da área, com o ID no nome: `test_ds_14_...`.
3. Cite a regra no docstring ou no nome. Prefira montar a situação com os
   helpers a depender de sorteio.
4. Se o teste revela um bug, deixe-o escrito pela regra e marque
   `@pytest.mark.xfail(reason="BUG: ...")`; não afrouxe o teste para passar.
5. Mexeu em geometria de mesa? Rode `pytest -m lento` antes de commitar.
