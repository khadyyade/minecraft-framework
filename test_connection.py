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

import time
import sys
import os
import random

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
    print("Intentando conectar a localhost:4711...")
    
    try:
        mc = Minecraft.create()
        print("✓ Conectado exitosamente al servidor de Minecraft!")
        mc.postToChat("Hola desde Python! Prueba de conexion exitosa.")

        import random
        rand_x =  random.randint(-1000, 1000)
        rand_z =  random.randint(-1000, 1000)
        # 799
        # -313
        
        # -786
        # -297
        mc.player.setPos(rand_x, 155, rand_z)
        scan_range = 6
        heights = []
        mc.postToChat("/time set day")

        player_pos = mc.player.getTilePos()  # Guardamos la posición del jugador
        
        # Limpiar bloques de altura 150 en el área de escaneo antes de empezar
        for dx_clean in range(-scan_range - 10, scan_range + 11):
            for dz_clean in range(-scan_range - 10, scan_range + 11):
                mc.setBlock(player_pos.x + dx_clean, 150, player_pos.z + dz_clean, block.AIR.id)
        
        inicio = mc.getHeight(player_pos.x, player_pos.z)

        solo_agua = True

        dx = -scan_range
        while dx <= scan_range:
            row = []
            dz = -scan_range
            while dz <= scan_range:
                altura = mc.getHeight(player_pos.x + dx, player_pos.z + dz)
                block_id = mc.getBlock(player_pos.x + dx, altura-1, player_pos.z + dz)

                if block_id == block.WATER_STATIONARY.id or block_id == block.WATER_FLOWING.id:
                    mc.setBlock(player_pos.x + dx, 150, player_pos.z + dz, block.WOOL.id, 3)
                    row.append(-1)
                elif altura == inicio:
                    mc.setBlock(player_pos.x + dx, 150, player_pos.z + dz, block.WOOL.id, 13)
                    row.append(altura)
                    solo_agua = False
                elif (altura+1 == inicio or altura-1 == inicio or altura+2 == inicio or altura-2 == inicio):
                    mc.setBlock(player_pos.x + dx, 150, player_pos.z + dz, block.WOOL.id, 1)
                    row.append(altura)
                    solo_agua = False
                else:
                    mc.setBlock(player_pos.x + dx, 150, player_pos.z + dz, block.WOOL.id, 14)
                    row.append(altura)
                    solo_agua = False
                dz += 1
            heights.append(row)
            dx += 1

        mc.player.setPos(rand_x, 155, rand_z)
        time.sleep(5)
        # Mostrar la matriz de alturas
        print("\n=== Matriz de alturas ===")
        for fila in heights:
            print(" ".join(f"{h:4}" if h != -1 else "  -1" for h in fila))
        print("========================\n")

        if solo_agua:
            print("Todo el área es agua, cambiando de sitio...")
        else:
            plano, pos_planicie = existe_planicie(heights, scan_range, 4, 4, tolerancia=0)
            if plano:
                print(f"Encontrada planicie en {pos_planicie}")
                print("Ya hay una planicie del tamaño deseado, no hace falta extender")
            else:
                print("No hay planicie del tamaño buscado")
                # Solo intentar extender si NO encontramos planicie
                porc = porcentaje_plano(heights, tolerancia=2)
                print(f"El terreno es plano en un {porc:.2f}%")

                if porc > 80:
                    print("Terreno bastante plano, buscando mejor extensión...")
                    
                    # Limpiar bloques de lana en altura 150 para evitar problemas con getHeight
                    for dx_clean in range(-scan_range, scan_range + 1):
                        for dz_clean in range(-scan_range, scan_range + 1):
                            mc.setBlock(player_pos.x + dx_clean, 150, player_pos.z + dz_clean, block.AIR.id)
                    
                    resultado = mejor_extension_planicie(mc, player_pos, heights, tam_planicie=4, tolerancia=0)
                    if resultado:
                        # Probar cada extensión hasta encontrar una válida
                        extension_exitosa = False
                        for extension in resultado:
                            print(f"\nProbando extensión hacia {extension[1]}...")
                            if verificar_extension(mc, player_pos, heights, extension, tam_planicie=4, tolerancia=0, scan_range=scan_range):
                                extension_exitosa = True
                                break
                            else:
                                # Limpiar bloques marcados y probar siguiente extensión
                                print("Limpiando bloques marcados...")
                                time.sleep(3)
                                for dx_clean in range(-scan_range-4, scan_range + 5):
                                    for dz_clean in range(-scan_range-4, scan_range + 5):
                                        mc.setBlock(player_pos.x + dx_clean, 150, player_pos.z + dz_clean, block.AIR.id)
                        
                        if not extension_exitosa:
                            print("\nNo se encontró ninguna extensión válida")
                elif porc > 50:
                    print("Terreno mixto, con desniveles")
                else:
                    print("Terreno muy irregular (montaña o socavón)")

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


