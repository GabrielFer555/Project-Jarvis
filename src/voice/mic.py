from collections import deque
import queue

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHUNK_MS = 30
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_MS // 1000
PRE_ROLL_CHUNKS = 12
CALIBRATE_CHUNKS = 20


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(chunk), dtype=np.float64)))


def play_audio(
    audio: np.ndarray,
    samplerate: int,
    lead_s: float = 0.28,
    tail_s: float = 0.45,
    blocking: bool = True,
) -> None:
    """Play audio with silence around it so the device does not clip either end."""
    lead = np.zeros(int(samplerate * lead_s), dtype=audio.dtype)
    tail = np.zeros(int(samplerate * tail_s), dtype=audio.dtype)
    sd.play(
        np.concatenate([lead, audio, tail]),
        samplerate,
        blocking=blocking,
        latency="high",
    )


def beep(frequency: float = 880.0, duration: float = 0.12, blocking: bool = False) -> None:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    tone = (0.22 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    play_audio(tone, SAMPLE_RATE, lead_s=0.04, tail_s=0.04, blocking=blocking)


class MicSession:
    """Keeps the microphone open so listening can start without reopening the device."""

    def __init__(self) -> None:
        self._q: queue.Queue[np.ndarray] = queue.Queue(maxsize=250)
        self.noise_rms: float | None = None
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=CHUNK_SAMPLES,
            latency="high",
            callback=self._on_audio,
        )

    def _on_audio(self, indata, _frames, _time_info, _status) -> None:
        chunk = indata[:, 0].copy()
        try:
            self._q.put_nowait(chunk)
        except queue.Full:
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            self._q.put_nowait(chunk)

    def start(self) -> None:
        self._stream.start()
        self._calibrate()
        play_audio(
            np.zeros(int(SAMPLE_RATE * 0.05), dtype=np.float32),
            SAMPLE_RATE,
            lead_s=0.15,
            tail_s=0.05,
        )

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()

    def __enter__(self) -> "MicSession":
        self.start()
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    def _read(self) -> np.ndarray:
        return self._q.get()

    def clear(self) -> None:
        while True:
            try:
                self._q.get_nowait()
            except queue.Empty:
                break

    def _calibrate(self) -> None:
        samples = [_rms(self._read()) for _ in range(CALIBRATE_CHUNKS)]
        quiet = sorted(samples)[: max(1, len(samples) // 2)]
        self.noise_rms = float(np.median(quiet))

    def record_utterance(
        self,
        silence_seconds: float = 1.6,
        max_seconds: float = 12.0,
        min_speech_seconds: float = 0.25,
        start_timeout: float | None = None,
        ignore_ms: int = 0,
    ) -> np.ndarray:
        """Record until a pause after speech. Empty array if nobody speaks in time."""
        pre_roll: deque[np.ndarray] = deque(maxlen=PRE_ROLL_CHUNKS)
        frames: list[np.ndarray] = []
        speech_started = False
        silent_chunks = 0
        speech_chunks = 0
        waited_chunks = 0
        ignore_chunks = ignore_ms // CHUNK_MS
        max_chunks = int(max_seconds * 1000 / CHUNK_MS)
        silence_needed = int(silence_seconds * 1000 / CHUNK_MS)
        min_speech_chunks = int(min_speech_seconds * 1000 / CHUNK_MS)
        start_limit = (
            int(start_timeout * 1000 / CHUNK_MS) if start_timeout is not None else None
        )
        noise_rms = self.noise_rms or 0.008
        threshold = max(noise_rms * 2.2, 0.008)

        while True:
            chunk = self._read()
            rms = _rms(chunk)
            waited_chunks += 1

            if waited_chunks <= ignore_chunks:
                pre_roll.append(chunk)
                continue

            if rms > threshold:
                if not speech_started:
                    frames.extend(pre_roll)
                    speech_started = True
                silent_chunks = 0
                speech_chunks += 1
                frames.append(chunk)
            elif speech_started:
                frames.append(chunk)
                silent_chunks += 1
                if silent_chunks >= silence_needed:
                    if speech_chunks >= min_speech_chunks:
                        break
                    frames.clear()
                    speech_started = False
                    silent_chunks = 0
                    speech_chunks = 0
                    pre_roll.clear()
            else:
                pre_roll.append(chunk)
                noise_rms = 0.98 * noise_rms + 0.02 * rms
                self.noise_rms = noise_rms
                threshold = max(noise_rms * 2.2, 0.008)
                if start_limit is not None and waited_chunks >= start_limit:
                    return np.array([], dtype=np.float32)

            if speech_started and len(frames) >= max_chunks:
                break

        if not frames:
            return np.array([], dtype=np.float32)
        return np.concatenate(frames)
