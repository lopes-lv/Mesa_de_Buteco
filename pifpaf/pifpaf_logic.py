"""
pifpaf_logic.py - Motor do modo de jogo Pif Paf.

Ver pifpaf/README.md para o resumo das regras e as decisões de design.
Contém:
 - PifPafPlayer: estado de cada jogador (vitorias, mao)
 - Baralho duplo (104 cartas), com 4 Jokers impressos opcionais como coringa
 - Validacao de combinacoes (trinca / sequencia), com suporte a coringa
 - PifPafTable: orquestra uma mao completa (distribuir -> turnos -> batida -> liquidacao)
"""
import random
from itertools import combinations

from core.deck import NAIPES, VALORES, NAIPE_CORINGA, VALOR_CORINGA, Card

VITORIAS_PARA_VENCER = 3  # quem bater primeiro N maos vence a partida
LIMITE_TURNOS_SEM_BATIDA = 200
JOKERS_POR_BARALHO_DUPLO = 4  # 2 por copia de 52, baralho duplo = 4

# Origem da acao de um jogador (mesmo padrao de game_logic.py, ver
# MULTIPLAYER_PLANO.md secao 7): PifPafTable nunca olha para este campo.
TIPO_BOT = "bot"
TIPO_HUMANO_LOCAL = "humano_local"
TIPO_HUMANO_REMOTO = "humano_remoto"


def criar_baralho_duplo(usar_joker=False):
    """Dois baralhos de 52 cartas combinados (104 cartas). Com `usar_joker`,
    acrescenta 4 Jokers impressos (2 por copia de 52), o unico coringa do
    jogo (ver `eh_coringa`)."""
    baralho = [Card(v, n) for _ in range(2) for n in NAIPES for v in VALORES]
    if usar_joker:
        baralho += [Card(VALOR_CORINGA, NAIPE_CORINGA) for _ in range(JOKERS_POR_BARALHO_DUPLO)]
    return baralho


def eh_coringa(carta):
    """True se `carta` e um Joker impresso (unico coringa do Pif Paf)."""
    return carta.naipe == NAIPE_CORINGA


def valor_pontos(carta):
    """Pontuacao de uma carta solta (nao combinada) ao fim da mao."""
    if eh_coringa(carta):
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
        # Faixa de valores que uma sequência pode ocupar nesta leitura do As
        # (o Joker que estende a ponta não pode sair dela).
        piso, teto = (1, 13) if as_baixo else (2, 14)
        for i in range(len(ordenados)):
            for j in range(i, len(ordenados)):
                ini, fim = ordenados[i], ordenados[j]
                span = fim - ini + 1
                presentes = [v for v in ordenados if ini <= v <= fim]
                falta = span - len(presentes)
                if falta > coringas_disp:
                    continue
                cartas = tuple(valores[v] for v in presentes)
                if span >= 3:
                    candidatos.append((cartas, falta))
                    continue
                # Janela curta (2 cartas naturais seguidas): o Joker estende a
                # ponta até fechar 3 posições. Uma carta sozinha não vira
                # sequência só com Jokers.
                if i == j:
                    continue
                extra = 3 - span  # i < j garante span >= 2, logo 1 Joker
                cabe = ini - extra >= piso or fim + extra <= teto
                if cabe and falta + extra <= coringas_disp:
                    candidatos.append((cartas, falta + extra))
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


def carta_completa_combinacao(carta, mao):
    """True se `carta` (candidata a compra) formaria, junto de cartas ja na
    mao, um grupo real (2+ cartas naturais associadas a ela) - usado pela
    IA para decidir se vale a pena comprar do descarte."""
    if eh_coringa(carta):
        return True
    coringas_disp = sum(1 for c in mao if eh_coringa(c))
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


def pode_bater_mao(mao):
    """True se a mao inteira (9 ou 10 cartas) pode ser organizada em
    trincas/sequencias validas, sem nenhuma carta solta."""
    naturais = [c for c in mao if not eh_coringa(c)]
    n_coringas = len(mao) - len(naturais)
    return _encaixar_tudo(naturais, n_coringas) is not None


