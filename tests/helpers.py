"""Fábricas de cartas, peças e mesas usadas pelos testes."""
from core.deck import Card

_VALORES = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
            "J": 11, "Q": 12, "K": 13, "A": 14}
_NAIPES = {"c": "copas", "o": "ouros", "p": "paus", "e": "espadas", "*": "coringa"}


def carta(texto):
    """Uma carta a partir de 'valor+naipe': 'Ae' (Ás de espadas), '10c' (10 de
    copas), 'Kp' (Rei de paus), 'Jo' (Valete de ouros). '*' é o Joker."""
    if texto == "*":
        return Card(0, "coringa")
    return Card(_VALORES[texto[:-1]], _NAIPES[texto[-1]])


def cartas(texto):
    """'Ae Ke Qe' vira uma lista de Card."""
    return [carta(t) for t in texto.split()]


# ---------------------------------------------------------------- Dominó
def pecas(texto):
    """'4-4 4-2' vira [Peca(4, 4), Peca(4, 2)]."""
    from domino.domino_logic import Peca
    return [Peca(*(int(n) for n in item.split("-"))) for item in texto.split()]


def mesa_domino(*maos):
    """Mesa de Dominó com mãos escolhidas a dedo, vez do primeiro jogador e
    abertura livre (sem a 6/6 forçada). `maos` são textos como '4-4 4-2'.
    Devolve (mesa, jogadores)."""
    from domino.domino_logic import DominoPlayer, DominoTable
    jogadores = [DominoPlayer(i, f"J{i}") for i in range(len(maos))]
    mesa = DominoTable(jogadores)
    mesa.iniciar_nova_mao()
    for jogador, texto in zip(jogadores, maos):
        jogador.mao = pecas(texto)
    mesa._ordem = list(jogadores)
    mesa.indice_da_vez = 0
    mesa.peca_obrigatoria = None
    mesa.forcar_abertura_6_6 = False
    return mesa, jogadores


def jogar(mesa, jogador, texto, direcao="esquerda"):
    """Joga a peça '4-2' do jogador e confere que a jogada foi aceita."""
    peca = pecas(texto)[0]
    assert mesa.jogar(jogador, peca, direcao), f"{jogador.nome} não conseguiu jogar {peca} em {direcao}"
