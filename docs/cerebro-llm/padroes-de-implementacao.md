# Padrões de implementação — Cérebro LLM

## Convenções

- Interpretador: `py -3.11`
- Sem dependências fora da stack obrigatória da task
- Inferência só via LangChain `HuggingFaceEndpoint`; não ligar tools, agentes nem embeddings

## Contratos

```python
def load_settings() -> Settings  # token, model; falha se faltar env
def init_brain() -> Settings     # monta o endpoint uma vez
def generate_reply(text: str, language: str = "") -> str
```

Variáveis:

| Chave | Papel |
| --- | --- |
| `HF_TOKEN` | Access token Hugging Face (também aceita `HUGGINGFACEHUB_API_TOKEN`) |
| `HF_MODEL` | Repo id no Hub, ex. `HuggingFaceTB/SmolLM2-1.7B-Instruct` |

O prompt pede resposta curta, no idioma da pessoa, sem markdown. `return_full_text=False` para o TTS receber só a geração.

## Testes

`tests/test_settings.py`: token/modelo ausentes disparam `RuntimeError`; carga válida devolve `Settings`. Sem teste de integração com a API (depende de credencial e rede).

## Decisões

| Decisão | Motivo |
| --- | --- |
| `.env` + `.env.example` | A chave não entra no git; o exemplo documenta as chaves |
| `HuggingFaceEndpoint` sem tools | Pedido explícito: nenhum processamento extra nem tool |
| `provider="auto"` | O Hub escolhe um provedor gratuito disponível para o modelo |
| Import do endpoint pelo submódulo | Evita puxar `HuggingFacePipeline` / transformers na subida |
| `langchain-huggingface>=1.2` | A 0.1.x usa a Inference API antiga, incompatível com o Hub atual |
