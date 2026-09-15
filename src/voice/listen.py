import logging
import re
from enum import Enum

from agent.brain import generate_reply, init_brain
from hardware.face import create_face

from .mic import MicSession, beep
from .stt import load_stt, transcribe
from .tts import speak
from .voices import ensure_voice

logger = logging.getLogger(__name__)

WAKE_PATTERN = re.compile(r"\bj[aáà]r?vis?\b", re.IGNORECASE)
WAKE_SILENCE_S = 0.4
COMMAND_SILENCE_S = 1.6


class FollowUpAction(Enum):
    WAIT_WAKE = "wait_wake"
    AWAIT_COMMAND = "await_command"
    CONTINUE = "continue"


def split_wake_word(text: str) -> tuple[bool, str]:
    """Return (heard_wake_word, original command after it)."""
    match = WAKE_PATTERN.search(text)
    if not match:
        return False, ""
    command = re.sub(r"^[\s,.:;!?-]+", "", text[match.end() :]).strip()
    return True, command


def classify_follow_up(text: str) -> tuple[FollowUpAction, str]:
    """(WAIT_WAKE, '') | (AWAIT_COMMAND, '') | (CONTINUE, comando)."""
    stripped = text.strip()
    if not stripped:
        return FollowUpAction.WAIT_WAKE, ""
    heard, command = split_wake_word(stripped)
    if heard and not command:
        return FollowUpAction.AWAIT_COMMAND, ""
    if heard:
        return FollowUpAction.CONTINUE, command
    return FollowUpAction.CONTINUE, stripped


def run_listen() -> None:
    ensure_voice("en")
    ensure_voice("pt")
    load_stt()
    settings = init_brain()
    window_s = settings.conversation_window_seconds
    face = create_face()
    face.sleep()

    logger.info("Jarvis pronto. Diga 'Jarvis' e depois a pergunta.")

    with MicSession() as mic:
        while True:
            logger.info("\nAguardando 'Jarvis'...")
            audio = mic.record_utterance(silence_seconds=WAKE_SILENCE_S)
            text, language = transcribe(audio)
            if not text:
                continue

            logger.info(f"Ouvi [{language}]: {text}")
            heard, command = split_wake_word(text)
            if not heard:
                continue

            face.listen()

            if not command:
                logger.info("Pode falar.")
                beep()
                follow_up = mic.record_utterance(
                    silence_seconds=COMMAND_SILENCE_S,
                    start_timeout=6.0,
                    ignore_ms=250,
                )
                if follow_up.size == 0:
                    logger.info("Nada depois da wake word.")
                    face.sleep()
                    continue
                command, language = transcribe(follow_up)
                command = command.strip()
                if command:
                    logger.info(f"Ouvi [{language}]: {command}")

            if not command:
                face.sleep()
                continue

            while True:
                face.think()
                try:
                    reply = generate_reply(command, language=language)
                except Exception as exc:
                    logger.error(f"Erro na LLM: {exc}")
                    face.sleep()
                    mic.clear()
                    break

                print(f"Jarvis [{language}]: {reply.spoken}")
                if reply.spoken:
                    face.answer()
                    speak(reply.spoken, language=language)
                mic.clear()

                face.listen()
                logger.info(f"\nJanela de conversa ({window_s}s)...")
                follow_audio = mic.record_utterance(
                    silence_seconds=COMMAND_SILENCE_S,
                    start_timeout=float(window_s),
                    ignore_ms=250,
                    reset_start_timeout_on_short=True,
                )
                follow_text, follow_language = transcribe(follow_audio)
                if follow_text:
                    logger.info(f"Ouvi [{follow_language}]: {follow_text}")
                action, command = classify_follow_up(follow_text)

                if action is FollowUpAction.WAIT_WAKE:
                    face.sleep()
                    break

                if action is FollowUpAction.AWAIT_COMMAND:
                    logger.info("Pode falar.")
                    beep()
                    follow_up = mic.record_utterance(
                        silence_seconds=COMMAND_SILENCE_S,
                        start_timeout=6.0,
                        ignore_ms=250,
                    )
                    if follow_up.size == 0:
                        logger.info("Nada depois da wake word.")
                        face.sleep()
                        break
                    command, language = transcribe(follow_up)
                    command = command.strip()
                    if command:
                        logger.info(f"Ouvi [{language}]: {command}")
                    if not command:
                        face.sleep()
                        break
                if action is FollowUpAction.CONTINUE:
                    language = follow_language or language
