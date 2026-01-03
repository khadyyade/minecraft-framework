# Cliente para controlar los agentes de Minecraft desde otra máquina
# Se conecta al servidor remoto y manda comandos
# Uso: python remote_client.py

import Pyro4


class RemoteClient:
    # Cliente que se conecta al servidor de control remoto

    def __init__(self, server_host: str = "localhost", server_port: int = 9090):
        # Intenta conectarse al servidor Pyro4
        # server_host: IP del servidor (donde corre Minecraft)
        # server_port: Puerto del servidor (por defecto 9090)
        try:
            uri = f"PYRO:minecraft.agents.controller@{server_host}:{server_port}"
            self.controller = Pyro4.Proxy(uri)

            # Probar la conexión
            self.controller._pyroBind()
            print(f"✓ Conectado al servidor {server_host}:{server_port}")

        except Exception as e:
            print(f"✗ Error al conectar al servidor: {e}")
            print(f"  Asegúrate de que el servidor está ejecutándose en {server_host}:{server_port}")
            self.controller = None

    def is_connected(self):
        # Verifica si la conexión está activa
        return self.controller is not None

    def send_command(self, agent_name: str, command: str, args: dict = None):
        # Envía un comando genérico a un agente
        if not self.is_connected():
            return {"success": False, "message": "No conectado al servidor"}

        try:
            result = self.controller.send_command(agent_name, command, args)
            return result
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    # Métodos para cada agente - básicamente wrappers sobre send_command

    def explorer_start(self, x=None, z=None, range_scan=6):
        # Manda al explorer a explorar
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.explorer_start(x, z, range_scan)

    def miner_start(self, x=None, z=None, y=None, strategy="vertical"):
        # Arranca el minero
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.miner_start(x, z, y, strategy)

    def miner_fulfill(self):
        # Llena el inventario automáticamente (para testing rápido)
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.miner_fulfill()

    def builder_plan(self, template="torre.csv"):
        # Carga un template para construir
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.builder_plan(template)

    def builder_bom(self):
        # Publica la lista de materiales
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.builder_bom()

    def builder_build(self):
        # Le dice al builder que construya
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.builder_build()

    def pause(self, agent_name="ALL"):
        # Pausa agentes
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.pause_agent(agent_name)

    def resume(self, agent_name="ALL"):
        # Reanuda agentes
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.resume_agent(agent_name)

    def stop(self, agent_name="ALL"):
        # Para agentes
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.stop_agent(agent_name)

    def status(self, agent_name="ALL"):
        # Pide el estado de los agentes
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.status(agent_name)

    def workflow(self, x=None, z=None, range_scan=6, template="torre.csv", strategy="vertical"):
        # Ejecuta todo el workflow de una vez
        if not self.is_connected():
            return {"success": False, "message": "No conectado"}
        return self.controller.workflow_run(x, z, range_scan, template, strategy)


def print_result(result):
    # Muestra el resultado de un comando de forma bonita
    if result["success"]:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")


def interactive_mode():
    # Modo interactivo - se conecta directamente a localhost
    print("=" * 60)
    print("CLIENTE DE CONTROL REMOTO - Minecraft Agents")
    print("=" * 60)
    print("Conectando a localhost:9090...")
    print("")

    # Conectar directamente a localhost
    client = RemoteClient("localhost", 9090)


    if not client.is_connected():
        print("\nNo se pudo conectar. Saliendo...")
        return

    print("\nComandos disponibles:")
    print("  1. explorer start [x] [z] [range]")
    print("  2. miner start [x] [z] [y] [strategy]")
    print("  3. miner fulfill")
    print("  4. builder plan [template]")
    print("  5. builder bom")
    print("  6. builder build")
    print("  7. pause [agent]")
    print("  8. resume [agent]")
    print("  9. stop [agent]")
    print(" 10. status [agent]")
    print(" 11. workflow [x] [z] [range] [template] [strategy]")
    print("  q. quit")
    print("")

    while True:
        try:
            cmd = input("> ").strip().lower()

            if cmd == "q" or cmd == "quit":
                print("Saliendo...")
                break

            parts = cmd.split()
            if not parts:
                continue

            if parts[0] == "explorer" and len(parts) >= 2 and parts[1] == "start":
                x = int(parts[2]) if len(parts) > 2 else None
                z = int(parts[3]) if len(parts) > 3 else None
                r = int(parts[4]) if len(parts) > 4 else 6
                result = client.explorer_start(x, z, r)
                print_result(result)

            elif parts[0] == "miner" and len(parts) >= 2 and parts[1] == "start":
                x = int(parts[2]) if len(parts) > 2 else None
                z = int(parts[3]) if len(parts) > 3 else None
                y = int(parts[4]) if len(parts) > 4 else None
                s = parts[5] if len(parts) > 5 else "vertical"
                result = client.miner_start(x, z, y, s)
                print_result(result)

            elif parts[0] == "miner" and len(parts) >= 2 and parts[1] == "fulfill":
                result = client.miner_fulfill()
                print_result(result)

            elif parts[0] == "builder" and len(parts) >= 2 and parts[1] == "plan":
                template = parts[2] if len(parts) > 2 else "torre.csv"
                result = client.builder_plan(template)
                print_result(result)

            elif parts[0] == "builder" and len(parts) >= 2 and parts[1] == "bom":
                result = client.builder_bom()
                print_result(result)

            elif parts[0] == "builder" and len(parts) >= 2 and parts[1] == "build":
                result = client.builder_build()
                print_result(result)

            elif parts[0] == "pause":
                agent = parts[1] if len(parts) > 1 else "ALL"
                result = client.pause(agent)
                print_result(result)

            elif parts[0] == "resume":
                agent = parts[1] if len(parts) > 1 else "ALL"
                result = client.resume(agent)
                print_result(result)

            elif parts[0] == "stop":
                agent = parts[1] if len(parts) > 1 else "ALL"
                result = client.stop(agent)
                print_result(result)

            elif parts[0] == "status":
                agent = parts[1] if len(parts) > 1 else "ALL"
                result = client.status(agent)
                print_result(result)

            elif parts[0] == "workflow":
                x = int(parts[1]) if len(parts) > 1 else None
                z = int(parts[2]) if len(parts) > 2 else None
                r = int(parts[3]) if len(parts) > 3 else 6
                t = parts[4] if len(parts) > 4 else "torre.csv"
                s = parts[5] if len(parts) > 5 else "vertical"
                result = client.workflow(x, z, r, t, s)
                print_result(result)

            else:
                print("Comando no reconocido. Escribe 'q' para salir.")

        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    interactive_mode()

