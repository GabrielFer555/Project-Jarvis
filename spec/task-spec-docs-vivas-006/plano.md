# Spec: docs vivas e documentação no planejamento

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 7/7 etapas

## Descrição breve da tarefa

Refatorar a skill `spec` para que a regra de negócio e a arquitetura da feature nasçam no planejamento, na pasta da task, e para que o plano diga com caminho concreto qual documentação de `docs/` a execução deve atualizar ou criar. O `padroes-de-implementacao.md` deixa de existir por feature e passa a ser um arquivo único do projeto.

## Requisitos funcionais

- RF1: A skill `spec` grava três arquivos em `spec/task-{slug}-{NNN}/`: `plano.md`, `regra-de-negocio.md` e `arquitetura.md`.
- RF2: A skill `spec` não gera `padroes-de-implementacao.md` por feature. Os padrões vigentes ficam em `docs/padroes-de-implementacao.md`, arquivo único; contrato de feature (assinaturas, variáveis de ambiente, eventos) vai na seção `## Contratos` do `arquitetura.md`.
- RF3: Antes de escrever qualquer arquivo, a spec inventaria `docs/`: índice, docs das funcionalidades afetadas e padrões vigentes. A regra vigente é insumo obrigatório do plano.
- RF4: A spec classifica o impacto em três situações — atualizar funcionalidade mapeada, criar pasta para capacidade nova, não tocar — e registra a classificação no plano. Na dúvida entre criar e atualizar, atualizar.
- RF5: Feature que mexe em funcionalidade já mapeada nunca cria pasta paralela em `docs/`, por profunda que seja a mudança.
- RF6: O checklist de documentação do plano tem caminhos concretos, com o que muda em cada arquivo, e a lista das docs não impactadas.
- RF7: A spec continua sem tocar `src/`, `tests/`, `README.md`, `docs/progresso.md` e `docs/`; a documentação viva é planejada por ela e escrita pelo `rock-it`.
- RF8: O `rock-it` lê `docs/padroes-de-implementacao.md` na Fase 0, atualiza em `docs/` só o que o checklist listou e não recria a regra e a arquitetura da pasta da task, exceto se a implementação divergiu do plano.

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| Spec e execução de tasks | `docs/spec/regra-de-negocio.md` | Spec só grava `plano.md`; regra, arquitetura e padrões são criados pelo rock-it no encerramento | Spec grava plano, regra e arquitetura da task e planeja as docs de `docs/`; rock-it executa a documentação viva |
| Spec e execução de tasks | `docs/spec/arquitetura.md` | Dois lugares de doc sem papel definido; padrões por feature | `docs/` é canônico, pasta da task é registro congelado, padrões num arquivo único |
| Cérebro LLM | `docs/cerebro-llm/*` | Descrevia `HuggingFaceEndpoint`, `HF_TOKEN` e `HF_MODEL` | Groq (`ChatGroq`, `GROQ_API_KEY`, `GROQ_MODEL`) e instruções em `src/agent/instructions.md`, como o código já está desde a task 004 |
| Rosto do robô | `docs/rosto-do-robo/arquitetura.md` | Contratos e decisões moravam no `padroes-de-implementacao.md` da feature | Contratos e decisões dentro do `arquitetura.md` |

Nova documentação: `docs/padroes-de-implementacao.md` (padrões do projeto) e `docs/README.md` (índice do mapa de funcionalidades).

Não impactadas: `src/`, `tests/`, pastas de tasks 001–004.

## Implementação técnica

### Etapa 1 — padrões globais [Concluído]

Criar `docs/padroes-de-implementacao.md` consolidando os três arquivos por feature: convenções, stack obrigatória, comandos, formato do plano, contratos de documentação, testes e decisões do projeto.

Antes de apagar, mover o que é específico da feature para o `arquitetura.md` correspondente, em `## Contratos`. Remover `docs/spec/padroes-de-implementacao.md`, `docs/rosto-do-robo/padroes-de-implementacao.md` e `docs/cerebro-llm/padroes-de-implementacao.md`.

### Etapa 2 — refatorar a skill spec [Concluído]

`.cursor/skills/spec/SKILL.md`: fase de inventário e impacto, tabela de quem escreve o quê, três arquivos na pasta da task, seção **Evitar** invertida (proíbe editar `docs/`, permite gravar a decisão da task), seção de impacto no corpo do plano e checklist de documentação com caminhos concretos.

### Etapa 3 — templates [Concluído]

`.cursor/skills/spec/reference.md`: remover o template de `padroes-de-implementacao.md`; `regra-de-negocio.md` ganha `## Impacto nas regras existentes`; `arquitetura.md` ganha `## Contratos` e `## Decisões`; acrescentar a regra de atualizar-ou-criar, o formato do índice e como atualizar sem reescrever.

### Etapa 4 — alinhar o rock-it [Concluído]

