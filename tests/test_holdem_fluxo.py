"""HF-* — fluxo de uma mão e torneio (holdem/README.md, "Fluxo de uma mão",
"Blinds" e "Eliminação e espectador")."""
import inspect

import pytest

from holdem import game_logic
from holdem.game_logic import ESTRUTURA_BLINDS, MAOS_POR_NIVEL, BettingRound, Player, Table


def nova_mesa(quantidade=4, stack=1500):
    jogadores = [Player(i, f"J{i}", stack=stack) for i in range(quantidade)]
    return Table(jogadores), jogadores


def test_hf_01_blinds_saem_dos_assentos_certos_e_o_primeiro_a_agir_vem_depois():
    mesa, j = nova_mesa(4)
    mesa.iniciar_nova_mao()
    assert mesa.dealer_idx == 0
    assert j[1].aposta_rodada == 10 and j[1].stack == 1490      # small blind
    assert j[2].aposta_rodada == 20 and j[2].stack == 1480      # big blind
    assert mesa.rodada_atual.jogador_da_vez() is j[3]


def test_hf_01_com_tres_jogadores_o_dealer_age_primeiro_no_pre_flop():
    mesa, j = nova_mesa(3)
    mesa.iniciar_nova_mao()
    assert mesa.rodada_atual.jogador_da_vez() is j[0]


def test_hf_02_dois_cartas_para_cada_e_nenhuma_repetida():
    mesa, j = nova_mesa(6)
    mesa.iniciar_nova_mao()
    assert all(len(x.mao) == 2 for x in j)
    todas = [c for x in j for c in x.mao] + mesa.deck.cartas
    assert len(todas) == 52 - 0 and len(set(todas)) == 52


def test_hf_03_flop_turn_river_e_showdown():
    mesa, _ = nova_mesa(3)
    mesa.iniciar_nova_mao()
    quantidades = []
    for _ in range(3):
        mesa.avancar_estagio()
        quantidades.append((mesa.estagio, len(mesa.comunitarias)))
    assert quantidades == [("flop", 3), ("turn", 4), ("river", 5)]
    mesa.avancar_estagio()
    assert mesa.estagio == "showdown"


def test_hf_04_o_dealer_avanca_a_cada_mao():
    mesa, _ = nova_mesa(4)
    posicoes = []
    for _ in range(5):
        mesa.iniciar_nova_mao()
        posicoes.append(mesa.dealer_idx)
    assert posicoes == [0, 1, 2, 3, 0]


def test_hf_04_o_dealer_pula_quem_foi_eliminado():
    mesa, j = nova_mesa(4)
    mesa.iniciar_nova_mao()
    assert mesa.dealer_idx == 0
    j[1].stack = 0
    mesa.iniciar_nova_mao()
    assert mesa.dealer_idx == 2


@pytest.mark.xfail(reason="BUG (off-by-one): o nível sobe na 5ª mão, não na 6ª. iniciar_nova_mao "
                          "incrementa mao_numero e depois faz mao_numero // MAOS_POR_NIVEL, então o "
                          "nível 10/20 dura só 4 mãos. README: o nível sobe a cada 5 mãos.")
def test_hf_05_cada_nivel_de_blind_dura_cinco_maos():
    mesa, _ = nova_mesa(3)
    niveis = []
    for _ in range(MAOS_POR_NIVEL * 2):
        mesa.iniciar_nova_mao()
        niveis.append(mesa.blinds_atuais())
    assert niveis == [ESTRUTURA_BLINDS[0]] * MAOS_POR_NIVEL + [ESTRUTURA_BLINDS[1]] * MAOS_POR_NIVEL


def test_hf_05_o_nivel_nunca_diminui_e_para_em_400_800():
    mesa, _ = nova_mesa(3, stack=10 ** 9)
    anterior = (0, 0)
    for _ in range(80):
        mesa.iniciar_nova_mao()
        atual = mesa.blinds_atuais()
        assert atual >= anterior
        anterior = atual
    assert anterior == (400, 800) == ESTRUTURA_BLINDS[-1]


def test_hf_05_a_primeira_mao_comeca_em_10_20():
    mesa, _ = nova_mesa(3)
    mesa.iniciar_nova_mao()
    assert mesa.blinds_atuais() == (10, 20)


def test_hf_06_stack_zero_elimina_e_um_so_jogador_encerra_o_jogo():
    mesa, j = nova_mesa(3)
    assert not mesa.jogo_tem_vencedor()
    j[0].stack = 0
    j[1].stack = 0
    mesa.marcar_eliminados()
    assert j[0].eliminado and j[1].eliminado and not j[2].eliminado
    assert mesa.jogo_tem_vencedor()
    assert mesa.jogadores_na_mesa() == [j[2]]


def test_hf_07_heads_up_roda_uma_mao_inteira_sem_travar():
    mesa, j = nova_mesa(2)
    mesa.iniciar_nova_mao()
    total = sum(x.stack + x.total_apostado_mao for x in j)
    while mesa.estagio != "showdown":
        r = mesa.rodada_atual
        passos = 0
        while not r.rodada_terminou():
            jogador = r.jogador_da_vez()
            r.aplicar_acao(jogador, "call" if r.aposta_alvo > jogador.aposta_rodada else "check")
            passos += 1
            assert passos < 20
        mesa.avancar_estagio()
    mesa.processar_showdown()
    assert sum(x.stack for x in j) == total


def test_hf_08_motor_nao_le_o_tipo_do_jogador():
    for objeto in (Table, BettingRound):
        codigo = inspect.getsource(objeto)
        assert ".tipo" not in codigo and ".is_bot" not in codigo
    assert game_logic.BettingRound is BettingRound
