"""HE-* — avaliador de mãos (holdem/hand_evaluator.py; holdem/README.md,
"Pote, side pots e empates": tuplas (categoria, desempates...))."""
from holdem.hand_evaluator import (NOME_CATEGORIA, _avaliar_5_cartas, comparar_maos,
                                   determinar_vencedores, melhor_mao)
from tests.helpers import cartas


def forca(texto):
    return _avaliar_5_cartas(cartas(texto))


def test_he_01_as_nove_categorias_estao_na_ordem_certa():
    ordem = [
        "2c 5o 9p Je Kc",     # carta alta
        "2c 2o 9p Je Kc",     # par
        "2c 2o 9p 9e Kc",     # dois pares
        "2c 2o 2p Je Kc",     # trinca
        "5c 6o 7p 8e 9c",     # sequência
        "2c 5c 9c Jc Kc",     # flush
        "2c 2o 2p Ke Kc",     # full house
        "2c 2o 2p 2e Kc",     # quadra
        "5c 6c 7c 8c 9c",     # straight flush
    ]
    forcas = [forca(m) for m in ordem]
    assert [f[0] for f in forcas] == list(range(1, 10))
    assert forcas == sorted(forcas)
    assert len(set(forcas)) == 9
    assert [NOME_CATEGORIA[f[0]] for f in forcas][-1] == "Straight Flush"


def test_he_02_a_roda_a_2_3_4_5_e_sequencia_de_topo_5():
    roda = forca("Ac 2o 3p 4e 5c")
    assert roda == (5, 5)
    assert roda < forca("2c 3o 4p 5e 6c")


def test_he_02_straight_flush_na_roda_perde_para_o_de_6_alto():
    assert forca("Ac 2c 3c 4c 5c") < forca("2c 3c 4c 5c 6c")


def test_he_03_q_k_a_2_3_nao_e_sequencia():
    assert forca("Qc Ko Ap 2e 3c")[0] == 1


def test_he_04_desempate_por_kicker():
    assert forca("9c 9o Ap 4e 2c") > forca("9p 9e Kc 4o 2o")


def test_he_05_dois_pares_compara_par_maior_depois_menor_depois_kicker():
    assert forca("Kc Ko 4p 4e 2c") > forca("Qc Qo Jp Je Ac")      # par maior
    assert forca("Kc Ko 4p 4e 2c") > forca("Kp Ke 3c 3o Ac")      # par menor
    assert forca("Kc Ko 4p 4e Ac") > forca("Kp Ke 4c 4o Qc")      # kicker


def test_he_06_full_house_a_trinca_pesa_mais_que_o_par():
    assert forca("3c 3o 3p 2e 2c") > forca("2c 2o 2p Ae Ac")


def test_he_07_com_sete_cartas_escolhe_as_cinco_melhores():
    mao = cartas("Ac Kc") + cartas("Qc Jc 10c 2o 3p")
    valor, categoria, escolhidas = melhor_mao(mao)
    assert categoria == "Straight Flush"
    assert valor == (9, 14)
    assert len(escolhidas) == 5


def test_he_07_par_da_mesa_melhora_com_a_mao():
    _, categoria, _ = melhor_mao(cartas("Ac Ao") + cartas("Ap Ke Qc 4o 2p"))
    assert categoria == "Trinca"


def test_he_08_maos_iguais_em_valor_empatam():
    mesa = "Kp Qo 9c 5e 2o"
    avaliadas = comparar_maos({1: cartas("Ac 3o") + cartas(mesa), 2: cartas("Ao 3c") + cartas(mesa)})
    assert sorted(determinar_vencedores(avaliadas)) == [1, 2]


def test_he_08_mao_melhor_vence_sozinha():
    mesa = "Kp Qo 9c 5e 2o"
    avaliadas = comparar_maos({1: cartas("Ac Ao") + cartas(mesa), 2: cartas("Ac 3o") + cartas(mesa)})
    assert determinar_vencedores(avaliadas) == [1]


def test_he_09_flush_compara_carta_a_carta_da_mais_alta_para_a_mais_baixa():
    assert forca("Ac 9c 7c 4c 2c") > forca("Kc Qc Jc 9c 7c")
    assert forca("Ac Kc 7c 4c 2c") > forca("Ac Kc 7c 3c 2c")
