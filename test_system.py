"""
Script de prueba para verificar el sistema de agentes.

Ejecuta: python test_system.py
"""
import time

def test_imports():
    """Prueba 1: Verificar que todos los imports funcionan"""
    print("=" * 60)
    print("TEST 1: Verificando imports...")
    print("=" * 60)

    try:
        from minecraft_framework.agents.miner import Miner
        from minecraft_framework.agents.builder import BuilerBot
        from minecraft_framework.agents.explorer import ExplorerBot
        from minecraft_framework.cli import ChatRouter, parse_command
        print("✓ Todos los imports funcionan correctamente")
        return True
    except Exception as e:
        print(f"✗ Error en imports: {e}")
        return False

def test_command_parsing():
    """Prueba 2: Verificar que los comandos se parsean correctamente"""
    print("\n" + "=" * 60)
    print("TEST 2: Verificando parseo de comandos...")
    print("=" * 60)

    from minecraft_framework.cli import parse_command

    tests = [
        ("$miner set strategy vertical", {"type": "control", "target": "MinerBot"}),
        ("$miner start x=10 z=5 y=64", {"type": "control", "target": "MinerBot"}),
        ("$miner status", {"type": "control", "target": "MinerBot"}),
        ("$explorer start x=0 z=0", {"type": "control", "target": "ExplorerBot"}),
        ("$builder plan list", {"type": "control", "target": "BuilderBot"}),
    ]

    all_passed = True
    for cmd, expected in tests:
        result = parse_command(cmd)
        if result.get("type") == expected.get("type") and result.get("target") == expected.get("target"):
            print(f"✓ '{cmd}' → {result.get('type')}")
        else:
            print(f"✗ '{cmd}' → {result}")
            all_passed = False

    return all_passed

def test_agent_states():
    """Prueba 3: Verificar estados de agentes"""
    print("\n" + "=" * 60)
    print("TEST 3: Verificando estados de agentes...")
    print("=" * 60)

    from minecraft_framework.baseAgent import EstadoAgente
    from multiprocessing import Queue
    from minecraft_framework.agents.miner import Miner

    # Crear colas
    q1 = Queue()
    q2 = Queue()
    q3 = Queue()

    # Crear agente
    miner = Miner("TestMiner", q1, q1, q2, q3)

    # Verificar estado inicial
    if miner.estadoActual == EstadoAgente.IDLE:
        print(f"✓ Estado inicial: {miner.estadoActual.name}")
    else:
        print(f"✗ Estado inicial incorrecto: {miner.estadoActual.name}")
        return False

    # Verificar flags
    print(f"  - start_executed: {miner.start_executed}")
    print(f"  - strategy_setted: {miner.strategy_setted}")
    print(f"  - can_mine(): {miner.can_mine()}")

    return True

def test_message_sending():
    """Prueba 4: Verificar envío de mensajes entre agentes"""
    print("\n" + "=" * 60)
    print("TEST 4: Verificando envío de mensajes...")
    print("=" * 60)

    from multiprocessing import Queue
    from minecraft_framework.agents.miner import Miner
    from minecraft_framework.agents.builder import BuilerBot
    import json

    # Crear colas
    q_miner = Queue()
    q_builder = Queue()
    q_explorer = Queue()

    # Crear agentes
    builder = BuilerBot("TestBuilder", q_builder, q_explorer, q_miner, q_builder)
    miner = Miner("TestMiner", q_miner, q_explorer, q_miner, q_builder)

    print("\n1. Builder envía BOM al Miner...")

    # Builder envía mensaje al Miner
    test_bom = {
        "type": "materials.requirements.v1",
        "origin": "TestBuilder",
        "timestamp": 0,
        "payload": {"stone": 10, "dirt": 5}
    }

    builder.enviarMensaje("MinerBot", test_bom)

    # Verificar que el mensaje llegó a la cola del miner
    import time
    time.sleep(0.1)  # Pequeña pausa

    if not q_miner.empty():
        raw_msg = q_miner.get_nowait()
        received_msg = json.loads(raw_msg)
        print(f"✓ Mensaje recibido en cola del Miner: {received_msg['type']}")
        print(f"  Payload: {received_msg['payload']}")

        # Verificar contenido
        if received_msg['type'] == 'materials.requirements.v1' and received_msg['payload'] == {"stone": 10, "dirt": 5}:
            print("✓ Contenido del mensaje es correcto")
        else:
            print("✗ Contenido del mensaje incorrecto")
            return False
    else:
        print("✗ No se recibió mensaje en la cola del Miner")
        return False

    return True

