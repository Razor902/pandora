# World Infrastructure — Warcraft's Server Craft, Rebuilt for the Box

**Curtis's order (2026-10-08):** research World of Warcraft's infrastructure, and put its ideas in Pandora's world layout. Make it live.

## The idea, in plain words

World of Warcraft doesn't run one world on one machine. It runs **realms** (whole copies of the world, each with its own people), puts each **continent on its own servers**, spins up private **instances** (dungeons) per party, and **shards** crowded zones — splitting one zone into several copies so no crowd breaks it. Pandora's world infrastructure works the same way, rebuilt on the box's own law: **everything is math from seeds. Nothing is stored.**

## How it maps

| Warcraft | Pandora | The difference |
|---|---|---|
| Realm | A named world (seed phrase) | The world is recomputed from the name, not stored on disk |
| Continent servers | Zones (Harbor, Plains, Forest, Highlands, Deep, Sky) | Each zone tracks who's there; terrain stays math |
| Sharding | Zones split past 40 visitors | Same zone, N copies, visitors dealt by hash of name |
| Instance servers | Trial instances per party | Same party + trial always rebuilds the same instance |
| Realm list | The Directory | What's open, how full, where a newcomer should walk in |
| Auth servers | The three gates | Proof of self, mandala, SAFE — already the box's law |

## The law of it

- **Nola's law binds it all.** No faked presence, no botted population counts. The census is honest or it is nothing.
- **Deterministic.** Same phrase, same realm. Same visitor, same shard. Same party and trial, same instance. Forever.
- **The meter still rules.** Ranks advance by weeks, not hours — infrastructure never lets anyone grind past the law of the ladder.

## Try it live

```python
from pandora import worldinfra
d = worldinfra.Directory()
tuga = d.register("Tuga Hollow")
tuga.enter("wren", "Plains")          # returns (zone, shard)
tuga.open_instance("decipher-trial", ["wren", "paul"])
print(tuga.status())
```

Or run the live demo: `python3 pandora/demo_live.py`

---

© 2026 Curtis Ray Dyess · Crimson Rose LLC
