import ctypes
import io
import logging
import os
import struct
import sys
import threading
import time

logger = logging.getLogger(__name__)

_stdout, _stderr = sys.stdout, sys.stderr
sys.stdout = sys.stderr = io.StringIO()
try:
    from raylibpy import (
        FLAG_WINDOW_TOPMOST,
        FLAG_WINDOW_TRANSPARENT,
        FLAG_WINDOW_UNDECORATED,
        LOG_NONE,
        begin_drawing,
        clear_background,
        close_window,
        end_drawing,
        get_window_handle,
        init_window,
        load_font_ex,
        set_config_flags,
        set_target_fps,
        set_trace_log_level,
        window_should_close,
    )

    try:
        from raylibpy import FLAG_WINDOW_MOUSE_PASSTHROUGH

        _HAS_PASSTHROUGH = True
    except ImportError:
        _HAS_PASSTHROUGH = False
finally:
    sys.stdout, sys.stderr = _stdout, _stderr

from utils.config import config
from utils.entity import EntityManager
from utils.memory import ProcessMemory
from utils.offsets import offsets
from utils.renderer import ESPRenderer
from utils.structs import ScreenSize
from utils.thread_manager import ThreadConfig


class ESPController:
    __slots__ = ("_mem", "_client", "_screen", "_entity_mgr")

    def __init__(self, mem: ProcessMemory, client: int, screen: ScreenSize) -> None:
        self._mem = mem
        self._client = client
        self._screen = screen
        self._entity_mgr = EntityManager(mem, client, offsets, config.BONE_INDICES)

    def _get_view_matrix(self) -> tuple[float, ...] | None:
        raw = self._mem.read_bytes(self._client + offsets["dwViewMatrix"], 64)
        return struct.unpack("16f", raw) if raw else None

    @staticmethod
    def _apply_win32_styles(hwnd: int) -> None:
        """
        Apply WS_EX_TRANSPARENT (click-through) and WS_EX_TOOLWINDOW (hide
        from taskbar/Alt-Tab) to the overlay window.
        """
        if not hwnd:
            logger.warning("get_window_handle() returned NULL; click-through not applied")
            return
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, config.GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, config.GWL_EXSTYLE, style | config.WS_EX_TRANSPARENT | config.WS_EX_TOOLWINDOW)

    def _reader(self, stop_event: threading.Event, cfg: ThreadConfig, vm_cell: list, ent_cell: list) -> None:
        """Background memory-reader thread (~60 Hz)."""
        while not stop_event.is_set():
            if cfg.enable_esp:
                try:
                    vm_cell[0] = self._get_view_matrix()
                    ent_cell[0] = self._entity_mgr.get_entities()
                except Exception:
                    logger.debug("ESP reader error", exc_info=True)
            else:
                vm_cell[0] = None
                ent_cell[0] = []
            time.sleep(config.READER_TICK)

    def run(self, stop_event: threading.Event, cfg: ThreadConfig) -> None:
        set_trace_log_level(LOG_NONE)

        # window flags before creation
        flags = FLAG_WINDOW_UNDECORATED | FLAG_WINDOW_TRANSPARENT | FLAG_WINDOW_TOPMOST
        if _HAS_PASSTHROUGH:
            flags |= FLAG_WINDOW_MOUSE_PASSTHROUGH  # type: ignore
        set_config_flags(flags)

        # create window
        init_window(self._screen.width, self._screen.height, b"ESP Overlay")
        set_target_fps(144)

        # obtain HWND
        hwnd = get_window_handle()

        # Apply Win32 styles before the sentinel frame
        self._apply_win32_styles(hwnd)  # type: ignore

        # sentinel frame
        begin_drawing()
        clear_background(config.TRANSPARENT)
        end_drawing()

        # load font
        windir = os.environ.get("WINDIR", r"C:\Windows")
        font_path = os.path.join(windir, "Fonts", "calibri.ttf").encode()
        font = load_font_ex(font_path, 20, None, 0)

        # Shared state reference cells + start reader
        vm_cell: list = [None]
        ent_cell: list = [[]]

        reader_thread = threading.Thread(target=self._reader, args=(stop_event, cfg, vm_cell, ent_cell), daemon=True)
        reader_thread.start()

        # Construct renderer once
        renderer = ESPRenderer(self._screen, font)

        # render loop
        while not window_should_close() and not stop_event.is_set():
            vm = vm_cell[0]
            entities = ent_cell[0]

            begin_drawing()
            clear_background(config.TRANSPARENT)

            if cfg.enable_esp and vm is not None:
                renderer.update_matrix(vm)
                for entity in entities:
                    renderer.draw_entity(entity, config.ENTITY_COLOR)

            end_drawing()

        close_window()
