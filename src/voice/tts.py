from pathlib import Path
import wave

import numpy as np
import sounddevice as sd
from piper import PiperVoice

from .mic import play_audio
from .voices import ensure_voice, normalize_language

_voices: dict[str, PiperVoice] = {}


def load_voice(
    model_path: Path | str | None = None,
    language: str | None = None,
) -> PiperVoice:
    if model_path is not None:
        path = Path(model_path)
        key = str(path)
        if key not in _voices:
            _voices[key] = PiperVoice.load(str(path))
        return _voices[key]

    lang = normalize_language(language)
    if lang not in _voices:
        _voices[lang] = PiperVoice.load(str(ensure_voice(lang)))
    return _voices[lang]


def speak(
    text: str,
    output_file: Path | str | None = None,
    play: bool = True,
    language: str | None = None,
) -> Path:
    """Synthesize text to a WAV file and optionally play it."""
    wav_path = Path(output_file) if output_file else Path("output.wav")
    voice = load_voice(language=language)

    with wave.open(str(wav_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    if play:
        with wave.open(str(wav_path), "rb") as wav_file:
            fs = wav_file.getframerate()
            audio_data = np.frombuffer(
                wav_file.readframes(wav_file.getnframes()),
                dtype=np.int16,
            )
            play_audio(audio_data, fs)

    return wav_path
