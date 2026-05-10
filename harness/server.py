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

# Security limits for PTY ingest frames.
_MAX_PAYLOAD = 64 * 1024       # 64 KiB — reject oversized frames
_MAX_LINE_BUFFER = 1024 * 1024 # 1 MiB  — drop unbracketed per-agent buffers
_MAX_PTY_CONNECTIONS = 5       # reject additional TCP connections above this
_FRAME_TIMEOUT = 30.0          # seconds per-frame read deadline
_MAX_AGENT_ID_LEN = 256        # reject agent_id fields longer than this

_clients: set[WebSocketServerProtocol] = set()

# Incomplete lines per agent_id (PTY chunks may split mid-line).
_pty_line_buffers: dict[str, bytearray] = defaultdict(bytearray)

# Active PTY ingress connections (for connection cap).
_active_pty_connections: set[int] = set()


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
    if len(buf) > _MAX_LINE_BUFFER and b"\n" not in buf:
        log.warning(
            "Line buffer cap exceeded for '%s' (%d bytes), dropping buffer", agent_id, len(buf)
        )
        buf.clear()
        return
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
            prefix = await asyncio.wait_for(reader.readexactly(6), timeout=_FRAME_TIMEOUT)
            id_len = int.from_bytes(prefix[:2], "little")
            payload_len = int.from_bytes(prefix[2:6], "little")

            if id_len > _MAX_AGENT_ID_LEN:
                log.warning("Agent id too long (%d bytes) from %s", id_len, peer)
                break
            if payload_len > _MAX_PAYLOAD:
                log.warning("Oversized payload (%d bytes) from %s", payload_len, peer)
                break

            try:
                agent_id = (
                    await asyncio.wait_for(reader.readexactly(id_len), timeout=_FRAME_TIMEOUT)
                ).decode("utf-8")
            except UnicodeDecodeError:
                log.warning("Malformed UTF-8 agent_id from %s", peer)
                break

            if agent_id not in state.agents:
                log.warning("Unknown agent_id '%s' from %s, closing connection", agent_id, peer)
                break

            payload = await asyncio.wait_for(
                reader.readexactly(payload_len), timeout=_FRAME_TIMEOUT
            )
            await _feed_pty_chunk(state, agent_id, payload)
    except (asyncio.IncompleteReadError, asyncio.TimeoutError):
        log.info("PTY ingest closed/timeout from %s", peer)
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
        conn_id = id(writer)
        if len(_active_pty_connections) >= _MAX_PTY_CONNECTIONS:
            log.warning(
                "PTY connection limit (%d) reached, rejecting new connection",
                _MAX_PTY_CONNECTIONS,
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return
        _active_pty_connections.add(conn_id)
        try:
            await _handle_pty_client(reader, writer, state)
        finally:
            _active_pty_connections.discard(conn_id)

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
