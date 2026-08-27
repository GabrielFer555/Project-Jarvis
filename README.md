# Project Jarvis

Robô conversacional que anda e usa uma LLM como cérebro de operações.

O objetivo é um assistente físico: escuta, pensa, fala e se move. Cada etapa é construída e validada isoladamente antes de entrar no loop principal.

Histórico detalhado do que já foi feito: [docs/progresso.md](docs/progresso.md).

## Visão

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↓
                 locomoção / sensores
```

A LLM decide o que dizer e o que fazer. Voz e movimento são atuadores; microfone e sensores são entradas.

## Estrutura

```
project-jarvis/
├── src/
│   ├── main.py                 # ponto de entrada (ouvir e repetir)
│   ├── agent/                  # cérebro (LLM) — ainda vazio
│   ├── voice/
│   │   ├── listen_repeat.py    # wake word + repetir
│   │   ├── mic.py              # microfone e VAD
│   │   ├── stt.py              # Whisper
│   │   ├── tts.py              # Piper
│   │   ├── voices.py           # vozes EN/PT
│   │   └── models/             # modelos Piper
│   ├── hardware/               # sensores e I/O — ainda vazio
│   ├── vision/                 # câmera e percepção — ainda vazio
│   ├── memory/                 # memória do agente — ainda vazio
│   └── robot/                  # locomoção — ainda vazio
├── tests/                      # reservado
├── docs/
│   └── progresso.md
├── requirements.txt
└── README.md
```

## Progresso

| Etapa | Status | Descrição |
| --- | --- | --- |
| 1. TTS offline | Feito | Piper sintetiza e reproduz áudio localmente (EN e PT) |
| 2. STT + wake word | Feito | Whisper transcreve; "Jarvis" aciona o ouvir e repetir |
| 3. Cérebro (LLM) | Pendente | Integração da LLM para diálogo e decisões |
| 4. Loop conversacional | Pendente | Ouvir → pensar → falar, em ciclo |
| 5. Locomoção | Pendente | Andar e reagir a comandos da LLM |
| 6. Integração no hardware | Pendente | Raspberry Pi e corpo do robô |

## O que já funciona

Depois da wake word **Jarvis**, o microfone captura a frase, o Whisper transcreve (PT ou EN) e o Piper repete com a voz do mesmo idioma.

- `speak(text, language=None)` — sintetiza e toca
- `transcribe(audio)` — devolve `(texto, idioma)`
- `run_listen_repeat()` — loop: acordar → ouvir → repetir

Dá para falar tudo numa frase (`Jarvis olá, tudo bem?`) ou em duas (`Jarvis` … `olá, tudo bem?`).

Vozes:

- Inglês: `en_US-lessac-medium` (já no repo)
- Português: `pt_BR-faber-medium` (baixada na primeira execução)

## Como rodar

Use **Python 3.11**. Neste repositório, `py` (sem versão) aponta para o 3.14, que não tem as dependências.

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 src/main.py
```

Na primeira execução o Whisper `base` e a voz PT são baixados. Depois: Ctrl+C para sair.

Dependências: `piper-tts`, `sounddevice`, `numpy`, `faster-whisper`.

## Decisões e problemas já resolvidos

- **Dois Pythons no Windows.** Sempre usar `py -3.11`.
- **API do Piper 1.6.** Quem grava o WAV é `synthesize_wav()`.
- **Idioma automático.** Whisper detecta PT/EN; o TTS escolhe a voz correspondente.
- **`output.wav` é gerado.** Está no `.gitignore`.

## Próximo passo

Ligar a LLM no lugar da repetição, para o robô responder em vez de só ecoar.

## Licença

MIT — ver [LICENSE](LICENSE).
