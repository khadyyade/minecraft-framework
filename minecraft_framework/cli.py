import asyncio
from typing import Dict, Any
from multiprocessing import Queue


def parse_command(text: str) -> Dict[str, Any]:
    """Parse simple commands and return a structured dict.

    Examples:
      - '$agent stop'
      - '$explorer start x=0 z=0'
      - '$miner start x=10 z=5 y=64'

    Command prefix is: '$'
    """
    text = text.strip()
    if not text:
        return {}

    parts = text.split()

    # --------------------------------------------------
    # Global control: \agent ...
    # --------------------------------------------------
    if parts[0] == "$agent":
        cmd = parts[1] if len(parts) > 1 else ""
        return {"type": "control", "target": "ALL", "payload": {"cmd": cmd}}

    # --------------------------------------------------
    # Explorer CLI: \explorer ...
    # --------------------------------------------------
    if parts[0] == "$explorer":
        sub = parts[1] if len(parts) > 1 else ""
        if sub == "start":
            args: Dict[str, Any] = {}
            for p in parts[2:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    args[k] = int(v)
            return {
                "type": "control",
                "target": "ExplorerBot",
                "payload": {"cmd": "update", "args": {"start": args}},
            }
        if sub == "stop":
            return {
                "type": "control",
                "target": "ExplorerBot",
                "payload": {"cmd": "stop"},
            }
        if sub == "pause":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "pause"}}
        if sub == "resume":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "resume"}}
        if sub == "status":
            return {"type": "control", "target": "ExplorerBot", "payload": {"cmd": "status"}}
        if sub == "set" and len(parts) >= 3 and parts[2] == "range":
            try:
                range_value = int(parts[3])
                return {
                    "type": "control",
                    "target": "ExplorerBot",
                    "payload": {"cmd": "update", "args": {"range": range_value}},
                }
            except (IndexError, ValueError):
                pass

    # --------------------------------------------------
    # Miner CLI: \miner ...
    # --------------------------------------------------
    if parts[0] == "$miner":
        sub = parts[1] if len(parts) > 1 else ""

        if sub == "pause":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "pause"}}

        if sub == "resume":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "resume"}}

        if sub == "stop":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "stop"}}

        if sub == "status":
            return {"type": "control", "target": "MinerBot", "payload": {"cmd": "status"}}

        if sub == "set" and len(parts) >= 4 and parts[2] == "strategy":
            strategy = parts[3]  # "vertical" | "grid" | "vein"

            args: Dict[str, Any] = {"strategy": strategy}

            # Soporte: \miner set strategy grid 4 4
            if strategy == "grid" and len(parts) >= 6:
                try:
                    args["grid_width"] = int(parts[4])
                    args["grid_length"] = int(parts[5])
                except ValueError:
                    # ignore si no son ints
                    pass
            return {
                "type": "control",
                "target": "MinerBot",
                "payload": {"cmd": "update", "args": args},
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

    # --------------------------------------------------
    # Builder CLI: \builder ...
    # --------------------------------------------------
    if parts[0] == "$builder":
        sub = parts[1] if len(parts) > 1 else ""

        # Control commands
        if sub == "pause":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "pause"}}
        if sub == "resume":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "resume"}}
        if sub == "stop":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "stop"}}
        if sub == "status":
            return {"type": "control", "target": "BuilderBot", "payload": {"cmd": "status"}}

        # Plan management: \builder plan list | \builder plan set <template>
        if sub == "plan":
            subsub = parts[2] if len(parts) > 2 else ""

            if subsub == "list":
                return {
                    "type": "control",
                    "target": "BuilderBot",
                    "payload": {"cmd": "update", "args": {"list": True}}
                }

            if subsub == "set" and len(parts) > 3:
                template_name = parts[3]
                return {
                    "type": "control",
                    "target": "BuilderBot",
                    "payload": {"cmd": "update", "args": {"plan_set": template_name}}
                }

        # Bill of Materials: \builder bom
        if sub == "bom":
            return {
                "type": "control",
                "target": "BuilderBot",
                "payload": {"cmd": "update", "args": {"bom": True}}
            }

        # Build command: \builder build
        if sub == "build":
            return {
                "type": "control",
                "target": "BuilderBot",
                "payload": {"cmd": "update", "args": {"build": True}}
            }

    # Default: plain text
    return {"type": "text", "target": "LOCAL", "payload": {"text": text}}


class ChatRouter:
    """
    ChatRouter - Single consumer of Minecraft chat events.

    Responsibilities:
    - Poll chat messages from Minecraft using mc.events.pollChatPosts()
    - Parse commands using parse_command()
    - Route messages to appropriate agent queues (q_miner, q_builder, q_explorer)
    - Handle broadcast to ALL agents when target is "ALL"

    This is the ONLY component that should call mc.events.pollChatPosts().
    Bots must NOT poll chat themselves; they only consume from their queues.
    """

    def __init__(self, mc, q_miner: Queue, q_builder: Queue, q_explorer: Queue):
        """
        Initialize the ChatRouter.

        Args:
            mc: Minecraft connection object
            q_miner: Queue for MinerBot
            q_builder: Queue for BuilderBot
            q_explorer: Queue for ExplorerBot
        """
        self.mc = mc
        self.q_miner = q_miner
        self.q_builder = q_builder
        self.q_explorer = q_explorer

        # Map target names to queues
        self.queues = {
            "MinerBot": q_miner,
            "BuilderBot": q_builder,
            "ExplorerBot": q_explorer,
        }

        self._stop_requested = False

    def route_message(self, message: Dict[str, Any]):
        """
        Route a parsed message to the appropriate queue(s).

        Args:
            message: Parsed command dictionary from parse_command()
        """
        if not isinstance(message, dict):
            return

        target = message.get("target")

        # Handle text messages (local only, don't route)
        if message.get("type") == "text":
            return

        # Broadcast to ALL queues
        if target == "ALL":
            for queue in self.queues.values():
                try:
                    queue.put_nowait(message)
                except Exception as e:
                    print(f"[ChatRouter] Error routing to queue: {e}")
        # Route to specific agent
        elif target is not None and target in self.queues:
            try:
                self.queues[target].put_nowait(message)
            except Exception as e:
                print(f"[ChatRouter] Error routing to {target}: {e}")

    async def run(self):
        """
        Main polling loop.

        Continuously polls Minecraft chat, parses commands, and routes them
        to the appropriate agent queues.
        """
        print("[ChatRouter] Started polling chat messages")

        while not self._stop_requested:
            try:
                # Poll chat posts from Minecraft (SINGLE CONSUMER)
                for post in self.mc.events.pollChatPosts():
                    text = post.message.strip()
                    print(f"[ChatRouter] Received chat: {text}")

                    # Parse the command
                    parsed = parse_command(text)

                    if parsed:
                        print(f"[ChatRouter] Parsed: {parsed}")
                        # Route to appropriate queue(s)
                        self.route_message(parsed)

                # Sleep to avoid busy-waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"[ChatRouter] Error in polling loop: {e}")
                await asyncio.sleep(0.5)

        print("[ChatRouter] Stopped")

    def stop(self):
        """Request the ChatRouter to stop."""
        self._stop_requested = True
