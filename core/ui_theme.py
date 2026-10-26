"""
ui_theme.py - Biblioteca de desenho do estilo visual "Pixel Art Retrô CRT"
(ver design/07_pixel_retro_crt/mockup.html para a referência original em HTML).

Tudo é desenhado via pygame.draw / pygame.Surface, sem imagens externas:
cantos retos (sem arredondamento), bordas grossas, sombra sólida deslocada
(sem blur) e paleta escura "tela de CRT" com acentos saturados tipo arcade.
Esta é a segunda estética implementada no motor vetorial - a primeira
("Neobrutalismo Suave") está preservada em design/01_neobrutalismo_suave/.
"""
import math
import pygame

from .deck import NAIPE_CORINGA
from . import baralhos_skins
from . import layout

# ---------- Paleta ----------
# Papéis fixos (não trocam de lado claro/escuro):
#   BG/PANEL/LOCKED = fundo e superfícies neutras (escuras)
#   INK             = texto/borda principal (claro, "tinta" sobre fundo escuro)
#   SOMBRA          = cor fixa da sombra sólida deslocada (sempre escura)
#   CARTA_FACE/CARTA_INK = a carta é "papel": sempre clara, com tinta escura,
#                     mesmo com o resto da UI em modo escuro.
# Os valores ficam em config/layout_padrao.json (grupo "cores"), editáveis
# pelo editor visual. Cada cor é um pygame.Color (mutável) e não uma tupla: as
# telas fazem `from core.ui_theme import YELLOW`, então guardam uma referência
# ao MESMO objeto - aplicar_tema() muda a cor no lugar e todo mundo enxerga.
# Por isso, ao juntar alfa, use `(*COR[:3], alfa)` (um Color já tem 4 canais).
BG = pygame.Color(0, 0, 0)
PANEL = pygame.Color(0, 0, 0)
FELT = pygame.Color(0, 0, 0)
FELT_DARK = pygame.Color(0, 0, 0)
INK = pygame.Color(0, 0, 0)
TEXT_MUTED = pygame.Color(0, 0, 0)
YELLOW = pygame.Color(0, 0, 0)
CORAL = pygame.Color(0, 0, 0)
BLUE = pygame.Color(0, 0, 0)
MINT = pygame.Color(0, 0, 0)
PURPLE = pygame.Color(0, 0, 0)
LOCKED = pygame.Color(0, 0, 0)
RED_SUIT = pygame.Color(0, 0, 0)
SOMBRA = pygame.Color(0, 0, 0)
CARTA_FACE = pygame.Color(0, 0, 0)
CARTA_INK = pygame.Color(0, 0, 0)

# chave em "cores.*" -> objeto de cor (preenchido por aplicar_tema(), logo abaixo)
_PALETA = {
    "fundo": BG, "painel": PANEL, "feltro": FELT, "feltro_escuro": FELT_DARK,
    "tinta": INK, "texto_apagado": TEXT_MUTED, "amarelo": YELLOW, "coral": CORAL,
    "azul": BLUE, "verde": MINT, "roxo": PURPLE, "bloqueado": LOCKED,
    "naipe_vermelho": RED_SUIT, "sombra": SOMBRA, "carta_face": CARTA_FACE, "carta_tinta": CARTA_INK,
}

# Compatibilidade com nomes antigos usados em outros módulos.
COR_TEXTO = INK

CHIP_CORES = [YELLOW, BLUE, MINT, CORAL, PURPLE]

CROUPIER_PELE = (235, 195, 155)
CROUPIER_COLETE = (38, 40, 54)
CROUPIER_CABELO = (74, 52, 38)

# Espessura da borda e deslocamento da sombra de botões/painéis, e escala de
# todas as fontes (%) - também de config/layout_padrao.json ("geral.*").
_tema = {"borda": 4, "sombra": 6, "escala_fonte": 100}


