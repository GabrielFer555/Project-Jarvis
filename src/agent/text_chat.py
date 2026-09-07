from memory.conversation import close_session, get_active_session

from .brain import generate_reply, init_brain

_EXIT_COMMANDS = frozenset({"sair", "quit", "exit"})


def run_text_chat(language: str = "pt") -> None:
    init_brain()
    while True:
        try:
            line = input("Você: ")
        except EOFError:
            break

        texto = line.strip()
        if not texto:
            continue
        if texto.casefold() in _EXIT_COMMANDS:
            sid = get_active_session()
            if sid is not None:
                close_session(sid)
            break

        try:
            reply = generate_reply(texto, language=language)
        except Exception as exc:
            print(f"Erro na LLM: {exc}")
            continue

        if reply.reasoning:
            print("Raciocínio:")
            print(reply.reasoning)
        print(f"Jarvis [{language}]: {reply.spoken}")
