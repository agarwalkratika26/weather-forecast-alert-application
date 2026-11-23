# 13 — Validation Checklist

> This file tells you exactly **how to verify** that each part of the implementation is correct.
> Run these checks after each implementation phase.

---

## ✅ Phase 0 — Environment Setup

| Check | Command / Action | Expected Result |
|-------|-----------------|----------------|
| Python installed | `python --version` | `3.11+` |
| Virtual env active | `pip list` | Shows project packages |
| Dependencies installed | `pip install -r requirements.txt` | No errors |
| Local environment settings | Optional: copy `.env.example` to `.env` | `WEATHER_API_URL` defaults to `http://localhost:8000`; no API key is needed for Open-Meteo |

---

## ✅ Phase 1 — Backend Starts

| Check | Command | Expected Result |
|-------|---------|----------------|
| Uvicorn starts | `uvicorn main:app --reload` | `Application startup complete` in logs |
| Health endpoint | `curl http://localhost:8000/health` | `{"status":"ok","service":"Weather Forecast & Alert API","version":"1.0.0"}` |
| OpenAPI docs load | Open browser → `http://localhost:8000/docs` | Swagger UI shows 5 endpoints |
| Locations endpoint | `curl http://localhost:8000/locations` | Returns list of 5 cities |

---

## ✅ Phase 2 — Simulation Mode (Offline)

| Check | Command | Expected Result |
|-------|---------|----------------|
| Simulation works | `curl "http://localhost:8000/weather?city=Tokyo&simulation=true"` | JSON with `"source":"simulation"`, Tokyo data |
| Fallback works | `curl "http://localhost:8000/weather?city=UnknownCity&simulation=true"` | Returns "New Delhi" data with source="simulation" |
| All 5 cities | Test each of: New Delhi, London, Tokyo, New York, Sydney | Each returns different base temperature/humidity |
| Alert generation | Check Tokyo response | Should have `"level":"high","kind":"humidity"` (humidity=96%) |
| Alert generation | Check New York response | Should have `"level":"high","kind":"rain"` (rain=76%) |
| Alert generation | Check Sydney response | Should have `"level":"info","kind":"clear"` (all below threshold) |
| Hourly count | Check `hourly` array length | 24 items |
| Daily count | Check `daily` array length | 7 items |

---

## ✅ Phase 3 — Live Mode (Needs Internet)

| Check | Command | Expected Result |
|-------|---------|----------------|
| Known city | `curl "http://localhost:8000/weather?city=Mumbai"` | JSON with `"source":"Open-Meteo"`, real coordinates |
| Unknown city | `curl "http://localhost:8000/weather?city=xyzzznotacity"` | `404` with a helpful error message |
| AQI present | Check Mumbai response | `current.us_aqi` is a number or null (not crashing) |
| Geocoding match | Check `location.name` in response | Matches expected city (or nearest match) |
| Cache works | Call the same city twice and compare results/logs | Second response uses the cached response; do not rely on a fixed millisecond target |

---

## ✅ Phase 4 — Alert Engine

| Check | Method | Expected Result |
|-------|--------|----------------|
| All 7 rules fire | Manually call `build_alerts()` with crafted dicts | Rain chance, rain amount, heat, humidity, wind, AQI, and storm code each trigger the expected alert |
| None-safety | Pass dict with missing fields | No KeyError or TypeError |
| Fallback fires | Pass all values below threshold and omit the storm code | Exactly 1 alert, level="info", kind="clear" |
| Multiple alerts | Pass high rain + high temp | Returns 2 alerts |
| Level accuracy | rain=70 → | level="high" (not moderate) |
| Level accuracy | rain=40 → | level="moderate" |
| Level accuracy | rain=39 → | No rain alert |

**Manual test code:**
```python
from src.weather_app.alerts import build_alerts

# Test: High rain + moderate temp
alerts = build_alerts({"precipitation_probability": 75, "temperature_c": 36})
assert any(a["level"]=="high" and a["kind"]=="rain" for a in alerts)
assert any(a["level"]=="moderate" and a["kind"]=="heat" for a in alerts)

# Test: None safety
alerts = build_alerts({})
assert len(alerts) == 1 and alerts[0]["kind"] == "clear"

print("All alert tests passed!")
```

---

## ✅ Phase 5 — CSV Report

| Check | Command | Expected Result |
|-------|---------|----------------|
| File created | `curl "http://localhost:8000/weather/report?city=London&simulation=true" -o test.csv` | File downloaded |
| File saved | Check `outputs/` folder | `weather_report_London_*.csv` exists |
| CSV header | Open CSV | First row: `record_type,location,timestamp,metric,value,unit,notes` |
| Sections present | Grep CSV | Has rows for `report_info`, `current`, `hourly`, `daily`, `alert` |
| Excel compat | Open in Excel | No encoding errors, columns align |
| Unique timestamps | Download twice | Two different files (microsecond timestamp in name) |

---

## ✅ Phase 6 — Streamlit Dashboard

| Check | Action | Expected Result |
|-------|--------|----------------|
| Dashboard starts | `streamlit run src/dashboard/streamlit_app.py` | Opens on `http://localhost:8501` |
| Simulation loads | Toggle simulation ON → Click "Get weather" | 6 metric cards populate, no error |
| Alert colours | New York (rain=76%) | Red alert box visible |
| All 3 charts render | Check left+right columns | Line, bar, map all visible |
| Download button | Click "Generate CSV report" | Download button appears, file downloads |
| City change | Type "London" → Get weather | Data updates to London values |
| Error handling | Turn off API server → Click Get weather | Shows error message, doesn't crash |

---

## ✅ Phase 7 — Validation Logic

| Check | Expectation |
|-------|------------|
| Short city name | `GET /weather?city=X` → `422 Unprocessable Entity` |
| Long city name | `GET /weather?city=${'A'*101}` → `422` |
| Out-of-range latitude | `GET /weather?latitude=91` → `422` |
| Out-of-range longitude | `GET /weather?longitude=181` → `422` |
| Invalid simulation value | `GET /weather?simulation=banana` → `422` |

---

> **Updated:** 2026-11-24  
> **To be updated after each implementation session.**
