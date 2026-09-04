from abc import ABC, abstractmethod
from enum import Enum


class FaceState(Enum):
    SLEEPING = "sleeping"
    LISTENING = "listening"
    THINKING = "thinking"
    ANSWERING = "answering"


class RobotFace(ABC):
    """Face of the robot: Sleeping → Listening → Thinking → Answering → Sleeping."""

    def __init__(self) -> None:
        self._state = FaceState.SLEEPING

    @property
    def state(self) -> FaceState:
        return self._state

    def sleep(self) -> None:
        self._set(FaceState.SLEEPING)

    def listen(self) -> None:
        self._set(FaceState.LISTENING)

    def think(self) -> None:
        self._set(FaceState.THINKING)

    def answer(self) -> None:
        self._set(FaceState.ANSWERING)

    def _set(self, state: FaceState) -> None:
        self._state = state
        self.render(state)

    @abstractmethod
    def render(self, state: FaceState) -> None:
        """Draw the current face state on the concrete backend."""
