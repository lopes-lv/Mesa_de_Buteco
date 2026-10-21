"""ET-* — as telas desenham sem erro (render headless): menus, as três mesas do
host e as três mesas do cliente remoto, alimentadas pelo estado real que o host
serializa (passando por JSON, como na rede)."""
import json
import queue
import random

import pygame
import pytest

import main
from core import ui_theme
from core.settings import ORDEM_BARALHO_SKINS
from domino.domino_logic import DominoPlayer, DominoTable
from domino.domino_screen import DominoTableScreen
from domino.mesa_remota_domino_screen import MesaRemotaDominoScreen
from holdem.game_logic import TIPO_HUMANO_REMOTO, Player, Table
from holdem.mesa_remota_screen import MesaRemotaScreen
from holdem.table_screen import TableScreen
from pifpaf.mesa_remota_pifpaf_screen import MesaRemotaPifPafScreen
from pifpaf.pifpaf_logic import PifPafPlayer, PifPafTable
from pifpaf.pifpaf_screen import PifPafTableScreen
from rede import protocolo
from tests.test_host_validacao import SalaFalsa
from tools import editor_mesa

JANELAS = [(1280, 800), (1024, 768)]


@pytest.fixture(params=JANELAS, ids=lambda j: f"{j[0]}x{j[1]}")
def janela(request):
    return request.param


def superficie(tamanho):
    return pygame.Surface(tamanho)


# ---------------------------------------------------------------- Menus
def test_et_01_as_telas_de_menu_desenham(janela):
    app = main.App()
    app.tela = pygame.display.set_mode(janela)
    for ir in (app.ir_para_menu, app.ir_para_escolha_modo, app.ir_para_ajustes,
               lambda: app.ir_para_config("holdem"), lambda: app.ir_para_config("pifpaf"),
               lambda: app.ir_para_config("domino")):
        ir()
        app.tela_atual.atualizar(1 / 60)
        app.tela_atual.desenhar(app.tela)


# ---------------------------------------------------------------- Mesas do host
@pytest.mark.parametrize("modo", ["holdem", "pifpaf", "domino"])
def test_et_02_a_mesa_do_host_desenha_do_comeco_ao_fim_de_uma_mao(modo, janela):
    random.seed(5)
    alvo = superficie(janela)
    with editor_mesa._ambiente_de_desenho(alvo):
        tela = editor_mesa._nova_partida(modo, 4)
        desenhos = 0
        for passo in range(1500):
            tela.atualizar(editor_mesa.PASSO_SIMULACAO)
            if passo % 60 == 0 or editor_mesa._mao_terminou(tela):
                tela.desenhar(alvo)
                desenhos += 1
            if editor_mesa._mao_terminou(tela):
                break
    assert desenhos >= 3


# ---------------------------------------------------------------- Cliente remoto
class ClienteFalso:
    """O mínimo de rede.cliente.ClienteSala que as telas remotas usam."""

    def __init__(self, meu_id):
        self.meu_id = meu_id
        self.status = "conectado"
        self.erro = None
        self.mensagens_entrantes = queue.Queue()
        self.enviadas = []

    def enviar(self, mensagem):
        self.enviadas.append(mensagem)

    def fechar(self):
        self.status = "desconectado"


def _estado_para_o_cliente(tela_host, id_cliente):
    """Mensagens que o host mandaria ao cliente, depois de passar por JSON."""
    tela_host.sala_rede.enviados.clear()
    tela_host._broadcast_estado()
    mensagens = [m for destino, m in tela_host.sala_rede.enviados if destino in (None, id_cliente)]
    assert any(m["tipo"] == protocolo.ESTADO for m in mensagens)
    return [json.loads(json.dumps(m)) for m in mensagens]


def _montar(modo):
    sala = SalaFalsa()
    app = editor_mesa.AppFalso()
    if modo == "holdem":
        jogadores = [Player(i, f"J{i}", stack=1500) for i in range(4)]
        jogadores[1].tipo = TIPO_HUMANO_REMOTO
        host = TableScreen(app, Table(jogadores), sala_rede=sala)
        remota = MesaRemotaScreen
    elif modo == "pifpaf":
        jogadores = [PifPafPlayer(i, f"J{i}") for i in range(4)]
        jogadores[1].tipo = TIPO_HUMANO_REMOTO
        host = PifPafTableScreen(app, PifPafTable(jogadores), sala_rede=sala)
        remota = MesaRemotaPifPafScreen
    else:
        jogadores = [DominoPlayer(i, f"J{i}") for i in range(4)]
        jogadores[1].tipo = TIPO_HUMANO_REMOTO
        host = DominoTableScreen(app, DominoTable(jogadores), sala_rede=sala)
        remota = MesaRemotaDominoScreen
    return app, host, remota


