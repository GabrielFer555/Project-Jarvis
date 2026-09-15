# Arquitetura — Voz

## Contexto

A peça é o canal de áudio do robô: microfone, wake word, STT, TTS e o loop que orquestra cérebro e rosto.

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                 ↑                    │
                 └── janela (env) ────┘
                      (sem wake word)
```

A wake word permanece a porta de **entrada**. Depois do Piper, o microfone continua escutando na janela. O cérebro, a memória e o rosto são chamados daqui; este pacote não conhece Postgres nem a Groq além de `generate_reply`.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Loop de voz | `src/voice/listen.py` | Wake word, turno, janela de follow-up, transições do rosto; exporta `run_listen` |
| Pacote voz | `src/voice/__init__.py` | Reexporta `run_listen` (não `run_listen_repeat`) |
| Entrada | `src/main.py` | Chama `run_listen()` no ramo sem `--text` |
| `FollowUpAction` | `src/voice/listen.py` | Enum da classificação: `WAIT_WAKE`, `AWAIT_COMMAND`, `CONTINUE` |
| `classify_follow_up` | `src/voice/listen.py` | Decidir se a transcrição da janela continua, pede pergunta ou volta à wake word |
| `split_wake_word` | `src/voice/listen.py` | Detectar **Jarvis** e o comando depois dela |
| Microfone / VAD | `src/voice/mic.py` | `record_utterance`; `start_timeout` só no silêncio; `reset_start_timeout_on_short` (default `False`) |
| STT | `src/voice/stt.py` | Whisper `base`, CPU, int8; devolve `(texto, idioma)` |
| TTS | `src/voice/tts.py` | Piper: sintetiza WAV e toca |
| Vozes | `src/voice/voices.py` | Catálogo EN/PT; download da voz PT no Hugging Face Hub |
| Settings | `src/agent/settings.py` | `conversation_window_seconds` (default 15) |
| Cérebro | `src/agent/brain.py` | `generate_reply` inalterado |
| Rosto | `src/hardware/face/` | Inalterado; o loop só muda **quando** chama `listen()` / `sleep()` |
| Testes | `tests/test_listen.py`, `tests/test_settings.py` | Classificador, wake word e env; sem hardware |

## Fluxo

```
.env → load_settings() → conversation_window_seconds (default 15)
        │
        ▼
run_listen()                          # src/voice/listen.py
Aguardando Jarvis
        │
        ▼
wake word (+ frase ou “Pode falar.” / 6s, sem reset_start_timeout_on_short)
        │
        ▼
think → generate_reply → answer → speak
        │
        ├── exceção → sleep → Aguardando Jarvis
        │
        ▼
mic.clear(); face.listen()            # janela, NÃO sleep
record_utterance(
    start_timeout=window_s,
    reset_start_timeout_on_short=True,
)                                     # window_s só no silêncio
        │
        ├── silêncio contínuo / classify wait_wake → sleep → Aguardando Jarvis
        ├── fala começa → timeout da janela cancelado; take até COMMAND_SILENCE_S
        │         └── take curta descartada → waited_chunks zera (janela cheia)
        ├── classify await_command → Pode falar. / 6s (flag omitido / False)
        │         └── sem frase → sleep → Aguardando Jarvis
        └── classify continue → think → speak → janela REINICIA cheia
```

## Contratos

```python
# src/agent/settings.py
class Settings:
    conversation_window_seconds: int = 15  # CONVERSATION_WINDOW_SECONDS

def load_settings() -> Settings
    # _positive_int("CONVERSATION_WINDOW_SECONDS", ..., 15)
    # ausente/vazia → 15; não inteiro ou <= 0 → RuntimeError

# src/voice/listen.py
def split_wake_word(text: str) -> tuple[bool, str]: ...

class FollowUpAction(Enum):
    WAIT_WAKE = "wait_wake"
    AWAIT_COMMAND = "await_command"
    CONTINUE = "continue"

def classify_follow_up(text: str) -> tuple[FollowUpAction, str]:
    """Retorna (ação, comando)."""

def run_listen() -> None: ...

# src/voice/mic.py
def record_utterance(
    ...,
    start_timeout: float | None = None,
    ignore_ms: int = 0,
    reset_start_timeout_on_short: bool = False,
) -> np.ndarray: ...

# src/voice/stt.py
def transcribe(audio: np.ndarray, model_size: str = "base") -> tuple[str, str]

# src/voice/tts.py
def speak(text, output_file=None, play=True, language=None) -> Path
```

`start_timeout` aborta **somente** enquanto não há fala. Com fala iniciada, o corte da take é `silence_seconds`. Take descartada (abaixo de `min_speech_seconds`) zera `waited_chunks` **somente** se `reset_start_timeout_on_short=True`: a janela passa `True`; o **Pode falar.** (`start_timeout=6.0`) não passa o flag (prazo desde o início). `CONVERSATION_WINDOW_SECONDS` **não** vai em `max_seconds`.

`WAKE_SILENCE_S` (0.4) e `COMMAND_SILENCE_S` (1.6) são constantes do módulo: cortes de VAD da frase, não o fim da conversa.

Não há reexport de `run_listen_repeat` nem de `listen_repeat`.

| Chave | Papel |
| --- | --- |
| `CONVERSATION_WINDOW_SECONDS` | Opcional. Segundos de **silêncio contínuo** para fechar a janela. Default `15`. Inteiro `> 0`. Não é teto da frase |

## Dados

Nenhum dado persistido neste pacote. Sessão e mensagens continuam em Postgres via `generate_reply`. Fechar a janela de voz não grava `ended_at`. Áudio gerado (`output.wav`) não entra no git.

## Dependências

- Python 3.11
- `sounddevice` / `numpy` (microfone e reprodução)
- faster-whisper (STT)
- Piper (TTS)
- LangChain + Groq (cérebro, chamado daqui)
- Hugging Face Hub (artefatos STT/TTS: Whisper `base` e voz PT)
- `python-dotenv` (já usado em `load_settings`)

## Decisões

| Decisão | Motivo |
| --- | --- |
| `CONVERSATION_WINDOW_SECONDS` no `.env`, default 15 | Timeout da janela configurável; mesmo `_positive_int` de `SESSION_IDLE_MINUTES` |
| Timeout só no silêncio; janela reinicia depois do TTS | Os segundos não podem cortar quem já está falando; o relógio volta cheio na próxima escuta |
| `reset_start_timeout_on_short` só na janela | Take curta devolve o relógio cheio no follow-up; o **Pode falar.** (6s) mantém o prazo desde o início |
| Env não alimenta `max_seconds` | `max_seconds=12` já é teto técnico de uma take; a janela é outra regra |
| `WAKE_SILENCE_S` / `COMMAND_SILENCE_S` continuam constantes | São cortes de VAD da frase, não o fim da conversa |
| Arquivo `listen.py` e função `run_listen()` | `listen_repeat` nomeava o eco da frase; o loop já é cérebro + TTS |
| Sem alias do nome antigo | Um caminho só no código vivo |
| Follow-up sem wake word | A janela só faz sentido se a pessoa puder responder naturalmente |
| `classify_follow_up` separado do loop | Ramificação testável sem microfone |
| Listening na janela, sem estado novo | Os quatro estados do rosto já cobrem “escutando” |
| Falha da LLM fecha a janela | Sem resposta, volta a exigir **Jarvis** |
| Não expirar a sessão ao fechar a janela | `SESSION_IDLE_MINUTES` é o corte da memória; a janela é só o microfone |
