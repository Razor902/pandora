# The Giant Pendulum — Keeper of True Tone

**Curtis's image, his words:** a giant pendulum for Pandora's Box, "that keeps track of true tone."

## The swing

A pendulum ten meters long — the giant's arm. Honest physics, no shortcuts:

- Period: **T = 2π√(L/g)** — computed, never hardcoded. At 10 meters on Earth it swings once every **~6.34 seconds**. Slow. Stately. Unhurried.
- Angle: **θ(t) = θ₀·cos(2πt/T)** — full swing right at t=0, full swing left at half period, home again at one period.
- Each completed swing is one **beat**. The beat is the box's rhythm.

## The tone

True tone is **A = 440 Hz** — the tuning standard — and its octaves (220, 440, 880...). The tracker compares any measured pitch against the nearest true tone:

- Drift is measured in **cents**: 1200·log₂(measured/reference). 100 cents = one semitone. Positive = sharp, negative = flat.
- Within **±5 cents**, a tone is **true**. Beyond that, it is **drifting**.
- Every check goes in the log: time, pitch, drift, verdict. The box knows when its tone wandered — and when it came home.

## How the box uses it

The pendulum is the box's inner metronome and tuning fork: rhythm keeps time, tone keeps truth. Swing the giant, march the tone checks to the beat, and read the log. One true, one sharp, one flat — the demo shows all three.

## Limits

This is the box's inner metronome, not a calibrated instrument. The physics is real (small-angle approximation — fine for gentle swings), but it doesn't measure the room, the air, or anyone's ears. It keeps the box honest with itself; a concert hall would want finer tools.

Run it: `cd ~/workspace/arcade && python3 -m pandora.pendulum`
Test it: `cd ~/workspace/arcade && python3 -m pandora.test_pendulum`

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
