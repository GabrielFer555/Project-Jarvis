# Progresso

Registro do que foi feito no Project Jarvis até agora.

## Objetivo

Construir um robô conversacional que anda e usa uma LLM como cérebro. A fala, a escuta, o raciocínio e a locomoção entram por etapas, cada uma validada sozinha antes de ir para o loop principal.

## 2026-08-13

### Etapa 1 — TTS offline

Prova de que o robô consegue falar sem internet, com o Raspberry Pi como alvo.

O primeiro `main.py` carregava a voz Piper `en_US-lessac-medium`, sintetizava uma frase de teste e reproduzia o WAV com `sounddevice`.

Dependências: `piper-tts`, `sounddevice`, `numpy`.

### Problemas dessa etapa

1. **Python errado.** `pip install` ia para o Python 3.11. `py` (sem versão) abre o 3.14, que não tinha os pacotes. Erro: `ModuleNotFoundError: No module named 'sounddevice'`. Correção: `py -3.11` para instalar e para rodar.

2. **API do Piper 1.6.** `voice.synthesize(text, wav_file)` não grava mais o arquivo. O WAV fechava sem canais, sample rate nem sample width. Erro: `wave.Error: # channels not specified`. Correção: `voice.synthesize_wav(text, wav_file)`.

3. **`requirements.txt` inválido.** Tinha a saída do `pip install`, não a lista de pacotes. Foi reduzido a `piper-tts`, `sounddevice` e `numpy`.

### Documentação inicial

O README passou a descrever a visão do robô, a tabela de etapas e como rodar o TTS.

### Reorganização do repositório

O código saiu do script único e foi para esta estrutura:

```
src/
├── main.py
├── agent/
├── voice/
├── hardware/
├── vision/
├── memory/
└── robot/
tests/
docs/
```

O TTS foi extraído para `src/voice/tts.py`:

| Função | Papel |
| --- | --- |
| `load_voice(model_path=None)` | Carrega o modelo Piper e guarda em cache |
| `speak(text, output_file=None, play=True)` | Sintetiza, grava WAV e opcionalmente toca |

`src/main.py` só chama `speak()` com a frase de teste.

Os modelos foram para `src/voice/models/`:

- `en_US-lessac-medium.onnx`
- `en_US-lessac-medium.onnx.json`

`agent`, `hardware`, `vision`, `memory` e `robot` existem como pacotes vazios, reservados para as próximas etapas. `tests/` e `docs/` também.

`output.wav` (arquivo gerado) entrou no `.gitignore`.

### Etapa 2 — Ouvir e repetir (Whisper + wake word)

O fluxo deixou de ser só TTS. O microfone espera a wake word **Jarvis**, transcreve o que vem depois com Whisper e repete com Piper.

Comportamento:

- `Jarvis olá, tudo bem?` — uma frase só; repete o que vem depois da wake word
- `Jarvis` + pausa + `olá, tudo bem?` — bip e escuta a segunda frase
- Idioma automático: Whisper detecta PT ou EN; Piper usa `pt_BR-faber-medium` ou `en_US-lessac-medium`

Arquivos novos em `src/voice/`:

| Arquivo | Papel |
| --- | --- |
| `mic.py` | Gravação com VAD por energia e bip de confirmação |
| `stt.py` | `faster-whisper` (`base`, CPU, int8) |
| `voices.py` | Catálogo EN/PT e download da voz PT |
| `listen_repeat.py` | Loop da wake word |

A voz PT é baixada do Hugging Face na primeira execução e não entra no git. O modelo Whisper `base` vai para o cache do Hugging Face.

`src/main.py` agora só chama `run_listen_repeat()`.

## 2026-08-30

### Spec — plano de execução de task

O repositório passou a ter um contrato de como uma solicitação vira etapa: plano com branch base e modo (`non stop` ou `parada por execução`), requisitos, implementação por etapas, Gherkin, testes só se necessário, fora de escopo, dúvidas impeditivas e documentação.

A skill do agente está em `.cursor/skills/spec/`. A documentação da funcionalidade, no formato padrão do projeto, está em `docs/spec/`:

| Arquivo | Papel |
| --- | --- |
| `regra-de-negocio.md` | Quando parar, o que entra e o que não entra |
| `arquitetura.md` | Onde a spec se encaixa no fluxo do robô e nos arquivos |
| `padroes-de-implementacao.md` | Formato do plano, stack e como atualizar README/progresso |

Cada task nova grava plano e docs da feature em `spec/task-{slug}-{NNN}/` na raiz (número sequencial `001`, `002`, …). O diário do robô continua em `docs/progresso.md`.

Stack que toda task nova precisa respeitar: Python 3.11, LangChain, Postgres para vetores, modelos gratuitos do Hugging Face.

### Pasta de plano por task

O plano deixou de ser opcional em `docs/specs/`. Cada task cria na raiz `spec/task-{slug}-{NNN}/` (número sequencial `001`, `002`, …) com `plano.md`, progresso da execução nesse arquivo, e regra/arquitetura/padrões da feature.

Primeira pasta: `spec/task-pasta-de-planos-001/`. Docs antigas em `docs/cerebro-llm/` e `docs/rosto-do-robo/` não foram migradas.

