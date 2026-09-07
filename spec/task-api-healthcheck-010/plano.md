# Spec: Domínio HTTP e healthcheck (Postgres e Groq)

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 5/5 etapas

## Descrição breve da tarefa

O processo do Jarvis passa a expor HTTP num pacote próprio (`src/api/`), separado da memória, do cérebro e dos loops. O primeiro endpoint é `GET /health`: verifica se a **aplicação** alcança o Postgres (mesma engine de `src/memory/`) **e** a Groq (mesmo token de `GROQ_API_KEY`). Não é o `pg_isready` do Compose nem uma chamada de completion à LLM.

O domínio existe para receber outros endpoints depois. Esta task só entrega o healthcheck.

## Requisitos funcionais

- RF1: Existe um pacote `src/api/` que concentra HTTP. Rotas novas no futuro entram nesse pacote, não em `memory/`, `agent/` ou `voice/`. SQLAlchemy não é importado em `src/api/`.
- RF2: `GET /health` devolve **200** e JSON `{"status": "ok", "postgres": "up", "groq": "up"}` somente quando **as duas** checagens passam: `SELECT 1` no Postgres pela engine da memória, e um GET autenticado à API da Groq (`/openai/v1/models`) com `GROQ_API_KEY`.
- RF3: Se **qualquer** checagem falhar, `GET /health` devolve **503** e JSON `{"status": "unavailable", "postgres": "<up|down>", "groq": "<up|down>"}`, com o estado de cada dependência. O corpo **não** inclui URL, senha, chave, traceback nem a mensagem crua do driver ou da Groq.
- RF4: `/health` verifica só conexão (e autenticação da chave, no caso da Groq). O `ping()` sob demanda **não chama** `assert_schema_up_to_date` nem qualquer verificação Alembic. A proteção da subida permanece fail-closed: se a revisão já estiver defasada quando `init_brain()` validar a inicialização, o processo aborta, a thread daemon da API é encerrada com ele e o loop não começa. Somente se o Jarvis tiver iniciado com revisão válida e a defasagem surgir depois, banco alcançável continua `postgres: "up"`. O healthcheck também não confere existência de `GROQ_MODEL` na lista, Whisper, Piper nem sessão ativa. Falha da Groq **não** chama `ChatGroq.invoke` nem gasta completion.
- RF5: O servidor HTTP sobe no mesmo processo do loop (voz ou `--text`), em thread de fundo, na ordem `load_settings()` → `start_api()` → `run_text_chat()` ou `run_listen_repeat()`. `start_api()` constrói, binda e ativa o `ThreadingHTTPServer` sincronamente; somente depois inicia `serve_forever()` numa thread daemon e retorna. Falha na criação ou no bind se propaga, impede o despacho do fluxo escolhido e garante que o loop não rode sem HTTP. A validação de `init_brain()` permanece dentro do fluxo escolhido e ocorre depois de `start_api()`; se falhar, a exceção encerra o processo e a thread daemon antes de o loop começar. Encerrar o processo normalmente (Ctrl+C, `sair`) também derruba o servidor.
- RF6: Escuta só em `127.0.0.1`. A porta vem de `API_PORT` no `.env`: opcional, default **8080**; valor não inteiro ou `<= 0` aborta na subida com `RuntimeError` citando a variável e o valor. Ausência cai no default.
- RF7: O ping do banco mora em `src/memory/db.py` (`ping()`). O ping da Groq mora em `src/agent/brain.py` (`ping_groq()`). A API só traduz os dois resultados em HTTP. Objeto ORM não sai de `memory/`; a API não monta cliente LangChain.
- RF8: Sem autenticação neste endpoint (só localhost). Caminho desconhecido devolve **404** e JSON `{"status": "not_found"}`, sem listar as rotas. Sem CORS, TLS, proxy ou documentação OpenAPI nesta task.

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| Memória conversacional | `docs/memoria-conversacional/regra-de-negocio.md` | Exceções cobrem Postgres inacessível na **subida** e no **turno** | Continua igual; ganha `ping()` sob demanda para o healthcheck; sessão e janela intactas |
| Memória conversacional | `docs/memoria-conversacional/arquitetura.md` | `db.py` expõe `get_engine()` e `assert_schema_up_to_date()` | Ganha `ping()` (`SELECT 1`); a API é cliente, não dona da engine |
| Cérebro LLM | `docs/cerebro-llm/regra-de-negocio.md` | Falha da Groq só no turno de `generate_reply` | Sem mudar o turno. `ping_groq()` passa a existir para o healthcheck (conexão/auth, não completion) |
| Cérebro LLM | `docs/cerebro-llm/arquitetura.md` | Contratos: `load_settings`, `init_brain`, `generate_reply` | Ganha `ping_groq()`; `ChatGroq` e o prompt continuam iguais |
| Chat texto | `docs/chat-texto/arquitetura.md` | O modo `--text` entra diretamente em `run_text_chat()`, que inicializa o cérebro antes do loop | `main.py` passa a executar `load_settings()` e `start_api()` antes de despachar `run_text_chat()`; `init_brain()` continua antes do loop de entrada |
| Padrões | `docs/padroes-de-implementacao.md` | Pacotes: `voice`, `agent`, `memory`, `hardware`, `vision`, `robot` | A lista inclui `api`. Sem framework HTTP novo: stdlib `http.server` |

