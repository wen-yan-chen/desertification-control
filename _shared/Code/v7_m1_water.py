"""M1 water storage extension. Scenario model, not a calibrated water forecast.

Annual vegetation equation is unchanged. Available storage M (mm above wilting
point) evolves within each year. Monthly climatology is distributed uniformly
over its days; these substeps are numerical assumptions, not daily observations.
FAO-56 ch.8 supplies the storage/stress structure, not site parameter values.
"""
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class WaterParameters:
    capacity_mm: float = 75.0   # scenario; NOT inferred from incomplete SoilGrids
    depletion_fraction: float = 0.5
    c: float = 1.0
    eta_w: float = 0.75        # net transpirable share, includes irrigation losses
    rain_fraction: float = 0.25  # after interception/runoff/soil evaporation
    groundwater_mm_yr: float = 0.0
    v_full_pct: float = 66.5875 # local NDVI scaling assumption, not field validation

    def validate(self):
        if not all(math.isfinite(v) for v in self.__dict__.values()):
            raise ValueError("Nonfinite water parameter")
        if self.capacity_mm <= 0 or self.c <= 0 or self.v_full_pct <= 0:
            raise ValueError("Capacity, c and V_full must be positive")
        if not 0 <= self.depletion_fraction < 1:
            raise ValueError("depletion fraction must be in [0,1)")
        if not 0 <= self.eta_w <= 1 or not 0 <= self.rain_fraction <= 1 or self.groundwater_mm_yr < 0:
            raise ValueError("Invalid water supply coefficient")

def vegetation_step(v, K, w, r, d):
    """Annual cover step. No wind term: wind acts through the forcing (ET0 demand)."""
    values = [v, K, w, r, d]
    if not all(math.isfinite(x) for x in values) or K <= 0 or not 0 <= v <= K:
        raise ValueError("Invalid cover state")
    if not (0 <= w <= 1 and 0 <= r <= 1 and 0 <= d <= 1):
        raise ValueError("Parameters outside supported invariant annual-step domain")
    result = v + r*v*(1-v/K)*w - d*v
    if not -1e-10 <= result <= K + 1e-10:
        raise ArithmeticError("State domain violation")
    return min(K, max(0., result))

def water_year(v, m0, irrigation, forcing, params=WaterParameters(), record=True):
    params.validate()
    if not (0 <= m0 <= params.capacity_mm and irrigation >= 0 and v >= 0):
        raise ValueError("Negative water/cover or storage outside capacity")
    f = np.asarray(forcing, float)  # columns: days, P, temperature-weighted ET0
    if f.shape != (12, 3) or not np.isfinite(f).all() or (f < 0).any() or (f[:, 0] < 1).any():
        raise ValueError("Need 12 complete nonnegative forcing months")
    demand = params.c * min(1., 2*v/params.v_full_pct) * f[:, 2]
    weights = f[:, 2] / f[:, 2].sum() if f[:, 2].sum() > 0 else f[:, 0]/f[:, 0].sum()
    m, rows, total_transp, total_demand = m0, [], 0., float(demand.sum())
    for i in range(12):
        days, rain, _ = f[i]
        days = int(days)
        gross = irrigation * weights[i]
        effective_rain = params.rain_fraction * rain
        net_irrigation = params.eta_w * gross
        groundwater = params.groundwater_mm_yr * days / f[:, 0].sum()
        inflow = effective_rain + net_irrigation + groundwater
        start, transp, drain = m, 0., 0.
        for _ in range(days):
            available = m + inflow/days
            excess = max(available-params.capacity_mm, 0.)
            available -= excess
            ks = min(1., available / ((1-params.depletion_fraction)*params.capacity_mm))
            uptake = min(available, ks*demand[i]/days)
            m = available-uptake
            transp += uptake
            drain += excess
        residual = start + inflow - transp - drain - m
        if abs(residual) > 1e-8 or m < -1e-10 or m > params.capacity_mm+1e-10:
            raise ArithmeticError("Water mass balance violated")
        total_transp += transp
        if record:
            rows.append(dict(month=i+1, M_start_mm=start, M_end_mm=m,
                effective_moisture_fraction=m/params.capacity_mm,
                gross_irrigation_mm=gross, effective_rain_mm=effective_rain,
                net_irrigation_mm=net_irrigation, groundwater_mm=groundwater,
                potential_transpiration_mm=float(demand[i]), transpiration_mm=transp,
                drainage_mm=drain, balance_residual_mm=residual))
    w = total_transp / total_demand if total_demand > 0 else 0.
    return m, min(1., max(0., w)), rows

def trajectory(v0, m0, years, K, r, d, forcing, irrigation, params=WaterParameters(), record=True):
    if years < 1:
        raise ValueError("years must be positive")
    quotas = np.broadcast_to(np.asarray(irrigation, float), (years,))
    v, m, annual, monthly = float(v0), float(m0), [], []
    for t, quota in enumerate(quotas):
        mend, w, rows = water_year(v, m, float(quota), forcing, params, record)
        vnext = vegetation_step(v, K, w, r, d)
        annual.append(dict(year=t+1, V_start_pct=v, V_end_pct=vnext, M_start_mm=m,
            M_end_mm=mend, W=w, irrigation_mm_yr=float(quota), irrigation_m3_ha_yr=10*float(quota),
            # Output: sand exposure at average wind (E = 1), the unsheltered share 1 - V/K.
            relative_erosion_scenario=max(0., 1-v/K)))
        monthly.extend(dict(year=t+1, V_pct=v, **row) for row in rows)
        v, m = vnext, mend
    return pd.DataFrame(annual), pd.DataFrame(monthly)

def equilibrium(v0, m0, K, r, d, forcing, irrigation, params=WaterParameters(), max_years=500, tol=1e-7):
    v, m = float(v0), float(m0)
    for year in range(1, max_years+1):
        mend, w, _ = water_year(v, m, irrigation, forcing, params, False)
        vend = vegetation_step(v, K, w, r, d)
        error = max(abs(vend-v), abs(mend-m))
        v, m = vend, mend
        if error < tol:
            return dict(V_pct=v, M_mm=m, W=w, iterations=year, residual=error, converged=True)
    return dict(V_pct=v, M_mm=m, W=w, iterations=max_years, residual=error, converged=False)
