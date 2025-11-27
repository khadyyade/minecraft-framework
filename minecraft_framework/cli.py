"""
CLI esqueleto para enviar comandos a los agentes usando queues.

Este CLI está pensado para uso en el terminal local (modo desarrollo). No es
un parser completo, solo demuestra cómo traducir comandos a mensajes de control
que se colocan en las colas de `multiprocessing.Queue`.
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
