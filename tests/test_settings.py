import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent.settings import load_settings


class SettingsTests(unittest.TestCase):
    def test_missing_token_raises(self) -> None:
        env = {"GROQ_API_KEY": "", "GROQ_MODEL": "openai/gpt-oss-20b"}
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                load_settings()
        self.assertIn("GROQ_API_KEY", str(ctx.exception))

    def test_missing_model_raises(self) -> None:
        env = {"GROQ_API_KEY": "gsk_test", "GROQ_MODEL": ""}
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                load_settings()
        self.assertIn("GROQ_MODEL", str(ctx.exception))

    def test_loads_token_and_model(self) -> None:
        env = {"GROQ_API_KEY": "gsk_test", "GROQ_MODEL": "openai/gpt-oss-20b"}
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(settings.token, "gsk_test")
        self.assertEqual(settings.model, "openai/gpt-oss-20b")


if __name__ == "__main__":
    unittest.main()
