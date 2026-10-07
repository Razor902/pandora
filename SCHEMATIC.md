# Pandora's Box — The Schematic (Unreal Engine Foundation)

> EDUCATIONAL MODEL ONLY. This is a blueprint, not a finished build. It maps
> the box's systems onto Unreal Engine as the chosen foundation. The Python
> modules in this directory are the logic prototypes; wiring them into Unreal
> is the roadmap, not a claim of a finished engine build.

**Curtis's order (2026-10-07):** "Incorporate the unreal engine into my
Pandora schematics." So the schematic stands on three layers, and Unreal
Engine is the ground floor — the skeleton everything hangs on.

## Layer 0 — The Foundation: Unreal Engine

Unreal is the engine room. It gives the box, in plain words:

- **Rendering** — what the citizen sees: light, shadow, color, the world itself.
- **Physics** — how things move and collide: weight, swing, fall.
- **Audio** — what the citizen hears: the drone, the tone, the thunder.
- **Input** — how the citizen touches the world: hands, controllers, motion.
- **The world editor** — where the world gets built: the workshop floor.

Nothing in the upper layers invents its own physics or its own sky. They all
stand on this floor.

## Layer 1 — The Box's Systems

Each system is built and tested as a Python module today; each has its home
waiting in Unreal tomorrow.

| System (module) | What it is, plainly | Its Unreal home |
|---|---|---|
| **The giant pendulum** (`pendulum.py`) — 10-meter arm, ~6.34s beat, keeper of true tone (A = 440 Hz, ±5 cents) | The box's inner metronome and tuning fork: rhythm keeps time, tone keeps truth | Physics: the swing as a constrained physics body. Audio: the tone tracker on the audio engine (MetaSounds), the 440 Hz reference as the master tuning |
| **The inside weather** (`weather.py`) — the box borrows the citizen's sky: area, timezone, country; 14 conditions → the box's weather words; dawn/day/dusk/night from the local hour | The world breathes with the outside | Sky/Atmosphere: Unreal's sky, volumetric clouds, and directional light driven by the borrowed weather; time-of-day bound to the citizen's timezone |
| **The treasure-map bridge** (`pandora_x.py`) — `hide()` layers payloads, `reveal()` decodes through PythonX's triage gate; only opens when the box reads SAFE | X marks the spot — maps unfold in layers | World streaming: each payload layer as a streamed level/world partition; PythonX decode as an engine module (plugin) feeding the stream |
| **The entry threshold** (`threshold.py`) — three gates: proof-of-self, the mandala shown (1 mandala to the treasury), the box reading SAFE | The door and its three locks | Game framework: proof-of-self as player authentication, the mandala as an inventory/currency check, SAFE as the game-state gate — login flow, Unreal style |
| **The mandala treasury** (mandala-economy) — fees flow to `pandora-treasury`; chain, vault, economy, flywheel | The box's economy | Save/economy hooks: the on-chain ledger mirrored in game state; the treasury as the persistent account |
| **Guardrails + biometric breaker** (`guardrails.py`, `biometrics.py`) — 18+ gate, level caps, play-time budget, heart-rate/motion trip, the kill switch | The safety contract, enforced by the machine | A safety subsystem above game logic: the trip as an engine-level override — pause and wind-down that no game system can veto. Fail-secure, never fail-open |

## Layer 2 — The Citizen's Experience

What stepping into the box feels like, when the layers work as one:

> You prove yourself, show your mandala, and the box reads SAFE — the three
> gates open. You step in at dusk, because it is dusk where you stand, and a
> soft rain is falling inside, same as over your county. Somewhere below the
> world you feel the pendulum's beat — slow, stately, six seconds a swing —
> and every tone in the box is true to it. A treasure map unfolds around you
> in layers, X marking the spot. The box watches your heart the whole time,
> and if your body says too much, it winds down gentle and lets you go.

The citizen never sees the layers. They only feel the world holding together.

## The roadmap, honestly

1. **Today:** the logic lives in Python — every system modeled, tested, and
   documented in this directory.
2. **Next:** each module's contract (inputs, outputs, plain-words behavior)
   becomes the spec for its Unreal counterpart.
3. **Then:** the Unreal project stands up — Layer 0 first, then each Layer-1
   system wired into its Unreal home, one at a time, tested as it lands.
4. **Always:** the safety contract rides along. The guardrails and the
   breaker are not features to add later; they are the walls the rest gets
   built inside.

## Files

- `SCHEMATIC.md` — this file: the three layers, the Unreal mapping, the roadmap.
- `assets/pandora-schematic-unreal.png` — the visual: three layers, Unreal at the base, watermarked.
- `DESIGN.md` — the product design (points here for architecture).
- `OPERATE.md` — operating the box.

© 2026 Curtis Ray Dyess · Crimson Rose LLC
