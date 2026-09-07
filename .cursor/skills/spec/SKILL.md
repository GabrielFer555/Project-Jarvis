---
name: spec
description: >-
  Monta o plano de task para o Project Jarvis (IA e robótica): pasta
  spec/task-{slug}-{NNN}/ na raiz com plano.md, regra-de-negocio.md e
  arquitetura.md, cabeçalho com branch base e modo de execução, requisitos,
  etapas técnicas, Gherkin, impacto nas funcionalidades já mapeadas em docs/
  e checklist de documentação com caminhos concretos. Não implementa código
  nem edita docs/. Use when the user pede um plano, spec, task, requisitos
  funcionais, ou qualquer solicitação de feature neste repositório. Não use
  para executar um plano existente (skill rock-it).
---

# Spec — plano de execução de task

Você é um especialista em IA e Robótica. Baseado na solicitação, **monte o plano de execução, documente a decisão e pare**. Não implemente código nem testes. A execução é exclusiva da skill [rock-it](../rock-it/SKILL.md).

Documentar a decisão faz parte do planejamento: a regra de negócio e a arquitetura da feature nascem **agora**, junto com o plano, porque são o que o plano decide. O que a spec **não** faz é mexer na documentação viva do projeto (`docs/`): isso ela planeja, e o rock-it executa.

| Arquivo | Quando nasce | Quem escreve |
| --- | --- | --- |
| `spec/task-{slug}-{NNN}/plano.md` | Planejamento | spec |
| `spec/task-{slug}-{NNN}/regra-de-negocio.md` | Planejamento | spec |
| `spec/task-{slug}-{NNN}/arquitetura.md` | Planejamento | spec |
| `docs/<funcionalidade>/*` | Execução | rock-it, conforme o checklist do plano |
| `README.md`, `docs/progresso.md` | Execução | rock-it |
| `src/`, `tests/` | Execução | rock-it |

Os arquivos da pasta da task são o **registro daquela decisão, congelado no tempo**. A fonte viva de cada funcionalidade é `docs/<funcionalidade>/`.

## Quando aplicar

Toda solicitação de feature, correção, integração ou mudança neste repositório. Produza o plano **e aguarde** `/rock-it`. Não espere o usuário pedir o documento.

- Pedido de feature **sem** plano → gerar a pasta da task e parar.
- Pedido de **executar / implementar** um plano que já existe → não usar esta skill; isso é a skill `rock-it`.
- Pedido de implementar **sem** plano → gerar o plano e parar (não implementar).

## Fase 1 — inventário e impacto (antes de escrever qualquer arquivo)

Nenhum plano é escrito antes deste levantamento. Planejar sem ler a regra vigente é como reescrever a funcionalidade do zero.

1. Ler o índice [docs/README.md](../../../docs/README.md) e listar as pastas `docs/<funcionalidade>/`.
2. Identificar quais módulos de `src/` a feature toca e a qual funcionalidade mapeada eles pertencem.
3. Ler o `regra-de-negocio.md` e o `arquitetura.md` da(s) funcionalidade(s) afetada(s). A regra vigente é insumo obrigatório: o plano precisa dizer **o que ela passa a ser**, não ignorá-la.
4. Ler [docs/padroes-de-implementacao.md](../../../docs/padroes-de-implementacao.md) — padrões e stack vigentes do projeto.
5. Classificar cada doc de `docs/` em uma das três colunas abaixo e registrar isso no plano.

| Situação | Decisão | Exemplo |
| --- | --- | --- |
| A feature toca funcionalidade já mapeada | **Atualizar** a pasta existente, por profunda que seja a mudança | Mexer no cérebro atualiza `docs/cerebro-llm/`; não cria `docs/cerebro-groq/` |
| Capacidade nova, sem pasta que a cubra | **Criar** `docs/<nova>/regra-de-negocio.md` e `arquitetura.md`, e registrar no índice | Locomoção, memória vetorial, visão |
| Funcionalidade não relacionada | **Não tocar**; listar como não impactada | Feature de voz não mexe em `docs/spec/` |

- Nunca criar pasta paralela para uma funcionalidade que já existe, mesmo que a tecnologia mude por completo.
- Na dúvida entre criar e atualizar, **atualizar**.
- Mudança de comportamento interno não justifica doc nova: justifica doc atualizada.

## Cabeçalho (obrigatório)

- **Branch base**: branch a partir da qual o trabalho parte (detectar via git; em geral `main`)
- **Modo de execução**: `non stop` ou `parada por execução` — vale para o **rock-it**, não para esta skill
- **Progresso**: gravar `0/N etapas` no `plano.md`. Esta skill **não** atualiza o contador depois disso

