# Padrões de implementação — Rosto do robô

## Convenções

- Interpretador: `py -3.11`
- Sem dependências fora da stack obrigatória da task
- Backends em classes separadas; o loop só conhece `RobotFace` / `create_face()`

## Contratos

```python
class FaceState(Enum):
    SLEEPING
    LISTENING
    THINKING
    ANSWERING

class RobotFace(ABC):
    def sleep(self) -> None
    def listen(self) -> None
    def think(self) -> None
    def answer(self) -> None
    def render(self, state: FaceState) -> None  # abstrato

def create_face() -> RobotFace  # hoje: TerminalFace
```

`TerminalFace` imprime linhas do tipo `rosto [-_-] sleeping`.  
`RaspberryLcdFace.render` levanta `NotImplementedError` com a marcação TODO.

Para usar o LCD no Pi, implementar `render` e trocar o retorno de `create_face()`.

## Testes

`tests/test_face.py`: estado inicial Sleeping; ciclo Listening → Thinking → Answering → Sleeping; factory devolve `TerminalFace`; LCD ainda não implementado.

## Decisões

| Decisão | Motivo |
| --- | --- |
| Métodos concretos + `render` abstrato | Os quatro comportamentos são iguais; só o desenho muda |
| Mock no terminal por padrão | Desenvolvimento no Windows, sem hardware |
| LCD só com TODO | Pedido explícito: não implementar a tela agora |
| Pacote `hardware/face/` | I/O do corpo, separado de locomoção em `robot/` |
