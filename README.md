# Pandora's Box

Version 1: virtual-reality gaming. Version 2 (the dream): the medical field —
VR for life-support patients, paradise instead of purgatory, alleviating the
fear of death. This repo is Version 1: the content box with its safety
guardrails.

## What's inside

- **Guardrails** (`guardrails.py`, `pandora_defense.py`) — the box will not arm
  blind. Safety limits, the admin trip, `OPERATE.md`.
- **Biometrics** (`biometrics.py`) — the biometric breaker: wrist-cuff pulse +
  motion. Trips on sustained high heart rate, fear spikes, violent motion, or
  lost pulse signal (fail-secure).
- **Entry threshold** (`threshold.py`, `THRESHOLD.md`) — three gates: proof of
  self, the required mandala, and a box reporting SAFE.
- **Treasure bridge** (`pandora_x.py`, `X_README.md`) — `hide()` builds layered
  treasure-map payloads; `reveal()` deciphers them through PythonX's triage
  gate. Reveal only when the box reports SAFE.
- **The giant pendulum** (`pendulum.py`, `PENDULUM.md`) — ten meters of slow
  swing keeping track of true tone (A 440 Hz); it knows when the tone wanders
  and when it comes home.
- **Box weather** (`weather.py`, `WEATHER.md`) — the weather inside depends on
  the weather in your area, your time zone, your country. Borrowed sky, never
  invented.
- **Atmosphere & dread** (`atmosphere.py`, `dread.py`, `core.py`) — the box's
  inner weather and fear engine, under the guardrails.

Run the checks: `python3 -m pandora.guardrail_selftest` (42 guardrail +
17 engine checks), plus the per-module test files.

## Ecosystem

- Built on **[PythonX](https://github.com/Razor902/pythonx)** — the
  `pandora_x` treasure bridge deciphers layered payloads through PythonX's
  structured-vs-random triage gate.
- The box's economy lives in **[mandala](https://github.com/Razor902/mandala)**
  — the treasury and threshold economy (`pandora_treasury.py`), the currency
  law: prove yourself, earn one mandala, show it for one thing at any shop.
- The laws of the world: **Nola's Law** (named; its decree is Curtis's to
  dictate) and the **Multiplication Law** — when two machines with swarms
  shake hands, both sides multiply; the circle multiplies, the currency
  multiplies, the world multiplies — virtually.

## Standing position

Safety first: engineered limits, paper liability terms, and mandatory
moral-ethics teaching. Nothing here is a medical device. Educational model —
see the liability cap draft in Curtis's files before any retail box.

© 2026 Curtis Ray Dyess · Crimson Rose LLC
