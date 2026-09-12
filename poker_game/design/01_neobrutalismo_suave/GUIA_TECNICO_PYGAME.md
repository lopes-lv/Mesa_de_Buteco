# Guia Técnico — Estilo 1: Neobrutalismo Suave / Dashboard Analítico

Especificação para implementação em Pygame, resolução base **1920x1080** (16:9). Todas as medidas devem ser tratadas como proporcionais (multiplicar por `screen_width / 1920`) para suportar outras resoluções widescreen.

---

## 1. Paleta de Cores

Estilo "soft neobrutalism": fundo claro e quente, bordas grossas quase-pretas, sombras sólidas (sem blur, deslocadas), cores de destaque saturadas mas não neon.

| Papel | Hex | RGB (Python) | RGBA (Python, c/ transparência) |
|---|---|---|---|
| Fundo principal (app) | `#F2EFE7` | `(242, 239, 231)` | — |
| Fundo secundário / painel | `#FFFFFF` | `(255, 255, 255)` | — |
| Feltro da mesa (verde) | `#2F6B4F` | `(47, 107, 79)` | — |
| Feltro da mesa (sombra interna) | `#245740` | `(36, 87, 64)` | — |
| Contorno / linha estrutural (quase-preto) | `#1B1B1B` | `(27, 27, 27)` | — |
| Texto principal | `#1B1B1B` | `(27, 27, 27)` | — |
| Texto secundário / muted | `#5C5850` | `(92, 88, 80)` | — |
| Amarelo destaque (Pote / CTA principal) | `#FFC93C` | `(255, 201, 60)` | — |
| Coral (Fold / Alerta) | `#FF6B57` | `(255, 107, 87)` | — |
| Azul (Call / Check / Info) | `#4C86F0` | `(76, 134, 240)` | — |
| Verde-menta (Sucesso / Raise / Ativo) | `#3DD9A4` | `(61, 217, 164)` | — |
| Roxo (badge / modo bloqueado) | `#A78BFA` | `(167, 139, 250)` | — |
| Cinza card bloqueado | `#D8D4C8` | `(216, 212, 200)` | — |
| Sombra sólida (offset shadow) | `#1B1B1B` a 100% opacidade | `(27, 27, 27)` | `(27, 27, 27, 255)` |
| Overlay escurecido (modais) | preto 55% | — | `(0, 0, 0, 140)` |
| Vidro de contagem de fichas (fundo mono chip) | `#1B1B1B` | `(27, 27, 27)` | `(27, 27, 27, 235)` |
| Borda de destaque dourado (naipe ouros/copas texto) | `#D93B3B` | `(217, 59, 59)` | — |
| Naipes pretos (espadas/paus) | `#1B1B1B` | `(27, 27, 27)` | — |

**Regra de contraste:** nunca usar sombra com alpha < 255 — neobrutalismo pede sombra **sólida e opaca**, sem blur/glow. Blur é reservado ao estilo Glassmorphism (estilo 2).

---

## 2. Tipografia

Todas gratuitas, via Google Fonts, com bom suporte a glifos e fácil de converter para `.ttf` local (baixar e usar com `pygame.font.Font`, não `pygame.font.SysFont`, para garantir consistência entre máquinas).

| Uso | Fonte | Peso | Observação |
|---|---|---|---|
| Títulos / display (logo, headers de tela) | **Space Grotesk** | Bold (700) | Geométrica, com personalidade — combina com neobrutalismo |
| Corpo de texto / UI geral (botões, labels) | **Inter** | Medium (500) / SemiBold (600) | Alta legibilidade em tamanhos pequenos |
| Números, fichas, badges de atalho | **JetBrains Mono** | Medium (500) / Bold (700) | Números tabulares, ótimo para valores que mudam (evita "jitter" de largura) |

```python
import pygame
pygame.font.init()

FONT_DISPLAY = pygame.font.Font("assets/fonts/SpaceGrotesk-Bold.ttf", 64)
FONT_H2       = pygame.font.Font("assets/fonts/SpaceGrotesk-Bold.ttf", 32)
FONT_BODY     = pygame.font.Font("assets/fonts/Inter-SemiBold.ttf", 20)
FONT_BODY_SM  = pygame.font.Font("assets/fonts/Inter-Medium.ttf", 16)
FONT_MONO     = pygame.font.Font("assets/fonts/JetBrainsMono-Bold.ttf", 22)
FONT_MONO_SM  = pygame.font.Font("assets/fonts/JetBrainsMono-Medium.ttf", 14)
```

---

## 3. Dimensões e Proporções Base (referência 1920x1080)

### Cartas
| Elemento | Largura x Altura | border_radius | Borda |
|---|---|---|---|
| Carta comunitária (mesa) | 96 x 134 px | 10 px | 3 px preto `#1B1B1B` |
| Carta do jogador (mão, destaque) | 148 x 207 px | 14 px | 4 px preto |
| Carta de bot (virada, minimal) | 60 x 84 px | 8 px | 2 px preto |
| Verso da carta (back) | mesma medida da carta | igual | igual, preenchimento sólido `#4C86F0` com padrão geométrico simples |

Proporção usada: ~1:1.4 (padrão poker/bridge).

