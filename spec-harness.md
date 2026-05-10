# Product Spec: Harness

> A bento-grid terminal workspace for multi-agent AI development workflows, with structured signal parsing, per-agent context tracking, and an isolated user terminal.

**Version:** 1.0 draft  
**Date:** 2026-05-10  
**Author:** Filipe Negrão  

---

## 1. Problem & Vision

### 1.1 Problem Statement

Developers running multi-agent AI workflows (Claude Code, OpenAI Agents, custom LLM pipelines) today manage them by opening 4–6 separate terminal windows in VS Code or iTerm2, manually switching between them to track agent state. There is no unified view of what each agent is doing, how much context it has consumed, which agent finished last, or what comes next. The cognitive overhead of context-switching between windows breaks flow and increases the chance of missing agent errors or handoff signals.

Existing terminal multiplexers (tmux, Zellij) solve the split-pane problem but provide no semantic layer: they treat all output as undifferentiated text streams with no awareness of agent identity, status, or inter-agent dependencies.

### 1.2 Target Audience

**Primary:** Solo developers and small teams running agentic AI workflows — coding agents, font engineering pipelines, document automation, or any task decomposed into specialized sub-agents. Technically proficient; comfortable with CLIs and config files; frustrated by the friction of window management during agentic sessions.

**Secondary:** AI engineers building and debugging multi-agent systems who need observability into agent behavior in real time.

### 1.3 Value Proposition

Harness gives every agent its own named, observable pane — with status, token usage, and handoff signals surfaced at a glance — while keeping the user's own terminal isolated and always accessible. One screen replaces five windows.

### 1.4 Competitive Landscape

| Tool | What it does | Gap |
|------|-------------|------|
| tmux / Zellij | Terminal multiplexer, splits, sessions | No agent awareness, no semantic layer |
| VS Code Terminal | Integrated terminals with tabs | No status indicators, no cross-agent state |
| Warp | AI-augmented terminal | Single-user focus, no multi-agent orchestration |
| OpenHands / SWE-agent UI | Web UI for single coding agent | Not composable, not local-first |

Harness's differentiator is the **harness layer**: a structured protocol (AGENTS.md) that any LLM can follow to emit parseable signals, making the terminal aware of agent intent rather than just agent output.

---

## 2. Functionalities & User Stories

### 2.1 Core Features

**F1 — Bento Grid Layout**  
A configurable grid of terminal panes. Default layout: context panel (left, full height) + 2×2 agent grid (right) + user terminal (bottom right, spanning both columns). Layout defined in `harness.toml`.

**F2 — Agent Panes**  
Each agent pane embeds a full PTY session rendering via xterm.js. Panes have a header (icon, name, status dot) and footer (model, context size). Status dot reflects the agent's last emitted `[STATUS]` signal: working (amber), idle (gray), done (green), error (red).

**F3 — User Terminal**  
An isolated PTY pane visually distinct from agent panes (green cursor, `❯` prompt, "you" badge). Shares the project working directory but runs in a clean environment without agent context variables. Not connected to the harness signal parser.

**F4 — Context Panel**  
Left panel showing: token usage bars per agent (from `[TOKENS]` signals), project file tree with modified indicators, last-completed-agent banner, next-step banner. Read-only — no terminal.

**F5 — Harness Signal Protocol**  
A structured signal format defined in `AGENTS.md`, loaded into every agent's context. The harness parser reads each agent's PTY stream and extracts signals to update UI state. Protocol is model-agnostic plain text.

**F6 — AGENTS.md Loader**  
At session start, Harness reads `AGENTS.md` from the project root and injects its content as a prefix to each agent's system prompt or context file. Eliminates per-agent manual setup.

**F7 — Bottom Status Strip**  
Single-row bar across the bottom: project name, agent counts by status, last-completed agent + action, next-step agent + action.

**F8 — Project Configuration**  
`harness.toml` at project root defines agents (name, icon, model, command, color), layout, and working directory. Harness reads this on launch.

### 2.2 User Stories

- **As a developer**, I want to see all my agents in one screen so that I don't lose track of which is working and which is waiting.
- **As a developer**, I want each agent's status (working / idle / done / error) shown visually so that I can spot blockers without reading every line of output.
- **As a developer**, I want to know which agent just finished and what it did so that I can decide whether to intervene before the next handoff.
- **As a developer**, I want to run my own commands in a clean terminal so that I don't accidentally pollute agent sessions with manual commands.
- **As a developer**, I want to see each agent's token usage at a glance so that I know when a context window is getting full.
- **As a developer**, I want to define my agent setup once in a config file so that I can launch the full workspace with a single command.
- **As a developer**, I want the signal protocol loaded automatically into every agent so that I don't manually configure each one.
- **As a developer using multiple models**, I want the protocol to be model-agnostic plain text so that it works with Claude, GPT-4, Gemini, or any locally-hosted model.

