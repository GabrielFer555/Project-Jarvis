import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voice.listen import FollowUpAction, classify_follow_up, split_wake_word


class SplitWakeWordTests(unittest.TestCase):
    def test_no_wake_word(self) -> None:
        self.assertEqual(split_wake_word("está frio hoje"), (False, ""))

    def test_wake_word_only(self) -> None:
        self.assertEqual(split_wake_word("Jarvis"), (True, ""))

    def test_wake_word_with_command(self) -> None:
        self.assertEqual(
            split_wake_word("Jarvis qual é a hora"),
            (True, "qual é a hora"),
        )

    def test_wake_word_strips_leading_punctuation(self) -> None:
        self.assertEqual(
            split_wake_word("Jarvis, liga a luz"),
            (True, "liga a luz"),
        )


class ClassifyFollowUpTests(unittest.TestCase):
    def test_empty_or_whitespace_waits_wake(self) -> None:
        for text in ("", "   ", "\n"):
            with self.subTest(text=repr(text)):
                self.assertEqual(
                    classify_follow_up(text),
                    (FollowUpAction.WAIT_WAKE, ""),
                )

    def test_wake_word_only_awaits_command(self) -> None:
        self.assertEqual(
            classify_follow_up("Jarvis"),
            (FollowUpAction.AWAIT_COMMAND, ""),
        )
        self.assertEqual(
            classify_follow_up("  Jarvis  "),
            (FollowUpAction.AWAIT_COMMAND, ""),
        )

    def test_wake_word_with_command_continues(self) -> None:
        self.assertEqual(
            classify_follow_up("Jarvis qual é a hora"),
            (FollowUpAction.CONTINUE, "qual é a hora"),
        )

    def test_text_without_wake_word_continues(self) -> None:
        self.assertEqual(
            classify_follow_up("está frio hoje"),
            (FollowUpAction.CONTINUE, "está frio hoje"),
        )


if __name__ == "__main__":
    unittest.main()
