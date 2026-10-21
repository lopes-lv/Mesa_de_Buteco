"""
mesa_remota_screen.py - Tela do jogador "cliente" no multiplayer local
(ver MULTIPLAYER_PLANO.md, seção 7).

Não roda nenhuma `Table` de verdade: só guarda o último snapshot de `estado`
recebido do host e a própria mão recebida por `sua_mao`. Quando é a vez do
jogador local (segundo o snapshot), os botões de ação mandam `acao` pro host
em vez de aplicar localmente.
"""
import math
import queue

import pygame
from core.deck import Card
from core.ui_theme import (
    BG, PANEL, INK, SOMBRA, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_carta, desenhar_carta_vazia,
    desenhar_mesa, desenhar_pilha_fichas, desenhar_avatar, desenhar_badge,
    desenhar_kbd, desenhar_glow_de_vez, desenhar_cropie, desenhar_mesa_oval_recorte,
)
from core.chat_widget import ChatWidget
from core import layout
from rede import protocolo

# Tamanhos de carta, espaçamentos e botões: mesmas chaves "holdem.*"/"geral.*"
# de core/layout.py que table_screen.py usa.

ANIM_CROUPIER_DURACAO = 0.9

PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]

HIST_MAX_LINHAS = 7
HIST_LARGURA = 300
HIST_MARGEM = 24

# Metade do painel de um bot (178px) + o selo SB/BB que passa da borda direita
# dele + folga: o centro de um assento nunca fica mais perto da borda da tela
# que isso (em janelas estreitas os assentos laterais saíam da tela).
MEIA_LARGURA_ASSENTO = 112
# Vão entre o painel de um bot e as cartas dele, embaixo. Era 14: com 8
# jogadores em 768px de altura os 4 assentos da esquerda (painel + vão +
# cartas = 136px cada) não cabiam empilhados sem um invadir o outro.
VAO_PAINEL_CARTAS_BOT = 10


def _desenhar_selo_aposta(tela, texto, x, y_cartas, largura_total, eh_voce, centro_mesa_x):
    """Selo com a aposta da rodada, ao lado das cartas: o seu à direita delas
    (o painel "Você" fica à esquerda), o dos bots virado pro centro da mesa.
    Ficava embaixo das cartas - o seu, atrás dos botões Fold/Call/Raise; o dos
    bots, com 7-8 jogadores ou em janelas baixas, sobre o painel do vizinho,
    o painel "Você" ou o histórico (o painel do bot já diz "Apostou N")."""
    if eh_voce or x <= centro_mesa_x:
        desenhar_badge(tela, x + largura_total // 2 + 8, y_cartas, texto, PANEL, cor_texto=INK,
                       tamanho_fonte=11, familia="mono", borda=INK, ancorar="midleft")
    else:
        desenhar_badge(tela, x - largura_total // 2 - 8, y_cartas, texto, PANEL, cor_texto=INK,
                       tamanho_fonte=11, familia="mono", borda=INK, ancorar="midright")


def _limite_direito_controles(largura):
    """Até onde (x) os controles do rodapé (Fold/Call/Raise e o painel do
    raise) podem ir sem encostar no histórico, fixo no canto inferior direito."""
    return largura - HIST_MARGEM - HIST_LARGURA - 20


def _posicoes_assentos(mesa_rect, n_jogadores):
    """Mesmos ângulos fixos de table_screen.py, para o layout visual ficar
    igual do ponto de vista de qualquer jogador conectado."""
    if n_jogadores == 2:
        angulos = [90, 180]
    elif n_jogadores == 3:
        angulos = [90, 180, 0]
    elif n_jogadores == 4:
        angulos = [90, 180, 225, 0]
    elif n_jogadores == 5:
        angulos = [90, 150, 210, 330, 30]
    elif n_jogadores == 6:
        angulos = [90, 135, 180, 225, 315, 0]
    elif n_jogadores == 7:
        angulos = [90, 135, 180, 225, 315, 0, 35]
    else:
        angulos = [90, 130, 165, 194, 228, 312, 348, 20]

    posicoes = []
    for i in range(n_jogadores):
        ang = math.radians(angulos[i])
        rx = mesa_rect.width // 2 + 45
        ry = mesa_rect.height // 2 + 70
        x = mesa_rect.centerx + int(rx * math.cos(ang))
        y = mesa_rect.centery + int(ry * math.sin(ang))
        largura_tela = mesa_rect.centerx * 2  # a mesa é centrada na janela
        x = max(MEIA_LARGURA_ASSENTO, min(largura_tela - MEIA_LARGURA_ASSENTO, x))
        posicoes.append((x, y))
    return posicoes


