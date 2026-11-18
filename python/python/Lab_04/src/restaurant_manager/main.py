from restaurant_manager.application import ConsoleNotifier, RestaurantService
from restaurant_manager.data import demo_orders
from restaurant_manager.models import Menu, Money, Order
from restaurant_manager.repositories import MemoryRepository


def main() -> None:
    repository: MemoryRepository[Order] = MemoryRepository()
    service = RestaurantService(repository, ConsoleNotifier())
    samples = demo_orders()
    for sample in samples:
        service.create(sample.number)
        for item in sample:
            service.add(sample.number, item.dish, item.quantity)
    print("menu contains Борщ:", "Борщ" in Menu([samples[0].items[0].dish]))
    print("dto:", service.dto(1))
    print(
        "average:",
        Money(service.average().quantize(__import__("decimal").Decimal("0.01"))),
    )


if __name__ == "__main__":
    main()
