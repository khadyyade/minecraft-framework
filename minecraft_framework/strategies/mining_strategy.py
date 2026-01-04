from __future__ import annotations

from typing import Dict, Tuple, Optional, Any, Protocol


class MiningStrategy(Protocol):
    """Interfaz de estrategia de minado.

    Una estrategia decide qué bloque (x, y, z) se debe minar en el siguiente paso,
    basándose en:
      - state: diccionario con estado interno de la estrategia
      - missing: materiales que todavía faltan (requirements - inventory)

    Devuelve:
      - target: (x, y, z) o None si no hay target
      - new_state: estado actualizado
    """

    def next_target(
        self,
        state: Dict[str, Any],
        missing: Dict[str, int],
    ) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        ...

