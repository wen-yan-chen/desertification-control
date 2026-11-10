# Handoff to Astra — Model 1 on v7, state on 2026-11-10 (evening)

Written by Claude. Read `Docs/20261110_model1_v7_rebuild.md` next; it has the evidence for everything below.

## What was added (branch `model1-v7-rebuild`, cut from `main` at 32b6534)

| Path | What it is |
|---|---|
| `Code/v7_model1.py` | Task 1 rebuilt on the v7 panel: checks of v7 inputs, pooled nested fits, transfer test, water closure, V*(I) curve, sensitivity, two figures. Offline, about 10 s |
| `Results/v7/model1/` | `model1_results.json`, `yearly_table.csv`, `water_cover_curve.csv`, `sensitivity.csv` |
| `Figures/v7/m1_fig1_station_evidence.png`, `m1_fig2_transfer_and_water.png` | diagnostic figures |
| `Data/v7/section_modis/` | small tables copied from branch `model1-first-version` (commit 270e468): converted-pixel cohort, class cover, windows, end-members, earlier daily-model curve |
| `Docs/20261110_model1_v7_rebuild.md` | model, check of v7 Task 1, changes C1–C7, results, limits, Chinese summary |

Not touched: `Reports/model_v7.tex`, `Code/v7_*.py`, the v7 panel.

## First-trial daily model, merged into this branch

Branch `model1-first-version` is merged here (not into `main`), so both versions sit side by side:

| Version | Code | Data | Results / figures | Write-up |
|---|---|---|---|---|
| v7 rebuild (current, yearly, simple) | `Code/v7_model1.py` | `Data/v7/` | `Results/v7/model1/`, `Figures/v7/m1_fig*.png` | `Docs/20261110_model1_v7_rebuild.md` |
| First trial (daily, FAO-56 water balance, more parameters) | `Code/m1_*.py` | `Data/raw/model1/`, `Data/processed/model1/` | `Results/model1/`, `Figures/model1/` | `Docs/20261110_audit_check_and_model1.md`, `Reports/M1/model1_en.pdf`, `model1_zh.pdf`; its own handoff is `Docs/HANDOFF_to_Astra_first_trial.md` |

Use the v7 rebuild as Model 1. The first trial is kept as a reference: it supplies the section pixel data, the daily water balance behind the water relation, and a cross-check of the water–cover curve. `Data/v7/section_modis/` is a copy of four of its tables so that `v7_model1.py` runs without it.

## The model in two lines

```
V[t+1] = V + r·V·(1 − V/K)·W − d·V − k·E·(1 − η·V/K)·V          (v7 equation, unchanged)
W = min(1, (η_w·I + G) / (c · min(1, 2·V/V_full) · ET0g))        (added: water budget)
```

Adopted: r = 0.584 ± 0.180, d = 0.117 ± 0.035 (pooled over 7 stations), K by the v7 rule, k = 0 and η = 1 as scenario parameters, c = 1.0, η_w = 0.75, V_full = 66.6 %, ET0g = 1163 mm/yr.

## Verified / not verified

Verified by running: pooled fit and nested comparison; hold-out and leave-one-station-out scores; transfer of station r, d to 217 section pixels (held-out window R² 0.31); free fit there gives r 0.64, d 0.10.

Not verified, do not present as fact:

- The water-limited part of V*(I). No observation of cover against applied water exists. Quote ranges from `sensitivity.csv`.
- k (wind damage). Estimate 0.00 ± 0.27.
- Loss rate after irrigation stops. The model gives a 5.9-year half-life from d alone; real loss is probably faster.
- The model does not beat persistence for one-year-ahead station cover (0.068 against 0.058).

## Next steps

1. **Carry C1–C7 into `Reports/model_v7.tex` §3** (Task 1): pooled calibration, k and η as scenario parameters, the W relation in place of GWETROOT, f(T) absorbed in r. The closed form x* = (rW − d − kE)/(rW − kEη) still holds for given W.
2. **Task 2.** Replace `steady_v()` in `Code/v7_ablation.py` (Ks = 0.45 + 0.55·I/60) by interpolation of `Results/v7/model1/water_cover_curve.csv`, or call `steady()` from `v7_model1.py`. Note the units: I in mm/yr on the treated area; 1 mm = 10 m³/ha.
3. **Task 3.** Use the same r, d. Treat k ∈ {0, 0.02, 0.05, 0.10} and a faster no-water loss rate as scenarios, since neither is identified.
4. **If time allows:** find one measured pair of irrigation depth and shrub-belt cover to anchor c and η_w; that is the single most useful missing number.

## Rules kept

Fit on training data only; report hold-out next to persistence and mean baselines; keep unfavourable scores; every parameter is fitted with an s.d., taken from the v7 rule, or a named assumption with a range.
