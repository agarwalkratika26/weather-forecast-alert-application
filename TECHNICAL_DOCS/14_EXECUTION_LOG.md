# 14 — Execution Log

> This file tracks what has been implemented, verified, and what is pending — updated every session.

---

## Session 5 — 2026-11-24 (GitHub-Ready Preparation & Local Commit)

**Status:** Clean local Git repository initialized on branch main.

**Actions & Observed Results:**
- Re-scanned entire repository for hardcoded credentials; confirmed zero secrets.
- Created local `.env` configuration file and verified exclusion via `.gitignore`.
- Rewrote root `README.md` to executive standard: zero emojis, zero em dashes, professional architecture diagrams, directory breakdown, full API route references, and linked `images/dashboard-overview.png`.
- Added `images/.gitkeep` to ensure directory tracking in Git.
- Initialized local repository (`git init -b main`).
- Staged all 42 files (`git add .`) and committed (`commit 554ae5f`).
- Confirmed `git status` shows clean working tree with `.env` and `.venv/` strictly untracked.

**Status:** ✅ Both servers running; runtime validation verified.

**Actions & Observed Results:**
- Virtual environment (`.venv`) created using Python 3.13.14.
- All packages from `requirements.txt` successfully installed (`FastAPI`, `Uvicorn`, `Streamlit`, `Plotly`, `Pandas`, `httpx`, `requests`, `pydantic`).
- Launched FastAPI backend daemon on `http://127.0.0.1:8000`. Verified `/health` returned `200 OK` (`status: "ok"`).
- Launched Streamlit dashboard daemon on `http://127.0.0.1:8501`. Verified HTML shell response.
- Executed smoke test for simulation: `GET /weather?city=Tokyo&simulation=true` returned `source: "simulation"` and proper data.
- Executed smoke test for live Open-Meteo: `GET /weather?city=London` returned `source: "Open-Meteo"`, resolved coordinates, and live current/forecast conditions.

**Status:** Implementation complete; runtime validation pending.

**Review findings and corrections:**
- Confirmed the five FastAPI routes (`/health`, `/locations`, `/thresholds`, `/weather`, `/weather/report`), seven alert rules, and 15 `TECHNICAL_DOCS` files are present in the workspace.
- Corrected live hourly extraction to begin at the current observation hour, so the current rain probability and “Next 24 Hours” chart use matching hours.
- Direct-coordinate queries pass `timezone="auto"`, allowing Open-Meteo to resolve and return the true local timezone.
- Added the WMO storm-code list (`[95, 96, 99]`) to the `/thresholds` response and made malformed storm-code values safe to ignore.
- Corrected the dashboard error hint and sidebar toggle to clarify that offline simulation still needs the local FastAPI backend running.
- Updated API reference, CSV report docs, and validation checklist expectations to match the current routes and response fields.

**Security & Environment Notice:**
- No real provider key appears in the reviewed workspace files; Git is not initialized, so there is no commit history to inspect.
- Runtime tests, provider calls, dashboard launch, and screenshot capture remain unverified because Python execution was unavailable in the sandbox environment.

---

## Session 1 — 2026-11-24 (Pre-Execution)

**Status:** 🟡 Documentation Phase Only

**What was done:**
- Explored full project structure
- Read all existing source files
- Created `TECHNICAL_DOCS/` folder with 15 documentation files

---

## Session 2 — 2026-11-24 (Full Implementation)

**Status:** ✅ Code Complete (Pending Runtime Validation)

### What was implemented

