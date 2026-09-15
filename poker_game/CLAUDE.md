# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python + Pygame desktop card game ("Solo vs Bots") with two playable modes — Texas Hold'em and Pif Paf — sharing one tournament/elimination structure and one visual style ("Neobrutalismo Suave / Dashboard Analítico") drawn entirely with `pygame.draw` (no external card images). Docs are in Portuguese; match that when editing them.

## Commands

```bash
pip install pygame
python main.py
```

There is no requirements.txt, test suite, linter, or build config in this repo — `pygame` is the only dependency. There are no automated tests; verify gameplay changes by running the game and playing through the affected flow (or via `Agent`/manual play), not by adding a test framework.

Build a Windows executable (must be run on Windows, no cross-compile):
```bash
pip install pygame pyinstaller
pyinstaller --onefile --windowed --name "PixelPoker" main.py
```

## Architecture

**Screen state machine.** `main.py`'s `App` holds `self.tela_atual` (current screen object) and swaps it via `ir_para_*` methods. Every screen implements `atualizar(dt)`, `desenhar(tela)`, `tratar_evento(evento)`. The main loop (`App.executar`) just delegates to whichever screen is current — new screens plug in by following this same trio of methods and getting a `ir_para_*` navigation method on `App`.

**Two parallel game engines, one shared shell.** Each mode has its own self-contained logic/AI/screen trio that never imports from the other's:
- Hold'em: `game_logic.py` (`Player`, `BettingRound`, `Table`) + `hand_evaluator.py` + `bot_ai.py` + `table_screen.py`
- Pif Paf: `pifpaf_logic.py` (`PifPafPlayer`, `PifPafTable`) + `pifpaf_bot_ai.py` + `pifpaf_screen.py`

Both share `deck.py` (cards), `ui_theme.py` (all drawing primitives — panels, buttons, badges, cards), and `settings.py` (in-memory session settings, not persisted to disk).

**Hold'em engine is a pure state machine.** `Table` orchestrates one hand (blinds → preflop → flop → turn → river → showdown) and doesn't know or care whether an action came from mouse input, `bot_ai.decidir_acao_bot`, or a network packet from `rede/anfitriao.py` (per `MULTIPLAYER_PLANO.md`) — every action flows through `rodada_atual.aplicar_acao(jogador, acao, valor)`. `Player.tipo` (`bot`/`humano_local`/`humano_remoto`) records the origin for whoever draws/decides the next action; `Table`/`BettingRound` never read it. Keep this decoupling when touching `game_logic.py`: don't let it reach into UI or input state.

**Hand evaluation via tuples.** `hand_evaluator.py` scores a 5-card hand as a tuple `(categoria, desempates...)` where larger tuples win — this makes comparison, tie-breaking, and split-pot detection just Python tuple comparison (`>`, `<`, `==`). Preserve this shape if you extend it (e.g. new categories or kicker rules).

**Side pots.** `calcular_potes()` in `game_logic.py` computes main pot + side pots from each player's `total_apostado_mao`, supporting partial all-ins, then merges consecutive pots with identical eligible-player sets. Split-pot remainder chips go to whoever is closest to the dealer.

**Bot AI is per-mode and stateless-ish.** `bot_ai.py` (Hold'em) assigns each bot a fixed risk profile per match (tight/balanced/aggressive/tricky) and decides using hand strength, draws, pot odds, bet pressure, table position, and active opponent count. `pifpaf_bot_ai.py` (Pif Paf) is a single heuristic (no per-match profiles): only draws from discard when it actually reduces loose-card points, always knocks (`bate`) when possible, never discards the wild card.

**Deprecated code kept for reference.** `ui_pixelart.py` (old pixel-art rendering) and `assets/assets.png` are unused by the current game (replaced by `ui_theme.py`'s vector style) but intentionally kept — see `GDD.md` §3.2 for the rationale (possible future reintroduction as an alternate deck skin). Don't delete them without checking with the user; don't wire new features into them either.

**`design/` directory.** Contains standalone HTML mockups + technical guides for visual styles that were evaluated before implementation. Only `design/01_neobrutalismo_suave/` was actually implemented in Pygame; `03_casino_minimalista/` and `05_cozy_flat/` are validated-but-unbuilt alternatives. These are design references, not part of the running app.

## Key docs

- `README.md` — setup, project layout, implemented rules summary, PyInstaller packaging.
- `GDD.md` — living game design document (modes, economy, planned features).
- `PIF_PAF_GUIA.md` — Pif Paf rules research and this project's specific design decisions/deviations (e.g. "a louca" rule is explicitly out of scope; "Mão Fechada" and the "knock by discarding the leftover card" fix are documented here with rationale).
- `MELHORIAS.md` — project backlog/changelog of ideas and completed work, organized by theme.
- `MULTIPLAYER_PLANO.md` — architecture plan for local-network multiplayer via a host-authoritative model built on the existing `Table` class (implemented for Hold'em in the `rede/` package + `multiplayer_screens.py` + `mesa_remota_screen.py`; Pif Paf multiplayer is still out of scope). Read this before touching any networking code — it specifies the protocol, threading model, and which files/methods it touches.

When making non-trivial gameplay or architecture decisions, these docs are the source of truth for prior reasoning — check them before re-deciding something already settled, and update the relevant doc (especially `MELHORIAS.md`/`GDD.md`) when you implement backlog items or change scope.
