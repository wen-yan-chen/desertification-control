"""Model 1: coupled vegetation - water - sand dynamics of one land cell of the belt.

State variables (per unit ground area, daily step)
    V   vegetation cover fraction                          [-], 0..V_max
    Dr  root-zone depletion below field capacity           [mm], 0..TAW
        -> effective soil moisture  M = 1 - Dr/TAW          [-], 0..1   (the Task-1 state)
    De_i, De_p  depletion of the 0.10 m evaporative layer  [mm], 0..TEW
        (drip-wetted / rain-only exposed soil; auxiliary fast states)

Equations
    water   dDr/dt = E + T + ... - P - I_net - G            (FAO-56 dual crop coefficient)
            T = Ks(M) * Kcb_full * min(1, 2V) * phi(Ta) * ET0        [FAO-56 Eq. 98, 84]
            E = sum_x Kr(De_x) * few_x * Kc_max * ET0, capped        [FAO-56 Eq. 71-77]
    veg     dV/dt = r*phi*Ks*V*(1 - V/V_max)
                    - [ m0 + m_w*phi*(1-Ks) + eps*g(V) + gam*DPbar^(2/3) ] * V + planting
    sand    DP  = < U^2 (U - U_t)_+ >  (U in knots at 10 m; Fryberger drift potential, VU)
            g   = 0.5*DP_eff*(tanh(d*(v_c - V)) + 1)*(1 - V)         [Yizhaq & Ashkenazy 2021, Eq. 4]
            DP_eff uses a threshold raised by surface wetness        [Fecan et al. 1999, Eq. 14-15]

Couplings (all six directions of the triangle are explicit)
    water -> veg   Ks limits growth and drives drought mortality
    veg -> water   transpiration grows with V; canopy shades soil evaporation (few = 1 - V)
    veg -> sand    g(V): sand transport is switched off above the critical cover v_c
    sand -> veg    eps*g*V (abrasion / erosion / burial) and gam*DP^(2/3)*V (wind drag)
    water -> sand  wet surface raises the threshold wind speed (only after rain here)
    sand -> water  not modelled (sand-mulch effect on evaporation is ignored; assumption A9)

What is NOT claimed: the sand part gives a *relative* transport potential (vector
units).  Converting DP to kg m-1 s-1 or to burial depth needs a locally measured
coefficient that we do not have (see Docs, open items).
"""
from dataclasses import dataclass, asdict, replace

import numpy as np

YEAR = 365.25


