import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st
st.set_page_config(page_title='County election monitor',layout='wide')
st.title('2026 County Election Monitor')
st.caption('Observed returns and historical comparisons only. No race calls or projected winners. Data are not independently verified.')
from monitor import db
with db() as connection:
    pass
import requests

@st.cache_data(ttl=3600, show_spinner="Loading verified historical county returns...")
def get_historical(state, year, office):
    response=requests.get(
        "https://www.pollingforecast.com/api/us/counties",
        params={"office":office,"year":year,"state":state},
        timeout=25,
        headers={"User-Agent":"ElectionMonitor2026/0.3 historical research"})
    response.raise_for_status()
    payload=response.json()
    rows=payload.get("rows",[])
    expected={"fips","county","dem_votes","rep_votes","total_votes"}
    if not isinstance(rows,list) or not rows or not expected.issubset(rows[0]):
        raise ValueError("Historical feed has an unexpected format")
    data=pd.DataFrame(rows)
    data["dem_two_party_share"]=100*data["dem_votes"]/(data["dem_votes"]+data["rep_votes"]).replace(0,float("nan"))
    return data,payload.get("attribution","Polling Forecast"),payload.get("asOf","")


@st.cache_data(ttl=300, show_spinner="Checking official state feeds via Open America...")
def open_america_results(office):
    url="https://openamerica.io/elections/results.json"
    response=requests.get(url,params={"year":2026,"office":office},timeout=25,
                          headers={"User-Agent":"ElectionMonitor2026/0.4","Accept":"application/json"})
    response.raise_for_status()
    payload=response.json()
    if not isinstance(payload,dict) or payload.get("year")!=2026 or str(payload.get("office","")).lower()!=office.lower():
        raise ValueError("Unexpected year, office, or response format")
    return payload

st.subheader("Michigan 2026: Senate and governor")
st.caption("Live candidate totals from Polling Desk (citing civicAPI). These are reported votes, not our own projections or certified totals.")
@st.cache_data(ttl=300,show_spinner="Loading Michigan election returns...")
def michigan_2026():
    import io
    response=requests.get("https://polling-desk.com/data/mi/results.csv",timeout=20,
                          headers={"User-Agent":"ElectionMonitor2026/0.5","Accept":"text/csv"})
    response.raise_for_status()
    if "html" in response.headers.get("Content-Type","").lower():
        raise ValueError("CSV source returned HTML")
    frame=pd.read_csv(io.BytesIO(response.content))
    if frame.empty:
        raise ValueError("No candidate results in source")
    return frame
try:
    mi=michigan_2026()
    st.caption("Source: Polling Desk / civicAPI | Refreshes on dashboard approximately every 5 minutes.")
    st.dataframe(mi,hide_index=True,use_container_width=True)
    st.caption("County-level Michigan 2026 candidate results have not yet been verified; this is the statewide race-results feed.")
except Exception as exc:
    st.warning(f"Michigan candidate results unavailable from source: {exc}")
st.divider()

st.subheader("2026 statewide reported results")
st.caption("Official state-election-office counts via Open America. Partial coverage, no county detail, no race calls or projections.")
office_2026=st.selectbox("2026 office",["Senate","House","Governor"])
try:
    live=open_america_results(office_2026)
    st.caption(f"Source: https://openamerica.io/elections/api/ | As of: {live.get('as_of') or 'No state reporting timestamp'}")
    if live.get("stale"):
        st.warning("Feed is marked stale by its provider.")
    if not live.get("counting"):
        st.info("No reported votes in the currently available provider feed.")
    races=live.get("races",{})
    if isinstance(races,dict):
        st.metric("Races present in source feed",len(races))
        if races:
            st.json(races,expanded=False)
    elif isinstance(races,list):
        st.metric("Races present in source feed",len(races))
        if races:
            st.dataframe(pd.json_normalize(races),hide_index=True,use_container_width=True)
    else:
        st.info("Provider has not supplied a compatible race collection.")
except Exception as exc:
    st.warning(f"2026 statewide feed is currently unavailable: {exc}")
st.divider()

st.subheader("Historical county election results")
st.caption("Verified historical results only. These are NOT 2026 live returns.")
historical_state=st.selectbox("Historical state",["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"])
historical_office=st.selectbox("Historical election",["2024 President","2022 Senate"])
year,office=(2024,"P") if historical_office=="2024 President" else (2022,"S")
try:
    hist,attribution,asof=get_historical(historical_state,year,office)
    st.metric("Counties with historical returns",len(hist))
    st.dataframe(hist[["fips","county","dem_votes","rep_votes","total_votes","dem_two_party_share"]].sort_values("county"),hide_index=True,use_container_width=True)
    st.caption(f"Source: {attribution}. As of: {asof}. Row-specific licenses apply.")
except Exception as exc:
    st.warning(f"Historical results not available for this selection: {exc}")
st.divider()

p=Path(__file__).parent/'monitor.sqlite'
with sqlite3.connect(p) as c:
 snaps=pd.read_sql_query('SELECT * FROM snapshots ORDER BY observed_at',c)
 current=pd.read_sql_query('SELECT * FROM current',c)
 logs=pd.read_sql_query('SELECT * FROM ingest_log ORDER BY at DESC LIMIT 15',c)
if snaps.empty:
    st.info('Dashboard deployed and database initialized. No verified live 2026 county results have been ingested yet.')
    st.warning('This app is not yet connected to civicAPI or a scheduled poller. Do not interpret the empty dashboard as zero reported votes.')
    with st.expander('Ingestion diagnostics'):
        st.dataframe(logs,hide_index=True,use_container_width=True)
    st.stop()
latest=snaps.sort_values('observed_at').groupby(['state','race']).tail(1).copy()
latest['two_party_dem_share']=100*latest.observed_dem/(latest.observed_dem+latest.observed_rep).replace(0,float('nan'))
st.subheader('National observed aggregate')
a,b,c=st.columns(3)
a.metric('D share of reported two-party votes',f"{100*latest.observed_dem.sum()/(latest.observed_dem.sum()+latest.observed_rep.sum()):.1f}%" if latest.observed_dem.sum()+latest.observed_rep.sum()>0 else 'N/A')
b.metric('Votes reported',f"{latest.observed_total.sum():,.0f}")
c.metric('Counties marked complete',f"{latest.counties_complete.sum():,.0f}")
st.warning('National aggregate is only from reporting counties and is not an estimate of final national vote share. Reporting order creates strong selection bias.')
st.subheader('State reporting')
st.dataframe(latest[['state','race','counties_reporting','counties_complete','observed_total','two_party_dem_share','swing_2024_pp','swing_2022_pp','observed_at','source']].sort_values('state'),hide_index=True,use_container_width=True)
state=st.selectbox('Inspect state',sorted(current.state.unique()))
st.subheader(f'{state}: county returns')
st.dataframe(current[current.state==state].sort_values('county'),hide_index=True,use_container_width=True)
st.subheader('Five-minute snapshot history')
chart=snaps[snaps.state==state].copy()
chart['dem_share']=100*chart.observed_dem/(chart.observed_dem+chart.observed_rep).replace(0,float('nan'))
st.line_chart(chart.set_index('observed_at')[['dem_share','swing_2024_pp']])
with st.expander('Ingestion diagnostics'):st.dataframe(logs,hide_index=True,use_container_width=True)
