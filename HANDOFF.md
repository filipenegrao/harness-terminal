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

## Orchestrator cycle (last completed)

| Field | Value |
|-------|--------|
| Task | Wire launch sequence (HANDOFF “Next task”) |
| Attempt | 1 of 3 |
| Step | **Final check** — completed **2026-05-10** |
| Status | **Success** — QA approved with reservations; Security returned ADVISORY with no critical findings. |
| Dashboard | `final_check` |

### Builder return summary (attempt 1)

- **PTY → Python:** localhost TCP `127.0.0.1:7374`, framed chunks (u16 LE agent id len, u32 LE payload len, UTF-8 `agent_id`, raw bytes); documented in `harness/server.py` / `PTY_INGEST_ADDR` in `pty.rs`.
- **Rust:** repo-root `harness.toml` resolution (cwd + parent walk), bootstrap JSON, `bootstrap_harness` spawns one PTY per agent (`sh -c "<command>"`), `BootstrapDone` avoids double spawn under React Strict Mode.
- **Forwarding:** PTY readers emit `pty-data-{id}` to xterm and mirror bytes to sidecar when TCP up (lazy connect, reconnect on write failure).
- **Python:** WS `7373` + ingest `7374`; lines → `parse_line` → `apply_signal` → `state_diff` over WS.
- **React:** `bootstrap_harness` on mount; `useWebSocket` applies `full_state` / `state_diff`; `applyDiff` merges per-agent patches.
- **xterm:** `usePtyTerminal` still `[]` effect deps (no remount on store updates).
- **AGENTS.md:** restored to Harness Signal Protocol v1 (was unrelated Notion text).
- **Verification (Builder):** `cargo check` pass (unused `start_sidecar` warning); `npm run build` pass.
- **Scope hygiene:** `.gitignore`, `HANDOFF.md`, `STATUS.json`, untracked `NOTION_PROJECT_PROTOCOL.md` may be mixed — review before commit. New file: `src-tauri/src/config.rs` (ensure tracked).

### QA verdict (attempt 1)

**VERDICT:** APPROVED WITH RESERVATIONS

- Acceptance criteria judged satisfied from code review: `harness.toml` bootstrap, all 4 PTYs spawned, PTY input/output path, Python ingest, and signal parsing/broadcast.
- xterm remount constraint judged fully satisfied: `usePtyTerminal` attaches once with `[]` deps and store updates only affect chrome.
- Non-blocking reservations to carry forward:
  1. `applyDiff` drops new agents if a `state_diff` contains an agent absent from the current store.
  2. `bootstrap_harness` static snapshot can theoretically clobber earlier live WS state.
  3. Python ingest has no payload size bound.
  4. `git rev-parse` runs synchronously on startup without timeout.
  5. `SidecarForward` does not set `TCP_NODELAY`.
  6. `useWebSocket` subscribes `App` to the full store.
  7. `resolve_harness_toml` has harmless dead fallback code.

QA recommended addressing reservations 1 and 5 before shipping, but did not block the gate.

### Security verdict (attempt 1)

**VERDICT:** ADVISORY

- No exploitable remote blocker found.
- New network services bind to `127.0.0.1`.
- React renders parsed signal/config fields through text interpolation, not HTML.
- PTY command execution from repo-local `harness.toml` is intentional for this local dev harness.
- Security advisories to carry forward before broader release:
  1. Bound `payload_len` in `harness/server.py`.
  2. Validate `agent_id` before creating/growing PTY line buffers.
  3. Cap incomplete line buffers and add read timeouts/connection limits for partial frames.
  4. Handle malformed UTF-8 agent IDs cleanly.
  5. Consider gating/removing arbitrary `pty_spawn` from webview once bootstrap is the only needed path.
  6. Treat untrusted repos/configs as unsafe because `harness.toml` commands run via `sh -c`.
  7. Add startup timeout/backgrounding around `git rev-parse`.
  8. Keep PTY frame payload casts explicit if the read path ever exceeds 4096-byte chunks.
  9. Consider allowlisting config-derived class/style fields for UI integrity.

### Final result

Attempt 1 succeeded. The launch-sequence implementation can proceed with ADVISORY security status. Do not mark the overall project complete without explicit human approval.

## Orchestrator cycle (last completed)

| Field | Value |
|-------|--------|
| Task | Security hardening follow-up |
| Attempt | 1 of 3 |
| Step | **Final check** — completed **2026-05-10** |
| Status | **Success** — QA approved; Security returned ADVISORY with no critical findings. |
| Dashboard | `final_check` |

### Builder scope (attempt 1)

- Harden Python PTY ingest in `harness/server.py`:
  - bound frame payload sizes before `readexactly(payload_len)`;
  - validate `agent_id` against configured `state.agents` before creating/growing `_pty_line_buffers`;
  - cap incomplete per-agent line buffers;
  - add per-frame read timeouts and a reasonable connection limit;
  - handle malformed UTF-8 agent IDs cleanly without unhandled task exceptions.
