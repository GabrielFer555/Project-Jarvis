import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import MagicMock, patch
from urllib.parse import quote
from uuid import uuid4

from sqlalchemy import URL
from sqlalchemy.engine import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent.settings import Settings
from memory import db
from memory.conversation import (
    HISTORY_MAX_CHARS,
    HISTORY_MAX_MESSAGES,
    append_message,
    build_window,
)
from memory.db import get_database_url, ping
from memory.models import Message, Reasoning


def _settings(**overrides) -> Settings:
    values = dict(
        token="gsk_test",
        model="openai/gpt-oss-20b",
        postgres_user="jarvis",
        postgres_password="jarvis",
        postgres_db="jarvis",
        postgres_host="localhost",
        postgres_port=5432,
        database_url=None,
        session_idle_minutes=10,
    )
    values.update(overrides)
    return Settings(**values)


class BuildWindowTests(unittest.TestCase):
    def test_build_window_respects_message_cap(self) -> None:
        rows = [("user", f"m{i:02d}") for i in range(HISTORY_MAX_MESSAGES + 2)]
        window = build_window(rows)
        self.assertEqual(len(window), HISTORY_MAX_MESSAGES)
        self.assertEqual(window[0], ("user", "m02"))
        self.assertEqual(window[-1], ("user", f"m{HISTORY_MAX_MESSAGES + 1:02d}"))

    def test_build_window_respects_char_cap(self) -> None:
        chunk = "x" * 3000
        rows = [("user", chunk), ("user", chunk), ("user", chunk)]
        window = build_window(rows)
        self.assertEqual(window, [("user", chunk), ("user", chunk)])
        self.assertLessEqual(sum(len(content) for _, content in window), HISTORY_MAX_CHARS)

    def test_build_window_aligns_start_to_user(self) -> None:
        rows = [
            ("assistant", "órfã"),
            ("user", "oi"),
            ("assistant", "olá"),
        ]
        window = build_window(rows)
        self.assertEqual(window, [("user", "oi"), ("assistant", "olá")])
        self.assertEqual(window[0][0], "user")

    def test_build_window_aligns_after_char_cap(self) -> None:
        rows = [
            ("user", "a" * 100),
            ("assistant", "b" * 50),
            ("user", "c" * 100),
        ]
        window = build_window(rows, max_messages=10, max_chars=160)
        self.assertEqual(window, [("user", "c" * 100)])
        self.assertEqual(window[0][0], "user")


class AppendMessageTests(unittest.TestCase):
    def test_user_role_rejects_reasoning(self) -> None:
        session_factory = MagicMock()
        with patch(
            "memory.conversation.get_sessionmaker", return_value=session_factory
        ):
            with self.assertRaises(RuntimeError):
                append_message(uuid4(), "user", "oi", reasoning="nao deveria")
        session_factory.assert_not_called()

    def _mocked_session(self):
        session = MagicMock()
        session.scalar.return_value = 1
        added: list[object] = []
        ops: list[str] = []

        def add(obj: object) -> None:
            added.append(obj)
            ops.append("add")

        def flush() -> None:
            for obj in added:
                if isinstance(obj, Message) and obj.id is None:
                    obj.id = uuid4()
            ops.append("flush")

        def commit() -> None:
            ops.append("commit")

        session.add.side_effect = add
        session.flush.side_effect = flush
        session.commit.side_effect = commit
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        return session, session_factory, added, ops

    def test_assistant_reasoning_inserted_1_to_1_same_commit(self) -> None:
        session, session_factory, added, ops = self._mocked_session()
        with patch(
            "memory.conversation.get_sessionmaker", return_value=session_factory
        ):
            append_message(uuid4(), "assistant", "falado", reasoning="penso")

        messages = [obj for obj in added if isinstance(obj, Message)]
        reasonings = [obj for obj in added if isinstance(obj, Reasoning)]
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(reasonings), 1)
        self.assertEqual(messages[0].content, "falado")
        self.assertEqual(reasonings[0].content, "penso")
        self.assertIsNotNone(messages[0].id)
        self.assertEqual(reasonings[0].message_id, messages[0].id)
        self.assertEqual(ops, ["add", "flush", "add", "commit"])
        session.commit.assert_called_once_with()

    def test_none_reasoning_does_not_add_reasoning(self) -> None:
        session, session_factory, added, ops = self._mocked_session()
        with patch(
            "memory.conversation.get_sessionmaker", return_value=session_factory
        ):
            append_message(uuid4(), "assistant", "falado", reasoning=None)

        messages = [obj for obj in added if isinstance(obj, Message)]
        reasonings = [obj for obj in added if isinstance(obj, Reasoning)]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "falado")
        self.assertEqual(reasonings, [])
        self.assertEqual(ops, ["add", "commit"])
        session.flush.assert_not_called()
        session.commit.assert_called_once_with()


