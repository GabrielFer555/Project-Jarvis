# Regra de negócio — Registro de discussão no rock-it

## Objetivo

A execução de uma task deixa de ter os debates só no chat. Cada ponto de vista, cada debate e cada decisão ficam gravados na pasta da task. O Product Manager passa a julgar também a regra de negócio das features envolvidas. O Dev Reviewer passa a julgar também a arquitetura.

## Comportamento

- Em toda execução `/rock-it`, o Orquestrador cria `spec/task-{slug}-{NNN}/discussao.md` na Fase 0 (ou retoma o arquivo se já existir) e o atualiza até o encerramento.
- O arquivo registra o ponto de vista de cada agent chamado (Product Manager, Dev Implementador, Dev Reviewer, QA), mesmo quando o retorno é aprovação sem achado.
- Debate: posições, evidências (arquivo, linha ou requisito), número da rodada e decisão (procede, refutado, parcial, ou levado ao usuário), com o motivo. Resposta do usuário a um impasse entra no arquivo como decisão.
- Só o Orquestrador escreve em `discussao.md`. Subagents não editam esse arquivo.
- Despachos seguintes recebem o caminho do arquivo, para não contradizer decisão já registrada.
- Product Manager: mantém a revisão dos requisitos funcionais, do impacto e do checklist. Além disso, lê a regra de negócio da task e a regra vigente em `docs/<funcionalidade>/` de cada funcionalidade listada no impacto. Inconsistência de regra entra na mesma lista de inconsistências.
- Dev Reviewer: mantém a revisão de código, segurança, padrões e Python. Além disso, confronta a arquitetura da task e a arquitetura vigente das funcionalidades impactadas com o que foi implementado.
- Funcionalidade nova, ainda sem pasta em `docs/`: PM e Reviewer revisam só os arquivos da pasta da task.
- A skill spec continua gravando só `plano.md`, `regra-de-negocio.md` e `arquitetura.md`. Não cria `discussao.md`.

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/spec/regra-de-negocio.md` | Pasta da task: plano, regra e arquitetura gravados pela spec. Debates só no chat. PM revisa RFs. Reviewer revisa código. | Rock-it acrescenta `discussao.md`. PM revisa também regra de negócio das features. Reviewer revisa também arquitetura. |
| `docs/spec/arquitetura.md` | Três arquivos na pasta da task. Protocolo de debate sem persistência. | Quarto arquivo na execução. Template e protocolo no rock-it. Personas com entrada ampliada. |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Plano e decisão da task | `spec/task-{slug}-{NNN}/` | Cabeçalho de `discussao.md` | Pasta da task (Fase 0) |
| Retorno de cada subagent | Task tool | Ponto de vista, debate e decisão | `discussao.md` (append) |
| Regra de negócio da task e das features impactadas | Pasta da task + `docs/<funcionalidade>/` | Inconsistências de regra, se houver | Retorno do PM + `discussao.md` |
| Arquitetura da task e das features impactadas | Pasta da task + `docs/<funcionalidade>/` | Achados de arquitetura, se houver | Retorno do Reviewer + `discussao.md` |
| Resposta do usuário a impasse | Chat | Decisão registrada | `discussao.md` |

## Exceções

- Retomada: se `discussao.md` já existe, não recriar; só anexar.
- Sem debate: gravar ponto de vista e a decisão de seguir; não inventar seção de debate.
- Impacto vazio ou funcionalidade nova: PM e Reviewer não exigem arquivo em `docs/` que ainda não existe.
- Plano só no chat: o rock-it grava a pasta da task (plano, regra, arquitetura) como já faz, e cria `discussao.md` nessa mesma pasta.

## Fora de escopo

- Migrar tasks antigas para ter `discussao.md`.
- Mudar o papel do QA além de registrar o retorno dele no arquivo.
- Spec criar `discussao.md` no planejamento.
- Validação automática do formato do arquivo.
- Qualquer mudança no robô (`src/`, testes das funcionalidades mapeadas em `docs/cerebro-llm/`, `docs/chat-texto/`, `docs/rosto-do-robo/`).
