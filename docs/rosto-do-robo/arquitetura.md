# Arquitetura — Rosto do robô

## Contexto

O rosto é um atuador paralelo ao áudio, no mesmo loop:

```
Sleeping ──wake word──► Listening ──frase──► Thinking ──LLM──► Answering ──TTS──► Sleeping
```

Não substitui STT/LLM/TTS; só reflete o estágio atual. O backend de desenvolvimento é o terminal Windows; o de hardware (LCD no Raspberry Pi) fica reservado.

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| `FaceState` / `RobotFace` | `src/hardware/face/base.py` | Enum e classe abstrata (`sleep`, `listen`, `think`, `answer`, `render`) |
| `TerminalFace` | `src/hardware/face/terminal.py` | Mock ASCII no terminal |
| `RaspberryLcdFace` | `src/hardware/face/lcd.py` | Stub com TODO para o LCD |
| `create_face()` | `src/hardware/face/__init__.py` | Devolve `TerminalFace` até o LCD existir |
| Loop | `src/voice/listen_repeat.py` | Dispara as transições |

## Fluxo

```
create_face() → TerminalFace
        │
        ▼
sleep()     Aguardando "Jarvis"
listen()    Wake word ouvida
think()     generate_reply(...)
answer()    speak(resposta)
sleep()     Fim do turno
```

## Dados

Nenhum persistido. O estado vive na instância (`RobotFace.state`).

## Dependências

- Python 3.11
- Sem LangChain, Hugging Face ou Postgres nesta peça
