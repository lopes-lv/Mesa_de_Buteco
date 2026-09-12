"""
ui_theme.py - Biblioteca de desenho do estilo visual "Neobrutalismo Suave /
Dashboard Analítico" (ver design/01_neobrutalismo_suave/GUIA_TECNICO_PYGAME.md).

Tudo é desenhado via pygame.draw / pygame.Surface, sem imagens externas:
bordas grossas quase-pretas, sombra sólida deslocada (sem blur) e paleta
clara com acentos saturados.
"""
import math
import pygame

# ---------- Paleta (ver GUIA_TECNICO_PYGAME.md, secao 1) ----------
BG = (242, 239, 231)
PANEL = (255, 255, 255)
FELT = (47, 107, 79)
FELT_DARK = (36, 87, 64)
INK = (27, 27, 27)
TEXT_MUTED = (92, 88, 80)
YELLOW = (255, 201, 60)
CORAL = (255, 107, 87)
BLUE = (76, 134, 240)
MINT = (61, 217, 164)
PURPLE = (167, 139, 250)
LOCKED = (216, 212, 200)
RED_SUIT = (217, 59, 59)

# Compatibilidade com nomes antigos usados em outros módulos.
COR_FUNDO = BG
COR_TEXTO = INK

CHIP_CORES = [YELLOW, BLUE, MINT, CORAL, PURPLE]

# ---------- Fontes ----------
# Sem arquivos .ttf baixados: usamos fontes de sistema equivalentes em
# limpeza/legibilidade às sugeridas no guia (Space Grotesk/Inter/JetBrains
# Mono). Trocar por .ttf reais em assets/fonts/ no futuro é trivial: basta
# apontar pygame.font.Font(caminho, tamanho) dentro de _criar_fonte().
FAMILIAS = {
    "display": ["Segoe UI Semibold", "Segoe UI", "Verdana", "Arial"],
    "body": ["Segoe UI", "Verdana", "Arial"],
    "mono": ["Consolas", "Courier New", "DejaVu Sans Mono"],
}

_fonte_cache = {}


def obter_fonte(tamanho, negrito=False, familia="body"):
    chave = (tamanho, negrito, familia)
    if chave not in _fonte_cache:
        candidatos = FAMILIAS.get(familia, FAMILIAS["body"])
        fonte = None
        for nome in candidatos:
            try:
                fonte = pygame.font.SysFont(nome, tamanho, bold=negrito)
                break
            except Exception:
                continue
        if fonte is None:
            fonte = pygame.font.Font(None, tamanho)
        _fonte_cache[chave] = fonte
    return _fonte_cache[chave]


def desenhar_texto(tela, texto, x, y, tamanho=18, cor=INK, negrito=False,
                    centralizado=False, familia="body"):
    fonte = obter_fonte(tamanho, negrito, familia)
    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)
    return rect


# ---------- Primitivas: retângulos com borda e sombra sólida ----------
def retangulo_borda(tela, rect, cor_fundo, cor_borda=INK, largura_borda=3, radius=16):
    pygame.draw.rect(tela, cor_fundo, rect, border_radius=radius)
    if largura_borda > 0:
        pygame.draw.rect(tela, cor_borda, rect, width=largura_borda, border_radius=radius)


def desenhar_painel(tela, rect, cor=PANEL, cor_borda=INK, radius=24, sombra=True,
                     largura_borda=3, deslocamento_sombra=(6, 6)):
    """Painel neobrutalista: preenchimento + borda grossa + sombra sólida deslocada."""
    if sombra:
        pygame.draw.rect(tela, INK, rect.move(*deslocamento_sombra), border_radius=radius)
    retangulo_borda(tela, rect, cor, cor_borda, largura_borda, radius)


def desenhar_botao(tela, rect, texto, hover=False, ativo=True, tamanho_fonte=18,
                    cor=YELLOW, cor_texto=INK, radius=14, largura_borda=3):
    """Botão neobrutalista. Ao passar o mouse, 'levanta' (sombra maior, corpo
    deslocado); a área de clique (rect original) não muda de tamanho/posição."""
    if not ativo:
        desenho_rect = rect
        sombra_offset = (3, 3)
        fundo = LOCKED
        cor_txt = TEXT_MUTED
    elif hover:
        desenho_rect = rect.move(-2, -2)
        sombra_offset = (7, 7)
        fundo = cor
        cor_txt = cor_texto
    else:
        desenho_rect = rect
        sombra_offset = (5, 5)
        fundo = cor
        cor_txt = cor_texto

    pygame.draw.rect(tela, INK, desenho_rect.move(*sombra_offset), border_radius=radius)
    retangulo_borda(tela, desenho_rect, fundo, INK, largura_borda, radius)
    desenhar_texto(tela, texto, desenho_rect.centerx, desenho_rect.centery,
                    tamanho=tamanho_fonte, cor=cor_txt, negrito=True,
                    centralizado=True, familia="display")
    return rect


