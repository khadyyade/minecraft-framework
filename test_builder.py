import asyncio
from multiprocessing import Process, Queue

def _builder_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    """Entry point del proceso del Builder."""
    from minecraft_framework.agents.builder import BuilerBot

    bot = BuilerBot("BuilderBot", in_q, q_explorer, q_miner, q_builder)
    asyncio.run(bot.iniciarAgente())

async def main():
    """Runner para probar BuilderBot en Minecraft usando ChatRouter.

    - Crea colas UNA sola vez (en este proceso).
    - Arranca BuilderBot en su propio proceso.
    - Ejecuta ChatRouter en el proceso principal (single consumer de chat).
    - Inyecta mapa falso (como si viniera de ExplorerBot).
    - Inyecta inventario falso (como si viniera de MinerBot).

    Comandos (en el chat de Minecraft):
      - $builder plan list
      - $builder plan set little_house.csv
      - $builder bom
      - $builder build
      - $builder pause | resume
      - $agent stop   (broadcast)

    Nota: para terminar, Ctrl+C en esta terminal.
    """

    # 1) Colas (una por agente). Para este test solo usamos Builder,
    # pero el framework espera que existan las tres.
    q_builder = Queue()
    q_miner = Queue()
    q_explorer = Queue()

    # 2) Arrancar Builder en un proceso
    builder_proc = Process(
        target=_builder_process,
        args=(q_builder, q_explorer, q_miner, q_builder),
        name="BuilderBot",
    )
    builder_proc.start()

    # Conectar a Minecraft para obtener posición del jugador
    from mcpi.minecraft import Minecraft
    mc = Minecraft.create()

    # Obtener posición del jugador
    player_pos = mc.player.getTilePos()

    # Construir 5 bloques delante del jugador (en dirección +X)
    build_x = player_pos.x + 1
    build_z = player_pos.z
    build_y = player_pos.y

    print(f"[TestHarness] Jugador en ({player_pos.x}, {player_pos.y}, {player_pos.z})")
    print(f"[TestHarness] Construcción en ({build_x}, {build_y}, {build_z})")

    # 2.1) Inyectar mensaje de mapa falso (como si viniera del ExplorerBot)
    # El Builder espera `map.v1` con coordenadas de terreno plano.
    fake_map_msg = {
        "type": "map.v1",
        "origin": "TestHarness",
        "timestamp": 0,
        "payload": {
            "coordenadasInicioTerrenoPlano": {"x": build_x, "z": build_z},
            "coordenadasFinalTerrenoPlano": {"x": build_x + 10, "z": build_z + 10},
            "alturaPlanicie": build_y
        }
    }
    q_builder.put_nowait(fake_map_msg)

    # 2.2) Inyectar inventario falso inmediatamente (como si viniera del MinerBot)
    fake_inventory_msg = {
        "type": "materials.inventory.v1",
        "origin": "TestHarness",
        "timestamp": 0,
        "payload": {
            "stone": 20,
            "planks": 30,
            "wood_planks": 30,
            "cobblestone": 20,
            "gold_block": 15,
            "iron_block": 10
        }
    }
    q_builder.put_nowait(fake_inventory_msg)
    print("[TestHarness] Inventario falso inyectado en la cola del Builder")

    # 2.3) Esperar un poco para que el Builder procese los mensajes
    await asyncio.sleep(1)

    # 3) Arrancar ChatRouter (mc ya está creado arriba)
    from minecraft_framework.cli import ChatRouter

    router = ChatRouter(mc, q_miner=q_miner, q_builder=q_builder, q_explorer=q_explorer)


    try:
        await router.run()
    except KeyboardInterrupt:
        print("\n[TestHarness] Deteniendo...")
    finally:
        router.stop()
        if builder_proc.is_alive():
            builder_proc.terminate()
        builder_proc.join(timeout=2)
        print("[TestHarness] Test finalizado.")


if __name__ == "__main__":
    asyncio.run(main())