def test_message_processing():
    """Prueba 5: Verificar procesamiento de mensajes en ciclo asyncio"""
    print("\n" + "=" * 60)
    print("TEST 5: Verificando procesamiento asyncio de mensajes...")
    print("=" * 60)

    import asyncio
    from multiprocessing import Queue
    from minecraft_framework.agents.miner import Miner
    import json

    # Crear colas
    q_miner = Queue()
    q_builder = Queue()
    q_explorer = Queue()

    # Crear agente
    miner = Miner("TestMiner", q_miner, q_explorer, q_miner, q_builder)

    print("\n1. Enviando comando 'set strategy' al Miner...")

    # Enviar comando de control
    control_msg = {
        "type": "control",
        "target": "MinerBot",
        "payload": {
            "cmd": "update",
            "args": {"strategy": "vertical"}
        }
    }

    q_miner.put_nowait(json.dumps(control_msg))

    async def test_perceive():
        """Función async para probar perceive"""
        # Llamar a perceive (que debería leer el mensaje)
        perception = await miner.perceive()
        return perception

    # Ejecutar la prueba
    try:
        perception = asyncio.run(test_perceive())

        print(f"✓ Perceive ejecutado correctamente")
        print(f"  Requirements: {perception.get('requirements', {})}")
        print(f"  Last control: {perception.get('lastControl', 'None')}")

        # Verificar que la estrategia se configuró
        if miner.current_strategy_name == "vertical":
            print(f"✓ Estrategia configurada correctamente: {miner.current_strategy_name}")
        else:
            print(f"✗ Estrategia NO configurada. Actual: {miner.current_strategy_name}")
            return False

        return True

    except Exception as e:
        print(f"✗ Error en test asyncio: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_cycle():
    """Prueba 6: Verificar ciclo completo perceive-decide-act"""
    print("\n" + "=" * 60)
    print("TEST 6: Verificando ciclo completo...")
    print("=" * 60)

    import asyncio
    from multiprocessing import Queue
    from minecraft_framework.agents.miner import Miner
    import json

    # Crear colas
    q_miner = Queue()
    q_builder = Queue()
    q_explorer = Queue()

    # Crear agente
    miner = Miner("TestMiner", q_miner, q_explorer, q_miner, q_builder)

    print("\n1. Configurando estrategia...")
    control_msg = {
        "type": "control",
        "target": "MinerBot",
        "payload": {
            "cmd": "update",
            "args": {"strategy": "vertical"}
        }
    }
    q_miner.put_nowait(json.dumps(control_msg))

    print("2. Configurando coordenadas de inicio...")
    start_msg = {
        "type": "control",
        "target": "MinerBot",
        "payload": {
            "cmd": "update",
            "args": {"start": {"x": 10, "z": 5, "y": 64}}
        }
    }
    q_miner.put_nowait(json.dumps(start_msg))

    async def test_full_cycle_inner():
        """Función async para probar ciclo completo"""
        # Perceive
        perception = await miner.perceive()
        print(f"✓ Perceive: strategy_setted={miner.strategy_setted}, start_executed={miner.start_executed}")

        # Decide
        decision = await miner.decide(perception)
        print(f"✓ Decide: type={decision.get('type')}, reason={decision.get('reason', 'N/A')}")

        # Verificar estado
        if miner.estadoActual.name == "RUNNING":
            print(f"✓ Estado cambió a RUNNING")
        else:
            print(f"⚠ Estado actual: {miner.estadoActual.name} (esperaba RUNNING)")

        return decision.get('type') is not None

    try:
        result = asyncio.run(test_full_cycle_inner())
        return result
    except Exception as e:
        print(f"✗ Error en ciclo completo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "PRUEBAS DEL SISTEMA DE AGENTES" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")

    results = []

    # Ejecutar pruebas
    results.append(("Imports", test_imports()))
    results.append(("Parseo de comandos", test_command_parsing()))
    results.append(("Estados de agentes", test_agent_states()))
    results.append(("Envío de mensajes", test_message_sending()))
    results.append(("Procesamiento asyncio", test_message_processing()))
    results.append(("Ciclo completo", test_full_cycle()))

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nResultado: {passed}/{total} pruebas pasadas")

    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        print("\nPara usar el sistema:")
        print("1. Inicia Minecraft con el plugin RaspberryJuice")
        print("2. Ejecuta: python main.py")
        print("3. En Minecraft, usa comandos como:")
        print("   $miner set strategy vertical")
        print("   $miner start x=10 z=5 y=64")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

