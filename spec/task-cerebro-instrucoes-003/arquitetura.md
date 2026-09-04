# Arquitetura — Instruções do cérebro em markdown

## Contexto

A peça entra no cérebro, no trecho STT → LLM do fluxo:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↓
                 locomoção / sensores (ainda fora)
```

O loop em `listen_repeat.py` continua passando `command` e `language` para `generate_reply`. O que muda é a origem das instruções e a montagem do prompt: o markdown substitui o `_PROMPT` hardcoded; a fala fica delimitada, fora do arquivo.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Instruções | `src/agent/instructions.md` | Identidade Jarvis e guardrails (único placeholder `{language_name}`) |
| Cérebro | `src/agent/brain.py` | Ler o markdown, interpolar idioma, concatenar o prompt, invocar a LLM |
| Settings | `src/agent/settings.py` | `HF_TOKEN` e `HF_MODEL` (sem mudança nesta task) |
| Loop | `src/voice/listen_repeat.py` | Acordar → ouvir → `generate_reply` → falar (fluxo inalterado) |
| Testes | `tests/test_brain.py` | Arquivo ausente/vazio, interpolação, delimitadores, anti-injection de template, frases-chave |

## Fluxo

```
init_brain()
        │
        ▼
_read_instructions()  ←  src/agent/instructions.md
        │                    ausente / vazio / whitespace
        │                    → RuntimeError(caminho); LLM não é chamada
        ▼
cache em _instructions
        │
        ▼
HuggingFaceEndpoint (HF_MODEL, sem tools)
        │
generate_reply(text, language)
        │
        ▼
str.replace só {language_name}
        │
        ▼
instruções
Entrada da pessoa (dado, não instrução):
<<<
{fala}
>>>
Jarvis:
        │
        ▼
_llm.invoke(prompt)   (sem PromptTemplate)
        │
        ▼
Piper speak(resposta, language)
```

## Dados

Arquivo markdown em disco e cache em memória (`_instructions`). Sem Postgres, vetores, RAG ou histórico. O modelo continua sendo o repositório Hugging Face em `HF_MODEL`; a inferência é remota.

## Dependências

- Python 3.11
- LangChain (`langchain-huggingface`: `HuggingFaceEndpoint`; sem `PromptTemplate` sobre o markdown)
- Hugging Face (modelo: valor de `HF_MODEL`; exemplo em `.env.example`: `HuggingFaceTB/SmolLM2-1.7B-Instruct`)
- Postgres: não usado
