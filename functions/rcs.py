import threading
import time
from typing import Any

from pymem import Pymem  # type: ignore
from win32gui import GetForegroundWindow, GetWindowText

from utils.mouse import get_mouse_pos, move_mouse_to_location
from utils.offsets import offsets
from utils.player import PlayerPawn
from utils.structs import Vec2
from utils.thread_manager import ThreadConfig


def rcs(stop_event: threading.Event, config: ThreadConfig, pm: Pymem, client: Any, smoothing: float = 1.0) -> None:
    """
    Recoil control system function.

    Args:
        stop_event (threading.Event): Event to signal stopping.
        config (ThreadConfig): Shared configuration.
        pm (Pymem): Pymem instance.
        client (Any): Client module base address.
        smoothing (float, optional): Smoothing factor. Defaults to 1.0.
    """
    old_punch = Vec2(0.0, 0.0)
    while not stop_event.is_set():
        try:
            if not config.enable_rcs:
                time.sleep(0.1)
                continue

            amt = config.rcs_amount

            if GetWindowText(GetForegroundWindow()) != "Counter-Strike 2":
                time.sleep(0.005)
                continue

            player = pm.read_longlong(client + offsets["dwLocalPlayerPawn"])
            if not player:
                time.sleep(0.005)
                continue

            local = PlayerPawn(pm, player, client, offsets)  # type: ignore
            shots_fired = local.get_shots_fired()
            punch_angle = local.AimPunchAngle
            sensitivity = local.client_sensitivity

            if 1 < shots_fired < 999999:
                new_punch = Vec2((punch_angle.x - old_punch.x) * -1.0, (punch_angle.y - old_punch.y) * -1.0)

                move = Vec2((new_punch.y * amt / sensitivity) / -0.022, (new_punch.x * amt / sensitivity) / 0.022)

                current_mouse = get_mouse_pos()
                target_mouse = Vec2(current_mouse.x + move.x, current_mouse.y + move.y)

                smooth_factor = max(1.0, min(smoothing, 3.0))
                delta = Vec2(target_mouse.x - current_mouse.x, target_mouse.y - current_mouse.y)

                smoothed_move = Vec2(delta.x / smooth_factor, delta.y / smooth_factor)
                next_mouse = Vec2(current_mouse.x + smoothed_move.x, current_mouse.y + smoothed_move.y)

                # Move mouse relative to center of screen
                move_mouse_to_location(next_mouse)

                old_punch = Vec2(punch_angle.x, punch_angle.y)
            else:
                old_punch = Vec2(0.0, 0.0)

            old_punch = Vec2(punch_angle.x, punch_angle.y)

        except KeyboardInterrupt:
            break

        except Exception as e:
            print(f"RCS error: {e}")
            time.sleep(0.005)
            continue
