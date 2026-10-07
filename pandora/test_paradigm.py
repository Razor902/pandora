# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Tests for the paradigm -- Curtis's laws, encoded and verified."""
import unittest

from .paradigm import (
    PowerOn, ChaosMeter, SessionTracker, ProfileRegistry, ParadigmError,
    RATING, CURTIS, RAIL_LOW, RAIL_HIGH, EDGE_CHAOS, EDGE_DESIRE,
)


class TestPowerOn(unittest.TestCase):
    def test_no_admin_refused(self):
        box = PowerOn()
        with self.assertRaises(ParadigmError) as ctx:
            box.power_on(by_admin=False)
        self.assertIn(RATING, str(ctx.exception))
        self.assertFalse(box.is_on)

    def test_admin_powers_on(self):
        box = PowerOn()
        msg = box.power_on(by_admin=True)
        self.assertTrue(box.is_on)
        self.assertIn(RATING, msg)


class TestChaosMeter(unittest.TestCase):
    def test_desire_pushes_toward_chaos(self):
        m = ChaosMeter(start=50.0)
        before = m.meter
        m.tick(100)
        self.assertGreater(m.meter, before)

    def test_chaos_edge_auto_pulls_back(self):
        m = ChaosMeter(start=89.0)
        m.tick(100)  # 89 + 6 = 95 -> >= 90 edge -> -12 -> 83
        self.assertLess(m.meter, 89.0)
        self.assertEqual(m.where(), "in the swing -- neither stuck nor lost")

    def test_desire_edge_draws_back_toward_chaos(self):
        m = ChaosMeter(start=11.0)
        m.tick(0)  # 11 - 4 = 7 -> <= 10 edge -> +8 -> 15
        self.assertGreater(m.meter, 11.0)

    def test_never_sticks_at_extremes(self):
        m = ChaosMeter(start=50.0)
        for _ in range(200):
            m.tick(100)
        self.assertLess(m.meter, EDGE_CHAOS)
        for _ in range(200):
            m.tick(0)
        self.assertGreater(m.meter, EDGE_DESIRE)

    def test_hard_rails(self):
        m = ChaosMeter(start=50.0)
        for level in (0, 100, 50, 70, 30):
            for _ in range(100):
                m.tick(level)
                self.assertGreaterEqual(m.meter, RAIL_LOW)
                self.assertLessEqual(m.meter, RAIL_HIGH)

    def test_where_speaks_plainly(self):
        m = ChaosMeter(start=95.0)
        self.assertIn("chaos", m.where())
        m = ChaosMeter(start=5.0)
        self.assertIn("desire", m.where())


class TestSessionTracker(unittest.TestCase):
    def test_three_days_ok_fourth_refused(self):
        s = SessionTracker()
        s.log_session("2026-10-05", 60)  # Monday
        s.log_session("2026-10-07", 60)  # Wednesday
        s.log_session("2026-10-09", 60)  # Friday
        with self.assertRaises(ParadigmError) as ctx:
            s.log_session("2026-10-11", 60)  # Sunday, same ISO week
        self.assertIn(RATING, str(ctx.exception))
        self.assertIn("rests", str(ctx.exception))

    def test_three_hours_plus_one_minute_refused(self):
        s = SessionTracker()
        s.log_session("2026-10-05", 180)
        with self.assertRaises(ParadigmError) as ctx:
            s.log_session("2026-10-05", 1)
        self.assertIn("Three hours", str(ctx.exception))

    def test_new_week_resets(self):
        s = SessionTracker()
        s.log_session("2026-10-05", 60)
        s.log_session("2026-10-07", 60)
        s.log_session("2026-10-09", 60)
        # Next ISO week: the law opens again.
        s.log_session("2026-10-12", 60)

    def test_can_play_asks_first(self):
        s = SessionTracker()
        ok, reason = s.can_play("2026-10-05", 60)
        self.assertTrue(ok)
        self.assertIn(RATING, reason)


class TestProfileRegistry(unittest.TestCase):
    def test_create_is_permanent_by_default(self):
        r = ProfileRegistry()
        r.create_profile("citizen-one")
        self.assertTrue(r.has_profile("citizen-one"))

    def test_delete_without_admin_refused(self):
        r = ProfileRegistry()
        r.create_profile("citizen-one")
        with self.assertRaises(ParadigmError) as ctx:
            r.delete_profile("citizen-one", by_admin=False,
                             approved_by=CURTIS)
        self.assertTrue(r.has_profile("citizen-one"))
        self.assertIn(RATING, str(ctx.exception))

    def test_delete_without_curtis_approval_refused(self):
        r = ProfileRegistry()
        r.create_profile("citizen-one")
        for imposter in ("Admin", "Curtis", "curtis ray dyess", None, ""):
            with self.assertRaises(ParadigmError):
                r.delete_profile("citizen-one", by_admin=True,
                                 approved_by=imposter)
        self.assertTrue(r.has_profile("citizen-one"))

    def test_delete_with_curtis_approval_allowed(self):
        r = ProfileRegistry()
        r.create_profile("citizen-one")
        msg = r.delete_profile("citizen-one", by_admin=True,
                               approved_by="Curtis Ray Dyess")
        self.assertFalse(r.has_profile("citizen-one"))
        self.assertIn(RATING, msg)

    def test_delete_unknown_profile_refused(self):
        r = ProfileRegistry()
        with self.assertRaises(ParadigmError):
            r.delete_profile("ghost", by_admin=True, approved_by=CURTIS)


if __name__ == "__main__":
    unittest.main()
