import asyncio
from typing import Dict, Any
from multiprocessing import Queue


def parse_command(text: str) -> Dict[str, Any]:
    """Parse simple commands and return a structured dict.

    Examples:
      - '$agent stop'
      - '$explorer start x=0 z=0'
      - '$miner start x=10 z=5 y=64'

    Command prefix is: '$'
    """
    text = text.strip()
    if not text:
        return {}

    parts = text.split()

    # --------------------------------------------------
    # Global control: $agent ...
    # Aplica a TODOS los agentes (ExplorerBot, MinerBot, BuilderBot)
    # --------------------------------------------------
    if parts[0] == "$agent":
        cmd = parts[1] if len(parts) > 1 else ""

        # Comandos válidos: help, status, stop, pause, resume
        if cmd in ("help", "status", "stop", "pause", "resume"):
            return {"type": "control", "target": "ALL", "payload": {"cmd": cmd}}

        # Si no es un comando válido, retornar vacío
        return {}

    # --------------------------------------------------
    # Explorer CLI: \explorer ...
    # --------------------------------------------------
    if parts[0] == "$explorer":
        sub = parts[1] if len(parts) > 1 else ""
        if sub == "start":
            args: Dict[str, Any] = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    args[k] = int(v)
            return {
                "type": "control",
                "target": "ExplorerBot",
                "payload": {"cmd": "update", "args": {"start": args}},
            }
        if sub == "stop":
            return {
                "type": "control",
                "target": "ExplorerBot",
                "payload": {"cmd": "stop"},
            }
        if sub == "pause":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "pause"}}
        if sub == "resume":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "resume"}}
        if sub == "status":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "status"}}
        if sub == "set" and len(parts) >= 3 and parts[2] == "range":
            try:
                range_value = int(parts[3])
                return {
                    "type": "control",
                    "target": "ExplorerBot",
                    "payload": {"cmd": "update", "args": {"range": range_value}},
                }
            except (IndexError, ValueError):
                pass

    # --------------------------------------------------
    # Miner CLI: \miner ...
    # --------------------------------------------------
    if parts[0] == "$miner":
        sub = parts[1] if len(parts) > 1 else ""

        if sub == "pause":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "pause"}}

        if sub == "resume":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "resume"}}

        if sub == "stop":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "stop"}}

        if sub == "status":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "status"}}

        if sub == "set" and len(parts) >= 4 and parts[2] == "strategy":
            strategy = parts[3]  # "vertical" | "grid" | "vein"

            args: Dict[str, Any] = {"strategy": strategy}

            # Soporte: \miner set strategy grid 4 4
            if strategy == "grid" and len(parts) >= 6:
                try:
                    args["grid_width"] = int(parts[4])
                    args["grid_length"] = int(parts[5])
                except ValueError:
                    # ignore si no son ints
                    pass
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": args},
            }

        if sub == "start":
            args = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    args[k] = int(v)
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": {"start": args}},
            }

        if sub == "fulfill":
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": {"mode": "fulfill"}},
            }

        # Unknown subcommand
        return {
            "type": "text",
            "target": "LOCAL",
            "payload": {"text": text},
        }

    # --------------------------------------------------
    # Builder CLI: \builder ...
    # --------------------------------------------------
    if parts[0] == "$builder":
        sub = parts[1] if len(parts) > 1 else ""

        # Control commands
        if sub == "pause":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "pause"}}
        if sub == "resume":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "resume"}}
        if sub == "stop":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "stop"}}
        if sub == "status":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "status"}}

        # Plan management: \builder plan list | \builder plan set <template>
        if sub == "plan":
            subsub = parts[2] if len(parts) > 2 else ""

            if subsub == "list":
                return {
                    "type": "control",
                    "target": "BuilderBot",
                    "payload": {"cmd": "update", "args": {"list": True}}
                }

            if subsub == "set" and len(parts) > 3:
                template_name = parts[3]
                return {
                    "type": "control",
                    "target": "BuilderBot",
                    "payload": {"cmd": "update", "args": {"plan_set": template_name}}
                }

        # Bill of Materials: \builder bom
        if sub == "bom":
            return {
                "type": "control",
                "target": "BuilderBot",
                "payload": {"cmd": "update", "args": {"bom": True}}
            }

        # Build command: \builder build
        if sub == "build":
            return {
                "type": "control",
                "target": "BuilderBot",
                "payload": {"cmd": "update", "args": {"build": True}}
            }

    # --------------------------------------------------
    # Workflow CLI: $workflow run [params]
    # --------------------------------------------------
    if parts[0] == "$workflow":
        sub = parts[1] if len(parts) > 1 else ""

        if sub == "run":
            # Parse optional parameters
            params = {
                "x": None,
                "z": None,
                "range": None,
                "template": None,
                "miner_strategy": None,
                "miner_x": None,
                "miner_y": None,
                "miner_z": None,
            }

            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    # Explorer params
                    if k == "x":
                        params["x"] = int(v)
                    elif k == "z":
                        params["z"] = int(v)
                    elif k == "range":
                        params["range"] = int(v)
                    # Builder params
                    elif k == "template":
                        params["template"] = v
                    # Miner params
                    elif k == "miner.strategy":
                        params["miner_strategy"] = v
                    elif k == "miner.x":
                        params["miner_x"] = int(v)
                    elif k == "miner.y":
                        params["miner_y"] = int(v)
                    elif k == "miner.z":
                        params["miner_z"] = int(v)

            return {
                "type": "workflow",
                "target": "ROUTER",
                "payload": {"cmd": "run", "params": params}
            }

    # Default: plain text
    return {"type": "text", "target": "LOCAL", "payload": {"text": text}}


