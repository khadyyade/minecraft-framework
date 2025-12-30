"""
Clase Exploracion - Encapsula la lógica de exploración del terreno en Minecraft

Patrón de diseño aplicado: Strategy Pattern / Service Layer
Separa la lógica de interacción con el mundo de Minecraft de la lógica del agente.

Esta clase se encarga de:
- Escanear el terreno y generar mapas de alturas
- Detectar zonas planas aptas para construcción
- Visualizar mapas de calor en Minecraft
- Encontrar y verificar extensiones de terreno plano
"""

import asyncio
from typing import List, Dict, Any, Tuple
import mcpi.block as block


class Exploracion:
    """
    Servicio de exploración de terreno para Minecraft.

    Proporciona métodos para escanear, analizar y visualizar el terreno,
    buscando zonas planas óptimas para construcción.
    """

    def __init__(self, mc, altura_mapa: int = 150):
        """
        Inicializa el servicio de exploración.

        Args:
            mc: Instancia de conexión a Minecraft (mcpi.minecraft.Minecraft)
            altura_mapa: Altura (Y) donde se dibuja el mapa de calor visual (default: 150)
        """
        self.mc = mc
        self.alturaMapa = altura_mapa

    async def escanear_terreno_inicial(self, x: int, z: int, rango_scan: int) -> Dict[str, Any]:
        """
        Escanea el terreno y genera una matriz de alturas.

        Recorre el área especificada y crea un mapa de alturas 2D,
        detectando también presencia de arena y árboles.

        Args:
            x: Coordenada X central del escaneo
            z: Coordenada Z central del escaneo
            rango_scan: Radio de escaneo desde el centro

        Returns:
            Dict con:
                - alturas: Matriz 2D con las alturas del terreno (-1 para agua)
                - hay_arena: Booleano indicando si se detectó arena
                - hay_arboles: Booleano indicando si se detectaron árboles
        """
        try:
            # Mover jugador a la posición de escaneo (altura alta para ver todo)
            self.mc.player.setPos(x, 155, z)

            # Limpiar marcas visuales previas
            self.limpiarMapaCalor(x, z, rango_scan + 10)

            # Altura de referencia (centro del área)
            inicio_altura = self.mc.getHeight(x, z)

            # Variables para detectar características del terreno
            hay_arena = False
            hay_arboles = False

            # Matriz de alturas de todo el terreno
            alturas = []

            # Recorrer el terreno por filas y columnas
            for dx in range(-rango_scan, rango_scan + 1):
                row = []
                for dz in range(-rango_scan, rango_scan + 1):
                    # Obtener altura del terreno y tipo de bloque en la superficie
                    altura = self.mc.getHeight(x + dx, z + dz)
                    block_id = self.mc.getBlock(x + dx, altura - 1, z + dz)

                    # Si el bloque es agua, marcarlo especialmente
                    if block_id in [block.WATER_STATIONARY.id, block.WATER_FLOWING.id]:
                        # Marcar agua en azul oscuro (lana color 11)
                        self.mc.setBlock(x + dx, self.alturaMapa, z + dz, block.WOOL.id, 11)
                        row.append(-1)  # -1 indica agua
                    else:
                        # Detectar arena (posible desierto)
                        if not hay_arena and block_id == block.SAND.id:
                            hay_arena = True

                        # Detectar hojas (posible bosque)
                        if not hay_arboles and block_id == block.LEAVES.id:
                            hay_arboles = True

                        # Colorear según diferencia de altura respecto al centro
                        if altura == inicio_altura:
                            # Altura igual: verde (lana color 13)
                            self.mc.setBlock(x + dx, self.alturaMapa, z + dz, block.WOOL.id, 13)
                        elif abs(altura - inicio_altura) <= 2:
                            # Diferencia pequeña: naranja (lana color 1)
                            self.mc.setBlock(x + dx, self.alturaMapa, z + dz, block.WOOL.id, 1)
                        else:
                            # Gran diferencia: rojo (lana color 14)
                            self.mc.setBlock(x + dx, self.alturaMapa, z + dz, block.WOOL.id, 14)

                        row.append(altura)

                alturas.append(row)

            return {
                "alturas": alturas,
                "hay_arena": hay_arena,
                "hay_arboles": hay_arboles
            }

        except Exception as e:
            print(f"[Exploracion] Error durante el escaneo: {e}")
            return {"alturas": None, "hay_arena": False, "hay_arboles": False}


    async def reubicar_aleatoriamente(self, x_nuevo: int, z_nuevo: int, rango_scan: int):
        """
        Mueve al jugador a una nueva posición y limpia el área anterior.

        Args:
            x_nuevo: Nueva coordenada X
            z_nuevo: Nueva coordenada Z
            rango_scan: Radio del área a limpiar
        """
        # Limpiar mapa de calor en la altura visual
        self.limpiarMapaCalor(x_nuevo, z_nuevo, rango_scan + 10)

        # Mover jugador a las nuevas coordenadas (altura alta)
        self.mc.player.setPos(x_nuevo, 155, z_nuevo)
        self.mc.postToChat(f"[ExplorerBot] Explorando una nueva area...")

        await asyncio.sleep(0.5)

    async def probar_extensiones(self, x: int, z: int, rango_scan: int, extensiones: List[tuple],
                                 alturas: List[List[int]], tam_planicie: int, tolerancia: int) -> bool:
        """
        Prueba las extensiones encontradas para ver si generan una planicie válida.

        Para cada extensión, prueba múltiples offsets dentro de la secuencia
        para maximizar las posibilidades de encontrar una zona plana.

        Args:
            x, z: Coordenadas centrales
            rango_scan: Radio del área escaneada
            extensiones: Lista de tuplas (altura, dirección, coords, longitud)
            alturas: Matriz de alturas del escaneo inicial
            tam_planicie: Tamaño mínimo de planicie buscado
            tolerancia: Diferencia de altura máxima permitida

        Returns:
            True si se encontró una extensión válida, False en caso contrario
        """
        self.limpiarMapaCalor(x, z, rango_scan)

        # Probar cada extensión encontrada
        for extension in extensiones:
            altura_ref, direccion, coords, longitud = extension

            # Calcular cuántas posiciones diferentes podemos probar en esta secuencia
            num_posiciones = max(1, longitud - tam_planicie + 1)

            # Probar cada offset posible dentro de la secuencia
            for offset in range(num_posiciones):
                # Crear nueva extensión con el offset aplicado
                i, j = coords

                if direccion in ["norte", "sur"]:
                    # Para norte/sur, el offset se aplica en la columna (j)
                    coords_offset = (i, j + offset)
                else:
                    # Para este/oeste, el offset se aplica en la fila (i)
                    coords_offset = (i + offset, j)

                extension_offset = (altura_ref, direccion, coords_offset, tam_planicie)

                # Verificar si esta extensión con este offset es válida
                if self.verificar_extension(x, z, alturas, extension_offset, tam_planicie, tolerancia):
                    self.mc.postToChat(f"[ExplorerBot] Extension encontrada: {direccion} en offset {offset}")
                    return True
                else:
                    # Limpiar y probar siguiente offset
                    await asyncio.sleep(0.5)
                    self.limpiarMapaCalor(x, z, rango_scan + 4)

        # Si ninguna extensión genera un terreno plano, retornar False
        return False

    def existe_planicie(self, alturas: List[List[int]], ancho: int, alto: int,
                       tolerancia: int = 0) -> Tuple[bool, tuple]:
        """
        Busca una planicie del tamaño especificado en la matriz de alturas.

        Recorre toda la matriz buscando un área rectangular que cumpla
        con los requisitos de tamaño y planitud.

        Args:
            alturas: Matriz 2D de alturas del terreno
            ancho: Ancho mínimo de la planicie buscada
            alto: Alto mínimo de la planicie buscada
            tolerancia: Diferencia máxima de altura permitida (default: 0)

        Returns:
            Tupla (encontrado, coordenadas)
                - encontrado: True si se encontró una planicie válida
                - coordenadas: (i, j) de la esquina superior izquierda, o None
        """
        filas = len(alturas)
        cols = len(alturas[0])

        # Recorrer todas las posiciones posibles donde pueda caber la planicie
        for i in range(filas - alto + 1):
            for j in range(cols - ancho + 1):
                ref = alturas[i][j]  # Altura de referencia

                if ref == -1:  # Ignorar agua
                    continue

                plano = True
                tiene_agua = False

                # Verificar el área rectangular desde (i,j)
                for di in range(alto):
                    for dj in range(ancho):
                        val = alturas[i + di][j + dj]

                        if val == -1:
                            tiene_agua = True
                            plano = False
                            break

                        # Verificar que la altura esté dentro de la tolerancia
                        if abs(val - ref) > tolerancia:
                            plano = False
                            break

                    if not plano:
                        break

                # Si encontramos una planicie válida sin agua
                if plano and not tiene_agua:
                    return True, (i, j)

        return False, None

    def encontrar_mejores_extensiones(self, alturas: List[List[int]], tam_planicie: int = 4,
                                     tolerancia: int = 0) -> List[tuple]:
        """
        Encuentra bordes que pueden extenderse para generar una planicie.

        Analiza los cuatro bordes de la matriz de alturas buscando secuencias
        de bloques consecutivos con la misma altura que puedan ser extendidos.

        Args:
            alturas: Matriz 2D de alturas del terreno
            tam_planicie: Tamaño mínimo de planicie objetivo
            tolerancia: Diferencia de altura máxima permitida

        Returns:
            Lista de tuplas ordenadas por longitud (mayor a menor):
                (altura, dirección, coordenadas, longitud)
            Ejemplo: (5, "norte", (0, 3), 7)
        """
        filas = len(alturas)
        cols = len(alturas[0]) if alturas else 0
        extensiones_encontradas = []

        def encontrar_secuencias(linea):
            """
            Función auxiliar que busca secuencias de bloques con altura similar.

            Recorre una línea (fila o columna) y encuentra todos los segmentos
            consecutivos de bloques que tienen la misma altura (dentro de tolerancia).

            Args:
                linea: Lista de alturas

            Returns:
                Lista de tuplas (altura, índice_inicio, longitud)
            """
            secuencias = []
            actual_val, actual_idx, actual_len = None, None, 0

            for idx, val in enumerate(linea):
                # Si es agua, terminar secuencia actual
                if val == -1:
                    if actual_len >= tam_planicie:
                        secuencias.append((actual_val, actual_idx, actual_len))
                    actual_val, actual_idx, actual_len = None, None, 0
                    continue

                # Si es un nuevo valor o diferencia mayor que tolerancia
                if actual_val is None or abs(val - actual_val) > tolerancia:
                    # Guardar secuencia anterior si es válida
                    if actual_len >= tam_planicie:
                        secuencias.append((actual_val, actual_idx, actual_len))
                    # Empezar nueva secuencia
                    actual_val, actual_idx, actual_len = val, idx, 1
                else:
                    # Continuar con la secuencia actual
                    actual_len += 1

            # Guardar la última secuencia si es válida
            if actual_len >= tam_planicie:
                secuencias.append((actual_val, actual_idx, actual_len))

            return secuencias

        # Analizar los 4 bordes de la matriz

        # Norte (primera fila, índice 0)
        for altura, idx_inicio, longitud in encontrar_secuencias(alturas[0]):
            extensiones_encontradas.append((altura, "norte", (0, idx_inicio), longitud))

        # Sur (última fila)
        for altura, idx_inicio, longitud in encontrar_secuencias(alturas[-1]):
            extensiones_encontradas.append((altura, "sur", (filas-1, idx_inicio), longitud))

        # Oeste (primera columna, índice 0)
        col_oeste = [alturas[i][0] for i in range(filas)]
        for altura, idx_inicio, longitud in encontrar_secuencias(col_oeste):
            extensiones_encontradas.append((altura, "oeste", (idx_inicio, 0), longitud))

        # Este (última columna)
        col_este = [alturas[i][-1] for i in range(filas)]
        for altura, idx_inicio, longitud in encontrar_secuencias(col_este):
            extensiones_encontradas.append((altura, "este", (idx_inicio, cols-1), longitud))

        # Ordenar por longitud descendente (las más largas primero)
        return sorted(extensiones_encontradas, key=lambda x: x[3], reverse=True)

    def verificar_extension(self, x: int, z: int, alturas: List[List[int]],
                           extension_info: tuple, tam_planicie: int = 4,
                           tolerancia: int = 0) -> bool:
        """
        Verifica si una extensión es válida escaneando el terreno real.

        Comprueba cuántas filas/columnas ya existen con la altura correcta
        y luego verifica si el área de extensión necesaria cumple los requisitos.

        Args:
            x, z: Coordenadas centrales del área escaneada
            alturas: Matriz de alturas del escaneo inicial
            extension_info: Tupla (altura, dirección, coords, longitud)
            tam_planicie: Tamaño objetivo de la planicie
            tolerancia: Diferencia máxima de altura permitida

        Returns:
            True si la extensión es válida y puede generar una planicie,
            False en caso contrario
        """
        altura_ref, direccion, coords, longitud = extension_info
        filas = len(alturas)
        cols = len(alturas[0])
        i, j = coords

        # Contar cuántas filas/columnas ya existen con la altura correcta
        filas_columnas_existentes = 0

        if direccion in ["norte", "sur"]:
            if direccion == "norte":
                # Contar desde el borde norte hacia adentro
                for row_idx in range(filas):
                    fila_valida = all(
                        alturas[row_idx][j + col_offset] == altura_ref
                        for col_offset in range(min(longitud, tam_planicie))
                    )
                    if fila_valida:
                        filas_columnas_existentes += 1
                    else:
                        break
            else:  # sur
                # Contar desde el borde sur hacia adentro
                for row_idx in range(filas-1, -1, -1):
                    fila_valida = all(
                        alturas[row_idx][j + col_offset] == altura_ref
                        for col_offset in range(min(longitud, tam_planicie))
                    )
                    if fila_valida:
                        filas_columnas_existentes += 1
                    else:
                        break
        else:  # oeste o este
            if direccion == "oeste":
                # Contar desde el borde oeste hacia adentro
                for col_idx in range(cols):
                    columna_valida = all(
                        alturas[i + row_offset][col_idx] == altura_ref
                        for row_offset in range(min(longitud, tam_planicie))
                    )
                    if columna_valida:
                        filas_columnas_existentes += 1
                    else:
                        break
            else:  # este
                # Contar desde el borde este hacia adentro
                for col_idx in range(cols-1, -1, -1):
                    columna_valida = all(
                        alturas[i + row_offset][col_idx] == altura_ref
                        for row_offset in range(min(longitud, tam_planicie))
                    )
                    if columna_valida:
                        filas_columnas_existentes += 1
                    else:
                        break

        # Calcular cuánto necesitamos extender
        necesita_extender = max(0, tam_planicie - filas_columnas_existentes)

        # Si ya hay suficiente área, retornar True
        if necesita_extender == 0:
            return True

        # Obtener los bloques del área que necesita extenderse
        bloques_area = self._obtener_bloques_extension(
            x, z, filas, cols, direccion, i, j, longitud,
            necesita_extender, tam_planicie
        )

        if not bloques_area:
            return False

        # Verificar los bloques del área de extensión
        bloques_validos, bloques_agua = self._verificar_bloques_area(
            bloques_area, altura_ref, tolerancia
        )

        # Marcar visualmente las filas/columnas que ya son planas
        self.marcarBloquesQueYaSonPlanos(
            x, z, filas, cols, direccion, i, j,
            longitud, filas_columnas_existentes, tam_planicie
        )

        # Calcular cuántos bloques necesitamos que sean válidos
        bloques_necesarios = necesita_extender * min(longitud, tam_planicie)

        # La extensión es válida si hay suficientes bloques válidos y no hay agua
        return bloques_validos >= bloques_necesarios and bloques_agua == 0

    def limpiarMapaCalor(self, x: int, z: int, rango: int):
        """
        Limpia las marcas visuales de un área (mapa de calor).

        Reemplaza todos los bloques en la altura del mapa de calor con aire.

        Args:
            x, z: Coordenadas centrales del área
            rango: Radio del área a limpiar
        """
        for dx_clean in range(-rango, rango + 1):
            for dz_clean in range(-rango, rango + 1):
                self.mc.setBlock(
                    x + dx_clean, self.alturaMapa, z + dz_clean,
                    block.AIR.id
                )

    def _obtener_bloques_extension(self, x: int, z: int, filas: int, cols: int,
                                   direccion: str, i: int, j: int, longitud: int,
                                   necesita_extender: int, tam_planicie: int) -> List[Tuple[int, int, int]]:
        """
        Obtiene los bloques del área de extensión a verificar.

        Calcula las coordenadas mundiales de los bloques que están
        fuera del área escaneada inicialmente pero que necesitan
        verificarse para completar la planicie.

        Args:
            x, z: Coordenadas centrales del área escaneada
            filas, cols: Dimensiones de la matriz de alturas
            direccion: Dirección de extensión ("norte", "sur", "este", "oeste")
            i, j: Coordenadas en la matriz donde empieza la extensión
            longitud: Longitud de la secuencia plana en el borde
            necesita_extender: Número de filas/columnas adicionales necesarias
            tam_planicie: Tamaño objetivo de la planicie

        Returns:
            Lista de tuplas (x_world, z_world, altura) con las coordenadas
            y alturas de los bloques a verificar
        """
        bloques_area = []

        if direccion == "norte":
            # Extender hacia el norte (X negativa)
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 - e - 1
                    z_world = z - cols//2 + j + offset
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))

        elif direccion == "sur":
            # Extender hacia el sur (X positiva)
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 + filas + e
                    z_world = z - cols//2 + j + offset
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))

        elif direccion == "oeste":
            # Extender hacia el oeste (Z negativa)
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 + i + offset
                    z_world = z - cols//2 - e - 1
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))

        elif direccion == "este":
            # Extender hacia el este (Z positiva)
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 + i + offset
                    z_world = z - cols//2 + cols + e
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))

        return bloques_area

    def _verificar_bloques_area(self, bloques_area: List[Tuple[int, int, int]],
                                altura_ref: int, tolerancia: int) -> Tuple[int, int]:
        """
        Verifica los bloques de un área y los marca visualmente.

        Comprueba cada bloque del área para ver si cumple con los
        requisitos de altura y no es agua. Marca cada bloque con
        un color según su estado.

        Args:
            bloques_area: Lista de tuplas (x, z, altura) a verificar
            altura_ref: Altura de referencia
            tolerancia: Diferencia máxima de altura permitida

        Returns:
            Tupla (bloques_validos, bloques_agua)
                - bloques_validos: Cantidad de bloques que cumplen requisitos
                - bloques_agua: Cantidad de bloques de agua encontrados
        """
        bloques_validos = 0
        bloques_agua = 0

        for x, z, altura in bloques_area:
            block_id = self.mc.getBlock(x, altura-1, z)

            # Verificar si es agua
            if block_id in [block.WATER_STATIONARY.id, block.WATER_FLOWING.id]:
                # Marcar agua en azul oscuro (lana color 11)
                self.mc.setBlock(x, self.alturaMapa, z, block.WOOL.id, 11)
                bloques_agua += 1
            elif abs(altura - altura_ref) <= tolerancia:
                # Bloque válido: verde lima (lana color 5)
                self.mc.setBlock(x, self.alturaMapa, z, block.WOOL.id, 5)
                bloques_validos += 1
            else:
                # Bloque inválido (altura incorrecta): rojo (lana color 14)
                self.mc.setBlock(x, self.alturaMapa, z, block.WOOL.id, 14)

        return bloques_validos, bloques_agua

    def marcarBloquesQueYaSonPlanos(self, x: int, z: int, filas: int, cols: int,
                                   direccion: str, i: int, j: int, longitud: int,
                                   filas_columnas_existentes: int, tam_planicie: int):
        """
        Marca visualmente el área existente que ya cumple los requisitos.

        Colorea en verde los bloques que ya forman parte de la planicie
        encontrada en el escaneo inicial.

        Args:
            x, z: Coordenadas centrales del área
            filas, cols: Dimensiones de la matriz
            direccion: Dirección de la extensión
            i, j: Coordenadas de inicio en la matriz
            longitud: Longitud de la secuencia plana
            filas_columnas_existentes: Número de filas/columnas ya válidas
            tam_planicie: Tamaño objetivo de la planicie
        """
        if direccion == "norte":
            for row_offset in range(filas_columnas_existentes):
                for col_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + row_offset
                    z_w = z - cols//2 + j + col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, block.WOOL.id, 13)

        elif direccion == "sur":
            for row_offset in range(filas_columnas_existentes):
                for col_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + filas - 1 - row_offset
                    z_w = z - cols//2 + j + col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, block.WOOL.id, 13)

        elif direccion == "oeste":
            for col_offset in range(filas_columnas_existentes):
                for row_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + i + row_offset
                    z_w = z - cols//2 + col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, block.WOOL.id, 13)

        elif direccion == "este":
            for col_offset in range(filas_columnas_existentes):
                for row_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + i + row_offset
                    z_w = z - cols//2 + cols - 1 - col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, block.WOOL.id, 13)

