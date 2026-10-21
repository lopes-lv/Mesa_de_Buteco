"""
editor_mesa.py - Prévia da mesa completa do editor visual (Fase 3 do plano em
../.Viana/plano-editor-visual-poker-game.md).

Em vez de imitar a mesa, usa as telas de verdade do jogo
(holdem/table_screen.py, pifpaf/pifpaf_screen.py, domino/domino_screen.py):
monta uma partida contra bots com semente fixa (via os próprios
`App.iniciar_partida*` de main.py, sobre um App falso), deixa o "Você" jogar
como bot até chegar na cena pedida (ex.: "sua vez no flop") e congela ali.
Depois, a cada mudança de valor, chama `tela.desenhar()` numa superfície do
tamanho da resolução escolhida - como as telas leem core/layout.py na hora
do desenho, a prévia acompanha cada clique sem simular de novo.

Durante o desenho, as funções de desenho que as telas importaram
(desenhar_carta, desenhar_botao, desenhar_peca, desenhar_painel...) são
trocadas por versões que também anotam o retângulo de cada elemento; com
isso dá pra apontar o que sai da tela ou se sobrepõe (`calcular_alertas`).

Dois desvios do jogo, isolados aqui: `pygame.display.get_surface()` passa a
devolver a superfície da prévia (algumas telas medem a janela por ele) e
`pygame.mouse.get_pos()` fica fora da tela (pra não acender hover por acaso).
"""
import contextlib
import random

import pygame

import main as jogo
from core import layout, ui_theme
from core.settings import Settings
from core.ui_theme import obter_fonte
from holdem import table_screen
from holdem.game_logic import TIPO_HUMANO_LOCAL
from pifpaf import pifpaf_screen
from domino import domino_screen
from domino.domino_logic import FASE_JOGANDO

RESOLUCOES = [(1280, 800), (1024, 768), (1366, 768), (1600, 900), (1920, 1080)]
JOGADORES = {"holdem": (2, 8), "pifpaf": (2, 8), "domino": (3, 4)}
JOGADORES_PADRAO = {"holdem": 6, "pifpaf": 6, "domino": 4}
NOMES_MODO = {"holdem": "Hold'em", "pifpaf": "Pif Paf", "domino": "Dominó"}
MODULOS_TELA = {"holdem": table_screen, "pifpaf": pifpaf_screen, "domino": domino_screen}

PASSO_SIMULACAO = 0.05
MAX_PASSOS = 6000
SEMENTES = range(1, 41)  # tenta sementes em ordem até achar a cena (determinístico)


class AppFalso:
    """O mínimo de main.App que as telas de mesa usam."""

    def __init__(self):
        self.settings = Settings()
        self.settings.velocidade_bots = "rapida"
        self.settings.selecao_automatica_pecas = True
        self.jogo_finalizado = False
        self.nome_vencedor = None
        self.tela_atual = None

    def finalizar_jogo(self, nome_vencedor):
        self.jogo_finalizado = True
        self.nome_vencedor = nome_vencedor

    def ir_para_menu(self):
        pass


@contextlib.contextmanager
def _ambiente_de_desenho(superficie):
    """Faz as telas enxergarem `superficie` como a janela e o mouse longe."""
    original_superficie = pygame.display.get_surface
    original_mouse = pygame.mouse.get_pos
    pygame.display.get_surface = lambda: superficie
    pygame.mouse.get_pos = lambda: (-10000, -10000)
    try:
        yield
    finally:
        pygame.display.get_surface = original_superficie
        pygame.mouse.get_pos = original_mouse


# ---------------------------------------------------------------- Cenas
def _vez_do_humano(tela, jogador):
    return jogador is not None and jogador.id == tela.id_humano


def _holdem_flop(tela):
    rodada = tela.table.rodada_atual
    return (rodada is not None and len(tela.table.comunitarias) >= 3
            and _vez_do_humano(tela, rodada.jogador_da_vez()))


def _holdem_preflop_com_aposta(tela):
    """Sua vez no pré-flop já tendo apostado (blind): mostra o selo da sua aposta."""
    rodada = tela.table.rodada_atual
    jogador = rodada.jogador_da_vez() if rodada is not None else None
    return (rodada is not None and not tela.table.comunitarias and _vez_do_humano(tela, jogador)
            and jogador.aposta_rodada > 0)


def _abrir_raise(tela):
    tela.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, mod=0, unicode="r"))


