"""Decisões dos bots de Texas Hold'em."""
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
    valores = {c.valor for c in cartas_jogador + comunitarias}
    if categoria_num == 1 and len(valores) >= 4:
        score += 8
    naipes = {}
    for carta in cartas_jogador + comunitarias:
        naipes[carta.naipe] = naipes.get(carta.naipe, 0) + 1
    if categoria_num < 6 and max(naipes.values(), default=0) == 4:
        score += 10
    return min(score, 100)


def decidir_acao_bot(
    jogador, estagio, comunitarias, aposta_alvo, big_blind,
    pote=0, oponentes_ativos=2, posicao=0, jogadores_agiram=0,
):
    """
    Retorna tupla (acao, valor_raise) onde acao em
    {'fold', 'check', 'call', 'raise'}.
    """
    if estagio == "preflop":
        score = _forca_pre_flop(jogador.mao)
    else:
        score = _forca_pos_flop(jogador.mao, comunitarias)

    perfil = jogador.id % 4
    ajuste_perfil = (-5, 0, 6, 2)[perfil]
    blefe_base = (0.05, 0.10, 0.16, 0.22)[perfil]
    score += ajuste_perfil
    a_pagar = max(0, aposta_alvo - jogador.aposta_rodada)
    pode_dar_check = a_pagar <= 0
    stack_efetivo = max(1, jogador.stack + jogador.aposta_rodada)
    pote_atual = max(1, pote)
    pot_odds = a_pagar / (pote_atual + a_pagar) if a_pagar else 0
    pressao = min(25, (a_pagar / stack_efetivo) * 100)

    score += min(8, max(0, posicao) * 2) - pressao * 0.18
    score += random.uniform(-5, 5)
    blefando = random.random() < blefe_base + (0.04 if pode_dar_check else 0)

    if score >= 67:
        if jogador.stack <= big_blind:
            return ("call", 0)
        valor_raise = max(big_blind, int(max(aposta_alvo, big_blind) * 0.65))
        valor_raise = min(valor_raise, jogador.stack - max(0, a_pagar))
        if valor_raise <= 0:
            return ("call", 0)
        return ("raise", valor_raise)

    if score >= 43:
        if pode_dar_check:
            return ("raise", big_blind) if random.random() < 0.22 else ("check", 0)
        if pot_odds <= 0.28 or a_pagar <= big_blind * 2.5:
            return ("call", 0)
        return ("call", 0) if random.random() < 0.30 else ("fold", 0)

    if pode_dar_check:
        if blefando and jogador.stack > big_blind:
            return ("raise", big_blind)
        return ("check", 0)
    if a_pagar <= big_blind * 1.5 or pot_odds <= 0.16:
        return ("call", 0)
    if blefando and score >= 30 and jogador.stack > a_pagar + big_blind:
        return ("raise", min(big_blind, jogador.stack - a_pagar))
    if random.random() < 0.12 and jogadores_agiram >= max(1, oponentes_ativos - 1):
        return ("call", 0)
    return ("fold", 0)
