"""
domino_theme.py - Desenho das pedras de dominó, compartilhado entre
domino_screen.py (host/local) e mesa_remota_domino_screen.py (cliente).

Cada metade da peça mostra os pontos como bolinhas (padrão clássico de
dado/dominó), no mesmo estilo Pixel Art Retrô (cantos retos, borda grossa,
sombra sólida) do resto do jogo - ver ui_theme.py. A peça em si é "marfim",
igual à carta: clara mesmo com o resto da UI escuro.
"""
import pygame

from core.ui_theme import SOMBRA, CARTA_FACE, CARTA_INK, BLUE, YELLOW

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
        pygame.draw.circle(tela, CARTA_INK, (cx, cy), raio)


def desenhar_peca(tela, x, y, largura, altura, valor_a, valor_b, vertical=False, destaque=False):
    """Desenha uma peça com as duas metades viradas para cima. Recebe os
    dois valores já orientados (`valor_a` fica na metade esquerda/superior,
    `valor_b` na direita/inferior) em vez de um objeto `Peca` - a peça
    normalizada (a<=b) não sabe pra qual lado da mesa ela foi virada ao ser
    jogada, então quem desenha precisa mandar a orientação visual de
    verdade (ver `PecaNaMesa` em domino_logic.py) pros pontos baterem com a
    peça vizinha na cadeia. `vertical` empilha as metades uma sobre a outra
    em vez de lado a lado (usado na mão do jogador)."""
    rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, SOMBRA, rect.move(2, 2))
    pygame.draw.rect(tela, CARTA_FACE, rect)
    cor_borda = YELLOW if destaque else CARTA_INK
    pygame.draw.rect(tela, cor_borda, rect, width=3 if destaque else 2)

    if vertical:
        pygame.draw.line(tela, CARTA_INK, (rect.x + 3, rect.centery), (rect.right - 3, rect.centery), 2)
        _desenhar_pips(tela, valor_a, pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2))
        _desenhar_pips(tela, valor_b, pygame.Rect(rect.x, rect.centery, rect.width, rect.height // 2))
    else:
        pygame.draw.line(tela, CARTA_INK, (rect.centerx, rect.y + 3), (rect.centerx, rect.bottom - 3), 2)
        _desenhar_pips(tela, valor_a, pygame.Rect(rect.x, rect.y, rect.width // 2, rect.height))
        _desenhar_pips(tela, valor_b, pygame.Rect(rect.centerx, rect.y, rect.width // 2, rect.height))

    return rect


def desenhar_peca_verso(tela, x, y, largura, altura, destaque=False):
    """Peça virada pra baixo (verso) - usada na pilha de escolha do início de
    mão (ver domino_screen.py/mesa_remota_domino_screen.py). `destaque`
    espelha o hover amarelo de `desenhar_peca`."""
    rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, SOMBRA, rect.move(2, 2))
    pygame.draw.rect(tela, BLUE, rect)
    cx, cy = rect.center
    s = min(largura, altura) * 0.18
    losango = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
    pygame.draw.polygon(tela, (130, 160, 232), losango)
    cor_borda = YELLOW if destaque else CARTA_INK
    pygame.draw.rect(tela, cor_borda, rect, width=3 if destaque else 2)
    return rect
