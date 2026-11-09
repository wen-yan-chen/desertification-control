"""Download original NASA POWER monthly responses with HTTPS verification.
No proxy sand flux or fabricated observations. Python: requests,pandas.
"""
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures,json,hashlib
import requests
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Data/raw/nasa_power_verified'

def fetch(row, previous):
    code=row['站代码']
    params=dict(parameters='WS10M,T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN',community='RE',
                longitude=float(row['经度']),latitude=float(row['纬度']),start='2015',end='2024',format='JSON')
    path=OUT/f'{code}.json'
    url='https://power.larc.nasa.gov/api/temporal/monthly/point'
    if path.exists():
        content=path.read_bytes();data=json.loads(content)
        if code not in previous or previous[code]['request']!=params:
            raise ValueError('Cached response lacks matching provenance: '+code)
        if hashlib.sha256(content).hexdigest()!=previous[code]['sha256']:
            raise ValueError('Cached response hash mismatch: '+code)
        return previous[code],data
    else:
        response=requests.get(url,params=params,timeout=120)
        response.raise_for_status();data=response.json();content=response.content
        assert data.get('properties',{}).get('parameter'),data
        path.write_bytes(content)
    return dict(station=code,url=url,request=params,file=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(content).hexdigest(),units=data.get('parameters'),
                provider_header=data.get('header'),retrieved_date=datetime.now(timezone.utc).date().isoformat()),data

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stations=pd.read_csv(ROOT/'Data/raw/00_站点信息.csv').to_dict('records')
    index=OUT/'manifest.json'
    previous={s['station']:s for s in json.loads(index.read_text(encoding='utf-8'))['sources']} if index.exists() else {}
    manifest=[];rows=[];failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(fetch,row,previous):row['站代码'] for row in stations}
        for fut in concurrent.futures.as_completed(futures):
            try:
                meta,data=fut.result();manifest.append(meta)
                params=data['properties']['parameter'];fill=data.get('header',{}).get('fill_value',-999)
                for month in params['WS10M']:
                    if len(month)!=6 or not month.isdigit() or not 1<=int(month[4:])<=12:continue
                    row={'station':meta['station'],'month':month[:4]+'-'+month[4:]}
                    for var in params:
                        value=params[var].get(month)
                        row[var]=None if value is None or value==fill else value
                    rows.append(row)
                print(meta['station'],'OK',flush=True)
            except Exception as exc:
                failures.append({'station':futures[fut],'error':str(exc)});print(futures[fut],str(exc),flush=True)
    if failures:
        (OUT/'download_failures.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2),encoding='utf-8')
        raise SystemExit('Incomplete download; see download_failures.json. Existing manifest and table preserved; no fabricated replacements.')
    (OUT/'manifest.json').write_text(json.dumps({'sources':sorted(manifest,key=lambda x:x['station']),'failures':failures},ensure_ascii=False,indent=2),encoding='utf-8')
    if rows:pd.DataFrame(rows).sort_values(['station','month']).to_csv(OUT/'monthly.csv',index=False,encoding='utf-8-sig')

if __name__=='__main__':main()
