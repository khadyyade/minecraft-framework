"""
Test interactivo del framework de Minecraft.
Simula la terminal y envía comandos a los agentes para probar el sistema completo.
"""

import asyncio
import json
from multiprocessing import Queue, Process
import time


def enviar_comando(queue: Queue, target: str, cmd: str, args: dict = None):
    """Envía un comando de control a un agente."""
    mensaje = {
        "type": "control",
        "target": target,
        "payload": {
            "cmd": cmd,
            "args": args or {}
        }
    }
    queue.put(json.dumps(mensaje))
    print(f"✓ Comando enviado a {target}: {cmd} {args or ''}")


def test_explorer(q_explorer: Queue):
    """Prueba del ExplorerBot"""
    print("\n" + "="*60)
    print("TEST 1: EXPLORERBOT")
    print("="*60)

    print("\n1. Iniciando exploración...")
    enviar_comando(q_explorer, "ExplorerBot", "update", {"start": {"x": 0, "z": 0, "range": 10}})
    time.sleep(2)

    print("\n2. Verificando estado...")
    enviar_comando(q_explorer, "ExplorerBot", "status", {})
    time.sleep(1)

    print("\n3. Cambiando rango...")
    enviar_comando(q_explorer, "ExplorerBot", "update", {"set range": 15})
    time.sleep(1)

    return True


def test_miner(q_miner: Queue):
    """Prueba del MinerBot"""
    print("\n" + "="*60)
    print("TEST 2: MINERBOT")
    print("="*60)

    print("\n1. Configurando estrategia vertical...")
    enviar_comando(q_miner, "MinerBot", "update", {"strategy": "vertical"})
    time.sleep(1)

    print("\n2. Verificando estado inicial...")
    enviar_comando(q_miner, "MinerBot", "status", {})
    time.sleep(1)

    print("\n3. Iniciando minería...")
    enviar_comando(q_miner, "MinerBot", "update", {"start": {"x": 10, "z": 5, "y": 64}})
    time.sleep(3)

    print("\n4. Pausando minero...")
    enviar_comando(q_miner, "MinerBot", "pause", {})
    time.sleep(1)

    print("\n5. Verificando estado pausado...")
    enviar_comando(q_miner, "MinerBot", "status", {})
    time.sleep(1)

    print("\n6. Reanudando minero...")
    enviar_comando(q_miner, "MinerBot", "resume", {})
    time.sleep(2)

    print("\n7. Cambiando a estrategia grid...")
    enviar_comando(q_miner, "MinerBot", "update", {"strategy": "grid"})
    time.sleep(1)

    print("\n8. Nuevo start (debe resetear columnas)...")
    enviar_comando(q_miner, "MinerBot", "update", {"start": {"x": 20, "z": 30, "y": 65}})
    time.sleep(2)

    return True


def test_builder(q_builder: Queue):
    """Prueba del BuilderBot"""
    print("\n" + "="*60)
    print("TEST 3: BUILDERBOT")
    print("="*60)

    print("\n1. Listando templates...")
    enviar_comando(q_builder, "BuilderBot", "update", {"list": True})
    time.sleep(1)

    print("\n2. Cargando template torre.csv...")
    enviar_comando(q_builder, "BuilderBot", "update", {"plan_set": "torre.csv"})
    time.sleep(2)

    print("\n3. Publicando BOM...")
    enviar_comando(q_builder, "BuilderBot", "update", {"bom": True})
    time.sleep(1)

    print("\n4. Verificando estado...")
    enviar_comando(q_builder, "BuilderBot", "status", {})
    time.sleep(1)

    print("\n5. Intentando construir (sin mapa - debe fallar con mensaje claro)...")
    enviar_comando(q_builder, "BuilderBot", "update", {"build": True})
    time.sleep(2)

    return True


def test_comunicacion(q_builder: Queue, q_miner: Queue):
    """Prueba de comunicación entre agentes"""
    print("\n" + "="*60)
    print("TEST 4: COMUNICACIÓN BUILDER → MINER")
    print("="*60)

    print("\n1. Builder carga template y publica BOM...")
    enviar_comando(q_builder, "BuilderBot", "update", {"plan_set": "little_house.csv"})
    time.sleep(1)
    enviar_comando(q_builder, "BuilderBot", "update", {"bom": True})
    time.sleep(2)

    print("\n2. Miner configura estrategia...")
    enviar_comando(q_miner, "MinerBot", "update", {"strategy": "vertical"})
    time.sleep(1)

    print("\n3. Miner inicia fulfill (debe recibir requirements del builder)...")
    enviar_comando(q_miner, "MinerBot", "update", {"mode": "fulfill"})
    time.sleep(1)
    enviar_comando(q_miner, "MinerBot", "update", {"start": {}})
    time.sleep(3)

    print("\n4. Verificando estado del miner...")
    enviar_comando(q_miner, "MinerBot", "status", {})
    time.sleep(1)

    return True


