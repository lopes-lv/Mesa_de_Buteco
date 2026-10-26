"""
editor_widgets.py - Widgets do editor visual de layout (tools/editor_visual.py):
campo numérico digitável, botão -/+ que repete enquanto segurado e caixa de
marcar. Desenhados com as primitivas de core/ui_theme.py, no mesmo estilo
Pixel Art Retrô CRT do jogo, mas em versão compacta (borda fina, sem a sombra
grande dos botões do jogo, que ficaria pesada em controles de 26px).
"""
from typing import Any

import pygame

from core.ui_theme import (
    PANEL, INK, TEXT_MUTED, YELLOW, SOMBRA, LOCKED,
    retangulo_borda, desenhar_texto, obter_fonte,
)
from core.ui_widgets import CampoTexto

ATRASO_REPETICAO = 0.4    # segurar o botão por esse tempo começa a repetir...
INTERVALO_REPETICAO = 0.06  # ...um passo a cada intervalo


def shift_pressionado():
    return bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)


def desenhar_texto_central(tela, texto, rect, tamanho=14, cor=INK, negrito=True, familia="mono"):
    fonte = obter_fonte(tamanho, negrito, familia)
    superficie = fonte.render(texto, True, cor)
    tela.blit(superficie, superficie.get_rect(center=rect.center))


def caber_texto(texto, largura_max, tamanho, negrito=False, familia="body"):
    """Corta `texto` com reticências pra caber em `largura_max` pixels."""
    fonte = obter_fonte(tamanho, negrito, familia)
    if fonte.size(texto)[0] <= largura_max:
        return texto
    while texto and fonte.size(texto + "…")[0] > largura_max:
        texto = texto[:-1]
    return texto + "…"


def quebrar_texto(texto, largura_max, tamanho, negrito=False, familia="body"):
    """Quebra `texto` em linhas que caibam em `largura_max` pixels."""
    fonte = obter_fonte(tamanho, negrito, familia)
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if fonte.size(tentativa)[0] <= largura_max or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


class CampoNumero(CampoTexto):
    """Campo de texto que só aceita dígitos. Fora de foco mostra o valor
    atual; ao receber o clique entra em edição com o valor selecionado (o
    primeiro dígito digitado substitui tudo). Enter ou clicar fora confirma
    (chama `ao_confirmar(int)`), Esc cancela."""

    def __init__(self, rect, ao_confirmar, max_len=4):
        super().__init__(rect, max_len=max_len)
        self.ao_confirmar = ao_confirmar
        self.valor: Any = 0
        self._substituir = False

    def _confirmar(self):
        if self.focado and self.texto:
            self.ao_confirmar(int(self.texto))
        self.focado = False

    def tratar_evento(self, evento):
        """Devolve True se o evento foi consumido pelo campo."""
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            dentro = self.rect.collidepoint(evento.pos)
            if dentro and not self.focado:
                self.focado = True
                self.texto = str(self.valor)
                self._substituir = True
            elif not dentro and self.focado:
                self._confirmar()
            return dentro
        if evento.type == pygame.KEYDOWN and self.focado:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
                self._confirmar()
            elif evento.key == pygame.K_ESCAPE:
                self.focado = False
            elif evento.key == pygame.K_BACKSPACE:
                self.texto = "" if self._substituir else self.texto[:-1]
                self._substituir = False
            elif evento.unicode.isdigit():
                if self._substituir:
                    self.texto = ""
                    self._substituir = False
                if len(self.texto) < self.max_len:
                    self.texto += evento.unicode
            return True
        return False

    def desenhar(self, tela):
        retangulo_borda(tela, self.rect, SOMBRA if self.focado else PANEL,
                        YELLOW if self.focado else TEXT_MUTED, 2)
        if self.focado:
            texto, cor = self.texto, YELLOW
            if self._substituir:
                # "seleção" do valor inteiro, como num campo de texto comum
                fonte = obter_fonte(14, True, "mono")
                largura = fonte.size(texto)[0] + 6
                fundo = pygame.Rect(0, 0, largura, self.rect.height - 8)
                fundo.center = self.rect.center
                pygame.draw.rect(tela, LOCKED, fundo)
        else:
            texto, cor = str(self.valor), INK
        desenhar_texto_central(tela, texto, self.rect, cor=cor)


def cor_para_hex(cor):
    return "#{:02X}{:02X}{:02X}".format(*cor[:3])


class CampoHex(CampoNumero):
    """Variante do CampoNumero para cor em hexadecimal (6 dígitos, com ou sem
    "#"): `ao_confirmar` recebe (r, g, b). Fora de foco mostra `#RRGGBB`."""

    def __init__(self, rect, ao_confirmar):
        super().__init__(rect, ao_confirmar, max_len=6)
        self.valor = (0, 0, 0)

    def _confirmar(self):
        if self.focado and len(self.texto) == 6:
            self.ao_confirmar(tuple(int(self.texto[i:i + 2], 16) for i in (0, 2, 4)))
        self.focado = False

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            dentro = self.rect.collidepoint(evento.pos)
            if dentro and not self.focado:
                self.focado = True
                self.texto = cor_para_hex(self.valor)[1:]
                self._substituir = True
            elif not dentro and self.focado:
                self._confirmar()
            return dentro
        if evento.type == pygame.KEYDOWN and self.focado:
            caractere = evento.unicode.upper()
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
                self._confirmar()
            elif evento.key == pygame.K_ESCAPE:
                self.focado = False
            elif evento.key == pygame.K_BACKSPACE:
                self.texto = "" if self._substituir else self.texto[:-1]
                self._substituir = False
            elif caractere and caractere in "0123456789ABCDEF":
                if self._substituir:
                    self.texto = ""
                    self._substituir = False
                if len(self.texto) < self.max_len:
                    self.texto += caractere
            return True
        return False

    def desenhar(self, tela):
        retangulo_borda(tela, self.rect, SOMBRA if self.focado else PANEL,
                        YELLOW if self.focado else TEXT_MUTED, 2)
        texto = "#" + self.texto if self.focado else cor_para_hex(self.valor)
        desenhar_texto_central(tela, texto, self.rect, cor=YELLOW if self.focado else INK)


