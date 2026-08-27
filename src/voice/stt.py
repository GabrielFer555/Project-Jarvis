import numpy as np
from faster_whisper import WhisperModel

_model: WhisperModel | None = None


def load_stt(model_size: str = "base") -> WhisperModel:
    global _model
    if _model is None:
        print(f"Carregando Whisper ({model_size})...")
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(audio: np.ndarray, model_size: str = "base") -> tuple[str, str]:
    """Return (text, language_code) from 16 kHz mono float32 audio."""
    if audio.size == 0:
        return "", ""

    model = load_stt(model_size)
    segments, info = model.transcribe(
        audio,
        language=None,
        vad_filter=False,
        beam_size=1,
        condition_on_previous_text=False,
    )
    text = " ".join(segment.text for segment in segments).strip()
    return text, info.language or ""
