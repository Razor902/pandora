# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora DLC core selftest — headless.

Verifies the safety contract: clean attach/detach, default disarmed,
gating, kill switch, and that no level-1/2 effect can startle, flash,
or crash. Prints PASS/FAIL per test; exits nonzero on any failure.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pandora import Engine, armed, __version__
from pandora import atmosphere, dread
from pandora.atmosphere import _split

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print("PASS: %s" % name)
    except Exception as e:  # noqa: BLE001 - selftest must catch everything
        RESULTS.append((name, False, "%s: %s" % (type(e).__name__, e)))
        print("FAIL: %s -- %s: %s" % (name, type(e).__name__, e))


# ---------------------------------------------------------------------------
# fake game + buffer helpers
# ---------------------------------------------------------------------------

class FakeGame:
    """A small stand-in game. update/render are instance attributes so the
    attach/detach identity check is meaningful."""

    def __init__(self, h=12, w=40):
        self.h = h
        self.w = w
        self.update_calls = []
        self.update = self._do_update
        self.render = self._do_render

    def _do_update(self, dt):
        self.update_calls.append(dt)

    def _do_render(self, buf):
        slots = ["normal", "bright_green", "VIOLET", "white", "gold", 7]
        for ri in range(min(self.h, len(buf))):
            row = buf[ri]
            for ci in range(min(self.w, len(row))):
                if (ri + ci) % 5 == 0:
                    ch = " "
                else:
                    ch = chr(ord("a") + (ri + ci) % 26)
                bold = (ri + ci) % 4 == 0
                slot = slots[(ri * 7 + ci) % len(slots)]
                row[ci] = (ch, slot, bold)
        # odd cell shapes the effects must survive
        if len(buf) > 3 and len(buf[3]) > 3:
            buf[0][0] = "X"        # bare string
            buf[1][1] = 42         # not a cell at all
            buf[2][2] = None       # nothing
            buf[3][3] = ("z",)     # 1-tuple
        return buf


def make_buffer(h=12, w=40):
    return [[(" ", "normal", False) for _ in range(w)] for _ in range(h)]


def fill(game, buf):
    return game.render(buf)


def buffers_equal(a, b):
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        for ca, cb in zip(ra, rb):
            if ca != cb:
                return False
    return True


def brightness(cell):
    """Score a cell's brightness. Effects at levels 1-2 may only lower it."""
    parts = _split(cell)
    if not parts:
        return 0
    ch, _slot, bold = parts
    return (1 if ch.strip() else 0) + (1 if bold else 0)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def t_version():
    assert __version__ == "0.3.0", __version__


def t_attach_detach_identity():
    g = FakeGame()
    e = Engine(level=1)
    orig_u, orig_r = g.update, g.render
    e.attach(g)
    assert g.update is not orig_u and g.render is not orig_r
    assert e.is_attached
    e.detach()
    assert g.update is orig_u, "update not restored by identity"
    assert g.render is orig_r, "render not restored by identity"
    assert not e.is_attached


def t_default_disarmed():
    g1, g2 = FakeGame(), FakeGame()
    e = Engine(level=2)
    e.attach(g1)  # attached but never armed
    b1, b2 = make_buffer(), make_buffer()
    g1.update(0.016)
    g2.update(0.016)
    r1, r2 = g1.render(b1), g2.render(b2)
    assert buffers_equal(r1, r2), "disarmed engine changed the render"
    assert g1.update_calls == g2.update_calls == [0.016]
    e.detach()


def t_arm_disarm_toggle():
    g = FakeGame()
    e = Engine(level=2)
    e.attach(g)
    baseline = fill(g, make_buffer())
    e.arm()
    assert e.is_armed
    e.tension = 1.0
    changed = False
    for _ in range(40):
        g.update(0.016)
        if not buffers_equal(g.render(make_buffer()), baseline):
            changed = True
            break
    assert changed, "armed engine produced no visible effect"
    e.disarm()
    assert not e.is_armed
    assert buffers_equal(fill(g, make_buffer()), baseline), \
        "disarmed render differs from original"
    e.detach()


def t_double_attach_raises():
    g = FakeGame()
    e = Engine()
    e.attach(g)
    try:
        e.attach(g)
        raise AssertionError("double attach did not raise")
    except RuntimeError:
        pass
    finally:
        e.detach()


def t_detach_without_attach_raises():
    e = Engine()
    try:
        e.detach()
        raise AssertionError("detach without attach did not raise")
    except RuntimeError:
        pass


def t_invalid_level():
    for bad in (0, 3, -1, "1", None, 1.5):
        try:
            Engine(level=bad)
            raise AssertionError("level %r accepted" % (bad,))
        except ValueError:
            pass


def t_no_escalation():
    e = Engine(level=1)
    try:
        e.level = 2
        raise AssertionError("level escalation allowed")
    except ValueError:
        pass
    e.level = 1  # same level: fine
    assert e.level == 1
    e2 = Engine(level=2)
    e2.level = 1  # de-escalation is safe
    assert e2.level == 1


def t_tension_clamp():
    e = Engine()
    e.tension = 2.0
    assert e.tension == 1.0
    e.tension = -5
    assert e.tension == 0.0
    e.tension = 0.7
    assert e.tension == 0.7
    try:
        e.tension = "high"
        raise AssertionError("non-numeric tension accepted")
    except TypeError:
        pass


