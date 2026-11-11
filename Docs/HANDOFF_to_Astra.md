# Handoff to Astra — 2026-11-11: M2 minimum-cover rule, tables and figures regenerated

Written by Claude, at the request of the user's colleague.

**Changed**
- `Code/v7_m2_core.py`: new `meets_min_cover`. A batch scores ecological ha-years only if its irrigation path brings the cover proxy to `min_cover_pct` by the end of age `min_cover_by_age_year` (judged on the full-horizon path; cost and water are always charged). New array `counted_effective_ha` is the score; `effective_ha` is unchanged. Threshold 0 reproduces the old model.
- `Data/v7/m2_inputs/scenario.json`: `min_cover_pct=20`, `min_cover_by_age_year=10`, scenario id `illustrative_15y_v2_min_cover`. Both values are assumptions; no site-verified protection threshold exists in the repo.
- `Code/v7_model2.py`: four `group=threshold` runs (rule off, 15%, 25%, age 12); `policy_library.csv` gains `meets_min_cover`, `cohorts.csv` gains `counts_toward_score`.
- `Code/test_v7_m2.py`: 8 tests (new one for the rule; the exhaustive-enumeration test switches the rule off because it uses a 100 mm library).
- `Results/v7/model2/*` and `Figures/M2/*` regenerated. `Code/v7_m2_figures.py` no longer hard-codes the cohort set or axis ranges, draws the threshold in f02, and marks infeasible cases in f06.
- Docs: update section at the top of `Docs/20261111_m2_audit_and_implementation.md` (old vs new table), `Data/v7/m2_inputs/README.md`, `Results/v7/model2/README.md`, `Figures/M2/README.md`.

**State (verified by running)**
- Base: 100 ha (50 ha in years 1 and 2, 300 then 600 mm), 10 MW PV, net present cost 7.04 M CNY, score 529.1 against target 522.5; maximum-ecology reference 870.9 (was 2097.0). 33 runs, 32 feasible; `initial_cover_low` is infeasible at the fixed target. M1+M2 tests pass (17).
- Read before writing about it: the old base plan re-scored under the rule gets 259 of its 1265 ha-years; the cost drop comes from the smaller "60% of reference" target, so old and new costs are not comparable; and with the rule switched off at the new target the plan is identical, so the rule binds the reference and the high-target end, not the base plan.

**Not done**
- `Reports/M2/` (writing brief, structure) and `Reports/model_v7` still quote the old M2 numbers and the linear score.

**Next**
1. Update the M2 text and brief in `Reports/` with the rule and the new numbers.
2. Find a literature or field value for the protection threshold; 20% at age 10 is a placeholder and the 25% case costs 63% more.
3. `finer_area_grid` now changes the plan (−3.2%): consider 25 ha blocks as the base grid.

# Handoff to Astra — 2026-11-11: M1 and M2 writing briefs

Written by Claude.

**Added**
- `Reports/M1/M1_writing_brief.{tex,pdf}` (9 pp) and `Reports/M2/M2_writing_brief.{tex,pdf}` (11 pp), in English for writing the paper: goal vs problem requirements, structure diagram, every formula with its meaning, parameter table with values and status, results tables, decision rules (M2), can/cannot-claim lists, figure list, suggested section outline.
- `Reports/M1/m1_structure.{tex,pdf}`, `Reports/M2/m2_structure.{tex,pdf}` — model structure diagrams drawn with the TikZ kit in `FigureAndFlowworkStyle/WorkFlowStyle/`; usable in the paper.
- Later the same day: an "Algorithms" section was added to both briefs, before Parameters (M1: calibration, one model year, scenarios/fixed point; M2: build MILP, two-step ε-constraint solve, replay check). Each algorithm names the matching functions in `Code/v7_model1.py`, `v7_m1_run.py`, `v7_m1_water.py`, `v7_m2_core.py`, `v7_model2.py`. M1 brief now 11 pp, M2 12 pp.
- Added `Code/v7_m1_bucket_figure.py` → `Figures/M1/m1_f10_bucket_mechanism.{pdf,png}` (bucket schematic, K_s ramp, daily storage at 300 and 1,500 mm/yr, demand vs transpiration). It re-runs the bucket day by day with the adopted M1 parameters and asserts that monthly totals and W match `water_year`. Inserted in the M1 brief after Algorithm 3 (brief now 12 pp); M1 algorithms were also simplified (data preparation split out, calibration written as linear regression).
- Build: `pdflatex` twice in each folder. All numbers were copied from `Results/v7/model1/` and `Results/v7/model2/`; no model was re-run.

