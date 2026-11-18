import json

import pytest

from restaurant_manager.errors import ValidationError
from restaurant_manager.main import main
from restaurant_manager.streaming import benchmark, clean, generate


def test_eager_lazy_equivalence(tmp_path):
    path = tmp_path / "rows.csv"
    generate(path, 32)
    result = benchmark(path)
    assert result[0]["orders"] == result[1]["orders"] == 8
    assert result[0]["revenue"] == result[1]["revenue"]
    assert all(r["peak_mib"] > 0 for r in result)


def test_invalid_stream_row():
    with pytest.raises(ValidationError):
        list(clean([{"order_id": None}]))


def test_cli_tolerant(csv_path, tmp_path, monkeypatch):
    config = tmp_path / "settings.yml"
    config.write_text("categories: [супи, напої]\n")
    output = tmp_path / "out.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "demo",
            "--input",
            str(csv_path),
            "--config",
            str(config),
            "--output",
            str(output),
        ],
    )
    main()
    assert len(json.loads(output.read_text())) == 2


def test_cli_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["demo", "--config", str(tmp_path / "missing")])
    with pytest.raises(SystemExit) as info:
        main()
    assert info.value.code == 1
