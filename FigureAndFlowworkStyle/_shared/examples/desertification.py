"""Render two kit recipes against a desertification-control results checkout."""
import argparse
import calendar
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from mcm_library.charts import quota_pressure, recovery_gap
from mcm_style import panels, paper_context, save_paper


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def render(root, out):
    results = root / "Results" / "v7"
    monthly = rows(results / "model2/monthly.csv")
    config = json.loads((results / "model2/model2_results.json").read_text())["config"]
    years = sorted({int(r["year"]) for r in monthly})
    usage = np.full((len(years), 12), np.nan)
    caps = np.full_like(usage, np.nan)
    seen = set()
    for r in monthly:
        month = int(r["month"])
        key = (years.index(int(r["year"])), month - 1)
        if key in seen or not 1 <= month <= 12:
            raise ValueError(f"Invalid or repeated year/month: {r}")
        seen.add(key)
        usage[key] = float(r["gross_water_m3"]) / 1e4
        caps[key] = float(r["cap_m3"]) / 1e4
    annual = rows(results / "model3/project_annual.csv")
    base = sorted((r for r in annual if r["case"] == "base_nonstationary"),
                  key=lambda r: int(r["post_year"]))
    with paper_context():
        quota = quota_pressure(usage, caps, config["annual_water_cap_m3"] / 1e4,
                               years=years, periods=calendar.month_abbr[1:], unit="$10^4$ m³")
        gap, axes = panels(3.0)
        recovery_gap(axes[0, 0], [int(r["post_year"]) for r in base],
                     [float(r["expected_ever_failed_area_ha"]) for r in base],
                     [float(r["expected_current_failed_area_ha"]) for r in base],
                     xlabel="Years after construction", unit="ha")
        for name, fig in [("quota_pressure", quota), ("recovery_gap", gap)]:
            paths, issues = save_paper(fig, out / name)
            print(paths["png"], [(issue.code, issue.detail) for issue in issues])
            plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    render(args.checkout, args.out)
