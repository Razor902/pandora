# The Watchdog — the box watching itself

© 2026 Curtis Ray Dyess · Crimson Rose LLC

EDUCATIONAL MODEL ONLY. Not a medical device. No diagnosis, no treatment,
no advice of any kind. Never use on real patients.

## What it is

A watchdog is the box watching itself. Every subsystem reports in with a
heartbeat — guardrails, biometrics, the pendulum, the weather, the
treasure bridge, the threshold — and if any heartbeat goes stale, the
watchdog raises the alarm and fails safe.

Curtis's order: "Incorporate Watchdog into my system."
His philosophy, running as code: safety first, silence reads as danger.

## What it watches

| Subsystem | Why it must keep beating |
|---|---|
| guardrails | the leash — if the leash goes quiet, nothing may run |
| biometrics | the cuff — a lost pulse is already a trip |
| pendulum | the true tone — the box's inner metronome |
| weather | the borrowed sky — stale sky is a lie |
| treasure-bridge | the maps — a stuck bridge strands the seeker |
| threshold | the three gates — a gate that can't answer is a gate left open |

Each subsystem registers with its own patience (`max_silence`): the cuff
reports fast (seconds), the weather may take minutes. The watchdog does
not treat them all alike — it knows what each one owes.

## The fail-secure rule

Same as the cuff: **silence reads as danger.** A subsystem quiet longer
than its limit is sick, and the sick action fires:

1. The watchdog calls `wind_down(reason=...)` on the guardrails —
   INTO them, never around them. The box saves, plays its farewell
   beat, and goes quiet.
2. The alarm fires once per newly-sick subsystem — no alarm spam.
3. If the subsystem recovers and reports in again, the sick flag
   clears. Recovery is real. So is relapse: go quiet again and the
   alarm fires again.

## Honest limits

- It is a **software supervisor**, not a hardware watchdog timer. It
  watches from inside the same program, so it cannot catch a total
  freeze of the host machine. It is the conscience on duty, not the
  power cord.
- It never ignores a stale heartbeat — but it can only act on what
  the program can still do. Fail-secure, never fail-open.
- The audit log records every registration, heartbeat, sickness, and
  recovery — the cheapest insurance is a written record.

## Files

- `watchdog.py` — the Watchdog class + demo
- `test_watchdog.py` — 11 tests, all passing
