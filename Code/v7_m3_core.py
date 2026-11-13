"""M3: compound storms + drought + nonstationary forcing on the FINAL M1 map.

M2's final cohort states start a new post-construction clock. Water allocation is
constrained each month; no refitting M1, no wind-loss coefficient, no plotting.
First passage is a diagnostic flag; physical cover may recover after failure.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import poisson
from scipy.sparse.linalg import spsolve
from v7_m1_water import WaterParameters, water_year, vegetation_step, trajectory

ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    c = json.loads((ROOT/'Data/v7/m3_inputs/scenario.json').read_text(encoding='utf-8'))
    m = json.loads((ROOT/'Results/v7/model1/model1_results.json').read_text(encoding='utf-8'))['adopted_parameters']
    m2 = json.loads((ROOT/'Results/v7/model2/model2_results.json').read_text(encoding='utf-8'))
    f = pd.read_csv(ROOT/'Results/v7/model1/section_forcing_climatology.csv')
    if list(f.month) != list(range(1,13)):
        raise ValueError('Forcing months must be ordered 1..12')
    f = f[['days','P_mm','ET0g_mm']].to_numpy()
    all_cohorts = pd.read_csv(ROOT/'Results/v7/model2/cohorts.csv')
    cohorts = all_cohorts.sort_values('year').groupby('cohort_id',sort=True).tail(1).sort_values('cohort_id').reset_index(drop=True)
    if not (cohorts.year == m2['config']['years']).all() or (cohorts.area_ha <= 0).any():
        raise ValueError('Need positive-area M2 cohorts at the planning horizon')
    # Latest M1 removes the old k=0 term; small floating fit changes are accepted
    # only after replay of every existing M2 cohort, never silent initial reset.
    errs=[]
    for cid,g in all_cohorts.groupby('cohort_id'):
        g=g.sort_values('year')
        a,_=trajectory(float(g.iloc[0].V_start_pct),float(g.iloc[0].M_start_mm),len(g),
            m['K_section_pct'],m['r'],m['d'],f,g.irrigation_mm_yr.to_numpy(),WaterParameters(**m['water']))
        errs.append(max(float(np.max(abs(a.V_end_pct.to_numpy()-g.V_end_pct.to_numpy()))),
                        float(np.max(abs(a.M_end_mm.to_numpy()-g.M_end_mm.to_numpy())))))
    if max(errs)>1e-5:
        raise ValueError(f'M1/M2 interface mismatch; replay error {max(errs)}')
    return c,m,m2,cohorts,f,max(errs)


def validate(c,m):
    numeric=[v for v in c.values() if isinstance(v,(float,int))]
    if not np.isfinite(numeric).all():
        raise ValueError('Nonfinite scenario')
    for key in ('horizon_years','paths','sensitivity_paths'):
        if not isinstance(c[key],int) or c[key]<1:
            raise ValueError(f'Invalid {key}')
    if not 0<c['failure_cover_fraction_K']<1 or not 0<c['project_failed_area_fraction']<=1:
        raise ValueError('Invalid failure threshold')
    if not 0<=c['storm_loss_low']<=c['storm_loss_high']<1:
        raise ValueError('Invalid storm mark range')
    for key in ('storm_rate_per_year','storm_rate_drought_multiplier','irrigation_multiplier','drought_et_multiplier'):
        if c[key]<0:
            raise ValueError(f'Negative {key}')
    for key in ('drought_rain_multiplier','drought_supply_multiplier'):
        if not 0<=c[key]<=1:
            raise ValueError(f'Invalid {key}')
    probs=c['drought_probability']+np.arange(c['horizon_years'])*c['drought_probability_increment']
    if ((probs<0)|(probs>1)).any() or c['shock_order'] not in ('start','end'):
        raise ValueError('Invalid drought probabilities or shock ordering')
    WaterParameters(**m['water']).validate()


def batch_year(v,m0,forcing,gross_mm,model):
    """Exact vectorized M1 daily bucket, with externally scheduled monthly water.

    Last axis of gross_mm is month; leading axes broadcast over state/path/cohort.
    Scalar M1 is unchanged; equivalence is tested when its annual quota is used.
    """
    v,m0=np.broadcast_arrays(np.asarray(v,float),np.asarray(m0,float))
    f=np.asarray(forcing,float); gross=np.asarray(gross_mm,float)
    p=WaterParameters(**model['water']);p.validate();K=model['K_section_pct']
    if f.shape!=(12,3) or (f<0).any() or not np.isfinite(f).all() or not np.all(f[:,0]==f[:,0].astype(int)) or (f[:,0]<1).any():
        raise ValueError('Invalid monthly forcing')
    if gross.shape[-1]!=12 or (gross<0).any() or not np.isfinite(gross).all():
        raise ValueError('Invalid gross irrigation')
    if not np.isfinite(v).all() or not np.isfinite(m0).all() or (v<0).any() or (v>K).any() or (m0<0).any() or (m0>p.capacity_mm).any():
        raise ValueError('State outside M1 domain')
    storage=m0.copy(); transp=np.zeros_like(v); demand_total=np.zeros_like(v); max_res=0.
    cover_factor=p.c*np.minimum(1.,2*v/p.v_full_pct)
    for month,(days,rain,et) in enumerate(f):
        inflow=p.rain_fraction*rain+p.eta_w*gross[...,month]+p.groundwater_mm_yr*days/f[:,0].sum()
        demand=cover_factor*et
        start=storage.copy(); uptake_total=np.zeros_like(v);drain=np.zeros_like(v)
        for _ in range(int(days)):
            available=storage+inflow/days
            excess=np.maximum(available-p.capacity_mm,0.)
            available=available-excess
            stress=np.minimum(1.,available/((1-p.depletion_fraction)*p.capacity_mm))
            uptake=np.minimum(available,stress*demand/days)
            storage=available-uptake;uptake_total+=uptake;drain+=excess
        max_res=max(max_res,float(np.max(abs(start+inflow-uptake_total-drain-storage))))
        transp+=uptake_total;demand_total+=demand
    w=np.divide(transp,demand_total,out=np.zeros_like(v),where=demand_total>0)
    vend=v+model['r']*v*(1-v/K)*w-model['d']*v
    if max_res>1e-8 or (vend<-1e-9).any() or (vend>K+1e-9).any():
        raise ArithmeticError('M1 water balance or cover domain violated')
    return vend,storage,w,max_res


def climate(c,forcing,wind_factors,t,dry=False):
    f=forcing.copy()
    f[:,1]*=np.exp(c['rain_log_trend_per_year']*t)
    f[:,2]*=wind_factors[t]
    if dry:
        f[:,1]*=c['drought_rain_multiplier'];f[:,2]*=c['drought_et_multiplier']
    return f


def allocation(c,m2,cohorts,f,dry=False):
    """Pro-rata ecological rationing after reserving continued PV cleaning water."""
    mc=m2['config'];weights=f[:,2]/f[:,2].sum()
    request=cohorts.irrigation_mm_yr.to_numpy()[:,None]*c['irrigation_multiplier']*weights
    volumes=request*cohorts.area_ha.to_numpy()[:,None]*10
    supply=c['drought_supply_multiplier'] if dry else 1.
    month_cap=np.asarray(mc['monthly_water_caps_m3'])*supply
    annual_cap=mc['annual_water_cap_m3']*supply
    pv=m2['base']['pv_installed_final_kw']*mc['pv_cleaning_m3_kw_year']/12
    pv_month=np.minimum(pv,month_cap)
    if pv_month.sum()>annual_cap:
        pv_month*=annual_cap/pv_month.sum()
    available=np.maximum(month_cap-pv_month,0.)
    totals=volumes.sum(axis=0)
    ratio=np.minimum(1.,np.divide(available,totals,out=np.ones(12),where=totals>0))
    actual=request*ratio
    actual_vol=actual*cohorts.area_ha.to_numpy()[:,None]*10
    year_ratio=min(1.,max(annual_cap-pv_month.sum(),0.)/actual_vol.sum()) if actual_vol.sum()>0 else 1.
    actual*=year_ratio
    total=(actual*cohorts.area_ha.to_numpy()[:,None]*10).sum(axis=0)+pv_month
    if (total>month_cap+1e-7).any() or total.sum()>annual_cap+1e-7:
        raise ArithmeticError('Water allocation violates capacity')
    return actual,dict(total_m3=total,cap_m3=month_cap,annual_cap_m3=annual_cap,
        requested_eco_m3=volumes.sum(axis=0),delivered_eco_m3=total-pv_month,pv_m3=pv_month)


def storm_draw(rng,lam,lo,hi):
    n=rng.poisson(lam); retention=np.ones(n.shape)
    for k in range(int(n.max(initial=0))):
        u=rng.uniform(lo,hi,n.shape)
        retention*=np.where(n>k,1-u,1.)
    return retention,n


def wilson(events,n):
    p=np.asarray(events,dtype=float)/n;z=1.959963984540054
    center=(p+z*z/(2*n))/(1+z*z/n)
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return np.where(p==0,0.,np.maximum(0,center-half)),np.where(p==1,1.,np.minimum(1,center+half))


def simulate(c,model,m2,cohorts,forcing,wind_factors,case='base',paths=None):
    validate(c,model)
    n=paths or c['paths'];H=c['horizon_years'];C=len(cohorts);K=model['K_section_pct']
    rng=np.random.default_rng(c['seed']);area=cohorts.area_ha.to_numpy();crit=c['failure_cover_fraction_K']*K
    v=np.broadcast_to(cohorts.V_end_pct.to_numpy(),(n,C)).copy()
    m=np.broadcast_to(cohorts.M_end_mm.to_numpy(),(n,C)).copy()
    tau=np.where(v<crit,0,H+1);project_tau=np.where(((v<crit)*area).sum(axis=1)/area.sum()>=c['project_failed_area_fraction'],0,H+1)
    eco=np.zeros(n);records=[];project=[];resource=[];samples=[];max_res=0.;events_total=0;dry_total=0
    def record(t):
        for j,row in cohorts.iterrows():
            hit=(tau[:,j]<=t);lo,hi=wilson(hit.sum(),n)
            records.append(dict(case=case,post_year=t,cohort_id=row.cohort_id,area_ha=row.area_ha,
                V_mean_pct=float(v[:,j].mean()),V_p05_pct=float(np.quantile(v[:,j],.05)),
                V_p50_pct=float(np.quantile(v[:,j],.5)),V_p95_pct=float(np.quantile(v[:,j],.95)),
                M_mean_mm=float(m[:,j].mean()),failure_probability=float(hit.mean()),ci95_low=float(lo),ci95_high=float(hi),
                current_below_threshold_probability=float((v[:,j]<crit).mean())))
        hit=project_tau<=t;lo,hi=wilson(hit.sum(),n)
        project.append(dict(case=case,post_year=t,project_failure_probability=float(hit.mean()),
            ci95_low=float(lo),ci95_high=float(hi),expected_ever_failed_area_ha=float(((tau<=t)*area).sum(axis=1).mean()),
            expected_current_failed_area_ha=float(((v<crit)*area).sum(axis=1).mean()),
            expected_cover_area_ha=float((v/K*area).sum(axis=1).mean()),
            cumulative_cover_ha_year_mean=float(eco.mean()),
            cumulative_cover_ha_year_p05=float(np.quantile(eco,.05)),
            cumulative_cover_ha_year_p95=float(np.quantile(eco,.95)),
            V_area_weighted_mean_pct=float((v@area/area.sum()).mean())))
        for i in range(min(n,12)):
            for j,row in cohorts.iterrows():
                samples.append(dict(case=case,path_id=i,post_year=t,cohort_id=row.cohort_id,V_pct=v[i,j],M_mm=m[i,j],ever_failed=bool(tau[i,j]<=t)))
    record(0)
    for t in range(H):
        dry=rng.random(n)<c['drought_probability']+t*c['drought_probability_increment'];dry_total+=int(dry.sum())
        lam=c['storm_rate_per_year']*np.exp(c['storm_rate_log_trend_per_year']*t)*np.where(dry,c['storm_rate_drought_multiplier'],1.)
        lam=lam[:,None] if c['shared_storms'] else np.broadcast_to(lam[:,None],(n,C))
        retention,counts=storm_draw(rng,lam,c['storm_loss_low'],c['storm_loss_high']);events_total+=int(counts.sum())
        if c['shock_order']=='start':
            v*=retention
        # Annual-census definition: failure checked after the complete year.
        eco+=(v/K*area).sum(axis=1)
        for flag in (False,True):
            f=climate(c,forcing,wind_factors,t,flag);gross,ledger=allocation(c,m2,cohorts,f,flag)
            mask=dry==flag
            if mask.any():
                vn,mn,_,err=batch_year(v[mask],m[mask],f,gross,model)
                v[mask]=vn;m[mask]=mn;max_res=max(max_res,err)
            for month in range(12):
                resource.append(dict(case=case,post_year=t+1,drought=flag,month=month+1,
                    gross_water_m3=ledger['total_m3'][month],cap_m3=ledger['cap_m3'][month],
                    slack_m3=ledger['cap_m3'][month]-ledger['total_m3'][month],
                    requested_eco_m3=ledger['requested_eco_m3'][month],delivered_eco_m3=ledger['delivered_eco_m3'][month],
                    rain_mm=f[month,1],ET0g_mm=f[month,2],wind_speed_scale=np.exp(c['wind_log_trend_per_year']*t)))
        if c['shock_order']=='end':v*=retention
        tau=np.where((tau==H+1)&(v<crit),t+1,tau)
        project_hit=((v<crit)*area).sum(axis=1)/area.sum()>=c['project_failed_area_fraction']
        project_tau=np.where((project_tau==H+1)&project_hit,t+1,project_tau)
        record(t+1)
    summaries=[];hist=[]
    for j,cid in enumerate(cohorts.cohort_id):
        lo,hi=wilson((tau[:,j]<=H).sum(),n)
        summaries.append(dict(case=case,entity=cid,paths=n,horizon_years=H,p_failure=float((tau[:,j]<=H).mean()),
            ci95_low=float(lo),ci95_high=float(hi),restricted_mean_first_passage_years=float(np.minimum(tau[:,j],H).mean()),
            restricted_mean_mc_se=float(np.minimum(tau[:,j],H).std(ddof=1)/np.sqrt(n)) if n>1 else 0.,
            censored_count=int((tau[:,j]>H).sum()),V_final_mean_pct=float(v[:,j].mean())))
        hist.extend(dict(case=case,entity=cid,first_failure_year=t,count=int((tau[:,j]==t).sum()),censored=t==H+1) for t in range(H+2))
    lo,hi=wilson((project_tau<=H).sum(),n)
    summaries.append(dict(case=case,entity='project',paths=n,horizon_years=H,p_failure=float((project_tau<=H).mean()),
        ci95_low=float(lo),ci95_high=float(hi),restricted_mean_first_passage_years=float(np.minimum(project_tau,H).mean()),
        restricted_mean_mc_se=float(np.minimum(project_tau,H).std(ddof=1)/np.sqrt(n)) if n>1 else 0.,
        censored_count=int((project_tau>H).sum()),V_final_mean_pct=float((v@area/area.sum()).mean())))
    hist.extend(dict(case=case,entity='project',first_failure_year=t,count=int((project_tau==t).sum()),censored=t==H+1) for t in range(H+2))
    return dict(cohort_annual=pd.DataFrame(records),project_annual=pd.DataFrame(project),resources=pd.DataFrame(resource),
        sample_paths=pd.DataFrame(samples),summary=pd.DataFrame(summaries),first_passage_counts=pd.DataFrame(hist)),dict(
            max_water_balance_residual_mm=max_res,storm_event_draw_count=events_total,drought_path_years=dry_total,
            ecological_integral_mean=float(eco.mean()),ecological_integral_mc_se=float(eco.std(ddof=1)/np.sqrt(n)))


def compound_nodes(lam,lo,hi,nodes=48,tol=1e-12,bins=256):
    """Deterministic quantile compression of a compound log-loss convolution.

    Exact no-event atom retained. Poisson tail goes to zero retention; exported
    tail bound separates that error from log bins/quantile and state-grid errors.
    """
    if lam<0 or not 0<=lo<=hi<1:raise ValueError('Invalid compound distribution')
    if lam==0 or hi==0:return np.array([1.]),np.array([1.]),dict(tail_mass=0.,mean_error=0.)
    nmax=int(poisson.isf(tol,lam));tail=float(poisson.sf(nmax,lam));p0=float(np.exp(-lam))
    if lo==hi:
        ns=np.arange(nmax+1);r=(1-lo)**ns;weights=poisson.pmf(ns,lam)
        return np.r_[r,0.],np.r_[weights,tail],dict(tail_mass=tail,mean_error=float(r@weights-np.exp(-lam*lo)))
    delta=-np.log1p(-hi)/bins;edges=np.arange(bins+1)*delta
    probs=np.diff(np.clip((1-np.exp(-edges)-lo)/(hi-lo),0,1))
    probs/=probs.sum();mass=np.array([1.]);values=[];weights=[]
    for count in range(1,nmax+1):
        mass=np.convolve(mass,probs)
        values.extend(np.exp(-delta*(np.arange(len(mass))+count/2)))
        weights.extend(poisson.pmf(count,lam)*mass)
    order=np.argsort(values);values=np.asarray(values)[order];weights=np.asarray(weights)[order]
    positive_mass=weights.sum();cdf=np.cumsum(weights)/positive_mass
    r=values[np.searchsorted(cdf,(np.arange(nodes)+.5)/nodes)]
    rr=np.r_[1.,r,0.];ww=np.r_[p0,np.full(nodes,positive_mass/nodes),tail];ww/=ww.sum()
    return rr,ww,dict(tail_mass=tail,mean_error=float(rr@ww-np.exp(-lam*(lo+hi)/2)))


def interpolation(v,m,vg,mg):
    """Bilinear projection on transient (V,M) grid; threshold test is external."""
    v=np.clip(v,vg[0],vg[-1]);m=np.clip(m,mg[0],mg[-1])
    i=np.minimum(np.searchsorted(vg,v,side='right')-1,len(vg)-2)
    j=np.minimum(np.searchsorted(mg,m,side='right')-1,len(mg)-2)
    a=(v-vg[i])/(vg[i+1]-vg[i]);b=(m-mg[j])/(mg[j+1]-mg[j])
    indices=np.stack((i*len(mg)+j,(i+1)*len(mg)+j,i*len(mg)+j+1,(i+1)*len(mg)+j+1))
    weights=np.stack(((1-a)*(1-b),a*(1-b),(1-a)*b,a*b))
    return indices,weights


def stationary_chain(c,model,m2,cohorts,forcing,cohort_index,nv,nm,nq):
    """2-D killed chain for stationary end-of-year shocks only, not a 1-D V chain."""
    if c['shock_order']!='end' or any(c[k]!=0 for k in ('wind_log_trend_per_year','rain_log_trend_per_year','storm_rate_log_trend_per_year','drought_probability_increment')):
        raise ValueError('Stationary chain requires stationary forcing and end shocks')
    crit=c['failure_cover_fraction_K']*model['K_section_pct'];vg=np.linspace(crit,model['K_section_pct'],nv)
    mg=np.linspace(0,model['water']['capacity_mm'],nm);vv,mm=np.meshgrid(vg,mg,indexing='ij');v=vv.ravel();m=mm.ravel();N=len(v)
    rows=[];cols=[];data=[];marks=[]
    for dry,prob in ((False,1-c['drought_probability']),(True,c['drought_probability'])):
        if prob==0:continue
        f=climate(c,forcing,np.ones((c['horizon_years'],12)),0,dry)
        gross,_=allocation(c,m2,cohorts,f,dry)
        vend,mend,_,_=batch_year(v,m,f,gross[cohort_index],model)
        r,w,diag=compound_nodes(c['storm_rate_per_year']*(c['storm_rate_drought_multiplier'] if dry else 1),c['storm_loss_low'],c['storm_loss_high'],nq,c['poisson_tail_tolerance'])
        marks.append(diag)
        for retention,weight in zip(r,w):
            vn=vend*retention;alive=vn>=crit
            idx,ww=interpolation(vn[alive],mend[alive],vg,mg)
            rows.append(np.tile(np.flatnonzero(alive),4));cols.append(idx.ravel());data.append((ww*weight*prob).ravel())
    Q=sparse.coo_matrix((np.concatenate(data),(np.concatenate(rows),np.concatenate(cols))),shape=(N,N)).tocsr();Q.eliminate_zeros()
    row_sums=np.asarray(Q.sum(axis=1)).ravel()
    if Q.data.min(initial=0)<-1e-12 or row_sums.max()>1+1e-10:raise ArithmeticError('Invalid substochastic matrix')
    init=cohorts.iloc[cohort_index];p=np.zeros(N)
    if init.V_end_pct>=crit:
        idx,ww=interpolation(np.array([init.V_end_pct]),np.array([init.M_end_mm]),vg,mg)
        np.add.at(p,idx.ravel(),ww.ravel())
    p0=p.copy();survival=[float(p.sum())]
    for _ in range(c['horizon_years']):p=p@Q;survival.append(float(p.sum()))
    # Do not invert a singular fundamental matrix. Only report moments when a
    # nonnegative solution with small residual is found (positive storm baseline).
    mean=variance=None;residual=None
    if c['storm_rate_per_year']>0 and c['storm_loss_high']>0:
        I=sparse.eye(N,format='csr');t=spsolve(I-Q,np.ones(N));second=spsolve(I-Q,2*t-1)
        residual=float(np.max(abs((I-Q)@t-1)))
        if np.isfinite(t).all() and (t>=-1e-6).all() and residual<1e-6:
            mean=float(p0@t);variance=float(p0@second-mean**2)
    return pd.DataFrame(dict(post_year=np.arange(c['horizon_years']+1),failure_probability=1-np.asarray(survival))),dict(
        nv=nv,nm=nm,shock_nodes=nq,transient_states=N,nonzeros=Q.nnz,max_row_sum=float(row_sums.max()),
        min_absorption_probability=float((1-row_sums).min()),expected_first_passage_years=mean,
        variance_first_passage_years2=variance,linear_solve_residual=residual,
        restricted_mean_first_passage_years=float(sum(survival[:-1])),compound_diagnostics=marks)
