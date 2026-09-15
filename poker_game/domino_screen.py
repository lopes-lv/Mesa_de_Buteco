"""
domino_screen.py - Tela principal de gameplay do modo Dominó (bloqueio e
compra, livre-pra-todos - ver domino_logic.py e MELHORIAS.md).

Diferente do Pôquer/Pif Paf, aqui não existem botões de ação: comprar do
monte e passar a vez não são decisões do jogador (acontecem sozinhos quando
não há jogada possível, ver `DominoTable.deve_comprar/deve_passar`) - o
único gesto do jogador é clicar numa peça jogável da própria mão e, se ela
encaixar nas duas pontas da mesa, escolher qual lado.
"""
import math
import queue
from collections import deque

import pygame
from ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL, BLUE, MINT, PURPLE, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_avatar,
    desenhar_badge, desenhar_glow_de_vez,
)
from domino_theme import desenhar_peca, desenhar_peca_verso
from domino_logic import Peca, TIPO_HUMANO_REMOTO
from domino_bot_ai import escolher_jogada_bot
from chat_widget import ChatWidget
from rede import protocolo

DELAY_BOT_SEGUNDOS = 0.7
TAMANHO_PECA_MAO = (46, 92)
TAMANHO_PECA_MESA = (40, 64)

PALETA_AVATAR = [CORAL, PURPLE, BLUE, MINT, (230, 160, 60)]