### 2.3 User Flows

**Flow 1 — Project Launch**
1. User runs `harness` in a project directory.
2. Harness reads `harness.toml` → resolves agent definitions.
3. Harness reads `AGENTS.md` → loads signal protocol.
4. Harness spawns one PTY per agent, injecting AGENTS.md content as context prefix where applicable.
5. Bento layout renders; each agent pane shows the agent's startup output.
6. User terminal spawns in the same working directory with a clean environment.
7. Context panel initializes with empty token bars and the project file tree.

**Flow 2 — Agent Emits Signal**
1. Agent prints `[STATUS:working] [NEXT:qa] [TOKENS:48234]` to stdout.
2. Harness PTY reader captures the line for that agent's stream.
3. Parser extracts fields; state store updates agent record.
4. Context panel re-renders token bar; status dot updates; bottom strip updates last/next banners.
5. If `[NEXT]` agent is currently idle, its pane header pulses briefly.

**Flow 3 — User Runs Independent Command**
1. User focuses the user terminal pane (click or keyboard shortcut).
2. User types a command (e.g. `python export.py --check-only`).
3. Command runs in the isolated PTY; output appears in the user terminal.
4. No signals are parsed from this pane; no agent state is affected.

**Flow 4 — Agent Context Warning**
1. An agent's token count exceeds 80% of the configured max.
2. Context panel renders the bar in amber instead of the agent's default color.
3. Bottom strip shows a warning badge next to that agent's name.
4. At 95%, the bar turns red and the pane header shows a warning icon.

### 2.4 Out of Scope (v1)

- Agent-to-agent messaging or programmatic task delegation (orchestration logic stays in the agents themselves)
- Cloud sync or remote sessions
- Windows support (macOS and Linux only)
- Built-in AI chat interface (Harness is a terminal wrapper, not an AI client)
- Plugin marketplace
- Agent log persistence / searchable history
- Authentication or multi-user support

---

## 3. Data Model & Technical Architecture

### 3.1 Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Desktop shell | **Tauri 2** (Rust) | Native window, PTY management via `portable-pty`, low memory, ships as a single binary |
| UI framework | **React 18** + Vite | Component model fits the bento grid; fast HMR during development |
| Terminal rendering | **xterm.js 5** | Battle-tested, GPU-accelerated, handles ANSI/VT correctly |
| Harness backend | **Python 3.12** (Tauri sidecar) | Matches Filipe's existing stack; handles signal parsing, state aggregation, file watching |
| State bus | **Local WebSocket** (Python `websockets`) | Sidecar exposes `ws://127.0.0.1:7373`; Tauri webview connects on launch |
| Config format | **TOML** (`harness.toml`) | Simple, readable, no surprises |
| Protocol definition | **AGENTS.md** (Markdown) | Plain text, versionable, model-agnostic |
| File watching | **watchdog** (Python) | Monitors project files for modified indicators in context panel |
| Styling | **CSS custom properties** | No framework; theme tokens defined in `base.css` |

### 3.2 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Tauri App (Rust)                                   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Webview (React + xterm.js)                 │   │
│  │                                             │   │
│  │  ┌──────────┐  ┌──────┐  ┌──────┐  ┌────┐  │   │
│  │  │ Context  │  │ Agt1 │  │ Agt2 │  │... │  │   │
│  │  │  Panel   │  │ Pane │  │ Pane │  │    │  │   │
│  │  └──────────┘  └──────┘  └──────┘  └────┘  │   │
│  │                ┌──────────────────────────┐  │   │
│  │                │    User Terminal Pane    │  │   │
│  │                └──────────────────────────┘  │   │
│  └──────────────────┬──────────────────────────┘   │
│                     │ Tauri IPC (invoke/emit)       │
│  ┌──────────────────┴──────────────────────────┐   │
│  │  Rust Core                                  │   │
│  │  - PTY spawning (portable-pty)              │   │
│  │  - PTY I/O bridge → WebSocket forward       │   │
│  │  - Sidecar process manager                  │   │
│  └──────────────────┬──────────────────────────┘   │
└─────────────────────┼───────────────────────────────┘
                      │ stdin/stdout (sidecar IPC)
