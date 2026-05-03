import struct
import threading
import time
from typing import Any

from utils.entity import EntityManager
from utils.memory import ProcessMemory
from utils.offsets import offsets
from utils.renderer import ESPOverlay
from utils.structs import ScreenSize


class ESPController:
    __slots__ = ("_mem", "_client", "_entities", "_screen")

    def __init__(self, mem: ProcessMemory, client: int, screen: ScreenSize) -> None:
        from utils.config import config

        self._mem = mem
        self._client = client
        self._screen = screen
        self._entities = EntityManager(mem=mem, client=client, offsets=offsets, bone_indices=config.BONE_INDICES)

    def _get_view_matrix(self) -> tuple[float, ...] | None:
        raw = self._mem.read_bytes(self._client + offsets["dwViewMatrix"], 64)
        return struct.unpack("16f", raw) if raw else None

    def run(self, stop_event: threading.Event, cfg: Any) -> None:
        overlay = ESPOverlay(self._screen.width, self._screen.height)

        view_matrix: tuple[float, ...] | None = None
        entities = []

        def reader() -> None:
            nonlocal view_matrix, entities
            while not stop_event.is_set():
                if cfg.enable_esp:
                    view_matrix = self._get_view_matrix()
                    entities = self._entities.get_entities()
                time.sleep(1.0 / 60.0)

        reader_thread = threading.Thread(target=reader, daemon=True)
        reader_thread.start()

        while overlay.alive and not stop_event.is_set():
            if not cfg.enable_esp or view_matrix is None:
                overlay.begin_frame((), [])
                overlay.end_frame()
                continue

            overlay.begin_frame(view_matrix=view_matrix, entities=entities)
            overlay.end_frame()

        overlay.shutdown()
