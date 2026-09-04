# Regra de negócio — Cérebro LLM

## Objetivo

Depois da wake word **Jarvis**, o robô deixa de repetir a frase. A transcrição vai para uma LLM (Hugging Face via LangChain), que estrutura uma resposta breve; o Piper fala essa resposta em voz alta.

## Comportamento

- O microfone e a wake word continuam iguais: `Jarvis …` numa frase só, ou `Jarvis` e a pergunta em seguida.
- A LLM recebe só o texto transcrito e o idioma detectado. Responde em no máximo duas frases, no mesmo idioma, prontas para TTS.
- Nenhuma tool, RAG, memória vetorial ou outro processamento entra no caminho.
- A chave e o modelo vêm de `.env` (`HF_TOKEN`, `HF_MODEL`). Sem token ou sem modelo, o programa não inicia o loop.
- Se a chamada à LLM falhar, o erro vai para o terminal; o robô volta a esperar **Jarvis** sem falar.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Frase depois da wake word | STT (Whisper) | Texto da resposta | TTS (Piper) |
| Idioma (`pt` / `en`) | Whisper | Voz correspondente | Piper |
| `HF_TOKEN`, `HF_MODEL` | `.env` | Cliente LangChain | Hugging Face Inference |

## Exceções

- `HF_TOKEN` ou `HF_MODEL` ausentes: `RuntimeError` na subida, com instrução de copiar `.env.example`.
- Falha de rede ou do provedor Hugging Face: mensagem no terminal, estado do rosto volta a Sleeping, loop segue.

## Fora de escopo

- Tools, agentes com function calling, RAG, Postgres.
- Histórico multi-turno.
- Escolha automática de modelo além do valor em `.env`.
