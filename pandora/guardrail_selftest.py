# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora's Box guardrails selftest — headless.

Verifies Curtis's guardrail orders: the box's internals are never altered
(the engine's own 17 tests must still pass), content restrictions, parental
controls, and the hard rule that ONLY Curtis can approve admin access —
no self-provisioning, no default PIN, no backdoor.

Prints PASS/FAIL per test; exits nonzero on any failure.
"""

import os
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pandora import Engine
from pandora.guardrails import (
    Guardrails, GuardrailError, curtis_approval_code)
from pandora.biometrics import BiometricTrip, SimulatedCuff

RESULTS = []
OWNER = "00" * 32  # Curtis's owner secret in tests (64 hex chars)


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print("PASS: %s" % name)
    except Exception as e:  # noqa: BLE001 - selftest must catch everything
        RESULTS.append((name, False, "%s: %s" % (type(e).__name__, e)))
        print("FAIL: %s -- %s: %s" % (name, type(e).__name__, e))


# ---------------------------------------------------------------------------
# helpers: a controllable clock and a fresh box
# ---------------------------------------------------------------------------

class Clock:
    """Monday 2026-10-05 12:00 UTC. tick() moves time."""

    def __init__(self):
        self.t = 1791201600.0

    def __call__(self):
        return self.t

    def tick(self, seconds):
        self.t += seconds


def fresh_box(clock=None):
    d = tempfile.mkdtemp(prefix="pandora-guard-")
    path = os.path.join(d, "guardrails.json")
    return Guardrails(path, clock=clock or Clock())


def manufactured(clock=None):
    g = fresh_box(clock)
    g.manufacture(OWNER)
    return g


def ready_box(clock=None, days=None, pin="admin-1234"):
    """A box through the full Curtis-approved setup."""
    g = manufactured(clock)
    token = g.begin_setup(age_attested=True,
                          days=days or ["Mon", "Tue", "Wed"],
                          admin_pin=pin)
    code = curtis_approval_code(OWNER, token, "grant-admin")
    g.curtis_approve(token, code)
    return g


def expect_refused(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except GuardrailError:
        return
    raise AssertionError("expected GuardrailError, call was allowed")


class FakeGame:
    def __init__(self):
        self.update_calls = []
        self.saved = False
        self.update = self._do_update
        self.render = self._do_render

    def _do_update(self, dt):
        self.update_calls.append(dt)

    def _do_render(self, buf):
        return buf

    def save(self):
        self.saved = True


# ---------------------------------------------------------------------------
# manufacture + setup
# ---------------------------------------------------------------------------

def t_manufacture_once():
    g = fresh_box()
    g.manufacture(OWNER)
    expect_refused(g.manufacture, OWNER)
    # weak secret refused
    g2 = fresh_box()
    expect_refused(g2.manufacture, "abcd")


def t_setup_needs_18():
    g = manufactured()
    expect_refused(g.begin_setup, age_attested=False,
                   days=["Mon", "Tue", "Wed"], admin_pin="admin-1234")
    assert g._state["state"] == "FACTORY"


def t_setup_validates_days():
    g = manufactured()
    expect_refused(g.begin_setup, True, ["Mon", "Tue"], "admin-1234")
    expect_refused(g.begin_setup, True, ["Mon", "Tue", "Funday"], "admin-1234")
    expect_refused(g.begin_setup, True, ["Mon", "Mon", "Tue"], "admin-1234")
    expect_refused(g.begin_setup, True, ["Mon", "Tue", "Wed"], "abc")


def t_locked_until_curtis_approves():
    g = manufactured()
    token = g.begin_setup(True, ["Mon", "Tue", "Wed"], "admin-1234")
    assert g._state["state"] == "AWAITING_CURTIS"
    e = Engine(level=1)
    expect_refused(g.arm, e)  # locked: Curtis hasn't approved
    assert "Curtis" in g.status()
    # no admin exists yet
    expect_refused(g.admin_auth, "admin-1234")
    assert token and len(token) == 16


def t_no_backdoor_paths():
    """Every mutator refuses without Curtis's approval. There is no other
    way to bring an admin into existence."""
    g = manufactured()
    g.begin_setup(True, ["Mon", "Tue", "Wed"], "admin-1234")
    e = Engine(level=1)
    expect_refused(g.arm, e)
    expect_refused(g.set_level_cap, "whatever", 2)
    expect_refused(g.set_days, "whatever", ["Thu", "Fri", "Sat"])
    expect_refused(g.clear_usage, "whatever")
    expect_refused(g.factory_reset_with_pin, "whatever")
    expect_refused(g.failed_attempts, "whatever")
    # wrong approval code: no admin
    expect_refused(g.curtis_approve, g._state["pending_request"]["token"],
                   "deadbeef1234")
    assert g._state["admin"] is None
    assert g._state["state"] == "AWAITING_CURTIS"


def t_forged_approval_fails():
    """An attacker with the box but not Curtis's secret cannot mint codes."""
    g = manufactured()
    token = g.begin_setup(True, ["Mon", "Tue", "Wed"], "admin-1234")
    forged = curtis_approval_code("ff" * 32, token, "grant-admin")
    expect_refused(g.curtis_approve, token, forged)
    assert g._state["admin"] is None


def t_curtis_approval_opens_box():
    g = ready_box()
    assert g._state["state"] == "READY"
    assert g.admin_auth("admin-1234") is True
    assert "minutes left" in g.status()


def t_approval_token_single_use():
    g = manufactured()
    token = g.begin_setup(True, ["Mon", "Tue", "Wed"], "admin-1234")
    code = curtis_approval_code(OWNER, token, "grant-admin")
    g.curtis_approve(token, code)
    expect_refused(g.curtis_approve, token, code)  # replay refused


# ---------------------------------------------------------------------------
# admin PIN gate
# ---------------------------------------------------------------------------

def t_pin_lockout():
    c = Clock()
    g = ready_box(c)
    for _ in range(5):
        assert g.admin_auth("wrong") is False
    # 5 bad tries: cooldown, even the right PIN refused
    expect_refused(g.admin_auth, "admin-1234")
    assert "PINs are ignored" in g.status()
    c.tick(601)
    assert g.admin_auth("admin-1234") is True


def t_failed_attempts_logged():
    g = ready_box()
    g.admin_auth("nope")
    log = g.failed_attempts("admin-1234")
    assert any(a["kind"] == "pin" and not a["ok"] for a in log)
    expect_refused(g.failed_attempts, "nope")  # players get zero access


def t_level_cap_never_above_two():
    g = ready_box()
    assert g.set_level_cap("admin-1234", 2).startswith("Content cap is now")
    expect_refused(g.set_level_cap, "admin-1234", 3)
    expect_refused(g.set_level_cap, "admin-1234", 0)
    expect_refused(g.set_level_cap, "wrong-pin", 2)
    assert g._state["level_cap"] == 2


def t_days_change_admin_only():
    g = ready_box()
    expect_refused(g.set_days, "wrong-pin", ["Thu", "Fri", "Sat"])
    g.set_days("admin-1234", ["Thu", "Fri", "Sat"])
    assert g._state["play_days"] == ["Thu", "Fri", "Sat"]


def t_clear_usage_admin_only():
    g = ready_box()
    expect_refused(g.clear_usage, "wrong-pin")


# ---------------------------------------------------------------------------
# content restrictions at arm time
# ---------------------------------------------------------------------------

def t_arm_level2_needs_consent():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    g.set_level_cap("admin-1234", 2)
    e = Engine(level=2)
    expect_refused(g.arm, e, 2)  # no consent
    g.arm(e, 2, consent=True)
    assert e.is_armed
    e.kill()


def t_arm_blocked_by_cap():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    e = Engine(level=2)
    expect_refused(g.arm, e, 2, consent=True)  # cap is 1
    g.arm(e, 1)
    assert e.is_armed
    e.kill()


def t_arm_level3_impossible():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    g.set_level_cap("admin-1234", 2)
    e = Engine(level=2)
    expect_refused(g.arm, e, 3)


def g_weekday(clock):
    from datetime import datetime
    return datetime.fromtimestamp(clock()).strftime("%a")


def play_days_including(clock):
    """3 valid play days including today."""
    wd = g_weekday(clock)
    others = [d for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
              if d != wd]
    return [wd] + others[:2]


# ---------------------------------------------------------------------------
# parental controls: time budget + wind-down
# ---------------------------------------------------------------------------

def t_time_budget_and_winddown():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    game, e = FakeGame(), Engine(level=1)
    g.arm(e, game=game)
    assert g.remaining_today() == 60
    msg = g.record_play(40)
    assert "20 minutes left" in msg
    report = g.record_play(20)  # budget spent -> graceful wind-down
    assert report["saved"] is True, "save hook was not called"
    assert report["farewell"]["type"] == "farewell"
    assert report["quiet"] is True
    assert not e.is_armed and not e.is_attached, "box did not go quiet"
    assert "resting" in g.status()
    expect_refused(g.arm, Engine(level=1))  # no re-arm today


def t_winddown_without_save_hook():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))

    class NoSave:
        def update(self, dt):
            pass

        def render(self, buf):
            return buf

    game, e = NoSave(), Engine(level=1)
    g.arm(e, game=game)
    report = g.record_play(60)
    assert report["saved"] is None  # no hook, still graceful
    assert report["quiet"] is True


