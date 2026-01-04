from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Optional, Set, Tuple


class VeinMiningStrategy:
    """Estrategia de búsqueda de vetas (vein search) con BFS.

    Contrato:
    - El agente (Miner) tiene acceso al mundo (`mc.getBlock`). Cuando detecta un bloque
      objetivo, calcula vecinos candidatos y los aporta mediante:
        state['discovered_neighbors'] = [(x,y,z), ...]
    - La estrategia consume `discovered_neighbors`, los mete en `frontier` y devuelve
      targets BFS.

    Estado esperado:
      - origin_x, origin_y, origin_z
      - max_depth

    Estado interno:
      - frontier: lista de posiciones pendientes (serializable)
      - visited: lista de posiciones visitadas (serializable)
      - scan_cursor/scan_step: fallback scan cuando no hay frontier
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
        max_depth = new_state.get("max_depth", 50)

        if origin_x is None or origin_z is None or origin_y is None:
            return None, new_state

        frontier_list = new_state.get("frontier") or []
        visited_list = new_state.get("visited") or []

        def _to_pos(p: Any) -> Optional[Tuple[int, int, int]]:
            if not isinstance(p, (list, tuple)) or len(p) != 3:
                return None
            try:
                return int(p[0]), int(p[1]), int(p[2])
            except Exception:
                return None

        frontier: Deque[Tuple[int, int, int]] = deque(
            pos for pos in (_to_pos(p) for p in frontier_list) if pos is not None
        )
        visited: Set[Tuple[int, int, int]] = set(
            pos for pos in (_to_pos(p) for p in visited_list) if pos is not None
        )

        # 1) Consumir vecinos descubiertos por el agente
        discovered = new_state.pop("discovered_neighbors", None)
        if isinstance(discovered, list):
            for p in discovered:
                pos = _to_pos(p)
                if pos is None:
                    continue
                x, y, z = pos
                if not self._within_depth(origin_y, y, max_depth):
                    continue
                if pos in visited:
                    continue
                frontier.append(pos)

        # 2) Sacar siguiente target de la frontier
        while frontier:
            pos = frontier.popleft()
            if pos in visited:
                continue
            x, y, z = pos
            if not self._within_depth(origin_y, y, max_depth):
                continue
            visited.add(pos)
            new_state["frontier"] = list(frontier)
            new_state["visited"] = list(visited)
            return pos, new_state

        # 3) Fallback scan
        seed = self._next_scan_seed(new_state, origin_x, origin_y, origin_z, max_depth)
        if seed is None:
            new_state["frontier"] = []
            new_state["visited"] = list(visited)
            return None, new_state

        if seed not in visited:
            visited.add(seed)
            new_state["frontier"] = []
            new_state["visited"] = list(visited)
            return seed, new_state

        new_state["frontier"] = []
        new_state["visited"] = list(visited)
        return None, new_state

    @staticmethod
    def _within_depth(origin_y: int, y: int, max_depth: int) -> bool:
        return y > 0 and (origin_y - y) <= max_depth

    @staticmethod
    def _next_scan_seed(
        state: Dict[str, Any],
        ox: int,
        oy: int,
        oz: int,
        max_depth: int,
    ) -> Optional[Tuple[int, int, int]]:
        cursor = state.get("scan_cursor")
        if cursor is None:
            state["scan_cursor"] = (ox, oy, oz)
            state["scan_step"] = 0
            return (ox, oy, oz)

        x, y, z = cursor
        step = int(state.get("scan_step", 0))

        moves = [
            (1, 0, 0),
            (0, 0, 1),
            (-1, 0, 0),
            (0, 0, -1),
            (0, -1, 0),
        ]
        dx, dy, dz = moves[step % len(moves)]
        nx, ny, nz = x + dx, y + dy, z + dz

        if ny <= 0 or (oy - ny) > max_depth:
            return None

        state["scan_cursor"] = (nx, ny, nz)
        state["scan_step"] = step + 1
        return (nx, ny, nz)
