"""
domino_screen.py - Tela principal de gameplay do modo Dominó (corrida de
pontos até 250 - ver domino_logic.py e domino/README.md).

Não existe mais compra: cada jogador já recebe na mão todas as peças que vai
ter na mão inteira (sem monte, ver domino_logic.criar_pecas). O jogador tem
duas decisões possíveis: arrastar uma peça jogável da própria mão até a
ponta/ramo da mesa onde quer encaixá-la (largando-a numa das zonas
destacadas) ou, quando não há nenhuma jogada possível, clicar no botão
"Passar".

A mesa é montada em cruz: a peça de abertura fica no centro; se ela for
carroça (spinner/bucho), o jogo pode crescer nos 4 sentidos (esquerda,
direita, cima, baixo) a partir dela, não só esquerda/direita - ver
`_layout_mesa` e `domino_logic.DominoTable` (`ramos`/`extremidades`).
"""
import math
import queue
import random
from collections import deque

import pygame
from core.ui_theme import (
    BG, PANEL, INK, SOMBRA, FELT, FELT_DARK, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_avatar, desenhar_mesa,
    desenhar_badge, desenhar_glow_de_vez,
)
from .domino_theme import desenhar_peca, desenhar_peca_verso
from .domino_logic import (
    Peca, TIPO_HUMANO_REMOTO, BONUS_PASSE, DIRECOES,
    FASE_EMBARALHANDO, FASE_ESCOLHENDO, FASE_JOGANDO, DURACAO_EMBARALHAR,
)
from .domino_bot_ai import escolher_jogada_bot
from core.chat_widget import ChatWidget
from core import layout
from rede import protocolo

# Tamanhos de peça, espaçamentos e botões vêm de core/layout.py (chaves
# "domino.*" e "geral.*"), compartilhados com mesa_remota_domino_screen.py;
# o tempo de jogada dos bots também ("domino.delay_bot_ms").
# "domino.peca_mesa" é (comprimento, espessura) de uma peça normal deitada
# numa linha horizontal, no tamanho máximo - _layout_mesa() só reduz a partir
# dele pra caber no feltro.

# Geometria da mesa (a mesma em mesa_remota_domino_screen.py): o feltro fica
# centrado em 44% da altura (era 36%) e os assentos da metade de cima ficam a
# só FOLGA_ASSENTO_CIMA px dele (os de baixo seguem a FOLGA_ASSENTO_BAIXO) -
# antes o assento do topo, com 4 jogadores, saía pela borda superior da tela
# e disputava espaço com os selos "MÃO #n"/"Vez de".
CENTRO_MESA_Y = 0.44
FOLGA_ASSENTO_CIMA = 36
FOLGA_ASSENTO_BAIXO = 70
FOLGA_BOTAO_PASSAR = 24  # distância do "Passar" para a ponta da mão
MEIA_LARGURA_ASSENTO = 97  # metade do painel (178px) + folga: o centro de um assento nunca fica
                           # mais perto da borda da tela que isso (em 1024px os laterais saíam)

PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]


def _horizontal(direcao):
    return direcao in ("esquerda", "direita")


