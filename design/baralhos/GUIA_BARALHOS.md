# Guia: baralhos dos 8 estilos novos

Prévia: [previa_baralhos.png](previa_baralhos.png) (gerada pelo Pygame, é a referência) e
[baralhos.html](baralhos.html) (aproximação no navegador). Cada linha mostra: A♠, K♥, 10♦, Q♣, coringa,
verso, espaço vazio e carta destacada.

| id (`skin_id`) | Rótulo | Combina com o mockup |
|---|---|---|
| `dark_glass` | Dark Glass | `02_dark_glassmorphism` |
| `terminal` | Terminal | `04_terminal_tatico` |
| `art_deco` | Art Déco | `06_art_deco_cassino` |
| `pixel_crt` | Pixel CRT | `07_pixel_retro_crt` |
| `synthwave` | Synthwave | `08_synthwave_neon` |
| `papel_vintage` | Papel Vintage | `09_papel_vintage` |
| `editorial` | Editorial | `10_editorial_suico` |
| `zen` | Zen | `11_zen_japones` |

Os dois baralhos atuais (`padrao` e `dark`, neobrutalistas) continuam sendo desenhados por
`ui_theme.desenhar_carta`; nada abaixo os substitui.

## Arquivos

- `baralhos_skins.py`: os 8 baralhos como **dados** (`SKINS`) + o desenhista
  `desenhar_carta_skin(...)`. Só usa `pygame.draw`, sem imagens. Tem cache de superfícies.
- `previa_baralhos.py`: regenera o PNG e o HTML (`python design/baralhos/previa_baralhos.py`).

A carta passada só precisa ter `.texto`, `.naipe` e `.simbolo_naipe` (o mesmo contrato de `core/deck.py:Card`).

## Como ligar no jogo (4 passos)

O jogo já tem tudo para trocar de baralho: `Settings.baralho_skin`, o botão em Ajustes que cicla as
skins e `ui_theme.set_estilo_baralho()`, chamado a cada frame em `main.py:197`. Basta registrar as novas skins.

**1. Copiar o módulo**

```bash
cp design/baralhos/baralhos_skins.py core/baralhos_skins.py
```

**2. Registrar as skins em `core/settings.py`**

```python
from .baralhos_skins import ORDEM_SKINS as _NOVAS, ROTULOS_SKINS as _ROTULOS_NOVOS

ORDEM_BARALHO_SKINS = ["padrao", "dark"] + _NOVAS
ROTULOS_BARALHO_SKIN = {"padrao": "Padrão", "dark": "Dark", **_ROTULOS_NOVOS}
```

`ciclar_baralho_skin()` e o rótulo no botão de Ajustes passam a funcionar sem mais mudanças.

**3. Desviar `desenhar_carta` em `core/ui_theme.py`**

No início da função, depois da assinatura:

```python
from . import baralhos_skins   # no topo do arquivo

def desenhar_carta(tela, x, y, largura, altura, carta=None, virada_para_baixo=False, destaque=False):
    if _estilo_baralho in baralhos_skins.SKINS:
        return baralhos_skins.desenhar_carta_skin(
            tela, _estilo_baralho, x, y, largura, altura,
            carta=carta, virada_para_baixo=virada_para_baixo, destaque=destaque)
    ...  # código atual (padrao/dark) continua igual
```

Todos os pontos de desenho (mesa de Hold'em, Pif Paf, preview em Config) já chamam essa função, então o
baralho muda em todos os lugares de uma vez. O retorno é o `Rect` da carta, como hoje.

**4. Slots vazios (opcional)**

As cartas comunitárias ainda não reveladas hoje são retângulos brancos desenhados em `holdem/table_screen.py`
(perto da linha 513). Para usar o tracejado da skin, chame
`baralhos_skins.desenhar_carta_skin(..., vazia=True)` quando a skin for uma das novas.

## Testar

```bash
python main.py
```

Ajustes → botão do baralho (cicla Padrão, Dark e os 8 novos), depois inicie uma partida de Hold'em ou Pif Paf.
Como não há suíte de testes, a conferência é visual. Para ver só as cartas, rode `previa_baralhos.py`.

## Ajustar ou criar um baralho

Cada skin é uma entrada em `SKINS` (campos documentados no topo de `baralhos_skins.py`): cores da face e
da borda, raio, sombra deslocada ou brilho neon, cor de naipes pretos e vermelhos, família de fonte e padrão do
verso (`losango`, `rede`, `xadrez`, `listras`, `quadrado`, `circulo`, `moldura`, `neon`). Para um baralho
novo, copie uma entrada, mude o id e rode a prévia. Ele aparece no ciclo de Ajustes automaticamente, pois
`ORDEM_SKINS` é derivada do dicionário.

## Pontos de atenção

- **Fontes**: usam fontes de sistema (Georgia, Consolas, Segoe UI), como o resto do jogo. A skin `pixel_crt`
  desliga o antialias para parecer pixelada; para um visual 8-bit fiel, adicione uma `.ttf` pixel em `assets/fonts/`
  e troque `_fonte()`.
- **Tamanhos**: espessura de borda, raio e sombra escalam com a largura (`largura / 64`), então funcionam do
  tamanho dos bots (~42 px) ao da mão do jogador (~84 px).
- **Contraste**: no Terminal e no Synthwave, copas/ouros são distinguidos de paus/espadas por **cor e borda**
  (âmbar / rosa); o formato do naipe continua visível para quem não distingue cores.
- **Dominó**: as peças (`domino_theme.desenhar_peca`) não mudam com o baralho; para combinar com a skin,
  seria um trabalho à parte.
- **Cache**: `_cache` guarda até 400 superfícies; é esvaziado sozinho.
