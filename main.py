"""
main.py - Ponto de entrada do jogo Texas Hold'em Solo vs Bots.

Janela redimensionável, sem imagens externas (tudo desenhado via pygame.draw,
estética "Neobrutalismo Suave / Dashboard Analítico" - ver ui_theme.py).
Execute com: python main.py
Compile com PyInstaller (ver README.md) para gerar o .exe no Windows.
"""
import sys
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
from core import ui_theme

LARGURA_INICIAL, ALTURA_INICIAL = 1280, 800
FPS = 60

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

        self.tela_atual = MenuScreen(self)

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

    def encerrar(self):
        self.rodando = False

    def alternar_tela_cheia(self):
        self.settings.tela_cheia = not self.settings.tela_cheia
        if self.settings.tela_cheia:
            self.tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.tela = pygame.display.set_mode((LARGURA_INICIAL, ALTURA_INICIAL), pygame.RESIZABLE)

    def iniciar_partida(self, quantidade_bots):
        stack_inicial = self.settings.fichas_iniciais
        jogadores = [Player(id_jogador=0, nome="Você", stack=stack_inicial, tipo=TIPO_HUMANO_LOCAL)]
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

        if jogo == "pifpaf":
            ClassePlayer, TIPO_LOCAL, TIPO_REMOTO, TIPO_BOT_ = (
                PifPafPlayer, PIFPAF_TIPO_HUMANO_LOCAL, PIFPAF_TIPO_HUMANO_REMOTO, PIFPAF_TIPO_BOT)
        elif jogo == "domino":
            ClassePlayer, TIPO_LOCAL, TIPO_REMOTO, TIPO_BOT_ = (
                DominoPlayer, DOMINO_TIPO_HUMANO_LOCAL, DOMINO_TIPO_HUMANO_REMOTO, DOMINO_TIPO_BOT)
        else:
            ClassePlayer, TIPO_LOCAL, TIPO_REMOTO, TIPO_BOT_ = (
                Player, TIPO_HUMANO_LOCAL, TIPO_HUMANO_REMOTO, TIPO_BOT)

        jogadores = []
        for participante in nomes_participantes:
            tipo = TIPO_LOCAL if participante["id"] == 0 else TIPO_REMOTO
            jogadores.append(ClassePlayer(id_jogador=participante["id"], nome=participante["nome"],
                                           stack=stack_inicial, tipo=tipo))

        if completar_com_bots:
            ids_usados = {j.id for j in jogadores}
            proximo_id = max(ids_usados) + 1
            vagas = max(0, MAX_JOGADORES_POR_JOGO.get(jogo, 8) - len(jogadores))
            for i in range(vagas):
                nome = NOMES_BOTS[i % len(NOMES_BOTS)]
                jogadores.append(ClassePlayer(id_jogador=proximo_id + i, nome=nome,
                                               stack=stack_inicial, tipo=TIPO_BOT_))

        self.jogo_finalizado = False
        sala_rede.em_jogo = True
        # Manda "iniciar_partida" ANTES de criar a tela de mesa: ela já
        # transmite o primeiro "estado"/"sua_mao" no construtor, e
        # LobbyScreen (do lado do cliente) descarta qualquer mensagem que
        # não seja "iniciar_partida" enquanto espera - se a ordem fosse
        # invertida, o snapshot inicial da mão se perderia.
        sala_rede.enviar_para_todos({"tipo": "iniciar_partida", "jogo": jogo})

        if jogo == "pifpaf":
            mesa = PifPafTable(jogadores, usar_joker=self.settings.usar_joker_pifpaf)
            self.tela_atual = PifPafTableScreen(self, mesa, sala_rede=sala_rede)
        elif jogo == "domino":
            mesa = DominoTable(jogadores)
            self.tela_atual = DominoTableScreen(self, mesa, sala_rede=sala_rede)
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
        stack_inicial = self.settings.fichas_iniciais
        jogadores = [PifPafPlayer(id_jogador=0, nome="Você", stack=stack_inicial, tipo=PIFPAF_TIPO_HUMANO_LOCAL)]
        for i in range(quantidade_bots):
            nome = NOMES_BOTS[i % len(NOMES_BOTS)]
            jogadores.append(PifPafPlayer(id_jogador=i + 1, nome=nome, stack=stack_inicial, tipo=PIFPAF_TIPO_BOT))

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
            self.tela_atual.atualizar(dt)
            ui_theme.set_estilo_baralho(self.settings.baralho_skin)
            self.tela_atual.desenhar(self.tela)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type == pygame.VIDEORESIZE:
                self.tela = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.rodando = False
            else:
                self.tela_atual.tratar_evento(evento)


if __name__ == "__main__":
    App().executar()
