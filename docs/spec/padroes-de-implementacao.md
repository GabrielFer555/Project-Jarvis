# Padrões de implementação — Spec

Alinhado ao que o repositório já usa: texto curto em português, tabelas, árvore de pastas, seções datadas no progresso, decisões registradas no README.

A skill spec **só escreve** `plano.md`. Código, testes e docs da feature são da skill rock-it.

## Convenções

- Interpretador: `py -3.11` (na execução, rock-it)
- Sem dependência fora da stack da task: Postgres (vetores), Python 3.11, LangChain, Groq no cérebro; Hugging Face Hub só para artefatos STT/TTS
- Escopo fechado: só o que está nos requisitos funcionais
- Código novo em `src/`, no pacote da etapa (`voice`, `agent`, `memory`, `hardware`, `vision`, `robot`) — só via rock-it
- `src/main.py` permanece ponto de entrada fino (hoje só chama `run_listen_repeat()`)

## Formato do plano

Cabeçalho:

- Branch base
- Modo de execução (`non stop` ou `parada por execução`) — para o rock-it
- Progresso `0/N etapas` (spec inicializa; rock-it atualiza)

Corpo:

- Descrição breve da tarefa
- Requisitos funcionais
- Implementação técnica por etapas (snapshot de código só se for importante)
- Casos de teste em Gherkin

Etapas obrigatórias **no plano** (rock-it cumpre):

- Cobertura com testes unitários e integração (somente se houver necessidade)
- Fora de escopo / não coberto
- Dúvidas impeditivas
- Documentação (README, `docs/progresso.md`, `spec/task-{slug}-{NNN}/`)

## Contratos de documentação

Quem atualiza README e progresso é o **rock-it** (Fase 5), com os templates de `.cursor/skills/spec/reference.md`.

**README.md** — tabela de Progresso, “O que já funciona”, Como rodar, árvore em Estrutura, Decisões, Próximo passo.

**docs/progresso.md** — nova seção `## AAAA-MM-DD` com `### Etapa N — nome`, o que mudou, arquivos (tabela quando fizer sentido), problemas e correções. No final, **Estado atual** e **Próximo passo**.

**spec/task-{slug}-{NNN}/** — pasta na raiz, número sequencial único (`001`, `002`, …):

| Arquivo | Quem cria | Conteúdo |
| --- | --- | --- |
| `plano.md` | spec | Plano; progresso `N/M etapas` atualizado pelo rock-it |
| `regra-de-negocio.md` | rock-it | Objetivo, comportamento, entradas/saídas, exceções, fora de escopo |
| `arquitetura.md` | rock-it | Contexto no pipeline, componentes, fluxo em texto, dados, dependências |
| `padroes-de-implementacao.md` | rock-it | Convenções, contratos, testes, decisões |

## Testes

Gherkin: um `Scenario` por comportamento distinto. Não repetir o mesmo fluxo com dados cosméticos. Spec só descreve; rock-it escreve testes se o plano exigir.

Automatizados (unitário/integração) só com lógica ramificada, contrato ou regressão. Se não houver necessidade, dizer isso na spec e não criar `tests/` vazio de propósito.

## Evitar

- Spec não implementa (código, testes, README, progresso, docs da feature)
- Spec não invoca rock-it sozinha
- Não criar cenários de teste redundantes no plano
- Não incluir no plano implementação extra ou “melhoria” não pedida

## Decisões

| Decisão | Motivo |
| --- | --- |
| Spec só gera o plano | Separar contrato e execução; rock-it é o orquestrador multi-agent |
| Plano antes do código | Mesma disciplina das etapas TTS/STT: validar o recorte antes de misturar no loop |
| `non stop` como padrão | No rock-it, só pausa quando falta dado impeditivo |
| Docs da feature na pasta da task | Regra, arquitetura e padrões ficam com o plano; o progresso do projeto continua sendo o diário |
| Número sequencial `001`, `002`, … | Uma pasta por task, ordem cronológica na raiz, sem colisão de slug |
| `py -3.11` obrigatório | `py` sem versão abre 3.14, sem as dependências do projeto |
| Postgres + LangChain + Groq no cérebro | Stack fechada: memória vetorial em Postgres; LLM na Groq via LangChain; Hub só para Whisper/Piper |
