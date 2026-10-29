# Pandora Warlock (Godot 4)

A deck, board, chess, lore game with health and battle point systems.
Guard the lighthouse through 8 rounds against the Shades.

## Play it

1. Open **Godot Engine 4** (4.2 or newer).
2. Import this folder as a project (or open `project.godot`).
3. Press **Play** (F5). Portrait, touch-friendly — works with mouse too.

No Godot on this machine? The project is source-only here on purpose: open it
in Godot on your phone or computer and it runs. Android export (APK) is a
Godot-editor step on your side when you want it.

## How to play

- Tap a card in your hand, then **Deploy here** on an open constellation.
  Deploying costs starlight (shown on each card).
- Tap **Strike** to hit a Shade in that warlock's lane.
- Tap **End round**: Polaris heals its warlock, Shades fight or creep closer,
  a new Shade gathers, you gain +2 starlight and draw a card.
- **Polaris** heals 1 HP at round start. **Orion** strikes at +1 BP.
- A Shade that reaches an unguarded constellation hits the lighthouse for
  its BP. Lighthouse at 0 means the light goes out. Survive 8 rounds to win.
- Rumor says the table hides secrets. The counter under the status line
  keeps count of the ones you've found.

## Files

- `project.godot` — Godot 4 project (portrait 720x1280, GL Compatibility).
- `main.tscn` — the one scene; the script builds the whole UI in code.
- `main.gd` — all game logic: deck, lanes, Shades, rounds, Easter eggs.
- `DESIGN.md` — full rules, egg list (dev note), and the next-updates list.
- `icon.svg` — gold star + lighthouse mark.

## Update as we go

Tell me what to change next — a new constellation, a new card, a new egg,
a rule tweak — and the design doc and build move together.


---
© Crimson Rose LLC, Curtis Ray Dyess 2026-27
