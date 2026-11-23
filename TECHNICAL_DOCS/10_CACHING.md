# 10 — Caching

## Overview

The backend uses a **simple in-memory TTL (Time-To-Live) cache** to avoid redundant API calls.

---

## Cache Implementation

**Location:** `src/weather_app/service.py`

```python
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
```

| Part | Type | Meaning |
|------|------|---------|
| Key | `str` | `f"{city}|{latitude}|{longitude}"` |
| Value[0] | `float` | `time.time()` when it was stored |
| Value[1] | `dict` | The full weather response dict |

---

## Cache Key Design

```python
key = f"{city}|{latitude}|{longitude}"
```

**Examples:**
- `"New Delhi|None|None"` — city-only lookup
- `"Mumbai|19.076|72.878"` — with explicit coordinates

This means:
- Same city name + same coordinates → cache hit
- Different city → different key → fresh fetch
- If user sends `latitude=19.076` for the first time and later sends `latitude=None`, these are **different cache keys** (different entries)

---

## TTL (Time-To-Live)

**Configured in:** `config.py` → `settings.cache_ttl_seconds = 600`  
**Default:** **600 seconds (10 minutes)**

**Cache hit logic:**
```python
if key in _cache:
    cached_time, cached_data = _cache[key]
    if time.time() - cached_time < settings.cache_ttl_seconds:
        return cached_data  # ← served from cache
# else: re-fetch from API
```

---

## Cache Characteristics

| Property | Detail |
|----------|--------|
| **Scope** | Process-level (in-memory) |
| **Persistence** | None — lost on server restart |
| **Thread safety** | Not explicitly locked (single-threaded asyncio event loop handles serialisation) |
| **Invalidation** | TTL only — no explicit invalidation |
| **Max size** | Unbounded (no eviction — suitable for small-scale project) |

---

## Cache Bypass

**Simulation mode does NOT use the cache.**  
When `simulation=True`, `_demo()` is called directly and no cache read/write occurs.

---

## Cache in Action (Timeline)

```
T=0:00  User requests "Tokyo"
        → Cache MISS → Fetch from Open-Meteo (~1–2s)
        → Store in cache with timestamp T=0:00

T=0:05  User requests "Tokyo" again
        → Cache HIT (age=5s < 600s) → Return instantly (<1ms)

T=10:01 User requests "Tokyo"
        → Cache HIT (age=601s > 600s) → Cache EXPIRED
        → Fetch from Open-Meteo again → Store new entry

T=10:02 User requests "London"
        → Different key → Cache MISS → Fetch London data
```

---

## Future Improvements

- **Redis cache** — shared across multiple workers/restarts
- **Cache eviction** — LRU or max-size limit
- **User-triggered refresh** — `force_refresh=true` query param
- **Cache headers** — expose `X-Cache-Hit: true/false` in API response

---

> **Updated:** 2026-11-24
