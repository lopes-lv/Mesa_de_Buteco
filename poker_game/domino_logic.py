"""
domino_logic.py - Motor do modo de jogo Dominó (bloqueio/compra,
livre-pra-todos, 2 a 4 jogadores, jogo duplo-seis de 28 peças).

Contém:
 - Peca: uma pedra normalizada (a <= b), com pontos = a + b
 - DominoPlayer: estado de cada jogador (stack, mão, elimincao)
 - DominoTable: orquestra uma mão completa (distribuir -> turnos -> bateu
   ou bloqueio -> liquidação)

Regras (ver GDD.md/MELHORIAS.md para a decisão de escopo): sem duplas, cada
jogador por si; quem não consegue jogar compra do monte até conseguir jogar
ou o monte esvaziar (nesse caso passa, sem escolha - não é uma decisão do
jogador, então nem chega a virar uma ação de UI/rede, ver domino_screen.py).
"""
import random

STACK_INICIAL = 1500
LADO_MIN, LADO_MAX = 0, 6
PECAS_POR_JOGADOR = 7
MAX_JOGADORES = 4

TIPO_BOT = "bot"
TIPO_HUMANO_LOCAL = "humano_local"
TIPO_HUMANO_REMOTO = "humano_remoto"


class Peca:
    """Uma pedra de dominó, normalizada (a <= b) para que Peca(3, 5) e
    Peca(5, 3) sejam a mesma peça (comparação e hash consistentes)."""
    __slots__ = ("a", "b")

    def __init__(self, a, b):
        self.a, self.b = (a, b) if a <= b else (b, a)

    @property
    def eh_carroca(self):
        return self.a == self.b

    @property
    def pontos(self):
        return self.a + self.b

    def combina(self, valor):
        return self.a == valor or self.b == valor

    def outro_lado(self, valor_encaixado):
        """Dado o valor que encaixou numa extremidade, devolve o valor que
        fica aberto do lado de fora da peça."""
        return self.b if valor_encaixado == self.a else self.a

    def __eq__(self, other):
        return isinstance(other, Peca) and self.a == other.a and self.b == other.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __repr__(self):
        return f"[{self.a}|{self.b}]"


def criar_pecas():
    """As 28 peças do jogo duplo-seis."""
    return [Peca(a, b) for a in range(LADO_MIN, LADO_MAX + 1) for b in range(a, LADO_MAX + 1)]


def jogadas_possiveis_em(mao, extremidade_esquerda, extremidade_direita):
    """Versão pura de `DominoTable.jogadas_possiveis`, sem depender de uma
    mesa/jogador de verdade - usada também pelo cliente remoto
    (`mesa_remota_domino_screen.py`) pra saber quais das próprias peças
    jogar, já que extremidade_esquerda/direita são informação pública."""
    if extremidade_esquerda is None and extremidade_direita is None:
        return [(p, "esquerda") for p in mao]

    pontas_iguais = extremidade_esquerda == extremidade_direita
    jogadas = []
    for p in mao:
        if p.combina(extremidade_esquerda):
            jogadas.append((p, "esquerda"))
        # Quando as duas pontas têm o mesmo valor, jogar "na direita"
        # produziria o mesmo resultado visual/lógico de jogar "na esquerda"
        # - evita oferecer a mesma jogada duas vezes.
        if p.combina(extremidade_direita) and not pontas_iguais:
            jogadas.append((p, "direita"))
    return jogadas


class DominoPlayer:
    def __init__(self, id_jogador, nome, stack=STACK_INICIAL, tipo=TIPO_BOT):
        self.id = id_jogador
        self.nome = nome
        self.stack = stack
        self.tipo = tipo
        self.mao = []
        self.eliminado = stack <= 0

    @property
    def is_bot(self):
        return self.tipo == TIPO_BOT

    def reset_para_mao(self):
        self.mao = []
        self.eliminado = self.stack <= 0

    def pontos_na_mao(self):
        return sum(p.pontos for p in self.mao)