def existe_planicie(heights, scan_range, ancho, alto, tolerancia=0):
    """
    heights: matriz 2D con las alturas
    scan_range: radio del escaneo (matriz tiene tamaño (2*scan_range+1)^2)
    ancho: tamaño en X del subrecuadro a comprobar
    alto: tamaño en Y del subrecuadro a comprobar
    tolerancia: diferencia máxima permitida entre alturas (0 = plano exacto)
    """
    filas = len(heights)
    cols = len(heights[0]) if heights else 0
    
    # Recorremos todas las posibles posiciones de inicio del subrecuadro
    for i in range(filas - alto + 1):
        for j in range(cols - ancho + 1):
            # Tomamos la altura de referencia (ignoramos agua)
            ref = heights[i][j]
            if ref == -1:  # Si la primera celda es agua, no es válido
                continue
                
            plano = True
            tiene_agua = False

            # Recorremos el subrecuadro
            for di in range(alto):
                for dj in range(ancho):
                    val = heights[i + di][j + dj]
                    if val == -1:  # Si hay agua en el subrecuadro, no es válido
                        tiene_agua = True
                        plano = False
                        break
                    if abs(val - ref) > tolerancia:
                        plano = False
                        break
                if not plano:
                    break

            if plano and not tiene_agua:
                return True, (i, j)  # Encontramos una planicie en (i,j)

    return False, None

def porcentaje_plano(heights, tolerancia=1):
    """
    Calcula el porcentaje de bloques 'planos' en la matriz heights.
    Un bloque se considera plano si la diferencia con sus vecinos
    inmediatos (arriba, abajo, izquierda, derecha) no supera la tolerancia.

    heights: matriz 2D de alturas
    tolerancia: diferencia máxima permitida
    """
    filas = len(heights)
    cols = len(heights[0])
    total = 0
    planos = 0

    for i in range(filas):
        for j in range(cols):
            if heights[i][j] == -1:  # ignoramos agua
                continue
            total += 1
            plano = True
            # vecinos inmediatos
            for di, dj in [(1,0), (-1,0), (0,1), (0,-1)]:
                ni, nj = i+di, j+dj
                if 0 <= ni < filas and 0 <= nj < cols and heights[ni][nj] != -1:
                    if abs(heights[i][j] - heights[ni][nj]) > tolerancia:
                        plano = False
                        break
            if plano:
                planos += 1

    if total == 0:
        return 0.0
    return (planos / total) * 100

