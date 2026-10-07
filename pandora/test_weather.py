# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY. Tests for the classroom weather model.
# Run:  cd ~/workspace/arcade && python3 -m pandora.test_weather
# ============================================================================
"""Tests for weather.py -- Curtis's weather law, encoded and checked."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pandora import weather as w


def check(name, cond):
    print("[%s] %s" % ("ok " if cond else "FAIL", name))
    if not cond:
        raise SystemExit("FAILED: " + name)


def fake_provider(condition):
    def _p(area, timezone, country):
        return {"condition": condition, "temp_f": 70.0, "humidity_pct": 50,
                "wind_mph": 5.0, "area": area, "timezone": timezone,
                "country": country, "source": "TEST"}
    return _p


def main():
    # 1. Mapping table coverage: every known outside -> inside words.
    pairs = [("clear", "open sky"), ("sunny", "open sky"),
             ("partly cloudy", "wandering clouds"),
             ("cloudy", "soft gray"), ("overcast", "soft gray"),
             ("rain", "soft rain"), ("drizzle", "soft rain"),
             ("thunderstorm", "distant thunder"), ("storm", "distant thunder"),
             ("snow", "quiet snow"), ("sleet", "quiet snow"),
             ("fog", "low mist"), ("mist", "low mist"),
             ("windy", "high wind")]
    for outside, inside in pairs:
        check("map %r -> %r" % (outside, inside),
              w.map_condition(outside) == inside)
    check("unknown condition -> strange sky",
          w.map_condition("volcanic ash") == "strange sky")
    check("empty condition -> strange sky", w.map_condition("") == "strange sky")
    check("case-insensitive", w.map_condition("RAIN") == "soft rain")

    # 2. Daylight boundaries.
    check("05 is dawn", w.daylight_phase(5) == "dawn")
    check("06 is dawn", w.daylight_phase(6) == "dawn")
    check("07 is day (edge to day)", w.daylight_phase(7) == "day")
    check("12 is day", w.daylight_phase(12) == "day")
    check("16 is day", w.daylight_phase(16) == "day")
    check("17 is dusk (edge to dusk)", w.daylight_phase(17) == "dusk")
    check("18 is dusk", w.daylight_phase(18) == "dusk")
    check("19 is night (edge to night)", w.daylight_phase(19) == "night")
    check("23 is night", w.daylight_phase(23) == "night")
    check("00 is night", w.daylight_phase(0) == "night")
    check("04 is night", w.daylight_phase(4) == "night")

    # 3. Inside weather is derived, never invented.
    out = {"condition": "rain", "temp_f": 68.0, "humidity_pct": 82,
           "wind_mph": 9.0, "source": "TEST"}
    iw = w.inside_weather(out, 18)
    check("inside condition derived", iw["inside_condition"] == "soft rain")
    check("daylight from hour", iw["daylight"] == "dusk")
    check("derived_from names the outside", iw["derived_from"] == "rain")

    # 4. describe_inside mentions the area's real condition.
    desc = w.describe_inside("Homer", "America/Chicago", "USA", 9,
                             provider=fake_provider("snow"))
    check("mentions area", "Homer" in desc)
    check("mentions inside words", "quiet snow" in desc)
    check("mentions daylight", "day" in desc)

    # 5. Fallback when the provider fails: honest, never a fake forecast.
    desc_none = w.describe_inside("Homer", "America/Chicago", "USA", 9,
                                  provider=lambda a, t, c: None)
    check("fallback says waiting", "waiting" in desc_none)
    check("fallback names area", "Homer" in desc_none)

    def boom(a, t, c):
        raise RuntimeError("network down")
    desc_boom = w.describe_inside("Homer", "America/Chicago", "USA", 9,
                                  provider=boom)
    check("exception -> fallback too", "waiting" in desc_boom)

    # 6. live_provider is a wiring point, not a connection.
    try:
        w.live_provider("Homer", "America/Chicago", "USA")
        check("live_provider raises", False)
    except NotImplementedError as e:
        check("live_provider raises plainly", "wiring point" in str(e))

    # 7. demo_provider is honest about what it is.
    d = w.demo_provider("Homer", "America/Chicago", "USA")
    check("demo labels itself", "DEMO" in d["source"])

    print("\nAll weather tests passed.")


if __name__ == "__main__":
    main()
