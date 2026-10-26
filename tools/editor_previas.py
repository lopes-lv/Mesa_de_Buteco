"""
editor_previas.py - Prévias do editor visual de layout: para cada chave de
config/layout_padrao.json, desenha o trecho da mesa que ela afeta, em tamanho
real e com as mesmas funções de desenho do jogo (ui_theme.desenhar_carta,
domino_theme.desenhar_peca, ui_theme.desenhar_botao...), reproduzindo a
geometria das telas (holdem/table_screen.py, pifpaf/pifpaf_screen.py,
domino/domino_screen.py). Os valores vêm de `layout.obter()`, que o editor
altera em memória - por isso a prévia acompanha cada clique.

Cada prévia desenha centralizada em (cx, cy) e devolve
`(area_ocupada: pygame.Rect, info: str)`; o editor recorta essa área e reduz
a escala só se ela não couber no painel. `PREVIAS[chave]` diz qual prévia e
qual fundo (feltro da mesa ou fundo da tela) usar.
"""
import pygame

from core import layout
from core.deck import Card
from core.ui_theme import (
    BG, FELT, FELT_DARK, PANEL, INK, SOMBRA, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    RED_SUIT, CARTA_FACE, CARTA_INK,
    desenhar_carta, desenhar_carta_vazia, desenhar_botao, desenhar_kbd, desenhar_badge,
    desenhar_painel, desenhar_texto, desenhar_glow_de_vez, desenhar_avatar, desenhar_mesa,
    get_estilo_baralho, contraste, cor_texto_sobre,
)
from domino.domino_theme import desenhar_peca, desenhar_peca_verso

LARGURA_JANELA_PADRAO = 1280  # main.py:LARGURA_INICIAL, referência pras dicas de largura
SOMBRA_CARTA = 8              # folga pra sombra deslocada não ser cortada no recorte

MAO_HOLDEM = [Card(14, "espadas"), Card(13, "copas")]
COMUNITARIAS = [Card(10, "ouros"), Card(7, "paus"), Card(2, "copas")]
MAO_PIFPAF = [Card(v, n) for v, n in [(3, "copas"), (4, "copas"), (5, "copas"), (9, "paus"),
                                       (9, "ouros"), (9, "espadas"), (11, "espadas"), (12, "espadas"),
                                       (13, "espadas")]]
DESCARTE_PIFPAF = Card(12, "ouros")
MAO_DOMINO = [(6, 6), (2, 5), (0, 3), (4, 4), (1, 6), (3, 5), (2, 2)]


def _dica_borda_carta(largura):
    """A carta dos baralhos Padrão/Dark muda a espessura da borda/sombra por
    faixa de largura (ui_theme.desenhar_carta) - vale avisar perto da faixa."""
    if get_estilo_baralho() not in ("padrao", "dark"):
        return ""
    borda = 3 if largura <= 50 else 4 if largura <= 80 else 5
    return f"  ·  borda {borda}px (muda ao cruzar 50 e 80px de largura)"


def _dica_largura(total, o_que):
    percentual = total * 100 // LARGURA_JANELA_PADRAO
    return f"{o_que}: {total}px de largura ({percentual}% da janela padrão de {LARGURA_JANELA_PADRAO}px)"


def _unir(rects, folga=SOMBRA_CARTA):
    area = rects[0].unionall(rects[1:]) if len(rects) > 1 else rects[0].copy()
    return area.inflate(folga * 2, folga * 2)


