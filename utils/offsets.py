import json

from .structs import Offsets


class Client:
    def __init__(self):
        try:
            with open("output/offsets.json") as f:
                self.offsets = json.load(f)
        except Exception as e:
            print(f"Unable to get offsets: {e}")
            exit()

        try:
            with open("output/client_dll.json") as f:
                self.clientdll = json.load(f)
        except Exception as e:
            print(f"Unable to get client.dll: {e}")
            exit()

    def offset(self, a: str) -> int:
        try:
            return self.offsets["client.dll"][a]
        except Exception as e:
            print(f"Offset {a} not found: {e}")
            exit()

    def get(self, a: str, b: str) -> int:
        try:
            return self.clientdll["client.dll"]["classes"][a]["fields"][b]
        except Exception as e:
            print(f"Unable to get {a}, {b}: {e}")
            exit()


nv = Client()

offsets_dict = {
    "dwEntityList": nv.offset("dwEntityList"),
    "dwLocalPlayerPawn": nv.offset("dwLocalPlayerPawn"),
    "dwSensitivity": nv.offset("dwSensitivity"),
    "dwSensitivity_sensitivity": nv.offset("dwSensitivity_sensitivity"),
    "m_iIDEntIndex": nv.get("C_CSPlayerPawnBase", "m_iIDEntIndex"),
    "m_iTeamNum": nv.get("C_BaseEntity", "m_iTeamNum"),
    "m_iHealth": nv.get("C_BaseEntity", "m_iHealth"),
    "m_iShotsFired": nv.get("C_CSPlayerPawn", "m_iShotsFired"),
    "m_aimPunchCache": nv.get("C_CSPlayerPawn", "m_aimPunchCache"),
    "m_angEyeAngles": nv.get("C_CSPlayerPawnBase", "m_angEyeAngles"),
    "m_aimPunchAngle": nv.get("C_CSPlayerPawn", "m_aimPunchAngle"),
    "dwViewMatrix": nv.offset("dwViewMatrix"),
    "m_lifeState": nv.get("C_BaseEntity", "m_lifeState"),
    "m_pGameSceneNode": nv.get("C_BaseEntity", "m_pGameSceneNode"),
    "m_modelState": nv.get("CSkeletonInstance", "m_modelState"),
    "m_hPlayerPawn": nv.get("CCSPlayerController", "m_hPlayerPawn"),
    "m_iszPlayerName": nv.get("CBasePlayerController", "m_iszPlayerName"),
}

offsets = Offsets()
offsets.add_offsets(offsets_dict)
