# Arquitetura — Spec

## Contexto

A spec não entra no fluxo de áudio do robô. Ela produz o contrato da etapa e o registro da decisão. Quem implementa é a skill rock-it:

```
solicitação → spec (plano + regra + arquitetura da task) → parar
           → /rock-it → src/ + testes + docs/ + README + progresso
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
| Skill spec | `.cursor/skills/spec/SKILL.md` | Inventariar `docs/`, montar o plano, gravar a decisão e parar |
| Templates de docs | `.cursor/skills/spec/reference.md` | Formato da regra, da arquitetura e das atualizações de `docs/` |
| Skill rock-it | `.cursor/skills/rock-it/SKILL.md` | Executar o plano (código, testes, docs vivas) |
| Contrato da spec | `docs/spec/` | Regra de negócio e arquitetura deste processo |
| Padrões do projeto | `docs/padroes-de-implementacao.md` | Convenções, stack, comandos e decisões vigentes |
| Índice de funcionalidades | `docs/README.md` | Mapa funcionalidade → documentação → código |
| Documentação viva | `docs/<funcionalidade>/` | Como cada funcionalidade se comporta hoje (rock-it atualiza) |
| Pasta da task | `spec/task-{slug}-{NNN}/` | `plano.md`, `regra-de-negocio.md`, `arquitetura.md` (spec) |
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
inventário: docs/README.md + docs/<afetadas>/ + padroes-de-implementacao.md
        │
        ▼
classificar impacto: atualizar | criar | não tocar
        │
        ▼
calcular NNN e gravar spec/task-{slug}-{NNN}/
   plano.md + regra-de-negocio.md + arquitetura.md
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
(rock-it) README + docs/progresso.md + docs/<funcionalidade>/ do checklist
```

## Contratos

Dois lugares para documentação de funcionalidade, com papéis diferentes:

| Lugar | Papel | Quem escreve |
| --- | --- | --- |
| `docs/<funcionalidade>/` | Fonte viva e canônica | rock-it, conforme o checklist do plano |
| `spec/task-{slug}-{NNN}/` | Registro da decisão daquela task, congelado | spec, no planejamento |

Nomeação da pasta da task: `{slug}` em kebab-case e `{NNN}` sequencial de três dígitos, único no repositório (maior valor existente + 1).

Checklist de documentação do plano: caminhos concretos, com o que muda em cada arquivo, mais a lista de docs não impactadas. Item genérico não vale — o rock-it não adivinha caminho.

## Dados

A spec não persiste estado além dos três arquivos da pasta da task. Quando a task usar memória vetorial, o banco é **Postgres**. O cérebro (LLM) é **Groq** via LangChain. Artefatos de voz (Whisper, Piper) podem vir do **Hugging Face Hub**; o Hub não é o provedor da LLM.

## Dependências

- Python 3.11 (`py -3.11`; `py` sem versão aponta para 3.14 neste Windows) — na execução (rock-it)
- LangChain, quando a task ligar o cérebro (LLM)
- Groq: cérebro (LLM via LangChain)
- Hugging Face Hub: só artefatos STT/TTS (Whisper, vozes Piper), não o cérebro
- Postgres: bancos vetoriais

## Decisões

| Decisão | Motivo |
| --- | --- |
| Spec grava a regra e a arquitetura da task | São a decisão que o plano toma; escrever depois é reconstruir de memória |
| Spec não edita `docs/` | A documentação viva acompanha código que existe, e código só nasce no rock-it |
| Checklist com caminho concreto | Evita "atualizar a documentação" e doc esquecida ou reescrita à toa |
| Atualizar em vez de criar, na dúvida | Impede pasta paralela para a mesma funcionalidade |
| Padrões num arquivo único | `padroes-de-implementacao.md` por feature repetia as mesmas convenções |
