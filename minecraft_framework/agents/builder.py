import importlib
from mcpi.minecraft import Minecraft
import mcpi.block as block
from typing import Dict, Any, Optional
from multiprocessing import Queue
from collections import defaultdict
import asyncio
import csv
import os

# Cargar clases del framework con reflection
baseAgent_module = importlib.import_module('minecraft_framework.baseAgent')
BaseAgent = getattr(baseAgent_module, 'BaseAgent')
EstadoAgente = getattr(baseAgent_module, 'EstadoAgente')

block_parser_module = importlib.import_module('minecraft_framework.block_parser')
material_to_block = getattr(block_parser_module, 'material_to_block')

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

                    # help: mostrar comandos disponibles
                    if cmd == "help":
                        help_msg = "[BuilderBot] Comandos: $builder plan list, $builder plan set <template>, $builder bom, $builder build, $builder pause, $builder resume, $builder status, $builder stop"
                        self.logs(f"HELP: {help_msg}")
                        if self.mc:
                            self.mc.postToChat(help_msg)
                        continue

                    # status: enviar resumen al chat de Minecraft
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

                        # Comando: $builder plan list
                        if "list" in args:
                            await self._list_templates()
                            continue

                        # Comando: $builder bom
                        if "bom" in args:
                            await self._publish_bom()
                            continue

                        # Comando: $builder build
                        if "build" in args:
                            self.pending_build = True
                            self.logs(f"BUILD command received. Has materials: {self.available_materials is not None}, Has map: {self.coordenadasInicioTerrenoPlano is not None}")

                            # Verificar si tenemos TODO lo necesario para construir
                            tiene_materiales = self.available_materials is not None and self.check_materials_available()
                            tiene_mapa = self.coordenadasInicioTerrenoPlano is not None

                            if tiene_materiales and tiene_mapa:
                                # Todo listo para construir
                                self.can_build = True
                                if self.mc:
                                    self.mc.postToChat("[Builder] Materiales y mapa disponibles. Iniciando construcción...")
                                self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="materiales y mapa disponibles para construir")
                            elif not tiene_materiales and not tiene_mapa:
                                # Falta todo
                                if self.mc:
                                    self.mc.postToChat("[Builder] Faltan materiales Y mapa del Explorer")
                                    self.mc.postToChat("[Builder] 1) Usa $builder bom para solicitar materiales")
                                    self.mc.postToChat("[Builder] 2) Usa $explorer start para obtener mapa")
                            elif not tiene_materiales:
                                # Solo falta materiales
                                if self.mc:
                                    self.mc.postToChat("[Builder] Esperando materiales del Miner...")
                            elif not tiene_mapa:
                                # Solo falta mapa
                                if self.mc:
                                    self.mc.postToChat("[Builder] Falta mapa del Explorer")
                                    self.mc.postToChat("[Builder] Usa $explorer start para escanear terreno")
                            continue

                        # Comando: $builder plan set <template>
                        if "plan_set" in args:
                            template_name = args["plan_set"]
                            await self.set_template(template_name)
                            # Resetear flags cuando se carga un nuevo template
                            self.bom_published = False
                            self.pending_build = False
                            self.can_build = False
                            continue

            if msg_type == "materials.inventory.v1":
                payload = msg.get("payload", {})
                self.available_materials = payload

                self.logs(f"Inventory recibido del Miner: {payload}")

                # Verificar si tenemos materiales suficientes
                materiales_completos = self.check_materials_available()

                if materiales_completos:
                    # Tenemos materiales suficientes
                    if self.pending_build:
                        # Si ya estábamos esperando construir, cambiar a RUNNING
                        self.can_build = True
                        if self.mc:
                            self.mc.postToChat("[Builder] Materiales recibidos. Usa $builder build para construir.")
                        self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="materiales recibidos del miner")
                    else:
                        # Si NO estábamos esperando, solo notificar que los materiales están disponibles
                        if self.mc:
                            self.mc.postToChat("[Builder] Materiales disponibles. Usa $builder build para construir.")
                else:
                    # No tenemos suficientes materiales
                    if self.pending_build:
                        self.logs(f"Materiales insuficientes. Necesito: {self.bom}, Tengo: {payload}")
                        if self.mc:
                            self.mc.postToChat("[Builder] Materiales insuficientes aún. Esperando...")
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
        """Carga un template CSV y calcula su Bill of Materials."""
        template_path = os.path.join("minecraft_framework/templates", template_name)

        if not os.path.exists(template_path):
            self.logs(f"Template '{template_name}' not found at {template_path}")
            if self.mc:
                self.mc.postToChat(f"[Builder] Template '{template_name}' no encontrado")
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
                self.mc.postToChat(f"[Builder] Template '{template_name}' cargado ({len(blocks)} bloques)")

        except Exception as e:
            self.logs(f"Error loading template: {e}")
            if self.mc:
                self.mc.postToChat(f"[Builder] Error al cargar template: {str(e)}")

    def _calculate_bom(self) -> None:
        """Calcula el Bill of Materials del template actual."""
        if self.current_template is None:
            return

        bom = defaultdict(int)
        for block in self.current_template['blocks']:
            bom[block['block_type']] += 1

        self.bom = dict(bom)

    async def _publish_bom(self) -> None:
        """Publica el BOM (Bill of Materials) al MinerBot."""
        if self.bom is None:
            self.logs("Cannot publish BOM: no template selected")
            if self.mc:
                self.mc.postToChat("[Builder] No hay template seleccionado")
            return

        # Evitar publicar el mismo BOM múltiples veces
        if self.bom_published:
            self.logs("BOM already published, skipping")
            if self.mc:
                self.mc.postToChat("[Builder] BOM ya fue publicado anteriormente")
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
            self.mc.postToChat("[Builder] Bill Of Materials enviado al Miner:")
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
        Decide la acción a tomar basándose en la percepción.

        Acciones posibles:
          - NO_OP: No hacer nada
          - BUILD: Construir la estructura
          - WAITING_FOR_MATERIALS: Esperar materiales del miner
          - WAITING_FOR_MAP: Esperar mapa del explorer
        """
        # Si estamos pausados, no hacer nada
        if self.last_control == "pause":
            return {"action": "NO_OP"}

        # Si tenemos todo listo para construir
        if self.can_build and self.current_template is not None:
            return {"action": "BUILD"}

        # Si estamos esperando materiales
        if self.pending_build and not self.can_build:
            return {"action": "WAITING_FOR_MATERIALS"}

        # Por defecto, esperar más mensajes
        return {"action": "NO_OP"}

    # ======================================================================
    #  ACT
    # ======================================================================

    async def act(self, decision: Dict[str, Any]):
        """
        Ejecuta la acción decidida.
        """
        action = decision.get("action", "NO_OP")
        reason = decision.get("reason", "")

        if action == "BUILD":
            await self._build_structure()

        elif action == "WAITING_FOR_MATERIALS":
            # Cambiar a WAITING si no estamos ya en ese estado
            if self.estadoActual != EstadoAgente.WAITING:
                self.logs(f"Waiting for materials: {reason}")
                if self.mc:
                    self.mc.postToChat("[Builder] Esperando materiales del Miner...")
                self.cambiarEstadoAgente(EstadoAgente.WAITING, razon="esperando materiales del miner")

        elif action == "WAITING_FOR_MAP":
            # Cambiar a WAITING si falta el mapa del explorer
            if self.estadoActual != EstadoAgente.WAITING:
                self.logs(f"Waiting for map: {reason}")
                if self.mc:
                    self.mc.postToChat("[Builder] Esperando mapa del Explorer...")
                    self.mc.postToChat("[Builder] Usa: $explorer start x=X z=Z range=R")
                self.cambiarEstadoAgente(EstadoAgente.WAITING, razon="esperando mapa del explorer")

        elif action == "NO_OP":
            # No hacer nada
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
                self.mc.postToChat("[Builder] ERROR: No hay informacion del terreno.")
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
        # NO borrar template ni available_materials para permitir reconstruir
        # self.current_template = None  # ← Mantener el template
        # self.available_materials = None  # ← Mantener los materiales disponibles
        # Pero sí resetear bom_published para que se pueda solicitar BOM de nuevo si se carga otro template
        # self.bom_published = False  # ← Mantener para evitar duplicar BOM

        if self.mc:
            self.mc.postToChat("[Builder] Construcción completada!")
            self.mc.postToChat("[Builder] Puedes reconstruir con $builder build")

        # Cambiar a IDLE esperando nuevo comando
        self.cambiarEstadoAgente(EstadoAgente.IDLE, razon="Construcción completada, esperando nuevo comando")

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
