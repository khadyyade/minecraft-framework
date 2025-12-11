from typing import Dict, Any


def parse_command(text: str) -> Dict[str, Any]:
    """Parse simple commands and return a structured dict.

    Examples:
      - '/agent stop'
      - '/explorer start x=0 z=0'
      - '/miner start x=10 z=5 y=64'
    """
    text = text.strip()
    if not text:
        return {}

    parts = text.split()

    # --------------------------------------------------
    # Global control: /agent ...
    # --------------------------------------------------
    if parts[0] == "/agent":
        cmd = parts[1]
        return {"type": "control", "target": "ALL", "payload": {"cmd": cmd}}

    # --------------------------------------------------
    # Explorer CLI example (ya lo tenías)
    # --------------------------------------------------
    if parts[0] == "\explorer":
        sub = parts[1]
        if sub == "start":
            args: Dict[str, Any] = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    args[k] = int(v)
            return {
                "type": "control",
                "target": "ExplorerBot",
                "payload": {"cmd": "update", "args": args},
            }
        if sub == "stop":
            return {
                "type": "control",
                "target": "ExplorerBot",
                "payload": {"cmd": "stop"},
            }

    # --------------------------------------------------
    # Miner CLI: /miner ...
    # --------------------------------------------------
    if parts[0] == "\miner":
        sub = parts[1]

        if sub == "pause":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "pause"}}

        if sub == "resume":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "resume"}}

        if sub == "status":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "status"}}

        if sub == "set" and len(parts) >= 4 and parts[2] == "strategy":
            strategy = parts[3]  # "vertical" | "grid" | "vein"
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": {"strategy": strategy}},
            }

        if sub == "start":
            args = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    args[k] = int(v)
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": {"start": args}},
            }

        if sub == "fulfill":
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": {"mode": "fulfill"}},
            }

        # Unknown subcommand
        return {
            "type": "text",
            "target": "LOCAL",
            "payload": {"text": text},
        }

    # Default: plain text
    return {"type": "text", "target": "LOCAL", "payload": {"text": text}}
