# Project Jarvis

Robô conversacional que anda e usa uma LLM como cérebro de operações.

O objetivo é um assistente físico: escuta, pensa, fala e se move. Cada etapa é construída e validada isoladamente antes de entrar no loop principal.

Mapa das funcionalidades: [docs/](docs/README.md) — [cérebro](docs/cerebro-llm/regra-de-negocio.md), [chat texto](docs/chat-texto/regra-de-negocio.md), [rosto](docs/rosto-do-robo/regra-de-negocio.md), [spec](docs/spec/regra-de-negocio.md). Padrões do projeto: [docs/padroes-de-implementacao.md](docs/padroes-de-implementacao.md). Histórico detalhado: [docs/progresso.md](docs/progresso.md). Plano e decisão de cada task: [spec/](spec/task-spec-docs-vivas-006/plano.md) (skill spec; a execução é `/rock-it`).

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
│   │   ├── instructions.md     # identidade e guardrails (não no Python)
│   │   └── text_chat.py        # chat por texto no terminal (--text)
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
├── docs/                       # documentação viva das funcionalidades
│   ├── README.md               # índice: funcionalidade → doc → código
│   ├── padroes-de-implementacao.md
│   ├── progresso.md
│   ├── spec/
│   ├── cerebro-llm/
│   ├── chat-texto/
│   └── rosto-do-robo/
├── spec/
│   └── task-{slug}-{NNN}/      # plano + decisão da task (001, 002, …)
├── .vscode/
│   └── launch.json             # debug no Cursor: chat texto e voz
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
| Chat texto (debug) | Feito | `--text` no terminal; F5 no Cursor (Python 3.11) |
| 5. Locomoção | Pendente | Andar e reagir a comandos da LLM |
| 6. Integração no hardware | Parcial | Rosto no terminal; LCD no Raspberry Pi ainda TODO |

## O que já funciona

Depois da wake word **Jarvis**, o microfone captura a frase, o Whisper transcreve (PT ou EN), a LLM estrutura a resposta e o Piper fala essa resposta com a voz do mesmo idioma.

- `speak(text, language=None)` — sintetiza e toca
- `transcribe(audio)` — devolve `(texto, idioma)`
- `generate_reply(text, language)` — LLM (LangChain / Groq), sem tools; identidade e guardrails em `src/agent/instructions.md`, não no Python
- `run_listen_repeat()` — loop: acordar → ouvir → pensar → falar
- `run_text_chat(language="pt")` — chat por texto no terminal (`--text`), sem microfone, Whisper ou Piper
- Rosto: Sleeping → Listening → Thinking → Answering → Sleeping (mock no terminal; só no loop de voz)

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
py -3.11 src/main.py --text
py -3.11 src/main.py --text --lang en
```

Sem `--text`, o loop de voz sobe (na primeira execução o Whisper `base` e a voz PT são baixados). Com `--text`, o chat no terminal usa o mesmo cérebro, sem áudio. Encerrar: `sair`, `quit`, `exit` ou Ctrl+C.

Para depurar no Cursor: **Python: Select Interpreter** → Python 3.11, depois F5 na configuração `Jarvis: chat texto` ou `Jarvis: voz` (`.vscode/launch.json`; console no terminal integrado para o `input()`).

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
- **Pasta por task.** Plano e decisão da task em `spec/task-{slug}-{NNN}/` na raiz (001, 002, …), congelados no tempo.
- **Spec planeja, rock-it executa.** A spec grava plano, regra de negócio e arquitetura da task e para; código, testes e a documentação viva de `docs/` são do `/rock-it`.
- **`docs/` é a fonte viva.** Uma funcionalidade tem uma pasta só: feature que mexe no cérebro atualiza `docs/cerebro-llm/`, não cria pasta nova. Padrões do projeto num arquivo único.

## Próximo passo

Locomoção e, no hardware, desenhar os quatro estados do rosto no LCD.

## Licença

MIT — ver [LICENSE](LICENSE).
