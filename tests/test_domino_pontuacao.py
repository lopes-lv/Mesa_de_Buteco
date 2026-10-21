"""DS-* — pontuação do Dominó (domino/README.md, tabela de "Pontuação" e "Vitória")."""
import copy
import random

from domino.domino_logic import (BONUS_CARROCA_FECHOU, BONUS_PASSE, BONUS_TRANCAR_PARCIAL,
                                 PONTUACAO_VITORIA, DominoPlayer, DominoTable, Peca)
from tests.helpers import jogar, mesa_domino


def test_ds_01_pontas_em_multiplo_de_5_dao_o_total_das_pontas():
    # Abertura 5-5: as pontas somam 5 + 5 = 10, múltiplo de 5.
    mesa, (a, *_) = mesa_domino("5-5 0-1", "2-3", "1-1")
    jogar(mesa, a, "5-5")
    assert a.pontuacao == 10
    assert mesa.pontuou_pontas == 10


def test_ds_01_pontas_fora_de_multiplo_de_5_nao_pontuam():
    mesa, (a, *_) = mesa_domino("6-6 0-1", "2-3", "1-1")
    jogar(mesa, a, "6-6")                      # 6 + 6 = 12
    assert a.pontuacao == 0
    assert mesa.pontuou_pontas is None


def test_ds_02_carroca_na_ponta_conta_em_dobro():
    # abertura 4-4 (carroça): a ponta direita continua sendo ela, valendo 4 x 2.
    # 4-2 na esquerda deixa 2 + 8 = 10.
    mesa, (a, b, _c) = mesa_domino("4-4 0-1", "4-2 3-3", "5-5")
    jogar(mesa, a, "4-4")
    jogar(mesa, b, "4-2", "esquerda")
    assert b.pontuacao == 10


def test_ds_03_abertura_sozinha_soma_as_duas_pontas_sem_dobrar():
    mesa, (a, *_) = mesa_domino("5-5 0-1", "2-3", "1-1")
    jogar(mesa, a, "5-5")
    assert mesa.pontos_pontas() == 10          # e não 20


def test_ds_04_cima_e_baixo_so_contam_depois_de_terem_peca():
    mesa, (a, b, c) = mesa_domino("4-4 4-0 0-0", "4-2 6-6", "4-3 1-1")
    jogar(mesa, a, "4-4")
    jogar(mesa, b, "4-2", "esquerda")          # 2 + 8 = 10 -> b pontua 10
    assert b.pontuacao == 10
    jogar(mesa, c, "4-3", "direita")           # esq 2 + dir 3 = 5 (cima/baixo ainda vazios)
    assert mesa.pontuou_pontas == 5
    assert c.pontuacao == 5
    # a coloca 4-0 em cima: 2 + 3 + 0 = 5, agora contando o ramo de cima
    jogar(mesa, a, "4-0", "cima")
    assert mesa.pontuou_pontas == 5


def test_ds_05_bater_soma_as_maos_dos_outros_arredondada_para_baixo():
    mesa, (a, b, c) = mesa_domino("4-4 4-2", "4-6 3-5", "6-1 5-5")
    jogar(mesa, a, "4-4")
    jogar(mesa, b, "4-6", "esquerda")
    jogar(mesa, c, "6-1", "esquerda")
    antes = a.pontuacao
    jogar(mesa, a, "4-2", "direita")           # a esvazia a mão
    resultado = mesa.resultado_mao
    assert resultado["tipo"] == "bateu"
    assert resultado["vencedor"] == a.nome
    # sobraram 3-5 (8) e 5-5 (10) = 18 -> 15
    assert resultado["pontos_ganhos"] == 15
    assert not resultado["carroca_bonus"]
    assert a.pontuacao - antes >= 15


def test_ds_06_batida_com_carroca_vale_mais_30():
    mesa, (a, b, c) = mesa_domino("6-6", "3-5 5-5", "2-3")
    jogar(mesa, a, "6-6")
    resultado = mesa.resultado_mao
    assert resultado["carroca_bonus"]
    # 3-5 + 5-5 + 2-3 = 8 + 10 + 5 = 23 -> 20, mais o bônus
    assert resultado["pontos_ganhos"] == 20 + BONUS_CARROCA_FECHOU
    assert a.pontuacao == 20 + BONUS_CARROCA_FECHOU


def test_ds_07_passar_da_10_a_quem_jogou_antes():
    mesa, (a, b, c) = mesa_domino("4-4 0-1", "2-3", "5-5")
    jogar(mesa, a, "4-4")
    mesa.passar(b)
    assert a.pontuacao == BONUS_PASSE
    assert mesa.bonus_passe_para == a.nome


def test_ds_07_o_bonus_do_passe_volta_ao_ultimo_da_ordem_quando_a_vez_e_do_primeiro():
    mesa, (a, b, c) = mesa_domino("4-4 0-1", "2-3", "5-5")
    mesa.indice_da_vez = 0
    mesa.passes_consecutivos = 0
    mesa.passar(a)
    assert c.pontuacao == BONUS_PASSE


