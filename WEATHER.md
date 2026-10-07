# The Weather Inside Pandora's Box

**Curtis's law (2026-10-07, his words):** *"The weather inside of the box
depends on the weather in your area, in your time zone, and in your country."*

## The idea, plainly

The box's inner world breathes with the outer world. Rain where the citizen
stands means rain inside the box. Dawn in their timezone means dawn inside.
The box never has weather of its own — it borrows the citizen's sky.

## How it works

1. **Fetch** — `fetch_weather(area, timezone, country)` reads the outside
   sky through a provider. Two ship with the module:
   - `demo_provider`: honest sample data, every reading labeled DEMO.
     Runs offline, always.
   - `live_provider`: a documented wiring point for a real weather API.
     No keys, no network calls — it raises in plain words until a real
     service is wired in.
2. **Translate** — the outside condition becomes the box's weather words
   (`CONDITION_MAP`): rain → "soft rain", thunderstorm → "distant
   thunder", snow → "quiet snow", fog → "low mist", clear → "open sky".
   Unknown conditions become "strange sky" — never guessed at.
3. **Time** — the citizen's local hour sets the phase: dawn (05–07),
   day (07–17), dusk (17–19), night otherwise.
4. **Describe** — `describe_inside()` speaks one plain paragraph: what the
   citizen feels stepping in.

## The honest fallback

Inside weather is DERIVED, never invented. If no outside data can be
fetched, the box says *"the sky is waiting"* — no sky at all rather than
a false one.

## Limits

- Classroom model: the demo sky is sample data, not a forecast.
- Going live means wiring `live_provider` to a real weather service and
  holding the API key outside this module.
- The box borrows the sky; it does not change it.

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
