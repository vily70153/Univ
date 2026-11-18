import pytest

from restaurant_orders.config import Settings
from restaurant_orders.errors import ValidationError


def test_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    settings = Settings.from_env()
    assert settings.app_env == "testing" and settings.log_level == "DEBUG"


@pytest.mark.parametrize(
    "key,value", [("LOG_LEVEL", "bad"), ("DATABASE_URL", "postgresql://localhost/db")]
)
def test_invalid_environment(monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValidationError):
        Settings.from_env()
