"""
deck.py - Representação de cartas e baralho para o Texas Hold'em
"""
import random

NAIPES = ["copas", "ouros", "paus", "espadas"]
VALORES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]  # 11=J, 12=Q, 13=K, 14=A

VALOR_TEXTO = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
    10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"
}

NAIPE_SIMBOLO = {
    "copas": "H",
    "ouros": "D",
    "paus": "C",
    "espadas": "S"
}

# Cores estilo pixel art (naipes vermelhos vs pretos)
NAIPE_COR = {
    "copas": (200, 40, 40),
    "ouros": (200, 40, 40),
    "paus": (25, 25, 25),
    "espadas": (25, 25, 25)
}


class Card:
    __slots__ = ("valor", "naipe")

    def __init__(self, valor, naipe):
        self.valor = valor
        self.naipe = naipe

    @property
    def texto(self):
        return VALOR_TEXTO[self.valor]

    @property
    def simbolo_naipe(self):
        return NAIPE_SIMBOLO[self.naipe]

    @property
    def cor(self):
        return NAIPE_COR[self.naipe]

    def __repr__(self):
        return f"{self.texto}{self.simbolo_naipe}"

    def __eq__(self, other):
        return self.valor == other.valor and self.naipe == other.naipe

    def __hash__(self):
        return hash((self.valor, self.naipe))


class Deck:
    def __init__(self):
        self.cartas = [Card(v, n) for n in NAIPES for v in VALORES]
        self.embaralhar()

    def embaralhar(self):
        random.shuffle(self.cartas)

    def comprar(self, quantidade=1):
        compradas = self.cartas[:quantidade]
        self.cartas = self.cartas[quantidade:]
        return compradas

    def restantes(self):
        return len(self.cartas)
