"""DB-* — IA dos bots do Dominó (domino/README.md, "IA dos bots")."""
import random

from domino.domino_bot_ai import escolher_jogada_bot
from domino.domino_logic import DominoPlayer, DominoTable, Peca
from tests.helpers import jogar, mesa_domino


def test_db_01_sem_jogada_devolve_none():
    mesa, (a, b, _c) = mesa_domino("4-4 0-1", "2-2 3-3", "5-5")
    jogar(mesa, a, "4-4")
    assert escolher_jogada_bot(b, mesa) is None


def test_db_02_prefere_a_jogada_que_pontua():
    # 4-2 na esquerda deixa 2 + 8 = 10 (pontua); 4-6 deixa 6 + 8 = 14 (não pontua, mas tem mais pontos)
    mesa, (a, b, _c) = mesa_domino("4-4 0-1", "4-6 4-2", "5-5")
    jogar(mesa, a, "4-4")
    peca, _ = escolher_jogada_bot(b, mesa)
    assert peca == Peca(4, 2)


def test_db_03_sem_pontuar_prefere_carroca_e_depois_a_maior_peca():
    # esquerda 1 (6-1), direita 6 (carroça de abertura 6-6)
    mesa, (a, b, c) = mesa_domino("6-6 0-0", "6-1 0-3", "1-1 1-5 6-3")
    jogar(mesa, a, "6-6")
    jogar(mesa, b, "6-1", "esquerda")
    peca, _ = escolher_jogada_bot(c, mesa)
    assert peca == Peca(1, 1)                  # carroça antes das outras

    c.mao = [Peca(1, 5), Peca(6, 3)]
    peca, _ = escolher_jogada_bot(c, mesa)
    assert peca == Peca(6, 3)                  # a de maior valor (9 contra 6)


def test_db_04_a_jogada_devolvida_sempre_esta_entre_as_possiveis():
    for semente in range(20):
        random.seed(semente)
        jogadores = [DominoPlayer(i, f"J{i}") for i in range(4)]
        mesa = DominoTable(jogadores)
        mesa.iniciar_nova_mao()
        for _ in range(300):
            if mesa.resultado_mao is not None:
                break
            jogador = mesa.jogador_da_vez()
            escolha = escolher_jogada_bot(jogador, mesa)
            if escolha is None:
                assert not mesa.jogadas_possiveis(jogador)
                mesa.passar(jogador)
            else:
                assert escolha in mesa.jogadas_possiveis(jogador)
                assert mesa.jogar(jogador, *escolha)
