# 📚 Technical Documentation Index
## Weather Forecast & Alert Application

> This folder is the **single source of truth** for all technical details about this project.
> Every file is kept up-to-date as implementation progresses.

---

## 📂 File Map

| File | What it covers |
|------|---------------|
| [00_INDEX.md](00_INDEX.md) | ← You are here. Master index of all docs. |
| [01_PROJECT_OVERVIEW.md](01_PROJECT_OVERVIEW.md) | High-level purpose, goals, scope, and what the project is NOT |
| [02_ARCHITECTURE.md](02_ARCHITECTURE.md) | System architecture, component diagram, layer responsibilities |
| [03_DATA_FLOW.md](03_DATA_FLOW.md) | End-to-end data flow: user → API → external services → response |
| [04_MODULES.md](04_MODULES.md) | Every Python module explained: purpose, inputs, outputs, key functions |
| [05_DATASET_AND_DATA_SOURCES.md](05_DATASET_AND_DATA_SOURCES.md) | External APIs used, fields fetched, demo data details |
| [06_ALERT_ENGINE.md](06_ALERT_ENGINE.md) | How the rule-based alert system works, all thresholds documented |
| [07_API_REFERENCE.md](07_API_REFERENCE.md) | All FastAPI endpoints, request params, response schemas |
| [08_TECH_STACK.md](08_TECH_STACK.md) | Libraries, versions, why each was chosen |
| [09_SIMULATION_MODE.md](09_SIMULATION_MODE.md) | How offline demo/simulation mode works internally |
| [10_CACHING.md](10_CACHING.md) | In-memory cache strategy, TTL, invalidation rules |
| [11_CSV_REPORT.md](11_CSV_REPORT.md) | Report generation logic, CSV schema, file naming |
| [12_DASHBOARD.md](12_DASHBOARD.md) | Streamlit dashboard internals, state management, charts |
| [13_VALIDATION_CHECKLIST.md](13_VALIDATION_CHECKLIST.md) | ✅ How to validate every piece of the implementation |
| [14_EXECUTION_LOG.md](14_EXECUTION_LOG.md) | Running log of what has been implemented each session |

---

## 🗂️ Folder Structure (Project Root)

```
Weather Forecast & Alert Application/
│
├── main.py                          # ASGI entry point → uvicorn main:app
│
├── src/
│   ├── __init__.py
│   ├── weather_app/
│   │   ├── __init__.py
│   │   ├── config.py               # Settings (Pydantic), env vars
│   │   ├── service.py              # Business logic: geocode, fetch, cache
│   │   ├── alerts.py               # Rule-based alert engine
│   │   └── main.py                 # FastAPI app + routes
│   └── dashboard/
│       └── streamlit_app.py        # Streamlit UI
│
├── data/                           # (reserved for future stored data)
├── outputs/                        # Auto-generated CSV weather reports
├── reports/                        # (reserved for future report storage)
├── images/                         # Screenshots / UI images
├── assets/screenshots/             # Screenshot storage
│
├── docs/                           # Existing project-level docs
├── TECHNICAL_DOCS/                 # ← THIS FOLDER (deep technical reference)
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

> **Last Updated:** 2026-11-24  
> **Status:** 🟡 Project not yet executed — documentation reflects code as written, pre-run.
