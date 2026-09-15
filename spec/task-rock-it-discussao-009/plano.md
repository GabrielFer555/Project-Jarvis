# Spec: Registro de discussão no rock-it

## Cabeçalho

- **Branch base:** main
- **Modo de execução:** non stop
- **Progresso:** 0/5 etapas

## Descrição breve da tarefa

A skill rock-it passa a gravar, na pasta da task, um arquivo com o ponto de vista de cada agent, os debates e a decisão de cada escolha. O Product Manager passa a revisar também o `regra-de-negocio.md` de cada feature envolvida. O Dev Reviewer passa a revisar também o `arquitetura.md`.

## Requisitos funcionais

- RF1: Em toda execução, o Orquestrador cria `spec/task-{slug}-{NNN}/discussao.md` na Fase 0 e o atualiza até o encerramento.
- RF2: O arquivo registra o ponto de vista de cada agent chamado (PM, Dev Implementador, Dev Reviewer, QA), mesmo quando não há debate.
- RF3: Cada debate registra as posições, as evidências, as rodadas e a decisão (procede, refutado, parcial, ou levado ao usuário), com o motivo.
- RF4: O Orquestrador é o único que escreve em `discussao.md`. Os subagents não editam esse arquivo.
- RF5: O Product Manager, além da revisão atual dos requisitos funcionais, revisa `spec/task-{slug}-{NNN}/regra-de-negocio.md` e o `docs/<funcionalidade>/regra-de-negocio.md` de cada funcionalidade listada no impacto do plano.
- RF6: O Dev Reviewer, além da revisão atual do código, revisa `spec/task-{slug}-{NNN}/arquitetura.md` e o `docs/<funcionalidade>/arquitetura.md` de cada funcionalidade listada no impacto do plano.
- RF7: A skill spec continua gravando só os três arquivos do planejamento. Ela não cria `discussao.md`; apenas descreve que o rock-it o acrescenta na execução.

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| Spec e execução de tasks | `docs/spec/regra-de-negocio.md` | Pasta da task tem plano, regra e arquitetura (spec). PM revisa RFs e impacto. Reviewer revisa código. Debates ficam só no chat. | Rock-it grava `discussao.md` na pasta da task. PM revisa também a regra de negócio da task e a de cada feature impactada. Reviewer revisa também a arquitetura da task e a de cada feature impactada. Debates e decisões vão para o arquivo. |
| Spec e execução de tasks | `docs/spec/arquitetura.md` | Pasta da task: três arquivos da spec. Protocolo de debate sem persistência. | Quarto arquivo `discussao.md` (rock-it). Template e protocolo no rock-it. Personas PM e Reviewer com escopo ampliado. |

Nova funcionalidade: não, atualiza a existente (`docs/spec/`).
Não impactadas: `docs/cerebro-llm/`, `docs/chat-texto/`, `docs/rosto-do-robo/`.

## Implementação técnica

### Etapa 1 — protocolo do Orquestrador e template de `discussao.md`

Alterar `.cursor/skills/rock-it/SKILL.md` e criar `.cursor/skills/rock-it/reference.md` (template do arquivo).

Fase 0: depois de localizar o plano, criar `spec/task-{slug}-{NNN}/discussao.md` se ainda não existir, com o cabeçalho do template. Não recriar se o arquivo já existir (retomada).

Depois de cada retorno de subagent, o Orquestrador anexa a seção correspondente: ponto de vista, debate (se houver) e decisão. Continua registrando no chat; o arquivo é a persistência.

Despachos seguintes incluem o caminho de `discussao.md` no prompt, para o agent não contradizer decisão já registrada.

Protocolo de debate: a frase que hoje manda registrar só no chat passa a mandar gravar também em `discussao.md`. Resposta do usuário a um impasse entra no arquivo como decisão.

Tabela de Papéis: Orquestrador passa a ter `discussao.md` na saída; PM e Reviewer passam a ter os markdowns extras na entrada.

Quem escreve: só o Orquestrador. O prompt das personas continua com "Não altere arquivo nenhum" no PM, Reviewer e QA.

### Etapa 2 — persona Product Manager

Alterar `.cursor/skills/rock-it/personas/product-manager.md`. Manter a revisão atual (RFs, impacto, checklist). Acrescentar:

1. Ler `spec/task-{slug}-{NNN}/regra-de-negocio.md` e confrontar com os RFs: a regra cobre os requisitos; nenhum RF ficou de fora; a regra não inventa requisito.
2. Para cada linha da seção "Impacto nas funcionalidades mapeadas", ler `docs/<funcionalidade>/regra-de-negocio.md`. A coluna "Regra vigente" é o que o arquivo diz hoje; "Passa a valer" não contradiz regra que continua valendo.
3. Funcionalidade nova, ainda sem pasta em `docs/`: revisar só a regra da task.
4. Inconsistência de regra entra na lista numerada no mesmo formato já usado (requisito, evidência, por quê, pergunta objetiva).

O prompt recebe os caminhos concretos dos `regra-de-negocio.md` a ler (task + cada feature impactada). O Orquestrador preenche esses caminhos na Fase 1 a partir da tabela de impacto.

### Etapa 3 — persona Dev Reviewer

Alterar `.cursor/skills/rock-it/personas/dev-reviewer.md`. Manter a ordem atual (RFs, segurança, padrões, Python). Acrescentar depois disso:

1. Ler `spec/task-{slug}-{NNN}/arquitetura.md` e confrontar componentes, fluxo, contratos e decisões com o diff. Achado se o código viola o contrato da task ou se a arquitetura descreve peça que o plano pedia e o código não entregou.
2. Para cada funcionalidade impactada, ler `docs/<funcionalidade>/arquitetura.md` vigente. Achado se a implementação contradiz arquitetura viva que o plano não disse que mudaria.
3. Funcionalidade nova, ainda sem pasta em `docs/`: revisar só a arquitetura da task.
4. Achado de arquitetura usa a mesma classificação (Bloqueante / Relevante / Observação).