def _pifpaf_comprar(tela):
    mesa = tela.mesa
    return (_vez_do_humano(tela, mesa.jogador_da_vez()) and mesa.pode_comprar() and bool(mesa.descarte))


def _pifpaf_descartar(tela):
    mesa = tela.mesa
    return _vez_do_humano(tela, mesa.jogador_da_vez()) and not mesa.pode_comprar()


def _pecas_na_mesa(mesa):
    return 0 if mesa.mesa_vazia() else 1 + sum(len(ramo) for ramo in mesa.ramos.values())


def _domino_cruz(tela):
    mesa = tela.mesa
    return (tela.fase_mao == FASE_JOGANDO and _vez_do_humano(tela, mesa.jogador_da_vez())
            and _pecas_na_mesa(mesa) >= 8 and bool(mesa.ramos.get("cima") or mesa.ramos.get("baixo"))
            and bool(mesa.jogadas_possiveis(mesa.jogador_da_vez())))


def _domino_passar(tela):
    mesa = tela.mesa
    jogador = mesa.jogador_da_vez()
    return (tela.fase_mao == FASE_JOGANDO and _vez_do_humano(tela, jogador)
            and not mesa.mesa_vazia() and not mesa.jogadas_possiveis(jogador))


# modo -> [(nome da cena, condição pra parar, ajuste depois de parar)]
CENAS = {
    "holdem": [("Sua vez no flop", _holdem_flop, None),
               ("Raise aberto", _holdem_flop, _abrir_raise),
               ("Sua vez no pré-flop, com aposta", _holdem_preflop_com_aposta, None)],
    "pifpaf": [("Sua vez: comprar", _pifpaf_comprar, None),
               ("Sua vez: descartar/bater", _pifpaf_descartar, None)],
    "domino": [("Sua vez, mesa em cruz", _domino_cruz, None),
               ("Sem jogada (botão Passar)", _domino_passar, None)],
}


def _nova_partida(modo, n_jogadores):
    app = AppFalso()
    n_bots = n_jogadores - 1
    if modo == "holdem":
        jogo.App.iniciar_partida(app, n_bots)
    elif modo == "pifpaf":
        jogo.App.iniciar_partida_pifpaf(app, n_bots)
    else:
        jogo.App.iniciar_partida_domino(app, n_bots)
    return app.tela_atual


def _mao_terminou(tela):
    if hasattr(tela, "table"):
        return tela.resultados_showdown is not None or tela.mensagem_vencedor_por_fold is not None
    return tela.mesa.resultado_mao is not None


def simular_cena(modo, n_jogadores, indice_cena, superficie):
    """Devolve a tela do jogo congelada na cena pedida, ou None se nenhuma
    semente chegou lá. O "Você" joga como bot só durante a simulação."""
    _, condicao, ajuste = CENAS[modo][indice_cena]
    estado_random = random.getstate()
    try:
        with _ambiente_de_desenho(superficie):
            for semente in SEMENTES:
                random.seed(semente)
                tela = _nova_partida(modo, n_jogadores)
                humano = tela.table.jogadores[0] if modo == "holdem" else tela.mesa.jogadores[0]
                tipo_original = humano.tipo
                humano.tipo = "bot"
                for _ in range(MAX_PASSOS):
                    if tela.app.jogo_finalizado:
                        break
                    if not _mao_terminou(tela) and condicao(tela):
                        humano.tipo = tipo_original
                        tela.timer_bot = 0.0
                        if ajuste:
                            ajuste(tela)
                        return tela
                    if _mao_terminou(tela):
                        tela._comecar_proxima_mao_ou_finalizar()
                    tela.atualizar(PASSO_SIMULACAO)
                humano.tipo = TIPO_HUMANO_LOCAL
    finally:
        random.setstate(estado_random)
    return None


# ---------------------------------------------------------------- Registro do que foi desenhado
class Elemento:
    __slots__ = ("tipo", "rect", "descricao", "rect_texto")

    def __init__(self, tipo, rect, descricao, rect_texto=None):
        self.tipo, self.rect, self.descricao, self.rect_texto = tipo, pygame.Rect(rect), descricao, rect_texto


