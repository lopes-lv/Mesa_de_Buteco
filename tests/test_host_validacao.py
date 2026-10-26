"""HV-* — o host valida as ações que chegam pela rede antes de aplicá-las
(`_processar_acao_remota` das telas de mesa; rede/protocolo.py, ERRO_ACAO).

Num multiplayer o host é a única autoridade: um cliente com defeito ou
alterado não pode jogar fora da vez nem violar a regra. A validação mora nas
telas do host, não nos motores (ver DJ-12, DJ-13 e HA-07).
"""
import queue

import pytest

from domino.domino_logic import DominoPlayer, DominoTable, Peca
from domino.domino_screen import DominoTableScreen
from holdem.game_logic import Player, Table
from holdem.table_screen import TableScreen
from pifpaf.pifpaf_logic import PifPafPlayer, PifPafTable
from pifpaf.pifpaf_screen import PifPafTableScreen
from rede import protocolo
from tests.helpers import cartas, pecas
from tools.editor_mesa import AppFalso


class SalaFalsa:
    """O mínimo de AnfitriaoSala que as telas do host usam."""

    def __init__(self):
        self.enviados = []
        self.desconectados = set()
        self.nome_anfitriao = "Host"
        self.mensagens_entrantes = queue.Queue()

    def enviar_para(self, jogador_id, mensagem):
        self.enviados.append((jogador_id, mensagem))

    def enviar_para_todos(self, mensagem):
        self.enviados.append((None, mensagem))

    def encerrar(self):
        pass

    def erros(self):
        return [m["motivo"] for _, m in self.enviados if m.get("tipo") == protocolo.ERRO_ACAO]


# ---------------------------------------------------------------- Hold'em
@pytest.fixture
def holdem():
    jogadores = [Player(i, f"J{i}", stack=1000) for i in range(3)]
    sala = SalaFalsa()
    tela = TableScreen(AppFalso(), Table(jogadores), sala_rede=sala)
    rodada = tela.table.rodada_atual
    vez = rodada.jogador_da_vez()
    outro = next(j for j in jogadores if j is not vez)
    return tela, sala, vez, outro


def _estado_holdem(tela):
    return [(j.stack, j.aposta_rodada, j.foldou) for j in tela.table.jogadores]


def test_hv_01_holdem_acao_fora_da_vez_e_recusada(holdem):
    tela, sala, vez, outro = holdem
    antes = _estado_holdem(tela)
    tela._processar_acao_remota(outro.id, {"acao": "call"})
    assert sala.erros() == ["Não é a sua vez"]
    assert _estado_holdem(tela) == antes


def test_hv_02_holdem_check_com_aposta_a_pagar_e_recusado(holdem):
    tela, sala, vez, _ = holdem
    assert tela.table.rodada_atual.aposta_alvo > vez.aposta_rodada
    antes = _estado_holdem(tela)
    tela._processar_acao_remota(vez.id, {"acao": "check"})
    assert sala.erros() and "check" in sala.erros()[0]
    assert _estado_holdem(tela) == antes


def test_hv_03_holdem_raise_maior_que_o_stack_e_recusado(holdem):
    tela, sala, vez, _ = holdem
    tela._processar_acao_remota(vez.id, {"acao": "raise", "valor": 10 ** 6})
    assert sala.erros() == ["Valor de raise maior que seu stack disponível"]


@pytest.mark.parametrize("acao", ["foldar", "all-in", None])
def test_hv_04_holdem_acao_desconhecida_e_recusada(holdem, acao):
    tela, sala, vez, _ = holdem
    tela._processar_acao_remota(vez.id, {"acao": acao})
    assert sala.erros() == ["Ação inválida"]


def test_hv_05_holdem_jogador_desconhecido_e_recusado(holdem):
    tela, sala, _, _ = holdem
    tela._processar_acao_remota(99, {"acao": "call"})
    assert sala.erros() == ["Jogador desconhecido"]


def test_hv_06_holdem_acao_valida_e_aplicada(holdem):
    tela, sala, vez, _ = holdem
    a_pagar = tela.table.rodada_atual.aposta_alvo - vez.aposta_rodada
    stack = vez.stack
    tela._processar_acao_remota(vez.id, {"acao": "call"})
    assert sala.erros() == []
    assert vez.stack == stack - a_pagar


@pytest.mark.xfail(reason="BUG: o host aceita raise de qualquer valor positivo (1 ficha, por exemplo); "
                          "não há raise mínimo nem no host (table_screen._processar_acao_remota) nem no "
                          "motor. Um cliente remoto consegue 'minraise' abaixo do big blind.")
def test_hv_07_holdem_raise_abaixo_do_minimo_e_recusado(holdem):
    tela, sala, vez, _ = holdem
    big_blind = tela.table.blinds_atuais()[1]
    tela._processar_acao_remota(vez.id, {"acao": "raise", "valor": 1})
    assert 1 < big_blind
    assert sala.erros(), "raise de 1 ficha foi aceito"


# ---------------------------------------------------------------- Dominó
@pytest.fixture
def domino():
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(3)]
    sala = SalaFalsa()
    tela = DominoTableScreen(AppFalso(), DominoTable(jogadores), sala_rede=sala)
    mesa = tela.mesa
    for jogador, texto in zip(mesa.jogadores, ["4-4 0-1", "4-1 2-3", "5-5 6-6"], strict=True):
        jogador.mao = pecas(texto)
    mesa._ordem = list(mesa.jogadores)
    mesa.indice_da_vez = 0
    mesa.peca_obrigatoria = None
    mesa.forcar_abertura_6_6 = False
    sala.enviados.clear()
    return tela, sala, mesa.jogadores