┌─────────────────────┴───────────────────────────────┐
│  Python Sidecar (harness/)                          │
│                                                     │
│  ┌─────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │ PTY Stream  │  │ Signal Parser │  │  State   │  │
│  │  Listener   │→ │  (regex/      │→ │  Store   │  │
│  │  per agent  │  │   AGENTS.md)  │  │  (dict)  │  │
│  └─────────────┘  └───────────────┘  └────┬─────┘  │
│                                           │         │
│  ┌─────────────────────────────────────────┴──────┐ │
│  │  WebSocket Server (ws://127.0.0.1:7373)        │ │
│  │  Broadcasts state diffs to Webview             │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │ File Watcher│  │ AGENTS.md Loader             │  │
│  │ (watchdog)  │  │ Reads + injects on session   │  │
│  └─────────────┘  │ start per agent type         │  │
│                   └─────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Data flow summary:**
1. Tauri spawns PTYs (one per agent + user terminal) via `portable-pty`.
2. Each agent PTY's output is forwarded to the Python sidecar over a named pipe / stdin multiplexer.
3. The sidecar's signal parser extracts structured signals from the stream.
4. Parsed state is broadcast over the local WebSocket to the React UI.
5. The UI updates the relevant pane header, context panel bars, and status strip — without re-rendering the xterm.js instance (state updates are surgical).

### 3.3 Data Model

**Agent State (in-memory, Python sidecar)**

| Field | Type | Source |
|-------|------|--------|
| `id` | string | `harness.toml` |
| `name` | string | `harness.toml` |
| `icon` | string | `harness.toml` |
| `model` | string | `harness.toml` |
| `status` | enum: `working\|idle\|done\|error` | `[STATUS]` signal |
| `next_agent` | string \| null | `[NEXT]` signal |
| `tokens_used` | int | `[TOKENS]` signal |
| `tokens_max` | int | `harness.toml` |
| `last_task` | string \| null | `[TASK]` signal |
| `last_warn` | string \| null | `[WARN]` signal |
| `updated_at` | float (unix ts) | parser |

**Project State (in-memory, Python sidecar)**

| Field | Type | Source |
|-------|------|--------|
| `project_name` | string | `harness.toml` / dir name |
| `working_dir` | string | `harness.toml` |
| `git_branch` | string | `git rev-parse` on launch |
| `modified_files` | `list[str]` | watchdog |
| `last_done` | `{agent, task}` | latest `STATUS:done` signal |
| `next_step` | `{agent, task}` | latest `NEXT` signal |
| `agents` | `dict[str, AgentState]` | signal parser |

**harness.toml schema**

```toml
[project]
name = "afya-sans-v2"
working_dir = "."
agents_md = "./AGENTS.md"

[[agents]]
id = "orchestrator"
name = "Orchestrator"
icon = "ti-adjustments"
model = "claude-sonnet-4"
command = "claude --agent orchestrator"
tokens_max = 100000
color = "amber"

[[agents]]
id = "builder"
name = "Builder"
icon = "ti-hammer"
model = "claude-sonnet-4"
command = "claude --agent builder"
tokens_max = 100000
color = "blue"

[[agents]]
id = "qa"
name = "QA"
icon = "ti-checklist"
model = "claude-sonnet-4"
command = "claude --agent qa"
tokens_max = 100000
color = "purple"

[[agents]]
id = "security"
name = "Security"
icon = "ti-shield-check"
model = "claude-sonnet-4"
command = "claude --agent security"
tokens_max = 100000
color = "green"

[layout]
context_panel_width = 220
user_terminal_height = 100
grid_columns = 2
```

**AGENTS.md signal protocol (canonical)**

```markdown
# AGENTS.md — Harness Signal Protocol v1

Emit structured signals on any line where your status changes.
Signals are parsed by the Harness terminal; follow the format exactly.

## Required signal (emit whenever status changes)
[STATUS:working|idle|done|error] [NEXT:agent_id|none] [TOKENS:n]

## Optional signals (emit as needed)
[TASK:short description of current task]
[WARN:message for orchestrator]
[HANDOFF:agent_id reason for handoff]

## Rules
- Signals on their own line — no prose on the same line
- NEXT:none when there is no clear handoff
- STATUS:error must include a WARN signal
- Do not emit signals inside code blocks
- TOKEN count is total tokens used in this session
```

### 3.4 Authentication & Authorization

None. Harness is a local desktop tool — no accounts, no network auth, no remote access. The Python WebSocket server binds to `127.0.0.1` only.

### 3.5 Integrations

| Integration | Purpose | Method |
|-------------|---------|--------|
| Claude Code | Primary agent runtime | Subprocess / PTY |
| OpenAI / Gemini APIs | Alternative agent models | Subprocess (model-agnostic) |
| Git | Branch name in status bar, modified file detection | `git` CLI subprocess |
| watchdog (Python) | File tree modification tracking | Library |
| portable-pty (Rust) | Cross-platform PTY management | Tauri Rust dependency |

### 3.6 Infrastructure & Deployment

**Local desktop app only.** No server-side infrastructure.

- **Distribution:** Tauri produces a `.dmg` (macOS) and `.AppImage` / `.deb` (Linux). No app store.
- **Python sidecar:** Bundled as a PyInstaller binary inside the Tauri app bundle. No Python installation required for end users. For development, a local venv is used.
- **Updates:** Manual download or GitHub Releases. Auto-update via Tauri's built-in updater in Phase 2.
- **Development environments:** `dev` (local, hot-reload) and `release` (bundled sidecar). No staging.

---

## 4. MVP Scope, Roadmap & Estimates

### 4.1 MVP Definition

A working local app that: (1) reads `harness.toml` and `AGENTS.md`, (2) spawns PTYs for all defined agents and the user terminal, (3) renders the bento layout with xterm.js panes, (4) parses `[STATUS]` / `[NEXT]` / `[TOKENS]` signals and updates the context panel and status dots in real time.

Everything else — file tree, git integration, keyboard shortcuts, multi-model injection, warnings — is Phase 2.

### 4.2 MVP Feature Matrix

| Feature | Priority | Complexity | MVP |
|---------|----------|------------|-----|
| harness.toml config parsing | P0 | Low | ✅ |
| AGENTS.md loading + display | P0 | Low | ✅ |
| PTY spawning per agent | P0 | High | ✅ |
| xterm.js rendering per pane | P0 | Medium | ✅ |
| Bento grid layout | P0 | Medium | ✅ |
| Signal parser (STATUS/NEXT/TOKENS) | P0 | Medium | ✅ |
| WebSocket state bus | P0 | Medium | ✅ |
| Context panel — token bars | P0 | Low | ✅ |
| Status dots (working/idle/done/error) | P0 | Low | ✅ |
| Last done / next step banners | P0 | Low | ✅ |
| Bottom status strip | P0 | Low | ✅ |
| User terminal (isolated PTY) | P0 | Medium | ✅ |
| Pane icons + color theming | P1 | Low | ✅ |
| Context panel — file tree | P1 | Medium | ❌ |
| Git branch display | P1 | Low | ❌ |
| Modified files indicator | P1 | Medium | ❌ |
| TASK / WARN / HANDOFF signals | P1 | Low | ❌ |
| Token warning threshold (80% / 95%) | P1 | Low | ❌ |
| Keyboard shortcuts (pane focus) | P1 | Medium | ❌ |
| AGENTS.md auto-injection per model | P2 | High | ❌ |
| Multi-model context injection | P2 | High | ❌ |
| Session log persistence | P2 | Medium | ❌ |
| Auto-updater | P2 | Low | ❌ |
| Custom themes | P3 | Low | ❌ |
| Plugin system | P3 | High | ❌ |

### 4.3 Roadmap

**Phase 1 — MVP** (4–6 weeks, solo dev)
- Tauri + React scaffold with Vite
- Python sidecar with WebSocket server
- PTY spawning + xterm.js per pane
- Signal parser for STATUS / NEXT / TOKENS
- Bento layout: context panel, agent panes, user terminal
- harness.toml config reader
- AGENTS.md loader (reads and displays in context panel)
- Status dots, token bars, last/next banners, bottom strip

**Phase 2 — Useful** (3–4 weeks post-MVP)
- File tree with modified indicators (watchdog)
- Git branch in status bar
- TASK, WARN, HANDOFF signal support
- Token warning thresholds with color change
- Keyboard shortcuts for pane focus (cmd+1..5)
- AGENTS.md auto-injection for Claude Code agents
- Session start/end timestamps per agent

**Phase 3 — Polished** (future)
- Multi-model context injection (OpenAI / Gemini system prompt prefix)
- Session log persistence + searchable history
- Agent pane drag-to-resize
- Auto-updater via GitHub Releases
- Configurable layout presets (2 agents, 4 agents, 6 agents)
- Optional plugin system for custom signal parsers

### 4.4 Effort Estimates

| Phase | Estimated Effort | Key Risks |
|-------|-----------------|-----------|
| Phase 1 — MVP | 4–6 weeks (solo, part-time) | PTY/xterm.js integration complexity on macOS; Tauri sidecar process management |
| Phase 2 — Useful | 3–4 weeks | File watcher performance on large repos; AGENTS.md injection reliability across models |
| Phase 3 — Polished | 4–8 weeks | Multi-model testing matrix; plugin API design |

**Biggest single risk:** PTY ↔ xterm.js bridging in Tauri. The `portable-pty` crate handles PTY creation, but piping PTY output through the Tauri IPC to xterm.js in the webview requires careful backpressure management. Spike this first in Phase 1 before building anything else.

**Second risk:** Python sidecar bundling via PyInstaller. Binary size can balloon; test the bundled binary early.

### 4.5 Open Questions

1. **Sidecar IPC mechanism** — Named pipe vs stdin/stdout multiplexer for routing multiple agent streams from Tauri Rust to Python sidecar. Evaluate performance with 4+ concurrent agents during the PTY spike.
2. **AGENTS.md injection for Claude Code** — Claude Code reads `CLAUDE.md` automatically. The cleanest injection path may be a `@import ./AGENTS.md` line that Harness writes into a temporary `CLAUDE.md` wrapper on session start, rather than passing as CLI arg.
3. **xterm.js pane resize on bento drag** — xterm.js requires explicit `fit()` calls on resize. Need to evaluate whether Tauri's window resize events propagate correctly to all pane instances.
4. **PTY environment isolation for user terminal** — Determine the minimal env-var set that should be stripped for the user terminal (agent IDs, CLAUDE_CONTEXT_FILE, etc.) without breaking common shell aliases.
5. **Signal reliability at high output rate** — Agents that produce high-volume output (e.g. compilation logs) may buffer or delay signals. Evaluate whether signals should be searched on a fixed-interval scan rather than line-by-line to avoid missed signals on partial lines.

---

## Appendix A — Project Structure

```
harness/
├── src-tauri/              # Rust / Tauri core
│   ├── src/
│   │   ├── main.rs         # Tauri app entry
│   │   ├── pty.rs          # PTY spawning + I/O bridge
│   │   └── sidecar.rs      # Python sidecar process manager
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                    # React UI (Vite)
│   ├── components/
│   │   ├── BentoGrid.tsx
│   │   ├── AgentPane.tsx   # xterm.js instance + header/footer
│   │   ├── UserTerminal.tsx
│   │   ├── ContextPanel.tsx
│   │   └── StatusStrip.tsx
│   ├── store/
│   │   └── agentStore.ts   # Zustand store, updated from WebSocket
│   ├── App.tsx
│   └── base.css            # Design tokens
├── harness/                # Python sidecar
│   ├── main.py             # Entry point, WebSocket server
│   ├── parser.py           # Signal regex parser
│   ├── state.py            # AgentState + ProjectState dataclasses
│   ├── loader.py           # AGENTS.md + harness.toml reader
│   ├── watcher.py          # watchdog file tree monitor
│   └── requirements.txt
├── AGENTS.md               # Signal protocol (project-level)
├── harness.toml            # Project config (project-level)
└── README.md
```

## Appendix B — Signal Parser Reference

```python
# harness/parser.py
import re
from dataclasses import dataclass, field
from typing import Optional

REQUIRED = re.compile(
    r'\[STATUS:(?P<status>working|idle|done|error)\]'
    r'(?:\s+\[NEXT:(?P<next>[\w]+|none)\])?'
    r'(?:\s+\[TOKENS:(?P<tokens>\d+)\])?'
)

OPTIONAL = {
    'task':    re.compile(r'\[TASK:(?P<value>[^\]]{1,120})\]'),
    'warn':    re.compile(r'\[WARN:(?P<value>[^\]]{1,240})\]'),
    'handoff': re.compile(r'\[HANDOFF:(?P<target>\w+)\s+(?P<reason>[^\]]{1,120})\]'),
}

def parse_line(agent_id: str, line: str) -> Optional[dict]:
    m = REQUIRED.search(line)
    if not m:
        return None
    result = {'agent_id': agent_id, **m.groupdict()}
    for key, pat in OPTIONAL.items():
        om = pat.search(line)
        if om:
            result[key] = om.groupdict()
    return result
```
