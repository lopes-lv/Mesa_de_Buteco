"""DP-* — peças e distribuição do Dominó (domino/README.md, "Distribuição")."""
import pytest

from domino.domino_logic import DominoPlayer, DominoTable, Peca, criar_pecas


def test_dp_01_peca_normalizada_igualdade_e_hash():
    """Peca(3,5) e Peca(5,3) são a mesma peça."""
    assert Peca(3, 5) == Peca(5, 3)
    assert hash(Peca(3, 5)) == hash(Peca(5, 3))
    assert len({Peca(3, 5), Peca(5, 3)}) == 1


def test_dp_02_quatro_jogadores_tem_28_pecas_unicas():
    pecas = criar_pecas(4)
    assert len(pecas) == 28
    assert len(set(pecas)) == 28


def test_dp_02_tres_jogadores_tem_27_pecas_sem_a_zero_zero():
    pecas = criar_pecas(3)
    assert len(pecas) == 27
    assert len(set(pecas)) == 27
    assert Peca(0, 0) not in pecas


@pytest.mark.parametrize("quantidade,por_jogador", [(3, 9), (4, 7)])
def test_dp_03_distribuicao_exata_sem_sobra(quantidade, por_jogador):
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(quantidade)]
    mesa = DominoTable(jogadores)
    mesa.iniciar_nova_mao()
    assert all(len(j.mao) == por_jogador for j in jogadores)
    assert sum(len(j.mao) for j in jogadores) == len(criar_pecas(quantidade))


@pytest.mark.parametrize("quantidade", [3, 4])
def test_dp_04_nenhuma_peca_repetida_entre_jogadores(quantidade):
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(quantidade)]
    DominoTable(jogadores).iniciar_nova_mao()
    todas = [p for j in jogadores for p in j.mao]
    assert len(todas) == len(set(todas))


def test_dp_05_propriedades_da_peca():
    carroca, comum = Peca(4, 4), Peca(2, 6)
    assert carroca.eh_carroca and not comum.eh_carroca
    assert comum.pontos == 8
    assert comum.combina(2) and comum.combina(6) and not comum.combina(3)
    assert comum.outro_lado(2) == 6
    assert comum.outro_lado(6) == 2
    assert carroca.outro_lado(4) == 4
