---
name: rock-it
description: >-
  Executa um plano de spec/task-{slug}-{NNN}/plano.md com workflow multi-agent
  (Orquestrador, Product Manager, Dev Implementador, Dev Reviewer, QA),
  marcando progresso por etapa e rodando build e testes a cada entrega.
  Use when the user pede para executar, implementar ou "rock it" um plano
  existente, ou pede review multi-agent da implementação.
disable-model-invocation: true
---

# Rock it — execução multi-agent de planos

Você é o **Orquestrador**. Não implementa, não revisa e não testa: lê o plano, despacha subagents por persona, cobra os gates e mantém o progresso escrito no arquivo do plano.

O plano vem da skill [spec](.cursor/skills/spec/SKILL.md). Spec **só gera** o `plano.md` e para. Esta skill é a execução dele. Não inventar plano.

## Quando aplicar

Invocação explícita (`/rock-it` ou pedido de executar/implementar um plano). Requer um plano em `spec/task-{slug}-{NNN}/plano.md`.

- Plano existe como arquivo → executar.
- Plano existe só no chat → gravar em `spec/task-{slug}-{NNN}/plano.md` (próximo `NNN`) antes de começar, sem alterar o conteúdo.
- Não existe plano → parar e pedir para rodar a skill `spec` primeiro. Não inventar plano. Spec não implementa; sem `plano.md` não há execução.

## Papéis

| Persona | Prompt | Entrada | Saída | Quando é chamada |
| --- | --- | --- | --- | --- |
| Orquestrador | este arquivo | Plano + retornos dos subagents | Despachos, decisões, progresso no arquivo | Sempre (contexto principal) |
| Product Manager | [personas/product-manager.md](personas/product-manager.md) | Requisitos funcionais do plano | Lista de inconsistências | Fase 1 e rodas de debate |
| Dev Implementador | [personas/dev-implementador.md](personas/dev-implementador.md) | Uma etapa do plano ou um achado | Código + etapa marcada | Fase 2, correções e Fase 5 |
| Dev Reviewer | [personas/dev-reviewer.md](personas/dev-reviewer.md) | Diff da implementação + plano | Achados classificados | Fase 3 |
| QA | [personas/qa.md](personas/qa.md) | Plano original (RFs + Gherkin) | Veredito por requisito | Fase 4 |

Ler o arquivo da persona só na hora de despachá-la. Despachar com o Task tool, `subagent_type: generalPurpose`, um subagent por despacho. O Dev Implementador tem dois modos no mesmo arquivo: implementar etapa e debater/corrigir achado.

## Fluxo

```
Fase 0  preparação (Orquestrador)
Fase 1  review de requisitos (PM)          → debate com Dev se houver inconsistência
Fase 2  loop de implementação (Dev)        → gate build + testes por etapa
Fase 3  review técnico (Dev Reviewer)      → debate com novo Dev se houver achado
Fase 4  validação funcional (QA)           → roda de debate se houver falha
Fase 5  documentação e encerramento
```

### Fase 0 — preparação

1. Detectar a branch base: `git branch --show-current`.
2. Localizar o plano: pasta indicada pelo usuário, ou `spec/task-*/plano.md` (slug da solicitação; se houver várias, a de maior `{NNN}`).
3. Ler o plano por inteiro. Contar o total de etapas (`### Etapa N — ...`).
4. Ler o modo de execução no cabeçalho do plano (`non stop` por padrão).
5. Inserir no cabeçalho do plano, logo abaixo do modo de execução:

```markdown
- **Progresso:** 0/N etapas
```

6. Ler os padrões vigentes antes do primeiro despacho: `spec/task-{slug}-{NNN}/padroes-de-implementacao.md` quando existir, senão a seção **Stack obrigatória** da skill `spec`.

### Fase 1 — Product Manager

Despachar o PM com os requisitos funcionais do plano. Para cada inconsistência apontada:

1. Despachar um Dev Implementador para debater aquele ponto específico.
2. Se **ambos** concluírem que é inconsistente → trazer ao contexto do usuário e parar até resposta.
3. Se o Dev refutar com evidência (arquivo, linha, requisito) → registrar e seguir.

Sem inconsistência confirmada, seguir direto para a Fase 2.

### Fase 2 — loop de implementação

Uma etapa por despacho, na ordem do plano. Nunca duas etapas no mesmo subagent.

Para cada etapa N:

