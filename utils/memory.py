from ctypes import Structure, sizeof
from typing import TypeVar

import win32api
import win32con
import win32process
from PyMemoryEditor import OpenProcess, ProcessOperationsEnum
from pywintypes import error as Win32Error

T = TypeVar("T", bound=Structure)

READ_ONLY_ACCESS = ProcessOperationsEnum.PROCESS_VM_READ | ProcessOperationsEnum.PROCESS_QUERY_INFORMATION
STILL_ACTIVE = 259  # GetExitCodeProcess result for a process that has not exited

# PyMemoryEditor reports a failed read as a plain OSError (unmapped page, partial read, bad address)
MemoryReadError = OSError


class ProcessMemory:
    """Typed wrapper around PyMemoryEditor.

    The target is opened with `READ_ONLY_ACCESS` and nothing else: PyMemoryEditor takes the access mask
    as an argument and never enables SeDebugPrivilege, so the features run through a handle that carries
    no write or inject capability. That is the point of the read-only showcase, and a concrete artifact
    (handle rights + absence of the debug privilege) for anti-cheat work.

    Error contract:
    - read_i32 / read_u8 / read_f32 raise MemoryReadError: a 0 sentinel would be
      indistinguishable from real data (0 is LIFE_ALIVE and a valid team; 0.0 sensitivity is a divisor).
    - read_ptr returns 0; read_struct / read_bytes / read_region return None.
    Pointer-chain walks must catch MemoryReadError per entity (see EntityManager.get_entities).
    """

    __slots__ = ("_pm",)

    def __init__(self, process_name: str, pm: OpenProcess | None = None) -> None:
        # pm lets tests inject a fake backend and still exercise the real read_* contract above
        self._pm = pm if pm is not None else OpenProcess(name=process_name, permission=READ_ONLY_ACCESS)

    def read_i32(self, address: int) -> int:
        return self._pm.read_int(address)

    def read_u8(self, address: int) -> int:
        """Read a single unsigned byte.

        Source 2 declares m_iTeamNum / m_lifeState as uint8 and packs the next
        field immediately after them, so read_i32 on those offsets silently
        drags in up to three neighbouring bytes.
        """
        return self._pm.read_uchar(address)

    def read_f32(self, address: int) -> float:
        return self._pm.read_float(address)

    def read_ptr(self, address: int) -> int:
        try:
            return self._pm.read_longlong(address)
        except MemoryReadError:
            return 0

    def read_struct(self, address: int, struct_type: type[T]) -> T | None:
        try:
            raw = self._pm.read_bytes(address, sizeof(struct_type))
            return struct_type.from_buffer_copy(raw)
        except MemoryReadError:
            return None

    def read_bytes(self, address: int, size: int) -> bytes | None:
        try:
            return self._pm.read_bytes(address, size)
        except MemoryReadError:
            return None

    def read_region(self, base: int, size: int) -> memoryview | None:
        raw = self.read_bytes(address=base, size=size)
        return memoryview(raw) if raw else None

    def module_base(self, module_name: str) -> int | None:
        """Load address of a module in the target, or None if it is not loaded (yet)."""
        wanted = module_name.lower()
        for module in self._pm.get_modules():
            if module.name.lower() == wanted:
                return module.base_address
        return None

    def is_alive(self) -> bool:
        # our own handle keeps the pid reserved after cs2.exe exits, so the pid cannot have been recycled
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, self._pm.pid)
        except Win32Error:
            return False
        try:
            return win32process.GetExitCodeProcess(handle) == STILL_ACTIVE
        finally:
            handle.Close()

    def close(self) -> None:
        self._pm.close()
