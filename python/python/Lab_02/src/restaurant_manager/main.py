from decimal import Decimal

from restaurant_manager.analytics import (
    filter_orders,
    find_order,
    sort_orders,
    summarize,
    timed,
)
from restaurant_manager.data import demo_orders
from restaurant_manager.services import calc_average_order


def main() -> None:
    orders = demo_orders()
    for order in sort_orders(orders):
        print(order)
    print("statistics:", timed(summarize)(orders))
    print("average:", calc_average_order(orders))
    print(
        "at least 180:", [o.number for o in filter_orders(orders, minimum=Decimal(180))]
    )
    print("find #2:", find_order(orders, 2))


if __name__ == "__main__":
    main()
