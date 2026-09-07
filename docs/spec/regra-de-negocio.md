# Regra de negócio — Spec

Como uma solicitação vira plano neste repositório. A implementação só começa quando o usuário chama a skill **rock-it**.

Cada etapa do robô é construída e validada sozinha antes de entrar no loop principal. A spec é o contrato dessa etapa: o que entra, o que sai, o que não entra. Spec **não** escreve código.

## Objetivo

Diante de um pedido de feature, correção ou integração, o agente monta o plano de execução e registra a decisão em `spec/task-{slug}-{NNN}/` — `plano.md`, `regra-de-negocio.md` e `arquitetura.md` — e **para**. Quem executa é a skill rock-it. A implementação não ultrapassa o que está no plano.

Documentar a decisão é parte do planejamento. Mexer na documentação viva do projeto (`docs/`) não é: a spec **planeja** essas mudanças, com caminho e conteúdo, e o rock-it as executa.

## Comportamento

1. Detectar a **branch base** (git; em geral `main`).
2. Definir o **modo de execução**: `non stop` (padrão) ou `parada por execução` (campo para o rock-it).
3. **Inventário e impacto**, antes de escrever qualquer arquivo: ler o índice `docs/README.md`, as docs das funcionalidades que a feature toca e `docs/padroes-de-implementacao.md`. A regra vigente é insumo obrigatório do plano.
4. Classificar cada documentação: atualizar a funcionalidade mapeada, criar pasta para capacidade nova, ou não tocar. Na dúvida entre criar e atualizar, **atualizar**.
5. Calcular o próximo `{NNN}` e gravar os três arquivos da pasta da task.
6. Se houver **dúvida impeditiva**, parar e esperar resposta. Não inventar. Não pedir rock-it até o plano estar resolvido.
7. Sem dúvida impeditiva: **parar**. Informar os caminhos, dizer qual doc de `docs/` será mexida na execução e pedir `/rock-it`.

A spec não edita `src/`, `tests/`, `README.md`, `docs/progresso.md` nem qualquer arquivo de `docs/`.

| Modo | Comportamento (rock-it) |
| --- | --- |
| `non stop` | Segue todas as etapas sem pausar, salvo dúvida impeditiva |
| `parada por execução` | Entrega uma etapa e espera confirmação antes da próxima |

## Decisão de documentação

| Situação | Decisão |
| --- | --- |
| A feature toca funcionalidade já mapeada em `docs/` | Atualizar a pasta existente, por profunda que seja a mudança |
| Capacidade nova, sem pasta que a cubra | Criar `docs/<nova>/` e registrar no índice |
| Funcionalidade não relacionada | Não tocar; listar no plano como não impactada |

Trocar a tecnologia de uma funcionalidade não cria funcionalidade nova: o cérebro passou de Hugging Face para Groq e continua sendo `docs/cerebro-llm/`.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Solicitação da task | Usuário | Pasta `spec/task-{slug}-{NNN}/` com plano, regra e arquitetura | Raiz do repositório |
| Funcionalidades mapeadas e regras vigentes | `docs/` | Seção de impacto e checklist de documentação | Plano |
| Padrões vigentes | `docs/padroes-de-implementacao.md` | Etapas técnicas dentro da stack | Plano |
| Branch atual | git | Campo branch base no cabeçalho | Plano |
| Modo de execução | Usuário ou padrão `non stop` | Campo modo no cabeçalho | Plano (ritmo do rock-it) |
| Dúvida sem a qual não dá para planejar | Análise do pedido | Lista de dúvidas impeditivas | Chat (spec pausa; rock-it ainda não) |

## Exceções

- **Dúvida impeditiva:** falta dado sem o qual o plano vira adivinhação (API, hardware, regra de negócio, credencial, decisão de arquitetura). Preferência de estilo não pausa.
- **Testes no plano:** unitários e de integração só se houver necessidade. Sem cenário redundante. Spec não escreve os testes; só descreve se serão necessários.
- **Código no plano:** snapshot só em caso importante (contrato, API frágil, algoritmo). O restante descreve arquivos e responsabilidades.
- **Divergência na execução:** se o rock-it precisar sair do que foi decidido, ele corrige a regra e a arquitetura da pasta da task, para o registro não mentir.

## Fora de escopo

- Spec implementar código, testes, README ou `docs/progresso.md` (isso é rock-it).
- Spec editar `docs/`: a documentação viva é planejada aqui e escrita na execução.
- Gerar `padroes-de-implementacao.md` por feature: os padrões são o arquivo único `docs/padroes-de-implementacao.md`.
- Criar pasta nova em `docs/` para funcionalidade que já existe.
- Invocar rock-it automaticamente.
- Implementar além do que foi pedido (refactors, extras, "melhorias").
- Trocar a stack obrigatória por equivalente.
- Migrar pastas de tasks antigas para o formato novo: elas são registro histórico.
