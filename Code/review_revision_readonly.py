"""Read-only review of teammate revision; writes JSON/CSV only under Results/review_b686eab.
Loads selected mathematical functions via AST; never runs plotting/main routines.
Reviewed copy of a pre-existing local review draft; that draft is left untouched.
"""
from pathlib import Path
import ast, hashlib, json, subprocess, sys, os
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Results/review_b686eab'

def main():
    inputs=['Code/modeling_v2.py','Data/processed/panel_v2.csv','Results/model_fit_by_station.csv',
            'Results/model_v2.json','Data/raw/modis_ndvi_qa_sample.csv',
            'Data/raw/nasa_power_verified/power_monthly.csv','Data/raw/nasa_power_verified/manifest_v2.json']
    if subprocess.run(['git','diff','--quiet','b686eab','--',*inputs],cwd=ROOT).returncode:
        raise SystemExit('Reviewed inputs differ from b686eab; update the review before reusing it.')
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    protected = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked if p and not p.startswith(('Results/review_b686eab/', 'Docs/20261109_第二轮复核', 'Code/review_revision_b686eab.py'))}
    source = ROOT/'Code/modeling_v2.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    constants = {'ZR','TH_FC','TH_WP','AWC','SCEN'}
    nodes = [n for n in tree.body if isinstance(n,ast.FunctionDef) or
             (isinstance(n,ast.Assign) and all(isinstance(t,(ast.Name,ast.Tuple)) for t in n.targets)
              and all(t.id in constants for target in n.targets
              for t in ast.walk(target) if isinstance(t,ast.Name) and isinstance(t.ctx,ast.Store)))]
    env = {'np':np,'pd':pd}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),env)
    panel = pd.read_csv(ROOT/'Data/processed/panel_v2.csv').sort_values(['站代码','月份']).reset_index(drop=True)
    fit = pd.read_csv(ROOT/'Results/model_fit_by_station.csv')
    saved = json.loads((ROOT/'Results/model_v2.json').read_text(encoding='utf-8'))
    missing = panel[panel.FVC_fixed.isna()][['站代码','月份','split','NDVI','ndvi_flag']].copy()
    panel['FVC_filled'] = panel.groupby('站代码').FVC_fixed.transform(lambda x:x.interpolate(limit=3,limit_direction='both'))
    # List later observations used to fill held-out labels, and train/test boundary cases.
    interpolation = []
    for code,d in panel.groupby('站代码'):
        for idx,r in d[d.FVC_fixed.isna()].iterrows():
            before=d[(d.index<idx)&d.FVC_fixed.notna()]
            after=d[(d.index>idx)&d.FVC_fixed.notna()]
            interpolation.append(dict(station=code,month=r['月份'],split=r['split'],
                previous_month=None if before.empty else before.iloc[-1]['月份'],
                next_month=None if after.empty else after.iloc[0]['月份'],
                filled_value=float(r.FVC_filled)))
    code=saved['task2']['station']
    row=fit.set_index('站代码').loc[code]
    d=panel[panel['站代码']==code].copy()
    tr=d[d.split=='train']
    lo,hi=np.percentile(tr.GWETROOT,[5,90])
    d['W_norm']=env['w_norm'](d.GWETROOT.to_numpy(),lo,hi)
    d['FVC_fixed']=d.FVC_filled
    p=np.array([row.g,row.m,row.k]);cap=row.Vcap
    Wbar=float(d.loc[d.split=='train','W_norm'].mean())
    Tbar=float(tr.T2M.mean());wft=row.WfT_bar
    scen=saved['task2']['scenario']
    ledger=[]
    for r in saved['task2']['path']:
        a=r['a_khm2'];A=r['cum_khm2'];I=r['I_mm']
        ledger.append(dict(year=r['year'],new_ha=a*1000,cumulative_ha=A*1000,
          building_cost=scen['build']*a*1000,maintenance_cost=scen['maint']*A*1000,
          water_cost=scen['water_cost']*(I/100)*a*1000,
          total_cost_as_report_constraint=scen['build']*a*1000+scen['maint']*A*1000+scen['water_cost']*(I/100)*a*1000,
          claimed_B=scen['B'],new_area_water_m3=I*10*a*1000,
          code_reward_zero_if_no_build=a<=0))
    no_build=env['dp_plan'](p,cap,Wbar,Tbar,controls=(0.0,),WfT_bar=wft)
    small_water={}
    for a in (.5,1.,2.):
        wmax=1.0
        I=min(wmax/max(a,1e-9)*1e4/(a*1000),60)
        small_water[str(a)]={'I_mm':I,'water_m3':I*10*a*1000,'limit_if_Wmax_is_10k_m3':wmax*1e4}
    r=env['resilience'](d,p,cap,saved['task3']['lambda_per_year'],n_sim=100)
    recovered=0;censored=0
    for traj in r['paths']:
        failures=np.flatnonzero(traj<r['thr'])
        if len(failures):
            f0=failures[0]
            if (traj[f0:]>=.9*r['V0']).any(): recovered+=1
            else:censored+=1
    no_shock=env['resilience'](d,p,cap,0,n_sim=1)
    wind=env['resilience'](d,p,cap,saved['task3']['lambda_per_year'],n_sim=100,dW=.5)
    qa=pd.read_csv(ROOT/'Data/raw/modis_ndvi_qa_sample.csv')
    qa['month']=qa.calendar_date.str[:7]
    qam=qa[qa.valid].groupby(['站代码','month']).ndvi.max().rename('NDVI_after_QA').reset_index()
    comparisons=panel.merge(qam,left_on=['站代码','月份'],right_on=['站代码','month'])
    comparisons['ndvi_abs_difference']=(comparisons.NDVI-comparisons.NDVI_after_QA).abs()
    comparisons['fvc_difference_pp']=((comparisons.NDVI-.05)/.8).clip(0,1)*100-((comparisons.NDVI_after_QA-.05)/.8).clip(0,1)*100
    qa_difference=comparisons[comparisons.ndvi_abs_difference>1e-10][['站代码','月份','NDVI','NDVI_after_QA','NDVI_qc','ndvi_abs_difference','fvc_difference_pp']]
    # A fresh official response is a metadata probe, not the missing original cache.
    probe_path=OUT/'power_TZ_metadata_probe.json'
    probe=json.loads(probe_path.read_text(encoding='utf-8-sig'))
    power=pd.read_csv(ROOT/'Data/raw/nasa_power_verified/power_monthly.csv')
    tz=power[power['站代码']=='TZ'].copy()
    values=probe['properties']['parameter']['ALLSKY_SFC_SW_DWN']
    tz['probe_radiation']=tz['月份'].str.replace('-','').map(values)
    tz['Rs_MJ_over_probe']=tz.Rs_MJ/tz.probe_radiation
    assert np.allclose(tz.ALLSKY_SFC_SW_DWN,tz.probe_radiation)
    assert np.allclose(tz.Rs_MJ_over_probe,3.6)
    # For a retained footprint, choosing no new construction must not erase O&M.
    zero_new_years=[x for x in ledger if x['new_ha']==0 and x['cumulative_ha']>0]
    # Capacity clipping allows area-based revenue from more new land than exists.
    small_scen=dict(env['SCEN'],A_pot=1.0,T=2,pv_rev=100.0)
    land_probe=env['dp_plan'](p,cap,Wbar,Tbar,scen=small_scen,controls=(0.0,2.0),WfT_bar=wft)
    result=dict(reviewed_commit='b686eab',formal_model_ready=False,
      input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
      panel_rows=len(panel),missing_fvc=len(missing),test_missing_fvc=int((missing.split=='test').sum()),
      r2_median_csv=float(fit.R2_h1_test.median()),r2_median_json=saved['task1']['R2_h1_test_median'],
      worse_than_persistence_from_published_table=fit.loc[fit.RMSE_h1>fit.RMSE_h1_persist,'站代码'].tolist(),
      new_power_responses_present=sum((ROOT/f'Data/cache/power_v2_{c}.json').exists() for c in fit['站代码']),
      old_ndvi_cache_present=(ROOT/'Data/cache/ndvi').exists(),
      source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
      planned_building_cost_sum=sum(x['building_cost'] for x in ledger),
      budget_violating_years=[x['year'] for x in ledger if x['total_cost_as_report_constraint']>x['claimed_B']],
      water_counterexamples=small_water,
      recovery_probe=dict(note='100 simulations using rounded published parameters; counts diagnose implementation, not replacement scientific results',
        function_recov_n=r['recov_n'],actual_returns_to_its_own_threshold=recovered,right_censored=censored,
        function_median=r['recov_median']),
      no_shock_failure_probability=float(no_shock['fail_prob']),
      wind_change_max_difference=float(np.max(np.abs(r['paths']-wind['paths']))),
      plotted_terminal_year=2026+(r['paths'].shape[1]-1)/12,
      qa_months_with_changed_max=len(qa_difference),
      radiation_probe=dict(url=json.loads((ROOT/'Data/raw/nasa_power_verified/manifest_v2.json').read_text(encoding='utf-8'))['entries'][0]['url'],
        checked_on='2026-11-09',sha256=hashlib.sha256(probe_path.read_bytes()).hexdigest(),
        returned_unit=probe['parameters']['ALLSKY_SFC_SW_DWN']['units'],matching_TZ_months=len(tz),
        pipeline_multiplier=float(tz.Rs_MJ_over_probe.median()),
        original_response_hash_matches=hashlib.sha256(probe_path.read_bytes()).hexdigest()==json.loads((ROOT/'Data/raw/nasa_power_verified/manifest_v2.json').read_text(encoding='utf-8'))['entries'][0]['sha256']),
      zero_new_area_years_with_unbilled_maintenance=[x['year'] for x in zero_new_years],
      maintenance_per_zero_new_year_wan_yuan=[x['maintenance_cost'] for x in zero_new_years],
      land_capacity_probe=dict(A_pot=small_scen['A_pot'],path=land_probe['path'],note='Synthetic edge case to test feasibility; not a project result'),
      python_hash_seed_probe={str(seed):int(subprocess.check_output([sys.executable,'-c',"print(abs(hash('ALE')) % 997)"],
          env={**os.environ,'PYTHONHASHSEED':str(seed)})) for seed in (11,23,37)},
      runtime=dict(python=sys.version.split()[0],numpy=np.__version__,pandas=pd.__version__))
    OUT.mkdir(parents=True,exist_ok=True)
    missing.to_csv(OUT/'missing_fvc.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(interpolation).to_csv(OUT/'interpolation_dependencies.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(ledger).to_csv(OUT/'budget_reconciliation.csv',index=False,encoding='utf-8-sig')
    qa_difference.to_csv(OUT/'qa_differences.csv',index=False,encoding='utf-8-sig')
    tz[['月份','ALLSKY_SFC_SW_DWN','Rs_MJ','probe_radiation','Rs_MJ_over_probe']].to_csv(OUT/'radiation_unit_check.csv',index=False,encoding='utf-8-sig')
    changed=[p for p,h in protected.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    assert not changed,changed
    result['tracked_input_files_unchanged']=len(protected)
    (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
