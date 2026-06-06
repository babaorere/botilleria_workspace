from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.database import get_db
from config.settings import settings
from services.auth_service import AuthService
from services.tenant_service import TenantService
from middleware.security import oauth2_scheme


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate user (Admin or Tenant) and return a JWT token.
    - Admin: username="admin", password=<ADMIN_API_KEY>
    - Tenant: username=<tenant_slug>, password=<PORTAL_TOKEN>
    """
    username = form_data.username
    password = form_data.password

    import hmac

    # Check for Admin login
    if username == "admin":
        if hmac.compare_digest(password.encode("utf-8"), settings.admin_api_key.encode("utf-8")):
            token = AuthService.create_access_token(
                data={"sub": "admin", "role": "admin"}
            )
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Check for Tenant login
    tenant_service = TenantService(db)
    tenant = tenant_service.tenant_repo.find_by_slug(username)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    portal_token = tenant.get_portal_token() or ""
    if not hmac.compare_digest(password.encode("utf-8"), portal_token.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = AuthService.create_access_token(
        data={"sub": str(tenant.id), "role": "tenant", "slug": tenant.slug}
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    payload = AuthService.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    AuthService.revoke_token(payload)
    return {"detail": "Successfully logged out"}
