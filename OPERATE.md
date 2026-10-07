# OPERATE.md — Pandora defense system, plain language

This is the defense stack for Pandora's Box, wired into one runnable box:
`pandora_defense.py`. It guards the scare engine — it doesn't make anything
scarier. Defense layer only.

## The pieces

- **Guardrails** (`guardrails.py`) — the leash. Content caps (18+ age gate,
  level cap 1 or 2, never 3), play-time budget (1 hour/day, 3 days/week,
  buyer picks the days), admin access that only Curtis can approve, a
  tamper-evident state seal, and a monotonic play clock nobody can cheat
  by rolling the wall clock back.
- **The biometric breaker** (`biometrics.py`) — the heart-rate cuff and
  motion sensor. It trips the box before your body gets somewhere
  dangerous. Fail-secure: a lost signal reads as danger, never as "fine."
- **The kill switch** — one call, one button. Instant, for everyone,
  always. No PIN, no checks, no waiting.
- **The engine** (`core.py`) — the scare platform being guarded. It does
  nothing until armed, and arming only happens through the guardrails.

## Start it

From the arcade folder:

```
cd ~/workspace/arcade
python3 -m pandora.pandora_defense --demo spike
```

That runs a safe, fully scripted trip test — fake cuff, fake clock, throwaway
state in /tmp. Nothing real is touched. Five scenarios:

| demo       | what it proves |
|------------|----------------|
| `healthy`  | steady 72 bpm — the box stays ARMED, disarms clean |
| `spike`    | heart jumps 72 → 120 — trips on the fear spike |
| `sustained`| heart holds above 150 — trips on the ceiling |
| `signal`   | cuff loses the pulse — trips fail-secure, won't run blind |
| `motion`   | violent motion 5s — trips on the motion sensor |

Run the shipped test suites any time:

```
python3 -m pandora.pandora_defense --selftest
```

59 tests: 42 guardrail, 17 engine. They must all pass before the box
ships anywhere.

## The real path (a real box, not the demo)

One time, at manufacture — Curtis, on his machine:

```python
from pandora.pandora_defense import PandoraDefense
box = PandoraDefense()                      # state at ~/.pandora/guardrails.json
box.guard.manufacture("<curtis-owner-secret-hex>")
```

Setup — the buyer asks, Curtis approves (the approval code is minted by
Curtis on his own machine with his secret; there is no other path):

```python
token = box.guard.begin_setup(age_attested=True,
                              days=["Mon", "Wed", "Fri"],
                              admin_pin="<buyer-pin>")
# Curtis: code = curtis_approval_code(secret, token, "grant-admin")
box.guard.curtis_approve(token, code)        # READY
```

Every session — cuff first, then arm:

```python
box.attach_biometrics(real_cuff_reader)     # any CuffReader; won't arm blind
box.arm(level=1)                            # level 2 needs consent=True
```

In the game loop, one call per beat:

```python
box.tick()     # debits real time; trips the box the instant the body says too much
```

End of session:

```python
box.disarm()   # calm stop, time debited
box.kill()     # the kill switch — instant, no questions
```

Read the box at a glance:

```python
print(box.status_line())
# [PANDORA] ARMED — level 1. Content level cap: 1 (atmosphere). 60 minutes left today. ...
# [PANDORA] TRIPPED — Your heart spiked 48 beats in under 10 seconds. ...
# [PANDORA] DISARMED — ...
# [PANDORA] SAFE — ...
```

## What each trip reason means

- **"Your heart spiked N beats in under 10 seconds."** A sudden fear jump
  of 40+ bpm inside 10 seconds. The box decided that was too fast and
  went quiet.
- **"Your heart stayed above 150 beats for 8 seconds."** A racing heart
  that wouldn't come down. The ceiling is conservative on purpose — it
  trips long before a doctor would worry.
- **"The cuff lost your pulse."** No reading for 5 seconds — cuff slipped,
  came off, or failed. The box trips rather than run blind. An unworn
  cuff reads the same as danger. There is no "sensor off" mode.
- **"The motion sensor reads violent movement."** Hard thrashing for
  5 seconds straight.

After any trip, that day's play is over — the box won't re-arm until the
next play day. That's not a bug; that's the breaker doing its job.

## The rules that never bend

1. **Never arms blind.** No cuff reader attached → `arm()` refuses, in
   plain language. The only exception is the admin explicitly detaching
   the trip with their PIN — and the box remembers it was the admin's call.
2. **Fail-secure, never fail-open.** Lost signal, tampered state, dead
   cuff — every one of these makes the box *safer*, never looser.
3. **Thresholds are not negotiable.** 150 bpm / 8 s, 40 bpm / 10 s,
   5 s motion, 5 s signal loss. No test, demo, or admin setting weakens
   them. If a test ever contradicts a threshold, the threshold wins and
   the test gets fixed with a note.
4. **Curtis is the only approver.** Admins exist only through his approval
   codes. No self-provisioning, no default PIN, no backdoor.
5. **The kill switch is above everything.** It works tampered or not,
   armed or not, admin or stranger. One press, quiet.

© 2026 Curtis Ray Dyess · Crimson Rose LLC
