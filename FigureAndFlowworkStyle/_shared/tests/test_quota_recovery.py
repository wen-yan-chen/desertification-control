import unittest

import matplotlib.pyplot as plt
import numpy as np

from mcm_library.charts import quota_pressure, recovery_gap


class ResourceFigures(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_missing_values_do_not_contribute_zero_and_overuse_is_visible(self):
        fig = quota_pressure([[9, np.nan], [2, 12]], [10, 8], 30,
                             years=["Y1", "Y2"], periods=["Dry", "Wet"], unit="m³")
        annual, detail, heat, _ = fig.axes
        self.assertTrue(np.isnan(annual.patches[0].get_height()))
        self.assertEqual(annual.patches[1].get_height(), 14)
        self.assertIn("150.0%", detail.get_title(loc="left"))
        self.assertEqual(heat.images[0].get_clim()[1], 150)

    def test_closed_period_with_use_is_marked(self):
        fig = quota_pressure([[1, 0]], [0, 0], [2], years=[1], periods=["A", "B"], unit="kWh")
        self.assertEqual([t.get_text() for t in fig.axes[2].texts], ["×"])
        self.assertIn("zero cap", fig.axes[1].get_title(loc="left"))

    def test_gap_annotation_uses_last_paired_observation(self):
        _, ax = plt.subplots()
        recovery_gap(ax, [1, 2, 3], [3, 7, 9], [2, 1.25, np.nan], xlabel="Year", unit="ha")
        self.assertEqual(ax.texts[0].get_text(), "5.75 ha")
        self.assertEqual(ax.texts[0].xy[0], 2)

    def test_gap_rejects_non_nested_or_decreasing_cumulative_series(self):
        for ever, current in [([1, 4], [2, 3]), ([4, 3], [2, 1])]:
            with self.subTest(ever=ever), self.assertRaises(ValueError):
                recovery_gap(plt.subplots()[1], [1, 2], ever, current, xlabel="Year", unit="ha")


class ImageProfile(unittest.TestCase):
    def test_reversed_profile_preserves_pixel_order(self):
        from PIL import Image
        from examples.image_data.line_profile import line_profile
        pixels = np.asarray([[8, 13, 21], [34, 55, 89]], dtype=np.uint8)
        fig, series = line_profile(Image.fromarray(pixels), (2, 1), (0, 1), credit="Fixture")
        self.addCleanup(plt.close, fig)
        np.testing.assert_array_equal(series[:, 0], [0, 1, 2])
        np.testing.assert_array_equal(series[:, 1], [89, 55, 34])
