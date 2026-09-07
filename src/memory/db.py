from pathlib import Path
from threading import Lock

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import URL, Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from agent.settings import load_settings

ROOT = Path(__file__).resolve().parents[2]

_engine: Engine | None = None
_engine_lock = Lock()
_sessionmaker: sessionmaker[Session] | None = None
_CONNECT_TIMEOUT_SECONDS = 5


def get_database_url() -> URL | str:
    settings = load_settings()
    return settings.database_url or URL.create(
        "postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = create_engine(
                    get_database_url(),
                    connect_args={"connect_timeout": _CONNECT_TIMEOUT_SECONDS},
                )
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = sessionmaker(bind=get_engine())
    return _sessionmaker


def ping() -> None:
    """Confirma que a engine alcança o Postgres. Não confere revisão Alembic."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise RuntimeError(f"Postgres inacessível: {exc}") from exc


def assert_schema_up_to_date() -> None:
    alembic_cfg = Config(str(ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(ROOT / "alembic"))
    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()
    try:
        with get_engine().connect() as connection:
            context = MigrationContext.configure(connection)
            current = context.get_current_revision()
    except OperationalError as exc:
        raise RuntimeError(f"Postgres inacessível: {exc}") from exc
    if current != head:
        raise RuntimeError(
            "Esquema do banco desatualizado. Rode: alembic upgrade head"
        )
