"""Non-destructive civicAPI connectivity/schema probe; never invents vote totals."""
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://civicapi.org/api/v2"
OUTPUT = Path(__file__).resolve().parent / "feed_diagnostics.json"
# Only documented base and candidate discovery paths; do not assume a response schema.
PATHS = ["/races"]
def run():
    checks=[]
    for path in PATHS:
        url=BASE+path
        item={"url":url}
        try:
            response=requests.get(url,params={"date":"2026-11-03"},timeout=20,
                                  headers={"User-Agent":"ElectionMonitor2026/0.1 (public research)"})
            item["http_status"]=response.status_code
            item["content_type"]=response.headers.get("Content-Type","")
            try:
                payload=response.json()
                item["json_type"]=type(payload).__name__
                if isinstance(payload,dict):
                    item["top_level_keys"]=list(payload.keys())[:35]
                    item["sample_types"]={k:type(v).__name__ for k,v in list(payload.items())[:20]}
                elif isinstance(payload,list):
                    item["list_length"]=len(payload)
                    if payload and isinstance(payload[0],dict):
                        item["first_item_keys"]=list(payload[0].keys())[:35]
            except ValueError:
                item["error"]="Non-JSON response"
        except requests.RequestException as exc:
            item["error"]=str(exc)[:350]
        checks.append(item)
    OUTPUT.write_text(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(),
                                   "status":"schema_discovery_only","checks":checks},indent=2)+"\n")
    print(OUTPUT.read_text())
if __name__=="__main__":run()
