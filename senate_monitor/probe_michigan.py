"""Check official Michigan county results pages for downloadable structured data.

Never parse HTML as election returns; report metadata only.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
from michigan_sources import SOURCES

out={"checked_at":datetime.now(timezone.utc).isoformat(),"status":"source_discovery_only","counties":[]}
for county,source in SOURCES.items():
    record={"county":county,"url":source["url"],"verified_vote_feed":False}
    try:
        response=requests.get(source["url"],timeout=25,headers={"User-Agent":"ElectionMonitor2026/0.6 public results research"})
        record["http_status"]=response.status_code
        record["content_type"]=response.headers.get("Content-Type","")
        record["final_url"]=response.url
        if response.ok and "json" in record["content_type"].lower():
            payload=response.json()
            record["json_type"]=type(payload).__name__
            record["top_level_keys"]=list(payload)[:30] if isinstance(payload,dict) else None
        elif response.ok:
            record["note"]="Page accessible, not a verified machine-readable election feed"
        else:
            record["note"]="Source inaccessible from GitHub Actions"
    except requests.RequestException as exc:
        record["error"]=str(exc)[:200]
    out["counties"].append(record)
target=Path(__file__).resolve().parent/"michigan_diagnostics.json"
target.write_text(json.dumps(out,indent=2)+"\n")
print(target.read_text())
