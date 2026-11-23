# 06 — Alert Engine (Rule-Based System)

## What is the Alert Engine?

The alert engine is a **deterministic rule evaluation system** — not ML, not probabilistic.  
It reads current weather values, compares them to fixed thresholds, and emits structured alert objects.

**File:** `src/weather_app/alerts.py`  
**Entry point:** `build_alerts(weather: dict) → list[dict]`

---

## Alert Object Schema

Every alert returned is a dict with exactly 4 keys:

```python
{
    "level": "high" | "moderate" | "info",
    "kind":  "rain" | "heat" | "humidity" | "wind" | "air_quality" | "clear",
    "title": str,      # Short human-readable title
    "message": str     # Explanation with the actual measured value
}
```

---

## Threshold Table (All Rules)

| Category | Input Field | Moderate (≥) | High (≥) | Moderate Message | High Message |
|---------|------------|-------------|---------|-----------------|--------------|
| **Rain probability** | `precipitation_probability` | 40% | 70% | "Rain possible" | "High chance of rain" |
| **Rain amount** | `precipitation_mm` | — | 20 mm | — | "Heavy precipitation" |
| **Temperature** | `temperature_c` | 35°C | 40°C | "High temperature" | "Extreme heat" |
| **Humidity** | `relative_humidity_percent` | 85% | 95% | "High humidity" | "Very high humidity" |
| **Wind** | `wind_speed_kmh` | 40 km/h | 60 km/h | "Strong wind" | "Very strong wind" |
| **Air Quality** | `us_aqi` | 101 | 151 | "Elevated AQI" | "Unhealthy air quality" |
| **Storm (WMO)** | `weather_code` | — | 95, 96, 99 | — | "Thunderstorm reported" |

> **Rule 7 (Storm):** Only fires when Open-Meteo explicitly reports WMO weather codes 95 (thunderstorm), 96 (thunderstorm + hail), or 99 (severe thunderstorm + hail). Rain or wind alone is never classified as a storm.

Thresholds are exposed through the `GET /thresholds` API endpoint.

---

## Evaluation Logic (Pseudocode)

```python
def build_alerts(weather):
    alerts = []

    # Rule 1: Rain probability
    rain = weather.get("precipitation_probability")
    if rain >= 70: alerts.append(HIGH, "rain", ...)
    elif rain >= 40: alerts.append(MODERATE, "rain", ...)

    # Rule 2: Rain amount
    rain_mm = weather.get("precipitation_mm")
    if rain_mm >= 20: alerts.append(HIGH, "rain", ...)

    # Rule 3: Temperature
    temp = weather.get("temperature_c")
    if temp >= 40: alerts.append(HIGH, "heat", ...)
    elif temp >= 35: alerts.append(MODERATE, "heat", ...)

    # Rule 4: Humidity
    humidity = weather.get("relative_humidity_percent")
    if humidity >= 95: alerts.append(HIGH, "humidity", ...)
    elif humidity >= 85: alerts.append(MODERATE, "humidity", ...)

    # Rule 5: Wind
    wind = weather.get("wind_speed_kmh")
    if wind >= 60: alerts.append(HIGH, "wind", ...)
    elif wind >= 40: alerts.append(MODERATE, "wind", ...)

    # Rule 6: AQI
    aqi = weather.get("us_aqi")
    if aqi >= 151: alerts.append(HIGH, "air_quality", ...)
    elif aqi >= 101: alerts.append(MODERATE, "air_quality", ...)

    # Fallback
    if not alerts:
        alerts.append(INFO, "clear", "No elevated risks detected", ...)

    return alerts
```

---

## None-Safety

Every field access uses `weather.get(field)` which returns `None` if missing.  
All comparisons are guarded:
```python
if rain is not None and rain >= 70:
```
This means: missing data → no alert for that category (no crash).

---

## Multiple Alerts Per Request

A single request can trigger **multiple alerts simultaneously**.  
Example: New Delhi (simulation)
- `precipitation_probability = 42%` → moderate rain alert
- `us_aqi = 78` → no AQI alert (below 101)
- `relative_humidity_percent = 91%` → high humidity alert

Result: **2 alerts** returned.

---

## How Streamlit Renders Alerts

```python
for alert in alerts:
    if alert["level"] == "info":
        st.success(...)    # Green box
    elif alert["level"] == "high":
        st.error(...)      # Red box
    else:  # moderate
        st.warning(...)    # Yellow/orange box
```

---

## Limitations (Educational Thresholds)

> These thresholds are project defaults, **not official government warnings**.  
> Real weather agencies (IMD, NOAA, UK Met Office) use different, location-specific thresholds.  
> The dashboard shows this disclaimer: *"Follow your local weather service for official warnings."*

---

> **Updated:** 2026-11-24
