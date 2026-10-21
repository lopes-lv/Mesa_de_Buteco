"""
carteira.py - Saldo de fichas do jogador no Hold'em solo, guardado em disco
entre as sessões (config/carteira.json, fora do git).

O jogador entra na mesa com o saldo inteiro e o que sobra volta para a
carteira. Se zerar, fica `ESPERA_REPOSICAO_S` (12 h) sem jogar; passado esse
tempo o saldo volta a `SALDO_INICIAL` (2000).
"""
import json
import os
import sys
import time


ARQUIVO = "carteira.json"
ESPERA_REPOSICAO_S = 12 * 60 * 60
SALDO_INICIAL = 2000  # carteira nova e reposição (independe de "geral.fichas_iniciais")


def caminho():
    # Mesma regra do layout.json: no .exe fica ao lado do executável.
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "config", ARQUIVO)


def _ler():
    """{"saldo": int, "zerou_em": epoch|None}; arquivo ausente/corrompido
    vira carteira nova com o valor padrão."""
    try:
        with open(caminho(), encoding="utf-8") as f:
            dados = json.load(f)
        saldo = dados["saldo"]
        zerou_em = dados.get("zerou_em")
        if isinstance(saldo, bool) or not isinstance(saldo, (int, float)):
            raise ValueError
        if zerou_em is not None and (isinstance(zerou_em, bool) or not isinstance(zerou_em, (int, float))):
            zerou_em = None
        return {"saldo": max(0, int(saldo)), "zerou_em": zerou_em}
    except (OSError, ValueError, KeyError, TypeError):
        return {"saldo": SALDO_INICIAL, "zerou_em": None}


def _gravar(dados):
    try:
        os.makedirs(os.path.dirname(caminho()), exist_ok=True)
        with open(caminho(), "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2)
    except OSError:
        pass  # sem permissão de escrita: o jogo segue, só não persiste


def _atualizar(dados, agora):
    """Aplica a reposição se o prazo de 12 h já passou. Devolve `dados`."""
    if dados["saldo"] > 0:
        dados["zerou_em"] = None
    elif dados["zerou_em"] is None:
        dados["zerou_em"] = agora
    elif agora - dados["zerou_em"] >= ESPERA_REPOSICAO_S or dados["zerou_em"] > agora:
        # (zerou_em no futuro = relógio mexido: repõe em vez de travar a carteira)
        dados["saldo"] = SALDO_INICIAL
        dados["zerou_em"] = None
    return dados


def saldo():
    """Saldo atual (já com a reposição aplicada, se o prazo passou)."""
    dados = _ler()
    antes = dict(dados)
    _atualizar(dados, time.time())
    if dados != antes:
        _gravar(dados)
    return dados["saldo"]


def segundos_para_reposicao():
    """Segundos até as fichas voltarem, ou None se o saldo é maior que zero."""
    saldo()  # aplica a reposição e fixa `zerou_em` se acabou de zerar
    dados = _ler()
    if dados["saldo"] > 0 or dados["zerou_em"] is None:
        return None
    return max(0, int(dados["zerou_em"] + ESPERA_REPOSICAO_S - time.time()))


def registrar(novo_saldo):
    """Grava o saldo depois de uma mão/partida; ao zerar, começa a espera."""
    dados = {"saldo": max(0, int(novo_saldo)), "zerou_em": None}
    if dados["saldo"] == 0:
        anterior = _ler()
        dados["zerou_em"] = anterior["zerou_em"] if anterior["saldo"] == 0 and anterior["zerou_em"] else time.time()
    _gravar(dados)


def formatar_espera(segundos):
    horas, resto = divmod(int(segundos), 3600)
    return f"{horas}h{resto // 60:02d}min"
