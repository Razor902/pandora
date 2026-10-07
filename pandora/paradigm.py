# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — NOT A PRODUCTION ACCESS SYSTEM.
# A classroom model of Curtis's paradigm laws for Pandora's Box. Demo
# sessions, demo profiles, a demo meter. The real hardware, the real
# registry, and the real administrator process are his to wire in.
# ============================================================================
"""The paradigm of Pandora's Box -- the laws built into the machine.

Curtis's laws (2026-10-07, his words, DECIDED):

    "Pandora's box can only be turned on by administrator access.
     Which is the parents."
    "It's rated 18 plus. M A."
    "It has a chaos meter."
    "Built into a Pandora is a paradigm with guardrails."
    "If it starts giving you too much of what you desire, then it starts
     telling you what you want to hear. And then it draws back from
     desire and goes back towards chaos. But if it gets too close to
     chaos, it automatically pulls back."
    "So there's no way you can get stuck in a virtual reality."
    "You can only play three hours a day three times a week."
    "Once you make your profile, you cannot delete it. Without
     administrative access." -- "And I solely am the only one that can
     approve of deleting an account."

The paradigm calls INTO the defense stack (guardrails, watchdog) when it
needs safety action, never around it, and never imports anything that
could weaken the guardrails.
"""

RATING = "Rated 18+ MA"

# The one and only approver of profile deletion, in his words.
CURTIS = "Curtis Ray Dyess"

# --- Chaos meter rails and edges --------------------------------------------
RAIL_LOW = 5        # the meter can never leave the rails
RAIL_HIGH = 95
EDGE_DESIRE = 10    # near the desire edge it draws back toward chaos
EDGE_CHAOS = 90     # near the chaos edge it automatically pulls back

# --- Session law --------------------------------------------------------------
MAX_MINUTES_PER_DAY = 180   # three hours a day
MAX_DAYS_PER_WEEK = 3       # three times a week


class ParadigmError(Exception):
    """Any refusal from the paradigm speaks plainly, and carries the rating."""


def _stamped(message):
    return "%s (%s)" % (message, RATING)


class PowerOn:
    """The box only powers on with administrator access. The parents hold it.

    No admin, no power. The refusal is plain and stamped.
    """

    def __init__(self):
        self.is_on = False

    def power_on(self, by_admin):
        """Turn the box on. by_admin must be True -- the parents' access."""
        if not by_admin:
            raise ParadigmError(_stamped(
                "The box does not wake without administrator access. "
                "The parents hold the key."))
        self.is_on = True
        return _stamped("The box wakes. The parents have spoken.")

    def power_off(self):
        self.is_on = False
        return _stamped("The box sleeps.")


class ChaosMeter:
    """The chaos meter: 0 is pure desire-gratification, 100 is pure chaos.

    His dynamics, encoded:
      - Too much of what you desire (high desire_level) and the box draws
        back from desire, toward chaos: "it starts telling you what you
        want to hear."
      - Near the chaos edge (>= 90) it AUTOMATICALLY pulls back.
      - Near the desire edge (<= 10) it draws back toward chaos.
      - Hard rails at 5 and 95: the meter physically cannot leave them.
    Result: the meter swings but never rests at an extreme -- there is no
    way to get stuck.
    """

    def __init__(self, start=50.0):
        self.meter = self._rail(float(start))
        self.log = []  # (tick_number, desire_level, meter_after)

    @staticmethod
    def _rail(value):
        return max(RAIL_LOW, min(RAIL_HIGH, value))

    def tick(self, desire_level):
        """Advance the meter one beat. desire_level is 0..100."""
        desire_level = max(0.0, min(100.0, float(desire_level)))

        if desire_level >= 70:
            # Too much of what you desire: draw back from desire, toward chaos.
            self.meter += 6.0
        elif desire_level <= 30:
            # Starved of gratification: drift back toward desire.
            self.meter -= 4.0
        # else: a neutral beat -- the meter holds its ground.

        if self.meter >= EDGE_CHAOS:
            # Too close to chaos: it automatically pulls back.
            self.meter -= 12.0
        elif self.meter <= EDGE_DESIRE:
            # Too close to pure desire: it draws back toward chaos.
            self.meter += 8.0

        self.meter = self._rail(self.meter)
        self.log.append((len(self.log) + 1, desire_level, self.meter))
        return self.meter

    def where(self):
        """Plain-words reading of the meter."""
        if self.meter >= EDGE_CHAOS:
            return "near chaos -- pulling back"
        if self.meter <= EDGE_DESIRE:
            return "near desire -- drawing back"
        return "in the swing -- neither stuck nor lost"


