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

### 1. Prepare your terminal

**Where do I paste each instruction?**

You will use two places:

- **A regular Terminal tab** is for setup commands. On a Mac, open the Terminal
  app and press **Command + T** to open a new tab. Paste one command, then press
  **Return**.
- **The Claude Code conversation** is where you ask questions, such as
  “What is the weather in Tokyo?”

If Claude is already chatting with you, open a new Terminal tab for the setup
commands. Keep your Claude conversation in its original tab so you can return
to it afterward.

Open **Terminal** on macOS/Linux or **PowerShell** on Windows. Paste the command
blocks in this guide there. Weather questions and commands beginning with `/`,
such as `/login` and `/mcp`, belong inside a Claude Code conversation.
If Claude Code is already open in your terminal, use a new terminal tab for setup.

1. Install Claude Code using its [official setup guide](https://code.claude.com/docs/en/setup).
   Run `claude --version` in your terminal to check that it is available.
   Then run `claude` and follow the sign-in prompts; if needed, type `/login`
   inside Claude Code. Keep a separate terminal tab open for the next steps.
2. Install uv using the [instructions for your operating system](https://docs.astral.sh/uv/getting-started/installation/).
   uv supplies `uvx`, which downloads and runs the weather package for you.
   Reopen your terminal after installation and run `uvx --version`.
   If either version check says “command not found,” finish that installation
   before continuing.

You need an internet connection to download the package and fetch weather.
No weather API key is needed.

### 2. Add the weather server

Run this in your terminal:

```bash
claude mcp add --scope user weather -- uvx myai-weather-mcp==0.1.2
```

`weather` is the name you will see in Claude Code. `myai-weather-mcp` is the
published package it runs. User scope makes this setup available across your
Claude Code projects. No repository clone or separate package installation is needed.
See the [Claude Code MCP reference](https://code.claude.com/docs/en/mcp) for other setup options.

The `==0.1.2` pin selects the release used in this guide, so a later release does
not silently change your setup. It is intentional; see [Updating your version](#updating-your-version)
when you want to upgrade.

If `weather` already exists, inspect it with `claude mcp get weather`.
If it already uses the command above, continue to the next step. To replace an
older user-scope setup, follow the replacement steps under [Updating your version](#updating-your-version).

### 3. Check the connection and ask for weather

Run in your terminal:

```bash
claude mcp get weather
```

Look for `Connected`. If you see a different status or no server is found, use
[Connection troubleshooting](#connection-troubleshooting) below.

Start a new Claude Code session by running `claude`, or type `/mcp` inside an
existing session and reconnect `weather`. At Claude Code's conversation prompt, paste:

- “Use the weather tool to tell me the current weather in Tokyo.”
- “Use the hourly forecast tool to show the next six hours in Tokyo.”

Expect current conditions, temperature in °F, wind in mph, and six forecast rows
with local times and rain probabilities. Values change with the weather.

### Updating your version

Check the [release notes](https://github.com/myAI-2025/weather-mcp/releases) and
choose a published version. To replace the user-scope registration, first inspect
`claude mcp get weather` and save any custom settings you want to keep. Then run
the following commands, **replacing `0.1.2` with your chosen version** in the add command:

```bash
claude mcp remove --scope user weather
claude mcp add --scope user weather -- uvx myai-weather-mcp==0.1.2
claude mcp get weather
```

Removing the registration removes that client configuration, not your repository
or source files. If your existing registration is in local or project scope,
inspect that configuration before changing it; a same-name entry there may override
the user-scope entry.

Reconnect through `/mcp` or start a new Claude Code session after replacing it.
For Claude Desktop, change the version in its configuration's `args` and restart.

Refreshing uv's cache does **not** change a saved version pin. If a version that
is already published cannot be found, run the following with the version you selected:

```bash
uvx --refresh myai-weather-mcp==0.1.2
```

If the terminal stays blank without an error, the server is waiting for a client;
press Control+C, then reconnect your client. See [uv's tool guide](https://docs.astral.sh/uv/guides/tools/)
for more about running tools and selecting versions.

### Connection troubleshooting

- **No server named `weather`:** run the add command in step 2, then check again.
- **Failed to connect or another non-connected status:** inspect the command and
  arguments printed by `claude mcp get weather`. Try
  `uvx myai-weather-mcp==0.1.2` directly in your terminal and read any error.
  If it starts without an error and waits, press Control+C and reconnect through
  `/mcp`. A successful start checks that the package can launch; ask for weather
  to check the network too.
- **`uvx` not found:** install uv and reopen your terminal. If the terminal finds
  it but your client does not, find its full path with `command -v uvx`
  (macOS/Linux) or `where.exe uvx` (Windows PowerShell). Use that path in place of
  `uvx` in the registration or configuration; quote paths containing spaces.
- **Package download fails:** check your internet connection and the exact package
  name and version. If the selected release exists but uv cannot find it, use the
  cache-refresh command above. For `UnknownIssuer`, see the
  [certificate-error steps](#pypi-certificate-error-unknownissuer) below.
- **Connected, but tools are missing:** start a new Claude Code session or use
  `/mcp` to check whether `weather` is enabled and reconnect it.
- **A blank terminal after starting the server directly:** it is waiting for an
  MCP client. This is expected; press Control+C and use the client setup above.
- **Claude Code says “Not logged in”:** open `claude` and run `/login`.
- **Connected, but weather requests fail:** check the returned error and your
  internet connection. The server must reach Open-Meteo to retrieve weather.
- **Location not found:** try a well-known city name. An unknown place should
  return a readable error rather than a forecast.

### PyPI certificate error (`UnknownIssuer`)

If the terminal shows `invalid peer certificate: UnknownIssuer` while uvx fetches
from `pypi.org`, the package launcher cannot verify that HTTPS connection. This
happens before the weather server starts and may appear in your client as
`Connection closed` during initialization. Other connection errors can have
different causes.

Try using the certificates already trusted by your operating system:

```bash
uvx --system-certs myai-weather-mcp==0.1.2
```

This can help on a managed network whose certificate is in the system trust store.
It keeps certificate verification enabled. If the server starts and waits without
an error, press Control+C. To use the same option in Claude Code, follow the
[registration replacement steps](#updating-your-version), using this add command:

```bash
claude mcp add --scope user weather -- uvx --system-certs myai-weather-mcp==0.1.2
```

For Claude Desktop's uvx setup, change `args` to
`["--system-certs", "myai-weather-mcp==0.1.2"]`. Reconnect or restart your client,
then ask for weather to check the full connection. Use your selected package
version if it differs from this guide's pin.

If uvx does not recognize the flag, update uv using its installation method.
If certificate verification still fails, consult your network administrator and
[uv's certificate documentation](https://docs.astral.sh/uv/concepts/authentication/certificates/).
Keep verification enabled; do not use `--allow-insecure-host` to bypass the error.
If your existing setup works, no configuration change is needed.

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

With uv installed, paste this whole block into a **macOS/Linux terminal using
bash or zsh**. It downloads the pinned package if needed and works from any
folder; no clone or separate package installation is required. This shell example
is not PowerShell syntax.

It sends a small JSON-RPC exchange directly to the server:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"cli"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_weather","arguments":{"location":"Seattle"}}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_hourly_forecast","arguments":{"location":"Tokyo","hours":6}}}' \
  | uvx myai-weather-mcp==0.1.2
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

The quick start already runs the published package through uvx. The options below
are alternatives; you do not need to complete all of them.

Use `myai-weather-mcp` as the package and launch command throughout this guide.
`openmeteo-mcp` is an older compatibility alias for the same server.

**Run the published release with uv (recommended):**

```bash
uvx myai-weather-mcp==0.1.2
```

**Install a persistent command with [pipx](https://pipx.pypa.io/stable/installation/):**

```bash
pipx install myai-weather-mcp==0.1.2
myai-weather-mcp
```

Alternatively, install with `python3 -m pip install myai-weather-mcp==0.1.2`
inside an activated Python virtual environment.

**Run the source from GitHub with uv:**

```bash
uvx --from git+https://github.com/myAI-2025/weather-mcp myai-weather-mcp
```

This uses the repository's default branch, which may differ from the published release.

**Run a local clone (requires Git and Python 3.8+):**

```bash
git clone https://github.com/myAI-2025/weather-mcp
python3 weather-mcp/weather_mcp/server.py
```

Run the second command from the same folder where you ran `git clone`, or use
the script's full path. On Windows, use your Python launcher if it is named `python`
instead of `python3`.

All of these launch the server and wait for MCP input. A blank terminal is normal;
press Control+C to stop it before configuring a client.

## Configure a client

### Claude Code

Use the [quick start](#quick-start-claude-code) for the recommended uvx setup.
If you already registered `weather` there, no second registration is needed.

If you chose the persistent pipx installation instead, the alternative is:

```bash
claude mcp add --scope user weather -- myai-weather-mcp
```

For a local clone, replace the example path below with the script's actual full path:

```bash
claude mcp add --scope user weather -- python3 /path/to/weather-mcp/weather_mcp/server.py
```

When replacing an existing registration, inspect it first and follow
[Updating your version](#updating-your-version). Restart Claude Code or reconnect
via `/mcp`, then ask it to use `get_weather` or `get_hourly_forecast`.

### Claude Desktop

Install uv first, as described in the quick start. Edit `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`).
Add the `weather` entry under `mcpServers`, preserving any other servers already there:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": ["myai-weather-mcp==0.1.2"]
    }
  }
}
```

If Desktop cannot find uvx, replace `"uvx"` with its full path from `command -v uvx`
(macOS) or `where.exe uvx` (Windows). In JSON, Windows backslashes must be doubled,
for example `"C:\\Users\\YourName\\.local\\bin\\uvx.exe"`; use your actual path.

If you installed the package with pipx instead, use `"command": "myai-weather-mcp"`
(or its full path) and omit `args`.

Quit and reopen Claude Desktop, then ask it to use the weather tools.
The Desktop configuration is an alternative setup; the end-to-end client checks
for this guide were performed in Claude Code.

### Any other MCP client

Configure a stdio server with command `uvx` and argument
`myai-weather-mcp==0.1.2`. With a persistent installation, the command can instead
be `myai-weather-mcp`. The client launches the process and exchanges JSON-RPC 2.0
over its stdin/stdout. See **How it works** below.

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
