# 2026-11-10 · Audit check, fixes, and Model 1 (first version)

Scope: Task 1 of 2026 CQU_MCM Problem B. This note (1) checks the 2026-11-09 audit written with GPT, (2) lists what was fixed and how, (3) documents Model 1 as built, with every number traced to a file. All numbers below are produced by `Code/m1_run.py` and stored in `Results/model1/`.

Status in one paragraph: the audit's criticisms of the old data and model are correct and I found three more structural problems. Its conclusion, "no formal model until local GIS boundaries, permits and cost sheets are obtained", is not workable for this problem, which gives no data and asks teams to consult public data and state assumptions. The data layer has been rebuilt for one defined section with verified public sources, and a first coupled vegetation–water–sand model runs on it. The model reproduces levels and establishment curves; it does **not** explain year-to-year variation of natural cover, and its water-requirement numbers depend strongly on two uncertain parameters. Both limits are stated with numbers in §5–6.

---

## 1. Check of the 2026-11-09 audit

Verdicts come from reading the archived code (`archive/invalidated_20261109/Code/`) and re-querying the data providers.

| # | Audit claim | Verdict | Evidence | What was done now |
|---|---|---|---|---|
| 1 | Station "sand transport" was scaled to hand-set targets 400–3200 t/km²/a | **Confirmed** | `01_fetch_real_data.py`, `target = {...}` dict and the rescaling loop below it | Variable dropped. Sand driver is now drift potential from hourly wind (§3) |
| 2 | kg/(m·s) converted to t/km² by a constant; daily max wind held for 24 h | **Confirmed** | `lettau_monthly()`: `q*86400*1000/1e6`; a line flux cannot become an areal mass without a width | No areal erosion mass is claimed. DP is a time-mean of U²(U−Uₜ) over hourly values |
| 3 | Soil-water equation had no depth, mixed % and mm, clipping created water | **Confirmed** | old `simulate()`: `np.clip(W, 0.1, 45)` | Root-zone balance in mm with a ledger; residual 1e-12 mm over 24 years |
| 4 | "Hargreaves PET" was a linear temperature proxy | **Confirmed** | `pet_mm()`: `2.6*(T+17.8)/25*30` | Full FAO-56 Penman–Monteith; checked against two independent sources (§2) |
| 5 | No hold-out; reported soil-water R² came from a separate OLS | **Confirmed** | `main()`: `R2_含水率` uses `water_regression()` | Spatial and temporal hold-outs; scores are of the coupled model only, next to baselines |
| 6 | Task-2 DP did not use the Task-1 model; unit slip in O&M | **Confirmed** | `dp_plan()`: `V_of(A)` is a fixed power law; `maint*A_new` lacks ×1000 | Out of scope today. Model 1 exposes the hooks Task 2 needs (§7) |
| 7 | Resilience used a monthly AR(1) as yearly; λ=0.35 hard-coded; "recovery time" mis-defined | **Confirmed** | `ar1_params()`, `resilience()` | Out of scope today (Task 3) |
| 8 | "2050 projection" was a flat line | **Confirmed** | `longterm()`: `w_trend` is never used | Out of scope today |
| 9 | Meteorology model unspecified | **Confirmed, and worse than stated** | see N1 below | Model fixed and recorded |
| 10 | NDVI had no QA; fixed end-members 0.05/0.85 | **Confirmed** | `nd.loc[nd_raw == fill]` is the only filter | `pixel_reliability` used; end-members read from section pixels |
| 11 | 8 "stations" are not a belt section; TZ–XT are 36 km apart | **Confirmed** | TZ is in the desert centre; MF is the town | One section defined; old panel not used |
| 12 | Model cannot proceed until local boundary/permit/cost evidence exists | **Overstated** | The problem statement gives no data and says "consult relevant data"; such evidence is not public | Replaced by explicit assumptions A1–A10 with sensitivity ranges (§4, §6) |

### New problems the audit did not catch

**N1. The old weather series has a source change in 2017.** The legacy fetch called Open-Meteo without `models=`. Re-querying shows the default equals ERA5 exactly for 2015–2016 and departs from 2017 on (`Results/model1/legacy_source_break.csv`):