Se o usuário não disser o modo, use **non stop**.

| Modo | Comportamento (na skill rock-it) |
| --- | --- |
| `non stop` | Executa todas as etapas sem pausar, salvo dúvida impeditiva |
| `parada por execução` | Entrega uma etapa, para e espera confirmação antes da próxima |

## Corpo do documento (obrigatório)

1. **Descrição breve da tarefa**
2. **Requisitos funcionais**
3. **Impacto nas funcionalidades mapeadas** — o que muda na regra vigente de cada `docs/<funcionalidade>/` afetada
4. **Implementação técnica** segregada por etapas, com snapshots de código *somente em casos importantes*
5. **Casos de teste utilizando linguagem de Gherkin**

## Etapas obrigatórias no plano (rock-it cumpre; spec não)

Incluir no `plano.md` para a skill `rock-it` executar depois:

- **Cobertura com testes unitários e integração** (somente se houver necessidade)
- **Fora de escopo / não coberto**
- **Dúvidas impeditivas**
- **Documentação**: uma etapa própria, com os caminhos concretos de `docs/` a atualizar ou criar, o README e o `docs/progresso.md`

A etapa de documentação do plano nunca diz "atualizar a documentação": diz qual arquivo, e o que nele muda.

## Stack obrigatória

Os padrões vigentes estão em [docs/padroes-de-implementacao.md](../../../docs/padroes-de-implementacao.md); o plano respeita esse arquivo sem substituir tecnologia por equivalente. Resumo:

- Postgres para bancos vetoriais
- Python 3.11
- LangChain
- Modelos de IA da Groq (cérebro, via LangChain). Artefatos de voz (Whisper, Piper) podem vir do Hugging Face Hub.

Rodar e instalar com `py -3.11` (neste repo, `py` sem versão aponta para 3.14).

## Evitar

- **Não implementar**: sem editar `src/`, `tests/`, `README.md` nem `docs/progresso.md`
- **Não editar `docs/`**: nem atualizar funcionalidade mapeada, nem criar pasta nova, nem mexer em `docs/padroes-de-implementacao.md`. A spec só **planeja** essas mudanças
- **Não** gerar `padroes-de-implementacao.md` por feature: os padrões são um arquivo único do projeto. O que é contrato da feature (assinaturas, variáveis de ambiente, eventos) vai na seção `## Contratos` do `arquitetura.md` da task
- **Não** marcar etapas como `[Concluído]` nem avançar o **Progresso**
- **Não** invocar a skill `rock-it` sozinho; só informar o usuário
- Não criar cenários de testes redundantes no Gherkin
- Não incluir no plano implementação extra ou "melhorias" não pedidas

## Pasta da task (obrigatório)

Toda task **cria** uma pasta na raiz do repositório:

```
spec/task-{slug}-{NNN}/
├── plano.md
├── regra-de-negocio.md
└── arquitetura.md
```

- `{slug}`: kebab-case curto da tarefa (ex.: `cerebro-llm`, `rosto-do-robo`)
- `{NNN}`: número sequencial de 3 dígitos, **único no repositório** (`001`, `002`, …)

Como obter `{NNN}`:

1. Listar pastas `spec/task-*` na raiz.
2. Extrair o sufixo `-\d{3}$` de cada nome.
3. `NNN` = maior valor encontrado + 1; se não houver nenhuma pasta, usar `001`.
4. Não reutilizar número. Não reiniciar a contagem por slug.

Templates dos três arquivos: [reference.md](reference.md).

O progresso da execução (contador `N/M etapas` e `[Concluído]` / `[Reaberto]`) é atualizado pelo **rock-it** no próprio `plano.md`. O diário do projeto continua em `docs/progresso.md`.

Pastas de tasks antigas não são migradas quando o formato muda; elas são registro histórico.

## Fluxo

1. Detectar branch base (`git branch --show-current` / `git rev-parse --abbrev-ref HEAD`).
2. Fazer a **Fase 1** (inventário e impacto): índice, docs afetadas, padrões vigentes.
3. Calcular o próximo `{NNN}` e gravar `spec/task-{slug}-{NNN}/` com `plano.md`, `regra-de-negocio.md` e `arquitetura.md`. Publicar o `plano.md` no chat.
4. Se **Dúvidas impeditivas** não estiver vazio: **parar**, listar as dúvidas, esperar resposta. Não inventar. Não pedir `/rock-it` até as dúvidas serem resolvidas e o plano atualizado.
5. Caso contrário: **parar**. Informar os caminhos gravados e pedir para o usuário chamar a skill `rock-it` (`/rock-it`).
6. Não executar etapas, não escrever testes, não tocar `src/`, `README.md`, `docs/progresso.md` nem `docs/`.

