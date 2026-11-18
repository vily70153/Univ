import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from restaurant_orders.api import create_app
from restaurant_orders.async_client import fetch_totals


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'api.db'}")) as client:
        yield client


def test_rest_flow(client):
    assert client.get("/health").json() == {"status": "ok"}
    r = client.post(
        "/dishes", json={"name": "soup", "category": "food", "price": "85.00"}
    )
    assert r.status_code == 201
    dish = r.json()["id"]
    assert len(client.get("/dishes?category=food").json()) == 1
    assert client.get("/dishes?category=other").json() == []
    r = client.post("/orders", json={"items": [{"dish_id": dish, "quantity": 2}]})
    assert r.status_code == 201
    number = r.json()["id"]
    assert client.get(f"/orders/{number}/total").json()["total"] == "170"
    assert client.get("/orders/statistics").json()["average"] == "170"
    assert len(client.get("/orders").json()) == 1
    assert (
        client.patch(
            f"/dishes/{dish}", json={"name": "borsch", "price": "90"}
        ).status_code
        == 200
    )
    assert client.get(f"/orders/{number}/total").json()["total"] == "170"
    assert client.patch(f"/orders/{number}", json={"status": "paid"}).status_code == 200
    item = client.get(f"/orders/{number}").json()["items"][0]["id"]
    assert client.delete(f"/dishes/{dish}").status_code == 409
    assert client.delete(f"/orders/{number}/items/{item}").status_code == 204
    assert (
        client.post(
            f"/orders/{number}/items", json={"dish_id": dish, "quantity": 1}
        ).status_code
        == 201
    )
    assert client.get(f"/orders/{number}/total").json()["total"] == "90"


def test_invalid_and_missing(client):
    assert client.get("/orders/999").status_code == 404
    assert (
        client.post(
            "/dishes", json={"name": "x", "category": "y", "price": -1}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/orders", json={"items": [{"dish_id": 1, "quantity": 0}]}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/orders", json={"items": [{"dish_id": 999, "quantity": 1}]}
        ).status_code
        == 404
    )
    assert client.get("/orders").json() == []
    assert client.patch("/orders/1", json={"status": "nonsense"}).status_code == 422


async def test_async_http_integration(client):
    a = client.post("/orders", json={}).json()["id"]
    b = client.post("/orders", json={}).json()["id"]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=client.app), base_url="http://test"
    ) as http:
        assert await fetch_totals(http, [a, b], concurrency=1) == [
            {"total": "0"},
            {"total": "0"},
        ]


async def test_retry():
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(503 if calls == 1 else 200, json={"total": "12"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as http:
        assert await fetch_totals(http, [1]) == [{"total": "12"}]
    assert calls == 2


async def test_no_retry_404():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(404)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as http:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_totals(http, [1])
    assert calls == 1


async def test_timeout():
    async def handler(request):
        await asyncio.sleep(1)
        return httpx.Response(200)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as http:
        with pytest.raises(TimeoutError):
            await fetch_totals(http, [1], retries=0, timeout=0.001)
