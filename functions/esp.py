import ctypes
import io
import struct
import sys
import threading
from typing import Any

from pymem import Pymem

_stdout = sys.stdout
_stderr = sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
try:
    from raylibpy import (
        FLAG_WINDOW_TOPMOST,
        FLAG_WINDOW_TRANSPARENT,
        FLAG_WINDOW_UNDECORATED,
        LOG_NONE,
        Color,
        begin_drawing,
        clear_background,
        close_window,
        end_drawing,
        init_window,
        load_font_ex,
        set_config_flags,
        set_target_fps,
        set_trace_log_level,
        window_should_close,
    )
finally:
    sys.stdout = _stdout
    sys.stderr = _stderr

from utils.config import config
from utils.entity import EntityManager
from utils.offsets import offsets
from utils.renderer import ESPRenderer


class ESPController:
    def __init__(self, pm: Pymem, client: Any) -> None:
        self.pm = pm
        self.client = client
        self.entity_manager = EntityManager(pm, client, offsets, config.BONE_INDICES)
        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT

    def get_view_matrix(self) -> tuple[float, ...]:
        data = self.pm.read_bytes(self.client + offsets["dwViewMatrix"], 64)
        return struct.unpack("16f", data)

    def _memory_reader_thread(self, stop_event: threading.Event, config: Any) -> None:
        """Background thread that reads memory at a fixed cadence (e.g., 60Hz) to save CPU."""
        import time

        while not stop_event.is_set():
            if not config.enable_esp:
                time.sleep(0.1)
                continue

            try:
                # Read aggressively, but only at our desired data refresh rate
                self.cached_view_matrix = self.get_view_matrix()
                self.cached_entities = self.entity_manager.get_entities()
            except Exception as e:
                print(f"Memory read error: {e}")

            time.sleep(1.0 / 60.0)  # ~60Hz read cadence

    def run_esp(self, stop_event: threading.Event, config: Any) -> None:
        set_trace_log_level(LOG_NONE)

        # Set window flags BEFORE initializing to prevent black screen flash or permanent black background
        set_config_flags(FLAG_WINDOW_UNDECORATED | FLAG_WINDOW_TRANSPARENT | FLAG_WINDOW_TOPMOST)
        init_window(self.screen_width, self.screen_height, b"ESP Overlay")
        set_target_fps(144)

        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.FindWindowW(None, "ESP Overlay")
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            ctypes.windll.user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED | WS_EX_TRANSPARENT,
            )
            # SetLayeredWindowAttributes(hwnd, RGB(0,0,0), 0, LWA_COLORKEY)
            LWA_COLORKEY = 0x1
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0x000000, 0, LWA_COLORKEY)

        # Initialize cache
        self.cached_view_matrix = None
        self.cached_entities = []

        # Start background memory reading thread
        reader_thread = threading.Thread(target=self._memory_reader_thread, args=(stop_event, config), daemon=True)
        reader_thread.start()

        # Load custom font
        font_path = b"C:\\Windows\\Fonts\\calibri.ttf"
        custom_font = load_font_ex(font_path, 20, None, 0)

        while not window_should_close() and not stop_event.is_set():
            if not config.enable_esp:
                clear_background(Color(0, 0, 0, 0))
                end_drawing()
                continue

            # Use cached data directly
            view_matrix = self.cached_view_matrix
            entities = self.cached_entities

            if view_matrix is None:
                clear_background(Color(0, 0, 0, 0))
                end_drawing()
                continue

            renderer = ESPRenderer(self.screen_width, self.screen_height, view_matrix, custom_font)

            begin_drawing()
            clear_background(Color(0, 0, 0, 0))
            for entity in entities:
                renderer.draw_entity(entity, Color(0, 180, 255, 255))
            end_drawing()

        close_window()