O prompt recebe os caminhos concretos dos `arquitetura.md` a ler. O Orquestrador preenche na Fase 3.

### Etapa 4 — alinhar skill spec

Alterar `.cursor/skills/spec/SKILL.md` e `.cursor/skills/spec/reference.md` só o suficiente para o contrato da pasta não mentir:

- Spec continua gravando `plano.md`, `regra-de-negocio.md` e `arquitetura.md`.
- A pasta da task, depois da execução, também tem `discussao.md`, escrito pelo rock-it.
- Spec não cria `discussao.md` e não espera que ele exista no planejamento.

Não mudar o fluxo da spec, o inventário, nem os templates de regra e arquitetura.

### Etapa 5 — documentação

- `docs/spec/regra-de-negocio.md`: comportamento do rock-it (arquivo de discussão; escopo do PM e do Reviewer)
- `docs/spec/arquitetura.md`: componente `discussao.md`, fluxo com persistência do debate, contratos do arquivo e das personas
- `docs/padroes-de-implementacao.md`: pasta da task passa a listar `discussao.md` como artefato da execução
- `README.md`: estrutura de `spec/task-{slug}-{NNN}/` e a decisão "Spec planeja, rock-it executa" mencionam o registro de discussão
- `docs/progresso.md`: seção datada

## Casos de teste (Gherkin)

Feature: Registro de discussão no rock-it

  Scenario: Orquestrador cria o arquivo na preparação
    Given existe um plano em `spec/task-{slug}-{NNN}/plano.md`
    And a pasta da task ainda não tem `discussao.md`
    When o rock-it executa a Fase 0
    Then o arquivo `spec/task-{slug}-{NNN}/discussao.md` existe com o cabeçalho do template

  Scenario: Ponto de vista é gravado mesmo sem debate
    Given o Product Manager devolveu "Requisitos consistentes."
    When o Orquestrador registra o retorno
    Then `discussao.md` contém o ponto de vista do Product Manager
    And contém a decisão de seguir para a Fase 2
    And não contém seção de debate

  Scenario: Debate e decisão ficam no arquivo
    Given o Product Manager apontou uma inconsistência
    And o Dev Implementador refutou com evidência
    When o Orquestrador encerra o debate
    Then `discussao.md` contém a posição dos dois
    And contém a decisão (refutado) e o motivo

  Scenario: Impasse vai ao usuário e a resposta entra no registro
    Given duas rodadas de debate sem consenso
    When o Orquestrador leva as duas posições ao usuário e o usuário responde
    Then `discussao.md` contém as duas posições
    And contém a decisão do usuário

  Scenario: Product Manager revisa a regra de negócio das features
    Given o plano lista funcionalidades impactadas em `docs/`
    When o Product Manager é despachado na Fase 1
    Then o prompt inclui `spec/task-{slug}-{NNN}/regra-de-negocio.md`
    And inclui o `docs/<funcionalidade>/regra-de-negocio.md` de cada funcionalidade impactada
    And a revisão dos requisitos funcionais continua obrigatória

  Scenario: Dev Reviewer revisa a arquitetura
    Given a implementação da última etapa passou no gate
    When o Dev Reviewer é despachado na Fase 3
    Then o prompt inclui o diff e `spec/task-{slug}-{NNN}/arquitetura.md`
    And inclui o `docs/<funcionalidade>/arquitetura.md` de cada funcionalidade impactada
    And a revisão de código, segurança e padrões continua obrigatória

  Scenario: Spec não cria o arquivo de discussão
    Given um pedido de feature sem plano
    When a skill spec grava a pasta da task
    Then a pasta contém `plano.md`, `regra-de-negocio.md` e `arquitetura.md`
    And a pasta não contém `discussao.md`

## Cobertura com testes unitários e integração

Não necessário: a mudança é de processo em markdown (skills e personas). Não há lógica em `src/` nem contrato executável para assert. O gate (`compileall` + `unittest`) continua rodando nas etapas; não se criam testes novos só para espelhar o Gherkin.

## Fora de escopo / não coberto

- Migrar pastas de tasks antigas para incluir `discussao.md`.
- Alterar a persona de QA além de o Orquestrador registrar o retorno dela no arquivo.
- Spec gerar `discussao.md` vazio no planejamento.
- Ferramenta ou script para validar o formato do arquivo.
- Mudança em `src/`, `tests/` ou em `docs/cerebro-llm/`, `docs/chat-texto/`, `docs/rosto-do-robo/`.

## Dúvidas impeditivas

Nenhuma.

## Documentação

- [ ] README.md — estrutura de `spec/task-{slug}-{NNN}/` inclui `discussao.md`; decisão "Spec planeja, rock-it executa" menciona o registro de discussão
- [ ] docs/progresso.md — seção datada desta task
- [ ] docs/spec/regra-de-negocio.md — atualizar: pasta da task ganha `discussao.md` na execução; PM revisa regra de negócio das features; Reviewer revisa arquitetura
- [ ] docs/spec/arquitetura.md — atualizar: componente e fluxo do registro de discussão; contratos do arquivo e das personas
- [ ] docs/padroes-de-implementacao.md — pasta da task lista `discussao.md` como artefato do rock-it
- [x] spec/task-rock-it-discussao-009/regra-de-negocio.md — gravado pela spec
- [x] spec/task-rock-it-discussao-009/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): docs/cerebro-llm/, docs/chat-texto/, docs/rosto-do-robo/
