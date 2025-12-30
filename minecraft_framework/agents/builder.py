from minecraft_framework.baseAgent import BaseAgent, EstadoAgente
from minecraft_framework.block_parser import material_to_block
from mcpi.minecraft import Minecraft
import mcpi.block as block
from typing import Dict, Any, Optional
from multiprocessing import Queue
from collections import defaultdict
import asyncio
import csv
import os

class BuilerBot(BaseAgent):
    def __init__(
            self,
            name: str,
            in_queue: Queue,
            q_explorer: Queue,
            q_miner: Queue,
            q_builder: Queue,
    ):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)

        # Connection to Minecraft (se inicializa después)
        self.mc = None

        # Control state
        self.last_control: Optional[str] = None

        # Template and building state
        self.current_template: Optional[Dict[str, Any]] = None
        self.bom: Optional[Dict[str, int]] = None
        self.bom_published: bool = False

        # Materials and building flags
        self.available_materials: Optional[Dict[str, int]] = None
        self.pending_build: bool = False
        self.can_build: bool = False

        # Map information from ExplorerBot
        self.coordenadasInicioTerrenoPlano: Optional[Dict[str, int]] = None
        self.coordenadasFinalTerrenoPlano: Optional[Dict[str, int]] = None
        self.alturaPlanicie: Optional[int] = None
    # ======================================================================
    #                              PERCEIVE
    # ======================================================================

    async def perceive(self) -> Dict[str, Any]:
        """
        Perception phase.

        - Reads messages from the input queue (requirements, control).
        - Builds and returns a perception dictionary to be used by decide().

        """
        # 1) Process all available messages in the multiprocessing queue
        await self._perceive_queue_messages()

        # 2) Build the perception object
        perception = self._build_perception()
        return perception

    async def _perceive_queue_messages(self) -> None:
        while True:
            msg = await self.leerMensaje()

            # No more messages in the queue
            if msg is None or msg == "":
                break

            msg_type = msg.get("type")

            # Control message
            # Shape: { 'type': 'control', 'target': 'BuilderBot', 'payload': { 'cmd': '...' } }
            if msg_type == "control":
                payload = msg.get("payload", {})
                if isinstance(payload, dict):
                    cmd = payload.get("cmd")

                    # pause, resume or stop
                    if cmd in ("pause", "resume", "stop"):
                        self.gestionarControles(payload)
                        self.last_control = cmd
                        continue

                    # status: send a summary in the Minecraft chat
                    if cmd == "status":
                        status_msg = f"[Builder] state={self.estadoActual.name}, template={self.current_template['name'] if self.current_template else 'None'}, can_build={self.can_build}"
                        self.logs(f"STATUS: {status_msg}")
                        if self.mc:
                            self.mc.postToChat(status_msg)
                            if self.bom:
                                self.mc.postToChat(f"BOM: {self.bom}")
                            if self.coordenadasInicioTerrenoPlano:
                                self.mc.postToChat(f"Build coords: {self.coordenadasInicioTerrenoPlano}, y={self.alturaPlanicie}")
                        continue

                    if cmd == "update":
                        args = payload.get("args", {})

                        if "list" in args:
                            # plan list
                            await self._list_templates()
                            continue

                        if "bom" in args:
                            #bom
                            await self._publish_bom()
                            continue

                        if "build" in args:
                            self.pending_build = True
                            self.logs(f"BUILD command received. Has materials: {self.available_materials is not None}, Has map: {self.coordenadasInicioTerrenoPlano is not None}")

                            # Verificar si ya tenemos materiales disponibles
                            if self.available_materials is not None and self.check_materials_available():
                                self.can_build = True
                                if self.mc:
                                    self.mc.postToChat("Materiales disponibles. Iniciando construcción...")
                                # Cambiar a RUNNING
                                self.gestionarControles(payload)
                            else:
                                if self.mc:
                                    self.mc.postToChat("Construcción solicitada. Esperando materiales...")
                            continue

                        if "plan_set" in args:
                            template_name = args["plan_set"]
                            await self.set_template(template_name)
                            continue

            if msg_type == "materials.inventory.v1":  # Cambio aquí
                payload = msg.get("payload", {})
                self.available_materials = payload

                self.logs(f"Inventory recibido del Miner: {payload}")

                if self.pending_build and self.check_materials_available():
                    self.can_build = True
                    if self.mc:
                        self.mc.postToChat("Materiales recibidos. Iniciando construcción...")
                    # Cambiar a RUNNING para empezar a construir
                    self.gestionarControles({'cmd': 'update', 'args': {}})
                else:
                    if self.pending_build:
                        self.logs(f"Materiales insuficientes. Necesito: {self.bom}, Tengo: {payload}")
                continue

            if msg_type == "map.v1":
                # El Explorer envía los datos en 'data', no en 'payload'
                data = msg.get("data", {})
                if not data:
                    # Fallback por si acaso usa 'payload'
                    data = msg.get("payload", {})

                altura = data.get("alturaPlanicie")

                # Validar que la altura sea válida
                if altura is None or altura < 0:
                    self.logs(f"MAP received but invalid height: {altura}. Ignoring.")
                    if self.mc:
                        self.mc.postToChat("[Builder] Mapa inválido recibido (altura < 0). Explorer debe buscar mejor terreno.")
                    continue

                self.coordenadasInicioTerrenoPlano = data.get("coordenadasInicioTerrenoPlano")
                self.coordenadasFinalTerrenoPlano = data.get("coordenadasFinalTerrenoPlano")
                self.alturaPlanicie = altura

                self.logs(f"MAP received: start={self.coordenadasInicioTerrenoPlano}, height={self.alturaPlanicie}")

                if self.mc:
                    self.mc.postToChat(f"[Builder] Mapa recibido del Explorer. Planicie en y={self.alturaPlanicie}")

                # Si estábamos esperando el mapa, cambiar a IDLE
                if self.estadoActual == EstadoAgente.WAITING:
                    self.cambiarEstadoAgente(EstadoAgente.IDLE, razon="Mapa recibido del Explorer")

                continue

    def _build_perception(self) -> Dict[str, Any]:
        """
        Build the perception dictionary passed to decide().
        """
        return {
            "has_template": self.current_template is not None,
            "bom_published": self.bom_published,
            "has_materials": self.can_build,
            "pending_build": self.pending_build,
            "has_map": self.coordenadasInicioTerrenoPlano is not None,
            "control_state": self.last_control,
        }

    async def _list_templates(self) -> None:
        """Posts the available templates in /templates folder"""

        templates_dir = "minecraft_framework/templates"

        if not os.path.exists(templates_dir):
            if self.mc:
                self.mc.postToChat("No hay templates disponibles")
            return

        template_files = [f for f in os.listdir(templates_dir) if os.path.isfile(os.path.join(templates_dir, f))]

        if not template_files:
            if self.mc:
                self.mc.postToChat("No hay templates disponibles")
            return

        # Postear lista en el chat
        if self.mc:
            self.mc.postToChat("Templates disponibles:")
            for template in template_files:
                self.mc.postToChat(f"- {template}")

    async def set_template(self, template_name: str) -> None:
        template_path = os.path.join("minecraft_framework/templates", template_name)

        if not os.path.exists(template_path):
            self.logs(f"Template '{template_name}' not found at {template_path}")
            if self.mc:
                self.mc.postToChat(f"Template '{template_name}' no encontrado")
            return

        try:
            # Parsear el CSV
            blocks = []
            with open(template_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    blocks.append({
                        'layer': int(row['layer']),
                        'x': int(row['x']),
                        'z': int(row['z']),
                        'block_type': row['block_type']
                    })

            self.current_template = {
                'name': template_name,
                'blocks': blocks
            }

            # Calcular BOM
            self._calculate_bom()

            self.logs(f"Template '{template_name}' loaded. Total blocks: {len(blocks)}, BOM: {self.bom}")

            if self.mc:
                self.mc.postToChat(f"Template '{template_name}' cargado. Total bloques: {len(blocks)}")

        except Exception as e:
            self.logs(f"Error loading template: {e}")
            if self.mc:
                self.mc.postToChat(f"Error al cargar template: {str(e)}")

    def _calculate_bom(self) -> None:
        """Calcula el Bill of Materials del template actual."""
        if self.current_template is None:
            return

        bom = defaultdict(int)
        for block in self.current_template['blocks']:
            bom[block['block_type']] += 1

        self.bom = dict(bom)

    async def _publish_bom(self) -> None:
        """Publica el BOM en la cola de salida."""
        if self.bom is None:
            self.logs("Cannot publish BOM: no template selected")
            if self.mc:
                self.mc.postToChat("No hay template seleccionado")
            return

        bom_msg = {
            "type": "materials.requirements.v1",
            "origin": self.name,
            "timestamp": 0,
            "payload": self.bom
        }

        self.enviarMensaje("MinerBot", bom_msg)
        self.bom_published = True

        self.logs(f"BOM published to MinerBot: {self.bom}")

        if self.mc:
            self.mc.postToChat("Bill Of Materials:")
            for block_type, count in self.bom.items():
                self.mc.postToChat(f"  {block_type}: {count}")

    def check_materials_available(self) -> bool:
        """Verifica si hay suficientes materiales disponibles."""
        if self.bom is None or self.available_materials is None:
            return False

        for block_type, required in self.bom.items():
            available = self.available_materials.get(block_type, 0)
            if available < required:
                if self.mc:
                    self.mc.postToChat(f"Faltan materiales: {block_type} ({available}/{required})")
                return False

        return True

    def _get_block_id(self, material_name: str) -> int:
        """Convierte un nombre de material a block_id.

        Args:
            material_name: Nombre del material (ej: "stone", "planks", "gold_block")

        Returns:
            Block ID correspondiente, o STONE.id si no se encuentra
        """
        block_id = material_to_block(material_name)

        if block_id is not None:
            return block_id

        # Si no se encuentra, loguear error y usar piedra por defecto
        if self.mc:
            self.mc.postToChat(f"ADVERTENCIA: Bloque '{material_name}' no encontrado, usando piedra")

        return block.STONE.id

    # ======================================================================
    #  DECIDE
    # ======================================================================
    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        From the perception, select ONE high level action:
          - NO_OP
          - SEND_BOM
          - WAITING_FOR_MATERIALS
          - BUILD_COMPLETED
          - BUILD
        """
        if self.last_control == "pause":
            return {"action": "NO_OP"}

        if self.can_build and self.current_template is not None:
            return {"action": "BUILD"}

        # Si hay template seleccionado pero no hemos publicado BOM
        if self.current_template is not None and not self.bom_published:
            return {"action": "SEND_BOM"}

        # Si esperamos materiales
        if self.pending_build and not self.can_build:
            return {"action": "WAITING_FOR_MATERIALS"}

        # Esperar más mensajes
        return {"action": "NO_OP"}

    # ======================================================================
    #  ACT
    # ======================================================================

    async def act(self, decision: Dict[str, Any]):
        """
        Execute the decided action.
        """
        action = decision.get("action", "NO_OP")
        reason = decision.get("reason", "")

        if action == "SEND_BOM":
            await self._publish_bom()

        elif action == "BUILD":
            await self._build_structure()

        elif action == "WAITING_FOR_MATERIALS":
            # Cambiar a WAITING si no estamos ya en ese estado
            if self.estadoActual != EstadoAgente.WAITING:
                self.logs(f"Waiting for materials: {reason}")
                if self.mc:
                    self.mc.postToChat("[Builder] Esperando materiales del Miner...")
                self.cambiarEstadoAgente(EstadoAgente.WAITING, razon=reason)

        elif action == "WAITING_FOR_MAP":
            # Cambiar a WAITING si falta el mapa del explorer
            if self.estadoActual != EstadoAgente.WAITING:
                self.logs(f"Waiting for map: {reason}")
                if self.mc:
                    self.mc.postToChat("[Builder] Esperando mapa del Explorer...")
                    self.mc.postToChat("[Builder] Usa: $explorer start x=X z=Z range=R")
                self.cambiarEstadoAgente(EstadoAgente.WAITING, razon=reason)

        elif action == "NO_OP":
            # Do nothing
            pass

    async def _build_structure(self) -> None:
        """Construye la estructura capa por capa."""
        if self.current_template is None or self.mc is None:
            self.logs("Cannot build: no template or no minecraft connection")
            return

        # Verificar que tenemos coordenadas del Explorer
        if self.coordenadasInicioTerrenoPlano is None or self.alturaPlanicie is None:
            self.logs("Cannot build: no map data from explorer")
            if self.mc:
                self.mc.postToChat("[Builder] ❌ No hay información del terreno.")
                self.mc.postToChat("[Builder] Usa: $explorer start x=X z=Z range=R")
            # Cambiar a WAITING
            self.cambiarEstadoAgente(EstadoAgente.WAITING, razon="Sin coordenadas de construcción")
            return

        # Usar coordenadas del explorer
        start_x = self.coordenadasInicioTerrenoPlano['x']
        start_z = self.coordenadasInicioTerrenoPlano['z']
        start_y = self.alturaPlanicie
        self.logs(f"Using map coordinates from Explorer: ({start_x}, {start_y}, {start_z})")

        self.logs(f"Starting construction at ({start_x}, {start_y}, {start_z})")

        if self.mc:
            self.mc.postToChat(f"[Builder] Iniciando construcción en ({start_x}, {start_y}, {start_z})")

        # Ordenar bloques por capa
        blocks = sorted(self.current_template['blocks'], key=lambda b: b['layer'])

        current_layer = -1
        for block in blocks:
            # Anunciar nueva capa
            if block['layer'] != current_layer:
                current_layer = block['layer']
                if self.mc:
                    self.mc.postToChat(f"Construyendo capa {current_layer}...")
                await asyncio.sleep(0.3)  # Pausa al cambiar de capa

            # Colocar bloque
            abs_x = start_x + block['x']
            abs_y = start_y + block['layer']
            abs_z = start_z + block['z']

            # Obtener el block_id del material y colocar el bloque
            block_type_name = block['block_type']
            block_id = self._get_block_id(block_type_name)
            self.mc.setBlock(abs_x, abs_y, abs_z, block_id)

            # Delay para ver el proceso de construcción
            await asyncio.sleep(0.1)

        # Construcción completada
        self.can_build = False
        self.pending_build = False
        self.bom_published = False
        self.current_template = None
        self.available_materials = None

        if self.mc:
            self.mc.postToChat("Construcción completada!")

        # Cambiar a IDLE esperando nuevo plan
        self.cambiarEstadoAgente(EstadoAgente.IDLE, razon="Construcción completada, esperando nuevo plan")

    # ============================================================================
    # ENTRY POINT: Función de proceso
    # ============================================================================

    @staticmethod
    def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
        """Función de entrada que recibe todos los parametros para lanzar el proceso por separado"""

        mc = None
        mc_host = kwargs.get("mc_host", "localhost")
        mc_port = kwargs.get("mc_port", 4711)

        try:
            from mcpi.minecraft import Minecraft
            mc = Minecraft.create(mc_host, mc_port)
            print(f"El BuilderBot se ha conseguido conectar al mundo {mc_host}:{mc_port}")
        except Exception as e:
            print(f"El BuilderBot NO se ha conseguido conectar: {e}")
            mc = None

        # Crear instancia del builder
        bot = BuilerBot(
            "BuilderBot",
            in_queue,
            q_explorer,
            q_miner,
            q_builder
        )

        # Si se pudo conectar, actualizar la instancia mc
        if mc:
            bot.mc = mc

        # Iniciar el agente (usa el ciclo perceive-decide-act de BaseAgent)
        try:
            import asyncio
            asyncio.run(bot.iniciarAgente())
        except KeyboardInterrupt:
            bot.logs("KeyboardInterrupt in process")
