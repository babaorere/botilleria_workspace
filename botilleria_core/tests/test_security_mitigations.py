from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import ValidationError

from config.settings import settings
from dtos.request import ChatRequest
from main import app
from services.auth_service import AuthService
from services.rate_limiter import RateLimiter


# =====================================================================
# 1. INPUT LIMITATION TESTS (Defect 4)
# =====================================================================


def test_chat_request_validation_success_on_valid_length() -> None:
    """A message of 4096 characters should pass validation."""
    valid_message = "A" * 4096

    # Act
    request = ChatRequest(
        user_id="user_123",
        platform="telegram",
        message=valid_message,
        session_id=str(uuid.uuid4()),
    )

    # Assert
    assert len(request.message) == 4096


def test_chat_request_validation_error_on_too_long() -> None:
    """A message of 4097 characters should raise ValidationError."""
    invalid_message = "A" * 4097

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(
            user_id="user_123",
            platform="telegram",
            message=invalid_message,
            session_id=str(uuid.uuid4()),
        )

    assert "String should have at most 4096 characters" in str(exc_info.value)


# =====================================================================
# 2. RATE LIMITER TESTS (Defect 2)
# =====================================================================


@pytest.mark.asyncio
async def test_rate_limiter_in_memory_sliding_window() -> None:
    """Test in-memory sliding window rate limiter."""
    limiter = RateLimiter(redis_client=None)
    tenant_id = str(uuid.uuid4())
    user_id = "user_test_in_mem"

    # Arrange: limit of 3 requests in a 60-second window
    limit = 3
    window = 60

    # Act & Assert: first 3 requests should be allowed
    for _ in range(3):
        is_limited = await limiter.is_rate_limited(tenant_id, user_id, limit, window)
        assert not is_limited

    # The 4th request must be limited
    is_limited = await limiter.is_rate_limited(tenant_id, user_id, limit, window)
    assert is_limited


@pytest.mark.asyncio
async def test_rate_limiter_redis_sliding_window() -> None:
    """Test Redis sliding window rate limiter using a mocked Redis pipeline."""
    mock_redis = MagicMock()
    mock_pipeline = MagicMock()

    # zcard is the 3rd operation in pipeline execution
    # pipeline returns [removed_count, added_count, total_count, expire_result]
    mock_pipeline.execute = AsyncMock(return_value=[0, 1, 4, True])
    mock_redis.pipeline.return_value = mock_pipeline

    limiter = RateLimiter(redis_client=mock_redis)
    tenant_id = str(uuid.uuid4())
    user_id = "user_test_redis"

    # Act: 4th request in redis should return limited (count=4 > limit=3)
    is_limited = await limiter.is_rate_limited(tenant_id, user_id, limit=3, window=60)

    # Assert
    assert is_limited
    mock_pipeline.zremrangebyscore.assert_called_once()
    mock_pipeline.zadd.assert_called_once()
    mock_pipeline.zcard.assert_called_once()
    mock_pipeline.expire.assert_called_once()


def test_chat_endpoint_rate_limit_integration() -> None:
    """Test that FastAPI chat endpoint returns HTTP 429 when rate limited."""
    # Arrange: Setup custom rate limiter mock that returns True (limited)
    mock_limiter = AsyncMock()
    mock_limiter.is_rate_limited.return_value = True

    # Override the rate limiter dependency
    from controllers.chat_controller import get_rate_limiter

    app.dependency_overrides[get_rate_limiter] = lambda: mock_limiter

    # Setup database tenant resolver mock
    mock_tenant = MagicMock()
    mock_tenant.id = uuid.uuid4()
    mock_tenant.slug = "el_buen_trago"

    with patch(
        "controllers.chat_controller.resolve_tenant_from_request",
        AsyncMock(return_value=mock_tenant),
    ):
        client = TestClient(app)

        # Act
        response = client.post(
            "/chat",
            json={
                "user_id": "user123",
                "platform": "telegram",
                "message": "Hola",
            },
            headers={"X-Tenant-ID": str(mock_tenant.id)},
        )

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Demasiadas solicitudes" in response.json()["detail"]

    # Cleanup dependency overrides
    app.dependency_overrides.clear()


# =====================================================================
# 3. JWT REVOCATION TESTS (Defect 3)
# =====================================================================


def test_jwt_revocation_logic_in_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test token revocation and validation using in-memory denylist."""
    # Arrange: Set session_backend to 'inmemory' to ensure Redis check is skipped
    monkeypatch.setattr(settings, "session_backend", "inmemory")

    data = {"sub": "tenant_123", "role": "tenant"}
    token = AuthService.create_access_token(data)

    # Act: Decode valid token
    payload = AuthService.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "tenant_123"

    # Revoke the token
    AuthService.revoke_token(payload)

    # Act & Assert: Decode revoked token
    revoked_payload = AuthService.decode_access_token(token)
    assert revoked_payload is None


def test_logout_endpoint_revokes_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /auth/logout should revoke the token and reject subsequent calls."""
    # Arrange: Set session_backend to 'inmemory'
    monkeypatch.setattr(settings, "session_backend", "inmemory")
    client = TestClient(app)

    # Login or create a token manually
    token = AuthService.create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # Act: Request to logout route should succeed first
    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {"detail": "Successfully logged out"}

    # Act & Assert: Subsequent call using the same token should fail
    subsequent_logout = client.post("/auth/logout", headers=headers)
    assert subsequent_logout.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================================
# 4. EVENT LOOP BLOCKING TESTS (Defect 1)
# =====================================================================


@pytest.mark.asyncio
async def test_async_thread_delegation_in_chat_service() -> None:
    """Verify that ChatService executes DB user/conversation setup in an external thread."""
    # Arrange
    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_llm.run_chat = AsyncMock(return_value="Respuesta")

    from services.chat_service import ChatService

    service = ChatService(db=mock_db, llm_service=mock_llm)

    tenant = MagicMock()
    tenant.id = uuid.uuid4()

    # Mock _resolve_user_and_conversation to return 123, avoiding real DB queries
    with patch.object(service, "_resolve_user_and_conversation", return_value=123):
        with patch("asyncio.to_thread", AsyncMock(return_value=123)) as mock_to_thread:
            # Act
            await service.process_message(
                tenant=tenant,
                user_id="user_123",
                platform="telegram",
                message="Hola",
                session_id=str(uuid.uuid4()),
            )

            # Assert: asyncio.to_thread should have been called with the resolve method
            mock_to_thread.assert_called_once()
            args = mock_to_thread.call_args[0]
            assert args[0] == service._resolve_user_and_conversation
