"""
ExplorerBot (Punto 4.1)

Requisitos del PDF:

    ExplorerBot surveys the surrounding terrain to identify suitable and stable regions for
construction. Using the getHeight(x, z) function, it scans defined areas and detects
zones with minimal elevation variance that can serve as foundations for BuilderBot’s
structures.
    The user initiates exploration through in-game chat commands, specifying coordinates
and optional range parameters. If new coordinates are received while exploration is active,
ExplorerBot must confirm whether to interrupt the current process or queue the new
request.
    During execution, ExplorerBot periodically publishes map.v1 mensajes containing
structured terrain data, including elevation maps, identified flat regions, and potential
obstacles. These mensajes are consumed by BuilderBot to plan construction. The bot
must respond appropriately to control commands (pause, resume, stop) to ensure explo-
ration can be safely suspended, resumed, or terminated while preserving its context.

Resumen de lo que tiene que hacer:
- Escanear el terreno usando getHeight(x, z)

- Detectar zonas planas con pocos desniveles
- Publicar map.v1 periódicamente hacia BuilderBot (Punto 5)
- Aceptar comandos: pause, resume, stop o update con nuevas coordenadas o rango

"""

import asyncio
import random
import importlib
from multiprocessing import Queue
from typing import Dict, Any, List

from minecraft_framework.baseAgent import BaseAgent, EstadoAgente

