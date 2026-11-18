"""Sorted-input pipeline. order_id must be nondecreasing; no hidden full sort."""

import csv
import json
import tracemalloc
from collections.abc import Iterable, Iterator
from decimal import Decimal
from itertools import chain, groupby, islice
from pathlib import Path
from time import perf_counter

from restaurant_manager.errors import ValidationError
from restaurant_manager.models import Dish, OrderItem

Record = tuple[int, OrderItem]


def read_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream)


def clean(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValidationError("malformed CSV row")
        yield {k.strip(): v.strip() for k, v in row.items()}


def parse(rows: Iterable[dict[str, str]]) -> Iterator[Record]:
    previous = 0
    for row in rows:
        number = int(row["order_id"])
        if number <= 0 or number < previous:
            raise ValidationError("input must be sorted by positive order_id")
        previous = number
        yield (
            number,
            OrderItem(
                Dish(row["dish"], row["category"], Decimal(row["price"])),
                int(row["quantity"]),
            ),
        )


def category_filter(
    rows: Iterable[Record], category: str | None = None
) -> Iterator[Record]:
    for record in rows:
        if category is None or record[1].dish.category == category:
            yield record


def transform(rows: Iterable[Record]) -> Iterator[tuple[int, Decimal, Decimal]]:
    for number, item in rows:
        yield number, item.total, item.dish.price


def order_totals(
    rows: Iterable[tuple[int, Decimal, Decimal]],
) -> Iterator[tuple[int, Decimal, Decimal]]:
    for number, group in groupby(rows, key=lambda r: r[0]):
        total, expensive = Decimal(0), Decimal(0)
        for _, value, price in group:
            total += value
            expensive = max(expensive, price)
        yield number, total, expensive


def batches(
    rows: Iterable[tuple[int, Decimal, Decimal]], size: int = 500
) -> Iterator[list[tuple[int, Decimal, Decimal]]]:
    if size <= 0:
        raise ValueError("size must be positive")
    iterator = iter(rows)
    while batch := list(islice(iterator, size)):
        yield batch


def pipeline(
    path: Path, category: str | None = None
) -> Iterator[tuple[int, Decimal, Decimal]]:
    return order_totals(
        transform(category_filter(parse(clean(read_rows(path))), category))
    )


def generate(path: Path, count: int = 100_000) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["order_id", "dish", "category", "price", "quantity"])
        writer.writerows(
            (
                i // 4 + 1,
                f"dish-{i % 20}",
                "food" if i % 2 else "drinks",
                f"{30 + i % 100}.00",
                i % 3 + 1,
            )
            for i in range(count)
        )


def benchmark(path: Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for mode in ("eager", "lazy"):
        tracemalloc.start()
        start = perf_counter()
        records: Iterable[Record] = parse(clean(read_rows(path)))
        if mode == "eager":
            records = list(records)
        count, revenue = 0, Decimal(0)
        for batch in batches(order_totals(transform(chain(records, ())))):
            for _, total, _ in batch:
                count += 1
                revenue += total
        seconds = perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results.append(
            {
                "mode": mode,
                "seconds": seconds,
                "peak_mib": peak / 1024**2,
                "orders": count,
                "revenue": str(revenue),
                "average": str(revenue / count if count else 0),
            }
        )
    assert results[0]["revenue"] == results[1]["revenue"]
    assert results[0]["orders"] == results[1]["orders"]
    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True)
    path = args.output / "orders.csv"
    generate(path, args.count)
    result = benchmark(path)
    print(json.dumps(result, indent=2))
    (args.output / "streaming.json").write_text(json.dumps(result, indent=2))
    print(
        "first qualifying:", list(islice((r for r in pipeline(path) if r[1] >= 500), 3))
    )


if __name__ == "__main__":
    main()
