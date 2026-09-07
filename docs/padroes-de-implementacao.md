# Padrões de implementação — Project Jarvis

Arquivo único do projeto. Vale para toda task e **não** é reescrito por feature: o que é específico de uma funcionalidade mora no `arquitetura.md` dela, em `## Contratos`.

A skill `spec` respeita estes padrões ao montar o plano. A skill `rock-it` lê este arquivo antes do primeiro despacho. Só uma task que mude padrão do projeto altera este documento.

## Convenções

- Interpretador: `py -3.11`. Neste Windows, `py` sem versão abre o 3.14, que não tem as dependências.
- Escopo fechado: só o que está nos requisitos funcionais do plano. Sem refactor, extra ou "melhoria" não pedida.
- Código novo em `src/`, no pacote da etapa (`voice`, `agent`, `memory`, `hardware`, `vision`, `robot`).
- `src/main.py` permanece um ponto de entrada fino: roteia para o loop, não contém regra.
- Sem dependência fora da stack obrigatória; nada de substituto equivalente por conveniência.
- Segredos no `.env`; `.env.example` documenta as chaves. A chave real não entra no git.
- Fail-closed na subida: credencial ou arquivo obrigatório ausente levanta `RuntimeError` antes do loop começar.
- Identidade e guardrails da LLM ficam em markdown (`src/agent/instructions.md`), não em string no Python.
- Backend de hardware em classe separada; o loop conhece só a abstração (ex.: `RobotFace` / `create_face()`).

## Stack obrigatória

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.11 |
| Cérebro (LLM) | Groq via LangChain (`ChatGroq`) |
| Orquestração de LLM | LangChain (`langchain-core`, `langchain-groq`) |
| STT | `faster-whisper` |
| TTS | Piper |
| Artefatos de voz | Hugging Face Hub (modelos Whisper e vozes Piper) |
| Banco vetorial | Postgres |

O Hugging Face Hub é fonte de artefatos STT/TTS, **não** provedor do cérebro.

## Comandos

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 src/main.py
py -3.11 src/main.py --text
py -3.11 -m compileall src
py -3.11 -m unittest discover -s tests -v
```

`compileall` é o build deste repositório (Python puro, sem empacotamento): erro de sintaxe ou import quebrado bloqueia a etapa. Os testes são `unittest`; `pytest` não é dependência do projeto.

## Formato do plano

Cabeçalho: branch base, modo de execução (`non stop` ou `parada por execução`) e progresso `N/M etapas` (a spec inicializa em `0/N`; o rock-it atualiza).

Corpo: descrição breve, requisitos funcionais, implementação técnica por etapas e casos de teste em Gherkin. Snapshot de código só em caso importante (contrato, API frágil, algoritmo); o resto descreve arquivos e responsabilidades.

Seções obrigatórias no fim do plano: cobertura de testes (ou o motivo de não haver), fora de escopo, dúvidas impeditivas e o checklist de documentação com caminhos concretos.

## Documentação

Dois lugares, com papéis diferentes:

| Lugar | Papel | Quem escreve |
| --- | --- | --- |
| `docs/<funcionalidade>/regra-de-negocio.md` e `arquitetura.md` | Fonte viva e canônica de cada funcionalidade | rock-it, conforme o checklist do plano |
| `docs/README.md` | Índice do mapa de funcionalidades | rock-it, quando entra funcionalidade nova |
| `docs/progresso.md` | Diário datado do projeto | rock-it |
| `docs/padroes-de-implementacao.md` | Este arquivo: padrões vigentes | rock-it, só se a task mudar um padrão |
| `spec/task-{slug}-{NNN}/plano.md`, `regra-de-negocio.md`, `arquitetura.md` | Registro da decisão daquela task, congelado no tempo | spec, no planejamento |
| `README.md` | Visão, estrutura, como rodar, progresso | rock-it |

Regra de decisão entre atualizar e criar:

- A feature toca funcionalidade já mapeada em `docs/` → **atualizar** a pasta existente, por profunda que seja a mudança. Nunca criar pasta paralela para a mesma funcionalidade.
- A feature é capacidade nova, sem pasta que a cubra → **criar** `docs/<nova>/` com os dois arquivos e registrar no índice.
- Na dúvida, atualizar.
- Doc não relacionada à feature não é tocada.

Ao atualizar, mexer só no que a task mudou. Não reescrever o documento inteiro nem apagar histórico de `docs/progresso.md`.

## Testes

Gherkin: um `Scenario` por comportamento distinto. Não repetir o mesmo fluxo com dados cosméticos.

Testes automatizados só quando houver necessidade real: lógica ramificada, contrato ou regressão. Sem rede nos testes — cliente de LLM, microfone e TTS entram mockados. Se não houver necessidade, dizer isso no plano em vez de criar teste vazio ou que só espelha o Gherkin sem assert útil.

## Evitar

- Spec implementar código, testes ou docs de `docs/` (isso é rock-it).
- Rock-it marcar etapa com o gate vermelho, ou pular gate por aprovação do usuário.
- Cenário de teste redundante.
- Implementação além do plano.

## Decisões do projeto

| Decisão | Motivo |
| --- | --- |
| `py -3.11` obrigatório | `py` sem versão abre o 3.14, sem as dependências |
| Groq como cérebro, via LangChain | Stack fechada; o Hub fica só com Whisper e Piper |
| `.env` + `.env.example` | A chave não entra no git; o exemplo documenta as chaves |
| Falta de credencial aborta na subida | Erro claro no início em vez de falha no meio da conversa |
| Instruções da LLM em `instructions.md` | Tom, limites e recusas mudam sem tocar Python |
| Cérebro sem tools, RAG ou memória | Cada capacidade entra como etapa própria, validada sozinha |
| Métodos concretos e `render` abstrato no rosto | Os quatro comportamentos são iguais; só o desenho muda |
| Mock no terminal quando falta hardware | Desenvolvimento no Windows, sem Raspberry Pi |
| Pasta por task em `spec/task-{slug}-{NNN}/` | Ordem cronológica na raiz, sem colisão de slug |
| Spec planeja e para; rock-it executa | Separar contrato de execução |
| `docs/` canônico e pasta da task congelada | Uma fonte viva por funcionalidade, sem cópias divergentes |
| Padrões num único arquivo global | Evita repetir as mesmas convenções em cada feature |
| `synthesize_wav()` no Piper | Na API 1.6 é quem grava o WAV |
| `output.wav` no `.gitignore` | É arquivo gerado |
