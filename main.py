# Main mejorado que inicia los tres agentes en estado IDLE
# y utiliza ChatRouter para gestionar comandos desde el chat de Minecraft
#
# Los agentes permanecen en IDLE hasta recibir comandos específicos vía chat:
# - $ explorer start x=<int> z=<int> [range=<int>]
# - $ miner start [x=<int> z=<int> y=<int>]
# - $ builder plan set <template>
#
# Para detener: CTRL+C en la terminal

import asyncio
from multiprocessing import Process, Queue
import importlib


def _explorer_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    """Entry point del proceso del Explorer."""
    import asyncio
    from mcpi.minecraft import Minecraft

    # Cargar ExplorerBot con reflection
    explorer_module = importlib.import_module('minecraft_framework.agents.explorer')
    ExplorerBot = getattr(explorer_module, 'ExplorerBot')

    # Conectar a Minecraft dentro del proceso
    try:
        mc = Minecraft.create()
        print(f"[ExplorerBot] Conectado a Minecraft")
    except Exception as e:
        print(f"[ExplorerBot] Error al conectar: {e}")
        mc = None

    bot = ExplorerBot("ExplorerBot", in_q, q_explorer, q_miner, q_builder, mc=mc)
    asyncio.run(bot.iniciarAgente())


def _miner_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    """Entry point del proceso del Miner."""
    import asyncio
    from mcpi.minecraft import Minecraft

    # Cargar Miner con reflection
    miner_module = importlib.import_module('minecraft_framework.agents.miner')
    Miner = getattr(miner_module, 'Miner')

    # Conectar a Minecraft dentro del proceso
    try:
        mc = Minecraft.create()
        print(f"[MinerBot] Conectado a Minecraft")
    except Exception as e:
        print(f"[MinerBot] Error al conectar: {e}")
        mc = None

    bot = Miner("MinerBot", in_q, q_explorer, q_miner, q_builder)
    if mc:
        bot.mc = mc
    asyncio.run(bot.iniciarAgente())


def _builder_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    """Entry point del proceso del Builder."""
    import asyncio
    from mcpi.minecraft import Minecraft

    # Cargar BuilerBot con reflection
    builder_module = importlib.import_module('minecraft_framework.agents.builder')
    BuilerBot = getattr(builder_module, 'BuilerBot')

    # Conectar a Minecraft dentro del proceso
    try:
        mc = Minecraft.create()
        print(f"[BuilderBot] Conectado a Minecraft")
    except Exception as e:
        print(f"[BuilderBot] Error al conectar: {e}")
        mc = None

    bot = BuilerBot("BuilderBot", in_q, q_explorer, q_miner, q_builder)
    if mc:
        bot.mc = mc
    asyncio.run(bot.iniciarAgente())


async def main():
    """
    Main que inicia los 3 agentes en estado IDLE y el ChatRouter.

    Los agentes permanecen en IDLE hasta recibir comandos desde Minecraft:

    ExplorerBot:
      - $explorer start x=<int> z=<int> [range=<int>]
      - $explorer stop
      - $explorer set range <int>
      - $explorer status

    MinerBot:
      - $miner start [x=<int> z=<int> y=<int>]
      - $miner set strategy <vertical|grid|vein>
      - $miner fulfill
      - $miner pause
      - $miner resume
      - $miner status

    BuilderBot:
      - $builder plan list
      - $builder plan set <template>
      - $builder bom
      - $builder build
      - $builder pause
      - $builder resume
      - $builder status

    Control Global:
      - $agent stop (detiene todos los agentes)
    """

    print("=" * 60)
    print("MINECRAFT FRAMEWORK - Iniciando sistema de agentes")
    print("=" * 60)

    # Crear las colas (una por agente)
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()

    print("[Main] Creando colas de comunicación...")

    # Arrancar los tres agentes en procesos separados
    print("[Main] Iniciando ExplorerBot en estado IDLE...")
    explorer_proc = Process(
        target=_explorer_process,
        args=(q_explorer, q_explorer, q_miner, q_builder),
        name="ExplorerBot",
    )
    explorer_proc.start()

    print("[Main] Iniciando MinerBot en estado IDLE...")
    miner_proc = Process(
        target=_miner_process,
        args=(q_miner, q_explorer, q_miner, q_builder),
        name="MinerBot",
    )
    miner_proc.start()

    print("[Main] Iniciando BuilderBot en estado IDLE...")
    builder_proc = Process(
        target=_builder_process,
        args=(q_builder, q_explorer, q_miner, q_builder),
        name="BuilderBot",
    )
    builder_proc.start()

    # Pequeña pausa para que los agentes se inicialicen
    await asyncio.sleep(1)

    # ============================================================================
    # OPCIONAL: CONTROL REMOTO
    # ============================================================================
    import threading

    # Cargar el módulo de control remoto con reflection
    remote_module = importlib.import_module('remote_control')
    start_remote_server = getattr(remote_module, 'start_remote_server')

    # Iniciar servidor remoto en un thread separado
    remote_thread = threading.Thread(
        target=start_remote_server,
        args=(q_explorer, q_miner, q_builder),
        kwargs={"host": "0.0.0.0", "port": 9090},
        daemon=True
    )
    remote_thread.start()
    print("[Main] ✓ Servidor de control remoto iniciado en puerto 9090")
    print("[Main]   Los clientes pueden conectarse remotamente")
    print("")
    # ============================================================================

    # Conectar a Minecraft para el ChatRouter
    print("[Main] Conectando al servidor de Minecraft...")
    try:
        from mcpi.minecraft import Minecraft
        mc = Minecraft.create()
        print("[Main] ✓ Conexión a Minecraft establecida")
    except Exception as e:
        print(f"[Main] ✗ Error al conectar con Minecraft: {e}")
        print("[Main] El ChatRouter no podrá funcionar sin conexión")
        print("[Main] Asegúrate de que:")
        print("  1. Minecraft está ejecutándose")
        print("  2. El plugin RaspberryJuice está instalado")
        print("  3. El servidor está en localhost:4711")
        # Terminar procesos
        explorer_proc.terminate()
        miner_proc.terminate()
        builder_proc.terminate()
        return

    # Arrancar ChatRouter
    print("[Main] Iniciando ChatRouter...")

    # Cargar ChatRouter con reflection
    cli_module = importlib.import_module('minecraft_framework.cli')
    ChatRouter = getattr(cli_module, 'ChatRouter')

    router = ChatRouter(mc, q_miner=q_miner, q_builder=q_builder, q_explorer=q_explorer)

    print("=" * 60)
    print("SISTEMA INICIADO")
    print("=" * 60)
    print("Los agentes están en estado IDLE esperando comandos.")
    print("Usa los comandos en el chat de Minecraft (prefijo $):")
    print("  - $explorer start x=0 z=0 range=10")
    print("  - $miner start x=10 z=5 y=64")
    print("  - $builder plan list")
    print("  - $agent stop (para detener todos)")
    print("")
    print("Para salir: CTRL+C")
    print("=" * 60)

    try:
        await router.run()
    except KeyboardInterrupt:
        print("\n[Main] Deteniendo sistema...")
    finally:
        router.stop()

        # Terminar procesos
        if explorer_proc.is_alive():
            explorer_proc.terminate()
        if miner_proc.is_alive():
            miner_proc.terminate()
        if builder_proc.is_alive():
            builder_proc.terminate()

        explorer_proc.join(timeout=2)
        miner_proc.join(timeout=2)
        builder_proc.join(timeout=2)

        print("[Main] Sistema detenido correctamente.")


if __name__ == "__main__":
    asyncio.run(main())
