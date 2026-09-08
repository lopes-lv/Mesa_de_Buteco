"""
ui_pixelart.py - Toda a estética "pixel art" é desenhada via pygame.draw,
sem nenhuma imagem externa. As formas são deliberadamente blocadas
(retângulos, sem anti-aliasing) e usam paleta de cores sólidas para
lembrar jogos 8/16-bit.
"""
import pygame

# ---------- Paleta ----------
COR_FUNDO = (14, 20, 24)
COR_MESA = (24, 92, 58)
COR_MESA_BORDA = (14, 58, 36)
COR_MESA_BORDA_EXTERNA = (60, 38, 20)
COR_CARTA_FUNDO = (240, 236, 220)
COR_CARTA_BORDA = (20, 20, 20)
COR_CARTA_VERSO = (40, 60, 150)
COR_CARTA_VERSO_DETALHE = (70, 100, 210)
COR_BOTAO = (58, 110, 180)
COR_BOTAO_HOVER = (80, 140, 210)
COR_BOTAO_BORDA = (18, 30, 50)
COR_TEXTO = (245, 245, 235)
COR_TEXTO_ESCURO = (20, 20, 20)
COR_FICHA_BASE = [
    (210, 60, 60),    # vermelha (baixo valor)
    (60, 110, 210),   # azul
    (60, 180, 90),    # verde
    (30, 30, 30),     # preta (alto valor)
    (230, 200, 60),   # dourada
]

_fonte_cache = {}


def obter_fonte(tamanho, negrito=False):
    """Usa uma fonte monoespaçada do sistema para reforçar o visual pixelado."""
    chave = (tamanho, negrito)
    if chave not in _fonte_cache:
        candidatos = ["Courier New", "Consolas", "DejaVu Sans Mono", "monospace"]
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


def desenhar_texto(tela, texto, x, y, tamanho=18, cor=COR_TEXTO, negrito=False, centralizado=False):
    fonte = obter_fonte(tamanho, negrito)
    superficie = fonte.render(texto, False, cor)  # antialias=False -> visual mais "blocado"
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)
    return rect


