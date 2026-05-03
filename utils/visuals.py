import struct

from pymem import Pymem


def w2s(mtx: tuple[float, ...], posx: float, posy: float, posz: float, width: int, height: int) -> list[float]:
    """
    World to screen function.

    Args:
        mtx (tuple[float, ...]): View matrix.
        posx (float): x position.
        posy (float): y position.
        posz (float): z position.
        width (int): Screen width.
        height (int): Screen height.

    Returns:
        list[float]: Screen position [x, y].
    """
    screenW = (mtx[12] * posx) + (mtx[13] * posy) + (mtx[14] * posz) + mtx[15]

    if screenW > 0.001:
        screenX = (mtx[0] * posx) + (mtx[1] * posy) + (mtx[2] * posz) + mtx[3]
        screenY = (mtx[4] * posx) + (mtx[5] * posy) + (mtx[6] * posz) + mtx[7]

        camX = width / 2
        camY = height / 2

        x = camX + int(camX * screenX / screenW)
        y = camY - int(camY * screenY / screenW)

        return [x, y]

    return [-999, -999]


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
