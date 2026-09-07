# Arquitetura — Cérebro LLM

## Contexto

A peça entra no lugar da repetição:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↓
                 locomoção / sensores (ainda fora)
```

A wake word e o VAD permanecem em `src/voice/`. Só o trecho "o que falar" muda: em vez de `speak(command)`, o loop chama `generate_reply` e depois `speak(reply)`. O modo `--text` é um segundo chamador do mesmo `generate_reply` (`src/agent/text_chat.py`); a assinatura do cérebro não muda.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Variáveis de ambiente | `.env` / `.env.example` | Chave da Groq e id do modelo |
| Settings | `src/agent/settings.py` | Carregar dotenv, validar `GROQ_API_KEY` e `GROQ_MODEL` |
| Instruções | `src/agent/instructions.md` | Identidade e guardrails, em português, fora do Python |
| Cérebro | `src/agent/brain.py` | Ler instruções, montar o prompt e invocar `ChatGroq`, sem tools |
| Loop de voz | `src/voice/listen_repeat.py` | Acordar → ouvir → pensar → falar |
| Loop de texto | `src/agent/text_chat.py` | Segundo chamador: stdin → `generate_reply` → stdout |
| Testes | `tests/test_settings.py`, `tests/test_brain.py` | Env obrigatório, prompt e contrato, com `ChatGroq` mockado |

## Fluxo

```
.env (GROQ_API_KEY, GROQ_MODEL)
        │
        ▼
init_brain()  →  instructions.md + ChatGroq(model, temperature=0.7, max_tokens=128)
        │
wake word "Jarvis" + frase
        │
        ▼
generate_reply(texto, idioma)     # voz: listen_repeat; texto: text_chat
        │
        ├── prompt = instruções + fala entre <<< e >>>
        └── resposta = AIMessage.content
        │
        ├── voz   → Piper speak(resposta, language)
        └── texto → print no terminal (sem Piper)
```

## Contratos

```python
def load_settings() -> Settings    # token e model; RuntimeError se faltar env
def init_brain() -> Settings       # lê instructions.md e monta o ChatGroq uma vez
def generate_reply(text: str, language: str = "") -> str
```

| Chave | Papel |
| --- | --- |
| `GROQ_API_KEY` | Chave da Groq ([console.groq.com/keys](https://console.groq.com/keys)) |
| `GROQ_MODEL` | Id do modelo, ex. `openai/gpt-oss-20b` |

O prompt é montado por concatenação, sem `PromptTemplate`: as instruções de `instructions.md` (com `{language_name}` resolvido para "português", "inglês" ou "o mesmo idioma da pessoa") e a fala da pessoa entre `<<<` e `>>>`, terminando em `Jarvis:`. A resposta falada é `AIMessage.content`, com `strip()`.

## Dados

Nenhum banco. Sem Postgres nesta etapa. O modelo roda na infraestrutura da Groq; a inferência é remota.

## Dependências

- Python 3.11
- LangChain (`langchain-core`, `langchain-groq`) — só invocação, sem tools
- Groq (modelo: valor de `GROQ_MODEL`; exemplo em `.env.example`: `openai/gpt-oss-20b`)
- `python-dotenv`
- Postgres: não usado

## Decisões

| Decisão | Motivo |
| --- | --- |
| `ChatGroq` no lugar de `HuggingFaceEndpoint` | Inferência estável e rápida para conversa por voz |
| Instruções em markdown | Tom, limites e recusas mudam sem tocar Python |
| Prompt por concatenação | A fala entra como dado delimitado, sem template interpretar chaves |
| Falar só `AIMessage.content` | Evita mandar raciocínio interno ou objeto LangChain para o TTS |
| `temperature=0.7`, `max_tokens=128` | Resposta curta, pronta para ser falada |
| Sem tools nem RAG | Pedido explícito: nenhum processamento extra no caminho da conversa |