Nova funcionalidade: sim, criar `docs/api/` para o pacote `src/api/` e registrar no índice `docs/README.md`.

Não impactadas: `docs/chat-texto/regra-de-negocio.md`, `docs/rosto-do-robo/`, `docs/spec/`. A regra e o loop do chat texto, assim como `generate_reply`, não mudam; somente sua arquitetura de inicialização passa a incluir o servidor HTTP antes do despacho.

## Implementação técnica

### Etapa 1 — pings e porta [Concluído]

`src/memory/db.py` ganha `ping()`, ao lado de `assert_schema_up_to_date`. Não substitui a verificação de esquema.

```python
def ping() -> None:
    """Confirma que a engine alcança o Postgres. Não confere revisão Alembic."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise RuntimeError(f"Postgres inacessível: {exc}") from exc
```

`src/agent/brain.py` ganha `ping_groq()`. Stdlib `urllib.request`, **sem** `ChatGroq.invoke`. Timeout de **5 segundos**. Resposta HTTP 2xx = ok; rede, timeout, HTTP não-2xx = `RuntimeError("Groq inacessível")` (sem o corpo da Groq na mensagem pública do handler; a exceção pode citar o status internamente).

```python
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

def ping_groq() -> None:
    """Confirma que GROQ_API_KEY autentica na Groq. Não invoca o modelo."""
```

Cabeçalho `Authorization: Bearer <token>` a partir de `load_settings().token`. Não envia o texto da pessoa. Não confere se `GROQ_MODEL` está na lista.

`src/agent/settings.py`: campo `api_port: int = 8080`, lido de `API_PORT` com o mesmo `_positive_int` já usado em `POSTGRES_PORT`. Host **não** é configurável: fica `127.0.0.1` no servidor.

`.env.example` documenta `# API_PORT=8080`.

### Etapa 2 — domínio `src/api/` [Concluído]

Pacote novo, transport em stdlib (`http.server.ThreadingHTTPServer`). O roteamento é um registro explícito no pacote.

```
src/api/
├── __init__.py
├── app.py          # registro de rotas; despacha (método, path) → handler
├── server.py       # ThreadingHTTPServer em 127.0.0.1:api_port, thread daemon
└── routers/
    ├── __init__.py
    └── health.py   # GET /health
```

Contrato do handler (snapshot — é o que os testes exercitam). As duas checagens **sempre rodam**; uma falha não pula a outra, para o JSON mostrar os dois estados:

```python
def health() -> tuple[int, dict[str, str]]:
    postgres = "up"
    groq = "up"
    try:
        ping()
    except Exception:
        postgres = "down"
    try:
        ping_groq()
    except Exception:
        groq = "down"
    if postgres == "up" and groq == "up":
        return 200, {"status": "ok", "postgres": postgres, "groq": groq}
    return 503, {"status": "unavailable", "postgres": postgres, "groq": groq}
```

`app.py` serializa o dict em JSON (`Content-Type: application/json`). Caminho desconhecido → 404 JSON `{"status": "not_found"}`, sem listar rotas. `log_message` do handler não imprime corpo nem credencial.

`server.py` expõe `start_api() -> None`: lê `load_settings().api_port` e, na thread chamadora, instancia o `ThreadingHTTPServer`, concluindo construção, bind e ativação antes de criar a thread daemon. Somente `server.serve_forever()` roda na daemon; `start_api()` retorna depois de iniciá-la e não bloqueia o loop. Qualquer exceção da construção/bind/ativação se propaga sincronicamente, nenhuma thread é iniciada e o despacho para o loop não ocorre. Não importa SQLAlchemy nem LangChain.

### Etapa 3 — ligar em `main.py` [Concluído]

`src/main.py` continua fino e preserva esta ordem deliberada: `load_settings()` → `start_api()` → despacho para `run_text_chat()` ou `run_listen_repeat()`. Como `start_api()` só retorna após o bind e a ativação, falha ao ocupar `127.0.0.1:API_PORT` se propaga e impede o despacho; o loop nunca começa sem um servidor HTTP já ligado. Não antecipa `init_brain()` para o `main` e não coloca regra de healthcheck nele; os loops continuam sem conhecer HTTP.