def desenhar_carta(tela, x, y, largura, altura, carta=None, virada_para_baixo=False, destaque=False):
    """Desenha uma carta estilo pixel art (blocos sólidos, sem gradiente)."""
    rect = pygame.Rect(x, y, largura, altura)

    if virada_para_baixo or carta is None:
        pygame.draw.rect(tela, COR_CARTA_VERSO, rect)
        pygame.draw.rect(tela, COR_CARTA_BORDA, rect, 3)
        # padrão "xadrez" pixelado no verso
        bloco = max(4, largura // 6)
        for i in range(0, largura, bloco * 2):
            for j in range(0, altura, bloco * 2):
                pygame.draw.rect(
                    tela, COR_CARTA_VERSO_DETALHE,
                    (x + i, y + j, bloco, bloco)
                )
        return rect

    cor_fundo = COR_CARTA_FUNDO
    borda = 4 if destaque else 3
    cor_borda = (230, 200, 60) if destaque else COR_CARTA_BORDA
    pygame.draw.rect(tela, cor_fundo, rect)
    pygame.draw.rect(tela, cor_borda, rect, borda)

    tam_fonte = max(14, largura // 3)
    cor_naipe = carta.cor
    desenhar_texto(tela, carta.texto, x + 6, y + 4, tamanho=tam_fonte, cor=cor_naipe, negrito=True)
    desenhar_texto(
        tela, carta.texto, x + largura - 6, y + altura - tam_fonte - 4,
        tamanho=tam_fonte, cor=cor_naipe, negrito=True
    )
    _desenhar_naipe_simbolo(tela, carta, x + largura // 2, y + altura // 2, max(10, largura // 4))
    return rect


def _desenhar_naipe_simbolo(tela, carta, cx, cy, tamanho):
    cor = carta.cor
    s = carta.simbolo_naipe
    if s == "H":  # copas: dois círculos + triângulo (blocado)
        r = tamanho // 3
        pygame.draw.circle(tela, cor, (cx - r // 2, cy - r // 3), r)
        pygame.draw.circle(tela, cor, (cx + r // 2, cy - r // 3), r)
        pygame.draw.polygon(tela, cor, [
            (cx - r, cy), (cx + r, cy), (cx, cy + r)
        ])
    elif s == "D":  # ouros: losango
        pygame.draw.polygon(tela, cor, [
            (cx, cy - tamanho // 2), (cx + tamanho // 2, cy),
            (cx, cy + tamanho // 2), (cx - tamanho // 2, cy)
        ])
    elif s == "C":  # paus: três círculos + haste
        r = tamanho // 3
        pygame.draw.circle(tela, cor, (cx, cy - r), r)
        pygame.draw.circle(tela, cor, (cx - r, cy + r // 3), r)
        pygame.draw.circle(tela, cor, (cx + r, cy + r // 3), r)
        pygame.draw.rect(tela, cor, (cx - 2, cy, 4, tamanho // 2))
    else:  # espadas: triângulo + haste
        pygame.draw.polygon(tela, cor, [
            (cx, cy - tamanho // 2), (cx + tamanho // 2, cy + tamanho // 4),
            (cx - tamanho // 2, cy + tamanho // 4)
        ])
        pygame.draw.rect(tela, cor, (cx - 2, cy + tamanho // 4, 4, tamanho // 3))


def desenhar_ficha(tela, cx, cy, raio, valor_indice=0):
    """Ficha de poker estilo pixel art: círculo com faixas nas bordas."""
    cor = COR_FICHA_BASE[valor_indice % len(COR_FICHA_BASE)]
    pygame.draw.circle(tela, cor, (cx, cy), raio)
    pygame.draw.circle(tela, (20, 20, 20), (cx, cy), raio, 2)
    pygame.draw.circle(tela, (250, 250, 240), (cx, cy), int(raio * 0.6), 2)
    # marcas ao redor (efeito "serrilhado" pixelado)
    for i in range(8):
        import math
        ang = i * (360 / 8)
        px = cx + int(raio * 0.85 * math.cos(math.radians(ang)))
        py = cy + int(raio * 0.85 * math.sin(math.radians(ang)))
        pygame.draw.rect(tela, (250, 250, 240), (px - 2, py - 2, 4, 4))


def desenhar_pilha_fichas(tela, x, y, valor, raio=10):
    """Desenha uma pilha visual de fichas + o valor numérico ao lado."""
    n_fichas = min(6, max(1, valor // 50 + 1))
    for i in range(n_fichas):
        indice_cor = i % len(COR_FICHA_BASE)
        desenhar_ficha(tela, x, y - i * (raio // 2), raio, indice_cor)
    desenhar_texto(tela, str(valor), x + raio + 8, y - n_fichas * (raio // 2) // 2,
                    tamanho=16, cor=COR_TEXTO, negrito=True)


def desenhar_botao(tela, rect, texto, hover=False, ativo=True, tamanho_fonte=18):
    cor = COR_BOTAO_HOVER if hover and ativo else COR_BOTAO
    if not ativo:
        cor = (70, 70, 70)
    pygame.draw.rect(tela, cor, rect)
    pygame.draw.rect(tela, COR_BOTAO_BORDA, rect, 3)
    # highlight pixelado no topo (efeito bevel simples)
    pygame.draw.rect(tela, tuple(min(255, c + 25) for c in cor), (rect.x + 3, rect.y + 3, rect.width - 6, 4))
    desenhar_texto(tela, texto, rect.centerx, rect.centery, tamanho=tamanho_fonte,
                    cor=COR_TEXTO, negrito=True, centralizado=True)


def desenhar_mesa(tela, rect):
    """Desenha o feltro oval da mesa (aproximado por elipses, estilo pixelado)."""
    pygame.draw.ellipse(tela, COR_MESA_BORDA_EXTERNA, rect.inflate(40, 40))
    pygame.draw.ellipse(tela, COR_MESA_BORDA, rect.inflate(16, 16))
    pygame.draw.ellipse(tela, COR_MESA, rect)


def desenhar_painel(tela, rect, cor=(30, 34, 40), cor_borda=(70, 78, 90)):
    pygame.draw.rect(tela, cor, rect)
    pygame.draw.rect(tela, cor_borda, rect, 3)