def posicionar_botao_passar(botao, rects_mao, largura, altura):
    """Põe o botão "Passar" à direita da mão, centrado nela; se não couber na
    tela, à esquerda. Sem mão (não deveria acontecer na vez do jogador), no
    rodapé. Usado também por mesa_remota_domino_screen.py."""
    if not rects_mao:
        botao.center = (largura // 2, altura - 46)
        return
    centro_y = rects_mao[0].centery
    botao.midleft = (rects_mao[-1].right + FOLGA_BOTAO_PASSAR, centro_y)
    if botao.right > largura - 16:
        botao.midright = (rects_mao[0].left - FOLGA_BOTAO_PASSAR, centro_y)


def _tamanho_peca(direcao, eh_carroca, escala=1.0):
    """(largura, altura) de renderização pra uma peça nesse ramo. Ramos
    horizontais (esquerda/direita) crescem deitados (peça normal em
    paisagem); ramos verticais (cima/baixo) crescem em pé (peça normal em
    retrato). Carroças sempre viram perpendicular ao crescimento do ramo
    ("carroça deitada")."""
    comprimento, espessura = layout.obter("domino.peca_mesa")
    retrato = eh_carroca if _horizontal(direcao) else not eh_carroca
    largura, altura = (espessura, comprimento) if retrato else (comprimento, espessura)
    return int(largura * escala), int(altura * escala)


class DominoTableScreen:
    def __init__(self, app, mesa, sala_rede=None):
        self.app = app
        self.mesa = mesa
        self.id_humano = mesa.jogadores[0].id
        self.sala_rede = sala_rede

        self.timer_bot = 0.0
        self.tempo_decorrido = 0.0

        self.peca_arrastando = None
        self.pos_arraste = (0, 0)
        self.zonas_drop_ativas = {}   # direcao -> rect, só as legais pra peca_arrastando
        self._zonas_mesa = {}         # direcao -> rect, calculado a cada desenhar() (todas as ativas)

        # Fase visual de início de mão (ver domino_logic.FASE_*) - puramente
        # cosmética/local: `pecas_para_escolher` é uma cópia embaralhada da
        # mão real (já conhecida por inteiro desde `iniciar_nova_mao`), e
        # cada clique tira uma peça dela até esvaziar, sem tocar na mão de
        # verdade (ver `_iniciar_fase_embaralhar`).
        self.fase_mao = FASE_JOGANDO
        self.timer_embaralhar = 0.0
        self.pecas_para_escolher = []
        self._qtd_embaralhando = 0

        self.botao_continuar = pygame.Rect(0, 0, 0, 0)
        self.botao_sair = pygame.Rect(0, 0, 0, 0)
        self.botao_passar = pygame.Rect(0, 0, 0, 0)
        self._dimensionar_botoes()

        self.historico = deque(maxlen=1)
        self.chat = ChatWidget(self._enviar_chat_host) if sala_rede is not None else None
        self._iniciar_mao()

    # ---------------------------------------------------------------- Histórico
    def _registrar(self, texto, cor=TEXT_MUTED):
        self.historico.append((texto, cor))

    def _iniciar_mao(self):
        self.mesa.iniciar_nova_mao()
        self.peca_arrastando = None
        self.zonas_drop_ativas = {}
        self.historico.clear()
        self._enviar_maos_privadas()
        self._broadcast_estado()
        self._iniciar_fase_embaralhar()

    def _iniciar_fase_embaralhar(self):
        self.timer_embaralhar = 0.0
        if self.app.settings.selecao_automatica_pecas:
            self.fase_mao = FASE_JOGANDO
            self.pecas_para_escolher = []
            return
        self.fase_mao = FASE_EMBARALHANDO
        self._qtd_embaralhando = sum(len(j.mao) for j in self.mesa.jogadores)
        humano = self._jogador(self.id_humano)
        self.pecas_para_escolher = list(humano.mao)
        random.shuffle(self.pecas_para_escolher)

    def _jogador(self, id_jogador):
        return next(j for j in self.mesa.jogadores if j.id == id_jogador)

    def _jogador_por_id(self, id_jogador):
        return next((j for j in self.mesa.jogadores if j.id == id_jogador), None)

    # ---------------------------------------------------------------- Rede (host)
    def _enviar_chat_host(self, texto):
        nome = self.sala_rede.nome_anfitriao
        self.chat.adicionar_mensagem(nome, texto)
        self.sala_rede.enviar_para_todos({"tipo": protocolo.CHAT, "remetente": nome, "texto": texto})

    def _enviar_maos_privadas(self):
        if self.sala_rede is None:
            return
        for jogador in self.mesa.jogadores:
            if jogador.tipo == TIPO_HUMANO_REMOTO:
                self.sala_rede.enviar_para(jogador.id, {
                    "tipo": protocolo.SUA_MAO,
                    "pecas": [[p.a, p.b] for p in jogador.mao],
                })

    def _broadcast_estado(self):
        if self.sala_rede is None:
            return
        self._enviar_maos_privadas()
        self.sala_rede.enviar_para_todos(self._serializar_estado())

    def _serializar_estado(self):
        jogador_da_vez = self.mesa.jogador_da_vez()
        jogadores = []
        for j in self.mesa.jogadores:
            jogadores.append({
                "id": j.id, "nome": j.nome, "pontuacao": j.pontuacao,
                "num_pecas": len(j.mao),
                "desconectado": bool(self.sala_rede and j.id in self.sala_rede.desconectados),
            })
        peca_obrig = self.mesa.peca_obrigatoria
        primeira = self.mesa.primeira_peca
        return {
            "tipo": protocolo.ESTADO,
            "mao_numero": self.mesa.mao_numero,
            "primeira_peca": [primeira.peca.a, primeira.peca.b] if primeira else None,
            "eh_spinner": self.mesa.eh_spinner,
            "ramos": {d: [[item.interno, item.externo] for item in self.mesa.ramos[d]] for d in DIRECOES},
            "extremidades": dict(self.mesa.extremidades),
            "peca_obrigatoria": [peca_obrig.a, peca_obrig.b] if peca_obrig else None,
            "jogador_da_vez_id": jogador_da_vez.id if jogador_da_vez else None,
            "jogadores": jogadores,
            "ultima_acao": self.historico[-1][0] if self.historico else None,
            "resultado": self.mesa.resultado_mao,
        }

    def _drenar_mensagens_rede(self):
        while True:
            try:
                jogador_id, msg = self.sala_rede.mensagens_entrantes.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == protocolo.ACAO_DOMINO:
                self._processar_acao_remota(jogador_id, msg)
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

    def _processar_acao_remota(self, jogador_id, msg):
        jogador_da_vez = self.mesa.jogador_da_vez()
        jogador = self._jogador_por_id(jogador_id)
        acao = msg.get("acao")

        if jogador is None or jogador_da_vez is None or jogador_da_vez.id != jogador_id:
            self.sala_rede.enviar_para(jogador_id, {
                "tipo": protocolo.ERRO_ACAO,
                "motivo": "Jogador desconhecido" if jogador is None else "Não é a sua vez",
            })
            return

        if acao == "passar":
            if self.mesa.pode_jogar(jogador):
                self.sala_rede.enviar_para(jogador_id, {
                    "tipo": protocolo.ERRO_ACAO, "motivo": "Você ainda tem jogada possível"})
                return
            self._passar(jogador)
            return

        if acao == "jogar":
            dados_peca = msg.get("peca")
            direcao = msg.get("lado")
            erro = None
            if not dados_peca or len(dados_peca) != 2 or direcao not in DIRECOES:
                erro = "Jogada inválida"
            else:
                peca = Peca(dados_peca[0], dados_peca[1])
                if not self.mesa.pode_jogar(jogador):
                    erro = "Você precisa passar"
                elif peca not in jogador.mao:
                    erro = "Você não tem essa peça"
                elif (peca, direcao) not in self.mesa.jogadas_possiveis(jogador):
                    erro = "Essa jogada não é válida agora"
            if erro:
                self.sala_rede.enviar_para(jogador_id, {"tipo": protocolo.ERRO_ACAO, "motivo": erro})
                return
            self._jogar(jogador, peca, direcao)
            return

        self.sala_rede.enviar_para(jogador_id, {"tipo": protocolo.ERRO_ACAO, "motivo": "Ação inválida"})

    # ---------------------------------------------------------------- Ações de mesa
    def _jogar(self, jogador, peca, direcao):
        ok = self.mesa.jogar(jogador, peca, direcao)
        if ok:
            partes = [f"{jogador.nome} jogou {peca}"]
            if self.mesa.pontuou_pontas:
                partes.append(f"marcou {self.mesa.pontuou_pontas} pontos")
            if self.mesa.trancou_parcial:
                partes.append("trancou o jogo e ganhou 50 pontos")
            self._registrar(" — ".join(partes), MINT)
        self._broadcast_estado()
        return ok

    def _passar(self, jogador):
        self.mesa.passar(jogador)
        msg = f"{jogador.nome} passou"
        if self.mesa.bonus_passe_para:
            msg += f" — {self.mesa.bonus_passe_para} ganha {BONUS_PASSE} pontos"
        self._registrar(msg, TEXT_MUTED)
        self._broadcast_estado()

    def _comecar_proxima_mao_ou_finalizar(self):
        vencedor = self.mesa.vencedor_do_jogo()
        if vencedor is not None:
            if self.sala_rede is not None:
                self.sala_rede.enviar_para_todos({"tipo": protocolo.FIM_DE_JOGO, "vencedor": vencedor.nome})
            self.app.finalizar_jogo(vencedor.nome)
        else:
            self._iniciar_mao()

    def _sair_para_menu(self):
        if self.sala_rede is not None:
            self.sala_rede.encerrar()
        self.app.ir_para_menu()

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        if self.chat is not None and self.chat.tratar_evento(evento):
            return

        if self.app.jogo_finalizado:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self._sair_para_menu()
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_sair.collidepoint(evento.pos):
                self._sair_para_menu()
                return

        if self.fase_mao == FASE_EMBARALHANDO:
            return

        if self.fase_mao == FASE_ESCOLHENDO:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._clicar_pilha_escolha(evento.pos)
            return

        if self.mesa.resultado_mao is not None:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.botao_continuar.collidepoint(evento.pos):
                    self._comecar_proxima_mao_ou_finalizar()
            return

        if evento.type == pygame.MOUSEMOTION:
            if self.peca_arrastando is not None:
                self.pos_arraste = evento.pos
            return

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.peca_arrastando is not None:
                self._soltar_peca(evento.pos)
            return

        if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
            return

        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        if not eh_vez_do_humano:
            return
        humano = self._jogador(self.id_humano)

        if not self.mesa.pode_jogar(humano):
            if self.botao_passar.collidepoint(evento.pos):
                self._passar(humano)
            return

        for rect, peca in self._rects_mao_humano(humano):
            if rect.collidepoint(evento.pos):
                self._comecar_arraste(humano, peca, evento.pos)
                return

    def _comecar_arraste(self, humano, peca, pos_mouse):
        direcoes = [d for p, d in self.mesa.jogadas_possiveis(humano) if p == peca]
        if not direcoes:
            return
        self.peca_arrastando = peca
        self.pos_arraste = pos_mouse
        self.zonas_drop_ativas = {d: r for d, r in self._zonas_mesa.items() if d in direcoes}

    def _soltar_peca(self, pos_mouse):
        peca = self.peca_arrastando
        direcao_escolhida = next((d for d, rect in self.zonas_drop_ativas.items()
                                   if rect.collidepoint(pos_mouse)), None)
        self.peca_arrastando = None
        self.zonas_drop_ativas = {}
        if direcao_escolhida is not None:
            self._jogar(self._jogador(self.id_humano), peca, direcao_escolhida)

    def _clicar_pilha_escolha(self, pos_mouse):
        for rect, peca in self._rects_pilha_escolha(self._mesa_rect()):
            if rect.collidepoint(pos_mouse):
                self.pecas_para_escolher.remove(peca)
                if not self.pecas_para_escolher:
                    self.fase_mao = FASE_JOGANDO
                return

    # ---------------------------------------------------------------- Update
    def atualizar(self, dt):
        self.tempo_decorrido += dt

        if self.sala_rede is not None:
            self._drenar_mensagens_rede()

        if self.fase_mao == FASE_EMBARALHANDO:
            self.timer_embaralhar += dt
            if self.timer_embaralhar >= DURACAO_EMBARALHAR:
                self.fase_mao = FASE_ESCOLHENDO
            return

        if self.fase_mao == FASE_ESCOLHENDO:
            return

        if self.app.jogo_finalizado or self.mesa.resultado_mao is not None:
            return

        jogador_da_vez = self.mesa.jogador_da_vez()
        if jogador_da_vez is None:
            return

        desconectado = (
            self.sala_rede is not None
            and jogador_da_vez.tipo == TIPO_HUMANO_REMOTO
            and jogador_da_vez.id in self.sala_rede.desconectados
        )

        if jogador_da_vez.is_bot or desconectado:
            self.timer_bot += dt
            if self.timer_bot < layout.obter("domino.delay_bot_ms") / 1000:
                return
            self.timer_bot = 0.0
            if not self.mesa.pode_jogar(jogador_da_vez):
                self._passar(jogador_da_vez)
                return
            resultado = escolher_jogada_bot(jogador_da_vez, self.mesa)
            if resultado is not None:
                peca, direcao = resultado
                self._jogar(jogador_da_vez, peca, direcao)
        else:
            self.timer_bot = 0.0

    # ---------------------------------------------------------------- Desenho
    def _mesa_rect(self):
        largura, altura = pygame.display.get_surface().get_size()
        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.5))
        mesa_rect.center = (largura // 2, int(altura * CENTRO_MESA_Y))
        return mesa_rect

    def _dimensionar_botoes(self):
        """Tamanhos dos botões vêm de core/layout.py. Reaplicado a cada
        desenhar() pra um layout alterado (editor visual, recarregar) valer
        sem recriar a tela - a posição é definida depois, no próprio desenho."""
        self.botao_continuar.size = layout.obter("geral.botao_continuar")
        self.botao_sair.size = layout.obter("geral.botao_sair")
        self.botao_passar.size = layout.obter("domino.botao_passar")

    def desenhar(self, tela):
        self._dimensionar_botoes()
        largura, altura = tela.get_size()
        tela.fill(BG)

        mesa_rect = self._mesa_rect()
        desenhar_mesa(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
        if self.fase_mao == FASE_EMBARALHANDO:
            self._desenhar_embaralhando(tela, mesa_rect)
        elif self.fase_mao == FASE_ESCOLHENDO:
            self._desenhar_escolhendo(tela, mesa_rect)
        else:
            self._desenhar_centro_mesa(tela, mesa_rect)
        self._desenhar_jogadores(tela, mesa_rect)
        self._desenhar_historico(tela, largura, altura)

        if self.chat is not None:
            self.chat.desenhar(tela, largura, altura)

        if self.app.jogo_finalizado:
            self._desenhar_tela_final(tela, largura, altura)
            return

        self._desenhar_botao_sair(tela)
        self._desenhar_bandeja_mao(tela, largura, altura)

        if self.fase_mao != FASE_JOGANDO:
            self._desenhar_dica_escolha(tela, largura, altura)
        elif self.mesa.resultado_mao is not None:
            self._desenhar_resultado(tela, largura, altura)
        else:
            self._desenhar_controles(tela, largura, altura)

    def _rects_pilha_escolha(self, mesa_rect):
        largura_peca, altura_peca = layout.obter("domino.peca_pilha_escolha")
        espaco = layout.obter("domino.espaco_pilha_escolha")
        pecas = self.pecas_para_escolher
        n = len(pecas)
        por_linha = min(7, max(1, n))
        linhas = math.ceil(n / por_linha) if n else 0
        total_largura = por_linha * largura_peca + (por_linha - 1) * espaco
        total_altura = linhas * altura_peca + max(0, linhas - 1) * espaco
        x0 = mesa_rect.centerx - total_largura // 2
        y0 = mesa_rect.centery - total_altura // 2
        pares = []
        for i, peca in enumerate(pecas):
            linha, col = divmod(i, por_linha)
            rect = pygame.Rect(x0 + col * (largura_peca + espaco), y0 + linha * (altura_peca + espaco),
                                largura_peca, altura_peca)
            pares.append((rect, peca))
        return pares

    def _desenhar_embaralhando(self, tela, mesa_rect):
        t = self.timer_embaralhar
        largura_peca, altura_peca = 30, 16
        raio_base = min(mesa_rect.width, mesa_rect.height) * 0.22
        for i in range(self._qtd_embaralhando):
            angulo_base = (i / max(1, self._qtd_embaralhando)) * 2 * math.pi
            raio = raio_base * (0.35 + 0.6 * ((i * 37) % 100) / 100)
            vibra = math.sin(t * 18 + i) * 6
            angulo = angulo_base + t * 3.0 + math.sin(t * 5 + i) * 0.3
            x = mesa_rect.centerx + math.cos(angulo) * (raio + vibra) - largura_peca / 2
            y = mesa_rect.centery + math.sin(angulo) * (raio + vibra) * 0.6 - altura_peca / 2
            desenhar_peca_verso(tela, x, y, largura_peca, altura_peca)
        desenhar_texto(tela, "Embaralhando...", mesa_rect.centerx, mesa_rect.centery,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_escolhendo(self, tela, mesa_rect):
        mouse_pos = pygame.mouse.get_pos()
        for rect, _peca in self._rects_pilha_escolha(mesa_rect):
            hover = rect.collidepoint(mouse_pos)
            desenhar_peca_verso(tela, rect.x, rect.y, rect.width, rect.height, destaque=hover)

    def _desenhar_dica_escolha(self, tela, largura, altura):
        if self.fase_mao == FASE_EMBARALHANDO:
            texto = "Embaralhando as peças..."
        else:
            faltam = len(self.pecas_para_escolher)
            texto = f"Escolha suas peças — faltam {faltam}"
        desenhar_texto(tela, texto, largura // 2, altura - 20,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_topo(self, tela, largura):
        desenhar_badge(tela, largura // 2, 30, f"MÃO #{self.mesa.mao_numero}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        humano = self._jogador(self.id_humano)
        desenhar_badge(tela, largura - 24, 30, f"VOCÊ: {humano.pontuacao} pts",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    # ---------------------------------------------------------------- Layout da mesa
    def _layout_mesa(self, mesa_rect):
        """Monta o layout físico da mesa em cruz (peça central + até 4
        ramos). Devolve (tiles, zonas): `tiles` é uma lista de (rect,
        valor_a, valor_b, vertical) pra desenhar cada peça já colocada;
        `zonas` é um dict direcao -> rect com a posição da próxima peça de
        cada ramo ativo agora (onde soltar/clicar pra jogar nessa
        direção)."""
        mesa = self.mesa
        largura_base, altura_base = layout.obter("domino.peca_mesa")
        espaco = layout.obter("domino.espaco_mesa")

        if mesa.mesa_vazia():
            zona = pygame.Rect(0, 0, largura_base + 24, altura_base + 24)
            zona.center = mesa_rect.center
            return [], {"esquerda": zona}

        def extensao(direcao, ramo, escala=1.0):
            if not ramo:
                return 0
            eixo = 0 if _horizontal(direcao) else 1
            total = sum(_tamanho_peca(direcao, item.peca.eh_carroca, escala)[eixo] for item in ramo)
            return total + espaco * (len(ramo) - 1)

        lc, ac = _tamanho_peca("esquerda", mesa.eh_spinner)
        ext_esq = extensao("esquerda", mesa.ramos["esquerda"])
        ext_dir = extensao("direita", mesa.ramos["direita"])
        ext_cima = extensao("cima", mesa.ramos["cima"]) if mesa.eh_spinner else 0
        ext_baixo = extensao("baixo", mesa.ramos["baixo"]) if mesa.eh_spinner else 0

        largura_padrao = ext_esq + lc + ext_dir + espaco * 2
        altura_padrao = ext_cima + ac + ext_baixo + espaco * 2
        disp_largura = mesa_rect.width - 40
        disp_altura = mesa_rect.height - 30
        # Sem piso alto aqui de propósito: caber dentro do feltro importa mais
        # que o tamanho mínimo da peça (um piso como 0.35 deixava a fileira
        # "vazar" pra fora da mesa quando tinha peça demais numa linha só).
        escala = max(0.12, min(1.0, disp_largura / max(1, largura_padrao), disp_altura / max(1, altura_padrao)))

        lc, ac = _tamanho_peca("esquerda", mesa.eh_spinner, escala)
        centro_rect = pygame.Rect(0, 0, lc, ac)
        centro_rect.center = (0, 0)  # espaço local, provisório - recentralizado no fim (ver abaixo)

        tiles = [(centro_rect, mesa.primeira_peca.interno, mesa.primeira_peca.externo, mesa.eh_spinner)]
        zonas = {}

        def montar_ramo(direcao, ramo, cursor_inicial):
            cursor = cursor_inicial
            for item in ramo:
                largura, altura = _tamanho_peca(direcao, item.peca.eh_carroca, escala)
                rect = pygame.Rect(0, 0, largura, altura)
                if direcao == "direita":
                    rect.left = cursor
                    rect.centery = centro_rect.centery
                    cursor = rect.right + int(espaco * escala)
                elif direcao == "esquerda":
                    rect.right = cursor
                    rect.centery = centro_rect.centery
                    cursor = rect.left - int(espaco * escala)
                elif direcao == "baixo":
                    rect.top = cursor
                    rect.centerx = centro_rect.centerx
                    cursor = rect.bottom + int(espaco * escala)
                else:  # cima
                    rect.bottom = cursor
                    rect.centerx = centro_rect.centerx
                    cursor = rect.top - int(espaco * escala)

                if direcao in ("direita", "baixo"):
                    valor_a, valor_b = item.interno, item.externo
                else:
                    valor_a, valor_b = item.externo, item.interno
                retrato = item.peca.eh_carroca if _horizontal(direcao) else not item.peca.eh_carroca
                tiles.append((rect, valor_a, valor_b, retrato))

            largura_zona, altura_zona = _tamanho_peca(direcao, False, escala)
            zona = pygame.Rect(0, 0, largura_zona, altura_zona)
            if direcao == "direita":
                zona.left, zona.centery = cursor, centro_rect.centery
            elif direcao == "esquerda":
                zona.right, zona.centery = cursor, centro_rect.centery
            elif direcao == "baixo":
                zona.top, zona.centerx = cursor, centro_rect.centerx
            else:
                zona.bottom, zona.centerx = cursor, centro_rect.centerx
            zonas[direcao] = zona

        montar_ramo("direita", mesa.ramos["direita"], centro_rect.right + int(espaco * escala))
        montar_ramo("esquerda", mesa.ramos["esquerda"], centro_rect.left - int(espaco * escala))
        if mesa.eh_spinner:
            montar_ramo("baixo", mesa.ramos["baixo"], centro_rect.bottom + int(espaco * escala))
            montar_ramo("cima", mesa.ramos["cima"], centro_rect.top - int(espaco * escala))

        # A peça central foi montada num espaço local (0,0) porque os ramos
        # normalmente não crescem simétrico (mais peça de um lado que do
        # outro) - centralizar sempre a peça central em mesa_rect.center
        # deixava o lado mais comprido vazar pra fora do feltro. Em vez
        # disso, centraliza a CAIXA QUE ENGLOBA TUDO (peças + zonas de
        # soltar) em mesa_rect - como o total já cabe (ver escala acima),
        # isso garante que nada fica de fora.
        limites = centro_rect.copy()
        for rect, _a, _b, _v in tiles:
            limites.union_ip(rect)
        for rect in zonas.values():
            limites.union_ip(rect)
        deslocamento = (mesa_rect.centerx - limites.centerx, mesa_rect.centery - limites.centery)
        for rect, _a, _b, _v in tiles:
            rect.move_ip(deslocamento)
        for rect in zonas.values():
            rect.move_ip(deslocamento)

        return tiles, zonas

    def _desenhar_centro_mesa(self, tela, mesa_rect):
        tiles, zonas = self._layout_mesa(mesa_rect)
        self._zonas_mesa = zonas

        if self.mesa.mesa_vazia():
            if self.mesa.peca_obrigatoria is not None:
                texto = f"Mesa vazia — jogue a peça {self.mesa.peca_obrigatoria}"
            else:
                texto = "Mesa vazia — abra com uma carroça"
            desenhar_texto(tela, texto, mesa_rect.centerx, mesa_rect.centery,
                            tamanho=13, cor=TEXT_MUTED, centralizado=True)
        else:
            for rect, valor_a, valor_b, vertical in tiles:
                desenhar_peca(tela, rect.x, rect.y, rect.width, rect.height, valor_a, valor_b, vertical=vertical)

        if self.peca_arrastando is not None:
            for direcao, rect in self.zonas_drop_ativas.items():
                pygame.draw.rect(tela, YELLOW, rect, border_radius=0)
                pygame.draw.rect(tela, INK, rect, width=2, border_radius=0)
                valor = self.mesa.extremidades.get(direcao)
                if valor is not None:
                    desenhar_texto(tela, str(valor), rect.centerx, rect.centery,
                                    tamanho=14, cor=INK, negrito=True, centralizado=True)

    def _iniciais(self, nome):
        partes = nome.replace('"', "").split()
        if len(partes) >= 2:
            return (partes[0][0] + partes[1][0]).upper()
        return nome[:2].upper()

    def _status_jogador(self, jogador, eh_vez_dele):
        if (self.sala_rede is not None and jogador.tipo == TIPO_HUMANO_REMOTO
                and jogador.id in self.sala_rede.desconectados):
            return "Desconectado", LOCKED, TEXT_MUTED
        if jogador.id == self.id_humano:
            return None, None, None
        if eh_vez_dele:
            return "Pensando...", BLUE, INK
        return f"{len(jogador.mao)} peças", MINT, SOMBRA

    def _desenhar_jogadores(self, tela, mesa_rect):
        n = len(self.mesa.jogadores)
        posicoes = self._posicoes_assentos(mesa_rect, n)
        jogador_da_vez = self.mesa.jogador_da_vez() if not self.app.jogo_finalizado else None

        for indice, (x, y) in enumerate(posicoes):
            jogador = self.mesa.jogadores[indice]
            eh_humano = jogador.id == self.id_humano
            eh_vez_dele = jogador_da_vez is not None and jogador.id == jogador_da_vez.id

            painel = pygame.Rect(0, 0, 178, 62)
            painel.centerx = x
            painel.centery = y

            if eh_vez_dele:
                desenhar_glow_de_vez(tela, x, y, 46, 64, self.tempo_decorrido)

            desenhar_painel(tela, painel, cor=PANEL, radius=0, deslocamento_sombra=(3, 3))

            cor_avatar = YELLOW if eh_humano else PALETA_AVATAR[jogador.id % len(PALETA_AVATAR)]
            desenhar_avatar(tela, painel.x + 34, painel.centery, 22, cor_avatar, self._iniciais(jogador.nome))

            desenhar_texto(tela, jogador.nome, painel.x + 62, painel.y + 12, tamanho=13, cor=INK, negrito=True)
            desenhar_texto(tela, f"{jogador.pontuacao} pts", painel.x + 62, painel.y + 30, tamanho=12,
                            cor=TEXT_MUTED, familia="mono")

            status_texto, status_cor, status_cor_texto = self._status_jogador(jogador, eh_vez_dele)
            if status_texto:
                desenhar_badge(tela, painel.x + 62, painel.y + 48, status_texto, status_cor,
                                cor_texto=status_cor_texto, tamanho_fonte=9, ancorar="midleft")

    def _posicoes_assentos(self, mesa_rect, n_jogadores):
        if n_jogadores == 3:
            angulos = [90, 210, 330]
        else:
            angulos = [90, 180, 270, 0]

        posicoes = []
        for i in range(n_jogadores):
            ang = math.radians(angulos[i])
            rx = mesa_rect.width // 2 + 70
            ry = mesa_rect.height // 2 + (FOLGA_ASSENTO_CIMA if math.sin(ang) < 0 else FOLGA_ASSENTO_BAIXO)
            x = mesa_rect.centerx + int(rx * math.cos(ang))
            y = mesa_rect.centery + int(ry * math.sin(ang))
            largura_tela = mesa_rect.centerx * 2  # a mesa é centrada na janela
            x = max(MEIA_LARGURA_ASSENTO, min(largura_tela - MEIA_LARGURA_ASSENTO, x))
            posicoes.append((x, y))
        return posicoes

    # ---------------------------------------------------------------- Bandeja da mão
    def _rects_mao(self, pecas):
        largura_peca, altura_peca = layout.obter("domino.peca_mao")
        espaco = layout.obter("domino.espaco_mao")
        n = len(pecas)
        total_largura = n * largura_peca + max(0, n - 1) * espaco
        largura_tela, altura_tela = pygame.display.get_surface().get_size()
        x0 = largura_tela // 2 - total_largura // 2
        y0 = altura_tela - altura_peca - 40
        pares = []
        for i, peca in enumerate(pecas):
            rect = pygame.Rect(x0 + i * (largura_peca + espaco), y0, largura_peca, altura_peca)
            pares.append((rect, peca))
        return pares

    def _rects_mao_humano(self, humano):
        return self._rects_mao(humano.mao)

    def _desenhar_bandeja_mao(self, tela, largura, altura):
        humano = self._jogador(self.id_humano)

        if self.fase_mao != FASE_JOGANDO:
            reveladas = [p for p in humano.mao if p not in self.pecas_para_escolher]
            for rect, peca in self._rects_mao(reveladas):
                desenhar_peca(tela, rect.x, rect.y, rect.width, rect.height, peca.a, peca.b, vertical=True)
            return

        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        jogaveis = {p for p, _direcao in self.mesa.jogadas_possiveis(humano)} if eh_vez_do_humano else set()

        for rect, peca in self._rects_mao_humano(humano):
            if peca == self.peca_arrastando:
                continue
            destaque = eh_vez_do_humano and peca in jogaveis
            desenhar_peca(tela, rect.x, rect.y, rect.width, rect.height, peca.a, peca.b,
                          vertical=True, destaque=destaque)

        if self.peca_arrastando is not None:
            largura_peca, altura_peca = layout.obter("domino.peca_mao")
            x = self.pos_arraste[0] - largura_peca // 2
            y = self.pos_arraste[1] - altura_peca // 2
            desenhar_peca(tela, x, y, largura_peca, altura_peca,
                          self.peca_arrastando.a, self.peca_arrastando.b, vertical=True, destaque=True)

    def _desenhar_historico(self, tela, largura, altura):
        if not self.historico:
            return
        texto, cor = self.historico[-1]
        desenhar_badge(tela, largura - 24, 64, texto[:44], PANEL, cor_texto=INK,
                        tamanho_fonte=11, ancorar="topright", borda=cor)

    def _desenhar_controles(self, tela, largura, altura):
        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        if not eh_vez_do_humano:
            nome_vez = jogador_da_vez.nome if jogador_da_vez else "-"
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)
            return

        humano = self._jogador(self.id_humano)
        if not self.mesa.pode_jogar(humano):
            # Ao lado da mão (que fica sem peça jogável): embaixo dela não cabe -
            # a mão termina em altura - 40 e ficava por cima do botão e da dica.
            desenhar_texto(tela, "Você não tem peça pra jogar — clique em Passar",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            posicionar_botao_passar(self.botao_passar, [r for r, _ in self._rects_mao_humano(humano)],
                                     largura, altura)
            mouse_pos = pygame.mouse.get_pos()
            desenhar_botao(tela, self.botao_passar, "Passar",
                            hover=self.botao_passar.collidepoint(mouse_pos), tamanho_fonte=16, cor=CORAL)
        elif self.peca_arrastando is not None:
            desenhar_texto(tela, "Arraste até uma ponta destacada e solte pra jogar",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)
        else:
            desenhar_texto(tela, "Sua vez — arraste uma peça em destaque até a mesa",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_resultado(self, tela, largura, altura):
        resultado = self.mesa.resultado_mao
        n_linhas = 1 + len(resultado["detalhes"])
        painel = pygame.Rect(0, 0, 480, 110 + 26 * n_linhas)
        painel.center = (largura // 2, altura - 200)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        desenhar_texto(tela, "RESULTADO DA MÃO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")

        if resultado["tipo"] == "bloqueio_total":
            prefixo = "Jogo travou! " + ("Empate entre " if resultado.get("empate") else "")
            texto_vitoria = (f"{prefixo}{resultado['vencedor']} venceu com menos pontos "
                              f"na mão (+{resultado['pontos_ganhos']} pts)")
        else:
            extra = " (com bônus de carroça!)" if resultado.get("carroca_bonus") else ""
            texto_vitoria = f"{resultado['vencedor']} bateu e ganhou {resultado['pontos_ganhos']} pontos{extra}!"
        desenhar_texto(tela, texto_vitoria, painel.centerx, painel.y + 52,
                        tamanho=14, cor=INK, centralizado=True, negrito=True)

        y = painel.y + 82
        for d in resultado["detalhes"]:
            desenhar_texto(tela, f"{d['jogador']} ficou com {d['pontos']} pontos em peças na mão",
                            painel.centerx, y, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            y += 26

        self.botao_continuar.center = (painel.centerx, painel.bottom - 30)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_continuar, "Continuar",
                        hover=self.botao_continuar.collidepoint(mouse_pos), tamanho_fonte=18)

    def _desenhar_tela_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((*INK[:3], 150))
        tela.blit(overlay, (0, 0))

        painel = pygame.Rect(0, 0, 440, 220)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        desenhar_texto(tela, "FIM DE JOGO", painel.centerx, painel.y + 46,
                        tamanho=32, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, f"Vencedor: {self.app.nome_vencedor}", painel.centerx, painel.y + 100,
                        tamanho=19, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=12)