| Minfeng point | 2015 | 2016 | 2017 | 2021 | 2024 |
|---|---|---|---|---|---|
| daily-max wind, default (m/s) | 5.03 | 5.09 | 6.11 | 6.13 | 5.91 |
| daily-max wind, ERA5 (m/s) | 5.03 | 5.09 | 5.03 | 5.26 | 5.11 |
| soil moisture 0–100 cm, default | 0.087 | 0.085 | 0.157 | 0.203 | 0.247 |
| soil moisture 0–100 cm, ERA5 | 0.010 | 0.017 | 0.029 | 0.055 | 0.072 |

A 20 % step in wind is a much larger step in anything cubic in wind, and the "rising soil moisture" is a product switch. Any trend or fit over 2015–2024 on the old panel is contaminated.

**N2. The old V–W "coupling" was a seasonal curve fit.** In the old panel 77–92 % of NDVI variance at vegetated points is the mean seasonal cycle, and NDVI anomalies are uncorrelated with soil-moisture anomalies (r between −0.33 and +0.14). The old model had 13 parameters per station including four free sine/cosine terms, so it could fit the cycle without any coupling. Two of the eight points carry no vegetation signal at all (XT: NDVI 0.058 ± 0.004).

**N3. Reanalysis soil moisture cannot be the "effective soil moisture" target.** ERA5-Land has no irrigation, and on this section its 7–28 cm layer sits at 0.000–0.001 m³/m³ and its 28–100 cm layer drifts by −0.06 per decade (Kendall τ = −0.84). It says only that natural root-zone water is near zero. Effective soil moisture in the belt has to be simulated from a water balance.

**N4. TLS verification was switched off** in both legacy fetchers (`ssl.CERT_NONE`). New code verifies certificates.

**Missing data that mattered:** daily Tmax/Tmin/humidity/radiation (for ET0), hourly wind (for sand), NDVI quality flags, any record before 2015 (most planting on this section happened 2003–2021), and any treated-versus-untreated contrast. All are now in the repo.

---

## 2. Rebuilt data (all public, hashes in `Data/raw/model1/manifest.json`)

**Section (assumption A1).** Southern margin between the Yutian and Minfeng oases, where the belt closed in November 2024 and where the two documented 2024 projects lie. Stylised as 100 km × 1.5 km = 15,000 ha (planned projects: 15,667 ha). There is no public GIS boundary; this is stated, not hidden.

**Windows, chosen by rule not by eye.** Mean summer NDVI of 2001–03 and 2022–24 over the area classifies every 250 m pixel; the purest 9×9-pixel windows per class are taken (`Code/m1_fetch_data.py::select_windows`, `Data/processed/model1/windows.csv`).

| Class | Rule | Windows | Pixels | Role |
|---|---|---|---|---|
| converted | bare in 2001–03, NDVI ≥ 0.25 in 2022–24 | CON1–4 | 218 | treated, irrigated land: establishment dynamics |
| ecotone | 0.09–0.20, stable | ECO1–3 | 242 | natural sparse vegetation, no irrigation |
| desert | < 0.08 both epochs | DES1–2 | 162 | bare reference, soil end-member |
| oasis | ≥ 0.40 both epochs | OAS1–2 | 158 | vegetation end-member |

| Dataset | Source | Period | Notes |
|---|---|---|---|
| NDVI + pixel reliability | MOD13Q1 v061 via ORNL DAAC | 2001–2024, 552 composites | only reliability 0/1 kept; 99.99 % of peak-season pixel-years valid; no interpolation |
| Daily weather, soil layers | Open-Meteo archive, `models=era5_seamless` | 2001–2024 | ERA5-Land for T, dew point, soil; ERA5 for wind, rain, radiation, pressure |
| Hourly 10 m wind, gust, direction | same | 2001–2024 | 210,384 h per site |
| Independent daily weather | NASA POWER (MERRA-2/CERES) | 2001–2024 | cross-check only |

**Cover.** FVC = (NDVI − 0.0505)/(0.5827 − 0.0505), clipped to [0, 1]. Soil end-member is the median of desert pixels (interannual s.d. 0.006); vegetation end-member is the 95th percentile of oasis pixels. Peak season = four composites from mid-July to early September.

**Checks that passed.**

