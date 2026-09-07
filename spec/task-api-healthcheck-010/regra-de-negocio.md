# Regra de negócio — API HTTP e healthcheck

## Objetivo

O processo do Jarvis passa a responder HTTP. O primeiro uso é um healthcheck das **conexões da aplicação**: Postgres (mesma engine da memória) e Groq (mesma `GROQ_API_KEY` do cérebro). Um probe local pergunta se o robô ainda alcança banco e LLM, sem confundir isso com o `pg_isready` do contêiner nem com uma geração de texto.

Os endpoints moram num domínio próprio. Esta task só define o `/health`; o pacote existe para não misturar HTTP com memória, cérebro ou voz.

## Comportamento

- `GET /health` consulta Postgres (`SELECT 1` na engine da memória) **e** a Groq (GET autenticado em `/openai/v1/models`). As duas checagens rodam sempre, para o JSON mostrar os dois estados.
- Sucesso das duas: HTTP 200 e `{"status": "ok", "postgres": "up", "groq": "up"}`.
- Qualquer falha: HTTP 503 e `{"status": "unavailable", "postgres": "up"|"down", "groq": "up"|"down"}`. Nada no corpo identifica host, usuário, senha, chave, URL ou o texto da exceção.
- O healthcheck não é a verificação de esquema da subida. A proteção permanece fail-closed: `start_api()` ocorre antes do fluxo escolhido, mas revisão Alembic já defasada faz `init_brain()` abortar o processo e a thread daemon da API antes de o loop começar. Se o Jarvis iniciou com revisão válida e a defasagem surgiu depois, banco alcançável continua `postgres: "up"`, pois o `ping()` sob demanda não chama `assert_schema_up_to_date` nem outra verificação Alembic.
- O ping da Groq não chama o modelo (`ChatGroq.invoke`). Não gasta completion e não confere se `GROQ_MODEL` está na lista. Timeout de 5 segundos: silêncio da Groq conta como `down`.
- Whisper, Piper, sessão ativa e janela do prompt não entram no `/health`.
- O servidor escuta só em `127.0.0.1`. Porta `API_PORT`, default 8080. Ausência da variável não é erro; lixo ou `<= 0` aborta na subida.
- HTTP sobe no mesmo processo do loop de voz ou do `--text`, em paralelo, na ordem `load_settings()` → `start_api()` → fluxo escolhido. `start_api()` constrói, binda e ativa o `ThreadingHTTPServer` sincronamente; só `serve_forever()` roda na thread daemon. Portanto, falha de criação ou bind se propaga antes do retorno e impede que o fluxo escolhido e seu loop comecem sem HTTP. `init_brain()` continua dentro desse fluxo e antes do loop; se falhar, encerra processo/API e nenhuma entrada é processada. Não há modo “só API”. Encerrar o processo encerra o servidor.
- Sem autenticação: a porta não é publicada na rede da casa.
- Caminho que não existe: 404, sem listar as rotas.
- Falha no `/health` **não** mata o loop: 503 e o processo continua. Diferente da subida, que aborta se faltar credencial ou o banco estiver fora do ar no `init_brain`.

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/memoria-conversacional/regra-de-negocio.md` | Postgres inacessível na subida e no turno; sem checagem HTTP | Sem mudança de sessão/janela. `ping()` passa a existir para o healthcheck |
| `docs/memoria-conversacional/arquitetura.md` | `db.py` sem `ping` | `ping()` (`SELECT 1`) na fronteira do pacote |
| `docs/cerebro-llm/regra-de-negocio.md` | Falha da Groq só no turno | `ping_groq()` para o healthcheck (conexão/auth); o turno de `generate_reply` não muda |
| `docs/cerebro-llm/arquitetura.md` | Contratos sem ping | Ganha `ping_groq()` |
| `docs/chat-texto/arquitetura.md` | `--text` despacha diretamente para `run_text_chat()`, que chama `init_brain()` antes do loop | O fluxo passa por `load_settings()` e `start_api()` antes de `run_text_chat()`; `init_brain()` permanece como gate antes do loop |
| `docs/padroes-de-implementacao.md` | Pacotes sem `api` | Inclui `api`. Sem framework HTTP na stack |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| `GET /health` | HTTP em `127.0.0.1:API_PORT` | JSON 200 (ambos up) ou 503 | Cliente local (curl, probe) |
| Resultado de `ping()` | `src/memory/db.py` | `postgres: up` ou `down` | Corpo do `/health` |
| Resultado de `ping_groq()` | `src/agent/brain.py` (GET models, Bearer) | `groq: up` ou `down` | Corpo do `/health` |
| `API_PORT` | `.env` (opcional, default 8080) | Porta do `ThreadingHTTPServer` | `src/api/server.py` |
| `POSTGRES_*` / `DATABASE_URL` | `.env` (já existentes) | Mesma URL da memória | Engine; o healthcheck não monta URL própria |
| `GROQ_API_KEY` | `.env` (já existente) | Bearer do GET `/openai/v1/models` | Groq; o healthcheck não usa `GROQ_MODEL` |

## Exceções

- `API_PORT` não inteiro ou `<= 0`: `RuntimeError` na subida, citando a variável e o valor. O servidor e o loop não começam.
- Falha ao criar, bindar ou ativar o `ThreadingHTTPServer`: a exceção se propaga sincronamente por `start_api()`, nenhuma thread daemon é iniciada e o loop não começa.
- Postgres inacessível no `GET /health`: `postgres: "down"`, HTTP 503 se a Groq não compensar (e mesmo se a Groq estiver up). Processo e loop **continuam**.
- Groq inacessível, timeout ou HTTP não-2xx no `GET /health`: `groq: "down"`, HTTP 503 se o Postgres não compensar (e mesmo se o Postgres estiver up). Processo e loop **continuam**.
- Caminho desconhecido: 404 JSON `{"status": "not_found"}`.
- Credenciais Postgres ou Groq ausentes: o processo já aborta em `load_settings()`, antes de ligar o HTTP — o healthcheck nem chega a escutar.
- Revisão Alembic defasada durante `init_brain()`: embora `start_api()` já tenha iniciado a thread daemon, a exceção aborta o processo e a API antes de o loop começar. Defasagem surgida após uma inicialização válida não é reavaliada por `ping()`.

## Fora de escopo

- Demais endpoints.
- Framework HTTP (FastAPI, Flask, uvicorn).
- Auth, TLS, CORS, OpenAPI.
- Checar STT, TTS ou esquema Alembic no `/health`; a revisão continua validada de forma fail-closed na inicialização, não pelo `ping()` sob demanda.
- Checar se `GROQ_MODEL` existe; `ChatGroq.invoke` no healthcheck.
- Expor a porta fora de localhost.
- Processo HTTP separado do loop.
- Alterar o healthcheck do serviço Postgres no Compose.
