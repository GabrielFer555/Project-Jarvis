# Spec: chat por texto e debug no Cursor

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 5/5 etapas

## Descrição breve da tarefa

Abrir um canal de texto no terminal para conversar com o Jarvis sem microfone, STT, wake word ou TTS, reusando o mesmo cérebro e os mesmos guardrails da voz. Incluir uma configuração de debug do Cursor (`.vscode/launch.json`) apontando para o Python 3.11, para inspecionar o fluxo da LLM.

## Requisitos funcionais

- RF1: Existir um modo de interação só por texto: a pessoa digita no terminal e a resposta da LLM é impressa, sem áudio.
- RF2: O modo texto não carrega microfone, Whisper, Piper nem a wake word **Jarvis**.
- RF3: O modo texto chama o mesmo `generate_reply` e lê o mesmo `src/agent/instructions.md`. Guardrails, delimitação `<<<` `>>>` e turno isolado são os da voz.
- RF4: Cada linha digitada é um turno isolado: sem histórico, tools, RAG ou memória.
- RF5: O idioma do prompt é explícito no modo texto (`--lang pt` ou `--lang en`; padrão `pt`). Não há detecção automática (Whisper não roda).
- RF6: Encerrar com `sair`, `quit` ou `exit` (sem distinção de maiúsculas) ou Ctrl+C. Linha vazia ou só espaços não chama a LLM.
- RF7: Sem `GROQ_API_KEY`, `GROQ_MODEL` ou `instructions.md` válido, o modo texto aborta na subida com o mesmo `RuntimeError` do cérebro, antes do loop.
- RF8: Falha da Groq ou da rede imprime o erro no terminal e o loop de texto continua, sem encerrar o processo.
- RF9: `src/main.py` sem `--text` continua abrindo o loop de voz, inalterado.
- RF10: O repositório passa a ter `.vscode/launch.json` usável no Cursor para depurar o processo Python (breakpoint, passo a passo), com console no terminal integrado para o `input()` do chat.

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| Cérebro LLM | `docs/cerebro-llm/regra-de-negocio.md` | A LLM só recebe texto transcrito pelo Whisper depois da wake word; a saída vai ao Piper | A LLM também recebe texto digitado no modo `--text`, com idioma da flag; a saída desse modo vai ao terminal, sem TTS. Contrato de `generate_reply` e `instructions.md` não muda |
| Cérebro LLM | `docs/cerebro-llm/arquitetura.md` | O único chamador do cérebro é `src/voice/listen_repeat.py` | `src/agent/text_chat.py` entra como segundo chamador; o loop de voz permanece |

Nova funcionalidade: sim, criar `docs/chat-texto/` (canal de texto + launch de debug). Registrar no índice `docs/README.md`.

Não impactadas: `docs/rosto-do-robo/`, `docs/spec/`. Voz (`src/voice/`) continua sem pasta em `docs/`; esta task não a cria.

## Implementação técnica

### Etapa 1 — loop de chat por texto [Concluído]

Criar `src/agent/text_chat.py` com `run_text_chat(language: str = "pt") -> None`.

- Na subida: só `init_brain()`. Não importar `voice`, `mic`, `stt`, `tts` nem `hardware.face`.
- Loop: `input("Você: ")` → interpretar a linha → `generate_reply(texto, language=language)` → `print` no formato `Jarvis [{language}]: {reply}`.
- Comandos de saída (depois de `strip`, casefold): `sair`, `quit`, `exit`. `EOFError` (stdin fechado) também encerra.
- Exceção de `generate_reply`: `print(f"Erro na LLM: {exc}")` e `continue`, no mesmo espírito do loop de voz.
- Exportar `run_text_chat` em `src/agent/__init__.py`.
- Não alterar `brain.py`, `settings.py` nem `instructions.md`.

### Etapa 2 — roteamento em `main.py` [Concluído]

`src/main.py` continua fino: só escolhe o loop.

- Flag `--text` abre `run_text_chat`.
- Flag `--lang` aceita só `pt` e `en`; padrão `pt`. Sem `--text`, `--lang` é ignorado (o Whisper segue detectando o idioma).
- `argparse` da biblioteca padrão. Sem dependência nova.
- `KeyboardInterrupt` no `if __name__` permanece e imprime `Encerrado.` nos dois modos.

Contrato da CLI:

```
py -3.11 src/main.py
py -3.11 src/main.py --text
py -3.11 src/main.py --text --lang en
```

### Etapa 3 — configuração de debug no Cursor [Concluído]

Criar `.vscode/launch.json` versionado (a pasta não está no `.gitignore`). O Cursor lê esse arquivo como o VS Code.

Duas configurações, tipo `debugpy`, `request: launch`, `console: integratedTerminal` (obrigatório: `internalConsole` não aceita `input()`), `cwd` na raiz do repo, `justMyCode: true`:

| Nome | Programa | Args |
| --- | --- | --- |
| Jarvis: chat texto | `${workspaceFolder}/src/main.py` | `["--text"]` |
| Jarvis: voz | `${workspaceFolder}/src/main.py` | `[]` |

Não gravar caminho absoluto do `python.exe` (máquina-específica). O README da execução orienta a selecionar o interpretador **Python 3.11** no Cursor (`Python: Select Interpreter`) antes de F5. Não criar `.vscode/settings.json` com path local.

Não adicionar `debugpy` ao `requirements.txt`: o debugger vem da extensão Python do Cursor.

