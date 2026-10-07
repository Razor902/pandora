# Teleport — The Protocol, Taught Honestly

**Curtis's order (2026-10-07):** research quantum teleportation, and put it in Pandora's Box — as an educational model.

## The idea, in plain words

Quantum teleportation moves a **state**, not a thing. Alice holds a qubit in some unknown condition. She and Bob share an entangled pair. Alice measures her two qubits together — the measurement hands her **two ordinary bits** and **destroys her original** (no copies: the no-cloning law). She sends the two bits to Bob the slow way. Bob reads them, turns his half of the pair accordingly, and his qubit now holds exactly Alice's original state. The state moved. Nothing else did — no matter, no energy, nothing faster than light.

## How Pandora's version works

`teleport.py` runs the **real 1993 Bennett protocol mathematics** — Hadamard, CNOT, and Pauli gates as complex matrices, a true Bell pair, Alice's joint measurement, the two classical bits, Bob's correction — on an ordinary computer, in pure Python. Then `send_presence()` wraps it in Pandora's skin: a presence token travels between two named points in a world, the protocol's steps told as a story.

```python
from pandora import teleport
print(teleport.send_presence("ember", "the lighthouse", "the far shore")["story"])
```

## What was borrowed — and what wasn't

Borrowed from the real physics: the protocol itself — the gates, the measurement, the two bits, the correction map, the destruction of the original. The fidelity check proves the math: the rebuilt state matches the original exactly, every time, for every state tried.
Not borrowed: quantum hardware. There are no entangled particles here, no real measurement, no real channel — only arithmetic that follows the same rules. The module says so on its face, in the honesty banner at the top of the file.

## Limits — read these first

- **This is not quantum hardware.** It is the protocol's mathematics on a classical computer. Real teleportation needs real entangled particles and real measurements.
- **Nothing moves.** Not matter, not people, not energy. The only thing that "travels" is a pattern of information, and even that waits on two bits that obey the speed of light.
- **One pair, one trip.** Each teleportation consumes its entangled pair, exactly like the real thing.
- **Why the honesty matters:** Nola's Law — *no lies, no deception* — is Law 1 of Pandora. A module that pretended to be quantum hardware would break it. So the banner stays, permanently.

## Try it

Run `python3 teleport.py` for the demo: one state teleported with its bits, correction, and fidelity printed, plus one presence token's journey in plain words.

---
*Status: GATHERED — until Curtis says it stands.*

© 2026 Curtis Ray Dyess · Crimson Rose LLC
