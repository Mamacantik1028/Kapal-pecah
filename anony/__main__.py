import signal
import asyncio
import importlib

from anony import app, db, logger
from anony.modules import all_modules


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        def handler(sig, frame):
            loop.call_soon_threadsafe(stop_event.set)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    await stop_event.wait()


async def anony_boot():
    try:
        await app._start()
    except Exception as ex:
        raise RuntimeError(ex)
    await db.connect()

    imported = [
        importlib.import_module(f"anony.modules.{module}")
        for module in all_modules()
    ]
    logger.info(f"Loaded {len(imported)} modules.")

    await idle()
    await app._stop()
    await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(anony_boot())
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logger.error(f"Error occurred: {ex}")
    logger.info("Stopping...")
