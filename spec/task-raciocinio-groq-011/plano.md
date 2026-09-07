# Spec: Raciocínio da Groq visível no chat texto e persistido

## Cabeçalho

- **Branch base:** feat/created-memory
- **Modo de execução:** non stop
- **Progresso:** 5/5 etapas

## Descrição breve da tarefa

O modelo `openai/gpt-oss-20b` já devolve raciocínio interno no campo `reasoning` da Groq. O cérebro descarta isso hoje: `generate_reply` devolve só `AIMessage.content`. Esta task pede o raciocínio à API, expõe-o num `Reply`, imprime-o no modo `--text`, e grava-o em Postgres na tabela `reasonings` (1:1 com a mensagem `assistant`). O Piper e a janela do prompt continuam vendo só o texto falável.

## Requisitos funcionais

- RF1: `ChatGroq` pede o raciocínio à Groq (`include_reasoning=True` via `model_kwargs`). Não envia `reasoning_format`: o modelo vigente (`openai/gpt-oss-20b`) não aceita esse parâmetro.
- RF2: `max_tokens` sobe de 128 para **1024**. O orçamento extra cobre tokens de raciocínio; a resposta falada continua limitada a duas frases por `instructions.md`.
- RF3: `generate_reply` devolve um `Reply` com `spoken` (texto de `AIMessage.content`, `strip()`) e `reasoning` (`additional_kwargs["reasoning_content"]` após `strip()`, ou `None` se ausente/vazio). O valor de `spoken` não inclui raciocínio nem `str` cru do `AIMessage`.
- RF4: A mensagem `assistant` em `messages.content` é só `spoken`. Existe a tabela `reasonings`, 1:1 com `messages` via `message_id` único. A linha de raciocínio nasce **somente** junto da mensagem `assistant` e **somente** quando `reasoning` não é `None`. Fala `user` nunca tem linha em `reasonings`.
- RF5: `load_window` continua devolvendo só `(role, content)` de `messages`. O raciocínio persistido **não** entra no prompt nem volta para a LLM no turno seguinte.
- RF6: No modo `--text`, se houver raciocínio, o terminal imprime um bloco `Raciocínio:` **antes** da linha `Jarvis [lang]: <spoken>`. Sem raciocínio, só a linha do Jarvis, como hoje.
- RF7: No loop de voz, o Piper fala só `spoken`. A linha `Jarvis [lang]:` do terminal de voz também mostra só `spoken`. O raciocínio não é falado nem impresso nesse canal.

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| Cérebro LLM | `docs/cerebro-llm/regra-de-negocio.md` | O que é falado é só o conteúdo da mensagem, sem raciocínio interno | TTS e `spoken` sem raciocínio. O raciocínio é extraído, mostrado no `--text` e gravado em `reasonings` |
| Cérebro LLM | `docs/cerebro-llm/arquitetura.md` | `generate_reply(...) -> str`; `max_tokens=128`; falar só `AIMessage.content` | `generate_reply(...) -> Reply`; `max_tokens=1024`; `include_reasoning`; `append_message` da assistant leva `reasoning` |
| Chat texto | `docs/chat-texto/regra-de-negocio.md` | A resposta é só impressa | Imprime raciocínio (quando houver) e depois a resposta falável |
| Chat texto | `docs/chat-texto/arquitetura.md` | `generate_reply` → `Jarvis [lang]: <resposta>` | Lê `Reply`; bloco `Raciocínio:` opcional antes da linha do Jarvis |
| Memória conversacional | `docs/memoria-conversacional/regra-de-negocio.md` | Só `sessions` e `messages`; resposta da LLM é o `content` assistant | Ganha `reasonings` 1:1 com a mensagem assistant; janela ignora essa tabela |
| Memória conversacional | `docs/memoria-conversacional/arquitetura.md` | Modelos `ChatSession` e `Message`; `append_message` só grava `Message` | Modelo `Reasoning`; migração nova; `append_message(..., *, reasoning=)` na mesma transação da assistant |

Nova funcionalidade: não; atualiza cérebro, chat texto e memória.

