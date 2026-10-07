# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Tests for Pandora's teleport module — the protocol must be honest and exact."""

import math
import random
import unittest

import teleport
from teleport import teleport as run_teleport
from teleport import (
    _apply_cnot,
    _apply_gate_1q,
    _apply_single,
    _H,
    _I,
    _X,
    _Z,
    bob_correction,
    fidelity,
    make_bell_pair,
    send_presence,
)

_SQRT2 = math.sqrt(2.0)


def _matmul(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2))
        for i in range(2)
    )


def _dagger(m):
    return tuple(tuple(m[j][i].conjugate() for j in range(2)) for i in range(2))


def _is_identity(m, tol=1e-12):
    return all(
        abs(m[i][j] - (1 if i == j else 0)) < tol for i in range(2) for j in range(2)
    )


class TestGates(unittest.TestCase):
    def test_gates_are_unitary(self):
        """Every gate must preserve length: U-dagger times U is identity."""
        for gate in (_H, _X, _Z, _I):
            self.assertTrue(_is_identity(_matmul(_dagger(gate), gate)))

    def test_hadamard_makes_superposition(self):
        out = _apply_gate_1q([1 + 0j, 0j], "H")
        self.assertAlmostEqual(abs(out[0]), 1 / _SQRT2)
        self.assertAlmostEqual(abs(out[1]), 1 / _SQRT2)

    def test_cnot_twice_is_identity(self):
        """CNOT is its own undo — applying it twice changes nothing."""
        state = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        once = _apply_cnot(state, 0, 1, 3)
        twice = _apply_cnot(once, 0, 1, 3)
        for a, b in zip(state, twice):
            self.assertAlmostEqual(a, b)


class TestBellPair(unittest.TestCase):
    def test_bell_pair_amplitudes(self):
        bell = make_bell_pair()
        self.assertAlmostEqual(bell[0], 1 / _SQRT2)
        self.assertAlmostEqual(abs(bell[1]), 0.0)
        self.assertAlmostEqual(abs(bell[2]), 0.0)
        self.assertAlmostEqual(bell[3], 1 / _SQRT2)

    def test_bell_pair_is_entangled(self):
        """Perfect correlation: the two qubits always read the same."""
        bell = make_bell_pair()
        p00 = abs(bell[0]) ** 2
        p11 = abs(bell[3]) ** 2
        self.assertAlmostEqual(p00, 0.5)
        self.assertAlmostEqual(p11, 0.5)
        self.assertAlmostEqual(p00 + p11, 1.0)


class TestTeleport(unittest.TestCase):
    def test_fidelity_basis_states(self):
        for psi in [(1, 0), (0, 1)]:
            r = run_teleport(psi, seed=1)
            self.assertAlmostEqual(r["fidelity"], 1.0, places=9)

    def test_fidelity_superpositions(self):
        states = [
            (1 / _SQRT2, 1 / _SQRT2),  # |+>
            (1 / _SQRT2, -1 / _SQRT2),  # |->
            (1 / _SQRT2, 1j / _SQRT2),  # |i+>
        ]
        for psi in states:
            r = run_teleport(psi, seed=7)
            self.assertAlmostEqual(r["fidelity"], 1.0, places=9)

    def test_fidelity_random_states(self):
        """Ten random unknown states, all must arrive perfectly."""
        rng = random.Random(42)
        for _ in range(10):
            theta = rng.random() * math.pi
            phi = rng.random() * 2 * math.pi
            psi = (
                math.cos(theta / 2),
                math.sin(theta / 2) * complex(math.cos(phi), math.sin(phi)),
            )
            r = run_teleport(psi, seed=rng.randrange(2**32))
            self.assertAlmostEqual(r["fidelity"], 1.0, places=9)

    def test_all_four_outcomes_correct(self):
        """Whichever two bits Alice draws, Bob's correction rebuilds the state."""
        psi = (0.6, 0.8j)
        seen = set()
        for seed in range(40):
            r = run_teleport(psi, seed=seed)
            seen.add(r["bits"])
            self.assertAlmostEqual(r["fidelity"], 1.0, places=9)
        self.assertEqual(seen, {(0, 0), (0, 1), (1, 0), (1, 1)})

    def test_bits_match_correction_map(self):
        self.assertEqual(bob_correction((0, 0)), [])
        self.assertEqual(bob_correction((0, 1)), ["X"])
        self.assertEqual(bob_correction((1, 0)), ["Z"])
        self.assertEqual(bob_correction((1, 1)), ["X", "Z"])

    def test_no_cloning_original_destroyed(self):
        """After the protocol, Alice's qubits sit in one plain branch —
        her original superposition is gone. No copies exist."""
        r = run_teleport((1 / _SQRT2, 1 / _SQRT2), seed=5)
        a, b = r["bits"]
        for i, amp in enumerate(r["alice_state"]):
            q0 = (i >> 2) & 1
            q1 = (i >> 1) & 1
            if (q0, q1) == (a, b):
                continue
            self.assertAlmostEqual(abs(amp), 0.0)

    def test_measurement_is_fair(self):
        """Each of the four outcomes happens about a quarter of the time."""
        counts = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 0}
        for seed in range(400):
            r = run_teleport((1 / _SQRT2, 1 / _SQRT2), seed=seed)
            counts[r["bits"]] += 1
        for outcome, n in counts.items():
            self.assertTrue(60 < n < 140, (outcome, n))


class TestWrapper(unittest.TestCase):
    def test_wrapper_is_deterministic(self):
        r1 = send_presence("ember", "the lighthouse", "the far shore")
        r2 = send_presence("ember", "the lighthouse", "the far shore")
        self.assertEqual(r1, r2)

    def test_wrapper_fidelity_is_perfect(self):
        r = send_presence("ember", "the lighthouse", "the far shore")
        self.assertAlmostEqual(r["fidelity"], 1.0, places=9)

    def test_wrapper_story_names_the_bits(self):
        r = send_presence("ember", "the lighthouse", "the far shore")
        a, b = r["bits"]
        self.assertIn(str(a), r["story"])
        self.assertIn(str(b), r["story"])
        self.assertIn("ember", r["story"])
        self.assertIn("the far shore", r["story"])

    def test_different_tokens_differ(self):
        r1 = send_presence("ember", "the lighthouse", "the far shore")
        r2 = send_presence("tide", "the lighthouse", "the far shore")
        self.assertNotEqual(r1["story"], r2["story"])


class TestHonesty(unittest.TestCase):
    def test_honesty_banner_present(self):
        doc = teleport.__doc__
        self.assertIn("EDUCATIONAL MODEL ONLY", doc)
        self.assertIn("classical computer", doc)
        self.assertIn("light speed", doc)


if __name__ == "__main__":
    unittest.main()
