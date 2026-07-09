import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from pingest.exception_helper.core import SourceError
from pingest.logging_helper.core import get_logger

logger = get_logger(__name__)


def fetch_sequential(client: Any, tasks: list[tuple[str, dict]]) -> list[Any]:
    results = []
    for method_name, kwargs in tasks:
        result = getattr(client, method_name)(**kwargs)
        results.append(result)
    return results


def fetch_threaded(client: Any, tasks: list[tuple[str, dict]], max_workers: int = 3) -> list[Any]:
    results = [None] * len(tasks)

    def run(index: int, method_name: str, kwargs: dict):
        return index, getattr(client, method_name)(**kwargs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run, i, method, kwargs): i
            for i, (method, kwargs) in enumerate(tasks)
        }
        for future in as_completed(futures):
            try:
                index, result = future.result()
                results[index] = result
            except SourceError as e:
                i = futures[future]
                logger.error("fetch_threaded.task_failed", extra={"task_index": i, "error": str(e)})

    return results


def fetch_async(client: Any, tasks: list[tuple[str, dict]]) -> list[Any]:
    async def _run() -> list[Any]:
        async def call(method_name: str, kwargs: dict) -> Any:
            return await asyncio.to_thread(getattr(client, method_name), **kwargs)

        return list(await asyncio.gather(*[call(m, kw) for m, kw in tasks]))

    return asyncio.run(_run())
