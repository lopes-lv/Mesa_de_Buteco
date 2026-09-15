"""
rede/anfitriao.py - AnfitriaoSala: lado do host no multiplayer local.

Modelo de concorrencia (ver MULTIPLAYER_PLANO.md, secao 5): uma thread
aceitando conexoes, uma thread de leitura por cliente (empurrando mensagens
para uma fila compartilhada) e uma thread de escrita por cliente (drenando
uma fila de saida propria, para nunca travar o thread principal do jogo
esperando um cliente lento). O loop do jogo (TableScreen) so faz
`queue.get_nowait()` a cada frame - nunca bloqueia.
"""
import queue
import socket
import threading
import time

from . import protocolo
from .descoberta import ServidorDescoberta, gerar_codigo
from .protocolo import DecodificadorFrames, PORTA_TCP_PADRAO, MAX_JOGADORES


def obter_ip_local():
    """Melhor esforco para achar o IP da maquina na rede local (nao abre
    conexao de verdade - so usa o socket UDP pra descobrir a interface que
    o SO usaria para sair para a rede)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class _ClienteConectado:
    def __init__(self, conn, endereco):
        self.conn = conn
        self.endereco = endereco
        self.id = None
        self.nome = None
        self.fila_saida = queue.Queue()
        self.ativo = True


class AnfitriaoSala:
    def __init__(self, nome_anfitriao, max_jogadores=MAX_JOGADORES, porta_tcp=PORTA_TCP_PADRAO):
        self.nome_anfitriao = nome_anfitriao
        self.max_jogadores = max_jogadores
        self.codigo = gerar_codigo()

        self.mensagens_entrantes = queue.Queue()  # itens: (jogador_id, msg_dict)
        self.jogadores_conectados = {}  # id -> nome (so clientes remotos, sem contar o host)
        self.desconectados = set()      # ids que cairam durante uma partida em andamento
        self.em_jogo = False
        self.erro_fatal = None

        self._clientes = {}  # id -> _ClienteConectado
        self._proximo_id = 1  # id 0 e sempre o host (jogador humano local)
        self._lock = threading.Lock()
        self._parar = threading.Event()

        self._porta_tcp_desejada = porta_tcp
        self._socket_escuta = None
        self.porta_tcp = None
        self.ip_local = obter_ip_local()

        self._thread_aceitar = None
        self._servidor_descoberta = None

    # ------------------------------------------------------------ Ciclo de vida
    def iniciar(self):
        """Abre o socket de escuta TCP e comeca a aceitar clientes. Retorna
        True em caso de sucesso; em falha, guarda o erro em `erro_fatal`."""
        self._socket_escuta = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._socket_escuta.bind(("0.0.0.0", self._porta_tcp_desejada))
        except OSError:
            try:
                self._socket_escuta.bind(("0.0.0.0", 0))
            except OSError as erro:
                self.erro_fatal = str(erro)
                return False
        self._socket_escuta.listen(self.max_jogadores)
        self._socket_escuta.settimeout(0.5)
        self.porta_tcp = self._socket_escuta.getsockname()[1]

        self._thread_aceitar = threading.Thread(target=self._loop_aceitar, daemon=True)
        self._thread_aceitar.start()

        self._servidor_descoberta = ServidorDescoberta(self.codigo, self.porta_tcp, self.nome_anfitriao)
        self._servidor_descoberta.start()
        return True

    def encerrar(self, motivo="Sala encerrada pelo anfitriao"):
        with self._lock:
            clientes = list(self._clientes.values())
        for cliente in clientes:
            self._enviar_para_cliente(cliente, {"tipo": protocolo.SALA_ENCERRADA, "motivo": motivo})
        # da tempo das threads de escrita escoarem a mensagem acima antes de
        # fechar os sockets - senao a conexao morre antes do aviso sair.
        time.sleep(0.2)
        self._parar.set()
        for cliente in clientes:
            self._fechar_cliente(cliente)
        if self._servidor_descoberta:
            self._servidor_descoberta.parar()
        if self._socket_escuta:
            try:
                self._socket_escuta.close()
            except OSError:
                pass

    # ------------------------------------------------------------ Envio
    def enviar_para_todos(self, mensagem):
        with self._lock:
            clientes = list(self._clientes.values())
        for cliente in clientes:
            self._enviar_para_cliente(cliente, mensagem)

    def enviar_para(self, jogador_id, mensagem):
        with self._lock:
            cliente = self._clientes.get(jogador_id)
        if cliente:
            self._enviar_para_cliente(cliente, mensagem)

    def _enviar_para_cliente(self, cliente, mensagem):
        if cliente.ativo:
            cliente.fila_saida.put(mensagem)

    # ------------------------------------------------------------ Lobby
    def lista_jogadores_lobby(self):
        jogadores = [{"id": 0, "nome": self.nome_anfitriao, "anfitriao": True}]
        with self._lock:
            for jid, nome in self.jogadores_conectados.items():
                jogadores.append({"id": jid, "nome": nome, "anfitriao": False})
        return jogadores

    def total_jogadores(self):
        return 1 + len(self.jogadores_conectados)

    def remover_jogador(self, jogador_id, motivo_desconexao=True):
        with self._lock:
            cliente = self._clientes.pop(jogador_id, None)
            self.jogadores_conectados.pop(jogador_id, None)
            if motivo_desconexao and self.em_jogo:
                self.desconectados.add(jogador_id)
        if cliente:
            self._fechar_cliente(cliente)
        if not self.em_jogo:
            self.enviar_para_todos({"tipo": protocolo.LOBBY_ATUALIZADO, "jogadores": self.lista_jogadores_lobby()})

    # ------------------------------------------------------------ Threads internas
    def _loop_aceitar(self):
        while not self._parar.is_set():
            try:
                conn, endereco = self._socket_escuta.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            cliente = _ClienteConectado(conn, endereco)
            threading.Thread(target=self._loop_leitura, args=(cliente,), daemon=True).start()
            threading.Thread(target=self._loop_escrita, args=(cliente,), daemon=True).start()

    def _loop_leitura(self, cliente):
        decodificador = DecodificadorFrames()
        try:
            while not self._parar.is_set():
                try:
                    dados = cliente.conn.recv(4096)
                except OSError:
                    break
                if not dados:
                    break
                try:
                    mensagens = decodificador.alimentar(dados)
                except ValueError:
                    break
                for msg in mensagens:
                    self._processar_mensagem(cliente, msg)
        finally:
            # Durante um encerrar() intencional, o proprio encerrar() ja
            # cuida de fechar/remover os clientes - evita duplicar o
            # broadcast de lobby_atualizado ou reabrir um cliente ja removido.
            if not self._parar.is_set():
                if cliente.id is not None:
                    self.remover_jogador(cliente.id)
                else:
                    self._fechar_cliente(cliente)

    def _loop_escrita(self, cliente):
        while cliente.ativo:
            try:
                mensagem = cliente.fila_saida.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                cliente.conn.sendall(protocolo.empacotar(mensagem))
            except OSError:
                break

    def _processar_mensagem(self, cliente, msg):
        tipo = msg.get("tipo")
        if tipo == protocolo.ENTRAR:
            self._registrar_entrada(cliente, msg)
            return
        if cliente.id is None:
            return  # ignora mensagens de quem ainda nao completou o "entrar"
        if tipo == protocolo.SAIR:
            cliente.conn.close()
            return
        if tipo == protocolo.CHAT:
            # O relay (resolver o nome do remetente e reenviar pra todos,
            # inclusive de volta pra quem mandou) acontece aqui na camada de
            # rede - assim toda tela (lobby, mesa do Hold'em, mesa do Pif
            # Paf) so precisa tratar "chat" chegando pela fila igual a
            # qualquer outra mensagem, sem duplicar essa lógica.
            nome = cliente.nome or self.jogadores_conectados.get(cliente.id, "?")
            texto = str(msg.get("texto", "")).strip()[:200]
            if texto:
                mensagem_relay = {"tipo": protocolo.CHAT, "remetente": nome, "texto": texto}
                self.enviar_para_todos(mensagem_relay)
                self.mensagens_entrantes.put((cliente.id, mensagem_relay))
            return
        self.mensagens_entrantes.put((cliente.id, msg))

    def _registrar_entrada(self, cliente, msg):
        nome = str(msg.get("nome", "Jogador")).strip()[:20] or "Jogador"
        if self.em_jogo:
            self._enviar_para_cliente(cliente, {"tipo": protocolo.RECUSADO, "motivo": "A sala ja esta em jogo"})
            return
        with self._lock:
            if self.total_jogadores() >= self.max_jogadores:
                cheio = True
            else:
                cheio = False
                jogador_id = self._proximo_id
                self._proximo_id += 1
                self.jogadores_conectados[jogador_id] = nome
                self._clientes[jogador_id] = cliente
                cliente.id = jogador_id
                cliente.nome = nome
        if cheio:
            self._enviar_para_cliente(cliente, {"tipo": protocolo.RECUSADO, "motivo": "Sala cheia"})
            return
        self._enviar_para_cliente(cliente, {
            "tipo": protocolo.ENTRADA_OK,
            "seu_id": cliente.id,
            "jogadores": self.lista_jogadores_lobby(),
        })
        self.enviar_para_todos({"tipo": protocolo.LOBBY_ATUALIZADO, "jogadores": self.lista_jogadores_lobby()})

    def _fechar_cliente(self, cliente):
        cliente.ativo = False
        try:
            cliente.conn.close()
        except OSError:
            pass
