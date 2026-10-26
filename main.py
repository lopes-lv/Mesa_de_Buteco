"""
main.py - Ponto de entrada do jogo Texas Hold'em Solo vs Bots.

Janela redimensionável, sem imagens externas (tudo desenhado via pygame.draw,
estética "Neobrutalismo Suave / Dashboard Analítico" - ver ui_theme.py).
Execute com: python main.py
Compile com PyInstaller (ver README.md) para gerar o .exe no Windows.
Layout/cores vêm de config/layout.json (editor: python tools/editor_visual.py);
F5 recarrega, e o jogo recarrega sozinho quando o arquivo muda.
"""
import os
import sys
from typing import Any

import pygame

from holdem.game_logic import Table, Player, TIPO_BOT, TIPO_HUMANO_LOCAL, TIPO_HUMANO_REMOTO
from menus.screens import MenuScreen, ModeSelectScreen, ConfigScreen, SettingsScreen
from holdem.table_screen import TableScreen
from pifpaf.pifpaf_logic import (
    PifPafPlayer, PifPafTable, TIPO_BOT as PIFPAF_TIPO_BOT,
    TIPO_HUMANO_LOCAL as PIFPAF_TIPO_HUMANO_LOCAL, TIPO_HUMANO_REMOTO as PIFPAF_TIPO_HUMANO_REMOTO,
)
from pifpaf.pifpaf_screen import PifPafTableScreen
from domino.domino_logic import (
    DominoPlayer, DominoTable, TIPO_BOT as DOMINO_TIPO_BOT,
    TIPO_HUMANO_LOCAL as DOMINO_TIPO_HUMANO_LOCAL, TIPO_HUMANO_REMOTO as DOMINO_TIPO_HUMANO_REMOTO,
)
from domino.domino_screen import DominoTableScreen
from core.settings import Settings
from menus.multiplayer_screens import CriarSalaScreen, EntrarSalaScreen, LobbyScreen, MAX_JOGADORES_POR_JOGO
from core import carteira, layout, ui_theme
from core.tela import Tela

LARGURA_INICIAL, ALTURA_INICIAL = 1280, 800
FPS = 60

# Recarga do layout sem reiniciar: F5 força; e a cada INTERVALO_VIGIA_LAYOUT
# segundos o jogo confere se config/layout.json mudou (ex.: o editor visual
# salvou com o jogo aberto) e recarrega sozinho.
INTERVALO_VIGIA_LAYOUT = 1.0
DURACAO_AVISO_LAYOUT = 2.5