def desenhar_amostra_cor(tela, rect, cor):
    """Quadradinho com a cor, borda clara e, por dentro, fina borda escura -
    fica visível tanto pra cores claras quanto escuras."""
    pygame.draw.rect(tela, cor, rect)
    pygame.draw.rect(tela, INK, rect, 2)
    pygame.draw.rect(tela, SOMBRA, rect.inflate(-4, -4), 1)


class SliderCor:
    """Slider de um canal (0 = R, 1 = G, 2 = B) de uma cor. O trilho mostra
    o degradê daquele canal com os outros dois fixos, então dá pra ver pra
    onde a cor vai antes de arrastar."""
    NOMES = ("R", "G", "B")

    def __init__(self, rect, canal):
        self.rect = rect
        self.canal = canal

    def valor_em(self, x):
        return max(0, min(255, round((x - self.rect.x) * 255 / max(1, self.rect.width - 1))))

    def desenhar(self, tela, cor, arrastando=False):
        r = self.rect
        for i in range(r.width):
            componentes = list(cor[:3])
            componentes[self.canal] = i * 255 // max(1, r.width - 1)
            pygame.draw.line(tela, componentes, (r.x + i, r.y), (r.x + i, r.bottom - 1))
        pygame.draw.rect(tela, INK, r, 2)
        x = r.x + cor[self.canal] * (r.width - 1) // 255
        alca = pygame.Rect(0, 0, 10, r.height + 10)
        alca.center = (x, r.centery)
        retangulo_borda(tela, alca, YELLOW if arrastando else INK, SOMBRA, 2)
        desenhar_texto(tela, self.NOMES[self.canal], r.x - 22, r.centery - 8, tamanho=14, negrito=True,
                       familia="mono")
        desenhar_texto(tela, f"{cor[self.canal]:3d}", r.right + 12, r.centery - 8, tamanho=14,
                       familia="mono")


class BotaoRepetidor:
    """Botão pequeno (-/+) que chama `acao(shift)` no clique e, se segurado,
    repete depois de ATRASO_REPETICAO (como segurar uma tecla)."""

    def __init__(self, rect, texto, acao):
        self.rect = rect
        self.texto = texto
        self.acao = acao
        self.segurando = False
        self._tempo = 0.0

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.rect.collidepoint(evento.pos):
            self.segurando = True
            self._tempo = -ATRASO_REPETICAO
            self.acao(shift_pressionado())
            return True
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self.segurando = False
        return False

    def atualizar(self, dt):
        if not self.segurando:
            return
        if not self.rect.collidepoint(pygame.mouse.get_pos()):
            return  # arrastou pra fora: pausa sem soltar
        self._tempo += dt
        while self._tempo >= INTERVALO_REPETICAO:
            self._tempo -= INTERVALO_REPETICAO
            self.acao(shift_pressionado())

    def desenhar(self, tela):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        fundo = YELLOW if self.segurando else (LOCKED if hover else PANEL)
        retangulo_borda(tela, self.rect, fundo, INK, 2)
        desenhar_texto_central(tela, self.texto, self.rect, tamanho=16,
                               cor=SOMBRA if self.segurando else INK)


def desenhar_botao_pequeno(tela, rect, texto, ativo=True, cor=PANEL, tamanho=11):
    """Botão compacto de clique simples (ex.: "PADRÃO" de cada item)."""
    hover = ativo and rect.collidepoint(pygame.mouse.get_pos())
    fundo = (LOCKED if hover else cor) if ativo else SOMBRA
    retangulo_borda(tela, rect, fundo, INK if ativo else LOCKED, 2)
    desenhar_texto_central(tela, texto, rect, tamanho=tamanho, cor=INK if ativo else LOCKED)


def desenhar_seletor(tela, x, y, largura, texto, altura=30):
    """`<` [texto] `>`: devolve (rect_esquerda, rect_direita) pra quem
    trata o clique avançar/voltar a opção."""
    esquerda = pygame.Rect(x, y, altura, altura)
    caixa = pygame.Rect(esquerda.right + 4, y, largura - 2 * (altura + 4), altura)
    direita = pygame.Rect(caixa.right + 4, y, altura, altura)
    desenhar_botao_pequeno(tela, esquerda, "<", tamanho=15)
    retangulo_borda(tela, caixa, SOMBRA, TEXT_MUTED, 2)
    desenhar_texto_central(tela, caber_texto(texto, caixa.width - 12, 12, familia="body"), caixa,
                           tamanho=12, negrito=False, familia="body")
    desenhar_botao_pequeno(tela, direita, ">", tamanho=15)
    return esquerda, direita


def desenhar_caixa_marcar(tela, x, y, texto, marcado, tamanho=14):
    """Caixa de marcar + rótulo; devolve o rect clicável (caixa + texto)."""
    caixa = pygame.Rect(x, y, 22, 22)
    retangulo_borda(tela, caixa, SOMBRA, INK, 2)
    if marcado:
        pygame.draw.rect(tela, YELLOW, caixa.inflate(-10, -10))
    rect_texto = desenhar_texto(tela, texto, caixa.right + 10, caixa.centery - tamanho // 2 - 1,
                                tamanho=tamanho, cor=INK)
    return caixa.union(rect_texto)
