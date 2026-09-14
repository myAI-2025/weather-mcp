# weather-mcp

[![Python application](https://github.com/myAI-2025/weather-mcp/actions/workflows/python-app.yml/badge.svg)](https://github.com/myAI-2025/weather-mcp/actions/workflows/python-app.yml)
[![PyPI](https://img.shields.io/pypi/v/myai-weather-mcp)](https://pypi.org/project/myai-weather-mcp/)

<!-- mcp-name: io.github.myAI-2025/openmeteo-mcp -->

A minimal [Model Context Protocol](https://modelcontextprotocol.io) server in a
single file. It speaks JSON-RPC 2.0 over stdio and exposes two tools,
`get_weather` and `get_hourly_forecast`, backed by the free
[Open-Meteo](https://open-meteo.com) API.

No third-party runtime dependencies — standard library only. Requires Python 3.8+.

## Quick start: Claude Code

You need [Claude Code](https://code.claude.com/docs/en/overview) installed and signed in,
[uv](https://docs.astral.sh/uv/getting-started/installation/) installed (which provides
`uvx`), and an internet connection. No weather API key is needed.

Register the published release with one command:

```bash
claude mcp add --scope user weather -- uvx myai-weather-mcp==0.1.2
```

This lets Claude Code download and start the package automatically. No repository
clone or separate package installation is needed. If you already have a server
named `weather`, inspect it with `claude mcp get weather` before changing it.

Check the connection:

```bash
claude mcp get weather
```

Look for `Connected`. Start a new Claude Code session (or reconnect `weather`
through `/mcp` in an existing session), then ask:

- “Use the weather tool to tell me the current weather in Tokyo.”
- “Use the hourly forecast tool to show the next six hours in Tokyo.”

Expect current conditions, temperature in °F, wind in mph, and six forecast rows
with local times and rain probabilities. Values change with the weather.

### If something looks stuck

- **A blank terminal after `uvx myai-weather-mcp`:** the server is waiting for an
  MCP client. This is expected; press Control+C and use the client setup above.
- **`uvx` not found:** install uv, reopen your terminal, and retry. For a desktop
  client that cannot find it, use the full path reported by `command -v uvx`
  (macOS/Linux) or `where uvx` (Windows) as the command in its configuration.
- **New release not found:** run `uvx --refresh myai-weather-mcp==0.1.2` to refresh
  the package cache, then press Control+C and reconnect the client.
- **Claude Code says “Not logged in”:** open `claude` and run `/login`.
- **Location not found:** try a well-known city name. An unknown place should
  return a readable error rather than a forecast.

### Help us test

Try the two questions above and a made-up location such as `ZzzxqqNowhere`.
If anything is confusing, [open an issue](https://github.com/myAI-2025/weather-mcp/issues/new)
with your operating system, client, package version, steps, and the error message.
Remove passwords, authentication codes, and other private information before sharing.

## The tools

| Tool | Arguments | Returns |
| --- | --- | --- |
| `get_weather` | `location` (string, required) — a place name like `"Seattle"` or `"Paris, France"` | Current conditions, temperature (°F), and wind (mph) as a text block. Unknown place names come back as a result with `isError: true`. |
| `get_hourly_forecast` | `location` (string, required); `hours` (integer, optional, 1–48, default 12) | Hour-by-hour temperature (°F), precipitation probability, and conditions, one line per hour. Timestamps are local to the location. Out-of-range `hours` is clamped. |

## Usage

The responses below are illustrative snapshots, not current weather.

Once the server is wired into a client, just ask in natural
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
  | openmeteo-mcp        # or: python3 weather_mcp/server.py
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

Pick whichever fits your setup. All of them give you an `openmeteo-mcp`
command (or an equivalent) that clients can launch.

The distribution is named `myai-weather-mcp`; both `myai-weather-mcp` and
`openmeteo-mcp` launch the server.

**From PyPI:**

```bash
pipx install myai-weather-mcp      # or: pip install myai-weather-mcp
```

**With [uv](https://docs.astral.sh/uv/) — no install step at all:**

```bash
uvx myai-weather-mcp
# or straight from GitHub:
uvx --from git+https://github.com/myAI-2025/weather-mcp openmeteo-mcp
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
claude mcp add --scope user weather -- openmeteo-mcp
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
      "command": "openmeteo-mcp"
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
      "args": ["myai-weather-mcp"]
    }
  }
}
```

Restart Claude Desktop. The tools appear under the connectors (plug) menu.

### Any other MCP client

It's a standard stdio server: launch `openmeteo-mcp` (or
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

## Acknowledgments

Created and maintained by **Mona ([myAI-2025](https://github.com/myAI-2025))**,
who directed the project and tested it in Claude Code.

Developed with AI assistance from **Claude and Claude Code (Anthropic)** and
**ChatGPT and Codex (OpenAI)** across planning, implementation, debugging,
testing, documentation, packaging, and publication.

Weather data is provided by [Open-Meteo](https://open-meteo.com).
These acknowledgments credit the tools and services used; they do not imply
sponsorship or endorsement by their providers.

## License

MIT — see [LICENSE](LICENSE).
