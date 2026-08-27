from pathlib import Path
from urllib.request import urlretrieve

MODELS_DIR = Path(__file__).resolve().parent / "models"

VOICES = {
    "en": {
        "file": "en_US-lessac-medium.onnx",
        "onnx": None,
        "json": None,
    },
    "pt": {
        "file": "pt_BR-faber-medium.onnx",
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"
    code = language.lower().replace("-", "_")
    if code.startswith("pt"):
        return "pt"
    if code.startswith("en"):
        return "en"
    return "en"


def voice_path(language: str) -> Path:
    lang = normalize_language(language)
    return MODELS_DIR / VOICES[lang]["file"]


def ensure_voice(language: str) -> Path:
    """Return the local Piper model path, downloading it if needed."""
    lang = normalize_language(language)
    spec = VOICES[lang]
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    onnx_path = MODELS_DIR / spec["file"]
    json_path = Path(str(onnx_path) + ".json")

    if not onnx_path.exists() and spec["onnx"]:
        print(f"Baixando voz Piper ({lang})...")
        urlretrieve(spec["onnx"], onnx_path)
    if not json_path.exists() and spec["json"]:
        urlretrieve(spec["json"], json_path)

    if not onnx_path.exists():
        raise FileNotFoundError(f"Modelo Piper não encontrado: {onnx_path}")

    return onnx_path
