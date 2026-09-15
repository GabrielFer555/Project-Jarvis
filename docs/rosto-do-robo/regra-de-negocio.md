# Regra de negócio — Rosto do robô

## Objetivo

O robô tem um “rosto” com quatro estados, alinhados ao loop de conversa: dormindo por padrão, escutando quando ouve **Jarvis** e durante a janela após o TTS, pensando enquanto a LLM trabalha, respondendo enquanto o TTS fala, e de volta a dormir quando a janela fecha.

## Comportamento

| Estado | Quando |
| --- | --- |
| Sleeping | Padrão; espera a wake word; quando a janela fecha ou a LLM falha |
| Listening | A wake word foi reconhecida (ainda pode estar ouvendo a pergunta); durante a janela após o TTS |
| Thinking | A frase chegou e está na LLM |
| Answering | A resposta está sendo falada; em seguida Listening (janela) |

- Sem wake word, o rosto permanece Sleeping até alguém dizer **Jarvis**.
- Se **Jarvis** não vier seguido de frase, volta a Sleeping sem Thinking/Answering.
- Depois de Answering, o rosto fica **Listening** enquanto a janela de conversa está aberta. Sleeping só quando a janela fecha (silêncio, transcrição vazia ou só wake word sem pergunta) ou a LLM falha.
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
