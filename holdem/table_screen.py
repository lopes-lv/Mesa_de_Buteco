"""
table_screen.py - Tela principal de gameplay (a "Mesa").

Responsável por:
 - Desenhar mesa, cartas próprias e comunitárias, stacks e pote
 - Botões interativos: Fold, Check/Call, Raise (com seletor/slider de valor)
 - Orquestrar o turno dos bots automaticamente (com pequeno delay)
 - Mostrar resultado do showdown (incluindo split pot) antes da próxima mão
 - Histórico de ações da rodada, num painel fixo no canto inferior direito
"""
import math
import queue
from collections import deque

import pygame
from core.ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_carta, desenhar_carta_vazia,
    desenhar_mesa, desenhar_pilha_fichas, desenhar_avatar, desenhar_badge,
    desenhar_kbd, desenhar_glow_de_vez, desenhar_cropie,
)
from .bot_ai import decidir_acao_bot
from .game_logic import TIPO_HUMANO_REMOTO
from core.chat_widget import ChatWidget
from rede import protocolo

ANIM_CROUPIER_DURACAO = 0.9

CARTA_BOT = (46, 64)
CARTA_COMUNITARIA = (64, 90)
CARTA_HUMANO = (100, 140)

# As cartas do jogador humano são desenhadas um pouco acima do assento para
# não ficarem atrás dos botões de ação (Fold/Call/Raise), que ficam perto do
# rodapé da tela.
DESLOCAMENTO_CARTAS_HUMANO = 40

PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]

HIST_MAX_LINHAS = 7
HIST_LARGURA = 300
HIST_MARGEM = 24

NAIPE_UNICODE = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}


def _carta_str(carta):
    return f"{carta.texto}{NAIPE_UNICODE.get(carta.simbolo_naipe, carta.simbolo_naipe)}"


