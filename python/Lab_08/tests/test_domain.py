from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from restaurant_manager.application import RestaurantService
from restaurant_manager.errors import NotFound, ValidationError
from restaurant_manager.models import Dish, Menu, Money, Order, OrderItem
from restaurant_manager.repositories import MemoryRepository
from restaurant_manager.services import (
    add_dish,
    calc_average_order,
    calc_total,
    get_most_expensive,
)


def test_dish(dish):
    assert dish.name == "Борщ" and dish.price == 85


@pytest.mark.parametrize("price", ["0", "-1", "NaN", "Infinity", "1.001"])
def test_invalid_price(price):
    with pytest.raises(ValidationError):
        Dish("x", "y", Decimal(price))


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
def test_invalid_quantity(dish, quantity):
    with pytest.raises(ValidationError, match="quantity"):
        OrderItem(dish, quantity)


def test_blank_name():
    with pytest.raises(ValidationError):
        Dish(" ", "y", Decimal(1))


def test_blank_category():
    with pytest.raises(ValidationError):
        Dish("x", " ", Decimal(1))


def test_invalid_order():
    with pytest.raises(ValidationError):
        Order(0)


def test_empty(order):
    assert calc_total(order) == 0 and get_most_expensive(order) is None


def test_add(order, dish):
    add_dish(order, dish, 2)
    assert calc_total(order) == 170 and len(order) == 1


def test_total_exact(order):
    add_dish(order, Dish("x", "y", Decimal("0.10")), 3)
    assert order.total == Decimal("0.30")


def test_most_expensive(order, dish):
    add_dish(order, dish)
    add_dish(order, Dish("tea", "drinks", Decimal(30)), 10)
    assert get_most_expensive(order) == dish


def test_average(order, dish):
    add_dish(order, dish)
    assert float(calc_average_order([order, Order(2)])) == pytest.approx(42.5)


def test_empty_average():
    assert calc_average_order([]) == 0


def test_menu(dish):
    assert "Борщ" in Menu([dish]) and "no" not in Menu()


def test_money():
    assert str(Money(Decimal("1.20"))) == "1.20 UAH"


def test_order_str(order):
    assert str(order) == "Order #1: 0.00 UAH"


def test_repository(order):
    repo = MemoryRepository()
    repo.add(1, order)
    assert repo.get(1) is order and repo.all() == [order]
    with pytest.raises(ValidationError):
        repo.add(1, order)
    with pytest.raises(NotFound):
        repo.get(2)


def test_checkout_mock(order, dish):
    add_dish(order, dish)
    repository, notifier, payment = Mock(), Mock(), Mock()
    repository.get.return_value = order
    payment.charge.return_value = True
    service = RestaurantService(repository, notifier)
    assert service.checkout(1, payment)
    payment.charge.assert_called_once_with(Decimal(85))
    notifier.send.assert_called_once_with("paid #1: 85")


def test_payment_declined(order, dish):
    add_dish(order, dish)
    repo, notifier, payment = Mock(), Mock(), Mock()
    repo.get.return_value = order
    payment.charge.return_value = False
    assert not RestaurantService(repo, notifier).checkout(1, payment)
    notifier.send.assert_not_called()


def test_payment_failure(order, dish):
    add_dish(order, dish)
    repo, notifier, payment = Mock(), Mock(), Mock()
    repo.get.return_value = order
    payment.charge.side_effect = ConnectionError("offline")
    with pytest.raises(ConnectionError):
        RestaurantService(repo, notifier).checkout(1, payment)
    notifier.send.assert_not_called()


def test_empty_checkout(order):
    repo = Mock()
    repo.get.return_value = order
    with pytest.raises(ValidationError):
        RestaurantService(repo, Mock()).checkout(1, Mock())


async def test_async_delivery(order):
    repo = Mock()
    repo.get.return_value = order
    delivery = Mock()
    delivery.dispatch = AsyncMock(return_value="sent")
    assert await RestaurantService(repo, Mock()).deliver(1, delivery) == "sent"
    delivery.dispatch.assert_awaited_once_with(1)


async def test_delivery_failure(order):
    repo = Mock()
    repo.get.return_value = order
    delivery = Mock()
    delivery.dispatch = AsyncMock(side_effect=TimeoutError)
    with pytest.raises(TimeoutError):
        await RestaurantService(repo, Mock()).deliver(1, delivery)


def test_service_flow(dish):
    service = RestaurantService(MemoryRepository(), Mock())
    service.create(1)
    service.add(1, dish, 2)
    assert service.dto(1) == {"number": 1, "total": "170", "positions": 1}
    assert service.average() == 170
