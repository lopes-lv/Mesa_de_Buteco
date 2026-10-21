"""ER-* — protocolo de rede (rede/protocolo.py) e limites da sala."""
import json
import struct

import pytest

from menus.multiplayer_screens import MAX_JOGADORES_POR_JOGO
from rede.protocolo import (TAMANHO_MAXIMO_MENSAGEM, DecodificadorFrames, empacotar)


def test_er_01_ida_e_volta_preserva_acentos_e_emoji():
    mensagem = {"tipo": "chat", "texto": "olá, coração ♠ 🎲", "n": [1, 2, 3]}
    assert DecodificadorFrames().alimentar(empacotar(mensagem)) == [mensagem]


def test_er_02_mensagem_chegando_byte_a_byte_e_remontada():
    mensagem = {"tipo": "estado", "pote": 120}
    decodificador = DecodificadorFrames()
    saida = []
    for byte in empacotar(mensagem):
        saida += decodificador.alimentar(bytes([byte]))
    assert saida == [mensagem]


def test_er_03_duas_mensagens_coladas_saem_separadas():
    a, b = {"tipo": "a"}, {"tipo": "b", "x": 1}
    assert DecodificadorFrames().alimentar(empacotar(a) + empacotar(b)) == [a, b]


def test_er_03_mensagem_incompleta_fica_esperando():
    pacote = empacotar({"tipo": "a"})
    decodificador = DecodificadorFrames()
    assert decodificador.alimentar(pacote[:-1]) == []
    assert decodificador.alimentar(pacote[-1:]) == [{"tipo": "a"}]


def test_er_04_mensagem_maior_que_o_limite_e_recusada():
    cabecalho = struct.pack("!I", TAMANHO_MAXIMO_MENSAGEM + 1)
    with pytest.raises(ValueError):
        DecodificadorFrames().alimentar(cabecalho + b"x")


def test_er_05_json_invalido_levanta_erro_claro():
    corpo = b"{isto nao e json"
    with pytest.raises(ValueError):                       # JSONDecodeError é um ValueError
        DecodificadorFrames().alimentar(struct.pack("!I", len(corpo)) + corpo)


def test_er_05_o_cabecalho_declara_o_tamanho_em_bytes_do_corpo():
    pacote = empacotar({"texto": "ç"})
    tamanho = struct.unpack("!I", pacote[:4])[0]
    assert tamanho == len(pacote) - 4
    assert json.loads(pacote[4:].decode("utf-8")) == {"texto": "ç"}


def test_er_06_limite_de_jogadores_por_jogo():
    assert MAX_JOGADORES_POR_JOGO == {"holdem": 8, "pifpaf": 8, "domino": 4}
