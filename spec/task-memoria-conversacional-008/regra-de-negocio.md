# Regra de negócio — Memória conversacional

## Objetivo

O Jarvis passa a lembrar do que foi dito. Cada fala da pessoa e cada resposta do robô são gravadas em Postgres, agrupadas por sessão, e o histórico da sessão ativa acompanha o prompt em toda chamada à LLM. A pessoa pode dizer "meu nome é Gabriel" e, dois turnos depois, perguntar "qual é o meu nome?".

A sessão é a unidade de conversa: nasce na primeira fala e morre por inatividade.

## Comportamento

### Sessão

- Existe no máximo uma sessão ativa. Ativa é a sessão sem encerramento cuja última atividade foi há menos que o **tempo de expiração**, configurado em `SESSION_IDLE_MINUTES` e valendo **10 minutos** quando a variável não é informada.
- A sessão nasce da **primeira fala da pessoa**, não da subida do processo. Ligar o Jarvis e não falar nada não cria sessão.
- Cada fala da pessoa renova a última atividade da sessão. A resposta do Jarvis não renova: quem mantém a conversa viva é a pessoa.
- Sessão aberta e ociosa além do tempo de expiração é encerrada quando a próxima fala procura por sessão ativa, com o encerramento datado na última atividade real — não no momento em que foi descoberta. Não há job periódico nem processo de fundo.
- Mudar `SESSION_IDLE_MINUTES` não reabre sessão já encerrada nem encerra sessão já aberta: o novo valor vale a partir da próxima resolução.
- `sair`, `quit` ou `exit` no modo `--text` encerram a sessão ativa antes de o processo terminar. Ctrl+C e EOF não encerram: a sessão fica aberta e expira sozinha.
- Reiniciar o processo não encerra a sessão. Se a pessoa voltar dentro do tempo de expiração, a conversa continua de onde parou, inclusive depois de um reboot do robô.
- Voz e chat texto compartilham a sessão. O que foi dito por voz aparece no histórico do modo texto e vice-versa; o canal de entrada não separa a conversa.

### Mensagens

- Toda fala da pessoa e toda resposta do Jarvis são gravadas **no instante em que acontecem**, com papel (`user` ou `assistant`), ordem dentro da sessão e idioma. Nada espera o fim da sessão para ser salvo.
- A fala da pessoa é gravada e **comitada antes** de a LLM ser chamada. Se a chamada falhar, a fala permanece registrada sem resposta correspondente; nenhum texto de desculpa ou placeholder é gravado no lugar da resposta que não veio.
- Mensagem gravada não é editada. Um turno já dito é registro histórico.
- O que vai para o banco é o conteúdo cru: a transcrição do Whisper ou a linha digitada, sem os delimitadores do prompt.

### Janela enviada à LLM

