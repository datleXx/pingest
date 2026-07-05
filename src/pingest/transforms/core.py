from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
from typing import Any, Callable, Dict, Iterable, Union
from math import sin, cos, radians, asin, sqrt

from pydantic_core.core_schema import float_schema

from pingest.logging_helper.core import get_logger
from pingest.models import TaxiRecord
from pingest.pipeline import batched

Record = Union[Dict[str, Any], list]

logger = get_logger(__name__)


def flatten(record: Record, iterative: bool = False, sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dict/list structure into a flat dict with dot-separated keys.

    Containers are dict and list; strings, ints, floats, bools, and None are treated
    as atomic leaves.  Lists are indexed with integer keys.

    Args:
        record: The nested structure to flatten. Must be a dict or list.
        iterative: Use an explicit stack (iterative) instead of recursion.
                   Default False (recursive).
        sep: Separator for joining path components (default ".").

    Returns:
        A flat dictionary.

    Raises:
        TypeError: If `record` is not a dict or list.

    Examples:
        >>> flatten({"a": {"b": 1, "c": [2, 3]}})
        {'a.b': 1, 'a.c.0': 2, 'a.c.1': 3}
        >>> flatten({"a": {"b": 1, "c": [2, 3]}}, iterative=True)
        {'a.b': 1, 'a.c.0': 2, 'a.c.1': 3}
    """
    if not isinstance(record, (dict, list)):
        raise TypeError(
            f"Top-level record must be either dict or list, got {type(record)}"
        )

    if iterative:
        return _flatten_recursive(record, sep)

    return _flatten_stack(record, sep)


def _flatten_recursive(
    record: Record,
    sep: str,
) -> Dict[str, Any]:
    result = {}

    def _walk(value, prefix):
        if isinstance(value, dict):
            for key, val in value.items():
                new_prefix = f"{prefix}{sep}{key}" if prefix else key
                _walk(val, new_prefix)
        elif isinstance(value, list):
            for idx, val in enumerate(value):
                new_prefix = f"{prefix}{sep}{idx}" if prefix else str(idx)
                _walk(val, new_prefix)
        else:
            result[prefix] = value

    _walk(record, "")

    return result


def _flatten_stack(record: Record, sep) -> Dict[str, Any]:
    result = {}
    stack = [(record, "")]

    while stack:
        value, prefix = stack.pop()
        if isinstance(value, dict):
            for key, val in value.items():
                new_prefix = f"{prefix}{sep}{key}" if prefix else key
                stack.append((val, new_prefix))

        elif isinstance(value, list):
            for idx, val in enumerate(value):
                new_prefix = f"{prefix}{sep}{idx}" if prefix else str(idx)
                stack.append((val, new_prefix))

        else:
            result[prefix] = value

    return result


def frequency(rows: Iterable[dict], key: str) -> Counter:
    """Return a Counter of values for the given key across all rows.

    Args:
        rows: Iterable of dictionaries.
        key: The field to count by.

    Returns:
        Counter mapping each unique value for `key` to its count.
        Rows missing the key are skipped.
    """
    result = Counter()

    for row in rows:
        if key in row:
            result[row[key]] += 1

    return result


def group_by(
    rows: Iterable[dict],
    key: str,
    agg_col: str | None = None,
    agg_fn: Callable | None = None,
) -> dict:
    groups = defaultdict(list)
    for row in rows:
        group_key = row[key]
        groups[group_key].append(row)

    if agg_col is None or agg_fn is None:
        return dict(groups)

    result = {}
    for gk, gr in groups.items():
        values = [r[agg_col] for r in gr]
        result[gk] = agg_fn(values)
    return result


def dedup(rows: Iterable[dict], key: str) -> list[dict]:
    """Return a list of rows with duplicates removed, keeping first occurrence.

    Deduplication is based on the value of ``key``.  Original order is preserved.
    Uses a ``set`` internally for O(1) look‑ups, so the memory footprint is
    proportional to the number of distinct keys.

    Args:
        rows: Iterable of dictionaries.
        key: The column whose value defines uniqueness.

    Returns:
        List of dicts in original order, without duplicates.

    Raises:
        KeyError: If any row is missing ``key``.

    Example:
        >>> rows = [{"id": 1, "x": "a"}, {"id": 2, "x": "b"}, {"id": 1, "x": "c"}]
        >>> dedup(rows, "id")
        [{'id': 1, 'x': 'a'}, {'id': 2, 'x': 'b'}]
    """
    seen = set()
    result = []
    for row in rows:
        if key not in row:
            raise KeyError(key)
        val = row[key]
        if val not in seen:
            seen.add(val)
            result.append(row)

    return result


def haversine(
    pickup_lat: float, pickup_lon: float, dropoff_lat: float, dropoff_lon: float
) -> float:
    pickup_lat_rad = radians(pickup_lat)
    pickup_lon_rad = radians(pickup_lon)
    dropoff_lat_rad = radians(dropoff_lat)
    dropoff_lon_rad = radians(dropoff_lon)

    dlat = dropoff_lat_rad - pickup_lat_rad
    dlon = dropoff_lon_rad - pickup_lon_rad

    a = (
        sin(dlat / 2) ** 2
        + cos(pickup_lat_rad) * cos(dropoff_lat_rad) * sin(dlon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))

    distance = 6371 * c

    return distance


def _haversine_batch(records: list[tuple[float, float, float, float]]) -> list[float]:
    return [haversine(*args) for args in records]


def run_haversine_parallel(records: list[TaxiRecord], max_workers: int = 5):
    start = time.perf_counter()
    extracted_records = [
        (r.pickup_lat, r.pickup_lon, r.dropoff_lat, r.dropoff_lon) for r in records
    ]
    batched_extracted_records = batched(
        extracted_records, n=int(len(records) / max_workers)
    )

    res = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_haversine_batch, batch)
            for batch in batched_extracted_records
        ]

        for future in as_completed(futures):
            res.extend(future.result())

    end = time.perf_counter()
    duration = (end - start) * 1000

    logger.info(
        "Haversine parallel done",
        extra={"duration_ms": duration, "max_workers": max_workers},
    )

    return res
