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
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, strategy: str = "vertical", mc=None):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        self.strategy = strategy
        self.inventory = {}
        self.current_task = None
        self.mc = mc  # Minecraft connection (opcional)

    async def _run_task(self):
        # Bucle principal: espera BOM de BuilderBot y ejecuta minería hasta completar
        self.estadoActual(f"Miner starting with strategy={self.strategy}")
        while not self._stop_requested:
            # revisar cola de entrada en cada iteración
            incoming = await self.leerMensaje()
            if incoming:
                # Mensajes tipo control o materials.requirements.v1
                if isinstance(incoming, dict) and incoming.get("type") == "materials.requirements.v1":
                    payload = incoming.get("payload", {})
                    bom = payload.get("bom", {})
                    await self._fulfill_bom(bom)
                elif isinstance(incoming, dict) and incoming.get("type") == "control":
                    self.gestionarControles(incoming.get("payload", {}))
                else:
                    self.estadoActual(f"Miner received unknown message: {incoming}")

            await asyncio.sleep(0.5)

    async def _fulfill_bom(self, bom: Dict[str, int]):
        """Simula minería hasta completar el BOM.

        Publica `inventory.v1` con progress y al completar con complete=True.
        TODO: implementar estrategias reales.
        """
        # Recolecta materiales del BOM y publica actualizaciones de inventario
        self.estadoActual(f"Received BOM: {bom}. Starting mining using {self.strategy}")
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
            self.enviarMensaje("BuilderBot", inv_msg)
            self.estadoActual(f"Published inventory.v1 progress={progress:.2f}")
            await asyncio.sleep(1)

        self.estadoActual("Miner finished BOM (simulated)")


def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
    """Entry point para ejecutar en un proceso separado.

    Args:
        in_queue: Cola de entrada del agente
        q_explorer: Cola del ExplorerBot
        q_miner: Cola del MinerBot
        q_builder: Cola del BuilderBot
        **kwargs: Parámetros adicionales (mc_host, mc_port, strategy)
    """
    # Intentar conectar a Minecraft si se proporcionan credenciales
    mc = None
    mc_host = kwargs.get("mc_host")
    mc_port = kwargs.get("mc_port")
    
    if mc_host and mc_port:
        try:
            import sys
            import os
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            mcpi_path = os.path.join(base, "AdventuresInMinecraft-PC", "MyAdventures")
            if os.path.exists(mcpi_path):
                sys.path.insert(0, mcpi_path)
            from mcpi.minecraft import Minecraft
            mc = Minecraft.create(mc_host, mc_port)
            print(f"[MinerBot] Connected to Minecraft at {mc_host}:{mc_port}")
        except Exception as e:
            print(f"[MinerBot] Could not connect to Minecraft: {e}. Using simulation.")
    
    bot = MinerBot("MinerBot", in_queue, q_explorer, q_miner, q_builder, strategy=kwargs.get("strategy", "vertical"), mc=mc)
    try:
        import asyncio
        asyncio.run(bot.iniciarAgente())
    except KeyboardInterrupt:
        bot.estadoActual("KeyboardInterrupt in process")
