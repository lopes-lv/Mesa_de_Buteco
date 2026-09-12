"""
screens.py - Telas de Menu Inicial e Configuração (pré-jogo).
A tela de Mesa/Gameplay fica em table_screen.py por ser mais extensa.
"""
import pygame
from ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL, MINT, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_carta,
    desenhar_kbd, desenhar_badge, obter_fonte,
)
from deck import Card


class MenuScreen:
    """Menu Inicial: título + ação principal."""

    def __init__(self, app):
        self.app = app
        self.botao_jogar = pygame.Rect(0, 0, 320, 68)
        self.botao_sair = pygame.Rect(0, 0, 180, 68)

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_jogar.collidepoint(evento.pos):
                self.app.ir_para_config()
            elif self.botao_sair.collidepoint(evento.pos):
                self.app.encerrar()
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_RETURN:
                self.app.ir_para_config()

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
        desenhar_painel(tela, selo, cor=YELLOW, radius=20, deslocamento_sombra=(5, 5))
        desenhar_texto(tela, "♠", selo.centerx, selo.centery - 2, tamanho=40,
                        cor=INK, centralizado=True)

        titulo_x = inicio_x + selo_w + gap
        titulo_rect = titulo_surf.get_rect(midleft=(titulo_x, centro_y - 14))
        tela.blit(titulo_surf, titulo_rect)
        desenhar_texto(tela, "SOLO VS BOTS  •  MESA DE 8 JOGADORES",
                        titulo_rect.left, titulo_rect.bottom + 12, tamanho=13, cor=TEXT_MUTED,
                        familia="mono")

        # ---- Ações principais ----
        self.botao_jogar.center = (largura // 2 - 100, altura // 2 + 70)
        self.botao_sair.center = (largura // 2 + 140, altura // 2 + 70)

        hover_jogar = self.botao_jogar.collidepoint(mouse_pos)
        hover_sair = self.botao_sair.collidepoint(mouse_pos)

        desenhar_botao(tela, self.botao_jogar, "Jogar", hover=hover_jogar,
                        tamanho_fonte=22, cor=YELLOW)
        desenhar_kbd(tela, self.botao_jogar.right - 16, self.botao_jogar.centery, "Enter", ancorar="midright")

        desenhar_botao(tela, self.botao_sair, "Sair", hover=hover_sair,
                        tamanho_fonte=22, cor=CORAL, cor_texto=PANEL)
        desenhar_kbd(tela, self.botao_sair.right - 16, self.botao_sair.centery, "Esc", ancorar="midright")

        desenhar_texto(tela, "Redimensione a janela livremente",
                        largura // 2, altura - 36, tamanho=13, cor=TEXT_MUTED, centralizado=True)


class ConfigScreen:
    """Tela de Configuração: escolha da quantidade de bots na mesa."""

    def __init__(self, app):
        self.app = app
        self.quantidade_bots = 3
        self.min_bots = 1
        self.max_bots = 7
        self.botao_menos = pygame.Rect(0, 0, 52, 52)
        self.botao_mais = pygame.Rect(0, 0, 52, 52)
        self.botao_iniciar = pygame.Rect(0, 0, 360, 64)
        self.botao_voltar = pygame.Rect(0, 0, 150, 48)
        self.carta_preview = Card(14, "espadas")  # Ás de Espadas

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_menos.collidepoint(evento.pos):
                self.quantidade_bots = max(self.min_bots, self.quantidade_bots - 1)
            elif self.botao_mais.collidepoint(evento.pos):
                self.quantidade_bots = min(self.max_bots, self.quantidade_bots + 1)
            elif self.botao_iniciar.collidepoint(evento.pos):
                self.app.iniciar_partida(self.quantidade_bots)
            elif self.botao_voltar.collidepoint(evento.pos):
                self.app.ir_para_menu()
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_RETURN:
                self.app.iniciar_partida(self.quantidade_bots)

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        desenhar_texto(tela, "CONFIGURAÇÃO DA MESA", largura // 2, altura // 6,
                        tamanho=30, cor=INK, negrito=True, centralizado=True, familia="display")

        painel = pygame.Rect(0, 0, 460, 340)
        painel.center = (largura // 2, altura // 2 + 10)
        desenhar_painel(tela, painel, radius=24)

        y_bots = painel.y + 34
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

        # ---- Preview de carta (deck único, estilo neobrutalista) ----
        y_deck = y_bots + 140
        desenhar_texto(tela, "Baralho", painel.centerx, y_deck, tamanho=16,
                        cor=INK, negrito=True, centralizado=True)
        largura_carta, altura_carta = 64, 90
        desenhar_carta(tela, painel.centerx - largura_carta // 2, y_deck + 20,
                        largura_carta, altura_carta, carta=self.carta_preview)
        desenhar_badge(tela, painel.centerx, y_deck + 20 + altura_carta + 22, "PADRÃO",
                        MINT, cor_texto=INK, tamanho_fonte=11)

        self.botao_iniciar.center = (largura // 2, painel.bottom + 56)
        desenhar_botao(tela, self.botao_iniciar, "Iniciar Partida",
                        hover=self.botao_iniciar.collidepoint(mouse_pos), tamanho_fonte=22)
        desenhar_kbd(tela, self.botao_iniciar.right - 16, self.botao_iniciar.centery, "Enter", ancorar="midright")

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)
