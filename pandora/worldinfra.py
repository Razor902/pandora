# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""WORLD INFRASTRUCTURE — how Pandora holds many worlds at once.

Borrowed from World of Warcraft's server architecture, rebuilt for Pandora:

- REALM: one named world (a seed phrase). Like a WoW realm — its own copy
  of the world, its own people. Cheap here: the world is math, not storage.
- ZONE: one region of a realm. WoW ran each continent on its own hardware;
  we run each zone as its own roster of who's there. Terrain stays math.
- SHARD: when a zone gets crowded, it splits. Same zone, N copies, visitors
  dealt out by hash of their name. WoW's sharding, same idea, same honesty.
- INSTANCE: a private copy of a trial for one party. Deterministic: same
  party plus same trial always rebuilds the same instance. Nothing stored.
- DIRECTORY: the realm list. What's open, how full, where to go.

House rules:
- Nola's law binds it all: no faked presence, no botted population counts.
- Everything derives from seeds. The infrastructure is math, not memory.
- stdlib only.
"""

import hashlib
import math

from pandora import procgen

_SHARD_CAP = 40  # visitors per shard before a zone splits, WoW-style


def _h(*parts):
    """One deterministic hex digest from the parts given."""
    text = "|".join(str(p) for p in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hi(hexstr, mod):
    """A deterministic integer in range(mod) from a hex digest."""
    return int(hexstr, 16) % mod


# The zone roster every realm grows. Names are fixed; character comes from seed.
_ZONE_NAMES = ("Harbor", "Plains", "Forest", "Highlands", "Deep", "Sky")


class Zone:
    """One region of a realm. Tracks who's there; terrain stays in procgen."""

    def __init__(self, realm, name, index):
        self.realm = realm
        self.name = name
        # The zone's own sub-seed: same realm + same zone, forever the same.
        self.seed = procgen.world_seed(realm.phrase + ":" + name)
        self.index = index
        self.visitors = set()

    def join(self, visitor):
        self.visitors.add(visitor)

    def leave(self, visitor):
        self.visitors.discard(visitor)

    @property
    def population(self):
        return len(self.visitors)

    @property
    def shards(self):
        """How many copies of this zone are running. Grows with crowd."""
        return max(1, math.ceil(self.population / _SHARD_CAP))

    def shard_for(self, visitor):
        """Which shard a visitor lands on. Deterministic, stable per visitor."""
        return _hi(_h("shard", self.realm.seed, self.name, visitor), self.shards)

    def census(self):
        """Shard -> visitor count. The honest population, per shard."""
        counts = {i: 0 for i in range(self.shards)}
        for v in self.visitors:
            counts[self.shard_for(v)] += 1
        return counts


class Instance:
    """A private trial copy for one party. Same party + trial = same instance."""

    def __init__(self, realm, trial, party):
        self.realm = realm
        self.trial = trial
        self.party = tuple(sorted(party))
        self.instance_id = _h("instance", realm.seed, trial, ",".join(self.party))[:16]
        # The instance's own world seed: deterministic, private to the party.
        self.seed = procgen.world_seed(realm.phrase + ":instance:" + self.instance_id)

    def describe(self):
        return (f"Instance {self.instance_id} of '{self.trial}' "
                f"in {self.realm.phrase} for {', '.join(self.party)}")


class Realm:
    """One named world. A seed phrase, its zones, its people."""

    def __init__(self, phrase):
        self.phrase = phrase
        self.seed = procgen.world_seed(phrase)
        self.zones = {name: Zone(self, name, i)
                      for i, name in enumerate(_ZONE_NAMES)}

    @property
    def population(self):
        return sum(z.population for z in self.zones.values())

    def enter(self, visitor, zone_name):
        """A visitor walks into a zone. Returns (zone, shard)."""
        zone = self.zones[zone_name]
        zone.join(visitor)
        return zone, zone.shard_for(visitor)

    def leave(self, visitor):
        for zone in self.zones.values():
            zone.leave(visitor)

    def open_instance(self, trial, party):
        """Spawn a private trial instance for a party."""
        return Instance(self, trial, party)

    def status(self):
        lines = [f"Realm '{self.phrase}' — {self.population} inside:"]
        for name, zone in self.zones.items():
            lines.append(f"  {name}: {zone.population} visitors, "
                         f"{zone.shards} shard(s)")
        return "\n".join(lines)


class Directory:
    """The realm list. What's open, how full, where to go."""

    def __init__(self):
        self.realms = {}

    def register(self, phrase):
        """Open a realm by naming it. Naming is how worlds are born here."""
        if phrase not in self.realms:
            self.realms[phrase] = Realm(phrase)
        return self.realms[phrase]

    def find_room(self, phrase):
        """Least-crowded zone of a realm — where a newcomer should walk in."""
        realm = self.realms[phrase]
        return min(realm.zones.values(), key=lambda z: z.population)

    def status(self):
        lines = [f"Directory — {len(self.realms)} realm(s):"]
        for phrase, realm in self.realms.items():
            lines.append(f"  '{phrase}': {realm.population} inside")
        return "\n".join(lines)
