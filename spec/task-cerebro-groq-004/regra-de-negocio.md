# Regra de negócio — Cérebro LLM via Groq

## Objetivo

O robô deixa de chamar Hugging Face Inference (`HuggingFaceEndpoint`) como cérebro e passa a usar modelos da Groq via LangChain (`ChatGroq`). Chave e id do modelo vêm do `.env`. Instruções em `instructions.md`, delimitadores anti-injection, ausência de tools e o loop de voz permanecem iguais.

## Comportamento

- A invocação da LLM usa `ChatGroq` (`langchain-groq`), não `HuggingFaceEndpoint` nem `langchain-huggingface`.
- Credenciais e modelo vêm de `.env`: `GROQ_API_KEY` e `GROQ_MODEL`. Sem chave ou sem modelo, `RuntimeError` na subida (fail-closed), com instrução de copiar `.env.example`.
- Não ler nem aceitar `HF_TOKEN` / `HF_MODEL` como fallback.
- `generate_reply(text, language)` e `init_brain()` mantêm o contrato. O prompt continua sendo o markdown + fala delimitada (`<<<` / `>>>`).
- A resposta falada é só o texto da mensagem (`AIMessage.content`), sem `reasoning_content` nem a representação crua do objeto LangChain.
- Sem tools, `groq/compound`, function calling, streaming, RAG ou agentes.
- `instructions.md` permanece inalterado.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | `.env` via `load_settings` | `Settings.token` / `api_key` do `ChatGroq` | Cliente LangChain Groq |
| `GROQ_MODEL` | `.env` via `load_settings` | `Settings.model` / `model` do `ChatGroq` | Cliente LangChain Groq |
| `src/agent/instructions.md` | Disco, lido em `init_brain()` | Bloco de instrução (cache `_instructions`) | Prompt da LLM |
| Frase transcrita | STT (Whisper), via `generate_reply` | Texto delimitado por `<<<` `>>>` | Prompt da LLM (dado, não template) |
| `AIMessage` da Groq | `ChatGroq.invoke` | `.content` (string, `strip()`) | TTS (Piper) |

## Exceções

- `GROQ_API_KEY` ausente ou em branco: `RuntimeError` citando `GROQ_API_KEY`; a Groq não é chamada.
- `GROQ_MODEL` ausente ou em branco: `RuntimeError` citando `GROQ_MODEL`; a Groq não é chamada.
- Arquivo `instructions.md` ausente, vazio ou só whitespace: `RuntimeError` com o caminho; a LLM não é chamada.
- Se a mensagem não tiver `.content`, usa-se `str(raw)` e depois `strip()`.

## Fora de escopo

- Manter Hugging Face como provedor alternativo da LLM ou ler `HF_TOKEN` / `HF_MODEL`.
- Tools, `groq/compound`, function calling, streaming, RAG, Postgres.
- Trocar Whisper ou o download das vozes Piper (continuam no Hub).
- Alterar `instructions.md` ou o loop `listen_repeat.py`.
- Migrar `docs/cerebro-llm/`.
- Commitar `.env` ou a chave real.
