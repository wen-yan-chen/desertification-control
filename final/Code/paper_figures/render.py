"""Render the selected or complete Practice2 paper figure set from saved data."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import diagrams
import model1
import model2
import model3
from style import ROOT, configure


FIGURES = {
    "01_research_framework": diagrams.overview,
    "02_study_area": model1.study_area,
    "03_m1_water_cover_cycle": diagrams.water_cycle,
    "04_m1_holdout": model1.validation,
    "05_m1_irrigation_response": model1.irrigation,
    "06_m1_drivers": model1.drivers,
    "07_m2_cohort_schedule": model2.cohort_schedule,
    "08_m2_resources_finance": model2.resources,
    "09_m2_tradeoff_pv": model2.tradeoff,
    "10_m2_investment_sensitivity": model2.investment,
    "11_m3_disaster_cycle": diagrams.hazard_cycle,
    "12_m3_resilience": model3.outcomes,
    "13_m3_stress_tests": model3.stress_tests,
    "14_m3_numerical_check": model3.numerical_check,
    "15_policy_roadmap": diagrams.policy,
}

PAPER_FIGURES = (
    "02_study_area",
    "04_m1_holdout",
    "05_m1_irrigation_response",
    "06_m1_drivers",
    "09_m2_tradeoff_pv",
    "12_m3_resilience",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=tuple(FIGURES), help="Figure stems to render.")
    parser.add_argument("--out", type=Path, default=ROOT / "Figures/Paper2026")
    args = parser.parse_args()
    names = args.only or PAPER_FIGURES
    for name in names:
        for extension in ("pdf", "png"):
            path = args.out / f"{name}.{extension}"
            if path.exists():
                raise FileExistsError(path)
    args.out.mkdir(parents=True, exist_ok=True)
    configure()
    for name in names:
        fig = FIGURES[name]()
        try:
            fig.savefig(args.out / f"{name}.pdf", metadata={"Title": name.replace("_", " ")})
            fig.savefig(args.out / f"{name}.png", dpi=300)
        finally:
            plt.close(fig)
        print(name)


if __name__ == "__main__":
    main()
