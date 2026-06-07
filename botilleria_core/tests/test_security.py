from __future__ import annotations

from unittest.mock import MagicMock
import uuid
import pytest
from fastapi import FastAPI, Depends, status
from fastapi.testclient import TestClient

from middleware.security import verify_admin_key
from controllers.dependencies import get_current_tenant
from models.tenant import Tenant


def test_admin_auth_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings

    monkeypatch.setattr(settings, "admin_api_key", "test-secret-key")

    app: FastAPI = FastAPI()

    @app.get("/test-admin", dependencies=[Depends(verify_admin_key)])
    def admin_route() -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get("/test-admin", headers={"X-Admin-API-Key": "test-secret-key"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_admin_auth_missing_header(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings

    monkeypatch.setattr(settings, "admin_api_key", "test-secret-key")

    app: FastAPI = FastAPI()

    @app.get("/test-admin", dependencies=[Depends(verify_admin_key)])
    def admin_route() -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get("/test-admin")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing X-Admin-API-Key header" in response.json()["detail"]


def test_admin_auth_invalid_header(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings

    monkeypatch.setattr(settings, "admin_api_key", "test-secret-key")

    app: FastAPI = FastAPI()

    @app.get("/test-admin", dependencies=[Depends(verify_admin_key)])
    def admin_route() -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get("/test-admin", headers={"X-Admin-API-Key": "wrong-key"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid Admin API Key" in response.json()["detail"]


def test_admin_auth_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings

    monkeypatch.setattr(settings, "admin_api_key", "")

    app: FastAPI = FastAPI()

    @app.get("/test-admin", dependencies=[Depends(verify_admin_key)])
    def admin_route() -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get("/test-admin", headers={"X-Admin-API-Key": "some-key"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Admin API key is not configured" in response.json()["detail"]


def test_tenant_portal_auth_success(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_tenant: MagicMock = MagicMock(spec=Tenant)
    tenant_id: uuid.UUID = uuid.uuid4()
    mock_tenant.id = tenant_id

    mock_tenant_service: MagicMock = MagicMock()
    mock_tenant_service.get_tenant_by_id.return_value = mock_tenant

    monkeypatch.setattr(
        "controllers.dependencies.TenantService",
        lambda db: mock_tenant_service,
    )

    from services.auth_service import AuthService

    token = AuthService.create_access_token({"sub": str(tenant_id), "role": "tenant"})

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok", "tenant_id": str(tenant.id)}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "tenant_id": str(tenant_id)}


def test_tenant_portal_auth_missing_header(monkeypatch: pytest.MonkeyPatch) -> None:
    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get("/test-portal")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing or invalid Authorization header" in response.json()["detail"]


def test_tenant_portal_auth_invalid_header_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={"Authorization": "NotBearer token123"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing or invalid Authorization header" in response.json()["detail"]


def test_tenant_portal_auth_invalid_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={"Authorization": "Bearer invalidtokenhere"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired JWT token" in response.json()["detail"]


def test_tenant_portal_auth_wrong_role(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.auth_service import AuthService

    token = AuthService.create_access_token({"sub": str(uuid.uuid4()), "role": "user"})

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired JWT token" in response.json()["detail"]


def test_tenant_portal_auth_tenant_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_tenant_service: MagicMock = MagicMock()
    mock_tenant_service.get_tenant_by_id.return_value = None

    monkeypatch.setattr(
        "controllers.dependencies.TenantService",
        lambda db: mock_tenant_service,
    )

    from services.auth_service import AuthService

    token = AuthService.create_access_token(
        {"sub": str(uuid.uuid4()), "role": "tenant"}
    )

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired JWT token" in response.json()["detail"]
