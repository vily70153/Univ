import pytest

from restaurant_orders.errors import ValidationError
from restaurant_orders.streaming import batches, generate, parse, pipeline


def test_stream_totals(tmp_path):
    path = tmp_path / "data.csv"
    generate(path, 8)
    records = list(pipeline(path))
    assert len(records) == 2
    assert records[0][1] == 221
    assert len(list(batches(records, 1))) == 2
    assert all(r[1] > 0 for r in pipeline(path, "food"))


def test_unsorted():
    row = dict(order_id="2", dish="a", category="b", price="1", quantity="1")
    with pytest.raises(ValidationError):
        list(parse([row, dict(row, order_id="1")]))


def test_bad_batch():
    with pytest.raises(ValueError):
        list(batches([], 0))