@contextlib.contextmanager
def _registrando(modulo, elementos):
    """Troca as funções de desenho que `modulo` importou por versões que
    anotam cada elemento desenhado em `elementos`."""
    def embrulhar(nome, anotar):
        original = getattr(modulo, nome)

        def funcao(*args, **kwargs):
            resultado = original(*args, **kwargs)
            anotar(resultado, *args, **kwargs)
            return resultado
        return nome, original, funcao

    def carta(_, tela, x, y, largura, altura, *args, **kwargs):
        elementos.append(Elemento("carta", (x, y, largura, altura), f"carta {largura}x{altura}"))

    def peca(_, tela, x, y, largura, altura, *args, **kwargs):
        elementos.append(Elemento("peca", (x, y, largura, altura), f"peça {largura}x{altura}"))

    def botao(_, tela, rect, texto, *args, **kwargs):
        tamanho = kwargs.get("tamanho_fonte", 18)
        largura_txt, altura_txt = obter_fonte(tamanho, True, "display").size(texto.upper())
        rect_texto = pygame.Rect(0, 0, largura_txt, altura_txt)
        rect_texto.center = rect.center
        elementos.append(Elemento("botao", rect, f"botão \"{texto.upper()}\"", rect_texto))

    def painel(_, tela, rect, *args, **kwargs):
        elementos.append(Elemento("painel", rect, f"painel {rect.width}x{rect.height}"))

    def kbd(resultado, tela, x, y, texto, *args, **kwargs):
        elementos.append(Elemento("kbd", resultado, f"selo {texto.upper()}"))

    def badge(resultado, tela, x, y, texto, *args, **kwargs):
        elementos.append(Elemento("selo", resultado, f"selo \"{texto}\""))

    anotadores = {"desenhar_carta": carta, "desenhar_carta_vazia": carta, "desenhar_peca": peca,
                  "desenhar_peca_verso": peca, "desenhar_botao": botao, "desenhar_painel": painel,
                  "desenhar_kbd": kbd, "desenhar_badge": badge}
    trocas = [embrulhar(nome, anotar) for nome, anotar in anotadores.items() if hasattr(modulo, nome)]
    for nome, _, funcao in trocas:
        setattr(modulo, nome, funcao)
    try:
        yield
    finally:
        for nome, original, _ in trocas:
            setattr(modulo, nome, original)


def desenhar_mesa(tela_jogo, modo, superficie):
    """Desenha a tela do jogo em `superficie` (com as scanlines, como no
    jogo) e devolve a lista de elementos desenhados."""
    elementos = []
    with _ambiente_de_desenho(superficie), _registrando(MODULOS_TELA[modo], elementos):
        tela_jogo.desenhar(superficie)
    ui_theme.aplicar_scanlines(superficie)
    return elementos


# ---------------------------------------------------------------- Alertas
_SOBREPOSICAO_PROIBIDA = {("carta", "carta"), ("peca", "peca"), ("botao", "botao"), ("botao", "carta"),
                          ("botao", "peca"), ("carta", "peca")}
_COM_PAINEL = {"carta", "peca", "botao"}


def _lados_fora(rect, area):
    lados = []
    if rect.top < area.top:
        lados.append("de cima")
    if rect.bottom > area.bottom:
        lados.append("de baixo")
    if rect.left < area.left:
        lados.append("da esquerda")
    if rect.right > area.right:
        lados.append("da direita")
    return " e ".join(lados)


class Alerta:
    """`nivel` "erro": algo sai da tela, se sobrepõe ou esconde texto.
    `nivel` "info": um painel desenhado por cima (ex.: o modal do raise)
    cobre o que estava embaixo - em geral proposital, mas bom saber."""
    __slots__ = ("nivel", "mensagem", "rects")

    def __init__(self, nivel, mensagem, rects):
        self.nivel, self.mensagem, self.rects = nivel, mensagem, rects


