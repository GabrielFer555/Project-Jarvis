import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main
from agent.text_chat import run_text_chat


class TextChatTests(unittest.TestCase):
    def setUp(self) -> None:
        chatgroq = patch("agent.brain.ChatGroq")
        self.mock_chatgroq = chatgroq.start()
        self.addCleanup(chatgroq.stop)

        init_brain = patch("agent.text_chat.init_brain")
        self.mock_init_brain = init_brain.start()
        self.addCleanup(init_brain.stop)

        generate_reply = patch("agent.text_chat.generate_reply")
        self.mock_generate_reply = generate_reply.start()
        self.addCleanup(generate_reply.stop)

    def test_empty_line_does_not_call_llm(self) -> None:
        with patch("builtins.input", side_effect=["", "   ", "sair"]):
            run_text_chat()
        self.mock_init_brain.assert_called_once()
        self.mock_generate_reply.assert_not_called()
        self.mock_chatgroq.assert_not_called()

    def test_exit_commands_end_loop_without_llm(self) -> None:
        for command in ("sair", "quit", "exit"):
            with self.subTest(command=command):
                self.mock_generate_reply.reset_mock()
                self.mock_init_brain.reset_mock()
                with patch("builtins.input", side_effect=[command]):
                    run_text_chat()
                self.mock_init_brain.assert_called_once()
                self.mock_generate_reply.assert_not_called()

    def test_message_calls_generate_reply_with_text_and_language(self) -> None:
        self.mock_generate_reply.return_value = "resposta"
        with patch("builtins.input", side_effect=["olá jarvis", "sair"]):
            with patch("sys.stdout", new_callable=StringIO) as stdout:
                run_text_chat()
        self.mock_init_brain.assert_called_once()
        self.mock_generate_reply.assert_called_once_with("olá jarvis", language="pt")
        self.assertIn("Jarvis [pt]: resposta", stdout.getvalue())

    def test_llm_failure_prints_and_next_turn_runs(self) -> None:
        self.mock_generate_reply.side_effect = [
            RuntimeError("groq indisponivel"),
            "tudo certo",
        ]
        with patch("builtins.input", side_effect=["primeira", "segunda", "sair"]):
            with patch("sys.stdout", new_callable=StringIO) as stdout:
                run_text_chat()
        self.mock_init_brain.assert_called_once()
        self.assertEqual(self.mock_generate_reply.call_count, 2)
        output = stdout.getvalue()
        self.assertIn("Erro na LLM: groq indisponivel", output)
        self.assertIn("Jarvis [pt]: tudo certo", output)

    def test_init_brain_failure_aborts_before_loop(self) -> None:
        self.mock_init_brain.side_effect = RuntimeError("GROQ_API_KEY ausente")
        mock_input = MagicMock()
        with patch("builtins.input", mock_input):
            with self.assertRaises(RuntimeError) as ctx:
                run_text_chat()
        self.assertEqual(str(ctx.exception), "GROQ_API_KEY ausente")
        mock_input.assert_not_called()
        self.mock_generate_reply.assert_not_called()


class MainRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_voice = MagicMock()
        voice_modules = patch.dict(sys.modules, {"voice": self.mock_voice})
        voice_modules.start()
        self.addCleanup(voice_modules.stop)

        text_chat = patch("main.run_text_chat")
        self.mock_text_chat = text_chat.start()
        self.addCleanup(text_chat.stop)

    def test_main_without_text_dispatches_voice(self) -> None:
        main.main([])
        self.mock_voice.run_listen_repeat.assert_called_once_with()
        self.mock_text_chat.assert_not_called()

    def test_main_text_dispatches_chat_with_pt(self) -> None:
        main.main(["--text"])
        self.mock_text_chat.assert_called_once_with(language="pt")
        self.mock_voice.run_listen_repeat.assert_not_called()

    def test_main_text_lang_en_passes_en(self) -> None:
        main.main(["--text", "--lang", "en"])
        self.mock_text_chat.assert_called_once_with(language="en")
        self.mock_voice.run_listen_repeat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
