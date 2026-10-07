# Pandora — pluggable scare platform (DESIGN)

Product: **Pandora's Box** (the physical box, for sale).
Platform: **Pandora** (the software platform the box and the games run on).

Status: design v1, drafted 2026-10-02 at Curtis's order ("design an engine we can
hook up to the game when we need it to be scary, as a package we can plug in
and unplug"). Named by Curtis 2026-10-02: the box for sale is Pandora's Box,
the platform is Pandora. Stands only when Curtis says so.

## The idea in one line

Pandora is the platform — the scare engine, the DLC system, the framework
games plug into. Pandora's Box is the physical product: an actual box you buy,
the full package. The DLC (software-only) is real, but it is not the full
package. The full package is the box.

## Two tiers

**Tier 1 — DLC (software only).** The Python package. Clips onto any game,
unclips clean. Levels 1–2 (atmosphere, dread). Sold/downloadable on its own —
but everyone knows it's not the full package.

**Tier 2 — Pandora's Box (hardware, for sale).** The full package. A physical
box on the desk, wired into the platform. Unlocks everything the DLC has,
plus physical effects no software can fake: the box glows, breathes, shakes,
and its lid cracks open as the dread rises. When the game gets scary, the
room gets scary.

## The box (hardware sketch)

- **Brain:** Raspberry Pi Pico (a few dollars, USB serial, plenty for this) —
  or Pico W if the link goes wireless.
- **Link:** USB serial to the phone/Termux (or Bluetooth on the W). Simple
  text protocol from the game: `DREAD 0.0-1.0`, `STINGER`, `ARM`, `DISARM`.
- **Effects:**
  - Red LED array — the box glows, pulses with the dread value
  - Vibration motor — physical haptics beyond the phone
  - Small speaker/buzzer — low drone, rising with tension
  - Servo lid — the lid cracks open as dread climbs. Pandora's box, opening.
    (And at the bottom of the myth: hope. A small steady light that never
    goes out — his call whether that ships.)
- **Hardware kill switch:** a physical button on the box. Press it, everything
  stops instantly — light, sound, shake. The safety contract you can touch.
- **Power:** USB powered. No batteries to babysit.

## The safety contract (his rule, built into the machine)

Curtis's standing rule — no jump scares in anything built for him — is not
suspended by this engine. It is enforced by it:

- **Default OFF.** The engine does nothing until explicitly armed. A game
  with ScareKit installed but not armed plays exactly like the clean game.
- **Intensity levels, gated:**
  - Level 1 — ATMOSPHERE: unease only. Palette drain, flicker-dim, vignette
    creep, text corruption, low drone. Nothing startles.
  - Level 2 — DREAD: tension events. A presence at the screen edge, pursuit
    cues, heartbeat pacing. Still nothing that pops.
  - Level 3 — STARTLE: jump-scare class effects. Requires explicit per-session
    opt-in (`arm(level=3, consent=True)`). Never the default, never silent.
- **Kill switch:** one call (`disarm()`) or one keypress restores the original
  game instantly. No fade-out theater, just off.
- **The package never arms itself.** Only the game — which means only Curtis
  or his explicit game logic — decides when scary is on.
- When unplugged, zero footprint: no leftover hooks, no modified game code.

## Plug / unplug mechanism (DLC tier)

The engine talks to the game through two hooks the game already has —
`update(dt)` and `render(buf)`. Attaching wraps them; detaching unwraps them.

```python
import scarekit

engine = scarekit.Engine(level=1)   # atmosphere only
engine.attach(game)                 # wraps update/render; game plays unchanged
engine.arm()                        # scary is ON
engine.disarm()                     # scary is OFF, instantly
engine.detach()                     # unwrapped; game is byte-for-byte original

# or, scoped:
with scarekit.armed(game, level=2):
    ...  # dread inside this block only
```

Attach/detach must be provably clean: `detach()` restores the exact original
method objects (verified by identity check in the selftest).

## Effects catalog (terminal-native, Termux-safe)

All effects render through the game's existing text buffer — no new
dependencies, no network, works offline.

**Level 1 — atmosphere:**
- `palette_drain` — colors desaturate toward blood-red and black over seconds
- `flicker_dim` — brief controlled dimming (dim, never full-screen flash)
- `vignette_creep` — screen edges darken as in-game danger rises
- `text_rot` — dialogue and banners glitch/corrupt progressively
- `drone` — low haptic pulse pattern (uses the existing termux-vibrate path)

**Level 2 — dread:**
- `presence` — something wrong at the screen edge; never center, never sudden
- `pursuit_cues` — the game world reacts to being hunted (audio/haptic ticks)
- `heartbeat` — pacing layer synced to in-game tension value 0.0–1.0

**Level 3 — startle (opt-in only):**
- `stinger` — the sudden event, parameterized (visual + haptic + audio)
- Gated behind `consent=True`; logs every firing to a session record

## File layout

> The full architecture — Unreal Engine as the foundation, the box's systems,
> and the citizen's experience — lives in **SCHEMATIC.md** (with the visual
> at `assets/pandora-schematic-unreal.png`). The layout below is the Python
> prototype tier of that schematic.

```
scarekit/
    __init__.py      # Engine, armed(), __version__
    core.py          # attach/detach, arm/disarm, level gating, kill switch
    atmosphere.py    # level-1 effects
    dread.py         # level-2 effects
    startle.py       # level-3 effects (consent-gated)
    selftest.py      # headless tests: clean detach, gating, kill switch
    DESIGN.md        # this file
```

## What it will NOT do

- Never modify the game files on disk. It wraps in memory only.
- Never phone home, never log outside the session record Curtis can read.
- Never escalate its own level. Level is set at arm time, period.
- No effect may exceed its level's contract — a level-1 effect that startles
  is a bug, filed and fixed like the castle3 crash.

