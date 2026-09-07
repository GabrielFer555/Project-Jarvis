# Regra de negócio — Memória conversacional

## Objetivo

O Jarvis lembra do que foi dito na conversa em andamento. Cada fala da pessoa e cada resposta do robô são gravadas em Postgres, agrupadas por sessão, e o histórico da sessão ativa acompanha o prompt em toda chamada à LLM. A pessoa pode dizer "meu nome é Gabriel" e, dois turnos depois, perguntar "qual é o meu nome?".

A sessão é a unidade de conversa: nasce na primeira fala e morre por inatividade ou pelo encerramento manual no chat texto.

## Comportamento

### Sessão

- Existe no máximo uma sessão ativa. Ativa é a sessão sem encerramento cuja última atividade foi há menos que o **tempo de expiração**, configurado em `SESSION_IDLE_MINUTES` e valendo **10 minutos** quando a variável não é informada.
- A sessão nasce da **primeira fala da pessoa**, não da subida do processo. Ligar o Jarvis e não falar nada não cria sessão.
- Cada fala da pessoa renova a última atividade da sessão. A resposta do Jarvis não renova: quem mantém a conversa viva é a pessoa.
- Sessão aberta e ociosa além do tempo de expiração é encerrada quando a próxima fala procura por sessão ativa (`resolve_session`), com o encerramento datado na última atividade real — não no momento em que foi descoberta. Não há job periódico nem processo de fundo.
- Mudar `SESSION_IDLE_MINUTES` não reabre sessão já encerrada nem encerra sessão já aberta: o novo valor vale a partir da próxima resolução.
- `sair`, `quit` ou `exit` no modo `--text` localizam a sessão ativa com `get_active_session()` — **sem criar sessão**. Se existir (inclusive a aberta pela voz), encerram (`close_session`); se não, no-op. Ctrl+C e EOF não encerram: a sessão fica aberta e expira sozinha.
- Reiniciar o processo não encerra a sessão. Se a pessoa voltar dentro do tempo de expiração, a conversa continua de onde parou.
- Voz e chat texto compartilham a sessão. O canal de entrada não separa a conversa.

### Mensagens

- Toda fala da pessoa e toda resposta do Jarvis são gravadas **no instante em que acontecem**, com papel (`user` ou `assistant`), ordem dentro da sessão e idioma.
- A fala da pessoa é gravada e **comitada antes** de a LLM ser chamada. Se a chamada falhar, a fala permanece registrada sem resposta correspondente; nenhum placeholder é gravado no lugar da resposta que não veio; também não nasce linha em `reasonings`.
- A mensagem `assistant` em `messages.content` é só o texto falável (`spoken`). O raciocínio da Groq, quando existir, vai para a tabela `reasonings`, 1:1 com essa mensagem via `message_id` único. Fala `user` nunca tem linha em `reasonings`. Se a Groq não mandar raciocínio, a assistant é gravada sem linha nessa tabela.
- A assistant e o eventual `reasonings` entram no **mesmo commit**.
- Mensagem gravada não é editada. Um turno já dito é registro histórico.
- O que vai para o banco em `messages` é o conteúdo cru: a transcrição do Whisper, a linha digitada ou o `spoken` da LLM, sem os delimitadores do prompt.

### Janela enviada à LLM

- O prompt é: as instruções do Jarvis, o histórico da sessão ativa e a fala atual no fim.
- As instruções de `src/agent/instructions.md` entram **inteiras em toda chamada** e nunca são cortadas pelo limite da janela.
- A janela é limitada a **40 mensagens** e cerca de **8.000 caracteres**. O que passa disso fica no banco, mas não vai para a LLM.
- Ao cortar, o corte avança até a próxima fala da pessoa. A janela nunca começa numa resposta do Jarvis sem a pergunta que a originou.
- Toda fala da pessoa reidratada do banco volta ao prompt **dentro do envelope `<<<` `>>>`**, igual à fala atual.
- `load_window` lê só `(role, content)` de `messages`. A tabela `reasonings` **não** entra no join nem no prompt: o raciocínio persistido não volta para a LLM no turno seguinte.
- Nenhuma tool, RAG ou busca por similaridade entra no caminho. O histórico é carregado por consulta direta à sessão ativa; a LLM não consulta o banco.

### Healthcheck de conexão

