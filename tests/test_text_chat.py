import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

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

        get_active_session = patch("agent.text_chat.get_active_session")
        self.mock_get_active_session = get_active_session.start()
        self.mock_get_active_session.return_value = None
        self.addCleanup(get_active_session.stop)

        close_session = patch("agent.text_chat.close_session")
        self.mock_close_session = close_session.start()
        self.addCleanup(close_session.stop)

    def test_empty_line_does_not_call_llm(self) -> None:
        with patch("builtins.input", side_effect=["", "   ", "sair"]):
            run_text_chat()
        self.mock_init_brain.assert_called_once()
        self.mock_generate_reply.assert_not_called()
        self.mock_chatgroq.assert_not_called()

    def test_exit_commands_end_loop_without_llm(self) -> None:
        session_id = uuid4()
        cases = (
            ("sair", session_id),
            ("quit", None),
            ("exit", session_id),
        )
        for command, active in cases:
            with self.subTest(command=command, active=active):
                self.mock_generate_reply.reset_mock()
                self.mock_init_brain.reset_mock()
                self.mock_get_active_session.reset_mock()
                self.mock_close_session.reset_mock()
                self.mock_get_active_session.return_value = active
                with patch("builtins.input", side_effect=[command]):
                    run_text_chat()
                self.mock_init_brain.assert_called_once()
                self.mock_generate_reply.assert_not_called()
                self.mock_get_active_session.assert_called_once()
                if active is not None:
                    self.mock_close_session.assert_called_once_with(active)
                else:
                    self.mock_close_session.assert_not_called()

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
        self.events: list[str] = []

        self.mock_voice = MagicMock()
        self.mock_voice.run_listen_repeat.side_effect = lambda: self.events.append(
            "flow"
        )
        voice_modules = patch.dict(sys.modules, {"voice": self.mock_voice})
        voice_modules.start()
        self.addCleanup(voice_modules.stop)

        text_chat = patch("main.run_text_chat")
        self.mock_text_chat = text_chat.start()
        self.mock_text_chat.side_effect = lambda **_kwargs: self.events.append("flow")
        self.addCleanup(text_chat.stop)

        load_settings = patch(
            "main.load_settings",
            side_effect=lambda: self.events.append("load_settings"),
        )
        self.mock_load_settings = load_settings.start()
        self.addCleanup(load_settings.stop)

        start_api = patch(
            "main.start_api",
            side_effect=lambda: self.events.append("start_api"),
        )
        self.mock_start_api = start_api.start()
        self.addCleanup(start_api.stop)

    def test_main_without_text_dispatches_voice(self) -> None:
        main.main([])
        self.assertEqual(self.events, ["load_settings", "start_api", "flow"])
        self.mock_load_settings.assert_called_once_with()
        self.mock_start_api.assert_called_once_with()
        self.mock_voice.run_listen_repeat.assert_called_once_with()
        self.mock_text_chat.assert_not_called()

    def test_main_text_dispatches_chat_with_pt(self) -> None:
        main.main(["--text"])
        self.assertEqual(self.events, ["load_settings", "start_api", "flow"])
        self.mock_load_settings.assert_called_once_with()
        self.mock_start_api.assert_called_once_with()
        self.mock_text_chat.assert_called_once_with(language="pt")
        self.mock_voice.run_listen_repeat.assert_not_called()

    def test_main_text_lang_en_passes_en(self) -> None:
        main.main(["--text", "--lang", "en"])
        self.assertEqual(self.events, ["load_settings", "start_api", "flow"])
        self.mock_load_settings.assert_called_once_with()
        self.mock_start_api.assert_called_once_with()
        self.mock_text_chat.assert_called_once_with(language="en")
        self.mock_voice.run_listen_repeat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
