import time
from random import uniform
from typing import Any

import keyboard
from pymem import Pymem  # type: ignore
from pynput.mouse import Button, Controller
from win32gui import GetForegroundWindow, GetWindowText

from utils.offsets import offsets
from utils.player import PlayerPawn

mouse = Controller()


import threading

from utils.thread_manager import ThreadConfig


def trig(stop_event: threading.Event, config: ThreadConfig, pm: Pymem, client: Any) -> None:
    """
    Trigger bot function.

    Args:
        stop_event (threading.Event): Event to signal stopping.
        config (ThreadConfig): Shared configuration.
        pm (Pymem): Pymem instance.
        client (Any): Client module base address.
    """
    while not stop_event.is_set():
        try:
            if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2":
                time.sleep(0.1)
                continue

            # Read from config
            triggerkey = config.trigger_key
            if not config.enable_trigger:
                time.sleep(0.1)
                continue

            player = pm.read_longlong(client + offsets["dwLocalPlayerPawn"])
            entity_id = pm.read_int(player + offsets["m_iIDEntIndex"])
            local = PlayerPawn(pm, player, client, offsets)

            if keyboard.is_pressed(triggerkey):
                if isinstance(entity_id, int) and entity_id > 0:
                    ent_list = pm.read_longlong(client + offsets["dwEntityList"])

                    ent_entry = pm.read_longlong(ent_list + 0x8 * (entity_id >> 9) + 0x10)
                    entity = pm.read_longlong(ent_entry + 112 * (entity_id & 0x1FF))

                    entity_team = pm.read_int(entity + offsets["m_iTeamNum"])
                    if entity_team != local.team:
                        entity_hp = pm.read_int(entity + offsets["m_iHealth"])
                        if isinstance(entity_hp, int) and entity_hp > 0:
                            time.sleep(uniform(0.01, 0.03))
                            mouse.press(Button.left)
                            time.sleep(uniform(0.01, 0.05))
                            mouse.release(Button.left)

                time.sleep(0.03)
            else:
                time.sleep(0.1)

        except KeyboardInterrupt:
            break

        except Exception:
            pass