class TableScreen:
    def __init__(self, app, table, sala_rede=None):
        self.app = app
        self.table = table
        self.id_humano = table.jogadores[0].id
        self.sala_rede = sala_rede  # AnfitriaoSala, só quando é uma mesa multiplayer (host)

        self.botao_fold = pygame.Rect(0, 0, 172, 68)
        self.botao_call = pygame.Rect(0, 0, 172, 68)
        self.botao_raise = pygame.Rect(0, 0, 172, 68)
        self.botao_confirmar_raise = pygame.Rect(0, 0, 180, 48)
        self.botao_cancelar_raise = pygame.Rect(0, 0, 130, 48)
        self.slider_rect = pygame.Rect(0, 0, 320, 14)
        self.slider_alca = pygame.Rect(0, 0, 22, 32)
        self.botao_continuar = pygame.Rect(0, 0, 240, 56)
        self.botao_sair = pygame.Rect(0, 0, 110, 44)

        self.modo_raise = False
        self.arrastando_slider = False
        self.valor_raise_atual = 0

        self.timer_bot = 0.0
        self.tempo_decorrido = 0.0  # usado para o brilho pulsante de "vez do jogador"
        self.resultados_showdown = None
        self.mensagem_vencedor_por_fold = None

        self.anim_cropie_inicio = None  # instante (tempo_decorrido) em que a última distribuição começou

        self.historico = deque(maxlen=HIST_MAX_LINHAS)
        self.chat = ChatWidget(self._enviar_chat_host) if sala_rede is not None else None
        self._iniciar_mao()

    def _enviar_chat_host(self, texto):
        nome = self.sala_rede.nome_anfitriao
        self.chat.adicionar_mensagem(nome, texto)
        self.sala_rede.enviar_para_todos({"tipo": protocolo.CHAT, "remetente": nome, "texto": texto})

    # ---------------------------------------------------------------- Histórico
    def _registrar(self, texto, cor=TEXT_MUTED):
        self.historico.append((texto, cor))

    def _iniciar_mao(self):
        self.table.iniciar_nova_mao()
        self.historico.clear()
        self._registrar(f"— Mão #{self.table.mao_numero} —", INK)
        self._iniciar_animacao_cropie()
        self._enviar_maos_privadas()
        self._broadcast_estado()

    def _iniciar_animacao_cropie(self):
        self.anim_cropie_inicio = self.tempo_decorrido

    def _registrar_acao(self, jogador, acao, valor):
        rotulos = {"fold": "Fold", "check": "Check", "call": "Call", "raise": f"Raise ({valor})"}
        cores = {"fold": CORAL, "check": BLUE, "call": BLUE, "raise": MINT}
        texto = f"{jogador.nome} deu {rotulos.get(acao, acao)}"
        if jogador.all_in:
            texto += " — All-in!"
        self._registrar(texto, cores.get(acao, TEXT_MUTED))

    def _registrar_estagio(self, estagio):
        com = self.table.comunitarias
        if estagio == "flop":
            cartas = " ".join(_carta_str(c) for c in com[:3])
            self._registrar(f"— Flop: {cartas} —", INK)
        elif estagio == "turn":
            self._registrar(f"— Turn: {_carta_str(com[3])} —", INK)
        elif estagio == "river":
            self._registrar(f"— River: {_carta_str(com[4])} —", INK)

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

        # Resultado da mão (showdown ou vitória por fold): só avança quando
        # o jogador clicar em "Continuar" - nada acontece automaticamente.
        if self.resultados_showdown is not None or self.mensagem_vencedor_por_fold is not None:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.botao_continuar.collidepoint(evento.pos):
                    self._comecar_proxima_mao_ou_finalizar()
            return

        jogador_da_vez = self._jogador_da_vez_seguro()
        eh_vez_do_humano = (
            jogador_da_vez is not None
            and jogador_da_vez.id == self.id_humano
        )

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if not eh_vez_do_humano:
                return
            humano = self._jogador(self.id_humano)
            a_pagar = self.table.rodada_atual.aposta_alvo - humano.aposta_rodada

            if self.modo_raise:
                if self.slider_alca.collidepoint(evento.pos):
                    self.arrastando_slider = True
                elif self.botao_confirmar_raise.collidepoint(evento.pos):
                    self._aplicar_acao_humano("raise", self.valor_raise_atual)
                    self.modo_raise = False
                elif self.botao_cancelar_raise.collidepoint(evento.pos):
                    self.modo_raise = False
                return

            if self.botao_fold.collidepoint(evento.pos):
                self._aplicar_acao_humano("fold", 0)
            elif self.botao_call.collidepoint(evento.pos):
                acao = "check" if a_pagar <= 0 else "call"
                self._aplicar_acao_humano(acao, 0)
            elif self.botao_raise.collidepoint(evento.pos):
                bb = self.table.blinds_atuais()[1]
                min_raise = max(bb, self.table.rodada_atual.ultimo_raise_valor)
                self.valor_raise_atual = min(min_raise, max(1, humano.stack - max(0, a_pagar)))
                self.modo_raise = True

        elif evento.type == pygame.MOUSEBUTTONUP:
            self.arrastando_slider = False

        elif evento.type == pygame.MOUSEMOTION and self.arrastando_slider:
            self._atualizar_valor_slider(evento.pos[0])

        elif evento.type == pygame.KEYDOWN:
            if not eh_vez_do_humano:
                return
            humano = self._jogador(self.id_humano)
            a_pagar = self.table.rodada_atual.aposta_alvo - humano.aposta_rodada

            if self.modo_raise:
                if evento.key == pygame.K_RETURN:
                    self._aplicar_acao_humano("raise", self.valor_raise_atual)
                    self.modo_raise = False
                return

            if evento.key == pygame.K_f:
                self._aplicar_acao_humano("fold", 0)
            elif evento.key == pygame.K_c:
                acao = "check" if a_pagar <= 0 else "call"
                self._aplicar_acao_humano(acao, 0)
            elif evento.key == pygame.K_r:
                bb = self.table.blinds_atuais()[1]
                min_raise = max(bb, self.table.rodada_atual.ultimo_raise_valor)
                self.valor_raise_atual = min(min_raise, max(1, humano.stack - max(0, a_pagar)))
                self.modo_raise = True

    def _atualizar_valor_slider(self, mouse_x):
        humano = self._jogador(self.id_humano)
        a_pagar = max(0, self.table.rodada_atual.aposta_alvo - humano.aposta_rodada)
        maximo = max(1, humano.stack - a_pagar)
        bb = self.table.blinds_atuais()[1]
        min_raise = max(bb, self.table.rodada_atual.ultimo_raise_valor)
        min_raise = min(min_raise, maximo)

        proporcao = (mouse_x - self.slider_rect.x) / max(1, self.slider_rect.width)
        proporcao = min(1.0, max(0.0, proporcao))

        valor_bruto = int(maximo * proporcao)
        self.valor_raise_atual = max(min_raise, valor_bruto)

    def _aplicar_acao_jogador(self, jogador, acao, valor_raise):
        self.table.rodada_atual.aplicar_acao(jogador, acao, valor_raise)
        self._registrar_acao(jogador, acao, valor_raise)

    def _aplicar_acao_humano(self, acao, valor_raise):
        humano = self._jogador(self.id_humano)
        self._aplicar_acao_jogador(humano, acao, valor_raise)
        self._broadcast_estado()

    def _jogador(self, id_jogador):
        return next(j for j in self.table.jogadores if j.id == id_jogador)

    def _jogador_por_id(self, id_jogador):
        return next((j for j in self.table.jogadores if j.id == id_jogador), None)

    # ---------------------------------------------------------------- Rede (host)
    def _enviar_maos_privadas(self):
        if self.sala_rede is None:
            return
        for jogador in self.table.jogadores:
            if jogador.tipo == TIPO_HUMANO_REMOTO and not jogador.eliminado:
                self.sala_rede.enviar_para(jogador.id, {
                    "tipo": protocolo.SUA_MAO,
                    "cartas": [[carta.valor, carta.naipe] for carta in jogador.mao],
                })

    def _broadcast_estado(self):
        if self.sala_rede is None:
            return
        self.sala_rede.enviar_para_todos(self._serializar_estado())

    def _serializar_estado(self):
        rodada = self.table.rodada_atual
        jogador_da_vez = rodada.jogador_da_vez() if rodada else None
        sb, bb = self.table.blinds_atuais()

        jogadores = []
        for j in self.table.jogadores:
            jogadores.append({
                "id": j.id, "nome": j.nome, "stack": j.stack,
                "aposta_rodada": j.aposta_rodada, "foldou": j.foldou,
                "all_in": j.all_in, "eliminado": j.eliminado,
                "desconectado": bool(self.sala_rede and j.id in self.sala_rede.desconectados),
            })

        resultado = self.resultados_showdown or self.mensagem_vencedor_por_fold

        return {
            "tipo": protocolo.ESTADO,
            "mao_numero": self.table.mao_numero,
            "blinds": [sb, bb],
            "estagio": self.table.estagio,
            "comunitarias": [[c.valor, c.naipe] for c in self.table.comunitarias],
            "pote": sum(j.total_apostado_mao for j in self.table.jogadores),
            "aposta_alvo": rodada.aposta_alvo if rodada else 0,
            "ultimo_raise_valor": rodada.ultimo_raise_valor if rodada else bb,
            "dealer_id": self.table.jogadores[self.table.dealer_idx].id,
            "jogador_da_vez_id": jogador_da_vez.id if jogador_da_vez else None,
            "jogadores": jogadores,
            "historico": [texto for texto, _cor in list(self.historico)],
            "resultado": resultado,
        }

    def _drenar_mensagens_rede(self):
        while True:
            try:
                jogador_id, msg = self.sala_rede.mensagens_entrantes.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == protocolo.ACAO:
                self._processar_acao_remota(jogador_id, msg)
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

    def _processar_acao_remota(self, jogador_id, msg):
        rodada = self.table.rodada_atual
        jogador_da_vez = rodada.jogador_da_vez() if rodada else None
        jogador = self._jogador_por_id(jogador_id)

        erro = None
        acao = msg.get("acao")
        valor = msg.get("valor", 0)

        if jogador is None:
            erro = "Jogador desconhecido"
        elif jogador_da_vez is None or jogador_da_vez.id != jogador_id:
            erro = "Não é a sua vez"
        elif acao not in ("fold", "check", "call", "raise"):
            erro = "Ação inválida"
        else:
            a_pagar = max(0, rodada.aposta_alvo - jogador.aposta_rodada)
            if acao == "check" and a_pagar > 0:
                erro = "Não é possível dar check havendo aposta a pagar"
            elif acao == "raise":
                if not isinstance(valor, (int, float)) or valor <= 0:
                    erro = "Valor de raise inválido"
                elif valor > jogador.stack - a_pagar:
                    erro = "Valor de raise maior que seu stack disponível"

        if erro:
            self.sala_rede.enviar_para(jogador_id, {"tipo": protocolo.ERRO_ACAO, "motivo": erro})
            return

        self._aplicar_acao_jogador(jogador, acao, int(valor) if acao == "raise" else 0)
        self._broadcast_estado()

    def _posicao_relativa(self, jogador):
        """Retorna quantos jogadores ativos agem depois deste bot."""
        ativos = [
            self.table.jogadores[i]
            for i in self.table.ordem_assentos
            if not self.table.jogadores[i].eliminado
        ]
        if not ativos:
            return 0
        indice = ativos.index(jogador)
        indice_dealer = next(
            (i for i, j in enumerate(ativos) if j.id == self._id_dealer()), 0
        )
        return (indice - indice_dealer - 1) % len(ativos)

    def _jogador_da_vez_seguro(self):
        if self.table.rodada_atual is None:
            return None
        return self.table.rodada_atual.jogador_da_vez()

    # ---------------------------------------------------------------- Update
    def atualizar(self, dt):
        self.tempo_decorrido += dt

        if self.app.jogo_finalizado:
            return

        if self.sala_rede is not None:
            self._drenar_mensagens_rede()

        # Enquanto o resultado da mão estiver na tela, aguarda o clique em
        # "Continuar" (ver tratar_evento) em vez de avançar sozinho.
        if self.resultados_showdown is not None or self.mensagem_vencedor_por_fold is not None:
            return

        rodada = self.table.rodada_atual
        if rodada is None:
            return

        if self.table.mao_finalizada_por_fold():
            resultados = self.table.processar_showdown()
            self.table.marcar_eliminados()
            self.mensagem_vencedor_por_fold = resultados
            self._broadcast_estado()
            return

        if rodada.rodada_terminou():
            self.table.avancar_estagio()
            self._registrar_estagio(self.table.estagio)
            if self.table.estagio in ("flop", "turn", "river"):
                self._iniciar_animacao_cropie()
            if self.table.estagio == "showdown":
                self.resultados_showdown = self.table.processar_showdown()
                self.table.marcar_eliminados()
            self._broadcast_estado()
            return

        jogador_da_vez = rodada.jogador_da_vez()
        if jogador_da_vez is None:
            return

        desconectado = (
            self.sala_rede is not None
            and jogador_da_vez.tipo == TIPO_HUMANO_REMOTO
            and jogador_da_vez.id in self.sala_rede.desconectados
        )

        if jogador_da_vez.is_bot or desconectado:
            self.timer_bot += dt
            if self.timer_bot >= self.app.settings.delay_bot():
                self.timer_bot = 0.0
                if desconectado:
                    acao, valor = "fold", 0
                else:
                    sb, bb = self.table.blinds_atuais()
                    acao, valor = decidir_acao_bot(
                        jogador_da_vez, self.table.estagio, self.table.comunitarias,
                        rodada.aposta_alvo, bb,
                        pote=sum(j.total_apostado_mao for j in self.table.jogadores),
                        oponentes_ativos=len(rodada.jogadores_ativos_na_mao()) - 1,
                        posicao=self._posicao_relativa(jogador_da_vez),
                        jogadores_agiram=len(rodada.jogadores_que_agiram),
                        ultimo_raise=rodada.ultimo_raise_valor
                    )
                rodada.aplicar_acao(jogador_da_vez, acao, valor)
                self._registrar_acao(jogador_da_vez, acao, valor)
                self._broadcast_estado()
        else:
            self.timer_bot = 0.0

    def _comecar_proxima_mao_ou_finalizar(self):
        self.resultados_showdown = None
        self.mensagem_vencedor_por_fold = None
        if self.table.jogo_tem_vencedor():
            vencedor = self.table.jogadores_na_mesa()[0]
            if self.sala_rede is not None:
                self.sala_rede.enviar_para_todos({"tipo": protocolo.FIM_DE_JOGO, "vencedor": vencedor.nome})
            self.app.finalizar_jogo(vencedor.nome)
        else:
            self._iniciar_mao()

    def _sair_para_menu(self):
        if self.sala_rede is not None:
            self.sala_rede.encerrar()
        self.app.ir_para_menu()

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)

        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.55))
        mesa_rect.center = (largura // 2, int(altura * 0.42))
        desenhar_mesa(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
        self._desenhar_comunitarias(tela, mesa_rect)
        self._desenhar_pote(tela, mesa_rect)
        self._desenhar_marcador_dealer(tela, mesa_rect)
        self._desenhar_jogadores(tela, mesa_rect, largura, altura)
        self._desenhar_historico(tela, largura, altura)

        if self.chat is not None:
            self.chat.desenhar(tela, largura, altura)

        if self.app.jogo_finalizado:
            self._desenhar_tela_final(tela, largura, altura)
            return

        self._desenhar_botao_sair(tela)

        if self.resultados_showdown is not None:
            self._desenhar_resultado(tela, largura, altura, self.resultados_showdown)
        elif self.mensagem_vencedor_por_fold is not None:
            self._desenhar_resultado(tela, largura, altura, self.mensagem_vencedor_por_fold)
        else:
            self._desenhar_controles(tela, largura, altura)

    def _desenhar_topo(self, tela, largura):
        sb, bb = self.table.blinds_atuais()
        desenhar_badge(tela, largura // 2, 30, f"MÃO #{self.table.mao_numero}   BLINDS {sb}/{bb}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)

        humano = self._jogador(self.id_humano)
        desenhar_badge(tela, largura - 24, 30, f"VOCÊ: {humano.stack}",
                        YELLOW, cor_texto=INK, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    def _desenhar_comunitarias(self, tela, mesa_rect):
        n = len(self.table.comunitarias)
        largura_carta, altura_carta = CARTA_COMUNITARIA
        espaco = 12
        # largura sempre calculada para as 5 cartas finais, para o grupo
        # ficar perfeitamente centralizado na mesa e não "pular" de lugar
        # conforme as cartas do flop/turn/river vão sendo reveladas.
        total_largura = 5 * largura_carta + 4 * espaco
        x0 = mesa_rect.centerx - total_largura // 2
        y0 = mesa_rect.centery - altura_carta // 2 - 22
        for i in range(5):
            x = x0 + i * (largura_carta + espaco)
            if i < n:
                desenhar_carta(tela, x, y0, largura_carta, altura_carta, self.table.comunitarias[i])
            else:
                desenhar_carta_vazia(tela, x, y0, largura_carta, altura_carta)

    def _desenhar_pote(self, tela, mesa_rect):
        pote = sum(j.total_apostado_mao for j in self.table.jogadores)
        desenhar_badge(tela, mesa_rect.centerx, mesa_rect.centery + 56, f"POTE: {pote}",
                        YELLOW, cor_texto=INK, tamanho_fonte=16, familia="mono", borda=INK)

    def _indices_blinds(self):
        dealer_idx = self.table.dealer_idx
        small_blind_idx = self.table._proximo_ativo(dealer_idx)
        big_blind_idx = self.table._proximo_ativo(small_blind_idx)
        return dealer_idx, small_blind_idx, big_blind_idx

    def _desenhar_marcador_dealer(self, tela, mesa_rect):
        x = mesa_rect.centerx
        y = mesa_rect.top + 44

        progresso = 0.0
        if self.anim_cropie_inicio is not None:
            decorrido = self.tempo_decorrido - self.anim_cropie_inicio
            if decorrido < ANIM_CROUPIER_DURACAO:
                progresso = decorrido / ANIM_CROUPIER_DURACAO
            else:
                self.anim_cropie_inicio = None

        desenhar_cropie(tela, x, y, progresso)
        desenhar_badge(tela, x, y + 64, "CROUPIÊ", INK, cor_texto=BG, tamanho_fonte=9, familia="mono")

    def _posicoes_assentos(self, mesa_rect, n_jogadores):
        """Retorna assentos visuais FIXOS para todos os n jogadores."""
        if n_jogadores == 2:
            angulos = [90, 180]
        elif n_jogadores == 3:
            angulos = [90, 180, 0]
        elif n_jogadores == 4:
            # Em vez de usar 270 (topo), usamos 225 (diagonal superior esquerda)
            # para deixar o centro livre para o Dealer.
            angulos = [90, 180, 225, 0]
        elif n_jogadores == 5:
            angulos = [90, 150, 210, 330, 30]
        elif n_jogadores == 6:
            angulos = [90, 135, 180, 225, 315, 0]
        elif n_jogadores == 7:
            angulos = [90, 135, 180, 225, 315, 0, 45]
        else:  # 8 jogadores (7 bots)
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

    def _iniciais(self, nome):
        partes = nome.replace('"', "").split()
        if len(partes) >= 2:
            return (partes[0][0] + partes[1][0]).upper()
        return nome[:2].upper()

    def _status_bot(self, jogador, eh_vez_dele):
        if jogador.eliminado:
            return "Eliminado", LOCKED, TEXT_MUTED
        if (self.sala_rede is not None and jogador.tipo == TIPO_HUMANO_REMOTO
                and jogador.id in self.sala_rede.desconectados):
            return "Desconectado", LOCKED, TEXT_MUTED
        if jogador.foldou:
            return "Fold", LOCKED, TEXT_MUTED
        if jogador.all_in:
            return "All-in", PURPLE, PANEL
        if eh_vez_dele:
            return "Pensando...", BLUE, PANEL
        if jogador.aposta_rodada > 0:
            return f"Apostou {jogador.aposta_rodada}", MINT, INK
        return None, None, None

    def _desenhar_jogadores(self, tela, mesa_rect, largura, altura):
        n = len(self.table.jogadores)
        posicoes = self._posicoes_assentos(mesa_rect, n)
        mostrar_cartas_bots = self.resultados_showdown is not None or self.mensagem_vencedor_por_fold is not None
        dealer_idx, small_blind_idx, big_blind_idx = self._indices_blinds()

        jogador_da_vez = None
        if not mostrar_cartas_bots and not self.app.jogo_finalizado:
            jogador_da_vez = self._jogador_da_vez_seguro()

        for indice_jogador, (x, y) in enumerate(posicoes):
            jogador = self.table.jogadores[indice_jogador]
            eh_humano = jogador.id == self.id_humano
            largura_carta, altura_carta = CARTA_HUMANO if eh_humano else CARTA_BOT
            eh_vez_dele = jogador_da_vez is not None and jogador.id == jogador_da_vez.id

            if indice_jogador == small_blind_idx:
                selo_posicao = ("SB", BLUE)
            elif indice_jogador == big_blind_idx:
                selo_posicao = ("BB", CORAL)
            else:
                selo_posicao = None

            # As cartas (e tudo ancorado a elas: glow, badge de aposta) do
            # jogador humano sobem um pouco para não ficarem atrás dos
            # botões de ação; o painel de nome/stack ao lado não é afetado.
            y_cartas = y - DESLOCAMENTO_CARTAS_HUMANO if eh_humano else y

            if eh_vez_dele:
                desenhar_glow_de_vez(tela, x, y_cartas, largura_carta, altura_carta, self.tempo_decorrido)

            espaco_cartas = 8 if eh_humano else 4
            total_largura = 2 * largura_carta + espaco_cartas

            if eh_humano:
                self._desenhar_painel_humano(tela, jogador, x, y, largura_carta, altura_carta, total_largura, selo_posicao)
            else:
                self._desenhar_painel_bot(tela, jogador, x, y, altura_carta, eh_vez_dele, selo_posicao)

            if jogador.eliminado:
                continue

            x0 = x - total_largura // 2
            for i, carta in enumerate(jogador.mao):
                mostrar_face = eh_humano or (mostrar_cartas_bots and not jogador.foldou)
                desenhar_carta(
                    tela, x0 + i * (largura_carta + espaco_cartas), y_cartas - altura_carta // 2,
                    largura_carta, altura_carta,
                    carta=carta if mostrar_face else None,
                    virada_para_baixo=not mostrar_face
                )

            if jogador.aposta_rodada > 0:
                desenhar_badge(tela, x, y_cartas + altura_carta // 2 + 20, str(jogador.aposta_rodada),
                                PANEL, cor_texto=INK, tamanho_fonte=11, familia="mono", borda=INK)

    def _desenhar_painel_bot(self, tela, jogador, x, y, altura_carta, eh_vez_dele, selo_posicao=None):
        cor_avatar = PALETA_AVATAR[jogador.id % len(PALETA_AVATAR)]
        painel_w, painel_h = 178, 62
        painel = pygame.Rect(0, 0, painel_w, painel_h)
        painel.centerx = x
        painel.bottom = y - altura_carta // 2 - 14

        fundo = LOCKED if (jogador.foldou or jogador.eliminado) else PANEL
        desenhar_painel(tela, painel, cor=fundo, radius=16, deslocamento_sombra=(3, 3))

        cx_avatar = painel.x + 34
        desenhar_avatar(tela, cx_avatar, painel.centery, 22, cor_avatar, self._iniciais(jogador.nome))

        cor_nome = TEXT_MUTED if (jogador.foldou or jogador.eliminado) else INK
        desenhar_texto(tela, jogador.nome, painel.x + 62, painel.y + 12, tamanho=13,
                        cor=cor_nome, negrito=True)
        desenhar_texto(tela, str(jogador.stack), painel.x + 62, painel.y + 30, tamanho=12,
                        cor=TEXT_MUTED, familia="mono")

        status_texto, status_cor, status_cor_texto = self._status_bot(jogador, eh_vez_dele)
        if status_texto:
            desenhar_badge(tela, painel.x + 62, painel.y + 48, status_texto, status_cor,
                            cor_texto=status_cor_texto, tamanho_fonte=9, ancorar="midleft")

        if selo_posicao:
            texto_selo, cor_selo = selo_posicao
            desenhar_badge(tela, painel.right, painel.top, texto_selo, cor_selo,
                            cor_texto=PANEL, tamanho_fonte=9, ancorar="center", borda=INK)

    def _desenhar_painel_humano(self, tela, jogador, x, y, largura_carta, altura_carta, total_largura, selo_posicao=None):
        painel_w, painel_h = 176, 68
        painel = pygame.Rect(0, 0, painel_w, painel_h)
        painel.right = x - total_largura // 2 - 26
        painel.centery = y

        if selo_posicao:
            texto_selo, cor_selo = selo_posicao
            desenhar_badge(tela, painel.right, painel.top, texto_selo, cor_selo,
                            cor_texto=PANEL, tamanho_fonte=9, ancorar="center", borda=INK)

        desenhar_painel(tela, painel, cor=PANEL, radius=16, deslocamento_sombra=(3, 3))
        desenhar_texto(tela, jogador.nome, painel.centerx, painel.y + 18, tamanho=15,
                        cor=INK, negrito=True, centralizado=True)
        desenhar_pilha_fichas(tela, painel.centerx - 30, painel.y + 46, jogador.stack, raio=8)

        if jogador.foldou:
            desenhar_badge(tela, painel.centerx, painel.bottom - 12, "Fold", LOCKED,
                            cor_texto=TEXT_MUTED, tamanho_fonte=9)
        elif jogador.all_in:
            desenhar_badge(tela, painel.centerx, painel.bottom - 12, "All-in", PURPLE,
                            cor_texto=PANEL, tamanho_fonte=9)

    def _id_dealer(self):
        return self.table.jogadores[self.table.dealer_idx].id

    # ---------------------------------------------------------------- Histórico (HUD)
    def _desenhar_historico(self, tela, largura, altura):
        altura_linha = 26
        altura_painel = 44 + HIST_MAX_LINHAS * altura_linha
        painel = pygame.Rect(0, 0, HIST_LARGURA, altura_painel)
        painel.bottomright = (largura - HIST_MARGEM, altura - HIST_MARGEM)
        desenhar_painel(tela, painel, cor=PANEL, radius=20, deslocamento_sombra=(5, 5))

        desenhar_texto(tela, "HISTÓRICO DA RODADA", painel.x + 18, painel.y + 14,
                        tamanho=12, cor=INK, negrito=True)
        pygame.draw.line(tela, INK, (painel.x + 16, painel.y + 34),
                          (painel.right - 16, painel.y + 34), 2)

        y = painel.y + 42
        for texto, cor in self.historico:
            pygame.draw.rect(tela, cor, (painel.x + 16, y + 4, 4, altura_linha - 10), border_radius=2)
            desenhar_texto(tela, texto[:34], painel.x + 26, y + int(altura_linha * 0.5),
                            tamanho=12, cor=INK if cor != TEXT_MUTED else TEXT_MUTED)
            y += altura_linha

    def _desenhar_resultado(self, tela, largura, altura, resultados):
        painel = pygame.Rect(0, 0, 480, 110 + 30 * len(resultados))
        painel.center = (largura // 2, altura - 160)
        desenhar_painel(tela, painel, cor=PANEL, radius=20)
        desenhar_texto(tela, "RESULTADO DA MÃO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")
        for i, r in enumerate(resultados):
            texto = f"{', '.join(r['vencedores'])} venceu {r['pote']} ({r['categoria']})"
            desenhar_texto(tela, texto, painel.centerx, painel.y + 52 + i * 26,
                            tamanho=14, cor=TEXT_MUTED, centralizado=True)

        self.botao_continuar.center = (painel.centerx, painel.bottom - 38)
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

    def _desenhar_controles(self, tela, largura, altura):
        rodada = self.table.rodada_atual
        jogador_da_vez = rodada.jogador_da_vez() if rodada else None
        humano = self._jogador(self.id_humano)
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano

        base_y = altura - 90
        self.botao_fold.midleft = (largura // 2 - 278, base_y)
        self.botao_call.midleft = (largura // 2 - 86, base_y)
        self.botao_raise.midleft = (largura // 2 + 106, base_y)

        ativo = eh_vez_do_humano and not self.modo_raise
        mouse_pos = pygame.mouse.get_pos()

        a_pagar = max(0, rodada.aposta_alvo - humano.aposta_rodada) if rodada else 0
        texto_call = "Check" if a_pagar <= 0 else f"Call {a_pagar}"

        mostrar_atalhos = self.app.settings.mostrar_atalhos

        desenhar_botao(tela, self.botao_fold, "Fold", hover=ativo and self.botao_fold.collidepoint(mouse_pos),
                        ativo=ativo, cor=CORAL, cor_texto=PANEL)
        if mostrar_atalhos:
            desenhar_kbd(tela, self.botao_fold.right - 12, self.botao_fold.bottom - 12, "F", ancorar="bottomright")

        desenhar_botao(tela, self.botao_call, texto_call, hover=ativo and self.botao_call.collidepoint(mouse_pos),
                        ativo=ativo, cor=BLUE, cor_texto=PANEL)
        if mostrar_atalhos:
            desenhar_kbd(tela, self.botao_call.right - 12, self.botao_call.bottom - 12, "C", ancorar="bottomright")

        pode_raise = ativo and humano.stack > a_pagar
        desenhar_botao(tela, self.botao_raise, "Raise", hover=pode_raise and self.botao_raise.collidepoint(mouse_pos),
                        ativo=pode_raise, cor=MINT, cor_texto=INK)
        if mostrar_atalhos:
            desenhar_kbd(tela, self.botao_raise.right - 12, self.botao_raise.bottom - 12, "R", ancorar="bottomright")

        if not eh_vez_do_humano:
            nome_vez = jogador_da_vez.nome if jogador_da_vez else "-"
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)

        if self.modo_raise:
            self._desenhar_slider_raise(tela, largura, altura, humano, a_pagar)

    def _desenhar_slider_raise(self, tela, largura, altura, humano, a_pagar):
        painel = pygame.Rect(0, 0, 420, 140)
        painel.center = (largura // 2, altura - 180)
        desenhar_painel(tela, painel, cor=PANEL, radius=20)

        maximo = max(1, humano.stack - a_pagar)
        self.valor_raise_atual = min(self.valor_raise_atual, maximo)

        desenhar_texto(tela, f"Valor do Raise: {self.valor_raise_atual}", painel.centerx, painel.y + 24,
                        tamanho=16, cor=INK, centralizado=True, negrito=True, familia="mono")

        self.slider_rect.midleft = (painel.x + 30, painel.y + 62)
        self.slider_rect.width = painel.width - 60
        pygame.draw.rect(tela, LOCKED, self.slider_rect, border_radius=7)
        pygame.draw.rect(tela, INK, self.slider_rect, 2, border_radius=7)

        proporcao = self.valor_raise_atual / maximo if maximo > 0 else 0
        alca_x = self.slider_rect.x + int(proporcao * self.slider_rect.width)
        self.slider_alca.center = (alca_x, self.slider_rect.centery)
        pygame.draw.rect(tela, INK, self.slider_alca.move(2, 2), border_radius=6)
        pygame.draw.rect(tela, MINT, self.slider_alca, border_radius=6)
        pygame.draw.rect(tela, INK, self.slider_alca, 2, border_radius=6)

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
