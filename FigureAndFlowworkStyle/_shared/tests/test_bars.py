"""Contracts for 100% composition and zero-based grouped comparisons."""

from pathlib import Path
import sys
import unittest

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcm_library import bars
from mcm_style import panels, paper_context


class BarContracts(unittest.TestCase):
    def setUp(self):
        scope = paper_context()
        scope.__enter__()
        self.addCleanup(scope.__exit__, None, None, None)
        self.addCleanup(plt.close, "all")

    def test_composition_retains_aligned_percentages_and_omits_narrow_label(self):
        fig, axes = panels(2.7)
        ax = axes[0, 0]
        bars.composition_bars(ax, ["A", "B"], [[5, 95], [20, 80]],
                              segments=["Small", "Large"])
        self.assertEqual(ax.get_xlim(), (0, 100))
        self.assertEqual([p.get_width() for p in ax.patches], [5, 20, 95, 80])
        self.assertEqual([t.get_text() for t in ax.texts], ["20%", "95%", "80%"])
        self.assertTrue(ax.yaxis_inverted())
        with self.assertRaisesRegex(ValueError, "total 100"):
            bars.composition_bars(ax, ["A"], [[40, 50]], segments=["X", "Y"])
        with self.assertRaisesRegex(ValueError, "finite nonnegative"):
            bars.composition_bars(ax, ["A"], [[np.nan, 100]], segments=["X", "Y"])

    def test_grouped_bars_use_zero_baseline_and_do_not_cover_series(self):
        fig, axes = panels(2.7)
        ax = axes[0, 0]
        bars.grouped_bars(ax, ["S1", "S2"], [
            bars.BarSeries("Base", [.5, .6]), bars.BarSeries("New", [.7, .8]),
        ], value_label="Score (0–1)", maximum=1)
        self.assertEqual(ax.get_ylim(), (0, 1))
        self.assertEqual([p.get_height() for p in ax.patches], [.5, .6, .7, .8])
        b0, b1, b2, b3 = ax.patches
        self.assertLessEqual(b0.get_x()+b0.get_width(), b2.get_x())
        self.assertLessEqual(b1.get_x()+b1.get_width(), b3.get_x())
        with self.assertRaisesRegex(ValueError, "aligned, finite nonnegative"):
            bars.grouped_bars(ax, ["S1"], [bars.BarSeries("X", [-1])],
                              value_label="Score (0–1)")

    def test_value_at_fixed_ceiling_is_labeled_inside_bar(self):
        fig, axes = panels(2.7)
        ax = axes[0, 0]
        bars.grouped_bars(ax, ["Full"], [bars.BarSeries("Score", [1])],
                          value_label="Score (0–1)", maximum=1)
        self.assertEqual(ax.texts[0].get_va(), "top")
        self.assertLess(ax.texts[0].get_position()[1], 1)


if __name__ == "__main__":
    unittest.main()
