"""
CLI esqueleto para enviar comandos a los agentes usando queues.

Este CLI está pensado para uso en el terminal local (modo desarrollo). No es
un parser completo, solo demuestra cómo traducir comandos a mensajes de control
que se colocan en las colas de `multiprocessing.Queue`.

    
    CMD /explorer start     E1[ExplorerBot: IDLE → RUNNING]
    CMD /explorer pause     E2[ExplorerBot: RUNNING → PAUSED]
    CMD /explorer resume    E3[ExplorerBot: PAUSED → RUNNING]
    CMD /explorer stop      E4[ExplorerBot: → STOPPED]
    
    CMD /miner start        M1[MinerBot: IDLE → RUNNING]
    CMD /miner set strategy M2[MinerBot: Actualiza config]
    CMD /miner pause        M3[MinerBot: RUNNING → PAUSED]
    CMD /miner fulfill      M4[MinerBot: Inicia cumplimiento BOM]
    
    CMD /builder plan set   B1[BuilderBot: Carga template]
    CMD /builder build      B2[BuilderBot: IDLE → RUNNING]
    CMD /builder pause      B3[BuilderBot: RUNNING → PAUSED]
    CMD /builder bom        B4[BuilderBot: Muestra BOM actual]
    
    CMD /workflow run       W1[Ejecuta secuencia completa]
    W1                      W2[1. ExplorerBot scan]
    W2                      W3[2. BuilderBot genera BOM]
    W3                      W4[3. MinerBot recolecta]
    W4                      W5[4. BuilderBot construye]
    
    CMD /agent status       S1[Muestra estado de todos]
    CMD /agent help         H1[Muestra ayuda]

"""

from typing import Dict, Any


def parse_command(text: str) -> Dict[str, Any]:
    """Parsea comandos simples y devuelve una estructura interpretable.

    Ejemplos:
    - '/agent stop' -> {'type': 'control', 'target': 'ALL', 'payload': {'cmd':'stop'}}
    - '/explorer start x=0 z=0 range=8'
    """
    text = text.strip()
    if not text:
        return {}

    parts = text.split()
    if parts[0] == "/agent":
        cmd = parts[1]
        return {"type": "control", "target": "ALL", "payload": {"cmd": cmd}}

    # ejemplo: /explorer start x=0 z=0
    if parts[0] == "/explorer":
        sub = parts[1]
        if sub == "start":
            args = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    args[k] = int(v)
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "update", "args": args}}
        if sub == "stop":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "stop"}}

    # TODO: parsear resto de comandos de miner/builder/workflow

    return {"type": "text", "target": "LOCAL", "payload": {"text": text}}
