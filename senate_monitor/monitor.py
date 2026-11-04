"""Public-source county election monitor. No winner/seat predictions.
Run: python monitor.py --once   OR python monitor.py --loop
"""
import argparse, csv, io, json, os, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT=Path(__file__).parent
DB=ROOT/'monitor.sqlite'
HIST='https://www.pollingforecast.com/api/us/counties'
STATES='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
SENATE_STATES='AL AK AR CO DE FL GA ID IL IA KS KY LA ME MA MI MS MT NE NH NJ NM NC OH OK OR RI SC SD TN TX VA WV WY'.split()
# Verify list with official election authority; configure as necessary. 2026 special elections included.

def db():
 c=sqlite3.connect(DB);c.execute('PRAGMA journal_mode=WAL')
 c.executescript('''CREATE TABLE IF NOT EXISTS historical (state TEXT, county TEXT, year INTEGER, office TEXT, dem INTEGER, rep INTEGER, total INTEGER, PRIMARY KEY(state,county,year,office));
 CREATE TABLE IF NOT EXISTS current (state TEXT, county TEXT, race TEXT, dem INTEGER, rep INTEGER, total INTEGER, complete INTEGER, source TEXT, observed_at TEXT, PRIMARY KEY(state,county,race));
 CREATE TABLE IF NOT EXISTS snapshots (observed_at TEXT, state TEXT, race TEXT, counties_reporting INTEGER, counties_complete INTEGER, observed_dem INTEGER, observed_rep INTEGER, observed_total INTEGER, swing_2024_pp REAL, swing_2022_pp REAL, source TEXT);
 CREATE TABLE IF NOT EXISTS ingest_log (at TEXT, source TEXT, status TEXT, details TEXT);''');return c

def norm(s):
 s=str(s).strip().upper().replace(' COUNTY','').replace(' PARISH','').replace(' BOROUGH','')
 return ' '.join(s.split())

def log(c,src,status,msg):
 c.execute('INSERT INTO ingest_log VALUES (?,?,?,?)',(datetime.now(timezone.utc).isoformat(),src,status,msg[:400]))

def historical(state,year,office,session=None):
 r=(session or requests).get(HIST,params={'office':office,'year':year,'state':state},timeout=25,headers={'User-Agent':'CountyMonitor/0.1 research'})
 r.raise_for_status();obj=r.json();rows=obj.get('rows',[]) if isinstance(obj,dict) else obj
 out=[]
 for x in rows:
  def get(*keys):
   for k in keys:
    if x.get(k) is not None:return x[k]
  county=get('county','county_name','name','countyName')
  if not county:continue
  try:
   d=int(float(get('dem','dem_votes','democratic_votes','votes_dem') or 0));p=int(float(get('rep','rep_votes','republican_votes','votes_rep') or 0));t=int(float(get('total','total_votes','votes_total') or d+p))
   out.append((state,norm(county),year,office,d,p,t))
  except (TypeError,ValueError):continue
 if not out:raise ValueError('No compatible county rows; inspect provider JSON schema before mapping')
 return out

def load_history(states,year_office=((2024,'P'),(2022,'S'))):
 with db() as c:
  for st in states:
   for year,office in year_office:
    try:
     rows=historical(st,year,office)
     c.executemany('INSERT OR REPLACE INTO historical VALUES (?,?,?,?,?,?,?)',rows)
     log(c,f'history:{st}:{year}:{office}','ok',f'{len(rows)} counties')
    except Exception as e:log(c,f'history:{st}:{year}:{office}','error',str(e))

def ingest_csv(path):
 """CSV: state,county,race,dem,rep,total,complete,source. `complete` must be confirmed by provider."""
 stamp=datetime.now(timezone.utc).isoformat();count=0
 with open(path,newline='',encoding='utf-8-sig') as f,db() as c:
  for x in csv.DictReader(f):
   st=x['state'].strip().upper();co=norm(x['county']);race=x.get('race','SENATE').strip().upper()
   d=int(x['dem']);r=int(x['rep']);t=int(x.get('total') or d+r)
   if d<0 or r<0 or t<d+r:raise ValueError(f'Invalid vote totals: {st} {co}')
   complete=int(str(x.get('complete','0')).lower() in ('1','true','yes'))
   c.execute('INSERT INTO current VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(state,county,race) DO UPDATE SET dem=excluded.dem,rep=excluded.rep,total=excluded.total,complete=excluded.complete,source=excluded.source,observed_at=excluded.observed_at',(st,co,race,d,r,t,complete,x.get('source','csv'),stamp));count+=1
  log(c,str(path),'ok',f'{count} records')
 return count

def fetch_public_csv(url):
 """Only fetch an authorized publicly accessible CSV URL; no bypasses or hidden endpoints."""
 if not url.startswith('https://'):raise ValueError('HTTPS URL required')
 resp=requests.get(url,timeout=25,headers={'User-Agent':'CountyMonitor/0.1 research'});resp.raise_for_status()
 if len(resp.content)>10_000_000:raise ValueError('Feed too large')
 path=ROOT/'latest_feed.csv';path.write_bytes(resp.content);return ingest_csv(path)

def calculate():
 stamp=datetime.now(timezone.utc).isoformat()
 with db() as c:
  groups=c.execute('SELECT DISTINCT state,race FROM current').fetchall()
  for st,race in groups:
   curr=c.execute('SELECT county,dem,rep,total,complete,source FROM current WHERE state=? AND race=?',(st,race)).fetchall()
   history={}
   for year,office in ((2024,'P'),(2022,'S')):
    history[(year,office)]={x[0]:(x[1],x[2]) for x in c.execute('SELECT county,dem,rep FROM historical WHERE state=? AND year=? AND office=?',(st,year,office))}
   def swing(key):
    pairs=[(d,r,*history[key][co]) for co,d,r,t,complete,src in curr if complete and co in history[key] and d+r>0 and sum(history[key][co])>0]
    if not pairs:return None
    cd=sum(v[0] for v in pairs);cr=sum(v[1] for v in pairs);hd=sum(v[2] for v in pairs);hr=sum(v[3] for v in pairs)
    return round(100*(cd/(cd+cr)-hd/(hd+hr)),2)
   d=sum(x[1] for x in curr);r=sum(x[2] for x in curr);t=sum(x[3] for x in curr)
   c.execute('INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?)',(stamp,st,race,len(curr),sum(x[4] for x in curr),d,r,t,swing((2024,'P')),swing((2022,'S')),','.join(sorted(set(x[5] for x in curr)))))
  log(c,'calculate','ok',f'{len(groups)} state/race groups')

def main():
 p=argparse.ArgumentParser();p.add_argument('--history',action='store_true');p.add_argument('--states',default='SC,GA,NC,TX');p.add_argument('--csv');p.add_argument('--url');p.add_argument('--once',action='store_true');p.add_argument('--loop',action='store_true');p.add_argument('--interval',type=int,default=300)
 a=p.parse_args();states=[s.strip().upper() for s in a.states.split(',')]
 if a.history:load_history(states)
 if not (a.once or a.loop or a.csv or a.url):p.print_help();return
 while True:
  try:
   if a.url:fetch_public_csv(a.url)
   if a.csv:ingest_csv(a.csv)
   calculate();print('snapshot',datetime.now(timezone.utc).isoformat(),flush=True)
  except Exception as e:
   with db() as c:log(c,'poll','error',str(e))
   print('poll error:',e,flush=True)
  if not a.loop:break
  time.sleep(a.interval)
if __name__=='__main__':main()
