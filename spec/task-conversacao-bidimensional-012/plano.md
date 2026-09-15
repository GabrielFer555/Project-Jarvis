# Spec: Janela de conversa por voz após a resposta

## Cabeçalho

- **Branch base:** feat/created-memory
- **Modo de execução:** non stop
- **Progresso:** 5/5 etapas

## Descrição breve da tarefa

Hoje cada turno de voz é `wake word → frase → resposta → fim`: depois do Piper, o loop volta a exigir **Jarvis**. A conversa passa a ter uma janela após o fim do TTS, com default de **15 segundos** (`CONVERSATION_WINDOW_SECONDS`). Esse valor mede **só silêncio**: se a pessoa começar a falar, o timeout não corta a frase e a janela **reinicia** (relógio cheio de novo). Se ninguém falar, o comportamento permanece o AS-IS. O módulo do loop deixa de se chamar `listen_repeat.py` e passa a ser `listen.py`.

## Requisitos funcionais

- RF1: Depois que o Piper termina de falar, o loop abre uma janela de escuta. `CONVERSATION_WINDOW_SECONDS` (default **15**) conta **somente silêncio contínuo** à espera de uma fala. Não é teto da frase, da LLM nem do TTS. Não alimenta `max_seconds`.
- RF2: Fala transcrita não vazia dentro da janela **não exige** a wake word. O texto vai para `generate_reply` e o Piper fala a nova resposta.
- RF3: Se a transcrição da janela contiver a wake word, `split_wake_word` continua valendo: o comando depois de **Jarvis** é o texto enviado à LLM; se a pessoa disser só **Jarvis**, reutiliza o caminho atual (`Pode falar.` + bip + escuta da pergunta com `start_timeout=6.0`). Sem pergunta depois disso, fecha a janela e volta a esperar a wake word.
- RF4: Só **silêncio contínuo** pelo valor da env (áudio vazio / ninguém começou a falar) fecha a janela: rosto Sleeping e espera por **Jarvis** (AS-IS). Transcrição vazia depois de uma take também fecha.
- RF5: No instante em que o VAD marca **início de fala**, o timeout da janela **deixa de valer** para aquela take (a pessoa termina a frase com `COMMAND_SILENCE_S`, como hoje). A janela **reinicia**: relógio cheio, não o restante. Reinício depois do TTS da resposta (novo `record_utterance`) e também se a take for descartada como curta demais (zerar o relógio de silêncio em vez de aproveitar o tempo já gasto).
- RF6: Falha da LLM (ou do Postgres no turno) durante um follow-up: mensagem no terminal, rosto Sleeping, `mic.clear()`, janela **não** reabre; o loop volta a esperar **Jarvis**.
- RF7: Durante a janela o rosto fica **Listening**, não Sleeping. Sleeping só na espera da wake word, no abandono da janela e no erro.
- RF8: O modo `--text` não muda. A sessão em Postgres e `SESSION_IDLE_MINUTES` não mudam: a janela de voz **não** encerra a sessão.
- RF9: `CONVERSATION_WINDOW_SECONDS` é opcional no `.env`. Ausente ou vazia cai em **15**. Valor não inteiro ou `<= 0` aborta na subida com `RuntimeError` citando a variável e o valor — o mesmo `_positive_int` de `SESSION_IDLE_MINUTES`.
- RF10: O loop de voz mora em `src/voice/listen.py`. A função pública passa a ser `run_listen()`. `listen_repeat.py` e `run_listen_repeat()` saem do código vivo.

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| Cérebro LLM | `docs/cerebro-llm/regra-de-negocio.md` | Depois da wake word a transcrição vai à LLM; se a LLM falhar, espera **Jarvis** de novo | Wake word inicia a conversa por voz; turnos seguintes na janela chamam a mesma `generate_reply` sem wake word. Falha da LLM continua fechando o turno e esperando **Jarvis** |
| Cérebro LLM | `docs/cerebro-llm/arquitetura.md` | Loop em `listen_repeat.py`: acordar → ouvir → pensar → falar | Loop em `listen.py` (`run_listen`); ramo pós-TTS com janela configurável |
| Rosto do robô | `docs/rosto-do-robo/regra-de-negocio.md` | Depois de falar, Sleeping; Listening só após a wake word | Depois de Answering, Listening enquanto a janela está aberta; Sleeping quando a janela fecha ou a LLM falha |
| Rosto do robô | `docs/rosto-do-robo/arquitetura.md` | Loop em `listen_repeat.py`; `Answering → TTS → Sleeping` | Loop em `listen.py`; `Answering → TTS → Listening` (janela) → Thinking ou Sleeping |
| Memória conversacional | `docs/memoria-conversacional/regra-de-negocio.md` | Entrada de voz descrita como “frase depois da wake word” | Também a fala na janela, sem wake word; sessão inalterada |
| Memória conversacional | `docs/memoria-conversacional/arquitetura.md` | Caminho do loop: `listen_repeat.py` | Caminho: `listen.py` |
| Chat texto | `docs/chat-texto/arquitetura.md` | Despacho `run_listen_repeat()` | Despacho `run_listen()`; comportamento do `--text` igual |
| API HTTP | `docs/api/arquitetura.md` | Fluxo voz → `run_listen_repeat()` | Fluxo voz → `run_listen()` |

