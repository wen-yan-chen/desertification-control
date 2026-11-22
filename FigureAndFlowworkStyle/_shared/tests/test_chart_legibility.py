"""Checks for chart legibility failures seen in the paper replays."""

from pathlib import Path
import math
import sys
import unittest

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcm_library import charts
from mcm_style import panels, paper_context


class ChartLegibility(unittest.TestCase):
    def setUp(self):
        scope = paper_context()
        scope.__enter__()
        self.addCleanup(scope.__exit__, None, None, None)
        self.addCleanup(plt.close, "all")

    def test_dot_values_avoid_reference_line(self):
        fig, axes = panels(2.7)
        ax = axes[0, 0]
        charts.comparison_dots(ax, ["A", "B", "C"], [6.5, 7.1, 8.1],
                               xlabel="Restricted mean (yr)", baseline=(7.1, "Baseline"))
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        labels = [t for t in ax.texts if t.get_text() in {"6.5", "7.1", "8.1"}]
        self.assertEqual(len(labels), 3)
        line_x = ax.transData.transform((7.1, 0))[0]
        boxes = [label.get_window_extent(renderer) for label in labels]
        self.assertTrue(all(box.x0 > line_x for box in boxes))
        self.assertLess(max(box.x1 for box in boxes), ax.bbox.x1)

    def test_radar_category_labels_sit_outside_outer_ring(self):
        labels = ["Capacity", "Shore power", "Visitor cap", "Fee / tax",
                  "Rent subsidy", "Transit", "Alcohol control"]
        fig = charts.radar_profile(labels, [
            charts.Series("A", np.linspace(.2, .8, len(labels)), "#08786F"),
            charts.Series("B", np.linspace(.8, .2, len(labels)), "#9D5526"),
        ])
        fig.canvas.draw()
        ax = fig.axes[0]
        renderer = fig.canvas.get_renderer()
        center = ax.transData.transform((0, 0))
        radius = np.linalg.norm(ax.transData.transform((0, 1))-center)
        for label in ax.get_xticklabels():
            box = label.get_window_extent(renderer)
            dx = max(box.x0-center[0], 0, center[0]-box.x1)
            dy = max(box.y0-center[1], 0, center[1]-box.y1)
            self.assertGreaterEqual(math.hypot(dx, dy), radius-1,
                                    msg=f"{label.get_text()} touches the outer ring")
        # Numerical ring labels must not sit over arbitrary data edges/markers.
        self.assertFalse(any(t.get_visible() and t.get_text()
                             for t in ax.get_yticklabels()))
        key, = [t for t in fig.texts if t.get_text().startswith("Center 0")]
        self.assertFalse(key.get_window_extent(renderer).overlaps(ax.bbox))

    def test_reference_band_separates_coincident_estimates_without_moving_x(self):
        fig, axes = panels(2.7)
        ax = axes[0, 0]
        charts.comparison_intervals(
            ax, ["North", "South"], [-.2, -.4], [.3, .1],
            [charts.Series("Coarse", [0, -.5], "#285987", marker="o"),
             charts.Series("Fine", [0, -.3], "#08786F", marker="D")],
            xlabel="Difference (pp)", interval_label="Reference", row_separation=.4,
        )
        first, second = [artist.get_offsets() for artist in ax.collections[-2:]]
        np.testing.assert_allclose(first[:, 0], [0, -.5])
        np.testing.assert_allclose(second[:, 0], [0, -.3])
        np.testing.assert_allclose(second[:, 1] - first[:, 1], [.4, .4])
        self.assertAlmostEqual(ax.patches[1].get_x(), -.4)
        self.assertAlmostEqual(ax.patches[1].get_width(), .5)
        self.assertLess(first[1, 0], ax.patches[1].get_x())  # Outside estimate stays visible.


if __name__ == "__main__":
    unittest.main()