Não impactadas: `docs/api/`, `docs/rosto-do-robo/`, `docs/spec/`, `docs/padroes-de-implementacao.md`, `docs/README.md` (sem pasta nova). Voz (`src/voice/listen_repeat.py`) muda só o acesso a `.spoken`.

## Implementação técnica

### Etapa 1 — tabela `reasonings` e gravação [Concluído]

`src/memory/models.py`: entidade nova, no mesmo estilo de `Message` (FK sem `relationship()`):

```python
class Reasoning(Base):
    __tablename__ = "reasonings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        unique=True,
    )
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

Migração Alembic **nova** (`alembic revision --autogenerate`), revisão `20260907_0002`, `down_revision` = `20260907_0001`. Não editar a `0001`.

`src/memory/conversation.py`: `append_message` ganha argumento somente-nome `reasoning: str | None = None`.

- `reasoning is None`: comportamento atual (só `Message`).
- `reasoning` preenchido e `role == "assistant"`: na **mesma** `Session` e no mesmo `commit`, insere `Reasoning(message_id=..., content=reasoning)`.
- `reasoning` preenchido e `role != "assistant"`: `RuntimeError` (erro de programação; fala da pessoa não tem raciocínio da LLM).
- `load_window` **não** faz join com `reasonings`.

A fala `user` continua comitada **antes** do `invoke`, sem `reasoning`.

### Etapa 2 — contrato do cérebro [Concluído]

Em `src/agent/brain.py`:

- Dataclass congelada `Reply` com `spoken: str` e `reasoning: str | None = None`.
- `init_brain` monta `ChatGroq` com `max_tokens=1024` e `model_kwargs={"include_reasoning": True}`. Sem `reasoning_format`. Sem `reasoning_effort`.
- Depois do `invoke`, extrair `spoken` como hoje. Extrair `reasoning` de `additional_kwargs.get("reasoning_content")` somente se for `str` não vazia após `strip()`; senão `None`.
- `append_message(sid, "assistant", spoken, language, reasoning=reasoning)`.
- `generate_reply` retorna `Reply(spoken=spoken, reasoning=reasoning)`.

```python
@dataclass(frozen=True)
class Reply:
    spoken: str
    reasoning: str | None = None

def generate_reply(text: str, language: str = "") -> Reply:
    ...
