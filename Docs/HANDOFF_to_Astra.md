# Handoff to Astra — 2026-11-11: M2 figures drawn from the model2 tables

Written by Claude, in answer to `Docs/20261111_m2_figure_handoff.md`.

**Added**
- `Code/v7_m2_figures.py` — draws 7 figures from `Results/v7/model2/*.csv`, `model2_results.json` and `scenario_configs.json` only (no optimisation re-run). Run: `.venv/bin/python Code/v7_m2_figures.py` (needs matplotlib; imports the style constants from `v7_m1_figures.py`). It stops if any of the 6 hashes in `model2_results.json` differs from the working tree, so re-run `v7_model2.py` first after changing M2 inputs or code.
- `Figures/M2/` — `m2_f01`…`m2_f07`, each as PDF + PNG, plus `Figures/M2/README.md` (what each figure shows, which table it uses, numbers readable from it, caveats for captions). One figure per row of your handoff table.
- Pointers added in `README.md` and `Code/README.md`. No model code, table or M1 figure was touched.

**State**
- All 7 figures checked by eye; plotted values match the tables (base 300 ha / 9.5 MW / 25.3 M CNY; frontier −4.9, 4.8, 14.2, 25.3, 40.5, 64.4 M CNY; tightest month May of years 8–15 at 95% of the cap). `fig_cohorts` asserts that the per-cohort contributions add to `annual.effective_ha`. `test_v7_m2.py` still passes (7 tests).
- All 29 runs appear: 6 frontier points in f04 (the base is the 60% point, the maximum-ecology reference is the 100% point), 11 in f05, 10 in f06.
- Choices you may want to know: the frontier is drawn as unconnected points; f06(a) uses a symmetric-log axis so that 0.2% and 29% are both readable, with the ±0.2% solver tolerance as two red dashed lines; at the user's request every limit line (budget cap, water caps, section K, storage capacity, solver tolerance, base PV price) is red dashed via the `LIMIT` style in the script, while plain reference values stay grey; `eco_capex_low/high` sit with the price/cost cases in f05, and `water_relax_10pct`, `budget_low`, `labor_low` with the assumption checks in f06.
- M1 figures restyled the same way, also at the user's request: `LIMIT` now lives in `Code/v7_m1_figures.py` and the M2 script imports it. Changed images: `m1_f01` (local K), `m1_f04` (plateau), `m1_f06` (W = 1, storage capacity), `m1_f08` (storage capacity). `m1_f02/03/05/07/09` are pixel-identical to the committed versions and their files were left as committed. No M1 number, table or model code changed; the hold-out shading, bootstrap percentile lines, E = 1 line and irrigation-stop markers stay grey because they are not limits. M1 and M2 tests pass (16).
- Not done: nothing copied to `Paper/Figure/`, no captions written, nothing committed.

**Next**
1. Choose which M2 figures go into the paper's Model 2 section, copy their PDFs to `Paper/Figure/`, and write captions that carry the caveats listed in `Figures/M2/README.md`.
2. If the scenario set or cohort set changes, `fig_cohorts` (three named cohorts) and the case lists in `fig_investment` / `fig_assumptions` need the new names; the script fails loudly rather than drawing a partial figure.
3. M3 is still pending.

# Handoff to Astra — 2026-11-11: M1 correction merged into model_v7 Task 1

Written by Claude.

**Changed**
- `Reports/model_v7.tex` §3 (Task 1) rewritten with the 2026-11-10 M1 correction: annual vegetation `V_t` plus within-year effective storage `M_j` (FAO-56-style balance, eq:m1demand/m1bal/m1W/m1cons), `f(T)` only in transpiration timing, daily-first wind index, discrete half-life, coupled fixed point (eq:fixed), one-step pooled `(r,d)` least squares (eq:obj, linear in r,d), station-cluster bootstrap, non-identifiability example (eq:ident), CON4 retrospective only. All old labels kept, so M2/M3 and appendix references still resolve.
- Also updated to match: status box, Table 1 row, assumptions (year scale, water), data-field and quality tables, minimum data set, sensitivity recursion (eq:sens uses `\overline W_t`, no `f(T)`), appendix symbol/field/parameter/formula tables.
- `Reports/m1_correction.tex` deleted (content now in §3; recoverable from git). Pointers updated in `README.md`, `Reports/README.md`, `archive/invalidated_20261109/README.md`, `Reports/M1/model1_v7_{zh,en}.tex` (those two PDFs not recompiled).

