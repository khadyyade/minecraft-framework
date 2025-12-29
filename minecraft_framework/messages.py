"""
Mensaje JSON estandar:

{
    "type": "map.v1 o materials.requirements.v1 o inventory.v1 o build.v1",
    "source": "ExplorerBot o BuilderBot o MinerBot",
    "target": "ExplorerBot o BuilderBot o MinerBot",
    "timestamp": tiempo,
    "data": {
        // Campos específicos del tipo de mensaje
    },
    "context": {
        "state": "RUNNING o PAUSED o WAITING"
    }
}
"""

from typing import Any, Dict
import time





def crearMensaje(msg_type: str, source: str, target: str, agent_state: str, data: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "type": msg_type,
        "source": source,
        "target": target,
        "timestamp": time.time(),
        "data": data,   # Datos concretos de cada tipo de mensaje
        "context": {
            "state": agent_state
        }
    }


def crearMensajeMapV1(agent_state: str, coordenadaDeBusqueda: Dict[str, int], rangoDeBusqueda: int, esBusquedaInicial: bool, esBusquedaAmpliada: bool, hayTerrenoPlano: bool, coordenadasInicioTerrenoPlano: Dict[str, int], coordenadasFinalTerrenoPlano: Dict[str, int], numeroDeBusquedas: int, esTodoAgua: bool, hayArboles: bool, hayArena: bool, alturaPlanicie: int) -> Dict[str, Any]:

    data = {
        "coordenadaDeBusqueda": coordenadaDeBusqueda,
        "rangoDeBusqueda": rangoDeBusqueda,
        "esBusquedaInicial": esBusquedaInicial,
        "esBusquedaAmpliada": esBusquedaAmpliada,
        "hayTerrenoPlano": hayTerrenoPlano,
        "coordenadasInicioTerrenoPlano": coordenadasInicioTerrenoPlano,
        "coordenadasFinalTerrenoPlano": coordenadasFinalTerrenoPlano,
        "numeroDeBusquedas": numeroDeBusquedas,
        "esTodoAgua": esTodoAgua,
        "hayArboles": hayArboles,
        "hayArena": hayArena,
        "alturaPlanicie": alturaPlanicie
    }
    
    return crearMensaje(
        msg_type="map.v1",
        source="ExplorerBot",
        target="BuilderBot",
        agent_state=agent_state,
        data=data
    )


def crearMensajeMaterialsRequirementsV1(agent_state: str) -> Dict[str, Any]:

    data = {
        # Faltan los campos que la Khady quiere mandar
    }
    
    return crearMensaje(
        msg_type="materials.requirements.v1",
        source="BuilderBot",
        target="MinerBot",
        agent_state=agent_state,
        data=data
    )


def crearMensajeInventoryV1(agent_state: str) -> Dict[str, Any]:

    data = {
       # Faltan los campos que la Khady quiere mandar
    }
    
    return crearMensaje(
        msg_type="inventory.v1",
        source="MinerBot",
        target="BuilderBot",
        agent_state=agent_state,
        data=data
    )

def crearMensajeBuildV1(agent_state: str) -> Dict[str, Any]:

    data = {
        # Faltan los campos que la Khady quiere mandar
    }
    
    return crearMensaje(
        msg_type="build.v1",
        source="BuilderBot",
        target="MinerBot y ExplorerBot",
        agent_state=agent_state,
        data=data
    )
