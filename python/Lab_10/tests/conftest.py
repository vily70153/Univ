from decimal import Decimal

import pytest

from restaurant_orders.files import Config
from restaurant_orders.models import Dish, Order


@pytest.fixture
def dish():
    return Dish("Борщ", "супи", Decimal(85))


@pytest.fixture
def order():
    return Order(1)


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "orders.csv"
    path.write_text(
        "order_id,dish,category,price,quantity\n1,Борщ,супи,85,2\n2,Чай,напої,30,1\n",
        encoding="utf-8",
    )
    return path
