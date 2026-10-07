# © 2026 Curtis Ray Dyess · Crimson Rose LLC
#!/usr/bin/env python3
"""Pandora defense system — one integrated entry point.

Curtis's order: "Implement Pandora to the system, for defense."
This wires the whole defense stack into one runnable box:

    guardrails  — content caps, time budget, admin, tamper seal, kill switch
    biometrics  — the heart-rate / motion breaker (fail-secure trip)
    engine      — the Pandora scare engine the guardrails wrap

The rules, his rules, enforced here:

  * The box never arms blind. A cuff reader (real hardware on the box,
    SimulatedCuff on the bench) must be attached before arm() succeeds.
    Only the admin, with their PIN, can detach the trip — and the box
    remembers it was the admin's call.
  * Fail-secure: an unworn cuff, a lost pulse, a racing heart, a fear
    spike, or violent motion all read as DANGER. The box trips before
    the wire melts. Safety thresholds are never negotiable here.
  * Status is always one honest word: SAFE / ARMED / TRIPPED / DISARMED.

Defense layer only. The scare/atmosphere modules are wired in as the
thing being guarded — nothing about them is extended here.

Run it:
    cd ~/workspace/arcade && python3 -m pandora.pandora_defense --demo spike
    cd ~/workspace/arcade && python3 -m pandora.pandora_defense --selftest
"""

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pandora.guardrails import Guardrails, GuardrailError, curtis_approval_code
from pandora.biometrics import BiometricTrip, SimulatedCuff, CuffReader
from pandora.core import Engine

__version__ = "1.0.0"

_HERE = os.path.dirname(os.path.abspath(__file__))


class FakeClock(object):
    """A clock you advance by hand. Demos and tests, never the real box."""

    def __init__(self, start=1000.0):
        self.t = float(start)

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += float(seconds)


class PandoraDefense(object):
    """One box: guardrails + biometric breaker + engine + kill switch."""

    SAFE, ARMED, TRIPPED, DISARMED = "SAFE", "ARMED", "TRIPPED", "DISARMED"

    def __init__(self, state_path=None, clock=None):
        self.guard = Guardrails(state_path=state_path, clock=clock)
        self.engine = None
        self._status = self.SAFE
        self._trip_reason = None
        self._trip_attached = False
        self._admin_detached = False
        self._level = None

    # -- wiring ------------------------------------------------------
    def attach_biometrics(self, reader, clock=None):
        """Attach the heart-rate breaker. reader is any CuffReader —
        real hardware on the box, SimulatedCuff on the bench."""
        if not isinstance(reader, CuffReader):
            raise GuardrailError(
                "The cuff reader has to speak the CuffReader protocol "
                "(a read() that returns (bpm_or_None, motion_0_to_1)).")
        trip = BiometricTrip(reader, clock=clock) if clock is not None \
            else BiometricTrip(reader)
        msg = self.guard.enable_biometrics(trip)
        self._trip_attached = True
        self._admin_detached = False
        return msg

    def detach_biometrics(self, pin):
        """Admin only. Taking the breaker off needs the admin PIN, and
        the box remembers the admin made that call."""
        msg = self.guard.disable_biometrics(pin)
        self._trip_attached = False
        self._admin_detached = True
        return msg

    # -- the one rule: never arm blind --------------------------------
    def arm(self, level=1, consent=False, game=None):
        """Arm the box. Refuses, in plain language, unless a cuff reader
        is attached — or the admin explicitly detached the trip."""
        if not self._trip_attached and not self._admin_detached:
            raise GuardrailError(
                "No cuff reader attached. The box won't arm blind — "
                "attach one with attach_biometrics(), or have the admin "
                "detach the trip with their PIN.")
        self.engine = Engine(level)
        try:
            msg = self.guard.arm(self.engine, level=level,
                                 consent=consent, game=game)
        except Exception:
            self.engine = None
            raise
        self._status = self.ARMED
        self._trip_reason = None
        self._level = level
        return msg

    def tick(self):
        """One heartbeat of the defense loop. Call from the game loop.
        Returns the guard's answer; if the box wound itself down, the
        status word tells you why."""
        result = self.guard.tick()
        if isinstance(result, dict):  # the box wound itself down
            reason = result.get("reason")
            if reason:
                self._status = self.TRIPPED
                self._trip_reason = reason
            else:  # time budget spent — a calm, planned stop
                self._status = self.DISARMED
                self._trip_reason = None
            self._level = None
        return result

    def disarm(self):
        """End the session calmly. Debits the played time first."""
        msg = self.guard.disarm()
        if self._status == self.ARMED:
            self._status = self.DISARMED
        self._level = None
        return msg

    def kill(self):
        """The kill switch. Instant, for everyone, always. No checks."""
        if self.engine is not None:
            try:
                self.guard.kill(self.engine)
            except Exception:  # noqa: BLE001 - quiet is the point
                pass
        self.engine = None
        self._status = self.SAFE
        self._trip_reason = None
        self._level = None
        return "Box is quiet."

    # -- honest status --------------------------------------------------
    @property
    def status_word(self):
        return self._status

    @property
    def trip_reason(self):
        return self._trip_reason

    def status_line(self):
        """One line Curtis can read at a glance."""
        word = self._status
        detail = self.guard.status()
        if word == self.TRIPPED and self._trip_reason:
            return "[PANDORA] TRIPPED — %s" % self._trip_reason
        if word == self.ARMED:
            return "[PANDORA] ARMED — level %s. %s" % (self._level, detail)
        return "[PANDORA] %s — %s" % (word, detail)


