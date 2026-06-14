"""负鼠振动控制器 Python 库"""

from .controller import PossumController
from .constants import (
    DEFAULT_DEVICE_NAME,
    INTENSITY_MIN, INTENSITY_MAX, WAVEFORM_MAX,
)

__all__ = [
    "PossumController",
    "DEFAULT_DEVICE_NAME",
    "INTENSITY_MIN", "INTENSITY_MAX", "WAVEFORM_MAX",
]