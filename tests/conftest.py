"""Configuração comum dos testes: SDL sem tela, caminhos e semente fixa."""
import os
import random
import sys

# Antes de qualquer import do pygame: sem janela e sem áudio.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def semente_fixa():
    """Toda aleatoriedade dos motores parte de uma semente conhecida."""
    random.seed(20261021)


@pytest.fixture(scope="session", autouse=True)
def layout_do_projeto_sem_ajustes_do_usuario(tmp_path_factory):
    """Os testes enxergam só o config/layout_padrao.json: o config/layout.json do
    jogador (que existe na máquina de quem desenvolve) nunca influencia o resultado
    nem é tocado."""
    from core import layout, ui_theme
    pasta = tmp_path_factory.mktemp("sem_ajustes")
    patch = pytest.MonkeyPatch()
    patch.setattr(layout, "caminho_usuario", lambda: str(pasta / "config" / "layout.json"))
    layout.carregar()
    ui_theme.aplicar_tema()
    yield
    patch.undo()
    layout.carregar()
    ui_theme.aplicar_tema()


@pytest.fixture(scope="session", autouse=True)
def carteira_fora_do_config_real(tmp_path_factory):
    """A carteira do Hold'em solo grava em disco; nos testes ela vive numa pasta temporária."""
    from core import carteira
    pasta = tmp_path_factory.mktemp("carteira")
    patch = pytest.MonkeyPatch()
    patch.setattr(carteira, "caminho", lambda: str(pasta / "carteira.json"))
    yield
    patch.undo()


@pytest.fixture(scope="session", autouse=True)
def pygame_iniciado():
    """pygame inicializado uma vez, com vídeo e áudio "dummy" (sem janela, sem som)."""
    import pygame
    pygame.init()
    pygame.display.set_mode((1280, 800))
    yield
    pygame.quit()
