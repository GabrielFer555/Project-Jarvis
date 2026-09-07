# Arquitetura — API HTTP e healthcheck

## Contexto

HTTP entra ao lado do fluxo existente, sem substituí-lo:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↕                    ↕
                  memória (Postgres)     Groq (API)
                      ↑                    ↑
                 ping()              ping_groq()
                      \                  /
                       GET /health (src/api/)
```

O pacote `src/api/` é o domínio dos endpoints. A memória continua dona do SQLAlchemy; o cérebro continua dono da Groq. `main.py` só liga o servidor e despacha o loop.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Settings | `src/agent/settings.py` | `api_port` (default 8080), mesmo `_positive_int` das outras portas |
| Ping Postgres | `src/memory/db.py` | `ping()`: `SELECT 1` na engine existente |
| Ping Groq | `src/agent/brain.py` | `ping_groq()`: GET `/openai/v1/models` com Bearer, timeout 5s, stdlib `urllib` |
| App / roteador | `src/api/app.py` | Mapa `(método, path)` → handler; JSON; 404 |
| Health | `src/api/routers/health.py` | Roda os dois pings; traduz em 200/503 |
| Servidor | `src/api/server.py` | Constrói/binda/ativa `ThreadingHTTPServer` em `127.0.0.1` sincronamente; executa somente `serve_forever()` em thread daemon |
| Entrada | `src/main.py` | `load_settings()` → `start_api()` → loop voz ou texto |
| Testes | `tests/test_api_health.py`, `tests/test_api_server.py`, `tests/test_settings.py` | Handler com os dois pings mockados; subida/bind e thread mockados sem socket real; `API_PORT` |

## Fluxo

```
.py -3.11 src/main.py [--text]
        │
        ▼
load_settings()          # fail-closed (GROQ_*, POSTGRES_*, API_PORT)
        │
        ▼
start_api()              # construção + bind + ativação síncronos
        │
        ├── falha       → exceção se propaga; nenhuma daemon; loop não começa
        ├── sucesso     → inicia daemon com serve_forever()
        │
        ├── --text → run_text_chat() → init_brain() → loop de entrada
        └── voz    → run_listen_repeat() → inicialização → init_brain() → loop
                                      │
                                      └── falha em init_brain()
                                          → exceção encerra processo + API daemon
                                          → loop não começa

GET /health
        │
        ▼
health()
        ├── ping()      → postgres up|down
        ├── ping_groq() → groq up|down     # sempre os dois
        ├── ambos up    → 200 {"status":"ok", ...}
        └── qualquer down → 503 {"status":"unavailable", ...}
```

## Contratos

```python
# src/memory/db.py
def ping() -> None
    # SELECT 1; OperationalError → RuntimeError("Postgres inacessível: …")
    # não chama assert_schema_up_to_date nem compara revisão Alembic

# src/agent/brain.py
def ping_groq() -> None
    # GET https://api.groq.com/openai/v1/models
    # Authorization: Bearer load_settings().token
    # timeout 5s; HTTP 2xx ok; senão RuntimeError("Groq inacessível")
    # não chama ChatGroq.invoke; não usa GROQ_MODEL

# src/api/routers/health.py
def health() -> tuple[int, dict[str, str]]

# src/api/server.py
def start_api() -> None
    # constrói/binda/ativa ThreadingHTTPServer em 127.0.0.1 na thread chamadora
    # falha nessa etapa se propaga; não cria nem inicia thread daemon
    # após sucesso, inicia daemon cujo target é server.serve_forever e retorna

# src/main.py — permanece fino
def main(argv: list[str] | None = None) -> None
```

JSON do healthcheck:

| HTTP | Corpo |
| --- | --- |
| 200 | `{"status": "ok", "postgres": "up", "groq": "up"}` |
| 503 | `{"status": "unavailable", "postgres": "up"|"down", "groq": "up"|"down"}` (pelo menos um `down`) |
| 404 | `{"status": "not_found"}` |

| Chave | Papel |
| --- | --- |
| `API_PORT` | Opcional, default `8080`. Porta local do HTTP. Lixo ou `<= 0` aborta na subida |
| `GROQ_API_KEY` | Já existente. Bearer do ping da Groq |
| `GROQ_MODEL` | Já existente. **Não** entra no `/health` |

Host fixo `127.0.0.1`. Sem `API_HOST`.

## Dados

Nenhuma tabela nova. `ping()` não lê `sessions` nem `messages`. `ping_groq()` não persiste nada.

## Dependências

- Python 3.11
- stdlib `http.server`, `json`, `threading`, `urllib.request`
- Postgres via `src/memory/db.py` (SQLAlchemy já existente)
- Groq via HTTPS + `GROQ_API_KEY` (sem LangChain no caminho do ping)
- Sem FastAPI, Flask ou uvicorn

## Decisões

| Decisão | Motivo |
| --- | --- |
| Pacote `src/api/` separado | HTTP vai crescer; não misturar rota com ORM nem com o cérebro |
| stdlib `http.server` | A stack vigente não tem framework web; um GET JSON não justifica FastAPI nesta task |
| Um `/health` agregado, não dois paths | Um probe vê as duas dependências; 200 só se as duas estiverem no ar |
| Rodar os dois pings sempre | 503 com `postgres`/`groq` independentes mostra o que quebrou |
| `ping()` em `memory/db.py` | A engine é da memória; a API não importa SQLAlchemy |
| `ping_groq()` em `brain.py` | A chave e o provedor são do cérebro; a API não monta `ChatGroq` |
| GET `/openai/v1/models`, não `invoke` | Connection + auth, sem gastar completion nem medir o modelo |
| Timeout 5s na Groq | Probe não pode travar a thread HTTP à espera da rede |
| `SELECT 1`, não `assert_schema_up_to_date` | A validação de esquema é fail-closed na inicialização. Depois de uma subida com revisão válida, o `ping()` sob demanda mede só conexão, mesmo se a defasagem surgir posteriormente |
| Construção/bind/ativação síncronos em `start_api()` | O retorno comprova que o servidor já ocupou `127.0.0.1:API_PORT`; falha se propaga antes do despacho e impede o loop sem HTTP |
| Somente `serve_forever()` na thread daemon | Mantém o HTTP não bloqueante depois que a subida síncrona foi confirmada |
| `start_api()` antes de `run_text_chat()`/`init_brain()` | Preserva a ordem `load_settings()` → API confirmada → fluxo escolhido. `init_brain()` continua sendo o gate fail-closed antes do loop: se falhar, a exceção encerra o processo e a thread daemon da API, e nenhuma entrada é processada |
| 503 no turno HTTP, aborto só na subida | Probe repetido não pode matar o loop de voz |
| Bind `127.0.0.1`, porta configurável | Mesmo critério do Postgres publicado; host aberto seria exposição na LAN |
| Thread daemon no mesmo processo | O healthcheck testa **este** Jarvis, não outro processo |
| Corpo sem detalhe de erro | ISO 27001: não vazar DSN, senha nem chave |
| Sem auth no endpoint | Localhost + GET de saúde; auth entra quando o domínio sair da máquina |
