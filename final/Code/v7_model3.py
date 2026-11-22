"""Export M3 tables and validation for Claude; deliberately no figure generation."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from v7_m3_core import ROOT,load_inputs,simulate,stationary_chain
from v7_m1_wind import wind_demand_factors


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def run(out,base_only=False):
    out.mkdir(parents=True,exist_ok=True)
    c,m,m2,coh,f,replay_error=load_inputs();H=c['horizon_years']
    coh.to_csv(out/'initial_cohorts.csv',index=False,float_format='%.10g')
    wind_cache={}
    def factors(cfg):
        trend=cfg['wind_log_trend_per_year']
        if trend not in wind_cache:
            scales=np.exp(trend*np.arange(H))
            table,check=wind_demand_factors(tuple(np.unique(scales)))
            wind_cache[trend]=(np.array([table[s].to_numpy() for s in scales]),check)
        return wind_cache[trend][0]
    stationary=dict(wind_log_trend_per_year=0.,rain_log_trend_per_year=0.,storm_rate_log_trend_per_year=0.,drought_probability_increment=0.)
    cases={
        'base_nonstationary':{},
        'stationary_reference':stationary,
        'no_storm':{'storm_rate_per_year':0.},
        'no_drought':{'drought_probability':0.,'drought_probability_increment':0.},
        'no_random_disasters':{'storm_rate_per_year':0.,'drought_probability':0.,'drought_probability_increment':0.},
        'stable_no_disasters':{**stationary,'storm_rate_per_year':0.,'drought_probability':0.},
        'no_irrigation':{'irrigation_multiplier':0.},
        'water_80pct':{'irrigation_multiplier':.8},
        'water_120pct':{'irrigation_multiplier':1.2},
        'storm_at_year_start':{'shock_order':'start'},
        'independent_cohort_storms':{'shared_storms':False},
        'no_drought_storm_association':{'storm_rate_drought_multiplier':1.},
        'fixed_mean_loss':{'storm_loss_low':.3,'storm_loss_high':.3},
        'threshold_20pctK':{'failure_cover_fraction_K':.2},
        'threshold_40pctK':{'failure_cover_fraction_K':.4},
        'wind_trend_only':{**stationary,'wind_log_trend_per_year':c['wind_log_trend_per_year']},
        'rain_trend_only':{**stationary,'rain_log_trend_per_year':c['rain_log_trend_per_year']},
        'wetter_calmer':{'wind_log_trend_per_year':-.002,'rain_log_trend_per_year':.005,
                         'storm_rate_log_trend_per_year':-.005,'drought_probability_increment':0.},
    }
    for rate in (.1,.25,.5):
        for mean in (.15,.3,.45):
            cases[f'joint_rate_{rate}_loss_{mean}']=dict(storm_rate_per_year=rate,storm_loss_low=mean/2,storm_loss_high=mean*1.5)
    tables={};diagnostics={};configs={};stationary_tables=None
    for name,changes in cases.items():
        if base_only and name!='base_nonstationary':continue
        cfg={**c,**changes};n=c['paths'] if name in ('base_nonstationary','stationary_reference') else c['sensitivity_paths']
        tab,diag=simulate(cfg,m,m2,coh,f,factors(cfg),name,n)
        configs[name]=cfg;diagnostics[name]=diag
        for key,df in tab.items():tables.setdefault(key,[]).append(df)
        if name=='stationary_reference':stationary_tables=tab
        print(name,tab['summary'].iloc[-1][['p_failure','restricted_mean_first_passage_years']].to_dict(),flush=True)
    for key,frames in tables.items():pd.concat(frames,ignore_index=True).to_csv(out/f'{key}.csv',index=False,float_format='%.10g')
    comparison=[];chain_rows=[];chain_diag=[]
    if not base_only:
        cfg={**c,**stationary}
        for nv,nm,nq in c['markov_grids']:
            for j,row in coh.iterrows():
                curve,diag=stationary_chain(cfg,m,m2,coh,f,j,nv,nm,nq)
                chain_rows.append(curve.assign(cohort_id=row.cohort_id,nv=nv,nm=nm,shock_nodes=nq))
                chain_diag.append(dict(cohort_id=row.cohort_id,**diag))
                mc=stationary_tables['cohort_annual'].query('cohort_id == @row.cohort_id')
                for year in (10,30,50):
                    if year>H:continue
                    a=mc.loc[mc.post_year==year].iloc[0];b=curve.loc[curve.post_year==year].iloc[0]
                    comparison.append(dict(cohort_id=row.cohort_id,post_year=year,nv=nv,nm=nm,shock_nodes=nq,
                        markov_failure_probability=b.failure_probability,mc_failure_probability=a.failure_probability,
                        mc_ci95_low=a.ci95_low,mc_ci95_high=a.ci95_high,
                        absolute_difference=abs(b.failure_probability-a.failure_probability),
                        inside_mc_ci95=bool(a.ci95_low<=b.failure_probability<=a.ci95_high)))
                print(f'chain {row.cohort_id} grid={nv}x{nm}, Qnodes={nq}, p50={curve.failure_probability.iloc[-1]:.6f}',flush=True)
        pd.concat(chain_rows,ignore_index=True).to_csv(out/'markov_survival.csv',index=False,float_format='%.10g')
        pd.DataFrame(comparison).to_csv(out/'markov_mc_comparison.csv',index=False,float_format='%.10g')
        write_json(out/'markov_diagnostics.json',chain_diag)
    write_json(out/'scenario_configs.json',configs)
    sources=['Data/v7/m3_inputs/scenario.json','Results/v7/model1/model1_results.json',
        'Results/v7/model1/section_forcing_climatology.csv','Results/v7/model2/model2_results.json',
        'Results/v7/model2/cohorts.csv','Data/v7/processed/panel_monthly_clean.csv',
        'Data/v7/m1_audited/panel_monthly.csv',
        'Code/v7_m1_water.py','Code/v7_m1_wind.py','Code/v7_model1.py','Code/v7_m3_core.py','Code/v7_model3.py']
    # Use the M1 module's actual audited-panel path, not a guessed filename.
    from v7_model1 import PANEL
    sources[6]=str(Path(PANEL).relative_to(ROOT)).replace('\\','/')
    hashes={name:hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in sources}
    result=dict(status='conditional scenario implementation; not a calibrated forecast',formal_model_ready=False,
        model_version='m3_compound_v1',input_text_sha256_lf=hashes,config=c,m1_parameters=m,
        m1_m2_replay_max_abs_error=replay_error,
        time_origin='M2 year 15 end; post-year 1 = project year 16. Initial state is not K.',
        failure_definition='annual census V < rho*K; absorbing first-passage FLAG, physical vegetation can recover',
        project_failure_definition='first annual census with >= configured fraction of area simultaneously below cohort threshold',
        initial_m2_provenance_note='M2 saved pre-removal k=0 metadata; current M1 is replay-compatible within 1e-5; M1/M2 not regenerated',
        environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__),
        wind_response_checks={str(k):v[1] for k,v in wind_cache.items()},simulation_checks=diagnostics,
        markov_checks=chain_diag,
        limitations=['Hazard rates, loss marks, drought associations and future trends are declared assumptions, not local estimates',
            'Storm loss aggregates sandstorm abrasion, wind erosion and burial; not three independent counts',
            'Future wind enters M1 through the existing Penman-Monteith demand ratio, not a restored k coefficient',
            'Drought affects rainfall, demand and available irrigation; future supply continues M2 caps as a scenario',
            'Post-construction O&M and PV cleaning are assumed maintained; future replacement funding and PV revenue not projected',
            '50-year Monte Carlo first-passage mean is right-censored: report RMST, not unconditional expected lifetime',
            'Stationary Markov calculations approximate state and shock integrals, not exact continuous-state solutions',
            'Annual census can miss subannual failure and recovery; thresholds are not measured sand-control standards',
            'Earlier M2 cover-threshold suggestion is not in latest finalized M2; M3 does not reopen M2 objective'],
        case_count=len(configs))
    write_json(out/'model3_results.json',result)
    print('WROTE',out,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'Results/v7/model3')
    p.add_argument('--base-only',action='store_true');args=p.parse_args();run(args.output,args.base_only)