## The box learns your fears (added 2026-10-02, Curtis's order)

Pandora's Box watches what works — and tunes itself. The learning loop:

- **Signals (honest, observable):** how fast the kill switch gets hit after an
  effect fires, which effects get re-armed vs left off, session length per
  level, which level he reaches for. The box cannot read minds — it reads
  actions.
- **What learning changes:** WHICH effects the engine deploys within the
  currently armed level, and how hard it leans on each. A fear profile of
  weights per effect.
- **What learning NEVER changes:** the level itself. Learning tunes the what,
  never the how-much. Level 3 still needs his explicit opt-in every session,
  no matter what the profile says. The kill switch still kills everything.
- **The profile lives on the box.** Local only — it never leaves the hardware,
  never uploads, never syncs. Viewable in plain language (`engine.profile()`
  shows what it learned, in words). Wipeable in one command (`engine.forget()`
  — his data, his call, gone instantly).
- **New module:** `memory.py` — the profile store and the weighting logic.
  Builds after the core lands (phase 2).

## Purchase contract (added 2026-10-02, Curtis's order)

- **Rating: M 18+.** Pandora's Box is a mature product — buyers must be 18 or
  older. The scare platform is built for adults.
- **Screen time: 1 hour per day, 3 days per week.** Hard limit, not a
- **Enforced by the box itself** — the platform tracks play time per box; when
  the budget is spent, the session winds down gracefully (game saves, farewell
  beat, then the box goes quiet). No abrupt mid-game kill — the wind-down is
  part of the design, his call on the exact shape.
- **Which 3 days** is set by the buyer at setup (parent's call).
- This is the product's stance in the market: the game box that tells the kid
  to go outside. A selling point, not fine print.
- Planned module: `contract.py` — play-time tracking and enforcement (phase 3,
  after core + memory).

## Open decisions for Curtis

1. **Name — DECIDED 2026-10-02.** Platform: Pandora. Product: Pandora's Box.
2. **Level-3 consent shape.** Per-session flag is proposed; he may want a
   different gate (a physical key combo, a config file, per-game default).
3. **Which game first.** castle3 is the natural host (it already has tension:
   shadows, stealing, screen shake). starship second.
4. **Build order.** Proposed: Pandora platform core + DLC (levels 1–2, no
   consent machinery) first, then the Pandora's Box hardware prototype
   (Pico + LEDs + vibration + servo lid), then the level-3 startle module
   after he rules on the gate.

## Guardrails on the black box (built 2026-10-02, Curtis's order)

"Put guardrails on the black box" — without altering the box's internals.
New module: `guardrails.py` (+ `guardrail_selftest.py`, 27 tests). It wraps
the engine; the engine's own 17 tests still pass unchanged.

- **Content restrictions:** 18+ age gate at setup (local attestation).
  Content cap defaults to 1, raisable by the admin only, never above 2.
  Level 3 does not exist and cannot be enabled. Level 2 needs explicit
  per-session opt-in (`consent=True`) every session.
- **Parental controls:** 1 hour/day, 3 days/week, buyer picks the days at
  setup. Usage tracked in local JSON (`~/.pandora/guardrails.json`, 0600).
  Budget spent → graceful wind-down: game save hook, farewell beat, box
  goes quiet. Weekly reset. `status()` speaks plain language.
- **Admin, Curtis-approved only:** Curtis bakes an owner secret into each
  box at manufacture. An admin comes into existence ONLY via an approval
  code (HMAC of a one-time request token under that secret) that only
  Curtis can mint. No self-provisioning, no default PIN, no backdoor, no
  alternate path. Curtis can revoke the admin; the box locks until he
  approves again. Admin PIN stored PBKDF2-hashed; only the admin changes
  caps, days, usage logs, or factory-resets. 5 bad PINs → 10-minute
  cooldown. Failed attempts logged. The kill switch stays instant for
  everyone, always — no checks, no PIN, no Curtis.

### Hardened (same day, Curtis: "make it better") — 35 tests

- **Tamper-evident state:** the state file carries an HMAC-SHA256 seal made
  with the owner secret. Hand-editing it (e.g. resetting the time budget)
  breaks the seal: the box then refuses to arm, refuses admin changes, and
  refuses new approvals. Only Curtis's factory-reset approval re-seals it.
  Kill switch and wind-down still work — fail-secure, never fail-open.
- **Monotonic play clock:** the budget no longer trusts the game to report
  minutes honestly. Arming starts a monotonic timer (rolling the wall clock
  back can't cheat it); `tick()`/`disarm()` debit real elapsed time, and
  `record_play()` never debits less than the elapsed floor. Double-arming
  is refused.
- **Approval requests expire:** a Curtis approval token lives 24 hours; a
  stale code found later doesn't work.

### The breaker (same day, Curtis: "trips out before it can cause serious
damage") — 42 tests

- **Biometric safety trip** (`biometrics.py`): a heart-rate cuff on the
  wrist plus a motion sensor watch the player while the box is armed. The
  box trips — graceful wind-down, plain-language farewell — when the body
  says too much: heart rate sustained above 150 bpm for 8 seconds, a fear
  spike of 40+ bpm inside 10 seconds, violent motion for 5 seconds, or the
  cuff losing the pulse for 5 seconds. Losing the signal trips the box;
  a cuff that isn't worn reads the same as danger. The box will not arm
  blind — no live cuff reading, no arm. Attaching the trip is always
  allowed; only the admin can detach it. Like a circuit breaker: it trips
  before the wire melts.

© 2026 Curtis Ray Dyess · Crimson Rose LLC
