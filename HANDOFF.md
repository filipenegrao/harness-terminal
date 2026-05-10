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

**Live end-to-end smoke:** prove the committed launch sequence works in the real
app flow with Python sidecar + Tauri app + 4 PTYs + signal parsing into UI.

Acceptance criteria:
1. Python sidecar starts and listens on `ws://127.0.0.1:7373` and PTY ingest `127.0.0.1:7374`
2. `npm run tauri dev` starts the app without manual agent spawning
3. All 4 agents from `harness.toml` have live PTY panes
4. Typing in an agent pane sends input to the correct PTY
5. PTY output renders correctly in xterm.js
6. A real Harness signal emitted from a PTY reaches Python, parses, broadcasts over WebSocket, and updates UI state

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

## Orchestrator cycle (last completed)

| Field | Value |
|-------|--------|
| Task | Live end-to-end smoke |
| Attempt | 1 of 3 |
| Step | **Final check** — completed **2026-05-10** |
| Status | **Success with reservations** — QA approved with reservations; Security returned ADVISORY with no critical findings. |
| Dashboard | `final_check` |

### Builder scope (attempt 1)

- Run the real app path with Python sidecar and Tauri dev.
- Verify 4 configured PTY panes are live.
- Verify keyboard input reaches the intended PTY.
- Verify PTY output renders in xterm.
- Emit at least one Harness signal from a PTY and verify Python parses/broadcasts it and UI state updates.
- Prefer no code changes. Only make minimal fixes if the smoke exposes a real blocker, and report them explicitly.

### Builder return summary (attempt 1)

**VERDICT:** PASS WITH RESERVATIONS

- No code changes.
- Created `harness/.venv` because Homebrew Python is PEP 668-managed, then installed `harness/requirements.txt`.
- Started `harness/.venv/bin/python harness/main.py`; sidecar loaded project `my-project` with 4 agents and listened on WebSocket `7373` plus PTY ingest `7374`.
- Ran `npm run tauri dev`; Vite started on `1420`, Cargo ran, and native binary reached `Running target/debug/harness` after clearing a stale process on port `1420`.
- Sidecar logs showed WebSocket connections and a PTY ingest connection from the native app.
- Scripted WebSocket/TCP checks verified:
  - `full_state` includes `builder`, `orchestrator`, `qa`, and `security`;
  - framed PTY ingest produces `state_diff`;
  - `[STATUS:working] [NEXT:none] [TOKENS:123]` parses and broadcasts;
  - single-line required signal plus `[TASK:live smoke signal parse]` updates `last_task`;
  - oversized payload frame logs warning and is rejected.
- Not visually verified in GUI: four visible xterm panes, keyboard input through a pane, xterm echo/rendering, UI update after signal, and no xterm remount during live React state updates.
- Operational reservations:
  1. GUI/xterm criteria require human or UI automation confirmation.
  2. `[TASK:...]` only updates when it appears on the same line as the required `[STATUS:...]` signal, per parser behavior.
  3. First plain `python3 harness/main.py` required venv setup on this PEP 668 Homebrew Python.
  4. A stale Vite process on port `1420` had to be killed before Tauri dev could start.

### QA verdict (attempt 1)

**VERDICT:** APPROVED WITH RESERVATIONS

- QA confirmed zero functional code changes in the smoke cycle; only `HANDOFF.md` and `STATUS.json` differ.
- Backend/protocol evidence is accepted: sidecar on `7373` and `7374`, Tauri startup without manual spawning, `full_state` with all 4 agents, native PTY ingest connection, signal parse/broadcast, optional same-line `[TASK]`, and oversized-frame rejection.
- No blockers.
- Reservations to carry into Security/follow-up:
  1. Keyboard input to PTY and PTY output rendering in xterm were not visually or mechanically exercised.
  2. The visual UI update path (`useWebSocket` -> `applyDiff` -> Zustand -> `AgentPane`) was not observed in the running GUI.
  3. The xterm no-remount invariant was inferred from unchanged reviewed code but not exercised under live `state_diff` traffic.
  4. AGENTS.md permits optional signals on separate lines, but `harness/parser.py` only captures optional fields on the same line as the required status signal.
  5. The Homebrew Python venv requirement and stale Vite port are operational notes, not product bugs.

### Security verdict (attempt 1)

**VERDICT:** ADVISORY

- No functional code changes were introduced by this smoke cycle; only orchestration docs changed.
- Backend smoke evidence is acceptable for Security: localhost sidecar/ingest, WS `full_state`, framed TCP `state_diff`, valid signal parsing, same-line `[TASK]`, and oversized-frame rejection.
- No critical findings and no Builder remediation required.
- Security advisories to carry forward:
  1. AGENTS.md optional-signal examples allow separate lines, while `harness/parser.py` only captures optionals on lines that also contain `[STATUS:...]`; Security sees no unsafe spoofing/state-confusion impact, but metadata can be missed.
  2. GUI evidence remains partial: keyboard input, xterm rendering, visible UI updates, and live no-remount behavior were not exercised.
  3. `harness/.venv` was created by smoke setup and is ignored by `.gitignore`; no tracked dependency material was introduced.
  4. A local Node listener remained on `[::1]:1420`; no `7373`/`7374` listeners were observed. Treat as operational cleanup.

### Final result

Attempt 1 succeeded with ADVISORY security status. Backend/protocol runtime smoke passed; GUI/xterm live verification remains a follow-up before claiming the UI criteria are fully closed.

---

## Known risks / open questions

1. **PTY → sidecar IPC** — Builder chose **TCP 7374 multiplex**; QA and Security accepted it with localhost DoS hardening advisories.
2. **xterm resize** — `fitAddon.fit()` must be called on pane resize.
   Tauri window resize events need to propagate correctly.
3. **Sidecar bundling** — PyInstaller binary size; test early before release.
4. **GUI/xterm live verification** — Run a targeted local GUI check for visible panes, keyboard input, xterm rendering, UI status update, and no xterm remount/flicker under live `state_diff`.
5. **Signal protocol alignment** — Either update AGENTS.md to require optional fields on the same line as `[STATUS:...]`, or patch `harness/parser.py` to support optional signal lines as the spec implies.

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

## Backlog — operational docs

1. Document the Homebrew Python / PEP 668 dev path: create `harness/.venv` and install `harness/requirements.txt`.
2. Document cleanup for stale dev listeners on port `1420` before `npm run tauri dev`.

---

## Workflow

This project uses the orchestrator cycle in `_prompts/orchestrator.md`.
Each feature task goes through: Builder → QA → Security before merge.
