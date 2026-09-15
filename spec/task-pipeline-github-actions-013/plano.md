# Spec: Pipeline GitHub Actions em PRs para main e develop

## Cabeçalho

- **Branch base:** feat/created-memory
- **Modo de execução:** non stop
- **Progresso:** 3/3 etapas

## Descrição breve da tarefa

O repositório não tem CI. Cada pull request cujo alvo é `main` ou `develop` passa a rodar um workflow GitHub Actions com três passos em sequência: **build** (`compileall` do `src/`), **todos os testes `unittest`**, **publicar artifact** com o relatório XML desses testes. Falha no build ou nos testes deixa o check do PR vermelho.

## Requisitos funcionais

- RF1: O workflow dispara em pull request cujo **base** é `main` ou `develop`. Eventos: `opened`, `synchronize` e `reopened` (abrir o PR e cada push seguinte no head). Push direto, merge e PR contra qualquer outra branch não disparam.
- RF2: Um único job, Ubuntu, **Python 3.11**. Passos nesta ordem: instalar dependências → build → testes → publicar artifact. Sem `pytest`.
- RF3: Build = `python -m compileall src` (o mesmo critério local de `docs/padroes-de-implementacao.md`). Erro de sintaxe ou bytecode impede os testes; o job falha.
- RF4: Testes = descoberta `unittest` em `tests/`, gerando relatório **JUnit XML** via `unittest-xml-reporting` (`xmlrunner`), instalado **só no runner**. `requirements.txt` não ganha essa lib. Qualquer teste falho deixa o job falho.
- RF5: O XML vai para um artifact do run (`actions/upload-artifact`), mesmo quando os testes falham (`if: always()`), para o relatório existir no caso em que mais se precisa dele. Sem XML (build quebrou antes), o upload não falha o job de novo: `if-no-files-found: ignore`.
- RF6: Sem rede real nos testes (já é o contrato do repo). Sem secrets (`GROQ_API_KEY`, Postgres). Sem Docker/Postgres no job. `libportaudio2` no Ubuntu porque importar `voice` / `main` carrega `sounddevice`.
- RF7: `test-results/` entra no `.gitignore`. Relatório XML gerado localmente (ou copiado do runner) não é versionado. (Decisão do usuário na Fase 1 do rock-it.)

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| *(nenhuma mapeada cobre CI)* | — | Não há pipeline no GitHub | Capacidade nova: PRs para `main`/`develop` compilam, testam e publicam XML |
| Padrões do projeto | `docs/padroes-de-implementacao.md` | Comandos locais `py -3.11`, `compileall`, `unittest`; pytest fora da stack. Sem afirmação de exclusividade local | O mesmo build/teste passa a rodar também no GitHub Actions (PRs para `main`/`develop`): fim da exclusividade local. XML só no runner. pytest continua fora |

Nova funcionalidade: **sim**, criar `docs/ci/` e registrar no índice `docs/README.md`.
Não impactadas: `docs/api/`, `docs/cerebro-llm/`, `docs/chat-texto/`, `docs/memoria-conversacional/`, `docs/rosto-do-robo/`, `docs/spec/`, `docs/voz/`.

A branch remota `develop` **ainda não existe** (só `main`). O workflow lista as duas; PRs para `develop` só passam a disparar quando a branch existir. Não é impeditivo e **não** cria a branch nesta task.

## Implementação técnica

### Etapa 1 — workflow `.github/workflows/ci.yml` [Concluído]

Criar o arquivo. Não há pasta `.github/` hoje.

Contrato do YAML (snapshot — o rock-it pode pinar o SHA das actions oficiais, mas majors e nomes abaixo são obrigatórios):

```yaml
name: CI

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main, develop]

permissions:
  contents: read

jobs:
  build-test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - name: Install PortAudio
        run: sudo apt-get update && sudo apt-get install -y libportaudio2

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
          python -m pip install unittest-xml-reporting

      - name: Build
        run: python -m compileall src

      - name: Run tests
        run: python -m xmlrunner discover -s tests -v -o test-results

      - name: Publish test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results/*.xml
          if-no-files-found: ignore
```

Decisões desta etapa:

- **Um job, três passos de produto** (build → testes → artifact), não três jobs: o XML e o `compileall` compartilham o mesmo checkout e o mesmo Python.
- **`synchronize` incluso:** "PR opened directed at" cobre o PR cujo alvo é `main`/`develop`; sem `synchronize` o CI não revalidaria commits novos, o que anularia o gate.
- **`unittest-xml-reporting` só no `pip install` do job.** Não entra em `requirements.txt`. pytest continua proibido.
- **Actions oficiais** `checkout`, `setup-python`, `upload-artifact`. Sem action de terceiros para “pretty print” do JUnit no PR (o pedido é artifact XML).
- **`libportaudio2`:** `tests/test_text_chat.py` faz `import main` → `from voice import run_listen` → `sounddevice`. Sem a lib o import quebra no Ubuntu.
- **Timeout 30 min:** Piper + faster-whisper no pip do runner é pesado; 30 evita job zumbi, não é cache nem otimização extra.
- Sem `cache: pip`, sem matrix de OS, sem `permissions` além de `contents: read`.

