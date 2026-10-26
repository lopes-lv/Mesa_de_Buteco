"""
mesa_remota_pifpaf_screen.py - Tela do jogador "cliente" no multiplayer
local do Pif Paf (ver MULTIPLAYER_PLANO.md e pifpaf_screen.py, do qual esta
tela é o espelho do lado do host).

Não roda nenhuma `PifPafTable` de verdade: guarda o último snapshot de
`estado` público recebido do host e a própria mão (`sua_mao`), reconciliando
a cada atualização para preservar a ordenação manual que o jogador já tiver
feito (arrastar para organizar). As checagens de "posso bater agora?" são
recalculadas localmente com as mesmas funções puras de `pifpaf_logic.py`
(operam só sobre a própria mão, já que o coringa é sempre o Joker impresso) -
evita duplicar a regra e evita ida-e-volta de rede a cada carta selecionada.
"""
import queue
from typing import Any

import pygame
from core.ui_theme import tamanho_janela
from core.deck import Card
from core.ui_theme import (
    BG, PANEL, INK, SOMBRA, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_carta,
    desenhar_mesa, desenhar_avatar, desenhar_badge, desenhar_kbd,
    desenhar_glow_de_vez,
)
from .pifpaf_logic import pode_bater_mao, VITORIAS_PARA_VENCER
from .pifpaf_screen import (
    posicoes_assentos, mesa_rect_para, topo_da_mao, posicao_selo_historico,
    LARGURA_PAINEL_ASSENTO, ALTURA_PAINEL_ASSENTO,
)
from core.chat_widget import ChatWidget
from core import layout
from rede import protocolo

# Tamanhos de carta, espaçamentos e botões: mesmas chaves "pifpaf.*"/"geral.*"
# de core/layout.py que pifpaf_screen.py usa.
LIMIAR_ARRASTO_PX = 6

PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]

NAIPE_UNICODE = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}


def _carta_str(carta):
    return f"{carta.texto}{NAIPE_UNICODE.get(carta.simbolo_naipe, carta.simbolo_naipe)}"


def _iniciais(nome):
    partes = nome.replace('"', "").split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    return nome[:2].upper()


