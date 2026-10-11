"""
multiplayer_screens.py - Telas do modo "Multiplayer Local" (ver
MULTIPLAYER_PLANO.md, seção 2): CriarSalaScreen, EntrarSalaScreen, LobbyScreen.

Seguem o mesmo estilo visual de screens.py (ui_theme.py), mas ficam num
módulo à parte para não misturar o fluxo solo (sem rede) com o de rede.
"""
import threading

import pygame
from core.ui_theme import (
    BG, PANEL, INK, TEXT_MUTED, YELLOW, CORAL, MINT, LOCKED,
    desenhar_texto, desenhar_botao, desenhar_painel, desenhar_badge,
)
from rede.anfitriao import AnfitriaoSala
from rede.cliente import ClienteSala
from rede.descoberta import procurar_sala_na_rede
from rede.protocolo import PORTA_TCP_PADRAO
from rede import protocolo
from core.ui_widgets import CampoTexto
from core.chat_widget import ChatWidget

# Cada jogo tem seu próprio limite de assentos (Dominó duplo-seis só
# comporta 2-4 jogadores; Hold'em/Pif Paf usam o limite geral de 8 já
# existente no solo vs bots). Fonte única usada tanto ao criar a sala
# (AnfitriaoSala.max_jogadores) quanto para calcular quantos bots cabem nas
# vagas restantes (main.py:iniciar_partida_multiplayer_host).
MAX_JOGADORES_POR_JOGO = {"holdem": 8, "pifpaf": 8, "domino": 4}


def _parse_ip_porta(texto):
    texto = texto.strip()
    if ":" in texto:
        ip, porta = texto.rsplit(":", 1)
        try:
            return ip.strip(), int(porta.strip())
        except ValueError:
            return ip.strip(), PORTA_TCP_PADRAO
    return texto, PORTA_TCP_PADRAO


class CriarSalaScreen:
    """Pede o nome do jogador e sobe o AnfitriaoSala ao confirmar."""

    def __init__(self, app, jogo="holdem"):
        self.app = app
        self.jogo = jogo
        self.campo_nome = CampoTexto(pygame.Rect(0, 0, 360, 52), placeholder="Seu nome")
        self.campo_nome.focado = True
        self.botao_criar = pygame.Rect(0, 0, 260, 60)
        self.botao_voltar = pygame.Rect(0, 0, 150, 48)
        self.erro = None

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.app.ir_para_config(self.jogo)
            return
        self.campo_nome.tratar_evento(evento)
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_voltar.collidepoint(evento.pos):
                self.app.ir_para_config(self.jogo)
            elif self.botao_criar.collidepoint(evento.pos):
                self._criar_sala()
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
            self._criar_sala()

    def _criar_sala(self):
        nome = self.campo_nome.texto.strip() or "Anfitrião"
        max_jogadores = MAX_JOGADORES_POR_JOGO.get(self.jogo, 8)
        sala = AnfitriaoSala(nome, max_jogadores=max_jogadores)
        if not sala.iniciar():
            self.erro = f"Não foi possível abrir a sala: {sala.erro_fatal}"
            return
        self.app.ir_para_lobby_host(sala, jogo=self.jogo)

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        desenhar_texto(tela, "CRIAR SALA", largura // 2, altura // 6,
                        tamanho=28, cor=INK, negrito=True, centralizado=True, familia="display")

        painel = pygame.Rect(0, 0, 440, 260)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, radius=0)

        desenhar_texto(tela, "Como você quer ser chamado na mesa?", painel.centerx, painel.y + 34,
                        tamanho=15, cor=INK, negrito=True, centralizado=True)

        self.campo_nome.rect.midtop = (painel.centerx, painel.y + 62)
        self.campo_nome.desenhar(tela)

        self.botao_criar.midtop = (painel.centerx, painel.y + 140)
        desenhar_botao(tela, self.botao_criar, "Criar Sala",
                        hover=self.botao_criar.collidepoint(mouse_pos), tamanho_fonte=19)

        if self.erro:
            desenhar_texto(tela, self.erro, painel.centerx, painel.bottom - 24,
                            tamanho=12, cor=CORAL, centralizado=True)

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)


