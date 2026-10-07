# © 2026 Curtis Ray Dyess · Crimson Rose LLC
#!/usr/bin/env python3
"""
pendulum.py -- the giant pendulum of Pandora's Box.

Curtis's image, his words: a giant pendulum for the box, "that keeps
track of true tone." So this is the box's timekeeper and tuning fork.
The swing is the rhythm. The tone is the pitch. True tone is the
reference the box stays tuned to.

Two halves, one body:
    Pendulum   -- honest physics. Length L, gravity g, period
                  T = 2*pi*sqrt(L/g). Angle over time:
                  theta(t) = theta0 * cos(2*pi*t/T).
                  Giant by default: 10 meters of slow, stately swing.
    ToneTracker -- the keeper of true tone. True tone is A = 440 Hz,
                  the tuning standard, and its octaves. Feed it a
                  measured pitch; it tells you how far you've drifted
                  in cents (100 cents = one semitone) and whether the
                  tone is true (within +/-5 cents) or wandering. Every
                  check goes in the log, so the box knows when its
                  tone wandered and when it came home.

The pendulum's swing is the beat: each completed swing is one beat,
and the beat is what the tone checks march to. Rhythm keeps time;
tone keeps truth.

EDUCATIONAL MODEL ONLY.
"""

import math

# ---------------------------------------------------------------------------
# The pendulum -- honest physics.
# ---------------------------------------------------------------------------

G = 9.81          # gravity, m/s^2 -- Earth, where the box stands
GIANT_LENGTH = 10.0   # meters -- the giant's arm
TRUE_TONE_HZ = 440.0  # A4, the tuning standard -- true tone
TRUE_CENTS = 5.0      # within this many cents, a tone is true


class Pendulum:
    """A simple pendulum. Small angles, honest math, no shortcuts.

    theta(t) = theta0 * cos(2*pi*t / T),  T = 2*pi*sqrt(L/g).
    """

    def __init__(self, length=GIANT_LENGTH, amplitude_deg=10.0, gravity=G):
        if length <= 0:
            raise ValueError("a pendulum needs a positive length")
        self.length = float(length)
        self.amplitude = math.radians(amplitude_deg)
        self.gravity = float(gravity)

    @property
    def period(self):
        """One full swing there and back, in seconds. Computed, not hardcoded."""
        return 2.0 * math.pi * math.sqrt(self.length / self.gravity)

    def angle(self, t):
        """Angle in radians at time t (seconds). t=0 is full swing right."""
        return self.amplitude * math.cos(2.0 * math.pi * t / self.period)

    def angle_deg(self, t):
        """Angle in degrees -- easier to picture."""
        return math.degrees(self.angle(t))

    def beats(self, n):
        """The times (seconds) of the next n beat points -- each full swing."""
        return [i * self.period for i in range(1, n + 1)]


# ---------------------------------------------------------------------------
# The tone tracker -- keeper of true tone.
# ---------------------------------------------------------------------------

def drift_cents(measured_hz, reference_hz=TRUE_TONE_HZ):
    """How far a measured pitch sits from the reference, in cents.

    Positive = sharp, negative = flat. 100 cents = one semitone.
    Formula: cents = 1200 * log2(measured / reference).
    """
    if measured_hz <= 0 or reference_hz <= 0:
        raise ValueError("pitches must be positive")
    return 1200.0 * math.log2(measured_hz / reference_hz)


def nearest_true_tone(measured_hz):
    """True tone isn't only 440 -- it's 440 and its octaves (220, 880, ...).

    Returns (reference_hz, drift_cents) against the closest true tone.
    """
    # Walk the octaves until we bracket the measured pitch.
    ref = TRUE_TONE_HZ
    while ref * 2 <= measured_hz * 1.5:
        ref *= 2
    while ref / 2 >= measured_hz / 1.5 and ref > 1:
        ref /= 2
    return ref, drift_cents(measured_hz, ref)


class ToneTracker:
    """Keeps track of true tone. Every check is logged:
    (time, measured_hz, reference_hz, drift_cents, true_or_drift).
    """

    def __init__(self, pendulum=None):
        self.pendulum = pendulum or Pendulum()
        self.log = []  # the record -- when the tone wandered, when it came home

    def check(self, measured_hz, t=None):
        """Check one tone. Returns a dict; appends to the log."""
        if t is None:
            t = len(self.log) * self.pendulum.period  # one check per beat
        reference, cents = nearest_true_tone(measured_hz)
        verdict = "true" if abs(cents) <= TRUE_CENTS else "drifting"
        entry = {
            "time": round(t, 3),
            "measured_hz": measured_hz,
            "reference_hz": reference,
            "drift_cents": round(cents, 2),
            "verdict": verdict,
        }
        self.log.append(entry)
        return entry

    def wanderings(self):
        """Only the entries where the tone drifted -- the wanderings."""
        return [e for e in self.log if e["verdict"] == "drifting"]

    def homecomings(self):
        """Only the entries where the tone was true -- the homecomings."""
        return [e for e in self.log if e["verdict"] == "true"]

    def describe(self, entry):
        """One log entry in plain words."""
        direction = "sharp" if entry["drift_cents"] > 0 else "flat"
        if entry["verdict"] == "true":
            return (f"at {entry['time']}s the tone read {entry['measured_hz']} Hz "
                    f"-- true tone ({entry['drift_cents']:+.1f} cents). It is home.")
        return (f"at {entry['time']}s the tone read {entry['measured_hz']} Hz "
                f"-- {direction} by {abs(entry['drift_cents']):.1f} cents "
                f"against {entry['reference_hz']} Hz. It is wandering.")


# ---------------------------------------------------------------------------
# The demo -- swing the giant, check the tones.
# ---------------------------------------------------------------------------

def demo():
    print("The giant pendulum of Pandora's Box")
    print("=" * 52)
    p = Pendulum()  # 10 meters, the giant
    print(f"arm length : {p.length} m")
    print(f"one swing  : {p.period:.3f} seconds -- slow and stately")
    print(f"true tone  : {TRUE_TONE_HZ} Hz (and its octaves)")
    print()
    print("Three beats, three tones:")
    tracker = ToneTracker(p)
    for measured in (440.0, 445.0, 435.0):
        entry = tracker.check(measured)
        print("  " + tracker.describe(entry))
    print()
    n_true = len(tracker.homecomings())
    n_drift = len(tracker.wanderings())
    print(f"The log keeps {len(tracker.log)} checks: "
          f"{n_true} home, {n_drift} wandering.")
    print("The pendulum remembers. The tone always knows the way back.")


if __name__ == "__main__":
    demo()
