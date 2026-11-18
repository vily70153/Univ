"""SQLite schema, SQLAlchemy unit of work and DB-API example."""

import sqlite3
from pathlib import Path

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class CategoryRow(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)


class DishRow(Base):
    __tablename__ = "dishes"
    __table_args__ = (CheckConstraint("price_cents > 0"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    price_cents: Mapped[int] = mapped_column(Integer)


class OrderRow(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String, default="new", server_default="new")


class ItemRow(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0"),
        CheckConstraint("price_cents > 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)


def make_engine(url: str) -> Engine:
    engine = create_engine(
        url, connect_args={"check_same_thread": False, "timeout": 15}
    )

    @event.listens_for(engine, "connect")
    def set_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def initialize(url: str):
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)


def search_category(path: Path, category: str) -> list[tuple]:
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT d.id, d.name, d.price_cents FROM dishes d JOIN categories c ON d.category_id=c.id WHERE c.name=?",
            (category,),
        ).fetchall()
    finally:
        connection.close()


def migrate_status(engine: Engine) -> None:
    """Idempotent v1 -> v2 migration; SQLite DDL within explicit transaction."""
    with engine.begin() as connection:
        columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(orders)"))
        }
        if "status" not in columns:
            connection.execute(
                text("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
            )
