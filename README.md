# Harness

> Bento-grid terminal workspace for multi-agent AI workflows.

One screen replaces five windows. Each AI agent gets its own named PTY pane
with live status, token usage, and handoff signals surfaced at a glance.
An isolated user terminal sits alongside, unaffected by agent sessions.

---

## What it does

- **Bento layout** — context panel + 2×2 agent grid + user terminal, driven by `harness.toml`
- **Live status** — status dot per pane (working / idle / done / error) from structured signals
- **Token bars** — per-agent context usage in the context panel, updated in real time
- **Signal protocol** — agents emit structured `[STATUS] [NEXT] [TOKENS]` signals; Harness parses them without modifying the agent
- **Isolated user terminal** — clean PTY for manual commands, visually distinct (green cursor, "you" badge)
- **Model-agnostic** — works with Claude, GPT-4, Gemini, or any locally-hosted model

## Stack

| Layer | Technology |
|-------|-----------|
| Desktop shell | Tauri 2 (Rust) |
| UI | React 18 + Vite (TypeScript) |
| Terminal rendering | xterm.js 5 |
| State | Zustand |
| Signal parsing + state bus | Python 3.12 sidecar |
| Config | `harness.toml` (TOML) |
| Signal protocol | `AGENTS.md` (plain text) |

## Prerequisites

| Tool | Version |
|------|---------|
| Rust + Cargo | 1.85+ (`rustup`) |
| Node | 20+ |
| Python | 3.11+ |

## Dev setup

```bash
# 1. Python sidecar
cd harness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py          # starts ws://127.0.0.1:7373

# 2. Tauri app (new terminal)
cd ..
npm install
npm run tauri dev
```

## Project config — harness.toml

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
color = "amber"           # amber | blue | purple | green

[layout]
context_panel_width = 220
user_terminal_height = 100
grid_columns = 2
```

## Signal protocol

Agents emit structured signals in their stdout. Harness parses them without
any modifications to the agent runtime.

```
[STATUS:working] [NEXT:qa] [TOKENS:48234]
[TASK:Implementing PTY bridge]
[WARN:Context window at 85%]
```

Full spec in [AGENTS.md](./AGENTS.md).

## Architecture

```
Tauri (Rust)
  PTY per agent (portable-pty)
    → reader thread → emit("pty-data-{id}")
      → React usePtyTerminal → xterm.js

  invoke("pty_write") ← xterm.js onData ← keyboard input

Python sidecar
  ws://127.0.0.1:7373
    → WebSocket → Zustand store → React re-render
    (surgical: only header/footer/overlay update — xterm never remounts)
```

## Development workflow

This project uses a structured Builder → QA → Security cycle.
See `_prompts/orchestrator.md` for the orchestration protocol and
`HANDOFF.md` for current project state.

## Status

See [STATUS.json](./STATUS.json) for feature-level status and
[docs/session-log.md](./docs/session-log.md) for session history.

Current phase: **MVP (Phase 1)** — PTY bridge spiked, launch sequence next.

## Build

```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/
```

## License

MIT
