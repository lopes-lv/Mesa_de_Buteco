# Guia Técnico — Estilo 5: Cozy Flat / Indie Boardgame

Especificação para implementação em Pygame, resolução base **1920x1080** (16:9). Todas as medidas devem ser tratadas como proporcionais (multiplicar por `screen_width / 1920`).

Filosofia: acolhedor, amigável, "jogo de tabuleiro de mesa de madeira num fim de tarde". Cores quentes e pastel, formas bem arredondadas, contornos em marrom (nunca preto puro), sombras suaves e baixas — flat design com leve profundidade, sem gradientes complexos nem efeitos técnicos (sem glass, sem hard-shadow neobrutalista).

---

## 1. Paleta de Cores

| Papel | Hex | RGB (Python) | RGBA (Python) |
|---|---|---|---|
| Fundo principal (app) | `#FDF3E2` | `(253, 243, 226)` | — |
| Painel / card (branco quente) | `#FFFDF8` | `(255, 253, 248)` | — |
| Mesa (tampo de madeira, substitui o feltro) | `#E8A45C` | `(232, 164, 92)` | — |
| Mesa (sombra/veio mais escuro) | `#C97F3D` | `(201, 127, 61)` | — |
| Contorno / linha estrutural (marrom quente, substitui o preto) | `#5C4433` | `(92, 68, 51)` | — |
| Texto principal | `#4A3728` | `(74, 55, 40)` | — |
| Texto secundário / muted | `#9C8770` | `(156, 135, 112)` | — |
| Terracota (Fold / alerta) | `#E4674B` | `(228, 103, 75)` | — |
| Verde-sálvia (Call / Check / sucesso) | `#7FB685` | `(127, 182, 133)` | — |
| Mostarda (Pote / CTA / Raise) | `#F3C64B` | `(243, 198, 75)` | — |
| Azul-poeira (Pensando / info) | `#6FA8D6` | `(111, 168, 214)` | — |
| Lavanda (badge bloqueado) | `#B79FD1` | `(183, 159, 209)` | — |
| Naipe vermelho (copas/ouros), tom amigável | `#E1594B` | `(225, 89, 75)` | — |
| Naipe "preto" (espadas/paus) — usa marrom-tinta, nunca preto puro | `#4A3728` | `(74, 55, 40)` | — |
| Cinza bloqueado (modos "em breve") | `#E6DCC8` | `(230, 220, 200)` | — |
| Sombra suave quente | marrom 15% opacidade | — | `(74, 55, 40, 38)` |
| Overlay de modal | marrom escuro 50% | — | `(58, 40, 28, 128)` |

**Regra de ouro:** nunca usar preto puro `(0,0,0)` em lugar nenhum — todo "escuro" da paleta é um marrom quente. Isso é o que dá a sensação "cozy".

---

## 2. Tipografia

| Uso | Fonte | Peso | Observação |
|---|---|---|---|
| Títulos / display (logo, headers) | **Baloo 2** | Bold (700) / ExtraBold (800) | Bem arredondada e amigável, ótima para jogos indie |
| Corpo / UI (botões, labels, nomes) | **Nunito** | SemiBold (600) / Bold (700) | Terminais arredondados, combina com a Baloo 2 |
| Números, fichas, pote | **Nunito** | ExtraBold (800), com `tabular numbers` | Evita usar fonte mono técnica — mantém o clima "de tabuleiro" |

```python
import pygame
pygame.font.init()

FONT_DISPLAY  = pygame.font.Font("assets/fonts/Baloo2-Bold.ttf", 58)
FONT_H2       = pygame.font.Font("assets/fonts/Baloo2-Bold.ttf", 28)
FONT_BODY     = pygame.font.Font("assets/fonts/Nunito-SemiBold.ttf", 19)
FONT_BODY_SM  = pygame.font.Font("assets/fonts/Nunito-SemiBold.ttf", 15)
FONT_NUMBERS  = pygame.font.Font("assets/fonts/Nunito-ExtraBold.ttf", 22)
```
> Nota: Pygame não aplica `font-feature-settings` (tabular-nums) automaticamente. Para números que mudam de dígitos (fichas, pote), monitore a largura renderizada e centralize o texto pelo `rect` a cada frame — ou use `Nunito` que já tem números com largura bem próxima entre si.

---

## 3. Dimensões e Proporções Base (1920x1080)

### Cartas
| Elemento | Largura x Altura | border_radius | Borda |
|---|---|---|---|
| Carta comunitária | 100 x 138 px | 18 px | 3 px marrom `#5C4433` |
| Carta do jogador (mão) | 152 x 210 px | 22 px | 4 px marrom |
| Carta de bot (virada) | 62 x 86 px | 12 px | 2.5 px marrom |
| Verso da carta | mesma medida | igual | preenchimento `#6FA8D6` com padrão de pontinhos/losangos simples |

