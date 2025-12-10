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
      - “column_x”: column in X
      - “column_z”: column in Z
      - “start_y”: initial height from which the bot will start descending
      - “current_depth”: how many blocks we have already excavated
      - “max_depth”: maximum depth allowed

    The strategy:
      - at each step, reduce y = start_y - current_depth
      - if max_depth is exceeded or y <= 0, stop proposing targets (target = None)
      - otherwise, propose (column_x, y, column_z) and increase current_depth
    """

    def next_target(self, state: Dict[str, Any], missing: Dict[str, int],) -> Tuple[Optional[Tuple[int, int, int]], Dict[str, Any]]:
        # We copy the status to not  modify the original.
        new_state = dict(state)

        # Extract expected parameters from the state
        column_x = new_state.get("column_x")
        column_z = new_state.get("column_z")
        start_y = new_state.get("start_y")
        current_depth = new_state.get("current_depth", 0)
        max_depth = new_state.get("max_depth", 50)

        # If basic information is missing, th bot cannot mine.
        if column_x is None or column_z is None or start_y is None:
            # target = None indicates “I don't know where to mine”
            return None, new_state

        # Calculate the current y-coordinate
        y = start_y - current_depth

        # Check depth limits
        if current_depth >= max_depth or y <= 0:
            # We are not proposing any more targets: we have reached the limit.
            return None, new_state

        # Target building
        target = (column_x, y, column_z)

        # Update the depth for the next step
        new_state["current_depth"] = current_depth + 1

        return target, new_state