### Etapa 4 — testes [Concluído]

`tests/test_text_chat.py` e extensão de um teste de roteamento (mesmo arquivo ou `tests/test_main.py`), com `ChatGroq` e `generate_reply` mockados. Sem rede, sem microfone.

Cobrir: linha vazia não chama a LLM; `sair`/`quit`/`exit` encerram; uma mensagem chama `generate_reply` com o texto e o idioma; falha da LLM imprime e o próximo turno ainda roda; `main` sem `--text` despacha o loop de voz; `main --text` despacha o chat com `pt`; `main --text --lang en` passa `en`.

Não criar teste que leia `launch.json`.

### Etapa 5 — documentação [Concluído]

- `docs/chat-texto/regra-de-negocio.md`: criar a regra do canal de texto (objetivo, comportamento, entradas, exceções, fora de escopo).
- `docs/chat-texto/arquitetura.md`: criar componentes (`text_chat`, `main` como roteador, `launch.json`), fluxo, contratos da CLI e do debug, decisões.
- `docs/cerebro-llm/regra-de-negocio.md`: a entrada deixa de ser só a transcrição; o modo texto é outra origem do mesmo `generate_reply`.
- `docs/cerebro-llm/arquitetura.md`: incluir o loop de texto na tabela de componentes e no fluxo, sem mudar a assinatura do cérebro.
- `docs/README.md`: linha nova no índice para Chat texto → `docs/chat-texto/` → `src/agent/text_chat.py`.
- `docs/padroes-de-implementacao.md`: acrescentar `py -3.11 src/main.py --text` em Comandos.
- `README.md`: como rodar o modo texto; como depurar no Cursor (interpretador 3.11 + F5); árvore com `.vscode/launch.json` e `text_chat.py`.
- `docs/progresso.md`: seção datada desta task.

## Casos de teste (Gherkin)

Feature: chat por texto sem voz
  Scenario: pergunta digitada vai à LLM e a resposta sai no terminal
    Given o programa iniciado com `--text` e o cérebro no ar
    When a pessoa digita uma pergunta e confirma
    Then `generate_reply` é chamado com esse texto e o idioma da flag
    And a resposta é impressa no terminal
    And nenhum microfone, Whisper ou Piper é acionado

  Scenario: linha em branco não chama a LLM
    Given o chat texto em execução
    When a pessoa envia uma linha vazia ou só espaços
    Then a LLM não é chamada
    And o prompt de entrada volta a aparecer

  Scenario: encerrar o chat
    Given o chat texto em execução
    When a pessoa digita `sair`, `quit` ou `exit`
    Then o loop termina sem chamar a LLM nessa linha

  Scenario: falha da LLM não derruba o chat
    Given o chat texto em execução
    When `generate_reply` levanta uma exceção
    Then o erro é impresso no terminal
    And o loop segue aceitando a próxima linha

  Scenario: mesmos guardrails da voz
    Given o chat texto em execução
    When a pessoa digita uma ordem para ignorar as instruções
    Then o texto entra no prompt só entre `<<<` e `>>>`
    And as regras de `instructions.md` continuam valendo

  Scenario: entrada padrão continua sendo voz
    Given o programa iniciado sem `--text`
    When o processo sobe
    Then o loop de voz (`run_listen_repeat`) é o que roda

Feature: debug no Cursor
  Scenario: F5 no chat texto
    Given `.vscode/launch.json` no repositório e o interpretador Python 3.11 selecionado
    When a pessoa inicia a configuração `Jarvis: chat texto`
    Then o debugger lança `src/main.py --text` no terminal integrado
    And breakpoints em `src/agent/` param a execução

## Cobertura com testes unitários e integração

Necessário: o roteamento em `main.py` e o loop de texto ramificam (vazio, sair, turno, erro, flag de idioma). Testes com `generate_reply` e os loops de voz/texto mockados evitam regressão sem rede. `launch.json` não entra no `unittest`.

## Fora de escopo / não coberto

- Histórico multi-turno, tools, RAG, memória vetorial.
- Interface web, TUI ou chat gráfico.
- Alterar `instructions.md`, tom, limites ou recusas.
- Usar o rosto no modo texto.
- Documentar a funcionalidade de voz em `docs/voz/`.
- Preencher ou apagar a pasta vazia `spec/task-chat-texto-debug-005/`.
- Gravar path absoluto do Python em `settings.json`.
- Depuração remota (attach) ou debug do interpretador 3.14.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md — modo `--text`, comando, como depurar no Cursor (Python 3.11 + F5), arquivos novos na árvore
- [x] docs/progresso.md — seção datada
- [x] docs/cerebro-llm/regra-de-negocio.md — atualizar: entrada também pode ser texto digitado; no modo texto a saída não vai ao Piper
- [x] docs/cerebro-llm/arquitetura.md — atualizar: `text_chat.py` como segundo chamador de `generate_reply`
- [x] docs/chat-texto/ — criar `regra-de-negocio.md` e `arquitetura.md`
- [x] docs/README.md — registrar Chat texto no índice
- [x] docs/padroes-de-implementacao.md — acrescentar `py -3.11 src/main.py --text` em Comandos
- [x] spec/task-chat-texto-debug-007/regra-de-negocio.md — gravado pela spec
- [x] spec/task-chat-texto-debug-007/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): `docs/rosto-do-robo/`, `docs/spec/`.
