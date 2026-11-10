# Recommendations for improving the new Task 1 model

Date: 2026-11-10  
Scope: Task 1 only — coupled vegetation, effective soil moisture and wind–sand dynamics.  
Working assumption: all supplied data are valid. These recommendations concern model structure, parameter estimation, observation matching and predictive evaluation, not a repeat of the data-source audit.

## Recommendation

Keep the new model as the foundation. Its daily root-zone water balance and vegetation–water–sand feedbacks are more suitable for studying irrigation and vegetation response than the older monthly formulation. Improve its observational constraints before adding more equations.

The first priority is **joint evaluation of vegetation and moisture under water-limited conditions**. The present establishment calibration assumes demand irrigation, so it mostly identifies potential growth and maximum cover. It does not establish the response to irrigation shortage. A physically reasonable equation is useful, but that response still needs its own evidence.

This note proposes changes; it does not implement them or claim that the revised model has been validated.

## 1. Current strengths and limits

Retain these parts of the new model:

- Root-zone depletion in mm and normalized effective moisture, rather than an unconstrained percentage balance.
- Separate transpiration and soil evaporation, explicit irrigation efficiency and drainage.
- Vegetation suppression of sand transport and moisture-dependent wind threshold.
- Daily simulation, held-out evaluation and comparisons with simple baselines.

The current results establish a useful starting point, with clear limits:

| Existing result | Interpretation for improvement |
|---|---|
| Establishment hold-out R² approximately 0.29; logistic baseline approximately 0.29 | The additional mechanisms have not demonstrated extra establishment prediction skill under this evaluation. |
| Natural-cover hold-out R² approximately −0.76 | Reproducing mean cover is insufficient to explain annual changes. |
| Minimum irrigation approximately 624 mm/year in the baseline run | This is a conditional simulation result, not a directly observed requirement. |
| Strong sensitivity to drought mortality and the basal transpiration coefficient | These parameters deserve priority over adding many weakly constrained processes. |

These results are taken from `Results/model1/model1_results.json` and `Reports/model1_en.pdf`. Valid data do not guarantee that every parameter can be identified from the particular variables and conditions used in calibration.

## 2. Priority 1 — constrain both vegetation and effective moisture

### Match the model to the observations

For a uniform root-zone interpretation, the existing state implies:

\[
M=1-D_r/\mathrm{TAW},\qquad
\widehat{\theta}_{root}=\theta_{wp}+(\theta_{fc}-\theta_{wp})M.
\]

Compare this prediction with observations representing the same depth, area and time period. A shallow surface-moisture series is not automatically an observation of the complete root zone. If observations are layered, use a documented depth-weighted estimate or a layer-specific observation model. Keep the current single root-zone bucket initially; add another layer only if the observations and residuals justify it.

Validity and applicability are separate: a valid moisture product without irrigation cannot directly validate the moisture of an irrigated cell. Use it for the matching natural-land case, or state the difference in represented management.

### Use one coupled simulation for calibration and scoring

Where suitable observations exist, estimate parameters using both states. One possible objective is:

\[
J(\vartheta)=
\frac{w_V}{n_V}\sum_i\left(\frac{V_i^{obs}-H_V(x_i)}{\sigma_{V,i}}\right)^2
+\frac{w_M}{n_M}\sum_j\left(\frac{M_j^{obs}-H_M(x_j)}{\sigma_{M,j}}\right)^2
+\lambda R(\vartheta).
\]

Here, `H_V` and `H_M` map simulated states to the observation support; `sigma` describes observation uncertainty; and `R` constrains implausible parameter departures. Document the weights and check whether conclusions change with reasonable alternatives. Normalization prevents a more frequently sampled variable from dominating merely through record count.

Use the same recursive simulator to generate both predictions. A separate moisture regression may be a baseline, but its score must not be reported as validation of the coupled moisture state.

### Estimate parameters in stages

1. Use adequately watered establishment observations to constrain growth rate, maximum cover and initial cover.
2. Use matching moisture, water application and, where available, evapotranspiration observations to constrain storage and water use.
3. Use water-limited observations to constrain drought mortality and stress response.
4. Jointly refine only the subset supported by these observations, keeping the remaining parameters fixed or within documented ranges.

In particular, assess `m_w`, `kcb_full`, root-zone storage and groundwater supply together. Different combinations may reproduce similar cover. Inspect parameter profiles and correlations; if parameters remain inseparable, propagate their joint uncertainty instead of reporting unique estimates. If the necessary water-response observations are absent, label the irrigation response as scenario-based and proceed with a bounded ensemble.

