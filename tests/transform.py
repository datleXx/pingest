import pytest
from pingest.transforms.core import flatten


def test_flatten_rejects_non_container():
    with pytest.raises(TypeError, match="Top-level record must be"):
        flatten("hello")
