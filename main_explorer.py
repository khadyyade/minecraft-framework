# Main simplificado para solo ejecutar ExplorerBot
from multiprocessing import Process, Queue
import time
import json
import importlib


def obtenerClaseAgente(agent_name: str):
    # Obtiene la clase del agente usando reflection.
    module = importlib.import_module(f"minecraft_framework.agents.{agent_name}")
    class_name = agent_name.capitalize() + "Bot"
    return getattr(module, class_name)


def iniciarExplorer(mc_host="localhost", mc_port=4711, x=0, z=0, scan_range=8, tam_planicie=4):
    """Inicia solo el ExplorerBot.
    
    Args:
        mc_host: Host del servidor Minecraft
        mc_port: Puerto del servidor Minecraft
        x: Coordenada X inicial
        z: Coordenada Z inicial
        scan_range: Rango de escaneo
        tam_planicie: Tamaño de la planicie a buscar (NxN)
    """
    # Cargar clase del ExplorerBot
    ExplorerBot = obtenerClaseAgente("explorer")

    # Crear cola para el explorer
    q_explorer = Queue()
    
    # Crear colas dummy para los otros agentes (no se usarán)
    q_miner = Queue()
    q_builder = Queue()

    # Parámetros de conexión a Minecraft
    minecraft_connection_params = {
        "mc_host": mc_host,
        "mc_port": mc_port
    }

    # Parámetros específicos del explorer
    explorer_kwargs = {
        **minecraft_connection_params,
        "x": x,
        "z": z,
        "range": scan_range,
        "size": tam_planicie
    }

    # Lanzar proceso del ExplorerBot
    # args: (cola_propia, cola_explorer, cola_miner, cola_builder)
    p_explorer = Process(
        target=ExplorerBot.agent_process_main,
        args=(q_explorer, q_explorer, q_miner, q_builder),
        kwargs=explorer_kwargs
    )

    # Iniciar el proceso
    p_explorer.start()

    # Bucle de control de mensajes
    try:
        print("ExplorerBot iniciado. Puedes detenerlo con CTRL+C")
        print(f"Conectado a: {mc_host}:{mc_port}")
        print(f"Escaneando desde ({x}, {z}) con rango {scan_range}")
        print(f"Buscando planicie de tamaño {tam_planicie}x{tam_planicie}")
        print("-" * 60)
        
        while True:
            # Leer mensajes de la cola del explorer
            while not q_explorer.empty():
                raw = q_explorer.get()
                msg = json.loads(raw)
                print(f"[Main] ExplorerBot: {msg}")
                    
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nParando ExplorerBot")
        p_explorer.terminate()
        p_explorer.join(timeout=1)
        print("ExplorerBot parado")


if __name__ == "__main__":
    import sys
    
    # Valores por defecto
    param_mc_host = "localhost"
    param_mc_port = 4711
    param_x = 0
    param_z = 0
    param_scan_range = 8
    param_tam_planicie = 4
    
    # Leer parámetros desde terminal
    # Uso: python main_explorer.py --host=localhost --port=4711 --x=0 --z=0 --range=8 --size=4
    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            param_mc_host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            param_mc_port = int(arg.split("=", 1)[1])
        elif arg.startswith("--x="):
            param_x = int(arg.split("=", 1)[1])
        elif arg.startswith("--z="):
            param_z = int(arg.split("=", 1)[1])
        elif arg.startswith("--range="):
            param_scan_range = int(arg.split("=", 1)[1])
        elif arg.startswith("--size="):
            param_tam_planicie = int(arg.split("=", 1)[1])
    
    print("=" * 60)
    print("INICIANDO EXPLORERBOT")
    print("=" * 60)
    iniciarExplorer(
        mc_host=param_mc_host,
        mc_port=param_mc_port,
        x=param_x,
        z=param_z,
        scan_range=param_scan_range,
        tam_planicie=param_tam_planicie
    )
