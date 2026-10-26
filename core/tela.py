"""Contrato comum das telas: `App.tela_atual` aceita qualquer objeto com estes três métodos."""
from typing import Any, Protocol


class Tela(Protocol):
    def atualizar(self, dt: Any) -> Any: ...

    def desenhar(self, tela: Any) -> Any: ...

    def tratar_evento(self, evento: Any) -> Any: ...