Nova funcionalidade: **sim**, criar `docs/voz/` (wake word, STT, TTS e o loop com a janela). A voz existe em `src/voice/` e hoje só aparece como “ainda sem documentação” no índice.

Não impactadas: `docs/spec/`, `docs/padroes-de-implementacao.md`, `docs/chat-texto/regra-de-negocio.md` (o modo texto não muda).

## Implementação técnica

### Etapa 1 — `CONVERSATION_WINDOW_SECONDS` em settings [Concluído]

`src/agent/settings.py`: campo `conversation_window_seconds: int = 15`, lido com o `_positive_int` já usado por `SESSION_IDLE_MINUTES` / `API_PORT`.

`.env.example`: linha comentada `# CONVERSATION_WINDOW_SECONDS=15`, no mesmo bloco das opcionais.

`load_settings()` já corre em `main` antes do loop; o loop lê o valor do `Settings` (nova chamada a `load_settings()` no início de `run_listen` é aceitável — dotenv já está carregado — ou usa o retorno de `init_brain()`, que já devolve `Settings`). Não passar o timeout por argumento de `main.py`.

### Etapa 2 — listen.py e janela pós-TTS [Concluído]

Renomear `src/voice/listen_repeat.py` → `src/voice/listen.py` (git mv). Apagar o arquivo antigo. Sem alias, sem reexport do nome velho.

Atualizar imports vivos:

- `src/voice/__init__.py`: `from .listen import run_listen`; `__all__` troca `run_listen_repeat` por `run_listen`
- `src/main.py`: `from voice import run_listen` e `run_listen()`
- `tests/test_text_chat.py`: mock e asserts passam a `run_listen` (o `--text` em si não muda)

`src/main.py` permanece fino. Sem mudança em `generate_reply`, memória, Piper, Whisper ou na ABC do rosto.

Em `listen.py`, `classify_follow_up` (testável sem microfone):

```python
def classify_follow_up(text: str) -> tuple[str, str]:
    """('wait_wake', '') | ('await_command', '') | ('continue', comando)."""
```

- texto vazio após `strip` → `wait_wake`
- `split_wake_word` ouviu a wake e o comando está vazio → `await_command`
- ouviu a wake e há comando → `continue`, comando
- não ouviu a wake e há texto → `continue`, texto inteiro

O `while True` deixa de cair sempre em “Aguardando 'Jarvis'...” depois do TTS. Depois de `speak` + `mic.clear()`, o loop entra no ramo de follow-up:

1. `face.listen()` (não `sleep()`)
2. `mic.record_utterance(silence_seconds=COMMAND_SILENCE_S, start_timeout=float(window_s), ignore_ms=250)` — `window_s` vem de `settings.conversation_window_seconds`. **Não** passar a env em `max_seconds` (o teto técnico de 12s de uma take permanece o default atual, independente da janela).
3. `classify_follow_up` na transcrição
4. `wait_wake` → `face.sleep()` e volta à espera da wake word
5. `await_command` → o bloco atual `Pode falar.` / `beep()` / `start_timeout=6.0`; sem frase, `wait_wake`
6. `continue` → o mesmo bloco `face.think()` / `generate_reply` / `speak` de hoje; sucesso abre uma janela **nova e cheia**