| Component | File | Changes |
|-----------|------|---------|
| **Config** | `src/weather_app/config.py` | Rewrote with Pydantic `Field()` validators, `default_factory` for env var, comprehensive docstrings |
| **Alert Engine** | `src/weather_app/alerts.py` | Complete rewrite: named threshold constants, `threshold_summary()` endpoint helper, WMO storm-code detection (rule 7), better None-safety guards, educational messaging in every alert |
| **Service Layer** | `src/weather_app/service.py` | Major refactor: extracted `_fetch_forecast()`, `_fetch_air_quality()`, `_extract_current_aqi()`, `_normalise_forecast()` as separate functions; granular error handling (Timeout vs HTTPStatus vs generic); `logging` module; cache key normalised to casefold; simulation never silently substitutes for live failure; CSV export with separate unit dicts per section |
| **FastAPI Routes** | `src/weather_app/main.py` | Added `GET /thresholds` endpoint; shared query param objects with descriptions; structured OpenAPI docstrings; logging on failures |
| **Streamlit Dashboard** | `src/dashboard/streamlit_app.py` | Enhanced error handling (ConnectionError, Timeout, HTTPError with detail extraction); emoji metric labels; tabbed raw data view (Daily/Hourly tabs); simulation city list in sidebar; source banner label; API docs link; footer with attribution |
| **Root entry** | `main.py` | Cleaned up with docstring |
| **Dependencies** | `requirements.txt` | Added inline comments explaining each library |
| **Env template** | `.env.example` | Added explanatory header about committing |
| **Git ignore** | `.gitignore` | Added `env/`, `*.egg-info/`, `*.log`, `dist/`, `build/`, `Thumbs.db` |

### Key improvements over original code

1. **Granular error types** — `TimeoutException` vs `HTTPStatusError` vs generic `HTTPError` (was: single `HTTPError` catch)
2. **Storm detection** — WMO codes 95/96/99 trigger a thunderstorm alert with explicit disclaimer (was: no storm detection)
3. **Normalisation layer** — `_normalise_forecast()` maps provider field names to internal schema (was: inline in `get_weather`)
4. **AQI extraction** — `_extract_current_aqi()` matches the current hour index (was: inline logic)
5. **Cache key normalisation** — `casefold()` prevents duplicate cache entries for "london" vs "London"
6. **Threshold constants** — Named module-level constants with units (was: magic numbers inline)
7. **`/thresholds` endpoint** — Exposes all alert thresholds for transparency
8. **Dashboard error UX** — Shows specific error messages (connection refused, timeout, HTTP error detail) with recovery tips (was: generic error string)
9. **Dashboard tabs** — Raw data view has Daily / Hourly tabs (was: single DataFrame)
10. **Explicit never-fallback guarantee** — Code and docstrings guarantee simulation never replaces failed live calls

### What was validated

| Check | Method | Result |
|-------|--------|--------|
| All 6 .py files exist | `Get-ChildItem` | ✅ Confirmed |
| Bracket/paren/brace balance | PowerShell char counting | ✅ All 6 files balanced |
| service.py completeness | String search for all function names | ✅ All 6 key functions present |
| File inventory complete | Directory listing | ✅ 7 src files + 15 TECHNICAL_DOCS |

### What could NOT be validated (environment limitation)

| Check | Reason |
|-------|--------|
| `pip install -r requirements.txt` | Python not available in sandbox (Windows Store stub) |
| `uvicorn main:app` starts | No Python runtime |
| `/health` endpoint responds | No Python runtime |
| Simulation mode returns correct data | No Python runtime |
| Live mode fetches real data | No Python runtime + no network in sandbox |
| Alert engine returns expected alerts | No Python runtime |
| CSV report generates correctly | No Python runtime |
| Streamlit dashboard renders | No Python runtime |
| Dashboard screenshot capture | No Python runtime |

### What the student must do next

1. Create venv and install dependencies
2. Run the backend: `py -m uvicorn main:app --reload`
3. Test `/health`, `/locations`, `/thresholds` endpoints
4. Test simulation: `/weather?city=Tokyo&simulation=true`
5. Test live (with internet): `/weather?city=Mumbai`
6. Run Streamlit: `py -m streamlit run src/dashboard/streamlit_app.py`
7. Verify all dashboard components render
8. Capture dashboard screenshot → save to `images/dashboard-overview.png`
9. Run validation checklist from `13_VALIDATION_CHECKLIST.md`
10. Push to GitHub

---