def test_hv_10_domino_jogada_fora_da_vez_e_recusada(domino):
    tela, sala, (a, b, c) = domino
    tela._processar_acao_remota(c.id, {"acao": "jogar", "peca": [5, 5], "lado": "esquerda"})
    assert sala.erros() == ["Não é a sua vez"]
    assert tela.mesa.mesa_vazia() and Peca(5, 5) in c.mao


def test_hv_11_domino_passar_com_jogada_possivel_e_recusado(domino):
    tela, sala, (a, b, c) = domino
    tela._processar_acao_remota(a.id, {"acao": "jogar", "peca": [4, 4], "lado": "esquerda"})
    sala.enviados.clear()
    assert tela.mesa.jogador_da_vez() is b
    tela._processar_acao_remota(b.id, {"acao": "passar"})
    assert sala.erros() == ["Você ainda tem jogada possível"]
    assert tela.mesa.passes_consecutivos == 0


def test_hv_12_domino_peca_que_o_jogador_nao_tem_e_recusada(domino):
    tela, sala, (a, *_) = domino
    tela._processar_acao_remota(a.id, {"acao": "jogar", "peca": [3, 3], "lado": "esquerda"})
    assert sala.erros() == ["Você não tem essa peça"]


@pytest.mark.parametrize("dados", [
    {"acao": "jogar", "peca": [4, 4]},
    {"acao": "jogar", "peca": [4], "lado": "esquerda"},
    {"acao": "jogar", "peca": [4, 4], "lado": "diagonal"},
])
def test_hv_13_domino_jogada_mal_formada_e_recusada(domino, dados):
    tela, sala, (a, *_) = domino
    tela._processar_acao_remota(a.id, dados)
    assert sala.erros() == ["Jogada inválida"]


def test_hv_14_domino_jogada_valida_e_aplicada(domino):
    tela, sala, (a, *_) = domino
    tela._processar_acao_remota(a.id, {"acao": "jogar", "peca": [4, 4], "lado": "esquerda"})
    assert sala.erros() == []
    assert Peca(4, 4) not in a.mao and not tela.mesa.mesa_vazia()


# ---------------------------------------------------------------- Pif Paf
@pytest.fixture
def pifpaf():
    jogadores = [PifPafPlayer(i, f"J{i}") for i in range(3)]
    sala = SalaFalsa()
    tela = PifPafTableScreen(AppFalso(), PifPafTable(jogadores), sala_rede=sala)
    sala.enviados.clear()
    mesa = tela.mesa
    vez = mesa.jogador_da_vez()
    outro = next(j for j in jogadores if j is not vez)
    return tela, sala, mesa, vez, outro


def test_hv_20_pifpaf_acao_fora_da_vez_e_recusada(pifpaf):
    tela, sala, mesa, vez, outro = pifpaf
    tela._processar_acao_remota(outro.id, {"acao": "comprar_monte"})
    assert sala.erros() == ["Não é a sua vez"]
    assert len(outro.mao) == 9


def test_hv_21_pifpaf_descartar_antes_de_comprar_e_recusado(pifpaf):
    tela, sala, mesa, vez, _ = pifpaf
    carta = vez.mao[0]
    tela._processar_acao_remota(vez.id, {"acao": "descartar", "carta": [carta.valor, carta.naipe]})
    assert sala.erros() == ["Precisa comprar antes de descartar"]
    assert carta in vez.mao


def test_hv_22_pifpaf_comprar_duas_vezes_e_recusado(pifpaf):
    tela, sala, mesa, vez, _ = pifpaf
    tela._processar_acao_remota(vez.id, {"acao": "comprar_monte"})
    assert sala.erros() == []
    tela._processar_acao_remota(vez.id, {"acao": "comprar_descarte"})
    assert sala.erros() == ["Você já comprou nesta rodada"]
    assert len(vez.mao) == 10


def test_hv_23_pifpaf_bater_sem_poder_e_recusado(pifpaf):
    tela, sala, mesa, vez, _ = pifpaf
    tela._processar_acao_remota(vez.id, {"acao": "comprar_monte"})
    vez.mao = cartas("2c 5o 9p Je Kc Ac 3o 8e 6p 4c")
    tela._processar_acao_remota(vez.id, {"acao": "bater"})
    assert sala.erros() == ["Não é possível bater agora"]
    assert mesa.resultado_mao is None


def test_hv_24_pifpaf_mao_fechada_sem_poder_e_recusada(pifpaf):
    tela, sala, mesa, vez, _ = pifpaf
    vez.mao = cartas("2c 5o 9p Je Kc Ac 3o 8e 6p")
    tela._processar_acao_remota(vez.id, {"acao": "bater_mao_fechada"})
    assert sala.erros() == ["Mão fechada não disponível"]


def test_hv_25_pifpaf_descartar_carta_que_nao_tem_e_recusado(pifpaf):
    tela, sala, mesa, vez, _ = pifpaf
    tela._processar_acao_remota(vez.id, {"acao": "comprar_monte"})
    vez.mao = cartas("2c 5o 9p Je Kc Ac 3o 8e 6p 4c")
    tela._processar_acao_remota(vez.id, {"acao": "descartar", "carta": [7, "espadas"]})
    assert sala.erros() == ["Você não tem essa carta"]