| Check | Result |
|---|---|
| ET0, own FAO-56 PM vs provider vs POWER | 1663 / 1755 / 1717 mm/yr; daily r = 0.996 and 0.96 |
| Hours ≥ 6 m/s from ERA5 hourly mean wind | 450–590 h/yr; Tazhong station record: 550–800 h/yr (Zhang et al. 2016, p. 5) |
| Precipitation | 30–33 mm/yr (ERA5); POWER gives 63 mm/yr, so rain is uncertain by a factor of two |

**Facts from the data (2001–2024).**

| Quantity | Value | Trend per decade (Mann–Kendall p) |
|---|---|---|
| Natural ecotone cover | 0.13 | +0.010 (0.001) |
| Desert cover | 0.005 | +0.001 (0.06) |
| Converted pixels (class median) | 0.00 → 0.53 | establishment years 2003–2021, peak 2015 |
| Precipitation | 31 mm/yr | −6.9 mm (0.10) |
| ET0 | 1663 mm/yr | +19 mm (0.19) |
| Temperature | 13.8 °C | +0.24 °C (0.13) |
| Drift potential, hourly mean wind | 45–55 VU (low-energy) | −2.9 VU (0.29) |
| Drift direction | towards 77–85° (east-north-east), RDP/DP 0.47–0.75 | along the margin |

Year-to-year changes in ecotone cover are not significantly related to rain, ET0 or temperature (|ρ| ≤ 0.26); the only nominal link is with windiness (ρ = −0.43, p = 0.04, one of ten tests, so weak evidence).

---

## 3. Model 1

Daily step, one land cell. Code: `Code/m1_model.py`.

**States.** Cover V ∈ [0, V_max]; root-zone depletion D_r (mm), reported as effective soil moisture M = 1 − D_r/TAW ∈ [0, 1]; two surface-layer depletions (drip-wetted and rain-only exposed soil) used for evaporation and for surface wetness.

**Water** (FAO-56 dual crop coefficient, Ch. 7–9):

- TAW = 1000·Z_r·(θ_fc − θ_wp), M = 1 − D_r/TAW
- K_s = min(1, M/(1 − p))
- T = K_s · K_cb,full · min(1, 2V) · φ(T_a) · ET0
- E = Σ_x K_r(D_e,x) · f_ew,x · K_c,max · ET0, capped by K_c,max − K_cb and by the water present
- D_r ← D_r + T + E − P − η·I − G, excess above field capacity drains

**Vegetation:**

dV/dt = r·φ·K_s·V·(1 − V/V_max) − [m₀ + m_w·φ·(1 − K_s) + ε·g + γ·DP^(2/3)]·V + planting

**Sand:**

- DP = ⟨U²(U − U_t)₊⟩, U in knots at 10 m, U_t = 12 kn, hourly
- g = ½·DP_eff·[tanh(d(v_c − V)) + 1]·(1 − V)
- U_t is raised on a moist surface by √(1 + 1.21(w − w′)^0.68) (Fécan et al. 1999)

**Couplings.** Water → vegetation (K_s in growth and drought loss); vegetation → water (transpiration ∝ min(1, 2V), shading 1 − V); vegetation → sand (g switches off above v_c); sand → vegetation (ε·g and γ terms); water → sand (wet threshold). Sand → water is not modelled.

### Parameters

| Symbol | Value | Unit | Source |
|---|---|---|---|
| θ_fc, θ_wp | 0.12, 0.045 | m³/m³ | FAO-56 Table 19 "Sand" (PDF p. 170), mid-range |
| REW, Z_e | 4.5, 0.10 | mm, m | same table |
| K_c,max, f_w | 1.2, 0.3 | – | FAO-56 Eq. 72; Table 20 (drip) |
| K_cb,full | 1.0 | – | FAO-56 Eq. 98–102; **A: range 0.7–1.2** |
| Z_r | 1.0 | m | A3; Haloxylon roots mainly 0.2–0.8 m (Liu et al. 2022, p. 2) |
| p | 0.6 | – | A4 |
| η | 0.9 | – | A5 |
| G | 0 (treated), fitted (ecotone) | mm/day | water table > 10 m under dunes (Liu et al. 2022, p. 11) |
| r | 1.43 ± 0.28 | 1/yr | **calibrated** (§5) |
| V_max | 0.55 ± 0.03 | – | **calibrated** (§5) |
| m₀ | 0.02 | 1/yr | Yizhaq & Ashkenazy 2021, parameter list |
| m_w | 1.0 | 1/yr | **A6, range 0.3–3** |
| T_base, T_opt | 10, 25 | °C | A7 |
| ε, γ, v_c, d | 0.001, 8e-4, 0.3, 15 | per yr·VU etc. | Yizhaq & Ashkenazy 2021, parameter list |
| U_t | 12 kn ≈ 6.2 m/s | – | same; Zhang et al. 2016 p. 5 uses 6.0 m/s |
| irrigation timing | every 15 d Mar–Oct, 10 d Jul–Aug | – | Zhang et al. 2016 p. 5; Liu et al. 2022 p. 3 |

