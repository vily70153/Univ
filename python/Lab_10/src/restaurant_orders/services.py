from decimal import Decimal

from restaurant_orders.models import Dish, Order, OrderItem


def add_dish(order: Order, dish: Dish, quantity: int = 1) -> None:
    order.items.append(OrderItem(dish, quantity))


def calc_total(order: Order) -> Decimal:
    return order.total


def get_most_expensive(order: Order) -> Dish | None:
    return max((i.dish for i in order), key=lambda d: d.price, default=None)


def calc_average_order(orders: list[Order]) -> Decimal:
    return (
        sum((o.total for o in orders), Decimal(0)) / len(orders)
        if orders
        else Decimal(0)
    )
