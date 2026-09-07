# Documentação — Project Jarvis

Mapa das funcionalidades do robô. Esta pasta é a **fonte viva**: descreve como cada peça se comporta hoje, não o histórico de como chegou aqui.

A skill `spec` lê este índice antes de planejar, para decidir se a feature **atualiza** uma funcionalidade mapeada ou **cria** uma nova. A skill `rock-it` atualiza estes arquivos na execução, seguindo o checklist do plano.

## Funcionalidades mapeadas

| Funcionalidade | Documentação | Código |
| --- | --- | --- |
| API HTTP e healthcheck | [api/](api/regra-de-negocio.md) | `src/api/` |
| Cérebro LLM | [cerebro-llm/](cerebro-llm/regra-de-negocio.md) | `src/agent/` |
| Chat texto | [chat-texto/](chat-texto/regra-de-negocio.md) | `src/agent/text_chat.py` |
| Memória conversacional | [memoria-conversacional/](memoria-conversacional/regra-de-negocio.md) | `src/memory/` |
| Rosto do robô | [rosto-do-robo/](rosto-do-robo/regra-de-negocio.md) | `src/hardware/face/` |
| Spec e execução de tasks | [spec/](spec/regra-de-negocio.md) | `.cursor/skills/spec/`, `.cursor/skills/rock-it/` |

Cada pasta tem `regra-de-negocio.md` (o que a funcionalidade faz e não faz) e `arquitetura.md` (componentes, fluxo, contratos, dependências e decisões).

## Documentos do projeto

| Arquivo | Papel |
| --- | --- |
| [padroes-de-implementacao.md](padroes-de-implementacao.md) | Convenções, stack obrigatória, comandos e decisões vigentes |
| [progresso.md](progresso.md) | Diário datado do que já foi feito |

## Ainda sem documentação

Código que existe mas não tem pasta aqui. Uma feature que mexa nestas áreas cria a documentação da funcionalidade:

| Área | Código | Situação |
| --- | --- | --- |
| Voz (wake word, STT, TTS) | `src/voice/` | Funciona; descrita só no README e no progresso |
| Locomoção | `src/robot/` | Pacote reservado, ainda vazio |
| Visão | `src/vision/` | Pacote reservado, ainda vazio |

## Registro por task

O plano e a decisão de cada task ficam em `spec/task-{slug}-{NNN}/` na raiz, congelados no tempo. Quando a documentação daqui e a de uma pasta de task divergirem, vale a desta pasta.
