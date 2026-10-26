"""EL-* — sistema de layout (core/layout.py, config/, tools/editor_previas.py;
tools/README.md). Tudo em pasta temporária: nunca grava em config/ de verdade."""
import json

import pytest

from core import layout, ui_theme


@pytest.fixture
def arquivo_usuario(tmp_path, monkeypatch):
    """layout.json do usuário numa pasta temporária; recarrega ao entrar e ao sair."""
    caminho = tmp_path / "config" / "layout.json"
    monkeypatch.setattr(layout, "caminho_usuario", lambda: str(caminho))
    layout.carregar()
    yield caminho
    monkeypatch.undo()
    layout.carregar()
    ui_theme.aplicar_tema()


def _chave_numerica_com_faixa():
    for chave in layout.chaves():
        meta = layout.metadados(chave)
        if isinstance(meta["valor"], int) and "min" in meta and "max" in meta:
            return chave, meta["min"], meta["max"]
    raise AssertionError("nenhum item numérico com min/max")


def test_el_01_todo_item_do_padrao_esta_dentro_da_propria_faixa():
    assert len(layout.chaves()) >= 50
    for chave in layout.chaves():
        meta = layout.metadados(chave)
        valor, minimo, maximo = meta["valor"], meta.get("min"), meta.get("max")
        assert valor is not None, chave
        itens = list(zip(valor, minimo, maximo, strict=True)) if isinstance(valor, list) else [(valor, minimo, maximo)]
        for v, lo, hi in itens:
            if lo is not None:
                assert v >= lo, f"{chave}: {v} < min {lo}"
            if hi is not None:
                assert v <= hi, f"{chave}: {v} > max {hi}"


def test_el_02_toda_chave_tem_previa_no_editor_e_vice_versa():
    from tools.editor_previas import PREVIAS
    assert set(PREVIAS) == set(layout.chaves())


def test_el_03_cada_preset_do_jogo_so_usa_chaves_validas_e_valores_aceitos(arquivo_usuario):
    presets = [p for p in layout.listar_presets() if p[1] == "padrao"]
    assert {p[0] for p in presets} >= {"compacto", "grande"}
    chaves = set(layout.chaves())
    for nome, _, _ in presets:
        caminho = f"{layout.pasta_presets_padrao()}/{nome}.json"
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        pedidos = {f"{g}.{n}": v for g, itens in dados.items() if not g.startswith("_")
                   for n, v in itens.items()}
        assert pedidos, nome
        assert set(pedidos) <= chaves, f"{nome}: chaves desconhecidas {set(pedidos) - chaves}"
        assert layout.carregar_preset(nome)
        for chave, pedido in pedidos.items():
            esperado = tuple(pedido) if isinstance(pedido, list) else pedido
            assert layout.obter(chave) == esperado, f"{nome}: {chave} foi ajustado pelo limite (fora da faixa)"
        layout.restaurar_padrao()


def test_el_03_preset_inexistente_devolve_false(arquivo_usuario):
    assert layout.carregar_preset("nao_existe_mesmo") is False


@pytest.mark.parametrize("conteudo", [
    "isto não é json",
    "[1, 2, 3]",
    '{"holdem": "texto"}',
    '{"holdem": {"carta_jogador": "grande"}}',
    '{"holdem": {"carta_jogador": [1]}}',
    '{"inventado": {"x": 1}}',
])
def test_el_04_arquivo_do_usuario_estragado_cai_no_padrao_sem_excecao(arquivo_usuario, conteudo):
    arquivo_usuario.parent.mkdir(parents=True)
    arquivo_usuario.write_text(conteudo, encoding="utf-8")
    layout.carregar()
    for chave in layout.chaves():
        assert layout.obter(chave) == layout.padrao(chave)


def test_el_04_arquivo_ausente_usa_o_padrao(arquivo_usuario):
    assert not arquivo_usuario.exists()
    assert layout.ajustes_atuais() == {}


def test_el_05_valor_fora_da_faixa_e_limitado(arquivo_usuario):
    chave, minimo, maximo = _chave_numerica_com_faixa()
    grupo, nome = chave.split(".")
    arquivo_usuario.parent.mkdir(parents=True)
    arquivo_usuario.write_text(json.dumps({grupo: {nome: maximo + 1000}}), encoding="utf-8")
    layout.carregar()
    assert layout.obter(chave) == maximo
    arquivo_usuario.write_text(json.dumps({grupo: {nome: minimo - 1000}}), encoding="utf-8")
    layout.carregar()
    assert layout.obter(chave) == minimo


def test_el_05_definir_tambem_limita(arquivo_usuario):
    chave, _, maximo = _chave_numerica_com_faixa()
    assert layout.definir(chave, maximo + 5000) == maximo


def test_el_05_definir_com_formato_errado_levanta_erro(arquivo_usuario):
    chave, _, _ = _chave_numerica_com_faixa()
    with pytest.raises(ValueError):
        layout.definir(chave, "abc")


def test_el_06_salvar_grava_so_o_que_mudou_e_recarregar_le_de_volta(arquivo_usuario):
    chave, minimo, maximo = _chave_numerica_com_faixa()
    novo = layout.padrao(chave) + layout.metadados(chave).get("passo", 1)
    novo = min(novo, maximo) if novo != layout.padrao(chave) else minimo
    layout.definir(chave, novo)
    layout.salvar()
    grupo, nome = chave.split(".")
    assert json.loads(arquivo_usuario.read_text(encoding="utf-8")) == {grupo: {nome: novo}}
    layout.restaurar_padrao()
    layout.recarregar()
    assert layout.obter(chave) == novo


def test_el_06_preset_do_usuario_e_gravado_e_listado(arquivo_usuario):
    chave, _, maximo = _chave_numerica_com_faixa()
    layout.definir(chave, maximo)
    assert layout.salvar_preset("meu teste") is not None
    nomes = [(n, origem) for n, origem, _ in layout.listar_presets()]
    assert ("meu teste", "usuario") in nomes
    assert layout.salvar_preset("///") is None            # nome sem nada aproveitável


def test_el_07_chave_inexistente_levanta_keyerror():
    with pytest.raises(KeyError):
        layout.obter("holdem.isto_nao_existe")


def test_el_08_aplicar_tema_muda_a_cor_no_lugar_sem_trocar_o_objeto():
    objeto = ui_theme.YELLOW
    original = tuple(objeto)
    try:
        ui_theme.aplicar_tema(lambda chave: (1, 2, 3) if chave == "cores.amarelo" else layout.obter(chave))
        assert ui_theme.YELLOW is objeto
        assert tuple(objeto)[:3] == (1, 2, 3)
    finally:
        ui_theme.aplicar_tema()
    assert tuple(objeto) == original


def test_el_09_as_cores_do_tema_sao_color_mutaveis():
    import pygame
    for nome in ("BG", "PANEL", "YELLOW", "INK", "MINT"):
        assert isinstance(getattr(ui_theme, nome), pygame.Color)
