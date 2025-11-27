"""
Sistema de registro dinámico de agentes usando reflexión (reflection).

Este módulo escanea automáticamente el directorio agents/ y registra
todos los agentes válidos sin necesidad de imports manuales.

Uso:
    from minecraft_framework.registry import AgentRegistry
    
    # Registrar agentes automáticamente
    registry = AgentRegistry()
    registry.discover_agents()
    
    # Obtener un agente
    ExplorerBotClass = registry.get_agent("ExplorerBot")
"""

import os
import importlib
import inspect
from typing import Dict, Type, Optional
from pathlib import Path


class AgentRegistry:
    """Registro dinámico de agentes usando reflexión."""
    
    def __init__(self):
        self._agents: Dict[str, Type] = {}
        self._strategies: Dict[str, Type] = {}
    
    def discover_agents(self, agents_dir: Optional[str] = None):
        """Escanea el directorio agents/ y registra automáticamente todos los agentes.
        
        Args:
            agents_dir: Ruta al directorio de agentes. Si None, usa la carpeta por defecto.
        """
        if agents_dir is None:
            # Obtener la ruta del directorio agents/
            current_dir = Path(__file__).parent
            agents_dir = current_dir / "agents"
        else:
            agents_dir = Path(agents_dir)
        
        if not agents_dir.exists():
            print(f"Warning: Agents directory not found: {agents_dir}")
            return
        
        print(f"Scanning for agents in: {agents_dir}")
        
        # Escanear todos los archivos .py en agents/
        for file_path in agents_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue  # Ignorar __init__.py y otros archivos privados
            
            module_name = file_path.stem
            self._load_agent_module(module_name, agents_dir)
    
    def _load_agent_module(self, module_name: str, agents_dir: Path):
        """Carga un módulo de agente y registra las clases encontradas.
        
        Args:
            module_name: Nombre del módulo (ej: 'explorer', 'miner')
            agents_dir: Directorio donde está el módulo
        """
        try:
            # Importar el módulo dinámicamente
            module_path = f"minecraft_framework.agents.{module_name}"
            module = importlib.import_module(module_path)
            
            # Buscar todas las clases que hereden de BaseAgent
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Verificar si la clase está definida en este módulo (no importada)
                if obj.__module__ == module_path:
                    # Verificar si hereda de BaseAgent (sin importar BaseAgent para evitar ciclos)
                    if self._is_agent_class(obj):
                        self._agents[name] = obj
                        print(f"  ✓ Registered agent: {name} from {module_name}.py")
        
        except Exception as e:
            print(f"  ✗ Failed to load {module_name}.py: {e}")
    
    def _is_agent_class(self, cls) -> bool:
        """Verifica si una clase es un agente válido (hereda de BaseAgent).
        
        Args:
            cls: Clase a verificar
        
        Returns:
            True si es un agente válido
        """
        # Verificar que tenga los métodos requeridos
        required_methods = ['perceive', 'decide', 'act', 'iniciarAgente']
        for method in required_methods:
            if not hasattr(cls, method):
                return False
        return True
    
    def get_agent(self, agent_name: str) -> Optional[Type]:
        """Obtiene una clase de agente por su nombre.
        
        Args:
            agent_name: Nombre del agente (ej: 'ExplorerBot')
        
        Returns:
            Clase del agente o None si no existe
        """
        return self._agents.get(agent_name)
    
    def list_agents(self):
        """Lista todos los agentes registrados."""
        return list(self._agents.keys())
    
    def discover_strategies(self, strategies_dir: Optional[str] = None):
        """Escanea el directorio strategies/ y registra automáticamente estrategias.
        
        Args:
            strategies_dir: Ruta al directorio de estrategias
        """
        if strategies_dir is None:
            current_dir = Path(__file__).parent
            strategies_dir = current_dir / "strategies"
        else:
            strategies_dir = Path(strategies_dir)
        
        if not strategies_dir.exists():
            print(f"Info: Strategies directory not found: {strategies_dir}")
            return
        
        print(f"Scanning for strategies in: {strategies_dir}")
        
        # Escanear todos los archivos .py en strategies/
        for file_path in strategies_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            module_name = file_path.stem
            self._load_strategy_module(module_name)
    
    def _load_strategy_module(self, module_name: str):
        """Carga un módulo de estrategia y registra las clases encontradas."""
        try:
            module_path = f"minecraft_framework.strategies.{module_name}"
            module = importlib.import_module(module_path)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_path:
                    self._strategies[name] = obj
                    print(f"  ✓ Registered strategy: {name} from {module_name}.py")
        
        except Exception as e:
            print(f"  ✗ Failed to load strategy {module_name}.py: {e}")
    
    def get_strategy(self, strategy_name: str) -> Optional[Type]:
        """Obtiene una clase de estrategia por su nombre."""
        return self._strategies.get(strategy_name)
    
    def list_strategies(self):
        """Lista todas las estrategias registradas."""
        return list(self._strategies.keys())


# Instancia global del registro (singleton)
_global_registry = None

def get_registry() -> AgentRegistry:
    """Obtiene la instancia global del registro de agentes."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
        _global_registry.discover_agents()
        _global_registry.discover_strategies()
    return _global_registry
