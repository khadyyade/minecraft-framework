"""
Configuración de pytest para el proyecto minecraft-framework.

Este archivo configura fixtures globales y mocks necesarios para ejecutar
los tests sin depender de Minecraft real.
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock


# =============================================================================
# MOCK DE MCPI
# =============================================================================
# Crear mocks del módulo mcpi para evitar dependencia de Minecraft

@pytest.fixture(scope="session", autouse=True)
def mock_mcpi_module():
    """
    Mock global del módulo mcpi que se aplica a toda la sesión de tests.

    Esto permite importar código que depende de mcpi sin tener Minecraft instalado.
    """
    # Crear mock de mcpi.block con los bloques comunes
    mock_block = MagicMock()

    # Bloques básicos (IDs de Minecraft Pi Edition)
    mock_block.AIR = Mock(id=0)
    mock_block.STONE = Mock(id=1)
    mock_block.GRASS = Mock(id=2)
    mock_block.DIRT = Mock(id=3)
    mock_block.COBBLESTONE = Mock(id=4)
    mock_block.WOOD_PLANKS = Mock(id=5)
    mock_block.SAPLING = Mock(id=6)
    mock_block.BEDROCK = Mock(id=7)
    mock_block.SAND = Mock(id=12)
    mock_block.GRAVEL = Mock(id=13)
    mock_block.GOLD_ORE = Mock(id=14)
    mock_block.IRON_ORE = Mock(id=15)
    mock_block.COAL_ORE = Mock(id=16)
    mock_block.WOOD = Mock(id=17)
    mock_block.LEAVES = Mock(id=18)
    mock_block.GLASS = Mock(id=20)
    mock_block.LAPIS_LAZULI_ORE = Mock(id=21)
    mock_block.LAPIS_LAZULI_BLOCK = Mock(id=22)
    mock_block.SANDSTONE = Mock(id=24)
    mock_block.BED = Mock(id=26)
    mock_block.COBWEB = Mock(id=30)
    mock_block.GRASS_TALL = Mock(id=31)
    mock_block.WOOL = Mock(id=35)
    mock_block.GOLD_BLOCK = Mock(id=41)
    mock_block.IRON_BLOCK = Mock(id=42)
    mock_block.STONE_SLAB_DOUBLE = Mock(id=43)
    mock_block.STONE_SLAB = Mock(id=44)
    mock_block.BRICK_BLOCK = Mock(id=45)
    mock_block.TNT = Mock(id=46)
    mock_block.BOOKSHELF = Mock(id=47)
    mock_block.MOSS_STONE = Mock(id=48)
    mock_block.OBSIDIAN = Mock(id=49)
    mock_block.TORCH = Mock(id=50)
    mock_block.FIRE = Mock(id=51)
    mock_block.STAIRS_WOOD = Mock(id=53)
    mock_block.CHEST = Mock(id=54)
    mock_block.DIAMOND_ORE = Mock(id=56)
    mock_block.DIAMOND_BLOCK = Mock(id=57)
    mock_block.CRAFTING_TABLE = Mock(id=58)
    mock_block.FARMLAND = Mock(id=60)
    mock_block.FURNACE_INACTIVE = Mock(id=61)
    mock_block.FURNACE_ACTIVE = Mock(id=62)
    mock_block.DOOR_WOOD = Mock(id=64)
    mock_block.LADDER = Mock(id=65)
    mock_block.STAIRS_COBBLESTONE = Mock(id=67)
    mock_block.DOOR_IRON = Mock(id=71)
    mock_block.REDSTONE_ORE = Mock(id=73)
    mock_block.SNOW = Mock(id=78)
    mock_block.ICE = Mock(id=79)
    mock_block.SNOW_BLOCK = Mock(id=80)
    mock_block.CACTUS = Mock(id=81)
    mock_block.CLAY = Mock(id=82)
    mock_block.SUGAR_CANE = Mock(id=83)
    mock_block.FENCE = Mock(id=85)
    mock_block.GLOWSTONE_BLOCK = Mock(id=89)
    mock_block.STONE_BRICK = Mock(id=98)
    mock_block.GLASS_PANE = Mock(id=102)
    mock_block.MELON = Mock(id=103)
    mock_block.FENCE_GATE = Mock(id=107)
    mock_block.NETHER_BRICK = Mock(id=112)
    mock_block.NETHER_BRICK_FENCE = Mock(id=113)
    mock_block.NETHER_BRICK_STAIRS = Mock(id=114)
    mock_block.SANDSTONE_STAIRS = Mock(id=128)
    mock_block.QUARTZ_BLOCK = Mock(id=155)

    # Mock de Minecraft connection
    mock_minecraft = MagicMock()
    mock_minecraft.Minecraft = MagicMock()
    mock_minecraft.Minecraft.create = MagicMock(return_value=MagicMock())

    # Insertar mocks en sys.modules
    sys.modules['mcpi'] = MagicMock()
    sys.modules['mcpi.minecraft'] = mock_minecraft
    sys.modules['mcpi.block'] = mock_block

    yield mock_block

    # Limpiar después de los tests
    if 'mcpi' in sys.modules:
        del sys.modules['mcpi']
    if 'mcpi.minecraft' in sys.modules:
        del sys.modules['mcpi.minecraft']
    if 'mcpi.block' in sys.modules:
        del sys.modules['mcpi.block']


# =============================================================================
# FIXTURES DE COLAS MOCKEADAS
# =============================================================================

class MockQueue:
    """Mock de multiprocessing.Queue para tests."""

    def __init__(self):
        self._items = []

    def put(self, item):
        self._items.append(item)

    def put_nowait(self, item):
        self._items.append(item)

    def get(self, block=True, timeout=None):
        if self._items:
            return self._items.pop(0)
        if not block:
            return None
        raise Exception("Queue empty")

    def get_nowait(self):
        if self._items:
            return self._items.pop(0)
        return None

    def empty(self):
        return len(self._items) == 0

    def qsize(self):
        return len(self._items)


@pytest.fixture
def mock_queue():
    """Fixture que proporciona una cola mockeada."""
    return MockQueue()


@pytest.fixture
def agent_queues():
    """Fixture que proporciona un set completo de colas para agentes."""
    return {
        "ExplorerBot": MockQueue(),
        "MinerBot": MockQueue(),
        "BuilderBot": MockQueue()
    }


# =============================================================================
# CONFIGURACIÓN DE PYTEST-ASYNCIO
# =============================================================================

@pytest.fixture
def event_loop():
    """Proporciona un event loop para tests asíncronos."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