```

### Etapa 3 — canais de voz e texto [Concluído]

`src/agent/text_chat.py`: se `reply.reasoning`, `print("Raciocínio:")` e `print(reply.reasoning)`; depois `print(f"Jarvis [{language}]: {reply.spoken}")`. Falha da LLM inalterada.

`src/voice/listen_repeat.py`: print e `speak` só com `reply.spoken`. Não imprime raciocínio.

### Etapa 4 — testes [Concluído]

- `tests/test_brain.py`: asserts passam a usar `.spoken`. `test_generate_reply_excludes_reasoning_content`: `spoken` sem o raciocínio; `reply.reasoning` preenchido; `append` da assistant chamado com `reasoning=...` e `content` só o texto falado; `append` do user **sem** `reasoning`. Novo teste: `ChatGroq` com `max_tokens=1024` e `model_kwargs={"include_reasoning": True}`. Novo teste: raciocínio ausente/vazio → `reasoning is None` e `append` assistant com `reasoning=None`.
- `tests/test_text_chat.py`: mocks devolvem `Reply`. Com e sem raciocínio no stdout.
- `tests/test_memory.py`: `append_message` com `role="user"` e `reasoning="..."` levanta `RuntimeError`. Sem Postgres: mockar a sessão / testar o ramo se o restante do módulo já for mockável; se o teste exigir engine real, **não** criar SQLite — cobrir o `RuntimeError` com a sessão mockada, ou deixar só o teste do cérebro se o ramo não for isolável sem banco. Preferir um teste de `append_message` com `Session` mockada.

Sem teste novo de `listen_repeat`. Sem rede.

Gate: `py -3.11 -m compileall src` e `py -3.11 -m unittest discover -s tests -v`. Depois da migração gerada, `alembic upgrade head` no ambiente de dev (não nos testes unitários).

### Etapa 5 — documentação [Concluído]

Atualizar os arquivos do checklist abaixo.

## Casos de teste (Gherkin)

Feature: Raciocínio da Groq

  Scenario: chat texto mostra o raciocínio e a resposta
    Given o modo `--text` e a Groq devolveu content e reasoning
    When a pessoa envia uma linha
    Then o terminal imprime o bloco Raciocínio com o texto interno
    And em seguida imprime Jarvis [lang] com só o content

  Scenario: chat texto sem raciocínio permanece igual
    Given o modo `--text` e a Groq devolveu só content
    When a pessoa envia uma linha
    Then o terminal imprime só Jarvis [lang]: <spoken>
    And não imprime a linha Raciocínio

  Scenario: voz fala só a resposta
    Given o loop de voz e a Groq devolveu content e reasoning
    When o cérebro responde
    Then o Piper recebe só spoken
    And o terminal de voz imprime só spoken

  Scenario: raciocínio gravado 1:1 com a mensagem assistant
    Given um turno em que a Groq devolveu reasoning
    When generate_reply persiste a resposta
    Then messages.content da assistant é só spoken
    And reasonings tem uma linha cujo message_id é o dessa assistant
    And load_window não inclui o texto do raciocínio

  Scenario: fala da pessoa não gera reasoning
    Given a fala do user é gravada antes da LLM
    When append_message grava o papel user
    Then não existe linha em reasonings para essa mensagem

  Scenario: LLM falha depois da fala
    Given a fala do user já comitada
    When o invoke falha
    Then não há mensagem assistant nem linha em reasonings

## Cobertura com testes unitários e integração

Necessário: retorno deixa de ser `str`; raciocínio não vaza para `spoken` nem para a janela; `append` da assistant recebe `reasoning`; chat texto ramifica com/sem raciocínio; user+reasoning é erro. `ChatGroq` e memória mockados. Sem Postgres real nos testes.

## Fora de escopo / não coberto

- Coluna `reasoning` em `messages` (a tabela própria é a decisão).
- 1:1 obrigatório com **toda** mensagem, inclusive `user`.
- Relacionamento ORM (`relationship()`) — o pacote hoje só usa FK.
- Endpoint ou comando para listar raciocínios depois; esta task só grava e mostra no `--text` do turno atual.
- Variáveis de ambiente para `include_reasoning`, `reasoning_effort` ou `max_tokens`.
- `reasoning_format` (`parsed`/`raw`/`hidden`).
- Recortar tags `<think>` no `content`.
- Imprimir raciocínio no loop de voz.
- Tools, RAG, mudança de `instructions.md`.

## Dúvidas impeditivas

Nenhuma. Interpretação fechada: 1:1 **opcional** com a mensagem `assistant` (raciocínio da LLM), não com cada linha de `messages`.

## Documentação

- [x] README.md — `generate_reply` devolve `Reply`; `--text` mostra o raciocínio; tabela `reasonings`
- [x] docs/progresso.md — seção datada `2026-09-07` para esta etapa
- [x] docs/cerebro-llm/regra-de-negocio.md — raciocínio extraído, visível no `--text` e gravado em `reasonings`; falado continua só o content
- [x] docs/cerebro-llm/arquitetura.md — `Reply`, `include_reasoning`, `max_tokens=1024`, `append_message(..., reasoning=)`
- [x] docs/chat-texto/regra-de-negocio.md — bloco `Raciocínio:` no stdout quando houver
- [x] docs/chat-texto/arquitetura.md — `Reply` no fluxo do loop
- [x] docs/memoria-conversacional/regra-de-negocio.md — tabela `reasonings`; 1:1 com assistant; janela ignora
- [x] docs/memoria-conversacional/arquitetura.md — modelo `Reasoning`, contrato de `append_message`, migração `0002`
- [x] spec/task-raciocinio-groq-011/regra-de-negocio.md — gravado pela spec
- [x] spec/task-raciocinio-groq-011/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): `docs/api/`, `docs/rosto-do-robo/`, `docs/spec/`, `docs/padroes-de-implementacao.md`, `docs/README.md`.
