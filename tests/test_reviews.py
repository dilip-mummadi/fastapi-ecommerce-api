"""Tests for product reviews."""
import pytest

from tests.conftest import make_admin, register_and_login

pytestmark = pytest.mark.asyncio


async def _seed_product(client) -> str:
    headers = await register_and_login(client, "reviewadmin@example.com")
    await make_admin("reviewadmin@example.com")
    resp = await client.post(
        "/api/v1/products/", json={"name": "Coffee Grinder", "price": "39.99", "stock": 10}, headers=headers
    )
    return resp.json()["id"]


async def test_create_review_and_it_affects_product_rating(client):
    product_id = await _seed_product(client)
    headers = await register_and_login(client, "reviewer1@example.com")

    resp = await client.post(
        f"/api/v1/products/{product_id}/reviews",
        json={"rating": 5, "comment": "Great grinder!"},
        headers=headers,
    )
    assert resp.status_code == 201

    product_resp = await client.get(f"/api/v1/products/{product_id}")
    body = product_resp.json()
    assert body["avg_rating"] == 5.0
    assert body["review_count"] == 1


async def test_cannot_review_same_product_twice(client):
    product_id = await _seed_product(client)
    headers = await register_and_login(client, "reviewer2@example.com")

    first = await client.post(
        f"/api/v1/products/{product_id}/reviews", json={"rating": 4}, headers=headers
    )
    second = await client.post(
        f"/api/v1/products/{product_id}/reviews", json={"rating": 2}, headers=headers
    )
    assert first.status_code == 201
    assert second.status_code == 409
