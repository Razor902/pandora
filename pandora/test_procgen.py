# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""EDUCATIONAL MODEL ONLY. Tests for the procgen world-grower."""

import unittest

from pandora import procgen


class TestProcgen(unittest.TestCase):
    def test_same_seed_same_world(self):
        a = procgen.heightmap(procgen.world_seed("Tuga Hollow"))
        b = procgen.heightmap(procgen.world_seed("Tuga Hollow"))
        self.assertEqual(a, b)

    def test_same_phrase_same_seed(self):
        self.assertEqual(procgen.world_seed("Valhalla"), procgen.world_seed("Valhalla"))

    def test_different_seeds_differ(self):
        a = procgen.heightmap(procgen.world_seed("Tuga Hollow"))
        b = procgen.heightmap(procgen.world_seed("The Lighthouse"))
        self.assertNotEqual(a, b)

    def test_describe_deterministic(self):
        self.assertEqual(
            procgen.describe_world("Valhalla"), procgen.describe_world("Valhalla")
        )

    def test_describe_differs(self):
        self.assertNotEqual(
            procgen.describe_world("Valhalla"), describe_world_check("Tuga Hollow")
        )

    def test_heightmap_bounds(self):
        grid = procgen.heightmap(procgen.world_seed("Valhalla"), size=24)
        for row in grid:
            for h in row:
                self.assertGreaterEqual(h, 0.0)
                self.assertLessEqual(h, 1.0)

    def test_heightmap_size(self):
        grid = procgen.heightmap(procgen.world_seed("Valhalla"), size=24)
        self.assertEqual(len(grid), 24)
        self.assertEqual(len(grid[0]), 24)

    def test_biome_coverage(self):
        seen = set()
        for i in range(60):
            seed = procgen.world_seed("world-%d" % i)
            heights = procgen.heightmap(seed, size=16)
            moistures = procgen.moisturemap(seed, size=16)
            for iy in range(16):
                for ix in range(16):
                    seen.add(procgen.biome(heights[iy][ix], moistures[iy][ix]))
        # water, land, and high ground must all appear across worlds
        self.assertTrue({"ocean", "deep ocean"} & seen)
        self.assertTrue({"plains", "forest", "beach"} & seen)
        self.assertTrue({"hills", "mountains", "snowcaps"} & seen)

    def test_biome_edges(self):
        self.assertEqual(procgen.biome(0.10, 0.5), "deep ocean")
        self.assertEqual(procgen.biome(0.35, 0.5), "ocean")
        self.assertEqual(procgen.biome(0.40, 0.5), "beach")
        self.assertEqual(procgen.biome(0.50, 0.2), "plains")
        self.assertEqual(procgen.biome(0.50, 0.8), "forest")
        self.assertEqual(procgen.biome(0.70, 0.5), "hills")
        self.assertEqual(procgen.biome(0.80, 0.2), "mountains")
        self.assertEqual(procgen.biome(0.80, 0.8), "snowcaps")

    def test_sky_deterministic(self):
        self.assertEqual(
            procgen.sky(procgen.world_seed("Valhalla")),
            procgen.sky(procgen.world_seed("Valhalla")),
        )

    def test_sky_bounds(self):
        skies = procgen.sky(procgen.world_seed("Valhalla"))
        self.assertGreaterEqual(skies["cloud_cover"], 0.0)
        self.assertLessEqual(skies["cloud_cover"], 1.0)
        self.assertGreaterEqual(skies["star_density"], 0.0)
        self.assertLessEqual(skies["star_density"], 1.0)
        self.assertIn(skies["suns"], (1, 2))

    def test_describe_mentions_terrain_and_sky(self):
        text = procgen.describe_world("Tuga Hollow").lower()
        self.assertIn("tuga hollow", text)
        self.assertTrue(any(w in text for w in ("ocean", "land", "islands", "plains",
                                                "forest", "hills", "mountains", "beach")))
        self.assertIn("sk", text)  # sky / skies
        self.assertIn("sun", text)


def describe_world_check(phrase):
    return procgen.describe_world(phrase)


if __name__ == "__main__":
    unittest.main()
