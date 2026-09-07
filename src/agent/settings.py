import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    model: str
    postgres_user: str
    postgres_password: str = field(repr=False)
    postgres_db: str
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    database_url: str | None = None
    session_idle_minutes: int = 10
    api_port: int = 8080


def _require(name: str, hint: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"{name} ausente. Copie .env.example para .env e preencha {hint}."
        )
    return value


def _positive_int(name: str, raw: str | None, default: int) -> int:
    value = (raw or "").strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        raise RuntimeError(f"{name} inválida: recebido {value!r}.") from None
    if parsed <= 0:
        raise RuntimeError(f"{name} inválida: recebido {value!r}.")
    return parsed


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    token = (os.getenv("GROQ_API_KEY") or "").strip()
    model = (os.getenv("GROQ_MODEL") or "").strip()
    if not token:
        raise RuntimeError(
            "GROQ_API_KEY ausente. Copie .env.example para .env e preencha a chave."
        )
    if not model:
        raise RuntimeError(
            "GROQ_MODEL ausente. Copie .env.example para .env e preencha o modelo."
        )
    postgres_user = _require("POSTGRES_USER", "o usuário")
    postgres_password = _require("POSTGRES_PASSWORD", "a senha")
    postgres_db = _require("POSTGRES_DB", "o banco")
    postgres_host = (os.getenv("POSTGRES_HOST") or "").strip() or "127.0.0.1"
    postgres_port = _positive_int("POSTGRES_PORT", os.getenv("POSTGRES_PORT"), 5432)
    database_url = (os.getenv("DATABASE_URL") or "").strip() or None
    session_idle_minutes = _positive_int(
        "SESSION_IDLE_MINUTES", os.getenv("SESSION_IDLE_MINUTES"), 10
    )
    api_port = _positive_int("API_PORT", os.getenv("API_PORT"), 8080)
    os.environ.setdefault("GROQ_API_KEY", token)
    return Settings(
        token=token,
        model=model,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_db=postgres_db,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        database_url=database_url,
        session_idle_minutes=session_idle_minutes,
        api_port=api_port,
    )
