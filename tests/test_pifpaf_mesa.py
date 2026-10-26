"""PM-* — a mesa do Pif Paf (pifpaf/README.md, "Regras implementadas")."""
import pytest

from pifpaf.pifpaf_logic import (LIMITE_TURNOS_SEM_BATIDA, VITORIAS_PARA_VENCER, PifPafPlayer,
                                 PifPafTable)
from tests.helpers import carta, cartas

PRONTA_9 = "4e 5e 6e 7c 7o 7p 9c 10c Jc"             # 9 cartas, tudo combinado
PRONTA_10 = "4e 5e 6e 7e 7c 7o 7p 9c 10c Jc"          # 10 cartas, tudo combinado


def nova_mesa(quantidade=3, usar_joker=False):
    jogadores = [PifPafPlayer(i, f"J{i}") for i in range(quantidade)]
    mesa = PifPafTable(jogadores, usar_joker=usar_joker)
    mesa.iniciar_nova_mao()
    return mesa, jogadores


def total_de_cartas(mesa):
    return sum(len(j.mao) for j in mesa.jogadores) + len(mesa.monte) + len(mesa.descarte)


@pytest.mark.parametrize("usar_joker,total", [(False, 104), (True, 108)])
def test_pm_01_distribuicao_inicial(usar_joker, total):
    mesa, jogadores = nova_mesa(4, usar_joker)
    assert all(len(j.mao) == 9 for j in jogadores)
    assert len(mesa.descarte) == 1
    assert len(mesa.monte) == total - 4 * 9 - 1
    assert total_de_cartas(mesa) == total


def test_pm_02_o_primeiro_a_jogar_gira_a_cada_mao():
    mesa, jogadores = nova_mesa(3)
    primeiros = [mesa.jogador_da_vez()]
    for _ in range(2):
        mesa.iniciar_nova_mao()
        primeiros.append(mesa.jogador_da_vez())
    assert primeiros == jogadores                     # J0, J1, J2


def test_pm_03_so_se_compra_uma_vez_por_vez():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    assert mesa.pode_comprar()
    mesa.comprar_do_monte(jogador)
    assert not mesa.pode_comprar()
    assert len(jogador.mao) == 10


def test_pm_04_comprar_do_descarte_leva_a_carta_do_topo():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    topo = mesa.descarte[-1]
    comprada = mesa.comprar_do_descarte(jogador)
    assert comprada == topo and comprada in jogador.mao
    assert mesa.descarte == []


def test_pm_05_bater_descartando_so_com_as_9_restantes_fechadas():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    jogador.mao = cartas(PRONTA_9 + " 2o")
    mesa.comprou_nesta_vez = True
    assert not mesa.pode_bater_descartando(jogador, carta("4e"))   # tirar 4e desfaz a sequência
    assert mesa.bater_descartando(jogador, carta("4e")) is None
    assert len(jogador.mao) == 10 and jogador.vitorias == 0
    resultado = mesa.bater_descartando(jogador, carta("2o"))
    assert resultado is not None and resultado["vencedor"] == jogador.nome
    assert carta("2o") in mesa.descarte
    assert jogador.vitorias == 1


def test_pm_05_nao_se_bate_descartando_sem_ter_comprado():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    jogador.mao = cartas(PRONTA_9 + " 2o")
    assert not mesa.pode_bater_descartando(jogador, carta("2o"))


def test_pm_06_bater_da_uma_vitoria_e_ninguem_e_eliminado():
    mesa, jogadores = nova_mesa()
    batedor = mesa.jogador_da_vez()
    batedor.mao = cartas(PRONTA_10)
    mesa.comprou_nesta_vez = True
    assert mesa.pode_bater(batedor)
    resultado = mesa.bater(batedor)
    assert resultado["vitorias_ganhas"] == 1
    assert resultado["mao_fechada"] is False
    assert batedor.vitorias == 1
    assert all(j.vitorias == 0 for j in jogadores if j is not batedor)
    assert len(mesa.jogadores_na_mesa()) == len(jogadores)
    assert mesa.jogador_da_vez() is None              # a mão acabou


