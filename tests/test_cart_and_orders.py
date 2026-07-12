"""Tests for the cart -> checkout -> order flow, including stock enforcement."""
import pytest

from tests.conftest import make_admin, register_and_login

pytestmark = pytest.mark.asyncio


async def _seed_product(client, name="Yoga Mat", price="29.99", stock=5) -> str:
    admin_headers = await register_and_login(client, f"seed_{name.replace(' ', '')}@example.com")
    await make_admin(f"seed_{name.replace(' ', '')}@example.com")
    resp = await client.post(
        "/api/v1/products/", json={"name": name, "price": price, "stock": stock}, headers=admin_headers
    )
    return resp.json()["id"]


async def test_add_to_cart_and_view(client):
    product_id = await _seed_product(client)
    headers = await register_and_login(client, "buyer1@example.com")

    resp = await client.post(
        "/api/v1/cart/items", json={"product_id": product_id, "quantity": 2}, headers=headers
    )
    assert resp.status_code == 201
    cart = resp.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert float(cart["total"]) == pytest.approx(59.98)


async def test_cannot_add_more_than_stock(client):
    product_id = await _seed_product(client, name="Limited Item", stock=2)
    headers = await register_and_login(client, "buyer2@example.com")

    resp = await client.post(
        "/api/v1/cart/items", json={"product_id": product_id, "quantity": 3}, headers=headers
    )
    assert resp.status_code == 409


async def test_checkout_creates_order_and_decrements_stock(client):
    product_id = await _seed_product(client, name="Desk Lamp", price="45.00", stock=3)
    headers = await register_and_login(client, "buyer3@example.com")

    await client.post(
        "/api/v1/cart/items", json={"product_id": product_id, "quantity": 2}, headers=headers
    )
    checkout_resp = await client.post(
        "/api/v1/orders/checkout", json={"shipping_address": "123 Main St, Springfield"}, headers=headers
    )
    assert checkout_resp.status_code == 201
    order = checkout_resp.json()
    assert order["status"] == "paid"
    assert float(order["total_amount"]) == pytest.approx(90.00)
    assert order["payment_reference"].startswith("mock_pay_")

    # cart should now be empty
    cart_resp = await client.get("/api/v1/cart/", headers=headers)
    assert cart_resp.json()["items"] == []

    # stock decremented: only 1 left, so buying 2 more should fail
    fail_resp = await client.post(
        "/api/v1/cart/items", json={"product_id": product_id, "quantity": 2}, headers=headers
    )
    assert fail_resp.status_code == 409


async def test_checkout_with_empty_cart_fails(client):
    headers = await register_and_login(client, "buyer4@example.com")
    resp = await client.post(
        "/api/v1/orders/checkout", json={"shipping_address": "1 Empty Ave"}, headers=headers
    )
    assert resp.status_code == 400


async def test_admin_can_update_order_status(client):
    product_id = await _seed_product(client, name="Notebook", price="5.00", stock=10)
    headers = await register_and_login(client, "buyer5@example.com")
    await client.post("/api/v1/cart/items", json={"product_id": product_id, "quantity": 1}, headers=headers)
    checkout_resp = await client.post(
        "/api/v1/orders/checkout", json={"shipping_address": "1 Test Way"}, headers=headers
    )
    order_id = checkout_resp.json()["id"]

    admin_headers = await register_and_login(client, "orderadmin@example.com")
    await make_admin("orderadmin@example.com")

    update_resp = await client.patch(
        f"/api/v1/orders/admin/{order_id}/status", json={"status": "shipped"}, headers=admin_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "shipped"

    non_admin_resp = await client.patch(
        f"/api/v1/orders/admin/{order_id}/status", json={"status": "delivered"}, headers=headers
    )
    assert non_admin_resp.status_code == 403
