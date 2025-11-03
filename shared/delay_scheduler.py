import threading
import heapq
import time
import logging
import traceback

logger = logging.getLogger(__name__)

class DelayScheduler:
    """
    Thread-safe, non-blocking delay scheduler for deferred task execution.
    Singleton pattern to share across modules.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cv = threading.Condition()
        self._heap = []
        self._shutdown = False
        self._thread = threading.Thread(target=self._run, daemon=True, name="DelayScheduler")
        self._thread.start()
        logger.info("DelayScheduler initialized")

    def call_later(self, delay_sec, fn, *args, **kwargs):
        """Schedule a function to be called after delay_sec seconds."""
        if self._shutdown:
            logger.warning("Scheduler is shutdown, ignoring task")
            return
        
        run_at = time.time() + float(delay_sec)
        with self._cv:
            heapq.heappush(self._heap, (run_at, fn, args, kwargs))
            self._cv.notify()

    def _run(self):
        """Main scheduler loop - runs in dedicated thread."""
        while not self._shutdown:
            with self._cv:
                while not self._heap and not self._shutdown:
                    self._cv.wait()
                
                if self._shutdown:
                    break
                
                run_at, fn, args, kwargs = self._heap[0]
                now = time.time()
                wait = run_at - now
                
                if wait > 0:
                    self._cv.wait(timeout=wait)
                    continue
                
                heapq.heappop(self._heap)
            
            # Execute outside the lock
            try:
                fn(*args, **kwargs)
            except Exception:
                logger.error("Delayed task error:\n%s", traceback.format_exc())

    def shutdown(self):
        """Gracefully shutdown the scheduler."""
        with self._cv:
            self._shutdown = True
            self._cv.notify()
        self._thread.join(timeout=5)
        logger.info("DelayScheduler shutdown complete")
