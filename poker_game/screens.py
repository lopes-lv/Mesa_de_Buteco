"""
screens.py - Telas de Menu Inicial e Configuração (pré-jogo).
A tela de Mesa/Gameplay fica em table_screen.py por ser mais extensa.
"""
import pygame
from ui_pixelart import (
    COR_FUNDO, COR_TEXTO, desenhar_texto, desenhar_botao, desenhar_painel
)


class MenuScreen:
    """Menu Inicial: seleção do modo de jogo."""

    def __init__(self, app):
        self.app = app
        self.botao_rect = pygame.Rect(0, 0, 360, 64)
        self.botao_sair = pygame.Rect(0, 0, 160, 46)

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_rect.collidepoint(evento.pos):
                self.app.ir_para_config()
            elif self.botao_sair.collidepoint(evento.pos):
                self.app.encerrar()

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(COR_FUNDO)
        desenhar_texto(tela, "TEXAS HOLD'EM", largura // 2, altura // 3 - 40,
                        tamanho=48, cor=(230, 200, 60), negrito=True, centralizado=True)
        desenhar_texto(tela, "PIXEL POKER", largura // 2, altura // 3 + 10,
                        tamanho=20, cor=COR_TEXTO, centralizado=True)

        self.botao_rect.center = (largura // 2, altura // 2 + 40)
        mouse_pos = pygame.mouse.get_pos()
        hover = self.botao_rect.collidepoint(mouse_pos)
        desenhar_botao(tela, self.botao_rect, "Texas Hold'em Solo", hover=hover, tamanho_fonte=22)

        self.botao_sair.center = (largura // 2, self.botao_rect.bottom + 60)
        hover_sair = self.botao_sair.collidepoint(mouse_pos)
        desenhar_botao(tela, self.botao_sair, "Sair", hover=hover_sair, tamanho_fonte=18)

        desenhar_texto(tela, "Solo vs Bots  |  Redimensione a janela livremente",
                        largura // 2, altura - 40, tamanho=14, cor=(150, 150, 150), centralizado=True)


class ConfigScreen:
    """Tela de Configuração: escolha da quantidade de bots na mesa."""

    def __init__(self, app):
        self.app = app
        self.quantidade_bots = 3
        self.min_bots = 1
        self.max_bots = 7
        self.botao_menos = pygame.Rect(0, 0, 50, 50)
        self.botao_mais = pygame.Rect(0, 0, 50, 50)
        self.botao_iniciar = pygame.Rect(0, 0, 280, 60)
        self.botao_voltar = pygame.Rect(0, 0, 140, 44)

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

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(COR_FUNDO)
        desenhar_texto(tela, "CONFIGURAÇÃO DA MESA", largura // 2, altura // 5,
                        tamanho=32, cor=(230, 200, 60), negrito=True, centralizado=True)

        painel = pygame.Rect(0, 0, 420, 200)
        painel.center = (largura // 2, altura // 2 - 20)
        desenhar_painel(tela, painel)

        desenhar_texto(tela, "Quantidade de Bots na mesa", painel.centerx, painel.y + 30,
                        tamanho=18, cor=COR_TEXTO, centralizado=True)

        self.botao_menos.center = (painel.centerx - 90, painel.centery + 10)
        self.botao_mais.center = (painel.centerx + 90, painel.centery + 10)
        mouse_pos = pygame.mouse.get_pos()

        desenhar_botao(tela, self.botao_menos, "-", hover=self.botao_menos.collidepoint(mouse_pos), tamanho_fonte=26)
        desenhar_botao(tela, self.botao_mais, "+", hover=self.botao_mais.collidepoint(mouse_pos), tamanho_fonte=26)
        desenhar_texto(tela, str(self.quantidade_bots), painel.centerx, painel.centery + 10,
                        tamanho=36, cor=(230, 200, 60), negrito=True, centralizado=True)
        desenhar_texto(tela, f"Mesa final: você + {self.quantidade_bots} bot(s) = {self.quantidade_bots + 1} jogadores",
                        painel.centerx, painel.y + painel.height - 30, tamanho=14, cor=(180, 180, 180),
                        centralizado=True)

        self.botao_iniciar.center = (largura // 2, painel.bottom + 60)
        desenhar_botao(tela, self.botao_iniciar, "Iniciar Partida",
                        hover=self.botao_iniciar.collidepoint(mouse_pos), tamanho_fonte=22)

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=16)
