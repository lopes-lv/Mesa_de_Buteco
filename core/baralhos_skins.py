"""
baralhos_skins.py - 8 baralhos (skins de carta) prontos para o Pygame, um por
estilo visual proposto em design/<NN>_<estilo>/mockup.html.

Pensado para ser copiado para `core/baralhos_skins.py` (ver GUIA_BARALHOS.md).
Não depende do resto do jogo: a carta só precisa ter os atributos
`.texto` ("A", "10", "JK"...), `.naipe` ("copas"/"ouros"/"paus"/"espadas"/
"coringa") e `.simbolo_naipe` ("H"/"D"/"C"/"S"/"★") - o mesmo contrato de
`core/deck.py:Card`.

Cada skin é só dados (SKINS). Para ajustar um baralho, mexa no dicionário;
para criar outro, copie uma entrada. O desenho é feito 100% com pygame.draw,
sem imagens externas, como o restante do jogo.

API principal:
    desenhar_carta_skin(tela, skin_id, x, y, largura, altura, carta=None,
                        virada_para_baixo=False, destaque=False, vazia=False)
"""
import math
import pygame

# ---------------------------------------------------------------- definição
# Campos de cada skin:
#   nome        rótulo para o menu de Ajustes
#   face        cor do fundo da frente
#   borda, borda_w       cor / espessura-base (px a 64 de largura) da borda
#   raio        raio dos cantos (px a 64 de largura)
#   sombra      (dx, dy, cor RGBA) sombra sólida deslocada, ou None
#   glow        cor RGBA do brilho externo (neon), ou None
#   tinta       cor dos naipes/valores pretos (espadas/paus)
#   vermelho    cor dos naipes/valores vermelhos (copas/ouros)
#   borda_vermelha  se definido, cartas vermelhas usam esta borda (neon/terminal)
#   fonte       "mono" | "serif" | "sans" | "pixel"
#   verso_a, verso_b     cor(es) do verso (b opcional: gradiente vertical)
#   verso_borda          cor da borda do verso
#   padrao      padrão do verso: losango | rede | xadrez | listras | quadrado
#               | circulo | moldura | neon
#   padrao_cor  cor do padrão do verso
#   vazia       cor do contorno tracejado do "espaço de carta" vazio
SKINS: dict[str, dict] = {
    "dark_glass": dict(
        nome="Dark Glass", face=(232, 236, 255), borda=(255, 255, 255, 140), borda_w=1.5, raio=12,
        sombra=(0, 4, (0, 0, 0, 90)), glow=None, tinta=(20, 23, 46), vermelho=(226, 61, 107),
        fonte="sans", verso_a=(107, 91, 255), verso_b=(43, 212, 192), verso_borda=(255, 255, 255, 170),
        padrao="moldura", padrao_cor=(255, 255, 255, 150), vazia=(255, 255, 255, 70)),
    "terminal": dict(
        nome="Terminal", face=(5, 8, 5), borda=(125, 255, 160), borda_w=1.5, raio=0,
        sombra=None, glow=(125, 255, 160, 40), tinta=(125, 255, 160), vermelho=(255, 179, 71),
        borda_vermelha=(255, 179, 71), fonte="mono", verso_a=(5, 8, 5), verso_b=None,
        verso_borda=(125, 255, 160), padrao="listras", padrao_cor=(42, 74, 51), vazia=(42, 74, 51)),
    "art_deco": dict(
        nome="Art Déco", face=(247, 239, 216), borda=(201, 162, 75), borda_w=1.5, raio=6,
        sombra=(2, 3, (0, 0, 0, 110)), glow=None, tinta=(18, 32, 28), vermelho=(168, 40, 31),
        fonte="serif", verso_a=(15, 59, 50), verso_b=None, verso_borda=(201, 162, 75),
        padrao="rede", padrao_cor=(201, 162, 75, 130), vazia=(201, 162, 75, 150)),
    "pixel_crt": dict(
        nome="Pixel CRT", face=(244, 244, 244), borda=(0, 0, 0), borda_w=4, raio=0,
        sombra=(4, 4, (12, 13, 23, 255)), glow=None, tinta=(26, 28, 44), vermelho=(177, 62, 83),
        fonte="pixel", verso_a=(59, 93, 201), verso_b=None, verso_borda=(255, 255, 255),
        padrao="xadrez", padrao_cor=(65, 166, 246), vazia=(93, 106, 138)),
    "synthwave": dict(
        nome="Synthwave", face=(16, 5, 42), borda=(39, 232, 255), borda_w=2, raio=8,
        sombra=None, glow=(39, 232, 255, 70), tinta=(39, 232, 255), vermelho=(255, 46, 147),
        borda_vermelha=(255, 46, 147), fonte="sans", verso_a=(42, 8, 69), verso_b=(16, 5, 42),
        verso_borda=(255, 46, 147), padrao="neon", padrao_cor=(255, 46, 147), vazia=(93, 59, 138)),
    "papel_vintage": dict(
        nome="Papel Vintage", face=(251, 244, 222), borda=(42, 26, 16), borda_w=2, raio=5,
        sombra=(0, 0, (0, 0, 0, 0)), glow=None, tinta=(42, 26, 16), vermelho=(168, 50, 31),
        fonte="serif", verso_a=(168, 50, 31), verso_b=None, verso_borda=(243, 232, 201),
        padrao="listras", padrao_cor=(243, 232, 201, 150), vazia=(217, 194, 138)),
    "editorial": dict(
        nome="Editorial", face=(255, 255, 255), borda=(13, 13, 13), borda_w=3, raio=0,
        sombra=None, glow=None, tinta=(13, 13, 13), vermelho=(255, 59, 31),
        fonte="sans", verso_a=(13, 13, 13), verso_b=None, verso_borda=(13, 13, 13),
        padrao="quadrado", padrao_cor=(255, 59, 31), vazia=(170, 170, 170)),
    "zen": dict(
        nome="Zen", face=(255, 250, 240), borda=(43, 38, 34), borda_w=1.5, raio=4,
        sombra=(0, 3, (0, 0, 0, 55)), glow=None, tinta=(43, 38, 34), vermelho=(192, 57, 43),
        fonte="serif", verso_a=(30, 42, 58), verso_b=None, verso_borda=(43, 38, 34),
        padrao="circulo", padrao_cor=(192, 57, 43), vazia=(239, 231, 214)),
}

