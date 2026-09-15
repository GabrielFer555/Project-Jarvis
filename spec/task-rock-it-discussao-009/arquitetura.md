# Arquitetura — Registro de discussão no rock-it

## Contexto

Nada entra no fluxo de áudio do robô. A mudança é no processo de execução das tasks:

```
solicitação → spec (plano + regra + arquitetura) → parar
           → /rock-it → src/ + testes + docs/ + README + progresso
                      → discussao.md (pontos de vista, debates, decisões)
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Orquestrador | `.cursor/skills/rock-it/SKILL.md` | Cria e atualiza `discussao.md`; despacha personas; não implementa |
| Template do registro | `.cursor/skills/rock-it/reference.md` | Formato de `discussao.md` |
| Product Manager | `.cursor/skills/rock-it/personas/product-manager.md` | RFs + regra de negócio da task e das features impactadas |
| Dev Reviewer | `.cursor/skills/rock-it/personas/dev-reviewer.md` | Diff + arquitetura da task e das features impactadas |
| Dev Implementador | `.cursor/skills/rock-it/personas/dev-implementador.md` | Sem mudança de papel; debates continuam no Modo 2 |
| QA | `.cursor/skills/rock-it/personas/qa.md` | Sem mudança de papel; o retorno vai para `discussao.md` |
| Skill spec | `.cursor/skills/spec/SKILL.md`, `reference.md` | Continua gravando três arquivos; descreve o quarto como artefato do rock-it |
| Registro da execução | `spec/task-{slug}-{NNN}/discussao.md` | Ata daquela execução |

## Fluxo

```
Fase 0  Orquestrador cria/retoma discussao.md
Fase 1  PM (RFs + regra-de-negocio.md) → gravar ponto de vista
        inconsistência? → Dev debate → gravar posições e decisão
Fase 2  Dev implementa etapas (sem mudança neste fluxo)
Fase 3  Reviewer (código + arquitetura.md) → gravar ponto de vista
        achado? → Dev novo debate → gravar posições e decisão
Fase 4  QA → gravar ponto de vista
        falha? → roda de debate → gravar posições e decisão
Fase 5  documentação viva em docs/
        discussao.md já está completo; não é item do checklist de docs/
```

## Contratos

Pasta da task depois da execução:

```
spec/task-{slug}-{NNN}/
├── plano.md              # spec (progresso: rock-it)
├── regra-de-negocio.md   # spec
├── arquitetura.md        # spec
└── discussao.md          # rock-it
```

Quem escreve `discussao.md`: só o Orquestrador. Personas de leitura (PM, Reviewer, QA) não alteram arquivo nenhum.

Template mínimo (seções só existem quando aquele agent foi chamado):

```markdown
# Discussão — task-{slug}-{NNN}

## Fase 0 — Preparação

- Plano: `spec/task-{slug}-{NNN}/plano.md`
- Branch: <branch>
- Modo: <modo>

## Fase <N> — <persona ou debate>

### Ponto de vista — <persona>

<retorno fiel>

### Debate — <achado ou inconsistência>

**Product Manager | Dev Reviewer | QA:** <posição e evidência>
**Dev Implementador:** <posição e evidência>
**Rodada:** 1 | 2

### Decisão

- Resultado: procede | refutado | parcial | levado ao usuário
- Motivo: ...
- Quem decidiu: consenso dos agents | usuário
```

Caminhos que o Orquestrador injeta no prompt:

| Persona | Além do que já recebe | Arquivos novos |
| --- | --- | --- |
| Product Manager | RFs, plano, `src/`, `docs/` | `spec/task-.../regra-de-negocio.md`; `docs/<func>/regra-de-negocio.md` de cada linha da tabela de impacto |
| Dev Reviewer | Diff, plano, padrões | `spec/task-.../arquitetura.md`; `docs/<func>/arquitetura.md` de cada linha da tabela de impacto |
| Qualquer despacho após o primeiro | — | Caminho de `discussao.md` (leitura; não editar) |

Funcionalidade nova sem pasta em `docs/`: omitir os caminhos de `docs/<func>/` que ainda não existem.

## Dados

Nada além de markdown na pasta da task. Sem Postgres, LangChain ou Groq nesta peça.

## Dependências

- Nenhuma dependência de runtime: a mudança é de processo, em markdown
- Python 3.11 e `py -3.11` continuam valendo para o gate do rock-it (`compileall` + `unittest`) nas tasks que mexem em `src/`

## Decisões

| Decisão | Motivo |
| --- | --- |
| Arquivo na pasta da task, não em `docs/` | É ata daquela execução, congelada com o plano; `docs/` é a regra viva da funcionalidade |
| Nome `discussao.md` | Um arquivo por task, paralelo a `plano.md` |
| Orquestrador escreve; agents não | Subagent não vê o histórico; o Orquestrador é quem junta os retornos |
| Criar na Fase 0, append depois | Evita perder o primeiro retorno; retomada não apaga o que já foi gravado |
| PM lê regra da task e a vigente em `docs/` | "Cada feature" é a decisão sendo executada mais as regras vivas que o plano disse que mudam |
| Reviewer lê arquitetura da task e a vigente em `docs/` | O código precisa respeitar o contrato da task e não violar arquitetura viva que o plano não alterou |
| Spec não cria o arquivo | Não há discussão no planejamento |
| Sem teste automatizado | Não há lógica em `src/` para assert |
