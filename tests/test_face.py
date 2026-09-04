import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hardware.face import FaceState, RaspberryLcdFace, TerminalFace, create_face


class TerminalFaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.face = TerminalFace()

    def test_starts_sleeping(self) -> None:
        self.assertEqual(self.face.state, FaceState.SLEEPING)

    def test_full_cycle(self) -> None:
        with patch("sys.stdout", new_callable=StringIO):
            self.face.listen()
            self.assertEqual(self.face.state, FaceState.LISTENING)
            self.face.think()
            self.assertEqual(self.face.state, FaceState.THINKING)
            self.face.answer()
            self.assertEqual(self.face.state, FaceState.ANSWERING)
            self.face.sleep()
            self.assertEqual(self.face.state, FaceState.SLEEPING)

    def test_create_face_is_terminal(self) -> None:
        self.assertIsInstance(create_face(), TerminalFace)


class RaspberryLcdFaceTests(unittest.TestCase):
    def test_render_is_not_implemented(self) -> None:
        face = RaspberryLcdFace()
        with self.assertRaises(NotImplementedError) as ctx:
            face.listen()
        self.assertIn("TODO", str(ctx.exception))
        self.assertIn("listening", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
