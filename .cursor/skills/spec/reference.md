# Templates de documentação (skill spec)

Dois usos:

- A skill **spec**, no planejamento, grava `regra-de-negocio.md` e `arquitetura.md` na pasta da task (`spec/task-{slug}-{NNN}/`), junto com o `plano.md`.
- A skill **rock-it**, na Fase 5, atualiza a documentação viva em `docs/` seguindo o checklist do plano, além de `README.md` e `docs/progresso.md`.

Não existe `padroes-de-implementacao.md` por feature. Os padrões do projeto são o arquivo único `docs/padroes-de-implementacao.md`; o que é contrato da feature vai na seção `## Contratos` do `arquitetura.md`.

`{slug}`: kebab-case da funcionalidade (ex.: `cerebro-llm`, `memoria-vetorial`). `{NNN}`: próximo número sequencial de 3 dígitos (ver skill).

## Atualizar ou criar em `docs/`

| Situação | Decisão |
| --- | --- |
| A feature toca funcionalidade já mapeada em `docs/` | Atualizar a pasta existente, por profunda que seja a mudança |
| Capacidade nova, sem pasta que a cubra | Criar `docs/<nova>/` com os dois arquivos e registrar no índice `docs/README.md` |
| Funcionalidade não relacionada | Não tocar |

Na dúvida, atualizar. Nunca criar pasta paralela para a mesma funcionalidade (`docs/cerebro-llm/` continua sendo o cérebro, mesmo trocando de provedor).

Ao atualizar, mexer só na seção afetada: a regra que mudou, o componente novo, a dependência que saiu. Não reescrever o documento inteiro nem apagar decisão anterior que continua valendo. Regra que deixou de valer é **substituída**, não acumulada ao lado da nova.

## README.md

Atualizar só o que a task mudou: tabela de Progresso, "O que já funciona", Como rodar, estrutura de pastas, Decisões, próximo passo. Não reescrever o documento inteiro.

## docs/progresso.md

Acrescentar seção datada no mesmo estilo existente (`## AAAA-MM-DD`, `### Etapa N — nome`, o que mudou, problemas e correções se houver). Atualizar **Estado atual** e **Próximo passo** no final.

Não apagar histórico anterior.

## docs/README.md (índice)

Só muda quando entra funcionalidade nova. Uma linha por funcionalidade mapeada:

```markdown
| Funcionalidade | Documentação | Código |
| --- | --- | --- |
| <nome> | [docs/<slug>/](<slug>/regra-de-negocio.md) | `src/<pacote>/` |
```

## regra-de-negocio.md

Na pasta da task (spec, no planejamento) e em `docs/<slug>/` (rock-it, na execução). Na task, o documento descreve a decisão daquela feature; em `docs/`, descreve a funcionalidade inteira como ela passa a ser.

```markdown
# Regra de negócio — <funcionalidade>

## Objetivo

<o que o robô passa a fazer ou deixar de fazer>

## Comportamento

- ...

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/<slug>/regra-de-negocio.md` | ... | ... |

<Somente na pasta da task. Se nada muda em funcionalidade mapeada: `Nenhuma; funcionalidade nova.`>

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## Exceções

- ...

## Fora de escopo

- ...
```

## arquitetura.md

~~~markdown
# Arquitetura — <funcionalidade>

## Contexto

<onde a peça entra no fluxo microfone → STT → LLM → TTS / locomoção>

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| ... | `src/...` | ... |

## Fluxo

```
<diagrama texto>
```

## Contratos

<assinaturas, variáveis de ambiente, eventos — só o que esta funcionalidade expõe>

```python
def exemplo(...) -> ...
```

| Chave | Papel |
| --- | --- |
| `VAR_DE_AMBIENTE` | ... |

## Dados

<Postgres / vetores / arquivos / cache — só o que a task usa>

## Dependências

- Python 3.11
- LangChain (se aplicável)
- Groq (cérebro: `GROQ_MODEL`)
- Hugging Face Hub (artefatos STT/TTS, se aplicável)
- Postgres (se aplicável)

## Decisões

| Decisão | Motivo |
| --- | --- |
| ... | ... |

<Só decisões desta funcionalidade. Padrão que vale para o projeto inteiro vai em `docs/padroes-de-implementacao.md`.>
~~~
