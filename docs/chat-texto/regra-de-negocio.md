# Regra de negócio — Chat texto

## Objetivo

O Jarvis pode ser exercitado sem voz: a pessoa digita no terminal, a mesma LLM e os mesmos guardrails respondem, e o texto da resposta aparece na tela. No Cursor, esse processo (e o de voz) pode ser depurado com F5.

## Comportamento

- Sem `--text`, nada muda: wake word, microfone, Whisper, LLM e Piper seguem como no loop de voz.
- Com `--text`, não há wake word. Cada linha digitada é um pedido ao cérebro. A resposta é só impressa.
- O modo texto não abre microfone, não transcreve, não sintetiza e não mexe no rosto.
- Identidade, tom, limites e recusas continuam em `src/agent/instructions.md`. O modo texto não tem instruções próprias.
- A fala digitada entra no prompt como **dado**, entre `<<<` e `>>>`, igual à transcrição da voz.
- Cada linha entra na sessão ativa e enxerga as anteriores.
- Idioma do prompt: `--lang pt` (padrão) ou `--lang en`. Não há detecção automática.
- Encerrar: `sair`, `quit`, `exit` (qualquer capitalização) ou Ctrl+C. `sair` / `quit` / `exit` localizam a sessão ativa sem criar (`get_active_session`); se existir, encerram; se não, no-op. Ctrl+C e EOF não encerram a sessão. Linha vazia não chama a LLM.
- Credencial, modelo e `instructions.md` ausentes abortam na subida, como no loop de voz.
- Erro da LLM: mensagem no terminal, o chat continua.
- Debug: `.vscode/launch.json` lança `src/main.py` (com ou sem `--text`) no terminal integrado do Cursor, no interpretador Python 3.11 escolhido pela pessoa.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Linha de texto | stdin (`input`) | Texto da resposta | stdout (`print`) |
| `--lang` (`pt` / `en`) | CLI | `{language_name}` no prompt | `generate_reply` |
| Identidade e guardrails | `src/agent/instructions.md` | Prompt montado | LLM na Groq |
| `GROQ_API_KEY`, `GROQ_MODEL` | `.env` | Cliente `ChatGroq` | API da Groq |
| `sair` / `quit` / `exit` | stdin | Encerramento da sessão, se houver | `src/memory/` (`get_active_session` / `close_session`) |
| F5 / configuração de debug | `.vscode/launch.json` | Processo Python 3.11 pausável | Cursor |

## Exceções

- `GROQ_API_KEY`, `GROQ_MODEL` ou `instructions.md` inválido: `RuntimeError` na subida, loop de texto não começa.
- `--lang` diferente de `pt` e `en`: `argparse` recusa e o processo não inicia.
- Falha de rede ou da Groq: erro no terminal, próximo prompt de `Você:` aparece.
- Interpretador 3.14 selecionado no Cursor: o debug falha por dependências ausentes; a correção é trocar para 3.11, não alterar o `launch.json`.

## Fora de escopo

- Tools, RAG.
- Mudança de guardrails ou de `instructions.md`.
- Rosto, locomoção, visão.
- UI além do terminal.
- Path absoluto do Python no repositório.
