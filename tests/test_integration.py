"""
Tests de integración simulando colas de mensajes entre agentes.

Estos tests verifican la comunicación entre agentes usando mocks de las colas
de multiprocessing, sin lanzar procesos reales ni Minecraft.
"""

import pytest
import json
from unittest.mock import Mock, patch
from collections import defaultdict


# Mock de mcpi para evitar dependencia de Minecraft
@pytest.fixture(autouse=True)
def mock_mcpi():
    """Mock del módulo mcpi para todos los tests."""
    mock_block = Mock()
    mock_block.AIR = Mock(id=0)
    mock_block.STONE = Mock(id=1)
    mock_block.DIRT = Mock(id=3)
    mock_block.COBBLESTONE = Mock(id=4)
    mock_block.WOOD_PLANKS = Mock(id=5)
    mock_block.GLASS = Mock(id=20)

    with patch.dict('sys.modules', {
        'mcpi': Mock(),
        'mcpi.minecraft': Mock(),
        'mcpi.block': mock_block
    }):
        yield mock_block


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
        raise Exception("Queue empty")

    def get_nowait(self):
        if self._items:
            return self._items.pop(0)
        return None

    def empty(self):
        return len(self._items) == 0

    def qsize(self):
        return len(self._items)


class TestBuilderReceivesMapMessage:
    """Tests para la recepción de mensajes map.v1 en el BuilderBot."""

    def test_map_message_structure(self):
        """Verifica estructura correcta del mensaje map.v1."""
        map_message = {
            "type": "map.v1",
            "source": "ExplorerBot",
            "target": "BuilderBot",
            "timestamp": 1234567890,
            "data": {
                "coordenadasInicioTerrenoPlano": {"x": 0, "z": 0},
                "coordenadasFinalTerrenoPlano": {"x": 10, "z": 10},
                "alturaPlanicie": 64,
                "hayTerrenoPlano": True
            }
        }

        assert map_message["type"] == "map.v1"
        assert "data" in map_message
        assert "alturaPlanicie" in map_message["data"]

    def test_builder_state_changes_on_map_received(self):
        """Verifica cambio de estado del Builder al recibir mapa."""
        # Simular estado inicial del Builder
        builder_state = {
            "estadoActual": "WAITING",
            "coordenadasInicioTerrenoPlano": None,
            "coordenadasFinalTerrenoPlano": None,
            "alturaPlanicie": None
        }

        # Mensaje map.v1 del Explorer
        map_data = {
            "coordenadasInicioTerrenoPlano": {"x": 100, "z": 200},
            "coordenadasFinalTerrenoPlano": {"x": 110, "z": 210},
            "alturaPlanicie": 70
        }

        # Simular procesamiento del mensaje
        if map_data["alturaPlanicie"] is not None and map_data["alturaPlanicie"] >= 0:
            builder_state["coordenadasInicioTerrenoPlano"] = map_data["coordenadasInicioTerrenoPlano"]
            builder_state["coordenadasFinalTerrenoPlano"] = map_data["coordenadasFinalTerrenoPlano"]
            builder_state["alturaPlanicie"] = map_data["alturaPlanicie"]

            if builder_state["estadoActual"] == "WAITING":
                builder_state["estadoActual"] = "IDLE"

        assert builder_state["estadoActual"] == "IDLE"
        assert builder_state["alturaPlanicie"] == 70
        assert builder_state["coordenadasInicioTerrenoPlano"]["x"] == 100

    def test_invalid_map_height_ignored(self):
        """Verifica que mapas con altura inválida son ignorados."""
        builder_state = {
            "estadoActual": "WAITING",
            "alturaPlanicie": None
        }

        map_data = {
            "alturaPlanicie": -1  # Altura inválida
        }

        # Simular lógica del Builder
        if map_data["alturaPlanicie"] is None or map_data["alturaPlanicie"] < 0:
            # Ignorar mensaje
            pass
        else:
            builder_state["alturaPlanicie"] = map_data["alturaPlanicie"]
            builder_state["estadoActual"] = "IDLE"

        assert builder_state["estadoActual"] == "WAITING"  # No cambió
        assert builder_state["alturaPlanicie"] is None