### Etapa 2 — `.gitignore` [Concluído]

RF7: incluir `test-results/` (diretório do XML). O `.gitignore` já ignora `nosetests.xml` / `coverage.xml`; o diretório do xmlrunner entra para relatório local não ser commitado.

Não criar `requirements-dev.txt` nem helper Python para XML.

### Etapa 3 — documentação [Concluído]

- `docs/ci/regra-de-negocio.md`: criar (quando o CI roda, o que passa/falha, o que o artifact contém)
- `docs/ci/arquitetura.md`: criar (workflow, job, comandos, artifact)
- `docs/README.md`: linha nova na tabela de funcionalidades (CI → `docs/ci/` → `.github/workflows/ci.yml`)
- `docs/padroes-de-implementacao.md`: decisão + comando do CI; pytest continua fora
- `README.md`: pasta `.github/` na estrutura; menção de que PR para `main`/`develop` dispara o CI
- `docs/progresso.md`: seção datada

## Casos de teste (Gherkin)

Feature: Pipeline CI em pull request

  Scenario: PR contra main executa build, unittest e publica XML
    Given um pull request cujo base é "main"
    When o PR é aberto ou recebe um novo commit
    Then o job instala Python 3.11 e as dependências
    And executa compileall em src
    And executa unittest discover em tests gerando XML em test-results/
    And publica o artifact "test-results" com esses XML
    And o check do PR fica verde se build e testes passaram

  Scenario: PR contra develop dispara o mesmo job
    Given a branch develop existe
    And um pull request cujo base é "develop"
    When o PR é aberto ou recebe um novo commit
    Then o mesmo job de build, testes e artifact roda

  Scenario: testes falhos deixam o PR vermelho e ainda publicam o XML
    Given um pull request cujo base é "main" ou "develop"
    When algum TestCase unittest falha
    Then o passo de testes falha e o job fica failed
    And o artifact "test-results" é publicado com o XML da execução

  Scenario: falha no build não roda os testes
    Given um pull request cujo base é "main" ou "develop"
    When compileall encontra erro em src
    Then o passo de testes não executa
    And o job fica failed
    And o upload do artifact não falha o run por ausência de XML

  Scenario: PR contra outra branch não dispara o workflow
    Given um pull request cujo base não é "main" nem "develop"
    When o PR é aberto
    Then o workflow CI não inicia

  Scenario: relatório XML local não entra no git
    Given o diretório test-results/ com XML gerado
    When alguém tenta versionar o repositório
    Then test-results/ está no .gitignore

## Cobertura com testes unitários e integração

Não necessário: o contrato é YAML no GitHub Actions, sem lógica ramificada em `src/`. Não há como o unittest local simular o runner sem duplicar o Gherkin. Gate do rock-it continua `compileall` + `unittest` no que já existe; esta task não adiciona testes Python.

## Fora de escopo / não coberto

- Criar a branch `develop`.
- CI em `push` para `main`/`develop` (só PR).
- Comentário/check JUnit no PR (`dorny/test-reporter`, `EnricoMi/publish-unit-test-result-action`).
- Coverage, lint, type-check, cache de pip, matrix Windows/macOS.
- Postgres, Docker, Groq ou secrets no job.
- Alterar testes, `requirements.txt` ou o código do robô.
- Deploy / release.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md — incluir `.github/workflows/ci.yml` na estrutura; uma frase em Como rodar / Progresso: PR para `main` ou `develop` dispara build + unittest + artifact XML
- [x] docs/progresso.md — seção datada: pipeline básico no GitHub Actions
- [x] docs/ci/regra-de-negocio.md — criar: quando dispara, ordem dos passos, vermelho/verde, artifact
- [x] docs/ci/arquitetura.md — criar: workflow, job, Python 3.11, xmlrunner, upload-artifact
- [x] docs/README.md — registrar a funcionalidade CI na tabela (código: `.github/workflows/ci.yml`)
- [x] docs/padroes-de-implementacao.md — decisão: CI em PR para `main`/`develop`; XML só no runner via `unittest-xml-reporting`; pytest continua fora. Comando do runner ao lado dos comandos locais
- [x] spec/task-pipeline-github-actions-013/regra-de-negocio.md — gravado pela spec
- [x] spec/task-pipeline-github-actions-013/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): docs/api/, docs/cerebro-llm/, docs/chat-texto/, docs/memoria-conversacional/, docs/rosto-do-robo/, docs/spec/, docs/voz/
