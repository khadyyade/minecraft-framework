import asyncio
from multiprocessing import Process, Queue

def _miner_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    """Entry point del proceso del Miner."""
    from minecraft_framework.agents.miner import Miner

    bot = Miner("MinerBot", in_q, q_explorer, q_miner, q_builder)
    asyncio.run(bot.iniciarAgente())

async def main():
    """Runner para probar MinerBot en Minecraft usando ChatRouter.

    - Crea colas UNA sola vez (en este proceso).
    - Arranca MinerBot en su propio proceso.
    - Ejecuta ChatRouter en el proceso principal (single consumer de chat).
    - Inyecta requirements falsos para no depender de BuilderBot.

    Comandos (en el chat de Minecraft):
      - \\miner set strategy vertical
      - \\miner start x=10 z=5 y=64
      - \\miner pause | resume | status | fulfill
      - \\agent stop   (broadcast)

    Nota: para terminar, Ctrl+C en esta terminal.
    """

    # 1) Colas (una por agente). Para este test solo usamos Miner,
    # pero el framework espera que existan las tres.
    q_miner = Queue()
    q_builder = Queue()
    q_explorer = Queue()

    # 2) Arrancar Miner en un proceso
    miner_proc = Process(
        target=_miner_process,
        args=(q_miner, q_explorer, q_miner, q_builder),
        name="MinerBot",
    )
    miner_proc.start()

    # 2.1) Inyectar requirements falsos (como si vinieran del Builder)
    # El Miner espera `materials.requirements.v1` con payload tipo {'bom': {...}}.
    fake_requirements_msg = {
        "type": "materials.requirements.v1",
        "origin": "TestHarness",
        "timestamp": 0,
        "payload": {"gold_block": 11, "iron_block":6},
    }
    q_miner.put_nowait(fake_requirements_msg)

    # 3) Conectar a Minecraft y arrancar ChatRouter
    from mcpi.minecraft import Minecraft
    from minecraft_framework.cli import ChatRouter

    mc = Minecraft.create()
    router = ChatRouter(mc, q_miner=q_miner, q_builder=q_builder, q_explorer=q_explorer)

    try:
        await router.run()
    except KeyboardInterrupt:
        pass
    finally:
        router.stop()
        if miner_proc.is_alive():
            miner_proc.terminate()
        miner_proc.join(timeout=2)


if __name__ == "__main__":
    asyncio.run(main())