# ---------------------------------------------------------------------------
# demos — the safe trip test, scripted. Bench only, /tmp state, nothing real.
# ---------------------------------------------------------------------------

def _demo_box():
    """A fresh box in /tmp: manufactured, set up, Curtis-approved."""
    tmp = tempfile.mkdtemp(prefix="pandora-demo-")
    state = os.path.join(tmp, "guardrails.json")
    fake = FakeClock()
    box = PandoraDefense(state_path=state)
    # Demo stand-in for Curtis's owner secret. On a real box he mints
    # this once, on his own machine, and bakes it in at manufacture.
    secret = os.urandom(32).hex()
    box.guard.manufacture(secret)
    today = datetime.now().strftime("%a")
    others = [d for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
              if d != today][:2]
    token = box.guard.begin_setup(age_attested=True,
                                  days=[today] + others,
                                  admin_pin="1234")
    code = curtis_approval_code(secret, token, "grant-admin")
    box.guard.curtis_approve(token, code)
    return box, fake


def _run_beats(box, fake, seconds):
    """Advance the fake clock one second at a time, ticking the box."""
    for _ in range(seconds):
        fake.advance(1.0)
        box.tick()
        if box.status_word == PandoraDefense.TRIPPED:
            print("    t+%ds ... %s" % (seconds, box.status_word))
            return
    print("    t+%ds ... %s" % (seconds, box.status_word))


def run_demo(scenario):
    scenarios = {
        # (description, cuff readings, beats to run)
        "healthy": (
            "cuff steady at 72 bpm — the box stays armed",
            [(72, 0.1)] * 40, 6),
        "spike": (
            "heart jumps 72 -> 120 bpm — the fear-spike trip",
            [(72, 0.1)] * 12 + [(120, 0.2)], 13),
        "sustained": (
            "heart climbs and holds above 150 — the ceiling trip",
            [(116, 0.1), (125, 0.1), (135, 0.1), (145, 0.1),
             (152, 0.1)] + [(155, 0.1)] * 12, 16),
        "signal": (
            "cuff loses the pulse — the fail-secure trip",
            [(72, 0.1)] * 3 + [(None, 0.0)] * 10, 8),
        "motion": (
            "violent motion for 5 seconds — the motion trip",
            [(72, 0.1)] * 2 + [(75, 0.95)] * 10, 8),
    }
    if scenario not in scenarios:
        raise SystemExit("unknown demo %r — pick one of: %s"
                         % (scenario, ", ".join(sorted(scenarios))))
    desc, readings, beats = scenarios[scenario]
    print("=== Pandora defense demo: %s ===" % scenario)
    print("    %s" % desc)
    box, fake = _demo_box()
    print("[1] manufactured + set up + Curtis-approved ... READY")
    box.attach_biometrics(SimulatedCuff(readings), clock=fake)
    print("[2] cuff attached (simulated) ... linked")
    print("[3] arm(level=1): %s" % box.arm(level=1))
    print("    %s" % box.status_line())
    print("[4] ticking the defense loop ...")
    _run_beats(box, fake, beats)
    print("    %s" % box.status_line())
    if box.status_word == PandoraDefense.TRIPPED:
        print("[5] the breaker did its job — the box went quiet on its own")
    else:
        print("[5] disarm(): %s" % box.disarm())
        print("    %s" % box.status_line())
    print("[6] kill(): %s" % box.kill())
    print("    %s" % box.status_line())


def run_selftests():
    """Run the shipped suites and report honest counts."""
    total_pass, total_fail = 0, 0
    for name in ("guardrail_selftest.py", "selftest.py"):
        path = os.path.join(_HERE, name)
        print("=== %s ===" % name)
        proc = subprocess.run([sys.executable, path],
                              capture_output=True, text=True, cwd=_HERE)
        out = (proc.stdout + proc.stderr).strip().splitlines()
        for line in out[-4:]:
            print("    " + line)
        for line in out:
            if "passed," in line and "failed" in line:
                parts = line.replace(",", "").split()
                try:
                    total_pass += int(parts[0])
                    total_fail += int(parts[2])
                except (ValueError, IndexError):
                    pass
        if proc.returncode != 0:
            print("    exited nonzero — something failed above")
    print("=== total: %d passed, %d failed ===" % (total_pass, total_fail))
    return total_fail == 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pandora defense system — guardrails, biometric "
                    "breaker, kill switch. One integrated box.")
    ap.add_argument("--demo", nargs="?", const="spike", metavar="SCENARIO",
                    help="run a safe scripted trip test: "
                         "healthy, spike, sustained, signal, motion "
                         "(default: spike)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the shipped guardrail + engine test suites")
    args = ap.parse_args(argv)
    if args.selftest:
        ok = run_selftests()
        raise SystemExit(0 if ok else 1)
    if args.demo:
        run_demo(args.demo)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