@dataclass(frozen=True)
class Params:
    # ---- soil water (FAO-56 Table 19, soil type "Sand"; PDF p.170) -----------------
    theta_fc: float = 0.12      # field capacity, m3/m3      (range 0.07-0.17; mid value)
    theta_wp: float = 0.045     # wilting point, m3/m3       (range 0.02-0.07; mid value)
    z_root: float = 1.0         # effective root depth, m    (assumption A3; Haloxylon roots mainly
    #                             0.2-0.8 m, Liu et al. 2022 Water 14:1908 p.2; sensitivity 0.6-2.0)
    z_evap: float = 0.10        # evaporative layer depth, m (FAO-56 recommends 0.10-0.15)
    rew: float = 4.5            # readily evaporable water, mm (Table 19 sand: 2-7)
    p_stress: float = 0.6       # depletion fraction before stress (assumption A4; FAO-56 Table 22
    #                             gives 0.3-0.7 for crops; drought-tolerant shrubs -> upper part)
    # ---- crop-coefficient side (FAO-56 ch.7 and ch.9) ---------------------------------
    kcb_full: float = 1.0       # basal coefficient at full cover (Eq. 99-101 give ~1.15 for 2 m
    #                             vegetation; reduced for stomatal control, Eq. 102; sens. 0.7-1.2)
    kc_max: float = 1.2         # upper limit of evaporation + transpiration (Eq. 72)
    f_wet: float = 0.3          # soil fraction wetted by drip irrigation (Table 20: 0.3-0.4)
    eta_irr: float = 0.9        # share of gross irrigation reaching the root zone (assumption A5)
    g_cap: float = 0.0          # capillary rise / groundwater subsidy, mm/day (0 for treated sand:
    #                             water table > 10 m, Liu et al. 2022 p.11; calibrated for ecotone)
    # ---- vegetation ----------------------------------------------------------------------
    r: float = 0.004            # max growth rate of cover, 1/day  (CALIBRATED, see m1_run.py)
    v_max: float = 0.80         # max attainable cover             (CALIBRATED / data upper envelope)
    m0: float = 0.02 / YEAR     # background mortality, 1/day (Yizhaq & Ashkenazy 2021: 0.02 /yr)
    m_w: float = 1.0 / YEAR     # extra mortality under full water stress, 1/day (assumption A6:
    #                             cover e-folds in ~1 growing year without water; sens. 0.3-3 /yr)
    t_base: float = 10.0        # deg C: no growth / transpiration below (assumption A7)
    t_opt: float = 25.0         # deg C: full activity above        (assumption A7)
    # ---- sand (Yizhaq & Ashkenazy 2021, parameter list under their Fig. 1) -----------------
    eps: float = 0.001 / YEAR   # sand-transport damage, 1/(day VU)
    gam: float = 8e-4 / YEAR    # direct wind-drag damage, 1/(day VU^(2/3))
    v_c: float = 0.30           # critical cover above which sand transport stops
    d_c: float = 15.0           # steepness of the switch
    shelter: float = 1.0        # multiplier on DP from engineering barriers (1 = none; Task 2 hook)
    # ---- surface wetness -> threshold (Fecan et al. 1999 Eq. 14-15) ------------------------
    clay_pct: float = 1.0       # clay content of dune sand, % (assumption A8)
    rho_b: float = 1.6          # dry bulk density, g/cm3     (assumption A8)

    @property
    def taw(self):              # total available water in the root zone, mm (FAO-56 Eq. 82)
        return 1000.0 * self.z_root * (self.theta_fc - self.theta_wp)

    @property
    def tew(self):              # total evaporable water of the surface layer, mm (FAO-56 Eq. 73)
        return 1000.0 * self.z_evap * (self.theta_fc - 0.5 * self.theta_wp)

    def with_(self, **kw):
        return replace(self, **kw)

    def as_dict(self):
        return dict(asdict(self), taw_mm=self.taw, tew_mm=self.tew)


# ------------------------------------------------------------------------------------ pieces
def phi_temp(t_smooth, p):
    """Thermal activity 0..1 (growth and transpiration) from 15-day mean air temperature."""
    return np.clip((t_smooth - p.t_base) / (p.t_opt - p.t_base), 0.0, 1.0)


def ks_stress(dr, p):
    """FAO-56 Eq. 84 water-stress coefficient: 1 until p*TAW is depleted, then linear to 0."""
    return min(1.0, max(0.0, (p.taw - dr) / ((1.0 - p.p_stress) * p.taw)))


def sand_switch(v, p):
    """Relative sand-transport capacity of the surface, 1 (bare) -> 0 (v >> v_c)."""
    return 0.5 * (np.tanh(p.d_c * (p.v_c - v)) + 1.0) * (1.0 - v)


def fecan_factor(theta_surf, p):
    """Ratio wet/dry threshold wind speed.  theta_surf: volumetric water of the top layer
    above the air-dry state (m3/m3).  w and w' are GRAVIMETRIC PERCENT (5 means 5 %)."""
    w = 100.0 * theta_surf / p.rho_b                       # rho_water = 1 g/cm3
    w_res = 0.0014 * p.clay_pct ** 2 + 0.17 * p.clay_pct
    return 1.0 if w <= w_res else float(np.sqrt(1.0 + 1.21 * (w - w_res) ** 0.68))


