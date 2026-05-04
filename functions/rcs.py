import logging
import threading
import time

from win32gui import GetForegroundWindow, GetWindowText

from utils.config import config as cfg
from utils.memory import ProcessMemory
from utils.mouse import get_mouse_pos, move_mouse_to_location
from utils.offsets import offsets
from utils.player import PlayerPawn
from utils.structs import Vec2
from utils.thread_manager import ThreadConfig

logger = logging.getLogger(__name__)


def rcs(
    stop_event: threading.Event, config: ThreadConfig, mem: ProcessMemory, client: int, smoothing: float = 1.0
) -> None:
    """
    Recoil control system function.

    Args:
        stop_event (threading.Event): Event to signal stopping.
        config (ThreadConfig): Shared configuration.
        mem (ProcessMemory): Pymem instance.
        client (int): Client module base address.
        smoothing (float, optional): Smoothing factor. Defaults to 1.0.
    """
    smooth_factor = max(cfg.SMOOTHING_MIN, min(smoothing, cfg.SMOOTHING_MAX))
    old_punch = Vec2(0.0, 0.0)
    pawn: PlayerPawn | None = None

    while not stop_event.is_set():
        try:
            if not config.enable_rcs:
                pawn = None
                old_punch = Vec2(0.0, 0.0)
                time.sleep(cfg.SLEEP_INACTIVE)
                continue

            amt = config.rcs_amount

            if GetWindowText(GetForegroundWindow()) != cfg.CS2_WINDOW_TITLE:
                time.sleep(cfg.SLEEP_TICK)
                continue

            player_addr = mem.read_ptr(client + offsets["dwLocalPlayerPawn"])

            if not player_addr:
                pawn = None
                time.sleep(cfg.SLEEP_TICK)
                continue

            if pawn is None or pawn._address != player_addr:
                pawn = PlayerPawn(mem, player_addr, client, offsets)

            state = pawn.snapshot()
            if state is None:
                time.sleep(cfg.SLEEP_TICK)
                continue

            shots_fired = state.shots_fired
            punch_x, punch_y, _ = state.aim_punch
            sensitivity = state.sensitivity
            amt = config.rcs_amount

            if 1 < shots_fired < 999_999:
                delta_x = (punch_x - old_punch.x) * -1.0
                delta_y = (punch_y - old_punch.y) * -1.0

                raw_move = Vec2(
                    x=(delta_y * amt / sensitivity) / -0.022,
                    y=(delta_x * amt / sensitivity) / 0.022,
                )

                current = get_mouse_pos()
                target = Vec2(current.x + raw_move.x, current.y + raw_move.y)
                smoothed = Vec2(
                    x=current.x + (target.x - current.x) / smooth_factor,
                    y=current.y + (target.y - current.y) / smooth_factor,
                )

                move_mouse_to_location(smoothed)
                old_punch = Vec2(punch_x, punch_y)
            else:
                old_punch = Vec2(0.0, 0.0)

            old_punch = Vec2(punch_x, punch_y)

        except KeyboardInterrupt:
            break

        except Exception as exc:
            logger.warning("RCS error: %s", exc)
            time.sleep(cfg.SLEEP_TICK)
            continue
