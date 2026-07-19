"""
Core API Mock — a small fictional "internal company backend" for MCP development.

It is intentionally DIVERSE so that MCP tools built on top of it are interesting to test:
- different response shapes (markdown text, flat dicts, nested objects, lists)
- parameters (path params like /users/{id}, query params like ?severity=high)
- dynamic / live-ish data that changes between calls (metrics, prices, incidents)
- deliberately CHALLENGING endpoints: 404 on bad ids, a flaky 503, an artificially slow one

Everything is fake and self-contained — no external services, safe to run offline.
"""

import asyncio
import hashlib
import random
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Core API Mock Server",
    description="Simulates internal company backend systems for MCP infrastructure development",
    version="2.0.0",
)


# --------------------------------------------------------------------------------------
# Helpers — deterministic-but-varied fake data. We seed randomness by the input + a
# time bucket so values look "live" (change over minutes) yet stay explainable in a demo.
# --------------------------------------------------------------------------------------
def _seeded_rng(*parts: object) -> random.Random:
    key = "|".join(str(p) for p in parts)
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------------------
# Original endpoints (kept for backward compatibility with the first tools)
# --------------------------------------------------------------------------------------
MOCK_TEXT_DATA = {
    "report_id": "REP-2026-XYZ",
    "status": "Success",
    "generated_at": "2026-06-17T12:00:00Z",
    "content": (
        "### Internal System Status Report\n\n"
        "All core components are operating within normal parameters.\n"
        "- **Database:** Stable (99.9% uptime)\n"
        "- **Authentication Gateway:** Nominal latency (45ms)\n"
        "- **Storage Clusters:** 62% capacity utilized."
    ),
}

MOCK_IMAGE_DATA = {
    "image_id": "IMG-404-DATA",
    "format": "PNG",
    "dimensions": "1024x1024",
    "mock_url": "https://placeholder.pics/svg/300",
    "status": "Rendered",
}


@app.get("/")
def read_root():
    return {"message": "Internal Core API Mock is running successfully!", "version": app.version}


@app.get("/api/v1/data/text")
def get_mock_text():
    """Static, well-formed markdown mimicking internal database logs."""
    return JSONResponse(content=MOCK_TEXT_DATA)


@app.get("/api/v1/data/image")
def get_mock_image():
    """Simulated image metadata mimicking media generation pipelines."""
    return JSONResponse(content=MOCK_IMAGE_DATA)


# --------------------------------------------------------------------------------------
# Weather — PATH param, nested response. Works for any city (hash-derived), so it never
# 404s: good "happy path" example of a parameterized tool.
# --------------------------------------------------------------------------------------
_CONDITIONS = ["Clear", "Partly Cloudy", "Overcast", "Light Rain", "Thunderstorm", "Fog", "Snow"]


@app.get("/api/v1/weather/{city}")
def get_weather(city: str):
    """Current (fake) weather for any city. Nested JSON: parsing challenge for the model."""
    rng = _seeded_rng("weather", city.lower(), _now().strftime("%Y-%m-%d-%H"))
    temp_c = round(rng.uniform(-5, 38), 1)
    return {
        "location": {"city": city.title(), "timezone": "UTC"},
        "observed_at": _iso(_now()),
        "current": {
            "temperature_c": temp_c,
            "temperature_f": round(temp_c * 9 / 5 + 32, 1),
            "condition": rng.choice(_CONDITIONS),
            "humidity_pct": rng.randint(20, 95),
            "wind": {"speed_kmh": round(rng.uniform(0, 60), 1), "direction": rng.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])},
        },
        "forecast_3d": [
            {
                "date": (_now() + timedelta(days=d)).strftime("%Y-%m-%d"),
                "high_c": round(temp_c + rng.uniform(-2, 6), 1),
                "low_c": round(temp_c - rng.uniform(2, 8), 1),
                "condition": rng.choice(_CONDITIONS),
            }
            for d in range(1, 4)
        ],
    }


