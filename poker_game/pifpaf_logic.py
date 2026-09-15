"""
pifpaf_logic.py - Motor do modo de jogo Pif Paf.

Ver PIF_PAF_GUIA.md para o resumo das regras e as decisões de design.
Contém:
 - PifPafPlayer: estado de cada jogador (stack, mao, elimincao)
 - Baralho duplo (104 cartas) e sorteio da vira/coringa
 - Validacao de combinacoes (trinca / sequencia), com suporte a coringa
 - PifPafTable: orquestra uma mao completa (distribuir -> turnos -> batida -> liquidacao)
"""
import random
from itertools import combinations

from deck import NAIPES, VALORES, NAIPE_CORINGA, VALOR_CORINGA, Card

STACK_INICIAL = 1500
LIMITE_TURNOS_SEM_BATIDA = 200
JOKERS_POR_BARALHO_DUPLO = 4  # 2 por copia de 52, baralho duplo = 4


def criar_baralho_duplo(usar_joker=False):
    """Dois baralhos de 52 cartas combinados (104 cartas). Com `usar_joker`,
    acrescenta 4 Jokers impressos (2 por copia de 52) como unico coringa da
    mao - nesse modo a vira nao gera mais coringa por valor (ver `eh_coringa`
    e `PifPafTable.iniciar_nova_mao`)."""
    baralho = [Card(v, n) for _ in range(2) for n in NAIPES for v in VALORES]
    if usar_joker:
        baralho += [Card(VALOR_CORINGA, NAIPE_CORINGA) for _ in range(JOKERS_POR_BARALHO_DUPLO)]
    return baralho


def _valor_seguinte(valor):
    return 2 if valor == 14 else valor + 1


def eh_coringa(carta, coringa_valor):
    """True se `carta` funciona como coringa nesta mao: ou e um Joker
    impresso (sempre coringa, independente de `coringa_valor`), ou tem o
    valor da vira (quando a mao usa o sistema tradicional - `coringa_valor`
    fica None quando a mesa usa Joker impresso, ver iniciar_nova_mao)."""
    if carta.naipe == NAIPE_CORINGA:
        return True
    return coringa_valor is not None and carta.valor == coringa_valor


def valor_pontos(carta, coringa_valor):
    """Pontuacao de uma carta solta (nao combinada) ao fim da mao."""
    if eh_coringa(carta, coringa_valor):
        return 20
    if carta.valor == 14:
        return 15
    if carta.valor >= 11:  # J, Q, K
        return 10
    return carta.valor


# ---------------------------------------------------------------- Combinacoes
def _candidatos_trinca(cartas_mesmo_valor, coringas_disp):
    """Candidatos de trinca/quadra (3 ou 4 cartas de mesmo valor, naipes
    diferentes), completando com coringas quando necessario. Cada naipe
    contribui no maximo 1 carta representante (duplicatas do segundo
    baralho ficam disponiveis para outros grupos)."""
    por_naipe = {}
    for c in cartas_mesmo_valor:
        por_naipe.setdefault(c.naipe, c)
    naipes = list(por_naipe.keys())
    candidatos = []
    for tam_naipes in range(1, len(naipes) + 1):
        for combo in combinations(naipes, tam_naipes):
            cartas = tuple(por_naipe[n] for n in combo)
            for tamanho_grupo in (3, 4):
                falta = tamanho_grupo - len(cartas)
                if 0 <= falta <= coringas_disp:
                    candidatos.append((cartas, falta))
    return candidatos


def _candidatos_sequencia(cartas_mesmo_naipe, coringas_disp):
    """Candidatos de sequencia (3+ cartas seguidas do mesmo naipe). O As
    pode servir como 14 (acima do Rei) ou 1 (abaixo do 2), mas nunca liga
    Q-K-A-2 (as duas leituras sao geradas separadamente, sem mistura)."""
    por_valor = {}
    for c in cartas_mesmo_naipe:
        por_valor.setdefault(c.valor, c)
    candidatos = []
    for as_baixo in (False, True):
        if as_baixo and 14 not in por_valor:
            continue
        valores = {}
        for v, c in por_valor.items():
            vv = 1 if (v == 14 and as_baixo) else v
            valores[vv] = c
        ordenados = sorted(valores.keys())
        for i in range(len(ordenados)):
            for j in range(i, len(ordenados)):
                ini, fim = ordenados[i], ordenados[j]
                span = fim - ini + 1
                if span < 3:
                    continue
                presentes = [v for v in ordenados if ini <= v <= fim]
                falta = span - len(presentes)
                if falta > coringas_disp:
                    continue
                cartas = tuple(valores[v] for v in presentes)
                candidatos.append((cartas, falta))
    return candidatos


