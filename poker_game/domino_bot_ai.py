"""
domino_bot_ai.py - IA do modo Dominó: uma heurística simples (sem perfis por
partida, mesmo espírito de pifpaf_bot_ai.py).

Prioriza jogar carroças primeiro (só encaixam num número, ficam presas na
mão mais fácil) e, entre as opções restantes, a peça de maior pontuação
(reduz o prejuízo se a mão travar/bloquear antes do bot conseguir bater).
"""


def escolher_jogada_bot(jogador, mesa):
    """Retorna (peca, lado) a jogar, ou None se não há jogada possível
    (nesse caso quem chama deve comprar/passar antes de perguntar de novo)."""
    opcoes = mesa.jogadas_possiveis(jogador)
    if not opcoes:
        return None

    def prioridade(item):
        peca, _lado = item
        return (peca.eh_carroca, peca.pontos)

    return max(opcoes, key=prioridade)