def test_ds_08_trancar_parcial_da_50_e_a_mao_continua():
    mesa, (a, b, c) = mesa_domino("4-4 4-1 0-0", "2-3", "2-5")
    jogar(mesa, a, "4-4")
    mesa.passar(b)
    mesa.passar(c)                             # volta pra a, que ainda joga
    antes = a.pontuacao
    jogar(mesa, a, "4-1", "esquerda")
    assert mesa.trancou_parcial
    assert a.pontuacao - antes == BONUS_TRANCAR_PARCIAL
    assert mesa.resultado_mao is None


def test_ds_09_bloqueio_total_vai_para_quem_tem_menos_pontos():
    mesa, (a, b, c) = mesa_domino("4-4 0-1", "2-3", "5-5 0-2")
    jogar(mesa, a, "4-4")
    mesa.passar(b)
    mesa.passar(c)
    mesa.passar(a)
    resultado = mesa.resultado_mao
    assert resultado["tipo"] == "bloqueio_total"
    assert resultado["vencedor"] == a.nome     # 0-1 = 1 ponto
    # b: 5, c: 5 + 2 + 5... = 12 -> soma 17 -> 15
    assert resultado["pontos_ganhos"] == 15
    assert not resultado["empate"]


def test_ds_10_empate_no_bloqueio_divide_e_o_resto_vai_para_o_primeiro():
    mesa, (a, b, c) = mesa_domino("4-4 0-5", "2-3", "5-5 3-2")
    jogar(mesa, a, "4-4")
    mesa.passar(b)
    mesa.passar(c)
    mesa.passar(a)
    resultado = mesa.resultado_mao
    assert resultado["empate"]
    assert resultado["vencedor"] == f"{a.nome}, {b.nome}"
    # soma dos perdedores: 15 -> dividida em 2: a leva 8, b leva 7 (fora o bônus do passe)
    assert resultado["pontos_ganhos"] == 15
    assert a.pontuacao == BONUS_PASSE + 8
    assert b.pontuacao == BONUS_PASSE + 7


def test_ds_11_vitoria_so_e_conferida_pelo_vencedor_do_jogo_ao_fim_da_mao():
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(3)]
    mesa = DominoTable(jogadores)
    assert mesa.vencedor_do_jogo() is None
    jogadores[0].pontuacao = PONTUACAO_VITORIA - 1
    assert mesa.vencedor_do_jogo() is None
    jogadores[0].pontuacao = PONTUACAO_VITORIA
    jogadores[1].pontuacao = PONTUACAO_VITORIA + 20
    assert mesa.vencedor_do_jogo() is jogadores[1]   # o maior


def test_ds_11_passar_de_250_no_meio_da_mao_nao_encerra_a_mao():
    mesa, (a, *_) = mesa_domino("5-5 0-1", "2-3", "1-1")
    a.pontuacao = PONTUACAO_VITORIA - 1
    jogar(mesa, a, "5-5")                      # +10
    assert a.pontuacao >= PONTUACAO_VITORIA
    assert mesa.resultado_mao is None


def test_ds_12_pontuacao_acumula_entre_maos():
    mesa, (a, b, c) = mesa_domino("4-4", "2-3", "5-5")
    jogar(mesa, a, "4-4")                      # bate de primeira
    acumulado = a.pontuacao
    assert acumulado > 0
    mesa.iniciar_nova_mao()
    assert a.pontuacao == acumulado


def _jogadas_de_uma_partida(semente):
    """Gera (mesa, jogador, peca, direcao) de cada jogada de uma partida de bots."""
    random.seed(semente)
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(4)]
    mesa = DominoTable(jogadores)
    mesa.iniciar_nova_mao()
    for _ in range(300):
        if mesa.resultado_mao is not None:
            return
        jogador = mesa.jogador_da_vez()
        opcoes = mesa.jogadas_possiveis(jogador)
        if not opcoes:
            mesa.passar(jogador)
            continue
        peca, direcao = random.choice(opcoes)
        yield mesa, jogador, peca, direcao
        assert mesa.jogar(jogador, peca, direcao)


def test_ds_13_pontuacao_se_jogar_prevê_o_que_jogar_aplica():
    verificadas = 0
    for semente in range(15):
        for mesa, jogador, peca, direcao in _jogadas_de_uma_partida(semente):
            previsto = mesa.pontuacao_se_jogar(peca, direcao)
            copia = copy.deepcopy(mesa)
            jogador_copia = next(j for j in copia.jogadores if j.id == jogador.id)
            copia.jogar(jogador_copia, peca, direcao)
            assert (copia.pontuou_pontas or 0) == previsto, f"semente {semente}: {peca} em {direcao}"
            verificadas += 1
    assert verificadas > 100
