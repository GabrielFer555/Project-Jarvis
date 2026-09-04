# Padrões de implementação — Instruções do cérebro em markdown

## Convenções

- Interpretador: `py -3.11`
- Sem dependências fora da stack obrigatória da task
- Instruções em português no markdown; resposta ao usuário no `{language_name}`
- Único placeholder no arquivo: `{language_name}`

## Contratos

- `_INSTRUCTIONS_PATH`: `Path(__file__).resolve().parent / "instructions.md"`
- `_read_instructions() -> str`: lê UTF-8; `FileNotFoundError` ou conteúdo sem texto útil → `RuntimeError` citando o caminho
- `init_brain() -> Settings`: chama `_read_instructions()`, guarda em `_instructions`, depois monta `HuggingFaceEndpoint`
- `_build_prompt(text, language) -> str`: `str.replace` só de `{language_name}`; concatena instruções + delimitadores `<<<` / `>>>` + sufixo `Jarvis:`
- `generate_reply(text, language) -> str`: se o cérebro ainda não inicializou, chama `init_brain()`; `_llm.invoke` no prompt concatenado, sem `PromptTemplate`

## Testes

`tests/test_brain.py` (7 testes novos; 14 no total do repositório), LLM mockada, sem rede:

- Arquivo ausente, vazio ou só whitespace → `RuntimeError` com o caminho; `HuggingFaceEndpoint` / `invoke` não são chamados
- Interpolação `pt` → português e inclusão do conteúdo do markdown no prompt
- Fala só na zona `<<<` `>>>`
- Fala com `{` `}` ou “ignore as instruções” permanece dado; instruções originais não são substituídas
- Frases-chave dos guardrails presentes em `instructions.md`

## Decisões

| Decisão | Motivo |
| --- | --- |
| Prompt no markdown, não no Python | RF1/RF3: alterar tom e limites sem mudar a invocação da LLM |
| `str.replace` só de `{language_name}`, sem `PromptTemplate` | RF6/RF8: chaves na fala da pessoa não viram variáveis e não quebram o prompt |
| Fala entre `<<<` e `>>>` | RF6: delimitador claro; a entrada é dado, não instrução |
| `RuntimeError` na leitura, antes da LLM | RF7: arquivo ausente/vazio não dispara chamada de rede |
| Guardrail de tool só no markdown | Pipeline continua sem tools; handshake de permissão ficou fora de escopo |
| Não migrar `docs/cerebro-llm/` | Histórico já publicado; docs desta feature ficam na pasta da task |
