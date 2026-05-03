import functools
import logging
from ctypes import sizeof
from typing import Any

from utils.memory import MemoryReadError, ProcessMemory
from utils.structs import C_UTL_VECTOR, PlayerState, Vec3

logger = logging.getLogger(__name__)


def pymem_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MemoryReadError as e:
            logger.warning("Memory read error in %s: %s", func.__name__, e)
            return None

    return wrapper


class PlayerPawn:
    def __init__(self, mem: ProcessMemory, address: int, client: Any, offsets: dict[str, int]) -> None:
        self._mem = mem
        self._address = address
        self._client = client
        self._offsets = offsets

    def snapshot(self) -> PlayerState | None:
        off = self._offsets
        addr = self._address
        mem = self._mem

        team = mem.read_i32(addr + off["m_iTeamNum"])
        health = mem.read_i32(addr + off["m_iHealth"])
        life_state = mem.read_i32(addr + off["m_lifeState"])
        shots_fired = mem.read_i32(addr + off["m_iShotsFired"])

        # View angle
        raw_va = mem.read_bytes(addr + off["m_angEyeAngles"], 8)
        if raw_va is None:
            return None
        view_angle = tuple(raw_va[i : i + 4] for i in (0, 4))
        import struct

        vax, vay = struct.unpack("ff", raw_va)

        # Aim punch
        punch = self._read_aim_punch()

        # Sensitivity
        sens_ptr = mem.read_ptr(self._client + off["dwSensitivity"])
        sensitivity = mem.read_f32(sens_ptr + off["dwSensitivity_sensitivity"]) if sens_ptr else 1.0

        return PlayerState(
            team=team,
            health=health,
            life_state=life_state,
            shots_fired=shots_fired,
            view_angle=(vax, vay),
            aim_punch=punch,
            origin=self._read_origin(),
            sensitivity=sensitivity,
        )

    def _read_origin(self) -> tuple[float, float, float]:
        import struct

        raw = self._mem.read_bytes(self._address + self._offsets["m_vOldOrigin"], 12)
        return struct.unpack("fff", raw) if raw else (0.0, 0.0, 0.0)

    def _read_aim_punch(self) -> tuple[float, float, float]:
        mem = self._mem
        off = self._offsets

        services_ptr = mem.read_ptr(self._address + off["m_pAimPunchServices"])
        if not services_ptr:
            return (0.0, 0.0, 0.0)

        utlvec = mem.read_struct(services_ptr + 0x88, C_UTL_VECTOR)
        if utlvec is None or not (0 < utlvec.Count < 0xFFFF) or not utlvec.Data:
            return (0.0, 0.0, 0.0)

        last = utlvec.Count - 1
        raw = mem.read_bytes(utlvec.Data + last * sizeof(Vec3), sizeof(Vec3))
        if raw is None:
            return (0.0, 0.0, 0.0)

        v = Vec3.from_buffer_copy(raw)
        return (v.x, v.y, v.z)