class DatabaseUrlTests(unittest.TestCase):
    def test_database_url_takes_precedence(self) -> None:
        external = "postgresql+psycopg://other:secret@external:5433/otherdb"
        settings = _settings(database_url=external)
        with patch("memory.db.load_settings", return_value=settings):
            url = get_database_url()
        self.assertEqual(url, external)

    def test_password_special_chars_are_escaped(self) -> None:
        password = "p@ss:w/ord"
        settings = _settings(postgres_password=password)
        with patch("memory.db.load_settings", return_value=settings):
            url = get_database_url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.password, password)
        self.assertEqual(url.host, "localhost")
        self.assertEqual(url.database, "jarvis")
        rendered = url.render_as_string(hide_password=False)
        self.assertNotIn(password, rendered)
        self.assertIn(quote(password, safe=""), rendered)
        parsed = make_url(rendered)
        self.assertEqual(parsed.password, password)
        self.assertEqual(parsed.host, "localhost")
        self.assertEqual(parsed.database, "jarvis")


class PingTests(unittest.TestCase):
    def test_ping_executes_only_select_one_without_schema_check(self) -> None:
        connection = MagicMock()
        engine = MagicMock()
        engine.connect.return_value.__enter__.return_value = connection

        with patch("memory.db.get_engine", return_value=engine):
            with patch("memory.db.assert_schema_up_to_date") as schema_check:
                ping()

        engine.connect.assert_called_once_with()
        connection.execute.assert_called_once()
        statement = connection.execute.call_args.args[0]
        self.assertEqual(str(statement), "SELECT 1")
        schema_check.assert_not_called()


class EngineInitializationTests(unittest.TestCase):
    def test_concurrent_initialization_creates_engine_once(self) -> None:
        worker_count = 8
        barrier = Barrier(worker_count)
        engine = MagicMock()

        def get_engine_concurrently():
            barrier.wait()
            return db.get_engine()

        with patch.object(db, "_engine", None):
            with patch.object(db, "get_database_url", return_value="postgresql://test"):
                with patch.object(db, "create_engine", return_value=engine) as create:
                    with ThreadPoolExecutor(max_workers=worker_count) as executor:
                        results = list(
                            executor.map(
                                lambda _index: get_engine_concurrently(),
                                range(worker_count),
                            )
                        )

        self.assertTrue(all(result is engine for result in results))
        create.assert_called_once_with(
            "postgresql://test",
            connect_args={"connect_timeout": db._CONNECT_TIMEOUT_SECONDS},
        )


class AlembicBootstrapTests(unittest.TestCase):
    def test_importing_db_first_does_not_cycle_through_brain(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        src = repo / "src"
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(src)!r})\n"
            "from memory.db import get_database_url, get_sessionmaker\n"
            "assert callable(get_database_url)\n"
            "assert callable(get_sessionmaker)\n"
            "assert 'agent.brain' not in sys.modules\n"
            "assert 'memory.conversation' not in sys.modules\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