def _candidatos_para_carta(carta, cartas_disponiveis, coringas_disp):
    """Todos os grupos validos (trinca ou sequencia) que contem `carta`,
    montados a partir de `cartas_disponiveis` (naturais, sem coringas)."""
    mesmo_valor = [c for c in cartas_disponiveis if c.valor == carta.valor]
    mesmo_naipe = [c for c in cartas_disponiveis if c.naipe == carta.naipe]
    candidatos = []
    candidatos += [g for g in _candidatos_trinca(mesmo_valor, coringas_disp) if carta in g[0]]
    candidatos += [g for g in _candidatos_sequencia(mesmo_naipe, coringas_disp) if carta in g[0]]
    return candidatos


def carta_completa_combinacao(carta, mao, coringa_valor):
    """True se `carta` (candidata a compra) formaria, junto de cartas ja na
    mao, um grupo real (2+ cartas naturais associadas a ela) - usado pela
    IA para decidir se vale a pena comprar do descarte."""
    if eh_coringa(carta, coringa_valor):
        return True
    coringas_disp = sum(1 for c in mao if eh_coringa(c, coringa_valor))
    candidatos = _candidatos_para_carta(carta, mao + [carta], coringas_disp)
    return any(len(cartas_grupo) >= 2 for cartas_grupo, _ in candidatos)


def _encaixar_tudo(naturais, coringas_disp):
    """Backtracking exato: tenta encaixar TODAS as cartas naturais em
    grupos validos (trincas/sequencias), usando ate `coringas_disp`
    coringas para completar. Retorna lista de (cartas_grupo, coringas_usados),
    ou None se nao der para encaixar tudo. Maos tem no maximo 10 cartas,
    entao a busca e pequena mesmo sendo exaustiva."""
    if not naturais:
        return []
    primeira = naturais[0]
    for cartas_grupo, coringas_usados in _candidatos_para_carta(primeira, naturais, coringas_disp):
        restantes = list(naturais)
        for c in cartas_grupo:
            restantes.remove(c)
        sub = _encaixar_tudo(restantes, coringas_disp - coringas_usados)
        if sub is not None:
            return [(cartas_grupo, coringas_usados)] + sub
    return None


def pode_bater_mao(mao, coringa_valor):
    """True se a mao inteira (9 ou 10 cartas) pode ser organizada em
    trincas/sequencias validas, sem nenhuma carta solta."""
    naturais = [c for c in mao if not eh_coringa(c, coringa_valor)]
    n_coringas = len(mao) - len(naturais)
    return _encaixar_tudo(naturais, n_coringas) is not None


def agrupar_para_bater(mao, coringa_valor):
    """Retorna os grupos (listas de Card) que zeram a mao, ou None se a mao
    nao pode bater. Coringas usados para completar um grupo sao anexados
    ao final da lista de cartas naturais daquele grupo."""
    naturais = [c for c in mao if not eh_coringa(c, coringa_valor)]
    coringas = [c for c in mao if eh_coringa(c, coringa_valor)]
    grupos = _encaixar_tudo(naturais, len(coringas))
    if grupos is None:
        return None
    coringas_restantes = list(coringas)
    grupos_finais = []
    for cartas_grupo, coringas_usados in grupos:
        usados = coringas_restantes[:coringas_usados]
        del coringas_restantes[:coringas_usados]
        grupos_finais.append(list(cartas_grupo) + usados)
    return grupos_finais


def calcular_pontos_soltos(mao, coringa_valor):
    """Agrupa a mao de forma gulosa (sempre pegando o maior grupo valido
    disponivel) para minimizar as cartas soltas, e retorna
    (grupos, cartas_soltas, pontos_soltos). Usado para pontuar quem nao
    bateu - nao precisa ser a organizacao perfeita, so uma organizacao
    razoavel (times reais tambem nem sempre acham o encaixe otimo)."""
    naturais = [c for c in mao if not eh_coringa(c, coringa_valor)]
    coringas_disp = len(mao) - len(naturais)
    grupos = []

    progrediu = True
    while progrediu and naturais:
        progrediu = False
        melhor = None
        for carta in list(naturais):
            for cartas_grupo, coringas_usados in _candidatos_para_carta(carta, naturais, coringas_disp):
                tamanho = len(cartas_grupo) + coringas_usados
                if melhor is None or tamanho > melhor[2]:
                    melhor = (cartas_grupo, coringas_usados, tamanho)
        if melhor:
            cartas_grupo, coringas_usados, _ = melhor
            for c in cartas_grupo:
                naturais.remove(c)
            coringas_disp -= coringas_usados
            grupos.append(cartas_grupo)
            progrediu = True

    soltas = naturais
    pontos = sum(valor_pontos(c, coringa_valor) for c in soltas) + coringas_disp * 20
    return grupos, soltas, pontos


