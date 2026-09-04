# Arquitetura — Spec

## Contexto

A spec não entra no fluxo de áudio do robô. Ela só produz o contrato da etapa. Quem implementa é a skill rock-it:

```
solicitação → spec (plano.md) → parar → /rock-it → src/ + testes + docs
```

O fluxo do produto continua o mesmo:

```
microfone → STT → LLM (cérebro) → TTS → alto-falante
                      ↓
                 locomoção / sensores
```

Novas peças caem em `src/agent`, `src/memory`, `src/hardware`, `src/vision` ou `src/robot`, cada uma validada isoladamente, como as etapas de TTS e STT — **depois** do `/rock-it`.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Skill spec | `.cursor/skills/spec/SKILL.md` | Montar `plano.md` e parar |
| Templates de docs | `.cursor/skills/spec/reference.md` | Usados na Fase 5 do rock-it |
| Skill rock-it | `.cursor/skills/rock-it/SKILL.md` | Executar o plano (código, testes, docs) |
| Contrato da spec | `docs/spec/` | Regra de negócio, arquitetura e padrões deste processo |
| Pasta da task | `spec/task-{slug}-{NNN}/` | `plano.md` (spec); docs da feature (rock-it) |
| Histórico do robô | `docs/progresso.md` | O que já foi feito, por data (rock-it atualiza) |
| Visão e como rodar | `README.md` | Pipeline, estrutura, tabela de etapas, `py -3.11` |
| Código | `src/` | Implementação da etapa via rock-it |

## Fluxo

```
pedido do usuário
        │
        ▼
detectar branch base + modo
        │
        ▼
calcular NNN e criar spec/task-{slug}-{NNN}/plano.md
        │
        ├── dúvidas impeditivas? ──► parar e perguntar
        │
        ▼
PARAR — pedir /rock-it
        │
        ▼
(rock-it) executar etapas + testes se necessário
        │
        ▼
(rock-it) README + docs/progresso.md + docs na pasta da task
```

## Dados

A spec em si não persiste estado além do `plano.md`. Quando a task usar memória vetorial, o banco é **Postgres**. O cérebro (LLM) é **Groq** via LangChain. Artefatos de voz (Whisper, Piper) podem vir do **Hugging Face Hub**; o Hub não é o provedor da LLM.

## Dependências

- Python 3.11 (`py -3.11`; `py` sem versão aponta para 3.14 neste Windows) — na execução (rock-it)
- LangChain, quando a task ligar o cérebro (LLM)
- Groq: cérebro (LLM via LangChain)
- Hugging Face Hub: só artefatos STT/TTS (Whisper, vozes Piper), não o cérebro
- Postgres: bancos vetoriais