def t_wrong_day_refused():
    c = Clock()
    g = ready_box(c, days=["Sat", "Sun", "Fri"])  # today is Mon
    assert g_weekday(c) not in ("Sat", "Sun", "Fri")
    expect_refused(g.arm, Engine(level=1))
    assert "isn't a play day" in g.status()


def t_weekly_reset():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    g.record_play(60)
    assert g.remaining_today() == 0
    c.tick(7 * 24 * 3600)  # next week
    assert g.remaining_today() == 60


def t_status_plain_language():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    s = g.status()
    assert "Content level cap: 1" in s
    assert "60 minutes left today" in s


# ---------------------------------------------------------------------------
# Curtis revokes
# ---------------------------------------------------------------------------

def t_curtis_revoke_locks_box():
    g = ready_box()
    token = g.request_revoke()
    code = curtis_approval_code(OWNER, token, "revoke-admin")
    g.curtis_revoke(token, code)
    assert g._state["state"] == "AWAITING_CURTIS"
    assert g._state["admin"] is None
    expect_refused(g.arm, Engine(level=1))  # locked again
    expect_refused(g.admin_auth, "admin-1234")
    # wrong code can't revoke
    g2 = ready_box()
    t2 = g2.request_revoke()
    expect_refused(g2.curtis_revoke, t2, "badcode123456")
    assert g2._state["admin"] is not None


