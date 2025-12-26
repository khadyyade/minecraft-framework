# strategies/mining.py

from typing import Dict, Tuple, Optional, Any, Protocol
from collections import deque
from typing import Deque, Set, List


class MiningStrategy(Protocol):
    """
    Mining strategy interface

    A strategy decides which block (x, y, z) to mine in the
    next step, based on:
      - state: a dictionary with its internal state
      - missing: materials that are still missing (requirements - inventory)

    Returns:
      - target: tuple (x, y, z) or None if there is nothing left to mine
      - new_state: the updated state of the strategy
    """

    def next_target(
        self,
        state: Dict[str, Any],
        missing: Dict[str, int],
    ) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        ...


class VerticalMiningStrategy:
    """
     Vertical mining strategy.

    The expected state has the following keys:
      - "origin_x": column in X (origin for the vertical drill)
      - "origin_z": column in Z
      - "origin_y": initial height from which the bot will start descending
      - "current_depth": how many blocks we have already excavated
      - "max_depth": maximum depth allowed

    The strategy:
      - at each step, reduce y = origin_y - current_depth
      - if max_depth is exceeded or y <= 0, stop proposing targets (target = None)
      - otherwise, propose (origin_x, y, origin_z) and increase current_depth
    """

    def next_target(self, state: Dict[str, Any], missing: Dict[str, int],) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        # We copy the status to not modify the original.
        new_state = dict(state)

        # Extract expected parameters from the state (use origin_* naming)
        origin_x = new_state.get("origin_x")
        origin_z = new_state.get("origin_z")
        origin_y = new_state.get("origin_y")
        current_depth = new_state.get("current_depth", 0)
        max_depth = new_state.get("max_depth", 50)

        # If basic information is missing, the bot cannot mine.
        if origin_x is None or origin_z is None or origin_y is None:
            # target = None indicates “I don't know where to mine”
            return None, new_state

        # Calculate the current y-coordinate
        y = origin_y - current_depth

        # Check depth limits
        if current_depth >= max_depth or y <= 0:
            # We are not proposing any more targets: we have reached the limit.
            return None, new_state

        # Target building
        target = (origin_x, y, origin_z)

        # Update the depth for the next step
        new_state["current_depth"] = current_depth + 1

        return target, new_state

class GridMiningStrategy:
    def next_target(self, state: Dict[str, Any], missing: Dict[str, int],) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        # We copy the status to not modify the original.
        new_state = dict(state)

        # Extract expected parameters from the state
        origin_x = new_state.get("origin_x")
        origin_z = new_state.get("origin_z")
        origin_y = new_state.get("origin_y")
        current_depth = new_state.get("current_depth", 0)
        max_depth = new_state.get("max_depth", 50)
        grid_width = new_state.get("grid_width", 3)
        grid_length = new_state.get("grid_length", 3)
        current_col = new_state.get("current_col", 0)
        current_row = new_state.get("current_row", 0)

        # If basic information is missing, the bot cannot mine.
        if origin_x is None or origin_z is None or origin_y is None:
            return None, new_state

        # Iterate to find the next valid (col,row,depth) position or finish
        while True:
            # If all rows completed, finish
            if current_row >= grid_length:
                return None, new_state

            # Compute y for the current depth in this column
            y = origin_y - current_depth

            # If we exhausted depth for this column, move to next column/row
            if current_depth >= max_depth or y <= 0:
                # Finished this column excavation, so we move to the next column
                current_depth = 0
                current_col += 1

                # If the new column is out of limits, we move to the next row
                if current_col >= grid_width:
                    current_col = 0
                    current_row += 1

                # Update state with the new column and row before next iteration
                new_state["current_depth"] = current_depth
                new_state["current_col"] = current_col
                new_state["current_row"] = current_row

                # After moving, check termination and continue the loop
                if current_row >= grid_length:
                    return None, new_state

                # continue to evaluate the new column
                continue

            # Otherwise we have a valid (col,row,depth) for mining: break to build the target
            break

        # Target building
        x = origin_x + current_col
        z = origin_z + current_row
        target = (x, y, z)

        # Advance depth for the next call
        new_state["current_depth"] = current_depth + 1
        new_state["current_col"] = current_col
        new_state["current_row"] = current_row

        return target, new_state

class VeinMiningStrategy:
    """Vein mining strategy (búsqueda de vetas) basada en BFS.

    Variante recomendada para este framework:
    - La estrategia mantiene la BFS (frontier/visited) y decide el *siguiente target*.
    - El agente (Miner) sí puede hacer `mc.getBlock()` y, cuando detecta que el bloque
      minado es un material objetivo, puede calcular/filtrar vecinos y pasarlos a la
      estrategia a través del estado.

    Cómo pasar vecinos desde el agente:
      - state['discovered_neighbors'] = [(x,y,z), ...]
    La estrategia los consume y los añade a `frontier`.

    Esto evita que la estrategia suponga vecinos a ciegas y permite filtrar por:
    - rango de profundidad
    - bloque sólido/aire
    - o incluso por tipo de mena (si quieres)

    Campos de estado usados:
      - frontier: lista de candidatos BFS
      - visited: lista de visitados
      - discovered_neighbors: lista temporal aportada por el agente (se consume)
      - scan_cursor/scan_step: fallback scan
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
                if not isinstance(p, (list, tuple)) or len(p) != 3:
                    continue
                x, y, z = int(p[0]), int(p[1]), int(p[2])
                if not self._within_depth(origin_y, y, max_depth):
                    continue
                if (x, y, z) in visited:
                    continue
                frontier.append((x, y, z))

        # 2) Sacar siguiente target de la frontier
        while frontier:
            x, y, z = frontier.popleft()
            if (x, y, z) in visited:
                continue
            if not self._within_depth(origin_y, y, max_depth):
                continue
            visited.add((x, y, z))
            new_state["frontier"] = list(frontier)
            new_state["visited"] = list(visited)
            return (x, y, z), new_state

        # 3) Si no hay frontier, fallback scan
        seed = self._next_scan_seed(new_state, origin_x, origin_y, origin_z, max_depth)
        if seed is None:
            new_state["frontier"] = []
            new_state["visited"] = list(visited)
            return None, new_state

        sx, sy, sz = seed
        if (sx, sy, sz) not in visited:
            visited.add((sx, sy, sz))
            new_state["frontier"] = []
            new_state["visited"] = list(visited)
            return (sx, sy, sz), new_state

        new_state["frontier"] = []
        new_state["visited"] = list(visited)
        return None, new_state

    @staticmethod
    def _neighbors6(p: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        x, y, z = p
        return [
            (x + 1, y, z),
            (x - 1, y, z),
            (x, y + 1, z),
            (x, y - 1, z),
            (x, y, z + 1),
            (x, y, z - 1),
        ]

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
        """Escaneo simple alrededor del origen: espiral 2D con una pequeña bajada.

        Esto es un fallback para encontrar el primer bloque de una veta.
        """
        cursor = state.get("scan_cursor")
        if cursor is None:
            # arrancamos al lado del jugador
            state["scan_cursor"] = (ox, oy, oz)
            state["scan_step"] = 0
            return (ox, oy, oz)

        x, y, z = cursor
        step = int(state.get("scan_step", 0))

        # patrón simple: x+1, z+1, x-1, z-1, y-1 (repite)
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
