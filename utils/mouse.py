import ctypes
import threading
from time import time
from typing import Literal

import win32api

from utils.config import config
from utils.structs import INPUT, MOUSEINPUT, Vec2

# ctypes function prototypes
SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = ctypes.c_uint

# Global state
last_moved = threading.Lock()
last_moved_time = time()


def create_mouse_input(flags: Literal[1], dx: int, dy: int, data: int, extra_info: int) -> INPUT:
    """
    Creates a mouse input event.

    Args:
        flags (Literal[1]): The mouse event flags.
        dx (int): Amount to move in the x direction.
        dy (int): Amount to move in the y direction.
        data (int): Additional data for the event.
        extra_info (int): Extra information for the event.

    Returns:
        INPUT: The constructed INPUT structure.
    """
    mi = MOUSEINPUT(
        dx=dx, dy=dy, mouseData=data, dwFlags=flags, time=0, dwExtraInfo=ctypes.pointer(ctypes.c_ulong(extra_info))
    )
    input = INPUT(type=0, u=INPUT.INPUT_UNION(mi=mi))
    return input


def send_input(input: INPUT) -> None:
    """
    Sends a single input event to the system.

    Args:
        input (INPUT): The INPUT structure to send.
    """
    SendInput(1, ctypes.byref(input), ctypes.sizeof(input))


def move_mouse(x: int, y: int, set_last_moved: bool) -> None:
    """
    Moves the mouse by specified x and y offsets.

    Args:
        x (int): The x coordinate to move the mouse to.
        y (int): The y coordinate to move the mouse to.
        set_last_moved (bool): Whether to update the last moved time.
    """
    send_input(create_mouse_input(config.MOUSEEVENTF_MOVE, x, y, 0, 0))
    if set_last_moved:
        global last_moved_time
        with last_moved:
            last_moved_time = time()


def get_mouse_pos() -> Vec2:
    """
    Gets the current mouse position.

    Returns:
        Vec2: Current mouse position as Vec2 (x, y).
    """
    pos = win32api.GetCursorPos()
    if pos:
        return Vec2(pos[0], pos[1])
    return Vec2(0, 0)


def move_mouse_to_location(pos: Vec2) -> None:
    """
    Moves the mouse to a specified location on the screen.

    Args:
        pos (Vec2): The target position to move the mouse to.
    """
    if pos.x < 0.0 and pos.y < 0.0:
        return

    center_of_screen = Vec2(config.SCREEN_WIDTH / 2.0, config.SCREEN_HEIGHT / 2.0)
    dx = int(pos.x - center_of_screen.x)
    dy = int(pos.y - center_of_screen.y)

    ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)