def t_revoke_then_new_admin_needs_curtis():
    g = ready_box()
    token = g.request_revoke()
    g.curtis_revoke(token, curtis_approval_code(OWNER, token, "revoke-admin"))
    token2 = g.begin_setup(True, ["Mon", "Tue", "Wed"], "new-pin-99")
    expect_refused(g.admin_auth, "new-pin-99")  # still locked
    g.curtis_approve(token2, curtis_approval_code(OWNER, token2, "grant-admin"))
    assert g.admin_auth("new-pin-99") is True


# ---------------------------------------------------------------------------
# kill switch + factory reset
# ---------------------------------------------------------------------------

def t_kill_always_works():
    g = manufactured()  # not even set up
    game, e = FakeGame(), Engine(level=1)
    e.attach(game)
    e.arm()
    assert g.kill(e) == "Box is quiet."
    assert not e.is_armed and not e.is_attached


def t_factory_reset_keeps_manufacture():
    g = ready_box()
    g.factory_reset_with_pin("admin-1234")
    assert g._state["state"] == "FACTORY"
    assert g._state["manufactured"] is True  # Curtis's bake survives
    expect_refused(g.manufacture, OWNER)  # still can't re-manufacture
    # Curtis can approve a fresh setup after reset
    token = g.begin_setup(True, ["Mon", "Tue", "Wed"], "pin-2")
    g.curtis_approve(token, curtis_approval_code(OWNER, token, "grant-admin"))
    assert g.admin_auth("pin-2") is True