class ExplorerBot(BaseAgent):
    
    # CONSTRUCTOR
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, x: int = 0, z: int = 0, rangoScan: int = 6, tam_planicie: int = 4, mc=None):
        
        # Llamamos al constructor padre BaseAgent
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        
        # Parámetros de exploración
        self.x = x # random.randint(-1000, 1000)
        self.z = z # random.randint(-1000, 1000)
        self.rangoScan = rangoScan # Rango de los escaneos generales
        self.tamanoPlanicie = tam_planicie  # Tamaño de la planicie que neceseitamos
        self.mc = mc # Instancia del mundo
        
        # Configuración
        self.alturaMapa = 150 # Altura donde pintamos el mapa de calor
        self.tolerancia = 0
        
        # Variables internas
        self.alturasActuales = None     # Matriz mas importante que guarda las alturas del ultimo terreno explorado
        self.zonasPlanas = []
        self.contadorEscaneos = 0
        self.intentosPorPosicion = {}
        self.posicionesEscogidas = []
        self.escaneoInicial = False  # Flag para saber si ya se ha hecho el escan inicial
        self.hayArena = False  # Flag para saber si el último scan detectó arena
        self.hayArboles = False  # Flag para saber si el último scan detectó árboles
        
        # Cargar clase Exploracion usando reflection (patrón Strategy)
        self.exploracion = self.CargarClaseExploracion()

    def CargarClaseExploracion(self):
        try:
            modulo_exploracion = importlib.import_module("minecraft_framework.agents.exploracion")
            ClaseExploracion = getattr(modulo_exploracion, "Exploracion")
            return ClaseExploracion(self.mc, self.alturaMapa)
        except Exception as e:
            self.logs(f"Error al cargar clase Exploracion: {e}")
            return None

    # Metodos que implementamos desde baseAgent

    async def perceive(self) -> Dict[str, Any]:
        """FASE 1: PERCEPCIÓN
        
        Se encarga principalmente de leer mensajes externos
        Si estos mensajes contienen algo que modifique el ciclo, avisa con un mensaje interno:
            {
                "mensajes": List[dict],  # Mensajes recibidos
                "hemosHechoEscaneoInicial": bool,     # Si ya se hizo un scan
                "datosEscaneo": dict or None,  # Datos del último scan si existe
            }
        """
        # Usamos la librería time para enviar timestamps
        import time
        # Crear nuevo mensaje interno de percepción
        msgPerception = {
            "mensajes": [],
            "hemosHechoEscaneoInicial": self.escaneoInicial,
            "datosEscaneo": {
                "alturas": self.alturasActuales,
                "playerPosicion": None
            } if self.alturasActuales else None,
            "timestamp": time.time()
        }
        
        # Leer mensajes de la cola (comandos de control, updates, etc)
        msg = await self.leerMensaje() # Usamos el método del metodo padre baseAgent para leer el los mensajes que tengamos en nuestra cola
        # Si hay mensaje...
        if msg:
            msgPerception["mensajes"].append(msg) # Añadimos los mensajes recibidos al mensaje interno (no se usarán, solo los almacenamos)
            
            # Miramos de que tipo mensaje es
            # Los mensajes de control como pause, resume o stop no nos importan aquí (los gestiona baseAgent)
            # Nos fijamos si nos llega un update
            # El explorer no recibe ningún mensaje concreto del Communication Flow (el BuilderBot notifica a todos el estado global, pero eso es independiente a nosotros)

            msg_type = msg.get("type")
            
            if msg_type == "control":
                control = msg.get("payload", {})
                cmd = control.get("command")
                
                # Si es un update, resetear estado
                if cmd == "update":
                    self.logs("Hemos recibido un update, reseteamos todo")  # Entiendo que se refiere a esto cuando la teoría dice: "Agents must confirm updates via acknowledgment mensajes"
                    # Reseteamos todo
                    self.escaneoInicial = False
                    self.alturasActuales = None
                    self.zonasPlanas = []
                    msgPerception["hemosHechoEscaneoInicial"] = False
                    msgPerception["datosEscaneo"] = None
                    #############
                    # IMPORTANTE: El update puede ser que lleve nuevas coordenadas, tamaño de la planicie y rango
                    #############
        
        return msgPerception    # Enviamos el mensaje interno

    async def decide(self, msgPerception: Dict[str, Any]) -> Dict[str, Any]:
        """FASE 2: DECISIÓN
        
        Analiza la percepción y los datos del scan (si existen)
        Decide qué acción tomar, avisa con un mensaje interno:
            {
                "action": str,  ("initial_scan", "extend", "relocate", "success" o "wait")
                "params": dict,
                "reason": str
            }
        Además enviamos los mensajes pertinentes a cada buzón del resto de agentes para avisar de nuestro estado actual
        """
        from minecraft_framework.messages import crearMensajeMapV1
        
        # Creamos un nuevo mansaje interno de decisión
        msgDecision = {
            "action": "wait",
            "params": {},
            "reason": ""
        }
        
        # Variable para controlar si debemos enviar mensaje map.v1
        hayQueEnviarMapV1 = False
        datosMapV1 = None
        
        # 1) Si no se ha hecho scan inicial, lo hacemos (primer caso o update)
        if not msgPerception.get("hemosHechoEscaneoInicial"):
            msgDecision["action"] = "initial_scan"
            msgDecision["reason"] = "need_initial_scan"
            # No enviamos mensaje todavía, esperamos a tener datos del scan
            return msgDecision  # Acabamos de decidir
        
        # 2) Si ya hay scan, ANALIZAR los datos aquí en decide()
        # Además después del primer Scan enviaremos el primer mensaje MapV1 con los datos procesados
        datosEscaneo = msgPerception.get("datosEscaneo")
        if datosEscaneo and datosEscaneo.get("alturas"):
            alturas = datosEscaneo.get("alturas")
            
            # Verificar si es todo agua (en este caso la decisión será hacer un scan en nuevas posiciones aleatorioas)
            solo_agua = all(h == -1 for row in alturas for h in row) # Funcion de python que solo devuelve true si se cumple una condición en todos los casos
            if solo_agua:
                msgDecision["action"] = "relocate"
                msgDecision["reason"] = "all_water"
                # Mensaje a BuilderBot
                hayQueEnviarMapV1 = True
                datosMapV1 = {
                    "esBusquedaInicial": self.escaneoInicial,
                    "esBusquedaAmpliada": False,
                    "hayTerrenoPlano": False,
                    "esTodoAgua": True,
                    "hayArboles": False,
                    "hayArena": False,
                    "coordenadasInicioTerrenoPlano": {"x": -1, "z": -1},
                    "coordenadasFinalTerrenoPlano": {"x": -1, "z": -1},
                    "alturaPlanicie": -1
                }
            else:
                # Calcular métricas del terreno
                tam_scan = len(alturas)  # Funcion de python que devuelve la cantidad de elems que hay en una tabla (lenght())
                self.logs(f"Tamaño del escaneo: {tam_scan}x{tam_scan} y superficie buscada: {self.tamanoPlanicie}x{self.tamanoPlanicie}")
                
                # Buscar planicie existente (solo si el área es suficientemente grande)
                if tam_scan >= self.tamanoPlanicie:
                    planicie_existe, pos_planicie = self.exploracion.existe_planicie(alturas, self.tamanoPlanicie, self.tamanoPlanicie, self.tolerancia)   # Función de devuelve dos params
                    
                    if planicie_existe:
                        msgDecision["action"] = "success"
                        msgDecision["params"] = {"pos_planicie": pos_planicie}
                        msgDecision["reason"] = "PlanicieEncontrada"
                        # Preparar datos del mensaje
                        hayQueEnviarMapV1 = True
                        datosMapV1 = {
                            "esBusquedaInicial": self.contadorEscaneos == 1,
                            "esBusquedaAmpliada": False,
                            "hayTerrenoPlano": True,
                            "esTodoAgua": False,
                            "hayArboles": self.hayArboles,
                            "hayArena": self.hayArena,
                            # Importante: Lo que obtenemos en pos_planicie son coordenadas relativas a la matriz alturas
                            # Para calcular las coordenadas reales del mundo son respecto al personaje: self.x y self.z
                            "coordenadasInicioTerrenoPlano": {"x": self.x - len(alturas)//2 + pos_planicie[0], "z": self.z - len(alturas[0])//2 + pos_planicie[1]},
                            "coordenadasFinalTerrenoPlano": {"x": self.x - len(alturas)//2 + pos_planicie[0] + self.tamanoPlanicie - 1, "z": self.z - len(alturas[0])//2 + pos_planicie[1] + self.tamanoPlanicie - 1},
                            "alturaPlanicie": alturas[pos_planicie[0]][pos_planicie[1]]     # Obtenemos la altura del terreno mirando la altura que hay en las posiciones donde empieza la planicie en el mapa de alturas
                        }
                
                # Si no encontramos una planicie directamente, intentar extender
                if msgDecision["action"] != "success":
                    # Buscar si hay extensiones
                    extensiones = self.exploracion.encontrar_mejores_extensiones(alturas, self.tamanoPlanicie, self.tolerancia)
                    
                    if extensiones:
                        self.logs(f"Hemos encontrado {len(extensiones)} posibles extensiones")
                        msgDecision["action"] = "extend"
                        msgDecision["params"] = {
                            "extensiones": extensiones,
                            "datosEscaneo": datosEscaneo
                        }
                        msgDecision["reason"] = "IntentandoExtender"
                        hayQueEnviarMapV1 = True
                        datosMapV1 = {
                            "esBusquedaInicial": self.contadorEscaneos == 1,
                            "esBusquedaAmpliada": True,
                            "hayTerrenoPlano": False,
                            "esTodoAgua": False,
                            "hayArboles": self.hayArboles,
                            "hayArena": self.hayArena,
                            "coordenadasInicioTerrenoPlano": {"x": -1, "z": -1},
                            "coordenadasFinalTerrenoPlano": {"x": -1, "z": -1},
                            "alturaPlanicie": -1
                        }
                    else:
                        self.logs(f"No se puede extender")
                        msgDecision["action"] = "relocate"
                        msgDecision["reason"] = "NoSePuedeExtender"
                        hayQueEnviarMapV1 = True
                        datosMapV1 = {
                            "esBusquedaInicial": self.contadorEscaneos == 1,
                            "esBusquedaAmpliada": False,
                            "hayTerrenoPlano": False,
                            "esTodoAgua": False,
                            "hayArboles": self.hayArboles,
                            "hayArena": self.hayArena,
                            "coordenadasInicioTerrenoPlano": {"x": 0, "z": 0},
                            "coordenadasFinalTerrenoPlano": {"x": 0, "z": 0},
                            "alturaPlanicie": -1
                        }
        
        # Esto solo lo hacemos por defecto, aunque no deberíamos entrar
        if msgDecision["action"] == "wait":
            msgDecision["reason"] = "NadaQueHacer"
        
        # ENVIAR MENSAJE map.v1
        if hayQueEnviarMapV1 and datosMapV1:
            try:
                mensaje = crearMensajeMapV1(
                    agent_state=self.estadoActual.value,
                    coordenadaDeBusqueda={"x": self.x, "z": self.z},
                    rangoDeBusqueda=self.rangoScan,
                    numeroDeBusquedas=self.contadorEscaneos,
                    **datosMapV1
                )
                self.enviarMensaje("BuilderBot", mensaje)
                self.logs(f"Mensaje map.v1 enviado a BuilderBot: {msgDecision['reason']}")
                self.logs(f"{mensaje}")
            except Exception as e:
                self.logs(f"Error al enviar mensaje map.v1 {e}")
        
        return msgDecision


    async def act(self, decision: Dict[str, Any]):
        """FASE 3: ACCIÓN
        
        Ejecuta la acción que decide() nos ha dicho.
        NO analiza nada, solo ejecuta.
        Todas las acciones sobre Minecraft las hace la clase Exploracion.
        """
        action = decision.get("action")
        params = decision.get("params", {})
        reason = decision.get("reason", "")
        
        self.logs(f"Action: {action} - {reason}")
        
        if action == "initial_scan":
            # Ejecutar con la instancia que tenemos de la clase exploración
            resultado = await self.exploracion.escanear_terreno_inicial(self.x, self.z, self.rangoScan)
            # Guardar los resultados
            self.alturasActuales = resultado["alturas"]
            self.hayArena = resultado["hay_arena"]
            self.hayArboles = resultado["hay_arboles"]
            self.escaneoInicial = True
            self.contadorEscaneos += 1
            
            self.logs(f"Escaneo hecho en ({self.x}, {self.z}) Numero de escaneo: #{self.contadorEscaneos}")
            
            # Mostrar matriz por terminal (para debugear)
            if self.alturasActuales:
                self.logs("Height matrix:")
                for row in self.alturasActuales:
                    row_str = " ".join(f"{h:4}" if h != -1 else " WAT" for h in row)
                    self.logs(f"  {row_str}")
            
        elif action == "success":
            pos_planicie = params.get("pos_planicie")
            self.logs(f"SUCCESS: Planicie encontrada en {pos_planicie}")
            self.estadoActual("STOPPED")    # Paramos cuando encontremos un
            
        elif action == "extend":
            extensiones = params.get("extensiones")
            datosEscaneo = params.get("datosEscaneo")
            alturas = datosEscaneo.get("alturas") if datosEscaneo else None
            
            if alturas:
                self.logs(f"Probando {len(extensiones)} posibles extensiones")
                
                # Delegar verificación de extensiones a la clase Exploracion
                extension_exitosa = await self.exploracion.probar_extensiones(
                    self.x, self.z, self.rangoScan, extensiones, alturas, 
                    self.tamanoPlanicie, self.tolerancia
                )
                
                if extension_exitosa:
                    self.logs(f"SUCCESS: Extension valida encontrada")
                    self.estadoActual = EstadoAgente.STOPPED
                else:
                    self.logs("No hay extensiones validas, escaner aleatorio")
                    # Generar nuevas coordenadas aleatorias
                    self.x = random.randint(-1000, 1000)
                    self.z = random.randint(-1000, 1000)
                    self.posicionesEscogidas.append((self.x, self.z))
                    
                    # Delegar reubicación a la clase Exploracion
                    await self.exploracion.reubicar_aleatoriamente(self.x, self.z, self.rangoScan)
                    
                    # Resetear para hacer nuevo scan
                    self.escaneoInicial = False
                    self.alturasActuales = None
                    self.hayArena = False
                    self.hayArboles = False
            
        elif action == "relocate":
            # Generar nuevas coordenadas aleatorias
            self.x = random.randint(-1000, 1000)
            self.z = random.randint(-1000, 1000)
            
            self.logs(f"Reubicando a ({self.x}, {self.z}) - {reason}")
            self.posicionesEscogidas.append((self.x, self.z))
            
            # Delegar reubicación a la clase Exploracion
            await self.exploracion.reubicar_aleatoriamente(self.x, self.z, self.rangoScan)
            
            # Resetear para hacer nuevo scan
            self.escaneoInicial = False
            self.alturasActuales = None
            self.hayArena = False
            self.hayArboles = False
            
        elif action == "wait":
            await asyncio.sleep(1)
            
        else:
            self.logs(f"Acción desconocida: {action}")
            await asyncio.sleep(0.5)

    # ============================================================================
    # ENTRY POINT: Función de proceso
    # ============================================================================
    
    @staticmethod
    def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
        """Función de entrada que recibe todos los parametros para lanzar el porceso por separado

        Recibimos por paramtro:
            in_queue: Cola de entrada del agente
            q_explorer: Cola del ExplorerBot
            q_miner: Cola del MinerBot
            q_builder: Cola del BuilderBot
            y otros parámetros adicionales como mc_host, mc_port, x, z, range, size
        """

        mc = None
        mc_host = kwargs.get("mc_host", "localhost")
        mc_port = kwargs.get("mc_port", 4711)
        
        try:
            import sys
            import os
            # Esta es la solución que hemos conseguido para poder usar la librería MCPI
            # No hemos conseguido importarla usando reflection
            # Nos ha ayudado copilot ya que no había manera de que pudieramos llamar a la librería
            # ---------------
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            mcpi_path = os.path.join(base, "AdventuresInMinecraft-PC", "MyAdventures")
            if os.path.exists(mcpi_path):
                sys.path.insert(0, mcpi_path)
            from mcpi.minecraft import Minecraft
            # ---------------

            # Ahora creamos la instancia que está conectada al mundo
            # Nos permite ejecutar acciones sobre el mundo
            mc = Minecraft.create(mc_host, mc_port)
            print(f"El ExplorerBot se ha consguido conectar al mundo {mc_host}:{mc_port}")
        except Exception as e:
            print(f"El ExplorerBot NO se ha consguido conectar: {e}")
            return
        
        # Crear instancia del explorer
        bot = ExplorerBot(
            "ExplorerBot",
            in_queue,
            q_explorer,
            q_miner,
            q_builder,
            x=kwargs.get("x", 0),
            z=kwargs.get("z", 0),
            rangoScan=kwargs.get("range", 8),
            tam_planicie=kwargs.get("size", 4),
            mc=mc
        )
        
        # Iniciar el agente (usa el ciclo perceive-decide-act de BaseAgent)
        try:
            asyncio.run(bot.iniciarAgente())
        except KeyboardInterrupt:
            bot.logs("KeyboardInterrupt in process")
