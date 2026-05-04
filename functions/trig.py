import logging
import threading
import time
from random import uniform

import keyboard
from pynput.mouse import Button, Controller
from win32gui import GetForegroundWindow, GetWindowText

from utils.config import config as cfg
from utils.memory import ProcessMemory
from utils.offsets import offsets
from utils.thread_manager import ThreadConfig

_mouse = Controller()
logger = logging.getLogger(__name__)


def _is_cs2_focused() -> bool:
    return GetWindowText(GetForegroundWindow()) == cfg.CS2_WINDOW_TITLE


def _click() -> None:
    """Simulate a left-click with randomised pre/post delays."""
    time.sleep(uniform(*cfg.CLICK_PRE_DELAY))
    _mouse.press(Button.left)
    time.sleep(uniform(*cfg.CLICK_POST_DELAY))
    _mouse.release(Button.left)


def _resolve_entity(mem: ProcessMemory, client: int, entity_id: int) -> int:
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


def trig(stop_event: threading.Event, config: ThreadConfig, mem: ProcessMemory, client: int) -> None:
    """
    Trigger bot thread.

    Args:
        stop_event (threading.Event): Signals the thread to exit cleanly.
        config (ThreadConfig): Shared mutable configuration (enable flag, trigger key).
        mem (ProcessMemory): Process memory handle.
        client (int): client.dll base address.
    """
    while not stop_event.is_set():
        try:
            if not config.enable_trigger:
                time.sleep(cfg.SLEEP_INACTIVE)
                continue

            if not _is_cs2_focused():
                time.sleep(cfg.SLEEP_INACTIVE)
                continue

            if not keyboard.is_pressed(config.trigger_key):
                time.sleep(cfg.SLEEP_RELEASED)
                continue

            # Only read memory once the trigger key is confirmed held
            player = mem.read_ptr(client + offsets["dwLocalPlayerPawn"])
            if not player:
                time.sleep(cfg.SLEEP_PRESSED)
                continue

            entity_id = mem.read_i32(player + offsets["m_iIDEntIndex"])
            if not isinstance(entity_id, int) or entity_id <= 0:
                time.sleep(cfg.SLEEP_PRESSED)
                continue

            local_team = mem.read_i32(player + offsets["m_iTeamNum"])

            entity = _resolve_entity(mem, client, entity_id)
            if not entity:
                time.sleep(cfg.SLEEP_PRESSED)
                continue

            entity_team = mem.read_i32(entity + offsets["m_iTeamNum"])
            if entity_team == local_team:
                time.sleep(cfg.SLEEP_PRESSED)
                continue

            entity_hp = mem.read_i32(entity + offsets["m_iHealth"])
            if isinstance(entity_hp, int) and entity_hp > 0:
                _click()

            time.sleep(cfg.SLEEP_PRESSED)

        except KeyboardInterrupt:
            break

        except Exception as e:
            logger.warning("Triggerbot error: %s", e)
            time.sleep(0.1)
