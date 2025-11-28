"""
Todos los agentes tienen que tener un formato estandar de JSON (Punto 3)

Hay diferentes tipos de mensajes (Punto 5)

- map.v1                        (ExplorerBot → BuilderBot)
- materials.requirements.v1     (BuilderBot → MinerBot)
- inventory.v1                  (MinerBot → BuilderBot)
- build.v1                      (BuilderBot → All)

Cada mensaje es un diccionario. 
Esta clase la hemos creado para simplificar la creación y validación de estos mensajes

"""


from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import time


def now_ts():
    return time.time()


def wrap_message(msg_type: str, payload: Dict[str, Any], origin: str = "") -> Dict[str, Any]:
    """Crea un mensaje estandarizado."""
    return {
        "type": msg_type,
        "origin": origin,
        "timestamp": now_ts(),
        "payload": payload,
    }


@dataclass
class MapV1:
    """Estructura básica de `map.v1`.

    payload ejemplo:
    {
        'origin': 'ExplorerBot',
        'area': {'x': 0, 'z': 0, 'range': 10},
        'heights': [[...], ...],
        'flat_zones': [ {'x':..,'z':..,'w':..,'d':..}, ... ],
    }
    """
    area: Dict[str, int]
    heights: List[List[int]]
    flat_zones: List[Dict[str, int]]

    def to_message(self, origin: str = "ExplorerBot") -> Dict[str, Any]:
        return wrap_message("map.v1", asdict(self), origin=origin)


@dataclass
class MaterialsRequirementsV1:
    bom: Dict[str, int]  # {'stone': 50, 'wood': 20}

    def to_message(self, origin: str = "BuilderBot") -> Dict[str, Any]:
        return wrap_message("materials.requirements.v1", asdict(self), origin=origin)


@dataclass
class InventoryV1:
    inventory: Dict[str, int]
    complete: bool = False

    def to_message(self, origin: str = "MinerBot") -> Dict[str, Any]:
        return wrap_message("inventory.v1", asdict(self), origin=origin)


@dataclass
class BuildV1:
    progress: float  # 0.0 - 1.0
    details: Dict[str, Any]

    def to_message(self, origin: str = "BuilderBot") -> Dict[str, Any]:
        return wrap_message("build.v1", asdict(self), origin=origin)
