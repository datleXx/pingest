from typing import Any, Callable
import pytest
from pingest.transforms.core import flatten, frequency, group_by
from collections import Counter

ROWS = [
    {"dept": "eng", "sal": 100},
    {"dept": "eng", "sal": 150},
    {"dept": "hr", "sal": 90},
]


def test_flatten_rejects_non_container():
    with pytest.raises(TypeError, match="Top-level record must be"):
        flatten("hello")


@pytest.mark.parametrize(
    "rows, key, expected",
    [([], "status", Counter()), ([{"status": "open"}], "status", Counter({"open": 1}))],
)
def test_frequency(rows, key, expected):
    assert frequency(rows, key) == expected


def test_frequency_missing_key_skipped():
    rows = [{"status": "open"}, {"other": "data"}]  # second row has no "status"
    assert frequency(rows, "status") == Counter({"open": 1})
    # No KeyError, no "None" counted


def test_frequency_all_rows_missing_key():
    rows = [{"other": 1}, {"other": 2}]
    assert frequency(rows, "status") == Counter()


def test_frequency_none_is_valid_value():
    rows = [{"status": None}, {"status": None}, {"status": "open"}]
    assert frequency(rows, "status") == Counter({None: 2, "open": 1})


@pytest.mark.parametrize(
    "rows, key, agg_col, agg_fn, expected",
    [
        # No aggregation – return groups
        (
            ROWS,
            "dept",
            None,
            None,
            {
                "eng": [{"dept": "eng", "sal": 100}, {"dept": "eng", "sal": 150}],
                "hr": [{"dept": "hr", "sal": 90}],
            },
        ),
        # Sum aggregation
        (ROWS, "dept", "sal", sum, {"eng": 250, "hr": 90}),
        # Count aggregation via len – col doesn’t matter, but still required
        (ROWS, "dept", "sal", len, {"eng": 2, "hr": 1}),
        # Empty input
        ([], "dept", None, None, {}),
        ([], "dept", "sal", sum, {}),
        # Single row
        (
            [{"dept": "eng", "sal": 100}],
            "dept",
            None,
            None,
            {"eng": [{"dept": "eng", "sal": 100}]},
        ),
    ],
)
def test_group_by(
    rows: list[dict[str, Any]],
    key: str,
    agg_col: str | None,
    agg_fn: Callable | None,
    expected: dict,
) -> None:
    assert group_by(rows, key, agg_col=agg_col, agg_fn=agg_fn) == expected


def test_group_by_missing_group_key() -> None:
    rows = [{"dept": "eng"}, {"x": 1}]  # second row lacks "dept"
    with pytest.raises(KeyError):
        group_by(rows, "dept")


def test_group_by_missing_agg_col() -> None:
    rows = [{"dept": "eng", "sal": 100}, {"dept": "eng"}]  # second row lacks "sal"
    with pytest.raises(KeyError):
        group_by(rows, "dept", agg_col="sal", agg_fn=sum)