def desenhar_kbd(tela, x, y, texto, ancorar="center"):
    """Selo pequeno estilo 'atalho de teclado' ([Enter], [Esc], [F]...)."""
    fonte = obter_fonte(12, True, "mono")
    superficie = fonte.render(texto, True, BG)
    pad_x, pad_y = 9, 4
    rect = pygame.Rect(0, 0, superficie.get_width() + pad_x * 2, superficie.get_height() + pad_y * 2)
    setattr(rect, ancorar, (x, y))
    pygame.draw.rect(tela, INK, rect, border_radius=rect.height // 2)
    tela.blit(superficie, superficie.get_rect(center=rect.center))
    return rect


def desenhar_badge(tela, x, y, texto, cor_fundo, cor_texto=INK, tamanho_fonte=12,
                    ancorar="center", borda=None, familia="body"):
    """Pill genérico (status de bot, marcador SB/BB, tags 'ATIVO'/'EM BREVE')."""
    fonte = obter_fonte(tamanho_fonte, True, familia)
    superficie = fonte.render(texto, True, cor_texto)
    pad_x, pad_y = 10, 5
    rect = pygame.Rect(0, 0, superficie.get_width() + pad_x * 2, superficie.get_height() + pad_y * 2)
    setattr(rect, ancorar, (x, y))
    pygame.draw.rect(tela, cor_fundo, rect, border_radius=rect.height // 2)
    if borda:
        pygame.draw.rect(tela, borda, rect, width=2, border_radius=rect.height // 2)
    tela.blit(superficie, superficie.get_rect(center=rect.center))
    return rect


def desenhar_avatar(tela, cx, cy, raio, cor_fundo, iniciais, cor_borda=INK,
                     largura_borda=3, sombra=(3, 3)):
    if sombra:
        pygame.draw.circle(tela, INK, (cx + sombra[0], cy + sombra[1]), raio)
    pygame.draw.circle(tela, cor_fundo, (cx, cy), raio)
    pygame.draw.circle(tela, cor_borda, (cx, cy), raio, largura_borda)
    desenhar_texto(tela, iniciais, cx, cy, tamanho=max(12, int(raio * 0.62)),
                    cor=BG, negrito=True, centralizado=True, familia="display")


# ---------- Cartas ----------
def _desenhar_naipe_simbolo(tela, simbolo, cx, cy, tamanho, cor):
    if simbolo == "H":  # copas
        r = tamanho // 3
        pygame.draw.circle(tela, cor, (cx - r // 2, cy - r // 3), r)
        pygame.draw.circle(tela, cor, (cx + r // 2, cy - r // 3), r)
        pygame.draw.polygon(tela, cor, [(cx - r, cy), (cx + r, cy), (cx, cy + r)])
    elif simbolo == "D":  # ouros
        pygame.draw.polygon(tela, cor, [
            (cx, cy - tamanho // 2), (cx + tamanho // 2, cy),
            (cx, cy + tamanho // 2), (cx - tamanho // 2, cy)
        ])
    elif simbolo == "C":  # paus
        r = tamanho // 3
        pygame.draw.circle(tela, cor, (cx, cy - r), r)
        pygame.draw.circle(tela, cor, (cx - r, cy + r // 3), r)
        pygame.draw.circle(tela, cor, (cx + r, cy + r // 3), r)
        pygame.draw.rect(tela, cor, (cx - 2, cy, 4, tamanho // 2))
    else:  # espadas
        pygame.draw.polygon(tela, cor, [
            (cx, cy - tamanho // 2), (cx + tamanho // 2, cy + tamanho // 4),
            (cx - tamanho // 2, cy + tamanho // 4)
        ])
        pygame.draw.rect(tela, cor, (cx - 2, cy + tamanho // 4, 4, tamanho // 3))


def desenhar_carta(tela, x, y, largura, altura, carta=None, virada_para_baixo=False, destaque=False):
    """Carta neobrutalista: face marfim, borda grossa preta, sombra sólida
    deslocada. `radius`/`borda` seguem a "tier" da carta (bot/comunitária/mão),
    conforme a tabela do GUIA_TECNICO (seção 3)."""
    rect = pygame.Rect(x, y, largura, altura)
    if largura <= 50:
        radius, borda, sombra = 8, 2, (2, 2)
    elif largura <= 80:
        radius, borda, sombra = 10, 3, (3, 3)
    else:
        radius, borda, sombra = 14, 4, (5, 5)

    pygame.draw.rect(tela, INK, rect.move(*sombra), border_radius=radius)

    if virada_para_baixo or carta is None:
        pygame.draw.rect(tela, BLUE, rect, border_radius=radius)
        pygame.draw.rect(tela, INK, rect, width=borda, border_radius=radius)
        cx, cy = rect.center
        s = min(largura, altura) * 0.22
        losango = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
        pygame.draw.polygon(tela, BG, losango)
        pygame.draw.polygon(tela, INK, losango, width=2)
        return rect

    pygame.draw.rect(tela, PANEL, rect, border_radius=radius)
    cor_borda_final = YELLOW if destaque else INK
    largura_borda_final = borda + (2 if destaque else 0)
    pygame.draw.rect(tela, cor_borda_final, rect, width=largura_borda_final, border_radius=radius)

    vermelho = carta.naipe in ("copas", "ouros")
    cor_texto = RED_SUIT if vermelho else INK
    tam_rank = max(11, int(largura * 0.24))
    tam_naipe = max(14, int(largura * 0.36))
    pad = max(3, int(largura * 0.09))

    desenhar_texto(tela, carta.texto, x + pad, y + pad - 2, tamanho=tam_rank,
                    cor=cor_texto, negrito=True, familia="mono")
    _desenhar_naipe_simbolo(tela, carta.simbolo_naipe, rect.centerx, rect.centery, tam_naipe, cor_texto)

    fonte_rank = obter_fonte(tam_rank, True, "mono")
    rank_surf = fonte_rank.render(carta.texto, True, cor_texto)
    rank_rot = pygame.transform.rotate(rank_surf, 180)
    tela.blit(rank_rot, (x + largura - pad - rank_rot.get_width(),
                          y + altura - pad - rank_rot.get_height() + 2))

    return rect


# ---------- Fichas ----------
def desenhar_ficha(tela, cx, cy, raio, indice=0):
    cor = CHIP_CORES[indice % len(CHIP_CORES)]
    pygame.draw.circle(tela, INK, (cx + 2, cy + 2), raio)
    pygame.draw.circle(tela, cor, (cx, cy), raio)
    pygame.draw.circle(tela, INK, (cx, cy), raio, 2)
    pygame.draw.circle(tela, BG, (cx, cy), max(1, int(raio * 0.55)), 2)


def desenhar_pilha_fichas(tela, x, y, valor, raio=10):
    n_fichas = min(5, max(1, valor // 50 + 1))
    for i in range(n_fichas):
        desenhar_ficha(tela, x, y - i * (raio // 2), raio, i)
    desenhar_texto(tela, str(valor), x + raio + 10, y - n_fichas * (raio // 2) // 2,
                    tamanho=15, cor=INK, negrito=True, familia="mono")


# ---------- Mesa ----------
def desenhar_mesa(tela, rect):
    """Mesa retangular arredondada (feltro), com leve bisel e sombra sólida
    deslocada -- substitui a mesa oval do estilo pixel art anterior."""
    radius = max(16, min(44, min(rect.width, rect.height) // 7))
    pygame.draw.rect(tela, INK, rect.move(8, 8), border_radius=radius)
    pygame.draw.rect(tela, FELT_DARK, rect, border_radius=radius)
    interno = rect.inflate(-20, -20)
    pygame.draw.rect(tela, FELT, interno, border_radius=max(6, radius - 10))
    pygame.draw.rect(tela, INK, rect, width=5, border_radius=radius)


def desenhar_glow_de_vez(tela, x, y, largura_carta, altura_carta, tempo):
    """Anel pulsante (mint) ao redor de quem está com a vez de agir."""
    pulso = (math.sin(tempo * 4.0) + 1) / 2
    raio_x = largura_carta + 34 + int(pulso * 6)
    raio_y = altura_carta // 2 + 34 + int(pulso * 6)
    alpha = 120 + int(pulso * 100)
    superficie = pygame.Surface((raio_x * 2, raio_y * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(superficie, (*MINT, alpha), (0, 0, raio_x * 2, raio_y * 2), width=5)
    tela.blit(superficie, (x - raio_x, y - raio_y))