### Assumptions

- **A1** Stylised 100 km × 1.5 km section; no official boundary.
- **A2** NDVI class thresholds are operational definitions.
- **A3–A5** Root depth, stress threshold, irrigation efficiency: values above, all in the sensitivity run.
- **A6** Drought mortality m_w: no local measurement. This is the weakest number in the model.
- **A7** One temperature ramp drives both growth and transpiration; no heat stress.
- **A8** Dune sand: 1 % clay, bulk density 1.6 g/cm³.
- **A9** No runoff on sand; no interception; no sand-mulch effect on evaporation; salinity not modelled.
- **A10** DP uses ERA5 hourly mean wind. Hourly gusts give 650–750 VU and are an upper bound only.
- **A11** Converted pixels are irrigated land of unknown type (shelter forest, orchard or crop). They identify growth rate and ceiling, not a water response.

---

## 4. What the fits can and cannot support

| Fit | Free parameters | Calibration | Hold-out | Naive baseline on hold-out | Reading |
|---|---|---|---|---|---|
| Irrigated establishment (converted pixels; CON1–3 fit, CON4 held out) | r, V_max, V₀ | R² 0.40, RMSE 0.12 | R² 0.29, RMSE 0.185 | mean: R² −0.02; plain logistic in time: R² 0.29 | Captures the average rise; equals a plain logistic because water is not limiting in these runs. Pixel-to-pixel spread dominates; CON4 plateaus higher than V_max |
| Natural ecotone (fit ≤ 2016, test 2017–24) | G | RMSE 0.008 | R² −0.76, RMSE 0.015 | mean: RMSE 0.015 | Level reproduced with G = 0.45 mm/day (166 mm/yr). **No skill for year-to-year change**; the upward drift after 2017 is missed |
| Bare desert (no fit) | none | – | cover 0.05 → 0.007 in 5 yr; observed 0.002 | – | Rain alone cannot hold cover. With rain only, ecotone cover would fall to 0.001 |

Consequences: r and V_max are usable for planning curves. The model must not be presented as predicting interannual variability of natural vegetation. The fitted G shows the natural ecotone lives on roughly five times the local rainfall, i.e. on groundwater or floodwater, which the belt on dunes does not have.

---

## 5. What the model says (mid-section forcing, `Results/model1/`)

| Gross irrigation (mm/yr) | 0 | 100 | 200 | 300 | 400 | 500 | 600 | 800 |
|---|---|---|---|---|---|---|---|---|
| Steady cover V | 0.004 | 0.03 | 0.11 | 0.17 | 0.22 | 0.26 | 0.29 | 0.35 |
| Sand transport vs bare | 0.98 | 0.95 | 0.88 | 0.80 | 0.70 | 0.55 | 0.36 | 0.10 |
| Transpiration (mm/yr) | 3 | 37 | 128 | 219 | 302 | 370 | 436 | 564 |
| Soil evaporation (mm/yr) | 21 | 75 | 74 | 72 | 71 | 71 | 70 | 68 |
| Deep percolation (mm/yr) | 0 | 0 | 0 | 0 | 9 | 32 | 56 | 109 |

- Holding the critical cover v_c = 0.30 needs about **624 mm/yr = 6,240 m³/ha/yr**; over the whole 15,000 ha that is 94 million m³/yr. For comparison the Tarim Desert Highway belt is run at roughly 270–670 mm/yr depending on which published event depth is used (15 mm from 30 L per plant on 2 m², or 35 mm per event).
- Water not limiting: full stands (V ≥ 0.5) use about 1,350 mm/yr.
- Below about 50 mm/yr nothing survives; the first 70 mm of any quota is lost to soil evaporation.
- From planting (V₀ = 0.05) at 600 mm/yr, v_c is reached in 13 years; at ≤ 400 mm/yr never.
- If irrigation stops, half the cover is lost in 2 years. Halving DP with barriers does not change this: the loss is from drought, not sand.
- New and established stands converge to the same cover: one stable state, no hysteresis in this version.
- Wet-surface suppression of sand transport is 2.2 % of DP: real, but negligible at 30 mm/yr of rain.
- Water balance closes: residual 1e-12 mm over 24 years.