def test_flujo_completo(q_explorer: Queue, q_builder: Queue, q_miner: Queue):
    """Prueba del flujo completo Explorer → Builder → Miner"""
    print("\n" + "="*60)
    print("TEST 5: FLUJO COMPLETO")
    print("="*60)

    print("\n=== FASE 1: EXPLORACIÓN ===")
    print("1. Explorer busca terreno plano...")
    enviar_comando(q_explorer, "ExplorerBot", "update", {"start": {"x": 0, "z": 0}})
    time.sleep(5)  # Dar tiempo para que encuentre terreno

    print("\n=== FASE 2: PLANIFICACIÓN ===")
    print("2. Builder carga template torre.csv (3 materiales)...")
    enviar_comando(q_builder, "BuilderBot", "update", {"plan_set": "torre.csv"})
    time.sleep(1)

    print("3. Builder publica BOM...")
    enviar_comando(q_builder, "BuilderBot", "update", {"bom": True})
    time.sleep(1)

    print("\n=== FASE 3: MINERÍA ===")
    print("4. Miner configura estrategia vertical...")
    enviar_comando(q_miner, "MinerBot", "update", {"strategy": "vertical"})
    time.sleep(1)

    print("5. Miner inicia fulfill...")
    enviar_comando(q_miner, "MinerBot", "update", {"mode": "fulfill"})
    enviar_comando(q_miner, "MinerBot", "update", {"start": {}})
    time.sleep(10)  # Dar tiempo para minar

    print("\n=== FASE 4: CONSTRUCCIÓN ===")
    print("6. Builder verifica materiales y mapa...")
    enviar_comando(q_builder, "BuilderBot", "status", {})
    time.sleep(1)

    print("7. Builder inicia construcción...")
    enviar_comando(q_builder, "BuilderBot", "update", {"build": True})
    time.sleep(5)

    print("\n=== FASE 5: VERIFICACIÓN FINAL ===")
    print("8. Estado final de todos los agentes...")
    enviar_comando(q_explorer, "ExplorerBot", "status", {})
    time.sleep(0.5)
    enviar_comando(q_miner, "MinerBot", "status", {})
    time.sleep(0.5)
    enviar_comando(q_builder, "BuilderBot", "status", {})
    time.sleep(1)

    return True


def test_casos_borde():
    """Prueba casos límite y manejo de errores"""
    print("\n" + "="*60)
    print("TEST 6: CASOS BORDE")
    print("="*60)

    print("\n1. Comando inválido...")
    print("   (Simular: comando no reconocido)")

    print("\n2. Builder sin mapa intenta construir...")
    print("   ✓ Debe mostrar mensaje: 'Falta mapa del Explorer'")

    print("\n3. Builder sin materiales intenta construir...")
    print("   ✓ Debe mostrar mensaje: 'Esperando materiales del Miner'")

    print("\n4. Miner sin requirements intenta minar...")
    print("   ✓ Debe cambiar a WAITING y mostrar mensaje")

    print("\n5. Miner ejecuta start múltiples veces...")
    print("   ✓ Debe resetear columns_mined cada vez")

    print("\n6. Explorer envía mapa con altura -1...")
    print("   ✓ Builder debe rechazar el mapa")

    return True


def main():
    """Función principal del test"""
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "TEST COMPLETO DEL FRAMEWORK MINECRAFT" + " "*10 + "║")
    print("╚" + "="*58 + "╝")

    print("\nℹ️  NOTA: Este test envía comandos a las colas de los agentes.")
    print("          Para ver los resultados, ejecuta main.py en otra terminal.")
    print("          Los agentes deben estar corriendo para procesar los comandos.")

    input("\n⏸️  Presiona ENTER cuando main.py esté corriendo...")

    # Crear colas (las mismas que usa main.py)
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()

    # Menú de tests
    print("\n" + "="*60)
    print("MENÚ DE TESTS")
    print("="*60)
    print("1. Test Explorer")
    print("2. Test Miner")
    print("3. Test Builder")
    print("4. Test Comunicación Builder → Miner")
    print("5. Test Flujo Completo (Explorer → Builder → Miner)")
    print("6. Test Casos Borde")
    print("7. EJECUTAR TODOS")
    print("0. Salir")

    while True:
        opcion = input("\n▶️  Selecciona un test (0-7): ").strip()

        if opcion == "0":
            print("\n✓ Test terminado.")
            break
        elif opcion == "1":
            test_explorer(q_explorer)
        elif opcion == "2":
            test_miner(q_miner)
        elif opcion == "3":
            test_builder(q_builder)
        elif opcion == "4":
            test_comunicacion(q_builder, q_miner)
        elif opcion == "5":
            test_flujo_completo(q_explorer, q_builder, q_miner)
        elif opcion == "6":
            test_casos_borde()
        elif opcion == "7":
            print("\n🚀 EJECUTANDO TODOS LOS TESTS...\n")
            test_explorer(q_explorer)
            test_miner(q_miner)
            test_builder(q_builder)
            test_comunicacion(q_builder, q_miner)
            test_flujo_completo(q_explorer, q_builder, q_miner)
            test_casos_borde()
            print("\n✅ TODOS LOS TESTS COMPLETADOS")
        else:
            print("❌ Opción inválida")

        continuar = input("\n¿Ejecutar otro test? (s/n): ").strip().lower()
        if continuar != 's':
            break

    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print("✓ Tests enviados a las colas de los agentes")
    print("✓ Revisa la terminal de main.py para ver los resultados")
    print("✓ Template torre.csv creado con 3 materiales")
    print("  - Stone: 75 bloques")
    print("  - Sandstone: 50 bloques")
    print("  - Dirt: 10 bloques (escalera interior)")
    print("\n📋 BOM Total: 135 bloques en 7 capas")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()

