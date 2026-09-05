#!/usr/bin/env python3
"""
A minimal Model Context Protocol (MCP) server.

It speaks JSON-RPC 2.0 over stdio (newline-delimited messages on stdin/stdout)
and exposes a single tool, ``get_weather``, backed by the free Open-Meteo API.

There are no third-party dependencies: JSON-RPC framing and HTTP are done by
hand with the standard library, so the server runs anywhere Python 3 does.

Wire protocol
-------------
* ``initialize``                -> echoes the protocol version, advertises the
                                  ``tools`` capability and server info.
* ``notifications/initialized`` -> notification, produces no response.
* ``tools/list``                -> returns the single ``get_weather`` tool.
* ``tools/call``                -> runs ``get_weather`` and returns a text
                                  content block; lookup failures come back as
                                  a normal result with ``isError: true``.
* anything else (with an id)    -> JSON-RPC error ``-32601`` (method not found).
"""

import json
import sys
import urllib.parse
import urllib.request

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "weather-mcp"
SERVER_VERSION = "0.1.0"

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HTTP_TIMEOUT = 15
USER_AGENT = f"{SERVER_NAME}/{SERVER_VERSION}"

DEFAULT_FORECAST_HOURS = 12
MAX_FORECAST_HOURS = 48

# WMO weather interpretation codes (Open-Meteo `weather_code`).
WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


# ---------------------------------------------------------------------------
# HTTP + upstream API helpers
# ---------------------------------------------------------------------------

def _http_get_json(url, params):
    """GET ``url`` with a query string built from ``params`` and parse JSON."""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode(place_name):
    """Resolve a place name to a location dict, or ``None`` if not found."""
    data = _http_get_json(GEOCODE_URL, {
        "name": place_name,
        "count": 1,
        "language": "en",
        "format": "json",
    })
    results = data.get("results") or []
    if not results:
        return None
    top = results[0]
    return {
        "name": top.get("name"),
        "country": top.get("country"),
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
    }


def fetch_current_weather(lat, lon):
    """Return Open-Meteo's forecast payload (with a ``current`` block)."""
    return _http_get_json(FORECAST_URL, {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,weather_code",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
    })


def fetch_hourly_forecast(lat, lon, hours):
    """Return Open-Meteo's hourly forecast for the next ``hours`` hours.

    ``forecast_hours`` limits the ``hourly`` block to that many entries
    starting at the current hour; ``timezone=auto`` makes the timestamps
    local to the coordinate.
    """
    return _http_get_json(FORECAST_URL, {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "auto",
        "forecast_hours": hours,
    })


# ---------------------------------------------------------------------------
# JSON-RPC plumbing
# ---------------------------------------------------------------------------

def send(message):
    """Write one JSON-RPC message to stdout as a single line."""
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def _result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _text_content(text, is_error=False):
    """Build a ``tools/call`` result carrying a single text block."""
    result = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


# ---------------------------------------------------------------------------
# Tool definitions + dispatch
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "Get the current weather for a location given its name "
            "(city, town, or landmark). Returns conditions, temperature "
            "in Fahrenheit, and wind speed in mph."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Place name, e.g. 'Seattle' or 'Paris, France'.",
                },
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_hourly_forecast",
        "description": (
            "Get the hour-by-hour weather forecast for a location given its "
            "name. Returns temperature (Fahrenheit), precipitation "
            "probability, and conditions for each upcoming hour."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Place name, e.g. 'Tokyo' or 'Austin, Texas'.",
                },
                "hours": {
                    "type": "integer",
                    "description": (
                        f"How many hours ahead to forecast "
                        f"(1-{MAX_FORECAST_HOURS}). Default {DEFAULT_FORECAST_HOURS}."
                    ),
                    "minimum": 1,
                    "maximum": MAX_FORECAST_HOURS,
                },
            },
            "required": ["location"],
        },
    },
]


