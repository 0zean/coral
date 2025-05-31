import time
from typing import Any

from pymem import Pymem
from win32gui import GetForegroundWindow, GetWindowText

from utils.mouse import move_mouse
from utils.offsets import offsets
from utils.player import PlayerPawn
from utils.structs import Vec3


def rcs(pm: Pymem, client: Any, amt: float) -> None:
    old_punch = Vec3(0.0, 0.0, 0.0)
    while True:
        try:
            if GetWindowText(GetForegroundWindow()) != "Counter-Strike 2":
                time.sleep(0.05)
                continue

            else:
                player = pm.read_longlong(client + offsets.dwLocalPlayerPawn)

                if player:
                    local = PlayerPawn(pm, player, client, offsets)

                    if local.get_aim_punch_cache() and local.get_view_angle() and local.get_shots_fired():

                        punch_angle = Vec3()

                        while local.AimPunchCache.Count <= 0 or local.AimPunchCache.Count > 0xFFFF:
                            time.sleep(0.01)
                            continue

                        punch_angle = local.cache_to_punch()

                        if local.get_shots_fired() > 1:

                            new_punch = Vec3(punch_angle.x - old_punch.x, punch_angle.y - old_punch.y, 0)

                            new_angle = Vec3(
                                local.ViewAngle.x - new_punch.x * amt, local.ViewAngle.y - new_punch.y * amt, 0
                            )

                            move_mouse(
                                x=int(((new_angle.y - local.ViewAngle.y) / local.ClientSensitivity) / -0.022),
                                y=int(((new_angle.x - local.ViewAngle.x) / local.ClientSensitivity) / 0.022),
                                set_last_moved=False,
                            )

                            old_punch = punch_angle

                        else:
                            old_punch = punch_angle

                else:
                    continue

                time.sleep(0.001)

        except KeyboardInterrupt:
            break

        except Exception:
            time.sleep(0.01)
            continue
