# Spec: Spec só gera o plano

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 4/4 etapas

## Descrição breve da tarefa

A skill spec deixa de implementar. Ela só cria `spec/task-{slug}-{NNN}/plano.md` e espera o usuário chamar a skill rock-it. Código, testes, README, `docs/progresso.md` e os três arquivos de docs da feature passam a ser exclusivos do rock-it.

## Requisitos funcionais

- RF1: Spec não edita `src/`, `tests/`, README, `docs/progresso.md`, nem cria regra/arquitetura/padrões da feature.
- RF2: Depois de gravar o `plano.md` sem dúvidas impeditivas, spec para e pede `/rock-it`.
- RF3: Com dúvidas impeditivas, spec para e não pede rock-it até o plano ser resolvido.
- RF4: O modo `non stop` / `parada por execução` permanece no cabeçalho para o rock-it, não para a spec.
- RF5: Pedido de implementar sem plano → spec gera o plano e para (não implementa).
- RF6: Pedido de executar plano existente → skill rock-it, não spec.

## Implementação técnica

### Etapa 1 — skill spec [Concluído]

Reescrever `.cursor/skills/spec/SKILL.md`: descrição sem “executa”, fluxo termina no `plano.md`, seção Evitar proíbe implementação, encerramento obrigatório pedindo rock-it.

### Etapa 2 — reference e rock-it [Concluído]

`reference.md` só na Fase 5 do rock-it. Rock-it deixa explícito que spec não implementa e que sem `plano.md` não há execução.

### Etapa 3 — contrato docs/spec [Concluído]

Atualizar regra, arquitetura e padrões em `docs/spec/` para o fluxo `spec → parar → /rock-it`.

### Etapa 4 — pasta desta task, README e progresso [Concluído]

Criar `spec/task-spec-somente-plano-002/` e registrar a mudança no README e em `docs/progresso.md`.

## Casos de teste (Gherkin)

Feature: spec não implementa
  Scenario: feature nova sem plano
    Given uma solicitação de feature
    When a skill spec roda
    Then existe `spec/task-{slug}-{NNN}/plano.md`
    And nenhum arquivo em `src/` foi alterado
    And a resposta pede `/rock-it`

  Scenario: dúvidas impeditivas
    Given o plano tem dúvidas impeditivas não vazias
    When a skill spec termina
    Then ela não pede `/rock-it`

## Cobertura com testes unitários e integração

Não necessário: mudança só em markdown/skills.

## Fora de escopo / não coberto

- Alterar o fluxo interno das fases do rock-it (PM, Dev, Reviewer, QA)
- Migrar pastas antigas `docs/cerebro-llm/` e `docs/rosto-do-robo/`
- Código do robô em `src/`

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md
- [x] docs/progresso.md
- [x] spec/task-spec-somente-plano-002/regra-de-negocio.md
- [x] spec/task-spec-somente-plano-002/arquitetura.md
- [x] spec/task-spec-somente-plano-002/padroes-de-implementacao.md