def agrupar_para_bater(mao):
    """Retorna os grupos (listas de Card) que zeram a mao, ou None se a mao
    nao pode bater. Coringas usados para completar um grupo sao anexados
    ao final da lista de cartas naturais daquele grupo."""
    naturais = [c for c in mao if not eh_coringa(c)]
    coringas = [c for c in mao if eh_coringa(c)]
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


def calcular_pontos_soltos(mao):
    """Agrupa a mao de forma gulosa (sempre pegando o maior grupo valido
    disponivel) para minimizar as cartas soltas, e retorna
    (grupos, cartas_soltas, pontos_soltos). Usado para pontuar quem nao
    bateu - nao precisa ser a organizacao perfeita, so uma organizacao
    razoavel (times reais tambem nem sempre acham o encaixe otimo)."""
    naturais = [c for c in mao if not eh_coringa(c)]
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
    pontos = sum(valor_pontos(c) for c in soltas) + coringas_disp * 20
    return grupos, soltas, pontos


# ---------------------------------------------------------------- Jogador
class PifPafPlayer:
    def __init__(self, id_jogador, nome, tipo=TIPO_BOT):
        self.id = id_jogador
        self.nome = nome
        self.vitorias = 0  # maos vencidas (bateu primeiro) nesta partida
        self.tipo = tipo
        self.mao = []

    @property
    def is_bot(self):
        return self.tipo == TIPO_BOT

    def reset_para_mao(self):
        self.mao = []


# ---------------------------------------------------------------- Mesa
class PifPafTable:
    def __init__(self, jogadores, usar_joker=False):
        self.jogadores = jogadores
        self.usar_joker = usar_joker
        self.dealer_idx = 0
        self.mao_numero = 0

        self.monte = []
        self.descarte = []

        self._ordem = []
        self.indice_da_vez = 0
        self.comprou_nesta_vez = False
        self.resultado_mao = None
        self.jogadores_ja_agiram_na_mao = set()  # ids que ja compraram/descartaram nesta mao

    def jogadores_na_mesa(self):
        return list(self.jogadores)

    def vencedor_do_jogo(self):
        """Quem chegou a `VITORIAS_PARA_VENCER` maos vencidas (None se ninguem)."""
        return next((j for j in self.jogadores if j.vitorias >= VITORIAS_PARA_VENCER), None)

    def jogo_tem_vencedor(self):
        return self.vencedor_do_jogo() is not None

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
        return pode_bater_mao(jogador.mao)

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
        return pode_bater_mao(jogador.mao)

    def bater(self, jogador):
        grupos = agrupar_para_bater(jogador.mao)
        if grupos is None:
            return None
        self.resultado_mao = self._liquidar(jogador, grupos)
        self.resultado_mao["mao_fechada"] = False
        return self.resultado_mao

    def bater_mao_fechada(self, jogador):
        if not self.pode_bater_mao_fechada(jogador):
            return None
        grupos = agrupar_para_bater(jogador.mao)
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
        return pode_bater_mao(resto)

    def bater_descartando(self, jogador, carta):
        if not self.pode_bater_descartando(jogador, carta):
            return None
        resto = list(jogador.mao)
        resto.remove(carta)
        grupos = agrupar_para_bater(resto)
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
            self.resultado_mao = {"vencedor": None, "vitorias_ganhas": 0, "detalhes": [], "grupos": None,
                                   "empate": True, "mao_fechada": False}

    def _liquidar(self, batedor, grupos_batedor, multiplicador=1):
        """Registra a vitoria da mao (`multiplicador` = 2 na mao fechada). Os
        pontos soltos dos adversarios entram so como informacao na tela."""
        batedor.vitorias += multiplicador
        detalhes = []
        for j in self.jogadores:
            if j is batedor:
                continue
            _, soltas, pontos = calcular_pontos_soltos(j.mao)
            detalhes.append({"jogador": j.nome, "pontos": pontos, "cartas_soltas": soltas})
        return {
            "vencedor": batedor.nome,
            "vitorias_ganhas": multiplicador,
            "detalhes": detalhes,
            "grupos": grupos_batedor,
        }
