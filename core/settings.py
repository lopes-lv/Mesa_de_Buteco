"""
settings.py - Configurações básicas do jogo, mantidas em memória durante a
sessão (não persistidas em disco). Acessadas via `app.settings` a partir de
qualquer tela.
"""
from .baralhos_skins import ORDEM_SKINS as _ORDEM_SKINS_NOVAS, ROTULOS_SKINS as _ROTULOS_SKINS_NOVOS
from . import layout

# Tempo (s) de cada velocidade de bot no Hold'em: vem de "geral.delay_bot_*_ms"
# em config/layout_padrao.json (editável pelo editor visual).
ORDEM_VELOCIDADES = ["lenta", "normal", "rapida"]
ROTULOS_VELOCIDADE = {"lenta": "Lenta", "normal": "Normal", "rapida": "Rápida"}

# Faixa do seletor de fichas na Configuração; o valor inicial vem de
# "geral.fichas_iniciais".
FICHAS_MIN, FICHAS_MAX, FICHAS_PASSO = 500, 5000, 500

ORDEM_BARALHO_SKINS = ["padrao", "dark"] + _ORDEM_SKINS_NOVAS
ROTULOS_BARALHO_SKIN = {"padrao": "Padrão", "dark": "Dark", **_ROTULOS_SKINS_NOVOS}


class Settings:
    """Estado das configurações básicas, com valores padrão sensatos."""

    def __init__(self):
        self.tela_cheia = False
        self.velocidade_bots = "normal"
        self.fichas_iniciais = layout.obter("geral.fichas_iniciais")
        self.mostrar_atalhos = True
        self.usar_joker_pifpaf = False
        self.baralho_skin = "padrao"
        self.selecao_automatica_pecas = False

    def delay_bot(self):
        return layout.obter(f"geral.delay_bot_{self.velocidade_bots}_ms") / 1000

    def ciclar_velocidade_bots(self):
        indice = ORDEM_VELOCIDADES.index(self.velocidade_bots)
        self.velocidade_bots = ORDEM_VELOCIDADES[(indice + 1) % len(ORDEM_VELOCIDADES)]

    def diminuir_fichas(self):
        self.fichas_iniciais = max(FICHAS_MIN, self.fichas_iniciais - FICHAS_PASSO)

    def aumentar_fichas(self):
        self.fichas_iniciais = min(FICHAS_MAX, self.fichas_iniciais + FICHAS_PASSO)

    def alternar_atalhos(self):
        self.mostrar_atalhos = not self.mostrar_atalhos

    def alternar_joker_pifpaf(self):
        self.usar_joker_pifpaf = not self.usar_joker_pifpaf

    def ciclar_baralho_skin(self, direcao=1):
        indice = ORDEM_BARALHO_SKINS.index(self.baralho_skin)
        self.baralho_skin = ORDEM_BARALHO_SKINS[(indice + direcao) % len(ORDEM_BARALHO_SKINS)]

    def alternar_selecao_automatica_pecas(self):
        self.selecao_automatica_pecas = not self.selecao_automatica_pecas