def mejor_extension_planicie(mc, pos, heights, tam_planicie=4, tolerancia=0):
    filas = len(heights)
    cols = len(heights[0])
    extensiones_encontradas = []

    def encontrar_secuencias(linea):
        """Encuentra todas las secuencias de bloques válidos (>= tam_planicie)"""
        secuencias = []  # [(altura, idx_inicio, longitud)]
        actual_val, actual_idx, actual_len = None, None, 0
        
        for idx, val in enumerate(linea):
            if val == -1:  # ignoramos agua
                if actual_len >= tam_planicie:
                    secuencias.append((actual_val, actual_idx, actual_len))
                actual_val, actual_idx, actual_len = None, None, 0
                continue
            
            if actual_val is None or abs(val - actual_val) > tolerancia:
                # Nueva secuencia
                if actual_len >= tam_planicie:
                    secuencias.append((actual_val, actual_idx, actual_len))
                actual_val, actual_idx, actual_len = val, idx, 1
            else:
                # Continuar secuencia
                actual_len += 1
        
        # No olvidar la última secuencia
        if actual_len >= tam_planicie:
            secuencias.append((actual_val, actual_idx, actual_len))
        
        return secuencias

    # Norte (fila 0)
    secuencias_norte = encontrar_secuencias(heights[0])
    for altura, idx_inicio, longitud in secuencias_norte:
        extensiones_encontradas.append((altura, "norte", (0, idx_inicio), longitud))
        print(f"  Norte: altura {altura}, desde índice {idx_inicio}, longitud {longitud}")

    # Sur (última fila)
    secuencias_sur = encontrar_secuencias(heights[-1])
    for altura, idx_inicio, longitud in secuencias_sur:
        extensiones_encontradas.append((altura, "sur", (filas-1, idx_inicio), longitud))
        print(f"  Sur: altura {altura}, desde índice {idx_inicio}, longitud {longitud}")

    # Oeste (columna 0)
    col_oeste = [heights[i][0] for i in range(filas)]
    secuencias_oeste = encontrar_secuencias(col_oeste)
    for altura, idx_inicio, longitud in secuencias_oeste:
        extensiones_encontradas.append((altura, "oeste", (idx_inicio, 0), longitud))
        print(f"  Oeste: altura {altura}, desde índice {idx_inicio}, longitud {longitud}")

    # Este (última columna)
    col_este = [heights[i][-1] for i in range(filas)]
    secuencias_este = encontrar_secuencias(col_este)
    for altura, idx_inicio, longitud in secuencias_este:
        extensiones_encontradas.append((altura, "este", (idx_inicio, cols-1), longitud))
        print(f"  Este: altura {altura}, desde índice {idx_inicio}, longitud {longitud}")

    if not extensiones_encontradas:
        print("No hay bordes válidos para extender planicie (mínimo {} bloques consecutivos)".format(tam_planicie))
        return []

    # Ordenar extensiones por longitud (de mayor a menor)
    extensiones_ordenadas = sorted(extensiones_encontradas, key=lambda x: x[3], reverse=True)
    
    print(f"\nSe encontraron {len(extensiones_ordenadas)} extensiones válidas")
    for altura, direccion, coords, longitud in extensiones_ordenadas:
        print(f"  - {direccion}: altura {altura}, longitud {longitud}")

    return extensiones_ordenadas


