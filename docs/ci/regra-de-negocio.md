# Regra de negócio — Pipeline GitHub Actions

## Objetivo

Todo pull request dirigido a `main` ou `develop` é barrado automaticamente se o código em `src/` não compilar ou se algum teste `unittest` falhar. O run deixa um artifact XML com o resultado dos testes, inclusive quando eles falham.

O CI não substitui o gate local (`py -3.11 -m compileall src` e `unittest discover`). Replica o mesmo critério no GitHub, para o revisor não depender da máquina de quem abriu o PR.

## Comportamento

- Disparo: evento `pull_request` com base `main` ou `develop`, nos tipos `opened`, `synchronize` e `reopened`. Abrir o PR e empurrar commits no head reexecutam o job. Push direto, merge e PR contra outra branch **não** disparam.
- Ordem fixa: instalar dependências → **build** (`compileall` em `src/`) → **todos** os testes em `tests/` → **publicar** o XML como artifact `test-results`.
- Build verde: `src/` gera bytecode sem erro. Build vermelho: job failed; testes não rodam.
- Testes: `unittest` via descoberta em `tests/`. Relatório JUnit XML escrito em `test-results/`. Um TestCase falho ou um erro de import no discover deixa o job failed.
- Artifact: os `*.xml` de `test-results/` sobem com `actions/upload-artifact` mesmo se os testes falharam. Se o build quebrou e não há XML, o upload não adiciona uma segunda falha.
- Sem `pytest`. Sem chamar Groq, Postgres, microfone ou TTS de verdade. Sem secrets no workflow.
- A ausência da branch `develop` no remoto não quebra o workflow: ela só passa a receber PRs quando existir.
- `test-results/` está no `.gitignore`: XML gerado localmente (ou copiado do runner) não é versionado.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Evento `pull_request` (opened / synchronize / reopened) | GitHub, base `main` ou `develop` | Run do workflow `CI` | Checks do PR |
| Árvore do head do PR | `actions/checkout` | Código em `src/` e `tests/` | Job `build-test` |
| `requirements.txt` | Raiz do repo | Ambiente Python 3.11 no runner | Passo de testes |
| Resultado de `compileall src` | Stdlib | Job segue ou falha | Passo de testes (só se verde) |
| Resultado dos TestCase | `tests/` via `xmlrunner` | XML JUnit + exit code | Artifact `test-results`; status do check |
| Artifact `test-results` | `test-results/*.xml` | ZIP baixável no run | Revisor / histórico do Actions |
| `test-results/` | Working tree (runner ou cópia local) | Entrada no `.gitignore` | Git não versiona o XML |

## Exceções

- PR cujo base não é `main` nem `develop`: o workflow não inicia.
- `compileall` falha: testes pulados; job failed; upload com `if-no-files-found: ignore`.
- Teste falho ou erro na descoberta: job failed; XML (se gerado) ainda é publicado.
- `sounddevice` sem PortAudio no Ubuntu: import de `voice`/`main` quebra — o job instala `libportaudio2` antes do pip para não tratar isso como falha de produto.
- Timeout de 30 minutos: job cancelled; XML publicado só se o passo de testes chegou a escrever arquivos.

## Fora de escopo

- Criar a branch `develop`.
- Rodar em `push` para `main`/`develop`.
- Anotação JUnit no PR, coverage, lint, cache de pip, matrix de SO.
- Secrets, Postgres, Docker ou rede real no job.
- Mudar testes, `src/` ou `requirements.txt` (exceto o pip extra `unittest-xml-reporting` **no runner**).