## 3. Priority 2 — test seasonal dynamics at the observation timescale

The model runs daily, but its main vegetation calibration uses annual peak-season cover. That evaluation cannot establish whether it reproduces green-up, seasonal peaks or senescence.

Derive a seasonal vegetation series from the existing 16-day observations. Apply the same temporal aggregation to simulated output and score seasonal and annual behaviour separately. Report peak timing, seasonal amplitude, bias and anomalies after removing the mean seasonal cycle.

Before interpreting seasonal FVC, define whether `V` means green cover or persistent physical canopy cover. Satellite greenness and year-round aerodynamic shelter need not change identically. Start with a documented observation mapping; introduce a separate structural-cover state only if the available evidence supports estimating it.

If residuals show repeatable seasonal errors, compare the current temperature ramp with a small phenology extension, such as separate green-up and senescence timing. Test a high-temperature decline only if residuals support it. Retain any extension only when it improves held-out seasonal performance. Do not automatically restore four freely fitted harmonic coefficients per location.

## 4. Priority 3 — restore limited local variation

The older approach allowed a separate parameter set at each station. The new approach shares a more restrictive parameterization across locations. Recover useful heterogeneity without fitting every process independently at every site.

Start by comparing:

| Candidate | Parameters allowed to vary locally | Purpose |
|---|---|---|
| A: current shared model | Existing local forcing and initial conditions | Reference case |
| B: limited local variation | Maximum cover and supported groundwater supply | Represent persistent site differences |
| C: additional local process variation | Growth or storage, only when supported by observations | Address remaining systematic errors |

For positive parameters, a partially pooled form such as `log(r_s) = log(r_global) + u_s` with a penalty on `u_s` can limit overfitting. Use a bounded transformation for cover parameters.

Evaluate on entire withheld windows or spatial blocks. Nearby pixels and repeated observations of the same cohort should remain together. For a new location, distinguish predictions using global parameters from predictions using locally calibrated parameters.

The current windows were identified using both early and late imagery. This supports retrospective analysis of those selected land classes; it should not be described as prospective identification of future successful conversion sites.

## 5. Priority 4 — strengthen the sand component selectively

Keep the existing vegetation–sand and moisture–sand feedbacks. Improve the interpretation and calibration of their parameters:

- Check that wind height, threshold, knots-to-m/s conversion, temporal averaging and DP normalization match the conventions underlying transferred coefficients. A change in DP scale requires a corresponding coefficient change.
- Treat critical cover `v_c` and damage coefficients as locally uncertain rather than universal constants. Estimate them where suitable cover–transport or damage observations exist.
- Describe the tanh response as smooth suppression. At `V = v_c`, its value is `(1 - V)/2`; transport is not exactly zero at that threshold.
- If absolute transport observations are available, calibrate an observation relation such as `q_hat = c_q * g(V, M, U)`, defining the units of `q` and the coefficient. Evaluate it on withheld transport observations.

The old formulation used absolute transport as an external input; it did not thereby predict absolute transport through vegetation feedback. Adding a calibrated absolute-output relation would extend the new model, rather than simply restore an old capability.

If only relative potential is supported, retain that output. Converting line flux to areal erosion or burial requires explicit geometry and a sediment balance; a scalar change of units is insufficient.

## 6. Priority 5 — make uncertainty and threshold claims consistent

Replace sole reliance on one-at-a-time sensitivity with an ensemble that varies important parameters jointly. Prioritize `m_w`, `kcb_full`, growth rate, maximum cover, root-zone storage, irrigation efficiency and `v_c`. Preserve parameter dependencies where calibration identifies them.

Recompute the water–cover curve for every accepted ensemble member. Report median curves, uncertainty bands and cases where the target cannot be reached within the investigated irrigation range. Use spatial/cohort block resampling for fitted-parameter uncertainty where feasible.

Call bands based on assumed parameter ranges **scenario envelopes**. Do not label the existing 400–750 mm/year range a statistical confidence interval. Any probability of meeting a target is conditional on the specified ensemble distribution.

Also separate three different quantities:

1. **First attainment:** the first year cover crosses a target.
2. **Sustained attainment:** cover meets a predeclared persistence criterion, such as five consecutive peak seasons.
3. **Long-run maintenance:** cover remains adequate under the defined long-run forcing and summary statistic.

The present results show first attainment of 30% cover at 600 mm/year after 13 years, while reporting long-run cover near 29% at that quota and approximately 624 mm/year for mean maintenance. These need not conflict: a transient or favourable year can cross a target that the long-run mean does not meet. Report the definitions beside the numbers.

