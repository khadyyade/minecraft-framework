"""
MinerBot (Punto 4.2)

Requisitos del PDF:

    MinerBot manages the extraction and collection of materials required by BuilderBot. It
supports multiple mining strategies—at least two must be implemented:
    • Vertical Search: Drills downward through layers to extract resources at increasing
depths.
    • Grid Search: Explores a cubic region following a structured grid pattern for uni-
form coverage.
    • Vein Search: Detects clusters of identical materials (veins) and recursively mines
adjacent blocks to maximize yield.

    Upon receiving a Bill of Materials (BOM) from BuilderBot via materials.requirements.v1,
MinerBot validates its inventory and begins mining operations until the requirements are
fulfilled. Progress updates are periodically published through inventory.v1. Control
commands (pause, resume, stop) must be handled safely, maintaining context such as
position, collected materials, and current strategy.

Resumen de lo que tiene que hacer:
- Recibe los mesajes de tipo mensajes materials.requirements.v1 desde BuilderBot.
- Revisa el inventario y lleva a cabo una estrategia (Vertical, cubo o veta)
- Envia inventory.v1 indicando los recursos que tiene

"""

import asyncio
from multiprocessing import Queue
from typing import Dict, Any
import random

from minecraft_framework.baseAgent import BaseAgent, EstadoAgente
from minecraft_framework.messages import InventoryV1


class MinerBot(BaseAgent):
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, strategy: str = "vertical", mc=None):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        self.strategy = strategy
        self.inventory = {}
        self.current_bom = None
        self.mining_progress = 0.0
        self.mc = mc  # Minecraft connection (opcional)
        self.logs(f"MinerBot initialized with strategy={self.strategy}")

    # ============================================================================
    # PERCEIVE: Leer mensajes de la cola
    # ============================================================================
    async def perceive(self) -> Dict[str, Any]:
        """Lee mensajes de la cola y detecta BOM o comandos de control.
        
        Returns:
            Dict con:
                - messages: lista de mensajes recibidos
                - bom_received: BOM si se recibió materials.requirements.v1
                - control: comando de control si se recibió
        """
        perception = {
            "messages": [],
            "bom_received": None,
            "control": None
        }
        
        # Leer un mensaje de la cola
        msg = await self.leerMensaje()
        if msg:
            perception["messages"].append(msg)
            
            # Detectar tipo de mensaje
            if isinstance(msg, dict):
                msg_type = msg.get("type")
                
                if msg_type == "materials.requirements.v1":
                    payload = msg.get("payload", {})
                    bom = payload.get("bom", {})
                    perception["bom_received"] = bom
                    self.logs(f"📦 Received BOM: {bom}")
                    
                elif msg_type == "control":
                    control = msg.get("payload", {})
                    perception["control"] = control
                    self.logs(f"🎮 Received control: {control}")
                    
                else:
                    self.logs(f"❓ Unknown message type: {msg_type}")
        
        return perception

    # ============================================================================
    # DECIDE: Procesar percepción y decidir acción
    # ============================================================================
    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los mensajes y decide qué hacer.
        
        Args:
            perception: Datos de perceive()
            
        Returns:
            Dict con:
                - action: "mine", "wait", "handle_control"
                - bom: BOM a procesar (si action == "mine")
                - control: comando a procesar (si action == "handle_control")
        """
        decision = {
            "action": "wait",
            "bom": None,
            "control": None
        }
        
        # Prioridad 1: Comandos de control
        if perception["control"]:
            decision["action"] = "handle_control"
            decision["control"] = perception["control"]
            return decision
        
        # Prioridad 2: Nuevo BOM recibido
        if perception["bom_received"]:
            decision["action"] = "mine"
            decision["bom"] = perception["bom_received"]
            self.current_bom = perception["bom_received"]
            return decision
        
        # Prioridad 3: Continuar minería en progreso
        if self.current_bom and self.mining_progress < 1.0:
            decision["action"] = "mine"
            decision["bom"] = self.current_bom
            return decision
        
        # Sin tareas pendientes
        decision["action"] = "wait"
        return decision

    # ============================================================================
    # ACT: Ejecutar la acción decidida
    # ============================================================================
    async def act(self, decision: Dict[str, Any]):
        """Ejecuta la acción decidida.
        
        Args:
            decision: Datos de decide()
        """
        action = decision.get("action")
        
        if action == "handle_control":
            # Gestionar comando de control
            control = decision.get("control", {})
            self.gestionarControles(control)
            
        elif action == "mine":
            # Ejecutar minería
            bom = decision.get("bom", {})
            await self._mine_step(bom)
            
        elif action == "wait":
            # Esperar sin hacer nada
            await asyncio.sleep(0.3)
            
        else:
            self.logs(f"⚠️  Unknown action: {action}")
            await asyncio.sleep(0.1)

    # ============================================================================
    # HELPERS: Funciones auxiliares
    # ============================================================================
    async def _mine_step(self, bom: Dict[str, int]):
        """Ejecuta un paso de minería hacia el BOM objetivo.
        
        Args:
            bom: Bill of Materials (diccionario material -> cantidad)
        """
        if not bom:
            return
        
        total_items = sum(bom.values())
        collected_items = sum(self.inventory.values())
        
        # Simular recolección de materiales
        step = random.randint(1, 3)
        
        # Actualizar inventario de forma simplificada
        for material, target_count in bom.items():
            current = self.inventory.get(material, 0)
            if current < target_count:
                increment = min(step, target_count - current)
                self.inventory[material] = current + increment
                collected_items += increment
                self.logs(f"⛏️  Mined {increment} {material} (total: {self.inventory[material]}/{target_count})")
                break
        
        # Calcular progreso
        self.mining_progress = min(1.0, collected_items / total_items) if total_items > 0 else 1.0
        
        # Publicar actualización de inventario
        complete = self.mining_progress >= 1.0
        inv_msg = InventoryV1(inventory=self.inventory.copy(), complete=complete).to_message(origin=self.name)
        self.enviarMensaje("BuilderBot", inv_msg)
        self.logs(f"📊 Published inventory.v1 progress={self.mining_progress:.2f} complete={complete}")
        
        if complete:
            self.logs("✅ Mining completed!")
            self.current_bom = None
            self.mining_progress = 0.0
        
        await asyncio.sleep(0.5)

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
        bot.logs("KeyboardInterrupt in process")