**State**
- `xelatex model_v7.tex` ×2: no errors, no undefined refs, no overfull boxes; 25 pages. Model text only, no result numbers.

**Next**
1. Task 3 (§5) still uses an exogenous `W_t` trend in eq:trend and `F(v)` on `V` only; when M3 is implemented, carry `(V,M)` through the annual map `Φ` as §3 now requires.
2. Symbol `p` is both the FAO-56 depletion fraction (Task 1) and the strategy index (Task 2); noted in Table t1par, rename if it confuses readers.

# M2 update — 2026-11-11

M2 is implemented as a scenario-only cohort MILP; no figures generated. Read [M2 audit](20261111_m2_audit_and_implementation.md) and [figure handoff to Claude](20261111_m2_figure_handoff.md). Use `Results/v7/model2/`; preserve the completed M1 figures. M3 is still pending.

# Handoff to Astra — 2026-11-11: M1 figures redrawn from the new tables

Written by Claude.

**Added**
- `Code/v7_m1_figures.py` — draws 9 figures from `Results/v7/model1/*.csv` and `model1_results.json` only (no model re-run). Run: `.venv/bin/python Code/v7_m1_figures.py` (needs matplotlib; not in `Code/requirements-m1.txt`).
- `Figures/M1/` — `m1_f01`…`m1_f09`, each as PDF + PNG, plus `Figures/M1/README.md` (what each figure shows, which table it uses, caveats).

**State**
- All 9 figures checked by eye; numbers on figures match the tables (e.g. steady V 17.9 % at 300 mm/yr, 24.1 % at 600; hold-out RMSE 0.0635 vs persistence 0.0536).
- English labels, Times font, 6.3 in wide to fit `Paper/main.tex`.
- The 13 earlier figures are preserved in `Figures/v7_init_test/`, including `m1_fig1_station_evidence.png` and `m1_fig2_transfer_and_water.png`.

**Next**
1. Choose which figures go into the paper's Model 1 section and copy their PDFs to `Paper/Figure/`.
2. Write captions that carry the caveats (figures have no footnotes; list in `Figures/M1/README.md`) (V is a cover proxy; model does not beat persistence; CON4 is retrospective; water parameters and k are scenarios).
3. Use `Figures/v7_init_test/` to locate the earlier diagnostics when comparing versions.

---

# Handoff to Astra — Model 1 on v7, state on 2026-11-10 (evening)

> Superseded by [the M1 audit and implementation](20261110_m1_audit_and_implementation.md).
> Notes below are historical, not current pipeline instructions. CON4 is retrospective;
> free r/d/K are non-identifiable; dynamic water storage is now implemented.

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

## First-trial daily model: archived on its own branch

The first-trial daily model (FAO-56 water balance, more parameters) is **not** in this branch any more. Its code (`Code/m1_*.py`), raw and processed data, results, figures, its own handoff note and the two Task 1 improvement notes stay on branch `model1-first-version` (tip f0b7750) and can be restored from there with `git checkout model1-first-version -- <path>`.

Kept on `main` as the record of that version (write-up and PDFs in `archive/model1_first_trial/`):

- `archive/model1_first_trial/20261110_audit_check_and_model1.md` — audit check, daily model, results, limits
- `archive/model1_first_trial/model1_en.pdf`, `model1_zh.pdf` (with `.tex`; the figures they include are on the old branch)
- `Data/v7/section_modis/` (not archived, still in use) — the five small tables `v7_model1.py` needs from it

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
