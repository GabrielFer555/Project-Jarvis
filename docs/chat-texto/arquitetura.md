# Arquitetura — Chat texto

## Contexto

O cérebro já aceita texto (`generate_reply`). O canal de texto é um segundo ponto de entrada, no pacote `agent`, para testar a LLM sem áudio. Não substitui a voz. O debug no Cursor lança um desses dois processos com o debugger anexado.

```
voz:   microfone → STT → LLM → TTS → alto-falante
texto: stdin     →      LLM →      stdout
```

## Componentes

| Componente | Módulo | Responsabilidade |
| --- | --- | --- |
| Chat texto | `src/agent/text_chat.py` | `init_brain` + loop stdin → `generate_reply` → stdout |
| Roteador | `src/main.py` | `--text` / `--lang` ou loop de voz; `voice` só no ramo sem `--text` |
| Cérebro (inalterado) | `src/agent/brain.py` | Prompt, guardrails, `ChatGroq` |
| Launch | `.vscode/launch.json` | Configurações `debugpy` do Cursor |
| Testes | `tests/test_text_chat.py` | Flags, vazio, sair, erro, idioma |

## Fluxo

```
py -3.11 src/main.py [--text] [--lang pt|en]
        │
        ├── sem --text ──► import voice ──► run_listen_repeat()
        │
        └── --text
                │
                ▼
        init_brain()     # .env + instructions.md + ChatGroq
                │
                ▼
        loop:
          Você: <linha>
            ├── vazio / espaços     → de novo
            ├── sair|quit|exit|EOF  → fim
            └── texto
                  ├── generate_reply(texto, language)
                  └── Jarvis [lang]: <resposta>
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

Nenhum banco. Sem histórico em arquivo. O `.env` já existente.

## Dependências

- Python 3.11
- LangChain + Groq (cérebro já existente)
- Extensão Python / `debugpy` no Cursor (não entra em `requirements.txt`)
- Hugging Face Hub: não usado neste canal
- Postgres: não usado

## Decisões

| Decisão | Motivo |
| --- | --- |
| Canal novo em `src/agent/text_chat.py`, não em `voice/` | O objetivo é pular áudio; o pacote de voz não deve ser importado |
| Import preguiçoso de `voice` em `main.py` | `voice` só entra no ramo sem `--text`; o modo texto não carrega microfone, Whisper, Piper nem a wake word |
| Reusar `generate_reply` sem wrapper de prompt | Testar os guardrails reais, não uma cópia |
| Idioma por flag, padrão `pt` | Sem Whisper não há detecção; o projeto é em português |
| `argparse` só com `--text` e `--lang` | `main.py` permanece roteador fino |
| Sem rosto no modo texto | Pedido é testar a LLM, não o hardware |
| `console: integratedTerminal` | `input()` não funciona no `internalConsole` |
| Sem path absoluto do Python no git | Cada máquina aponta o 3.11 pelo seletor do Cursor |
| Duas configs no `launch.json` | O mesmo arquivo serve para depurar texto e voz |
