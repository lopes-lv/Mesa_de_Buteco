"""
game_logic.py - Motor do jogo de Texas Hold'em

Contém:
 - Player: estado de cada jogador (stack, cartas, aposta, status)
 - BettingRound: controla de quem é a vez, valor mínimo de raise, etc.
 - Table: orquestra uma mão completa (blinds -> preflop -> flop -> turn -> river -> showdown)
 - Cálculo de pote principal + side pots (para all-ins) e split pot em empates
"""
from deck import Deck
from hand_evaluator import melhor_mao, determinar_vencedores

# Estrutura de blinds crescentes (estilo torneio).
# Cada item: (small_blind, big_blind) e o nível dura N mãos.
ESTRUTURA_BLINDS = [
    (10, 20), (15, 30), (25, 50), (50, 100), (75, 150),
    (100, 200), (150, 300), (200, 400), (300, 600), (400, 800),
]
MAOS_POR_NIVEL = 5
STACK_INICIAL = 1500


class Player:
    def __init__(self, id_jogador, nome, stack=STACK_INICIAL, is_bot=True):
        self.id = id_jogador
        self.nome = nome
        self.stack = stack
        self.is_bot = is_bot
        self.reset_para_mao()

    def reset_para_mao(self):
        self.mao = []
        self.aposta_rodada = 0       # quanto apostou na rodada de apostas atual
        self.total_apostado_mao = 0  # total apostado na mão inteira (para side pots)
        self.foldou = False
        self.all_in = False
        self.eliminado = self.stack <= 0

    def apostar(self, valor):
        valor = min(valor, self.stack)
        self.stack -= valor
        self.aposta_rodada += valor
        self.total_apostado_mao += valor
        if self.stack == 0:
            self.all_in = True
        return valor

    def pode_agir(self):
        return not self.foldou and not self.all_in and not self.eliminado


class BettingRound:
    """Controla uma única rodada de apostas (pre-flop, flop, turn ou river)."""

    def __init__(self, jogadores, indice_inicial, aposta_minima):
        self.jogadores = jogadores
        self.indice_atual = indice_inicial
        self.aposta_alvo = aposta_minima  # maior aposta atual na mesa
        self.ultimo_raise_valor = aposta_minima
        self.jogadores_que_agiram = set()
        self._ajustar_para_jogador_valido()

    def jogador_da_vez(self):
        if self.rodada_terminou():
            return None
        return self.jogadores[self.indice_atual]

    def _ajustar_para_jogador_valido(self):
        tentativas = 0
        n = len(self.jogadores)
        while tentativas < n and not self.jogadores[self.indice_atual].pode_agir():
            self.indice_atual = (self.indice_atual + 1) % n
            tentativas += 1

    def _avancar_indice(self):
        n = len(self.jogadores)
        self.indice_atual = (self.indice_atual + 1) % n

    def aplicar_acao(self, jogador, acao, valor_raise=0):
        """acao em {'fold', 'check', 'call', 'raise'}"""
        if acao == "fold":
            jogador.foldou = True
        elif acao == "check":
            pass
        elif acao == "call":
            faltante = self.aposta_alvo - jogador.aposta_rodada
            jogador.apostar(max(0, faltante))
        elif acao == "raise":
            total_necessario = (self.aposta_alvo - jogador.aposta_rodada) + valor_raise
            jogador.apostar(total_necessario)
            self.ultimo_raise_valor = valor_raise
            self.aposta_alvo = jogador.aposta_rodada
            # novo raise reabre a ação para todos que ainda podem jogar
            self.jogadores_que_agiram = set()

        self.jogadores_que_agiram.add(jogador.id)
        self._avancar_indice()
        self._ajustar_para_jogador_valido()

    def jogadores_ativos_na_mao(self):
        return [j for j in self.jogadores if not j.foldou and not j.eliminado]

    def rodada_terminou(self):
        ativos = self.jogadores_ativos_na_mao()
        if len(ativos) <= 1:
            return True
        pendentes = [j for j in ativos if j.pode_agir()]
        if not pendentes:
            return True
        # termina quando todo jogador que pode agir já agiu E está com aposta igualada
        for j in pendentes:
            if j.id not in self.jogadores_que_agiram or j.aposta_rodada != self.aposta_alvo:
                return False
        return True


def calcular_potes(jogadores):
    """
    Calcula pote principal + side pots com base no total apostado por
    cada jogador na mão (suporta all-ins parciais).
    Retorna lista de dicts: {"valor": int, "elegiveis": [ids de jogadores]}
    """
    participantes = [j for j in jogadores if j.total_apostado_mao > 0]
    if not participantes:
        return []

    niveis = sorted(set(j.total_apostado_mao for j in participantes))
    potes = []
    nivel_anterior = 0
    for nivel in niveis:
        contribuintes = [j for j in participantes if j.total_apostado_mao >= nivel]
        incremento = nivel - nivel_anterior
        valor_pote = incremento * len(contribuintes)
        if valor_pote > 0:
            elegiveis = [j.id for j in contribuintes if not j.foldou]
            potes.append({"valor": valor_pote, "elegiveis": elegiveis})
        nivel_anterior = nivel

    # funde potes consecutivos com exatamente os mesmos elegíveis
    potes_fundidos = []
    for p in potes:
        if potes_fundidos and potes_fundidos[-1]["elegiveis"] == p["elegiveis"]:
            potes_fundidos[-1]["valor"] += p["valor"]
        else:
            potes_fundidos.append(p)
    return potes_fundidos


