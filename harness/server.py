"""WebSocket server — broadcasts ProjectState to the Tauri webview.

Listens on ws://127.0.0.1:7373.
Protocol:
  full_state  — sent once on client connect: {"type": "full_state", "payload": {...}}
  state_diff  — sent on any state change:   {"type": "state_diff", "payload": {...}}

PTY ingest (TCP localhost:7374): Rust forwards raw PTY stdout in framed chunks so we can parse
Harness signals (see AGENTS.md / parser.py) and broadcast parsed agent updates.
Frame layout per chunk: u16 agent_id_len LE, u32 payload_len LE, agent_id UTF-8, payload bytes.
"""

import asyncio
import json
import logging
from collections import defaultdict

import websockets
from websockets.server import WebSocketServerProtocol

from parser import parse_line
from state import ProjectState

log = logging.getLogger("harness.server")
HOST = "127.0.0.1"
PORT = 7373

# PTY → Python IPC (must match `PTY_INGEST_ADDR` in `src-tauri/src/pty.rs`).
PTY_INGEST_HOST = "127.0.0.1"
PTY_INGEST_PORT = 7374

_clients: set[WebSocketServerProtocol] = set()

# Incomplete lines per agent_id (PTY chunks may split mid-line).
_pty_line_buffers: dict[str, bytearray] = defaultdict(bytearray)


async def broadcast(message: dict) -> None:
    """Send a message to all connected clients."""
    if not _clients:
        return
    data = json.dumps(message)
    await asyncio.gather(
        *(client.send(data) for client in list(_clients)),
        return_exceptions=True,
    )


async def _handler(ws: WebSocketServerProtocol, state: ProjectState) -> None:
    _clients.add(ws)
    log.info("Client connected (%d total)", len(_clients))
    try:
        # Send full state immediately on connect so the UI can initialise
        await ws.send(json.dumps({"type": "full_state", "payload": state.to_dict()}))
        async for _ in ws:
            pass  # server is broadcast-only; inbound messages ignored
    finally:
        _clients.discard(ws)
        log.info("Client disconnected (%d total)", len(_clients))


async def _feed_pty_chunk(state: ProjectState, agent_id: str, payload: bytes) -> None:
    buf = _pty_line_buffers[agent_id]
    buf.extend(payload)
    while True:
        try:
            nl = buf.index(0x0A)
        except ValueError:
            break
        raw = bytes(buf[:nl])
        del buf[: nl + 1]
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        parsed = parse_line(agent_id, line)
        if not parsed:
            continue
        agent = state.agents.get(agent_id)
        if not agent:
            continue
        agent.apply_signal(parsed)
        await broadcast(
            {
                "type": "state_diff",
                "payload": {
                    "agents": {
                        agent_id: agent.to_dict(),
                    },
                },
            }
        )


async def _handle_pty_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    state: ProjectState,
) -> None:
    peer = writer.get_extra_info("peername")
    log.info("PTY ingest connected from %s", peer)
    try:
        while True:
            prefix = await reader.readexactly(6)
            id_len = int.from_bytes(prefix[:2], "little")
            payload_len = int.from_bytes(prefix[2:6], "little")
            agent_id = (await reader.readexactly(id_len)).decode("utf-8")
            payload = await reader.readexactly(payload_len)
            await _feed_pty_chunk(state, agent_id, payload)
    except asyncio.IncompleteReadError:
        log.info("PTY ingest closed from %s", peer)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def run_server(state: ProjectState) -> None:
    async def ws_handler(ws: WebSocketServerProtocol) -> None:
        await _handler(ws, state)

    async def accept_pty(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        await _handle_pty_client(reader, writer, state)

    log.info("WebSocket server on ws://%s:%d", HOST, PORT)
    log.info(
        "PTY ingest TCP on %s:%d — Rust forwards PTY stdout for parsing",
        PTY_INGEST_HOST,
        PTY_INGEST_PORT,
    )

    async def ws_loop() -> None:
        async with websockets.serve(ws_handler, HOST, PORT):
            await asyncio.Future()

    async def pty_loop() -> None:
        server = await asyncio.start_server(
            accept_pty,
            PTY_INGEST_HOST,
            PTY_INGEST_PORT,
        )
        async with server:
            await asyncio.Future()

    await asyncio.gather(ws_loop(), pty_loop())
