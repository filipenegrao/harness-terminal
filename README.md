# Harness

Bento-grid terminal workspace for multi-agent AI workflows. One screen replaces five windows.

Each agent gets a named PTY pane with live status, token usage, and handoff signals. An isolated user terminal sits alongside, unaffected by agent sessions.

## Prerequisites

| Tool | Version |
|------|---------|
| Rust + Cargo | 1.80+ (`rustup`) |
| Node | 20+ |
| Python | 3.11+ (3.12 recommended) |
| Tauri CLI | installed via `npm run tauri` |

## Dev setup

### 1. Python sidecar

```bash
cd harness
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                 # starts ws://127.0.0.1:7373
```

### 2. Tauri app

```bash
# from project root
npm install
npm run tauri dev
```

The Vite dev server starts on port 1420; Tauri opens the window automatically.

## Project config — harness.toml

Place `harness.toml` in the root of your project (not the Harness repo).

```toml
[project]
name = "my-project"
working_dir = "."
agents_md = "./AGENTS.md"

[[agents]]
id = "orchestrator"
name = "Orchestrator"
icon = "ti-adjustments"
model = "claude-sonnet-4"
command = "claude --agent orchestrator"
tokens_max = 100000
color = "amber"             # amber | blue | purple | green

[[agents]]
id = "builder"
name = "Builder"
icon = "ti-hammer"
model = "claude-sonnet-4"
command = "claude --agent builder"
tokens_max = 100000
color = "blue"

[layout]
context_panel_width = 220   # px
user_terminal_height = 100  # px
grid_columns = 2
```

### Agent fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, used in `NEXT:` signals |
| `name` | string | Display name in pane header |
| `icon` | string | Tabler icon class (e.g. `ti-hammer`) |
| `model` | string | Model name shown in pane footer |
| `command` | string | Shell command to spawn the agent |
| `tokens_max` | int | Context window size for token bar |
| `color` | string | Accent color: `amber`, `blue`, `purple`, `green` |

## Signal protocol

Agents emit structured signals in their stdout. See [AGENTS.md](./AGENTS.md) for the full spec.

```
[STATUS:working] [NEXT:qa] [TOKENS:48234]
[TASK:Implementing PTY bridge]
```

## Architecture

```
Tauri (Rust)  ←→  Webview (React + xterm.js)
     ↕ IPC
  PTY per agent  →  Python sidecar (parser + state)  →  WebSocket  →  Zustand store
```

See [CLAUDE.md](./CLAUDE.md) for implementation details.

## Build

```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/
```
