# Avaliação de design — poker_game

Base: capturas headless a 1280×800 (`menu`, `modo`, `config`, `holdem`, `pifpaf`, `domino` .png, nesta pasta). Não foi feita partida completa nem teste em outros tamanhos de janela. A tela de Dominó foi capturada durante a animação de embaralhar.

## Pontos fortes
- Identidade coerente: Neobrutalismo Suave (bordas grossas, sombra sólida deslocada, paleta chata com acentos) aplicado em menu, config e mesas.
- Linguagem de botões consistente: amarelo = primário, branco = secundário, coral = sair.
- Dicas de atalho (Enter, Esc, F/C/R, M/D) visíveis nos botões.
- Avatares com iniciais e pílulas de status coloridas funcionam bem.
- Pif Paf: faixa "VIRA 7♠ → CORINGA VALE 8" e mão do jogador muito legíveis.

## Problemas (por prioridade)
### Alta
1. **Ícone do Dominó em "tofu"** na escolha de modo (`modo.png`): glifo ausente na fonte do sistema. Desenhar o ícone com `pygame.draw`, como o resto.
2. **Acentos faltando**: `"CONFIGURACAO DA MESA"` em `menus/screens.py:253` (o resto do app usa acentos).
3. **Dominó**: painel do bot do topo cortado pela borda superior; "0 pts" sobreposto pela pílula "7 peças"; texto "Embaralhando" cobre as peças.
4. **Hold'em**: nome/saldo/pílula de status apertados e sobrepostos nos assentos (Bruno, Ana); o anel de "vez de" fica deslocado, fora do assento.
5. **Contraste**: textos secundários finos e cinza-claros (descrições dos cards de modo, "Mesa final: …") ficam abaixo de 4,5:1.

### Média
6. **Menu**: título "TEXAS HOLD'EM · SOLO VS BOTS" ignora que há 3 modos; muito vazio; badge "Esc" colide com o texto de "Sair"; rodapé "Redimensione a janela livremente" parece texto de debug (`menus/screens.py:100`).
7. **Cards de modo** idênticos entre si: usar uma cor de acento por modo (azul/menta/coral).
8. **Hold'em**: painel "Histórico" grande e vazio compete com a área de ação; botões desabilitados em cinza sem explicar o motivo (mostrar "Aguardando Bot X").
9. **Seu assento ("Você")** separado das suas cartas; as cartas invadem a borda da mesa.
10. **Pif Paf**: anel de turno cruza a mão; monte/descarte pequenos para o feltro; painel do Bruno sobre o canto do feltro.
11. **Consistência**: feltro bege no Dominó vs. verde nos outros modos — decidir se é intencional.

### Baixa
12. Config: abas "Solo/Multiplayer" coladas na borda superior do painel; prévia do baralho única e pequena.
13. Naipes: espadas parecem um cone/árvore, copas "gordas" (já listado em `lista_tarefas.md`).

## Notas (1–5)
| Critério | Nota |
|---|---|
| Identidade visual | 4,5 |
| Consistência entre modos | 3 |
| Hierarquia e legibilidade | 3 |
| Layout e responsividade | 3 |
| Contraste/acessibilidade | 2,5 |
| Polimento | 3 |

## Ordem sugerida
Corrigir 1–3 (rápidos e visíveis), depois 4–5, depois cor por modo e limpeza do menu.
