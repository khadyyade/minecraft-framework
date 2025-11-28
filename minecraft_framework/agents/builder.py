"""
BuilderBot (Punto 4.3)

Requisitos del PDF:

    BuilderBot constructs structures using the materials supplied by MinerBot and the terrain
data produced by ExplorerBot. It analyzes terrain maps, generates a Bill of Materials
(BOM), and publishes it as a materials.requirements.v1 message. If resources are
insufficient, it suspends activity until materials become available.
    When construction begins, BuilderBot places blocks layer by layer while logging co-
ordinates, timestamps, and material types. It supports the same control commands for
pausing, resuming, or stopping construction safely. If a building plan changes, BuilderBot
recalculates the BOM and republishes updated requirements, ensuring synchronization
across dependent agents.

Resumen de lo que tiene que hacer:
- Recibir mensaje map.v1 de ExplorerBot y generar un plan de construcción con la lista de materiales que necesitará (BOM)
- Envia los materials.requirements.v1 a MinerBot
- Recibe inventory.v1 y, cuando haya materiales suficientes, construye y va enviando build.v1 explicando el progreso

"""

import asyncio
from multiprocessing import Queue
from typing import Dict, Any

from minecraft_framework.baseAgent import BaseAgent, EstadoAgente
from minecraft_framework.messages import MaterialsRequirementsV1, BuildV1


