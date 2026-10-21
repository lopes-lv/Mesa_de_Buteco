"""HB-* — IA dos bots do Hold'em (holdem/README.md, "IA dos bots")."""
import random

import pytest

from holdem.bot_ai import decidir_acao_bot
from holdem.game_logic import Player
from tests.helpers import cartas

ACOES = {"fold", "check", "call", "raise"}
BB = 20


def bot(id_jogador, mao, stack=1000, aposta_rodada=0):
    jogador = Player(id_jogador, f"B{id_jogador}", stack=stack)
    jogador.mao = cartas(mao)
    jogador.aposta_rodada = aposta_rodada
    return jogador


def decidir(jogador, aposta_alvo=BB, estagio="preflop", comunitarias="", **extras):
    return decidir_acao_bot(jogador, estagio, cartas(comunitarias), aposta_alvo, BB, **extras)


def cenarios(quantidade=600):
    """Situações variadas e reproduzíveis: mãos, apostas, stacks e estágios."""
    sorteio = random.Random(7)
    valores = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    baralho = [f"{v}{n}" for v in valores for n in "copo"]
    for _ in range(quantidade):
        mao = sorteio.sample(baralho, 2)
        mesa = sorteio.sample([c for c in baralho if c not in mao], sorteio.choice([0, 3, 4, 5]))
        stack = sorteio.choice([5, 10, 20, 60, 400, 1500])
        aposta = sorteio.choice([0, BB, BB * 3, 200, 900])
        yield (sorteio.randrange(0, 8), " ".join(mao), " ".join(mesa), stack, aposta,
               sorteio.randrange(0, 5))


def test_hb_01_a_acao_e_sempre_uma_das_quatro():
    for id_jogador, mao, mesa, stack, aposta, posicao in cenarios():
        estagio = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}[len(mesa.split())]
        acao, valor = decidir(bot(id_jogador, mao, stack), aposta, estagio, mesa,
                              pote=aposta * 2, posicao=posicao)
        assert acao in ACOES
        assert isinstance(valor, int) and valor >= 0


def test_hb_02_nunca_da_check_quando_ha_aposta_a_pagar():
    for id_jogador, mao, mesa, stack, aposta, posicao in cenarios():
        if aposta == 0:
            continue
        estagio = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}[len(mesa.split())]
        acao, _ = decidir(bot(id_jogador, mao, stack), aposta, estagio, mesa, posicao=posicao)
        assert acao != "check"


@pytest.mark.xfail(reason="BUG: com 'check' disponível o bot às vezes devolve raise de um big blind "
                          "inteiro mesmo com stack menor que isso (bot_ai.py, ramos 'score >= 43' e "
                          "blefe); a aposta é cortada pelo stack, mas o valor do raise registrado em "
                          "BettingRound.ultimo_raise_valor fica maior que as fichas que existiam.")
def test_hb_03_o_raise_nunca_passa_do_que_o_bot_tem():
    for id_jogador, mao, mesa, stack, aposta, posicao in cenarios(1500):
        estagio = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}[len(mesa.split())]
        jogador = bot(id_jogador, mao, stack)
        acao, valor = decidir(jogador, aposta, estagio, mesa, posicao=posicao)
        if acao == "raise":
            assert valor <= jogador.stack - max(0, aposta - jogador.aposta_rodada), \
                f"raise {valor} com stack {stack} e {aposta} a pagar"


def test_hb_04_mao_muito_forte_nunca_desiste():
    for id_jogador in range(8):
        for _ in range(100):
            acao, _ = decidir(bot(id_jogador, "Ac Ao"), aposta_alvo=300)
            assert acao != "fold"


def test_hb_04_mao_fraca_diante_de_aposta_alta_nunca_aumenta():
    for id_jogador in range(8):
        for _ in range(100):
            acao, _ = decidir(bot(id_jogador, "2c 7o"), aposta_alvo=400, posicao=0)
            assert acao != "raise"


def test_hb_05_o_perfil_muda_o_comportamento_de_forma_fixa_por_jogador():
    """Perfil por id: o 'tight' (id 0) desiste mais que o 'agressivo' (id 2) com a mesma mão."""
    def taxa_de_fold(id_jogador):
        random.seed(11)
        return sum(decidir(bot(id_jogador, "9c 4o"), aposta_alvo=100)[0] == "fold"
                   for _ in range(2000))
    assert taxa_de_fold(0) > taxa_de_fold(2)
    assert taxa_de_fold(0) == taxa_de_fold(4)          # mesmo perfil (id % 4), mesma semente