# ---------------------------------------------------------------- Hold'em
def previa_holdem_jogador(tela, cx, cy, opcoes):
    """Suas 2 cartas + o painel "Você" à esquerda, ancorado no centro do
    assento (table_screen._desenhar_jogadores/_desenhar_painel_humano): as
    cartas sobem `deslocamento_cartas_jogador` em relação ao painel."""
    largura, altura = layout.obter("holdem.carta_jogador")
    espaco = layout.obter("holdem.espaco_cartas_jogador")
    y_assento = cy + layout.obter("holdem.deslocamento_cartas_jogador") // 2
    y_cartas = y_assento - layout.obter("holdem.deslocamento_cartas_jogador")
    total = 2 * largura + espaco
    x_assento = cx + 100  # o painel fica à esquerda das cartas; desloca o conjunto pra centralizar

    rects = []
    x0 = x_assento - total // 2
    for i, carta in enumerate(MAO_HOLDEM):
        x = x0 + i * (largura + espaco)
        desenhar_carta(tela, x, y_cartas - altura // 2, largura, altura,
                       carta=None if opcoes["virada"] else carta, virada_para_baixo=opcoes["virada"])
        rects.append(pygame.Rect(x, y_cartas - altura // 2, largura, altura))

    painel = pygame.Rect(0, 0, 176, 68)
    painel.right = x_assento - total // 2 - 26
    painel.centery = y_assento
    desenhar_painel(tela, painel, cor=PANEL, deslocamento_sombra=(3, 3))
    desenhar_texto(tela, "Você", painel.centerx, painel.y + 18, tamanho=15, negrito=True, centralizado=True)
    desenhar_texto(tela, "1500", painel.centerx, painel.y + 46, tamanho=13, cor=TEXT_MUTED,
                   centralizado=True, familia="mono")
    rects.append(painel)

    # linha de referência: o painel fica no centro do assento, as cartas sobem
    linha_y = y_assento
    pygame.draw.line(tela, YELLOW, (painel.left - 10, linha_y), (rects[1].right + 14, linha_y), 1)
    desenhar_texto(tela, "assento", rects[1].right + 18, linha_y - 8, tamanho=11, cor=YELLOW, familia="mono")
    rects.append(pygame.Rect(rects[1].right + 14, linha_y - 10, 60, 20))
    return _unir(rects), f"Cartas: {total}px de largura no total{_dica_borda_carta(largura)}"


def previa_holdem_oponente(tela, cx, cy, opcoes):
    largura, altura = layout.obter("holdem.carta_oponente")
    espaco = layout.obter("holdem.espaco_cartas_oponente")
    total = 2 * largura + espaco
    rects = []
    for i in range(2):
        x = cx - total // 2 + i * (largura + espaco)
        virada = not opcoes["virada"]  # oponente: normalmente virada; "virar" mostra a face (showdown)
        desenhar_carta(tela, x, cy - altura // 2, largura, altura,
                       carta=None if virada else MAO_HOLDEM[i], virada_para_baixo=virada)
        rects.append(pygame.Rect(x, cy - altura // 2, largura, altura))
    return _unir(rects), f"Cartas de cada oponente: {total}px de largura{_dica_borda_carta(largura)}"


def previa_comunitarias(tela, cx, cy, opcoes):
    """5 slots (3 reveladas no flop + 2 vazias), centralizados como em
    table_screen._desenhar_comunitarias."""
    largura, altura = layout.obter("holdem.carta_comunitaria")
    espaco = layout.obter("holdem.espaco_comunitarias")
    total = 5 * largura + 4 * espaco
    rects = []
    for i in range(5):
        x = cx - total // 2 + i * (largura + espaco)
        y = cy - altura // 2
        if i < len(COMUNITARIAS):
            desenhar_carta(tela, x, y, largura, altura,
                           carta=None if opcoes["virada"] else COMUNITARIAS[i], virada_para_baixo=opcoes["virada"])
        else:
            desenhar_carta_vazia(tela, x, y, largura, altura)
        rects.append(pygame.Rect(x, y, largura, altura))
    return _unir(rects), _dica_largura(total, "Comunitárias") + _dica_borda_carta(largura)


def previa_botoes_acao(tela, cx, cy, opcoes):
    """Fold/Call/Raise, posicionados como em table_screen._desenhar_controles."""
    tamanho = layout.obter("holdem.botao_acao")
    espaco = layout.obter("holdem.espaco_botoes")
    botoes = [pygame.Rect(0, 0, *tamanho) for _ in range(3)]
    total = 3 * tamanho[0] + 2 * espaco
    botoes[0].midleft = (cx - total // 2, cy)
    botoes[1].midleft = (botoes[0].right + espaco, cy)
    botoes[2].midleft = (botoes[1].right + espaco, cy)
    for rect, texto, cor, cor_texto, tecla in zip(
            botoes, ["Fold", "Call 20", "Raise"], [CORAL, BLUE, MINT], [INK, INK, SOMBRA], "FCR", strict=True):
        desenhar_botao(tela, rect, texto, cor=cor, cor_texto=cor_texto)
        desenhar_kbd(tela, rect.right - 12, rect.bottom - 12, tecla, ancorar="bottomright")
    return _unir(botoes), _dica_largura(total, "Fileira de botões")


def previa_botoes_raise(tela, cx, cy, opcoes):
    """Painel do raise (420x140) com Confirmar/Cancelar, como em
    table_screen._desenhar_slider_raise (o slider fica de fora)."""
    painel = pygame.Rect(0, 0, 420, 140)
    painel.center = (cx, cy)
    desenhar_painel(tela, painel)
    confirmar = pygame.Rect(0, 0, *layout.obter("holdem.botao_confirmar_raise"))
    cancelar = pygame.Rect(0, 0, *layout.obter("holdem.botao_cancelar_raise"))
    confirmar.midleft = (painel.x + 20, painel.bottom - 28)
    cancelar.midright = (painel.right - 20, painel.bottom - 28)
    desenhar_texto(tela, "Valor do raise: 120", painel.x + 20, painel.y + 16, tamanho=15, negrito=True)
    desenhar_botao(tela, confirmar, "Confirmar", tamanho_fonte=15, cor=MINT)
    desenhar_botao(tela, cancelar, "Cancelar", tamanho_fonte=15, cor=PANEL)
    info = "Painel do raise tem 420px fixos"
    if confirmar.right + 10 > cancelar.left:
        info += " - os botões estão se sobrepondo!"
    return _unir([painel, confirmar, cancelar]), info


# ---------------------------------------------------------------- Pif Paf
def previa_mao_pifpaf(tela, cx, cy, opcoes):
    """Bandeja da mão (9 cartas), como em pifpaf_screen._rects_mao_humano."""
    largura, altura = layout.obter("pifpaf.carta_mao")
    espaco = layout.obter("pifpaf.espaco_mao")
    n = len(MAO_PIFPAF)
    total = n * largura + (n - 1) * espaco
    rects = []
    for i, carta in enumerate(MAO_PIFPAF):
        x = cx - total // 2 + i * (largura + espaco)
        desenhar_carta(tela, x, cy - altura // 2, largura, altura,
                       carta=None if opcoes["virada"] else carta, virada_para_baixo=opcoes["virada"])
        rects.append(pygame.Rect(x, cy - altura // 2, largura, altura))
    return _unir(rects), _dica_largura(total, f"Mão de {n} cartas") + _dica_borda_carta(largura)


def previa_monte(tela, cx, cy, opcoes):
    """Monte + descarte no centro da mesa (pifpaf_screen._desenhar_centro_mesa)."""
    largura, altura = layout.obter("pifpaf.carta_monte")
    espaco = layout.obter("pifpaf.espaco_monte")
    monte = pygame.Rect(0, 0, largura, altura)
    monte.center = (cx - espaco - largura // 2, cy)
    descarte = pygame.Rect(0, 0, largura, altura)
    descarte.center = (cx + espaco + largura // 2, cy)
    desenhar_carta(tela, monte.x, monte.y, largura, altura, virada_para_baixo=True)
    desenhar_carta(tela, descarte.x, descarte.y, largura, altura,
                   carta=None if opcoes["virada"] else DESCARTE_PIFPAF, virada_para_baixo=opcoes["virada"])
    desenhar_badge(tela, monte.centerx, monte.bottom + 18, "MONTE (14)", PANEL, cor_texto=INK,
                   tamanho_fonte=10, borda=INK)
    desenhar_badge(tela, descarte.centerx, descarte.bottom + 18, "DESCARTE", PANEL, cor_texto=INK,
                   tamanho_fonte=10, borda=INK)
    selos = pygame.Rect(monte.x, monte.bottom, descarte.right - monte.x, 30)
    return _unir([monte, descarte, selos]), f"Distância entre as cartas: {2 * espaco}px{_dica_borda_carta(largura)}"


def previa_glow_oponente(tela, cx, cy, opcoes):
    """Anel de "vez de jogar" ao redor do painel de um oponente
    (pifpaf_screen._desenhar_jogadores): o tamanho do anel sai daqui."""
    largura, altura = layout.obter("pifpaf.carta_oponente")
    desenhar_glow_de_vez(tela, cx, cy, largura, altura, opcoes["tempo"])
    painel = pygame.Rect(0, 0, 178, 62)
    painel.center = (cx, cy)
    desenhar_painel(tela, painel, cor=PANEL, deslocamento_sombra=(3, 3))
    desenhar_avatar(tela, painel.x + 34, painel.centery, 22, BLUE, "BA")
    desenhar_texto(tela, "Bot Ana", painel.x + 64, painel.y + 12, tamanho=13, negrito=True)
    desenhar_texto(tela, "1500", painel.x + 64, painel.y + 32, tamanho=12, cor=TEXT_MUTED, familia="mono")
    anel = pygame.Rect(0, 0, 2 * (largura + 40), altura + 80)
    anel.center = (cx, cy)
    return (_unir([anel, painel], folga=4),
            "O anel pulsa; seu tamanho acompanha esta \"carta\" (o painel tem 178px fixos)")


def previa_botoes_compra(tela, cx, cy, opcoes):
    """Fileira "Mão fechada" + Comprar Monte + Comprar Descarte
    (pifpaf_screen._desenhar_controles, caso com Mão Fechada liberada)."""
    espaco = layout.obter("pifpaf.espaco_botoes")
    fechada = pygame.Rect(0, 0, *layout.obter("pifpaf.botao_mao_fechada"))
    monte = pygame.Rect(0, 0, *layout.obter("pifpaf.botao_compra"))
    descarte = pygame.Rect(0, 0, *layout.obter("pifpaf.botao_compra"))
    total = fechada.width + monte.width + descarte.width + 2 * espaco
    fechada.midleft = (cx - total // 2, cy)
    monte.midleft = (fechada.right + espaco, cy)
    descarte.midleft = (monte.right + espaco, cy)
    desenhar_botao(tela, fechada, "Bater (2x)", tamanho_fonte=16, cor=YELLOW)
    desenhar_kbd(tela, fechada.right - 14, fechada.bottom - 14, "B", ancorar="bottomright")
    desenhar_botao(tela, monte, "Comprar Monte", tamanho_fonte=16, cor=BLUE, cor_texto=INK)
    desenhar_kbd(tela, monte.right - 14, monte.bottom - 14, "M", ancorar="bottomright")
    desenhar_botao(tela, descarte, "Comprar Descarte", tamanho_fonte=16, cor=MINT)
    desenhar_kbd(tela, descarte.right - 14, descarte.bottom - 14, "D", ancorar="bottomright")
    return _unir([fechada, monte, descarte]), _dica_largura(total, "Fileira com Mão Fechada")


def previa_botoes_jogada(tela, cx, cy, opcoes):
    """Bater + Descartar, com o vão fixo de 30px do jogo
    (pifpaf_screen._desenhar_controles)."""
    bater = pygame.Rect(0, 0, *layout.obter("pifpaf.botao_jogada"))
    descartar = pygame.Rect(0, 0, *layout.obter("pifpaf.botao_jogada"))
    bater.midright = (cx - 15, cy)
    descartar.midleft = (cx + 15, cy)
    desenhar_botao(tela, bater, "Bater", tamanho_fonte=18, cor=YELLOW)
    desenhar_kbd(tela, bater.right - 12, bater.bottom - 12, "B", ancorar="bottomright")
    desenhar_botao(tela, descartar, "Descartar", tamanho_fonte=18, cor=CORAL, cor_texto=INK)
    desenhar_kbd(tela, descartar.right - 12, descartar.bottom - 12, "Enter", ancorar="bottomright")
    return _unir([bater, descartar]), "Confira se o texto não fica por baixo do selo da tecla"


# ---------------------------------------------------------------- Dominó
def previa_mao_domino(tela, cx, cy, opcoes):
    """Bandeja da mão (domino_screen._rects_mao): peças em pé."""
    largura, altura = layout.obter("domino.peca_mao")
    espaco = layout.obter("domino.espaco_mao")
    n = len(MAO_DOMINO)
    total = n * largura + (n - 1) * espaco
    rects = []
    for i, (a, b) in enumerate(MAO_DOMINO):
        x = cx - total // 2 + i * (largura + espaco)
        desenhar_peca(tela, x, cy - altura // 2, largura, altura, a, b, vertical=True)
        rects.append(pygame.Rect(x, cy - altura // 2, largura, altura))
    return _unir(rects), _dica_largura(total, f"Mão de {n} peças")


def previa_linha_domino(tela, cx, cy, opcoes):
    """Um trecho de ramo horizontal na mesa: peça normal deitada
    (comprimento x espessura) e carroça atravessada (espessura x
    comprimento), como domino_screen._tamanho_peca com escala 1."""
    comprimento, espessura = layout.obter("domino.peca_mesa")
    espaco = layout.obter("domino.espaco_mesa")
    pecas = [(3, 5, False), (5, 5, True), (5, 1, False), (1, 6, False)]
    tamanhos = [(espessura, comprimento) if carroca else (comprimento, espessura) for _, _, carroca in pecas]
    total = sum(w for w, _ in tamanhos) + espaco * (len(pecas) - 1)
    x = cx - total // 2
    rects = []
    for (a, b, carroca), (w, h) in zip(pecas, tamanhos, strict=True):
        desenhar_peca(tela, x, cy - h // 2, w, h, a, b, vertical=carroca)
        rects.append(pygame.Rect(x, cy - h // 2, w, h))
        x += w + espaco
    return _unir(rects), "Tamanho máximo: na partida a mesa reduz as peças sozinha quando o ramo não cabe no feltro"


def previa_pilha_escolha(tela, cx, cy, opcoes):
    """Pilha de escolha do início da mão (domino_screen._rects_pilha_escolha):
    até 7 por linha, viradas."""
    largura, altura = layout.obter("domino.peca_pilha_escolha")
    espaco = layout.obter("domino.espaco_pilha_escolha")
    n, por_linha = 9, 7
    linhas = 2
    total_largura = por_linha * largura + (por_linha - 1) * espaco
    total_altura = linhas * altura + (linhas - 1) * espaco
    x0, y0 = cx - total_largura // 2, cy - total_altura // 2
    rects = []
    for i in range(n):
        x = x0 + (i % por_linha) * (largura + espaco)
        y = y0 + (i // por_linha) * (altura + espaco)
        desenhar_peca_verso(tela, x, y, largura, altura)
        rects.append(pygame.Rect(x, y, largura, altura))
    return _unir(rects), _dica_largura(total_largura, "Linha de 7 peças")


# ---------------------------------------------------------------- Paleta, fonte, borda/sombra
# Com que fundo cada cor de texto costuma aparecer (pra calcular contraste).
_FUNDO_DO_TEXTO = {"tinta": PANEL, "texto_apagado": PANEL, "sombra": YELLOW,
                   "carta_tinta": CARTA_FACE, "naipe_vermelho": CARTA_FACE}
_COR_DA_CHAVE = {"fundo": BG, "painel": PANEL, "feltro": FELT, "feltro_escuro": FELT_DARK, "tinta": INK,
                 "texto_apagado": TEXT_MUTED, "amarelo": YELLOW, "coral": CORAL, "azul": BLUE, "verde": MINT,
                 "roxo": PURPLE, "bloqueado": LOCKED, "naipe_vermelho": RED_SUIT, "sombra": SOMBRA,
                 "carta_face": CARTA_FACE, "carta_tinta": CARTA_INK}


def info_contraste(chave):
    """Texto sobre o contraste da cor de `chave` ("cores.*"), com aviso
    quando fica abaixo do mínimo recomendado pra texto (4.5:1)."""
    nome = chave.split(".", 1)[1]
    cor = _COR_DA_CHAVE[nome]
    if nome in _FUNDO_DO_TEXTO:
        fundo = _FUNDO_DO_TEXTO[nome]
        razao = contraste(cor, fundo)
        texto = f"Contraste com o fundo onde aparece: {razao:.1f}:1"
    else:
        claro, escuro = contraste(cor, INK), contraste(cor, SOMBRA)
        razao = max(claro, escuro)
        usa = "escuro" if cor_texto_sobre(cor) is SOMBRA else "claro"
        texto = f"Contraste: texto claro {claro:.1f}:1 · texto escuro {escuro:.1f}:1 · botões usam texto {usa}"
    if razao < 4.5:
        texto += "  ·  BAIXO: abaixo de 4.5:1 o texto fica difícil de ler"
    return texto


def previa_paleta(tela, cx, cy, opcoes):
    """Amostra com todas as cores do tema, desenhada pelas funções do jogo:
    feltro com cartas e peça, painel de jogador com selos e uma fileira de
    botões de cada destaque (inclusive desativado). Serve pras cores e pra
    escala de fonte/borda/sombra."""
    rects = []
    mesa = pygame.Rect(0, 0, 300, 190)
    mesa.topleft = (cx - 330, cy - 150)
    desenhar_mesa(tela, mesa)
    rects.append(mesa)
    largura, altura = 64, 90
    x = mesa.x + 26
    y = mesa.centery - altura // 2
    desenhar_carta(tela, x, y, largura, altura, carta=Card(14, "copas"))
    desenhar_carta(tela, x + 76, y, largura, altura, carta=Card(13, "espadas"))
    desenhar_carta(tela, x + 152, y, largura, altura, virada_para_baixo=True)
    desenhar_peca(tela, mesa.right - 53, mesa.centery - 46, 46, 92, 5, 2, vertical=True)

    painel = pygame.Rect(mesa.right + 30, mesa.y + 10, 270, 82)
    desenhar_painel(tela, painel, cor=PANEL)
    desenhar_avatar(tela, painel.x + 40, painel.centery, 26, YELLOW, "VO")
    desenhar_texto(tela, "Jogador", painel.x + 78, painel.y + 12, tamanho=16, negrito=True)
    desenhar_texto(tela, "1500 fichas", painel.x + 78, painel.y + 34, tamanho=13, cor=TEXT_MUTED, familia="mono")
    desenhar_badge(tela, painel.x + 78, painel.y + 56, "Apostou 20", MINT, cor_texto=SOMBRA, tamanho_fonte=10,
                   ancorar="midleft")
    desenhar_badge(tela, painel.x + 178, painel.y + 56, "Eliminado", LOCKED, cor_texto=TEXT_MUTED,
                   tamanho_fonte=10, ancorar="midleft")
    rects.append(painel)
    selos = pygame.Rect(painel.x, painel.bottom + 18, 270, 30)
    desenhar_badge(tela, selos.x, selos.centery, "POTE: 180", YELLOW, cor_texto=SOMBRA, tamanho_fonte=14,
                   ancorar="midleft", borda=INK, familia="mono")
    desenhar_kbd(tela, selos.x + 150, selos.centery, "Enter", ancorar="midleft")
    rects.append(selos)

    botoes = [("Bater", YELLOW, True), ("Fold", CORAL, True), ("Call", BLUE, True), ("Raise", MINT, True),
              ("Roxo", PURPLE, True), ("Desat.", PANEL, False)]
    largura_botao, espaco = 92, 12
    x0 = cx - (len(botoes) * largura_botao + (len(botoes) - 1) * espaco) // 2
    for i, (texto, cor, ativo) in enumerate(botoes):
        rect = pygame.Rect(x0 + i * (largura_botao + espaco), mesa.bottom + 40, largura_botao, 52)
        desenhar_botao(tela, rect, texto, cor=cor, ativo=ativo, tamanho_fonte=16)
        rects.append(rect)

    chave = opcoes.get("chave", "")
    if chave.startswith("cores."):
        info = info_contraste(chave)
    else:
        info = (f"Fonte {layout.obter('geral.escala_fonte')}%  ·  borda {layout.obter('geral.borda')}px  ·  "
                f"sombra {layout.obter('geral.sombra')}px - confira os textos na MESA COMPLETA (M)")
    return _unir(rects, folga=14), info


def _previa_valor(chave, explicar):
    """Valores sem efeito visual (fichas, tempo dos bots): mostra o valor num
    painel e explica onde ele é usado."""
    def previa(tela, cx, cy, opcoes):
        painel = pygame.Rect(0, 0, 520, 150)
        painel.center = (cx, cy)
        desenhar_painel(tela, painel)
        titulo, detalhe = explicar(layout.obter(chave))
        desenhar_texto(tela, titulo, painel.centerx, painel.y + 52, tamanho=26, negrito=True,
                       centralizado=True, familia="display")
        desenhar_texto(tela, detalhe, painel.centerx, painel.y + 104, tamanho=13, cor=TEXT_MUTED,
                       centralizado=True)
        return _unir([painel]), "Sem efeito visual - vale assim que o jogo recarregar o layout (sozinho ou com F5)"
    return previa


def _segundos(ms):
    return f"{ms / 1000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " s"


# ---------------------------------------------------------------- Botões isolados
def _previa_botao(chave, texto, cor, tamanho_fonte, tecla=None):
    def previa(tela, cx, cy, opcoes):
        rect = pygame.Rect(0, 0, *layout.obter(chave))
        rect.center = (cx, cy)
        desenhar_botao(tela, rect, texto, tamanho_fonte=tamanho_fonte, cor=cor)
        if tecla:
            desenhar_kbd(tela, rect.right - 12, rect.bottom - 12, tecla, ancorar="bottomright")
        return _unir([rect]), f"Botão de {rect.width} x {rect.height}px"
    return previa


# chave -> (função de prévia, cor de fundo, mostra controles de baralho?)
_MESA, _TELA = FELT, BG
PREVIAS = {
    "geral.botao_sair": (_previa_botao("geral.botao_sair", "Sair", PANEL, 14), _TELA, False),
    "geral.botao_continuar": (_previa_botao("geral.botao_continuar", "Continuar", YELLOW, 18), _TELA, False),
    "holdem.carta_jogador": (previa_holdem_jogador, _MESA, True),
    "holdem.espaco_cartas_jogador": (previa_holdem_jogador, _MESA, True),
    "holdem.deslocamento_cartas_jogador": (previa_holdem_jogador, _MESA, True),
    "holdem.carta_oponente": (previa_holdem_oponente, _MESA, True),
    "holdem.espaco_cartas_oponente": (previa_holdem_oponente, _MESA, True),
    "holdem.carta_comunitaria": (previa_comunitarias, _MESA, True),
    "holdem.espaco_comunitarias": (previa_comunitarias, _MESA, True),
    "holdem.botao_acao": (previa_botoes_acao, _TELA, False),
    "holdem.espaco_botoes": (previa_botoes_acao, _TELA, False),
    "holdem.botao_confirmar_raise": (previa_botoes_raise, _TELA, False),
    "holdem.botao_cancelar_raise": (previa_botoes_raise, _TELA, False),
    "pifpaf.carta_mao": (previa_mao_pifpaf, _MESA, True),
    "pifpaf.espaco_mao": (previa_mao_pifpaf, _MESA, True),
    "pifpaf.carta_monte": (previa_monte, _MESA, True),
    "pifpaf.espaco_monte": (previa_monte, _MESA, True),
    "pifpaf.carta_oponente": (previa_glow_oponente, _MESA, False),
    "pifpaf.espaco_botoes": (previa_botoes_compra, _TELA, False),
    "pifpaf.botao_compra": (previa_botoes_compra, _TELA, False),
    "pifpaf.botao_mao_fechada": (previa_botoes_compra, _TELA, False),
    "pifpaf.botao_jogada": (previa_botoes_jogada, _TELA, False),
    "domino.peca_mao": (previa_mao_domino, _MESA, False),
    "domino.espaco_mao": (previa_mao_domino, _MESA, False),
    "domino.peca_mesa": (previa_linha_domino, _MESA, False),
    "domino.espaco_mesa": (previa_linha_domino, _MESA, False),
    "domino.peca_pilha_escolha": (previa_pilha_escolha, _MESA, False),
    "domino.espaco_pilha_escolha": (previa_pilha_escolha, _MESA, False),
    "domino.botao_passar": (_previa_botao("domino.botao_passar", "Passar", CORAL, 16), _TELA, False),
    "geral.escala_fonte": (previa_paleta, _TELA, True),
    "geral.borda": (previa_paleta, _TELA, True),
    "geral.sombra": (previa_paleta, _TELA, True),
    "geral.fichas_iniciais": (_previa_valor("geral.fichas_iniciais", lambda v: (
        f"{v} fichas", "valor inicial do seletor de fichas na tela de Configuração")), _TELA, False),
    "pifpaf.delay_bot_ms": (_previa_valor("pifpaf.delay_bot_ms", lambda v: (
        _segundos(v), "tempo que cada bot leva para jogar no Pif Paf")), _TELA, False),
    "domino.delay_bot_ms": (_previa_valor("domino.delay_bot_ms", lambda v: (
        _segundos(v), "tempo que cada bot leva para jogar no Dominó")), _TELA, False),
}
for _velocidade, _rotulo in (("lenta", "Lenta"), ("normal", "Normal"), ("rapida", "Rápida")):
    _chave = f"geral.delay_bot_{_velocidade}_ms"
    PREVIAS[_chave] = (_previa_valor(_chave, lambda v, rotulo=_rotulo: (
        _segundos(v), f"tempo de jogada dos bots no Hold'em na velocidade {rotulo} (Ajustes)")), _TELA, False)
for _nome in _COR_DA_CHAVE:
    PREVIAS[f"cores.{_nome}"] = (previa_paleta, _TELA, True)
