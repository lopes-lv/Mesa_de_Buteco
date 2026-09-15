"""
rede/descoberta.py - Geracao do codigo de sala + descoberta automatica via
broadcast UDP na rede local (ver MULTIPLAYER_PLANO.md, secao 3).
"""
import json
import random
import socket
import threading

from .protocolo import PORTA_UDP_DESCOBERTA

# Sem caracteres ambiguos (sem O/0, I/1) - facil de ditar/digitar em voz alta.
LETRAS_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ"
DIGITOS_CODIGO = "23456789"

PROCURAR_SALA = "procurar_sala"
SALA_ENCONTRADA = "sala_encontrada"


def gerar_codigo():
    """Código curto: 3 letras + 1 número (ex.: `KTR4`) - simples de ditar e
    digitar entre pessoas na mesma sala física."""
    letras = "".join(random.choices(LETRAS_CODIGO, k=3))
    numero = random.choice(DIGITOS_CODIGO)
    return f"{letras}{numero}"


class ServidorDescoberta(threading.Thread):
    """
    Roda no host: escuta broadcasts UDP perguntando pelo codigo da sala e
    responde (unicast) com o IP/porta TCP para quem perguntar o codigo certo.
    """

    def __init__(self, codigo, porta_tcp, nome_anfitriao, porta_udp=PORTA_UDP_DESCOBERTA):
        super().__init__(daemon=True)
        self.codigo = codigo
        self.porta_tcp = porta_tcp
        self.nome_anfitriao = nome_anfitriao
        self.porta_udp = porta_udp
        self._parar = threading.Event()
        self._socket = None

    def run(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._socket.bind(("", self.porta_udp))
        except OSError:
            # Porta ja em uso (ex.: outra instancia local) - descoberta
            # automatica fica indisponivel, mas o fallback manual por IP
            # continua funcionando normalmente.
            return
        self._socket.settimeout(0.5)

        while not self._parar.is_set():
            try:
                dados, endereco = self._socket.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                pedido = json.loads(dados.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if pedido.get("tipo") == PROCURAR_SALA and pedido.get("codigo") == self.codigo:
                resposta = json.dumps({
                    "tipo": SALA_ENCONTRADA,
                    "codigo": self.codigo,
                    "porta_tcp": self.porta_tcp,
                    "anfitriao": self.nome_anfitriao,
                }).encode("utf-8")
                try:
                    self._socket.sendto(resposta, endereco)
                except OSError:
                    pass

    def parar(self):
        self._parar.set()
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass


def procurar_sala_na_rede(codigo, porta_udp=PORTA_UDP_DESCOBERTA, timeout=3.0):
    """
    Cliente: manda um broadcast UDP perguntando pelo codigo e aguarda ate
    `timeout` segundos por uma resposta. Retorna dict {ip, porta_tcp,
    anfitriao} ou None se ninguem respondeu a tempo (rede sem broadcast,
    firewall, ou codigo errado) - nesse caso a tela de entrada deve deixar
    o usuario digitar IP:porta manualmente.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    pedido = json.dumps({"tipo": PROCURAR_SALA, "codigo": codigo}).encode("utf-8")
    try:
        sock.sendto(pedido, ("255.255.255.255", porta_udp))
    except OSError:
        sock.close()
        return None

    try:
        while True:
            try:
                dados, endereco = sock.recvfrom(4096)
            except socket.timeout:
                return None
            try:
                resposta = json.loads(dados.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if resposta.get("tipo") == SALA_ENCONTRADA and resposta.get("codigo") == codigo:
                return {
                    "ip": endereco[0],
                    "porta_tcp": resposta.get("porta_tcp"),
                    "anfitriao": resposta.get("anfitriao", "?"),
                }
    finally:
        sock.close()
