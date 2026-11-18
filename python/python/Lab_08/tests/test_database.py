from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from restaurant_manager.database import initialize, migrate_status, search_category
from restaurant_manager.errors import NotFound
from restaurant_manager.persistence import (
    MenuRepository,
    OrderRepository,
    PersistentService,
)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "test.db"
    engine, factory = initialize(f"sqlite:///{path}")
    yield path, engine, factory
    engine.dispose()


def test_menu_crud(database):
    path, _, factory = database
    with factory.begin() as s:
        repo = MenuRepository(s)
        identifier = repo.add("soup", "food", Decimal(85)).id
        assert repo.get(identifier).price_cents == 8500
        repo.update(identifier, "borsch", Decimal(90))
        assert repo.all("food")[0].name == "borsch"
    assert search_category(path, "food")[0][2] == 9000
    assert search_category(path, "' OR 1=1 --") == []
    with factory.begin() as s:
        repo = MenuRepository(s)
        repo.delete(identifier)
        assert repo.all() == []


def test_order_transaction(database):
    _, _, factory = database
    with factory.begin() as s:
        a = MenuRepository(s).add("soup", "food", Decimal(85)).id
        b = MenuRepository(s).add("tea", "drink", Decimal(30)).id
    identifier = PersistentService(factory).create_order([(a, 2), (b, 1)])
    with factory.begin() as s:
        repo = OrderRepository(s)
        assert repo.total(identifier) == 200 and repo.average() == 200
        assert repo.expensive(identifier).dish_id == a
        repo.update_status(identifier, "paid")
        assert repo.get(identifier).status == "paid"
        repo.remove_item(identifier, repo.items(identifier)[1].id)
        assert repo.total(identifier) == 170
        repo.delete(identifier)
        assert repo.all() == [] and repo.average() == 0


def test_rollback(database):
    _, _, factory = database
    with factory.begin() as s:
        dish_id = MenuRepository(s).add("soup", "food", Decimal(85)).id
    with pytest.raises(NotFound):
        PersistentService(factory).create_order([(dish_id, 1), (9999, 1)])
    with factory() as s:
        assert OrderRepository(s).all() == []
        assert s.execute(text("SELECT count(*) FROM order_items")).scalar() == 0


def test_price_snapshot(database):
    _, _, factory = database
    with factory.begin() as s:
        dish_id = MenuRepository(s).add("soup", "food", Decimal(85)).id
    order_id = PersistentService(factory).create_order([(dish_id, 1)])
    with factory.begin() as s:
        MenuRepository(s).update(dish_id, "soup", Decimal(99))
        assert OrderRepository(s).total(order_id) == 85


def test_foreign_key(database):
    _, _, factory = database
    with pytest.raises(IntegrityError):
        with factory.begin() as s:
            s.execute(
                text(
                    "INSERT INTO dishes (name,category_id,price_cents) VALUES ('x',999,100)"
                )
            )


def test_migration(tmp_path):
    from restaurant_manager.database import make_engine

    engine = make_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as c:
        c.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY)"))
        c.execute(text("INSERT INTO orders VALUES (1)"))
    migrate_status(engine)
    migrate_status(engine)
    with engine.connect() as c:
        assert c.execute(text("SELECT status FROM orders")).scalar() == "new"
    engine.dispose()
