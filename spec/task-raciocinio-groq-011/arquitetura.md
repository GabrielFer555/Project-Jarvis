# Arquitetura — Raciocínio da Groq no chat texto

## Contexto

No fluxo `LLM → TTS` / `LLM → stdout`, o cérebro já invoca `ChatGroq` e recorta `AIMessage.content`. O modelo `openai/gpt-oss-20b` devolve raciocínio num campo separado. Esta task pede esse campo, empacota os dois valores num `Reply`, imprime o raciocínio só no `--text` e persiste-o em `reasonings`, ligado à mensagem `assistant`.

```
microfone → STT → LLM (cérebro) → TTS          # só Reply.spoken
stdin     →      LLM (cérebro) → stdout        # reasoning (opcional) + spoken
                      ↕
              messages.assistant = spoken
              reasonings 1:1     = reasoning (se houver)
              load_window lê só messages
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Modelo | `src/memory/models.py` | Entidade `Reasoning` (`reasonings`) |
| Migração | `alembic/versions/20260907_0002_*.py` | Criar `reasonings`; não alterar a `0001` |
| Gravação | `src/memory/conversation.py` | `append_message(..., *, reasoning=)` na mesma transação da assistant |
| Cérebro | `src/agent/brain.py` | `ChatGroq` com `include_reasoning`; montar `Reply`; passar `reasoning` no append da assistant |
| Chat texto | `src/agent/text_chat.py` | Imprimir `Raciocínio:` quando houver; linha Jarvis com `spoken` |
| Loop de voz | `src/voice/listen_repeat.py` | Print e Piper só com `reply.spoken` |
| Testes | `tests/test_brain.py`, `tests/test_text_chat.py`, `tests/test_memory.py` | `Reply`, stdout, e contrato do `reasoning=` |

## Fluxo

```
init_brain()
  ChatGroq(..., max_tokens=1024, model_kwargs={"include_reasoning": True})
  assert_schema_up_to_date()   # exige head incluindo 0002

generate_reply(texto, idioma)
  → append user (commit, sem reasoning)
  → load_window                 # SELECT messages; sem join reasonings
  → invoke
  → spoken    = AIMessage.content.strip()
  → reasoning = additional_kwargs["reasoning_content"]  # ou None
  → append assistant(spoken, reasoning=reasoning)       # um commit
  → return Reply(spoken, reasoning)

--text:
  [se reasoning] print Raciocínio: / print reasoning
  print Jarvis [lang]: spoken

voz:
  print Jarvis [lang]: spoken
  speak(spoken)
```

## Contratos

```python
@dataclass(frozen=True)
class Reply:
    spoken: str
    reasoning: str | None = None

def generate_reply(text: str, language: str = "") -> Reply

def append_message(
    session_id: UUID,
    role: str,
    content: str,
    language: str = "",
    *,
    reasoning: str | None = None,
) -> None
```

Nenhuma variável de ambiente nova. Continuam `GROQ_API_KEY` e `GROQ_MODEL`.

`include_reasoning` vai em `model_kwargs` porque `ChatGroq` não tem esse campo de primeira classe. Não enviar `reasoning_format`.

LangChain mapeia `message.reasoning` da Groq para `additional_kwargs["reasoning_content"]`.

Objeto mapeado não sai de `src/memory/`. Sem `relationship()`.

## Dados

Postgres. Tabela nova, declarada em `src/memory/models.py` e materializada pela migração `20260907_0002`:

```python
class Reasoning(Base):
    __tablename__ = "reasonings"
    id:         Mapped[UUID]  # PK
    message_id: Mapped[UUID]  # FK messages.id ON DELETE CASCADE, UNIQUE
    content:    Mapped[str]
    created_at: Mapped[datetime]  # timestamptz, server_default now()
```

1:1 **opcional**: no máximo uma linha por `messages.id`; zero linhas quando a mensagem é `user` ou quando a assistant veio sem raciocínio.

`load_window` não lê esta tabela. Apagar a mensagem (cascade da sessão) apaga o raciocínio.

## Dependências

- Python 3.11
- LangChain (`langchain-core`, `langchain-groq`)
- Groq (`GROQ_MODEL`, exemplo `openai/gpt-oss-20b`)
- Postgres / SQLAlchemy 2.0 / Alembic
- `src/memory/`

## Decisões

| Decisão | Motivo |
| --- | --- |
| Tabela `reasonings` em vez de coluna em `messages` | Raciocínio é opcional, pode ser longo e não participa da janela; `messages` continua o recorte do prompt |
| 1:1 com a mensagem `assistant`, não com toda `messages` | Só a LLM produz raciocínio; a fala da pessoa é dado, não thought process |
| Linha ausente quando não há raciocínio | Evita `content` vazio e 1:1 obrigatório falso |
| Mesmo commit da assistant | Resposta e raciocínio nascem juntos; falha da LLM continua sem os dois |
| `load_window` ignora `reasonings` | Não inflar o prompt nem devolver chain-of-thought ao modelo |
| `Reply` no lugar de `str` | Dois valores sem global nem segundo `generate_*` |
| `include_reasoning`, sem `reasoning_format` | Contrato do GPT-OSS |
| `max_tokens=1024` | 128 costuma ser consumido pelo raciocínio |
| Imprimir raciocínio só no `--text` | Canal de debug; voz não fala nem polui o terminal de operação |
| Sem `relationship()` | O pacote hoje expõe só FK e tipos simples |
