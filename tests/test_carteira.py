"""CA-* — carteira persistente do Hold'em solo (holdem/README.md, "Fichas e
carteira"). Nunca toca em config/carteira.json: o caminho e o relógio são trocados."""
import json

import pytest

from core import carteira


class Relogio:
    def __init__(self, agora=1_000_000.0):
        self.agora = agora

    def time(self):
        return self.agora


@pytest.fixture
def arquivo(tmp_path, monkeypatch):
    caminho = tmp_path / "config" / "carteira.json"
    monkeypatch.setattr(carteira, "caminho", lambda: str(caminho))
    return caminho


@pytest.fixture
def relogio(monkeypatch):
    r = Relogio()
    monkeypatch.setattr(carteira, "time", r)
    return r


def test_ca_01_sem_arquivo_comeca_com_o_saldo_inicial(arquivo, relogio):
    assert not arquivo.exists()
    assert carteira.saldo() == carteira.SALDO_INICIAL == 2000


@pytest.mark.parametrize("conteudo", [
    "isto não é json",
    "[]",
    '{"saldo": "muito"}',
    '{"saldo": true}',
    "{}",
])
def test_ca_02_arquivo_corrompido_vira_carteira_nova(arquivo, relogio, conteudo):
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text(conteudo, encoding="utf-8")
    assert carteira.saldo() == carteira.SALDO_INICIAL


def test_ca_03_registrar_e_ler_devolve_o_mesmo_saldo(arquivo, relogio):
    carteira.registrar(3450)
    assert carteira.saldo() == 3450
    assert json.loads(arquivo.read_text(encoding="utf-8"))["saldo"] == 3450


def test_ca_03_saldo_negativo_e_tratado_como_zero(arquivo, relogio):
    carteira.registrar(-50)
    assert json.loads(arquivo.read_text(encoding="utf-8"))["saldo"] == 0


def test_ca_04_saldo_zerado_bloqueia_por_doze_horas_e_depois_repoe(arquivo, relogio):
    carteira.registrar(0)
    assert carteira.saldo() == 0
    assert carteira.segundos_para_reposicao() == carteira.ESPERA_REPOSICAO_S

    relogio.agora += carteira.ESPERA_REPOSICAO_S - 60
    assert carteira.saldo() == 0
    assert carteira.segundos_para_reposicao() == 60

    relogio.agora += 60
    assert carteira.saldo() == carteira.SALDO_INICIAL
    assert carteira.segundos_para_reposicao() is None


def test_ca_04_com_saldo_positivo_nao_ha_espera(arquivo, relogio):
    carteira.registrar(10)
    assert carteira.segundos_para_reposicao() is None


def test_ca_04_registrar_zero_de_novo_nao_reinicia_a_espera(arquivo, relogio):
    carteira.registrar(0)
    relogio.agora += 3600
    carteira.registrar(0)
    assert carteira.segundos_para_reposicao() == carteira.ESPERA_REPOSICAO_S - 3600


def test_ca_05_zerou_em_invalido_e_ignorado(arquivo, relogio):
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text('{"saldo": 0, "zerou_em": "ontem"}', encoding="utf-8")
    assert carteira.saldo() == 0                       # a espera recomeça agora
    assert carteira.segundos_para_reposicao() == carteira.ESPERA_REPOSICAO_S


def test_ca_05_relogio_voltando_no_tempo_repoe_em_vez_de_travar(arquivo, relogio):
    carteira.registrar(0)
    relogio.agora -= 10 * 3600
    assert carteira.saldo() == carteira.SALDO_INICIAL


def test_ca_06_formatar_espera():
    assert carteira.formatar_espera(12 * 3600) == "12h00min"
    assert carteira.formatar_espera(3600 + 5 * 60) == "1h05min"
