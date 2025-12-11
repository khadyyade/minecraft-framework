import asyncio
from multiprocessing import Queue
from minecraft_framework.agents.miner import Miner

async def main():
    q_in = Queue()
    q_explorer = Queue()
    q_miner = Queue()
    q_builder = Queue()
    miner = Miner("MinerBot", q_in, q_explorer, q_miner, q_builder)
    miner.requirements = {"stone": 200}
    await miner.iniciarAgente()

if __name__ == "__main__":
    asyncio.run(main())