ORDEM_SKINS = list(SKINS.keys())
ROTULOS_SKINS = {k: v["nome"] for k, v in SKINS.items()}

FONTES = {
    "mono": ["Consolas", "Courier New", "DejaVu Sans Mono"],
    "serif": ["Georgia", "Palatino Linotype", "Times New Roman", "DejaVu Serif"],
    "sans": ["Segoe UI", "Verdana", "Arial"],
    "pixel": ["Consolas", "Courier New", "DejaVu Sans Mono"],
}

# ------------------------------------------------------------------ cache
_fontes: dict = {}
_cache: dict = {}


def _fonte(familia, tamanho):
    chave = (familia, tamanho)
    if chave not in _fontes:
        fonte = None
        for nome in FONTES[familia]:
            try:
                fonte = pygame.font.SysFont(nome, tamanho, bold=True)
                break
            except Exception:
                continue
        _fontes[chave] = fonte or pygame.font.Font(None, tamanho)
    return _fontes[chave]


def _rgba(c, a=255):
    return c if len(c) == 4 else (*c, a)


# ------------------------------------------------------------------ naipes
def desenhar_naipe(s, simbolo, cx, cy, t, cor):
    """Naipes vetoriais (H/D/C/S/★) centrados em (cx, cy), tamanho ~t."""
    if simbolo == "H":
        r = t * 0.27
        pygame.draw.circle(s, cor, (cx - r, cy - r * 0.55), r)
        pygame.draw.circle(s, cor, (cx + r, cy - r * 0.55), r)
        pygame.draw.polygon(s, cor, [(cx - r * 1.93, cy - r * 0.2), (cx + r * 1.93, cy - r * 0.2), (cx, cy + t * 0.48)])
    elif simbolo == "D":
        pygame.draw.polygon(s, cor, [(cx, cy - t * 0.5), (cx + t * 0.36, cy), (cx, cy + t * 0.5), (cx - t * 0.36, cy)])
    elif simbolo == "C":
        r = t * 0.22
        pygame.draw.circle(s, cor, (cx, cy - r * 1.1), r)
        pygame.draw.circle(s, cor, (cx - r * 1.15, cy + r * 0.55), r)
        pygame.draw.circle(s, cor, (cx + r * 1.15, cy + r * 0.55), r)
        pygame.draw.polygon(s, cor, [(cx - t * 0.07, cy + r * 0.4), (cx + t * 0.07, cy + r * 0.4),
                                     (cx + t * 0.16, cy + t * 0.5), (cx - t * 0.16, cy + t * 0.5)])
    elif simbolo == "S":
        r = t * 0.27
        pygame.draw.circle(s, cor, (cx - r, cy + r * 0.2), r)
        pygame.draw.circle(s, cor, (cx + r, cy + r * 0.2), r)
        pygame.draw.polygon(s, cor, [(cx, cy - t * 0.5), (cx + r * 1.93, cy + r * 0.1), (cx - r * 1.93, cy + r * 0.1)])
        pygame.draw.polygon(s, cor, [(cx - t * 0.07, cy + r * 0.4), (cx + t * 0.07, cy + r * 0.4),
                                     (cx + t * 0.16, cy + t * 0.5), (cx - t * 0.16, cy + t * 0.5)])
    else:  # coringa
        pts = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            raio = t * 0.5 if i % 2 == 0 else t * 0.2
            pts.append((cx + raio * math.cos(ang), cy - raio * math.sin(ang)))
        pygame.draw.polygon(s, cor, pts)


