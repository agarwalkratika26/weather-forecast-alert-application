# 09 — Simulation / Demo Mode

## What is Simulation Mode?

Simulation mode is an **explicit offline data source** that returns a fully formed weather response without making any external weather-provider HTTP calls. The local FastAPI server must still be running when the Streamlit dashboard uses this mode. It is useful when:
- The developer has no internet connection
- Open-Meteo is down or rate-limiting
- Testing the UI / alert engine without network dependency

---

## How to Activate

```
# API query param:
GET /weather?city=Tokyo&simulation=true

# Streamlit UI:
Toggle "Simulation mode (works offline)" → ON → Click "Get weather"
```

---

## Supported Cities in Simulation Mode

| City | Lat | Lon | Timezone | Rain % | Temp (°C) | Wind (km/h) | AQI | Humidity % |
|------|-----|-----|----------|--------|----------|------------|-----|-----------|
| New Delhi | 28.61 | 77.21 | Asia/Kolkata | 42 | 31.4 | 56 | 78 | 91 |
| London | 51.51 | -0.13 | Europe/London | 58 | 18.2 | 24 | 8 | 78 |
| Tokyo | 35.68 | 139.65 | Asia/Tokyo | 22 | 27.1 | 18 | 42 | 96 |
| New York | 40.71 | -74.01 | America/New_York | 76 | 24.0 | 34 | 22 | 70 |
| Sydney | -33.87 | 151.21 | Australia/Sydney | 12 | 21.7 | 17 | 11 | 60 |

**City not in this list?** → Falls back to "New Delhi" data, labelled with the city name in source.

---

## Data Generation Algorithm

The `_demo(city)` function uses modular arithmetic to generate variation:

### Hourly Data (24 entries, i = 0..23)

```python
temperature_c            = base_temp + (i % 5 - 2) * 1.2
                           # Pattern repeats every 5 hours; range: base ± 2.4°C
precipitation_probability = clamp(rain_chance + (i%4-1)*9, 0, 100)
                           # Pattern repeats every 4 hours; ±9% variation per step
precipitation_mm         = 2.4 if i % 3 == 0 else 0.0
                           # Rain every 3rd hour
```

### Daily Data (7 entries, i = 0..6)

```python
temperature_max_c              = base_temp + i * 0.4     # +0.4°C per day
temperature_min_c              = base_temp - 7 + i * 0.2 # +0.2°C per day
precipitation_probability_max  = clamp(rain + (i%3-1)*10, 0, 100)
precipitation_sum_mm           = i * 2.0                 # 0, 2, 4, 6... mm
```

### Current Snapshot

Taken directly from the base values in `DEMO_LOCATIONS`. No variation applied.

---

## Alerts in Simulation Mode

Alert engine **runs identically** in both live and simulation modes — `build_alerts()` is called on the generated current dict.

**Expected alerts per city:**

| City | Triggered Alerts |
|------|----------------|
| New Delhi | Moderate rain (42%), High humidity (91%), Wind moderate (56 km/h → actually high ≥60? No, 56 → moderate ≥40) |
| London | Moderate rain (58%) |
| Tokyo | High humidity (96%) |
| New York | **High** rain (76%) |
| Sydney | No elevated risks (all below thresholds) |

---

## Response Differences: Live vs Simulation

| Field | Live Mode | Simulation Mode |
|-------|----------|----------------|
| `source` | `"Open-Meteo"` | `"simulation"` |
| `location.country` | Actual country | `"Demo data"` |
| Hourly timestamps | Real ISO timestamps | `"2026-11-24T01:00+0h"` format |
| Daily dates | ISO date strings | `"Day 1"`, `"Day 2"`, ... |
| All other fields | Same schema | Same schema |

---

> **Updated:** 2026-11-24
