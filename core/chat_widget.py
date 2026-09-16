"""
chat_widget.py - Aba de chat reutilizável para as telas de multiplayer local
(lobby e mesa, tanto Hold'em quanto Pif Paf).

Fica encostada no canto esquerdo da tela: uma aba fechada por padrão (não
atrapalha o resto da UI) que expande num painel com histórico + campo de
texto ao ser clicada. Quem instancia passa só um `enviar_callback(texto)` -
o widget não sabe nada de rede, cada tela decide o que fazer (mandar pro
host, ou já retransmitir pra todo mundo, no caso do próprio host).
"""
from collections import deque

import pygame
from .ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL,
    desenhar_texto, desenhar_painel,
)
from .ui_widgets import CampoTexto

MAX_MENSAGENS = 60
LARGURA_PAINEL = 280
PROPORCAO_ALTURA = 0.6


class ChatWidget:
    def __init__(self, enviar_callback):
        self.enviar_callback = enviar_callback
        self.expandido = False
        self.tem_novas = False
        self.mensagens = deque(maxlen=MAX_MENSAGENS)

        self.aba_rect = pygame.Rect(0, 0, 46, 120)
        self.painel_rect = pygame.Rect(0, 0, LARGURA_PAINEL, 360)
        self.botao_fechar = pygame.Rect(0, 0, 28, 28)
        self.campo = CampoTexto(pygame.Rect(0, 0, 10, 10), placeholder="Digite e pressione Enter...",
                                 max_len=140)

    def adicionar_mensagem(self, remetente, texto):
        self.mensagens.append((remetente, texto))
        if not self.expandido:
            self.tem_novas = True

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        """Retorna True se o evento foi consumido pelo chat (não deve ser
        repassado pro resto da tela)."""
        if not self.expandido:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 \
                    and self.aba_rect.collidepoint(evento.pos):
                self.expandido = True
                self.tem_novas = False
                self.campo.focado = True
                return True
            return False

        consumido = False
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_fechar.collidepoint(evento.pos):
                self.expandido = False
                return True
            if self.painel_rect.collidepoint(evento.pos):
                consumido = True

        self.campo.tratar_evento(evento)

        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN and self.campo.focado:
            texto = self.campo.texto.strip()
            if texto:
                self.enviar_callback(texto)
                self.campo.texto = ""
            consumido = True

        return consumido

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela, largura, altura):
        if not self.expandido:
            self._desenhar_aba(tela, altura)
            return

        self.painel_rect.height = int(altura * PROPORCAO_ALTURA)
        self.painel_rect.width = min(LARGURA_PAINEL, largura - 20)
        self.painel_rect.topleft = (0, (altura - self.painel_rect.height) // 2)
        desenhar_painel(tela, self.painel_rect, cor=PANEL, radius=18, deslocamento_sombra=(5, 5))

        desenhar_texto(tela, "CHAT DA SALA", self.painel_rect.x + 18, self.painel_rect.y + 16,
                        tamanho=14, cor=INK, negrito=True)

        self.botao_fechar.topright = (self.painel_rect.right - 14, self.painel_rect.y + 12)
        pygame.draw.rect(tela, CORAL, self.botao_fechar, border_radius=8)
        pygame.draw.rect(tela, INK, self.botao_fechar, width=2, border_radius=8)
        desenhar_texto(tela, "x", self.botao_fechar.centerx, self.botao_fechar.centery - 9,
                        tamanho=14, cor=PANEL, negrito=True, centralizado=True)

        area_msgs = pygame.Rect(self.painel_rect.x + 16, self.painel_rect.y + 46,
                                 self.painel_rect.width - 32, self.painel_rect.height - 106)
        pygame.draw.rect(tela, BG, area_msgs, border_radius=10)
        pygame.draw.rect(tela, INK, area_msgs, width=2, border_radius=10)

        largura_util = area_msgs.width - 20
        y = area_msgs.bottom - 22
        for remetente, texto in reversed(self.mensagens):
            if y < area_msgs.y + 10:
                break
            for linha in reversed(self._quebrar_linha(f"{remetente}: {texto}", largura_util)):
                if y < area_msgs.y + 10:
                    break
                desenhar_texto(tela, linha, area_msgs.x + 10, y, tamanho=12, cor=INK)
                y -= 18

        self.campo.rect = pygame.Rect(self.painel_rect.x + 16, self.painel_rect.bottom - 44,
                                       self.painel_rect.width - 32, 34)
        self.campo.desenhar(tela)

    def _desenhar_aba(self, tela, altura):
        self.aba_rect.midleft = (0, altura // 2)
        cor = YELLOW if self.tem_novas else PANEL
        pygame.draw.rect(tela, INK, self.aba_rect.move(3, 3), border_radius=12)
        pygame.draw.rect(tela, cor, self.aba_rect, border_radius=12)
        pygame.draw.rect(tela, INK, self.aba_rect, width=3, border_radius=12)
        desenhar_texto(tela, "CHAT", self.aba_rect.centerx, self.aba_rect.centery - 8,
                        tamanho=13, cor=INK, negrito=True, centralizado=True, familia="mono")
        if self.tem_novas:
            desenhar_texto(tela, "●", self.aba_rect.centerx, self.aba_rect.centery + 16,
                            tamanho=16, cor=CORAL, centralizado=True)

    @staticmethod
    def _quebrar_linha(texto, largura_max_px, tamanho_fonte=12):
        from ui_theme import obter_fonte
        fonte = obter_fonte(tamanho_fonte, False, "body")
        palavras = texto.split(" ")
        linhas = []
        atual = ""
        for palavra in palavras:
            candidato = f"{atual} {palavra}".strip()
            if fonte.size(candidato)[0] <= largura_max_px or not atual:
                atual = candidato
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas or [""]
