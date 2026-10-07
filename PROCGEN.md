# Procgen — Worlds Grown From Math

**Curtis's order (2026-10-07):** research No Man's Sky's infrastructure, and put its ideas in Pandora's Box.

## The idea, in plain words

No Man's Sky doesn't store 18 quintillion planets. It stores a recipe: one seed number goes in, a whole world comes out — the same world, every time. Pandora's procgen works the same way. **Name a world and the box grows it back exactly, forever. Nothing is stored; the world is recomputed from the name.**

## How a world grows

1. **The name becomes a number.** Your seed phrase ("Tuga Hollow") is hashed into a 64-bit world seed. Same phrase, same number, always.
2. **The land rises.** A small deterministic noise function — value noise layered in octaves, written from scratch, no libraries — rolls out a heightmap: broad continents first, fine bumps last.
3. **Height + wetness become biomes.** A second noise field decides moisture. Together they paint deep ocean, ocean, beach, plains, forest, hills, mountains, snowcaps.
4. **The sky is grown too.** From the same seed: a sky color, cloud cover, star density for the night — and one world in seven gets twin suns.
5. **Nothing is saved.** Visit again next year, say the name, and the box regrows the identical world.

## What was borrowed — and what wasn't

Borrowed from No Man's Sky: the deterministic seed core, the cascade (seed → terrain → climate → sky), generate-on-visit with nothing stored, the honest tuning mindset.
Not borrowed: the 3D engine, creature grammars, multiplayer discovery. This is a classroom model — terrain, biomes, and sky from pure-Python math — not a game engine.

## Limits

Classroom procgen: a 48×48 heightmap and a paragraph of description, not rendered worlds. Math has patterns — across thousands of worlds, some will rhyme, the same honest limit No Man's Sky carries. The tuning (interesting but walkable) is the craft; the code is the easy part.

## Try it

```python
from pandora import procgen
print(procgen.describe_world("Tuga Hollow"))
```

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