class MesaRemotaPifPafScreen:
    def __init__(self, app, sala_cliente):
        self.app = app
        self.sala = sala_cliente
        self.meu_id = sala_cliente.meu_id

        self.estado: Any = None
        self.minha_mao = []  # lista de [valor, naipe]
        self.carta_selecionada = None
        self.arraste: Any = None
        self.tempo_decorrido = 0.0

        self.erro_acao = None
        self.tempo_erro_acao = 0.0
        self.mensagem_final = None
        self.vencedor_final = None

        self.chat = ChatWidget(self._enviar_chat)

        self.botao_monte = pygame.Rect(0, 0, 0, 0)
        self.botao_descarte = pygame.Rect(0, 0, 0, 0)
        self.botao_mao_fechada = pygame.Rect(0, 0, 0, 0)
        self.botao_bater = pygame.Rect(0, 0, 0, 0)
        self.botao_descartar = pygame.Rect(0, 0, 0, 0)
        self.botao_sair = pygame.Rect(0, 0, 0, 0)
        self._dimensionar_botoes()
        self.monte_rect = pygame.Rect(0, 0, *layout.obter("pifpaf.carta_monte"))
        self.descarte_rect = pygame.Rect(0, 0, *layout.obter("pifpaf.carta_monte"))

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

    def _enviar_acao(self, acao, carta=None):
        msg = {"tipo": protocolo.ACAO_PIFPAF, "acao": acao}
        if carta is not None:
            msg["carta"] = list(carta)
        self.sala.enviar(msg)

    def _atualizar_minha_mao(self, cartas_servidor):
        """Reconcilia com o servidor preservando a ordem que o jogador já
        tiver organizado: mantém na mesma posição relativa quem já estava,
        só acrescenta cartas novas (compradas) no final e remove as que
        sumiram (descartadas)."""
        novas = [tuple(c) for c in cartas_servidor]
        restante = list(novas)
        reconciliada = []
        for carta_local in self.minha_mao:
            chave = tuple(carta_local)
            if chave in restante:
                reconciliada.append(list(chave))
                restante.remove(chave)
        reconciliada.extend(list(c) for c in restante)
        self.minha_mao = reconciliada
        if self.carta_selecionada is not None and tuple(self.carta_selecionada) not in novas:
            self.carta_selecionada = None

    # ---------------------------------------------------------------- Regras (locais, puras)
    def _minha_mao_cards(self):
        return [Card(v, n) for v, n in self.minha_mao]

    def _pode_bater(self):
        if self.estado is None or not self.estado.get("comprou_nesta_vez"):
            return False
        return pode_bater_mao(self._minha_mao_cards())

    def _pode_bater_mao_fechada(self):
        if self.estado is None or self.estado.get("comprou_nesta_vez"):
            return False
        meu = self._meu_jogador()
        if meu is None or meu.get("ja_agiu_nesta_mao"):
            return False
        return pode_bater_mao(self._minha_mao_cards())

    def _pode_bater_descartando(self, carta):
        if self.estado is None or not self.estado.get("comprou_nesta_vez"):
            return False
        resto = self._minha_mao_cards()
        alvo = Card(carta[0], carta[1])
        if alvo not in resto:
            return False
        resto.remove(alvo)
        return pode_bater_mao(resto)

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
                self.estado = msg
            elif tipo == protocolo.SUA_MAO:
                self._atualizar_minha_mao(msg.get("cartas", []))
            elif tipo == protocolo.ERRO_ACAO:
                self.erro_acao = msg.get("motivo")
                self.tempo_erro_acao = 3.0
            elif tipo == protocolo.FIM_DE_JOGO:
                self.vencedor_final = msg.get("vencedor")
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

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

        if self.estado is None or self.estado.get("resultado") is not None:
            return

        meu = self._meu_jogador()
        if meu is None:
            return

        # Arrastar/selecionar a própria mão é liberado a qualquer momento,
        # mesmo fora do turno (só reorganiza visualmente).
        if self._tratar_evento_mao(evento):
            return

        if not self._eh_minha_vez():
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._tratar_clique(evento.pos)
        elif evento.type == pygame.KEYDOWN:
            self._tratar_tecla(evento.key)

    def _rects_mao(self):
        largura_carta, altura_carta = layout.obter("pifpaf.carta_mao")
        espaco = layout.obter("pifpaf.espaco_mao")
        n = len(self.minha_mao)
        total_largura = n * largura_carta + (n - 1) * espaco
        largura_tela, altura_tela = tamanho_janela()
        x0 = largura_tela // 2 - total_largura // 2
        y0 = topo_da_mao(largura_tela, altura_tela, altura_carta)
        pares = []
        for i, carta in enumerate(self.minha_mao):
            rect = pygame.Rect(x0 + i * (largura_carta + espaco), y0, largura_carta, altura_carta)
            pares.append((rect, carta))
        return pares

    def _tratar_evento_mao(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, (rect, _carta) in enumerate(self._rects_mao()):
                if rect.collidepoint(evento.pos):
                    self.arraste = {"indice": i, "inicio": evento.pos, "pos": evento.pos, "moveu": False}
                    return True
            return False

        if evento.type == pygame.MOUSEMOTION and self.arraste is not None:
            self.arraste["pos"] = evento.pos
            dx = evento.pos[0] - self.arraste["inicio"][0]
            dy = evento.pos[1] - self.arraste["inicio"][1]
            if abs(dx) > LIMIAR_ARRASTO_PX or abs(dy) > LIMIAR_ARRASTO_PX:
                self.arraste["moveu"] = True
            return True

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.arraste is not None:
            indice_origem = self.arraste["indice"]
            if self.arraste["moveu"]:
                self._reordenar_mao(indice_origem, evento.pos[0])
            else:
                carta = self.minha_mao[indice_origem]
                self.carta_selecionada = None if self.carta_selecionada == carta else carta
            self.arraste = None
            return True

        return False

    def _reordenar_mao(self, indice_origem, mouse_x):
        carta = self.minha_mao.pop(indice_origem)
        rects_restantes = self._rects_mao()
        novo_indice = len(rects_restantes)
        for i, (rect, _) in enumerate(rects_restantes):
            if mouse_x < rect.centerx:
                novo_indice = i
                break
        self.minha_mao.insert(novo_indice, carta)

    def _tratar_clique(self, pos):
        comprou = self.estado.get("comprou_nesta_vez", False)
        if not comprou:
            if self._pode_bater_mao_fechada() and self.botao_mao_fechada.collidepoint(pos):
                self._enviar_acao("bater_mao_fechada")
                return
            if self.monte_rect.collidepoint(pos) or self.botao_monte.collidepoint(pos):
                self._enviar_acao("comprar_monte")
            elif self.descarte_rect.collidepoint(pos) or self.botao_descarte.collidepoint(pos):
                self._enviar_acao("comprar_descarte")
            return

        if self.botao_bater.collidepoint(pos) and self._pode_bater():
            self._enviar_acao("bater")
            return

        if self.botao_descartar.collidepoint(pos) and self.carta_selecionada is not None:
            self._enviar_acao("descartar", self.carta_selecionada)
            self.carta_selecionada = None

    def _tratar_tecla(self, tecla):
        comprou = self.estado.get("comprou_nesta_vez", False)
        if not comprou:
            if tecla == pygame.K_b and self._pode_bater_mao_fechada():
                self._enviar_acao("bater_mao_fechada")
            elif tecla == pygame.K_m:
                self._enviar_acao("comprar_monte")
            elif tecla == pygame.K_d:
                self._enviar_acao("comprar_descarte")
            return

        if tecla == pygame.K_b and self._pode_bater():
            self._enviar_acao("bater")
        elif tecla == pygame.K_RETURN and self.carta_selecionada is not None:
            self._enviar_acao("descartar", self.carta_selecionada)
            self.carta_selecionada = None

    # ---------------------------------------------------------------- Desenho
    def _dimensionar_botoes(self):
        """Tamanhos dos botões vêm de core/layout.py. Reaplicado a cada
        desenhar() pra um layout alterado (editor visual, recarregar) valer
        sem recriar a tela - a posição é definida depois, no próprio desenho."""
        self.botao_monte.size = self.botao_descarte.size = layout.obter("pifpaf.botao_compra")
        self.botao_mao_fechada.size = layout.obter("pifpaf.botao_mao_fechada")
        self.botao_bater.size = self.botao_descartar.size = layout.obter("pifpaf.botao_jogada")
        self.botao_sair.size = layout.obter("geral.botao_sair")

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

        mesa_rect = mesa_rect_para(largura, altura)
        desenhar_mesa(tela, mesa_rect)

        self._desenhar_topo(tela, largura)
        self._desenhar_centro_mesa(tela, mesa_rect)
        self._desenhar_jogadores(tela, mesa_rect)
        self._desenhar_historico(tela, largura, altura)
        self.chat.desenhar(tela, largura, altura)
        self._desenhar_botao_sair(tela)

        if self.mensagem_final is not None:
            self._desenhar_mensagem_final(tela, largura, altura)
            return

        self._desenhar_bandeja_mao(tela, largura, altura)

        if self.estado.get("resultado") is not None:
            self._desenhar_resultado(tela, largura, altura)
        else:
            self._desenhar_controles(tela, largura, altura)

        if self.erro_acao:
            desenhar_badge(tela, largura // 2, altura - 140, self.erro_acao, CORAL,
                            cor_texto=INK, tamanho_fonte=12, borda=INK)

    def _desenhar_topo(self, tela, largura):
        desenhar_badge(tela, largura // 2, 30, f"MAO #{self.estado['mao_numero']}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        meu = self._meu_jogador()
        vitorias = meu["vitorias"] if meu else 0
        desenhar_badge(tela, largura - 24, 30, f"VOCE: {vitorias}/{VITORIAS_PARA_VENCER} VITORIAS",
                        YELLOW, cor_texto=SOMBRA, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    def _desenhar_centro_mesa(self, tela, mesa_rect):
        largura_carta, altura_carta = layout.obter("pifpaf.carta_monte")
        espaco = layout.obter("pifpaf.espaco_monte")
        cx, cy = mesa_rect.centerx, mesa_rect.centery

        self.monte_rect = pygame.Rect(0, 0, largura_carta, altura_carta)
        self.monte_rect.center = (cx - espaco - largura_carta // 2, cy)
        desenhar_carta(tela, self.monte_rect.x, self.monte_rect.y, largura_carta, altura_carta,
                        virada_para_baixo=True)
        desenhar_badge(tela, self.monte_rect.centerx, self.monte_rect.bottom + 18,
                        f"MONTE ({self.estado['monte_restante']})", PANEL, cor_texto=INK, tamanho_fonte=10, borda=INK)

        self.descarte_rect = pygame.Rect(0, 0, largura_carta, altura_carta)
        self.descarte_rect.center = (cx + espaco + largura_carta // 2, cy)
        if self.estado.get("descarte_topo"):
            carta_topo = Card(*self.estado["descarte_topo"])
            desenhar_carta(tela, self.descarte_rect.x, self.descarte_rect.y, largura_carta, altura_carta,
                            carta=carta_topo)
        desenhar_badge(tela, self.descarte_rect.centerx, self.descarte_rect.bottom + 18,
                        "DESCARTE", PANEL, cor_texto=INK, tamanho_fonte=10, borda=INK)

    def _desenhar_jogadores(self, tela, mesa_rect):
        jogadores = self.estado["jogadores"]
        n = len(jogadores)
        posicoes = posicoes_assentos(mesa_rect, n)
        jogador_da_vez_id = self.estado.get("jogador_da_vez_id")

        for indice, (x, y) in enumerate(posicoes):
            jogador = jogadores[indice]
            eh_eu = jogador["id"] == self.meu_id
            eh_vez_dele = jogador_da_vez_id == jogador["id"]

            painel = pygame.Rect(0, 0, LARGURA_PAINEL_ASSENTO, ALTURA_PAINEL_ASSENTO)
            painel.centerx = x
            painel.centery = y

            if eh_vez_dele:
                largura_op, altura_op = layout.obter("pifpaf.carta_oponente")
                desenhar_glow_de_vez(tela, x, y, largura_op, altura_op, self.tempo_decorrido)

            desenhar_painel(tela, painel, cor=PANEL, radius=0, deslocamento_sombra=(3, 3))

            cor_avatar = YELLOW if eh_eu else PALETA_AVATAR[jogador["id"] % len(PALETA_AVATAR)]
            desenhar_avatar(tela, painel.x + 34, painel.centery, 22, cor_avatar, _iniciais(jogador["nome"]))

            desenhar_texto(tela, jogador["nome"], painel.x + 62, painel.y + 12, tamanho=13,
                            cor=INK, negrito=True)
            desenhar_texto(tela, f"{jogador['vitorias']} vit.", painel.x + 62, painel.y + 30, tamanho=12,
                            cor=TEXT_MUTED, familia="mono")

            if jogador.get("desconectado"):
                status = "Desconectado"
            elif eh_eu:
                status = None
            elif eh_vez_dele and self.estado.get("comprou_nesta_vez"):
                status = "Pensando..."
            elif eh_vez_dele:
                status = "Comprando..."
            else:
                status = f"{jogador['num_cartas']} cartas"

            if status:
                desenhar_badge(tela, painel.x + 62, painel.y + 48, status,
                                MINT, cor_texto=SOMBRA, tamanho_fonte=9, ancorar="midleft")

    def _desenhar_bandeja_mao(self, tela, largura, altura):
        meu = self._meu_jogador()
        if meu is None:
            return

        pares = self._rects_mao()
        indice_arrastando = self.arraste["indice"] if (self.arraste and self.arraste["moveu"]) else None

        for i, (rect, carta_dados) in enumerate(pares):
            if i == indice_arrastando:
                continue
            carta = Card(*carta_dados)
            destaque = carta_dados == self.carta_selecionada
            y = rect.y - 14 if destaque else rect.y
            desenhar_carta(tela, rect.x, y, rect.width, rect.height, carta=carta, destaque=destaque)

        if indice_arrastando is not None:
            rect, carta_dados = pares[indice_arrastando]
            carta = Card(*carta_dados)
            mouse_x, mouse_y = self.arraste["pos"]
            desenhar_carta(tela, mouse_x - rect.width // 2, mouse_y - rect.height // 2,
                            rect.width, rect.height, carta=carta, destaque=True)

    def _desenhar_historico(self, tela, largura, altura):
        ultima = self.estado.get("ultima_acao") if self.estado else None
        if not ultima:
            return
        texto = ultima[:44]
        x, y = posicao_selo_historico(texto, largura, altura, len(self.estado["jogadores"]))
        desenhar_badge(tela, x, y, texto, PANEL, cor_texto=INK, tamanho_fonte=11, ancorar="topright", borda=INK)

    def _desenhar_resultado(self, tela, largura, altura):
        resultado = self.estado["resultado"]
        n_linhas = 1 + len(resultado["detalhes"])
        painel = pygame.Rect(0, 0, 480, 130 + 26 * n_linhas)
        painel.center = (largura // 2, altura - 200)
        desenhar_painel(tela, painel, cor=PANEL, radius=0)

        desenhar_texto(tela, "RESULTADO DA MAO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")

        if resultado.get("empate"):
            desenhar_texto(tela, "Ninguem bateu a tempo - mao empatada, ninguem pontua.",
                            painel.centerx, painel.y + 52, tamanho=14, cor=INK, centralizado=True, negrito=True)
        else:
            if resultado.get("mao_fechada"):
                texto_vitoria = f"{resultado['vencedor']} bateu de MÃO FECHADA e ganhou 2 vitórias!"
            else:
                texto_vitoria = f"{resultado['vencedor']} bateu e ganhou a mão!"
            desenhar_texto(tela, texto_vitoria, painel.centerx, painel.y + 52,
                            tamanho=14, cor=INK, centralizado=True, negrito=True)

            y = painel.y + 82
            for d in resultado["detalhes"]:
                desenhar_texto(tela, f"{d['jogador']} ficou com {d['pontos']} pontos em cartas soltas",
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

    def _desenhar_controles(self, tela, largura, altura):
        eh_minha_vez = self._eh_minha_vez()
        mouse_pos = pygame.mouse.get_pos()
        base_y = altura - 40

        if not eh_minha_vez:
            vez_id = self.estado.get("jogador_da_vez_id")
            nome_vez = next((j["nome"] for j in self.estado["jogadores"] if j["id"] == vez_id), "-")
            desenhar_badge(tela, largura // 2, 58, f"Vez de: {nome_vez}",
                            PANEL, cor_texto=INK, tamanho_fonte=12, borda=INK)
            return

        comprou = self.estado.get("comprou_nesta_vez", False)
        if not comprou:
            pode_mao_fechada = self._pode_bater_mao_fechada()
            espaco = layout.obter("pifpaf.espaco_botoes")

            if pode_mao_fechada:
                largura_total = (self.botao_mao_fechada.width + self.botao_monte.width
                                  + self.botao_descarte.width + 2 * espaco)
                x0 = largura // 2 - largura_total // 2
                self.botao_mao_fechada.midleft = (x0, base_y)
                self.botao_monte.midleft = (self.botao_mao_fechada.right + espaco, base_y)
                self.botao_descarte.midleft = (self.botao_monte.right + espaco, base_y)

                desenhar_badge(tela, largura // 2, base_y - 48,
                                "MÃO FECHADA! Bata sem comprar e ganhe em dobro",
                                YELLOW, cor_texto=SOMBRA, tamanho_fonte=12, borda=INK)
                desenhar_botao(tela, self.botao_mao_fechada, "Bater (2x)",
                                hover=self.botao_mao_fechada.collidepoint(mouse_pos),
                                tamanho_fonte=16, cor=YELLOW)
                desenhar_kbd(tela, self.botao_mao_fechada.right - 14, self.botao_mao_fechada.bottom - 14,
                              "B", ancorar="bottomright")
            else:
                self.botao_monte.midright = (largura // 2 - espaco // 2, base_y)
                self.botao_descarte.midleft = (largura // 2 + espaco // 2, base_y)

            desenhar_botao(tela, self.botao_monte, "Comprar Monte",
                            hover=self.botao_monte.collidepoint(mouse_pos), tamanho_fonte=16, cor=BLUE, cor_texto=INK)
            desenhar_kbd(tela, self.botao_monte.right - 14, self.botao_monte.bottom - 14, "M", ancorar="bottomright")

            desenhar_botao(tela, self.botao_descarte, "Comprar Descarte",
                            hover=self.botao_descarte.collidepoint(mouse_pos), tamanho_fonte=16, cor=MINT)
            desenhar_kbd(tela, self.botao_descarte.right - 14, self.botao_descarte.bottom - 14, "D",
                         ancorar="bottomright")
            return

        pode_bater = self._pode_bater()
        self.botao_bater.midright = (largura // 2 - 15, base_y)
        desenhar_botao(tela, self.botao_bater, "Bater", ativo=pode_bater,
                        hover=pode_bater and self.botao_bater.collidepoint(mouse_pos),
                        tamanho_fonte=18, cor=YELLOW)
        desenhar_kbd(tela, self.botao_bater.right - 12, self.botao_bater.bottom - 12, "B", ancorar="bottomright")

        pode_descartar = self.carta_selecionada is not None
        descarte_fecha_mao = pode_descartar and self._pode_bater_descartando(self.carta_selecionada)

        self.botao_descartar.midleft = (largura // 2 + 15, base_y)
        if descarte_fecha_mao:
            desenhar_badge(tela, largura // 2, base_y - 60,
                            "Essa carta fecha sua mão! Descartar = Bater",
                            YELLOW, cor_texto=SOMBRA, tamanho_fonte=12, borda=INK)
            desenhar_botao(tela, self.botao_descartar, "Bater!", ativo=True,
                            hover=self.botao_descartar.collidepoint(mouse_pos),
                            tamanho_fonte=18, cor=YELLOW)
        else:
            desenhar_botao(tela, self.botao_descartar, "Descartar", ativo=pode_descartar,
                            hover=pode_descartar and self.botao_descartar.collidepoint(mouse_pos),
                            tamanho_fonte=18, cor=CORAL, cor_texto=INK)
        desenhar_kbd(tela, self.botao_descartar.right - 12, self.botao_descartar.bottom - 12, "Enter",
                     ancorar="bottomright")

        if not pode_descartar:
            desenhar_texto(tela, "Arraste as cartas para organizar a mao - clique numa carta para descartar",
                            largura // 2, base_y - 44, tamanho=13, cor=TEXT_MUTED, centralizado=True)
