"""EM-* — a estrutura do projeto continua de pé: imports, ponto de entrada,
geometria compartilhada entre host e cliente remoto, arquivos do build."""
import importlib
import os
import pkgutil
import re

import pytest

from tests.conftest import RAIZ

PACOTES = ["core", "holdem", "pifpaf", "domino", "menus", "rede", "tools"]


def _modulos():
    nomes = ["main"]
    for pacote in PACOTES:
        modulo = importlib.import_module(pacote)
        nomes += [m.name for m in pkgutil.iter_modules(modulo.__path__, pacote + ".")]
    return nomes


@pytest.mark.parametrize("nome", _modulos())
def test_em_01_todo_modulo_importa_sem_erro(nome):
    importlib.import_module(nome)


def test_em_02_o_app_sobe_e_desenha_varios_quadros():
    import pygame
    import main
    app = main.App()
    for _ in range(30):
        app.tela_atual.atualizar(1 / 60)
        app.tela_atual.desenhar(app.tela)
        main.ui_theme.aplicar_scanlines(app.tela)
        pygame.display.flip()
    assert app.rodando


def test_em_02_o_app_navega_pelos_menus_sem_erro():
    import main
    app = main.App()
    navegacao = [app.ir_para_escolha_modo, app.ir_para_ajustes, app.ir_para_menu,
                 lambda: app.ir_para_config("holdem"), lambda: app.ir_para_config("pifpaf"),
                 lambda: app.ir_para_config("domino"), app.ir_para_multiplayer_entrar,
                 lambda: app.ir_para_multiplayer_criar("domino")]
    for ir in navegacao:
        ir()
        app.tela_atual.atualizar(1 / 60)
        app.tela_atual.desenhar(app.tela)


def test_em_03_cliente_remoto_reusa_a_geometria_do_host():
    from pifpaf import mesa_remota_pifpaf_screen as remota_pf, pifpaf_screen as host_pf
    from domino import mesa_remota_domino_screen as remota_dm, domino_screen as host_dm
    for nome in ("posicoes_assentos", "mesa_rect_para", "topo_da_mao", "posicao_selo_historico"):
        assert getattr(remota_pf, nome) is getattr(host_pf, nome), nome
    for nome in ("CENTRO_MESA_Y", "FOLGA_ASSENTO_CIMA", "FOLGA_ASSENTO_BAIXO", "MEIA_LARGURA_ASSENTO",
                 "posicionar_botao_passar"):
        assert getattr(remota_dm, nome) is getattr(host_dm, nome), nome


def test_em_04_o_spec_do_pyinstaller_aponta_para_arquivos_que_existem():
    with open(os.path.join(RAIZ, "PixelPoker.spec"), encoding="utf-8") as f:
        spec = f.read()
    origens = re.findall(r"\('([^']+)',\s*'[^']+'\)", spec)
    assert origens, "o .spec deveria embutir arquivos de dados"
    for origem in origens:
        if "*" in origem:
            pasta = os.path.dirname(os.path.join(RAIZ, origem))
            assert os.path.isdir(pasta) and any(f.endswith(".json") for f in os.listdir(pasta)), origem
        else:
            assert os.path.exists(os.path.join(RAIZ, origem)), origem
    assert any("layout_padrao.json" in o for o in origens)


def test_em_05_o_jogo_nao_importa_as_ferramentas_de_desenvolvimento():
    """tools/ não vai no .exe: nenhum módulo do jogo pode depender dele."""
    for pasta in ("core", "holdem", "pifpaf", "domino", "menus", "rede"):
        for nome in os.listdir(os.path.join(RAIZ, pasta)):
            if nome.endswith(".py"):
                with open(os.path.join(RAIZ, pasta, nome), encoding="utf-8") as f:
                    assert not re.search(r"^\s*(from|import)\s+tools\b", f.read(), re.M), f"{pasta}/{nome}"
    with open(os.path.join(RAIZ, "main.py"), encoding="utf-8") as f:
        assert not re.search(r"^\s*(from|import)\s+tools\b", f.read(), re.M)


def test_em_06_motores_dos_modos_nao_importam_um_ao_outro():
    for pacote, proibidos in {"holdem": ("pifpaf", "domino"), "pifpaf": ("holdem", "domino"),
                              "domino": ("holdem", "pifpaf")}.items():
        for nome in os.listdir(os.path.join(RAIZ, pacote)):
            if nome.endswith(".py"):
                with open(os.path.join(RAIZ, pacote, nome), encoding="utf-8") as f:
                    codigo = f.read()
                for outro in proibidos:
                    assert not re.search(rf"^\s*(from|import)\s+{outro}\b", codigo, re.M), f"{pacote}/{nome} → {outro}"
