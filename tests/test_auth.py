"""Tests for registration, login, and token refresh."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_register_and_login(client):
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "jane@example.com", "full_name": "Jane Doe", "password": "supersecret"},
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["role"] == "customer"

    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": "jane@example.com", "password": "supersecret"}
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert "access_token" in body and "refresh_token" in body


async def test_duplicate_registration_fails(client):
    payload = {"email": "dup@example.com", "full_name": "Dup User", "password": "supersecret"}
    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 400


async def test_refresh_token_issues_new_access_token(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "full_name": "R User", "password": "supersecret"},
    )
    login = await client.post(
        "/api/v1/auth/login", data={"username": "refresh@example.com", "password": "supersecret"}
    )
    refresh_token = login.json()["refresh_token"]

    refresh_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


async def test_wrong_password_rejected(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wp@example.com", "full_name": "WP", "password": "supersecret"},
    )
    resp = await client.post("/api/v1/auth/login", data={"username": "wp@example.com", "password": "wrong"})
    assert resp.status_code == 401
