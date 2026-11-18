from restaurant_manager.performance import (
    History,
    generate,
    numpy_stats,
    process_stats,
    sequential,
    synchronized_demo,
    threaded_files,
)


def test_implementations():
    rows = generate(101)
    assert sequential(rows) == numpy_stats(rows) == process_stats(rows)
    assert sequential([]) == numpy_stats([]) == process_stats([])


def test_cache_invalidation():
    history = History(generate(10))
    old = history.revenue()
    assert history.revenue() == old
    history.change_price(0, 3100)
    assert history.revenue() == old + 100


def test_threads(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_text("10\n20")
    b.write_text("30")
    assert threaded_files([a, b]) == 60
    assert synchronized_demo() == 4000


def test_benchmark_evidence(tmp_path):
    from restaurant_manager.performance import benchmark

    result = benchmark(101, 2, tmp_path)
    assert result["records"] == 101 and result["orders"] == 26
    assert len(result["cpu"]) == 3
    assert all(len(row["repeats"]) == 2 for row in result["cpu"])
    assert result["cache"]["after"] > result["cache"]["before"]
    assert (tmp_path / "profile.txt").is_file()
