"""Harness sidecar entry point. Starts WebSocket server + PTY listeners."""

import asyncio
import logging
from pathlib import Path

from loader import load_config
from server import run_server

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("harness.main")


async def main() -> None:
    config_path = Path(__file__).parent.parent / "harness.toml"
    state = load_config(config_path)
    log.info(
        "Loaded project '%s' with %d agents",
        state.project_name,
        len(state.agents),
    )
    await run_server(state)


if __name__ == "__main__":
    asyncio.run(main())