- Apply two cheap launch-sequence polish fixes from QA/Security if low-risk:
  - set `TCP_NODELAY` on the Rust TCP forwarder in `src-tauri/src/pty.rs`;
  - fix `applyDiff` so new agents from server diffs are not silently dropped.
- Do not broaden into PTY resize, sidecar bundling, file tree, git branch UI, or unrelated cleanup.

### Builder return summary (attempt 1)

- `harness/server.py`: added `_MAX_PAYLOAD` 64 KiB, `_MAX_LINE_BUFFER` 1 MiB, `_MAX_PTY_CONNECTIONS` 5, `_FRAME_TIMEOUT` 30s, and `_MAX_AGENT_ID_LEN` 256.
- Oversized frames are rejected before payload `readexactly`.
- Malformed UTF-8 agent IDs and too-long agent IDs close the ingest connection cleanly.
- Unknown agent IDs are rejected before `_pty_line_buffers` is touched.
- Incomplete per-agent line buffers are cleared when they exceed the cap without a newline.
- PTY ingest reads use `asyncio.wait_for`; active connections are capped with `_active_pty_connections`.
- `src-tauri/src/pty.rs`: sets `TCP_NODELAY` after connecting to Python ingest.
- `src/store/agentStore.ts`: `applyDiff` now inserts new agents from server diffs instead of dropping them.
- Builder sensors: `cd src-tauri && cargo check` passed with pre-existing unused `start_sidecar` warning; `npm run build` passed. No Python tests exist; syntax/import check parsed AST, but `websockets` import was unavailable outside bundled environment.
- Builder remaining risks: no dead-agent buffer cleanup if agents are removed while data is in transit; connection tracking uses `id(writer)`.

### QA verdict (attempt 1)

**VERDICT:** APPROVED

- QA confirmed all five Python hardening items and both optional fixes landed correctly.
- No blockers.
- Sensors: `npm run build` passed; `cargo check` passed with only the pre-existing unused `start_sidecar` warning; no Python tests exist.
- Non-blocking reservations to carry forward:
  1. `_FRAME_TIMEOUT` applies per `readexactly` call, so one full slow frame can hold a slot for up to roughly 90 seconds.
  2. `id(writer)` as connection key is correct for CPython but non-obvious and less portable.
  3. `applyDiff` new-agent insertion assumes server diffs contain complete `AgentState` objects.
  4. `b"\n" not in buf` scans up to 1 MiB on every chunk.
  5. `set_nodelay` failure is silently swallowed, acceptable because it is an optimization.

### Security verdict (attempt 1)

**VERDICT:** ADVISORY

- Previous Security ADVISORY items are adequately addressed for this local dev context.
- Valid PTY frames still parse and broadcast.
- Malformed, oversized, and unknown-agent frames close cleanly in review/smoke coverage.
- No critical findings and no Builder remediation required before merge.
- Remaining non-blocking items:
  1. `_FRAME_TIMEOUT` is per read step, so five slow local clients can temporarily occupy the PTY ingest pool; consider a total per-frame deadline later.
  2. `b"\n" not in buf` bounds memory but can still create local CPU churn up to the 1 MiB cap.
  3. `id(writer)` connection tracking is adequate in CPython but a monotonic counter or storing writer objects would be clearer.
  4. `applyDiff` new-agent insertion depends on the current server contract that agent diffs are complete `agent.to_dict()` objects.

### Final result

Attempt 1 succeeded. The security hardening follow-up can proceed with ADVISORY status.

---

## Known risks / open questions

1. **PTY → sidecar IPC** — Builder chose **TCP 7374 multiplex**; QA and Security accepted it with localhost DoS hardening advisories.
2. **xterm resize** — `fitAddon.fit()` must be called on pane resize.
   Tauri window resize events need to propagate correctly.
3. **Sidecar bundling** — PyInstaller binary size; test early before release.

## Backlog — security hardening polish

Carry these lower-priority polish items forward:

1. Replace per-read PTY ingest timeout windows with a total per-frame deadline.
2. Replace `id(writer)` connection tracking with writer-object tracking or a monotonic connection ID.
3. Keep the server contract explicit: inserted `state_diff` agents must be complete `AgentState` objects.
4. Consider optimizing the no-newline buffer cap check if large-output agents create CPU churn.
5. Consider gating or removing arbitrary `pty_spawn` from the webview once bootstrap is the only supported spawn path.
6. Document that opening untrusted repos/configs is unsafe because `harness.toml` commands execute via `sh -c`.
7. Add timeout/backgrounding around startup `git rev-parse`.
8. Keep PTY frame payload casts explicit if the read path ever changes beyond 4096-byte chunks.
9. Consider allowlisting config-derived class/style fields for UI integrity.

---

## Workflow

This project uses the orchestrator cycle in `_prompts/orchestrator.md`.
Each feature task goes through: Builder → QA → Security before merge.
