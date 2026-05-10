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

---

## 2026-05-10 — Session 2: Launch sequence orchestration gate

**Operator:** Filipe Negrão
**Agent:** Codex orchestrator

### What was done

1. Processed Builder attempt 1 for launch-sequence wiring:
   - `harness.toml` bootstrap into Tauri state
   - auto-spawn one PTY per configured agent
   - PTY stdout mirrored to Python sidecar over localhost TCP `127.0.0.1:7374`
   - WebSocket state updates wired into Zustand

2. Sent the implementation through QA:
   - Result: APPROVED WITH RESERVATIONS
   - Acceptance criteria satisfied from review
   - xterm no-remount constraint confirmed satisfied

3. Sent the approved diff through Security:
   - Result: ADVISORY
   - No critical findings
   - Main follow-up: harden localhost PTY ingest against oversized/partial/malformed frames and arbitrary agent IDs

### Final state

Launch sequence gate succeeded on attempt 1. Security advisories remain for a hardening pass before broader release.

---

## 2026-05-10 — Session 3: PTY ingest security hardening gate

**Operator:** Filipe Negrão
**Agent:** Codex orchestrator

### What was done

1. Processed Builder attempt 1 for the Security ADVISORY follow-up:
   - bounded PTY ingest frame payloads
   - validated agent IDs before line-buffer creation/growth
   - capped incomplete per-agent line buffers
   - added per-read timeouts and active connection cap
   - handled malformed UTF-8 agent IDs cleanly
   - added `TCP_NODELAY` on Rust PTY ingest forwarding
   - fixed `applyDiff` new-agent insertion

2. Sent the implementation through QA:
   - Result: APPROVED
   - No blockers
   - `npm run build` and `cargo check` passed, with only the pre-existing unused `start_sidecar` warning

3. Sent the approved diff through Security:
   - Result: ADVISORY
   - No critical findings
   - Previous advisory items adequately addressed for the local dev context

### Final state

Security hardening follow-up succeeded on attempt 1. Remaining items are non-blocking polish: total per-frame deadline, clearer connection tracking, explicit complete-agent diff contract, and optional no-newline buffer scan optimization.
