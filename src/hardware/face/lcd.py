from .base import FaceState, RobotFace


class RaspberryLcdFace(RobotFace):
    """LCD face on Raspberry Pi. Not implemented yet."""

    def render(self, state: FaceState) -> None:
        # TODO: desenhar o estado no LCD via Raspberry Pi (GPIO / framebuffer / SPI).
        # Sleeping, Listening, Thinking e Answering devem aparecer na tela do robô.
        raise NotImplementedError(
            f"TODO: manipular LCD no Raspberry Pi (estado={state.value})"
        )
