"""
pifpaf_screen.py - Tela principal de gameplay do modo Pif Paf.

Responsavel por:
 - Desenhar mesa, monte, descarte, vira/coringa e os assentos dos jogadores
 - Mao do jogador humano numa bandeja inferior: arrastar uma carta reordena
   a mao (para organizar trincas/sequencias visualmente) e um clique simples
   seleciona a carta para descarte
 - Botoes: Comprar do Monte, Comprar do Descarte, Bater, Descartar
 - Orquestrar o turno dos bots automaticamente (com pequeno delay)
 - Mostrar o resultado de cada mao (pontos pagos por quem nao bateu) e o fim de jogo
"""
import math
import queue
from collections import deque

import pygame
from core.deck import Card
from core.ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_carta,
    desenhar_mesa, desenhar_avatar, desenhar_badge, desenhar_kbd,
    desenhar_glow_de_vez,
)
from .pifpaf_bot_ai import decidir_fonte_compra_bot, escolher_descarte_bot
from .pifpaf_logic import TIPO_HUMANO_REMOTO
from core.chat_widget import ChatWidget
from rede import protocolo

DELAY_BOT_SEGUNDOS = 0.9
LIMIAR_ARRASTO_PX = 6

CARTA_BOT_TAMANHO = (46, 64)
CARTA_MAO_TAMANHO = (66, 92)
CARTA_MONTE_TAMANHO = (60, 84)

PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]

HIST_MARGEM = 24

NAIPE_UNICODE = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}


def _carta_str(carta):
    return f"{carta.texto}{NAIPE_UNICODE.get(carta.simbolo_naipe, carta.simbolo_naipe)}"


def _posicoes_assentos(mesa_rect, n_jogadores):
    """Assentos visuais fixos ao redor da mesa (mesma geometria usada na
    mesa de Texas Hold'em, ver table_screen.py)."""
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
        angulos = [90, 135, 180, 225, 315, 0, 45]
    else:
        angulos = [90, 125, 160, 195, 230, 310, 350, 30]

    posicoes = []
    for i in range(n_jogadores):
        ang = math.radians(angulos[i])
        rx = mesa_rect.width // 2 + 70
        ry = mesa_rect.height // 2 + 70
        x = mesa_rect.centerx + int(rx * math.cos(ang))
        y = mesa_rect.centery + int(ry * math.sin(ang))
        posicoes.append((x, y))
    return posicoes


