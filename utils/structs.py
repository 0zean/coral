from ctypes import POINTER, Structure, Union, c_float, c_long, c_uint64, c_ulong


class Vec3(Structure):
    _fields_ = [("x", c_float), ("y", c_float), ("z", c_float)]


class Vec2(Structure):
    _fields_ = [("x", c_float), ("y", c_float)]


class C_UTL_VECTOR(Structure):
    _fields_ = [("Count", c_uint64), ("Data", c_uint64)]


class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", POINTER(c_ulong)),
    ]


class INPUT(Structure):
    class INPUT_UNION(Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("u",)
    _fields_ = [("type", c_ulong), ("u", INPUT_UNION)]
