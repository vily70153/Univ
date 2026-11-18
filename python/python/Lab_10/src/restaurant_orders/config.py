import os
from dataclasses import dataclass

from restaurant_orders.errors import ValidationError


@dataclass(frozen=True)
class Settings:
    database_url: str
    app_env: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValidationError("invalid LOG_LEVEL")
        url = os.getenv("DATABASE_URL", "sqlite:///restaurant.db")
        if not url.startswith("sqlite:///"):
            raise ValidationError("this laboratory supports SQLite only")
        return cls(url, os.getenv("APP_ENV", "development"), level)