class SessionTracker:
    """The session law: three hours a day, three times a week.

    Sessions are logged by calendar day (YYYY-MM-DD). A day past 180
    minutes, or a fourth distinct day in one ISO week, is refused in
    plain words: "The box rests. Come back tomorrow."
    """

    def __init__(self):
        self.days = {}  # date string -> minutes used

    @staticmethod
    def _week_of(date):
        from datetime import date as _date
        y, m, d = int(date[0:4]), int(date[5:7]), int(date[8:10])
        return _date(y, m, d).isocalendar()[1]

    def can_play(self, date, minutes):
        """Ask first. Returns (ok, reason)."""
        minutes = int(minutes)
        used = self.days.get(date, 0)
        if used + minutes > MAX_MINUTES_PER_DAY:
            return (False, _stamped(
                "The box rests. Three hours a day is the law; "
                "come back tomorrow."))
        week = self._week_of(date)
        distinct_days = sum(
            1 for d in self.days if self._week_of(d) == week and self.days[d] > 0)
        if date not in self.days and distinct_days >= MAX_DAYS_PER_WEEK:
            return (False, _stamped(
                "The box rests. Three times a week is the law; "
                "come back next week."))
        return (True, _stamped("The gates are open. Play well."))

    def log_session(self, date, minutes):
        """Log a session. Refuses (raises) past the law."""
        ok, reason = self.can_play(date, minutes)
        if not ok:
            raise ParadigmError(reason)
        self.days[date] = self.days.get(date, 0) + int(minutes)
        return _stamped("Session written: %s, %d minutes." % (date, int(minutes)))


class ProfileRegistry:
    """Profiles are permanent. Creation is forever; deletion needs two keys.

    His law: "Once you make your profile, you cannot delete it. Without
    administrative access." -- "And I solely am the only one that can
    approve of deleting an account."

    delete_profile(name, by_admin, approved_by): refused unless by_admin is
    True AND approved_by is exactly "Curtis Ray Dyess". No one else can
    approve. Ever.
    """

    def __init__(self):
        self.profiles = set()

    def create_profile(self, name):
        self.profiles.add(name)
        return _stamped("Profile '%s' is made. It does not unmake." % name)

    def has_profile(self, name):
        return name in self.profiles

    def delete_profile(self, name, by_admin=False, approved_by=None):
        if name not in self.profiles:
            raise ParadigmError(_stamped(
                "There is no profile '%s' to delete." % name))
        if not by_admin:
            raise ParadigmError(_stamped(
                "Profiles do not delete without administrator access."))
        if approved_by != CURTIS:
            raise ParadigmError(_stamped(
                "Only Curtis Ray Dyess can approve the deleting of an "
                "account. No one else."))
        self.profiles.discard(name)
        return _stamped("Profile '%s' is released, by his hand alone." % name)


def demo():
    """Walk the paradigm through its paces, in plain words."""
    print("== POWER ==")
    box = PowerOn()
    try:
        box.power_on(by_admin=False)
    except ParadigmError as e:
        print("refused:", e)
    print(box.power_on(by_admin=True))

    print("== CHAOS METER ==")
    meter = ChaosMeter()
    print("Too much desire for 30 beats...")
    for _ in range(30):
        meter.tick(100)
    print("meter after desire flood:", round(meter.meter, 1), "--", meter.where())
    print("Starved of desire for 30 beats...")
    for _ in range(30):
        meter.tick(0)
    print("meter after starvation:", round(meter.meter, 1), "--", meter.where())
    print("never left the rails:", all(RAIL_LOW <= m <= RAIL_HIGH
                                      for _, _, m in meter.log))

    print("== SESSIONS ==")
    sessions = SessionTracker()
    print(sessions.log_session("2026-10-05", 180))
    print(sessions.log_session("2026-10-07", 180))
    print(sessions.log_session("2026-10-09", 180))
    try:
        sessions.log_session("2026-10-11", 60)
    except ParadigmError as e:
        print("refused:", e)

    print("== PROFILES ==")
    registry = ProfileRegistry()
    print(registry.create_profile("citizen-one"))
    try:
        registry.delete_profile("citizen-one", by_admin=True,
                                approved_by="Someone Else")
    except ParadigmError as e:
        print("refused:", e)
    print(registry.delete_profile("citizen-one", by_admin=True,
                                  approved_by="Curtis Ray Dyess"))


if __name__ == "__main__":
    demo()
