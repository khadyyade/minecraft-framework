"""
Tests unitarios para el parseo de comandos CLI (ChatRouter).

Estos tests verifican que parse_command() interprete correctamente los comandos
de chat sin necesidad de Minecraft real.
"""

import pytest
from minecraft_framework.cli import parse_command


class TestParseCommandAgent:
    """Tests para comandos globales de $agent."""

    def test_agent_stop(self):
        """Verifica parseo de $agent stop."""
        result = parse_command("$agent stop")
        assert result == {
            "type": "control",
            "target": "ALL",
            "payload": {"cmd": "stop"}
        }

    def test_agent_pause(self):
        """Verifica parseo de $agent pause."""
        result = parse_command("$agent pause")
        assert result == {
            "type": "control",
            "target": "ALL",
            "payload": {"cmd": "pause"}
        }

    def test_agent_resume(self):
        """Verifica parseo de $agent resume."""
        result = parse_command("$agent resume")
        assert result == {
            "type": "control",
            "target": "ALL",
            "payload": {"cmd": "resume"}
        }

    def test_agent_status(self):
        """Verifica parseo de $agent status."""
        result = parse_command("$agent status")
        assert result == {
            "type": "control",
            "target": "ALL",
            "payload": {"cmd": "status"}
        }

    def test_agent_help(self):
        """Verifica parseo de $agent help."""
        result = parse_command("$agent help")
        assert result == {
            "type": "control",
            "target": "ALL",
            "payload": {"cmd": "help"}
        }

    def test_agent_invalid_command(self):
        """Verifica que comandos inválidos de $agent retornan vacío."""
        result = parse_command("$agent invalid")
        assert result == {}


class TestParseCommandExplorer:
    """Tests para comandos del ExplorerBot."""

    def test_explorer_start_with_coords(self):
        """Verifica parseo de $explorer start x=0 z=0."""
        result = parse_command("$explorer start x=0 z=0")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "update", "args": {"start": {"x": 0, "z": 0}}}
        }

    def test_explorer_start_with_different_coords(self):
        """Verifica parseo con coordenadas diferentes."""
        result = parse_command("$explorer start x=100 z=-50")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "update", "args": {"start": {"x": 100, "z": -50}}}
        }

    def test_explorer_stop(self):
        """Verifica parseo de $explorer stop."""
        result = parse_command("$explorer stop")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "stop"}
        }

    def test_explorer_pause(self):
        """Verifica parseo de $explorer pause."""
        result = parse_command("$explorer pause")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "pause"}
        }

    def test_explorer_resume(self):
        """Verifica parseo de $explorer resume."""
        result = parse_command("$explorer resume")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "resume"}
        }

    def test_explorer_status(self):
        """Verifica parseo de $explorer status."""
        result = parse_command("$explorer status")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "status"}
        }

    def test_explorer_set_range(self):
        """Verifica parseo de $explorer set range 20."""
        result = parse_command("$explorer set range 20")
        assert result == {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "update", "args": {"range": 20}}
        }


class TestParseCommandMiner:
    """Tests para comandos del MinerBot."""

    def test_miner_set_strategy_vertical(self):
        """Verifica parseo de $miner set strategy vertical."""
        result = parse_command("$miner set strategy vertical")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"strategy": "vertical"}}
        }

    def test_miner_set_strategy_grid(self):
        """Verifica parseo de $miner set strategy grid."""
        result = parse_command("$miner set strategy grid")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"strategy": "grid"}}
        }

    def test_miner_set_strategy_grid_with_dimensions(self):
        """Verifica parseo de $miner set strategy grid 4 4."""
        result = parse_command("$miner set strategy grid 4 4")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {
                "cmd": "update",
                "args": {"strategy": "grid", "grid_width": 4, "grid_length": 4}
            }
        }

    def test_miner_set_strategy_vein(self):
        """Verifica parseo de $miner set strategy vein."""
        result = parse_command("$miner set strategy vein")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"strategy": "vein"}}
        }

    def test_miner_start_with_coords(self):
        """Verifica parseo de $miner start x=10 z=5 y=64."""
        result = parse_command("$miner start x=10 z=5 y=64")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"start": {"x": 10, "z": 5, "y": 64}}}
        }

    def test_miner_pause(self):
        """Verifica parseo de $miner pause."""
        result = parse_command("$miner pause")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "pause"}
        }

    def test_miner_resume(self):
        """Verifica parseo de $miner resume."""
        result = parse_command("$miner resume")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "resume"}
        }

    def test_miner_stop(self):
        """Verifica parseo de $miner stop."""
        result = parse_command("$miner stop")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "stop"}
        }

    def test_miner_status(self):
        """Verifica parseo de $miner status."""
        result = parse_command("$miner status")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "status"}
        }

    def test_miner_fulfill(self):
        """Verifica parseo de $miner fulfill."""
        result = parse_command("$miner fulfill")
        assert result == {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"mode": "fulfill"}}
        }


class TestParseCommandBuilder:
    """Tests para comandos del BuilderBot."""

    def test_builder_plan_list(self):
        """Verifica parseo de $builder plan list."""
        result = parse_command("$builder plan list")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"list": True}}
        }

    def test_builder_plan_set_refugio(self):
        """Verifica parseo de $builder plan set refugio."""
        result = parse_command("$builder plan set refugio")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"plan_set": "refugio"}}
        }

    def test_builder_plan_set_torre(self):
        """Verifica parseo de $builder plan set torre.csv."""
        result = parse_command("$builder plan set torre.csv")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"plan_set": "torre.csv"}}
        }

    def test_builder_bom(self):
        """Verifica parseo de $builder bom."""
        result = parse_command("$builder bom")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"bom": True}}
        }

    def test_builder_build(self):
        """Verifica parseo de $builder build."""
        result = parse_command("$builder build")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"build": True}}
        }

    def test_builder_pause(self):
        """Verifica parseo de $builder pause."""
        result = parse_command("$builder pause")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "pause"}
        }

    def test_builder_resume(self):
        """Verifica parseo de $builder resume."""
        result = parse_command("$builder resume")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "resume"}
        }

    def test_builder_stop(self):
        """Verifica parseo de $builder stop."""
        result = parse_command("$builder stop")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "stop"}
        }

    def test_builder_status(self):
        """Verifica parseo de $builder status."""
        result = parse_command("$builder status")
        assert result == {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "status"}
        }


class TestParseCommandEdgeCases:
    """Tests para casos límite y entradas inválidas."""

    def test_empty_string(self):
        """Verifica que una cadena vacía retorna dict vacío."""
        result = parse_command("")
        assert result == {}

    def test_whitespace_only(self):
        """Verifica que solo espacios retorna dict vacío."""
        result = parse_command("   ")
        assert result == {}

    def test_unknown_command(self):
        """Verifica que comandos desconocidos no causan error."""
        result = parse_command("$unknown command")
        # No debería fallar, simplemente no matchea ningún patrón
        assert isinstance(result, dict)

    def test_command_with_extra_whitespace(self):
        """Verifica que whitespace extra se maneja correctamente."""
        result = parse_command("  $agent stop  ")
        assert result == {
            "type": "control",
            "target": "ALL",
            "payload": {"cmd": "stop"}
        }

