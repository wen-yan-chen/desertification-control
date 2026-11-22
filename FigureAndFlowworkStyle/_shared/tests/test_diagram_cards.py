"""Check the rich framework remains data driven and printable."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcm_library.diagrams import CardStage, research_framework_cards
from mcm_style import paper_context, save_paper


class FrameworkCards(unittest.TestCase):
    def test_two_distinct_stages_export_with_named_handoff(self):
        stages = [
            CardStage("Prepare", "DATA CHECK", (
                ("Align rows", "Keys and units"),
                ("Audit gaps", "Flag missing values"),
                ("Freeze input", "Record the version"),
            )),
            CardStage("Evaluate", "MODEL CHECK", (
                ("Compare", "Shared time window"),
                ("Review", "Threshold cases"),
                ("Summarize", "Uncertainty limits"),
            ), color="#724C79", pale="#F3EDF4"),
        ]
        with paper_context("modern_sans"):
            fig = research_framework_cards(
                stages, title="Data to decision", subtitle="Synthetic workflow",
                inputs=("INPUT RECORDS", "Aligned measurements and stated assumptions"),
                handoffs=("cleaned cases",),
                deliverable=("DECISION NOTE", (("RESULT", "Documented limits"),)),
            )
            try:
                words = " ".join(text.get_text() for text in fig.axes[0].texts)
                self.assertIn("Passes: cleaned cases", words)
                self.assertIn("Documented limits", words)
                with TemporaryDirectory() as directory:
                    paths, issues = save_paper(fig, Path(directory) / "framework")
                    self.assertEqual(issues, [])
                    self.assertTrue(paths["pdf"].exists())
                    self.assertTrue(paths["png"].exists())
            finally:
                plt.close(fig)

    def test_three_stages_and_rejects_bad_handoff_or_steps(self):
        valid = CardStage("Check", "MODEL CHECK", (
            ("Collect", "Records"), ("Compare", "Estimates"),
            ("Report", "Limits"),
        ))
        inputs = ("Input", "Records")
        deliverable = ("Output", (("Result", "Summary"),))
        with paper_context("modern_sans"):
            fig = research_framework_cards([valid, valid, valid],
                                           title="Three stages", subtitle="Synthetic",
                                           inputs=inputs, handoffs=("states", "plans"),
                                           deliverable=deliverable)
            try:
                self.assertEqual(sum(t.get_text().startswith("Passes:")
                                     for t in fig.axes[0].texts), 2)
            finally:
                plt.close(fig)
        with self.assertRaises(ValueError):
            research_framework_cards([valid, valid], title="x", subtitle="",
                                     inputs=inputs, handoffs=(),
                                     deliverable=deliverable)
        incomplete = CardStage("Check", "MODEL CHECK", (("Collect", "Records"),))
        with self.assertRaises(ValueError):
            research_framework_cards([valid, incomplete], title="x", subtitle="",
                                     inputs=inputs, handoffs=("records",),
                                     deliverable=deliverable)


if __name__ == "__main__":
    unittest.main()
