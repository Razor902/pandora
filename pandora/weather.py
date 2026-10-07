# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — NOT A PRODUCTION WEATHER SYSTEM.
# A classroom model of Curtis's weather law for Pandora's Box. The demo
# provider returns honest sample data; the live provider is a documented
# wiring point with no keys and no network calls. The box's sky is always
# DERIVED from the citizen's sky, never invented.
# ============================================================================
"""The weather inside Pandora's Box -- borrowed from the citizen's sky.

Curtis's law (2026-10-07, his words):
    "The weather inside of the box depends on the weather in your area,
    in your time zone, and in your country."

The idea: the box's inner world breathes with the outer world. Rain where
the citizen stands means rain inside the box. Dawn in their timezone means
dawn inside. The box never has weather of its own -- it borrows the
citizen's sky.

Three ingredients go in, one sky comes out:
    area      -- where the citizen stands (a place name, plain words)
    timezone  -- their timezone (for local hour: dawn/day/dusk/night)
    country   -- their country (kept on the record with the reading)

The law, encoded: inside weather is DERIVED, never invented. If no outside
data can be fetched, the box says "the sky is waiting" -- an honest
fallback, never a fake forecast.
"""

# ---------------------------------------------------------------------------
# The provider interface.
# fetch_weather(area, timezone, country) -> dict or None.
# The dict carries: condition, temp_f, humidity_pct, wind_mph, source.
# None means the fetch failed -- the caller falls back honestly.
# ---------------------------------------------------------------------------

def demo_provider(area, timezone, country):
    """Honest sample data, clearly labeled DEMO. Runs offline, always.

    This is a stand-in, not a forecast. Every reading it returns says
    DEMO on it, so nobody mistakes the classroom for the sky.
    """
    return {
        "condition": "rain",
        "temp_f": 68.0,
        "humidity_pct": 82,
        "wind_mph": 9.0,
        "area": area,
        "timezone": timezone,
        "country": country,
        "source": "DEMO -- sample data, not a real forecast",
    }


def live_provider(area, timezone, country):
    """WIRING POINT for a real weather API. Not connected in this build.

    To go live, Curtis (or his engineer) wires this function to a weather
    service: take area/timezone/country, call the service, and return the
    same dict shape demo_provider returns -- condition, temp_f,
    humidity_pct, wind_mph -- with source naming the service.

    No API keys live here. No network calls happen here. This stub raises
    in plain words so a half-wired box can never fake a forecast.
    """
    raise NotImplementedError(
        "live_provider is a wiring point, not a connection. "
        "No weather API is configured and no keys are stored here. "
        "Wire a real service (returning condition/temp_f/humidity_pct/"
        "wind_mph) to make the box read the live sky."
    )


# ---------------------------------------------------------------------------
# The mapping table: outside condition -> the box's poetic register.
# The box speaks its own weather words, but every word is DERIVED from
# the outside reading beside it. Unknown conditions map to "strange sky"
# rather than being guessed at.
# ---------------------------------------------------------------------------

CONDITION_MAP = {
    "clear": "open sky",
    "sunny": "open sky",
    "partly cloudy": "wandering clouds",
    "cloudy": "soft gray",
    "overcast": "soft gray",
    "rain": "soft rain",
    "drizzle": "soft rain",
    "showers": "soft rain",
    "thunderstorm": "distant thunder",
    "storm": "distant thunder",
    "snow": "quiet snow",
    "sleet": "quiet snow",
    "fog": "low mist",
    "mist": "low mist",
    "haze": "low mist",
    "windy": "high wind",
}


def map_condition(outside_condition):
    """Translate an outside condition into the box's weather words."""
    key = (outside_condition or "").strip().lower()
    return CONDITION_MAP.get(key, "strange sky")


# ---------------------------------------------------------------------------
# Daylight: the box keeps the citizen's time.
# Dawn 05-07, day 07-17, dusk 17-19, night otherwise. The edges belong to
# the earlier phase (hour 7 is day, hour 17 is dusk, hour 19 is night).
# ---------------------------------------------------------------------------

def daylight_phase(local_hour):
    """Name the phase of day inside the box from the citizen's local hour."""
    h = int(local_hour) % 24
    if 5 <= h < 7:
        return "dawn"
    if 7 <= h < 17:
        return "day"
    if 17 <= h < 19:
        return "dusk"
    return "night"


# ---------------------------------------------------------------------------
# The inside weather: derived from outside, never invented.
# ---------------------------------------------------------------------------

def inside_weather(outside, local_hour):
    """Compute the inside weather from an outside reading + local hour.

    outside: dict with condition, temp_f, humidity_pct, wind_mph (any may
    be missing -- the box carries what it was given and says nothing
    about what it wasn't).
    Returns a dict describing the box's sky.
    """
    condition = map_condition(outside.get("condition"))
    phase = daylight_phase(local_hour)
    return {
        "inside_condition": condition,
        "daylight": phase,
        "temp_f": outside.get("temp_f"),
        "humidity_pct": outside.get("humidity_pct"),
        "wind_mph": outside.get("wind_mph"),
        "derived_from": outside.get("condition"),
        "source": outside.get("source", "unknown source"),
    }


def describe_inside(area, timezone, country, local_hour, provider=demo_provider):
    """One plain-words paragraph: what the citizen feels stepping in.

    Fetches the outside weather through the provider, derives the inside
    sky, and describes it. If the provider fails, the box says the sky
    is waiting -- honestly, never inventing.
    """
    try:
        outside = provider(area, timezone, country)
    except Exception:
        outside = None
    if not outside:
        return ("You step in, and the sky is waiting. The box could not read "
                "the weather over %s, so it shows you no sky at all rather "
                "than a false one." % area)

    inside = inside_weather(outside, local_hour)
    bits = []
    bits.append("You step in at %s." % inside["daylight"])
    bits.append("Inside, %s -- the same sky as over %s."
                % (inside["inside_condition"], area))
    if inside["temp_f"] is not None:
        bits.append("It holds your afternoon's warmth: about %.0f degrees."
                    % inside["temp_f"])
    if inside["wind_mph"] is not None and inside["wind_mph"] >= 15:
        bits.append("The wind moves through it the way it moves through your county.")
    bits.append("The box borrows your sky; it keeps none of its own.")
    return " ".join(bits)


# ---------------------------------------------------------------------------
# Demo walkthrough: python3 weather.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(describe_inside("Ruston", "America/Chicago", "USA", 18))
    print()
    print(describe_inside("Ruston", "America/Chicago", "USA", 18,
                           provider=lambda a, t, c: None))
