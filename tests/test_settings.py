import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent.settings import load_settings

_POSTGRES = {
    "POSTGRES_USER": "jarvis",
    "POSTGRES_PASSWORD": "jarvis",
    "POSTGRES_DB": "jarvis",
}


class SettingsTests(unittest.TestCase):
    def test_missing_token_raises(self) -> None:
        env = {**_POSTGRES, "GROQ_API_KEY": "", "GROQ_MODEL": "openai/gpt-oss-20b"}
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                load_settings()
        self.assertIn("GROQ_API_KEY", str(ctx.exception))

    def test_missing_model_raises(self) -> None:
        env = {**_POSTGRES, "GROQ_API_KEY": "gsk_test", "GROQ_MODEL": ""}
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                load_settings()
        self.assertIn("GROQ_MODEL", str(ctx.exception))

    def test_loads_token_and_model(self) -> None:
        env = {**_POSTGRES, "GROQ_API_KEY": "gsk_test", "GROQ_MODEL": "openai/gpt-oss-20b"}
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(settings.token, "gsk_test")
        self.assertEqual(settings.model, "openai/gpt-oss-20b")
        self.assertEqual(settings.postgres_user, "jarvis")
        self.assertEqual(settings.postgres_password, "jarvis")
        self.assertEqual(settings.postgres_db, "jarvis")
        self.assertEqual(settings.postgres_host, "127.0.0.1")
        self.assertEqual(settings.postgres_port, 5432)
        self.assertEqual(settings.session_idle_minutes, 10)
        self.assertEqual(settings.api_port, 8080)
        self.assertIsNone(settings.database_url)

    def test_missing_postgres_credentials_raise(self) -> None:
        for name in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
            with self.subTest(name=name):
                env = {
                    **_POSTGRES,
                    "GROQ_API_KEY": "gsk_test",
                    "GROQ_MODEL": "openai/gpt-oss-20b",
                    name: "",
                }
                with patch("agent.settings.load_dotenv"), patch.dict(
                    os.environ, env, clear=True
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        load_settings()
                self.assertIn(name, str(ctx.exception))

    def test_invalid_postgres_port_and_idle_minutes_raise(self) -> None:
        cases = (
            ("POSTGRES_PORT", "abc"),
            ("POSTGRES_PORT", "0"),
            ("POSTGRES_PORT", "-1"),
            ("SESSION_IDLE_MINUTES", "abc"),
            ("SESSION_IDLE_MINUTES", "0"),
            ("SESSION_IDLE_MINUTES", "-1"),
        )
        for name, value in cases:
            with self.subTest(name=name, value=value):
                env = {
                    **_POSTGRES,
                    "GROQ_API_KEY": "gsk_test",
                    "GROQ_MODEL": "openai/gpt-oss-20b",
                    name: value,
                }
                with patch("agent.settings.load_dotenv"), patch.dict(
                    os.environ, env, clear=True
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        load_settings()
                message = str(ctx.exception)
                self.assertIn(name, message)
                self.assertIn(value, message)

    def test_api_port_defaults_to_8080_when_absent(self) -> None:
        env = {
            **_POSTGRES,
            "GROQ_API_KEY": "gsk_test",
            "GROQ_MODEL": "openai/gpt-oss-20b",
        }
        with patch("agent.settings.load_dotenv"), patch.dict(
            os.environ, env, clear=True
        ):
            settings = load_settings()
        self.assertEqual(settings.api_port, 8080)

    def test_invalid_api_port_raises_with_name_and_value(self) -> None:
        for value in ("abc", "0"):
            with self.subTest(value=value):
                env = {
                    **_POSTGRES,
                    "GROQ_API_KEY": "gsk_test",
                    "GROQ_MODEL": "openai/gpt-oss-20b",
                    "API_PORT": value,
                }
                with patch("agent.settings.load_dotenv"), patch.dict(
                    os.environ, env, clear=True
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        load_settings()
                message = str(ctx.exception)
                self.assertIn("API_PORT", message)
                self.assertIn(value, message)

    def test_database_url_does_not_waive_postgres_credentials(self) -> None:
        env = {
            "GROQ_API_KEY": "gsk_test",
            "GROQ_MODEL": "openai/gpt-oss-20b",
            "POSTGRES_USER": "jarvis",
            "POSTGRES_PASSWORD": "",
            "POSTGRES_DB": "jarvis",
            "DATABASE_URL": "postgresql+psycopg://other:secret@external:5433/otherdb",
        }
        with patch("agent.settings.load_dotenv"), patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                load_settings()
        self.assertIn("POSTGRES_PASSWORD", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
