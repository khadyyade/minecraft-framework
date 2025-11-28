# Importamos las librerías necesarias
from multiprocessing import Process, Queue
import time
import json
import importlib


# Función para obtener un agente usando reflection (importlib) (Punto 3)
# Parametro: nombre del agente
# Salida: clase del agente
def obtenerClaseAgente(agent_name: str):

    module = importlib.import_module(f"minecraft_framework.agents.{agent_name}")
    # Obtener la clase principal del módulo (ExplorerBot, MinerBot, BuilderBot)
    class_name = agent_name.capitalize() + "Bot"
    return getattr(module, class_name)


# Función que inicia a los 3 agentes
# Parametro 1 (mc_host) indica el host del servidor, por defecto localhost
# Parametro 2 (mc_port) indica el puerto del servidor, por defecto 4711
#   [11:38:58 INFO]: [RaspberryJuice] Enabling RaspberryJuice v1.10
#   [11:38:58 INFO]: [RaspberryJuice] Using port 4711

def iniciarAgentes(mc_host="localhost", mc_port=4711):
    
    # Cargar las clases de los agentes usando reflection
    ExplorerBot = obtenerClaseAgente("explorer")
    MinerBot = obtenerClaseAgente("miner")
    BuilderBot = obtenerClaseAgente("builder")

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


    # Lanzar procesos de cada agente usando las clases obtenidas del registry
    # Cada agente se instancia con sus colas y parámetros específicos
    # args: (cola_propia, cola_explorer, cola_miner, cola_builder)
    p_explorer = Process(target=ExplorerBot.agent_process_main, args=(q_explorer, q_explorer, q_miner, q_builder), kwargs=explorer_kwargs)
    p_miner = Process(target=MinerBot.agent_process_main, args=(q_miner, q_explorer, q_miner, q_builder), kwargs=miner_kwargs)
    p_builder = Process(target=BuilderBot.agent_process_main, args=(q_builder, q_explorer, q_miner, q_builder), kwargs=builder_kwargs)

    # Una vez creados solo queda iniciarlos
    # Al hacer .start() se ejecuta el método agent_process_main de ese agente
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

                    # Mostrammos como JSON
                    msg = json.loads(raw)
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
    iniciarAgentes(mc_host=mc_host, mc_port=mc_port)