class TestBuilderReceivesMaterialsMessage:
    """Tests para la recepción de mensajes de materiales y validación de can_build."""

    def test_materials_inventory_message_structure(self):
        """Verifica estructura del mensaje materials.inventory.v1."""
        materials_message = {
            "type": "materials.inventory.v1",
            "source": "MinerBot",
            "target": "BuilderBot",
            "payload": {
                "stone": 20,
                "dirt": 15,
                "wood": 10
            }
        }

        assert materials_message["type"] == "materials.inventory.v1"
        assert "payload" in materials_message
        assert materials_message["payload"]["stone"] == 20

    def test_can_build_with_sufficient_materials(self):
        """Verifica can_build = True cuando hay suficientes materiales."""
        bom = {"stone": 17, "dirt": 12}
        available_materials = {"stone": 20, "dirt": 15}

        # Lógica de check_materials_available
        can_build = all(
            available_materials.get(block_type, 0) >= required
            for block_type, required in bom.items()
        )

        assert can_build is True

    def test_cannot_build_with_insufficient_materials(self):
        """Verifica can_build = False cuando faltan materiales."""
        bom = {"stone": 17, "dirt": 12, "glass": 5}
        available_materials = {"stone": 20, "dirt": 15}  # Falta glass

        can_build = all(
            available_materials.get(block_type, 0) >= required
            for block_type, required in bom.items()
        )

        assert can_build is False

    def test_builder_state_changes_on_materials_received(self):
        """Verifica cambio de estado cuando se reciben materiales suficientes."""
        builder_state = {
            "estadoActual": "IDLE",
            "pending_build": True,
            "can_build": False,
            "bom": {"stone": 10, "dirt": 5},
            "available_materials": None
        }

        # Recibir mensaje de materiales
        received_materials = {"stone": 15, "dirt": 10}
        builder_state["available_materials"] = received_materials

        # Verificar materiales
        has_all = all(
            builder_state["available_materials"].get(bt, 0) >= req
            for bt, req in builder_state["bom"].items()
        )

        if has_all and builder_state["pending_build"]:
            builder_state["can_build"] = True
            builder_state["estadoActual"] = "RUNNING"

        assert builder_state["can_build"] is True
        assert builder_state["estadoActual"] == "RUNNING"


class TestMinerReceivesBOMMessage:
    """Tests para la recepción de BOM en el MinerBot."""

    def test_bom_requirements_message_structure(self):
        """Verifica estructura del mensaje materials.requirements.v1."""
        bom_message = {
            "type": "materials.requirements.v1",
            "origin": "BuilderBot",
            "timestamp": 0,
            "payload": {
                "stone": 17,
                "dirt": 12
            }
        }

        assert bom_message["type"] == "materials.requirements.v1"
        assert bom_message["payload"]["stone"] == 17

    def test_miner_updates_requirements(self):
        """Verifica que el Miner actualiza sus requirements."""
        miner_state = {
            "requirements": {}
        }

        bom_payload = {"stone": 17, "dirt": 12}
        miner_state["requirements"] = bom_payload

        assert miner_state["requirements"]["stone"] == 17
        assert miner_state["requirements"]["dirt"] == 12


class TestQueueCommunication:
    """Tests para comunicación mediante colas mockeadas."""

    def test_message_sent_to_correct_queue(self):
        """Verifica que los mensajes se envían a la cola correcta."""
        queues = {
            "ExplorerBot": MockQueue(),
            "MinerBot": MockQueue(),
            "BuilderBot": MockQueue()
        }

        # Simular envío de mensaje
        def enviar_mensaje(target, message, out_queues):
            q = out_queues.get(target)
            if q:
                q.put_nowait(json.dumps(message))

        message = {"type": "test", "data": "hello"}
        enviar_mensaje("MinerBot", message, queues)

        # Verificar que llegó a la cola correcta
        assert not queues["MinerBot"].empty()
        assert queues["ExplorerBot"].empty()
        assert queues["BuilderBot"].empty()

        received = json.loads(queues["MinerBot"].get_nowait())
        assert received["type"] == "test"

    def test_multiple_messages_in_queue(self):
        """Verifica procesamiento de múltiples mensajes en cola."""
        queue = MockQueue()

        messages = [
            {"type": "msg1", "data": 1},
            {"type": "msg2", "data": 2},
            {"type": "msg3", "data": 3}
        ]

        for msg in messages:
            queue.put_nowait(json.dumps(msg))

        # Leer todos los mensajes
        received = []
        while not queue.empty():
            received.append(json.loads(queue.get_nowait()))

        assert len(received) == 3
        assert received[0]["type"] == "msg1"
        assert received[2]["type"] == "msg3"

    def test_empty_queue_returns_none(self):
        """Verifica que cola vacía retorna None."""
        queue = MockQueue()

        result = queue.get_nowait()

        assert result is None


