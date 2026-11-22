"""Contract tests for the 1.4.0 figure-type promotions.

Every promoted function must accept clean caller-supplied data and reject
misaligned or irregular inputs loudly, without reading any project file.
"""

import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mcm_library.charts import (
    break_even_curves,
    break_even_points,
    dual_axis_lines,
    feasible_band,
    signed_bars,
    three_d_columns,
    tornado,
)
from mcm_library.diagrams import LoopStage, feedback_loop


class TestSignedBars(unittest.TestCase):
    def test_happy_and_sign_colors(self):
        fig, ax = plt.subplots()
        result = signed_bars(ax, ["P1", "P2", "P3"], [1.0, -0.5, 0.2], xlabel="Elasticity")
        plt.close(fig)
        self.assertIs(result, ax)
        bars = [p for p in ax.patches if p.get_height() > 0]
        self.assertEqual(len(bars), 3)

    def test_sorts_by_magnitude_by_default(self):
        fig, ax = plt.subplots()
        signed_bars(ax, ["A", "B", "C"], [0.1, -1.0, 0.4], xlabel="x")
        labels = [t.get_text() for t in ax.get_yticklabels()]
        plt.close(fig)
        self.assertEqual(labels, ["B", "C", "A"])

    def test_input_order(self):
        fig, ax = plt.subplots()
        signed_bars(ax, ["A", "B", "C"], [0.1, -1.0, 0.4], xlabel="x",
                    sort_by="input")
        labels = [t.get_text() for t in ax.get_yticklabels()]
        plt.close(fig)
        self.assertEqual(labels, ["A", "B", "C"])

    def test_irregular_inputs(self):
        fig, ax = plt.subplots()
        with self.assertRaises(ValueError):
            signed_bars(ax, ["A", "B"], [1.0], xlabel="x")
        with self.assertRaises(ValueError):
            signed_bars(ax, ["A", "A"], [1.0, 2.0], xlabel="x")
        with self.assertRaises(ValueError):
            signed_bars(ax, ["A", "B"], [1.0, np.nan], xlabel="x")
        plt.close(fig)


class TestTornado(unittest.TestCase):
    def test_happy_and_sorting(self):
        fig, ax = plt.subplots()
        tornado(ax, ["p1", "p2"], [1.0, 2.0], [3.0, 2.5], baseline=2.2,
                xlabel="Output")
        labels = [t.get_text() for t in ax.get_yticklabels()]
        plt.close(fig)
        self.assertEqual(labels, ["p1", "p2"])  # p1 range 2.0 > p2 range 0.5

    def test_irregular_inputs(self):
        fig, ax = plt.subplots()
        with self.assertRaises(ValueError):
            tornado(ax, ["p1"], [2.0], [1.0], baseline=1.5, xlabel="x")
        with self.assertRaises(ValueError):
            tornado(ax, ["p1"], [1.0, 1.0], [2.0], baseline=1.5, xlabel="x")
        with self.assertRaises(ValueError):
            tornado(ax, ["p1"], [1.0], [2.0], baseline=np.inf, xlabel="x")
        plt.close(fig)


class TestBreakEven(unittest.TestCase):
    def test_roots_include_exact_zero(self):
        x = np.array([0.0, 1.0, 2.0])
        revenue = np.array([0.0, 2.0, 4.0])
        cost = np.array([1.0, 2.0, 1.0])
        roots = break_even_points(x, revenue, cost)
        np.testing.assert_allclose(roots, [1.0], atol=1e-9)

    def test_no_crossing_is_empty(self):
        x = np.linspace(0, 1, 51)
        roots = break_even_points(x, x + 2, x)
        self.assertEqual(roots.size, 0)

    def test_rejects_non_increasing_x(self):
        with self.assertRaises(ValueError):
            break_even_points([0, 1, 1], [0, 1, 2], [1, 1, 1])

    def test_curves_figure_and_note(self):
        x = np.linspace(0, 2, 101)
        fig = break_even_curves(x, 4*x - x*x, 1 + .5*x, xlabel="x",
                                ylabel="y", note="synthetic")
        self.assertEqual(len(fig.axes), 1)
        self.assertTrue(fig.texts)
        plt.close(fig)


