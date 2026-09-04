# Regra de negócio — Spec

Como uma solicitação vira plano neste repositório. A implementação só começa quando o usuário chama a skill **rock-it**.

Cada etapa do robô é construída e validada sozinha antes de entrar no loop principal. A spec é o contrato dessa etapa: o que entra, o que sai, o que não entra. Spec **não** escreve código.

## Objetivo

Diante de um pedido de feature, correção ou integração, o agente monta um plano de execução em `spec/task-{slug}-{NNN}/plano.md` e **para**. Quem executa é a skill rock-it. A implementação não ultrapassa o que está no plano.

## Comportamento

1. Detectar a **branch base** (git; em geral `main`).
2. Definir o **modo de execução**: `non stop` (padrão) ou `parada por execução` (campo para o rock-it).
3. Calcular o próximo `{NNN}` e criar `spec/task-{slug}-{NNN}/plano.md` (cabeçalho, corpo e etapas obrigatórias).
4. Se houver **dúvida impeditiva**, parar e esperar resposta. Não inventar. Não pedir rock-it até o plano estar resolvido.
5. Sem dúvida impeditiva: **parar**. Informar o caminho do plano e pedir `/rock-it`.
6. Spec não edita `src/`, `tests/`, README, `docs/progresso.md`, nem cria os três arquivos de docs da feature.

| Modo | Comportamento (rock-it) |
| --- | --- |
| `non stop` | Segue todas as etapas sem pausar, salvo dúvida impeditiva |
| `parada por execução` | Entrega uma etapa e espera confirmação antes da próxima |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Solicitação da task | Usuário | Pasta `spec/task-{slug}-{NNN}/` com `plano.md` | Raiz do repositório |
| Branch atual | git | Campo branch base no cabeçalho | Plano |
| Modo de execução | Usuário ou padrão `non stop` | Campo modo no cabeçalho | Plano (ritmo do rock-it) |
| Dúvida sem a qual não dá para planejar | Análise do pedido | Lista de dúvidas impeditivas | Chat (spec pausa; rock-it ainda não) |

## Exceções

- **Dúvida impeditiva:** falta dado sem o qual o plano vira adivinhação (API, hardware, regra de negócio, credencial, decisão de arquitetura). Preferência de estilo não pausa.
- **Testes no plano:** unitários e de integração só se houver necessidade. Sem cenário redundante. Spec não escreve os testes; só descreve se serão necessários.
- **Código no plano:** snapshot só em caso importante (contrato, API frágil, algoritmo). O restante descreve arquivos e responsabilidades.

## Fora de escopo

- Spec implementar código, testes ou documentação da feature (isso é rock-it).
- Invocar rock-it automaticamente.
- Implementar além do que foi pedido (refactors, extras, “melhorias”).
- Trocar a stack obrigatória por equivalente.
- Documentar de novo o histórico antigo de `docs/progresso.md` (só o rock-it acrescenta).
- Migrar pastas antigas em `docs/<slug>/` (ex.: `docs/cerebro-llm/`).
