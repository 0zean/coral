import struct

from utils.memory import ProcessMemory
from utils.structs import EntitySnapshot


class EntityManager:
    """Reads all visible entities at once"""

    __slots__ = ("_mem", "_client", "_offsets", "_bone_indices")

    def __init__(self, mem: ProcessMemory, client: int, offsets: dict[str, int], bone_indices: dict[str, int]) -> None:
        self._mem = mem
        self._client = client
        self._offsets = offsets
        self._bone_indices = bone_indices

    def _local_team(self) -> tuple[int, int]:
        pawn = self._mem.read_ptr(self._client + self._offsets["dwLocalPlayerPawn"])
        team = self._mem.read_i32(pawn + self._offsets["m_iTeamNum"])
        return pawn, team

    def _batch_bones(self, bone_matrix: int) -> dict[str, tuple[float, float, float]]:
        indices = self._bone_indices
        if not indices:
            return {}

        min_idx = min(indices.values())
        max_idx = max(indices.values())
        base_offset = min_idx * 0x20
        total_bytes = (max_idx - min_idx + 1) * 0x20

        region = self._mem.read_region(bone_matrix + base_offset, total_bytes)
        if region is None:
            return {}

        bones: dict[str, tuple[float, float, float]] = {}
        for name, idx in indices.items():
            off = (idx - min_idx) * 0x20
            x, y, z = struct.unpack_from("fff", region, off)
            bones[name] = (x, y, z)
        return bones

    def get_entities(self) -> list[EntitySnapshot]:
        mem = self._mem
        off = self._offsets
        client = self._client
        snapshots: list[EntitySnapshot] = []

        ent_list = mem.read_ptr(client + off["dwEntityList"])
        if not ent_list:
            return snapshots

        local_addr, local_team = self._local_team()

        for i in range(64):
            list_entry = mem.read_ptr(ent_list + ((8 * (i & 0x7FFF) >> 9) + 16))
            if not list_entry:
                continue

            controller = mem.read_ptr(list_entry + (112) * (i & 0x1FF))
            if not controller:
                continue

            pawn_handle = mem.read_i32(controller + off["m_hPlayerPawn"])
            if not pawn_handle:
                continue

            list2 = mem.read_ptr(ent_list + (0x8 * ((pawn_handle & 0x7FFF) >> 9) + 16))
            if not list2:
                continue

            pawn = mem.read_ptr(list2 + 0x70 * (pawn_handle & 0x1FF))
            if not pawn or pawn == local_addr:
                continue

            if mem.read_i32(pawn + off["m_lifeState"]) != 256:
                continue

            if mem.read_i32(pawn + off["m_iTeamNum"]) == local_team:
                continue

            raw_name = mem.read_bytes(controller + off["m_iszPlayerName"], 64)
            name = raw_name.split(b"\x00")[0].decode("utf-8", "ignore") if raw_name else "?"

            health = mem.read_i32(pawn + off["m_iHealth"])
            team = mem.read_i32(pawn + off["m_iTeamNum"])

            game_scene = mem.read_ptr(pawn + off["m_pGameSceneNode"])
            bone_matrix = mem.read_ptr(game_scene + off["m_modelState"] + 0x80) if game_scene else 0
            bones = self._batch_bones(bone_matrix) if bone_matrix else {}

            snapshots.append(
                EntitySnapshot(
                    address=pawn,
                    team=team,
                    health=health,
                    name=name,
                    bones=bones,
                )
            )

        return snapshots
