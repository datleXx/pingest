import pytest
from pingest.transforms.core import flatten, frequency
from collections import Counter


def test_flatten_rejects_non_container():
    with pytest.raises(TypeError, match="Top-level record must be"):
        flatten("hello")


@pytest.mark.parametrize(
    "rows, key, expected",
    [
        ([], "status", Counter()),
        ([{"status": "open"}], "status", Counter({"open": 1})),
        (
            [{"status": "open"}, {"status": "closed"}, {"status": "open"}],
            "status",
            Counter({"open": 2, "closed": 1}),
        ),
        (
            [{"x": 1}, {"x": 2}, {"x": 1}],
            "x",
            Counter({1: 2, 2: 1}),
        ),
    ],
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
