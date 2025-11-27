"""
Script de prueba simple para verificar la conexión con el servidor Minecraft.

Este script:
1. Se conecta al servidor de Minecraft (localhost:4711 por defecto con RaspberryJuice)
2. Envía un mensaje al chat
3. Obtiene la posición del jugador
4. Coloca un bloque de piedra cerca del jugador

Para ejecutar:
    python minecraft-framework/test_connection.py

NOTA: Asegúrate de que:
- El servidor de Minecraft esté corriendo (StartServer.bat en la carpeta Server)
- Estés conectado como jugador en el juego
- La ruta de mcpi esté en PYTHONPATH o usa el path absoluto
"""

import sys
import os

# Añadir la carpeta MyAdventures al path para importar mcpi
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AdventuresInMinecraft-PC", "MyAdventures"))

try:
    from mcpi.minecraft import Minecraft
    import mcpi.block as block
except ImportError as e:
    print(f"Error importando mcpi: {e}")
    print("Asegúrate de que la carpeta MyAdventures está en el path correcto")
    sys.exit(1)


def test_connection():
    """Prueba de conexión básica al servidor Minecraft."""
    print("Intentando conectar a localhost:4711...")
    
    try:
        # Conectar al servidor (por defecto localhost:4711)
        mc = Minecraft.create()
        print("✓ Conectado exitosamente al servidor de Minecraft!")
        
        # Enviar mensaje al chat
        mc.postToChat("¡Hola desde Python! Prueba de conexión exitosa.")
        print("✓ Mensaje enviado al chat del juego")
        
        # Obtener posición del jugador
        pos = mc.player.getTilePos()
        print(f"✓ Posición del jugador: x={pos.x}, y={pos.y}, z={pos.z}")
        
        # Colocar un bloque de piedra 3 bloques al este del jugador
        mc.setBlock(pos.x + 3, pos.y, pos.z, block.STONE.id)
        print(f"✓ Bloque de PIEDRA colocado en ({pos.x + 3}, {pos.y}, {pos.z})")
        
        # Colocar un bloque de oro 3 bloques al oeste
        mc.setBlock(pos.x - 3, pos.y, pos.z, block.GOLD_BLOCK.id)
        print(f"✓ Bloque de ORO colocado en ({pos.x - 3}, {pos.y}, {pos.z})")
        
        # Obtener altura del terreno en la posición del jugador
        height = mc.getHeight(pos.x, pos.z)
        print(f"✓ Altura del terreno en ({pos.x}, {pos.z}): {height}")
        
        print("\n¡Todas las pruebas completadas exitosamente!")
        print("Revisa el juego para ver los bloques colocados y el mensaje en el chat.")
        
    except ConnectionRefusedError:
        print("✗ Error: No se pudo conectar al servidor.")
        print("  Asegúrate de que:")
        print("  1. El servidor de Minecraft está corriendo (StartServer.bat)")
        print("  2. Estás conectado como jugador en el juego")
        print("  3. El plugin RaspberryJuice está instalado y activo")
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_connection()
