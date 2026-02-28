"""Tests for auth & user-profile endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user_id
from app.main import app

# ---------------------------------------------------------------------------
# Helpers / overrides
# ---------------------------------------------------------------------------

FAKE_CLERK_ID = "clerk_test_user_123"


def _override_get_current_user_id() -> str:
    """Always return a deterministic fake clerk_id."""
    return FAKE_CLERK_ID


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def _override_auth():
    """Override JWT verification so tests don't need real tokens."""
    app.dependency_overrides[get_current_user_id] = _override_get_current_user_id
    yield
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def authed_client(_override_auth) -> AsyncClient:  # type: ignore[misc]
    """Async client with auth dependency overridden."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def unauthed_client() -> AsyncClient:  # type: ignore[misc]
    """Async client with NO auth overrides – requests should fail 401/422."""
    # Make sure no overrides leak
    app.dependency_overrides.pop(get_current_user_id, None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Webhook tests
# ---------------------------------------------------------------------------


class TestClerkWebhook:
    """POST /api/v1/auth/webhook."""

    async def test_user_created(self, authed_client: AsyncClient) -> None:
        payload = {
            "type": "user.created",
            "data": {
                "id": FAKE_CLERK_ID,
                "email_addresses": [{"email_address": "test@example.com"}],
                "first_name": "Test",
                "username": "testuser",
            },
        }
        resp = await authed_client.post("/api/v1/auth/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    async def test_user_deleted_nonexistent(self, authed_client: AsyncClient) -> None:
        """Deleting a user that doesn't exist should still return 200."""
        payload = {
            "type": "user.deleted",
            "data": {"id": "clerk_nonexistent"},
        }
        resp = await authed_client.post("/api/v1/auth/webhook", json=payload)
        assert resp.status_code == 200

    async def test_unknown_event_type(self, authed_client: AsyncClient) -> None:
        payload = {
            "type": "session.created",
            "data": {"id": "sess_123"},
        }
        resp = await authed_client.post("/api/v1/auth/webhook", json=payload)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /users/me tests
# ---------------------------------------------------------------------------


class TestGetMe:
    """GET /api/v1/users/me."""

    async def test_returns_404_when_user_not_synced(self, authed_client: AsyncClient) -> None:
        """If the webhook hasn't created the user yet, expect 404."""
        resp = await authed_client.get("/api/v1/users/me")
        assert resp.status_code == 404

    async def test_returns_user_after_webhook(self, authed_client: AsyncClient) -> None:
        # First, create the user via webhook
        webhook_payload = {
            "type": "user.created",
            "data": {
                "id": FAKE_CLERK_ID,
                "email_addresses": [{"email_address": "me@example.com"}],
                "first_name": "Alice",
            },
        }
        resp = await authed_client.post("/api/v1/auth/webhook", json=webhook_payload)
        assert resp.status_code == 200

        # Now fetch profile
        resp = await authed_client.get("/api/v1/users/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["clerk_id"] == FAKE_CLERK_ID
        assert body["email"] == "me@example.com"
        assert body["display_name"] == "Alice"


class TestUpdateMe:
    """PUT /api/v1/users/me."""

    async def test_update_display_name(self, authed_client: AsyncClient) -> None:
        # Seed user
        await authed_client.post(
            "/api/v1/auth/webhook",
            json={
                "type": "user.created",
                "data": {
                    "id": FAKE_CLERK_ID,
                    "email_addresses": [{"email_address": "up@example.com"}],
                    "first_name": "Before",
                },
            },
        )

        resp = await authed_client.put(
            "/api/v1/users/me",
            json={"display_name": "After"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "After"

    async def test_update_locale(self, authed_client: AsyncClient) -> None:
        await authed_client.post(
            "/api/v1/auth/webhook",
            json={
                "type": "user.created",
                "data": {
                    "id": FAKE_CLERK_ID,
                    "email_addresses": [{"email_address": "loc@example.com"}],
                },
            },
        )

        resp = await authed_client.put(
            "/api/v1/users/me",
            json={"locale": "en"},
        )
        assert resp.status_code == 200
        assert resp.json()["locale"] == "en"


class TestDeleteMe:
    """DELETE /api/v1/users/me."""

    async def test_delete_user(self, authed_client: AsyncClient) -> None:
        # Seed user
        await authed_client.post(
            "/api/v1/auth/webhook",
            json={
                "type": "user.created",
                "data": {
                    "id": FAKE_CLERK_ID,
                    "email_addresses": [{"email_address": "del@example.com"}],
                },
            },
        )

        resp = await authed_client.delete("/api/v1/users/me")
        assert resp.status_code == 204

        # Confirm user is gone
        resp = await authed_client.get("/api/v1/users/me")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------


class TestUnauthenticated:
    """Endpoints should reject requests without auth."""

    async def test_get_me_no_auth(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.get("/api/v1/users/me")
        # FastAPI returns 422 when required Header is missing
        assert resp.status_code in (401, 422)

    async def test_put_me_no_auth(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.put("/api/v1/users/me", json={"display_name": "x"})
        assert resp.status_code in (401, 422)

    async def test_delete_me_no_auth(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.delete("/api/v1/users/me")
        assert resp.status_code in (401, 422)
