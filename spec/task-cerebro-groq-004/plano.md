# Spec: Cérebro LLM via Groq

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 6/6 etapas

## Descrição breve da tarefa

O cérebro deixa de chamar Hugging Face Inference (`HuggingFaceEndpoint`) e passa a usar modelos da Groq via LangChain (`ChatGroq`). Chave e id do modelo vêm do `.env`. Instruções em `instructions.md`, delimitadores anti-injection, ausência de tools e o loop de voz permanecem iguais.

## Requisitos funcionais

- RF1: A invocação da LLM no cérebro usa Groq (`langchain-groq` / `ChatGroq`), não `HuggingFaceEndpoint` nem `langchain-huggingface`.
- RF2: Credenciais e modelo vêm de `.env`: `GROQ_API_KEY` e `GROQ_MODEL`. Sem chave ou sem modelo, `RuntimeError` na subida (mesmo padrão de fail-closed de `load_settings`), com instrução de copiar `.env.example`.
- RF3: `.env.example` documenta `GROQ_API_KEY` (link para o console Groq) e um `GROQ_MODEL` padrão de produção. Não commitar `.env`.
- RF4: `generate_reply(text, language)` e `init_brain()` mantêm o contrato. O prompt continua sendo o markdown + fala delimitada (`<<<` / `>>>`). Sem tools, RAG ou agentes.
- RF5: A resposta falada é só o texto da mensagem (`AIMessage.content`), sem `reasoning_content` nem representação crua do objeto LangChain.
- RF6: `requirements.txt` troca `langchain-huggingface` por `langchain-groq`. `langchain-core` permanece.
- RF7: Testes de settings e do cérebro passam a Groq (`GROQ_*`, mock de `ChatGroq`). Sem chamada de rede.
- RF8: A stack obrigatória das skills spec/rock-it e de `docs/spec/` deixa de exigir Hugging Face **como provedor da LLM**. Groq é o cérebro. Artefatos de STT/TTS (Whisper, vozes Piper) podem continuar vindo do Hub; isso não é o cérebro.

## Implementação técnica

### Etapa 1 — `.env.example` e `settings.py` [Concluído]

- Substituir `HF_TOKEN` / `HF_MODEL` / `HUGGINGFACEHUB_API_TOKEN` por `GROQ_API_KEY` e `GROQ_MODEL`.
- Mensagens de erro citam as chaves novas e pedem copiar `.env.example`.
- `os.environ.setdefault("GROQ_API_KEY", token)` para o cliente LangChain ler a chave.
- `.env.example`: comentário com https://console.groq.com/keys ; modelo padrão `openai/gpt-oss-20b` (produção Groq, sucessor do Llama 3.1 8B Instant no plano gratuito; rápido, adequado a respostas curtas). O valor continua configurável.
- Não ler nem aceitar `HF_TOKEN` / `HF_MODEL` como fallback.

### Etapa 2 — `brain.py` com `ChatGroq` [Concluído]

- Trocar o import e o tipo de `_llm` para `ChatGroq` (`from langchain_groq import ChatGroq`).
- Em `init_brain()`: `ChatGroq(model=_settings.model, api_key=_settings.token, temperature=0.7, max_tokens=128)`. Sem tools.
- Manter `_read_instructions`, `_build_prompt`, `_language_name` e o fluxo `if _llm is None: init_brain()`.
- Em `generate_reply`: `raw = _llm.invoke(prompt)`; se `raw` tiver `.content`, usar esse valor (string); senão `str(raw)`. `strip()` no final. Não interpolar a fala com `PromptTemplate`.
- Não usar `groq/compound` nem function calling.

### Etapa 3 — `requirements.txt` [Concluído]

Remover `langchain-huggingface` (todas as linhas). Incluir `langchain-groq`. Manter `langchain-core`. Sem outras mudanças de dependência.

### Etapa 4 — testes [Concluído]

- `tests/test_settings.py`: ausente `GROQ_API_KEY` / `GROQ_MODEL` → `RuntimeError` com o nome da chave; carga válida devolve `Settings`.
- `tests/test_brain.py`: patch `ChatGroq` (não `HuggingFaceEndpoint`) no teste de arquivo ausente/vazio. Demais testes de prompt/delimitadores/guardrails permanecem.
- Sem teste de integração com a API Groq.

### Etapa 5 — stack spec / rock-it / docs/spec [Concluído]

Atualizar a linha de stack para o cérebro ser Groq, sem deixar o rock-it bloqueado pela regra antiga de Hugging Face:

- `.cursor/skills/spec/SKILL.md`: “Modelos de IA da Groq (cérebro, via LangChain). Artefatos de voz (Whisper, Piper) podem vir do Hugging Face Hub.”
- `.cursor/skills/rock-it/SKILL.md` e personas `dev-implementador.md` / `dev-reviewer.md`: mesma regra.
- `.cursor/skills/spec/reference.md`: dependência da LLM = Groq (`GROQ_MODEL`).
- `docs/spec/arquitetura.md` e `docs/spec/padroes-de-implementacao.md`: LLM = Groq; Hub só para artefatos STT/TTS, não para o cérebro.

Não reescrever as skills além desse alinhamento de stack.

### Etapa 6 — documentação [Concluído]

Atualizar README (árvore, Como rodar, dependências: `GROQ_API_KEY` / `GROQ_MODEL`, token em console.groq.com) e `docs/progresso.md`. Criar regra, arquitetura e padrões em `spec/task-cerebro-groq-004/`. Não migrar `docs/cerebro-llm/`.

## Casos de teste (Gherkin)

Feature: cérebro via Groq
  Scenario: subida sem chave Groq
    Given `GROQ_API_KEY` ausente ou em branco
    When `load_settings` / `init_brain` roda
    Then ocorre `RuntimeError` citando `GROQ_API_KEY`
    And a Groq não é chamada

  Scenario: subida sem modelo
    Given `GROQ_MODEL` ausente ou em branco
    When `load_settings` roda
    Then ocorre `RuntimeError` citando `GROQ_MODEL`

  Scenario: resposta a partir do ChatGroq
    Given chave e modelo válidos em memória e a LLM mockada
    When `generate_reply` é chamado
    Then o cliente é `ChatGroq` com o modelo do `.env`
    And o texto falado é o `content` da mensagem
    And o prompt ainda inclui `instructions.md` e a fala entre `<<<` e `>>>`

## Cobertura com testes unitários e integração

Necessário: as chaves e o cliente mudam; os testes atuais quebram se não forem atualizados. Unitários com mock cobrem fail-closed e o `content` da mensagem. Sem integração com a API Groq.

## Fora de escopo / não coberto

- Manter Hugging Face como provedor alternativo da LLM ou ler `HF_TOKEN` / `HF_MODEL`.
- Tools, `groq/compound`, function calling, streaming, RAG, Postgres.
- Trocar Whisper ou o download das vozes Piper (continuam no Hub).
- Alterar `instructions.md` ou o loop `listen_repeat.py`.
- Migrar `docs/cerebro-llm/`.
- Commitar `.env` ou a chave real.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md
- [x] docs/progresso.md
- [x] spec/task-cerebro-groq-004/regra-de-negocio.md
- [x] spec/task-cerebro-groq-004/arquitetura.md
- [x] spec/task-cerebro-groq-004/padroes-de-implementacao.md
