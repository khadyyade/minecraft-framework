# strategies/mining.py

from typing import Dict, Tuple, Optional, Any, Protocol


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