def _call_get_weather(arguments):
    location = (arguments or {}).get("location")
    if not location or not str(location).strip():
        return _text_content("Error: the 'location' argument is required.", is_error=True)

    try:
        place = geocode(location)
    except Exception as exc:  # network / parse failure -> surface as tool error
        return _text_content(f"Error looking up '{location}': {exc}", is_error=True)

    if not place:
        return _text_content(
            f"Could not find any location named '{location}'.", is_error=True
        )

    try:
        payload = fetch_current_weather(place["latitude"], place["longitude"])
    except Exception as exc:
        return _text_content(
            f"Error fetching weather for '{location}': {exc}", is_error=True
        )

    current = (payload or {}).get("current") or {}
    temp = current.get("temperature_2m")
    wind = current.get("wind_speed_10m")
    conditions = WEATHER_CODES.get(current.get("weather_code"), "unknown conditions")

    label = place["name"]
    if place.get("country"):
        label = f"{label}, {place['country']}"

    text = (
        f"Current weather in {label}:\n"
        f"  Conditions:  {conditions}\n"
        f"  Temperature: {temp}°F\n"
        f"  Wind:        {wind} mph"
    )
    return _text_content(text)


def _call_get_hourly_forecast(arguments):
    arguments = arguments or {}
    location = arguments.get("location")
    if not location or not str(location).strip():
        return _text_content("Error: the 'location' argument is required.", is_error=True)

    hours = arguments.get("hours", DEFAULT_FORECAST_HOURS)
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        return _text_content("Error: 'hours' must be an integer.", is_error=True)
    hours = max(1, min(hours, MAX_FORECAST_HOURS))

    try:
        place = geocode(location)
    except Exception as exc:
        return _text_content(f"Error looking up '{location}': {exc}", is_error=True)

    if not place:
        return _text_content(
            f"Could not find any location named '{location}'.", is_error=True
        )

    try:
        payload = fetch_hourly_forecast(place["latitude"], place["longitude"], hours)
    except Exception as exc:
        return _text_content(
            f"Error fetching forecast for '{location}': {exc}", is_error=True
        )

    hourly = (payload or {}).get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    precip = hourly.get("precipitation_probability") or []
    codes = hourly.get("weather_code") or []
    if not times:
        return _text_content(
            f"No hourly forecast data available for '{location}'.", is_error=True
        )

    label = place["name"]
    if place.get("country"):
        label = f"{label}, {place['country']}"

    lines = [f"Hourly forecast for {label} (next {len(times)} hours):"]
    for i, stamp in enumerate(times):
        temp = temps[i] if i < len(temps) else "?"
        pop = precip[i] if i < len(precip) else None
        conditions = WEATHER_CODES.get(
            codes[i] if i < len(codes) else None, "unknown conditions"
        )
        pop_str = f"{pop}%" if pop is not None else "n/a"
        lines.append(
            f"  {stamp.replace('T', ' ')}  {temp}°F  precip {pop_str:>4}  {conditions}"
        )
    return _text_content("\n".join(lines))


TOOL_HANDLERS = {
    "get_weather": _call_get_weather,
    "get_hourly_forecast": _call_get_hourly_forecast,
}


def handle_request(req):
    """Dispatch a single decoded JSON-RPC request object."""
    method = req.get("method")
    req_id = req.get("id")
    is_notification = "id" not in req

    if method == "initialize":
        params = req.get("params") or {}
        version = params.get("protocolVersion") or PROTOCOL_VERSION
        send(_result(req_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }))
        return

    if method == "notifications/initialized":
        return  # notification: no response

    if method == "tools/list":
        send(_result(req_id, {"tools": TOOLS}))
        return

    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            send(_result(req_id, _text_content(
                f"Unknown tool: {name!r}", is_error=True
            )))
        else:
            send(_result(req_id, handler(arguments)))
        return

    # Unknown method. Stay silent for notifications; error for requests.
    if not is_notification:
        send(_error(req_id, -32601, f"Method not found: {method}"))


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            send(_error(None, -32700, "Parse error"))
            continue
        if not isinstance(req, dict):
            send(_error(None, -32600, "Invalid Request"))
            continue
        try:
            handle_request(req)
        except Exception as exc:  # never let the loop die on one bad request
            if "id" in req:
                send(_error(req.get("id"), -32603, f"Internal error: {exc}"))


if __name__ == "__main__":
    main()