def irrigation_schedule(dates, annual_mm, months=(3, 10), interval=15, summer_interval=10):
    """Gross irrigation depth per day (mm over the treated area) for a yearly quota.

    Timing follows the Tarim Desert Highway shelterbelt practice: every 15 days from
    March to October, every 10 days in July-August, none in winter (Zhang et al. 2016
    PLoS ONE 11:e0164106 p.5; Liu et al. 2022 Water 14:1908 p.3).  The yearly quota is
    split equally over the events of that year.  annual_mm may be a scalar or a
    {year: mm} mapping (Task 2 control variable w_t).
    """
    dates = np.asarray(dates, dtype="datetime64[D]")
    years = dates.astype("datetime64[Y]").astype(int) + 1970
    months_ = dates.astype("datetime64[M]").astype(int) % 12 + 1
    doy = (dates - dates.astype("datetime64[Y]")).astype(int)
    out = np.zeros(len(dates))
    for y in np.unique(years):
        quota = annual_mm.get(int(y), 0.0) if isinstance(annual_mm, dict) else float(annual_mm)
        if quota <= 0:
            continue
        idx, last = [], -10 ** 6
        for i in np.where(years == y)[0]:
            if not (months[0] <= months_[i] <= months[1]):
                continue
            gap = summer_interval if months_[i] in (7, 8) else interval
            if doy[i] - last >= gap:
                idx.append(i)
                last = doy[i]
        out[idx] = quota / len(idx)
    return out


