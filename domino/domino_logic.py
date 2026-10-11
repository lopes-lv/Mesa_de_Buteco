"""
domino_logic.py - Motor do modo de jogo Dominó (corrida de pontos até 250,
livre-pra-todos, 3 ou 4 jogadores, jogo duplo-seis).

Contém:
 - Peca: uma pedra normalizada (a <= b), com pontos = a + b
 - PecaNaMesa: uma pedra já jogada na mesa, com a orientação visual
   (interno/externo) resolvida - necessária pra desenhar a peça encaixando
   os números certos com a vizinha (ver domino_theme.py)
 - DominoPlayer: estado de cada jogador (mão, pontuação acumulada)
 - DominoTable: orquestra uma mão completa (distribuir -> turnos -> bateu
   ou travamento -> pontuação) e a corrida até 250 pontos entre mãos

Regras (ver GDD.md/MELHORIAS.md para a decisão de escopo): sem duplas, cada
jogador por si, só 3 ou 4 jogadores por mesa (28 peças não dividem por 2, e
sem monte não sobra lugar pra peça nenhuma - por isso com 3 jogadores a
peça 0/0 é retirada do jogo pra fechar 27 = 9x3). Não existe compra: cada
jogador recebe todas as peças que vai ter na mão de uma vez, e quem não
consegue jogar passa a vez manualmente (ver domino_screen.py) - a decisão do
jogador é sempre "qual peça jogar, e em qual ramo" ou "passar".

A mesa é uma "cruz": a peça de abertura fica no centro e a linha principal
cresce pra esquerda/direita, como um dominó de mesa normal. Quando a peça de
abertura é uma carroça, ela vira um "spinner"/bucho - os dois lados livres
dela (perpendiculares à linha) também podem receber peça, então o jogo
também cresce pra cima/baixo a partir dali. Só a carroça de ABERTURA faz
isso; outras carroças que aparecerem depois em qualquer ramo só ficam
"deitadas" na hora de desenhar (ver domino_screen.py), sem ramificar de
novo.
"""
import random
from collections import namedtuple

LADO_MIN, LADO_MAX = 0, 6
DIRECOES = ("esquerda", "direita", "cima", "baixo")

TIPO_BOT = "bot"
TIPO_HUMANO_LOCAL = "humano_local"
TIPO_HUMANO_REMOTO = "humano_remoto"

# Fases visuais do início de mão (ver domino_screen.py/mesa_remota_domino_screen.py):
# a mão inteira já é conhecida desde `iniciar_nova_mao` (sem monte, sem
# compra - ver acima), então "embaralhando"/"escolhendo" são puramente
# cosméticas/locais a cada tela, não fazem parte do estado real da mesa.
FASE_EMBARALHANDO = "embaralhando"
FASE_ESCOLHENDO = "escolhendo"
FASE_JOGANDO = "jogando"
DURACAO_EMBARALHAR = 1.0

PONTUACAO_VITORIA = 250
BONUS_TRANCAR_PARCIAL = 50   # todo mundo passa e a vez volta pra quem jogou, que ainda consegue jogar
BONUS_PASSE = 10             # pra quem jogou imediatamente antes de alguém passar
BONUS_CARROCA_FECHOU = 30    # bônus extra se a última peça (a que bateu) for carroça


class Peca:
    """Uma pedra de dominó, normalizada (a <= b) para que Peca(3, 5) e
    Peca(5, 3) sejam a mesma peça (comparação e hash consistentes). Essa
    normalização é só de identidade - a orientação em que a peça aparece na
    mesa é resolvida à parte, ver PecaNaMesa."""
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


# Uma peça já colocada na mesa, com os valores já orientados visualmente:
# `interno` é o ponto que toca a peça anterior (voltado pro centro da mesa),
# `externo` é o ponto que fica aberto (voltado pra fora, é o valor que
# entra em `DominoTable.extremidades`). Nomes neutros de direção porque um
# mesmo ramo pode crescer tanto na horizontal (esquerda/direita) quanto na
# vertical (cima/baixo, só quando há spinner) - quem desenha decide, pela
# direção do ramo, se interno/externo viram esquerda/direita ou cima/baixo
# na tela (ver domino_screen.py).
PecaNaMesa = namedtuple("PecaNaMesa", "peca interno externo")


