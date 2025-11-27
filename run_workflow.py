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


def start_agents():
    # Crear colas de comunicación (cada agente tiene su propia cola de entrada)
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()

    # Map de colas que cada agente necesita conocer (nombres arbitrarios)
    # En un diseño real, este mapeo sería dinámico o convenido por configuración
    out_queues_for_explorer = {"BuilderBot": q_builder, "MinerBot": q_miner}
    out_queues_for_miner = {"BuilderBot": q_builder, "ExplorerBot": q_explorer}
    out_queues_for_builder = {"MinerBot": q_miner, "ExplorerBot": q_explorer}

    # Lanzar procesos
    p_explorer = Process(target=explorer_main, args=(q_explorer, out_queues_for_explorer), kwargs={"x": 0, "z": 0, "range": 8})
    p_miner = Process(target=miner_main, args=(q_miner, out_queues_for_miner), kwargs={"strategy": "vertical"})
    p_builder = Process(target=builder_main, args=(q_builder, out_queues_for_builder), kwargs={})

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
    start_agents()
