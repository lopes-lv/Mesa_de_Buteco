"""
main.py - Ponto de entrada do jogo Pixel Poker (Texas Hold'em Solo vs Bots).

Janela redimensionável, sem imagens externas (tudo desenhado via pygame.draw).
Execute com: python main.py
Compile com PyInstaller (ver README.md) para gerar o .exe no Windows.
"""
import sys
import pygame

from game_logic import Table, Player
from screens import MenuScreen, ConfigScreen
from table_screen import TableScreen

LARGURA_INICIAL, ALTURA_INICIAL = 1280, 800
FPS = 60

NOMES_BOTS = ["Bot Ana", "Bot Bruno", "Bot Caio", "Bot Duda", "Bot Elis", "Bot Fabio"]


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pixel Poker - Texas Hold'em Solo")
        self.tela = pygame.display.set_mode((LARGURA_INICIAL, ALTURA_INICIAL), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.rodando = True

        self.jogo_finalizado = False
        self.nome_vencedor = None

        self.tela_atual = MenuScreen(self)

    # ---------------- Navegação entre telas ----------------
    def ir_para_menu(self):
        self.jogo_finalizado = False
        self.tela_atual = MenuScreen(self)

    def ir_para_config(self):
        self.tela_atual = ConfigScreen(self)

    def encerrar(self):
        self.rodando = False

    def iniciar_partida(self, quantidade_bots):
        jogadores = [Player(id_jogador=0, nome="Você", is_bot=False)]
        for i in range(quantidade_bots):
            nome = NOMES_BOTS[i % len(NOMES_BOTS)]
            jogadores.append(Player(id_jogador=i + 1, nome=nome, is_bot=True))

        table = Table(jogadores)
        self.jogo_finalizado = False
        self.tela_atual = TableScreen(self, table)

    def finalizar_jogo(self, nome_vencedor):
        self.jogo_finalizado = True
        self.nome_vencedor = nome_vencedor

    # ---------------- Loop principal ----------------
    def executar(self):
        while self.rodando:
            dt = self.clock.tick(FPS) / 1000.0
            self._processar_eventos()
            self.tela_atual.atualizar(dt)
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
