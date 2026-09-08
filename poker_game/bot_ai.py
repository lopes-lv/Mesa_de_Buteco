"""
bot_ai.py - IA simples para os bots.

A decisão é baseada exclusivamente na força estimada da mão:
 - Pré-flop: força heurística das 2 cartas (pares altos, cartas altas, conectadas)
 - Pós-flop: avalia a melhor mão possível com as cartas comunitárias reveladas
Sem blefe: o bot age de forma direta e previsível, coerente com a
força real da mão. Quanto mais forte a mão, maior a chance de apostar/raise.
"""
import random
from hand_evaluator import melhor_mao

VALOR_TEXTO_ORDEM = list(range(2, 15))


def _forca_pre_flop(mao):
    """Retorna um score de 0 a 100 para uma mão de 2 cartas (pré-flop)."""
    c1, c2 = mao
    alto = max(c1.valor, c2.valor)
    baixo = min(c1.valor, c2.valor)
    par = c1.valor == c2.valor
    mesmo_naipe = c1.naipe == c2.naipe
    conectadas = abs(c1.valor - c2.valor) == 1 or (par is False and {c1.valor, c2.valor} == {14, 2})

    score = (alto + baixo) * 2  # base pela carta alta somada à baixa
    if par:
        score += 40 + (c1.valor * 2)  # pares valem bem mais, pares altos ainda mais
    if mesmo_naipe:
        score += 10
    if conectadas:
        score += 8
    return min(score, 100)


def _forca_pos_flop(cartas_jogador, comunitarias):
    """Retorna um score de 0 a 100 baseado na categoria da melhor mão formada."""
    forca, categoria, _ = melhor_mao(cartas_jogador + comunitarias)
    categoria_num = forca[0]  # 1 (carta alta) a 9 (straight flush)
    # normaliza categoria (peso principal) + um pouco do primeiro desempate
    score = categoria_num * 10 + min(forca[1] if len(forca) > 1 else 0, 14) * 0.7
    return min(score, 100)


def decidir_acao_bot(jogador, estagio, comunitarias, aposta_alvo, big_blind):
    """
    Retorna tupla (acao, valor_raise) onde acao em
    {'fold', 'check', 'call', 'raise'}.
    """
    if estagio == "preflop":
        score = _forca_pre_flop(jogador.mao)
    else:
        score = _forca_pos_flop(jogador.mao, comunitarias)

    a_pagar = aposta_alvo - jogador.aposta_rodada
    pode_dar_check = a_pagar <= 0

    # pequena variação para os bots não jogarem 100% deterministicamente
    ruido = random.uniform(-4, 4)
    score += ruido

    if score >= 70:
        # mão forte: aumenta
        if jogador.stack <= big_blind:
            return ("call", 0)
        valor_raise = max(big_blind, int(aposta_alvo * 0.75) + big_blind)
        valor_raise = min(valor_raise, jogador.stack - max(0, a_pagar))
        if valor_raise <= 0:
            return ("call", 0)
        return ("raise", valor_raise)

    if score >= 40:
        # mão mediana: paga se não for caro demais, senão desiste
        if pode_dar_check:
            return ("check", 0)
        if a_pagar <= big_blind * 3 or a_pagar <= jogador.stack * 0.2:
            return ("call", 0)
        return ("fold", 0)

    # mão fraca
    if pode_dar_check:
        return ("check", 0)
    if a_pagar <= big_blind:
        # aposta muito barata, ainda vale pagar
        return ("call", 0)
    return ("fold", 0)