### Layout geral
| Elemento | Valor |
|---|---|
| Margem externa segura | 48 px |
| Gutter entre painéis | 24 px |
| Gutter pequeno | 12 px |
| `border_radius` painéis grandes | 32 px |
| `border_radius` botões | 18 px |
| `border_radius` badges/pills | 999 px |
| Espessura de borda padrão | 3 px |
| Espessura de borda em elementos grandes (mesa) | 4 px |
| Sombra suave — offset | (0, 8) px, baixa opacidade (ver §4.2) |

### Mesa de jogo
| Elemento | Medida |
|---|---|
| Painel da mesa (tampo de madeira) | 1500 x 620 px, centralizado, `border_radius` 48 px, borda 4 px marrom |
| Pote (badge) | 190 x 64 px, pill, fundo mostarda `#F3C64B`, borda 3 px marrom |
| Cartas comunitárias | 5 slots, gap 16 px |
| Avatar do bot | círculo 74 px diâmetro, borda 3 px marrom, fundo pastel |
| Card de bot | 220 x 100 px, `border_radius` 22 px |
| Painel de ação do jogador | 620 x 96 px, `border_radius` 28 px |
| Botão de ação | 180 x 72 px, `border_radius` 18 px |
| HUD lateral (histórico) | 320 px largura, `border_radius` 28 px |

---

## 4. Instruções de Renderização em Pygame

### 4.1 Painel arredondado com contorno marrom
```python
def draw_cozy_panel(surface, rect, fill_color, border_color=(92, 68, 51),
                     border_width=3, radius=24):
    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)
```

### 4.2 Sombra suave quente (baixo offset, baixa opacidade)
Assim como no estilo Casino, evite recalcular blur por frame — pré-renderize a sombra uma vez em `Surface(SRCALPHA)` e faça cache. A diferença aqui é a cor (marrom quente, não preto) e o offset pequeno:

```python
def make_cozy_shadow(size, radius, offset=(0, 8), color=(74, 55, 40, 45)):
    w, h = size
    shadow_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(10, 10 + offset[1], w, h)
    pygame.draw.rect(shadow_surf, color, shadow_rect, border_radius=radius)
    return shadow_surf  # blitar atrás do painel principal, cacheado
```

### 4.3 Avatares "blob" arredondados
Círculo simples com contorno marrom grosso — mantém consistência com o resto (evitar rostos ilustrados complexos nesta fase de protótipo; a "personalidade" vem da cor de fundo + iniciais):

```python
def draw_avatar(surface, center, radius, fill_color, border_color=(92,68,51), border_width=3):
    pygame.draw.circle(surface, fill_color, center, radius)
    pygame.draw.circle(surface, border_color, center, radius, width=border_width)
```

### 4.4 Botões com efeito "squish" (em vez de sombra deslocada dura)
No hover, aumente levemente a escala (1.03x) do retângulo; no clique, reduza para 0.97x. Isso substitui o efeito de "sombra que se move" do neobrutalismo por algo mais macio e orgânico — coerente com a estética cozy. Combine com um leve deslocamento vertical (-2px no hover, +2px no clique).

### 4.5 Naipes e cartas
Face branca quente (`#FFFDF8`), contorno marrom grosso e bem arredondado (`radius` alto), rank + naipe em `#E1594B` (vermelho amigável) ou `#4A3728` (marrom-tinta, nunca preto). O verso da carta pode ter um padrão simples de losangos ou bolinhas em `#6FA8D6` sobre fundo branco, contornado em marrom.

### 4.6 Status do bot (badges)
Pills com contorno marrom fino (2px) e preenchimento pastel:
- Pensando → `#6FA8D6` (azul-poeira), texto `#FFFDF8`
- Call/Check → `#7FB685` (verde-sálvia), texto `#4A3728`
- Raise → `#F3C64B` (mostarda), texto `#4A3728`
- Fold → `#E6DCC8` (cinza quente), texto `#9C8770`, card do bot com alpha reduzido (~60%)

### 4.7 Organização de camadas (z-order)
1. Fundo (`#FDF3E2`)
2. Sombra suave pré-renderizada do painel da mesa
3. Painel da mesa (tampo de madeira) com contorno marrom
4. Cards de bots + avatares
5. Cartas comunitárias + pote
6. Cartas do jogador + painel de ação (maior escala, mais destaque visual)
7. HUD lateral
8. Overlays/modais (`SRCALPHA`, overlay marrom 50%)

---

## 5. Checklist de Consistência
- [ ] Nunca usar preto puro `(0,0,0)` — todo contorno/texto escuro é marrom quente `#4A3728`/`#5C4433`.
- [ ] `border_radius` sempre generoso (mín. 12 px, ideal 18–32 px nos painéis grandes) — é o que garante a sensação "fofa".
- [ ] Sombras sempre suaves e de baixo offset, nunca duras/deslocadas como no neobrutalismo.
- [ ] Paleta pastel, saturação média — evitar cores neon ou muito vibrantes, que quebrariam o clima acolhedor.
- [ ] Números em fonte arredondada (`Nunito`), nunca em fonte mono técnica.
