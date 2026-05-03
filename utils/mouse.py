import ctypes
import threading
from time import time

import win32api

from utils.config import config
from utils.structs import INPUT, MOUSEINPUT, Vec2

# ctypes function prototype
SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = ctypes.c_uint

# Global rate-limit state
_last_moved_lock = threading.Lock()
_last_moved_time: float = time()


# Internal helpers
def _make_relative_input(dx: int, dy: int) -> INPUT:
    """Build a relative-move INPUT struct (MOUSEEVENTF_MOVE = 0x0001)."""
    mi = MOUSEINPUT(
        dx=dx,
        dy=dy,
        mouseData=0,
        dwFlags=config.MOUSEEVENTF_MOVE,
        time=0,
        dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
    )
    return INPUT(type=0, u=INPUT.INPUT_UNION(mi=mi))


def _send(inp: INPUT) -> None:
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


# Public API
def get_mouse_pos() -> Vec2:
    """
    Return the current absolute cursor position.

    Returns:
        Vec2: Current [x, y] mouse position.
    """
    pos = win32api.GetCursorPos()
    return Vec2(pos[0], pos[1]) if pos else Vec2(0, 0)


def move_mouse(dx: int, dy: int, *, record_time: bool = False) -> None:
    """
    Send a relative mouse movement via SendInput.

    Args:
        dx (int): Horizontal delta in pixels.
        dy (int): Vertical delta in pixels.
        record_time (bool, optional): If True, update the global last-moved timestamp. Defaults to False.
    """
    _send(_make_relative_input(dx, dy))
    if record_time:
        global _last_moved_time
        with _last_moved_lock:
            _last_moved_time = time()


def move_mouse_to_location(pos: Vec2) -> None:
    """
    Move the cursor to an absolute screen position via a relative SendInput call.

    Computes the delta from screen centre and sends it as a move event through SendInput.

    Args:
        pos (Vec2): Target absolute screen position
    """
    if pos.x < 0.0 or pos.y < 0.0:
        return

    center = Vec2(config.SCREEN_WIDTH / 2.0, config.SCREEN_HEIGHT / 2.0)
    dx = int(pos.x - center.x)
    dy = int(pos.y - center.y)

    if dx == 0 and dy == 0:
        return

    _send(_make_relative_input(dx, dy))
