# Regra de negócio — Raciocínio da Groq no chat texto

## Objetivo

Quem exerce o Jarvis no modo `--text` passa a conseguir **ler** o raciocínio interno que a Groq já devolve. Esse raciocínio também fica gravado em Postgres, ligado 1:1 à mensagem `assistant` que ele produziu. A resposta falável continua sendo o único texto enviado ao Piper, gravado em `messages.content` e impresso na linha `Jarvis [lang]:`.

## Comportamento

- A Groq é pedida com `include_reasoning=True`. O modelo `openai/gpt-oss-20b` coloca o raciocínio em `message.reasoning` (LangChain: `additional_kwargs["reasoning_content"]`), separado do `content`.
- `generate_reply` devolve os dois campos: `spoken` (content) e `reasoning` (ou `None`).
- Modo `--text`: se houver raciocínio, imprime `Raciocínio:` e o texto interno, depois a linha do Jarvis com `spoken`. Sem raciocínio, o terminal fica como hoje.
- Modo voz: Piper e a linha `Jarvis [lang]:` usam só `spoken`. O raciocínio não é falado nem impresso.
- `messages.content` da assistant é só `spoken`. O raciocínio vai para a tabela `reasonings`, com `message_id` único apontando para essa mensagem. Não existe linha de raciocínio para fala `user`. Se a Groq não mandar raciocínio, a assistant é gravada sem linha em `reasonings`.
- A janela enviada à LLM lê só `messages`. O raciocínio persistido não volta no prompt.
- A fala da pessoa continua comitada **antes** da LLM. Se o invoke falhar, não há assistant nem `reasonings`.
- A assistant e o eventual `reasonings` entram no mesmo commit.
- `instructions.md` não muda: a resposta ao usuário continua no máximo duas frases.
- `max_tokens=1024` para o raciocínio não esgotar o orçamento que hoje é 128.

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/cerebro-llm/regra-de-negocio.md` | O que é falado é só o conteúdo, sem raciocínio interno | Permanece para TTS e `spoken`. O raciocínio é extraído, mostrado no `--text` e gravado em `reasonings` |
| `docs/chat-texto/regra-de-negocio.md` | A resposta é só impressa | Imprime raciocínio (quando a Groq mandar) e a resposta |
| `docs/memoria-conversacional/regra-de-negocio.md` | Duas tabelas; `assistant` é o texto da LLM | Três tabelas; `reasonings` 1:1 opcional com a mensagem assistant; janela inalterada |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| `AIMessage.content` | Groq / LangChain | `Reply.spoken` | TTS, stdout `Jarvis [lang]:`, Postgres `messages` (assistant) |
| `additional_kwargs["reasoning_content"]` | Groq `message.reasoning` via LangChain | `Reply.reasoning` | stdout do `--text`; Postgres `reasonings` (se houver) |
| Linha digitada | stdin | Pedido ao cérebro | `generate_reply` |
| Fala `user` | voz ou `--text` | Mensagem `user` | Postgres `messages` (sem `reasonings`) |

## Exceções

- Raciocínio ausente, `None` ou só espaços: `Reply.reasoning` é `None`; o chat texto não imprime o bloco; não há insert em `reasonings`.
- `append_message` com `reasoning` em papel que não é `assistant`: `RuntimeError`.
- Falha da Groq: igual ao hoje — erro no terminal, sem gravar `assistant` nem `reasonings`, loop segue.
- Demais falhas de credencial, `instructions.md`, esquema Alembic e Postgres: inalteradas. Esquema sem a `0002` aborta na subida como qualquer revisão defasada.

## Fora de escopo

- Coluna de raciocínio em `messages`.
- Linha em `reasonings` para mensagem `user`.
- API para consultar raciocínios antigos.
- Configuração por `.env` de `include_reasoning`, `reasoning_effort` ou `max_tokens`.
- `reasoning_format` (não suportado no GPT-OSS).
- Exibir raciocínio na voz.
- Tools, RAG, mudança de guardrails.
