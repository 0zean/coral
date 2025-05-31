import struct
from ctypes import sizeof
from typing import Any

import pymem.exception  # type: ignore
from pymem import Pymem  # type: ignore

from .structs import C_UTL_VECTOR, Offsets, Vec2, Vec3


def pymem_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pymem.exception.MemoryReadError as e:
            print(f"Memory read error occurred in {func.__name__}: {e}")

    return wrapper


class PlayerPawn:
    def __init__(self, pm: Pymem, address: int, client: Any, offsets: Offsets):
        self.pm = pm
        self.client = client
        self.address = address
        self.offsets = offsets
        self.ViewAngle = self.get_view_angle()
        self.AimPunchAngle = self.get_aim_punch_angle()
        self.ShotsFired = self.get_shots_fired()
        self.AimPunchCache = self.get_aim_punch_cache()
        self.ClientSensitivity = self.get_sensitivity()

    @pymem_exception
    def get_view_angle(self) -> Vec2:
        return Vec2(*struct.unpack("ff", self.pm.read_bytes(self.address + self.offsets.m_angEyeAngles, 8)))

    @pymem_exception
    def get_aim_punch_angle(self) -> Vec3:
        return Vec3(*struct.unpack("fff", self.pm.read_bytes(self.address + self.offsets.m_aimPunchAngle, 12)))

    @pymem_exception
    def get_shots_fired(self) -> int:
        return self.pm.read_int(self.address + self.offsets.m_iShotsFired)

    @pymem_exception
    def get_aim_punch_cache(self) -> C_UTL_VECTOR:
        cache_bytes = self.pm.read_bytes(self.address + self.offsets.m_aimPunchCache, sizeof(C_UTL_VECTOR))
        return C_UTL_VECTOR.from_buffer_copy(cache_bytes)

    @pymem_exception
    def cache_to_punch(self) -> Vec3:
        punch_angle_ptr = self.AimPunchCache.Data + (self.AimPunchCache.Count - 1) * sizeof(Vec3)
        punch_angle_bytes = self.pm.read_bytes(punch_angle_ptr, sizeof(Vec3))
        return Vec3.from_buffer_copy(punch_angle_bytes)

    @pymem_exception
    def get_sensitivity(self) -> float:
        sensitivity_ptr = self.pm.read_longlong(self.client + self.offsets.dwSensitivity)
        return self.pm.read_float(sensitivity_ptr + self.offsets.dwSensitivity_sensitivity)
