from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from restaurant_orders.errors import NotFound, ValidationError

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def add(self, key: int, item: T) -> None: ...
    @abstractmethod
    def get(self, key: int) -> T: ...
    @abstractmethod
    def all(self) -> list[T]: ...


class MemoryRepository(Repository[T]):
    def __init__(self) -> None:
        self._items: dict[int, T] = {}

    def add(self, key: int, item: T) -> None:
        if key in self._items:
            raise ValidationError("duplicate identifier")
        self._items[key] = item

    def get(self, key: int) -> T:
        try:
            return self._items[key]
        except KeyError as exc:
            raise NotFound(str(key)) from exc

    def all(self) -> list[T]:
        return list(self._items.values())
