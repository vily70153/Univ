from restaurant_manager.models import dish, order
from restaurant_manager.services import add_dish, calc_total, get_most_expensive, calc_average_order

def main() -> None:
    d1 = dish("борщ", "перше", 120.0)
    d2 = dish("стейк", "основне", 450.0)
    o1 = order(1)

    add_dish(o1, d1)
    add_dish(o1, d2)

    print("сума замовлення:", calc_total(o1))

    expensive = get_most_expensive(o1)
    if expensive:
        print("найдорожча страва:", expensive.name)
        
    print("середня вартість усіх замовлень:", calc_average_order([o1]))

if __name__ == "__main__":
    main()