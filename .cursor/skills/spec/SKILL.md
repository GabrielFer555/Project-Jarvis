---
name: spec
description: >-
  Monta o plano de task para o Project Jarvis (IA e robótica): pasta
  spec/task-{slug}-{NNN}/plano.md na raiz, cabeçalho com branch base e modo de
  execução, requisitos, etapas técnicas, Gherkin, testes só se necessário,
  fora de escopo, dúvidas impeditivas e checklist de documentação. Não
  implementa. Use when the user pede um plano, spec, task, requisitos
  funcionais, ou qualquer solicitação de feature neste repositório. Não use
  para executar um plano existente (skill rock-it).
---

# Spec — plano de execução de task

Você é um especialista em IA e Robótica. Baseado na solicitação, **monte o plano de execução e pare**. Não implemente código, testes nem documentação além do `plano.md`. A execução é exclusiva da skill [rock-it](../rock-it/SKILL.md).

## Quando aplicar

Toda solicitação de feature, correção, integração ou mudança neste repositório. Produza o plano **e aguarde** `/rock-it`. Não espere o usuário pedir o documento.

- Pedido de feature **sem** plano → gerar `plano.md` e parar.
- Pedido de **executar / implementar** um plano que já existe → não usar esta skill; isso é a skill `rock-it`.
- Pedido de implementar **sem** plano → gerar o plano e parar (não implementar).

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
3. **Implementação técnica** segregada por etapas, com snapshots de código *somente em casos importantes*
4. **Casos de teste utilizando linguagem de Gherkin**

## Etapas obrigatórias no plano (rock-it cumpre; spec não)

Incluir no `plano.md` para a skill `rock-it` executar depois:

- **Cobertura com testes unitários e integração** (somente se houver necessidade)
- **Fora de escopo / não coberto**
- **Dúvidas impeditivas**
- **Documentação**: atualizar README e `docs/progresso.md`; criar regra de negócio, arquitetura e padrões na **mesma pasta da task** (`spec/task-{slug}-{NNN}/`)

## Stack obrigatória

O plano deve respeitar, sem substituir por equivalentes (o rock-it também):

- Postgres para bancos vetoriais
- Python 3.11
- LangChain
- Modelos de IA da Groq (cérebro, via LangChain). Artefatos de voz (Whisper, Piper) podem vir do Hugging Face Hub.

Rodar e instalar com `py -3.11` (neste repo, `py` sem versão aponta para 3.14).

## Evitar

- **Não implementar nada**: sem editar `src/`, `tests/`, README, `docs/progresso.md`, nem criar `regra-de-negocio.md` / `arquitetura.md` / `padroes-de-implementacao.md`
- **Não** marcar etapas como `[Concluído]` nem avançar o **Progresso**
- **Não** invocar a skill `rock-it` sozinho; só informar o usuário
- Não criar cenários de testes redundantes no Gherkin
- Não incluir no plano implementação extra ou “melhorias” não pedidas

## Pasta da task (obrigatório)

Toda task **cria** uma pasta na raiz do repositório:

```
spec/task-{slug}-{NNN}/
```

- `{slug}`: kebab-case curto da tarefa (ex.: `cerebro-llm`, `rosto-do-robo`)
- `{NNN}`: número sequencial de 3 dígitos, **único no repositório** (`001`, `002`, …)

Como obter `{NNN}`:

1. Listar pastas `spec/task-*` na raiz.
2. Extrair o sufixo `-\d{3}$` de cada nome.
3. `NNN` = maior valor encontrado + 1; se não houver nenhuma pasta, usar `001`.
4. Não reutilizar número. Não reiniciar a contagem por slug.

Esta skill grava **somente** `plano.md`. Os outros arquivos da pasta nascem na Fase 5 do rock-it:

| Arquivo | Quem cria |
| --- | --- |
| `plano.md` | spec (sempre, **antes** de qualquer implementação) |
| `regra-de-negocio.md` | rock-it (encerramento) |
| `arquitetura.md` | rock-it (encerramento) |
| `padroes-de-implementacao.md` | rock-it (encerramento) |

O progresso da execução (contador `N/M etapas` e `[Concluído]` / `[Reaberto]`) é atualizado pelo **rock-it** no próprio `plano.md`. O diário do projeto continua em `docs/progresso.md`.

Pastas antigas em `docs/<slug>/` (ex.: `docs/cerebro-llm/`) não são migradas.

## Fluxo

1. Detectar branch base (`git branch --show-current` / `git rev-parse --abbrev-ref HEAD`).
2. Calcular o próximo `{NNN}` e criar `spec/task-{slug}-{NNN}/plano.md` com o plano no formato deste skill (cabeçalho + corpo + etapas obrigatórias). Publicar o mesmo conteúdo no chat.
3. Se **Dúvidas impeditivas** não estiver vazio: **parar**, listar as dúvidas, esperar resposta. Não inventar. Não pedir `/rock-it` até as dúvidas serem resolvidas e o plano atualizado.
4. Caso contrário: **parar**. Informar o caminho do `plano.md` e pedir para o usuário chamar a skill `rock-it` (`/rock-it`).
5. Não executar etapas. Não escrever testes. Não atualizar README nem `docs/progresso.md`. Templates de docs da feature: [reference.md](reference.md) (usados pelo rock-it).

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

## Implementação técnica

### Etapa 1 — <nome>

<o que muda, arquivos, decisões>

Snapshots de código somente se o trecho for crítico (API frágil, contrato, algoritmo).

### Etapa 2 — <nome>

...

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

- [ ] README.md
- [ ] docs/progresso.md
- [ ] spec/task-<slug>-<NNN>/regra-de-negocio.md
- [ ] spec/task-<slug>-<NNN>/arquitetura.md
- [ ] spec/task-<slug>-<NNN>/padroes-de-implementacao.md
```

## Regras que o plano impõe à execução (rock-it)

- Escopo fechado: só requisitos listados. Sem extras, refactors ou “melhorias” não pedidas.
- Snapshots de código no plano: raros. Preferir descrição de arquivos e responsabilidades.
- Gherkin: um cenário por comportamento distinto. Não duplicar o mesmo fluxo com dados cosméticos.
- Testes automatizados: só quando houver necessidade (lógica ramificada, contrato, regressão). Não criar testes que só espelham o cenário Gherkin sem assert útil.
- Dúvida impeditiva = falta dado sem o qual a implementação fica adivinhação (API, hardware, regra de negócio, credencial, decisão de arquitetura). Preferência de estilo não é impeditiva.
- Documentação da funcionalidade: três arquivos na pasta `spec/task-{slug}-{NNN}/`, junto com o `plano.md`. Não juntar tudo num único markdown se a feature tiver regra, arquitetura e padrões.

## Encerramento desta skill

Depois de gravar o `plano.md`, a resposta ao usuário deve:

1. Confirmar o caminho (`spec/task-{slug}-{NNN}/plano.md`)
2. Dizer que **nada foi implementado**
3. Pedir a skill **rock-it** (`/rock-it`) para executar o plano

## Projeto

Robô conversacional (STT → LLM → TTS + locomoção). Código em `src/`. Planos em `spec/task-{slug}-{NNN}/plano.md`. Histórico em `docs/progresso.md`. Visão e como rodar no README.
