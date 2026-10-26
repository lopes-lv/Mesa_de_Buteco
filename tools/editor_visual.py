"""
editor_visual.py - Editor visual de layout do PixelPoker (Fases 2 e 3 do
plano em ../.Viana/plano-editor-visual-poker-game.md).

Execute a partir da pasta do projeto:  python tools/editor_visual.py

Lista as variáveis de config/layout_padrao.json agrupadas por modo; cada uma
tem botões -/+ (Shift = passo 5x maior, segurar repete), campo numérico
digitável e "PADRÃO" para voltar ao valor original. À direita, duas vistas:
- ITEM: o trecho da mesa afetado, em tamanho real (tools/editor_previas.py);
- MESA COMPLETA: a tela de verdade do jogo numa cena simulada, na resolução
  escolhida, com alertas do que sai da tela ou se sobrepõe
  (tools/editor_mesa.py). O número de problemas aparece na aba mesmo
  enquanto se edita na vista ITEM.
"Salvar" grava config/layout.json (só o que difere do padrão) via
core/layout.py - um jogo aberto percebe o arquivo novo e recarrega sozinho (ou F5).

Nada aqui altera código do jogo: o editor só mexe nos valores em memória de
core/layout.py e no arquivo de ajustes.
"""
import contextlib
import os
import sys

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_PROJETO not in sys.path:
    sys.path.insert(0, PASTA_PROJETO)

import pygame  # noqa: E402

from core import layout, ui_theme  # noqa: E402
from core.settings import ORDEM_BARALHO_SKINS, ROTULOS_BARALHO_SKIN  # noqa: E402
from core.ui_theme import (  # noqa: E402
    BG, PANEL, INK, SOMBRA, TEXT_MUTED, YELLOW, CORAL, MINT, LOCKED, BLUE, PURPLE,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_badge, desenhar_kbd,
    retangulo_borda, aplicar_scanlines, obter_fonte,
)
from core.ui_widgets import CampoTexto  # noqa: E402
from tools import editor_mesa  # noqa: E402
from tools.editor_previas import PREVIAS  # noqa: E402
from tools.editor_widgets import (  # noqa: E402
    CampoNumero, CampoHex, BotaoRepetidor, SliderCor, desenhar_botao_pequeno, desenhar_caixa_marcar,
    desenhar_seletor, desenhar_amostra_cor, cor_para_hex, caber_texto, quebrar_texto, shift_pressionado,
)

LARGURA_INICIAL, ALTURA_INICIAL = 1280, 800
FPS = 60
MULTIPLICADOR_SHIFT = 5

GRUPOS = [("holdem", "HOLD'EM"), ("pifpaf", "PIF PAF"), ("domino", "DOMINÓ"), ("geral", "GERAL"),
          ("cores", "CORES")]

ALTURA_LINHA = 66
ALTURA_ABAS = 44
MARGEM = 20
ALTURA_RODAPE = 104


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


def eh_cor(chave):
    return chave.startswith("cores.")


def trava_proporcao(chave):
    """Só cartas e peças mantêm proporção (um botão mais largo quase nunca
    deve ficar mais alto junto)."""
    nome = chave.split(".", 1)[1]
    return nome.startswith(("carta_", "peca_"))


class LinhaItem:
    """Uma variável na lista: rótulo, chave e, por dimensão, [-] [campo] [+],
    mais o botão PADRÃO. Os rects são reposicionados a cada desenho."""

    def __init__(self, editor, chave):
        self.chave = chave
        self.meta = layout.metadados(chave)
        self.eh_cor = eh_cor(chave)
        self.amostra = pygame.Rect(0, 0, 40, 28)
        self.campo_hex = CampoHex(pygame.Rect(0, 0, 96, 28),
                                  lambda rgb: editor.definir_cor(chave, rgb)) if self.eh_cor else None
        dimensoes = 0 if self.eh_cor else (len(self.meta["valor"]) if isinstance(self.meta["valor"], list) else 1)
        self.campos, self.menos, self.mais = [], [], []
        for indice in range(dimensoes):
            self.campos.append(CampoNumero(
                pygame.Rect(0, 0, 58, 28),
                lambda numero, i=indice: editor.definir_dimensao(chave, i, numero)))
            self.menos.append(BotaoRepetidor(
                pygame.Rect(0, 0, 28, 28), "-",
                lambda shift, i=indice: editor.ajustar(chave, i, -1, shift)))
            self.mais.append(BotaoRepetidor(
                pygame.Rect(0, 0, 28, 28), "+",
                lambda shift, i=indice: editor.ajustar(chave, i, +1, shift)))
        self.botao_padrao = pygame.Rect(0, 0, 70, 28)
        self.rect = pygame.Rect(0, 0, 0, ALTURA_LINHA)

    def widgets(self):
        return self.campos + self.menos + self.mais + ([self.campo_hex] if self.campo_hex else [])

    def campos_texto(self):
        """Campos que recebem teclado (numéricos e o hexadecimal)."""
        return self.campos + ([self.campo_hex] if self.campo_hex else [])

    def posicionar(self, rect):
        self.rect = rect
        y = rect.y + 32
        x = rect.right - 10 - self.botao_padrao.width
        self.botao_padrao.topleft = (x, y)
        x -= 14
        if self.campo_hex is not None:  # só as linhas de cor têm campo hexadecimal
            self.campo_hex.rect.topright = (x, y)
            self.amostra.topright = (self.campo_hex.rect.left - 8, y)
            return
        for indice in reversed(range(len(self.campos))):
            self.mais[indice].rect.topright = (x, y)
            self.campos[indice].rect.topright = (self.mais[indice].rect.left - 3, y)
            self.menos[indice].rect.topright = (self.campos[indice].rect.left - 3, y)
            x = self.menos[indice].rect.left - (26 if indice > 0 else 0)

    def inicio_controles(self):
        return self.amostra.left if self.eh_cor else self.menos[0].rect.left


