from typing import Any

from pymem import Pymem

from utils.visuals import batch_bone_read


class Entity:
    def __init__(
        self, address: int, team: int, health: int, name: str, bones: dict[str, tuple[float, float, float]]
    ) -> None:
        self.address = address
        self.team = team
        self.health = health
        self.name = name
        self.bones = bones


class EntityManager:
    def __init__(self, pm: Pymem, client: Any, offsets: dict[str, int], bone_indicies: dict[str, int]) -> None:
        self.pm = pm
        self.client = client
        self.offsets = offsets
        self.bone_indicies = bone_indicies

    def get_local_player(self) -> tuple[int, int]:
        pawn_addr = self.pm.read_longlong(self.client + self.offsets["dwLocalPlayerPawn"])
        team = self.pm.read_int(pawn_addr + self.offsets["m_iTeamNum"])
        return pawn_addr, team

    def _read_bones(self, bone_matrix_addr: int) -> dict[str, tuple[float, float, float]]:
        return batch_bone_read(self.pm, bone_matrix_addr, self.bone_indicies)

    def get_entities(self) -> list[Entity]:
        entities = []

        entity_list = self.pm.read_longlong(self.client + self.offsets["dwEntityList"])
        local_addr, local_team = self.get_local_player()

        for i in range(64):
            list_entry = self.pm.read_longlong(entity_list + ((8 * (i & 0x7FFF) >> 9) + 16))
            if not list_entry:
                continue

            entity_controller = self.pm.read_longlong(list_entry + (112) * (i & 0x1FF))
            if not entity_controller:
                continue

            entity_controller_pawn = self.pm.read_longlong(entity_controller + self.offsets["m_hPlayerPawn"])
            if not entity_controller_pawn:
                continue

            list_entry2 = self.pm.read_longlong(entity_list + (0x8 * ((entity_controller_pawn & 0x7FFF) >> 9) + 16))
            if not list_entry2:
                continue

            entity_pawn_addr = self.pm.read_longlong(list_entry2 + 0x70 * (entity_controller_pawn & 0x1FF))
            if not entity_pawn_addr or entity_pawn_addr == local_addr:
                continue

            if self.pm.read_int(entity_pawn_addr + self.offsets["m_lifeState"]) != 256:
                continue

            entity_team = self.pm.read_int(entity_pawn_addr + self.offsets["m_iTeamNum"])
            if entity_team == local_team:
                continue

            name = self.pm.read_string(entity_controller + self.offsets["m_iszPlayerName"], 64).split("\x00")[0]
            health = self.pm.read_int(entity_pawn_addr + self.offsets["m_iHealth"])
            game_scene = self.pm.read_longlong(entity_pawn_addr + self.offsets["m_pGameSceneNode"])
            bone_matrix = self.pm.read_longlong(game_scene + self.offsets["m_modelState"] + 0x80)
            bones = self._read_bones(int(bone_matrix))
            entities.append(Entity(entity_pawn_addr, entity_team, health, name, bones))
        return entities
