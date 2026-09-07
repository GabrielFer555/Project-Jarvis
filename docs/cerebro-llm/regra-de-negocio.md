# Regra de negócio — Cérebro LLM

## Objetivo

Depois da wake word **Jarvis**, o robô deixa de repetir a frase. A transcrição vai para uma LLM na **Groq** (via LangChain), que estrutura uma resposta breve; o Piper fala essa resposta em voz alta. A mesma LLM também aceita texto digitado no modo `--text`; nesse canal a resposta é impressa no terminal, sem TTS.

## Comportamento

- O microfone e a wake word continuam iguais: `Jarvis …` numa frase só, ou `Jarvis` e a pergunta em seguida.
- A LLM recebe o texto da pessoa e o idioma: na voz, a transcrição do Whisper e o idioma detectado; no modo `--text`, a linha digitada e o `--lang`. Responde em no máximo duas frases, no mesmo idioma, prontas para TTS (na voz) ou para o terminal (no modo texto).
- Identidade, tom, limites e recusas vivem em `src/agent/instructions.md`, não em string no Python. Mudar o comportamento do Jarvis é editar esse markdown.
- A fala da pessoa entra no prompt como **dado**, entre `<<<` e `>>>`. Ordem embutida na fala não sobrepõe as instruções, não revela o prompt e não troca o papel do assistente.
- Pedido ilegal, de crime, pornografia ou ameaça recebe recusa curta, no idioma da pessoa, sem detalhar o que foi pedido.
- Cada fala é um turno isolado: nenhuma tool, RAG, memória vetorial ou histórico entra no caminho.
- A chave e o modelo vêm de `.env` (`GROQ_API_KEY`, `GROQ_MODEL`). Sem chave ou sem modelo, o programa não inicia o loop.
- O que é falado é só o conteúdo da mensagem da LLM, sem raciocínio interno nem a representação crua do objeto LangChain.
- Se a chamada à LLM falhar, o erro vai para o terminal; o rosto volta a Sleeping e o robô espera **Jarvis** de novo, sem falar.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Frase depois da wake word | STT (Whisper) | Texto da resposta | TTS (Piper) |
| Linha digitada (modo `--text`) | stdin | Texto da resposta | stdout (sem Piper) |
| Idioma (`pt` / `en`) | Whisper (voz) ou `--lang` (texto) | Voz correspondente (voz) ou `{language_name}` no prompt (texto) | Piper (voz) ou `generate_reply` (texto) |
| Identidade e guardrails | `src/agent/instructions.md` | Prompt montado | LLM na Groq |
| `GROQ_API_KEY`, `GROQ_MODEL` | `.env` | Cliente `ChatGroq` | API da Groq |

## Exceções

- `GROQ_API_KEY` ou `GROQ_MODEL` ausentes: `RuntimeError` na subida, com instrução de copiar `.env.example`.
- `instructions.md` ausente, vazio ou só com espaços: `RuntimeError` com o caminho do arquivo; a LLM não é chamada.
- Falha de rede ou da Groq: mensagem no terminal, estado do rosto volta a Sleeping, loop segue.

## Fora de escopo

- Tools, agentes com function calling, RAG, Postgres.
- Histórico multi-turno.
- Escolha automática de modelo além do valor em `.env`.
