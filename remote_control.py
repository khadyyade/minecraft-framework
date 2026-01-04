# Control remoto para los agentes usando Pyro4
# Esto es opcional - solo si quieres controlar desde otra máquina
# Instalación: pip install Pyro4

import Pyro4
from multiprocessing import Queue
import json


@Pyro4.expose  # Esto hace que Pyro4 pueda acceder a los métodos remotamente
class RemoteAgentController:
    # Esta clase es el controlador que corre en el servidor
    # Los clientes se conectan y llaman a estos métodos para enviar comandos

    def __init__(self, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
        # Guardamos las referencias a las colas de los agentes
        # Así podemos meterles mensajes desde aquí
        self.queues = {
            "ExplorerBot": q_explorer,
            "MinerBot": q_miner,
            "BuilderBot": q_builder,
            "ALL": [q_explorer, q_miner, q_builder]
        }
        print("[RemoteControl] Controlador inicializado")

    def send_command(self, agent_name: str, command: str, args: dict = None):
        # Método genérico para enviar comandos a los agentes
        # Construye el mensaje JSON y lo mete en la cola correspondiente
        if args is None:
            args = {}

        try:
            # Armamos el mensaje en el formato que espera el sistema
            message = {
                "type": "control",
                "target": agent_name,
                "payload": {
                    # Los comandos como pause/stop van directos, los demás van como update
                    "cmd": command if command in ["pause", "resume", "stop", "status"] else "update",
                    "args": args if command not in ["pause", "resume", "stop", "status"] else {}
                }
            }

            # Si es ALL mandamos a todos, si no solo al que toque
            if agent_name == "ALL":
                for queue in self.queues["ALL"]:
                    queue.put_nowait(json.dumps(message))
                return {"success": True, "message": f"Comando '{command}' enviado a todos los agentes"}
            elif agent_name in self.queues:
                self.queues[agent_name].put_nowait(json.dumps(message))
                return {"success": True, "message": f"Comando '{command}' enviado a {agent_name}"}
            else:
                return {"success": False, "message": f"Agente '{agent_name}' no encontrado"}

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def explorer_start(self, x: int = None, z: int = None, range_scan: int = 6):
        # Inicia la exploración
        # Si no pasas coordenadas usa la posición del jugador
        args = {"start": {}}
        if x is not None:
            args["start"]["x"] = x
        if z is not None:
            args["start"]["z"] = z
        if range_scan:
            args["start"]["range"] = range_scan

        return self.send_command("ExplorerBot", "start", args)

    def miner_start(self, x: int = None, z: int = None, y: int = None, strategy: str = "vertical"):
        # Inicia el minado
        # Primero configura la estrategia y luego manda el start

        # Configurar estrategia
        result1 = self.send_command("MinerBot", "set_strategy", {"strategy": strategy})

        # Iniciar minado
        args = {"start": {}}
        if x is not None:
            args["start"]["x"] = x
        if z is not None:
            args["start"]["z"] = z
        if y is not None:
            args["start"]["y"] = y

        result2 = self.send_command("MinerBot", "start", args)

        return {"success": result1["success"] and result2["success"],
                "message": f"{result1['message']} | {result2['message']}"}

    def miner_fulfill(self):
        # Auto-llena el inventario (es un hack para demos, no mina de verdad)
        return self.send_command("MinerBot", "fulfill", {"mode": "fulfill"})

    def builder_plan(self, template: str = "torre.csv"):
        # Carga un template de construcción
        return self.send_command("BuilderBot", "plan", {"plan_set": template})

    def builder_bom(self):
        # Publica la lista de materiales al Miner
        return self.send_command("BuilderBot", "bom", {"bom": True})

    def builder_build(self):
        # Empieza a construir
        return self.send_command("BuilderBot", "build", {"build": True})

    def pause_agent(self, agent_name: str = "ALL"):
        # Pausa un agente o todos
        return self.send_command(agent_name, "pause")

    def resume_agent(self, agent_name: str = "ALL"):
        # Reanuda un agente o todos
        return self.send_command(agent_name, "resume")

    def stop_agent(self, agent_name: str = "ALL"):
        # Detiene un agente o todos (mata el proceso)
        return self.send_command(agent_name, "stop")

    def status(self, agent_name: str = "ALL"):
        # Pide el estado de los agentes (se muestra en el chat de Minecraft)
        return self.send_command(agent_name, "status")

    def workflow_run(self, x: int = None, z: int = None, range_scan: int = 6,
                    template: str = "torre.csv", strategy: str = "vertical"):
        # Ejecuta el workflow completo: explorar → planificar → minar → construir
        # Es básicamente mandar todos los comandos en secuencia
        try:
            # Mandamos todos los comandos en orden
            result1 = self.explorer_start(x, z, range_scan)
            result2 = self.builder_plan(template)
            result3 = self.builder_bom()
            result4 = self.send_command("MinerBot", "strategy", {"strategy": strategy})
            result5 = self.miner_fulfill()
            result6 = self.builder_build()

            return {
                "success": True,
                "message": "Workflow iniciado. Los agentes ejecutarán las tareas automáticamente."
            }
        except Exception as e:
            return {"success": False, "message": f"Error en workflow: {str(e)}"}


def start_remote_server(q_explorer: Queue, q_miner: Queue, q_builder: Queue,
                       host: str = "0.0.0.0", port: int = 9090):
    # Inicia el servidor Pyro4 para control remoto
    # host="0.0.0.0" significa que acepta conexiones de cualquier interfaz de red
    try:
        # Crear el daemon de Pyro y registrar el controlador
        daemon = Pyro4.Daemon(host=host, port=port)
        controller = RemoteAgentController(q_explorer, q_miner, q_builder)
        uri = daemon.register(controller, "minecraft.agents.controller")

        print("=" * 60)
        print("SERVIDOR DE CONTROL REMOTO INICIADO")
        print("=" * 60)
        print(f"URI: {uri}")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print("")
        print("Los clientes pueden conectarse usando:")
        print(f"  import Pyro4")
        print(f"  controller = Pyro4.Proxy('PYRO:minecraft.agents.controller@{host}:{port}')")
        print("=" * 60)

        # Loop infinito esperando peticiones
        daemon.requestLoop()

    except Exception as e:
        print(f"[RemoteControl] Error al iniciar servidor: {e}")


if __name__ == "__main__":
    print("Este módulo debe importarse desde main.py")
    print("No ejecutar directamente.")

