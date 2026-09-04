# Regra de negócio — Spec só gera o plano

## Objetivo

A skill spec passa a ser só o contrato da etapa: gravar o plano e parar. Implementar, testar e documentar a feature fica na skill rock-it, quando o usuário a chamar.

## Comportamento

- Spec cria `spec/task-{slug}-{NNN}/plano.md` e publica o mesmo texto no chat.
- Sem dúvida impeditiva: pede `/rock-it` e não toca em mais nenhum arquivo.
- Com dúvida impeditiva: espera resposta; não pede rock-it.
- Pedido de “implementar X” sem plano: gera o plano e para.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Solicitação | Usuário | `plano.md` | `spec/task-{slug}-{NNN}/` |
| Plano existente + pedido de executar | Usuário | (spec não age) | skill rock-it |

## Exceções

- Dúvida impeditiva bloqueia o pedido de rock-it.
- Spec pode criar a pasta da task e o `plano.md`; nada além disso.

## Fora de escopo

- Spec escrever código, testes ou docs da feature.
- Spec invocar rock-it sozinha.
