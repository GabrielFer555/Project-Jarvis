from voice import run_listen_repeat

if __name__ == "__main__":
    try:
        run_listen_repeat()
    except KeyboardInterrupt:
        print("\nEncerrado.")
