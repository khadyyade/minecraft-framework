from __future__ import annotations

from typing import Dict, Tuple, Optional, Any


class GridMiningStrategy:
    """Estrategia de minado en rejilla (grid).

    Estado esperado:
      - origin_x, origin_z, origin_y
      - current_depth
      - max_depth
      - grid_width
      - grid_length
      - current_col
      - current_row
    """

    def next_target(
        self,
        state: Dict[str, Any],
        missing: Dict[str, int],
    ) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        new_state = dict(state)

        origin_x = new_state.get("origin_x")
        origin_z = new_state.get("origin_z")
        origin_y = new_state.get("origin_y")
        current_depth = new_state.get("current_depth", 0)
        max_depth = new_state.get("max_depth", 50)
        grid_width = new_state.get("grid_width", 3)
        grid_length = new_state.get("grid_length", 3)
        current_col = new_state.get("current_col", 0)
        current_row = new_state.get("current_row", 0)

        if origin_x is None or origin_z is None or origin_y is None:
            return None, new_state

        while True:
            if current_row >= grid_length:
                return None, new_state

            y = origin_y - current_depth

            if current_depth >= max_depth or y <= 0:
                current_depth = 0
                current_col += 1

                if current_col >= grid_width:
                    current_col = 0
                    current_row += 1

                new_state["current_depth"] = current_depth
                new_state["current_col"] = current_col
                new_state["current_row"] = current_row

                if current_row >= grid_length:
                    return None, new_state

                continue

            break

        x = origin_x + current_col
        z = origin_z + current_row
        target = (x, y, z)

        new_state["current_depth"] = current_depth + 1
        new_state["current_col"] = current_col
        new_state["current_row"] = current_row

        return target, new_state

