from .base import FaceState, RobotFace

_ASCII = {
    FaceState.SLEEPING: "[-_-] sleeping",
    FaceState.LISTENING: "[o_o] listening",
    FaceState.THINKING: "[o_O] thinking",
    FaceState.ANSWERING: "[^_^] answering",
}


class TerminalFace(RobotFace):
    """Mock face for the Windows terminal."""

    def render(self, state: FaceState) -> None:
        print(f"rosto {_ASCII[state]}", flush=True)
