# Regra de negócio — API HTTP e healthcheck

## Objetivo

O processo do Jarvis expõe HTTP em um domínio próprio. O primeiro endpoint, `GET /health`, informa se a aplicação alcança o Postgres e autentica na Groq, sem executar uma conversa.

## Comportamento

- As checagens de Postgres e Groq sempre são executadas.
- Com as duas dependências disponíveis, responde HTTP 200 e `{"status": "ok", "postgres": "up", "groq": "up"}`.
- Se qualquer dependência falhar, responde HTTP 503 e `{"status": "unavailable", "postgres": "up"|"down", "groq": "up"|"down"}`.
- O Postgres é consultado com `SELECT 1` pela engine da memória. O healthcheck não valida a revisão Alembic.
- A Groq é consultada por GET autenticado em `/openai/v1/models`, com timeout de 5 segundos. O healthcheck não chama `ChatGroq.invoke`, não gasta completion e não valida `GROQ_MODEL`.
- O servidor escuta somente em `127.0.0.1`, na porta `API_PORT` (default 8080), no mesmo processo dos loops de voz e texto.
- Caminhos desconhecidos respondem HTTP 404 e `{"status": "not_found"}`.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| `GET /health` | Cliente local | JSON com o estado agregado | Cliente local |
| `ping()` | `src/memory/db.py` | `postgres: "up"` ou `"down"` | Handler de health |
| `ping_groq()` | `src/agent/brain.py` | `groq: "up"` ou `"down"` | Handler de health |
| `API_PORT` | `.env` (opcional) | Porta HTTP; default 8080 | Servidor local |

## Exceções

- `API_PORT` não inteira ou menor ou igual a zero: `RuntimeError` na subida; o loop não começa.
- Falha de criação, bind ou ativação do servidor: a exceção se propaga antes do despacho do loop.
- Falha de Postgres ou Groq durante o healthcheck: HTTP 503; o processo continua.
- O corpo nunca inclui URL, usuário, senha, chave, traceback nem mensagem crua da dependência.
- Credencial obrigatória ausente ou revisão Alembic inválida durante `init_brain()`: a subida falha e encerra o processo e a API daemon antes do loop.

## Fora de escopo

- Outros endpoints, autenticação, TLS, CORS, rate limit e OpenAPI.
- Healthcheck de Whisper, Piper, microfone, sessão ativa ou revisão Alembic.
- Expor a API na LAN ou executar o HTTP em processo separado.
- FastAPI, Flask, Starlette ou uvicorn.