class BuilderBot(BaseAgent):
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, mc=None):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        self.current_plan = None
        self.bom = {}
        self.inventory = {}
        self.building_in_progress = False
        self.build_progress = 0.0
        self.mc = mc  # Minecraft connection (opcional)
        self.logs("BuilderBot initialized")

    # ============================================================================
    # PERCEIVE: Leer mensajes de la cola
    # ============================================================================
    async def perceive(self) -> Dict[str, Any]:
        """Lee mensajes de la cola y detecta mapas, inventario o comandos.
        
        Returns:
            Dict con:
                - messages: lista de mensajes recibidos
                - map_received: datos del mapa si se recibió map.v1
                - inventory_update: inventario si se recibió inventory.v1
                - control: comando de control si se recibió
        """
        perception = {
            "messages": [],
            "map_received": None,
            "inventory_update": None,
            "control": None
        }
        
        # Leer un mensaje de la cola
        msg = await self.leerMensaje()
        if msg:
            perception["messages"].append(msg)
            
            # Detectar tipo de mensaje
            if isinstance(msg, dict):
                msg_type = msg.get("type")
                
                if msg_type == "map.v1":
                    payload = msg.get("payload", {})
                    perception["map_received"] = payload
                    self.logs(f"🗺️  Received map.v1")
                    
                elif msg_type == "inventory.v1":
                    payload = msg.get("payload", {})
                    perception["inventory_update"] = payload
                    self.logs(f"📦 Received inventory.v1: {payload.get('inventory', {})}")
                    
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
                - action: "generate_plan", "update_inventory", "build", "handle_control", "wait"
                - map_data: datos del mapa (si action == "generate_plan")
                - inventory: inventario (si action == "update_inventory" o "build")
                - control: comando (si action == "handle_control")
        """
        decision = {
            "action": "wait",
            "map_data": None,
            "inventory": None,
            "control": None
        }
        
        # Prioridad 1: Comandos de control
        if perception["control"]:
            decision["action"] = "handle_control"
            decision["control"] = perception["control"]
            return decision
        
        # Prioridad 2: Nuevo mapa recibido -> generar plan y BOM
        if perception["map_received"]:
            decision["action"] = "generate_plan"
            decision["map_data"] = perception["map_received"]
            return decision
        
        # Prioridad 3: Actualización de inventario -> verificar si podemos construir
        if perception["inventory_update"]:
            decision["action"] = "update_inventory"
            decision["inventory"] = perception["inventory_update"]
            return decision
        
        # Prioridad 4: Continuar construcción en progreso
        if self.building_in_progress:
            decision["action"] = "build"
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
            
        elif action == "generate_plan":
            # Generar plan de construcción y BOM
            map_data = decision.get("map_data", {})
            await self._generate_plan_and_bom(map_data)
            
        elif action == "update_inventory":
            # Actualizar inventario y verificar si podemos construir
            inventory_data = decision.get("inventory", {})
            await self._update_inventory(inventory_data)
            
        elif action == "build":
            # Ejecutar paso de construcción
            await self._build_step()
            
        elif action == "wait":
            # Esperar sin hacer nada
            await asyncio.sleep(0.3)
            
        else:
            self.logs(f"⚠️  Unknown action: {action}")
            await asyncio.sleep(0.1)

    # ============================================================================
    # HELPERS: Funciones auxiliares
    # ============================================================================
    async def _generate_plan_and_bom(self, map_data: Dict[str, Any]):
        """Genera plan de construcción y BOM a partir del mapa.
        
        Args:
            map_data: Datos del mapa de ExplorerBot
        """
        self.logs("🏗️  Generating plan and BOM from map data...")
        
        # TODO: analizar heights y flat_zones para generar plan
        # Plan simple de ejemplo: construir 10x10 de stone
        self.current_plan = {"template": "simple_square", "params": {"w": 10, "d": 10}}
        self.bom = {"stone": 100}
        
        # Publicar BOM a MinerBot
        msg = MaterialsRequirementsV1(bom=self.bom).to_message(origin=self.name)
        self.enviarMensaje("MinerBot", msg)
        self.logs(f"📤 Published materials.requirements.v1 with BOM: {self.bom}")

    async def _update_inventory(self, inventory_data: Dict[str, Any]):
        """Actualiza el inventario y verifica si podemos empezar a construir.
        
        Args:
            inventory_data: Datos de inventory.v1
        """
        inv = inventory_data.get("inventory", {})
        complete = inventory_data.get("complete", False)
        
        self.inventory.update(inv)
        self.logs(f"📊 Inventory updated: {self.inventory}; complete={complete}")
        
        # Verificar si tenemos suficientes materiales para construir
        if all(self.inventory.get(k, 0) >= v for k, v in self.bom.items()):
            if not self.building_in_progress:
                self.logs("✅ Sufficient materials available. Starting build...")
                self.building_in_progress = True
                self.build_progress = 0.0

    async def _build_step(self):
        """Ejecuta un paso de construcción."""
        if not self.building_in_progress:
            return
        
        total_steps = 10
        current_step = int(self.build_progress * total_steps)
        
        if current_step >= total_steps:
            self.logs("🎉 Build completed!")
            self.building_in_progress = False
            if self.mc is not None:
                self.mc.postToChat("BuilderBot: Construcción completada!")
            return
        
        # Obtener posición base (jugador + offset)
        base_x, base_y, base_z = 0, 64, 0
        if self.mc is not None:
            try:
                pos = self.mc.player.getTilePos()
                base_x, base_y, base_z = pos.x + 5, pos.y, pos.z
            except Exception as e:
                self.logs(f"⚠️  Error getting player position: {e}")
        
        # Colocar bloque
        if self.mc is not None:
            try:
                import sys
                import os
                base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                mcpi_path = os.path.join(base, "AdventuresInMinecraft-PC", "MyAdventures")
                if mcpi_path not in sys.path:
                    sys.path.insert(0, mcpi_path)
                import mcpi.block as block
                self.mc.setBlock(base_x + current_step, base_y, base_z, block.STONE.id)
                self.logs(f"🧱 Placed block at ({base_x + current_step}, {base_y}, {base_z})")
            except Exception as e:
                self.logs(f"⚠️  Error placing block: {e}")
        
        # Actualizar progreso
        current_step += 1
        self.build_progress = current_step / total_steps
        
        # Publicar progreso
        details = {"step": current_step, "total": total_steps, "pos": (base_x + current_step - 1, base_y, base_z)}
        msg = BuildV1(progress=self.build_progress, details=details).to_message(origin=self.name)
        
        # Broadcast a todos los agentes
        for target in self.out_queues.keys():
            self.enviarMensaje(target, msg)
        
        self.logs(f"📊 Build progress: {self.build_progress:.2f}")
        await asyncio.sleep(0.8)

def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
    """Entry point para ejecutar en un proceso separado.

    Args:
        in_queue: Cola de entrada del agente
        q_explorer: Cola del ExplorerBot
        q_miner: Cola del MinerBot
        q_builder: Cola del BuilderBot
        **kwargs: Parámetros adicionales (mc_host, mc_port)
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
            print(f"[BuilderBot] Connected to Minecraft at {mc_host}:{mc_port}")
        except Exception as e:
            print(f"[BuilderBot] Could not connect to Minecraft: {e}. Using simulation.")
    
    bot = BuilderBot("BuilderBot", in_queue, q_explorer, q_miner, q_builder, mc=mc)
    try:
        import asyncio
        asyncio.run(bot.iniciarAgente())
    except KeyboardInterrupt:
        bot.logs("KeyboardInterrupt in process")
