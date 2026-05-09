from dataclasses import dataclass, field

import win32api
from raylibpy import Color

TRIGGER_KEYS: tuple[str, ...] = (
    "shift", "x", "x2", "alt", "ctrl",
    "insert", "home", "page up", "delete", "end", "page down",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "up", "left", "down", "right",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "y", "z",
    "-", "=", "backspace", "tab", "[", "]", "caps lock",
    ";", "'", "enter", ",", ".", "/",
    "num lock", "*", "+", "scroll lock", "pause", "`",
)

CS2_WINDOW_TITLE: str = "Counter-Strike 2"


@dataclass(frozen=True)
class TimingConfig:
    sleep_tick: float = 0.005
    sleep_inactive: float = 0.1
    sleep_pressed: float = 0.03
    sleep_released: float = 0.1
    click_pre_delay: tuple[float, float] = (0.01, 0.03)
    click_post_delay: tuple[float, float] = (0.01, 0.05)
    reader_tick: float = 1.0 / 60


@dataclass(frozen=True)
class MouseConfig:
    smoothing_min: float = 1.0
    smoothing_max: float = 3.0
    mouseeventf_move: int = 0x0001


@dataclass(frozen=True)
class Win32Config:
    gwl_exstyle: int = -20
    ws_ex_transparent: int = 0x00000020
    ws_ex_toolwindow: int = 0x00000080


@dataclass(frozen=True)
class RenderConfig:
    hp_high: Color = field(default_factory=lambda: Color(0, 200, 0, 255))
    hp_med: Color = field(default_factory=lambda: Color(255, 140, 0, 255))
    hp_low: Color = field(default_factory=lambda: Color(255, 0, 0, 255))
    name_color: Color = field(default_factory=lambda: Color(255, 255, 0, 255))
    entity_color: Color = field(default_factory=lambda: Color(0, 180, 255, 255))
    transparent: Color = field(default_factory=lambda: Color(0, 0, 0, 0))
    name_sz: int = 16
    hp_text_sz: int = 12


@dataclass(frozen=True)
class SkeletonConfig:
    bone_indices: dict[str, int] = field(
        default_factory=lambda: {
            "waist": 1,
            "spine_2": 4,
            "spine_1": 3,
            "neck": 6,
            "head": 7,
            "shoulder_right": 13,
            "arm_right": 14,
            "hand_left": 11,
            "shoulder_left": 9,
            "arm_left": 10,
            "hand_right": 15,
            "leg_left": 17,
            "knee_left": 18,
            "ankle_left": 19,
            "leg_right": 20,
            "knee_right": 21,
            "ankle_right": 22,
            "leg": 22,
        }
    )


@dataclass
class ScreenConfig:
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self) -> None:
        self.width = win32api.GetSystemMetrics(0)
        self.height = win32api.GetSystemMetrics(1)


@dataclass(frozen=True)
class AppConfig:
    timing: TimingConfig = field(default_factory=TimingConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    win32: Win32Config = field(default_factory=Win32Config)
    render: RenderConfig = field(default_factory=RenderConfig)
    skeleton: SkeletonConfig = field(default_factory=SkeletonConfig)
    screen: ScreenConfig = field(default_factory=ScreenConfig)


config = AppConfig()
