# Templates de documentação (skill spec)

Ler este arquivo **somente na Fase 5 da skill rock-it** (documentação). A skill spec não usa estes templates: ela só grava `plano.md`.

Atualizar README e `docs/progresso.md`; criar os três arquivos na pasta da task (`spec/task-{slug}-{NNN}/`), junto com o `plano.md` já existente.

`{slug}`: kebab-case da funcionalidade (ex.: `cerebro-llm`, `memoria-vetorial`). `{NNN}`: próximo número sequencial de 3 dígitos (ver skill).

## README.md

Atualizar só o que a task mudou: tabela de Progresso, “O que já funciona”, Como rodar, estrutura de pastas, próximo passo. Não reescrever o documento inteiro.

## docs/progresso.md

Acrescentar seção datada no mesmo estilo existente (`## AAAA-MM-DD`, `### Etapa N — nome`, o que mudou, problemas e correções se houver). Atualizar **Estado atual** e **Próximo passo** no final.

Não apagar histórico anterior.

## spec/task-{slug}-{NNN}/regra-de-negocio.md

```markdown
# Regra de negócio — <funcionalidade>

## Objetivo

<o que o robô passa a fazer ou deixar de fazer>

## Comportamento

- ...

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## Exceções

- ...

## Fora de escopo

- ...
```

## spec/task-{slug}-{NNN}/arquitetura.md

```markdown
# Arquitetura — <funcionalidade>

## Contexto

<onde a peça entra no fluxo microfone → STT → LLM → TTS / locomoção>

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| ... | `src/...` | ... |

## Fluxo

```
<diagrama texto>
```

## Dados

<Postgres / vetores / arquivos / cache — só o que a task usa>

## Dependências

- Python 3.11
- LangChain (se aplicável)
- Groq (cérebro: `GROQ_MODEL`)
- Hugging Face Hub (artefatos STT/TTS, se aplicável)
- Postgres (se aplicável)
```

## spec/task-{slug}-{NNN}/padroes-de-implementacao.md

```markdown
# Padrões de implementação — <funcionalidade>

## Convenções

- Interpretador: `py -3.11`
- Sem dependências fora da stack obrigatória da task

## Contratos

<funções, assinaturas, eventos — só o introduzido nesta task>

## Testes

<o que cobrir ou “não aplicável”>

## Decisões

| Decisão | Motivo |
| --- | --- |
| ... | ... |
```
