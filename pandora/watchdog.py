# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora's Box watchdog — the box watching itself.

EDUCATIONAL MODEL ONLY. Not a medical device. No diagnosis, no treatment,
no advice of any kind. Never use on real patients.

Curtis's order: "Incorporate Watchdog into my system."

A watchdog is the box watching itself. Every subsystem reports in with a
heartbeat — guardrails, biometrics, the pendulum, the weather, the treasure
bridge, the threshold — and if any heartbeat goes stale, the watchdog
raises the alarm and fails safe.

The fail-secure rule, same as the cuff: silence reads as danger. A
subsystem that stops reporting is treated exactly like a pulse signal
lost — the box winds down, never on.

The watchdog calls INTO the guardrails (wind_down), never around them.
It is a software supervisor, not a hardware watchdog timer — it watches
from inside the same program, so it cannot catch a total freeze of the
host. Say so honestly: it is the conscience on duty, not the power cord.
"""

import time


class Watchdog:
    """Supervisor heartbeat monitor for Pandora's Box subsystems.

    Register each subsystem with a name and a max_silence (seconds). Call
    heartbeat(name) whenever the subsystem reports in. Call check(now)
    on a tick; any subsystem silent longer than its max_silence comes
    back sick, and the on_sick action fires once per newly-sick
    subsystem (no alarm spam).
    """

    def __init__(self, clock=None, on_sick=None, guardrails=None):
        # clock: () -> float seconds; defaults to time.monotonic (rollback-proof)
        self._clock = clock or time.monotonic
        self._guardrails = guardrails
        self._systems = {}   # name -> {"max_silence": float, "last": float|None}
        self._sick = set()   # names currently sick (alarm already raised)
        self._log = []       # (t, name, event) plain audit trail
        self.on_sick = on_sick or self._default_on_sick

    # -- registration --------------------------------------------------
    def register(self, name, max_silence):
        """Add a subsystem. max_silence is seconds of quiet tolerated."""
        if max_silence <= 0:
            raise ValueError("max_silence must be positive")
        self._systems[name] = {"max_silence": float(max_silence),
                               "last": None}
        self._log.append((self._clock(), name, "registered"))

    def heartbeat(self, name):
        """A subsystem reports in. Unknown names are refused, not invented."""
        if name not in self._systems:
            raise KeyError("unknown subsystem: %r" % (name,))
        now = self._clock()
        self._systems[name]["last"] = now
        self._log.append((now, name, "heartbeat"))
        if name in self._sick:
            # It came back. Clear the sick flag so a future lapse
            # alarms again — recovery is real, and so is relapse.
            self._sick.discard(name)
            self._log.append((now, name, "recovered"))

    # -- the check ------------------------------------------------------
    def check(self, now=None):
        """Return the list of sick subsystem names right now.

        A subsystem is sick when silent longer than its max_silence.
        Never-reported counts as silent since registration.
        """
        now = self._clock() if now is None else now
        sick = []
        for name, sys in self._systems.items():
            last = sys["last"]
            silent_for = now - last if last is not None else float("inf")
            if silent_for > sys["max_silence"]:
                sick.append(name)
        newly = [n for n in sick if n not in self._sick]
        for name in newly:
            self._sick.add(name)
            self._log.append((now, name, "sick"))
            try:
                self.on_sick(name, now)
            except Exception:
                # The alarm must never die inside the watchdog.
                # Log it and keep watching.
                self._log.append((now, name, "on_sick raised"))
        return sick

    # -- the teeth -------------------------------------------------------
    def _default_on_sick(self, name, now):
        """Fail safe: wind the box down through the guardrails."""
        reason = "watchdog: subsystem %r went quiet" % (name,)
        if self._guardrails is not None:
            wind = getattr(self._guardrails, "wind_down", None)
            if callable(wind):
                wind(reason=reason)
                return
        # No guardrails wired in (tests, demos): log the ALARM loudly.
        self._log.append((now, name, "ALARM: " + reason))

    # -- plain-words status ----------------------------------------------
    def silent_for(self, name, now=None):
        """How long a subsystem has been quiet, in seconds."""
        if name not in self._systems:
            raise KeyError("unknown subsystem: %r" % (name,))
        now = self._clock() if now is None else now
        last = self._systems[name]["last"]
        if last is None:
            return None  # never reported
        return max(0.0, now - last)

    def status(self, now=None):
        """Plain-words report: who's alive, who's quiet, how long."""
        now = self._clock() if now is None else now
        lines = []
        if not self._systems:
            return "The watchdog is watching nothing. No subsystems registered."
        for name in sorted(self._systems):
            s = self.silent_for(name, now)
            max_s = self._systems[name]["max_silence"]
            if s is None:
                lines.append("%s: never reported in (allowed %s seconds of quiet)"
                             % (name, _fmt(max_s)))
            elif s > max_s:
                lines.append("%s: QUIET for %s — over the %s limit. Alarm raised."
                             % (name, _fmt(s), _fmt(max_s)))
            else:
                lines.append("%s: alive, last heartbeat %s ago (limit %s)"
                             % (name, _fmt(s), _fmt(max_s)))
        return "\n".join(lines)

    def log(self):
        """The audit trail, oldest first."""
        return list(self._log)


def _fmt(seconds):
    if seconds >= 60:
        return "%d min %d s" % (int(seconds // 60), int(seconds % 60))
    if seconds == int(seconds):
        return "%d s" % int(seconds)
    return "%.1f s" % seconds


def demo():
    """The watchdog on duty: healthy beats, then one system goes quiet."""
    print("=== Pandora's Box watchdog — demo ===")
    t = [0.0]
    clock = lambda: t[0]
    alarms = []

    wd = Watchdog(clock=clock)
    wd.on_sick = lambda name, now: alarms.append((name, now))

    # Register the box's systems, each with its own patience.
    wd.register("guardrails", max_silence=5)
    wd.register("biometrics", max_silence=5)   # the cuff reports fast
    wd.register("pendulum", max_silence=30)
    wd.register("weather", max_silence=300)
    wd.register("treasure-bridge", max_silence=60)
    wd.register("threshold", max_silence=60)

    # Everybody reports in. All healthy.
    for name in ("guardrails", "biometrics", "pendulum",
                 "weather", "treasure-bridge", "threshold"):
        wd.heartbeat(name)
    print(wd.status())
    print("sick:", wd.check())

    # Time passes; everyone keeps beating except the cuff.
    t[0] = 4.0
    for name in ("guardrails", "pendulum", "weather",
                 "treasure-bridge", "threshold"):
        wd.heartbeat(name)
    print("\n-- four seconds later, biometrics silent --")
    print(wd.status())
    print("sick:", wd.check())

    # Six seconds with no cuff heartbeat: over the 5s limit.
    t[0] = 10.0
    for name in ("guardrails", "pendulum", "weather",
                 "treasure-bridge", "threshold"):
        wd.heartbeat(name)
    print("\n-- the cuff stays quiet past its limit --")
    print(wd.status())
    sick = wd.check()
    print("sick:", sick)
    print("alarms raised:", alarms)

    # The alarm fires once — no spam on repeat checks.
    wd.check()
    print("alarms after second check:", alarms)

    # The cuff comes back. Recovery is real.
    wd.heartbeat("biometrics")
    print("\n-- the cuff reports in again --")
    print(wd.status())
    print("sick:", wd.check())
    print("=== demo done ===")


if __name__ == "__main__":
    demo()