No modo `--text`, `run_text_chat()` chama `init_brain()` depois que a thread daemon da API foi iniciada e antes de entrar no `while`. Se essa validação falhar (inclusive por revisão Alembic defasada ou Postgres inacessível), a exceção encerra o processo e, com ele, a API daemon; o loop de entrada não começa. Essa ordem mantém a subida fail-closed, ainda que a thread HTTP possa ter sido criada imediatamente antes da falha.

### Etapa 4 — testes [Concluído]

Sem rede, sem Postgres, sem chamada real à Groq e sem socket real. `ping` e `ping_groq` mockados no teste do handler. A orquestração de subida usa `ThreadingHTTPServer` e thread mockados.

- `tests/test_api_health.py`: 200 quando os dois pings passam; 503 com `postgres`/`groq` corretos quando um ou os dois levantam; corpo sem `postgres_password`, `GROQ_API_KEY`, `DATABASE_URL` nem traceback; 404 em caminho inexistente.
- `tests/test_api_server.py`: teste unitário de `start_api()` com `ThreadingHTTPServer` e thread mockados; confirma que o servidor é construído/bindado antes de a daemon ser criada/iniciada e que ela recebe `serve_forever`. Quando a construção/bind mockada levanta, a mesma exceção se propaga e nenhuma thread é criada ou iniciada. Nenhum socket real é aberto.
- `tests/test_memory.py`: teste unitário isolado de `ping()` com engine e conexão mockadas; confirma uma única execução de `SELECT 1` e que `assert_schema_up_to_date` não é chamado, sem Postgres real.
- `tests/test_brain.py`: teste unitário isolado de `ping_groq()` com settings e transporte HTTP mockados; confirma `GET https://api.groq.com/openai/v1/models`, cabeçalho `Authorization: Bearer <token>`, timeout de 5 segundos e nenhuma chamada a `ChatGroq.invoke`, sem rede real.
- `tests/test_settings.py`: `API_PORT` ausente → 8080; `"abc"` e `"0"` → `RuntimeError`.

Não testar concorrência real, ciclo de vida real da thread, socket real, nem executar `SELECT 1` ou GET reais. Testar apenas a orquestração síncrona de criação/bind e a passagem de `serve_forever` para uma daemon, tudo com mocks; os contratos dos pings também são verificados por mocks.

### Etapa 5 — documentação [Concluído]

Ver checklist em **Documentação**.

## Casos de teste (Gherkin)

```gherkin
Feature: Healthcheck da conexão com Postgres e Groq

  Scenario: Postgres e Groq no ar respondem ok
    Given a aplicação alcança o Postgres
    And a aplicação autentica na Groq
    When GET /health
    Then a resposta é 200
    And o JSON é {"status": "ok", "postgres": "up", "groq": "up"}

  Scenario: Banco inacessível responde unavailable e Groq continua visível
    Given o Postgres recusa a conexão
    And a Groq responde 2xx
    When GET /health
    Then a resposta é 503
    And o JSON tem postgres "down" e groq "up"
    And o corpo não contém senha, chave, URL nem traceback

  Scenario: Groq inacessível responde unavailable e Postgres continua visível
    Given o Postgres aceita conexão
    And a Groq recusa ou não responde
    When GET /health
    Then a resposta é 503
    And o JSON tem postgres "up" e groq "down"
    And o corpo não contém a GROQ_API_KEY nem traceback

  Scenario: Defasagem posterior à inicialização não afeta o ping de conexão
    Given o Jarvis iniciou com a revisão Alembic válida
    And depois da inicialização a revisão do banco ficou atrás da head
    And o Postgres continua aceitando conexão
    And a Groq responde 2xx
    When GET /health
    Then a resposta é 200
    And postgres é "up"
    And ping() não chama a verificação Alembic

  Scenario: Healthcheck da Groq não invoca o modelo
    Given GET /health
    Then nenhuma chamada ChatGroq.invoke acontece
    And a checagem usa o endpoint de models com a chave

  Scenario: API_PORT ausente usa 8080
    Given um .env sem API_PORT
    When o processo sobe
    Then o servidor HTTP escuta em 127.0.0.1:8080

  Scenario: API_PORT inválida aborta na subida
    Given um .env com API_PORT igual a "abc" ou a "0"
    When o processo sobe
    Then um RuntimeError cita a variável e o valor recebido
    And o loop não começa

  Scenario: Falha de bind impede o loop sem abrir socket real
    Given a construção mockada do ThreadingHTTPServer falha ao fazer bind
    When start_api é chamado antes do fluxo escolhido
    Then a exceção de bind se propaga sincronamente
    And nenhuma thread daemon é iniciada
    And o loop não começa

  Scenario: Servidor sobe junto do chat texto
    Given o processo iniciado com --text
    When GET /health em 127.0.0.1:8080
    Then a requisição é atendida pelo mesmo processo do chat

  Scenario: Falha na inicialização do cérebro encerra API antes do loop
    Given start_api iniciou a thread daemon
    And init_brain falha durante a inicialização do modo --text
    When a exceção se propaga
    Then o processo e a API são encerrados
    And o loop de entrada não começa
```