def criar_pecas(quantidade_jogadores=4):
    """As peças do jogo duplo-seis. Com 3 jogadores a peça 0/0 é retirada
    (27 peças, 9 por jogador); com 4, o jogo completo (28 peças, 7 cada) -
    nos dois casos dá uma divisão exata, então não sobra peça nenhuma pra
    monte."""
    pecas = [Peca(a, b) for a in range(LADO_MIN, LADO_MAX + 1) for b in range(a, LADO_MAX + 1)]
    if quantidade_jogadores == 3:
        pecas = [p for p in pecas if p != Peca(0, 0)]
    return pecas


def jogadas_possiveis_em(mao, extremidades, eh_spinner=False, peca_obrigatoria=None):
    """Versão pura de `DominoTable.jogadas_possiveis`, sem depender de uma
    mesa/jogador de verdade - usada também pelo cliente remoto
    (`mesa_remota_domino_screen.py`) pra saber quais das próprias peças
    jogar, já que o estado do tabuleiro é informação pública.

    `extremidades` é um dict com as 4 chaves de `DIRECOES`; uma direção
    inativa (mesa vazia, ou cima/baixo fora de uma mão com spinner) vale
    `None`. Mesa vazia é inferida de todas as direções virem `None`, já que
    esquerda/direita sempre ficam preenchidas juntas assim que a primeira
    peça é jogada."""
    ativas = [d for d in DIRECOES if extremidades.get(d) is not None]
    if not ativas:
        if peca_obrigatoria is not None:
            return [(peca_obrigatoria, "esquerda")] if peca_obrigatoria in mao else []
        # Toda abertura de mão é obrigatoriamente uma carroça - na 1ª mão
        # (e após travamento total) é uma carroça específica (6/6, via
        # `peca_obrigatoria` acima); nas demais, quem abre escolhe qual
        # carroça jogar entre as que tiver. Só abre livre com qualquer peça
        # se não tiver carroça nenhuma na mão (não trava o jogo por isso).
        carrocas = [p for p in mao if p.eh_carroca]
        pecas_validas = carrocas if carrocas else mao
        return [(p, "esquerda") for p in pecas_validas]

    if not eh_spinner:
        esq, dirr = extremidades["esquerda"], extremidades["direita"]
        pontas_iguais = esq == dirr
        jogadas = []
        for p in mao:
            if p.combina(esq):
                jogadas.append((p, "esquerda"))
            # Quando as duas pontas têm o mesmo valor, jogar "na direita"
            # produziria o mesmo resultado visual/lógico de jogar "na
            # esquerda" - evita oferecer a mesma jogada duas vezes.
            if p.combina(dirr) and not pontas_iguais:
                jogadas.append((p, "direita"))
        return jogadas

    # Com spinner, cada direção é um lugar fisicamente diferente na mesa -
    # mesmo que duas pontas tenham o mesmo valor (ex.: logo depois do
    # spinner sozinho, as 4 pontas começam iguais), não faz sentido esconder
    # nenhuma: o jogador está escolhendo pra que lado o jogo cresce.
    jogadas = []
    for d in ativas:
        valor = extremidades[d]
        for p in mao:
            if p.combina(valor):
                jogadas.append((p, d))
    return jogadas


class DominoPlayer:
    def __init__(self, id_jogador, nome, stack=0, tipo=TIPO_BOT):
        self.id = id_jogador
        self.nome = nome
        self.stack = stack  # vestigial: só existe pra manter a assinatura usada
        self.tipo = tipo    # pelo código genérico de multiplayer em main.py
        self.mao = []
        self.pontuacao = 0

    @property
    def is_bot(self):
        return self.tipo == TIPO_BOT

    def reset_para_mao(self):
        """Limpa a mão pra uma mão nova - a pontuação NÃO reseta, ela é
        acumulada ao longo de todo o jogo (corrida até 250 pontos)."""
        self.mao = []

    def pontos_na_mao(self):
        return sum(p.pontos for p in self.mao)


