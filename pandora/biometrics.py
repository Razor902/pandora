# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Biometric safety trip for Pandora's Box — the breaker.

Curtis's order: the box trips out BEFORE it can cause serious damage.
A heart-rate cuff on the wrist and a motion sensor watch the player while
the box is armed. If the body says "too much" — a racing heart that won't
come down, a sudden fear spike, violent thrashing, or the cuff coming off —
the box goes quiet on its own. The way a circuit breaker trips before the
wire melts.

Fail-secure: losing the signal trips the box. A cuff that isn't worn reads
the same as a cuff that reads danger. There is no "sensor off" mode.

Hardware note: the retail cuff is a wrist band carrying an optical pulse
sensor (e.g. MAX30102 over I2C on the Pi Pico) plus an IMU for motion.
This module speaks to any reader object with a read() method — real
hardware ships with the box; tests and demos use SimulatedCuff below.
"""

import time
from collections import deque


class GuardrailError(Exception):
    pass


# Conservative defaults. These are ceilings for entertainment, not medical
# thresholds — the box trips long before a doctor would worry.
CEILING_BPM = 150       # sustained above this -> trip
SUSTAINED_S = 8         # seconds above the ceiling before the trip
SPIKE_DELTA_BPM = 40    # jump this big inside the window -> trip
SPIKE_WINDOW_S = 10     # seconds the spike is measured over
SIGNAL_TIMEOUT_S = 5    # seconds without any reading -> trip (fail-secure)
MOTION_TRIP_LEVEL = 0.9  # violent motion, 0..1 scale
MOTION_SUSTAINED_S = 5  # seconds of violent motion before the trip


class CuffReader(object):
    """Protocol for the real hardware. read() returns
    (bpm_or_None, motion_0_to_1). bpm is None when the sensor has no
    pulse — cuff off, poor contact, hardware fault."""

    def read(self):
        raise NotImplementedError


class SimulatedCuff(CuffReader):
    """Scripted cuff for tests and demos. readings is a list of
    (bpm_or_None, motion) tuples; it holds the last one when the script
    runs out."""

    def __init__(self, readings):
        self._readings = list(readings)
        self._i = 0

    def read(self):
        r = self._readings[min(self._i, len(self._readings) - 1)]
        self._i += 1
        return r


class BiometricTrip(object):
    """The breaker. Poll update() from the game loop; it returns None
    while the body is fine, or a plain-language reason the moment the box
    must trip. Latched: once tripped it stays tripped until reset()."""

    def __init__(self, reader, clock=None,
                 ceiling_bpm=CEILING_BPM, sustained_s=SUSTAINED_S,
                 spike_delta_bpm=SPIKE_DELTA_BPM,
                 spike_window_s=SPIKE_WINDOW_S,
                 signal_timeout_s=SIGNAL_TIMEOUT_S,
                 motion_trip_level=MOTION_TRIP_LEVEL,
                 motion_sustained_s=MOTION_SUSTAINED_S):
        self.reader = reader
        self._clock = clock or time.monotonic
        self.ceiling_bpm = ceiling_bpm
        self.sustained_s = sustained_s
        self.spike_delta_bpm = spike_delta_bpm
        self.spike_window_s = spike_window_s
        self.signal_timeout_s = signal_timeout_s
        self.motion_trip_level = motion_trip_level
        self.motion_sustained_s = motion_sustained_s
        self._history = deque()  # (t, bpm) inside the spike window
        self._above_since = None
        self._motion_since = None
        self._last_good = None
        self._tripped_reason = None

    @property
    def tripped(self):
        return self._tripped_reason is not None

    @property
    def reason(self):
        return self._tripped_reason

    def reset(self):
        self._history.clear()
        self._above_since = None
        self._motion_since = None
        self._last_good = None
        self._tripped_reason = None

    def arm_check(self):
        """The cuff must be on and reading before the box arms."""
        bpm, _motion = self.reader.read()
        if bpm is None:
            return (False, "The heart cuff isn't reading. Put the cuff "
                           "on snug and try again — the box won't arm "
                           "blind.")
        if bpm >= self.ceiling_bpm:
            return (False, "Your heart is already racing past the safe "
                           "ceiling. Rest first — the box won't arm "
                           "until it settles.")
        self.reset()
        self._last_good = self._clock()
        self._history.append((self._last_good, bpm))
        return (True, "Cuff linked.")

    def _trip(self, reason):
        self._tripped_reason = reason
        return reason

    def update(self):
        """Poll me every loop. Returns None while safe, or the trip
        reason the moment the box must go quiet."""
        if self._tripped_reason is not None:
            return self._tripped_reason
        now = self._clock()
        bpm, motion = self.reader.read()

        # -- fail-secure: no signal is a trip, not a shrug ----------------
        if bpm is None:
            if self._last_good is None:
                self._last_good = now  # first read ever; allow one beat
                return None
            if now - self._last_good >= self.signal_timeout_s:
                return self._trip(
                    "The cuff lost your pulse. The box trips rather "
                    "than run blind.")
            return None
        self._last_good = now

        # -- fear spike: a sudden jump inside the window ------------------
        self._history.append((now, bpm))
        while self._history and now - self._history[0][0] > self.spike_window_s:
            self._history.popleft()
        if self._history:
            lo = min(b for _t, b in self._history)
            hi = max(b for _t, b in self._history)
            if hi - lo >= self.spike_delta_bpm:
                return self._trip(
                    "Your heart spiked %d beats in under %d seconds. "
                    "The box is going quiet to keep you safe."
                    % (hi - lo, self.spike_window_s))

        # -- sustained ceiling -------------------------------------------
        if bpm >= self.ceiling_bpm:
            if self._above_since is None:
                self._above_since = now
            elif now - self._above_since >= self.sustained_s:
                return self._trip(
                    "Your heart stayed above %d beats for %d seconds. "
                    "The box is going quiet to keep you safe."
                    % (self.ceiling_bpm, self.sustained_s))
        else:
            self._above_since = None

        # -- violent motion ------------------------------------------------
        if motion is not None and motion >= self.motion_trip_level:
            if self._motion_since is None:
                self._motion_since = now
            elif now - self._motion_since >= self.motion_sustained_s:
                return self._trip(
                    "The motion sensor reads violent movement. The box "
                    "is going quiet to keep you safe.")
        else:
            self._motion_since = None

        return None