A skill `rock-it` passou a ler o mesmo caminho.

### Spec só gera o plano

A skill spec deixou de implementar. Ela só cria `spec/task-{slug}-{NNN}/plano.md` e pede `/rock-it`. Código, testes, README, `docs/progresso.md` e os três arquivos de docs da feature ficam na skill rock-it.

Pasta desta mudança: `spec/task-spec-somente-plano-002/`.

### Etapa 3 — Cérebro LLM (sem tools)

O loop deixou de ecoar a frase. Depois da wake word, a transcrição vai para `generate_reply` (LangChain `HuggingFaceEndpoint` + Hugging Face Inference Providers) e o Piper fala a resposta.

Arquivos:

| Arquivo | Papel |
| --- | --- |
| `.env.example` / `.env` | `HF_TOKEN` e `HF_MODEL` |
| `src/agent/settings.py` | Carrega dotenv e valida as chaves |
| `src/agent/brain.py` | Um prompt, uma invocação, sem tools |
| `docs/cerebro-llm/` | Regra, arquitetura e padrões |

Sem token ou modelo o programa não sobe. Sem tools, RAG ou Postgres.

### Etapa 4 — Rosto e loop conversacional

O mesmo `run_listen_repeat()` orquestra o cérebro e o rosto:

Sleeping → Listening (wake word) → Thinking (LLM) → Answering (TTS) → Sleeping.

| Arquivo | Papel |
| --- | --- |
| `src/hardware/face/base.py` | `RobotFace` + `FaceState` |
| `src/hardware/face/terminal.py` | Mock ASCII no terminal Windows |
| `src/hardware/face/lcd.py` | TODO: LCD no Raspberry Pi |
| `src/voice/listen_repeat.py` | Transições + `generate_reply` + `speak` |
| `tests/test_face.py`, `tests/test_settings.py` | Contrato do rosto e do env |
| `docs/rosto-do-robo/` | Regra, arquitetura e padrões |

## 2026-08-31

### Instruções do cérebro em markdown

O prompt hardcoded saiu de `brain.py`. Identidade e guardrails vivem em `src/agent/instructions.md` (português; único placeholder `{language_name}`). `init_brain()` lê o arquivo, guarda em `_instructions` e monta o prompt por concatenação, com a fala entre `<<<` e `>>>`. A LLM é chamada com `_llm.invoke`, sem `PromptTemplate`.

Guardrails no markdown: identidade Jarvis, no máximo duas frases para TTS, idioma exclusivo, anti-injection, recusa de ilícito/crime/pornografia/ameaças, tools só com permissão (só no prompt; o pipeline continua sem tools), sem markdown/listas/emojis/ferramentas, sem código, perguntar na dúvida.

Arquivo ausente, vazio ou só whitespace: `RuntimeError` com o caminho; a LLM não é chamada.

Testes em `tests/test_brain.py` (7 novos; 14 no total do repositório). Docs da feature em `spec/task-cerebro-instrucoes-003/`. `docs/cerebro-llm/` não foi migrado.

## 2026-09-03

### Cérebro LLM via Groq

O cérebro deixou de chamar Hugging Face Inference (`HuggingFaceEndpoint`) e passou a usar Groq via LangChain (`ChatGroq`). Chave e modelo vêm do `.env`: `GROQ_API_KEY` e `GROQ_MODEL`. Sem chave ou sem modelo, `RuntimeError` na subida (fail-closed), com instrução de copiar `.env.example`. Token em https://console.groq.com/keys. Modelo padrão de produção: `openai/gpt-oss-20b`.

`generate_reply(text, language)` e `init_brain()` mantêm o contrato. O prompt continua sendo `instructions.md` + fala entre `<<<` e `>>>`. A resposta falada é só o `.content` da mensagem (`AIMessage.content`), sem `reasoning_content` nem a representação crua do objeto LangChain. Sem tools, RAG ou agentes.

`requirements.txt` troca `langchain-huggingface` por `langchain-groq`. `langchain-core` permanece. Testes em `tests/test_settings.py` e `tests/test_brain.py` (mock de `ChatGroq`, sem rede). 17 testes no repositório.

A stack das skills spec/rock-it e de `docs/spec/` deixa de exigir Hugging Face como provedor da LLM. Groq é o cérebro. Whisper e vozes Piper podem continuar vindo do Hub; isso não é o cérebro.

Docs da feature em `spec/task-cerebro-groq-004/`. `docs/cerebro-llm/` não foi migrado. `.env` e a chave real não entram no git.

## Estado atual

Feito: TTS offline (EN/PT), STT com Whisper, wake word "Jarvis", LLM via LangChain/Groq (`ChatGroq`, sem tools), credenciais `GROQ_API_KEY` / `GROQ_MODEL`, instruções e guardrails do cérebro em `src/agent/instructions.md` (não no Python), loop ouvir → pensar → falar, rosto mock no terminal.

Pendente: locomoção, LCD no Raspberry Pi, memória vetorial.

## Próximo passo

Locomoção e implementação do LCD (`RaspberryLcdFace`).
