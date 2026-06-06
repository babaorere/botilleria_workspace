from __future__ import annotations

from unittest.mock import MagicMock
import uuid
import pytest
from fastapi import FastAPI, Depends, status
from fastapi.testclient import TestClient

from middleware.security import verify_admin_key
from controllers.tenant_portal_controller import get_current_tenant
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
    mock_tenant.get_portal_token.return_value = "tenant-portal-secret"

    mock_tenant_service: MagicMock = MagicMock()
    mock_tenant_service.get_tenant_by_id.return_value = mock_tenant

    monkeypatch.setattr(
        "controllers.tenant_portal_controller.TenantService",
        lambda db: mock_tenant_service,
    )

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok", "tenant_id": str(tenant.id)}

    client: TestClient = TestClient(app)
    tenant_uuid_str: str = str(tenant_id)
    response = client.get(
        "/test-portal",
        headers={
            "X-Tenant-ID": tenant_uuid_str,
            "X-Tenant-API-Key": "tenant-portal-secret",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "tenant_id": tenant_uuid_str}


def test_tenant_portal_auth_missing_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={
            "X-Tenant-API-Key": "some-key",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing Authorization or X-Tenant-ID header" in response.json()["detail"]


def test_tenant_portal_auth_invalid_tenant_uuid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    response = client.get(
        "/test-portal",
        headers={
            "X-Tenant-ID": "not-a-uuid",
            "X-Tenant-API-Key": "some-key",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid X-Tenant-ID format" in response.json()["detail"]


def test_tenant_portal_auth_tenant_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_tenant_service: MagicMock = MagicMock()
    mock_tenant_service.get_tenant_by_id.return_value = None

    monkeypatch.setattr(
        "controllers.tenant_portal_controller.TenantService",
        lambda db: mock_tenant_service,
    )

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    tenant_uuid_str: str = str(uuid.uuid4())
    response = client.get(
        "/test-portal",
        headers={
            "X-Tenant-ID": tenant_uuid_str,
            "X-Tenant-API-Key": "some-key",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not found or inactive" in response.json()["detail"]


def test_tenant_portal_auth_missing_portal_key(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_tenant: MagicMock = MagicMock(spec=Tenant)
    tenant_id: uuid.UUID = uuid.uuid4()
    mock_tenant.id = tenant_id
    mock_tenant.get_portal_token.return_value = "tenant-portal-secret"

    mock_tenant_service: MagicMock = MagicMock()
    mock_tenant_service.get_tenant_by_id.return_value = mock_tenant

    monkeypatch.setattr(
        "controllers.tenant_portal_controller.TenantService",
        lambda db: mock_tenant_service,
    )

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    tenant_uuid_str: str = str(tenant_id)
    response = client.get(
        "/test-portal",
        headers={
            "X-Tenant-ID": tenant_uuid_str,
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Invalid or missing X-Tenant-API-Key header" in response.json()["detail"]


def test_tenant_portal_auth_wrong_portal_key(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_tenant: MagicMock = MagicMock(spec=Tenant)
    tenant_id: uuid.UUID = uuid.uuid4()
    mock_tenant.id = tenant_id
    mock_tenant.get_portal_token.return_value = "tenant-portal-secret"

    mock_tenant_service: MagicMock = MagicMock()
    mock_tenant_service.get_tenant_by_id.return_value = mock_tenant

    monkeypatch.setattr(
        "controllers.tenant_portal_controller.TenantService",
        lambda db: mock_tenant_service,
    )

    app: FastAPI = FastAPI()

    @app.get("/test-portal")
    def portal_route(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, str]:
        return {"status": "ok"}

    client: TestClient = TestClient(app)
    tenant_uuid_str: str = str(tenant_id)
    response = client.get(
        "/test-portal",
        headers={
            "X-Tenant-ID": tenant_uuid_str,
            "X-Tenant-API-Key": "wrong-portal-secret",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Invalid or missing X-Tenant-API-Key header" in response.json()["detail"]
