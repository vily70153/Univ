from decimal import Decimal
from typing import Protocol, TypedDict

from restaurant_manager.errors import ValidationError
from restaurant_manager.models import Dish, Order, OrderItem
from restaurant_manager.repositories import Repository
from restaurant_manager.services import calc_average_order


class Notifier(Protocol):
    def send(self, message: str) -> None: ...


class Payment(Protocol):
    def charge(self, amount: Decimal) -> bool: ...


class Delivery(Protocol):
    async def dispatch(self, number: int) -> str: ...


class OrderDTO(TypedDict):
    number: int
    total: str
    positions: int


class ConsoleNotifier:
    def send(self, message: str) -> None:
        print(message)


class RestaurantService:
    def __init__(self, repository: Repository[Order], notifier: Notifier) -> None:
        self.repository = repository
        self.notifier = notifier

    def create(self, number: int) -> Order:
        order = Order(number)
        self.repository.add(number, order)
        return order

    def add(self, number: int, dish: Dish, quantity: int = 1) -> None:
        self.repository.get(number).items.append(OrderItem(dish, quantity))

    def average(self) -> Decimal:
        return calc_average_order(self.repository.all())

    def checkout(self, number: int, payment: Payment) -> bool:
        order = self.repository.get(number)
        if not order.items:
            raise ValidationError("empty order")
        if not payment.charge(order.total):
            return False
        self.notifier.send(f"paid #{number}: {order.total}")
        return True

    async def deliver(self, number: int, delivery: Delivery) -> str:
        self.repository.get(number)
        return await delivery.dispatch(number)

    def dto(self, number: int) -> OrderDTO:
        order = self.repository.get(number)
        return {"number": number, "total": str(order.total), "positions": len(order)}
