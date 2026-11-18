from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from restaurant_orders.database import CategoryRow, DishRow, ItemRow, OrderRow
from restaurant_orders.errors import NotFound, ValidationError
from restaurant_orders.models import Dish, OrderItem


class MenuRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, name: str, category: str, price: Decimal) -> DishRow:
        validated = Dish(name, category, price)
        cat = self.session.scalar(
            select(CategoryRow).where(CategoryRow.name == category)
        )
        if cat is None:
            cat = CategoryRow(name=category)
            self.session.add(cat)
            self.session.flush()
        row = DishRow(
            name=name, category_id=cat.id, price_cents=int(validated.price * 100)
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, identifier: int) -> DishRow:
        row = self.session.get(DishRow, identifier)
        if row is None:
            raise NotFound("dish not found")
        return row

    def all(self, category: str | None = None) -> list[DishRow]:
        stmt = select(DishRow).order_by(DishRow.id)
        if category is not None:
            stmt = stmt.join(CategoryRow).where(CategoryRow.name == category)
        return list(self.session.scalars(stmt))

    def update(self, identifier: int, name: str, price: Decimal) -> DishRow:
        row = self.get(identifier)
        validated = Dish(name, "validated-category", price)
        row.name, row.price_cents = validated.name, int(validated.price * 100)
        self.session.flush()
        return row

    def delete(self, identifier: int) -> None:
        self.session.delete(self.get(identifier))
        self.session.flush()


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, identifier: int) -> OrderRow:
        row = self.session.get(OrderRow, identifier)
        if row is None:
            raise NotFound("order not found")
        return row

    def all(self) -> list[OrderRow]:
        return list(self.session.scalars(select(OrderRow).order_by(OrderRow.id)))

    def create(self, items: list[tuple[int, int]]) -> OrderRow:
        row = OrderRow()
        self.session.add(row)
        self.session.flush()
        for dish_id, quantity in items:
            self.add_item(row.id, dish_id, quantity)
        return row

    def add_item(self, identifier: int, dish_id: int, quantity: int) -> ItemRow:
        self.get(identifier)
        dish = MenuRepository(self.session).get(dish_id)
        OrderItem(Dish(dish.name, "menu", Decimal(dish.price_cents) / 100), quantity)
        item = ItemRow(
            order_id=identifier,
            dish_id=dish_id,
            quantity=quantity,
            price_cents=dish.price_cents,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def items(self, identifier: int) -> list[ItemRow]:
        self.get(identifier)
        return list(
            self.session.scalars(
                select(ItemRow)
                .where(ItemRow.order_id == identifier)
                .order_by(ItemRow.id)
            )
        )

    def remove_item(self, identifier: int, item_id: int) -> None:
        self.get(identifier)
        item = self.session.get(ItemRow, item_id)
        if item is None or item.order_id != identifier:
            raise NotFound("item not found in order")
        self.session.delete(item)
        self.session.flush()

    def total(self, identifier: int) -> Decimal:
        return sum(
            (Decimal(i.price_cents) * i.quantity / 100 for i in self.items(identifier)),
            Decimal(0),
        )

    def expensive(self, identifier: int) -> ItemRow | None:
        return max(self.items(identifier), key=lambda i: i.price_cents, default=None)

    def average(self) -> Decimal:
        orders = self.all()
        return (
            sum((self.total(o.id) for o in orders), Decimal(0)) / len(orders)
            if orders
            else Decimal(0)
        )

    def update_status(self, identifier: int, status: str) -> None:
        if status not in {"new", "paid", "completed", "cancelled"}:
            raise ValidationError("invalid status")
        self.get(identifier).status = status
        self.session.flush()

    def delete(self, identifier: int) -> None:
        self.session.delete(self.get(identifier))
        self.session.flush()


class PersistentService:
    """One session and transaction per operation. Context rolls back on failure."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def create_order(self, items: list[tuple[int, int]]) -> int:
        with self.factory() as session:
            try:
                order = OrderRepository(session).create(items)
                session.commit()
                return order.id
            except Exception:
                session.rollback()
                raise
