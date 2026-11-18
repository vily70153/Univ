import csv
import json
import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import IO

import yaml

from restaurant_orders.errors import DataError, ValidationError
from restaurant_orders.models import Dish, Order, OrderItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    categories: tuple[str, ...] = ("супи", "напої", "десерти")
    min_price: Decimal = Decimal("0.01")
    max_price: Decimal = Decimal(10000)

    def __post_init__(self) -> None:
        if not self.categories or any(
            not isinstance(c, str) or not c.strip() for c in self.categories
        ):
            raise ValidationError("invalid categories")
        if (
            not self.min_price.is_finite()
            or not self.max_price.is_finite()
            or not 0 < self.min_price <= self.max_price
        ):
            raise ValidationError("invalid price range")


@dataclass
class ImportStats:
    valid: int = 0
    invalid: int = 0


def load_config(path: Path) -> Config:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("categories"), list):
            raise ValidationError("configuration must contain category list")
        return Config(
            tuple(raw["categories"]),
            Decimal(str(raw.get("min_price", ".01"))),
            Decimal(str(raw.get("max_price", "10000"))),
        )
    except (OSError, yaml.YAMLError, ValueError, InvalidOperation, TypeError) as exc:
        raise DataError(f"cannot load configuration: {path}") from exc


@contextmanager
def atomic_text(path: Path) -> Iterator[IO[str]]:
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            yield stream.file
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise DataError(f"cannot write {path}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def import_rows(
    path: Path, config: Config, stats: ImportStats, strict: bool = True
) -> Iterator[tuple[int, OrderItem]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"order_id", "dish", "category", "price", "quantity"}
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                raise DataError("missing CSV columns")
            for line, row in enumerate(reader, 2):
                try:
                    if None in row or any(value is None for value in row.values()):
                        raise ValidationError("malformed record")
                    number = int(row["order_id"])
                    Order(number)
                    dish = Dish(
                        row["dish"].strip(),
                        row["category"].strip(),
                        Decimal(row["price"]),
                    )
                    item = OrderItem(dish, int(row["quantity"]))
                    if (
                        dish.category not in config.categories
                        or not config.min_price <= dish.price <= config.max_price
                    ):
                        raise ValidationError("category or price outside configuration")
                except (ValueError, InvalidOperation, TypeError) as exc:
                    stats.invalid += 1
                    logger.warning("invalid record at line %s", line)
                    if strict:
                        raise DataError(f"invalid record at line {line}") from exc
                    continue
                stats.valid += 1
                yield number, item
    except (OSError, csv.Error, UnicodeError) as exc:
        raise DataError(f"cannot read {path}") from exc


def collect_orders(rows: Iterator[tuple[int, OrderItem]]) -> list[Order]:
    orders: dict[int, Order] = {}
    for number, item in rows:
        orders.setdefault(number, Order(number)).items.append(item)
    return list(orders.values())


def export_orders(path: Path, orders: list[Order]) -> None:
    data = [
        {
            "number": o.number,
            "total": str(o.total),
            "items": [
                {
                    "dish": i.dish.name,
                    "category": i.dish.category,
                    "price": str(i.dish.price),
                    "quantity": i.quantity,
                }
                for i in o
            ],
        }
        for o in orders
    ]
    with atomic_text(path) as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
