# 11 — CSV Report Generation

## Overview

The `/weather/report` endpoint fetches weather data and returns a structured CSV file as a download. A local copy is also saved to `outputs/`.

---

## File Naming Convention

```
weather_report_{safe_city}_{YYYYMMDD_HHMMSS_microseconds}.csv
```

**Example:** `weather_report_New_Delhi_20261124_010000_123456.csv`

**City name sanitisation:**
```python
safe_city = re.sub(r"[^A-Za-z0-9_-]+", "_", city_name).strip("_") or "weather"
```
- Spaces, special characters → replaced with `_`
- Leading/trailing underscores → stripped
- Empty result → falls back to `"weather"`

---

## Output Directory

```
Weather Forecast & Alert Application/
└── outputs/     ← Auto-created by save_csv_report() if it doesn't exist
    └── weather_report_*.csv
```

---

## CSV Schema

The CSV uses a **long (tidy) format** — one metric per row, all sections in one file.

**Header row:**
```
record_type, location, timestamp, metric, value, unit, notes
```

### Section 1: `report_info` rows

| record_type | location | timestamp | metric | value | unit | notes |
|------------|----------|-----------|--------|-------|------|-------|
| report_info | New Delhi | 2026-11-24T... | source | Open-Meteo | | |
| report_info | New Delhi | 2026-11-24T... | fetched_at | 2026-11-24T... | | |
| report_info | New Delhi | 2026-11-24T... | country | India | | |
| report_info | New Delhi | 2026-11-24T... | timezone | Asia/Kolkata | | |
| report_info | New Delhi | 2026-11-24T... | latitude | 28.6139 | | |
| report_info | New Delhi | 2026-11-24T... | longitude | 77.209 | | |
| report_info | New Delhi | 2026-11-24T... | simulation | no | | |

### Section 2: `current` rows

| record_type | location | timestamp | metric | value | unit | notes |
|------------|----------|-----------|--------|-------|------|-------|
| current | New Delhi | 2026-11-24T01:00 | temperature_c | 31.4 | °C | |
| current | New Delhi | 2026-11-24T01:00 | apparent_temperature_c | 32.4 | °C | |
| current | New Delhi | 2026-11-24T01:00 | relative_humidity_percent | 91 | % | |
| current | New Delhi | 2026-11-24T01:00 | wind_speed_kmh | 56 | km/h | |
| current | New Delhi | 2026-11-24T01:00 | us_aqi | 78 | US AQI | |

### Section 3: `hourly` rows

24 rows starting from the current observation hour. Each row:
```
hourly, {location}, {hour_time}, {metric_name}, {value}, {unit}, ""
```

### Section 4: `daily` rows

7 rows, one per day. Each row:
```
daily, {location}, {date}, {metric_name}, {value}, {unit}, ""
```

### Section 5: `alert` rows

One row per triggered alert:
```
alert, {location}, {fetched_at}, {kind}, {level}, {title}, {message}
```

---

## Encoding

**UTF-8 with BOM (`utf-8-sig`)** — ensures Microsoft Excel opens the file without encoding issues.

---

## Delivery to User

1. File is written to disk in `outputs/`
2. FastAPI returns `FileResponse(path, media_type="text/csv; charset=utf-8", filename=...)`
3. Streamlit shows `st.download_button(...)` → user browser downloads the file

---

> **Updated:** 2026-11-24
