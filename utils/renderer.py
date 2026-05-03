import array

import glfw
import moderngl

from utils.structs import EntitySnapshot

# GLSL shaders
_VERT = """
#version 330 core
in vec2 in_pos;
in vec4 in_color;
out vec4 v_color;
uniform vec2 u_resolution;

void main() {
    // Map pixel coords → NDC
    vec2 ndc = (in_pos / u_resolution) * 2.0 - 1.0;
    ndc.y = -ndc.y;
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_color = in_color;
}
"""

_FRAG = """
#version 330 core
in vec4 v_color;
out vec4 out_color;
void main() { out_color = v_color; }
"""

# Color helper
RGBA = tuple[float, float, float, float]


def _hp_color(hp: int) -> RGBA:
    if hp >= 70:
        return (0.0, 0.78, 0.0, 1.0)
    if hp > 30:
        return (1.0, 0.55, 0.0, 1.0)
    return (1.0, 0.0, 0.0, 1.0)


# Geometry helpers (write directly into a pre-allocated float buffer)
def _push_line(
    buf: array.array,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    r: float,
    g: float,
    b: float,
    a: float,
) -> None:
    buf.extend((x0, y0, r, g, b, a, x1, y1, r, g, b, a))


def _push_rect(
    buf: array.array,
    lx: float,
    ty: float,
    rx: float,
    by: float,
    r: float,
    g: float,
    b: float,
    a: float,
) -> None:
    """Four edges of a rectangle as 8 line-segment endpoints."""
    _push_line(buf, lx, ty, rx, ty, r, g, b, a)  # top
    _push_line(buf, rx, ty, rx, by, r, g, b, a)  # right
    _push_line(buf, rx, by, lx, by, r, g, b, a)  # bottom
    _push_line(buf, lx, by, lx, ty, r, g, b, a)  # left


def w2s(mtx: tuple[float, ...], px: float, py: float, pz: float, width: int, height: int) -> tuple[float, float] | None:
    w = mtx[12] * px + mtx[13] * py + mtx[14] * pz + mtx[15]
    if w <= 0.001:
        return None
    sx = mtx[0] * px + mtx[1] * py + mtx[2] * pz + mtx[3]
    sy = mtx[4] * px + mtx[5] * py + mtx[6] * pz + mtx[7]
    cx, cy = width / 2.0, height / 2.0
    return cx + cx * sx / w, cy - cy * sy / w


_BONE_CONNECTIONS: tuple[tuple[str, str], ...] = (
    ("neck", "shoulder_right"),
    ("neck", "shoulder_left"),
    ("shoulder_left", "arm_left"),
    ("shoulder_right", "arm_right"),
    ("arm_right", "hand_right"),
    ("arm_left", "hand_left"),
    ("neck", "waist"),
    ("waist", "knee_right"),
    ("waist", "knee_left"),
    ("knee_left", "ankle_left"),
    ("knee_right", "ankle_right"),
)