def t_factory_reset_needs_admin_or_curtis():
    g = ready_box()
    expect_refused(g.factory_reset_with_pin, "wrong-pin")
    token = g.request_factory_reset()
    expect_refused(g.curtis_factory_reset, token, "badcode123456")
    g.curtis_factory_reset(token, curtis_approval_code(
        OWNER, token, "factory-reset"))
    assert g._state["state"] == "FACTORY"


def t_state_file_locked_down():
    g = ready_box()
    mode = oct(os.stat(g.state_path).st_mode & 0o777)
    assert mode == "0o600", mode


# ---------------------------------------------------------------------------
# better: tamper-evident seal, monotonic clock, expiring approvals
# ---------------------------------------------------------------------------

def t_state_sealed_on_manufacture():
    import hashlib
    import hmac as hmac_mod
    import json as json_mod
    g = ready_box()
    assert g._state["seal"], "no seal written"
    g2 = Guardrails(g.state_path)  # reload from disk
    assert g2._tampered is False
    st = dict(g2._state)
    st.pop("seal")
    payload = json_mod.dumps(st, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
    expect = hmac_mod.new(bytes.fromhex(OWNER), payload,
                          hashlib.sha256).hexdigest()
    assert g2._state["seal"] == expect


def _tamper_with(path):
    import json as json_mod
    with open(path, "r", encoding="utf-8") as f:
        st = json_mod.load(f)
    # the cheater's edit: grant themselves a full fake hour already "used"
    # (must differ from what's stored, or the seal rightly still verifies)
    st["usage"]["days"] = {"2026-10-05": 999}
    with open(path, "w", encoding="utf-8") as f:
        json_mod.dump(st, f)


def t_tampered_state_refuses_arm():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    _tamper_with(g.state_path)
    g2 = Guardrails(g.state_path, clock=c)
    assert g2._tampered is True
    expect_refused(g2.arm, Engine(level=1))
    assert "tampered" in g2.status()
    expect_refused(g2.set_level_cap, "admin-1234", 2)
    expect_refused(g2.begin_setup, True, ["Mon", "Tue", "Wed"], "x" * 8)
    # the kill switch still works on a tampered box
    game, e = FakeGame(), Engine(level=1)
    e.attach(game)
    e.arm()
    assert g2.kill(e) == "Box is quiet."


def t_tamper_recovery_needs_curtis():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    _tamper_with(g.state_path)
    g2 = Guardrails(g.state_path, clock=c)
    assert g2._tampered is True
    token = g2.request_factory_reset()
    expect_refused(g2.curtis_factory_reset, token, "badcode123456")
    g2.curtis_factory_reset(
        token, curtis_approval_code(OWNER, token, "factory-reset"))
    assert g2._tampered is False
    assert g2._state["state"] == "FACTORY"


def t_approval_request_expires():
    c = Clock()
    g = manufactured(c)
    token = g.begin_setup(True, ["Mon", "Tue", "Wed"], "admin-1234")
    c.tick(86401)  # 24 hours + 1 second
    code = curtis_approval_code(OWNER, token, "grant-admin")
    try:
        g.curtis_approve(token, code)
    except GuardrailError as ex:
        assert "expired" in str(ex), ex
    else:
        raise AssertionError("an expired approval was honored")
    assert g._state["admin"] is None


def t_double_arm_refused():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    e = Engine(level=1)
    g.arm(e)
    expect_refused(g.arm, Engine(level=1))
    g.disarm()


def t_tick_debits_monotonic_time():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    e = Engine(level=1)
    with mock.patch("time.monotonic") as m:
        m.return_value = 1000.0
        g.arm(e)
        m.return_value = 1000.0 + 61  # 61 real seconds pass
        msg = g.tick()
    assert g._state["usage"]["days"][g._today()] == 2
    assert "58 minutes left" in msg


def t_record_play_never_below_elapsed():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    e = Engine(level=1)
    with mock.patch("time.monotonic") as m:
        m.return_value = 2000.0
        g.arm(e)
        m.return_value = 2000.0 + 121  # 121s elapse; game claims 1 minute
        msg = g.record_play(1)
    used = g._state["usage"]["days"][g._today()]
    assert used == 3, used  # ceil(121/60) = 3, not the game's 1
    assert "57 minutes left" in msg


def t_disarm_debits_and_clears():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    e = Engine(level=1)
    with mock.patch("time.monotonic") as m:
        m.return_value = 3000.0
        g.arm(e)
        m.return_value = 3000.0 + 61
        g.disarm()
    assert g._session is None
    assert not e.is_armed
    assert g._state["usage"]["days"][g._today()] == 2


# ---------------------------------------------------------------------------
# better: the biometric breaker
# ---------------------------------------------------------------------------

class MonoClock(object):
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def tick(self, s):
        self.t += s


def _pump(trip, mc, n, step=1):
    """Run n loop iterations; return the first trip reason, or None."""
    for _ in range(n):
        mc.tick(step)
        reason = trip.update()
        if reason is not None:
            return reason
    return None


def t_trip_sustained_high_hr():
    mc = MonoClock()
    # slow climb so the spike detector stays quiet, then parks at 155
    ramp = [(90, 0.1), (100, 0.1), (110, 0.1), (120, 0.1), (130, 0.1),
            (140, 0.1), (150, 0.1), (155, 0.2)]
    cuff = SimulatedCuff(ramp)
    trip = BiometricTrip(cuff, clock=mc)
    ok, _ = trip.arm_check()
    assert ok
    for _ in range(len(ramp) - 1):
        mc.tick(3)
        assert trip.update() is None  # climbing, not tripped yet
    reason = _pump(trip, mc, 12)  # holds 155
    assert reason and "stayed above" in reason, reason


def t_trip_fear_spike():
    mc = MonoClock()
    cuff = SimulatedCuff([(80, 0.1), (130, 0.4)])
    trip = BiometricTrip(cuff, clock=mc)
    ok, _ = trip.arm_check()
    assert ok
    mc.tick(2)
    reason = trip.update()
    assert reason and "spiked" in reason, reason


def t_trip_signal_loss_fails_secure():
    mc = MonoClock()
    cuff = SimulatedCuff([(85, 0.1), (None, 0.0)])
    trip = BiometricTrip(cuff, clock=mc)
    ok, _ = trip.arm_check()
    assert ok
    reason = _pump(trip, mc, 8)  # no pulse for 8s
    assert reason and "lost your pulse" in reason, reason


def t_no_trip_normal_excitement():
    mc = MonoClock()
    cuff = SimulatedCuff([(120, 0.3)] * 40)
    trip = BiometricTrip(cuff, clock=mc)
    ok, _ = trip.arm_check()
    assert ok
    assert _pump(trip, mc, 35) is None  # excited, not dangerous


def t_arm_refuses_without_cuff():
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    trip = BiometricTrip(SimulatedCuff([(None, 0.0)]), clock=MonoClock())
    g.enable_biometrics(trip)
    expect_refused(g.arm, Engine(level=1))  # the box won't arm blind


def t_trip_quiets_the_box():
    mc = MonoClock()
    c = Clock()
    g = ready_box(c, days=play_days_including(c))
    cuff = SimulatedCuff([(85, 0.1), (140, 0.3)])
    trip = BiometricTrip(cuff, clock=mc)
    g.enable_biometrics(trip)
    e = Engine(level=1)
    g.arm(e)
    report = g.tick()  # fear spike on the second reading
    assert isinstance(report, dict) and report["quiet"] is True
    assert report["reason"] and "spiked" in report["reason"]
    assert not e.is_armed, "box did not go quiet on trip"
    assert "too much" in report["farewell"]["message"]


def t_disable_trip_needs_admin():
    g = ready_box()
    trip = BiometricTrip(SimulatedCuff([(80, 0.1)]), clock=MonoClock())
    g.enable_biometrics(trip)
    expect_refused(g.disable_biometrics, "wrong-pin")
    assert g.disable_biometrics("admin-1234").startswith("Biometric trip")
    assert g._trip is None


TESTS = [
    ("manufacture runs once, weak secret refused", t_manufacture_once),
    ("setup needs 18+ attestation", t_setup_needs_18),
    ("setup validates days and PIN", t_setup_validates_days),
    ("box locked until Curtis approves", t_locked_until_curtis_approves),
    ("no backdoor: every mutator refuses pre-approval", t_no_backdoor_paths),
    ("forged approval code fails", t_forged_approval_fails),
    ("Curtis approval opens the box", t_curtis_approval_opens_box),
    ("approval token is single-use", t_approval_token_single_use),
    ("5 bad PINs trigger cooldown lockout", t_pin_lockout),
    ("failed attempts are logged, admin-only", t_failed_attempts_logged),
    ("level cap never above 2", t_level_cap_never_above_two),
    ("play days change is admin-only", t_days_change_admin_only),
    ("usage wipe is admin-only", t_clear_usage_admin_only),
    ("level 2 needs per-session consent", t_arm_level2_needs_consent),
    ("arm blocked by content cap", t_arm_blocked_by_cap),
    ("level 3 can never arm", t_arm_level3_impossible),
    ("time budget winds down gracefully", t_time_budget_and_winddown),
    ("wind-down works without save hook", t_winddown_without_save_hook),
    ("wrong day refused in plain language", t_wrong_day_refused),
    ("weekly reset restores budget", t_weekly_reset),
    ("status speaks plain language", t_status_plain_language),
    ("Curtis revoke locks the box", t_curtis_revoke_locks_box),
    ("new admin after revoke needs Curtis", t_revoke_then_new_admin_needs_curtis),
    ("kill switch works even unset up", t_kill_always_works),
    ("factory reset keeps manufacture", t_factory_reset_keeps_manufacture),
    ("factory reset needs admin or Curtis", t_factory_reset_needs_admin_or_curtis),
    ("state file is 0600", t_state_file_locked_down),
    ("state sealed on manufacture", t_state_sealed_on_manufacture),
    ("tampered state refuses to arm", t_tampered_state_refuses_arm),
    ("tamper recovery needs Curtis", t_tamper_recovery_needs_curtis),
    ("approval request expires after 24h", t_approval_request_expires),
    ("double arm refused", t_double_arm_refused),
    ("tick debits monotonic time", t_tick_debits_monotonic_time),
    ("record_play never below elapsed", t_record_play_never_below_elapsed),
    ("disarm debits and clears session", t_disarm_debits_and_clears),
    ("trip on sustained high heart rate", t_trip_sustained_high_hr),
    ("trip on fear spike", t_trip_fear_spike),
    ("trip on signal loss (fail-secure)", t_trip_signal_loss_fails_secure),
    ("no trip on normal excitement", t_no_trip_normal_excitement),
    ("arm refuses without cuff", t_arm_refuses_without_cuff),
    ("trip quiets the box", t_trip_quiets_the_box),
    ("disable trip needs admin", t_disable_trip_needs_admin),
]


def main():
    print("Pandora guardrails selftest -- %d tests" % len(TESTS))
    print("-" * 60)
    for name, fn in TESTS:
        check(name, fn)
    print("-" * 60)
    failed = [r for r in RESULTS if not r[1]]
    print("%d passed, %d failed" % (len(RESULTS) - len(failed), len(failed)))
    for name, _ok, err in failed:
        print("  FAILED: %s -- %s" % (name, err))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
