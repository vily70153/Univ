import argparse
import logging
from pathlib import Path

from restaurant_orders.errors import RestaurantError
from restaurant_orders.files import (
    ImportStats,
    collect_orders,
    export_orders,
    import_rows,
    load_config,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/orders.csv"))
    parser.add_argument("--config", type=Path, default=Path("data/config.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/orders.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        stats = ImportStats()
        orders = collect_orders(
            import_rows(args.input, load_config(args.config), stats, args.strict)
        )
        export_orders(args.output, orders)
        print(f"valid={stats.valid}; invalid={stats.invalid}; orders={len(orders)}")
        for order in orders:
            print(order)
    except RestaurantError as exc:
        logging.error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
