"""
mesa_remota_domino_screen.py - Tela do jogador "cliente" no multiplayer
local do Dominó (ver domino_screen.py, do qual esta tela é o espelho do
lado do host, e MULTIPLAYER_PLANO.md pela arquitetura geral).

Não roda nenhuma `DominoTable` de verdade: guarda o snapshot público de
`estado` e a própria mão (`sua_mao`). Comprar/passar não existem como ação
de rede (são automáticos no host, ver domino_screen.py) - a única coisa que
este lado manda é "jogar uma peça". As checagens de "essa peça é jogável?"
são recalculadas localmente com a mesma função pura de `domino_logic.py`
(`jogadas_possiveis_em`), já que as extremidades da mesa são públicas.
"""
import math
import queue

import pygame
from ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_avatar,
    desenhar_badge, desenhar_glow_de_vez,
)
from domino_theme import desenhar_peca
from domino_logic import Peca, jogadas_possiveis_em
from chat_widget import ChatWidget
from rede import protocolo

TAMANHO_PECA_MAO = (46, 92)
TAMANHO_PECA_MESA = (40, 64)
PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]


def _posicoes_assentos(mesa_rect, n_jogadores):
    if n_jogadores == 2:
        angulos = [90, 270]
    elif n_jogadores == 3:
        angulos = [90, 210, 330]
    else:
        angulos = [90, 180, 270, 0]

    posicoes = []
    for i in range(n_jogadores):
        ang = math.radians(angulos[i])
        rx = mesa_rect.width // 2 + 70
        ry = mesa_rect.height // 2 + 70
        x = mesa_rect.centerx + int(rx * math.cos(ang))
        y = mesa_rect.centery + int(ry * math.sin(ang))
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
        self.peca_selecionada = None
        self.rect_ponta_esquerda = None
        self.rect_ponta_direita = None
        self.tempo_decorrido = 0.0

        self.erro_acao = None
        self.tempo_erro_acao = 0.0
        self.mensagem_final = None
        self.vencedor_final = None

        self.chat = ChatWidget(self._enviar_chat)
        self.botao_sair = pygame.Rect(0, 0, 110, 44)

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

    def _minhas_jogadas_possiveis(self):
        if self.estado is None:
            return []
        return jogadas_possiveis_em(self._minha_mao_pecas(), self.estado.get("extremidade_esquerda"),
                                     self.estado.get("extremidade_direita"))

    def _enviar_jogada(self, peca, lado):
        self.sala.enviar({"tipo": protocolo.ACAO_DOMINO, "acao": "jogar", "peca": [peca.a, peca.b], "lado": lado})

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
                if not self._eh_minha_vez():
                    self.peca_selecionada = None
            elif tipo == protocolo.SUA_MAO:
                self.minha_mao = msg.get("pecas", [])
                validas = {tuple(p) for p in self.minha_mao}
                if self.peca_selecionada is not None and (self.peca_selecionada.a, self.peca_selecionada.b) not in validas:
                    self.peca_selecionada = None
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
        if meu is None or meu["eliminado"]:
            return

        if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
            return

        if not self._eh_minha_vez():
            return

        if self.peca_selecionada is not None:
            if self.rect_ponta_esquerda and self.rect_ponta_esquerda.collidepoint(evento.pos):
                self._tentar_jogar(self.peca_selecionada, "esquerda")
                return
            if self.rect_ponta_direita and self.rect_ponta_direita.collidepoint(evento.pos):
                self._tentar_jogar(self.peca_selecionada, "direita")
                return
            self.peca_selecionada = None

        for rect, peca in self._rects_mao():
            if rect.collidepoint(evento.pos):
                self._selecionar_peca(peca)
                return

    def _rects_mao(self):
        largura_peca, altura_peca = TAMANHO_PECA_MAO
        espaco = 8
        pecas = self._minha_mao_pecas()
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

    def _selecionar_peca(self, peca):
        opcoes = [lado for p, lado in self._minhas_jogadas_possiveis() if p == peca]
        if not opcoes:
            return
        if len(opcoes) == 1:
            self._tentar_jogar(peca, opcoes[0])
        else:
            self.peca_selecionada = peca

    def _tentar_jogar(self, peca, lado):
        self.peca_selecionada = None
        self._enviar_jogada(peca, lado)

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)

        if self.vencedor_final is not None:
            self._desenhar_tela_final(tela, largura, altura)
            return

        if self.estado is None:
            desenhar_texto(tela, "Conectando à mesa...", largura // 2, altura // 2,
                            tamanho=20, cor=INK, centralizado=True, negrito=True)
            return

        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.5))
        mesa_rect.center = (largura // 2, int(altura * 0.36))
        pygame.draw.rect(tela, INK, mesa_rect.move(8, 8), border_radius=28)
        pygame.draw.rect(tela, (223, 219, 205), mesa_rect, border_radius=28)
        pygame.draw.rect(tela, INK, mesa_rect, width=5, border_radius=28)

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
                            cor_texto=PANEL, tamanho_fonte=12, borda=INK)

    def _desenhar_topo(self, tela, largura):
        desenhar_badge(tela, largura // 2, 30,
                        f"MÃO #{self.estado['mao_numero']}   MONTE: {self.estado['monte_restante']}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        meu = self._meu_jogador()
        stack = meu["stack"] if meu else 0
        desenhar_badge(tela, largura - 24, 30, f"VOCÊ: {stack}",
                        YELLOW, cor_texto=INK, tamanho_fonte=13, familia="mono",
                        ancorar="midright", borda=INK)

    def _desenhar_botao_sair(self, tela):
        self.botao_sair.topleft = (20, 20)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_sair, "Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=14, cor=PANEL)

    def _desenhar_centro_mesa(self, tela, mesa_rect):
        self.rect_ponta_esquerda = None
        self.rect_ponta_direita = None

        cadeia = [Peca(a, b) for a, b in self.estado.get("cadeia", [])]
        n = len(cadeia)
        if n == 0:
            desenhar_texto(tela, "Mesa vazia — a primeira peça vale qualquer uma",
                            mesa_rect.centerx, mesa_rect.centery, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            return

        largura_peca, altura_peca = TAMANHO_PECA_MESA
        espaco = 4
        disponivel = mesa_rect.width - 50
        largura_padrao = n * largura_peca + (n - 1) * espaco
        escala = min(1.0, disponivel / max(1, largura_padrao))
        lp = max(16, int(largura_peca * escala))
        ap = max(24, int(altura_peca * escala))
        total_largura = n * lp + max(0, n - 1) * espaco
        x0 = mesa_rect.centerx - total_largura // 2
        y0 = mesa_rect.centery - ap // 2

        for i, peca in enumerate(cadeia):
            x = x0 + i * (lp + espaco)
            desenhar_peca(tela, x, y0, lp, ap, peca)

        if self.peca_selecionada is not None:
            largura_zona = 34
            self.rect_ponta_esquerda = pygame.Rect(0, 0, largura_zona, ap)
            self.rect_ponta_esquerda.midright = (x0 - 8, y0 + ap // 2)
            self.rect_ponta_direita = pygame.Rect(0, 0, largura_zona, ap)
            self.rect_ponta_direita.midleft = (x0 + total_largura + 8, y0 + ap // 2)

            for rect, valor in ((self.rect_ponta_esquerda, self.estado.get("extremidade_esquerda")),
                                 (self.rect_ponta_direita, self.estado.get("extremidade_direita"))):
                pygame.draw.rect(tela, YELLOW, rect, border_radius=8)
                pygame.draw.rect(tela, INK, rect, width=2, border_radius=8)
                desenhar_texto(tela, str(valor), rect.centerx, rect.centery - 9,
                                tamanho=16, cor=INK, negrito=True, centralizado=True)

    def _status_jogador(self, jogador, eh_vez_dele):
        if jogador["eliminado"]:
            return "Eliminado", LOCKED, TEXT_MUTED
        if jogador.get("desconectado"):
            return "Desconectado", LOCKED, TEXT_MUTED
        if jogador["id"] == self.meu_id:
            return None, None, None
        if eh_vez_dele:
            return "Pensando...", BLUE, PANEL
        return f"{jogador['num_pecas']} peças", MINT, INK

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

            fundo = LOCKED if jogador["eliminado"] else PANEL
            desenhar_painel(tela, painel, cor=fundo, radius=16, deslocamento_sombra=(3, 3))

            cor_avatar = YELLOW if eh_eu else PALETA_AVATAR[jogador["id"] % len(PALETA_AVATAR)]
            desenhar_avatar(tela, painel.x + 34, painel.centery, 22, cor_avatar, _iniciais(jogador["nome"]))

            cor_nome = TEXT_MUTED if jogador["eliminado"] else INK
            desenhar_texto(tela, jogador["nome"], painel.x + 62, painel.y + 12, tamanho=13,
                            cor=cor_nome, negrito=True)
            desenhar_texto(tela, str(jogador["stack"]), painel.x + 62, painel.y + 30, tamanho=12,
                            cor=TEXT_MUTED, familia="mono")

            status_texto, status_cor, status_cor_texto = self._status_jogador(jogador, eh_vez_dele)
            if status_texto:
                desenhar_badge(tela, painel.x + 62, painel.y + 48, status_texto, status_cor,
                                cor_texto=status_cor_texto, tamanho_fonte=9, ancorar="midleft")

    def _desenhar_bandeja_mao(self, tela, largura, altura):
        meu = self._meu_jogador()
        if meu is None or meu["eliminado"]:
            return
        eh_minha_vez = self._eh_minha_vez()
        jogaveis = {p for p, _lado in self._minhas_jogadas_possiveis()} if eh_minha_vez else set()

        for rect, peca in self._rects_mao():
            destaque = (peca == self.peca_selecionada) or (eh_minha_vez and peca in jogaveis
                                                             and self.peca_selecionada is None)
            y = rect.y - 10 if peca == self.peca_selecionada else rect.y
            desenhar_peca(tela, rect.x, y, rect.width, rect.height, peca, vertical=True, destaque=destaque)

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

        if self.peca_selecionada is not None:
            desenhar_texto(tela, "Essa peça encaixa nas duas pontas — clique em qual lado jogar",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)
        else:
            desenhar_texto(tela, "Sua vez — clique numa peça em destaque para jogar",
                            largura // 2, altura - 20, tamanho=13, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_resultado(self, tela, largura, altura):
        resultado = self.estado["resultado"]
        n_linhas = 1 + len(resultado["detalhes"])
        painel = pygame.Rect(0, 0, 480, 130 + 26 * n_linhas)
        painel.center = (largura // 2, altura - 200)
        desenhar_painel(tela, painel, cor=PANEL, radius=20)

        desenhar_texto(tela, "RESULTADO DA MAO", painel.centerx, painel.y + 24,
                        tamanho=17, cor=INK, centralizado=True, negrito=True, familia="display")

        if resultado.get("bloqueio"):
            prefixo = "Jogo bloqueado! " + ("Empate entre " if resultado.get("empate") else "")
            texto_vitoria = f"{prefixo}{resultado['vencedor']} venceu com menos pontos na mão"
        else:
            texto_vitoria = f"{resultado['vencedor']} bateu e ganhou {resultado['pote']} fichas!"
        desenhar_texto(tela, texto_vitoria, painel.centerx, painel.y + 52,
                        tamanho=14, cor=INK, centralizado=True, negrito=True)

        y = painel.y + 82
        for d in resultado["detalhes"]:
            desenhar_texto(tela, f"{d['jogador']} pagou {d['pontos']} pontos em peças na mão",
                            painel.centerx, y, tamanho=13, cor=TEXT_MUTED, centralizado=True)
            y += 26

        desenhar_texto(tela, "Aguardando o anfitrião avançar para a próxima mão...",
                        painel.centerx, painel.bottom - 20, tamanho=11, cor=TEXT_MUTED, centralizado=True)

    def _desenhar_mensagem_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((*INK, 150))
        tela.blit(overlay, (0, 0))

        painel = pygame.Rect(0, 0, 440, 200)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=24)
        desenhar_texto(tela, "Sala encerrada", painel.centerx, painel.y + 50,
                        tamanho=26, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, self.mensagem_final, painel.centerx, painel.y + 100,
                        tamanho=13, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=INK, tamanho_fonte=12)

    def _desenhar_tela_final(self, tela, largura, altura):
        painel = pygame.Rect(0, 0, 440, 220)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=24)

        desenhar_texto(tela, "FIM DE JOGO", painel.centerx, painel.y + 46,
                        tamanho=32, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, f"Vencedor: {self.vencedor_final}", painel.centerx, painel.y + 100,
                        tamanho=19, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=INK, tamanho_fonte=12)
