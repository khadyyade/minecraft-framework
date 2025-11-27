"""
Paquete de agentes: ExplorerBot, MinerBot, BuilderBot.

Cada agente expone una función `agent_process_main(queue_in, out_queues, **kwargs)`
que puede ser pasada a `multiprocessing.Process` como target.
"""

__all__ = ["explorer", "miner", "builder"]
