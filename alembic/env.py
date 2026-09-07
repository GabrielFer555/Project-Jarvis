import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from memory.db import get_database_url  # noqa: E402
from memory.models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url_string() -> str:
    url = get_database_url()
    if hasattr(url, "render_as_string"):
        return url.render_as_string(hide_password=False)
    return str(url)


def run_migrations_offline() -> None:
    context.configure(
        url=_url_string(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    connectable = create_engine(_url_string())
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