Em `src/voice/mic.py`, o `start_timeout` já só aborta no ramo **sem** fala (`speech_started` falso). Ajustar o relógio para a janela **reiniciar**:

- Enquanto `speech_started` é verdadeiro, `start_timeout` **não** corta a gravação (já é o caso).
- Se a take for descartada (fala mais curta que `min_speech_seconds`), **zerar** o contador usado pelo `start_timeout` (`waited_chunks`). Hoje o tempo de silêncio anterior continua acumulado e o restante da janela mataria a espera. Com o zera, a pessoa ganha de novo o valor cheio de `CONVERSATION_WINDOW_SECONDS` de silêncio.

Print no terminal quando a janela abre, com o valor efetivo em segundos (análogo a `Aguardando 'Jarvis'...`).

`WAKE_SILENCE_S` e `COMMAND_SILENCE_S` continuam constantes do módulo. Só a janela de conversa vai para o `.env`. `COMMAND_SILENCE_S` (1.6s) continua sendo o fim da **frase**, não o fim da conversa.

### Etapa 3 — rosto no loop (mesmo `listen.py`) [Concluído]

Nenhum estado novo em `FaceState`. Só a ordem das chamadas:

- fim do TTS com janela aberta → `listen()`, não `sleep()`
- timeout / transcrição vazia / só wake word sem pergunta → `sleep()`
- exceção de `generate_reply` → `sleep()`, janela fechada (já é o tratamento atual; passa a valer também no follow-up)

Sem mudança em `src/hardware/face/`. Sem cenário novo em `tests/test_face.py`.

### Etapa 4 — testes [Concluído]

- `tests/test_listen.py` (novo): `classify_follow_up` e `split_wake_word` nos casos da janela. Sem microfone, Whisper, Piper ou Groq.
- `tests/test_settings.py`: default 15 quando a chave falta; valor positivo customizado; inválidos (`abc`, `0`, `-1`) levantam `RuntimeError` com nome e valor — incluir `CONVERSATION_WINDOW_SECONDS` no teste já existente de port/idle ou num caso irmão.
- `tests/test_text_chat.py`: só a troca `run_listen_repeat` → `run_listen`.
- Sem teste do `while True` com `MicSession` real.

### Etapa 5 — documentação [Concluído]

- `docs/voz/regra-de-negocio.md`: criar (wake word, STT, TTS, loop, janela só de silêncio e reinício ao iniciar fala)
- `docs/voz/arquitetura.md`: criar (`listen.py`, `run_listen`, `classify_follow_up`, `start_timeout` só no silêncio, contrato da env)
- `docs/README.md`: linha **Voz** na tabela mapeada; remover voz de “Ainda sem documentação”
- `docs/cerebro-llm/regra-de-negocio.md` e `arquitetura.md`: wake word inicia; follow-up na janela; caminho `listen.py`
- `docs/rosto-do-robo/regra-de-negocio.md` e `arquitetura.md`: Listening durante a janela; loop em `listen.py`
- `docs/memoria-conversacional/regra-de-negocio.md`: fala na janela também grava `user`
- `docs/memoria-conversacional/arquitetura.md`: caminho do loop `listen.py` (só isso)
- `docs/chat-texto/arquitetura.md`: `run_listen()` no despacho sem `--text`
- `docs/api/arquitetura.md`: voz → `run_listen()`
- `README.md`: estrutura (`listen.py`), `run_listen()`, janela, `CONVERSATION_WINDOW_SECONDS` em Como rodar
- `docs/progresso.md`: seção datada `2026-09-14`

Pastas `spec/task-*` antigas não são editadas.

## Casos de teste (Gherkin)

