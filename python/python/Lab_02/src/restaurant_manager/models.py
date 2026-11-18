from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from restaurant_manager.errors import ValidationError


@dataclass(frozen=True)
class Money:
    amount: Decimal

    def __post_init__(self) -> None:
        try:
            value = Decimal(str(self.amount))
            if (
                not value.is_finite()
                or value < 0
                or value != value.quantize(Decimal("0.01"))
            ):
                raise ValidationError(
                    "amount must be finite, non-negative, with at most 2 decimals"
                )
            object.__setattr__(self, "amount", value)
        except InvalidOperation as exc:
            raise ValidationError("invalid money") from exc

    def __str__(self) -> str:
        return f"{self.amount:.2f} UAH"


@dataclass(frozen=True)
class Dish:
    name: str
    category: str
    price: Decimal

    def __post_init__(self) -> None:
        price = Money(self.price).amount
        if not self.name.strip() or not self.category.strip() or price <= 0:
            raise ValidationError("name/category required, price must be positive")
        object.__setattr__(self, "price", price)


@dataclass(frozen=True)
class OrderItem:
    dish: Dish
    quantity: int = 1

    def __post_init__(self) -> None:
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValidationError("quantity must be a positive integer")

    @property
    def total(self) -> Decimal:
        return self.dish.price * self.quantity


@dataclass
class Order:
    number: int
    items: list[OrderItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if type(self.number) is not int or self.number <= 0:
            raise ValidationError("order number must be positive")

    @property
    def total(self) -> Decimal:
        return sum((item.total for item in self.items), Decimal(0))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[OrderItem]:
        return iter(self.items)

    def __str__(self) -> str:
        return f"Order #{self.number}: {self.total:.2f} UAH"


@dataclass
class Menu:
    dishes: list[Dish] = field(default_factory=list)

    def __contains__(self, name: str) -> bool:
        return any(d.name == name for d in self.dishes)
