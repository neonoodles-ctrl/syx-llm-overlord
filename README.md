# Syx LLM Overlord

Watch LLMs play Songs of Syx -- a fantasy city-builder with thousands of simulated citizens.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Songs of Syx (Java)                 │
│  ┌─────────────────────────────────────────────┐    │
│  │         syx-llm-mod (Java Mod)              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐ │    │
│  │  │ State    │  │ Command  │  │ HTTP API  │ │    │
│  │  │ Reader   │  │ Executor │  │ :47823    │ │    │
│  │  └──────────┘  └──────────┘  └───────────┘ │    │
│  └─────────────────────┬───────────────────────┘    │
└────────────────────────┼────────────────────────────┘
                         │ HTTP (localhost:47823)
┌────────────────────────┼────────────────────────────┐
│              Python Bridge Service                   │
│  ┌──────────┐  ┌──────┴──────┐  ┌───────────────┐  │
│  │ Game API │  │  LLM Brain  │  │ Command Queue │  │
│  │ Client   │──│  (OpenAI)   │──│  & Validator  │  │
│  └──────────┘  └─────────────┘  └───────────────┘  │
│  ┌──────────────────────────────────────────────┐   │
│  │          FastAPI Server :8472                 │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │ WebSocket + REST
┌─────────────────────┼───────────────────────────────┐
│           Web Dashboard :3847                       │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ Live    │ │ LLM      │ │ Command  │ │ Stats  │  │
│  │ State   │ │ Thoughts │ │ History  │ │ Charts │  │
│  └─────────┘ └──────────┘ └──────────┘ └────────┘  │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. `syx-llm-mod/` -- Java Mod (runs inside the game)
- Implements `script.SCRIPT` interface to hook into game lifecycle
- Reads game state each tick: population, resources, happiness, rooms, military, diplomacy
- Exposes HTTP API on `localhost:47823` using JDK's built-in `com.sun.net.httpserver`
- Accepts commands: build, demolish, set_policy, recruit, trade, etc.
- Thread-safe state snapshots via `synchronized` blocks

### 2. `bridge/` -- Python Bridge Service
- FastAPI service on `localhost:8472`
- Polls the mod's HTTP API for game state
- Formats state into LLM prompts with game context
- Sends to configurable LLM backend (OpenAI, Ollama, Anthropic)
- Parses structured JSON commands from LLM responses
- Validates and queues commands back to the mod
- Rate-limits decisions (configurable tick interval)
- Logs all LLM reasoning and decisions

### 3. `dashboard/` -- Web Dashboard
- Single-page app served by the bridge service
- WebSocket for real-time updates
- Shows: current game state, LLM reasoning, command history, population/resource charts
- Dark fantasy theme matching the game's aesthetic

## Quick Start

```bash
/home/hermesprime/GAMES/Neonoodles-ctrl/syx/syx
```

One launcher starts the game (HiDPI fix), waits for the LLM Overlord mod, runs the OpenRouter bridge, and opens the dashboard at http://localhost:3847.

In game (SOS Launcher window):

1. **Launch** — left button under the SONGS OF SYX title
2. **LLM Overlord** — click in the mods list (should show **1** when selected; pre-enabled in settings)
3. **Play** — top-right

Then in the game main menu:

4. **play** — right-side menu
5. **random game** — second section
6. **go!** — bottom (LLM Overlord auto-loads; no Scripts checkbox needed)

Dashboard opens at http://localhost:3847 once the mod API is live.

Stop: `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/scripts/stop-syx.sh`

See `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/README.md` for full docs.

## Configuration

Copy `bridge/config.example.yaml` to `bridge/config.yaml`:

```yaml
llm:
  provider: openai        # openai, ollama, anthropic
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}
  base_url: null          # for Ollama: http://localhost:11434/v1
  max_tokens: 2048
  temperature: 0.7

game:
  mod_url: http://localhost:47823
  poll_interval_seconds: 5
  command_rate_limit: 3   # max commands per tick

dashboard:
  port: 3847
  ws_enabled: true
```

## LLM Command Format

The LLM outputs structured JSON decisions:

```json
{
  "reasoning": "Population is growing but food production is lagging. Need more farms.",
  "mood": "cautious",
  "commands": [
    {"action": "build", "target": "room_farm", "x": 45, "y": 32, "params": {"size": "3x3"}},
    {"action": "set_policy", "target": "food_rationing", "params": {"value": "normal"}}
  ]
}
```

## License

MIT
