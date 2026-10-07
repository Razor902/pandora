# The Entry Threshold — What It Takes to Step Into the Box

**Curtis's law (2026-10-07, his words):** "The mandala is a currency used in Pandora. Each citizen that proves their self earns one mandala. That will get them one thing out of any shop — they just have to show it."

## The three gates

A citizen steps into Pandora's Box only when all three gates open:

1. **PROOF-OF-SELF.** The citizen must be registered as proven. The mandala is earned, not given. (The registry here is a demo with fictional citizens — the real registry is Curtis's to build.)
2. **THE MANDALA SHOWN.** The citizen must hold the entry fee: **1 mandala** — one mandala, one step inside, mirroring his one-mandala-one-thing law. The fee moves to the box treasury (`pandora-treasury` on the chain, the same id the mandala-economy treasury module uses — one treasury, one id). Nothing is created or destroyed: citizen −1, treasury +1.
3. **THE BOX IS SAFE.** The box must read SAFE. The threshold only *reads* the safety word — it never touches the defense stack, so the guardrails, the biometric breaker, and the kill switch stand exactly as built. ARMED, TRIPPED, DISARMED, or no box at all: the door stays shut, in plain words.

## Refusals speak plainly

`check_entry()` names every closed gate and why — so a refused citizen knows exactly what to fix. `enter()` runs the gates, moves the fee on-chain, and hands back a receipt; on failure it raises with the plain-words reasons.

## What Curtis still sets

- **The fee.** 1 mandala is ASSUMED from his law — he sets the real price of a step inside.
- **The registry.** Who counts as proven, and how proof is recorded.
- **The box wiring.** Which live box object the threshold reads (anything with a `status_word`).

## Limits

Classroom model: demo citizens, demo mandalas, demo box. Not a production access system.

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
