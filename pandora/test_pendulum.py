# © 2026 Curtis Ray Dyess · Crimson Rose LLC
#!/usr/bin/env python3
"""Tests for the giant pendulum -- physics honest, tone tracker faithful.

Run:  cd ~/workspace/arcade && python3 -m pandora.test_pendulum
"""

import math
import sys

sys.path.insert(0, __file__.rsplit("/pandora/", 1)[0] + "/..")

from pandora.pendulum import (
    Pendulum, ToneTracker, drift_cents, nearest_true_tone,
    G, GIANT_LENGTH, TRUE_TONE_HZ, TRUE_CENTS,
)

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[ok ] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol


def pitch_refused():
    try:
        drift_cents(0)
    except ValueError:
        return True
    return False


# --- the physics ---
p = Pendulum()  # the giant: 10 meters
expected_T = 2 * math.pi * math.sqrt(GIANT_LENGTH / G)
check("giant arm is 10 m", p.length == 10.0)
check("period computed, ~6.34 s", approx(p.period, expected_T) and 6.3 < p.period < 6.4)
check("angle at t=0 is full amplitude", approx(p.angle(0), p.amplitude))
check("angle at t=T/2 is opposite swing", approx(p.angle(p.period / 2), -p.amplitude))
check("angle at t=T is back home", approx(p.angle(p.period), p.amplitude, tol=1e-6))
check("beats land on period multiples",
      all(approx(b, (i + 1) * p.period) for i, b in enumerate(p.beats(3))))
check("shorter arm swings faster", Pendulum(length=1.0).period < p.period)

# --- the tone math ---
check("440 Hz is true (0 cents)", drift_cents(440.0) == 0.0)
check("445 Hz is sharp ~+19.6 cents", 19.0 < drift_cents(445.0) < 20.5)
check("435 Hz is flat ~-19.8 cents", -20.5 < drift_cents(435.0) < -19.0)
check("880 Hz finds the 880 octave, 0 cents",
      nearest_true_tone(880.0) == (880.0, 0.0))
check("220 Hz finds the 220 octave, 0 cents",
      nearest_true_tone(220.0) == (220.0, 0.0))
check("bad pitch refused", pitch_refused())

# --- the tracker ---
t = ToneTracker()
e1 = t.check(440.0)
e2 = t.check(445.0)
e3 = t.check(435.0)
check("true tone logged as home", e1["verdict"] == "true")
check("sharp tone logged as wandering", e2["verdict"] == "drifting" and e2["drift_cents"] > 0)
check("flat tone logged as wandering", e3["verdict"] == "drifting" and e3["drift_cents"] < 0)
check("log holds all three checks", len(t.log) == 3)
check("wanderings counts the drifters", len(t.wanderings()) == 2)
check("homecomings counts the true", len(t.homecomings()) == 1)
check("boundary: just under 5 cents still true",
      t.check(440.0 * 2 ** (4.9 / 1200))["verdict"] == "true")
check("boundary: 6 cents is drifting",
      t.check(440.0 * 2 ** (6 / 1200))["verdict"] == "drifting")
check("describe speaks plain words", "home" in t.describe(e1) and "wandering" in t.describe(e2))

print()
print(f"{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
