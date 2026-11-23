# 12 — Streamlit Dashboard Internals

## Overview

The dashboard is a single-file Streamlit app that talks to the FastAPI backend over HTTP and renders weather data as charts, metrics, and alerts.

**File:** `src/dashboard/streamlit_app.py`  
**Default port:** 8501

---

## Page Configuration

```python
st.set_page_config(page_title="Weather & Risk Monitor", page_icon="🌦️", layout="wide")
```
- `layout="wide"` → uses full browser width for multi-column charts

---

## Configuration & Backend URL

```python
api_url = os.getenv("WEATHER_API_URL", "http://localhost:8000")
```
- Reads `WEATHER_API_URL` from `.env` file (via `load_dotenv()`)
- Defaults to `http://localhost:8000` if not set

---

## Sidebar Inputs

| Widget | Variable | Default | Purpose |
|--------|---------|---------|---------|
| `st.text_input` | `city` | `"New Delhi"` | City to fetch |
| `st.toggle` | `simulation` | `False` | Enable offline demo mode |
| `st.button` | `refresh` | — | Triggers a new API call |

---

## Session State

```python
st.session_state.weather_result
```

**Why session state?**  
Streamlit re-runs the entire script on **every user interaction** (button clicks, toggles, text changes).  
Session state persists the last API response so the page doesn't go blank between interactions.

**Cache invalidation:**
- If `refresh` button is clicked → new API call, state updated
- If page is first loaded (key not in state) → API call triggered automatically

---

## Data Fetching

```python
response = requests.get(
    f"{api_url}/weather",
    params={"city": city, "simulation": simulation},
    timeout=25
)
```

- Uses synchronous `requests` (not async)
- `timeout=25` seconds
- Error handling: `st.error(...)` + `st.stop()` on failure

---

## UI Components (Top to Bottom)

### 1. Source Caption
```python
st.caption(f"Data source: **{source}** · Updated: {fetched_at} · Time zone: {timezone}")
```

### 2. CSV Download Button
```python
if st.button("Generate CSV report"):
    report_response = requests.get(f"{api_url}/weather/report", ...)
    st.download_button("Download weather report", data=..., file_name=..., mime="text/csv")
```

### 3. Metric Cards (6 columns)
```python
cols = st.columns(6)
metrics = [
    ("Temperature",   temperature_c,              "°C"),
    ("Feels like",    apparent_temperature_c,     "°C"),
    ("Humidity",      relative_humidity_percent,  "%"),
    ("Rain chance",   precipitation_probability,  "%"),
    ("Wind",          wind_speed_kmh,             "km/h"),
    ("US AQI",        us_aqi,                     ""),
]
for col, (label, value, suffix) in zip(cols, metrics):
    col.metric(label, f"{value}{suffix}" if value is not None else "Unavailable")
```

### 4. Alert Boxes
```python
for alert in alerts:
    if alert["level"] == "info":    st.success(...)
    elif alert["level"] == "high":  st.error(...)
    else:                           st.warning(...)
```

### 5. Charts (Two Columns)

**Left column:**
- `px.line` — 7-day temperature max/min (°C)
- `px.bar` — 7-day precipitation probability (%)

**Right column:**
- `px.line` — 24-hour temperature (°C)
- `px.scatter_geo` — World map with city pin

### 6. Data Expander
```python
with st.expander("View forecast data"):
    st.dataframe(pd.DataFrame(data["daily"]))
```

---

## Plotly Chart Details

| Chart | Type | X-axis | Y-axis | Library Call |
|-------|------|--------|--------|-------------|
| 7-day temp | Line | `date` | temp_max_c + temp_min_c | `px.line(..., y=[...])` |
| 7-day rain | Bar | `date` | `precipitation_probability_max` | `px.bar(...)` |
| 24h temp | Line | `time` | `temperature_c` | `px.line(...)` |
| Geo map | Scatter geo | Longitude | Latitude | `px.scatter_geo(...)` |

---

## Geo Map Configuration

```python
fig_map.update_geos(
    showland=True,     landcolor="#edf2f4",
    showcountries=True, countrycolor="#b8c4cc",
    showocean=True,    oceancolor="#e9f3f8"
)
```
City marker: red circle, size 14.

---

> **Updated:** 2026-11-24
