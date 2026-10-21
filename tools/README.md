# tools — Editor visual de layout

Ferramenta de desenvolvimento para ajustar, sem programar, o tamanho das
cartas e peças, os espaçamentos e botões das mesas, as cores do tema, a escala
da fonte, a borda e a sombra, as fichas iniciais e o tempo de jogada dos bots.
Tudo o que ela edita fica em arquivos JSON em `config/`; ela não altera código
do jogo.

> `tools/` não é importado por `main.py` e **não vai no `.exe`**. O botão
> "Editor de layout" dos Ajustes só aparece quando o jogo roda pelo código-fonte.

## Como abrir

```bash
python tools/editor_visual.py
```

ou pelo botão **"Editor de layout"** na tela de Ajustes do jogo (abre o editor
como um processo separado). Rode a partir da pasta do projeto.

## Arquivos

| Arquivo | Papel |
|---|---|
| `editor_visual.py` | A janela do editor: abas, controles, vistas ITEM e MESA COMPLETA, presets, salvar |
| `editor_widgets.py` | Widgets do editor: campo numérico e hexadecimal, botão `-`/`+` com repetição, slider de cor, caixa de marcar |
| `editor_previas.py` | Dicionário `PREVIAS`: para cada chave do layout, a prévia em tamanho real que a mostra |
| `editor_mesa.py` | Vista MESA COMPLETA: monta uma partida simulada com as telas reais do jogo e detecta problemas de layout |

## Como usar

### Painel da esquerda: as variáveis
Abas **Hold'em**, **Pif Paf**, **Dominó**, **Geral** e **Cores** (`1`-`5` ou
`Tab` trocam). Cada item tem:

- `-` / `+`: ajusta pelo passo do item. **Shift** usa um passo 5 vezes maior;
  segurar o botão repete.
- Um **campo** onde se digita o número (Enter confirma, Esc cancela). A roda do
  mouse sobre o número também ajusta.
- **PADRÃO**: volta ao valor original.
- Um `*` marca o que foi alterado e ainda não foi salvo (por item e por aba).
- "Manter proporção" (tecla `P`, só cartas e peças) faz largura e altura andarem juntas.
- `Delete`/`Backspace` restauram o item selecionado ao padrão.

A aba **Cores** mostra cada cor com amostra e código hexadecimal (`#E6A92E`,
digitável). A cor selecionada ganha sliders R/G/B e o contraste com o texto
(aviso em vermelho abaixo de 4,5:1). `←`/`→` e a roda clareiam e escurecem.

> Os botões escolhem texto claro ou escuro sozinhos pelo contraste. Selos com
> cor de texto fixada no código não acompanham: confira na MESA COMPLETA.

A interface do editor usa sempre o tema padrão; só as prévias usam o que você
está editando, para uma paleta ruim não deixar o próprio editor ilegível.

### Painel da direita: duas vistas (tecla `M` alterna)
- **ITEM:** o trecho da mesa afetado pelo item selecionado, em tamanho real e
  desenhado com o mesmo código do jogo. Dá para trocar o baralho (`B`, com Shift volta) e
  virar as cartas (`V`).
