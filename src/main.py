import argparse

from agent.settings import load_settings
from agent.text_chat import run_text_chat
from api import start_api


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", action="store_true")
    parser.add_argument("--lang", choices=("pt", "en"), default="en")
    args = parser.parse_args(argv)

    load_settings()
    start_api()

    if args.text:
        run_text_chat(language=args.lang)
        return

    from voice import run_listen_repeat

    run_listen_repeat()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")
