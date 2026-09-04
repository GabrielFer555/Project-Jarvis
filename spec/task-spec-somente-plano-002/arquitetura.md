# Arquitetura — Spec só gera o plano

## Contexto

A spec sai do caminho de implementação. O recorte da etapa continua o mesmo (uma peça do robô por vez); muda quem executa.

```
solicitação → spec (plano.md) → /rock-it → src/ + testes + docs
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| spec | `.cursor/skills/spec/SKILL.md` | Plano e pare |
| rock-it | `.cursor/skills/rock-it/SKILL.md` | Execução multi-agent |
| templates | `.cursor/skills/spec/reference.md` | Fase 5 do rock-it |
| contrato | `docs/spec/` | Processo estável |

## Fluxo

```
pedido
  → spec grava plano.md
  → parar
  → usuário chama /rock-it
  → implementação + docs
```

## Dados

Só markdown do plano. Sem estado extra.

## Dependências

As da stack da task, aplicadas na execução (rock-it): Python 3.11, LangChain, Hugging Face, Postgres se couber.