**Moved**
- Old drafts `Reports/M1/model1_v7_{zh,en}.{tex,pdf}` → `archive/model1_v7_drafts/` (outdated numbers; replaced by the M1 brief). Their LaTeX build files were deleted. Links updated in `Reports/README.md`, `archive/README.md`, `archive/model1_first_trial/README.md`, `Results/v7/model1/README.md`.
- `Reports/model_v7.{tex,pdf}` and `Reports/m2_correction.tex` → `Reports/model_v7/` (the `\input{m2_correction.tex}` still resolves; recompiled there with XeLaTeX ×2, 25 pp, no errors). Links updated in `README.md`, `Reports/README.md`, `Docs/20261111_m2_audit_and_implementation.md`, `archive/invalidated_20261109/README.md`. Older handoff entries below still say `Reports/model_v7.tex`; they are history.
- `Reports/` now holds `M1/`, `M2/`, `model_v7/`, plus `preprocess_v7.*` at the root.

**State**
- Both briefs compile without errors or overfull boxes. Numbers checked against the CSV/JSON results (fit table, water–cover curve, scenarios, sensitivity; base plan, yearly ledger, frontier, 21 sensitivity cases, PV screening).
- Derived values computed here, not stored in the result files: M1 ET0 total 1,685.6 mm/yr and marginal cover per mm; M2 marginal cost per effective ha·yr between frontier points (22.6, 22.8, 26.3, 36.7, 57.1 k CNY) and PV saving vs no-PV (2.49 M, 9%).

**Next**
1. Write the Model 1 and Model 2 paper sections from these briefs; if results are regenerated, update the briefs' tables.

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

## 2026-11-11 — Section 3 outline + station map
- `Paper/main.tex` §3 rewritten as prose in two subsections (Study area and station categories; Data sources and preprocessing), with dimidiate-pixel cover equation and citations REF01, REF06, CN16, REF15, EN10 added.
- New `Code/v7_data_stations_figure.py` regenerates `Paper/Figure/data_stations.{pdf,png}` on an Esri World Imagery basemap (tiles cached in `Data/v7/raw/basemap_tiles`). Run with `.venv/bin/python`.

## 2026-11-11 — Model 1 sketch in the paper
- New `Paper/Section/model1.tex` (input from `main.tex`, replaces the Model 1 placeholders): logic chain + structure figure, cover equation, daily bucket, W-bar link, calibration as linear regression, Algorithm 1 (one model year), results with figs f02, f06, f07, f10.
- `main.tex`: added `algorithm`/`algpseudocode`; `\graphicspath` now also reads `../Figures/M1/` and `../Reports/M1/` (for `m1_structure.pdf`).
- No parameter table on purpose; numbers in text come from `Reports/M1/M1_writing_brief.tex`.