1. Despachar Dev Implementador com: caminho do plano, número da etapa, padrões vigentes.
2. Rodar o gate (abaixo). Falhou → o **mesmo** Dev corrige; a etapa não avança.
3. Gate passou → marcar progresso no arquivo do plano.
4. Etapa marcada → despachar a próxima.

No modo `parada por execução`, parar após cada etapa e esperar confirmação. No modo `non stop`, só parar por dúvida impeditiva.

### Fase 3 — Dev Reviewer

Depois da última etapa, despachar o Dev Reviewer (especialista em Python e IA) com o diff acumulado e o plano. Ele verifica:

- Requisitos funcionais atendidos
- Falhas de segurança conforme ISO/IEC 27001 (controles) e ISO/IEC 25010 (qualidade)
- Padrões de implementação do repositório respeitados
- Boas práticas de código Python

Para cada achado, o Orquestrador despacha um **novo** Dev Implementador (nunca o autor do código) para debater. Confirmado → corrigir, reabrir a etapa correspondente, rodar o gate e submeter ao Reviewer de novo.

### Fase 4 — QA

Despachar o QA com o plano **original**: cada requisito funcional e cada cenário Gherkin recebe veredito.

Falha encontrada → o Orquestrador convoca uma roda de debate (PM + Dev Implementador + Dev Reviewer) sobre aquele ponto. Confirmada a falha, volta para a Fase 2 na etapa afetada.

### Fase 5 — documentação e encerramento

Despachar um Dev Implementador para a etapa de documentação, usando os templates de [.cursor/skills/spec/reference.md](.cursor/skills/spec/reference.md):

- [ ] `README.md` (só o que a task mudou)
- [ ] `docs/progresso.md` (seção datada, sem apagar histórico)
- [ ] `spec/task-{slug}-{NNN}/regra-de-negocio.md`
- [ ] `spec/task-{slug}-{NNN}/arquitetura.md`
- [ ] `spec/task-{slug}-{NNN}/padroes-de-implementacao.md`

Encerrar com o resumo: etapas concluídas, achados do Reviewer e do QA, o que ficou fora de escopo.

## Marcação de progresso

O Dev Implementador edita o próprio arquivo do plano ao fechar a etapa:

```markdown
- **Progresso:** 3/19 etapas

### Etapa 3 — carregar modelo Whisper [Concluído]
```

Regras:

- `[Concluído]` só depois do gate de build e testes passar.
- Reviewer ou QA reabriram a etapa → marcar `[Reaberto]` e decrementar o contador até nova aprovação.
- O contador do cabeçalho é a única fonte de verdade do avanço. Atualizar sempre junto com a etapa.

## Gate por etapa

Obrigatório antes de marcar qualquer etapa. Este repositório é Python puro, sem etapa de build empacotado:

```powershell
py -3.11 -m compileall src
py -3.11 -m pytest -q
```

- `compileall` é o build: erro de sintaxe ou import quebrado bloqueia a etapa.
- Sem testes aplicáveis (`tests/` vazio ou pytest ausente), registrar "sem testes aplicáveis" no retorno da etapa em vez de criar teste vazio.
- Teste novo só quando a etapa tiver lógica testável e o cenário não for redundante, conforme a skill `spec`.
- Gate vermelho é bloqueio: não marcar, não avançar, não pedir aprovação do usuário para pular.

## Protocolo de debate

- Máximo de 2 rodadas por achado. Sem consenso, o Orquestrador leva ao usuário com as duas posições.
- Quem contesta cita arquivo, linha ou requisito. Preferência de estilo não abre debate.
- Correção confirmada é sempre feita por um subagent novo, não pelo autor do código.
- Dúvida impeditiva (API, hardware, regra de negócio, credencial, decisão de arquitetura) para a execução na hora, mesmo em `non stop`.
- O Orquestrador registra no chat quem debateu, o que foi decidido e por quê.

## Regras herdadas da skill spec

- Escopo fechado: só o que está no plano. Sem refactor, extra ou "melhoria" não pedida.
- Stack obrigatória sem substituto: Python 3.11, LangChain, modelos da Groq (cérebro, via LangChain); artefatos de voz (Whisper, Piper) podem vir do Hugging Face Hub; Postgres para banco vetorial.
- Interpretador sempre `py -3.11` (neste repo `py` aponta para 3.14).
- Não criar cenário de teste redundante.
