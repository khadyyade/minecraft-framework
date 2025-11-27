# Importamos las librerías necesarias
from multiprocessing import Process, Queue
import time
import json
# Renombramos los mains de cada agente con un nombre mas facil
from minecraft_framework.agents.explorer import agent_process_main as explorer_main
from minecraft_framework.agents.miner import agent_process_main as miner_main
from minecraft_framework.agents.builder import agent_process_main as builder_main

# Función que inicia a los 3 agentes
# Parametro 1 (mc_host) indica el host del servidor, por defecto localhost
# Parametro 2 (mc_port) indica el puerto del servidor, por defecto 4711
#   [11:38:58 INFO]: [RaspberryJuice] Enabling RaspberryJuice v1.10
#   [11:38:58 INFO]: [RaspberryJuice] Using port 4711

def start_agents(mc_host="localhost", mc_port=4711):

    # Crear las colas (cada agente tiene la suya)
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()

    # Parámetros de conexión a Minecraft que se pasan a todos los agentes
    # Contiene: mc_host (ej: "localhost") y mc_port (ej: 4711)
    minecraft_connection_params = {
        "mc_host": mc_host,
        "mc_port": mc_port
    }

    # Parámetros que necesita cada agente para funcionar
    # Hay que intentar pasar los params por terminal tambien
    explorer_kwargs = {**minecraft_connection_params, "x": 0, "z": 0, "range": 8}
    miner_kwargs = {**minecraft_connection_params, "strategy": "vertical"}
    builder_kwargs = {**minecraft_connection_params}


    # Lanzar procesos de cada agente con los parámetros que necesitan
    # args: (cola_propia, cola_explorer, cola_miner, cola_builder)
    p_explorer = Process(target=explorer_main, args=(q_explorer, q_explorer, q_miner, q_builder), kwargs=explorer_kwargs)
    p_miner = Process(target=miner_main, args=(q_miner, q_explorer, q_miner, q_builder), kwargs=miner_kwargs)
    p_builder = Process(target=builder_main, args=(q_builder, q_explorer, q_miner, q_builder), kwargs=builder_kwargs)

    # Una vez creados solo queda iniciarlos
    p_explorer.start()
    p_miner.start()
    p_builder.start()


    # Con este bucle vamos a controlar los mensajes que circulan por las mailboxes
    # Y a detener los procesos si se pulas CTRL+C
    try:
        print("Todos los agentes se han inciado. Puedes detener con CTRL+C")
        # Recibimos los mensajes desde las colas y los mostramos por pantalla
        while True:
            # Iterar por todas las colas
            for name, q in [("Explorer", q_explorer), ("Miner", q_miner), ("Builder", q_builder)]:
                # Cuando encontremos una cola no vacia
                while not q.empty():
                    # Obtener el mensaje de la cola
                    raw = q.get()
                    # Intentamos mostrar como JSON
                    try:
                        msg = json.loads(raw)
                    # Si no lo mostramos como texto plano
                    except Exception:
                        msg = raw
                    print(f"[Main] Message from {name}: {msg}")
            time.sleep(0.5)
    # Cuando se pulsa CTRL+C cancelamos todo
    except KeyboardInterrupt:
        print("Stopping agents...")
        p_explorer.terminate()
        p_miner.terminate()
        p_builder.terminate()
        p_explorer.join(timeout=1)
        p_miner.join(timeout=1)
        p_builder.join(timeout=1)

# Main de todo el programa python que lee si hay parámetros concretos por terminal para lanzar los agentes
if __name__ == "__main__":
    import sys
    
    # Por defecto siempre conecta a localhost:4711
    mc_host = "localhost"
    mc_port = 4711
    
    # Se permite cambiar host y/o puerto desde terminal
    # python main.py --host=192.168.1.100 --port=4711
    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            mc_host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            mc_port = int(arg.split("=", 1)[1])
    
    print(f"Iniciando agentes...")
    print(f"Conectando al servidor de Minecraft en: {mc_host}:{mc_port}")
    # Lanzamos la función principal que inicia los agentes
    start_agents(mc_host=mc_host, mc_port=mc_port)
