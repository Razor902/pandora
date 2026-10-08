# Tests for pandora.worldinfra — plain asserts, no framework.
"""Run: python3 test_worldinfra.py"""

from pandora import worldinfra
from pandora import procgen


def test_realm_seed_deterministic():
    a = worldinfra.Realm("Tuga Hollow")
    b = worldinfra.Realm("Tuga Hollow")
    assert a.seed == b.seed == procgen.world_seed("Tuga Hollow")
    c = worldinfra.Realm("Other Place")
    assert c.seed != a.seed


def test_zones_born_with_realm():
    r = worldinfra.Realm("Tuga Hollow")
    assert set(r.zones) == {"Harbor", "Plains", "Forest", "Highlands", "Deep", "Sky"}
    for name, zone in r.zones.items():
        assert zone.seed == procgen.world_seed("Tuga Hollow:" + name)


def test_sharding():
    r = worldinfra.Realm("Tuga Hollow")
    zone = r.zones["Plains"]
    assert zone.shards == 1  # empty zone, one shard
    visitors = [f"visitor-{i}" for i in range(85)]
    for v in visitors:
        zone.join(v)
    assert zone.shards == 3  # 85 over cap 40 -> 3 shards
    # Stable per visitor: same visitor, same shard, every time.
    for v in visitors:
        assert zone.shard_for(v) == zone.shard_for(v)
    # Census is honest: shards sum to population.
    census = zone.census()
    assert sum(census.values()) == 85
    assert max(census.values()) - min(census.values()) <= 20  # roughly even deal


def test_enter_and_leave():
    r = worldinfra.Realm("Tuga Hollow")
    zone, shard = r.enter("wren", "Forest")
    assert zone.name == "Forest"
    assert r.population == 1
    r.leave("wren")
    assert r.population == 0
    assert r.zones["Forest"].population == 0


def test_instance_deterministic():
    r = worldinfra.Realm("Tuga Hollow")
    i1 = r.open_instance("decipher-trial", ["wren", "paul"])
    i2 = r.open_instance("decipher-trial", ["paul", "wren"])  # order irrelevant
    assert i1.instance_id == i2.instance_id
    assert i1.seed == i2.seed
    i3 = r.open_instance("decipher-trial", ["wren", "becka"])
    assert i3.instance_id != i1.instance_id
    assert len(i1.instance_id) == 16


def test_directory():
    d = worldinfra.Directory()
    d.register("Tuga Hollow")
    d.register("Tuga Hollow")  # registering twice opens it once
    assert len(d.realms) == 1
    d.register("Second World")
    assert len(d.realms) == 2
    # Newcomers go where it's emptiest.
    d.realms["Tuga Hollow"].enter("crowd-1", "Plains")
    room = d.find_room("Tuga Hollow")
    assert room.name != "Plains"
    assert "2 realm(s)" in d.status()


if __name__ == "__main__":
    test_realm_seed_deterministic()
    test_zones_born_with_realm()
    test_sharding()
    test_enter_and_leave()
    test_instance_deterministic()
    test_directory()
    print("worldinfra: all 6 tests pass")
