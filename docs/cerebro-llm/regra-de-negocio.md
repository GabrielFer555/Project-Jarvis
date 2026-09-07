# Regra de negócio — Cérebro LLM

## Objetivo

Depois da wake word **Jarvis**, o robô deixa de repetir a frase. A transcrição vai para uma LLM na **Groq** (via LangChain), que estrutura uma resposta breve; o Piper fala essa resposta em voz alta. A mesma LLM também aceita texto digitado no modo `--text`; nesse canal a resposta falável e, se houver, o raciocínio interno são impressos no terminal, sem TTS.

## Comportamento

- O microfone e a wake word continuam iguais: `Jarvis …` numa frase só, ou `Jarvis` e a pergunta em seguida.
- A LLM recebe o texto da pessoa e o idioma: na voz, a transcrição do Whisper e o idioma detectado; no modo `--text`, a linha digitada e o `--lang`. Responde em no máximo duas frases, no mesmo idioma, prontas para TTS (na voz) ou para o terminal (no modo texto).
- Identidade, tom, limites e recusas vivem em `src/agent/instructions.md`, não em string no Python. Mudar o comportamento do Jarvis é editar esse markdown.
- A fala da pessoa entra no prompt como **dado**, entre `<<<` e `>>>`. Ordem embutida na fala não sobrepõe as instruções, não revela o prompt e não troca o papel do assistente.
- Pedido ilegal, de crime, pornografia ou ameaça recebe recusa curta, no idioma da pessoa, sem detalhar o que foi pedido.
- O histórico da sessão ativa entra no prompt; nenhuma tool, RAG ou memória vetorial entra no caminho.
- A chave e o modelo vêm de `.env` (`GROQ_API_KEY`, `GROQ_MODEL`). Sem chave ou sem modelo, o programa não inicia o loop.
- O `GET /health` usa `ping_groq()` para validar conexão e autenticação com a mesma `GROQ_API_KEY`, por GET em `/openai/v1/models`. Essa checagem não chama `ChatGroq.invoke`, não gasta completion, não verifica `GROQ_MODEL` e não altera o turno de `generate_reply`.
- O que é falado (Piper e `Reply.spoken`) é só o conteúdo da mensagem da LLM (`AIMessage.content`), sem raciocínio interno nem a representação crua do objeto LangChain. O raciocínio, quando a Groq manda, é extraído de `additional_kwargs["reasoning_content"]`, visível no `--text` e gravado em `reasonings`; não entra no texto falado nem na janela do prompt.
- Se a chamada à LLM falhar, o erro vai para o terminal; o rosto volta a Sleeping e o robô espera **Jarvis** de novo, sem falar.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Frase depois da wake word | STT (Whisper) | `Reply.spoken` | TTS (Piper) |
| Linha digitada (modo `--text`) | stdin | `Reply.spoken` e, se houver, `Reply.reasoning` | stdout (sem Piper); bloco `Raciocínio:` antes da linha do Jarvis |
| `AIMessage.content` | Groq / LangChain | `Reply.spoken` | TTS, stdout `Jarvis [lang]:`, Postgres `messages` (assistant) |
| `additional_kwargs["reasoning_content"]` | Groq via LangChain | `Reply.reasoning` | stdout do `--text`; Postgres `reasonings` (se houver) |
| Idioma (`pt` / `en`) | Whisper (voz) ou `--lang` (texto) | Voz correspondente (voz) ou `{language_name}` no prompt (texto) | Piper (voz) ou `generate_reply` (texto) |
| Identidade e guardrails | `src/agent/instructions.md` | `SystemMessage` do prompt | LLM na Groq |
| Histórico da sessão ativa | Postgres (`src/memory/`) | Lista de mensagens (`HumanMessage` / `AIMessage`) | LLM na Groq |
| `GROQ_API_KEY`, `GROQ_MODEL` | `.env` | Cliente `ChatGroq` | API da Groq |
| `GET /health` | API local | `ping_groq()` com Bearer e timeout de 5 segundos | Estado `groq: "up"` ou `"down"` |

## Exceções

- `GROQ_API_KEY` ou `GROQ_MODEL` ausentes: `RuntimeError` na subida, com instrução de copiar `.env.example`.
- `POSTGRES_USER`, `POSTGRES_PASSWORD` ou `POSTGRES_DB` ausentes: `RuntimeError` na subida, mesmo com `DATABASE_URL`.
- Postgres inacessível na subida: `RuntimeError("Postgres inacessível: …")`. Esquema diferente da `head` do repositório: `RuntimeError` instruindo `alembic upgrade head`.
- `instructions.md` ausente, vazio ou só com espaços: `RuntimeError` com o caminho do arquivo; a LLM não é chamada.
- Falha de rede ou da Groq: mensagem no terminal, estado do rosto volta a Sleeping, loop segue.
- Falha, timeout ou HTTP não-2xx no ping da Groq: o healthcheck responde `groq: "down"` sem expor a chave nem o erro bruto; a conversa continua disponível para novos turnos.
- Falha do Postgres durante um turno: o mesmo tratamento — mensagem no terminal, rosto volta a Sleeping, nada é falado, o loop continua. A fala já comitada permanece no banco sem resposta se a falha ocorrer depois do commit e antes (ou durante) a LLM.
- Raciocínio ausente, `None` ou só espaços: `Reply.reasoning` é `None`; o `--text` não imprime o bloco; a assistant é gravada sem linha em `reasonings`.

## Fora de escopo

- Tools, agentes com function calling, RAG.
- Escolha automática de modelo além do valor em `.env`.
