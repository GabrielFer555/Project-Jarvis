# Regra de negócio — Pasta de plano por task

Onde o plano de execução e a documentação da funcionalidade ficam no repositório.

## Objetivo

Cada task deixa um pacote único na raiz: pasta numerada com o plano, o progresso da execução e os três arquivos de documentação da feature. README e o diário `docs/progresso.md` continuam no lugar de sempre.

## Comportamento

1. Antes de implementar, criar `spec/task-{slug}-{NNN}/plano.md`.
2. `{NNN}` é o próximo número de 3 dígitos (001, 002, …), único no repositório.
3. Progresso da execução (contador e `[Concluído]` / `[Reaberto]`) é escrito no `plano.md`.
4. Ao encerrar, gravar regra de negócio, arquitetura e padrões **nessa mesma pasta**.
5. Atualizar README e `docs/progresso.md` como nas tasks anteriores.
6. Não migrar pastas antigas em `docs/<slug>/`.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Solicitação da task | Usuário | Pasta `spec/task-{slug}-{NNN}/` com `plano.md` | Raiz do repositório |
| Pastas `spec/task-*` existentes | Disco | Próximo `{NNN}` | Nome da pasta nova |
| Feature concluída | Execução | `regra-de-negocio.md`, `arquitetura.md`, `padroes-de-implementacao.md` | Mesma pasta da task |
| Diário do robô | `docs/progresso.md` | Seção datada | `docs/progresso.md` |

## Exceções

- Sem pasta `spec/task-*`: usar `001`.
- Dúvida impeditiva pausa a execução; a pasta e o `plano.md` já existem.
- Skill `rock-it` lê o mesmo `plano.md`; se o plano só estiver no chat, grava no próximo `{NNN}` antes de executar.

## Fora de escopo

- Migrar `docs/cerebro-llm/` e `docs/rosto-do-robo/`.
- Script automático de numeração.
- Mudança em `src/` ou no comportamento do robô.
