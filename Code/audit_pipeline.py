"""Reproducible evidence audit, not a fitted physical model or policy result."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def main():
    output=ROOT/'Results/audit';output.mkdir(parents=True,exist_ok=True)
    figures=ROOT/'Figures/audit';figures.mkdir(parents=True,exist_ok=True)
    raw=ROOT/'Data/raw/01_站点月尺度面板_real_raw.csv'
    old=ROOT/'archive/invalidated_20261109/Data/processed/02_panel_clean.csv'
    if not old.exists():old=ROOT/'Data/processed/02_panel_clean.csv'
    r=pd.read_csv(raw);c=pd.read_csv(old)
    assert not r.duplicated(['站代码','月份']).any()
    assert len(r)==960 and r.groupby('站代码').size().eq(120).all()
    joined=r.merge(c,left_on=['站代码','月份'],right_on=['站代码','月份_str'],suffixes=('_raw','_clean'),validate='one_to_one')
    changes={key:int((abs(joined[key+'_raw']-joined[key+'_clean'])>1e-8).sum()) for key in ['风速','降水','气温','植被覆盖度','输沙率']}
    annual=r.assign(year=r['月份'].str[:4]).groupby(['站代码','year'])['输沙率'].sum().groupby(level=0).mean()
    annual.rename('legacy_imposed_mean_not_observation').to_csv(output/'legacy_sand_targets.csv',encoding='utf-8-sig')
    source=ROOT/'Data/raw/nasa_power_verified'
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    assert not manifest['failures'] and len(manifest['sources'])==8
    original_records=[]
    for item in manifest['sources']:
        assert hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['sha256']
        assert item['units']['WS10M']['units']=='m/s'
        assert item['units']['PRECTOTCORR']['units']=='mm/day'
        assert item['units']['T2M']['units']=='C'
        assert item['units']['ALLSKY_SFC_SW_DWN']['units']=='kW-hr/m^2/day'
        original=json.loads((ROOT/item['file']).read_text(encoding='utf-8'))
        values=original['properties']['parameter']
        for key in values['WS10M']:
            if len(key)==6 and key.isdigit() and 1<=int(key[4:])<=12:
                original_records.append(dict(station=item['station'],month=key[:4]+'-'+key[4:],
                                             **{var:series[key] for var,series in values.items()}))
    n=pd.read_csv(source/'monthly.csv')
    assert len(n)==960 and not n.duplicated(['station','month']).any()
    expected=pd.DataFrame(original_records).sort_values(['station','month']).reset_index(drop=True)
    pd.testing.assert_frame_equal(n.sort_values(['station','month']).reset_index(drop=True),expected[n.columns],check_dtype=False)
    assert n.notna().all().all() and n.groupby('station').size().eq(120).all()
    assert (n[['WS10M','PRECTOTCORR','ALLSKY_SFC_SW_DWN']]>=0).all().all()
    n['days']=pd.to_datetime(n['month']+'-01').dt.days_in_month
    n['precip_mm_month']=n.PRECTOTCORR*n.days
    assert n.loc[n.month=='2020-02','days'].eq(29).all()
    for source_item in json.loads((ROOT/'Data/raw/local_project_evidence/sources.json').read_text(encoding='utf-8')):
        assert hashlib.sha256((ROOT/source_item['file']).read_bytes()).hexdigest()==source_item['sha256']
    archive_items=json.loads((ROOT/'archive/invalidated_20261109/manifest.json').read_text(encoding='utf-8-sig'))
    assert len(archive_items)==50
    for archived in archive_items:
        assert hashlib.sha256((ROOT/archived['archive_path']).read_bytes()).hexdigest()==archived['sha256']
    m=r.merge(n,left_on=['站代码','月份'],right_on=['station','month'],validate='one_to_one')
    rows=[]
    pairs=[('wind_10m','风速','WS10M','m/s'),('temperature','气温','T2M','degC'),('precipitation','降水','precip_mm_month','mm/month')]
    for station,d in [('ALL',m)]+list(m.groupby('站代码')):
        for label,left,right,unit in pairs:
            z=d[[left,right]].dropna();a=z[left].to_numpy();b=z[right].to_numpy()
            assert len(z)>1
            rows.append(dict(station=station,variable=label,n=len(z),unit=unit,bias_legacy_minus_POWER=float((a-b).mean()),
                             rmse=float(np.sqrt(np.mean((a-b)**2))),pearson_r=float(np.corrcoef(a,b)[0,1]),
                             agreement_r2_relative_to_POWER=float(1-np.sum((a-b)**2)/np.sum((b-b.mean())**2))))
    pd.DataFrame(rows).to_csv(output/'matched_height_source_comparison.csv',index=False,encoding='utf-8-sig')
    # Keep physical variables, missing flags and explicit source status. Do not impute or clip tails.
    diagnostic=r.drop(columns=['输沙率','输沙势','植被覆盖度','端元方案']).copy()
    diagnostic['ndvi_quality_status']='QA unavailable; exploratory only'
    diagnostic['meteorology_source_status']='legacy API model unspecified; not station observations'
    diagnostic['elapsed_years_since_2015']=((pd.to_datetime(diagnostic['月份']).dt.year-2015)*12+pd.to_datetime(diagnostic['月份']).dt.month-1)/12
    diagnostic['split']=np.where(diagnostic['月份']<'2023-01','train','test')
    prepared=ROOT/'Data/processed/audited';prepared.mkdir(parents=True,exist_ok=True)
    diagnostic.to_csv(prepared/'exploratory_panel.csv',index=False,encoding='utf-8-sig')
    n.to_csv(prepared/'nasa_power_monthly.csv',index=False,encoding='utf-8-sig')
    anchors=pd.read_csv(ROOT/'Data/raw/01_文献参数锚点_raw.csv')
    anchor_status=anchors[['锚点编号']].copy()
    anchor_status['verification_status']='pending_source_verification'
    anchor_status['model_parameter_eligible']=False
    anchor_status['reason']='Exact source page, experimental scale and applicability must be verified'
    anchor_status.to_csv(prepared/'anchor_verification.csv',index=False,encoding='utf-8-sig')
    blockers=['representative margin section geometry not identified','NDVI composite QA and original responses unavailable',
              'root depth, field capacity, wilting point and local water supply not established',
              'engineering costs, labor productivity, PV tariff and budget require local sources or explicit scenario specification',
              'event damage/recovery observations and nonstationary climate inputs not established']
    report=dict(date='2026-11-09',raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),rows=len(r),
                missing_raw=r.isna().sum().to_dict(),changed_by_old_winsorization=changes,
                nasa_rows=len(n),nasa_missing=n.isna().sum().to_dict(),task3_authorized_condition_met=False,
                archive_files_verified=len(archive_items),local_official_pages_verified=2,
                runtime_versions=dict(numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__),
                formal_model_ready=False,blockers=blockers,
                legacy_claims_invalidated=['NPV 20384万元','optimal plan superiority 2.2x','15-year failure probability 84%','2050 coverage 6.7%'])
    (output/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'font.size':10})
    fig,axes=plt.subplots(1,3,figsize=(12,3.7))
    for ax,(label,left,right,unit) in zip(axes,pairs):
        ax.scatter(m[right],m[left],s=9,alpha=.3,color='#387F83',rasterized=True)
        lo=min(m[left].min(),m[right].min());hi=max(m[left].max(),m[right].max())
        ax.plot([lo,hi],[lo,hi],ls='--',lw=1,color='#B77D51')
        ax.set(xlabel='NASA POWER ('+unit+')',ylabel='Legacy API panel ('+unit+')',title=label.replace('_',' ').title())
    fig.suptitle('Reanalysis agreement audit | matched wind height | not validation against ground truth',fontsize=11)
    fig.tight_layout();fig.savefig(figures/'source_comparison.png',dpi=220);plt.close(fig)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
