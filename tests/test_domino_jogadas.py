"""DJ-* — abertura, encaixe, spinner e bucho (domino/README.md, "Abertura" e
"A mesa em cruz")."""
import pytest

from domino.domino_logic import DominoPlayer, DominoTable, Peca, jogadas_possiveis_em
from tests.helpers import jogar, mesa_domino, pecas


def _dono_da_seis_seis(jogadores):
    return next(j for j in jogadores if Peca(6, 6) in j.mao)


@pytest.mark.parametrize("quantidade", [3, 4])
def test_dj_01_primeira_mao_quem_tem_6_6_abre_so_com_ela(quantidade):
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(quantidade)]
    mesa = DominoTable(jogadores)
    mesa.iniciar_nova_mao()
    dono = _dono_da_seis_seis(jogadores)
    assert mesa.jogador_da_vez() is dono
    assert mesa.jogadas_possiveis(dono) == [(Peca(6, 6), "esquerda")]
    outra = next(p for p in dono.mao if p != Peca(6, 6))
    assert not mesa.jogar(dono, outra, "esquerda")
    assert mesa.mesa_vazia()


def test_dj_02_demais_maos_o_vencedor_anterior_abre_com_qualquer_carroca():
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(3)]
    mesa = DominoTable(jogadores)
    mesa.forcar_abertura_6_6 = False
    mesa.ultimo_vencedor_id = jogadores[2].id
    mesa.iniciar_nova_mao()
    assert mesa.jogador_da_vez() is jogadores[2]
    jogadores[2].mao = pecas("2-2 5-5 1-3")
    jogadas = mesa.jogadas_possiveis(jogadores[2])
    assert {p for p, _ in jogadas} == {Peca(2, 2), Peca(5, 5)}


def test_dj_03_sem_carroca_na_mao_a_abertura_e_livre():
    mesa, (a, *_) = mesa_domino("1-2 3-4", "0-5", "1-6")
    assert {p for p, _ in mesa.jogadas_possiveis(a)} == {Peca(1, 2), Peca(3, 4)}
    assert mesa.jogar(a, Peca(1, 2), "esquerda")


def test_dj_04_abrir_com_peca_comum_tendo_carroca_e_recusado():
    mesa, (a, *_) = mesa_domino("1-2 3-3", "0-5", "1-6")
    assert not mesa.jogar(a, Peca(1, 2), "esquerda")
    assert mesa.mesa_vazia()
    assert Peca(1, 2) in a.mao


def test_dj_05_depois_do_bloqueio_total_a_abertura_volta_a_ser_6_6():
    mesa, (a, b, c) = mesa_domino("4-4 0-1", "2-3", "5-5 0-2")
    jogar(mesa, a, "4-4")
    mesa.passar(b)
    mesa.passar(c)
    mesa.passar(a)
    assert mesa.resultado_mao["tipo"] == "bloqueio_total"
    assert mesa.forcar_abertura_6_6
    mesa.iniciar_nova_mao()
    assert mesa.peca_obrigatoria == Peca(6, 6)


def test_dj_06_peca_que_nao_encaixa_e_recusada():
    mesa, (a, b, _c) = mesa_domino("4-4 0-1", "1-2 0-3", "5-5")
    jogar(mesa, a, "4-4")
    assert not mesa.jogar(b, Peca(1, 2), "esquerda")
    assert Peca(1, 2) in b.mao


def test_dj_07_abertura_com_carroca_cria_spinner_e_sem_carroca_nao():
    mesa, (a, *_) = mesa_domino("4-4 0-1", "2-3", "5-5")
    jogar(mesa, a, "4-4")
    assert mesa.eh_spinner
    assert mesa.extremidades["cima"] == 4 and mesa.extremidades["baixo"] == 4

    mesa2, (a2, *_) = mesa_domino("1-2 0-3", "2-3", "5-5")
    jogar(mesa2, a2, "1-2")
    assert not mesa2.eh_spinner
    assert mesa2.extremidades["cima"] is None and mesa2.extremidades["baixo"] is None


