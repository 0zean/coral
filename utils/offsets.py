import json


class Client:
    def __init__(self) -> None:
        try:
            with open("output/offsets.json") as f:
                self.offsets = json.load(f)
            with open("output/client_dll.json") as f:
                self.clientdll = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load offsets or client DLL: {e}")

    def offset(self, key: str) -> int:
        try:
            return self.offsets["client.dll"][key]
        except KeyError:
            raise KeyError(f"Offset '{key}' not found in offsets.json")
        except Exception as e:
            raise RuntimeError(f"Error retrieving offset '{key}': {e}")

    def get(self, class_name: str, field_name: str) -> int:
        try:
            return self.clientdll["client.dll"]["classes"][class_name]["fields"][field_name]
        except KeyError:
            raise KeyError(f"Field '{field_name}' not found in class '{class_name}' in client_dll.json")
        except Exception as e:
            raise RuntimeError(f"Error retrieving field '{field_name}' from class '{class_name}': {e}")


nv = Client()

offsets: dict[str, int] = {
    "dwEntityList": nv.offset("dwEntityList"),
    "dwLocalPlayerPawn": nv.offset("dwLocalPlayerPawn"),
    "dwSensitivity": nv.offset("dwSensitivity"),
    "dwSensitivity_sensitivity": nv.offset("dwSensitivity_sensitivity"),
    "dwViewAngles": nv.offset("dwViewAngles"),
    "m_iIDEntIndex": nv.get("C_CSPlayerPawn", "m_iIDEntIndex"),
    "m_iTeamNum": nv.get("C_BaseEntity", "m_iTeamNum"),
    "m_iHealth": nv.get("C_BaseEntity", "m_iHealth"),
    "m_iShotsFired": nv.get("C_CSPlayerPawn", "m_iShotsFired"),
    "m_angEyeAngles": nv.get("C_CSPlayerPawn", "m_angEyeAngles"),
    "m_aimPunchAngle": nv.get("C_CSPlayerPawn", "m_aimPunchAngle"),
    "m_vOldOrigin": nv.get("C_BasePlayerPawn", "m_vOldOrigin"),
    "dwViewMatrix": nv.offset("dwViewMatrix"),
    "m_lifeState": nv.get("C_BaseEntity", "m_lifeState"),
    "m_pGameSceneNode": nv.get("C_BaseEntity", "m_pGameSceneNode"),
    "m_modelState": nv.get("CSkeletonInstance", "m_modelState"),
    "m_hPlayerPawn": nv.get("CCSPlayerController", "m_hPlayerPawn"),
    "m_iszPlayerName": nv.get("CBasePlayerController", "m_iszPlayerName"),
}