def calcular_alertas(elementos, tamanho_tela):
    """Alertas da cena, erros primeiro, sem repetir mensagem igual.
    `elementos` está na ordem de desenho - o que vem depois fica por cima."""
    area = pygame.Rect((0, 0), tamanho_tela)
    alertas, por_mensagem = [], {}

    def alertar(nivel, mensagem, *rects):
        # mesma mensagem de novo (ex.: dois pares carta/painel do mesmo tamanho):
        # um alerta só, mas com os retângulos de todas as ocorrências
        if mensagem in por_mensagem:
            por_mensagem[mensagem].rects.extend(r for r in rects if r not in por_mensagem[mensagem].rects)
            return
        por_mensagem[mensagem] = Alerta(nivel, mensagem, list(rects))
        alertas.append(por_mensagem[mensagem])

    for el in elementos:
        if el.tipo != "kbd" and not area.contains(el.rect):
            alertar("erro", f"{el.descricao} sai pela borda {_lados_fora(el.rect, area)} da tela", el.rect)

    principais = [el for el in elementos if el.tipo in ("carta", "peca", "botao", "painel")]
    # Modal = painel desenhado depois do primeiro botão: nas 3 telas a ordem é
    # mesa/jogadores/histórico -> botão "Sair" -> mão e controles -> modais
    # (painel do raise, resultado da mão). Painel modal cobrindo o que está
    # embaixo é proposital (aviso informativo); um painel fixo, como o
    # histórico, cobrindo cartas é problema e segue as regras normais.
    primeiro_botao = next((j for j, el in enumerate(principais) if el.tipo == "botao"), len(principais))
    paineis = [(j, el) for j, el in enumerate(principais) if el.tipo == "painel" and j > primeiro_botao]
    cobertos = {}  # painel desenhado por cima -> elementos que ele cobre
    for i, a in enumerate(principais):
        for j in range(i + 1, len(principais)):
            b = principais[j]
            if not a.rect.colliderect(b.rect):
                continue
            # b é (ou está dentro de) um painel desenhado depois de `a` que o cobre:
            # `a` só ficou embaixo de um painel por cima - vira um aviso só, por painel
            cobridor = next((p for k, p in paineis if i < k <= j and p.rect.contains(b.rect)
                             and p.rect.colliderect(a.rect)), None)
            if cobridor is not None:
                if a is not cobridor:  # inclui painel por cima de painel (ex.: raise sobre o histórico)
                    cobertos.setdefault(id(cobridor), (cobridor, []))[1].append(a)
                continue
            par = tuple(sorted((a.tipo, b.tipo)))
            if par in _SOBREPOSICAO_PROIBIDA:
                alertar("erro", f"{a.descricao} se sobrepõe a {b.descricao}", a.rect, b.rect)
            elif "painel" in par and (par[0] if par[1] == "painel" else par[1]) in _COM_PAINEL:
                painel_, outro = (a, b) if a.tipo == "painel" else (b, a)
                if not painel_.rect.contains(outro.rect):
                    alertar("erro", f"{outro.descricao} invade um {painel_.descricao}", outro.rect, painel_.rect)

    # Selo sobre painel: problema, a não ser que esteja inteiro dentro dele
    # (status "Apostou 20") ou preso na borda dele, com o centro em cima da
    # borda (SB/BB no canto do painel) - os dois são propositais.
    for selo in (el for el in elementos if el.tipo == "selo"):
        for painel_ in (el for el in elementos if el.tipo == "painel"):
            if not selo.rect.colliderect(painel_.rect) or painel_.rect.contains(selo.rect):
                continue
            cx, cy = selo.rect.center
            p = painel_.rect
            na_borda = ((abs(cx - p.left) <= 2 or abs(cx - p.right) <= 2) and p.top - 2 <= cy <= p.bottom + 2) or \
                       ((abs(cy - p.top) <= 2 or abs(cy - p.bottom) <= 2) and p.left - 2 <= cx <= p.right + 2)
            if not na_borda:
                alertar("erro", f"{selo.descricao} se sobrepõe a um {painel_.descricao}", selo.rect, p)
        for outro in (el for el in elementos if el.tipo in ("botao", "carta", "peca")):
            if selo.rect.colliderect(outro.rect):
                alertar("erro", f"{selo.descricao} se sobrepõe a {outro.descricao}", selo.rect, outro.rect)

    for botao in (el for el in elementos if el.tipo == "botao"):
        for selo in (el for el in elementos if el.tipo == "kbd"):
            if botao.rect.colliderect(selo.rect) and botao.rect_texto.colliderect(selo.rect):
                alertar("erro", f"texto do {botao.descricao} fica por baixo do {selo.descricao}",
                        botao.rect_texto, selo.rect)

    for painel_, embaixo in cobertos.values():
        nomes = list(dict.fromkeys(el.descricao for el in embaixo))
        alertar("info", f"{painel_.descricao} fica por cima de: {', '.join(nomes)}", painel_.rect)
    return sorted(alertas, key=lambda alerta: alerta.nivel != "erro")


def elementos_do_item(elementos, chave):
    """Elementos que, pelo tamanho, são do item selecionado (pra destacar na
    mesa). Só itens de tamanho (largura, altura); "peca_mesa" fica de fora
    porque a mesa do Dominó reduz a escala das peças."""
    valor = layout.obter(chave)
    if not isinstance(valor, tuple) or chave == "domino.peca_mesa":
        return []
    return [el.rect for el in elementos if el.tipo in ("carta", "peca", "botao") and el.rect.size == valor]