class EditorVisual:
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(400, 50)
        self.tela = pygame.display.set_mode((LARGURA_INICIAL, ALTURA_INICIAL), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.rodando = True
        self.tempo = 0.0

        layout.carregar()
        # A interface do editor usa sempre o tema PADRÃO (cores, fonte, borda),
        # pra continuar legível mesmo com um tema editado maluco; só as prévias
        # usam o tema editado (ver _tema_editado).
        ui_theme.aplicar_tema(layout.padrao)
        self.salvos = self._instantaneo()
        self.proporcoes = {}  # chave -> altura/largura travada enquanto "manter proporção" estiver ligado
        self.manter_proporcao = True
        self.virada = False
        self.indice_skin = 0
        ui_theme.set_estilo_baralho(ORDEM_BARALHO_SKINS[self.indice_skin])

        self.mensagem, self.cor_mensagem, self.tempo_mensagem = "", INK, 0.0
        self.confirmando_saida = False

        self.abas = {}
        self.botao_salvar = pygame.Rect(0, 0, 240, 50)
        self.botao_descartar = pygame.Rect(0, 0, 220, 50)
        self.botao_restaurar = pygame.Rect(0, 0, 200, 50)
        self.botao_presets = pygame.Rect(0, 0, 150, 50)

        # janela de presets (Fase 5)
        self.dialogo_presets = False
        self.lista_presets = []
        self.campo_nome_preset = CampoTexto(pygame.Rect(0, 0, 260, 44), placeholder="nome do preset", max_len=30)
        self.botoes_presets = {}   # "aplicar:<nome>" / "salvar" / "pasta" / "fechar" -> rect
        self.aviso_presets = None
        self.rect_proporcao = pygame.Rect(0, 0, 0, 0)
        self.rect_virar = pygame.Rect(0, 0, 0, 0)
        self.seletores = {}  # nome -> (rect "<", rect ">", função(direcao)), refeito a cada desenho
        self.sliders = []    # SliderCor da cor selecionada, refeitos a cada desenho
        self.slider_arrastando = None  # canal (0-2) sendo arrastado
        self.dialogo_botoes = {}
        self.area_lista = pygame.Rect(0, 0, 0, 0)

        # vista "mesa completa" (Fase 3)
        self.vista = "item"
        self.abas_vista = {}
        self.rect_canvas_mesa = pygame.Rect(0, 0, 0, 0)
        self.mesa_ampliada = False
        self.modo_mesa_geral = "holdem"  # nas abas GERAL e CORES, qual jogo mostrar
        self.jogadores = dict(editor_mesa.JOGADORES_PADRAO)
        self.cena = {modo: 0 for modo in editor_mesa.CENAS}
        self.indice_resolucao = 0
        self._telas_simuladas = {}   # (modo, jogadores, cena, resolução) -> tela do jogo congelada (ou None)
        self._render_mesa = (None, None)  # (chave do estado, (superfície, elementos, alertas))

        self.grupo = None
        self.selecionar_grupo("holdem")

    # ---------------------------------------------------------------- Estado
    def _instantaneo(self):
        return {chave: layout.obter(chave) for chave in layout.chaves()}

    def nao_salvas(self):
        return [chave for chave in layout.chaves() if layout.obter(chave) != self.salvos[chave]]

    def avisar(self, texto, cor=INK):
        self.mensagem, self.cor_mensagem, self.tempo_mensagem = texto, cor, 4.0

    def selecionar_grupo(self, grupo):
        self._confirmar_campos()
        self.grupo = grupo
        self.linhas = [LinhaItem(self, chave) for chave in layout.chaves() if chave.startswith(grupo + ".")]
        self.selecionada = 0
        self.rolagem = 0

    def linha_selecionada(self):
        return self.linhas[self.selecionada]

    def _confirmar_campos(self):
        for linha in getattr(self, "linhas", []):
            for campo in linha.campos_texto():
                campo._confirmar()

    def _campo_focado(self):
        for linha in self.linhas:
            for campo in linha.campos_texto():
                if campo.focado:
                    return campo
        return None

    @contextlib.contextmanager
    def _tema_editado(self):
        """Durante o bloco, o ui_theme usa os valores em edição (pras
        prévias); ao sair, volta ao tema padrão da interface do editor."""
        ui_theme.aplicar_tema(layout.obter)
        try:
            yield
        finally:
            ui_theme.aplicar_tema(layout.padrao)

    # ---------------------------------------------------------------- Alteração de valores
    def ajustar(self, chave, indice, sinal, shift=False):
        passo = layout.metadados(chave).get("passo", 1) * (MULTIPLICADOR_SHIFT if shift else 1)
        if eh_cor(chave):  # em cor, -/+ (setas, roda) escurece/clareia os 3 canais juntos
            self.definir_cor(chave, tuple(c + sinal * passo for c in layout.obter(chave)))
            return
        valor = layout.obter(chave)
        atual = valor[indice] if isinstance(valor, tuple) else valor
        self.definir_dimensao(chave, indice, atual + sinal * passo)

    def definir_dimensao(self, chave, indice, numero):
        """Muda uma dimensão (0 = largura, 1 = altura) de `chave`. Com
        "manter proporção" ligado (só cartas/peças), a outra acompanha pela
        razão que o item tinha quando começou a ser editado; senão, a razão
        é esquecida."""
        meta = layout.metadados(chave)
        valor = layout.obter(chave)
        if not isinstance(valor, tuple):
            layout.definir(chave, numero)
            return
        novo = list(valor)
        minimo, maximo = meta.get("min"), meta.get("max")
        if minimo:
            numero = max(minimo[indice], numero)
        if maximo:
            numero = min(maximo[indice], numero)
        novo[indice] = numero
        if self.manter_proporcao and trava_proporcao(chave) and len(novo) == 2:
            if chave not in self.proporcoes:
                self.proporcoes[chave] = valor[1] / valor[0]
            razao = self.proporcoes[chave]
            if indice == 0:
                novo[1] = round(numero * razao)
            else:
                novo[0] = round(numero / razao)
        else:
            self.proporcoes.pop(chave, None)
        layout.definir(chave, novo)

    def definir_cor(self, chave, rgb):
        layout.definir(chave, [max(0, min(255, int(c))) for c in rgb])

    def definir_canal(self, chave, canal, valor):
        rgb = list(layout.obter(chave))
        rgb[canal] = valor
        self.definir_cor(chave, rgb)

    def restaurar_item(self, chave):
        layout.restaurar_padrao(chave)
        self.proporcoes.pop(chave, None)

    def salvar(self):
        self._confirmar_campos()
        caminho = layout.salvar()
        self.salvos = self._instantaneo()
        alterados = sum(1 for chave in layout.chaves() if layout.obter(chave) != layout.padrao(chave))
        self.avisar(f"Salvo em {os.path.relpath(caminho, PASTA_PROJETO)} ({alterados} itens fora do padrão) - "
                    f"o jogo aberto recarrega sozinho (ou aperte F5 nele)", MINT)

    def descartar(self):
        self._confirmar_campos()
        layout.recarregar()
        self.proporcoes.clear()
        self.avisar("Alterações descartadas: valores recarregados do disco", YELLOW)

    def restaurar_tudo(self):
        self._confirmar_campos()
        layout.restaurar_padrao()
        self.proporcoes.clear()
        self.avisar("Todos os itens voltaram ao padrão - clique em Salvar para gravar", YELLOW)

    # ---------------------------------------------------------------- Presets
    def abrir_presets(self):
        self._confirmar_campos()
        self.lista_presets = layout.listar_presets()
        self.aviso_presets = None
        self.campo_nome_preset.texto = ""
        self.dialogo_presets = True

    def aplicar_preset(self, nome):
        if layout.carregar_preset(nome):
            self.proporcoes.clear()
            self.dialogo_presets = False
            self.avisar(f'Preset "{nome}" aplicado - confira na MESA COMPLETA e clique em Salvar pra usar no jogo',
                        YELLOW)

    def salvar_preset(self):
        nome = self.campo_nome_preset.texto.strip()
        caminho = layout.salvar_preset(nome)
        if caminho is None:
            self.aviso_presets = ("Dê um nome com letras ou números", CORAL)
            return
        self.campo_nome_preset.texto = ""
        self.campo_nome_preset.focado = False
        self.lista_presets = layout.listar_presets()
        self.aviso_presets = (f"Salvo em {os.path.relpath(caminho, PASTA_PROJETO)}", MINT)

    def abrir_pasta_presets(self):
        pasta = layout.pasta_presets_usuario()
        os.makedirs(pasta, exist_ok=True)
        if hasattr(os, "startfile"):  # Windows
            os.startfile(pasta)
            self.aviso_presets = ("Pasta aberta - copie .json pra lá pra importar, ou de lá pra exportar", MINT)
        else:
            self.aviso_presets = (f"Pasta: {pasta}", TEXT_MUTED)

    def _tratar_evento_presets(self, evento):
        campo = self.campo_nome_preset
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.dialogo_presets = False
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and campo.focado:
                self.salvar_preset()
            else:
                campo.tratar_evento(evento)
            return
        if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
            return
        campo.tratar_evento(evento)
        for acao, rect in self.botoes_presets.items():
            if not rect.collidepoint(evento.pos):
                continue
            if acao.startswith("aplicar:"):
                self.aplicar_preset(acao.split(":", 1)[1])
            elif acao == "salvar":
                self.salvar_preset()
            elif acao == "pasta":
                self.abrir_pasta_presets()
            elif acao == "fechar":
                self.dialogo_presets = False
            return

    def pedir_saida(self):
        self._confirmar_campos()
        if self.nao_salvas():
            self.confirmando_saida = True
        else:
            self.rodando = False

    def mudar_skin(self, direcao):
        self.indice_skin = (self.indice_skin + direcao) % len(ORDEM_BARALHO_SKINS)
        ui_theme.set_estilo_baralho(ORDEM_BARALHO_SKINS[self.indice_skin])

    # ---------------------------------------------------------------- Mesa completa
    def modo_mesa(self):
        return self.grupo if self.grupo in editor_mesa.CENAS else self.modo_mesa_geral

    def resolucao(self):
        return editor_mesa.RESOLUCOES[self.indice_resolucao]

    def mudar_modo_mesa_geral(self, direcao):
        modos = list(editor_mesa.CENAS)
        self.modo_mesa_geral = modos[(modos.index(self.modo_mesa_geral) + direcao) % len(modos)]

    def mudar_jogadores(self, direcao):
        modo = self.modo_mesa()
        minimo, maximo = editor_mesa.JOGADORES[modo]
        self.jogadores[modo] = minimo + (self.jogadores[modo] - minimo + direcao) % (maximo - minimo + 1)

    def mudar_cena(self, direcao):
        modo = self.modo_mesa()
        self.cena[modo] = (self.cena[modo] + direcao) % len(editor_mesa.CENAS[modo])

    def mudar_resolucao(self, direcao):
        self.indice_resolucao = (self.indice_resolucao + direcao) % len(editor_mesa.RESOLUCOES)

    def mesa_atual(self):
        """(superfície na resolução escolhida, elementos, alertas) da cena
        atual, ou None se a cena não pôde ser simulada. Só simula quando muda
        jogo/jogadores/cena/resolução e só redesenha quando muda algum valor."""
        modo = self.modo_mesa()
        chave_cena = (modo, self.jogadores[modo], self.cena[modo], self.resolucao())
        chave = (chave_cena, self.indice_skin, tuple(layout.obter(c) for c in layout.chaves()))
        if self._render_mesa[0] == chave:
            return self._render_mesa[1]
        superficie = pygame.Surface(self.resolucao())
        with self._tema_editado():
            if chave_cena not in self._telas_simuladas:
                self._telas_simuladas[chave_cena] = editor_mesa.simular_cena(
                    modo, self.jogadores[modo], self.cena[modo], superficie)
            tela_jogo = self._telas_simuladas[chave_cena]
            resultado = None
            if tela_jogo is not None:
                elementos = editor_mesa.desenhar_mesa(tela_jogo, modo, superficie)
                resultado = (superficie, elementos,
                             editor_mesa.calcular_alertas(elementos, superficie.get_size()))
        self._render_mesa = (chave, resultado)
        return resultado

    def erros_mesa(self):
        resultado = self.mesa_atual()
        return [] if resultado is None else [a for a in resultado[2] if a.nivel == "erro"]

    def _mesa_com_marcacoes(self, escala):
        """Cópia da mesa com contorno vermelho nos problemas e amarelo nos
        elementos do item selecionado (linhas mais grossas se a imagem vai
        ser reduzida, pra continuarem visíveis)."""
        superficie, elementos, alertas = self.mesa_atual()
        imagem = superficie.copy()
        espessura = max(2, round(2 / max(escala, 0.01)))
        for rect in editor_mesa.elementos_do_item(elementos, self.linha_selecionada().chave):
            pygame.draw.rect(imagem, YELLOW, rect.inflate(espessura * 2, espessura * 2), espessura)
        for alerta in alertas:
            if alerta.nivel == "erro":
                for rect in alerta.rects:
                    pygame.draw.rect(imagem, CORAL, rect.inflate(espessura, espessura), espessura)
        return imagem

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        if evento.type == pygame.QUIT:
            self.pedir_saida()
            return
        if self.confirmando_saida:
            self._tratar_evento_dialogo(evento)
            return
        if self.dialogo_presets:
            self._tratar_evento_presets(evento)
            return
        if self.mesa_ampliada:
            # mesa ampliada: qualquer clique, Esc ou F volta ao editor
            if (evento.type == pygame.MOUSEBUTTONDOWN
                    or (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_f))):
                self.mesa_ampliada = False
            return

        campo = self._campo_focado()
        if campo is not None and evento.type == pygame.KEYDOWN:
            campo.tratar_evento(evento)
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._tratar_clique(evento)
        elif evento.type == pygame.MOUSEMOTION and self.slider_arrastando is not None:
            self._arrastar_slider(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONUP:
            self.slider_arrastando = None
            for linha in self.linhas:
                for botao in linha.menos + linha.mais:
                    botao.tratar_evento(evento)
        elif evento.type == pygame.MOUSEWHEEL:
            self._tratar_roda(evento)
        elif evento.type == pygame.KEYDOWN:
            self._tratar_tecla(evento)

    def _tratar_clique(self, evento):
        pos = evento.pos
        # campos primeiro: um clique fora confirma o campo que estava em edição
        if self.area_lista.collidepoint(pos):
            for indice, linha in enumerate(self.linhas):
                if not linha.rect.collidepoint(pos):
                    for campo in linha.campos_texto():
                        campo.tratar_evento(evento)
                    continue
                self.selecionada = indice
                for widget in linha.widgets():
                    widget.tratar_evento(evento)
                if linha.botao_padrao.collidepoint(pos):
                    self.restaurar_item(linha.chave)
            return
        self._confirmar_campos()

        for grupo, rect in self.abas.items():
            if rect.collidepoint(pos):
                self.selecionar_grupo(grupo)
                return
        for vista, rect in self.abas_vista.items():
            if rect.collidepoint(pos):
                self.vista = vista
                return
        for esquerda, direita, mudar in self.seletores.values():
            if esquerda.collidepoint(pos) or direita.collidepoint(pos):
                mudar(-1 if esquerda.collidepoint(pos) else 1)
                return
        for slider in self.sliders:
            if slider.rect.inflate(0, 12).collidepoint(pos):
                self.slider_arrastando = slider.canal
                self._arrastar_slider(pos)
                return
        if self.vista == "mesa" and self.rect_canvas_mesa.collidepoint(pos) and self.mesa_atual():
            self.mesa_ampliada = True
        elif self.botao_salvar.collidepoint(pos):
            self.salvar()
        elif self.botao_descartar.collidepoint(pos) and self.nao_salvas():
            self.descartar()
        elif self.botao_restaurar.collidepoint(pos):
            self.restaurar_tudo()
        elif self.botao_presets.collidepoint(pos):
            self.abrir_presets()
        elif self.rect_proporcao.collidepoint(pos):
            self.manter_proporcao = not self.manter_proporcao
            self.proporcoes.clear()
        elif self.rect_virar.collidepoint(pos):
            self.virada = not self.virada

    def _arrastar_slider(self, pos):
        slider = next((s for s in self.sliders if s.canal == self.slider_arrastando), None)
        if slider is None or not eh_cor(self.linha_selecionada().chave):
            self.slider_arrastando = None
            return
        self.definir_canal(self.linha_selecionada().chave, slider.canal, slider.valor_em(pos[0]))

    def _tratar_roda(self, evento):
        """Roda sobre um campo numérico ajusta o valor; no resto da lista, rola."""
        pos = pygame.mouse.get_pos()
        if not self.area_lista.collidepoint(pos):
            return
        for indice, linha in enumerate(self.linhas):
            alvos = list(enumerate(linha.campos))
            if linha.eh_cor:  # na cor, a roda sobre a amostra ou o hex clareia/escurece
                alvos = [(0, linha.campo_hex), (0, linha)]
            for i_campo, alvo in alvos:
                rect = linha.amostra if alvo is linha else alvo.rect
                if rect.collidepoint(pos) and not getattr(alvo, "focado", False):
                    self.selecionada = indice
                    self.ajustar(linha.chave, i_campo, 1 if evento.y > 0 else -1, shift_pressionado())
                    return
        self.rolagem -= evento.y * 40
        self._limitar_rolagem()

    def _tratar_tecla(self, evento):
        ctrl = evento.mod & pygame.KMOD_CTRL
        tecla = evento.key
        if tecla == pygame.K_s and ctrl:
            self.salvar()
        elif tecla == pygame.K_ESCAPE:
            self.pedir_saida()
        elif tecla in (pygame.K_UP, pygame.K_DOWN):
            self.selecionada = (self.selecionada + (1 if tecla == pygame.K_DOWN else -1)) % len(self.linhas)
            self._rolar_ate_selecionada()
        elif tecla in (pygame.K_LEFT, pygame.K_RIGHT):
            linha = self.linha_selecionada()
            self.ajustar(linha.chave, 0, 1 if tecla == pygame.K_RIGHT else -1, bool(evento.mod & pygame.KMOD_SHIFT))
        elif pygame.K_1 <= tecla < pygame.K_1 + len(GRUPOS):
            self.selecionar_grupo(GRUPOS[tecla - pygame.K_1][0])
        elif tecla == pygame.K_TAB:
            indice = [g for g, _ in GRUPOS].index(self.grupo)
            passo = -1 if evento.mod & pygame.KMOD_SHIFT else 1
            self.selecionar_grupo(GRUPOS[(indice + passo) % len(GRUPOS)][0])
        elif tecla == pygame.K_v:
            self.virada = not self.virada
        elif tecla == pygame.K_b:
            self.mudar_skin(-1 if evento.mod & pygame.KMOD_SHIFT else 1)
        elif tecla == pygame.K_p:
            self.manter_proporcao = not self.manter_proporcao
            self.proporcoes.clear()
        elif tecla == pygame.K_m:
            self.vista = "mesa" if self.vista == "item" else "item"
        elif tecla == pygame.K_f and self.vista == "mesa" and self.mesa_atual():
            self.mesa_ampliada = True
        elif tecla == pygame.K_c and self.vista == "mesa":
            self.mudar_cena(-1 if evento.mod & pygame.KMOD_SHIFT else 1)
        elif tecla in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self.restaurar_item(self.linha_selecionada().chave)

    def _tratar_evento_dialogo(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.confirmando_saida = False
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for acao, rect in self.dialogo_botoes.items():
                if rect.collidepoint(evento.pos):
                    if acao == "salvar":
                        self.salvar()
                        self.rodando = False
                    elif acao == "sair":
                        self.rodando = False
                    self.confirmando_saida = False

    # ---------------------------------------------------------------- Rolagem
    def _altura_conteudo(self):
        return len(self.linhas) * ALTURA_LINHA

    def _limitar_rolagem(self):
        maximo = max(0, self._altura_conteudo() - self.area_lista.height)
        self.rolagem = max(0, min(self.rolagem, maximo))

    def _rolar_ate_selecionada(self):
        topo = self.selecionada * ALTURA_LINHA
        if topo < self.rolagem:
            self.rolagem = topo
        elif topo + ALTURA_LINHA > self.rolagem + self.area_lista.height:
            self.rolagem = topo + ALTURA_LINHA - self.area_lista.height
        self._limitar_rolagem()

    # ---------------------------------------------------------------- Loop
    def atualizar(self, dt):
        self.tempo += dt
        if self.tempo_mensagem > 0:
            self.tempo_mensagem -= dt
        for linha in self.linhas:
            for botao in linha.menos + linha.mais:
                botao.atualizar(dt)
        pendentes = len(self.nao_salvas())
        pygame.display.set_caption("Editor de Layout - PixelPoker" + (f"  ({pendentes} não salvas)" if pendentes else ""))

    def executar(self):
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000.0
            for evento in pygame.event.get():
                if evento.type == pygame.VIDEORESIZE:
                    self.tela = pygame.display.get_surface()
                else:
                    self.tratar_evento(evento)
            self.atualizar(dt)
            self.desenhar(self.tela)
            pygame.display.flip()
        pygame.quit()

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela):
        ui_theme.aplicar_tema(layout.padrao)  # moldura do editor sempre no tema padrão
        largura, altura = tela.get_size()
        tela.fill(BG)
        self.sliders = []
        largura_esq = max(500, min(600, int(largura * 0.42)))
        painel_esq = pygame.Rect(MARGEM, 78, largura_esq, altura - 78 - ALTURA_RODAPE)
        painel_dir = pygame.Rect(painel_esq.right + 24, 78, largura - painel_esq.right - 24 - MARGEM,
                                 painel_esq.height)

        self.seletores = {}
        self._desenhar_topo(tela, largura)
        self._desenhar_lista(tela, painel_esq)
        self._desenhar_previa(tela, painel_dir)
        self._desenhar_rodape(tela, largura, altura)
        if self.dialogo_presets:
            self._desenhar_dialogo_presets(tela, largura, altura)
        if self.confirmando_saida:
            self._desenhar_dialogo_saida(tela, largura, altura)
        aplicar_scanlines(tela)
        if self.mesa_ampliada and self.mesa_atual():
            self._desenhar_mesa_ampliada(tela, largura, altura)  # a mesa já vem com as scanlines do jogo

    def _desenhar_topo(self, tela, largura):
        desenhar_texto(tela, "EDITOR DE LAYOUT", MARGEM, 18, tamanho=26, negrito=True, familia="display")
        desenhar_texto(tela, "PixelPoker · tamanhos de cartas, peças e botões das mesas", MARGEM, 50,
                       tamanho=13, cor=TEXT_MUTED)
        pendentes = len(self.nao_salvas())
        if pendentes:
            texto = plural(pendentes, "ALTERAÇÃO NÃO SALVA", "ALTERAÇÕES NÃO SALVAS")
            cor, cor_texto = YELLOW, SOMBRA
        else:
            texto, cor, cor_texto = "TUDO SALVO", PANEL, INK
        desenhar_badge(tela, largura - MARGEM, 30, texto, cor, cor_texto=cor_texto, tamanho_fonte=12,
                       ancorar="midright", borda=INK, familia="mono")

    def _desenhar_lista(self, tela, painel):
        desenhar_painel(tela, painel)
        # abas dos grupos
        x = painel.x + 12
        largura_aba = (painel.width - 24 - 3 * 6) // len(GRUPOS)
        self.abas = {}
        for numero, (grupo, nome) in enumerate(GRUPOS, start=1):
            rect = pygame.Rect(x, painel.y + 12, largura_aba, ALTURA_ABAS - 8)
            ativa = grupo == self.grupo
            alterado = any(layout.obter(c) != self.salvos[c] for c in layout.chaves() if c.startswith(grupo + "."))
            retangulo_borda(tela, rect, YELLOW if ativa else SOMBRA, INK if ativa else TEXT_MUTED, 2)
            rotulo = f"{nome}{' *' if alterado else ''}"
            desenhar_texto(tela, rotulo, rect.centerx, rect.centery, tamanho=14, negrito=True,
                           cor=SOMBRA if ativa else INK, centralizado=True, familia="mono")
            desenhar_texto(tela, str(numero), rect.x + 6, rect.y + 3, tamanho=10,
                           cor=SOMBRA if ativa else TEXT_MUTED, familia="mono")
            self.abas[grupo] = rect
            x += largura_aba + 6

        self.area_lista = pygame.Rect(painel.x + 8, painel.y + ALTURA_ABAS + 14,
                                      painel.width - 16, painel.height - ALTURA_ABAS - 22)
        self._limitar_rolagem()
        tela.set_clip(self.area_lista)
        for indice, linha in enumerate(self.linhas):
            rect = pygame.Rect(self.area_lista.x, self.area_lista.y + indice * ALTURA_LINHA - self.rolagem,
                               self.area_lista.width - 8, ALTURA_LINHA - 4)
            linha.posicionar(rect)
            if rect.bottom >= self.area_lista.top and rect.top <= self.area_lista.bottom:
                self._desenhar_linha(tela, linha, indice == self.selecionada)
        tela.set_clip(None)

        # barra de rolagem
        conteudo = self._altura_conteudo()
        if conteudo > self.area_lista.height:
            trilho = pygame.Rect(self.area_lista.right - 4, self.area_lista.y, 4, self.area_lista.height)
            pygame.draw.rect(tela, SOMBRA, trilho)
            altura_alca = max(30, trilho.height * self.area_lista.height // conteudo)
            y_alca = trilho.y + (trilho.height - altura_alca) * self.rolagem // max(1, conteudo - self.area_lista.height)
            pygame.draw.rect(tela, TEXT_MUTED, (trilho.x, y_alca, 4, altura_alca))

    def _desenhar_linha(self, tela, linha, selecionada):
        rect = linha.rect
        retangulo_borda(tela, rect, LOCKED if selecionada else PANEL, YELLOW if selecionada else PANEL, 2)
        valor = layout.obter(linha.chave)
        nao_salvo = valor != self.salvos[linha.chave]
        fora_padrao = valor != layout.padrao(linha.chave)

        x_texto = rect.x + 12
        if nao_salvo:
            desenhar_texto(tela, "*", x_texto, rect.y + 7, tamanho=16, negrito=True, cor=YELLOW, familia="mono")
            x_texto += 14
        rotulo = caber_texto(linha.meta.get("rotulo", linha.chave), rect.right - x_texto - 12, 14, negrito=True)
        desenhar_texto(tela, rotulo, x_texto, rect.y + 8, tamanho=14, negrito=True)

        espaco_chave = linha.inicio_controles() - rect.x - 24
        chave = caber_texto(linha.chave, espaco_chave, 11, familia="mono")
        desenhar_texto(tela, chave, rect.x + 12, rect.y + 40, tamanho=11, cor=TEXT_MUTED, familia="mono")

        if linha.eh_cor:
            if not linha.campo_hex.focado:
                linha.campo_hex.valor = valor
            desenhar_amostra_cor(tela, linha.amostra, valor)
            linha.campo_hex.desenhar(tela)
            desenhar_botao_pequeno(tela, linha.botao_padrao, "PADRÃO", ativo=fora_padrao)
            return
        valores = valor if isinstance(valor, tuple) else (valor,)
        for indice, campo in enumerate(linha.campos):
            if not campo.focado:
                campo.valor = valores[indice]
            linha.menos[indice].desenhar(tela)
            campo.desenhar(tela)
            linha.mais[indice].desenhar(tela)
        if len(linha.campos) == 2:
            # "x" amarelo = largura e altura andam juntas (proporção travada)
            travado = self.manter_proporcao and trava_proporcao(linha.chave)
            meio = (linha.mais[0].rect.right + linha.menos[1].rect.left) // 2
            desenhar_texto(tela, "x", meio, linha.campos[0].rect.centery, tamanho=14,
                           cor=YELLOW if travado else TEXT_MUTED, centralizado=True, familia="mono")
        desenhar_botao_pequeno(tela, linha.botao_padrao, "PADRÃO", ativo=fora_padrao)

    def _desenhar_previa(self, tela, painel):
        desenhar_painel(tela, painel)
        linha = self.linha_selecionada()
        meta = linha.meta

        # abas das vistas; a de mesa mostra quantos problemas a cena tem
        erros = len(self.erros_mesa())
        x = painel.x + 16
        self.abas_vista = {}
        for vista, texto in (("item", "ITEM"), ("mesa", "MESA COMPLETA" + (f" ({erros}!)" if erros else ""))):
            rect = pygame.Rect(x, painel.y + 12, obter_fonte(13, True, "mono").size(texto)[0] + 28, 30)
            ativa = self.vista == vista
            retangulo_borda(tela, rect, YELLOW if ativa else SOMBRA, INK if ativa else TEXT_MUTED, 2)
            cor_texto = SOMBRA if ativa else (CORAL if vista == "mesa" and erros else INK)
            desenhar_texto(tela, texto, rect.centerx, rect.centery, tamanho=13, negrito=True, cor=cor_texto,
                           centralizado=True, familia="mono")
            self.abas_vista[vista] = rect
            x = rect.right + 6
        dica = "M alterna" + (" · clique na mesa ou F amplia" if self.vista == "mesa" else "")
        desenhar_texto(tela, caber_texto(dica, painel.right - x - 22, 11, familia="mono"), x + 6, painel.y + 20,
                       tamanho=11, cor=TEXT_MUTED, familia="mono")

        # cabeçalho: rótulo completo + faixa permitida
        y = painel.y + 52
        linhas_rotulo = 2 if self.vista == "item" else 1
        for texto in quebrar_texto(meta.get("rotulo", linha.chave), painel.width - 32, 17,
                                   negrito=True)[:linhas_rotulo]:
            desenhar_texto(tela, caber_texto(texto, painel.width - 32, 17, negrito=True), painel.x + 16, y,
                           tamanho=17, negrito=True)
            y += 22

        def fmt(v):
            return " x ".join(str(n) for n in v) if isinstance(v, (list, tuple)) else str(v)
        passo = meta.get("passo", 1)
        if linha.eh_cor:
            detalhes = (f"{linha.chave}  ·  padrão {cor_para_hex(layout.padrao(linha.chave))}  ·  R, G e B de 0 a "
                        f"255  ·  ←→/roda clareiam e escurecem de {passo} em {passo} (Shift: {passo * MULTIPLICADOR_SHIFT})")
        else:
            ordem = ""
            if isinstance(meta["valor"], list) and "comprimento" not in meta.get("rotulo", ""):
                ordem = " (largura x altura)"
            detalhes = (f"{linha.chave}  ·  padrão {fmt(layout.padrao(linha.chave))}{ordem}  ·  faixa "
                        f"{fmt(meta.get('min', '-'))} a {fmt(meta.get('max', '-'))}  ·  passo {passo} "
                        f"(Shift: {passo * MULTIPLICADOR_SHIFT})")
        desenhar_texto(tela, caber_texto(detalhes, painel.width - 32, 11, familia="mono"), painel.x + 16, y + 2,
                       tamanho=11, cor=TEXT_MUTED, familia="mono")
        y += 26

        self.rect_virar = pygame.Rect(0, 0, 0, 0)
        if self.vista == "item":
            self.rect_canvas_mesa = pygame.Rect(0, 0, 0, 0)
            self._desenhar_vista_item(tela, painel, y, linha)
        else:
            self._desenhar_vista_mesa(tela, painel, y)

    def _desenhar_vista_item(self, tela, painel, y, linha):
        funcao, fundo, usa_baralho = PREVIAS[linha.chave]
        altura_controles = 46 if usa_baralho else 0
        altura_sliders = 3 * 34 + 20 if linha.eh_cor else 0  # sliders R/G/B + 1 linha a mais de info
        canvas = pygame.Rect(painel.x + 16, y, painel.width - 32,
                             painel.bottom - y - 58 - altura_controles - altura_sliders)
        info, escala = self._desenhar_canvas(tela, canvas, funcao, fundo, linha.chave)

        if escala >= 1:
            desenhar_texto(tela, "Tamanho real (1:1)", painel.x + 16, canvas.bottom + 8, tamanho=12, cor=TEXT_MUTED)
        else:
            desenhar_texto(tela, f"Reduzida para {int(escala * 100)}% para caber aqui - maximize a janela para ver "
                                 f"em tamanho real", painel.x + 16, canvas.bottom + 8, tamanho=12, cor=YELLOW)
        cor_info = CORAL if "BAIXO" in info else TEXT_MUTED
        linhas_info = quebrar_texto(info, painel.width - 32, 12)[:2 if linha.eh_cor else 1]
        for i, texto in enumerate(linhas_info):
            desenhar_texto(tela, caber_texto(texto, painel.width - 32, 12), painel.x + 16,
                           canvas.bottom + 26 + i * 17, tamanho=12, cor=cor_info)

        y_controles = canvas.bottom + 50
        if linha.eh_cor:
            y_sliders = canvas.bottom + 70
            cor = layout.obter(linha.chave)
            for canal in range(3):
                slider = SliderCor(pygame.Rect(painel.x + 44, y_sliders + canal * 34, painel.width - 44 - 76, 20),
                                   canal)
                slider.desenhar(tela, cor, arrastando=self.slider_arrastando == canal)
                self.sliders.append(slider)
            y_controles += altura_sliders

        if usa_baralho:
            esquerda, direita = desenhar_seletor(tela, painel.x + 16, y_controles, 280,
                                                 f"Baralho: {self._nome_skin()} (B)", altura=32)
            self.seletores["baralho"] = (esquerda, direita, self.mudar_skin)
            self.rect_virar = desenhar_caixa_marcar(tela, direita.right + 24, y_controles + 5,
                                                    "Virar cartas (V)", self.virada, tamanho=13)

    def _nome_skin(self):
        return ROTULOS_BARALHO_SKIN[ORDEM_BARALHO_SKINS[self.indice_skin]]

    def _desenhar_vista_mesa(self, tela, painel, y):
        """A tela de verdade do jogo, reduzida pra caber, com os seletores de
        cena/jogadores/resolução/baralho e a lista de alertas embaixo."""
        modo = self.modo_mesa()
        linhas_seletor = 2 if self.grupo in editor_mesa.CENAS else 3
        max_alertas = 4
        reservado = linhas_seletor * 38 + max_alertas * 17 + 22
        area = pygame.Rect(painel.x + 16, y, painel.width - 32, painel.bottom - y - 12 - reservado)
        res = self.resolucao()
        escala = min(area.width / res[0], area.height / res[1])
        canvas = pygame.Rect(0, 0, int(res[0] * escala), int(res[1] * escala))
        canvas.midtop = area.midtop
        self.rect_canvas_mesa = canvas

        resultado = self.mesa_atual()
        if resultado is None:
            pygame.draw.rect(tela, SOMBRA, canvas)
            for i, texto in enumerate(quebrar_texto(
                    f"Não consegui chegar nessa cena com {self.jogadores[modo]} jogadores - tente outra cena "
                    f"ou outro número de jogadores.", canvas.width - 40, 13)):
                desenhar_texto(tela, texto, canvas.centerx, canvas.centery - 10 + i * 18, tamanho=13,
                               cor=TEXT_MUTED, centralizado=True)
        else:
            imagem = pygame.transform.smoothscale(self._mesa_com_marcacoes(escala), canvas.size)
            tela.blit(imagem, canvas)
        pygame.draw.rect(tela, INK, canvas, width=2)

        # seletores, em duas colunas (nas abas GERAL e CORES, uma linha a mais pra escolher o jogo)
        x1 = painel.x + 16
        meia = (painel.width - 32 - 10) // 2
        x2 = x1 + meia + 10
        yc = canvas.bottom + 10
        if self.grupo not in editor_mesa.CENAS:  # GERAL e CORES: escolhe o jogo
            esq, dir_ = desenhar_seletor(tela, x1, yc, meia, f"Jogo: {editor_mesa.NOMES_MODO[modo]}")
            self.seletores["jogo"] = (esq, dir_, self.mudar_modo_mesa_geral)
            yc += 38
        nome_cena = editor_mesa.CENAS[modo][self.cena[modo]][0]
        esq, dir_ = desenhar_seletor(tela, x1, yc, meia, f"Cena: {nome_cena} (C)")
        self.seletores["cena"] = (esq, dir_, self.mudar_cena)
        esq, dir_ = desenhar_seletor(tela, x2, yc, meia, f"{self.jogadores[modo]} jogadores")
        self.seletores["jogadores"] = (esq, dir_, self.mudar_jogadores)
        yc += 38
        esq, dir_ = desenhar_seletor(tela, x1, yc, meia, f"Janela do jogo: {res[0]} x {res[1]}")
        self.seletores["resolucao"] = (esq, dir_, self.mudar_resolucao)
        esq, dir_ = desenhar_seletor(tela, x2, yc, meia, f"Baralho: {self._nome_skin()} (B)")
        self.seletores["baralho"] = (esq, dir_, self.mudar_skin)
        yc += 40

        # alertas: problemas (vermelho) primeiro, depois os informativos
        largura_texto = painel.width - 32
        if resultado is None:
            return
        alertas = resultado[2]
        if not alertas:
            desenhar_texto(tela, "Nenhum elemento saindo da tela ou sobreposto nesta cena.", x1, yc, tamanho=12,
                           cor=MINT)
            return
        visiveis = alertas if len(alertas) <= max_alertas else alertas[:max_alertas - 1]
        for alerta in visiveis:
            marcador, cor = ("!", CORAL) if alerta.nivel == "erro" else ("i", TEXT_MUTED)
            desenhar_texto(tela, caber_texto(f"{marcador} {alerta.mensagem}", largura_texto, 12), x1, yc,
                           tamanho=12, cor=cor)
            yc += 17
        if len(alertas) > len(visiveis):
            desenhar_texto(tela, f"+ {len(alertas) - len(visiveis)} outros (veja contornados em vermelho na mesa)",
                           x1, yc, tamanho=12, cor=TEXT_MUTED)

    def _desenhar_mesa_ampliada(self, tela, largura, altura):
        modo = self.modo_mesa()
        res = self.resolucao()
        tela.fill(SOMBRA)
        area = pygame.Rect(16, 16, largura - 32, altura - 56)
        escala = min(1.0, area.width / res[0], area.height / res[1])
        imagem = self._mesa_com_marcacoes(escala)
        if escala < 1:
            imagem = pygame.transform.smoothscale(imagem, (int(res[0] * escala), int(res[1] * escala)))
        rect = imagem.get_rect(center=area.center)
        tela.blit(imagem, rect)
        pygame.draw.rect(tela, INK, rect, width=2)
        nome_cena = editor_mesa.CENAS[modo][self.cena[modo]][0]
        escala_txt = "tamanho real" if escala >= 1 else f"{int(escala * 100)}% (aumente a janela do editor para ver maior)"
        texto = (f"{editor_mesa.NOMES_MODO[modo]} · {nome_cena} · {self.jogadores[modo]} jogadores · "
                 f"{res[0]}x{res[1]} · {escala_txt}  —  clique, Esc ou F para voltar")
        desenhar_texto(tela, caber_texto(texto, largura - 32, 13), largura // 2, altura - 20, tamanho=13,
                       cor=TEXT_MUTED, centralizado=True)

    def _desenhar_canvas(self, tela, canvas, funcao, fundo, chave):
        """Desenha a prévia (no tema editado) numa superfície grande, recorta a
        área usada e, se não couber no canvas, reduz a escala."""
        with self._tema_editado():
            rascunho = pygame.Surface((1800, 1000))
            rascunho.fill(fundo)
            area, info = funcao(rascunho, 900, 500, {"virada": self.virada, "tempo": self.tempo, "chave": chave})
            area = area.clip(rascunho.get_rect())
            pygame.draw.rect(tela, fundo, canvas)

        escala = min(1.0, canvas.width / max(1, area.width), canvas.height / max(1, area.height))
        recorte = rascunho.subsurface(area)
        if escala < 1:
            recorte = pygame.transform.smoothscale(recorte, (int(area.width * escala), int(area.height * escala)))
        tela.blit(recorte, recorte.get_rect(center=canvas.center))
        pygame.draw.rect(tela, INK, canvas, width=2)
        return info, escala

    def _desenhar_rodape(self, tela, largura, altura):
        y = altura - ALTURA_RODAPE + 18
        self.botao_salvar.topleft = (MARGEM, y)
        self.botao_descartar.topleft = (self.botao_salvar.right + 18, y)
        self.botao_restaurar.topleft = (self.botao_descartar.right + 18, y)
        mouse = pygame.mouse.get_pos()
        pendentes = bool(self.nao_salvas())
        desenhar_botao(tela, self.botao_salvar, "Salvar", hover=self.botao_salvar.collidepoint(mouse),
                       tamanho_fonte=17, cor=MINT)
        desenhar_kbd(tela, self.botao_salvar.right - 10, self.botao_salvar.bottom - 10, "Ctrl+S", ancorar="bottomright")
        desenhar_botao(tela, self.botao_descartar, "Descartar alterações", ativo=pendentes,
                       hover=pendentes and self.botao_descartar.collidepoint(mouse), tamanho_fonte=15, cor=PANEL)
        desenhar_botao(tela, self.botao_restaurar, "Tudo ao padrão", hover=self.botao_restaurar.collidepoint(mouse),
                       tamanho_fonte=15, cor=CORAL)
        self.botao_presets.topleft = (self.botao_restaurar.right + 18, y)
        desenhar_botao(tela, self.botao_presets, "Presets", hover=self.botao_presets.collidepoint(mouse),
                       tamanho_fonte=15, cor=PURPLE)
        self.rect_proporcao = desenhar_caixa_marcar(tela, self.botao_presets.right + 28, y + 14,
                                                    "Manter proporção de cartas/peças (P)", self.manter_proporcao)

        if self.tempo_mensagem > 0:
            texto, cor = self.mensagem, self.cor_mensagem
        else:
            texto, cor = ("↑↓ item · ←→ diminui/aumenta (Shift: passo maior) · 1-5/Tab aba · Del padrão · "
                          "M mesa completa · C cena · F ampliar · B baralho · Esc sai"), TEXT_MUTED
        desenhar_texto(tela, caber_texto(texto, largura - 2 * MARGEM, 12), MARGEM, altura - 24, tamanho=12, cor=cor)

    def _desenhar_dialogo_presets(self, tela, largura, altura):
        veu = pygame.Surface((largura, altura), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 170))
        tela.blit(veu, (0, 0))
        altura_linha = 54
        painel = pygame.Rect(0, 0, 640, 200 + altura_linha * max(1, len(self.lista_presets)))
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel)
        mouse = pygame.mouse.get_pos()
        self.botoes_presets = {}

        desenhar_texto(tela, "PRESETS", painel.x + 24, painel.y + 18, tamanho=20, negrito=True, familia="display")
        desenhar_texto(tela, "Aplicar troca TODOS os valores pelos do preset (falta Salvar pra valer no jogo)",
                       painel.x + 24, painel.y + 46, tamanho=12, cor=TEXT_MUTED)
        y = painel.y + 74
        if not self.lista_presets:
            desenhar_texto(tela, "Nenhum preset encontrado.", painel.x + 24, y + 14, tamanho=14, cor=TEXT_MUTED)
        for nome, origem, sobre in self.lista_presets:
            linha = pygame.Rect(painel.x + 16, y, painel.width - 32, altura_linha - 6)
            retangulo_borda(tela, linha, SOMBRA, PANEL, 2)
            desenhar_texto(tela, nome, linha.x + 12, linha.y + 6, tamanho=15, negrito=True)
            etiqueta = "do jogo" if origem == "padrao" else "seu"
            desenhar_badge(tela, linha.x + 20 + obter_fonte(15, True).size(nome)[0], linha.y + 15, etiqueta,
                           BLUE if origem == "padrao" else MINT, cor_texto=INK if origem == "padrao" else SOMBRA,
                           tamanho_fonte=10, ancorar="midleft")
            botao = pygame.Rect(0, 0, 110, 34)
            botao.midright = (linha.right - 8, linha.centery)
            desenhar_texto(tela, caber_texto(sobre or "-", botao.left - linha.x - 24, 11), linha.x + 12, linha.y + 28,
                           tamanho=11, cor=TEXT_MUTED)
            desenhar_botao(tela, botao, "Aplicar", hover=botao.collidepoint(mouse), tamanho_fonte=13, cor=YELLOW,
                           largura_borda=2)
            self.botoes_presets[f"aplicar:{nome}"] = botao
            y += altura_linha

        y += 10
        self.campo_nome_preset.rect.topleft = (painel.x + 24, y)
        self.campo_nome_preset.desenhar(tela)
        salvar = pygame.Rect(self.campo_nome_preset.rect.right + 12, y, 300, 44)
        desenhar_botao(tela, salvar, "Salvar atual como preset", hover=salvar.collidepoint(mouse), tamanho_fonte=13,
                       cor=MINT)
        self.botoes_presets["salvar"] = salvar

        fechar = pygame.Rect(0, 0, 120, 40)
        fechar.bottomright = (painel.right - 24, painel.bottom - 16)
        pasta = pygame.Rect(0, 0, 170, 40)
        pasta.bottomright = (fechar.left - 12, fechar.bottom)
        desenhar_botao(tela, pasta, "Abrir pasta", hover=pasta.collidepoint(mouse), tamanho_fonte=13, cor=PANEL)
        desenhar_botao(tela, fechar, "Fechar", hover=fechar.collidepoint(mouse), tamanho_fonte=13, cor=PANEL)
        self.botoes_presets["pasta"] = pasta
        self.botoes_presets["fechar"] = fechar
        if self.aviso_presets:
            texto, cor = self.aviso_presets
            desenhar_texto(tela, caber_texto(texto, pasta.left - painel.x - 40, 12), painel.x + 24,
                           fechar.centery - 8, tamanho=12, cor=cor)

    def _desenhar_dialogo_saida(self, tela, largura, altura):
        veu = pygame.Surface((largura, altura), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 170))
        tela.blit(veu, (0, 0))
        painel = pygame.Rect(0, 0, 560, 200)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel)
        pendentes = len(self.nao_salvas())
        desenhar_texto(tela, "Sair do editor?", painel.centerx, painel.y + 34, tamanho=20, negrito=True,
                       centralizado=True)
        desenhar_texto(tela, f"Há {plural(pendentes, 'alteração não salva', 'alterações não salvas')}.",
                       painel.centerx, painel.y + 70,
                       tamanho=14, cor=TEXT_MUTED, centralizado=True)
        mouse = pygame.mouse.get_pos()
        botoes = [("salvar", "Salvar e sair", MINT, 170), ("sair", "Sair sem salvar", CORAL, 170),
                  ("cancelar", "Cancelar", PANEL, 140)]
        x = painel.centerx - (sum(b[3] for b in botoes) + 2 * 16) // 2
        self.dialogo_botoes = {}
        for acao, texto, cor, largura_botao in botoes:
            rect = pygame.Rect(x, painel.bottom - 74, largura_botao, 48)
            desenhar_botao(tela, rect, texto, hover=rect.collidepoint(mouse), tamanho_fonte=14, cor=cor)
            self.dialogo_botoes[acao] = rect
            x += largura_botao + 16


if __name__ == "__main__":
    EditorVisual().executar()