## 2026-11-11 — Model 1: W-bar explanation + two-clocks figure
- `Section/model1.tex`: new "What W-bar means" paragraph (meaning, 0/0.37/1 examples, 4 reader questions; cites FAO-56 REF11). "Two states on two clocks" rewritten as bold-labelled bullets.
- New figure `Paper/Figure/m1_two_clocks.{tex,pdf}` (standalone TikZ; build with pdflatex in `Paper/Figure`): outer year dial (cover V), inner day dial (bucket M), handoff arrows D_j and W-bar, colour-matched equation panel.
- `main.tex`: `\paragraph` headings now bold (template printed them plain).
- (later) Removed the "What W-bar means" paragraph and its 4 reader questions. W-bar's physical meaning (=1 / between / =0) now sits right after the cover equation, linked to the up-arrow in the two-clocks figure.
- (later) W-bar meaning merged into "The link between the two clocks" as paper-style prose (no bullets); cover-equation paragraph rewritten as prose and points to Eq. (4).
- (later) Bucket figure split for the paper: Fig. 4 schematic (`m1_f10a_bucket_schematic`), Fig. 5 K_s ramp (`m1_f10b_stress_ramp`), Fig. 6 year storage + demand (`m1_f10c_year_water`). Script refactored into panel functions; combined `m1_f10` still written.
- (later) Two-clocks figure redrawn: inner dial = day clock with months (one turn = one year), outer ring = years t-2..t+3 with V_t->V_{t+1} arc at 12 o clock; handoffs numbered (1) D_j down, (2) W-bar up, same numbers in the text list and equation panel. Caption shortened.
- (later) "Two clocks talk" bullets replaced by Algorithm 1 (nested year/day loops, handoffs (1)/(2)); old "One model year" algorithm in Solution approach removed, Steps 2-3 now point to Algorithm 1.
- (later) Algorithm 1 rewritten in plain words (no equations except W-bar); `\AlgWrap` helper added in main.tex so wrapped algorithm lines keep their indent.
- (later) "How the two clocks are coupled" rewritten as a one-year timeline: (1) 1 Jan V_t frozen sets D_j; day clock runs alone; (2) 31 Dec W-bar updates V; M carries over. Step 1 now "calibration by least squares": Eq. 5 regression form with y, z1, z2; Eq. 6 LS objective; Eq. 7 normal equations + closed form; why unique, why K is fixed, cluster bootstrap, hold-out.
- (later) Reverted the "two clocks coupled" timeline back to the short two-bullet version (1 Down / 2 Up + carry-over line). Least-squares Step 1 kept.
- (later) Model 1 intro: "chain of four links" is now an inline TikZ arrow chain (Water arrives -> Root-zone store -> Demand met -> Cover changes, solid feedback arrow 4 back to the store), followed by a numbered sentence; added tikz `calc` library in main.tex.
- (later) Four-link chain simplified: boxes show symbols only (P,I -> M_j -> W-bar_t -> V_t), arrows lettered a-d (letters avoid clash with clock badges 1/2); sentence below explains a-d.
- (later) Bucket schematic (Fig. 4) redrawn in TikZ: `Paper/Figure/m1_bucket.{tex,pdf}` (blue water, green plant/transpiration, red dashed capacity and threshold, braces for stressed / no-stress zones). Replaces m1_f10a in the paper; the matplotlib m1_f10a file is still generated but unused.
- (later) Least-squares stacking / normal equations / closed form moved into Algorithm 1 "Least-squares calibration of r and d" (also bootstrap + hold-out); Eq. 7 removed. The one-model-year algorithm is now Algorithm 2.
- (later) Fig. 4 bucket: added gross input (rain + irrigation), grey branch "evaporation & losses (1-alpha_P)P+(1-eta_w)I", "effective inflow" label; outflow relabelled "plant transpiration (root uptake only)". Text after Eq. 3 now says evaporation is removed at the inflow and T_a is transpiration only. User-edited caption left as is.
- (later) Moved the year-water figure (now Fig. 8) and its 37% paragraph from "link between two clocks" into Results as "Why the curve flattens" (right after the water-cover curve). Removed the Model 1 "Wind index" paragraph; its daily-first-then-average rationale merged into the Section 3 wind-index item in main.tex; cover equation now points to Section 3 for E_t.
- (later) Model 1 Results rewritten as "Results: answering Task 1": trust check -> how V and M change (3 phases + stop case + within-year) -> drivers (1) water supply, (2) demand/delivery/wind with new sensitivity figure f09 -> boxed "Answer to Task 1" incl. implication for Model 2. Numbers from Reports/M1/M1_writing_brief.tex. Model 1 now ~10 pages (pp. 8-17).
- (later) Model 1 Results reworded in academic register (no new content): headings Model reliability / Evolution of the state variables / Controlling factors: water supply / Controlling factors: demand, delivery and wind; bullets turned into prose; box renamed "Summary of findings for Task 1".
- (later) Results language simplified; phases, irrigation returns and factor groups now numbered lists. No content change.
- (later) Added Model 1 parameter table (Table "Model 1 parameters", label tab:m1-par) at end of 5.2 Solution approach: fitted (r, d with bootstrap 95%), data rules (K, V_full), assumed scenario values with tested ranges. Values from Reports/M1/M1_writing_brief.tex sec:par.
- (later) Model 1 trimmed to pp. 8-14: removed K_s ramp figure, calibration-check figure, year-water figure, summary box; figure captions and figure descriptions shortened; short "Summary" paragraph at the end. Figures/tables now float (!htb), lists compacted, no large page gaps.
- (later) Added demand + stress formulas (new Eq. 4): D_j = c min(1, 2V_t/V_full) f(T_j) ET0_j, K_s = min{1, M_j/((1-p)C)}, f(T) = min{1, max{0,(T-5)/20}}. c is called "transpiration coefficient" everywhere (table, text, and f09 label via Code/v7_m1_figures.py; f09 regenerated). Removed G row from parameter table (G = 0, not in the paper equations); Section 3 wind index now states u_T = 5 m/s.
- (later) Parameter table rebuilt: columns Symbol | Meaning | Value | Range tested | Unit, three groups (fitted / data rule / assumed), dagger = bootstrap 95% interval; V0 and M0 split into two rows. Table and Algorithm 2 pinned with [H] so the order is Alg 2 -> Parameter values + Table 4 -> 5.3 Results. Fig 7 pinned after its list, Summary last; Model 1 still ends p. 14.
- (later) Station series figure (m1_f01, suptitle removed in Code/v7_m1_figures.py and regenerated) combined with the scenario-path figure as Fig. 5 (a) observed 2015-2025, (b) scenarios 2026-2050 (subfigures, labels fig:m1-obs / fig:m1-scen). Model reliability now cites 5a (free run misses the 2023-2025 greening). Float pages top-aligned via \@fptop=0pt in main.tex. Model 1 now pp. 8-15.
- (later) Fig. 5 now side by side: (a) m1_f01_station_series_tall (4x2), (b) m1_f07_scenario_trajectories_tall (3 stacked panels, titles without letters). New tall=True options in Code/v7_m1_figures.py; wide originals unchanged. Fig. 5 placed [!t] so text fills below it. Model 1 = pp. 8-15. Note: Table 4 caption was shortened outside this session; the dagger on r, d ranges is no longer explained.
- (later) Controlling factors now two-column (text left, figure right via minipage + 