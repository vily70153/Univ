# лабораторна робота 9

Паралельність, багатопроцесність та оптимізація. варіант 11: облік замовлень ресторану.
автор: ценьов віталій, феп-31с. продовження Lab_01; ця папка є самостійним знімком проєкту.
для Lab_02 загальні вимоги методички адаптовано до ресторану, оскільки в наданому файлі залишено лише варіант 4.

## встановлення

Python 3.11+. виконуйте команди саме з цієї папки. для кожної лабораторної створюйте окреме середовище: однойменні пакети різних робіт не потрібно встановлювати разом.

```sh
python -m venv .venv
# linux/macos
source .venv/bin/activate
# windows powershell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m restaurant_manager.main
pytest -q --cov=restaurant_manager --cov-branch --cov-report=term-missing
ruff check .
ruff format --check .
mypy src
```

## предметна модель

Dish зберігає назву, категорію та додатну ціну Decimal із точністю до копійки.
Order містить OrderItem; quantity є додатним цілим числом. сума позиції дорівнює price × quantity.
найдорожчу страву визначено за одиничною ціною. середній чек включає порожні замовлення з нульовою сумою.
результати перевірок знаходяться у results/. гроші в SQLite зберігаються цілими копійками.

## структура

src/restaurant_manager/models.py: доменні моделі та валідація.
services.py: сума, найдорожча страва, середній чек.
analytics.py: індекс, сортування, фільтрація, групування та популярність.
data.py: демонстраційні замовлення з сумами 200, 155 і 0 грн.
main.py: точка входу, відокремлена від логіки.
tests/: автоматизовані перевірки; pyproject.toml: пакет, залежності та інструменти.

## складність

побудова індексу замовлень O(n), наступний пошук за ключем у готовому dict у середньому O(1).
find_order будує індекс на кожний виклик, тому весь цей виклик O(n).
сортування n замовлень за сумою коштує O(m + n log n), де m є кількістю позицій.
агрегація категорій і обороту O(m), пам'ять для категорій O(k).

## потокова обробка

```sh
python -m restaurant_manager.streaming --count 100000
```

вхідний CSV вже впорядкований за order_id. неупорядкований ввід відхиляється; сортування всього файла не приховано всередині pipeline. генератор групує лише сусідні записи. eager та lazy обробляють однакові дані, показують час і peak tracemalloc; batches мають до 500 замовлень.

## архітектура

Money є frozen value object. Menu та Order використовують композицію. MemoryRepository успадковує generic ABC Repository[T]. RestaurantService одержує repository і notifier через constructor injection. payment та async delivery передаються у методи. SRP відокремлює модель, I/O і сервіс; DIP задає Protocol/ABC; OCP дозволяє додати інший repository без зміни сервісу. checkout демонструє виклик платіжної залежності, не є реальною платіжною системою.

## файли

```sh
python -m restaurant_manager.main --input data/orders.csv --config data/config.yaml --output results/orders.json
python -m restaurant_manager.main --strict
```

демонстраційний CSV має 4 валідні та 1 навмисно невалідний запис. tolerant пропускає помилку; strict повертає exit code 1 і не змінює вихідний JSON. atomic replace виконується через тимчасовий файл у тому самому каталозі. імпорт потоковий; collect_orders накопичує замовлення в пам'яті для JSON export.

## тести

pytest перевіряє unit, інтеграцію CSV → domain → JSON, malformed records, конфігурацію, атомарність, Mock payment, side_effect та AsyncMock delivery. fixture isolation забезпечується tmp_path. coverage включає branches; рекомендований мінімум від Lab_06: 80%.

## база даних

```sh
python -m restaurant_manager.db_demo
```

categories → dishes, orders → order_items; order_items посилається на dish. checkout записує замовлення та позиції однією транзакцією; виняток викликає rollback. ціна фіксується у позиції, тому зміна меню не змінює старі чеки. видалення страви, на яку є посилання, заборонене FK.

міграція migrations/001_status.sql додає status у стару v1 таблицю orders. функція database.migrate_status(engine) перевіряє стовпці та застосовує її ідемпотентно. нова база вже має status. integration test створює стару схему, мігрує її двічі й перевіряє збереження рядка.

## api

```sh
uvicorn restaurant_manager.api:app --host 127.0.0.1 --port 8000
```

Swagger: http://127.0.0.1:8000/docs. GET /dishes?category=..., POST /dishes, PATCH/DELETE /dishes/{id}. GET/POST /orders, GET/PATCH /orders/{id}, POST /orders/{id}/items, DELETE /orders/{id}/items/{item_id}, GET /orders/{id}/total, GET /orders/statistics, GET /health.

створення повертає 201, видалення 204, відсутній ресурс 404, невалідні дані 422, конфлікт FK 409. синхронні DB handlers виконуються FastAPI у thread pool; async client використовує Task/gather, Semaphore, timeout та backoff. retry лише для GET і transient errors. кількість одночасно створених Task також обмежена.

```python
import asyncio
import httpx
from restaurant_manager.async_client import fetch_totals


async def demo():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print(await fetch_totals(client, [1, 2]))


asyncio.run(demo())
```

## експерименти

```sh
python -m restaurant_manager.performance --count 100000 --repeats 3
```

порівнюються повні статистики sequential, NumPy, ProcessPoolExecutor, включно з конвертацією даних і запуском worker processes. ThreadPoolExecutor читає 4 локальні файли; Lock захищає спільний лічильник. benchmark.json зберігає повтори, медіану, speedup і peak пам'яті батьківського процесу; дочірню RSS tracemalloc не вимірює. cache очищується після зміни ціни. профіль: results/profile.txt.
