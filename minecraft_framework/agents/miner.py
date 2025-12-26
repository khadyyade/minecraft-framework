from multiprocessing import Queue
from typing import Dict, Any, Optional
from mcpi.minecraft import Minecraft
import mcpi.block as block
from minecraft_framework.baseAgent import BaseAgent, AgentState
from minecraft_framework.strategies.mining import MiningStrategy, VerticalMiningStrategy, GridMiningStrategy
from minecraft_framework.block_parser import block_to_material


class Miner(BaseAgent):

    def __init__(
        self,
        name: str,
        in_queue: Queue,
        q_explorer: Queue,
        q_miner: Queue,
        q_builder: Queue,
    ):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)

        # Requirements sent by the Builder
        self.requirements: Dict[str, int] = {}

        # Internal logical inventory
        self.inventory: Dict[str, int] = {}

        # Last control command
        self.last_control: str = ""

        # Connection to Minecraft
        self.mc = Minecraft.create()

        #  Strategy Pattern: available mining strategies
        self.strategies: Dict[str, MiningStrategy] = {
            "vertical": VerticalMiningStrategy(),
            "grid": GridMiningStrategy()
            # "vein": VeinMiningStrategy(),
        }
        # Current strategy object
        self.current_strategy: Optional[MiningStrategy]= None
        # Current strategy name (useful to decide how to fill strategy_state)
        self.current_strategy_name: Optional[str] = None

        # Internal state of the current strategy.
        self.strategy_state: Dict[str, Any] = {}

        #-----------------FLAGS------------------------
        self.start_executed: bool = False
        self.fulfill_executed: bool = False
        self.strategy_setted: bool = False
        self.no_target: bool = False
        self.sent_start_warning : bool = False
        self.sent_strategy_warning : bool = False


        # Safety limit for vertical drilling depth
        self.max_depth: int = 50

    # ======================================================================
    #                              PERCEIVE
    # ======================================================================
    async def perceive(self) -> Dict[str, Any]:
        """
        Perception phase.

        - Reads messages from the input queue (requirements, control).
        - Builds and returns a perception dictionary to be used by decide().

        Note: Chat polling is now handled by ChatRouter, not by individual bots.
        """

        # 1) Process all available messages in the multiprocessing queue
        await self._perceive_queue_messages()

        # 2) Build the perception object
        perception = self._build_perception()
        return perception

    async def _perceive_queue_messages(self) -> None:
        """
        Read and interpret all messages currently available in the input queue.

        This updates:
          - self.requirements  (functional messages from Builder)
          - self.last_control  (control commands)
          - agent state        (via gestionarControles)

        Messages now come from ChatRouter which routes parsed chat commands to this queue.
        """
        while True:
            msg = await self.leerMensaje()

            # No more messages in the queue
            if msg is None or msg == "":
                break

            if not isinstance(msg, dict):
                self.logs("Message not recognised (it is not a dictionary)")
                continue

            # Standard control message produced by cli.parse_command (via ChatRouter)
            # Expected shape: { 'type': 'control', 'target': 'MinerBot', 'payload': { 'cmd': '...' } }
            if msg.get("type") == "control":
                payload = msg.get("payload", {})
                if isinstance(payload, dict):
                    cmd = payload.get("cmd")

                    # Basic control commands: pause / resume / stop
                    if cmd in ("pause", "resume", "stop"):
                        self.gestionarControles(payload)
                        self.last_control = cmd
                        continue

                    # /miner status: send a summary in the Minecraft chat
                    if cmd == "status":
                        if self.mc:
                            self.mc.postToChat(
                                f"[Miner] state={self.state.name}, inventory={self.inventory}"
                            )
                        continue

                    # /miner set strategy, /miner start, /miner fulfill
                    if cmd == "update":
                        args = payload.get("args", {})

                        # /miner set strategy <name>
                        if "strategy" in args:
                            # Accept optional grid dimensions when provided
                            gw = args.get("grid_width")
                            gl = args.get("grid_length")
                            self.set_strategy(args["strategy"], gw, gl)

                        # /miner start x,z,y
                        if "start" in args:
                            coords = args["start"]
                            pos = None
                            try:
                                pos = self.mc.player.getTilePos()
                            except Exception:
                                pos = None

                            # If a coordinate is missing, we fallback to the player position.
                            x = coords.get("x", pos.x + 1 if pos is not None else 0)
                            z = coords.get("z", pos.z if pos is not None else 0)
                            y = coords.get("y", pos.y if pos is not None else 64)

                            # If a strategy has been selected, use update_strategy_state to merge
                            # the origin/column into the existing state without losing grid dims.
                            if self.current_strategy_name:
                                self.update_strategy_state(x, z, y)
                            else:
                                # No strategy selected yet: store origin keys so that a later
                                # /miner set strategy grid will keep them.
                                self.strategy_state.setdefault("origin_x", x)
                                self.strategy_state.setdefault("origin_z", z)
                                self.strategy_state.setdefault("origin_y", y)

                            self.start_executed = True
                            self.sent_start_warning = False
                            self.logs(
                                f"Start mining from command: origin_x={x}, "
                                f"origin_z={z}, origin_y={y}"
                            )

                        # Fulfill mode: /miner fulfill
                        if args.get("mode") == "fulfill":
                            try:
                                pos = self.mc.player.getTilePos()
                                # Ensure we are using the vertical strategy when fulfilling
                                self.current_strategy = self.strategies.get("vertical", self.current_strategy)
                                self.current_strategy_name = "vertical"

                                # Merge origin coordinates into the existing state instead of
                                # replacing it (preserve any other keys)
                                self.update_strategy_state(pos.x + 1, pos.z, pos.y)

                                # Mark that a strategy has been set (vertical) and fulfill requested
                                self.strategy_setted = True
                                self.fulfill_executed = True
                                self.sent_start_warning = False
                                self.logs("[Miner] fulfill mode activated from command")
                            except Exception:
                                self.logs("Could not activate fulfill mode (no player position)")

                    self.last_control = cmd
                else:
                    self.logs("Control message payload not a dict")
                continue

            # Backwards-compatible: direct control dict with 'cmd' at root
            if "cmd" in msg:
                self.gestionarControles(msg)
                self.last_control = msg.get("cmd", "")
                continue

            # Functional messages
            msg_type = msg.get("type")

            # Requirements coming from the Builder
            if msg_type == "materials.requirements.v1":
                payload = msg.get("payload", {})
                # Accept payloads where the BOM is wrapped into {'bom': {...}} or the payload is the dict
                if isinstance(payload, dict) and "bom" in payload:
                    bom = payload.get("bom", {})
                    if isinstance(bom, dict):
                        self.requirements = bom
                    else:
                        self.logs("materials.requirements.v1 payload.bom is not a dict")
                elif isinstance(payload, dict):
                    self.requirements = payload
                else:
                    self.logs("materials.requirements.v1 payload not understood")

                self.logs("Received a requirements message")
            else:
                self.logs(f"Received an unknown message type: {msg_type}")

    def _build_perception(self) -> Dict[str, Any]:
        """
        Build the perception dictionary passed to decide().
        """
        return {
            "requirements": self.requirements,
            "inventory": self.inventory,
            "lastControl": self.last_control,
        }

    # ======================================================================
    #  DECIDE
    # ======================================================================
    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        From the perception, select ONE high level action:
          - NO_OP
          - WAITING_FOR_REQUIREMENTS
          - REPORT_COMPLETED
          - MINE
        """
        requirements = perception.get("requirements")
        inventory = perception.get("inventory", {})
        last_control = perception.get("lastControl")

        decision: Dict[str, Any] = {}

        # 0) If mining has already been marked as impossible, avoid planning.
        if not self.can_mine():
            decision["type"] = "NO_OP"
            if not self.strategy_setted:
                decision["reason"] = "Strategy not defined (use \\miner set strategy <strategy>)"
            if not (self.start_executed or self.fulfill_executed):
                decision["reason"] = "Start mining from chat (use \\miner start x=<x> z=<z> y=<y> or use \\miner fulfill)"
            return decision

        # 1) If a pause or stop control has been received, do not plan anything.
        if last_control in ("pause", "stop"):
            decision = {
                "type": "NO_OP",
                "reason": f"control '{last_control}' received in this cycle",
            }
            return decision

        # 2) If we still have no requirements from the Builder, we wait.
        if not requirements:
            self.cambiarEstadoAgente(
                AgentState.WAITING, "No requirements received"
            )
            decision = {
                "type": "WAITING_FOR_REQUIREMENTS",
                "reason": "No materials to mine have been received yet",
            }
            return decision

        # 3) Compute which materials are still missing (requirements - inventory)
        missing: Dict[str, int] = {}
        for material, needed_quantity in requirements.items():
            current_quantity = inventory.get(material, 0)
            deficit = needed_quantity - current_quantity
            if deficit > 0:
                missing[material] = deficit

        # 4) If nothing is missing, we can report completion.
        if not missing:
            decision = {
                "type": "REPORT_COMPLETED",
                "reason": "All material requirements are satisfied",
            }
            return decision

        # 5) Otherwise, we plan to mine.
        decision = {
            "type": "MINE",
            "reason": "There are still missing materials",
            "missing": missing,
        }
        return decision

    # ======================================================================
    #  ACT
    # ======================================================================
    async def act(self, decision: Dict[str, Any]):
        """
        Action phase.

        Execute the decision produced by decide():
          - NO_OP :log reason and do nothing
          - WAITING_FOR_REQUIREMENTS :log and do nothing
          - REPORT_COMPLETED :notify the Builder
          - MINE: perform one mining step using the strategy
        """
        action_type = decision.get("type")

        # 1) NO_OP
        if action_type == "NO_OP":
            reason = decision.get("reason")

            if reason:
                if "Start mining from chat" in reason:
                    if self.sent_start_warning:
                        return
                    self.sent_start_warning = True
                if "Strategy not defined" in reason:
                    if self.sent_strategy_warning:
                        return
                    self.sent_strategy_warning = True
            self.logs(f"NO_OP in act(): {reason}")
            return

        # 2) WAITING_FOR_REQUIREMENTS
        if action_type == "WAITING_FOR_REQUIREMENTS":
            self.logs(
                "Waiting for requirements: no mining performed in this cycle."
            )
            return

        # 3) REPORT_COMPLETED
        if action_type == "REPORT_COMPLETED":
            reason = decision.get("reason", "")
            self.logs(f"REPORT_COMPLETED in act(): {reason}")

            # Notify the Builder that mining is done with current inventory
            msg = {
                "type": "miner.completed.v1",
                "source": self.name,
                "target": "BuilderBot",
                "payload": {
                    "inventory": self.inventory,
                    "requirements": self.requirements,
                },
                "status": "DONE",
            }
            self.enviarMensaje("BuilderBot", msg)
            return

        # 4) MINE
        if action_type == "MINE":
            missing = decision.get("missing", {})

            # Ask the strategy for the next target block to mine
            target, new_state = self.current_strategy.next_target(
                self.strategy_state,
                missing,
            )
            self.strategy_state = new_state

            # If the strategy returns None, there is nothing more to mine
            # according to that strategy (e.g., reached max depth).
            if target is None:
                self.logs(
                    "Strategy returned no target (None). "
                    "Stopping mining for now."
                )
                self.no_target = True
                return

            x, y, z = target

            # ------------------------------------------------------------------
            #  MINING
            # ------------------------------------------------------------------
            block_id = self.mc.getBlock(x, y, z)
            material_found = block_to_material(block_id)

            self.logs(
                f"Mining step at (x={x}, y={y}, z={z}): "
                f"block_id={block_id}, material_found={material_found}"
            )

            # Replace the mined block with air (simulate excavation)
            self.mc.setBlock(x, y, z, block.AIR.id)

            # If the block is not mapped to a logical material, we skip it.
            if material_found is None:
                self.logs(
                    "The mined block does not correspond to any useful material."
                )
                return

            # We only add the material to our inventory if it appears in 'missing'
            if material_found in missing:
                current_qty = self.inventory.get(material_found, 0)
                self.inventory[material_found] = current_qty + 1

                self.logs(
                    f"Collecting 1 '{material_found}'. "
                    f"Inventory[{material_found}] = {self.inventory[material_found]}"
                )

                # Notify the Builder with updated inventory
                msg = {
                    "type": "inventory.v1",
                    "source": self.name,
                    "target": "BuilderBot",
                    "payload": self.inventory,
                    "status": "RUNNING",
                }
                self.enviarMensaje("BuilderBot", msg)
            else:
                self.logs(
                    f"Ignoring material '{material_found}' "
                    f"because it is not in 'missing'."
                )

            return

    def can_mine (self) -> bool:
        return (self.start_executed or  self.fulfill_executed) and  self.strategy_setted and not self.no_target
    # ======================================================================
    #  UTILITIES
    # ======================================================================
    def set_strategy(self, name: str, grid_width: Optional[int] = None, grid_length: Optional[int] = None) -> bool:
        """
        Cambia la estrategia actual sin sobrescribir coordenadas ya existentes.
        Usa el helper para evitar duplicación.
        """
        name = name.lower()

        if name not in self.strategies:
            self.logs(f"Unknown strategy '{name}'. No changes made.")
            if self.mc:
                self.mc.postToChat(f"[Miner] Unknown strategy: {name}")
            return False

        # Set the strategy object and remember its name
        self.current_strategy = self.strategies[name]
        self.current_strategy_name = name

        # Centralized defaults
        self._ensure_strategy_state_defaults(name, grid_width, grid_length)

        self.strategy_setted = True
        self.sent_start_warning = False
        self.sent_strategy_warning = False

        self.logs(f"Strategy changed to '{name}' (keeping coordinates).")
        if self.mc:
            self.mc.postToChat(f"[Miner] Strategy set to {name}")
        return True


    def update_strategy_state(self, x: int, z: int, y: int, strategy_name: Optional[str] = None) -> None:
        """
        Merge de las coordenadas en strategy_state.

        - Si `strategy_name` o `self.current_strategy_name` existe, resetea current_depth
          y actualiza max_depth (inicio de la ejecución desde esa posición).
        - Si no hay estrategia seleccionada, guarda las coordenadas con setdefault para
          que un posterior `set_strategy` las conserve.
        """
        target_strategy = strategy_name or self.current_strategy_name

        if target_strategy is None:
            # No strategy yet: keep origin only if not present (compatible con comportamiento previo)
            self.strategy_state.setdefault("origin_x", x)
            self.strategy_state.setdefault("origin_z", z)
            self.strategy_state.setdefault("origin_y", y)
            return

        # Con estrategia: hacer merge y reset de depth
        self.strategy_state.update({
            "origin_x": x,
            "origin_z": z,
            "origin_y": y,
            "current_depth": 0,
            "max_depth": self.max_depth,
        })

        # Preserve / ensure grid dimensions if grid strategy
        if target_strategy == "grid":
            self.strategy_state.setdefault("grid_width", self.strategy_state.get("grid_width", 3))
            self.strategy_state.setdefault("grid_length", self.strategy_state.get("grid_length", 3))

    def _ensure_strategy_state_defaults(self, name: str, grid_width: Optional[int] = None,
                                        grid_length: Optional[int] = None) -> None:
        """
        Inicializa/defaults de strategy_state para la estrategia `name`.
        Centraliza la lógica de setear current_depth, max_depth, grid dims y keys de origen.
        """
        # Depth defaults (común)
        self.strategy_state.setdefault("current_depth", 0)
        self.strategy_state["current_depth"] = 0
        self.strategy_state["max_depth"] = self.max_depth

        # Origin keys (ambas estrategias usan origin_*)
        self.strategy_state.setdefault("origin_x", None)
        self.strategy_state.setdefault("origin_z", None)
        self.strategy_state.setdefault("origin_y", None)

        # Grid-specific defaults
        if name == "grid":
            if grid_width is not None:
                self.strategy_state["grid_width"] = grid_width
            else:
                self.strategy_state.setdefault("grid_width", 3)

            if grid_length is not None:
                self.strategy_state["grid_length"] = grid_length
            else:
                self.strategy_state.setdefault("grid_length", 3)

    def logs(self, param):
        self.estadoActual(str(param))