def aplicar_tema(obter=None):
    """Carrega cores, borda/sombra e escala de fonte de `obter(chave)`
    (padrão: `layout.obter`, ou seja, o layout em uso). Chamado ao importar
    este módulo; o editor visual chama de novo pra alternar entre o tema
    padrão (na própria interface) e o tema editado (nas prévias)."""
    obter = obter or layout.obter
    for chave, cor in _PALETA.items():
        cor.update(*obter(f"cores.{chave}"))
    for chave in _tema:
        _tema[chave] = obter(f"geral.{chave}")


aplicar_tema()


def luminancia(cor):
    """Luminância relativa (WCAG 2) de uma cor RGB, de 0 (preto) a 1 (branco)."""
    def canal(valor):
        valor /= 255
        return valor / 12.92 if valor <= 0.03928 else ((valor + 0.055) / 1.055) ** 2.4
    r, g, b = cor[:3]
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(cor_a, cor_b):
    """Razão de contraste WCAG entre duas cores (1 a 21; texto pede >= 4.5)."""
    claro, escuro = sorted((luminancia(cor_a), luminancia(cor_b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def cor_texto_sobre(fundo):
    """Texto escuro (SOMBRA) ou claro (INK), o que tiver mais contraste com
    `fundo`. Com a paleta padrão dá texto escuro só no amarelo e no verde (era
    uma lista fixa antes de as cores ficarem editáveis)."""
    return SOMBRA if contraste(fundo, SOMBRA) > contraste(fundo, INK) else INK

# ---------- Fontes ----------
# Sem arquivos .ttf baixados: usamos uma fonte monoespaçada de sistema (bem
# mais "retrô/terminal" que a Segoe UI do estilo anterior) pra título, corpo
# e números. Trocar por uma bitmap font real em assets/fonts/ no futuro é
# trivial: basta apontar pygame.font.Font(caminho, tamanho) em obter_fonte().
FAMILIAS = {
    "display": ["Consolas", "Lucida Console", "Courier New", "DejaVu Sans Mono"],
    "body": ["Consolas", "Lucida Console", "Courier New", "DejaVu Sans Mono"],
    "mono": ["Consolas", "Courier New", "DejaVu Sans Mono"],
}

_fonte_cache: dict = {}


def obter_fonte(tamanho, negrito=False, familia="body"):
    """Fonte do tamanho pedido, já aplicada a escala "geral.escala_fonte"."""
    tamanho = max(6, round(tamanho * _tema["escala_fonte"] / 100))
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


# ---------- Primitivas: retângulos de cantos retos, borda e sombra sólida ----------
def retangulo_borda(tela, rect, cor_fundo, cor_borda=INK, largura_borda=4, radius=0):
    pygame.draw.rect(tela, cor_fundo, rect, border_radius=radius)
    if largura_borda > 0:
        pygame.draw.rect(tela, cor_borda, rect, width=largura_borda, border_radius=radius)


def desenhar_painel(tela, rect, cor=PANEL, cor_borda=INK, radius=0, sombra=True,
                     largura_borda=None, deslocamento_sombra=None):
    """Painel pixel art: preenchimento + borda grossa + sombra sólida deslocada,
    sem arredondamento de cantos. Sem `largura_borda`/`deslocamento_sombra`
    explícitos, usa "geral.borda"/"geral.sombra" do layout."""
    if largura_borda is None:
        largura_borda = _tema["borda"]
    if deslocamento_sombra is None:
        deslocamento_sombra = (_tema["sombra"], _tema["sombra"])
    if sombra:
        pygame.draw.rect(tela, SOMBRA, rect.move(*deslocamento_sombra), border_radius=radius)
    retangulo_borda(tela, rect, cor, cor_borda, largura_borda, radius)


def desenhar_botao(tela, rect, texto, hover=False, ativo=True, tamanho_fonte=18,
                    cor=YELLOW, cor_texto=None, radius=0, largura_borda=None):
    """Botão pixel art. Ao passar o mouse, 'levanta' (sombra maior, corpo
    deslocado); a área de clique (rect original) não muda de tamanho/posição.
    `cor_texto=None` (padrão) escolhe automaticamente o texto de maior
    contraste com o fundo (cor_texto_sobre) - só é preciso informar
    `cor_texto` explicitamente pra fugir dessa regra. Borda e sombra seguem
    "geral.borda"/"geral.sombra" (sombra +2 no hover, metade se desativado)."""
    if largura_borda is None:
        largura_borda = _tema["borda"]
    sombra = _tema["sombra"]
    if not ativo:
        desenho_rect = rect
        sombra_offset = (sombra // 2, sombra // 2)
        fundo = LOCKED
        cor_txt = TEXT_MUTED
    else:
        if hover:
            desenho_rect = rect.move(-2, -2)
            sombra_offset = (sombra + 2, sombra + 2)
        else:
            desenho_rect = rect
            sombra_offset = (sombra, sombra)
        fundo = cor
        cor_txt = cor_texto if cor_texto is not None else cor_texto_sobre(cor)

    pygame.draw.rect(tela, SOMBRA, desenho_rect.move(*sombra_offset), border_radius=radius)
    retangulo_borda(tela, desenho_rect, fundo, INK, largura_borda, radius)
    desenhar_texto(tela, texto.upper(), desenho_rect.centerx, desenho_rect.centery,
                    tamanho=tamanho_fonte, cor=cor_txt, negrito=True,
                    centralizado=True, familia="display")
    return rect


def desenhar_kbd(tela, x, y, texto, ancorar="center"):
    """Selo pequeno estilo 'tecla física' ([ENTER], [ESC], [F]...): keycap
    claro com borda e texto escuros."""
    fonte = obter_fonte(12, True, "mono")
    superficie = fonte.render(texto.upper(), True, SOMBRA)
    pad_x, pad_y = 9, 4
    rect = pygame.Rect(0, 0, superficie.get_width() + pad_x * 2, superficie.get_height() + pad_y * 2)
    setattr(rect, ancorar, (x, y))
    pygame.draw.rect(tela, INK, rect)
    pygame.draw.rect(tela, SOMBRA, rect, width=2)
    tela.blit(superficie, superficie.get_rect(center=rect.center))
    return rect


def tamanho_badge(texto, tamanho_fonte=12, familia="body"):
    """(largura, altura) que desenhar_badge() vai ocupar - pra posicionar um
    selo antes de desenhá-lo."""
    # mede a superfície renderizada (como o selo é desenhado), não Font.size(),
    # que pode diferir em 1px
    largura, altura = obter_fonte(tamanho_fonte, True, familia).render(texto, True, (0, 0, 0)).get_size()
    return largura + 2 * 10, altura + 2 * 5


def desenhar_badge(tela, x, y, texto, cor_fundo, cor_texto=INK, tamanho_fonte=12,
                    ancorar="center", borda=None, familia="body"):
    """Pill genérico virou tag retangular (status de bot, marcador SB/BB,
    tags 'ATIVO'/'EM BREVE', pote, etc.) - cantos retos, borda opcional."""
    fonte = obter_fonte(tamanho_fonte, True, familia)
    superficie = fonte.render(texto, True, cor_texto)
    rect = pygame.Rect((0, 0), tamanho_badge(texto, tamanho_fonte, familia))
    setattr(rect, ancorar, (x, y))
    pygame.draw.rect(tela, cor_fundo, rect)
    if borda:
        pygame.draw.rect(tela, borda, rect, width=2)
    tela.blit(superficie, superficie.get_rect(center=rect.center))
    return rect


def desenhar_avatar(tela, cx, cy, raio, cor_fundo, iniciais, cor_borda=INK,
                     largura_borda=4, sombra=(4, 4)):
    """Avatar quadrado (era um círculo no Neobrutalismo) - crachá pixel art
    com borda grossa clara e sombra sólida."""
    lado = raio * 2
    rect = pygame.Rect(0, 0, lado, lado)
    rect.center = (cx, cy)
    if sombra:
        pygame.draw.rect(tela, SOMBRA, rect.move(*sombra))
    pygame.draw.rect(tela, cor_fundo, rect)
    pygame.draw.rect(tela, cor_borda, rect, largura_borda)
    desenhar_texto(tela, iniciais, cx, cy, tamanho=max(12, int(raio * 0.62)),
                    cor=BG, negrito=True, centralizado=True, familia="display")


# ---------- Cartas ----------
# Skin de baralho (opção em Ajustes, ver settings.py). Estado global lido por
# `desenhar_carta` a cada frame - sincronizado uma vez por App.executar(),
# nenhum call site precisa passar o skin manualmente. Mesmo padrão do antigo
# seletor de estilos em ui_pixelart.py (descontinuado), agora dentro do
# motor vetorial atual.
_estilo_baralho = "padrao"


def set_estilo_baralho(estilo):
    global _estilo_baralho
    _estilo_baralho = estilo


def get_estilo_baralho():
    return _estilo_baralho


def desenhar_carta_vazia(tela, x, y, largura, altura):
    """Slot de carta comunitária ainda não revelada."""
    if _estilo_baralho in baralhos_skins.SKINS:
        baralhos_skins.desenhar_carta_skin(tela, _estilo_baralho, x, y, largura, altura, vazia=True)
        return
    pygame.draw.rect(tela, (255, 255, 255), pygame.Rect(x, y, largura, altura), width=2, border_radius=0)


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
    elif simbolo == "★":  # coringa (Joker)
        pontos = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            raio = tamanho // 2 if i % 2 == 0 else tamanho // 5
            pontos.append((cx + raio * math.cos(ang), cy - raio * math.sin(ang)))
        pygame.draw.polygon(tela, cor, pontos)
    else:  # espadas
        pygame.draw.polygon(tela, cor, [
            (cx, cy - tamanho // 2), (cx + tamanho // 2, cy + tamanho // 4),
            (cx - tamanho // 2, cy + tamanho // 4)
        ])
        pygame.draw.rect(tela, cor, (cx - 2, cy + tamanho // 4, 4, tamanho // 3))


def desenhar_carta(tela, x, y, largura, altura, carta=None, virada_para_baixo=False, destaque=False):
    """Carta pixel art: face "papel" clara (sempre clara, mesmo com o resto
    da UI escuro - é assim que uma carta de baralho de verdade funciona),
    borda grossa reta, sombra sólida deslocada. `borda`/`sombra` seguem a
    "tier" da carta (bot/comunitária/mão)."""
    if _estilo_baralho in baralhos_skins.SKINS:
        return baralhos_skins.desenhar_carta_skin(
            tela, _estilo_baralho, x, y, largura, altura,
            carta=carta, virada_para_baixo=virada_para_baixo, destaque=destaque)

    rect = pygame.Rect(x, y, largura, altura)
    if largura <= 50:
        borda, sombra = 3, (3, 3)
    elif largura <= 80:
        borda, sombra = 4, (4, 4)
    else:
        borda, sombra = 5, (6, 6)
    radius = 0

    dark = _estilo_baralho == "dark"
    cor_borda_padrao = INK if dark else CARTA_INK

    pygame.draw.rect(tela, SOMBRA, rect.move(*sombra), border_radius=radius)

    if virada_para_baixo or carta is None:
        cor_verso = (24, 24, 30) if dark else BLUE
        cor_verso_detalhe = (48, 50, 70) if dark else (130, 160, 232)
        pygame.draw.rect(tela, cor_verso, rect, border_radius=radius)
        pygame.draw.rect(tela, cor_borda_padrao, rect, width=borda, border_radius=radius)
        cx, cy = rect.center
        s = min(largura, altura) * 0.22
        losango = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
        pygame.draw.polygon(tela, cor_verso_detalhe, losango)
        pygame.draw.polygon(tela, cor_borda_padrao, losango, width=2)
        return rect

    eh_joker = carta.naipe == NAIPE_CORINGA
    cor_fundo_face = PURPLE if eh_joker else ((38, 38, 46) if dark else CARTA_FACE)
    pygame.draw.rect(tela, cor_fundo_face, rect, border_radius=radius)
    cor_borda_final = YELLOW if destaque else cor_borda_padrao
    largura_borda_final = borda + (2 if destaque else 0)
    pygame.draw.rect(tela, cor_borda_final, rect, width=largura_borda_final, border_radius=radius)

    if eh_joker:
        cor_texto = INK
    else:
        vermelho = carta.naipe in ("copas", "ouros")
        cor_texto_preta = INK if dark else CARTA_INK
        cor_texto = RED_SUIT if vermelho else cor_texto_preta
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
    pygame.draw.circle(tela, SOMBRA, (cx + 2, cy + 2), raio)
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
    """Mesa retangular de cantos retos (feltro), com sombra sólida deslocada."""
    radius = 0
    pygame.draw.rect(tela, SOMBRA, rect.move(8, 8), border_radius=radius)
    pygame.draw.rect(tela, FELT_DARK, rect, border_radius=radius)
    interno = rect.inflate(-20, -20)
    pygame.draw.rect(tela, FELT, interno, border_radius=radius)
    pygame.draw.rect(tela, INK, rect, width=5, border_radius=radius)


def desenhar_mesa_oval_recorte(tela, rect, largura_recorte=150, profundidade=54):
    """Mesa de poker oval com um recorte (baia) na borda de cima, onde o
    croupiê fica em pé, do lado de fora do feltro. Retorna o `Rect` do recorte
    (meio-topo ancorado na borda superior da mesa)."""
    pygame.draw.ellipse(tela, SOMBRA, rect.move(8, 8))
    pygame.draw.ellipse(tela, FELT_DARK, rect)
    pygame.draw.ellipse(tela, FELT, rect.inflate(-24, -24))
    pygame.draw.ellipse(tela, INK, rect, width=5)

    recorte = pygame.Rect(0, 0, largura_recorte, profundidade)
    recorte.midtop = (rect.centerx, rect.top)
    clip_anterior = tela.get_clip()
    tela.set_clip(pygame.Rect(rect.x, rect.top, rect.width, rect.height).clip(clip_anterior))
    pygame.draw.rect(tela, INK, recorte.inflate(10, 5).move(0, 2))
    pygame.draw.rect(tela, BG, recorte)
    tela.set_clip(clip_anterior)
    return recorte


def desenhar_cropie(tela, cx, cy, progresso=0.0):
    """Croupiê em pé do lado de fora da mesa, visto de cima/de longe: só o topo
    da cabeça (cabelo + viseira) e os ombros aparecem.

    `cy` é o centro da cabeça. `progresso` (0..1) anima o braço estendendo-se
    em direção ao centro da mesa (para baixo na tela) com uma cartinha."""
    r_cabeca = 17
    ombros = pygame.Rect(0, 0, 76, 30)
    ombros.center = (cx, cy - 8)

    # braço (desenhado antes, por trás dos ombros/cabeça)
    t = math.sin(min(1.0, max(0.0, progresso)) * math.pi)  # 0 -> 1 -> 0
    ombro = (cx + 30, cy - 4)
    mao = (ombro[0] - int(10 * t), ombro[1] + 8 + int(34 * t))
    pygame.draw.line(tela, SOMBRA, ombro, mao, 11)
    pygame.draw.line(tela, CROUPIER_COLETE, ombro, mao, 7)
    pygame.draw.circle(tela, CROUPIER_PELE, mao, 6)
    pygame.draw.circle(tela, SOMBRA, mao, 6, 2)
    if 0.12 < progresso < 0.88:
        carta = pygame.Rect(0, 0, 14, 20)
        carta.center = (mao[0] - 4, mao[1] + 12)
        pygame.draw.rect(tela, CARTA_FACE, carta)
        pygame.draw.rect(tela, CARTA_INK, carta, width=1)

    # ombros / colete
    pygame.draw.ellipse(tela, SOMBRA, ombros.move(3, 3))
    pygame.draw.ellipse(tela, CROUPIER_COLETE, ombros)
    pygame.draw.ellipse(tela, SOMBRA, ombros, width=3)

    # orelhas + cabeça (topo): cabelo com repartido
    pygame.draw.circle(tela, CROUPIER_PELE, (cx - r_cabeca, cy + 2), 5)
    pygame.draw.circle(tela, SOMBRA, (cx - r_cabeca, cy + 2), 5, 2)
    pygame.draw.circle(tela, CROUPIER_PELE, (cx + r_cabeca, cy + 2), 5)
    pygame.draw.circle(tela, SOMBRA, (cx + r_cabeca, cy + 2), 5, 2)
    pygame.draw.circle(tela, SOMBRA, (cx + 2, cy + 2), r_cabeca)
    pygame.draw.circle(tela, CROUPIER_CABELO, (cx, cy), r_cabeca)
    pygame.draw.circle(tela, SOMBRA, (cx, cy), r_cabeca, 3)
    pygame.draw.line(tela, SOMBRA, (cx - 3, cy - r_cabeca + 4), (cx - 5, cy + 2), 2)

    # viseira de dealer na frente (lado voltado para a câmera)
    viseira = pygame.Rect(0, 0, r_cabeca * 2 - 6, 9)
    viseira.midbottom = (cx, cy + r_cabeca - 1)
    pygame.draw.rect(tela, MINT, viseira)
    pygame.draw.rect(tela, SOMBRA, viseira, width=2)


def tamanho_janela():
    """(largura, altura) da janela do jogo."""
    superficie = pygame.display.get_surface()
    assert superficie is not None, "pygame.display.set_mode ainda não foi chamado"
    return superficie.get_size()


def desenhar_glow_de_vez(tela, x, y, largura_carta, altura_carta, tempo):
    """Anel pulsante (mint) ao redor de quem está com a vez de agir."""
    pulso = (math.sin(tempo * 4.0) + 1) / 2
    raio_x = largura_carta + 34 + int(pulso * 6)
    raio_y = altura_carta // 2 + 34 + int(pulso * 6)
    alpha = 120 + int(pulso * 100)
    superficie = pygame.Surface((raio_x * 2, raio_y * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(superficie, (*MINT[:3], alpha), (0, 0, raio_x * 2, raio_y * 2), width=5)
    tela.blit(superficie, (x - raio_x, y - raio_y))


# ---------- Overlay de "tela CRT" ----------
_scanlines_cache = None
_scanlines_tamanho = None


def aplicar_scanlines(tela, intensidade=26, passo=3):
    """Chamado uma vez por frame, por cima de tudo (ver main.py:App.executar),
    pra dar o ar de monitor CRT ao estilo Pixel Art Retrô: linhas horizontais
    translúcidas bem sutis. A superfície é gerada uma vez e reaproveitada -
    só é recriada se o tamanho da janela mudar (redimensionar/tela cheia)."""
    global _scanlines_cache, _scanlines_tamanho
    tamanho = tela.get_size()
    if _scanlines_cache is None or _scanlines_tamanho != tamanho:
        largura, altura = tamanho
        overlay = pygame.Surface(tamanho, pygame.SRCALPHA)
        for y in range(0, altura, passo):
            pygame.draw.line(overlay, (0, 0, 0, intensidade), (0, y), (largura, y))
        _scanlines_cache = overlay
        _scanlines_tamanho = tamanho
    tela.blit(_scanlines_cache, (0, 0))
