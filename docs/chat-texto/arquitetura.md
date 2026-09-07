# Arquitetura — Chat texto

## Contexto

O cérebro já aceita texto (`generate_reply`). O canal de texto é um segundo ponto de entrada, no pacote `agent`, para testar a LLM sem áudio. Não substitui a voz. O debug no Cursor lança um desses dois processos com o debugger anexado.

```
voz:   microfone → STT → LLM → TTS → alto-falante
texto: stdin     →      LLM →      stdout   # Reply: reasoning (opcional) + spoken
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Chat texto | `src/agent/text_chat.py` | `init_brain` + loop stdin → `generate_reply` → `Reply`; bloco `Raciocínio:` opcional e linha Jarvis com `spoken`; `sair` dispara o encerramento |
| Roteador | `src/main.py` | `--text` / `--lang` ou loop de voz; `voice` só no ramo sem `--text` |
| Cérebro | `src/agent/brain.py` | `generate_reply(...) -> Reply`; grava e carrega o histórico via `src/memory/` |
| Encerramento da sessão | `src/memory/conversation.py` | `get_active_session()` e `close_session()`; o canal não grava histórico |
| Launch | `.vscode/launch.json` | Configurações `debugpy` do Cursor |
| Testes | `tests/test_text_chat.py` | Flags, vazio, sair, erro, idioma |

## Fluxo

```
py -3.11 src/main.py [--text] [--lang pt|en]
        │
        ▼
load_settings()
        │
        ▼
start_api()              # bind síncrono; serve_forever em daemon
        ├── falha ──────► exceção; nenhum loop começa
        │
        ├── sem --text ─► import voice ─► run_listen_repeat()
        │
        └── --text ─────► run_text_chat()
                                │
                                ▼
        init_brain()     # instructions.md + ChatGroq + revisão Alembic
                ├── falha → exceção encerra processo e API; loop não começa
                │
                ▼
        loop:
          Você: <linha>
            ├── vazio / espaços     → de novo
            ├── sair|quit|exit
            │     ├── get_active_session()  → UUID | None (não cria)
            │     ├── se UUID → close_session(sid)
            │     └── fim
            ├── EOF / Ctrl+C → fim (sem encerrar sessão)
            └── texto
                  ├── generate_reply(texto, language) → Reply
                  ├── [se reply.reasoning] Raciocínio: / print reasoning
                  └── Jarvis [lang]: <spoken>
                  (exceção → print erro → loop)
```

Debug (Cursor):

```
F5 → launch.json → debugpy → src/main.py [--text]  (terminal integrado)
```

## Contratos

```python
def run_text_chat(language: str = "pt") -> None
def main(argv: list[str] | None = None) -> None
```

| Flag | Papel |
| --- | --- |
| `--text` | Abre o chat por texto; sem ela, voz |
| `--lang {pt,en}` | Idioma do prompt no modo texto; padrão `pt`; ignorada na voz |

Nenhuma variável de ambiente nova. Continuam `GROQ_API_KEY` e `GROQ_MODEL`.

`launch.json` (contrato do debug):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Jarvis: chat texto",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "args": ["--text"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "justMyCode": true
    },
    {
      "name": "Jarvis: voz",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "justMyCode": true
    }
  ]
}
```

## Dados

O canal não tem banco próprio nem arquivo de histórico. A sessão vive em Postgres via o cérebro (`src/memory/`). O chat só dispara o encerramento manual (`get_active_session` / `close_session`).

## Dependências

- Python 3.11
- LangChain + Groq (cérebro já existente)
- Extensão Python / `debugpy` no Cursor (não entra em `requirements.txt`)
- Hugging Face Hub: não usado neste canal
- Histórico: passa pelo cérebro / `src/memory/`; o canal só chama `get_active_session` e `close_session`

## Decisões

| Decisão | Motivo |
| --- | --- |
| Canal novo em `src/agent/text_chat.py`, não em `voice/` | O objetivo é pular áudio; o pacote de voz não deve ser importado |
| Import preguiçoso de `voice` em `main.py` | `voice` só entra no ramo sem `--text`; o modo texto não carrega microfone, Whisper, Piper nem a wake word |
| Reusar `generate_reply` sem wrapper de prompt | Testar os guardrails reais, não uma cópia |
| Ler `Reply` e imprimir `Raciocínio:` só quando houver | Canal de debug; sem raciocínio o stdout fica como antes |
| Idioma por flag, padrão `pt` | Sem Whisper não há detecção; o projeto é em português |
| `argparse` só com `--text` e `--lang` | `main.py` permanece roteador fino |
| Sem rosto no modo texto | Pedido é testar a LLM, não o hardware |
| `console: integratedTerminal` | `input()` não funciona no `internalConsole` |
| Sem path absoluto do Python no git | Cada máquina aponta o 3.11 pelo seletor do Cursor |
| Duas configs no `launch.json` | O mesmo arquivo serve para depurar texto e voz |
