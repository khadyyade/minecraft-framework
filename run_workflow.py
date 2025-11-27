"""
Script de orquestación para ejecutar los agentes en procesos separados.

Este archivo sirve como ejemplo para arrancar ExplorerBot, MinerBot y BuilderBot
en procesos diferentes usando `multiprocessing.Process` y `Queue`.

Es un demostrador: no implementa un parser robusto ni recuperación completa.
"""
from multiprocessing import Process, Queue
import time
import json

from minecraft_framework.agents.explorer import agent_process_main as explorer_main
from minecraft_framework.agents.miner import agent_process_main as miner_main
from minecraft_framework.agents.builder import agent_process_main as builder_main


def start_agents(mc_host="localhost", mc_port=4711, use_minecraft=True):
    """Inicia los agentes en procesos separados.
    
    Args:
        mc_host: Host del servidor Minecraft (default: localhost)
        mc_port: Puerto del servidor Minecraft (default: 4711 para RaspberryJuice)
        use_minecraft: Si True, intenta conectar a Minecraft; si False, usa simulación
    """
    # Crear colas de comunicación (cada agente tiene su propia cola de entrada)
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()

    # Map de colas que cada agente necesita conocer (nombres arbitrarios)
    # En un diseño real, este mapeo sería dinámico o convenido por configuración
    out_queues_for_explorer = {"BuilderBot": q_builder, "MinerBot": q_miner}
    out_queues_for_miner = {"BuilderBot": q_builder, "ExplorerBot": q_explorer}
    out_queues_for_builder = {"MinerBot": q_miner, "ExplorerBot": q_explorer}

    # Preparar kwargs comunes (conexión a Minecraft)
    common_kwargs = {}
    if use_minecraft:
        common_kwargs["mc_host"] = mc_host
        common_kwargs["mc_port"] = mc_port

    # Lanzar procesos
    explorer_kwargs = {**common_kwargs, "x": 0, "z": 0, "range": 8}
    miner_kwargs = {**common_kwargs, "strategy": "vertical"}
    builder_kwargs = {**common_kwargs}
    
    p_explorer = Process(target=explorer_main, args=(q_explorer, out_queues_for_explorer), kwargs=explorer_kwargs)
    p_miner = Process(target=miner_main, args=(q_miner, out_queues_for_miner), kwargs=miner_kwargs)
    p_builder = Process(target=builder_main, args=(q_builder, out_queues_for_builder), kwargs=builder_kwargs)

    p_explorer.start()
    p_miner.start()
    p_builder.start()

    try:
        print("Agents started. Type commands or Ctrl-C to stop.")
        # demo: recibir mensajes desde las colas y mostrar por pantalla
        while True:
            # escuchar cualquier mensaje en las queues para mostrar progreso
            for name, q in [("Explorer", q_explorer), ("Miner", q_miner), ("Builder", q_builder)]:
                while not q.empty():
                    raw = q.get()
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        msg = raw
                    print(f"[Main] Message from {name}: {msg}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping agents...")
        p_explorer.terminate()
        p_miner.terminate()
        p_builder.terminate()
        p_explorer.join(timeout=1)
        p_miner.join(timeout=1)
        p_builder.join(timeout=1)


if __name__ == "__main__":
    import sys
    
    # Parsear argumentos simples
    use_minecraft = "--no-minecraft" not in sys.argv
    mc_host = "localhost"
    mc_port = 4711
    
    # Permitir cambiar host/puerto desde la línea de comandos
    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            mc_host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            mc_port = int(arg.split("=", 1)[1])
    
    print(f"Starting agents...")
    if use_minecraft:
        print(f"Connecting to Minecraft server at {mc_host}:{mc_port}")
        print("(Use --no-minecraft to run in simulation mode)")
    else:
        print("Running in simulation mode (no Minecraft connection)")
    
    start_agents(mc_host=mc_host, mc_port=mc_port, use_minecraft=use_minecraft)
