"""
hand_evaluator.py - Avaliação de mãos de poker (Texas Hold'em)

Cada mão é avaliada como uma tupla (categoria, desempates...) onde
tuplas maiores vencem. Isso permite comparar mãos diretamente com
operadores Python (>, <, ==) e resolver empates / split pots com
exatidão, pois duas tuplas iguais significam mãos empatadas.
"""
from itertools import combinations
from collections import Counter

NOME_CATEGORIA = {
    9: "Straight Flush",
    8: "Quadra",
    7: "Full House",
    6: "Flush",
    5: "Sequência",
    4: "Trinca",
    3: "Dois Pares",
    2: "Par",
    1: "Carta Alta",
}


def _avaliar_5_cartas(cartas):
    """Recebe exatamente 5 objetos Card e retorna tupla de força."""
    valores = sorted((c.valor for c in cartas), reverse=True)
    naipes = [c.naipe for c in cartas]
    contagem = Counter(valores)
    # agrupa por (quantidade, valor) ordenado: mais repetido e maior valor primeiro
    grupos = sorted(contagem.items(), key=lambda kv: (-kv[1], -kv[0]))
    valores_ordenados_por_grupo = [v for v, _ in grupos]

    eh_flush = len(set(naipes)) == 1

    # trata sequência, incluindo A-2-3-4-5 (roda / "wheel")
    valores_unicos = sorted(set(valores), reverse=True)
    eh_sequencia = False
    topo_sequencia = None
    if len(valores_unicos) == 5:
        if valores_unicos[0] - valores_unicos[4] == 4:
            eh_sequencia = True
            topo_sequencia = valores_unicos[0]
        elif valores_unicos == [14, 5, 4, 3, 2]:
            eh_sequencia = True
            topo_sequencia = 5  # A conta como 1, sequência "5 alta"

    padrao = tuple(sorted(contagem.values(), reverse=True))

    if eh_sequencia and eh_flush:
        return (9, topo_sequencia)
    if padrao == (4, 1):
        return (8,) + tuple(valores_ordenados_por_grupo)
    if padrao == (3, 2):
        return (7,) + tuple(valores_ordenados_por_grupo)
    if eh_flush:
        return (6,) + tuple(valores)
    if eh_sequencia:
        return (5, topo_sequencia)
    if padrao == (3, 1, 1):
        return (4,) + tuple(valores_ordenados_por_grupo)
    if padrao == (2, 2, 1):
        return (3,) + tuple(valores_ordenados_por_grupo)
    if padrao == (2, 1, 1, 1):
        return (2,) + tuple(valores_ordenados_por_grupo)
    return (1,) + tuple(valores)


def melhor_mao(cartas_totais):
    """
    Recebe uma lista com as cartas do jogador + cartas comunitárias
    (normalmente 7 cartas) e retorna (forca, categoria_nome, melhores_5_cartas).
    """
    melhor_forca = None
    melhores_cartas = None
    for combo in combinations(cartas_totais, 5):
        forca = _avaliar_5_cartas(combo)
        if melhor_forca is None or forca > melhor_forca:
            melhor_forca = forca
            melhores_cartas = combo
    categoria = NOME_CATEGORIA[melhor_forca[0]]
    return melhor_forca, categoria, melhores_cartas


def comparar_maos(lista_cartas_por_jogador):
    """
    Recebe dict {jogador_id: [cartas...]} e retorna dict
    {jogador_id: (forca, categoria, melhores_5)} já avaliado,
    útil para determinar vencedores e empates (split pot).
    """
    resultado = {}
    for jogador_id, cartas in lista_cartas_por_jogador.items():
        resultado[jogador_id] = melhor_mao(cartas)
    return resultado


def determinar_vencedores(resultados):
    """
    Recebe dict {jogador_id: (forca, categoria, melhores_5)} (já avaliado)
    e retorna lista de jogador_id(s) vencedor(es). Mais de um id
    indica empate exato -> split pot.
    """
    melhor_forca = max(r[0] for r in resultados.values())
    vencedores = [jid for jid, r in resultados.items() if r[0] == melhor_forca]
    return vencedores
