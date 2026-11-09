"""Save official pages and manually verified, scope-limited numeric facts."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, csv
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Data/raw/local_project_evidence'
SOURCES = [
    dict(id='G01', title='新疆和田探索以防沙治沙实现兴绿富民',
         url='https://www.forestry.gov.cn/c/www/dfdt/620170.jhtml',
         publication_date='2025-04-11', publisher='国家林业和草原局；原载中国绿色时报'),
    dict(id='G02', title='中国铁建和田地区沙漠边缘阻击战锁边固沙工程启动！',
         url='https://www.xjyt.gov.cn/zfgk/diqu/2024-05-24/9105.html',
         publication_date='2024-05-24', publisher='于田县人民政府；来源和田政府网'),
]
# Extracted facts, not automated parameter selection. 1 ha = 15 mu.
FACTS = [
    ['G01-1','G01','后河坝三期工程模式段落','民丰后河坝三期','芦苇方格边长',1.5,'m',1.5,'m','identity','local_reported_configuration','不是最优尺寸；不是草方格保护系数'],
    ['G01-2','G01','后河坝三期工程模式段落','民丰后河坝三期','报道果树栽植密度',66,'plants/mu',990,'plants/ha','66*15','local_reported_configuration','沙枣等果树配置，不适用于所有灌木或风洞模型'],
    ['G01-3','G01','后河坝三期工程模式段落','民丰后河坝三期','三不模式成本节约',964,'CNY/mu',14460,'CNY/ha','964*15','reported_saving_only','节约额不是总造价；价格年/基准未详述，不能设为建设单价'],
    ['G02-1','G02','分别在民丰县于田县实施段落','民丰中国铁建项目','生物治沙规划面积',130000,'mu',130000/15,'ha','130000/15','planned_area','2024年计划，不是已完成面积，缺GIS边界'],
    ['G02-2','G02','分别在民丰县于田县实施段落','于田中国铁建项目','工程固沙规划面积',105000,'mu',7000,'ha','105000/15','planned_area','不同县和工程类型，不与民丰面积相加作均质区段'],
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = OUT / 'sources.json'
    previous = {s['id']: s for s in json.loads(index.read_text(encoding='utf-8'))} if index.exists() else {}
    records = []
    for source in SOURCES:
        path = OUT / (source['id'] + '.html')
        if path.exists():
            known = previous.get(source['id'])
            if not known or known['url'] != source['url'] or hashlib.sha256(path.read_bytes()).hexdigest() != known['sha256']:
                raise RuntimeError('Cached page provenance mismatch: ' + source['id'])
        else:
            response = requests.get(source['url'], timeout=45)
            response.raise_for_status()
            response.encoding = 'utf-8'
            if source['title'] not in response.text:
                raise RuntimeError('Expected article title missing: ' + source['id'])
            path.write_bytes(response.content)
        records.append({**source, 'retrieved_at': previous.get(source['id'], {}).get('retrieved_at', datetime.now(timezone.utc).isoformat()),
                        'file': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'verification_status': 'page_read_and_numeric_context_checked; not a local cost quotation'})
        print(source['id'], 'saved')
    index.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    with (OUT / 'parameters.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id','source_id','locator','location','meaning','original_value','original_unit','converted_value','converted_unit','transformation','evidence_type','applicability'])
        writer.writerows(FACTS)

if __name__ == '__main__':
    main()