class EntrarSalaScreen:
    """Pede nome + código (ou IP:porta manual) e conecta num ClienteSala."""

    def __init__(self, app):
        self.app = app
        self.campo_nome = CampoTexto(pygame.Rect(0, 0, 360, 52), placeholder="Seu nome")
        self.campo_codigo = CampoTexto(pygame.Rect(0, 0, 360, 52), placeholder="Código (ex.: KTR4)",
                                        max_len=8, maiusculas=True)
        self.campo_ip = CampoTexto(pygame.Rect(0, 0, 360, 44), placeholder="ou IP:porta manual", max_len=32)
        self.botao_conectar = pygame.Rect(0, 0, 260, 60)
        self.botao_voltar = pygame.Rect(0, 0, 150, 48)

        self.estado = "idle"  # idle | buscando | conectando | erro
        self.mensagem_erro = None
        self.sala_cliente = None

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.app.ir_para_config("holdem")
            return
        for campo in (self.campo_nome, self.campo_codigo, self.campo_ip):
            campo.tratar_evento(evento)
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_voltar.collidepoint(evento.pos):
                self.app.ir_para_config("holdem")
            elif self.botao_conectar.collidepoint(evento.pos):
                self._conectar()
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
            self._conectar()

    def _conectar(self):
        if self.estado in ("buscando", "conectando"):
            return
        nome = self.campo_nome.texto.strip() or "Jogador"
        ip_manual = self.campo_ip.texto.strip()
        codigo = self.campo_codigo.texto.strip().upper()

        if ip_manual:
            ip, porta = _parse_ip_porta(ip_manual)
            self._iniciar_conexao(nome, ip, porta)
        elif codigo:
            self.estado = "buscando"
            self.mensagem_erro = None
            threading.Thread(target=self._buscar_e_conectar, args=(nome, codigo), daemon=True).start()
        else:
            self.mensagem_erro = "Digite o código da sala ou um IP:porta manual."

    def _buscar_e_conectar(self, nome, codigo):
        resultado = procurar_sala_na_rede(codigo, timeout=3.0)
        if resultado is None:
            self.estado = "erro"
            self.mensagem_erro = "Sala não encontrada na rede. Tente digitar o IP:porta manualmente."
            return
        self._iniciar_conexao(nome, resultado["ip"], resultado["porta_tcp"])

    def _iniciar_conexao(self, nome, ip, porta):
        self.sala_cliente = ClienteSala(nome)
        self.sala_cliente.conectar_async(ip, porta)
        self.estado = "conectando"

    def atualizar(self, dt):
        if self.estado == "conectando" and self.sala_cliente:
            status = self.sala_cliente.status
            if status == "conectado":
                self.app.ir_para_lobby_cliente(self.sala_cliente)
            elif status in ("erro", "recusado"):
                self.estado = "erro"
                self.mensagem_erro = self.sala_cliente.erro or "Não foi possível conectar."
                self.sala_cliente = None

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        desenhar_texto(tela, "ENTRAR EM SALA", largura // 2, altura // 6,
                        tamanho=28, cor=INK, negrito=True, centralizado=True, familia="display")

        painel = pygame.Rect(0, 0, 460, 380)
        painel.center = (largura // 2, altura // 2)
        desenhar_painel(tela, painel, radius=0)

        desenhar_texto(tela, "Seu nome", painel.x + 40, painel.y + 30, tamanho=13, cor=TEXT_MUTED, negrito=True)
        self.campo_nome.rect.midtop = (painel.centerx, painel.y + 48)
        self.campo_nome.desenhar(tela)

        desenhar_texto(tela, "Código da sala", painel.x + 40, painel.y + 112, tamanho=13, cor=TEXT_MUTED, negrito=True)
        self.campo_codigo.rect.midtop = (painel.centerx, painel.y + 130)
        self.campo_codigo.desenhar(tela)

        desenhar_texto(tela, "— ou —", painel.centerx, painel.y + 196, tamanho=12, cor=TEXT_MUTED, centralizado=True)

        self.campo_ip.rect.midtop = (painel.centerx, painel.y + 212)
        self.campo_ip.desenhar(tela)

        self.botao_conectar.midtop = (painel.centerx, painel.y + 274)
        texto_botao = {"buscando": "Procurando sala...", "conectando": "Conectando..."}.get(
            self.estado, "Conectar")
        ativo = self.estado not in ("buscando", "conectando")
        desenhar_botao(tela, self.botao_conectar, texto_botao,
                        hover=ativo and self.botao_conectar.collidepoint(mouse_pos),
                        ativo=ativo, tamanho_fonte=18)

        if self.mensagem_erro:
            desenhar_texto(tela, self.mensagem_erro, painel.centerx, painel.bottom - 22,
                            tamanho=12, cor=CORAL, centralizado=True)

        self.botao_voltar.topleft = (30, 30)
        desenhar_botao(tela, self.botao_voltar, "< Voltar",
                        hover=self.botao_voltar.collidepoint(mouse_pos), tamanho_fonte=15, cor=PANEL)


class LobbyScreen:
    """Comum a host e cliente: mostra quem já entrou e aguarda o host iniciar."""

    def __init__(self, app, sala_rede=None, sala_cliente=None, jogo="holdem"):
        self.app = app
        self.sala_rede = sala_rede        # AnfitriaoSala, só quando somos o host
        self.sala_cliente = sala_cliente  # ClienteSala, só quando somos cliente
        self.eh_host = sala_rede is not None
        self.jogo = jogo  # só é decidido pelo host - o cliente descobre via "iniciar_partida"

        self.completar_com_bots = True
        self.checkbox_bots = pygame.Rect(0, 0, 26, 26)
        self.botao_iniciar = pygame.Rect(0, 0, 300, 60)
        self.botao_sair = pygame.Rect(0, 0, 150, 48)

        self.mensagem_final = None  # sala encerrada / desconectado (lado cliente)
        self.chat = ChatWidget(self._enviar_chat)

    def _enviar_chat(self, texto):
        if self.eh_host:
            nome = self.sala_rede.nome_anfitriao
            self.chat.adicionar_mensagem(nome, texto)
            self.sala_rede.enviar_para_todos({"tipo": protocolo.CHAT, "remetente": nome, "texto": texto})
        else:
            self.sala_cliente.enviar({"tipo": protocolo.CHAT, "texto": texto})

    def _sair(self):
        if self.eh_host:
            self.sala_rede.encerrar()
        elif self.sala_cliente:
            self.sala_cliente.fechar()
        self.app.ir_para_menu()

    def tratar_evento(self, evento):
        if self.chat.tratar_evento(evento):
            return
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self._sair()
            return
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.botao_sair.collidepoint(evento.pos):
                self._sair()
                return
            if self.eh_host:
                if self.checkbox_bots.collidepoint(evento.pos):
                    self.completar_com_bots = not self.completar_com_bots
                elif self.botao_iniciar.collidepoint(evento.pos) and self._pode_iniciar():
                    self._iniciar_partida()

    def _pode_iniciar(self):
        if self.completar_com_bots:
            return True
        minimo = 3 if self.jogo == "domino" else 2
        return self.sala_rede.total_jogadores() >= minimo

    def _iniciar_partida(self):
        jogadores = self.sala_rede.lista_jogadores_lobby()
        self.app.iniciar_partida_multiplayer_host(self.sala_rede, jogadores, self.completar_com_bots, self.jogo)

    def atualizar(self, dt):
        if self.eh_host and self.sala_rede:
            while not self.sala_rede.mensagens_entrantes.empty():
                _jogador_id, msg = self.sala_rede.mensagens_entrantes.get_nowait()
                if msg.get("tipo") == protocolo.CHAT:
                    self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))
        if not self.eh_host and self.sala_cliente:
            while not self.sala_cliente.mensagens_entrantes.empty():
                msg = self.sala_cliente.mensagens_entrantes.get_nowait()
                if msg.get("tipo") == "iniciar_partida":
                    self.app.iniciar_partida_multiplayer_cliente(self.sala_cliente, msg.get("jogo", "holdem"))
                    return
                if msg.get("tipo") == protocolo.CHAT:
                    self.chat.adicionar_mensagem(msg.get("remetente", "?"), msg.get("texto", ""))
            if self.sala_cliente.status in ("sala_encerrada", "desconectado"):
                self.mensagem_final = self.sala_cliente.erro or "Conexão com o anfitrião perdida."

    def desenhar(self, tela):
        largura, altura = tela.get_size()
        tela.fill(BG)
        mouse_pos = pygame.mouse.get_pos()

        desenhar_texto(tela, "SALA DE ESPERA", largura // 2, altura // 8,
                        tamanho=28, cor=INK, negrito=True, centralizado=True, familia="display")

        painel = pygame.Rect(0, 0, 480, 440)
        painel.center = (largura // 2, altura // 2 + 10)
        desenhar_painel(tela, painel, radius=0)

        self.chat.desenhar(tela, largura, altura)

        if self.mensagem_final:
            desenhar_texto(tela, "Sala encerrada", painel.centerx, painel.centery - 20,
                            tamanho=20, cor=INK, negrito=True, centralizado=True)
            desenhar_texto(tela, self.mensagem_final, painel.centerx, painel.centery + 12,
                            tamanho=13, cor=TEXT_MUTED, centralizado=True)
            self.botao_sair.center = (painel.centerx, painel.centery + 60)
            desenhar_botao(tela, self.botao_sair, "Voltar ao Menu",
                            hover=self.botao_sair.collidepoint(mouse_pos), tamanho_fonte=14, cor=PANEL)
            return

        if self.eh_host:
            desenhar_badge(tela, painel.centerx, painel.y + 40, self.sala_rede.codigo,
                            YELLOW, cor_texto=SOMBRA, tamanho_fonte=22, familia="mono", borda=INK)
            desenhar_texto(tela, f"IP: {self.sala_rede.ip_local}:{self.sala_rede.porta_tcp} (fallback manual)",
                            painel.centerx, painel.y + 78, tamanho=12, cor=TEXT_MUTED, centralizado=True)
            jogadores = self.sala_rede.lista_jogadores_lobby()
        else:
            desenhar_texto(tela, "Aguardando o anfitrião iniciar a partida...",
                            painel.centerx, painel.y + 50, tamanho=15, cor=INK, negrito=True, centralizado=True)
            jogadores = self.sala_cliente.jogadores_lobby

        y_lista = painel.y + 116
        desenhar_texto(tela, f"JOGADORES ({len(jogadores)})", painel.x + 30, y_lista,
                        tamanho=13, cor=TEXT_MUTED, negrito=True)
        y_lista += 28
        for jogador in jogadores:
            rotulo = jogador["nome"] + ("  (anfitrião)" if jogador.get("anfitriao") else "")
            desenhar_texto(tela, rotulo, painel.x + 40, y_lista, tamanho=15, cor=INK)
            y_lista += 30

        if self.eh_host:
            self.checkbox_bots.midleft = (painel.x + 30, painel.bottom - 118)
            marcado = self.completar_com_bots
            pygame.draw.rect(tela, MINT if marcado else PANEL, self.checkbox_bots, border_radius=0)
            pygame.draw.rect(tela, INK, self.checkbox_bots, width=2, border_radius=0)
            desenhar_texto(tela, "Completar vagas restantes com bots",
                            self.checkbox_bots.right + 12, self.checkbox_bots.centery - 9,
                            tamanho=13, cor=INK)

            pode_iniciar = self._pode_iniciar()
            self.botao_iniciar.center = (painel.centerx, painel.bottom - 58)
            desenhar_botao(tela, self.botao_iniciar, "Iniciar Partida",
                            hover=pode_iniciar and self.botao_iniciar.collidepoint(mouse_pos),
                            ativo=pode_iniciar, tamanho_fonte=19)
            if not pode_iniciar:
                desenhar_texto(tela, "Aguardando mais gente entrar (ou marque 'completar com bots')",
                                painel.centerx, self.botao_iniciar.bottom + 16,
                                tamanho=11, cor=TEXT_MUTED, centralizado=True)

        self.botao_sair.topleft = (30, 30)
        desenhar_botao(tela, self.botao_sair, "< Sair", hover=self.botao_sair.collidepoint(mouse_pos),
                        tamanho_fonte=15, cor=PANEL)