def test_dj_08_bucho_so_libera_com_peca_dos_dois_lados():
    mesa, (a, b, c) = mesa_domino("4-4 4-3 0-0", "4-1 4-6", "4-2 5-5")
    jogar(mesa, a, "4-4")
    assert all(d in ("esquerda", "direita") for _, d in mesa.jogadas_possiveis(b))
    assert not mesa.jogar(b, Peca(4, 1), "cima")        # bucho ainda fechado
    jogar(mesa, b, "4-1", "esquerda")
    assert all(d in ("esquerda", "direita") for _, d in mesa.jogadas_possiveis(c))
    assert not mesa.jogar(c, Peca(4, 2), "baixo")       # só um lado jogado
    jogar(mesa, c, "4-2", "direita")
    direcoes = {d for _, d in mesa.jogadas_possiveis(a)}
    assert {"cima", "baixo"} <= direcoes                # agora liberou
    assert mesa.jogar(a, Peca(4, 3), "cima")


def test_dj_09_pontas_iguais_sem_spinner_nao_duplicam_jogadas():
    extremidades = {"esquerda": 3, "direita": 3, "cima": None, "baixo": None}
    jogadas = jogadas_possiveis_em(pecas("3-5"), extremidades, eh_spinner=False)
    assert jogadas == [(Peca(3, 5), "esquerda")]


def test_dj_09_com_spinner_ha_uma_jogada_por_direcao():
    extremidades = {"esquerda": 4, "direita": 4, "cima": 4, "baixo": 4}
    jogadas = jogadas_possiveis_em(pecas("4-1"), extremidades, eh_spinner=True)
    assert sorted(d for _, d in jogadas) == ["baixo", "cima", "direita", "esquerda"]


def test_dj_10_carroca_jogada_depois_nao_cria_ramo_novo():
    mesa, (a, b, _c) = mesa_domino("1-2 0-3", "2-2 5-5", "2-6")
    jogar(mesa, a, "1-2")
    jogar(mesa, b, "2-2", "direita")
    assert not mesa.eh_spinner
    assert mesa.ramos["cima"] == [] and mesa.ramos["baixo"] == []
    assert mesa.extremidades["cima"] is None


def test_dj_11_peca_fora_da_mao_e_recusada():
    mesa, (a, *_) = mesa_domino("4-4", "2-3", "5-5")
    assert not mesa.jogar(a, Peca(6, 6), "esquerda")
    assert mesa.mesa_vazia()


@pytest.mark.xfail(reason="Defesa em profundidade: DominoTable.jogar() aceita jogada de qualquer jogador; "
                          "quem confere a vez é a tela do host (ver HV-10), não o motor.")
def test_dj_12_jogar_fora_da_vez_e_recusado():
    mesa, (a, b, c) = mesa_domino("4-4 0-1", "4-1 2-3", "4-2 5-5")
    jogar(mesa, a, "4-4")
    assert mesa.jogador_da_vez() is b
    assert not mesa.jogar(c, Peca(4, 2), "esquerda")
    assert Peca(4, 2) in c.mao


@pytest.mark.xfail(reason="Defesa em profundidade: DominoTable.passar() aceita passe de quem tem peça que "
                          "encaixa; quem confere é a tela do host (ver HV-11), não o motor.")
def test_dj_13_passar_com_jogada_possivel_e_recusado():
    mesa, (a, b, _c) = mesa_domino("4-4 0-1", "4-1 2-3", "5-5")
    jogar(mesa, a, "4-4")
    assert mesa.pode_jogar(b)
    antes = (a.pontuacao, mesa.passes_consecutivos, mesa.indice_da_vez)
    mesa.passar(b)
    assert (a.pontuacao, mesa.passes_consecutivos, mesa.indice_da_vez) == antes