### Sensitivity (one at a time; `sensitivity_oat.csv`, `fig5_sensitivity.png`)

Minimum irrigation to hold V ≥ 0.30, baseline 624 mm/yr:

| Parameter | Low → High | W_min (mm/yr) |
|---|---|---|
| m_w 0.3 → 3 /yr | | 364 → not reachable ≤ 800 |
| K_cb,full 0.7 → 1.2 | | 425 → 756 |
| r ±30 % | | 738 → 540 |
| V_max ∓0.1 | | 727 → 567 |
| ET0 ∓10 % | | 557 → 693 |
| DP ×0.5 → ×4 | | 601 → 734 |
| η 0.8 → 0.95 | | 704 → 589 |
| Z_r 0.6 → 2.0 m | | 663 → 560 |
| f_w 0.2 → 0.5 | | 600 → 668 |
| +2 °C on growth/transpiration timing | | 624 → 644 |
| p, θ_fc − θ_wp, v_c, T_base, rain ×0.5–×2 | | within ±6 % |

The water constraint handed to Task 2 should therefore be a range, about **400–750 mm/yr**, not the single value 624. Two parameters, m_w and K_cb,full, account for most of it and neither can be fixed from the data we have.

---

## 6. Limits

1. Converted pixels are of unknown land use; some are probably orchards or fields. V_max = 0.55 and r describe "irrigated fringe land", not specifically shrub belts.
2. No measurement of belt cover against applied water exists in the repo, so the water–cover curve is model-derived and unvalidated. The one external check is the order of magnitude against Tarim Desert Highway practice.
3. Interannual variability of natural cover is not explained.
4. DP is relative (vector units). Converting to kg/m/s or burial depth needs a local coefficient.
5. ERA5 hourly mean wind misses sub-hourly peaks; true DP is likely higher than 50 VU. The ×4 case is in the sensitivity table.
6. Salinity of irrigation water (2.8–30 g/L on the highway belt) is not modelled.
7. v_c = 0.3 comes from a Negev-calibrated model.

## 7. Interfaces for Tasks 2 and 3

- `simulate(p, forcing, v0, irrigation=..., planting=...)`: yearly quota w_t through `irrigation_schedule(dates, {year: mm})`; newly treated area as cohorts with their own start year; `Params.shelter` for engineering barriers.
- `water_cover_curve.csv`: the water constraint as a curve.
- Forcing scaling (`load_forcing(scale={"P":…, "ET0":…, "DP":…, "dT":…})`) for climate baselines; daily DP series for storm sampling.

## 8. Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install numpy scipy pandas matplotlib requests
```
```bash
.venv/bin/python Code/m1_fetch_data.py
```
```bash
.venv/bin/python Code/m1_build_dataset.py
```
```bash
.venv/bin/python Code/m1_run.py
```

The first script is skipped file by file when raw data are present (they are committed), so the last two run offline in about one minute.

## References used

- Allen et al. 1998, FAO Irrigation and Drainage Paper 56 (`Reference/01_水盐与灌溉/11_FAO56…pdf`): Table 19 p. 170; Eq. 71–77, 84, 98.
- Zhang et al. 2016, PLoS ONE 11:e0164106 (`01_水盐灌溉.pdf`): belt geometry, 30 L per plant, cycles, wind hours.
- Liu et al. 2022, Water 14:1908 (`03_2022_…pdf`): 35 mm events, root distribution, groundwater depth.
- Yizhaq & Ashkenazy 2021, arXiv:2105.13687 (`08_生物结皮.pdf`): vegetation–sand equations and parameters.
- Fécan et al. 1999, Ann. Geophys. 17:149–157 (EN02): Eq. 14–15.
- Fryberger 1979 (drift potential) and Gutman & Ignatov 1998 (linear NDVI mixing) are cited from memory and are **not in the repo**: add them to the bibliography after checking the originals.
