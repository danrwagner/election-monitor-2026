# 2026 County Election Monitor (public-source MVP)

This is a runnable, **not yet live-connected**, election-return monitor. It imports a standardized county CSV, stores timestamped snapshots every five minutes, compares completed counties with 2024 presidential and 2022 Senate results, and displays observed returns. **It does not predict winners, Senate seats, or final vote shares.**

## Run

```bash
python -m pip install -r requirements.txt
python monitor.py --history --states SC,GA,NC,TX  # historical public API, network needed
python monitor.py --csv example_feed.csv --once    # TEST DATA ONLY
streamlit run dashboard.py
```

For a verified, publicly authorized HTTPS CSV endpoint with exactly the expected columns:

```bash
python monitor.py --url 'https://YOUR-AUTHORIZED-COUNTY-CSV.csv' --loop --interval 300
```

For manual ingestion, export a county CSV from an official election office and map the columns to `state,county,race,dem,rep,total,complete,source`; use `python monitor.py --csv file.csv --once`. `complete` must mean officially confirmed complete, not just 100% precincts reporting on an aggregator. Partial counties are included in observed totals but excluded from historical swing calculations. All races default to a Senate designation if `race` is blank. Independent candidates and fusion voting require a dedicated mapping before use.

## Public-source findings (Nov. 3, 2026)

- Historical county returns: https://www.pollingforecast.com/us/data documents a free no-key API at `/api/us/counties?office=P&year=2024&state=SC`, and Senate county data for 2022/2024. API response column names need live validation; the loader logs schema errors rather than silently fabricating data.
- AP results API: https://api.ap.org/v3/elections/xplor requires an API key and is not a public no-key solution.
- NBC/CNN/Politico public election pages are **not** verified as stable, permitted five-minute county-level machine-readable endpoints.
- A national public county-level feed for 2026 has **not been confirmed**. Do not treat this prototype as a live election monitor until one is connected and checked.

## Accuracy and limitations

- No synthetic returns are used except the explicitly labeled example row.
- No estimate of unreported votes is produced. Historical swing is an observed-completed-county statistic, not a statewide projection.
- 2022 Senate contests are not held in every state, so some comparison columns will be empty. 2024 presidential is the common baseline.
- Cross-cycle candidate, turnout, uncontested race, county name and third-party differences can bias comparisons.
- National observed two-party vote share is highly sensitive to which states/counties report first. The dashboard labels it as an observed aggregate only.
- The application does not have hosting or a scheduled job configured. Keep the polling process running to receive five-minute updates.
- Respect source terms, rate limits and election authority attribution.

## Next steps to make it live

1. Confirm one or more authorized public county-level CSV/JSON feeds with 2026 Senate results, stable IDs, completion flags, and timestamps.
2. Build a source-specific adapter and validate against official state totals; never infer complete status from missing updates.
3. Load history across the Senate states, validate API schema, and reconcile counties/FIPS.
4. Deploy the dashboard and poller on a server with network access and persistence.
5. Backtest any proposed statewide vote-share extrapolation on historical election-night sequences before displaying it.