`.cursor/skills/rock-it/SKILL.md`: Fase 0 lê o padrões global e as docs que o checklist vai tocar; Fase 5 atualiza `docs/` conforme o plano, não recria a regra e a arquitetura da task e corrige esses arquivos só em caso de divergência. Gate de teste passa de `pytest` para `unittest`, que é o que o repositório usa.

### Etapa 5 — reconciliar o cérebro [Concluído]

Atualizar `docs/cerebro-llm/regra-de-negocio.md` e `arquitetura.md` para o estado real: Groq via LangChain, `GROQ_API_KEY` / `GROQ_MODEL`, instruções e guardrails em `src/agent/instructions.md`, fala entre `<<<` e `>>>`, resposta falada só do `content`.

### Etapa 6 — documentação do processo [Concluído]

Atualizar `docs/spec/regra-de-negocio.md` e `docs/spec/arquitetura.md`; criar `docs/README.md` com o índice das funcionalidades mapeadas e a lista do que ainda não tem documentação.

### Etapa 7 — fechamento [Concluído]

README (links do topo, árvore de `docs/`, decisões), `docs/progresso.md` com seção datada, registro desta task em `spec/task-spec-docs-vivas-006/` e alinhamento do checklist do plano da task 005, que ainda não foi executada.

## Casos de teste (Gherkin)

Feature: planejamento com documentação viva
  Scenario: feature que toca funcionalidade mapeada
    Given a solicitação mexe no cérebro do robô
    When a skill spec monta o plano
    Then o plano lista `docs/cerebro-llm/` para atualização
    And nenhuma pasta nova é criada em `docs/`
    And a regra vigente do cérebro aparece na seção de impacto

  Scenario: capacidade nova
    Given a solicitação adiciona locomoção, sem pasta correspondente em `docs/`
    When a skill spec monta o plano
    Then o plano prevê criar `docs/locomocao/` com regra e arquitetura
    And prevê a linha nova no índice `docs/README.md`

  Scenario: documentação não relacionada
    Given a solicitação mexe só na voz
    When a skill spec monta o plano
    Then `docs/spec/` e `docs/rosto-do-robo/` aparecem como não impactadas
    And o plano não prevê alteração nelas

  Scenario: decisão registrada no planejamento
    Given qualquer solicitação de feature
    When a skill spec termina
    Then a pasta da task tem `plano.md`, `regra-de-negocio.md` e `arquitetura.md`
    And não tem `padroes-de-implementacao.md`
    And nada em `src/`, `tests/` ou `docs/` foi modificado

Feature: execução conforme o checklist
  Scenario: rock-it na fase de documentação
    Given um plano com checklist de documentação preenchido
    When o rock-it chega à Fase 5
    Then só os arquivos de `docs/` do checklist são alterados
    And a regra e a arquitetura da pasta da task não são recriadas

  Scenario: implementação divergiu do plano
    Given um achado do Reviewer que muda a decisão de arquitetura
    When a correção é aplicada
    Then o rock-it atualiza também a regra e a arquitetura da pasta da task

## Cobertura com testes unitários e integração

Não necessário: a task muda apenas contrato de skills e documentação em markdown. Não há código em `src/` para testar, e os testes existentes (`tests/test_brain.py`, `tests/test_settings.py`, `tests/test_face.py`) não são afetados. O gate `compileall` + `unittest` continua sendo a verificação.

## Fora de escopo / não coberto

- Criar `docs/voz/` para wake word, STT e TTS: o mapa de `docs/` segue incompleto de propósito; documentar código existente é outra task.
- Migrar as pastas das tasks 001–004 para o formato novo: são registro histórico.
- Qualquer mudança em `src/` ou `tests/`.
- Executar a task 005 (chat por texto): só o checklist de documentação dela foi alinhado.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [x] README.md — links do topo, árvore de `docs/`, decisões
- [x] docs/progresso.md — seção datada
- [x] docs/spec/regra-de-negocio.md — atualizar: spec grava três arquivos e planeja as docs vivas
- [x] docs/spec/arquitetura.md — atualizar: papéis de `docs/` e da pasta da task, novo fluxo
- [x] docs/cerebro-llm/regra-de-negocio.md — atualizar: Groq e instruções em markdown
- [x] docs/cerebro-llm/arquitetura.md — atualizar: componentes, contratos e decisões do cérebro atual
- [x] docs/rosto-do-robo/arquitetura.md — atualizar: contratos e decisões vindos do padrões por feature
- [x] docs/padroes-de-implementacao.md — criar: padrões únicos do projeto
- [x] docs/README.md — criar: índice do mapa de funcionalidades
- [x] spec/task-spec-docs-vivas-006/regra-de-negocio.md — gravado pela spec
- [x] spec/task-spec-docs-vivas-006/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): nenhuma pasta de `docs/` ficou de fora nesta task, por ela mudar o próprio contrato de documentação.
