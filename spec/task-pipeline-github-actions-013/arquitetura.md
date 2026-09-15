# Arquitetura — Pipeline GitHub Actions

## Contexto

A pipeline não entra no fluxo microfone → STT → LLM → TTS. Ela valida o mesmo código que esse fluxo usa, no GitHub, antes do merge em `main` ou `develop`.

```
PR (base: main | develop)
        → checkout
        → Python 3.11 + requirements.txt + xmlrunner
        → compileall src          # build
        → xmlrunner discover      # unittest + XML
        → upload-artifact         # test-results/*.xml
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Workflow | `.github/workflows/ci.yml` | Trigger, job único, ordem dos passos |
| Runner | `ubuntu-latest` | Python 3.11, apt `libportaudio2` |
| Build | `python -m compileall src` | Mesmo critério local; sem empacotar |
| Testes | `python -m xmlrunner discover -s tests -v -o test-results` | unittest do repo + XML JUnit |
| Relator XML | pacote `unittest-xml-reporting` (pip só no job) | Substitui `python -m unittest` no CI para haver arquivo XML |
| Artifact | `actions/upload-artifact@v4` | Publica `test-results/*.xml` como `test-results` |
| Ignore | `.gitignore` (`test-results/`) | Relatório local não entra no git |

Nenhum módulo em `src/` muda.

## Fluxo

```
pull_request (opened | synchronize | reopened)
        │
        ├── base ∉ {main, develop}  → workflow não dispara
        └── base ∈ {main, develop}
                │
                ▼
        job build-test (ubuntu-latest, 30 min)
                │
                ├── checkout
                ├── apt libportaudio2
                ├── setup-python 3.11
                ├── pip: requirements.txt + unittest-xml-reporting
                │
                ▼
        compileall src
                ├── falha → job failed; testes não rodam; upload ignore se sem XML
                └── ok
                        │
                        ▼
                xmlrunner discover -s tests -o test-results
                        ├── falha → job failed
                        └── ok    → job segue verde
                        │
                        ▼
                upload-artifact (if: always())
                        name: test-results
                        path: test-results/*.xml
```

## Contratos

```yaml
# .github/workflows/ci.yml
on.pull_request.types: [opened, synchronize, reopened]
on.pull_request.branches: [main, develop]
permissions.contents: read
jobs.build-test.runs-on: ubuntu-latest
jobs.build-test.timeout-minutes: 30

# passos de produto (nessa ordem, depois de checkout/python/deps)
Build:  python -m compileall src
Test:   python -m xmlrunner discover -s tests -v -o test-results
Publish:
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results/*.xml
    if-no-files-found: ignore
```

| Chave | Papel |
| --- | --- |
| *(nenhuma env de produto)* | O job não lê `GROQ_*` nem `POSTGRES_*` |
| Artifact `test-results` | ZIP dos XML JUnit da execução |

O formato do XML é o JUnit que o `xmlrunner` grava (arquivos `TEST-*.xml` em `test-results/`). Não há API Python nova.

## Dados

Nenhum banco, vetor ou cache. O único artefato persistido no GitHub é o ZIP do XML, com a retenção padrão do Actions.

`test-results/` no working tree do runner (e, se alguém rodar xmlrunner local, na máquina) não é fonte de verdade do produto.

## Dependências

- Python 3.11 (`actions/setup-python`)
- `requirements.txt` (inclui LangChain, Groq client, Piper, faster-whisper, SQLAlchemy — necessários porque testes importam `main` / `voice` / `agent`)
- `unittest-xml-reporting` **somente no job**
- `libportaudio2` no Ubuntu (`sounddevice`)
- Actions: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`

Não entra: pytest, framework web, Postgres no runner, Hugging Face Hub no job (os testes não baixam modelo).

## Decisões

| Decisão | Motivo |
| --- | --- |
| Um job com passos em sequência | Build, testes e XML compartilham o mesmo ambiente; três jobs só atrasariam |
| Trigger só em PR para `main` e `develop`, com `synchronize` | Pedido do PR dirigido a essas branches; commits novos precisam revalidar |
| `compileall` como build | Já é o build do repo (Python puro) |
| `xmlrunner` em vez de pytest `--junitxml` | pytest não é dependência; unittest é o runner vigente |
| `unittest-xml-reporting` só no runner | Relatório XML é necessidade do CI, não do robô em runtime |
| Artifact mesmo se testes falharem | O XML importa sobretudo no vermelho |
| Actions oficiais, sem reporter de PR | O requisito é publicar artifact XML, não anotar o PR |
| `libportaudio2` no Ubuntu | Import existente de `voice`/`main` nos testes carrega `sounddevice` |
| Não criar `develop` nesta task | O YAML pode listar a branch antes dela existir |
| Sem cache de pip / matrix | Fora do pedido; pipeline básico |
