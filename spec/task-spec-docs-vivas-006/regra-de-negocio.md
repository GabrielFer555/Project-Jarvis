# Regra de negócio — Docs vivas no planejamento

## Objetivo

A regra de negócio e a arquitetura de uma feature passam a nascer no planejamento, junto com o plano, porque são o que o plano decide. E o plano passa a dizer, com caminho concreto, qual documentação viva de `docs/` a execução deve atualizar ou criar — em vez de um item genérico "documentação".

## Comportamento

- A skill `spec` grava três arquivos em `spec/task-{slug}-{NNN}/`: `plano.md`, `regra-de-negocio.md` e `arquitetura.md`. Esses arquivos são o registro da decisão daquela task, congelado no tempo.
- `padroes-de-implementacao.md` não é mais gerado por feature: as convenções eram as mesmas em toda task. Os padrões vigentes ficam em `docs/padroes-de-implementacao.md`; o que é contrato da feature (assinaturas, variáveis de ambiente, eventos) vai na seção `## Contratos` do `arquitetura.md`.
- Antes de escrever, a spec inventaria `docs/`: índice `docs/README.md`, docs das funcionalidades que a feature toca e `docs/padroes-de-implementacao.md`. A regra vigente entra no plano na seção de impacto, dizendo o que ela **passa a ser**.
- Classificação obrigatória de cada documentação: atualizar funcionalidade mapeada, criar pasta para capacidade nova, ou não tocar. Na dúvida entre criar e atualizar, atualizar.
- Funcionalidade mapeada nunca ganha pasta paralela, mesmo trocando a tecnologia por completo: o cérebro saiu do Hugging Face e foi para a Groq e continua sendo `docs/cerebro-llm/`.
- A spec não edita `docs/`, `src/`, `tests/`, `README.md` nem `docs/progresso.md`. A documentação viva é planejada aqui e escrita pelo `rock-it`, que só mexe no que o checklist listou.
- `docs/` é a fonte canônica de como cada funcionalidade se comporta hoje. Divergindo da pasta de uma task, vale `docs/`.

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/spec/regra-de-negocio.md` | "Spec não cria `regra-de-negocio.md` / `arquitetura.md` / `padroes-de-implementacao.md`"; os três nascem no encerramento do rock-it | Spec grava regra e arquitetura da task no planejamento; padrões por feature deixam de existir; rock-it escreve a documentação viva de `docs/` |
| `docs/spec/arquitetura.md` | Pasta da task e `docs/<slug>/` sem papel definido, com cópias equivalentes | `docs/` é canônico e vivo; pasta da task é registro congelado |
| `docs/cerebro-llm/*` | Cérebro descrito como Hugging Face Inference (`HF_TOKEN`, `HF_MODEL`) | Groq via LangChain (`GROQ_API_KEY`, `GROQ_MODEL`) e guardrails em `src/agent/instructions.md` |
| `docs/rosto-do-robo/*` | Contratos e decisões do rosto no `padroes-de-implementacao.md` da feature | Mesmos contratos e decisões dentro do `arquitetura.md` |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Solicitação da feature | Usuário | `plano.md` com seção de impacto e checklist concreto | Pasta da task |
| Índice e docs das funcionalidades | `docs/README.md`, `docs/<slug>/` | Classificação atualizar / criar / não tocar | Plano |
| Padrões vigentes | `docs/padroes-de-implementacao.md` | Etapas técnicas dentro da stack | Plano |
| Decisão da feature | Planejamento | `regra-de-negocio.md`, `arquitetura.md` | Pasta da task |
| Checklist de documentação | Plano | Docs vivas atualizadas ou criadas | `docs/`, na execução |

## Exceções

- Plano que veio só do chat, sem passar pela spec: o `rock-it` grava a regra e a arquitetura da task na Fase 5, com os templates.
- Implementação que diverge do plano (achado do Reviewer, falha do QA): o `rock-it` corrige também a regra e a arquitetura da pasta da task, para o registro não mentir.
- Doc de `docs/` fora do checklist não é tocada, mesmo parecendo desatualizada: isso vira outra task.
- Task que mude um padrão do projeto precisa listar `docs/padroes-de-implementacao.md` no checklist; sem isso, o arquivo não muda.

## Fora de escopo

- Documentar em `docs/` código que já existe e nunca foi mapeado (voz: wake word, STT, TTS).
- Migrar pastas de tasks antigas para o formato novo.
- Qualquer mudança em `src/` ou `tests/`.
- Automatizar a checagem de que o checklist do plano foi cumprido.
