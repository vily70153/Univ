import os
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from restaurant_manager.database import initialize
from restaurant_manager.errors import NotFound, ValidationError
from restaurant_manager.persistence import (
    MenuRepository,
    OrderRepository,
    PersistentService,
)


class DishInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: Decimal = Field(gt=0, decimal_places=2, allow_inf_nan=False)


class DishUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0, decimal_places=2, allow_inf_nan=False)


class ItemInput(BaseModel):
    dish_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, strict=True)


class OrderInput(BaseModel):
    items: list[ItemInput] = Field(default_factory=list)


class StatusInput(BaseModel):
    status: str


class DishOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category_id: int
    price_cents: int


class TotalOutput(BaseModel):
    total: str


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine, factory = initialize(
            database_url
            if database_url is not None
            else str(os.getenv("DATABASE_URL", "sqlite:///restaurant.db"))
        )
        app.state.factory = factory
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Restaurant orders", lifespan=lifespan)

    @app.exception_handler(NotFound)
    async def missing(request: Request, exc: NotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def invalid(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def conflict(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409, content={"detail": "related data prevents operation"}
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/dishes", response_model=list[DishOutput])
    def dishes(category: str | None = None):
        with app.state.factory() as session:
            return MenuRepository(session).all(category)

    @app.post("/dishes", status_code=201, response_model=DishOutput)
    def add_dish(payload: DishInput):
        with app.state.factory.begin() as session:
            return MenuRepository(session).add(
                payload.name, payload.category, payload.price
            )

    @app.patch("/dishes/{identifier}", response_model=DishOutput)
    def update_dish(identifier: int, payload: DishUpdate):
        with app.state.factory.begin() as session:
            return MenuRepository(session).update(
                identifier, payload.name, payload.price
            )

    @app.delete("/dishes/{identifier}", status_code=204)
    def delete_dish(identifier: int):
        with app.state.factory.begin() as session:
            MenuRepository(session).delete(identifier)

    @app.get("/orders/statistics")
    def statistics():
        with app.state.factory() as session:
            repository = OrderRepository(session)
            return {
                "count": len(repository.all()),
                "average": str(repository.average()),
            }

    @app.get("/orders")
    def history():
        with app.state.factory() as session:
            return [
                {"id": o.id, "status": o.status} for o in OrderRepository(session).all()
            ]

    @app.post("/orders", status_code=201)
    def create_order(payload: OrderInput):
        identifier = PersistentService(app.state.factory).create_order(
            [(i.dish_id, i.quantity) for i in payload.items]
        )
        return {"id": identifier}

    @app.get("/orders/{identifier}")
    def get_order(identifier: int):
        with app.state.factory() as session:
            repository = OrderRepository(session)
            order = repository.get(identifier)
            expensive = repository.expensive(identifier)
            return {
                "id": order.id,
                "status": order.status,
                "items": [
                    {
                        "id": i.id,
                        "dish_id": i.dish_id,
                        "quantity": i.quantity,
                        "price_cents": i.price_cents,
                    }
                    for i in repository.items(identifier)
                ],
                "most_expensive_item_id": expensive.id if expensive else None,
            }

    @app.patch("/orders/{identifier}")
    def update_order(identifier: int, payload: StatusInput):
        with app.state.factory.begin() as session:
            OrderRepository(session).update_status(identifier, payload.status)
            return {"id": identifier, "status": payload.status}

    @app.post("/orders/{identifier}/items", status_code=201)
    def add_item(identifier: int, payload: ItemInput):
        with app.state.factory.begin() as session:
            item = OrderRepository(session).add_item(
                identifier, payload.dish_id, payload.quantity
            )
            return {"id": item.id}

    @app.delete("/orders/{identifier}/items/{item_id}", status_code=204)
    def delete_item(identifier: int, item_id: int):
        with app.state.factory.begin() as session:
            OrderRepository(session).remove_item(identifier, item_id)

    @app.get("/orders/{identifier}/total", response_model=TotalOutput)
    def total(identifier: int):
        with app.state.factory() as session:
            return {"total": str(OrderRepository(session).total(identifier))}

    return app


app = create_app()
