from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select, update

from agent.settings import load_settings
from memory.db import get_sessionmaker
from memory.models import ChatSession, Message, Reasoning

HISTORY_MAX_MESSAGES = 40
HISTORY_MAX_CHARS = 8000


def _inactivity_cutoff():
    minutes = load_settings().session_idle_minutes
    return func.now() - timedelta(minutes=minutes)


def resolve_session(language: str = "") -> UUID:
    cutoff = _inactivity_cutoff()
    with get_sessionmaker()() as db:
        db.execute(
            update(ChatSession)
            .where(
                ChatSession.ended_at.is_(None),
                ChatSession.last_seen_at <= cutoff,
            )
            .values(ended_at=ChatSession.last_seen_at)
        )
        session_id = db.scalar(
            select(ChatSession.id)
            .where(
                ChatSession.ended_at.is_(None),
                ChatSession.last_seen_at > cutoff,
            )
            .order_by(ChatSession.last_seen_at.desc())
            .limit(1)
        )
        if session_id is None:
            chat = ChatSession(language=language or None)
            db.add(chat)
            db.flush()
            session_id = chat.id
        db.commit()
        return session_id


def get_active_session() -> UUID | None:
    cutoff = _inactivity_cutoff()
    with get_sessionmaker()() as db:
        session_id = db.scalar(
            select(ChatSession.id)
            .where(
                ChatSession.ended_at.is_(None),
                ChatSession.last_seen_at > cutoff,
            )
            .order_by(ChatSession.last_seen_at.desc())
            .limit(1)
        )
        db.commit()
        return session_id


def append_message(
    session_id: UUID,
    role: str,
    content: str,
    language: str = "",
    *,
    reasoning: str | None = None,
) -> None:
    if reasoning is not None and role != "assistant":
        raise RuntimeError("Raciocínio só pode ser gravado para mensagem assistant")
    with get_sessionmaker()() as db:
        next_seq = db.scalar(
            select(func.coalesce(func.max(Message.seq), 0) + 1).where(
                Message.session_id == session_id
            )
        )
        message = Message(
            session_id=session_id,
            seq=next_seq,
            role=role,
            content=content,
            language=language or None,
        )
        db.add(message)
        if reasoning is not None:
            db.flush()
            db.add(Reasoning(message_id=message.id, content=reasoning))
        if role == "user":
            db.execute(
                update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(last_seen_at=func.now())
            )
        db.commit()


def load_window(session_id: UUID) -> list[tuple[str, str]]:
    with get_sessionmaker()() as db:
        rows = list(
            db.execute(
                select(Message.role, Message.content)
                .where(Message.session_id == session_id)
                .order_by(Message.seq.desc())
                .limit(HISTORY_MAX_MESSAGES)
            )
        )
        db.commit()
    chronological = [(role, content) for role, content in reversed(rows)]
    return build_window(chronological)


def close_session(session_id: UUID) -> None:
    with get_sessionmaker()() as db:
        db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(ended_at=func.now())
        )
        db.commit()


def build_window(
    rows: list[tuple[str, str]],
    max_messages: int = HISTORY_MAX_MESSAGES,
    max_chars: int = HISTORY_MAX_CHARS,
) -> list[tuple[str, str]]:
    """Recorta (role, content) pelo teto e alinha o início em uma fala do usuário."""
    window = list(rows[-max_messages:])
    while window and sum(len(content) for _, content in window) > max_chars:
        window.pop(0)
    while window and window[0][0] != "user":
        window.pop(0)
    return window
