from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from restaurant_orders.database import initialize, search_category
from restaurant_orders.errors import NotFound
from restaurant_orders.persistence import (
    MenuRepository,
    OrderRepository,
    PersistentService,
)


def main() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "demo.db"
        engine, factory = initialize(f"sqlite:///{path}")
        with factory.begin() as session:
            menu = MenuRepository(session)
            a = menu.add("Борщ", "супи", Decimal(85)).id
            b = menu.add("Чай", "напої", Decimal(30)).id
        service = PersistentService(factory)
        number = service.create_order([(a, 2), (b, 1)])
        try:
            service.create_order([(a, 1), (99999, 1)])
        except NotFound:
            print("rollback: invalid dish rejected")
        with factory() as session:
            repo = OrderRepository(session)
            print(
                "orders:",
                len(repo.all()),
                "total:",
                repo.total(number),
                "average:",
                repo.average(),
            )
        print("DB-API search:", search_category(path, "супи"))
        engine.dispose()


if __name__ == "__main__":
    main()
