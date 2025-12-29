#!/usr/bin/env python3
import asyncio
import multiprocessing as mp
from multiprocessing import Process, Queue
from typing import Optional


def _connect_minecraft(host: Optional[str] = None, port: Optional[int] = None):
    from mcpi.minecraft import Minecraft

    if host is not None and port is not None:
        return Minecraft.create(host, port)
    return Minecraft.create()


def _miner_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    from minecraft_framework.agents.miner import Miner

    bot = Miner("MinerBot", in_q, q_explorer, q_miner, q_builder)
    asyncio.run(bot.iniciarAgente())


def _explorer_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    from minecraft_framework.agents.explorer import ExplorerBot

    bot = ExplorerBot("ExplorerBot", in_q, q_explorer, q_miner, q_builder)
    asyncio.run(bot.iniciarAgente())


def _builder_process(in_q: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
    from minecraft_framework.agents.builder import BuilderBot

    bot = BuilderBot("BuilderBot", in_q, q_explorer, q_miner, q_builder)
    asyncio.run(bot.iniciarAgente())


async def async_main():
    q_miner = Queue()
    q_builder = Queue()
    q_explorer = Queue()

    procs = [
        Process(target=_miner_process, args=(q_miner, q_explorer, q_miner, q_builder), name="MinerBot"),
        Process(target=_builder_process, args=(q_builder, q_explorer, q_miner, q_builder), name="BuilderBot"),
        Process(target=_explorer_process, args=(q_explorer, q_explorer, q_miner, q_builder), name="ExplorerBot"),
    ]

    for p in procs:
        p.start()

    from minecraft_framework.cli import ChatRouter

    mc = _connect_minecraft()
    router = ChatRouter(mc, q_miner=q_miner, q_builder=q_builder, q_explorer=q_explorer)

    try:
        await router.run()
    except KeyboardInterrupt:
        pass
    finally:
        router.stop()
        for p in procs:
            if p.is_alive():
                p.terminate()
        for p in procs:
            p.join(timeout=2)


def main():
    mp.set_start_method("spawn", force=True)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
