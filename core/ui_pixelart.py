"""
ui_pixelart.py - Toda a estética "pixel art" é desenhada via pygame.draw,
sem nenhuma imagem externa. As formas são deliberadamente blocadas
(retângulos, sem anti-aliasing) e usam paleta de cores sólidas para
lembrar jogos 8/16-bit.
"""
import pygame
import os

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

class SpriteLoader:
    def __init__(self, assets_path='assets/assets.png'):
        self.sheet = pygame.image.load(assets_path).convert_alpha()
        
        self.naipes = {
            'espadas': pygame.Rect(19, 23, 20, 23),
            'paus': pygame.Rect(48, 21, 20, 21),
            'copas': pygame.Rect(28, 57, 20, 19),
            'ouros': pygame.Rect(54, 54, 18, 29)
        }
        
        self.faces_vermelhas = {
            'J': pygame.Rect(92, 20, 44, 36),
            'Q': pygame.Rect(146, 7, 37, 64),
            'K': pygame.Rect(194, 10, 41, 54)
        }
        
        self.faces_pretas = {
            'J': pygame.Rect(242, 20, 44, 36),
            'Q': pygame.Rect(296, 7, 37, 64),
            'K': pygame.Rect(344, 10, 41, 54)
        }
        
        self.base_verso = pygame.Rect(15, 92, 58, 74)
        self.base_frente = pygame.Rect(88, 91, 58, 74)
        
        self.textos_vermelhos = {
            'A': pygame.Rect(173, 95, 14, 18),
            '2': pygame.Rect(195, 96, 11, 16),
            '3': pygame.Rect(216, 98, 13, 14),
            '4': pygame.Rect(239, 97, 18, 16),
            '5': pygame.Rect(268, 97, 14, 17),
            '6': pygame.Rect(294, 98, 9, 15),
            '7': pygame.Rect(313, 100, 11, 17),
            '8': pygame.Rect(330, 100, 9, 18),
            '9': pygame.Rect(346, 101, 9, 18),
            '10': pygame.Rect(362, 103, 13, 12),
            'J': pygame.Rect(393, 103, 15, 14),
            'Q': pygame.Rect(411, 103, 15, 13),
            'K': pygame.Rect(432, 104, 11, 14)
        }
        
        self.textos_pretos = {
            'A': pygame.Rect(169, 131, 14, 18),
            '2': pygame.Rect(191, 132, 11, 16),
            '3': pygame.Rect(212, 134, 13, 14),
            '4': pygame.Rect(235, 133, 18, 16),
            '5': pygame.Rect(264, 133, 14, 17),
            '6': pygame.Rect(290, 134, 9, 15),
            '7': pygame.Rect(309, 136, 11, 17),
            '8': pygame.Rect(326, 136, 9, 18),
            '9': pygame.Rect(342, 137, 9, 18),
            '10': pygame.Rect(358, 139, 13, 12),
            'J': pygame.Rect(389, 139, 15, 14),
            'Q': pygame.Rect(407, 139, 15, 13),
            'K': pygame.Rect(428, 140, 11, 14)
        }
        
        self._cache = {}
        self._cache_verso = None
        self._gerar_cache()

    def get_sprite(self, rect):
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.blit(self.sheet, (0, 0), rect)
        return surf

    def _gerar_cache(self):
        self._cache_verso = self.get_sprite(self.base_verso)
        
        valores = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        naipes_dict = {
            'copas': ('vermelho', self.naipes['copas']),
            'ouros': ('vermelho', self.naipes['ouros']),
            'espadas': ('preto', self.naipes['espadas']),
            'paus': ('preto', self.naipes['paus'])
        }
        
        for valor in valores:
            for nome_naipe, (cor, rect_naipe) in naipes_dict.items():
                carta_surf = self.get_sprite(self.base_frente).copy()
                
                dict_textos = self.textos_vermelhos if cor == 'vermelho' else self.textos_pretos
                surf_texto = self.get_sprite(dict_textos[valor])
                
                surf_naipe = self.get_sprite(rect_naipe)
                surf_naipe_pequeno = pygame.transform.smoothscale(surf_naipe, (10, 10))
                
                # Canto superior esquerdo
                carta_surf.blit(surf_texto, (3, 3))
                carta_surf.blit(surf_naipe_pequeno, (3 + surf_texto.get_width()//2 - 5, 3 + surf_texto.get_height() + 1))
                
                # Canto inferior direito (rotacionado 180)
                surf_texto_rot = pygame.transform.rotate(surf_texto, 180)
                surf_naipe_pequeno_rot = pygame.transform.rotate(surf_naipe_pequeno, 180)
                
                cw, ch = carta_surf.get_size()
                carta_surf.blit(surf_texto_rot, (cw - 3 - surf_texto_rot.get_width(), ch - 3 - surf_texto_rot.get_height()))
                carta_surf.blit(surf_naipe_pequeno_rot, (cw - 3 - surf_texto_rot.get_width()//2 - 5, ch - 3 - surf_texto_rot.get_height() - 1 - 10))
                
                # Centro
                if valor in ['J', 'Q', 'K']:
                    faces = self.faces_vermelhas if cor == 'vermelho' else self.faces_pretas
                    surf_face = self.get_sprite(faces[valor])
                    fx = (cw - surf_face.get_width()) // 2
                    fy = (ch - surf_face.get_height()) // 2
                    carta_surf.blit(surf_face, (fx, fy))
                else:
                    nx = (cw - surf_naipe.get_width()) // 2
                    ny = (ch - surf_naipe.get_height()) // 2
                    carta_surf.blit(surf_naipe, (nx, ny))
                
                self._cache[f"{valor}_de_{nome_naipe}"] = carta_surf

    def get_carta(self, valor, naipe):
        key = f"{valor}_de_{naipe.lower()}"
        return self._cache.get(key, self._cache_verso)
        
    def get_verso(self):
        return self._cache_verso

_sprite_loader = None
_estilo_baralho = "sprites"

def set_estilo_baralho(estilo):
    global _estilo_baralho
    _estilo_baralho = estilo

def get_estilo_baralho():
    global _estilo_baralho
    return _estilo_baralho

def inicializar_sprites(assets_path='assets/assets.png'):
    global _sprite_loader
    if _sprite_loader is None and os.path.exists(assets_path):
        _sprite_loader = SpriteLoader(assets_path)

def desenhar_carta(tela, x, y, largura, altura, carta=None, virada_para_baixo=False, destaque=False):
    """Desenha uma carta estilo pixel art. Usa sprites se disponíveis."""
    rect = pygame.Rect(x, y, largura, altura)
    
    global _sprite_loader, _estilo_baralho
    if _estilo_baralho == "sprites" and _sprite_loader is not None:
        if virada_para_baixo or carta is None:
            imagem = _sprite_loader.get_verso()
        else:
            imagem = _sprite_loader.get_carta(carta.texto, carta.naipe)
            
        if imagem.get_width() != largura or imagem.get_height() != altura:
            imagem = pygame.transform.scale(imagem, (largura, altura))
            
        tela.blit(imagem, (x, y))
        
        if destaque:
            pygame.draw.rect(tela, (230, 200, 60), rect, 4)
            
        return rect

    # Procedural drawing
    cor_fundo = COR_CARTA_FUNDO
    cor_borda = COR_CARTA_BORDA
    cor_verso = COR_CARTA_VERSO
    cor_verso_detalhe = COR_CARTA_VERSO_DETALHE
    
    if _estilo_baralho == "dark":
        cor_fundo = (45, 45, 50)
        cor_borda = (15, 15, 18)
        cor_verso = (30, 30, 35)
        cor_verso_detalhe = (50, 50, 55)

    if virada_para_baixo or carta is None:
        pygame.draw.rect(tela, cor_verso, rect)
        pygame.draw.rect(tela, cor_borda, rect, 3)
        # padrão "xadrez" pixelado no verso
        bloco = max(4, largura // 6)
        for i in range(0, largura, bloco * 2):
            for j in range(0, altura, bloco * 2):
                pygame.draw.rect(
                    tela, cor_verso_detalhe,
                    (x + i, y + j, bloco, bloco)
                )
        return rect

    borda = 4 if destaque else 3
    cor_borda_ativa = (230, 200, 60) if destaque else cor_borda
    pygame.draw.rect(tela, cor_fundo, rect)
    pygame.draw.rect(tela, cor_borda_ativa, rect, borda)

    tam_fonte = max(14, largura // 3)
    cor_naipe = carta.cor
    
    # Adaptar cor dos naipes pretos para o dark mode
    if _estilo_baralho == "dark" and cor_naipe == (25, 25, 25):
        cor_naipe = (220, 220, 220)

    desenhar_texto(tela, carta.texto, x + 6, y + 4, tamanho=tam_fonte, cor=cor_naipe, negrito=True)
    desenhar_texto(
        tela, carta.texto, x + largura - 6, y + altura - tam_fonte - 4,
        tamanho=tam_fonte, cor=cor_naipe, negrito=True
    )
    _desenhar_naipe_simbolo(tela, carta, x + largura // 2, y + altura // 2, max(10, largura // 4), cor_naipe=cor_naipe)
    return rect


def _desenhar_naipe_simbolo(tela, carta, cx, cy, tamanho, cor_naipe=None):
    cor = cor_naipe if cor_naipe else carta.cor
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
