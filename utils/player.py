import struct
from typing import Any

import pymem.exception  # type: ignore
from pymem import Pymem  # type: ignore

from .structs import Vec2, Vec3


def pymem_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pymem.exception.MemoryReadError as e:
            print(f"Memory read error occurred in {func.__name__}: {e}")

    return wrapper


class PlayerPawn:
    def __init__(self, pm: Pymem, address: int, client: Any, offsets: dict[str, int]):
        self.pm = pm
        self.client = client
        self.address = address
        self.offsets = offsets
        self._cache = {}
        self.ViewAngle = self.get_view_angle()
        self.AimPunchAngle = self.get_aim_punch_angle()
        self.ShotsFired = self.get_shots_fired()
        self.origin = self.get_origin()
        self.refresh()

    def refresh(self) -> None:
        self._cache["team"] = self.pm.read_int(self.address + self.offsets["m_iTeamNum"])
        self._cache["health"] = self.pm.read_int(self.address + self.offsets["m_iHealth"])
        self._cache["life_state"] = self.pm.read_int(self.address + self.offsets["m_lifeState"])

        sensitivity_ptr = self.pm.read_longlong(self.client + self.offsets["dwSensitivity"])
        self._cache["client_sensitivity"] = self.pm.read_float(
            sensitivity_ptr + self.offsets["dwSensitivity_sensitivity"]
        )

    @property
    def team(self) -> int:
        return self._cache["team"]

    @property
    def health(self) -> int:
        return self._cache["health"]

    @property
    def life_state(self) -> int:
        return self._cache["life_state"]

    @property
    def client_sensitivity(self) -> float:
        return self._cache["client_sensitivity"]

    @pymem_exception
    def get_origin(self) -> Vec3:
        return Vec3(*struct.unpack("fff", self.pm.read_bytes(self.address + self.offsets["m_vOldOrigin"], 12)))

    @pymem_exception
    def get_view_angle(self) -> Vec2:
        return Vec2(*struct.unpack("ff", self.pm.read_bytes(self.address + self.offsets["m_angEyeAngles"], 8)))

    @pymem_exception
    def get_aim_punch_angle(self) -> Vec3:
        return Vec3(*struct.unpack("fff", self.pm.read_bytes(self.address + self.offsets["m_aimPunchAngle"], 12)))

    @pymem_exception
    def get_shots_fired(self) -> int:
        return self.pm.read_int(self.address + self.offsets["m_iShotsFired"])