class PifPafTableScreen:
    def __init__(self, app, mesa, sala_rede=None):
        self.app = app
        self.mesa = mesa
        self.id_humano = mesa.jogadores[0].id
        self.sala_rede = sala_rede  # AnfitriaoSala, só quando é uma mesa multiplayer (host)

        self.carta_selecionada = None
        self.arraste = None  # {"indice", "inicio", "pos", "moveu"} enquanto arrasta uma carta da mao
        self.timer_bot = 0.0
        self.tempo_decorrido = 0.0

        # Largura maior que o texto pedia (180px estourava "Comprar Descarte"
        # por baixo do selo de atalho no canto inferior direito do botao).
        self.botao_monte = pygame.Rect(0, 0, 230, 56)
        self.botao_descarte = pygame.Rect(0, 0, 230, 56)
        self.botao_mao_fechada = pygame.Rect(0, 0, 190, 56)
        self.botao_bater = pygame.Rect(0, 0, 150, 56)
        self.botao_descartar = pygame.Rect(0, 0, 150, 56)
        self.botao_continuar = pygame.Rect(0, 0, 240, 56)
        self.botao_sair = pygame.Rect(0, 0, 110, 44)

        self.monte_rect = pygame.Rect(0, 0, *CARTA_MONTE_TAMANHO)
        self.descarte_rect = pygame.Rect(0, 0, *CARTA_MONTE_TAMANHO)

        self.historico = deque(maxlen=1)
        self.chat = ChatWidget(self._enviar_chat_host) if sala_rede is not None else None
        self._iniciar_mao()

    # ---------------------------------------------------------------- Historico
    def _registrar(self, texto, cor=TEXT_MUTED):
        self.historico.append((texto, cor))

    def _iniciar_mao(self):
        self.mesa.iniciar_nova_mao()
        self.carta_selecionada = None
        self.arraste = None
        self.historico.clear()
        self._enviar_maos_privadas()
        self._broadcast_estado()

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
            if jogador.tipo == TIPO_HUMANO_REMOTO and not jogador.eliminado:
                self.sala_rede.enviar_para(jogador.id, {
                    "tipo": protocolo.SUA_MAO,
                    "cartas": [[carta.valor, carta.naipe] for carta in jogador.mao],
                })

    def _broadcast_estado(self):
        if self.sala_rede is None:
            return
        self._enviar_maos_privadas()
        self.sala_rede.enviar_para_todos(self._serializar_estado())

    def _serializar_resultado(self, resultado):
        if resultado is None:
            return None
        return {
            "vencedor": resultado.get("vencedor"),
            "pote": resultado.get("pote"),
            "empate": resultado.get("empate", False),
            "mao_fechada": resultado.get("mao_fechada", False),
            "detalhes": [{"jogador": d["jogador"], "pontos": d["pontos"]}
                         for d in resultado.get("detalhes", [])],
        }

    def _serializar_estado(self):
        jogador_da_vez = self.mesa.jogador_da_vez()
        jogadores = []
        for j in self.mesa.jogadores:
            jogadores.append({
                "id": j.id, "nome": j.nome, "stack": j.stack, "eliminado": j.eliminado,
                "num_cartas": len(j.mao),
                "ja_agiu_nesta_mao": j.id in self.mesa.jogadores_ja_agiram_na_mao,
                "desconectado": bool(self.sala_rede and j.id in self.sala_rede.desconectados),
            })

        return {
            "tipo": protocolo.ESTADO,
            "mao_numero": self.mesa.mao_numero,
            "vira": [self.mesa.vira.valor, self.mesa.vira.naipe] if self.mesa.vira else None,
            "coringa_valor": self.mesa.coringa_valor,
            "usar_joker": self.mesa.usar_joker,
            "monte_restante": len(self.mesa.monte),
            "descarte_topo": [self.mesa.descarte[-1].valor, self.mesa.descarte[-1].naipe] if self.mesa.descarte else None,
            "comprou_nesta_vez": self.mesa.comprou_nesta_vez,
            "jogador_da_vez_id": jogador_da_vez.id if jogador_da_vez else None,
            "jogadores": jogadores,
            "ultima_acao": self.historico[-1][0] if self.historico else None,
            "resultado": self._serializar_resultado(self.mesa.resultado_mao),
        }

    def _drenar_mensagens_rede(self):
        while True:
            try:
                jogador_id, msg = self.sala_rede.mensagens_entrantes.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == protocolo.ACAO_PIFPAF:
                self._processar_acao_remota(jogador_id, msg)
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

    def _processar_acao_remota(self, jogador_id, msg):
        jogador_da_vez = self.mesa.jogador_da_vez()
        jogador = self._jogador_por_id(jogador_id)
        acao = msg.get("acao")
        carta = None

        erro = None
        if jogador is None:
            erro = "Jogador desconhecido"
        elif jogador_da_vez is None or jogador_da_vez.id != jogador_id:
            erro = "Não é a sua vez"
        elif acao == "bater_mao_fechada":
            if not self.mesa.pode_bater_mao_fechada(jogador):
                erro = "Mão fechada não disponível"
        elif acao in ("comprar_monte", "comprar_descarte"):
            if not self.mesa.pode_comprar():
                erro = "Você já comprou nesta rodada"
        elif acao == "bater":
            if not self.mesa.pode_bater(jogador):
                erro = "Não é possível bater agora"
        elif acao == "descartar":
            dados_carta = msg.get("carta")
            if not dados_carta or len(dados_carta) != 2:
                erro = "Carta inválida"
            else:
                carta = Card(dados_carta[0], dados_carta[1])
                if self.mesa.pode_comprar():
                    erro = "Precisa comprar antes de descartar"
                elif carta not in jogador.mao:
                    erro = "Você não tem essa carta"
        else:
            erro = "Ação inválida"

        if erro:
            self.sala_rede.enviar_para(jogador_id, {"tipo": protocolo.ERRO_ACAO, "motivo": erro})
            return

        if acao == "bater_mao_fechada":
            self._bater_mao_fechada(jogador)
        elif acao == "comprar_monte":
            self._comprar(jogador, "monte")
        elif acao == "comprar_descarte":
            self._comprar(jogador, "descarte")
        elif acao == "bater":
            self._bater(jogador)
        elif acao == "descartar":
            self._descartar(jogador, carta)

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

        if self.mesa.resultado_mao is not None:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.botao_continuar.collidepoint(evento.pos):
                    self._comecar_proxima_mao_ou_finalizar()
            return

        humano = self._jogador(self.id_humano)

        # Arrastar/organizar as cartas da propria mao (reordenar para montar
        # trincas/sequencias visualmente) e a selecao por clique simples sao
        # liberadas a qualquer momento, mesmo fora do seu turno - so mudam a
        # ordem/selecao visual, nao a partida.
        if not humano.eliminado and self._tratar_evento_mao(evento, humano):
            return

        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        if not eh_vez_do_humano:
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._tratar_clique_humano(evento.pos, humano)
        elif evento.type == pygame.KEYDOWN:
            self._tratar_tecla_humana(evento.key, humano)

    def _tratar_evento_mao(self, evento, humano):
        """Trata clique/arrasto sobre as cartas da mao do jogador humano.
        Retorna True se o evento foi consumido (era sobre uma carta)."""
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, (rect, carta) in enumerate(self._rects_mao_humano(humano)):
                if rect.collidepoint(evento.pos):
                    self.arraste = {"indice": i, "inicio": evento.pos, "pos": evento.pos, "moveu": False}
                    return True
            return False

        if evento.type == pygame.MOUSEMOTION and self.arraste is not None:
            self.arraste["pos"] = evento.pos
            dx = evento.pos[0] - self.arraste["inicio"][0]
            dy = evento.pos[1] - self.arraste["inicio"][1]
            if abs(dx) > LIMIAR_ARRASTO_PX or abs(dy) > LIMIAR_ARRASTO_PX:
                self.arraste["moveu"] = True
            return True

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.arraste is not None:
            indice_origem = self.arraste["indice"]
            if self.arraste["moveu"]:
                self._reordenar_mao(humano, indice_origem, evento.pos[0])
            else:
                carta = humano.mao[indice_origem]
                self.carta_selecionada = None if self.carta_selecionada == carta else carta
            self.arraste = None
            return True

        return False

    def _reordenar_mao(self, humano, indice_origem, mouse_x):
        carta = humano.mao.pop(indice_origem)
        rects_restantes = self._rects_mao_humano(humano)
        novo_indice = len(rects_restantes)
        for i, (rect, _) in enumerate(rects_restantes):
            if mouse_x < rect.centerx:
                novo_indice = i
                break
        humano.mao.insert(novo_indice, carta)

    def _tratar_clique_humano(self, pos, humano):
        if self.mesa.pode_comprar():
            if self.mesa.pode_bater_mao_fechada(humano) and self.botao_mao_fechada.collidepoint(pos):
                self._bater_mao_fechada(humano)
                return
            if self.monte_rect.collidepoint(pos) or self.botao_monte.collidepoint(pos):
                self._comprar(humano, "monte")
            elif self.descarte_rect.collidepoint(pos) or self.botao_descarte.collidepoint(pos):
                self._comprar(humano, "descarte")
            return

        if self.botao_bater.collidepoint(pos) and self.mesa.pode_bater(humano):
            self._bater(humano)
            return

        if self.botao_descartar.collidepoint(pos) and self.carta_selecionada is not None:
            self._descartar(humano, self.carta_selecionada)
            return

    def _tratar_tecla_humana(self, tecla, humano):
        if self.mesa.pode_comprar():
            if tecla == pygame.K_b and self.mesa.pode_bater_mao_fechada(humano):
                self._bater_mao_fechada(humano)
            elif tecla == pygame.K_m:
                self._comprar(humano, "monte")
            elif tecla == pygame.K_d:
                self._comprar(humano, "descarte")
            return

        if tecla == pygame.K_b and self.mesa.pode_bater(humano):
            self._bater(humano)
        elif tecla == pygame.K_RETURN and self.carta_selecionada is not None:
            self._descartar(humano, self.carta_selecionada)

    def _comprar(self, jogador, fonte):
        if fonte == "monte":
            carta = self.mesa.comprar_do_monte(jogador)
            self._registrar(f"{jogador.nome} comprou do monte", TEXT_MUTED)
        else:
            carta = self.mesa.comprar_do_descarte(jogador)
            if carta is not None:
                self._registrar(f"{jogador.nome} comprou {_carta_str(carta)} do descarte", BLUE)
        self._broadcast_estado()

    def _bater(self, jogador):
        resultado = self.mesa.bater(jogador)
        if resultado is not None:
            self._registrar(f"{jogador.nome} bateu! +{resultado['pote']} fichas", MINT)
            self.mesa.marcar_eliminados()
        self._broadcast_estado()

    def _bater_mao_fechada(self, jogador):
        resultado = self.mesa.bater_mao_fechada(jogador)
        if resultado is not None:
            self._registrar(f"{jogador.nome} bateu de mão fechada! +{resultado['pote']} fichas (dobrado)", YELLOW)
            self.mesa.marcar_eliminados()
        self._broadcast_estado()

    def _descartar(self, jogador, carta):
        # Se descartar essa carta especifica fecha o resto da mao (jeito mais
        # comum de bater), o descarte vira a propria batida - ver
        # `pode_bater_descartando`/`bater_descartando` em pifpaf_logic.py.
        if self.mesa.pode_bater_descartando(jogador, carta):
            resultado = self.mesa.bater_descartando(jogador, carta)
            if resultado is not None:
                self._registrar(f"{jogador.nome} bateu descartando {_carta_str(carta)}! +{resultado['pote']} fichas", MINT)
                self.mesa.marcar_eliminados()
                self.carta_selecionada = None
                self._broadcast_estado()
                return

        self.mesa.descartar(jogador, carta)
        self._registrar(f"{jogador.nome} descartou {_carta_str(carta)}", CORAL)
        self.carta_selecionada = None
        self._broadcast_estado()

    def _comecar_proxima_mao_ou_finalizar(self):
        if self.mesa.jogo_tem_vencedor():
            vencedor = self.mesa.jogadores_na_mesa()[0]
            if self.sala_rede is not None:
                self.sala_rede.enviar_para_todos({"tipo": protocolo.FIM_DE_JOGO, "vencedor": vencedor.nome})
            self.app.finalizar_jogo(vencedor.nome)
        else:
            self._iniciar_mao()

    def _sair_para_menu(self):
        if self.sala_rede is not None:
            self.sala_rede.encerrar()
        self.app.ir_para_menu()

    # ---------------------------------------------------------------- Update
    def atualizar(self, dt):
        self.tempo_decorrido += dt

        if self.sala_rede is not None:
            self._drenar_mensagens_rede()

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

        if not (jogador_da_vez.is_bot or desconectado):
            self.timer_bot = 0.0
            return

        self.timer_bot += dt
        if self.timer_bot < DELAY_BOT_SEGUNDOS:
            return
        self.timer_bot = 0.0

        if self.mesa.pode_bater_mao_fechada(jogador_da_vez):
            self._bater_mao_fechada(jogador_da_vez)
            return

        if self.mesa.pode_comprar():
            fonte = decidir_fonte_compra_bot(jogador_da_vez, self.mesa)
            self._comprar(jogador_da_vez, fonte)
            return

        if self.mesa.pode_bater(jogador_da_vez):
            self._bater(jogador_da_vez)
            return

        carta = escolher_descarte_bot(jogador_da_vez, self.mesa)
        self._descartar(jogador_da_vez, carta)

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)

        mesa_rect = pygame.Rect(0, 0, int(largura * 0.7), int(altura * 0.48))
        mesa_rect.center = (largura // 2, int(altura * 0.36))
        desenhar_mesa(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
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

        if self.mesa.resultado_mao is not None:
            self._desenhar_resultado(tela, largura, altura)
        else:
            self._desenhar_controles(tela, largura, altura)

    def _desenhar_topo(self, tela, largura):
        desenhar_badge(tela, largura // 2, 30, f"MAO #{self.mesa.mao_numero}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        humano = self._jogador(self.id_humano)
        desenhar_badge(tela, largura - 24, 30, f"VOCE: {humano.stack}",
                        YELLOW, cor_texto=INK, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    def _desenhar_centro_mesa(self, tela, mesa_rect):
        largura_carta, altura_carta = CARTA_MONTE_TAMANHO
        espaco = 40
        cx = mesa_rect.centerx
        cy = mesa_rect.centery

        self.monte_rect = pygame.Rect(0, 0, largura_carta, altura_carta)
        self.monte_rect.center = (cx - espaco - largura_carta // 2, cy)
        desenhar_carta(tela, self.monte_rect.x, self.monte_rect.y, largura_carta, altura_carta,
                        virada_para_baixo=True)
        desenhar_badge(tela, self.monte_rect.centerx, self.monte_rect.bottom + 18,
                        f"MONTE ({len(self.mesa.monte)})", PANEL, cor_texto=INK, tamanho_fonte=10, borda=INK)

        self.descarte_rect = pygame.Rect(0, 0, largura_carta, altura_carta)
        self.descarte_rect.center = (cx + espaco + largura_carta // 2, cy)
        if self.mesa.descarte:
            desenhar_carta(tela, self.descarte_rect.x, self.descarte_rect.y, largura_carta, altura_carta,
                            carta=self.mesa.descarte[-1])
        desenhar_badge(tela, self.descarte_rect.centerx, self.descarte_rect.bottom + 18,
                        "DESCARTE", PANEL, cor_texto=INK, tamanho_fonte=10, borda=INK)

        if self.mesa.vira is not None:
            if self.mesa.usar_joker:
                texto_vira = f"VIRA {_carta_str(self.mesa.vira)} (decorativa) — JOKERS SÃO CORINGA"
            else:
                texto_vira = f"VIRA {_carta_str(self.mesa.vira)}  →  CORINGA VALE {self.mesa.coringa_valor}"
            desenhar_badge(tela, cx, mesa_rect.top + 30, texto_vira,
                            YELLOW, cor_texto=INK, tamanho_fonte=11, familia="mono", borda=INK)

    def _iniciais(self, nome):
        partes = nome.replace('"', "").split()
        if len(partes) >= 2:
            return (partes[0][0] + partes[1][0]).upper()
        return nome[:2].upper()

    def _desenhar_jogadores(self, tela, mesa_rect):
        n = len(self.mesa.jogadores)
        posicoes = _posicoes_assentos(mesa_rect, n)
        jogador_da_vez = self.mesa.jogador_da_vez() if not self.app.jogo_finalizado else None

        for indice, (x, y) in enumerate(posicoes):
            jogador = self.mesa.jogadores[indice]
            eh_humano = jogador.id == self.id_humano
            eh_vez_dele = jogador_da_vez is not None and jogador.id == jogador_da_vez.id

            painel_w, painel_h = 178, 62
            painel = pygame.Rect(0, 0, painel_w, painel_h)
            painel.centerx = x
            painel.centery = y

            if eh_vez_dele:
                desenhar_glow_de_vez(tela, x, y, CARTA_BOT_TAMANHO[0], CARTA_BOT_TAMANHO[1], self.tempo_decorrido)

            fundo = LOCKED if jogador.eliminado else PANEL
            desenhar_painel(tela, painel, cor=fundo, radius=16, deslocamento_sombra=(3, 3))

            cor_avatar = YELLOW if eh_humano else PALETA_AVATAR[jogador.id % len(PALETA_AVATAR)]
            cx_avatar = painel.x + 34
            desenhar_avatar(tela, cx_avatar, painel.centery, 22, cor_avatar, self._iniciais(jogador.nome))

            cor_nome = TEXT_MUTED if jogador.eliminado else INK
            desenhar_texto(tela, jogador.nome, painel.x + 62, painel.y + 12, tamanho=13,
                            cor=cor_nome, negrito=True)
            desenhar_texto(tela, str(jogador.stack), painel.x + 62, painel.y + 30, tamanho=12,
                            cor=TEXT_MUTED, familia="mono")

            if jogador.eliminado:
                status = "Eliminado"
            elif (self.sala_rede is not None and jogador.tipo == TIPO_HUMANO_REMOTO
                    and jogador.id in self.sala_rede.desconectados):
                status = "Desconectado"
            elif eh_humano:
                status = None
            elif eh_vez_dele and self.mesa.comprou_nesta_vez:
                status = "Pensando..."
            elif eh_vez_dele:
                status = "Comprando..."
            else:
                status = f"{len(jogador.mao)} cartas"

            if status:
                desenhar_badge(tela, painel.x + 62, painel.y + 48, status, MINT if not jogador.eliminado else LOCKED,
                                cor_texto=INK, tamanho_fonte=9, ancorar="midleft")

    # ---------------------------------------------------------------- Bandeja da mao
    def _rects_mao_humano(self, humano):
        largura_carta, altura_carta = CARTA_MAO_TAMANHO
        espaco = 10
        n = len(humano.mao)
        total_largura = n * largura_carta + (n - 1) * espaco
        largura_tela, altura_tela = pygame.display.get_surface().get_size()
        x0 = largura_tela // 2 - total_largura // 2
        y0 = altura_tela - altura_carta - 120
        pares = []
        for i, carta in enumerate(humano.mao):
            rect = pygame.Rect(x0 + i * (largura_carta + espaco), y0, largura_carta, altura_carta)
            pares.append((rect, carta))
        return pares

    def _desenhar_bandeja_mao(self, tela, largura, altura):
        humano = self._jogador(self.id_humano)
        if humano.eliminado:
            return

        pares = self._rects_mao_humano(humano)
        indice_arrastando = self.arraste["indice"] if (self.arraste and self.arraste["moveu"]) else None

        for i, (rect, carta) in enumerate(pares):
            if i == indice_arrastando:
                continue
            destaque = carta == self.carta_selecionada
            y = rect.y - 14 if destaque else rect.y
            desenhar_carta(tela, rect.x, y, rect.width, rect.height, carta=carta, destaque=destaque)

        if indice_arrastando is not None:
            rect, carta = pares[indice_arrastando]
            mouse_x, mouse_y = self.arraste["pos"]
            desenhar_carta(tela, mouse_x - rect.width // 2, mouse_y - rect.height // 2,
                            rect.width, rect.height, carta=carta, destaque=True)

    # ---------------------------------------------------------------- Controles
    def _desenhar_controles(self, tela, largura, altura):
        jogador_da_vez = self.mesa.jogador_da_vez()
        humano = self._jogador(self.id_humano)
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        mouse_pos = pygame.mouse.get_pos()

        base_y = altura - 40

        if not eh_vez_do_humano:
            nome_vez = jogador_da_vez.nome if jogador_da_vez else "-"
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)
            return

        if self.mesa.pode_comprar():
            pode_mao_fechada = self.mesa.pode_bater_mao_fechada(humano)
            espaco = 20

            if pode_mao_fechada:
                largura_total = (self.botao_mao_fechada.width + self.botao_monte.width
                                  + self.botao_descarte.width + 2 * espaco)
                x0 = largura // 2 - largura_total // 2
                self.botao_mao_fechada.midleft = (x0, base_y)
                self.botao_monte.midleft = (self.botao_mao_fechada.right + espaco, base_y)
                self.botao_descarte.midleft = (self.botao_monte.right + espaco, base_y)

                desenhar_badge(tela, largura // 2, base_y - 48,
                                "MÃO FECHADA! Bata sem comprar e ganhe em dobro",
                                YELLOW, cor_texto=INK, tamanho_fonte=12, borda=INK)
                desenhar_botao(tela, self.botao_mao_fechada, "Bater (2x)",
                                hover=self.botao_mao_fechada.collidepoint(mouse_pos),
                                tamanho_fonte=16, cor=YELLOW)
                desenhar_kbd(tela, self.botao_mao_fechada.right - 14, self.botao_mao_fechada.bottom - 14,
                              "B", ancorar="bottomright")
            else:
                self.botao_monte.midleft = (largura // 2 - 240, base_y)
                self.botao_descarte.midleft = (largura // 2 + 10, base_y)

            desenhar_botao(tela, self.botao_monte, "Comprar Monte",
                            hover=self.botao_monte.collidepoint(mouse_pos), tamanho_fonte=16, cor=BLUE, cor_texto=PANEL)
            desenhar_kbd(tela, self.botao_monte.right - 14, self.botao_monte.bottom - 14, "M", ancorar="bottomright")

            desenhar_botao(tela, self.botao_descarte, "Comprar Descarte",
                            hover=self.botao_descarte.collidepoint(mouse_pos), tamanho_fonte=16, cor=MINT)
            desenhar_kbd(tela, self.botao_descarte.right - 14, self.botao_descarte.bottom - 14, "D", ancorar="bottomright")
            return

        pode_bater = self.mesa.pode_bater(humano)
        self.botao_bater.midleft = (largura // 2 - 165, base_y)
        desenhar_botao(tela, self.botao_bater, "Bater", ativo=pode_bater,
                        hover=pode_bater and self.botao_bater.collidepoint(mouse_pos),
                        tamanho_fonte=18, cor=YELLOW)
        desenhar_kbd(tela, self.botao_bater.right - 12, self.botao_bater.bottom - 12, "B", ancorar="bottomright")

        pode_descartar = self.carta_selecionada is not None
        descarte_fecha_mao = pode_descartar and self.mesa.pode_bater_descartando(humano, self.carta_selecionada)

        self.botao_descartar.midleft = (largura // 2 + 15, base_y)
        if descarte_fecha_mao:
            desenhar_badge(tela, largura // 2, base_y - 60,
                            "Essa carta fecha sua mão! Descartar = Bater",
                            YELLOW, cor_texto=INK, tamanho_fonte=12, borda=INK)
            desenhar_botao(tela, self.botao_descartar, "Bater!", ativo=True,
                            hover=self.botao_descartar.collidepoint(mouse_pos),
                            tamanho_fonte=18, cor=YELLOW)
        else:
            desenhar_botao(tela, self.botao_descartar, "Descartar", ativo=pode_descartar,
                            hover=pode_descartar and self.botao_descartar.collidepoint(mouse_pos),
                            tamanho_fonte=18, cor=CORAL, cor_texto=PANEL)
        desenhar_kbd(tela, self.botao_descartar.right - 12, self.botao_descartar.bottom - 12, "Enter", ancorar="bottomright")

        if not pode_descartar:
            desenhar_texto(tela, "Arraste as cartas para organizar a mao - clique numa carta para descartar",
                            largura // 2, base_y - 44, tamanho=13, cor=TEXT_MUTED, centralizado=True)

    # ---------------------------------------------------------------- Ultima acao (HUD)
    def _desenhar_historico(self, tela, largura, altura):
        if not self.historico:
            return
        texto, cor = self.historico[-1]
        desenhar_badge(tela, largura - HIST_MARGEM, 64, texto[:44], PANEL, cor_texto=INK,
                        tamanho_fonte=11, ancorar="topright", borda=cor)

    # ---------------------------------------------------------------- Resultado / Fim
    def _desenhar_resultado(self, tela, largura, altura):
        resultado = self.mesa.resultado_mao
        n_linhas = 1 + len(resultado["detalhes"])
        painel = pygame.Rect(0, 0, 480, 110 + 26 * n_linhas)
        painel.center = (largura // 2, altura - 200)
        desenhar_painel(tela, painel, cor=PANEL, radius=20)

        desenhar_texto(tela, "RESULTADO DA MAO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")

        if resultado.get("empate"):
            desenhar_texto(tela, "Ninguem bateu a tempo - mao empatada, ninguem paga.",
                            painel.centerx, painel.y + 52, tamanho=14, cor=INK, centralizado=True, negrito=True)
            return

        if resultado.get("mao_fechada"):
            texto_vitoria = f"{resultado['vencedor']} bateu de MÃO FECHADA e ganhou {resultado['pote']} fichas (dobrado)!"
        else:
            texto_vitoria = f"{resultado['vencedor']} bateu e ganhou {resultado['pote']} fichas!"
        desenhar_texto(tela, texto_vitoria,
                        painel.centerx, painel.y + 52, tamanho=14, cor=INK, centralizado=True, negrito=True)

        y = painel.y + 82
        for d in resultado["detalhes"]:
            desenhar_texto(tela, f"{d['jogador']} pagou {d['pontos']} pontos em cartas soltas",
                            painel.centerx, y, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            y += 26

        self.botao_continuar.center = (painel.centerx, painel.bottom - 30)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_continuar, "Continuar",
                        hover=self.botao_continuar.collidepoint(mouse_pos), tamanho_fonte=18)

    def _desenhar_tela_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((*INK, 150))
        tela.blit(overlay, (0, 0))

        painel = pygame.Rect(0, 0, 440, 220)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=24)

        desenhar_texto(tela, "FIM DE JOGO", painel.centerx, painel.y + 46,
                        tamanho=32, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, f"Vencedor: {self.app.nome_vencedor}", painel.centerx, painel.y + 100,
                        tamanho=19, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=INK, tamanho_fonte=12)
