"""Finite M1 cohort-policy library + MILP. No plotting; no field-optimality claim.

Physical units: ha, mm, m3, kW, person-days, CNY. Solver cost rows use million
CNY and water rows million m3 only for conditioning. Spending is gross: PV
income does NOT replenish the hard total budget. Capital paid at year start;
operations/income at year end. PV commissioned at end of its construction year.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix
from v7_m1_water import WaterParameters, trajectory

ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    cfg = json.loads((ROOT / "Data/v7/m2_inputs/scenario.json").read_text(encoding="utf-8"))
    m1 = json.loads((ROOT / "Results/v7/model1/model1_results.json").read_text(encoding="utf-8"))
    f = pd.read_csv(ROOT / "Results/v7/model1/section_forcing_climatology.csv")
    if list(f.month) != list(range(1, 13)):
        raise ValueError("M1 forcing must contain ordered months 1..12")
    return cfg, m1["adopted_parameters"], f[["days", "P_mm", "ET0g_mm"]].to_numpy()


def validate_config(c, m):
    for key, value in c.items():
        if isinstance(value, (float, int)) and (not np.isfinite(value) or value < 0):
            raise ValueError(f"Nonnegative finite parameter required: {key}")
    if not isinstance(c["years"], int) or not 1 <= c["years"] <= 20:
        raise ValueError("Supported horizon: integer 1..20 (base case 15)")
    for key in ("area_block_ha", "pv_block_kw", "solver_time_limit_s"):
        if c[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if not 0 <= c["initial_V_pct"] <= m["K_section_pct"]:
        raise ValueError("Initial cover outside M1 domain")
    if not 0 <= c["initial_M_mm"] <= m["water"]["capacity_mm"]:
        raise ValueError("Initial storage outside M1 domain")
    if not 0 <= c["ecological_target_fraction"] <= 1 or not 0 <= c["pv_degradation_fraction_year"] < 1:
        raise ValueError("Invalid fraction")
    if not 0 <= c["pv_capex_share_min"] <= c["pv_capex_share_max"] <= 1:
        raise ValueError("Invalid PV investment-share limits")
    if not 0 <= c.get("min_cover_pct", 0.) <= m["K_section_pct"]:
        raise ValueError("Minimum cover threshold outside M1 domain")
    age = c.get("min_cover_by_age_year", 1)
    if not isinstance(age, int) or age < 1:
        raise ValueError("min_cover_by_age_year must be a positive integer")
    caps = np.asarray(c["monthly_water_caps_m3"], float)
    if caps.shape != (12,) or not np.isfinite(caps).all() or (caps < 0).any():
        raise ValueError("Need 12 nonnegative monthly water caps")
    WaterParameters(**m["water"]).validate()


def policy_library(T):
    """Fixed quotas and both rising/falling irrigation schedules, all assumptions."""
    policies = {f"constant_{q}": np.full(T, q, float) for q in (0, 100, 300, 600, 1000)}
    for first, later in ((100, 300), (100, 600), (300, 600), (600, 300), (1000, 600), (300, 100)):
        for switch in (3, 5):
            policies[f"{first}_to_{later}_after_{switch}"] = np.where(np.arange(T) < switch, first, later).astype(float)
    policies["ramp_100_300_600"] = np.select([np.arange(T) < 3, np.arange(T) < 7], [100, 300], 600).astype(float)
    # Small horizons can make different policy names identical; remove duplicates.
    unique = {}
    seen = set()
    for name, quotas in policies.items():
        if tuple(quotas) not in seen:
            unique[name] = quotas
            seen.add(tuple(quotas))
    return unique


def meets_min_cover(c, ann):
    """Protection rule: a batch scores only if its policy brings the cover proxy to
    min_cover_pct by the end of age min_cover_by_age_year. It is a property of the
    irrigation path, judged on the full-horizon M1 trajectory `ann`, so a late batch
    on a qualifying path still scores for the years it has. If the horizon is shorter
    than that age, the last simulated year is used. Threshold 0 switches the rule off."""
    threshold = c.get("min_cover_pct", 0.)
    if threshold <= 0:
        return True
    age = min(c.get("min_cover_by_age_year", 1), len(ann))
    return bool(ann.iloc[age-1].V_end_pct >= threshold-1e-9)


def simulate_policy(c, m, forcing, quotas):
    return trajectory(c["initial_V_pct"], c["initial_M_mm"], len(quotas),
        m["K_section_pct"], m["r"], m["d"], forcing, quotas,
        WaterParameters(**m["water"]), k=m["k"], eta=m["eta"])


@dataclass
class Problem:
    config: dict
    m1: dict
    forcing: np.ndarray
    policies: dict
    columns: list
    arrays: dict
    eco: np.ndarray
    net_cost: np.ndarray
    A: np.ndarray
    upper: np.ndarray
    row_names: list
    variable_upper: np.ndarray


def build_problem(c, m, forcing, policies=None):
    validate_config(c, m)
    T, block, pvblock = c["years"], c["area_block_ha"], c["pv_block_kw"]
    policies = policy_library(T) if policies is None else policies
    cache = {name: simulate_policy(c, m, forcing, q) for name, q in policies.items()}
    # Truncation makes some policies identical near horizon; avoid duplicate columns.
    columns = []
    for start in range(T):
        seen = set()
        for name, q in policies.items():
            prefix = tuple(q[:T-start])
            if prefix not in seen:
                columns.append(dict(kind="eco", start=start, policy=name))
                seen.add(prefix)
        if start < T-1:  # last-year PV has no modeled benefit and no terminal value
            columns.append(dict(kind="pv", start=start, policy="pv"))
    n = len(columns)
    keys = ["new_area_ha", "eco_area_ha", "new_pv_kw", "pv_installed_kw", "pv_operating_kw",
            "land_ha", "construction_cny", "om_cny", "pv_facilities_cny", "revenue_cny",
            "water_m3", "labor_person_days", "effective_ha", "counted_effective_ha", "energy_kwh"]
    arrays = {key: np.zeros((T, n)) for key in keys}
    arrays["monthly_water_m3"] = np.zeros((T, 12, n))
    ub = np.empty(n)
    for j, col in enumerate(columns):
        s = col["start"]
        if col["kind"] == "eco":
            ann, mon = cache[col["policy"]]
            counted = meets_min_cover(c, ann)
            ub[j] = np.floor(min(c["annual_new_area_cap_ha"], c["land_cap_ha"]) / block)
            arrays["new_area_ha"][s,j] = block
            arrays["construction_cny"][s,j] = block*c["eco_capex_cny_ha"]
            arrays["labor_person_days"][s,j] += block*c["eco_build_person_days_ha"]
            for t in range(s, T):
                age = t-s
                water = 10*block*ann.iloc[age].irrigation_mm_yr
                arrays["eco_area_ha"][t,j] = arrays["land_ha"][t,j] = block
                arrays["water_m3"][t,j] = water
                arrays["monthly_water_m3"][t,:,j] = mon.loc[mon.year == age+1, "gross_irrigation_mm"].to_numpy()*10*block
                arrays["om_cny"][t,j] = block*c["eco_om_cny_ha_year"] + water*c["water_cny_m3"]
                arrays["labor_person_days"][t,j] += block*c["eco_om_person_days_ha_year"]
                # Within each M1 year cover is V_start, not the newly updated V_end.
                arrays["effective_ha"][t,j] = block*ann.iloc[age].V_start_pct/m["K_section_pct"]
                # Batches on a path that never reaches the protection threshold score nothing.
                arrays["counted_effective_ha"][t,j] = arrays["effective_ha"][t,j] if counted else 0.
        else:
            ub[j] = np.floor(c["pv_capacity_cap_kw"]/pvblock)
            arrays["new_pv_kw"][s,j] = pvblock
            arrays["pv_facilities_cny"][s,j] = pvblock*c["pv_capex_cny_kw"]
            arrays["labor_person_days"][s,j] += pvblock*c["pv_build_person_days_kw"]
            arrays["pv_installed_kw"][s:,j] = pvblock
            arrays["land_ha"][s:,j] = pvblock*c["pv_land_ha_kw"]
            for t in range(s+1, T):
                age = t-s-1
                energy = pvblock*c["pv_net_yield_kwh_kw_year"]*(1-c["pv_degradation_fraction_year"])**age
                water = pvblock*c["pv_cleaning_m3_kw_year"]
                arrays["pv_operating_kw"][t,j] = pvblock
                arrays["energy_kwh"][t,j] = energy
                arrays["revenue_cny"][t,j] = energy*c["pv_price_cny_kwh"]
                arrays["water_m3"][t,j] = water
                arrays["monthly_water_m3"][t,:,j] = water/12
                arrays["om_cny"][t,j] = pvblock*c["pv_om_cny_kw_year"]+water*c["water_cny_m3"]
                arrays["labor_person_days"][t,j] += pvblock*c["pv_om_person_days_kw_year"]
    arrays["gross_spending_cny"] = arrays["construction_cny"]+arrays["om_cny"]+arrays["pv_facilities_cny"]
    start_disc = (1+c["discount_rate"])**(-np.arange(T, dtype=float))
    end_disc = start_disc/(1+c["discount_rate"])
    net = start_disc@(arrays["construction_cny"]+arrays["pv_facilities_cny"]) + end_disc@(arrays["om_cny"]-arrays["revenue_cny"])
    eco = arrays["counted_effective_ha"].sum(axis=0)  # physical ha-years, not cash/discounted
    rows, limits, names = [], [], []
    def add(name, values, cap, scale=1.):
        rows.append(values/scale); limits.append(cap/scale); names.append(name)
    add("total_budget", arrays["gross_spending_cny"].sum(axis=0), c["total_budget_cny"], 1e6)
    gross = arrays["gross_spending_cny"].sum(axis=0)
    pv_cost = arrays["pv_facilities_cny"].sum(axis=0)
    add("pv_share_max", pv_cost-c["pv_capex_share_max"]*gross, 0., 1e6)
    add("pv_share_min", c["pv_capex_share_min"]*gross-pv_cost, 0., 1e6)
    for t in range(T):
        for name, field, cap, scale in (
            ("annual_budget", "gross_spending_cny", c["annual_budget_cny"], 1e6),
            ("annual_water", "water_m3", c["annual_water_cap_m3"], 1e6),
            ("land", "land_ha", c["land_cap_ha"], 1000),
            ("new_area", "new_area_ha", c["annual_new_area_cap_ha"], 1000),
            ("labor", "labor_person_days", c["annual_labor_cap_person_days"], 10000),
            ("pv_capacity", "pv_installed_kw", c["pv_capacity_cap_kw"], 10000)):
            add(f"{name}_y{t+1}", arrays[field][t], cap, scale)
        for month in range(12):
            add(f"monthly_water_y{t+1}_m{month+1}", arrays["monthly_water_m3"][t,month], c["monthly_water_caps_m3"][month], 1e6)
    return Problem(c, m, forcing, policies, columns, arrays, eco, net, np.array(rows), np.array(limits), names, ub)


def solve(p, objective="cost", eco_target=0., fixed=None):
    if objective not in ("cost", "ecology") or not np.isfinite(eco_target) or eco_target < 0:
        raise ValueError("Invalid objective/target")
    A, upper = p.A, p.upper
    if eco_target > 0:
        A = np.vstack((A, -p.eco/1000))
        upper = np.r_[upper, -eco_target/1000]
    lower_x, upper_x = np.zeros(len(p.columns)), p.variable_upper.copy()
    for j, value in (fixed or {}).items():
        if value < 0 or value > upper_x[j] or value != int(value):
            raise ValueError("Fixed integer outside domain")
        lower_x[j] = upper_x[j] = value
    objective_vector = p.net_cost/1e6 if objective == "cost" else -p.eco/1000
    result = milp(objective_vector, integrality=np.ones(len(p.columns)),
        bounds=Bounds(lower_x, upper_x), constraints=LinearConstraint(csc_matrix(A), -np.inf, upper),
        options=dict(mip_rel_gap=p.config["solver_relative_gap"], time_limit=p.config["solver_time_limit_s"]))
    meta = dict(status=int(result.status), message=result.message, objective=objective,
        ecological_target_ha_year=eco_target, feasible=False,
        mip_gap=float(result.mip_gap) if getattr(result, "mip_gap", None) is not None else None,
        dual_bound_scaled=float(result.mip_dual_bound) if getattr(result, "mip_dual_bound", None) is not None else None)
    if result.x is None:
        return None, meta
    x = np.rint(result.x)
    if np.max(abs(result.x-x)) > 1e-4 or np.max(A@x-upper) > 1e-7:
        raise ArithmeticError("Solver incumbent fails independent integer/constraint check")
    if (x < lower_x-1e-8).any() or (x > upper_x+1e-8).any():
        raise ArithmeticError("Solver incumbent violates variable bounds")
    meta.update(feasible=True, ecological_ha_year=float(p.eco@x),
        net_present_cost_cny=float(p.net_cost@x), gross_spending_cny=float(p.arrays["gross_spending_cny"].sum(axis=0)@x),
        new_area_total_ha=float(p.arrays["new_area_ha"].sum(axis=0)@x),
        pv_installed_final_kw=float(p.arrays["pv_installed_kw"][-1]@x))
    return x, meta


def replay(p, x):
    """Recompute selected M1 cohorts and the cash/resource ledger, not just A@x."""
    c, m, T = p.config, p.m1, p.config["years"]
    annual = pd.DataFrame({"year": np.arange(1,T+1)})
    fields = [k for k in p.arrays if k != "monthly_water_m3"]
    for key in fields:
        annual[key] = 0.
    mw = np.zeros((T,12))
    cohort_rows, water_rows, decisions = [], [], []
    for j, count in enumerate(x):
        if count == 0:
            continue
        col, start = p.columns[j], p.columns[j]["start"]
        cid = f"{col['kind']}_y{start+1}_{col['policy']}"
        decisions.append(dict(cohort_id=cid, start_year=start+1, policy=col["policy"], kind=col["kind"], blocks=int(count),
            area_ha=count*c["area_block_ha"] if col["kind"]=="eco" else 0.,
            capacity_kw=count*c["pv_block_kw"] if col["kind"]=="pv" else 0.))
        if col["kind"] == "eco":
            area = count*c["area_block_ha"]
            ann, mon = simulate_policy(c, m, p.forcing, p.policies[col["policy"]][:T-start])
            # Judge the rule on the full-horizon path, exactly as build_problem does.
            counted = meets_min_cover(c, simulate_policy(c, m, p.forcing, p.policies[col["policy"]])[0])
            annual.loc[start,"new_area_ha"] += area
            annual.loc[start,"construction_cny"] += area*c["eco_capex_cny_ha"]
            annual.loc[start,"labor_person_days"] += area*c["eco_build_person_days_ha"]
            for a in ann.to_dict("records"):
                t = start+int(a["year"])-1
                water = area*a["irrigation_mm_yr"]*10
                annual.loc[t,"eco_area_ha"] += area
                annual.loc[t,"land_ha"] += area
                annual.loc[t,"water_m3"] += water
                annual.loc[t,"om_cny"] += area*c["eco_om_cny_ha_year"]+water*c["water_cny_m3"]
                annual.loc[t,"labor_person_days"] += area*c["eco_om_person_days_ha_year"]
                annual.loc[t,"effective_ha"] += area*a["V_start_pct"]/m["K_section_pct"]
                if counted:
                    annual.loc[t,"counted_effective_ha"] += area*a["V_start_pct"]/m["K_section_pct"]
                cohort_rows.append(dict(cohort_id=cid, area_ha=area, age_year=int(a["year"]),
                    counts_toward_score=counted, **{**a,"year":t+1}))
            for a in mon.to_dict("records"):
                t = start+int(a["year"])-1
                mw[t,int(a["month"])-1] += area*10*a["gross_irrigation_mm"]
                water_rows.append(dict(cohort_id=cid, area_ha=area, **{**a,"year":t+1}))
        else:
            kw = count*c["pv_block_kw"]
            annual.loc[start,"new_pv_kw"] += kw
            annual.loc[start,"pv_facilities_cny"] += kw*c["pv_capex_cny_kw"]
            annual.loc[start,"labor_person_days"] += kw*c["pv_build_person_days_kw"]
            annual.loc[start:,"pv_installed_kw"] += kw
            annual.loc[start:,"land_ha"] += kw*c["pv_land_ha_kw"]
            for t in range(start+1,T):
                energy = kw*c["pv_net_yield_kwh_kw_year"]*(1-c["pv_degradation_fraction_year"])**(t-start-1)
                water = kw*c["pv_cleaning_m3_kw_year"]
                annual.loc[t,"pv_operating_kw"] += kw
                annual.loc[t,"energy_kwh"] += energy
                annual.loc[t,"revenue_cny"] += energy*c["pv_price_cny_kwh"]
                annual.loc[t,"om_cny"] += kw*c["pv_om_cny_kw_year"]+water*c["water_cny_m3"]
                annual.loc[t,"water_m3"] += water
                annual.loc[t,"labor_person_days"] += kw*c["pv_om_person_days_kw_year"]
                mw[t,:] += water/12
    annual["gross_spending_cny"] = annual.construction_cny+annual.om_cny+annual.pv_facilities_cny
    errors = {k:float(np.max(abs(annual[k].to_numpy()-p.arrays[k]@x))) for k in fields}
    errors["monthly_water_m3"] = float(np.max(abs(mw-p.arrays["monthly_water_m3"]@x)))
    if max(errors.values()) > 1e-6:
        raise ArithmeticError(f"Forward ledger disagrees with optimization: {errors}")
    if np.max(p.A@x-p.upper) > 1e-7:
        raise ArithmeticError("Replay violates resource cap")
    for category in ("construction", "om", "pv_facilities"):
        annual[category+"_fund_share"] = annual[category+"_cny"].div(annual.gross_spending_cny.replace(0,np.nan))
    annual["unspent_total_budget_cny"] = c["total_budget_cny"]-annual.gross_spending_cny.cumsum()
    annual["annual_budget_slack_cny"] = c["annual_budget_cny"]-annual.gross_spending_cny
    annual["annual_water_slack_m3"] = c["annual_water_cap_m3"]-annual.water_m3
    annual["labor_slack_person_days"] = c["annual_labor_cap_person_days"]-annual.labor_person_days
    annual["land_slack_ha"] = c["land_cap_ha"]-annual.land_ha
    annual["net_cash_flow_cny"] = annual.revenue_cny-annual.gross_spending_cny
    start_disc = (1+c["discount_rate"])**(-np.arange(T,dtype=float))
    annual["discounted_net_cost_cny"] = (annual.construction_cny+annual.pv_facilities_cny)*start_disc+(annual.om_cny-annual.revenue_cny)*start_disc/(1+c["discount_rate"])
    monthly = pd.DataFrame([dict(year=t+1, month=k+1, gross_water_m3=mw[t,k],
        cap_m3=c["monthly_water_caps_m3"][k], slack_m3=c["monthly_water_caps_m3"][k]-mw[t,k]) for t in range(T) for k in range(12)])
    return dict(annual=annual, monthly=monthly, decisions=pd.DataFrame(decisions),
        cohorts=pd.DataFrame(cohort_rows), cohort_water=pd.DataFrame(water_rows)), errors
