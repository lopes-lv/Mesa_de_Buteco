"""SI-* — partidas completas só de bots, com as invariantes conferidas a cada
passo. Reproduz o fluxo das telas do host (atualizar/_descartar/...), sem janela.
Marcadas `lento`: rodam no job "completo" do CI."""
import random

import pytest

from domino.domino_bot_ai import escolher_jogada_bot
from domino.domino_logic import PONTUACAO_VITORIA, DominoPlayer, DominoTable, criar_pecas
from holdem.bot_ai import decidir_acao_bot
from holdem.game_logic import Player, Table
from pifpaf.pifpaf_bot_ai import decidir_fonte_compra_bot, escolher_descarte_bot
from pifpaf.pifpaf_logic import VITORIAS_PARA_VENCER, PifPafPlayer, PifPafTable, criar_baralho_duplo

pytestmark = pytest.mark.lento

MAX_PASSOS_POR_MAO = 600
MAX_MAOS = 400


# ---------------------------------------------------------------- Hold'em
def _acao_do_bot(table, jogador):
    rodada = table.rodada_atual
    ativos = [j for j in table.jogadores_na_mesa()]
    indice = ativos.index(jogador)
    posicao = (indice - ativos.index(table.jogadores[table.dealer_idx]) - 1) % len(ativos)
    return decidir_acao_bot(
        jogador, table.estagio, table.comunitarias, rodada.aposta_alvo, table.blinds_atuais()[1],
        pote=sum(j.total_apostado_mao for j in table.jogadores),
        oponentes_ativos=len(rodada.jogadores_ativos_na_mao()) - 1,
        posicao=posicao, jogadores_agiram=len(rodada.jogadores_que_agiram),
        ultimo_raise=rodada.ultimo_raise_valor)


def _conferir_holdem(table, total):
    assert all(j.stack >= 0 for j in table.jogadores), "stack negativo"
    assert sum(j.stack + j.total_apostado_mao for j in table.jogadores) == total, "fichas criadas/perdidas"
    cartas = [c for j in table.jogadores for c in j.mao] + table.comunitarias + table.deck.cartas
    assert len(cartas) == 52 and len(set(cartas)) == 52, "carta repetida"


def jogar_holdem(n_jogadores, semente, stack=1000):
    random.seed(semente)
    jogadores = [Player(i, f"B{i}", stack=stack) for i in range(n_jogadores)]
    table = Table(jogadores)
    total = stack * n_jogadores
    for _ in range(MAX_MAOS):
        if table.jogo_tem_vencedor():
            return table
        table.iniciar_nova_mao()
        for _passo in range(MAX_PASSOS_POR_MAO):
            _conferir_holdem(table, total)
            if table.mao_finalizada_por_fold():
                table.processar_showdown()
                break
            rodada = table.rodada_atual
            if rodada.rodada_terminou():
                table.avancar_estagio()
                if table.estagio == "showdown":
                    table.processar_showdown()
                    break
                continue
            jogador = rodada.jogador_da_vez()
            acao, valor = _acao_do_bot(table, jogador)
            rodada.aplicar_acao(jogador, acao, valor)
        else:
            pytest.fail(f"mão do Hold'em não terminou em {MAX_PASSOS_POR_MAO} passos (semente {semente})")
        table.marcar_eliminados()
        assert sum(j.stack for j in jogadores) == total
    pytest.fail(f"partida do Hold'em não terminou em {MAX_MAOS} mãos (semente {semente})")


@pytest.mark.parametrize("n_jogadores", [2, 3, 5, 8])
def test_si_01_holdem_partidas_completas_terminam_conservando_as_fichas(n_jogadores):
    for semente in range(6):
        table = jogar_holdem(n_jogadores, semente)
        assert len(table.jogadores_na_mesa()) == 1
        assert sum(j.stack for j in table.jogadores) == 1000 * n_jogadores


# ---------------------------------------------------------------- Pif Paf
def jogar_pifpaf(n_jogadores, semente, usar_joker):
    random.seed(semente)
    jogadores = [PifPafPlayer(i, f"B{i}") for i in range(n_jogadores)]
    mesa = PifPafTable(jogadores, usar_joker=usar_joker)
    total_cartas = len(criar_baralho_duplo(usar_joker))
    for _ in range(MAX_MAOS):
        if mesa.jogo_tem_vencedor():
            return mesa
        mesa.iniciar_nova_mao()
        for _passo in range(MAX_PASSOS_POR_MAO * 2):
            if mesa.resultado_mao is not None:
                break
            assert sum(len(j.mao) for j in jogadores) + len(mesa.monte) + len(mesa.descarte) == total_cartas
            jogador = mesa.jogador_da_vez()
            if mesa.pode_bater_mao_fechada(jogador):
                mesa.bater_mao_fechada(jogador)
            elif mesa.pode_comprar():
                fonte = decidir_fonte_compra_bot(jogador, mesa)
                (mesa.comprar_do_descarte if fonte == "descarte" else mesa.comprar_do_monte)(jogador)
            elif mesa.pode_bater(jogador):
                mesa.bater(jogador)
            else:
                carta = escolher_descarte_bot(jogador, mesa)
                assert carta in jogador.mao
                if mesa.pode_bater_descartando(jogador, carta):
                    mesa.bater_descartando(jogador, carta)
                else:
                    mesa.descartar(jogador, carta)
        else:
            pytest.fail(f"mão do Pif Paf não terminou (semente {semente})")
    pytest.fail(f"partida do Pif Paf não terminou em {MAX_MAOS} mãos (semente {semente})")


