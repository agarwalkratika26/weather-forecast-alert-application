# Project architecture

This document describes the requested end-to-end design and maps it to the current student project. The target design includes configurable thresholds, humidity/storm analysis, and saved reports; some of those are future extensions in the current code.

## Text-based architecture diagram

```text
┌─────────────────────────────── User / Streamlit Dashboard ───────────────────────────────┐
│ Inputs: city name · alert thresholds · provider/API-key configuration (if required)       │
└──────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │ HTTP request
                                       ▼
┌────────────────────────────────── FastAPI ───────────────────────────────────────────────┐
│ 1. Validate city, coordinates, and requested threshold configuration                     │
│ 2. Weather provider adapter                                                               │
│      ├─ Geocoding request: city → coordinates                                              │
│      ├─ Forecast request: current and forecast observations                               │
│      └─ Optional air-quality request: AQI                                                 │
│ 3. Parse JSON and normalize provider fields                                                │
│ 4. Analyze temperature · humidity · rain · storm indicators · wind · AQI                  │
│ 5. Generate alert records with level, category, message, and observation time             │
│ 6. Build a report snapshot                                                               │
└───────────────────────┬─────────────────────────────────┬────────────────────────────────┘
                        │                                 │
                        ▼                                 ▼
           ┌──────────────────────┐          ┌────────────────────────────┐
           │ Weather provider API │          │ Report store (target)      │
           │ JSON over HTTPS      │          │ SQLite / PostgreSQL        │
           └──────────────────────┘          └──────────────┬─────────────┘
                                                           │ report ID / history
                                                           ▼
┌─────────────────────────────── API response ─────────────────────────────────────────────┐
│ Current weather · forecast summary · alert messages · saved report confirmation/history  │
└──────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │
                                       ▼
┌────────────────────────────── Streamlit Dashboard ──────────────────────────────────────┐
│ Metrics · charts · map · risk notifications · report view/download                       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Inputs

- **City name:** The user enters a location. A geocoding request resolves it to coordinates so forecast services can retrieve data for the right place.
- **Weather API key:** Store a provider key in an environment variable or secrets manager when the chosen provider requires one. Never send a secret from the browser or commit it to Git. Open-Meteo is used by the current app without a key, so this input is not required there.
- **Alert thresholds:** User or administrator settings for conditions such as maximum temperature, humidity, rain probability, precipitation amount, wind speed, and AQI. Validate their ranges and units before analysis. The current app uses fixed example thresholds in Python code.

## Processing stages

1. **Validate request:** Check that the city is present, coordinates are in range if supplied, and threshold values use supported units and ranges.
2. **Fetch provider data:** Resolve the city, then request current conditions and forecast data. Request AQI separately when the provider supports it. Apply request timeouts and handle provider errors clearly.
3. **Parse and normalize JSON:** Convert provider-specific names and units into one internal structure. Preserve timestamps and location/time-zone information. Represent unavailable measurements as `null` instead of inventing values.
4. **Analyze measurements:** Compare temperature and humidity with configured thresholds. Check rain probability and expected precipitation. Detect a storm only if the data provider supplies suitable weather codes or storm indicators; rain or wind alone is not proof of a storm. Wind and AQI can also be assessed.
5. **Generate alerts:** Each triggered rule creates an alert with a type, severity, explanatory message, time, and relevant measured value. A no-risk result can return an empty alert list or an explicit informational message.
6. **Build and save a report:** Assemble a time-stamped snapshot containing the location, source, current conditions, forecast summary, thresholds used, and generated alerts. Persist it using a database if history is required.
7. **Return and display:** Return JSON through FastAPI. The dashboard shows current weather, forecast, alerts, and report details, with an option to open or download a saved report.

## Outputs

- **Current weather:** Measurements such as temperature, feels-like temperature, humidity, wind, precipitation, and optional AQI.
- **Forecast summary:** Hourly and daily values with local timestamps.
- **Alert message:** Human-readable category, severity, reason, and value that crossed a threshold.
- **Saved report:** A time-stamped, reproducible record of the location, source data summary, thresholds, and alerts. A report ID can link to it later.

## Data flow explanation

The user submits a city and alert preferences in the dashboard. The UI sends those values to FastAPI. The backend validates the request and resolves the city to latitude/longitude. It calls the weather provider using server-side credentials when the provider requires a key. Provider JSON is parsed into a consistent internal format, then the analysis layer checks each available measurement against the selected thresholds. The resulting alerts and forecast summary are assembled into a report snapshot and saved to a database. FastAPI returns the weather response and report status; the dashboard presents the results and can retrieve saved history.

If provider data is missing or a request fails, the backend should report the limitation instead of substituting fake live values. A separate, clearly labeled simulation mode can still be used for offline demonstrations.

## Current implementation versus target design

| Architecture item | Current project |
|---|---|
| City input and geocoding | Implemented with Open-Meteo Geocoding |
| API key | Not needed for the current Open-Meteo setup; no provider key field is implemented |
| Current weather and forecast | Implemented through FastAPI and Open-Meteo |
| Temperature, rain, humidity, wind, and AQI alert rules | Implemented with fixed educational thresholds |
| Humidity threshold alert | Implemented with example thresholds of 85% (moderate) and 95% (high) |
| Storm-specific alert | Implemented for provider-reported WMO thunderstorm codes 95, 96, and 99 |
| CSV report download | Implemented through `/weather/report`; a snapshot is saved under `outputs/` and returned as a download |
| Persistent report history | Not implemented; output files are local and there is no database/history endpoint |
| Dashboard | Implemented with Streamlit, charts, map, and alert notifications |

To reach the full target design, the next practical steps are to accept validated threshold settings and create a report model with SQLite persistence and a report-history endpoint.
