# Regra de negócio — Conversação bidimensional por voz

## Objetivo

Depois que o Jarvis responde em voz alta, a pessoa pode continuar falando **sem dizer Jarvis de novo**. A janela (default 15 segundos) vale **só para silêncio**: se a fala começar, esse timeout não corta nada e a janela **reinicia** cheia. Se o silêncio durar o valor configurado, o robô volta a dormir e só acorda com a wake word. O loop de voz deixa o nome do eco (`listen_repeat`) e passa a se chamar `listen`.

## Comportamento

- A wake word **Jarvis** continua obrigatória para **começar** uma conversa por voz (uma frase só, ou **Jarvis** e a pergunta em seguida).
- Quando o Piper termina de falar, abre-se uma janela de escuta. `CONVERSATION_WINDOW_SECONDS` (opcional; default **15**) mede **só silêncio contínuo** à espera de uma fala. Não limita o tempo da frase, da LLM nem do TTS.
- No instante em que o VAD detecta o **início** de uma fala, o timeout da janela **deixa de valer** para aquela take. A pessoa termina a frase com a pausa curta de sempre (`COMMAND_SILENCE_S`). A janela **reinicia** com o valor cheio depois do TTS da resposta. Take curta demais descartada zera `waited_chunks` **somente** na janela, via `reset_start_timeout_on_short=True` em `record_utterance` (default `False`). O caminho **Pode falar.** (`start_timeout=6.0`) **não** passa o flag: o prazo conta desde o início da take; uma take curta não devolve tempo.
- Fala útil na janela segue para a LLM e o TTS **sem** nova wake word.
- Só o silêncio contínuo pelo valor da env (ninguém começou a falar), áudio vazio ou transcrição vazia: Sleeping e espera por **Jarvis**.
- Dizer só **Jarvis** na janela reutiliza o caminho atual de “Pode falar”; sem pergunta, a janela fecha.
- Falha da LLM no follow-up não reabre a janela; espera **Jarvis**.
- Durante a janela o rosto está Listening. Sleeping é espera da wake word, abandono da janela ou erro.
- `--text` inalterado. A sessão em Postgres continua expirando por `SESSION_IDLE_MINUTES` (default 10 minutos): fechar a janela de voz **não** encerra a sessão.
- `CONVERSATION_WINDOW_SECONDS` ausente ou vazia cai em 15. Não inteiro ou `<= 0`: `RuntimeError` na subida, com o nome e o valor; o loop não começa.
- O ponto de entrada do loop de voz é `run_listen()` em `src/voice/listen.py`.

## Impacto nas regras existentes

| Doc afetada | Regra vigente | Passa a valer |
| --- | --- | --- |
| `docs/cerebro-llm/regra-de-negocio.md` | Cada turno de voz nasce da wake word; depois de falar (ou da falha da LLM) espera **Jarvis** | Wake word inicia; turnos na janela não exigem wake word. Falha da LLM ainda espera **Jarvis** |
| `docs/rosto-do-robo/regra-de-negocio.md` | Depois de falar, Sleeping; Listening só após a wake word | Depois de falar, Listening na janela; Sleeping quando a janela fecha |
| `docs/memoria-conversacional/regra-de-negocio.md` | Origem da fala de voz = frase depois da wake word | Também a fala na janela, sem wake word; sessão e expiração iguais |
| `docs/memoria-conversacional/arquitetura.md` | Loop em `listen_repeat.py` | Loop em `listen.py` |
| `docs/chat-texto/arquitetura.md` | `run_listen_repeat()` no ramo sem `--text` | `run_listen()`; regra do chat texto igual |
| `docs/api/arquitetura.md` | Voz → `run_listen_repeat()` | Voz → `run_listen()` |
| (voz ainda sem pasta em `docs/`) | Loop de um turno em `listen_repeat.py` | Loop com janela em `listen.py`; documentar em `docs/voz/` |

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Wake word + frase | Microfone / Whisper | Primeiro turno | LLM + TTS |
| Fala na janela | Microfone / Whisper, sem exigir wake word | Turno seguinte; timeout da janela cancelado; janela reinicia depois do TTS | LLM + TTS |
| Silêncio contínuo de `CONVERSATION_WINDOW_SECONDS` | VAD (`start_timeout`), só enquanto não há fala | Janela fechada | Espera da wake word |
| Só “Jarvis” na janela | Whisper + `split_wake_word` | Caminho “Pode falar.” | Escuta da pergunta ou volta à wake word |
| Fim do TTS | Piper | Rosto Listening | Escuta da janela |
| Exceção de `generate_reply` | Groq / Postgres | Rosto Sleeping, janela fechada | Espera da wake word |
| `CONVERSATION_WINDOW_SECONDS` | `.env` (opcional, default 15) | Segundos de **silêncio** até fechar a janela; não é teto da frase | `start_timeout` do VAD no follow-up |

## Exceções

- Transcrição vazia depois de áudio capturado na janela: trata como ausência de resposta (fecha a janela).
- Eco do TTS: `mic.clear()` e `ignore_ms=250` antes de escutar, no mesmo espírito do trecho pós-wake word.
- Frase mais longa que `CONVERSATION_WINDOW_SECONDS`: o timeout da janela **não** encerra a take; vale a pausa de `COMMAND_SILENCE_S`.
- Take curta demais descartada pelo VAD **na janela** (`reset_start_timeout_on_short=True`): o relógio da janela zera (`waited_chunks`); a pessoa ganha de novo o valor cheio de silêncio.
- Take curta no **Pode falar.** (`start_timeout=6.0`, flag ausente/`False`): o prazo continua desde o início; a take curta não devolve tempo.
- `CONVERSATION_WINDOW_SECONDS` inválida: `RuntimeError` na subida; o loop não começa.
- Ctrl+C continua encerrando o processo sem fechar a sessão.

## Fora de escopo

- Chat texto (comportamento).
- Encerrar a sessão Postgres ao fechar a janela de voz.
- Barge-in, estado extra no rosto, comando falado de despedida.
- Alias de `listen_repeat` / `run_listen_repeat`.
