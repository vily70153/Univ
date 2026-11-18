from decimal import Decimal

from restaurant_manager.models import Dish, Order, OrderItem


def demo_orders() -> list[Order]:
    soup = Dish("Борщ", "супи", Decimal("85.00"))
    tea = Dish("Чай", "напої", Decimal("30.00"))
    cake = Dish("Сирник", "десерти", Decimal("95.00"))
    return [
        Order(1, [OrderItem(soup, 2), OrderItem(tea)]),
        Order(2, [OrderItem(cake), OrderItem(tea, 2)]),
        Order(3),
    ]