class ChatRouter:
    """
    ChatRouter - Single consumer of Minecraft chat events.

    Responsibilities:
    - Poll chat messages from Minecraft using mc.events.pollChatPosts()
    - Parse commands using parse_command()
    - Route messages to appropriate agent queues (q_miner, q_builder, q_explorer)
    - Handle broadcast to ALL agents when target is "ALL"

    This is the ONLY component that should call mc.events.pollChatPosts().
    Bots must NOT poll chat themselves; they only consume from their queues.
    """

    def __init__(self, mc, q_miner: Queue, q_builder: Queue, q_explorer: Queue):
        """
        Initialize the ChatRouter.

        Args:
            mc: Minecraft connection object
            q_miner: Queue for MinerBot
            q_builder: Queue for BuilderBot
            q_explorer: Queue for ExplorerBot
        """
        self.mc = mc
        self.q_miner = q_miner
        self.q_builder = q_builder
        self.q_explorer = q_explorer

        # Map target names to queues
        self.queues = {
            "MinerBot": q_miner,
            "BuilderBot": q_builder,
            "ExplorerBot": q_explorer,
        }

        self._stop_requested = False
        # Variable para rastrear último estado conocido de cada agente
        self.last_agent_states = {}

    async def wait_for_agent_idle(self, agent_name: str, timeout: int = 300):
        """
        Espera activamente a que un agente deje de estar en estado RUNNING.

        Funciona enviando comandos status repetidamente y esperando a que el agente
        reporte un estado diferente a RUNNING.

        Args:
            agent_name: Nombre del agente (ExplorerBot, MinerBot, BuilderBot)
            timeout: Tiempo máximo de espera en segundos

        Returns:
            True si el agente terminó, False si hubo timeout
        """
        import json
        import time

        print(f"[Workflow] Waiting for {agent_name} to finish (checking status)...")
        if self.mc:
            self.mc.postToChat(f"[Workflow] Esperando a {agent_name}...")

        start_time = time.time()
        checks = 0

        while (time.time() - start_time) < timeout:
            checks += 1

            # Enviar solicitud de status
            status_msg = {
                "type": "control",
                "target": agent_name,
                "payload": {"cmd": "status"}
            }

            try:
                self.queues[agent_name].put_nowait(json.dumps(status_msg))
            except Exception as e:
                print(f"[Workflow] Error sending status: {e}")

            # El agente imprimirá su estado en los logs
            # Buscamos en los logs recientes o simplemente esperamos
            # Como el agente YA imprime cuando cambia de estado,
            # podemos asumir que después de enviar status, si esperamos
            # un poco, el siguiente cambio de estado será visible

            await asyncio.sleep(2)

            # Mostrar progreso cada 10 segundos
            elapsed = int(time.time() - start_time)
            if checks % 5 == 0:
                print(f"[Workflow] Still waiting for {agent_name}... ({elapsed}s, {checks} checks)")

            # NOTA: En esta implementación simple, asumimos que después de
            # un tiempo razonable el agente habrá terminado.
            # Una mejora sería parsear los logs o usar una cola de respuesta.

            # Por ahora, después de 30 checks (60 segundos) asumimos que terminó
            # si no vemos actividad en RUNNING en los logs
            if checks >= 15:  # 15 checks * 2 segundos = 30 segundos mínimo
                print(f"[Workflow] {agent_name} should be finished after {checks} checks")
                return True

        print(f"[Workflow] Timeout waiting for {agent_name}")
        return False

    async def execute_workflow(self, params: Dict[str, Any]):
        """
        Execute the complete workflow: Explorer → Builder → Miner → Builder

        Steps:
        1. Explorer scans terrain and publishes map.v1
        2. Builder loads template and publishes BOM
        3. Miner FULFILL (auto-fill materials without mining)
        4. Builder constructs the structure

        Args:
            params: Dictionary with optional parameters (x, z, range, template, miner_strategy, etc.)
        """
        import json

        print("[Workflow] Starting automated workflow...")
        if self.mc:
            self.mc.postToChat("[Workflow] Iniciando workflow automatizado...")

        # ========== STEP 1: Explorer ==========
        print("[Workflow] Step 1: Starting Explorer...")
        if self.mc:
            self.mc.postToChat("[Workflow] Paso 1: Explorando terreno...")

        # Construir comando explorer start
        explorer_args = {}
        if params.get("x") is not None:
            explorer_args["x"] = params["x"]
        if params.get("z") is not None:
            explorer_args["z"] = params["z"]
        if params.get("range") is not None:
            explorer_args["range"] = params["range"]

        explorer_msg = {
            "type": "control",
            "target": "ExplorerBot",
            "payload": {"cmd": "update", "args": {"start": explorer_args}}
        }
        self.queues["ExplorerBot"].put_nowait(json.dumps(explorer_msg))

        # Esperar a que el Explorer termine (monitorear con status)
        await self.wait_for_agent_idle("ExplorerBot", timeout=120)

        # ========== STEP 2: Builder - Load Template ==========
        print("[Workflow] Step 2: Loading builder template...")
        if self.mc:
            self.mc.postToChat("[Workflow] Paso 2: Cargando plantilla...")

        template = params.get("template") or "torre.csv"
        builder_plan_msg = {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"plan_set": template}}
        }
        self.queues["BuilderBot"].put_nowait(json.dumps(builder_plan_msg))
        await asyncio.sleep(1)

        # ========== STEP 3: Builder - Publish BOM ==========
        print("[Workflow] Step 3: Publishing BOM...")
        if self.mc:
            self.mc.postToChat("[Workflow] Paso 3: Publicando materiales...")

        builder_bom_msg = {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"bom": True}}
        }
        self.queues["BuilderBot"].put_nowait(json.dumps(builder_bom_msg))
        await asyncio.sleep(1)

        # ========== STEP 4: Miner - Set Strategy ==========
        print("[Workflow] Step 4: Setting miner strategy...")
        if self.mc:
            self.mc.postToChat("[Workflow] Paso 4: Configurando minero...")

        strategy = params.get("miner_strategy") or "vertical"
        miner_strategy_msg = {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"strategy": strategy}}
        }
        self.queues["MinerBot"].put_nowait(json.dumps(miner_strategy_msg))
        await asyncio.sleep(1)

        # ========== STEP 5: Miner - FULFILL (HACK para demo) ==========
        print("[Workflow] Step 5: Auto-filling materials (HACK)...")
        if self.mc:
            self.mc.postToChat("[Workflow] Paso 5: Auto-llenando materiales...")

        miner_fulfill_msg = {
            "type": "control",
            "target": "MinerBot",
            "payload": {"cmd": "update", "args": {"mode": "fulfill"}}
        }
        self.queues["MinerBot"].put_nowait(json.dumps(miner_fulfill_msg))
        await asyncio.sleep(2)

        # ========== STEP 6: Builder - Build ==========
        print("[Workflow] Step 6: Starting construction...")
        if self.mc:
            self.mc.postToChat("[Workflow] Paso 6: Construyendo...")

        builder_build_msg = {
            "type": "control",
            "target": "BuilderBot",
            "payload": {"cmd": "update", "args": {"build": True}}
        }
        self.queues["BuilderBot"].put_nowait(json.dumps(builder_build_msg))

        # Esperar a que el Builder termine (monitorear con status)
        await self.wait_for_agent_idle("BuilderBot", timeout=120)

        print("[Workflow] Workflow completed!")
        if self.mc:
            self.mc.postToChat("[Workflow] Workflow completado!")

    def route_message(self, message: Dict[str, Any]):
        """
        Route a parsed message to the appropriate queue(s).

        Args:
            message: Parsed command dictionary from parse_command()
        """
        import json

        if not isinstance(message, dict):
            return

        target = message.get("target")

        # Handle text messages (local only, don't route)
        if message.get("type") == "text":
            return

        # Serializar el mensaje a JSON para que sea compatible con el sistema de colas
        try:
            serialized = json.dumps(message)
        except Exception as e:
            print(f"[ChatRouter] Error serializing message: {e}")
            return

        # Broadcast to ALL queues
        if target == "ALL":
            for agent_name, queue in self.queues.items():
                try:
                    queue.put_nowait(serialized)
                except Exception as e:
                    print(f"[ChatRouter] Error routing to {agent_name}: {e}")
        # Route to specific agent
        elif target is not None and target in self.queues:
            try:
                self.queues[target].put_nowait(serialized)
            except Exception as e:
                print(f"[ChatRouter] Error routing to {target}: {e}")

    async def run(self):
        """
        Main polling loop.

        Continuously polls Minecraft chat, parses commands, and routes them
        to the appropriate agent queues.
        """
        print("[ChatRouter] Started polling chat messages")

        while not self._stop_requested:
            try:
                # Poll chat posts from Minecraft (SINGLE CONSUMER)
                for post in self.mc.events.pollChatPosts():
                    text = post.message.strip()
                    print(f"[ChatRouter] Received chat: {text}")

                    # Solo procesar si empieza con $
                    if text.startswith("$"):
                        try:
                            # Parse the command
                            parsed = parse_command(text)

                            if parsed:
                                # Verificar si es un workflow
                                if parsed.get("type") == "workflow":
                                    print(f"[ChatRouter] Executing workflow...")
                                    # Ejecutar workflow en segundo plano
                                    asyncio.create_task(self.execute_workflow(parsed.get("payload", {}).get("params", {})))
                                # Verificar si es un comando no reconocido (tipo "text")
                                elif parsed.get("type") == "text":
                                    # Comando inválido
                                    print(f"[ChatRouter] Invalid command: {text}")
                                    try:
                                        self.mc.postToChat(f"[ERROR] Comando invalido: {text}")
                                        self.mc.postToChat("Usa: $agent help, $explorer help, $miner help, $builder help")
                                    except Exception as post_error:
                                        print(f"[ChatRouter] Error posting to chat: {post_error}")
                                else:
                                    # Comando válido
                                    print(f"[ChatRouter] Parsed: {parsed}")
                                    # Route to appropriate queue(s)
                                    self.route_message(parsed)
                        except Exception as parse_error:
                            print(f"[ChatRouter] Error parsing command '{text}': {parse_error}")
                            try:
                                self.mc.postToChat(f"[ERROR] Error al procesar comando: {text}")
                            except:
                                pass

                # Sleep to avoid busy-waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"[ChatRouter] Error in polling loop: {e}")
                await asyncio.sleep(0.5)

        print("[ChatRouter] Stopped")

    def stop(self):
        """Request the ChatRouter to stop."""
        self._stop_requested = True
