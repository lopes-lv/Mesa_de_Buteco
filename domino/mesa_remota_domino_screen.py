"""
mesa_remota_domino_screen.py - Tela do jogador "cliente" no multiplayer
local do Dominó (ver domino_screen.py, do qual esta tela é o espelho do
lado do host, e MULTIPLAYER_PLANO.md pela arquitetura geral).

Não roda nenhuma `DominoTable` de verdade: guarda o snapshot público de
`estado` e a própria mão (`sua_mao`). Como não existe mais monte/compra
(ver domino_logic.py), as duas ações de rede que este lado manda são "jogar
uma peça" (arrastando até a ponta/ramo desejado) e "passar" - as checagens
de "essa peça é jogável?"/"eu realmente não tenho jogada?" são recalculadas
localmente com a mesma função pura de `domino_logic.py`
(`jogadas_possiveis_em`), já que o estado do tabuleiro (`ramos`,
`extremidades`, `eh_spinner`) é informação pública.
"""
import math
import queue
import random

import pygame
from core.ui_theme import (
    BG, PANEL, INK, SOMBRA, FELT, FELT_DARK, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_avatar, desenhar_mesa,
    desenhar_badge, desenhar_glow_de_vez,
)
from .domino_theme import desenhar_peca, desenhar_peca_verso
from .domino_logic import (
    Peca, jogadas_possiveis_em, BONUS_PASSE, DIRECOES,
    FASE_EMBARALHANDO, FASE_ESCOLHENDO, FASE_JOGANDO, DURACAO_EMBARALHAR,
)
from .domino_screen import (
    CENTRO_MESA_Y, FOLGA_ASSENTO_CIMA, FOLGA_ASSENTO_BAIXO, MEIA_LARGURA_ASSENTO, posicionar_botao_passar,
)
from core.chat_widget import ChatWidget
from core import layout
from rede import protocolo

# Tamanhos de peça, espaçamentos e botões: mesmas chaves "domino.*"/"geral.*"
# de core/layout.py que domino_screen.py usa; a geometria da mesa (centro do
# feltro, folga dos assentos, posição do "Passar") também vem de lá.
PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]


def _horizontal(direcao):
    return direcao in ("esquerda", "direita")


def _tamanho_peca(direcao, eh_carroca, escala=1.0):
    comprimento, espessura = layout.obter("domino.peca_mesa")
    retrato = eh_carroca if _horizontal(direcao) else not eh_carroca
    largura, altura = (espessura, comprimento) if retrato else (comprimento, espessura)
    return int(largura * escala), int(altura * escala)


def _posicoes_assentos(mesa_rect, n_jogadores):
    if n_jogadores == 3:
        angulos = [90, 210, 330]
    else:
        angulos = [90, 180, 270, 0]

    posicoes = []
    for i in range(n_jogadores):
        ang = math.radians(angulos[i])
        rx = mesa_rect.width // 2 + 70
        ry = mesa_rect.height // 2 + (FOLGA_ASSENTO_CIMA if math.sin(ang) < 0 else FOLGA_ASSENTO_BAIXO)
        x = mesa_rect.centerx + int(rx * math.cos(ang))
        y = mesa_rect.centery + int(ry * math.sin(ang))
        largura_tela = mesa_rect.centerx * 2  # a mesa é centrada na janela
        x = max(MEIA_LARGURA_ASSENTO, min(largura_tela - MEIA_LARGURA_ASSENTO, x))
        posicoes.append((x, y))
    return posicoes


def _iniciais(nome):
    partes = nome.replace('"', "").split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    return nome[:2].upper()


