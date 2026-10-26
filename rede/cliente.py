"""
rede/cliente.py - ClienteSala: lado de quem entra numa sala pelo codigo/IP.

Mesmo padrao de threads+filas do host (ver anfitriao.py): a conexao (mesmo
o `connect()` inicial, que pode demorar/travar se o host nao responder) roda
em background, nunca no thread principal do jogo. As telas (EntrarSalaScreen,
LobbyScreen, MesaRemotaScreen) so leem o atributo `status`/`jogadores_lobby`
ou drenam `mensagens_entrantes` a cada frame - nunca bloqueiam.
"""
import queue
from typing import Any
import socket
import threading

from . import protocolo
from .protocolo import DecodificadorFrames

TIMEOUT_CONEXAO = 5.0


class ClienteSala:
    def __init__(self, nome):
        self.nome = nome
        self.mensagens_entrantes: queue.Queue = queue.Queue()
        self.jogadores_lobby = []
        self.meu_id = None

        # "conectando" -> "conectado" -> ("desconectado" | "sala_encerrada")
        # ou "conectando" -> ("erro" | "recusado")
        self.status = "conectando"
        self.erro = None

        self._sock: Any = None
        self._fila_saida: queue.Queue = queue.Queue()
        self._parar = threading.Event()

    def conectar_async(self, ip, porta):
        threading.Thread(target=self._conectar, args=(ip, porta), daemon=True).start()

    def _conectar(self, ip, porta):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT_CONEXAO)
        try:
            sock.connect((ip, int(porta)))
        except (OSError, ValueError) as erro:
            self.status = "erro"
            self.erro = str(erro)
            return
        sock.settimeout(None)
        self._sock = sock
        threading.Thread(target=self._loop_leitura, daemon=True).start()
        threading.Thread(target=self._loop_escrita, daemon=True).start()
        self.enviar({"tipo": protocolo.ENTRAR, "nome": self.nome})

    def _loop_leitura(self):
        decodificador = DecodificadorFrames()
        try:
            while not self._parar.is_set():
                try:
                    dados = self._sock.recv(4096)
                except OSError:
                    break
                if not dados:
                    break
                try:
                    mensagens = decodificador.alimentar(dados)
                except ValueError:
                    break
                for msg in mensagens:
                    self._processar(msg)
        finally:
            if self.status == "conectado":
                self.status = "desconectado"

    def _processar(self, msg):
        tipo = msg.get("tipo")
        if tipo == protocolo.ENTRADA_OK:
            self.meu_id = msg.get("seu_id")
            self.jogadores_lobby = msg.get("jogadores", [])
            self.status = "conectado"
        elif tipo == protocolo.RECUSADO:
            self.status = "recusado"
            self.erro = msg.get("motivo", "Conexao recusada")
        elif tipo == protocolo.LOBBY_ATUALIZADO:
            self.jogadores_lobby = msg.get("jogadores", [])
        elif tipo == protocolo.SALA_ENCERRADA:
            self.status = "sala_encerrada"
            self.erro = msg.get("motivo", "Sala encerrada pelo anfitriao")
        else:
            self.mensagens_entrantes.put(msg)

    def _loop_escrita(self):
        while not self._parar.is_set():
            try:
                mensagem = self._fila_saida.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._sock.sendall(protocolo.empacotar(mensagem))
            except OSError:
                break

    def enviar(self, mensagem):
        self._fila_saida.put(mensagem)

    def fechar(self):
        self._parar.set()
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
