"""HP-* — pote principal, side pots e showdown (holdem/README.md,
"Pote, side pots e empates")."""
import pytest

from holdem.game_logic import Player, Table, calcular_potes
from tests.helpers import cartas


def apostadores(*totais, foldaram=()):
    jogadores = []
    for i, total in enumerate(totais):
        j = Player(i, f"J{i}", stack=1000)
        j.total_apostado_mao = total
        j.foldou = i in foldaram
        jogadores.append(j)
    return jogadores


def mesa_no_showdown(maos, comunitarias, apostado, foldaram=(), ids=None):
    """Mesa pronta para `processar_showdown`: mãos/apostas escolhidas a dedo,
    dealer no assento 0. As fichas iniciais são 1000 menos o apostado."""
    ids = ids or list(range(len(maos)))
    jogadores = []
    for i, (mao, total) in enumerate(zip(maos, apostado)):
        j = Player(ids[i], f"J{i}", stack=1000 - total)
        j.mao = cartas(mao)
        j.total_apostado_mao = total
        j.foldou = i in foldaram
        jogadores.append(j)
    mesa = Table(jogadores)
    mesa.comunitarias = cartas(comunitarias)
    mesa.dealer_idx = 0
    return mesa, jogadores


def test_hp_01_sem_all_in_ha_um_pote_so():
    potes = calcular_potes(apostadores(100, 100, 100))
    assert potes == [{"valor": 300, "elegiveis": [0, 1, 2]}]


def test_hp_01_sem_apostas_nao_ha_potes():
    assert calcular_potes(apostadores(0, 0, 0)) == []


def test_hp_02_um_all_in_curto_cria_pote_principal_e_side_pot():
    potes = calcular_potes(apostadores(50, 100, 100))
    assert potes == [{"valor": 150, "elegiveis": [0, 1, 2]},
                     {"valor": 100, "elegiveis": [1, 2]}]


def test_hp_03_tres_all_ins_de_valores_diferentes_criam_tres_potes():
    potes = calcular_potes(apostadores(30, 60, 100))
    assert potes == [{"valor": 90, "elegiveis": [0, 1, 2]},
                     {"valor": 60, "elegiveis": [1, 2]},
                     {"valor": 40, "elegiveis": [2]}]


def test_hp_04_potes_consecutivos_com_os_mesmos_elegiveis_sao_fundidos():
    # j0 desistiu depois de apostar 50: os dois níveis têm os mesmos elegíveis [1, 2]
    potes = calcular_potes(apostadores(50, 100, 100, foldaram=(0,)))
    assert potes == [{"valor": 250, "elegiveis": [1, 2]}]


@pytest.mark.parametrize("totais,foldaram", [
    ((100, 100, 100), ()), ((50, 100, 100), ()), ((30, 60, 100), ()),
    ((50, 100, 100), (0,)), ((10, 20, 30, 40, 50), (1, 3)),
])
def test_hp_05_a_soma_dos_potes_e_o_total_apostado_inclusive_de_quem_desistiu(totais, foldaram):
    potes = calcular_potes(apostadores(*totais, foldaram=foldaram))
    assert sum(p["valor"] for p in potes) == sum(totais)


def test_hp_06_quem_desistiu_paga_mas_nao_e_elegivel():
    potes = calcular_potes(apostadores(100, 100, 100, foldaram=(1,)))
    assert potes == [{"valor": 300, "elegiveis": [0, 2]}]


def test_hp_07_empate_divide_o_pote_e_o_resto_vai_para_quem_esta_perto_do_dealer():
    # J2 desistiu pondo 1 ficha: pote de 101 entre J0 e J1 empatados -> 51 e 50.
    # Dealer no assento 0, então J1 é o primeiro depois dele e fica com a ficha extra.
    mesa, j = mesa_no_showdown(["Ac 3o", "Ao 3c", "2c 7p"], "Kp Qo 9c 5e 2o",
                               apostado=[50, 50, 1], foldaram=(2,))
    inicio = [x.stack for x in j]
    resultado = mesa.processar_showdown()
    ganhos = [x.stack - s for x, s in zip(j, inicio)]
    assert ganhos == [50, 51, 0]
    assert resultado[0]["pote"] == 101
    assert set(resultado[0]["vencedores"]) == {"J0", "J1"}


def test_hp_08_o_vencedor_do_principal_pode_perder_o_side_pot():
    # J0 (all-in curto) tem trinca de reis; J1 tem par de ases; J2 par de damas
    mesa, j = mesa_no_showdown(["Kp Ko", "Ac Ao", "Qc Qo"], "Kc 7o 9p 2e 3c", apostado=[50, 100, 100])
    inicio = [x.stack for x in j]
    mesa.processar_showdown()
    ganhos = [x.stack - s for x, s in zip(j, inicio)]
    assert ganhos == [150, 100, 0]


def test_hp_09_se_todos_desistem_menos_um_ele_leva_tudo_sem_mostrar_a_mao():
    mesa, j = mesa_no_showdown(["Ac Ao", "2c 7o", "3c 8o"], "Kc 7p 9p 2e 3o",
                               apostado=[100, 60, 30], foldaram=(1, 2))
    inicio = j[0].stack
    resultado = mesa.processar_showdown()
    assert j[0].stack - inicio == 190
    assert resultado[0]["vencedores"] == ["J0"]


def test_hp_10_o_showdown_funciona_com_ids_que_nao_sao_a_posicao_do_assento():
    mesa, j = mesa_no_showdown(["Ac Ao", "2c 7o", "3c 8o"], "Kc 7p 9p 2e 3o",
                               apostado=[100, 100, 100], ids=[3, 7, 9])
    mesa.processar_showdown()
    assert sum(x.stack for x in j) == 3000


def test_hp_11_a_soma_das_fichas_nao_muda_no_showdown():
    mesa, j = mesa_no_showdown(["Kp Ko", "Ac Ao", "Qc Qo", "2o 4o"], "Kc 7o 9p 2e 3c",
                               apostado=[50, 100, 100, 80], foldaram=(3,))
    total = sum(x.stack + x.total_apostado_mao for x in j)
    mesa.processar_showdown()
    assert sum(x.stack for x in j) == total
