from restaurant_manager.models import dish, order

def add_dish(order_obj: order, new_dish: dish) -> None:
    order_obj.dishes.append(new_dish)

def calc_total(order_obj: order) -> float:
    return sum(d.price for d in order_obj.dishes)

def get_most_expensive(order_obj: order) -> dish | None:
    if not order_obj.dishes:
        return None
    return max(order_obj.dishes, key=lambda d: d.price)

def calc_average_order(orders: list[order]) -> float:
    if not orders:
        return 0.0
    total = sum(calc_total(o) for o in orders)
    return total / len(orders)