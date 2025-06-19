import time
from random import uniform
from typing import Any

import keyboard
from pymem import Pymem  # type: ignore
from pynput.mouse import Button, Controller
from win32gui import GetForegroundWindow, GetWindowText

from utils.offsets import offsets

mouse = Controller()


def trig(pm: Pymem, client: Any, triggerkey: str = "shift") -> None:
    while True:
        try:
            if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2":
                continue

            if keyboard.is_pressed(triggerkey):
                player = pm.read_longlong(client + offsets["dwLocalPlayerPawn"])
                entityId = pm.read_int(int(player) + offsets["m_iIDEntIndex"])

                if isinstance(entityId, int) and entityId > 0:
                    entList = pm.read_longlong(client + offsets["dwEntityList"])

                    entEntry = pm.read_longlong(int(entList) + 0x8 * (entityId >> 9) + 0x10)
                    entity = pm.read_longlong(int(entEntry) + 120 * (entityId & 0x1FF))

                    entityTeam = pm.read_int(int(entity) + offsets["m_iTeamNum"])
                    playerTeam = pm.read_int(int(player) + offsets["m_iTeamNum"])

                    if entityTeam != playerTeam:
                        entityHp = pm.read_int(int(entity) + offsets["m_iHealth"])
                        if isinstance(entityHp, int) and entityHp > 0:
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