@pytest.mark.parametrize("modo", ["holdem", "pifpaf", "domino"])
def test_et_03_a_mesa_remota_desenha_a_partir_do_estado_do_host(modo, janela):
    random.seed(9)
    app, host, classe_remota = _montar(modo)
    cliente = ClienteFalso(meu_id=1)
    remota = classe_remota(app, cliente)
    alvo = superficie(janela)
    with editor_mesa._ambiente_de_desenho(alvo):
        for passo in range(400):
            host.atualizar(editor_mesa.PASSO_SIMULACAO)
            if passo % 40 == 0:
                for mensagem in _estado_para_o_cliente(host, 1):
                    cliente.mensagens_entrantes.put(mensagem)
                remota.atualizar(editor_mesa.PASSO_SIMULACAO)
                remota.desenhar(alvo)
    assert remota.estado is not None
    assert remota.mensagem_final is None


# ---------------------------------------------------------------- Sala de espera (multiplayer)
class AnfitriaoFalso(SalaFalsa):
    codigo = "ABCD"
    ip_local = "192.168.0.10"
    porta_tcp = 53000

    def lista_jogadores_lobby(self):
        return [{"id": 0, "nome": "Host", "anfitriao": True}, {"id": 1, "nome": "Ana", "anfitriao": False}]


@pytest.mark.xfail(reason="BUG: LobbyScreen.desenhar (menus/multiplayer_screens.py:324) usa SOMBRA, que "
                          "não está importado: NameError ao desenhar a sala de espera do anfitrião, "
                          "então nenhum host consegue abrir uma sala multiplayer. Achado pelo ruff (F821).")
@pytest.mark.parametrize("jogo", ["holdem", "pifpaf", "domino"])
def test_et_06_a_sala_de_espera_do_anfitriao_desenha(jogo, janela):
    from menus.multiplayer_screens import LobbyScreen
    tela = LobbyScreen(editor_mesa.AppFalso(), sala_rede=AnfitriaoFalso(), jogo=jogo)
    tela.atualizar(1 / 60)
    tela.desenhar(superficie(janela))


def test_et_06_a_sala_de_espera_do_cliente_desenha(janela):
    from menus.multiplayer_screens import LobbyScreen
    cliente = ClienteFalso(meu_id=1)
    cliente.jogadores_lobby = [{"id": 0, "nome": "Host", "anfitriao": True}, {"id": 1, "nome": "Ana", "anfitriao": False}]
    tela = LobbyScreen(editor_mesa.AppFalso(), sala_cliente=cliente)
    tela.atualizar(1 / 60)
    tela.desenhar(superficie(janela))


# ---------------------------------------------------------------- Baralhos
@pytest.mark.parametrize("skin", ORDEM_BARALHO_SKINS)
def test_et_04_todo_baralho_desenha_carta_verso_e_slot_vazio(skin):
    from core.deck import Card
    alvo = superficie((300, 220))
    ui_theme.set_estilo_baralho(skin)
    try:
        for carta in (Card(14, "espadas"), Card(10, "copas"), Card(7, "ouros"), Card(12, "paus")):
            ui_theme.desenhar_carta(alvo, 10, 10, 90, 126, carta)
        ui_theme.desenhar_carta(alvo, 110, 10, 90, 126, None, virada=False) \
            if False else None
        ui_theme.desenhar_carta_vazia(alvo, 210, 10, 80, 112)
    finally:
        ui_theme.set_estilo_baralho("padrao")


# ---------------------------------------------------------------- Detector de sobreposição (lento)
@pytest.mark.lento
@pytest.mark.parametrize("modo", ["holdem", "pifpaf", "domino"])
def test_et_05_o_detector_do_editor_nao_acusa_erro_em_nenhuma_combinacao(modo):
    """Invariante do CLAUDE.md: zero problemas em modo × jogadores × janela × cena."""
    minimo, maximo = editor_mesa.JOGADORES[modo]
    problemas = []
    for n_jogadores in range(minimo, maximo + 1):
        for indice_cena in range(len(editor_mesa.CENAS[modo])):
            for tamanho in editor_mesa.RESOLUCOES:
                alvo = superficie(tamanho)
                tela = editor_mesa.simular_cena(modo, n_jogadores, indice_cena, alvo)
                assert tela is not None, f"{modo} {n_jogadores}j: nenhuma semente chegou à cena {indice_cena}"
                elementos = editor_mesa.desenhar_mesa(tela, modo, alvo)
                for alerta in editor_mesa.calcular_alertas(elementos, tamanho):
                    if alerta.nivel == "erro":
                        problemas.append(f"{modo} {n_jogadores}j {tamanho} cena {indice_cena}: {alerta.mensagem}")
    assert not problemas, "\n".join(problemas)
