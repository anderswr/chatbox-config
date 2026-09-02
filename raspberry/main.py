#!/usr/bin/env python3
"""Process lifecycle for the modular Liv Realtime voice assistant."""

from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path

from raspberry.audio import DuplexAudio
from raspberry.config import Config
from raspberry.memory import MemoryStore
from raspberry.realtime_client import RealtimeClient
from raspberry.usage import UsageTracker


def configure_logging() -> None:
    log_dir = Path.home() / ".local" / "state" / "chatbox"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_dir / "chatbox.log", encoding="utf-8")],
    )


async def main() -> None:
    configure_logging()
    logging.info("Starter modulær Liv-klient med GA Realtime og lyd-diagnostikk")
    config = Config.load()
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, stop.set)

    memory = MemoryStore(config.database_path, config.memory_enabled)
    usage = UsageTracker(config.database_path)
    audio = DuplexAudio(loop, config.input_device, config.output_device)
    try:
        audio.start()
        client = RealtimeClient(config, audio, memory, usage)
        task = asyncio.create_task(client.run_forever())
        await stop.wait()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    finally:
        audio.close()
        usage.close()
        memory.close()


if __name__ == "__main__":
    asyncio.run(main())
