"""Run M2 and export auditable numerical tables for the team's figure author."""
import argparse
import copy
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from v7_m2_core import ROOT, load_inputs, build_problem, solve, replay, simulate_policy, meets_min_cover


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def run(output, suite=True):
    output.mkdir(parents=True, exist_ok=True)
    cfg, m1, forcing = load_inputs()
    p = build_problem(cfg, m1, forcing)
    xmax, maxmeta = solve(p, "ecology")
    if xmax is None:
        raise RuntimeError(f"No ecological reference incumbent: {maxmeta}")
    reference = maxmeta["ecological_ha_year"]
    target = cfg["ecological_target_fraction"]*reference
    base_x, base_meta = solve(p, "cost", target)
    if base_x is None:
        raise RuntimeError(f"No base incumbent: {base_meta}")
    tables, errors = replay(p, base_x)
    for name, frame in tables.items():
        frame.to_csv(output/f"{name}.csv", index=False, float_format="%.10g")
    print(f"BASE {base_meta}", flush=True)
    # Full policy library enables cohort-age heat maps without rerunning the model.
    library = []
    for name, quotas in p.policies.items():
        ann, _ = simulate_policy(cfg, m1, forcing, quotas)
        ok = meets_min_cover(cfg, ann)
        library.extend(dict(policy=name, meets_min_cover=ok, **row) for row in ann.to_dict("records"))
    pd.DataFrame(library).to_csv(output/"policy_library.csv", index=False, float_format="%.10g")
    # Standalone PV break-even tariff is a screening condition only. The MILP
    # still accounts for competing land, water, labor and gross-budget capacity.
    screening = []
    for start in range(cfg["years"]-1):
        ages = np.arange(cfg["years"]-start-1, dtype=float)
        discount = (1+cfg["discount_rate"])**(-(ages+2))
        discounted_energy = float(np.sum(cfg["pv_net_yield_kwh_kw_year"]*(1-cfg["pv_degradation_fraction_year"])**ages*discount))
        cost = cfg["pv_capex_cny_kw"]+float(discount.sum())*(cfg["pv_om_cny_kw_year"]+cfg["pv_cleaning_m3_kw_year"]*cfg["water_cny_m3"])
        screening.append(dict(start_year=start+1, discounted_lifetime_kwh_per_kw=discounted_energy,
            discounted_lifetime_cost_cny_per_kw=cost, break_even_price_cny_kwh=cost/discounted_energy,
            standalone_npv_cny_per_kw=cfg["pv_price_cny_kwh"]*discounted_energy-cost,
            scope="Screen only; excludes scarcity opportunity cost, tax, financing and residual value"))
    pd.DataFrame(screening).to_csv(output/"pv_screening.csv", index=False, float_format="%.10g")
    runs, annuals, decisions, monthly = [], [], [], []
    configs = {}
    def record(label, prob, x, meta, group):
        runs.append(dict(case=label, group=group, **meta))
        configs[label] = dict(scenario=prob.config, m1=prob.m1, policy_names=list(prob.policies))
        if x is not None:
            tab, _ = replay(prob,x)
            annuals.append(tab["annual"].assign(case=label, group=group))
            decisions.append(tab["decisions"].assign(case=label, group=group))
            monthly.append(tab["monthly"].assign(case=label, group=group))
        print(f"{label}: status={meta['status']} feasible={meta['feasible']} gap={meta['mip_gap']}", flush=True)
    record("base",p,base_x,base_meta,"base")
    record("maximum_ecology_reference",p,xmax,maxmeta,"reference")
    if suite:
        # Same absolute ecological target for all sensitivities: a harder scenario
        # cannot look cheaper by silently lowering its protection requirement.
        for fraction in (0., .2, .4, .6, .8, 1.):
            if fraction == .6:
                x, meta = base_x, base_meta
            else:
                x, meta = solve(p,"cost",fraction*reference)
            record(f"frontier_{fraction:.1f}",p,x,meta,"frontier")
        cases = {
            "no_pv": {"pv_capacity_cap_kw":0.},
            "pv_price_low": {"pv_price_cny_kwh":.15},
            "pv_price_high": {"pv_price_cny_kwh":.40},
            "pv_capex_low": {"pv_capex_cny_kw":2250.},
            "pv_capex_high": {"pv_capex_cny_kw":3750.},
            "pv_share_min_10pct": {"pv_capex_share_min":.1},
            "pv_share_min_30pct": {"pv_capex_share_min":.3},
            "om_low": {"eco_om_cny_ha_year":750.,"pv_om_cny_kw_year":25.},
            "om_high": {"eco_om_cny_ha_year":2250.,"pv_om_cny_kw_year":75.},
            "eco_capex_low": {"eco_capex_cny_ha":39375.},
            "eco_capex_high": {"eco_capex_cny_ha":65625.},
            "water_low": {"annual_water_cap_m3":1200000.,"monthly_water_caps_m3":[v*.8 for v in cfg["monthly_water_caps_m3"]]},
            "water_relax_10pct": {"annual_water_cap_m3":1650000.,"monthly_water_caps_m3":[v*1.1 for v in cfg["monthly_water_caps_m3"]]},
            "budget_low": {"total_budget_cny":64000000.},
            "labor_low": {"annual_labor_cap_person_days":6000.},
            "initial_cover_low": {"initial_V_pct":1.},
            "initial_cover_high": {"initial_V_pct":4.},
            "finer_area_grid": {"area_block_ha":25.},
        }
        for label, changes in cases.items():
            c = {**cfg, **changes}
            prob = build_problem(c,m1,forcing)
            x, meta = solve(prob,"cost",target)
            record(label,prob,x,meta,"sensitivity")
        for label, cap in (("storage_low",37.5),("storage_high",150.)):
            mm = copy.deepcopy(m1)
            mm["water"]["capacity_mm"] = cap
            c = {**cfg, "initial_M_mm":cap/2}
            prob = build_problem(c,mm,forcing)
            x, meta = solve(prob,"cost",target)
            record(label,prob,x,meta,"sensitivity")
        # Protection-threshold checks. The score definition itself changes with the rule, so
        # these are comparisons of rules at one numerical target, not of like-for-like plans.
        for label, changes in (("min_cover_off", {"min_cover_pct":0.}),
                               ("min_cover_15pct", {"min_cover_pct":15.}),
                               ("min_cover_25pct", {"min_cover_pct":25.}),
                               ("min_cover_by_age_12", {"min_cover_by_age_year":12})):
            prob = build_problem({**cfg, **changes},m1,forcing)
            x, meta = solve(prob,"cost",target)
            record(label,prob,x,meta,"threshold")
        constant = {k:v for k,v in p.policies.items() if k.startswith("constant_")}
        prob = build_problem(cfg,m1,forcing,constant)
        x, meta = solve(prob,"cost",target)
        record("constant_irrigation_only",prob,x,meta,"control_library")
    pd.DataFrame(runs).to_csv(output/"scenario_summary.csv", index=False, float_format="%.10g")
    pd.concat(annuals, ignore_index=True).to_csv(output/"scenario_annual.csv", index=False, float_format="%.10g")
    pd.concat(decisions, ignore_index=True).to_csv(output/"scenario_decisions.csv", index=False, float_format="%.10g")
    pd.concat(monthly, ignore_index=True).to_csv(output/"scenario_monthly.csv", index=False, float_format="%.10g")
    write_json(output/"scenario_configs.json",configs)
    inputs = ["Data/v7/m2_inputs/scenario.json", "Results/v7/model1/model1_results.json",
              "Results/v7/model1/section_forcing_climatology.csv", "Code/v7_m1_water.py",
              "Code/v7_m2_core.py", "Code/v7_model2.py"]
    provenance = {name: hashlib.sha256((ROOT/name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in inputs}
    summary = dict(status="scenario-ready; restricted finite control library", formal_model_ready=False,
        units="ha, mm, m3, kW, CNY, person-days; ecology = undiscounted effective ha-years of batches meeting the minimum-cover rule",
        input_text_sha256_lf=provenance, config=cfg, m1_parameters=m1,
        environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__),
        maximum_ecology_reference=maxmeta, base=base_meta, replay_max_abs_errors=errors,
        solution_scope="MILP incumbent and reported gap only within supplied cohort policies/area grid. Not a global continuous-control optimum.",
        ecological_reference_scope="Best feasible ecological reference; solver dual bound gives upper bound. 60% is an illustrative policy target, not a problem-given weight.",
        accounting="Start-year capital; end-year recurring costs/income. PV starts following year. No taxes, debt, recycling of revenues, terminal salvage, or post-horizon obligations modeled.",
        limitations=["No verified site budget, legal water allocation, land boundary, work norms or PV settlement contract",
                     "M1 long-term states are conditional scenarios, not validated predictions",
                     "Initial planted cover/storage and irrigation policy library are assumptions",
                     "Ecological score is managed-area cover/K, not causal additionality, measured erosion or monetized ecosystem services",
                     "Minimum-cover rule (threshold and age) is a scenario assumption without a site-verified protection threshold; batches below it score zero but still cost money and water",
                     "PV and restoration occupy disjoint land; no inferred PV vegetation benefit",
                     "Unit prices include labor; person-days constrain capacity and are not charged twice"],
        runs=runs)
    write_json(output/"model2_results.json",summary)
    print(f"WROTE {output}",flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"Results/v7/model2")
    parser.add_argument("--base-only",action="store_true")
    args = parser.parse_args()
    run(args.output,not args.base_only)
