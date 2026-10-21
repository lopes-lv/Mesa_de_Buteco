"""PB-* — IA dos bots do Pif Paf (pifpaf/README.md, "IA dos bots")."""
import random

from pifpaf.pifpaf_bot_ai import decidir_fonte_compra_bot, escolher_descarte_bot
from pifpaf.pifpaf_logic import PifPafPlayer, PifPafTable, eh_coringa
from tests.helpers import carta, cartas


def mesa_com_um_bot(mao, descarte):
    jogadores = [PifPafPlayer(i, f"B{i}") for i in range(3)]
    mesa = PifPafTable(jogadores)
    mesa.iniciar_nova_mao()
    bot = jogadores[0]
    bot.mao = cartas(mao)
    mesa.descarte = cartas(descarte) if descarte else []
    return mesa, bot


def test_pb_01_descarte_vazio_obriga_a_comprar_do_monte():
    mesa, bot = mesa_com_um_bot("7c 7o 2e 9p Kc 3o 5e Jo 4p", "")
    assert decidir_fonte_compra_bot(bot, mesa) == "monte"


def test_pb_01_so_devolve_monte_ou_descarte():
    for topo in ("7p", "Ac", "2e", "*"):
        mesa, bot = mesa_com_um_bot("7c 7o 2e 9p Kc 3o 5e Jo 4p", topo)
        assert decidir_fonte_compra_bot(bot, mesa) in ("monte", "descarte")


def test_pb_02_compra_do_descarte_quando_a_carta_forma_grupo():
    mesa, bot = mesa_com_um_bot("7c 7o 2e 9p Kc 3o 5e Jo 4p", "7p")
    assert decidir_fonte_compra_bot(bot, mesa) == "descarte"


def test_pb_02_nao_compra_do_descarte_carta_que_nao_ajuda():
    mesa, bot = mesa_com_um_bot("7c 7o 2e 9p Kc 3o 5e Jo 4p", "Ac")
    assert decidir_fonte_compra_bot(bot, mesa) == "monte"


def test_pb_03_o_descarte_escolhido_esta_sempre_na_mao():
    for semente in range(40):
        random.seed(semente)
        jogadores = [PifPafPlayer(i, f"B{i}") for i in range(3)]
        mesa = PifPafTable(jogadores, usar_joker=bool(semente % 2))
        mesa.iniciar_nova_mao()
        bot = mesa.jogador_da_vez()
        mesa.comprar_do_monte(bot)
        assert escolher_descarte_bot(bot, mesa) in bot.mao


def test_pb_04_nunca_descarta_o_joker_havendo_outra_carta():
    mesa, bot = mesa_com_um_bot("* 2c 9o Kp", "")
    descarte = escolher_descarte_bot(bot, mesa)
    assert not eh_coringa(descarte)


def test_pb_05_descarta_a_solta_de_maior_valor():
    mesa, bot = mesa_com_um_bot("7c 7o 7p 4e 5e 6e Kc 9o 2p", "")
    assert escolher_descarte_bot(bot, mesa) == carta("Kc")
    mesa, bot = mesa_com_um_bot("7c 7o 7p 4e 5e 6e Ac 9o 2p", "")
    assert escolher_descarte_bot(bot, mesa) == carta("Ac")   # Ás vale 15
