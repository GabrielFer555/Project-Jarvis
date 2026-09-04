# Arquitetura — Pasta de plano por task

## Contexto

A spec não entra no fluxo de áudio do robô. Ela organiza o trabalho em volta dele. Cada task passa a ter um diretório próprio na raiz, em vez de `docs/specs/<slug>.md` e `docs/<slug>/`.

```
solicitação → spec/task-{slug}-{NNN}/plano.md → implementação em src/ → testes (se necessário) → docs na mesma pasta
```

O fluxo do produto continua o mesmo:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↓
                 locomoção / sensores
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Skill spec | `.cursor/skills/spec/SKILL.md` | Formato do plano, numeração, stack |
| Templates | `.cursor/skills/spec/reference.md` | README, progresso e os três arquivos na pasta da task |
| Contrato do processo | `docs/spec/` | Como a spec funciona (estável) |
| Pasta da task | `spec/task-{slug}-{NNN}/` | Plano, progresso da execução, docs da feature |
| Skill rock-it | `.cursor/skills/rock-it/` | Executa o `plano.md` da pasta |
| Histórico do robô | `docs/progresso.md` | Diário por data |
| Código | `src/` | Implementação da etapa |

## Fluxo

```
pedido do usuário
        │
        ▼
detectar branch base + modo
        │
        ▼
listar spec/task-* → NNN = max+1 (ou 001)
        │
        ▼
criar spec/task-{slug}-{NNN}/plano.md
        │
        ├── dúvidas impeditivas? ──► parar e perguntar
        │
        ▼
executar etapas (non stop | parada por execução)
        │
        ▼
atualizar README + docs/progresso.md
gravar regra/arquitetura/padrões na pasta da task
```

## Dados

A spec em si não persiste estado além de arquivos markdown. Numeração é derivada dos nomes das pastas já existentes.

## Dependências

- Python 3.11 (`py -3.11`), quando a task tocar código
- LangChain, Hugging Face, Postgres: só se a task usar
