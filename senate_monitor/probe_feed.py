"""Probe documented public election feeds. Diagnostics only; no vote data is fabricated."""
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

OUTPUT = Path(__file__).resolve().parent / "feed_diagnostics.json"
FEEDS = [
    ("civicapi", "https://civicapi.org/api/v2/races", {}),
    ("peoples_tally", "https://thepeoplestally.com/data/results.json", {}),
    ("pollingforecast_2024_sc", "https://www.pollingforecast.com/api/us/counties", {"office":"P","year":2024,"state":"SC"}),
    ("pollingforecast_2022_sc", "https://www.pollingforecast.com/api/us/counties", {"office":"S","year":2022,"state":"SC"}),
]
def probe(name,url,params):
    item={"provider":name,"url":url,"params":params}
    try:
        r=requests.get(url,params=params,timeout=25,headers={"User-Agent":"ElectionMonitor2026/0.2 public research"})
        item["http_status"]=r.status_code
        item["content_type"]=r.headers.get("Content-Type","")
        if not r.ok:
            item["error"]="HTTP error; no data imported"
            return item
        try:
            data=r.json()
        except ValueError:
            item["error"]="Non-JSON response; no data imported"
            return item
        item["json_type"]=type(data).__name__
        if isinstance(data,dict):
            item["top_level_keys"]=list(data)[:35]
            item["field_types"]={k:type(v).__name__ for k,v in list(data.items())[:25]}
            if name.startswith("pollingforecast"):
                item["row_count"]=data.get("count")
                item["licence"]=data.get("licence")
                item["licence_note"]=data.get("licenceNote")
                item["attribution"]=data.get("attribution")
                rows=data.get("rows",[])
                if isinstance(rows,list) and rows and isinstance(rows[0],dict):
                    item["first_row_keys"]=list(rows[0])
                    item["first_row_sample"]=rows[0]
            if name=="peoples_tally":
                item["generated_at"]=data.get("generated_at")
                item["status"]=data.get("status")
                for field in ("races","states","counties"):
                    v=data.get(field)
                    item[field+"_count"]=len(v) if isinstance(v,(dict,list)) else None
                if isinstance(data.get("counties"),dict) and data["counties"]:
                    key=next(iter(data["counties"]))
                    item["county_example_key"]=key
                    value=data["counties"][key]
                    item["county_example_fields"]=list(value)[:35] if isinstance(value,dict) else type(value).__name__
        elif isinstance(data,list):
            item["list_length"]=len(data)
            if data and isinstance(data[0],dict):
                item["first_item_keys"]=list(data[0])[:35]
    except requests.RequestException as e:
        item["error"]=str(e)[:250]
    return item

if __name__=="__main__":
    result={"checked_at":datetime.now(timezone.utc).isoformat(),
            "status":"schema_discovery_only",
            "checks":[probe(*feed) for feed in FEEDS]}
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
    print(OUTPUT.read_text())
