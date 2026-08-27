# Progresso

Registro do que foi feito no Project Jarvis até agora.

## Objetivo

Construir um robô conversacional que anda e usa uma LLM como cérebro. A fala, a escuta, o raciocínio e a locomoção entram por etapas, cada uma validada sozinha antes de ir para o loop principal.

## 2026-08-13

### Etapa 1 — TTS offline

Prova de que o robô consegue falar sem internet, com o Raspberry Pi como alvo.

O primeiro `main.py` carregava a voz Piper `en_US-lessac-medium`, sintetizava uma frase de teste e reproduzia o WAV com `sounddevice`.

Dependências: `piper-tts`, `sounddevice`, `numpy`.

### Problemas dessa etapa

1. **Python errado.** `pip install` ia para o Python 3.11. `py` (sem versão) abre o 3.14, que não tinha os pacotes. Erro: `ModuleNotFoundError: No module named 'sounddevice'`. Correção: `py -3.11` para instalar e para rodar.

2. **API do Piper 1.6.** `voice.synthesize(text, wav_file)` não grava mais o arquivo. O WAV fechava sem canais, sample rate nem sample width. Erro: `wave.Error: # channels not specified`. Correção: `voice.synthesize_wav(text, wav_file)`.

3. **`requirements.txt` inválido.** Tinha a saída do `pip install`, não a lista de pacotes. Foi reduzido a `piper-tts`, `sounddevice` e `numpy`.

### Documentação inicial

O README passou a descrever a visão do robô, a tabela de etapas e como rodar o TTS.

### Reorganização do repositório

O código saiu do script único e foi para esta estrutura:

```
src/
├── main.py
├── agent/
├── voice/
├── hardware/
├── vision/
├── memory/
└── robot/
tests/
docs/
```

O TTS foi extraído para `src/voice/tts.py`:

| Função | Papel |
| --- | --- |
| `load_voice(model_path=None)` | Carrega o modelo Piper e guarda em cache |
| `speak(text, output_file=None, play=True)` | Sintetiza, grava WAV e opcionalmente toca |

`src/main.py` só chama `speak()` com a frase de teste.

Os modelos foram para `src/voice/models/`:

- `en_US-lessac-medium.onnx`
- `en_US-lessac-medium.onnx.json`

`agent`, `hardware`, `vision`, `memory` e `robot` existem como pacotes vazios, reservados para as próximas etapas. `tests/` e `docs/` também.

`output.wav` (arquivo gerado) entrou no `.gitignore`.

### Etapa 2 — Ouvir e repetir (Whisper + wake word)

O fluxo deixou de ser só TTS. O microfone espera a wake word **Jarvis**, transcreve o que vem depois com Whisper e repete com Piper.

Comportamento:

- `Jarvis olá, tudo bem?` — uma frase só; repete o que vem depois da wake word
- `Jarvis` + pausa + `olá, tudo bem?` — bip e escuta a segunda frase
- Idioma automático: Whisper detecta PT ou EN; Piper usa `pt_BR-faber-medium` ou `en_US-lessac-medium`

Arquivos novos em `src/voice/`:

| Arquivo | Papel |
| --- | --- |
| `mic.py` | Gravação com VAD por energia e bip de confirmação |
| `stt.py` | `faster-whisper` (`base`, CPU, int8) |
| `voices.py` | Catálogo EN/PT e download da voz PT |
| `listen_repeat.py` | Loop da wake word |

A voz PT é baixada do Hugging Face na primeira execução e não entra no git. O modelo Whisper `base` vai para o cache do Hugging Face.

`src/main.py` agora só chama `run_listen_repeat()`.

## Estado atual

Feito: TTS offline (EN/PT), STT com Whisper, wake word "Jarvis", loop ouvir e repetir.

Pendente: LLM, loop conversacional com cérebro, locomoção e integração no hardware.

## Próximo passo

Trocar a repetição por uma resposta da LLM.
