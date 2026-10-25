import unittest
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nous_anki import tree


class TestTreePath(unittest.TestCase):
    def test_rand_reproducibility(self):
        # Known outputs verified against JS mulberry32
        val0 = tree.rand("testuser123#tier#0")
        val1 = tree.rand("testuser123#tree#0")
        val2 = tree.rand("testuser123#tier#1")

        self.assertAlmostEqual(val0, 0.8633953866083175, places=7)
        self.assertAlmostEqual(val1, 0.24675378645770252, places=7)
        self.assertAlmostEqual(val2, 0.8755051721818745, places=7)

    def test_plan_generation(self):
        steps = tree.plan("testuser123")
        self.assertEqual(len(steps), 35)
        # First tree should be oak, 1 hour
        self.assertEqual(steps[0]["id"], "oak")
        self.assertEqual(steps[0]["hours"], 1)
        self.assertEqual(steps[0]["tier"], "rare")

        # Second tree should be bamboo, 2 hours
        self.assertEqual(steps[1]["id"], "bamboo")
        self.assertEqual(steps[1]["hours"], 2)

        # Third tree should be willow, 1 hour
        self.assertEqual(steps[2]["id"], "willow")
        self.assertEqual(steps[2]["hours"], 1)

    def test_progress_calculation(self):
        steps = tree.plan("testuser123")
        # At 0 hours
        prog0 = tree.progress(steps, 0.0)
        self.assertEqual(prog0["grown"], 0)
        self.assertEqual(prog0["current"]["id"], "oak")
        self.assertEqual(prog0["into"], 0.0)
        self.assertEqual(prog0["hours_left"], 1.0)
        self.assertEqual(prog0["pct"], 0.0)

        # At 0.5 hours (halfway into oak)
        prog_half = tree.progress(steps, 0.5)
        self.assertEqual(prog_half["grown"], 0)
        self.assertEqual(prog_half["current"]["id"], "oak")
        self.assertEqual(prog_half["into"], 0.5)
        self.assertEqual(prog_half["pct"], 50.0)

        # At 3.5 hours (oak 1h + bamboo 2h = 3h grown; 0.5h into willow 1h)
        prog35 = tree.progress(steps, 3.5)
        self.assertEqual(prog35["grown"], 2)
        self.assertEqual(prog35["current"]["id"], "willow")
        self.assertEqual(prog35["into"], 0.5)
        self.assertEqual(prog35["hours_left"], 0.5)
        self.assertEqual(prog35["pct"], 50.0)

    def test_svg_generation(self):
        svg = tree.generate_tree_svg("oak", 50.0)
        self.assertIn("<svg", svg)
        self.assertIn("tree-branch", svg)
        self.assertIn("tree-leaf", svg)


if __name__ == "__main__":
    unittest.main()