def _iniciais(nome):
    partes = nome.replace('"', "").split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    return nome[:2].upper()


class MesaRemotaScreen:
    def __init__(self, app, sala_cliente):
        self.app = app
        self.sala = sala_cliente
        self.meu_id = sala_cliente.meu_id

        self.estado = None
        self.minha_mao = []
        self.maos_espectador = {}  # id (str) -> cartas de todos, só quando fold/eliminado
        self.tempo_decorrido = 0.0
        self.anim_cropie_inicio = None
        self._mao_numero_visto = None
        self._estagio_visto = None

        self.erro_acao = None
        self.tempo_erro_acao = 0.0

        self.mensagem_final = None  # sala encerrada / conexão perdida
        self.vencedor_final = None

        self.chat = ChatWidget(self._enviar_chat)

        self.modo_raise = False
        self.valor_raise_atual = 0
        self.arrastando_slider = False

        self.botao_fold = pygame.Rect(0, 0, 0, 0)
        self.botao_call = pygame.Rect(0, 0, 0, 0)
        self.botao_raise = pygame.Rect(0, 0, 0, 0)
        self.botao_confirmar_raise = pygame.Rect(0, 0, 0, 0)
        self.botao_cancelar_raise = pygame.Rect(0, 0, 0, 0)
        self.slider_rect = pygame.Rect(0, 0, 320, 14)
        self.slider_alca = pygame.Rect(0, 0, 22, 32)
        self.botao_sair = pygame.Rect(0, 0, 0, 0)
        self._dimensionar_botoes()

    # ---------------------------------------------------------------- Estado
    def _meu_jogador(self):
        if self.estado is None:
            return None
        for j in self.estado["jogadores"]:
            if j["id"] == self.meu_id:
                return j
        return None

    def _eh_minha_vez(self):
        return self.estado is not None and self.estado.get("jogador_da_vez_id") == self.meu_id

    def _enviar_acao(self, acao, valor):
        self.sala.enviar({"tipo": protocolo.ACAO, "acao": acao, "valor": valor})

    def _enviar_chat(self, texto):
        self.sala.enviar({"tipo": protocolo.CHAT, "texto": texto})

    def _sair(self):
        self.sala.fechar()
        self.app.ir_para_menu()

    # ---------------------------------------------------------------- Update
    def atualizar(self, dt):
        self.tempo_decorrido += dt
        if self.tempo_erro_acao > 0:
            self.tempo_erro_acao -= dt
            if self.tempo_erro_acao <= 0:
                self.erro_acao = None

        while True:
            try:
                msg = self.sala.mensagens_entrantes.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == protocolo.ESTADO:
                self.estado = msg
                if msg.get("mao_numero") != self._mao_numero_visto:
                    self.maos_espectador = {}
                estagio = (msg.get("mao_numero"), len(msg.get("comunitarias", [])))
                if estagio != self._estagio_visto:
                    self._estagio_visto = estagio
                    self.anim_cropie_inicio = self.tempo_decorrido
                self._mao_numero_visto = msg.get("mao_numero")
                if not self._eh_minha_vez():
                    self.modo_raise = False
            elif tipo == protocolo.MAOS_ESPECTADOR:
                self.maos_espectador = msg.get("maos", {})
            elif tipo == protocolo.SUA_MAO:
                self.minha_mao = msg.get("cartas", [])
            elif tipo == protocolo.ERRO_ACAO:
                self.erro_acao = msg.get("motivo")
                self.tempo_erro_acao = 3.0
            elif tipo == protocolo.FIM_DE_JOGO:
                self.vencedor_final = msg.get("vencedor")
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

        if self.vencedor_final is None and self.sala.status in ("sala_encerrada", "desconectado"):
            self.mensagem_final = self.sala.erro or "Conexão com o anfitrião perdida."

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        if self.chat.tratar_evento(evento):
            return

        if self.vencedor_final is not None or self.mensagem_final is not None:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self._sair()
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_sair.collidepoint(evento.pos):
                self._sair()
                return

        if self.estado is None or self.estado.get("resultado") is not None:
            return

        meu = self._meu_jogador()
        if meu is None:
            return
        eh_minha_vez = self._eh_minha_vez()
        a_pagar = max(0, self.estado.get("aposta_alvo", 0) - meu["aposta_rodada"])

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if not eh_minha_vez:
                return
            if self.modo_raise:
                if self.slider_alca.collidepoint(evento.pos):
                    self.arrastando_slider = True
                elif self.botao_confirmar_raise.collidepoint(evento.pos):
                    self._enviar_acao("raise", self.valor_raise_atual)
                    self.modo_raise = False
                elif self.botao_cancelar_raise.collidepoint(evento.pos):
                    self.modo_raise = False
                return

            if self.botao_fold.collidepoint(evento.pos):
                self._enviar_acao("fold", 0)
            elif self.botao_call.collidepoint(evento.pos):
                self._enviar_acao("check" if a_pagar <= 0 else "call", 0)
            elif self.botao_raise.collidepoint(evento.pos):
                self._entrar_modo_raise(meu, a_pagar)

        elif evento.type == pygame.MOUSEBUTTONUP:
            self.arrastando_slider = False

        elif evento.type == pygame.MOUSEMOTION and self.arrastando_slider:
            self._atualizar_valor_slider(evento.pos[0], meu, a_pagar)

        elif evento.type == pygame.KEYDOWN:
            if not eh_minha_vez:
                return
            if self.modo_raise:
                if evento.key == pygame.K_RETURN:
                    self._enviar_acao("raise", self.valor_raise_atual)
                    self.modo_raise = False
                return
            if evento.key == pygame.K_f:
                self._enviar_acao("fold", 0)
            elif evento.key == pygame.K_c:
                self._enviar_acao("check" if a_pagar <= 0 else "call", 0)
            elif evento.key == pygame.K_r:
                self._entrar_modo_raise(meu, a_pagar)

    def _entrar_modo_raise(self, meu, a_pagar):
        bb = self.estado["blinds"][1]
        min_raise = max(bb, self.estado.get("ultimo_raise_valor", bb))
        maximo = max(1, meu["stack"] - a_pagar)
        self.valor_raise_atual = min(min_raise, maximo)
        self.modo_raise = True

    def _atualizar_valor_slider(self, mouse_x, meu, a_pagar):
        maximo = max(1, meu["stack"] - a_pagar)
        bb = self.estado["blinds"][1]
        min_raise = min(max(bb, self.estado.get("ultimo_raise_valor", bb)), maximo)

        proporcao = (mouse_x - self.slider_rect.x) / max(1, self.slider_rect.width)
        proporcao = min(1.0, max(0.0, proporcao))
        valor_bruto = int(maximo * proporcao)
        self.valor_raise_atual = max(min_raise, valor_bruto)

    # ---------------------------------------------------------------- Desenho
    def _dimensionar_botoes(self):
        """Tamanhos dos botões vêm de core/layout.py. Reaplicado a cada
        desenhar() pra um layout alterado (editor visual, recarregar) valer
        sem recriar a tela - a posição é definida depois, no próprio desenho."""
        self.botao_fold.size = self.botao_call.size = self.botao_raise.size = layout.obter("holdem.botao_acao")
        self.botao_confirmar_raise.size = layout.obter("holdem.botao_confirmar_raise")
        self.botao_cancelar_raise.size = layout.obter("holdem.botao_cancelar_raise")
        self.botao_sair.size = layout.obter("geral.botao_sair")

    def desenhar(self, tela):
        self._dimensionar_botoes()
        largura, altura = tela.get_size()
        tela.fill(BG)

        if self.vencedor_final is not None:
            self._desenhar_tela_final(tela, largura, altura)
            return

        if self.estado is None:
            desenhar_texto(tela, "Conectando à mesa...", largura // 2, altura // 2,
                            tamanho=20, cor=INK, centralizado=True, negrito=True)
            return

        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.55))
        mesa_rect.center = (largura // 2, int(altura * 0.42))
        recorte = desenhar_mesa_oval_recorte(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
        self._desenhar_comunitarias(tela, mesa_rect)
        self._desenhar_pote(tela, mesa_rect)
        self._desenhar_croupie(tela, recorte)
        self._desenhar_jogadores(tela, mesa_rect, largura, altura)
        self._desenhar_historico(tela, largura, altura)
        self._desenhar_botao_sair(tela)
        self.chat.desenhar(tela, largura, altura)

        if self.mensagem_final is not None:
            self._desenhar_mensagem_final(tela, largura, altura)
            return

        resultado = self.estado.get("resultado")
        if resultado is not None:
            self._desenhar_resultado(tela, largura, altura, resultado)
        else:
            self._desenhar_controles(tela, largura, altura)

        if self.erro_acao:
            desenhar_badge(tela, largura // 2, altura - 140, self.erro_acao, CORAL,
                            cor_texto=INK, tamanho_fonte=12, borda=INK)

    def _desenhar_topo(self, tela, largura):
        sb, bb = self.estado["blinds"]
        desenhar_badge(tela, largura // 2, 30, f"MÃO #{self.estado['mao_numero']}   BLINDS {sb}/{bb}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        meu = self._meu_jogador()
        stack = meu["stack"] if meu else 0
        desenhar_badge(tela, largura - 24, 30, f"VOCÊ: {stack}",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    def _desenhar_comunitarias(self, tela, mesa_rect):
        cartas = [Card(valor, naipe) for valor, naipe in self.estado["comunitarias"]]
        n = len(cartas)
        largura_carta, altura_carta = layout.obter("holdem.carta_comunitaria")
        espaco = layout.obter("holdem.espaco_comunitarias")
        total_largura = 5 * largura_carta + 4 * espaco
        x0 = mesa_rect.centerx - total_largura // 2
        y0 = mesa_rect.centery - altura_carta // 2 - 22
        for i in range(5):
            x = x0 + i * (largura_carta + espaco)
            if i < n:
                desenhar_carta(tela, x, y0, largura_carta, altura_carta, cartas[i])
            else:
                desenhar_carta_vazia(tela, x, y0, largura_carta, altura_carta)

    def _desenhar_croupie(self, tela, recorte):
        progresso = 0.0
        if self.anim_cropie_inicio is not None:
            decorrido = self.tempo_decorrido - self.anim_cropie_inicio
            if decorrido < ANIM_CROUPIER_DURACAO:
                progresso = decorrido / ANIM_CROUPIER_DURACAO
            else:
                self.anim_cropie_inicio = None
        desenhar_cropie(tela, recorte.centerx, recorte.top + 22, progresso)

    def _sou_espectador(self):
        meu = self._meu_jogador()
        return meu is not None and (meu["eliminado"] or meu["foldou"])

    def _desenhar_pote(self, tela, mesa_rect):
        desenhar_badge(tela, mesa_rect.centerx, mesa_rect.centery + 56, f"POTE: {self.estado['pote']}",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=16, familia="mono", borda=INK)

    def _status_jogador(self, jogador, eh_vez_dele):
        if jogador["eliminado"]:
            return "Eliminado", LOCKED, TEXT_MUTED
        if jogador.get("desconectado"):
            return "Desconectado", LOCKED, TEXT_MUTED
        if jogador["foldou"]:
            return "Fold", LOCKED, TEXT_MUTED
        if jogador["all_in"]:
            return "All-in", PURPLE, INK
        if eh_vez_dele:
            return "Pensando...", BLUE, INK
        if jogador["aposta_rodada"] > 0:
            return f"Apostou {jogador['aposta_rodada']}", MINT, SOMBRA
        return None, None, None

    def _desenhar_jogadores(self, tela, mesa_rect, largura, altura):
        jogadores = self.estado["jogadores"]
        n = len(jogadores)
        posicoes = _posicoes_assentos(mesa_rect, n)
        jogador_da_vez_id = self.estado.get("jogador_da_vez_id")
        espectador = self._sou_espectador()

        for indice, (x, y) in enumerate(posicoes):
            jogador = jogadores[indice]
            eh_eu = jogador["id"] == self.meu_id
            largura_carta, altura_carta = layout.obter(
                "holdem.carta_jogador" if eh_eu else "holdem.carta_oponente")
            eh_vez_dele = jogador_da_vez_id == jogador["id"]

            y_cartas = y - layout.obter("holdem.deslocamento_cartas_jogador") if eh_eu else y

            if eh_vez_dele:
                desenhar_glow_de_vez(tela, x, y_cartas, largura_carta, altura_carta, self.tempo_decorrido)

            espaco_cartas = layout.obter(
                "holdem.espaco_cartas_jogador" if eh_eu else "holdem.espaco_cartas_oponente")
            total_largura = 2 * largura_carta + espaco_cartas

            if eh_eu:
                self._desenhar_painel_proprio(tela, jogador, x, y, total_largura)
            else:
                self._desenhar_painel_outro(tela, jogador, x, y, altura_carta, eh_vez_dele)

            if jogador["eliminado"]:
                continue

            x0 = x - total_largura // 2
            cartas_espectador = self.maos_espectador.get(str(jogador["id"])) if espectador else None
            if cartas_espectador:
                for i, (valor, naipe) in enumerate(cartas_espectador):
                    desenhar_carta(tela, x0 + i * (largura_carta + espaco_cartas), y_cartas - altura_carta // 2,
                                    largura_carta, altura_carta, carta=Card(valor, naipe))
            elif eh_eu:
                cartas = [Card(valor, naipe) for valor, naipe in self.minha_mao]
                for i in range(2):
                    carta = cartas[i] if i < len(cartas) else None
                    desenhar_carta(tela, x0 + i * (largura_carta + espaco_cartas), y_cartas - altura_carta // 2,
                                    largura_carta, altura_carta, carta=carta, virada_para_baixo=carta is None)
            elif not jogador["foldou"]:
                for i in range(2):
                    desenhar_carta(tela, x0 + i * (largura_carta + espaco_cartas), y_cartas - altura_carta // 2,
                                    largura_carta, altura_carta, carta=None, virada_para_baixo=True)

            if jogador["aposta_rodada"] > 0:
                _desenhar_selo_aposta(tela, str(jogador["aposta_rodada"]), x, y_cartas, largura_total=total_largura,
                                      eh_voce=eh_eu, centro_mesa_x=mesa_rect.centerx)

    def _desenhar_painel_outro(self, tela, jogador, x, y, altura_carta, eh_vez_dele):
        cor_avatar = PALETA_AVATAR[jogador["id"] % len(PALETA_AVATAR)]
        painel_w, painel_h = 178, 62
        painel = pygame.Rect(0, 0, painel_w, painel_h)
        painel.centerx = x
        painel.bottom = y - altura_carta // 2 - VAO_PAINEL_CARTAS_BOT

        fundo = LOCKED if (jogador["foldou"] or jogador["eliminado"]) else PANEL
        desenhar_painel(tela, painel, cor=fundo, radius=0, deslocamento_sombra=(3, 3))

        desenhar_avatar(tela, painel.x + 34, painel.centery, 22, cor_avatar, _iniciais(jogador["nome"]))

        cor_nome = TEXT_MUTED if (jogador["foldou"] or jogador["eliminado"]) else INK
        desenhar_texto(tela, jogador["nome"], painel.x + 62, painel.y + 12, tamanho=13,
                        cor=cor_nome, negrito=True)
        desenhar_texto(tela, str(jogador["stack"]), painel.x + 62, painel.y + 30, tamanho=12,
                        cor=TEXT_MUTED, familia="mono")

        status_texto, status_cor, status_cor_texto = self._status_jogador(jogador, eh_vez_dele)
        if status_texto:
            desenhar_badge(tela, painel.x + 62, painel.y + 48, status_texto, status_cor,
                            cor_texto=status_cor_texto, tamanho_fonte=9, ancorar="midleft")

    def _desenhar_painel_proprio(self, tela, jogador, x, y, total_largura):
        painel_w, painel_h = 176, 68
        painel = pygame.Rect(0, 0, painel_w, painel_h)
        painel.right = x - total_largura // 2 - 26
        painel.centery = y

        desenhar_painel(tela, painel, cor=PANEL, radius=0, deslocamento_sombra=(3, 3))
        desenhar_texto(tela, jogador["nome"], painel.centerx, painel.y + 18, tamanho=15,
                        cor=INK, negrito=True, centralizado=True)
        desenhar_pilha_fichas(tela, painel.centerx - 30, painel.y + 46, jogador["stack"], raio=8)

        if jogador["foldou"]:
            desenhar_badge(tela, painel.centerx, painel.bottom - 12, "Fold", LOCKED,
                            cor_texto=TEXT_MUTED, tamanho_fonte=9)
        elif jogador["all_in"]:
            desenhar_badge(tela, painel.centerx, painel.bottom - 12, "All-in", PURPLE,
                            cor_texto=INK, tamanho_fonte=9)

    def _desenhar_historico(self, tela, largura, altura):
        altura_linha = 26
        altura_painel = 44 + HIST_MAX_LINHAS * altura_linha
        painel = pygame.Rect(0, 0, HIST_LARGURA, altura_painel)
        painel.bottomright = (largura - HIST_MARGEM, altura - HIST_MARGEM)
        desenhar_painel(tela, painel, cor=PANEL, radius=0, deslocamento_sombra=(5, 5))

        desenhar_texto(tela, "HISTÓRICO DA RODADA", painel.x + 18, painel.y + 14,
                        tamanho=12, cor=INK, negrito=True)
        pygame.draw.line(tela, INK, (painel.x + 16, painel.y + 34),
                          (painel.right - 16, painel.y + 34), 2)

        y = painel.y + 42
        for texto in self.estado.get("historico", [])[-HIST_MAX_LINHAS:]:
            pygame.draw.rect(tela, TEXT_MUTED, (painel.x + 16, y + 4, 4, altura_linha - 10), border_radius=0)
            desenhar_texto(tela, texto[:34], painel.x + 26, y + int(altura_linha * 0.5),
                            tamanho=12, cor=INK)
            y += altura_linha

    def _desenhar_resultado(self, tela, largura, altura, resultados):
        painel = pygame.Rect(0, 0, 480, 130 + 30 * len(resultados))
        painel.center = (largura // 2, altura - 160)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)
        desenhar_texto(tela, "RESULTADO DA MÃO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")
        for i, r in enumerate(resultados):
            texto = f"{', '.join(r['vencedores'])} venceu {r['pote']} ({r['categoria']})"
            desenhar_texto(tela, texto, painel.centerx, painel.y + 52 + i * 26,
                            tamanho=14, cor=TEXT_MUTED, centralizado=True)
        desenhar_texto(tela, "Aguardando o anfitrião avançar para a próxima mão...",
                        painel.centerx, painel.bottom - 20, tamanho=11, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_mensagem_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((*INK[:3], 150))
        tela.blit(overlay, (0, 0))

        painel = pygame.Rect(0, 0, 440, 200)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)
        desenhar_texto(tela, "Sala encerrada", painel.centerx, painel.y + 50,
                        tamanho=26, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, self.mensagem_final, painel.centerx, painel.y + 100,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=12)

    def _desenhar_tela_final(self, tela, largura, altura):
        painel = pygame.Rect(0, 0, 440, 220)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        desenhar_texto(tela, "FIM DE JOGO", painel.centerx, painel.y + 46,
                        tamanho=32, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, f"Vencedor: {self.vencedor_final}", painel.centerx, painel.y + 100,
                        tamanho=19, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=12)

    def _desenhar_controles(self, tela, largura, altura):
        meu = self._meu_jogador()
        if meu is None:
            return
        eh_minha_vez = self._eh_minha_vez()
        a_pagar = max(0, self.estado.get("aposta_alvo", 0) - meu["aposta_rodada"])

        if self._sou_espectador():
            motivo = "Sem fichas" if meu["eliminado"] else "Você deu fold"
            desenhar_badge(tela, largura // 2, altura - 90, f"ESPECTADOR — {motivo}: vendo as cartas de todos",
                            YELLOW, cor_texto=SOMBRA, tamanho_fonte=14, borda=INK)
            vez_id = self.estado.get("jogador_da_vez_id")
            nome_vez = next((j["nome"] for j in self.estado["jogadores"] if j["id"] == vez_id), "-")
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)
            return

        base_y = altura - 90
        espaco = layout.obter("holdem.espaco_botoes")
        largura_total = self.botao_fold.width + self.botao_call.width + self.botao_raise.width + 2 * espaco
        self.botao_fold.midleft = (largura // 2 - largura_total // 2, base_y)
        self.botao_call.midleft = (self.botao_fold.right + espaco, base_y)
        self.botao_raise.midleft = (self.botao_call.right + espaco, base_y)
        # Janela estreita: a fileira anda pra esquerda pra não invadir o histórico.
        excesso = self.botao_raise.right - _limite_direito_controles(largura)
        if excesso > 0:
            deslocamento = min(excesso, self.botao_fold.x - 20)
            for botao in (self.botao_fold, self.botao_call, self.botao_raise):
                botao.x -= deslocamento

        ativo = eh_minha_vez and not self.modo_raise
        mouse_pos = pygame.mouse.get_pos()
        texto_call = "Check" if a_pagar <= 0 else f"Call {a_pagar}"
        mostrar_atalhos = self.app.settings.mostrar_atalhos

        desenhar_botao(tela, self.botao_fold, "Fold", hover=ativo and self.botao_fold.collidepoint(mouse_pos),
                        ativo=ativo, cor=CORAL, cor_texto=INK)
        if mostrar_atalhos:
            desenhar_kbd(tela, self.botao_fold.right - 12, self.botao_fold.bottom - 12, "F", ancorar="bottomright")

        desenhar_botao(tela, self.botao_call, texto_call, hover=ativo and self.botao_call.collidepoint(mouse_pos),
                        ativo=ativo, cor=BLUE, cor_texto=INK)
        if mostrar_atalhos:
            desenhar_kbd(tela, self.botao_call.right - 12, self.botao_call.bottom - 12, "C", ancorar="bottomright")

        pode_raise = ativo and meu["stack"] > a_pagar
        desenhar_botao(tela, self.botao_raise, "Raise", hover=pode_raise and self.botao_raise.collidepoint(mouse_pos),
                        ativo=pode_raise, cor=MINT, cor_texto=SOMBRA)
        if mostrar_atalhos:
            desenhar_kbd(tela, self.botao_raise.right - 12, self.botao_raise.bottom - 12, "R", ancorar="bottomright")

        if not eh_minha_vez:
            vez_id = self.estado.get("jogador_da_vez_id")
            nome_vez = next((j["nome"] for j in self.estado["jogadores"] if j["id"] == vez_id), "-")
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)

        if self.modo_raise:
            self._desenhar_slider_raise(tela, largura, altura, meu, a_pagar)

    def _desenhar_slider_raise(self, tela, largura, altura, meu, a_pagar):
        painel = pygame.Rect(0, 0, 420, 140)
        painel.center = (largura // 2, altura - 180)
        painel.right = min(painel.right, _limite_direito_controles(largura))  # idem botões
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        maximo = max(1, meu["stack"] - a_pagar)
        self.valor_raise_atual = min(self.valor_raise_atual, maximo)

        desenhar_texto(tela, f"Valor do Raise: {self.valor_raise_atual}", painel.centerx, painel.y + 24,
                        tamanho=16, cor=INK, centralizado=True, negrito=True, familia="mono")

        self.slider_rect.midleft = (painel.x + 30, painel.y + 62)
        self.slider_rect.width = painel.width - 60
        pygame.draw.rect(tela, LOCKED, self.slider_rect, border_radius=0)
        pygame.draw.rect(tela, INK, self.slider_rect, 2, border_radius=0)

        proporcao = self.valor_raise_atual / maximo if maximo > 0 else 0
        alca_x = self.slider_rect.x + int(proporcao * self.slider_rect.width)
        self.slider_alca.center = (alca_x, self.slider_rect.centery)
        pygame.draw.rect(tela, INK, self.slider_alca.move(2, 2), border_radius=0)
        pygame.draw.rect(tela, MINT, self.slider_alca, border_radius=0)
        pygame.draw.rect(tela, INK, self.slider_alca, 2, border_radius=0)

        desenhar_texto(tela, "1", self.slider_rect.x, self.slider_rect.y + 22, tamanho=12, cor=TEXT_MUTED, familia="mono")
        desenhar_texto(tela, f"{maximo} (all-in)", self.slider_rect.right, self.slider_rect.y + 22,
                        tamanho=12, cor=TEXT_MUTED, familia="mono")

        self.botao_confirmar_raise.midleft = (painel.x + 20, painel.bottom - 28)
        self.botao_cancelar_raise.midright = (painel.right - 20, painel.bottom - 28)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_confirmar_raise, "Confirmar",
                        hover=self.botao_confirmar_raise.collidepoint(mouse_pos), tamanho_fonte=15, cor=MINT)
        desenhar_botao(tela, self.botao_cancelar_raise, "Cancelar",
                        hover=self.botao_cancelar_raise.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)
