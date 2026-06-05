from collections import Counter, defaultdict
from typing import Any, Callable, Dict, Iterable, Union

Record = Union[Dict[str, Any], list]


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
