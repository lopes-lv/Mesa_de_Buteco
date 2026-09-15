"""
ui_widgets.py - Widgets de UI pequenos e reutilizáveis (campo de texto),
usados tanto pelas telas de sala (multiplayer_screens.py) quanto pelo
widget de chat (chat_widget.py). Separado num módulo próprio só pra não
criar import circular entre os dois.
"""
import pygame
from ui_theme import PANEL, INK, TEXT_MUTED, desenhar_texto


class CampoTexto:
    """Campo de texto simples de uma linha: clique para focar, digita, backspace apaga."""

    def __init__(self, rect, placeholder="", max_len=24, maiusculas=False):
        self.rect = rect
        self.texto = ""
        self.placeholder = placeholder
        self.max_len = max_len
        self.maiusculas = maiusculas
        self.focado = False

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.focado = self.rect.collidepoint(evento.pos)
        elif evento.type == pygame.KEYDOWN and self.focado:
            if evento.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_TAB):
                pass
            elif evento.unicode and evento.unicode.isprintable() and len(self.texto) < self.max_len:
                ch = evento.unicode.upper() if self.maiusculas else evento.unicode
                self.texto += ch

    def desenhar(self, tela):
        pygame.draw.rect(tela, PANEL, self.rect, border_radius=10)
        cor_borda = INK if self.focado else TEXT_MUTED
        pygame.draw.rect(tela, cor_borda, self.rect, width=3 if self.focado else 2, border_radius=10)
        texto_exibir = self.texto if self.texto else self.placeholder
        cor_texto = INK if self.texto else TEXT_MUTED
        desenhar_texto(tela, texto_exibir, self.rect.x + 14, self.rect.centery - 9,
                        tamanho=16, cor=cor_texto, familia="mono")