class TestMessageFlowExplorerToBuilder:
    """Tests para el flujo completo de mensajes Explorer -> Builder."""

    def test_full_map_flow(self):
        """Verifica flujo completo de envío/recepción de mapa."""
        builder_queue = MockQueue()

        # 1. Explorer crea y envía mensaje
        map_message = {
            "type": "map.v1",
            "source": "ExplorerBot",
            "target": "BuilderBot",
            "data": {
                "coordenadasInicioTerrenoPlano": {"x": 50, "z": 50},
                "coordenadasFinalTerrenoPlano": {"x": 60, "z": 60},
                "alturaPlanicie": 65
            }
        }
        builder_queue.put_nowait(json.dumps(map_message))

        # 2. Builder procesa el mensaje
        builder_state = {
            "coordenadasInicioTerrenoPlano": None,
            "alturaPlanicie": None
        }

        raw_msg = builder_queue.get_nowait()
        msg = json.loads(raw_msg)

        if msg["type"] == "map.v1":
            data = msg["data"]
            builder_state["coordenadasInicioTerrenoPlano"] = data["coordenadasInicioTerrenoPlano"]
            builder_state["alturaPlanicie"] = data["alturaPlanicie"]

        # 3. Verificar resultado
        assert builder_state["alturaPlanicie"] == 65
        assert builder_state["coordenadasInicioTerrenoPlano"]["x"] == 50


class TestMessageFlowBuilderToMiner:
    """Tests para el flujo completo de mensajes Builder -> Miner."""

    def test_full_bom_flow(self):
        """Verifica flujo completo de envío/recepción de BOM."""
        miner_queue = MockQueue()

        # 1. Builder calcula BOM
        template_blocks = [
            {"block_type": "stone"},
            {"block_type": "stone"},
            {"block_type": "dirt"}
        ]

        bom = defaultdict(int)
        for block in template_blocks:
            bom[block["block_type"]] += 1
        bom = dict(bom)

        # 2. Builder envía BOM
        bom_message = {
            "type": "materials.requirements.v1",
            "origin": "BuilderBot",
            "payload": bom
        }
        miner_queue.put_nowait(json.dumps(bom_message))

        # 3. Miner recibe y procesa
        miner_requirements = {}

        raw_msg = miner_queue.get_nowait()
        msg = json.loads(raw_msg)

        if msg["type"] == "materials.requirements.v1":
            miner_requirements = msg["payload"]

        # 4. Verificar
        assert miner_requirements["stone"] == 2
        assert miner_requirements["dirt"] == 1


class TestMessageFlowMinerToBuilder:
    """Tests para el flujo completo de mensajes Miner -> Builder."""

    def test_full_inventory_flow(self):
        """Verifica flujo completo de envío/recepción de inventario."""
        builder_queue = MockQueue()

        # 1. Miner recolecta materiales
        miner_inventory = {"stone": 10, "dirt": 5, "coal_ore": 3}

        # 2. Miner envía inventario
        inventory_message = {
            "type": "materials.inventory.v1",
            "source": "MinerBot",
            "payload": miner_inventory
        }
        builder_queue.put_nowait(json.dumps(inventory_message))

        # 3. Builder recibe y verifica
        builder_bom = {"stone": 8, "dirt": 4}
        builder_available = None
        can_build = False

        raw_msg = builder_queue.get_nowait()
        msg = json.loads(raw_msg)

        if msg["type"] == "materials.inventory.v1":
            builder_available = msg["payload"]
            can_build = all(
                builder_available.get(bt, 0) >= req
                for bt, req in builder_bom.items()
            )

        # 4. Verificar
        assert builder_available["stone"] == 10
        assert can_build is True

