
from agent.brain import ping_groq
from memory.db import ping


def health() -> tuple[int, dict[str, str]]:
    """Resume a disponibilidade das dependências sem expor suas exceções."""
    postgres = "up"
    groq = "up"

    try:
        ping()
    except Exception:
        postgres = "down"

    try:
        ping_groq()
    except Exception:
        groq = "down"

    if postgres == "up" and groq == "up":
        return 200, {"status": "ok", "postgres": postgres, "groq": groq}
    return 503, {
        "status": "unavailable",
        "postgres": postgres,
        "groq": groq,
    }
