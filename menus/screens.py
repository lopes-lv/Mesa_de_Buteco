"""
screens.py - Telas de Menu Inicial e Configuração (pré-jogo).
A tela de Mesa/Gameplay fica em table_screen.py por ser mais extensa.
"""
import pygame
from core.ui_theme import (
    BG, PANEL, INK, SOMBRA, TEXT_MUTED, YELLOW, CORAL, MINT, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_carta,
    desenhar_kbd, desenhar_badge, obter_fonte,
)
from core.deck import Card
from domino.domino_theme import desenhar_peca
from core.settings import ROTULOS_VELOCIDADE, ROTULOS_BARALHO_SKIN


class MenuScreen:
    """Menu Inicial: título + ações principais."""

    def __init__(self, app):
        self.app = app
        self.botao_jogar = pygame.Rect(0, 0, 300, 68)
        self.botao_config = pygame.Rect(0, 0, 230, 68)
        self.botao_sair = pygame.Rect(0, 0, 160, 68)

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_jogar.collidepoint(evento.pos):
                self.app.ir_para_escolha_modo()
            elif self.botao_config.collidepoint(evento.pos):
                self.app.ir_para_ajustes()
            elif self.botao_sair.collidepoint(evento.pos):
                self.app.encerrar()
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_RETURN:
                self.app.ir_para_escolha_modo()
            elif evento.key == pygame.K_ESCAPE:
                self.app.encerrar()

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        # ---- Logo / título ----
        # Largura do lockup (selo + título) é medida antes de desenhar, para
        # o grupo inteiro ficar corretamente centralizado sem se sobrepor.
        centro_y = altura // 2 - 90
        selo_w = 84
        gap = 22
        fonte_titulo = obter_fonte(46, True, "display")
        titulo_surf = fonte_titulo.render("TEXAS HOLD'EM", True, INK)

        total_w = selo_w + gap + titulo_surf.get_width()
        inicio_x = largura // 2 - total_w // 2

        selo = pygame.Rect(0, 0, selo_w, selo_w)
        selo.center = (inicio_x + selo_w // 2, centro_y)
        desenhar_painel(tela, selo, cor=YELLOW, radius=0, deslocamento_sombra=(5, 5))
        desenhar_texto(tela, "♠", selo.centerx, selo.centery - 2, tamanho=40,
                        cor=INK, centralizado=True)

        titulo_x = inicio_x + selo_w + gap
        titulo_rect = titulo_surf.get_rect(midleft=(titulo_x, centro_y - 14))
        tela.blit(titulo_surf, titulo_rect)
        desenhar_texto(tela, "SOLO VS BOTS  •  MESA DE 8 JOGADORES",
                        titulo_rect.left, titulo_rect.bottom + 12, tamanho=13, cor=TEXT_MUTED,
                        familia="mono")

        # ---- Ações principais ----
        # Linha de 3 botões (Jogar / Configurações / Sair) com espaço real
        # entre eles, centralizada como um único grupo.
        espaco_botoes = 24
        largura_total = (self.botao_jogar.width + self.botao_config.width
                          + self.botao_sair.width + 2 * espaco_botoes)
        x0 = largura // 2 - largura_total // 2
        y_botoes = altura // 2 + 70

        self.botao_jogar.midleft = (x0, y_botoes)
        self.botao_config.midleft = (self.botao_jogar.right + espaco_botoes, y_botoes)
        self.botao_sair.midleft = (self.botao_config.right + espaco_botoes, y_botoes)

        hover_jogar = self.botao_jogar.collidepoint(mouse_pos)
        hover_config = self.botao_config.collidepoint(mouse_pos)
        hover_sair = self.botao_sair.collidepoint(mouse_pos)

        desenhar_botao(tela, self.botao_jogar, "Jogar", hover=hover_jogar,
                        tamanho_fonte=22, cor=YELLOW)
        desenhar_kbd(tela, self.botao_jogar.right - 16, self.botao_jogar.centery, "Enter", ancorar="midright")

        desenhar_botao(tela, self.botao_config, "Configurações", hover=hover_config,
                        tamanho_fonte=17, cor=PANEL)

        desenhar_botao(tela, self.botao_sair, "Sair", hover=hover_sair,
                        tamanho_fonte=22, cor=CORAL, cor_texto=INK)
        desenhar_kbd(tela, self.botao_sair.right - 16, self.botao_sair.centery, "Esc", ancorar="midright")

        desenhar_texto(tela, "Redimensione a janela livremente",
                        largura // 2, altura - 36, tamanho=13, cor=TEXT_MUTED, centralizado=True)


class ModeSelectScreen:
    """Tela de Escolha de Modo: Texas Hold'em, Pif Paf ou modos futuros."""

    MODOS = [
        {"id": "holdem", "titulo": "TEXAS HOLD'EM", "subtitulo": "No-Limit, torneio contra bots",
         "simbolo": "♠", "ativo": True},
        {"id": "pifpaf", "titulo": "PIF PAF", "subtitulo": "Compra, descarte e batida",
         "simbolo": "♣", "ativo": True},
        {"id": "domino", "titulo": "DOMINÓ", "subtitulo": "Corrida aos 250 pontos, 3 a 4 jogadores",
         "simbolo": None, "ativo": True},
        {"id": "inedito", "titulo": "MODO INEDITO", "subtitulo": "Em breve",
         "simbolo": "?", "ativo": False},
    ]

    def __init__(self, app):
        self.app = app
        self.cartoes = [pygame.Rect(0, 0, 250, 280) for _ in self.MODOS]
        self.botao_voltar = pygame.Rect(0, 0, 150, 48)

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_voltar.collidepoint(evento.pos):
                self.app.ir_para_menu()
                return
            for rect, modo in zip(self.cartoes, self.MODOS):
                if modo["ativo"] and rect.collidepoint(evento.pos):
                    self.app.ir_para_config(modo["id"])
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.app.ir_para_menu()

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        desenhar_texto(tela, "ESCOLHA O MODO", largura // 2, altura // 6,
                        tamanho=30, cor=INK, negrito=True, centralizado=True, familia="display")

        espaco = 30
        n = len(self.MODOS)
        total_largura = n * self.cartoes[0].width + (n - 1) * espaco
        x0 = largura // 2 - total_largura // 2
        y0 = altura // 2 - self.cartoes[0].height // 2

        for i, (rect, modo) in enumerate(zip(self.cartoes, self.MODOS)):
            rect.topleft = (x0 + i * (rect.width + espaco), y0)
            hover = modo["ativo"] and rect.collidepoint(mouse_pos)
            cor_fundo = PANEL if modo["ativo"] else LOCKED
            desenho_rect = rect.move(-3, -3) if hover else rect
            desenhar_painel(tela, desenho_rect, cor=cor_fundo, radius=0,
                             deslocamento_sombra=(8, 8) if hover else (6, 6))

            cor_simbolo = INK if modo["ativo"] else TEXT_MUTED
            if modo["simbolo"] is None:  # Dominó: sem glifo Unicode confiável, desenha a peça
                largura_icone, altura_icone = 34, 58
                desenhar_peca(tela, desenho_rect.centerx - largura_icone // 2, desenho_rect.y + 70 - altura_icone // 2,
                              largura_icone, altura_icone, 6, 5, vertical=True)
            else:
                desenhar_texto(tela, modo["simbolo"], desenho_rect.centerx, desenho_rect.y + 70,
                                tamanho=48, cor=cor_simbolo, centralizado=True)
            desenhar_texto(tela, modo["titulo"], desenho_rect.centerx, desenho_rect.y + 140,
                            tamanho=17, cor=INK if modo["ativo"] else TEXT_MUTED, negrito=True,
                            centralizado=True, familia="display")
            desenhar_texto(tela, modo["subtitulo"], desenho_rect.centerx, desenho_rect.y + 168,
                            tamanho=12, cor=TEXT_MUTED, centralizado=True)

            badge_texto = "ATIVO" if modo["ativo"] else "EM BREVE"
            badge_cor = MINT if modo["ativo"] else LOCKED
            desenhar_badge(tela, desenho_rect.centerx, desenho_rect.bottom - 30, badge_texto,
                            badge_cor, cor_texto=(SOMBRA if modo["ativo"] else INK),
                            tamanho_fonte=11, borda=INK)

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)


class ConfigScreen:
    """Tela de Configuração: escolha da quantidade de bots na mesa."""

    TITULOS_MODO = {"holdem": "TEXAS HOLD'EM", "pifpaf": "PIF PAF", "domino": "DOMINÓ"}

    def __init__(self, app, modo="holdem"):
        self.app = app
        self.modo = modo
        self.quantidade_bots = 2 if modo == "domino" else 3
        # Dominó (duplo-seis) só comporta 3-4 jogadores no total (com 3, a
        # peça 0/0 sai do jogo pra dividir 27 peças certinho em 9 cada -
        # ver domino_logic.criar_pecas).
        self.min_bots = 2 if modo == "domino" else 1
        self.max_bots = 3 if modo == "domino" else 7
        self.botao_menos = pygame.Rect(0, 0, 52, 52)
        self.botao_mais = pygame.Rect(0, 0, 52, 52)
        self.botao_iniciar = pygame.Rect(0, 0, 360, 64)
        self.botao_voltar = pygame.Rect(0, 0, 150, 48)
        self.carta_preview = Card(14, "espadas")  # Ás de Espadas

        # Multiplayer local: Hold'em, Pif Paf e Dominó (ver MULTIPLAYER_PLANO.md).
        self.suporta_multiplayer = modo in ("holdem", "pifpaf", "domino")
        self.modo_partida = "solo"  # "solo" | "multiplayer"
        self.botao_solo = pygame.Rect(0, 0, 190, 44)
        self.botao_multiplayer = pygame.Rect(0, 0, 190, 44)
        self.botao_criar_sala = pygame.Rect(0, 0, 360, 60)
        self.botao_entrar_sala = pygame.Rect(0, 0, 360, 60)

    def _iniciar_partida(self):
        if self.modo == "pifpaf":
            self.app.iniciar_partida_pifpaf(self.quantidade_bots)
        elif self.modo == "domino":
            self.app.iniciar_partida_domino(self.quantidade_bots)
        else:
            self.app.iniciar_partida(self.quantidade_bots)

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_voltar.collidepoint(evento.pos):
                self.app.ir_para_escolha_modo()
                return
            if self.suporta_multiplayer:
                if self.botao_solo.collidepoint(evento.pos):
                    self.modo_partida = "solo"
                    return
                elif self.botao_multiplayer.collidepoint(evento.pos):
                    self.modo_partida = "multiplayer"
                    return
            if self.modo_partida == "multiplayer":
                if self.botao_criar_sala.collidepoint(evento.pos):
                    self.app.ir_para_multiplayer_criar(self.modo)
                elif self.botao_entrar_sala.collidepoint(evento.pos):
                    self.app.ir_para_multiplayer_entrar()
                return
            if self.botao_menos.collidepoint(evento.pos):
                self.quantidade_bots = max(self.min_bots, self.quantidade_bots - 1)
            elif self.botao_mais.collidepoint(evento.pos):
                self.quantidade_bots = min(self.max_bots, self.quantidade_bots + 1)
            elif self.botao_iniciar.collidepoint(evento.pos):
                self._iniciar_partida()
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_RETURN and self.modo_partida == "solo":
                self._iniciar_partida()
            elif evento.key == pygame.K_ESCAPE:
                self.app.ir_para_escolha_modo()

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        titulo = self.TITULOS_MODO.get(self.modo, "PARTIDA")
        desenhar_texto(tela, f"CONFIGURAÇÃO DA MESA — {titulo}", largura // 2, altura // 6,
                        tamanho=26, cor=INK, negrito=True, centralizado=True, familia="display")

        altura_painel = 340 + (66 if self.suporta_multiplayer else 0)
        painel = pygame.Rect(0, 0, 460, altura_painel)
        painel.center = (largura // 2, altura // 2 + 10)
        desenhar_painel(tela, painel, radius=0)

        y_bots = painel.y + 34

        if self.suporta_multiplayer:
            self.botao_solo.midright = (painel.centerx - 6, y_bots)
            self.botao_multiplayer.midleft = (painel.centerx + 6, y_bots)
            desenhar_botao(tela, self.botao_solo, "Solo vs Bots",
                            hover=self.botao_solo.collidepoint(mouse_pos),
                            tamanho_fonte=13, cor=YELLOW if self.modo_partida == "solo" else PANEL)
            desenhar_botao(tela, self.botao_multiplayer, "Multiplayer Local",
                            hover=self.botao_multiplayer.collidepoint(mouse_pos),
                            tamanho_fonte=13, cor=YELLOW if self.modo_partida == "multiplayer" else PANEL)
            y_bots += 66

        if self.modo_partida == "multiplayer":
            desenhar_texto(tela, "Jogue com outras pessoas na mesma rede Wi-Fi/LAN",
                            painel.centerx, y_bots + 6, tamanho=13, cor=TEXT_MUTED, centralizado=True)

            self.botao_criar_sala.center = (painel.centerx, y_bots + 66)
            desenhar_botao(tela, self.botao_criar_sala, "Criar Sala (ser anfitrião)",
                            hover=self.botao_criar_sala.collidepoint(mouse_pos), tamanho_fonte=18, cor=YELLOW)

            self.botao_entrar_sala.center = (painel.centerx, y_bots + 140)
            desenhar_botao(tela, self.botao_entrar_sala, "Entrar em Sala",
                            hover=self.botao_entrar_sala.collidepoint(mouse_pos), tamanho_fonte=18, cor=PANEL)

            self.botao_voltar.topleft = (30, 30)
            desenhar_botao(tela, self.botao_voltar, "< Voltar",
                            hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)
            return

        desenhar_texto(tela, "Quantidade de Bots na mesa", painel.centerx, y_bots,
                        tamanho=16, cor=INK, negrito=True, centralizado=True)

        self.botao_menos.center = (painel.centerx - 100, y_bots + 46)
        self.botao_mais.center = (painel.centerx + 100, y_bots + 46)

        desenhar_botao(tela, self.botao_menos, "-", hover=self.botao_menos.collidepoint(mouse_pos),
                        tamanho_fonte=26, cor=PANEL)
        desenhar_botao(tela, self.botao_mais, "+", hover=self.botao_mais.collidepoint(mouse_pos),
                        tamanho_fonte=26, cor=PANEL)
        desenhar_texto(tela, str(self.quantidade_bots), painel.centerx, y_bots + 46,
                        tamanho=38, cor=INK, negrito=True, centralizado=True, familia="mono")
        desenhar_texto(tela, f"Mesa final: você + {self.quantidade_bots} bot(s) = {self.quantidade_bots + 1} jogadores",
                        painel.centerx, y_bots + 92, tamanho=13, cor=TEXT_MUTED, centralizado=True)

        # ---- Preview do "baralho" (carta ou peça de dominó) ----
        y_deck = y_bots + 140
        if self.modo == "domino":
            desenhar_texto(tela, "Jogo duplo-seis (28 peças)", painel.centerx, y_deck, tamanho=16,
                            cor=INK, negrito=True, centralizado=True)
            largura_peca, altura_peca = 50, 90
            desenhar_peca(tela, painel.centerx - largura_peca // 2, y_deck + 20,
                          largura_peca, altura_peca, 6, 6, vertical=True)
        else:
            desenhar_texto(tela, "Baralho", painel.centerx, y_deck, tamanho=16,
                            cor=INK, negrito=True, centralizado=True)
            largura_carta, altura_carta = 64, 90
            desenhar_carta(tela, painel.centerx - largura_carta // 2, y_deck + 20,
                            largura_carta, altura_carta, carta=self.carta_preview)
            rotulo_skin = ROTULOS_BARALHO_SKIN[self.app.settings.baralho_skin].upper()
            desenhar_badge(tela, painel.centerx, y_deck + 20 + altura_carta + 22, rotulo_skin,
                            MINT, cor_texto=SOMBRA, tamanho_fonte=11)

        self.botao_iniciar.center = (largura // 2, painel.bottom + 56)
        desenhar_botao(tela, self.botao_iniciar, "Iniciar Partida",
                        hover=self.botao_iniciar.collidepoint(mouse_pos), tamanho_fonte=22)
        desenhar_kbd(tela, self.botao_iniciar.right - 16, self.botao_iniciar.centery, "Enter", ancorar="midright")

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)


class SettingsScreen:
    """Tela de Ajustes: configurações básicas da sessão (não afetam uma
    partida em andamento, valem para a próxima partida iniciada)."""

    def __init__(self, app):
        self.app = app
        self.botao_voltar = pygame.Rect(0, 0, 150, 48)

        self.botao_tela_cheia = pygame.Rect(0, 0, 190, 48)
        self.botao_velocidade = pygame.Rect(0, 0, 190, 48)
        self.botao_atalhos = pygame.Rect(0, 0, 190, 48)
        self.botao_fichas_menos = pygame.Rect(0, 0, 48, 48)
        self.botao_fichas_mais = pygame.Rect(0, 0, 48, 48)
        self.botao_joker_pifpaf = pygame.Rect(0, 0, 190, 48)
        self.botao_baralho_skin = pygame.Rect(0, 0, 190, 48)
        self.botao_selecao_pecas = pygame.Rect(0, 0, 190, 48)

    def tratar_evento(self, evento):
        settings = self.app.settings
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_voltar.collidepoint(evento.pos):
                self.app.ir_para_menu()
            elif self.botao_tela_cheia.collidepoint(evento.pos):
                self.app.alternar_tela_cheia()
            elif self.botao_velocidade.collidepoint(evento.pos):
                settings.ciclar_velocidade_bots()
            elif self.botao_atalhos.collidepoint(evento.pos):
                settings.alternar_atalhos()
            elif self.botao_fichas_menos.collidepoint(evento.pos):
                settings.diminuir_fichas()
            elif self.botao_fichas_mais.collidepoint(evento.pos):
                settings.aumentar_fichas()
            elif self.botao_joker_pifpaf.collidepoint(evento.pos):
                settings.alternar_joker_pifpaf()
            elif self.botao_baralho_skin.collidepoint(evento.pos):
                settings.ciclar_baralho_skin()
            elif self.botao_selecao_pecas.collidepoint(evento.pos):
                settings.alternar_selecao_automatica_pecas()
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.app.ir_para_menu()

    def atualizar(self, dt):
        pass

    def _linha(self, tela, painel, y, rotulo):
        desenhar_texto(tela, rotulo, painel.x + 30, y, tamanho=16, cor=INK, negrito=True)

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()
        settings = self.app.settings

        desenhar_texto(tela, "AJUSTES", largura // 2, altura // 6,
                        tamanho=30, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, "Valem a partir da próxima partida iniciada",
                        largura // 2, altura // 6 + 34, tamanho=13, cor=TEXT_MUTED, centralizado=True)

        painel = pygame.Rect(0, 0, 480, 504)
        painel.center = (largura // 2, altura // 2 + 10)
        desenhar_painel(tela, painel, radius=0)

        espaco_linha = 68
        y = painel.y + 46

        # ---- Tela cheia ----
        self._linha(tela, painel, y, "Tela cheia")
        self.botao_tela_cheia.midright = (painel.right - 30, y + 2)
        texto_tela_cheia = "Ativada" if settings.tela_cheia else "Desativada"
        desenhar_botao(tela, self.botao_tela_cheia, texto_tela_cheia,
                        hover=self.botao_tela_cheia.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=MINT if settings.tela_cheia else PANEL)
        y += espaco_linha

        # ---- Velocidade dos bots ----
        self._linha(tela, painel, y, "Velocidade dos bots")
        self.botao_velocidade.midright = (painel.right - 30, y + 2)
        desenhar_botao(tela, self.botao_velocidade, ROTULOS_VELOCIDADE[settings.velocidade_bots],
                        hover=self.botao_velocidade.collidepoint(mouse_pos), tamanho_fonte=14, cor=PANEL)
        y += espaco_linha

        # ---- Fichas iniciais ----
        self._linha(tela, painel, y, "Fichas iniciais")
        self.botao_fichas_mais.midright = (painel.right - 30, y + 2)
        self.botao_fichas_menos.midright = (self.botao_fichas_mais.left - 12, y + 2)
        desenhar_botao(tela, self.botao_fichas_menos, "-",
                        hover=self.botao_fichas_menos.collidepoint(mouse_pos), tamanho_fonte=20, cor=PANEL)
        desenhar_botao(tela, self.botao_fichas_mais, "+",
                        hover=self.botao_fichas_mais.collidepoint(mouse_pos), tamanho_fonte=20, cor=PANEL)
        largura_num = obter_fonte(18, True, "mono").size(str(settings.fichas_iniciais))[0]
        desenhar_texto(tela, str(settings.fichas_iniciais),
                        self.botao_fichas_menos.left - 16 - largura_num, y - 8,
                        tamanho=18, cor=INK, negrito=True, familia="mono")
        y += espaco_linha

        # ---- Mostrar atalhos de teclado ----
        self._linha(tela, painel, y, "Atalhos de teclado")
        self.botao_atalhos.midright = (painel.right - 30, y + 2)
        texto_atalhos = "Mostrar" if settings.mostrar_atalhos else "Ocultar"
        desenhar_botao(tela, self.botao_atalhos, texto_atalhos,
                        hover=self.botao_atalhos.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=MINT if settings.mostrar_atalhos else PANEL)
        y += espaco_linha

        # ---- Joker no Pif Paf ----
        self._linha(tela, painel, y, "Joker no Pif Paf")
        self.botao_joker_pifpaf.midright = (painel.right - 30, y + 2)
        texto_joker = "Ativado" if settings.usar_joker_pifpaf else "Desativado"
        desenhar_botao(tela, self.botao_joker_pifpaf, texto_joker,
                        hover=self.botao_joker_pifpaf.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=MINT if settings.usar_joker_pifpaf else PANEL)
        y += espaco_linha

        # ---- Baralho (skin visual) ----
        self._linha(tela, painel, y, "Baralho")
        self.botao_baralho_skin.midright = (painel.right - 30, y + 2)
        desenhar_botao(tela, self.botao_baralho_skin, ROTULOS_BARALHO_SKIN[settings.baralho_skin],
                        hover=self.botao_baralho_skin.collidepoint(mouse_pos), tamanho_fonte=14, cor=PANEL)
        y += espaco_linha

        # ---- Seleção de peças no Dominó ----
        self._linha(tela, painel, y, "Seleção de peças (Dominó)")
        self.botao_selecao_pecas.midright = (painel.right - 30, y + 2)
        texto_selecao = "Automática" if settings.selecao_automatica_pecas else "Manual"
        desenhar_botao(tela, self.botao_selecao_pecas, texto_selecao,
                        hover=self.botao_selecao_pecas.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=MINT if settings.selecao_automatica_pecas else PANEL)

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)
