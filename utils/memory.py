import struct
from ctypes import Structure, sizeof
from dataclasses import dataclass
from typing import TypeVar

import pymem
import pymem.exception

T = TypeVar("T", bound=Structure)


@dataclass(slots=True)
class ReadRequest:
    address: int
    size: int


class MemoryReadError(Exception):
    pass


class ProcessMemory:
    """Typed wrapper around pymem"""

    __slots__ = "_pm"

    def __init__(self, process_name: str) -> None:
        self._pm = pymem.Pymem(process_name=process_name)

    def read_i32(self, address: int) -> int:
        return self._pm.read_int(address=address)

    def read_i64(self, address: int) -> int:
        return self._pm.read_longlong(address=address)

    def read_f32(self, address: int) -> float:
        return self._pm.read_float(address=address)

    def read_ptr(self, address: int) -> int:
        try:
            return self._pm.read_longlong(address=address)
        except pymem.exception.MemoryReadError:
            return 0

    def read_struct(self, address: int, struct_type: type[T]) -> T | None:
        try:
            raw = self._pm.read_bytes(address=address, length=sizeof(struct_type))
            return struct_type.from_buffer_copy(raw)
        except pymem.exception.MemoryReadError:
            return None

    def read_bytes(self, address: int, size: int) -> bytes | None:
        try:
            return self._pm.read_bytes(address=address, length=size)
        except pymem.exception.MemoryReadError:
            return None

    def read_region(self, base: int, size: int) -> memoryview | None:
        raw = self.read_bytes(address=base, size=size)
        return memoryview(raw) if raw else None

    def unpack_from_region(self, region: memoryview, fmt: str, offset: int) -> tuple:
        size = struct.calcsize(fmt)
        return struct.unpack_from(fmt, region, offset)

    @property
    def handle(self):
        return self._pm.process_handle

    @property
    def pymem(self) -> pymem.Pymem:
        return self._pm
