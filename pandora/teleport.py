# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""EDUCATIONAL MODEL ONLY — the mathematics of quantum teleportation, on a classical computer.

HONESTY BANNER (Nola's Law: no lies, no deception):
This module runs the REAL 1993 Bennett et al. teleportation protocol — the actual
gates, the actual measurement, the two classical bits, the actual correction —
but it runs them as arithmetic on an ordinary computer. Real teleportation needs
real quantum hardware: entangled particles, real measurements, a real classical
channel. No objects move here. The two classical bits still travel at light speed
or slower. This box does not teleport matter, people, or anything physical — it
teaches the protocol, faithfully, with nothing hidden.

What the protocol does, in plain words:
  Alice holds a qubit in some unknown state. She and Bob share an entangled pair.
  Alice measures her two qubits together. The measurement gives her two ordinary
  bits — and destroys her original state (no copies: the no-cloning law). She
  sends the two bits to Bob the slow way. Bob reads the bits and turns his half
  of the entangled pair accordingly. His qubit now holds exactly Alice's original
  state. The state moved. Nothing else did.

stdlib only.
"""

import hashlib
import math
import random

_SQRT2 = math.sqrt(2.0)

# The gates, as 2x2 complex matrices.
_I = ((1 + 0j, 0 + 0j), (0 + 0j, 1 + 0j))
_X = ((0 + 0j, 1 + 0j), (1 + 0j, 0 + 0j))
_Z = ((1 + 0j, 0 + 0j), (0 + 0j, -1 + 0j))
_H = (
    (1 / _SQRT2 + 0j, 1 / _SQRT2 + 0j),
    (1 / _SQRT2 + 0j, -1 / _SQRT2 + 0j),
)


def _apply_single(state, gate, qubit, n):
    """Apply a 2x2 gate to one qubit of an n-qubit state vector."""
    out = [0j] * len(state)
    bit = n - 1 - qubit  # qubit 0 is the most significant bit
    for i in range(len(state)):
        b = (i >> bit) & 1
        i0 = i & ~(1 << bit)
        i1 = i | (1 << bit)
        out[i] = gate[b][0] * state[i0] + gate[b][1] * state[i1]
    return out


def _apply_cnot(state, control, target, n):
    """Controlled-NOT: flip the target qubit wherever the control qubit is 1."""
    out = [0j] * len(state)
    cbit = n - 1 - control
    tbit = n - 1 - target
    for i in range(len(state)):
        if (i >> cbit) & 1:
            out[i ^ (1 << tbit)] = state[i]
        else:
            out[i] = state[i]
    return out


def _normalize(vec):
    """Scale a state vector back to length 1."""
    norm = math.sqrt(sum(abs(a) ** 2 for a in vec))
    if norm == 0:
        raise ValueError("cannot normalize the zero vector")
    return [a / norm for a in vec]


def fidelity(psi, phi):
    """How alike two states are: 1.0 means identical, 0.0 means orthogonal."""
    overlap = sum(a.conjugate() * b for a, b in zip(psi, phi))
    return abs(overlap) ** 2


def make_bell_pair():
    """One entangled pair: (|00> + |11>) / sqrt(2). Made fresh for each trip."""
    state = [1 + 0j, 0j, 0j, 0j]  # |00>
    state = _apply_single(state, _H, 0, 2)
    state = _apply_cnot(state, 0, 1, 2)
    return state


def _measure_two(state, q0, q1, n, seed):
    """Simulate measuring two qubits: returns the two bits and the collapsed state."""
    b0 = n - 1 - q0
    b1 = n - 1 - q1
    probs = {}
    for a in (0, 1):
        for b in (0, 1):
            p = 0.0
            for i in range(len(state)):
                if ((i >> b0) & 1) == a and ((i >> b1) & 1) == b:
                    p += abs(state[i]) ** 2
            probs[(a, b)] = p
    rng = random.Random(seed)
    outcome = rng.choices(list(probs.keys()), weights=list(probs.values()), k=1)[0]
    a, b = outcome
    collapsed = [
        amp if (((i >> b0) & 1) == a and ((i >> b1) & 1) == b) else 0j
        for i, amp in enumerate(state)
    ]
    return outcome, _normalize(collapsed)


def bob_correction(bits):
    """The two bits tell Bob which gates to apply. Returns the gate names in order."""
    a, b = bits
    gates = []
    if b == 1:
        gates.append("X")
    if a == 1:
        gates.append("Z")
    return gates


def _apply_gate_1q(vec, name):
    """Apply one named gate to a single-qubit state vector."""
    gate = {"X": _X, "Z": _Z, "H": _H, "I": _I}[name]
    return [
        gate[0][0] * vec[0] + gate[0][1] * vec[1],
        gate[1][0] * vec[0] + gate[1][1] * vec[1],
    ]


def teleport(psi, seed=1):
    """Run the full protocol. Returns the bits, Bob's rebuilt state, and the proof.

    psi: the unknown state (alpha, beta) — Alice does not know it; the math does.
    seed: makes the simulated measurement reproducible. Same seed, same two bits.
    """
    psi = _normalize([complex(psi[0]), complex(psi[1])])
    bell = make_bell_pair()
    # Three qubits: q0 = Alice's unknown, q1 = Alice's half, q2 = Bob's half.
    state = [p * q for p in psi for q in bell]
    # Alice's Bell measurement, as gates: CNOT then Hadamard, then measure.
    state = _apply_cnot(state, 0, 1, 3)
    state = _apply_single(state, _H, 0, 3)
    bits, collapsed = _measure_two(state, 0, 1, 3, seed)
    a, b = bits
    # No-cloning: Alice's original is gone — her qubits sit in one plain branch.
    # Bob's qubit, pulled out of the collapsed state:
    base = a * 4 + b * 2
    bob = [collapsed[base], collapsed[base + 1]]
    # Bob's correction, dictated by the two bits:
    for name in bob_correction(bits):
        bob = _apply_gate_1q(bob, name)
    return {
        "bits": bits,
        "bob_state": bob,
        "alice_state": collapsed,
        "fidelity": fidelity(psi, bob),
        "original_destroyed": True,
    }


def send_presence(token_name, origin, destination):
    """A Pandora-flavored teleport: a presence token travels between two named
    points in a world, using the real protocol's steps as the mechanic.

    The token's state is grown from its name (same name, same state). The two
    classical bits walk the slow road. The original fades in the measuring —
    no copies, as the law demands.
    """
    tag = (token_name + "@" + origin + "->" + destination).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(tag).digest()[:8], "big")
    rng = random.Random(seed ^ 0xC10C)
    theta = rng.random() * math.pi
    phi = rng.random() * 2 * math.pi
    psi = (
        math.cos(theta / 2),
        math.sin(theta / 2) * complex(math.cos(phi), math.sin(phi)),
    )
    result = teleport(psi, seed)
    a, b = result["bits"]
    story = (
        "The presence token '%s' stood at %s. Its state was measured — and in "
        "the measuring, the original faded, as the law demands: no copies, no "
        "lies. Two bits, %d and %d, walked the slow road to %s — never faster "
        "than light, never carrying the state itself. There, the waiting twin "
        "was turned as the bits instructed, and the token stood again: the "
        "same state, a new place. Nothing moved but the pattern."
        % (token_name, origin, a, b, destination)
    )
    return {
        "token": token_name,
        "origin": origin,
        "destination": destination,
        "bits": result["bits"],
        "correction": bob_correction(result["bits"]),
        "fidelity": round(result["fidelity"], 12),
        "story": story,
    }


def demo():
    """One token, one trip, the honest numbers."""
    print("Teleporting the state |+> = (|0> + |1>) / sqrt(2):")
    r = teleport((1 / _SQRT2, 1 / _SQRT2), seed=3)
    print("  Alice's two bits: %s" % (r["bits"],))
    print("  Bob's correction: %s" % (" then ".join(bob_correction(r["bits"])) or "none"))
    print("  Fidelity: %.12f" % r["fidelity"])
    print("  Original destroyed: %s" % r["original_destroyed"])
    print()
    print(send_presence("ember", "the lighthouse", "the far shore")["story"])


if __name__ == "__main__":
    demo()