Feature: Janela de conversa por voz

  Scenario: pessoa responde sem wake word dentro da janela
    Given o Jarvis acabou de falar uma resposta pelo Piper
    And CONVERSATION_WINDOW_SECONDS vale 15
    When a pessoa começa a falar antes de 15 segundos de silêncio sem dizer Jarvis
    Then a transcrição vai para generate_reply
    And o Piper fala a nova resposta
    And uma janela cheia nova de 15 segundos de silêncio abre

  Scenario: fala iniciada não é cortada pelo timeout da janela
    Given a janela está aberta com CONVERSATION_WINDOW_SECONDS igual a 15
    When a pessoa começa a falar e a frase dura mais de 15 segundos até a pausa do VAD
    Then CONVERSATION_WINDOW_SECONDS não encerra a take
    And a gravação segue até COMMAND_SILENCE_S de pausa
    And depois do TTS a janela reinicia com 15 segundos cheios de silêncio

  Scenario: silêncio contínuo até o fim da janela volta a exigir a wake word
    Given o Jarvis acabou de falar uma resposta pelo Piper
    When ninguém começa a falar durante CONVERSATION_WINDOW_SECONDS de silêncio contínuo
    Then o rosto vai para Sleeping
    And o loop volta a aguardar a wake word Jarvis

  Scenario: só a wake word dentro da janela pede a pergunta
    Given a janela está aberta
    When a pessoa diz só Jarvis
    Then o loop faz o caminho Pode falar e escuta a pergunta
    And se não houver pergunta o loop volta a aguardar a wake word

  Scenario: falha da LLM no follow-up fecha a janela
    Given a janela está aberta e a pessoa falou um follow-up
    When generate_reply levanta exceção
    Then o terminal mostra o erro
    And o rosto vai para Sleeping
    And o loop volta a aguardar a wake word sem reabrir a janela

  Scenario: CONVERSATION_WINDOW_SECONDS inválida aborta na subida
    Given CONVERSATION_WINDOW_SECONDS vale 0 ou não é inteiro
    When load_settings corre
    Then RuntimeError cita a variável e o valor
    And o loop não começa

## Cobertura com testes unitários e integração

Unitário de `classify_follow_up` / `split_wake_word` em `tests/test_listen.py`. Unitário da env em `tests/test_settings.py` (default, valor válido, inválido). Ajuste de mock em `tests/test_text_chat.py`. Sem microfone e sem Groq. Sem teste novo do rosto.

## Fora de escopo / não coberto

- Mudança de comportamento do modo `--text`.
- Mudar `SESSION_IDLE_MINUTES`, esquema Postgres ou `generate_reply`.
- Estado novo no rosto, beep ao abrir a janela, barge-in (interromper o TTS).
- Identificação de locutor, cancelamento da janela por comando falado do tipo “obrigado, tchau”.
- Locomoção, visão, tools, RAG.
- Reexport ou alias de `listen_repeat` / `run_listen_repeat`.
- Reescrever pastas `spec/task-*` históricas.
- Documentar a voz além do que esta task passa a ser.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md — `listen.py` / `run_listen()`; janela; `CONVERSATION_WINDOW_SECONDS` em Como rodar; “O que já funciona”
- [x] docs/progresso.md — seção datada 2026-09-14
- [x] docs/voz/ — criar `regra-de-negocio.md` e `arquitetura.md` (timeout só de silêncio; janela reinicia ao iniciar fala) + índice em docs/README.md
- [x] docs/cerebro-llm/regra-de-negocio.md — atualizar: wake word inicia; follow-up na janela sem wake word
- [x] docs/cerebro-llm/arquitetura.md — atualizar: ramo pós-TTS; caminho `src/voice/listen.py`
- [x] docs/rosto-do-robo/regra-de-negocio.md — atualizar: Listening durante a janela
- [x] docs/rosto-do-robo/arquitetura.md — atualizar: Answering → Listening; loop em `listen.py`
- [x] docs/memoria-conversacional/regra-de-negocio.md — atualizar: fala na janela também grava `user`
- [x] docs/memoria-conversacional/arquitetura.md — atualizar: caminho do loop `listen.py`
- [x] docs/chat-texto/arquitetura.md — atualizar: despacho `run_listen()`
- [x] docs/api/arquitetura.md — atualizar: voz → `run_listen()`
- [x] spec/task-conversacao-bidimensional-012/regra-de-negocio.md — gravado pela spec; divergência do VAD (`reset_start_timeout_on_short` só na janela)
- [x] spec/task-conversacao-bidimensional-012/arquitetura.md — gravado pela spec; divergência do VAD (`reset_start_timeout_on_short` só na janela)

Docs não impactadas (não tocar): docs/chat-texto/regra-de-negocio.md, docs/spec/, docs/padroes-de-implementacao.md.
