import tracemalloc
import itertools
import functools
from collections.abc import Callable, Iterable
from typing import Any, Generator

from pingest.observability import timed


def read_records(source: Iterable) -> Generator[Any, None, None]:
    """Yield one record at a time. Source is consumed exactly once"""
    for rec in source:
        yield rec


def batched(iterable: Iterable, n: int) -> Generator[list[Any], None, None]:
    """Yield a list of n at once"""
    if n <= 0:
        raise ValueError("n must be >= 0")
    source = iter(iterable)
    while True:
        chunk = list(itertools.islice(source, n))
        if chunk:
            yield chunk
        else:
            break


def filter_records(
    records: Iterable[dict], predicate: Callable
) -> Generator[dict, None, None]:
    """Filter list of dicts when predicate on record is truthy"""
    for record in records:
        if predicate(record):
            yield record


def transform_records(
    records: Iterable[dict], func: Callable
) -> Generator[Any, None, None]:
    """Applies `func` to each record and yields the result"""
    for record in records:
        yield func(record)


@timed
def run_pipeline(
    source: Iterable, stages: list[Callable[[Iterable], Iterable]]
) -> Generator[Any, None, None]:
    if not stages:
        return
    current = source
    for func in stages:
        current = func(current)

    yield from current


def giant_source(n: int) -> Generator[dict, None, None]:
    for i in range(n):
        yield {"id": i, "value": i * 2}


if __name__ == "__main__":
    test_souce = giant_source(10_000_000)

    test_pipe_transform = functools.partial(
        transform_records, func=lambda r: {**r, "square": r["value"] ** 2}
    )

    test_pipe_filter = functools.partial(
        filter_records, predicate=lambda r: r["square"] % 2 == 0
    )

    pipe_func = [read_records, test_pipe_transform, test_pipe_filter]

    tracemalloc.start()

    pipeline = run_pipeline(test_souce, pipe_func)

    for i, _ in enumerate(pipeline):
        if i % 1_000_000 == 0:
            current, peak = tracemalloc.get_traced_memory()
            print(
                f"Processed {i:>8,} records  |  current: {current / 1024:>8.1f} KiB  |  peak: {peak / 1024:>8.1f} KiB"
            )

    _, peak = tracemalloc.get_traced_memory()
    print(f"\nFinal peak: {peak / 1024 / 1024:.2f} MiB")