- `ping()` executa somente `SELECT 1` pela mesma engine da memória para informar o estado do Postgres ao `GET /health`.
- Essa checagem sob demanda não chama `assert_schema_up_to_date` nem compara revisões Alembic. A validação de esquema continua fail-closed na inicialização.
- O ping não cria sessão, não lê nem grava mensagens e não altera as regras de expiração ou da janela.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Frase depois da wake word | STT (Whisper) | Mensagem `user` gravada | Postgres (`messages`) |
| Linha digitada (modo `--text`) | stdin | Mensagem `user` gravada | Postgres (`messages`) |
| Resposta da LLM | Groq | Mensagem `assistant` gravada (`spoken`) | Postgres (`messages`) |
| Raciocínio da LLM (se houver) | Groq | Linha 1:1 com a mensagem `assistant` | Postgres (`reasonings`) |
| Sessão ativa e histórico | Postgres (`sessions`, `messages`) | Lista de mensagens do prompt (sem `reasonings`) | LLM na Groq |
| Idioma (`pt` / `en`) | Whisper (voz) ou `--lang` (texto) | Idioma da mensagem e da sessão | Postgres e prompt |
| `sair` / `quit` / `exit` | stdin | `get_active_session()` → se UUID, `close_session`; senão no-op | Postgres (`sessions.ended_at`) |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `.env` (obrigatórias, mesmo com `DATABASE_URL`) | Credenciais do contêiner **e** da aplicação | Docker Compose e `src/memory/db.py` |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `.env` (opcionais: `127.0.0.1`, `5432`) | Endereço da conexão e porta publicada pelo contêiner | Docker Compose e `src/memory/db.py` |
| `DATABASE_URL` | `.env` (opcional) | URL usada na montagem da conexão; não dispensa as `POSTGRES_*` obrigatórias | `src/memory/db.py` |
| `SESSION_IDLE_MINUTES` | `.env` (opcional, default 10) | Corte de inatividade da consulta de sessão ativa | `resolve_session` / `get_active_session` |
| `docker-compose.yml` | Raiz do repositório | Contêiner do Postgres com volume nomeado | Docker, na máquina de desenvolvimento |
| `GET /health` | API local | `ping()` com `SELECT 1` | Estado `postgres: "up"` ou `"down"` |

## Exceções

- `POSTGRES_USER`, `POSTGRES_PASSWORD` ou `POSTGRES_DB` ausente ou vazia: `RuntimeError` na subida, com instrução de copiar `.env.example`. O loop não começa e a LLM não é chamada — mesmo com `DATABASE_URL` preenchida.
- Mesma variável ausente no `docker compose up`: o Compose aborta antes de criar o contêiner, com a mensagem da própria variável.
- `POSTGRES_PORT` com valor não inteiro ou menor ou igual a zero: `RuntimeError` na subida. Ausente cai em 5432.
- Postgres inacessível na subida: `assert_schema_up_to_date` captura `OperationalError` e relança `RuntimeError("Postgres inacessível: …")`. O caso comum é o contêiner não ter subido; o README documenta `docker compose up -d --wait`.
- Postgres inacessível no healthcheck: `ping()` falha e a API responde `postgres: "down"` sem expor a exceção; o loop continua.
- `SESSION_IDLE_MINUTES` com valor não inteiro ou menor ou igual a zero: `RuntimeError` na subida, citando a variável e o valor recebido. Ausente ou vazia **não** é erro: cai no default de 10 minutos.
- Esquema desatualizado na subida: se a revisão aplicada no banco for diferente da última migração do repositório, `RuntimeError` instruindo a rodar `alembic upgrade head`. O programa nunca migra sozinho.
- Falha do Postgres durante um turno: mensagem no terminal, o rosto volta a Sleeping, nada é falado e o loop aguarda a wake word de novo. É o mesmo tratamento que a falha da Groq já recebe. Sem persistência, não há conversa.
- Falha da LLM depois da fala gravada: a mensagem da pessoa fica no banco sem resposta e sem linha em `reasonings`. O turno seguinte carrega essa fala como parte do histórico.
- `append_message` com `reasoning` preenchido e papel que não é `assistant`: `RuntimeError` (a fala da pessoa não tem raciocínio da LLM).
- Sessão ativa não encontrada: não é erro. A fala abre uma sessão nova (`resolve_session`). `get_active_session` devolve `None` e o `sair` não cria sessão.

## Fora de escopo

- Tools, function calling e qualquer consulta ao banco feita pela LLM.
- RAG, embeddings e pgvector.
- Memoização de fatos de longo prazo (rostos, gostos, preferências, dados da casa).
- Sumarização progressiva do histórico e resumo da sessão.
- Aplicação automática de migração na subida.
- Subir o contêiner pelo programa. O `docker compose up -d` é passo manual, documentado no README.
- Compose de produção, empacotar o Jarvis em contêiner, `systemd` ou senha por segredo.
- Tetos da janela configuráveis por variável de ambiente.
- Identificação de quem está falando. `sessions` não tem dono.
- Retenção, expurgo ou consulta histórica de sessões encerradas.
- Sessão separada por canal de entrada.
- Mudança de provedor da LLM, de `instructions.md` ou de guardrails.