class Table:
    def __init__(self, jogadores):
        self.jogadores = jogadores  # lista de Player, ordem de assento fixa
        self.dealer_idx = 0
        self.deck = None
        self.comunitarias = []
        self.pote_total = 0
        self.estagio = "preflop"
        self.mao_numero = 0
        self.nivel_blind_idx = 0
        self.rodada_atual = None
        self.log = []

    # ---------- Blinds (estrutura de torneio) ----------
    def blinds_atuais(self):
        idx = min(self.nivel_blind_idx, len(ESTRUTURA_BLINDS) - 1)
        return ESTRUTURA_BLINDS[idx]

    def atualizar_nivel_blind(self):
        self.nivel_blind_idx = self.mao_numero // MAOS_POR_NIVEL
        self.nivel_blind_idx = min(self.nivel_blind_idx, len(ESTRUTURA_BLINDS) - 1)

    # ---------- Fluxo de uma mão ----------
    def jogadores_na_mesa(self):
        return [j for j in self.jogadores if not j.eliminado]

    def iniciar_nova_mao(self):
        self.mao_numero += 1
        self.atualizar_nivel_blind()
        self.deck = Deck()
        self.comunitarias = []
        self.estagio = "preflop"
        self.log = []
        for j in self.jogadores:
            j.reset_para_mao()

        ativos = self.jogadores_na_mesa()
        if len(ativos) <= 1:
            return  # jogo acabou

        # avança dealer para o próximo jogador não eliminado
        n = len(self.jogadores)
        for _ in range(n):
            self.dealer_idx = (self.dealer_idx + 1) % n
            if not self.jogadores[self.dealer_idx].eliminado:
                break

        sb, bb = self.blinds_atuais()
        idx_sb = self._proximo_ativo(self.dealer_idx)
        idx_bb = self._proximo_ativo(idx_sb)
        self.jogadores[idx_sb].apostar(sb)
        self.jogadores[idx_bb].apostar(bb)
        self.log.append(f"{self.jogadores[idx_sb].nome} paga Small Blind ({sb})")
        self.log.append(f"{self.jogadores[idx_bb].nome} paga Big Blind ({bb})")

        # distribui 2 cartas para cada jogador ativo
        for j in ativos:
            j.mao = self.deck.comprar(2)

        idx_primeiro_a_agir = self._proximo_ativo(idx_bb)
        self.rodada_atual = BettingRound(self.jogadores, idx_primeiro_a_agir, aposta_minima=bb)

    def _proximo_ativo(self, indice):
        n = len(self.jogadores)
        i = indice
        for _ in range(n):
            i = (i + 1) % n
            if not self.jogadores[i].eliminado:
                return i
        return indice

    def avancar_estagio(self):
        """Chamado quando a rodada de apostas atual termina."""
        for j in self.jogadores:
            j.aposta_rodada = 0

        ativos = [j for j in self.jogadores if not j.foldou and not j.eliminado]
        if self.estagio == "preflop":
            self.comunitarias += self.deck.comprar(3)
            self.estagio = "flop"
        elif self.estagio == "flop":
            self.comunitarias += self.deck.comprar(1)
            self.estagio = "turn"
        elif self.estagio == "turn":
            self.comunitarias += self.deck.comprar(1)
            self.estagio = "river"
        elif self.estagio == "river":
            self.estagio = "showdown"
            return

        if len(ativos) <= 1:
            self.estagio = "showdown"
            return

        idx_inicial = self._proximo_ativo(self.dealer_idx)
        self.rodada_atual = BettingRound(self.jogadores, idx_inicial, aposta_minima=0)

    def mao_finalizada_por_fold(self):
        ativos = [j for j in self.jogadores if not j.foldou and not j.eliminado]
        return len(ativos) == 1

    def processar_showdown(self):
        """
        Avalia mãos, calcula potes/side-pots e distribui fichas.
        Retorna lista de resultados para exibição:
        [{"pote": valor, "vencedores": [nomes], "categoria": str}]
        """
        potes = calcular_potes(self.jogadores)
        ativos = [j for j in self.jogadores if not j.foldou and not j.eliminado]
        resultados_exibicao = []

        if len(ativos) == 1:
            unico = ativos[0]
            valor_total = sum(p["valor"] for p in potes)
            unico.stack += valor_total
            resultados_exibicao.append({
                "pote": valor_total, "vencedores": [unico.nome], "categoria": "Demais jogadores desistiram"
            })
            return resultados_exibicao

        avaliacoes = {}
        for j in ativos:
            avaliacoes[j.id] = melhor_mao(j.mao + self.comunitarias)

        for pote in potes:
            elegiveis_ids = [pid for pid in pote["elegiveis"]]
            if not elegiveis_ids:
                continue
            sub_avaliacoes = {pid: avaliacoes[pid] for pid in elegiveis_ids if pid in avaliacoes}
            if not sub_avaliacoes:
                continue
            vencedores_ids = determinar_vencedores(sub_avaliacoes)
            divisao = pote["valor"] // len(vencedores_ids)
            resto = pote["valor"] % len(vencedores_ids)
            nomes_vencedores = []
            for i, pid in enumerate(vencedores_ids):
                jogador = next(j for j in self.jogadores if j.id == pid)
                ganho = divisao + (1 if i < resto else 0)  # distribui o resto (arredondamento)
                jogador.stack += ganho
                nomes_vencedores.append(jogador.nome)
            categoria = sub_avaliacoes[vencedores_ids[0]][1]
            resultados_exibicao.append({
                "pote": pote["valor"], "vencedores": nomes_vencedores, "categoria": categoria
            })

        return resultados_exibicao

    def marcar_eliminados(self):
        for j in self.jogadores:
            if j.stack <= 0:
                j.eliminado = True

    def jogo_tem_vencedor(self):
        restantes = self.jogadores_na_mesa()
        return len(restantes) <= 1
