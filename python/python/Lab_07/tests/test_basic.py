from decimal import Decimal

from restaurant_manager.analytics import (
    filter_orders,
    find_order,
    sort_orders,
    summarize,
)
from restaurant_manager.data import demo_orders
from restaurant_manager.services import calc_average_order, get_most_expensive


def test_demo_totals():
    orders = demo_orders()
    assert [o.total for o in orders] == [200, 155, 0]
    assert summarize(orders)["revenue"] == 355
    assert calc_average_order([]) == 0
    assert get_most_expensive(orders[2]) is None


def test_analytics():
    orders = demo_orders()
    assert find_order(orders, 20) is None
    assert find_order(orders, 1) is orders[0]
    assert [o.number for o in sort_orders(orders)] == [1, 2, 3]
    assert [o.number for o in filter_orders(orders, minimum=Decimal(180))] == [1]
