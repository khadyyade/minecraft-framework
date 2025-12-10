import asyncio
from multiprocessing import Queue
from minecraft_framework.agents.miner import Miner

async def main():
    # Queues for agent communication
    q_in = Queue()
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()

    miner = Miner("MinerBot", q_in, q_explorer, q_miner, q_builder)

    # TEMPORARY: Fake requirements for testing (stone: 3)
    miner.requirements = {"stone": 30}

    await miner.iniciarAgente()

if __name__ == "__main__":
    asyncio.run(main())
