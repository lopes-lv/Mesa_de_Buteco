"""
domino_bot_ai.py - IA do modo Dominó: uma heurística simples (sem perfis por
partida, mesmo espírito de pifpaf_bot_ai.py).

Prioriza, nessa ordem: 1) jogadas que pontuam (pontas somam múltiplo de 5,
preferindo a de maior pontuação), 2) carroças (só encaixam num número, ficam
presas na mão mais fácil), 3) entre as opções restantes, a peça de maior
pontuação (reduz o prejuízo se a mão travar/bloquear antes do bot conseguir
bater).
"""


def escolher_jogada_bot(jogador, mesa):
    """Retorna (peca, lado) a jogar, ou None se não há jogada possível
    (nesse caso quem chama deve fazer o bot passar a vez)."""
    opcoes = mesa.jogadas_possiveis(jogador)
    if not opcoes:
        return None

    def prioridade(item):
        peca, lado = item
        return (mesa.pontuacao_se_jogar(peca, lado), peca.eh_carroca, peca.pontos)

    return max(opcoes, key=prioridade)
