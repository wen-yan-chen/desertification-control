"""Isolate state-grid and shock-quadrature errors without rerunning simulations."""
import hashlib
import json
import numpy as np
import pandas as pd
from v7_m3_core import ROOT,load_inputs,stationary_chain


def run():
    out=ROOT/'Results/v7/model3'
    saved=json.loads((out/'model3_results.json').read_text(encoding='utf-8'))
    for name,want in saved['input_text_sha256_lf'].items():
        if hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=want:
            raise ValueError(f'Stale M3 input: {name}')
    c,m,m2,coh,f,_=load_inputs()
    c.update(wind_log_trend_per_year=0.,rain_log_trend_per_year=0.,storm_rate_log_trend_per_year=0.,drought_probability_increment=0.)
    curves=pd.read_csv(out/'markov_survival.csv');checks=[];cross=[]
    for j,row in coh.iterrows():
        # Same shock quadrature as fine grid, state grid as medium run.
        x,diag=stationary_chain(c,m,m2,coh,f,j,161,21,96)
        cross.append(x.assign(cohort_id=row.cohort_id,nv=161,nm=21,shock_nodes=96))
        medium=curves[(curves.cohort_id==row.cohort_id)&(curves.nv==161)].sort_values('post_year')
        fine=curves[(curves.cohort_id==row.cohort_id)&(curves.nv==321)].sort_values('post_year')
        for kind,other in [('state_grid',fine),('shock_quadrature',medium)]:
            error=np.abs(x.failure_probability.to_numpy()-other.failure_probability.to_numpy())
            checks.append(dict(cohort_id=row.cohort_id,comparison=kind,max_absolute_probability_difference=float(error.max()),
                p50_absolute_difference=float(error[-1]),below_one_percentage_point=bool(error.max()<.01)))
    pd.concat(cross,ignore_index=True).to_csv(out/'markov_cross_grid.csv',index=False,float_format='%.10g')
    pd.DataFrame(checks).to_csv(out/'grid_validation.csv',index=False,float_format='%.10g')
    mc=pd.read_csv(out/'markov_mc_comparison.csv');fine=mc[mc.nv==321]
    resources=pd.read_csv(out/'resources.csv');proj=pd.read_csv(out/'project_annual.csv');ca=pd.read_csv(out/'cohort_annual.csv')
    if resources.slack_m3.min()<-1e-6:raise ArithmeticError('Exported water limit violated')
    if (proj.groupby('case').project_failure_probability.diff().dropna()<-1e-9).any():raise ArithmeticError('Nonmonotone project first passage')
    if (ca.groupby(['case','cohort_id']).failure_probability.diff().dropna()<-1e-9).any():raise ArithmeticError('Nonmonotone cohort first passage')
    summary=dict(state_and_quadrature_checks=checks,finest_markov_vs_mc_points=int(len(fine)),
        finest_points_inside_mc_ci95=int(fine.inside_mc_ci95.sum()),max_markov_mc_absolute_difference=float(fine.absolute_difference.max()),
        min_exported_monthly_water_slack_m3=float(resources.slack_m3.min()),first_passage_monotone=True,
        note='Numerical agreement is not empirical validation. A 95% MC interval need not contain every approximation in repeated comparisons.',
        checker_sha256_lf=hashlib.sha256((ROOT/'Code/v7_m3_grid_check.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest())
    (out/'validation_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':run()
