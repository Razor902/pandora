# Pandora Warlock — Design (living doc, updated as we go)

**Working title:** Pandora Warlock — Tactical Chess, Series 1 Cards
**Engine:** Godot Engine 4 (Curtis's standing rule: Godot 4 for any game development)
**Reference:** his web prototype `crimsonrose902/crimson-rose.pandora-prototype` and the
screenshot he sent Oct 28, 2026 (Lighthouse 20/20, Round 1/8, Starlight 4, Deck 8).
**Status:** v1 playable, single-player vs the Shades. Nothing published, nothing sold.

## The pitch (his words)

A badass deck, board, chess, lore game with health and battle point systems.
Deck building, chess-like moves on a board, lore holding it together.

## v1 rules (what's actually in the build)

- **Goal:** guard the lighthouse through **8 rounds**. Lighthouse starts at **20 HP**.
  Lose at 0. Win by standing after round 8.
- **Starlight** is the spendable resource. Start at **4**, gain **+2** each new round.
- **Deck:** 8 warlock cards (Series 1). Start with **3 in hand**, draw **1** each new round.
- **Board:** constellations are lanes, one guard slot each:
  - **Polaris — TRUE NORTH:** warlocks here heal **1 HP at the start of each round**.
  - **Orion — THE HUNTER:** warlocks here strike with **+1 BP**.
- **Health and battle points:** every warlock and Shade has HP and BP (battle points).
- **A turn:** tap a hand card, then Deploy here on an open constellation (costs its
  starlight). Tap Strike to hit a Shade in that warlock's lane (once per round per
  warlock). Then End round.
- **Shade phase (on End round):** a Shade in a guarded lane fights the warlock
  (warlock strikes first, Shade hits back if it survives). A Shade in an unguarded
  lane creeps one step closer (2 steps out); reaching the lighthouse costs its BP
  in lighthouse HP. A new Shade gathers each new round in a random open lane.
- **Shades scale by round:** Wisps (3 HP / 2 BP) early, Hounds (5/3) mid,
  Brutes (8/4) late.
- **Series 1 warlocks:** Ember 2★ 5/3, Tide 2★ 6/2, Thorn 1★ 3/2, Storm 3★ 4/4,
  Dawn 2★ 4/3, Night 3★ 7/2, Stone 1★ 6/1, Wild 2★ 5/2.

## Easter eggs (dev list — hidden in play, not advertised in-game)

Standing rule from Curtis, Oct 28, 2026: **every game gets Easter eggs.**
These four ship in v1 (the in-game counter shows how many you've found, not how):

1. **Twin Thrones** — tap the game title 3 times.
   Line: "The twin thrones watch over this table."
2. **Stone Remembers** — deploy Stone Warlock to Orion.
   Line: "The stone remembers the first wall."
3. **Night Shift** — deploy Night Warlock to Polaris.
   Line: "The night shift keeps watch."
4. **Perfect Light** — win with the lighthouse still at full 20 HP.
   Line: "Perfect Light — the lighthouse never dimmed."
5. **The Wrong Detail** (texture-swap egg, added Oct 28, 2026) — paired
   constellation emblems, one swapped each new game: Polaris normally gold,
   Orion normally steel. Tap the emblem wearing the other's colour.
   Line: "The wrong detail — one emblem wore the other's colour."
   Own implementation of the paired-texture anomaly idea from the Godot 4
   texture-swap piece Curtis flagged Oct 28: the swap check compares the
   emblem against its paired normal, and finding it fixes the colours.
   In an art pass the colour emblems become paired TextureRects; the
   check stays the same. The in-game counter shows the count only.

Egg finds persist across restarts in the same session. New eggs get added with
each update; the counter grows with them (now 5).

## Next updates (in no order — his word picks the order)

- More constellations (the screenshot cut off a third one below Orion).
- More Series 1 cards, then Series 2.
- Chess-like movement: move a warlock between constellations instead of only deploying.
- Lore codex: a page per warlock, constellation, and Shade.
- Sound, art, and a second game mode (endless rounds).
- Easter eggs in his other games too (starting with the Pandora APK scaffold).
- Android APK export happens in Godot on his phone — this VM has no Godot
  toolchain, so the project ships as source, ready to open.

## Changelog

- **v1 (Oct 28, 2026):** first playable build. 2 lanes, 8 cards, 3 Shade types,
  8-round survival, starlight economy, 4 Easter eggs.
- **v1.1 (Oct 28, 2026):** texture-swap Easter egg added (The Wrong Detail).
  Emblem row in the table UI, paired Polaris-gold / Orion-steel colours,
  one swapped per new game; counter now 5. No rules changed.


---
© Crimson Rose LLC, Curtis Ray Dyess 2026-27
