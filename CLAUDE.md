# Harness — Claude Code Context

Agentic terminal workspace. Bento-grid layout with one PTY pane per agent + isolated user terminal.

## Architecture

| Layer | Role |
|-------|------|
| Tauri 2 (Rust) | Window, PTY spawning via `portable-pty`, sidecar process management |
| React + xterm.js | UI — one `Terminal` instance per `AgentPane` |
| Python sidecar | Signal parsing, WebSocket broadcast on `ws://127.0.0.1:7373` |
| Zustand store | Client-side state — updated from WebSocket, read by components |

**State flow:** PTY stdout → sidecar parser → WebSocket → Zustand store → React re-render (surgical — never re-renders xterm.js instances).

## Signal protocol

Defined in `AGENTS.md`. Parser in `harness/parser.py`. Do not modify signal format without updating both files.

## Critical constraint — xterm.js

xterm.js instances **must never be unmounted/remounted** on state updates. Only header, footer, and overlay elements update reactively. Use refs; attach xterm once on mount with empty deps `[]`.

## PTY bridge (spiked — not wired to real agents yet)

`src-tauri/src/pty.rs` — `PtyRegistry` + reader thread → Tauri events per agent.

**Data flow (implemented):**
- `pty_spawn(agentId, command)` — spawns PTY, starts reader thread
- Reader thread emits `pty-data-{agent_id}` events with `Vec<u8>` payload
- `usePtyTerminal` hook in React listens and writes `new Uint8Array(data)` to xterm
- Keyboard input: xterm `onData` → `invoke('pty_write', {agentId, data})`

**Not yet wired:**
- Commands in `harness.toml` are not yet auto-spawned on app start
- Python sidecar not yet receiving PTY stdout (named pipe / stdin mux not implemented)
- Resize (`pty_resize`) not yet implemented — deferred to Phase 2

## Dev setup

```bash
# Terminal 1 — Python sidecar
cd harness && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py

# Terminal 2 — Tauri dev
npm install
npm run tauri dev
```

## File map

```
src/types.ts              — AgentState, ProjectState, Signal interfaces
src/store/agentStore.ts   — Zustand store + mock data
src/hooks/useWebSocket.ts — WS subscriber, dispatches to store
src/components/
  BentoGrid.tsx           — grid layout shell
  AgentPane.tsx           — xterm.js pane + header/footer
  UserTerminal.tsx        — isolated user pane
  ContextPanel.tsx        — token bars, last/next banners
  StatusStrip.tsx         — bottom bar
harness/
  parser.py               — fully implemented signal parser
  state.py                — AgentState + ProjectState dataclasses
  loader.py               — harness.toml reader
  server.py               — WebSocket broadcast server
  watcher.py              — file watcher stub (Phase 2)
src-tauri/src/
  pty.rs                  — PTY spawn stub (spike first)
  sidecar.rs              — sidecar process manager stub
```
