import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    token: str
    model: str


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
    os.environ.setdefault("GROQ_API_KEY", token)
    return Settings(token=token, model=model)
