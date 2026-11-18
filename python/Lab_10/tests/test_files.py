import json
from decimal import Decimal

import pytest

from restaurant_orders.errors import DataError, ValidationError
from restaurant_orders.files import (
    Config,
    ImportStats,
    atomic_text,
    collect_orders,
    export_orders,
    import_rows,
    load_config,
)


def test_import_export_flow(csv_path, config, tmp_path):
    stats = ImportStats()
    orders = collect_orders(import_rows(csv_path, config, stats))
    target = tmp_path / "result.json"
    export_orders(target, orders)
    assert stats.valid == 2 and stats.invalid == 0
    assert json.loads(target.read_text())[0]["total"] == "170"


def test_tolerant_integration(csv_path, config):
    with csv_path.open("a") as stream:
        stream.write("3,no,soup,-5,0\n")
    stats = ImportStats()
    orders = collect_orders(import_rows(csv_path, config, stats, strict=False))
    assert len(orders) == 2 and stats.invalid == 1


def test_strict_preserves_output(csv_path, config, tmp_path):
    target = tmp_path / "output.json"
    target.write_text("old")
    with csv_path.open("a") as stream:
        stream.write("bad,row\n")
    with pytest.raises(DataError) as info:
        orders = collect_orders(import_rows(csv_path, config, ImportStats()))
        export_orders(target, orders)
    assert info.value.__cause__ is not None
    assert target.read_text() == "old"


def test_config(tmp_path):
    p = tmp_path / "config.yml"
    p.write_text("categories: [супи]\nmin_price: 1\nmax_price: 100\n")
    assert load_config(p).max_price == 100


@pytest.mark.parametrize(
    "raw",
    [
        "[]",
        "categories: bad",
        "categories: []",
        "categories: [a]\nmin_price: -1",
        "categories: [a]\nmax_price: NaN",
        "categories: [",
    ],
)
def test_bad_config(tmp_path, raw):
    p = tmp_path / "bad.yml"
    p.write_text(raw)
    with pytest.raises(DataError):
        load_config(p)


def test_missing_file(tmp_path, config):
    with pytest.raises(DataError):
        list(import_rows(tmp_path / "missing", config, ImportStats()))


def test_missing_header(tmp_path, config):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(DataError):
        list(import_rows(p, config, ImportStats()))


def test_disallowed_category(csv_path):
    with pytest.raises(DataError):
        list(import_rows(csv_path, Config(("other",)), ImportStats()))


def test_price_limit(csv_path):
    with pytest.raises(DataError):
        list(import_rows(csv_path, Config(max_price=Decimal(10)), ImportStats()))


def test_atomic_failure(tmp_path):
    p = tmp_path / "old.json"
    p.write_text("old")
    with pytest.raises(RuntimeError), atomic_text(p) as f:
        f.write("new")
        raise RuntimeError()
    assert p.read_text() == "old"
    assert list(tmp_path.iterdir()) == [p]


def test_io_failure(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr("restaurant_orders.files.os.replace", fail)
    with pytest.raises(DataError):
        export_orders(tmp_path / "out.json", [])
    assert not list(tmp_path.iterdir())


def test_config_missing(tmp_path):
    with pytest.raises(DataError):
        load_config(tmp_path / "none")


def test_invalid_config_category():
    with pytest.raises(ValidationError):
        Config(("",))
