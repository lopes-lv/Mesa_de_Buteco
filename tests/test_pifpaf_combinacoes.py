"""PC-* — combinações do Pif Paf (pifpaf/README.md, "Combinações válidas" e "Bater").

Convenção das cartas nos testes (tests/helpers.py): valor + naipe, ex. 'Ae'
(Ás de espadas), '10c', 'Kp'; '*' é o Joker.
"""
from collections import Counter

import pytest

from pifpaf.pifpaf_logic import (JOKERS_POR_BARALHO_DUPLO, agrupar_para_bater,
                                 calcular_pontos_soltos, carta_completa_combinacao,
                                 criar_baralho_duplo, pode_bater_mao, valor_pontos)
from tests.helpers import carta, cartas


def test_pc_01_trinca_e_quadra_de_naipes_diferentes_sao_validas():
    assert pode_bater_mao(cartas("7c 7o 7p"))
    assert pode_bater_mao(cartas("7c 7o 7p 7e"))


def test_pc_02_mesmo_valor_com_naipe_repetido_nao_e_trinca():
    assert not pode_bater_mao(cartas("7c 7c 7o"))
    assert not pode_bater_mao(cartas("7c 7c 7c"))


def test_pc_03_sequencia_de_tres_ou_mais_do_mesmo_naipe():
    assert pode_bater_mao(cartas("4e 5e 6e"))
    assert pode_bater_mao(cartas("4e 5e 6e 7e 8e"))
    assert not pode_bater_mao(cartas("4e 5e 7e"))      # buraco
    assert not pode_bater_mao(cartas("4e 5e 6o"))      # naipe diferente


def test_pc_04_o_as_vale_alto_e_baixo():
    assert pode_bater_mao(cartas("Qe Ke Ae"))
    assert pode_bater_mao(cartas("Ae 2e 3e"))


def test_pc_05_nunca_liga_rei_as_dois():
    assert not pode_bater_mao(cartas("Ke Ae 2e"))
    assert not pode_bater_mao(cartas("Qe Ke Ae 2e"))


def test_pc_06_o_joker_completa_trinca_e_sequencia():
    assert pode_bater_mao(cartas("7c 7o *"))           # trinca
    assert pode_bater_mao(cartas("4e 6e *"))           # sequência com buraco
    assert pode_bater_mao(cartas("7c 7o 7p *"))        # quadra com Joker


@pytest.mark.parametrize("texto", ["4e 5e *", "Ke Ae *", "Ae 2e *"])
def test_pc_06_o_joker_estende_a_ponta_de_uma_sequencia(texto):
    assert pode_bater_mao(cartas(texto))


def test_pc_06_joker_com_so_uma_carta_natural_nao_forma_grupo():
    assert not pode_bater_mao(cartas("4e 9o *"))
    assert not pode_bater_mao(cartas("4e *"))


def test_pc_07_bater_exige_zero_sobras():
    pronta = cartas("4e 5e 6e 7c 7o 7p 9c 10c Jc")
    assert pode_bater_mao(pronta)
    com_sobra = cartas("4e 5e 6e 7c 7o 7p 9c 10c Qc")
    assert not pode_bater_mao(com_sobra)


def test_pc_08_agrupar_para_bater_usa_exatamente_as_cartas_da_mao():
    mao = cartas("4e 5e 6e 7c 7o 7p 9c 10c Jc")
    grupos = agrupar_para_bater(mao)
    assert grupos is not None
    achatadas = [c for g in grupos for c in g]
    assert Counter(map(repr, achatadas)) == Counter(map(repr, mao))
    assert all(len(g) >= 3 for g in grupos)


def test_pc_08_agrupar_para_bater_devolve_none_quando_nao_fecha():
    assert agrupar_para_bater(cartas("4e 5e 6e 7c 7o 7p 9c 10c Qc")) is None


def test_pc_09_pontos_das_cartas_soltas():
    assert valor_pontos(carta("2c")) == 2
    assert valor_pontos(carta("10c")) == 10
    for figura in ("Jc", "Qc", "Kc"):
        assert valor_pontos(carta(figura)) == 10
    assert valor_pontos(carta("Ac")) == 15
    assert valor_pontos(carta("*")) == 20


def test_pc_09_calcular_pontos_soltos_soma_so_o_que_nao_combina():
    _, soltas, pontos = calcular_pontos_soltos(cartas("2c 5o Jp Qe Kc Ac"))
    assert len(soltas) == 6
    assert pontos == 2 + 5 + 10 + 10 + 10 + 15
    _, soltas, pontos = calcular_pontos_soltos(cartas("2c 5o *"))
    assert pontos == 2 + 5 + 20                         # o Joker sem grupo vale 20


def test_pc_09_carta_que_combina_nao_conta_como_solta():
    grupos, soltas, pontos = calcular_pontos_soltos(cartas("7c 7o 7p Kc"))
    assert pontos == 10
    assert len(grupos) == 1


def test_pc_10_duplicata_do_segundo_baralho_fica_livre_para_outro_grupo():
    # 7c aparece duas vezes: uma na trinca, outra na sequência 7-8-9 de copas
    assert pode_bater_mao(cartas("7c 7o 7p 7c 8c 9c"))


def test_pc_10_duplicata_sem_uso_fica_como_solta():
    _, soltas, pontos = calcular_pontos_soltos(cartas("7c 7c 7o 7p"))
    assert pontos == 7


def test_pc_11_tamanho_do_baralho_duplo():
    assert len(criar_baralho_duplo()) == 104
    com_joker = criar_baralho_duplo(usar_joker=True)
    assert len(com_joker) == 104 + JOKERS_POR_BARALHO_DUPLO == 108
    assert sum(1 for c in com_joker if c.naipe == "coringa") == 4


def test_pc_12_carta_completa_combinacao():
    mao = cartas("7c 7o 2e 9p")
    assert carta_completa_combinacao(carta("7p"), mao)       # fecha trinca
    assert not carta_completa_combinacao(carta("Ke"), mao)
    assert carta_completa_combinacao(carta("*"), mao)        # Joker sempre ajuda