- O prompt deixa de ser uma fala solta e passa a ser: as instruções do Jarvis, o histórico da sessão ativa e a fala atual no fim.
- As instruções de `src/agent/instructions.md` entram **inteiras em toda chamada** e nunca são cortadas pelo limite da janela. Identidade, recusas e guardrails valem igual no turno 1 e no turno 40.
- A janela é limitada a **40 mensagens** e cerca de **8.000 caracteres**. O que passa disso fica no banco, mas não vai para a LLM.
- Ao cortar, o corte avança até a próxima fala da pessoa. A janela nunca começa numa resposta do Jarvis sem a pergunta que a originou.
- Toda fala da pessoa reidratada do banco volta ao prompt **dentro do envelope `<<<` `>>>`**, igual à fala atual. Uma ordem embutida numa frase dita dez turnos atrás continua sendo dado, não instrução: o guardrail que vale no primeiro turno vale no histórico.
- Nenhuma tool, RAG ou busca por similaridade entra no caminho. O histórico é carregado por consulta direta à sessão ativa; a LLM não consulta o banco.

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/cerebro-llm/regra-de-negocio.md` | "Cada fala é um turno isolado: nenhuma tool, RAG, memória vetorial ou histórico entra no caminho" | "O histórico da sessão ativa entra no prompt; tool, RAG e memória vetorial continuam fora" |
| `docs/cerebro-llm/regra-de-negocio.md` | Fora de escopo lista "Histórico multi-turno" | Sai de Fora de escopo; tools, function calling e RAG permanecem |
| `docs/cerebro-llm/regra-de-negocio.md` | Exceções cobrem falta de credencial, `instructions.md` inválido e falha da Groq | Ganha credencial do Postgres ausente, banco inacessível e migração pendente na subida, mais falha do Postgres durante o turno |
| `docs/chat-texto/regra-de-negocio.md` | "Cada linha é um turno isolado: sem histórico entre linhas" | "Cada linha entra na sessão ativa e enxerga as anteriores" |
| `docs/chat-texto/regra-de-negocio.md` | "Encerrar: `sair`, `quit`, `exit` ou Ctrl+C" | Igual, mas `sair` / `quit` / `exit` também encerram a sessão; Ctrl+C não |
| `docs/chat-texto/regra-de-negocio.md` | Fora de escopo lista "Histórico, tools, RAG, Postgres" | Fora de escopo perde histórico e Postgres; mantém tools e RAG |
| `docs/padroes-de-implementacao.md` | Decisão "Cérebro sem tools, RAG ou memória" | A decisão passa a cobrir só tools e RAG; memória vira etapa entregue |
| `docs/padroes-de-implementacao.md` | Stack: "Banco vetorial — Postgres" | Postgres passa a ser também o armazenamento de sessões e mensagens, acessado por SQLAlchemy ORM com migrações Alembic |
| `docs/padroes-de-implementacao.md` | Comandos: instalar, rodar, `compileall`, `unittest` | Ganham `alembic upgrade head` e `alembic revision --autogenerate` |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Frase depois da wake word | STT (Whisper) | Mensagem `user` gravada | Postgres (`messages`) |
| Linha digitada (modo `--text`) | stdin | Mensagem `user` gravada | Postgres (`messages`) |
| Resposta da LLM | Groq | Mensagem `assistant` gravada | Postgres (`messages`) |
| Sessão ativa e histórico | Postgres (`sessions`, `messages`) | Lista de mensagens do prompt | LLM na Groq |
| Idioma (`pt` / `en`) | Whisper (voz) ou `--lang` (texto) | Idioma da mensagem e da sessão | Postgres e prompt |
| `sair` / `quit` / `exit` | stdin | Encerramento da sessão | Postgres (`sessions.ended_at`) |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `.env` (obrigatórias) | Credenciais do contêiner **e** da conexão da aplicação | Docker Compose e `src/memory/db.py` |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `.env` (opcionais: `localhost`, `5432`) | Endereço da conexão e porta publicada pelo contêiner | Docker Compose e `src/memory/db.py` |
| `DATABASE_URL` | `.env` (opcional) | URL completa que substitui as variáveis acima | `src/memory/db.py` |
| `SESSION_IDLE_MINUTES` | `.env` (opcional, default 10) | Corte de inatividade da consulta de sessão ativa | `resolve_session` |
| `docker-compose.yml` | Raiz do repositório | Contêiner do Postgres com volume nomeado | Docker, na máquina de desenvolvimento |

## Exceções

- `POSTGRES_USER`, `POSTGRES_PASSWORD` ou `POSTGRES_DB` ausente ou vazia: `RuntimeError` na subida, com instrução de copiar `.env.example`. O loop não começa e a LLM não é chamada — mesmo tratamento fail-closed de `GROQ_API_KEY` e `GROQ_MODEL`.
- Mesma variável ausente no `docker compose up`: o Compose aborta antes de criar o contêiner, com a mensagem da própria variável. O banco nunca sobe com senha em branco.
- `POSTGRES_PORT` com valor não inteiro ou menor ou igual a zero: `RuntimeError` na subida. Ausente cai em 5432.
- Postgres inacessível na subida: `RuntimeError` antes do loop, com o erro de conexão. O caso comum é o contêiner não ter subido; o README documenta `docker compose up -d --wait`.
- `SESSION_IDLE_MINUTES` com valor não inteiro ou menor ou igual a zero: `RuntimeError` na subida, citando a variável e o valor recebido. Ausente ou vazia **não** é erro: cai no default de 10 minutos. A diferença em relação a `GROQ_API_KEY` é que existe um default seguro para um tempo de expiração e não existe para uma credencial.
- Esquema desatualizado na subida: se a revisão aplicada no banco for diferente da última migração do repositório, `RuntimeError` instruindo a rodar `alembic upgrade head`. O programa nunca migra sozinho — banco de robô em campo não é lugar para alteração de esquema automática e silenciosa.
- Falha do Postgres durante um turno: mensagem no terminal, o rosto volta a Sleeping, nada é falado e o loop aguarda a wake word de novo. É o mesmo tratamento que a falha da Groq já recebe. Não há operação em memória sem banco: sem persistência, não há conversa.
- Falha da LLM depois da fala gravada: a mensagem da pessoa fica no banco sem resposta. O turno seguinte carrega essa fala como parte do histórico, o que é fiel ao que aconteceu.
- Sessão ativa não encontrada: não é erro. A fala abre uma sessão nova.

## Fora de escopo

- Tools, function calling e qualquer consulta ao banco feita pela LLM. A frase da pessoa nunca vira SQL.
- RAG, embeddings e pgvector.
- Tabela de fatos de longo prazo — rostos, gostos, preferências, dados da casa. Esse conhecimento sobrevive à sessão, não tem ordem e é recuperado por similaridade: é uma tabela própria, na task do RAG, e não pertence a `messages`. Misturar as duas coisas faria o RAG futuro recuperar pedaço de diálogo em vez de fato consolidado.
- Sumarização progressiva do histórico e resumo da sessão.
- Aplicação automática de migração na subida. O programa verifica e aborta; quem migra é a pessoa.
- Subir o contêiner pelo programa. O `docker compose up -d` é passo manual, documentado no README.
- Compose de produção, empacotar o Jarvis em contêiner, `systemd` ou senha por segredo. O `docker-compose.yml` é de desenvolvimento local.
- Tetos da janela configuráveis por variável de ambiente. Só o tempo de expiração é configurável.
- Identificação de quem está falando. `sessions` não tem dono; o robô assume uma pessoa.
- Retenção, expurgo ou consulta histórica de sessões encerradas.
- Sessão separada por canal de entrada.
- Mudança de provedor da LLM, de `instructions.md` ou de guardrails.
