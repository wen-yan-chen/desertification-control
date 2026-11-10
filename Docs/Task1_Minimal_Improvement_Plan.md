# Task 1: improve accuracy while keeping the model simple

Date: 2026-11-10  
Scope: Task 1 only. Assume all supplied data are valid.

## Decision

**Keep the current daily vegetation–water–sand model in `Reports/model1_en.pdf`. Use the revised specification in `Reports/model.pdf` selectively, rather than replacing the implementation with the entire proposed framework.**

The revised specification provides useful modelling checks, but it does not present calibrated evidence that all its additional mechanisms improve accuracy. More physical detail can introduce parameters that the observations cannot distinguish.

This is the recommended immediate plan. The earlier [detailed improvement note](Task1_Model1_Improvement_Recommendations.md) is a menu of possible extensions, not a requirement to implement them all. No model code is changed by this document.

## What to retain

Keep the current model's:

- Daily root-zone water balance and effective moisture state.
- Separate transpiration and soil evaporation, irrigation efficiency and drainage.
- Water stress acting on vegetation growth and mortality.
- Vegetation suppression of sand transport and surface-moisture adjustment of the wind threshold.
- Held-out evaluation and comparison with simple baselines.

Changing from depletion `Dr` to storage `S` is not itself an accuracy improvement. With the same root depth and field capacity, the two are related by `S = 1000 × Zr × theta_fc − Dr`. Differences in process assumptions and calibration matter more than the choice of state notation.

## What to borrow from the revised specification

| Element | Immediate action | Complexity added |
|---|---|---|
| Observation-to-state matching | Match simulated and observed moisture by depth, time and land unit | Observation mapping; no new dynamic state |
| Joint vegetation–moisture evaluation | Score both states from the same coupled simulation | Additional evaluation; joint fitting where supported |
| Parameter identifiability checks | Check whether different parameter combinations fit similarly | Analysis, without extra mechanisms |
| Local variation | Introduce only if persistent spatial errors remain | Initially at most a small supported subset of local parameters |
| Salt stress | Defer until evidence shows it is needed | Potentially substantial |
| Friction-velocity and absolute sand-flux formulation | Retain relative drift potential initially | Avoids adding roughness and transport-conversion parameters |
| Burial state and boundary sediment balance | Defer unless absolute burial or erosion is a required output | Substantial |

## Step 1 — evaluate both states without changing the equations

The current establishment calibration assumes adequate irrigation. It can constrain growth rate and maximum cover, but it does not independently establish the model's response to water shortage.

First compare simulated vegetation and moisture against matching observations. For the existing uniform root-zone bucket, predicted mean volumetric moisture is:

`theta_root = theta_wp + M × (theta_fc − theta_wp)`.

Only compare this directly with observations representing the same root zone. Shallow moisture requires a separate mapping; a valid product without irrigation represents a different management condition from an irrigated cell. Do not treat these differences as measurement errors that calibration must absorb.

Use the coupled simulator's own predictions for all scores. A separate moisture regression can be a baseline, but cannot validate the simulated moisture state.

**Deliverable:** one table of held-out vegetation and moisture RMSE, bias and R², with matching observation definitions. If suitable moisture observations are unavailable, explicitly state that the moisture state and irrigation-response curve remain unvalidated.

## Step 2 — constrain a few influential parameters

Prioritize the existing drought mortality coefficient `m_w` and basal transpiration coefficient `kcb_full`, because current sensitivity results show that they strongly influence irrigation requirements. Check their interaction with root-zone storage and groundwater supply rather than fitting all parameters freely.

Use adequately watered establishment observations for growth parameters, and matching water-limited observations for stress and water-use parameters. Where both vegetation and moisture observations exist, use a joint objective with documented error scaling and weights.

Check whether substantially different parameter combinations produce similar fits. If they do, report a joint range of plausible predictions. Do not select a single combination merely because it gives a desirable irrigation requirement. Without suitable water-response observations, retain bounded parameter scenarios rather than claiming new calibration accuracy.

**Deliverable:** an updated water–cover curve with a clearly labelled uncertainty or scenario band. The existing 400–750 mm/year sensitivity range is not a statistical confidence interval.

## Step 3 — add complexity only when errors justify it

After Steps 1–2, inspect held-out errors:

| Error pattern | Smallest next change to compare |
|---|---|
| Repeatable seasonal timing errors | A simple phenology correction, evaluated at the satellite observation timescale |
| Persistent site-specific cover bias | Local maximum cover, with other parameters initially shared |
| Persistent natural-land moisture bias | Revisit supported groundwater supply or storage assumptions |
| Errors linked to salinity or measured burial | A targeted mechanism, only with observations to constrain it |

Do not introduce all changes together. Compare one addition at a time with the current model using the same validation blocks. Keep related pixels and repeated cohort observations together when splitting data, and reserve a final test set for the selected model.

Daily simulation does not itself prove seasonal accuracy: the current main cover evaluation uses annual peak-season summaries. Define whether `V` represents green cover or persistent physical shelter before interpreting seasonal satellite variation.

## Checks before accepting a revision

- Keep a physical water ledger and inspect any storage-bound corrections; a small residual alone does not validate process allocation.
- Compare vegetation results with a simple logistic establishment model, and moisture results with appropriate climatology or persistence baselines.
- Evaluate both states separately so that improvement in one cannot hide deterioration in the other.
- Distinguish first crossing of a cover target from sustained attainment and long-run maintenance. The current 600 mm/year first-crossing result and approximately 624 mm/year mean-maintenance result describe different criteria.
- Retain an extension when its held-out benefit, physical interpretation and parameter support justify its complexity. Do not prescribe a minimum R² or require a favourable result.

## Recommended next version

**Keep the existing dynamic states and core equations. Improve observation matching, constrain the few important water-response parameters, and quantify uncertainty. Add local or seasonal flexibility only if a specific remaining error supports it.**

This approach can improve the credibility of predictions without guaranteeing a higher score. Whether accuracy improves must be determined by held-out evaluation. Salt balance, burial dynamics and absolute transport can remain later options rather than immediate requirements.

## Project references

- [Current Task 1 model](../Reports/model1_en.pdf).
- [Revised candidate specification](../Reports/model.pdf), Sections 2.1–2.4.
- [Current simulator](../Code/m1_model.py).
- [Calibration and evaluation](../Code/m1_run.py).
- [Stored baseline results](../Results/model1/model1_results.json).

The candidate specification is distinct from the older archived report under `Reports/invalidated_20261109/`. This plan treats document contents as reference material; the selected scope and validity assumption come from the user's request.
