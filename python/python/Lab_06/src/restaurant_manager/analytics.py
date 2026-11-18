from collections import Counter, defaultdict
from collections.abc import Callable
from decimal import Decimal
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

from restaurant_manager.models import Order

P = ParamSpec("P")
R = TypeVar("R")


def timed(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {perf_counter() - start:.6f} s")
        return result

    return wrapper


def make_threshold(minimum: Decimal) -> Callable[[Order], bool]:
    return lambda order: order.total >= minimum


def index_orders(orders: list[Order]) -> dict[int, Order]:
    return {o.number: o for o in orders}


def find_order(orders: list[Order], number: int) -> Order | None:
    return index_orders(orders).get(number)


def filter_orders(orders: list[Order], **criteria: Decimal) -> list[Order]:
    predicate = make_threshold(criteria.get("minimum", Decimal(0)))
    return [o for o in orders if predicate(o)]


def total_revenue(*orders: Order) -> Decimal:
    return sum((o.total for o in orders), Decimal(0))


def sort_orders(orders: list[Order]) -> list[Order]:
    return sorted(orders, key=lambda o: o.total, reverse=True)


def group_categories(orders: list[Order]) -> dict[str, Decimal]:
    groups: dict[str, Decimal] = defaultdict(Decimal)
    for order in orders:
        for item in order:
            groups[item.dish.category] += item.total
    return dict(groups)


def summarize(orders: list[Order]) -> dict[str, object]:
    categories = {i.dish.category for o in orders for i in o}
    popularity: Counter[str] = Counter()
    for o in orders:
        for i in o:
            popularity[i.dish.name] += i.quantity
    bounds = (
        min((o.total for o in orders), default=Decimal(0)),
        max((o.total for o in orders), default=Decimal(0)),
    )
    return {
        "categories": sorted(categories),
        "popularity": dict(popularity),
        "bounds": bounds,
        "revenue": total_revenue(*orders),
        "groups": group_categories(orders),
    }
