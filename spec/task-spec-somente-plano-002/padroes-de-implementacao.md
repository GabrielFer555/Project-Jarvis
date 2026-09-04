# Padrões de implementação — Spec só gera o plano

## Convenções

- Spec: somente `plano.md`
- Rock-it: código, testes, README, `docs/progresso.md`, três docs na pasta da task
- Interpretador na execução: `py -3.11`

## Contratos

Depois de gravar o plano, a resposta da spec confirma o caminho, diz que nada foi implementado e pede `/rock-it`.

## Testes

Não aplicável (skills e markdown).

## Decisões

| Decisão | Motivo |
| --- | --- |
| Spec não implementa | Evitar misturar planejamento com execução; rock-it já orquestra Dev/Reviewer/QA |
| Modo de execução fica no plano | O ritmo (`non stop` / `parada por execução`) é do rock-it |
| Templates só no rock-it | Spec não chega na etapa de documentação |
