#!/usr/bin/env python3
# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""LIVE: Pandora's world infrastructure, running.

Warcraft's server craft, rebuilt for the box:
realms, zones, shards, instances, the directory.
Run: python3 demo_live.py
"""
import time

from pandora import worldinfra


def say(line=""):
    print(line, flush=True)


def main():
    say("PANDORA — WORLD INFRASTRUCTURE, LIVE")
    say("=" * 44)
    directory = worldinfra.Directory()

    # Open two realms by naming them. Naming is how worlds are born here.
    for phrase in ("Tuga Hollow", "Ember Rise"):
        directory.register(phrase)
        say(f"Realm opened: '{phrase}'")
    time.sleep(0.6)

    tuga = directory.realms["Tuga Hollow"]

    # A crowd pours into the Plains. Watch it shard.
    say("\nA crowd walks into the Plains of Tuga Hollow...")
    time.sleep(0.6)
    for i in range(95):
        tuga.enter(f"walker-{i:03d}", "Plains")
    plains = tuga.zones["Plains"]
    say(f"  {plains.population} walkers -> {plains.shards} shards")
    for shard, count in sorted(plains.census().items()):
        say(f"    shard {shard}: {count} walkers")
    time.sleep(0.6)

    # A party opens a private trial instance.
    say("\nA party opens a trial instance...")
    time.sleep(0.6)
    inst = tuga.open_instance("decipher-trial", ["wren", "paul"])
    say(f"  {inst.describe()}")
    time.sleep(0.6)

    # A newcomer arrives; the directory sends them where it's emptiest.
    say("\nA newcomer arrives. The directory sends them where it's emptiest...")
    time.sleep(0.6)
    room = directory.find_room("Tuga Hollow")
    say(f"  -> the {room.name} ({room.population} inside)")
    time.sleep(0.6)

    say("\n" + tuga.status())
    say("\n" + directory.status())
    say("\nThe box is live. Nola's law holds: no faked presence, no exceptions.")


if __name__ == "__main__":
    main()