class DominoTableScreen:
    def __init__(self, app, mesa, sala_rede=None):
        self.app = app
        self.mesa = mesa
        self.id_humano = mesa.jogadores[0].id
        self.sala_rede = sala_rede

        self.timer_bot = 0.0
        self.tempo_decorrido = 0.0
        self.peca_selecionada = None
        self.rect_ponta_esquerda = None
        self.rect_ponta_direita = None

        self.botao_continuar = pygame.Rect(0, 0, 240, 56)
        self.botao_sair = pygame.Rect(0, 0, 110, 44)

        self.historico = deque(maxlen=1)
        self.chat = ChatWidget(self._enviar_chat_host) if sala_rede is not None else None
        self._iniciar_mao()

    # ---------------------------------------------------------------- Histórico
    def _registrar(self, texto, cor=TEXT_MUTED):
        self.historico.append((texto, cor))

    def _iniciar_mao(self):
        self.mesa.iniciar_nova_mao()
        self.peca_selecionada = None
        self.historico.clear()
        self._enviar_maos_privadas()
        self._broadcast_estado()

    def _jogador(self, id_jogador):
        return next(j for j in self.mesa.jogadores if j.id == id_jogador)

    def _jogador_por_id(self, id_jogador):
        return next((j for j in self.mesa.jogadores if j.id == id_jogador), None)

    # ---------------------------------------------------------------- Rede (host)
    def _enviar_chat_host(self, texto):
        nome = self.sala_rede.nome_anfitriao
        self.chat.adicionar_mensagem(nome, texto)
        self.sala_rede.enviar_para_todos({"tipo": protocolo.CHAT, "remetente": nome, "texto": texto})

    def _enviar_maos_privadas(self):
        if self.sala_rede is None:
            return
        for jogador in self.mesa.jogadores:
            if jogador.tipo == TIPO_HUMANO_REMOTO and not jogador.eliminado:
                self.sala_rede.enviar_para(jogador.id, {
                    "tipo": protocolo.SUA_MAO,
                    "pecas": [[p.a, p.b] for p in jogador.mao],
                })

    def _broadcast_estado(self):
        if self.sala_rede is None:
            return
        self._enviar_maos_privadas()
        self.sala_rede.enviar_para_todos(self._serializar_estado())

    def _serializar_estado(self):
        jogador_da_vez = self.mesa.jogador_da_vez()
        jogadores = []
        for j in self.mesa.jogadores:
            jogadores.append({
                "id": j.id, "nome": j.nome, "stack": j.stack, "eliminado": j.eliminado,
                "num_pecas": len(j.mao),
                "desconectado": bool(self.sala_rede and j.id in self.sala_rede.desconectados),
            })
        return {
            "tipo": protocolo.ESTADO,
            "mao_numero": self.mesa.mao_numero,
            "cadeia": [[p.a, p.b] for p in self.mesa.cadeia],
            "extremidade_esquerda": self.mesa.extremidade_esquerda,
            "extremidade_direita": self.mesa.extremidade_direita,
            "monte_restante": len(self.mesa.monte),
            "jogador_da_vez_id": jogador_da_vez.id if jogador_da_vez else None,
            "jogadores": jogadores,
            "ultima_acao": self.historico[-1][0] if self.historico else None,
            "resultado": self.mesa.resultado_mao,
        }

    def _drenar_mensagens_rede(self):
        while True:
            try:
                jogador_id, msg = self.sala_rede.mensagens_entrantes.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == protocolo.ACAO_DOMINO:
                self._processar_acao_remota(jogador_id, msg)
            elif tipo == protocolo.CHAT:
                self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))

    def _processar_acao_remota(self, jogador_id, msg):
        jogador_da_vez = self.mesa.jogador_da_vez()
        jogador = self._jogador_por_id(jogador_id)
        acao = msg.get("acao")

        erro = None
        peca = None
        lado = msg.get("lado")
        if jogador is None:
            erro = "Jogador desconhecido"
        elif jogador_da_vez is None or jogador_da_vez.id != jogador_id:
            erro = "Não é a sua vez"
        elif acao != "jogar":
            erro = "Ação inválida"
        else:
            dados_peca = msg.get("peca")
            if not dados_peca or len(dados_peca) != 2 or lado not in ("esquerda", "direita"):
                erro = "Jogada inválida"
            else:
                peca = Peca(dados_peca[0], dados_peca[1])
                if self.mesa.deve_comprar(jogador) or self.mesa.deve_passar(jogador):
                    erro = "Você precisa comprar/passar antes"
                elif peca not in jogador.mao:
                    erro = "Você não tem essa peça"
                elif (peca, lado) not in self.mesa.jogadas_possiveis(jogador):
                    erro = "Essa jogada não é válida agora"

        if erro:
            self.sala_rede.enviar_para(jogador_id, {"tipo": protocolo.ERRO_ACAO, "motivo": erro})
            return

        self._jogar(jogador, peca, lado)

    # ---------------------------------------------------------------- Ações de mesa
    def _jogar(self, jogador, peca, lado):
        ok = self.mesa.jogar(jogador, peca, lado)
        if ok:
            self._registrar(f"{jogador.nome} jogou {peca}", MINT)
            if self.mesa.resultado_mao is not None:
                self.mesa.marcar_eliminados()
        self._broadcast_estado()
        return ok

    def _passar(self, jogador):
        self.mesa.passar(jogador)
        self._registrar(f"{jogador.nome} passou (sem jogada)", TEXT_MUTED)
        if self.mesa.resultado_mao is not None:
            self.mesa.marcar_eliminados()
        self._broadcast_estado()

    def _comecar_proxima_mao_ou_finalizar(self):
        if self.mesa.jogo_tem_vencedor():
            vencedor = self.mesa.jogadores_na_mesa()[0]
            if self.sala_rede is not None:
                self.sala_rede.enviar_para_todos({"tipo": protocolo.FIM_DE_JOGO, "vencedor": vencedor.nome})
            self.app.finalizar_jogo(vencedor.nome)
        else:
            self._iniciar_mao()

    def _sair_para_menu(self):
        if self.sala_rede is not None:
            self.sala_rede.encerrar()
        self.app.ir_para_menu()

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento):
        if self.chat is not None and self.chat.tratar_evento(evento):
            return

        if self.app.jogo_finalizado:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self._sair_para_menu()
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_sair.collidepoint(evento.pos):
                self._sair_para_menu()
                return

        if self.mesa.resultado_mao is not None:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.botao_continuar.collidepoint(evento.pos):
                    self._comecar_proxima_mao_ou_finalizar()
            return

        if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
            return

        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        if not eh_vez_do_humano:
            return
        humano = self._jogador(self.id_humano)

        if self.peca_selecionada is not None:
            if self.rect_ponta_esquerda and self.rect_ponta_esquerda.collidepoint(evento.pos):
                self._tentar_jogar(humano, self.peca_selecionada, "esquerda")
                return
            if self.rect_ponta_direita and self.rect_ponta_direita.collidepoint(evento.pos):
                self._tentar_jogar(humano, self.peca_selecionada, "direita")
                return
            self.peca_selecionada = None

        for rect, peca in self._rects_mao_humano(humano):
            if rect.collidepoint(evento.pos):
                self._selecionar_peca(humano, peca)
                return

    def _selecionar_peca(self, humano, peca):
        opcoes = [lado for p, lado in self.mesa.jogadas_possiveis(humano) if p == peca]
        if not opcoes:
            return
        if len(opcoes) == 1:
            self._tentar_jogar(humano, peca, opcoes[0])
        else:
            self.peca_selecionada = peca

    def _tentar_jogar(self, humano, peca, lado):
        self.peca_selecionada = None
        self._jogar(humano, peca, lado)

    # ---------------------------------------------------------------- Update
    def atualizar(self, dt):
        self.tempo_decorrido += dt

        if self.sala_rede is not None:
            self._drenar_mensagens_rede()

        if self.app.jogo_finalizado or self.mesa.resultado_mao is not None:
            return

        jogador_da_vez = self.mesa.jogador_da_vez()
        if jogador_da_vez is None:
            return

        houve_auto = False
        while self.mesa.deve_comprar(jogador_da_vez):
            self.mesa.comprar(jogador_da_vez)
            houve_auto = True
        if self.mesa.deve_passar(jogador_da_vez):
            self._passar(jogador_da_vez)
            return
        if houve_auto:
            self._broadcast_estado()

        desconectado = (
            self.sala_rede is not None
            and jogador_da_vez.tipo == TIPO_HUMANO_REMOTO
            and jogador_da_vez.id in self.sala_rede.desconectados
        )

        if jogador_da_vez.is_bot or desconectado:
            self.timer_bot += dt
            if self.timer_bot < DELAY_BOT_SEGUNDOS:
                return
            self.timer_bot = 0.0
            resultado = escolher_jogada_bot(jogador_da_vez, self.mesa)
            if resultado is not None:
                peca, lado = resultado
                self._jogar(jogador_da_vez, peca, lado)
        else:
            self.timer_bot = 0.0

    # ---------------------------------------------------------------- Desenho
    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)

        mesa_rect = pygame.Rect(0, 0, int(largura * 0.72), int(altura * 0.5))
        mesa_rect.center = (largura // 2, int(altura * 0.36))
        pygame.draw.rect(tela, INK, mesa_rect.move(8, 8), border_radius=28)
        pygame.draw.rect(tela, (223, 219, 205), mesa_rect, border_radius=28)
        pygame.draw.rect(tela, INK, mesa_rect, width=5, border_radius=28)

        self._desenhar_topo(tela, largura)
        self._desenhar_centro_mesa(tela, mesa_rect)
        self._desenhar_jogadores(tela, mesa_rect)
        self._desenhar_historico(tela, largura, altura)

        if self.chat is not None:
            self.chat.desenhar(tela, largura, altura)

        if self.app.jogo_finalizado:
            self._desenhar_tela_final(tela, largura, altura)
            return

        self._desenhar_botao_sair(tela)
        self._desenhar_bandeja_mao(tela, largura, altura)

        if self.mesa.resultado_mao is not None:
            self._desenhar_resultado(tela, largura, altura)
        else:
            self._desenhar_controles(tela, largura, altura)

    def _desenhar_topo(self, tela, largura):
        desenhar_badge(tela, largura // 2, 30, f"MÃO #{self.mesa.mao_numero}   MONTE: {len(self.mesa.monte)}",
                        PANEL, cor_texto=INK, tamanho_fonte=13, familia="mono", borda=INK)
        humano = self._jogador(self.id_humano)
        desenhar_badge(tela, largura - 24, 30, f"VOCÊ: {humano.stack}",
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

        cadeia = self.mesa.cadeia
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

            for rect, valor in ((self.rect_ponta_esquerda, self.mesa.extremidade_esquerda),
                                 (self.rect_ponta_direita, self.mesa.extremidade_direita)):
                pygame.draw.rect(tela, YELLOW, rect, border_radius=8)
                pygame.draw.rect(tela, INK, rect, width=2, border_radius=8)
                desenhar_texto(tela, str(valor), rect.centerx, rect.centery - 9,
                                tamanho=16, cor=INK, negrito=True, centralizado=True)

    def _iniciais(self, nome):
        partes = nome.replace('"', "").split()
        if len(partes) >= 2:
            return (partes[0][0] + partes[1][0]).upper()
        return nome[:2].upper()

    def _status_jogador(self, jogador, eh_vez_dele):
        if jogador.eliminado:
            return "Eliminado", LOCKED, TEXT_MUTED
        if (self.sala_rede is not None and jogador.tipo == TIPO_HUMANO_REMOTO
                and jogador.id in self.sala_rede.desconectados):
            return "Desconectado", LOCKED, TEXT_MUTED
        if jogador.id == self.id_humano:
            return None, None, None
        if eh_vez_dele:
            return "Pensando...", BLUE, PANEL
        return f"{len(jogador.mao)} peças", MINT, INK

    def _desenhar_jogadores(self, tela, mesa_rect):
        n = len(self.mesa.jogadores)
        posicoes = self._posicoes_assentos(mesa_rect, n)
        jogador_da_vez = self.mesa.jogador_da_vez() if not self.app.jogo_finalizado else None

        for indice, (x, y) in enumerate(posicoes):
            jogador = self.mesa.jogadores[indice]
            eh_humano = jogador.id == self.id_humano
            eh_vez_dele = jogador_da_vez is not None and jogador.id == jogador_da_vez.id

            painel = pygame.Rect(0, 0, 178, 62)
            painel.centerx = x
            painel.centery = y

            if eh_vez_dele:
                desenhar_glow_de_vez(tela, x, y, 46, 64, self.tempo_decorrido)

            fundo = LOCKED if jogador.eliminado else PANEL
            desenhar_painel(tela, painel, cor=fundo, radius=16, deslocamento_sombra=(3, 3))

            cor_avatar = YELLOW if eh_humano else PALETA_AVATAR[jogador.id % len(PALETA_AVATAR)]
            desenhar_avatar(tela, painel.x + 34, painel.centery, 22, cor_avatar, self._iniciais(jogador.nome))

            cor_nome = TEXT_MUTED if jogador.eliminado else INK
            desenhar_texto(tela, jogador.nome, painel.x + 62, painel.y + 12, tamanho=13, cor=cor_nome, negrito=True)
            desenhar_texto(tela, str(jogador.stack), painel.x + 62, painel.y + 30, tamanho=12,
                            cor=TEXT_MUTED, familia="mono")

            status_texto, status_cor, status_cor_texto = self._status_jogador(jogador, eh_vez_dele)
            if status_texto:
                desenhar_badge(tela, painel.x + 62, painel.y + 48, status_texto, status_cor,
                                cor_texto=status_cor_texto, tamanho_fonte=9, ancorar="midleft")

    def _posicoes_assentos(self, mesa_rect, n_jogadores):
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

    # ---------------------------------------------------------------- Bandeja da mão
    def _rects_mao_humano(self, humano):
        largura_peca, altura_peca = TAMANHO_PECA_MAO
        espaco = 8
        n = len(humano.mao)
        total_largura = n * largura_peca + max(0, n - 1) * espaco
        largura_tela, altura_tela = pygame.display.get_surface().get_size()
        x0 = largura_tela // 2 - total_largura // 2
        y0 = altura_tela - altura_peca - 40
        pares = []
        for i, peca in enumerate(humano.mao):
            rect = pygame.Rect(x0 + i * (largura_peca + espaco), y0, largura_peca, altura_peca)
            pares.append((rect, peca))
        return pares

    def _desenhar_bandeja_mao(self, tela, largura, altura):
        humano = self._jogador(self.id_humano)
        if humano.eliminado:
            return
        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        jogaveis = {p for p, _lado in self.mesa.jogadas_possiveis(humano)} if eh_vez_do_humano else set()

        for rect, peca in self._rects_mao_humano(humano):
            destaque = (peca == self.peca_selecionada) or (eh_vez_do_humano and peca in jogaveis
                                                             and self.peca_selecionada is None)
            y = rect.y - 10 if peca == self.peca_selecionada else rect.y
            desenhar_peca(tela, rect.x, y, rect.width, rect.height, peca, vertical=True, destaque=destaque)

    def _desenhar_historico(self, tela, largura, altura):
        if not self.historico:
            return
        texto, cor = self.historico[-1]
        desenhar_badge(tela, largura - 24, 64, texto[:44], PANEL, cor_texto=INK,
                        tamanho_fonte=11, ancorar="topright", borda=cor)

    def _desenhar_controles(self, tela, largura, altura):
        jogador_da_vez = self.mesa.jogador_da_vez()
        eh_vez_do_humano = jogador_da_vez is not None and jogador_da_vez.id == self.id_humano
        if not eh_vez_do_humano:
            nome_vez = jogador_da_vez.nome if jogador_da_vez else "-"
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
        resultado = self.mesa.resultado_mao
        n_linhas = 1 + len(resultado["detalhes"])
        painel = pygame.Rect(0, 0, 480, 110 + 26 * n_linhas)
        painel.center = (largura // 2, altura - 200)
        desenhar_painel(tela, painel, cor=PANEL, radius=20)

        desenhar_texto(tela, "RESULTADO DA MÃO", painel.centerx, painel.y + 24,
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

        self.botao_continuar.center = (painel.centerx, painel.bottom - 30)
        mouse_pos = pygame.mouse.get_pos()
        desenhar_botao(tela, self.botao_continuar, "Continuar",
                        hover=self.botao_continuar.collidepoint(mouse_pos), tamanho_fonte=18)

    def _desenhar_tela_final(self, tela, largura, altura):
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((*INK, 150))
        tela.blit(overlay, (0, 0))

        painel = pygame.Rect(0, 0, 440, 220)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, cor=PANEL, radius=24)

        desenhar_texto(tela, "FIM DE JOGO", painel.centerx, painel.y + 46,
                        tamanho=32, cor=INK, negrito=True, centralizado=True, familia="display")
        desenhar_texto(tela, f"Vencedor: {self.app.nome_vencedor}", painel.centerx, painel.y + 100,
                        tamanho=19, cor=TEXT_MUTED, centralizado=True)
        desenhar_badge(tela, painel.centerx, painel.y + 150, "Clique para voltar ao menu",
                        YELLOW, cor_texto=INK, tamanho_fonte=12)
