import asyncio
import threading
import os

from celery.signals import worker_process_init, worker_process_shutdown

from app.database.init import init_mongo, close_mongo

_worker_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_init_lock = threading.Lock()


def _run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def ensure_worker_loop_running():
    global _worker_loop, _loop_thread

    with _init_lock:
        # Already initialized for this worker process
        if _worker_loop is not None:
            return

        print(f"🚀 [Worker] PID {os.getpid()} starting async runtime...")

        # Create a dedicated asyncio event loop
        _worker_loop = asyncio.new_event_loop()

        # Run the loop in a background thread
        _loop_thread = threading.Thread(
            target=_run_loop,
            args=(_worker_loop,),
            daemon=True,
        )
        _loop_thread.start()

        # Initialize MongoDB/Beanie on this loop
        future = asyncio.run_coroutine_threadsafe(
            init_mongo(),
            _worker_loop,
        )
        future.result()

        print(f"✅ [Worker] PID {os.getpid()} runtime ready.")


def run_async(coro):
    """
    Submit an async coroutine to the worker's event loop
    and wait for the result.
    """
    ensure_worker_loop_running()

    assert _worker_loop is not None

    future = asyncio.run_coroutine_threadsafe(
        coro,
        _worker_loop,
    )

    return future.result()


@worker_process_init.connect
def _on_worker_init(**kwargs):
    ensure_worker_loop_running()


@worker_process_shutdown.connect
def _on_worker_shutdown(**kwargs):
    global _worker_loop, _loop_thread

    print(f"🛑 [Worker] PID {os.getpid()} shutting down...")

    if _worker_loop:
        try:
            future = asyncio.run_coroutine_threadsafe(
                close_mongo(),
                _worker_loop,
            )
            future.result(timeout=5)
        except Exception:
            pass

        _worker_loop.call_soon_threadsafe(_worker_loop.stop)

        if _loop_thread:
            _loop_thread.join(timeout=5)

        _worker_loop.close()

        _worker_loop = None
        _loop_thread = None

    print(f"🔌 [Worker] PID {os.getpid()} shutdown complete.")
