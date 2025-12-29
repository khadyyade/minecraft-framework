"""
Clase Exploracion - Encapsula la lógica de exploración del terreno en Minecraft

Patrón de diseño aplicado: Strategy Pattern / Service Layer
Separa la lógica de interacción con el mundo de Minecraft de la lógica del agente.
"""

import asyncio
from typing import List, Dict, Any, Tuple


class Exploracion:

    # Contructor    
    def __init__(self, mc, altura_mapa: int = 150):
        self.mc = mc
        self.alturaMapa = altura_mapa
        
        # Importar bloques de Minecraft
        try:
            from mcpi import block
            self.block = block
        except ImportError:
            self.block = None
    
    async def escanear_terreno_inicial(self, x: int, z: int, rango_scan: int) -> Dict[str, Any]:
        '''
        Función que escanea el terreno y genera una matriz de alturas
        '''
        try:
            # Mover jugador a la posición de escaneo
            self.mc.player.setPos(x, 155, z)
            
            # Limpiar marcas previas
            self.limpiarMapaCalor(x, z, rango_scan + 10)
            
            # Altura de referencia
            inicio_altura = self.mc.getHeight(x, z)
            
            # Variables para detectar arena y árboles
            hay_arena = False
            hay_arboles = False
            
            # Matriz de alturas de todo el terreno
            alturas = []
            # Recorrer el terreno por filas y columnas
            for dx in range(-rango_scan, rango_scan + 1):
                row = []
                for dz in range(-rango_scan, rango_scan + 1):
                    # Miramos la altura del terreno y que bloque hay en el suelo
                    altura = self.mc.getHeight(x + dx, z + dz)
                    block_id = self.mc.getBlock(x + dx, altura - 1, z + dz)
                    # Si el suelo es agua no cuenta
                    if block_id in [self.block.WATER_STATIONARY.id, self.block.WATER_FLOWING.id]:
                        self.mc.setBlock(x + dx, self.alturaMapa, z + dz, self.block.WOOL.id, 3)
                        row.append(-1)
                    else:
                        # Detectar arena o hojas
                        if not hay_arena and block_id == self.block.SAND.id:
                            hay_arena = True
                        if not hay_arboles and block_id == self.block.LEAVES.id:
                            hay_arboles = True
                        # Colocar bloques del mapa de alturas
                        if altura == inicio_altura:
                            self.mc.setBlock(x + dx, self.alturaMapa, z + dz, self.block.WOOL.id, 13)
                        elif abs(altura - inicio_altura) <= 2:
                            self.mc.setBlock(x + dx, self.alturaMapa, z + dz, self.block.WOOL.id, 1)
                        else:
                            self.mc.setBlock(x + dx, self.alturaMapa, z + dz, self.block.WOOL.id, 14)
                        row.append(altura)
                
                alturas.append(row)
            
            return {
                "alturas": alturas,
                "hay_arena": hay_arena,
                "hay_arboles": hay_arboles
            }
            
        except Exception as e:
            print(f"Error durante el escaneo: {e}")
            return {"alturas": None, "hay_arena": False, "hay_arboles": False}
        

    async def reubicar_aleatoriamente(self, x_nuevo: int, z_nuevo: int, rango_scan: int):
        """Mueve al jugador a una nueva posición y limpia el área anterior."""
        
        # Limpiar por si hay un mapa de calor en esa altura
        self.limpiarMapaCalor(x_nuevo, z_nuevo, rango_scan + 10)
        
        # Mover jugador a las nuevas coordenadas
        self.mc.player.setPos(x_nuevo, 155, z_nuevo)
        self.mc.postToChat(f"[ExplorerBot] Explorando una nueva area...")
        
        await asyncio.sleep(0.5)
    
    async def probar_extensiones(self, x: int, z: int, rango_scan: int, extensiones: List[tuple], alturas: List[List[int]], tam_planicie: int, tolerancia: int) -> bool:
        """
        De todas las extensiones encontradas posibles se revisa cuales generan una planicie.
        Para cada extensión, prueba múltiples offsets dentro de la secuencia.
        """
       
        self.limpiarMapaCalor(x, z, rango_scan)
        
        # Probar cada extensión
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
                
                if self.verificar_extension(x, z, alturas, extension_offset, tam_planicie, tolerancia):
                    self.mc.postToChat(f"[ExplorerBot] Extensión encontrada: {direccion} en offset {offset}")
                    return True
                else:
                    # Limpiar y probar siguiente offset
                    await asyncio.sleep(0.5)  # Reducido para no hacer esperar tanto
                    self.limpiarMapaCalor(x, z, rango_scan + 4)
        
        return False    # Si ninguna genera un terreno plano, false y tocará reintentar en otro sitio
    
    def existe_planicie(self, alturas: List[List[int]], ancho: int, alto: int, tolerancia: int = 0) -> Tuple[bool, tuple]:
        """
        Busca una planicie del tamaño especificado en la matriz de alturas
        """
        filas = len(alturas)
        cols = len(alturas[0])
        # Recorremos todas las posiciones posibles (solo las pos que a su alrededor pueden tener una planicie, no miramos un borde por ejemplo)
        for i in range(filas - alto + 1):
            for j in range(cols - ancho + 1):
                ref = alturas[i][j] # Tomamos el bloque de enmedio como referencia
                if ref == -1:  # Ignorar agua
                    continue

                plano = True
                tiene_agua = False
                # Bucle que mira alrededor del bloque de referencia tantos bloques de rango como la planicie que buscamos
                for di in range(alto):
                    for dj in range(ancho):
                        val = alturas[i + di][j + dj]
                        if val == -1:
                            tiene_agua = True
                            plano = False
                            break
                        if abs(val - ref) > tolerancia:
                            plano = False
                            break
                    if not plano:
                        break
                
                if plano and not tiene_agua:
                    # Solo se devuelve true en caso que una de las iteraciones no tenga ningún bloque de agua y sea totalmente plano
                    return True, (i, j)
        
        return False, None
    
    def encontrar_mejores_extensiones(self, alturas: List[List[int]], tam_planicie: int = 4, tolerancia: int = 0) -> List[tuple]:
        """
        Encuentra bordes que pueden extenderse para generar una planicie
        Devolvemos una lista de extensiones: [(altura, direccion, coords, longitud), (altura, direccion, coords, longitud), etc] 
        Ej: (5, "norte", (0, 3), 7)
        """
        filas = len(alturas)
        cols = len(alturas[0]) if alturas else 0
        extensiones_encontradas = []

        # Función privada que busca todos los bloques seguidos con la misma altura en los bordes de la matriz de alturas
        def encontrar_secuencias(linea):

            secuencias = []
            actual_val, actual_idx, actual_len = None, None, 0
            

            # El funcionamiento es simple, vamos recorriendo valor a valor de la linea que se nos ha pasado
            # Mientras el valor (altura) sea igual a la anterior, continuamos sumando longitud (cantidad de bloques planos seguidos)
            # Cada vez que nos encontramos con un bloque de agua o con uno que sea mas alto que la tolerancia (normalemente buscamos de 0) 
            # guardamos esa serie de bloques planos seguidos si es lo suficiente largo para formar una planicie en secuencias
            for idx, val in enumerate(linea):
                
                # Si es agua
                if val == -1:
                    if actual_len >= tam_planicie:
                        secuencias.append((actual_val, actual_idx, actual_len))
                    actual_val, actual_idx, actual_len = None, None, 0
                    continue
                
                # Si es nuevo valor (mas alto o mas bajo)
                if actual_val is None or abs(val - actual_val) > tolerancia:
                    # Guardar secuencia anterior si es válida
                    if actual_len >= tam_planicie:
                        secuencias.append((actual_val, actual_idx, actual_len))
                    # Empezar nueva secuencia
                    actual_val, actual_idx, actual_len = val, idx, 1

                else:
                    # Continuar con la secuencia actual
                    actual_len += 1
            
            # Al salir del bucle controlamos la ultima secuencia
            if actual_len >= tam_planicie:
                secuencias.append((actual_val, actual_idx, actual_len))
            
            return secuencias
        
        # Miramos los 4 bordes (norte, sur, este y oeste)

        # Norte (primera fila)
        for altura, idx_inicio, longitud in encontrar_secuencias(alturas[0]):
            extensiones_encontradas.append((altura, "norte", (0, idx_inicio), longitud))
        
        # Sur (última fila)
        for altura, idx_inicio, longitud in encontrar_secuencias(alturas[-1]):
            extensiones_encontradas.append((altura, "sur", (filas-1, idx_inicio), longitud))
        
        # Oeste (primera columna)
        col_oeste = [alturas[i][0] for i in range(filas)]
        for altura, idx_inicio, longitud in encontrar_secuencias(col_oeste):
            extensiones_encontradas.append((altura, "oeste", (idx_inicio, 0), longitud))
        
        # Este (última columna)
        col_este = [alturas[i][-1] for i in range(filas)]
        for altura, idx_inicio, longitud in encontrar_secuencias(col_este):
            extensiones_encontradas.append((altura, "este", (idx_inicio, cols-1), longitud))
        
        # Ordenar por longitud (mayor a menor)
        # Usamos una función lambda que solo devuelve el tercer parametro de cada tabla, la longitud, con la que ordenamos
        return sorted(extensiones_encontradas, key=lambda x: x[3], reverse=True)
    
    def verificar_extension(self, x: int, z: int, alturas: List[List[int]], extension_info: tuple, tam_planicie: int = 4, tolerancia: int = 0) -> bool:
        """
        Verifica si una extensión es válida escaneando el terreno real.
        
        Args:
            x, z: Coordenadas centrales
            alturas: Matriz de alturas del escaneo inicial
            extension_info: (altura, direccion, coords, longitud)
            tam_planicie: Tamaño objetivo
            tolerancia: Diferencia máxima permitida
            
        Returns:
            True si la extensión es válida
        """
        if not self.block:
            return False
            
        altura_ref, direccion, coords, longitud = extension_info
        filas = len(alturas)
        cols = len(alturas[0])
        i, j = coords
        
        # Contar filas/columnas existentes
        filas_columnas_existentes = 0
        
        if direccion in ["norte", "sur"]:
            if direccion == "norte":
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
                for col_idx in range(cols-1, -1, -1):
                    columna_valida = all(
                        alturas[i + row_offset][col_idx] == altura_ref
                        for row_offset in range(min(longitud, tam_planicie))
                    )
                    if columna_valida:
                        filas_columnas_existentes += 1
                    else:
                        break
        
        necesita_extender = max(0, tam_planicie - filas_columnas_existentes)
        
        # Si ya hay suficiente, marcar y retornar True
        if necesita_extender == 0:
            return True
        
        # Escanear zona de extensión
        bloques_area = self._obtener_bloques_extension(x, z, filas, cols, direccion, 
                                                        i, j, longitud, necesita_extender, 
                                                        tam_planicie)
        
        if not bloques_area:
            return False
        
        # Verificar bloques
        bloques_validos, bloques_agua = self._verificar_bloques_area(bloques_area, altura_ref, tolerancia)
        
        # Marcar filas/columnas existentes
        self.marcarBloquesQueYaSonPlanos(x, z, filas, cols, direccion, i, j, 
                                     longitud, filas_columnas_existentes, tam_planicie)
        
        bloques_necesarios = necesita_extender * min(longitud, tam_planicie)
        
        return bloques_validos >= bloques_necesarios and bloques_agua == 0
    
    def limpiarMapaCalor(self, x: int, z: int, rango: int):
        """Limpia las marcas visuales de un área."""
        if not self.block:
            return
        
        for dx_clean in range(-rango, rango + 1):
            for dz_clean in range(-rango, rango + 1):
                self.mc.setBlock(x + dx_clean, self.alturaMapa, z + dz_clean, self.block.AIR.id)
    
    def _obtener_bloques_extension(self, x: int, z: int, filas: int, cols: int, direccion: str,
                                   i: int, j: int, longitud: int, necesita_extender: int,
                                   tam_planicie: int) -> List[Tuple[int, int, int]]:
        """Obtiene los bloques del área de extensión a verificar."""
        bloques_area = []
        
        if direccion == "norte":
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 - e - 1
                    z_world = z - cols//2 + j + offset
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))
        elif direccion == "sur":
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 + filas + e
                    z_world = z - cols//2 + j + offset
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))
        elif direccion == "oeste":
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 + i + offset
                    z_world = z - cols//2 - e - 1
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))
        elif direccion == "este":
            for e in range(necesita_extender):
                for offset in range(min(longitud, tam_planicie)):
                    x_world = x - filas//2 + i + offset
                    z_world = z - cols//2 + cols + e
                    altura = self.mc.getHeight(x_world, z_world)
                    bloques_area.append((x_world, z_world, altura))
        
        return bloques_area
    
    def _verificar_bloques_area(self, bloques_area: List[Tuple[int, int, int]], 
                                altura_ref: int, tolerancia: int) -> Tuple[int, int]:
        """Verifica los bloques de un área y los marca visualmente."""
        bloques_validos = 0
        bloques_agua = 0
        
        for x, z, altura in bloques_area:
            block_id = self.mc.getBlock(x, altura-1, z)
            
            if block_id in [self.block.WATER_STATIONARY.id, self.block.WATER_FLOWING.id]:
                self.mc.setBlock(x, self.alturaMapa, z, self.block.WOOL.id, 11)
                bloques_agua += 1
            elif abs(altura - altura_ref) <= tolerancia:
                self.mc.setBlock(x, self.alturaMapa, z, self.block.WOOL.id, 5)
                bloques_validos += 1
            else:
                self.mc.setBlock(x, self.alturaMapa, z, self.block.WOOL.id, 14)
        
        return bloques_validos, bloques_agua
    
    def marcarBloquesQueYaSonPlanos(self, x: int, z: int, filas: int, cols: int, direccion: str,
                              i: int, j: int, longitud: int, filas_columnas_existentes: int,
                              tam_planicie: int):
        """Marca visualmente el área existente que ya cumple los requisitos."""
        if not self.block:
            return
        
        if direccion == "norte":
            for row_offset in range(filas_columnas_existentes):
                for col_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + row_offset
                    z_w = z - cols//2 + j + col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, self.block.WOOL.id, 13)
        elif direccion == "sur":
            for row_offset in range(filas_columnas_existentes):
                for col_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + filas - 1 - row_offset
                    z_w = z - cols//2 + j + col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, self.block.WOOL.id, 13)
        elif direccion == "oeste":
            for col_offset in range(filas_columnas_existentes):
                for row_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + i + row_offset
                    z_w = z - cols//2 + col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, self.block.WOOL.id, 13)
        elif direccion == "este":
            for col_offset in range(filas_columnas_existentes):
                for row_offset in range(min(longitud, tam_planicie)):
                    x_w = x - filas//2 + i + row_offset
                    z_w = z - cols//2 + cols - 1 - col_offset
                    self.mc.setBlock(x_w, self.alturaMapa, z_w, self.block.WOOL.id, 13)
