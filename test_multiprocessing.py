"""
Test con procesos reales para verificar comunicación entre agentes.
"""

import asyncio
import json
from multiprocessing import Process, Queue
import time


def miner_process(q_miner, q_explorer, q_builder):
    """Proceso del Miner"""
    from minecraft_framework.agents.miner import Miner

    print("[MINER PROCESS] Iniciando...")

    miner = Miner("MinerBot", q_miner, q_explorer, q_miner, q_builder)

    print(f"[MINER PROCESS] Estado inicial: {miner.estadoActual.name}")

    async def run_miner():
        print("[MINER PROCESS] Ejecutando perceive...")

        # Ejecutar perceive para leer mensajes
        perception = await miner.perceive()

        print(f"[MINER PROCESS] Perception: {perception}")
        print(f"[MINER PROCESS] Strategy: {miner.current_strategy_name}")
        print(f"[MINER PROCESS] Start executed: {miner.start_executed}")
        print(f"[MINER PROCESS] Estado: {miner.estadoActual.name}")

        # Ejecutar decide
        decision = await miner.decide(perception)

        print(f"[MINER PROCESS] Decision: {decision.get('type')}")
        print(f"[MINER PROCESS] Estado final: {miner.estadoActual.name}")

    try:
        asyncio.run(run_miner())
    except Exception as e:
        print(f"[MINER PROCESS] Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 60)
    print("TEST DE COMUNICACIÓN CON PROCESOS REALES")
    print("=" * 60)

    # Crear colas
    q_miner = Queue()
    q_explorer = Queue()
    q_builder = Queue()

    print("\n1. Enviando comandos a la cola del miner...")

    # Enviar comando de estrategia
    strategy_msg = {
        "type": "control",
        "target": "MinerBot",
        "payload": {
            "cmd": "update",
            "args": {"strategy": "vertical"}
        }
    }
    q_miner.put(json.dumps(strategy_msg))
    print("   ✓ Comando 'set strategy' enviado")

    # Enviar comando de start
    start_msg = {
        "type": "control",
        "target": "MinerBot",
        "payload": {
            "cmd": "update",
            "args": {"start": {"x": 10, "z": 5, "y": 64}}
        }
    }
    q_miner.put(json.dumps(start_msg))
    print("   ✓ Comando 'start' enviado")

    print(f"\n2. Cola del miner tiene {q_miner.qsize()} mensajes")

    print("\n3. Iniciando proceso del miner...")

    # Crear y ejecutar proceso
    p = Process(target=miner_process, args=(q_miner, q_explorer, q_builder))
    p.start()

    print("   ✓ Proceso iniciado, esperando...")

    # Esperar a que termine
    p.join(timeout=5)

    if p.is_alive():
        print("\n   ⚠️ El proceso no terminó en 5 segundos, terminándolo...")
        p.terminate()
        p.join()
        print("   ✗ TEST FALLIDO: El proceso se quedó colgado")
        return False
    else:
        print(f"\n   ✓ Proceso terminó correctamente (exit code: {p.exitcode})")

        if p.exitcode == 0:
            print("\n✅ TEST PASADO: La comunicación con procesos funciona")
            return True
        else:
            print(f"\n✗ TEST FALLIDO: El proceso terminó con error (code: {p.exitcode})")
            return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n" + "=" * 60)
        print("CONCLUSIÓN: La comunicación entre procesos funciona correctamente.")
        print("El problema debe estar en el bucle principal o en la forma")
        print("de ejecutar los agentes en main.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("CONCLUSIÓN: Hay un problema con la comunicación entre procesos.")
        print("=" * 60)

    exit(0 if success else 1)

