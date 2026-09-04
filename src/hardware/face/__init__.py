from .base import FaceState, RobotFace
from .lcd import RaspberryLcdFace
from .terminal import TerminalFace


def create_face() -> RobotFace:
    """Return the terminal mock. Swap to RaspberryLcdFace on the Pi when LCD exists."""
    return TerminalFace()


__all__ = [
    "FaceState",
    "RaspberryLcdFace",
    "RobotFace",
    "TerminalFace",
    "create_face",
]