def t_kill():
    g = FakeGame()
    e = Engine(level=2)
    orig_u, orig_r = g.update, g.render
    e.attach(g)
    e.arm()
    e.tension = 0.9
    e.kill()
    assert g.update is orig_u and g.render is orig_r
    assert not e.is_attached and not e.is_armed
    e.kill()  # kill when not attached: still safe


def t_effects_no_crash():
    fns = [atmosphere.palette_drain, atmosphere.flicker_dim,
           atmosphere.vignette_creep, atmosphere.text_rot, atmosphere.drone,
           dread.presence, dread.pursuit_cues, dread.heartbeat]
    g = FakeGame()
    for fn in fns:
        for tension in (0.0, 0.5, 1.0):
            for tick in (0, 30, 200):
                buf = fill(g, make_buffer())
                out = fn(buf, 12, 40, tension, tick)
                assert out is not None
    # ragged buffer with odd shapes and empty buffer
    nasty = [[("a", "white", True), "s", 7], [], "notarow", [("b",)]]
    empty = []
    for fn in fns:
        fn(nasty, 4, 2, 1.0, 99)
        fn(empty, 0, 0, 1.0, 99)


def t_flicker_never_brightens():
    g = FakeGame()
    for tension in (0.5, 1.0):
        for tick in range(0, 210, 7):
            buf = fill(g, make_buffer())
            out = atmosphere.flicker_dim(buf, 12, 40, tension, tick)
            lit_in = lit_out = 0
            for ri in range(12):
                for ci in range(40):
                    bi, bo = brightness(buf[ri][ci]), brightness(out[ri][ci])
                    assert bo <= bi, \
                        "flicker brightened cell (%d,%d) at tick %d" % (ri, ci, tick)
                    lit_in += 1 if bi else 0
                    lit_out += 1 if bo else 0
            assert lit_out >= 0.5 * lit_in, \
                "flicker dimmed too far at tick %d (%.2f left)" % (
                    tick, lit_out / max(lit_in, 1))


def t_presence_edges_only():
    g = FakeGame()
    h, w = 12, 40
    buf = fill(g, make_buffer())
    out = dread.presence(buf, h, w, 1.0, 500)
    changed = []
    for ri in range(h):
        for ci in range(w):
            if out[ri][ci] != buf[ri][ci]:
                changed.append((ri, ci))
    assert changed, "presence changed nothing at full fade"
    for ri, ci in changed:
        edge = ri < 2 or ri >= h - 2 or ci < 3 or ci >= w - 3
        assert edge, "presence touched center cell (%d,%d)" % (ri, ci)
    # before the fade, nothing changes
    out0 = dread.presence(fill(g, make_buffer()), h, w, 1.0, 0)
    assert buffers_equal(out0, fill(g, make_buffer()))


def t_armed_context_manager():
    g = FakeGame()
    orig_u, orig_r = g.update, g.render
    with armed(g, level=2) as eng:
        assert eng.is_attached and eng.is_armed and eng.level == 2
        eng.tension = 0.5
        g.update(0.016)
        g.render(make_buffer())
    assert g.update is orig_u and g.render is orig_r
    assert not eng.is_attached
    # exception inside still cleans up
    g2 = FakeGame()
    ou, orr = g2.update, g2.render
    try:
        with armed(g2):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert g2.update is ou and g2.render is orr


def t_attach_typeerror():
    e = Engine()
    for bad in (object(), 42, "game"):
        try:
            e.attach(bad)
            raise AssertionError("attach(%r) did not raise" % (bad,))
        except TypeError:
            pass

    class OnlyUpdate:
        def update(self, dt):
            pass

    try:
        e.attach(OnlyUpdate())
        raise AssertionError("attach without render did not raise")
    except TypeError:
        pass


def t_drone_pattern():
    p = atmosphere.drone_pattern(0.7, 10)
    assert p["type"] == "drone"
    assert 0.0 <= p["intensity"] <= 1.0
    assert p["interval_ms"] > 0 and p["pulse_ms"] > 0
    g = FakeGame()
    buf = fill(g, make_buffer())
    assert atmosphere.drone(buf, 12, 40, 1.0, 99) is buf, \
        "drone must pass the buffer through untouched"


def t_chain_levels():
    assert len(Engine(level=1)._chain()) == 4, "level 1 must run 4 effects"
    assert len(Engine(level=2)._chain()) == 7, "level 2 must run 7 effects"


TESTS = [
    ("version exports", t_version),
    ("attach/detach restores method identity", t_attach_detach_identity),
    ("default state is disarmed", t_default_disarmed),
    ("arm/disarm toggling", t_arm_disarm_toggle),
    ("double attach raises RuntimeError", t_double_attach_raises),
    ("detach without attach raises RuntimeError", t_detach_without_attach_raises),
    ("invalid level raises ValueError", t_invalid_level),
    ("level can never be escalated", t_no_escalation),
    ("tension clamps to 0.0-1.0", t_tension_clamp),
    ("kill() disarms and detaches", t_kill),
    ("all effects run without crashing", t_effects_no_crash),
    ("flicker_dim never brightens", t_flicker_never_brightens),
    ("presence stays on the edges", t_presence_edges_only),
    ("armed() context manager cleans up", t_armed_context_manager),
    ("attach rejects bad games with TypeError", t_attach_typeerror),
    ("drone returns data, never executes", t_drone_pattern),
    ("effect chain matches level", t_chain_levels),
]


def main():
    print("Pandora DLC core selftest -- %d tests" % len(TESTS))
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
