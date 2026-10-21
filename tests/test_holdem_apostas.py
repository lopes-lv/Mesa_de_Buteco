"""HA-* — rodada de apostas (holdem/game_logic.py, BettingRound; holdem/README.md,
"Fluxo de uma mão")."""
import pytest

from holdem.game_logic import BettingRound, Player


def rodada(aposta_minima=20, stacks=(1000, 1000, 1000)):
    jogadores = [Player(i, f"J{i}", stack=s) for i, s in enumerate(stacks)]
    return BettingRound(jogadores, list(range(len(jogadores))), 0, aposta_minima), jogadores


def agir(r, jogadores, *acoes):
    """Cada ação é (indice_do_jogador, 'call'), (i, 'raise', valor)..."""
    for item in acoes:
        r.aplicar_acao(jogadores[item[0]], *item[1:])


def test_ha_01_so_termina_quando_todos_agiram_e_igualaram():
    r, j = rodada()
    agir(r, j, (0, "call"), (1, "call"))
    assert not r.rodada_terminou()
    agir(r, j, (2, "call"))
    assert r.rodada_terminou()
    assert r.jogador_da_vez() is None


def test_ha_01_todos_dando_check_sem_aposta_termina():
    r, j = rodada(aposta_minima=0)
    agir(r, j, (0, "check"), (1, "check"))
    assert not r.rodada_terminou()
    agir(r, j, (2, "check"))
    assert r.rodada_terminou()


def test_ha_02_raise_reabre_a_acao_para_quem_ja_agiu():
    r, j = rodada()
    agir(r, j, (0, "call"), (1, "raise", 20))
    assert r.jogador_da_vez() is j[2]
    agir(r, j, (2, "call"))
    assert r.jogador_da_vez() is j[0]                 # j0 precisa responder ao raise
    assert not r.rodada_terminou()
    agir(r, j, (0, "call"))
    assert r.rodada_terminou()
    assert {x.aposta_rodada for x in j} == {40}


def test_ha_03_fold_tira_o_jogador_e_sobrando_um_a_rodada_acaba():
    r, j = rodada()
    agir(r, j, (0, "fold"))
    assert j[0] not in r.jogadores_ativos_na_mao()
    assert not r.rodada_terminou()
    agir(r, j, (1, "fold"))
    assert r.rodada_terminou()


def test_ha_04_call_com_stack_menor_vira_all_in_sem_stack_negativo():
    r, j = rodada(stacks=(1000, 15, 1000))
    agir(r, j, (0, "call"), (1, "call"))
    assert j[1].stack == 0 and j[1].all_in
    assert j[1].aposta_rodada == 15
    assert all(x.stack >= 0 for x in j)


def test_ha_05_quem_esta_all_in_nao_e_mais_chamado_a_agir():
    r, j = rodada(stacks=(1000, 15, 1000))
    agir(r, j, (0, "call"), (1, "call"), (2, "call"))
    assert r.rodada_terminou()
    r2, j2 = rodada(aposta_minima=0, stacks=(1000, 15, 1000))
    agir(r2, j2, (0, "raise", 100))                   # j1 não consegue cobrir e fica all-in
    agir(r2, j2, (1, "call"))
    assert j2[1].all_in
    assert r2.jogador_da_vez() is j2[2]
    agir(r2, j2, (2, "call"))
    assert r2.rodada_terminou()


def test_ha_06_raise_atualiza_aposta_alvo_e_ultimo_raise():
    r, j = rodada(aposta_minima=20)
    agir(r, j, (0, "raise", 50))
    assert r.ultimo_raise_valor == 50
    assert r.aposta_alvo == 70                        # 20 a pagar + 50 de raise
    assert j[0].aposta_rodada == 70


def _estado(r, jogadores):
    return ([(x.stack, x.aposta_rodada, x.foldou) for x in jogadores],
            set(r.jogadores_que_agiram), r.indice_atual)


def _tentar(r, jogador, *acao):
    try:
        r.aplicar_acao(jogador, *acao)
    except (ValueError, AssertionError):
        pass


@pytest.mark.xfail(reason="Defesa em profundidade: BettingRound.aplicar_acao aceita check com aposta aberta; "
                          "quem confere é a tela do host (ver HV-02), não o motor.")
def test_ha_07_check_com_aposta_aberta_e_recusado():
    r, j = rodada(aposta_minima=20)
    antes = _estado(r, j)
    _tentar(r, j[0], "check")
    assert _estado(r, j) == antes


@pytest.mark.xfail(reason="O motor aceita raise menor que o mínimo (o último raise, ou o big blind) e o host "
                          "também não confere (ver HV-07).")
def test_ha_07_raise_abaixo_do_minimo_e_recusado():
    r, j = rodada(aposta_minima=20)
    antes = _estado(r, j)
    _tentar(r, j[0], "raise", 5)
    assert _estado(r, j) == antes


@pytest.mark.xfail(reason="Defesa em profundidade: o motor aceita ação de quem não é da vez; quem confere "
                          "é a tela do host (ver HV-01).")
def test_ha_07_acao_fora_da_vez_e_recusada():
    r, j = rodada(aposta_minima=20)
    antes = _estado(r, j)
    _tentar(r, j[2], "call")
    assert _estado(r, j) == antes
