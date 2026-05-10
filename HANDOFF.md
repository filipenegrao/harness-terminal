# HANDOFF.md — Harness

> Current project state for the orchestrator and any agent picking up work.
> Updated at the end of each session or completed cycle.

---

## Project summary

Harness is a bento-grid terminal workspace for multi-agent AI workflows.
One Tauri 2 desktop app with one xterm.js PTY pane per agent, a Python
WebSocket sidecar for signal parsing, and a structured signal protocol
(AGENTS.md) that any LLM can follow.

## Last session — 2026-05-10

**What was done:**
- Full project scaffold: Tauri 2 + React 18 + Vite + xterm.js 5 + Zustand
- Python sidecar: `parser.py` (fully implemented + tested), `state.py`,
  `loader.py`, `server.py`, `watcher.py` stub
- PTY bridge spike: `pty.rs` — `PtyRegistry`, `spawn_pty`, reader thread →
  Tauri event, `pty_write` command
- `usePtyTerminal` React hook: xterm init + `listen('pty-data-{id}')` + `invoke('pty_write')`
- `cargo check` and `tsc --noEmit` both pass clean
- Git repo initialized, remote added: `git@github.com:filipenegrao/harness-terminal.git`
- Rust updated from 1.82 → 1.95 (required for Tauri 2 deps)

**Commit:** `364ef73`

---

## Current state

| Layer | Status |
|-------|--------|
| Scaffold | ✅ Complete |
| CSS tokens + bento layout | ✅ Complete |
| Zustand store + mock data | ✅ Complete |
| WebSocket hook (sidecar) | ✅ Skeleton (reconnects, dispatches) |
| Python parser.py | ✅ Fully implemented |
| Python state/loader/server | ✅ Implemented (not battle-tested) |
| PTY bridge (Rust ↔ xterm.js) | ✅ Spiked — read/write path works |
| Auto-spawn agents on launch | ❌ Not wired |
| PTY stdout → Python sidecar | ❌ Not wired |
| PTY resize | ❌ Not implemented |
| Real PTY sessions rendering | ❌ Not end-to-end tested |
| File tree (watchdog) | ❌ Phase 2 |
| Git branch in status bar | ❌ Phase 2 |

---

## Next task

**Wire the launch sequence:** read `harness.toml` on app start, spawn one
PTY per agent via `pty_spawn`, connect the Zustand store to real WebSocket
state from the Python sidecar.

Acceptance criteria:
1. `npm run tauri dev` + `python harness/main.py` starts the app
2. All 4 agents from `harness.toml` have live PTY panes
3. Typing in an agent pane sends input to the PTY
4. PTY output renders correctly in xterm.js
5. Python sidecar receives stdout and parses signals

---

## Known risks / open questions

1. **PTY → sidecar IPC** — mechanism not chosen. Named pipe vs. stdin mux.
   See spec section 4.5.
2. **xterm resize** — `fitAddon.fit()` must be called on pane resize.
   Tauri window resize events need to propagate correctly.
3. **Sidecar bundling** — PyInstaller binary size; test early before release.

---

## Workflow

This project uses the orchestrator cycle in `_prompts/orchestrator.md`.
Each feature task goes through: Builder → QA → Security before merge.
