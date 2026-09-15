# Arquitetura — Conversação bidimensional por voz

## Contexto

A peça entra no loop de voz, depois do TTS, sem trocar STT, LLM nem Piper:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                 ↑                    │
                 └── janela (env) ────┘
                      (sem wake word)
```

A wake word permanece a porta de **entrada**. A memória já agrupa turnos na mesma sessão; o que faltava era o microfone continuar escutando após a resposta. O módulo deixa o nome `listen_repeat` (eco da frase) e passa a `listen`.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Settings | `src/agent/settings.py` | `conversation_window_seconds` (default 15) |
| Loop de voz | `src/voice/listen.py` | Wake word, turno, janela de follow-up, transições do rosto; exporta `run_listen` |
| Pacote voz | `src/voice/__init__.py` | Reexporta `run_listen` (não `run_listen_repeat`) |
| Entrada | `src/main.py` | Chama `run_listen()` no ramo sem `--text` |
| `classify_follow_up` | `src/voice/listen.py` | Decidir se a transcrição da janela continua, pede pergunta ou volta à wake word |
| `split_wake_word` | `src/voice/listen.py` | Já existe; reutilizado na janela |
| Microfone / VAD | `src/voice/mic.py` | `start_timeout` só no silêncio; `reset_start_timeout_on_short` (default `False`) zera `waited_chunks` só quando a janela passa `True`; `max_seconds` não recebe a env |
| STT / TTS | `src/voice/stt.py`, `src/voice/tts.py` | Inalterados |
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
wake word (+ frase ou “Pode falar.”)
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

def classify_follow_up(text: str) -> tuple[str, str]:
    """Retorna (ação, comando).
    ação: 'wait_wake' | 'await_command' | 'continue'
    """

def run_listen() -> None: ...

# src/voice/mic.py
def record_utterance(
    ...,
    start_timeout: float | None = None,
    reset_start_timeout_on_short: bool = False,
) -> np.ndarray: ...
```

`record_utterance`: `start_timeout` aborta **somente** enquanto não há fala. Com fala iniciada, o corte da take é `silence_seconds` (`COMMAND_SILENCE_S`, 1.6). Take descartada (abaixo de `min_speech_seconds`) zera `waited_chunks` **somente** se `reset_start_timeout_on_short=True` — a janela passa `True`; o **Pode falar.** (`start_timeout=6.0`) não passa o flag (prazo desde o início). `CONVERSATION_WINDOW_SECONDS` **não** vai em `max_seconds`.

| Chave | Papel |
| --- | --- |
| `CONVERSATION_WINDOW_SECONDS` | Opcional. Segundos de **silêncio contínuo** para fechar a janela. Default `15`. Inteiro `> 0`. Não é teto da frase |

Não há reexport de `run_listen_repeat` nem de `listen_repeat`.

## Dados

Nenhum dado persistido novo. Sessão e mensagens continuam em Postgres via `generate_reply`. Fechar a janela de voz não grava `ended_at`.

## Dependências

- Python 3.11
- `sounddevice` / `numpy` (microfone já usado)
- faster-whisper (STT)
- Piper (TTS)
- LangChain + Groq (cérebro, inalterado)
- Hugging Face Hub (artefatos STT/TTS, inalterado)
- `python-dotenv` (já usado em `load_settings`)

## Decisões

| Decisão | Motivo |
| --- | --- |
| `CONVERSATION_WINDOW_SECONDS` no `.env`, default 15 | Pedido explícito; mesmo `_positive_int` de `SESSION_IDLE_MINUTES` |
| Timeout só no silêncio; janela reinicia depois do TTS | Os segundos não podem cortar quem já está falando; o relógio volta cheio na próxima escuta |
| `reset_start_timeout_on_short` só na janela | Take curta devolve o relógio cheio no follow-up; o **Pode falar.** (6s) mantém o prazo desde o início. Não zerar de forma global no VAD |
| Env não alimenta `max_seconds` | `max_seconds=12` já é teto técnico de uma take; a janela é outra regra |
| `WAKE_SILENCE_S` / `COMMAND_SILENCE_S` continuam constantes | São cortes de VAD da frase, não o fim da conversa |
| Arquivo `listen.py` e função `run_listen()` | `listen_repeat` nomeava o eco da frase; o loop já é cérebro + TTS |
| Sem alias do nome antigo | Um caminho só no código vivo |
| Follow-up sem wake word | A janela só faz sentido se a pessoa puder responder naturalmente |
| `classify_follow_up` separado do loop | Ramificação testável sem microfone |
| Listening na janela, sem estado novo | Os quatro estados do rosto já cobrem “escutando” |
| Falha da LLM fecha a janela | Sem resposta, volta a exigir **Jarvis** |
| `--text` de fora (só o nome da função no despacho) | Já é conversa por turnos sem wake word |
| Não expirar a sessão ao fechar a janela | `SESSION_IDLE_MINUTES` é o corte da memória; a janela é só o microfone |
