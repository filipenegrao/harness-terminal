"""WebSocket server — broadcasts ProjectState to the Tauri webview.

Listens on ws://127.0.0.1:7373.
Protocol:
  full_state  — sent once on client connect: {"type": "full_state", "payload": {...}}
  state_diff  — sent on any state change:   {"type": "state_diff", "payload": {...}}
"""

import asyncio
import json
import logging

import websockets
from websockets.server import WebSocketServerProtocol

from state import ProjectState

log = logging.getLogger("harness.server")
HOST = "127.0.0.1"
PORT = 7373

_clients: set[WebSocketServerProtocol] = set()


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


async def run_server(state: ProjectState) -> None:
    async def handler(ws: WebSocketServerProtocol) -> None:
        await _handler(ws, state)

    log.info("WebSocket server on ws://%s:%d", HOST, PORT)
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()  # run until cancelled
