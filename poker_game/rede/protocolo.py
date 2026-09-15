"""
rede/protocolo.py - Framing das mensagens TCP + constantes de tipo.

Cada mensagem e um JSON serializado, prefixado por 4 bytes (big-endian) com
o tamanho em bytes do JSON que vem a seguir. Isso evita o problema de "onde
termina uma mensagem e comeca a proxima" em um stream TCP, sem depender de o
JSON nunca conter certos caracteres.
"""
import json
import struct

PORTA_TCP_PADRAO = 53000
PORTA_UDP_DESCOBERTA = 52999
MAX_JOGADORES = 8

TAMANHO_CABECALHO = 4  # bytes (unsigned int big-endian)
TAMANHO_MAXIMO_MENSAGEM = 1024 * 1024  # 1 MiB, generoso para o snapshot de estado

# ---------------------------------------------------------------- Tipos
ENTRAR = "entrar"                 # cliente -> host: {nome}
ENTRADA_OK = "entrada_ok"         # host -> cliente: {seu_id, jogadores[]}
RECUSADO = "recusado"             # host -> cliente: {motivo}
LOBBY_ATUALIZADO = "lobby_atualizado"  # host -> todos: {jogadores[]}
INICIAR_PARTIDA = "iniciar_partida"    # host -> todos: {}
ESTADO = "estado"                 # host -> todos: snapshot publico da mesa
SUA_MAO = "sua_mao"               # host -> 1 cliente: {cartas: [...]}
ACAO = "acao"                     # cliente -> host: {acao, valor} (Hold'em: fold/check/call/raise)
ACAO_PIFPAF = "acao_pifpaf"       # cliente -> host: {acao, carta?} (comprar_monte/comprar_descarte/bater/bater_mao_fechada/descartar)
ACAO_DOMINO = "acao_domino"       # cliente -> host: {acao: "jogar", peca: [a,b], lado} - comprar/passar são automáticos, não vêm do cliente
ERRO_ACAO = "erro_acao"           # host -> 1 cliente: {motivo}
SAIR = "sair"                     # qualquer -> outro lado
SALA_ENCERRADA = "sala_encerrada"      # host -> todos: {motivo}
FIM_DE_JOGO = "fim_de_jogo"       # host -> todos: {vencedor}
CHAT = "chat"                     # cliente -> host: {texto} | host -> todos: {remetente, texto}


def empacotar(mensagem: dict) -> bytes:
    """Serializa um dict em JSON e prefixa com o tamanho (4 bytes big-endian)."""
    corpo = json.dumps(mensagem, ensure_ascii=False).encode("utf-8")
    cabecalho = struct.pack("!I", len(corpo))
    return cabecalho + corpo


class DecodificadorFrames:
    """
    Acumula bytes recebidos aos poucos (via socket.recv()) e extrai as
    mensagens JSON completas conforme o framing acima permite.
    """

    def __init__(self):
        self._buffer = bytearray()

    def alimentar(self, dados: bytes):
        """Adiciona bytes recebidos e retorna a lista de mensagens (dicts)
        que ja ficaram completas."""
        self._buffer.extend(dados)
        mensagens = []
        while True:
            if len(self._buffer) < TAMANHO_CABECALHO:
                break
            tamanho = struct.unpack("!I", self._buffer[:TAMANHO_CABECALHO])[0]
            if tamanho > TAMANHO_MAXIMO_MENSAGEM:
                raise ValueError(f"Mensagem de rede excede o tamanho maximo permitido ({tamanho} bytes)")
            if len(self._buffer) < TAMANHO_CABECALHO + tamanho:
                break
            corpo = bytes(self._buffer[TAMANHO_CABECALHO:TAMANHO_CABECALHO + tamanho])
            del self._buffer[:TAMANHO_CABECALHO + tamanho]
            mensagens.append(json.loads(corpo.decode("utf-8")))
        return mensagens