class TestDualAxis(unittest.TestCase):
    def test_happy(self):
        x = np.linspace(0, 10, 51)
        fig = dual_axis_lines(x, np.sin(x) + 2, np.cos(x)*10,
                              primary_label="A", secondary_label="B",
                              xlabel="x", ylabel_primary="A (u)",
                              ylabel_secondary="B (v)")
        self.assertEqual(len(fig.axes), 2)
        plt.close(fig)

    def test_misaligned_raises(self):
        with self.assertRaises(ValueError):
            dual_axis_lines([0, 1, 2], [1, 2], [3, 4, 5],
                            primary_label="A", secondary_label="B",
                            xlabel="x", ylabel_primary="u", ylabel_secondary="v")


class TestFeasibleBand(unittest.TestCase):
    def test_happy_with_points(self):
        x = np.linspace(0, 1, 101)
        lower, upper = x*.2, x*.2 + .4
        fig, ax = plt.subplots()
        feasible_band(ax, x, lower, upper, samples=([.3, .6], [.3, .4]),
                      observed=([.5], [.35]), xlabel="x", ylabel="y")
        plt.close(fig)

    def test_inverted_bounds_raise(self):
        fig, ax = plt.subplots()
        with self.assertRaises(ValueError):
            feasible_band(ax, [0, 1], [.5, .5], [.4, .4], xlabel="x", ylabel="y")
        plt.close(fig)


class TestThreeDColumns(unittest.TestCase):
    def test_happy_grid_and_table(self):
        values = np.array([[41.8, 16.6, 11.4], [20.7, 7.3, 5.2], [8.8, 3.7, 2.8]])
        fig = three_d_columns(values, rows=["0.10", "0.25", "0.50"],
                              cols=["0.15", "0.30", "0.45"], unit="RMST(50) (yr)",
                              title="First passage", detail="3×3 cases",
                              note="discrete cases")
        texts = [t.get_text() for t in fig.texts]
        for axis in fig.axes:
            texts += [t.get_text() for t in axis.texts]
        self.assertTrue(any("41.8" in t for t in texts))  # orthographic table
        plt.close(fig)

    def test_irregular_inputs(self):
        with self.assertRaises(ValueError):
            three_d_columns(np.ones((2, 2)), rows=["a", "b"], cols=["c"],
                            unit="u")
        with self.assertRaises(ValueError):
            three_d_columns(np.array([[1.0, np.nan]]), rows=["a"], cols=["c", "d"],
                            unit="u")
        with self.assertRaises(ValueError):
            three_d_columns(np.array([[5.0]]), rows=["a"], cols=["c"], unit="u",
                            limits=(0, 4))

    def test_limits_cover_data(self):
        fig = three_d_columns(np.array([[2.0, 8.0]]), rows=["a"], cols=["c", "d"],
                              unit="u", limits=(0, 10))
        plt.close(fig)


class TestFeedbackLoop(unittest.TestCase):
    def test_happy_five_stages(self):
        stages = [
            LoopStage("Cover V", "annual state", "#426750"),
            LoopStage("Demand D", "daily flow", "#416B75"),
            LoopStage("Root water M", "daily store", "#416B75"),
            LoopStage("Demand met W", "annual ratio", "#416B75"),
            LoopStage("Growth", "annual change", "#426750"),
        ]
        fig = feedback_loop(stages, title="Two balancing feedbacks",
                            subtitle="daily balance feeds annual growth",
                            signs=["+", "−", "+", "+", "+"],
                            center="K", footer="local directional effects")
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_validation(self):
        with self.assertRaises(ValueError):
            feedback_loop([LoopStage("a", "b")], title="t", subtitle="s")
        with self.assertRaises(ValueError):
            feedback_loop([LoopStage("a", "b"), LoopStage("c", "d"),
                           LoopStage("e", "f")], title="t", subtitle="s",
                          signs=["+", "+"])
        with self.assertRaises(ValueError):
            feedback_loop([LoopStage("a", "b"), LoopStage("c", "d"),
                           LoopStage("e", "f")], title="", subtitle="s")


if __name__ == "__main__":
    unittest.main()
