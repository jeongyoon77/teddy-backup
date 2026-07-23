import subprocess
import threading
import queue
import time

_queue = queue.Queue()
MIN_GAP_SECONDS = 1.5


def speak(text):
    _queue.put(text)


def _worker():
    last_time = 0

    while True:
        text = _queue.get()

        now = time.time()
        wait = MIN_GAP_SECONDS - (now - last_time)

        if wait > 0:
            time.sleep(wait)

        subprocess.run(
            [
                "espeak-ng",
                "-v",
                "en",
                "-s",
                "155",
                text
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        last_time = time.time()


_worker_thread = threading.Thread(target=_worker, daemon=True)
_worker_thread.start()