NOMES_BOTS = ["Bot Ana", "Bot Bruno", "Bot Caio", "Bot Duda", "Bot Elis", "Bot Fabio", "Bot Gabi", "Bot Hugo"]


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Texas Hold'em Solo")
        self.tela = pygame.display.set_mode((LARGURA_INICIAL, ALTURA_INICIAL), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.rodando = True

        self.jogo_finalizado = False
        self.nome_vencedor = None
        self.settings = Settings()

        self._marca_layout = self._marca_arquivo_layout()
        self._tempo_vigia_layout = 0.0
        self._aviso_layout = None  # (texto, segundos restantes)

        self.tela_atual: Tela = MenuScreen(self)

    # ---------------- Recarga do layout (config/layout.json) ----------------
    @staticmethod
    def _marca_arquivo_layout():
        """Identifica a versão do layout.json no disco (None se não existir)."""
        try:
            estado = os.stat(layout.caminho_usuario())
        except OSError:
            return None
        return (estado.st_mtime_ns, estado.st_size)

    def recarregar_layout(self, motivo):
        """Relê config/layout.json e aplica na hora: tamanhos e botões já são
        lidos a cada quadro, cores/fonte/borda via ui_theme.aplicar_tema().
        As fichas iniciais só acompanham se o jogador não mexeu nelas."""
        fichas_antes = layout.obter("geral.fichas_iniciais")
        layout.recarregar()
        ui_theme.aplicar_tema()
        if self.settings.fichas_iniciais == fichas_antes:
            self.settings.fichas_iniciais = layout.obter("geral.fichas_iniciais")
        self._marca_layout = self._marca_arquivo_layout()
        self._aviso_layout = (f"Layout recarregado ({motivo})", DURACAO_AVISO_LAYOUT)

    def _vigiar_layout(self, dt):
        self._tempo_vigia_layout += dt
        if self._tempo_vigia_layout < INTERVALO_VIGIA_LAYOUT:
            return
        self._tempo_vigia_layout = 0.0
        if self._marca_arquivo_layout() != self._marca_layout:
            self.recarregar_layout("arquivo alterado")

    def _desenhar_aviso_layout(self, dt):
        if self._aviso_layout is None:
            return
        texto, restante = self._aviso_layout
        _, altura = self.tela.get_size()
        ui_theme.desenhar_badge(self.tela, 16, altura - 16, texto, ui_theme.PANEL, cor_texto=ui_theme.INK,
                                tamanho_fonte=12, ancorar="bottomleft", borda=ui_theme.MINT)
        restante -= dt
        self._aviso_layout = (texto, restante) if restante > 0 else None

    # ---------------- Navegação entre telas ----------------
    def ir_para_menu(self):
        self.jogo_finalizado = False
        self.tela_atual = MenuScreen(self)

    def ir_para_escolha_modo(self):
        self.tela_atual = ModeSelectScreen(self)

    def ir_para_config(self, modo="holdem"):
        self.tela_atual = ConfigScreen(self, modo)

    def ir_para_ajustes(self):
        self.tela_atual = SettingsScreen(self)

    def ir_para_multiplayer_criar(self, jogo="holdem"):
        self.tela_atual = CriarSalaScreen(self, jogo)

    def ir_para_multiplayer_entrar(self):
        self.tela_atual = EntrarSalaScreen(self)

    def ir_para_lobby_host(self, sala_rede, jogo="holdem"):
        self.tela_atual = LobbyScreen(self, sala_rede=sala_rede, jogo=jogo)

    def ir_para_lobby_cliente(self, sala_cliente):
        self.tela_atual = LobbyScreen(self, sala_cliente=sala_cliente)

    def registrar_carteira(self, saldo):
        """Chamado pela mesa de Hold'em solo; a mesa do editor (App falso)
        não tem este método e por isso nunca mexe na carteira real."""
        carteira.registrar(saldo)

    def encerrar(self):
        self.rodando = False

    def alternar_tela_cheia(self):
        self.settings.tela_cheia = not self.settings.tela_cheia
        if self.settings.tela_cheia:
            self._tamanho_janela = self.tela.get_size()
            self.tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            tamanho = getattr(self, "_tamanho_janela", (LARGURA_INICIAL, ALTURA_INICIAL))
            self.tela = pygame.display.set_mode(tamanho, pygame.RESIZABLE)
        # descarta VIDEORESIZE/eventos de janela gerados pela própria troca
        pygame.event.clear(pygame.VIDEORESIZE)

    def iniciar_partida(self, quantidade_bots):
        stack_inicial = self.settings.fichas_iniciais
        # Hold'em solo: você entra com a carteira (saldo guardado entre sessões).
        # (o App falso do editor visual não tem registrar_carteira: usa o padrão)
        if hasattr(self, "registrar_carteira"):
            saldo = carteira.saldo()
            if saldo <= 0:
                return  # carteira zerada, esperando a reposição (a ConfigScreen avisa)
        else:
            saldo = stack_inicial
        jogadores = [Player(id_jogador=0, nome="Você", stack=saldo, tipo=TIPO_HUMANO_LOCAL)]
        for i in range(quantidade_bots):
            nome = NOMES_BOTS[i % len(NOMES_BOTS)]
            jogadores.append(Player(id_jogador=i + 1, nome=nome, stack=stack_inicial, tipo=TIPO_BOT))

        table = Table(jogadores)
        self.jogo_finalizado = False
        self.tela_atual = TableScreen(self, table)

    def iniciar_partida_multiplayer_host(self, sala_rede, nomes_participantes, completar_com_bots, jogo="holdem"):
        """
        `nomes_participantes` é a lista de dicts do lobby (id, nome,
        anfitriao) já com o host na posição 0. Vagas restantes viram bots
        (reaproveitando NOMES_BOTS) se `completar_com_bots` for True.
        `jogo` decide qual motor/tela sobe ("holdem", "pifpaf" ou "domino").
        """
        stack_inicial = self.settings.fichas_iniciais

        ClassePlayer: type[Player] | type[PifPafPlayer] | type[DominoPlayer]
        if jogo == "pifpaf":
            ClassePlayer, TIPO_LOCAL, TIPO_REMOTO, TIPO_BOT_ = (
                PifPafPlayer, PIFPAF_TIPO_HUMANO_LOCAL, PIFPAF_TIPO_HUMANO_REMOTO, PIFPAF_TIPO_BOT)
        elif jogo == "domino":
            ClassePlayer, TIPO_LOCAL, TIPO_REMOTO, TIPO_BOT_ = (
                DominoPlayer, DOMINO_TIPO_HUMANO_LOCAL, DOMINO_TIPO_HUMANO_REMOTO, DOMINO_TIPO_BOT)
        else:
            ClassePlayer, TIPO_LOCAL, TIPO_REMOTO, TIPO_BOT_ = (
                Player, TIPO_HUMANO_LOCAL, TIPO_HUMANO_REMOTO, TIPO_BOT)

        kwargs_fichas = {} if jogo == "pifpaf" else {"stack": stack_inicial}  # Pif Paf não usa fichas
        jogadores: list[Any] = []
        for participante in nomes_participantes:
            tipo = TIPO_LOCAL if participante["id"] == 0 else TIPO_REMOTO
            jogadores.append(ClassePlayer(id_jogador=participante["id"], nome=participante["nome"],
                                           tipo=tipo, **kwargs_fichas))

        if completar_com_bots:
            ids_usados = {j.id for j in jogadores}
            proximo_id = max(ids_usados) + 1
            vagas = max(0, MAX_JOGADORES_POR_JOGO.get(jogo, 8) - len(jogadores))
            for i in range(vagas):
                nome = NOMES_BOTS[i % len(NOMES_BOTS)]
                jogadores.append(ClassePlayer(id_jogador=proximo_id + i, nome=nome,
                                               tipo=TIPO_BOT_, **kwargs_fichas))

        self.jogo_finalizado = False
        sala_rede.em_jogo = True
        # Manda "iniciar_partida" ANTES de criar a tela de mesa: ela já
        # transmite o primeiro "estado"/"sua_mao" no construtor, e
        # LobbyScreen (do lado do cliente) descarta qualquer mensagem que
        # não seja "iniciar_partida" enquanto espera - se a ordem fosse
        # invertida, o snapshot inicial da mão se perderia.
        sala_rede.enviar_para_todos({"tipo": "iniciar_partida", "jogo": jogo})

        if jogo == "pifpaf":
            mesa_pifpaf = PifPafTable(jogadores, usar_joker=self.settings.usar_joker_pifpaf)
            self.tela_atual = PifPafTableScreen(self, mesa_pifpaf, sala_rede=sala_rede)
        elif jogo == "domino":
            mesa_domino = DominoTable(jogadores)
            self.tela_atual = DominoTableScreen(self, mesa_domino, sala_rede=sala_rede)
        else:
            table = Table(jogadores)
            self.tela_atual = TableScreen(self, table, sala_rede=sala_rede)

    def iniciar_partida_multiplayer_cliente(self, sala_cliente, jogo="holdem"):
        self.jogo_finalizado = False
        if jogo == "pifpaf":
            from pifpaf.mesa_remota_pifpaf_screen import MesaRemotaPifPafScreen
            self.tela_atual = MesaRemotaPifPafScreen(self, sala_cliente)
        elif jogo == "domino":
            from domino.mesa_remota_domino_screen import MesaRemotaDominoScreen
            self.tela_atual = MesaRemotaDominoScreen(self, sala_cliente)
        else:
            from holdem.mesa_remota_screen import MesaRemotaScreen
            self.tela_atual = MesaRemotaScreen(self, sala_cliente)

    def iniciar_partida_pifpaf(self, quantidade_bots):
        jogadores = [PifPafPlayer(id_jogador=0, nome="Você", tipo=PIFPAF_TIPO_HUMANO_LOCAL)]
        for i in range(quantidade_bots):
            nome = NOMES_BOTS[i % len(NOMES_BOTS)]
            jogadores.append(PifPafPlayer(id_jogador=i + 1, nome=nome, tipo=PIFPAF_TIPO_BOT))

        mesa = PifPafTable(jogadores, usar_joker=self.settings.usar_joker_pifpaf)
        self.jogo_finalizado = False
        self.tela_atual = PifPafTableScreen(self, mesa)

    def iniciar_partida_domino(self, quantidade_bots):
        stack_inicial = self.settings.fichas_iniciais
        jogadores = [DominoPlayer(id_jogador=0, nome="Você", stack=stack_inicial, tipo=DOMINO_TIPO_HUMANO_LOCAL)]
        for i in range(quantidade_bots):
            nome = NOMES_BOTS[i % len(NOMES_BOTS)]
            jogadores.append(DominoPlayer(id_jogador=i + 1, nome=nome, stack=stack_inicial, tipo=DOMINO_TIPO_BOT))

        mesa = DominoTable(jogadores)
        self.jogo_finalizado = False
        self.tela_atual = DominoTableScreen(self, mesa)

    def finalizar_jogo(self, nome_vencedor):
        self.jogo_finalizado = True
        self.nome_vencedor = nome_vencedor

    # ---------------- Loop principal ----------------
    def executar(self):
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000.0
            self._processar_eventos()
            self._vigiar_layout(dt)
            self.tela_atual.atualizar(dt)
            ui_theme.set_estilo_baralho(self.settings.baralho_skin)
            self.tela_atual.desenhar(self.tela)
            self._desenhar_aviso_layout(dt)
            ui_theme.aplicar_scanlines(self.tela)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                salvar = getattr(self.tela_atual, "salvar_carteira", None)
                if salvar:
                    salvar()  # fechar a janela no meio da mão não livra da aposta
                self.rodando = False
            elif evento.type == pygame.VIDEORESIZE:
                # No pygame 2 a surface da janela já é redimensionada sozinha;
                # chamar set_mode aqui (principalmente logo após alternar a tela
                # cheia) derrubava o modo fullscreen e desincronizava o botão.
                self.tela = pygame.display.get_surface() or self.tela
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_F5:
                self.recarregar_layout("F5")
            else:
                self.tela_atual.tratar_evento(evento)


if __name__ == "__main__":
    App().executar()