class MesaRemotaDominoScreen:
    def __init__(self, app, sala_cliente):
        self.app = app
        self.sala = sala_cliente
        self.meu_id = sala_cliente.meu_id

        self.estado = None
        self.minha_mao = []  # lista de [a, b]
        self.tempo_decorrido = 0.0

        self.peca_arrastando = None
        self.pos_arraste = (0, 0)
        self.zonas_drop_ativas = {}
        self._zonas_mesa = {}

        # Fase visual de início de mão (ver domino_logic.FASE_* e o mesmo
        # mecanismo em domino_screen.DominoTableScreen) - puramente local a
        # esta tela: `pecas_para_escolher` é uma cópia embaralhada de
        # `minha_mao` (que já chegou inteira via SUA_MAO), sem afetar nada no
        # host.
        self.fase_mao = FASE_JOGANDO
        self.timer_embaralhar = 0.0
        self.pecas_para_escolher = []
        self._qtd_embaralhando = 0
        self._ultimo_mao_numero = None

        self.erro_acao = None
        self.tempo_erro_acao = 0.0
        self.mensagem_final = None
        self.vencedor_final = None

        self.chat = ChatWidget(self._enviar_chat)
        self.botao_sair = pygame.Rect(0, 0, 0, 0)
        self.botao_passar = pygame.Rect(0, 0, 0, 0)
        self._dimensionar_botoes()

    # ---------------------------------------------------------------- Estado
    def _enviar_chat(self, texto):
        self.sala.enviar({"tipo": protocolo.CHAT, "texto": texto})

    def _sair(self):
        self.sala.fechar()
        self.app.ir_para_menu()

    def _meu_jogador(self):
        if self.estado is None:
            return None
        for j in self.estado["jogadores"]:
            if j["id"] == self.meu_id:
                return j
        return None

    def _eh_minha_vez(self):
        return self.estado is not None and self.estado.get("jogador_da_vez_id") == self.meu_id

    def _minha_mao_pecas(self):
        return [Peca(a, b) for a, b in self.minha_mao]

    def _minha_peca_obrigatoria(self):
        dados = self.estado.get("peca_obrigatoria") if self.estado else None
        return Peca(dados[0], dados[1]) if dados else None

    def _bucho_liberado(self):
        ramos = self.estado.get("ramos", {}) if self.estado else {}
        return bool(ramos.get("esquerda")) and bool(ramos.get("direita"))

    def _minhas_jogadas_possiveis(self):
        if self.estado is None:
            return []
        eh_spinner = self.estado.get("eh_spinner", False)
        extremidades = dict(self.estado.get("extremidades", {}))
        if eh_spinner and not self._bucho_liberado():
            extremidades["cima"] = None
            extremidades["baixo"] = None
        return jogadas_possiveis_em(self._minha_mao_pecas(), extremidades, eh_spinner, self._minha_peca_obrigatoria())

    def _tenho_jogada(self):
        return len(self._minhas_jogadas_possiveis()) > 0

    def _enviar_jogada(self, peca, direcao):
        self.sala.enviar({"tipo": protocolo.ACAO_DOMINO, "acao": "jogar", "peca": [peca.a, peca.b], "lado": direcao})

    def _enviar_passar(self):
        self.sala.enviar({"tipo": protocolo.ACAO_DOMINO, "acao": "passar"})

    def _iniciar_fase_embaralhar(self):
        self.timer_embaralhar = 0.0
        if self.app.settings.selecao_automatica_pecas:
            self.fase_mao = FASE_JOGANDO
            self.pecas_para_escolher = []
            return
        self.fase_mao = FASE_EMBARALHANDO
        n_jogadores = len(self.estado["jogadores"]) if self.estado else 1
        self._qtd_embaralhando = n_jogadores * len(self.minha_mao)
        self.pecas_para_escolher = list(self._minha_mao_pecas())
        random.shuffle(self.pecas_para_escolher)

    # ---------------------------------------------------------------- Update
    def atualizar(self, dt):
        self.tempo_decorrido += dt
        if self.tempo_erro_acao > 0:
            self.tempo_erro_acao -= dt
            if self.tempo_erro_acao <= 0:
                self.erro_acao = None

        while True:
            try:
                msg = self.sala.mensagens_entrantes.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == protocolo.ESTADO:
                novo_mao_numero = msg.get("mao_numero")
                if novo_mao_numero != self._ultimo_mao_numero:
                    self._ultimo_mao_numero = novo_mao_numero
                    self._iniciar_fase_embaralhar()
                self.estado = msg
                if not self._eh_minha_vez():
                    self.peca_arrastando = None
                    self.zonas_drop_ativas = {}
            elif tipo == protocolo.SUA_MAO:
                self.minha_mao = msg.get("pecas", [])
                validas = {tuple(p) for p in self.minha_mao}
                if self.peca_arrastando is not None and (self.peca_arrastando.a, self.peca_arrastando.b) not in validas:
                    self.peca_arrastando = None
                    self.zonas_drop_ativas = {}
            elif tipo == protocolo.ERRO_ACAO:
                self.erro_acao = msg.get("motivo")
                self.tempo_erro_acao = 3.0
            elif tipo == protocolo.FIM_DE_JOGO:
                self.vencedor_final = msg.get("vencedor")
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

        if self.fase_mao == FASE_EMBARALHANDO:
            self.timer_embaralhar += dt
            if self.timer_embaralhar >= DURACAO_EMBARALHAR:
                self.fase_mao = FASE_ESCOLHENDO

        if self.vencedor_final is None and self.sala.status in ("sala_encerrada", "desconectado"):
            self.mensagem_final = self.sala.erro or "Conexão com o anfitrião perdida."

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        if self.chat.tratar_evento(evento):
            return

        if self.vencedor_final is not None or self.mensagem_final is not None:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self._sair()
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_sair.collidepoint(evento.pos):
                self._sair()
                return

        if self.fase_mao == FASE_EMBARALHANDO:
            return

        if self.fase_mao == FASE_ESCOLHENDO:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._clicar_pilha_escolha(evento.pos)
            return

        if self.estado is None or self.estado.get("resultado") is not None:
            return

        meu = self._meu_jogador()
        if meu is None:
            return

        if evento.type == pygame.MOUSEMOTION:
            if self.peca_arrastando is not None:
                self.pos_arraste = evento.pos
            return

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.peca_arrastando is not None:
                self._soltar_peca(evento.pos)
            return

        if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
            return

        if not self._eh_minha_vez():
            return

        if not self._tenho_jogada():
            if self.botao_passar.collidepoint(evento.pos):
                self._enviar_passar()
            return

        for rect, peca in self._rects_mao():
            if rect.collidepoint(evento.pos):
                self._comecar_arraste(peca, evento.pos)
                return

    def _comecar_arraste(self, peca, pos_mouse):
        direcoes = [d for p, d in self._minhas_jogadas_possiveis() if p == peca]
        if not direcoes:
            return
        self.peca_arrastando = peca
        self.pos_arraste = pos_mouse
        self.zonas_drop_ativas = {d: r for d, r in self._zonas_mesa.items() if d in direcoes}

    def _soltar_peca(self, pos_mouse):
        peca = self.peca_arrastando
        direcao_escolhida = next((d for d, rect in self.zonas_drop_ativas.items()
                                   if rect.collidepoint(pos_mouse)), None)
        self.peca_arrastando = None
        self.zonas_drop_ativas = {}
        if direcao_escolhida is not None:
            self._enviar_jogada(peca, direcao_escolhida)

    def _clicar_pilha_escolha(self, pos_mouse):
        for rect, peca in self._rects_pilha_escolha(self._mesa_rect()):
            if rect.collidepoint(pos_mouse):
                self.pecas_para_escolher.remove(peca)
                if not self.pecas_para_escolher:
                    self.fase_mao = FASE_JOGANDO
                return

    def _rects_mao_pecas(self, pecas):
        largura_peca, altura_peca = layout.obter("domino.peca_mao")
        espaco = layout.obter("domino.espaco_mao")
        n = len(pecas)
        total_largura = n * largura_peca + max(0, n - 1) * espaco
        largura_tela, altura_tela = pygame.display.get_surface().get_size()
        x0 = largura_tela // 2 - total_largura // 2
        y0 = altura_tela - altura_peca - 40
        pares = []
        for i, peca in enumerate(pecas):
            rect = pygame.Rect(x0 + i * (largura_peca + espaco), y0, largura_peca, altura_peca)
            pares.append((rect, peca))
        return pares

    def _rects_mao(self):
        return self._rects_mao_pecas(self._minha_mao_pecas())

    def _rects_pilha_escolha(self, mesa_rect):
        largura_peca, altura_peca = layout.obter("domino.peca_pilha_escolha")
        espaco = layout.obter("domino.espaco_pilha_escolha")
        pecas = self.pecas_para_escolher
        n = len(pecas)
        por_linha = min(7, max(1, n))
        linhas = math.ceil(n / por_linha) if n else 0
        total_largura = por_linha * largura_peca + (por_linha - 1) * espaco
        total_altura = linhas * altura_peca + max(0, linhas - 1) * espaco
        x0 = mesa_rect.centerx - total_largura // 2
        y0 = mesa_rect.centery - total_altura // 2
        pares = []
        for i, peca in enumerate(pecas):
            linha, col = divmod(i, por_linha)
            rect = pygame.Rect(x0 + col * (largura_peca + espaco), y0 + linha * (altura_peca + espaco),
                                largura_peca, altura_peca)
            pares.append((rect, peca))
        return pares

    # ---------------------------------------------------------------- Desenho
    def _mesa_rect(self):
        largura, altura = pygame.display.get_surface().get_size()
        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.5))
        mesa_rect.center = (largura // 2, int(altura * CENTRO_MESA_Y))
        return mesa_rect

    def _dimensionar_botoes(self):
        """Tamanhos dos botões vêm de core/layout.py. Reaplicado a cada
        desenhar() pra um layout alterado (editor visual, recarregar) valer
        sem recriar a tela - a posição é definida depois, no próprio desenho."""
        self.botao_sair.size = layout.obter("geral.botao_sair")
        self.botao_passar.size = layout.obter("domino.botao_passar")

    def desenhar(self, tela):
        self._dimensionar_botoes()
        largura, altura = tela.get_size()
        tela.fill(BG)

        if self.vencedor_final is not None:
            self._desenhar_tela_final(tela, largura, altura)
            return

        if self.estado is None:
            desenhar_texto(tela, "Conectando à mesa...", largura // 2, altura // 2,
                            tamanho=20, cor=INK, centralizado=True, negrito=True)
            return

        mesa_rect = self._mesa_rect()
        desenhar_mesa(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
        if self.fase_mao == FASE_EMBARALHANDO:
            self._desenhar_embaralhando(tela, mesa_rect)
        elif self.fase_mao == FASE_ESCOLHENDO:
            self._desenhar_escolhendo(tela, mesa_rect)
        else:
            self._desenhar_centro_mesa(tela, mesa_rect)
        self._desenhar_jogadores(tela, mesa_rect)
        self._desenhar_historico(tela, largura, altura)
        self.chat.desenhar(tela, largura, altura)
        self._desenhar_botao_sair(tela)

        if self.mensagem_final is not None:
            self._desenhar_mensagem_final(tela, largura, altura)
            return

        self._desenhar_bandeja_mao(tela, largura, altura)

        if self.fase_mao != FASE_JOGANDO:
            self._desenhar_dica_escolha(tela, largura, altura)
        elif self.estado.get("resultado") is not None:
            self._desenhar_resultado(tela, largura, altura)
        else:
            self._desenhar_controles(tela, largura, altura)

        if self.erro_acao:
            desenhar_badge(tela, largura // 2, altura - 140, self.erro_acao, CORAL,
                            cor_texto=INK, tamanho_fonte=12, borda=INK)

    def _desenhar_embaralhando(self, tela, mesa_rect):
        t = self.timer_embaralhar
        largura_peca, altura_peca = 30, 16
        raio_base = min(mesa_rect.width, mesa_rect.height) * 0.22
        for i in range(self._qtd_embaralhando):
            angulo_base = (i / max(1, self._qtd_embaralhando)) * 2 * math.pi
            raio = raio_base * (0.35 + 0.6 * ((i * 37) % 100) / 100)
            vibra = math.sin(t * 18 + i) * 6
            angulo = angulo_base + t * 3.0 + math.sin(t * 5 + i) * 0.3
            x = mesa_rect.centerx + math.cos(angulo) * (raio + vibra) - largura_peca / 2
            y = mesa_rect.centery + math.sin(angulo) * (raio + vibra) * 0.6 - altura_peca / 2
            desenhar_peca_verso(tela, x, y, largura_peca, altura_peca)
        desenhar_texto(tela, "Embaralhando...", mesa_rect.centerx, mesa_rect.centery,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_escolhendo(self, tela, mesa_rect):
        mouse_pos = pygame.mouse.get_pos()
        for rect, _peca in self._rects_pilha_escolha(mesa_rect):
            hover = rect.collidepoint(mouse_pos)
            desenhar_peca_verso(tela, rect.x, rect.y, rect.width, rect.height, destaque=hover)

    def _desenhar_dica_escolha(self, tela, largura, altura):
        if self.fase_mao == FASE_EMBARALHANDO:
            texto = "Embaralhando as peças..."
        else:
            faltam = len(self.pecas_para_escolher)
            texto = f"Escolha suas peças — faltam {faltam}"
        desenhar_texto(tela, texto, largura // 2, altura - 20,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_topo(self, tela, largura):
        desenhar_badge(tela, largura // 2, 30, f"MÃO #{self.estado['mao_numero']}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        meu = self._meu_jogador()
        pontuacao = meu["pontuacao"] if meu else 0
        desenhar_badge(tela, largura - 24, 30, f"VOCÊ: {pontuacao} pts",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    # ---------------------------------------------------------------- Layout da mesa
    def _layout_mesa(self, mesa_rect):
        """Espelha `DominoTableScreen._layout_mesa`, lendo do snapshot
        público (`self.estado`) em vez de uma `DominoTable` de verdade."""
        largura_base, altura_base = layout.obter("domino.peca_mesa")
        espaco = layout.obter("domino.espaco_mesa")

        primeira = self.estado.get("primeira_peca")
        if not primeira:
            zona = pygame.Rect(0, 0, largura_base + 24, altura_base + 24)
            zona.center = mesa_rect.center
            return [], {"esquerda": zona}

        eh_spinner = self.estado.get("eh_spinner", False)
        ramos = self.estado.get("ramos", {})

        def extensao(direcao, ramo, escala=1.0):
            if not ramo:
                return 0
            eixo = 0 if _horizontal(direcao) else 1
            total = sum(_tamanho_peca(direcao, interno == externo, escala)[eixo] for interno, externo in ramo)
            return total + espaco * (len(ramo) - 1)

        lc, ac = _tamanho_peca("esquerda", eh_spinner)
        ext_esq = extensao("esquerda", ramos.get("esquerda", []))
        ext_dir = extensao("direita", ramos.get("direita", []))
        ext_cima = extensao("cima", ramos.get("cima", [])) if eh_spinner else 0
        ext_baixo = extensao("baixo", ramos.get("baixo", [])) if eh_spinner else 0

        largura_padrao = ext_esq + lc + ext_dir + espaco * 2
        altura_padrao = ext_cima + ac + ext_baixo + espaco * 2
        disp_largura = mesa_rect.width - 40
        disp_altura = mesa_rect.height - 30
        # Sem piso alto aqui de propósito: caber dentro do feltro importa mais
        # que o tamanho mínimo da peça (um piso como 0.35 deixava a fileira
        # "vazar" pra fora da mesa quando tinha peça demais numa linha só).
        escala = max(0.12, min(1.0, disp_largura / max(1, largura_padrao), disp_altura / max(1, altura_padrao)))

        lc, ac = _tamanho_peca("esquerda", eh_spinner, escala)
        centro_rect = pygame.Rect(0, 0, lc, ac)
        centro_rect.center = (0, 0)  # espaço local, provisório - recentralizado no fim (ver abaixo)

        tiles = [(centro_rect, primeira[0], primeira[1], eh_spinner)]
        zonas = {}

        def montar_ramo(direcao, ramo, cursor_inicial):
            cursor = cursor_inicial
            for interno, externo in ramo:
                eh_carroca = interno == externo
                largura, altura = _tamanho_peca(direcao, eh_carroca, escala)
                rect = pygame.Rect(0, 0, largura, altura)
                if direcao == "direita":
                    rect.left = cursor
                    rect.centery = centro_rect.centery
                    cursor = rect.right + int(espaco * escala)
                elif direcao == "esquerda":
                    rect.right = cursor
                    rect.centery = centro_rect.centery
                    cursor = rect.left - int(espaco * escala)
                elif direcao == "baixo":
                    rect.top = cursor
                    rect.centerx = centro_rect.centerx
                    cursor = rect.bottom + int(espaco * escala)
                else:  # cima
                    rect.bottom = cursor
                    rect.centerx = centro_rect.centerx
                    cursor = rect.top - int(espaco * escala)

                if direcao in ("direita", "baixo"):
                    valor_a, valor_b = interno, externo
                else:
                    valor_a, valor_b = externo, interno
                retrato = eh_carroca if _horizontal(direcao) else not eh_carroca
                tiles.append((rect, valor_a, valor_b, retrato))

            largura_zona, altura_zona = _tamanho_peca(direcao, False, escala)
            zona = pygame.Rect(0, 0, largura_zona, altura_zona)
            if direcao == "direita":
                zona.left, zona.centery = cursor, centro_rect.centery
            elif direcao == "esquerda":
                zona.right, zona.centery = cursor, centro_rect.centery
            elif direcao == "baixo":
                zona.top, zona.centerx = cursor, centro_rect.centerx
            else:
                zona.bottom, zona.centerx = cursor, centro_rect.centerx
            zonas[direcao] = zona

        montar_ramo("direita", ramos.get("direita", []), centro_rect.right + int(espaco * escala))
        montar_ramo("esquerda", ramos.get("esquerda", []), centro_rect.left - int(espaco * escala))
        if eh_spinner:
            montar_ramo("baixo", ramos.get("baixo", []), centro_rect.bottom + int(espaco * escala))
            montar_ramo("cima", ramos.get("cima", []), centro_rect.top - int(espaco * escala))

        # Ver comentário equivalente em DominoTableScreen._layout_mesa: os
        # ramos raramente crescem simétrico, então centraliza a caixa que
        # engloba tudo (peças + zonas) em mesa_rect, não a peça central.
        limites = centro_rect.copy()
        for rect, _a, _b, _v in tiles:
            limites.union_ip(rect)
        for rect in zonas.values():
            limites.union_ip(rect)
        deslocamento = (mesa_rect.centerx - limites.centerx, mesa_rect.centery - limites.centery)
        for rect, _a, _b, _v in tiles:
            rect.move_ip(deslocamento)
        for rect in zonas.values():
            rect.move_ip(deslocamento)

        return tiles, zonas

    def _desenhar_centro_mesa(self, tela, mesa_rect):
        tiles, zonas = self._layout_mesa(mesa_rect)
        self._zonas_mesa = zonas

        if not self.estado.get("primeira_peca"):
            peca_obrig = self._minha_peca_obrigatoria()
            if peca_obrig is not None:
                texto = f"Mesa vazia — jogue a peça {peca_obrig}"
            else:
                texto = "Mesa vazia — abra com uma carroça"
            desenhar_texto(tela, texto, mesa_rect.centerx, mesa_rect.centery,
                            tamanho=13, cor=TEXT_MUTED, centralizado=True)
        else:
            for rect, valor_a, valor_b, vertical in tiles:
                desenhar_peca(tela, rect.x, rect.y, rect.width, rect.height, valor_a, valor_b, vertical=vertical)

        if self.peca_arrastando is not None:
            extremidades = self.estado.get("extremidades", {})
            for direcao, rect in self.zonas_drop_ativas.items():
                pygame.draw.rect(tela, YELLOW, rect, border_radius=0)
                pygame.draw.rect(tela, INK, rect, width=2, border_radius=0)
                valor = extremidades.get(direcao)
                if valor is not None:
                    desenhar_texto(tela, str(valor), rect.centerx, rect.centery,
                                    tamanho=14, cor=INK, negrito=True, centralizado=True)

    def _status_jogador(self, jogador, eh_vez_dele):
        if jogador.get("desconectado"):
            return "Desconectado", LOCKED, TEXT_MUTED
        if jogador["id"] == self.meu_id:
            return None, None, None
        if eh_vez_dele:
            return "Pensando...", BLUE, INK
        return f"{jogador['num_pecas']} peças", MINT, SOMBRA

    def _desenhar_jogadores(self, tela, mesa_rect):
        jogadores = self.estado["jogadores"]
        n = len(jogadores)
        posicoes = _posicoes_assentos(mesa_rect, n)
        jogador_da_vez_id = self.estado.get("jogador_da_vez_id")

        for indice, (x, y) in enumerate(posicoes):
            jogador = jogadores[indice]
            eh_eu = jogador["id"] == self.meu_id
            eh_vez_dele = jogador_da_vez_id == jogador["id"]

            painel = pygame.Rect(0, 0, 178, 62)
            painel.centerx = x
            painel.centery = y

            if eh_vez_dele:
                desenhar_glow_de_vez(tela, x, y, 46, 64, self.tempo_decorrido)

            desenhar_painel(tela, painel, cor=PANEL, radius=0, deslocamento_sombra=(3, 3))

            cor_avatar = YELLOW if eh_eu else PALETA_AVATAR[jogador["id"] % len(PALETA_AVATAR)]
            desenhar_avatar(tela, painel.x + 34, painel.centery, 22, cor_avatar, _iniciais(jogador["nome"]))

            desenhar_texto(tela, jogador["nome"], painel.x + 62, painel.y + 12, tamanho=13,
                            cor=INK, negrito=True)
            desenhar_texto(tela, f"{jogador['pontuacao']} pts", painel.x + 62, painel.y + 30, tamanho=12,
                            cor=TEXT_MUTED, familia="mono")

            status_texto, status_cor, status_cor_texto = self._status_jogador(jogador, eh_vez_dele)
            if status_texto:
                desenhar_badge(tela, painel.x + 62, painel.y + 48, status_texto, status_cor,
                                cor_texto=status_cor_texto, tamanho_fonte=9, ancorar="midleft")

    def _desenhar_bandeja_mao(self, tela, largura, altura):
        meu = self._meu_jogador()
        if meu is None:
            return

        if self.fase_mao != FASE_JOGANDO:
            reveladas = [p for p in self._minha_mao_pecas() if p not in self.pecas_para_escolher]
            for rect, peca in self._rects_mao_pecas(reveladas):
                desenhar_peca(tela, rect.x, rect.y, rect.width, rect.height, peca.a, peca.b, vertical=True)
            return

        eh_minha_vez = self._eh_minha_vez()
        jogaveis = {p for p, _direcao in self._minhas_jogadas_possiveis()} if eh_minha_vez else set()

        for rect, peca in self._rects_mao():
            if peca == self.peca_arrastando:
                continue
            destaque = eh_minha_vez and peca in jogaveis
            desenhar_peca(tela, rect.x, rect.y, rect.width, rect.height, peca.a, peca.b,
                          vertical=True, destaque=destaque)

        if self.peca_arrastando is not None:
            largura_peca, altura_peca = layout.obter("domino.peca_mao")
            x = self.pos_arraste[0] - largura_peca // 2
            y = self.pos_arraste[1] - altura_peca // 2
            desenhar_peca(tela, x, y, largura_peca, altura_peca,
                          self.peca_arrastando.a, self.peca_arrastando.b, vertical=True, destaque=True)

    def _desenhar_historico(self, tela, largura, altura):
        ultima = self.estado.get("ultima_acao") if self.estado else None
        if not ultima:
            return
        desenhar_badge(tela, largura - 24, 64, ultima[:44], PANEL, cor_texto=INK,
                        tamanho_fonte=11, ancorar="topright", borda=INK)

    def _desenhar_controles(self, tela, largura, altura):
        if not self._eh_minha_vez():
            vez_id = self.estado.get("jogador_da_vez_id")
            nome_vez = next((j["nome"] for j in self.estado["jogadores"] if j["id"] == vez_id), "-")
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)
            return

        if not self._tenho_jogada():
            desenhar_texto(tela, "Você não tem peça pra jogar — clique em Passar",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            posicionar_botao_passar(self.botao_passar, [r for r, _ in self._rects_mao()], largura, altura)
            mouse_pos = pygame.mouse.get_pos()
            desenhar_botao(tela, self.botao_passar, "Passar",
                            hover=self.botao_passar.collidepoint(mouse_pos), tamanho_fonte=16, cor=CORAL)
        elif self.peca_arrastando is not None:
            desenhar_texto(tela, "Arraste até uma ponta destacada e solte pra jogar",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)
        else:
            desenhar_texto(tela, "Sua vez — arraste uma peça em destaque até a mesa",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_resultado(self, tela, largura, altura):
        resultado = self.estado["resultado"]
        n_linhas = 1 + len(resultado["detalhes"])
        painel = pygame.Rect(0, 0, 480, 130 + 26 * n_linhas)
        painel.center = (largura // 2, altura - 200)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        desenhar_texto(tela, "RESULTADO DA MAO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")

        if resultado["tipo"] == "bloqueio_total":
            prefixo = "Jogo travou! " + ("Empate entre " if resultado.get("empate") else "")
            texto_vitoria = (f"{prefixo}{resultado['vencedor']} venceu com menos pontos "
                              f"na mão (+{resultado['pontos_ganhos']} pts)")
        else:
            extra = " (com bônus de carroça!)" if resultado.get("carroca_bonus") else ""
            texto_vitoria = f"{resultado['vencedor']} bateu e ganhou {resultado['pontos_ganhos']} pontos{extra}!"
        desenhar_texto(tela, texto_vitoria, painel.centerx, painel.y + 52,
                        tamanho=14, cor=INK, centralizado=True, negrito=True)

        y = painel.y + 82
        for d in resultado["detalhes"]:
            desenhar_texto(tela, f"{d['jogador']} ficou com {d['pontos']} pontos em peças na mão",
                            painel.centerx, y, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            y += 26

        desenhar_texto(tela, "Aguardando o anfitrião avançar para a próxima mão...",
                        painel.centerx, painel.bottom - 20, tamanho=11, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_mensagem_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((*INK[:3], 150))
        tela.blit(overlay, (0, 0))

        painel = pygame.Rect(0, 0, 440, 200)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)
        desenhar_texto(tela, "Sala encerrada", painel.centerx, painel.y + 50,
                        tamanho=26, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, self.mensagem_final, painel.centerx, painel.y + 100,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=12)

    def _desenhar_tela_final(self, tela, largura, altura):
        painel = pygame.Rect(0, 0, 440, 220)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        desenhar_texto(tela, "FIM DE JOGO", painel.centerx, painel.y + 46,
                        tamanho=32, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, f"Vencedor: {self.vencedor_final}", painel.centerx, painel.y + 100,
                        tamanho=19, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=12)
