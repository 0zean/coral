import logging
import threading
import time
from random import uniform

import keyboard
from pynput.mouse import Button, Controller

from utils.memory import ProcessMemory
from utils.offsets import offsets
from utils.thread_manager import ThreadConfig

_mouse = Controller()
logger = logging.getLogger(__name__)

_CS2_WINDOW_TITLE = "Counter-Strike 2"
_SLEEP_INACTIVE = 0.1
_SLEEP_PRESSED = 0.03
_SLEEP_RELEASED = 0.1
_CLICK_PRE_DELAY = (0.01, 0.03)  # seconds before press
_CLICK_POST_DELAY = (0.01, 0.05)  # seconds before release

try:
    from win32gui import GetForegroundWindow, GetWindowText

    def _is_cs2_focused() -> bool:
        return GetWindowText(GetForegroundWindow()) == _CS2_WINDOW_TITLE
except ImportError:

    def _is_cs2_focused() -> bool:
        return True


def _click() -> None:
    """Simulate a left-click with randomised pre/post delays."""
    time.sleep(uniform(*_CLICK_PRE_DELAY))
    _mouse.press(Button.left)
    time.sleep(uniform(*_CLICK_POST_DELAY))
    _mouse.release(Button.left)


def _resolve_entity(
    mem: ProcessMemory,
    client: int,
    entity_id: int,
) -> int:
    """
    Walk the entity list to resolve an entity controller pawn address.

    Returns the pawn address, or 0 if any pointer in the chain is invalid.
    """
    ent_list = mem.read_ptr(client + offsets["dwEntityList"])
    if not ent_list:
        return 0

    ent_entry = mem.read_ptr(ent_list + 0x8 * (entity_id >> 9) + 0x10)
    if not ent_entry:
        return 0

    entity = mem.read_ptr(ent_entry + 112 * (entity_id & 0x1FF))
    return entity


def trig(
    stop_event: threading.Event,
    config: ThreadConfig,
    mem: ProcessMemory,
    client: int,
) -> None:
    """
    Trigger bot thread.

    Fires a left-click when the crosshair is over a living enemy while the
    configured trigger key is held.

    Args:
        stop_event: Signals the thread to exit cleanly.
        config: Shared mutable configuration (enable flag, trigger key).
        mem: Process memory handle.
        client: client.dll base address.
    """
    while not stop_event.is_set():
        try:
            if not config.enable_trigger:
                time.sleep(_SLEEP_INACTIVE)
                continue

            if not _is_cs2_focused():
                time.sleep(_SLEEP_INACTIVE)
                continue

            if not keyboard.is_pressed(config.trigger_key):
                time.sleep(_SLEEP_RELEASED)
                continue

            # Only read memory once the trigger key is confirmed held
            player = mem.read_ptr(client + offsets["dwLocalPlayerPawn"])
            if not player:
                time.sleep(_SLEEP_PRESSED)
                continue

            entity_id = mem.read_i32(player + offsets["m_iIDEntIndex"])
            if not isinstance(entity_id, int) or entity_id <= 0:
                time.sleep(_SLEEP_PRESSED)
                continue

            local_team = mem.read_i32(player + offsets["m_iTeamNum"])

            entity = _resolve_entity(mem, client, entity_id)
            if not entity:
                time.sleep(_SLEEP_PRESSED)
                continue

            entity_team = mem.read_i32(entity + offsets["m_iTeamNum"])
            if entity_team == local_team:
                time.sleep(_SLEEP_PRESSED)
                continue

            entity_hp = mem.read_i32(entity + offsets["m_iHealth"])
            if isinstance(entity_hp, int) and entity_hp > 0:
                _click()

            time.sleep(_SLEEP_PRESSED)

        except KeyboardInterrupt:
            break

        except Exception as e:
            logger.warning("Triggerbot error: %s", e)
            time.sleep(0.1)
