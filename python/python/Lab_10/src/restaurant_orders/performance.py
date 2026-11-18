import cProfile
import json
import statistics
import threading
import tracemalloc
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from time import perf_counter

import numpy as np

# order, dish, category, unit price in kopecks, quantity
Row = tuple[int, int, int, int, int]


def generate(count: int) -> list[Row]:
    return [
        (i // 4, i % 20, i % 3, (30 + i % 100) * 100, i % 3 + 1) for i in range(count)
    ]


def sequential(rows: list[Row]) -> dict:
    orders: dict[int, int] = defaultdict(int)
    categories: dict[int, int] = defaultdict(int)
    popularity: Counter[int] = Counter()
    expensive: dict[int, int] = defaultdict(int)
    for order, dish, category, price, quantity in rows:
        value = price * quantity
        orders[order] += value
        categories[category] += value
        popularity[dish] += quantity
        expensive[dish] = max(expensive[dish], price)
    revenue = sum(orders.values())
    return {
        "revenue": revenue,
        "average_cents": revenue / len(orders) if orders else 0,
        "orders": dict(orders),
        "categories": dict(categories),
        "popularity": dict(popularity),
        "expensive": dict(expensive),
    }


def numpy_stats(rows: list[Row]) -> dict:
    if not rows:
        return sequential([])
    data = np.asarray(rows, dtype=np.int64)
    value = data[:, 3] * data[:, 4]

    def grouped(column: int, weights) -> dict[int, int]:
        keys, inverse = np.unique(data[:, column], return_inverse=True)
        totals = np.zeros(len(keys), dtype=np.int64)
        np.add.at(totals, inverse, weights)
        return {int(k): int(v) for k, v in zip(keys, totals)}

    orders = grouped(0, value)
    keys, inverse = np.unique(data[:, 1], return_inverse=True)
    maximum = np.zeros(len(keys), dtype=np.int64)
    np.maximum.at(maximum, inverse, data[:, 3])
    revenue = int(value.sum())
    return {
        "revenue": revenue,
        "average_cents": revenue / len(orders),
        "orders": orders,
        "categories": grouped(2, value),
        "popularity": grouped(1, data[:, 4]),
        "expensive": {int(k): int(v) for k, v in zip(keys, maximum)},
    }


def process_stats(rows: list[Row]) -> dict:
    size = max(1, (len(rows) + 3) // 4)
    chunks = [rows[i : i + size] for i in range(0, len(rows), size)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        pieces = list(pool.map(sequential, chunks))
    result = sequential([])
    for key in ("orders", "categories", "popularity", "expensive"):
        combined: dict[int, int] = defaultdict(int)
        for piece in pieces:
            for k, value in piece[key].items():
                combined[k] = (
                    max(combined[k], value)
                    if key == "expensive"
                    else combined[k] + value
                )
        result[key] = dict(combined)
    result["revenue"] = sum(result["orders"].values())
    result["average_cents"] = (
        result["revenue"] / len(result["orders"]) if result["orders"] else 0
    )
    return result


@lru_cache(maxsize=16)
def cached_revenue(rows: tuple[Row, ...]) -> int:
    return sum(r[3] * r[4] for r in rows)


class History:
    def __init__(self, rows: list[Row]):
        self.rows = list(rows)

    def revenue(self) -> int:
        return cached_revenue(tuple(self.rows))

    def change_price(self, index: int, cents: int) -> None:
        if cents <= 0:
            raise ValueError("positive price required")
        a, b, c, _, e = self.rows[index]
        self.rows[index] = (a, b, c, cents, e)
        cached_revenue.cache_clear()


def read_file(path: Path) -> int:
    return sum(int(line) for line in path.read_text().splitlines())


def threaded_files(paths: list[Path]) -> int:
    with ThreadPoolExecutor(max_workers=4) as pool:
        return sum(pool.map(read_file, paths))


def synchronized_demo() -> int:
    total = 0
    lock = threading.Lock()

    def worker():
        nonlocal total
        for _ in range(1000):
            with lock:
                total += 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return total


def benchmark(count: int, repeats: int, output: Path) -> dict:
    rows = generate(count)
    baseline = sequential(rows)
    results: list[dict] = []
    for name, implementation in (
        ("sequential", sequential),
        ("numpy", numpy_stats),
        ("process_pool", process_stats),
    ):
        times = []
        for _ in range(repeats):
            start = perf_counter()
            actual = implementation(rows)
            times.append(perf_counter() - start)
            assert actual == baseline
        tracemalloc.start()
        implementation(rows)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results.append(
            {
                "implementation": name,
                "seconds": statistics.median(times),
                "repeats": times,
                "parent_peak_mib": peak / 1024**2,
            }
        )
    for result in results:
        result["speedup"] = results[0]["seconds"] / result["seconds"]
    profiler = cProfile.Profile()
    profiler.runcall(sequential, rows)
    profiler.dump_stats(str(output / "baseline.prof"))
    import pstats

    with (output / "profile.txt").open("w") as stream:
        pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(15)
    paths = []
    for i in range(4):
        path = output / f"part-{i}.txt"
        path.write_text("\n".join(str(r[3] * r[4]) for r in rows[i::4]))
        paths.append(path)
    io = {}
    for name, operation in (
        ("sequential", lambda: sum(map(read_file, paths))),
        ("threads", lambda: threaded_files(paths)),
    ):
        times = []
        for _ in range(repeats):
            start = perf_counter()
            value = operation()
            times.append(perf_counter() - start)
            assert value == baseline["revenue"]
        io[name] = statistics.median(times)
    history = History(rows)
    before = history.revenue()
    history.revenue()
    hits = cached_revenue.cache_info().hits
    history.change_price(0, rows[0][3] + 100)
    after = history.revenue()
    assert after == before + 100 * rows[0][4]
    assert synchronized_demo() == 4000
    return {
        "records": count,
        "orders": len(baseline["orders"]),
        "cpu": results,
        "io": io,
        "cache": {"hits_before_invalidation": hits, "before": before, "after": after},
        "memory_note": "tracemalloc measures Python allocations in parent only; excludes worker RSS",
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.count < 1 or args.repeats < 2:
        parser.error("count >= 1 and repeats >= 2 required")
    args.output.mkdir(exist_ok=True)
    result = benchmark(args.count, args.repeats, args.output)
    (args.output / "benchmark.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
