# Padrões de implementação — Pasta de plano por task

## Convenções

- Interpretador: `py -3.11` (não usado nesta task; só markdown)
- Pasta na raiz: `spec/task-{slug}-{NNN}/`
- `{NNN}`: três dígitos, sequencial no repositório, nunca por slug
- Plano sempre em `plano.md`, criado antes do código
- Progresso da execução no `plano.md`; diário do projeto em `docs/progresso.md`

## Contratos

Nome da pasta: `task-` + kebab-case + `-` + três dígitos.

Algoritmo de `{NNN}`: listar `spec/task-*`, extrair sufixo `-\d{3}$`, `max + 1`, senão `001`.

Skill `rock-it` lê `spec/task-{slug}-{NNN}/plano.md`, não `docs/specs/`.

## Testes

Não aplicável (skills e markdown).

## Decisões

| Decisão | Motivo |
| --- | --- |
| Pasta na raiz `spec/`, não `docs/spec/` | `docs/spec/` já é o contrato do processo; a pasta da task é o artefato de cada pedido |
| Número global, não por slug | Ordem cronológica e pasta única por execução |
| Docs da feature junto do plano | Um lugar para plano, progresso da execução e regra/arquitetura/padrões |
| Não migrar `docs/cerebro-llm/` nem `docs/rosto-do-robo/` | Histórico já publicado; o layout vale daqui para frente |