# ------------------------------------------------------------------------------------ simulator
def simulate(p, forcing, v0, irrigation=None, demand_irrigation=False, planting=None,
             m_init=0.5, record=True):
    """Integrate the coupled model with a daily step.

    forcing : dict of equal-length daily arrays
        P [mm], ET0 [mm], Tsm [deg C, 15-day mean], DP [VU, daily drift potential at the
        dry threshold], DPbar [VU, trailing 365-day mean], dp_tab [n x k] and dp_mult [k]
        (daily DP recomputed for threshold multipliers, used for the wet-surface effect).
    irrigation : daily gross irrigation depth [mm] or None.
    demand_irrigation : if True, irrigate (Mar-Oct) whenever Dr exceeds p_stress*TAW,
        refilling to field capacity -> "water not limiting" reference; the applied
        amounts are returned so the water requirement can be read off.
    planting : daily cover added by planting [-] or None (Task 2 hook).
    Returns dict of daily arrays and a water-balance ledger whose residual must be ~0.
    """
    n = len(forcing["P"])
    P, ET0, Tsm = forcing["P"], forcing["ET0"], forcing["Tsm"]
    DP, DPbar = forcing["DP"] * p.shelter, forcing["DPbar"] * p.shelter
    dp_tab, dp_mult = forcing.get("dp_tab"), forcing.get("dp_mult")
    month = forcing["month"]
    phi = phi_temp(Tsm, p)
    taw, tew, rew = p.taw, p.tew, p.rew
    irrigated_cell = demand_irrigation or (irrigation is not None and np.any(irrigation > 0))

    v = float(v0)
    dr = (1.0 - m_init) * taw
    de_i = de_p = tew                                        # start with a dry surface
    out = {k: np.zeros(n) for k in ("V", "M", "E", "T", "I", "perc", "Ks", "DPeff", "sand", "below_wp")} \
        if record else None
    s0 = taw - dr
    for t in range(n):
        if planting is not None and planting[t] > 0:
            v = min(p.v_max, v + planting[t])
        # ---- wetting (start of day) ------------------------------------------------------
        gross = irrigation[t] if irrigation is not None else 0.0
        if demand_irrigation and 3 <= month[t] <= 10 and dr > p.p_stress * taw:
            gross = dr / p.eta_irr                           # refill to field capacity
        i_net = p.eta_irr * gross                            # the rest is conveyance/drift loss
        rain = P[t]
        de_p = max(de_p - rain, 0.0)
        de_i = max(de_i - rain - i_net / p.f_wet, 0.0)
        dr -= rain + i_net + p.g_cap
        # ---- transpiration ---------------------------------------------------------------
        ks = ks_stress(max(dr, 0.0), p)
        kcb = p.kcb_full * min(1.0, 2.0 * v) * phi[t]        # FAO-56 Eq. 98 without Kc_min
        tr = ks * kcb * ET0[t]
        # ---- soil evaporation from exposed fractions ---------------------------------------
        few_i = min(1.0 - v, p.f_wet) if irrigated_cell else 0.0
        few_p = max(1.0 - v - few_i, 0.0)
        kr_i = 1.0 if de_i <= rew else max((tew - de_i) / (tew - rew), 0.0)
        kr_p = 1.0 if de_p <= rew else max((tew - de_p) / (tew - rew), 0.0)
        ke_i, ke_p = kr_i * few_i * p.kc_max, kr_p * few_p * p.kc_max
        cap = max(p.kc_max - kcb, 0.0)                       # energy limit, FAO-56 Eq. 71
        if ke_i + ke_p > cap and ke_i + ke_p > 0:
            scale = cap / (ke_i + ke_p)
            ke_i, ke_p = ke_i * scale, ke_p * scale
        e_i = min(ke_i * ET0[t], (tew - de_i) * few_i)       # cannot evaporate more than is there
        e_p = min(ke_p * ET0[t], (tew - de_p) * few_p)
        if few_i > 0:
            de_i = min(de_i + e_i / few_i, tew)
        if few_p > 0:
            de_p = min(de_p + e_p / few_p, tew)
        ev = e_i + e_p
        # ---- root-zone bookkeeping (mass conserving; every correction is logged) -----------
        dr += tr + ev
        perc = below = 0.0
        if dr < 0.0:                                         # above field capacity -> drains
            perc, dr = -dr, 0.0
        elif dr > taw:                                       # surface layer dried below wilting
            below, dr = dr - taw, taw                        # point: water outside TAW (logged)
        # ---- sand ---------------------------------------------------------------------------
        if dp_tab is not None and de_p < tew:                # surface still moist after rain
            fac = fecan_factor((tew - de_p) / (1000.0 * p.z_evap), p)
            dpe = float(np.interp(fac, dp_mult, dp_tab[t])) * p.shelter
        else:
            dpe = DP[t]
        g = dpe * sand_switch(v, p)
        # ---- vegetation ----------------------------------------------------------------------
        growth = p.r * phi[t] * ks * v * (1.0 - v / p.v_max)
        loss = (p.m0 + p.m_w * phi[t] * (1.0 - ks) + p.eps * g + p.gam * DPbar[t] ** (2.0 / 3.0)) * v
        if record:
            out["V"][t], out["M"][t], out["E"][t], out["T"][t] = v, 1.0 - dr / taw, ev, tr
            out["I"][t], out["perc"][t], out["Ks"][t] = gross, perc, ks
            out["DPeff"][t], out["sand"][t], out["below_wp"][t] = dpe, g, below
        v = min(max(v + growth - loss, 0.0), p.v_max)
    if not record:
        return v
    # water-balance ledger over the whole run, mm
    net_in = float(np.sum(P) + p.eta_irr * np.sum(out["I"]) + p.g_cap * n)
    net_out = float(np.sum(out["E"]) + np.sum(out["T"]) + np.sum(out["perc"]))
    ds = (taw - dr) - s0
    out["ledger"] = dict(rain=float(np.sum(P)), irrigation_gross=float(np.sum(out["I"])),
                         irrigation_net=float(p.eta_irr * np.sum(out["I"])), capillary=float(p.g_cap * n),
                         evaporation=float(np.sum(out["E"])), transpiration=float(np.sum(out["T"])),
                         percolation=float(np.sum(out["perc"])), below_wp_surface=float(np.sum(out["below_wp"])),
                         storage_change=float(ds),
                         residual=float(net_in - net_out + np.sum(out["below_wp"]) - ds))
    out["V_end"] = v
    return out


def annual_means(out, forcing, key, months=(7, 8)):
    """Mean of a daily output over the given months of each year -> (years, values)."""
    sel = (forcing["month"] >= months[0]) & (forcing["month"] <= months[1])
    years = np.unique(forcing["year"])
    return years, np.array([out[key][sel & (forcing["year"] == y)].mean() for y in years])


def annual_sums(out, forcing, key):
    years = np.unique(forcing["year"])
    return years, np.array([out[key][forcing["year"] == y].sum() for y in years])
