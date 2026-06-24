from datetime import datetime
import time
import functools
from contextlib import contextmanager
from collections.abc import Generator
from typing import Callable, Any
from pingest.logging_helper.core import get_logger

logger = get_logger(__name__)


def timed(func: Callable) -> Callable:
    @functools.wraps(func)
    def inner(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            t1 = time.perf_counter()
            duration_ms = (t1 - t0) * 1000
            logger.info(
                "Run completed",
                extra={"func_name": func.__name__, "duration_ms": duration_ms},
            )
        return result

    return inner


def retry(times: int = 3, backoff: float = 1.0) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{times} failed: {e}"
                    )
                    if attempt < times:
                        time.sleep(backoff * attempt)
            raise last_exc  # type: ignore[misc]

        return inner

    return decorator


@contextmanager
def timer(label: str = "block") -> Generator[None, None, None]:
    t0 = time.perf_counter()
    try:
        yield
    finally:
        t1 = time.perf_counter()
        logger.info(f"{label} completed in {t1 - t0:.3f}s")


if __name__ == "__main__":
    logger.info("Test", extra={"when": datetime.now()})
