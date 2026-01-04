from __future__ import annotations

from typing import Dict, Tuple, Optional, Any


class VerticalMiningStrategy:
    """Estrategia de minado vertical.

    Estado esperado:
      - origin_x, origin_z, origin_y
      - current_depth
      - max_depth
    """

    def next_target(
        self,
        state: Dict[str, Any],
        missing: Dict[str, int],
    ) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        """
        Estrategia de minado vertical simple.

        Cava una columna vertical desde origin_y hacia abajo hasta max_depth.
        Cuando termina la columna, retorna None.

        El AGENTE (en decide) es responsable de:
        - Detectar cuando retorna None
        - Decidir si cambiar de posición
        - Actualizar origin_x/origin_z para nueva columna
        """
        new_state = dict(state)

        origin_x = new_state.get("origin_x")
        origin_z = new_state.get("origin_z")
        origin_y = new_state.get("origin_y")
        current_depth = new_state.get("current_depth", 0)
        max_depth = new_state.get("max_depth", 50)

        if origin_x is None or origin_z is None or origin_y is None:
            return None, new_state

        y = origin_y - current_depth

        # Si alcanzamos max_depth o llegamos a y=0, terminar columna
        if current_depth >= max_depth or y <= 0:
            return None, new_state

        target = (origin_x, y, origin_z)
        new_state["current_depth"] = current_depth + 1

        return target, new_state

