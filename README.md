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

## Try it without a client

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"cli"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_weather","arguments":{"location":"Seattle"}}}' \
  | python3 server.py
```

## Run the tests

```bash
python3 test_server.py
```

The suite monkeypatches the two network functions, so it runs offline.

## Wire it into a client

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) and add:

```json
{
  "mcpServers": {
    "weather": {
      "command": "python3",
      "args": ["/Users/mona/projects/weather-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop. The `get_weather` tool appears under the connectors
(plug) menu.

### Claude Code

```bash
claude mcp add weather -- python3 /Users/mona/projects/weather-mcp/server.py
```

## How it works

`server.py` reads newline-delimited JSON-RPC messages from stdin and writes
responses to stdout:

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
