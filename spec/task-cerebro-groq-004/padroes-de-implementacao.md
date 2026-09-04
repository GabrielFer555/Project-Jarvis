# Padrões de implementação — Cérebro LLM via Groq

## Convenções

- Interpretador: `py -3.11`
- Sem dependências fora da stack obrigatória da task
- Cliente da LLM: `ChatGroq` (`from langchain_groq import ChatGroq`)
- Chaves: `GROQ_API_KEY` e `GROQ_MODEL`; sem fallback para `HF_TOKEN` / `HF_MODEL`
- Não commitar `.env` nem incluir chave real

## Contratos

- `Settings(token: str, model: str)`: `token` = `GROQ_API_KEY`, `model` = `GROQ_MODEL`
- `load_settings() -> Settings`: fail-closed se chave ou modelo ausente/em branco; `os.environ.setdefault("GROQ_API_KEY", token)`
- `init_brain() -> Settings`: lê `instructions.md`, chama `load_settings()`, monta `ChatGroq(model=_settings.model, api_key=_settings.token, temperature=0.7, max_tokens=128)`
- `generate_reply(text, language) -> str`: se `_llm is None`, chama `init_brain()`; `raw = _llm.invoke(prompt)`; se `raw` tiver `.content`, usa esse valor; senão `str(raw)`; `strip()` no final
- Prompt: markdown + fala entre `<<<` e `>>>`; sem `PromptTemplate`; `instructions.md` inalterado

## Testes

`tests/test_settings.py` e `tests/test_brain.py` (17 testes no repositório), LLM mockada, sem rede:

- Ausente `GROQ_API_KEY` / `GROQ_MODEL` → `RuntimeError` com o nome da chave
- Carga válida devolve `Settings`
- `init_brain` instancia `ChatGroq` com o modelo do `.env`
- `generate_reply` usa `.content` da mensagem; não interpola `reasoning_content` nem `str` cru do `AIMessage`
- Arquivo `instructions.md` ausente/vazio → `RuntimeError`; `ChatGroq` / `invoke` não são chamados
- Delimitadores `<<<` `>>>` e guardrails do markdown permanecem

## Decisões

| Decisão | Motivo |
| --- | --- |
| `ChatGroq` no lugar de `HuggingFaceEndpoint` | RF1: Groq é o provedor da LLM; Hub fica só para STT/TTS |
| `GROQ_API_KEY` + `GROQ_MODEL`, sem fallback HF | RF2/RF3: fail-closed nas chaves novas; não misturar provedores |
| Resposta falada = `.content` | RF5: não falar raciocínio interno nem o `repr` do objeto LangChain |
| `langchain-groq` no `requirements.txt` | RF6: remover `langchain-huggingface`; manter `langchain-core` |
| Mock de `ChatGroq`, sem integração Groq | RF7: testes unitários cobrem fail-closed e `.content` sem rede |
| Não migrar `docs/cerebro-llm/` | Histórico já publicado; docs desta feature ficam na pasta da task |
| Não commitar `.env` | RF3: a chave real não entra no git |
