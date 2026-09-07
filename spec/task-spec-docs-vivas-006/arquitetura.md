# Arquitetura — Docs vivas no planejamento

## Contexto

Nada aqui entra no fluxo de áudio do robô: a mudança é no processo que produz as etapas do robô. O que muda é **quando** cada documento nasce e **quem** escreve nele.

```
antes:  spec → plano.md
        rock-it → src/ + testes + regra + arquitetura + padrões (na pasta da task)

agora:  spec → plano.md + regra-de-negocio.md + arquitetura.md (pasta da task)
             → checklist com os caminhos de docs/ a atualizar ou criar
        rock-it → src/ + testes + docs/<funcionalidade>/ + README + progresso
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Skill spec | `.cursor/skills/spec/SKILL.md` | Inventariar `docs/`, classificar impacto, gravar plano e decisão, parar |
| Templates | `.cursor/skills/spec/reference.md` | Formato da regra, da arquitetura, do índice e das atualizações de `docs/` |
| Skill rock-it | `.cursor/skills/rock-it/SKILL.md` | Executar o plano e a documentação viva do checklist |
| Padrões do projeto | `docs/padroes-de-implementacao.md` | Convenções, stack, comandos e decisões vigentes (arquivo único) |
| Índice | `docs/README.md` | Mapa funcionalidade → documentação → código; insumo do inventário |
| Documentação viva | `docs/<funcionalidade>/` | Como a funcionalidade se comporta hoje |
| Registro da task | `spec/task-{slug}-{NNN}/` | Plano e decisão daquela task, congelados |

## Fluxo

```
solicitação
    │
    ▼
spec: inventário (docs/README.md, docs/<afetadas>/, padroes-de-implementacao.md)
    │
    ▼
classificar: atualizar mapeada | criar nova | não tocar
    │
    ▼
gravar spec/task-{slug}-{NNN}/
   plano.md (impacto + checklist com caminhos)
   regra-de-negocio.md
   arquitetura.md
    │
    ▼
PARAR — pedir /rock-it
    │
    ▼
rock-it Fase 0: lê o plano, a decisão da task, os padrões e as docs do checklist
    │
    ▼
rock-it Fases 2–4: implementar, gate (compileall + unittest), review, QA
    │
    ▼
rock-it Fase 5: docs/<funcionalidade>/ do checklist + README + progresso
                (+ corrigir a decisão da task, se houve divergência)
```

## Contratos

Pasta da task:

```
spec/task-{slug}-{NNN}/
├── plano.md
├── regra-de-negocio.md
└── arquitetura.md
```

Checklist de documentação do plano: um item por arquivo, com caminho concreto e o que muda nele, mais a lista de docs não impactadas. Item marcado `[x]` é o que a própria spec já gravou.

Regra de decisão:

| Situação | Decisão |
| --- | --- |
| Toca funcionalidade mapeada | Atualizar a pasta existente |
| Capacidade nova | Criar `docs/<nova>/` + linha no índice |
| Não relacionada | Não tocar |

Seções que o `arquitetura.md` passa a ter, para absorver o que morava no padrões por feature: `## Contratos` (assinaturas, variáveis de ambiente, eventos) e `## Decisões` (decisões daquela funcionalidade).

## Dados

Nada persistido além dos arquivos markdown. Sem Postgres, LangChain ou Groq nesta peça.

## Dependências

- Nenhuma dependência de runtime: a mudança é de processo, em markdown
- Python 3.11 e `py -3.11` continuam valendo para o gate do rock-it (`compileall` + `unittest`)

## Decisões

| Decisão | Motivo |
| --- | --- |
| Regra e arquitetura gravadas no planejamento | São a decisão que o plano toma; escrever no fim é reconstruir de memória |
| Spec não edita `docs/` | Documentação viva acompanha código que existe, e código nasce no rock-it |
| `docs/` canônico, pasta da task congelada | Antes havia duas cópias equivalentes, livres para divergir |
| Padrões num arquivo único | Os três `padroes-de-implementacao.md` repetiam `py -3.11` e a mesma stack |
| Contratos dentro do `arquitetura.md` | Assinaturas e variáveis de ambiente precisavam de casa depois do padrões por feature sair |
| Índice `docs/README.md` | O inventário da spec precisa de uma lista confiável de funcionalidades mapeadas |
| Reconciliar `docs/cerebro-llm/` nesta task | Doc canônica desatualizada faria a próxima feature do cérebro partir de premissa errada |
| Gate com `unittest` | `pytest` não é dependência do projeto; os testes são `unittest` |
