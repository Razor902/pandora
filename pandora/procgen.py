# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""EDUCATIONAL MODEL ONLY — classroom procedural generation, not a game engine.

Pandora's procgen: worlds grown from math, No Man's Sky style.
Name a world with a seed phrase and the box grows it back exactly,
every visit. Nothing is stored — the world is recomputed from the seed.

Borrowed from No Man's Sky: the deterministic seed core (same seed =
same world), the cascade (seed -> terrain -> climate -> sky), and
generate-on-visit with nothing stored. Not borrowed: the 3D engine,
creature grammars, multiplayer — this is terrain, biomes, and sky
from pure-Python math. stdlib only.
"""

import hashlib
import math

_MASK64 = 0xFFFFFFFFFFFFFFFF


def world_seed(phrase):
    """A seed phrase becomes a 64-bit world number. Same phrase, same number."""
    digest = hashlib.sha256(phrase.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _splitmix64(state):
    """Deterministic 64-bit mixer. Pure math, no storage, repeatable forever."""
    state = (state + 0x9E3779B97F4A7C15) & _MASK64
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
    return (z ^ (z >> 31)) & _MASK64


def _hash2(ix, iy, seed):
    """One deterministic value in [0, 1) for a lattice point. Same inputs, same output."""
    h = (ix * 0x9E3779B97F4A7C15 + iy * 0xBF58476D1CE4E5B9 + seed) & _MASK64
    return _splitmix64(h) / 2**64


def _smooth(t):
    """Smoothstep: eases interpolation so the noise rolls instead of jerks."""
    return t * t * (3 - 2 * t)


def _value_noise(x, y, seed):
    """Smooth value noise at one point: lattice corners hashed, blended."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    a = _hash2(ix, iy, seed)
    b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed)
    d = _hash2(ix + 1, iy + 1, seed)
    ux, uy = _smooth(fx), _smooth(fy)
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


def _fbm(x, y, seed, octaves=4):
    """Fractal noise: layered octaves, broad shapes first, fine detail last."""
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * _value_noise(x * freq, y * freq, seed + o * 7919)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


def heightmap(seed, size=48):
    """The land itself: a size x size grid of heights in [0, 1]."""
    grid = []
    scale = 6.0 / size
    for iy in range(size):
        row = []
        for ix in range(size):
            row.append(_fbm(ix * scale, iy * scale, seed))
        grid.append(row)
    return grid


def moisturemap(seed, size=48):
    """A second noise field: how wet each patch of land is, in [0, 1]."""
    return heightmap(seed ^ 0x5DEECE66D, size)


def biome(height, moisture):
    """Height + wetness decide what a patch of ground is."""
    if height < 0.30:
        return "deep ocean"
    if height < 0.38:
        return "ocean"
    if height < 0.42:
        return "beach"
    if height < 0.60:
        return "forest" if moisture >= 0.5 else "plains"
    if height < 0.75:
        return "hills"
    if moisture >= 0.6:
        return "snowcaps"
    return "mountains"


_SKY_COLORS = [
    "teal", "azure", "violet", "amber", "rose", "emerald", "cobalt", "copper",
]


def sky(seed):
    """The box's sky, grown from the seed: color, clouds, suns, night stars."""
    s = seed
    s = _splitmix64(s)
    color = _SKY_COLORS[s % len(_SKY_COLORS)]
    s = _splitmix64(s)
    cloud_cover = (s % 1000) / 1000.0
    s = _splitmix64(s)
    star_density = (s % 1000) / 1000.0
    s = _splitmix64(s)
    suns = 2 if (s % 7) == 0 else 1  # one world in seven gets two suns
    return {
        "color": color,
        "cloud_cover": round(cloud_cover, 3),
        "star_density": round(star_density, 3),
        "suns": suns,
    }


def _word_for_clouds(cover):
    if cover < 0.2:
        return "a clear, open sky"
    if cover < 0.5:
        return "a few wandering clouds"
    if cover < 0.8:
        return "a broad deck of clouds"
    return "a heavy, low overcast"


def _word_for_stars(density):
    if density < 0.25:
        return "a sparse scattering of stars"
    if density < 0.6:
        return "a rich field of stars"
    return "a blazing river of stars"


def _word_for_land(dominant, ocean_frac, peak):
    parts = []
    if ocean_frac > 0.6:
        parts.append("an ocean world")
    elif ocean_frac > 0.3:
        parts.append("a world of islands and wide seas")
    elif ocean_frac > 0.05:
        parts.append("a land with lakes and a far shoreline")
    else:
        parts.append("a dry, landlocked world")
    if dominant in ("mountains", "snowcaps"):
        parts.append("crowned with high %s" % dominant)
    elif dominant in ("hills",):
        parts.append("rolling in long hills")
    elif dominant == "forest":
        parts.append("thick with forest")
    elif dominant == "plains":
        parts.append("open underfoot, grass to the horizon")
    elif dominant == "beach":
        parts.append("low and sandy, the tide never far")
    if peak >= 0.9:
        parts.append("and one great peak that breaks the clouds")
    return ", ".join(parts)


def describe_world(seed_phrase, size=48):
    """One plain-words paragraph: what the citizen sees stepping in."""
    seed = world_seed(seed_phrase)
    heights = heightmap(seed, size)
    moistures = moisturemap(seed, size)
    counts = {}
    peak = 0.0
    ocean_cells = 0
    total = size * size
    for iy in range(size):
        for ix in range(size):
            h, m = heights[iy][ix], moistures[iy][ix]
            b = biome(h, m)
            counts[b] = counts.get(b, 0) + 1
            if h > peak:
                peak = h
            if b in ("ocean", "deep ocean"):
                ocean_cells += 1
    land_counts = {b: c for b, c in counts.items() if b not in ("ocean", "deep ocean")}
    dominant = max(land_counts, key=land_counts.get) if land_counts else "ocean"
    ocean_frac = ocean_cells / total
    skies = sky(seed)
    suns_word = "twin suns" if skies["suns"] == 2 else "a single sun"
    return (
        "You step into %s: %s. Above it all hangs %s beneath %s, lit by %s; "
        "at night, %s. Name this world again and it will be waiting, exactly as you left it — "
        "the box grows it from the name, and keeps nothing."
        % (
            seed_phrase,
            _word_for_land(dominant, ocean_frac, peak),
            skies["color"] + " skies",
            _word_for_clouds(skies["cloud_cover"]),
            suns_word,
            _word_for_stars(skies["star_density"]),
        )
    )


def demo():
    """Three named seeds, three worlds."""
    for name in ["Tuga Hollow", "Valhalla", "The Lighthouse"]:
        print(describe_world(name))
        print()


if __name__ == "__main__":
    demo()
