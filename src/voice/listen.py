import re

from agent.brain import generate_reply, init_brain
from hardware.face import create_face

from .mic import MicSession, beep
from .stt import load_stt, transcribe
from .tts import speak
from .voices import ensure_voice

WAKE_PATTERN = re.compile(r"\bj[aáà]r?vis?\b", re.IGNORECASE)
WAKE_SILENCE_S = 0.4
COMMAND_SILENCE_S = 1.6


def split_wake_word(text: str) -> tuple[bool, str]:
    """Return (heard_wake_word, original command after it)."""
    match = WAKE_PATTERN.search(text)
    if not match:
        return False, ""
    command = re.sub(r"^[\s,.:;!?-]+", "", text[match.end() :]).strip()
    return True, command


def run_listen_repeat() -> None:
    ensure_voice("en")
    ensure_voice("pt")
    load_stt()
    init_brain()
    face = create_face()
    face.sleep()

    print("Jarvis pronto. Diga 'Jarvis' e depois a pergunta.")
    print("Ctrl+C para sair.")

    with MicSession() as mic:
        while True:
            print("\nAguardando 'Jarvis'...")
            audio = mic.record_utterance(silence_seconds=WAKE_SILENCE_S)
            text, language = transcribe(audio)
            if not text:
                continue

            print(f"Ouvi [{language}]: {text}")
            heard, command = split_wake_word(text)
            if not heard:
                continue

            face.listen()

            if not command:
                print("Pode falar.")
                beep()
                follow_up = mic.record_utterance(
                    silence_seconds=COMMAND_SILENCE_S,
                    start_timeout=6.0,
                    ignore_ms=250,
                )
                if follow_up.size == 0:
                    print("Nada depois da wake word.")
                    face.sleep()
                    continue
                command, language = transcribe(follow_up)
                command = command.strip()
                if command:
                    print(f"Ouvi [{language}]: {command}")

            if not command:
                face.sleep()
                continue

            face.think()
            try:
                reply = generate_reply(command, language=language)
            except Exception as exc:
                print(f"Erro na LLM: {exc}")
                face.sleep()
                mic.clear()
                continue

            print(f"Jarvis [{language}]: {reply.spoken}")
            if reply.spoken:
                face.answer()
                speak(reply.spoken, language=language)
            face.sleep()
            mic.clear()
