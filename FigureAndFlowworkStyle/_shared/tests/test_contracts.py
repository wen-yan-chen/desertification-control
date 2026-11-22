"""Regression checks for data semantics and paper export, with no model runs."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcm_library import charts
from mcm_style import page, panels, paper_context, save_paper
from mcm_style.accents import gradient_bar


class PaperContracts(unittest.TestCase):
    def setUp(self):
        scope = paper_context()
        scope.__enter__()
        self.addCleanup(scope.__exit__, None, None, None)
        self.addCleanup(plt.close, "all")

    def test_target_positions_retain_zero_and_missing(self):
        fig = charts.target_tradeoff(["40%", "60%", "80%", "100%"],
                                     [800, 1200, np.nan, 2000], [10, 15, np.nan, 50],
                                     [6, 1, np.nan, 0], chosen="60%", benefit_label="Benefit",
                                     cost_label="Cost", capacity_label="Capacity")
        _, ax = fig.axes
        self.assertEqual([t.get_text() for t in ax.get_xticklabels()],
                         ["40%", "60%", "80%", "100%"])
        self.assertEqual([p.get_height() for p in ax.patches], [6, 1, 0])
        self.assertEqual({t.get_text(): t.get_position()[0] for t in ax.texts}, {"NA": 2, "0": 3})

    def test_heatmap_marks_missing_without_conflating_zero(self):
        fig, axes = panels(2.5)
        ax = axes[0, 0]
        mesh = charts.annotated_heatmap(ax, [[0, np.nan], [-1, 1]], rows=["A", "B"],
                                        cols=["X", "Y"], unit="Change (pp)", limits=(-1, 1),
                                        center=0, cmap="morandi_diverge")
        self.assertEqual(np.ma.getmaskarray(mesh.get_array()).sum(), 1)
        self.assertEqual([t.get_text() for t in ax.texts], ["0.0", "NA", "-1.0", "1.0"])

    def test_interval_plot_keeps_outside_estimate(self):
        fig, axes = panels(2.5)
        ax = axes[0, 0]
        charts.comparison_intervals(ax, ["Site A", "Site B"], [-.5, -.2], [.5, .2],
                                    [charts.Series("Estimate", [0, -.3], "#285987")],
                                    xlabel="Difference (pp)", interval_label="95% reference")
        self.assertAlmostEqual(ax.collections[1].get_offsets()[1, 0], -.3)

    def test_negative_gradient_does_not_reverse_axis(self):
        fig, axes = panels(2.5)
        ax = axes[0, 0]
        bar = gradient_bar(ax, 0, -2, 0, .5, horizontal=True, rounding=.1)
        self.assertEqual(tuple(bar.get_extent()), (-2, 0, 0, .5))
        self.assertFalse(ax.xaxis_inverted())
        self.assertIsNone(gradient_bar(ax, 0, 0, 1, .5, horizontal=True))

    def test_export_does_not_crop_or_overwrite_inherited_settings(self):
        from PIL import Image

        fig, axes = panels(2.5)
        axes[0, 0].plot([0, 1], [0, 1])
        axes[0, 0].set_xlabel("Year")
        with TemporaryDirectory() as directory, mpl.rc_context({"savefig.bbox": "tight"}):
            paths, issues = save_paper(fig, Path(directory) / "figure")
            self.assertEqual(issues, [])
            with Image.open(paths["png"]) as png:
                self.assertEqual(png.size, (1950, 750))
            with self.assertRaises(FileExistsError):
                save_paper(fig, Path(directory) / "figure")
        self.assertIn("small_text", {i.code for i in page.audit(fig, placed_width=3.25)})


if __name__ == "__main__":
    unittest.main()