class DominoTable:
    def __init__(self, jogadores):
        self.jogadores = jogadores
        self.dealer_idx = 0
        self.mao_numero = 0

        self.monte = []          # peças que ainda não foram distribuídas/compradas
        self.cadeia = []         # peças já jogadas, na ordem da mesa (esquerda -> direita)
        self.extremidade_esquerda = None
        self.extremidade_direita = None

        self._ordem = []         # ordem de turno fixa desta mão
        self.indice_da_vez = 0
        self.passes_consecutivos = 0
        self.resultado_mao = None
        self.ultima_compra_de = None  # id de quem comprou por último (feedback visual)

    # ------------------------------------------------------------ Setup
    def jogadores_na_mesa(self):
        return [j for j in self.jogadores if not j.eliminado]

    def jogo_tem_vencedor(self):
        return len(self.jogadores_na_mesa()) <= 1

    def iniciar_nova_mao(self):
        self.mao_numero += 1
        for j in self.jogadores:
            j.reset_para_mao()

        ativos = self.jogadores_na_mesa()
        self.dealer_idx = self.dealer_idx % len(ativos)
        ordem = ativos[self.dealer_idx:] + ativos[:self.dealer_idx]
        self.dealer_idx = (self.dealer_idx + 1) % len(ativos)

        pecas = criar_pecas()
        random.shuffle(pecas)

        for j in ordem:
            j.mao = [pecas.pop() for _ in range(PECAS_POR_JOGADOR)]

        self.monte = pecas
        self.cadeia = []
        self.extremidade_esquerda = None
        self.extremidade_direita = None

        self._ordem = ordem
        self.indice_da_vez = 0
        self.passes_consecutivos = 0
        self.resultado_mao = None
        self.ultima_compra_de = None

    def jogador_da_vez(self):
        if self.resultado_mao is not None or not self._ordem:
            return None
        return self._ordem[self.indice_da_vez]

    # ------------------------------------------------------------ Consultas
    def mesa_vazia(self):
        return not self.cadeia

    def pode_jogar(self, jogador):
        if self.mesa_vazia():
            return len(jogador.mao) > 0
        return any(p.combina(self.extremidade_esquerda) or p.combina(self.extremidade_direita)
                   for p in jogador.mao)

    def pode_comprar(self):
        return len(self.monte) > 0

    def deve_comprar(self, jogador):
        """True enquanto o jogador não tem jogada e ainda há peças no monte -
        compra não é uma decisão do jogador, é automático (ver módulo)."""
        return not self.pode_jogar(jogador) and self.pode_comprar()

    def deve_passar(self, jogador):
        """True quando não há jogada possível e o monte já secou - também
        automático, sem escolha do jogador."""
        return not self.pode_jogar(jogador) and not self.pode_comprar()

    def jogadas_possiveis(self, jogador):
        """Lista de (peca, lado) jogáveis agora. `lado` é 'esquerda' ou
        'direita'; com a mesa vazia, qualquer peça vale e o lado é sempre
        'esquerda' (mesa vazia não tem lado de verdade ainda)."""
        if self.mesa_vazia():
            return [(p, "esquerda") for p in jogador.mao]
        return jogadas_possiveis_em(jogador.mao, self.extremidade_esquerda, self.extremidade_direita)

    # ------------------------------------------------------------ Ações
    def comprar(self, jogador):
        if not self.monte:
            return None
        carta = self.monte.pop()
        jogador.mao.append(carta)
        self.ultima_compra_de = jogador.id
        return carta

    def jogar(self, jogador, peca, lado):
        """Aplica a jogada se for legal. Retorna True se aplicou."""
        if peca not in jogador.mao:
            return False

        if self.mesa_vazia():
            self.cadeia.append(peca)
            self.extremidade_esquerda = peca.a
            self.extremidade_direita = peca.b
        elif lado == "esquerda" and peca.combina(self.extremidade_esquerda):
            self.cadeia.insert(0, peca)
            self.extremidade_esquerda = peca.outro_lado(self.extremidade_esquerda)
        elif lado == "direita" and peca.combina(self.extremidade_direita):
            self.cadeia.append(peca)
            self.extremidade_direita = peca.outro_lado(self.extremidade_direita)
        else:
            return False

        jogador.mao.remove(peca)
        self.passes_consecutivos = 0

        if not jogador.mao:
            self.resultado_mao = self._liquidar_bateu(jogador)
        else:
            self._avancar_turno()
        return True

    def passar(self, jogador):
        self.passes_consecutivos += 1
        if self.passes_consecutivos >= len(self._ordem):
            self.resultado_mao = self._liquidar_bloqueio()
        else:
            self._avancar_turno()

    def _avancar_turno(self):
        self.indice_da_vez = (self.indice_da_vez + 1) % len(self._ordem)

    def marcar_eliminados(self):
        for j in self.jogadores_na_mesa():
            if j.stack <= 0:
                j.eliminado = True

    # ------------------------------------------------------------ Liquidação
    def _liquidar_bateu(self, vencedor):
        pote = 0
        detalhes = []
        for j in self.jogadores_na_mesa():
            if j is vencedor:
                continue
            pontos = j.pontos_na_mao()
            pontos_pagos = min(pontos, j.stack)
            j.stack -= pontos_pagos
            pote += pontos_pagos
            detalhes.append({"jogador": j.nome, "pontos": pontos_pagos})
        vencedor.stack += pote
        return {"vencedor": vencedor.nome, "pote": pote, "detalhes": detalhes,
                "bloqueio": False, "empate": False}

    def _liquidar_bloqueio(self):
        """Ninguém consegue jogar e o monte secou: quem tem menos pontos na
        mão vence a rodada (empate divide o pote, como um split pot)."""
        ativos = self.jogadores_na_mesa()
        menor = min(j.pontos_na_mao() for j in ativos)
        vencedores = [j for j in ativos if j.pontos_na_mao() == menor]

        pote = 0
        detalhes = []
        for j in ativos:
            if j in vencedores:
                continue
            pontos = j.pontos_na_mao()
            pontos_pagos = min(pontos, j.stack)
            j.stack -= pontos_pagos
            pote += pontos_pagos
            detalhes.append({"jogador": j.nome, "pontos": pontos_pagos})

        divisao = pote // len(vencedores)
        resto = pote % len(vencedores)
        for i, v in enumerate(vencedores):
            v.stack += divisao + (1 if i < resto else 0)

        return {"vencedor": ", ".join(v.nome for v in vencedores), "pote": pote,
                "detalhes": detalhes, "bloqueio": True, "empate": len(vencedores) > 1}