@pytest.mark.parametrize("semente", range(3))
@pytest.mark.parametrize("usar_joker", [False, True])
@pytest.mark.parametrize("n_jogadores", [2, 4, 8])
def test_si_02_pifpaf_partidas_completas_terminam_com_um_vencedor(n_jogadores, usar_joker, semente):
    # uma partida por teste: com 8 jogadores uma só leva alguns segundos, e o
    # timeout por teste do QA (60 s, com cobertura ligada) não pode estourar
    mesa = jogar_pifpaf(n_jogadores, semente, usar_joker)
    vencedor = mesa.vencedor_do_jogo()
    assert vencedor is not None and vencedor.vitorias >= VITORIAS_PARA_VENCER


# ---------------------------------------------------------------- Dominó
def jogar_domino(n_jogadores, semente):
    random.seed(semente)
    jogadores = [DominoPlayer(i, f"B{i}") for i in range(n_jogadores)]
    mesa = DominoTable(jogadores)
    todas = set(criar_pecas(n_jogadores))
    for _ in range(MAX_MAOS):
        if mesa.vencedor_do_jogo() is not None:
            return mesa
        mesa.iniciar_nova_mao()
        for _passo in range(MAX_PASSOS_POR_MAO):
            if mesa.resultado_mao is not None:
                break
            na_mesa = ([mesa.primeira_peca.peca] if mesa.primeira_peca else []) \
                + [i.peca for ramo in mesa.ramos.values() for i in ramo]
            em_jogo = [p for j in jogadores for p in j.mao] + na_mesa
            assert len(em_jogo) == len(set(em_jogo)) == len(todas), "peça perdida ou repetida"
            assert set(em_jogo) == todas
            jogador = mesa.jogador_da_vez()
            if not mesa.pode_jogar(jogador):
                mesa.passar(jogador)
                continue
            escolha = escolher_jogada_bot(jogador, mesa)
            assert escolha in mesa.jogadas_possiveis(jogador)
            assert mesa.jogar(jogador, *escolha)
        else:
            pytest.fail(f"mão do Dominó não terminou (semente {semente})")
        assert mesa.resultado_mao["tipo"] in ("bateu", "bloqueio_total")
    pytest.fail(f"partida do Dominó não terminou em {MAX_MAOS} mãos (semente {semente})")


@pytest.mark.parametrize("n_jogadores", [3, 4])
def test_si_03_domino_partidas_completas_terminam_em_250_pontos(n_jogadores):
    for semente in range(8):
        mesa = jogar_domino(n_jogadores, semente)
        assert mesa.vencedor_do_jogo().pontuacao >= PONTUACAO_VITORIA


# ---------------------------------------------------------------- Propriedades (Hypothesis)
def test_si_05_calcular_potes_conserva_o_total_para_qualquer_combinacao_de_apostas():
    hypothesis = pytest.importorskip("hypothesis")
    from hypothesis import given, strategies as st
    from holdem.game_logic import calcular_potes

    @hypothesis.settings(max_examples=120, deadline=None)
    @given(st.lists(st.tuples(st.integers(0, 500), st.booleans()), min_size=2, max_size=8))
    def propriedade(apostas):
        jogadores = []
        for i, (total, foldou) in enumerate(apostas):
            j = Player(i, f"J{i}", stack=1000)
            j.total_apostado_mao, j.foldou = total, foldou
            jogadores.append(j)
        potes = calcular_potes(jogadores)
        assert sum(p["valor"] for p in potes) == sum(t for t, _ in apostas)
        for p in potes:
            assert p["valor"] > 0
            assert all(not jogadores[i].foldou for i in p["elegiveis"])

    propriedade()


def test_si_05_melhor_mao_nunca_perde_para_um_subconjunto_de_cinco_cartas():
    hypothesis = pytest.importorskip("hypothesis")
    from itertools import combinations
    from hypothesis import given, strategies as st
    from core.deck import NAIPES, VALORES, Card
    from holdem.hand_evaluator import _avaliar_5_cartas, melhor_mao

    baralho = [Card(v, n) for n in NAIPES for v in VALORES]

    @hypothesis.settings(max_examples=150, deadline=None)
    @given(st.lists(st.sampled_from(baralho), min_size=7, max_size=7, unique=True))
    def propriedade(cartas):
        forca, _, _ = melhor_mao(cartas)
        assert forca == max(_avaliar_5_cartas(c) for c in combinations(cartas, 5))

    propriedade()
