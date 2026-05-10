"""watchdog file tree monitor stub. Phase 2 feature."""

import logging
from pathlib import Path
from typing import Callable

log = logging.getLogger("harness.watcher")


class FileWatcher:
    """Monitors working_dir for file modifications.

    Calls on_change(path: str) for each modified file.
    Stub — not yet wired to ProjectState or WebSocket broadcast.
    """

    def __init__(self, working_dir: str, on_change: Callable[[str], None]) -> None:
        self.working_dir = Path(working_dir)
        self.on_change = on_change
        self._observer = None

    def start(self) -> None:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _Handler(FileSystemEventHandler):
                def __init__(self, cb: Callable[[str], None]) -> None:
                    self._cb = cb

                def on_modified(self, event) -> None:  # type: ignore[override]
                    if not event.is_directory:
                        self._cb(event.src_path)

            self._observer = Observer()
            self._observer.schedule(
                _Handler(self.on_change), str(self.working_dir), recursive=True
            )
            self._observer.start()
            log.info("Watching %s", self.working_dir)
        except Exception as exc:
            log.warning("File watcher failed to start: %s", exc)

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
