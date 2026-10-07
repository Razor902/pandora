# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Tests for the Pandora's Box watchdog.

EDUCATIONAL MODEL ONLY.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from watchdog import Watchdog  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def make(**kw):
    clock = FakeClock()
    alarms = []
    wd = Watchdog(clock=clock,
                  on_sick=lambda n, now: alarms.append((n, now)), **kw)
    return wd, clock, alarms


def test_registration():
    wd, clock, _ = make()
    wd.register("guardrails", max_silence=5)
    wd.register("biometrics", max_silence=3)
    assert "guardrails" in wd.status()
    assert "biometrics" in wd.status()
    try:
        wd.register("bad", max_silence=0)
    except ValueError:
        pass
    else:
        raise AssertionError("non-positive max_silence must raise")


def test_healthy_heartbeats_pass():
    wd, clock, alarms = make()
    wd.register("pendulum", max_silence=30)
    wd.heartbeat("pendulum")
    clock.advance(10)
    assert wd.check() == []
    assert alarms == []
    wd.heartbeat("pendulum")
    clock.advance(29)
    assert wd.check() == []


def test_stale_flagged_past_max_silence():
    wd, clock, alarms = make()
    wd.register("biometrics", max_silence=5)
    wd.heartbeat("biometrics")
    clock.advance(5.0)
    # Exactly at the limit: still alive (strictly greater trips).
    assert wd.check() == []
    clock.advance(0.1)
    assert wd.check() == ["biometrics"]
    assert alarms == [("biometrics", 5.1)]


def test_never_reported_counts_as_sick():
    wd, clock, alarms = make()
    wd.register("weather", max_silence=300)
    # Never heartbeat'd: silent since forever -> sick.
    assert wd.check() == ["weather"]


def test_subsystems_independent():
    wd, clock, alarms = make()
    wd.register("a", max_silence=5)
    wd.register("b", max_silence=100)
    wd.heartbeat("a")
    wd.heartbeat("b")
    clock.advance(6)
    wd.heartbeat("b")  # b keeps beating
    sick = wd.check()
    assert sick == ["a"], sick
    assert [n for n, _ in alarms] == ["a"]


def test_no_alarm_spam():
    wd, clock, alarms = make()
    wd.register("cuff", max_silence=2)
    wd.heartbeat("cuff")
    clock.advance(10)
    wd.check()
    wd.check()
    wd.check()
    assert len(alarms) == 1, alarms
    # Recovery, then relapse: alarm again — that's correct, not spam.
    wd.heartbeat("cuff")
    clock.advance(10)
    wd.check()
    assert len(alarms) == 2, alarms


def test_default_on_sick_calls_guardrails():
    clock = FakeClock()
    wound = []
    guard = type("G", (), {"wind_down": lambda self, reason=None:
                           wound.append(reason)})()
    wd = Watchdog(clock=clock, guardrails=guard)
    wd.register("threshold", max_silence=1)
    wd.heartbeat("threshold")
    clock.advance(5)
    wd.check()
    assert len(wound) == 1
    assert "threshold" in wound[0]


def test_default_on_sick_without_guardrails_logs_alarm():
    clock = FakeClock()
    wd = Watchdog(clock=clock)  # no guardrails wired
    wd.register("x", max_silence=1)
    wd.heartbeat("x")
    clock.advance(5)
    wd.check()
    events = [e for _, _, e in wd.log()]
    assert any(e.startswith("ALARM") for e in events), events


def test_status_plain_words():
    wd, clock, _ = make()
    assert "watching nothing" in wd.status()
    wd.register("pendulum", max_silence=30)
    s = wd.status()
    assert "never reported" in s
    wd.heartbeat("pendulum")
    s = wd.status()
    assert "alive" in s
    clock.advance(60)
    s = wd.status()
    assert "QUIET" in s


def test_unknown_heartbeat_refused():
    wd, _, _ = make()
    try:
        wd.heartbeat("ghost")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown subsystem must raise KeyError")


def test_recovery_clears_sick():
    wd, clock, _ = make()
    wd.register("m", max_silence=1)
    wd.heartbeat("m")
    clock.advance(5)
    assert wd.check() == ["m"]
    wd.heartbeat("m")
    assert wd.check() == []


def run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    n = 0
    for fn in fns:
        fn()
        n += 1
        print("ok - %s" % fn.__name__)
    print("%d/%d watchdog tests passed" % (n, n))


if __name__ == "__main__":
    run()