# ---------------------------------------------------------------- Jogador
class PifPafPlayer:
    def __init__(self, id_jogador, nome, stack=STACK_INICIAL, is_bot=True):
        self.id = id_jogador
        self.nome = nome
        self.stack = stack
        self.is_bot = is_bot
        self.mao = []
        self.eliminado = stack <= 0

    def reset_para_mao(self):
        self.mao = []
        self.eliminado = self.stack <= 0


# ---------------------------------------------------------------- Mesa
class PifPafTable:
    def __init__(self, jogadores, usar_joker=False):
        self.jogadores = jogadores
        self.usar_joker = usar_joker
        self.dealer_idx = 0
        self.mao_numero = 0

        self.monte = []
        self.descarte = []
        self.vira = None
        self.coringa_valor = None

        self._ordem = []
        self.indice_da_vez = 0
        self.comprou_nesta_vez = False
        self.resultado_mao = None
        self.jogadores_ja_agiram_na_mao = set()  # ids que ja compraram/descartaram nesta mao

    def jogadores_na_mesa(self):
        return [j for j in self.jogadores if not j.eliminado]

    def jogo_tem_vencedor(self):
        return len(self.jogadores_na_mesa()) <= 1

    # ------------------------------------------------------------ Mao
    def iniciar_nova_mao(self):
        self.mao_numero += 1
        for j in self.jogadores:
            j.reset_para_mao()

        ativos = self.jogadores_na_mesa()
        self.dealer_idx = self.dealer_idx % len(ativos)
        ordem = ativos[self.dealer_idx:] + ativos[:self.dealer_idx]
        self.dealer_idx = (self.dealer_idx + 1) % len(ativos)

        baralho = criar_baralho_duplo(self.usar_joker)
        random.shuffle(baralho)

        self.vira = baralho.pop()
        # Com Joker impresso, a vira e so decorativa/define quem comeca -
        # o unico coringa da mao e a carta de Joker (ver eh_coringa()).
        self.coringa_valor = None if self.usar_joker else _valor_seguinte(self.vira.valor)

        for j in ordem:
            j.mao = []
        for _ in range(3):
            for j in ordem:
                for _ in range(3):
                    j.mao.append(baralho.pop())

        self.descarte = [baralho.pop()]
        self.monte = baralho

        self._ordem = ordem
        self.indice_da_vez = 0
        self.comprou_nesta_vez = False
        self.resultado_mao = None
        self.jogadores_ja_agiram_na_mao = set()
        self.turnos_nesta_mao = 0

    def jogador_da_vez(self):
        if self.resultado_mao is not None or not self._ordem:
            return None
        return self._ordem[self.indice_da_vez]

    # ------------------------------------------------------------ Acoes
    def pode_comprar(self):
        return self.resultado_mao is None and not self.comprou_nesta_vez

    def _reciclar_monte_se_preciso(self):
        if self.monte:
            return
        topo = self.descarte[-1]
        resto = self.descarte[:-1]
        random.shuffle(resto)
        self.monte = resto
        self.descarte = [topo]

    def comprar_do_monte(self, jogador):
        self.jogadores_ja_agiram_na_mao.add(jogador.id)
        self._reciclar_monte_se_preciso()
        if not self.monte:
            # Exaustao total: reciclar nao ajudou (so sobrava 1 carta no
            # descarte, que fica intocavel). Forca a compra do descarte
            # para o turno sempre progredir e o jogo nunca travar.
            return self.comprar_do_descarte(jogador)
        carta = self.monte.pop()
        jogador.mao.append(carta)
        self.comprou_nesta_vez = True
        return carta

    def comprar_do_descarte(self, jogador):
        self.jogadores_ja_agiram_na_mao.add(jogador.id)
        if not self.descarte:
            return None
        carta = self.descarte.pop()
        jogador.mao.append(carta)
        self.comprou_nesta_vez = True
        return carta

    def pode_bater(self, jogador):
        if not self.comprou_nesta_vez or self.resultado_mao is not None:
            return False
        return pode_bater_mao(jogador.mao, self.coringa_valor)

    def pode_bater_mao_fechada(self, jogador):
        """'Mao fechada': bater sem comprar, valendo so na primeira vez que
        e a vez do jogador nesta mao (antes de qualquer compra dele) - a
        mao dele esta exatamente como foi distribuida. Paga o dobro dos
        pontos soltos dos adversarios (ver `_liquidar`), como no Buraco
        tradicional."""
        if self.comprou_nesta_vez or self.resultado_mao is not None:
            return False
        if jogador.id in self.jogadores_ja_agiram_na_mao:
            return False
        return pode_bater_mao(jogador.mao, self.coringa_valor)

    def bater(self, jogador):
        grupos = agrupar_para_bater(jogador.mao, self.coringa_valor)
        if grupos is None:
            return None
        self.resultado_mao = self._liquidar(jogador, grupos)
        self.resultado_mao["mao_fechada"] = False
        return self.resultado_mao

    def bater_mao_fechada(self, jogador):
        if not self.pode_bater_mao_fechada(jogador):
            return None
        grupos = agrupar_para_bater(jogador.mao, self.coringa_valor)
        if grupos is None:
            return None
        self.resultado_mao = self._liquidar(jogador, grupos, multiplicador=2)
        self.resultado_mao["mao_fechada"] = True
        return self.resultado_mao

    def pode_bater_descartando(self, jogador, carta):
        """True se descartar `carta` deixaria as 9 cartas restantes 100%
        combinadas (jeito mais comum de bater: a compra quase sempre deixa
        1 carta solta, e e essa carta que se descarta pra fechar a mao) -
        diferente de `pode_bater`, que so cobre o caso raro de as 10 cartas
        ja virem prontas sem precisar descartar nada."""
        if not self.comprou_nesta_vez or self.resultado_mao is not None:
            return False
        if carta not in jogador.mao:
            return False
        resto = list(jogador.mao)
        resto.remove(carta)
        return pode_bater_mao(resto, self.coringa_valor)

    def bater_descartando(self, jogador, carta):
        if not self.pode_bater_descartando(jogador, carta):
            return None
        resto = list(jogador.mao)
        resto.remove(carta)
        grupos = agrupar_para_bater(resto, self.coringa_valor)
        if grupos is None:
            return None
        jogador.mao.remove(carta)
        self.descarte.append(carta)
        self.resultado_mao = self._liquidar(jogador, grupos)
        self.resultado_mao["mao_fechada"] = False
        return self.resultado_mao

    def descartar(self, jogador, carta):
        jogador.mao.remove(carta)
        self.descarte.append(carta)
        self.comprou_nesta_vez = False
        self.indice_da_vez = (self.indice_da_vez + 1) % len(self._ordem)

        self.turnos_nesta_mao += 1
        if self.turnos_nesta_mao >= LIMITE_TURNOS_SEM_BATIDA:
            # Ninguem bateu depois de muitas rodadas (mao "empacada" -
            # nenhum jogador com uma boa combinacao a vista): a mao empata,
            # ninguem paga, e o jogo segue para a proxima. Evita travar a
            # partida indefinidamente por causa de uma distribuicao ruim.
            self.resultado_mao = {"vencedor": None, "pote": 0, "detalhes": [], "grupos": None,
                                   "empate": True, "mao_fechada": False}

    def marcar_eliminados(self):
        for j in self.jogadores_na_mesa():
            if j.stack <= 0:
                j.eliminado = True

    def _liquidar(self, batedor, grupos_batedor, multiplicador=1):
        pote = 0
        detalhes = []
        for j in self.jogadores_na_mesa():
            if j is batedor:
                continue
            _, soltas, pontos = calcular_pontos_soltos(j.mao, self.coringa_valor)
            pontos *= multiplicador
            pontos_pagos = min(pontos, j.stack)
            j.stack -= pontos_pagos
            pote += pontos_pagos
            detalhes.append({"jogador": j.nome, "pontos": pontos_pagos, "cartas_soltas": soltas})
        batedor.stack += pote
        return {
            "vencedor": batedor.nome,
            "pote": pote,
            "detalhes": detalhes,
            "grupos": grupos_batedor,
        }
