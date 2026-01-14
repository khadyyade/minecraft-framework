# 🧪 Documentación de Testing - Minecraft Framework

## Índice
1. [Introducción](#introducción)
2. [Objetivos de Testing](#objetivos-de-testing)
3. [Arquitectura de Tests](#arquitectura-de-tests)
4. [Tests Implementados](#tests-implementados)
5. [Estrategia de Mocking](#estrategia-de-mocking)
6. [CI/CD con GitHub Actions](#cicd-con-github-actions)
7. [Ejecución de Tests](#ejecución-de-tests)
8. [Cobertura de Código](#cobertura-de-código)

---

## Introducción

Este documento describe la **fase de testing** del proyecto `minecraft-framework`, un sistema multi-agente para automatización en Minecraft Pi Edition. La estrategia de testing está diseñada para ser **independiente de Minecraft**, utilizando mocks para todas las dependencias externas.

### Tecnologías Utilizadas
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| pytest | ≥7.0.0 | Framework de testing |
| pytest-asyncio | ≥0.21.0 | Soporte para tests asíncronos |
| pytest-cov | ≥4.0.0 | Cobertura de código |
| unittest.mock | stdlib | Mocking de dependencias |

---

## Objetivos de Testing

### Objetivos Principales
1. **Validar el parseo de comandos** del ChatRouter sin conexión a Minecraft
2. **Verificar el cálculo del BOM** (Bill of Materials) del BuilderBot
3. **Testear estrategias de minería** del MinerBot (vertical, grid, vein)
4. **Simular comunicación entre agentes** mediante colas mockeadas
5. **Verificar sincronización** de estados (pause, resume, stop)

### Restricciones
- ❌ No usar Minecraft real
- ❌ No modificar la lógica del proyecto
- ✅ Mockear todas las dependencias externas
- ✅ Mantener código claro y sencillo (enfoque académico)

---

## Arquitectura de Tests

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Configuración global y fixtures
├── test_cli_parse.py        # Tests unitarios - Parser CLI
├── test_builder.py          # Tests unitarios - BOM BuilderBot
├── test_miner_strategies.py # Tests unitarios - Estrategias MinerBot
├── test_integration.py      # Tests de integración - Colas
└── test_sync.py             # Tests de sincronización - Estados
```

### Diagrama de Dependencias

```
┌─────────────────────────────────────────────────────────────┐
│                        conftest.py                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Mock mcpi      │  │  MockQueue      │  │  Fixtures   │ │
│  │  (block, mc)    │  │  (multiprocess) │  │  (queues)   │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
└───────────┼────────────────────┼─────────────────┼─────────┘
            │                    │                 │
    ┌───────▼───────┐    ┌───────▼───────┐   ┌────▼────┐
    │ test_cli_parse│    │test_integration│   │test_sync│
    │ test_builder  │    └───────────────┘   └─────────┘
    │test_miner_str │
    └───────────────┘
```

---

## Tests Implementados

### 1. Tests Unitarios del Parser CLI (`test_cli_parse.py`)

Valida que `parse_command()` interprete correctamente los comandos de chat.

#### Clases de Test

| Clase | Descripción | Nº Tests |
|-------|-------------|----------|
| `TestParseCommandAgent` | Comandos globales `$agent` | 6 |
| `TestParseCommandExplorer` | Comandos `$explorer` | 7 |
| `TestParseCommandMiner` | Comandos `$miner` | 10 |
| `TestParseCommandBuilder` | Comandos `$builder` | 9 |
| `TestParseCommandEdgeCases` | Casos límite | 4 |

#### Ejemplos de Tests

```python
def test_miner_set_strategy_vertical():
    """Verifica parseo de $miner set strategy vertical."""
    result = parse_command("$miner set strategy vertical")
    assert result == {
        "type": "control",
        "target": "MinerBot",
        "payload": {"cmd": "update", "args": {"strategy": "vertical"}}
    }

def test_builder_plan_set_refugio():
    """Verifica parseo de $builder plan set refugio."""
    result = parse_command("$builder plan set refugio")
    assert result == {
        "type": "control",
        "target": "BuilderBot",
        "payload": {"cmd": "update", "args": {"plan_set": "refugio"}}
    }
```

---

### 2. Tests del BuilderBot (`test_builder.py`)

Valida el cálculo del BOM y verificación de materiales.

#### Clases de Test

| Clase | Descripción | Nº Tests |
|-------|-------------|----------|
| `TestBOMCalculation` | Cálculo de Bill of Materials | 5 |
| `TestCheckMaterialsAvailable` | Verificación de materiales | 5 |

#### Ejemplo: Test del BOM con CSV real

```python
def test_calculate_bom_refugio_csv():
    """Verifica cálculo de BOM del template refugio.csv real."""
    # Parsear CSV del template refugio
    # ...
    result = dict(bom)
    
    assert result['stone'] == 17  # 8 en layer 0 + 9 en layer 4
    assert result['dirt'] == 12   # 4 en cada layer 1, 2, 3
    assert sum(result.values()) == 29  # Total de bloques
```

---

### 3. Tests de Estrategias de Minería (`test_miner_strategies.py`)

Valida las tres estrategias del MinerBot.

#### Estrategia Vertical

| Test | Descripción |
|------|-------------|
| `test_first_target_returns_origin` | Primer target = origen |
| `test_subsequent_targets_go_down` | Targets bajan en Y |
| `test_max_depth_returns_none` | None al llegar a max_depth |
| `test_bedrock_level_returns_none` | None al llegar a Y=0 |
| `test_missing_origin_returns_none` | None sin coordenadas |

#### Estrategia Grid

| Test | Descripción |
|------|-------------|
| `test_first_target_at_origin` | Primer target = origen |
| `test_moves_to_next_column_after_depth` | Avanza columna tras depth |
| `test_moves_to_next_row_after_columns` | Avanza fila tras columnas |
| `test_returns_none_when_grid_complete` | None al completar grid |
| `test_correct_coordinates_in_grid` | Coordenadas X,Z correctas |

#### Estrategia Vein (BFS)

| Test | Descripción |
|------|-------------|
| `test_consumes_discovered_neighbors` | Consume vecinos descubiertos |
| `test_uses_frontier_fifo` | BFS con FIFO |
| `test_skips_visited_positions` | Salta posiciones visitadas |
| `test_respects_max_depth` | Respeta límite de profundidad |

#### Inmutabilidad del Estado

```python
def test_vertical_state_immutability():
    """Verifica que el estado original no se modifica."""
    state = {'origin_x': 10, 'current_depth': 5, ...}
    original_state = dict(state)
    
    strategy.next_target(state, missing)
    
    assert state == original_state  # Estado original intacto
```

---

### 4. Tests de Integración (`test_integration.py`)

Simula la comunicación entre agentes mediante colas mockeadas.

#### Flujos Testeados

```
┌─────────────┐   map.v1    ┌─────────────┐
│ ExplorerBot │ ──────────► │ BuilderBot  │
└─────────────┘             └──────┬──────┘
                                   │
                    materials.requirements.v1
                                   │
                                   ▼
                            ┌─────────────┐
                            │  MinerBot   │
                            └──────┬──────┘
                                   │
                    materials.inventory.v1
                                   │
                                   ▼
                            ┌─────────────┐
                            │ BuilderBot  │
                            └─────────────┘
```

#### Clases de Test

| Clase | Descripción |
|-------|-------------|
| `TestBuilderReceivesMapMessage` | Recepción de map.v1 |
| `TestBuilderReceivesMaterialsMessage` | Recepción de inventario |
| `TestMinerReceivesBOMMessage` | Recepción de requirements |
| `TestQueueCommunication` | Comunicación por colas |
| `TestMessageFlowExplorerToBuilder` | Flujo Explorer→Builder |
| `TestMessageFlowBuilderToMiner` | Flujo Builder→Miner |
| `TestMessageFlowMinerToBuilder` | Flujo Miner→Builder |

---

### 5. Tests de Sincronización (`test_sync.py`)

Verifica el comportamiento de los comandos de control.

#### Máquina de Estados

```
         ┌──────────────────────────────────────┐
         │                                      │
         ▼                                      │
    ┌────────┐  start   ┌─────────┐  pause  ┌──────┐
    │  IDLE  │ ───────► │ RUNNING │ ──────► │PAUSED│
    └────────┘          └────┬────┘         └──┬───┘
                             │                 │
                             │ stop       resume
                             │                 │
                             ▼                 │
                       ┌─────────┐             │
                       │ STOPPED │ ◄───────────┘
                       └─────────┘      stop
```

#### Tests Implementados

| Clase | Tests |
|-------|-------|
| `TestPauseCommand` | pause desde RUNNING, WAITING, IDLE, STOPPED |
| `TestResumeCommand` | resume desde PAUSED, RUNNING, IDLE, STOPPED |
| `TestStopCommand` | stop desde todos los estados |
| `TestActNotExecutedWhenPaused` | Verificar que act() no ejecuta en PAUSED |
| `TestStateTransitions` | Transiciones válidas de estado |
| `TestConcurrentStateAccess` | Acceso concurrente simulado |

#### Test Clave: act() No Ejecuta en PAUSED

```python
@pytest.mark.asyncio
async def test_act_not_called_when_paused():
    """Verifica que act() no se ejecuta cuando el agente está pausado."""
    agent = MockAgent("TestBot")
    agent.estadoActual = EstadoAgente.PAUSED
    
    await agent.act({"action": "BUILD"})
    
    assert agent.act_called is False
    assert agent.act_call_count == 0
```

---

## Estrategia de Mocking

### Mock de mcpi (Minecraft Pi API)

El archivo `conftest.py` mockea completamente el módulo mcpi:

```python
@pytest.fixture(scope="session", autouse=True)
def mock_mcpi_module():
    # Mock de bloques
    mock_block = MagicMock()
    mock_block.STONE = Mock(id=1)
    mock_block.DIRT = Mock(id=3)
    mock_block.COBBLESTONE = Mock(id=4)
    # ... más bloques
    
    # Insertar en sys.modules
    sys.modules['mcpi'] = MagicMock()
    sys.modules['mcpi.minecraft'] = mock_minecraft
    sys.modules['mcpi.block'] = mock_block
```

### MockQueue para Multiprocessing

```python
class MockQueue:
    """Mock de multiprocessing.Queue para tests."""
    
    def __init__(self):
        self._items = []
    
    def put_nowait(self, item):
        self._items.append(item)
    
    def get_nowait(self):
        if self._items:
            return self._items.pop(0)
        return None
    
    def empty(self):
        return len(self._items) == 0
```

---

## CI/CD con GitHub Actions

### Workflow: `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Instalar dependencias
      run: |
        pip install pytest pytest-asyncio pytest-cov
    - name: Ejecutar tests
      run: pytest tests/ -v --tb=short
```

### Pipeline de CI/CD

```
┌──────────────────────────────────────────────────────────────┐
│                     GitHub Actions                           │
├──────────────────────────────────────────────────────────────┤
│  Trigger: push/PR a main, master, develop                    │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  Python 3.10    │    │  Python 3.11    │                 │
│  │                 │    │                 │                 │
│  │ 1. Checkout     │    │ 1. Checkout     │                 │
│  │ 2. Setup Python │    │ 2. Setup Python │                 │
│  │ 3. pip install  │    │ 3. pip install  │                 │
│  │ 4. pytest       │    │ 4. pytest       │                 │
│  │                 │    │ 5. Coverage     │                 │
│  └─────────────────┘    └─────────────────┘                 │
│                                                              │
│  ┌─────────────────┐                                        │
│  │     Lint        │  flake8 (no bloqueante)                │
│  └─────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Ejecución de Tests

### Instalación de Dependencias

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Comandos de Ejecución

| Comando | Descripción |
|---------|-------------|
| `pytest tests/ -v` | Ejecutar todos los tests |
| `pytest tests/ -v --tb=short` | Con traceback corto |
| `pytest tests/test_cli_parse.py` | Solo tests de CLI |
| `pytest tests/test_miner_strategies.py` | Solo estrategias |
| `pytest tests/test_integration.py` | Solo integración |
| `pytest tests/test_sync.py` | Solo sincronización |
| `pytest tests/ -k "vertical"` | Tests que contengan "vertical" |
| `pytest tests/ -x` | Parar al primer fallo |

### Ejecución con Cobertura

```bash
# Reporte en terminal
pytest tests/ --cov=minecraft_framework --cov-report=term-missing

# Generar HTML
pytest tests/ --cov=minecraft_framework --cov-report=html

# Generar XML (para CI)
pytest tests/ --cov=minecraft_framework --cov-report=xml
```

---

## Cobertura de Código

### Métricas Objetivo

| Métrica | Objetivo | Descripción |
|---------|----------|-------------|
| Line Coverage | > 70% | Líneas ejecutadas |
| Branch Coverage | > 60% | Ramas condicionales |
| Function Coverage | > 80% | Funciones testeadas |

### Módulos Cubiertos

| Módulo | Tests Asociados |
|--------|-----------------|
| `minecraft_framework/cli.py` | `test_cli_parse.py` |
| `minecraft_framework/strategies/*.py` | `test_miner_strategies.py` |
| `minecraft_framework/agents/builder.py` | `test_builder.py` |
| `minecraft_framework/baseAgent.py` | `test_sync.py` |
| Comunicación inter-agentes | `test_integration.py` |

---

## Resumen de Tests

| Archivo | Tipo | Nº Tests | Descripción |
|---------|------|----------|-------------|
| `test_cli_parse.py` | Unitario | ~36 | Parser de comandos |
| `test_builder.py` | Unitario | ~10 | BOM y materiales |
| `test_miner_strategies.py` | Unitario | ~20 | Estrategias minería |
| `test_integration.py` | Integración | ~15 | Colas y mensajes |
| `test_sync.py` | Sincronización | ~18 | Estados y control |
| **Total** | | **~99** | |

---

## Conclusiones

La estrategia de testing implementada garantiza:

1. ✅ **Independencia de Minecraft**: Todos los tests funcionan sin servidor
2. ✅ **Cobertura completa del CLI**: Todos los comandos están testeados
3. ✅ **Validación de estrategias**: Las 3 estrategias de minería verificadas
4. ✅ **Comunicación simulada**: Flujos de mensajes probados con mocks
5. ✅ **Control de estados**: Pause/resume/stop funcionan correctamente
6. ✅ **CI/CD automatizado**: Tests en cada push/PR

---

*Documentación generada para el proyecto TAP - URV - 2024/2025*

