"""
domino_theme.py - Desenho das pedras de dominó, compartilhado entre
domino_screen.py (host/local) e mesa_remota_domino_screen.py (cliente).

Cada metade da peça mostra os pontos como bolinhas (padrão clássico de
dado/dominó), no mesmo estilo neobrutalista (borda grossa preta + sombra
sólida) do resto do jogo - ver ui_theme.py.
"""
import pygame

from ui_theme import INK, PANEL, BLUE, BG, YELLOW

# Posições relativas (0-1) das bolinhas dentro de cada metade, por valor.
PADRAO_PIPS = {
    0: [],
    1: [(0.5, 0.5)],
    2: [(0.28, 0.28), (0.72, 0.72)],
    3: [(0.28, 0.28), (0.5, 0.5), (0.72, 0.72)],
    4: [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)],
    5: [(0.28, 0.28), (0.72, 0.28), (0.5, 0.5), (0.28, 0.72), (0.72, 0.72)],
    6: [(0.28, 0.22), (0.72, 0.22), (0.28, 0.5), (0.72, 0.5), (0.28, 0.78), (0.72, 0.78)],
}


def _desenhar_pips(tela, valor, area):
    raio = max(2, int(min(area.width, area.height) * 0.13))
    for px, py in PADRAO_PIPS.get(valor, []):
        cx = area.x + int(area.width * px)
        cy = area.y + int(area.height * py)
        pygame.draw.circle(tela, INK, (cx, cy), raio)


def desenhar_peca(tela, x, y, largura, altura, peca, vertical=False, destaque=False):
    """Desenha uma peça com as duas metades viradas para cima. `vertical`
    empilha as metades uma sobre a outra em vez de lado a lado (útil pra
    caber peças verticais numa fileira apertada, se algum dia precisar)."""
    rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, INK, rect.move(2, 2), border_radius=6)
    pygame.draw.rect(tela, PANEL, rect, border_radius=6)
    cor_borda = YELLOW if destaque else INK
    pygame.draw.rect(tela, cor_borda, rect, width=3 if destaque else 2, border_radius=6)

    if vertical:
        pygame.draw.line(tela, INK, (rect.x + 3, rect.centery), (rect.right - 3, rect.centery), 2)
        _desenhar_pips(tela, peca.a, pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2))
        _desenhar_pips(tela, peca.b, pygame.Rect(rect.x, rect.centery, rect.width, rect.height // 2))
    else:
        pygame.draw.line(tela, INK, (rect.centerx, rect.y + 3), (rect.centerx, rect.bottom - 3), 2)
        _desenhar_pips(tela, peca.a, pygame.Rect(rect.x, rect.y, rect.width // 2, rect.height))
        _desenhar_pips(tela, peca.b, pygame.Rect(rect.centerx, rect.y, rect.width // 2, rect.height))

    return rect


def desenhar_peca_verso(tela, x, y, largura, altura):
    rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, INK, rect.move(2, 2), border_radius=6)
    pygame.draw.rect(tela, BLUE, rect, border_radius=6)
    cx, cy = rect.center
    s = min(largura, altura) * 0.18
    losango = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
    pygame.draw.polygon(tela, BG, losango)
    pygame.draw.rect(tela, INK, rect, width=2, border_radius=6)
    return rect
