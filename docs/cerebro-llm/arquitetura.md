# Arquitetura — Cérebro LLM

## Contexto

A peça entra no lugar da repetição:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↓
                 locomoção / sensores (ainda fora)
```

A wake word e o VAD permanecem em `src/voice/`. Só o trecho “o que falar” muda: em vez de `speak(command)`, o loop chama `generate_reply` e depois `speak(reply)`.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Variáveis de ambiente | `.env` / `.env.example` | Token Hugging Face e id do modelo |
| Settings | `src/agent/settings.py` | Carregar dotenv, validar `HF_TOKEN` e `HF_MODEL` |
| Cérebro | `src/agent/brain.py` | Um prompt + `HuggingFaceEndpoint`, sem tools |
| Loop | `src/voice/listen_repeat.py` | Acordar → ouvir → pensar → falar |

## Fluxo

```
.env (HF_TOKEN, HF_MODEL)
        │
        ▼
init_brain()  →  HuggingFaceEndpoint (provider=auto, text-generation)
        │
wake word "Jarvis" + frase
        │
        ▼
generate_reply(texto, idioma)
        │
        ▼
Piper speak(resposta, language)
```

## Dados

Nenhum banco. Sem Postgres nesta etapa. O modelo é o repositório Hugging Face indicado em `HF_MODEL`; a inferência é remota (Inference Providers), não local.

## Dependências

- Python 3.11
- LangChain (`langchain-core`, `langchain-huggingface`) — só invocação, sem tools
- Hugging Face (modelo: valor de `HF_MODEL`; exemplo em `.env.example`: `HuggingFaceTB/SmolLM2-1.7B-Instruct`)
- `python-dotenv`
- Postgres: não usado
