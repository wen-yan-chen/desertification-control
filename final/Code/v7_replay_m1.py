"""Replay original public MODIS chunks and daily POWER; never rewrite the manifest.

Cache is local/ignored. A differing server response is recorded and never called
the original snapshot. Run this only to rebuild the committed audited M1 inputs.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib
import json
import time
import urllib.request
import urllib.parse
try:
    import truststore
    truststore.inject_into_ssl()  # use OS trust; never disable TLS verification
except ImportError:
    pass

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tmp/m1_raw_complete"

def fetch(rec):
    path = CACHE / rec["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        for attempt in range(3):
            try:
                req = urllib.request.Request(rec["url"], headers={"User-Agent": "MCM research audit"})
                with urllib.request.urlopen(req, timeout=60) as response:
                    data = response.read()
                json.loads(data)
                path.write_bytes(data)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(file=rec["file"], url=rec["url"], original_url=rec.get("original_url", rec["url"]), original_sha256=rec["sha256"],
                replay_sha256=actual, exact_match=actual == rec["sha256"])

def main():
    manifest = json.loads((ROOT / "Data/v7/raw/manifest.json").read_text(encoding="utf-8"))
    requests = []
    for source in manifest["requests"]:
        r = dict(source)
        if r["file"].startswith("power_daily_"):
            requests.append(r)
        elif r["file"].startswith("_cache/modis/"):
            # v7_finalize_fetch incorrectly recorded endDate=startDate, although
            # v7_fetch requested 10-composite blocks (001..145, 161..305, 321..353).
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(r["url"]).query)
            start = query["startDate"][0]
            day = int(start[-3:])
            if day != 161:
                continue  # M1 uses Jun-Sep only; 161..305 includes every such composite
            query["endDate"] = [start[:5]+f"{min(day+144,353):03d}"]
            r["original_url"] = r["url"]
            r["url"] = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?"+urllib.parse.urlencode(query,doseq=True)
            requests.append(r)
    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=12) as pool:
        tasks = {pool.submit(fetch, r): r for r in requests}
        for i, task in enumerate(as_completed(tasks), 1):
            try:
                rows.append(task.result())
            except Exception as exc:
                errors.append(dict(file=tasks[task]["file"], error=str(exc)))
                if len(errors) <= 3:
                    print(errors[-1], flush=True)
            if i % 40 == 0:
                print(f"{i}/{len(requests)}, failures={len(errors)}", flush=True)
    out = ROOT / "Data/v7/m1_audited"
    out.mkdir(exist_ok=True)
    (out / "replay_manifest.json").write_text(json.dumps(dict(
        requests=sorted(rows, key=lambda r: r["file"]), errors=errors), indent=2), encoding="utf-8")
    if errors:
        raise RuntimeError(f"{len(errors)} downloads failed; rerun to resume")
    print(f"Finished {len(rows)} responses; exact hashes: {sum(r['exact_match'] for r in rows)}")

if __name__ == "__main__":
    main()