class ESPOverlay:
    """Transparent overlay rendered with ModernGL."""

    _INITIAL_VERTEX_CAPACITY = 8_192  # floats; grows automatically

    def __init__(self, width: int, height: int) -> None:
        self._w = width
        self._h = height
        self._buf: array.array = array.array("f")

        # GLFW
        if not glfw.init():
            raise RuntimeError("GLFW init failed")

        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, 4)  # 4x MSAA

        self._win = glfw.create_window(width, height, "ESP Overlay", None, None)
        if not self._win:
            glfw.terminate()
            raise RuntimeError("GLFW window creation failed")

        glfw.make_context_current(self._win)
        glfw.swap_interval(0)

        # make window click-through and layered
        self._setup_win32_layered()

        # ModernGL
        self._ctx = moderngl.create_context()
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        self._prog = self._ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG)
        self._prog["u_resolution"].value = (float(width), float(height))  # type: ignore

        # dynamic VBO
        self._vbo = self._ctx.buffer(reserve=self._INITIAL_VERTEX_CAPACITY * 4)
        self._vao = self._ctx.vertex_array(
            self._prog,
            [(self._vbo, "2f 4f", "in_pos", "in_color")],
        )

    # Win32 helpers
    def _setup_win32_layered(self) -> None:
        import ctypes

        hwnd = glfw.get_win32_window(self._win)
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        # LWA_COLORKEY: treat pure black as transparent
        user32.SetLayeredWindowAttributes(hwnd, 0x000000, 0, 0x1)

    # Frame API
    @property
    def alive(self) -> bool:
        return not glfw.window_should_close(self._win)

    def begin_frame(
        self,
        view_matrix: tuple[float, ...],
        entities: list[EntitySnapshot],
    ) -> None:
        glfw.poll_events()
        self._buf = array.array("f")

        for ent in entities:
            self._draw_entity(view_matrix, ent)

    def end_frame(self) -> None:
        self._ctx.clear(0.0, 0.0, 0.0, 0.0)  # transparent clear

        if self._buf:
            data = self._buf.tobytes()
            # Grow VBO if needed
            if len(data) > self._vbo.size:
                self._vbo.orphan(len(data) * 2)

            self._vbo.write(data)
            vertex_count = len(self._buf) // 6  # 6 floats per vertex
            self._vao.render(moderngl.LINES, vertices=vertex_count)

        glfw.swap_buffers(self._win)

    # entity geometry
    def _draw_entity(
        self,
        mtx: tuple[float, ...],
        ent: EntitySnapshot,
    ) -> None:
        bones = ent.bones
        w, h = self._w, self._h

        def proj(name: str) -> tuple[float, float] | None:
            b = bones.get(name)
            return w2s(mtx, *b, w, h) if b else None

        # Skeleton
        er, eg, eb = 0.0, 0.71, 1.0  # entity colour: #00B4FF
        valid_xs: list[float] = []
        valid_ys: list[float] = []

        for a_name, b_name in _BONE_CONNECTIONS:
            a, b = proj(a_name), proj(b_name)
            if a and b:
                _push_line(self._buf, *a, *b, er, eg, eb, 1.0)
                valid_xs.extend((a[0], b[0]))
                valid_ys.extend((a[1], b[1]))

        head = proj("head")
        if head:
            valid_xs.append(head[0])
            valid_ys.append(head[1])

        if not valid_xs:
            return

        # Bounding box
        min_y = min(valid_ys) - 10.0
        max_y = max(valid_ys) + 5.0
        box_h = max_y - min_y
        box_w = box_h / 2.0
        cx = (min(valid_xs) + max(valid_xs)) / 2.0
        lx = cx - box_w / 2.0
        rx = cx + box_w / 2.0
        _push_rect(self._buf, lx, min_y, rx, max_y, er, eg, eb, 1.0)

        # Head circle
        neck = proj("neck")
        if head and neck:
            import math

            radius = abs(head[1] - neck[1]) * 1.125
            N = 12
            pts = [
                (head[0] + radius * math.cos(2 * math.pi * i / N), head[1] + radius * math.sin(2 * math.pi * i / N))
                for i in range(N)
            ]
            for i in range(N):
                p0, p1 = pts[i], pts[(i + 1) % N]
                _push_line(self._buf, *p0, *p1, er, eg, eb, 1.0)

        # Health bar
        hp = max(0, min(100, ent.health))
        hr, hg, hb, ha = _hp_color(hp)
        bar_top = min_y + (1.0 - hp / 100.0) * box_h
        _push_line(self._buf, lx - 5, bar_top, lx - 5, max_y, hr, hg, hb, ha)

    # Cleanup
    def shutdown(self) -> None:
        self._vao.release()
        self._vbo.release()
        self._prog.release()
        self._ctx.release()
        glfw.destroy_window(self._win)
        glfw.terminate()
