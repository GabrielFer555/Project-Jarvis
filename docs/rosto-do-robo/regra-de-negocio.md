# Regra de negócio — Rosto do robô

## Objetivo

O robô tem um “rosto” com quatro estados, alinhados ao loop de conversa: dormindo por padrão, escutando quando ouve **Jarvis**, pensando enquanto a LLM trabalha, respondendo enquanto o TTS fala, e de volta a dormir.

## Comportamento

| Estado | Quando |
| --- | --- |
| Sleeping | Padrão; espera a wake word; depois de falar |
| Listening | A wake word foi reconhecida (ainda pode estar ouvendo a pergunta) |
| Thinking | A frase chegou e está na LLM |
| Answering | A resposta está sendo falada; em seguida Sleeping |

- Sem wake word, o rosto permanece Sleeping.
- Se **Jarvis** não vier seguido de frase, volta a Sleeping sem Thinking/Answering.
- No Windows o rosto é um mock no terminal (ASCII).
- No Raspberry Pi a classe de LCD existe, mas a manipulação da tela está marcada com TODO e levanta `NotImplementedError`.

## Entradas e saídas

| Entrada | Origem | Saída | Destino |
| --- | --- | --- | --- |
| Wake word detectada | Loop de voz | `listen()` | Backend do rosto |
| Frase pronta para a LLM | Loop de voz | `think()` | Backend do rosto |
| Resposta pronta para TTS | Loop de voz | `answer()` | Backend do rosto |
| Fim da fala ou abandono | Loop de voz | `sleep()` | Backend do rosto |

## Exceções

- `RaspberryLcdFace.render`: `NotImplementedError` com TODO até existir o driver do LCD.
- Falha da LLM: o loop chama `sleep()` sem passar por Answering.

## Fora de escopo

- Implementação real do LCD, GPIO, SPI ou framebuffer.
- Animações, boca sincronizada com o áudio, expressões extras.
