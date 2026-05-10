# Session Log

---

## 2026-05-10 — Session 1: Initial scaffold + PTY spike

**Operator:** Filipe Negrão
**Agent:** Claude Sonnet 4.6

### What was done

1. Full project scaffold from spec (`spec-harness.md`):
   - Tauri 2 + React 18 + Vite + TypeScript
   - xterm.js 5 + Zustand + CSS custom properties
   - Python sidecar structure (`harness/`)

2. All source files written manually (no `create-tauri-app` interactive CLI):
   - 5 React components: `BentoGrid`, `AgentPane`, `UserTerminal`,
     `ContextPanel`, `StatusStrip`
   - `usePtyTerminal` hook, `useWebSocket` hook
   - `agentStore.ts` with mock data matching `harness.toml` agents
   - `base.css` with full design token set

3. Python sidecar:
   - `parser.py` fully implemented — regex parser for Signal Protocol v1
   - `state.py` — `AgentState` + `ProjectState` dataclasses
   - `loader.py` — reads `harness.toml`, builds initial state
   - `server.py` — WebSocket broadcast server on `ws://127.0.0.1:7373`
   - `watcher.py` — watchdog stub (Phase 2)
   - `parser.py` smoke-tested via Python assertions

4. PTY bridge spiked (`pty.rs`):
   - `PtyRegistry` holds writers by agent_id
   - `spawn_pty()` opens PTY, starts reader thread → Tauri event emission
   - `pty_spawn` + `pty_write` Tauri commands registered
   - `usePtyTerminal` hook: xterm ↔ Tauri event bridge, keyboard input back

5. Infra:
   - Rust updated 1.82 → 1.95 (Tauri 2 requires edition2024 deps)
   - `cargo check` passes clean
   - `tsc --noEmit` passes clean
   - Git repo initialized, initial commit `364ef73`
   - Remote: `git@github.com:filipenegrao/harness-terminal.git`

### What was not done

- Launch sequence not wired (agents not auto-spawned from harness.toml)
- PTY stdout not piped to Python sidecar
- PTY resize not implemented
- No end-to-end test with real agents

### Decisions made

- `Vec<u8>` over base64 for PTY event payload (no extra dep, xterm accepts `Uint8Array`)
- `externalBin` removed from `tauri.conf.json` for dev (sidecar runs manually)
- Rust `[lib]` section removed (desktop-only, no mobile targets)

### Next session

Wire the launch sequence: read `harness.toml` on app start, auto-spawn PTY
per agent, connect sidecar IPC. See HANDOFF.md for acceptance criteria.
