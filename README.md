# weather-mcp

[![Python application](https://github.com/myAI-2025/weather-mcp/actions/workflows/python-app.yml/badge.svg)](https://github.com/myAI-2025/weather-mcp/actions/workflows/python-app.yml)

A minimal [Model Context Protocol](https://modelcontextprotocol.io) server in a
single file. It speaks JSON-RPC 2.0 over stdio and exposes two tools,
`get_weather` and `get_hourly_forecast`, backed by the free
[Open-Meteo](https://open-meteo.com) API.

No third-party dependencies — standard library only. Requires Python 3.7+.

## The tools

| Tool | Arguments | Returns |
| --- | --- | --- |
| `get_weather` | `location` (string, required) — a place name like `"Seattle"` or `"Paris, France"` | Current conditions, temperature (°F), and wind (mph) as a text block. Unknown place names come back as a result with `isError: true`. |
| `get_hourly_forecast` | `location` (string, required); `hours` (integer, optional, 1–48, default 12) | Hour-by-hour temperature (°F), precipitation probability, and conditions, one line per hour. Timestamps are local to the location. Out-of-range `hours` is clamped. |

## Usage

Once the server is wired into a client (see below), just ask in natural
language — the model picks the tool and fills in the arguments:

> **You:** What's the weather in Seattle right now?
>
> **Claude:** *(calls `get_weather` with `location: "Seattle"`)*
> Current weather in Seattle, United States: overcast, 54.2 °F, wind 1.1 mph.

> **You:** Will it rain in Tokyo over the next 6 hours?
>
> **Claude:** *(calls `get_hourly_forecast` with `location: "Tokyo"`, `hours: 6`)*
> Yes — drizzle every hour, precipitation probability climbing from 76 % to 89 %.

### Try it without a client

Drive the server directly over stdio with a hand-written JSON-RPC exchange:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"cli"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_weather","arguments":{"location":"Seattle"}}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_hourly_forecast","arguments":{"location":"Tokyo","hours":6}}}' \
  | weather-mcp          # or: python3 weather_mcp/server.py
```

The `tools/call` responses look like:

```json
{"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text",
  "text": "Current weather in Seattle, United States:\n  Conditions:  overcast\n  Temperature: 54.2°F\n  Wind:        1.1 mph"}]}}
```

```text
Hourly forecast for Tokyo, Japan (next 6 hours):
  2026-09-04 18:00  73.0°F  precip  76%  dense drizzle
  2026-09-04 19:00  72.5°F  precip  76%  dense drizzle
  2026-09-04 20:00  72.2°F  precip  78%  dense drizzle
  2026-09-04 21:00  71.8°F  precip  80%  slight rain
  2026-09-04 22:00  71.7°F  precip  84%  dense drizzle
  2026-09-04 23:00  71.3°F  precip  89%  moderate drizzle
```

An unknown place name comes back as a normal result with `"isError": true`:

```json
{"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text",
  "text": "Could not find any location named 'Zzzxqq'."}], "isError": true}}
```

## Install

Pick whichever fits your setup. All of them give you a `weather-mcp`
command (or an equivalent) that clients can launch.

**With [uv](https://docs.astral.sh/uv/) — no install step at all:**

```bash
uvx --from git+https://github.com/myAI-2025/weather-mcp weather-mcp
```

**With pipx or pip:**

```bash
pipx install git+https://github.com/myAI-2025/weather-mcp
# or
pip install git+https://github.com/myAI-2025/weather-mcp
```

**From a clone (no install):**

```bash
git clone https://github.com/myAI-2025/weather-mcp
python3 weather-mcp/weather_mcp/server.py     # runs the server directly
```

## Configure a client

### Claude Code

```bash
claude mcp add --scope user weather -- weather-mcp
```

If you cloned instead of installing, point at the file:

```bash
claude mcp add --scope user weather -- python3 /path/to/weather-mcp/weather_mcp/server.py
```

Restart Claude Code (or reconnect via `/mcp`). Both tools then appear as
`mcp__weather__get_weather` and `mcp__weather__get_hourly_forecast`.

### Claude Desktop

Edit `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`)
and add:

```json
{
  "mcpServers": {
    "weather": {
      "command": "weather-mcp"
    }
  }
}
```

Using `uvx` instead, so nothing needs installing first:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/myAI-2025/weather-mcp", "weather-mcp"]
    }
  }
}
```

Restart Claude Desktop. The tools appear under the connectors (plug) menu.

### Any other MCP client

It's a standard stdio server: launch `weather-mcp` (or
`python3 -m weather_mcp`) as a subprocess and speak JSON-RPC 2.0 over its
stdin/stdout. See **How it works** below.

## Development

```bash
git clone https://github.com/myAI-2025/weather-mcp
cd weather-mcp
pip install -e ".[dev]"
python3 test_server.py     # one line per check
pytest                     # same checks, pytest-style
```

The suite monkeypatches the network functions, so it runs offline.

## How it works

`weather_mcp/server.py` reads newline-delimited JSON-RPC messages from stdin
and writes responses to stdout:

| Method | Behavior |
| --- | --- |
| `initialize` | Echoes the client's `protocolVersion`, advertises the `tools` capability, returns `serverInfo`. |
| `notifications/initialized` | Notification — no response. |
| `tools/list` | Returns the `get_weather` and `get_hourly_forecast` tools and their input schemas. |
| `tools/call` | Dispatches to the named tool: geocodes the location, fetches weather from Open-Meteo, formats a text block. Lookup/network failures return `isError: true` rather than a JSON-RPC error. |
| anything else (with an `id`) | JSON-RPC error `-32601`, method not found. |

Upstream calls: Open-Meteo geocoding (`geocoding-api.open-meteo.com`) then the
forecast endpoint (`api.open-meteo.com`) with `current=temperature_2m,wind_speed_10m,weather_code`.

## License

MIT — see [LICENSE](LICENSE).
