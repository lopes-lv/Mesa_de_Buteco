"""
table_screen.py - Tela principal de gameplay (a "Mesa").

Responsável por:
 - Desenhar mesa, cartas próprias e comunitárias, stacks e pote
 - Botões interativos: Fold, Check/Call, Raise (com seletor/slider de valor)
 - Orquestrar o turno dos bots automaticamente (com pequeno delay)
 - Mostrar resultado do showdown (incluindo split pot) antes da próxima mão
"""
import pygame
from ui_pixelart import (
    COR_FUNDO, COR_TEXTO, COR_MESA, desenhar_texto, desenhar_botao, desenhar_painel,
    desenhar_carta, desenhar_mesa, desenhar_pilha_fichas
)
from bot_ai import decidir_acao_bot

DELAY_BOT_SEGUNDOS = 0.9


class TableScreen:
    def __init__(self, app, table):
        self.app = app
        self.table = table
        self.id_humano = table.jogadores[0].id

        self.botao_fold = pygame.Rect(0, 0, 140, 54)
        self.botao_call = pygame.Rect(0, 0, 160, 54)
        self.botao_raise = pygame.Rect(0, 0, 140, 54)
        self.botao_confirmar_raise = pygame.Rect(0, 0, 180, 46)
        self.botao_cancelar_raise = pygame.Rect(0, 0, 120, 46)
        self.slider_rect = pygame.Rect(0, 0, 320, 14)
        self.slider_alca = pygame.Rect(0, 0, 20, 30)
        self.botao_continuar = pygame.Rect(0, 0, 240, 54)
        self.botao_sair = pygame.Rect(0, 0, 110, 40)

        self.modo_raise = False
        self.arrastando_slider = False
        self.valor_raise_atual = 0

        self.timer_bot = 0.0
        self.tempo_decorrido = 0.0  # usado para o brilho pulsante de "vez do jogador"
        self.resultados_showdown = None
        self.mensagem_vencedor_por_fold = None

        self.table.iniciar_nova_mao()

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        if self.app.jogo_finalizado:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self.app.ir_para_menu()
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_sair.collidepoint(evento.pos):
                self.app.ir_para_menu()
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

    def _aplicar_acao_humano(self, acao, valor_raise):
        humano = self._jogador(self.id_humano)
        self.table.rodada_atual.aplicar_acao(humano, acao, valor_raise)

    def _jogador(self, id_jogador):
        return next(j for j in self.table.jogadores if j.id == id_jogador)

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
            return

        if rodada.rodada_terminou():
            self.table.avancar_estagio()
            if self.table.estagio == "showdown":
                self.resultados_showdown = self.table.processar_showdown()
                self.table.marcar_eliminados()
            return

        jogador_da_vez = rodada.jogador_da_vez()
        if jogador_da_vez is None:
            return

        if jogador_da_vez.is_bot:
            self.timer_bot += dt
            if self.timer_bot >= DELAY_BOT_SEGUNDOS:
                self.timer_bot = 0.0
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
        else:
            self.timer_bot = 0.0

    def _comecar_proxima_mao_ou_finalizar(self):
        self.resultados_showdown = None
        self.mensagem_vencedor_por_fold = None
        if self.table.jogo_tem_vencedor():
            vencedor = self.table.jogadores_na_mesa()[0]
            self.app.finalizar_jogo(vencedor.nome)
        else:
            self.table.iniciar_nova_mao()

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(COR_FUNDO)

        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.55))
        mesa_rect.center = (largura // 2, int(altura * 0.42))
        desenhar_mesa(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
        self._desenhar_comunitarias(tela, mesa_rect)
        self._desenhar_pote(tela, mesa_rect)
        self._desenhar_marcador_dealer(tela, mesa_rect)
        self._desenhar_jogadores(tela, mesa_rect, largura, altura)

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
        desenhar_texto(tela, f"Mão #{self.table.mao_numero}   Blinds: {sb}/{bb}",
                        largura // 2, 24, tamanho=18, cor=(220, 220, 220), centralizado=True)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos), tamanho_fonte=15)

    def _desenhar_comunitarias(self, tela, mesa_rect):
        n = len(self.table.comunitarias)
        largura_carta, altura_carta = 56, 80
        espaco = 10
        # largura sempre calculada para as 5 cartas finais, para o grupo
        # ficar perfeitamente centralizado na mesa e não "pular" de lugar
        # conforme as cartas do flop/turn/river vão sendo reveladas.
        total_largura = 5 * largura_carta + 4 * espaco
        x0 = mesa_rect.centerx - total_largura // 2
        y0 = mesa_rect.centery - altura_carta // 2 - 20
        for i in range(5):
            x = x0 + i * (largura_carta + espaco)
            if i < n:
                desenhar_carta(tela, x, y0, largura_carta, altura_carta, self.table.comunitarias[i])
            else:
                pygame.draw.rect(tela, (18, 70, 44), (x, y0, largura_carta, altura_carta), 2, border_radius=2)

    def _desenhar_pote(self, tela, mesa_rect):
        pote = sum(j.total_apostado_mao for j in self.table.jogadores)
        desenhar_texto(tela, f"POTE: {pote}", mesa_rect.centerx, mesa_rect.centery + 50,
                        tamanho=20, cor=(230, 200, 60), negrito=True, centralizado=True)

    def _indices_blinds(self):
        dealer_idx = self.table.dealer_idx
        small_blind_idx = self.table._proximo_ativo(dealer_idx)
        big_blind_idx = self.table._proximo_ativo(small_blind_idx)
        return dealer_idx, small_blind_idx, big_blind_idx

    def _desenhar_marcador_dealer(self, tela, mesa_rect):
        x = mesa_rect.centerx
        y = mesa_rect.top + 38
        pygame.draw.circle(tela, (230, 200, 60), (x, y), 24)
        pygame.draw.circle(tela, (30, 30, 24), (x, y), 24, 3)
        desenhar_texto(tela, "D", x, y - 1, tamanho=22, cor=(30, 30, 24),
                       negrito=True, centralizado=True)
        desenhar_texto(tela, "DEALER", x, y + 34, tamanho=11,
                       cor=(230, 200, 60), negrito=True, centralizado=True)

    def _desenhar_marcador_assento(self, tela, mesa_rect, x, y, texto, cor):
        raio = 15 if len(texto) == 1 else 19
        distancia_x = x - mesa_rect.centerx
        distancia_y = y - mesa_rect.centery
        distancia = max(1, (distancia_x ** 2 + distancia_y ** 2) ** 0.5)
        marcador_x = x - int(distancia_x / distancia * 52)
        marcador_y = y - int(distancia_y / distancia * 52)
        pygame.draw.circle(tela, cor, (marcador_x, marcador_y), raio)
        pygame.draw.circle(tela, (20, 24, 30), (marcador_x, marcador_y), raio, 2)
        desenhar_texto(tela, texto, marcador_x, marcador_y, tamanho=11,
                       cor=(20, 24, 30), negrito=True, centralizado=True)

    def _posicoes_assentos(self, mesa_rect, n_jogadores):
        """Retorna assentos visuais FIXOS para todos os n jogadores."""
        import math
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
        else: # 8 jogadores (7 bots)
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
            largura_carta, altura_carta = (60, 86) if eh_humano else (40, 58)
            eh_vez_dele = jogador_da_vez is not None and jogador.id == jogador_da_vez.id

            if indice_jogador == small_blind_idx:
                self._desenhar_marcador_assento(tela, mesa_rect, x, y, "SB", (80, 180, 240))
            elif indice_jogador == big_blind_idx:
                self._desenhar_marcador_assento(tela, mesa_rect, x, y, "BB", (240, 130, 80))

            if eh_vez_dele:
                self._desenhar_brilho_de_vez(tela, x, y, largura_carta, altura_carta)

            cor_nome = COR_TEXTO
            if eh_vez_dele:
                cor_nome = (120, 240, 140)
            status = ""
            if jogador.eliminado:
                status = " (fora)"
            elif jogador.foldou:
                status = " (fold)"
            elif jogador.all_in:
                status = " (all-in)"

            espaco_cartas = 4
            total_largura = 2 * largura_carta + espaco_cartas
            if eh_humano:
                painel_x = x - total_largura // 2 - 118
                desenhar_texto(tela, f"{jogador.nome}{status}", painel_x, y - 28,
                               tamanho=14, cor=cor_nome, centralizado=True,
                               negrito=True)
                desenhar_pilha_fichas(tela, painel_x - 30, y + 2, jogador.stack, raio=7)
            else:
                desenhar_texto(tela, f"{jogador.nome}{status}", x, y - altura_carta - 22,
                               tamanho=14, cor=cor_nome, centralizado=True, negrito=eh_vez_dele)
                desenhar_pilha_fichas(tela, x - 30, y - altura_carta - 4, jogador.stack, raio=7)

            if jogador.eliminado:
                continue

            x0 = x - total_largura // 2
            for i, carta in enumerate(jogador.mao):
                virada = (not eh_humano) and (not mostrar_cartas_bots)
                mostrar_face = eh_humano or (mostrar_cartas_bots and not jogador.foldou)
                desenhar_carta(
                    tela, x0 + i * (largura_carta + espaco_cartas), y - altura_carta // 2,
                    largura_carta, altura_carta,
                    carta=carta if mostrar_face else None,
                    virada_para_baixo=not mostrar_face
                )

            if jogador.aposta_rodada > 0:
                desenhar_texto(tela, f"aposta: {jogador.aposta_rodada}", x, y + altura_carta // 2 + 16,
                                tamanho=12, cor=(200, 200, 120), centralizado=True)

    def _id_dealer(self):
        return self.table.jogadores[self.table.dealer_idx].id

    def _desenhar_brilho_de_vez(self, tela, x, y, largura_carta, altura_carta):
        """Anel pulsante ao redor do assento de quem está com a vez de agir."""
        import math
        pulso = (math.sin(self.tempo_decorrido * 4.0) + 1) / 2  # 0..1
        raio_x = largura_carta + 34 + int(pulso * 6)
        raio_y = altura_carta // 2 + 34 + int(pulso * 6)
        alpha = 110 + int(pulso * 90)

        superficie = pygame.Surface((raio_x * 2, raio_y * 2), pygame.SRCALPHA)
        cor = (120, 240, 140, alpha)
        pygame.draw.ellipse(superficie, cor, (0, 0, raio_x * 2, raio_y * 2), width=5)
        tela.blit(superficie, (x - raio_x, y - raio_y))

    def _desenhar_resultado(self, tela, largura, altura, resultados):
        painel = pygame.Rect(0, 0, 480, 100 + 30 * len(resultados))
        painel.center = (largura // 2, altura - 150)
        desenhar_painel(tela, painel, cor=(20, 24, 30))
        desenhar_texto(tela, "RESULTADO DA MÃO", painel.centerx, painel.y + 20,
                        tamanho=16, cor=(230, 200, 60), centralizado=True, negrito=True)
        for i, r in enumerate(resultados):
            texto = f"{', '.join(r['vencedores'])} venceu {r['pote']} ({r['categoria']})"
            desenhar_texto(tela, texto, painel.centerx, painel.y + 46 + i * 26,
                            tamanho=14, cor=COR_TEXTO, centralizado=True)

        self.botao_continuar.center = (painel.centerx, painel.bottom - 34)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_continuar, "Continuar",
                        hover=self.botao_continuar.collidepoint(mouse_pos), tamanho_fonte=18)

    def _desenhar_tela_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura))
        overlay.set_alpha(210)
        overlay.fill((10, 10, 14))
        tela.blit(overlay, (0, 0))
        desenhar_texto(tela, "FIM DE JOGO", largura // 2, altura // 2 - 50,
                        tamanho=40, cor=(230, 200, 60), negrito=True, centralizado=True)
        desenhar_texto(tela, f"Vencedor: {self.app.nome_vencedor}", largura // 2, altura // 2 + 4,
                        tamanho=22, cor=COR_TEXTO, centralizado=True)
        desenhar_texto(tela, "Clique para voltar ao menu", largura // 2, altura // 2 + 50,
                        tamanho=14, cor=(180, 180, 180), centralizado=True)

    def _desenhar_controles(self, tela, largura, altura):
        rodada = self.table.rodada_atual
        jogador_da_vez = rodada.jogador_da_vez() if rodada else None
        humano = self._jogador(self.id_humano)
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano

        base_y = altura - 90
        self.botao_fold.midleft = (largura // 2 - 240, base_y)
        self.botao_call.midleft = (largura // 2 - 80, base_y)
        self.botao_raise.midleft = (largura // 2 + 100, base_y)

        ativo = eh_vez_do_humano and not self.modo_raise
        mouse_pos = pygame.mouse.get_pos()

        a_pagar = max(0, rodada.aposta_alvo - humano.aposta_rodada) if rodada else 0
        texto_call = "Check" if a_pagar <= 0 else f"Call {a_pagar}"

        desenhar_botao(tela, self.botao_fold, "Fold", hover=ativo and self.botao_fold.collidepoint(mouse_pos), ativo=ativo)
        desenhar_botao(tela, self.botao_call, texto_call, hover=ativo and self.botao_call.collidepoint(mouse_pos), ativo=ativo)
        desenhar_botao(tela, self.botao_raise, "Raise", hover=ativo and self.botao_raise.collidepoint(mouse_pos), ativo=ativo and humano.stack > a_pagar)

        if not eh_vez_do_humano:
            nome_vez = jogador_da_vez.nome if jogador_da_vez else "-"
            desenhar_texto(tela, f"Vez de: {nome_vez}", largura // 2, base_y - 50,
                            tamanho=16, cor=(180, 180, 180), centralizado=True)

        if self.modo_raise:
            self._desenhar_slider_raise(tela, largura, altura, humano, a_pagar)

    def _desenhar_slider_raise(self, tela, largura, altura, humano, a_pagar):
        painel = pygame.Rect(0, 0, 420, 130)
        painel.center = (largura // 2, altura - 170)
        desenhar_painel(tela, painel)

        maximo = max(1, humano.stack - a_pagar)
        self.valor_raise_atual = min(self.valor_raise_atual, maximo)

        desenhar_texto(tela, f"Valor do Raise: {self.valor_raise_atual}", painel.centerx, painel.y + 20,
                        tamanho=16, cor=(230, 200, 60), centralizado=True, negrito=True)

        self.slider_rect.midleft = (painel.x + 30, painel.y + 55)
        self.slider_rect.width = painel.width - 60
        pygame.draw.rect(tela, (60, 66, 76), self.slider_rect)
        pygame.draw.rect(tela, (18, 20, 24), self.slider_rect, 2)

        proporcao = self.valor_raise_atual / maximo if maximo > 0 else 0
        alca_x = self.slider_rect.x + int(proporcao * self.slider_rect.width)
        self.slider_alca.center = (alca_x, self.slider_rect.centery)
        pygame.draw.rect(tela, (230, 200, 60), self.slider_alca)
        pygame.draw.rect(tela, (18, 20, 24), self.slider_alca, 2)

        desenhar_texto(tela, "1", self.slider_rect.x, self.slider_rect.y + 22, tamanho=12, cor=(160, 160, 160))
        desenhar_texto(tela, f"{maximo} (all-in)", self.slider_rect.right, self.slider_rect.y + 22,
                        tamanho=12, cor=(160, 160, 160), centralizado=False)

        self.botao_confirmar_raise.midleft = (painel.x + 20, painel.bottom - 25)
        self.botao_cancelar_raise.midright = (painel.right - 20, painel.bottom - 25)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_confirmar_raise, "Confirmar",
                        hover=self.botao_confirmar_raise.collidepoint(mouse_pos), tamanho_fonte=16)
        desenhar_botao(tela, self.botao_cancelar_raise, "Cancelar",
                        hover=self.botao_cancelar_raise.collidepoint(mouse_pos), tamanho_fonte=16)