## Formato do plano

Usar exatamente esta estrutura no chat e em `spec/task-{slug}-{NNN}/plano.md`:

```markdown
# Spec: <título curto>

## Cabeçalho

- **Branch base:** <branch>
- **Modo de execução:** non stop | parada por execução
- **Progresso:** 0/N etapas

## Descrição breve da tarefa

<1–3 frases>

## Requisitos funcionais

- RF1: ...
- RF2: ...

## Impacto nas funcionalidades mapeadas

| Funcionalidade | Doc | Regra vigente | Passa a valer |
| --- | --- | --- | --- |
| <nome> | `docs/<slug>/regra-de-negocio.md` | <o que vale hoje> | <o que muda> |

Nova funcionalidade: <sim, criar `docs/<slug>/`> ou <não, atualiza a existente>.
Não impactadas: `docs/<outra>/`, `docs/<outra>/`.

## Implementação técnica

### Etapa 1 — <nome>

<o que muda, arquivos, decisões>

Snapshots de código somente se o trecho for crítico (API frágil, contrato, algoritmo).

### Etapa 2 — <nome>

...

### Etapa N — documentação

- `docs/<slug>/regra-de-negocio.md`: <o que muda>
- `docs/<slug>/arquitetura.md`: <o que muda>
- `README.md`: <o que muda>
- `docs/progresso.md`: seção datada

## Casos de teste (Gherkin)

Feature: <nome>
  Scenario: <caso distinto, não redundante>
    Given ...
    When ...
    Then ...

## Cobertura com testes unitários e integração

<o que será testado e por quê> ou <não necessário: motivo>

## Fora de escopo / não coberto

- ...

## Dúvidas impeditivas

<lista> ou `Nenhuma.`

## Documentação

- [ ] README.md — <o que muda>
- [ ] docs/progresso.md — seção datada
- [ ] docs/<funcionalidade-mapeada>/regra-de-negocio.md — atualizar: <regra que muda>
- [ ] docs/<funcionalidade-mapeada>/arquitetura.md — atualizar: <componente que muda>
- [ ] docs/<nova-funcionalidade>/ — criar (somente se capacidade nova) + índice em docs/README.md
- [ ] docs/padroes-de-implementacao.md — só se a task mudar padrão do projeto
- [x] spec/task-<slug>-<NNN>/regra-de-negocio.md — gravado pela spec
- [x] spec/task-<slug>-<NNN>/arquitetura.md — gravado pela spec

Docs não impactadas (não tocar): docs/<outras>/
```

Linhas que não se aplicam saem do checklist. Não deixar item genérico ou placeholder para o rock-it adivinhar.

## Regras que o plano impõe à execução (rock-it)

- Escopo fechado: só requisitos listados. Sem extras, refactors ou "melhorias" não pedidas.
- Snapshots de código no plano: raros. Preferir descrição de arquivos e responsabilidades.
- Gherkin: um cenário por comportamento distinto. Não duplicar o mesmo fluxo com dados cosméticos.
- Testes automatizados: só quando houver necessidade (lógica ramificada, contrato, regressão). Não criar testes que só espelham o cenário Gherkin sem assert útil.
- Dúvida impeditiva = falta dado sem o qual a implementação fica adivinhação (API, hardware, regra de negócio, credencial, decisão de arquitetura). Preferência de estilo não é impeditiva.
- Documentação viva: o rock-it atualiza só os arquivos de `docs/` listados no checklist, mexendo apenas no que a task mudou. Doc fora do checklist não é tocada.
- Divergência: se a implementação sair do que o plano decidiu, o rock-it corrige também `regra-de-negocio.md` e `arquitetura.md` da pasta da task, para o registro não mentir.

## Encerramento desta skill

Depois de gravar os três arquivos, a resposta ao usuário deve:

1. Confirmar os caminhos (`spec/task-{slug}-{NNN}/plano.md`, `regra-de-negocio.md`, `arquitetura.md`)
2. Dizer qual documentação de `docs/` o plano prevê atualizar ou criar
3. Dizer que **nada foi implementado** e que `docs/` não foi tocado
4. Pedir a skill **rock-it** (`/rock-it`) para executar o plano

## Projeto

Robô conversacional (STT → LLM → TTS + locomoção). Código em `src/`. Planos e decisões por task em `spec/task-{slug}-{NNN}/`. Documentação viva das funcionalidades em `docs/`. Histórico em `docs/progresso.md`. Visão e como rodar no README.