# --------------------------------------------------------------------------------------
# User directory — QUERY search + a get-by-id that 404s. Teaches list filtering and
# error handling in one domain.
# --------------------------------------------------------------------------------------
_USERS = [
    {"id": "u-1001", "name": "Ada Lovelace", "role": "Platform Engineer", "team": "Infra", "on_call": True},
    {"id": "u-1002", "name": "Alan Turing", "role": "Security Lead", "team": "Security", "on_call": False},
    {"id": "u-1003", "name": "Grace Hopper", "role": "Staff SRE", "team": "Infra", "on_call": True},
    {"id": "u-1004", "name": "Katherine Johnson", "role": "Data Scientist", "team": "Analytics", "on_call": False},
    {"id": "u-1005", "name": "Linus Pauling", "role": "Backend Engineer", "team": "Payments", "on_call": False},
    {"id": "u-1006", "name": "Hedy Lamarr", "role": "Network Engineer", "team": "Infra", "on_call": False},
]


@app.get("/api/v1/users")
def search_users(
    q: str | None = Query(None, description="Case-insensitive match on name, role, or team"),
    team: str | None = Query(None, description="Exact team filter, e.g. Infra"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search the staff directory. Returns a list — model must pick/summarize."""
    results = _USERS
    if q:
        ql = q.lower()
        results = [u for u in results if ql in u["name"].lower() or ql in u["role"].lower() or ql in u["team"].lower()]
    if team:
        results = [u for u in results if u["team"].lower() == team.lower()]
    return {"count": len(results[:limit]), "query": {"q": q, "team": team}, "results": results[:limit]}


@app.get("/api/v1/users/{user_id}")
def get_user(user_id: str):
    """Fetch one user by id. 404 on unknown id — a real error path to handle."""
    for u in _USERS:
        if u["id"] == user_id:
            return u
    raise HTTPException(status_code=404, detail=f"No user with id '{user_id}'. Try u-1001..u-1006.")


# --------------------------------------------------------------------------------------
# Incidents — QUERY filter, live-ish list that shifts over time.
# --------------------------------------------------------------------------------------
_SERVICES = ["auth-gateway", "payments-api", "storage-cluster", "search-index", "notification-bus"]
_SEVERITIES = ["low", "medium", "high", "critical"]


@app.get("/api/v1/incidents")
def list_incidents(
    severity: str | None = Query(None, description="One of: low, medium, high, critical"),
    status: str = Query("open", description="open or resolved"),
):
    """Current incidents. Count/detail change every few minutes (live feel)."""
    rng = _seeded_rng("incidents", _now().strftime("%Y-%m-%d-%H-%M"))
    n = rng.randint(1, 5)
    incidents = []
    for i in range(n):
        sev = rng.choice(_SEVERITIES)
        opened = _now() - timedelta(minutes=rng.randint(3, 600))
        incidents.append({
            "id": f"INC-{opened.strftime('%Y%m%d')}-{rng.randint(100, 999)}",
            "service": rng.choice(_SERVICES),
            "severity": sev,
            "status": "resolved" if rng.random() < 0.3 else "open",
            "opened_at": _iso(opened),
            "summary": rng.choice([
                "Elevated error rate on write path",
                "Latency spike above SLO",
                "Intermittent 5xx from upstream",
                "Disk pressure on primary node",
                "Auth token refresh failures",
            ]),
        })
    if severity:
        incidents = [x for x in incidents if x["severity"] == severity.lower()]
    incidents = [x for x in incidents if x["status"] == status.lower()]
    return {"generated_at": _iso(_now()), "filter": {"severity": severity, "status": status}, "incidents": incidents}


# --------------------------------------------------------------------------------------
# Metrics time-series — PATH + QUERY, returns an ARRAY of datapoints (aggregation task).
# --------------------------------------------------------------------------------------
@app.get("/api/v1/metrics/{service}")
def get_metrics(
    service: str,
    window: str = Query("1h", description="1h, 24h, or 7d"),
    metric: str = Query("latency_ms", description="latency_ms, error_rate, or rps"),
):
    """Time-series for a service. The model must reason over the array (max/avg/trend)."""
    points_map = {"1h": 12, "24h": 24, "7d": 28}
    n = points_map.get(window, 12)
    rng = _seeded_rng("metrics", service, window, metric, _now().strftime("%Y-%m-%d-%H"))
    base = {"latency_ms": 45, "error_rate": 0.5, "rps": 320}.get(metric, 50)
    series = []
    for i in range(n):
        ts = _now() - timedelta(minutes=(n - i) * 5)
        jitter = rng.uniform(-0.3, 0.5) * base
        spike = base * rng.uniform(2, 4) if rng.random() < 0.12 else 0  # occasional anomaly
        series.append({"t": _iso(ts), "value": round(max(0, base + jitter + spike), 2)})
    values = [p["value"] for p in series]
    return {
        "service": service,
        "metric": metric,
        "window": window,
        "unit": {"latency_ms": "ms", "error_rate": "%", "rps": "req/s"}.get(metric, ""),
        "summary": {"min": min(values), "max": max(values), "avg": round(sum(values) / len(values), 2)},
        "series": series,
    }


# --------------------------------------------------------------------------------------
# Market price — QUERY param, flat numeric response that moves each call.
# --------------------------------------------------------------------------------------
_BASE_PRICES = {"BTC": 68000, "ETH": 3500, "AAPL": 225, "GOOG": 178, "NVDA": 132, "TSLA": 245}


@app.get("/api/v1/price")
def get_price(symbol: str = Query(..., description="Ticker, e.g. BTC, ETH, AAPL, NVDA")):
    """Latest (fake) price + 24h change. Unknown symbols get a generated price."""
    sym = symbol.upper()
    base = _BASE_PRICES.get(sym, _seeded_rng("price", sym).uniform(10, 500))
    rng = _seeded_rng("price", sym, _now().strftime("%Y-%m-%d-%H-%M"))
    change_pct = round(rng.uniform(-6, 6), 2)
    price = round(base * (1 + change_pct / 100), 2)
    return {
        "symbol": sym,
        "price": price,
        "currency": "USD",
        "change_24h_pct": change_pct,
        "as_of": _iso(_now()),
        "known_symbol": sym in _BASE_PRICES,
    }


# --------------------------------------------------------------------------------------
# IoT sensor telemetry — PATH param, physical-looking readings.
# --------------------------------------------------------------------------------------
@app.get("/api/v1/sensors/{sensor_id}")
def get_sensor(sensor_id: str):
    """Telemetry for a warehouse sensor. Flags out-of-range readings."""
    rng = _seeded_rng("sensor", sensor_id, _now().strftime("%Y-%m-%d-%H-%M"))
    temp = round(rng.uniform(-2, 12), 2)   # cold-storage range
    humidity = round(rng.uniform(30, 80), 1)
    return {
        "sensor_id": sensor_id,
        "zone": rng.choice(["A-cold", "B-cold", "C-ambient", "D-loading"]),
        "reading": {"temperature_c": temp, "humidity_pct": humidity, "battery_pct": rng.randint(5, 100)},
        "alert": "TEMP_OUT_OF_RANGE" if temp > 8 else ("LOW_BATTERY" if rng.random() < 0.15 else None),
        "measured_at": _iso(_now()),
    }


# --------------------------------------------------------------------------------------
# CHALLENGING endpoints — for testing resilience/timeouts, not just happy paths.
# --------------------------------------------------------------------------------------
@app.get("/api/v1/flaky")
def flaky():
    """Fails ~40% of the time with 503. Use it to test retry / error-handling behavior."""
    if random.random() < 0.4:
        raise HTTPException(status_code=503, detail="Upstream temporarily unavailable. Retry with backoff.")
    return {"status": "ok", "served_at": _iso(_now()), "note": "You caught it on a good attempt."}


@app.get("/api/v1/slow")
async def slow(seconds: float = Query(2.0, ge=0, le=12, description="Artificial delay before responding")):
    """Sleeps, then responds. Use it to exercise client-side timeouts."""
    await asyncio.sleep(seconds)
    return {"status": "ok", "waited_seconds": seconds, "served_at": _iso(_now())}


# --------------------------------------------------------------------------------------
# Fun — random developer joke, purely to make demos less dry.
# --------------------------------------------------------------------------------------
_JOKES = [
    "There are only 10 kinds of people: those who understand binary and those who don't.",
    "A SQL query walks into a bar, sees two tables, and asks: 'Can I JOIN you?'",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "It works on my machine. Shipping my machine.",
    "To understand recursion, you must first understand recursion.",
]


@app.get("/api/v1/joke")
def joke():
    """A random developer joke. Content field so it renders as plain text via the tool."""
    return {"content": random.choice(_JOKES)}
