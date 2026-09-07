# Arquitetura — Cérebro LLM

## Contexto

A peça entra no lugar da repetição:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↕
                  memória (Postgres)
                      ↓
                 locomoção / sensores (ainda fora)
```

A wake word e o VAD permanecem em `src/voice/`. Só o trecho "o que falar" muda: em vez de `speak(command)`, o loop chama `generate_reply` e depois `speak(reply)`. O modo `--text` é um segundo chamador do mesmo `generate_reply` (`src/agent/text_chat.py`); a assinatura do cérebro não muda.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Variáveis de ambiente | `.env` / `.env.example` | Chave da Groq, modelo, `POSTGRES_*` e `SESSION_IDLE_MINUTES` |
| Settings | `src/agent/settings.py` | Carregar dotenv, validar obrigatórias e defaults |
| Instruções | `src/agent/instructions.md` | Identidade e guardrails, em português, fora do Python |
| Memória | `src/memory/` | Sessão ativa, gravação e janela do histórico |
| Cérebro | `src/agent/brain.py` | Ler instruções, montar a lista de mensagens, invocar `ChatGroq` e expor `ping_groq()` para o healthcheck |
| Loop de voz | `src/voice/listen_repeat.py` | Acordar → ouvir → pensar → falar |
| Loop de texto | `src/agent/text_chat.py` | Segundo chamador: stdin → `generate_reply` → stdout |
| Testes | `tests/test_settings.py`, `tests/test_brain.py`, `tests/test_memory.py` | Env, prompt como lista e recorte da janela, com `ChatGroq` e memória mockados |

## Fluxo

```
.env (GROQ_API_KEY, GROQ_MODEL, POSTGRES_*)
        │
        ▼
init_brain()  →  instructions.md + ChatGroq + assert_schema_up_to_date()
        │
wake word "Jarvis" + frase
        │
        ▼
generate_reply(texto, idioma)     # voz: listen_repeat; texto: text_chat
        │
        ├── resolve_session → append user (commit) → load_window
        ├── invoke([SystemMessage(instruções), *janela])
        │     envelope <<< >>> em cada mensagem de user
        ├── append assistant
        └── resposta = AIMessage.content
        │
        ├── voz   → Piper speak(resposta, language)
        └── texto → print no terminal (sem Piper)

GET /health → ping_groq()
                  └── GET /openai/v1/models com Bearer, User-Agent Jarvis/1.0, timeout 5s
                      (sem ChatGroq.invoke e sem conferir GROQ_MODEL)
```

## Contratos

```python
def load_settings() -> Settings    # token, model e Postgres; RuntimeError se faltar env
def init_brain() -> Settings       # lê instructions.md, verifica o esquema e monta o ChatGroq uma vez
def ping_groq() -> None             # conexão/auth via GET models; não invoca a LLM
def generate_reply(text: str, language: str = "") -> str
```

| Chave | Papel |
| --- | --- |
| `GROQ_API_KEY` | Chave da Groq ([console.groq.com/keys](https://console.groq.com/keys)) |
| `GROQ_MODEL` | Id do modelo, ex. `openai/gpt-oss-20b` |

O prompt é uma lista de mensagens LangChain, sem `PromptTemplate`: `SystemMessage` com as instruções de `instructions.md` (com `{language_name}` resolvido para "português", "inglês" ou "o mesmo idioma da pessoa"), seguidas do histórico da sessão como `HumanMessage` / `AIMessage`. Cada fala de usuário — atual ou reidratada — entra entre `<<<` e `>>>`. A resposta falada é `AIMessage.content`, com `strip()`.

## Dados

Postgres via `src/memory/`: tabelas `sessions` e `messages`. O cérebro não monta SQL; chama `resolve_session`, `append_message` e `load_window`. A inferência continua remota na Groq.

## Dependências

- Python 3.11
- LangChain (`langchain-core`, `langchain-groq`) — só invocação, sem tools
- Groq (modelo: valor de `GROQ_MODEL`; exemplo em `.env.example`: `openai/gpt-oss-20b`)
- stdlib `urllib.request` para o ping autenticado da Groq
- `src/memory/` — sessão, persistência e janela
- Postgres, via SQLAlchemy e Alembic
- `python-dotenv`

## Decisões

| Decisão | Motivo |
| --- | --- |
| `ChatGroq` no lugar de `HuggingFaceEndpoint` | Inferência estável e rápida para conversa por voz |
| Instruções em markdown | Tom, limites e recusas mudam sem tocar Python |
| Prompt como lista de mensagens | SystemMessage (instruções) + histórico da sessão; envelope `<<<` `>>>` em cada fala de usuário |
| Falar só `AIMessage.content` | Evita mandar raciocínio interno ou objeto LangChain para o TTS |
| `temperature=0.7`, `max_tokens=128` | Resposta curta, pronta para ser falada |
| `ping_groq()` separado de `generate_reply()` | O healthcheck mede conexão e autenticação sem gastar completion nem alterar o turno |
| Sem tools nem RAG | Pedido explícito: nenhum processamento extra no caminho da conversa |
