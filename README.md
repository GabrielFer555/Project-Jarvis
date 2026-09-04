# Project Jarvis

Robô conversacional que anda e usa uma LLM como cérebro de operações.

O objetivo é um assistente físico: escuta, pensa, fala e se move. Cada etapa é construída e validada isoladamente antes de entrar no loop principal.

Histórico detalhado do que já foi feito: [docs/progresso.md](docs/progresso.md). Como planejar uma etapa: [docs/spec/](docs/spec/regra-de-negocio.md) (skill spec; a execução é `/rock-it`). Planos de task: [spec/](spec/task-spec-somente-plano-002/plano.md). Cérebro: [spec/task-cerebro-groq-004/](spec/task-cerebro-groq-004/regra-de-negocio.md). Rosto: [docs/rosto-do-robo/](docs/rosto-do-robo/regra-de-negocio.md).

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
│   ├── main.py                 # ponto de entrada (conversa)
│   ├── agent/
│   │   ├── settings.py         # .env (GROQ_API_KEY, GROQ_MODEL)
│   │   ├── brain.py            # LLM LangChain ChatGroq, sem tools
│   │   └── instructions.md     # identidade e guardrails (não no Python)
│   ├── voice/
│   │   ├── listen_repeat.py    # wake word + LLM + TTS + rosto
│   │   ├── mic.py              # microfone e VAD
│   │   ├── stt.py              # Whisper
│   │   ├── tts.py              # Piper
│   │   ├── voices.py           # vozes EN/PT
│   │   └── models/             # modelos Piper
│   ├── hardware/
│   │   └── face/               # rosto: ABC, terminal, LCD (TODO)
│   ├── vision/                 # câmera e percepção — ainda vazio
│   ├── memory/                 # memória do agente — ainda vazio
│   └── robot/                  # locomoção — ainda vazio
├── tests/
├── docs/
│   ├── progresso.md
│   ├── spec/
│   ├── cerebro-llm/
│   └── rosto-do-robo/
├── spec/
│   └── task-{slug}-{NNN}/      # plano.md + docs da feature (001, 002, …)
├── .env.example
├── requirements.txt
└── README.md
```

## Progresso

| Etapa | Status | Descrição |
| --- | --- | --- |
| 1. TTS offline | Feito | Piper sintetiza e reproduz áudio localmente (EN e PT) |
| 2. STT + wake word | Feito | Whisper transcreve; "Jarvis" aciona o ouvir e repetir |
| 3. Cérebro (LLM) | Feito | LangChain + Groq (`ChatGroq`); instruções em `instructions.md`; sem tools |
| 4. Loop conversacional | Feito | Ouvir → pensar → falar, com estados do rosto |
| 5. Locomoção | Pendente | Andar e reagir a comandos da LLM |
| 6. Integração no hardware | Parcial | Rosto no terminal; LCD no Raspberry Pi ainda TODO |

## O que já funciona

Depois da wake word **Jarvis**, o microfone captura a frase, o Whisper transcreve (PT ou EN), a LLM estrutura a resposta e o Piper fala essa resposta com a voz do mesmo idioma.

- `speak(text, language=None)` — sintetiza e toca
- `transcribe(audio)` — devolve `(texto, idioma)`
- `generate_reply(text, language)` — LLM (LangChain / Groq), sem tools; identidade e guardrails em `src/agent/instructions.md`, não no Python
- `run_listen_repeat()` — loop: acordar → ouvir → pensar → falar
- Rosto: Sleeping → Listening → Thinking → Answering → Sleeping (mock no terminal)

Dá para falar tudo numa frase (`Jarvis olá, tudo bem?`) ou em duas (`Jarvis` … `olá, tudo bem?`).

Vozes:

- Inglês: `en_US-lessac-medium` (já no repo)
- Português: `pt_BR-faber-medium` (baixada na primeira execução)

## Como rodar

Use **Python 3.11**. Neste repositório, `py` (sem versão) aponta para o 3.14, que não tem as dependências.

1. Copie `.env.example` para `.env` e preencha `GROQ_API_KEY` (token em [console.groq.com/keys](https://console.groq.com/keys)). Ajuste `GROQ_MODEL` se quiser outro modelo da Groq.
2. Instale e rode:

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 src/main.py
```

Na primeira execução o Whisper `base` e a voz PT são baixados. Depois: Ctrl+C para sair.

O cérebro lê `src/agent/instructions.md` na subida. Arquivo ausente ou vazio aborta com `RuntimeError` e a LLM não é chamada. Tom, limites e recusas mudam só nesse markdown.

Dependências: `piper-tts`, `sounddevice`, `numpy`, `faster-whisper`, `python-dotenv`, `langchain-core`, `langchain-groq`.

Testes: `py -3.11 -m unittest discover -s tests -v`.

## Decisões e problemas já resolvidos

- **Dois Pythons no Windows.** Sempre usar `py -3.11`.
- **API do Piper 1.6.** Quem grava o WAV é `synthesize_wav()`.
- **Idioma automático.** Whisper detecta PT/EN; o TTS escolhe a voz correspondente.
- **`output.wav` é gerado.** Está no `.gitignore`.
- **LLM remota, sem tools.** A chave e o modelo ficam no `.env`; o loop só chama `generate_reply` e fala o texto.
- **Rosto no terminal.** O LCD no Raspberry Pi está stubado com TODO.
- **Pasta por task.** Plano e docs da feature em `spec/task-{slug}-{NNN}/` na raiz (001, 002, …).
- **Spec não implementa.** A skill spec só grava o plano; a execução é `/rock-it`.

## Próximo passo

Locomoção e, no hardware, desenhar os quatro estados do rosto no LCD.

## Licença

MIT — ver [LICENSE](LICENSE).