def test_pm_07_mao_fechada_vale_duas_vitorias():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    jogador.mao = cartas(PRONTA_9)
    assert mesa.pode_bater_mao_fechada(jogador)
    resultado = mesa.bater_mao_fechada(jogador)
    assert resultado["mao_fechada"] is True
    assert resultado["vitorias_ganhas"] == 2
    assert jogador.vitorias == 2


def test_pm_07_mao_fechada_com_mao_que_nao_fecha_e_recusada():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    jogador.mao = cartas("4e 5e 6e 7c 7o 7p 9c 10c Qc")
    assert not mesa.pode_bater_mao_fechada(jogador)
    assert mesa.bater_mao_fechada(jogador) is None
    assert jogador.vitorias == 0


def test_pm_08_depois_de_comprar_a_mao_fechada_nao_vale_mais():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    mesa.comprar_do_monte(jogador)
    jogador.mao = cartas(PRONTA_9)
    assert not mesa.pode_bater_mao_fechada(jogador)


def test_pm_08_a_janela_fecha_para_sempre_depois_da_primeira_vez_do_jogador():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    mesa.comprar_do_monte(jogador)
    mesa.descartar(jogador, jogador.mao[0])
    jogador.mao = cartas(PRONTA_9)
    assert not mesa.comprou_nesta_vez
    assert not mesa.pode_bater_mao_fechada(jogador)


def test_pm_09_tres_vitorias_encerram_a_partida():
    mesa, jogadores = nova_mesa()
    assert mesa.vencedor_do_jogo() is None and not mesa.jogo_tem_vencedor()
    jogadores[1].vitorias = VITORIAS_PARA_VENCER - 1
    assert mesa.vencedor_do_jogo() is None
    jogadores[1].vitorias = VITORIAS_PARA_VENCER
    assert mesa.vencedor_do_jogo() is jogadores[1]
    assert mesa.jogo_tem_vencedor()


def test_pm_10_mao_fechada_com_duas_vitorias_passa_do_limite_e_vence():
    """O placar não é limitado a 3: 2 + 2 = 4 e quem bateu vence."""
    mesa, jogadores = nova_mesa()
    jogador = mesa.jogador_da_vez()
    jogador.vitorias = 2
    jogador.mao = cartas(PRONTA_9)
    mesa.bater_mao_fechada(jogador)
    assert jogador.vitorias == 4
    assert mesa.vencedor_do_jogo() is jogador


def test_pm_11_monte_vazio_e_reciclado_do_descarte_e_o_topo_fica():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    mesa.monte = []
    mesa.descarte = cartas("2c 3c 4c 5c")
    comprada = mesa.comprar_do_monte(jogador)
    assert comprada in cartas("2c 3c 4c")
    assert mesa.descarte == cartas("5c")               # o topo não é reciclado
    assert len(mesa.monte) == 2


def test_pm_12_monte_e_descarte_esgotados_nunca_travam_o_turno():
    mesa, _ = nova_mesa()
    jogador = mesa.jogador_da_vez()
    mesa.monte = []
    mesa.descarte = cartas("5c")
    comprada = mesa.comprar_do_monte(jogador)         # força a compra do único descarte
    assert comprada == carta("5c")
    assert mesa.comprou_nesta_vez


def test_pm_13_duzentos_turnos_sem_bater_empatam_a_mao():
    mesa, jogadores = nova_mesa()
    for _turno in range(LIMITE_TURNOS_SEM_BATIDA):
        assert mesa.resultado_mao is None
        jogador = mesa.jogador_da_vez()
        mesa.comprar_do_monte(jogador)
        mesa.descartar(jogador, jogador.mao[0])
    assert mesa.resultado_mao["empate"] is True
    assert mesa.resultado_mao["vencedor"] is None
    assert all(j.vitorias == 0 for j in jogadores)


@pytest.mark.parametrize("usar_joker,total", [(False, 104), (True, 108)])
def test_pm_14_total_de_cartas_e_constante_durante_a_mao(usar_joker, total):
    mesa, _ = nova_mesa(4, usar_joker)
    for _ in range(150):
        jogador = mesa.jogador_da_vez()
        assert total_de_cartas(mesa) == total
        if mesa.pode_comprar():
            mesa.comprar_do_monte(jogador)
        assert total_de_cartas(mesa) == total
        mesa.descartar(jogador, jogador.mao[-1])
    assert total_de_cartas(mesa) == total
