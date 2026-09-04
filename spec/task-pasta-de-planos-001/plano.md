# Spec: Pasta de plano de execução por task

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 4/4 etapas

## Descrição breve da tarefa

O plano de execução deixa de ir para `docs/specs/<slug>.md`. Cada task ganha uma pasta na raiz, `spec/task-{tarefa}-{NNN}/`, com número sequencial (001, 002, …). Nessa pasta ficam o plano, o progresso da execução e a documentação da funcionalidade já pedida (regra, arquitetura, padrões). README e `docs/progresso.md` continuam na raiz/`docs/`.

## Requisitos funcionais

- RF1: Toda task cria (não só se o usuário pedir arquivo) a pasta `spec/task-{slug}-{NNN}/` na raiz do repositório.
- RF2: `{NNN}` é sequencial de 3 dígitos (001, 002, …), único no repositório, obtido pelo maior sufixo já existente + 1.
- RF3: O plano de execução é gravado em `spec/task-{slug}-{NNN}/plano.md`.
- RF4: Progresso da execução (contador e `[Concluído]`/`[Reaberto]`) fica nesse `plano.md`.
- RF5: A documentação da funcionalidade (regra de negócio, arquitetura, padrões) é criada na mesma pasta da task, não mais em `docs/<slug>/`.
- RF6: README e `docs/progresso.md` continuam sendo atualizados como antes.

## Implementação técnica

### Etapa 1 — skill spec e templates [Concluído]

Atualizar `.cursor/skills/spec/SKILL.md` e `reference.md`: caminho da pasta, regra de numeração, nome `plano.md`, checklist de docs na pasta da task.

### Etapa 2 — contrato em docs/spec e alinhamento rock-it [Concluído]

Atualizar `docs/spec/` (regra, arquitetura, padrões) e a skill rock-it (plano e docs da feature passam a ser lidos em `spec/task-*-*/`). Sem isso o orquestrador procuraria `docs/specs/`.

### Etapa 3 — pasta desta task [Concluído]

Criar `spec/task-pasta-de-planos-001/` com este `plano.md` e os três arquivos de documentação da mudança.

### Etapa 4 — README e progresso [Concluído]

Incluir `spec/` na árvore do README. Acrescentar seção datada em `docs/progresso.md`.

## Casos de teste (Gherkin)

Feature: pasta de plano por task
  Scenario: primeira task no repositório
    Given não existe nenhuma pasta `spec/task-*`
    When o agente monta o plano da task
    Then cria `spec/task-{slug}-001/plano.md`

  Scenario: task seguinte incrementa o número
    Given existe `spec/task-pasta-de-planos-001`
    When o agente monta o plano de outra task
    Then cria `spec/task-{outro-slug}-002/`, sem reutilizar 001

## Cobertura com testes unitários e integração

Não necessário: mudança só em markdown/skills, sem lógica em `src/`.

## Fora de escopo / não coberto

- Migrar `docs/cerebro-llm/` e `docs/rosto-do-robo/` para o novo layout
- Criar ferramenta/script de numeração (a skill descreve o algoritmo; o agente lista as pastas)
- Alterar comportamento do robô em `src/`

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md
- [x] docs/progresso.md
- [x] spec/task-pasta-de-planos-001/regra-de-negocio.md
- [x] spec/task-pasta-de-planos-001/arquitetura.md
- [x] spec/task-pasta-de-planos-001/padroes-de-implementacao.md
