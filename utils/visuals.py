import struct

from pymem import Pymem

from utils.structs import ScreenSize, Vec3


def world_to_screen(matrix: tuple[float, ...], pos: Vec3, screen: ScreenSize) -> list[float] | None:
    """
    World to screen function.

    Args:
        matrix (tuple[float, ...]): View matrix.
        pos (Vec3): x, y, z position.
        screen (ScreenSize): screen height and width.

    Returns:
        list[float] | None: Screen position [x, y].
    """
    if pos is None:
        return None

    x = matrix[0] * pos.x + matrix[1] * pos.y + matrix[2] * pos.z + matrix[3]
    y = matrix[4] * pos.x + matrix[5] * pos.y + matrix[6] * pos.z + matrix[7]
    w = matrix[12] * pos.x + matrix[13] * pos.y + matrix[14] * pos.z + matrix[15]

    if w < 0.1:
        return None

    inv_w = 1.0 / w

    x = screen.width / 2 + (x * inv_w) * screen.width / 2
    y = screen.height / 2 - (y * inv_w) * screen.height / 2
    return [x, y]


def batch_bone_read(pm: Pymem, bone_matrix: int, bone_indices: dict[str, int]) -> dict[str, tuple[float, float, float]]:
    """
    Batch read multiple bone positions.

    Args:
        pm (Pymem): Pymem instance.
        bone_matrix (int): Bone matrix address.
        bone_indices (dict[str, int]): Dictionary of bone names and their indices.

    Returns:
        dict[str, tuple[float, float, float]]: Dictionary of bone names and their positions.
    """
    min_bone = min(bone_indices.values())
    max_bone = max(bone_indices.values())
    total_bones = max_bone - min_bone + 1
    base_offset = min_bone * 0x20
    total_bytes = total_bones * 0x20

    data = pm.read_bytes(bone_matrix + base_offset, total_bytes)
    bones = {}
    for name, idx in bone_indices.items():
        offset = (idx - min_bone) * 0x20
        x, y, z = struct.unpack("fff", data[offset : offset + 12])
        bones[name] = (x, y, z)
    return bones
