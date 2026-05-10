# AGENTS.md — Harness Signal Protocol v1

Emit structured signals on any line where your status changes.
Signals are parsed by the Harness terminal; follow the format exactly.

## Required signal (emit on every status change)

```
[STATUS:working|idle|done|error] [NEXT:agent_id|none] [TOKENS:n]
```

## Optional signals

```
[TASK:short description of current task]
[WARN:message for orchestrator]
[HANDOFF:agent_id reason for handoff]
```

## Rules

- Signals on their own line — no prose on the same line
- `NEXT:none` when there is no clear handoff
- `STATUS:error` must include a `[WARN]` signal
- Never emit signals inside code blocks
- `TOKENS` is total tokens used this session