def verificar_extension(mc, pos, heights, extension_info, tam_planicie=4, tolerancia=0, scan_range=6):
    """
    Verifica si en la zona de extensión (incluyendo el borde existente) se puede formar 
    realmente una planicie del tamaño deseado.
    Analiza cuántas filas/columnas consecutivas ya tenemos en el borde y solo extiende lo necesario.
    
    extension_info: tupla (altura, direccion, coords, longitud) devuelta por mejor_extension_planicie
    """
    altura_ref, direccion, coords, longitud = extension_info
    filas = len(heights)
    cols = len(heights[0])
    i, j = coords
    
    print(f"\n=== Verificando extensión hacia {direccion} ===")
    print(f"Altura de referencia: {altura_ref}")
    
    # Primero, determinar cuántas filas/columnas consecutivas ya tenemos en el borde a la misma altura
    filas_columnas_existentes = 0
    
    if direccion == "norte" or direccion == "sur":
        # Contar filas consecutivas desde el borde
        if direccion == "norte":
            # Empezar desde fila 0 hacia el interior
            for row_idx in range(filas):
                fila_valida = True
                for col_offset in range(min(longitud, tam_planicie)):
                    if heights[row_idx][j + col_offset] != altura_ref:
                        fila_valida = False
                        break
                if fila_valida:
                    filas_columnas_existentes += 1
                else:
                    break
        else:  # sur
            # Empezar desde última fila hacia el interior
            for row_idx in range(filas-1, -1, -1):
                fila_valida = True
                for col_offset in range(min(longitud, tam_planicie)):
                    if heights[row_idx][j + col_offset] != altura_ref:
                        fila_valida = False
                        break
                if fila_valida:
                    filas_columnas_existentes += 1
                else:
                    break
    else:  # oeste o este
        # Contar columnas consecutivas desde el borde
        if direccion == "oeste":
            # Empezar desde columna 0 hacia el interior
            for col_idx in range(cols):
                columna_valida = True
                for row_offset in range(min(longitud, tam_planicie)):
                    if heights[i + row_offset][col_idx] != altura_ref:
                        columna_valida = False
                        break
                if columna_valida:
                    filas_columnas_existentes += 1
                else:
                    break
        else:  # este
            # Empezar desde última columna hacia el interior
            for col_idx in range(cols-1, -1, -1):
                columna_valida = True
                for row_offset in range(min(longitud, tam_planicie)):
                    if heights[i + row_offset][col_idx] != altura_ref:
                        columna_valida = False
                        break
                if columna_valida:
                    filas_columnas_existentes += 1
                else:
                    break
    
    print(f"Filas/columnas ya existentes en el borde: {filas_columnas_existentes}")
    
    # Calcular cuánto necesitamos extender
    necesita_extender = max(0, tam_planicie - filas_columnas_existentes)
    print(f"Necesita extender: {necesita_extender} filas/columnas")
    
    if necesita_extender == 0:
        print("✓ Ya hay suficientes filas/columnas en el borde para formar la planicie")
        # Marcar la zona válida
        if direccion == "norte" or direccion == "sur":
            for row_offset in range(tam_planicie):
                for col_offset in range(min(longitud, tam_planicie)):
                    if direccion == "norte":
                        x_w = pos.x - filas//2 + row_offset
                        z_w = pos.z - cols//2 + j + col_offset
                    else:
                        x_w = pos.x - filas//2 + filas - tam_planicie + row_offset
                        z_w = pos.z - cols//2 + j + col_offset
                    mc.setBlock(x_w, 150, z_w, block.WOOL.id, 5)
        else:
            for row_offset in range(min(longitud, tam_planicie)):
                for col_offset in range(tam_planicie):
                    if direccion == "oeste":
                        x_w = pos.x - filas//2 + i + row_offset
                        z_w = pos.z - cols//2 + col_offset
                    else:
                        x_w = pos.x - filas//2 + i + row_offset
                        z_w = pos.z - cols//2 + cols - tam_planicie + col_offset
                    mc.setBlock(x_w, 150, z_w, block.WOOL.id, 5)
        return True
    
    # Escanear zona de extensión
    bloques_area = []
    
    if direccion == "norte":
        # Ya tenemos filas_columnas_existentes, extendemos necesita_extender más
        for e in range(necesita_extender):
            for offset in range(min(longitud, tam_planicie)):
                x_world = pos.x - filas//2 - e - 1
                z_world = pos.z - cols//2 + j + offset
                altura = mc.getHeight(x_world, z_world)
                bloques_area.append((x_world, z_world, altura))
                
    elif direccion == "sur":
        for e in range(necesita_extender):
            for offset in range(min(longitud, tam_planicie)):
                x_world = pos.x - filas//2 + filas + e
                z_world = pos.z - cols//2 + j + offset
                altura = mc.getHeight(x_world, z_world)
                bloques_area.append((x_world, z_world, altura))
                
    elif direccion == "oeste":
        for e in range(necesita_extender):
            for offset in range(min(longitud, tam_planicie)):
                x_world = pos.x - filas//2 + i + offset
                z_world = pos.z - cols//2 - e - 1
                altura = mc.getHeight(x_world, z_world)
                bloques_area.append((x_world, z_world, altura))
                
    elif direccion == "este":
        for e in range(necesita_extender):
            for offset in range(min(longitud, tam_planicie)):
                x_world = pos.x - filas//2 + i + offset
                z_world = pos.z - cols//2 + cols + e
                altura = mc.getHeight(x_world, z_world)
                bloques_area.append((x_world, z_world, altura))
    
    if not bloques_area:
        print("✗ No se encontraron bloques para verificar")
        return False
    
    bloques_agua = 0
    bloques_validos = 0
    bloques_invalidos = 0
    
    for x, z, altura in bloques_area:
        block_id = mc.getBlock(x, altura-1, z)
        
        if block_id == block.WATER_STATIONARY.id or block_id == block.WATER_FLOWING.id:
            mc.setBlock(x, 150, z, block.WOOL.id, 11)  # lana azul (agua)
            bloques_agua += 1
        elif abs(altura - altura_ref) <= tolerancia:
            mc.setBlock(x, 150, z, block.WOOL.id, 5)  # lana verde lima (válido)
            bloques_validos += 1
        else:
            mc.setBlock(x, 150, z, block.WOOL.id, 14)  # lana roja (desnivel)
            bloques_invalidos += 1
    
    # También marcar las filas/columnas existentes
    if direccion == "norte":
        for row_offset in range(filas_columnas_existentes):
            for col_offset in range(min(longitud, tam_planicie)):
                x_w = pos.x - filas//2 + row_offset
                z_w = pos.z - cols//2 + j + col_offset
                mc.setBlock(x_w, 150, z_w, block.WOOL.id, 13)  # lana verde (borde existente)
    elif direccion == "sur":
        for row_offset in range(filas_columnas_existentes):
            for col_offset in range(min(longitud, tam_planicie)):
                x_w = pos.x - filas//2 + filas - 1 - row_offset
                z_w = pos.z - cols//2 + j + col_offset
                mc.setBlock(x_w, 150, z_w, block.WOOL.id, 13)
    elif direccion == "oeste":
        for col_offset in range(filas_columnas_existentes):
            for row_offset in range(min(longitud, tam_planicie)):
                x_w = pos.x - filas//2 + i + row_offset
                z_w = pos.z - cols//2 + col_offset
                mc.setBlock(x_w, 150, z_w, block.WOOL.id, 13)
    elif direccion == "este":
        for col_offset in range(filas_columnas_existentes):
            for row_offset in range(min(longitud, tam_planicie)):
                x_w = pos.x - filas//2 + i + row_offset
                z_w = pos.z - cols//2 + cols - 1 - col_offset
                mc.setBlock(x_w, 150, z_w, block.WOOL.id, 13)
    
    bloques_necesarios_extension = necesita_extender * min(longitud, tam_planicie)
    
    print(f"Bloques escaneados en extensión: {len(bloques_area)}")
    print(f"Bloques válidos: {bloques_validos}")
    print(f"Bloques inválidos: {bloques_invalidos}")
    print(f"Bloques de agua: {bloques_agua}")
    print(f"Bloques necesarios en extensión: {bloques_necesarios_extension}")
    
    if bloques_validos >= bloques_necesarios_extension and bloques_agua == 0:
        print(f"✓ SE PUEDE FORMAR UNA PLANICIE {tam_planicie}x{tam_planicie}")
        return True
    else:
        print(f"✗ NO se puede formar una planicie {tam_planicie}x{tam_planicie}")
        if bloques_agua > 0:
            print(f"  Razón: Hay {bloques_agua} bloques de agua")
        if bloques_validos < bloques_necesarios_extension:
            print(f"  Razón: Solo {bloques_validos}/{bloques_necesarios_extension} bloques son válidos en la extensión")
        return False


if __name__ == "__main__":
    test_connection()
