"""Decisoes dos bots no modo Pif Paf.

Heuristica simples (sem personalidades por partida, ver PIF_PAF_GUIA.md):
 - Compra do descarte apenas quando a carta do topo realmente reduz os
   pontos soltos da mao (mesmo criterio usado para escolher o descarte,
   ver `calcular_pontos_soltos` - evita o bot comprar uma carta achando
   que ela ajuda e devolve-la em seguida); caso contrario compra do monte.
 - Bate sempre que possivel (nao ha vantagem estrategica em segurar).
 - Ao descartar, se livra da carta solta de maior valor, nunca do coringa.
"""
from .pifpaf_logic import calcular_pontos_soltos, valor_pontos, eh_coringa


def decidir_fonte_compra_bot(jogador, mesa):
    """Retorna 'descarte' ou 'monte'."""
    if not mesa.descarte:
        return "monte"
    carta = mesa.descarte[-1]
    _, _, pontos_antes = calcular_pontos_soltos(jogador.mao, mesa.coringa_valor)
    _, _, pontos_depois = calcular_pontos_soltos(jogador.mao + [carta], mesa.coringa_valor)
    # so vale a pena comprar do descarte se a carta for realmente
    # absorvida por uma combinacao (pontos_depois cresce menos do que o
    # valor da propria carta, ou ate cai, ao juntar outras soltas a ela)
    if pontos_depois < pontos_antes + valor_pontos(carta, mesa.coringa_valor):
        return "descarte"
    return "monte"


def escolher_descarte_bot(jogador, mesa):
    """Retorna a carta da mao do bot a ser descartada."""
    _, soltas, _ = calcular_pontos_soltos(jogador.mao, mesa.coringa_valor)
    candidatas = [c for c in soltas if not eh_coringa(c, mesa.coringa_valor)]
    if candidatas:
        return max(candidatas, key=lambda c: valor_pontos(c, mesa.coringa_valor))

    nao_coringas = [c for c in jogador.mao if not eh_coringa(c, mesa.coringa_valor)]
    if nao_coringas:
        return min(nao_coringas, key=lambda c: valor_pontos(c, mesa.coringa_valor))

    return jogador.mao[0]