## Cobertura com testes unitários e integração

Necessária no handler: combinação postgres/groq (ambos up; um down; os dois down) e a garantia de não vazar credencial. É contrato HTTP.

`API_PORT` entra em `tests/test_settings.py` no mesmo padrão dos outros `int` opcionais.

Sem Postgres, sem Groq e sem socket: no teste do handler, `ping` e `ping_groq` ficam mockados para cobrir somente a agregação HTTP. Em teste unitário de `start_api()`, servidor e thread ficam mockados para provar a ordem construção/bind → criação/início da daemon, além da propagação da falha de construção/bind sem iniciar thread. Em testes unitários separados, `ping()` usa engine/conexão mockadas para provar que executa somente `SELECT 1`, sem Alembic; `ping_groq()` usa settings/transporte mockados para provar endpoint `/openai/v1/models`, Bearer e timeout de 5 segundos, sem `ChatGroq.invoke`. O cenário “mesmo processo do `--text`” fica para inspeção/QA.

## Fora de escopo / não coberto

- Outros endpoints (chat, sessão, admin, métricas). O domínio só se prepara para recebê-los.
- FastAPI, Flask, Starlette, uvicorn ou qualquer framework HTTP.
- Autenticação, TLS, CORS, rate limit, OpenAPI.
- Healthcheck do Whisper, do Piper ou do microfone.
- Conferir revisão Alembic no `/health`: `assert_schema_up_to_date` continua fail-closed na subida; após uma subida válida, `ping()` não a repete nas requisições.
- Conferir se `GROQ_MODEL` existe na lista de modelos; o ping só autentica a chave.
- `ChatGroq.invoke` no healthcheck (custa token e mede o modelo, não a conexão).
- Publicar a porta na LAN ou tornar o host configurável.
- Processo HTTP separado do loop (`--api` só). O servidor vive no mesmo processo.
- Kubernetes probes nomeadas (`/live` vs `/ready`), Docker HEALTHCHECK da aplicação, compose de produção.
- Trocar o `healthcheck:` do serviço Postgres no `docker-compose.yml`.
- UI, dashboard, ou documentar o endpoint além do README / `docs/api/`.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md — `src/api/` na estrutura; “O que já funciona”; Como rodar com `GET /health` em `127.0.0.1:8080`; `API_PORT` no `.env`
- [x] docs/progresso.md — seção datada
- [x] docs/README.md — índice ganha a linha da API HTTP
- [x] docs/api/regra-de-negocio.md — criar: `/health` agrega Postgres e Groq; 200 só com os dois; localhost; exceções
- [x] docs/api/arquitetura.md — criar: pacote `src/api/`, roteador, thread, contrato JSON, `ping()` e `ping_groq()` atrás das fronteiras
- [x] docs/memoria-conversacional/arquitetura.md — atualizar: `ping()` em `db.py` e nos contratos
- [x] docs/memoria-conversacional/regra-de-negocio.md — atualizar: registrar que `ping()` sob demanda executa somente `SELECT 1` para verificar a conexão usada pelo healthcheck, sem validar a revisão Alembic e sem alterar regras de sessão ou janela
- [x] docs/cerebro-llm/arquitetura.md — atualizar: `ping_groq()` nos contratos e componentes
- [x] docs/cerebro-llm/regra-de-negocio.md — atualizar: ping de conexão/auth da Groq para o healthcheck, sem mudar o turno
- [x] docs/chat-texto/arquitetura.md — atualizar somente o fluxo de inicialização: `load_settings()` → `start_api()` → `run_text_chat()` → `init_brain()` → loop; falha em `init_brain()` encerra processo/API antes do loop
- [x] docs/padroes-de-implementacao.md — atualizar: lista de pacotes inclui `api`; HTTP desta task é stdlib, sem framework
- [x] spec/task-api-healthcheck-010/regra-de-negocio.md — gravado pela spec
- [x] spec/task-api-healthcheck-010/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): docs/chat-texto/regra-de-negocio.md, docs/rosto-do-robo/, docs/spec/
