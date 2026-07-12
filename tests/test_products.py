"""Tests for the product catalog: admin-only writes, public search/filter/pagination."""
import pytest

from tests.conftest import make_admin, register_and_login

pytestmark = pytest.mark.asyncio


async def _admin_headers(client, email="admin1@example.com"):
    headers = await register_and_login(client, email)
    await make_admin(email)
    return headers


async def _create_category(client, headers, name="Electronics"):
    resp = await client.post("/api/v1/categories/", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_non_admin_cannot_create_product(client):
    headers = await register_and_login(client, "shopper@example.com")
    resp = await client.post(
        "/api/v1/products/",
        json={"name": "Phone", "price": "199.99", "stock": 10},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_admin_can_create_and_list_products(client):
    headers = await _admin_headers(client)
    category_id = await _create_category(client, headers)

    create_resp = await client.post(
        "/api/v1/products/",
        json={
            "name": "Wireless Headphones",
            "description": "Noise cancelling",
            "price": "149.99",
            "stock": 25,
            "category_id": category_id,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    product = create_resp.json()
    assert product["slug"] == "wireless-headphones"
    assert product["category"]["name"] == "Electronics"

    list_resp = await client.get("/api/v1/products/")
    assert list_resp.status_code == 200
    page = list_resp.json()
    assert page["total"] == 1
    assert page["page_size"] == 20
    assert page["pages"] == 1
    assert page["items"][0]["name"] == "Wireless Headphones"


async def test_product_search_and_price_filter(client):
    headers = await _admin_headers(client, "admin2@example.com")
    for name, price in [("Cheap Mouse", "9.99"), ("Gaming Mouse", "59.99"), ("Keyboard", "89.99")]:
        await client.post(
            "/api/v1/products/", json={"name": name, "price": price, "stock": 5}, headers=headers
        )

    resp = await client.get("/api/v1/products/", params={"search": "mouse"})
    assert resp.json()["total"] == 2

    resp = await client.get("/api/v1/products/", params={"min_price": 50, "max_price": 100})
    names = {p["name"] for p in resp.json()["items"]}
    assert names == {"Gaming Mouse", "Keyboard"}


async def test_pagination_page_size_and_invalid_page(client):
    headers = await _admin_headers(client, "admin4@example.com")
    for i in range(5):
        await client.post(
            "/api/v1/products/",
            json={"name": f"Item {i}", "price": "10.00", "stock": 1},
            headers=headers,
        )

    # page_size respected
    resp = await client.get("/api/v1/products/", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["page_size"] == 2
    assert data["total"] == 5
    assert data["pages"] == 3

    # page beyond total pages returns 422
    resp = await client.get("/api/v1/products/", params={"page": 99, "page_size": 20})
    assert resp.status_code == 422

    # page=0 is rejected by query validation
    resp = await client.get("/api/v1/products/", params={"page": 0})
    assert resp.status_code == 422


async def test_update_and_soft_delete_product(client):
    headers = await _admin_headers(client, "admin3@example.com")
    create_resp = await client.post(
        "/api/v1/products/", json={"name": "Old Laptop", "price": "999.00", "stock": 3}, headers=headers
    )
    product_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/v1/products/{product_id}", json={"price": "899.00", "stock": 2}, headers=headers
    )
    assert update_resp.status_code == 200
    assert float(update_resp.json()["price"]) == 899.00

    delete_resp = await client.delete(f"/api/v1/products/{product_id}", headers=headers)
    assert delete_resp.status_code == 204

    # soft-deleted products drop out of the public listing
    list_resp = await client.get("/api/v1/products/")
    assert all(p["id"] != product_id for p in list_resp.json()["items"])
