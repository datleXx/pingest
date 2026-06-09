import logging
import time
import functools
from contextlib import contextmanager
from collections.abc import Generator
from typing import Callable, Any

logger = logging.getLogger(__name__)


def timed(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        t1 = time.perf_counter()
        duration = t1 - t0
        logger.info(f"{func.__name__} completed in {duration:.3f}s")
        return result

    return inner


def retry(times=3, backoff=1.0):
    def decorate(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, times + 1):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exc = e
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{times} failed: {e}"
                    )
                    if attempt < times:
                        time.sleep(backoff * attempt)
            if last_exc:
                raise last_exc

        return inner

    return decorate
