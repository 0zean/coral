import ctypes
import io
import struct
import sys
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
        set_target_fps,
        set_trace_log_level,
        set_window_state,
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

    def run_esp(self) -> None:
        set_trace_log_level(LOG_NONE)
        init_window(self.screen_width, self.screen_height, b"ESP Overlay")
        set_target_fps(60)
        set_window_state(FLAG_WINDOW_UNDECORATED | FLAG_WINDOW_TRANSPARENT | FLAG_WINDOW_TOPMOST)

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

        while not window_should_close():
            view_matrix = self.get_view_matrix()
            renderer = ESPRenderer(self.screen_width, self.screen_height, view_matrix)
            entities = self.entity_manager.get_entities()
            begin_drawing()
            clear_background((0, 0, 0, 0))  # type: ignore
            for entity in entities:
                renderer.draw_entity(entity, Color(0, 180, 255, 255))
            end_drawing()
        close_window()