# ------------------------------------------------------------------- verso
def _gradiente(s, rect, a, b, raio):
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    for i in range(rect.height):
        k = i / max(1, rect.height - 1)
        pygame.draw.line(tmp, tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3)), (0, i), (rect.width, i))
    mascara = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=raio)
    tmp.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(tmp, rect.topleft)


def _padrao_verso(s, sk, rect, k):
    cor = _rgba(sk["padrao_cor"])
    p = sk["padrao"]
    inner = rect.inflate(-rect.width * 0.28, -rect.height * 0.22)
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    r = tmp.get_rect()
    ir = inner.move(-rect.x, -rect.y)
    cx, cy = r.center
    if p == "losango":
        d = min(r.w, r.h) * 0.22
        pygame.draw.polygon(tmp, cor, [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)])
    elif p == "moldura":
        pygame.draw.rect(tmp, cor, ir, width=max(1, int(k * 1.5)), border_radius=int(6 * k))
        d = min(ir.w, ir.h) * 0.22
        pygame.draw.polygon(tmp, cor, [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)],
                            width=max(1, int(k * 1.5)))
    elif p == "rede":
        pygame.draw.rect(tmp, cor, ir, width=max(1, int(k)))
        passo = max(5, int(9 * k))
        for i in range(-ir.h, ir.w, passo):
            pygame.draw.line(tmp, cor, (ir.x + i, ir.bottom), (ir.x + i + ir.h, ir.y), 1)
            pygame.draw.line(tmp, cor, (ir.x + i, ir.y), (ir.x + i + ir.h, ir.bottom), 1)
        clip = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(clip, (255, 255, 255, 255), ir)
        tmp.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.rect(tmp, cor, ir, width=max(1, int(k)))
    elif p == "listras":
        passo = max(4, int(8 * k))
        for i in range(-r.h, r.w, passo):
            pygame.draw.line(tmp, cor, (i, r.h), (i + r.h, 0), max(1, int(k)))
        clip = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(clip, (255, 255, 255, 255), r.inflate(-int(10 * k), -int(10 * k)))
        tmp.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    elif p == "xadrez":
        c = max(4, int(12 * k))
        for yy in range(ir.y, ir.bottom, c):
            for xx in range(ir.x, ir.right, c):
                if ((xx - ir.x) // c + (yy - ir.y) // c) % 2 == 0:
                    pygame.draw.rect(tmp, cor, (xx, yy, min(c, ir.right - xx), min(c, ir.bottom - yy)))
    elif p == "quadrado":
        d = min(r.w, r.h) * 0.30
        pygame.draw.rect(tmp, cor, (cx - d / 2, cy - d / 2, d, d))
    elif p == "circulo":
        pygame.draw.ellipse(tmp, cor, (cx - r.w * 0.21, cy - r.h * 0.15, r.w * 0.42, r.h * 0.30))
    elif p == "neon":
        d = min(r.w, r.h) * 0.30
        pts = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
        pygame.draw.polygon(tmp, (*cor[:3], 70), pts)
        pygame.draw.polygon(tmp, cor, pts, width=max(2, int(2 * k)))
    s.blit(tmp, rect.topleft)


# ------------------------------------------------------------------ carta
def _renderizar(skin_id, w, h, verso, destaque, vazia, carta):
    sk = SKINS[skin_id]
    k = w / 64.0
    raio = int(sk["raio"] * k)
    borda = max(1, int(round(sk["borda_w"] * k))) + (2 if destaque else 0)
    margem = int(10 * k) + 6
    s = pygame.Surface((w + 2 * margem, h + 2 * margem), pygame.SRCALPHA)
    rect = pygame.Rect(margem, margem, w, h)

    if vazia:
        cor = _rgba(sk["vazia"])
        passo = max(6, int(10 * k))
        for xx in range(rect.left + raio, rect.right - raio, passo * 2):
            pygame.draw.line(s, cor, (xx, rect.top), (min(xx + passo, rect.right - raio), rect.top), 2)
            pygame.draw.line(s, cor, (xx, rect.bottom - 1), (min(xx + passo, rect.right - raio), rect.bottom - 1), 2)
        for yy in range(rect.top + raio, rect.bottom - raio, passo * 2):
            pygame.draw.line(s, cor, (rect.left, yy), (rect.left, min(yy + passo, rect.bottom - raio)), 2)
            pygame.draw.line(s, cor, (rect.right - 1, yy), (rect.right - 1, min(yy + passo, rect.bottom - raio)), 2)
        return s

    vermelha = (not verso) and carta is not None and carta.naipe in ("copas", "ouros")
    cor_borda = _rgba(sk.get("borda_vermelha") if (vermelha and sk.get("borda_vermelha")) else sk["borda"])

    if sk["glow"]:
        g = _rgba(sk["glow"])
        for i in range(4, 0, -1):
            gl = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(gl, (*g[:3], max(8, g[3] // (i + 1))), rect.inflate(i * 4 * k, i * 4 * k),
                             border_radius=raio + i * 2)
            s.blit(gl, (0, 0))
    if sk["sombra"]:
        dx, dy, cor = sk["sombra"]
        sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(sombra, _rgba(cor), rect.move(int(dx * k), int(dy * k)), border_radius=raio)
        s.blit(sombra, (0, 0))

    if verso:
        if sk["verso_b"]:
            _gradiente(s, rect, sk["verso_a"], sk["verso_b"], raio)
        else:
            pygame.draw.rect(s, sk["verso_a"], rect, border_radius=raio)
        _padrao_verso(s, sk, rect, k)
        pygame.draw.rect(s, _rgba(sk["verso_borda"]), rect, width=max(borda, int(2 * k)), border_radius=raio)
        return s

    pygame.draw.rect(s, sk["face"], rect, border_radius=raio)
    cor_borda_final = (255, 201, 60, 255) if destaque else cor_borda
    pygame.draw.rect(s, cor_borda_final, rect, width=borda, border_radius=raio)

    if carta.naipe == "coringa":
        cor = (167, 139, 250)
    else:
        cor = sk["vermelho"] if vermelha else sk["tinta"]
    tam_rank = max(11, int(w * 0.26))
    pad = max(3, int(w * 0.09))
    fonte = _fonte(sk["fonte"], tam_rank)
    txt = fonte.render(carta.texto, sk["fonte"] != "pixel", cor)  # "pixel": sem antialias
    s.blit(txt, (rect.x + pad, rect.y + pad - 2))
    s.blit(pygame.transform.rotate(txt, 180),
           (rect.right - pad - txt.get_width(), rect.bottom - pad - txt.get_height() + 2))
    desenhar_naipe(s, carta.simbolo_naipe, rect.centerx, rect.centery, max(14, w * 0.42), cor)
    return s


def desenhar_carta_skin(tela, skin_id, x, y, largura, altura, carta=None,
                        virada_para_baixo=False, destaque=False, vazia=False):
    """Mesma assinatura de `ui_theme.desenhar_carta`, mais `skin_id`.
    Retorna o `pygame.Rect` da carta (sem a margem de sombra/brilho)."""
    verso = virada_para_baixo or (carta is None and not vazia)
    chave = (skin_id, largura, altura,
             None if verso or vazia else (carta.naipe, carta.texto), verso, destaque, vazia)
    surf = _cache.get(chave)
    if surf is None:
        if len(_cache) > 400:
            _cache.clear()
        surf = _cache[chave] = _renderizar(skin_id, largura, altura, verso, destaque, vazia, carta)
    margem = (surf.get_width() - largura) // 2
    tela.blit(surf, (x - margem, y - margem))
    return pygame.Rect(x, y, largura, altura)