### Layout geral
| Elemento | Valor |
|---|---|
| Margem externa segura (safe area) | 48 px |
| Gutter entre painéis/cards | 24 px |
| Gutter pequeno (entre botões) | 12 px |
| `border_radius` padrão de painéis grandes (dashboard cards) | 24 px |
| `border_radius` de botões | 14 px |
| `border_radius` de badges/pills (atalhos de teclado, status) | 999 px (pill total) |
| Espessura de borda padrão (cards, painéis) | 3 px |
| Espessura de borda em elementos grandes (mesa) | 5 px |
| Offset da sombra sólida (padrão) | (6, 6) px |
| Offset da sombra sólida (botões, elementos pequenos) | (4, 4) px |
| Offset da sombra ao "pressionar" (hover/active) | (2, 2) px — simula o botão "afundando" |

### Mesa de jogo
| Elemento | Medida |
|---|---|
| Painel da mesa (superfície feltro) | 1500 x 620 px, centralizado horizontalmente, `border_radius` 40 px, borda 5 px |
| Área central do pote (badge) | 180 x 64 px, pill (`border_radius` 32), fundo `#FFC93C`, borda 3px preto |
| Cartas comunitárias | 5 slots, centralizados, gap 16 px entre elas |
| Avatar do bot | círculo 72 px diâmetro, borda 3 px |
| Card de bot (nome + fichas + status) | 220 x 100 px, `border_radius` 18 px |
| Painel de ação do jogador | largura 620 px, altura 96 px, `border_radius` 24 px |
| Botão de ação (Fold/Call/Raise) | 180 x 72 px, `border_radius` 14 px |
| HUD lateral de histórico | 320 px largura, altura livre (até 100% - margens), `border_radius` 24 px |

---

## 4. Instruções de Renderização em Pygame

### 4.1 Retângulo com borda arredondada + borda contornada
`pygame.draw.rect` já suporta `border_radius` nativamente (Pygame ≥ 2.0). Para o efeito neobrutalista (preenchimento + contorno grosso), desenhe duas vezes: uma vez o preenchimento, depois só o contorno (`width=N`) por cima, ambos com o mesmo `border_radius`.

```python
def draw_neobrutal_rect(surface, rect, fill_color, border_color=(27, 27, 27),
                         border_width=3, radius=16):
    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)
```

### 4.2 Sombra sólida deslocada (a assinatura do neobrutalismo)
Nunca usar blur (evitar filtros gaussianos custosos). A sombra é apenas uma cópia do retângulo, cor sólida escura, desenhada primeiro e deslocada.

```python
def draw_neobrutal_card(surface, rect, fill_color, border_color=(27, 27, 27),
                         border_width=3, radius=16, shadow_offset=(6, 6),
                         shadow_color=(27, 27, 27)):
    shadow_rect = rect.move(*shadow_offset)
    pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=radius)
    draw_neobrutal_rect(surface, rect, fill_color, border_color, border_width, radius)
```

Para o estado "pressionado" de um botão, reduza `shadow_offset` para `(2, 2)` e desloque o próprio `rect` do botão em `+2, +2` no momento do clique — simula o botão "afundando" na sombra.

### 4.3 Superfícies com transparência (`SRCALPHA`)
Usar para overlays (modais, fade escurecido no menu de configurações) e para o preenchimento do "pill" do pote quando sobreposto a elementos com movimento (fichas animadas):

```python
overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 140))  # overlay 55% preto
surface.blit(overlay, (0, 0))
```

### 4.4 Badges de atalho de teclado (`[Enter]`, `[Esc]`, `[F]`, `[C]`, `[R]`)
Pill pequeno com fundo escuro sólido e texto mono claro — reutilizar `draw_neobrutal_rect` com:
- `radius = altura/2` (pill total)
- `border_width = 2`
- `fill_color = (27, 27, 27)`
- texto em `FONT_MONO_SM`, cor `#F2EFE7`

### 4.5 Avatares de bot (círculo)
```python
def draw_avatar(surface, center, radius, fill_color, border_color=(27,27,27), border_width=3):
    pygame.draw.circle(surface, (27,27,27), (center[0]+4, center[1]+4), radius)  # sombra
    pygame.draw.circle(surface, fill_color, center, radius)
    pygame.draw.circle(surface, border_color, center, radius, width=border_width)
```

### 4.6 Status do bot (Thinking / Call / Fold)
Pill colorido acima/abaixo do card do bot, cor por estado:
- Pensando → `#4C86F0` (azul) com texto branco
- Call/Check → `#3DD9A4` (menta) com texto `#1B1B1B`
- Raise → `#FFC93C` (amarelo) com texto `#1B1B1B`
- Fold → `#D8D4C8` (cinza), texto `#5C5850`, card do bot com opacidade reduzida (~60%, aplicar via `Surface` com `SRCALPHA` e `set_alpha(153)`)

### 4.7 Organização recomendada de camadas (z-order) na mesa
1. Fundo (`#F2EFE7`)
2. Painel do feltro (mesa) com sombra
3. Cards de bots + avatares
4. Cartas comunitárias + badge do pote
5. Painel de ação do jogador + cartas da mão (sempre por cima, maior escala)
6. HUD/histórico (painel lateral fixo)
7. Overlays/modais (por último, com `SRCALPHA`)

---

## 5. Checklist de Consistência
- [ ] Toda sombra é sólida, opaca, sem blur.
- [ ] Toda borda usa a mesma cor de contorno (`#1B1B1B`) em toda a UI — é o que unifica o estilo.
- [ ] `border_radius` cresce com o tamanho do elemento (badges pequenos = pill total; painéis grandes = 24–40 px).
- [ ] Números de fichas sempre em fonte mono (evita saltos de layout ao atualizar valores).
- [ ] Paleta de acento usada com moderação: amarelo = dinheiro/pote, azul = info/call, menta = sucesso/raise, coral = perigo/fold.