- **MESA COMPLETA:** a tela real do jogo numa partida simulada contra bots,
  congelada numa **cena** (ex.: "sua vez no flop", "raise aberto", "sua vez no
  pré-flop, com aposta", "sua vez: comprar/descartar", "mesa em cruz", "sem
  jogada"). A tecla `C` (com Shift, volta) troca a cena. Dá para escolher o número de jogadores e o tamanho da janela
  (1280x800, 1024x768, 1366x768, 1600x900, 1920x1080). Clique na mesa (ou `F`)
  para ampliar; `F`/`Esc`/clique fecham.
  - O que **sai da tela** ou **se sobrepõe** fica contornado em vermelho e
    listado embaixo; o item selecionado fica em amarelo. O número de problemas
    aparece na aba até enquanto você edita na vista ITEM.
  - Alertas: fora da tela; sobreposição de carta/peça/botão; carta, peça ou
    botão parcialmente dentro de um painel; texto de botão sob o seu selo de
    atalho; selo sobre um painel (a não ser que esteja inteiro dentro dele ou
    preso à borda, como SB/BB) e sobre botão, carta ou peça. Painéis desenhados
    depois do primeiro botão (modais como o de raise e o de resultado) só geram
    um aviso "info" sobre o que cobrem.

### Salvar e recarregar
- **Salvar** (`Ctrl+S`) grava `config/layout.json` só com o que difere do
  padrão. Um jogo aberto percebe o arquivo novo em até 1 segundo e recarrega
  sozinho; **F5** no jogo força a recarga.
- **Descartar alterações**, **Tudo ao padrão** e **Presets** estão no rodapé. `Esc` pede para sair (com opção de salvar).
- Teclado: `↑`/`↓` escolhem o item, `←`/`→` ajustam.

### Presets
Conjuntos prontos de ajustes (botão no rodapé). Vêm com o jogo o **compacto**
(janelas pequenas e notebooks, zero alertas em todas as combinações) e o
**grande** (telas de 1600x900 ou mais), em `config/presets_padrao/`. Você pode
salvar os seus com um nome em `config/presets/` (fora do git). Aplicar um
preset troca todos os valores; falta **Salvar** para valer no jogo. Para
exportar ou importar, copie o `.json` de/para essa pasta (o botão "Abrir pasta"
abre ela).

## Onde ficam os dados
- `config/layout_padrao.json`: valores padrão, versionados. Cada item tem
  `valor`, `min`, `max`, `passo` e `rotulo`.
- `config/layout.json`: seus ajustes (só o que mudou), fora do git. Um arquivo
  ausente, corrompido ou com valor de formato errado não quebra nada: o item
  afetado volta ao padrão, e valores fora da faixa são limitados.
- Quem lê e grava tudo isso é `core/layout.py`; o editor usa `layout.definir()`
  e `layout.salvar()`.

## Para quem mexe no código do jogo

- **Nova variável de tamanho:** crie a chave em `config/layout_padrao.json`
  (não uma constante nova na tela) **e** uma entrada em `PREVIAS`
  (`editor_previas.py`). Sem ela o editor levanta `KeyError`.
- **Mudou a geometria de uma tela** que tem prévia? Atualize a prévia
  correspondente, que reimplementa essa geometria com as funções de desenho do
  jogo.
- **Mesa completa:** `editor_mesa.py` monta a partida por
  `main.App.iniciar_partida*` sobre um App falso (por isso o editor nunca mexe
  na carteira real do Hold'em) e roda a partida com o "Você" jogando como bot
  até a cena pedida (`CENAS`). Troca temporariamente
  `pygame.display.get_surface`, `pygame.mouse.get_pos` e as funções de desenho
  que cada tela importa por nome (`desenhar_carta`, `desenhar_botao`,
  `desenhar_peca`, `desenhar_painel`, `desenhar_kbd`, `desenhar_badge`...) para
  registrar o retângulo de cada elemento. Consequências: desenhe elementos novos
  da mesa por essas funções importadas no módulo da tela, ou o detector não os
  vê; e se renomear campos de estado usados pelos predicados das `CENAS`
  (`table.rodada_atual`, `mesa.pode_comprar()`, `fase_mao`, `resultado_mao`,
  `_comecar_proxima_mao_ou_finalizar`...), atualize-os lá. Um estado que nunca
  aparece numa cena não é verificado.
- **Meta de qualidade:** com os valores padrão, o detector deve acusar **zero
  problemas** em todo modo × número de jogadores × janela × cena. Rode a vista
  MESA COMPLETA depois de mexer em ângulos ou deslocamentos de assento.
- Os botões das telas de mesa são dimensionados em `_dimensionar_botoes()`,
  chamada no início de cada `desenhar()`, para que mudanças de layout valham ao
  vivo.

## Histórico
O plano de construção do editor (fases 0 a 5) está em
`../.Viana/plano-editor-visual-poker-game.md`.

- **Fases 0 e 1:** `core/layout.py` e `config/layout_padrao.json`; as seis
  telas de mesa passaram a ler os tamanhos de lá.
- **Fase 2:** o editor com `-`/`+`, campo numérico, "padrão" e prévia ao vivo.
- **Fase 3:** a vista MESA COMPLETA com alertas de sobreposição.
- **Fase 4:** aba de cores, escala de fonte, borda/sombra, fichas iniciais e
  tempo dos bots.
- **Fase 5:** recarga do jogo sem reiniciar, presets nomeados e exportar/importar.

Pendências (ver `lista_tarefas.md`): testar com mouse e teclado reais, arrastar
para redimensionar direto na prévia, e integrar o editor como tela dentro do
jogo (hoje é um processo separado).
