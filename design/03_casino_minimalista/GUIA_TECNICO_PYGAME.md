# Guia Técnico — Estilo 3: Casino Minimalista High-End (Feltro Escuro + Dourado Vetorial)

Especificação para implementação em Pygame, resolução base **1920x1080** (16:9). Todas as medidas devem ser tratadas como proporcionais (multiplicar por `screen_width / 1920`).

Filosofia: luxo discreto. Muito espaço negativo, linhas finas douradas em vez de bordas grossas, sombras suaves e baixas (nunca sombra sólida deslocada), paleta quase monocromática (escuro + dourado) com toques pontuais de cor.

---

## 1. Paleta de Cores

| Papel | Hex | RGB (Python) | RGBA (Python) |
|---|---|---|---|
| Fundo principal (app) | `#15130F` | `(21, 19, 15)` | — |
| Painel elevado (cards, modais, HUD) | `#201C16` | `(32, 28, 22)` | — |
| Painel elevado (hover/realce) | `#2A241B` | `(42, 36, 27)` | — |
| Feltro da mesa | `#0F3D2C` | `(15, 61, 44)` | — |
| Feltro da mesa (vinheta/sombra interna) | `#082720` | `(8, 39, 32)` | — |
| Dourado primário (CTA, pote, destaque) | `#C9A227` | `(201, 162, 39)` | — |
| Dourado claro (hover, brilho) | `#E7C873` | `(231, 200, 115)` | — |
| Dourado escuro (hairline / borda sutil) | `#8C7024` | `(140, 112, 36)` | `(140, 112, 36, 130)` |
| Texto principal (sobre fundo escuro) | `#F5EFE0` | `(245, 239, 224)` | — |
| Texto secundário / muted | `#A79C86` | `(167, 156, 134)` | — |
| Face da carta (marfim) | `#F7F2E7` | `(247, 242, 231)` | — |
| Naipe vermelho (copas/ouros) — vinho elegante | `#9B2334` | `(155, 35, 52)` | — |
| Naipe preto (espadas/paus) — tinta | `#1A1710` | `(26, 23, 16)` | — |
| Status: pensando (info) — azul acinzentado | `#5E85A6` | `(94, 133, 166)` | — |
| Status: call/check — verde sálvia | `#6E8F5C` | `(110, 143, 92)` | — |
| Status: raise — usa o dourado primário | `#C9A227` | `(201, 162, 39)` | — |
| Status: fold — vinho apagado | `#6B3540` | `(107, 53, 64)` | — |
| Overlay de modal | preto 65% | — | `(0, 0, 0, 166)` |
| Sombra suave padrão | preto ~45% | — | `(0, 0, 0, 115)` |

**Regra de ouro:** dourado é usado com moderação — reservado para pote, CTA principal ("Jogar"/"Raise"), bordas hairline e pequenos acentos vetoriais (cantos, divisores). Nunca preencher grandes áreas sólidas de dourado.

---

## 2. Tipografia

| Uso | Fonte | Peso | Observação |
|---|---|---|---|
| Títulos / display (logo, headers) | **Playfair Display** | Bold (700) / Bold Italic | Serifada, elegante — assinatura do estilo "high-end" |
| Corpo / UI (botões, labels, nomes) | **Inter** | Regular (400) / SemiBold (600) | Neutra e legível, não compete com o serifado |
| Números, fichas, pote | **JetBrains Mono** | Medium (500) | Precisão "financeira" — números tabulares |

```python
import pygame
pygame.font.init()

FONT_DISPLAY   = pygame.font.Font("assets/fonts/PlayfairDisplay-Bold.ttf", 60)
FONT_DISPLAY_I = pygame.font.Font("assets/fonts/PlayfairDisplay-BoldItalic.ttf", 22)
FONT_BODY      = pygame.font.Font("assets/fonts/Inter-SemiBold.ttf", 18)
FONT_BODY_REG  = pygame.font.Font("assets/fonts/Inter-Regular.ttf", 15)
FONT_MONO      = pygame.font.Font("assets/fonts/JetBrainsMono-Medium.ttf", 20)
```

---

## 3. Dimensões e Proporções Base (1920x1080)

### Cartas
| Elemento | Largura x Altura | border_radius | Borda |
|---|---|---|---|
| Carta comunitária | 92 x 128 px | 8 px | 1.5 px dourado escuro `#8C7024` |
| Carta do jogador (mão) | 142 x 198 px | 10 px | 2 px dourado `#C9A227` |
| Carta de bot (virada) | 58 x 80 px | 6 px | 1.5 px dourado escuro |
| Verso da carta | mesma medida | igual | preenchimento `#0F3D2C` com filete dourado central fino |

### Layout geral
| Elemento | Valor |
|---|---|
| Margem externa segura | 56 px (mais espaço negativo que os demais estilos) |
| Gutter entre painéis | 28 px |
| Gutter pequeno | 12 px |
| `border_radius` painéis grandes | 10 px |
| `border_radius` botões | 6 px |
| `border_radius` badges/pills | 999 px |
| Espessura de borda padrão (hairline) | 1.5 px |
| Espessura de borda em elementos de destaque (mão do jogador, pote) | 2 px |
| Sombra suave — offset | (0, 10) px, blur equivalente (ver §4.2) |
| Comprimento do "corner accent" vetorial (bracket dourado) | 22 px por perna, 1.5 px espessura |

