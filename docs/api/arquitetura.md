# Arquitetura — API HTTP e healthcheck

## Contexto

O pacote `src/api/` expõe HTTP ao lado dos loops existentes. A API traduz os resultados das fronteiras de memória e cérebro; não importa SQLAlchemy nem monta cliente LangChain.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Registro de rotas | `src/api/app.py` | Despachar `(método, path)` para o handler e serializar JSON |
| Healthcheck | `src/api/routers/health.py` | Executar os dois pings e compor 200 ou 503 |
| Servidor | `src/api/server.py` | Bind síncrono em localhost e `serve_forever()` em thread daemon |
| Ping Postgres | `src/memory/db.py` | Executar `SELECT 1` pela engine existente |
| Ping Groq | `src/agent/brain.py` | Autenticar por GET em `/openai/v1/models`, sem invocar LLM |
| Entrada | `src/main.py` | Carregar settings, iniciar API e despachar voz ou texto |

## Fluxo

```
load_settings()
      │
      ▼
start_api() ── bind falhou ──► exceção; loop não começa
      │
      └── serve_forever() em thread daemon
      │
      ├── --text ─► run_text_chat() ─► init_brain() ─► loop
      └── voz    ─► run_listen_repeat() ─► init_brain() ─► loop

GET /health
      ├── memory.db.ping() ─────► postgres up|down
      ├── agent.brain.ping_groq() ► groq up|down
      ├── ambos up ─────────────► HTTP 200
      └── qualquer down ────────► HTTP 503
```

## Contratos

```python
# src/api/routers/health.py
def health() -> tuple[int, dict[str, str]]

# src/api/server.py
def start_api() -> None

# fronteiras chamadas pela API
def ping() -> None
def ping_groq() -> None
```

| HTTP | Corpo |
| --- | --- |
| 200 | `{"status": "ok", "postgres": "up", "groq": "up"}` |
| 503 | `{"status": "unavailable", "postgres": "up"|"down", "groq": "up"|"down"}` |
| 404 | `{"status": "not_found"}` |

| Chave | Papel |
| --- | --- |
| `API_PORT` | Porta local opcional; default 8080; deve ser inteira e positiva |

O host é fixo em `127.0.0.1`. `start_api()` constrói, binda e ativa `ThreadingHTTPServer` na thread chamadora; só depois cria a daemon com `server.serve_forever`.

## Dados

Nenhuma tabela nova. A API não recebe objetos ORM. `ping()` usa a engine da memória sem consultar sessões ou mensagens; `ping_groq()` não persiste dados.

## Dependências

- Python 3.11
- stdlib `http.server`, `json`, `threading` e `urllib.request`
- Postgres pela fronteira `src/memory/db.py`
- Groq pela fronteira `src/agent/brain.py`

## Decisões

| Decisão | Motivo |
| --- | --- |
| Domínio `src/api/` separado | Endpoints podem crescer sem misturar transporte, ORM e cérebro |
| Registro explícito de rotas | Um endpoint JSON não exige framework web |
| `ThreadingHTTPServer` da stdlib | Evita dependência HTTP nova nesta task |
| Bind síncrono antes do loop | Falha de subida impede o Jarvis de rodar sem HTTP |
| `serve_forever()` em daemon | HTTP acompanha o ciclo de vida do mesmo processo |
| Dois pings sempre executados | A resposta informa o estado independente das dependências |
| Pings atrás das fronteiras | Memória mantém SQLAlchemy; cérebro mantém a integração Groq |
| Corpo sem detalhes internos | Evita expor credenciais, URLs e erros das dependências |