class DominoTable:
    def __init__(self, jogadores):
        self.jogadores = jogadores
        self.mao_numero = 0

        self.primeira_peca = None   # PecaNaMesa da peça de abertura (centro da mesa)
        self.eh_spinner = False     # True se a peça de abertura for carroça (bucho: cima/baixo liberados)
        self.ramos = {d: [] for d in DIRECOES}          # cada um cresce de dentro pra fora
        self.extremidades = {d: None for d in DIRECOES}  # valor aberto na ponta de cada ramo

        self._ordem = []          # ordem de turno fixa desta mão
        self.indice_da_vez = 0
        self.passes_consecutivos = 0
        self.resultado_mao = None

        self.ultimo_a_jogar_id = None   # id de quem fez a última jogada (p/ bônus de trancar)
        self.ultimo_vencedor_id = None  # id de quem bateu na mão anterior (abre a próxima)
        self.forcar_abertura_6_6 = True  # 1ª mão do jogo, e toda mão após travamento total
        self.peca_obrigatoria = None    # peça que a abertura desta mão é obrigada a jogar

        # Preenchidos a cada `jogar`/`passar`, só pra tela montar mensagens
        # de histórico - não fazem parte do estado "de verdade" da mesa.
        self.pontuou_pontas = None
        self.trancou_parcial = False
        self.bonus_passe_para = None

    # ------------------------------------------------------------ Setup
    def iniciar_nova_mao(self):
        self.mao_numero += 1
        for j in self.jogadores:
            j.reset_para_mao()

        quantidade = len(self.jogadores)
        pecas = criar_pecas(quantidade)
        random.shuffle(pecas)
        pecas_por_jogador = len(pecas) // quantidade

        ordem_base = list(self.jogadores)
        if not self.forcar_abertura_6_6 and self.ultimo_vencedor_id is not None:
            idx = next((i for i, j in enumerate(ordem_base) if j.id == self.ultimo_vencedor_id), 0)
            ordem_base = ordem_base[idx:] + ordem_base[:idx]

        for j in ordem_base:
            j.mao = [pecas.pop() for _ in range(pecas_por_jogador)]

        self.primeira_peca = None
        self.eh_spinner = False
        self.ramos = {d: [] for d in DIRECOES}
        self.extremidades = {d: None for d in DIRECOES}
        self.indice_da_vez = 0
        self.passes_consecutivos = 0
        self.resultado_mao = None
        self.ultimo_a_jogar_id = None
        self.pontuou_pontas = None
        self.trancou_parcial = False
        self.bonus_passe_para = None

        if self.forcar_abertura_6_6:
            dono = next((j for j in ordem_base if Peca(6, 6) in j.mao), ordem_base[0])
            idx = ordem_base.index(dono)
            self._ordem = ordem_base[idx:] + ordem_base[:idx]
            self.peca_obrigatoria = Peca(6, 6)
        else:
            self._ordem = ordem_base
            self.peca_obrigatoria = None

    def jogador_da_vez(self):
        if self.resultado_mao is not None or not self._ordem:
            return None
        return self._ordem[self.indice_da_vez]

    def vencedor_do_jogo(self):
        """Jogador com pontuação >= 250, se houver (chamar só depois que uma
        mão termina - a checagem de vitória não acontece no meio da mão)."""
        candidatos = [j for j in self.jogadores if j.pontuacao >= PONTUACAO_VITORIA]
        if not candidatos:
            return None
        return max(candidatos, key=lambda j: j.pontuacao)

    # ------------------------------------------------------------ Consultas
    def mesa_vazia(self):
        return self.primeira_peca is None

    def pode_jogar(self, jogador):
        return len(self.jogadas_possiveis(jogador)) > 0

    def bucho_liberado(self):
        """O bucho (cima/baixo) só pode receber peça depois que a carroça de
        abertura já tiver sido jogada dos dois lados da linha principal
        (esquerda E direita) - regra tradicional do spinner. Antes disso,
        cima/baixo existem (self.extremidades já tem valor) mas não são uma
        jogada válida ainda."""
        return len(self.ramos["esquerda"]) > 0 and len(self.ramos["direita"]) > 0

    def jogadas_possiveis(self, jogador):
        """Lista de (peca, direcao) jogáveis agora. `direcao` é uma das
        chaves de `DIRECOES`; com a mesa vazia, 'esquerda' é só uma
        convenção (mesa vazia não tem direção de verdade ainda) e a peça
        pode ser obrigatória (abertura com 6/6)."""
        extremidades = self.extremidades
        if self.eh_spinner and not self.bucho_liberado():
            extremidades = dict(self.extremidades)
            extremidades["cima"] = None
            extremidades["baixo"] = None
        return jogadas_possiveis_em(jogador.mao, extremidades, self.eh_spinner, self.peca_obrigatoria)

    def pontos_pontas(self):
        """Soma das pontas abertas que contam pra pontuação agora, dobrando
        o valor de uma ponta quando a peça que está nela é carroça (estilo
        "All Fives"). Esquerda/direita contam desde a peça de abertura;
        cima/baixo (bucho) só entram depois que o ramo realmente tiver uma
        peça - só existir como jogada válida não é o bastante. Com uma peça
        só em jogo (a de abertura, nenhum ramo ainda), o total já sai certo
        via extremidade_esquerda + extremidade_direita, sem dobrar de novo -
        evita contar um spinner sozinho como 4x o valor em vez de 2x."""
        if self.primeira_peca is None:
            return 0
        total_pecas = 1 + sum(len(self.ramos[d]) for d in DIRECOES)
        if total_pecas == 1:
            return self.extremidades["esquerda"] + self.extremidades["direita"]

        soma = 0
        for d in ("esquerda", "direita"):
            ramo = self.ramos[d]
            ponta_carroca = ramo[-1].peca.eh_carroca if ramo else self.primeira_peca.peca.eh_carroca
            soma += self.extremidades[d] * (2 if ponta_carroca else 1)
        for d in ("cima", "baixo"):
            ramo = self.ramos[d]
            if ramo:
                soma += self.extremidades[d] * (2 if ramo[-1].peca.eh_carroca else 1)
        return soma

    def pontuacao_se_jogar(self, peca, direcao):
        """Quantos pontos essa jogada renderia pelo múltiplo de 5 nas
        pontas, sem aplicar de fato - usado pela IA do bot pra preferir
        jogadas que pontuam. 0 se a jogada não pontuaria."""
        if self.mesa_vazia():
            pontos = peca.a + peca.b
            return pontos if pontos % 5 == 0 else 0

        item, novo_valor = self._prever_insercao(peca, direcao)
        soma = 0
        for d in ("esquerda", "direita"):
            if d == direcao:
                valor, ponta_carroca = novo_valor, item.peca.eh_carroca
            else:
                ramo = self.ramos[d]
                valor = self.extremidades[d]
                ponta_carroca = ramo[-1].peca.eh_carroca if ramo else self.primeira_peca.peca.eh_carroca
            soma += valor * (2 if ponta_carroca else 1)
        for d in ("cima", "baixo"):
            if d == direcao:
                soma += novo_valor * (2 if item.peca.eh_carroca else 1)
            else:
                ramo = self.ramos[d]
                if ramo:
                    soma += self.extremidades[d] * (2 if ramo[-1].peca.eh_carroca else 1)
        return soma if soma % 5 == 0 else 0

    # ------------------------------------------------------------ Ações
    def _prever_insercao(self, peca, direcao):
        """Retorna (PecaNaMesa, novo_valor_da_extremidade) pra jogar `peca`
        no ramo `direcao`, sem mutar o estado - só chamado quando a mesa já
        tem pelo menos a peça de abertura (mesa vazia é tratado à parte)."""
        casado = self.extremidades[direcao]
        fora = peca.outro_lado(casado)
        return PecaNaMesa(peca, casado, fora), fora

    def jogar(self, jogador, peca, direcao):
        """Aplica a jogada se for legal. Retorna True se aplicou."""
        if peca not in jogador.mao:
            return False

        if self.mesa_vazia():
            if self.peca_obrigatoria is not None:
                if peca != self.peca_obrigatoria:
                    return False
            elif not peca.eh_carroca and any(p.eh_carroca for p in jogador.mao):
                return False  # tem que abrir com carroça se tiver alguma na mão
            trancou = False  # nunca tranca na primeira jogada da mão
            self.primeira_peca = PecaNaMesa(peca, peca.a, peca.b)
            self.eh_spinner = peca.eh_carroca
            self.extremidades["esquerda"] = peca.a
            self.extremidades["direita"] = peca.b
            if self.eh_spinner:
                self.extremidades["cima"] = peca.a
                self.extremidades["baixo"] = peca.a
        else:
            if direcao not in DIRECOES or self.extremidades[direcao] is None or not peca.combina(self.extremidades[direcao]):
                return False
            if direcao in ("cima", "baixo") and not self.bucho_liberado():
                return False
            trancou = (self.ultimo_a_jogar_id == jogador.id
                       and self.passes_consecutivos == len(self._ordem) - 1)
            item, novo_valor = self._prever_insercao(peca, direcao)
            self.ramos[direcao].append(item)
            self.extremidades[direcao] = novo_valor

        self.peca_obrigatoria = None
        jogador.mao.remove(peca)

        pontos_pontas = self.pontos_pontas()
        self.pontuou_pontas = pontos_pontas if (pontos_pontas > 0 and pontos_pontas % 5 == 0) else None
        if self.pontuou_pontas:
            jogador.pontuacao += self.pontuou_pontas

        self.trancou_parcial = trancou
        if trancou:
            jogador.pontuacao += BONUS_TRANCAR_PARCIAL

        self.bonus_passe_para = None
        self.passes_consecutivos = 0
        self.ultimo_a_jogar_id = jogador.id

        if not jogador.mao:
            self.resultado_mao = self._liquidar_bateu(jogador, peca)
        else:
            self._avancar_turno()
        return True

    def passar(self, jogador):
        self.pontuou_pontas = None
        self.trancou_parcial = False

        idx_anterior = (self.indice_da_vez - 1) % len(self._ordem)
        anterior = self._ordem[idx_anterior]
        anterior.pontuacao += BONUS_PASSE
        self.bonus_passe_para = anterior.nome

        self.passes_consecutivos += 1
        if self.passes_consecutivos >= len(self._ordem):
            self.resultado_mao = self._liquidar_bloqueio_total()
        else:
            self._avancar_turno()

    def _avancar_turno(self):
        self.indice_da_vez = (self.indice_da_vez + 1) % len(self._ordem)

    # ------------------------------------------------------------ Liquidação
    def _liquidar_bateu(self, vencedor, ultima_peca):
        soma = sum(j.pontos_na_mao() for j in self.jogadores if j is not vencedor)
        pontos_ganhos = (soma // 5) * 5
        carroca_bonus = ultima_peca.eh_carroca
        if carroca_bonus:
            pontos_ganhos += BONUS_CARROCA_FECHOU
        vencedor.pontuacao += pontos_ganhos

        detalhes = [{"jogador": j.nome, "pontos": j.pontos_na_mao()}
                    for j in self.jogadores if j is not vencedor]

        self.ultimo_vencedor_id = vencedor.id
        self.forcar_abertura_6_6 = False
        return {"tipo": "bateu", "vencedor": vencedor.nome, "pontos_ganhos": pontos_ganhos,
                "carroca_bonus": carroca_bonus, "detalhes": detalhes}

    def _liquidar_bloqueio_total(self):
        """Ninguém, nem quem travou o jogo, consegue jogar mais: quem tem
        menos pontos na mão vence (empate divide os pontos). A próxima mão
        volta a abrir com quem tiver a 6/6."""
        menor = min(j.pontos_na_mao() for j in self.jogadores)
        vencedores = [j for j in self.jogadores if j.pontos_na_mao() == menor]

        soma_outros = sum(j.pontos_na_mao() for j in self.jogadores if j not in vencedores)
        pontos_totais = (soma_outros // 5) * 5
        divisao = pontos_totais // len(vencedores)
        resto = pontos_totais % len(vencedores)
        for i, v in enumerate(vencedores):
            v.pontuacao += divisao + (1 if i < resto else 0)

        detalhes = [{"jogador": j.nome, "pontos": j.pontos_na_mao()}
                    for j in self.jogadores if j not in vencedores]

        self.forcar_abertura_6_6 = True
        return {"tipo": "bloqueio_total", "vencedor": ", ".join(v.nome for v in vencedores),
                "pontos_ganhos": pontos_totais, "carroca_bonus": False, "detalhes": detalhes,
                "empate": len(vencedores) > 1}