### Mesa de jogo
| Elemento | Medida |
|---|---|
| Painel da mesa (feltro) | 1480 x 600 px, centralizado, `border_radius` 16 px, borda 1.5 px dourada |
| Pote (badge) | 200 x 56 px, pill, fundo `#201C16`, borda 1.5 px dourada, texto dourado |
| Cartas comunitárias | 5 slots, gap 18 px |
| Avatar do bot | círculo 68 px diâmetro, anel dourado 1.5 px, fundo escuro |
| Card de bot | 216 x 92 px, `border_radius` 8 px |
| Painel de ação do jogador | 600 x 88 px, `border_radius` 10 px |
| Botão de ação | 172 x 64 px, `border_radius` 6 px |
| HUD lateral (histórico) | 300 px largura, `border_radius` 10 px |

---

## 4. Instruções de Renderização em Pygame

### 4.1 Painel com borda hairline dourada
Sem preenchimento de sombra sólida — usar borda fina e, opcionalmente, um leve gradiente vertical no fundo (simulado com `pygame.Surface` + blits de linhas, ou uma superfície pré-renderizada).

```python
def draw_luxury_panel(surface, rect, fill_color=(32, 28, 22),
                       border_color=(140, 112, 36), border_width=1, radius=10):
    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)
```

### 4.2 Sombra suave (soft shadow) via superfície com alpha
Diferente do neobrutalismo (sombra sólida deslocada), aqui a sombra deve ser **suave**. Pygame não tem blur nativo performático; a técnica recomendada é pré-renderizar uma sombra em baixa resolução com alpha decrescente (múltiplos retângulos concêntricos com alpha baixo) uma única vez e cachear como `Surface`, reaproveitando entre frames.

```python
def make_soft_shadow(size, radius, layers=6, base_alpha=10):
    w, h = size
    pad = layers * 4
    shadow_surf = pygame.Surface((w + pad*2, h + pad*2), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        alpha = base_alpha
        rect = pygame.Rect(pad - i*4, pad - i*4, w + i*8, h + i*8)
        pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), rect, border_radius=radius + i*2)
    return shadow_surf  # cachear e reusar; blitar antes do painel, levemente deslocado (0, 6-10px)
```

Use essa função **uma vez** por tamanho de painel (no carregamento da tela), nunca recalcular por frame.

### 4.3 Corner accent vetorial (detalhe dourado de canto)
Elemento assinatura do estilo — um pequeno "L" dourado nos cantos de painéis importantes (mesa, pote, card do jogador ativo), desenhado com `pygame.draw.line`:

```python
def draw_corner_accent(surface, rect, color=(201, 162, 39), leg=22, width=2, corners=("tl","br")):
    x, y, w, h = rect
    if "tl" in corners:
        pygame.draw.line(surface, color, (x, y), (x + leg, y), width)
        pygame.draw.line(surface, color, (x, y), (x, y + leg), width)
    if "br" in corners:
        pygame.draw.line(surface, color, (x + w, y + h), (x + w - leg, y + h), width)
        pygame.draw.line(surface, color, (x + w, y + h), (x + w, y + h - leg), width)
    # análogo para "tr" e "bl" se necessário
```

### 4.4 Naipes e cartas
Face marfim (`#F7F2E7`), rank + naipe em `#1A1710` (preto/tinta) ou `#9B2334` (vinho) conforme a cor do naipe. Nada de contorno grosso — usar apenas a borda hairline dourada padrão (`draw_luxury_panel`).

### 4.5 Status do bot (badges)
Pills pequenos, fundo sólido na cor de status, texto `#F5EFE0`, sem borda adicional (o próprio preenchimento já basta neste estilo mais limpo):
- Pensando → `#5E85A6`
- Call/Check → `#6E8F5C`
- Raise → `#C9A227` (texto em `#1A1710` para contraste sobre dourado)
- Fold → `#6B3540`, card do bot com alpha reduzido (~55%)

### 4.6 Organização de camadas (z-order)
1. Fundo escuro (`#15130F`)
2. Sombra suave pré-renderizada do painel da mesa
3. Painel do feltro (com hairline dourado + corner accents)
4. Cards de bots + avatares
5. Cartas comunitárias + pote
6. Cartas do jogador + painel de ação (com corner accent dourado, é o elemento de maior destaque)
7. HUD lateral
8. Overlays/modais (`SRCALPHA`, overlay 65% preto)

---

## 5. Checklist de Consistência
- [ ] Nenhuma borda preta grossa — tudo hairline dourado (1–2 px).
- [ ] Sombras sempre suaves/baixas, nunca sólidas deslocadas.
- [ ] Dourado reservado a: pote, CTA principal, bordas de destaque, corner accents. Nunca preenchimento grande.
- [ ] Espaço negativo generoso — evitar lotar a tela; menos elementos visíveis simultaneamente que nos outros estilos.
- [ ] Números sempre em `JetBrains Mono` para reforçar precisão "financeira".
