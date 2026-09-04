#!/usr/bin/env python3
"""
Structural test for server.py's JSON-RPC handling, without hitting the
real network (this sandbox can't reach external APIs). We monkeypatch
geocode()/fetch_current_weather()/fetch_hourly_forecast() with canned data
and drive the request handler directly, checking what it would write to
stdout.

Runs two ways:
  * ``python3 test_server.py``  -- prints one line per check
  * ``pytest``                  -- collects ``test_structural`` as a test
"""

import sys

import server  # our MCP server module


def fake_geocode(place_name):
    assert place_name == "Seattle"
    return {"name": "Seattle", "country": "United States", "latitude": 47.6, "longitude": -122.33}


def fake_fetch_current_weather(lat, lon):
    assert (lat, lon) == (47.6, -122.33)
    return {"current": {"temperature_2m": 68.5, "wind_speed_10m": 5.2, "weather_code": 1}}


def fake_fetch_hourly_forecast(lat, lon, hours):
    assert (lat, lon) == (47.6, -122.33)
    assert hours == 6
    stamps = [f"2026-09-04T{h:02d}:00" for h in range(15, 21)]
    return {"hourly": {
        "time": stamps,
        "temperature_2m": [60.1, 61.0, 62.3, 61.8, 59.5, 57.2],
        "precipitation_probability": [10, 20, 40, 30, 15, 5],
        "weather_code": [1, 2, 3, 61, 3, 2],
    }}


def clamp_checking_fetch(lat, lon, hours):
    assert 1 <= hours <= 48, f"hours not clamped: {hours}"
    return {"hourly": {"time": ["2026-09-04T15:00"], "temperature_2m": [60.0],
                       "precipitation_probability": [0], "weather_code": [0]}}


def run(req: dict):
    """Call handle_request and capture whatever it writes via send()."""
    captured = []
    original_send = server.send
    server.send = lambda msg: captured.append(msg)
    try:
        server.handle_request(req)
    finally:
        server.send = original_send
    return captured


def expect(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def test_structural():
    # 1. initialize -- should echo protocolVersion and advertise tools capability
    out = run({"jsonrpc": "2.0", "id": 1, "method": "initialize",
               "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test-client"}}})
    expect("initialize returns exactly one message", len(out) == 1)
    expect("initialize echoes protocolVersion", out[0]["result"]["protocolVersion"] == "2024-11-05")
    expect("initialize advertises tools capability", "tools" in out[0]["result"]["capabilities"])
    expect("initialize id matches request id", out[0]["id"] == 1)

    # 2. notifications/initialized -- must NOT produce a response
    out = run({"jsonrpc": "2.0", "method": "notifications/initialized"})
    expect("notifications/initialized produces no response", len(out) == 0)

    # 3. tools/list -- should return both tools with correct schema
    out = run({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = out[0]["result"]["tools"]
    by_name = {t["name"]: t for t in tools}
    expect("tools/list returns 2 tools", len(tools) == 2)
    expect("get_weather is listed", "get_weather" in by_name)
    expect("get_hourly_forecast is listed", "get_hourly_forecast" in by_name)
    expect("get_weather requires 'location'", by_name["get_weather"]["inputSchema"]["required"] == ["location"])
    expect("get_hourly_forecast requires 'location'", by_name["get_hourly_forecast"]["inputSchema"]["required"] == ["location"])

    # 4. tools/call (happy path) -- monkeypatch the network calls
    server.geocode = fake_geocode
    server.fetch_current_weather = fake_fetch_current_weather
    out = run({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
               "params": {"name": "get_weather", "arguments": {"location": "Seattle"}}})
    result = out[0]["result"]
    expect("tools/call returns content array", "content" in result)
    text = result["content"][0]["text"]
    expect("tools/call result mentions Seattle", "Seattle" in text)
    expect("tools/call result mentions temperature", "68.5" in text)
    expect("tools/call is not marked as error", not result.get("isError", False))

    # 5. tools/call with unknown location -- geocode returns None
    server.geocode = lambda name: None
    out = run({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
               "params": {"name": "get_weather", "arguments": {"location": "Nowhereville"}}})
    result = out[0]["result"]
    expect("unknown location is marked as error", result.get("isError") is True)

    # 6. unknown method with id -- should return a JSON-RPC error, not crash
    out = run({"jsonrpc": "2.0", "id": 5, "method": "totally/bogus"})
    expect("unknown method returns an error object", "error" in out[0])
    expect("unknown method error code is -32601", out[0]["error"]["code"] == -32601)

    # 7. tools/call get_hourly_forecast (happy path) -- monkeypatch the network calls
    server.geocode = fake_geocode  # test 5 left this stubbed to return None
    server.fetch_hourly_forecast = fake_fetch_hourly_forecast
    out = run({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
               "params": {"name": "get_hourly_forecast",
                          "arguments": {"location": "Seattle", "hours": 6}}})
    result = out[0]["result"]
    expect("hourly forecast returns content array", "content" in result)
    htext = result["content"][0]["text"]
    expect("hourly forecast mentions Seattle", "Seattle" in htext)
    expect("hourly forecast has 6 hour rows", htext.count("2026-09-04") == 6)
    expect("hourly forecast shows a temperature", "60.1" in htext)
    expect("hourly forecast shows precip probability", "40%" in htext)
    expect("hourly forecast is not marked as error", not result.get("isError", False))

    # 8. get_hourly_forecast clamps out-of-range hours instead of failing
    server.fetch_hourly_forecast = clamp_checking_fetch
    out = run({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
               "params": {"name": "get_hourly_forecast",
                          "arguments": {"location": "Seattle", "hours": 999}}})
    expect("out-of-range hours is clamped, not an error",
           not out[0]["result"].get("isError", False))


if __name__ == "__main__":
    try:
        test_structural()
    except AssertionError as exc:
        print(f"\nFAILED: {exc}")
        sys.exit(1)
    print("\nAll structural tests passed.")
