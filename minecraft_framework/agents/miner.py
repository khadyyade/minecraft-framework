"""
MinerBot skeleton.

Soporta (esqueleto de) estrategias: vertical, grid, vein.

Responsabilidades:
- Recibir `materials.requirements.v1` desde BuilderBot.
- Validar inventario y ejecutar estrategias de minería (simuladas aquí).
- Publicar `inventory.v1` periódicamente con progreso o al finalizar.
- Manejar control messages (pause/resume/stop/update).
"""
import asyncio
from multiprocessing import Queue
from typing import Dict, Any
import random

from minecraft_framework.core import BaseAgent, AgentState
from minecraft_framework.messages import InventoryV1


class MinerBot(BaseAgent):
    def __init__(self, name: str, in_queue: Queue, out_queues: Dict[str, Queue], strategy: str = "vertical"):
        super().__init__(name, in_queue, out_queues)
        self.strategy = strategy
        self.inventory = {}
        self.current_task = None

    async def _run_task(self):
        self.log(f"Miner starting with strategy={self.strategy}")
        while not self._stop_requested:
            # revisar cola de entrada en cada iteración
            incoming = await self._check_incoming()
            if incoming:
                # Mensajes tipo control o materials.requirements.v1
                if isinstance(incoming, dict) and incoming.get("type") == "materials.requirements.v1":
                    payload = incoming.get("payload", {})
                    bom = payload.get("bom", {})
                    await self._fulfill_bom(bom)
                elif isinstance(incoming, dict) and incoming.get("type") == "control":
                    self.handle_control(incoming.get("payload", {}))
                else:
                    self.log(f"Miner received unknown message: {incoming}")

            await asyncio.sleep(0.5)

    async def _fulfill_bom(self, bom: Dict[str, int]):
        """Simula minería hasta completar el BOM.

        Publica `inventory.v1` con progress y al completar con complete=True.
        TODO: implementar estrategias reales.
        """
        self.log(f"Received BOM: {bom}. Starting mining using {self.strategy}")
        total_items = sum(bom.values()) if bom else 0
        collected = 0
        # simulación simple: cada iteración recogemos entre 1 y 3 unidades
        while collected < total_items and not self._stop_requested:
            if self.state == AgentState.PAUSED:
                await asyncio.sleep(0.5)
                continue

            step = random.randint(1, 3)
            collected += step
            # actualizar inventario de forma simplificada
            for name, count in bom.items():
                self.inventory[name] = min(count, self.inventory.get(name, 0) + step)
                break

            progress = min(1.0, collected / total_items) if total_items else 1.0
            inv_msg = InventoryV1(inventory=self.inventory.copy(), complete=(progress >= 1.0)).to_message(origin=self.name)
            self.send("BuilderBot", inv_msg)
            self.log(f"Published inventory.v1 progress={progress:.2f}")
            await asyncio.sleep(1)

        self.log("Miner finished BOM (simulated)")


def agent_process_main(in_queue: Queue, out_queues: Dict[str, Queue], **kwargs):
    bot = MinerBot("MinerBot", in_queue, out_queues, strategy=kwargs.get("strategy", "vertical"))
    try:
        import asyncio

        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.log("KeyboardInterrupt in process")