The existing long-run curve repeats historical weather and averages the final ten peak seasons. Label it accordingly; check sensitivity to the weather-cycle phase and averaging window before calling it an equilibrium.

## 7. Priority 6 — verify physical and numerical accounting

The current water ledger is useful, but a small residual alone does not validate process allocation. Check the following before expanding the model:

- Surface evaporation and transpiration must draw from explicitly represented stores without double counting.
- The `below_wp` correction in `simulate()` must represent depletion of an actual store below the root-zone available-water range if it is nonzero. Including a correction in a ledger does not by itself supply the physical water. Report its magnitude separately and demonstrate closure for all represented stores.
- Test dry-down, heavy rain, irrigation refill and near-zero vegetation cases. Water inputs, storage changes and outputs should agree without unexplained sources.
- Document daily ordering of wetting, evaporation, transpiration and drainage; assess whether it materially changes irrigation-response conclusions.
- Check daily-step results against a finer integration step for representative cases, with forcing and event timing handled consistently.
- Document initialization and warm-up effects. For forecasting claims, use causal temperature smoothing; the current centred 15-day mean is appropriate only when the necessary future weather is available or for retrospective simulation.

FAO-56 describes the daily root-zone depletion balance and the dependence of transpiration stress on available water; it also treats surface evaporation with its own daily balance. These provide the physical reference for the accounting checks, rather than evidence that local parameters are correct. See [FAO-56 Chapter 8](https://www.fao.org/4/X0490E/x0490e0e.htm) and [Chapter 7](https://www.fao.org/4/x0490e/x0490e0c.htm).

## 8. Implementation order and acceptance criteria

| Order | Work | Main files | Evidence required |
|---|---|---|---|
| 1 | Observation mapping and water-accounting checks | `Code/m1_model.py`, `Code/m1_build_dataset.py` | Defined depth/time support; physical storage closure; correction magnitudes reported |
| 2 | Joint-state evaluation and staged calibration | `Code/m1_run.py` | Held-out V and moisture scores; parameter identifiability assessment |
| 3 | Seasonal evaluation and limited local variation | Dataset builder and calibration driver | Seasonal residuals; spatially blocked comparison with the shared model |
| 4 | Joint uncertainty and consistent target definitions | Calibration and response-curve routines | Conditional water–cover bands; first/sustained/long-run attainment reported separately |
| 5 | Optional phenology or absolute sand-output extension | Simulator and observation mappings | Additional held-out skill or a demonstrated new measurable output |

Freeze a final test set before model selection. Compare candidate structures using training/validation blocks, then evaluate the selected model once on the final test set. Report R², RMSE and bias for each state separately, alongside climatology, persistence and a plain establishment logistic curve. Interpret persistence carefully: a one-step prediction using the previous observation is a different information setting from a multi-year free-running simulation.

Do not prescribe an R² target or require the coupled model to beat every baseline. Accept an extension when its physical interpretation is defensible, parameters are sufficiently constrained for the intended claim, and its held-out benefit justifies its complexity. Report failures as well as improvements.

## 9. Recommended next version

The next version should remain a compact daily vegetation–water–sand model, with:

- Explicit observation mappings and joint V–moisture evaluation.
- Water-limited calibration or clearly bounded water-response scenarios.
- Seasonal checks and a small amount of supported local variation.
- Joint parameter uncertainty and consistent definitions of cover attainment.
- Verified physical water accounting.

Do not add spatial PDEs, salinity states or a separate canopy state by default. Consider them only when the current residuals expose a relevant missing mechanism and the available observations can constrain the extension.

## Sources and inspection basis

Local references, relative to this note:

- [New Task 1 report](../Reports/model1_en.pdf), especially formulas, validation, sensitivity and limitations.
- [Older report](../Reports/invalidated_20261109/Reports/model.pdf), Task 1 equations and calibration discussion.
- [Current simulator](../Code/m1_model.py), especially `Params`, `simulate()` and `sand_switch()`.
- [Current calibration and analysis](../Code/m1_run.py), especially `fit_establishment()`, `fit_ecotone()`, `steady_cover()`, `establishment_time()` and `sensitivity()`.
- [Current dataset builder](../Code/m1_build_dataset.py), especially seasonal aggregation and temperature smoothing.
- [Stored numerical results](../Results/model1/model1_results.json).

All extensions and acceptance criteria in this note are recommendations based on the inspected implementation. Existing numerical results are baseline results, not results of the proposed changes.
