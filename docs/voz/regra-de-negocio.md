# Regra de negócio — Voz

## Objetivo

O robô escuta pelo microfone (wake word **Jarvis** e Whisper) e fala pelo Piper. Depois de responder em voz alta, abre uma janela de escuta para a pessoa continuar **sem dizer Jarvis de novo**. O timeout dessa janela vale **só para silêncio contínuo**: se a fala começar, a take não é cortada e a janela **reinicia** cheia depois do TTS.

## Comportamento

- A wake word **Jarvis** é obrigatória para **começar** uma conversa por voz. Dá para falar numa frase só (`Jarvis olá, tudo bem?`) ou em duas (`Jarvis` + pausa + pergunta).
- No caminho de duas frases, o loop diz **Pode falar.**, toca um bip e escuta a pergunta com `start_timeout=6.0`. Sem pergunta, volta a esperar **Jarvis**.
- O Whisper transcreve em PT ou EN (idioma automático). O Piper usa a voz do mesmo idioma: `pt_BR-faber-medium` ou `en_US-lessac-medium`.
- A transcrição vai para `generate_reply`; o Piper fala só `Reply.spoken`. O raciocínio da Groq não é falado.
- Quando o Piper termina, o loop abre a janela. `CONVERSATION_WINDOW_SECONDS` (opcional; default **15**) mede **só silêncio contínuo** à espera de uma fala. Não limita o tempo da frase, da LLM nem do TTS. Não alimenta `max_seconds` (teto técnico da take, 12s).
- Fala transcrita não vazia na janela **não exige** wake word: o texto inteiro segue para a LLM e o Piper.
- Se a transcrição da janela contiver a wake word, `split_wake_word` vale: o comando depois de **Jarvis** vai à LLM; se a pessoa disser só **Jarvis**, reutiliza **Pode falar.** + bip + `start_timeout=6.0`. Sem pergunta, fecha a janela e espera a wake word.
- Só silêncio contínuo pelo valor da env (ninguém começou a falar), áudio vazio ou transcrição vazia fecha a janela: rosto Sleeping e espera por **Jarvis**.
- No instante em que o VAD marca **início de fala**, o `start_timeout` da janela **deixa de valer** para aquela take. A pessoa termina a frase com `COMMAND_SILENCE_S` (1.6s).
- A janela **reinicia** com o valor cheio depois do TTS da resposta (nova `record_utterance`). Take curta demais descartada zera `waited_chunks` **somente** na janela, via `reset_start_timeout_on_short=True`. O **Pode falar.** (`start_timeout=6.0`) **não** passa o flag: o prazo conta desde o início da take; uma take curta não devolve tempo.
- Falha da LLM (ou do Postgres no turno) na voz: mensagem no terminal, rosto Sleeping, `mic.clear()`, janela **não** reabre; o loop volta a esperar **Jarvis**.
- Durante a janela o rosto fica **Listening**. Sleeping é espera da wake word, abandono da janela ou erro.
- Fechar a janela de voz **não** encerra a sessão em Postgres (`SESSION_IDLE_MINUTES` continua sendo o corte da memória).
- O modo `--text` não usa este loop. O ponto de entrada da voz é `run_listen()` em `src/voice/listen.py`.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Wake word + frase | Microfone / Whisper | Primeiro turno | LLM + TTS |
| Fala na janela | Microfone / Whisper, sem exigir wake word | Turno seguinte; janela reinicia depois do TTS | LLM + TTS |
| Silêncio contínuo de `CONVERSATION_WINDOW_SECONDS` | VAD (`start_timeout`), só enquanto não há fala | Janela fechada | Espera da wake word |
| Só “Jarvis” (início ou janela) | Whisper + `split_wake_word` | Caminho “Pode falar.” | Escuta da pergunta ou volta à wake word |
| Fim do TTS | Piper | Rosto Listening | Escuta da janela |
| Exceção de `generate_reply` | Groq / Postgres | Rosto Sleeping, janela fechada | Espera da wake word |
| `CONVERSATION_WINDOW_SECONDS` | `.env` (opcional, default 15) | Segundos de **silêncio** até fechar a janela; não é teto da frase | `start_timeout` do VAD no follow-up |

## Exceções

- Transcrição vazia depois de áudio capturado na janela: trata como ausência de resposta (fecha a janela).
- Eco do TTS: `mic.clear()` e `ignore_ms=250` antes de escutar, no mesmo espírito do trecho pós-wake word.
- Frase mais longa que `CONVERSATION_WINDOW_SECONDS`: o timeout da janela **não** encerra a take; vale a pausa de `COMMAND_SILENCE_S`.
- Take curta demais descartada pelo VAD **na janela** (`reset_start_timeout_on_short=True`): o relógio zera (`waited_chunks`); a pessoa ganha de novo o valor cheio de silêncio.
- Take curta no **Pode falar.** (`start_timeout=6.0`, flag ausente/`False`): o prazo continua desde o início; a take curta não devolve tempo.
- `CONVERSATION_WINDOW_SECONDS` ausente ou vazia cai em 15. Não inteiro ou `<= 0`: `RuntimeError` na subida, com o nome e o valor; o loop não começa.
- Ctrl+C continua encerrando o processo sem fechar a sessão.

## Fora de escopo

- Chat texto (comportamento).
- Encerrar a sessão Postgres ao fechar a janela de voz.
- Barge-in (interromper o TTS), estado extra no rosto, comando falado de despedida.
- Identificação de locutor.
- Alias de `listen_repeat` / `run_listen_repeat`.
